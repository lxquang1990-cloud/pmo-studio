"""Customer-ready review mode for PMO Studio.

Produces a practical review dashboard, artifact-level findings, suggested fixes,
and regeneration guidance without mutating generated artifacts.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pmo_studio.quality.intelligence import analyze_project_quality

REVIEW_TARGETS = {
    "prd": "artifacts/ba/01-prd.md",
    "brd": "artifacts/ba/02-brd.md",
    "srs": "artifacts/ba/03-srs/srs.md",
    "user_stories": "artifacts/ba/04-user-stories.md",
    "test_cases": "artifacts/ba/05-test-cases.md",
    "uat_plan": "artifacts/ic/04-uat-plan.md",
    "charter": "artifacts/pm/01-charter.md",
    "vision": "artifacts/po/01-vision.md",
}

@dataclass
class CustomerReviewFinding:
    id: str
    severity: str
    artifact_key: str
    artifact_path: str
    message: str
    suggested_fix: str
    evidence: str = ""

@dataclass
class ArtifactReview:
    key: str
    path: str
    exists: bool
    score: int
    findings: list[CustomerReviewFinding] = field(default_factory=list)

@dataclass
class CustomerReviewReport:
    schema: str
    created_at: str
    project_slug: str
    score: int
    readiness: str
    artifacts: list[ArtifactReview]
    suggested_regenerations: list[dict[str, str]]


def run_customer_review(project_root: Path) -> CustomerReviewReport:
    artifacts = [_review_artifact(project_root, key, rel) for key, rel in REVIEW_TARGETS.items()]
    qi = analyze_project_quality(project_root)
    for finding in qi.findings:
        artifacts.append(ArtifactReview("quality_intelligence", "quality/intelligence.json", True, max(0, 100 - _penalty(finding.severity)), [CustomerReviewFinding(finding.id, finding.severity, "quality_intelligence", finding.artifact or "all", finding.message, _suggestion_for_quality(finding.id), finding.evidence)]))
    all_findings = [f for a in artifacts for f in a.findings]
    score = max(0, 100 - sum(_penalty(f.severity) for f in all_findings))
    readiness = "READY" if score >= 90 and not any(f.severity == "high" for f in all_findings) else "NEEDS_REVIEW" if score >= 70 else "NOT_READY"
    suggested = _suggested_regenerations(all_findings)
    return CustomerReviewReport("pmo.customer_review.v1", datetime.now(timezone.utc).isoformat(), project_root.name, score, readiness, artifacts, suggested)


def write_customer_review(project_root: Path) -> Path:
    report = run_customer_review(project_root)
    out = project_root / "quality" / "customer-review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = project_root / "quality" / "customer-review.md"
    md.write_text(render_customer_review_markdown(report), encoding="utf-8")
    html = project_root / "quality" / "customer-review.html"
    html.write_text(render_customer_review_html(report), encoding="utf-8")
    return out


def render_customer_review_markdown(report: CustomerReviewReport) -> str:
    lines = [f"# Customer-ready Review: {report.project_slug}", "", f"- Readiness: **{report.readiness}**", f"- Score: **{report.score}/100**", f"- Findings: **{sum(len(a.findings) for a in report.artifacts)}**", "", "## Artifact Dashboard", "", "| Artifact | Exists | Score | Findings |", "|---|---:|---:|---:|"]
    for a in report.artifacts:
        lines.append(f"| {a.key} | {a.exists} | {a.score} | {len(a.findings)} |")
    lines.extend(["", "## Findings", ""])
    findings = [f for a in report.artifacts for f in a.findings]
    if not findings:
        lines.append("No customer-readiness issues found.")
    else:
        lines.extend(["| ID | Severity | Artifact | Message | Suggested fix |", "|---|---|---|---|---|"])
        for f in findings:
            lines.append(f"| {f.id} | {f.severity} | {f.artifact_key} | {f.message} | {f.suggested_fix} |")
    lines.extend(["", "## Suggested Regenerations", ""])
    if not report.suggested_regenerations:
        lines.append("No targeted regeneration needed.")
    else:
        for item in report.suggested_regenerations:
            lines.append(f"- `{item['artifact_key']}`: {item['reason']} — `{item['command']}`")
    lines.append("")
    return "\n".join(lines)


def render_customer_review_html(report: CustomerReviewReport) -> str:
    md = render_customer_review_markdown(report)
    body = "\n".join(f"<p>{_inline(line)}</p>" if line and not line.startswith("|") and not line.startswith("#") and not line.startswith("-") else f"<pre>{_inline(line)}</pre>" for line in md.splitlines())
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Customer Review</title><style>body{{font-family:Arial,sans-serif;margin:32px;max-width:1100px}}pre{{background:#f6f8fa;padding:6px}}</style></head><body>{body}</body></html>"


def _review_artifact(project_root: Path, key: str, rel: str) -> ArtifactReview:
    path = project_root / rel
    if not path.exists():
        f = CustomerReviewFinding(f"CR-{key.upper()}-MISSING", "high", key, rel, "Expected customer artifact is missing.", f"Regenerate {key} or run `pmo generate <slug> all --from-sources --llm noop`.")
        return ArtifactReview(key, rel, False, 0, [f])
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[CustomerReviewFinding] = []
    if len(text.strip()) < 500:
        findings.append(CustomerReviewFinding(f"CR-{key.upper()}-SHORT", "medium", key, rel, "Artifact may be too short for customer review.", "Expand scope, workflow, assumptions, and acceptance details.", f"length={len(text.strip())}"))
    placeholders = re.findall(r"\b(TBD|TODO|FIXME|lorem ipsum|chưa xác định|cần bổ sung)\b", text, flags=re.I)
    if placeholders:
        findings.append(CustomerReviewFinding(f"CR-{key.upper()}-PLACEHOLDER", "high", key, rel, "Customer-facing placeholder text remains.", "Replace placeholders with explicit assumptions, exclusions, or confirmed values.", ", ".join(placeholders[:8])))
    if "{{" in text or "}}" in text:
        findings.append(CustomerReviewFinding(f"CR-{key.upper()}-TEMPLATE", "high", key, rel, "Unrendered template token remains.", "Fix template context and regenerate this artifact."))
    if key in {"srs", "brd", "prd"} and not re.search(r"\b(assumption|giả định|out of scope|ngoài phạm vi|scope|phạm vi)\b", text, flags=re.I):
        findings.append(CustomerReviewFinding(f"CR-{key.upper()}-SCOPE", "medium", key, rel, "Scope/assumption boundaries are not explicit.", "Add assumptions, exclusions, and Phase 2 boundaries."))
    if key in {"user_stories", "test_cases", "uat_plan"} and not re.search(r"\b(Given|When|Then|Expected|Acceptance|AC-|TC-|nghiệm thu)\b", text, flags=re.I):
        findings.append(CustomerReviewFinding(f"CR-{key.upper()}-TESTABILITY", "medium", key, rel, "Testability cues are weak or missing.", "Add Given/When/Then, expected results, and AC/TC links."))
    score = max(0, 100 - sum(_penalty(f.severity) for f in findings))
    return ArtifactReview(key, rel, True, score, findings)


def _suggested_regenerations(findings: list[CustomerReviewFinding]) -> list[dict[str, str]]:
    out = []
    seen = set()
    for f in findings:
        if f.artifact_key in seen or f.artifact_key == "quality_intelligence":
            continue
        if f.severity in {"high", "medium"}:
            seen.add(f.artifact_key)
            out.append({"artifact_key": f.artifact_key, "reason": f.message, "command": "pmo generate <slug> all --from-sources --llm noop --no-refine && pmo customer-review <slug>"})
    return out


def _suggestion_for_quality(finding_id: str) -> str:
    if "TRACE" in finding_id:
        return "Run trace validation and fix missing upstream/downstream links."
    if "DOMAIN" in finding_id:
        return "Confirm domain detection and regenerate with the correct domain pack."
    if "TEMPLATE" in finding_id:
        return "Fix template context and regenerate affected artifacts."
    return "Review source coverage and regenerate targeted artifacts."


def _penalty(severity: str) -> int:
    return {"high": 25, "medium": 12, "low": 5}.get(severity, 5)


def _inline(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
