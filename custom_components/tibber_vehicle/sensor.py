"""Sensor platform for Tibber Vehicle.

Entity setup modeled on Home Assistant core's Spotify integration —
SensorEntityDescription tuple + typed ConfigEntry.runtime_data instead of
hass.data[DOMAIN]. All five of Tibber's vehicle capabilities map to
sensors here, once per vehicle paired with the account (see
coordinator.py). Names/icons/units/device_classes/state_classes are
matched 1:1 to the equivalent entities in the
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

# Entities are populated entirely from data the coordinator already fetched
# on its own schedule — no per-entity I/O to throttle.
PARALLEL_UPDATES = 0

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Matches volkswagencarnet's "battery_level" sensor. translation_key
    # (not a literal `name`) so the displayed name follows the user's HA
    # language - see translations/*.json for the actual strings; the key
    # itself doubles as the stable English entity_id slug regardless of
    # active language.
    SensorEntityDescription(
        key=CAPABILITY_STATE_OF_CHARGE,
        translation_key="battery_level",
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
        translation_key="battery_target_charge_level",
        icon="mdi:battery-arrow-up",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
    ),
    # Matches volkswagencarnet's "electric_range" sensor (not its separate
    # "battery_cruising_range" — Tibber's range.remaining ["estimated
    # remaining driving range"] maps to the former, not a computed variant).
    SensorEntityDescription(
        key=CAPABILITY_RANGE_REMAINING,
        translation_key="electric_range",
        icon="mdi:car-electric",
        native_unit_of_measurement="km",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Matches volkswagencarnet's "charging_state" sensor — a plain string,
    # no device_class/state_class there either.
    SensorEntityDescription(
        key=CAPABILITY_CHARGING_STATUS,
        translation_key="charging_state",
        icon="mdi:car-turbocharger",
    ),
    # Deliberately NOT matched to VW Connect's "external_power"
    # binary_sensor (see docs/DECISIONS.md) — kept as a plain string
    # sensor so all three of Tibber's actual values (connected/
    # disconnected/unknown) stay directly visible instead of collapsing
    # "unknown" into a generic unavailable state.
    SensorEntityDescription(
        key=CAPABILITY_CONNECTOR_STATUS,
        translation_key="plug_status",
        icon="mdi:ev-plug-type2",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TibberVehicleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tibber Vehicle sensors — one set of 5 per paired vehicle."""
    coordinator = entry.runtime_data
    async_add_entities(
        TibberVehicleSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSOR_DESCRIPTIONS
    )


class TibberVehicleSensor(TibberVehicleEntity, SensorEntity):
    """A single capability of one Tibber-paired vehicle."""

    def __init__(
        self,
        coordinator: TibberVehicleCoordinator,
        device_id: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def native_value(self) -> str | int | float | None:
        """Return the capability's current value, straight off the coordinator."""
        for capability in self._device_data.get("capabilities", []):
            if capability.get("id") != self.entity_description.key:
                continue
            value = capability.get("value")
            if self.entity_description.key == CAPABILITY_RANGE_REMAINING and isinstance(
                value, (int, float)
            ):
                return round(value / 1000)
            return value
        return None
