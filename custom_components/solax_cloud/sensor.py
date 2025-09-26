"""Sensor platform for the SolaX Cloud integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_NUMBER, DOMAIN


@dataclass(frozen=True)
class SolaxCloudSensorEntityDescription(SensorEntityDescription):
    """Describes SolaX Cloud sensor entity."""

    api_keys: tuple[str, ...]


SENSOR_DESCRIPTIONS: tuple[SolaxCloudSensorEntityDescription, ...] = (
    SolaxCloudSensorEntityDescription(
        key="ac_power",
        translation_key="ac_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("acpower", "acPower"),
    ),
    SolaxCloudSensorEntityDescription(
        key="yield_today",
        translation_key="yield_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        api_keys=("yieldtoday", "yieldToday"),
    ),
    SolaxCloudSensorEntityDescription(
        key="yield_total",
        translation_key="yield_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        api_keys=("yieldtotal", "yieldTotal"),
    ),
    SolaxCloudSensorEntityDescription(
        key="feed_in_power",
        translation_key="feed_in_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("feedinpower", "feedInPower"),
    ),
    SolaxCloudSensorEntityDescription(
        key="feed_in_energy",
        translation_key="feed_in_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        api_keys=("feedinenergy", "feedInEnergy"),
    ),
    SolaxCloudSensorEntityDescription(
        key="consume_energy",
        translation_key="consume_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        api_keys=("consumeenergy", "consumeEnergy"),
    ),
    SolaxCloudSensorEntityDescription(
        key="consume_energy_today",
        translation_key="consume_energy_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        api_keys=("consumeenergy_today", "consumeEnergyToday"),
    ),
    SolaxCloudSensorEntityDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("bat_power", "batPower", "battery_power"),
    ),
    SolaxCloudSensorEntityDescription(
        key="soc",
        translation_key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("soc", "batterySoc"),
    ),
    SolaxCloudSensorEntityDescription(
        key="ac_frequency",
        translation_key="ac_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("acfre", "acFre"),
    ),
    SolaxCloudSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("tempperature", "temperature"),
    ),
)
async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up SolaX Cloud sensors based on a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial_number: str = entry.data[CONF_SERIAL_NUMBER]

    async_add_entities(
        SolaxCloudSensor(coordinator, entry, description, serial_number)
        for description in SENSOR_DESCRIPTIONS
        if any(key in coordinator.data for key in description.api_keys)
    )


class SolaxCloudSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SolaX Cloud sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: SolaxCloudSensorEntityDescription,
        serial_number: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            name="SolaX Inverter",
            manufacturer="SolaX",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""

        value = None
        for key in self.entity_description.api_keys:
            if key in self.coordinator.data:
                value = self.coordinator.data[key]
                break
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        return value
