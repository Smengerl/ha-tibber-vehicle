"""Tests for Tibber Vehicle's __init__.py (setup/unload).

See docs/TESTING.md for the full test concept and case list.
"""
from __future__ import annotations

import time

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.tibber_vehicle.const import DOMAIN

TOKEN_URL = "https://thewall.tibber.com/connect/token"
HOMES_URL = "https://data-api.tibber.com/v1/homes"
DEVICES_URL = f"{HOMES_URL}/home-1/devices"
DEVICE_DETAIL_URL = f"{HOMES_URL}/home-1/devices/ZGV2aWNlLTE"


def _mock_entry(*, expires_at: float | None = None) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="ID.7",
        unique_id="home-1",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": expires_at if expires_at is not None else time.time() + 3600,
            },
        },
    )


def _mock_vehicle_data(aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_one_vehicle.json"))
    aioclient_mock.get(DEVICE_DETAIL_URL, text=load_fixture("device_detail.json"))


async def test_setup_entry_success(
    hass: HomeAssistant,
    setup_credentials: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A valid, non-expired token sets up cleanly: coordinator populated, platform forwarded."""
    entry = _mock_entry()
    entry.add_to_hass(hass)
    _mock_vehicle_data(aioclient_mock)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert "ZGV2aWNlLTE" in entry.runtime_data.data
    assert hass.states.get("sensor.id_7_battery_level") is not None


async def test_setup_entry_oauth_implementation_unavailable(
    hass: HomeAssistant,
) -> None:
    """No Application Credential ever registered -> ConfigEntryNotReady/retry.

    Deliberately skips the setup_credentials fixture - that's the point.
    """
    entry = _mock_entry()
    entry.add_to_hass(hass)

    result = await hass.config_entries.async_setup(entry.entry_id)

    assert result is False
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_entry_token_refresh_fails(
    hass: HomeAssistant,
    setup_credentials: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An already-expired token that fails to refresh -> ConfigEntryNotReady/retry.

    A non-expired token would short-circuit async_ensure_token_valid()
    without attempting a refresh at all, so the fixture needs an expired
    expires_at to actually exercise this path.
    """
    entry = _mock_entry(expires_at=time.time() - 100)
    entry.add_to_hass(hass)
    aioclient_mock.post(TOKEN_URL, status=400)

    result = await hass.config_entries.async_setup(entry.entry_id)

    assert result is False
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    setup_credentials: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A loaded entry unloads cleanly."""
    entry = _mock_entry()
    entry.add_to_hass(hass)
    _mock_vehicle_data(aioclient_mock)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
