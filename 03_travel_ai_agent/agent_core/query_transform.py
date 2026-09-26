"""Deprecated import path kept for callers outside node 03.

``08_recommendation_feedback/recommendation_feedback/evaluation/eval_retrieval.py``
still does ``QueryTransformer().translate_to_english(question)``. The logic now
lives in ``context_manager.ContextManager``; this adapter keeps the old method
names and return types (plain strings) without any shared state.

Owner of node 08: prefer ``ContextManager.translate_for_retrieval()``, which also
returns a notice when the provider is unavailable.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.classifier import detect_language
from agent_core.context_manager import ContextManager, ConversationMemoryStore, normalize_history
from agent_core.llm_client import GroqChatClient

__all__ = ["QueryTransformer"]


class QueryTransformer:
    def __init__(self, llm_client: Optional[Any] = None, model: Optional[str] = None):
        client = llm_client if llm_client is not None else GroqChatClient()
        # A private store: this adapter never reads or writes conversation memory.
        self._context = ContextManager(
            llm_client=client, store=ConversationMemoryStore(), model=model, use_memory=False
        )

    def translate_to_english(self, query: str) -> str:
        """Returns the English retrieval query, or the original text if translation is unavailable."""
        english, _notice = self._context.translate_for_retrieval(query, detect_language(query))
        return english

    def reformulate_query(self, query: str, chat_history: Optional[List[Dict[str, Any]]]) -> str:
        """Returns a standalone question, or the original text if reformulation is unavailable."""
        standalone, _notice = self._context.reformulate_query(query, normalize_history(chat_history))
        return standalone
