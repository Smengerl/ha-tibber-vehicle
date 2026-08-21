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
| `docs/CONTEXT.md` | New facts emerge about the Tibber Data API, the VW backend block, `homeassistant-volkswagencarnet`'s status, or how this project relates to `weconnect_mvp` — anything in the "why"/background category. |
| `docs/DECISIONS.md` | A new design/architecture decision is made, or an existing one is revisited/reversed. |
| `docs/DEVELOPMENT.md` | The dev/test/deploy workflow itself changes (e.g. a different local test setup, a new CI check, a changed HACS install process). |
| `CHANGELOG.md` | Any notable code or behavior change — add an entry under `[Unreleased]` immediately, don't batch it up right before a release. |
| `README.md` | The feature set, install instructions, or project status (scaffold → functional → published) changes. |

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
