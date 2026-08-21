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
  integrations use — not stored as plain config entry data, and **not**
  something to add via `configuration.yaml`; it's entirely UI/storage-based
  (`.storage/application_credentials`).
- `custom_components/tibber_vehicle/application_credentials.py` is what
  makes "Tibber Vehicle" show up as an option at all on Settings > Devices
  & Services > Application Credentials ("OAuth Anmeldedaten" in the German
  UI) — without this file the domain never appears there, independent of
  whether the integration is otherwise installed. It declares the
  authorize/token URLs (`async_get_authorization_server`) and supplies the
  Tibber-client-registration walkthrough shown in that dialog
  (`async_get_description_placeholders` + the matching
  `application_credentials.description` string in `strings.json`/
  `translations/en.json`).
- The one-time interactive consent still happens through a browser, but via
  HA's frontend flow, not a `localhost:8515` redirect URI.

## The registered redirect_uri is always `https://my.home-assistant.io/redirect/oauth` — works fine for a LAN-only instance

Confirmed 2026-08-21 by reading `homeassistant/helpers/config_entry_oauth2_flow.py`
in HA core directly (`async_get_redirect_uri`): as long as the `my`
component is loaded — the default, part of `default_config`, true for
Simon's real instance — HA always uses the constant
`MY_AUTH_CALLBACK_PATH = "https://my.home-assistant.io/redirect/oauth"` as
the redirect_uri sent to the OAuth provider, **regardless of whether the HA
instance has any public URL configured.** This is the one value to register
as the redirect URI when creating the OAuth2 client at
`data-api.tibber.com/clients/manage/` — not the instance's local address
(e.g. `http://homeassistant.local:8123`).

This works for a purely LAN-only instance (confirmed relevant here: the
real HA instance has no public/external URL, only
`http://homeassistant.local:8123`) because the final hop back to the local
instance is a **client-side-only browser redirect**, not a server-to-server
call: `my.home-assistant.io/redirect/oauth` is a static page that reads
which HA instance URL the browser last used (stored client-side) and
302-redirects the *browser* to `<that instance>/auth/external/callback` —
`my.home-assistant.io`'s own servers never need network access to the LAN
instance.

How the browser gets bounced back to the *specific* local instance: not
via the OAuth `state` parameter (confirmed by reading
`async_generate_authorize_url` — the JWT-encoded `state` only carries
`flow_id` and the same `my.home-assistant.io` URL again, no local address).
Instead `my.home-assistant.io` relies on **browser-local storage** (per its
own FAQ: "your instance URL is stored locally in your browser and is never
sent to any external service"), set the first time that browser used any
`my.home-assistant.io` link from inside this HA instance. Practical
implication: the very first OAuth link-account attempt in a fresh browser
profile may prompt to confirm/select the instance; subsequent ones are
transparent. Also confirmed: the security-sensitive code-for-token exchange
(with the client secret) never touches `my.home-assistant.io` — it's a
direct server-to-server call from HA's backend to
`thewall.tibber.com/connect/token`, `my.home-assistant.io` is only involved
in the initial browser redirect.

Fallback (only relevant if the `my` component is ever disabled): HA uses
the current request's `HA-Frontend-Base` header instead, i.e. whatever URL
the browser is actually on, appended with `/auth/external/callback` — that
would need to be registered with Tibber verbatim instead, which is more
fragile (exact-match dependent, and Tibber's registration UI may reject a
non-HTTPS URI). Don't design `config_flow.py` around this fallback path;
rely on the `my` component being present.

## Token storage: the config entry itself, not a file this integration manages

Confirmed 2026-08-21 by reading `config_entry_oauth2_flow.py`'s default
`async_step_creation`/`async_oauth_create_entry`: once the OAuth2 flow
completes, the token dict (`access_token`, `refresh_token`, `expires_in`
→ converted to `expires_at`, etc.) is stored directly as
`entry.data["token"]` on the config entry HA creates
(`{"auth_implementation": ..., "token": token}` passed to
`async_create_entry`). Persistence is entirely HA core's job — config entry
data lives in `.storage/core.config_entries` inside the HA config
directory, not a file this integration reads/writes itself. Refresh at
runtime works the same way: `OAuth2Session.async_ensure_token_valid()`
(used from the coordinator, per the design above) calls
`hass.config_entries.async_update_entry(entry, data={**entry.data, "token":
new_token})` under the hood, so a refreshed token silently replaces the old
one in the same place.

Practical implication for `config_flow.py`/`__init__.py`: no custom
token-storage code is needed or should be written — don't reimplement
anything resembling `tibber_client.py`'s `TokenStore` here. The only thing
left to implement is `async_oauth_create_entry` (currently a bare TODO
comment) — override it to resolve the paired vehicle(s) via `GET /v1/homes`
→ `GET /v1/homes/{id}/devices` before calling the default behavior via
`super().async_oauth_create_entry(data)`, so the entry's title/unique_id
reflect the actual vehicle instead of just the OAuth implementation name.

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
