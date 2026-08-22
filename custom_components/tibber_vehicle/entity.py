"""Base entity for Tibber Vehicle.

Groups every sensor under one Home Assistant device representing the
physical vehicle. Modeled on Spotify's own entity.py
(homeassistant/components/spotify/entity.py) for the pattern itself, but
deliberately does NOT set `entry_type=DeviceEntryType.SERVICE` the way
Spotify's does — that classification is for when the "device" is really a
cloud account, not a physical thing. This one is a real car, so it should
appear as a regular device (Settings > Devices & Services > Devices), not
folded into a "service" bucket.
"""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TibberVehicleCoordinator


class TibberVehicleEntity(CoordinatorEntity[TibberVehicleCoordinator]):
    """Base entity, grouped under one device per paired vehicle."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TibberVehicleCoordinator) -> None:
        """Initialize the entity and its device info."""
        super().__init__(coordinator)
        info = coordinator.data.get("info", {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
            manufacturer=info.get("brand"),
            model=info.get("model"),
            name=info.get("name") or coordinator.config_entry.title,
        )
