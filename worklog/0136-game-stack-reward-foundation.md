# Commit Title

feat(game): add stack reward package foundation

# Changed File Scope

- `src/backend/app/models/game.py`
- `src/backend/app/services/game.py`
- `src/backend/app/routers/v1/game.py`
- `src/backend/app/routers/v1/rewards.py`
- `src/backend/alembic/versions/0010_game_stack_rewards.py`
- `src/backend/app/services/github.py`
- `src/backend/app/models/github.py`
- `src/backend/tests/integration/api/v1/game/`
- Backend and game design documentation

# Reason

Cabinlog needs the first backend game foundation after GitHub OAuth sync: stack
profiles, reward package delivery, and package claim behavior.

# Impact

- GitHub OAuth sync now recalculates stack profiles and creates idempotent stack
  reward packages when language mastery thresholds are reached.
- Users can query stack profiles, list delivered reward packages, and claim a
  package to create or upgrade an owned stack reward.
- Stack profiles reflect current GitHub snapshot data, while claimed stack
  rewards keep their highest claimed level.
- Daily reward timing remains a documented design decision for the next step.

# Verification

- `make backend-check`
- `make backend-test`
