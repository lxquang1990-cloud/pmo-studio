"""YAML-backed domain pack loader."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pmo_studio.domain.detector import detect_domain

PACK_DIR = Path(__file__).parent / "packs"

@dataclass
class ConfigDomainPack:
    id: str
    label: str
    keywords: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    roles: dict[str, str] = field(default_factory=dict)
    quotation_defaults: dict[str, Any] = field(default_factory=dict)
    pack_version: int = 1
    workflows: list[str] = field(default_factory=list)
    reports: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    acceptance_presets: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def list_domain_packs() -> list[str]:
    return sorted(p.stem for p in PACK_DIR.glob("*.yaml"))


def load_domain_pack(domain_id: str) -> ConfigDomainPack:
    path = PACK_DIR / f"{domain_id}.yaml"
    if not path.exists():
        path = PACK_DIR / "generic.yaml"
    data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    return ConfigDomainPack(
        id=str(data.get("id") or path.stem),
        label=str(data.get("label") or path.stem),
        keywords=list(data.get("keywords") or []),
        modules=list(data.get("modules") or []),
        roles=dict(data.get("roles") or {}),
        quotation_defaults=dict(data.get("quotation_defaults") or {}),
        pack_version=int(data.get("pack_version") or 1),
        workflows=list(data.get("workflows") or []),
        reports=list(data.get("reports") or []),
        integrations=list(data.get("integrations") or []),
        risk_factors=list(data.get("risk_factors") or []),
        acceptance_presets=list(data.get("acceptance_presets") or []),
        raw=data,
    )


def resolve_domain_pack(source_text: str, *, project_slug: str = "", customer: str = "") -> tuple[ConfigDomainPack, Any]:
    result = detect_domain(source_text, project_slug=project_slug, customer=customer)
    return load_domain_pack(result.selected_domain), result


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    # Prefer PyYAML when installed, but keep offline/no-dependency fallback.
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        pass
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip(); value = value.strip()
            current_key = key
            if value.startswith("[") and value.endswith("]"):
                data[key] = [x.strip().strip("'\"") for x in value[1:-1].split(",") if x.strip()]
            elif value:
                data[key] = value.strip("'\"")
            else:
                data[key] = {}
        elif current_key and raw.startswith("  - "):
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(raw.strip()[2:].strip())
        elif current_key and raw.startswith("  ") and ":" in raw:
            data.setdefault(current_key, {})
            if isinstance(data[current_key], dict):
                key, value = raw.strip().split(":", 1)
                data[current_key][key.strip()] = value.strip().strip("'\"")
    return data
