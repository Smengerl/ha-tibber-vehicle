# Agent instructions for this repo

## Keep the docs in sync with reality — every session, not just at milestones

This project was scaffolded from research done in a Claude Code session
(see `docs/CONTEXT.md`). The docs in `docs/` are the durable memory of *why*
this project looks the way it does — they must stay current, or the next
session (agent or human) re-derives things that are already known, or
worse, acts on stale assumptions (e.g. "the real HA's VW integration is
broken" or "no Tibber connector exists in carconnectivity" — both are
point-in-time facts that could change).

**Update these files as part of the same turn/commit as the change that
makes them stale — don't defer it to "later" or treat it as optional
cleanup:**

| File | Update when... |
|---|---|
| `README.md` | The feature set, **any step a user needs to actually install/configure this** (Tibber client registration, HACS install, Application Credentials, adding the integration), or project status (scaffold → functional → published) changes. This is the file HACS shows a user browsing/installing the repo — there is no separate "Documentation tab" for HACS integrations the way Supervisor add-ons get one (confirmed against [Presenting your app](https://developers.home-assistant.io/docs/apps/presentation/)). Concretely: **installation/setup steps belong here, never only in `docs/DEVELOPMENT.md`** — that mistake happened once already (2026-08-21) and had to be fixed. |
| `docs/CONTEXT.md` | New facts emerge about the Tibber Data API, the VW backend block, or `homeassistant-volkswagencarnet`'s status — anything in the "why"/background category. |
| `docs/DECISIONS.md` | A new design/architecture decision is made, or an existing one is revisited/reversed. |
| `docs/DEVELOPMENT.md` | The *developer-facing* workflow changes — local dev loop, testing, CI, versioning mechanics, or how a developer ships a change to the real instance. Never end-user setup steps (see `README.md` row above) — this file is not shown anywhere in Home Assistant's UI. |
| `docs/TESTING.md` | The test strategy/structure changes, a new test file or fixture shape is added, or a planned test case gets written (or deliberately dropped) — keep the case list matched to what actually exists in `tests/`. |
| `CONTRIBUTING.md` | The contribution process itself changes (branching/commit conventions, how issues should be reported). |
| `CHANGELOG.md` | Any notable code or behavior change — add an entry under `[Unreleased]` immediately, don't batch it up right before a release. Written for someone using the integration, not a commit-by-commit developer log. |

## How to update — append, don't overwrite

When a fact changes, **don't silently delete or rewrite**
the old text if it had reasoning attached. Either:
- correct it in place with a brief note of what changed and why (for
  small, unambiguous corrections), or
- append a new dated entry rather than rewriting history (for anything
  where the *history* of what was believed and why is itself useful later —
  e.g. `docs/DECISIONS.md` entries, or if a session log is ever added here).

Never leave a doc describing a decision or state that the code has since
moved away from — an inaccurate `docs/DECISIONS.md` is worse than none.

## Release & versioning policy

Version format: `major.minor.bugfix` (`custom_components/tibber_vehicle/manifest.json`'s
`"version"` field and git tags — see `docs/DEVELOPMENT.md`'s "Versioning"
section for the mechanics of actually bumping/tagging). This section is
the *policy* for which number to bump and whether to ask first; treat it
the same as the rest of this file — don't bump a version without
following it.

- **Bugfix** (the third number): a single, small fix — typically one
  commit's worth of change. No `CHANGELOG.md` entry is required for what a
  bugfix bump actually contains. **Always ask the user before bumping** —
  per commit, confirm whether *this* commit should increment the bugfix
  number. Never bump it unasked.
- **Minor** (the second number): used whenever a new feature is
  introduced. Gets a brief `CHANGELOG.md` entry under the new version
  heading — concise, not the full commit-level detail. If it's unclear
  whether a change is substantial enough to warrant a minor bump (versus
  staying within an unbumped bugfix-level change), **ask the user for
  confirmation** rather than deciding unilaterally.
- **Major** (the first number): comprehensive changes — gets a thorough
  `CHANGELOG.md` entry, more detail than a minor bump's. **Only the user
  bumps major, and only at their own explicit request.** Don't propose,
  suggest, or perform a major version bump on your own initiative under
  any circumstance — not even if a change seems large enough to warrant
  one. Surface that you think a change is major-sized if genuinely
  relevant, but the decision to actually bump stays with the user.

## HA Integration Quality Scale — the bar to measure code against

Home Assistant's official [Integration Quality Scale checklist](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist)
(four tiers: Bronze → Silver → Gold → Platinum, each a superset of the one
below) is the reference used for the pre-1.0.0 review (2026-08-24) and
should be the standard yardstick going forward — not just a one-time
audit.

**Target policy (the user's explicit call, 2026-08-25 — treat as settled,
don't re-litigate without asking):**
- **Bronze: mandatory, always.** Every rule below must stay ✅ or N/A. A
  change that regresses a previously-passing Bronze rule is a blocker to
  fix in the same change, not something to note and move past.
- **Silver: desirable, not mandatory.** Worth closing a gap opportunistically
  when it's cheap or comes up naturally while touching related code, but
  not a blocker for shipping or releasing.
- **Gold: optional.** Nice-to-have at most. Don't invest deliberate effort
  here unless the user asks, or a rule happens to be satisfied as a
  side-effect of other work (e.g. `entity-translations` was, by the
  translations feature).
- **Platinum: not tracked at all currently** — listed at the very bottom
  for completeness only, no per-rule status kept.

**When writing or reviewing code in this repo, always check it against
Bronze, and proactively tell the user when a change introduces a gap
against any tier** (a regression on something previously passing, or an
easy win left on the table) rather than noting it silently and moving on —
this applies even to Gold, since "optional" means "not required", not
"don't mention it".

### Bronze (the bar this integration should always meet)

| Rule | Requirement | Status as of 2026-08-24 |
|---|---|---|
| `action-setup` | Service actions registered in `async_setup` | N/A — no service actions |
| `appropriate-polling` | Reasonable polling interval | ✅ 5 min (`DEFAULT_UPDATE_INTERVAL_SECONDS`); no documented Tibber-side cadence to tune against, see `docs/DECISIONS.md` |
| `brands` | Branding assets available | ✅ local `custom_components/tibber_vehicle/brand/` |
| `common-modules` | No duplicated logic across modules | ✅ |
| `config-flow-test-coverage` | Full test coverage for the config flow | ✅ **closed 2026-08-24** — all 19 planned cases across `tests/test_{config_flow,api,init,sensor}.py` implemented and passing, running in CI. Found and fixed two real bugs in the process (see `docs/DECISIONS.md`): `missing_credentials` vs `missing_configuration`, and a wrong exception type (`ImplementationUnavailableError` vs the `ValueError` this HA version actually raises) that was silently swallowing a retry-worthy setup failure into a harder `SETUP_ERROR` state. |
| `config-flow` | Set up via UI, correct `ConfigEntry` data/options use | ✅ |
| `dependency-transparency` | External deps documented | ✅ — none beyond aiohttp (bundled with HA) |
| `docs-actions`/`docs-triggers`/`docs-conditions` | Document provided actions/triggers/conditions | N/A — none provided |
| `docs-high-level-description` | Explain the brand/service being integrated | ✅ README intro paragraph (restructured 2026-08-23 to match common HA-integration README conventions; no longer a dedicated "Why this exists" heading) |
| `docs-installation-instructions` | Step-by-step install docs | ✅ README "Installation" + "Setup" (split 2026-08-23 from the former single "Installation & setup" section) |
| `docs-removal-instructions` | Removal docs | ✅ README "Removal" (added 2026-08-24, was missing before) |
| `entity-event-setup` | Entity subscriptions at the right lifecycle phase | N/A — coordinator polling, not event-driven |
| `entity-unique-id` | Entities have a unique ID | ✅ |
| `has-entity-name` | `_attr_has_entity_name = True` | ✅ (`entity.py`) |
| `runtime-data` | Use `ConfigEntry.runtime_data` | ✅ |
| `test-before-configure` | Validate connectivity before finishing setup | ✅ the vehicle-list call in `async_oauth_create_entry` aborts on failure, now covered by `test_abort_connection_error`/`test_abort_no_vehicle_found` in `tests/test_config_flow.py` |
| `test-before-setup` | Verify init works before completing setup | ✅ `async_config_entry_first_refresh` raises `ConfigEntryNotReady` on failure, covered by `tests/test_init.py` |
| `unique-config-entry` | Can't set up the same account twice | ✅ `_abort_if_unique_id_configured()` keyed on home ids |

### Silver (desirable — close gaps opportunistically, not a blocker)

| Rule | Requirement | Status as of 2026-08-25 |
|---|---|---|
| `action-exceptions` | Service actions raise exceptions on failure | N/A — no service actions |
| `config-entry-unloading` | Support config entry unloading | ✅ `async_unload_entry` in `__init__.py` |
| `docs-configuration-parameters` | Document all configuration options | N/A — no configurable options beyond the one-time OAuth2 setup, which README already documents |
| `docs-installation-parameters` | Document all installation parameters | ✅ README "Prerequisites" (scopes, redirect URI, client registration steps) |
| `entity-unavailable` | Mark entity unavailable when appropriate | ✅ fixed 2026-08-24 — `TibberVehicleEntity.available` also requires `self._device_id in self.coordinator.data`, not just the whole coordinator's `last_update_success` |
| `integration-owner` | Has a codeowner | ✅ `manifest.json`'s `"codeowners": ["@Smengerl"]` |
| `log-when-unavailable` | Log when a connection is lost/restored | 🟡 not explicitly implemented in this integration's own code — relies entirely on `DataUpdateCoordinator`'s built-in logging, never verified that it actually covers this |
| `parallel-updates` | `PARALLEL_UPDATES` specified | ✅ `sensor.py`, set to `0` (coordinator-driven, no per-entity I/O to throttle) |
| `reauthentication-flow` | Reauthentication available via the UI | ❌ known, deliberately deferred gap — see `docs/DECISIONS.md`'s "Login flow implementation" |
| `test-coverage` | Above 95% test coverage | ❌ not measured — 20 tests exist (`docs/TESTING.md`'s full planned case list, all passing), but coverage % has never actually been run/checked |

### Gold (optional — nice-to-have at most, don't invest effort unasked)

| Rule | Requirement | Status as of 2026-08-25 |
|---|---|---|
| `devices` | Integration creates devices | ✅ one device per paired vehicle |
| `diagnostics` | Implements diagnostics | ❌ no `diagnostics.py` |
| `discovery` | Devices can be discovered | N/A — cloud-polling integration against a Tibber account, nothing on the local network to discover |
| `discovery-update-info` | Discovery info updates network details | N/A — same reason as `discovery` |
| `docs-data-update` | Document how data is updated | ✅ README (5-minute polling; "Data freshness depends on Tibber, not just this integration") |
| `docs-examples` | Provide automation examples | ❌ none in README |
| `docs-known-limitations` | Document known limitations | ✅ README "Known Issues / Limitations" |
| `docs-supported-devices` | Document known supported/unsupported devices | 🟡 partial — README says "for every vehicle paired inside your Tibber account, regardless of make" but also flags (as of the 2026-08-25 review) that only a Volkswagen has actually been verified end-to-end |
| `docs-supported-functions` | Document supported functionality | ✅ README "Entities" section, one subsection per sensor |
| `docs-troubleshooting` | Provide troubleshooting information | ❌ none dedicated — only the in-the-moment config-flow abort messages |
| `docs-use-cases` | Describe use cases | ❌ none |
| `dynamic-devices` | Devices added after integration setup, without a reload | ❌ known, deliberately deferred gap — a vehicle paired in Tibber after setup needs a manual reload (README "Known Issues") |
| `entity-category` | Entities assigned an appropriate `EntityCategory` | ✅ correctly left unset — all 5 entities are primary state, none are diagnostic/config-category candidates |
| `entity-device-class` | Use device classes where possible | ✅ `battery`/`distance` set where a matching class exists; `charging_state`/`plug_status` have no corresponding HA device class to use instead |
| `entity-disabled-by-default` | Disable less-popular/noisy entities by default | N/A — all 5 entities are core to the integration's purpose, none are noisy or niche |
| `entity-translations` | Entities have translated names | ✅ **closed 2026-08-24** (as a side effect of the translations feature, not a deliberate Gold push) — `translation_key` on every `SensorEntityDescription` + `translations/{en,de,fr,es}.json` |
| `exception-translations` | Exception messages are translatable | ❌ exceptions raised as plain strings — no `translation_domain`/`translation_key` |
| `icon-translations` | Entities implement icon translations | ❌ icons set directly via `icon="mdi:..."` on each `SensorEntityDescription`, no `icons.json` |
| `reconfiguration-flow` | Integration has a reconfigure flow | ❌ none |
| `repair-issues` | Repair issues/flows used when user intervention is needed | ❌ none |
| `stale-devices` | Stale devices are removed automatically | ❌ known, deliberately deferred gap — a vehicle removed from Tibber leaves an unavailable-but-undeleted device behind until a manual reload (README "Known Issues") |

### Platinum (not tracked — listed only for completeness)

`async-dependency`, `inject-websession`, `strict-typing`. No per-rule
status kept for this tier; not part of the current policy.

### CI must stay green — always, especially the `hacs` job

`.github/workflows/validate.yml`'s three jobs (`hassfest`, `hacs`,
`pytest`) must all pass on every push. Treat a red run as a blocker to fix
in the same change, not something to notice in passing and defer. The
`hacs` job specifically runs `hacs/action`'s full validation — 9 checks
(topics, description, license, archived status, issues, repository
information, `hacs.json`, `manifest.json`, brand assets) — and that's not
just a nice-to-have: it's the actual automated bar for HACS
default-repository eligibility, the same checks a `hacs/default`
submission would be judged against. It was red on **every single push**
from this repo's first commit until the missing brand assets were found
purely by chance during an unrelated pre-1.0.0 review (2026-08-24) —
nobody had actually looked at the CI status before then. After every push
that could plausibly affect any of the 9 checks, verify with
`gh run list`/`gh run view` rather than assuming green.

## Known pitfalls — re-check these when touching related code

Found during actual reviews (`docs/DECISIONS.md` has the full story for
each) — not covered by the generic Quality Scale checklist above, so
they'd otherwise only get caught again by chance. Check the matching row
whenever you touch the trigger, not just when reviewing on request:

| Trigger | What to check | Why |
|---|---|---|
| Adding any new Python language feature anywhere in `custom_components/tibber_vehicle/*.py` (new syntax, not just new logic — e.g. another PEP 695 `type` statement, a `match` statement, new stdlib-version-gated API) | Confirm it's available on the Python version Home Assistant actually ships for `hacs.json`'s declared `"homeassistant"` minimum, not just whatever Python this dev environment happens to run. `type` statements already forced `2024.4.0` as the floor (HA didn't require Python 3.12 until that release) — a stricter feature could force it higher again. | `hacs.json` declared `2024.1.0` while the code required Python 3.12 (`2024.4.0`+) — would have crashed with a `SyntaxError` on import for anyone still on an in-range-but-actually-incompatible version. |
| Adding a new entity platform or a new entity base class (anything that isn't a `TibberVehicleSensor` subclassing `TibberVehicleEntity`) | Make sure it still goes through `TibberVehicleEntity` (or otherwise reimplements its `available` override) — don't inherit `CoordinatorEntity` directly and assume the default `available` is enough. | `CoordinatorEntity`'s default `available` only checks the whole coordinator's `last_update_success`, not whether *this* vehicle's `device_id` is still in `coordinator.data`. A new platform built without going through `TibberVehicleEntity` would silently reintroduce the "removed vehicle stuck at `unknown` forever" bug already fixed once. |
| Writing a docstring/comment that cites *why* something is true or *where* a fact was confirmed | Cite something a reader of this public repo can actually reach (a section of `docs/*.md` in this repo, an official Tibber/HA doc URL, a specific commit) — never an external private/inaccessible project as the source of record. | `api.py`/`const.py`/`config_flow.py` cited `weconnect_mvp` (a private sibling project on the original maintainer's machine) as where facts were confirmed — a dead-end reference for anyone else reading this code. |
| Any change to `manifest.json`, `hacs.json`, the GitHub repo's topics/description, or the brand assets under `custom_components/tibber_vehicle/brand/` | Push, then actually check the `hacs` CI job (`gh run list`/`gh run view`) — don't assume it's still green. | This is exactly the class of change that silently broke the `hacs` job for this repo's entire history (see "CI must stay green" above) — it's cheap to re-check and expensive to leave broken unnoticed. |

## Before starting new work in this repo

Read `docs/CONTEXT.md` and `docs/DECISIONS.md` first. If something you're
about to do contradicts either (e.g. reintroducing a loopback-server OAuth2
flow instead of HA's `config_entry_oauth2_flow` helper, or coupling this
integration to `carconnectivity` or `homeassistant-volkswagencarnet`), that
contradiction is worth surfacing explicitly rather than silently going a
different direction — either the doc is stale and needs updating, or the
new approach needs justification added to `docs/DECISIONS.md`.
