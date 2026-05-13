#!/usr/bin/env bash
set -euo pipefail

SECRETS_FILE="/etc/snailbot/secrets.env"
SECRETS_DIR="$(dirname "$SECRETS_FILE")"
KEY_NAME="9ROUTER_API_KEY"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage:
  scripts/add_9router_api_key.sh

What it does:
  - Prompts for 9ROUTER_API_KEY using hidden input
  - Creates /etc/snailbot/secrets.env if missing
  - Updates or appends 9ROUTER_API_KEY
  - Sets owner root:root and chmod 600
  - Backs up existing secrets.env before changing it

Security:
  Do not pass the key as an argument. The script intentionally avoids CLI args
  so the secret is not stored in shell history or process listings.
EOF
  exit 0
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "This script needs root to write $SECRETS_FILE. Re-running with sudo..." >&2
  exec sudo --preserve-env=PATH bash "$0"
fi

printf "Enter %s: " "$KEY_NAME" >&2
IFS= read -r -s API_KEY
printf "\n" >&2

if [[ -z "$API_KEY" ]]; then
  echo "ERROR: empty key; nothing changed." >&2
  exit 1
fi

if [[ "$API_KEY" =~ [[:space:]] ]]; then
  echo "ERROR: key contains whitespace; nothing changed." >&2
  exit 1
fi

install -d -m 700 -o root -g root "$SECRETS_DIR"

if [[ -f "$SECRETS_FILE" ]]; then
  BACKUP="$SECRETS_FILE.bak.$(date +%Y%m%dT%H%M%S)"
  cp --preserve=mode,ownership,timestamps "$SECRETS_FILE" "$BACKUP"
  echo "Backup created: $BACKUP" >&2
else
  touch "$SECRETS_FILE"
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

# Preserve all existing lines except previous 9ROUTER_API_KEY assignment.
grep -v -E "^${KEY_NAME}=" "$SECRETS_FILE" > "$TMP_FILE" || true
printf '%s=%q\n' "$KEY_NAME" "$API_KEY" >> "$TMP_FILE"

install -m 600 -o root -g root "$TMP_FILE" "$SECRETS_FILE"

# Verify without printing the secret.
if grep -q -E "^${KEY_NAME}=" "$SECRETS_FILE"; then
  echo "OK: $KEY_NAME saved to $SECRETS_FILE" >&2
  echo "OK: permissions set to $(stat -c '%U:%G %a' "$SECRETS_FILE")" >&2
else
  echo "ERROR: verification failed; $KEY_NAME not found after write." >&2
  exit 1
fi
