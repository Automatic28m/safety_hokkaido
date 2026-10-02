import requests
from datetime import datetime
from external_data.models import LiveDataSnapshot

from data_integration.embedding_model import EmbeddingModel
from risk_knowledge.hybrid_retriever import HybridRetriever
from risk_knowledge.rerankers import Reranker
from decision_engine.generator import Generator
from external_data.tools import get_real_time_weather, get_disaster_warnings, check_train_status
from agent_core.query_transform import QueryTransformer
from agent_core.memory import ConversationMemory
from agent_core.router import Router
from config import config


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

    def ask_structured(self, request: dict) -> dict:
        query = request["original_query"]
        raw_history = request.get("chat_history") or []
        enabled_agents = request.get("enabled_agents")

        # Exclude the last message if it's the current query to avoid duplication
        if raw_history and raw_history[-1].get("role") == "user" and raw_history[-1].get("content") == query:
            past_history = raw_history[:-1]
        else:
            past_history = raw_history

        # ── MEMORY: load conversation history ───────────────────────────────
        if config.USE_MEMORY:
            mem = ConversationMemory()
            for m in past_history:
                if m.get("role") == "user":
                    mem.add_user_message(m.get("content", ""))
                else:
                    mem.add_ai_message(m.get("content", ""))
            chat_history = mem.get_history()
        else:
            chat_history = past_history

        # ── DL06 ROUTER: classify intent before doing any heavy work ────────
        route_result = self.router.classify(query, chat_history)
        route = route_result["route"]   # "general" | "rag" | "realtime" | "rag+realtime"
        route_intent = route_result.get("route_intent")

        # ── DL05 QUERY REFORMULATION: make standalone if needed ─────────────
        if config.USE_MEMORY and chat_history:
            standalone_query = self.transformer.reformulate_query(query, chat_history)
            print(f"[Reformulation] '{query}' → '{standalone_query}'")
        else:
            standalone_query = query

        # ── LANGUAGE: translate to English for retrieval ─────────────────────
        english_query = self.transformer.translate_to_english(standalone_query)
        print(f"[Language] '{standalone_query}' → '{english_query}'")

        # ── RAG RETRIEVAL: only run if the router says we need docs ─────────
        final_chunks = []
        if route in ("rag", "rag+realtime"):
            print(f"[Pipeline] Route='{route}' → Activating RAG retrieval.")
            candidates = self.retriever.retrieve(english_query, top_k=config.RETRIEVER_TOP_K)
            if self.reranker and config.USE_RERANK:
                final_chunks = self.reranker.rerank(english_query, candidates, top_k=config.FINAL_TOP_K)
            else:
                final_chunks = candidates[:config.FINAL_TOP_K]
        else:
            print(f"[Pipeline] Route='{route}' → Skipping RAG retrieval.")

        # ── TOOLS: only activate real-time tools if the router says so ──────
        if route in ("realtime", "rag+realtime"):
            print(f"[Pipeline] Route='{route}' → Activating real-time tools.")
            active_agents = {"weather": True, "disaster": True, "train": True}
        else:
            print(f"[Pipeline] Route='{route}' → Skipping real-time tools.")
            active_agents = {"weather": False, "disaster": False, "train": False}

        # Allow the API caller to still override tools (e.g. frontend toggles)
        if enabled_agents is not None:
            for key in enabled_agents:
                if not enabled_agents[key]:
                    active_agents[key] = False

        # ── LIVE DATA: node 03 runs the node 04 tools itself ────────────────
        live_data_list = []
        if active_agents.get("weather"):
            live_data_list.append(get_real_time_weather("Sapporo"))
        if active_agents.get("disaster"):
            live_data_list.append(get_disaster_warnings())
        if active_agents.get("train"):
            live_data_list.append(check_train_status("All"))

        # ── SYSTEM UI NOTE: tell Node 07 if a map was opened ─────────────────
        if route_intent:
            ui_note = LiveDataSnapshot(
                provider="SystemUI",
                kind="ui_action",
                scope={"region": "Local"},
                status="ok",
                fetched_at=datetime.utcnow().isoformat() + "Z",
                expires_at=datetime.utcnow().isoformat() + "Z",
                data={"summary": f"System has successfully opened an interactive map and Google Maps navigation button for the route from {route_intent.get('origin', 'A')} to {route_intent.get('destination', 'B')} by {route_intent.get('mode', 'vehicle')} on the right side of the screen. Acknowledge this to the user briefly."}
            )
            live_data_list.append(ui_note)

        # ── GENERATE: node 07 prompt -> Groq -> node 07 parse ───────────────
        messages = self.generator.format_prompt(query, chat_history, final_chunks, live_data_list)
        json_string_from_groq = self._call_groq(messages)
        decision_dict = self.generator.parse_llm_response(json_string_from_groq)

        # ── RESULT: combine the decision with the chunks and live data for node 02 ──
        return {
            "reply": decision_dict["reply"],
            "safety_level": decision_dict["safety_level"],
            "evidence": [chunk.to_dict() for chunk in final_chunks],
            "live_sources": [snapshot.to_dict() for snapshot in live_data_list],
            "degraded": decision_dict["degraded"],
            "notices": decision_dict["notices"],
            "route_intent": route_intent,
        }

    def ask(self, query: str, chat_history=None, enabled_agents=None):
        return self.ask_structured({
            "original_query": query,
            "chat_history": chat_history,
            "enabled_agents": enabled_agents,
        })["reply"]

    def _call_groq(self, messages: list) -> str:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.LLM_MODEL,
                "messages": messages,
            },
        )
        return response.json()["choices"][0]["message"]["content"]
