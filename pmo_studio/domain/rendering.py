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
    if len(modules) < 8:
        fallback_modules = ["Workflow", "Approval", "Reporting", "Permission", "Audit", "Integration", "Archive", "Notification"]
        for item in fallback_modules:
            if len(modules) >= 8:
                break
            if item not in modules:
                modules.append(item)
    roles = list((pack.roles or {}).values())[:8] or ["Admin", "Business User", "Approver", "Viewer"]
    br = [["BR ID", "Linked Source", "Business Requirement"]]
    req = [["REQ ID", "Linked BR", "Definition"]]
    ac = [["AC ID", "Linked US", "Definition"]]
    workflows = list(getattr(pack, "workflows", []) or [])
    reports = list(getattr(pack, "reports", []) or [])
    integrations = list(getattr(pack, "integrations", []) or [])
    presets = list(getattr(pack, "acceptance_presets", []) or [])
    for i, module in enumerate(modules, 1):
        workflow_hint = workflows[(i - 1) % len(workflows)] if workflows else "standard review workflow"
        report_hint = reports[(i - 1) % len(reports)] if reports else "operational report"
        if "thông báo" in module.lower() or "nhắc" in module.lower():
            integration_hint = next((x for x in integrations if "Email" in x or "notification" in x.lower()), "Email notification")
        elif "trình ký" in module.lower():
            integration_hint = "internal approval log; Digital signature provider remains Phase 2 until approved API contract"
        elif "phân quyền" in module.lower():
            integration_hint = next((x for x in integrations if "LDAP" in x or "AD" in x), "LDAP/AD")
        else:
            integration_hint = integrations[(i - 1) % len(integrations)] if integrations else "configured integration"
        br.append([f"BR-CORE-{i:03d}", "SRC-001", f"Support {module} business capability for {pack.label}, including {workflow_hint}, {report_hint}, role-based controls, SLA tracking, and audit evidence."])
        req.append([f"REQ-CORE-{i:03d}", f"BR-CORE-{i:03d}", f"For {module}, authorized users shall create/search/process records through {workflow_hint}; the system shall validate module metadata, enforce role permissions, record immutable audit history, update workflow status/SLA, support {report_hint}, and use {integration_hint} for the relevant integration boundary."])
        preset = presets[(i - 1) % len(presets)] if presets else f"Given an authorized user and valid {module} data, when the user completes {workflow_hint}, then the system validates inputs, updates status/SLA, writes audit evidence, and shows the record in {report_hint}."
        ac.append([f"AC-001-{i:02d}", "US-001", preset])
    return DomainRenderContext(pack, detection, modules, roles, req, ac, br)


def render_table(rows: list[list[str]]) -> str:
    return table(rows)
