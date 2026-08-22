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
anything resembling `tibber_client.py`'s `TokenStore` here.
`async_oauth_create_entry` is now implemented this way (see "Login flow
implementation" below).

## Login flow implementation — modeled on HA core's Spotify integration

Implemented 2026-08-21, structured after
`homeassistant/components/spotify/{config_flow,__init__,coordinator}.py`
line-for-line where the shape transfers directly (confirmed against the
real source, not from memory) — chosen as the reference because it's one
of the simplest core OAuth2 integrations that still does everything this
one needs: `extra_authorize_data` for scopes, an `async_oauth_create_entry`
override that resolves account-specific info before creating the entry,
and the modern `entry.runtime_data` pattern (a typed
`ConfigEntry[TibberVehicleCoordinator]` alias) instead of the older
`hass.data[DOMAIN][entry_id]` dict.

- **`config_flow.py`**: `extra_authorize_data` returns the scope string
  from `const.OAUTH2_SCOPES`. `async_oauth_create_entry` does a one-shot
  API call (`TibberVehicleApiClient.async_find_first_vehicle`, using the
  fresh access token directly — no `OAuth2Session` yet, since the config
  entry doesn't exist until this method returns) to resolve which vehicle
  this Tibber account exposes, sets the entry's `unique_id` to its VIN, and
  stores `home_id`/`device_id`/`vin` alongside the OAuth `data` dict.
- **`api.py`** (new): a thin `TibberVehicleApiClient` wrapping the three
  `GET` endpoints this integration needs. Response envelope shapes
  (`{"homes": [...]}`, `{"devices": [...]}`) are taken directly from
  `tibber_client.py`'s already-live-tested `homes()`/`devices()` methods,
  not re-guessed. Auth is injected via an `access_token_provider` async
  callback rather than the client holding a token itself — mirrors how
  `spotifyaio.SpotifyClient.refresh_token_function` keeps API access and
  token refresh as separate concerns.
- **`__init__.py`**: `async_get_config_entry_implementation` +
  `OAuth2Session` + `async_ensure_token_valid()`, wrapped in
  `ConfigEntryNotReady` on failure — same shape as Spotify's
  `async_setup_entry`. The coordinator gets an `_access_token()` closure
  that re-validates the session before every use, so token refresh is
  fully transparent to `api.py`.
- **`coordinator.py`** / **`sensor.py`**: implemented as designed above —
  `_async_update_data` calls `async_get_device`, wraps
  `TibberVehicleApiError` as `UpdateFailed`; sensors read their capability
  id out of `coordinator.data["capabilities"]`, converting `range.remaining`
  from meters to km.
- **`entity.py`** (new, added after the first pass missed it): a shared
  `TibberVehicleEntity(CoordinatorEntity)` base class setting
  `_attr_device_info`, so all five entities group under one HA **device**
  representing the vehicle itself (identified by VIN, manufacturer/model
  from the device detail's `info` object) — this is the actual point of
  the integration ("the car should appear as a device", not five loose
  entities with no device grouping). Modeled on Spotify's own `entity.py`,
  but **without** `entry_type=DeviceEntryType.SERVICE` — Spotify sets that
  because its "device" is a cloud account; ours is a physical vehicle, so
  it should register as a regular device, not get folded into HA's
  "services" bucket.

## Entity identity matched to `homeassistant-volkswagencarnet`, not invented fresh

2026-08-22: entity names, icons, units, and device classes were changed to
match the equivalent entity in `robinostlund/homeassistant-volkswagencarnet`
(backed by the `volkswagencarnet` PyPI package's `vw_dashboard.py`, which
defines every instrument as `(EntityClass, [], {"attr": ..., "name": ...,
"icon": ..., "unit": ..., "device_class": ..., "state_class": ...})`
tuples). Reasoning: this project exists specifically as a fallback data
source for the same underlying question ("what's my VW doing") that
`volkswagencarnet` answers when it isn't blocked (see `docs/CONTEXT.md`
§1) — matching identity means a user's dashboards/automations/history
graphs built against one keep working (or need only a device swap, not an
entity rewrite) if they ever switch between the two, or run both and want
consistent naming.

Comparison table (VW Connect's `attr` is its internal instrument key, not
user-visible — the `name` column is what actually matters for this match):

| Tibber capability | VW Connect `attr` | Matched name | Icon | Unit | device_class | state_class | Entity type |
|---|---|---|---|---|---|---|---|
| `storage.stateOfCharge` | `battery_level` | Battery level | `mdi:battery` | % | `battery` | `measurement` | sensor |
| `storage.targetStateOfCharge` | `battery_target_charge_level` | Battery target charge level | `mdi:battery-arrow-up` | % | `battery` | — | sensor |
| `range.remaining` | `electric_range` | Electric range | `mdi:car-electric` | km | `distance` | `measurement` | sensor |
| `connector.status` | `external_power` | *not matched — see below* | `mdi:ev-plug-type2` | — | — | — | sensor |
| `charging.status` | `charging_state` | Charging state | `mdi:car-turbocharger` | — | — | — | sensor |

Notes on the places this isn't a blind 1:1 copy:
- **`range.remaining` → `electric_range`, not `battery_cruising_range`.**
  VW Connect has both; `electric_range` ("Electric range") is the direct
  semantic match to Tibber's own field description ("estimated remaining
  driving range"), `battery_cruising_range` looks like a secondary/derived
  value in VW's own model.
- **`storage.targetStateOfCharge` stays a `sensor`, not VW's newer
  `Number` entity.** VW Connect has *both* a plain `Sensor` and a writable
  `Number` for the same `attr` (the latter added later, for
  vehicles/regions where VW's API accepts writes). Tibber's Data API is
  confirmed read-only (`docs/CONTEXT.md` §3) — offering a `Number` entity
  a user could try to drag/type into, with the write silently doing
  nothing, would be actively misleading. The plain-`Sensor` metadata
  (name/icon/unit/device_class) is what's matched here, not the `Number`
  entity's.
- **`connector.status` deliberately stays a plain `sensor`, not VW
  Connect's `binary_sensor`.** A first pass (same day) did match VW
  Connect's actual entity type here too — `TibberVehicleBinarySensor`
  mapping `connected`/`disconnected` to `True`/`False` and `"unknown"` to
  `is_on` returning `None` (HA's unavailable/unknown state). Simon then
  asked to revert this one back to a string sensor — the binary_sensor
  *type* being technically valid wasn't the issue, but the tri-state
  Tibber value collapsing "unknown" into a generic unavailable state
  (rather than staying visibly distinct from `disconnected`) apparently
  wasn't wanted. Reverted to `SensorEntityDescription(name="Plug status",
  icon="mdi:ev-plug-type2")` — `binary_sensor.py` removed,
  `Platform.BINARY_SENSOR` removed from `__init__.py`'s `PLATFORMS`.
  `mdi:ev-plug-type2` (not one of VW Connect's own icons for this
  specific field, since VW has no string-sensor equivalent to copy from)
  was picked from the same icon family VW Connect uses elsewhere for
  plug-related entities (e.g. `mdi:ev-plug-type1` for "Charger type").

**Verification done:** every module import-checked against a real
`homeassistant` pip install (Python 3.14, matching `weconnect_mvp`'s own
venv) — confirms import paths, class/attribute names, and the PEP 695
`type` alias syntax are all correct. **Not yet done:** no live OAuth2
round-trip against Tibber, no boot inside an actual HA instance (Docker
image pulls were unreachable from this sandboxed environment when tried,
see `docs/DEVELOPMENT.md` if that's still true later) — that's the
remaining verification step before this is trustworthy end-to-end.

**Known limitations, deliberately deferred rather than blocking a working
v1:**
- **No PKCE.** Tibber's own docs call PKCE "optional but recommended" for
  the auth code flow; HA's default `LocalOAuth2Implementation` (what
  `application_credentials.py`'s `AuthorizationServer` produces) doesn't
  send PKCE parameters. Withings-style integrations add a custom
  `AuthImplementation` subclass to get it — worth doing later, not
  required for a working login.
- **No reauth flow.** If the refresh token is ever revoked/expires beyond
  recovery, the config entry will start failing rather than prompting the
  user to re-link, unlike Spotify's `async_step_reauth`. A real gap, but
  additive — doesn't change anything about the flow already built.
- **First vehicle wins, no multi-vehicle support.** `async_find_first_vehicle`
  stops at the first device found across all homes. Fine for the single
  paired VW this was built against; a household with multiple Tibber-paired
  vehicles would need one config entry per vehicle, which isn't wired up
  (the unique-id-per-VIN design would support it, but the config flow
  doesn't yet offer a picker step).

## `DataUpdateCoordinator` for polling, refresh-token-only at runtime

Standard HA pattern: one `DataUpdateCoordinator` per config entry, polling
`GET /v1/homes/{homeId}/devices/{deviceId}` on an interval (`const.
DEFAULT_UPDATE_INTERVAL_SECONDS = 300`, i.e. 5 minutes) using only
non-interactive refresh-token exchange. This mirrors the separation
`tibber_client.py`'s `TokenStore` already has between one-time interactive
login and ongoing refresh — HA's OAuth2 session helper
(`OAuth2Session`) gives this for free once the Application Credential /
config flow above is wired up.

**Polling is confirmed the only option, not just the convenient default.**
2026-08-22: downloaded and searched the full Tibber Data API OpenAPI spec
(`https://data-api.tibber.com/openapi/v1.json`) after Simon observed the
visible update cadence looking closer to ~10 minutes than the configured
5. Two findings, now recorded in `weconnect_mvp`'s `TIBBER_API.md` session
log as the durable source (not duplicated in full here):
- The API's only push/SSE mechanism (`GET /homes/{homeId}/live-events`)
  is scoped to metering hardware only (Pulse CT clamps / Bridge-attached
  Pulses) per `GET .../live-events/devices`'s own description — vehicles
  are never mentioned. There is no non-polling way to read vehicle data
  from this API at all.
- The spec documents **no** refresh interval, rate limit, or recommended
  client polling cadence anywhere (exhaustive keyword search across the
  whole spec text came back empty). The observed ~10-minute effective
  cadence is most likely `status.lastSeen`/the underlying value simply not
  changing between every 5-minute poll (Tibber's own backend refresh
  against Enode/VW happens on some undocumented schedule we can't see or
  tune against) — not a bug in this integration's polling. Tightening
  `DEFAULT_UPDATE_INTERVAL_SECONDS` below 5 minutes would not be tuning
  against any documented ceiling; there isn't one to tune against.

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
