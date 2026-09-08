# Commit Title

feat(game): add default pet grab placement

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/services/game.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/frontend/src/api/game/gameApi.ts`
- `src/frontend/src/components/features/cabin/CabinPhaserStage.tsx`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/backend/README.md`
- `src/frontend/README.md`
- `notes/ko/...`

# Reason

The cabin needed a default GitHub pet log and a placement preparation flow before broader object and pet placement work.

# Impact

GitHub-linked users now receive the `default.octocat` pet log automatically. Inventory placement starts a held cursor flow, lets the user click the isometric floor cell, and updates local cabin placement state without reloading the full game state. Collect removes only the local placement after the delete API succeeds.

Changes:
- Added default Octocat pet log catalog data and automatic ownership for GitHub-linked users.
- Added frontend placement API wiring for cabin objects.
- Added Phaser held and idle Octocat placeholders with click-to-grid placement.
- Changed place and collect actions to avoid full cabin state reloads.
- Updated localized copy, docs, and tests.

Affected Files:
- Backend game repository/service and game integration tests.
- Frontend game API, cabin page, Phaser stage, styles, locales, and component tests.
- Backend/frontend README files and Korean localized game notes.

Verification:
- `make check`
- `make test`
- `npm run build`
