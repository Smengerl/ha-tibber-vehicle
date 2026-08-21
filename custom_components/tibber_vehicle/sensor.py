"""Sensor platform for Tibber Vehicle.

Entity setup modeled on Home Assistant core's Spotify integration —
SensorEntityDescription tuple + typed ConfigEntry.runtime_data instead of
hass.data[DOMAIN]. Five sensors mapping 1:1 to Tibber's complete vehicle
capability set (see docs/DECISIONS.md) — no attempt to backfill data this
API simply doesn't have.
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CAPABILITY_CHARGING_STATUS,
    CAPABILITY_CONNECTOR_STATUS,
    CAPABILITY_RANGE_REMAINING,
    CAPABILITY_STATE_OF_CHARGE,
    CAPABILITY_TARGET_STATE_OF_CHARGE,
)
from .coordinator import TibberVehicleConfigEntry, TibberVehicleCoordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=CAPABILITY_STATE_OF_CHARGE,
        name="State of Charge",
        native_unit_of_measurement="%",
    ),
    SensorEntityDescription(
        key=CAPABILITY_TARGET_STATE_OF_CHARGE,
        name="Target State of Charge",
        native_unit_of_measurement="%",
    ),
    SensorEntityDescription(
        key=CAPABILITY_RANGE_REMAINING,
        name="Range",
        native_unit_of_measurement="km",
    ),
    SensorEntityDescription(
        key=CAPABILITY_CONNECTOR_STATUS,
        name="Plug Status",
    ),
    SensorEntityDescription(
        key=CAPABILITY_CHARGING_STATUS,
        name="Charging Status",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TibberVehicleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tibber Vehicle sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        TibberVehicleSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class TibberVehicleSensor(CoordinatorEntity[TibberVehicleCoordinator], SensorEntity):
    """A single capability of a Tibber-paired vehicle."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TibberVehicleCoordinator,
        entry: TibberVehicleConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def native_value(self) -> str | int | float | None:
        """Return the capability's current value, straight off the coordinator."""
        for capability in self.coordinator.data.get("capabilities", []):
            if capability.get("id") != self.entity_description.key:
                continue
            value = capability.get("value")
            if self.entity_description.key == CAPABILITY_RANGE_REMAINING and isinstance(
                value, (int, float)
            ):
                return round(value / 1000)
            return value
        return None
