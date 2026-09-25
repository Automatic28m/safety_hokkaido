import json
import re
from typing import List, Optional
try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    BaseModel = object

# Module 07 Owns Its Prompt (Decoupled from Node 02)
DECISION_SYSTEM_PROMPT = """You are Tamago, a friendly, warm, and helpful female AI guide for Hokkaido tourists. 
While you are very polite and sweet, your absolute priority is tourist safety during disasters and extreme weather.

STRICT ANTI-HALLUCINATION RULES:
1. NEVER guess or invent the reasons for an action. You must state the exact consequences provided in the Evidence and Live Data.
2. Pay strict attention to the user's CURRENT situation. If they state they are already "stuck", "trapped", or "lost", DO NOT provide preventative advice meant for people who are still moving.
3. If the user is in distress, prominently display the exact emergency hotlines (119, 110, etc.) ONLY if they are found in the context.
4. Use ONLY the provided Evidence and Live Data to formulate your answer. Do not use outside knowledge. If the context does not contain the answer, explicitly state: "I'm sorry, I don't have enough information to advise on that right now."
5. CRITICAL LANGUAGE RULE: You MUST answer the user in the language they used in their query (e.g., '{language}'). Always maintain your warm, polite, and reassuring female persona unless there is a severe warning, in which case be serious.
6. Output your user-facing text in Markdown format. Do not use HTML, JavaScript, or tables.

OUTPUT FORMAT:
You MUST output a strict JSON object (and nothing else) containing exactly the following keys:
- "reply": Your Markdown-formatted response to the user.
- "safety_level": Must be exactly one of: "unknown", "advisory", "urgent".
- "used_evidence_ids": A list of strings containing the chunk_id of any Evidence you relied on.
- "used_live_sources": A list of strings containing the provider names of any Live Data you relied on.
- "degraded": boolean (true if any provided dependency was unavailable or missing).
- "notices": A list of strings explaining any data limitations to the user (e.g., "Train data is mocked", "Weather provider offline").

Context (Evidence & Live Data):
{context}
"""

class DecisionResponse(BaseModel if BaseModel is not object else object):
    reply: str
    safety_level: str
    used_evidence_ids: List[str]
    used_live_sources: List[str]
    degraded: bool
    notices: List[str]

class Generator:
    """
    Node 07: Controlled Synthesizer.
    Purely functional module. Does NOT make network calls.
    """
    
    def format_prompt(self, original_query: str, history=None, evidence=None, live_data=None, tool_policy=None, language="th") -> list:
        """
        Formats the strict prompt and context block. 
        Returns the messages array ready to be sent to the LLM by the orchestration layer.
        """
        evidence = evidence or []
        live_data = live_data or []
        history = history or []

        context_blocks = []
        if evidence:
            context_blocks.append("--- VERIFIED EVIDENCE ---")
            for chunk in evidence:
                chunk_id = chunk.get("chunk_id", "unknown_id")
                text = chunk.get("text", "")
                context_blocks.append(f"[Evidence ID: {chunk_id}]\n{text}")

        if live_data:
            context_blocks.append("--- LIVE DATA SNAPSHOTS ---")
            for snapshot in live_data:
                provider = snapshot.get("provider", "Unknown")
                status = snapshot.get("status", "unknown")
                data = snapshot.get("data", {})
                context_blocks.append(f"[Live Source: {provider} | Status: {status}]\n{json.dumps(data, ensure_ascii=False)}")

        context_str = "\n\n".join(context_blocks) if context_blocks else "No evidence or live data provided."
        
        system_prompt = DECISION_SYSTEM_PROMPT.replace("{context}", context_str).replace("{language}", language)
        messages = [{"role": "system", "content": system_prompt}]
        
        recent_history = history[-6:]
        for msg in recent_history:
            role = "assistant" if msg["role"] == "ai" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})
        
        messages.append({"role": "user", "content": original_query})
        
        return messages

    def parse_llm_response(self, json_str: str) -> dict:
        """
        Parses the JSON returned by the LLM, validates the schema, and sanitizes HTML.
        """
        try:
            # 1. Parse JSON
            decision_dict = json.loads(json_str)
            
            # 2. Strict Schema Validation (fallback to manual if pydantic missing)
            if BaseModel is not object:
                decision = DecisionResponse(**decision_dict)
                reply = decision.reply
                safety_level = decision.safety_level
                used_evidence_ids = decision.used_evidence_ids
                used_live_sources = decision.used_live_sources
                degraded = decision.degraded
                notices = decision.notices
            else:
                reply = str(decision_dict.get("reply", ""))
                safety_level = str(decision_dict.get("safety_level", "unknown"))
                used_evidence_ids = list(decision_dict.get("used_evidence_ids", []))
                used_live_sources = list(decision_dict.get("used_live_sources", []))
                degraded = bool(decision_dict.get("degraded", False))
                notices = list(decision_dict.get("notices", []))
            
            # 3. HTML/JS Sanitization (Strip tags)
            safe_reply = re.sub(r'<[^>]+>', '', reply)
            
            return {
                "reply": safe_reply,
                "safety_level": safety_level,
                "used_evidence_ids": used_evidence_ids,
                "used_live_sources": used_live_sources,
                "degraded": degraded,
                "notices": notices
            }
            
        except Exception as e:
            return self.get_fallback_response(f"Validation or parsing failed: {str(e)}")

    def get_fallback_response(self, reason: str) -> dict:
        """
        Guarantees a safe fallback dictionary if anything goes wrong.
        """
        return {
            "reply": "I am experiencing technical difficulties and cannot safely process your request at this moment. If you are in an emergency, please contact 119 or 110 immediately.",
            "safety_level": "unknown",
            "used_evidence_ids": [],
            "used_live_sources": [],
            "degraded": True,
            "notices": [f"Fallback activated: {reason}"]
        }
