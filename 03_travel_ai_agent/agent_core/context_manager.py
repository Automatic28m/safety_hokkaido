"""Conversation context for node 03.

* ``ConversationMemoryStore`` keeps one ``ConversationMemory`` per
  ``conversation_id``. There is no process-wide shared history: a request can
  only read the memory of its own conversation.
* History supplied by the API is authoritative; server memory is only a cache
  and summarization aid for a single conversation.
* ``ContextManager`` also prepares the retrieval query (reformulation and
  translation) and assembles the package handed to node 07.
"""
from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent_core.llm_client import LLMClientError
from agent_core.schemas import ContextPackage, OrchestrationRequest

logger = logging.getLogger("travel_ai_agent")

CHARS_PER_TOKEN = 4
MAX_HISTORY_TOKENS = 3000
RECENT_MESSAGES_TO_KEEP = 4
MAX_TURNS_PER_CONVERSATION = 40
MAX_CONVERSATIONS = 500
HISTORY_WINDOW_FOR_PROMPTS = 6

DEFAULT_TRANSFORM_MODEL = "openai/gpt-oss-20b"

SUMMARY_PROMPT = (
    "You are a conversation summarizer. Summarize the following conversation turns into "
    "2-3 concise sentences. Preserve ALL critical facts: the user's location, their situation, "
    "any people with them (especially children), and any danger they mentioned. Be factual and brief."
)
REFORMULATE_PROMPT = (
    "Given the following conversation history and the user's follow-up question, rephrase the "
    "follow-up question to be a standalone question that can be understood without the history. "
    "DO NOT answer the question. ONLY output the standalone question."
)
TRANSLATE_PROMPT = (
    "You are a professional translator. Translate the user's input into English. DO NOT answer "
    "the question. ONLY output the English translation."
)


