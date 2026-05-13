"""PO, PM, IC scaffold generators for full v2.1 coverage."""
from __future__ import annotations

from openpyxl import Workbook
from pmo_studio.core.project import Project
from pmo_studio.domain.prompts import get_domain


def generate_po(project: Project) -> None:
    domain = get_domain(project.config.domain_pack)
    d = project.root / "artifacts/po"
    d.mkdir(parents=True, exist_ok=True)
    (d / "01-vision.md").write_text(f"""# Product Vision

## Domain: {domain.label}

## Vision Statement
{domain.prd_context[:300] if domain.prd_context else 'PMO Studio giúp chuẩn hóa tài liệu dự án phần mềm từ intake đến go-live.'}

## Scope & Success Metrics
- Scope: chuẩn hóa pipeline tài liệu từ source intake tới BRD/SRS/US/AC/Quotation/export.
- KPI: giảm 50% thời gian draft tài liệu BA, 85% artifact đạt gate sau tối đa 2 vòng review.
- Review cadence: PO/PM/BA review theo từng release, evidence lưu trong quality gate output.

## Business Goals
### BG-001: Rút ngắn thời gian tạo tài liệu
**Linked source:** SRC-001
**Priority:** P0

## Target Customer
PM/BA/IC nội bộ BTECO.

## Non-Goals
Không tự gửi báo giá chính thức khi chưa có human approval.
""", encoding="utf-8")
    (d / "02-okr.md").write_text("# OKR Set\n\n| Objective | Key Result |\n|---|---|\n| Chuẩn hóa doc pipeline | 85% Gate pass sau <=2 retry |\n", encoding="utf-8")
    (d / "03-roadmap.md").write_text("# Roadmap\n\n## Now\nBA pipeline.\n\n## Next\nIC implementation pack.\n\n## Later\nGovernance dashboard.\n", encoding="utf-8")
    wb = Workbook(); ws = wb.active; ws.title = "Backlog"; ws.append(["Item", "RICE", "Priority"]); ws.append(["BA pipeline", 100, "P0"]); wb.save(d / "04-backlog.xlsx")
    (d / "05-release-notes.md").write_text("# Release Notes\n\n## v0.1\nInitial PMO Studio scaffold.\n", encoding="utf-8")
    project.mark_stage("po", "completed")


def generate_pm(project: Project) -> None:
    domain = get_domain(project.config.domain_pack)
    d = project.root / "artifacts/pm"
    d.mkdir(parents=True, exist_ok=True)
    (d / "01-charter.md").write_text(f"# Project Charter\n\n## Domain: {domain.label}\n\n## Objective\nBuild PMO Studio v2.1 for {domain.label}.\n\n## Industry Context\n{domain.industry}.\n\n## Scope\nStage 0 + PO/PM/BA/IC + gates + traceability.\n\n## Linked Outcomes\n- Linked source: SRC-001\n- Business goal: BG-001\n- Success metric: 85% quality gate pass rate after <=2 review cycles.\n\n## Acceptance / Review\nPM validates timeline, BA validates requirement evidence, IC validates implementation readiness before client-ready export.\n", encoding="utf-8")
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
    for i, name in enumerate(["deployment-plan", "uat-plan", "training", "migration-plan", "cutover-plan", "go-live-checklist", "hypercare-plan"], start=3):
        (d / f"{i:02d}-{name}.md").write_text(f"# {name.replace('-', ' ').title()}\n\nInitial scaffold for PMO Studio v2.1.\n", encoding="utf-8")
    project.mark_stage("ic", "completed")
