from pmo_studio.domain.detector import detect_domain


def test_detects_known_domains_with_explanation():
    legal = detect_domain("LIQ LegalIQ hỏi đáp pháp lý, quản lý ủy quyền, hợp đồng, B.PCTT")
    assert legal.selected_domain == "legal_ai"
    assert legal.confidence in {"medium", "high"}
    assert "legal_ai" in legal.explanation

    asset = detect_domain("Quản lý trang thiết bị tài sản TTB, cấp phát, kiểm kê, bảo trì, thanh lý")
    assert asset.selected_domain == "asset_management"
    assert asset.score >= 0.45


def test_unknown_domain_uses_generic_fallback():
    result = detect_domain("Ứng dụng nội bộ quản lý biểu mẫu khảo sát và thư viện tri thức chuyên ngành")
    assert result.selected_domain == "generic"
    assert result.confidence == "low"
    assert "generic" in result.explanation.lower()


def test_crm_detects_without_asset_or_legal_bias():
    result = detect_domain("CRM quản lý Lead, Opportunity, Customer và Sales Pipeline forecast")
    assert result.selected_domain == "crm"
    assert result.candidates[0].domain == "crm"
