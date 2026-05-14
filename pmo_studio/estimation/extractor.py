from __future__ import annotations
import re


def extract_features(source_text: str) -> list[tuple[str, str, str]]:
    features: list[tuple[str, str, str]] = []
    current_module = "Core"
    for line in (source_text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.strip("# ").strip()
            if title and not any(x in title.lower() for x in ["yêu cầu", "requirement", "source"]):
                current_module = title[:90]
        if "|" in stripped:
            cells = [c.strip() for c in stripped.strip().strip("|").split("|")]
            if len(cells) >= 3 and re.match(r"^(\d+(?:\.\d+)*|[ivx]+)$", cells[0], re.I):
                name, desc = cells[1], cells[2]
                if name and name.lower() not in {"chức năng", "mô tả", "module"}:
                    features.append((current_module, name[:100], (desc or name)[:260]))
        elif re.match(r"^[-•]\s+", stripped) and len(stripped) > 12:
            name = re.sub(r"^[-•]\s+", "", stripped).split(":", 1)[0].strip()
            features.append((current_module, name[:100], stripped[:260]))
    if not features:
        features = [("Core", "Core Workspace", "Source-driven core workspace"), ("Reporting", "Reports/Export", "Source-driven reporting and export")]
    seen, out = set(), []
    for item in features:
        key = (item[0].lower(), item[1].lower())
        if key not in seen:
            seen.add(key); out.append(item)
    return out[:20]
