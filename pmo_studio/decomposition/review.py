"""Decomposition Review Mode (v3.2)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from pmo_studio.decomposition.engine import load_decomposition, write_decomposition

@dataclass
class ReviewQuestion:
    id: str
    severity: str
    target: str
    question: str
    rationale: str

@dataclass
class DecompositionReviewReport:
    schema: str
    created_at: str
    project_slug: str
    readiness: str
    score: int
    questions: list[ReviewQuestion]


def run_decomposition_review(project_root: Path) -> DecompositionReviewReport:
    report = load_decomposition(project_root)
    if report is None:
        write_decomposition(project_root)
        report = load_decomposition(project_root)
    assert report is not None
    questions: list[ReviewQuestion] = []
    q = 1
    for cap in report.capabilities:
        questions.append(ReviewQuestion(f"DR-{q:03d}", "medium", cap.id, f"Capability '{cap.name}' có đúng ranh giới nghiệp vụ khách hàng mong muốn không?", "Capability boundary sai sẽ kéo sai SRS/estimate.")); q += 1
        for feat in cap.features:
            if feat.gaps:
                questions.append(ReviewQuestion(f"DR-{q:03d}", "high", feat.id, f"Feature '{feat.name}' còn gap: {'; '.join(feat.gaps[:3])}. Xác nhận bổ sung hay loại khỏi scope?", "Gap ở decomposition cần chốt trước quotation.")); q += 1
            questions.append(ReviewQuestion(f"DR-{q:03d}", "low", feat.id, f"Feature '{feat.name}' có thiếu role, trạng thái workflow, report/export hoặc integration nào không?", "BA review giúp bắt thiếu nghiệp vụ trước khi sinh test/UAT.")); q += 1
    score = max(0, report.score - sum(10 for x in questions if x.severity == "high") - sum(3 for x in questions if x.severity == "medium"))
    readiness = "READY_FOR_CUSTOMER_REVIEW" if score >= 85 else "NEEDS_BA_REVIEW" if score >= 65 else "NOT_READY"
    return DecompositionReviewReport("pmo.decomposition_review.v1", datetime.now(timezone.utc).isoformat(), project_root.name, readiness, score, questions)


def write_decomposition_review(project_root: Path) -> Path:
    r = run_decomposition_review(project_root)
    out = project_root / "quality" / "decomposition-review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out.parent / "decomposition-review.md").write_text(render_review_markdown(r), encoding="utf-8")
    (out.parent / "decomposition-review.html").write_text(render_review_html(r), encoding="utf-8")
    return out


def render_review_markdown(r: DecompositionReviewReport) -> str:
    lines = [f"# Decomposition Review: {r.project_slug}", "", f"- Readiness: **{r.readiness}**", f"- Score: **{r.score}/100**", f"- Questions: **{len(r.questions)}**", "", "| ID | Severity | Target | Question | Rationale |", "|---|---|---|---|---|"]
    for q in r.questions:
        lines.append(f"| {q.id} | {q.severity} | {q.target} | {q.question} | {q.rationale} |")
    lines.append("")
    return "\n".join(lines)


def render_review_html(r: DecompositionReviewReport) -> str:
    md = render_review_markdown(r)
    body = "\n".join(f"<pre>{_esc(line)}</pre>" if line.startswith("|") else f"<p>{_esc(line)}</p>" for line in md.splitlines())
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Decomposition Review</title><style>body{{font-family:Arial;margin:32px;max-width:1100px}}pre{{background:#f6f8fa;padding:5px}}</style></head><body>{body}</body></html>"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
