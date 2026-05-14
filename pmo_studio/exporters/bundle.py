"""ZIP bundle exporter for PMO Studio deliverables."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pmo_studio.exporters.docx_export import export_docx
from pmo_studio.exporters.static_html import export_static
from pmo_studio.core.signoff import assert_export_allowed


BUNDLE_INCLUDE_DIRS = [
    "artifacts",
    "traceability",
    "quality",
    "baselines",
    "change-requests",
    "metrics/aggregated",
]


def export_bundle(project_root: Path, profile: str = "client-ready", include_sources: bool = False, force: bool = False) -> Path:
    assert_export_allowed(project_root, force=force)
    html = export_static(project_root)
    docx = export_docx(project_root, profile=profile)
    out_dir = project_root / "exports" / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slug(project_root)
    out = out_dir / f"{slug}-pmo-bundle.zip"
    manifest = _bundle_manifest(project_root, profile=profile, include_sources=include_sources)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bundle-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        for rel_dir in BUNDLE_INCLUDE_DIRS:
            base = project_root / rel_dir
            if base.exists():
                for path in base.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(project_root))
        zf.write(html, html.relative_to(project_root))
        zf.write(docx, docx.relative_to(project_root))
        if include_sources:
            for path in (project_root / "source" / "redacted").glob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(project_root))
    return out


def _slug(project_root: Path) -> str:
    try:
        data = json.loads((project_root / "config.json").read_text(encoding="utf-8"))
        return data.get("project_slug") or project_root.name
    except Exception:
        return project_root.name


def _bundle_manifest(project_root: Path, profile: str, include_sources: bool) -> dict:
    return {
        "project_slug": _slug(project_root),
        "profile": profile,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "include_sources": include_sources,
        "source_policy": "redacted-only" if include_sources else "excluded",
        "contents": BUNDLE_INCLUDE_DIRS + ["exports/management/index.html", f"exports/{profile}/pmo-documentation-pack.docx"],
    }
