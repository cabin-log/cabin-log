# Commit Title

`chore(assets): track pet log source files`

# Changed File Scope

Changes:

- Add the Octocat Aseprite source files under `public/sprites/aseprites/pet-logs`.

# Reason

The editable pet-log source files must be versioned alongside the categorized runtime PNG so the asset can be maintained and regenerated later.

# Impact

Both `cat.aseprite` and `cat-raw.aseprite` are now included in the repository. Runtime rendering is unchanged.

# Affected Files

Affected Files:

- `src/frontend/public/sprites/aseprites/pet-logs/cat.aseprite`
- `src/frontend/public/sprites/aseprites/pet-logs/cat-raw.aseprite`

# Verification

Verification:

- Confirmed both source files exist under the categorized pet-log source directory.
- No runtime code changes.
