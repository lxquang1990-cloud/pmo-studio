"""Domain intelligence — industry-specific prompts, terminology, and defaults.

Every domain pack provides:
- Prompt injections for each artifact type (PRD, BRD, SRS, US, Test Cases)
- Terminology dictionary (generic → domain-specific replacements)
- Module suggestions for the domain
- Role/stakeholder vocabulary
- Acronyms used heavily in the domain

Add new domains here. The bteco domain pack (bteco.py) provides cost estimation
defaults; this module provides content intelligence for artifact generation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# ── Domain pack dataclass ────────────────────────────────────────────────────

@dataclass
class DomainPack:
    """Content intelligence for one domain."""
    domain_id: str
    label: str
    industry: str = ""
    # Prompt injections keyed by artifact type
    prd_context: str = ""
    brd_context: str = ""
    srs_context: str = ""
    us_context: str = ""
    test_context: str = ""
    # Modules typical for this domain
    modules: List[str] = field(default_factory=list)
    # Roles/stakeholders specific to this domain
    roles: Dict[str, str] = field(default_factory=dict)
    # Terminology: generic_term → domain_term
    terms: Dict[str, str] = field(default_factory=dict)
    # Acronyms the domain uses heavily
    acronyms: Dict[str, str] = field(default_factory=dict)


# ── eOffice ──────────────────────────────────────────────────────────────────

EOFFICE = DomainPack(
    domain_id="eoffice",
    label="eOffice",
    industry="Quản lý văn bản & Điều hành",
    prd_context=(
        "Sản phẩm là hệ thống Quản lý Văn bản và Điều hành (eOffice). "
        "Tập trung vào luồng duyệt đa cấp (multi-level approval), "
        "quản lý công văn đến/đi (incoming/outgoing documents), "
        "sổ văn bản (document register), "
        "quy trình phê duyệt (approval workflow) với SLA từng bước, "
        "theo dõi tình trạng xử lý văn bản (document processing status)."
    ),
    brd_context=(
        "Khách hàng là cơ quan hành chính / doanh nghiệp cần số hóa quy trình công văn. "
        "BR phải phản ánh: (1) quy trình tiếp nhận công văn đến, "
        "(2) luồng chuyển xử lý nội bộ, (3) phát hành công văn đi, "
        "(4) báo cáo tình trạng xử lý, (5) tích hợp chữ ký số, "
        "(6) lưu trữ và tra cứu văn bản theo Thông tư 02/2019/TT-BNV."
    ),
    srs_context=(
        "Hệ thống eOffice yêu cầu các module: xác thực & phân quyền (auth), "
        "đăng ký văn bản đến/đi (document register), "
        "luồng chuyển xử lý và phê duyệt (workflow engine), "
        "tra cứu và báo cáo thống kê (search & report), "
        "tích hợp ký số (digital signature). "
        "Chức năng chi tiết: đăng ký văn bản đến (register incoming), "
        "chuyển xử lý (forward/routing), xin ý kiến (consultation), "
        "phê duyệt (approval), ký duyệt (sign-off), "
        "phát hành văn bản đi (issue outgoing), tra cứu hồ sơ (docket search), "
        "báo cáo thống kê xử lý văn bản (document processing reports), "
        "cảnh báo quá hạn SLA (SLA overdue alerts). "
        "Yêu cầu phi chức năng: audit log, phân quyền theo phòng ban, "
        "mã hóa tài liệu nhạy cảm, backup tự động, khả năng mở rộng 5000+ văn bản/ngày."
    ),
    us_context=(
        "User Stories cho eOffice cần tập trung vào các persona: "
        "Văn thư (Clerk), Chuyên viên (Officer), Lãnh đạo phòng (Dept Head), "
        "Lãnh đạo cơ quan (Director/CEO), Người ký (Signer). "
        "Mỗi US phải gắn với một bước cụ thể trong luồng công văn "
        "(tiếp nhận → chuyển xử lý → xin ý kiến → phê duyệt → ký → phát hành)."
    ),
    test_context=(
        "Test Cases cho eOffice phải kiểm tra: đúng luồng duyệt (correct routing), "
        "SLA từng bước, phân quyền (role-based access), "
        "định dạng số văn bản (document numbering format), "
        "ký số hợp lệ, báo cáo đúng dữ liệu, "
        "xử lý văn bản đến đồng thời (concurrent incoming processing)."
    ),
    modules=["auth", "document", "workflow", "report", "signature"],
    roles={
        "Clerk": "Văn thư — tiếp nhận, đăng ký, phát hành văn bản",
        "Officer": "Chuyên viên — xử lý, trình ký",
        "DeptHead": "Lãnh đạo phòng — phê duyệt cấp phòng",
        "Director": "Lãnh đạo cơ quan — phê duyệt cấp cao nhất",
        "Signer": "Người ký — ký số văn bản",
    },
    terms={
        "document": "công văn / văn bản",
        "workflow": "luồng duyệt",
        "task": "nhiệm vụ xử lý",
        "notification": "thông báo xử lý văn bản",
        "report": "báo cáo thống kê văn bản",
        "status tracking": "theo dõi tình trạng xử lý văn bản",
        "approval flow": "quy trình phê duyệt",
        "entity": "văn bản / hồ sơ",
        "project": "hệ thống eOffice",
        "system": "Hệ thống quản lý văn bản và điều hành",
        "user": "cán bộ / chuyên viên",
    },
    acronyms={
        "SLA": "Service Level Agreement — cam kết thời gian xử lý",
        "BNV": "Bộ Nội vụ",
    },
)

# ── Digital Signature (Ký số) ────────────────────────────────────────────────

KY_SO = DomainPack(
    domain_id="ky_so",
    label="Ký số",
    industry="Chứng thư số & Bảo mật",
    prd_context=(
        "Sản phẩm là hệ thống Ký số (Digital Signature) — cung cấp giải pháp "
        "chứng thư số (digital certificate), ký số tập trung (centralized signing), "
        "và ký số từ xa (remote signing). Người dùng mục tiêu: cơ quan nhà nước, "
        "doanh nghiệp cần ký hóa đơn điện tử, hợp đồng số, văn bản hành chính. "
        "Tích hợp với HSM (Hardware Security Module), PKI, và chuẩn eIDAS/VNPT-CA."
    ),
    brd_context=(
        "Khách hàng cần giải pháp ký số tuân thủ: Nghị định 130/2018/NĐ-CP, "
        "Thông tư 16/2019/TT-BTTTT, chuẩn ETSI. "
        "BR phải bao gồm: (1) phát hành/thu hồi chứng thư số (cert issuance/revocation), "
        "(2) ký PDF/XML/Office, (3) xác thực chữ ký (signature verification), "
        "(4) timestamp (LTV — Long Term Validation), "
        "(5) audit trail đầy đủ, (6) OCSP/CRL check online."
    ),
    srs_context=(
        "Hệ thống Ký số cần các module: Certificate Authority (CA), "
        "Registration Authority (RA), Signing Service, Verification Service, "
        "Timestamp Authority (TSA), HSM Connector, Audit Service. "
        "API endpoints: POST /sign (ký tài liệu), POST /verify (xác thực), "
        "POST /certificates (phát hành), DELETE /certificates/{id} (thu hồi). "
        "Security requirements: FIPS 140-2 Level 3, mTLS, key escrow protection, "
        "HSM integration via PKCS#11, signing key never leaves HSM."
    ),
    us_context=(
        "Persona: Người ký (Signer), Quản trị CA (CA Admin), "
        "Người xác thực (Verifier), Kiểm toán (Auditor). "
        "US phải gắn với từng bước trong vòng đời chứng thư: "
        "đăng ký → xác minh danh tính → cấp phát → sử dụng ký → gia hạn → thu hồi."
    ),
    test_context=(
        "Test Cases cho Ký số phải kiểm tra: chứng thư hợp lệ/hết hạn/thu hồi, "
        "chữ ký bị giả mạo (tampered document), ký đúng định dạng (PAdES, XAdES, CAdES), "
        "timestamp LTV hợp lệ, OCSP response, audit log toàn vẹn, "
        "HSM failover, concurrent signing (100+ requests/s)."
    ),
    modules=["certificate", "signing", "verification", "audit", "timestamp"],
    roles={
        "Signer": "Người ký — thực hiện ký số tài liệu",
        "CAAdmin": "Quản trị CA — cấp/thu hồi chứng thư số",
        "Verifier": "Người xác thực — kiểm tra tính hợp lệ chữ ký",
        "Auditor": "Kiểm toán viên — rà soát nhật ký ký số",
    },
    terms={
        "document": "tài liệu cần ký",
        "workflow": "luồng phê duyệt ký",
        "task": "yêu cầu ký",
        "notification": "thông báo hết hạn chứng thư",
        "report": "báo cáo kiểm toán ký số",
        "status tracking": "theo dõi trạng thái chứng thư",
        "approval flow": "quy trình ký duyệt",
        "entity": "chứng thư số / token ký",
        "project": "hệ thống Ký số tập trung",
        "system": "Hệ thống chứng thư số và ký số",
        "user": "người dùng chứng thư số",
    },
    acronyms={
        "CA": "Certificate Authority — tổ chức phát hành chứng thư số",
        "HSM": "Hardware Security Module",
        "PKI": "Public Key Infrastructure",
        "OCSP": "Online Certificate Status Protocol",
        "CRL": "Certificate Revocation List",
        "LTV": "Long Term Validation",
        "TSA": "Timestamp Authority",
    },
)

# ── HSE ──────────────────────────────────────────────────────────────────────

HSE = DomainPack(
    domain_id="hse",
    label="HSE",
    industry="An toàn Sức khỏe Môi trường",
    prd_context=(
        "Sản phẩm là hệ thống Quản lý An toàn - Sức khỏe - Môi trường (HSE Management). "
        "Hỗ trợ doanh nghiệp tuân thủ ISO 45001 (An toàn & Sức khỏe nghề nghiệp) và "
        "ISO 14001 (Quản lý Môi trường). Core workflow: Incident Reporting → "
        "Investigation → Corrective/Preventive Action (CAPA) → Close-out."
    ),
    brd_context=(
        "Khách hàng là doanh nghiệp sản xuất / dầu khí / xây dựng cần quản lý HSE. "
        "BR phải đáp ứng: (1) báo cáo sự cố (incident report) và near-miss, "
        "(2) điều tra nguyên nhân gốc (root cause analysis — 5 Whys, Fishbone), "
        "(3) hành động khắc phục/phòng ngừa (CAPA) với tracking đến close-out, "
        "(4) thanh tra an toàn (safety inspection) định kỳ và đột xuất, "
        "(5) quản lý training & chứng chỉ an toàn (safety certification), "
        "(6) báo cáo compliance định kỳ theo ISO 45001/14001."
    ),
    srs_context=(
        "Hệ thống HSE cần các module: Incident Management (sự cố & near-miss), "
        "Inspection Management (thanh tra định kỳ/đột xuất), "
        "Training & Competency Management (khóa học & chứng chỉ), "
        "Permit to Work (giấy phép làm việc), "
        "Risk Assessment (ma trận rủi ro 5x5, JSA), "
        "Dashboard & Reporting (chỉ số KPI: LTIFR, TRIR). "
        "Phân quyền: Admin, HSE Manager, Inspector, Employee, Contractor."
    ),
    us_context=(
        "Persona: Nhân viên hiện trường (Field Worker), Giám sát an toàn (HSE Officer), "
        "Quản lý HSE (HSE Manager), Nhà thầu (Contractor), Kiểm toán viên (Auditor). "
        "User Stories phải cover: báo cáo sự cố từ mobile, điều tra sự cố, "
        "phê duyệt CAPA, lên lịch thanh tra, đào tạo định kỳ, cấp Permit to Work."
    ),
    test_context=(
        "Test Cases cho HSE phải kiểm tra: incident report flow đầy đủ "
        "(report → investigate → CAPA → close), "
        "cảnh báo sự cố nghiêm trọng (major incident escalation), "
        "tính toàn vẹn dữ liệu điều tra (investigation data integrity), "
        "compliance report đúng kỳ, phân quyền contractor vs employee, "
        "offline mobile report capability."
    ),
    modules=["incident", "inspection", "training", "report", "permit", "risk"],
    roles={
        "FieldWorker": "Nhân viên hiện trường — báo cáo sự cố, near-miss",
        "HSEOfficer": "Giám sát an toàn — điều tra sự cố, thanh tra",
        "HSEManager": "Quản lý HSE — phê duyệt CAPA, báo cáo compliance",
        "Contractor": "Nhà thầu — báo cáo sự cố, xin Permit to Work",
        "Auditor": "Kiểm toán viên — đánh giá tuân thủ ISO",
    },
    terms={
        "document": "hồ sơ an toàn",
        "workflow": "quy trình xử lý sự cố",
        "task": "hành động khắc phục (CAPA)",
        "notification": "cảnh báo an toàn",
        "report": "báo cáo sự cố / báo cáo compliance",
        "status tracking": "theo dõi trạng thái CAPA",
        "approval flow": "quy trình phê duyệt CAPA",
        "entity": "sự cố (incident) / near-miss",
        "project": "hệ thống HSE Management",
        "system": "Hệ thống quản lý An toàn - Sức khỏe - Môi trường",
        "user": "nhân viên / giám sát an toàn",
    },
    acronyms={
        "HSE": "Health, Safety, Environment",
        "CAPA": "Corrective and Preventive Action",
        "LTIFR": "Lost Time Injury Frequency Rate",
        "TRIR": "Total Recordable Incident Rate",
        "PTW": "Permit to Work",
        "JSA": "Job Safety Analysis",
    },
)

# ── PMS ──────────────────────────────────────────────────────────────────────

PMS = DomainPack(
    domain_id="pms",
    label="PMS",
    industry="Quản lý Dự án & Portfolio",
    prd_context=(
        "Sản phẩm là hệ thống Project Management System (PMS) — quản lý danh mục dự án "
        "(project portfolio), theo dõi tiến độ (progress tracking), quản lý chi phí "
        "(cost management), và báo cáo đầu tư (investment reporting)."
    ),
    brd_context=(
        "Khách hàng cần hệ thống PMS cho: lập kế hoạch (planning), "
        "phân bổ nguồn lực (resource allocation), theo dõi milestone, "
        "quản lý budget & actual, báo cáo EVM (Earned Value Management)."
    ),
    srs_context=(
        "PMS modules: Planning (WBS, Gantt), Resource Management, "
        "Cost Control (budget vs actual, EVM), Risk Register, "
        "Dashboard & Analytics, Portfolio View."
    ),
    us_context=(
        "Persona: Project Manager, Portfolio Manager, "
        "Resource Manager, Sponsor, Team Member."
    ),
    test_context=(
        "Test Cases: kiểm tra WBS đúng cấu trúc, Gantt chart, "
        "budget variance alert, resource overallocation warning, "
        "milestone notification, SPI/CPI calculation."
    ),
    modules=["planning", "tracking", "cost", "report", "resource"],
    roles={
        "PM": "Project Manager — quản lý dự án",
        "PfM": "Portfolio Manager — quản lý danh mục",
        "RM": "Resource Manager — phân bổ nguồn lực",
        "Sponsor": "Nhà tài trợ — phê duyệt ngân sách",
    },
    terms={
        "document": "tài liệu dự án",
        "workflow": "quy trình phê duyệt dự án",
        "task": "công việc (WBS)",
        "notification": "thông báo milestone",
        "report": "báo cáo tiến độ",
        "status tracking": "theo dõi milestone & % hoàn thành",
        "entity": "dự án / work package",
        "project": "danh mục dự án",
        "system": "Hệ thống quản lý dự án",
    },
    acronyms={
        "WBS": "Work Breakdown Structure",
        "EVM": "Earned Value Management",
        "SPI": "Schedule Performance Index",
        "CPI": "Cost Performance Index",
    },
)

# ── Registry ─────────────────────────────────────────────────────────────────

DOMAIN_PACKS: Dict[str, DomainPack] = {
    "eoffice": EOFFICE,
    "ky_so": KY_SO,
    "hse": HSE,
    "pms": PMS,
    "bteco": DomainPack(domain_id="bteco", label="BTECO Default", industry="General"),
}

DEFAULT_DOMAIN = "bteco"


def get_domain(domain_pack: str) -> DomainPack:
    """Resolve domain pack; falls back to generic."""
    return DOMAIN_PACKS.get(domain_pack, DOMAIN_PACKS[DEFAULT_DOMAIN])


def domain_products(domain_pack: str) -> list[str]:
    """Product labels associated with this domain pack."""
    d = get_domain(domain_pack)
    if d.domain_id == "bteco":
        from pmo_studio.domain.bteco import PRODUCTS
        return [v["name"] for v in PRODUCTS.values()]
    return [d.label]


def inject_domain_prompt(artifact_type: str, domain_pack: str, base_prompt: str) -> str:
    """Enrich a prompt with domain-specific context."""
    d = get_domain(domain_pack)
    ctx: Dict[str, str] = {
        "PRD": d.prd_context,
        "BRD": d.brd_context,
        "SRS": d.srs_context,
        "US": d.us_context,
    }
    injection = ctx.get(artifact_type.upper(), "")
    if not injection:
        return base_prompt
    return f"{injection}\n\n{base_prompt}"


def domain_terms(domain_pack: str) -> Dict[str, str]:
    """Get terminology dict for a domain (for refinement deterministic patches)."""
    return get_domain(domain_pack).terms


def domain_acronyms(domain_pack: str) -> Dict[str, str]:
    """Get acronym dict for a domain."""
    return get_domain(domain_pack).acronyms


def domain_modules(domain_pack: str) -> List[str]:
    """Get suggested modules for a domain."""
    return get_domain(domain_pack).modules


def domain_roles(domain_pack: str) -> Dict[str, str]:
    """Get role definitions for a domain."""
    return get_domain(domain_pack).roles
