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


def update_domain(domain_id: str, updates: dict[str, Any]) -> Path:
    path = PACK_DIR / f"{domain_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Domain pack not found: {domain_id}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key, value in updates.items():
        if key not in REQUIRED_V2 and key != "quotation_defaults":
            raise ValueError(f"Unsupported domain field: {key}")
        if isinstance(data.get(key), list):
            data[key] = _merge_list(data.get(key) or [], _coerce_list(value))
        elif isinstance(data.get(key), dict):
            if not isinstance(value, dict):
                raise ValueError(f"Field {key} expects JSON object")
            merged = dict(data.get(key) or {}); merged.update(value); data[key] = merged
        else:
            data[key] = value
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def export_domain(domain_id: str, out_dir: Path) -> Path:
    src = PACK_DIR / f"{domain_id}.yaml"
    if not src.exists():
        raise FileNotFoundError(f"Domain pack not found: {domain_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / src.name
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def import_domain(path: Path, force: bool = False) -> Path:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    domain_id = str(data.get("id") or path.stem)
    dest = PACK_DIR / f"{domain_id}.yaml"
    if dest.exists() and not force:
        raise FileExistsError(f"Domain pack exists: {dest}")
    missing = [k for k in REQUIRED_V2 if k not in data or data.get(k) in (None, [], {})]
    if missing:
        raise ValueError(f"Invalid domain pack {domain_id}; missing: {', '.join(missing)}")
    dest.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return dest


def _merge_list(existing: list[Any], additions: list[Any]) -> list[Any]:
    out = list(existing)
    for item in additions:
        if item not in out:
            out.append(item)
    return out


def _coerce_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return [value]


def benchmark_domain(domain_id: str) -> dict[str, Any]:
    pack = load_domain_pack(domain_id)
    source = "\n".join([pack.label, " ".join(pack.keywords), "\n".join(pack.modules), "\n".join(pack.workflows)])
    result = detect_domain(source, project_slug=f"bench-{domain_id}", customer="Domain Benchmark")
    return {"domain": domain_id, "detected": result.selected_domain, "score": result.score, "confidence": result.confidence, "passed": result.selected_domain == domain_id and result.score >= 0.5, "explanation": result.explanation}
