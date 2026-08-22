# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries
describe what changed for someone installing/using this integration, not a
full technical walkthrough of every commit — link the actual commit/PR for
that level of detail instead of writing it out here.

## [Unreleased]

### Added
- Local brand assets (`custom_components/tibber_vehicle/brand/icon.png`,
  `icon@2x.png`) so the integration shows a proper icon instead of a
  generic placeholder, in Home Assistant's UI (2026.3+) and in the HACS
  default-listing validation (`hacs/action`'s brands check). Same teal as
  Tibber's own icon, with an outlined lightning bolt (Tibber's style) next
  to a stylized vehicle silhouette. Submitting to the central
  `home-assistant/brands` repo (needed for older HA versions to see an
  icon at all) is deferred — see `docs/DECISIONS.md`.
- "Active Installations" badge in `README.md`, sourced live from Home
  Assistant's own opt-in analytics
  (`analytics.home-assistant.io/custom_integrations.json`) via shields.io's
  dynamic JSON badge. Will read 0/invalid until other users install this
  and have analytics reporting enabled — expected for a newly-public repo.

### Fixed
- Confirmed working end-to-end on a real Home Assistant instance
  (2026-08-23): OAuth2 login against Tibber, vehicle resolution, and all
  five entities populating correctly. Removed the "not yet verified"
  status note from `README.md` accordingly.
- The CI "Validate" workflow had been failing on every single push since
  the first commit (`hacs/action`'s brands check — fixed by the local
  brand assets above). Also fixed: `manifest.json`'s
  `codeowners`/`documentation`/`issue_tracker` and `const.py`'s
  `USER_AGENT` all pointed to `github.com/simongerlach` instead of the
  actual repo owner `Smengerl` — broken links, and an inaccurate
  User-Agent sent on every Tibber API request. Both found and fixed while
  checking overall HACS-readiness; CI is green as of this entry.

### Changed
- Restructured `README.md` to follow common HA-integration conventions:
  badges (CI status, HACS, license), a short motivation paragraph, a
  screenshot placeholder (`docs/images/screenshot.svg` — replace with a
  real one once verified live), a dedicated Prerequisites section, and
  "Open your Home Assistant instance" buttons for both the HACS
  repository (step 2) and starting the config flow directly (step 4).
- Entity names, icons, units, and device classes now match the equivalent
  entity in `robinostlund/homeassistant-volkswagencarnet` (Battery level,
  Battery target charge level, Electric range, Charging state) instead of
  the generic placeholder names from the initial implementation — so
  dashboards/history built against either integration use consistent
  entity identity. Full comparison table and reasoning (including the
  deliberate deviations from a blind 1:1 copy) in `docs/DECISIONS.md`.
- The plug-status entity (`connector.status`) briefly changed type to a
  `binary_sensor` (matching VW Connect's `external_power`), then was
  reverted back to a plain sensor named "Plug status" — collapsing
  Tibber's `unknown` value into `binary_sensor`'s generic
  unavailable/unknown state lost visible distinction from `disconnected`,
  which wasn't wanted. See `docs/DECISIONS.md` for the full back-and-forth.

### Fixed
- `README.md` step 1 didn't say to give the Tibber OAuth2 client a
  recognizable name. Added: that name is what Tibber's own consent screen
  actually shows during login (step 4) — confirmed against HA core's
  `application_credentials` source, where the "Name" field on HA's own
  Application Credential form only labels HA's local "pick implementation"
  step and is never sent to Tibber. Easy to mix the two up; a prior version
  of this guidance (given in chat, not yet written down) had it backwards.
- `README.md` step 3 now also covers the complementary point: the optional
  "Name" field on HA's own Application Credential form is purely local to
  Home Assistant (only matters if a second Tibber credential is ever
  added), so something like `Tibber Vehicle` is fine there.

### Changed
- The GitHub repository was switched from private to public (2026-08-22).
  Reason: HACS categorically cannot install from private repositories
  ("Private GitHub repositories can not be used with HACS at all", per
  HACS's own FAQ) — there is no token-based workaround. Confirmed no
  secrets/tokens/private network details were ever tracked in git before
  flipping visibility. The `README.md` install steps (HACS custom
  repository) now work as written; they didn't need any content change,
  only the repo's visibility did.

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
