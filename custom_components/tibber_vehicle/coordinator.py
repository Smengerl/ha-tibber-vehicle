"""DataUpdateCoordinator for Tibber Vehicle.

Polling shape modeled on Home Assistant core's Spotify integration
(SpotifyCoordinator in homeassistant/components/spotify/coordinator.py) —
a typed `ConfigEntry[TibberVehicleCoordinator]` via `entry.runtime_data`
instead of the older `hass.data[DOMAIN][entry_id]` dict pattern. The
coordinator only ever reads an already-valid token through the API
client's `access_token_provider` callback wired up in `__init__.py` — see
docs/DECISIONS.md for why token refresh itself is entirely
`OAuth2Session`'s job, not something this class does.

Polls *every* vehicle paired with the account on each cycle (re-listed via
`async_get_all_vehicles` every time, not cached from config-flow time) and
keyed by device id, so `sensor.py` can create one set of entities per
vehicle. New vehicles paired in Tibber after setup are picked up on the
next integration reload — there's no live add/remove of devices between
reloads (see docs/DECISIONS.md's known limitations).
"""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TibberVehicleApiClient, TibberVehicleApiError
from .const import DEFAULT_UPDATE_INTERVAL_SECONDS, DOMAIN

_LOGGER = logging.getLogger(__name__)

type TibberVehicleConfigEntry = ConfigEntry[TibberVehicleCoordinator]


class TibberVehicleCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Polls device detail for every vehicle paired with this Tibber account."""

    config_entry: TibberVehicleConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: TibberVehicleConfigEntry,
        client: TibberVehicleApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            vehicles = await self._client.async_get_all_vehicles()
            return {
                device["id"]: await self._client.async_get_device(home_id, device["id"])
                for home_id, device in vehicles
            }
        except TibberVehicleApiError as err:
            raise UpdateFailed(f"Error communicating with Tibber API: {err}") from err
