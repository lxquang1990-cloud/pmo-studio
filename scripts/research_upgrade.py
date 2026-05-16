#!/usr/bin/env python3
"""Periodic PMO Studio research upgrade scanner.

The scanner builds a conservative source catalog for PMO Studio improvement work.
It does not vendor/copy third-party template content. It records source metadata,
license hints, risk level, and target improvement areas.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "research"
USER_AGENT = "PMO-Studio-Research-Upgrade/1.0"

@dataclass(frozen=True)
class SeedSource:
    name: str
    url: str
    kind: str
    target: str
    usage: str
    priority: str = "medium"

@dataclass
class CatalogEntry:
    name: str
    url: str
    kind: str
    target: str
    usage: str
    priority: str
    license: str
    license_status: str
    risk: str
    action: str
    notes: str
    fetched_at: str

SEED_SOURCES = [
    SeedSource(
        "OWASP user security stories",
        "https://github.com/OWASP/user-security-stories",
        "security-acceptance-criteria",
        "security AC pack, NFR gate, API/auth/audit checklist",
        "adapt-if-license-allows; otherwise derive abstract checklist with attribution",
        "high",
    ),
    SeedSource(
        "Canaxess accessibility acceptance criteria",
        "https://github.com/canaxess/accessibility-acceptance-criteria",
        "accessibility-acceptance-criteria",
        "accessibility AC pack and UI/NFR gate",
        "adapt-if-license-allows; otherwise derive abstract WCAG-oriented rubric",
        "high",
    ),
    SeedSource(
        "inDriver handbook acceptance criteria",
        "https://github.com/inDriver/handbook/blob/main/docs/strategy-and-management/acceptance-criteria.md",
        "acceptance-criteria-guide",
        "user story / AC quality rubric",
        "reference-only unless repository license explicitly permits adaptation",
        "medium",
    ),
    SeedSource(
        "Jam01 SRS Template",
        "https://github.com/jam01/SRS-Template",
        "srs-template",
        "SRS completeness gate and section coverage",
        "already conceptually integrated; re-check for attribution and completeness gaps",
        "medium",
    ),
    SeedSource(
        "RequirementLinter",
        "https://github.com/jonverrier/RequirementLinter",
        "requirement-quality-linter",
        "vague term detection, compound requirement split rules",
        "already conceptually integrated; re-check for rule coverage gaps",
        "medium",
    ),
]

SEARCH_QUERIES = [
    "business requirements document template license",
    "software requirements specification template license",
    "product requirements document template license",
    "requirements traceability matrix template license",
    "user story acceptance criteria template license",
    "software estimation template license",
]

PERMISSIVE_LICENSE_KEYS = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "cc-by-4.0", "cc0-1.0"}
RESTRICTIVE_LICENSE_KEYS = {"gpl-2.0", "gpl-3.0", "agpl-3.0", "lgpl-2.1", "lgpl-3.0"}


def http_json(url: str, timeout: int = 20) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def github_repo_from_url(url: str) -> tuple[str, str] | None:
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    if owner in {"search"}:
        return None
    return owner, repo


def license_for_url(url: str) -> tuple[str, str, str]:
    repo = github_repo_from_url(url)
    if not repo:
        return "unknown", "manual-review", "Non-GitHub or non-repository URL; inspect manually."
    owner, repo_name = repo
    data = http_json(f"https://api.github.com/repos/{owner}/{repo_name}")
    if not data:
        return "unknown", "manual-review", "Could not fetch repository metadata; inspect manually."
    lic = data.get("license") or {}
    key = (lic.get("key") or "unknown").lower()
    name = lic.get("name") or key
    if key in PERMISSIVE_LICENSE_KEYS:
        return name, "permissive", "May be adapted with attribution and license notice."
    if key in RESTRICTIVE_LICENSE_KEYS:
        return name, "restrictive", "Do not vendor directly; use only as conceptual reference unless legal review approves."
    if key == "unknown" or not key:
        return "unknown", "manual-review", "No clear license found; do not copy/adapt content."
    return name, "manual-review", "License requires manual compatibility review."


def classify(seed: SeedSource, license_status: str) -> tuple[str, str]:
    if license_status == "permissive":
        return "low", "Candidate for adapted rubric/template with attribution."
    if license_status == "restrictive":
        return "high", "Reference only; do not copy into PMO Studio."
    if "official" in seed.kind or "standard" in seed.kind:
        return "medium", "Extract abstract structure only; avoid copying text."
    return "medium", "Manual review before implementation."


def build_seed_catalog() -> list[CatalogEntry]:
    now = datetime.now(timezone.utc).isoformat()
    entries: list[CatalogEntry] = []
    for seed in SEED_SOURCES:
        license_name, status, notes = license_for_url(seed.url)
        risk, action = classify(seed, status)
        entries.append(CatalogEntry(
            name=seed.name,
            url=seed.url,
            kind=seed.kind,
            target=seed.target,
            usage=seed.usage,
            priority=seed.priority,
            license=license_name,
            license_status=status,
            risk=risk,
            action=action,
            notes=notes,
            fetched_at=now,
        ))
    return entries


def search_github(max_results_per_query: int) -> list[CatalogEntry]:
    now = datetime.now(timezone.utc).isoformat()
    entries: list[CatalogEntry] = []
    seen: set[str] = {s.url for s in SEED_SOURCES}
    for query in SEARCH_QUERIES:
        params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": max_results_per_query})
        data = http_json(f"https://api.github.com/search/repositories?{params}")
        if not data:
            continue
        for item in data.get("items", [])[:max_results_per_query]:
            url = item.get("html_url")
            if not url or url in seen:
                continue
            seen.add(url)
            lic = item.get("license") or {}
            key = (lic.get("key") or "unknown").lower()
            license_name = lic.get("name") or key
            if key in PERMISSIVE_LICENSE_KEYS:
                status = "permissive"
            elif key in RESTRICTIVE_LICENSE_KEYS:
                status = "restrictive"
            else:
                status = "manual-review"
            seed = SeedSource(item.get("full_name", url), url, "github-search-result", "candidate source catalog item", f"query: {query}")
            risk, action = classify(seed, status)
            entries.append(CatalogEntry(
                name=item.get("full_name", url),
                url=url,
                kind="github-search-result",
                target="candidate source catalog item",
                usage=f"Discovered by query: {query}",
                priority="low",
                license=license_name,
                license_status=status,
                risk=risk,
                action=action,
                notes=(item.get("description") or "")[:240],
                fetched_at=now,
            ))
    return entries


def render_markdown(entries: list[CatalogEntry]) -> str:
    lines = [
        "# PMO Studio Research Source Catalog",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "This catalog is for PMO Studio improvement research. Do not copy third-party content unless license status allows adaptation and attribution is preserved.",
        "",
        "## Summary",
        "",
    ]
    counts: dict[str, int] = {}
    for e in entries:
        counts[e.license_status] = counts.get(e.license_status, 0) + 1
    for status in sorted(counts):
        lines.append(f"- {status}: {counts[status]}")
    lines.extend([
        "",
        "## Sources",
        "",
        "| Priority | Risk | License status | Source | Kind | PMO target | Action |",
        "|---|---|---|---|---|---|---|",
    ])
    for e in sorted(entries, key=lambda x: (x.priority != "high", x.risk, x.name.lower())):
        source = f"[{e.name}]({e.url})"
        lines.append(f"| {e.priority} | {e.risk} | {e.license_status} ({e.license}) | {source} | {e.kind} | {e.target} | {e.action} |")
    lines.extend([
        "",
        "## Recommended next implementation queue",
        "",
        "1. Security acceptance criteria pack from permissive/approved OWASP-style sources.",
        "2. Accessibility acceptance criteria pack from permissive/approved WCAG-oriented sources.",
        "3. SRS completeness gate improvements for external interfaces, constraints, dependencies, and verification.",
        "4. RTM quality gate for status, priority, source, and test coverage fields.",
        "5. Estimation rubric benchmark with phase/role/risk buffer sanity checks.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PMO Studio research upgrade source catalog")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--max-results-per-query", type=int, default=2)
    parser.add_argument("--no-search", action="store_true", help="Only use curated seed sources; skip GitHub search API")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = build_seed_catalog()
    if not args.no_search:
        entries.extend(search_github(max(0, args.max_results_per_query)))

    json_path = out_dir / "source-catalog.json"
    md_path = out_dir / "source-catalog.md"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "entries": [asdict(e) for e in entries]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(entries), encoding="utf-8")
    print(f"Research catalog: {md_path}")
    print(f"Research JSON: {json_path}")
    print(f"Entries: {len(entries)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
