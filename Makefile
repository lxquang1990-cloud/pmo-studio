.PHONY: compile smoke benchmark negative verify clean

PYTHON ?= python
SMOKE_ROOT ?= /tmp/pmo-smoke-phase11
BENCH_ROOT ?= /tmp/pmo-benchmark

compile:
	$(PYTHON) -m compileall -q pmo_studio

smoke:
	scripts/smoke_phase11.sh $(SMOKE_ROOT)

benchmark:
	scripts/benchmark.sh $(BENCH_ROOT)

negative:
	scripts/negative_checks.py

verify: compile smoke benchmark negative
	@echo "VERIFY_ALL_PASS"

clean:
	rm -rf .pytest_cache .mypy_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
