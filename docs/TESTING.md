# Test concept

Written 2026-08-24 to close this project's single biggest Bronze
quality-scale gap (`CLAUDE.md`'s checklist: `config-flow-test-coverage` —
currently zero test files exist beyond fixture scaffolding). This is the
concept/plan; it does not itself contain the test code. Update this file
whenever the test structure or strategy changes, same as any other
`docs/*.md` file per `CLAUDE.md`.

## Framework and building blocks (all verified importable, 2026-08-24)

`pytest-homeassistant-custom-component` (already in `requirements_test.txt`)
supplies everything needed — no additional dependency required:

| Building block | Import path | Purpose |
|---|---|---|
| `MockConfigEntry`, `load_fixture` | `pytest_homeassistant_custom_component.common` | Create a fake config entry; load JSON fixture files from `tests/fixtures/` |
| `AiohttpClientMocker` | `pytest_homeassistant_custom_component.test_util.aiohttp` | Intercepts every request made through `async_get_clientsession(hass)` — this is how both Tibber's token endpoint *and* our own `api.py` calls get mocked, without mocking our own classes |
| `ClientSessionGenerator` | `pytest_homeassistant_custom_component.typing` | Type for the `hass_client_no_auth` fixture |
| `_encode_jwt` | `homeassistant.helpers.config_entry_oauth2_flow` | Builds the `state` value needed to simulate the OAuth external-step callback |
| Fixtures: `aioclient_mock`, `hass_client_no_auth`, `current_request_with_host`, `enable_custom_integrations` | registered by the plugin, no import needed | see usage below |

The concrete pattern (OAuth2 config flow tests) is modeled directly on
`homeassistant/components/spotify/{conftest,test_config_flow}.py` in HA
core — fetched and read in full during planning, not reconstructed from
memory, since this is exactly the reference this project's actual code
already follows. Key shape:

```python
result = await hass.config_entries.flow.async_init(
    DOMAIN, context={"source": SOURCE_USER}
)
state = config_entry_oauth2_flow._encode_jwt(
    hass, {"flow_id": result["flow_id"], "redirect_uri": "https://example.com/auth/external/callback"},
)
client = await hass_client_no_auth()
await client.get(f"/auth/external/callback?code=abcd&state={state}")

aioclient_mock.post("https://thewall.tibber.com/connect/token", json={...})
aioclient_mock.get("https://data-api.tibber.com/v1/homes", json={...})
aioclient_mock.get("https://data-api.tibber.com/v1/homes/HOME1/devices", json={...})

result = await hass.config_entries.flow.async_configure(result["flow_id"])
assert result["type"] is FlowResultType.CREATE_ENTRY
```

Unlike Spotify (which mocks its whole `SpotifyClient` class), we mock at
the **HTTP level** via `aioclient_mock` for `api.py`-related calls — our
client is thin enough that this exercises our own retry/parsing/dedup
logic for free, instead of assuming it away.

## Fixture data

New `tests/fixtures/` directory, JSON files matching the *confirmed live*
response shapes documented in `docs/CONTEXT.md` §3 — not invented shapes:

- `homes.json` — `{"homes": [{"id": "home-1"}]}`
- `devices_one_vehicle.json` / `devices_two_vehicles.json` —
  `{"devices": [...]}`, each device with `id`/`externalId`/`info`
- `device_detail.json` — full shape including `capabilities`, one variant
  per test scenario needed (all five capabilities present; one with a
  missing/null capability; one with an unexpected/unknown status string)

Reused across `test_config_flow.py`, `test_init.py`, `test_sensor.py` —
one source of truth per shape, no copy-pasted inline dicts drifting apart.

## Test files and cases

### `tests/test_config_flow.py` — the Bronze-blocking priority — ✅ done (2026-08-24), all 6 passing

1. `test_abort_if_no_credentials` — no Application Credential registered →
   abort. **Turned out to be `missing_credentials`, not
   `missing_configuration`** as originally assumed here — see
   `docs/DECISIONS.md`'s "First `tests/test_config_flow.py` run" entry for
   why, found by actually running this test.
