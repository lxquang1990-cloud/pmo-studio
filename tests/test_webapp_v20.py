from pathlib import Path

from pmo_studio.webapp import _slug


def test_webapp_slug_sanitizer():
    assert _slug("CRM Sales 2026!") == "crm-sales-2026"
    assert _slug("  LegalIQ  ") == "legaliq"


def test_webapp_module_imports():
    import pmo_studio.webapp as webapp
    assert hasattr(webapp, "run_web")
