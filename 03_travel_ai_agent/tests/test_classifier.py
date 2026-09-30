from agent_core.classifier import IntentClassifier, detect_language
from conftest import FakeLLM


def test_detect_language():
    assert detect_language("Is it snowing in Sapporo?") == "en"
    assert detect_language("ตอนนี้ซัปโปโรหิมะตกไหม") == "th"
    assert detect_language("札幌は雪ですか") == "ja"


def test_keyword_route_english_and_thai():
    assert IntentClassifier.keyword_route("What is Hokkaido famous for?") is None
    assert IntentClassifier.keyword_route("Are JR trains running today?") == "realtime"
    assert IntentClassifier.keyword_route("What do I do during a blizzard?") == "rag"
    assert IntentClassifier.keyword_route("Is it safe to drive to Otaru right now?") == "rag+realtime"
    assert IntentClassifier.keyword_route("แผ่นดินไหวควรทำอย่างไร") == "rag"
    assert IntentClassifier.keyword_route("วันนี้รถไฟล่าช้าไหม") == "realtime"


def test_tool_hints():
    assert IntentClassifier.tool_hints("Is it snowing right now?") == ["weather"]
    assert IntentClassifier.tool_hints("Any earthquake alerts and train delays?") == ["disaster", "train"]
    assert IntentClassifier.tool_hints("อากาศที่ซัปโปโรเป็นยังไง") == ["weather"]


def test_extract_slots_from_thai_and_english():
    slots = IntentClassifier.extract_slots("อากาศที่โอตารุตอนนี้", None)
    assert slots["city"] == "Otaru"
    slots = IntentClassifier.extract_slots("Rapid airport train to Chitose?", None)
    assert slots["line_name"] == "Rapid Airport"
    slots = IntentClassifier.extract_slots("Any train issues?", "Any train issues?")
    assert slots["city"] is None and slots["line_name"] is None and slots["region"] == "Hokkaido"


def test_classify_uses_llm_route_when_confident():
    clf = IntentClassifier(llm_client=FakeLLM(route="general", confidence=0.9, tools=[]), model="m")
    decision = clf.classify_message("What is Hokkaido famous for?")
    assert decision.route == "general"
    assert decision.fallback_used is False and decision.source == "llm"


def test_classify_low_confidence_falls_back_to_keywords_and_flags_it():
    clf = IntentClassifier(llm_client=FakeLLM(route="general", confidence=0.2), model="m")
    decision = clf.classify_message("Are JR trains running today?")
    assert decision.route == "realtime"
    assert decision.fallback_used is True and decision.source == "keyword"


def test_classify_invalid_llm_route_falls_back():
    clf = IntentClassifier(llm_client=FakeLLM(route="browse-the-web", confidence=0.99), model="m")
    decision = clf.classify_message("What do I do during a blizzard?")
    assert decision.route == "rag" and decision.fallback_used is True


def test_classify_provider_error_defaults_conservatively_when_no_keywords():
    clf = IntentClassifier(llm_client=FakeLLM(fail_on={"router"}), model="m")
    decision = clf.classify_message("Tell me something nice")
    assert decision.route == "rag"
    assert decision.fallback_used is True and decision.source == "default"


def test_classify_without_provider_uses_keywords():
    clf = IntentClassifier(llm_client=FakeLLM(configured=False), model="m")
    decision = clf.classify_message("Is it snowing in Sapporo right now?")
    assert decision.route == "realtime" and decision.fallback_used is True
    assert decision.tool_hints == ["weather"]


def test_llm_tool_hints_are_merged_with_keyword_hints():
    clf = IntentClassifier(llm_client=FakeLLM(route="realtime", confidence=0.9, tools=["train"]), model="m")
    decision = clf.classify_message("weather please")
    assert decision.tool_hints == ["weather", "train"]


def test_missing_required_slots_only_for_live_routes():
    clf = IntentClassifier(llm_client=FakeLLM(route="realtime", confidence=0.9, tools=["weather", "train"]), model="m")
    decision = clf.classify_message("weather and trains?")
    assert clf.missing_required_slots(decision, {"city": None, "line_name": None}) == ["city", "line_name"]
    rag = IntentClassifier(llm_client=FakeLLM(route="rag", confidence=0.9), model="m").classify_message("blizzard")
    assert clf.missing_required_slots(rag, {"city": None, "line_name": None}) == []
