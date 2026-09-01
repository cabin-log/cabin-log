# Commit Title

chore(github): add app private key materialization helper

# Changed File Scope

- `scripts/materialize-github-app-private-key.sh`
- `src/backend/README.md`
- `notes/ko/backend/README.md`
- `src/backend/.env`

# Reason

Local GitHub App integration needs a repeatable way to place the GitHub-generated private key on disk and point backend configuration at that file without committing secrets.

# Impact

Developers can copy a downloaded GitHub App private key into the local Cabinlog config directory with safe file permissions. The local backend `.env` now references the expected private key path and includes the discovered GitHub App ID and slug.
