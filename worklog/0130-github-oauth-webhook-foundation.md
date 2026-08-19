# Commit Title

feat(github): add oauth profile and push webhook foundation

# Changed File Scope

- `src/backend/app/core/config/settings.py`
- `src/backend/app/core/error/`
- `src/backend/app/models/`
- `src/backend/app/services/`
- `src/backend/app/routers/v1/`
- `src/backend/alembic/`
- `src/backend/tests/integration/api/v1/github/`
- `src/backend/.env.example`
- `src/backend/README.md`
- `notes/ko/backend/README.md`

# Reason

Cabinlog needs a backend-only foundation that proves GitHub OAuth identity/profile persistence and signed GitHub push webhook ingestion without touching frontend code.

# Impact

GitHub OAuth login now stores a linked profile and repository/language snapshot that can be queried through `GET /api/v1/github/me`, `GET /api/v1/github/repositories`, and `GET /api/v1/github/stack-summary`. Backend-only OAuth verification can return token/profile JSON from the callback through `OAUTH_CALLBACK_RESPONSE_MODE=json`. Signed GitHub push and pull request webhooks create deduplicated Cabinlog activities that can be queried through `GET /api/v1/github/activities`. Backend request lifecycle and domain activity normalization loops are followed; background task loops are not applicable because webhook ingestion is synchronous in this milestone.
