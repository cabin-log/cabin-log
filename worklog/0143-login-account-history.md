# feat(auth): add recent GitHub login shortcut

# Commit Title

feat(auth): add recent GitHub login shortcut

# Changed File Scope

- `src/backend/app/models/user.py`
- `src/backend/app/services/auth.py`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/frontend/src/hooks/useAuth.tsx`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/frontend/src/pages/login/LoginPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/tests/component/pages/login/LoginPage.test.tsx`
- `src/frontend/src/tests/integration/hooks/useAuth.test.tsx`
- `src/frontend/src/tests/unit/utils/loginHistory.test.ts`
- `src/frontend/src/utils/loginHistory.ts`
- `worklog/0143-login-account-history.md`

# Reason

Returning users should be able to start from the login init screen by selecting their remembered GitHub account. The UI should avoid implying that GitHub OAuth can force account selection when the current GitHub browser session controls that behavior.

# Impact

The frontend stores only display-safe recent account metadata in localStorage, not tokens. Active sessions can enter the app directly from the remembered account button, while expired sessions continue through GitHub OAuth. GitHub OAuth login now fills an empty user profile image from the GitHub avatar so remembered account buttons can show the proper profile image after a fresh login.
