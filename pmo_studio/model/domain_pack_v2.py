from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PackFeaturePattern:
    name: str
    description: str = ""
    complexity: str = "Medium"
    priority: str = "Must"
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    validations: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    audit_events: list[str] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    manday: float = 3.0

@dataclass
class PackCapability:
    name: str
    description: str = ""
    features: list[PackFeaturePattern] = field(default_factory=list)

@dataclass
class DomainPackV2:
    id: str
    label: str
    roles: dict[str, str] = field(default_factory=dict)
    capabilities: list[PackCapability] = field(default_factory=list)
    data_entities: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    allowed_terms: list[str] = field(default_factory=list)
    blocked_terms: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "DomainPackV2":
        caps: list[PackCapability] = []
        for c in raw.get("capabilities_v2") or []:
            feats=[]
            for f in c.get("features") or []:
                feats.append(PackFeaturePattern(
                    name=str(f.get("name") or ""), description=str(f.get("description") or ""),
                    complexity=str(f.get("complexity") or "Medium"), priority=str(f.get("priority") or "Must"),
                    inputs=list(f.get("inputs") or []), outputs=list(f.get("outputs") or []),
                    validations=list(f.get("validations") or []), permissions=list(f.get("permissions") or []),
                    audit_events=list(f.get("audit_events") or []), business_rules=list(f.get("business_rules") or []),
                    manday=float(f.get("manday") or (5 if str(f.get("complexity") or "").lower()=="complex" else 3)),
                ))
            caps.append(PackCapability(str(c.get("name") or ""), str(c.get("description") or ""), feats))
        return cls(str(raw.get("id") or "generic"), str(raw.get("label") or raw.get("id") or "Generic"), dict(raw.get("roles") or {}), caps, list(raw.get("data_entities") or []), list(raw.get("integrations") or []), list(raw.get("assumptions") or []), list(raw.get("out_of_scope") or []), list(raw.get("allowed_terms") or []), list(raw.get("blocked_terms") or []), raw)
