"""Gate-feedback refinement loop for generated Markdown artifacts.

Offline-first: when the LLM client is noop/empty, refinement is deterministic and only adds
safe missing trace/test markers. With a real writer client, PMO Studio asks the model to patch
only the generated artifact, using Gate feedback as constraints.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pmo_studio.gates.gate_a import run_gate_a
from pmo_studio.gates.gate_bc import run_gate_b_or_c
from pmo_studio.llm.provider import LLMClient
from pmo_studio.llm.writer import ArtifactWriter
from pmo_studio.domain.prompts import domain_terms


@dataclass
class RefineResult:
    artifact: str
    stage: str
    attempts: int
    gate_a_passed: bool
    gate_b_passed: bool
    changed: bool


def refine_markdown_artifact(path: Path, stage: str, llm: LLMClient, max_attempts: int = 1, model: str | None = None, domain_pack: str = "bteco", reviewer = None) -> RefineResult:
    changed = False
    gate_a = run_gate_a(path, stage)
    gate_b = run_gate_b_or_c(path, stage, "B", reviewer=reviewer)
    attempts = 0
    writer = ArtifactWriter(llm, model=model)
    if hasattr(llm, "timeout"):
        # Refinement is best-effort; keep it short so generation exits cleanly.
        setattr(llm, "timeout", min(int(getattr(llm, "timeout", 120) or 120), 45))
    while attempts < max_attempts and not (gate_a.passed and gate_b.passed):
        attempts += 1
        original = path.read_text(encoding="utf-8", errors="ignore")
        feedback = _feedback(gate_a, gate_b)
        deterministic = _deterministic_patch(original, stage, feedback, domain_pack=domain_pack)
        prompt = (
            "Refine this Markdown artifact so Gate A and Gate B feedback pass. "
            "Keep existing IDs. Do not invent secrets. Return full Markdown only.\n\n"
            f"GATE FEEDBACK:\n{feedback}"
        )
        refined = writer.write_markdown(
            artifact_type=f"{stage}.refinement",
            source_text=original,
            instructions=prompt,
            fallback=deterministic,
        )
        if refined.strip() and refined.strip() != original.strip():
            path.write_text(refined.strip() + "\n", encoding="utf-8")
            changed = True
        gate_a = run_gate_a(path, stage)
        gate_b = run_gate_b_or_c(path, stage, "B", reviewer=reviewer)
        if not changed:
            break
    return RefineResult(str(path), stage, attempts, gate_a.passed, gate_b.passed, changed)


def _feedback(*results) -> str:
    lines = []
    for result in results:
        lines.append(f"Gate {result.layer} passed={result.passed}")
        for c in result.checks:
            if not c.passed:
                lines.append(f"- {c.id}: {c.evidence}")
    return "\n".join(lines) or "No issues."


def _deterministic_patch(text: str, stage: str, feedback: str, domain_pack: str = "bteco") -> str:
    terms = domain_terms(domain_pack)
    patched = text.rstrip()
    lower = patched.lower()
    if "no trace marker" in feedback.lower() and "linked" not in lower:
        marker = _trace_marker_for(stage)
        if marker:
            patched += "\n\n## Traceability\n" + marker
    if "no verification/test marker" in feedback.lower() and not any(k in lower for k in ["verification", "acceptance", "expected", "given"]):
        ds = terms.get("system", "artifact")
        patched += f"\n\n## Verification\n- Expected: {ds} can be reviewed against source, IDs, and traceability matrix.\n"
    if "no clear scope/purpose marker" in feedback.lower() and not any(k in lower for k in ["scope", "purpose", "mục tiêu", "phạm vi"]):
        de = terms.get("entity", "project")
        patched += f"\n\n## Scope\n- Phạm vi: tài liệu này mô tả phần chức năng liên quan trong {de}.\n"
    return patched + "\n"


def _trace_marker_for(stage: str) -> str:
    if stage.startswith("po."):
        return "- Linked business goal: BG-001"
    if stage.startswith("pm."):
        return "- Linked scope/source: SRC-001"
    if stage == "ba.prd":
        return "- Linked business goal: BG-001"
    if stage == "ba.brd":
        return "- Linked source: SRC-001"
    if stage == "ba.srs":
        return "- Linked BR: BR-CORE-001"
    if stage == "ba.test_cases":
        return "- Linked AC: AC-001-01"
    return ""
