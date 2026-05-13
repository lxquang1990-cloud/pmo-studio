#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/tmp/pmo-benchmark}"
cd "$(dirname "$0")/.."

python -m compileall -q pmo_studio
rm -rf "$ROOT"
python -m pmo_studio.cli --root "$ROOT" scaffold
python -m pmo_studio.cli --root "$ROOT" eval --benchmark --no-docx

python - <<PY
from pathlib import Path
import json
root = Path('$ROOT') / 'eval-runs' / 'benchmark'
results = json.loads((root/'results.json').read_text())
assert results['passed'], results
assert results['score'] >= 0.9, results['score']
print('BENCHMARK_PASS', results['score'], root/'report.md')
PY