def normalize_history(history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """Keeps only user/assistant turns with non-empty text; maps legacy ``ai`` to ``assistant``."""
    normalized: List[Dict[str, str]] = []
    for turn in history or []:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role")
        if role == "ai":
            role = "assistant"
        if role not in ("user", "assistant"):
            continue
        content = turn.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def strip_trailing_query(history: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
    """Removes the current question when the client included it as the last history turn."""
    if history and history[-1]["role"] == "user" and history[-1]["content"].strip() == query.strip():
        return history[:-1]
    return history


class ConversationMemory:
    """History of one conversation, summarized when it grows too long."""

    def __init__(self, summarizer: Optional[Callable[[List[Dict[str, str]]], str]] = None):
        self._turns: List[Dict[str, str]] = []
        self._summarizer = summarizer
        self._lock = threading.Lock()

    def add_turn(self, role: str, content: str) -> None:
        if role not in ("user", "assistant") or not isinstance(content, str) or not content.strip():
            return
        with self._lock:
            self._turns.append({"role": role, "content": content})
            self._maybe_summarize()

    def get_history(self) -> List[Dict[str, str]]:
        with self._lock:
            return [dict(turn) for turn in self._turns]

    def clear(self) -> None:
        with self._lock:
            self._turns = []

    def _estimate_tokens(self) -> int:
        return sum(len(turn["content"]) for turn in self._turns) // CHARS_PER_TOKEN

    def _maybe_summarize(self) -> None:
        too_long = self._estimate_tokens() > MAX_HISTORY_TOKENS or len(self._turns) > MAX_TURNS_PER_CONVERSATION
        if not too_long or len(self._turns) <= RECENT_MESSAGES_TO_KEEP:
            return
        old = self._turns[:-RECENT_MESSAGES_TO_KEEP]
        recent = self._turns[-RECENT_MESSAGES_TO_KEEP:]
        summary = self._summarizer(old) if self._summarizer else _truncate_summary(old)
        self._turns = [{"role": "assistant", "content": f"[Earlier conversation summary: {summary}]"}] + recent


def _truncate_summary(turns: List[Dict[str, str]]) -> str:
    return " | ".join(f"{t['role']}: {t['content'][:80]}" for t in turns[-6:])


class ConversationMemoryStore:
    """Registry of per-conversation memories with LRU eviction."""

    def __init__(
        self,
        summarizer: Optional[Callable[[List[Dict[str, str]]], str]] = None,
        max_conversations: int = MAX_CONVERSATIONS,
    ):
        self._memories: "OrderedDict[str, ConversationMemory]" = OrderedDict()
        self._summarizer = summarizer
        self._max = max_conversations
        self._lock = threading.Lock()

    def set_summarizer(self, summarizer: Optional[Callable[[List[Dict[str, str]]], str]]) -> None:
        self._summarizer = summarizer

    def get(self, conversation_id: str, create: bool = True) -> Optional[ConversationMemory]:
        with self._lock:
            memory = self._memories.get(conversation_id)
            if memory is not None:
                self._memories.move_to_end(conversation_id)
                return memory
            if not create:
                return None
            memory = ConversationMemory(summarizer=self._summarizer)
            self._memories[conversation_id] = memory
            while len(self._memories) > self._max:
                self._memories.popitem(last=False)
            return memory

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._memories.pop(conversation_id, None)

    def clear_all(self) -> None:
        with self._lock:
            self._memories.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._memories)


# Process-wide registry used by 02_api_backend/main.py for the debug reset endpoint.
# Access is always by conversation_id; there is no shared history.
memory_store = ConversationMemoryStore()


class ContextManager:
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        store: Optional[ConversationMemoryStore] = None,
        model: Optional[str] = None,
        use_memory: Optional[bool] = None,
    ):
        self.llm_client = llm_client
        # An empty store is falsy (it defines __len__), so test identity, not truthiness.
        self.store = store if store is not None else memory_store
        if model is None or use_memory is None:
            try:
                from config import config

                model = model or getattr(config, "LLM_MODEL", DEFAULT_TRANSFORM_MODEL)
                use_memory = getattr(config, "USE_MEMORY", True) if use_memory is None else use_memory
            except ImportError:
                model = model or DEFAULT_TRANSFORM_MODEL
                use_memory = True if use_memory is None else use_memory
        self.model = model
        self.use_memory = bool(use_memory)
        self.store.set_summarizer(self.summarize_history)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def resolve_history(self, request: OrchestrationRequest) -> Tuple[List[Dict[str, str]], str]:
        """Returns (history, source). API history wins; memory is used only for the same conversation."""
        api_history = normalize_history(request.chat_history)
        if api_history:
            return strip_trailing_query(api_history, request.original_query), "api"
        if self.use_memory and request.conversation_id:
            memory = self.store.get(request.conversation_id, create=False)
            if memory is not None:
                return memory.get_history(), "memory"
        return [], "none"

    def remember(self, request: OrchestrationRequest, reply: str) -> None:
        """Appends the exchange to the conversation's own memory only."""
        if not self.use_memory or not request.conversation_id:
            return
        memory = self.store.get(request.conversation_id)
        memory.add_turn("user", request.original_query)
        memory.add_turn("assistant", reply)

    def summarize_history(self, turns: List[Dict[str, str]]) -> str:
        if self.llm_client is None or not getattr(self.llm_client, "is_configured", True):
            return _truncate_summary(turns)
        transcript = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in turns)
        try:
            return self.llm_client.complete(
                [{"role": "system", "content": SUMMARY_PROMPT}, {"role": "user", "content": transcript}],
                model=self.model,
                temperature=0.0,
                max_tokens=200,
            ).strip()
        except LLMClientError as exc:
            logger.warning("history summarization failed: %s", exc)
            return _truncate_summary(turns)

    # ------------------------------------------------------------------
    # Retrieval query preparation
    # ------------------------------------------------------------------
    def reformulate_query(self, query: str, history: List[Dict[str, str]]) -> Tuple[str, Optional[str]]:
        """Rewrites a follow-up into a standalone question. The original query is never replaced."""
        if not history:
            return query, None
        if self.llm_client is None or not getattr(self.llm_client, "is_configured", True):
            return query, "query reformulation skipped: provider not configured"
        transcript = "".join(
            f"{'AI' if t['role'] == 'assistant' else 'User'}: {t['content']}\n" for t in history[-4:]
        )
        try:
            standalone = self.llm_client.complete(
                [
                    {"role": "system", "content": REFORMULATE_PROMPT},
                    {
                        "role": "user",
                        "content": f"Chat History:\n{transcript}\nFollow-up question: {query}\n\nStandalone question:",
                    },
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=200,
            ).strip()
        except LLMClientError as exc:
            logger.warning("query reformulation failed: %s", exc)
            return query, "query reformulation unavailable; used the original question"
        return (standalone or query), None

    def translate_for_retrieval(self, query: str, language: str) -> Tuple[str, Optional[str]]:
        """Translates only the retrieval query; the user's own text is never modified."""
        if language == "en":
            return query, None
        if self.llm_client is None or not getattr(self.llm_client, "is_configured", True):
            return query, "retrieval translation skipped: provider not configured"
        try:
            english = self.llm_client.complete(
                [
                    {"role": "system", "content": TRANSLATE_PROMPT},
                    {"role": "user", "content": f"Translate this into English: {query}"},
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=300,
            ).strip()
        except LLMClientError as exc:
            logger.warning("retrieval translation failed: %s", exc)
            return query, "retrieval translation unavailable; searched with the original text"
        return (english or query), None

    # ------------------------------------------------------------------
    # Package for node 07
    # ------------------------------------------------------------------
    @staticmethod
    def build_context_package(
        request: OrchestrationRequest,
        history: List[Dict[str, str]],
        evidence: List[Dict[str, Any]],
        live_data: List[Dict[str, Any]],
        language: str,
        tool_policy: Dict[str, Any],
        route: str,
    ) -> ContextPackage:
        return ContextPackage(
            original_query=request.original_query,
            history=history[-HISTORY_WINDOW_FOR_PROMPTS:],
            evidence=evidence,
            live_data=live_data,
            language=language,
            tool_policy=tool_policy,
            route=route,
        )
