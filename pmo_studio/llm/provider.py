"""LLM provider abstraction for PMO Studio.

The core package must remain testable without network access. Network-backed providers are
optional and selected explicitly via config/env.  API keys are read from the environment
or /etc/snailbot/secrets.env (chmod 600).

Providers:
- noop      — deterministic offline placeholder (default)
- 9router   — self-hosted model router on Tailscale (OpenAI-compatible API)
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from pmo_studio.metrics.recorder import TokenEstimator, _load_secrets_env

# ── Structured LLM response ─────────────────────────────────────────────────

@dataclass
class LLMResponse:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> str:
        ...

    def complete_with_tokens(self, *, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> LLMResponse:
        """Like complete() but also returns token counts from API or estimation."""
        ...


# ── Noop client (offline / tests) ───────────────────────────────────────────

@dataclass
class NoopLLMClient:
    """Safe deterministic placeholder used for tests/offline mode."""
    def complete(self, *, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> str:
        return ""

    def complete_with_tokens(self, *, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> LLMResponse:
        combined = (system or "") + (user or "")
        in_tok = TokenEstimator.count_tokens(combined)
        return LLMResponse(content="", input_tokens=in_tok, output_tokens=0, model="noop")


# ── 9Router client (self-hosted, OpenAI-compatible API) ─────────────────────

NINEROUTER_DEFAULT_BASE = "http://100.103.10.31:20128/v1"
NINEROUTER_DEFAULT_MODEL = "Tier2"
NINEROUTER_MODEL_PREFIX = "9Router/"


@dataclass
class NineRouterClient:
    """Self-hosted 9Router model router — OpenAI-compatible completions API.

    Reads 9ROUTER_API_KEY from env, then /etc/snailbot/secrets.env.
    Base URL defaults to http://100.103.10.31:20128/v1 (Tailscale Pi).
    Models: 9Router/Tier1, 9Router/Tier2, 9Router/Tier3, 9Router/Free.
    """
    api_key: str
    base_url: str = NINEROUTER_DEFAULT_BASE
    default_model: str = NINEROUTER_DEFAULT_MODEL
    timeout: int = 180

    @classmethod
    def from_env(cls) -> "NineRouterClient":
        key = os.environ.get("9ROUTER_API_KEY", "")
        if not key:
            key = _load_secrets_env().get("9ROUTER_API_KEY", "")
        if not key:
            raise RuntimeError(
                "9ROUTER_API_KEY is not set. "
                "Add it to env or /etc/snailbot/secrets.env as 9ROUTER_API_KEY=<key>"
            )
        base = os.environ.get("9ROUTER_BASE_URL", NINEROUTER_DEFAULT_BASE)
        default_model = os.environ.get("PMO_9ROUTER_MODEL", NINEROUTER_DEFAULT_MODEL)
        return cls(api_key=key, base_url=base, default_model=default_model)

    def complete(self, *, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> str:
        # Accept both "Tier2" and "9Router/Tier2" — strip prefix if present
        raw_model = model or self.default_model
        api_model = raw_model.removeprefix(NINEROUTER_MODEL_PREFIX) if raw_model.startswith(NINEROUTER_MODEL_PREFIX) else raw_model

        body = {
            "model": api_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8")
            # 9Router may append SSE-style "data: [DONE]" trailer — strip it
            if "\ndata: [DONE]" in raw:
                raw = raw[: raw.rindex("\ndata: [DONE]")]
            data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        self._last_usage = usage
        return content

    def complete_with_tokens(self, *, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> LLMResponse:
        content = self.complete(system=system, user=user, model=model, temperature=temperature)
        usage = getattr(self, "_last_usage", {})
        in_tok = usage.get("prompt_tokens", TokenEstimator.count_tokens((system or "") + (user or "")))
        out_tok = usage.get("completion_tokens", TokenEstimator.count_tokens(content))
        resolved = model or self.default_model
        return LLMResponse(content=content, input_tokens=in_tok, output_tokens=out_tok, model=resolved)


# ── Helpers ─────────────────────────────────────────────────────────────────

def client_from_env() -> LLMClient:
    provider = os.environ.get("PMO_LLM_PROVIDER", "noop").lower()
    if provider in ("9router", "ninerouter"):
        return NineRouterClient.from_env()
    if provider == "openrouter":
        raise ValueError("OpenRouter is discontinued. Please set 9ROUTER_API_KEY and use --llm 9router instead.")
    return NoopLLMClient()


def api_key_status() -> dict[str, str]:
    """Check API key availability without making a network call."""
    result: dict[str, str] = {}

    # 9Router
    key = os.environ.get("9ROUTER_API_KEY", "")
    if key:
        result["9router"] = f"set (env, {len(key)} chars)"
    else:
        secrets = _load_secrets_env()
        key = secrets.get("9ROUTER_API_KEY", "")
        result["9router"] = f"set (secrets.env, {len(key)} chars)" if key else "not set"

    # Telegram
    tg_token = os.environ.get("TG_BOT_TOKEN") or _load_secrets_env().get("TG_BOT_TOKEN", "")
    result["tg_bot_token"] = "set" if tg_token else "not set"

    return result
