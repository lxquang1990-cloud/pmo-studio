"""Small file-backed cache for LLM gate reviews."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class LLMReviewCache:
    """Deterministic JSON cache keyed by prompt inputs.

    This is intentionally simple and dependency-free. Values are JSON objects returned by
    reviewers. Cache misses/failures never block review execution.
    """

    def __init__(self, root: Path | str | None = None, namespace: str = "gate-review") -> None:
        base = Path(root) if root else Path.home() / ".cache" / "pmo-studio" / namespace
        self.root = base
        self.root.mkdir(parents=True, exist_ok=True)

    def key_for(self, *, provider: str, model: str | None, stage: str, layer: str, artifact: str, rubric: list[dict], context: str = "") -> str:
        payload = {
            "provider": provider,
            "model": model or "default",
            "stage": stage,
            "layer": layer,
            "artifact_sha256": hashlib.sha256(artifact.encode("utf-8", errors="ignore")).hexdigest(),
            "context_sha256": hashlib.sha256(context.encode("utf-8", errors="ignore")).hexdigest(),
            "rubric": rubric,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.root / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("value")
        except Exception:
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        path = self.root / f"{key}.json"
        tmp = path.with_suffix(".tmp")
        payload = {"created_at": time.time(), "value": value}
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
