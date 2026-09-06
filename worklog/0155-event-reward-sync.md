# Commit Title

feat(game): add event reward sync

# Changed File Scope

- `src/backend/app/services/game.py`
- `src/backend/tests/integration/api/v1/game/test_game_rewards_integration.py`
- `src/backend/tests/integration/api/v1/github/test_github_integration.py`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/backend/README.md`
- `src/frontend/README.md`
- `notes/ko/...`

# Reason

Event reward catalog entries were visible in the collection, but sync did not yet evaluate achievement conditions or create claimable packages.

# Impact

Reward sync now creates one-time `ACHIEVEMENT` packages for event milestones based on stored GitHub activity. Event packages use localized package copy in the cabin UI and claim through the existing reward inventory flow.

Changes:
- Added event reward progress calculation for activity time, review, release, bugfix, documentation, first sync, streak, weekend, and collaboration milestones.
- Added one-time achievement package creation during game reward sync.
- Localized event reward package display in the cabin package modal.
- Updated backend, frontend, and Korean game design documentation.
- Added integration and component test coverage for event reward package creation and display.

Affected Files:
- Backend game reward sync service and GitHub/game integration tests.
- Frontend cabin package display, locales, and component tests.
- Backend/frontend README files and Korean localized notes.

Verification:
- `make check`
- `make test`
