#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/tmp/pmo-asset-demo}"
SLUG="asset-management-demo"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_FILE="$REPO_ROOT/examples/asset-management-source.md"

rm -rf "$ROOT/$SLUG"

python -m pmo_studio.cli --root "$ROOT" init "$SLUG" \
  --customer "Demo Asset Customer" \
  --product "Asset Management Demo" \
  --brief "Generate a client-ready PMO documentation pack for an Asset Management MVP." \
  --domain-pack bteco \
  --source "$SOURCE_FILE"

python -m pmo_studio.cli --root "$ROOT" generate "$SLUG" all \
  --from-sources \
  --llm noop \
  --no-refine

python -m pmo_studio.cli --root "$ROOT" trace "$SLUG" --validate
python -m pmo_studio.cli --root "$ROOT" run-gates "$SLUG" --include-c --llm noop
python -m pmo_studio.cli --root "$ROOT" export "$SLUG" --format all --profile customer
python -m pmo_studio.cli --root "$ROOT" summary "$SLUG"
