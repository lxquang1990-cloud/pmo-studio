from pmo_studio.decomposition.review import write_decomposition_review, run_decomposition_review


def test_v32_decomposition_review_outputs_questions(tmp_path):
    root = tmp_path / "asset-v32"
    (root / "source" / "redacted").mkdir(parents=True)
    (root / "source" / "redacted" / "brief.md").write_text("Quản lý tài sản cấp phát kiểm kê báo cáo phân quyền", encoding="utf-8")
    out = write_decomposition_review(root)
    assert out.exists()
    assert (root / "quality" / "decomposition-review.md").exists()
    assert (root / "quality" / "decomposition-review.html").exists()
    report = run_decomposition_review(root)
    assert report.schema == "pmo.decomposition_review.v1"
    assert report.questions
    assert report.readiness in {"READY_FOR_CUSTOMER_REVIEW", "NEEDS_BA_REVIEW", "NOT_READY"}
