# ha-tibber-vehicle

A Home Assistant custom integration (installable via HACS) that reads EV
vehicle data — state of charge, target SoC, estimated range, plug status,
charging status — from the official [Tibber Data API](https://data-api.tibber.com)
(`data-api.tibber.com`), for any vehicle paired inside a Tibber account.

**Status: scaffold only, not yet functional.** This repo was just
bootstrapped (2026-08-21) with the standard HA custom-component boilerplate
and project docs. No OAuth2 flow, coordinator, or sensor logic is
implemented yet — see [`docs/CONTEXT.md`](docs/CONTEXT.md) for the full
background and [`docs/DECISIONS.md`](docs/DECISIONS.md) for the design
decisions already made, before writing any code here.

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

## Development

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for the full dev/test/
deploy workflow (local repo → disposable Dockerized HA instance for fast
iteration → `pytest-homeassistant-custom-component` for unit tests → HACS
custom-repository install onto the real HA instance for live testing).
Nothing here is installed on any real Home Assistant instance yet.

## License

MIT — see [`LICENSE`](LICENSE).
