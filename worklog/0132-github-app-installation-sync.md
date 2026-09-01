# Commit Title

feat(github): sync installed repositories with app tokens

# Changed File Scope

- `src/backend/app/core/config/settings.py`
- `src/backend/app/core/error/github_exception.py`
- `src/backend/app/models/github.py`
- `src/backend/app/routers/v1/github.py`
- `src/backend/app/services/github.py`
- `src/backend/tests/integration/api/v1/github/test_github_integration.py`
- `src/backend/.env.example`
- `src/backend/README.md`
- `notes/ko/backend/README.md`

# Reason

GitHub App installation based integration needs server-side repository lookup using installation access tokens, so Cabinlog can refresh installed repository and language snapshots without relying only on OAuth user tokens.

# Impact

Authenticated users can request repository synchronization for a linked GitHub App installation. The backend mints an installation access token from configured GitHub App credentials, fetches repositories and language data, persists the snapshot, and does not store the short-lived token.
