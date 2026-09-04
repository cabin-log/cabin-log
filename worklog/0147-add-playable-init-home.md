# feat(frontend): add playable cabin init route

# Commit Title

feat(frontend): add playable cabin init route

# Changed File Scope

- `src/frontend/src/App.tsx`
- `src/frontend/src/api/auth/authError.ts`
- `src/frontend/src/api/generated/openapi.ts`
- `src/frontend/src/api/game/*`
- `src/frontend/src/hooks/api/game/*`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/components/layout/*`
- `src/frontend/src/components/ui/overlays/Modal.tsx`
- `src/frontend/src/locales/*`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/tests/component/pages/cabin/*`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `notes/ko/frontend/README.md`
- `notes/ko/frontend/TEST.md`
- `notes/ko/CABINLOG_GAME_DESIGN.md`
- `worklog/0147-add-playable-init-home.md`

# Reason

After GitHub login, players need to arrive directly in a Cabinlog playable init screen instead of stopping on an intermediate success page or inherited showcase route.

# Impact

Adds a protected `/cabin` route backed by `GET /api/v1/game/state`, redirects `/login/success` directly into `/cabin`, removes the intermediate login success page, and provides transparent package/settings modal panels over the cabin pixel-art scene. The settings modal includes the GitHub-backed profile summary and logout action.
