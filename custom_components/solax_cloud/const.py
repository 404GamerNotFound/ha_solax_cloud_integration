"""Constants for the SolaX Cloud integration."""

from __future__ import annotations

from logging import Logger, getLogger

DOMAIN = "solax_cloud"
PLATFORMS: list[str] = ["sensor"]

LOGGER: Logger = getLogger(__package__)

API_BASE_URLS: tuple[str, ...] = (
    "https://www.solaxcloud.com:9443/proxy/api/getRealtimeInfo.do",
    "https://euapi.solaxcloud.com:9443/proxy/api/getRealtimeInfo.do",
)

CONF_TOKEN_ID = "token_id"
CONF_SERIAL_NUMBER = "serial_number"
DEFAULT_NAME = "SolaX Cloud"

COORDINATOR_UPDATE_INTERVAL = 300  # seconds

RESULT_KEY = "result"
SUCCESS_KEY = "success"
EXCEPTION_KEY = "exception"
