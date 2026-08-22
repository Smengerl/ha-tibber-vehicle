# Context and background

Written 2026-08-21 when this repo was scaffolded, from a Claude Code chat
session and prior research into the Tibber Data API.
This is the durable record of *why* this project exists and what's already
known — read this before writing any real code here.

## 1. The chain of events that led here

1. **VW closed direct third-party access to its backend.** `emea.bff.cariad.digital`
   (the We Connect BFF) stopped accepting third-party app tokens, confirmed
   by direct testing.
2. **This broke the real Home Assistant instance's VW integration
   independently.** The HACS-installed integration on that HA instance —
   [`robinostlund/homeassistant-volkswagencarnet`](https://github.com/robinostlund/homeassistant-volkswagencarnet)
   (domain `volkswagencarnet`) — is, as of `v5.5.1` (published 2026-08-17,
   still the latest release as of 2026-08-21), marked broken by its own
   maintainers in pinned issue
   [#989](https://github.com/robinostlund/homeassistant-volkswagencarnet/issues/989):
   *"Volkswagen has recently changed its authentication and API access
   mechanisms, preventing third-party applications from obtaining the tokens
   required to access vehicle data... there is no feasible workaround."*
   Two independent attempts at direct VW backend access hit the identical
   block.
3. **Tibber is a sanctioned alternative.** Tibber is an official VW
   integration partner. A VW vehicle paired inside a user's Tibber account
   is readable through Tibber's own public, documented, OAuth2 **Data API**
   (`data-api.tibber.com`) — a different API from the older Tibber GraphQL
   API (`developer.tibber.com`, prices/consumption/Pulse only, no vehicles).
   Its auth flow, scopes, endpoints, and field shapes were fully researched
   and confirmed live end-to-end on 2026-08-21 — see §3 below for the
   summary this integration's OAuth2 client is modeled on.
4. **Under the hood, Tibber's VW support is itself backed by
   [Enode](https://enode.com)**, a third-party EV/energy-device aggregator —
   confirmed by decoding the device `id` returned from Tibber's API (it
   decodes to `"volkswagen enode vehicle:<uuid>"`). Irrelevant to this
   integration's code (Tibber's API is the only thing it talks to), but
   explains why Tibber's data is read-only even though Enode's own API
   reportedly supports write operations — Tibber chose not to expose control
   endpoints publicly.

## 2. Why this is a standalone integration, not built on an existing library

A Python ecosystem exists for talking to VW-group vehicles directly:
**`carconnectivity`** (Till Steinbach's connector-based library —
`CarConnectivity-connector-{volkswagen,skoda,volkswagen-na,seatcupra,
audi,tronity}` + plugins, including an MQTT-based
`CarConnectivity-plugin-homeassistant`). **No Tibber connector exists in
that ecosystem** — it talks to each manufacturer's backend directly, which
is exactly the access path VW closed (§1). Pulling in that whole
plugin/connector infrastructure for 5 sensor values read from a completely
different API (Tibber's) would be the wrong shape for this integration.

This repo (`ha-tibber-vehicle`) is therefore a **standalone Home Assistant
custom integration** — a new `custom_components/tibber_vehicle/` folder,
own domain, own entities, no dependency on `carconnectivity` or on
`homeassistant-volkswagencarnet` (§1). It exists specifically to get
Tibber-sourced vehicle data into Home Assistant's entity/dashboard/
automation system via Tibber's own public Data API.

## 3. What the Tibber Data API actually offers

Confirmed live against the real API (initially 2026-08-21, re-verified
end-to-end 2026-08-23 — see `docs/DECISIONS.md`):

- **Auth:** OAuth2 Authorization Code flow (PKCE recommended), via
  `thewall.tibber.com`. Access tokens ~1h, refresh tokens ~30 days
  (rotating). Client registered at `data-api.tibber.com/clients/manage/`.
- **Scopes needed:** `openid profile email offline_access data-api-user-read
  data-api-homes-read data-api-vehicles-read` (the first five come bundled
  as a "required" group in the registration UI; only the `homes-read` and
  `vehicles-read` category scopes need active selection).
- **Endpoints (the complete set, confirmed via the OpenAPI schema — nothing
  else exists):**
  ```
  GET /v1/homes
  GET /v1/homes/{homeId}/devices
  GET /v1/homes/{homeId}/devices/{deviceId}
  GET /v1/homes/{homeId}/devices/{deviceId}/history
  GET /v1/homes/{homeId}/live-events            (SSE, meters only, not vehicles)
  GET /v1/homes/{homeId}/live-events/devices
  ```
  **Every endpoint is `GET`. This API is read-only — no start/stop
  charging, no target-SoC set, no climate control.** Confirm this hasn't
  changed before assuming otherwise.
- **Vehicles are not home-scoped** — a paired vehicle appears under every
  home the token can see; match by VIN (`externalId` in the device object)
  if more than one vehicle exists.
- **Vehicle capability fields** (the complete set for a VW/Enode-backed
  vehicle, confirmed live):

  | Capability id | Meaning | Unit / values |
  |---|---|---|
  | `storage.stateOfCharge` | State of charge | % |
  | `storage.targetStateOfCharge` | Configured charge limit (read-only) | % |
  | `range.remaining` | Estimated range | meters — convert to km |
  | `connector.status` | Plug status | `connected` / `disconnected` / `unknown` |
  | `charging.status` | Charging status | `charging` / `idle` / `unknown` |

  Plus `attributes` (`vinNumber`, `isOnline`) and `status.lastSeen` (ISO
  8601 staleness indicator) outside the `capabilities` array.
- **`externalId` is the bare VIN**, no `vendor:` prefix, for this
  VW/Enode-backed device — code should split on `:` defensively and fall
  back to the whole string, matching what the reference implementation
  (evcc, see below) already does.
- **Mandatory header:** a `User-Agent` following
  `<App>/<Version> [(platform hints)]`; missing/malformed risks throttling.
  Backoff with full jitter on `429`/`5xx`; don't retry `400/401/403/404`.

## 4. Reference implementations

- **evcc** (`evcc-io/evcc`) already ships a Tibber vehicle template
  ([issue](https://github.com/evcc-io/evcc/issues/30468),
  [PR](https://github.com/evcc-io/evcc/pull/30487),
  [docs](https://docs.evcc.io/en/vehicles/tibber/)) — Go, but the exact same
  OAuth2 config and capability ids. Good to diff against if something in the
  API's behavior seems to have changed since 2026-08-21.
- **Two existing HACS Tibber↔HA integrations were found and are worth
  knowing about but not copying from:**
  [`marq24/ha-tibber-graphapi`](https://github.com/marq24/ha-tibber-graphapi)
  and [`leeyuentuen/tibber_ev`](https://github.com/leeyuentuen/tibber_ev).
  **Both use username/password against Tibber's reverse-engineered internal
  mobile-app GraphQL API**, not the official documented OAuth2 Data API this
  project uses — that's a materially worse foundation (undocumented,
  unstable, credentials stored instead of OAuth tokens). This project
  intentionally does not build on either.

## 5. Design decisions already made

See [`docs/DECISIONS.md`](docs/DECISIONS.md) for the reasoning; short
version:

- Standalone `custom_components/tibber_vehicle/`, not a fork/extension of
  `homeassistant-volkswagencarnet`, and not a `carconnectivity` connector.
- Use Home Assistant's built-in
  `homeassistant.helpers.config_entry_oauth2_flow` for the OAuth2 dance
  instead of a custom loopback-listener approach — HA has native support
  for exactly this pattern.
- `DataUpdateCoordinator` doing non-interactive refresh-token polling only,
  keeping the one-time interactive login separate from ongoing refresh.
