# Commit Title

feat(game): add daily activity summary foundation

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/services/game.py`
- `src/backend/app/routers/v1/game.py`
- `src/backend/alembic/versions/0011_user_game_settings.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- Backend and game design documentation

# Reason

Cabinlog needs user-local daily reward windows and dashboard-ready activity
summary data before daily reward packages are implemented.

# Impact

- Users now have game settings with an IANA timezone and a fixed 05:00 daily
  cutoff hour.
- Daily activity summaries are calculated from persisted Cabinlog activities
  for a selected reward date.
- The summary returns activity counts, points, capped coins, food, pet EXP, and
  growth material preview values without creating reward packages yet.

# Verification

- `make backend-check`
- `make backend-test`
