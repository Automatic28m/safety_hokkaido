import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import requests
from config import config
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.tools import (
    get_real_time_weather,
    get_disaster_warnings,
    check_train_status
)


class TestIntegrationScenarios(unittest.TestCase):
    def setUp(self):
        global_cache.clear()

    # ─────────────────────────────────────────────────────────────
    # Scenario 1: Safe / Normal Scenario
    # ─────────────────────────────────────────────────────────────
    @patch("external_data.weather.requests.get")
    def test_scenario_01_safe_normal(self, mock_weather_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "test_valid_key"
        try:
            mock_find = MagicMock(status_code=200)
            mock_find.json.return_value = [{"place_id": "sapporo-center", "name": "Sapporo", "country": "Japan"}]
            mock_point = MagicMock(status_code=200)
            mock_point.json.return_value = {
                "current": {
                    "temperature": -2.0,
                    "summary": "Clear and cold",
                    "wind": {"speed": 2.1, "angle": 180, "dir": "S"},
                    "precipitation": {"total": 0.0, "type": "none"},
                    "cloud_cover": 10
                },
                "hourly": {"data": [{"date": "2026-09-24T12:00:00", "temperature": -1.5, "summary": "Clear"}]}
            }
            mock_weather_get.side_effect = [mock_find, mock_point]

            weather_res = get_real_time_weather("Sapporo")
            self.assertEqual(weather_res.status, "ok")
            self.assertEqual(weather_res.provider, "meteosource")
            self.assertEqual(weather_res.data["city_name"], "Sapporo")
            self.assertEqual(weather_res.data["current"]["temperature_c"], -2.0)
            self.assertIsNotNone(weather_res.source_url)
            self.assertIsNotNone(weather_res.fetched_at)

            train_res = check_train_status("Hakodate Line")
            self.assertEqual(train_res.status, "mocked")
            self.assertIn("Simulated", train_res.notice)
            self.assertEqual(train_res.data["line_name"], "Hakodate Line")
            self.assertEqual(train_res.data["simulation_details"]["operational_state"], "normal")
        finally:
            config.METEOSOURCE_API_KEY = original_key

    # ─────────────────────────────────────────────────────────────
    # Scenario 2: Degraded Scenario (Network / Provider Timeout)
    # ─────────────────────────────────────────────────────────────
    @patch("external_data.weather.requests.get")
    @patch("external_data.disaster.requests.get")
    def test_scenario_02_degraded_timeout(self, mock_disaster_get, mock_weather_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "test_valid_key"
        try:
            mock_weather_get.side_effect = requests.exceptions.Timeout("Meteosource gateway timeout")

            weather_res = get_real_time_weather("Sapporo")
            self.assertEqual(weather_res.status, "unavailable")
            self.assertEqual(weather_res.error_code, "TIMEOUT")
            self.assertIn("timed out", weather_res.notice.lower())

            mock_disaster_get.side_effect = requests.exceptions.ConnectionError("Failed to reach JMA")

            disaster_res = get_disaster_warnings("Hokkaido")
            self.assertEqual(disaster_res.status, "unavailable")
            self.assertEqual(disaster_res.error_code, "PROVIDER_UNAVAILABLE")
            self.assertNotIn("No warnings", str(disaster_res.data))
            self.assertNotIn("Normal winter conditions", disaster_res.notice)
        finally:
            config.METEOSOURCE_API_KEY = original_key

    # ─────────────────────────────────────────────────────────────
    # Scenario 3: Disaster Emergency Scenario (Earthquake + Tsunami)
    # ─────────────────────────────────────────────────────────────
    @patch("external_data.disaster.requests.get")
    def test_scenario_03_disaster_emergency(self, mock_disaster_get):
        mock_quake_resp = MagicMock(status_code=200)
        mock_quake_resp.json.return_value = [
            {
                "anm": "釧路沖",
                "en_anm": "Off the Coast of Kushiro",
                "rdt": "2026-09-24T15:00:00+09:00",
                "mag": "6.8",
                "maxi": "6-",
                "cod": "+42.8+145.0-30000/"
            }
        ]

        mock_warn_resp = MagicMock(status_code=200)
        mock_warn_resp.json.return_value = {
            "reportDatetime": "2026-09-24T15:05:00+09:00",
            "headlineText": "Blizzard and tsunami advisory in effect."
        }
        mock_disaster_get.side_effect = [mock_quake_resp, mock_warn_resp]

        disaster_res = get_disaster_warnings("Hokkaido")
        self.assertEqual(disaster_res.status, "ok")
        self.assertEqual(disaster_res.provider, "jma")
        self.assertGreater(disaster_res.data["earthquakes"]["count"], 0)

        latest_quake = disaster_res.data["earthquakes"]["latest_event"]
        self.assertEqual(latest_quake["magnitude"], "6.8")
        self.assertEqual(latest_quake["max_intensity"], "6-")
        self.assertEqual(latest_quake["epicenter_en"], "Off the Coast of Kushiro")

        warning_info = disaster_res.data["meteorological_warnings"]
        self.assertTrue(warning_info["is_available"])
        self.assertEqual(warning_info["active_headline"], "Blizzard and tsunami advisory in effect.")

    # ─────────────────────────────────────────────────────────────
    # Scenario 4: Airport Route Transit Delays Simulation
    # ─────────────────────────────────────────────────────────────
    def test_scenario_04_airport_transit_delay(self):
        train_res = check_train_status("Rapid Airport")
        self.assertEqual(train_res.status, "mocked")
        self.assertEqual(train_res.data["simulation_details"]["operational_state"], "delayed")
        self.assertEqual(train_res.data["simulation_details"]["estimated_delay_minutes"], 20)
        self.assertEqual(train_res.data["simulation_details"]["cause"], "track_snow_accumulation")
        self.assertIn("Sapporo - New Chitose Airport", train_res.data["simulation_details"]["affected_section"])

    # ─────────────────────────────────────────────────────────────
    # Scenario 5: Stale Fallback during Provider Outage
    # ─────────────────────────────────────────────────────────────
    @patch("external_data.weather.requests.get")
    def test_scenario_05_stale_cache_fallback(self, mock_weather_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "test_valid_key"
        try:
            # 1. Populate cache with valid snapshot
            past_time = (datetime.now(timezone.utc) - timedelta(seconds=1200)).strftime("%Y-%m-%dT%H:%M:%SZ")
            expired_time = (datetime.now(timezone.utc) - timedelta(seconds=600)).strftime("%Y-%m-%dT%H:%M:%SZ")
            seed_snapshot = LiveDataSnapshot(
                provider="meteosource",
                kind="weather",
                scope="Sapporo",
                status="ok",
                fetched_at=past_time,
                expires_at=expired_time,
                source_url="https://www.meteosource.com",
                data={"temperature_c": 14.0, "condition": "Sunny"}
            )
            global_cache.set(seed_snapshot, ttl_seconds=0)

            # 2. Simulate provider failure
            mock_weather_get.side_effect = requests.exceptions.Timeout("Provider is down")

            # 3. Must serve stale cache
            res = get_real_time_weather("Sapporo")
            self.assertEqual(res.status, "stale")
            self.assertEqual(res.fetched_at, past_time)
            self.assertEqual(res.data["temperature_c"], 14.0)
            self.assertIn("stale", res.notice.lower())
        finally:
            config.METEOSOURCE_API_KEY = original_key

    # ─────────────────────────────────────────────────────────────
    # Scenario 6: JMA Earthquake Filter Precision (No False Positives)
    # ─────────────────────────────────────────────────────────────
    @patch("external_data.disaster.requests.get")
    def test_scenario_06_earthquake_precision_filter(self, mock_disaster_get):
        mock_quake_resp = MagicMock(status_code=200)
        # Mix of Hokkaido and Non-Hokkaido earthquakes (Hiroshima, Kagoshima, Amami-Oshima)
        mock_quake_resp.json.return_value = [
            {"anm": "広島県北部", "en_anm": "Northern Hiroshima Prefecture", "rdt": "2026-09-24T10:00:00+09:00", "mag": "3.0"},
            {"anm": "奄美大島近海", "en_anm": "Adjacent Sea of Amami-Oshima Island", "rdt": "2026-09-24T10:05:00+09:00", "mag": "4.5"},
            {"anm": "根室半島南東沖", "en_anm": "Off the southeast Coast of the Nemuro Peninsula", "rdt": "2026-09-24T10:10:00+09:00", "mag": "4.8", "maxi": "3"},
            {"anm": "鹿児島県薩摩地方", "en_anm": "Satsuma Region, Kagoshima", "rdt": "2026-09-24T10:15:00+09:00", "mag": "2.1"},
            {"anm": "十勝地方南部", "en_anm": "Southern Tokachi", "rdt": "2026-09-24T10:20:00+09:00", "mag": "3.9", "maxi": "2"}
        ]

        mock_warn_resp = MagicMock(status_code=200)
        mock_warn_resp.json.return_value = {"reportDatetime": "2026-09-24T10:00:00+09:00", "headlineText": None}
        mock_disaster_get.side_effect = [mock_quake_resp, mock_warn_resp]

        res = get_disaster_warnings("Hokkaido")
        self.assertEqual(res.status, "ok")
        # Exactly 2 Hokkaido events (Nemuro and Tokachi) must be captured, 3 non-Hokkaido excluded
        self.assertEqual(res.data["earthquakes"]["count"], 2)
        epicenters = [e["epicenter_en"] for e in res.data["earthquakes"]["recent_hokkaido_events"]]
        self.assertIn("Off the southeast Coast of the Nemuro Peninsula", epicenters)
        self.assertIn("Southern Tokachi", epicenters)
        self.assertNotIn("Northern Hiroshima Prefecture", epicenters)
        self.assertNotIn("Adjacent Sea of Amami-Oshima Island", epicenters)


if __name__ == "__main__":
    unittest.main()
