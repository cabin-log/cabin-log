# feat(frontend): replace B4A app icons with Cabinlog art

# Commit Title

feat(frontend): replace B4A app icons with Cabinlog art

# Changed File Scope

- `src/frontend/index.html`
- `src/frontend/public/icons/icon.svg`
- `src/frontend/public/icons/icon.png`
- `src/frontend/public/sprites/aseprites/icon.aseprite`
- `src/frontend/src-tauri/icons/*`
- `src/frontend/src-tauri/tauri.macos.conf.json`
- `src/frontend/src/styles/app.css`
- `notes/ko/CABINLOG_GAME_DESIGN.md`
- `notes/ko/frontend/README.md`
- `src/frontend/README.md`
- `worklog/0145-cabinlog-app-icons.md`

# Reason

The frontend and packaged app should no longer show the inherited B4A icon. The browser favicon, public Cabinlog icon asset, and Tauri app icons need to share the same Cabinlog pixel art source.

# Impact

Adds the Cabinlog icon assets, points the browser favicon at `/icons/icon.svg`, regenerates the Tauri icon set from that SVG, keeps the login background fully visible by sizing it to viewport height with a dark fallback outside the artwork, and documents the `443 x 249` login scene ratio.
