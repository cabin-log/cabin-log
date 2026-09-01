# Blueprint4FastAPI

Blueprint4FastAPI is a full-stack template with:

- Backend: FastAPI + SQLAlchemy + Alembic + Redis
- Frontend: React + TypeScript + OpenAPI-generated API types
- Optional desktop shell: Tauri 2 using the same React frontend
- Monolithic static serving support (frontend build copied into backend static path)

## Documentation Entry

1. Agent/workflow rules: `AGENTS.md`
2. Deployment guide: `DEPLOY.md`
3. Backend engineering rules: `src/backend/BACKEND.md`
4. Frontend engineering rules: `src/frontend/FRONTEND.md`
5. Backend quick guide: `src/backend/README.md`
6. Frontend quick guide: `src/frontend/README.md`
7. Cabinlog game design foundation: `docs/CABINLOG_GAME_DESIGN.md`

Localized documentation rule:

- Keep translated/localized docs under `notes/<locale>/...`.
- Mirror the original document structure by domain (`backend`, `frontend`, etc.).

Current locale example (`ko`):

1. Root guide: `notes/ko/README.md`
2. Agent/workflow rules: `notes/ko/AGENTS.md`
3. Deployment guide: `notes/ko/DEPLOY.md`
4. Backend engineering rules: `notes/ko/backend/BACKEND.md`
5. Frontend engineering rules: `notes/ko/frontend/FRONTEND.md`
6. Backend test guide: `notes/ko/backend/TEST.md`
7. Frontend test guide: `notes/ko/frontend/TEST.md`
8. Cabinlog game design foundation: `notes/ko/CABINLOG_GAME_DESIGN.md`

## Repository Layout

```text
src/
  backend/
  frontend/
docker/
  scripts/
```

## Quick Start

1. Initialize env files:

```bash
make init
```

2. Run backend (local development):

```bash
make backend-install
make backend-dev
```

3. Run frontend (local development):

```bash
make frontend-install
make frontend-dev
```

4. Open:

- Backend API docs: `http://localhost:8000/docs`
- Frontend app (Vite): `http://localhost:5173`

## Make Workflow Hooks

Run `make help` to list the available workflow hooks.

Common targets:

```bash
make install              # Install backend and frontend dependencies
make backend-dev          # Run FastAPI development server
make frontend-dev         # Run Vite development server
make build                # Build backend environment and frontend artifacts
make test                 # Run backend and frontend tests
make check                # Run backend lint and frontend format checks
make format               # Format backend and frontend code
make ci                   # Run check, test, and build
```

Docker targets:

```bash
make docker-build
make docker-up
make docker-logs DOCKER_SERVICE=app
make docker-down
make docker-deploy
make docker-export
make docker-observability-up
make docker-observability-down
```

## Docker Deployment (Bash Only)

1. Prepare env:

```bash
make init
```

2. Build app image:

```bash
make docker-build
```

3. Start services (`app` + optional local `postgres/redis` based on `docker/.env`):

```bash
make docker-up
```

4. View logs:

```bash
make docker-logs DOCKER_SERVICE=app
```

5. Stop services:

```bash
make docker-down
```

6. One-shot deploy (build + recreate + export tar):

```bash
make docker-deploy
```

7. Export app image tar:

```bash
make docker-export
```

Exported image files are stored in `docker/artifacts/`.

## Build

Backend:

```bash
make backend-format
make backend-test
```

Frontend:

```bash
make frontend-format
make frontend-build
```

The browser frontend remains the default. For optional local desktop development:

```bash
cd src/frontend
npm run tauri:dev
```

Or run it from the repository root. The launcher automatically adds the standard
Rust installation path (`~/.cargo/bin`) when the current shell has not loaded it:

```bash
make frontend-desktop-dev
```
