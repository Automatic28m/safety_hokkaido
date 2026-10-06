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
        "earthquake now", "warning now", "alert now", "is it safe now"
    ],
    "rag": [
        "earthquake", "tsunami", "blizzard", "snowstorm", "frostbite",
        "hypothermia", "evacuate", "evacuation", "shelter", "emergency",
        "disaster", "trapped", "stuck", "hurt", "injured", "shaking",
        "safe", "danger", "warning", "what should i do", "what do i do",
        "help", "ambulance", "police", "119", "110"
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
        # Use a smaller, cheaper, faster model for routing only
        self.router_model = "qwen/qwen3.8-27b"   # Use Qwen 27B model for routing

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
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.router_model,
                    "messages": messages,
                    "temperature": 0.0,
                    "max_tokens": 512,
                    # NOTE: response_format json_object is NOT supported by all models
                    # We parse JSON manually from the raw text instead
                },
                timeout=10
            )

            raw = response.json()

            # Bug fix: guard against API errors that return no 'choices'
            if "choices" not in raw:
                raise ValueError(f"Groq router API error: {raw.get('error', raw)}")

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
                fallback_route = self._keyword_fallback(query)
                if fallback_route:
                    print(f"[Router] Low confidence ({confidence:.2f}). Keyword fallback → '{fallback_route}'")
                    result["route"] = fallback_route
                    result["reasoning"] = "[Keyword fallback] Overrode low-confidence LLM route."

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
            fallback_route = self._keyword_fallback(query)
            if fallback_route:
                print(f"[Router] System error. Keyword fallback → '{fallback_route}'")
                return {
                    "route": fallback_route,
                    "confidence": 0.5,
                    "reasoning": "Router error — rescued by keyword fallback.",
                    "route_intent": None,
                    "ui_widget": None,
                    "target_city": None
                }
            
            print("[Router] Defaulting to 'rag'.")
            return {
                "route": "rag",
                "confidence": 0.5,
                "reasoning": "Router error — safe default to RAG.",
                "route_intent": None,
                "ui_widget": None,
                "target_city": None
            }

    def _keyword_fallback(self, query: str) -> Optional[str]:
        """
        Simple keyword-based rule fallback when LLM confidence is low.
        Returns the matched route, or None if no keywords matched.
        """
        q = query.lower()
        realtime_hit = any(kw in q for kw in KEYWORD_RULES["realtime"])
        rag_hit = any(kw in q for kw in KEYWORD_RULES["rag"])

        if realtime_hit and rag_hit:
            return "rag+realtime"
        elif realtime_hit:
            return "realtime"
        elif rag_hit:
            return "rag"
        return None
