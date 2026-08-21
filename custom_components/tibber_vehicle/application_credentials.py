"""Application credentials platform for Tibber Vehicle.

This is what makes "Tibber Vehicle" appear as an option on Home Assistant's
"OAuth Anmeldedaten" / "Application Credentials" page (Settings > Devices &
Services > Application Credentials) at all — without this file, the domain
never shows up there, regardless of whether the integration is otherwise
installed. See docs/DECISIONS.md for the redirect_uri mechanism this feeds
into.
"""
from __future__ import annotations

from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return the authorization server for Tibber's Data API OAuth2 flow."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders shown on the 'Add credential' dialog."""
    return {
        "client_registration_url": "https://data-api.tibber.com/clients/manage/",
        "redirect_url": "https://my.home-assistant.io/redirect/oauth",
    }
