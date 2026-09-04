# Frontend Test Engineering Guide

This document defines frontend test architecture and execution rules for `src/frontend`.

## 0) Scope and Priority

- Scope: everything under `src/frontend/src/tests` and `src/frontend/tests`.
- Read order before frontend test work:

1. Root `AGENTS.md`
2. `src/frontend/FRONTEND.md`
3. This document (`src/frontend/TEST.md`)

## 1) Test Pyramid (De Facto)

1. Unit: pure utils and small logic branches
2. Component: page/component user interaction and rendering behavior
3. Integration: API layer + hook behavior with MSW
4. E2E: browser route smoke and critical user journey with Playwright

## 1.1) Backend-Scenario Alignment Rule

Frontend scenario tests must track backend `full-system` sequence from:

1. `src/backend/TEST.md` (`## 8.1) Seeded Full-System Scenario Sequence`)

Alignment policy:

1. Keep principal/credentials/API key names in shared scenario fixture (`src/tests/fixtures/fullSystemScenarioData.ts`).
2. Cover backend contract branches that are reachable from frontend UX.
3. For backend-only flows not exposed in frontend UI (for example API-key auth via `X-API-Key` on `/auth/me`), document as out-of-scope and keep validation in backend tests.

## 2) Current Test Layout

```text
src/frontend/
  src/
    tests/
      unit/
        hooks/
          serverConnectivity.test.ts
        utils/
          apiBase.test.ts
          desktopRuntime.test.ts
          validation.test.ts
      component/
        App.test.tsx
        components/
          layout/
            AppNavbar.test.tsx
            DesktopTitleBar.test.tsx
        pages/
          cabin/
            CabinInitPage.test.tsx
          login/
            LoginPage.test.tsx
          settings/
            SettingsPage.test.tsx
      integration/
        api/
          configApi.test.ts
          systemApi.test.ts
        hooks/
          useAuth.test.tsx
          useFeatures.test.tsx
          useServerConnectivity.test.tsx
      fixtures/
        fullSystemScenarioData.ts
      setup.ts
      mocks/
        handlers.ts
        server.ts
      utils/
        renderWithRouter.tsx
  tests/
    e2e/
      auth-smoke.spec.ts
  playwright.config.ts
```

## 3) Tooling

1. Unit/Component/Integration: `Vitest + Testing Library + MSW`
2. E2E: `Playwright`

## 4) Marker-free Execution Commands

Run all Vitest suites:

```bash
cd src/frontend
npm run test
```

Run unit tests only:

```bash
cd src/frontend
npm run test:unit
```

Run component tests only:

```bash
cd src/frontend
npm run test:component
```

Run integration tests only:

```bash
cd src/frontend
npm run test:integration
```

Run full test matrix in sequence (unit -> component -> integration -> e2e):

```bash
cd src/frontend
npm run test:all
```

Run Vitest in watch mode:

```bash
cd src/frontend
npm run test:watch
```

Run E2E route smoke:

```bash
cd src/frontend
npm run test:e2e
```

Run E2E with UI mode:

```bash
cd src/frontend
npm run test:e2e:ui
```

## 5) MSW Rules

1. Default API mocks are centralized in `src/tests/mocks/handlers.ts`.
2. Tests that need branch-specific payloads must override handlers with `server.use(...)`.
3. Unhandled requests are treated as failures (`onUnhandledRequest: "error"`).

## 6) Test Writing Format

Each test should keep scenario intent explicit using Given/When/Then comments.

Template:

```ts
it("<behavior>", async () => {
    // Given: ...
    // When: ...
    // Then: ...
});
```

## 7) Domain Onboarding Rules

When a new frontend domain is added:

1. Add unit tests for shared domain utils (if any).
2. Add component/page tests for key interaction and validation flows.
3. Add integration tests for API module error/success branches using MSW.
4. If route is critical, add at least one Playwright route smoke case.

## 8) Current Scenario Inventory

1. `src/tests/unit/utils/apiBase.test.ts`
    - Local loopback hostname alignment for same-site authentication cookies.
