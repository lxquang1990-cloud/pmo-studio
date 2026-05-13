"""Source-driven BA generation with optional LLM writer."""
from __future__ import annotations

from pathlib import Path
from openpyxl import Workbook

from pmo_studio.core.ids import IdAllocator
from pmo_studio.core.project import Project
from pmo_studio.llm.provider import LLMClient, NoopLLMClient
from pmo_studio.llm.writer import ArtifactWriter
from pmo_studio.domain.prompts import get_domain, inject_domain_prompt
from pmo_studio.generators.intelligence import apply_domain_terms, build_intelligence, bullets, table


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


def generate_ba_from_sources(project: Project, llm: LLMClient | None = None) -> None:
    llm = llm or NoopLLMClient()
    source_text = read_redacted_sources(project)
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

    prd_fallback = apply_domain_terms(f"""# PRD: {project.config.project_slug}

## Overview
Tài liệu PRD được tổng hợp từ redacted sources cho domain **{domain.label}**.

## Source Intelligence Summary
{bullets(intel.summary)}

## Personas / Stakeholders
{bullets(intel.roles)}

## Product Modules
{bullets(intel.modules)}

## Business Goals
- BG-001: Chuẩn hóa và tự động hóa vòng đời tài liệu dự án.
- BG-002: Giảm effort chỉnh sửa thủ công bằng artifact có ngữ cảnh domain, workflow và traceability rõ ràng.
- BG-003: Tạo baseline đủ dùng cho PM/BA/Dev/QA estimate, review và triển khai.

## Success Metrics
- 90%+ artifact có upstream/downstream ID rõ ràng.
- Gate B/C ghi evidence cụ thể thay vì chỉ PASS/FAIL.
- Client-ready export có mục lục, phạm vi và traceability index.
""", domain)
    br_rows = [["BR ID", "Requirement", "Domain Rationale", "Priority", "Evidence"]]
    br_rows.append([br, "Quản lý yêu cầu và tài liệu dự án theo traceability", "Cần biến source đầu vào thành PRD/BRD/SRS/US/Quotation có kiểm soát", "P0", "SRC-001"])
    for idx, wf_item in enumerate(intel.workflows[:3], start=2):
        br_rows.append([f"BR-CORE-{idx:03d}", f"Hỗ trợ workflow: {wf_item[:90]}", "Workflow nghiệp vụ cần được phản ánh vào SRS/US/AC", "P0" if idx == 2 else "P1", "SRC-001 / Domain-source intelligence"])
    brd_fallback = apply_domain_terms(f"""# BRD

## 1. Business Context
{bullets(intel.summary)}

## 2. Business Drivers
- Chuẩn hóa cách chuyển đổi source/raw notes thành bộ tài liệu PMO có thể review.
- Giảm output generic bằng domain terminology, workflow và negative cases.
- Tăng khả năng reuse cho BA/PM/Dev/QA thông qua traceability và quality gates.

## 2. Business Requirements
{table(br_rows)}

## 4. Scope
### In Scope
{bullets(intel.modules)}

### Out of Scope / Need Confirmation
- Custom integration chưa có API contract rõ ràng.
- Migration dữ liệu lịch sử nếu chưa có sample dataset.

## 5. Risks & Assumptions
{bullets(intel.risks)}
""", domain)
    workflow_text = bullets(intel.workflows)
    integration_text = bullets(intel.integrations)
    negative_text = bullets(intel.negative_cases)
    srs_fallback = apply_domain_terms(f"""# SRS

## 1. Introduction
SRS sinh từ source inventory của project {project.config.project_slug}, domain **{domain.label}**.

## 2. Overall Description
Hệ thống hỗ trợ intake, generate artifacts, quality gate, traceability, baseline và export. Nội dung fallback được enrich bằng source intelligence, terminology và workflow đặc thù domain.

## 3. Actors and Modules
### Actors
{bullets(intel.roles)}

### Modules
{bullets(intel.modules)}

## 4. Workflows
{workflow_text}

## 3. Specific Requirements
### {req}: Sinh tài liệu từ source đã redacted
**Linked BR:** {br}
**Description:** Người dùng có thể import source, hệ thống redact secret và sinh PRD/BRD/SRS/US/Quotation có domain context, traceability và evidence quality gate.
**Priority:** P0
**Verification:** Artifact có ID hợp lệ, Gate A/B pass, traceability cập nhật, export bundle có index.

### REQ-CORE-002: Áp dụng domain terminology và workflow
**Linked BR:** {br}
**Description:** Generator phải map thuật ngữ và workflow phổ biến của domain vào BRD/SRS/US/AC thay vì chỉ dùng placeholder generic.
**Priority:** P0
**Verification:** Output có module, role, workflow và negative cases thuộc domain.

### REQ-CORE-003: Hỗ trợ integration awareness
**Linked BR:** {br}
**Description:** Khi source/domain có integration points, tài liệu phải ghi nhận dependency, rủi ro và test scenario tương ứng.
**Priority:** P1
**Integration Points:** {', '.join(intel.integrations[:6]) or 'Cần xác nhận trong workshop integration'}
**Verification:** Test cases có scenario timeout/error/permission.

## 6. Negative / Exception Requirements
{negative_text}

### Linked Work Items
- Screen: {scr}
- API: {api}
- Workflow: {wf}
- User Story: {us}
""", domain)
    (ba_dir / "01-prd.md").write_text(writer.write_markdown(artifact_type="PRD", source_text=source_text, instructions=inject_domain_prompt("PRD", project.config.domain_pack, "Write a concise Vietnamese PRD. Include BG-001."), fallback=prd_fallback), encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(writer.write_markdown(artifact_type="BRD", source_text=source_text, instructions=inject_domain_prompt("BRD", project.config.domain_pack, f"Write Vietnamese BRD. Must include requirement ID {br} and Linked source SRC-001."), fallback=brd_fallback), encoding="utf-8")
    (srs_dir / "srs.md").write_text(writer.write_markdown(artifact_type="SRS", source_text=source_text, instructions=inject_domain_prompt("SRS", project.config.domain_pack, f"Write Vietnamese SRS with sections '# SRS', '## 1. Introduction', '## 2. Overall Description', '## 3. Specific Requirements'. Must include {req}, linked to {br}, and mention {scr}, {api}, {wf}, {us}."), fallback=srs_fallback), encoding="utf-8")
    (srs_dir / "screens" / f"{scr}.md").write_text(apply_domain_terms(f"# {scr}: Màn hình quản lý tài liệu\n\n**Linked REQ:** {req}\n\n## Purpose\nCho phép xem trạng thái artifact, gate, baseline và traceability theo module/domain.\n\n## Key Fields\n- Project / module / workflow\n- Artifact status và owner\n- Gate B/C evidence summary\n- Risk và open questions\n\n## Permission Notes\n- PM/BA được cập nhật artifact.\n- Reviewer được comment/approve.\n- Viewer chỉ được xem client-ready export.\n", domain), encoding="utf-8")
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

### AC-NEG-01 — Permission denied
Given a user does not have permission for the project, when they call artifact generation, then the system returns 403 and does not create or overwrite artifacts.

### AC-NEG-02 — Integration timeout
Given an external integration or LLM writer times out, when generation continues, then the fallback deterministic generator produces artifacts and records the limitation as a risk/open question.

### AC-NEG-03 — Incomplete source
Given source data is missing workflow or integration details, when artifacts are generated, then assumptions and workshop questions are explicitly listed instead of inventing unsupported details.
""", domain), encoding="utf-8")
    test_rows = [["ID", "Linked AC", "Type", "Scenario", "Expected Result"]]
    test_rows.append([tc, ac1, "Positive", "Source has API key and workflow text", "Secret is masked; workflow/module candidates are captured"])
    for idx, case in enumerate(intel.negative_cases[:5], start=2):
        linked_ac = ac2 if idx % 2 == 0 else ac1
        test_rows.append(["TC scenario", linked_ac, "Negative", case, "System blocks unsafe action, shows clear error/evidence, and preserves traceability"])
    (ba_dir / "05-test-cases.md").write_text(apply_domain_terms(f"""# Test Cases

## Test Strategy
- Cover happy path, permission, validation, integration timeout and domain-specific negative paths.
- Every critical AC must have at least one positive and one negative scenario.

{table(test_rows)}
""", domain), encoding="utf-8")
    _write_quotation(ba_dir / "06-quotation.xlsx", project, [(est_scr, "Screen", scr, 2.75 * intel.complexity_multiplier), (est_api, "API", api, 2.30 * intel.complexity_multiplier)], multiplier=intel.complexity_multiplier, risks=intel.risks)
    project.mark_stage("ba.source_driven", "completed")


def _source_summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("--- SOURCE")]
    return "\n".join(f"- {line[:180]}" for line in lines[:8])


def _write_quotation(path: Path, project: Project, rows: list[tuple[str, str, str, float]], multiplier: float = 1.0, risks: list[str] | None = None) -> None:
    wb = Workbook(); ws = wb.active; ws.title = "Summary"
    detail = wb.create_sheet("Estimate Detail")
    detail.append(["EST ID", "Module", "Function", "Work Item Type", "Work Item ID", "Complexity", "Rationale", "BA md", "UX md", "FE md", "BE md", "DB md", "QA md", "Total md", "Risk Factor", "Cost VND"])
    detail_total = 0.0
    detail_cost = 0.0
    detail_rows = []
    for est, typ, wid, md in rows:
        md_rounded = round(md, 2)
        cost = round(md_rounded * project.config.manday_rate_vnd, 0)
        detail_total += md_rounded
        detail_cost += cost
        detail_rows.append([est, "Core", "Source/domain-aware generation", typ, wid, "medium" if multiplier < 1.3 else "high", "Includes source intelligence, domain terminology, negative cases and export profile needs", round(0.35 * multiplier, 2), round((0.5 if typ == "Screen" else 0) * multiplier, 2), round((1.0 if typ == "Screen" else 0) * multiplier, 2), round((0.5 if typ == "Screen" else 1.5) * multiplier, 2), round((0.2 if typ == "API" else 0) * multiplier, 2), round(0.6 * multiplier, 2), md_rounded, multiplier, cost])
    total = round(detail_total, 2)
    ws.append(["Metric", "Value"])
    ws.append(["Manday Rate", project.config.manday_rate_vnd])
    ws.append(["Complexity multiplier", multiplier])
    ws.append(["Total manday", total])
    ws.append(["Total cost VND", detail_cost])
    for row in detail_rows:
        detail.append(row)
    risk_ws = wb.create_sheet("Risks & Assumptions")
    risk_ws.append(["Type", "Description", "Impact"])
    for risk in risks or []:
        risk_ws.append(["Risk", risk, "May increase analysis/dev/test effort if not clarified early"])
    if not risks:
        risk_ws.append(["Assumption", "Source sample is representative", "Estimate may change after workshop"])
    wb.save(path)
