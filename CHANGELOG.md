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
