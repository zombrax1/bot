import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

import discord

from cogs.alliance_sync import ProviderModal, ProviderView
from cogs.player_sync_provider import auth_headers, normalize_generic_roster, normalize_mapping, should_run_daily


class _Cursor:
    def __init__(self, config):
        self.config = config

    def execute(self, _sql, values):
        self.config["enabled"] = values[0]


class _Connection:
    def commit(self):
        pass


class _Cog:
    def __init__(self, **updates):
        self.config = {
            "enabled": 0,
            "provider": "zomradar",
            "url": "",
            "auth_type": "none",
            "secret_env": "",
            "header_name": "",
            "mapping_json": '{"members":"members","id":"id"}',
            "daily_time": "00:00",
            "last_daily_date": None,
            "validated": 0,
        }
        self.config.update(updates)
        self.cursor_settings = _Cursor(self.config)
        self.conn_settings = _Connection()

    def provider_config(self):
        return dict(self.config)


def _interaction():
    interaction = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    return interaction


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


def test_configure_modal_components_fit_discord_limits():
    async def run():
        modal = ProviderModal(_Cog())
        assert len(modal.children) == 5
        assert all(len(item.label) <= 45 for item in modal.children)

    asyncio.run(run())


def test_configure_immediately_opens_provider_modal():
    async def run():
        view = ProviderView(_Cog())
        interaction = _interaction()

        await view.configure.callback(interaction)

        interaction.response.send_modal.assert_awaited_once()
        assert isinstance(interaction.response.send_modal.await_args.args[0], ProviderModal)

    asyncio.run(run())


def test_toggle_acknowledges_and_visibly_confirms_new_state():
    async def run():
        cog = _Cog()
        view = ProviderView(cog)
        interaction = _interaction()
        assert view.toggle.style is discord.ButtonStyle.success
        assert view.toggle.label == "Enable Sync"

        await view.toggle.callback(interaction)

        interaction.response.defer.assert_awaited_once()
        interaction.edit_original_response.assert_awaited_once()
        assert cog.config["enabled"] == 1
        assert view.toggle.style is discord.ButtonStyle.danger
        assert view.toggle.label == "Disable Sync"
        embed = interaction.edit_original_response.await_args.kwargs["embed"]
        assert "Enabled" in embed.description
        assert embed.fields[0].name == "Status updated"

    asyncio.run(run())


def test_provider_test_defers_before_reporting_missing_url():
    async def run():
        view = ProviderView(_Cog(provider="generic"))
        interaction = _interaction()

        await view.test_provider.callback(interaction)

        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()

    asyncio.run(run())
