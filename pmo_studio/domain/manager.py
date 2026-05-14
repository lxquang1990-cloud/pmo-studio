"""Domain management CLI support."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from pmo_studio.domain.pack_loader import PACK_DIR, list_domain_packs, load_domain_pack
from pmo_studio.domain.detector import detect_domain

REQUIRED_V2 = ["id", "label", "keywords", "modules", "roles", "pack_version", "workflows", "reports", "integrations", "risk_factors", "acceptance_presets"]


def list_domains() -> list[dict[str, Any]]:
    rows = []
    for domain_id in list_domain_packs():
        pack = load_domain_pack(domain_id)
        rows.append({"id": pack.id, "label": pack.label, "pack_version": pack.pack_version, "keywords": len(pack.keywords), "modules": len(pack.modules)})
    return rows


def inspect_domain(domain_id: str) -> dict[str, Any]:
    pack = load_domain_pack(domain_id)
    return {
        "id": pack.id,
        "label": pack.label,
        "pack_version": pack.pack_version,
        "keywords": pack.keywords,
        "modules": pack.modules,
        "roles": pack.roles,
        "workflows": pack.workflows,
        "reports": pack.reports,
        "integrations": pack.integrations,
        "risk_factors": pack.risk_factors,
        "acceptance_presets": pack.acceptance_presets,
        "quotation_defaults": pack.quotation_defaults,
    }


def validate_domain(domain_id: str | None = None) -> dict[str, Any]:
    ids = [domain_id] if domain_id else list_domain_packs()
    checks = []
    for did in ids:
        path = PACK_DIR / f"{did}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        missing = [k for k in REQUIRED_V2 if k not in data or data.get(k) in (None, [], {})]
        checks.append({"id": did, "path": str(path), "passed": not missing, "missing": missing})
    return {"passed": all(c["passed"] for c in checks), "checks": checks}


def scaffold_domain(domain_id: str, label: str, force: bool = False) -> Path:
    path = PACK_DIR / f"{domain_id}.yaml"
    if path.exists() and not force:
        raise FileExistsError(f"Domain pack exists: {path}")
    data = {
        "id": domain_id,
        "label": label,
        "keywords": [domain_id, label.lower()],
        "modules": ["core workspace", "workflow", "reporting"],
        "roles": {"Admin": "Administrator", "User": "Business User", "Approver": "Approver"},
        "quotation_defaults": {"risk_level": "standard", "manday_rate_vnd": 3900000},
        "pack_version": 2,
        "workflows": ["request intake", "review approval", "execution tracking"],
        "reports": ["operational dashboard", "status summary"],
        "integrations": ["SSO", "Email notification", "API integration"],
        "risk_factors": ["unclear source scope", "data migration", "approval rule discovery"],
        "acceptance_presets": ["Role-based access is enforced", "Reports can filter/export core data", "All critical changes are audited"],
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def benchmark_domain(domain_id: str) -> dict[str, Any]:
    pack = load_domain_pack(domain_id)
    source = "\n".join([pack.label, " ".join(pack.keywords), "\n".join(pack.modules), "\n".join(pack.workflows)])
    result = detect_domain(source, project_slug=f"bench-{domain_id}", customer="Domain Benchmark")
    return {"domain": domain_id, "detected": result.selected_domain, "score": result.score, "confidence": result.confidence, "passed": result.selected_domain == domain_id and result.score >= 0.5, "explanation": result.explanation}
