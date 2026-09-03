# fix(frontend): cover the login background viewport

# Commit Title

fix(frontend): cover the login background viewport

# Changed File Scope

- `src/frontend/src/styles/app.css`
- `src/frontend/public/sprites/img/init-page.gif`
- `notes/ko/CABINLOG_GAME_DESIGN.md`
- `notes/ko/frontend/README.md`
- `src/frontend/README.md`
- `worklog/0146-cover-login-background.md`

# Reason

The login init background was fit by height, which preserved the whole artwork but left empty side areas on wider screens. The GIF also needed to keep the requested slower loop timing.

# Impact

Changes the login init background sizing to cover the full viewport while keeping the `443 x 249` pixel-art ratio, sets the GIF frame delay to `0.6s`, and updates the docs to state that edges can crop on mismatched viewport ratios.
