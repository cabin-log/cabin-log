# fix(auth): route remembered login through GitHub OAuth

# Commit Title

fix(auth): route remembered login through GitHub OAuth

# Changed File Scope

- `src/backend/app/routers/v1/auth.py`
- `src/backend/app/services/auth.py`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/frontend/src/components/features/auth/OAuthProviderButton.tsx`
- `src/frontend/src/pages/login/LoginPage.tsx`
- `src/frontend/src/tests/component/components/features/auth/OAuthProviderButton.test.tsx`
- `src/frontend/src/tests/component/pages/login/LoginPage.test.tsx`
- `worklog/0144-login-history-oauth-entry.md`

# Reason

Remembered GitHub account shortcuts should not bypass authentication by navigating directly to the app. Re-login should visibly start a GitHub OAuth flow and request GitHub's account picker when possible.

# Impact

Recent account clicks now start the GitHub OAuth flow and land on the configured OAuth success path after backend callback. The secondary GitHub login action appends `prompt=select_account`, which GitHub documents as the account picker prompt for OAuth authorization.
