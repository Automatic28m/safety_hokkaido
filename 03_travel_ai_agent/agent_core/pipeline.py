import re

import requests

from data_integration.embedding_model import EmbeddingModel
from risk_knowledge.hybrid_retriever import HybridRetriever
from risk_knowledge.rerankers import Reranker
from decision_engine.generator import Generator
from agent_core.query_transform import QueryTransformer
from agent_core.memory import global_memory
from agent_core.router import Router
from config import config

# Node 04 owns the live-data adapters; node 03 is the only caller (node 07 has no network access).
try:
    from external_data.tools import get_real_time_weather, get_disaster_warnings, check_train_status
    TOOLS_IMPORT_ERROR = None
except Exception as exc:  # node 04 missing or broken: answer without live data, but say so
    get_real_time_weather = get_disaster_warnings = check_train_status = None
    TOOLS_IMPORT_ERROR = f"{exc.__class__.__name__}: {exc}"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
LLM_TIMEOUT_SECONDS = 30
REALTIME_ROUTES = ("realtime", "rag+realtime")
RAG_ROUTES = ("rag", "rag+realtime")
# Snapshot statuses meaning the live data the answer needed is missing or unreliable.
DEGRADED_SNAPSHOT_STATUSES = ("unavailable", "stale", "partial", "error")

DEFAULT_CITY = "Sapporo"
KNOWN_CITIES = {
    "sapporo": "Sapporo", "ซัปโปโร": "Sapporo", "ซัปโปะโระ": "Sapporo",
    "otaru": "Otaru", "โอตารุ": "Otaru",
    "hakodate": "Hakodate", "ฮาโกดาเตะ": "Hakodate",
    "asahikawa": "Asahikawa", "อาซาฮิคาวะ": "Asahikawa",
    "niseko": "Niseko", "นิเซโกะ": "Niseko",
    "furano": "Furano", "ฟูราโน่": "Furano", "ฟุราโนะ": "Furano",
    "obihiro": "Obihiro", "kushiro": "Kushiro", "chitose": "Chitose", "noboribetsu": "Noboribetsu",
}