2. `src/tests/unit/utils/desktopRuntime.test.ts`
    - Browser/Tauri runtime distinction and desktop platform detection.
3. `src/tests/unit/utils/cabinEntryRedirect.test.ts`, `src/tests/unit/utils/cabinEntryReveal.test.ts`
    - OAuth callback bootstrap rewrite and one-time cabin reveal storage.
4. `src/tests/unit/utils/validation.test.ts`
    - Email/password validation success and failure branches.
5. `src/tests/component/components/layout/DesktopTitleBar.test.tsx`
    - Browser hidden state, native macOS controls, Windows window actions, and standalone connectivity placement.
6. `src/tests/integration/api/configApi.test.ts`
    - `/config` success and failure API response handling.
7. `src/tests/component/pages/login/LoginPage.test.tsx`
    - Invalid email client-side validation branch.
    - Successful login submit + navigation branch.
    - `INVALID_CREDENTIALS` remaining-attempts branch.
    - `EMAIL_NOT_VERIFIED` + resend verification branch.
8. `src/tests/component/pages/cabin/CabinInitPage.test.tsx`
    - Playable init screen loads backend game state.
    - Package and settings buttons open modal overlays without leaving `/cabin`.
    - Login success entry state applies the cabin reveal class.
9. `src/tests/component/pages/settings/SettingsPage.test.tsx`
    - Role badge visibility branch:
      admin role shows badge, user role hides badge.
    - Backend-aligned API key lifecycle flow:
      create -> reveal -> list-visible -> disable -> enable -> delete.
    - Backend-aligned error branches:
      duplicate-name (`API_KEY_NAME_ALREADY_EXISTS`), delete not-found (`API_KEY_NOT_FOUND`).
10. `src/tests/integration/hooks/useAuth.test.tsx`
    - refresh bootstrap success branch (no token -> refresh -> me).
    - stored token + `/me` success branch (refresh skip).
    - `/me` fail + refresh fail branch (token clear and logged-out state).
    - logout API failure branch with client-side session clear in `finally`.
11. `tests/e2e/auth-smoke.spec.ts`
    - Browser-level `/login` route render smoke.
12. `src/tests/unit/hooks/serverConnectivity.test.ts`
    - Exponential reconnect delay, cap, and jitter boundaries.
13. `src/tests/integration/api/systemApi.test.ts`
    - Ready and degraded `/health/ready` response handling.
14. `src/tests/integration/hooks/useServerConnectivity.test.tsx`
    - Browser polling exclusion and Tauri offline-to-online recovery.
15. `src/tests/component/App.test.tsx`
    - Fail-closed protected routing, shared public-navbar structure, and delayed retry loading state when `/config` is unavailable.
16. `src/tests/integration/hooks/useFeatures.test.tsx`
    - Configuration failure remains distinct from explicit login disablement and recovers on retry.
17. `src/tests/component/components/layout/AppNavbar.test.tsx`
    - Compact desktop connectivity status placement beside the profile control, stable retry label, and offline logout blocking.
18. `src/tests/component/pages/main/LandingPage.test.tsx`
    - Shared public-navbar structure and landing navigation behavior.

## 8.1) Backend Full-System Mapping (Frontend-Reachable Subset)

Mapped Auth branches:

1. Login success
2. Login invalid credentials with remaining attempts
3. Email-not-verified + resend verification action
4. Malformed email client-side validation
5. Session bootstrap via refresh when access token is missing
6. Session clear path when `/me` and refresh both fail
7. Logout `finally` clear path even if logout API fails

Mapped API key branches:

1. Create API key success
2. Duplicate API key name conflict
3. Key appears in list after create
4. Key disable status update
5. Key enable status update
6. Key delete success
7. Key delete not-found branch

Backend-only (not frontend-reachable) branches remain backend-owned:

1. API-key-based `/auth/me` auth success/rejection (`X-API-Key`)

## 9) Verification Checklist

Before commit:

```bash
cd src/frontend
npm run format
npm run format:check
npm run test
npm run build
```
