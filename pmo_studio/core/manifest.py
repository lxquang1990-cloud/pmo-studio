"""Baseline manifest and checksum governance."""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List


@dataclass
class ManifestItem:
    path: str
    sha256: str
    size_bytes: int


@dataclass
class BaselineManifest:
    version: str
    created_at: str
    project_slug: str
    item_count: int
    items: List[ManifestItem]
    manifest_sha256: str = ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_baseline_files(project_root: Path) -> Iterable[Path]:
    include_roots = [project_root / "artifacts", project_root / "traceability", project_root / "quality"]
    for root in include_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not path.name.endswith(".tmp"):
                yield path


def create_baseline(project_root: Path, project_slug: str, version: str, copy_artifacts: bool = True) -> BaselineManifest:
    baseline_dir = project_root / "baselines" / version
    baseline_dir.mkdir(parents=True, exist_ok=True)
    items: list[ManifestItem] = []
    for path in sorted(iter_baseline_files(project_root)):
        rel = path.relative_to(project_root).as_posix()
        items.append(ManifestItem(rel, sha256_file(path), path.stat().st_size))
        if copy_artifacts:
            dest = baseline_dir / "artifacts" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    manifest = BaselineManifest(
        version=version,
        created_at=datetime.now(timezone.utc).isoformat(),
        project_slug=project_slug,
        item_count=len(items),
        items=items,
    )
    raw = json.dumps({k: v for k, v in asdict(manifest).items() if k != "manifest_sha256"}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    manifest.manifest_sha256 = hashlib.sha256(raw).hexdigest()
    (baseline_dir / "manifest.json").write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_manifest(project_root: Path, version: str) -> BaselineManifest:
    data = json.loads((project_root / "baselines" / version / "manifest.json").read_text(encoding="utf-8"))
    data["items"] = [ManifestItem(**i) for i in data["items"]]
    return BaselineManifest(**data)


def diff_against_baseline(project_root: Path, version: str) -> dict:
    old = {i.path: i for i in load_manifest(project_root, version).items}
    current = {}
    for path in iter_baseline_files(project_root):
        rel = path.relative_to(project_root).as_posix()
        current[rel] = ManifestItem(rel, sha256_file(path), path.stat().st_size)
    added = sorted(set(current) - set(old))
    removed = sorted(set(old) - set(current))
    modified = sorted(p for p in set(current) & set(old) if current[p].sha256 != old[p].sha256)
    unchanged = sorted(p for p in set(current) & set(old) if current[p].sha256 == old[p].sha256)
    return {"baseline": version, "added": added, "removed": removed, "modified": modified, "unchanged_count": len(unchanged)}
