#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/tmp/pmo-install-check}"
VENV="${ROOT}-venv"
cd "$(dirname "$0")/.."

rm -rf "$ROOT" "$VENV"
python -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip >/tmp/pmo-install-check-pip.log
"$VENV/bin/python" -m pip install -e . >>/tmp/pmo-install-check-pip.log
"$VENV/bin/pmo" --help >/tmp/pmo-install-check-help.txt
"$VENV/bin/pmo-studio" --help >/tmp/pmo-install-check-help-alias.txt

"$VENV/bin/pmo" --root "$ROOT" scaffold
"$VENV/bin/pmo" --root "$ROOT" init install-check --customer 'Install Check'
"$VENV/bin/pmo" --root "$ROOT" generate install-check all --from-sources --llm noop --refine
"$VENV/bin/pmo" --root "$ROOT" trace install-check --validate
"$VENV/bin/pmo" --root "$ROOT" run-gates install-check
"$VENV/bin/pmo" --root "$ROOT" export install-check --format zip

python - <<PY
from pathlib import Path
root = Path('$ROOT') / 'install-check'
assert (root/'exports/client-ready/install-check-pmo-bundle.zip').exists()
assert (root/'quality/summary.json').exists()
assert (root/'traceability/views/validation.json').exists()
print('INSTALL_CHECK_PASS', root)
PY
