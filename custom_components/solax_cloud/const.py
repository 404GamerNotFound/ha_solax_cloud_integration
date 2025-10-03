"""Constants for the SolaX Cloud integration."""

from __future__ import annotations

from logging import Logger, getLogger

DOMAIN = "solax_cloud"
PLATFORMS: list[str] = ["sensor"]

LOGGER: Logger = getLogger(__package__)

API_HOSTS: tuple[str, ...] = (
    "www.solaxcloud.com",
    "api.solaxcloud.com",
    "euapi.solaxcloud.com",
    "usapi.solaxcloud.com",
    "global.solaxcloud.com",
)

API_PORTS: tuple[str, ...] = (":9443", "")

API_PATHS: tuple[str, ...] = (
    "/proxy/api/getRealtimeInfo.do",
    "/proxyApp/api/getRealtimeInfo.do",
    "/proxyApp/proxy/api/getRealtimeInfo.do",
)

API_BASE_URLS: tuple[str, ...] = tuple(
    dict.fromkeys(
        f"https://{host}{port}{path}"
        for host in API_HOSTS
        for port in API_PORTS
        for path in API_PATHS
    )
)

CONF_TOKEN_ID = "token_id"
CONF_SERIAL_NUMBER = "serial_number"
CONF_API_BASE_URL = "api_base_url"
DEFAULT_NAME = "SolaX Cloud"

COORDINATOR_UPDATE_INTERVAL = 300  # seconds

RESULT_KEY = "result"
SUCCESS_KEY = "success"
EXCEPTION_KEY = "exception"
