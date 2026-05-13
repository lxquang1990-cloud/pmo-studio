# Quality Gates

PMO Studio uses three gate layers.

## Gate A — structural/local

Runs without LLM.

Markdown checks:

- required headings;
- valid ID format;
- duplicate ID detection.

Excel checks:

- required sheet existence;
- required columns;
- mandatory cells;
- enum values;
- ID format;
- quotation total manday/cost consistency;
- config workbook plaintext secret guard.

## Gate B — semantic readiness

Default deterministic heuristic; optional LLM reviewer.

Typical checks:

- no critical placeholders/TBD;
- clear scope/purpose;
- trace markers exist;
- verification/test markers exist.

## Gate C — business readiness

Used before customer-facing delivery/sign-off.

Typical checks:

- ready for customer review;
- ready for dev/implementation;
- consistent with upstream artifacts;
- no critical open questions.

## Project-wide gate runner

```bash
python -m pmo_studio.cli run-gates <slug>
python -m pmo_studio.cli run-gates <slug> --include-c
```

Writes:

```text
quality/summary.json
quality/gate-a/*.json
quality/gate-b/*.json
quality/gate-c/*.json
```

## Refinement loop

`generate --refine` runs Gate A/B on Markdown artifacts and uses feedback to patch missing trace/scope/verification markers. In LLM mode, feedback is passed to the writer while preserving IDs.
