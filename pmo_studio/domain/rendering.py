"""Config-driven domain rendering primitives for generators."""
from __future__ import annotations

from dataclasses import dataclass

from pmo_studio.domain.pack_loader import ConfigDomainPack, resolve_domain_pack
from pmo_studio.generators.intelligence import table


@dataclass
class DomainRenderContext:
    pack: ConfigDomainPack
    detection: object
    modules: list[str]
    roles: list[str]
    requirements: list[list[str]]
    acceptance: list[list[str]]
    business_requirements: list[list[str]]


def build_render_context(source_text: str, *, project_slug: str = "", customer: str = "") -> DomainRenderContext:
    pack, detection = resolve_domain_pack(source_text, project_slug=project_slug, customer=customer)
    modules = list(pack.modules or [])[:8] or ["Core Workspace", "Workflow", "Reports"]
    while len(modules) < 8:
        modules.append(f"Generic validation/reporting baseline {len(modules) + 1}")
    roles = list((pack.roles or {}).values())[:8] or ["Admin", "Business User", "Approver", "Viewer"]
    br = [["BR ID", "Linked Source", "Business Requirement"]]
    req = [["REQ ID", "Linked BR", "Definition"]]
    ac = [["AC ID", "Linked US", "Definition"]]
    for i, module in enumerate(modules[:5], 1):
        br.append([f"BR-CORE-{i:03d}", "SRC-001", f"Support {module} business capability for {pack.label}."])
        req.append([f"REQ-CORE-{i:03d}", f"BR-CORE-{i:03d}", f"System shall support {module}, including validation, permissions, audit and reporting where applicable."])
    for i, module in enumerate(modules[:8], 1):
        ac.append([f"AC-001-{i:02d}", "US-001", f"Given authorized user, when executing {module}, then system validates, processes, audits and exposes expected result."])
    return DomainRenderContext(pack, detection, modules, roles, req, ac, br)


def render_table(rows: list[list[str]]) -> str:
    return table(rows)
