from pmo_studio.cli import main


def test_real_pdf_export(tmp_path):
    source = tmp_path / "crm.md"
    source.write_text("""
# CRM
| STT | CHỨC NĂNG | MÔ TẢ |
| 1 | Quản lý Lead | Capture, qualify, assign lead |
| 2 | Opportunity Pipeline | Stage, forecast, approval workflow |
""", encoding="utf-8")
    main(["--root", str(tmp_path), "run-project", "crm-v15", "--source", str(source), "--customer", "Demo", "--product", "CRM", "--llm", "noop", "--profile", "customer"])
    pdf = tmp_path / "crm-v15/exports/customer/pmo-documentation-pack.pdf"
    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF")
    assert pdf.stat().st_size > 1000
