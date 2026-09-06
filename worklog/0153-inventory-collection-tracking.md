# Commit Title

feat(game): add inventory and collection tracking

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/routers/v1/game.py`
- `src/backend/app/services/game.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/frontend/src/api/game/gameApi.ts`
- `src/frontend/src/api/generated/openapi.ts`
- `src/frontend/src/hooks/api/game/useGameApi.ts`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/frontend/src/tests/component/pages/cabin/CabinInitPage.test.tsx`
- `src/backend/README.md`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `notes/ko/...`

# Reason

Players need a way to claim delivered reward packages and track received game rewards before object placement and pet progression are added.

# Impact

The cabin state now includes categorized inventory and collection data. The cabin UI can claim packages in place, show supplies, furniture, and pet logs in inventory slots, and show furniture and pet logs in a collection grid while excluding consumable supplies from the collection.
