"""Tests for metrics/recorder module — TokenEstimator, MetricsRecorder."""
from pathlib import Path
import tempfile
from pmo_studio.metrics.recorder import (
    TokenEstimator, TokenEstimate, MetricsRecorder,
    _MODEL_PRICING, get_9router_key, _load_secrets_env,
)

# ── TokenEstimator.count_tokens ─────────────────────────────────────────────

def test_count_tokens_empty():
    assert TokenEstimator.count_tokens("") == 0

def test_count_tokens_english():
    # ~4 chars per token for English
    tokens = TokenEstimator.count_tokens("hello world")
    assert tokens >= 2  # 11 chars / 4 ≈ 2

def test_count_tokens_vietnamese():
    # ~2.8 chars per token for Vietnamese
    tokens = TokenEstimator.count_tokens("xin chào thế giới")
    assert tokens >= 3  # mixed VI/EN: 17 chars → 4 tokens (heuristic)

def test_count_tokens_mixed():
    text = "Hệ thống eOffice Document Management"
    tokens = TokenEstimator.count_tokens(text)
    assert tokens > 0

# ── TokenEstimator.estimate_cost ────────────────────────────────────────────

def test_estimate_cost_known_model():
    in_cost, out_cost, total = TokenEstimator.estimate_cost("openai/gpt-4o-mini", 1000, 500)
    # (1000/1M)*0.15 = 0.00015, (500/1M)*0.60 = 0.0003
    assert round(in_cost, 6) == 0.00015
    assert round(out_cost, 6) == 0.0003
    assert round(total, 6) == 0.00045

def test_estimate_cost_9router_zero():
    in_cost, out_cost, total = TokenEstimator.estimate_cost("9Router/Tier2", 1000, 500)
    assert in_cost == 0.0
    assert out_cost == 0.0
    assert total == 0.0

def test_estimate_cost_unknown_model_fallback():
    in_cost, out_cost, total = TokenEstimator.estimate_cost("nonexistent/model", 1000, 500)
    assert in_cost > 0  # falls back to default pricing

# ── TokenEstimator.estimate ─────────────────────────────────────────────────

def test_estimate_full():
    est = TokenEstimator.estimate("system prompt", "response text", model="openai/gpt-4o-mini")
    assert isinstance(est, TokenEstimate)
    assert est.input_tokens > 0
    assert est.output_tokens > 0
    assert est.total_tokens == est.input_tokens + est.output_tokens
    assert est.total_cost_usd > 0

def test_estimate_vietnamese():
    est = TokenEstimator.estimate(
        "Hệ thống quản lý văn bản và điều hành eOffice",
        "Phản hồi từ hệ thống bằng tiếng Việt",
        model="9Router/Tier2"
    )
    assert est.model == "9Router/Tier2"
    assert est.total_cost_usd == 0.0

# ── _MODEL_PRICING ──────────────────────────────────────────────────────────

def test_9router_models_have_zero_pricing():
    for tier in ["9Router/Tier1", "9Router/Tier2", "9Router/Tier3"]:
        in_rate, out_rate = _MODEL_PRICING[tier]
        assert in_rate == 0.0, f"{tier} input should be $0"
        assert out_rate == 0.0, f"{tier} output should be $0"

def test_pricing_has_default():
    assert "default" in _MODEL_PRICING

# ── MetricsRecorder ─────────────────────────────────────────────────────────

def test_metrics_recorder_init():
    with tempfile.TemporaryDirectory() as tmp:
        m = MetricsRecorder(Path(tmp))
        assert m.run_id
        assert m.project_root == Path(tmp)
        assert len(m.events) == 0

def test_record_event():
    with tempfile.TemporaryDirectory() as tmp:
        m = MetricsRecorder(Path(tmp))
        m.record("test.event", key="value")
        assert len(m.events) == 1
        assert m.events[0].event == "test.event"
        assert m.events[0].data["key"] == "value"

def test_record_llm_call():
    with tempfile.TemporaryDirectory() as tmp:
        m = MetricsRecorder(Path(tmp))
        est = m.record_llm_call("generate.ba", "prompt text", "response text", model="9Router/Tier2", llm="9router")
        assert isinstance(est, TokenEstimate)
        assert m._total_input_tokens > 0
        assert m._total_output_tokens > 0

def test_save_writes_file():
    with tempfile.TemporaryDirectory() as tmp:
        m = MetricsRecorder(Path(tmp), run_id="test-run")
        m.record_llm_call("test.gen", "prompt", "response")
        out = m.save()
        assert out.exists()
        assert "metrics/runs" in str(out)
        assert (Path(tmp) / "metrics/aggregated/latest.json").exists()

def test_span_context_manager():
    with tempfile.TemporaryDirectory() as tmp:
        m = MetricsRecorder(Path(tmp))
        with m.span("generate", persona="ba"):
            pass
        assert len(m.events) == 2
        assert m.events[0].event == "generate.start"
        assert m.events[1].event == "generate.end"
        assert "duration_seconds" in m.events[1].data

def test_span_error_recording():
    with tempfile.TemporaryDirectory() as tmp:
        m = MetricsRecorder(Path(tmp))
        with pytest.raises(ValueError):
            with m.span("generate"):
                raise ValueError("test error")
        assert any(e.event == "generate.error" for e in m.events)

# ── get_9router_key ─────────────────────────────────────────────────────────

def test_get_9router_key_not_set(monkeypatch):
    monkeypatch.delenv("9ROUTER_API_KEY", raising=False)
    monkeypatch.setenv("PMO_DISABLE_SECRETS_ENV", "1")
    key = get_9router_key()
    assert key is None or key == ""

# ── _load_secrets_env ───────────────────────────────────────────────────────

def test_load_secrets_env_returns_dict():
    secrets = _load_secrets_env()
    assert isinstance(secrets, dict)

import pytest
