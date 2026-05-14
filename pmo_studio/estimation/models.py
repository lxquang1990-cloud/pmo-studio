from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class WorkItemEstimate:
    work_item_type: str  # screen|api|workflow|report|data|security
    work_item_id: str
    name: str
    complexity: str
    role_effort: dict[str, float]
    risk_multiplier: float
    integration_multiplier: float
    final_manday: float
    rationale: str

@dataclass
class EstimateFeature:
    module: str
    feature: str
    description: str
    complexity: str
    base_manday: float
    risk_multiplier: float
    integration_multiplier: float
    final_manday: float
    rationale: str
    work_items: list[WorkItemEstimate] = field(default_factory=list)
    risk_buffers: dict[str, float] = field(default_factory=dict)

@dataclass
class EstimatePackage:
    features: list[EstimateFeature]
    role_totals: dict[str, float]
    risk_buffers: dict[str, float]
    total_manday: float
