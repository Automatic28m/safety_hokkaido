import json
import unittest
from external_data.models import LiveDataSnapshot


class TestLiveDataSnapshot(unittest.TestCase):
    def test_01_snapshot_full_attributes(self):
        snapshot = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope="Hokkaido",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z",
            expires_at="2026-09-24T08:05:00Z",
            data={"earthquakes": {"count": 0}},
            source_url="https://www.jma.go.jp/bosai/quake/",
            error_code=None,
            notice="Active"
        )
        self.assertEqual(snapshot.provider, "jma")
        self.assertEqual(snapshot.kind, "disaster")
        self.assertEqual(snapshot.scope, "Hokkaido")
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.fetched_at, "2026-09-24T08:00:00Z")
        self.assertEqual(snapshot.expires_at, "2026-09-24T08:05:00Z")
        self.assertEqual(snapshot.data, {"earthquakes": {"count": 0}})
        self.assertEqual(snapshot.source_url, "https://www.jma.go.jp/bosai/quake/")
        self.assertIsNone(snapshot.error_code)
        self.assertEqual(snapshot.notice, "Active")

    def test_02_snapshot_minimal_attributes(self):
        snapshot = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="unavailable",
            fetched_at="2026-09-24T08:00:00Z"
        )
        self.assertEqual(snapshot.provider, "meteosource")
        self.assertEqual(snapshot.status, "unavailable")
        self.assertIsNone(snapshot.expires_at)
        self.assertIsNone(snapshot.data)
        self.assertIsNone(snapshot.source_url)
        self.assertIsNone(snapshot.error_code)
        self.assertIsNone(snapshot.notice)

    def test_03_to_dict_method(self):
        snapshot = LiveDataSnapshot(
            provider="jr_hokkaido_simulator",
            kind="train",
            scope="Rapid Airport",
            status="mocked",
            fetched_at="2026-09-24T08:00:00Z",
            data={"operational_state": "delayed"}
        )
        d = snapshot.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["status"], "mocked")
        self.assertEqual(d["provider"], "jr_hokkaido_simulator")
        self.assertEqual(d["data"]["operational_state"], "delayed")

    def test_04_to_json_method(self):
        snapshot = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope="Hokkaido",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        json_str = snapshot.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["scope"], "Hokkaido")

    def test_05_str_magic_method(self):
        snapshot = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Otaru",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        s = str(snapshot)
        self.assertTrue(s.startswith("{"))
        parsed = json.loads(s)
        self.assertEqual(parsed["scope"], "Otaru")

    def test_06_dict_getitem_valid_key(self):
        snapshot = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        self.assertEqual(snapshot["provider"], "meteosource")
        self.assertEqual(snapshot["scope"], "Sapporo")

    def test_07_dict_getitem_invalid_key_raises(self):
        snapshot = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        with self.assertRaises(AttributeError):
            _ = snapshot["non_existent_key"]

    def test_08_contains_operator(self):
        snapshot = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        self.assertIn("status", snapshot)
        self.assertIn("provider", snapshot)
        self.assertNotIn("random_field_xyz", snapshot)

    def test_09_dict_get_with_defaults(self):
        snapshot = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope="Hokkaido",
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        self.assertEqual(snapshot.get("provider"), "jma")
        self.assertEqual(snapshot.get("unknown_key", "default_val"), "default_val")
        self.assertIsNone(snapshot.get("unknown_key"))

    def test_10_scope_as_dict_contract(self):
        scope_dict = {"region": "Hokkaido", "sub_office": "016000"}
        snapshot = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope=scope_dict,
            status="ok",
            fetched_at="2026-09-24T08:00:00Z"
        )
        self.assertIsInstance(snapshot.scope, dict)
        self.assertEqual(snapshot.scope["region"], "Hokkaido")
        self.assertEqual(snapshot["scope"]["sub_office"], "016000")
        parsed = json.loads(snapshot.to_json())
        self.assertEqual(parsed["scope"]["region"], "Hokkaido")


if __name__ == "__main__":
    unittest.main()
