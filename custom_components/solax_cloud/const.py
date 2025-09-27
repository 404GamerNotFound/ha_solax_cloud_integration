"""Constants for the SolaX Cloud integration."""

from __future__ import annotations

from logging import Logger, getLogger

DOMAIN = "solax_cloud"
PLATFORMS: list[str] = ["sensor"]

LOGGER: Logger = getLogger(__package__)

_API_HOSTS: tuple[str, ...] = (
    "www.solaxcloud.com",
    "api.solaxcloud.com",
    "euapi.solaxcloud.com",
    "usapi.solaxcloud.com",
)

_API_PORTS: tuple[str, ...] = (":9443", "")

_API_PATHS: tuple[str, ...] = (
    "/proxy/api/getRealtimeInfo.do",
    "/proxyApp/api/getRealtimeInfo.do",
)

API_BASE_URLS: tuple[str, ...] = tuple(
    dict.fromkeys(
        f"https://{host}{port}{path}"
        for host in _API_HOSTS
        for port in _API_PORTS
        for path in _API_PATHS
    )
)

CONF_TOKEN_ID = "token_id"
CONF_SERIAL_NUMBER = "serial_number"
DEFAULT_NAME = "SolaX Cloud"

COORDINATOR_UPDATE_INTERVAL = 300  # seconds

RESULT_KEY = "result"
SUCCESS_KEY = "success"
EXCEPTION_KEY = "exception"
