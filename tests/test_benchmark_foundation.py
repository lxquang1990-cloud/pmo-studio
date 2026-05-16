import json
from pathlib import Path

from pmo_studio.eval.runner import EvalCase, run_benchmark


def test_real_world_benchmark_fixture_is_well_formed():
    root = Path("evals/real-world/legal-ai-customer-style")
    source = root / "source.md"
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))
    rubric = (root / "review-rubric.md").read_text(encoding="utf-8")

    assert source.exists()
    text = source.read_text(encoding="utf-8")
    for module in expected["expected_modules"]:
        assert module in text
    for excluded in expected["out_of_scope"]:
        assert excluded in text
    assert expected["human_review_required"] is True
    assert "Minimum customer-ready bar" in rubric


def test_real_world_benchmark_case_runs_offline(tmp_path):
    fixture_root = Path("evals/real-world/legal-ai-customer-style")
    expected = json.loads((fixture_root / "expected.json").read_text(encoding="utf-8"))
    case = EvalCase(
        name="Legal AI Customer-Style Fixture",
        slug="bench-legal-ai-customer-style",
        customer="Legal AI Demo",
        products=["Legal AI"],
        brief="Validate customer-style Legal AI documentation package.",
        source=(fixture_root / "source.md").read_text(encoding="utf-8"),
        expected_id_types={"SRC", "BR", "REQ", "SCR", "API", "WF", "US", "AC", "TC", "EST"},
        min_trace_edges=20,
        expected_manday_min=expected["expected_manday_min"],
        expected_manday_max=expected["expected_manday_max"],
    )
    result = run_benchmark(tmp_path, cases=[case], export_docx_enabled=False, llm_provider="noop")
    assert result.report_path
    assert result.results_path
    assert result.case_results[0].details["redacted_ok"] is True
    assert result.case_results[0].details["trace_edges"] >= 20
    assert result.case_results[0].details["quotation_sane"] is True
