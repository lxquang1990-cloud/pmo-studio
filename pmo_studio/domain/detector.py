"""Deterministic domain detection with scoring and explanation."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class DomainCandidate:
    domain: str
    score: float
    matched_keywords: list[str] = field(default_factory=list)
    matched_modules: list[str] = field(default_factory=list)
    matched_roles: list[str] = field(default_factory=list)


@dataclass
class DomainDetectionResult:
    selected_domain: str
    score: float
    confidence: str
    candidates: list[DomainCandidate]
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


def _load_profiles() -> dict:
    try:
        from pmo_studio.domain.pack_loader import list_domain_packs, load_domain_pack
        profiles = {}
        for pack_id in list_domain_packs():
            pack = load_domain_pack(pack_id)
            if pack.id == "generic":
                continue
            profiles[pack.id] = {
                "keywords": pack.keywords,
                "modules": pack.modules,
                "roles": list(pack.roles.values()) + list(pack.roles.keys()),
            }
        if profiles:
            return profiles
    except Exception:
        pass
    return DOMAIN_PROFILES


DOMAIN_PROFILES = {
    "asset_management": {
        "keywords": ["tài sản", "tai san", "ttb", "trang thiết bị", "cap phat", "cấp phát", "kiểm kê", "kiem ke", "thanh lý", "bao tri", "bảo trì"],
        "modules": ["danh mục tài sản", "hồ sơ tài sản", "cấp phát", "thu hồi", "điều chuyển", "kiểm kê", "bảo trì", "thanh lý"],
        "roles": ["asset manager", "employee", "accounting"],
    },
    "legal_ai": {
        "keywords": ["legaliq", "pháp lý", "phap ly", "ủy quyền", "uy quyen", "hợp đồng", "hop dong", "b.pctt", "thẩm định", "tham dinh"],
        "modules": ["hỏi đáp pháp lý", "faq", "ai trả lời", "ủy quyền", "hợp đồng", "thẩm định"],
        "roles": ["legal officer", "b.pctt", "approver", "văn thư"],
    },
    "eoffice": {
        "keywords": ["eoffice", "văn bản", "van ban", "công văn", "cong van", "trình ký", "trinh ky", "phát hành văn bản"],
        "modules": ["văn bản đến", "văn bản đi", "hồ sơ công việc", "trình ký", "phát hành"],
        "roles": ["văn thư", "lãnh đạo", "chuyên viên"],
    },
    "hse": {
        "keywords": ["hse", "incident", "safety", "an toàn", "môi trường", "capa", "risk assessment"],
        "modules": ["incident report", "inspection", "capa", "risk assessment", "safety observation"],
        "roles": ["hse officer", "inspector"],
    },
    "digital_signature": {
        "keywords": ["ký số", "ky so", "digital signature", "hsm", "pki", "certificate", "ocsp", "tsa"],
        "modules": ["remote signing", "certificate validation", "hsm", "timestamp"],
        "roles": ["signer", "ca admin"],
    },
    "project_management": {
        "keywords": ["pms", "project", "wbs", "gantt", "milestone", "timesheet", "nguồn lực"],
        "modules": ["project plan", "wbs", "timesheet", "resource", "milestone"],
        "roles": ["project manager", "team lead"],
    },
    "crm": {
        "keywords": ["crm", "lead", "opportunity", "customer", "sales pipeline", "sales forecast", "account"],
        "modules": ["quản lý lead", "opportunity", "customer", "sales pipeline", "campaign"],
        "roles": ["sales", "account manager", "customer service"],
    },
}


def detect_domain(source_text: str, *, project_slug: str = "", customer: str = "") -> DomainDetectionResult:
    haystack = _normalize("\n".join([project_slug, customer, source_text or ""]))
    candidates: list[DomainCandidate] = []
    for domain, profile in _load_profiles().items():
        kw = _matches(haystack, profile["keywords"])
        modules = _matches(haystack, profile["modules"])
        roles = _matches(haystack, profile["roles"])
        raw = len(kw) * 1.0 + len(modules) * 2.0 + len(roles) * 0.75
        norm = min(raw / 8.0, 1.0)
        candidates.append(DomainCandidate(domain, round(norm, 3), kw, modules, roles))
    candidates.sort(key=lambda c: c.score, reverse=True)
    best = candidates[0] if candidates else DomainCandidate("generic", 0.0)
    if best.score < 0.45:
        selected = "generic"
        confidence = "low"
        score = best.score
        explanation = "No known domain reached threshold; selected generic source-driven fallback."
    else:
        selected = best.domain
        score = best.score
        confidence = "high" if score >= 0.75 else "medium"
        evidence = best.matched_modules or best.matched_keywords or best.matched_roles
        explanation = f"Selected {selected} with {confidence} confidence from matched evidence: {', '.join(evidence[:8])}."
    return DomainDetectionResult(selected, score, confidence, candidates, explanation)


def write_domain_detection(project_root: Path, result: DomainDetectionResult) -> Path:
    out = project_root / "artifacts" / "stage-0" / "domain-detection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _matches(haystack: str, terms: list[str]) -> list[str]:
    out = []
    for term in terms:
        if _normalize(term) in haystack:
            out.append(term)
    return out
