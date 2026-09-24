"""Test runner executing Mock Contract Tests, Boot Integration, and E2E Scenarios."""

import json
from unittest.mock import patch, MagicMock
import requests
from config import config
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache
from external_data.tools import (
    get_real_time_weather,
    get_disaster_warnings,
    check_train_status
)


def run_stage_1_mock_contract_test():
    print("\n" + "=" * 65)
    print("STAGE 1: MOCK CONTRACT TESTS (Schema & Normalization)")
    print("=" * 65)

    global_cache.clear()

    # 1. Train contract
    train_res = check_train_status("Rapid Airport")
    print("\n[Train Status Contract]")
    print(f"Provider: {train_res.provider}")
    print(f"Status:   {train_res.status} (Verified: Marked as mocked)")
    print(f"Notice:   {train_res.notice}")
    print(f"Data:     {json.dumps(train_res.data, indent=2)}")
    assert train_res.status == "mocked", "Train status must be mocked"
    assert "safety_level" not in train_res.data, "Node 04 must not emit safety_level"

    # 2. Disaster contract (live JMA test)
    disaster_res = get_disaster_warnings("Hokkaido")
    print("\n[Disaster Warnings Contract (Live JMA)]")
    print(f"Provider: {disaster_res.provider}")
    print(f"Status:   {disaster_res.status}")
    print(f"Fetched:  {disaster_res.fetched_at}")
    print(f"Quakes:   {disaster_res.data['earthquakes']['count']} Hokkaido event(s) detected")
    print(f"Headline: {disaster_res.data['meteorological_warnings']['active_headline']}")
    assert disaster_res.status in ["ok", "unavailable", "stale"], "Unexpected disaster status"

    # 3. Weather contract (missing config handling)
    orig_key = config.METEOSOURCE_API_KEY
    config.METEOSOURCE_API_KEY = ""
    try:
        weather_res = get_real_time_weather("Sapporo")
        print("\n[Weather Contract (No API Key Handling)]")
        print(f"Provider: {weather_res.provider}")
        print(f"Status:   {weather_res.status}")
        print(f"Code:     {weather_res.error_code}")
        print(f"Notice:   {weather_res.notice}")
        assert weather_res.status == "unavailable"
        assert weather_res.error_code == "CONFIG_MISSING"
    finally:
        config.METEOSOURCE_API_KEY = orig_key

    print("\n>>> STAGE 1 PASSED: All outputs comply with LiveDataSnapshot schema.")


def run_stage_2_boot_integration_test():
    print("\n" + "=" * 65)
    print("STAGE 2: BOOT INTEGRATION TESTS (Module Imports & Re-exports)")
    print("=" * 65)

    try:
        from src.tools import (
            get_real_time_weather as be_weather,
            get_disaster_warnings as be_disaster,
            check_train_status as be_train
        )
        print("  - Backend re-export from src.tools: OK")

        from external_data import (
            LiveDataSnapshot as LibSnapshot,
            global_cache as lib_cache
        )
        print("  - External data library package exports: OK")

        # Test dictionary-like compatibility for caller modules
        snap = LibSnapshot(
            provider="jma",
            kind="disaster",
            scope="Hokkaido",
            status="ok",
            fetched_at="2026-09-24T10:00:00Z",
            data={"count": 0}
        )
        assert snap["provider"] == "jma"
        assert snap.get("status") == "ok"
        print("  - Backward-compatibility (dict access & serialization): OK")

        print("\n>>> STAGE 2 PASSED: Module boot and interoperability verified.")
    except Exception as e:
        print(f"STAGE 2 FAILED: {e}")
        raise


