# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries
describe what changed for someone installing/using this integration, not a
full technical walkthrough of every commit — link the actual commit/PR for
that level of detail instead of writing it out here.

## [Unreleased]

### Changed
- Replaced the placeholder README screenshot with a real one, cropped to
  the actual device page (no more surrounding browser chrome). Added two
  more screenshots showing what an entity's history looks like — a
  graph for `battery_level` and a state timeline for `plug_status` — next
  to their respective entity descriptions.

## [1.0.0] - 2026-08-25

First stable release. Reads battery level, target charge level, electric
range, plug status, and charging state from any vehicle paired inside a
Tibber account, via Tibber's official OAuth2 Data API — a working
alternative for Volkswagen Group vehicles (VW, Audi, Cupra, Seat, Skoda)
now that direct third-party access to VW's own backend is blocked. See
`README.md` for the full setup walkthrough and `docs/DECISIONS.md` for
the design reasoning behind every choice below.

### Added
- Initial release: log in with your Tibber account once, and every vehicle
  paired to it becomes its own Home Assistant device — each exposing every
  vehicle data point the Tibber Data API offers: battery level, battery
  target charge level, electric range, plug status, and charging state.
- Sensor names now follow your Home Assistant instance's language —
  German, French, and Spanish translations added (English remains the
  fallback for any other language). Previously every entity name
  ("Battery level", "Electric range", etc.) always showed in English
  regardless of your HA language setting.

### Changed
- Restructured `README.md` to match common HA-integration conventions
  (separate Installation/Setup sections, a per-entity reference section,
  a Known Issues/Limitations section, reference-style links) — no
  functional change, documentation only.
- `README.md` documentation pass from a full end-user review: corrected
  the listed minimum Home Assistant version (was still 2024.1.0, out of
  sync with the actual 2024.4.0 requirement fixed below); moved the
  "read-only" note up to the introduction instead of only appearing in
  Known Issues; added notes on multi-Tibber-account support, that the
  polling interval isn't user-configurable, that a removed vehicle's
  device needs a manual reload to clean up, and that only a Volkswagen
  vehicle has been verified end-to-end so far; and fixed several
  `docs/DECISIONS.md` links that pointed at the top of that file instead
  of the relevant section.

### Fixed
- If the OAuth2 login session became unusable in a specific way (no
  implementation registered for the stored credential), the integration
  could land in a stuck error state on startup instead of automatically
  retrying. Fixed by catching the actual exception type Home Assistant
  raises for this.
- The minimum supported Home Assistant version listed for this
  integration was lower than what the code actually requires; corrected
  so installing on a genuinely unsupported (too old) Home Assistant
  version is refused up front instead of failing with a confusing error.
- If a vehicle was unpaired from your Tibber account, its sensors kept
  showing their last known value indefinitely instead of becoming
  unavailable. They now correctly show as unavailable.
