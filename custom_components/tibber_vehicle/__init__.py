"""The Tibber Vehicle integration.

Setup shape modeled on Home Assistant core's Spotify integration
(homeassistant/components/spotify/__init__.py) —
async_get_config_entry_implementation + OAuth2Session +
async_ensure_token_valid, entry.runtime_data instead of the older
hass.data[DOMAIN] dict pattern. See docs/DECISIONS.md for the design
decisions behind this.
"""
from __future__ import annotations

import aiohttp

from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    OAuth2Session,
    async_get_config_entry_implementation,
)

from .api import TibberVehicleApiClient
from .coordinator import TibberVehicleConfigEntry, TibberVehicleCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: TibberVehicleConfigEntry) -> bool:
    """Set up Tibber Vehicle from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady("OAuth2 implementation unavailable") from err

    session = OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    async def _access_token() -> str:
        await session.async_ensure_token_valid()
        return session.token[CONF_ACCESS_TOKEN]

    client = TibberVehicleApiClient(async_get_clientsession(hass), _access_token)

    coordinator = TibberVehicleCoordinator(
        hass,
        entry,
        client,
        home_id=entry.data["home_id"],
        device_id=entry.data["device_id"],
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TibberVehicleConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
