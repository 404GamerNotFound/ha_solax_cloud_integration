"""Tests for sensor helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)

from custom_components.solax_cloud.sensor import (
    SENSOR_DESCRIPTIONS,
    _build_device_info,
    _derive_units,
    _iter_dynamic_descriptions,
    _slugify,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("acpower", "ac_power"),
        ("pv1Voltage", "pv1_voltage"),
        ("pv1Current", "pv1_current"),
        ("batteryTemperature", "battery_temperature"),
        ("gridVolt", "grid_volt"),
        ("", ""),
    ),
)
def test_slugify(value: str, expected: str) -> None:
    """Ensure slugification produces readable keys."""

    assert _slugify(value) == expected


@pytest.mark.parametrize(
    ("slug", "value", "expected_device_class", "expected_unit", "expected_state_class"),
    (
        ("ac_power", 1200, SensorDeviceClass.POWER, UnitOfPower.WATT, SensorStateClass.MEASUREMENT),
        (
            "yield_total",
            32.5,
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorStateClass.TOTAL_INCREASING,
        ),
        (
            "pv1_current",
            10.2,
            SensorDeviceClass.CURRENT,
            UnitOfElectricCurrent.AMPERE,
            SensorStateClass.MEASUREMENT,
        ),
        (
            "battery_voltage",
            53.4,
            SensorDeviceClass.VOLTAGE,
            UnitOfElectricPotential.VOLT,
            SensorStateClass.MEASUREMENT,
        ),
        (
            "battery_temperature",
            25.1,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            SensorStateClass.MEASUREMENT,
        ),
        ("battery_soc", 78, SensorDeviceClass.BATTERY, PERCENTAGE, SensorStateClass.MEASUREMENT),
        ("efficiency", "90", None, PERCENTAGE, SensorStateClass.MEASUREMENT),
        ("battery_capacity", 5.8, None, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.MEASUREMENT),
        ("runtime", 12, None, None, SensorStateClass.MEASUREMENT),
        ("status", "Normal", None, None, None),
    ),
)
def test_derive_units(slug, value, expected_device_class, expected_unit, expected_state_class):
    """Validate heuristic unit detection."""

    device_class, unit, state_class = _derive_units(slug, value)
    assert device_class == expected_device_class
    assert unit == expected_unit
    assert state_class == expected_state_class


def test_dynamic_descriptions_create_for_supported_fields():
    """All supported fields should result in sensor descriptions."""

    data = {
        "acpower": 1234,
        "pv1Voltage": "350.4",
        "pv1Current": "8.1",
        "gridpower": 321.1,
        "status": "Normal",
        "soc": 67,
        "batteryTemperature": 29.1,
        "plantName": "My Plant",
    }
    used_slugs = {description.key for description in SENSOR_DESCRIPTIONS}
    used_data_keys = {"acpower", "soc"}

    dynamic = list(_iter_dynamic_descriptions(data, used_slugs, used_data_keys))
    generated_keys = {description.key for description, _ in dynamic}

    assert "pv1_voltage" in generated_keys
    assert "pv1_current" in generated_keys
    assert "grid_power" in generated_keys
    assert "battery_temperature" in generated_keys
    assert "status" in generated_keys
    # ensure we did not re-create already handled static sensors
    assert "ac_power" not in generated_keys


def test_dynamic_description_for_text_field_has_no_state_class():
    """Textual dynamic fields should not set a state class."""

    data = {"status": "Normal"}
    used_slugs = set()
    used_data_keys = set()

    dynamic = list(_iter_dynamic_descriptions(data, used_slugs, used_data_keys))
    assert len(dynamic) == 1
    description, _ = dynamic[0]
    assert description.key == "status"
    assert description.state_class is None


def test_device_info_uses_entry_and_payload_data():
    """Device info should include metadata from config entry and payload."""

    entry = MagicMock(spec=ConfigEntry)
    entry.title = "My inverter"
    data = {"inverterType": "X1", "fwVersion": "1.2.3"}

    device_info = _build_device_info(entry, data, "1234")

    assert device_info.name == "My inverter"
    assert device_info.model == "X1"
    assert device_info.sw_version == "1.2.3"
    assert ("solax_cloud", "1234") in device_info.identifiers
