#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/tmp/pmo-smoke-phase11}"
PROJECT="phase11-smoke"
SRC="${ROOT}-source.md"

cd "$(dirname "$0")/.."

python -m compileall -q pmo_studio
rm -rf "$ROOT" "$SRC"
cat > "$SRC" <<'EOF'
Khách hàng cần eOffice quản lý văn bản, duyệt đa cấp, dashboard SLA, báo cáo quá hạn.
token=should_be_redacted_phase11
EOF

python -m pmo_studio.cli --root "$ROOT" scaffold
python -m pmo_studio.cli --root "$ROOT" init "$PROJECT" --customer 'Phase11 Smoke Customer' --source "$SRC"
python -m pmo_studio.cli --root "$ROOT" list --refresh
python -m pmo_studio.cli --root "$ROOT" generate all --from-sources --llm noop --refine --max-refine 2
python -m pmo_studio.cli --root "$ROOT" trace --validate
python -m pmo_studio.cli --root "$ROOT" run-gates
python -m pmo_studio.cli --root "$ROOT" export --format zip --include-redacted-sources
python -m pmo_studio.cli --root "$ROOT" doctor

python - <<PY
from pathlib import Path
import json, zipfile
root = Path('$ROOT') / '$PROJECT'
validation = json.loads((root/'traceability/views/validation.json').read_text())
summary = json.loads((root/'quality/summary.json').read_text())
zip_path = next((root/'exports/client-ready').glob('*.zip'))
with zipfile.ZipFile(zip_path) as zf:
    names = zf.namelist()
assert validation['passed'], validation
assert summary['failed'] == 0, summary
assert 'bundle-manifest.json' in names
assert any(n.endswith('pmo-documentation-pack.docx') for n in names)
assert not any(n.startswith('source/uploads') for n in names)
assert any(n.startswith('source/redacted') for n in names)
print('SMOKE_PHASE11_PASS', zip_path)
PY
