"""Project registry helpers for PMO Studio."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pmo_studio.core.project import DEFAULT_ROOT, Project


@dataclass
class RegistryEntry:
    slug: str
    customer: str
    root: str
    lifecycle_state: str
    current_stage: str | None
    created_at: str
    updated_at: str


def registry_path(root_base: Path = DEFAULT_ROOT) -> Path:
    return root_base / ".pmo-studio-registry.json"


def register_project(project: Project, root_base: Path = DEFAULT_ROOT) -> Path:
    data = _load(root_base)
    data[project.config.project_slug] = asdict(_entry(project))
    return _save(root_base, data)


def refresh_registry(root_base: Path = DEFAULT_ROOT) -> Path:
    data: dict[str, Any] = {}
    root_base.mkdir(parents=True, exist_ok=True)
    for config in root_base.glob("*/config.json"):
        try:
            p = Project.load(config.parent)
            data[p.config.project_slug] = asdict(_entry(p))
        except Exception:
            continue
    return _save(root_base, data)


def list_projects(root_base: Path = DEFAULT_ROOT, refresh: bool = False, include_archived: bool = False) -> list[RegistryEntry]:
    if refresh or not registry_path(root_base).exists():
        refresh_registry(root_base)
    data = _load(root_base)
    entries = [RegistryEntry(**v) for v in data.values()]
    if not include_archived:
        entries = [e for e in entries if e.lifecycle_state != "ARCHIVED"]
    return sorted(entries, key=lambda e: e.updated_at, reverse=True)


def recent_project(root_base: Path = DEFAULT_ROOT) -> RegistryEntry | None:
    entries = list_projects(root_base)
    return entries[0] if entries else None


def _entry(project: Project) -> RegistryEntry:
    return RegistryEntry(
        slug=project.config.project_slug,
        customer=project.config.customer,
        root=str(project.root),
        lifecycle_state=project.state.lifecycle_state,
        current_stage=project.state.current_stage,
        created_at=project.state.created_at,
        updated_at=project.state.updated_at or datetime.now(timezone.utc).isoformat(),
    )


def _load(root_base: Path) -> dict[str, Any]:
    path = registry_path(root_base)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(root_base: Path, data: dict[str, Any]) -> Path:
    root_base.mkdir(parents=True, exist_ok=True)
    path = registry_path(root_base)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
