"""Config flow for Tibber Vehicle.

OAuth2 login flow, structured after Home Assistant core's Spotify
integration (homeassistant/components/spotify/config_flow.py) — same
AbstractOAuth2FlowHandler + extra_authorize_data + async_oauth_create_entry
shape, adapted to confirm the Tibber account has at least one vehicle
instead of resolving a user profile. See docs/DECISIONS.md for why HA's
built-in OAuth2 helper was chosen over a custom loopback-server approach,
and for where the resulting token ends up stored (the config entry
itself, not a file this integration manages).

One config entry = one Tibber account; every vehicle paired to that
account becomes its own device (see coordinator.py/sensor.py) — there is
deliberately no vehicle-picker step here, since the point is to expose
everything the account already has, not make the user choose a subset.

Deliberately out of scope for now (see docs/DECISIONS.md's known
limitations): reauth flow, and picking up a vehicle paired *after* setup
without reloading the integration. Neither blocks a working login.
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
        """Create an entry, after confirming this Tibber account has a vehicle."""
        access_token = data[CONF_TOKEN][CONF_ACCESS_TOKEN]

        async def _static_token() -> str:
            # Only used for these one-shot resolution calls, before the
            # config entry (and with it, OAuth2Session-backed refresh)
            # exists yet.
            return access_token

        client = TibberVehicleApiClient(
            async_get_clientsession(self.hass), _static_token
        )

        try:
            homes = await client.async_get_homes()
            vehicles = await client.async_get_all_vehicles()
        except TibberVehicleApiError:
            self.logger.exception("Error while resolving paired Tibber vehicles")
            return self.async_abort(reason="connection_error")

        if not vehicles:
            return self.async_abort(reason="no_vehicle_found")

        # Homes are a reasonably stable stand-in for "this Tibber account" —
        # there's no dedicated account/user-id endpoint in scope here (see
        # docs/DECISIONS.md). This only blocks linking the *same* account
        # twice; it has no bearing on how many vehicles that account has.
        await self.async_set_unique_id("|".join(sorted(home["id"] for home in homes)))
        self._abort_if_unique_id_configured()

        names = [
            device.get("info", {}).get("name") or device.get("externalId") or device["id"]
            for _, device in vehicles
        ]
        title = ", ".join(names) if len(names) <= 3 else f"{len(names)} vehicles"

        return self.async_create_entry(title=title, data=data)
