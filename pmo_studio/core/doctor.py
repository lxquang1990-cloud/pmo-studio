"""PMO Studio environment and project doctor."""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from pmo_studio.core.project import Project
from pmo_studio.llm.provider import api_key_status
from pmo_studio.rubrics.loader import rubric_path


@dataclass
class DoctorCheck:
    id: str
    passed: bool
    evidence: str


def run_doctor(project: Project | None = None) -> dict:
    checks: list[DoctorCheck] = []
    checks.append(DoctorCheck("python.version", sys.version_info >= (3, 11), sys.version.split()[0]))
    for mod in ["openpyxl", "docx", "yaml"]:
        checks.append(DoctorCheck(f"dep.{mod}", importlib.util.find_spec(mod) is not None, "installed" if importlib.util.find_spec(mod) else "missing"))
    nine_status = api_key_status().get("9router", "not set")
    checks.append(DoctorCheck("llm.9router_key", nine_status.startswith("set"), nine_status if nine_status.startswith("set") else "not set (OK for --llm noop)"))
    for stage in ["ba.srs", "ba.brd", "ba.quotation", "ic.fit_gap", "ic.config_workbook"]:
        for layer in ["A", "B", "C"]:
            p = rubric_path(stage, layer)
            checks.append(DoctorCheck(f"rubric.{stage}.{layer}", p.exists(), str(p)))
    if project:
        checks.append(DoctorCheck("project.root", project.root.exists(), str(project.root)))
        checks.append(DoctorCheck("project.config", project.config_path.exists(), str(project.config_path)))
        checks.append(DoctorCheck("project.state", project.state_path.exists(), str(project.state_path)))
        checks.append(DoctorCheck("project.artifacts", (project.root / "artifacts").exists(), str(project.root / "artifacts")))
        checks.append(DoctorCheck("project.ignore", (project.root / ".pmo-studioignore").exists(), str(project.root / ".pmo-studioignore")))
    return {"passed": all(c.passed or c.id == "llm.9router_key" for c in checks), "checks": [asdict(c) for c in checks]}
