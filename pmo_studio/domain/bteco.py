"""BTECO domain pack defaults — dùng bởi quotation generator và estimate engine."""

MANDAY_RATE_VND = 3_900_000

PRODUCTS = {
    "eoffice": {"name": "eOffice", "modules": ["auth", "document", "workflow", "report"]},
    "ky_so":   {"name": "Ký số",   "modules": ["certificate", "signing", "verification", "audit"]},
    "hse":     {"name": "HSE",     "modules": ["incident", "inspection", "training", "report"]},
    "pms":     {"name": "PMS",     "modules": ["planning", "tracking", "cost", "report"]},
}

# Độ phức tạp màn hình — midpoint manday (FE + BE + test gộp)
COMPLEXITY_MD = {
    "screen":        {"simple": 0.75, "medium": 2.0,  "complex": 4.0,  "very_complex": 8.0},
    "api":           {"simple": 1.2,  "medium": 2.3,  "complex": 4.5},
    "workflow":      {"simple": 2.0,  "medium": 4.0,  "complex": 7.0},
    "report":        {"simple": 1.5,  "medium": 3.0,  "complex": 5.0},
    "configuration": {"simple": 0.5,  "medium": 1.0,  "complex": 2.0},
}

# Hệ số nền tảng (nhân vào manday gốc của từng màn hình)
PLATFORM_FACTORS = {
    "web":               1.0,   # Chỉ Web
    "mobile_single":     1.0,   # Mobile 1 nền tảng (iOS hoặc Android)
    "mobile_cross":      1.3,   # Mobile đa nền tảng cùng mã nguồn (React Native / Flutter)
    "mobile_native":     1.7,   # Mobile native iOS + Android riêng biệt
    "web_mobile_native": 2.2,   # Web + Mobile native (3 nền tảng)
}

# Hệ số rủi ro / BRD clarity buffer (chỉ áp cho phần manday màn hình có độ bất định cao)
RISK_FACTORS = {
    "very_detailed": 1.10,  # BRD rất chi tiết: có wireframe, luồng, đặc tả API
    "detailed":      1.15,  # BRD chi tiết: có danh sách tính năng, thiếu wireframe
    "overview":      1.25,  # BRD tổng quan: mô tả phân hệ, phải suy luận màn hình
    "vague":         1.35,  # BRD mờ: phải phỏng đoán nhiều → cảnh báo khách
}

# Hạng mục ngoài màn hình — khuyến nghị manday (min–max)
OUT_OF_SCREEN_DEFAULTS = {
    "devops":    {"label": "Thiết lập dự án & DevOps",   "md_min": 3, "md_max": 5,  "pct_of_screen": None},
    "uat":       {"label": "Hỗ trợ tích hợp & UAT",      "md_min": None, "md_max": None, "pct_of_screen": 0.10},
    "docs":      {"label": "Tài liệu hóa",                "md_min": 3, "md_max": 7,  "pct_of_screen": None},
    "golive":    {"label": "Triển khai & Go-live",        "md_min": 2, "md_max": 4,  "pct_of_screen": None},
    "training":  {"label": "Đào tạo người dùng",          "md_min": 2, "md_max": 5,  "pct_of_screen": None},
    "warranty":  {"label": "Bảo hành 3 tháng",            "md_min": None, "md_max": None, "pct_of_screen": 0.08},
}

# Benchmark manday trung bình cho từng loại phân hệ phổ biến
SUBSYSTEM_BENCHMARKS = {
    "auth":          {"screens": (6, 8),  "md": (10, 16)},
    "dashboard":     {"screens": (1, 2),  "md": (4, 8)},
    "crud_basic":    {"screens": (4, 5),  "md": (8, 12)},
    "approval_flow": {"screens": (5, 8),  "md": (15, 25)},
    "report":        {"screens": (3, 5),  "md": (8, 15)},
    "notification":  {"screens": (2, 3),  "md": (4, 7)},
}
