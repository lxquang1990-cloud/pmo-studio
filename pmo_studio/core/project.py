"""Project state, filesystem layout and atomic persistence."""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_ROOT = Path.home() / "pmo-projects"
VALID_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,80}$")


@dataclass
class ProjectConfig:
    project_slug: str
    customer: str = "TBD"
    project_type: str = "new_development"
    domain_pack: str = "bteco"
    traceability_mode: str = "standard"  # lite|standard|strict
    manday_rate_vnd: int = 3_900_000
    enabled_personas: List[str] = field(default_factory=lambda: ["po", "pm", "ba", "ic"])
    governance: Dict[str, Any] = field(default_factory=lambda: {
        "baseline_required": True,
        "formal_cr_after_baseline": True,
        "human_approval_required": True,
    })
    llm: Dict[str, str] = field(default_factory=lambda: {
        "writer_model": "9router/Tier2",
        "reviewer_model": "9router/Tier2",
        "gate_c_model": "9router/Tier2",
    })
    export_profiles: List[str] = field(default_factory=lambda: ["internal", "client-ready", "developer", "management", "implementation"])


@dataclass
class ProjectState:
    version: str = "2.1"
    lifecycle_state: str = "INITIATED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    current_stage: str | None = None
    stages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    id_counters: Dict[str, int] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)


class Project:
    def __init__(self, root: Path, config: ProjectConfig, state: ProjectState | None = None):
        self.root = root
        self.config = config
        self.state = state or ProjectState()

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    @property
    def config_path(self) -> Path:
        return self.root / "config.json"

    @classmethod
    def create(cls, slug: str, customer: str = "TBD", root_base: Path = DEFAULT_ROOT, **kwargs: Any) -> "Project":
        if not VALID_SLUG.match(slug):
            raise ValueError("project_slug must match ^[a-z0-9][a-z0-9-]{1,80}$")
        root = root_base / slug
        root.mkdir(parents=True, exist_ok=True)
        config = ProjectConfig(project_slug=slug, customer=customer, **kwargs)
        project = cls(root, config)
        project.ensure_layout()
        project.save()
        try:
            from pmo_studio.core.registry import register_project
            register_project(project, root_base=root_base)
        except Exception:
            pass
        return project

    @classmethod
    def load(cls, slug_or_path: str | Path, root_base: Path = DEFAULT_ROOT) -> "Project":
        path = Path(slug_or_path)
        root = path if path.exists() and path.is_dir() else root_base / str(slug_or_path)
        config = ProjectConfig(**json.loads((root / "config.json").read_text()))
        state = ProjectState(**json.loads((root / "state.json").read_text()))
        return cls(root, config, state)

    def ensure_layout(self) -> None:
        dirs = [
            "source/uploads", "source/redacted", "source/transcripts", "source/screenshots", "source/web-crawl",
            "artifacts/stage-0", "artifacts/po", "artifacts/pm", "artifacts/ba", "artifacts/ic",
            "traceability/views", "quality/gate-a", "quality/gate-b", "quality/gate-c",
            "baselines", "change-requests", "exports/client-ready", "exports/internal", "exports/developer", "exports/management", "exports/implementation",
            "metrics/runs", "metrics/aggregated", "logs",
        ]
        for d in dirs:
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def atomic_write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            if path.exists():
                shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def save(self) -> None:
        self.state.updated_at = datetime.now(timezone.utc).isoformat()
        self.atomic_write_json(self.config_path, asdict(self.config))
        self.atomic_write_json(self.state_path, asdict(self.state))
        try:
            from pmo_studio.core.registry import register_project
            register_project(self, root_base=self.root.parent)
        except Exception:
            pass

    def mark_stage(self, stage_id: str, status: str, **extra: Any) -> None:
        current = self.state.stages.get(stage_id, {})
        current.update(extra)
        current["status"] = status
        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state.stages[stage_id] = current
        self.state.current_stage = stage_id
        self.save()
