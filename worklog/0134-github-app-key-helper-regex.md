# Commit Title

fix(github): support macos private key validation

# Changed File Scope

- `scripts/materialize-github-app-private-key.sh`

# Reason

The helper script's PEM validation regex used an empty alternation that fails on macOS `grep`, blocking local GitHub App private key materialization.

# Impact

The helper script now validates GitHub App PEM private keys consistently on macOS while preserving the same output path and file permission behavior.
