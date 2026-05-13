"""PMO Studio CLI."""
from __future__ import annotations

import argparse
from pathlib import Path

from pmo_studio.core.project import Project, DEFAULT_ROOT
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.generators.ba import generate_ba
from pmo_studio.generators.source_ba import generate_ba_from_sources
from pmo_studio.generators.po_pm_ic import generate_po, generate_pm, generate_ic
from pmo_studio.gates.gate_a import run_gate_a, save_gate_result as save_gate_a_result
from pmo_studio.gates.gate_bc import run_gate_b_or_c, save_gate_result as save_gate_bc_result
from pmo_studio.traceability.engine import TraceabilityEngine
from pmo_studio.traceability.validator import validate_traceability
from pmo_studio.exporters.static_html import export_static
from pmo_studio.exporters.docx_export import export_docx
from pmo_studio.exporters.bundle import export_bundle
from pmo_studio.core.manifest import create_baseline, diff_against_baseline
from pmo_studio.core.change_request import create_change_request
from pmo_studio.eval.runner import run_eval, run_benchmark
from pmo_studio.llm.factory import build_llm
from pmo_studio.llm.reviewer import JSONLLMReviewer, build_gate_reviewer
from pmo_studio.rubrics.loader import ensure_default_rubrics
from pmo_studio.templates.loader import ensure_default_templates
from pmo_studio.gates.runner import run_all_gates
from pmo_studio.core.doctor import run_doctor
from pmo_studio.generators.refinement import refine_markdown_artifact
from pmo_studio.metrics.recorder import MetricsRecorder
from pmo_studio.core.registry import list_projects, recent_project, refresh_registry
from pmo_studio.core.lifecycle import summarize_project, summary_markdown, sync_lifecycle, archive_project, clone_project, set_lifecycle


def _resolve_slug(args) -> str:
    if getattr(args, 'slug', None):
        return args.slug
    recent = recent_project(Path(args.root))
    if not recent:
        raise SystemExit('No PMO project found. Use init first or pass <slug>.')
    return recent.slug


def cmd_init(args):
    p = Project.create(args.slug, customer=args.customer, root_base=Path(args.root), domain_pack=args.domain_pack)
    sources = [Path(s) for s in args.source]
    generate_stage0(p, brief=args.brief, products=args.product, sources=sources)
    print(f"Created project: {p.root}")


