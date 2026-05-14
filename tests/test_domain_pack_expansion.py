from pmo_studio.domain.detector import detect_domain
from pmo_studio.domain.pack_loader import list_domain_packs, load_domain_pack


def test_extended_domain_packs_exist():
    expected = {"eoffice", "hse", "digital_signature", "project_management", "hrm", "procurement", "lms"}
    assert expected.issubset(set(list_domain_packs()))
    for pack_id in expected:
        pack = load_domain_pack(pack_id)
        assert pack.modules
        assert pack.roles


def test_extended_domain_detection_examples():
    examples = {
        "hse": "HSE incident safety inspection CAPA risk assessment",
        "digital_signature": "Ký số HSM PKI certificate OCSP remote signing",
        "project_management": "PMS project WBS milestone timesheet resource",
        "hrm": "HRM nhân sự employee payroll leave attendance recruitment",
        "procurement": "Procurement mua sắm vendor RFQ purchase order bidding",
        "lms": "LMS khóa học quiz exam certificate e-learning",
    }
    for expected, text in examples.items():
        assert detect_domain(text).selected_domain == expected
