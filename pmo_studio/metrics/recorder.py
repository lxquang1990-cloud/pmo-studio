"""Lightweight project metrics recorder for generation/gate runs.

Includes dry-run token estimation (no API needed) and cost tracking for
observability when real LLM calls are made.
"""
from __future__ import annotations

import json
import os
import re
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# ── Token estimation (dry-run, offline) ──────────────────────────────────────

# Per-model pricing in $/1M tokens (input, output)
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    # 9Router (self-hosted, $0 per-token cost)
    "9Router/Tier1": (0.0, 0.0),
    "9Router/Tier2": (0.0, 0.0),
    "9Router/Tier3": (0.0, 0.0),
    # Other providers (paid, per 1M tokens)
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o": (2.50, 10.00),
    "google/gemini-flash-2.0": (0.10, 0.40),
    "google/gemini-pro-2.5": (1.25, 10.00),
    "deepseek/deepseek-chat": (0.27, 1.10),
    "anthropic/claude-sonnet-4": (3.00, 15.00),
    "meta-llama/llama-4-maverick": (0.20, 0.60),
    "default": (0.50, 2.00),
}

_TOKEN_CHARS_PER_VI = 2.8    # ~1 token per 2.8 chars for Vietnamese
_TOKEN_CHARS_PER_EN = 4.0    # ~1 token per 4 chars for English/other


@dataclass
class TokenEstimate:
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    model: str = "dry-run"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class TokenEstimator:
    """Offline token counter using character-length heuristics.

    No API call needed — safe for dry-run estimation and observability.
    """

    @staticmethod
    def count_tokens(text: str) -> int:
        """Estimate token count from text length."""
        if not text:
            return 0
        vi_chars = len(re.findall(r'[\u00C0-\u1EF9\u0102\u0103\u0110\u0111\u0168\u0169\u01A0\u01A1\u01AF\u01B0\u0200-\u024F]', text))
        ascii_chars = len(text) - vi_chars
        return int(ascii_chars / _TOKEN_CHARS_PER_EN + vi_chars / _TOKEN_CHARS_PER_VI)

    @staticmethod
    def estimate_cost(model: str, input_tokens: int = 0, output_tokens: int = 0) -> tuple[float, float, float]:
        """Return (input_cost_usd, output_cost_usd, total_cost_usd)."""
        in_rate, out_rate = _MODEL_PRICING.get(model, _MODEL_PRICING["default"])
        in_cost = (input_tokens / 1_000_000) * in_rate
        out_cost = (output_tokens / 1_000_000) * out_rate
        return in_cost, out_cost, in_cost + out_cost

    @staticmethod
    def estimate(text_in: str, text_out: str, model: str = "dry-run") -> TokenEstimate:
        """Full estimate from prompt + response text."""
        in_tok = TokenEstimator.count_tokens(text_in)
        out_tok = TokenEstimator.count_tokens(text_out)
        in_cost, out_cost, total = TokenEstimator.estimate_cost(model, in_tok, out_tok)
        return TokenEstimate(input_tokens=in_tok, output_tokens=out_tok,
                             input_cost_usd=round(in_cost, 6), output_cost_usd=round(out_cost, 6),
                             total_cost_usd=round(total, 6), model=model)


def _load_secrets_env() -> dict[str, str]:
    """Load API keys from /etc/snailbot/secrets.env if readable."""
    if os.environ.get("PMO_DISABLE_SECRETS_ENV") == "1":
        return {}
    secrets: dict[str, str] = {}
    for candidate in ["/etc/snailbot/secrets.env", os.path.expanduser("~/.pmo-secrets.env")]:
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        secrets[k.strip()] = v.strip().strip('"').strip("'")
        except (OSError, PermissionError):
            continue
    return secrets


# ── Existing metrics recorder (extended) ─────────────────────────────────────

@dataclass
class MetricEvent:
    timestamp: str
    event: str
    data: dict[str, Any] = field(default_factory=dict)

class MetricsRecorder:
    def __init__(self, project_root: Path, run_id: str | None = None):
        self.project_root = project_root
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.events: list[MetricEvent] = []
        self.started_at = time.monotonic()
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0

    def record(self, event: str, **data: Any) -> None:
        self.events.append(MetricEvent(datetime.now(timezone.utc).isoformat(), event, data))

    @contextmanager
    def span(self, event: str, **data: Any) -> Iterator[None]:
        start = time.monotonic()
        self.record(f"{event}.start", **data)
        try:
            yield
            self.record(f"{event}.end", duration_seconds=round(time.monotonic() - start, 4), **data)
        except Exception as exc:
            self.record(f"{event}.error", duration_seconds=round(time.monotonic() - start, 4), error=type(exc).__name__, message=str(exc), **data)
            raise

    def record_llm_call(self, event: str, prompt: str, response: str, model: str = "dry-run", llm: str = "noop", **extra: Any) -> TokenEstimate:
        """Record an LLM call with token/cost estimation."""
        est = TokenEstimator.estimate(prompt, response, model=model)
        self._total_input_tokens += est.input_tokens
        self._total_output_tokens += est.output_tokens
        self._total_cost_usd += est.total_cost_usd
        self.record(event, model=model, llm=llm,
                     input_tokens=est.input_tokens, output_tokens=est.output_tokens,
                     input_cost_usd=est.input_cost_usd, output_cost_usd=est.output_cost_usd,
                     total_cost_usd=est.total_cost_usd, **extra)
        return est

    def save(self) -> Path:
        out = self.project_root / "metrics" / "runs" / f"{self.run_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": self.run_id,
            "duration_seconds": round(time.monotonic() - self.started_at, 4),
            "event_count": len(self.events),
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_usd": round(self._total_cost_usd, 6),
            "events": [asdict(e) for e in self.events],
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self._write_aggregate(payload)
        return out

    def _write_aggregate(self, payload: dict[str, Any]) -> None:
        out = self.project_root / "metrics" / "aggregated" / "latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_9router_key() -> str | None:
    """Return 9Router API key from env or secrets file."""
    key = os.environ.get("9ROUTER_API_KEY", "")
    if key:
        return key
    return _load_secrets_env().get("9ROUTER_API_KEY")
