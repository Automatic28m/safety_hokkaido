import re
import json
import requests
from typing import Optional
from config import config

# ---------------------------------------------------------------------------
# Router System Prompt
# Instructs a small, fast LLM to classify the user's intent into a route.
# ---------------------------------------------------------------------------
ROUTER_SYSTEM_PROMPT = """
You are an intent classifier for a Hokkaido disaster safety application.
Your job is to read the user's question and decide the BEST route to answer it.

Available routes:
- "general"      → General travel or knowledge questions that don't need live data or safety docs.
                   (e.g. "What is Hokkaido famous for?", "How do I say hello in Japanese?")
- "rag"          → Questions about disaster safety, blizzard survival, earthquake, tsunami,
                   frostbite, evacuation procedures, or emergency contacts.
                   (e.g. "What do I do during a blizzard?", "How do I evacuate from a tsunami?")
- "realtime"     → Questions that need live, up-to-date data: current weather, active earthquake
                   alerts, or live train status.
                   (e.g. "Is it snowing in Sapporo right now?", "Are JR trains running today?")
- "rag+realtime" → Questions that need BOTH safety guidance AND live data.
                   (e.g. "Is it safe to drive to Otaru right now?", "Should I take the train given the earthquake warning?")

You MUST reply with ONLY valid JSON and nothing else. No markdown, no explanation.
Format: 
{ 
  "route": "<route>", 
  "confidence": <0.0-1.0>, 
  "reasoning": "<brief reason>",
  "target_city": "<City name in English if mentioned (e.g. Sapporo, Hakodate, Niseko), else null>",
  "route_intent": {
    "origin": "<start in English>",
    "destination": "<end in English>",
    "mode": "<train|bus|car>"
  },
  "ui_widget": {
    "widget_type": "<weather_forecast|flight_board>",
    "payload": { "<key>": "<value>" }
  }
}

(Note for route_intent: If the user mentions travel from A to B, extract it and translate to ENGLISH. If no travel is mentioned, route_intent MUST be null.)

(Note for ui_widget: ONLY output this if the user requests extensive data like 'hourly forecast', 'all arriving flights', or 'flight board'. Do not trigger for simple questions like 'is it cold?' or 'is my flight delayed?'. Set to null if not needed.
Example payload for weather: {"location": "Sapporo"}
Example payload for flights: {"airport": "CTS", "direction": "arrival"})

Example 1 (No directions or widgets):
{ "route": "rag", "confidence": 0.97, "reasoning": "User asked about earthquake evacuation steps.", "target_city": null, "route_intent": null, "ui_widget": null }

Example 2 (Asking for directions):
{ "route": "general", "confidence": 0.99, "reasoning": "User asking how to travel between two cities.", "target_city": "Sapporo", "route_intent": { "origin": "Chitose Airport", "destination": "Sapporo", "mode": "train" }, "ui_widget": null }

Example 3 (Asking for detailed weather forecast):
{ "route": "realtime", "confidence": 0.99, "reasoning": "User explicitly asked for the hourly weather forecast.", "target_city": "Niseko", "route_intent": null, "ui_widget": { "widget_type": "weather_forecast", "payload": { "location": "Niseko" } } }
"""

# ---------------------------------------------------------------------------
# Keyword fallback rules (used when LLM confidence is below threshold)
# ---------------------------------------------------------------------------
KEYWORD_RULES = {
    "realtime": [
        "right now", "currently", "today", "at the moment", "live",
        "weather", "raining", "snowing", "temperature", "forecast",
        "train", "delay", "cancelled", "running", "jr",
        "earthquake now", "warning now", "alert now", "is it safe now",
        "อากาศ", "สภาพอากาศ", "ฝน", "หิมะ", "อุณหภูมิ", "พยากรณ์", "หนาว",
        "รถไฟ", "ดีเลย์", "ยกเลิก", "ตอนนี้", "วันนี้", "เดินทางได้ไหม",
        "ปลอดภัยไหม", "เที่ยวบิน", "สนามบิน", "ถนน", "ปิดทาง"
    ],
    "rag": [
        "earthquake", "tsunami", "blizzard", "snowstorm", "frostbite",
        "hypothermia", "evacuate", "evacuation", "shelter", "emergency",
        "disaster", "trapped", "stuck", "hurt", "injured", "shaking",
        "safe", "danger", "warning", "what should i do", "what do i do",
        "help", "ambulance", "police", "119", "110",
        "แผ่นดินไหว", "สึนามิ", "พายุหิมะ", "หนาวจัด", "อพยพ", "ที่หลบภัย",
        "ฉุกเฉิน", "ภัยพิบัติ", "ติดอยู่", "บาดเจ็บ", "ปลอดภัย", "อันตราย",
        "เตือนภัย", "ช่วยด้วย", "กู้ภัย", "ตำรวจ"
    ],
}

CONFIDENCE_THRESHOLD = 0.70


