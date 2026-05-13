# Architecture

PMO Studio is organized as a thin CLI/adapter layer over deterministic Python modules.

## Layers

```text
CLI / Telegram Adapter
  ↓
Generators / Gates / Traceability / Exporters
  ↓
Core project state / IDs / registry / manifest
  ↓
Filesystem project workspace
```

## Main packages

- `core/` — project config/state, ID allocation, baseline manifests, CR, registry, doctor.
- `security/` — source preprocessing, redaction, ignore rules, vault references.
- `generators/` — Stage 0, BA, PO/PM/IC, source-driven generation, refinement loop.
- `gates/` — Gate A structural checks, Gate B/C semantic checks, project-wide runner.
- `traceability/` — graph/RTM extraction and validation.
- `exporters/` — static HTML, DOCX, ZIP bundle.
- `llm/` — provider abstraction, 9Router/noop, writer/reviewer hooks.
- `eval/` — single eval and multi-project benchmark.
- `interfaces/` — Telegram/OpenClaw command adapter.

## Project workspace layout

```text
<root>/<slug>/
├── config.json
├── state.json
├── source/
│   ├── uploads/
│   └── redacted/
├── artifacts/
│   ├── stage-0/
│   ├── po/
│   ├── pm/
│   ├── ba/
│   └── ic/
├── traceability/
├── quality/
├── baselines/
├── change-requests/
├── exports/
├── metrics/
└── logs/
```

## Generation flow

```text
init → Stage 0/source preprocessing → generate PO/PM/BA/IC → optional refine → traceability → gates → export/baseline
```

## Offline vs LLM mode

- Offline mode: `--llm noop` returns deterministic fallback output.
- LLM mode: `--llm 9router` uses `9ROUTER_API_KEY` and optional `PMO_9ROUTER_MODEL`.
- Redacted source is the only intended LLM input.

## Registry

Registry file:

```text
<root>/.pmo-studio-registry.json
```

It stores project slug, customer, root, lifecycle state, current stage, timestamps. It enables recent-project fallback for CLI/Telegram commands.
