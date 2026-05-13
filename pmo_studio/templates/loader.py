"""Template library loader."""
from __future__ import annotations

from pathlib import Path

DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parent

TEMPLATES = {
    "ba/prd.md": """# PRD: {{project_slug}}

## Overview
{{overview}}

## Business Goals
- BG-001: {{business_goal}}
""",
    "ba/brd.md": """# BRD

## 1. Business Context
{{business_context}}

## 2. Business Requirements
### {{br_id}}: {{requirement_title}}
**Linked source:** {{source_id}}
**Description:** {{description}}
**Priority:** P0
""",
    "ba/srs.md": """# SRS

## 1. Introduction
{{introduction}}

## 2. Overall Description
{{overall_description}}

## 3. Specific Requirements
{{specific_requirements}}
""",
    "ba/user-story.md": """# User Story {{us_id}}: {{title}}

**Linked REQ:** {{req_id}}

As a {{role}}, I want {{want}} so that {{benefit}}.

## Acceptance Criteria
{{acceptance_criteria}}
""",
    "ic/fit-gap.md": """# Fit-Gap Analysis

## Summary
{{summary}}
""",
    "ic/config-workbook.md": """# Configuration Workbook

## Summary
{{summary}}
""",
    "pm/charter.md": """# Project Charter

## Objective
{{objective}}

## Scope
{{scope}}
""",
    "po/vision.md": """# Product Vision

## Vision Statement
{{vision}}

## Business Goals
{{business_goals}}
""",
}


def template_path(name: str, root: Path | None = None) -> Path:
    base = root or DEFAULT_TEMPLATE_DIR
    return base / name


def load_template(name: str, root: Path | None = None, default: str = "") -> str:
    path = template_path(name, root)
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def render_template(name: str, context: dict[str, str], root: Path | None = None, default: str = "") -> str:
    text = load_template(name, root, default)
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def ensure_default_templates(root: Path | None = None) -> None:
    base = root or DEFAULT_TEMPLATE_DIR
    for name, content in TEMPLATES.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
