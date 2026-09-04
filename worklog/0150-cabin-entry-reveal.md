# feat(auth): reveal cabin after oauth login

# Commit Title

feat(auth): reveal cabin after oauth login

# Changed File Scope

- `src/backend/app/core/config/settings.py`
- `src/backend/.env.example`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/frontend/src/App.tsx`
- `src/frontend/src/main.tsx`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/pages/login/LoginPage.tsx`
- `src/frontend/src/utils/cabinEntryRedirect.ts`
- `src/frontend/src/utils/cabinEntryReveal.ts`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/tests/*`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `src/backend/TEST.md`
- `notes/ko/*`

# Reason

OAuth login should land directly in the cabin instead of briefly showing an intermediate success route, while still making the cabin interior appear naturally on first entry.

# Impact

Backend OAuth redirect defaults to `/cabin`, frontend login queues a one-time cabin reveal flag, and the cabin screen consumes that flag to animate the existing interior view. `/login/success` remains as a legacy fallback that rewrites before React routing renders.
