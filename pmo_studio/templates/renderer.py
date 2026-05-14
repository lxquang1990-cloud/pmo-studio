"""Tiny versioned template renderer used by deterministic generators."""
from __future__ import annotations

import re
from pathlib import Path
from string import Template

TEMPLATE_VERSION = "1.0.0"
TEMPLATE_ROOT = Path(__file__).parent


def render_template(template_rel: str, context: dict) -> str:
    path = TEMPLATE_ROOT / template_rel
    text = path.read_text(encoding="utf-8")
    normalized = re.sub(r"{{\s*([a-zA-Z0-9_]+)\s*}}", r"${\1}", text)
    data = {k: str(v) for k, v in context.items()}
    data.setdefault("template_version", TEMPLATE_VERSION)
    return Template(normalized).safe_substitute(data)
