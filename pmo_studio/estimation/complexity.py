from __future__ import annotations

KEYWORDS = {
    "ai": ["ai", "gpt", "gemini", "citation", "trích dẫn", "machine learning", "llm"],
    "workflow": ["workflow", "phê duyệt", "phe duyet", "approval", "sla", "trình ký", "ký", "escalation"],
    "integration": ["api", "integration", "tích hợp", "eoffice", "pms", "erp", "hrm", "sso", "webhook"],
    "data": ["import", "migration", "đồng bộ", "dong bo", "export", "báo cáo", "dashboard", "report"],
    "security": ["rbac", "phân quyền", "audit", "security", "permission", "access denied"],
}

def signal_hits(feature: str, description: str) -> dict[str, bool]:
    text = f"{feature} {description}".lower()
    return {k: any(w in text for w in words) for k, words in KEYWORDS.items()}

def classify_complexity(feature: str, description: str) -> tuple[str, float, float, str]:
    hits = signal_hits(feature, description)
    score = 0
    reasons = []
    if hits["ai"]:
        score += 3; reasons.append("AI/citation processing")
    if hits["workflow"]:
        score += 2; reasons.append("workflow/approval")
    if hits["integration"]:
        score += 2; reasons.append("external integration")
    if hits["data"]:
        score += 1; reasons.append("data/reporting")
    if hits["security"]:
        score += 1; reasons.append("security/audit")
    if score >= 5:
        return "very_complex", 7.0, 1.25, ", ".join(reasons)
    if score >= 3:
        return "complex", 5.0, 1.15, ", ".join(reasons)
    if score >= 1:
        return "medium", 3.5, 1.05, ", ".join(reasons)
    return "simple", 2.5, 1.0, "CRUD/search baseline"
