import pytest
from datetime import datetime

from cogs.player_sync_provider import auth_headers, normalize_generic_roster, normalize_mapping, should_run_daily


def test_generic_mapping_and_no_auth():
    mapping = normalize_mapping('{"members":"data.players","id":"id","name":"name","power":"p","furnace":"f","state":"s"}')
    roster = normalize_generic_roster({"data":{"players":[{"id":7,"name":"A","p":12,"f":3,"s":9}]}}, mapping)
    assert roster["7"]["furnace_level"] == 3
    assert auth_headers("none", "") == {}


def test_auth_uses_environment_not_stored_secret(monkeypatch):
    monkeypatch.setenv("SYNC_SECRET", "hidden")
    assert auth_headers("bearer", "SYNC_SECRET")["Authorization"] == "Bearer hidden"
    assert auth_headers("api_key", "SYNC_SECRET", "X-Key")["X-Key"] == "hidden"
    assert auth_headers("basic", "SYNC_SECRET")["Authorization"].startswith("Basic ")


def test_invalid_provider_response_and_missing_credential_are_safe():
    with pytest.raises(ValueError):
        normalize_generic_roster({"members":[{}]}, {"members":"members", "id":"id"})
    with pytest.raises(ValueError):
        auth_headers("bearer", "MISSING_SYNC_SECRET")


def test_daily_schedule_respects_disable_time_and_persisted_run_marker():
    now = datetime(2026, 8, 11, 3, 30)
    assert not should_run_daily(False, "03:30", None, now)
    assert not should_run_daily(True, "03:29", None, now)
    assert not should_run_daily(True, "03:30", "2026-08-11", now)
    assert should_run_daily(True, "03:30", "2026-08-10", now)
