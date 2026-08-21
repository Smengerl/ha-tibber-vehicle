# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
- No functional code yet — `config_flow.py`, `coordinator.py`, `sensor.py`
  are stubs with `NotImplementedError` / `TODO` markers.

### Fixed
- `docs/DEVELOPMENT.md` install order: Application Credentials can only be
  added *after* the HACS install (+ restart) — the integration dropdown on
  that page only lists domains HA currently has loaded. Confirmed hands-on
  on the real instance: attempting to add credentials before install left
  "Tibber Vehicle" unselectable, since it wasn't a known domain yet.
