import os
import unittest
from unittest.mock import patch, MagicMock
import requests
try:
    from config import config
except ImportError:
    class _FallbackConfig:
        METEOSOURCE_API_KEY = os.getenv("METEOSOURCE_API_KEY", "")
    config = _FallbackConfig()
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache
from external_data.train import fetch_train_status
from external_data.disaster import fetch_disaster_warnings
from external_data.weather import fetch_real_time_weather


class TestAdapters(unittest.TestCase):
    def setUp(self):
        global_cache.clear()

    # ── Train Adapter Tests (Live Transit) ──────────────────────
    @patch("external_data.trains.requests.get")
    def test_01_train_status_live_success_normal(self, mock_get):
        mock_resp = MagicMock(status_code=200, text="""
        <table>
        <tr><td><a href="...">千歳線</a></td><td>平常運転</td><td>平常運転です</td></tr>
        </table>
        """)
        mock_get.return_value = mock_resp
        snapshot = fetch_train_status("Rapid Airport")
        self.assertIsInstance(snapshot, LiveDataSnapshot)
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.kind, "train")
        self.assertFalse(snapshot.data["is_delayed"])
        self.assertEqual(snapshot.data["status"], "normal")

    @patch("external_data.trains.requests.get")
    def test_02_train_live_disruption_detected(self, mock_get):
        mock_resp = MagicMock(status_code=200, text="""
        <table>
        <tr><td><a href="...">千歳線</a></td><td>遅延</td><td>大雪の影響で遅れが出ています</td></tr>
        </table>
        """)
        mock_get.return_value = mock_resp
        snap = fetch_train_status("Rapid Airport")
        self.assertEqual(snap.status, "ok")
        self.assertTrue(snap.data["is_delayed"])
        self.assertEqual(snap.data["status"], "disrupted")
        self.assertIn("千歳線", snap.data["disrupted_lines"][0]["line_name"])

    @patch("external_data.trains.requests.get")
    def test_03_train_timeout_returns_unavailable(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        snap = fetch_train_status("Hakodate Line")
        self.assertEqual(snap.status, "unavailable")
        self.assertEqual(snap.error_code, "TIMEOUT")
        self.assertTrue(snap.degraded)

    def test_04_train_invalid_input_returns_unavailable(self):
        snapshot = fetch_train_status("InvalidLine!@#$")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    @patch("external_data.trains.requests.get")
    def test_05_train_zero_safety_judgment(self, mock_get):
        mock_resp = MagicMock(status_code=200, text="""
        <table>
        <tr><td><a href="...">千歳線</a></td><td>平常運転</td><td>平常運転です</td></tr>
        </table>
        """)
        mock_get.return_value = mock_resp
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
        self.assertEqual(snapshot.status, "unavailable")
        self.assertTrue(snapshot.data["earthquakes"]["is_available"])
        self.assertFalse(snapshot.data["meteorological_warnings"]["is_available"])
        self.assertIn("Weather warning feed unavailable", snapshot.notice)
        self.assertIn("Earthquake data available", snapshot.notice)

    @patch("external_data.disaster.requests.get")
    def test_08_disaster_partial_when_quake_feed_fails(self, mock_get):
        mock_quake = MagicMock(status_code=503)
        mock_warn = MagicMock(status_code=200)
        mock_warn.json.return_value = {"headlineText": "Gale warning"}
        mock_get.side_effect = [mock_quake, mock_warn]

        snapshot = fetch_disaster_warnings("Hokkaido")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertFalse(snapshot.data["earthquakes"]["is_available"])
        self.assertTrue(snapshot.data["meteorological_warnings"]["is_available"])
        self.assertIn("Earthquake feed unavailable", snapshot.notice)
        self.assertIn("Weather warnings available", snapshot.notice)

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

    # ── Yahoo Transit Live Adapter Tests ─────────────────────────
    @patch("external_data.trains.requests.get")
    def test_17_yahoo_transit_success(self, mock_get):
        from external_data.trains import fetch_yahoo_transit_status
        sample_html = (
            "<table>"
            "<tr><td><a href='/1'>函館本線[小樽～札幌]</a></td><td>平常運転</td><td>事故・遅延情報はありません</td></tr>"
            "<tr><td><a href='/2'>千歳線</a></td><td>遅延</td><td>大雪の影響で一部遅延</td></tr>"
            "</table>"
        )
        mock_resp = MagicMock(status_code=200, text=sample_html)
        mock_get.return_value = mock_resp

        snapshot = fetch_yahoo_transit_status("All")
        self.assertIsInstance(snapshot, LiveDataSnapshot)
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider, "yahoo_transit")
        self.assertEqual(snapshot.kind, "train")
        self.assertEqual(snapshot.data["total_lines_monitored"], 2)
        self.assertEqual(snapshot.data["disruptions_count"], 1)
        self.assertTrue(snapshot.data["has_disruptions"])

    @patch("external_data.trains.requests.get")
    def test_18_yahoo_transit_timeout(self, mock_get):
        from external_data.trains import fetch_yahoo_transit_status
        mock_get.side_effect = requests.exceptions.Timeout("Yahoo timed out")
        snapshot = fetch_yahoo_transit_status("Rapid Airport")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "TIMEOUT")

    def test_19_yahoo_transit_invalid_line(self):
        from external_data.trains import fetch_yahoo_transit_status
        snapshot = fetch_yahoo_transit_status("InvalidLine!@#$")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    # ── Flight Adapter Tests ─────────────────────────────────────
    @patch("external_data.flights._get_api_key")
    def test_20_flight_missing_api_key(self, mock_key):
        from external_data.flights import fetch_flight_status
        mock_key.return_value = ""
        snapshot = fetch_flight_status("CTS")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "CONFIG_MISSING")

    @patch("external_data.flights._get_api_key")
    @patch("external_data.flights.requests.get")
    def test_21_flight_success(self, mock_get, mock_key):
        from external_data.flights import fetch_flight_status
        mock_key.return_value = "fake_key"
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "data": [
                {
                    "flight_status": "scheduled",
                    "flight": {"iata": "NH123"},
                    "airline": {"name": "All Nippon Airways"},
                    "departure": {"airport": "Tokyo Haneda", "iata": "HND"},
                    "arrival": {"airport": "New Chitose", "iata": "CTS", "scheduled": "2026-10-03T10:00:00", "delay": 0}
                }
            ]
        }
        mock_get.return_value = mock_resp

        snapshot = fetch_flight_status("CTS")
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider, "aviationstack")
        self.assertEqual(snapshot.kind, "flight")
        self.assertEqual(snapshot.data["total_flights"], 1)

    @patch("external_data.flights._get_api_key")
    @patch("external_data.flights.requests.get")
    def test_22_flight_quota_or_api_error(self, mock_get, mock_key):
        from external_data.flights import fetch_flight_status
        mock_key.return_value = "fake_key"
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "error": {
                "code": "usage_limit_reached",
                "info": "Your monthly usage limit has been reached."
            }
        }
        mock_get.return_value = mock_resp

        snapshot = fetch_flight_status("CTS")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "USAGE_LIMIT_REACHED")

    def test_23_flight_invalid_airport_code(self):
        from external_data.flights import fetch_flight_status
        snapshot = fetch_flight_status("INVALID_LONG_CODE!@#")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    # ── Road Adapter Tests ───────────────────────────────────────
    @patch("external_data.roads.requests.get")
    def test_24_road_success(self, mock_get):
        from external_data.roads import fetch_road_status
        mock_resp = MagicMock(status_code=200, text="<html><body>道路情報 通行規制情報</body></html>")
        mock_get.return_value = mock_resp

        snapshot = fetch_road_status("Hokkaido")
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider, "hokkaido_road_info")
        self.assertEqual(snapshot.kind, "road")
        self.assertTrue(snapshot.data["portal_accessible"])

    @patch("external_data.roads.requests.get")
    def test_25_road_timeout(self, mock_get):
        from external_data.roads import fetch_road_status
        mock_get.side_effect = requests.exceptions.Timeout("Road portal timeout")
        snapshot = fetch_road_status("Hokkaido")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "TIMEOUT")

    def test_26_road_invalid_region(self):
        from external_data.roads import fetch_road_status
        snapshot = fetch_road_status("TokyoRegion123")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertEqual(snapshot.error_code, "INVALID_INPUT")

    # ── Tools Wrapper Tests ──────────────────────────────────────
    def test_27_tools_schemas_registered(self):
        from external_data.tools import (
            LIVE_TRAIN_TOOL_SCHEMA,
            FLIGHT_TOOL_SCHEMA,
            ROAD_TOOL_SCHEMA,
            check_live_train_status,
            check_flight_status,
            check_road_status
        )
        self.assertEqual(LIVE_TRAIN_TOOL_SCHEMA["function"]["name"], "check_live_train_status")
        self.assertEqual(FLIGHT_TOOL_SCHEMA["function"]["name"], "check_flight_status")
        self.assertEqual(ROAD_TOOL_SCHEMA["function"]["name"], "check_road_status")
        self.assertTrue(callable(check_live_train_status))
        self.assertTrue(callable(check_flight_status))
        self.assertTrue(callable(check_road_status))

    # ── ODPT & Live Train Flag Tests ────────────────────────────
    @patch("external_data.trains.requests.get")
    def test_28_odpt_train_success(self, mock_get):
        from external_data.trains import fetch_live_train_status
        original_key = os.getenv("ODPT_API_KEY")
        os.environ["ODPT_API_KEY"] = "mock_odpt_key"
        try:
            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = [
                {
                    "odpt:railway": "odpt.Railway:JR-Hokkaido.Chitose",
                    "odpt:trainInformationText": "平常運転"
                }
            ]
            mock_get.return_value = mock_resp
            snapshot = fetch_live_train_status("Chitose Line")
            self.assertEqual(snapshot.status, "ok")
            self.assertEqual(snapshot.provider, "odpt_public_transport")
            self.assertFalse(snapshot.data["is_delayed"])
        finally:
            if original_key is not None:
                os.environ["ODPT_API_KEY"] = original_key
            else:
                os.environ.pop("ODPT_API_KEY", None)

    def test_29_use_live_train_disabled(self):
        from external_data.trains import fetch_live_train_status
        original_flag = os.getenv("USE_LIVE_TRAIN")
        os.environ["USE_LIVE_TRAIN"] = "false"
        try:
            snapshot = fetch_live_train_status("Rapid Airport")
            self.assertEqual(snapshot.status, "unavailable")
            self.assertEqual(snapshot.error_code, "LIVE_TRAIN_DISABLED")
            self.assertTrue(snapshot.degraded)
        finally:
            if original_flag is not None:
                os.environ["USE_LIVE_TRAIN"] = original_flag
            else:
                os.environ.pop("USE_LIVE_TRAIN", None)


if __name__ == "__main__":
    unittest.main()

