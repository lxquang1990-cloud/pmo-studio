"""Traceability validation: orphan and broken-link reports."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pmo_studio.traceability.engine import TraceabilityEngine, TraceNode, TraceEdge

UPSTREAM_REQUIRED = {
    "BR": {"BG", "SRC"},
    "REQ": {"BR"},
    "SCR": {"REQ"},
    "API": {"REQ"},
    "WF": {"REQ"},
    "RPT": {"REQ"},
    "US": {"REQ", "SCR", "API", "WF", "RPT"},
    "AC": {"US"},
    "TC": {"AC"},
    "EST": {"US", "REQ", "SCR", "API", "WF", "RPT"},
}


@dataclass
class TraceValidationResult:
    orphan_ids: list[str]
    broken_edges: list[dict]
    missing_upstream: list[dict]
    node_count: int
    edge_count: int
    passed: bool


def validate_traceability(project_root: Path) -> TraceValidationResult:
    nodes, edges = TraceabilityEngine(project_root).scan()
    node_by_id = {n.id: n for n in nodes}
    broken = [asdict(e) for e in edges if e.source not in node_by_id or e.target not in node_by_id]
    connected = {e.source for e in edges} | {e.target for e in edges}
    orphan = sorted(n.id for n in nodes if n.id not in connected and n.type not in {"SRC", "BG", "ASM", "DEC", "RISK", "CR", "CHK", "DP", "UAT"})
    incoming: dict[str, set[str]] = {n.id: set() for n in nodes}
    outgoing: dict[str, set[str]] = {n.id: set() for n in nodes}
    for e in edges:
        if e.target in incoming and e.source in node_by_id:
            incoming[e.target].add(node_by_id[e.source].type)
        if e.source in outgoing and e.target in node_by_id:
            outgoing[e.source].add(node_by_id[e.target].type)
    missing = []
    for n in nodes:
        required_types = UPSTREAM_REQUIRED.get(n.type)
        found = incoming.get(n.id, set()) | outgoing.get(n.id, set())
        # BR can be source-backed directly when BG is absent in lightweight mode.
        if required_types and not (found & required_types):
            missing.append({"id": n.id, "type": n.type, "required_any": sorted(required_types), "found": sorted(found)})
    result = TraceValidationResult(orphan, broken, missing, len(nodes), len(edges), not broken and not missing)
    out_dir = project_root / "traceability" / "views"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation.json").write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "orphaned.md").write_text(_md_list("Orphaned IDs", orphan), encoding="utf-8")
    (out_dir / "broken-links.md").write_text(_md_dicts("Broken Links", broken), encoding="utf-8")
    (out_dir / "missing-upstream.md").write_text(_md_dicts("Missing Upstream", missing), encoding="utf-8")
    return result


def _md_list(title: str, items: list[str]) -> str:
    return f"# {title}\n\n" + ("\n".join(f"- {i}" for i in items) if items else "No issues found") + "\n"


def _md_dicts(title: str, items: list[dict]) -> str:
    lines = [f"# {title}", ""]
    if not items:
        lines.append("No issues found")
    else:
        for item in items:
            lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"
