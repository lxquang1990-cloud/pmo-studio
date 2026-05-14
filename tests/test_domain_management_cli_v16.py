from pathlib import Path

from pmo_studio.cli import main
from pmo_studio.domain.manager import validate_domain


def test_domains_validate_and_benchmark(capsys):
    main(["domains", "validate"])
    out = capsys.readouterr().out
    assert "Domains: PASS" in out
    main(["domains", "benchmark", "crm"])
    out = capsys.readouterr().out
    assert "Domain benchmark crm: PASS" in out


def test_domains_scaffold(tmp_path, monkeypatch, capsys):
    import pmo_studio.domain.manager as manager
    import pmo_studio.domain.pack_loader as loader
    monkeypatch.setattr(manager, "PACK_DIR", tmp_path)
    monkeypatch.setattr(loader, "PACK_DIR", tmp_path)
    main(["domains", "scaffold", "banking", "--label", "Banking"])
    assert (tmp_path / "banking.yaml").exists()
    result = manager.validate_domain("banking")
    assert result["passed"] is True
