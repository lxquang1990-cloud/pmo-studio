"""Project lifecycle and UX helpers."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pmo_studio.core.project import Project, VALID_SLUG
from pmo_studio.core.registry import register_project, refresh_registry

LIFECYCLE_ORDER = ["INITIATED", "GENERATED", "GATED", "EXPORTED", "BASELINED", "ARCHIVED"]


@dataclass
class ProjectSummary:
    slug: str
    customer: str
    state: str
    current_stage: str | None
    artifact_count: int
    gate_total: int
    gate_passed: int
    gate_failed: int
    trace_passed: bool | None
    trace_nodes: int | None
    trace_edges: int | None
    latest_export: str | None
    root: str


def set_lifecycle(project: Project, state: str) -> None:
    state = state.upper()
    if state not in LIFECYCLE_ORDER:
        raise ValueError(f"Invalid lifecycle state: {state}")
    project.state.lifecycle_state = state
    project.save()


def infer_lifecycle(project: Project) -> str:
    if project.state.lifecycle_state == "ARCHIVED":
        return "ARCHIVED"
    if any((project.root / "baselines").glob("*/manifest.json")):
        return "BASELINED"
    if any((project.root / "exports").rglob("*.zip")) or any((project.root / "exports").rglob("*.docx")):
        return "EXPORTED"
    q = _json(project.root / "quality" / "summary.json")
    if q and q.get("failed") == 0 and q.get("total", 0) > 0:
        return "GATED"
    if any((project.root / "artifacts").rglob("*")):
        artifact_files = [p for p in (project.root / "artifacts").rglob("*") if p.is_file()]
        if len(artifact_files) > 1:
            return "GENERATED"
    return "INITIATED"


def sync_lifecycle(project: Project) -> str:
    state = infer_lifecycle(project)
    project.state.lifecycle_state = state
    project.save()
    return state


def summarize_project(project: Project, sync: bool = True) -> ProjectSummary:
    if sync:
        sync_lifecycle(project)
    quality = _json(project.root / "quality" / "summary.json") or {}
    trace = _json(project.root / "traceability" / "views" / "validation.json") or {}
    artifacts = [p for p in (project.root / "artifacts").rglob("*") if p.is_file()] if (project.root / "artifacts").exists() else []
    latest_export = _latest_export(project.root)
    return ProjectSummary(
        slug=project.config.project_slug,
        customer=project.config.customer,
        state=project.state.lifecycle_state,
        current_stage=project.state.current_stage,
        artifact_count=len(artifacts),
        gate_total=int(quality.get("total", 0) or 0),
        gate_passed=int(quality.get("passed", 0) or 0),
        gate_failed=int(quality.get("failed", 0) or 0),
        trace_passed=trace.get("passed") if trace else None,
        trace_nodes=trace.get("node_count") if trace else None,
        trace_edges=trace.get("edge_count") if trace else None,
        latest_export=str(latest_export) if latest_export else None,
        root=str(project.root),
    )


def archive_project(project: Project, reason: str = "", move: bool = False) -> Path:
    project.state.lifecycle_state = "ARCHIVED"
    project.state.stages.setdefault("archive", {})
    project.state.stages["archive"].update({"status": "completed", "reason": reason, "updated_at": datetime.now(timezone.utc).isoformat()})
    project.save()
    marker = project.root / "ARCHIVED.md"
    marker.write_text(f"# Archived\n\nReason: {reason or 'N/A'}\nTime: {datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8")
    if move:
        archive_dir = project.root.parent / "_archived"
        archive_dir.mkdir(parents=True, exist_ok=True)
        dest = archive_dir / project.root.name
        if dest.exists():
            raise FileExistsError(dest)
        shutil.move(str(project.root), str(dest))
        refresh_registry(project.root.parent)
        return dest
    register_project(project, root_base=project.root.parent)
    return project.root


def clone_project(source: Project, new_slug: str, customer: str | None = None) -> Project:
    if not VALID_SLUG.match(new_slug):
        raise ValueError("new_slug must match ^[a-z0-9][a-z0-9-]{1,80}$")
    dest = source.root.parent / new_slug
    if dest.exists():
        raise FileExistsError(dest)
    ignore = shutil.ignore_patterns("baselines", "change-requests", "metrics", "logs", "exports", "*.bak", "__pycache__")
    shutil.copytree(source.root, dest, ignore=ignore)
    p = Project.load(dest)
    p.config.project_slug = new_slug
    if customer:
        p.config.customer = customer
    p.state.lifecycle_state = "INITIATED"
    p.state.current_stage = "cloned"
    p.state.stages["clone"] = {"status": "completed", "source": str(source.root), "updated_at": datetime.now(timezone.utc).isoformat()}
    p.save()
    register_project(p, root_base=source.root.parent)
    return p


def summary_markdown(summary: ProjectSummary) -> str:
    trace = "chưa chạy" if summary.trace_passed is None else f"{'PASS' if summary.trace_passed else 'WARN'} ({summary.trace_nodes} nodes/{summary.trace_edges} edges)"
    quality = "chưa chạy" if summary.gate_total == 0 else f"{summary.gate_passed}/{summary.gate_total} passed, failed={summary.gate_failed}"
    export = summary.latest_export or "chưa có"
    return (
        f"# PMO Summary: {summary.slug}\n\n"
        f"- Customer: {summary.customer}\n"
        f"- Lifecycle: {summary.state}\n"
        f"- Current stage: {summary.current_stage}\n"
        f"- Artifacts: {summary.artifact_count}\n"
        f"- Quality: {quality}\n"
        f"- Traceability: {trace}\n"
        f"- Latest export: `{export}`\n"
        f"- Root: `{summary.root}`\n"
    )


def _json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_export(root: Path) -> Path | None:
    exports = [p for p in (root / "exports").rglob("*") if p.is_file()] if (root / "exports").exists() else []
    if not exports:
        return None
    return max(exports, key=lambda p: p.stat().st_mtime)
