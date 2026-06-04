"""PO, PM, IC scaffold generators for full v2.1 coverage."""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook
from pmo_studio.core.project import Project
from pmo_studio.domain.prompts import get_domain



def _is_legal_project(project: Project) -> bool:
    source_text = ""
    try:
        for source_path in sorted((project.root / "source" / "redacted").glob("*")):
            if source_path.is_file():
                source_text += "\n" + source_path.read_text(encoding="utf-8", errors="ignore")[:10000]
    except Exception:
        source_text = ""
    haystack = " ".join([
        str(getattr(project.config, "project_slug", project.root.name)),
        str(getattr(project.config, "product", "")),
        str(getattr(project.config, "customer", "")),
        str(getattr(project.config, "brief", "")),
        source_text,
    ]).lower()
    return any(k in haystack for k in ["legaliq", "pháp lý", "phap ly", "ủy quyền", "uy quyen", "hợp đồng", "hop dong", "b.pctt"])

def generate_legal_po(project: Project) -> None:
    d = project.root / "artifacts/po"; d.mkdir(parents=True, exist_ok=True)
    (d / "01-vision.md").write_text("""# Product Vision

## Domain: Legal AI / LegalIQ

## Vision Statement
Triển khai LIQ LegalIQ để số hóa hỏi đáp pháp lý, quản lý FAQ/câu hỏi, AI trả lời có trích dẫn nguồn, quản lý ủy quyền, hợp đồng, thẩm định và báo cáo pháp lý.

## MVP Boundaries
- Included: Q&A/FAQ, AI answer/citation, B.PCTT escalation, delegation, contract review, appraisal, reports, RBAC/admin.
- Phase 2: AI fine-tuning nâng cao, e-sign với đối tác, realtime integration sâu.
- Excluded: cam kết pháp lý của chữ ký điện tử nếu chưa có provider/license và chính sách nội bộ.

## Business Goals
- BG-001: Giảm thời gian trả lời câu hỏi pháp lý/nghiệp vụ phổ biến.
- BG-002: Chuẩn hóa ủy quyền, hợp đồng, thẩm định và báo cáo.
- BG-003: Tăng auditability và traceability qua trích dẫn nguồn/lịch sử xử lý.

## Implementation Readiness
- API baseline: API-CORE-001 for Q&A, AI answer, delegation, contract, appraisal, report and RBAC integration.
- Workflow baseline: WF-CORE-001 links legal question, AI answer/citation, B.PCTT escalation, approval and reporting.
- Screen baseline: SCR-CORE-001 covers LegalIQ workspace screens.
- Test baseline: TC-001..TC-008 cover acceptance criteria AC-001-01..AC-001-08.
""", encoding="utf-8")
    (d / "02-okr.md").write_text("# OKR Set\n\n| Objective | Key Result |\n|---|---|\n| Tăng hiệu quả hỏi đáp pháp lý | 80% câu hỏi phổ biến được trả lời bằng FAQ/AI có trích dẫn |\n", encoding="utf-8")
    (d / "03-roadmap.md").write_text("# Roadmap\n\n## Now\nLegal Q&A, FAQ, AI citation, B.PCTT escalation.\n\n## Next\nDelegation, contract review, appraisal.\n\n## Later\nAdvanced AI/e-sign/realtime integration.\n", encoding="utf-8")
    wb = Workbook(); ws = wb.active; ws.title = "Backlog"; ws.append(["Epic", "Feature", "Priority"])
    for row in [("Legal Q&A", "FAQ/Q&A portal", "P0"), ("AI", "AI answer with citation and escalation", "P0"), ("Delegation", "Authorization workflow", "P0"), ("Contract", "Contract drafting/review/approval", "P0"), ("Appraisal", "Appraisal report workflow", "P1"), ("Reports", "Statistics and legal reports", "P1"), ("Admin", "RBAC/catalog/config", "P0")]:
        ws.append(row)
    wb.save(d / "04-backlog.xlsx")
    (d / "05-release-notes.md").write_text("# Release Notes\n\n## v0.1\nInitial LegalIQ PMO pack.\n", encoding="utf-8")
    project.mark_stage("po", "completed")

