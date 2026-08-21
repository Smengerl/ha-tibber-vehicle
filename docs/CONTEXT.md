# Context and background

Written 2026-08-21 when this repo was scaffolded, from a Claude Code chat
session plus the prior research already done in the `weconnect_mvp` project.
This is the durable record of *why* this project exists and what's already
known — read this before writing any real code here.

## 1. The chain of events that led here

1. **VW closed direct third-party access to its backend.** `emea.bff.cariad.digital`
   (the We Connect BFF) stopped accepting third-party app tokens. This is
   documented in detail in a sibling project, `weconnect_mvp`, at
   `experiment/vw-device-flow-attestation-bypass/FINDING.md`.
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
   Two independent codebases (that integration, and `weconnect_mvp`'s own
   direct-BFF experiment) hit the identical VW-side block.
3. **Tibber is a sanctioned alternative.** Tibber is an official VW
   integration partner. A VW vehicle paired inside a user's Tibber account
   is readable through Tibber's own public, documented, OAuth2 **Data API**
   (`data-api.tibber.com`) — a different API from the older Tibber GraphQL
   API (`developer.tibber.com`, prices/consumption/Pulse only, no vehicles).
   `weconnect_mvp`'s `experiment/tibber-integration/TIBBER_API.md` is the
   full research record of this API (auth flow, scopes, endpoints, field
   shapes), confirmed live end-to-end on 2026-08-21. **This repo's OAuth2
   client should be modeled on that document and on its accompanying
   `tibber_client.py` proof-of-concept** (same repo), not re-researched from
   scratch.
4. **Under the hood, Tibber's VW support is itself backed by
   [Enode](https://enode.com)**, a third-party EV/energy-device aggregator —
   confirmed by decoding the device `id` returned from Tibber's API (it
   decodes to `"volkswagen enode vehicle:<uuid>"`). Irrelevant to this
   integration's code (Tibber's API is the only thing it talks to), but
   explains why Tibber's data is read-only even though Enode's own API
   reportedly supports write operations — Tibber chose not to expose control
   endpoints publicly.

## 2. This project vs. `weconnect_mvp` — not the same codebase

`weconnect_mvp` is a separate project (an MCP server exposing VW vehicle
data as tools for LLM agents) that:

- Normally talks to VW directly via the **`carconnectivity`** Python
  library (Till Steinbach's connector-based ecosystem —
  `CarConnectivity-connector-{volkswagen,skoda,volkswagen-na,seatcupra,
  audi,tronity}` + plugins). **No Tibber connector exists in that ecosystem.**
  This is a completely different codebase from `homeassistant-volkswagencarnet`
  (§1.2) despite both ultimately reading VW vehicle data — don't confuse the
  two when researching either one.
- Has already built and **live-tested** a working Tibber OAuth2 client
  (`experiment/tibber-integration/tibber_client.py`) as a proof-of-concept
  for a possible `TibberAdapter` inside *its own* `AbstractAdapter`
  interface — see `TIBBER_API.md` §7 for that architecture analysis. That
  analysis is MCP-server-specific (Python ABC classes, `Optional[Model]`
  return contracts) and does not apply directly here, but the underlying
  **OAuth2 flow, scopes, endpoints, and capability field mapping are
  identical** and should be reused conceptually.

This repo (`ha-tibber-vehicle`) is a **standalone Home Assistant custom
integration** — a new `custom_components/tibber_vehicle/` folder, own
domain, own entities, no code dependency on `weconnect_mvp` or on
`carconnectivity`. It exists specifically to get Tibber-sourced vehicle data
into Home Assistant's entity/dashboard/automation system, which
`weconnect_mvp` (an MCP server for LLM tool use, not a HA integration) does
not do and isn't meant to do.

## 3. What the Tibber Data API actually offers

Full detail lives in `weconnect_mvp`'s `TIBBER_API.md` (§3–§5) — summary
here for convenience, **treat that file as the source of truth if the two
ever disagree**, since it documents live-confirmed behavior, this is just a
copy taken at scaffold time:

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
  instead of reimplementing the loopback-listener approach from
  `tibber_client.py` — HA has native support for exactly this pattern.
- `DataUpdateCoordinator` doing non-interactive refresh-token polling only,
  matching how `tibber_client.py`'s `TokenStore` already separates the
  one-time interactive login from ongoing refresh.
