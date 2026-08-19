# Commit Title

feat(auth): disable password auth by default

# Changed File Scope

- `src/backend/app/core/config/settings.py`
- `src/backend/app/core/error/auth_exception.py`
- `src/backend/app/main.py`
- `src/backend/app/routers/v1/auth.py`
- `src/backend/app/services/auth.py`
- `src/backend/tests/`
- `src/backend/.env.example`
- `src/backend/README.md`
- `notes/ko/backend/README.md`

# Reason

Cabinlog uses GitHub-centered authentication, so legacy email/password authentication needs to be disabled by default without removing the existing Blueprint4FastAPI implementation.

# Impact

Password signup, password login, OAuth2 password token, email verification, and password reset flows now return `PASSWORD_AUTH_DISABLED` unless `PASSWORD_AUTH_ENABLED=true`. OAuth login remains available. Backend request lifecycle follows the existing router-service-error flow; domain event and background task loops are not applicable because this only gates auth entrypoints.
