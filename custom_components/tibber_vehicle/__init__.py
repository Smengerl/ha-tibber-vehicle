"""The Tibber Vehicle integration.

Scaffold only — see docs/CONTEXT.md and docs/DECISIONS.md in the repo root
before implementing setup_entry for real. Not yet functional: this module
intentionally does not implement OAuth2 session creation or coordinator
wiring yet.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tibber Vehicle from a config entry."""
    # TODO: create an OAuth2Session from the config entry's Application
    # Credential + stored token (see homeassistant.helpers.config_entry_oauth2_flow),
    # instantiate the coordinator, store it in hass.data[DOMAIN][entry.entry_id],
    # then forward to PLATFORMS. Left unimplemented until config_flow.py and
    # coordinator.py are built out — see docs/DECISIONS.md.
    raise NotImplementedError("tibber_vehicle setup is not implemented yet")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
