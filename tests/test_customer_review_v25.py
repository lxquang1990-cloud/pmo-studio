import json

from pmo_studio.core.project import Project
from pmo_studio.quality.customer_review import run_customer_review, write_customer_review


def test_customer_review_detects_customer_readiness_findings(tmp_path):
    p = Project.create("crm-review", customer="Demo", root_base=tmp_path, domain_pack="generic")
    prd = p.root / "artifacts/ba/01-prd.md"
    prd.parent.mkdir(parents=True, exist_ok=True)
    prd.write_text("# PRD\nTBD\n{{token}}\n", encoding="utf-8")
    report = run_customer_review(p.root)
    assert report.readiness in {"NEEDS_REVIEW", "NOT_READY"}
    ids = {f.id for artifact in report.artifacts for f in artifact.findings}
    assert "CR-PRD-PLACEHOLDER" in ids
    assert "CR-PRD-TEMPLATE" in ids
    assert "CR-BRD-MISSING" in ids
    assert any(item["artifact_key"] == "prd" for item in report.suggested_regenerations)


def test_customer_review_writes_json_markdown_html(tmp_path):
    p = Project.create("crm-review", customer="Demo", root_base=tmp_path, domain_pack="generic")
    out = write_customer_review(p.root)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == "pmo.customer_review.v1"
    assert (p.root / "quality/customer-review.md").exists()
    assert (p.root / "quality/customer-review.html").exists()
