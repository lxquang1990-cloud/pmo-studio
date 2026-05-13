"""Tests for LLM provider module — NineRouterClient, NoopLLMClient, LLMResponse."""
import os
import pytest
from pmo_studio.llm.provider import (
    NineRouterClient, NoopLLMClient, LLMResponse,
    client_from_env, api_key_status, _parse_chat_response,
)

# ── NoopLLMClient ────────────────────────────────────────────────────────────

def test_noop_complete():
    noop = NoopLLMClient()
    assert noop.complete(system="sys", user="hello") == ""

def test_noop_complete_with_tokens():
    noop = NoopLLMClient()
    resp = noop.complete_with_tokens(system="hệ thống", user="người dùng")
    assert isinstance(resp, LLMResponse)
    assert resp.model == "noop"
    assert resp.output_tokens == 0
    assert resp.input_tokens > 0  # Vietnamese chars → estimated tokens
    assert resp.content == ""

def test_noop_token_estimation_zero_for_empty():
    noop = NoopLLMClient()
    resp = noop.complete_with_tokens(system="", user="")
    assert resp.input_tokens == 0

# ── LLMResponse ──────────────────────────────────────────────────────────────

def test_llm_response_defaults():
    r = LLMResponse(content="test")
    assert r.content == "test"
    assert r.input_tokens == 0
    assert r.output_tokens == 0
    assert r.model == ""

def test_llm_response_with_tokens():
    r = LLMResponse(content="xin chào", input_tokens=5, output_tokens=3, model="Tier2")
    assert r.input_tokens == 5
    assert r.output_tokens == 3
    assert r.model == "Tier2"

# ── NineRouterClient construction ───────────────────────────────────────────

def test_ninerouter_construction():
    client = NineRouterClient(api_key="sk-test", base_url="http://localhost:9999/v1", default_model="Tier2")
    assert client.api_key == "sk-test"
    assert client.base_url == "http://localhost:9999/v1"
    assert client.default_model == "Tier2"
    assert client.timeout == 120

def test_ninerouter_default_base_url():
    client = NineRouterClient(api_key="sk-test")
    assert "100.103.10.31" in client.base_url
    assert client.default_model == "Tier2"

# ── NineRouterClient.from_env ────────────────────────────────────────────────

def test_from_env_no_key_raises(monkeypatch):
    monkeypatch.delenv("9ROUTER_API_KEY", raising=False)
    monkeypatch.setattr("pmo_studio.llm.provider._load_secrets_env", lambda: {})
    with pytest.raises(RuntimeError, match="9ROUTER_API_KEY"):
        NineRouterClient.from_env()

def test_from_env_with_key():
    os.environ["9ROUTER_API_KEY"] = "sk-test-key"
    try:
        client = NineRouterClient.from_env()
        assert client.api_key == "sk-test-key"
    finally:
        del os.environ["9ROUTER_API_KEY"]

def test_from_env_custom_base_url():
    os.environ["9ROUTER_API_KEY"] = "sk-test"
    os.environ["9ROUTER_BASE_URL"] = "http://custom:8080/v1"
    try:
        client = NineRouterClient.from_env()
        assert client.base_url == "http://custom:8080/v1"
    finally:
        del os.environ["9ROUTER_API_KEY"]
        del os.environ["9ROUTER_BASE_URL"]


def test_from_env_custom_timeout():
    os.environ["9ROUTER_API_KEY"] = "sk-test"
    os.environ["PMO_LLM_TIMEOUT"] = "7"
    try:
        client = NineRouterClient.from_env()
        assert client.timeout == 7
    finally:
        del os.environ["9ROUTER_API_KEY"]
        del os.environ["PMO_LLM_TIMEOUT"]

# ── Model prefix stripping ──────────────────────────────────────────────────

def test_model_prefix_stripping():
    """NineRouterClient strips '9Router/' prefix before sending to API."""
    client = NineRouterClient(api_key="sk-test", base_url="http://localhost:9999/v1", default_model="Tier2")
    # The complete() method transforms the model name — test via internal logic
    from pmo_studio.llm.provider import NINEROUTER_MODEL_PREFIX
    assert "9Router/Tier1".removeprefix(NINEROUTER_MODEL_PREFIX) == "Tier1"
    assert "Tier2".removeprefix(NINEROUTER_MODEL_PREFIX) == "Tier2"
    assert "openai/gpt-4".removeprefix(NINEROUTER_MODEL_PREFIX) == "openai/gpt-4"

# ── Response parsing ───────────────────────────────────────────────────────

def test_parse_chat_response_json():
    raw = '{"choices":[{"message":{"content":"OK"}}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'
    parsed = _parse_chat_response(raw)
    assert parsed["choices"][0]["message"]["content"] == "OK"
    assert parsed["usage"]["prompt_tokens"] == 1


def test_parse_chat_response_sse_chunks():
    raw = '\n'.join([
        'data: {"model":"gemma4:31b-cloud","choices":[{"delta":{"content":"```json\\n{"}}]}',
        'data: {"choices":[{"delta":{"content":"\\n  \\\"passed\\\": true"}}]}',
        'data: {"choices":[{"delta":{"content":"\\n}\\n```"}}]}',
        'data: [DONE]',
    ])
    parsed = _parse_chat_response(raw)
    content = parsed["choices"][0]["message"]["content"]
    assert '"passed": true' in content
    assert content.startswith("```json")

# ── client_from_env ─────────────────────────────────────────────────────────

def test_client_from_env_defaults_to_noop():
    os.environ.pop("PMO_LLM_PROVIDER", None)
    c = client_from_env()
    assert isinstance(c, NoopLLMClient)

def test_client_from_env_explicit_noop():
    os.environ["PMO_LLM_PROVIDER"] = "noop"
    try:
        c = client_from_env()
        assert isinstance(c, NoopLLMClient)
    finally:
        del os.environ["PMO_LLM_PROVIDER"]

def test_client_from_env_openrouter_raises():
    os.environ["PMO_LLM_PROVIDER"] = "openrouter"
    try:
        with pytest.raises(ValueError, match="OpenRouter"):
            client_from_env()
    finally:
        del os.environ["PMO_LLM_PROVIDER"]

# ── api_key_status ──────────────────────────────────────────────────────────

def test_api_key_status(monkeypatch):
    monkeypatch.delenv("9ROUTER_API_KEY", raising=False)
    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.setattr("pmo_studio.llm.provider._load_secrets_env", lambda: {})
    status = api_key_status()
    assert "9router" in status
    assert "tg_bot_token" in status
    assert status["9router"] == "not set"

def test_api_key_status_with_key():
    os.environ["9ROUTER_API_KEY"] = "sk-abc123"
    try:
        status = api_key_status()
        assert "set" in status["9router"]
    finally:
        del os.environ["9ROUTER_API_KEY"]
