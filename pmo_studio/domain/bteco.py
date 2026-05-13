"""BTECO domain pack defaults."""
MANDAY_RATE_VND = 3_900_000
PRODUCTS = {
    "eoffice": {"name": "eOffice", "modules": ["auth", "document", "workflow", "report"]},
    "ky_so": {"name": "Ký số", "modules": ["certificate", "signing", "verification", "audit"]},
    "hse": {"name": "HSE", "modules": ["incident", "inspection", "training", "report"]},
    "pms": {"name": "PMS", "modules": ["planning", "tracking", "cost", "report"]},
}
COMPLEXITY_MD = {
    "screen": {"simple": 1.5, "medium": 2.75, "complex": 5.0},
    "api": {"simple": 1.2, "medium": 2.3, "complex": 4.5},
    "workflow": {"simple": 2.0, "medium": 4.0, "complex": 7.0},
    "report": {"simple": 1.5, "medium": 3.0, "complex": 5.0},
    "configuration": {"simple": 0.5, "medium": 1.0, "complex": 2.0},
}
