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

## 3. Deploying to the real Home Assistant instance

The real instance is a **Home Assistant Green** (HAOS appliance) — no direct
root filesystem access. Never edit its `custom_components/` over Samba/SSH
as the primary workflow (see `docs/DECISIONS.md` for why).

Once a change is committed and pushed to this repo's GitHub remote:

1. In HACS on the real instance → **Custom repositories** → add this repo's
   URL, category "Integration" (only needed once).
2. Install / update `tibber_vehicle` from HACS like any other custom
   integration — same path `volkswagencarnet` already uses there, including
   its own update-tracking entity.
3. Configure via Settings → Devices & Services → Add Integration →
   "Tibber Vehicle" → complete the OAuth2 consent in the browser.

## 4. Versioning

Standard semantic-version git tags (`v0.1.0`, `v0.2.0`, …). Keep
`custom_components/tibber_vehicle/manifest.json`'s `"version"` field in sync
with the tag being released. Record notable changes in `CHANGELOG.md`
(Keep a Changelog format) before tagging.

## 5. CI

`.github/workflows/validate.yml` runs `hassfest` (HA's own manifest/schema
validator) and the HACS repository validator on every push — both are
boilerplate checks any HACS-listed integration is expected to pass, not
project-specific logic.
