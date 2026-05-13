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
    ids = re.findall(r"\b(?:SRC|BR|REQ|SCR|API|WF|US|AC|TC|EST)-[A-Z0-9-]+\b", artifact_text)
    headings = re.findall(r"^#{1,4}\s+(.+)$", artifact_text, flags=re.M)
    gwt_count = sum(1 for k in ["given", "when", "then"] if k in text_lower)
    domain_markers = [k for k in ["workflow", "luồng", "phân quyền", "ký", "sla", "integration", "api", "negative", "exception", "risk"] if k in text_lower]
    for r in rubrics:
        passed = True
        evidence = "Local heuristic pass"
        if r.id in {"no_tbd", "no_open_questions"}:
            # Allow explicit workshop/open-question language, but block placeholder debt.
            hits = re.findall(r"\b(TBD|TODO|FIXME|xxx|lorem ipsum|chưa xác định|cần bổ sung)\b", artifact_text, flags=re.I)
            passed = not hits
            evidence = "No placeholder debt found" if passed else f"Placeholder debt: {hits[:5]}"
        elif r.id == "clear_scope":
            markers = [k for k in ["scope", "phạm vi", "purpose", "mục tiêu", "business context", "overview", "description"] if k in text_lower]
            passed = len(markers) >= 1 and len(headings) >= 2
            evidence = f"Scope markers={markers[:4]}, headings={len(headings)}"
        elif r.id == "ids_linked":
            link_markers = [k for k in ["linked", "link", "source", "upstream", "downstream", "stakeholder", "owner", "depends"] if k in text_lower]
            passed = (len(ids) >= 1 and bool(link_markers)) or len(ids) >= 2 or len(domain_markers) >= 2
            evidence = f"ids={ids[:8]}, link_markers={link_markers}, domain_markers={domain_markers[:6]}"
        elif r.id == "testable":
            markers = [k for k in ["given", "when", "then", "verification", "expected", "acceptance", "test case", "scenario", "success metric", "kpi", "review", "approve", "đo", "nghiệm thu"] if k in text_lower]
            passed = gwt_count >= 2 or len(markers) >= 1 or len(domain_markers) >= 2
            evidence = f"testability markers={markers[:8]}, gwt_count={gwt_count}, domain_markers={domain_markers[:6]}"
        elif r.id == "ready_for_customer":
            blockers = [k for k in ["internal only", "draft only", "do not send", "confidential internal"] if k in text_lower]
            passed = not blockers and len(artifact_text.strip()) >= 400
            evidence = "No customer-facing blockers; content length sufficient" if passed else f"Customer blockers/short content: {blockers}, len={len(artifact_text.strip())}"
        elif r.id == "ready_for_dev":
            impl = [k for k in ["req-", "api-", "scr-", "workflow", "acceptance", "endpoint", "error cases", "permission"] if k in text_lower]
            passed = len(impl) >= 2 and len(ids) >= 2
            evidence = f"implementation markers={impl}, ids={ids[:8]}"
        elif r.id == "consistency":
            passed = len(domain_markers) >= 2 or len(ids) >= 3
            evidence = f"domain/consistency markers={domain_markers[:8]}, ids={ids[:8]}"
        checks.append(CheckResult(r.id, passed, evidence, r.blocker))
    result = GateResult(stage=stage, layer=layer, checks=checks)
    threshold = 0.7 if layer == "B" else 0.9
    result.passed = all(c.passed for c in checks if c.blocker) and (sum(1 for c in checks if c.passed) / max(len(checks), 1) >= threshold)
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
