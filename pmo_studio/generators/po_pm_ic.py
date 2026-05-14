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

def generate_po(project: Project) -> None:
    if _is_legal_project(project):
        return generate_legal_po(project)
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
| SRC-001 | Source-extracted baseline for Asset Management business scope and assumptions. |
| REQ-CORE-001 | Asset master with system-generated asset_code and required asset fields. |
| REQ-CORE-002 | Allocation/handover/return/transfer workflow with holder history and evidence. |
| REQ-CORE-003 | Inventory, maintenance and liquidation workflow with variance/review controls. |
| REQ-CORE-004 | Reports/dashboard/export by department, status, group, holder and period. |
| REQ-CORE-005 | Permission, audit log and import/export validation. |
| AC-001-01 | Create asset generates unique asset_code and audit event. |
| AC-001-02 | Allocation updates status, holder history and evidence. |
| AC-001-03 | Missing required asset fields blocks save. |
| AC-001-04 | Unauthorized UI/API action returns 403/access denied and logs security event. |
| AC-001-05 | Invalid asset status transition is blocked. |
| AC-001-06 | Inventory variance requires reason/evidence/review. |
| AC-001-07 | Import invalid rows rejected with row-level errors. |
| TST-001 | Login/permission smoke test. |
| TST-002 | Asset master smoke test. |
| TST-003 | Allocation workflow smoke test. |
| TST-004 | Report/export smoke test. |
| TST-005 | Audit/security smoke test. |
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
DP-001: Deploy MVP Asset Management baseline to staging/UAT environment for customer validation.
**Linked BR:** BR-CORE-001, BR-CORE-002, BR-CORE-003, BR-CORE-004, BR-CORE-005
**Linked REQ:** REQ-CORE-001, REQ-CORE-002, REQ-CORE-003, REQ-CORE-004, REQ-CORE-005

## Environment Baseline
| ID | Environment | Purpose | Owner | Status |
|---|---|---|---|---|
| ENV-001 | UAT/Staging | Customer UAT and sign-off rehearsal | IT/System Admin | Planned |
| ENV-002 | Production | Go-live target after UAT sign-off | IT/System Admin | Planned after UAT approval |

## Release Package
| ID | Package | Contents | Source | Status |
|---|---|---|---|---|
| REL-001 | Asset Management MVP Release | Config, migration scripts, deployment notes, rollback package | PMO baseline + repository release tag | Planned |

## Deployment Steps
| Step ID | Activity | Owner | Entry Criteria | Exit Criteria | Rollback |
|---|---|---|---|---|---|
| CHK-001 | Pre-deployment checklist | PM + IT | Scope baseline approved | Access, backup, package, window confirmed | Do not deploy |
| DP-002 | Deploy release package to ENV-001 | DevOps/IT | REL-001 available | Application/config available for smoke test | RBK-001 |
| TST-001 | Smoke test critical flows | QA/BA | ENV-001 deployed | Login, asset master, allocation, report smoke pass | RBK-001 |
| DP-003 | Production deployment to ENV-002 | DevOps/IT | UAT sign-off approved | Production smoke pass | RBK-001 |

## Validation Checklist
- TST-001: Login and role access works for Asset Manager, HR, Accounting, Employee, IT Admin.
- TST-002: Asset master create/update/import flow works in ENV-001.
- TST-003: Allocation/handover/return workflow smoke pass.
- TST-004: Report/dashboard smoke pass.
- TST-005: Audit log captures critical changes.

## Rollback Plan
RBK-001: Restore previous stable package/config/database backup if deployment smoke test fails or business owner rejects go-live.

## Deployment Assumptions
- Deployment window baseline is outside peak business hours: 20:00-22:00 ICT, validated by PM/IT in cutover checklist.
- API realtime integrations nằm Phase 2 trừ khi contract và test endpoint đã sẵn sàng trước UAT.
- Production credentials and secrets are never stored in this artifact.


## Referenced ID Appendix
| ID | Meaning |
|---|---|
| SRC-001 | Source-extracted baseline for Asset Management business scope and assumptions. |
| REQ-CORE-001 | Asset master with system-generated asset_code and required asset fields. |
| REQ-CORE-002 | Allocation/handover/return/transfer workflow with holder history and evidence. |
| REQ-CORE-003 | Inventory, maintenance and liquidation workflow with variance/review controls. |
| REQ-CORE-004 | Reports/dashboard/export by department, status, group, holder and period. |
| REQ-CORE-005 | Permission, audit log and import/export validation. |
| AC-001-01 | Create asset generates unique asset_code and audit event. |
| AC-001-02 | Allocation updates status, holder history and evidence. |
| AC-001-03 | Missing required asset fields blocks save. |
| AC-001-04 | Unauthorized UI/API action returns 403/access denied and logs security event. |
| AC-001-05 | Invalid asset status transition is blocked. |
| AC-001-06 | Inventory variance requires reason/evidence/review. |
| AC-001-07 | Import invalid rows rejected with row-level errors. |
| TST-001 | Login/permission smoke test. |
| TST-002 | Asset master smoke test. |
| TST-003 | Allocation workflow smoke test. |
| TST-004 | Report/export smoke test. |
| TST-005 | Audit/security smoke test. |

