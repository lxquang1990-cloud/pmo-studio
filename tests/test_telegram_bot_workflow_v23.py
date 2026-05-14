import json

from pmo_studio.integrations.telegram_workflow import ingest_inbound, load_session, run_session


def test_telegram_stateful_ingest_prompts_for_missing_metadata(tmp_path):
    src = tmp_path / "brief.md"
    src.write_text("# CRM\nLead management", encoding="utf-8")
    result = ingest_inbound(tmp_path, "telegram:1", source_path=str(src))
    assert result["state"] == "awaiting_metadata"
    assert set(result["missing"]) == {"slug", "customer", "product"}
    result = ingest_inbound(tmp_path, "telegram:1", slug="crm-tg", customer="Demo", product="CRM")
    assert result["state"] == "ready"
    session = load_session(tmp_path, "telegram:1")
    assert session.slug == "crm-tg"
    assert session.source_path == str(src)


def test_telegram_run_session_generates_manifest(tmp_path):
    src = tmp_path / "brief.md"
    src.write_text("""
# CRM
| STT | CHỨC NĂNG | MÔ TẢ |
| 1 | Lead | Capture and assign lead |
| 2 | Pipeline | Track deal stage and forecast |
""", encoding="utf-8")
    ingest_inbound(tmp_path, "telegram:1", source_path=str(src), slug="crm-tg", customer="Demo", product="CRM")
    manifest = run_session(tmp_path, "telegram:1", llm="noop", force=True)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["chat_id"] == "telegram:1"
    assert data["project_slug"] == "crm-tg"
    assert any(f["label"] == "PDF documentation pack" for f in data["files"])
    assert load_session(tmp_path, "telegram:1").state == "done"
