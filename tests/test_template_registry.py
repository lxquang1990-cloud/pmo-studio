from pathlib import Path


def test_template_registry_exists_with_versions():
    text = Path("pmo_studio/templates/registry.yaml").read_text(encoding="utf-8")
    assert "generic.ba.prd" in text
    assert "version: 1.0.0" in text
    assert "review/checklist.md" in text
