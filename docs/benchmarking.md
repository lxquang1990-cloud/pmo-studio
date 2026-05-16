# PMO Studio Benchmarking

PMO Studio benchmarks are designed to measure repeatable delivery readiness, not just whether files were generated.

## Built-in benchmark

```bash
pmo --root /tmp/pmo-benchmark eval --benchmark --samples asset-legaliq-crm --no-docx --llm noop
```

This validates multiple source-driven cases for:

- Quality gate pass rate
- Traceability validation
- Minimum trace edge count
- ID type coverage
- Redaction status
- Manifest item count
- Dashboard/export existence
- Quotation sanity bounds

## Real-world benchmark foundation

The built-in benchmark is a structural baseline. A real customer benchmark should add human-scored review dimensions:

| Dimension | Question |
|---|---|
| Completeness | Did the package cover the real source scope? |
| Correctness | Are requirements and workflows true to the business? |
| Specificity | Can engineers implement from the user stories/SRS? |
| Testability | Are acceptance criteria and UAT cases concrete? |
| Estimate defensibility | Are mandays, assumptions, and exclusions explainable? |
| Customer readiness | How much BA/PM rework is needed before sending? |

## Recommended real-world case format

Create a sanitized source file and a rubric file per case:

```text
evals/real-world/<case-id>/
├── source.md
├── expected.json
└── review-rubric.md
```

`expected.json` should include:

```json
{
  "case_id": "legal-ai-customer-style",
  "domain_pack": "legal_ai",
  "expected_modules": ["Legal Q&A", "Authorization", "Contract Review"],
  "out_of_scope": ["automatic legal advice without human review"],
  "expected_manday_min": 40,
  "expected_manday_max": 240
}
```

## Pass criteria

A case should not be considered customer-ready unless both are true:

1. Automated benchmark score passes the configured threshold.
2. Human BA/PM review marks the output acceptable or acceptable with minor rework.
