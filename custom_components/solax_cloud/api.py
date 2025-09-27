"""API client for the SolaX Cloud integration."""

from __future__ import annotations

from asyncio import TimeoutError as AsyncioTimeoutError
from dataclasses import dataclass

from json import JSONDecodeError

from aiohttp import ClientError, ClientResponseError, ClientSession, ContentTypeError
from typing import Any, Final

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


_AUTH_MESSAGE_CONTEXT: Final[tuple[str, ...]] = ("token", "tokenid", "serial", "sn", "inverter")

_AUTH_ERROR_MARKERS: Final[tuple[str, ...]] = (
    "not match",
    "not belong",
    "does not belong",
    "doesn't belong",
    "not exist",
    "does not exist",
    "doesn't exist",
    "invalid",
    "mismatch",
    "error",
    "expired",
)


def _redact_value(value: str, keep: int = 4) -> str:
    """Return a redacted representation of sensitive values."""

    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"


class SolaxCloudApiClient:
    """Minimal SolaX Cloud API client."""

    def __init__(self, session: ClientSession, data: SolaxCloudRequestData) -> None:
        self._session = session
        self._data = data
        self._base_url: str | None = None
        self._log_context: dict[str, Any] = {
            "token_id": _redact_value(data.token_id),
            "serial_number": _redact_value(data.serial_number),
        }

    def _context(self, **extra: Any) -> dict[str, Any]:
        """Return logging context enriched with integration metadata."""

        context = dict(self._log_context)
        context.update(extra)
        return context

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
                LOGGER.error(
                    "SolaX Cloud request to %s failed: %s",
                    base_url,
                    err,
                    extra=self._context(endpoint=base_url),
                    exc_info=err,
                )
                if base_url == self._base_url:
                    self._base_url = None
                continue

            self._base_url = base_url
            return result

        if last_error is not None:
            LOGGER.error(
                "SolaX Cloud data update failed after exhausting all endpoints",
                extra=self._context(error=str(last_error)),
            )
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
                try:
                    response.raise_for_status()
                except ClientResponseError as err:
                    LOGGER.error(
                        "SolaX Cloud API request returned HTTP %s: %s",
                        err.status,
                        err.message,
                        extra=self._context(endpoint=base_url, status=err.status),
                        exc_info=err,
                    )
                    raise SolaxCloudApiError(
                        "Could not connect to the SolaX Cloud API"
                    ) from err
                try:
                    payload: dict = await response.json(content_type=None)
                except (ContentTypeError, JSONDecodeError) as err:
                    LOGGER.error(
                        "Invalid JSON payload received from the SolaX Cloud API",
                        extra=self._context(endpoint=base_url, content_type=response.content_type),
                        exc_info=err,
                    )
                    raise SolaxCloudApiError(
                        "Invalid response received from the SolaX Cloud API"
                    ) from err
        except ClientError as err:
            LOGGER.error(
                "Error communicating with the SolaX Cloud API",
                extra=self._context(endpoint=base_url),
                exc_info=err,
            )
            raise SolaxCloudApiError("Could not connect to the SolaX Cloud API") from err
        except AsyncioTimeoutError as err:
            LOGGER.error(
                "Timeout while communicating with the SolaX Cloud API",
                extra=self._context(endpoint=base_url),
                exc_info=err,
            )
            raise SolaxCloudApiError("Timeout while communicating with the SolaX Cloud API") from err

        LOGGER.debug(
            "Received SolaX Cloud payload",
            extra={"endpoint": base_url, "payload": payload},
        )

        if not payload.get(SUCCESS_KEY, False):
            message = payload.get(EXCEPTION_KEY) or "Unknown error"
            normalized = message.casefold()
            if any(token in normalized for token in _AUTH_MESSAGE_CONTEXT) and any(
                marker in normalized for marker in _AUTH_ERROR_MARKERS
            ):
                LOGGER.error(
                    "Authentication with the SolaX Cloud API failed: %s",
                    message,
                    extra=self._context(endpoint=base_url),
                )
                raise SolaxCloudAuthenticationError(message)
            LOGGER.error(
                "SolaX Cloud API returned an error response: %s",
                message,
                extra=self._context(endpoint=base_url, raw_payload=payload),
            )
            raise SolaxCloudApiError(message)

        if RESULT_KEY not in payload or not isinstance(payload[RESULT_KEY], dict):
            LOGGER.error(
                "Unexpected payload structure received from the SolaX Cloud API",
                extra=self._context(endpoint=base_url, raw_payload=payload),
            )
            raise SolaxCloudApiError("Unexpected API payload received")

        return payload[RESULT_KEY]
