# feat(frontend): render cabin room with phaser

# Commit Title

feat(frontend): render cabin room with phaser

# Changed File Scope

- `src/frontend/package.json`
- `src/frontend/package-lock.json`
- `src/frontend/public/sprites/img/floor.png`
- `src/frontend/public/sprites/img/wall.png`
- `src/frontend/public/sprites/aseprites/floor.aseprite`
- `src/frontend/public/sprites/aseprites/wall.aseprite`
- `src/frontend/src/components/features/cabin/CabinPhaserStage.tsx`
- `src/frontend/src/pages/cabin/CabinInitPage.tsx`
- `src/frontend/src/styles/app.css`
- `src/frontend/src/locales/*`
- `src/frontend/src/tests/component/pages/cabin/CabinInitPage.test.tsx`
- `src/frontend/README.md`
- `notes/ko/frontend/README.md`
- `notes/ko/CABINLOG_GAME_DESIGN.md`

# Reason

The playable cabin screen needs to start rendering actual cabin room assets before furniture and pet placement work.

# Impact

Adds Phaser as the frontend renderer dependency and mounts a FIT-scaled pixel-art canvas behind the existing cabin HUD. The first scene preloads the wood wall and oak floor assets and renders them as the isometric room base. Room center and asset Y positions are exposed as top-level tuning constants.