class Router:
    """
    AI Router / Agent — classifies user intent and selects the best route.

    Routes:
        "general"      → Answer with Groq only (no RAG, no tools)
        "rag"          → Answer using safety document retrieval only
        "realtime"     → Answer using live tools (weather, disaster, train)
        "rag+realtime" → Answer using BOTH safety docs AND live tools
    """

    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = config.GROQ_API_KEY
        self.router_model = getattr(config, "LLM_MODEL", "openai/gpt-oss-120b")

    def classify(self, query: str, chat_history: list = None) -> dict:
        """
        Classifies the user query and returns a routing decision.
        """
        messages = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]

        # Give the router a short view of recent history for context
        if chat_history:
            for msg in chat_history[-4:]:
                role = "assistant" if msg["role"] == "ai" else msg["role"]
                messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": query})

        try:
            raw = None
            if self.api_key:
                for model_candidate in [self.router_model, "openai/gpt-oss-20b"]:
                    try:
                        response = requests.post(
                            self.api_url,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": model_candidate,
                                "messages": messages,
                                "temperature": 0.0,
                                "max_tokens": 512,
                            },
                            timeout=10
                        )
                        if response.status_code == 200:
                            raw = response.json()
                            break
                        elif response.status_code in (413, 429):
                            print(f"[Router Groq {model_candidate}] {response.status_code}. Trying fallback...")
                    except Exception as e:
                        print(f"[Router Groq Error] {e}")

            # Fallback to Gemini if Groq failed or not configured
            if (not raw or "choices" not in raw) and getattr(config, "GEMINI_API_KEY", ""):
                try:
                    gemini_res = requests.post(
                        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                        headers={
                            "Authorization": f"Bearer {config.GEMINI_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": getattr(config, "GEMINI_MODEL", "gemini-3.8-flash"),
                            "messages": messages,
                            "temperature": 0.0,
                            "max_tokens": 512,
                            "response_format": {"type": "json_object"}
                        },
                        timeout=10
                    )
                    if gemini_res.status_code == 200:
                        raw = gemini_res.json()
                except Exception as eg:
                    print(f"[Router Gemini Error] {eg}")

            # Bug fix: guard against API errors that return no 'choices'
            if not raw or "choices" not in raw:
                raise ValueError(f"Router API error: {raw.get('error', raw) if raw else 'No response'}")

            content = raw["choices"][0]["message"]["content"]

            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx == -1 or end_idx == -1:
                raise ValueError(f"No JSON found in router response: {content}")

            json_str = content[start_idx:end_idx+1]
            
            try:
                result = json.loads(json_str)
            except Exception as e:
                print(f"[Router Error] Failed to parse JSON: {e}")
                print(f"[Router Error] Raw string was: {json_str}")
                raise

            print(f"[Router Debug] Raw LLM Output: {result}")

            if "route" not in result:
                raise ValueError(f"Router response missing 'route': {result}")

            # Apply keyword fallback if confidence is too low
            confidence = result.get("confidence", 1.0)
            if confidence < CONFIDENCE_THRESHOLD:
                fallback_route, detected_city = self._keyword_fallback(query)
                if fallback_route:
                    print(f"[Router] Low confidence ({confidence:.2f}). Keyword fallback → '{fallback_route}'")
                    result["route"] = fallback_route
                    result["reasoning"] = "[Keyword fallback] Overrode low-confidence LLM route."
                    if not result.get("target_city") and detected_city:
                        result["target_city"] = detected_city

            # Ensure optional fields are explicitly in the result
            result["route_intent"] = result.get("route_intent", None)
            result["ui_widget"] = result.get("ui_widget", None)
            result["target_city"] = result.get("target_city", None)

            print(
                f"[Router] Route='{result['route']}' | "
                f"Confidence={result.get('confidence', '?')} | "
                f"Reason: {result.get('reasoning', '')}"
            )
            return result

        except Exception as e:
            print(f"[Router] Classification failed: {e}")
            fallback_route, detected_city = self._keyword_fallback(query)
            if fallback_route:
                print(f"[Router] System error. Keyword fallback → '{fallback_route}' (City: {detected_city})")
                return {
                    "route": fallback_route,
                    "confidence": 0.8,
                    "reasoning": f"Router error — rescued by keyword fallback. City: {detected_city}",
                    "route_intent": None,
                    "ui_widget": {"widget_type": "weather_forecast", "payload": {"location": detected_city}} if detected_city and ("weather" in query.lower() or "อากาศ" in query) else None,
                    "target_city": detected_city
                }
            
            print("[Router] Defaulting to 'rag'.")
            return {
                "route": "rag",
                "confidence": 0.5,
                "reasoning": "Router error — safe default to RAG.",
                "route_intent": None,
                "ui_widget": None,
                "target_city": detected_city
            }

    def _keyword_fallback(self, query: str) -> tuple[Optional[str], Optional[str]]:
        """
        Simple keyword-based rule fallback when LLM confidence is low or API fails.
        Returns (matched_route, detected_city).
        """
        q = query.lower()
        realtime_hit = any(kw in q or kw in query for kw in KEYWORD_RULES["realtime"])
        rag_hit = any(kw in q or kw in query for kw in KEYWORD_RULES["rag"])

        detected_city = None
        if "otaru" in q or "โอตารุ" in query:
            detected_city = "Otaru"
        elif "sapporo" in q or "ซัปโปโร" in query:
            detected_city = "Sapporo"
        elif "hakodate" in q or "ฮาโกดาเตะ" in query:
            detected_city = "Hakodate"
        elif "asahikawa" in q or "อาซาฮิกาวะ" in query:
            detected_city = "Asahikawa"
        elif "niseko" in q or "นิเซโกะ" in query:
            detected_city = "Niseko"
        elif "chitose" in q or "ชิโตเสะ" in query:
            detected_city = "New Chitose Airport"
        elif "furano" in q or "ฟุราโนะ" in query:
            detected_city = "Furano"
        elif "noboribetsu" in q or "โนโบริเบทสึ" in query:
            detected_city = "Noboribetsu"
        elif "kushiro" in q or "คุชิโระ" in query:
            detected_city = "Kushiro"

        matched_route = None
        if realtime_hit and rag_hit:
            matched_route = "rag+realtime"
        elif realtime_hit:
            matched_route = "realtime"
        elif rag_hit:
            matched_route = "rag"

        return matched_route, detected_city
