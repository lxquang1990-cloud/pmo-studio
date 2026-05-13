"""Minimal local credential reference vault.

No encryption yet: this stores references only, not secret values. Values are expected to
live in environment variables or external secret files. This prevents accidental quotation
or config workbook plaintext secrets.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class VaultRef:
    key: str
    kind: str  # env|file|external
    reference: str
    description: str = ""


class Vault:
    def __init__(self, path: Path):
        self.path = path
        self.refs: dict[str, VaultRef] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.refs = {k: VaultRef(**v) for k, v in data.get("refs", {}).items()}

    def add_ref(self, key: str, kind: str, reference: str, description: str = "") -> None:
        if kind not in {"env", "file", "external"}:
            raise ValueError("kind must be env|file|external")
        self.refs[key] = VaultRef(key, kind, reference, description)
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"refs": {k: asdict(v) for k, v in self.refs.items()}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def token(self, key: str) -> str:
        if key not in self.refs:
            raise KeyError(key)
        return f"vault:{key}"
