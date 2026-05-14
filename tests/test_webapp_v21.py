import json
from pathlib import Path

from pmo_studio.core.project import Project
from pmo_studio.webapp import WebRunStatus, _download_files, _parse_multipart, _read_status, _slug, _write_source, _write_status


def test_webapp_status_roundtrip(tmp_path):
    status = WebRunStatus("pmo.web_run_status.v1", "crm-web", "running", "t1", "t2", "/tmp/source.md")
    out = _write_status(tmp_path, status)
    assert out.exists()
    data = _read_status(tmp_path, "crm-web")
    assert data["status"] == "running"
    assert data["source_path"] == "/tmp/source.md"


def test_webapp_write_source_from_text_and_upload(tmp_path):
    text_path = _write_source(tmp_path, "crm-web", "# CRM", None)
    assert text_path and text_path.name == "crm-web-source.md"
    assert text_path.read_text(encoding="utf-8") == "# CRM"
    upload_path = _write_source(tmp_path, "crm-web", "", ("brief.txt", b"hello"))
    assert upload_path and upload_path.name == "crm-web-source.txt"
    assert upload_path.read_bytes() == b"hello"


def test_webapp_download_files(tmp_path):
    p = Project.create("crm-web", customer="Demo", root_base=tmp_path, domain_pack="generic")
    expected = p.root / "exports/customer/pmo-documentation-pack.pdf"
    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.write_bytes(b"%PDF")
    files = _download_files(p.root)
    assert ("PDF documentation pack", expected) in files


def test_webapp_multipart_parser_without_cgi():
    boundary = b"abc123"
    body = b"--abc123\r\nContent-Disposition: form-data; name=\"slug\"\r\n\r\ncrm-web\r\n--abc123\r\nContent-Disposition: form-data; name=\"source_file\"; filename=\"brief.md\"\r\nContent-Type: text/markdown\r\n\r\n# Brief\r\n--abc123--\r\n"
    data, files = _parse_multipart(body, boundary)
    assert data["slug"] == "crm-web"
    assert files["source_file"] == ("brief.md", b"# Brief")


def test_webapp_slug_sanitizer_v21():
    assert _slug("CRM Sales 2026!") == "crm-sales-2026"
