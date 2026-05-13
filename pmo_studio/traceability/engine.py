"""Cross-persona traceability extraction and RTM generation."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

from openpyxl import load_workbook
from pmo_studio.core.ids import extract_ids, id_type


@dataclass(frozen=True)
class TraceNode:
    id: str
    type: str
    artifact: str
    title: str = ""


@dataclass(frozen=True)
class TraceEdge:
    source: str
    target: str
    relation: str = "links_to"


# Child -> allowed upstream parent types. Used to orient generic linked lines.
PARENT_TYPES = {
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
    "UAT": {"TC", "AC", "US"},
}


class TraceabilityEngine:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> tuple[list[TraceNode], list[TraceEdge]]:
        nodes: dict[str, TraceNode] = {}
        edge_set: set[TraceEdge] = set()
        for path in (self.project_root / "artifacts").rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            self._scan_markdown(path, text, nodes, edge_set)
        for path in (self.project_root / "artifacts").rglob("*.xlsx"):
            self._scan_excel(path, nodes, edge_set)
        return list(nodes.values()), sorted(edge_set, key=lambda e: (e.source, e.target, e.relation))

    def _scan_markdown(self, path: Path, text: str, nodes: dict[str, TraceNode], edges: set[TraceEdge]) -> None:
        rel = str(path.relative_to(self.project_root))
        current_id: str | None = None
        for line in text.splitlines():
            line_ids = extract_ids(line)
            for item in line_ids:
                title = _title_from_line(line, item)
                nodes.setdefault(item, TraceNode(item, id_type(item) or "unknown", rel, title))
            heading_id = _heading_id(line_ids, line)
            if heading_id:
                current_id = heading_id
            if _is_link_line(line):
                self._add_oriented_edges(line_ids, edges, current_id=current_id, relation=_relation_from_line(line))
            elif line.lstrip().startswith("|") and len(line_ids) >= 2:
                # Markdown tables often carry trace columns without the word "linked".
                # Example: | TC-002 | AC-001-03 | ... | should create AC-001-03 -> TC-002.
                self._add_oriented_edges(line_ids, edges, current_id=current_id, relation="table_row_link")
            elif current_id and line_ids:
                # Detail lines under a heading like "**Linked REQ:** REQ-..." often only contain the parent ID.
                for other in line_ids:
                    if other != current_id:
                        self._add_edge_by_type(current_id, other, edges, relation=_relation_from_line(line))
        # Infer AC -> US from AC numbering even if not explicitly linked.
        for item in extract_ids(text):
            if id_type(item) == "AC":
                us = f"US-{item.split('-')[1]}"
                if us in nodes:
                    edges.add(TraceEdge(us, item, "parent_of"))

    def _scan_excel(self, path: Path, nodes: dict[str, TraceNode], edges: set[TraceEdge]) -> None:
        rel = str(path.relative_to(self.project_root))
        try:
            wb = load_workbook(path, data_only=True)
        except Exception:
            return
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue
            headers = [str(v).strip() if v is not None else "" for v in rows[0]]
            for row in rows[1:]:
                values = [str(v).strip() if v is not None else "" for v in row]
                joined = " | ".join(values)
                ids = extract_ids(joined)
                for item in ids:
                    nodes.setdefault(item, TraceNode(item, id_type(item) or "unknown", rel, ws.title))
                # If row has EST ID and Work Item ID, orient EST -> work item.
                by_header = {headers[i]: values[i] for i in range(min(len(headers), len(values)))}
                est_ids = extract_ids(by_header.get("EST ID", ""))
                work_ids = extract_ids(by_header.get("Work Item ID", ""))
                for est in est_ids:
                    for wid in work_ids:
                        edges.add(TraceEdge(wid, est, "estimated_by"))
                # Generic row-level orientation for fit-gap/config-like tables.
                self._add_oriented_edges(ids, edges, relation="excel_row_link")

    def _add_oriented_edges(self, ids: list[str], edges: set[TraceEdge], current_id: str | None = None, relation: str = "links_to") -> None:
        ids = list(dict.fromkeys(ids))
        if current_id and current_id not in ids:
            ids = [current_id] + ids
        for i, left in enumerate(ids):
            for right in ids[i + 1:]:
                self._add_edge_by_type(left, right, edges, relation)

    def _add_edge_by_type(self, left: str, right: str, edges: set[TraceEdge], relation: str = "links_to") -> None:
        lt, rt = id_type(left), id_type(right)
        if lt in PARENT_TYPES and rt in PARENT_TYPES.get(lt, set()):
            edges.add(TraceEdge(right, left, relation))
        elif rt in PARENT_TYPES and lt in PARENT_TYPES.get(rt, set()):
            edges.add(TraceEdge(left, right, relation))
        else:
            edges.add(TraceEdge(left, right, relation))

    def write_outputs(self) -> None:
        nodes, edges = self.scan()
        trace_dir = self.project_root / "traceability"
        trace_dir.mkdir(parents=True, exist_ok=True)
        graph = {"version": "2.1", "nodes": [asdict(n) for n in nodes], "edges": [asdict(e) for e in edges]}
        (trace_dir / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index = {n.id: asdict(n) for n in nodes}
        (trace_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = ["# Requirements Traceability Matrix", "", "| ID | Type | Artifact | Linked IDs |", "|---|---|---|---|"]
        edge_map: dict[str, list[str]] = {}
        for e in edges:
            edge_map.setdefault(e.source, []).append(e.target)
            edge_map.setdefault(e.target, []).append(e.source)
        for n in sorted(nodes, key=lambda x: x.id):
            linked = ", ".join(sorted(set(edge_map.get(n.id, []))))
            lines.append(f"| {n.id} | {n.type} | {n.artifact} | {linked} |")
        (trace_dir / "rtm.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _is_link_line(line: str) -> bool:
    lower = line.lower()
    return any(k in lower for k in ["linked", "link", "implements", "source", "upstream", "work item", "estimate", "linked br", "linked req"])


def _relation_from_line(line: str) -> str:
    lower = line.lower()
    if "source" in lower:
        return "sourced_from"
    if "estimate" in lower:
        return "estimated_by"
    if "work item" in lower:
        return "implemented_by"
    if "linked br" in lower:
        return "implements_br"
    if "linked req" in lower:
        return "implements_req"
    return "links_to"


def _heading_id(ids: list[str], line: str) -> str | None:
    if ids and re.match(r"^\s{0,3}#{1,6}\s+", line):
        return ids[0]
    return None


def _title_from_line(line: str, item: str) -> str:
    if item not in line:
        return ""
    title = line.split(item, 1)[-1].strip(" #:.-")
    return title[:120]