## Execution Detail
- Package version/tag: REL-001 maps to immutable release tag `asset-mgmt-mvp-rel-001` in the deployment repository.
- Environment endpoints: ENV-001 UAT `/uat/asset-management`, ENV-002 Production `/asset-management` (final hostnames supplied by customer IT).
- Backup procedure: export database dump, config snapshot and uploaded evidence files before DP-003; verify backup checksum and restore dry-run package before production deployment.
- Smoke command checklist: login, asset create, allocation, report export, audit log review.
- Rollback verification: restore previous stable package/config/database backup to staging, rerun TST-001 through TST-005, then approve production rollback if smoke passes.
- Rollback trigger: critical smoke failure, data corruption risk, or sponsor reject during go-live checkpoint.
"""


def _uat_plan(project: Project) -> str:
    return f"""# UAT Plan

## Document Control
- Document status: Baseline draft for customer review
- Customer: {project.config.customer}
- UAT owner: Sponsor/PM + Asset Manager
- Planned window: After MVP deployment to ENV-001
- Linked source: SRC-001

## UAT Scope
| UAT ID | Scope Item | Linked Requirement | Priority |
|---|---|---|---|
| UAT-001 | Asset master and classification | REQ-CORE-001 | P0 |
| UAT-002 | Allocation, handover, return, transfer | REQ-CORE-002 | P0 |
| UAT-003 | Maintenance/warranty tracking | REQ-CORE-003 | P1 |
| UAT-004 | Reporting/dashboard/export | REQ-CORE-004 | P0 |
| UAT-005 | Role permission and audit log | REQ-CORE-005 | P0 |

## Upstream Requirement and Test Reference
| ID | Definition |
|---|---|
| SRC-001 | Approved source-extracted baseline for Asset Management MVP scope and assumptions. |
| REQ-CORE-001 | Asset master: tạo/cập nhật/tra cứu/export tài sản với system-generated asset_code, serial, group, purchase info, status, department, holder và attachment. |
| REQ-CORE-002 | Asset transaction workflow: allocation, handover, return and transfer with valid status transition, holder history and evidence. |
| REQ-CORE-003 | Inventory, maintenance and liquidation: campaigns, variance, maintenance ticket, liquidation request, review and locked invalid transitions. |
| REQ-CORE-004 | Reports/dashboard: filter/export by department, holder, group, status, date period, inventory variance and transaction history. |
| REQ-CORE-005 | Permission/audit/import-export: role-based UI/API authorization, audit log, import validation and backup/export control. |
| TST-001 | Login and role permission smoke test. |
| TST-002 | Asset master creation/import smoke test. |
| TST-003 | Allocation/handover workflow smoke test. |
| TST-004 | Report/dashboard/export smoke test. |
| TST-005 | Audit/security smoke test. |

## Out of Scope for MVP UAT
- UAT-OOS-001: RFID full integration unless PoC approved.
- UAT-OOS-002: CA digital signature unless provider/license confirmed.
- UAT-OOS-003: API realtime integrations unless contract and test endpoint are ready.

## Test Scenarios
| Scenario ID | Linked Req/Test | Given | When | Then | Owner | Pass Criteria |
|---|---|---|---|---|---|---|
| UAT-001 | REQ-CORE-001 / TST-002 | Asset Manager has valid account; Department IT, asset group Laptop and sample serial SN001 exist | Create one asset manually and import one valid asset row | Manual and imported asset records are saved with system-generated asset_code, required fields, status Available and audit log | Asset Manager | No critical defect; created assets can be searched by asset_code/serial |
| UAT-002 | REQ-CORE-002 / TST-003 | Asset AST-2026-00001 is Available; Employee E001 and handover evidence file exist | Allocate and handover asset to E001, then perform return/transfer check | Handover record links employee, department, asset, date, evidence and status; holder history is updated | Asset Manager + HR | No critical defect; no duplicate allocation is allowed |
| UAT-003 | REQ-CORE-003 / TST-003 | Inventory campaign Q2 exists; asset AST-2026-00001 is expected but missing/damaged | Submit inventory variance with reason and evidence; create maintenance/liquidation follow-up if needed | Variance is Pending Manager Review; maintenance/liquidation locks new allocation until review closes | Asset Manager + Department Manager | No high defect; reason/evidence/review are visible |
| UAT-004 | REQ-CORE-004 / TST-004 | Allocated assets exist for Department IT and current month | Filter report by department/status/period and export XLSX/PDF | Report matches filters and includes asset_code, name, group, holder, department, status, original_cost and date columns | Accounting/PM | No critical defect; exported totals match on-screen totals |
| UAT-005 | REQ-CORE-005 / TST-001/TST-005 | Admin, Asset Manager, Staff and Auditor test users exist | Staff attempts allocation API/UI; Auditor opens report/audit log read-only | Unauthorized action returns access denied/403 and logs security event; Auditor cannot edit records | IT Admin/QA | No critical defect; security audit event is visible |

## Entry Criteria
- ENV-001 deployed and smoke tested via TST-001..TST-005.
- UAT test accounts and sample asset data are prepared.
- Scope Decision Matrix recommended defaults accepted for MVP, with Phase 2 items tracked separately.

## Exit Criteria
- All P0 UAT scenarios pass or have approved workaround.
- No open critical/high defect blocks go-live.
- Sponsor/PM signs off go-live readiness or requests change control.

## Sign-off
| Role | Name | Decision | Date |
|---|---|---|---|
| Sponsor/PM | Quang Snail / delegated PM | Pending UAT execution | Planned after ENV-001 validation |
| Asset Manager | Customer asset owner/delegate | Pending UAT execution | Planned after ENV-001 validation |
| IT/System Admin | Customer IT owner/delegate | Pending technical validation | Planned after ENV-001 validation |
"""
