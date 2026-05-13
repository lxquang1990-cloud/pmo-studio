"""YAML rubric loader for Gate A/B/C."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_RUBRIC_DIR = Path(__file__).resolve().parent

STAGE_SECTIONS = {
    "ba.prd": ["# PRD", "## Overview", "## Business Goals"],
    "ba.brd": ["# BRD", "## 1. Business Context", "## 2. Business Requirements"],
    "ba.srs": ["# SRS", "## 1. Introduction", "## 2. Overall Description", "## 3. Specific Requirements"],
    "ba.us_ac": ["# User Story", "## Acceptance Criteria"],
    "ba.test_cases": ["# Test Cases"],
    "po.vision": ["# Product Vision", "## Vision Statement", "## Business Goals"],
    "pm.charter": ["# Project Charter", "## Objective", "## Scope"],
    "ic.deployment_plan": ["# Deployment Plan"],
    "ic.uat_plan": ["# Uat Plan"],
}

SEMANTIC_CHECKS_B = [
    {"id": "no_tbd", "question": "Không còn placeholder/TBD critical?", "blocker": True},
    {"id": "clear_scope", "question": "Scope hoặc purpose có mô tả rõ ràng?"},
    {"id": "ids_linked", "question": "Các ID chính có link upstream/downstream?"},
    {"id": "testable", "question": "Requirement/AC có thể kiểm chứng?"},
]

SEMANTIC_CHECKS_C = [
    {"id": "ready_for_customer", "question": "Đủ sạch để gửi khách hàng review?", "blocker": True},
    {"id": "ready_for_dev", "question": "Đủ rõ để dev estimate/code?"},
    {"id": "consistency", "question": "Nhất quán với artifact upstream/context?", "blocker": True},
    {"id": "no_open_questions", "question": "Không còn open question critical?"},
]

EXCEL_STAGE_META = {
    "ba.quotation": {"kind": "excel", "sheets": ["Summary", "Estimate Detail"]},
    "ic.fit_gap": {"kind": "excel", "sheets": ["Summary", "Fit-Gap Detail"]},
    "ic.config_workbook": {"kind": "excel", "sheets": ["Summary", "Org Settings"]},
}


def rubric_path(stage: str, layer: str, root: Path | None = None) -> Path:
    base = root or DEFAULT_RUBRIC_DIR
    return base / stage.replace(".", "/") / f"gate_{layer.lower()}.yaml"


def load_rubric(stage: str, layer: str, root: Path | None = None) -> dict[str, Any] | None:
    path = rubric_path(stage, layer, root)
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def ensure_default_rubrics(root: Path | None = None) -> None:
    base = root or DEFAULT_RUBRIC_DIR
    for stage, sections in STAGE_SECTIONS.items():
        _write_stage_rubrics(base, stage, sections)
    for stage, meta in EXCEL_STAGE_META.items():
        _write_excel_rubrics(base, stage, meta["sheets"])


def _write_stage_rubrics(base: Path, stage: str, sections: list[str]) -> None:
    target = base / stage.replace(".", "/")
    target.mkdir(parents=True, exist_ok=True)
    _write_yaml(target / "gate_a.yaml", {"stage": stage, "layer": "A", "sections": sections, "ids": {"validate": True, "no_duplicates": True}})
    _write_yaml(target / "gate_b.yaml", {"stage": stage, "layer": "B", "pass_threshold": 0.8, "checks": SEMANTIC_CHECKS_B})
    _write_yaml(target / "gate_c.yaml", {"stage": stage, "layer": "C", "pass_threshold": 0.9, "checks": SEMANTIC_CHECKS_C})


def _write_excel_rubrics(base: Path, stage: str, sheets: list[str]) -> None:
    target = base / stage.replace(".", "/")
    target.mkdir(parents=True, exist_ok=True)
    _write_yaml(target / "gate_a.yaml", {"stage": stage, "layer": "A", "kind": "excel", "sheets": sheets})
    _write_yaml(target / "gate_b.yaml", {"stage": stage, "layer": "B", "pass_threshold": 0.8, "checks": SEMANTIC_CHECKS_B})
    _write_yaml(target / "gate_c.yaml", {"stage": stage, "layer": "C", "pass_threshold": 0.9, "checks": SEMANTIC_CHECKS_C})


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    if path.exists():
        return
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
