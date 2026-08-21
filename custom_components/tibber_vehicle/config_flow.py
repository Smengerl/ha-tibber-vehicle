"""Config flow for Tibber Vehicle.

Scaffold only. Design decision (docs/DECISIONS.md): use Home Assistant's
built-in homeassistant.helpers.config_entry_oauth2_flow instead of
reimplementing the loopback-listener approach from weconnect_mvp's
tibber_client.py. The client id/secret registered at
https://data-api.tibber.com/clients/manage/ should be stored as a HA
Application Credential (see the `application_credentials` platform), not as
plain config entry data.
"""
from __future__ import annotations

import logging

from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

_LOGGER = logging.getLogger(__name__)


class TibberVehicleOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow for Tibber Vehicle, driven by HA's OAuth2 helper."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict:
        # TODO: return {"scope": " ".join(OAUTH2_SCOPES)} once the
        # Application Credentials provider for this domain is registered
        # (see application_credentials.py, not yet created) and PKCE
        # parameters are wired up.
        raise NotImplementedError

    # TODO: async_oauth_create_entry — resolve the paired vehicle(s) via
    # GET /v1/homes -> GET /v1/homes/{id}/devices (see docs/CONTEXT.md §3)
    # and set them as the config entry's unique_id/data before finishing.
