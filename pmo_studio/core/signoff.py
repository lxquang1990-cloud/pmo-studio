"""Human sign-off workflow and export-lock governance."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pmo_studio.core.project import Project

APPROVAL_ROLES = ["PO", "PM", "BA", "IC", "Quotation", "Final"]

@dataclass
class SignoffEntry:
    role: str
    status: str
    approved_by: str
    note: str
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def signoff_path(project: Project | Path) -> Path:
    root = project.root if isinstance(project, Project) else Path(project)
    return root / "review" / "signoff.json"


def load_signoff(project: Project) -> dict:
    path = signoff_path(project)
    if not path.exists():
        return {"locked": False, "approvals": {}, "history": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"locked": False, "approvals": {}, "history": []}


def update_signoff(project: Project, role: str, status: str, approved_by: str = "Snail", note: str = "") -> Path:
    role = _normalize_role(role)
    status = status.lower()
    if status not in {"approved", "rejected", "pending"}:
        raise ValueError("status must be approved|rejected|pending")
    data = load_signoff(project)
    entry = SignoffEntry(role, status, approved_by, note)
    data.setdefault("approvals", {})[role] = asdict(entry)
    data.setdefault("history", []).append(asdict(entry))
    data["locked"] = _is_locked(data)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = signoff_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def export_locked(project_root: Path) -> bool:
    path = project_root / "review" / "signoff.json"
    if not path.exists():
        return False
    try:
        return bool(json.loads(path.read_text(encoding="utf-8")).get("locked"))
    except Exception:
        return False


def assert_export_allowed(project_root: Path, force: bool = False) -> None:
    if export_locked(project_root) and not force:
        raise RuntimeError("Project export is locked after final sign-off. Use --force only for an explicit re-export.")


def _normalize_role(role: str) -> str:
    lookup = {r.lower(): r for r in APPROVAL_ROLES}
    return lookup.get(role.lower(), role)


def _is_locked(data: dict) -> bool:
    final = data.get("approvals", {}).get("Final", {})
    return final.get("status") == "approved"
