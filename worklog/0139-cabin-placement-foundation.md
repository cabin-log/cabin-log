# feat(game): add cabin placement foundation

# Commit Title

feat(game): add cabin placement foundation

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/services/game.py`
- `src/backend/app/routers/v1/game.py`
- `src/backend/app/core/error/game_exception.py`
- `src/backend/alembic/versions/0013_cabin_placement_foundation.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/backend/README.md`
- `notes/ko/backend/README.md`
- `docs/CABINLOG_GAME_DESIGN.md`
- `notes/ko/CABINLOG_GAME_DESIGN.md`

# Reason

Cabinlog needs a persistent cabin layout contract before the frontend/game client
can render an isometric room. The backend must own the saved placement state so
users can directly arrange earned stack rewards, furniture, and later inventory
objects without relying on client-only state.

# Impact

- Adds fixed-size `18 x 12` cabin records with `64 x 32 px` isometric tile
  metadata and `32 px` vertical tile height.
- Adds persisted cabin placements with `x`, `y`, `z`, `rotation`, `width`, and
  `depth`.
- Adds cabin APIs under `/api/v1/game/cabin`.
- Includes cabin state in `/api/v1/game/state`.
- Blocks placement of unowned objects, same-layer footprint overlaps, and
  user edits to locked system placements.
- Documents the initial isometric coordinate contract and backend API behavior.

# Verification

- `uv run pytest tests/integration/api/v1/game/test_game_rewards_integration.py -q`
- `make backend-check`
- `make backend-test`
