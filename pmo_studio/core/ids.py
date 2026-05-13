"""PMO Studio v2.1 ID scheme and allocation."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable

ID_PATTERNS: Dict[str, str] = {
    "SRC": r"^SRC-\d{3}$",
    "BG": r"^BG-\d{3}$",
    "BR": r"^BR-[A-Z]{2,8}-\d{3}$",
    "REQ": r"^REQ-[A-Z]{2,8}-\d{3}$",
    "SCR": r"^SCR-[A-Z]{2,8}-\d{3}$",
    "API": r"^API-[A-Z]{2,8}-\d{3}$",
    "WF": r"^WF-[A-Z]{2,8}-\d{3}$",
    "RPT": r"^RPT-[A-Z]{2,8}-\d{3}$",
    "US": r"^US-\d{3}$",
    "AC": r"^AC-\d{3}-\d{2}$",
    "TC": r"^TC-\d{3}$",
    "UAT": r"^UAT-\d{3}$",
    "EST": r"^EST-\d{3}$",
    "RISK": r"^RISK-\d{3}$",
    "ASM": r"^ASM-\d{3}$",
    "DEC": r"^DEC-\d{3}$",
    "CR": r"^CR-\d{3}$",
}

AREA_TYPES = {"BR", "REQ", "SCR", "API", "WF", "RPT"}
SIMPLE_TYPES = {"SRC", "BG", "US", "TC", "UAT", "EST", "RISK", "ASM", "DEC", "CR"}


def validate_id(value: str) -> bool:
    return any(re.match(pattern, value) for pattern in ID_PATTERNS.values())


def id_type(value: str) -> str | None:
    for key, pattern in ID_PATTERNS.items():
        if re.match(pattern, value):
            return key
    return None


def extract_ids(text: str) -> list[str]:
    candidates = re.findall(r"\b(?:SRC|BG|BR|REQ|SCR|API|WF|RPT|US|AC|TC|UAT|EST|RISK|ASM|DEC|CR)(?:-[A-Z]{2,8})?-\d{3}(?:-\d{2})?\b", text)
    return [c for c in candidates if validate_id(c)]


@dataclass
class IdAllocator:
    counters: Dict[str, int] = field(default_factory=dict)

    def issue(self, kind: str, area: str | None = None, parent_us: str | None = None) -> str:
        kind = kind.upper()
        if kind == "AC":
            if not parent_us or not re.match(ID_PATTERNS["US"], parent_us):
                raise ValueError("AC IDs require parent_us like US-005")
            key = f"AC:{parent_us}"
            self.counters[key] = self.counters.get(key, 0) + 1
            return f"AC-{parent_us.split('-')[1]}-{self.counters[key]:02d}"
        if kind in AREA_TYPES:
            if not area:
                raise ValueError(f"{kind} requires area")
            area = area.upper()
            if not re.match(r"^[A-Z]{2,8}$", area):
                raise ValueError("area must be 2-8 uppercase letters")
            key = f"{kind}:{area}"
            self.counters[key] = self.counters.get(key, 0) + 1
            return f"{kind}-{area}-{self.counters[key]:03d}"
        if kind in SIMPLE_TYPES:
            self.counters[kind] = self.counters.get(kind, 0) + 1
            return f"{kind}-{self.counters[kind]:03d}"
        raise ValueError(f"Unknown ID kind: {kind}")

    @classmethod
    def from_state(cls, counters: Dict[str, int] | None) -> "IdAllocator":
        return cls(dict(counters or {}))
