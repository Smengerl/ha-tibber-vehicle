"""DataUpdateCoordinator for Tibber Vehicle.

Scaffold only. Design decision (docs/DECISIONS.md): non-interactive
refresh-token-only polling of
GET /v1/homes/{homeId}/devices/{deviceId}, mirroring the separation
weconnect_mvp's tibber_client.py already has between the one-time
interactive login and ongoing refresh. HA's OAuth2Session (from
homeassistant.helpers.config_entry_oauth2_flow) should supply the bearer
token here, handling refresh transparently.
"""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import API_BASE, DEFAULT_UPDATE_INTERVAL_SECONDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TibberVehicleCoordinator(DataUpdateCoordinator[dict]):
    """Polls a single Tibber-paired vehicle's device detail."""

    def __init__(self, hass: HomeAssistant, home_id: str, device_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        )
        self._home_id = home_id
        self._device_id = device_id

    async def _async_update_data(self) -> dict:
        # TODO: GET f"{API_BASE}/homes/{self._home_id}/devices/{self._device_id}"
        # via the OAuth2Session-backed aiohttp client, with the mandatory
        # User-Agent header (see docs/CONTEXT.md §3) and exponential
        # backoff-with-jitter on 429/5xx (not on 400/401/403/404 — those
        # mean fix the request, not retry it).
        raise NotImplementedError
