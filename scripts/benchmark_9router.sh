#!/usr/bin/env bash
set -euo pipefail
# PMO Studio benchmark with 9Router LLM generation.
# Requires 9ROUTER_API_KEY (autoloaded from models.json if not in env).

ROOT="${1:-/tmp/pmo-benchmark-9router}"
cd "$(dirname "$0")/.."

# Auto-detect 9Router API key from OpenClaw models.json if not already set
if [ -z "${9ROUTER_API_KEY:-}" ]; then
  KEY_FROM_JSON=$(python3 -c "
import json
with open('$HOME/.openclaw/agents/main/agent/models.json') as f:
    data = json.load(f)
print(data['providers']['9router']['apiKey'])
" 2>/dev/null || echo "")
  if [ -n "$KEY_FROM_JSON" ]; then
    export 9ROUTER_API_KEY="$KEY_FROM_JSON"
  fi
fi

MODEL="${PMO_9ROUTER_BENCHMARK_MODEL:-Tier2}"

echo "=== PMO Studio 9Router Benchmark ==="
echo "Model: $MODEL"
echo "Key: ${9ROUTER_API_KEY:0:8}... (${#9ROUTER_API_KEY} chars)" 2>/dev/null || echo "Key: not set"

python -m compileall -q pmo_studio
rm -rf "$ROOT"
python -m pmo_studio.cli --root "$ROOT" scaffold
python -m pmo_studio.cli --root "$ROOT" eval --benchmark --llm 9router --model "$MODEL" --no-docx

python - <<PY
from pathlib import Path
import json
root = Path('$ROOT') / 'eval-runs' / 'benchmark'
results = json.loads((root/'results.json').read_text())
assert results['passed'], results
print('BENCHMARK_9ROUTER_PASS', results['score'], root/'report.md')
PY