class RAGPipeline:
    def __init__(self):
        print("Initializing Hokkaido RAG Pipeline components...")
        self.embedder = EmbeddingModel()
        self.retriever = HybridRetriever(self.embedder)

        # Respect the toggle switches in config.py
        if config.USE_RERANK:
            self.reranker = Reranker()
        else:
            self.reranker = None

        self.generator = Generator()
        self.transformer = QueryTransformer()
        self.router = Router()          # DL06: AI Router / Agent
        print("RAG Pipeline is online and ready!")

    # ── Public interface used by node 02 ────────────────────────────────────
    def ask_structured(self, request: dict) -> dict:
        """Node 02 contract: takes the normalized request, returns reply + safety metadata."""
        query = request["original_query"]
        enabled_agents = request.get("enabled_agents") or {}
        notices = []

        # ── MEMORY: API history is authoritative; server memory only for callers without history ──
        chat_history = self._history_without_current_query(request.get("chat_history") or [], query)
        use_server_memory = config.USE_MEMORY and not chat_history
        if use_server_memory:
            chat_history = list(global_memory.get_history())

        # ── DL06 ROUTER: classify intent before doing any heavy work ────────
        route = self.router.classify(query, chat_history)["route"]

        # ── DL05 QUERY REFORMULATION + LANGUAGE: English standalone query for retrieval ──
        standalone_query = self.transformer.reformulate_query(query, chat_history) if chat_history else query
        english_query = self.transformer.translate_to_english(standalone_query)
        print(f"[Pipeline] route='{route}' query='{english_query}'")

        # ── RAG RETRIEVAL (node 06) ─────────────────────────────────────────
        final_chunks = []
        if route in RAG_ROUTES:
            candidates = self.retriever.retrieve(english_query, top_k=config.RETRIEVER_TOP_K)
            if self.reranker and config.USE_RERANK:
                final_chunks = self.reranker.rerank(english_query, candidates, top_k=config.FINAL_TOP_K)
            else:
                final_chunks = candidates[:config.FINAL_TOP_K]
            if not final_chunks:
                notices.append("No matching safety documents were found.")
        evidence = [self._evidence_dict(chunk) for chunk in final_chunks]

        # ── LIVE TOOLS (node 04): node 03 calls them itself ─────────────────
        live_data_list = []
        if route in REALTIME_ROUTES:
            live_data_list = self._run_live_tools(enabled_agents, query + " " + english_query, notices)
        live_degraded = any(s.get("status") in DEGRADED_SNAPSHOT_STATUSES for s in live_data_list)
        live_sources = [self._public_snapshot(s) for s in live_data_list]

        # ── GENERATE: node 07 builds the prompt, node 03 calls Groq, node 07 parses ──
        messages = self.generator.format_prompt(
            query, chat_history, evidence, live_data_list, language=self._detect_language(query)
        )
        try:
            json_string_from_groq = self._call_llm(messages)
        except Exception as exc:
            print(f"[Pipeline] Decision LLM unavailable: {exc}")
            # Node 02 turns this into HTTP 503 with its own safe message.
            return {
                "status": "unavailable",
                "reply": "",
                "route": route,
                "safety_level": "unknown",
                "degraded": True,
                "notices": notices + [f"Decision LLM unavailable: {exc}"],
                "evidence": evidence,
                "live_sources": live_sources,
            }
        decision_dict = self.generator.parse_llm_response(json_string_from_groq)

        # ── MEMORY: save exchange ───────────────────────────────────────────
        if use_server_memory:
            global_memory.add_user_message(query)
            global_memory.add_ai_message(decision_dict["reply"])

        # ── Combine for node 02 ─────────────────────────────────────────────
        return {
            "status": "ok",
            "reply": decision_dict["reply"],
            "route": route,
            "safety_level": decision_dict["safety_level"],
            "degraded": bool(decision_dict["degraded"] or live_degraded),
            "notices": self._dedupe(notices + list(decision_dict["notices"])),
            "evidence": evidence,
            "live_sources": live_sources,
            "used_evidence_ids": decision_dict["used_evidence_ids"],
            "used_live_sources": decision_dict["used_live_sources"],
        }

    def ask(self, query: str, chat_history=None, enabled_agents=None):
        """Legacy interface: returns the reply text only."""
        result = self.ask_structured({
            "original_query": query,
            "chat_history": chat_history or [],
            "enabled_agents": enabled_agents or {},
        })
        return result["reply"]

    # ── Live data (node 04) ─────────────────────────────────────────────────
    def _run_live_tools(self, enabled_agents: dict, text: str, notices: list) -> list:
        if TOOLS_IMPORT_ERROR:
            notices.append(f"Live data unavailable: node 04 tools could not be imported ({TOOLS_IMPORT_ERROR}).")
            return []

        calls = []
        if enabled_agents.get("weather", True):
            city = self._detect_city(text)
            if city is None:
                city = DEFAULT_CITY
                notices.append(f"No city was mentioned; weather is for {DEFAULT_CITY}.")
            calls.append(("weather", get_real_time_weather, city))
        if enabled_agents.get("disaster", True):
            calls.append(("disaster", get_disaster_warnings, "Hokkaido"))
        if enabled_agents.get("train", True):
            calls.append(("train", check_train_status, "All"))

        live_data_list = []
        for name, tool, argument in calls:
            try:
                snapshot = tool(argument)
                live_data_list.append(snapshot.to_dict() if hasattr(snapshot, "to_dict") else dict(snapshot))
            except Exception as exc:  # one failing provider must not break the whole answer
                print(f"[Pipeline] Tool '{name}' failed: {exc}")
                live_data_list.append({
                    "provider": name,
                    "kind": name,
                    "status": "unavailable",
                    "data": {},
                    "notice": f"{name} tool failed: {exc.__class__.__name__}",
                })
        return live_data_list

    @staticmethod
    def _detect_city(text: str):
        lowered = text.lower()
        for name, city in KNOWN_CITIES.items():
            if name in lowered:
                return city
        return None

    # ── Decision LLM call (Groq) ────────────────────────────────────────────
    @staticmethod
    def _call_llm(messages: list) -> str:
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set")
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": config.LLM_MODEL,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"] or ""
        # Models sometimes wrap the JSON in prose or code fences; hand node 07 the object only.
        match = re.search(r"\{.*\}", content, re.DOTALL)
        return match.group(0) if match else content

    # ── Helpers ─────────────────────────────────────────────────────────────
    @staticmethod
    def _history_without_current_query(history: list, query: str) -> list:
        # Node 02 "messages" mode sends the current question as the last item; node 07 appends it itself.
        if history and history[-1].get("role") == "user" and history[-1].get("content") == query:
            return history[:-1]
        return history

    @staticmethod
    def _detect_language(text: str) -> str:
        return "th" if re.search(r"[฀-๿]", text) else "en"

    @staticmethod
    def _evidence_dict(chunk) -> dict:
        metadata = chunk.get("metadata") or {}
        if isinstance(metadata, dict):
            source = metadata.get("source_file")
        else:
            source = getattr(metadata, "source_file", None)
        return {
            "chunk_id": str(chunk.get("chunk_id") or "unknown_id"),
            "text": str(chunk.get("text") or ""),
            "source": source,
            "score": float(chunk.get("score") or 0.0),
        }

    @staticmethod
    def _public_snapshot(snapshot: dict) -> dict:
        keys = ("provider", "kind", "scope", "status", "fetched_at", "expires_at", "source_url", "notice")
        return {key: snapshot.get(key) for key in keys if snapshot.get(key) is not None}

    @staticmethod
    def _dedupe(items: list) -> list:
        seen = set()
        result = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result
