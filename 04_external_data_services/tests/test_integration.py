import unittest
from external_data.models import LiveDataSnapshot
from external_data.tools import (
    get_real_time_weather,
    get_disaster_warnings,
    check_train_status,
    WEATHER_TOOL_SCHEMA,
    DISASTER_TOOL_SCHEMA,
    TRAIN_TOOL_SCHEMA
)


class TestIntegration(unittest.TestCase):
    def test_01_weather_schema_structure(self):
        self.assertEqual(WEATHER_TOOL_SCHEMA["type"], "function")
        func = WEATHER_TOOL_SCHEMA["function"]
        self.assertEqual(func["name"], "get_weather_for_city")
        self.assertIn("city", func["parameters"]["properties"])
        self.assertIn("city", func["parameters"]["required"])

    def test_02_disaster_schema_structure(self):
        self.assertEqual(DISASTER_TOOL_SCHEMA["type"], "function")
        func = DISASTER_TOOL_SCHEMA["function"]
        self.assertEqual(func["name"], "get_disaster_warnings")
        self.assertIn("region", func["parameters"]["properties"])

    def test_03_train_schema_structure(self):
        self.assertEqual(TRAIN_TOOL_SCHEMA["type"], "function")
        func = TRAIN_TOOL_SCHEMA["function"]
        self.assertEqual(func["name"], "check_train_status")
        self.assertIn("line_name", func["parameters"]["properties"])

    def test_04_train_status_mocked_contract(self):
        res = check_train_status("Rapid Airport")
        self.assertIsInstance(res, LiveDataSnapshot)
        self.assertEqual(res.status, "mocked")
        self.assertEqual(res.provider, "jr_hokkaido_simulator")
        self.assertEqual(res.kind, "train")
        self.assertIsNotNone(res.fetched_at)
        self.assertIsNotNone(res.expires_at)
        self.assertIn("Simulated status", res.notice)

    def test_05_disaster_warnings_live_fetch(self):
        res = get_disaster_warnings("Hokkaido")
        self.assertIsInstance(res, LiveDataSnapshot)
        self.assertEqual(res.provider, "jma")
        self.assertEqual(res.kind, "disaster")
        self.assertIn(res.status, ["ok", "unavailable", "stale"])
        self.assertIsNotNone(res.fetched_at)
        if res.status == "ok" or (res.status == "unavailable" and res.data):
            self.assertIsNotNone(res.data)
            self.assertIn("earthquakes", res.data)
            self.assertIn("meteorological_warnings", res.data)

    def test_06_weather_snapshot_contract(self):
        res = get_real_time_weather("Sapporo")
        self.assertIsInstance(res, LiveDataSnapshot)
        self.assertEqual(res.provider, "meteosource")
        self.assertEqual(res.kind, "weather")
        self.assertIn(res.status, ["ok", "partial", "unavailable", "stale"])
        self.assertIsNotNone(res.fetched_at)

    def test_07_disaster_specific_subregion_office(self):
        # Hakodate maps to office 017000
        res = get_disaster_warnings("Hakodate")
        self.assertIsInstance(res, LiveDataSnapshot)
        if res.status == "ok" or (res.status == "unavailable" and res.data):
            warn = res.data["meteorological_warnings"]
            self.assertEqual(warn["office_code"], "017000")

    def test_08_reexport_via_backend_src_tools(self):
        from src.tools import (
            get_real_time_weather as be_weather,
            get_disaster_warnings as be_disaster,
            check_train_status as be_train,
            WEATHER_TOOL_SCHEMA as be_ws,
            DISASTER_TOOL_SCHEMA as be_ds,
            TRAIN_TOOL_SCHEMA as be_ts
        )
        self.assertIs(be_weather, get_real_time_weather)
        self.assertIs(be_disaster, get_disaster_warnings)
        self.assertIs(be_train, check_train_status)
        self.assertEqual(be_ws, WEATHER_TOOL_SCHEMA)
        self.assertEqual(be_ds, DISASTER_TOOL_SCHEMA)
        self.assertEqual(be_ts, TRAIN_TOOL_SCHEMA)


if __name__ == "__main__":
    unittest.main()
