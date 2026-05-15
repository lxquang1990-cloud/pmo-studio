"""Functional Decomposition Engine (v3.0).

Turns source material into a BA-grade capability/feature/work-item model that can
feed SRS, user stories, test cases, and quotation with stable traceability IDs.
The implementation is deterministic and intentionally conservative.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from pmo_studio.domain.detector import detect_domain
from pmo_studio.generators.source_ba import read_redacted_sources

WORK_ITEM_TYPES = ["screen", "api", "workflow", "data", "validation", "permission", "report", "audit", "integration", "test", "estimate"]

DOMAIN_CAPABILITIES = {
    "asset_management": [
        ("Asset Master", ["Asset catalog", "Asset classification", "Asset import/export"]),
        ("Asset Lifecycle", ["Allocation", "Handover", "Return", "Transfer"]),
        ("Inventory & Maintenance", ["Inventory campaign", "Maintenance ticket", "Liquidation request"]),
        ("Reporting & Governance", ["Dashboard/report", "Permission and audit"]),
    ],
    "legal_ai": [
        ("Legal Knowledge Intake", ["Document upload", "Metadata extraction", "Citation indexing"]),
        ("Legal Q&A", ["Question answering", "Source citation", "Human review escalation"]),
        ("Governance", ["Permission", "Audit", "Export"]),
    ],
    "crm": [
        ("Customer Management", ["Customer profile", "Contact history", "Lead capture"]),
        ("Sales Pipeline", ["Opportunity", "Forecast", "Stage workflow"]),
        ("Reporting", ["Sales dashboard", "Export"]),
    ],
    "generic": [
        ("Core Operations", ["Core workspace", "Workflow processing", "Search and report"]),
        ("Governance", ["Permission", "Audit", "Import/export"]),
    ],
}

@dataclass
class WorkItem:
    id: str
    type: str
    name: str
    description: str
    estimate_unit: float

@dataclass
class FeatureNode:
    id: str
    capability_id: str
    name: str
    description: str
    source_terms: list[str]
    work_items: list[WorkItem] = field(default_factory=list)
    completeness_score: int = 0
    gaps: list[str] = field(default_factory=list)

@dataclass
class CapabilityNode:
    id: str
    name: str
    description: str
    features: list[FeatureNode] = field(default_factory=list)

@dataclass
class DecompositionReport:
    schema: str
    created_at: str
    project_slug: str
    domain: str
    capabilities: list[CapabilityNode]
    score: int
    gaps: list[str]


def decompose_project(project_root: Path) -> DecompositionReport:
    source_text = read_redacted_sources(_project_stub(project_root))
    domain = detect_domain(source_text, project_slug=project_root.name).selected_domain if source_text.strip() else "generic"
    if domain not in DOMAIN_CAPABILITIES:
        domain = "generic"
    terms = _source_terms(source_text)
    capabilities: list[CapabilityNode] = []
    global_gaps: list[str] = []
    for c_idx, (cap_name, feature_names) in enumerate(DOMAIN_CAPABILITIES[domain], 1):
        cap_id = f"CAP-{_slug(cap_name)}-{c_idx:03d}"
        cap = CapabilityNode(cap_id, cap_name, f"Business capability for {cap_name.lower()}.")
        for f_idx, fname in enumerate(feature_names, 1):
            fid = f"FEAT-{_slug(fname)}-{f_idx:03d}"
            matched_terms = _matched_terms(fname, source_text, terms)
            feature = FeatureNode(fid, cap_id, fname, f"Source-grounded feature covering {fname.lower()}.", matched_terms)
            feature.work_items = _work_items_for_feature(feature, domain)
            feature.completeness_score, feature.gaps = _score_feature(feature, source_text)
            global_gaps.extend([f"{feature.id}: {g}" for g in feature.gaps])
            cap.features.append(feature)
        capabilities.append(cap)
    score = max(0, round(sum(f.completeness_score for c in capabilities for f in c.features) / max(1, sum(len(c.features) for c in capabilities))))
    return DecompositionReport("pmo.functional_decomposition.v1", datetime.now(timezone.utc).isoformat(), project_root.name, domain, capabilities, score, global_gaps)


def write_decomposition(project_root: Path) -> Path:
    report = decompose_project(project_root)
    out = project_root / "artifacts" / "ba" / "00-functional-decomposition.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out.parent / "00-functional-decomposition.md").write_text(render_decomposition_markdown(report), encoding="utf-8")
    export_decomposition_xlsx(report, out.parent / "00-functional-decomposition.xlsx")
    qdir = project_root / "quality"; qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "decomposition-quality.json").write_text(json.dumps({"schema":"pmo.decomposition_quality.v1","score":report.score,"gaps":report.gaps}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def render_decomposition_markdown(report: DecompositionReport) -> str:
    lines = [f"# Functional Decomposition: {report.project_slug}", "", f"- Domain: **{report.domain}**", f"- Score: **{report.score}/100**", f"- Capabilities: **{len(report.capabilities)}**", ""]
    for cap in report.capabilities:
        lines += [f"## {cap.id} — {cap.name}", "", cap.description, ""]
        for feat in cap.features:
            lines += [f"### {feat.id} — {feat.name}", "", f"- Completeness: {feat.completeness_score}/100", f"- Source terms: {', '.join(feat.source_terms) or 'n/a'}", "", "| Work item | Type | Estimate unit | Description |", "|---|---|---:|---|"]
            for wi in feat.work_items:
                lines.append(f"| {wi.id} | {wi.type} | {wi.estimate_unit} | {wi.description} |")
            if feat.gaps:
                lines += ["", "Gaps:", *[f"- {g}" for g in feat.gaps]]
            lines.append("")
    return "\n".join(lines)


def export_decomposition_xlsx(report: DecompositionReport, out: Path) -> Path:
    wb = Workbook()
    ws = wb.active; ws.title = "Capability Map"
    _header(ws, ["Capability ID", "Capability", "Feature ID", "Feature", "Score", "Source Terms"])
    for cap in report.capabilities:
        for feat in cap.features:
            ws.append([cap.id, cap.name, feat.id, feat.name, feat.completeness_score, ", ".join(feat.source_terms)])
    wi = wb.create_sheet("Work Items")
    _header(wi, ["Feature ID", "Work Item ID", "Type", "Name", "Estimate Unit", "Description"])
    for cap in report.capabilities:
        for feat in cap.features:
            for item in feat.work_items:
                wi.append([feat.id, item.id, item.type, item.name, item.estimate_unit, item.description])
    gaps = wb.create_sheet("Coverage Gaps")
    _header(gaps, ["Gap"])
    for gap in report.gaps or ["No decomposition gaps found"]:
        gaps.append([gap])
    for sheet in wb.worksheets:
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = max(14, min(55, max(len(str(c.value or "")) for c in col) + 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def load_decomposition(project_root: Path) -> DecompositionReport | None:
    path = project_root / "artifacts" / "ba" / "00-functional-decomposition.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    caps = []
    for c in data.get("capabilities", []):
        cap = CapabilityNode(c["id"], c["name"], c.get("description", ""))
        for f in c.get("features", []):
            feat = FeatureNode(f["id"], f["capability_id"], f["name"], f.get("description", ""), f.get("source_terms", []), [WorkItem(**w) for w in f.get("work_items", [])], f.get("completeness_score", 0), f.get("gaps", []))
            cap.features.append(feat)
        caps.append(cap)
    return DecompositionReport(data.get("schema", "pmo.functional_decomposition.v1"), data.get("created_at", ""), data.get("project_slug", project_root.name), data.get("domain", "generic"), caps, data.get("score", 0), data.get("gaps", []))


def _work_items_for_feature(feature: FeatureNode, domain: str) -> list[WorkItem]:
    base = _slug(feature.name)
    weights = {"screen": 1.5, "api": 1.5, "workflow": 1.25, "data": 1.0, "validation": 0.75, "permission": 0.75, "report": 1.0, "audit": 0.5, "integration": 1.25, "test": 0.75, "estimate": 0.25}
    items = []
    for idx, typ in enumerate(WORK_ITEM_TYPES, 1):
        items.append(WorkItem(f"{typ.upper()}-{base}-{idx:03d}", typ, f"{feature.name} {typ}", f"{typ.title()} work item for {feature.name}.", weights[typ]))
    return items


def _score_feature(feature: FeatureNode, source_text: str) -> tuple[int, list[str]]:
    present = {w.type for w in feature.work_items}
    gaps = [f"Missing {t} decomposition" for t in WORK_ITEM_TYPES if t not in present]
    if not feature.source_terms:
        gaps.append("No explicit source term matched; confirm with customer")
    return max(0, 100 - len(gaps) * 8), gaps


def _source_terms(text: str) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9_-]{3,}", text)
    stop = {"source", "brief", "project", "người", "dùng", "thống", "quản", "chức", "năng"}
    out = []
    for w in words:
        if w.lower() not in stop and w.lower() not in [x.lower() for x in out]:
            out.append(w)
    return out[:40]


def _matched_terms(name: str, source_text: str, terms: list[str]) -> list[str]:
    name_l = name.lower(); src_l = source_text.lower()
    out = [t for t in terms if t.lower() in name_l or any(part and part in t.lower() for part in name_l.split())]
    if not out:
        out = [t for t in terms if t.lower() in src_l][:3]
    return out[:6]


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text.upper()).strip("-")
    return cleaned or "CORE"


def _header(ws, headers: list[str]) -> None:
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(horizontal="center")


def _project_stub(project_root: Path):
    class Stub:
        root = project_root
    return Stub()
