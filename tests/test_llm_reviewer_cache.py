import pytest

from pmo_studio.llm.cache import LLMReviewCache
from pmo_studio.llm.reviewer import JSONLLMReviewer, build_gate_reviewer


class CountingClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0
        self.timeout = 180

    def complete(self, *, system, user, model=None, temperature=0.2):
        self.calls += 1
        return self.response

    def complete_with_tokens(self, *, system, user, model=None, temperature=0.2):
        raise NotImplementedError


class FailingClient:
    def complete(self, *, system, user, model=None, temperature=0.2):
        raise TimeoutError("simulated timeout")

    def complete_with_tokens(self, *, system, user, model=None, temperature=0.2):
        raise NotImplementedError


def sample_rubric():
    return [
        {"id": "no_tbd", "question": "No TBD?", "blocker": True, "weight": 1.0},
        {"id": "clear_scope", "question": "Clear scope?", "blocker": False, "weight": 1.0},
    ]


def test_llm_review_cache_roundtrip(tmp_path):
    cache = LLMReviewCache(tmp_path)
    key = cache.key_for(
        provider="9router",
        model="Tier2",
        stage="ba.brd",
        layer="B",
        artifact="hello",
        rubric=sample_rubric(),
        context="ctx",
    )
    assert cache.get(key) is None
    cache.set(key, {"passed": True, "checks": []})
    assert cache.get(key) == {"passed": True, "checks": []}


def test_json_llm_reviewer_uses_cache(tmp_path):
    client = CountingClient('{"passed": true, "checks": [{"id": "no_tbd", "result": "Y", "evidence": "ok", "blocker": true}]}')
    reviewer = JSONLLMReviewer(client, model="Tier2", cache=LLMReviewCache(tmp_path), provider_name="9router")

    first = reviewer.review(stage="ba.brd", layer="B", artifact="artifact", rubric=sample_rubric())
    second = reviewer.review(stage="ba.brd", layer="B", artifact="artifact", rubric=sample_rubric())

    assert first["passed"] is True
    assert second["passed"] is True
    assert second["_cache"] == "hit"
    assert client.calls == 1


def test_json_llm_reviewer_fallback_on_error_marks_checks_failed():
    reviewer = JSONLLMReviewer(FailingClient(), model="Tier2", fallback_on_error=True)
    result = reviewer.review(stage="ba.brd", layer="B", artifact="artifact", rubric=sample_rubric())

    assert result["passed"] is False
    assert result["_fallback"] == "llm_error"
    assert "simulated timeout" in result["_error"]
    assert all(c["result"] == "N" for c in result["checks"])


def test_json_llm_reviewer_error_raises_without_fallback():
    reviewer = JSONLLMReviewer(FailingClient(), model="Tier2", fallback_on_error=False)
    with pytest.raises(TimeoutError):
        reviewer.review(stage="ba.brd", layer="B", artifact="artifact", rubric=sample_rubric())


def test_build_gate_reviewer_noop_returns_none():
    assert build_gate_reviewer("noop") is None
