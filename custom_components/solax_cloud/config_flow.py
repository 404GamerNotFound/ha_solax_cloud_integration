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
from .const import CONF_SERIAL_NUMBER, CONF_TOKEN_ID, DOMAIN, LOGGER


def _redact_value(value: str, keep: int = 4) -> str:
    """Return a redacted representation of sensitive values."""

    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"


class SolaxCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Cloud."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        error_message: str | None = None

        if user_input is not None:
            user_input = {
                CONF_TOKEN_ID: user_input[CONF_TOKEN_ID].strip(),
                CONF_SERIAL_NUMBER: user_input[CONF_SERIAL_NUMBER].strip().upper(),
            }

            await self.async_set_unique_id(
                user_input[CONF_SERIAL_NUMBER], raise_on_progress=False
            )
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            request_data = SolaxCloudRequestData(
                token_id=user_input[CONF_TOKEN_ID],
                serial_number=user_input[CONF_SERIAL_NUMBER],
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
                if error_message and error_message.lower() != "unknown error":
                    errors["base"] = "api_error"
                else:
                    error_message = None
                    errors["base"] = "cannot_connect"
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
            }
        )

        description_placeholders = None
        if errors.get("base") == "api_error" and error_message:
            description_placeholders = {"error": error_message}

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_import(self, import_data: dict) -> FlowResult:
        """Handle import from configuration.yaml."""

        return await self.async_step_user(import_data)
