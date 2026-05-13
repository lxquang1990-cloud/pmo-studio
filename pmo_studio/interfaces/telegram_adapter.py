"""Telegram/OpenClaw-friendly text command adapter.

This module does not send Telegram messages itself. OpenClaw routes assistant replies.
It maps short PMO commands to safe PMO Studio operations and returns Markdown text.
Use MEDIA:<path> lines for surfaces that support attachment delivery.
"""
from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

from pmo_studio.core.project import Project, DEFAULT_ROOT
from pmo_studio.core.registry import list_projects, recent_project, refresh_registry
from pmo_studio.core.lifecycle import summarize_project, summary_markdown, sync_lifecycle, archive_project, clone_project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.generators.source_ba import generate_ba_from_sources
from pmo_studio.generators.po_pm_ic import generate_po, generate_pm, generate_ic
from pmo_studio.gates.runner import run_all_gates
from pmo_studio.traceability.engine import TraceabilityEngine
from pmo_studio.traceability.validator import validate_traceability
from pmo_studio.core.manifest import create_baseline
from pmo_studio.exporters.static_html import export_static
from pmo_studio.exporters.docx_export import export_docx
from pmo_studio.exporters.bundle import export_bundle
from pmo_studio.eval.runner import run_benchmark
from pmo_studio.core.doctor import run_doctor
from pmo_studio.llm.factory import build_llm
from pmo_studio.llm.provider import api_key_status
from pmo_studio.llm.reviewer import build_gate_reviewer
from pmo_studio.generators.refinement import refine_markdown_artifact

DEFAULT_LLM_PROVIDER = "auto"
DEFAULT_LLM_MODEL = "Tier2"
DEFAULT_MAX_REFINE = 2
DEFAULT_GATE_TIMEOUT = 120


def _resolve_llm_provider(provider: str | None) -> str:
    provider = provider or DEFAULT_LLM_PROVIDER
    if provider != "auto":
        return provider
    return "9router" if api_key_status().get("9router", "").startswith("set") else "noop"


@dataclass
class CommandResponse:
    text: str
    requires_approval: bool = False
    approval_token: str | None = None
    media: list[Path] | None = None

    def render(self) -> str:
        lines = [self.text.strip()]
        if self.media:
            for path in self.media:
                lines.append(f"MEDIA:{path}")
        return "\n".join(lines).strip() + "\n"


APPROVAL_COMMANDS = {"baseline", "official-quotation", "signoff"}


def handle_command(text: str, root: Path = DEFAULT_ROOT, approved: bool = False) -> str:
    return handle_command_structured(text, root=root, approved=approved).render()


def handle_command_structured(text: str, root: Path = DEFAULT_ROOT, approved: bool = False) -> CommandResponse:
    try:
        parts = shlex.split(text)
    except ValueError as exc:
        return CommandResponse(f"Không parse được command: {exc}\nDùng: /pmo help")
    if not parts or parts[0] not in {"/pmo", "pmo"}:
        return CommandResponse("Không phải PMO command. Dùng: `/pmo help`")
    if len(parts) == 1 or parts[1] == "help":
        return CommandResponse(HELP)
    cmd = parts[1]
    if cmd in APPROVAL_COMMANDS and not approved:
        return _approval_required(parts)
    try:
        if cmd == "init": return _cmd_init(parts, root)
        if cmd == "generate": return _cmd_generate(parts, root)
        if cmd in {"generate-ba", "ba"}:
            slug = _slug_arg(parts, root)
            return _cmd_generate([parts[0], "generate", slug, "ba", "--from-sources"], root)
        if cmd in {"gates", "run-gates"}: return _cmd_gates(parts, root)
        if cmd == "trace": return _cmd_trace(parts, root)
        if cmd == "status": return _cmd_status(parts, root)
        if cmd == "summary": return _cmd_summary(parts, root)
        if cmd == "list": return _cmd_list(parts, root)
        if cmd == "recent": return _cmd_recent(parts, root)
        if cmd == "sync-lifecycle": return _cmd_sync_lifecycle(parts, root)
        if cmd == "archive": return _cmd_archive(parts, root)
        if cmd == "clone": return _cmd_clone(parts, root)
        if cmd == "doctor": return _cmd_doctor(parts, root)
        if cmd == "export": return _cmd_export(parts, root)
        if cmd == "baseline": return _cmd_baseline(parts, root)
        if cmd == "benchmark": return _cmd_benchmark(parts, root)
    except Exception as exc:
        return CommandResponse(f"⚠ PMO command lỗi: `{type(exc).__name__}: {exc}`")
    return CommandResponse(f"Không hiểu command `{cmd}`. Dùng `/pmo help`")


