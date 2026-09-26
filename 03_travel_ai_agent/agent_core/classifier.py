"""Intent analysis for node 03.

Responsibilities (and nothing more):
* classify the user's message into one of the four routes,
* say which context the route needs (retrieval / live data),
* detect the user's language,
* extract the primitive slots (city / region / line) node 04 adapters accept.

Routing is an optimization, never a safety authority. Every fallback is
recorded in ``RouteDecision.fallback_used`` so it can be audited.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from agent_core.llm_client import LLMClientError, extract_json_object
from agent_core.schemas import ROUTES, TOOL_NAMES, RouteDecision
from agent_core.settings import config_value, provider_ready

logger = logging.getLogger("travel_ai_agent")

DEFAULT_ROUTER_MODEL = "openai/gpt-oss-20b"
CONFIDENCE_THRESHOLD = 0.70
SAFE_DEFAULT_ROUTE = "rag"

ROUTER_SYSTEM_PROMPT = """
You are an intent classifier for a Hokkaido disaster safety application.
Read the user's question and decide the BEST route to answer it.

Available routes:
- "general"      -> General travel or knowledge questions that need neither live data nor safety documents.
- "rag"          -> Disaster safety guidance: blizzard, earthquake, tsunami, frostbite, evacuation, emergency contacts.
- "realtime"     -> Needs live data only: current weather, active earthquake alerts, live train status.
- "rag+realtime" -> Needs BOTH safety guidance AND live data (e.g. "Is it safe to drive to Otaru right now?").

Also list which live tools are needed, from: "weather", "disaster", "train".
For "realtime" and "rag+realtime" name at least one tool; for other routes use an empty list.

