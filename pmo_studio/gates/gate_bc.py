"""Gate B/C reviewer hooks.

This module is intentionally provider-agnostic. It can run deterministic local checks now,
and can be wired to OpenRouter/OpenClaw LLM calls by passing an LLMReviewer implementation.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from pmo_studio.gates.gate_a import CheckResult, GateResult
from pmo_studio.rubrics.loader import load_rubric


class LLMReviewer(Protocol):
    def review(self, *, stage: str, layer: str, artifact: str, rubric: list[dict], context: str = "") -> dict:
        ...


@dataclass
class SemanticRubric:
    id: str
    question: str
    blocker: bool = False
    weight: float = 1.0


DEFAULT_RUBRICS = {
    "B": [
        SemanticRubric("no_tbd", "Không còn placeholder/TBD critical?", blocker=True),
        SemanticRubric("clear_scope", "Scope hoặc purpose có mô tả rõ ràng?"),
        SemanticRubric("ids_linked", "Các ID chính có link upstream/downstream?"),
        SemanticRubric("testable", "Requirement/AC có thể kiểm chứng?"),
    ],
    "C": [
        SemanticRubric("ready_for_customer", "Đủ sạch để gửi khách hàng review?", blocker=True, weight=2.0),
        SemanticRubric("ready_for_dev", "Đủ rõ để dev estimate/code?", weight=1.5),
        SemanticRubric("consistency", "Nhất quán với artifact upstream/context?", blocker=True, weight=2.0),
        SemanticRubric("no_open_questions", "Không còn open question critical?", weight=1.5),
    ],
}


def _rubrics_for(stage: str, layer: str) -> list[SemanticRubric]:
    loaded = load_rubric(stage, layer) or {}
    if loaded.get("checks"):
        return [SemanticRubric(c["id"], c.get("question", ""), c.get("blocker", False), float(c.get("weight", 1.0))) for c in loaded["checks"]]
    return DEFAULT_RUBRICS[layer]


def deterministic_review(stage: str, layer: str, artifact_text: str, context: str = "") -> GateResult:
    checks: list[CheckResult] = []
    text_lower = artifact_text.lower()
    rubrics = _rubrics_for(stage, layer)
    for r in rubrics:
        passed = True
        evidence = "Local heuristic pass"
        if r.id in {"no_tbd", "no_open_questions"}:
            hits = re.findall(r"\b(TBD|TODO|FIXME|chưa xác định|cần bổ sung)\b", artifact_text, flags=re.I)
            passed = not hits
            evidence = "No placeholders" if passed else f"Placeholders found: {hits[:5]}"
        elif r.id == "clear_scope":
            passed = any(k in text_lower for k in ["scope", "phạm vi", "purpose", "mục tiêu", "description"])
            evidence = "Scope/purpose term found" if passed else "No clear scope/purpose marker"
        elif r.id == "ids_linked":
            passed = any(k in text_lower for k in ["linked", "link", "source", "req-", "br-"])
            evidence = "Trace marker found" if passed else "No trace marker found"
        elif r.id == "testable":
            passed = any(k in text_lower for k in ["given", "when", "then", "verification", "expected", "acceptance"])
            evidence = "Verification/test marker found" if passed else "No verification/test marker found"
        elif r.id == "ready_for_customer":
            passed = "internal only" not in text_lower and "draft only" not in text_lower
            evidence = "No internal-only marker" if passed else "Internal-only marker found"
        elif r.id == "ready_for_dev":
            passed = any(k in text_lower for k in ["req-", "api-", "scr-", "workflow", "acceptance", "endpoint"])
            evidence = "Implementation markers found" if passed else "No implementation markers"
        elif r.id == "consistency":
            passed = True
            evidence = "Deterministic consistency deferred to traceability engine"
        checks.append(CheckResult(r.id, passed, evidence, r.blocker))
    result = GateResult(stage=stage, layer=layer, checks=checks)
    result.passed = all(c.passed for c in checks if c.blocker) and (sum(1 for c in checks if c.passed) / max(len(checks), 1) >= (0.8 if layer == "B" else 0.9))
    return result


def run_gate_b_or_c(path: Path, stage: str, layer: str, reviewer: LLMReviewer | None = None, context: str = "") -> GateResult:
    if layer not in {"B", "C"}:
        raise ValueError("layer must be B or C")
    artifact = path.read_text(encoding="utf-8", errors="ignore")
    if reviewer is None:
        return deterministic_review(stage, layer, artifact, context)
    rubric = [asdict(r) for r in _rubrics_for(stage, layer)]
    raw = reviewer.review(stage=stage, layer=layer, artifact=artifact, rubric=rubric, context=context)
    checks = [CheckResult(c["id"], c.get("result") in {"Y", "PASS", True}, c.get("evidence", ""), c.get("blocker", False)) for c in raw.get("checks", [])]
    result = GateResult(stage=stage, layer=layer, checks=checks)
    result.passed = bool(raw.get("passed", all(c.passed for c in checks if c.blocker)))
    return result


def save_gate_result(result: GateResult, project_root: Path) -> Path:
    layer_dir = f"gate-{result.layer.lower()}"
    out = project_root / "quality" / layer_dir / f"{result.stage.replace('.', '-')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
