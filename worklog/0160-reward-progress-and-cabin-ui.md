# Commit Title

`feat(game): show reward progress and simplify cabin UI`

# Changed File Scope

- Backend game models/service and reward progress tests.
- Frontend cabin page, progress component, modal, styles, locales, generated API types, tests, environment example, and docs.

# Reason

Show actual reward acquisition and next-level progress in inventory and collection while simplifying the cabin presentation.

# Impact

- Collection responses expose current/target/remaining progress using existing mastery and event rules.
- Inventory and collection show compact progress below the level badge. Non-growing owned rewards hide level and growth labels.
- Settings, package cards, modal titles, empty states, square grids, scrolling, and action controls are simplified.
- Korean and English copy is localized; item descriptions use polite Korean declarative wording.
- `VITE_CABIN_SHOW_GRID=false` hides visual guides without changing placement coordinates.
- No database schema changes. Level-up mutation remains unimplemented; progress indicates eligibility only.

# Verification

- `make check`
- `make test`: 82 backend tests and 81 frontend tests passed.
- `make frontend-build`: TypeScript and Vite build passed; existing large bundle advisory remains.
- OpenAPI types regenerated from the local backend.
- Layout fixtures verified desktop/mobile modal sizing, centered empty states, square scrollable cells, five package rows, compact controls, and contrast.

# Loop Alignment

- Backend request lifecycle and frontend API/UI composition loops are followed.
- Progress is derived read data, so no new background, realtime, or desktop recovery loop applies.
- Internal collection scrolling is intentional per the requested UI behavior.
