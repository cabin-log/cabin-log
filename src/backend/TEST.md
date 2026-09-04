# Backend Test Engineering Guide

This document defines backend test architecture and working rules for `src/backend`.
Follow this guide when adding or changing tests.

## 0) Scope and Priority

- Scope: everything under `src/backend/tests`.
- Read order before backend test work:
1. Root `AGENTS.md`
2. `src/backend/BACKEND.md`
3. This document (`src/backend/TEST.md`)
- Priority on conflicts:
1. Root `AGENTS.md`
2. `src/backend/BACKEND.md`
3. This document

## 1) Test Strategy (De Facto, Project-Adapted)

Recommended pyramid:
1. Smoke: app boot and critical route availability
2. API Contract: router-level request/response/auth contract with dependency overrides
3. Unit: service/util logic with mocked dependencies
4. Integration: DB/Redis/external integration with isolated test data
5. E2E: full-system validation in running environment

Current baseline implemented:
1. Smoke test (`tests/test_smoke.py`)
2. API contract tests by domain (`tests/api/v1/<domain>/test_*_api.py`)
3. Integration tests by domain (`tests/integration/api/v1/<domain>/test_*_integration.py`)
4. Full-system seeded integration scenarios (`tests/integration/scenarios/test_full_system_scenario.py`)

## 2) Current Directory Layout

```text
src/backend/tests/
  conftest.py
  test_smoke.py
  api/
    v1/
      auth/
        test_auth_api.py
      api_key/
        test_api_key_api.py
      events/
        test_events_api.py
  integration/
    api/v1/
      auth/
        test_auth_integration.py
      api_key/
        test_api_key_integration.py
    scenarios/
      test_full_system_scenario.py
```

Planned expansion layout:

```text
src/backend/tests/
  unit/
    services/
    utils/
```

## 3) Core Principles

1. Keep `Router -> Service` boundary explicit in tests.
2. Prefer fast, deterministic tests first (smoke + API contract).
3. Use `dependency_overrides` for router tests to replace service/auth dependencies.
4. Avoid real external I/O in smoke/API contract tests.
5. Add integration tests when behavior depends on DB/Redis transaction semantics.

## 4) Smoke Test Rules

- Goal: verify application boot and critical route availability.
- Current endpoint contract: `GET /ping -> 200 {"status":"ok","message":"pong"}`.
- File: `tests/test_smoke.py`.
- Smoke tests must be minimal and always fast.

## 5) API Contract Test Rules (Current Main Harness)

For each API domain:
1. Create `tests/api/v1/<domain>/test_<domain>_api.py`.
2. Build a small test app and include only the target router.
3. Override dependencies (`AuthService`, `APIKeyService`, `get_current_user`, etc.).
4. Assert status code + essential response contract.

Mandatory coverage per domain (minimum):
1. Success case (200/201)
2. Auth failure case (401 when protected)
3. Request validation failure (422 when input invalid)
4. Auth OAuth callback redirect target when redirect-mode behavior changes

Notes for this codebase:
1. Router tests use fake services, not real repositories.
2. This keeps tests independent from DB and Redis runtime state.
3. API contract tests should use minimal contract payload data, not production-like seed datasets.

## 6) Fixtures and Reuse

- Shared fixtures belong in `tests/conftest.py`.
- API contract payload constants belong in `tests/fixtures/api_contract_data.py`.
- Shared payload builders (`signup/login`) belong in `tests/fixtures/payload_data.py`.
- Production-like seed dataset constants belong in `tests/fixtures/scenario_seed_data.py`.
- Current shared fixture: `sample_user` (`UserResponse`).
- Keep fixtures small and composable.
- If domain-only fixture is needed, define it near that domain test file.

Seed schema standard (required):
1. Seed user schema: `SeedUserSchema`
   - `email: str`
   - `name: str`
   - `password: str`
   - `role: str`
   - `is_verified: bool`
2. Seed profile schema: `SeedProfileSchema`
   - `profile_name: str`
   - `primary_user: SeedUserSchema`
   - `existing_user_count: int`
   - `existing_user_role: str`
   - `existing_user_email_prefix: str`
   - `existing_user_name_prefix: str`
   - `existing_user_start_index: int`
