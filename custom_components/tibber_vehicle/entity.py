"""Base entity for Tibber Vehicle.

Groups every vehicle's sensors under their own Home Assistant device — one
device per paired vehicle, since a single Tibber account can have several
(see coordinator.py). Modeled on Spotify's own entity.py
(homeassistant/components/spotify/entity.py) for the pattern itself, but
deliberately does NOT set `entry_type=DeviceEntryType.SERVICE` the way
Spotify's does — that classification is for when the "device" is really a
cloud account, not a physical thing. These are real cars, so they should
appear as regular devices (Settings > Devices & Services > Devices), not
folded into a "service" bucket.
"""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TibberVehicleCoordinator


class TibberVehicleEntity(CoordinatorEntity[TibberVehicleCoordinator]):
    """Base entity for a single vehicle, identified by its Tibber device id."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TibberVehicleCoordinator, device_id: str) -> None:
        """Initialize the entity and its device info."""
        super().__init__(coordinator)
        self._device_id = device_id
        detail = coordinator.data.get(device_id, {})
        info = detail.get("info", {})
        vin = detail.get("externalId") or device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer=info.get("brand"),
            model=info.get("model"),
            name=info.get("name") or vin,
        )

    @property
    def _device_data(self) -> dict:
        """Return this entity's own vehicle's current device detail."""
        return self.coordinator.data.get(self._device_id, {})

    @property
    def available(self) -> bool:
        """Return False once this specific vehicle drops out of the account.

        CoordinatorEntity's default only checks coordinator.last_update_success
        - a whole-coordinator flag - so if one vehicle is removed from the
        Tibber account while others remain, the poll as a whole still
        succeeds and this entity would otherwise stay "available" forever
        with every capability lookup silently returning None (shown as
        "unknown", not the more honest "unavailable"). See
        docs/DECISIONS.md's known limitations for why there's still no live
        removal of the device/entities themselves.
        """
        return super().available and self._device_id in self.coordinator.data
