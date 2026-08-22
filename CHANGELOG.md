# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries
describe what changed for someone installing/using this integration, not a
full technical walkthrough of every commit — link the actual commit/PR for
that level of detail instead of writing it out here.

## [Unreleased]

### Added
- Initial release: log in with your Tibber account once, and every vehicle
  paired to it becomes its own Home Assistant device — each exposing every
  vehicle data point the Tibber Data API offers: battery level, battery
  target charge level, electric range, plug status, and charging state.

### Changed
- Restructured `README.md` to match common HA-integration conventions
  (separate Installation/Setup sections, a per-entity reference section,
  a Known Issues/Limitations section, reference-style links) — no
  functional change, documentation only.

### Fixed
- If the OAuth2 login session became unusable in a specific way (no
  implementation registered for the stored credential), the integration
  could land in a stuck error state on startup instead of automatically
  retrying. Fixed by catching the actual exception type Home Assistant
  raises for this.
