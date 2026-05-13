# Traceability

PMO Studio extracts IDs and links from Markdown and Excel artifacts.

## ID types

```text
SRC, BG, BR, REQ, SCR, API, WF, RPT, US, AC, TC, UAT, EST, RISK, ASM, DEC, CR
```

## Direction

Preferred direction is upstream → downstream:

```text
SRC/BG → BR → REQ → SCR/API/WF/RPT → US → AC → TC
REQ/SCR/API/WF/RPT → EST
```

## Supported link patterns

Examples:

```markdown
**Linked source:** SRC-001
**Linked BR:** BR-CORE-001
**Linked REQ:** REQ-CORE-001
**Linked Work Items:** SCR-CORE-001, API-CORE-001, WF-CORE-001
```

The extractor also scans Excel rows and links quotation estimate rows to work item IDs.

## Outputs

```text
traceability/graph.json
traceability/index.json
traceability/rtm.md
traceability/views/validation.json
traceability/views/orphaned.md
traceability/views/broken-links.md
traceability/views/missing-upstream.md
```

## Validation

```bash
python -m pmo_studio.cli trace <slug> --validate
```

Checks:

- broken edges;
- orphan IDs;
- missing upstream links.
