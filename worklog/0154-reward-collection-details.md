# Commit Title

feat(game): add reward collection details

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/services/game.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/frontend/src/api/game/gameApi.ts`
- `src/frontend/src/hooks/api/game/useGameApi.ts`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/frontend/src/tests/component/pages/cabin/CabinInitPage.test.tsx`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `src/backend/README.md`
- `notes/ko/...`

# Reason

The reward collection needed to show every known furniture and pet log candidate, including event rewards, while inventory and package panels needed fixed-height, scrollable game-style layouts.

# Impact

Players can inspect all collection targets, locked unlock conditions, claimed inventory details, and placed reward state from the cabin UI. Package, inventory, and collection modals now keep stable heights even when content is empty or overflowing.

Changes:
- Added full stack and event reward collection entries with asset keys and unlock condition metadata.
- Reworked cabin package, inventory, and collection modal layouts into fixed-height, scrollable panels.
- Added inventory detail selection, asset fallback rendering, placement state, and collect action wiring.
- Documented the reward catalog, asset manifest, and updated frontend behavior.

Affected Files:
- Backend game reward models, service catalog, integration tests, and backend docs.
- Frontend game API wrapper, cabin page, styles, locales, component tests, and frontend docs.
- Korean localized game design and domain notes.

Verification:
- `make check`
- `make test`