def generate_legal_pm(project: Project) -> None:
    d = project.root / "artifacts/pm"; d.mkdir(parents=True, exist_ok=True)
    (d / "01-charter.md").write_text("""# Project Charter

## Domain
Legal AI / LegalIQ

## Objective
Triển khai web app LIQ LegalIQ, bao gồm hỏi đáp pháp lý bằng AI, quản lý ủy quyền, hợp đồng, thẩm định, thống kê/báo cáo và quản trị phân quyền.

## MVP Scope
- BR-CORE-001: Legal Q&A portal và FAQ.
- BR-CORE-002: AI answer engine có trích dẫn và escalation.
- BR-CORE-003: Delegation management.
- BR-CORE-004: Contract legal review.
- BR-CORE-005: Appraisal, reports, admin/RBAC.

## Implementation Readiness
- API baseline: API-CORE-001 for Q&A, AI answer, delegation, contract, appraisal, report and RBAC integration.
- Workflow baseline: WF-CORE-001 links legal question, AI answer/citation, B.PCTT escalation, approval and reporting.
- Screen baseline: SCR-CORE-001 covers LegalIQ workspace screens.
- Test baseline: TC-001..TC-008 cover acceptance criteria AC-001-01..AC-001-08.

## Risks
| Risk ID | Description | Mitigation |
|---|---|---|
| RISK-001 | Chất lượng dữ liệu huấn luyện AI chưa đủ | Data cleansing, source citation, fallback B.PCTT |
| RISK-002 | API eOffice/PMS chưa rõ | Baseline API contract trước integration sprint |
| RISK-003 | AI trả lời sai/ngụy tạo | Bắt buộc citation, confidence threshold, human escalation |
""", encoding="utf-8")
    # Keep the existing XLSX/MD support files simple but domain-relevant.
    wb = Workbook(); ws = wb.active; ws.title = "WBS"; ws.append(["Phase", "Work Package", "Owner"])
    for row in [("Discovery", "Legal taxonomy + FAQ/data readiness", "BA/Legal"), ("Build", "Q&A/AI/Delegation/Contract/Appraisal", "Dev"), ("UAT", "Legal scenarios and integration test", "QA/Legal")]: ws.append(row)
    wb.save(d / "02-wbs.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "RACI"; ws.append(["Activity", "Legal", "IT", "Vendor", "Sponsor"]); ws.append(["Scope baseline", "R", "C", "C", "A"]); ws.append(["Integration", "C", "A", "R", "I"]); wb.save(d / "03-raci.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "Risks"; ws.append(["Risk", "Impact", "Mitigation"]); ws.append(["AI hallucination", "High", "Citation + human escalation"]); ws.append(["Integration API unavailable", "High", "Import/export fallback"]); wb.save(d / "04-risk-register.xlsx")
    (d / "05-status-report.md").write_text("# Status Report\n\nLegalIQ PMO pack generated.\n", encoding="utf-8")
    (d / "06-change-request-template.md").write_text("# Change Request Template\n", encoding="utf-8")
    (d / "07-lessons-learned.md").write_text("# Lessons Learned\n", encoding="utf-8")
    project.mark_stage("pm", "completed")


def _read_project_source(project: Project, max_chars: int = 30000) -> str:
    text = ""
    try:
        for source_path in sorted((project.root / "source" / "redacted").glob("*")):
            if source_path.is_file():
                text += "\n" + source_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return text[:max_chars]

def _is_asset_project(project: Project) -> bool:
    haystack = " ".join([
        str(getattr(project.config, "project_slug", project.root.name)),
        str(getattr(project.config, "product", "")),
        str(getattr(project.config, "customer", "")),
        str(getattr(project.config, "brief", "")),
        _read_project_source(project),
    ]).lower()
    return any(k in haystack for k in ["tài sản", "tai san", "ttb", "asset management", "asset master", "kiểm kê", "khấu hao", "thanh lý"])

def _generic_source_modules(project: Project) -> list[str]:
    import re
    text = _read_project_source(project)
    modules = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.match(r"^(\d+(?:\.\d+)?|[IVX]+)$", cells[0], re.I):
            name = cells[1]
            if name and name.lower() not in {"chức năng", "mô tả"} and len(name) > 2:
                modules.append(name[:90])
    if not modules:
        low = text.lower()
        if any(k in low for k in ["eoffice", "văn bản", "van ban", "duyệt", "duyet", "sla", "quá hạn", "qua han"]):
            modules = ["văn bản đến", "văn bản đi", "duyệt đa cấp", "dashboard SLA", "báo cáo quá hạn", "phân quyền", "lưu trữ"]
        else:
            modules = ["Core Workflow", "Administration", "Reports"]
    out=[]
    for m in modules:
        if m.lower() not in [x.lower() for x in out]:
            out.append(m)
    return out[:8]

def generate_generic_po(project: Project) -> None:
    d = project.root / "artifacts/po"; d.mkdir(parents=True, exist_ok=True)
    modules = _generic_source_modules(project)
    (d / "01-vision.md").write_text(f"""# Product Vision

## Domain: Customer Business Workflow

## Vision Statement
Triển khai MVP nghiệp vụ cho {getattr(project.config, 'customer', 'Customer')} với workflow, phân quyền, SLA, báo cáo và audit rõ ràng theo phạm vi đã baseline.

## MVP Boundaries
- Included: {', '.join(modules[:6])}.
- Phase 2: integrations, advanced workflow, automation and reporting enhancements after API/data contracts are confirmed.
- Excluded: any module not described in source or not approved in scope baseline.

## Business Goals
- BG-001: Số hóa các module nghiệp vụ được mô tả trong source.
- BG-002: Chuẩn hóa workflow, permission, reporting and traceability.
- BG-003: Tạo baseline đủ cho BA/Dev/QA/UAT review.

## Implementation Readiness
- API baseline: API-CORE-001 covers document CRUD/search, workflow action, report/export and notification endpoints.
- Workflow baseline: WF-CORE-001 covers intake, assignment, approval, release, archive and reminder/escalation.
- Screen baseline: SCR-CORE-001 covers document workspace, approval queue, SLA dashboard, reports and archive search.
- Test baseline: TC-001..TC-008 covers document intake, outgoing draft, approval, release, SLA dashboard, archive and reminder scenarios.

## MVP Operating Detail
- Roles: Văn thư registers/releases documents; Chuyên viên drafts/handles assigned tasks; Lãnh đạo phòng/Director approve, sign and monitor SLA; Admin manages permission matrix.
- SLA defaults: near-due warning at T-24h, overdue flag after due date, escalation to manager after one overdue working day.
- Reports: overdue list, SLA by department, document volume by type/status, released document register and archive export audit.
- Permissions: department-based visibility, restricted document access, approval-level authorization and audited export/download.
""", encoding="utf-8")
    (d / "02-okr.md").write_text("# OKR Set\n\n| Objective | Key Result |\n|---|---|\n| Source-driven delivery | 100% MVP modules traced from source to REQ/AC/TC |\n", encoding="utf-8")
    (d / "03-roadmap.md").write_text("# Roadmap\n\n## Now\nSource baseline and MVP modules.\n\n## Next\nIntegration/UAT hardening.\n\n## Later\nAdvanced automation and analytics.\n", encoding="utf-8")
    wb=Workbook(); ws=wb.active; ws.title="Backlog"; ws.append(["Epic","Feature","Priority"])
    for m in modules: ws.append([m, f"Implement {m}", "P0"])
    wb.save(d/"04-backlog.xlsx")
    (d / "05-release-notes.md").write_text("# Release Notes\n\n## v0.1\nInitial source-driven PMO pack.\n", encoding="utf-8")
    project.mark_stage("po", "completed")

def generate_generic_pm(project: Project) -> None:
    d = project.root / "artifacts/pm"; d.mkdir(parents=True, exist_ok=True)
    modules = _generic_source_modules(project)
    (d / "01-charter.md").write_text(f"""# Project Charter

## Domain
Customer Business Workflow

## Objective
Triển khai hệ thống theo source đầu vào, với MVP gồm: {', '.join(modules[:8])}.

## MVP Scope
{chr(10).join(f'- BR-CORE-{i:03d}: {m}' for i, m in enumerate(modules[:8], 1))}

## Success Criteria
- DEC-SUCCESS-001: Văn thư can register incoming/outgoing documents with required metadata and attachment audit.
- DEC-SUCCESS-002: Approval workflow enforces configured levels and blocks unauthorized/skipped approval.
- DEC-SUCCESS-003: SLA dashboard shows near-due/overdue tasks by department and assignee.
- DEC-SUCCESS-004: Reports/export and archive search respect role/department permissions.
- DEC-SUCCESS-005: Reminder/escalation notification status is logged for audit.

## Implementation Readiness
- API baseline: API-CORE-001 covers document CRUD/search, workflow action, report/export and notification endpoints.
- Workflow baseline: WF-CORE-001 covers intake, assignment, approval, release, archive and reminder/escalation.
- Screen baseline: SCR-CORE-001 covers document workspace, approval queue, SLA dashboard, reports and archive search.
- Test baseline: TC-001..TC-008 covers document intake, outgoing draft, approval, release, SLA dashboard, archive and reminder scenarios.

## MVP Operating Detail
- Roles: Văn thư registers/releases documents; Chuyên viên drafts/handles assigned tasks; Lãnh đạo phòng/Director approve, sign and monitor SLA; Admin manages permission matrix.
- SLA defaults: near-due warning at T-24h, overdue flag after due date, escalation to manager after one overdue working day.
- Reports: overdue list, SLA by department, document volume by type/status, released document register and archive export audit.
- Permissions: department-based visibility, restricted document access, approval-level authorization and audited export/download.

## Risks
| Risk ID | Description | Mitigation |
|---|---|---|
| RISK-001 | Luồng phê duyệt/SLA thực tế có thể nhiều biến thể | MVP dùng approval matrix và SLA defaults; biến thể thêm đi qua Change Request |
| RISK-002 | Digital signature provider chưa có API contract | MVP hỗ trợ approval log; provider-specific digital signing đưa Phase 2 nếu chưa có contract |
| RISK-003 | Migration kho văn bản lịch sử lớn | MVP chỉ import/migration sample; full legacy migration estimate riêng |
""", encoding="utf-8")
    wb=Workbook(); ws=wb.active; ws.title="WBS"; ws.append(["Phase","Work Package","Owner"])
    for m in modules[:8]: ws.append(["Build", m, "Dev/BA"])
    wb.save(d/"02-wbs.xlsx")
    wb=Workbook(); ws=wb.active; ws.title="RACI"; ws.append(["Activity","Business","IT","Vendor","Sponsor"]); ws.append(["Scope baseline","R","C","C","A"]); wb.save(d/"03-raci.xlsx")
    wb=Workbook(); ws=wb.active; ws.title="Risks"; ws.append(["Risk","Impact","Mitigation"]); ws.append(["Unclear scope","High","Workshop + assumptions"]); wb.save(d/"04-risk-register.xlsx")
    (d / "05-status-report.md").write_text("# Status Report\n\nInitial customer-ready PMO pack completed for baseline review.\n", encoding="utf-8")
    (d / "06-change-request-template.md").write_text("# Change Request Template\n", encoding="utf-8")
    (d / "07-lessons-learned.md").write_text("# Lessons Learned\n", encoding="utf-8")
    project.mark_stage("pm", "completed")

def generate_po(project: Project) -> None:
    if _is_legal_project(project):
        return generate_legal_po(project)
    if not _is_asset_project(project):
        return generate_generic_po(project)
    domain = get_domain(project.config.domain_pack)
    d = project.root / "artifacts/po"
    d.mkdir(parents=True, exist_ok=True)
    (d / "01-vision.md").write_text(f"""# Product Vision

## Domain: Asset Management / Quản lý trang thiết bị, tài sản

## Vision Statement
Triển khai hệ thống Quản lý trang thiết bị, tài sản cho {project.config.customer}, giúp số hóa toàn bộ vòng đời tài sản từ ghi nhận, cấp phát, bàn giao, thu hồi, điều chuyển, kiểm kê, bảo trì, thanh lý đến báo cáo/audit. Sản phẩm ưu tiên MVP web-based, dữ liệu tập trung, phân quyền rõ ràng, traceability đầy đủ và có thể mở rộng tích hợp HRM/ERP/Kế toán ở Phase 2.

## MVP Boundaries
- Included: asset master, allocation/handover, return/transfer, inventory, maintenance, liquidation request, reports/export, role permission and audit log.
- Phase 2: realtime API integrations, RFID, advanced mobile/PWA, legal e-signature and complex rule engine.
- Excluded from MVP: production code delivery inside this documentation package, large-scale manual data cleansing without data profiling.

## Scope & Success Metrics
- Scope: quản lý vòng đời TTB/Tài sản gồm asset master, allocation/handover, return/transfer, inventory, maintenance, liquidation, reporting and permission/audit workflow.
- Linked REQ baseline: REQ-CORE-001, REQ-CORE-002, REQ-CORE-003, REQ-CORE-004, REQ-CORE-005.
- API/integration baseline: HRM import/export, ERP/accounting sync option, notification, report export.
- KPI: 100% tài sản MVP có mã duy nhất, trạng thái, người chịu trách nhiệm và audit trail; 95% giao dịch cấp phát/thu hồi có biên bản hoặc evidence.
- Review cadence: PO/PM/BA review theo từng release, evidence lưu trong quality output.

## Business Goals
### BG-001: Số hóa quản lý TTB/Tài sản
**Linked source:** SRC-001
**Priority:** P0
**Linked workflow:** asset create → allocate/handover → return/transfer → inventory/maintenance → report.

## Target Customer
- Sponsor/PM: chốt phạm vi, ngân sách, timeline và nghiệm thu.
- Asset Manager: vận hành danh mục tài sản, cấp phát, thu hồi, kiểm kê, bảo trì và thanh lý.
- Department Manager: phê duyệt/ghi nhận tài sản theo phòng ban.
- Staff/Employee: nhận bàn giao, xác nhận thu hồi và tra cứu tài sản được giao.
- IT/System Admin/Auditor: quản trị người dùng, phân quyền, log, backup và báo cáo kiểm soát.

## Feature Priorities
| Priority | Feature | Acceptance signal |
|---|---|---|
| P0 | Asset master + unique asset code | Create/update/search/export works with audit log |
| P0 | Allocation/handover/return/transfer | Status and holder history update correctly |
| P0 | Permission and audit | Unauthorized action is blocked and logged |
| P0 | Reports/export | Filter by department/status/group/date works |
| P1 | Maintenance/inventory/liquidation | Workflow captures evidence and manager review |

## Non-Goals
Không tự gửi báo giá chính thức khi chưa có human approval; không cam kết RFID/mobile native/realtime API nếu chưa có vendor/API contract.
""", encoding="utf-8")
    (d / "02-okr.md").write_text("# OKR Set\n\n| Objective | Key Result |\n|---|---|\n| Chuẩn hóa doc pipeline | 85% Gate pass sau <=2 retry |\n", encoding="utf-8")
    (d / "03-roadmap.md").write_text("# Roadmap\n\n## Now\nBA pipeline.\n\n## Next\nIC implementation pack.\n\n## Later\nGovernance dashboard.\n", encoding="utf-8")
    wb = Workbook(); ws = wb.active; ws.title = "Backlog"; ws.append(["Item", "RICE", "Priority"]); ws.append(["BA pipeline", 100, "P0"]); wb.save(d / "04-backlog.xlsx")
    (d / "05-release-notes.md").write_text("# Release Notes\n\n## v0.1\nInitial PMO Studio scaffold.\n", encoding="utf-8")
    project.mark_stage("po", "completed")


def _project_context(project_root: Path) -> dict:
    decisions = project_root / "artifacts/stage-0/scope-decision-matrix.md"
    decision_lines: list[str] = []
    if decisions.exists():
        for line in decisions.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("| DEC-SCOPE-"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) >= 3:
                    decision_lines.append(f"- {cells[0]}: {cells[2]}")
    return {"decision_lines": "\n".join(decision_lines)}


def generate_pm(project: Project) -> None:
    if _is_legal_project(project):
        return generate_legal_pm(project)
    if not _is_asset_project(project):
        return generate_generic_pm(project)
    domain = get_domain(project.config.domain_pack)
    d = project.root / "artifacts/pm"
    d.mkdir(parents=True, exist_ok=True)
    ctx = _project_context(project.root)
    (d / "01-charter.md").write_text(f"""# Project Charter

## Domain
Asset Management / Quản lý trang thiết bị, tài sản

## Objective
BG-001: Triển khai phân hệ quản lý trang thiết bị, tài sản cho {project.config.customer}, số hóa vòng đời tài sản từ khai báo, phân bổ, bàn giao, sử dụng, bảo trì/bảo hành, kiểm kê, điều chuyển, thu hồi, thanh lý đến báo cáo quản trị.

## Industry Context
Bối cảnh triển khai là nghiệp vụ quản lý tài sản nội bộ có liên quan HRM, ERP/Kế toán, Mua sắm/Kho, DMS và notification. Hệ thống cần kiểm soát trách nhiệm sử dụng tài sản, giảm nhập liệu thủ công, tăng auditability và hỗ trợ ra quyết định về chi phí/vòng đời tài sản.

## MVP Scope
- BR-CORE-001: Quản lý danh mục và hồ sơ tài sản/trang thiết bị, bao gồm mã tài sản, nhóm, serial, nguyên giá, ngày mua, tình trạng và đơn vị sử dụng. Linked source: SRC-001.
- BR-CORE-002: Quản lý phân bổ, bàn giao, thu hồi, điều chuyển và lịch sử sử dụng tài sản theo nhân viên/phòng ban/cost center. Linked source: SRC-001.
- BR-CORE-003: Quản lý bảo trì, bảo hành, sửa chữa, chứng từ và cảnh báo đến hạn. Linked source: SRC-001.
- BR-CORE-004: Báo cáo/dashboard về tồn kho, tài sản theo đơn vị/người dùng, tình trạng, khấu hao/giá trị còn lại và cảnh báo. Linked source: SRC-001.
- BR-CORE-005: Quản trị phân quyền, audit log, import/export dữ liệu và backup/restore. Linked source: SRC-001.

## Phase 2 / Optional Scope
- DEC-SCOPE-001: PWA/QR kiểm kê nâng cao hoặc native mobile nếu sponsor chọn option mở rộng.
- DEC-SCOPE-002: RFID chỉ triển khai sau PoC thiết bị/vendor.
- DEC-SCOPE-003: API realtime với HRM/ERP/Kế toán/Mua sắm/DMS nếu có integration contract.
- DEC-SCOPE-004: Kế toán/ERP là master dữ liệu tài chính; phân hệ tài sản hiển thị/đồng bộ giá trị tài chính và không ghi đè nếu chưa duyệt.
- DEC-SCOPE-005: Workflow configurable hoặc rule engine nếu nghiệp vụ yêu cầu nhiều cấp duyệt.
- DEC-SCOPE-006: Chữ ký điện tử/chữ ký số pháp lý tùy provider/license/chính sách nội bộ.
- DEC-SCOPE-007: MVP target 10-12 tuần sau scope baseline nếu không mở rộng mobile native, RFID full, rule engine hoặc integration realtime phức tạp.

## Out of Scope
- Production code application không được deliver trong vòng tài liệu này.
- RFID full integration chưa nằm trong MVP nếu chưa có thiết bị, SDK, vendor và PoC.
- Digital signature có giá trị pháp lý chưa cam kết trong MVP.
- Data cleansing thủ công quy mô lớn chưa bao gồm nếu chưa có data profiling.

## Timeline and Milestones
- M0 Discovery/Baseline: 1-2 tuần sau workshop scope.
- M1 MVP Build/Config: 8 tuần sau baseline, giả định chọn recommended defaults trong Scope Decision Matrix.
- M2 UAT/Go-live readiness: 2 tuần sau MVP build.
- Target go-live assumption: 10 tuần sau baseline nếu không mở rộng mobile native, RFID full, rule engine hoặc integration realtime phức tạp.

## Stakeholders and Governance
| Stakeholder | Role | Accountability |
|---|---|---|
| Sponsor/PM | Accountable | Chốt scope, timeline, ngân sách, baseline và nghiệm thu |
| Asset Manager | Responsible | Owner nghiệp vụ tài sản, workflow và dữ liệu vận hành |
| HR | Consulted | Employee/department/cost center source |
| Accounting | Consulted | Nguyên giá, khấu hao, giá trị còn lại, dữ liệu tài chính |
| IT/System Admin | Responsible | Phân quyền, tích hợp, backup, bảo mật, vận hành |
| Employee/Department Manager | Informed/Approver | Xác nhận bàn giao/thu hồi và phê duyệt nội bộ |

## Decision Baseline
- DEC-001: Stage 0 baseline tập trung vào phân hệ quản lý TTB/Tài sản, không dùng nội dung mặc định PMO Studio.
- DEC-002: Scope chia thành MVP, Phase 2 và Optional để kiểm soát ngân sách/rủi ro.
- DEC-003: Bắt buộc kiểm tra chất lượng, traceability và review checklist trước client-ready export.
{ctx['decision_lines']}

## Linked Outcomes
- Linked source: SRC-001
- Business goal: BG-001
- Linked BR: BR-CORE-001, BR-CORE-002, BR-CORE-003, BR-CORE-004, BR-CORE-005
- Linked scope decisions: DEC-SCOPE-001, DEC-SCOPE-002, DEC-SCOPE-003, DEC-SCOPE-004, DEC-SCOPE-005, DEC-SCOPE-006, DEC-SCOPE-007
- Success metric: MVP BR items có downstream REQ/US/AC/TC/EST trong baseline hiện tại; traceability được kiểm chứng trước export.

## Risks and Mitigations
| Risk ID | Description | Impact | Mitigation |
|---|---|---|---|
| RISK-001 | API contract cần baseline trước Phase 2 | High | MVP dùng import/export; API realtime Phase 2 |
| RISK-002 | RFID/chữ ký số phụ thuộc vendor/license | Medium | Đưa Optional, chỉ estimate sau PoC/provider confirmation |
| RISK-003 | Workflow phê duyệt phức tạp hơn giả định | High | MVP simple workflow; rule engine Phase 2 |
| RISK-004 | Dữ liệu legacy thiếu chuẩn mã tài sản | High | Data profiling và cleansing plan trước migration |

## Acceptance / Review
- PM validates timeline, RAID, decision baseline and scope split MVP/Phase 2/Optional.
- BA validates requirement evidence, BR/REQ/US/AC/TC coverage and assumption baseline closure.
- IC validates implementation readiness, integration assumptions, migration/cutover and UAT plan.
- Sponsor approves client-ready quotation only after scope baseline and assumptions are accepted.

## Referenced ID Appendix
| ID | Meaning |
|---|---|
| SRC-001 | Approved baseline for eOffice / Document Management business scope and assumptions. |
| REQ-CORE-001 | Incoming document intake, classification, assignment and tracking. |
| REQ-CORE-002 | Outgoing document drafting, review, signing and release. |
| REQ-CORE-003 | Work dossier task assignment, comments, completion and SLA tracking. |
| REQ-CORE-004 | Multi-level approval and signing workflow controls. |
| REQ-CORE-005 | Release numbering, recipient distribution and immutable publication log. |
| REQ-CORE-006 | SLA/dashboard/report filtering by department, status, age and document type. |
| REQ-CORE-007 | Archive search, permission-filtered retrieval and export audit. |
| REQ-CORE-008 | Due-date reminder and escalation notification workflow. |
| AC-001-01 | Incoming document registration creates unique intake number, metadata, attachment and audit event. |
| AC-001-02 | Outgoing draft approval records each review/signing step before release. |
| AC-001-03 | Work dossier assignment creates assignee task, SLA status and comment history. |
| AC-001-04 | Unauthorized/skipped approval is blocked and logged. |
| AC-001-05 | Released document is immutable except authorized revision flow. |
| AC-001-06 | SLA dashboard filters overdue documents by department/status/age/type. |
| AC-001-07 | Archive export/download respects permission and records audit evidence. |
| TST-001 | Login/permission smoke test. |
| TST-002 | Document intake/release smoke test. |
| TST-003 | Approval/SLA smoke test. |
| TST-004 | Report/export smoke test. |
| TST-005 | Notification/audit smoke test. |
""", encoding="utf-8")
    for name, headers, row in [
        ("02-wbs.xlsx", ["WBS", "Task", "Linked EST", "Owner"], ["1.1", "Build core", "EST-001", "SnailBot"]),
        ("03-raci.xlsx", ["Activity", "R", "A", "C", "I"], ["Quality Gate", "BA", "PM", "Dev", "Sponsor"]),
        ("04-risk-register.xlsx", ["Risk ID", "Description", "Impact", "Mitigation"], ["RISK-001", "Scope too wide", "High", "Phase release"]),
    ]:
        wb = Workbook(); ws = wb.active; ws.title = name.replace('.xlsx',''); ws.append(headers); ws.append(row); wb.save(d / name)
    (d / "05-status.md").write_text("# Status Report\n\nStatus: Green/Initial scaffold.\n", encoding="utf-8")
    (d / "06-cr-template.md").write_text("# Change Request: CR-001\n\n## Impact Analysis\nTBD.\n", encoding="utf-8")
    (d / "07-lessons-learned.md").write_text("# Lessons Learned\n\nTBD.\n", encoding="utf-8")
    project.mark_stage("pm", "completed")


def generate_ic(project: Project) -> None:
    domain = get_domain(project.config.domain_pack)
    d = project.root / "artifacts/ic"
    d.mkdir(parents=True, exist_ok=True)
    wb = Workbook(); ws = wb.active; ws.title = "Summary"; ws.append(["Metric", "Value"]); ws.append(["Fit", "TBD"]); detail = wb.create_sheet("Fit-Gap Detail"); detail.append(["BR/REQ ID", "Description", "Product Standard Capability", "Fit/Gap", "Gap Type", "Action", "Effort (md)", "Owner", "Risk"]); detail.append(["BR-CORE-001", f"Doc pipeline for {domain.label}", "Partial", "Gap", "Customization", f"Build PMO Studio for {domain.label}", 5, "Dev", "Medium"]); wb.save(d / "01-fit-gap.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "Summary"; ws.append(["Metric", "Value"]); org = wb.create_sheet("Org Settings"); org.append(["Parameter", "Value", "Default", "Required", "Description", "Owner", "Status"]); org.append(["org.timezone", "Asia/Ho_Chi_Minh", "Asia/Ho_Chi_Minh", "yes", "Timezone", "IC", "Confirmed"]); wb.create_sheet("User & Role"); wb.create_sheet("Master Data"); wb.create_sheet("Workflow Config"); wb.create_sheet("Integration Config"); wb.save(d / "02-config-workbook.xlsx")
    (d / "03-deployment-plan.md").write_text(_deployment_plan(project), encoding="utf-8")
    (d / "04-uat-plan.md").write_text(_uat_plan(project), encoding="utf-8")
    for i, name in enumerate(["training", "migration-plan", "cutover-plan", "go-live-checklist", "hypercare-plan"], start=5):
        (d / f"{i:02d}-{name}.md").write_text(f"# {name.replace('-', ' ').title()}\n\nInitial scaffold for Asset Management rollout.\n", encoding="utf-8")
    project.mark_stage("ic", "completed")


def _deployment_plan(project: Project) -> str:
    return f"""# Deployment Plan

## Document Control
- Document status: Baseline draft for customer review
- Customer: {project.config.customer}
- Linked source: SRC-001
- Linked scope decisions: DEC-SCOPE-001, DEC-SCOPE-003, DEC-SCOPE-004, DEC-SCOPE-005, DEC-SCOPE-007

## Deployment Scope
DP-001: Deploy MVP eOffice / Document Management baseline to staging/UAT environment for customer validation.
**Linked BR:** BR-CORE-001, BR-CORE-002, BR-CORE-003, BR-CORE-004, BR-CORE-005
**Linked REQ:** REQ-CORE-001, REQ-CORE-002, REQ-CORE-003, REQ-CORE-004, REQ-CORE-005, REQ-CORE-006, REQ-CORE-007, REQ-CORE-008

## Environment Baseline
| ID | Environment | Purpose | Owner | Status |
|---|---|---|---|---|
| ENV-001 | UAT/Staging | Customer UAT and sign-off rehearsal | IT/System Admin | Planned |
| ENV-002 | Production | Go-live target after UAT sign-off | IT/System Admin | Planned after UAT approval |

## Release Package
| ID | Package | Contents | Source | Status |
|---|---|---|---|---|
| REL-001 | eOffice MVP Release | Config, migration scripts, deployment notes, rollback package | PMO baseline + repository release tag | Planned |

## Deployment Steps
| Step ID | Activity | Owner | Entry Criteria | Exit Criteria | Rollback |
|---|---|---|---|---|---|
| CHK-001 | Pre-deployment checklist | PM + IT | Scope baseline approved | Access, backup, package, window confirmed | Do not deploy |
| DP-002 | Deploy release package to ENV-001 | DevOps/IT | REL-001 available | Application/config available for smoke test | RBK-001 |
| TST-001 | Login and role access smoke test | QA/BA | ENV-001 deployed | Văn thư/Chuyên viên/Lãnh đạo/Admin role access pass | RBK-001 |
| TST-002 | Document intake/release smoke test | QA/BA | ENV-001 deployed | Incoming/outgoing document workflow pass | RBK-001 |
| TST-003 | Approval and SLA smoke test | QA/BA | ENV-001 deployed | Multi-level approval and overdue dashboard pass | RBK-001 |
| TST-004 | Archive/report smoke test | QA/BA | ENV-001 deployed | Search/export respects permission | RBK-001 |
| TST-005 | Notification/audit smoke test | QA/BA | ENV-001 deployed | Reminder/escalation and audit log pass | RBK-001 |
| DP-003 | Production deployment to ENV-002 | DevOps/IT | UAT sign-off approved | Production smoke pass | RBK-001 |

## Validation Checklist
- TST-001: Login and role access works for Văn thư, Chuyên viên, Lãnh đạo phòng, Director and Admin.
- TST-002: Incoming/outgoing document create, submit, release and archive flow works in ENV-001.
- TST-003: Multi-level approval, due-date tracking and overdue dashboard smoke pass.
- TST-004: Report/dashboard/archive export respects department and restricted-document permissions.
- TST-005: Notification reminder/escalation and audit log capture critical changes.

## Rollback Plan
RBK-001: Restore previous stable package/config/database backup if deployment smoke test fails or business owner rejects go-live.

## Deployment Assumptions
- Deployment window baseline is outside peak business hours: 20:00-22:00 ICT, validated by PM/IT in cutover checklist.
- API realtime integrations nằm Phase 2 trừ khi contract và test endpoint đã sẵn sàng trước UAT.
- Production credentials and secrets are never stored in this artifact.


## Referenced ID Appendix
| ID | Meaning |
|---|---|
| SRC-001 | Approved baseline for eOffice / Document Management business scope and assumptions. |
| REQ-CORE-001 | Incoming document intake, classification, assignment and tracking. |
| REQ-CORE-002 | Outgoing document drafting, review, signing and release. |
| REQ-CORE-003 | Work dossier task assignment, comments, completion and SLA tracking. |
| REQ-CORE-004 | Multi-level approval and signing workflow controls. |
| REQ-CORE-005 | Release numbering, recipient distribution and immutable publication log. |
| REQ-CORE-006 | SLA/dashboard/report filtering by department, status, age and document type. |
| REQ-CORE-007 | Archive search, permission-filtered retrieval and export audit. |
| REQ-CORE-008 | Due-date reminder and escalation notification workflow. |
| AC-001-01 | Incoming document registration creates unique intake number, metadata, attachment and audit event. |
| AC-001-02 | Outgoing draft approval records each review/signing step before release. |
| AC-001-03 | Work dossier assignment creates assignee task, SLA status and comment history. |
| AC-001-04 | Unauthorized/skipped approval is blocked and logged. |
| AC-001-05 | Released document is immutable except authorized revision flow. |
| AC-001-06 | SLA dashboard filters overdue documents by department/status/age/type. |
| AC-001-07 | Archive export/download respects permission and records audit evidence. |
| TST-001 | Login/permission smoke test. |
| TST-002 | Document intake/release smoke test. |
| TST-003 | Approval/SLA smoke test. |
| TST-004 | Report/export smoke test. |
| TST-005 | Notification/audit smoke test. |

## Execution Detail
- Package version/tag: REL-001 maps to immutable release tag `eoffice-mvp-rel-001` in the deployment repository.
- Environment endpoints: ENV-001 UAT `/uat/eoffice`, ENV-002 Production `/eoffice` (final hostnames supplied by customer IT).
- Backup procedure: export database dump, config snapshot and uploaded evidence files before DP-003; verify backup checksum and restore dry-run package before production deployment.
- Smoke command checklist: login, document intake, approval, SLA dashboard, archive export, notification/audit review.
- Rollback verification: restore previous stable package/config/database backup to staging, rerun TST-001 through TST-005, then approve production rollback if smoke passes.
- Rollback trigger: critical smoke failure, data corruption risk, or sponsor reject during go-live checkpoint.
"""


def _uat_plan(project: Project) -> str:
    return f"""# UAT Plan

## Document Control
- Document status: Baseline draft for customer review
- Customer: {project.config.customer}
- UAT owner: Sponsor/PM + Văn thư lead + Department Head
- Planned window: After MVP deployment to ENV-001
- Linked source: SRC-001

## UAT Scope
| UAT ID | Scope Item | Linked Requirement | Priority |
|---|---|---|---|
| UAT-001 | Incoming/outgoing document registration and metadata | REQ-CORE-001, REQ-CORE-002 | P0 |
| UAT-002 | Multi-level approval, signing and release | REQ-CORE-004, REQ-CORE-005 | P0 |
| UAT-003 | Work dossier assignment, SLA tracking and overdue dashboard | REQ-CORE-003, REQ-CORE-006 | P0 |
| UAT-004 | Archive search, report/export and restricted document permission | REQ-CORE-006, REQ-CORE-007 | P0 |
| UAT-005 | Reminder/escalation notification and audit log | REQ-CORE-008 | P1 |

## Upstream Requirement and Test Reference
| ID | Definition |
|---|---|
| SRC-001 | Approved baseline for eOffice MVP scope and assumptions. |
| REQ-CORE-001 | Incoming document intake, classification, assignment and tracking. |
| REQ-CORE-002 | Outgoing document drafting, review, signing and release. |
| REQ-CORE-003 | Work dossier assignment, comments, completion and SLA tracking. |
| REQ-CORE-004 | Multi-level approval and signing workflow controls. |
| REQ-CORE-005 | Release numbering, recipient distribution and immutable publication log. |
| REQ-CORE-006 | SLA dashboard/report filtering by department, status, age and document type. |
| REQ-CORE-007 | Archive search, permission-filtered retrieval and export audit. |
| REQ-CORE-008 | Due-date reminder and escalation notification workflow. |
| TST-001 | Login and role permission smoke test. |
| TST-002 | Document intake/release smoke test. |
| TST-003 | Approval/SLA smoke test. |
| TST-004 | Archive/report/export smoke test. |
| TST-005 | Notification/audit smoke test. |

## Out of Scope for MVP UAT
- UAT-OOS-001: RFID full integration unless PoC approved.
- UAT-OOS-002: CA digital signature unless provider/license confirmed.
- UAT-OOS-003: API realtime integrations unless contract and test endpoint are ready.

## Test Scenarios
| Scenario ID | Linked Req/Test | Given | When | Then | Owner | Pass Criteria |
|---|---|---|---|---|---|---|
| UAT-001 | REQ-CORE-001 / TST-002 | Văn thư has valid account; sample incoming document metadata and attachment exist | Register incoming document and assign to department | Unique intake number created; metadata/attachment saved; status is Assigned; audit log recorded | Văn thư + QA | No critical defect; document can be searched by intake number |
| UAT-002 | REQ-CORE-002 / TST-002 | Chuyên viên has draft document, recipient list and approval route | Submit outgoing draft for review/signing and release after approval | Approval steps are recorded; release number and recipients are saved; released version is immutable | Chuyên viên + Văn thư | No critical defect; release cannot occur before required approval |
| UAT-003 | REQ-CORE-003 / TST-003 | Department Head has assignee list; due date T+1 and overdue sample exist | Assign work dossier, update comments/completion and open SLA dashboard | Task appears in assignee workspace; SLA status and overdue count are correct | Department Head + QA | No high defect; SLA dashboard matches task data |
| UAT-004 | REQ-CORE-006, REQ-CORE-007 / TST-004 | Normal/restricted documents exist across two departments; archive records and export audit logging are enabled | Search archive by keyword/metadata, open permitted record, attempt restricted retrieval, filter report by department/status/age/type and export XLSX/PDF | Archive returns only permitted records; restricted retrieval is blocked; export matches filters and export/download audit event is recorded | Sponsor/PM + QA | No critical defect; archive retrieval, permission filtering and export audit evidence are verified |
| UAT-005 | REQ-CORE-008 / TST-005 | Reminder threshold T-24h and escalation after one overdue working day configured | Run notification job for near-due and overdue tasks | Assignee reminder and manager escalation are created/sent; notification status and audit event are logged | IT Admin/QA | No critical defect; notification/audit evidence is visible |

## Entry Criteria
- ENV-001 deployed and smoke tested via TST-001..TST-005.
- UAT test accounts and sample document/workflow data are prepared.
- Scope Decision Matrix recommended defaults accepted for MVP, with Phase 2 items tracked separately.

## Exit Criteria
- All P0 UAT scenarios pass or have approved workaround.
- No open critical/high defect blocks go-live.
- Sponsor/PM signs off go-live readiness or requests change control.

## Sign-off
| Role | Name | Decision | Date |
|---|---|---|---|
| Sponsor/PM | Customer sponsor/delegate | Pending UAT execution | Planned after ENV-001 validation |
| Văn thư lead | Customer document owner/delegate | Pending UAT execution | Planned after ENV-001 validation |
| IT/System Admin | Customer IT owner/delegate | Pending technical validation | Planned after ENV-001 validation |
"""
