"""Template governance commands."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pmo_studio.templates.renderer import TEMPLATE_ROOT, TEMPLATE_VERSION


def list_versioned_templates() -> list[dict[str, Any]]:
    rows = []
    for path in sorted((TEMPLATE_ROOT / 'ba').rglob('*.tmpl')):
        rel = path.relative_to(TEMPLATE_ROOT).as_posix()
        rows.append({'id': rel.replace('/', '.').replace('.md.tmpl', ''), 'path': rel, 'version': TEMPLATE_VERSION, 'size_bytes': path.stat().st_size})
    return rows


def validate_templates() -> dict[str, Any]:
    required = ['ba/v1/prd.md.tmpl', 'ba/v1/brd.md.tmpl', 'ba/v1/srs.md.tmpl', 'ba/v1/us.md.tmpl', 'ba/v1/test_cases.md.tmpl']
    checks = []
    passed = True
    for rel in required:
        path = TEMPLATE_ROOT / rel
        ok = path.exists() and '{{ template_id }}' in path.read_text(encoding='utf-8', errors='ignore') and '{{ template_version }}' in path.read_text(encoding='utf-8', errors='ignore')
        checks.append({'path': rel, 'passed': bool(ok)})
        passed = passed and bool(ok)
    return {'passed': passed, 'version': TEMPLATE_VERSION, 'checks': checks, 'templates': list_versioned_templates()}
