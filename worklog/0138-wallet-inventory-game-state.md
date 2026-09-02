# Commit Title

feat(game): add wallet inventory and game state

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/services/game.py`
- `src/backend/app/routers/v1/game.py`
- `src/backend/alembic/versions/0012_wallet_inventory_foundation.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- Backend and game design documentation

# Reason

Cabinlog needs a minimal persisted ownership state before frontend game work can
consume a stable backend contract.

# Impact

- Daily reward package claims now add coins to the wallet and stack food,
  material, PET_EXP, and cosmetic items in inventory.
- Stack reward claims continue to create or upgrade owned stack rewards.
- `GET /api/v1/game/state` exposes the first playable cabin state contract:
  settings, today summary, wallet, inventory, stack profiles, owned stack
  rewards, and pending packages.

# Verification

- `make backend-check`
- `make backend-test`
