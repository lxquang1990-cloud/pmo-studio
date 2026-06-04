# PMO Studio v5.1

[![PMO Studio Verify](https://github.com/lxquang1990-cloud/pmo-studio/actions/workflows/verify.yml/badge.svg)](https://github.com/lxquang1990-cloud/pmo-studio/actions/workflows/verify.yml)
[![Release Check](https://github.com/lxquang1990-cloud/pmo-studio/actions/workflows/release.yml/badge.svg)](https://github.com/lxquang1990-cloud/pmo-studio/actions/workflows/release.yml)

PMO Studio is an offline-first Documentation Operating System for software projects. It generates and governs PO/PM/BA/IC artifacts: Stage 0 intake, PRD, BRD, SRS, user stories, acceptance criteria, test cases, quotation, fit-gap, configuration workbook, traceability, quality gates, baseline/change requests, and export packs.

## Current milestone

```text
PMO Studio v5.1.0 — detailed customer quotation generator, model-first BA pipeline, quality intelligence, delivery packs, traceability PASS, customer export ready
```

## Core principles

- **Offline-first:** default LLM provider is `noop`; 9Router is opt-in for generation/review.
- **Security-first:** original sources are untrusted; redacted sources are used for generation/LLM flows.
- **Traceable:** IDs and links are extracted into RTM/graph.
- **Governed:** official baseline/sign-off/quotation require human approval.
- **Portable:** CLI, Telegram/OpenClaw adapter, HTML/DOCX/ZIP exports.

## Install / dev

Fresh clone:

```bash
git clone https://github.com/lxquang1990-cloud/pmo-studio.git
cd pmo-studio

python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pmo --help
```

See [INSTALL.md](INSTALL.md) for detailed setup and troubleshooting.

## Quick start

### One-command demo

```bash
# From the cloned repository root: ./pmo-studio
python -m pmo_studio.cli --root /tmp/pmo-demo demo asset-management --force
```

Expected result:

```text
Quality: 26/26 passed, failed=0
Traceability: PASS
Lifecycle: EXPORTED
Latest export: /tmp/pmo-demo/asset-management-demo/exports/customer/asset-management-demo-pmo-bundle.zip
```

The demo uses the bundled source brief at [`examples/asset-management-source.md`](examples/asset-management-source.md) and runs fully offline with `--llm noop`.

For normal customer work, prefer the [Golden Path](docs/golden-path.md). Review [Known Limitations](docs/known-limitations.md) before sending externally.

### Web-doc-agent discovery ingest

PMO Studio can ingest read-only browser/web-doc-agent discovery captures and turn them into governed BA QA artifacts. The crawler/browser phase remains outside PMO Studio; PMO Studio shapes the evidence into Markdown + Excel test case packs.

```bash
python -m pmo_studio.cli --root /tmp/pmo-demo init pms-ai-webdoc \
  --customer 'PVCFC' \
  --product 'PMS AI' \
  --brief 'AI statistical QA from web-doc-agent discovery'

python -m pmo_studio.cli --root /tmp/pmo-demo webdoc-ingest pms-ai-webdoc \
  --discovery-dir /path/to/web-doc-agent/discovery/browser
```

Generated artifacts:

```text
artifacts/ba/05-test-cases.md
artifacts/ba/05-test-cases.xlsx
artifacts/webdoc/discovery-summary.md
```

Guardrails: ingest is evidence-only and read-only; it does not log in, submit, approve, create, edit, or delete target application data.

### Manual flow

```bash
python -m pmo_studio.cli --root /tmp/pmo-demo init asset-management-demo \
  --customer 'Demo Asset Customer' \
  --product 'Asset Management Demo' \
  --brief 'Generate a client-ready PMO documentation pack for an Asset Management MVP.' \
  --domain-pack bteco \
  --source examples/asset-management-source.md

python -m pmo_studio.cli --root /tmp/pmo-demo generate asset-management-demo all \
  --from-sources \
  --llm noop \
  --no-refine

python -m pmo_studio.cli --root /tmp/pmo-demo trace asset-management-demo --validate
python -m pmo_studio.cli --root /tmp/pmo-demo run-gates asset-management-demo --include-c --llm noop
python -m pmo_studio.cli --root /tmp/pmo-demo export asset-management-demo --format all --profile customer
python -m pmo_studio.cli --root /tmp/pmo-demo summary asset-management-demo
```

Generated files will be under `/tmp/pmo-demo/asset-management-demo/`.

## Project folder isolation

PMO Studio uses one isolated folder tree per project. With the default root, projects live under:

```text
~/pmo-projects/<project-slug>/
```

Every command is scoped to that project root:

```text
~/pmo-projects/<project-slug>/
├── config.json
├── state.json
├── source/
│   ├── uploads/      # original uploaded files; never included in customer ZIP
│   └── redacted/     # sanitized/converted source used by generators
├── artifacts/        # PO/PM/BA/IC generated outputs
├── quality/          # Gate A/B/C results and summary
├── traceability/     # RTM and graph outputs
├── exports/          # customer/management export packages
├── review/           # review checklist + sign-off state
└── metrics/          # run metrics
```

Generators read only `source/redacted/` inside the current project folder and write outputs only under that same project folder. The regression suite includes project-isolation tests to prevent cross-project source leakage.

## v1.1 workflow: domain packs, templates, sign-off, dashboard

Domain routing is project-local and source-driven:

- Asset Management source → `asset_management` domain pack.
- LegalIQ / legal source → `legal_ai` domain pack.
- CRM source → `crm` domain pack.
- eOffice/HSE/Digital Signature/PMS/HRM/Procurement/LMS sources → matching YAML domain packs.
- Unknown/new domain source → `generic` source-driven fallback, never Asset Management fallback.

Domain packs live in:

```text
pmo_studio/domain/packs/*.yaml
```

BA artifacts are rendered through versioned templates:

```text
pmo_studio/templates/ba/v1/prd.md.tmpl
pmo_studio/templates/ba/v1/brd.md.tmpl
pmo_studio/templates/ba/v1/srs.md.tmpl
pmo_studio/templates/ba/v1/us.md.tmpl
pmo_studio/templates/ba/v1/test_cases.md.tmpl
```

Each generated Markdown artifact includes metadata such as `template_id`, `template_version`, and `domain_pack`.

Recommended release workflow for a new project:

```bash
pmo --root ~/pmo-projects init <slug> --customer '<customer>' --source <source-file>
pmo --root ~/pmo-projects detect-domain <slug>
pmo --root ~/pmo-projects generate <slug> all --from-sources --llm noop --no-refine
pmo --root ~/pmo-projects trace <slug> --validate
pmo --root ~/pmo-projects run-gates <slug> --include-c --llm noop
pmo --root ~/pmo-projects export <slug> --format all --profile customer
pmo --root ~/pmo-projects index <slug>
pmo --root ~/pmo-projects signoff <slug> Final approved --by '<reviewer>' --note 'Ready for customer'
```

After final sign-off, exports are locked by default. To intentionally regenerate an export after approval:

```bash
pmo --root ~/pmo-projects export <slug> --format all --profile customer --force
```

Dashboard outputs:

```text
<project>/PROJECT_INDEX.md
<project>/index.html
<project>/exports/management/index.html
```

## v1.2 governance and one-command pipeline

Artifact manifests capture source/template/domain/generator hashes for auditability:

```bash
pmo --root ~/pmo-projects manifest <slug>
```

Manifest output:

```text
<project>/artifacts/manifest.json
```

Template governance commands:

```bash
pmo templates list
pmo templates validate
```

One-command pipeline for a new project:

```bash
pmo --root ~/pmo-projects run-project <slug> \
  --source ./source.md \
  --customer "Customer Name" \
  --product "Product Name" \
  --llm noop \
  --profile customer
```

This runs:

```text
init → detect-domain → generate all → trace validate → run-gates → export all → index → manifest → summary
```

Optional final sign-off:

```bash
pmo --root ~/pmo-projects run-project <slug> --source ./source.md --signoff-final --by "Reviewer"
```

v1.2 sample benchmark:

```bash
pmo --root /tmp/pmo-v12 eval --benchmark --samples asset-legaliq-crm --no-docx --llm noop
```

Expected sample benchmark coverage:

```text
Asset Management
LegalIQ
CRM
```

## v1.3 domain pack v2 enrichment

Domain packs now support business knowledge sections beyond keywords/modules/roles:

```yaml
pack_version: 2
workflows:
  - approval workflow
reports:
  - operational dashboard
integrations:
  - SSO
risk_factors:
  - data migration
acceptance_presets:
  - Role-based access is enforced
```

The render context uses these sections to produce more domain-specific BRD/SRS/AC content while staying offline-first.

## v1.4 professional DOCX and PDF-ready export

DOCX exports include professional document-control sections:

```text
cover page
header/footer
document control table
approval/sign-off table
change history
artifact index
rendered Markdown tables
```

PDF generation remains dependency-light by default. PMO Studio emits a print-optimized HTML dashboard that can be converted to PDF by browser/CI tooling:

```bash
pmo --root ~/pmo-projects export <slug> --format pdf-html --profile customer
```

Output:

```text
<project>/exports/customer/pmo-dashboard-print-ready.html
```

`--format all` also includes this PDF-ready HTML artifact.

## v1.5 real PDF and release package automation

Real PDF export is available via a lightweight ReportLab backend:

```bash
pmo --root ~/pmo-projects export <slug> --format pdf --profile customer
```

Output:

```text
<project>/exports/customer/pmo-documentation-pack.pdf
```

`--format all` includes both the real PDF and the print-ready HTML fallback.

Release/package verification:

```bash
make release-check
make dist
```

GitHub release workflow builds and uploads `dist/*` for version tags.

## v1.6 domain management CLI

Manage YAML domain packs from the CLI:

```bash
pmo domains list
pmo domains inspect crm
pmo domains validate
pmo domains validate crm
pmo domains scaffold banking --label "Banking"
pmo domains benchmark crm
```

Domain validation checks the required v2 knowledge sections: workflows, reports, integrations, risk factors, and acceptance presets.

## v1.7 Telegram document workflow

PMO Studio includes a Telegram-oriented preparation workflow that does not send messages or store bot tokens. It runs the project pipeline and writes a delivery manifest for OpenClaw/Telegram adapters.

```bash
pmo --root ~/pmo-projects telegram prepare crm-demo \
  --source ./source.docx \
  --customer "Customer" \
  --product "CRM" \
  --chat-id "telegram:640968010" \
  --llm noop
```

Delivery manifest:

```text
<project>/exports/customer/telegram-delivery.json
```

The manifest lists individual files to send, including DOCX, PDF, quotation XLSX, bundle ZIP, dashboard HTML, and artifact manifest. Individual file delivery is preferred when ZIP upload is unreliable.

## v2.5 Customer-ready Review Mode

Customer-ready Review Mode produces a practical dashboard for reviewing generated PMO artifacts before sending to a customer. It checks artifact presence, placeholders, template leakage, explicit scope/assumptions, testability cues, and integrates Quality Intelligence findings into suggested regeneration guidance.

```bash
pmo customer-review <slug>
```

Outputs:

```text
<project>/quality/customer-review.json
<project>/quality/customer-review.md
<project>/quality/customer-review.html
```

The Web UI now generates and exposes the customer review report when running a project.

## v2.4 Quality Intelligence

Quality Intelligence adds source-grounded checks for domain drift, source coverage gaps, traceability gaps, unrendered template tokens, and duplicate key IDs.

```bash
pmo quality-intel <slug>
```

Outputs:

```text
<project>/quality/intelligence.json
<project>/quality/intelligence.md
```

The Web UI now includes Quality Intelligence as a downloadable artifact when present.

## v2.3 Real Telegram Bot Workflow

PMO Studio now has a stateful Telegram workflow engine for provider adapters such as OpenClaw. It stores session state per chat, asks for missing metadata, runs the PMO pipeline, and returns a delivery manifest. It still does not store bot tokens or send provider messages directly.

```bash
pmo telegram ingest --chat-id telegram:640968010 --source ./brief.md
pmo telegram ingest --chat-id telegram:640968010 --slug crm-demo --customer "Customer" --product "CRM"
pmo telegram run-session --chat-id telegram:640968010 --llm noop --force
pmo telegram session --chat-id telegram:640968010
```

Session files are stored under `<root>/_telegram_sessions/`. Generated delivery manifests list individual DOCX/PDF/XLSX/ZIP/dashboard/manifest attachments for robust Telegram delivery.

## v2.2 Domain Pack Studio

Domain Pack Studio adds UI and CLI support for domain pack lifecycle management.

Web UI:

```text
/domains                    list/scaffold/import domain packs
/domains?selected=crm       inspect, validate, export YAML, append field values
```

CLI additions:

```bash
pmo domains update crm keywords "renewal, upsell"
pmo domains export crm --out-dir ./domain-exports
pmo domains import ./banking.yaml --force
```

Supported managed fields: keywords, modules, workflows, reports, integrations, risk_factors, acceptance_presets, quotation_defaults.

## v2.1 Web UI hardening

The local Web UI now includes a project detail dashboard, source file upload, run status JSON, clearer error pages, safer non-local bind warning, and a download center.

```bash
pmo web --root ~/pmo-projects --host 127.0.0.1 --port 8765
```

Routes:

```text
/                 project list + run form
/project/<slug>   project detail, quality, traceability, downloads
/status?slug=...  web run status JSON
/download?path=... safe root-bounded artifact download
```

Supported source input: pasted text or uploaded `.md`, `.txt`, `.docx`, `.pdf` files. The server remains local-first; when binding a non-local host it prints a warning to use Tailscale/auth reverse proxy.

## v2.0 local Web UI MVP

Run the local-first Web UI:

```bash
pmo web --root ~/pmo-projects --host 127.0.0.1 --port 8765
# or
pmo-web --root ~/pmo-projects
```

Features:

```text
- Create project from source Markdown/text form
- Run full PMO pipeline offline with noop LLM
- List recent projects
- Download DOCX, PDF, quotation XLSX, and delivery manifest
```

The Web UI is local-first and binds to `127.0.0.1` by default. Do not expose it publicly without an auth/reverse-proxy layer.

## CLI reference


### Demo

```bash
python -m pmo_studio.cli demo asset-management --force
scripts/demo_asset_management.sh /tmp/pmo-asset-demo
```

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
