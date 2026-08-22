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
