# feat(game): settle synced cabin rewards

# Commit Title

feat(game): settle synced cabin rewards

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/routers/v1/game.py`
- `src/backend/app/services/game.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/backend/tests/integration/api/v1/github/test_github_integration.py`
- `src/frontend/src/api/game/gameApi.ts`
- `src/frontend/src/api/generated/openapi.ts`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/frontend/src/tests/component/pages/cabin/CabinInitPage.test.tsx`
- `src/frontend/src/tests/unit/utils/cabinDailySync.test.ts`
- `src/frontend/src/utils/cabinDailySync.ts`
- `src/backend/README.md`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `notes/ko/...`

# Reason

Cabin entry needed a deterministic reward sync that settles the last completed
daily window, creates one-time onboarding rewards from existing GitHub history,
and avoids package-based pet evolution beyond the first stack unlock.

# Impact

- Adds `POST /api/v1/game/rewards/sync` for stored-data game reward settlement.
- Defaults omitted daily reward dates to the last completed reward date.
- Creates GitHub history onboarding rewards once per user.
- Limits stack packages to level 1 origin unlocks; later pet/furniture growth is
  left for selection-based level-up flows.
- Removes daily `growth_material` from the API contract and generated frontend
  types.
- Runs cabin reward sync once per local user and settled reward date, with a HUD
  refresh button for manual sync.
- Localizes package display labels from metadata and adds scroll bounds to the
  package modal.

# Verification

- `make check`
- `make test`
- `cd src/frontend && npm run build`