2. `test_full_flow_single_vehicle` — one home, one vehicle →
   `CREATE_ENTRY`; `unique_id` is the home-id set; title is the vehicle's
   name.
3. `test_full_flow_multiple_vehicles` — two vehicles under the account →
   `CREATE_ENTRY`; title lists both names.
4. `test_abort_no_vehicle_found` — homes exist, devices list empty →
   abort `no_vehicle_found`.
5. `test_abort_connection_error` — Tibber API call fails (500) during
   resolution → abort `connection_error`.
6. `test_abort_if_account_already_configured` — linking the same
   home-id set twice → abort `already_configured`.

Needed one addition beyond what this plan anticipated: a root
`pyproject.toml` with `[tool.pytest.ini_options]` `asyncio_mode = "auto"`
— without it, `pytest-asyncio` defaults to strict mode and every async
test errors out before even running (not a test-logic problem, a missing
one-line project config). Also worth knowing going forward: don't
hand-assert exact HA abort-reason strings in a test plan without actually
running it once — see finding 1 above.

### `tests/test_api.py` — the retry/backoff/dedup logic added during the pre-1.0.0 review

7. `test_get_homes_and_devices_happy_path`.
8. `test_async_get_all_vehicles_dedups_across_homes` — same vehicle
   returned under two homes → appears once.
9. `test_retries_on_429_then_succeeds` — first response 429, second 200;
   patch `asyncio.sleep` to keep the test fast, assert it was called.
10. `test_no_retry_on_401` — fails immediately, `_session.get` called
    exactly once.
11. `test_exhausts_retries_on_persistent_5xx` — all attempts 503 → raises
    `TibberVehicleApiError` after `MAX_RETRIES`.

### `tests/test_init.py`

12. `test_setup_entry_success` — coordinator populates, `entry.runtime_data`
    set, sensor platform forwarded.
13. `test_setup_entry_oauth_implementation_unavailable` →
    `ConfigEntryNotReady`.
14. `test_setup_entry_token_refresh_fails` (`aiohttp.ClientError` from
    `async_ensure_token_valid`) → `ConfigEntryNotReady`.
15. `test_unload_entry`.

### `tests/test_sensor.py`

16. `test_sensors_created_per_vehicle` — two vehicles → 10 entities (5
    each), correct `unique_id`s and device grouping (two distinct
    devices).
17. `test_sensor_native_value_mapping` — one assertion per capability id,
    including the `range.remaining` meters→km conversion.
18. `test_sensor_missing_capability_returns_none`.
19. `test_device_info_manufacturer_omitted_when_brand_missing` —
    regression test for the hardcoded-`"Volkswagen"`-fallback bug fixed
    2026-08-24; asserts `manufacturer is None` when `info.brand` is
    absent, not a guessed value.

## Priority order

1. **`test_config_flow.py` first** — it's the actual Bronze checklist
   item, and it exercises the OAuth2 dance + multi-vehicle account
   resolution together, the highest-risk path in the whole integration.
2. **`test_api.py` next** — the retry/backoff/dedup logic is new (this
   review cycle) and has no coverage proving it actually works as
   designed, as opposed to just "looks right on inspection".
3. **`test_init.py` and `test_sensor.py`** — round out coverage once the
   above two are in place; lower risk since they're thinner glue code
   over already-tested pieces.

## Explicitly out of scope for this pass

- **No live API tests.** Everything above mocks Tibber's API and OAuth2
  server; a real end-to-end check against `data-api.tibber.com` stays a
  manual step (`docs/DEVELOPMENT.md`'s disposable Docker instance, or the
  real HA instance), not something CI runs.
- **Not chasing 95% coverage** (that's a Silver-tier target, not Bronze).
  The case list above is deliberately scoped to what actually matters for
  correctness and the Bronze checklist, not exhaustive edge-case coverage
  of every possible malformed API response.
- **`application_credentials.py`** isn't separately unit-tested — it's
  three lines returning static URLs/strings, and `test_config_flow.py`'s
  `setup_credentials` fixture already exercises it indirectly on every
  run.
