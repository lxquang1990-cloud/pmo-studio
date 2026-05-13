#!/usr/bin/env python3
"""Release readiness audit for PMO Studio.

This script performs non-mutating checks suitable before manual git commit/tag/push.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ok(msg: str) -> None:
    print(f"[x] {msg}")


def fail(msg: str) -> None:
    print(f"[ ] {msg}")
    raise SystemExit(1)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    init = (ROOT / "pmo_studio" / "__init__.py").read_text(encoding="utf-8")
    if f'__version__ = "{version}"' not in init:
        fail("pyproject version matches pmo_studio.__version__")
    ok(f"version consistent: {version}")

    wheel = ROOT / "dist" / f"pmo_studio-{version}-py3-none-any.whl"
    sdist = ROOT / "dist" / f"pmo_studio-{version}.tar.gz"
    if not wheel.exists() or not sdist.exists():
        fail("wheel and sdist exist")
    ok("wheel and sdist exist")

    sums_path = ROOT / "dist" / "SHA256SUMS"
    if not sums_path.exists():
        fail("dist/SHA256SUMS exists")
    recorded = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        recorded[Path(name).name] = digest
    for artifact in (wheel, sdist):
        if recorded.get(artifact.name) != sha256(artifact):
            fail(f"checksum matches {artifact.name}")
    ok("checksums match wheel/sdist")

    manifest_path = ROOT / "dist" / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    if manifest.get("version") != version:
        fail("release manifest version matches")
    ok("release manifest version matches")

    docs = [
        "docs/release.md",
        "docs/llm-gate-operations.md",
        "README.md",
        "CHANGELOG.md",
    ]
    for rel in docs:
        if not (ROOT / rel).exists():
            fail(f"{rel} exists")
    ok("release docs exist")

    try:
        subprocess.run([sys.executable, "-m", "compileall", "-q", "pmo_studio"], cwd=ROOT, check=True)
    except subprocess.CalledProcessError:
        fail("compileall passes")
    ok("compileall passes")

    print(f"RELEASE_AUDIT_PASS {version}")


if __name__ == "__main__":
    main()
