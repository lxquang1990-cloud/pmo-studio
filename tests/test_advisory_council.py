from pathlib import Path
import json

from pmo_studio.advisory.council import run_advisory_council, save_council_result
from pmo_studio.advisory.profiles import load_advisor_profiles, select_advisors


def test_load_advisor_profiles_contains_required_roles():
    profiles = load_advisor_profiles()
    ids = {p.advisor_id for p in profiles}
    assert {"architect", "security", "ba_product", "qa_test", "devops", "ux"}.issubset(ids)


def test_select_advisors_includes_qa_default():
    profiles = load_advisor_profiles()
    selected = select_advisors("Build a simple internal tool", profiles)
    ids = {p.advisor_id for p in selected}
    assert "qa_test" in ids


def test_run_advisory_council_detects_release_and_secret_conflicts():
    result = run_advisory_council(
        "Build an agent runtime with GitHub auto-merge, CI/CD, OAuth credentials, and Telegram escalation."
    )
    assert result.orchestrator == "SnailBot"
    assert "security" in result.selected_advisors
    assert "devops" in result.selected_advisors
    assert result.conflict_report.agreement_level == "hard_conflict"
    assert result.conflict_report.requires_human_escalation is True
    assert "SnailBot replaces the CEO Agent" in result.decision_brief


def test_save_council_result_writes_json_and_markdown(tmp_path: Path):
    result = run_advisory_council("Design PMO Studio advisory council with gates and benchmark.")
    paths = save_council_result(result, tmp_path)
    assert paths["json"].exists()
    assert paths["markdown"].exists()
    assert paths["latest_json"].exists()
    assert paths["latest_markdown"].exists()
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert data["orchestrator"] == "SnailBot"
    assert data["opinions"]
