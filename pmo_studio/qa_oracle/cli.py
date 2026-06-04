from __future__ import annotations

from pathlib import Path
import json

from .config import load_adapter
from .snapshot import build_snapshot_from_json, write_snapshot, load_snapshot
from .testcases import build_oracle_testcases, export_oracle_workbook
from .quality import check_oracle_workbook, write_quality_report


def cmd_qa_oracle(args) -> int:
    if args.action == "snapshot":
        adapter = load_adapter(args.adapter)
        raw = json.loads(Path(args.raw_json).read_text(encoding="utf-8"))
        snapshot = build_snapshot_from_json(adapter, raw)
        out = write_snapshot(snapshot, args.out)
        print(f"Oracle snapshot: {out} metrics={len(snapshot.metrics)}")
        return 0
    if args.action == "generate":
        adapter = load_adapter(args.adapter)
        snapshot = load_snapshot(args.snapshot)
        cases = build_oracle_testcases(adapter, snapshot)
        out = export_oracle_workbook(cases, snapshot, args.out, project=args.project, module=args.module)
        print(f"Oracle testcase workbook: {out} cases={len(cases)}")
        return 0
    if args.action == "quality":
        result = check_oracle_workbook(args.workbook, min_cases=args.min_cases, require_oracle_sheet=not args.no_require_oracle_sheet)
        if args.out:
            write_quality_report(result, args.out)
        print(f"Oracle workbook quality: {'PASS' if result.passed else 'FAIL'} cases={result.counts.get('test_cases')}")
        for issue in result.issues:
            print(f"- {issue.severity.upper()} {issue.code}: {issue.message}")
        return 0 if result.passed else 2
    raise SystemExit(f"Unsupported qa-oracle action: {args.action}")
