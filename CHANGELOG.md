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
- No functional code yet — `config_flow.py`, `coordinator.py`, `sensor.py`
  are stubs with `NotImplementedError` / `TODO` markers.
