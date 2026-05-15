from pmo_studio.decomposition.generation import generate_from_decomposition


def test_v31_generates_addenda_from_decomposition(tmp_path):
    root = tmp_path / "asset-v31"
    (root / "source" / "redacted").mkdir(parents=True)
    (root / "source" / "redacted" / "brief.md").write_text("Quản lý tài sản cấp phát kiểm kê báo cáo phân quyền", encoding="utf-8")
    outputs = generate_from_decomposition(root)
    assert set(outputs) == {"brd_addendum", "srs_addendum", "user_stories", "test_cases"}
    assert (root / "artifacts" / "ba" / "02a-decomposition-addendum.md").exists()
    srs = (root / "artifacts" / "ba" / "03-srs" / "decomposition-requirements.md").read_text(encoding="utf-8")
    assert "REQ-DECOMP-001" in srs
    stories = (root / "artifacts" / "ba" / "04-us" / "US-DECOMP-001.md").read_text(encoding="utf-8")
    assert "AC-DECOMP" in stories
