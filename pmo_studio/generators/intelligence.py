"""Lightweight source/domain intelligence for deterministic artifact generation.

The goal is not to replace an LLM. It gives fallback generators enough structured
context to avoid generic placeholder output when no writer model is configured.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from pmo_studio.domain.prompts import DomainPack


@dataclass
class SourceIntelligence:
    summary: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    negative_cases: list[str] = field(default_factory=list)
    complexity_multiplier: float = 1.0


def build_intelligence(source_text: str, domain: DomainPack) -> SourceIntelligence:
    text = source_text or ""
    lower = text.lower()
    intel = SourceIntelligence()
    intel.modules = _unique(domain.modules or _detect_modules(lower))[:8]
    intel.roles = _unique(list(domain.roles.values()) or _detect_roles(text))[:8]
    intel.entities = _unique(_detect_entities(text, domain))[:10]
    intel.workflows = _unique(_domain_workflows(domain) + _detect_workflows(text))[:10]
    intel.integrations = _unique(_detect_integrations(text, domain))[:8]
    intel.negative_cases = _unique(_domain_negative_cases(domain) + _detect_negative_cases(lower))[:10]
    intel.risks = _unique(_domain_risks(domain) + _detect_risks(lower))[:8]
    intel.summary = _unique(_summarize(text, domain, intel))[:10]
    intel.complexity_multiplier = _complexity_multiplier(intel)
    return intel


def apply_domain_terms(text: str, domain: DomainPack) -> str:
    """Replace generic English nouns in fallback text with domain terminology."""
    if not domain.terms:
        return text
    out = text
    for generic, specific in sorted(domain.terms.items(), key=lambda x: len(x[0]), reverse=True):
        out = re.sub(rf"\b{re.escape(generic)}\b", specific, out, flags=re.I)
    return out


def bullets(items: list[str], empty: str = "- Chưa có dữ liệu nguồn đủ rõ; cần workshop xác nhận.") -> str:
    return "\n".join(f"- {x}" for x in items) if items else empty


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = len(rows[0])
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * width) + "|"]
    for row in rows[1:]:
        safe = [str(c).replace("\n", " ") for c in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def _unique(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        item = re.sub(r"\s+", " ", str(item)).strip(" -•\t")
        key = item.lower()
        if item and key not in seen:
            seen.add(key); out.append(item)
    return out


def _summarize(text: str, domain: DomainPack, intel: SourceIntelligence) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 30 and not ln.startswith("--- SOURCE")]
    picked = lines[:5]
    if domain.brd_context:
        picked.insert(0, f"Domain context: {domain.brd_context[:260]}")
    if intel.modules:
        picked.append("Modules trọng tâm: " + ", ".join(intel.modules[:6]))
    if intel.integrations:
        picked.append("Integration points: " + ", ".join(intel.integrations[:5]))
    return picked


def _detect_modules(lower: str) -> list[str]:
    mapping = {
        "auth": ["login", "đăng nhập", "permission", "role", "phân quyền"],
        "workflow": ["workflow", "approval", "phê duyệt", "luồng"],
        "report": ["report", "dashboard", "báo cáo"],
        "document": ["document", "văn bản", "hồ sơ", "file"],
        "notification": ["notification", "email", "sms", "telegram", "thông báo"],
    }
    return [m for m, keys in mapping.items() if any(k in lower for k in keys)]


def _detect_roles(text: str) -> list[str]:
    roles = re.findall(r"(?:role|actor|persona|vai trò)[:\- ]+([^\n,;]+)", text, flags=re.I)
    return roles or ["Admin", "Business User", "Approver", "Viewer"]


def _detect_entities(text: str, domain: DomainPack) -> list[str]:
    entities = re.findall(r"\b(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,2})\b", text)
    domain_entities = [v.split("/")[0].strip() for k, v in domain.terms.items() if k in {"document", "task", "entity", "report"}]
    return domain_entities + entities


def _domain_workflows(domain: DomainPack) -> list[str]:
    if domain.domain_id == "eoffice":
        return [
            "Tiếp nhận công văn đến → đăng ký sổ văn bản → phân luồng xử lý → theo dõi SLA",
            "Chuyên viên soạn thảo hồ sơ → trình lãnh đạo phòng → ký số → phát hành văn bản đi",
            "Xin ý kiến liên phòng ban → tổng hợp phản hồi → phê duyệt cuối",
        ]
    if domain.domain_id == "ky_so":
        return ["Tạo yêu cầu ký → xác thực người ký → ký qua HSM/remote signing → lưu audit trail", "Xác thực chữ ký → kiểm tra OCSP/CRL → trả kết quả hợp lệ/không hợp lệ"]
    if domain.domain_id == "hse":
        return ["Incident report → investigation → root cause → CAPA → close-out", "Inspection → finding → corrective action → verification"]
    return []


def _detect_workflows(text: str) -> list[str]:
    flows = []
    for ln in text.splitlines():
        if "→" in ln or re.search(r"\bthen\b|\bafter\b|workflow|quy trình|luồng", ln, re.I):
            flows.append(ln.strip()[:220])
    return flows


def _detect_integrations(text: str, domain: DomainPack) -> list[str]:
    found = re.findall(r"\b(?:API|SSO|LDAP|AD|OAuth|SAML|Webhook|Email|SMS|HSM|PKI|ERP|DMS|CRM|HRM)\b", text, flags=re.I)
    if domain.domain_id == "eoffice":
        found += ["LDAP/SSO", "Digital Signature", "Email notification", "Document storage/DMS"]
    if domain.domain_id == "ky_so":
        found += ["HSM", "PKI", "OCSP/CRL", "Timestamp Authority"]
    return found


def _domain_negative_cases(domain: DomainPack) -> list[str]:
    if domain.domain_id == "eoffice":
        return ["Người không có quyền truy cập hồ sơ công việc", "Văn bản quá hạn SLA", "Ký số thất bại hoặc chứng thư hết hạn", "Trùng số văn bản khi phát hành đồng thời"]
    if domain.domain_id == "ky_so":
        return ["Chứng thư bị thu hồi", "Tài liệu bị sửa sau khi ký", "HSM timeout", "OCSP không phản hồi"]
    if domain.domain_id == "hse":
        return ["CAPA quá hạn", "Incident thiếu bằng chứng", "User đóng sự cố khi chưa verify corrective action"]
    return ["Input thiếu trường bắt buộc", "User không đủ quyền", "Integration timeout", "Concurrent update conflict"]


def _detect_negative_cases(lower: str) -> list[str]:
    out = []
    if "permission" in lower or "phân quyền" in lower: out.append("User không đủ quyền thực hiện thao tác")
    if "sla" in lower or "deadline" in lower: out.append("Quá hạn SLA/deadline cần cảnh báo và escalation")
    if "api" in lower: out.append("API trả lỗi 4xx/5xx hoặc timeout")
    return out


def _domain_risks(domain: DomainPack) -> list[str]:
    common = ["Sai lệch nghiệp vụ nếu chưa workshop với key users", "Thiếu dữ liệu mẫu làm giảm độ chính xác estimate"]
    if domain.domain_id == "eoffice":
        return ["Phân quyền theo phòng ban/chức danh phức tạp", "Luồng ký và phát hành khác nhau giữa đơn vị", "Tuân thủ lưu trữ văn bản hành chính"] + common
    if domain.domain_id == "ky_so":
        return ["Yêu cầu tuân thủ PKI/HSM cao", "Phụ thuộc CA/TSA/OCSP bên thứ ba"] + common
    return common


def _detect_risks(lower: str) -> list[str]:
    risks = []
    if "migration" in lower or "import" in lower: risks.append("Data migration/import cần mapping và kiểm thử đối soát")
    if "integration" in lower or "api" in lower: risks.append("Integration contract chưa ổn định có thể ảnh hưởng timeline")
    return risks


def _complexity_multiplier(intel: SourceIntelligence) -> float:
    score = 1.0
    score += min(len(intel.integrations), 5) * 0.05
    score += min(len(intel.workflows), 5) * 0.04
    score += 0.1 if len(intel.roles) >= 4 else 0
    score += 0.1 if any("ký" in x.lower() or "hsm" in x.lower() or "sla" in x.lower() for x in intel.integrations + intel.workflows) else 0
    return round(min(score, 1.6), 2)
