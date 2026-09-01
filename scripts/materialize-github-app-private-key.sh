#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/materialize-github-app-private-key.sh [downloaded-private-key.pem]

Environment:
  GITHUB_APP_PRIVATE_KEY         Optional PEM content. Escaped \n sequences are supported.
  GITHUB_APP_PRIVATE_KEY_OUTPUT  Optional output path.

Default output:
  ~/.config/cabinlog/cabin-log-github-app.private-key.pem

Notes:
  The PEM must be generated from GitHub App settings. A locally generated key will
  not authenticate the GitHub App.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

source_path="${1:-}"
output_path="${GITHUB_APP_PRIVATE_KEY_OUTPUT:-$HOME/.config/cabinlog/cabin-log-github-app.private-key.pem}"
output_dir="$(dirname "$output_path")"

mkdir -p "$output_dir"

if [ -n "$source_path" ]; then
    if [ ! -f "$source_path" ]; then
        echo "private key source file not found: $source_path" >&2
        exit 1
    fi
    cp "$source_path" "$output_path"
elif [ -n "${GITHUB_APP_PRIVATE_KEY:-}" ]; then
    printf '%b\n' "$GITHUB_APP_PRIVATE_KEY" > "$output_path"
else
    usage >&2
    echo "missing downloaded PEM path or GITHUB_APP_PRIVATE_KEY content" >&2
    exit 1
fi

if ! grep -Eq -- "-----BEGIN ((RSA|EC|OPENSSH) )?PRIVATE KEY-----" "$output_path"; then
    rm -f "$output_path"
    echo "output did not look like a PEM private key" >&2
    exit 1
fi

chmod 600 "$output_path"
echo "$output_path"
