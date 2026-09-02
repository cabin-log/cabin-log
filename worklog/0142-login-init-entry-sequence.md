# feat(frontend): add login cabin entry sequence

# Commit Title

feat(frontend): add login cabin entry sequence

# Changed File Scope

- `src/frontend/src/components/features/auth/OAuthProviderButton.tsx`
- `src/frontend/src/pages/login/LoginPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/tests/component/pages/login/LoginPage.test.tsx`
- `worklog/0142-login-init-entry-sequence.md`

# Reason

The login init screen should feel like the first step into Cabinlog before GitHub OAuth starts. The title and login card need a staged entrance, and the GitHub login click should briefly transition toward the cabin before redirecting to GitHub.

# Impact

GitHub OAuth behavior remains unchanged after the short transition delay. The login page now starts a cabin-entry animation on click, prevents duplicate clicks during that sequence, zooms the background toward the cabin, and keeps reduced-motion users on static UI animations.
