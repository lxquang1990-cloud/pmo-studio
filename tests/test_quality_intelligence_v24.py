import json

from pmo_studio.core.project import Project
from pmo_studio.quality.intelligence import analyze_project_quality, write_quality_intelligence


def test_quality_intelligence_detects_missing_traceability_and_template_token(tmp_path):
    p = Project.create("crm-qi", customer="Demo", root_base=tmp_path, domain_pack="generic")
    src = p.root / "source/redacted/source.md"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("# CRM Lead Pipeline\nLead capture and opportunity forecast", encoding="utf-8")
    art = p.root / "artifacts/ba/03-srs/srs.md"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("# SRS\n{{unrendered}}\nREQ-CRM-001\nREQ-CRM-001", encoding="utf-8")
    report = analyze_project_quality(p.root)
    ids = {f.id for f in report.findings}
    assert "QI-TRACE-001" in ids
    assert "QI-TEMPLATE-001" in ids
    assert "QI-ID-001" in ids
    out = write_quality_intelligence(p.root)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == "pmo.quality_intelligence.v1"
    assert (p.root / "quality/intelligence.md").exists()
