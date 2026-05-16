# PMO Studio Known Limitations

PMO Studio is a documentation operating system, not a replacement for accountable BA/PM judgment.

## Output quality

- Generated artifacts can be structurally valid while still missing domain-specific nuance.
- Offline `noop` mode is deterministic and useful for repeatability, but may produce shallow wording compared with a reviewed LLM-assisted run.
- LLM-assisted output must be treated as draft content until reviewed by a human BA/PM.

## Estimation

- Manday estimates are planning estimates, not binding commercial commitments.
- Estimates depend on source quality, domain pack quality, assumptions, integrations, and non-functional requirements.
- Final quotation requires human approval.

## Source handling

- Text sources are redacted for common secrets/PII patterns.
- Binary files are currently copied to redacted storage without semantic text extraction/redaction. Do not upload sensitive binary documents unless an external preprocessing step has already sanitized them.
- Prompt-injection detection flags suspicious source text, but does not prove the source is safe.

## Export handling

- Customer bundles exclude original uploads by policy.
- Redacted sources are excluded unless explicitly requested.
- Operators should inspect export manifests before sending deliverables externally.

## Web and chat adapters

- Local Web UI is intended for trusted local operation unless deployed behind proper authentication and reverse proxy controls.
- Telegram/OpenClaw workflows are convenience interfaces; sensitive final approvals should remain explicit and auditable.

## Domain packs

- Domain packs encode reusable assumptions and vocabulary. They improve relevance but can bias output if the source belongs to a different domain.
- Use `generic` or create a new domain pack when no existing pack fits.

## Benchmarking

- Built-in benchmarks validate structural quality, traceability, redaction, and export readiness.
- They are not a substitute for a real customer acceptance benchmark with human-scored artifacts.
