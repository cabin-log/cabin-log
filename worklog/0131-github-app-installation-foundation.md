# Commit Title

feat(github): add app installation foundation

# Changed File Scope

- `src/backend/app/models/activity.py`
- `src/backend/app/models/github.py`
- `src/backend/app/routers/v1/github.py`
- `src/backend/app/services/github.py`
- `src/backend/app/core/config/settings.py`
- `src/backend/alembic/versions/0008_github_app_installations.py`
- `src/backend/tests/integration/api/v1/github/test_github_integration.py`
- `src/backend/.env.example`
- `src/backend/README.md`
- `notes/ko/backend/README.md`

# Reason

Cabinlog needs GitHub App installation state so repository/webhook activity can be attributed by installation instead of relying only on mutable user-facing GitHub login or webhook sender identity.

# Impact

GitHub App `installation` and `installation_repositories` webhooks now persist installation and selected repository state. Push and pull request activities can be linked through `installation.id`, and users can inspect the configured install URL and linked installations through the GitHub API endpoints.
