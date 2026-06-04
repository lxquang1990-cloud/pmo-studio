from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import json

from .config import OracleAdapter, get_path

@dataclass(frozen=True)
class OracleMetricValue:
    metric_id: str
    label: str
    module: str
    source: str
    value: Any
    value_path: str
    filter_hint: str

@dataclass(frozen=True)
class OracleSnapshot:
    adapter_id: str
    app_name: str
    snapshot_at: str
    metrics: list[OracleMetricValue]
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "app_name": self.app_name,
            "snapshot_at": self.snapshot_at,
            "metrics": [m.__dict__ for m in self.metrics],
            "raw": self.raw,
        }


def build_snapshot_from_json(adapter: OracleAdapter, raw_data: dict[str, Any], snapshot_at: str | None = None) -> OracleSnapshot:
    values: list[OracleMetricValue] = []
    for metric in adapter.metrics:
        source_obj = get_path(raw_data, metric.source, None)
        if source_obj is None and metric.source in raw_data:
            source_obj = raw_data[metric.source]
        value = get_path(source_obj, metric.value_path, None) if source_obj is not None else None
        values.append(OracleMetricValue(
            metric_id=metric.id,
            label=metric.label,
            module=metric.module,
            source=metric.source,
            value=value,
            value_path=metric.value_path,
            filter_hint=metric.filter_hint,
        ))
    return OracleSnapshot(
        adapter_id=adapter.adapter_id,
        app_name=adapter.app_name,
        snapshot_at=snapshot_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        metrics=values,
        raw=raw_data,
    )


def write_snapshot(snapshot: OracleSnapshot, out: str | Path) -> Path:
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def load_snapshot(path: str | Path) -> OracleSnapshot:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return OracleSnapshot(
        adapter_id=data.get("adapter_id", "unknown"),
        app_name=data.get("app_name", "unknown"),
        snapshot_at=data.get("snapshot_at", ""),
        metrics=[OracleMetricValue(**m) for m in data.get("metrics", [])],
        raw=data.get("raw", {}),
    )
