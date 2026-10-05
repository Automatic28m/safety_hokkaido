import unittest
from datetime import datetime, timezone
import sys
import os

# Ensure package roots are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_root = os.path.abspath(os.path.join(current_dir, ".."))
workspace_root = os.path.abspath(os.path.join(pkg_root, ".."))
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

external_data_dir = os.path.join(workspace_root, "04_external_data_services")
backend_dir = os.path.join(workspace_root, "02_api_backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if external_data_dir not in sys.path:
    sys.path.insert(0, external_data_dir)

from risk_knowledge.models import RiskLevel, RiskAssessment, RouteInfo
from risk_knowledge.risk_model import LocalRiskModel

# Optional LiveDataSnapshot import for cross-module contract testing
try:
    from external_data.models import LiveDataSnapshot
except ImportError:
    LiveDataSnapshot = None


class TestLocalRiskModel(unittest.TestCase):
    def setUp(self):
        self.model = LocalRiskModel()

    def test_low_risk_clear_conditions(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": 5.0,
                    "summary": "Clear sky",
                    "wind_speed_ms": 3.2,
                    "precipitation_total_mm": 0.0,
                    "precipitation_type": "none",
                }
            }
        }
        disaster = {
            "status": "ok",
            "data": {
                "earthquakes": {"is_available": True, "latest_event": None, "count": 0},
                "meteorological_warnings": {"is_available": True, "active_headline": None}
            }
        }
        transit = {
            "status": "ok",
            "data": {
                "line_name": "JR Chitose Line",
                "simulation_details": {
                    "operational_state": "normal",
                    "estimated_delay_minutes": 0,
                    "affected_section": "Full Route",
                }
            }
        }

        assessment, route_info = self.model.evaluate(
            weather_snapshot=weather,
            disaster_snapshot=disaster,
            transit_snapshot=transit,
            route_context={"origin": "Sapporo", "destination": "Otaru"}
        )

        self.assertEqual(assessment.risk_level, RiskLevel.LOW)
        self.assertLess(assessment.risk_score, 0.35)
        self.assertEqual(len(route_info.closed_segments), 0)
        self.assertIn("Sapporo", route_info.recommended_route)
        self.assertIn("Otaru", route_info.recommended_route)

    def test_high_risk_whiteout_blizzard(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -12.0,
                    "summary": "Heavy blizzard and blowing snow",
                    "wind_speed_ms": 23.5,
                    "precipitation_total_mm": 15.0,
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
                    "active_headline": "暴風雪警報 (Blizzard Warning) issued for Ishikari region",
                }
            }
        }
        transit = {
            "status": "ok",
            "data": {
                "line_name": "JR Hakodate Line",
                "simulation_details": {
                    "operational_state": "delayed",
                    "estimated_delay_minutes": 45,
                    "cause": "deep snowdrifts",
                }
            }
        }

        assessment, route_info = self.model.evaluate(
            weather_snapshot=weather,
            disaster_snapshot=disaster,
            transit_snapshot=transit,
        )

        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertGreaterEqual(assessment.risk_score, 0.70)
        factors_text = " ".join(assessment.primary_factors).lower()
        self.assertTrue("whiteout" in factors_text or "wind" in factors_text)
        self.assertTrue("blizzard" in factors_text or "warning" in factors_text)

    def test_high_risk_major_earthquake(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": 10.0,
                    "summary": "Clear",
                    "wind_speed_ms": 2.0,
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
                        "max_intensity": "6弱",
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
        self.assertGreaterEqual(assessment.risk_score, 0.75)
        factors_text = " ".join(assessment.primary_factors)
        self.assertIn("earthquake", factors_text.lower())

    def test_medium_risk_moderate_snow_and_delays(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -3.0,
                    "summary": "Moderate snow",
                    "wind_speed_ms": 15.0,
                    "precipitation_total_mm": 4.5,
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
                    "active_headline": "大雪注意報 (Snow Advisory) issued",
                }
            }
        }
        transit = {
            "status": "ok",
            "data": {
                "line_name": "JR Airport Rapid",
                "simulation_details": {
                    "operational_state": "delayed",
                    "estimated_delay_minutes": 20,
                    "affected_section": "Sapporo - New Chitose Airport",
                }
            }
        }

        assessment, route_info = self.model.evaluate(
            weather_snapshot=weather,
            disaster_snapshot=disaster,
            transit_snapshot=transit,
        )

        self.assertEqual(assessment.risk_level, RiskLevel.MEDIUM)
        self.assertGreaterEqual(assessment.risk_score, 0.35)
        self.assertLessEqual(assessment.risk_score, 0.69)

    def test_transit_suspension_detects_closed_segments(self):
        transit = {
            "status": "ok",
            "data": {
                "line_name": "JR Sekisho Line",
                "simulation_details": {
                    "operational_state": "suspended",
                    "cause": "avalanche risk",
                    "affected_section": "Minami-Chitose - Shintoku",
                }
            }
        }

        assessment, route_info = self.model.evaluate(transit_snapshot=transit)
        self.assertEqual(len(route_info.closed_segments), 1)
        self.assertIn("JR Sekisho Line (Minami-Chitose - Shintoku)", route_info.closed_segments[0])
        self.assertTrue(len(route_info.alternative_routes) > 0)

    def test_all_feeds_unavailable_returns_unknown_and_fails_conservatively(self):
        assessment, route_info = self.model.evaluate(
            weather_snapshot=None,
            disaster_snapshot={"status": "unavailable"},
            transit_snapshot=None,
        )

        self.assertEqual(assessment.risk_level, RiskLevel.UNKNOWN)
        self.assertEqual(assessment.risk_score, 0.0)
        self.assertTrue(any("unavailable" in f.lower() for f in assessment.primary_factors))
        self.assertIsNone(route_info.recommended_route)

    def test_partial_feed_availability(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -1.0,
                    "summary": "Clear",
                    "wind_speed_ms": 5.0,
                }
            }
        }
        # Disaster & Transit are unavailable
        assessment, route_info = self.model.evaluate(
            weather_snapshot=weather,
            disaster_snapshot={"status": "unavailable"},
            transit_snapshot=None,
        )

        self.assertNotEqual(assessment.risk_level, RiskLevel.UNKNOWN)
        self.assertEqual(assessment.risk_level, RiskLevel.LOW)

    def test_livedatasnapshot_dataclass_compatibility(self):
        if LiveDataSnapshot is None:
            self.skipTest("LiveDataSnapshot model from external_data not available in environment")

        snapshot = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="ok",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            data={
                "current": {
                    "temperature_c": -18.0,
                    "summary": "Extreme cold",
                    "wind_speed_ms": 22.0,
                    "precipitation_total_mm": 5.0,
                    "precipitation_type": "snow",
                }
            }
        )

        score, factors, is_avail = self.model.evaluate_weather_risk(snapshot)
        self.assertTrue(is_avail)
        self.assertGreater(score, 0.70)
        self.assertTrue(any("whiteout" in f.lower() or "wind" in f.lower() for f in factors))


if __name__ == "__main__":
    unittest.main()
