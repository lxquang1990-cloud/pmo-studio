"""Source-grounded quality intelligence for PMO Studio artifacts."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pmo_studio.domain.detector import detect_domain
from pmo_studio.generators.source_ba import read_redacted_sources

ARTIFACT_GLOBS = ["artifacts/ba/**/*.md", "artifacts/po/**/*.md", "artifacts/pm/**/*.md", "artifacts/ic/**/*.md"]
DOMAIN_TERMS = {
    "asset_management": ["asset", "tài sản", "thiết bị", "kiểm kê", "bảo trì"],
    "legal_ai": ["legal", "pháp lý", "văn bản", "trích dẫn", "hỏi đáp"],
    "crm": ["crm", "lead", "opportunity", "customer", "pipeline"],
    "eoffice": ["eoffice", "document", "văn bản", "công văn", "luồng ký"],
}

@dataclass
class QualityFinding:
    id: str
    severity: str
    category: str
    message: str
    evidence: str = ""
    artifact: str | None = None

@dataclass
class QualityIntelligenceReport:
    schema: str
    created_at: str
    project_slug: str
    source_domain: str
    artifact_domain: str
    score: int
    findings: list[QualityFinding] = field(default_factory=list)


def analyze_project_quality(project_root: Path) -> QualityIntelligenceReport:
    source_text = read_redacted_sources(_project_stub(project_root))
    artifact_texts = _artifact_texts(project_root)
    all_artifacts = "\n".join(artifact_texts.values())
    source_domain = detect_domain(source_text, project_slug=project_root.name).selected_domain if source_text.strip() else "generic"
    artifact_domain = detect_domain(all_artifacts, project_slug=project_root.name).selected_domain if all_artifacts.strip() else "generic"
    findings: list[QualityFinding] = []
    if source_domain != "generic" and artifact_domain != source_domain:
        findings.append(QualityFinding("QI-DOMAIN-001", "high", "domain_drift", f"Artifact domain appears to be {artifact_domain}, but source domain is {source_domain}.", artifact="all"))
    findings.extend(_missing_source_terms(source_text, all_artifacts))
    findings.extend(_traceability_gaps(project_root))
    findings.extend(_artifact_consistency(project_root, artifact_texts))
    score = max(0, 100 - sum({"high": 25, "medium": 12, "low": 5}.get(f.severity, 5) for f in findings))
    return QualityIntelligenceReport("pmo.quality_intelligence.v1", datetime.now(timezone.utc).isoformat(), project_root.name, source_domain, artifact_domain, score, findings)


def write_quality_intelligence(project_root: Path) -> Path:
    report = analyze_project_quality(project_root)
    out = project_root / "quality" / "intelligence.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = project_root / "quality" / "intelligence.md"
    md.write_text(render_quality_intelligence_markdown(report), encoding="utf-8")
    return out


def render_quality_intelligence_markdown(report: QualityIntelligenceReport) -> str:
    lines = [f"# Quality Intelligence: {report.project_slug}", "", f"- Score: {report.score}/100", f"- Source domain: {report.source_domain}", f"- Artifact domain: {report.artifact_domain}", f"- Findings: {len(report.findings)}", ""]
    if not report.findings:
        lines.append("No issues found.")
    else:
        lines.extend(["| ID | Severity | Category | Message | Artifact |", "|---|---|---|---|---|"])
        for f in report.findings:
            lines.append(f"| {f.id} | {f.severity} | {f.category} | {f.message} | {f.artifact or ''} |")
    lines.append("")
    return "\n".join(lines)


def _artifact_texts(project_root: Path) -> dict[str, str]:
    texts = {}
    for pattern in ARTIFACT_GLOBS:
        for path in project_root.glob(pattern):
            if path.is_file():
                texts[str(path.relative_to(project_root))] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def _missing_source_terms(source_text: str, artifact_text: str) -> list[QualityFinding]:
    terms = _important_terms(source_text)
    artifact_lower = artifact_text.lower()
    missing = [t for t in terms if t.lower() not in artifact_lower]
    if len(missing) >= 5:
        return [QualityFinding("QI-SOURCE-001", "medium", "source_coverage", "Several important source terms are missing from generated artifacts.", ", ".join(missing[:12]), "all")]
    return []


def _important_terms(text: str) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9_-]{4,}", text)
    stop = {"chức", "năng", "thống", "quản", "người", "dùng", "source", "brief", "project"}
    out = []
    for w in words:
        lw = w.lower()
        if lw not in stop and lw not in [x.lower() for x in out]:
            out.append(w)
    return out[:30]


def _traceability_gaps(project_root: Path) -> list[QualityFinding]:
    path = project_root / "traceability" / "views" / "validation.json"
    if not path.exists():
        return [QualityFinding("QI-TRACE-001", "medium", "traceability", "Traceability validation output is missing.", artifact="traceability")]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [QualityFinding("QI-TRACE-002", "medium", "traceability", f"Traceability validation JSON is invalid: {exc}", artifact=str(path))]
    if data.get("missing_upstream"):
        return [QualityFinding("QI-TRACE-003", "high", "traceability", "Traceability has missing upstream links.", str(data.get("missing_upstream")[:10]), "traceability")]
    return []


def _artifact_consistency(project_root: Path, artifact_texts: dict[str, str]) -> list[QualityFinding]:
    findings = []
    for rel, text in artifact_texts.items():
        if "{{" in text or "}}" in text:
            findings.append(QualityFinding("QI-TEMPLATE-001", "high", "template", "Unrendered template token found.", artifact=rel))
        ids = re.findall(r"^\s*(?:#{1,6}\s*)?((?:REQ|BR|US|TC)-[A-Z0-9-]*\d+)\b", text, flags=re.M)
        if len(ids) != len(set(ids)) and rel.endswith(("srs.md", "05-test-cases.md")):
            findings.append(QualityFinding("QI-ID-001", "low", "consistency", "Duplicate primary requirement/test definitions detected.", artifact=rel))
    return findings


def _project_stub(project_root: Path):
    class Stub:
        root = project_root
    return Stub()
