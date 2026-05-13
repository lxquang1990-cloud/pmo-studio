""".pmo-studioignore support."""
from __future__ import annotations

import fnmatch
from pathlib import Path

DEFAULT_PATTERNS = [
    "*.key", "*.pem", "*.p12", "*.pfx", "*.env", ".env*", "secrets.*",
    "id_rsa", "id_ed25519", "*.sqlite", "*.db",
]


def load_ignore_patterns(config_dir: Path | None = None, project_root: Path | None = None) -> list[str]:
    patterns = list(DEFAULT_PATTERNS)
    candidates = []
    if config_dir:
        candidates.append(config_dir / ".pmo-studioignore")
    if project_root:
        candidates.append(project_root / ".pmo-studioignore")
    for path in candidates:
        if path.exists():
            patterns.extend([line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")])
    return patterns


def is_ignored(path: Path, patterns: list[str]) -> bool:
    name = path.name
    as_posix = path.as_posix()
    return any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(as_posix, p) for p in patterns)


def write_default_ignore(project_root: Path) -> Path:
    path = project_root / ".pmo-studioignore"
    if not path.exists():
        path.write_text("\n".join(DEFAULT_PATTERNS) + "\n", encoding="utf-8")
    return path
