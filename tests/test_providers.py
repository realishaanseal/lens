import json

import pytest

from lens.providers import parse_gemini, parse_openai, parse_perplexity


def test_parse_openai_responses():
    data = {"model": "gpt-x", "output": [
        {"type": "web_search_call"},
        {"type": "message", "content": [{"type": "output_text", "text": "Try SSHRI Hospital.",
                                         "annotations": [{"url": "https://a"}, {"url": "https://a"}]}]}]}
    a = parse_openai(data, "fallback")
    assert a.text == "Try SSHRI Hospital." and a.model == "gpt-x" and a.citations == ["https://a"]


def test_parse_gemini():
    data = {"modelVersion": "gemini-x", "candidates": [{
        "content": {"parts": [{"text": "Hello "}, {"text": "world"}]},
        "groundingMetadata": {"groundingChunks": [{"web": {"uri": "https://b"}}]}}]}
    a = parse_gemini(data, "fallback")
    assert a.text == "Hello world" and a.citations == ["https://b"]


def test_parse_perplexity():
    data = {"model": "sonar", "choices": [{"message": {"content": "Hi"}}], "citations": ["https://c"]}
    a = parse_perplexity(data, "fallback")
    assert a.text == "Hi" and a.citations == ["https://c"]


def test_gemini_free_tier_waits_as_asked_and_stops_on_daily_quota(monkeypatch):
    import requests as rq
    from lens import providers as pv

    class Resp:
        def __init__(self, status, body, headers=None):
            self.status_code, self._body, self.headers = status, body, headers or {}
            self.text = json.dumps(body)
        def json(self):
            return self._body

    minute = Resp(429, {"error": {"message": "GenerateRequestsPerMinute", "details": [{"retryDelay": "7s"}]}})
    ok = Resp(200, {"candidates": [{"content": {"parts": [{"text": "Try City Care."}]}}]})
    daily = Resp(429, {"error": {"message": "Quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier"}})
    replies, waits, calls = [minute, ok, daily], [], []
    monkeypatch.setattr(rq, "post", lambda *a, **k: calls.append(1) or replies.pop(0))
    monkeypatch.setattr(pv.time, "sleep", waits.append)
    monkeypatch.setenv("GEMINI_API_KEY", "k"); monkeypatch.setenv("LENS_GEMINI_MIN_INTERVAL", "0")
    g = pv.GeminiProvider()
    assert g.ask("q1").text == "Try City Care."
    assert 7.0 in waits                                  # waited exactly as long as Google asked
    with pytest.raises(pv.QuotaExhausted):
        g.ask("q2")
    with pytest.raises(pv.QuotaExhausted):               # no further API call once the day's quota is gone
        g.ask("q3")
    assert len(calls) == 3
