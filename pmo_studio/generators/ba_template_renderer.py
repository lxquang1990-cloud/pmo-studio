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
    integrations = intel.integrations or list(getattr(ctx.pack, "integrations", []) or []) or ["LDAP/AD user-role sync", "Email notification gateway", "DMS/archive connector"]
    workflows = intel.workflows or list(getattr(ctx.pack, "workflows", []) or []) or ["User nhập/tra cứu dữ liệu → hệ thống validate → xử lý workflow → ghi audit/log → xuất báo cáo hoặc thông báo."]
    risks = intel.risks or ["Workflow/SLA chi tiết cần được Sponsor xác nhận trong baseline nhưng MVP dùng default documented below", "Integration contract chưa có thì đưa Phase 2, không block MVP documentation baseline"]
    requirements = render_table(ctx.requirements)
    acceptance = render_table(ctx.acceptance)
    business_requirements = render_table(ctx.business_requirements)
    summary = bullets(intel.summary or [f"Domain pack: {ctx.pack.label}", getattr(ctx.detection, "explanation", "")])

    common = {
        "template_version": TEMPLATE_VERSION,
        "domain_id": ctx.pack.id,
        "suppress_metadata": "true" if ctx.pack.id not in {"asset_management", "legal", "legal_ai"} else "false",
        "project_slug": project.config.project_slug,
        "summary": summary,
        "overview": f"Tài liệu này mô tả MVP {ctx.pack.label} cho {project.config.customer}: quản lý văn bản đến/đi, trình ký duyệt đa cấp, phân quyền, SLA/dashboard, báo cáo quá hạn, lưu trữ và thông báo nhắc hạn. MVP dùng LDAP/AD, Email notification và DMS API ở mức tích hợp chuẩn có owner/contract; Digital signature provider được đưa Phase 2 nếu chưa có contract/API chính thức. Metadata bắt buộc gồm số/ký hiệu, đơn vị gửi/nhận, ngày nhận/phát hành, độ mật/khẩn, người xử lý, hạn xử lý và file đính kèm; SLA mặc định cảnh báo T-24h và escalation sau 1 ngày quá hạn.",
        "roles": bullets(ctx.roles),
        "modules": bullets(modules[:8]),
        "business_goals": bullets([
            f"Số hóa các nghiệp vụ chính theo domain {ctx.pack.label}.",
            "Chuẩn hóa dữ liệu, workflow, phân quyền, báo cáo và traceability.",
            "Tạo baseline đủ để PO/PM/BA/IC review, estimate và triển khai MVP.",
        ]),
        "mvp_scope": bullets([f"{m}: create/search/process records with document metadata (number, sender/receiver, date, confidentiality/urgency, assignee, due date, attachment), enforce department/role validation, track workflow/SLA status, write audit evidence, and expose dashboard/export." for m in modules[:8]]),
        "phase2_scope": bullets([x for x in integrations if "Digital signature" in x] or ["Advanced integrations or provider-specific signing features after API contract approval"]),
        "requirements": requirements,
        "acceptance": acceptance,
        "business_requirements": business_requirements,
        "business_context": f"Dự án cần số hóa các module nghiệp vụ {ctx.pack.label} theo SRC-001, với workflow, phân quyền, SLA, báo cáo, audit và tích hợp rõ ràng cho MVP.",
        "business_drivers": bullets([
            "Cần chuyển yêu cầu nghiệp vụ thành bộ tài liệu PO/PM/BA/IC có thể review và estimate.",
            "Cần chuẩn hóa module, workflow, permission, integration, reporting và assumptions.",
            "Cần giữ traceability từ source tới BR/REQ/US/AC/TC/EST.",
        ]),
        "workflows": bullets(workflows),
        "risks": bullets(risks),
        "srs_intro": f"SRS mô tả baseline chức năng cho {ctx.pack.label}, linked từ SRC-001 tới BR/REQ/AC/TC.",
        "module_list": ", ".join(modules[:8]),
        "integrations": bullets(integrations),
        "us_title": f"Xử lý nghiệp vụ {ctx.pack.label}",
    }
    (ba_dir / "01-prd.md").write_text(render_template("ba/v1/prd.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.prd"}), encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(render_template("ba/v1/brd.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.brd"}), encoding="utf-8")
    (srs_dir / "srs.md").write_text(render_template("ba/v1/srs.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.srs"}), encoding="utf-8")
    (srs_dir / "screens" / "SCR-CORE-001.md").write_text(f"# SCR-CORE-001: {ctx.pack.label} Workspace\n\n**Linked REQ:** REQ-CORE-001\n\nScreens cover: {', '.join(modules[:8])}.\n", encoding="utf-8")
    (srs_dir / "apis" / "API-CORE-001.md").write_text(f"# API-CORE-001: {ctx.pack.label} API\n\n**Linked REQ:** REQ-CORE-001\n\nEndpoints support CRUD/search/workflow/report/export for source-driven modules.\n", encoding="utf-8")
    (srs_dir / "workflows" / "WF-CORE-001.md").write_text(f"# WF-CORE-001: {ctx.pack.label} Workflow\n\n**Linked REQ:** REQ-CORE-001\n\nEnter/search data → validate → process workflow → audit → report/export/notification.\n", encoding="utf-8")
    (us_dir / "US-001.md").write_text(render_template("ba/v1/us.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.us"}), encoding="utf-8")
    tc_rows = [["ID", "Linked AC", "Type", "Precondition", "Steps / Input", "Expected Result"]]
    detailed = [
        ("TC-001", "AC-001-01", "Văn thư user; metadata gồm số/ký hiệu, đơn vị gửi, ngày nhận, độ mật/khẩn, file PDF", "Register incoming document and assign to department", "Unique intake number; metadata/attachment saved; status=Assigned; audit event created"),
        ("TC-002", "AC-001-02", "Chuyên viên user; outgoing draft, recipient list and approval route exist", "Submit draft for review/signing and attempt release before approval", "Approval steps recorded; early release blocked; final release allowed only after required approvals"),
        ("TC-003", "AC-001-03", "Department Head user; work dossier and assignee exist; due date T+1", "Assign task, add comment, update completion status", "Task appears in assignee workspace; SLA status is Near-due/On-track; comment history retained"),
        ("TC-004", "AC-001-04", "Approval matrix has two levels; unauthorized user lacks level-2 approval", "Attempt skipped approval and unauthorized approval", "System blocks action with access denied/403 and writes security audit event"),
        ("TC-005", "AC-001-05", "Document has completed approval chain", "Release document, then attempt unauthorized edit", "Release number and recipients recorded; released version immutable except authorized revision flow"),
        ("TC-006", "AC-001-06", "Overdue and near-due workflow tasks exist across two departments", "Open SLA dashboard and filter by department/status/age/type; export XLSX", "Dashboard shows correct overdue/near-due counts; export respects selected filters"),
        ("TC-007", "AC-001-07", "Restricted and normal archive records exist", "Search/export archive as authorized and unauthorized users", "Only permitted records returned; unauthorized download/export blocked; export audit event logged"),
        ("TC-008", "AC-001-08", "Reminder threshold T-24h and escalation after 1 overdue working day configured", "Run notification job for near-due and overdue tasks", "Assignee reminder and manager escalation created/sent; notification status logged")
    ]
    for row in detailed[:len(modules[:8])]:
        tc_rows.append([row[0], row[1], "Functional", row[2], row[3], row[4]])
    (ba_dir / "05-test-cases.md").write_text(render_template("ba/v1/test_cases.md.tmpl", {**common, "template_id": f"{ctx.pack.id}.ba.test_cases", "test_cases": table(tc_rows)}), encoding="utf-8")
    from pmo_studio.generators.quotation import generate_quotation_for_project
    generate_quotation_for_project(project, ba_dir / "06-quotation.xlsx")
    project.mark_stage("ba.template_rendered", "completed", mode=mode, domain_pack=ctx.pack.id)
