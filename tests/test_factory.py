"""Tests for LLM factory module."""
import os
import pytest
from pmo_studio.llm.factory import build_llm, llm_help
from pmo_studio.llm.provider import NoopLLMClient, NineRouterClient

# ── build_llm ───────────────────────────────────────────────────────────────

def test_build_noop():
    c = build_llm("noop")
    assert isinstance(c, NoopLLMClient)

def test_build_none():
    # provider="none" → Noop
    c = build_llm("none")
    assert isinstance(c, NoopLLMClient)

def test_build_offline():
    c = build_llm("offline")
    assert isinstance(c, NoopLLMClient)

def test_build_empty_string():
    # Empty provider defaults to noop
    c = build_llm("")
    assert isinstance(c, NoopLLMClient)

def test_build_9router_no_key(monkeypatch):
    monkeypatch.delenv("9ROUTER_API_KEY", raising=False)
    monkeypatch.setenv("PMO_DISABLE_SECRETS_ENV", "1")
    with pytest.raises(RuntimeError, match="9ROUTER_API_KEY"):
        build_llm("9router")

def test_build_9router_with_key():
    os.environ["9ROUTER_API_KEY"] = "sk-test-key"
    try:
        c = build_llm("9router")
        assert isinstance(c, NineRouterClient)
        assert c.api_key == "sk-test-key"
    finally:
        del os.environ["9ROUTER_API_KEY"]

def test_build_9router_with_model_override():
    os.environ["9ROUTER_API_KEY"] = "sk-test"
    try:
        c = build_llm("9router", model="Tier3")
        assert c.default_model == "Tier3"
    finally:
        del os.environ["9ROUTER_API_KEY"]

def test_build_ninerouter_alias():
    os.environ["9ROUTER_API_KEY"] = "sk-test"
    try:
        c = build_llm("ninerouter")
        assert isinstance(c, NineRouterClient)
    finally:
        del os.environ["9ROUTER_API_KEY"]

def test_build_openrouter_raises_clear_error():
    with pytest.raises(ValueError, match="9Router"):
        build_llm("openrouter")

def test_build_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported"):
        build_llm("nonexistent_provider")

# ── llm_help ────────────────────────────────────────────────────────────────

def test_llm_help_mentions_9router():
    text = llm_help()
    assert "9router" in text.lower()

def test_llm_help_mentions_noop():
    text = llm_help()
    assert "noop" in text.lower()
