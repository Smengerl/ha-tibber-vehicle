"""Tests for Tibber Vehicle's sensor platform.

See docs/TESTING.md for the full test concept and case list.
"""
from __future__ import annotations

import json
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.tibber_vehicle.const import DOMAIN

HOMES_URL = "https://data-api.tibber.com/v1/homes"
DEVICES_URL = f"{HOMES_URL}/home-1/devices"
DEVICE_1_DETAIL_URL = f"{HOMES_URL}/home-1/devices/ZGV2aWNlLTE"
DEVICE_2_DETAIL_URL = f"{HOMES_URL}/home-1/devices/ZGV2aWNlLTI"


def _mock_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="ID.7",
        unique_id="home-1",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": time.time() + 3600,
            },
        },
    )


async def _setup_one_vehicle(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, detail: dict | None = None
) -> MockConfigEntry:
    entry = _mock_entry()
    entry.add_to_hass(hass)
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_one_vehicle.json"))
    aioclient_mock.get(
        DEVICE_1_DETAIL_URL, json=detail or json.loads(load_fixture("device_detail.json"))
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_sensors_created_per_vehicle(
    hass: HomeAssistant, setup_credentials: None, aioclient_mock: AiohttpClientMocker
) -> None:
    """Two vehicles -> 10 entities (5 each), grouped under 2 distinct devices."""
    entry = _mock_entry()
    entry.add_to_hass(hass)
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_two_vehicles.json"))

    detail_1 = json.loads(load_fixture("device_detail.json"))
    aioclient_mock.get(DEVICE_1_DETAIL_URL, json=detail_1)
    detail_2 = {
        **detail_1,
        "id": "ZGV2aWNlLTI",
        "externalId": "WVWZZZAAZLD000002",
        "info": {"name": "ID.4", "brand": "Volkswagen", "model": "ID.4"},
    }
    aioclient_mock.get(DEVICE_2_DETAIL_URL, json=detail_2)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    our_entities = [e for e in entity_registry.entities.values() if e.platform == DOMAIN]
    assert len(our_entities) == 10
    assert len({e.unique_id for e in our_entities}) == 10  # all unique

    device_registry = dr.async_get(hass)
    our_devices = [
        d for d in device_registry.devices.values()
        if any(identifier[0] == DOMAIN for identifier in d.identifiers)
    ]
    assert len(our_devices) == 2


async def test_sensor_native_value_mapping(
    hass: HomeAssistant, setup_credentials: None, aioclient_mock: AiohttpClientMocker
) -> None:
    """Each of the 5 capability ids maps to its sensor's state, range converted m->km."""
    await _setup_one_vehicle(hass, aioclient_mock)

    assert hass.states.get("sensor.id_7_battery_level").state == "74"
    assert hass.states.get("sensor.id_7_battery_target_charge_level").state == "80"
    assert hass.states.get("sensor.id_7_electric_range").state == "356"
    assert hass.states.get("sensor.id_7_plug_status").state == "disconnected"
    assert hass.states.get("sensor.id_7_charging_state").state == "idle"


async def test_sensor_missing_capability_returns_none(
    hass: HomeAssistant, setup_credentials: None, aioclient_mock: AiohttpClientMocker
) -> None:
    """A capability Tibber doesn't report for this vehicle -> unknown state, not a crash."""
    detail = json.loads(load_fixture("device_detail.json"))
    detail["capabilities"] = [
        c for c in detail["capabilities"] if c["id"] != "charging.status"
    ]
    await _setup_one_vehicle(hass, aioclient_mock, detail=detail)

    state = hass.states.get("sensor.id_7_charging_state")
    assert state is not None
    assert state.state == "unknown"


async def test_device_info_manufacturer_omitted_when_brand_missing(
    hass: HomeAssistant, setup_credentials: None, aioclient_mock: AiohttpClientMocker
) -> None:
    """Regression test for the hardcoded-"Volkswagen"-fallback bug fixed 2026-08-24."""
    detail = json.loads(load_fixture("device_detail.json"))
    detail["info"] = {"name": "ID.7", "model": "ID.7"}  # no "brand" key at all
    await _setup_one_vehicle(hass, aioclient_mock, detail=detail)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "WVWZZZAAZLD000001")}
    )
    assert device is not None
    assert device.manufacturer is None


async def test_entity_unavailable_when_vehicle_removed(
    hass: HomeAssistant, setup_credentials: None, aioclient_mock: AiohttpClientMocker
) -> None:
    """A vehicle dropping out of the account on a later poll -> unavailable, not "unknown".

    Regression test for the review finding that CoordinatorEntity's
    default `available` only checks the whole coordinator's
    last_update_success, not whether this specific device_id is still
    present - a poll that still succeeds overall (other vehicles remain)
    would otherwise leave a removed vehicle's entities silently reporting
    "unknown" forever.
    """
    entry = await _setup_one_vehicle(hass, aioclient_mock)
    assert hass.states.get("sensor.id_7_battery_level").state == "74"

    aioclient_mock.clear_requests()
    aioclient_mock.get(HOMES_URL, json={"homes": [{"id": "home-1"}]})
    aioclient_mock.get(DEVICES_URL, text=load_fixture("devices_empty.json"))

    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.id_7_battery_level").state == "unavailable"
