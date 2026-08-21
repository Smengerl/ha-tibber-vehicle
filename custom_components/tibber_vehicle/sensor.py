"""Sensor platform for Tibber Vehicle.

Scaffold only. Design decision (docs/DECISIONS.md): five sensors mapping
1:1 to the complete Tibber vehicle capability set — no attempt to backfill
data (doors, climate, position, lock) that this API simply doesn't have.
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CAPABILITY_CHARGING_STATUS,
    CAPABILITY_CONNECTOR_STATUS,
    CAPABILITY_RANGE_REMAINING,
    CAPABILITY_STATE_OF_CHARGE,
    CAPABILITY_TARGET_STATE_OF_CHARGE,
    DOMAIN,
)
from .coordinator import TibberVehicleCoordinator

SENSOR_DESCRIPTIONS: dict[str, str] = {
    CAPABILITY_STATE_OF_CHARGE: "State of Charge",
    CAPABILITY_TARGET_STATE_OF_CHARGE: "Target State of Charge",
    CAPABILITY_RANGE_REMAINING: "Range",
    CAPABILITY_CONNECTOR_STATUS: "Plug Status",
    CAPABILITY_CHARGING_STATUS: "Charging Status",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Tibber Vehicle sensors from a config entry."""
    # TODO: fetch the coordinator from hass.data[DOMAIN][entry.entry_id]
    # (set up in __init__.py) once that's implemented, then:
    # coordinator = hass.data[DOMAIN][entry.entry_id]
    # async_add_entities(
    #     TibberVehicleSensor(coordinator, capability_id, name)
    #     for capability_id, name in SENSOR_DESCRIPTIONS.items()
    # )
    raise NotImplementedError


class TibberVehicleSensor(CoordinatorEntity[TibberVehicleCoordinator], SensorEntity):
    """A single capability of a Tibber-paired vehicle."""

    def __init__(
        self, coordinator: TibberVehicleCoordinator, capability_id: str, name: str
    ) -> None:
        super().__init__(coordinator)
        self._capability_id = capability_id
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{capability_id}"

    @property
    def native_value(self):
        # TODO: look up self._capability_id in
        # self.coordinator.data["capabilities"] (list of
        # {"id", "value", ...} dicts — see docs/CONTEXT.md §3 for the
        # response shape) and convert range.remaining from meters to km.
        raise NotImplementedError
