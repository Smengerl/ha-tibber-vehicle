# Design decisions

Decisions made during scaffolding (2026-08-21), before any real
implementation. Record new decisions here as they're made — append, don't
rewrite history.

## Standalone integration, not an extension of anything

A new `custom_components/tibber_vehicle/` with its own domain, entities and
config entries. Not a fork or patch of `homeassistant-volkswagencarnet`
(different data source, different auth mechanism, and that integration is
currently broken anyway — extending broken code would be the wrong
foundation). Not a `carconnectivity` connector either (that ecosystem isn't
installed on the target HA instance and pulling it in — plus its
MQTT-based `CarConnectivity-plugin-homeassistant` — would be a lot of
infrastructure for 5 sensor values). Full reasoning in `docs/CONTEXT.md` §2.

Runs fully independently alongside `volkswagencarnet` on the same HA
instance — no shared code, no shared config, so a failure in one can't
affect the other, and if VW ever restores third-party access this
integration doesn't need to be touched or removed.

## OAuth2 via Home Assistant's built-in helper, not a custom loopback server

`weconnect_mvp`'s `tibber_client.py` proof-of-concept implements its own
local loopback HTTP server to catch the OAuth2 redirect — appropriate for a
standalone script, wrong fit for a HA integration. Home Assistant ships
`homeassistant.helpers.config_entry_oauth2_flow` specifically for this
pattern (Authorization Code flow with browser redirect back into HA,
integrates with `my.home-assistant.io` for instances without a public URL,
handles refresh-token storage and rotation as part of the config entry).
Use that instead of reimplementing PKCE/token exchange/local server from
scratch — same OAuth2 config (endpoints, scopes) as documented in
`docs/CONTEXT.md` §3, different transport for the redirect.

Concretely this means:
- `config_flow.py` subclasses `config_entry_oauth2_flow.AbstractOAuth2FlowHandler`.
- Client id/secret registered as a HA **Application Credential**
  (`application_credentials` platform), the same mechanism HA's own cloud
  integrations use — not stored as plain config entry data.
- The one-time interactive consent still happens through a browser, but via
  HA's frontend flow, not a `localhost:8515` redirect URI.

## `DataUpdateCoordinator` for polling, refresh-token-only at runtime

Standard HA pattern: one `DataUpdateCoordinator` per config entry, polling
`GET /v1/homes/{homeId}/devices/{deviceId}` on an interval (TBD, but should
respect Tibber's rate-limiting guidance — see `docs/CONTEXT.md` §3) using
only non-interactive refresh-token exchange. This mirrors the separation
`tibber_client.py`'s `TokenStore` already has between one-time interactive
login and ongoing refresh — HA's OAuth2 session helper
(`OAuth2Session`) gives this for free once the Application Credential /
config flow above is wired up.

## Sensor entities map 1:1 to Tibber's capability ids

No abstraction layer beyond what HA's entity model already provides — five
sensors (`storage.stateOfCharge`, `storage.targetStateOfCharge`,
`range.remaining`, `connector.status`, `charging.status`), full list and
units in `README.md`. No attempt to backfill doors/climate/position/lock
data from elsewhere — this integration is intentionally narrow-scope. If a
richer feature set is ever wanted, that's a new decision to make later
(e.g. combining sources), not something to design around speculatively now.

## Dev workflow: local repo → disposable Docker HA → HACS custom repo

Full detail in `docs/DEVELOPMENT.md`. Short version: never develop directly
against the real Home Assistant Green's mounted filesystem (Samba/SSH
add-on) — too slow, too risky against a production system with real
devices. Iterate locally against a throwaway Dockerized HA instance, add
unit tests via `pytest-homeassistant-custom-component`, and only reach the
real HA instance by pushing to GitHub and installing this repo as a HACS
custom repository (same install path `volkswagencarnet` already uses there).
