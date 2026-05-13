#!/usr/bin/env python3
"""Compare deterministic PMO benchmark gates vs LLM-powered Gate B/C review.

This script runs the same benchmark cases twice:
1. deterministic gates (`--llm noop` equivalent)
2. 9Router-backed generation + Gate B/C reviewer

It writes JSON and Markdown reports under the selected output root.
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

from pmo_studio.eval.runner import run_benchmark


def _load_key_from_openclaw_models() -> str:
    models_path = Path.home() / ".openclaw" / "agents" / "main" / "agent" / "models.json"
    if not models_path.exists():
        return ""
    try:
        data = json.loads(models_path.read_text(encoding="utf-8"))
        return data.get("providers", {}).get("9router", {}).get("apiKey", "")
    except Exception:
        return ""


def _write_report(det, llm, out: Path, model: str) -> None:
    rows = []
    for d_case, l_case in zip(det.case_results, llm.case_results):
        d = d_case.details
        l = l_case.details
        rows.append({
            "case": d_case.name,
            "deterministic_passed": d_case.passed,
            "llm_passed": l_case.passed,
            "deterministic_score": float(d.get("score", 0.0)),
            "llm_score": float(l.get("score", 0.0)),
            "score_delta": round(float(l.get("score", 0.0)) - float(d.get("score", 0.0)), 4),
            "deterministic_gate_pass_rate": float(d.get("gate_pass_rate", 0.0)),
            "llm_gate_pass_rate": float(l.get("gate_pass_rate", 0.0)),
            "gate_pass_rate_delta": round(float(l.get("gate_pass_rate", 0.0)) - float(d.get("gate_pass_rate", 0.0)), 4),
            "trace_edges": l.get("trace_edges"),
            "redacted_ok": l.get("redacted_ok"),
            "quotation_total_manday": l.get("quotation_total_manday"),
        })

    payload = {
        "model": model,
        "deterministic": asdict(det),
        "llm": asdict(llm),
        "comparison": rows,
        "summary": {
            "deterministic_score": det.score,
            "llm_score": llm.score,
            "score_delta": round(llm.score - det.score, 4),
            "deterministic_passed": det.passed,
            "llm_passed": llm.passed,
        },
    }
    (out / "comparison.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# PMO Studio LLM Gate Benchmark Comparison",
        "",
        f"**Model:** `{model}`",
        f"**Deterministic score:** {det.score:.2%}",
        f"**LLM score:** {llm.score:.2%}",
        f"**Delta:** {llm.score - det.score:+.2%}",
        f"**Status:** deterministic={'PASS' if det.passed else 'FAIL'}, llm={'PASS' if llm.passed else 'FAIL'}",
        "",
        "| Case | Det Score | LLM Score | Delta | Det Gate Rate | LLM Gate Rate | Gate Delta | LLM Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['case']} | {r['deterministic_score']:.2%} | {r['llm_score']:.2%} | {r['score_delta']:+.2%} | "
            f"{r['deterministic_gate_pass_rate']:.2%} | {r['llm_gate_pass_rate']:.2%} | {r['gate_pass_rate_delta']:+.2%} | "
            f"{'PASS' if r['llm_passed'] else 'FAIL'} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A lower LLM gate pass rate is not automatically worse: it usually means Gate B/C is reviewing semantic quality more strictly than deterministic keyword checks.",
        "Use this report to decide whether to refine artifacts, adjust rubrics, or keep deterministic gates as the CI default.",
        "",
    ])
    (out / "comparison.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/tmp/pmo-llm-gate-compare")
    parser.add_argument("--model", default="Tier2")
    parser.add_argument("--gate-timeout", type=int, default=60)
    parser.add_argument("--gate-fallback", action="store_true")
    parser.add_argument("--no-autoload-key", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("9ROUTER_API_KEY") and not args.no_autoload_key:
        key = _load_key_from_openclaw_models()
        if key:
            os.environ["9ROUTER_API_KEY"] = key

    root = Path(args.root)
    det_root = root / "deterministic"
    llm_root = root / "llm"
    out = root / "comparison"
    out.mkdir(parents=True, exist_ok=True)

    det = run_benchmark(det_root, export_docx_enabled=False, llm_provider="noop")
    llm = run_benchmark(
        llm_root,
        export_docx_enabled=False,
        llm_provider="noop",
        gate_reviewer_provider="9router",
        gate_reviewer_model=args.model,
        gate_cache_root=root / "gate-cache",
        gate_timeout=args.gate_timeout,
        gate_fallback=args.gate_fallback,
    )
    _write_report(det, llm, out, args.model)

    print(f"DETERMINISTIC score={det.score:.2%} passed={det.passed}")
    print(f"LLM_GATES score={llm.score:.2%} passed={llm.passed}")
    print(f"DELTA {llm.score - det.score:+.2%}")
    print(f"REPORT {out / 'comparison.md'}")
    if not llm.passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
