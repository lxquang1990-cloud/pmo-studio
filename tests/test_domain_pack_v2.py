from pmo_studio.domain.pack_loader import list_domain_packs, load_domain_pack
from pmo_studio.domain.rendering import build_render_context


def test_domain_packs_have_v2_knowledge_sections():
    for domain_id in list_domain_packs():
        pack = load_domain_pack(domain_id)
        assert pack.pack_version >= 2
        assert pack.workflows
        assert pack.reports
        assert pack.integrations
        assert pack.risk_factors
        assert pack.acceptance_presets


def test_render_context_uses_v2_acceptance_presets():
    ctx = build_render_context("CRM lead opportunity sales pipeline forecast", project_slug="crm-demo")
    text = "\n".join(" | ".join(row) for row in ctx.acceptance)
    assert "Lead duplicate" in text or "Opportunity forecast" in text or "Discount approval" in text
