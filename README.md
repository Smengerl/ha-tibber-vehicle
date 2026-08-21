# ha-tibber-vehicle

A Home Assistant custom integration (installable via HACS) that reads EV
vehicle data — state of charge, target SoC, estimated range, plug status,
charging status — from the official [Tibber Data API](https://data-api.tibber.com)
(`data-api.tibber.com`), for any vehicle paired inside a Tibber account.

**Status: scaffold only, not yet functional.** No OAuth2 flow, coordinator,
or sensor logic is implemented yet — `config_flow.py`, `coordinator.py`,
`sensor.py` are stubs. The installation steps below describe how it *will*
work once that lands; following them today ends at step 5 with nothing to
configure yet. See [`docs/CONTEXT.md`](docs/CONTEXT.md) for the full
background and [`docs/DECISIONS.md`](docs/DECISIONS.md) for the design
decisions already made.

## Why this exists

Home Assistant's usual route to Volkswagen-group vehicle data (the
[`robinostlund/homeassistant-volkswagencarnet`](https://github.com/robinostlund/homeassistant-volkswagencarnet)
integration) is currently broken — Volkswagen closed third-party access to
its backend auth (see repo's pinned issue
[#989](https://github.com/robinostlund/homeassistant-volkswagencarnet/issues/989)).
Tibber is an official VW integration partner and exposes vehicle data paired
inside a user's Tibber account through its own public, documented, OAuth2
Data API — a sanctioned alternative read-only path. Full background in
[`docs/CONTEXT.md`](docs/CONTEXT.md).

This project is **independent of** `weconnect_mvp` (a separate MCP-server
project on this machine that hit the same VW block and has its own,
further-along Tibber OAuth2 proof-of-concept — see
[`docs/CONTEXT.md`](docs/CONTEXT.md) for how the two relate and what this
repo reuses from it).

## What it will expose (planned)

Per paired vehicle, up to 5 sensor entities — this is the *complete* data
surface the Tibber Data API offers for vehicles, confirmed by direct
inspection of its OpenAPI schema (no doors/climate/position/lock data exists
in this API at all):

| Entity (planned) | Tibber capability id | Unit |
|---|---|---|
| State of charge | `storage.stateOfCharge` | % |
| Target state of charge | `storage.targetStateOfCharge` | % |
| Estimated range | `range.remaining` | km (converted from m) |
| Plug status | `connector.status` | connected / disconnected / unknown |
| Charging status | `charging.status` | charging / idle / unknown |

No write/control support is possible — the Tibber Data API is read-only
(confirmed: only `GET` endpoints exist in its schema).

## Installation & setup

### 1. Register an OAuth2 client with Tibber (one-time)

Go to [`data-api.tibber.com/clients/manage/`](https://data-api.tibber.com/clients/manage/),
log in with your Tibber account, and create a new client:

- Scopes: select at least `data-api-homes-read` and `data-api-vehicles-read`.
- Redirect URI: enter exactly **`https://my.home-assistant.io/redirect/oauth`**
  — not your own instance's address, even if (like the primary target
  instance for this integration) it's LAN-only with no public URL. This is
  Home Assistant's standard shared redirect page for OAuth2 account
  linking; the actual trip back to your instance happens entirely in your
  browser, so it works regardless of whether your instance is reachable
  from the internet. Full mechanism traced from HA's own source code in
  [`docs/DECISIONS.md`](docs/DECISIONS.md).

Note down the client ID and secret shown after creation — the secret is
only displayed once.

### 2. Install via HACS

In HACS on your Home Assistant instance: **⋮ → Custom repositories** → add
this repo's URL, category "Integration". Then install **Tibber Vehicle**
from the store and **restart Home Assistant** — a first install only
becomes fully known to HA (selectable anywhere in its UI) after a restart.

### 3. Add the Application Credential

Settings → Devices & Services → **Application Credentials** ("OAuth
Anmeldedaten" in the German UI) → Add application credential → select
**Tibber Vehicle** → enter the client ID/secret from step 1.

This has to happen *after* step 2, not before — the integration dropdown
here only lists domains HA currently has installed and loaded, so "Tibber
Vehicle" isn't selectable until the HACS install (+ restart) has completed.

### 4. Add the integration

Settings → Devices & Services → Add Integration → **Tibber Vehicle** → this
picks up the credential from step 3 and takes you straight to the OAuth2
consent screen in your browser. Approve access, and the integration
resolves your paired vehicle(s) and creates their sensor entities.

## Development

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for the dev/test workflow
(local repo → disposable Dockerized HA instance for fast iteration →
`pytest-homeassistant-custom-component` for unit tests → releasing a change
to the real instance) and [`CONTRIBUTING.md`](CONTRIBUTING.md) if you want
to contribute.

## License

MIT — see [`LICENSE`](LICENSE).
