from __future__ import annotations
from collections import defaultdict

from pmo_studio.estimation.extractor import extract_features
from pmo_studio.estimation.complexity import classify_complexity, signal_hits
from pmo_studio.estimation.models import EstimateFeature, EstimatePackage, WorkItemEstimate

ROLES = ["BA", "PM", "Dev", "QA", "DevOps", "UAT", "Training"]

ROLE_SPLITS = {
    "screen": {"BA": 0.12, "PM": 0.05, "Dev": 0.55, "QA": 0.18, "UAT": 0.07, "Training": 0.03},
    "api": {"BA": 0.08, "PM": 0.04, "Dev": 0.68, "QA": 0.16, "DevOps": 0.04},
    "workflow": {"BA": 0.16, "PM": 0.07, "Dev": 0.50, "QA": 0.18, "UAT": 0.07, "Training": 0.02},
    "report": {"BA": 0.14, "PM": 0.04, "Dev": 0.52, "QA": 0.18, "UAT": 0.08, "Training": 0.04},
    "data": {"BA": 0.12, "PM": 0.05, "Dev": 0.50, "QA": 0.18, "DevOps": 0.08, "UAT": 0.05, "Training": 0.02},
    "security": {"BA": 0.08, "PM": 0.05, "Dev": 0.55, "QA": 0.22, "DevOps": 0.10},
}

def estimate_from_source(source_text: str) -> list[EstimateFeature]:
    return estimate_package_from_source(source_text).features


def estimate_package_from_source(source_text: str) -> EstimatePackage:
    features: list[EstimateFeature] = []
    role_totals = defaultdict(float)
    risk_totals = defaultdict(float)
    for idx, (module, feature, desc) in enumerate(extract_features(source_text), 1):
        complexity, base, risk, rationale = classify_complexity(feature, desc)
        hits = signal_hits(feature, desc)
        integration_multiplier = 1.0 + (0.1 if hits["integration"] else 0.0)
        work_items = _build_work_items(idx, feature, desc, complexity, base, risk, integration_multiplier, hits, rationale)
        final = round(sum(w.final_manday for w in work_items), 1)
        buffers = _risk_buffers(hits, final)
        for k, v in buffers.items():
            risk_totals[k] += v
        for item in work_items:
            for role, md in item.role_effort.items():
                role_totals[role] += md
        features.append(EstimateFeature(module, feature, desc, complexity, base, risk, integration_multiplier, final, rationale, work_items, buffers))
    total = round(sum(f.final_manday for f in features) + sum(risk_totals.values()), 1)
    return EstimatePackage(features, {k: round(v, 1) for k, v in role_totals.items()}, {k: round(v, 1) for k, v in risk_totals.items()}, total)


def _build_work_items(idx: int, feature: str, desc: str, complexity: str, base: float, risk: float, integration_multiplier: float, hits: dict[str, bool], rationale: str) -> list[WorkItemEstimate]:
    items: list[tuple[str, str, float]] = [("screen", "Screen/UI", base)]
    if hits["integration"] or hits["ai"]:
        items.append(("api", "API/Integration", max(2.0, base * 0.55)))
    if hits["workflow"]:
        items.append(("workflow", "Workflow/Approval", max(2.0, base * 0.60)))
    if hits["data"]:
        items.append(("report", "Report/Export/Data", max(1.5, base * 0.45)))
    if hits["security"]:
        items.append(("security", "RBAC/Audit/Security", max(1.2, base * 0.35)))
    out = []
    for seq, (typ, label, raw) in enumerate(items, 1):
        md = round(raw * risk * integration_multiplier, 1)
        out.append(WorkItemEstimate(
            typ,
            _work_item_id(typ),
            f"{feature} - {label}",
            complexity,
            _split_roles(typ, md),
            risk,
            integration_multiplier,
            md,
            rationale or "Source-driven estimate",
        ))
    return out


def _work_item_id(typ: str) -> str:
    if typ == "api":
        return "API-CORE-001"
    if typ == "workflow":
        return "WF-CORE-001"
    if typ == "report":
        return "RPT-CORE-001"
    return "SCR-CORE-001"


def _split_roles(typ: str, md: float) -> dict[str, float]:
    split = ROLE_SPLITS.get(typ, ROLE_SPLITS["screen"])
    return {role: round(md * pct, 1) for role, pct in split.items() if md * pct > 0}


def _risk_buffers(hits: dict[str, bool], feature_md: float) -> dict[str, float]:
    buffers = {}
    if hits["integration"]:
        buffers["Integration/API uncertainty"] = round(feature_md * 0.12, 1)
    if hits["data"]:
        buffers["Data migration/report reconciliation"] = round(feature_md * 0.08, 1)
    if hits["ai"]:
        buffers["AI prompt/citation validation"] = round(feature_md * 0.15, 1)
    if hits["security"]:
        buffers["Security/RBAC hardening"] = round(feature_md * 0.06, 1)
    return buffers
