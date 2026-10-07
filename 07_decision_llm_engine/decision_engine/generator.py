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
4. Use ONLY the provided Evidence and Live Data for Hokkaido safety and travel facts. Do not use outside knowledge for safety facts. However, for greetings, polite small talk, or questions asking about your identity and capabilities as Tamago (e.g. 'สวัสดี', 'ตอบอะไรได้บ้าง', 'คุณเป็นใคร'), warmly introduce yourself and explain that you can help with Hokkaido weather, train status, flight delays, road conditions, and disaster emergency guidance. If the user asks an out-of-scope question and you do not have enough evidence to answer, you MUST apologize and state that you don't have the information IN THE EXACT SAME LANGUAGE AS THE USER'S QUERY.
5. CRITICAL LANGUAGE RULE: You MUST answer the user in the EXACT SAME LANGUAGE as their `original_query` (Hint: the user's preferred language code is '{language}'). If the user asks in English, you MUST reply in English. If they ask in Thai, reply in Thai. Do NOT reply in Japanese unless the user asked in Japanese. Always maintain your warm, polite, and reassuring female persona unless there is a severe warning, in which case be serious.
6. Output your user-facing text in Markdown format. Do not use HTML, JavaScript, or tables.

OUTPUT FORMAT:
You MUST output a strict JSON object (and nothing else) containing exactly the following keys:
- "reply": Your Markdown-formatted response to the user.
- "safety_level": Must be exactly one of: "unknown", "advisory", "urgent". If the user indicates they are currently trapped, in immediate danger, or actively experiencing a disaster (e.g., 'ติดอยู่ในอาคาร', 'แผ่นดินไหวตอนนี้'), you MUST output "safety_level": "urgent".
- "used_evidence_ids": A list of strings containing the chunk_id of any Evidence you relied on.
- "used_live_sources": A list of strings containing the provider names of any Live Data you relied on.
- "degraded": boolean (true if any provided dependency was unavailable or missing).
- "notices": A list of strings explaining any data limitations to the user (e.g., "Train data is mocked", "Weather provider offline").
- "route_intent": If the user asks for travel routes or directions, you MUST output an object containing "origin", "destination", and "mode" (train, bus, or car). Otherwise, output null.

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
    route_intent: Optional[dict] = None

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
            # Strip markdown code blocks if present
            raw = json_str.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            
            # Extract JSON object bounded by outermost braces
            s_idx = raw.find('{')
            e_idx = raw.rfind('}')
            if s_idx != -1 and e_idx != -1:
                raw = raw[s_idx:e_idx+1]

            # 1. Parse JSON
            try:
                decision_dict = json.loads(raw, strict=False)
            except Exception:
                reply_match = re.search(r'"reply"\s*:\s*"(.*?)(?:"\s*,\s*"[a-zA-Z_]+|\s*"\s*\}|\s*$)', raw, re.DOTALL)
                if reply_match:
                    extracted_reply = reply_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                    decision_dict = {"reply": extracted_reply}
                else:
                    raise

            if not isinstance(decision_dict, dict):
                decision_dict = {"reply": str(decision_dict)}
                
            # Ensure required schema fields exist with defaults
            if "reply" not in decision_dict:
                decision_dict["reply"] = str(decision_dict.get("message", decision_dict.get("answer", "")))
            if "safety_level" not in decision_dict:
                decision_dict["safety_level"] = "unknown"
            if "used_evidence_ids" not in decision_dict or not isinstance(decision_dict["used_evidence_ids"], list):
                decision_dict["used_evidence_ids"] = []
            if "used_live_sources" not in decision_dict or not isinstance(decision_dict["used_live_sources"], list):
                decision_dict["used_live_sources"] = []
            if "degraded" not in decision_dict:
                decision_dict["degraded"] = False
            if "notices" not in decision_dict or not isinstance(decision_dict["notices"], list):
                decision_dict["notices"] = []
            if "route_intent" not in decision_dict:
                decision_dict["route_intent"] = None
            
            # 2. Strict Schema Validation (fallback to manual if pydantic missing)
            if BaseModel is not object:
                decision = DecisionResponse(**decision_dict)
                reply = decision.reply
                safety_level = decision.safety_level
                used_evidence_ids = decision.used_evidence_ids
                used_live_sources = decision.used_live_sources
                degraded = decision.degraded
                notices = decision.notices
                route_intent = decision.route_intent
            else:
                reply = str(decision_dict.get("reply", ""))
                safety_level = str(decision_dict.get("safety_level", "unknown"))
                used_evidence_ids = list(decision_dict.get("used_evidence_ids", []))
                used_live_sources = list(decision_dict.get("used_live_sources", []))
                degraded = bool(decision_dict.get("degraded", False))
                notices = list(decision_dict.get("notices", []))
                route_intent = decision_dict.get("route_intent", None)
            
            # 3. HTML/JS Sanitization (Strip tags)
            safe_reply = re.sub(r'<[^>]+>', '', reply)
            
            return {
                "reply": safe_reply,
                "safety_level": safety_level,
                "used_evidence_ids": used_evidence_ids,
                "used_live_sources": used_live_sources,
                "degraded": degraded,
                "notices": notices,
                "route_intent": route_intent
            }
            
        except Exception as e:
            print(f"[Generator Parse Error] {e}")
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
            "notices": [f"Fallback activated: {reason}"],
            "route_intent": None
        }