3. Default profile constant: `DEFAULT_SEED_PROFILE`
4. Seed fixture (`seeded_integration_client`) must consume a `SeedProfileSchema` path, not raw ad-hoc constants.

Scenario flow schema standard (required):
1. Cross-domain scenario input schema belongs in `tests/fixtures/scenario_flow_data.py`.
2. Scenario schema should declare:
   - principal credentials (login email/password)
   - domain-specific action inputs (for example API key name)
   - expected branch flags (for example disabled-key rejection)
3. Scenario tests should consume schema constants (for example `DEFAULT_FULL_SYSTEM_SCENARIO`) instead of inline literals.

## 7) Unit / Integration / E2E Policy

Unit tests:
1. Target service or utility decision logic.
2. Mock repository/external calls.
3. No real DB/network.

Integration tests:
1. Use real test DB/Redis path.
2. Isolate data per test (transaction rollback or dedicated reset fixture).
3. Cover flows where repository/query behavior matters.
4. Include production-like seeded dataset scenarios when business behavior depends on existing records.
5. Use `seeded_integration_client` for preloaded-state flows (baseline user + existing users).
6. Maintain full-system scenario flow under `tests/integration/scenarios/`.
7. Marker boundaries are required:
   - `api_test`: API contract tests only
   - `primary_data`: integration tests on clean primary data state
   - `mocked_data`: integration tests on production-like seeded data
   - `email_enabled`: integration tests that require `EMAIL_ENABLED=true` flow

E2E tests:
1. Run against a real running app instance.
2. Keep only critical user journeys.
3. Do not duplicate broad API contract coverage already done by lower levels.

## 8) Commands

Run all backend tests:

```bash
cd src/backend
uv run pytest
```

Run API contract tests only:

```bash
cd src/backend
uv run pytest -m api_test
```

Run integration tests with clean primary data:

```bash
cd src/backend
uv run pytest -m primary_data
```

Run seeded production-like scenario/integration tests:

```bash
cd src/backend
uv run pytest -m mocked_data
```

Run email-enabled integration tests:

```bash
cd src/backend
uv run pytest -m email_enabled
```

Run only full-system seeded scenarios:

```bash
cd src/backend
uv run pytest -m "mocked_data and scenario_flow"
```

Quality checks before commit:

```bash
cd src/backend
uv run ruff check .
uv run ruff format . --check
uv run pytest
```

## 8.1) Seeded Full-System Scenario Sequence

File:
1. `tests/integration/scenarios/test_full_system_scenario.py`

Execution markers:
1. `mocked_data`
2. `scenario_flow`

Auth domain sequence (`test_seeded_auth_domain_main_flow`):
1. Seeded primary user login success
2. OAuth providers contract check
3. `/auth/me` success with bearer token
4. `/auth/admin/user-role-stats` success for seeded admin principal
5. `/auth/me` profile update success
6. `/auth/refresh` success with refresh context
7. `/auth/logout` success and session invalidation
8. `/auth/refresh` rejected after logout (`INVALID_TOKEN`)
9. `/auth/signup` duplicate email rejected (`EMAIL_ALREADY_EXISTS`)
10. `/auth/login` wrong password rejected (`INVALID_CREDENTIALS`)
11. `/auth/signup` malformed email rejected (422)
12. `/auth/resend-verification` contract success
13. `/auth/forgot-password` branch by `EMAIL_ENABLED` toggle

API key domain sequence (`test_seeded_api_key_domain_main_flow`):
1. Seeded primary user login success
2. `/api-keys` create success
3. Duplicate key name rejected (`API_KEY_NAME_ALREADY_EXISTS`)
4. `/api-keys` list includes created key
5. API key auth success on `/auth/me`
6. `/api-keys/{id}/status` disable success
7. Disabled key rejected on `/auth/me` (`API_KEY_INVALID`)
8. `/api-keys/{id}/status` enable success
9. Re-enabled key auth success on `/auth/me`
10. `/api-keys/{id}` delete success
11. Deleted key repeat-delete rejected (`API_KEY_NOT_FOUND`)

## 8.2) Test Data Lifecycle

