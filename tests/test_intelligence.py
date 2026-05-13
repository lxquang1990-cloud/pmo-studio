from pmo_studio.domain.prompts import get_domain
from pmo_studio.generators.intelligence import apply_domain_terms, build_intelligence


def test_eoffice_intelligence_adds_domain_workflows_and_negatives():
    domain = get_domain("eoffice")
    intel = build_intelligence("API approval workflow with SLA and permission", domain)
    assert any("công văn" in w.lower() or "văn bản" in w.lower() for w in intel.workflows)
    assert any("SLA" in c or "quyền" in c for c in intel.negative_cases)
    assert intel.complexity_multiplier > 1.0


def test_apply_domain_terms_replaces_generic_terms():
    domain = get_domain("eoffice")
    text = apply_domain_terms("The document workflow sends notification to user.", domain)
    assert "công văn" in text or "văn bản" in text
    assert "luồng" in text or "thông báo" in text
