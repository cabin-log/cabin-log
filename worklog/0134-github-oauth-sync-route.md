# Commit Title

feat(github): add oauth snapshot sync route

# Changed File Scope

- `src/backend/app/models/github.py`
- `src/backend/app/routers/v1/github.py`
- `src/backend/app/services/github.py`
- `src/backend/tests/integration/api/v1/github/test_github_integration.py`
- `src/backend/README.md`
- `notes/ko/backend/README.md`

# Reason

Cabinlog needs a backend-only route that lets a logged-in user refresh GitHub OAuth API snapshot data without requiring GitHub App installation or token persistence.

# Impact

The backend now exposes `POST /api/v1/github/sync`, which uses a request-scoped GitHub OAuth access token to refresh repositories, languages, commits, pull requests, issues, and deduplicated Cabinlog activities for the current user.
