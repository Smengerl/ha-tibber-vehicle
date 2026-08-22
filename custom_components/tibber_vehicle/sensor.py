"""Sensor platform for Tibber Vehicle.

Entity setup modeled on Home Assistant core's Spotify integration —
SensorEntityDescription tuple + typed ConfigEntry.runtime_data instead of
hass.data[DOMAIN]. All five of Tibber's vehicle capabilities map to
sensors here. Names/icons/units/device_classes/state_classes are matched
1:1 to the equivalent entities in the
robinostlund/homeassistant-volkswagencarnet integration (backed by the
`volkswagencarnet` PyPI package's vw_dashboard.py) so a user switching
between a direct VW connection and this Tibber-backed one sees the same
entity identity, with one deliberate exception: connector.status stays a
plain string sensor rather than VW Connect's binary_sensor
("external_power") — see docs/DECISIONS.md for the full comparison table
and reasoning.
"""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAPABILITY_CHARGING_STATUS,
    CAPABILITY_CONNECTOR_STATUS,
    CAPABILITY_RANGE_REMAINING,
    CAPABILITY_STATE_OF_CHARGE,
    CAPABILITY_TARGET_STATE_OF_CHARGE,
)
from .coordinator import TibberVehicleConfigEntry, TibberVehicleCoordinator
from .entity import TibberVehicleEntity

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Matches volkswagencarnet's "battery_level" sensor.
    SensorEntityDescription(
        key=CAPABILITY_STATE_OF_CHARGE,
        name="Battery level",
        icon="mdi:battery",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Matches volkswagencarnet's "battery_target_charge_level" sensor. No
    # state_class there either — VW models the writable version of this as
    # a separate Number entity, which would be misleading here since
    # Tibber's API is read-only (can't actually change the target).
    SensorEntityDescription(
        key=CAPABILITY_TARGET_STATE_OF_CHARGE,
        name="Battery target charge level",
        icon="mdi:battery-arrow-up",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
    ),
    # Matches volkswagencarnet's "electric_range" sensor (not its separate
    # "battery_cruising_range" — Tibber's range.remaining ["estimated
    # remaining driving range"] maps to the former, not a computed variant).
    SensorEntityDescription(
        key=CAPABILITY_RANGE_REMAINING,
        name="Electric range",
        icon="mdi:car-electric",
        native_unit_of_measurement="km",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Matches volkswagencarnet's "charging_state" sensor — a plain string,
    # no device_class/state_class there either.
    SensorEntityDescription(
        key=CAPABILITY_CHARGING_STATUS,
        name="Charging state",
        icon="mdi:car-turbocharger",
    ),
    # Deliberately NOT matched to VW Connect's "external_power"
    # binary_sensor (see docs/DECISIONS.md) — kept as a plain string
    # sensor so all three of Tibber's actual values (connected/
    # disconnected/unknown) stay directly visible instead of collapsing
    # "unknown" into a generic unavailable state.
    SensorEntityDescription(
        key=CAPABILITY_CONNECTOR_STATUS,
        name="Plug status",
        icon="mdi:ev-plug-type2",
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
        TibberVehicleSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class TibberVehicleSensor(TibberVehicleEntity, SensorEntity):
    """A single capability of a Tibber-paired vehicle."""

    def __init__(
        self,
        coordinator: TibberVehicleCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

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
