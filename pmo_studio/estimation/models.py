from __future__ import annotations
from dataclasses import dataclass

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
