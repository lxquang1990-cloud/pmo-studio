"""Telegram-oriented workflow helpers.

This module intentionally does not send Telegram messages or store bot tokens. It
creates a project from an inbound file, runs the PMO pipeline through existing
CLI primitives, and writes a delivery manifest that an outer OpenClaw/Telegram
adapter can use to attach files safely.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

@dataclass
class TelegramWorkflowSession:
    schema: str = "pmo.telegram_workflow_session.v1"
    chat_id: str = ""
    message_id: str | None = None
    state: str = "awaiting_source"
    source_path: str | None = None
    slug: str | None = None
    customer: str | None = None
    product: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_root: str | None = None
    delivery_manifest: str | None = None
    error: str | None = None


def session_path(root: Path, chat_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in chat_id)
    return root / "_telegram_sessions" / f"{safe}.json"


def load_session(root: Path, chat_id: str) -> TelegramWorkflowSession:
    path = session_path(root, chat_id)
    if not path.exists():
        return TelegramWorkflowSession(chat_id=chat_id)
    return TelegramWorkflowSession(**json.loads(path.read_text(encoding="utf-8")))


def save_session(root: Path, session: TelegramWorkflowSession) -> Path:
    session.updated_at = datetime.now(timezone.utc).isoformat()
    path = session_path(root, session.chat_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(session), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def ingest_inbound(root: Path, chat_id: str, *, message_id: str | None = None, source_path: str | None = None, text: str | None = None, slug: str | None = None, customer: str | None = None, product: str | None = None) -> dict[str, Any]:
    """Advance a Telegram workflow session without sending provider messages."""
    session = load_session(root, chat_id)
    session.message_id = message_id or session.message_id
    if source_path:
        session.source_path = source_path
    elif text and text.strip().startswith("#"):
        src = root / "_telegram_uploads" / f"{_slug(slug or chat_id)}-source.md"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text(text, encoding="utf-8")
        session.source_path = str(src)
    session.slug = _slug(slug or session.slug or "") or session.slug
    session.customer = customer or session.customer
    session.product = product or session.product
    missing = [name for name, value in [("source", session.source_path), ("slug", session.slug), ("customer", session.customer), ("product", session.product)] if not value]
    session.state = "ready" if not missing else "awaiting_metadata"
    save_session(root, session)
    prompt = "Ready to run PMO pipeline." if not missing else "Please provide: " + ", ".join(missing)
    return {"state": session.state, "missing": missing, "prompt": prompt, "session_path": str(session_path(root, chat_id))}


def run_session(root: Path, chat_id: str, *, llm: str = "noop", force: bool = True) -> Path:
    from pmo_studio.cli import cmd_run_project
    import argparse
    session = load_session(root, chat_id)
    missing = [name for name, value in [("source", session.source_path), ("slug", session.slug), ("customer", session.customer), ("product", session.product)] if not value]
    if missing:
        raise ValueError("Missing Telegram workflow metadata: " + ", ".join(missing))
    session.state = "running"; save_session(root, session)
    try:
        cmd_run_project(argparse.Namespace(root=str(root), slug=session.slug, source=session.source_path, customer=session.customer, product=session.product, brief="Generated from Telegram document workflow.", domain_pack="generic", profile="customer", llm=llm, model="Tier2", refine=False, max_refine=0, signoff_final=False, by="Telegram Workflow", force=force))
        project_root = root / session.slug
        manifest = build_delivery_manifest(project_root, chat_id=chat_id)
        session.state = "done"; session.project_root = str(project_root); session.delivery_manifest = str(manifest); session.error = None
        save_session(root, session)
        return manifest
    except Exception as exc:
        session.state = "error"; session.error = f"{type(exc).__name__}: {exc}"; save_session(root, session)
        raise


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.strip().lower()).strip("-")[:80]


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
