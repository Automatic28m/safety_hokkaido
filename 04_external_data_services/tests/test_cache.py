import unittest
from datetime import datetime, timezone, timedelta
from external_data.models import LiveDataSnapshot
from external_data.cache import CacheStore, utc_now_iso


class TestCacheStore(unittest.TestCase):
    def setUp(self):
        self.cache = CacheStore()

    def test_01_cache_miss_returns_none(self):
        res = self.cache.get("meteosource", "weather", "NonExistentCity")
        self.assertIsNone(res)

    def test_02_cache_set_and_get_valid(self):
        curr_time = utc_now_iso()
        snap = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="ok",
            fetched_at=curr_time,
            source_url="https://www.meteosource.com",
            data={"temperature_c": 12.0}
        )
        self.cache.set(snap, ttl_seconds=300)
        retrieved = self.cache.get("meteosource", "weather", "Sapporo")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.status, "ok")
        self.assertEqual(retrieved.fetched_at, curr_time)
        self.assertEqual(retrieved.data["temperature_c"], 12.0)

    def test_03_cache_case_insensitivity(self):
        curr_time = utc_now_iso()
        snap = LiveDataSnapshot(
            provider="MeteoSource",
            kind="WEATHER",
            scope="Sapporo",
            status="ok",
            fetched_at=curr_time
        )
        self.cache.set(snap, ttl_seconds=300)
        retrieved = self.cache.get("meteosource", "weather", "sapporo")
        self.assertIsNotNone(retrieved)

    def test_04_cache_distinct_keys_do_not_collide(self):
        curr_time = utc_now_iso()
        snap1 = LiveDataSnapshot(provider="meteosource", kind="weather", scope="Sapporo", status="ok", fetched_at=curr_time)
        snap2 = LiveDataSnapshot(provider="meteosource", kind="weather", scope="Otaru", status="ok", fetched_at=curr_time)

        self.cache.set(snap1, ttl_seconds=300)
        self.cache.set(snap2, ttl_seconds=300)

        self.assertEqual(self.cache.get("meteosource", "weather", "Sapporo").scope, "Sapporo")
        self.assertEqual(self.cache.get("meteosource", "weather", "Otaru").scope, "Otaru")

    def test_05_cache_dict_scope_supported(self):
        curr_time = utc_now_iso()
        scope_dict = {"region": "Hokkaido", "office": "016000"}
        snap = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope=scope_dict,
            status="ok",
            fetched_at=curr_time
        )
        self.cache.set(snap, ttl_seconds=300)
        retrieved = self.cache.get("jma", "disaster", scope_dict)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.scope["office"], "016000")

    def test_06_cache_expired_returns_none_on_get(self):
        past_time = (datetime.now(timezone.utc) - timedelta(seconds=120)).strftime("%Y-%m-%dT%H:%M:%SZ")
        expired_time = (datetime.now(timezone.utc) - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

        snap = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope="Hokkaido",
            status="ok",
            fetched_at=past_time,
            expires_at=expired_time
        )
        self.cache.set(snap, ttl_seconds=0)
        self.assertIsNone(self.cache.get("jma", "disaster", "Hokkaido"))

    def test_07_get_stale_returns_expired_snapshot_marked_as_stale(self):
        past_time = (datetime.now(timezone.utc) - timedelta(seconds=600)).strftime("%Y-%m-%dT%H:%M:%SZ")
        expired_time = (datetime.now(timezone.utc) - timedelta(seconds=300)).strftime("%Y-%m-%dT%H:%M:%SZ")

        snap = LiveDataSnapshot(
            provider="jma",
            kind="disaster",
            scope="Hokkaido",
            status="ok",
            fetched_at=past_time,
            expires_at=expired_time,
            source_url="https://www.jma.go.jp/bosai/quake/",
            data={"count": 2}
        )
        self.cache.set(snap, ttl_seconds=0)

        stale = self.cache.get_stale("jma", "disaster", "Hokkaido")
        self.assertIsNotNone(stale)
        self.assertEqual(stale.status, "stale")
        self.assertEqual(stale.fetched_at, past_time)
        self.assertEqual(stale.source_url, "https://www.jma.go.jp/bosai/quake/")
        self.assertIn("stale", stale.notice.lower())

    def test_08_get_stale_on_non_existent_key_returns_none(self):
        res = self.cache.get_stale("unknown", "unknown", "unknown")
        self.assertIsNone(res)

    def test_09_cache_clear_removes_all_entries(self):
        curr_time = utc_now_iso()
        snap = LiveDataSnapshot(provider="jma", kind="disaster", scope="Hokkaido", status="ok", fetched_at=curr_time)
        self.cache.set(snap, ttl_seconds=300)
        self.assertIsNotNone(self.cache.get("jma", "disaster", "Hokkaido"))

        self.cache.clear()
        self.assertIsNone(self.cache.get("jma", "disaster", "Hokkaido"))

    def test_10_cache_deep_copy_isolation(self):
        curr_time = utc_now_iso()
        original_data = {"temperature_c": 10.0}
        snap = LiveDataSnapshot(
            provider="meteosource",
            kind="weather",
            scope="Sapporo",
            status="ok",
            fetched_at=curr_time,
            data=original_data
        )
        self.cache.set(snap, ttl_seconds=300)

        # Mutate retrieved object
        retrieved = self.cache.get("meteosource", "weather", "Sapporo")
        retrieved.data["temperature_c"] = 999.0

        # Verify second retrieval still contains original data
        retrieved_again = self.cache.get("meteosource", "weather", "Sapporo")
        self.assertEqual(retrieved_again.data["temperature_c"], 10.0)


if __name__ == "__main__":
    unittest.main()