1. `api_test` does not use DB seed data.
2. `primary_data` integration uses per-test isolated temporary DB with clean initial state.
3. `mocked_data` integration uses per-test isolated temporary DB plus seeded profile data.
4. Seed data is recreated for each test execution and discarded with temporary DB teardown.
5. `email_enabled` integration uses `email_enabled_integration_client` fixture which forces `EMAIL_ENABLED=true` with null mail provider to avoid external SMTP dependency.

## 8.3) Error Contract Consistency Rule (Static Serving Mode)

1. In static serving mode, SPA fallback must apply only to non-API HTML requests.
2. API-path (`/api/...`) 404 responses must preserve domain error payload shape from raised exception detail.
3. Do not replace API 404 detail with plain `"Not Found"` in fallback handler logic.

## 8.4) Current Scenario Inventory

Smoke:
1. `tests/test_smoke.py::test_ping_returns_ok`

API contract (`api_test`):
1. `tests/api/v1/auth/test_auth_api.py`
2. `tests/api/v1/api_key/test_api_key_api.py`
3. `tests/api/v1/events/test_events_api.py`

Integration primary dataset (`primary_data`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` primary-state flows + RBAC forbidden/success branches
2. `tests/integration/api/v1/api_key/test_api_key_integration.py`

Integration email-enabled dataset (`email_enabled`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` email verification required login + forgot-password token issuance flows

Integration seeded dataset (`mocked_data`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` seeded-state flows
2. `tests/integration/scenarios/test_full_system_scenario.py`

## 9) Naming and Style Rules

1. File name: `test_<target>.py`
2. Test function name: `test_<behavior>_<expected_result>`
3. Each test function must include a one-line scenario docstring.
4. Multi-step tests must use `Given / When / Then` inline comments.
5. Use explicit assertions for:
   - status code
   - error code/message keys for domain failures
   - critical response payload fields
6. Keep each test focused on one behavior.

Required format template:

```python
def test_<behavior>_<expected_result>(...):
    """Scenario: <what flow is being verified in one sentence>."""
    # Given: <initial state or setup condition>
    # When: <action/request under test>
    # Then: <expected result/contract>
```

Example:

```python
def test_me_requires_authentication(sample_user):
    """Scenario: protected route denies access without auth dependency."""
    # Given: client without current-user override.
    # When: /api/v1/auth/me is requested.
    # Then: 401 with INVALID_TOKEN error code is returned.
```

## 10) Change Checklist

When backend API behavior changes:
1. Update matching domain API tests under `tests/api/v1/<domain>/`.
2. Add/adjust smoke test only if boot/critical route contract changed.
3. If behavior depends on persistence semantics, add integration coverage.
4. Keep docs synchronized (`BACKEND.md`, `README.md`, this file if needed).

## 11) New Domain Test Onboarding Rules (Required)

When a new backend domain/router is added, keep the same testing format.

Required directory targets:
1. API contract tests: `tests/api/v1/<domain>/test_<domain>_api.py`
2. Integration tests: `tests/integration/api/v1/<domain>/test_<domain>_integration.py`
3. If domain participates in end-to-end business flow, update/add scenario test under
   `tests/integration/scenarios/`.

Required minimum test set per new domain:
1. API contract success case (200/201)
2. API contract auth failure case (401/403 if protected)
3. API contract request validation failure (422)
4. Integration success flow on empty initial state
5. Integration scenario on seeded state (`seeded_integration_client`) when behavior depends on existing records
6. If domain is part of core flow, add/adjust cross-domain scenario assertion path.

Fixture/data boundary rules for new domains:
1. Do not put production-like seeded records in API contract data.
2. Put API contract constants in `tests/fixtures/api_contract_data.py`.
3. Put shared request payload builders in `tests/fixtures/payload_data.py`.
4. Put production-like dataset schemas/profiles in `tests/fixtures/scenario_seed_data.py`.
5. If a domain needs additional seeded scenarios, add new `SeedProfileSchema` profiles (do not bypass schema with ad-hoc fields).

Review gate before merging new domain tests:
1. Confirm docstring + Given/When/Then format compliance
2. Confirm API vs Integration data boundary is preserved
3. Run `uv run ruff check .`, `uv run ruff format . --check`, `uv run pytest`
