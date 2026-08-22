"""Binary sensor platform for Tibber Vehicle.

Tibber's connector.status capability maps to
robinostlund/homeassistant-volkswagencarnet's "external_power" binary
sensor (device_class POWER) — not a plain string sensor — so this
integration matches that entity type here too, not just the name/icon.
See docs/DECISIONS.md for the full VW Connect entity comparison.
"""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CAPABILITY_CONNECTOR_STATUS
from .coordinator import TibberVehicleConfigEntry, TibberVehicleCoordinator
from .entity import TibberVehicleEntity

# Matches volkswagencarnet's "external_power" binary sensor.
ENTITY_DESCRIPTION = BinarySensorEntityDescription(
    key=CAPABILITY_CONNECTOR_STATUS,
    name="External power",
    device_class=BinarySensorDeviceClass.POWER,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TibberVehicleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tibber Vehicle binary sensor from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([TibberVehicleBinarySensor(coordinator)])


class TibberVehicleBinarySensor(TibberVehicleEntity, BinarySensorEntity):
    """Whether the vehicle is currently plugged into external power."""

    entity_description = ENTITY_DESCRIPTION

    def __init__(self, coordinator: TibberVehicleCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}_{CAPABILITY_CONNECTOR_STATUS}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if connected, False if disconnected, None if unknown."""
        for capability in self.coordinator.data.get("capabilities", []):
            if capability.get("id") != CAPABILITY_CONNECTOR_STATUS:
                continue
            value = capability.get("value")
            if value == "connected":
                return True
            if value == "disconnected":
                return False
            return None
        return None
