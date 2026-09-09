# Pet Log Spritesheet Motion

# Commit Title

`feat(frontend): migrate pet logs to spritesheet motion`

# Changed File Scope

Changes:

- Replaced the vector Octocat placeholder in the Phaser cabin stage with the provided 32x32 spritesheet.
- Added reusable pet-log spritesheet metadata, frame mapping, reward-key resolution, and direction helpers.
- Added held, standing, walking, sleeping, and lying animation handling.
- Tuned wandering distance, pause timing, acceleration/deceleration, isometric grid direction mapping, and cursor placement alignment.
- Updated frontend and Korean game documentation and added unit coverage for frame and direction mapping.

# Reason

The default pet log needs to use the supplied production-style sheet and follow the cabin's isometric movement axes without floating or drifting during placement.

# Impact

`default.octocat` now renders with the real `cat-Sheet.png` asset. Future pet logs can register the same sheet layout through the shared sprite definition utility. The cabin placement flow remains local and does not reload the cabin state.

# Affected Files

Affected Files:

- `src/frontend/src/components/features/cabin/CabinPhaserStage.tsx`
- `src/frontend/src/utils/petLogSprites.ts`
- `src/frontend/src/tests/unit/utils/petLogSprites.test.ts`
- `src/frontend/public/sprites/aseprites/cat-Sheet.png`
- `src/frontend/README.md`
- `notes/ko/frontend/README.md`
- `notes/ko/CABINLOG_GAME_DESIGN.md`

# Verification

Verification:

- `make frontend-format-check`
- `make frontend-test`
- `npm run build:web`
- `git diff --check`

The untracked `cat-raw.aseprite` source file is intentionally excluded from the commit; `cat-Sheet.png` is included as the runtime asset.
