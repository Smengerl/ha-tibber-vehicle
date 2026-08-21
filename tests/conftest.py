"""Shared pytest fixtures for the Tibber Vehicle test suite.

Uses pytest-homeassistant-custom-component, which supplies the `hass`
fixture (an in-process HA core instance) and auto-enables custom
integration loading for anything under custom_components/. See
docs/DEVELOPMENT.md for how to run these tests.
"""
from __future__ import annotations

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom_components/ during tests (see the plugin's docs)."""
    yield