def run_stage_3_scenario_tests():
    print("\n" + "=" * 65)
    print("STAGE 3: END-TO-END SCENARIO TESTING (3 Required Scenarios)")
    print("=" * 65)

    global_cache.clear()

    # ─────────────────────────────────────────────────────────────
    # Scenario 1: Safe Scenario
    # ─────────────────────────────────────────────────────────────
    print("\n[Scenario 1: Safe / Normal Live Weather Scenario]")
    with patch("external_data.weather.requests.get") as mock_w:
        orig_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "test_key"
        try:
            m_find = MagicMock(status_code=200)
            m_find.json.return_value = [{"place_id": "sapporo-1", "name": "Sapporo", "country": "Japan"}]
            m_point = MagicMock(status_code=200)
            m_point.json.return_value = {
                "current": {
                    "temperature": 18.0,
                    "summary": "Clear and calm",
                    "wind": {"speed": 1.5, "dir": "N"},
                    "precipitation": {"total": 0.0, "type": "none"}
                },
                "hourly": {"data": [{"date": "2026-09-24T12:00:00", "temperature": 17.5, "summary": "Clear"}]}
            }
            mock_w.side_effect = [m_find, m_point]

            res = get_real_time_weather("Sapporo")
            print(f"  Result Status: {res.status}")
            print(f"  City:          {res.data['city_name']}")
            print(f"  Temperature:   {res.data['current']['temperature_c']} C ({res.data['current']['summary']})")
            print(f"  Source URL:    {res.source_url}")
            assert res.status == "ok"
            assert res.data["current"]["temperature_c"] == 18.0
            print("  Status Tag:    [SAFE] Provenance intact.")
        finally:
            config.METEOSOURCE_API_KEY = orig_key

    # ─────────────────────────────────────────────────────────────
    # Scenario 2: Degraded Scenario (Timeout / Provider Failure)
    # ─────────────────────────────────────────────────────────────
    print("\n[Scenario 2: Degraded Scenario (Provider Timeout / Outage)]")
    global_cache.clear()
    with patch("external_data.weather.requests.get") as mock_w, \
         patch("external_data.disaster.requests.get") as mock_d:

        orig_key = config.METEOSOURCE_API_KEY
        config.METEOSOURCE_API_KEY = "test_key"
        try:
            # Simulate network timeout
            mock_w.side_effect = requests.exceptions.Timeout("Connection timed out after 5.0s")
            mock_d.side_effect = requests.exceptions.ConnectionError("DNS resolution failed")

            w_res = get_real_time_weather("Sapporo")
            d_res = get_disaster_warnings("Hokkaido")

            print(f"  Weather Status:  {w_res.status} (Error: {w_res.error_code})")
            print(f"  Weather Notice:  {w_res.notice}")
            print(f"  Disaster Status: {d_res.status} (Error: {d_res.error_code})")
            print(f"  Disaster Notice: {d_res.notice}")

            assert w_res.status == "unavailable", "Must not report ok on timeout"
            assert d_res.status == "unavailable", "Must not report ok on connection drop"
            assert "No warnings" not in str(d_res.data), "Must not fabricate success"
            print("  Status Tag:      [WARNING / DEGRADED] Failure captured cleanly without crash.")
        finally:
            config.METEOSOURCE_API_KEY = orig_key

    # ─────────────────────────────────────────────────────────────
    # Scenario 3: Disaster Emergency Scenario
    # ─────────────────────────────────────────────────────────────
    print("\n[Scenario 3: Disaster Emergency Scenario (Major Earthquake Detected)]")
    global_cache.clear()
    with patch("external_data.disaster.requests.get") as mock_d:
        m_quake = MagicMock(status_code=200)
        m_quake.json.return_value = [
            {
                "anm": "釧路沖",
                "en_anm": "Off the Coast of Kushiro",
                "rdt": "2026-09-24T16:00:00+09:00",
                "mag": "7.1",
                "maxi": "6+",
                "cod": "+42.8+145.2-20000/"
            }
        ]
        m_warn = MagicMock(status_code=200)
        m_warn.json.return_value = {
            "reportDatetime": "2026-09-24T16:05:00+09:00",
            "headlineText": "Major Tsunami Warning issued for Pacific coast of Hokkaido."
        }
        mock_d.side_effect = [m_quake, m_warn]

        d_res = get_disaster_warnings("Hokkaido")
        latest = d_res.data["earthquakes"]["latest_event"]
        warn = d_res.data["meteorological_warnings"]

        print(f"  Disaster Status: {d_res.status}")
        print(f"  Quake Detected:  M{latest['magnitude']} at {latest['epicenter_en']} (Intensity {latest['max_intensity']})")
        print(f"  Warning Issued:  {warn['active_headline']}")
        print(f"  Source URL:      {d_res.source_url}")

        assert d_res.status == "ok"
        assert latest["magnitude"] == "7.1"
        assert "Tsunami Warning" in warn["active_headline"]
        print("  Status Tag:      [EMERGENCY EVIDENCE READY] Ready for Node 07 guardrails.")

    print("\n>>> STAGE 3 PASSED: All 3 mandatory scenarios verified successfully.")


def main():
    print("=" * 65)
    print("SAFETY HOKKAIDO - NODE 04 INTEGRATION TEST EXECUTION")
    print("=" * 65)

    run_stage_1_mock_contract_test()
    run_stage_2_boot_integration_test()
    run_stage_3_scenario_tests()

    print("\n" + "=" * 65)
    print("ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY (100% PASS)")
    print("=" * 65)


if __name__ == "__main__":
    main()
