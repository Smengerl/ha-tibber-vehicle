"""Config flow for Tibber Vehicle.

OAuth2 login flow, structured after Home Assistant core's Spotify
integration (homeassistant/components/spotify/config_flow.py) — same
AbstractOAuth2FlowHandler + extra_authorize_data + async_oauth_create_entry
shape, adapted to resolve a paired vehicle instead of a user profile. See
docs/DECISIONS.md for why HA's built-in OAuth2 helper was chosen over
weconnect_mvp's tibber_client.py loopback-server approach, and for where
the resulting token ends up stored (the config entry itself, not a file
this integration manages).

Deliberately out of scope for now (see docs/DECISIONS.md's known
limitations): reauth flow and multi-vehicle support. Neither blocks a
working single-vehicle login — both are natural, additive follow-ups.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TibberVehicleApiClient, TibberVehicleApiError
from .const import DOMAIN, OAUTH2_SCOPES

_LOGGER = logging.getLogger(__name__)


class TibberVehicleOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow for Tibber Vehicle, driven by HA's OAuth2 helper."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": " ".join(OAUTH2_SCOPES)}

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry, after resolving which vehicle this token can see."""
        access_token = data[CONF_TOKEN][CONF_ACCESS_TOKEN]

        async def _static_token() -> str:
            # Only used for this one-shot resolution call, before the config
            # entry (and with it, OAuth2Session-backed refresh) exists yet.
            return access_token

        client = TibberVehicleApiClient(
            async_get_clientsession(self.hass), _static_token
        )

        try:
            found = await client.async_find_first_vehicle()
        except TibberVehicleApiError:
            self.logger.exception("Error while resolving paired Tibber vehicle")
            return self.async_abort(reason="connection_error")

        if found is None:
            return self.async_abort(reason="no_vehicle_found")

        home_id, device = found
        vin = device.get("externalId") or device["id"]
        name = device.get("info", {}).get("name") or "Tibber Vehicle"

        await self.async_set_unique_id(vin)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=name,
            data={**data, "home_id": home_id, "device_id": device["id"], "vin": vin},
        )
