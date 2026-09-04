# feat(frontend): add cabin camera zoom controls

# Commit Title

feat(frontend): add cabin camera zoom controls

# Changed File Scope

- `src/frontend/src/components/features/cabin/CabinPhaserStage.tsx`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/locales/en.json`
- `src/frontend/src/locales/ko.json`
- `src/frontend/README.md`
- `notes/ko/frontend/README.md`
- `notes/ko/CABINLOG_GAME_DESIGN.md`

# Reason

Cabin exploration needs bounded camera movement and explicit zoom controls so players can inspect the Phaser-rendered room with keyboard, mouse wheel, drag, and on-screen buttons.

# Impact

The cabin renderer now uses a centered camera world, clamps zoom through a shared path, supports `Q`/`E`, mouse wheel, and zoom buttons, and documents the updated renderer contract in English and Korean docs.
