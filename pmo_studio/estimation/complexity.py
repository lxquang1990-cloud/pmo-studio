from __future__ import annotations


def classify_complexity(feature: str, description: str) -> tuple[str, float, float, str]:
    text = f"{feature} {description}".lower()
    score = 0
    reasons = []
    if any(k in text for k in ["ai", "gpt", "gemini", "citation", "trích dẫn", "machine learning"]):
        score += 3; reasons.append("AI/citation processing")
    if any(k in text for k in ["workflow", "phê duyệt", "phe duyet", "approval", "sla", "trình ký", "ký"]):
        score += 2; reasons.append("workflow/approval")
    if any(k in text for k in ["api", "integration", "tích hợp", "eoffice", "pms", "erp", "hrm", "sso"]):
        score += 2; reasons.append("external integration")
    if any(k in text for k in ["import", "migration", "đồng bộ", "dong bo", "export", "báo cáo", "dashboard"]):
        score += 1; reasons.append("data/reporting")
    if any(k in text for k in ["rbac", "phân quyền", "audit", "security"]):
        score += 1; reasons.append("security/audit")
    if score >= 5:
        return "very_complex", 7.0, 1.25, ", ".join(reasons)
    if score >= 3:
        return "complex", 5.0, 1.15, ", ".join(reasons)
    if score >= 1:
        return "medium", 3.5, 1.05, ", ".join(reasons)
    return "simple", 2.5, 1.0, "CRUD/search baseline"
