# Commit Title

`chore(frontend): organize sprite assets by category`

# Changed File Scope

Changes:

- Organized editable Aseprite sources and runtime images under matching `pet-logs`, `furniture`, `wallpaper`, `floor`, and `ui` folders.
- Moved the runtime pet-log spritesheet to `public/sprites/img/pet-logs` and updated Phaser, login, CSS, tests, and documentation paths.
- Added placeholder folders for future furniture and pet-log runtime assets.

# Reason

The asset library needs a stable category-based structure so future pet logs, furniture, wallpaper, and floor assets can be added without mixing source files and runtime images.

# Impact

Existing cabin, login, and pet-log rendering continues to use the same assets through their new canonical paths. No gameplay or API behavior changes.

# Affected Files

Affected Files:

- `src/frontend/public/sprites/aseprites/**`
- `src/frontend/public/sprites/img/**`
- Frontend asset references and documentation.

# Verification

Verification:

- `make frontend-format-check`
- `make frontend-test`
- `npm run build:web`
- `git diff --check`
