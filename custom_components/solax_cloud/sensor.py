"""Sensor platform for the SolaX Cloud integration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_NUMBER, DOMAIN


DEVICE_METADATA_KEYS = {
    "plantname",
    "plant_name",
    "plantid",
    "plant_id",
    "timezone",
    "time_zone",
    "invertertype",
    "inverter_type",
    "type",
    "fwversion",
    "fw_version",
    "firmware",
    "serialnumber",
    "serial_number",
}


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
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("soc", "batterySoc"),
    ),
    SolaxCloudSensorEntityDescription(
        key="ac_frequency",
        translation_key="ac_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        api_keys=("acfre", "acFre", "acFrequency"),
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


_SLUG_RE = re.compile(r"[^0-9a-z]+")


def _slugify(value: str) -> str:
    """Return a slugified version of an API key."""

    if not value:
        return ""

    camel_to_snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    camel_to_snake = re.sub(r"([A-Za-z])(\d)", r"\1_\2", camel_to_snake)
    camel_to_snake = re.sub(r"(\d)([A-Za-z])", r"\1_\2", camel_to_snake)
    for token in ("power", "energy", "voltage", "current", "temperature", "frequency", "capacity"):
        camel_to_snake = re.sub(
            rf"(?i)(?<=[a-z0-9])({token})",
            lambda match: f"_{match.group(1).lower()}",
            camel_to_snake,
        )
    slug = _SLUG_RE.sub("_", camel_to_snake.lower()).strip("_")
    return slug


def _title_from_slug(slug: str) -> str:
    """Return a human readable name from a slug."""

    return slug.replace("_", " ").replace("  ", " ").strip().title()


def _is_numeric(value: Any) -> bool:
    """Return True if the value can be interpreted as a number."""

    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return False
        try:
            float(value)
        except ValueError:
            return False
        return True
    return False


def _expand_key_variants(key: str) -> tuple[str, ...]:
    """Return a set of likely API key variations."""

    if not key:
        return tuple()
    slug = _slugify(key)
    if not slug:
        return (key,)
    parts = slug.split("_")
    camel = parts[0] + "".join(word.capitalize() for word in parts[1:])
    pascal = "".join(word.capitalize() for word in parts)
    variants = {key, slug.replace("_", ""), slug, camel, pascal, key.lower()}
    return tuple(variant for variant in variants if variant)


def _resolve_data_key(data: dict[str, Any], candidates: Iterable[str]) -> str | None:
    """Resolve the actual key from the API data for the provided candidates."""

    if not candidates:
        return None

    lowercase_map = {existing_key.lower(): existing_key for existing_key in data}
    for candidate in candidates:
        if candidate in data:
            return candidate
        candidate_lower = candidate.lower()
        if candidate_lower in lowercase_map:
            return lowercase_map[candidate_lower]
    return None


def _derive_units(
    key: str, value: Any
) -> tuple[SensorDeviceClass | None, str | None, SensorStateClass | None]:
    """Derive sensible defaults for units and device classes based on the key."""

    if not _is_numeric(value):
        return (None, None, None)

    lowered = key.lower()
    if any(token in lowered for token in ("yield", "energy", "generation")):
        return (
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorStateClass.TOTAL_INCREASING,
        )
    if "power" in lowered:
        return (
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
        )
    if "current" in lowered or lowered.endswith("_a"):
        return (
            SensorDeviceClass.CURRENT,
            UnitOfElectricCurrent.AMPERE,
            SensorStateClass.MEASUREMENT,
        )
    if "voltage" in lowered or lowered.endswith("_v") or "_volt" in lowered:
        return (
            SensorDeviceClass.VOLTAGE,
            UnitOfElectricPotential.VOLT,
            SensorStateClass.MEASUREMENT,
        )
    if any(token in lowered for token in ("temperature", "temp")):
        return (
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            SensorStateClass.MEASUREMENT,
        )
    if any(token in lowered for token in ("frequency", "freq", "hz")):
        return (
            SensorDeviceClass.FREQUENCY,
            "Hz",
            SensorStateClass.MEASUREMENT,
        )
    if "soc" in lowered or "soh" in lowered or "percent" in lowered:
        return (SensorDeviceClass.BATTERY, PERCENTAGE, SensorStateClass.MEASUREMENT)
    if "efficiency" in lowered:
        return (None, PERCENTAGE, SensorStateClass.MEASUREMENT)
    if "capacity" in lowered:
        return (None, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.MEASUREMENT)
    return (None, None, SensorStateClass.MEASUREMENT)


def _build_device_info(entry: ConfigEntry, data: dict[str, Any], serial_number: str) -> DeviceInfo:
    """Return the device information for the integration."""

    suggested_name = entry.title or data.get("plantname") or data.get("plantName")
    if not suggested_name:
        suggested_name = "SolaX Inverter"

    model = data.get("invertertype") or data.get("inverterType") or data.get("type")
    sw_version = data.get("fwversion") or data.get("firmware") or data.get("fwVersion")

    return DeviceInfo(
        identifiers={(DOMAIN, serial_number)},
        manufacturer="SolaX",
        name=suggested_name,
        model=model,
        sw_version=sw_version,
    )


def _iter_dynamic_descriptions(
    data: dict[str, Any],
    existing_slugs: set[str],
    used_data_keys: set[str],
) -> Iterable[tuple[SolaxCloudSensorEntityDescription, str]]:
    """Yield entity descriptions for all supported API fields."""

    seen_slugs = set(existing_slugs)

    for raw_key, value in data.items():
        if raw_key is None:
            continue

        lower_key = raw_key.lower()

        if lower_key in used_data_keys or lower_key in DEVICE_METADATA_KEYS:
            continue

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        slug = _slugify(raw_key)
        if not slug or slug in seen_slugs:
            # Avoid duplicates or invalid slugs
            if slug in seen_slugs:
                base_slug = slug
                counter = 2
                while f"{base_slug}_{counter}" in seen_slugs:
                    counter += 1
                slug = f"{base_slug}_{counter}"
            else:
                continue

        seen_slugs.add(slug)

        name = _title_from_slug(slug)
        device_class, unit, state_class = _derive_units(slug, value)
        description = SolaxCloudSensorEntityDescription(
            key=slug,
            name=name,
            device_class=device_class,
            native_unit_of_measurement=unit,
            state_class=state_class,
            api_keys=_expand_key_variants(raw_key),
        )
        yield description, raw_key


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up SolaX Cloud sensors based on a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial_number: str = entry.data[CONF_SERIAL_NUMBER]
    device_info = _build_device_info(entry, coordinator.data, serial_number)

    entities: list[SolaxCloudSensor] = []
    used_slugs: set[str] = set()
    used_data_keys: set[str] = set()

    for description in SENSOR_DESCRIPTIONS:
        data_key = _resolve_data_key(coordinator.data, description.api_keys)
        if not data_key:
            continue
        used_slugs.add(description.key)
        used_data_keys.add(data_key.lower())
        entities.append(
            SolaxCloudSensor(
                coordinator,
                entry,
                description,
                data_key,
                device_info,
            )
        )

    for description, raw_key in _iter_dynamic_descriptions(
        coordinator.data, used_slugs, used_data_keys
    ):
        data_key = _resolve_data_key(coordinator.data, description.api_keys)
        if not data_key:
            continue
        used_data_keys.add(data_key.lower())
        entities.append(
            SolaxCloudSensor(
                coordinator,
                entry,
                description,
                data_key,
                device_info,
            )
        )

    async_add_entities(entities)


class SolaxCloudSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SolaX Cloud sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: SolaxCloudSensorEntityDescription,
        data_key: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}-{description.key}"
        self._attr_device_info = device_info
        self._data_key = data_key

    @property
    def native_value(self):
        """Return the state of the sensor."""

        value = self.coordinator.data.get(self._data_key)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        return value
