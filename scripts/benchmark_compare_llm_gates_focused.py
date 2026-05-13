#!/usr/bin/env python3
"""Focused deterministic-vs-LLM Gate B/C comparison for Phase 21.

Generates one deterministic eOffice project, then runs Gate B on selected artifacts twice:
- deterministic reviewer
- 9Router LLM reviewer

This avoids long full-suite LLM latency while validating the comparison pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.generators.source_ba import generate_ba_from_sources
from pmo_studio.generators.po_pm_ic import generate_po, generate_pm, generate_ic
from pmo_studio.gates.gate_bc import run_gate_b_or_c, save_gate_result
from pmo_studio.llm.reviewer import build_gate_reviewer
from pmo_studio.traceability.engine import TraceabilityEngine

SOURCE = """# eOffice Document Workflow
## Overview
Hệ thống quản lý văn bản điện tử cho doanh nghiệp vừa và nhỏ.
Cho phép tạo, luân chuyển, phê duyệt và lưu trữ văn bản.

## Actors
- Nhân viên: tạo văn bản, gửi duyệt
- Trưởng phòng: phê duyệt cấp 1
- Giám đốc: phê duyệt cấp 2
- Văn thư: quản lý lưu trữ, cấp số

## Functional
1. Tạo văn bản đến/đi (REQ-CORE-001)
2. Luân chuyển văn bản theo workflow (WF-CORE-001)
3. Phê duyệt đa cấp (WF-CORE-002)
4. Lưu trữ và tra cứu (SCR-CORE-001)
5. API tích hợp ký số (API-CORE-001)

## Non-functional
- Bảo mật: phân quyền theo role
- Hiệu năng: <3s cho tra cứu văn bản
"""

TARGETS = [
    ("ba.prd", "artifacts/ba/01-prd.md"),
    ("ba.brd", "artifacts/ba/02-brd.md"),
]


def _load_key() -> None:
    if os.environ.get("9ROUTER_API_KEY"):
        return
    models_path = Path.home() / ".openclaw" / "agents" / "main" / "agent" / "models.json"
    if models_path.exists():
        data = json.loads(models_path.read_text(encoding="utf-8"))
        key = data.get("providers", {}).get("9router", {}).get("apiKey", "")
        if key:
            os.environ["9ROUTER_API_KEY"] = key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/tmp/pmo-phase21-focused")
    parser.add_argument("--model", default="Tier2")
    parser.add_argument("--gate-timeout", type=int, default=45)
    parser.add_argument("--gate-fallback", action="store_true")
    args = parser.parse_args()

    _load_key()
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    source = root / "source.md"
    source.write_text(SOURCE, encoding="utf-8")

    p = Project.create("phase21-eoffice", customer="Phase21", root_base=root)
    generate_stage0(p, brief="Hệ thống eOffice quản lý văn bản điện tử", products=["Văn bản đến", "Văn bản đi", "Phê duyệt"], sources=[source])
    generate_po(p); generate_pm(p); generate_ba_from_sources(p); generate_ic(p)
    TraceabilityEngine(p.root).write_outputs()

    reviewer = build_gate_reviewer("9router", args.model, cache_root=root / "gate-cache", timeout=args.gate_timeout, fallback_on_error=args.gate_fallback)
    rows = []
    for stage, rel in TARGETS:
        path = p.root / rel
        det = run_gate_b_or_c(path, stage, "B")
        llm = run_gate_b_or_c(path, stage, "B", reviewer=reviewer)
        save_gate_result(llm, p.root)
        rows.append({
            "stage": stage,
            "artifact": rel,
            "deterministic_passed": det.passed,
            "llm_passed": llm.passed,
            "deterministic_checks": [asdict(c) for c in det.checks],
            "llm_checks": [asdict(c) for c in llm.checks],
        })

    out = root / "comparison"
    out.mkdir(parents=True, exist_ok=True)
    payload = {"model": args.model, "project_root": str(p.root), "results": rows}
    (out / "focused-comparison.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Focused LLM Gate B Comparison",
        "",
        f"**Model:** `{args.model}`",
        f"**Project:** `{p.root}`",
        "",
        "| Stage | Deterministic | LLM | Observation |",
        "|---|---:|---:|---|",
    ]
    for r in rows:
        observation = "LLM stricter" if r["deterministic_passed"] and not r["llm_passed"] else "aligned"
        lines.append(f"| {r['stage']} | {'PASS' if r['deterministic_passed'] else 'FAIL'} | {'PASS' if r['llm_passed'] else 'FAIL'} | {observation} |")
    lines.append("")
    lines.append("## LLM Evidence")
    lines.append("")
    for r in rows:
        lines.append(f"### {r['stage']}")
        for c in r["llm_checks"]:
            lines.append(f"- **{c['id']}**: {'PASS' if c['passed'] else 'FAIL'} — {c.get('evidence', '')}")
        lines.append("")
    (out / "focused-comparison.md").write_text("\n".join(lines), encoding="utf-8")

    print("FOCUSED_LLM_GATE_COMPARISON_PASS")
    print(f"CACHE {reviewer.cache.root if reviewer and reviewer.cache else 'off'}")
    for r in rows:
        print(f"{r['stage']}: deterministic={'PASS' if r['deterministic_passed'] else 'FAIL'} llm={'PASS' if r['llm_passed'] else 'FAIL'}")
    print(f"REPORT {out / 'focused-comparison.md'}")


if __name__ == "__main__":
    main()