def cmd_generate(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    recorder = MetricsRecorder(p.root)
    llm = build_llm(args.llm, args.model)
    with recorder.span("generate", persona=args.persona, from_sources=args.from_sources, llm=args.llm, model=args.model):
        if args.persona in {"po", "all"}: generate_po(p)
        if args.persona in {"pm", "all"}: generate_pm(p)
        if args.persona in {"ba", "all"}:
            generate_ba_from_sources(p, llm=llm) if args.from_sources else generate_ba(p)
        if args.persona in {"ic", "all"}: generate_ic(p)
    if args.refine:
        targets = _refine_targets(p, args.persona)
        for stage, artifact in targets:
            if artifact.exists() and artifact.suffix.lower() == ".md":
                with recorder.span("refine", stage=stage, artifact=str(artifact.relative_to(p.root))):
                    rr = refine_markdown_artifact(artifact, stage, llm=llm, max_attempts=args.max_refine, model=args.model, domain_pack=p.config.domain_pack)
                    recorder.record("refine.result", **rr.__dict__)
    with recorder.span("trace.write"):
        TraceabilityEngine(p.root).write_outputs()
    metrics_path = recorder.save()
    print(f"Generated {args.persona} artifacts for {p.config.project_slug}")
    print(f"Metrics: {metrics_path}")


def _refine_targets(p: Project, persona: str):
    all_targets = []
    if persona in {"po", "all"}:
        all_targets.append(("po.vision", p.root / "artifacts" / "po" / "01-vision.md"))
    if persona in {"pm", "all"}:
        all_targets.append(("pm.charter", p.root / "artifacts" / "pm" / "01-charter.md"))
    if persona in {"ba", "all"}:
        all_targets.extend([
            ("ba.prd", p.root / "artifacts" / "ba" / "01-prd.md"),
            ("ba.brd", p.root / "artifacts" / "ba" / "02-brd.md"),
            ("ba.srs", p.root / "artifacts" / "ba" / "03-srs" / "srs.md"),
            ("ba.test_cases", p.root / "artifacts" / "ba" / "05-test-cases.md"),
        ])
    if persona in {"ic", "all"}:
        all_targets.extend([
            ("ic.deployment_plan", p.root / "artifacts" / "ic" / "03-deployment-plan.md"),
            ("ic.uat_plan", p.root / "artifacts" / "ic" / "04-uat-plan.md"),
        ])
    return all_targets


def cmd_gate(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    if args.layer == "A":
        result = run_gate_a(Path(args.artifact), args.stage)
        out = save_gate_a_result(result, p.root)
    else:
        reviewer = JSONLLMReviewer(build_llm(args.llm, args.model), model=args.model) if args.llm != "noop" else None
        result = run_gate_b_or_c(Path(args.artifact), args.stage, args.layer, reviewer=reviewer)
        out = save_gate_bc_result(result, p.root)
    print(f"Gate {args.layer} {args.stage}: {'PASS' if result.passed else 'FAIL'} -> {out}")
    for c in result.checks:
        print(f"- [{'x' if c.passed else ' '}] {c.id}: {c.evidence}")


def cmd_trace(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    TraceabilityEngine(p.root).write_outputs()
    if args.validate:
        result = validate_traceability(p.root)
        print(f"Traceability validation: {'PASS' if result.passed else 'WARN'} nodes={result.node_count} edges={result.edge_count} missing={len(result.missing_upstream)} orphan={len(result.orphan_ids)}")
    print(f"Traceability written: {p.root / 'traceability'}")


def cmd_export(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    outputs = []
    if args.format in {"html", "all"}:
        outputs.append(export_static(p.root))
    if args.format in {"docx", "all"}:
        outputs.append(export_docx(p.root, profile=args.profile))
    if args.format in {"zip", "all"}:
        outputs.append(export_bundle(p.root, profile=args.profile, include_sources=args.include_redacted_sources))
    for path in outputs:
        print(f"Exported: {path}")


def cmd_baseline(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    manifest = create_baseline(p.root, p.config.project_slug, args.version)
    p.state.lifecycle_state = "BASELINED"
    p.save()
    print(f"Baseline {args.version}: {manifest.item_count} files, sha256={manifest.manifest_sha256}")


def cmd_diff(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    diff = diff_against_baseline(p.root, args.version)
    print(f"Baseline diff {args.version}")
    for key in ["added", "modified", "removed"]:
        print(f"{key}: {len(diff[key])}")
        for item in diff[key][:30]:
            print(f"- {item}")
    print(f"unchanged_count: {diff['unchanged_count']}")


def cmd_cr(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    out = create_change_request(p, args.baseline, args.title, args.description, args.requested_by)
    print(f"Created CR: {out}")


def cmd_scaffold(args):
    ensure_default_rubrics()
    ensure_default_templates()
    print("Scaffolded default rubrics/templates")


def cmd_run_gates(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    reviewer = build_gate_reviewer(
        args.llm,
        args.model,
        cache_root=args.gate_cache,
        fallback_on_error=args.gate_fallback,
        timeout=args.gate_timeout,
    ) if hasattr(args, 'llm') and args.llm != "noop" else None
    summary = run_all_gates(p, include_c=args.include_c, reviewer=reviewer)
    if reviewer:
        print(f"Reviewer: {args.llm}/{args.model or 'default'} cache={reviewer.cache.root if reviewer.cache else 'off'} timeout={args.gate_timeout}s")
    print(f"Quality summary: total={summary['total']} passed={summary['passed']} failed={summary['failed']} skipped={summary['skipped']}")
    print(f"Written: {p.root / 'quality' / 'summary.json'}")


def cmd_doctor(args):
    project = None
    if args.slug:
        project = Project.load(args.slug, root_base=Path(args.root))
    result = run_doctor(project)
    print(f"Doctor: {'PASS' if result['passed'] else 'WARN'}")
    for c in result['checks']:
        mark = 'x' if c['passed'] else ' '
        print(f"- [{mark}] {c['id']}: {c['evidence']}")


def cmd_list(args):
    if args.refresh:
        refresh_registry(Path(args.root))
    entries = list_projects(Path(args.root), include_archived=args.include_archived)
    if not entries:
        print('No PMO projects found')
        return
    for e in entries[:args.limit]:
        print(f"{e.slug}\t{e.customer}\t{e.lifecycle_state}\t{e.current_stage}\t{e.root}")


def cmd_recent(args):
    e = recent_project(Path(args.root))
    if not e:
        print('No PMO projects found')
        return
    print(f"{e.slug}\t{e.customer}\t{e.lifecycle_state}\t{e.current_stage}\t{e.root}")


def cmd_summary(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    print(summary_markdown(summarize_project(p)))


def cmd_sync_lifecycle(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    state = sync_lifecycle(p)
    print(f"Lifecycle {p.config.project_slug}: {state}")


def cmd_set_lifecycle(args):
    args.slug = _resolve_slug(args)
    p = Project.load(args.slug, root_base=Path(args.root))
    set_lifecycle(p, args.state)
    print(f"Lifecycle {p.config.project_slug}: {p.state.lifecycle_state}")


def cmd_archive(args):
    args.slug = _resolve_slug(args)
    if not args.yes:
        raise SystemExit("Archive requires --yes")
    p = Project.load(args.slug, root_base=Path(args.root))
    dest = archive_project(p, reason=args.reason, move=args.move)
    print(f"Archived {args.slug}: {dest}")


def cmd_clone(args):
    source_slug = _resolve_slug(args)
    source = Project.load(source_slug, root_base=Path(args.root))
    cloned = clone_project(source, args.new_slug, customer=args.customer)
    print(f"Cloned {source_slug} -> {cloned.config.project_slug}: {cloned.root}")


def cmd_eval(args):
    eval_root = Path(args.root) / "eval-runs"
    if args.benchmark:
        result = run_benchmark(eval_root, export_docx_enabled=not args.no_docx,
                               llm_provider=args.llm, llm_model=args.model)
        print(f"Benchmark {result.name}: {'PASS' if result.passed else 'FAIL'} score={result.score:.2%}")
        print(f"Report: {result.report_path}")
        print(f"Results: {result.results_path}")
        for case in result.case_results:
            print(f"- {'PASS' if case.passed else 'FAIL'} {case.name}: score={float(case.details['score']):.2%} gates={float(case.details['gate_pass_rate']):.2%} trace_edges={case.details['trace_edges']}")
    else:
        result = run_eval(eval_root)
        print(f"Eval {result.name}: {'PASS' if result.passed else 'FAIL'}")
        for k, v in result.details.items():
            print(f"- {k}: {v}")


def build_parser():
    parser = argparse.ArgumentParser(prog="pmo", description="PMO Studio v2.1")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    sub = parser.add_subparsers(required=True)
    init = sub.add_parser("init")
    init.add_argument("slug")
    init.add_argument("--customer", default="TBD")
    init.add_argument("--brief", default="Tạo hệ thống PMO Studio v2.1 cho tài liệu dự án phần mềm.")
    init.add_argument("--product", action="append", default=["eOffice"])
    init.add_argument("--domain-pack", default="bteco", choices=["bteco", "eoffice", "ky_so", "hse", "pms"], help="Domain intelligence pack for domain-specific content")
    init.add_argument("--source", action="append", default=[])
    init.set_defaults(func=cmd_init)
    gen = sub.add_parser("generate")
    gen.add_argument("slug", nargs="?")
    gen.add_argument("persona", choices=["po", "pm", "ba", "ic", "all"])
    gen.add_argument("--from-sources", action="store_true", help="Generate BA artifacts from redacted sources with optional LLM fallback")
    gen.add_argument("--llm", choices=["noop", "9router"], default="noop")
    gen.add_argument("--model", default=None)
    gen.add_argument("--refine", action="store_true", help="Run Gate A/B feedback refinement loop for generated Markdown artifacts")
    gen.add_argument("--max-refine", type=int, default=1, help="Maximum refinement attempts per Markdown artifact")
    gen.set_defaults(func=cmd_generate)
    gate = sub.add_parser("gate")
    gate.add_argument("slug", nargs="?")
    gate.add_argument("stage")
    gate.add_argument("artifact")
    gate.add_argument("--layer", choices=["A", "B", "C"], default="A")
    gate.add_argument("--llm", choices=["noop", "9router"], default="noop")
    gate.add_argument("--model", default=None)
    gate.set_defaults(func=cmd_gate)
    trace = sub.add_parser("trace")
    trace.add_argument("slug", nargs="?")
    trace.add_argument("--validate", action="store_true")
    trace.set_defaults(func=cmd_trace)
    exp = sub.add_parser("export")
    exp.add_argument("slug", nargs="?")
    exp.add_argument("--format", choices=["html", "docx", "zip", "all"], default="html")
    exp.add_argument("--profile", default="client-ready")
    exp.add_argument("--include-redacted-sources", action="store_true", help="Include redacted sources in ZIP bundle; originals are never included")
    exp.set_defaults(func=cmd_export)
    baseline = sub.add_parser("baseline")
    baseline.add_argument("slug", nargs="?")
    baseline.add_argument("version")
    baseline.set_defaults(func=cmd_baseline)
    diff = sub.add_parser("diff")
    diff.add_argument("slug", nargs="?")
    diff.add_argument("version")
    diff.set_defaults(func=cmd_diff)
    cr = sub.add_parser("cr")
    cr.add_argument("slug", nargs="?")
    cr.add_argument("baseline")
    cr.add_argument("--title", required=True)
    cr.add_argument("--description", required=True)
    cr.add_argument("--requested-by", default="Snail")
    cr.set_defaults(func=cmd_cr)
    sc = sub.add_parser("scaffold")
    sc.set_defaults(func=cmd_scaffold)
    rg = sub.add_parser("run-gates")
    rg.add_argument("slug", nargs="?")
    rg.add_argument("--include-c", action="store_true")
    rg.add_argument("--llm", choices=["noop", "9router"], default="noop")
    rg.add_argument("--model", default=None)
    rg.add_argument("--gate-cache", default=None, help="Cache directory for LLM Gate B/C reviews")
    rg.add_argument("--gate-timeout", type=int, default=60, help="Per-review LLM timeout in seconds")
    rg.add_argument("--gate-fallback", action="store_true", help="Return failing gate checks instead of raising on LLM errors")
    rg.set_defaults(func=cmd_run_gates)
    ls = sub.add_parser("list")
    ls.add_argument("--refresh", action="store_true")
    ls.add_argument("--limit", type=int, default=20)
    ls.add_argument("--include-archived", action="store_true")
    ls.set_defaults(func=cmd_list)
    recent = sub.add_parser("recent")
    recent.set_defaults(func=cmd_recent)
    summ = sub.add_parser("summary")
    summ.add_argument("slug", nargs="?")
    summ.set_defaults(func=cmd_summary)
    sync = sub.add_parser("sync-lifecycle")
    sync.add_argument("slug", nargs="?")
    sync.set_defaults(func=cmd_sync_lifecycle)
    setlife = sub.add_parser("set-lifecycle")
    setlife.add_argument("slug", nargs="?")
    setlife.add_argument("state", choices=["INITIATED", "GENERATED", "GATED", "EXPORTED", "BASELINED", "ARCHIVED"])
    setlife.set_defaults(func=cmd_set_lifecycle)
    arch = sub.add_parser("archive")
    arch.add_argument("slug", nargs="?")
    arch.add_argument("--reason", default="")
    arch.add_argument("--move", action="store_true", help="Move project folder under _archived/")
    arch.add_argument("--yes", action="store_true", help="Required confirmation flag")
    arch.set_defaults(func=cmd_archive)
    clone = sub.add_parser("clone")
    clone.add_argument("slug", nargs="?")
    clone.add_argument("new_slug")
    clone.add_argument("--customer", default=None)
    clone.set_defaults(func=cmd_clone)
    doc = sub.add_parser("doctor")
    doc.add_argument("slug", nargs="?")
    doc.set_defaults(func=cmd_doctor)
    ev = sub.add_parser("eval")
    ev.add_argument("--benchmark", action="store_true", help="Run multi-project benchmark suite")
    ev.add_argument("--no-docx", action="store_true", help="Skip DOCX export during benchmark")
    ev.add_argument("--llm", choices=["noop", "9router"], default="noop")
    ev.add_argument("--model", default=None)
    ev.set_defaults(func=cmd_eval)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
