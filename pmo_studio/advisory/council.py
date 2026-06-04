"""Offline advisory council runner.

SnailBot replaces the CEO Agent: it owns final decisions and escalation. This
module only structures advisor opinions, detects conflicts, and emits an artifact
pack that SnailBot can review or feed into PMO Studio generation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re

from .profiles import AdvisorProfile, load_advisor_profiles, select_advisors

RISK_WORDS = {
    "credential", "secret", "token", "password", "payment", "money", "production",
    "delete", "destructive", "personal data", "pii", "security", "auth", "oauth",
}


@dataclass
class AdvisorOpinion:
    advisor_id: str
    label: str
    position: str
    recommendation: str
    risks: list[str]
    assumptions: list[str]
    confidence: str
    must_discuss: list[str]


@dataclass
class ConflictReport:
    agreement_level: str
    conflict_topics: list[str]
    requires_discussion_round: bool
    requires_human_escalation: bool
    rationale: str


@dataclass
class CouncilResult:
    council_id: str
    created_at: str
    orchestrator: str
    request_summary: str
    selected_advisors: list[str]
    opinions: list[AdvisorOpinion]
    conflict_report: ConflictReport
    decision_brief: str


def summarize_request(text: str, limit: int = 220) -> str:
    clean = " ".join(text.split())
    return clean[:limit] + ("..." if len(clean) > limit else "")


def _confidence_for(profile: AdvisorProfile, request_text: str) -> str:
    text = request_text.lower()
    hits = sum(1 for t in profile.triggers if t and t in text)
    if hits >= 3:
        return "high"
    if hits >= 1:
        return "medium"
    return "low"


def _risks_for(profile: AdvisorProfile, request_text: str) -> list[str]:
    text = request_text.lower()
    risks: list[str] = []
    if profile.advisor_id == "security" or any(w in text for w in RISK_WORDS):
        risks.append("Validate secrets, credentials, authorization, and data exposure before implementation.")
    if profile.advisor_id == "architect":
        risks.append("Avoid premature distributed runtime; start with schemas, artifacts, gates, and dry-run workflows.")
    if profile.advisor_id == "ba_product":
        risks.append("Clarify business goal, target users, acceptance criteria, and non-goals before building runtime automation.")
    if profile.advisor_id == "qa_test":
        risks.append("Define pass/fail gates and benchmark fixtures before agent execution is trusted.")
    if profile.advisor_id == "devops":
        risks.append("Separate auto-merge levels; require approval for production, credentials, money, or user-data changes.")
    if profile.advisor_id == "ux":
        risks.append("Do not optimize UI before workflow, status visibility, and human escalation paths are validated.")
    return risks or ["No critical risk identified by this advisor in offline mode."]


def make_offline_opinion(profile: AdvisorProfile, request_text: str) -> AdvisorOpinion:
    """Create a deterministic advisor opinion without calling an LLM."""

    summary = summarize_request(request_text, 140)
    focus = "; ".join(profile.output_focus[:3]) or "decision quality"
    return AdvisorOpinion(
        advisor_id=profile.advisor_id,
        label=profile.label,
        position=f"From {profile.label}: evaluate '{summary}' through {focus}.",
        recommendation=profile.stance,
        risks=_risks_for(profile, request_text),
        assumptions=[
            "SnailBot is the CEO/portfolio orchestrator and keeps final decision authority.",
            "This council run is advisory-only and does not execute code, create repositories, or call external systems.",
        ],
        confidence=_confidence_for(profile, request_text),
        must_discuss=[r for r in _risks_for(profile, request_text) if any(w in r.lower() for w in ["credential", "approval", "runtime", "business"])]
    )


def detect_conflicts(opinions: list[AdvisorOpinion], request_text: str) -> ConflictReport:
    """Detect conflicts with transparent heuristics suitable for a first gate."""

    topics: set[str] = set()
    text = request_text.lower()
    if any(word in text for word in ["auto-merge", "full ci/cd", "production", "release"]):
        topics.add("release-autonomy-policy")
    if any(word in text for word in ["credential", "secret", "token", "password", "oauth"]):
        topics.add("secret-handling")
    if any(word in text for word in ["runtime", "agent", "spawn", "message bus", "teamlead"]):
        topics.add("runtime-complexity")
    if len({op.confidence for op in opinions}) > 1:
        topics.add("advisor-confidence-variance")

    hard_topics = {"secret-handling", "release-autonomy-policy"} & topics
    level = "hard_conflict" if hard_topics else ("soft_conflict" if topics else "consensus")
    return ConflictReport(
        agreement_level=level,
        conflict_topics=sorted(topics),
        requires_discussion_round=level != "consensus",
        requires_human_escalation=bool(hard_topics),
        rationale=(
            "Potential safety/business-policy conflict requires SnailBot/human decision."
            if hard_topics else
            "Advisors can proceed after a bounded discussion round."
            if topics else
            "No material conflict detected in first-pass offline analysis."
        ),
    )


def render_decision_brief(request_text: str, opinions: list[AdvisorOpinion], conflict: ConflictReport) -> str:
    lines = [
        "# Advisory Council Decision Brief",
        "",
        "## Request Summary",
        "",
        summarize_request(request_text, 600),
        "",
        "## Orchestrator",
        "",
        "SnailBot replaces the CEO Agent. SnailBot owns final decision authority, escalation, and execution gating.",
        "",
        "## Advisor Opinions",
        "",
    ]
    for op in opinions:
        lines.extend([
            f"### {op.label} (`{op.advisor_id}`)",
            "",
            f"- Confidence: `{op.confidence}`",
            f"- Position: {op.position}",
            f"- Recommendation: {op.recommendation}",
            "- Risks:",
            *[f"  - {risk}" for risk in op.risks],
            "- Assumptions:",
            *[f"  - {a}" for a in op.assumptions],
            "",
        ])
    lines.extend([
        "## Conflict Report",
        "",
        f"- Agreement level: `{conflict.agreement_level}`",
        f"- Requires discussion round: `{conflict.requires_discussion_round}`",
        f"- Requires human escalation: `{conflict.requires_human_escalation}`",
        f"- Topics: {', '.join(conflict.conflict_topics) if conflict.conflict_topics else 'none'}",
        f"- Rationale: {conflict.rationale}",
        "",
        "## SnailBot Decision Gate",
        "",
        "Before implementation, SnailBot should decide:",
        "",
        "1. Is the request still conceptual, or ready for implementation planning?",
        "2. Which artifacts must PMO Studio generate first?",
        "3. Which gates block runtime execution?",
        "4. Does any topic require Snail/human approval before proceeding?",
        "",
    ])
    return "\n".join(lines)


def council_id_from_text(request_text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", request_text.lower()).strip("-")[:40] or "request"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"council-{stamp}-{slug}"


def run_advisory_council(request_text: str, max_advisors: int = 5) -> CouncilResult:
    profiles = load_advisor_profiles()
    selected = select_advisors(request_text, profiles, max_advisors=max_advisors)
    opinions = [make_offline_opinion(profile, request_text) for profile in selected]
    conflict = detect_conflicts(opinions, request_text)
    return CouncilResult(
        council_id=council_id_from_text(request_text),
        created_at=datetime.now(timezone.utc).isoformat(),
        orchestrator="SnailBot",
        request_summary=summarize_request(request_text),
        selected_advisors=[p.advisor_id for p in selected],
        opinions=opinions,
        conflict_report=conflict,
        decision_brief=render_decision_brief(request_text, opinions, conflict),
    )


def save_council_result(result: CouncilResult, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = asdict(result)
    json_path = out_dir / f"{result.council_id}.json"
    md_path = out_dir / f"{result.council_id}.md"
    latest_json = out_dir / "latest.json"
    latest_md = out_dir / "latest.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(result.decision_brief, encoding="utf-8")
    latest_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest_md.write_text(result.decision_brief, encoding="utf-8")
    return {"json": json_path, "markdown": md_path, "latest_json": latest_json, "latest_markdown": latest_md}
