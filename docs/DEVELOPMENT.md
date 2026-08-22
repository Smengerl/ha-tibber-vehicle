# Development workflow

## 1. Fast local iteration — disposable Dockerized HA instance

Don't touch the real Home Assistant Green for day-to-day development. Run a
throwaway instance locally with this repo's integration bind-mounted in:

```bash
./scripts/dev-instance.sh
```

(wraps the `docker run` shown below — see `scripts/dev-instance.sh`). Opens
at `http://localhost:8123`. State persists in `dev-config/` between runs
(gitignored); delete that folder to start clean. After editing files under
`custom_components/tibber_vehicle/`, reload the integration from HA's UI
(Settings → Devices & Services → the integration → ⋮ → Reload) — no
container restart needed for most changes.

## 2. Unit tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

Uses `pytest-homeassistant-custom-component` (the same test framework
`homeassistant-volkswagencarnet` itself uses) — tests run against a fixture
HA core instance in-process, no Docker needed. This is the fastest feedback
loop for coordinator/config-flow/OAuth-refresh logic; prefer it over the
Docker loop where a real UI interaction isn't what's being tested.

See [`docs/TESTING.md`](TESTING.md) for the actual test concept — which
files to add, what each should cover, and in what order — rather than
figuring that out from scratch each time.

## 3. Releasing a change to the real Home Assistant instance

The real instance is a **Home Assistant Green** (HAOS appliance) — no direct
root filesystem access. Never edit its `custom_components/` over Samba/SSH
as the primary workflow (see `docs/DECISIONS.md` for why).

For the one-time first-install walkthrough (registering the Tibber OAuth2
client, HACS custom repository, Application Credentials, adding the
integration) see [`README.md`](../README.md)'s "Installation & setup" —
that's the file HACS actually shows a user, so any step someone needs to
follow to get this running belongs there, not here. This section is only
about getting a *code change* from a local commit onto an instance that
already has the integration installed:

1. Commit and push to this repo's GitHub remote.
2. Bump `custom_components/tibber_vehicle/manifest.json`'s `"version"` and
   add a `CHANGELOG.md` entry (see "Versioning" below) — HACS's update
   mechanism is version-driven, not content-diffing.
3. On the target instance, HACS will offer an update for **Tibber Vehicle**
   (may need a manual store refresh depending on HACS's own cache cycle).
   Installing it does not require repeating the Application
   Credentials/OAuth2 steps — those are tied to the config entry, not the
   installed code version.

## 4. Versioning

Mechanics only — for the policy on *which* number to bump, whether a
`CHANGELOG.md` entry is needed, and when to ask the user first, see
`CLAUDE.md`'s "Release & versioning policy".

Standard `major.minor.bugfix` git tags (`v0.1.0`, `v0.1.1`, …). Keep
`custom_components/tibber_vehicle/manifest.json`'s `"version"` field in sync
with the tag being released.

## 5. CI

`.github/workflows/validate.yml` runs `hassfest` (HA's own manifest/schema
validator) and the HACS repository validator on every push — both are
boilerplate checks any HACS-listed integration is expected to pass, not
project-specific logic.
