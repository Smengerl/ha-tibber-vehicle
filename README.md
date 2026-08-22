# Tibber Vehicle

[![Validate](https://github.com/Smengerl/ha-tibber-vehicle/actions/workflows/validate.yml/badge.svg)](https://github.com/Smengerl/ha-tibber-vehicle/actions/workflows/validate.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
<!-- Sourced from Home Assistant's own opt-in analytics (https://analytics.home-assistant.io/custom_integrations.json),
     rendered live by shields.io's dynamic JSON badge. Will show 0/invalid until other users install this and have
     Settings > System > Analytics enabled on their own instance - that's expected for a newly-public repo, not a bug. -->
[![Active Installations](https://img.shields.io/badge/dynamic/json?url=https://analytics.home-assistant.io/custom_integrations.json&query=$.tibber_vehicle.total&label=Active%20Installations&color=41BDF5&logo=home-assistant&logoColor=white)](https://analytics.home-assistant.io/custom_integrations.json)

A Home Assistant integration that reads your EV's charge state, range, and
plug status from the official [Tibber Data API](https://data-api.tibber.com)
— for any vehicle paired inside your Tibber account, regardless of make.

## Why this exists

Home Assistant's usual route to Volkswagen-group vehicle data (the
[`homeassistant-volkswagencarnet`](https://github.com/robinostlund/homeassistant-volkswagencarnet)
integration) is currently broken — Volkswagen closed third-party access to
its backend auth. Tibber is an official VW integration partner and already
exposes the vehicle data paired inside your Tibber account through its own
public, documented OAuth2 API. This integration reads that data and turns
it into a Home Assistant device with sensor entities, so you get your
car's charge state back into your dashboards and automations without
depending on VW's own, currently-unreliable API access.

![Tibber Vehicle device with its entities in Home Assistant](docs/images/screenshot.svg)
<!-- TODO: replace docs/images/screenshot.svg with a real screenshot (PNG) of the Tibber Vehicle device once the integration has been verified end-to-end against a live vehicle. -->

## What it exposes

Per paired vehicle, 5 entities — this is the *complete* data surface the
Tibber Data API offers for vehicles, confirmed by direct inspection of its
OpenAPI schema (no doors/climate/position/lock data exists in this API at
all, and no write/control support is possible either). Name, icon, unit,
and device class are matched to the equivalent entity in
`homeassistant-volkswagencarnet` wherever that makes sense, so switching
between the two — or running both side by side — shows consistent entity
identity. Full comparison and reasoning in
[`docs/DECISIONS.md`](docs/DECISIONS.md).

| Entity | Type | Tibber capability id | Unit / device class |
| --- | --- | --- | --- |
| Battery level | sensor | `storage.stateOfCharge` | %, `battery`, measurement |
| Battery target charge level | sensor | `storage.targetStateOfCharge` | %, `battery` |
| Electric range | sensor | `range.remaining` | km (converted from m), `distance`, measurement |
| Plug status | sensor | `connector.status` | — |
| Charging state | sensor | `charging.status` | — |

## Prerequisites

- A **Tibber account** (the free tier is sufficient — no energy contract
  required).
- A **vehicle already paired inside the Tibber app** (Tibber's own
  vehicle-pairing flow, independent of Home Assistant).
- **Home Assistant** with [HACS](https://hacs.xyz) installed, version
  2024.1.0 or newer.

## Installation & setup

### 1. Register an OAuth2 client with Tibber (one-time)

Go to [`data-api.tibber.com/clients/manage/`](https://data-api.tibber.com/clients/manage/),
log in with your Tibber account, and create a new client:

- Client name: pick something recognizable, e.g. `Home Assistant - Tibber
  Vehicle`. This is the name **Tibber's own consent screen will show you**
  when you authorize access in step 4 — it has nothing to do with the
  "Name" field you may later give the credential inside Home Assistant
  (that one is purely local to HA's own UI, for telling multiple
  credentials apart, and is never sent to Tibber).
- Scopes: select at least `data-api-homes-read` and `data-api-vehicles-read`.
- Redirect URI: enter exactly **`https://my.home-assistant.io/redirect/oauth`**
  — not your own instance's address, even if it's LAN-only with no public
  URL. This is Home Assistant's standard shared redirect page for OAuth2
  account linking; the actual trip back to your instance happens entirely
  in your browser, so it works regardless of whether your instance is
  reachable from the internet. Full mechanism traced from HA's own source
  code in [`docs/DECISIONS.md`](docs/DECISIONS.md).

Note down the client ID and secret shown after creation — the secret is
only displayed once.

### 2. Install via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Smengerl&repository=ha-tibber-vehicle&category=integration)

Or manually: **HACS → ⋮ → Custom repositories** → add
`https://github.com/Smengerl/ha-tibber-vehicle`, category "Integration".
Then install **Tibber Vehicle** from the store and **restart Home
Assistant** — a first install only becomes fully known to HA (selectable
anywhere in its UI) after a restart.

### 3. Add the Application Credential

Settings → Devices & Services → **Application Credentials** ("OAuth
Anmeldedaten" in the German UI) → Add application credential → select
**Tibber Vehicle** → enter the client ID/secret from step 1. The optional
"Name" field here is separate from step 1's client name — it's used
exclusively inside Home Assistant itself (only shown back to you if you
ever add a second Tibber credential and have to tell them apart), never
sent to Tibber. Something like `Tibber Vehicle` is a fine choice.

This has to happen *after* step 2, not before — the integration dropdown
here only lists domains HA currently has installed and loaded, so "Tibber
Vehicle" isn't selectable until the HACS install (+ restart) has completed.

### 4. Add the integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tibber_vehicle)

Or manually: Settings → Devices & Services → Add Integration → **Tibber
Vehicle**. Either way, this picks up the credential from step 3 and takes
you straight to the OAuth2 consent screen in your browser. Approve access,
and the integration resolves your paired vehicle and creates its device
with the entities listed above.

## Development

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for the dev/test workflow
(local repo → disposable Dockerized HA instance for fast iteration →
`pytest-homeassistant-custom-component` for unit tests → releasing a change
to the real instance) and [`CONTRIBUTING.md`](CONTRIBUTING.md) if you want
to contribute.

Background on why this project exists and how it relates to sibling
projects is in [`docs/CONTEXT.md`](docs/CONTEXT.md).

## License

MIT — see [`LICENSE`](LICENSE).
