"""Change Request drafting and baseline impact analysis."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pmo_studio.core.ids import IdAllocator
from pmo_studio.core.manifest import diff_against_baseline, load_manifest
from pmo_studio.core.project import Project


def create_change_request(project: Project, baseline_version: str, title: str, description: str, requested_by: str = "Snail") -> Path:
    allocator = IdAllocator.from_state(project.state.id_counters)
    cr_id = allocator.issue("CR")
    project.state.id_counters = allocator.counters
    manifest = load_manifest(project.root, baseline_version)
    diff = diff_against_baseline(project.root, baseline_version)
    out = project.root / "change-requests" / f"{cr_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    def bullets(items):
        return "\n".join(f"- {x}" for x in items) if items else "- None"
    out.write_text(f"""# Change Request: {cr_id}

| Field | Value |
|---|---|
| CR ID | {cr_id} |
| Baseline Affected | {baseline_version} |
| Baseline SHA256 | {manifest.manifest_sha256} |
| Title | {title} |
| Requested by | {requested_by} |
| Date | {datetime.now(timezone.utc).isoformat()} |
| Status | Submitted |

## 1. Mô tả thay đổi
{description}

## 2. Impact Analysis

### Added
{bullets(diff['added'])}

### Modified
{bullets(diff['modified'])}

### Removed
{bullets(diff['removed'])}

### Unchanged Count
{diff['unchanged_count']}

## 3. Effort & Cost Impact
TBD — cần regenerate quotation hoặc review thủ công.

## 4. Recommendation
Review modified artifacts, regenerate Gate A/B, sau đó approve/reject CR.

## 5. Approval
| Role | Name | Decision | Date |
|---|---|---|---|
| Sponsor | | | |
| PM | | | |
| BA | | | |
""", encoding="utf-8")
    project.mark_stage("pm.change_request", "ready", artifact=str(out.relative_to(project.root)))
    return out
