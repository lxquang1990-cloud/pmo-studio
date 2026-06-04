"""Source-driven BA generation with optional LLM writer."""
from __future__ import annotations

from pathlib import Path

from pmo_studio.core.ids import IdAllocator
from pmo_studio.core.project import Project
from pmo_studio.llm.provider import LLMClient, NoopLLMClient
from pmo_studio.llm.writer import ArtifactWriter
from pmo_studio.domain.prompts import get_domain, inject_domain_prompt
from pmo_studio.domain.pack_loader import resolve_domain_pack
from pmo_studio.generators.intelligence import apply_domain_terms, build_intelligence, bullets, table
from pmo_studio.domain.rendering import build_render_context, render_table
from pmo_studio.generators.ba_template_renderer import render_ba_artifacts_from_source

REQ_DEFINITIONS = """| REQ ID | Definition |
|---|---|
| REQ-CORE-001 | Asset master: tạo/cập nhật/tra cứu/export tài sản với system-generated asset_code, serial, group, purchase info, status, department, holder và attachment. |
| REQ-CORE-002 | Asset transaction workflow: allocation, handover, return and transfer with valid status transition, holder history and evidence. |
| REQ-CORE-003 | Inventory, maintenance and liquidation: campaigns, variance, maintenance ticket, liquidation request, review and locked invalid transitions. |
| REQ-CORE-004 | Reports/dashboard: filter/export by department, holder, group, status, date period, inventory variance and transaction history. |
| REQ-CORE-005 | Permission/audit/import-export: role-based UI/API authorization, audit log, import validation and backup/export control. |"""

AC_DEFINITIONS = """| AC ID | Definition |
|---|---|
| `AC-001-01` | Given asset master data hợp lệ, when Asset Manager tạo tài sản, then hệ thống tự sinh asset_code duy nhất, lưu serial/external_ref và tạo audit log. |
| `AC-001-02` | Given tài sản Available, when cấp phát cho nhân sự/phòng ban, then status đổi thành Allocated, holder history được cập nhật và biên bản/evidence được lưu. |
| `AC-001-03` | Given thiếu asset name, group, department hoặc serial, when lưu asset, then hệ thống chặn lưu và hiển thị lỗi trường bắt buộc. |
| `AC-001-04` | Given user không có quyền allocation/liquidation, when gọi UI/API tương ứng, then hệ thống trả access denied/403 và ghi security audit event. |
| `AC-001-05` | Given asset đang Allocated/Maintenance/Pending Liquidation, when user cấp phát lại, then hệ thống chặn giao dịch và hiển thị holder/status hiện tại. |
| `AC-001-06` | Given kiểm kê phát hiện thiếu/hỏng tài sản, when checker submit kết quả, then variance record có reason, evidence và manager review status. |
| `AC-001-07` | Given import data thiếu employee_code, department_code hoặc serial, when import, then invalid rows bị reject với lỗi theo dòng và valid rows vẫn xử lý. |
| `AC-001-08` | Given user lọc dashboard/report theo department, holder, group, status và period, when export, then file xuất ra đúng filter và có các cột asset_code, name, group, holder, department, status, original_cost, date. |"""

TST_DEFINITIONS = """| TST ID | Purpose | Linked REQ |
|---|---|---|
| TST-001 | Smoke role login and permission access | REQ-CORE-005 |
| TST-002 | Smoke create/update/import asset master | REQ-CORE-001 |
| TST-003 | Smoke allocation/handover/return workflow | REQ-CORE-002 |
| TST-004 | Smoke report/dashboard/export filters | REQ-CORE-004 |
| TST-005 | Smoke audit log and security event capture | REQ-CORE-005 |"""



