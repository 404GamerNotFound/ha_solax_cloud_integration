"""Tests for the config flow helpers."""

from __future__ import annotations

from custom_components.solax_cloud.config_flow import _classify_api_error


def test_classify_api_error_for_unknown_message() -> None:
    """An unknown API error should map to a connection issue."""

    error, placeholders = _classify_api_error("Unknown error occurred")

    assert error == "cannot_connect"
    assert placeholders is None


def test_classify_api_error_for_blank_message() -> None:
    """A blank API error should also map to a connection issue."""

    error, placeholders = _classify_api_error("   ")

    assert error == "cannot_connect"
    assert placeholders is None


def test_classify_api_error_for_specific_message() -> None:
    """Specific API errors should surface their message to the user."""

    error, placeholders = _classify_api_error("Rate limited")

    assert error == "api_error"
    assert placeholders == {"error": "Rate limited"}
