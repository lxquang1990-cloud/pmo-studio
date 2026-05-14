"""Config/template-driven BA artifact renderer."""
from __future__ import annotations

from pathlib import Path

from pmo_studio.core.project import Project
from pmo_studio.domain.rendering import build_render_context, render_table
from pmo_studio.generators.intelligence import build_intelligence, bullets, table
from pmo_studio.domain.prompts import get_domain
from pmo_studio.templates.renderer import TEMPLATE_VERSION, render_template


def render_ba_artifacts_from_source(project: Project, source_text: str, *, mode: str = "config") -> None:
    ba_dir = project.root / "artifacts" / "ba"
    srs_dir = ba_dir / "03-srs"
    us_dir = ba_dir / "04-us"
    for d in [ba_dir, srs_dir, srs_dir / "screens", srs_dir / "apis", srs_dir / "workflows", srs_dir / "reports", us_dir]:
        d.mkdir(parents=True, exist_ok=True)

    ctx = build_render_context(source_text, project_slug=project.config.project_slug, customer=project.config.customer)
    intel = build_intelligence(source_text, get_domain(project.config.domain_pack))
    modules = ctx.modules
    integrations = intel.integrations or ["Integration scope cần xác nhận"]
    workflows = intel.workflows or ["User nhập/tra cứu dữ liệu → hệ thống validate → xử lý workflow → ghi audit/log → xuất báo cáo hoặc thông báo."]
    risks = intel.risks or ["Sai lệch nghiệp vụ nếu chưa workshop với key users", "Thiếu dữ liệu mẫu làm giảm độ chính xác estimate"]
    requirements = render_table(ctx.requirements)
    acceptance = render_table(ctx.acceptance)
    business_requirements = render_table(ctx.business_requirements)
    summary = bullets(intel.summary or [f"Domain pack: {ctx.pack.label}", getattr(ctx.detection, "explanation", "")])

    common = {
        "template_version": TEMPLATE_VERSION,
        "domain_id": ctx.pack.id,
        "project_slug": project.config.project_slug,
        "summary": summary,
        "roles": bullets(ctx.roles),
        "modules": bullets(modules[:8]),
        "business_goals": bullets([
            f"Số hóa các nghiệp vụ chính theo domain {ctx.pack.label}.",
            "Chuẩn hóa dữ liệu, workflow, phân quyền, báo cáo và traceability.",
            "Tạo baseline đủ để PO/PM/BA/IC review, estimate và triển khai MVP.",
        ]),
        "mvp_scope": bullets([f"{m}: xử lý nghiệp vụ, tra cứu, validation, trạng thái và báo cáo liên quan." for m in modules[:6]]),
        "phase2_scope": bullets(integrations),
        "requirements": requirements,
        "acceptance": acceptance,
        "business_requirements": business_requirements,
        "business_context": f"Dự án cần số hóa các module nghiệp vụ theo source đầu vào và domain pack {ctx.pack.label}.",
        "business_drivers": bullets([
            "Cần chuyển source mô tả thành bộ tài liệu PO/PM/BA/IC có thể review.",
            "Cần chuẩn hóa module, workflow, permission, integration, reporting và assumptions.",
            "Cần giữ traceability từ source tới BR/REQ/US/AC/TC/EST.",
        ]),
        "workflows": bullets(workflows),
        "risks": bullets(risks),
        "srs_intro": f"SRS mô tả baseline source-driven theo domain pack {ctx.pack.label}.",
        "module_list": ", ".join(modules[:8]),
        "integrations": bullets(integrations),
        "us_title": f"Xử lý nghiệp vụ theo source đầu vào ({ctx.pack.label})",
    }
    (ba_dir / "01-prd.md").write_text(render_template("ba/v1/prd.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.prd"}), encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(render_template("ba/v1/brd.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.brd"}), encoding="utf-8")
    (srs_dir / "srs.md").write_text(render_template("ba/v1/srs.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.srs"}), encoding="utf-8")
    (srs_dir / "screens" / "SCR-CORE-001.md").write_text(f"# SCR-CORE-001: {ctx.pack.label} Workspace\n\n**Linked REQ:** REQ-CORE-001\n\nScreens cover: {', '.join(modules[:8])}.\n", encoding="utf-8")
    (srs_dir / "apis" / "API-CORE-001.md").write_text(f"# API-CORE-001: {ctx.pack.label} API\n\n**Linked REQ:** REQ-CORE-001\n\nEndpoints support CRUD/search/workflow/report/export for source-driven modules.\n", encoding="utf-8")
    (srs_dir / "workflows" / "WF-CORE-001.md").write_text(f"# WF-CORE-001: {ctx.pack.label} Workflow\n\n**Linked REQ:** REQ-CORE-001\n\nEnter/search data → validate → process workflow → audit → report/export/notification.\n", encoding="utf-8")
    (us_dir / "US-001.md").write_text(render_template("ba/v1/us.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.us"}), encoding="utf-8")
    tc_rows = [["ID", "Linked AC", "Type", "Steps / Input", "Expected Result"]]
    for i, module in enumerate(modules[:8], 1):
        tc_rows.append([f"TC-{i:03d}", f"AC-001-{i:02d}", "Source-driven", f"Execute main workflow for {module}", "Data is validated, saved/processed, audited and visible in reports according to permission"])
    (ba_dir / "05-test-cases.md").write_text(render_template("ba/v1/test_cases.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.test_cases", "test_cases": table(tc_rows)}), encoding="utf-8")
    from pmo_studio.generators.quotation import generate_quotation_for_project
    generate_quotation_for_project(project, ba_dir / "06-quotation.xlsx")
    project.mark_stage("ba.template_rendered", "completed", mode=mode, domain_pack=ctx.pack.id)
