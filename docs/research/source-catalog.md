# PMO Studio Research Source Catalog

Generated: `2026-06-01T02:15:06.398670+00:00`

This catalog is for PMO Studio improvement research. Do not copy third-party content unless license status allows adaptation and attribution is preserved.

## Summary

- manual-review: 2
- permissive: 3

## Sources

| Priority | Risk | License status | Source | Kind | PMO target | Action |
|---|---|---|---|---|---|---|
| high | low | permissive (Apache License 2.0) | [OWASP user security stories](https://github.com/OWASP/user-security-stories) | security-acceptance-criteria | security AC pack, NFR gate, API/auth/audit checklist | Candidate for adapted rubric/template with attribution. |
| high | medium | manual-review (unknown) | [Canaxess accessibility acceptance criteria](https://github.com/canaxess/accessibility-acceptance-criteria) | accessibility-acceptance-criteria | accessibility AC pack and UI/NFR gate | Manual review before implementation. |
| medium | low | permissive (MIT License) | [inDriver handbook acceptance criteria](https://github.com/inDriver/handbook/blob/main/docs/strategy-and-management/acceptance-criteria.md) | acceptance-criteria-guide | user story / AC quality rubric | Candidate for adapted rubric/template with attribution. |
| medium | low | permissive (MIT License) | [RequirementLinter](https://github.com/jonverrier/RequirementLinter) | requirement-quality-linter | vague term detection, compound requirement split rules | Candidate for adapted rubric/template with attribution. |
| medium | medium | manual-review (Other) | [Jam01 SRS Template](https://github.com/jam01/SRS-Template) | srs-template | SRS completeness gate and section coverage | Manual review before implementation. |

## Recommended next implementation queue

1. Security acceptance criteria pack from permissive/approved OWASP-style sources.
2. Accessibility acceptance criteria pack from permissive/approved WCAG-oriented sources.
3. SRS completeness gate improvements for external interfaces, constraints, dependencies, and verification.
4. RTM quality gate for status, priority, source, and test coverage fields.
5. Estimation rubric benchmark with phase/role/risk buffer sanity checks.
