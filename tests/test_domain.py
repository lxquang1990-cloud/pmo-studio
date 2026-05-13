"""Tests for domain intelligence module."""
from pmo_studio.domain.prompts import (
    DomainPack, get_domain, domain_products, inject_domain_prompt,
    domain_terms, domain_acronyms, domain_modules,
    DOMAIN_PACKS, DEFAULT_DOMAIN,
    EOFFICE, KY_SO, HSE, PMS,
)

# ── DomainPack dataclass ────────────────────────────────────────────────────

def test_domain_pack_defaults():
    d = DomainPack(domain_id="test", label="Test")
    assert d.domain_id == "test"
    assert d.label == "Test"
    assert d.modules == []
    assert d.roles == {}
    assert d.terms == {}

def test_domain_pack_with_data():
    d = DomainPack(
        domain_id="custom",
        label="Custom Domain",
        prd_context="PRD context",
        modules=["m1", "m2"],
        roles={"admin": "Administrator"},
        terms={"document": "tài liệu"},
        acronyms={"API": "Application Programming Interface"},
    )
    assert d.prd_context == "PRD context"
    assert len(d.modules) == 2
    assert d.roles["admin"] == "Administrator"
    assert d.terms["document"] == "tài liệu"

# ── Registry ────────────────────────────────────────────────────────────────

def test_domain_packs_has_all_four():
    assert "eoffice" in DOMAIN_PACKS
    assert "ky_so" in DOMAIN_PACKS
    assert "hse" in DOMAIN_PACKS
    assert "pms" in DOMAIN_PACKS
    assert "bteco" in DOMAIN_PACKS

def test_domain_packs_are_domain_pack_instances():
    for key in DOMAIN_PACKS:
        assert isinstance(DOMAIN_PACKS[key], DomainPack), f"{key} is not DomainPack"

def test_default_domain_is_bteco():
    assert DEFAULT_DOMAIN == "bteco"

# ── get_domain ──────────────────────────────────────────────────────────────

def test_get_domain_known():
    d = get_domain("eoffice")
    assert d.domain_id == "eoffice"
    assert d.label == "eOffice"

def test_get_domain_unknown_falls_back():
    d = get_domain("nonexistent")
    assert d.domain_id == DEFAULT_DOMAIN

def test_get_domain_ky_so():
    d = get_domain("ky_so")
    assert d.label == "Ký số"
    assert "Ký số" in d.prd_context

def test_get_domain_hse():
    d = get_domain("hse")
    assert "HSE" in d.label
    assert len(d.modules) > 0

def test_get_domain_pms():
    d = get_domain("pms")
    assert "PMS" in d.label or "Project" in d.industry

# ── Domain content ──────────────────────────────────────────────────────────

def test_eoffice_has_prompt_injections():
    assert EOFFICE.prd_context
    assert EOFFICE.brd_context
    assert EOFFICE.srs_context
    assert EOFFICE.us_context
    assert EOFFICE.test_context

def test_ky_so_has_modules():
    assert len(KY_SO.modules) >= 3
    assert "certificate" in KY_SO.modules or "signing" in KY_SO.modules

def test_hse_has_roles():
    assert len(HSE.roles) >= 3
    assert any("HSEManager" in r or "HSE" in r for r in HSE.roles)

def test_pms_has_acronyms():
    assert "WBS" in PMS.acronyms
    assert "EVM" in PMS.acronyms

# ── inject_domain_prompt ────────────────────────────────────────────────────

def test_inject_domain_prompt_prd():
    base = "Write a PRD."
    result = inject_domain_prompt("PRD", "eoffice", base)
    assert "eOffice" in result or "văn bản" in result.lower()
    assert base in result

def test_inject_domain_prompt_srs():
    base = "Write SRS."
    result = inject_domain_prompt("SRS", "ky_so", base)
    assert "Ký số" in result or "chứng thư" in result.lower()
    assert base in result

def test_inject_domain_prompt_unknown_type():
    base = "Write something."
    result = inject_domain_prompt("UNKNOWN", "eoffice", base)
    assert result == base  # no injection for unknown artifact type

def test_inject_domain_prompt_empty_context():
    base = "Write a PRD."
    result = inject_domain_prompt("PRD", "bteco", base)
    assert result == base  # bteco has empty PRD context

# ── domain_terms ────────────────────────────────────────────────────────────

def test_domain_terms_eoffice():
    terms = domain_terms("eoffice")
    assert isinstance(terms, dict)
    assert "document" in terms
    assert "công văn" in terms["document"]

def test_domain_terms_returns_dict():
    for pack_id in DOMAIN_PACKS:
        terms = domain_terms(pack_id)
        assert isinstance(terms, dict), f"{pack_id} terms is not dict"

# ── domain_acronyms ─────────────────────────────────────────────────────────

def test_domain_acronyms_hse():
    acr = domain_acronyms("hse")
    assert "CAPA" in acr
    assert "Corrective" in acr["CAPA"]

# ── domain_modules ──────────────────────────────────────────────────────────

def test_domain_modules_eoffice():
    mods = domain_modules("eoffice")
    assert isinstance(mods, list)
    assert len(mods) > 0

# ── domain_products ─────────────────────────────────────────────────────────

def test_domain_products_returns_list():
    for pack_id in DOMAIN_PACKS:
        products = domain_products(pack_id)
        assert isinstance(products, list), f"{pack_id} products is not list"
