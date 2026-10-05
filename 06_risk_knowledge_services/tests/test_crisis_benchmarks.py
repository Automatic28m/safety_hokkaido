import unittest
import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_root = os.path.abspath(os.path.join(current_dir, ".."))
workspace_root = os.path.abspath(os.path.join(pkg_root, ".."))
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from risk_knowledge.models import (
    RiskLevel,
    RiskTrend,
    EvidenceChunk,
    RetrievalResultItem,
    RiskAssessment,
    RouteInfo,
    RiskKnowledgeResponse,
)
from risk_knowledge.risk_model import LocalRiskModel
from risk_knowledge.risk_service import RiskKnowledgeService


class BenchmarkMockRetriever:
    def __init__(self):
        self.degraded = False
        self.notices = []
        self.index_version = "benchmark-v2"

    def retrieve(self, query: str, top_k: int = 5):
        # Mix of general sightseeing and emergency survival chunks
        return [
            EvidenceChunk(
                chunk_id="chunk_otaru_canal_01",
                text="Otaru Canal is a picturesque scenic waterway lined with Victorian oil lamps and brick warehouses.",
                metadata={"source_file": "tourism_otaru.pdf", "page": 4, "category": "sightseeing", "situation": "leisure"},
            ),
            EvidenceChunk(
                chunk_id="chunk_whiteout_sos_02",
                text="CRITICAL SURVIVAL: If trapped in a vehicle during a blizzard whiteout, stay inside the car. Clear the exhaust pipe periodically to prevent carbon monoxide poisoning and dial 119.",
                metadata={"source_file": "winter_survival_manual.pdf", "page": 12, "category": "emergency", "situation": "whiteout_survival"},
            ),
            EvidenceChunk(
                chunk_id="chunk_hypothermia_03",
                text="FIRST AID FOR HYPOTHERMIA: Move victim to shelter, replace wet clothes with warm dry layers, and provide warm sweet beverages if conscious.",
                metadata={"source_file": "first_aid_hokkaido.pdf", "page": 8, "category": "firstaid", "situation": "hypothermia"},
            ),
        ]


