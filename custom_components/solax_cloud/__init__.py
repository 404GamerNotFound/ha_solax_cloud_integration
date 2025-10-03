"""The SolaX Cloud integration."""

from __future__ import annotations

from datetime import timedelta

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SolaxCloudApiClient,
    SolaxCloudApiError,
    SolaxCloudAuthenticationError,
    SolaxCloudRequestData,
)
from .const import (
    CONF_API_BASE_URL,
    CONF_SERIAL_NUMBER,
    CONF_TOKEN_ID,
    COORDINATOR_UPDATE_INTERVAL,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)


def _redact_value(value: str, keep: int = 4) -> str:
    """Return a redacted representation of sensitive values."""

    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up SolaX Cloud via YAML (not supported)."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolaX Cloud from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    session: ClientSession = async_get_clientsession(hass)
    request_data = SolaxCloudRequestData(
        token_id=entry.data[CONF_TOKEN_ID],
        serial_number=entry.data[CONF_SERIAL_NUMBER],
        api_base_url=entry.data.get(CONF_API_BASE_URL),
    )
    api = SolaxCloudApiClient(session, request_data)

    log_context = {
        "entry_id": entry.entry_id,
        "serial_number": _redact_value(request_data.serial_number),
    }

    async def async_update_data() -> dict:
        try:
            return await api.async_get_data()
        except SolaxCloudAuthenticationError as err:
            LOGGER.error(
                "Authentication failed while updating SolaX Cloud data",
                extra=log_context,
                exc_info=err,
            )
            raise UpdateFailed("Authentication failed while updating SolaX Cloud data") from err
        except SolaxCloudApiError as err:
            LOGGER.error(
                "Failed to update SolaX Cloud data: %s",
                err,
                extra=log_context,
                exc_info=err,
            )
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name="solax_cloud",
        update_method=async_update_data,
        update_interval=timedelta(seconds=COORDINATOR_UPDATE_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
