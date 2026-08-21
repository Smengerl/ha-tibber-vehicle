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

## Before starting new work in this repo

Read `docs/CONTEXT.md` and `docs/DECISIONS.md` first. If something you're
about to do contradicts either (e.g. reintroducing a loopback-server OAuth2
flow instead of HA's `config_entry_oauth2_flow` helper, or coupling this
integration to `carconnectivity` or `homeassistant-volkswagencarnet`), that
contradiction is worth surfacing explicitly rather than silently going a
different direction — either the doc is stale and needs updating, or the
new approach needs justification added to `docs/DECISIONS.md`.
