"""Source-driven BA generation with optional LLM writer."""
from __future__ import annotations

from pathlib import Path
from openpyxl import Workbook

from pmo_studio.core.ids import IdAllocator
from pmo_studio.core.project import Project
from pmo_studio.llm.provider import LLMClient, NoopLLMClient
from pmo_studio.llm.writer import ArtifactWriter
from pmo_studio.domain.prompts import inject_domain_prompt


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
    ba_dir = project.root / "artifacts" / "ba"
    ba_dir.mkdir(parents=True, exist_ok=True)
    srs_dir = ba_dir / "03-srs"
    for sub in ["functional-spec", "screens", "apis", "workflows", "reports"]:
        (srs_dir / sub).mkdir(parents=True, exist_ok=True)

    prd_fallback = f"""# PRD: {project.config.project_slug}

## Overview
Tài liệu PRD được tổng hợp từ redacted sources.

## Source Summary
{_source_summary(source_text)}

## Business Goals
- BG-001: Chuẩn hóa và tự động hóa vòng đời tài liệu dự án.
"""
    brd_fallback = f"""# BRD

## 1. Business Context
{_source_summary(source_text) or 'Khách hàng cần hệ thống quản lý tài liệu dự án phần mềm.'}

## 2. Business Requirements
### {br}: Quản lý yêu cầu và tài liệu dự án
**Linked source:** SRC-001
**Description:** Hệ thống phải chuyển nguồn đầu vào thành tài liệu có kiểm soát, traceability và báo giá.
**Priority:** P0
"""
    srs_fallback = f"""# SRS

## 1. Introduction
SRS sinh từ source inventory của project {project.config.project_slug}.

## 2. Overall Description
Hệ thống hỗ trợ intake, generate artifacts, quality gate, traceability, baseline và export.

## 3. Specific Requirements
### {req}: Sinh tài liệu từ source đã redacted
**Linked BR:** {br}
**Description:** Người dùng có thể import source, hệ thống redact secret và sinh PRD/BRD/SRS/US/Quotation.
**Verification:** Artifact có ID hợp lệ, Gate A/B pass, traceability cập nhật.

### Linked Work Items
- Screen: {scr}
- API: {api}
- Workflow: {wf}
- User Story: {us}
"""
    (ba_dir / "01-prd.md").write_text(writer.write_markdown(artifact_type="PRD", source_text=source_text, instructions=inject_domain_prompt("PRD", project.config.domain_pack, "Write a concise Vietnamese PRD. Include BG-001."), fallback=prd_fallback), encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(writer.write_markdown(artifact_type="BRD", source_text=source_text, instructions=inject_domain_prompt("BRD", project.config.domain_pack, f"Write Vietnamese BRD. Must include requirement ID {br} and Linked source SRC-001."), fallback=brd_fallback), encoding="utf-8")
    (srs_dir / "srs.md").write_text(writer.write_markdown(artifact_type="SRS", source_text=source_text, instructions=inject_domain_prompt("SRS", project.config.domain_pack, f"Write Vietnamese SRS with sections '# SRS', '## 1. Introduction', '## 2. Overall Description', '## 3. Specific Requirements'. Must include {req}, linked to {br}, and mention {scr}, {api}, {wf}, {us}."), fallback=srs_fallback), encoding="utf-8")
    (srs_dir / "screens" / f"{scr}.md").write_text(f"# {scr}: Màn hình quản lý tài liệu\n\n**Linked REQ:** {req}\n\n## Purpose\nCho phép xem trạng thái artifact, gate và baseline.\n", encoding="utf-8")
    (srs_dir / "apis" / f"{api}.md").write_text(f"# {api}: Artifact Generation API\n\n**Linked REQ:** {req}\n\n## Endpoint\nPOST /api/v1/projects/{{project_id}}/artifacts\n", encoding="utf-8")
    (srs_dir / "workflows" / f"{wf}.md").write_text(f"# {wf}: Source to Documentation Workflow\n\n**Linked REQ:** {req}\n\n## Steps\nUpload source → Redact → Generate → Gate A/B → Traceability.\n", encoding="utf-8")
    us_dir = ba_dir / "04-us"; us_dir.mkdir(exist_ok=True)
    (us_dir / f"{us}.md").write_text(f"""# User Story {us}: Sinh tài liệu từ source

**Linked REQ:** {req}
**Linked Work Items:** {scr}, {api}, {wf}

As a PM/BA, I want to import project sources so that PMO Studio can generate traceable documentation.

## Acceptance Criteria
### {ac1}
Given a source file contains sensitive values, when Stage 0 processes it, then redacted source is created and source inventory flags redaction.

### {ac2}
Given BA generation runs, when it completes, then PRD/BRD/SRS/US/Quotation artifacts exist with valid IDs.
""", encoding="utf-8")
    (ba_dir / "05-test-cases.md").write_text(f"""# Test Cases

| ID | Linked AC | Scenario | Expected Result |
|---|---|---|---|
| {tc} | {ac1} | Source has API key | Redacted source masks secret and inventory logs redaction |
""", encoding="utf-8")
    _write_quotation(ba_dir / "06-quotation.xlsx", project, [(est_scr, "Screen", scr, 2.75), (est_api, "API", api, 2.30)])
    project.mark_stage("ba.source_driven", "completed")


def _source_summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("--- SOURCE")]
    return "\n".join(f"- {line[:180]}" for line in lines[:8])


def _write_quotation(path: Path, project: Project, rows: list[tuple[str, str, str, float]]) -> None:
    wb = Workbook(); ws = wb.active; ws.title = "Summary"
    total = sum(r[3] for r in rows)
    ws.append(["Metric", "Value"]); ws.append(["Manday Rate", project.config.manday_rate_vnd]); ws.append(["Total manday", total]); ws.append(["Total cost VND", total * project.config.manday_rate_vnd])
    detail = wb.create_sheet("Estimate Detail")
    detail.append(["EST ID", "Module", "Function", "Work Item Type", "Work Item ID", "Complexity", "Rationale", "BA md", "UX md", "FE md", "BE md", "DB md", "QA md", "Total md", "Risk Factor", "Cost VND"])
    for est, typ, wid, md in rows:
        detail.append([est, "Core", "Source-driven generation", typ, wid, "medium", "Source-derived estimate", 0.25, 0.5 if typ == "Screen" else 0, 1.0 if typ == "Screen" else 0, 0.5 if typ == "Screen" else 1.5, 0.2 if typ == "API" else 0, 0.5, md, 1.0, md * project.config.manday_rate_vnd])
    wb.save(path)
