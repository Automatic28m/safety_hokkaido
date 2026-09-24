import unittest
from unittest.mock import patch, MagicMock
import requests
from config import config
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache
from external_data.train import fetch_train_status
from external_data.disaster import fetch_disaster_warnings
from external_data.weather import fetch_real_time_weather


class TestAdapters(unittest.TestCase):
    def setUp(self):
        global_cache.clear()

    # ── Train Adapter Tests ──────────────────────────────────────
    def test_01_train_status_always_mocked(self):
        snapshot = fetch_train_status("Rapid Airport")
        self.assertIsInstance(snapshot, LiveDataSnapshot)
        self.assertEqual(snapshot.provider, "jr_hokkaido_simulator")
        self.assertEqual(snapshot.kind, "train")
        self.assertEqual(snapshot.status, "mocked")
        self.assertIn("Simulated", snapshot.notice)
        self.assertEqual(snapshot.source_url, "https://www.jrhokkaido.co.jp/")
        self.assertTrue(snapshot.data["is_simulated"])
        self.assertEqual(snapshot.data["verification_status"], "unverified_mock")

    def test_02_train_airport_delays_simulated(self):
        snap = fetch_train_status("Rapid Airport")
        self.assertEqual(snap.data["simulation_details"]["operational_state"], "delayed")
        self.assertEqual(snap.data["simulation_details"]["estimated_delay_minutes"], 20)
        self.assertEqual(snap.data["simulation_details"]["cause"], "track_snow_accumulation")

    def test_03_train_standard_line_normal(self):
        snap = fetch_train_status("Hakodate Line")
        self.assertEqual(snap.data["simulation_details"]["operational_state"], "normal")
        self.assertEqual(snap.data["simulation_details"]["estimated_delay_minutes"], 0)

    def test_04_train_invalid_input_returns_unavailable(self):
        snapshot = fetch_train_status("InvalidLine!@#$")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    def test_05_train_zero_safety_judgment(self):
        snapshot = fetch_train_status("Rapid Airport")
        self.assertNotIn("safety_level", snapshot.data)
        self.assertNotIn("recommendation", snapshot.data)

    # ── Disaster Adapter Tests ───────────────────────────────────
    @patch("external_data.disaster.requests.get")
    def test_06_disaster_success_both_feeds(self, mock_get):
        mock_quake = MagicMock(status_code=200)
        mock_quake.json.return_value = [
            {"anm": "十勝地方", "en_anm": "Tokachi", "rdt": "2026-09-24T12:00:00+09:00", "mag": "4.2", "maxi": "2"}
        ]
        mock_warn = MagicMock(status_code=200)
        mock_warn.json.return_value = {
            "reportDatetime": "2026-09-24T12:00:00+09:00",
            "headlineText": "Heavy snow advisory in effect."
        }
        mock_get.side_effect = [mock_quake, mock_warn]

        snapshot = fetch_disaster_warnings("Hokkaido")
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider, "jma")
        self.assertEqual(snapshot.data["earthquakes"]["count"], 1)
        self.assertEqual(snapshot.data["meteorological_warnings"]["active_headline"], "Heavy snow advisory in effect.")

    @patch("external_data.disaster.requests.get")
    def test_07_disaster_partial_when_warning_feed_fails(self, mock_get):
        mock_quake = MagicMock(status_code=200)
        mock_quake.json.return_value = []
        mock_warn = MagicMock(status_code=500)
        mock_get.side_effect = [mock_quake, mock_warn]

        snapshot = fetch_disaster_warnings("Hokkaido")
        self.assertEqual(snapshot.status, "partial")
        self.assertTrue(snapshot.data["earthquakes"]["is_available"])
        self.assertFalse(snapshot.data["meteorological_warnings"]["is_available"])
        self.assertIn("Weather warning feed unavailable", snapshot.notice)

    @patch("external_data.disaster.requests.get")
    def test_08_disaster_partial_when_quake_feed_fails(self, mock_get):
        mock_quake = MagicMock(status_code=503)
        mock_warn = MagicMock(status_code=200)
        mock_warn.json.return_value = {"headlineText": "Gale warning"}
        mock_get.side_effect = [mock_quake, mock_warn]

        snapshot = fetch_disaster_warnings("Hokkaido")
        self.assertEqual(snapshot.status, "partial")
        self.assertFalse(snapshot.data["earthquakes"]["is_available"])
        self.assertTrue(snapshot.data["meteorological_warnings"]["is_available"])
        self.assertIn("Earthquake feed unavailable", snapshot.notice)

    @patch("external_data.disaster.requests.get")
    def test_09_disaster_unavailable_on_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("JMA timeout")
        snapshot = fetch_disaster_warnings("Hokkaido")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "PROVIDER_UNAVAILABLE")
        self.assertNotIn("No warnings", str(snapshot.data))

    def test_10_disaster_invalid_region_scope(self):
        snapshot = fetch_disaster_warnings("Paris")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    # ── Weather Adapter Tests ────────────────────────────────────
    def test_11_weather_missing_api_key(self):
        original_key = config.METEOSOURCE_API_KEY
        try:
            config.METEOSOURCE_API_KEY = ""
            snapshot = fetch_real_time_weather("Sapporo")
            self.assertEqual(snapshot.status, "unavailable")
            self.assertEqual(snapshot.error_code, "CONFIG_MISSING")
        finally:
            config.METEOSOURCE_API_KEY = original_key

    def test_12_weather_invalid_city_name(self):
        snapshot = fetch_real_time_weather("Sapporo; DROP TABLE cities;")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    @patch("external_data.weather.requests.get")
    def test_13_weather_city_not_found(self, mock_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "valid_key"
        try:
            mock_find = MagicMock(status_code=200)
            mock_find.json.return_value = []
            mock_get.return_value = mock_find

            snapshot = fetch_real_time_weather("UnknownCity12345")
            self.assertEqual(snapshot.status, "unavailable")
            self.assertEqual(snapshot.error_code, "CITY_NOT_FOUND")
        finally:
            config.METEOSOURCE_API_KEY = original_key

    @patch("external_data.weather.requests.get")
    def test_14_weather_full_success(self, mock_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "valid_key"
        try:
            mock_find = MagicMock(status_code=200)
            mock_find.json.return_value = [{"place_id": "sapporo-1", "name": "Sapporo", "country": "Japan"}]
            mock_point = MagicMock(status_code=200)
            mock_point.json.return_value = {
                "current": {"temperature": 5.0, "summary": "Rainy", "wind": {"speed": 3.0, "dir": "W"}},
                "hourly": {"data": [{"date": "2026-09-24T12:00:00", "temperature": 4.5, "summary": "Rain"}]}
            }
            mock_get.side_effect = [mock_find, mock_point]

            snapshot = fetch_real_time_weather("Sapporo")
            self.assertEqual(snapshot.status, "ok")
            self.assertEqual(snapshot.data["current"]["temperature_c"], 5.0)
            self.assertEqual(len(snapshot.data["hourly_forecast"]), 1)
        finally:
            config.METEOSOURCE_API_KEY = original_key

    @patch("external_data.weather.requests.get")
    def test_15_weather_partial_missing_hourly(self, mock_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "valid_key"
        try:
            mock_find = MagicMock(status_code=200)
            mock_find.json.return_value = [{"place_id": "otaru-1", "name": "Otaru", "country": "Japan"}]
            mock_point = MagicMock(status_code=200)
            mock_point.json.return_value = {
                "current": {"temperature": 2.0, "summary": "Cloudy"},
                "hourly": {"data": []}
            }
            mock_get.side_effect = [mock_find, mock_point]

            snapshot = fetch_real_time_weather("Otaru")
            self.assertEqual(snapshot.status, "partial")
            self.assertIn("missing hourly", snapshot.notice.lower())
        finally:
            config.METEOSOURCE_API_KEY = original_key

    @patch("external_data.weather.requests.get")
    def test_16_weather_timeout_handling(self, mock_get):
        original_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "valid_key"
        try:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout fetching point")
            snapshot = fetch_real_time_weather("Sapporo")
            self.assertEqual(snapshot.status, "unavailable")
            self.assertEqual(snapshot.error_code, "TIMEOUT")
        finally:
            config.METEOSOURCE_API_KEY = original_key


if __name__ == "__main__":
    unittest.main()
