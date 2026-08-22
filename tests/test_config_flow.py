"""Tests for the Tibber Vehicle config flow.

Pattern modeled directly on
homeassistant/components/spotify/test_config_flow.py in HA core — the
concrete, working way to test an AbstractOAuth2FlowHandler-based flow
(external-step callback simulated via _encode_jwt + hass_client_no_auth).
Unlike Spotify (which mocks its whole API client class), HTTP calls are
mocked directly via aioclient_mock, since api.py is thin enough that this
exercises our own request/retry/dedup logic too. See docs/TESTING.md for
the full test concept and case list this file implements.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from custom_components.tibber_vehicle.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

TOKEN_URL = "https://thewall.tibber.com/connect/token"
HOMES_URL = "https://data-api.tibber.com/v1/homes"
DEVICES_URL = "https://data-api.tibber.com/v1/homes/home-1/devices"


def _mock_token_response(aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )


async def _start_and_authorize(
    hass: HomeAssistant, hass_client_no_auth: ClientSessionGenerator
) -> str:
    """Start the flow and simulate the browser coming back from Tibber's consent page.

    Returns the flow_id, ready for async_configure() to finish it.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert "data-api-homes-read" in result["url"]
    assert "data-api-vehicles-read" in result["url"]

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    return result["flow_id"]


async def test_abort_if_no_credentials(hass: HomeAssistant) -> None:
    """No Application Credential registered yet -> abort immediately.

    Reason is "missing_credentials", not "missing_configuration" -
    because application_credentials.py makes this domain known to
    async_get_application_credentials() just by existing, the "no
    implementations at all" abort in async_step_pick_implementation always
    takes the missing_credentials branch for us, never
    missing_configuration (that one's for domains with no
    application_credentials.py at all). Confirmed by actually running this
    test, not assumed.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "missing_credentials"


@pytest.mark.usefixtures("current_request_with_host", "setup_credentials")
async def test_full_flow_single_vehicle(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """One home, one vehicle -> a config entry is created for the account."""
    flow_id = await _start_and_authorize(hass, hass_client_no_auth)

    _mock_token_response(aioclient_mock)
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_one_vehicle.json"))

    with patch(
        "custom_components.tibber_vehicle.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(flow_id)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ID.7"
    assert result["result"].unique_id == "home-1"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


@pytest.mark.usefixtures("current_request_with_host", "setup_credentials")
async def test_full_flow_multiple_vehicles(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Two vehicles paired to the account -> both are named in the entry title."""
    flow_id = await _start_and_authorize(hass, hass_client_no_auth)

    _mock_token_response(aioclient_mock)
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_two_vehicles.json"))

    with patch(
        "custom_components.tibber_vehicle.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(flow_id)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ID.7, ID.4"


@pytest.mark.usefixtures("current_request_with_host", "setup_credentials")
async def test_abort_no_vehicle_found(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Account has homes but no paired vehicles -> abort, not a crash."""
    flow_id = await _start_and_authorize(hass, hass_client_no_auth)

    _mock_token_response(aioclient_mock)
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_empty.json"))

    result = await hass.config_entries.flow.async_configure(flow_id)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_vehicle_found"


@pytest.mark.usefixtures("current_request_with_host", "setup_credentials")
async def test_abort_connection_error(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Tibber's API is unreachable while resolving vehicles -> connection_error abort.

    api.py retries 429/5xx three times with a jittered backoff before
    giving up - patch asyncio.sleep so this test doesn't actually wait.
    """
    flow_id = await _start_and_authorize(hass, hass_client_no_auth)

    _mock_token_response(aioclient_mock)
    aioclient_mock.get(HOMES_URL, status=500)

    with patch(
        "custom_components.tibber_vehicle.api.asyncio.sleep", new=AsyncMock()
    ):
        result = await hass.config_entries.flow.async_configure(flow_id)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "connection_error"


@pytest.mark.usefixtures("current_request_with_host", "setup_credentials")
async def test_abort_if_account_already_configured(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Linking the same Tibber account (same home ids) twice aborts, no duplicate."""
    MockConfigEntry(
        domain=DOMAIN,
        title="ID.7",
        unique_id="home-1",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "existing-access-token",
                "refresh_token": "existing-refresh-token",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        },
    ).add_to_hass(hass)

    flow_id = await _start_and_authorize(hass, hass_client_no_auth)

    _mock_token_response(aioclient_mock)
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_one_vehicle.json"))

    result = await hass.config_entries.flow.async_configure(flow_id)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
