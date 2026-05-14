"""Artifact manifest with source/template/domain/generator hashes."""
from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

from pmo_studio import __version__
from pmo_studio.domain.pack_loader import PACK_DIR
from pmo_studio.templates.renderer import TEMPLATE_ROOT


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _hash_tree(root: Path, suffixes: tuple[str, ...]) -> str:
    h = hashlib.sha256()
    if not root.exists():
        return ""
    for path in sorted(p for p in root.rglob('*') if p.is_file() and p.suffix in suffixes):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(sha256_file(path).encode())
    return h.hexdigest()


def write_artifact_manifest(project_root: Path) -> Path:
    config = _json(project_root / 'config.json') or {}
    detection = _json(project_root / 'artifacts/stage-0/domain-detection.json') or {}
    domain = detection.get('selected_domain') or config.get('domain_pack') or 'generic'
    source_files = sorted((project_root / 'source/redacted').rglob('*')) if (project_root / 'source/redacted').exists() else []
    artifacts = []
    for path in sorted((project_root / 'artifacts').rglob('*')) if (project_root / 'artifacts').exists() else []:
        if path.is_file():
            rel = path.relative_to(project_root).as_posix()
            artifacts.append({'path': rel, 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size})
    manifest = {
        'schema': 'pmo.artifact_manifest.v1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'project_slug': config.get('project_slug', project_root.name),
        'generator_version': __version__,
        'domain_pack': domain,
        'domain_pack_hash': sha256_file(PACK_DIR / f'{domain}.yaml') if (PACK_DIR / f'{domain}.yaml').exists() else '',
        'template_tree_hash': _hash_tree(TEMPLATE_ROOT / 'ba/v1', ('.tmpl',)),
        'source_hash': _hash_tree(project_root / 'source/redacted', ('.md', '.txt', '.json')),
        'sources': [{'path': p.relative_to(project_root).as_posix(), 'sha256': sha256_file(p), 'size_bytes': p.stat().st_size} for p in source_files if p.is_file()],
        'artifacts': artifacts,
    }
    out = project_root / 'artifacts/manifest.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out


def _json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
