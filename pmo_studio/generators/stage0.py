"""Stage 0 intake generator."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from pmo_studio.core.ids import IdAllocator
from pmo_studio.core.project import Project
from pmo_studio.security.preprocessor import process_source
from pmo_studio.security.ignore import is_ignored, load_ignore_patterns, write_default_ignore
from pmo_studio.domain.prompts import get_domain


def generate_stage0(project: Project, brief: str = "TBD", products: list[str] | None = None, sources: list[Path] | None = None) -> None:
    domain = get_domain(project.config.domain_pack)
    products = products or ["eOffice"]
    allocator = IdAllocator.from_state(project.state.id_counters)
    write_default_ignore(project.root)
    ignore_patterns = load_ignore_patterns(project_root=project.root)
    scan_results = []
    ignored_sources = []
    for src in sources or []:
        if is_ignored(src, ignore_patterns):
            ignored_sources.append(src)
            continue
        source_id = allocator.issue("SRC")
        scan_results.append(process_source(source_id, src, project.root))
    project.state.id_counters = allocator.counters

    product_lines = "\n".join([f"- [x] {p}" for p in products])
    domain_roles_str = "\n".join([f"| {role} | {desc} |" for role, desc in (domain.roles or {}).items()]) if domain.roles and domain.domain_id != "bteco" else "| N/A | Generic |"
    (project.root / "artifacts/stage-0/project-brief.md").write_text(f"""# Project Brief: {project.config.project_slug}

> **Project Slug:** {project.config.project_slug}
> **Customer:** {project.config.customer}
> **Project Type:** {project.config.project_type}
> **Domain:** {domain.label} ({domain.industry})

## 1. Mục tiêu kinh doanh
{brief}

## 2. Sản phẩm BTECO liên quan
{product_lines}

## 3. Phạm vi cấp cao
- In scope: Phân tích yêu cầu, tài liệu BA/PMO, báo giá, triển khai.
- In scope: Traceability và quality gate.
- In scope: Export tài liệu theo profile.
- Out of scope: Production code application.
- Out of scope: Gửi báo giá chính thức khi chưa có human approval.

## 4. Timeline mong muốn
- Start: TBD
- Target go-live: TBD

## 5. Stakeholder chính
| Tên | Role | Mức độ ảnh hưởng |
|---|---|---|
| Snail | Sponsor/PM | High |

## 6. Domain Context
| Role | Description |
|---|---|
{domain_roles_str}

## 7. Governance mong muốn
- Baseline required: {project.config.governance.get('baseline_required')}
- Formal CR after baseline: {project.config.governance.get('formal_cr_after_baseline')}
""", encoding="utf-8")

    inv_lines = ["# Source Inventory", "", "| Source ID | Type | Path | Hash | Trusted | Redaction | Injection |", "|---|---|---|---|---|---|---|"]
    for r in scan_results:
        inv_lines.append(f"| {r.source_id} | file | {r.redacted_path} | sha256:{r.sha256} | partial | {r.redaction_count} | {r.injection_detected} |")
    if not scan_results:
        inv_lines.append("| SRC-000 | manual_input | (none yet) | - | yes | 0 | false |")
    for src in ignored_sources:
        inv_lines.append(f"| IGNORED | ignored | {src} | - | n/a | n/a | n/a |")
    (project.root / "artifacts/stage-0/source-inventory.md").write_text("\n".join(inv_lines) + "\n", encoding="utf-8")

    (project.root / "artifacts/stage-0/assumption-log.md").write_text("""# Assumption Log

| ID | Description | Source Stage | Owner | Status |
|---|---|---|---|---|
| ASM-001 | Khách hàng sẽ xác nhận scope trước baseline. | stage-0 | Snail | Active |
""", encoding="utf-8")
    (project.root / "artifacts/stage-0/decision-log.md").write_text("""# Decision Log

| ID | Decision | Rationale | Owner | Date |
|---|---|---|---|---|
| DEC-001 | Sử dụng PMO Studio v2.1 structure. | Theo design đã duyệt. | Snail | TBD |
""", encoding="utf-8")
    project.mark_stage("stage-0", "completed", artifacts=["project-brief.md", "source-inventory.md", "assumption-log.md", "decision-log.md"])
