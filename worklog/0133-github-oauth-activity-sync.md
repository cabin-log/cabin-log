# Commit Title

feat(github): sync oauth activity snapshots

# Changed File Scope

- `src/backend/app/core/config/settings.py`
- `src/backend/app/models/activity.py`
- `src/backend/app/models/github.py`
- `src/backend/app/services/auth.py`
- `src/backend/app/services/github.py`
- `src/backend/alembic/versions/0009_activity_source_external_id.py`
- `src/backend/tests/integration/api/v1/github/test_github_integration.py`
- `src/backend/.env.example`
- `src/backend/README.md`
- `notes/ko/backend/README.md`

# Reason

Cabinlog should use GitHub OAuth as the default MVP data collection path instead of requiring every user to install the GitHub App before repository and activity data can be collected.

# Impact

GitHub OAuth login now snapshots repositories, languages, commits, pull requests, and issues through the OAuth API and persists deduplicated Cabinlog activities. GitHub App/webhook support remains available as an optional realtime integration path.
