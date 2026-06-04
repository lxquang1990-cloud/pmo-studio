from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

@dataclass(frozen=True)
class MetricSpec:
    id: str
    label: str
    module: str
    question_templates: list[str]
    expected_rule: str
    source: str
    value_path: str = "total"
    filter_hint: str = ""
    priority: str = "P1"
    test_type: str = "A - Dữ kiện trực tiếp"
    aliases: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class OracleAdapter:
    adapter_id: str
    app_name: str
    default_year: int | None
    metrics: list[MetricSpec]
    raw: dict[str, Any]


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML oracle adapter files")
        return yaml.safe_load(text) or {}
    return json.loads(text)


def load_adapter(path: str | Path) -> OracleAdapter:
    p = Path(path)
    data = _load_mapping(p)
    metrics: list[MetricSpec] = []
    for item in data.get("metrics", []) or []:
        metrics.append(MetricSpec(
            id=str(item["id"]),
            label=str(item.get("label") or item["id"]),
            module=str(item.get("module") or data.get("app_name") or "General"),
            question_templates=[str(q) for q in item.get("question_templates", [])],
            expected_rule=str(item.get("expected_rule") or "AI phải trả đúng số liệu oracle và nêu rõ phạm vi dữ liệu."),
            source=str(item.get("source") or item.get("endpoint") or item["id"]),
            value_path=str(item.get("value_path") or "total"),
            filter_hint=str(item.get("filter_hint") or ""),
            priority=str(item.get("priority") or "P1"),
            test_type=str(item.get("test_type") or "A - Dữ kiện trực tiếp"),
            aliases=[str(a) for a in item.get("aliases", [])],
        ))
    return OracleAdapter(
        adapter_id=str(data.get("adapter_id") or p.stem),
        app_name=str(data.get("app_name") or data.get("adapter_id") or p.stem),
        default_year=data.get("default_year"),
        metrics=metrics,
        raw=data,
    )


def get_path(obj: Any, path: str, default: Any = None) -> Any:
    cur = obj
    for part in (path or "").split("."):
        if part == "":
            continue
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur
