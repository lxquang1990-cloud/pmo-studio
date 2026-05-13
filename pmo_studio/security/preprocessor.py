"""Security pre-processing: hashing, redaction, injection flagging."""
from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

SECRET_PATTERNS = [
    ("api_key", re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^\s'\"]+")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone_vn", re.compile(r"(?<!\d)(?:\+?84|0)(?:\d[\s.-]?){8,10}\d(?!\d)")),
]
INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore (all )?(previous|prior|above) instructions"),
    re.compile(r"(?i)system prompt"),
    re.compile(r"(?i)developer message"),
    re.compile(r"(?i)you are now"),
    re.compile(r"(?i)exfiltrate|leak|send.*secret"),
]


@dataclass
class SourceScanResult:
    source_id: str
    original_path: str
    redacted_path: str
    sha256: str
    redaction_applied: bool
    redaction_count: int
    injection_detected: bool
    injection_hits: List[str]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def redact_text(text: str) -> tuple[str, int]:
    count = 0
    redacted = text
    for name, pattern in SECRET_PATTERNS:
        redacted, n = pattern.subn(f"[REDACTED:{name.upper()}]", redacted)
        count += n
    return redacted, count


def detect_injection(text: str) -> list[str]:
    hits = []
    for pattern in INJECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            hits.append(m.group(0)[:120])
    return hits


def process_source(source_id: str, input_path: Path, project_root: Path) -> SourceScanResult:
    uploads = project_root / "source" / "uploads"
    redacted_dir = project_root / "source" / "redacted"
    uploads.mkdir(parents=True, exist_ok=True)
    redacted_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads / f"{source_id}-{input_path.name}"
    if input_path.resolve() != dest.resolve():
        shutil.copy2(input_path, dest)
    digest = sha256_file(dest)
    try:
        text = dest.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Binary files are copied as-is for now; future DOCX/PDF extractors should feed text into this layer.
        redacted_dest = redacted_dir / dest.name
        shutil.copy2(dest, redacted_dest)
        return SourceScanResult(source_id, str(dest), str(redacted_dest), digest, False, 0, False, [])
    hits = detect_injection(text)
    redacted, count = redact_text(text)
    redacted_dest = redacted_dir / dest.name
    redacted_dest.write_text(redacted, encoding="utf-8")
    return SourceScanResult(source_id, str(dest), str(redacted_dest), digest, count > 0, count, bool(hits), hits)
