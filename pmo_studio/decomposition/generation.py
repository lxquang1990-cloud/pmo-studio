"""Decomposition-driven generation helpers (v3.1)."""
from __future__ import annotations

from pathlib import Path

from pmo_studio.decomposition.engine import load_decomposition, write_decomposition, DecompositionReport


def generate_from_decomposition(project_root: Path) -> dict[str, str]:
    report = load_decomposition(project_root)
    if report is None:
        write_decomposition(project_root)
        report = load_decomposition(project_root)
    assert report is not None
    ba = project_root / "artifacts" / "ba"
    srs = ba / "03-srs"
    us = ba / "04-us"
    ba.mkdir(parents=True, exist_ok=True); srs.mkdir(parents=True, exist_ok=True); us.mkdir(parents=True, exist_ok=True)
    paths = {
        "brd_addendum": ba / "02a-decomposition-addendum.md",
        "srs_addendum": srs / "decomposition-requirements.md",
        "user_stories": us / "US-DECOMP-001.md",
        "test_cases": ba / "05a-decomposition-test-cases.md",
    }
    paths["brd_addendum"].write_text(_brd(report), encoding="utf-8")
    paths["srs_addendum"].write_text(_srs(report), encoding="utf-8")
    paths["user_stories"].write_text(_stories(report), encoding="utf-8")
    paths["test_cases"].write_text(_tests(report), encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def _brd(r: DecompositionReport) -> str:
    lines = [f"# Decomposition-driven BRD Addendum: {r.project_slug}", "", f"Domain: {r.domain}", "", "## Capability to Feature Map", "", "| Capability | Feature | Work items | Score |", "|---|---|---:|---:|"]
    for c in r.capabilities:
        for f in c.features:
            lines.append(f"| {c.name} | {f.name} | {len(f.work_items)} | {f.completeness_score} |")
    lines += ["", "## Business Impact", "- SRS, user stories, tests, and estimate should use this decomposition as canonical scope input.", "- Gaps must be reviewed before customer signoff or quotation finalization.", ""]
    return "\n".join(lines)


def _srs(r: DecompositionReport) -> str:
    lines = [f"# Decomposition-driven SRS Requirements: {r.project_slug}", "", "| REQ ID | Feature | Requirement | Work Items |", "|---|---|---|---|"]
    idx = 1
    for c in r.capabilities:
        for f in c.features:
            req = f"REQ-DECOMP-{idx:03d}"
            lines.append(f"| {req} | {f.name} | System shall support {f.name.lower()} with UI, API, workflow, data, validation, permission, audit, test and estimate coverage. | {', '.join(w.id for w in f.work_items[:6])} |")
            idx += 1
    lines.append("")
    return "\n".join(lines)


def _stories(r: DecompositionReport) -> str:
    lines = [f"# User Stories from Functional Decomposition: {r.project_slug}", ""]
    idx = 1
    for c in r.capabilities:
        for f in c.features:
            lines += [f"## US-DECOMP-{idx:03d}: {f.name}", "", f"As a business user, I want {f.name.lower()} so that the {c.name.lower()} capability is supported end-to-end.", "", "### Acceptance Criteria", f"- AC-DECOMP-{idx:03d}-01: Given authorized user and valid data, when executing {f.name.lower()}, then the system completes the workflow and records audit evidence.", f"- AC-DECOMP-{idx:03d}-02: Given invalid data or insufficient permission, when executing {f.name.lower()}, then the system blocks the action with clear error and audit trail.", ""]
            idx += 1
    return "\n".join(lines)


def _tests(r: DecompositionReport) -> str:
    lines = [f"# Decomposition-driven Test Cases: {r.project_slug}", "", "| TC ID | Linked Feature | Scenario | Expected Result |", "|---|---|---|---|"]
    idx = 1
    for c in r.capabilities:
        for f in c.features:
            lines.append(f"| TC-DECOMP-{idx:03d} | {f.id} | Execute happy path and permission/validation negative path for {f.name}. | Workflow succeeds for valid input and blocks invalid/unauthorized input with audit evidence. |")
            idx += 1
    lines.append("")
    return "\n".join(lines)
