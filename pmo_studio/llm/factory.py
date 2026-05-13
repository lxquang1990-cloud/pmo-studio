"""Factory helpers for optional LLM wiring."""
from __future__ import annotations

import os
from pmo_studio.llm.provider import LLMClient, NoopLLMClient, NineRouterClient

def build_llm(provider: str = "noop", model: str | None = None) -> LLMClient:
    provider = (provider or "noop").lower()
    if provider in {"none", "noop", "offline"}:
        return NoopLLMClient()
    if provider in ("9router", "ninerouter"):
        client = NineRouterClient.from_env()
        if model:
            client.default_model = model
        return client
    if provider == "openrouter":
        raise ValueError(
            "OpenRouter has been replaced by 9Router. "
            "Set 9ROUTER_API_KEY in env or /etc/snailbot/secrets.env, then use --llm 9router"
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")

def llm_help() -> str:
    return (
        "Use --llm 9router --model <Tier1|Tier2|Tier3> with 9ROUTER_API_KEY set, "
        "or --llm noop for offline deterministic mode."
    )
