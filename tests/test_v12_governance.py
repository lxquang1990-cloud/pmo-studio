import json
from pathlib import Path

from pmo_studio.cli import main
from pmo_studio.templates.governance import validate_templates


def test_templates_validate():
    result = validate_templates()
    assert result["passed"] is True
    assert len(result["templates"]) >= 5


def test_run_project_writes_manifest(tmp_path):
    source = tmp_path / "crm.md"
    source.write_text("""
# CRM
| STT | CHỨC NĂNG | MÔ TẢ |
| 1 | Quản lý Lead | Capture lead, assign sales |
| 2 | Opportunity Pipeline | stage, forecast, dashboard export |
""", encoding="utf-8")
    main([
        "--root", str(tmp_path),
        "run-project", "crm-v12",
        "--source", str(source),
        "--customer", "Demo",
        "--product", "CRM",
        "--llm", "noop",
        "--profile", "customer",
    ])
    root = tmp_path / "crm-v12"
    manifest = json.loads((root / "artifacts/manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "pmo.artifact_manifest.v1"
    assert manifest["source_hash"]
    assert manifest["template_tree_hash"]
    assert manifest["domain_pack_hash"]
    assert len(manifest["artifacts"]) > 10
    quality = json.loads((root / "quality/summary.json").read_text(encoding="utf-8"))
    trace = json.loads((root / "traceability/views/validation.json").read_text(encoding="utf-8"))
    assert quality["failed"] == 0
    assert trace["passed"] is True
