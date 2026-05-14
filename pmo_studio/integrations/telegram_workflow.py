"""Telegram-oriented workflow helpers.

This module intentionally does not send Telegram messages or store bot tokens. It
creates a project from an inbound file, runs the PMO pipeline through existing
CLI primitives, and writes a delivery manifest that an outer OpenClaw/Telegram
adapter can use to attach files safely.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class TelegramDeliveryFile:
    label: str
    path: str
    mime_hint: str
    size_bytes: int


@dataclass
class TelegramDeliveryManifest:
    schema: str
    created_at: str
    chat_id: str | None
    project_slug: str
    project_root: str
    message: str
    files: list[TelegramDeliveryFile]


def build_delivery_manifest(project_root: Path, chat_id: str | None = None) -> Path:
    slug = project_root.name
    candidates = [
        ("DOCX documentation pack", project_root / "exports/customer/pmo-documentation-pack.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("PDF documentation pack", project_root / "exports/customer/pmo-documentation-pack.pdf", "application/pdf"),
        ("Quotation workbook", project_root / "artifacts/ba/06-quotation.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("Project bundle", project_root / f"exports/customer/{slug}-pmo-bundle.zip", "application/zip"),
        ("Dashboard HTML", project_root / "exports/management/index.html", "text/html"),
        ("Artifact manifest", project_root / "artifacts/manifest.json", "application/json"),
    ]
    files = [TelegramDeliveryFile(label, str(path), mime, path.stat().st_size) for label, path, mime in candidates if path.exists()]
    manifest = TelegramDeliveryManifest(
        schema="pmo.telegram_delivery.v1",
        created_at=datetime.now(timezone.utc).isoformat(),
        chat_id=chat_id,
        project_slug=slug,
        project_root=str(project_root),
        message=f"PMO Studio project {slug} generated. Attach files individually if ZIP delivery is unreliable.",
        files=files,
    )
    out = project_root / "exports/customer/telegram-delivery.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
