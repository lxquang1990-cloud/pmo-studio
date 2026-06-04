"""Advisor profile loading and task-based selection."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

PROFILE_DIR = Path(__file__).with_suffix("").parent / "profiles"


@dataclass(frozen=True)
class AdvisorProfile:
    """A deterministic advisor profile used by SnailBot's advisory council."""

    advisor_id: str
    label: str
    expertise: list[str]
    stance: str
    output_focus: list[str]
    triggers: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "AdvisorProfile":
        return cls(
            advisor_id=str(data["advisor_id"]),
            label=str(data["label"]),
            expertise=[str(x) for x in data.get("expertise", [])],
            stance=str(data.get("stance", "Provide a balanced evidence-backed opinion.")),
            output_focus=[str(x) for x in data.get("output_focus", [])],
            triggers=[str(x).lower() for x in data.get("triggers", [])],
        )


def load_advisor_profiles(profile_dir: Path | None = None) -> list[AdvisorProfile]:
    """Load advisor profiles from JSON files in deterministic order."""

    directory = profile_dir or PROFILE_DIR
    profiles = []
    for path in sorted(directory.glob("*.json")):
        profiles.append(AdvisorProfile.from_dict(json.loads(path.read_text(encoding="utf-8"))))
    if not profiles:
        raise ValueError(f"No advisor profiles found in {directory}")
    return profiles


def select_advisors(request_text: str, profiles: list[AdvisorProfile], max_advisors: int = 5) -> list[AdvisorProfile]:
    """Select advisors by trigger matches, with a safe default council.

    This is intentionally deterministic/offline. SnailBot is the CEO/orchestrator;
    this function only proposes the council composition.
    """

    text = request_text.lower()
    scored: list[tuple[int, str, AdvisorProfile]] = []
    for profile in profiles:
        score = sum(1 for trigger in profile.triggers if trigger and trigger in text)
        scored.append((score, profile.advisor_id, profile))
    selected = [profile for score, _, profile in sorted(scored, key=lambda x: (-x[0], x[1])) if score > 0]
    if not selected:
        default_ids = {"architect", "ba_product", "qa_test"}
        selected = [p for p in profiles if p.advisor_id in default_ids]
    if not any(p.advisor_id == "qa_test" for p in selected):
        selected.append(next(p for p in profiles if p.advisor_id == "qa_test"))
    return selected[:max_advisors]
