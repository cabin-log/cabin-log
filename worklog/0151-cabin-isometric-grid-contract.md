# feat(cabin): align isometric grid contract

# Commit Title

feat(cabin): align isometric grid contract

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/alembic/versions/0014_cabin_grid_contract_12x12.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/frontend/src/components/features/cabin/CabinPhaserStage.tsx`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/utils/cabinProjection.ts`
- `src/frontend/src/tests/*`
- `src/backend/README.md`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `notes/ko/*`

# Reason

The visible isometric debug grid that was adjusted against the cabin floor should become the real object and pet placement contract instead of remaining a temporary frontend override.

# Impact

New and existing cabins use a `12 x 12` logical floor with `60 x 30 px` isometric tiles and `46 px` z-height. The Phaser cabin stage renders the backend cabin contract directly, shows the placement grid and z guides for verification, and the backend bounds validation uses the same persisted cabin dimensions.