class TestHokkaidoCrisisBenchmarks(unittest.TestCase):
    def setUp(self):
        self.model = LocalRiskModel()
        self.retriever = BenchmarkMockRetriever()
        self.service = RiskKnowledgeService(retriever=self.retriever, risk_model=self.model)

    def test_2022_sapporo_whiteout_blizzard_scenario(self):
        """Simulate landmark Feb 2022 Sapporo Whiteout Blizzard."""
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -11.5,
                    "summary": "Violent blizzard with zero visibility",
                    "wind_speed_ms": 25.8,
                    "precipitation_total_mm": 18.0,
                    "precipitation_type": "snow",
                }
            }
        }
        disaster = {
            "status": "ok",
            "data": {
                "earthquakes": {"is_available": True, "latest_event": None},
                "meteorological_warnings": {
                    "is_available": True,
                    "active_headline": "暴風雪警報 (Blizzard Emergency Warning) for Ishikari and Shiribeshi",
                }
            }
        }
        transit = {
            "status": "ok",
            "data": {
                "line_name": "JR Hakodate Main Line",
                "simulation_details": {
                    "operational_state": "suspended",
                    "cause": "deep snowdrifts on tracks",
                    "affected_section": "Sapporo - Otaru",
                }
            }
        }

        assessment, route_info = self.model.evaluate(
            weather_snapshot=weather,
            disaster_snapshot=disaster,
            transit_snapshot=transit,
            route_context={"origin": "Sapporo", "destination": "Otaru"}
        )

        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertGreaterEqual(assessment.risk_score, 0.85)
        self.assertEqual(len(route_info.closed_segments), 1)
        self.assertIn("JR Hakodate Main Line (Sapporo - Otaru)", route_info.closed_segments[0])
        factors_str = " ".join(assessment.primary_factors).lower()
        self.assertTrue("whiteout" in factors_str or "blizzard" in factors_str)

    def test_2018_eastern_iburi_mega_earthquake_scenario(self):
        """Simulate Sep 2018 Eastern Iburi Shindo 7 mega-earthquake."""
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": 16.0,
                    "summary": "Clear",
                    "wind_speed_ms": 2.5,
                    "precipitation_total_mm": 0.0,
                }
            }
        }
        disaster = {
            "status": "ok",
            "data": {
                "earthquakes": {
                    "is_available": True,
                    "latest_event": {
                        "max_intensity": "7",
                        "magnitude": 6.7,
                        "epicenter_en": "Iburi Subprefecture",
                    }
                },
                "meteorological_warnings": {"is_available": True, "active_headline": None}
            }
        }

        assessment, _ = self.model.evaluate(
            weather_snapshot=weather,
            disaster_snapshot=disaster,
        )

        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertGreaterEqual(assessment.risk_score, 0.90)
        self.assertTrue(any("earthquake" in f.lower() for f in assessment.primary_factors))

    def test_nakayama_mountain_pass_elevation_multiplier(self):
        """Verify high-elevation mountain pass detection and multiplier."""
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -12.0,
                    "summary": "Snowing",
                    "wind_speed_ms": 14.0,
                    "precipitation_total_mm": 5.0,
                    "precipitation_type": "snow",
                }
            }
        }
        # Route via Nakayama Pass
        route_ctx = {"origin": "Sapporo", "destination": "Niseko", "via": "Nakayama Pass (Route 230)"}
        assessment, route_info = self.model.evaluate(weather_snapshot=weather, route_context=route_ctx)

        factors_str = " ".join(assessment.primary_factors)
        self.assertIn("Nakayama Pass", factors_str)
        self.assertIn("elevation multiplier", factors_str.lower())

    def test_hourly_forecast_deteriorating_trajectory(self):
        """Test Step 2.1: Temporal risk forecasting detects worsening weather."""
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -1.0,
                    "summary": "Cloudy",
                    "wind_speed_ms": 4.0,
                    "precipitation_total_mm": 0.0,
                },
                "hourly_forecast": [
                    {"time_utc": "2026-09-30T00:00:00Z", "temperature_c": -2.0, "precipitation_total_mm": 1.0, "summary": "Light snow"},
                    {"time_utc": "2026-09-30T03:00:00Z", "temperature_c": -8.0, "precipitation_total_mm": 8.0, "summary": "Snow squalls"},
                    {"time_utc": "2026-09-30T06:00:00Z", "temperature_c": -14.0, "precipitation_total_mm": 16.0, "summary": "Violent blizzard"},
                ]
            }
        }
        assessment, _ = self.model.evaluate(weather_snapshot=weather)

        self.assertEqual(assessment.risk_trend, RiskTrend.DETERIORATING)
        self.assertGreaterEqual(assessment.forecasted_peak_score, 0.80)
        self.assertIn("2026-09-30T06:00:00Z", assessment.forecasted_peak_window)

    def test_performance_cache_hit_and_speed(self):
        """Test Step 2.4: LRU caching delivers sub-10ms response on repeated requests."""
        self.service.clear_cache()
        query = "How to travel safely between Sapporo and Otaru?"
        weather = {"status": "ok", "data": {"current": {"temperature_c": 2.0, "wind_speed_ms": 3.0}}}

        t0 = time.perf_counter()
        resp1 = self.service.get_risk_knowledge(query, weather_snapshot=weather)
        dur1 = time.perf_counter() - t0

        t1 = time.perf_counter()
        resp2 = self.service.get_risk_knowledge(query, weather_snapshot=weather)
        dur2 = time.perf_counter() - t1

        stats = self.service.get_cache_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(resp1.risk_assessment.risk_score, resp2.risk_assessment.risk_score)
        self.assertLess(dur2, 0.010)  # Faster than 10 milliseconds

    def test_adaptive_emergency_category_prioritization(self):
        """Test Step 2.3: Emergency queries prioritize life-saving survival chunks over leisure."""
        emergency_query = "EMERGENCY: car stuck in whiteout snowdrift, engine failing"
        response = self.service.get_risk_knowledge(emergency_query, evaluate_risk=False)

        self.assertGreaterEqual(len(response.results), 2)
        # First chunk must be emergency or survival, not sightseeing!
        top_chunk = response.results[0].chunk
        self.assertIn(top_chunk.metadata.category, ["emergency", "whiteout", "firstaid", "survival"])
        self.assertIn("119", top_chunk.text)
        self.assertTrue(any("adaptive emergency filtering" in n.lower() for n in response.notices))


if __name__ == "__main__":
    unittest.main()
