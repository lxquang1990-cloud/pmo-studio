#!/usr/bin/env bash
set -euo pipefail

ROOT_PREFIX="${1:-/tmp/pmo-verify-all}"
cd "$(dirname "$0")/.."

python -m compileall -q pmo_studio
scripts/smoke_phase11.sh "${ROOT_PREFIX}-smoke"
scripts/benchmark.sh "${ROOT_PREFIX}-benchmark"
scripts/negative_checks.py

echo "VERIFY_ALL_PASS"
