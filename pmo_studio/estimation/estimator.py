from __future__ import annotations
from pmo_studio.estimation.extractor import extract_features
from pmo_studio.estimation.complexity import classify_complexity
from pmo_studio.estimation.models import EstimateFeature


def estimate_from_source(source_text: str) -> list[EstimateFeature]:
    estimates: list[EstimateFeature] = []
    for module, feature, desc in extract_features(source_text):
        complexity, base, risk, rationale = classify_complexity(feature, desc)
        integration_multiplier = 1.0 + (0.1 if any(k in f"{feature} {desc}".lower() for k in ["api", "tích hợp", "integration", "eoffice", "pms", "erp"]) else 0)
        final = round(base * risk * integration_multiplier, 1)
        estimates.append(EstimateFeature(module, feature, desc, complexity, base, risk, integration_multiplier, final, rationale))
    return estimates
