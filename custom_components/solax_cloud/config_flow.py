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
from .const import CONF_SERIAL_NUMBER, CONF_TOKEN_ID, DOMAIN


class SolaxCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Cloud."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = {
                CONF_TOKEN_ID: user_input[CONF_TOKEN_ID].strip(),
                CONF_SERIAL_NUMBER: user_input[CONF_SERIAL_NUMBER].strip().upper(),
            }

            await self.async_set_unique_id(user_input[CONF_SERIAL_NUMBER])
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            request_data = SolaxCloudRequestData(
                token_id=user_input[CONF_TOKEN_ID],
                serial_number=user_input[CONF_SERIAL_NUMBER],
            )
            api = SolaxCloudApiClient(session, request_data)

            try:
                result = await api.async_get_data()
            except SolaxCloudAuthenticationError:
                errors["base"] = "invalid_auth"
            except SolaxCloudApiError:
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

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, import_data: dict) -> FlowResult:
        """Handle import from configuration.yaml."""

        return await self.async_step_user(import_data)
