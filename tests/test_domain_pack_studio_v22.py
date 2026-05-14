import yaml

from pmo_studio.domain.manager import export_domain, import_domain, scaffold_domain, update_domain, validate_domain


def test_domain_update_export_import(tmp_path, monkeypatch):
    import pmo_studio.domain.manager as manager
    import pmo_studio.domain.pack_loader as loader
    monkeypatch.setattr(manager, "PACK_DIR", tmp_path)
    monkeypatch.setattr(loader, "PACK_DIR", tmp_path)

    scaffold_domain("banking", "Banking")
    update_domain("banking", {"keywords": "loan, deposit", "modules": ["customer onboarding"]})
    data = yaml.safe_load((tmp_path / "banking.yaml").read_text(encoding="utf-8"))
    assert "loan" in data["keywords"]
    assert "customer onboarding" in data["modules"]
    assert validate_domain("banking")["passed"] is True

    exported = export_domain("banking", tmp_path / "exports")
    assert exported.exists()
    (tmp_path / "banking.yaml").unlink()
    imported = import_domain(exported)
    assert imported.exists()
    assert validate_domain("banking")["passed"] is True
