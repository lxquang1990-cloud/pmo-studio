from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

@dataclass
class ProjectInfo:
    slug: str; customer: str = ""; product: str = ""; language: str = "vi"
@dataclass
class DomainInfo:
    id: str; label: str = ""; confidence: float = 0.0
@dataclass
class Role:
    id: str; name: str; description: str = ""
@dataclass
class Capability:
    id: str; name: str; description: str = ""; source_refs: list[str] = field(default_factory=list)
@dataclass
class Feature:
    id: str; capability_id: str; name: str; description: str = ""; priority: str = "Must"; complexity: str = "Medium"; source_refs: list[str] = field(default_factory=list)
@dataclass
class Requirement:
    id: str; feature_id: str; name: str; description: str; actor_roles: list[str] = field(default_factory=list); inputs: list[str] = field(default_factory=list); process: str = ""; outputs: list[str] = field(default_factory=list); business_rules: list[str] = field(default_factory=list); validation_rules: list[str] = field(default_factory=list); permission_rules: list[str] = field(default_factory=list); audit_events: list[str] = field(default_factory=list); priority: str = "Must"; source_refs: list[str] = field(default_factory=list)
@dataclass
class UserStory:
    id: str; feature_id: str; role: str; want: str; benefit: str; priority: str = "Must"; linked_requirements: list[str] = field(default_factory=list)
@dataclass
class AcceptanceCriteria:
    id: str; user_story_id: str; requirement_id: str; given: str; when: str; then: str
@dataclass
class TestCase:
    id: str; requirement_id: str; user_story_id: str; acceptance_criteria_id: str; role: str; priority: str; precondition: str; test_data: str; steps: list[str]; expected_result: str
@dataclass
class EstimateItem:
    id: str; feature_id: str; name: str; complexity: str; manday: float; rationale: str
@dataclass
class BAModel:
    schema: str; created_at: str; project: ProjectInfo; domain: DomainInfo; roles: list[Role] = field(default_factory=list); capabilities: list[Capability] = field(default_factory=list); features: list[Feature] = field(default_factory=list); requirements: list[Requirement] = field(default_factory=list); user_stories: list[UserStory] = field(default_factory=list); acceptance_criteria: list[AcceptanceCriteria] = field(default_factory=list); test_cases: list[TestCase] = field(default_factory=list); estimate_items: list[EstimateItem] = field(default_factory=list); business_rules: list[str] = field(default_factory=list); data_entities: list[str] = field(default_factory=list); permissions: list[str] = field(default_factory=list); audit_events: list[str] = field(default_factory=list); integrations: list[str] = field(default_factory=list); assumptions: list[str] = field(default_factory=list); out_of_scope: list[str] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

def now_iso() -> str: return datetime.now(timezone.utc).isoformat()
