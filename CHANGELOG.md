# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries
describe what changed for someone installing/using this integration, not a
full technical walkthrough of every commit — link the actual commit/PR for
that level of detail instead of writing it out here.

## [Unreleased]

### Added
- Project scaffold: repo structure, HACS/manifest boilerplate, dev
  tooling (`pytest-homeassistant-custom-component`, disposable Docker dev
  instance script), CI validation workflow.
- `docs/CONTEXT.md`, `docs/DECISIONS.md`, `docs/DEVELOPMENT.md` — full
  background (VW backend block, why Tibber, relation to `weconnect_mvp`)
  and design decisions, written before any real implementation.
- `CLAUDE.md` — instructs future sessions to keep `docs/` in sync as new
  facts/decisions emerge, instead of letting them go stale.
- `application_credentials.py` (+ matching `strings.json`/
  `translations/en.json` entries) — required for "Tibber Vehicle" to
  appear at all on Settings > Devices & Services > Application Credentials
  ("OAuth Anmeldedaten"); was missing from the initial scaffold.
- **Update 2026-08-21:** the line above is now stale — see the new "Added"
  entry below. `config_flow.py`/`coordinator.py`/`sensor.py` are no longer
  stubs.
- The OAuth2 login flow, vehicle resolution, polling, and all five sensor
  entities are now implemented — modeled directly on Home Assistant core's
  Spotify integration (`extra_authorize_data`, `async_oauth_create_entry`,
  `entry.runtime_data`). New `api.py` — a thin Tibber Data API client.
  Verified by import-checking every module against a real `homeassistant`
  install; **not yet verified with a live OAuth2 round-trip against
  Tibber or inside a booted HA instance** — see `docs/DECISIONS.md`'s
  "Login flow implementation" for the full detail and known, deliberately
  deferred gaps (no PKCE, no reauth, single-vehicle-only).
- New `entity.py`: all five sensors now group under one HA **device**
  representing the paired vehicle (manufacturer/model shown, VIN as
  identifier) instead of appearing as five ungrouped entities — this had
  been missed in the first implementation pass.

### Fixed
- `docs/DEVELOPMENT.md` install order: Application Credentials can only be
  added *after* the HACS install (+ restart) — the integration dropdown on
  that page only lists domains HA currently has loaded. Confirmed hands-on
  on the real instance: attempting to add credentials before install left
  "Tibber Vehicle" unselectable, since it wasn't a known domain yet.
- Moved the installation & setup walkthrough (Tibber client registration,
  HACS install, Application Credentials, adding the integration) from
  `docs/DEVELOPMENT.md` into `README.md`, where HACS actually shows it to
  users — unlike a Supervisor add-on, a HACS integration has no separate
  "Documentation" tab, so `README.md` is the only user-facing surface.
  Added `CONTRIBUTING.md` for contributor guidelines, split out from what
  had been developer-only content mixed into `docs/DEVELOPMENT.md`.
- `README.md`'s status callout was inaccurate ("ends at step 5" - there are
  only 4 steps) and vague about where following the install steps today
  actually fails. Corrected: steps 1-3 work as described; step 4 fails
  immediately (before Tibber's login page even loads), because
  `config_flow.py`'s `extra_authorize_data` deliberately raises
  `NotImplementedError`.
- `docs/DECISIONS.md` was missing where OAuth2 tokens actually get stored
  once implemented - added: directly in the config entry's own
  `data["token"]`, persisted by Home Assistant core itself
  (`.storage/core.config_entries`), not a file this integration manages.
