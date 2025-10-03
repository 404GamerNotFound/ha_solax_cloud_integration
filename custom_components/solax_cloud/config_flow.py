"""Config flow for the SolaX Cloud integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
    DOMAIN,
    LOGGER,
)


def _redact_value(value: str, keep: int = 4) -> str:
    """Return a redacted representation of sensitive values."""

    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"


def _classify_api_error(message: str) -> tuple[str, dict[str, str] | None]:
    """Translate API error messages into config flow errors and placeholders."""

    normalized = message.casefold().strip()
    if not normalized or "unknown error" in normalized:
        return "cannot_connect", None
    return "api_error", {"error": message}


def _normalize_credentials(
    token_id: str, serial_number: str, api_base_url: str | None = None
) -> tuple[dict, str]:
    """Normalise user supplied credentials for storage and uniqueness checks."""

    cleaned_data = {
        CONF_TOKEN_ID: token_id.strip(),
        CONF_SERIAL_NUMBER: serial_number.strip(),
    }

    if api_base_url is not None:
        value = api_base_url.strip()
        cleaned_data[CONF_API_BASE_URL] = value or None

    # SolaX serial numbers are usually printed in upper-case, but the API treats
    # them as case-sensitive. We therefore keep the original casing for storage
    # while still normalising the unique ID to avoid creating duplicate entries
    # for the same device when users enter the serial in a different case.
    unique_id = cleaned_data[CONF_SERIAL_NUMBER].upper()

    return cleaned_data, unique_id


class SolaxCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Cloud."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] | None = None

        if user_input is not None:
            user_input, unique_id = _normalize_credentials(
                user_input[CONF_TOKEN_ID],
                user_input[CONF_SERIAL_NUMBER],
                user_input.get(CONF_API_BASE_URL),
            )

            await self.async_set_unique_id(unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            request_data = SolaxCloudRequestData(
                token_id=user_input[CONF_TOKEN_ID],
                serial_number=user_input[CONF_SERIAL_NUMBER],
                api_base_url=user_input.get(CONF_API_BASE_URL),
            )
            api = SolaxCloudApiClient(session, request_data)
            log_context = {
                "serial_number": _redact_value(request_data.serial_number),
                "token_id": _redact_value(request_data.token_id),
            }

            try:
                result = await api.async_get_data()
            except SolaxCloudAuthenticationError as err:
                LOGGER.error(
                    "Authentication with the SolaX Cloud API failed during config flow",
                    extra=log_context,
                    exc_info=err,
                )
                errors["base"] = "invalid_auth"
            except SolaxCloudApiError as err:
                error_message = str(err).strip()
                LOGGER.error(
                    "SolaX Cloud API error during config flow: %s",
                    error_message or "unknown",
                    extra=log_context,
                    exc_info=err,
                )
                errors["base"], description_placeholders = _classify_api_error(
                    error_message
                )
            else:
                # Store some metadata for device info purposes
                return self.async_create_entry(
                    title=result.get("inverterSN") or user_input[CONF_SERIAL_NUMBER],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN_ID): str,
                vol.Required(CONF_SERIAL_NUMBER): str,
                vol.Required(CONF_API_BASE_URL, default="https://global.solaxcloud.com"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_import(self, import_data: dict) -> FlowResult:
        """Handle import from configuration.yaml."""

        return await self.async_step_user(import_data)
