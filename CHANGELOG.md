# Changelog

## 1.0.0rc2 - 2026-05-12

### Added
- GitHub Actions workflow templates for verify and release checks.
- `scripts/install_check.sh` to validate editable install and console scripts.
- **Lifecycle UX:** summary, archive, clone commands; lifecycle state management (INITIATED→BASELINED→ARCHIVED); `sync-lifecycle`.
- **Domain Intelligence (4 domain packs):** eOffice, Ký số (Digital Signature), HSE, PMS with domain-specific prompts, terminology, acronyms, and roles. `--domain-pack` argument on `init`.
- **Observability:** dry-run token counting (`TokenEstimator`) with heuristic char-length method; per-model cost estimation; `record_llm_call()` in `MetricsRecorder`.
- **Provider hardening:** auto-load API keys from `/etc/snailbot/secrets.env`; `LLMResponse` struct with token counts; `api_key_status()` helper.
- **Provider migration:** Replaced OpenRouter with 9Router (self-hosted, OpenAI-compatible). `NineRouterClient` at `http://100.103.10.31:20128/v1`. Models: `9Router/Tier1`, `9Router/Tier2`, `9Router/Tier3`. `--llm 9router` in CLI/Telegram. Legacy `--llm openrouter` raises a clear migration error.
- **9Router SSE trailer fix:** Strips `data: [DONE]` appended by 9Router streaming responses before JSON parsing.
- **Live 9Router verification:** Tier1 (`deepseek-v4-pro`) and Tier2 models confirmed operational — real API calls with token tracking work end-to-end.
- **PMO Studio skill v1.0:** Updated to reflect 9Router provider, lifecycle commands (`summary`, `clone`, `archive`, `sync-lifecycle`, `list`, `recent`), `--domain-pack` argument, and full v1.0 capability list.
- **Pytest suite (78 tests):** 5 test files covering provider (16 tests), recorder (18), factory (11), lifecycle (6), domain (23) + existing core (2). Integrated into CI verify.yml with coverage.
- **Coverage config:** Added `[tool.coverage.run]` and `[tool.coverage.report]` to pyproject.toml; `pytest-cov` as optional dev dependency.
- **9Router-powered benchmark infrastructure:** Added `--llm`/`--model` to `eval` CLI subcommand; `run_benchmark()` and `_run_case()` now accept `llm_provider`/`llm_model` and conditionally build+pass NineRouterClient to BA generator.
- **`scripts/benchmark_9router.sh`:** Wrapper script that auto-extracts 9ROUTER_API_KEY from OpenClaw models.json and runs the full benchmark with `--llm 9router --model Tier2`.
- **LLM-Powered Gate B/C Reviewer:** `build_gate_reviewer()` factory builds `JSONLLMReviewer` backed by 9Router Tier2 for semantic artifact review. Wired into `run_all_gates()`, `refine_markdown_artifact()`, `cmd_run_gates` (CLI `--llm 9router`), and benchmark `_run_case()`. Gate B/C layers can now use real LLM reviews instead of deterministic pattern-matching. Verified: single-gate 9Router Tier2 review produces structured JSON checks with specific evidence.
- **LLM Gate Benchmark Comparison:** Added `scripts/benchmark_compare_llm_gates.py` for full deterministic-vs-LLM gate benchmark reports and `scripts/benchmark_compare_llm_gates_focused.py` for fast focused comparison on eOffice PRD/BRD. `run_benchmark()` now separates artifact generation provider (`llm_provider`) from gate reviewer provider (`gate_reviewer_provider`) so LLM Gate B/C can be benchmarked on deterministic artifacts without invoking LLM generation.
- **LLM Gate Cache + Timeout:** Added `pmo_studio/llm/cache.py` (`LLMReviewCache`) and hardened `JSONLLMReviewer` with file-backed cache, per-review timeout wiring, and optional fail-closed fallback (`--gate-fallback`). CLI `run-gates`, full benchmark comparison, and focused comparison scripts now support `--gate-timeout`, cache directories, and fallback-safe LLM review runs.
- **LLM Reviewer Regression Tests:** Added `tests/test_llm_reviewer_cache.py` covering cache roundtrip, cache hits, fallback-on-error fail-closed behavior, error raising without fallback, and noop reviewer factory. Test suite now has 83 passing tests.
- **LLM Gate Operations Docs:** Added `docs/llm-gate-operations.md` documenting deterministic vs 9Router reviewer modes, cache keys, timeout/fallback policy, benchmark comparison scripts, and recommended CI vs human QA usage.

### Release
- Version bumped to `1.0.0rc2` in `pyproject.toml` and `pmo_studio/__init__.py`.
- Built release artifacts: `dist/pmo_studio-1.0.0rc2-py3-none-any.whl` and `dist/pmo_studio-1.0.0rc2.tar.gz`.
- Added `dist/SHA256SUMS` and `dist/release-manifest.json` for artifact integrity and release metadata.
- Added `scripts/release_audit.py` for non-mutating release readiness checks.
- README updated with 9Router, LLM gate comparison, artifact integrity commands, and documentation index.
- Release checklist updated with suggested tag `v1.0.0rc2`.

## 1.0.0rc1 - 2026-05-12

### Added
- PMO Studio v2.1 project scaffold and CLI.
- Stage 0 source intake and security preprocessing.
- PO/PM/BA/IC artifact generators.
- Source-driven BA generation with offline deterministic fallback and optional OpenRouter.
- Gate A/B/C quality framework.
- Advanced Excel Gate A checks for quotation, fit-gap, and config workbook.
- Traceability graph, RTM, and validator.
- Baseline manifest, diff, and Change Request impact analysis.
- HTML, DOCX, and ZIP bundle exporters.
- Project registry and recent-project fallback.
- Telegram/OpenClaw command adapter with media hints and approval guard.
- Metrics recorder and Gate feedback refinement loop.
- Multi-project benchmark suite: eOffice, Digital Signature, HSE.
- README, documentation pages, smoke/benchmark/negative scripts.
- Makefile and `scripts/verify_all.sh` release verification.

### Safety
- Original sources are never included in ZIP bundles.
- Redacted sources are included only with `--include-redacted-sources`.
- Baseline/sign-off/official quotation require approval in chat adapter.
- Default LLM mode remains `noop`.

### Verification
- `scripts/smoke_phase11.sh` PASS.
- `scripts/benchmark.sh` PASS, benchmark score 94.12%.
- `scripts/negative_checks.py` PASS.