Reply with ONLY valid JSON, no markdown, no explanation:
{ "route": "<route>", "confidence": <0.0-1.0>, "reasoning": "<brief reason>", "tools": ["weather"] }
"""

KEYWORD_RULES: Dict[str, List[str]] = {
    "realtime": [
        "right now", "currently", "today", "tonight", "at the moment", "live data",
        "weather", "raining", "snowing", "temperature", "forecast", "wind", "windy",
        "train", "delay", "delayed", "cancelled", "running", "jr",
        "earthquake now", "warning now", "alert now", "is it safe now",
        "ตอนนี้", "วันนี้", "คืนนี้", "อากาศ", "หิมะตก", "ฝนตก", "อุณหภูมิ", "พยากรณ์",
        "รถไฟ", "ล่าช้า", "ดีเลย์", "ยกเลิก", "วิ่งไหม",
    ],
    "rag": [
        "earthquake", "tsunami", "blizzard", "snowstorm", "whiteout", "frostbite",
        "hypothermia", "evacuate", "evacuation", "shelter", "emergency",
        "disaster", "trapped", "stuck", "hurt", "injured", "shaking",
        "safe", "danger", "warning", "what should i do", "what do i do",
        "help", "ambulance", "police", "119", "110",
        "แผ่นดินไหว", "สึนามิ", "พายุหิมะ", "หิมะถล่ม", "อพยพ", "หลบภัย", "ฉุกเฉิน",
        "ภัยพิบัติ", "ติดอยู่", "ติดหิมะ", "บาดเจ็บ", "ปลอดภัย", "อันตราย", "เตือนภัย",
        "ควรทำอย่างไร", "ทำยังไง", "ช่วยด้วย", "รถพยาบาล", "ตำรวจ",
    ],
}

TOOL_KEYWORDS: Dict[str, List[str]] = {
    "weather": [
        "weather", "snow", "snowing", "snowfall", "snowy", "rain", "raining", "temperature",
        "forecast", "wind", "windy", "cold", "storm", "drive", "driving", "road", "roads", "visibility",
        "อากาศ", "หิมะ", "ฝน", "อุณหภูมิ", "ลม", "หนาว", "ขับรถ", "ถนน", "พยากรณ์",
    ],
    "disaster": [
        "earthquake", "quake", "tsunami", "warning", "alert", "blizzard", "eruption", "aftershock",
        "แผ่นดินไหว", "สึนามิ", "เตือนภัย", "พายุหิมะ", "อาฟเตอร์ช็อก", "ภูเขาไฟ",
    ],
    "train": [
        "train", "jr", "rail", "railway", "airport", "chitose", "delay", "express", "shinkansen",
        "รถไฟ", "สนามบิน", "ชิโตเสะ", "ล่าช้า", "ดีเลย์", "ชินคันเซ็น",
    ],
}

# Hokkaido place names node 04 accepts as a weather scope, with common Thai spellings.
KNOWN_CITIES: Dict[str, List[str]] = {
    "Sapporo": ["sapporo", "ซัปโปโร", "ซับโปโร", "札幌"],
    "Otaru": ["otaru", "โอตารุ", "小樽"],
    "Hakodate": ["hakodate", "ฮาโกดาเตะ", "ฮาโกะดาเตะ", "函館"],
    "Asahikawa": ["asahikawa", "อาซาฮิกาวะ", "อาซาฮิคาวะ", "旭川"],
    "Niseko": ["niseko", "นิเซโกะ", "ニセコ"],
    "Furano": ["furano", "ฟูราโนะ", "富良野"],
    "Biei": ["biei", "บิเอะ", "美瑛"],
    "Obihiro": ["obihiro", "โอบิฮิโระ", "帯広"],
    "Kushiro": ["kushiro", "คุชิโระ", "釧路"],
    "Wakkanai": ["wakkanai", "วักกะไน", "稚内"],
    "Abashiri": ["abashiri", "อาบาชิริ", "網走"],
    "Kitami": ["kitami", "คิตามิ", "北見"],
    "Nemuro": ["nemuro", "เนมูโระ", "根室"],
    "Muroran": ["muroran", "มูโรรัน", "室蘭"],
    "Tomakomai": ["tomakomai", "โทมาโกไม", "苫小牧"],
    "Noboribetsu": ["noboribetsu", "โนโบริเบ็ตสึ", "登別"],
    "Chitose": ["chitose", "ชิโตเสะ", "千歳"],
    "Rumoi": ["rumoi", "รุโมอิ", "留萌"],
}
DEFAULT_CITY = "Sapporo"
DEFAULT_REGION = "Hokkaido"
DEFAULT_LINE = "All"

SUPPORTED_LANGUAGES = ("th", "ja", "en")
SHORT_KEYWORD_LEN = 4  # short or numeric keywords must match a whole word

_THAI_RE = re.compile(r"[฀-๿]")
_JAPANESE_RE = re.compile(r"[぀-ヿ一-鿿]")
_LETTER_RE = re.compile(r"[^\W\d_]")
_KEYWORD_CACHE: Dict[str, "re.Pattern[str]"] = {}


def _normalize_text(text: str) -> str:
    return " ".join((text or "").lower().split())


def contains_keyword(text: str, keyword: str) -> bool:
    """Keyword match for routing rules.

    * Non-ASCII keywords (Thai, Japanese) match as substrings: those scripts have no word spacing.
    * Short or numeric ASCII keywords (``jr``, ``live``, ``119``) must match a whole word,
      so ``jr`` does not match ``jrpass`` and ``119`` does not match ``1190``.
    * Longer ASCII keywords match at a word start, so ``snow`` matches ``snowing`` but
      ``rain`` never matches ``train``.
    """
    if not keyword.isascii():
        return keyword in text
    pattern = _KEYWORD_CACHE.get(keyword)
    if pattern is None:
        whole_word = len(keyword) <= SHORT_KEYWORD_LEN or keyword.isdigit()
        tail = r"(?![a-z0-9])" if whole_word else ""
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(keyword) + tail)
        _KEYWORD_CACHE[keyword] = pattern
    return pattern.search(text) is not None


def detect_language(text: str, fallback: Optional[str] = None) -> str:
    """Returns ``th``, ``ja`` or ``en`` from the script used in ``text``.

    ``fallback`` (the client's locale) is used only when the text contains no letters at all,
    because the user's own writing always decides the reply language.
    """
    if isinstance(text, str):
        if _THAI_RE.search(text):
            return "th"
        if _JAPANESE_RE.search(text):
            return "ja"
        if _LETTER_RE.search(text):
            return "en"
    if isinstance(fallback, str):
        code = fallback.strip().lower()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code
    return "en"


class IntentClassifier:
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        model: Optional[str] = None,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold
        self.model = model if model is not None else config_value("ROUTER_MODEL", DEFAULT_ROUTER_MODEL)

    # ------------------------------------------------------------------
    # Route classification
    # ------------------------------------------------------------------
    def classify_message(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> RouteDecision:
        """Classifies ``query``; on any provider or parsing failure falls back to keywords."""
        keyword_route = self.keyword_route(query)
        keyword_hints = self.tool_hints(query)

        if not provider_ready(self.llm_client):
            return self._fallback_decision(keyword_route, keyword_hints, "router unavailable: provider not configured")

        messages: List[Dict[str, str]] = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]
        for turn in (history or [])[-4:]:
            role = "assistant" if turn.get("role") in ("ai", "assistant") else "user"
            messages.append({"role": role, "content": str(turn.get("content", ""))})
        messages.append({"role": "user", "content": query})

        try:
            raw = self.llm_client.complete(
                messages, model=self.model, temperature=0.0, max_tokens=256, json_mode=True
            )
        except LLMClientError as exc:
            logger.warning("router provider failure: %s", exc)
            return self._fallback_decision(keyword_route, keyword_hints, f"router error: {exc}")

        parsed = extract_json_object(raw)
        if not parsed or parsed.get("route") not in ROUTES:
            logger.warning("router returned an invalid route payload")
            return self._fallback_decision(keyword_route, keyword_hints, "router returned an invalid route")

        try:
            confidence = float(parsed.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        llm_hints = parsed.get("tools") if isinstance(parsed.get("tools"), list) else None
        hints = self._merge_hints(llm_hints, keyword_hints)

        if confidence < self.confidence_threshold and keyword_route:
            logger.info("router low confidence (%.2f); keyword fallback -> %s", confidence, keyword_route)
            return RouteDecision(
                route=keyword_route,
                confidence=confidence,
                reasoning="low-confidence LLM route overridden by keyword rules",
                fallback_used=True,
                source="keyword",
                tool_hints=hints,
            )

        return RouteDecision(
            route=parsed["route"],
            confidence=confidence,
            reasoning=str(parsed.get("reasoning", ""))[:300],
            fallback_used=False,
            source="llm",
            tool_hints=hints,
        )

    @staticmethod
    def _merge_hints(llm_hints: Optional[List[Any]], keyword_hints: List[str]) -> Optional[List[str]]:
        """Combines router and keyword hints. ``None`` means "unknown": the planner then
        queries every permitted tool rather than guessing that none is needed."""
        merged = [name for name in TOOL_NAMES if (llm_hints and name in llm_hints) or name in keyword_hints]
        if merged:
            return merged
        return None

    def _fallback_decision(self, keyword_route: Optional[str], hints: List[str], reason: str) -> RouteDecision:
        tool_hints = hints or None
        if keyword_route:
            return RouteDecision(
                route=keyword_route,
                confidence=0.5,
                reasoning=f"{reason}; rescued by keyword rules",
                fallback_used=True,
                source="keyword",
                tool_hints=tool_hints,
            )
        return RouteDecision(
            route=SAFE_DEFAULT_ROUTE,
            confidence=0.5,
            reasoning=f"{reason}; conservative default to '{SAFE_DEFAULT_ROUTE}'",
            fallback_used=True,
            source="default",
            tool_hints=tool_hints,
        )

    @staticmethod
    def keyword_route(query: str) -> Optional[str]:
        q = _normalize_text(query)
        realtime_hit = any(contains_keyword(q, kw) for kw in KEYWORD_RULES["realtime"])
        rag_hit = any(contains_keyword(q, kw) for kw in KEYWORD_RULES["rag"])
        if realtime_hit and rag_hit:
            return "rag+realtime"
        if realtime_hit:
            return "realtime"
        if rag_hit:
            return "rag"
        return None

    @staticmethod
    def tool_hints(query: str) -> List[str]:
        q = _normalize_text(query)
        return [name for name in TOOL_NAMES if any(contains_keyword(q, kw) for kw in TOOL_KEYWORDS[name])]

    # ------------------------------------------------------------------
    # Context needs and slots
    # ------------------------------------------------------------------
    @staticmethod
    def detect_context_needs(decision: RouteDecision) -> Dict[str, bool]:
        return {
            "needs_retrieval": decision.needs_retrieval,
            "needs_live_data": decision.needs_live_data,
        }

    @staticmethod
    def extract_slots(query: str, english_query: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Extracts primitive adapter inputs. ``None`` means the user did not say.

        When several cities are mentioned the first one in the text wins.
        """
        haystack = _normalize_text(" ".join(part for part in (query, english_query) if part))

        city: Optional[str] = None
        best_position = len(haystack) + 1
        for canonical, aliases in KNOWN_CITIES.items():
            for alias in aliases:
                position = haystack.find(alias)
                if position != -1 and position < best_position:
                    best_position = position
                    city = canonical

        line: Optional[str] = None
        if any(token in haystack for token in ("airport", "chitose", "สนามบิน", "ชิโตเสะ")):
            line = "Rapid Airport"
        elif any(token in haystack for token in ("hakodate", "ฮาโกดาเตะ", "ฮาโกะดาเตะ")):
            line = "Hakodate Line"
        elif any(token in haystack for token in ("shinkansen", "ชินคันเซ็น")):
            line = "Hokkaido Shinkansen"

        return {"city": city, "region": DEFAULT_REGION, "line_name": line}

    @staticmethod
    def missing_required_slots(decision: RouteDecision, slots: Dict[str, Optional[str]]) -> List[str]:
        """Names slots the user did not provide for the tools the route needs.

        The planner fills these with conservative defaults; the orchestrator records a
        notice. A safety answer is never blocked on a clarifying question.
        """
        if not decision.needs_live_data:
            return []
        missing: List[str] = []
        hints = decision.tool_hints if decision.tool_hints is not None else list(TOOL_NAMES)
        if "weather" in hints and not slots.get("city"):
            missing.append("city")
        if "train" in hints and not slots.get("line_name"):
            missing.append("line_name")
        return missing
