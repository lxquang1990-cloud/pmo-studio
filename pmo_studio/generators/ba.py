"""Deterministic BA artifact generators for MVP/full v2.1 scaffold."""
from __future__ import annotations

from pathlib import Path

from pmo_studio.core.ids import IdAllocator
from pmo_studio.core.project import Project
from pmo_studio.domain.bteco import COMPLEXITY_MD
from pmo_studio.domain.prompts import get_domain


def _area(text: str = "CORE") -> str:
    return "CORE"


def generate_ba(project: Project, module: str = "Core") -> None:
    domain = get_domain(project.config.domain_pack)
    allocator = IdAllocator.from_state(project.state.id_counters)
    area = _area(module)
    br1 = allocator.issue("BR", area)
    req1 = allocator.issue("REQ", area)
    scr1 = allocator.issue("SCR", area)
    api1 = allocator.issue("API", area)
    wf1 = allocator.issue("WF", area)
    us1 = allocator.issue("US")
    ac1 = allocator.issue("AC", parent_us=us1)
    ac2 = allocator.issue("AC", parent_us=us1)
    tc1 = allocator.issue("TC")
    est1 = allocator.issue("EST")
    est2 = allocator.issue("EST")
    project.state.id_counters = allocator.counters

    ba_dir = project.root / "artifacts/ba"
    ba_dir.mkdir(parents=True, exist_ok=True)
    (ba_dir / "01-prd.md").write_text(f"""# PRD: {project.config.project_slug}

## Domain: {domain.label} ({domain.industry})

## Overview
Tài liệu PRD khởi tạo từ Stage 0 cho khách hàng {project.config.customer}.
{domain.prd_context[:200] if domain.prd_context else ""}

## Business Goals
- BG-001: Chuẩn hóa vòng đời tài liệu dự án và báo giá.
""", encoding="utf-8")
    (ba_dir / "02-brd.md").write_text(f"""# BRD

## Domain: {domain.label}

## 1. Business Context
{domain.brd_context[:300] if domain.brd_context else 'Khách hàng cần một Documentation Operating System để quản lý tài liệu dự án phần mềm.'}

## 2. Business Requirements
### {br1}: Quản lý tài liệu dự án theo traceability
**Linked source:** SRC-001
**Description:** Hệ thống phải hỗ trợ tạo và liên kết tài liệu từ intake đến quotation.
**Priority:** P0
""", encoding="utf-8")

    srs_dir = ba_dir / "03-srs"
    for sub in ["functional-spec", "screens", "apis", "workflows", "reports"]:
        (srs_dir / sub).mkdir(parents=True, exist_ok=True)
    (srs_dir / "srs.md").write_text(f"""# SRS

## Domain: {domain.label}

## 1. Introduction
SRS cho project {project.config.project_slug} — {domain.industry}.

## 2. Overall Description
{domain.srs_context[:400] if domain.srs_context else 'Hệ thống tạo artifact, kiểm tra quality gate, quản lý traceability và export.'}

## 3. Specific Requirements
### {req1}: Tạo project và artifact pipeline
**Linked BR:** {br1}
**Description:** Người dùng có thể tạo project, chạy Stage 0 và sinh BA artifacts.
**Verification:** Có state.json, artifact files và RTM.

### Linked Work Items
- Screen: {scr1}
- API: {api1}
- Workflow: {wf1}
- User Story: {us1}
""", encoding="utf-8")
    (srs_dir / "screens" / f"{scr1}.md").write_text(f"# {scr1}: Project Dashboard\n\n**Linked REQ:** {req1}\n\n## Purpose\nHiển thị trạng thái project và artifacts.\n", encoding="utf-8")
    (srs_dir / "apis" / f"{api1}.md").write_text(f"# {api1}: Create Project API\n\n**Linked REQ:** {req1}\n\n## Endpoint\nPOST /projects\n", encoding="utf-8")
    (srs_dir / "workflows" / f"{wf1}.md").write_text(f"# {wf1}: Intake to Artifact Workflow\n\n**Linked REQ:** {req1}\n\n## Steps\nStage 0 → BA → Gate → Export.\n", encoding="utf-8")

    us_dir = ba_dir / "04-us"
    us_dir.mkdir(exist_ok=True)
    (us_dir / f"{us1}.md").write_text(f"""# User Story {us1}: Tạo project PMO Studio

**Linked REQ:** {req1}
**Linked Work Items:** {scr1}, {api1}, {wf1}

As a PM/BA, I want to create a PMO Studio project so that I can generate controlled project documentation.

## Acceptance Criteria
### {ac1}
Given project input is valid, when I run init, then state.json and Stage 0 artifacts are created.

### {ac2}
Given the project exists, when I generate BA artifacts, then BRD/SRS/US/quotation files are produced with valid IDs.
""", encoding="utf-8")
    (ba_dir / "05-test-cases.md").write_text(f"""# Test Cases

| ID | Linked AC | Scenario | Expected Result |
|---|---|---|---|
| {tc1} | {ac1} | Init valid project | Project layout and Stage 0 files exist |
""", encoding="utf-8")

    from pmo_studio.generators.quotation import generate_quotation_for_project
    generate_quotation_for_project(project, ba_dir / "06-quotation.xlsx")
    project.mark_stage("ba", "completed", artifacts=["01-prd.md", "02-brd.md", "03-srs/srs.md", "04-us", "05-test-cases.md", "06-quotation.xlsx"])
