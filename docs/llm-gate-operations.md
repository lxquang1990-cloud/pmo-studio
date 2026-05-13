# LLM Gate Operations

PMO Studio can run Gate B/C semantic reviews using the deterministic local reviewer or a 9Router-backed LLM reviewer.

## Default mode: deterministic

Deterministic gates are the CI-safe default:

```bash
pmo run-gates <project-slug> --include-c
```

This mode is offline, fast, and stable for `verify_all.sh`.

## LLM reviewer mode

Use 9Router for stricter semantic Gate B/C review:

```bash
pmo run-gates <project-slug> --include-c \
  --llm 9router \
  --model Tier2 \
  --gate-timeout 60 \
  --gate-fallback
```

Options:

| Option | Purpose |
|---|---|
| `--llm 9router` | Use 9Router-backed `JSONLLMReviewer` for Gate B/C |
| `--model Tier2` | Recommended stable model for review |
| `--gate-cache <dir>` | File-backed cache for review results; defaults to `~/.cache/pmo-studio/gate-review` |
| `--gate-timeout <seconds>` | Per-review network timeout |
| `--gate-fallback` | Fail closed instead of raising if the LLM call errors/timeouts |

## Cache behavior

LLM reviews are keyed by:

- provider
- model
- stage
- layer
- artifact SHA256
- context SHA256
- rubric JSON

A cache hit returns the prior structured JSON review without another network call.

## Failure behavior

Without `--gate-fallback`, LLM exceptions are raised so operators see hard failures.

With `--gate-fallback`, the reviewer returns failing checks with evidence like:

```text
LLM reviewer error: <exception>
```

This is fail-closed: quality gates do not pass silently when the LLM is unavailable.

## Benchmark comparison

Full comparison:

```bash
python scripts/benchmark_compare_llm_gates.py \
  --root /tmp/pmo-llm-gate-compare \
  --model Tier2 \
  --gate-timeout 60 \
  --gate-fallback
```

Focused fast comparison:

```bash
python scripts/benchmark_compare_llm_gates_focused.py \
  --root /tmp/pmo-llm-gate-focused \
  --model Tier2 \
  --gate-timeout 45 \
  --gate-fallback
```

Use focused comparison when full benchmark is slow due to repeated network calls.

## Recommended policy

- CI/release: deterministic only.
- Human QA / pre-client review: LLM Gate B/C with cache and fallback.
- Full benchmark: run manually when 9Router is healthy; otherwise use focused comparison.
