"""Run all configured quality gates and write project summary."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pmo_studio.core.project import Project
from pmo_studio.gates.gate_a import run_gate_a, save_gate_result as save_gate_a
from pmo_studio.gates.gate_bc import run_gate_b_or_c, save_gate_result as save_gate_bc


@dataclass
class GateTarget:
    stage: str
    artifact: str
    layers: list[str]


DEFAULT_TARGETS = [
    GateTarget("stage-0.project_brief", "artifacts/stage-0/project-brief.md", ["A"]),
    GateTarget("po.vision", "artifacts/po/01-vision.md", ["A", "B"]),
    GateTarget("pm.charter", "artifacts/pm/01-charter.md", ["A", "B"]),
    GateTarget("ba.prd", "artifacts/ba/01-prd.md", ["A", "B"]),
    GateTarget("ba.brd", "artifacts/ba/02-brd.md", ["A", "B"]),
    GateTarget("ba.srs", "artifacts/ba/03-srs/srs.md", ["A", "B"]),
    GateTarget("ba.test_cases", "artifacts/ba/05-test-cases.md", ["A"]),
    GateTarget("ba.quotation", "artifacts/ba/06-quotation.xlsx", ["A"]),
    GateTarget("ic.fit_gap", "artifacts/ic/01-fit-gap.xlsx", ["A"]),
    GateTarget("ic.config_workbook", "artifacts/ic/02-config-workbook.xlsx", ["A"]),
    GateTarget("ic.deployment_plan", "artifacts/ic/03-deployment-plan.md", ["A"]),
    GateTarget("ic.uat_plan", "artifacts/ic/04-uat-plan.md", ["A"]),
]


def run_all_gates(project: Project, include_c: bool = False, reviewer = None) -> dict:
    results = []
    for target in DEFAULT_TARGETS:
        artifact = project.root / target.artifact
        if not artifact.exists():
            results.append({"stage": target.stage, "artifact": target.artifact, "layer": "-", "passed": False, "skipped": True, "reason": "missing artifact"})
            continue
        layers = list(target.layers)
        if include_c and artifact.suffix.lower() == ".md":
            layers.append("C")
        for layer in layers:
            if layer == "A":
                r = run_gate_a(artifact, target.stage); out = save_gate_a(r, project.root)
            else:
                r = run_gate_b_or_c(artifact, target.stage, layer, reviewer=reviewer); out = save_gate_bc(r, project.root)
            results.append({"stage": target.stage, "artifact": target.artifact, "layer": layer, "passed": r.passed, "result_path": str(out.relative_to(project.root)), "check_count": len(r.checks)})
    summary = {
        "project_slug": project.config.project_slug,
        "total": len(results),
        "passed": sum(1 for r in results if r.get("passed")),
        "failed": sum(1 for r in results if not r.get("passed") and not r.get("skipped")),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "results": results,
    }
    out = project.root / "quality" / "summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary
