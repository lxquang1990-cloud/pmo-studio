#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/tmp/pmo-release-check}"
rm -rf "$ROOT"
python3 -m compileall -q pmo_studio
python3 -m pytest -q
python3 -m pmo_studio.cli --root "$ROOT" eval --benchmark --samples asset-legaliq-crm --no-docx --llm noop
rm -rf dist
python3 -m pip wheel . --no-deps --wheel-dir dist
