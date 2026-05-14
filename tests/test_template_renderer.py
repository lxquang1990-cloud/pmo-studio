from pathlib import Path
from tempfile import TemporaryDirectory

from pmo_studio.core.project import Project, ProjectConfig
from pmo_studio.generators.source_ba import generate_ba_from_sources
from pmo_studio.templates.renderer import render_template


def test_versioned_template_renderer_replaces_metadata():
    text = render_template("ba/v1/prd.md.tmpl", {
        "template_id": "generic.ba.prd",
        "template_version": "1.0.0",
        "domain_id": "generic",
        "project_slug": "demo",
    })
    assert "template_id: generic.ba.prd" in text
    assert "template_version: 1.0.0" in text


def test_asset_and_legal_generators_use_versioned_templates():
    cases = {
        "asset": "Quản lý trang thiết bị tài sản TTB cấp phát kiểm kê bảo trì thanh lý",
        "legal": "LIQ LegalIQ hỏi đáp pháp lý quản lý ủy quyền hợp đồng B.PCTT",
    }
    with TemporaryDirectory() as td:
        for slug, source in cases.items():
            p = Project(Path(td) / slug, ProjectConfig(project_slug=slug, customer="Demo"))
            p.ensure_layout(); p.save()
            (p.root / "source/redacted/source.md").write_text(source, encoding="utf-8")
            generate_ba_from_sources(p)
            prd = (p.root / "artifacts/ba/01-prd.md").read_text(encoding="utf-8")
            assert "template_id:" in prd
            assert "template_version: 1.0.0" in prd
