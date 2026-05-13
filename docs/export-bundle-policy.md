# Export & Bundle Policy

PMO Studio supports HTML, DOCX, ZIP and all-in-one export.

## Commands

```bash
python -m pmo_studio.cli export <slug> --format html
python -m pmo_studio.cli export <slug> --format docx
python -m pmo_studio.cli export <slug> --format zip
python -m pmo_studio.cli export <slug> --format all
```

## ZIP bundle contents

```text
bundle-manifest.json
artifacts/
traceability/
quality/
baselines/
change-requests/
metrics/aggregated/
exports/management/index.html
exports/client-ready/pmo-documentation-pack.docx
```

## Source policy

Original uploaded sources are never included in ZIP bundles.

Optional flag:

```bash
--include-redacted-sources
```

Only includes:

```text
source/redacted/
```

Never includes:

```text
source/uploads/
```

## Telegram/OpenClaw media hints

When `/pmo export ... --send` is used, the adapter returns:

```text
MEDIA:/path/to/exported-file
```

OpenClaw-compatible surfaces can attach/render the file.
