"""Tests for the SolaX Cloud API client."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError
from pytest import mark
from unittest.mock import AsyncMock, MagicMock

from aiohttp import ContentTypeError
from pytest import raises

from custom_components.solax_cloud.api import (
    SolaxCloudApiClient,
    SolaxCloudApiError,
    SolaxCloudRequestData,
)


@mark.asyncio
async def test_api_client_falls_back_to_alternative_endpoint(monkeypatch) -> None:
    """Ensure the client retries other endpoints when the first one fails."""

    call_order: list[str] = []

    async def _json(_: Any = None, **__: Any) -> dict[str, Any]:
        return {"success": True, "result": {"value": 42}}

    response = AsyncMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = _json

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = response
    context_manager.__aexit__.return_value = False

    session = MagicMock()

    def _mock_get(url: str, *args: Any, **kwargs: Any) -> Any:
        call_order.append(url)
        if len(call_order) == 1:
            raise ClientError
        return context_manager

    session.get.side_effect = _mock_get

    monkeypatch.setattr(
        "custom_components.solax_cloud.api.API_BASE_URLS",
        ("https://first", "https://second"),
        raising=False,
    )

    client = SolaxCloudApiClient(session, SolaxCloudRequestData("token", "serial"))

    result = await client.async_get_data()

    assert call_order == ["https://first", "https://second"]
    assert result == {"value": 42}


@mark.asyncio
async def test_api_client_raises_for_invalid_json(monkeypatch) -> None:
    """Ensure the client fails gracefully when the payload is not JSON."""

    response = AsyncMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ContentTypeError(MagicMock(), ("", ""), message="bad json")

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = response
    context_manager.__aexit__.return_value = False

    session = MagicMock()
    session.get.return_value = context_manager

    monkeypatch.setattr(
        "custom_components.solax_cloud.api.API_BASE_URLS",
        ("https://only",),
        raising=False,
    )

    client = SolaxCloudApiClient(session, SolaxCloudRequestData("token", "serial"))

    with raises(SolaxCloudApiError):
        await client.async_get_data()
