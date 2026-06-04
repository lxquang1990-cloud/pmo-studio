# SnailBot Advisory Council

> First implementation slice for replacing the standalone CEO Agent with SnailBot as portfolio orchestrator.

## Principle

SnailBot is the CEO/Portfolio Orchestrator. The Advisory Council does not execute code, create repositories, call providers, or change project state. It only produces structured opinions, a conflict report, and a decision brief.

```text
Snail → SnailBot → Advisory Council → Decision Brief → PMO Studio artifacts/gates
```

## Current scope

Implemented as an offline/deterministic PMO Studio module:

```text
pmo_studio/advisory/
├── council.py
├── profiles.py
└── profiles/*.json
```

CLI:

```bash
pmo-studio advisory run --request-file request.md --out-dir .pmo/advisory
pmo-studio advisory profiles
```

## Advisor profiles

Initial council:

- Architect Advisor
- Security Advisor
- BA/Product Advisor
- QA/Test Advisor
- DevOps/Release Advisor
- UX/Human-in-the-loop Advisor

Selection is trigger-based for the first slice. QA/Test is always included as a safety/default quality voice.

## Output artifacts

Each council run writes:

```text
.pmo/advisory/<council-id>.json
.pmo/advisory/<council-id>.md
.pmo/advisory/latest.json
.pmo/advisory/latest.md
```

The Markdown file is a Decision Brief containing:

- request summary
- selected advisors
- advisor opinions
- risk/assumption lists
- conflict report
- SnailBot decision gate checklist

## Why offline first?

The goal is to build the governance rail before runtime autonomy:

```text
profiles + schemas + conflict report + decision brief
before
multi-agent spawning + GitHub automation + auto-release
```

This mirrors the PMO Studio pattern: artifact and gate first, runtime later.

## Next upgrades

1. Add JSON schemas for advisor opinion and conflict report.
2. Add benchmark fixtures for advisory selection and conflict detection.
3. Add optional LLM-backed advisor mode via existing PMO Studio LLM provider abstraction.
4. Add SnailBot decision log integration.
5. Feed approved decision brief into PMO artifact generation.
