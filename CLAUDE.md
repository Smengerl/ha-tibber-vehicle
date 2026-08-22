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
| `README.md` | The feature set, **any step a user needs to actually install/configure this** (Tibber client registration, HACS install, Application Credentials, adding the integration), or project status (scaffold → functional → published) changes. This is the file HACS shows a user browsing/installing the repo — there is no separate "Documentation tab" for HACS integrations the way Supervisor add-ons get one (confirmed against [Presenting your app](https://developers.home-assistant.io/docs/apps/presentation/) and the file layout of the sibling project `goosepaper-addon`, which *is* a Supervisor add-on and does split README/DOCS.md — that split doesn't apply here). Concretely: **installation/setup steps belong here, never only in `docs/DEVELOPMENT.md`** — that mistake happened once already (2026-08-21) and had to be fixed. |
| `docs/CONTEXT.md` | New facts emerge about the Tibber Data API, the VW backend block, `homeassistant-volkswagencarnet`'s status, or how this project relates to `weconnect_mvp` — anything in the "why"/background category. |
| `docs/DECISIONS.md` | A new design/architecture decision is made, or an existing one is revisited/reversed. |
| `docs/DEVELOPMENT.md` | The *developer-facing* workflow changes — local dev loop, testing, CI, versioning mechanics, or how a developer ships a change to the real instance. Never end-user setup steps (see `README.md` row above) — this file is not shown anywhere in Home Assistant's UI. |
| `CONTRIBUTING.md` | The contribution process itself changes (branching/commit conventions, how issues should be reported). |
| `CHANGELOG.md` | Any notable code or behavior change — add an entry under `[Unreleased]` immediately, don't batch it up right before a release. Written for someone using the integration, not a commit-by-commit developer log. |

## How to update — append, don't overwrite

Matching the convention already used in `weconnect_mvp`'s
`TIBBER_API.md`: when a fact changes, **don't silently delete or rewrite**
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
is the reference used for the pre-1.0.0 review (2026-08-24) and should be
the standard yardstick going forward — not just a one-time audit. **When
writing or reviewing code in this repo, check it against Bronze at
minimum, and proactively tell the user when a change introduces a gap
against any tier (a regression on something previously passing, or an
easy win left on the table) rather than noting it silently and moving on.**

### Bronze (the bar this integration should always meet)

| Rule | Requirement | Status as of 2026-08-24 |
|---|---|---|
| `action-setup` | Service actions registered in `async_setup` | N/A — no service actions |
| `appropriate-polling` | Reasonable polling interval | ✅ 5 min (`DEFAULT_UPDATE_INTERVAL_SECONDS`); no documented Tibber-side cadence to tune against, see `docs/DECISIONS.md` |
| `brands` | Branding assets available | ✅ local `custom_components/tibber_vehicle/brand/` |
| `common-modules` | No duplicated logic across modules | ✅ |
| `config-flow-test-coverage` | Full test coverage for the config flow | ❌ **zero test files exist** — `tests/` only has fixture scaffolding, no actual tests. Biggest open gap. |
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
| `test-before-configure` | Validate connectivity before finishing setup | ✅ logically (the vehicle-list call in `async_oauth_create_entry` aborts on failure) — but untested, see `config-flow-test-coverage` |
| `test-before-setup` | Verify init works before completing setup | ✅ logically (`async_config_entry_first_refresh` raises `ConfigEntryNotReady` on failure) — same test-coverage caveat |
| `unique-config-entry` | Can't set up the same account twice | ✅ `_abort_if_unique_id_configured()` keyed on home ids |

### Silver / Gold (aspirational — not required for v1.0.0, but worth knowing what's deliberately deferred)

Full lists in the checklist linked above. Relevant ones already tracked as
deliberate, documented scope boundaries in `docs/DECISIONS.md`: no reauth
flow, no PKCE, no live dynamic-device addition (a vehicle paired in Tibber
after setup needs a reload). Not yet done and not yet decided either way:
`diagnostics.py`, entity/icon translations, a linter/`pyproject.toml`
config. Don't silently start building toward these — if one comes up
naturally, mention it and let the user decide whether it's worth doing now
or staying deferred, same as any other scope decision in this repo.

## Before starting new work in this repo

Read `docs/CONTEXT.md` and `docs/DECISIONS.md` first. If something you're
about to do contradicts either (e.g. reintroducing a loopback-server OAuth2
flow instead of HA's `config_entry_oauth2_flow` helper, or coupling this
integration to `carconnectivity` or `homeassistant-volkswagencarnet`), that
contradiction is worth surfacing explicitly rather than silently going a
different direction — either the doc is stale and needs updating, or the
new approach needs justification added to `docs/DECISIONS.md`.
