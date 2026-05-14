from pmo_studio.domain.pack_loader import list_domain_packs, load_domain_pack, resolve_domain_pack


def test_loads_yaml_domain_packs():
    packs = list_domain_packs()
    assert "generic" in packs
    assert "asset_management" in packs
    legal = load_domain_pack("legal_ai")
    assert legal.id == "legal_ai"
    assert "hợp đồng" in legal.keywords
    assert legal.quotation_defaults["manday_rate_vnd"] == 3900000


def test_resolves_pack_from_source_with_detector_result():
    pack, result = resolve_domain_pack("LegalIQ pháp lý ủy quyền hợp đồng B.PCTT")
    assert pack.id == "legal_ai"
    assert result.selected_domain == "legal_ai"

    pack, result = resolve_domain_pack("A strange internal knowledge app with no clear industry")
    assert pack.id == "generic"
    assert result.selected_domain == "generic"