def _cmd_init(parts: list[str], root: Path) -> CommandResponse:
    slug = _arg(parts, 2, "slug")
    customer = _opt(parts, "--customer", "TBD")
    brief = _opt(parts, "--brief", "PMO Studio project")
    products = _opts(parts, "--product") or ["eOffice"]
    sources = [Path(s) for s in _opts(parts, "--source")]
    domain_pack = _opt(parts, "--domain-pack", "bteco")
    p = Project.create(slug, customer=customer, root_base=root, domain_pack=domain_pack)
    generate_stage0(p, brief=brief, products=products, sources=sources)
    return CommandResponse(f"✓ Đã tạo PMO project `{slug}`\nPath: `{p.root}`")


def _cmd_generate(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    persona = parts[3] if len(parts) > 3 and not parts[3].startswith("--") else "all"
    from_sources = "--from-sources" in parts
    refine = "--no-refine" not in parts
    llm_name = _resolve_llm_provider(_opt(parts, "--llm", DEFAULT_LLM_PROVIDER))
    model = _opt(parts, "--model", DEFAULT_LLM_MODEL)
    p = Project.load(slug, root_base=root)
    llm = build_llm(llm_name, model)
    if persona in {"po", "all"}: generate_po(p)
    if persona in {"pm", "all"}: generate_pm(p)
    if persona in {"ba", "all"}: generate_ba_from_sources(p, llm=llm) if from_sources else generate_ba_from_sources(p)
    if persona in {"ic", "all"}: generate_ic(p)
    refined = []
    if refine:
        for stage, artifact in _refine_targets(p, persona):
            if artifact.exists():
                r = refine_markdown_artifact(artifact, stage, llm=llm, max_attempts=int(_opt(parts, "--max-refine", str(DEFAULT_MAX_REFINE))), model=model, domain_pack=p.config.domain_pack)
                refined.append(f"{stage}:{'PASS' if r.gate_b_passed else 'WARN'}")
    TraceabilityEngine(p.root).write_outputs()
    suffix = "\nRefine: " + ", ".join(refined) if refined else ""
    return CommandResponse(f"✓ Đã generate `{persona}` cho `{slug}`\nTraceability: `{p.root / 'traceability'}`{suffix}")


def _cmd_gates(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    p = Project.load(slug, root_base=root)
    llm_name = _resolve_llm_provider(_opt(parts, "--llm", DEFAULT_LLM_PROVIDER))
    model = _opt(parts, "--model", DEFAULT_LLM_MODEL)
    reviewer = build_gate_reviewer(
        llm_name,
        model,
        cache_root=_opt(parts, "--gate-cache", None),
        fallback_on_error="--no-gate-fallback" not in parts,
        timeout=int(_opt(parts, "--gate-timeout", str(DEFAULT_GATE_TIMEOUT))),
    ) if llm_name != "noop" else None
    summary = run_all_gates(p, include_c="--no-include-c" not in parts, reviewer=reviewer)
    return CommandResponse(
        f"✓ Quality gates `{slug}`\n"
        f"- Total: {summary['total']}\n- Passed: {summary['passed']}\n- Failed: {summary['failed']}\n- Skipped: {summary['skipped']}\n"
        f"Result: `{p.root / 'quality' / 'summary.json'}`"
    )


def _cmd_trace(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    p = Project.load(slug, root_base=root)
    TraceabilityEngine(p.root).write_outputs()
    result = validate_traceability(p.root)
    return CommandResponse(
        f"✓ Traceability `{slug}`: {'PASS' if result.passed else 'WARN'}\n"
        f"- Nodes: {result.node_count}\n- Edges: {result.edge_count}\n- Missing upstream: {len(result.missing_upstream)}\n- Orphan: {len(result.orphan_ids)}\n"
        f"RTM: `{p.root / 'traceability' / 'rtm.md'}`"
    )


def _cmd_status(parts: list[str], root: Path) -> CommandResponse:
    return _cmd_summary(parts, root)


def _cmd_summary(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    p = Project.load(slug, root_base=root)
    return CommandResponse(summary_markdown(summarize_project(p)))


def _cmd_list(parts: list[str], root: Path) -> CommandResponse:
    if "--refresh" in parts:
        refresh_registry(root)
    entries = list_projects(root, include_archived="--include-archived" in parts)
    if not entries:
        return CommandResponse("Chưa có PMO project nào.")
    lines = ["PMO projects:"]
    for e in entries[:10]:
        lines.append(f"- `{e.slug}` · {e.customer} · {e.lifecycle_state} · {e.current_stage} · `{e.root}`")
    return CommandResponse("\n".join(lines))


def _cmd_recent(parts: list[str], root: Path) -> CommandResponse:
    e = recent_project(root)
    if not e:
        return CommandResponse("Chưa có PMO project nào.")
    return CommandResponse(f"Recent PMO: `{e.slug}` · {e.customer} · {e.lifecycle_state} · `{e.root}`")


def _cmd_sync_lifecycle(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    p = Project.load(slug, root_base=root)
    state = sync_lifecycle(p)
    return CommandResponse(f"Lifecycle `{slug}`: {state}")


def _cmd_archive(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    if "--yes" not in parts:
        return CommandResponse("⚠ Archive cần `--yes`. Ví dụ: `/pmo archive <slug> --reason \"done\" --yes`")
    reason = _opt(parts, "--reason", "")
    p = Project.load(slug, root_base=root)
    dest = archive_project(p, reason=reason, move="--move" in parts)
    return CommandResponse(f"✓ Archived `{slug}`: `{dest}`")


def _cmd_clone(parts: list[str], root: Path) -> CommandResponse:
    source_slug = _slug_arg(parts, root)
    # syntax: /pmo clone [source] <new_slug>
    if len(parts) > 3 and not parts[2].startswith("--"):
        new_slug = parts[3]
    elif len(parts) > 2:
        new_slug = parts[2]
    else:
        raise ValueError("missing new_slug")
    source = Project.load(source_slug, root_base=root)
    cloned = clone_project(source, new_slug, customer=_opt(parts, "--customer", None))
    return CommandResponse(f"✓ Cloned `{source_slug}` → `{cloned.config.project_slug}`\nPath: `{cloned.root}`")


def _cmd_doctor(parts: list[str], root: Path) -> CommandResponse:
    project = Project.load(parts[2], root_base=root) if len(parts) > 2 and not parts[2].startswith("--") else None
    result = run_doctor(project)
    failed = [c for c in result["checks"] if not c["passed"] and c["id"] != "llm.9router_key"]
    return CommandResponse(f"Doctor: {'PASS' if result['passed'] else 'WARN'}\nFailed checks: {len(failed)}")


def _cmd_export(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    fmt = _opt(parts, "--format", "docx")
    profile = _opt(parts, "--profile", "client-ready")
    p = Project.load(slug, root_base=root)
    outs = []
    if fmt in {"html", "all"}: outs.append(export_static(p.root))
    if fmt in {"docx", "all"}: outs.append(export_docx(p.root, profile=profile))
    if fmt in {"zip", "all"}: outs.append(export_bundle(p.root, profile=profile, include_sources="--include-redacted-sources" in parts))
    return CommandResponse("✓ Exported:\n" + "\n".join(f"- `{o}`" for o in outs), media=outs if "--send" in parts else None)


def _cmd_baseline(parts: list[str], root: Path) -> CommandResponse:
    slug = _slug_arg(parts, root)
    version_idx = 3 if len(parts) > 3 and not parts[2].startswith("--") else 2
    version = _arg(parts, version_idx, "version")
    p = Project.load(slug, root_base=root)
    m = create_baseline(p.root, p.config.project_slug, version)
    return CommandResponse(f"✓ Baseline `{version}`: {m.item_count} files\nSHA256: `{m.manifest_sha256}`")


def _cmd_benchmark(parts: list[str], root: Path) -> CommandResponse:
    result = run_benchmark(root / "eval-runs", export_docx_enabled="--no-docx" not in parts)
    media = [Path(result.report_path)] if result.report_path and "--send" in parts else None
    return CommandResponse(
        f"Benchmark: {'PASS' if result.passed else 'FAIL'} score={result.score:.2%}\n"
        f"Report: `{result.report_path}`\nResults: `{result.results_path}`",
        media=media,
    )


def _approval_required(parts: list[str]) -> CommandResponse:
    cmd = parts[1]
    token = f"APPROVE_PMO_{cmd.upper()}"
    return CommandResponse(
        f"⚠ Command `{cmd}` cần human approval vì tạo baseline/sign-off/official quotation.\n"
        f"Nếu chắc chắn, chạy lại với `--approved` hoặc reply token: `{token}`.",
        requires_approval=True,
        approval_token=token,
    )


def _refine_targets(p: Project, persona: str):
    targets = []
    if persona in {"po", "all"}: targets.append(("po.vision", p.root / "artifacts" / "po" / "01-vision.md"))
    if persona in {"pm", "all"}: targets.append(("pm.charter", p.root / "artifacts" / "pm" / "01-charter.md"))
    if persona in {"ba", "all"}:
        targets.extend([
            ("ba.prd", p.root / "artifacts" / "ba" / "01-prd.md"),
            ("ba.brd", p.root / "artifacts" / "ba" / "02-brd.md"),
            ("ba.srs", p.root / "artifacts" / "ba" / "03-srs" / "srs.md"),
            ("ba.test_cases", p.root / "artifacts" / "ba" / "05-test-cases.md"),
        ])
    if persona in {"ic", "all"}:
        targets.extend([
            ("ic.deployment_plan", p.root / "artifacts" / "ic" / "03-deployment-plan.md"),
            ("ic.uat_plan", p.root / "artifacts" / "ic" / "04-uat-plan.md"),
        ])
    return targets


def _slug_arg(parts: list[str], root: Path) -> str:
    if len(parts) > 2 and not parts[2].startswith("--"):
        return parts[2]
    e = recent_project(root)
    if not e:
        raise ValueError("missing slug and no recent PMO project")
    return e.slug


def _arg(parts: list[str], idx: int, name: str) -> str:
    if len(parts) <= idx:
        raise ValueError(f"missing {name}")
    return parts[idx]


def _opt(parts: list[str], name: str, default):
    if name not in parts:
        return default
    i = parts.index(name)
    return parts[i + 1] if i + 1 < len(parts) else default


def _opts(parts: list[str], name: str) -> list[str]:
    out = []
    for i, p in enumerate(parts):
        if p == name and i + 1 < len(parts):
            out.append(parts[i + 1])
    return out


HELP = """PMO Studio commands:
- `/pmo init <slug> --customer "Tên KH" --brief "Mô tả" [--domain-pack eoffice|ky_so|hse|pms|bteco] [--source file]`
- `/pmo generate [slug] all|po|pm|ba|ic --from-sources [--no-refine] [--llm auto|noop|9router]` (default: auto + Tier2 + refine on)
- `/pmo ba [slug]` shortcut for BA from sources + refine
- `/pmo trace [slug]`
- `/pmo gates [slug] [--no-include-c] [--llm auto|noop|9router]` (default: Gate C on)
- `/pmo status [slug]`
- `/pmo summary [slug]`
- `/pmo list [--refresh] [--include-archived]`
- `/pmo recent`
- `/pmo export [slug] --format html|docx|zip|all [--send] [--include-redacted-sources]`
- `/pmo baseline [slug] v1.0 --approved` official baseline, approval required
- `/pmo benchmark [--send] [--no-docx]`
- `/pmo sync-lifecycle [slug]`
- `/pmo clone [source_slug] <new_slug> [--customer "Tên KH"]`
- `/pmo archive [slug] --reason "..." --yes [--move]`
- `/pmo doctor [slug]`
"""
