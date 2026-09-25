import requests
import json
import os
from config import config  # Inheriting global settings (like GROQ_API_KEY) from the root config

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

class Generator:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = config.LLM_MODEL

    def generate(self, original_query, history=None, evidence=None, live_data=None, tool_policy=None, language="th"):
        """
        Node 07: Controlled Synthesizer.
        Takes pre-fetched evidence and live_data (from Node 03) and generates a structured JSON decision.
        """
        if not config.USE_LLM:
            return {
                "reply": "DEBUG MODE (LLM OFF)",
                "safety_level": "unknown",
                "used_evidence_ids": [],
                "used_live_sources": [],
                "degraded": True,
                "notices": ["LLM is disabled in config."]
            }

        evidence = evidence or []
        live_data = live_data or []
        history = history or []

        # 1. Format the provided Context
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
        
        # 2. Build the strict System Prompt using Module 07's isolated prompt
        system_prompt = DECISION_SYSTEM_PROMPT.replace("{context}", context_str).replace("{language}", language)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 3. Append User History
        recent_history = history[-6:]
        for msg in recent_history:
            role = "assistant" if msg["role"] == "ai" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})
        
        messages.append({"role": "user", "content": original_query})
        
        # 4. Prepare the Payload for Groq (Enforcing JSON Mode)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for strict adherence to guardrails
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 5. Make a SINGLE call to the LLM (No tool execution!)
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)
            
            if response.status_code != 200:
                print(f"[Generator] Groq API Error: {response.text}")
                return self._fallback_response("Groq API returned an error.")
                
            response_data = response.json()
            json_str = response_data["choices"][0]["message"]["content"]
            
            # 6. Parse and validate the JSON output
            decision = json.loads(json_str)
            
            # Ensure all contract fields are present
            return {
                "reply": decision.get("reply", "No reply generated."),
                "safety_level": decision.get("safety_level", "unknown"),
                "used_evidence_ids": decision.get("used_evidence_ids", []),
                "used_live_sources": decision.get("used_live_sources", []),
                "degraded": decision.get("degraded", False),
                "notices": decision.get("notices", [])
            }
            
        except json.JSONDecodeError:
            print("[Generator] LLM failed to output valid JSON.")
            return self._fallback_response("LLM hallucinated invalid JSON.")
        except requests.exceptions.RequestException as e:
            print(f"[Generator] Network error calling Groq: {e}")
            return self._fallback_response("Network timeout calling Groq API.")
            
    def _fallback_response(self, reason):
        return {
            "reply": "I am experiencing technical difficulties and cannot safely process your request at this moment. If you are in an emergency, please contact 119 or 110 immediately.",
            "safety_level": "unknown",
            "used_evidence_ids": [],
            "used_live_sources": [],
            "degraded": True,
            "notices": [f"Fallback activated: {reason}"]
        }
