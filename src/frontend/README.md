# Frontend Quick Guide

This guide is for human contributors working on `src/frontend`.
For full engineering constraints, follow `src/frontend/FRONTEND.md`.
Localized docs rule: place translations under `docs/<locale>/frontend/`.
Current locale example (`ko`): `docs/ko/frontend/README.md`, `docs/ko/frontend/FRONTEND.md`, `docs/ko/frontend/TEST.md`.

## 1) Setup

```bash
cd src/frontend
npm ci
```

## 2) Run Dev Server

```bash
cd src/frontend
npm run dev
```

Default local URL:

- `http://localhost:5173`

The browser remains the default frontend target. To run the same React application in the
optional Tauri desktop shell:

```bash
cd src/frontend
npm run tauri:dev
```

The launcher automatically adds `~/.cargo/bin` to the command PATH when Rust is
installed there but the current shell has not loaded it. From the repository root,
the equivalent command is `make frontend-desktop-dev`.

Tauri development requires the Rust toolchain. The local desktop shell connects to
`http://localhost:8000` by default. Set `VITE_API_BASE_URL` when a different API is required.
The desktop shell is currently online-first: static UI assets open offline, but authentication,
API key management, realtime events, and server data require FastAPI connectivity. Offline
data caching and synchronization are separate features and are not provided by the shell.
The packaged desktop runtime actively checks `GET /health/ready` on startup and every 30 seconds.
Failed checks use exponential backoff with jitter (up to 30 seconds), and the desktop UI shows an
offline status beside the app-navbar profile control or standalone titlebar tools. The
compact status provides an immediate retry action. Browser builds do not run this desktop probe.
Landing and server-unavailable pages share the same public navbar with a centered title.
Symmetric navbar columns and a reserved connectivity-status width keep the title fixed
when retry changes the status label. Manual retry clicks keep the compact disconnected label in
place and delay heavier loading affordances so short server checks do not flicker.
When connectivity returns, the app revalidates its authentication session and configuration, and
authenticated realtime subscriptions restart. This reconnect behavior does not queue offline
mutations or resolve data conflicts. Desktop sign-out from the profile menu is disabled while the
server is disconnected so the app does not clear the local session and route to login during an
outage.
If the application has never loaded `/config` successfully, it keeps protected routes locked and
shows the server-unavailable page. Missing configuration is never interpreted as
`login_enabled=false`; login-disabled navigation is allowed only after an explicit server response.
In Tauri, native window controls share the same title bar area as landing, authentication, and
in-app navigation. The browser frontend keeps its existing navigation layout.

Login init background asset:

- The canonical file is `src/frontend/public/sprites/img/init-page.gif`.
- The current canonical size is `443 x 249 px`, preserving an approximately `1.78:1` ratio.
- CSS uses `background-size: auto 100dvh` so the artwork is fit by viewport height.
- Extra screen area is filled with the dark solid fallback `#101416` without a secondary background image.
- Larger replacements should keep the same `443:249` ratio, for example `886 x 498` or `1329 x 747`.

API base URL behavior:

- If `VITE_API_BASE_URL` is set, frontend uses that value. Local loopback aliases
  (`localhost`, `127.0.0.1`, and `::1`) are aligned with the current frontend host so
  authentication cookies remain same-site.
- If not set and current port is `5173` (Vite dev), frontend defaults to `http(s)://<current-host>:8000`.
- Otherwise, frontend defaults to current page origin (same-origin), useful for backend static serving mode.

For a packaged desktop build, set `VITE_API_BASE_URL` to the deployed FastAPI origin before
running `npm run tauri -- build`. The backend must also allow the packaged Tauri webview origin
through its CORS policy when browser-enforced HTTP requests are used. The macOS packaged origin
is `tauri://localhost`; include it in `CORS_ORIGINS` and restart FastAPI after changing the env.
The GitHub desktop build workflow accepts `api_base_url` on manual runs, then falls back to
`DESKTOP_API_BASE_URL`, then `http://localhost:8000`.

## 3) API Type Generation

Frontend API contracts are generated from backend OpenAPI:

```bash
cd src/frontend
npm run generate:api
```

Server-optional sync (uses existing generated file when backend is unavailable):

```bash
cd src/frontend
npm run api:sync
```

Generated target:

- `src/api/generated/openapi.ts`

## 4) Format / Check

```bash
cd src/frontend
npm run format
npm run format:check
```

## 5) Test

```bash
cd src/frontend
npm run test
```

Run by layer:

```bash
cd src/frontend
npm run test:unit
npm run test:component
npm run test:integration
```

Run full matrix (unit -> component -> integration -> e2e):

```bash
cd src/frontend
npm run test:all
```

E2E smoke:

```bash
cd src/frontend
npm run test:e2e
```

## 6) Build

```bash
cd src/frontend
npm run build
```

Build only the shared web assets for the desktop shell without copying them into FastAPI:

```bash
npm run build:desktop
```

Optional API contract refresh + build:

```bash
cd src/frontend
npm run build:sync
```

Strict API contract refresh from backend + build:

```bash
cd src/frontend
npm run build:strict
```

Notes:

- `npm run build` is server-independent by default (no OpenAPI fetch).
- `npm run build:sync` performs optional OpenAPI refresh before build (fallback to existing generated file on fetch failure).
- `npm run build:strict` requires successful OpenAPI refresh from `localhost:8000` before build.

## 7) Core Frontend Rules (Summary)

- API flow: `generated -> api/<domain> -> hooks/api/<domain> -> pages`
- Domain set rule: `<domain>Api.ts` + `<domain>Error.ts` + `use<Domain>Api.ts` must stay 1:1:1
- Authenticated realtime stream (`/api/v1/events/stream`) should use fetch streaming in `api/events` domain (bearer header required)
- Domain hooks are called in page layer, not in feature components
- Feature components receive state/actions via props
- Reusable components belong to `src/components/ui/*` (category folders)
- Domain-specific components belong to `src/components/features/<domain>/*`
- All CSS is managed in `src/styles/app.css`
- New reusable UI components must be showcased in `src/pages/main/ShowCasePage.tsx`

## 8) Before Commit

```bash
cd src/frontend
npm run format
npm run format:check
npm run test
npx tsc --noEmit
npm run build
```
