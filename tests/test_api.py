"""Tests for TibberVehicleApiClient.

Covers the retry/backoff/dedup logic added during the pre-1.0.0 review
(docs/DECISIONS.md), which had no coverage proving it works as designed
before this file existed. See docs/TESTING.md for the full test concept.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.tibber_vehicle.api import (
    MAX_RETRIES,
    TibberVehicleApiClient,
    TibberVehicleApiError,
)
from pytest_homeassistant_custom_component.common import load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)

HOMES_URL = "https://data-api.tibber.com/v1/homes"
DEVICES_URL = f"{HOMES_URL}/home-1/devices"


async def _static_token() -> str:
    return "mock-access-token"


def _client(hass: HomeAssistant) -> TibberVehicleApiClient:
    return TibberVehicleApiClient(async_get_clientsession(hass), _static_token)


async def test_get_homes_and_devices_happy_path(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Plain GET calls parse the {"homes": [...]}/{"devices": [...]} envelopes."""
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_one_vehicle.json"))

    client = _client(hass)

    assert await client.async_get_homes() == [{"id": "home-1"}]
    devices = await client.async_get_devices("home-1")
    assert devices[0]["externalId"] == "WVWZZZAAZLD000001"


async def test_async_get_all_vehicles_dedups_across_homes(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The same vehicle listed under two homes is only returned once."""
    aioclient_mock.get(
        HOMES_URL, json={"homes": [{"id": "home-1"}, {"id": "home-2"}]}
    )
    one_vehicle = load_fixture("devices_one_vehicle.json")
    aioclient_mock.get(DEVICES_URL, text=one_vehicle)
    aioclient_mock.get(f"{HOMES_URL}/home-2/devices", text=one_vehicle)

    vehicles = await _client(hass).async_get_all_vehicles()

    assert len(vehicles) == 1
    home_id, device = vehicles[0]
    assert home_id == "home-1"  # first home wins, matching insertion order
    assert device["externalId"] == "WVWZZZAAZLD000001"


async def test_retries_on_429_then_succeeds(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A 429 on the first attempt is retried, not raised, once it then succeeds."""
    call_count = 0

    async def _side_effect(method, url, data):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return AiohttpClientMockResponse(method, url, status=429)
        return AiohttpClientMockResponse(
            method, url, status=200, json={"homes": [{"id": "home-1"}]}
        )

    aioclient_mock.get(HOMES_URL, side_effect=_side_effect)

    with patch(
        "custom_components.tibber_vehicle.api.asyncio.sleep", new=AsyncMock()
    ) as mock_sleep:
        result = await _client(hass).async_get_homes()

    assert result == [{"id": "home-1"}]
    assert call_count == 2
    mock_sleep.assert_awaited_once()


async def test_no_retry_on_401(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """401 means fix the request, not try again - no retry, fails immediately."""
    aioclient_mock.get(HOMES_URL, status=401)

    with (
        patch(
            "custom_components.tibber_vehicle.api.asyncio.sleep", new=AsyncMock()
        ) as mock_sleep,
        pytest.raises(TibberVehicleApiError),
    ):
        await _client(hass).async_get_homes()

    assert len(aioclient_mock.mock_calls) == 1
    mock_sleep.assert_not_awaited()


async def test_exhausts_retries_on_persistent_5xx(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Persistent 503s exhaust all retries and then raise, not loop forever."""
    aioclient_mock.get(HOMES_URL, status=503)

    with (
        patch("custom_components.tibber_vehicle.api.asyncio.sleep", new=AsyncMock()),
        pytest.raises(TibberVehicleApiError),
    ):
        await _client(hass).async_get_homes()

    # Initial attempt + MAX_RETRIES retries.
    assert len(aioclient_mock.mock_calls) == MAX_RETRIES + 1