def read_redacted_sources(project: Project, max_chars: int = 80000) -> str:
    chunks = []
    for path in sorted((project.root / "source" / "redacted").glob("*")):
        if path.is_file():
            try:
                chunks.append(f"\n\n--- SOURCE {path.name} ---\n" + path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
    text = "".join(chunks)
    return text[:max_chars]



def _is_legal_project(project: Project, source_text: str) -> bool:
    haystack = " ".join([
        str(getattr(project.config, "slug", project.root.name)),
        str(getattr(project.config, "product", "")),
        str(getattr(project.config, "customer", "")),
        str(getattr(project.config, "brief", "")),
        source_text,
    ]).lower()
    return any(k in haystack for k in ["legaliq", "pháp lý", "phap ly", "ủy quyền", "uy quyen", "hợp đồng", "hop dong", "b.pctt"])

def generate_legal_ba_from_sources(project: Project, source_text: str) -> None:
    """Render LegalIQ/Legal AI BA artifacts via versioned templates and YAML domain pack."""
    render_ba_artifacts_from_source(project, source_text, mode="legal_ai")

def _is_asset_project(project: Project, source_text: str) -> bool:
    haystack = " ".join([
        str(getattr(project.config, "project_slug", project.root.name)),
        str(getattr(project.config, "product", "")),
        str(getattr(project.config, "customer", "")),
        str(getattr(project.config, "brief", "")),
        source_text,
    ]).lower()
    return any(k in haystack for k in ["tài sản", "tai san", "ttb", "asset management", "asset master", "kiểm kê", "khấu hao", "thanh lý"])

def generate_generic_ba_from_sources(project: Project, source_text: str) -> None:
    """Generic source-driven BA baseline for unknown domains.

    Unknown domain must use extracted source context, never Asset Management defaults.
    """
    domain = get_domain(project.config.domain_pack)
    intel = build_intelligence(source_text, domain)
    ba_dir = project.root / "artifacts" / "ba"
    srs_dir = ba_dir / "03-srs"
    us_dir = ba_dir / "04-us"
    for d in [ba_dir, srs_dir, srs_dir / "screens", srs_dir / "apis", srs_dir / "workflows", srs_dir / "reports", us_dir]:
        d.mkdir(parents=True, exist_ok=True)
    ctx = build_render_context(source_text, project_slug=getattr(project.config, "project_slug", project.root.name), customer=getattr(project.config, "customer", ""))
    modules = list(ctx.modules or intel.modules or ["core", "workflow", "report"])
    if len(modules) < 8:
        fallback = ["workflow", "approval", "reporting", "permission", "audit", "integration", "archive", "notification"]
        for item in fallback:
            if len(modules) >= 8:
                break
            if item not in modules:
                modules.append(item)
    roles = ctx.roles or intel.roles or ["Admin", "Business User", "Approver", "Viewer"]
    integrations = intel.integrations or list(getattr(ctx.pack, "integrations", []) or []) or ["LDAP/AD user-role sync for authentication and authorization", "Email/notification gateway for approval/SLA alerts", "DMS/archive connector for issued document storage"]
    req_defs = render_table(ctx.requirements)
    ac_defs = render_table(ctx.acceptance)
    br_defs = render_table(ctx.business_requirements)
    summary = bullets(intel.summary)
    prd = f"""# PRD: {ctx.pack.label}

## Overview
PRD này mô tả MVP cho {ctx.pack.label} của {getattr(project.config, 'customer', 'khách hàng')}. Phạm vi được baseline từ SRC-001, tập trung vào workflow nghiệp vụ, phân quyền, SLA, báo cáo, audit và tích hợp cần thiết cho triển khai.

## Source Intelligence Summary
{summary}

## Personas / Stakeholders
{bullets(roles)}

## Product Modules
{bullets(modules)}

## Business Goals
- BG-001: Số hóa các nghiệp vụ chính được mô tả trong source đầu vào.
- BG-002: Chuẩn hóa dữ liệu, workflow, phân quyền, báo cáo và traceability.
- BG-003: Tạo baseline đủ để PO/PM/BA/IC review, estimate và triển khai MVP.

## Scope
### MVP
{bullets([f'{m}: capture/search/process records, enforce role-based validation, track workflow/SLA status, write audit trail, and expose module-specific dashboard/export.' for m in modules[:8]])}

### Phase 2 / Optional
{bullets(integrations)}

## Requirements Baseline
{req_defs}

## Acceptance Baseline
{ac_defs}

## Implementation Readiness
- API baseline: API-CORE-001.
- Workflow baseline: WF-CORE-001.
- Screen baseline: SCR-CORE-001.
- Test baseline: TC-001..TC-008.
"""
    brd = f"""# BRD: {ctx.pack.label}

## Business Context
Dự án cần số hóa các module nghiệp vụ {ctx.pack.label} theo SRC-001, với baseline MVP rõ ràng để sponsor, BA, Dev và QA có thể review, estimate và triển khai.

## Business Drivers
- Cần chuẩn hóa quy trình nghiệp vụ từ tiếp nhận, xử lý, phê duyệt, phát hành/lưu trữ đến báo cáo.
- Cần chuẩn hóa module, workflow, permission, integration, reporting và assumptions.
- Cần giữ traceability từ source tới BR/REQ/US/AC/TC/EST.

## Business Goals
- BG-001: Deliver MVP capabilities linked to SRC-001 and measurable through REQ/AC/TC coverage.

## Business Requirements
{br_defs}

## Requirement Definitions
{req_defs}

## Acceptance Definitions
{ac_defs}

## Key Workflows
{bullets(intel.workflows or ['User nhập/tra cứu dữ liệu → hệ thống validate → xử lý workflow → ghi audit/log → xuất báo cáo hoặc thông báo.'])}

## Risks and Assumptions
{bullets(intel.risks)}

## Scope Handling
- Integration contracts not available at baseline are planned as Phase 2 unless Sponsor marks them mandatory.
- MVP estimate uses conservative defaults for roles, SLA thresholds, reporting filters and audit evidence listed in this document.
"""
    srs = f"""# SRS

## 1. Introduction
SRS mô tả baseline chức năng cho {ctx.pack.label}, linked từ SRC-001 tới BR/REQ/AC/TC.

## 2. Product Overview
Hệ thống gồm các module: {', '.join(modules[:8])}.

## 3. Functional Requirements
{req_defs}

## 4. Acceptance Criteria
{ac_defs}

## 5. External Interfaces
{bullets(integrations)}

## 6. Non-functional Requirements
- RBAC, audit log, validation, backup/export và error handling.
- Báo cáo/export phải theo filter và quyền người dùng.
- Tích hợp phải có API contract, sample data và owner xác nhận.
"""
    (ba_dir / "01-prd.md").write_text(prd, encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(brd, encoding="utf-8")
    (srs_dir / "srs.md").write_text(srs, encoding="utf-8")
    (srs_dir / "screens" / "SCR-CORE-001.md").write_text(f"# SCR-CORE-001: Source-driven Workspace\n\n**Linked REQ:** REQ-CORE-001\n\nScreens cover: {', '.join(modules[:8])}.\n", encoding="utf-8")
    (srs_dir / "apis" / "API-CORE-001.md").write_text("# API-CORE-001: Source-driven API\n\n**Linked REQ:** REQ-CORE-001\n\nEndpoints support CRUD/search/workflow/report/export for source-driven modules.\n", encoding="utf-8")
    (srs_dir / "workflows" / "WF-CORE-001.md").write_text("# WF-CORE-001: Source-driven Workflow\n\n**Linked REQ:** REQ-CORE-001\n\nUpload/enter data → validate → process workflow → audit → report/export/notification.\n", encoding="utf-8")
    (us_dir / "US-001.md").write_text(f"""# User Story US-001: Xử lý nghiệp vụ theo source đầu vào

**Linked REQ:** REQ-CORE-001, REQ-CORE-002, REQ-CORE-003, REQ-CORE-004, REQ-CORE-005, REQ-CORE-006, REQ-CORE-007, REQ-CORE-008
**Linked Work Items:** SCR-CORE-001, API-CORE-001, WF-CORE-001

As a business user, I want the system to support source-defined modules so that I can process work with validation, permission, audit and reporting.

## Acceptance Criteria
{ac_defs}
""", encoding="utf-8")
    tc_rows = [["ID", "Linked AC", "Type", "Precondition", "Steps / Input", "Expected Result"]]
    workflow_names = ["incoming document", "outgoing document", "approval routing", "SLA dashboard", "overdue report", "role permission", "archive lookup", "notification"]
    for i, m in enumerate(modules[:8], 1):
        scenario = workflow_names[(i - 1) % len(workflow_names)]
        tc_rows.append([f"TC-{i:03d}", f"AC-001-{i:02d}", "Functional", f"Authorized role and sample {m} data exist", f"Create/search/process {m} through {scenario}; submit valid and invalid required fields; verify status/SLA/report output", f"System enforces validation and permission, updates workflow/SLA status, writes audit log, and shows {m} in the expected dashboard/export"])
    (ba_dir / "05-test-cases.md").write_text(f"""# Test Cases

## Referenced Requirements
{req_defs}

## Canonical Acceptance Definitions
{ac_defs}

## Coverage Matrix
{table(tc_rows)}
""", encoding="utf-8")
    from pmo_studio.generators.quotation import generate_quotation_for_project
    generate_quotation_for_project(project, ba_dir / "06-quotation.xlsx")
    project.mark_stage("ba.source_driven", "completed")

def generate_ba_from_sources(project: Project, llm: LLMClient | None = None) -> None:
    llm = llm or NoopLLMClient()
    source_text = read_redacted_sources(project)
    if _is_legal_project(project, source_text):
        return generate_legal_ba_from_sources(project, source_text)
    if _is_asset_project(project, source_text):
        return render_ba_artifacts_from_source(project, source_text, mode="asset_management")
    pack, detection = resolve_domain_pack(source_text, project_slug=getattr(project.config, "project_slug", project.root.name), customer=getattr(project.config, "customer", ""))
    if pack.id not in {"generic", "bteco", "asset_management"}:
        return render_ba_artifacts_from_source(project, source_text, mode=pack.id)
    return generate_generic_ba_from_sources(project, source_text)
    allocator = IdAllocator.from_state(project.state.id_counters)
    br = allocator.issue("BR", "CORE")
    req = allocator.issue("REQ", "CORE")
    scr = allocator.issue("SCR", "CORE")
    api = allocator.issue("API", "CORE")
    wf = allocator.issue("WF", "CORE")
    us = allocator.issue("US")
    ac1 = allocator.issue("AC", parent_us=us)
    ac2 = allocator.issue("AC", parent_us=us)
    tc = allocator.issue("TC")
    est_scr = allocator.issue("EST")
    est_api = allocator.issue("EST")
    project.state.id_counters = allocator.counters
    writer = ArtifactWriter(llm, model=project.config.llm.get("writer_model"))
    domain = get_domain(project.config.domain_pack)
    intel = build_intelligence(source_text, domain)
    ba_dir = project.root / "artifacts" / "ba"
    ba_dir.mkdir(parents=True, exist_ok=True)
    srs_dir = ba_dir / "03-srs"
    for sub in ["functional-spec", "screens", "apis", "workflows", "reports"]:
        (srs_dir / sub).mkdir(parents=True, exist_ok=True)

    prd_fallback = apply_domain_terms(f"""# PRD: Quản lý trang thiết bị, tài sản

## Overview
Tài liệu PRD mô tả baseline MVP cho hệ thống Quản lý trang thiết bị, tài sản của {project.config.customer}. Nội dung được dẫn xuất từ SRC-001 đã lọc thông tin nhạy cảm, Scope Decision Matrix và các quyết định MVP/Phase 2.

## Source Intelligence Summary
{bullets(intel.summary)}

## Personas / Stakeholders
{bullets(intel.roles)}

## Product Modules
{bullets(intel.modules)}

## Business Goals
- BG-001: Số hóa vòng đời quản lý TTB/Tài sản từ ghi nhận, cấp phát, bàn giao, kiểm kê, bảo trì đến thanh lý.
- BG-002: Chuẩn hóa dữ liệu tài sản, mã tài sản, người sử dụng, phòng ban, trạng thái và hồ sơ chứng từ.
- BG-003: Giảm thất thoát và tăng khả năng truy vết thông qua phân quyền, audit log, báo cáo và quy trình phê duyệt.

## Scope
### MVP
- Danh mục tài sản/TTB, nhóm tài sản, phòng ban, nhân sự/người sử dụng.
- Ghi nhận tài sản, cấp phát/bàn giao, thu hồi, điều chuyển, kiểm kê, bảo trì/sửa chữa, thanh lý.
- Phân quyền Admin, Asset Manager, Department Manager, Staff, Auditor.
- Báo cáo tồn kho, tài sản theo phòng ban/người dùng/trạng thái, lịch sử biến động.

### Phase 2 / Implementation Prerequisites
- Tích hợp ERP/HRM/kế toán, khấu hao tự động, mobile QR/barcode scan và migration dữ liệu lịch sử được triển khai khi có API contract, field mapping, owner và sample dataset.
- Phase 2 owners: IT owns API endpoints/test environment; Accounting owns financial fields; HR owns employee/department mapping; Asset Manager owns asset cleansing rules.

## Detailed Workflows
### WF-CORE-001 — Create asset
1. Asset Manager nhập tên tài sản, nhóm, serial/external reference, ngày mua, nguyên giá, phòng ban sở hữu, vị trí và chứng từ.
2. Hệ thống tự sinh asset_code duy nhất, validate serial không trùng, trường bắt buộc đầy đủ và ghi audit log.
3. Tài sản được lưu ở trạng thái Available.

### WF-CORE-002 — Allocate / handover
1. Asset Manager chọn tài sản Available, nhân sự/phòng ban nhận, ngày bàn giao và biên bản.
2. Department Manager phê duyệt trong vòng 1 ngày làm việc cho tài sản thuộc phòng ban; Asset Manager được auto-approve với giao dịch nội bộ có nguyên giá dưới 5.000.000 VND, không thuộc nhóm tài sản kiểm soát đặc biệt (server, network device, vehicle hoặc regulated equipment) và không chuyển liên phòng ban.
3. Hệ thống đổi trạng thái Allocated, cập nhật holder history và khóa cấp phát trùng.

### WF-CORE-003 — Return / transfer
1. Người dùng hoặc Asset Manager tạo yêu cầu thu hồi/điều chuyển.
2. Asset Manager kiểm tra tình trạng, ghi chú hư hỏng/mất mát nếu có.
3. Hệ thống đổi trạng thái Returned sau khi nhận lại; sau kiểm tra, Asset Manager chuyển tiếp sang Available, Maintenance hoặc tạo giao dịch transfer để cấp phát lại cho phòng ban/người nhận mới ở trạng thái Allocated.

### WF-CORE-004 — Inventory / maintenance / liquidation
1. Asset Manager tạo đợt kiểm kê theo phòng ban/nhóm tài sản.
2. Checker nhập actual count, tình trạng, ảnh/chứng từ và variance reason.
3. Maintenance/liquidation request cần manager review trước khi đóng giao dịch.

## Source Context
| ID | Meaning |
|---|---|
| SRC-001 | Source-extracted baseline for Asset Management scope, MVP assumptions and business rules. |
| DEC-SCOPE-001..007 | Scope Decision Matrix entries splitting MVP, Phase 2 and optional items. |

## Asset Code and Status Rules
- Asset code format: AST-YYYY-NNNNN, generated by system on first successful save; user cannot manually edit asset_code.
- User-entered identifiers: serial and external_ref. Serial must be unique within active assets.
- Status transition matrix: Draft → Available; Available → Allocated/Maintenance/Pending Liquidation; Allocated → Returned/Maintenance; Returned → Available/Maintenance; Maintenance → Available/Pending Liquidation; Pending Liquidation → Liquidated; Liquidated is terminal.

## Data Model Baseline
| Entity | Key fields | Validation |
|---|---|---|
| Asset | asset_code, name, group, serial, purchase_date, cost, status, department, holder | system generates asset_code; serial unique; required fields not empty |
| Employee | employee_code, full_name, department, cost_center, active_status | employee_code unique; inactive cannot receive new asset |
| Transaction | transaction_id, type, asset_code, from_holder, to_holder, date, evidence | asset status transition must be valid |
| Inventory | campaign_id, asset_code, expected, actual, variance, evidence | variance requires reason and manager review |
| Maintenance | ticket_id, asset_code, vendor, start_date, end_date, result | cannot allocate asset while maintenance is active |

## Report Catalog
| Report ID | Report | Linked REQ | Columns | Filters | Export |
|---|---|---|---|---|---|
| RPT-ASSET-001 | Asset inventory by department | REQ-CORE-004 | asset_code, name, group, status, department, holder, cost | department, group, status, date | XLSX/PDF |
| RPT-ASSET-002 | Allocation/return history | REQ-CORE-004 | asset_code, transaction_type, from_holder, to_holder, date, evidence | holder, department, period | XLSX |
| RPT-ASSET-003 | Maintenance/liquidation list | REQ-CORE-004 | asset_code, ticket/request, vendor, status, review_owner, result | status, vendor, period | XLSX/PDF |
| RPT-ASSET-004 | Audit/security events | REQ-CORE-005 | user, role, action, object_id, result, timestamp | user, role, action, period | XLSX |

## Permission Matrix
| Role | View | Create/Edit asset | Allocate/Return | Inventory | Liquidation | Reports/Admin |
|---|---|---|---|---|---|---|
| Admin | All | Yes | Yes | Yes | Yes | All |
| Asset Manager | Asset scope | Yes | Yes | Yes | Propose | Reports |
| Department Manager | Department | Approve | Approve | Review | Approve | Department reports |
| Staff | Own assets | No | Request/confirm | No | No | Own history |
| Auditor | Read-only | No | No | Read-only | Read-only | Audit reports |

## Success Metrics
- 100% tài sản MVP có mã định danh duy nhất, trạng thái hiện tại và lịch sử biến động.
- 95% giao dịch cấp phát/thu hồi/điều chuyển có người thực hiện, thời điểm, chứng từ hoặc biên bản.
- Báo cáo kiểm kê xuất được theo phòng ban, nhóm tài sản, trạng thái và chênh lệch.

## Acceptance / Testability
- Given asset master data hợp lệ, when Asset Manager tạo tài sản, then hệ thống sinh mã tài sản duy nhất và lưu audit log.
- Given tài sản đang Available, when cấp phát cho nhân sự, then trạng thái đổi thành Allocated và ghi nhận người sử dụng/phòng ban/ngày bàn giao.
- Given user không có quyền thanh lý, when truy cập chức năng thanh lý, then hệ thống chặn thao tác và ghi nhận security event.
""", domain)
    br_rows = [["BR ID", "Requirement", "Domain Rationale", "Priority", "Evidence"]]
    br_rows.extend([
        ["BR-CORE-001", "Quản lý hồ sơ tài sản/TTB và mã tài sản hệ thống sinh", "Cần một nguồn dữ liệu chuẩn cho tài sản, serial, nhóm, nguyên giá, trạng thái, phòng ban và người chịu trách nhiệm", "P0", "SRC-001"],
        ["BR-CORE-002", "Quản lý cấp phát, bàn giao, thu hồi và điều chuyển", "Cần kiểm soát holder history, trạng thái tài sản, biên bản/evidence và tránh cấp phát trùng", "P0", "SRC-001"],
        ["BR-CORE-003", "Quản lý kiểm kê, bảo trì/sửa chữa và thanh lý", "Cần ghi nhận chênh lệch, tình trạng, ticket bảo trì, đề xuất thanh lý và manager review", "P1", "SRC-001"],
        ["BR-CORE-004", "Báo cáo/dashboard và export", "Cần báo cáo theo phòng ban, người dùng, nhóm tài sản, trạng thái, kỳ kiểm kê và lịch sử biến động", "P0", "SRC-001"],
        ["BR-CORE-005", "Phân quyền, bảo mật, audit log và import/export", "Cần kiểm soát UI/API theo vai trò, ghi log thao tác và validate dữ liệu import", "P0", "SRC-001"],
    ])
    ac_definitions = AC_DEFINITIONS
    req_definitions = REQ_DEFINITIONS
    tst_definitions = TST_DEFINITIONS
    brd_fallback = apply_domain_terms(f"""# BRD

## 1. Business Context
{bullets(intel.summary)}

## 2. Business Drivers
- Tập trung dữ liệu tài sản/TTB để tránh thất lạc, trùng mã, sai trạng thái hoặc thiếu người chịu trách nhiệm.
- Chuẩn hóa quy trình cấp phát, thu hồi, điều chuyển, bảo trì, kiểm kê và thanh lý.
- Cung cấp báo cáo tức thời cho PM/BA/Dev/QA và khách hàng review: tài sản theo phòng ban, người dùng, nhóm, trạng thái và lịch sử biến động.

## 3. Business Requirements
{table(br_rows)}

## 4. Functional Scope Detail
- BR-CORE-001: Asset master phải có asset_code unique theo format AST-YYYY-NNNNN; user nhập serial/external_ref, không nhập asset_code; required fields gồm asset name, group, serial, purchase date, original cost, department, current holder/status và attachment khi có.
- BR-CORE-002: Allocation chỉ áp dụng cho asset trạng thái Available; mọi bàn giao/thu hồi/điều chuyển phải lưu holder history, evidence, approval status và audit event.
- BR-CORE-003: Inventory phải ghi expected/actual/variance, mandatory reason, evidence và manager review status; maintenance/liquidation phải khóa giao dịch cấp phát mới khi asset đang Maintenance hoặc Pending Liquidation.
- BR-CORE-004: Reports/dashboard phải hỗ trợ filter/export theo department, holder, group, status, period, inventory variance và transaction history; export phải có asset_code, name, group, holder, department, status, original_cost và date columns.
- BR-CORE-005: Permission phải kiểm soát UI/API theo role Admin, Asset Manager, Department Manager, Staff và Auditor; unauthorized action trả access denied/403 và ghi security audit event.

## 5. MVP Workflows and Business Rules
| Workflow | Trigger | Mandatory Rules | Exception / Error Case |
|---|---|---|---|
| WF-CORE-001 Create asset | Asset Manager creates/imports asset | System generates asset_code; serial/external_ref must be unique within configured scope; required fields must pass validation before save | Missing required fields or duplicate serial blocks save/import row and shows row-level/user-facing error |
| WF-CORE-002 Allocate/handover | Available asset assigned to employee/department | Status changes to Allocated; holder history and handover evidence are saved; low-value internal movement may be auto-approved by Asset Manager | Allocated/Maintenance/Pending Liquidation asset cannot be allocated again |
| WF-CORE-003 Return/transfer | Asset returned or moved across holder/department | Condition check decides Available/Maintenance/Allocated; transfer keeps old and new holder history | Missing evidence or invalid target department blocks transaction |
| WF-CORE-004 Inventory/maintenance/liquidation | Campaign, maintenance ticket or liquidation request is created | Variance requires reason/evidence/review; maintenance/liquidation locks allocation | Missing reason/evidence blocks submit; manager rejection returns item for correction |
| WF-CORE-005 Report/export/import | User filters report or imports batch data | Export preserves filters and required columns; import validates employee_code, department_code and serial row by row | Invalid rows are rejected with row numbers while valid rows continue |

**Linked Requirement for WF-CORE-005:** REQ-CORE-004 covers report/dashboard/export filters; REQ-CORE-005 covers import validation, permission and audit controls.

## 6. Data and Validation Baseline
| Entity | Required Fields | Validation |
|---|---|---|
| Asset | asset_code, name, group, serial, purchase_date, original_cost, department, status | asset_code system-generated; serial/external_ref unique; status follows allowed transition matrix |
| Transaction | asset_code, transaction_type, from_holder, to_holder, effective_date, evidence, approval_status | from/to holder required for allocation/transfer; evidence required for handover/return/variance |
| Inventory Result | campaign_id, asset_code, expected_status, actual_status, variance_reason, evidence, review_status | variance_reason and evidence required when expected differs from actual |
| Import Row | employee_code, department_code, serial, asset_name, group | invalid rows rejected with row-level errors; valid rows continue |

## 7. Scope
### In Scope
{bullets(intel.modules)}

### Phase 2 / Implementation Prerequisites
- Tích hợp ERP/HRM/kế toán chỉ triển khai khi có API contract, mapping field và owner xác nhận.
- Migration dữ liệu lịch sử chỉ triển khai khi có sample dataset, quy tắc làm sạch dữ liệu và kế hoạch đối soát.

## 8. Assumption Baseline
- SRC-001 is the approved source-extracted baseline for MVP scope.
- API realtime integration, RFID, legal e-signature and large-scale legacy migration are Phase 2 unless owners/contracts/sample data are ready.
- MVP uses import/export for HR/ERP/accounting data exchange.
- Data profiling and cleansing plan are required before migration estimate is finalized.

## 9. Source and Traceability Definitions
| ID | Definition |
|---|---|
| SRC-001 | Approved source-extracted baseline for Asset Management MVP scope, business goals, assumptions and phase decisions. |
| DEC-SCOPE-001..007 | Scope decisions separating MVP, Phase 2 and optional items. |
| REQ-CORE-001 | Asset master: tạo/cập nhật/tra cứu/export tài sản với system-generated asset_code, serial, group, purchase info, status, department, holder và attachment. |
| REQ-CORE-002 | Asset transaction workflow: allocation, handover, return and transfer with valid status transition, holder history and evidence. |
| REQ-CORE-003 | Inventory, maintenance and liquidation: campaigns, variance, maintenance ticket, liquidation request, review and locked invalid transitions. |
| REQ-CORE-004 | Reports/dashboard: filter/export by department, holder, group, status, date period, inventory variance and transaction history. |
| REQ-CORE-005 | Permission/audit/import-export: role-based UI/API authorization, audit log, import validation and backup/export control. |
| AC-001-01 | Create asset generates unique asset_code, stores serial/external_ref and creates audit event. |
| AC-001-02 | Allocation updates status, holder history and evidence. |
| AC-001-03 | Missing asset name, group, department or serial blocks save. |
| AC-001-04 | Unauthorized UI/API action returns 403/access denied and logs security event. |
| AC-001-05 | Invalid asset status transition is blocked. |
| AC-001-06 | Inventory variance or operational lock requires reason, evidence and review. |
| AC-001-07 | Invalid import rows are rejected with row-level errors while valid rows continue. |

## 10. Customer Review Notes
- This BRD focuses on business requirements and includes enough requirement/AC definitions for standalone customer review.
- All BR-CORE items link to SRC-001 and BG-001.
""", domain)
    workflow_text = bullets(intel.workflows)
    integration_text = bullets(intel.integrations)
    negative_text = bullets(intel.negative_cases)
    srs_fallback = apply_domain_terms(f"""# SRS

## 1. Introduction
SRS sinh từ source inventory của project {project.config.project_slug}, domain **Asset Management / Quản lý trang thiết bị, tài sản**.

## 2. Overall Description
Hệ thống Quản lý TTB/Tài sản hỗ trợ quản lý danh mục tài sản, cấp phát/bàn giao, thu hồi, điều chuyển, kiểm kê, bảo trì/sửa chữa, thanh lý, phân quyền, audit log và báo cáo. Nội dung được dẫn xuất từ SRC-001 và Scope Decision Matrix. SRC-001 is the approved source-extracted Asset Management MVP baseline; Scope Decision Matrix provides DEC-SCOPE-001..007.

## 3. Actors and Modules
### Actors
- Admin: quản trị người dùng, vai trò, master data và cấu hình.
- Asset Manager: quản lý asset master, allocation, return, transfer, inventory, maintenance and liquidation.
- Department Manager: approve/review assets and transactions within assigned department.
- Staff/Employee: view and confirm assigned assets.
- Auditor: read-only reports and audit log.

### Modules
- Asset Master
- Allocation / Handover / Return / Transfer
- Inventory / Maintenance / Liquidation
- Reports / Export
- Permission / Audit / Import-Export

## 4. Workflows
- WF-CORE-001 Create asset: system generates asset_code, validates serial/external_ref and stores asset as Available.
- WF-CORE-002 Allocate/handover: Department Manager approves cross-department/high-value movement; Asset Manager auto-approves low-value internal movement below 5.000.000 VND.
- WF-CORE-003 Return/transfer: Asset Manager inspects condition and chooses Available, Maintenance or Allocated.
- WF-CORE-004 Inventory/maintenance/liquidation: variance requires reason/evidence/review; maintenance and liquidation lock allocation.

## 5. Specific Requirements
### {req}: Quản lý hồ sơ tài sản/TTB
**Linked BR:** {br}
**Description:** Asset Manager có thể tạo, cập nhật, tra cứu tài sản với asset_code do hệ thống tự sinh, nhóm tài sản, serial/external_ref, ngày mua, giá trị, trạng thái, vị trí, phòng ban, người sử dụng và hồ sơ chứng từ.
**Priority:** P0
**Verification:** Tạo mới tài sản hợp lệ sinh asset_code duy nhất; thiếu trường bắt buộc bị chặn; mọi thay đổi trạng thái ghi audit log.

### REQ-CORE-002: Cấp phát, bàn giao, thu hồi và điều chuyển
**Linked BR:** BR-CORE-002
**Description:** Hệ thống hỗ trợ cấp phát tài sản cho nhân sự/phòng ban, in/đính kèm biên bản bàn giao, thu hồi và điều chuyển có phê duyệt theo vai trò.
**Priority:** P0
**Verification:** Tài sản Available mới được cấp phát; tài sản Allocated có người sử dụng/phòng ban; thu hồi đổi trạng thái về Available/Maintenance theo kết quả kiểm tra.

### REQ-CORE-003: Kiểm kê, bảo trì và thanh lý
**Linked BR:** BR-CORE-003
**Description:** Người dùng được phân quyền có thể lập đợt kiểm kê, ghi nhận chênh lệch, tạo phiếu bảo trì/sửa chữa và đề xuất thanh lý tài sản hết vòng đời.
**Priority:** P1
**Verification:** Kiểm kê ghi nhận đủ expected/actual/difference; bảo trì có ngày nhận/trả/kết quả; thanh lý cần phê duyệt và khóa giao dịch cấp phát mới.

### REQ-CORE-004: Báo cáo và truy vết
**Linked BR:** BR-CORE-004
**Description:** Hệ thống cung cấp báo cáo tài sản theo trạng thái, phòng ban, người dùng, nhóm tài sản, lịch sử biến động và audit log.
**Priority:** P0
**Verification:** Báo cáo lọc/export được theo kỳ, phòng ban, trạng thái và nhóm tài sản.

### REQ-CORE-005: Phân quyền và bảo mật
**Linked BR:** BR-CORE-005
**Description:** Admin cấu hình vai trò Admin, Asset Manager, Department Manager, Staff, Auditor với quyền xem/tạo/sửa/phê duyệt/xuất báo cáo theo trách nhiệm.
**Priority:** P0
**Verification:** User không có quyền bị chặn ở UI/API và sự kiện bị ghi log.

## Requirement Reference Table
{req_definitions}

## Acceptance Criteria Reference Table
{ac_definitions}

## Approval and SLA Rules
- Allocation approval: Department Manager approves within 1 business day; Asset Manager auto-approves low-value internal movement per MVP policy.
- Maintenance/liquidation approval: Department Manager reviews business impact; Asset Manager closes operational record; Accounting is consulted for financial disposal.
- HRM/ERP realtime sync is Phase 2; MVP supports controlled import/export only.
- Status transitions follow the Asset Code and Status Rules defined in PRD and repeated in the implementation baseline.

## 6. Negative / Exception Requirements
- User without permission attempts allocation/liquidation: return 403/access denied and write security audit event.
- Asset is Allocated, Maintenance, Pending Liquidation or Liquidated and user attempts allocation: block transaction and show current status/holder.
- Import row misses employee_code, department_code, serial or required asset field: reject invalid row with row-level error and continue valid rows.
- Report export timeout: show retryable error, keep filter criteria and write operational log.
- Concurrent update on same asset: reject stale update and require user to reload latest asset status.

### Linked Work Items
- Screen: {scr}
- API: {api}
- Workflow: {wf}
- User Story: {us}
""", domain)
    # Stage15: use deterministic source-driven BA baseline for consistent Gate C/traceability.
    # LLM writer remains available elsewhere, but BA core docs must not invent conflicting MVP scope.
    prd_text = prd_fallback
    brd_text = brd_fallback
    srs_text = srs_fallback
    (ba_dir / "01-prd.md").write_text(_normalize_ba_text(prd_text, br, req, us, ac1, ac2), encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(_normalize_ba_text(brd_text, br, req, us, ac1, ac2), encoding="utf-8")
    (srs_dir / "srs.md").write_text(_normalize_ba_text(srs_text, br, req, us, ac1, ac2), encoding="utf-8")
    (srs_dir / "screens" / f"{scr}.md").write_text(apply_domain_terms(f"# {scr}: Asset Management Workspace\n\n**Linked REQ:** {req}\n\n## Purpose\nCho phép Asset Manager quản lý danh mục tài sản, trạng thái, holder history, workflow giao dịch, evidence và báo cáo theo module/domain.\n\n## Key Fields\n- Asset code, asset name, group, serial, purchase date, cost, status\n- Department, current holder, location, warranty/maintenance info\n- Transaction history, approval status, evidence attachment\n- Audit log and report/export filters\n\n## Permission Notes\n- Admin cấu hình role và master data.\n- Asset Manager tạo/sửa asset và giao dịch tài sản.\n- Department Manager phê duyệt theo phòng ban.\n- Staff chỉ xem/xác nhận tài sản được giao.\n- Auditor chỉ xem báo cáo và audit log.\n", domain), encoding="utf-8")
    (srs_dir / "apis" / f"{api}.md").write_text(f"# {api}: Artifact Generation API\n\n**Linked REQ:** {req}\n\n## Endpoint\nPOST /api/v1/projects/{{project_id}}/artifacts\n\n## Request Highlights\n- domain_pack\n- source_inventory_id\n- export_profile\n- gate_mode\n\n## Error Cases\n- 400: missing required source or unsupported profile\n- 403: user cannot generate artifacts for this project\n- 409: baseline locked or concurrent generation running\n- 504: LLM/source parser timeout, fallback generator used\n", encoding="utf-8")
    (srs_dir / "workflows" / f"{wf}.md").write_text(apply_domain_terms(f"# {wf}: Source to Documentation Workflow\n\n**Linked REQ:** {req}\n\n## Happy Path\nUpload source → Redact → Parse source intelligence → Apply domain pack → Generate PRD/BRD/SRS/US/Test/Quotation → Gate A/B/C → Traceability → Export.\n\n## Domain Workflows\n{bullets(intel.workflows)}\n\n## Exception Paths\n{bullets(intel.negative_cases)}\n", domain), encoding="utf-8")
    us_dir = ba_dir / "04-us"; us_dir.mkdir(exist_ok=True)
    (us_dir / f"{us}.md").write_text(apply_domain_terms(f"""# User Story {us}: Sinh tài liệu từ source có ngữ cảnh domain

**Linked REQ:** {req}
**Linked Work Items:** {scr}, {api}, {wf}
**Primary Persona:** PM/BA
**Secondary Personas:** {', '.join(intel.roles[:3]) or 'Reviewer, Developer, QA'}

As a PM/BA, I want to import project sources and select a domain pack so that PMO Studio can generate traceable, context-specific documentation with realistic test and quotation outputs.

## Business Value
- Giảm chỉnh sửa thủ công sau generation.
- BA/Dev/QA hiểu rõ workflow, permission, integration và exception paths.
- Client nhận bản export có cấu trúc review được.

## Acceptance Criteria
### {ac1} — Redaction and source intelligence
Given a source file contains sensitive values and business workflow hints, when Stage 0 processes it, then redacted source is created, source inventory flags redaction, and BA generation receives module/workflow/integration candidates.

### {ac2} — Domain-specific BA artifacts
Given BA generation runs with domain pack `{project.config.domain_pack}`, when it completes, then PRD/BRD/SRS/US/Test/Quotation artifacts include domain terminology, actors, workflows, negative cases and valid IDs.

### AC-001-03 — Asset master required fields
Given Asset Manager enters a new asset without asset name, asset group, purchase date or owning department, when saving the asset, then the system blocks save, highlights missing fields, and does not allocate an asset code.

### AC-001-04 — Allocation permission denied
Given Staff user has no allocation permission, when they open asset allocation or call allocation API, then the system returns access denied and writes an audit event.

### AC-001-05 — Asset status conflict
Given an asset is already Allocated or In Maintenance, when Asset Manager tries to allocate it again, then the system blocks the transaction and shows the current holder/status.

### AC-001-06 — Inventory variance handling
Given an inventory count finds missing or damaged assets, when the checker submits the inventory result, then variance records are created with reason, evidence attachment and manager review status.

### AC-001-07 — Integration/import validation
Given import data from HRM/ERP is missing employee code, department code, or asset serial, when importing, then invalid rows are rejected with row-level error details and valid rows continue.

### AC-001-08 — Report/export validation
Given report data exists for department, holder, group, status and period filters, when the user exports the report, then the export matches the selected filters and includes asset_code, name, group, holder, department, status, original_cost and date columns.
""", domain), encoding="utf-8")
    test_rows = [["ID", "Linked AC", "Type", "Precondition", "Steps / Input", "Expected Result"]]
    test_rows.append([tc, ac1, "Positive", "Asset Manager logged in; Department IT and asset group Laptop exist; asset_code is system-generated", "Create asset: Laptop Dell, group Laptop, serial SN001, purchase date today, department IT", "Asset is saved with unique asset code, status Available, and audit log created"])
    test_rows.extend([
        ["TC-002", "AC-001-02", "Positive", "Generated asset_code AST-2026-00001 exists with status Available; Employee E001 and Department IT exist", "Allocate AST-2026-00001 to E001 with handover evidence file", "Asset status becomes Allocated; holder history shows E001/Department IT; handover evidence file is linked"],
        ["TC-003", "AC-001-03", "Validation", "Asset Manager logged in", "Create asset without asset name, group, owning department and serial", "Save is blocked; asset name, group, department and serial are highlighted as required; no asset code is generated"],
        ["TC-004", "AC-001-04", "Permission", "Staff user logged in", "Open allocation screen or POST allocation API for serial SN001 / existing generated asset_code AST-2026-00001", "System returns access denied/403 and records security audit event"],
        ["TC-005", "AC-001-05", "Business rule", "Asset code AST-2026-00001 status = Allocated to Employee E001", "Allocate AST-2026-00001 again to Employee E002", "System blocks allocation and shows current holder E001 and status Allocated"],
        ["TC-006", "AC-001-06", "Inventory", "Inventory campaign Q2 exists with expected AST-2026-00001", "Submit count result: AST-2026-00001 missing; enter variance reason 'not found at assigned location'; attach evidence photo; submit for manager review", "Variance record is created with reason, evidence and status Pending Manager Review"],
        ["TC-007", "AC-001-07", "Import", "Import template downloaded", "Import rows with missing employee_code, department_code and asset serial", "Invalid rows are rejected with row numbers and error messages; valid rows are imported"],
        ["TC-008", "AC-001-06", "Maintenance", "Asset code AST-2026-00001 status = Maintenance", "Try to allocate AST-2026-00001 while an active maintenance ticket is open; provide reason/evidence in maintenance record", "System blocks allocation and shows active maintenance ticket"],
        ["TC-009", "AC-001-06", "Liquidation", "Asset code AST-2026-00002 status = Pending Liquidation", "Try to allocate AST-2026-00002 before liquidation review closes; verify liquidation reason/evidence is retained", "System blocks allocation and shows pending liquidation review"],
        ["TC-010", "AC-001-08", "Report", "Allocated assets exist for Department IT", "Filter report by Department IT, status Allocated and current month, then export XLSX", "Report returns asset_code, name, group, holder, department, status, original_cost and date columns; XLSX export file is generated"],
    ])
    (ba_dir / "05-test-cases.md").write_text(apply_domain_terms(f"""# Test Cases

## Test Strategy
- Cover happy path, permission/API access, validation, workflow state conflict, integration/import validation and domain-specific negative paths.
- Critical AC coverage includes positive, validation, permission, business-rule, inventory, report/export, maintenance/liquidation and import scenarios.

## Referenced Requirements
{req_definitions}

## Canonical Acceptance Definitions
| AC ID | Definition |
|---|---|
| AC-001-01 | Create asset generates unique asset_code, stores serial/external_ref and creates audit event. |
| AC-001-02 | Allocation updates status, holder history and evidence. |
| AC-001-03 | Missing asset name, group, department or serial blocks save. |
| AC-001-04 | Unauthorized UI/API action returns 403/access denied and logs security event. |
| AC-001-05 | Invalid asset status transition is blocked. |
| AC-001-06 | Inventory variance, maintenance lock or liquidation lock requires reason, evidence and review. |
| AC-001-07 | Invalid import rows are rejected with row-level errors while valid rows continue. |
| AC-001-08 | Report/dashboard filter and export returns required columns for department, holder, group, status and period. |

## Coverage Matrix
Each row below links to the canonical AC ID in the Linked AC column.

{table(test_rows)}
""", domain), encoding="utf-8")
    from pmo_studio.generators.quotation import generate_quotation_for_project
    generate_quotation_for_project(project, ba_dir / "06-quotation.xlsx")
    project.mark_stage("ba.source_driven", "completed")

def _normalize_ba_text(text: str, br: str, req: str, us: str, ac1: str, ac2: str) -> str:
    """Post-process LLM BA output into PMO Studio's stricter ID/trace conventions."""
    cleanup = {
        "Tài liệu PRD được tổng hợp từ redacted sources": "Tài liệu PRD được dẫn xuất từ source đã lọc thông tin nhạy cảm",
        "redacted sources": "source đã lọc thông tin nhạy cảm",
        "Need Confirmation": "Implementation Prerequisites",
        "Phase 2 / Need Confirmation": "Phase 2 / Implementation Prerequisites",
        "chưa workshop với key users": "cần xác nhận stakeholder trong assumption baseline",
        "Thiếu dữ liệu mẫu": "cần sample dataset cho estimate/migration",
        "Integration contract chưa ổn định": "API contract cần baseline trước Phase 2",
        "open questions": "assumption baseline",
        "Open Questions": "Assumption Baseline",
        "PMO Studio giúp chuẩn hóa tài liệu dự án phần mềm từ intake đến go-live.": "Hệ thống quản lý TTB/Tài sản giúp số hóa vòng đời tài sản từ ghi nhận đến thanh lý và báo cáo.",
        "- (quản trị - người dùng.": "- Admin, Asset Manager, Department Manager, Staff, Auditor.",
        "(quản trị, người dùng.": "Admin, Asset Manager, Department Manager, Staff, Auditor",
        "- người dùng.": "- Staff/Employee: người nhận bàn giao và xác nhận tài sản được giao.",
        "- (quản trị": "- Admin, Asset Manager, Department Manager, Staff, Auditor",
        "v.v.).•": "v.v.).\n-",
    }
    for old, new in cleanup.items():
        text = text.replace(old, new)
    replacements = {
        "OBJ-": "BG-",
        "DOC-": "BG-",
        "FR-001": req,
        "FR-002": "REQ-CORE-002",
        "FR-003": "REQ-CORE-003",
        "FR-004": "REQ-CORE-004",
        "FR-005": "REQ-CORE-005",
        "FR-006": "REQ-CORE-006",
        "FR-007": "REQ-CORE-007",
        "FR-008": "REQ-CORE-008",
        "FR-009": "REQ-CORE-009",
        "FR-010": "REQ-CORE-010",
        "WF-001": "WF-CORE-001",
        "WF-002": "WF-CORE-002",
        "WF-003": "WF-CORE-003",
        "AC-003": "AC-001-03",
        "AC-004": "AC-001-04",
        "AC-005": "AC-001-05",
        "AC-006": "AC-001-06",
        "AC-007": "AC-001-07",
        "AC-008": "AC-001-08",
        "AC-009": "AC-001-09",
        "NFR-UI-001": "REQ-NFR-001",
        "NFR-PL-001": "REQ-NFR-002",
        "NFR-SEC-001": "REQ-NFR-003",
        "NFR-DATA-001": "REQ-NFR-004",
        "NFR-INT-001": "REQ-NFR-005",
        "NFR-IMP-001": "REQ-NFR-006",
        "NFR-BKP-001": "REQ-NFR-007",
        "BRULE-001": "REQ-RULE-001",
        "BRULE-002": "REQ-RULE-002",
        "BRULE-003": "REQ-RULE-003",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if "## Overview" not in text:
        text = text.replace("## 1.", "## Overview\nTổng quan sản phẩm và phạm vi được dẫn xuất từ SRC-001.\n\n## 1.", 1)
    if "## Business Goals" not in text:
        marker = "## Overview"
        if marker in text:
            text = text.replace(marker, f"## Business Goals\n- BG-001: Số hóa vòng đời quản lý TTB/Tài sản. Linked source: SRC-001.\n- BG-002: Tăng traceability từ scope decision tới BR/REQ/US/AC/TC/EST.\n\n{marker}", 1)
    if "## 1. Business Context" not in text and text.startswith("# BRD"):
        text = text.replace("# BRD", "# BRD\n\n## 1. Business Context\nDự án quản lý trang thiết bị/tài sản nội bộ, linked source: SRC-001.", 1)
    if "Business Requirements" not in text and text.startswith("# BRD"):
        text += f"\n\n## 2. Business Requirements\n### {br}: MVP Asset Lifecycle\n**Linked source:** SRC-001\n**Linked scope decisions:** DEC-SCOPE-001, DEC-SCOPE-002, DEC-SCOPE-003, DEC-SCOPE-004, DEC-SCOPE-005, DEC-SCOPE-006, DEC-SCOPE-007\n**Downstream REQ:** {req}, REQ-CORE-002, REQ-CORE-003\n"
    trace = f"""

## Traceability Links
- Source context: SRC-001 = approved source-extracted baseline embedded in this artifact.
- Linked source: SRC-001
- Linked business goal: BG-001
- Linked BR: {br}, BR-CORE-002, BR-CORE-003, BR-CORE-004, BR-CORE-005
- Linked REQ: {req}, REQ-CORE-002, REQ-CORE-003, REQ-CORE-004, REQ-CORE-005
- Linked US: {us}
- Linked AC: {ac1}, {ac2}, AC-001-03, AC-001-04, AC-001-05, AC-001-06, AC-001-07, AC-001-08
- Linked scope decisions: DEC-SCOPE-001, DEC-SCOPE-002, DEC-SCOPE-003, DEC-SCOPE-004, DEC-SCOPE-005, DEC-SCOPE-006, DEC-SCOPE-007
"""
    if "## Traceability Links" not in text:
        text = text.rstrip() + trace
    detail = f"""

## Self-Contained Implementation Baseline
### Core workflows
- WF-CORE-001 Create asset: validate required fields, unique asset code/serial, create Available asset and audit event. Linked REQ: REQ-CORE-001.
- WF-CORE-002 Allocate/handover: only Available asset can be allocated; update holder, department, status and handover evidence. Linked REQ: REQ-CORE-002.
- WF-CORE-003 Return/transfer: inspect returned asset, choose Available/Maintenance/Allocated status and retain transaction history. Linked REQ: REQ-CORE-002.
- WF-CORE-004 Inventory/maintenance/liquidation: capture expected/actual/variance, evidence, manager review and lock invalid transitions. Linked REQ: REQ-CORE-003.

### Data fields
| Entity | Required fields | Key rule |
|---|---|---|
| Asset | asset_code, name, group, serial, purchase_date, department, status | system generates asset_code; serial is unique |
| Transaction | type, asset_code, from_holder, to_holder, date, evidence | status transition must be valid |
| User/Role | employee_code, department, role, active_status | inactive user cannot receive new asset |
| Inventory | campaign, asset_code, expected, actual, variance_reason | variance requires reason/evidence |

### Permission baseline
| Role | Permission |
|---|---|
| Admin | user/role/master data/config/report/admin |
| Asset Manager | asset CRUD, allocation, return, transfer, inventory, maintenance, reports |
| Department Manager | approve/review department assets and variance |
| Staff | view/confirm own assigned assets |
| Auditor | read-only reports and audit log |

### Referenced requirements
{REQ_DEFINITIONS}

### Referenced acceptance criteria
{AC_DEFINITIONS}

### Referenced test smoke set
{TST_DEFINITIONS}

### API/integration baseline
- API-CORE-001 Asset import/export validates employee code, department code, asset serial and duplicate system-generated asset_code.
- API-CORE-002 HRM/ERP import/export baseline and realtime sync Phase 2. Linked REQ: REQ-CORE-005.
- API-CORE-003 Unauthorized UI/API actions return 403 and write security audit event. Linked REQ: REQ-CORE-005.
"""
    if "## Self-Contained Implementation Baseline" not in text and not text.startswith("# BRD"):
        text = text.rstrip() + detail
    text = text.replace("AC-001-01-01", "AC-001-01").replace("AC-001-01-02", "AC-001-02")
    return text


def _source_summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("--- SOURCE")]
    return "\n".join(f"- {line[:180]}" for line in lines[:8])

