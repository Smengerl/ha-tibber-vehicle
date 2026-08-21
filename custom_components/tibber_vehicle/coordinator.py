"""DataUpdateCoordinator for Tibber Vehicle.

Polling shape modeled on Home Assistant core's Spotify integration
(SpotifyCoordinator in homeassistant/components/spotify/coordinator.py) —
a typed `ConfigEntry[TibberVehicleCoordinator]` via `entry.runtime_data`
instead of the older `hass.data[DOMAIN][entry_id]` dict pattern. The
coordinator only ever reads an already-valid token through the API
client's `access_token_provider` callback wired up in `__init__.py` — see
docs/DECISIONS.md for why token refresh itself is entirely
`OAuth2Session`'s job, not something this class does.
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


class TibberVehicleCoordinator(DataUpdateCoordinator[dict]):
    """Polls a single Tibber-paired vehicle's device detail."""

    config_entry: TibberVehicleConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: TibberVehicleConfigEntry,
        client: TibberVehicleApiClient,
        home_id: str,
        device_id: str,
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
        self._home_id = home_id
        self._device_id = device_id

    async def _async_update_data(self) -> dict:
        try:
            return await self._client.async_get_device(self._home_id, self._device_id)
        except TibberVehicleApiError as err:
            raise UpdateFailed(f"Error communicating with Tibber API: {err}") from err
