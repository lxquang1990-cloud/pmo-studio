# PMO Studio Golden Path

This is the recommended operator flow for a normal customer documentation package.

## Goal

Turn one customer source brief into a governed delivery pack with traceability, quality reports, and customer-ready exports.

## Default mode

Use offline deterministic mode first:

```bash
pmo --root ~/pmo-projects run-project <project-slug> \
  --source ./source.md \
  --customer "Customer Name" \
  --product "Product Name" \
  --domain-pack generic \
  --llm noop \
  --profile customer
```

Use `--llm 9router` only when the source is approved for LLM processing and the redaction policy is acceptable.

## Expected outputs

After a successful run, inspect:

```text
~/pmo-projects/<project-slug>/
├── artifacts/        # PRD, BRD, SRS, user stories, test cases, quotation
├── traceability/     # RTM and graph
├── quality/          # gate and quality reports
├── exports/customer/ # customer-ready ZIP/DOCX/PDF/HTML outputs
├── PROJECT_INDEX.md
└── index.html
```

## Validation commands

```bash
pmo --root ~/pmo-projects trace <project-slug> --validate
pmo --root ~/pmo-projects run-gates <project-slug> --include-c --llm noop
pmo --root ~/pmo-projects quality-intel <project-slug>
pmo --root ~/pmo-projects summary <project-slug>
```

## Export policy

Original uploads under `source/uploads/` must never be included in customer bundles. Redacted sources are excluded by default and only included with explicit `--include-redacted-sources`.

```bash
pmo --root ~/pmo-projects export <project-slug> --format all --profile customer
```

## Human review gate

Do not send a PMO Studio package as final customer output without human BA/PM review. Minimum review checklist:

- Scope and out-of-scope are correct.
- Requirement IDs are traceable.
- User stories are specific enough to implement.
- Test cases cover business-critical workflows.
- Quotation mandays and assumptions are defensible.
- No confidential source material leaked into customer exports.
