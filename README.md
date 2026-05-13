# PMO Studio v2.1

PMO Studio is an offline-first Documentation Operating System for software projects. It generates and governs PO/PM/BA/IC artifacts: Stage 0 intake, PRD, BRD, SRS, user stories, acceptance criteria, test cases, quotation, fit-gap, configuration workbook, traceability, quality gates, baseline/change requests, and export packs.

## Current milestone

```text
PMO Studio v1.0.0rc2 — bundled, registry-aware, Telegram-ready, LLM-gate ready
```

## Core principles

- **Offline-first:** default LLM provider is `noop`; 9Router is opt-in for generation/review.
- **Security-first:** original sources are untrusted; redacted sources are used for generation/LLM flows.
- **Traceable:** IDs and links are extracted into RTM/graph.
- **Governed:** official baseline/sign-off/quotation require human approval.
- **Portable:** CLI, Telegram/OpenClaw adapter, HTML/DOCX/ZIP exports.

## Install / dev

From this repo:

```bash
cd /home/snail/.openclaw/workspace/pmo-studio
python -m compileall -q pmo_studio
```

Optional editable install:

```bash
python -m pip install -e .
pmo --help
```

## Quick start

```bash
cd /home/snail/.openclaw/workspace/pmo-studio

python -m pmo_studio.cli --root /tmp/pmo-demo scaffold

echo 'Khách hàng cần eOffice quản lý văn bản, duyệt đa cấp. token=secret' > /tmp/pmo-source.md

python -m pmo_studio.cli --root /tmp/pmo-demo init demo-project \
  --customer 'Demo Customer' \
  --source /tmp/pmo-source.md

python -m pmo_studio.cli --root /tmp/pmo-demo generate demo-project all \
  --from-sources \
  --llm noop \
  --refine \
  --max-refine 2

python -m pmo_studio.cli --root /tmp/pmo-demo trace demo-project --validate
python -m pmo_studio.cli --root /tmp/pmo-demo run-gates demo-project
python -m pmo_studio.cli --root /tmp/pmo-demo export demo-project --format zip
```

## CLI reference

### Project registry

```bash
python -m pmo_studio.cli list --refresh
python -m pmo_studio.cli recent
```

Most project commands accept omitted `<slug>` and use the recent project from registry.

### Generate

```bash
python -m pmo_studio.cli generate [slug] all|po|pm|ba|ic \
  --from-sources \
  --llm noop|9router \
  --model <model> \
  --refine \
  --max-refine 2
```

### Quality and traceability

```bash
python -m pmo_studio.cli trace [slug] --validate
python -m pmo_studio.cli run-gates [slug]
python -m pmo_studio.cli run-gates [slug] --include-c
python -m pmo_studio.cli run-gates [slug] --include-c --llm 9router --model Tier2 --gate-timeout 60 --gate-fallback
python -m pmo_studio.cli gate [slug] ba.srs /path/to/srs.md --layer A|B|C
```

### Export

```bash
python -m pmo_studio.cli export [slug] --format html|docx|zip|all
python -m pmo_studio.cli export [slug] --format zip --include-redacted-sources
```

ZIP bundles never include original `source/uploads`. `--include-redacted-sources` includes only `source/redacted`.

### Governance

```bash
python -m pmo_studio.cli baseline [slug] v1.0
python -m pmo_studio.cli diff [slug] v1.0
python -m pmo_studio.cli cr [slug] v1.0 --title 'Change' --description '...'
```

For chat/Telegram usage, baseline/sign-off/official quotation require explicit approval.

### Benchmark

```bash
python -m pmo_studio.cli eval --benchmark
python -m pmo_studio.cli eval --benchmark --no-docx
```

Benchmark cases:

- eOffice Document Workflow
- Digital Signature Platform
- HSE Incident Management

## Telegram/OpenClaw commands

Handled by `pmo_studio.interfaces.telegram_adapter`:

```text
/pmo help
/pmo init <slug> --customer "Tên KH" --brief "Mô tả" [--source file]
/pmo generate [slug] all|po|pm|ba|ic --from-sources --refine --llm noop|9router
/pmo ba [slug]
/pmo trace [slug]
/pmo gates [slug] [--include-c]
/pmo status [slug]
/pmo list [--refresh]
/pmo recent
/pmo export [slug] --format html|docx|zip|all [--send] [--include-redacted-sources]
/pmo baseline [slug] v1.0 --approved
/pmo benchmark [--send] [--no-docx]
/pmo doctor [slug]
```

`--send` adds `MEDIA:<path>` lines for OpenClaw-compatible surfaces.

## ID scheme

Supported IDs:

```text
SRC, BG, BR, REQ, SCR, API, WF, RPT, US, AC, TC, UAT, EST, RISK, ASM, DEC, CR
```

Main flow:

```text
SRC/BG → BR → REQ → SCR/API/WF/RPT → US → AC → TC
REQ/SCR/API/WF/RPT → EST
```

## Safety/security model

- Original source files are copied to `source/uploads`.
- Redacted files are copied to `source/redacted`.
- Redaction targets API keys, passwords, tokens, private keys, emails, VN phone numbers.
- Prompt injection patterns are detected during preprocessing.
- LLM writer treats source as untrusted data.
- Official baseline/sign-off/quotation require human approval in chat flow.

## Verification

Fast smoke:

```bash
scripts/smoke_phase11.sh
```

Benchmark:

```bash
scripts/benchmark.sh
```

Negative checks:

```bash
scripts/negative_checks.py
```

Install/console-script check:

```bash
scripts/install_check.sh
```

Full release verification:

```bash
scripts/verify_all.sh /tmp/pmo-release-verify
```

LLM Gate comparison:

```bash
python scripts/benchmark_compare_llm_gates_focused.py --model Tier2 --gate-fallback
python scripts/benchmark_compare_llm_gates.py --model Tier2 --gate-timeout 60 --gate-fallback
```

Release artifact integrity:

```bash
sha256sum -c dist/SHA256SUMS
cat dist/release-manifest.json
```

## CI

Workflow templates are provided under `.github/workflows/`:

- `verify.yml` — compile, smoke, benchmark, negative checks on Python 3.11/3.12/3.13.
- `release.yml` — tag/release verification and package build.

## Documentation index

- `docs/architecture.md` — system architecture.
- `docs/traceability.md` — traceability graph/RTM model.
- `docs/quality-gates.md` — Gate A/B/C framework.
- `docs/llm-gate-operations.md` — 9Router reviewer, cache, timeout, fallback policy.
- `docs/export-bundle-policy.md` — ZIP/source inclusion policy.
- `docs/release.md` — release checklist and tag suggestion.
