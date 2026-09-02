# Cabinlog GitHub Login UI

# Commit Title

feat(frontend): add Cabinlog GitHub login screen

# Changed File Scope

- `src/frontend/src/pages/login/*`
- `src/frontend/src/components/features/auth/*`
- `src/frontend/src/components/ui/*`
- `src/frontend/src/components/layout/*`
- `src/frontend/src/styles/app.css`
- `src/frontend/public/icons/*`
- `src/frontend/public/sprites/*`
- `src/frontend/src/locales/*`
- `src/frontend/src/tests/*`
- `src/backend/app/core/config/settings.py`
- `src/backend/app/services/auth.py`
- `src/backend/.env.example`
- `src/backend/README.md`
- `notes/ko/backend/README.md`
- `src/frontend/README.md`
- `notes/ko/frontend/README.md`
- `src/frontend/FRONTEND.md`
- `notes/ko/frontend/FRONTEND.md`

# Reason

- Cabinlog needs a focused GitHub-only login entry point instead of the inherited password-oriented template UI.
- OAuth login should complete quickly and not wait on repository, commit, pull request, issue, and language synchronization.

# Impact

- Login page now presents Cabinlog pixel-art branding with a GitHub OAuth button only.
- Password, signup, reset-password, verification, dark/light theme controls, and B4A branding are removed or redirected from the active login flow.
- GitHub OAuth success redirects to `/login/success`.
- GitHub activity synchronization is disabled during login by default and remains available through explicit GitHub sync APIs.
