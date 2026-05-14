import json

from pmo_studio.cli import main


def test_telegram_prepare_creates_delivery_manifest(tmp_path):
    source = tmp_path / "crm.md"
    source.write_text("""
# CRM
| STT | CHỨC NĂNG | MÔ TẢ |
| 1 | Quản lý Lead | Capture, qualify, assign lead |
| 2 | Opportunity Pipeline | Stage, forecast, approval workflow |
""", encoding="utf-8")
    main([
        "--root", str(tmp_path),
        "telegram", "prepare", "crm-tg",
        "--source", str(source),
        "--customer", "Demo",
        "--product", "CRM",
        "--chat-id", "telegram:640968010",
        "--llm", "noop",
    ])
    manifest_path = tmp_path / "crm-tg/exports/customer/telegram-delivery.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["schema"] == "pmo.telegram_delivery.v1"
    assert data["chat_id"] == "telegram:640968010"
    labels = {f["label"] for f in data["files"]}
    assert "DOCX documentation pack" in labels
    assert "PDF documentation pack" in labels
    assert "Quotation workbook" in labels
    assert "Artifact manifest" in labels
