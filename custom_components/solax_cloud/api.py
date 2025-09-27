"""API client for the SolaX Cloud integration."""

from __future__ import annotations

from asyncio import TimeoutError as AsyncioTimeoutError
from dataclasses import dataclass

from json import JSONDecodeError

from aiohttp import ClientError, ClientSession, ContentTypeError

from .const import (
    API_BASE_URLS,
    EXCEPTION_KEY,
    LOGGER,
    RESULT_KEY,
    SUCCESS_KEY,
)


class SolaxCloudApiError(RuntimeError):
    """Raised when the SolaX Cloud API returns an error."""


class SolaxCloudAuthenticationError(SolaxCloudApiError):
    """Raised when authentication with the SolaX Cloud API fails."""


@dataclass(slots=True)
class SolaxCloudRequestData:
    """Data required to query the SolaX Cloud API."""

    token_id: str
    serial_number: str


class SolaxCloudApiClient:
    """Minimal SolaX Cloud API client."""

    def __init__(self, session: ClientSession, data: SolaxCloudRequestData) -> None:
        self._session = session
        self._data = data
        self._base_url: str | None = None

    async def async_get_data(self) -> dict:
        """Return the latest data from the cloud API."""

        endpoints = (
            [self._base_url] if self._base_url else []
        ) + [url for url in API_BASE_URLS if url != self._base_url]

        last_error: SolaxCloudApiError | None = None

        for base_url in endpoints:
            try:
                result = await self._async_fetch(base_url)
            except SolaxCloudAuthenticationError:
                raise
            except SolaxCloudApiError as err:
                last_error = err
                LOGGER.debug(
                    "SolaX Cloud request failed", extra={"endpoint": base_url, "error": str(err)}
                )
                if base_url == self._base_url:
                    self._base_url = None
                continue

            self._base_url = base_url
            return result

        if last_error is not None:
            raise last_error

        raise SolaxCloudApiError("Could not connect to the SolaX Cloud API")

    async def _async_fetch(self, base_url: str) -> dict:
        """Fetch data from a specific endpoint."""

        params = {
            "tokenId": self._data.token_id,
            "sn": self._data.serial_number,
        }

        LOGGER.debug(
            "Requesting SolaX Cloud data",
            extra={"endpoint": base_url, "params": params},
        )

        try:
            async with self._session.get(base_url, params=params, timeout=30) as response:
                response.raise_for_status()
                payload: dict = await response.json(content_type=None)
        except (ContentTypeError, JSONDecodeError) as err:
            raise SolaxCloudApiError("Invalid response received from the SolaX Cloud API") from err
        except ClientError as err:
            raise SolaxCloudApiError("Could not connect to the SolaX Cloud API") from err
        except AsyncioTimeoutError as err:
            raise SolaxCloudApiError("Timeout while communicating with the SolaX Cloud API") from err

        LOGGER.debug(
            "Received SolaX Cloud payload",
            extra={"endpoint": base_url, "payload": payload},
        )

        if not payload.get(SUCCESS_KEY, False):
            message = payload.get(EXCEPTION_KEY) or "Unknown error"
            # Invalid token/serial number combinations use a specific exception string
            if "not match" in message.lower() or "tokenid" in message.lower():
                raise SolaxCloudAuthenticationError(message)
            raise SolaxCloudApiError(message)

        if RESULT_KEY not in payload or not isinstance(payload[RESULT_KEY], dict):
            raise SolaxCloudApiError("Unexpected API payload received")

        return payload[RESULT_KEY]
