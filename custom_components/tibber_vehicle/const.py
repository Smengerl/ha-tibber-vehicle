"""Constants for the Tibber Vehicle integration.

Values here are taken from the confirmed, live-tested findings in
weconnect_mvp's experiment/tibber-integration/TIBBER_API.md — see
docs/CONTEXT.md §3 in this repo for the condensed version. Don't guess at
replacements without re-checking that document (or the live OpenAPI schema
at https://data-api.tibber.com/playground/) first.
"""

DOMAIN = "tibber_vehicle"

# OAuth2 endpoints (thewall.tibber.com is Tibber's auth server, distinct
# from the data-api.tibber.com API host).
OAUTH2_AUTHORIZE = "https://thewall.tibber.com/connect/authorize"
OAUTH2_TOKEN = "https://thewall.tibber.com/connect/token"
API_BASE = "https://data-api.tibber.com/v1"

# Baseline scopes are bundled automatically by Tibber's client-registration
# UI; the two category scopes below must be actively selected there.
OAUTH2_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "data-api-user-read",
    "data-api-homes-read",
    "data-api-vehicles-read",
]

# Tibber vehicle capability ids -> what they mean. This is the *complete*
# set of vehicle data the Data API exposes as of the 2026-08-21 research —
# no doors/climate/position/lock capabilities exist for vehicles in this
# API at all.
CAPABILITY_STATE_OF_CHARGE = "storage.stateOfCharge"
CAPABILITY_TARGET_STATE_OF_CHARGE = "storage.targetStateOfCharge"
CAPABILITY_RANGE_REMAINING = "range.remaining"
CAPABILITY_CONNECTOR_STATUS = "connector.status"
CAPABILITY_CHARGING_STATUS = "charging.status"

DEFAULT_UPDATE_INTERVAL_SECONDS = 300

# Mandatory on every Tibber Data API request (see docs/CONTEXT.md §3) —
# missing/malformed risks throttling.
USER_AGENT = "ha-tibber-vehicle/0.1.0 (github.com/Smengerl/ha-tibber-vehicle)"
