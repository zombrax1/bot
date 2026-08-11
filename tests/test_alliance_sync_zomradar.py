import pytest
import inspect

from cogs.alliance_sync import (
    AllianceSync,
    get_zomradar_api_key,
    normalize_zomradar_roster,
    should_move_after_roster_miss,
    zomradar_queries,
)


def test_normalize_zomradar_roster_requires_complete_data():
    payload = {
        "alliance": {"member_count": 1},
        "members": [{"player_id": 123, "name": "Member", "state": 1755}],
    }
    assert normalize_zomradar_roster(payload)["123"]["name"] == "Member"

    payload["alliance"]["member_count"] = 2
    with pytest.raises(ValueError, match="incomplete"):
        normalize_zomradar_roster(payload)


def test_roster_transfer_starts_on_third_complete_miss():
    assert not should_move_after_roster_miss(1)
    assert not should_move_after_roster_miss(2)
    assert should_move_after_roster_miss(3)


def test_multistate_sync_uses_each_distinct_saved_state():
    users = [
        (1, "A", 0, None, 1451, 0),
        (2, "B", 0, None, 1755, 0),
        (3, "C", 0, None, 1451, 0),
    ]
    assert zomradar_queries("MIX", None, True, users) == [
        (1451, "mix"),
        (1755, "mix"),
    ]
    assert zomradar_queries("DeD", 1755, False, users) == [(1755, "ded")]


def test_process_environment_key_is_preferred(monkeypatch):
    monkeypatch.setenv("ZOMRADAR_API_KEY", "configured")
    assert get_zomradar_api_key() == "configured"


def test_sync_errors_never_publish_request_urls_or_key_names():
    source = inspect.getsource(AllianceSync.check_agslist)
    assert "raise_for_status" not in source
    assert "ZOMRADAR_API_KEY is missing" not in source
    assert "ZomRadar roster fetch failed: {error}" not in source
