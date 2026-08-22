"""Shared pytest fixtures for the Tibber Vehicle test suite.

Uses pytest-homeassistant-custom-component, which supplies the `hass`
fixture (an in-process HA core instance) and auto-enables custom
integration loading for anything under custom_components/. See
docs/DEVELOPMENT.md and docs/TESTING.md for how these tests are structured
and how to run them.
"""
from __future__ import annotations

import pytest

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.tibber_vehicle.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom_components/ during tests (see the plugin's docs)."""
    yield


@pytest.fixture
async def setup_credentials(hass: HomeAssistant) -> None:
    """Register a fake Application Credential so the config flow can start.

    Mirrors homeassistant/components/spotify/conftest.py's fixture of the
    same name and purpose — every OAuth2-based config flow test needs this
    before `hass.config_entries.flow.async_init` will get past the
    "pick_implementation" step.
    """
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential("CLIENT_ID", "CLIENT_SECRET"),
        DOMAIN,
    )
