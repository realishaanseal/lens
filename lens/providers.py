"""Clients for the AI tools we check: Gemini (free tier), ChatGPT (OpenAI) and Perplexity.

Each provider sends the question exactly as a customer would type it, with web
search switched on where the API supports it, because that is how these tools
answer "best X near me" questions for real users.
"""

from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Protocol

import requests

from .config import Client

PROVIDERS = ("gemini", "openai", "perplexity")  # Gemini first: it has a free tier
FREE_PROVIDERS = {"gemini"}
DEFAULT_MODELS = {"openai": "gpt-4.1-mini", "gemini": "gemini-2.5-flash", "perplexity": "sonar"}
TIMEOUT = 90


class ProviderError(RuntimeError):
    pass


@dataclass
class Answer:
    text: str
    model: str
    citations: list[str] = field(default_factory=list)


class Provider(Protocol):
    name: str
    model: str

    def ask(self, prompt: str) -> Answer: ...


def _retry_delay(resp: requests.Response) -> float | None:
    """Seconds the API asked us to wait, from Retry-After or Google's RetryInfo."""
    if resp.headers.get("retry-after", "").isdigit():
        return float(resp.headers["retry-after"])
    try:
        for detail in resp.json().get("error", {}).get("details", []):
            delay = detail.get("retryDelay", "")
            if delay.endswith("s"):
                return float(delay[:-1])
    except ValueError:
        pass
    return None


class QuotaExhausted(ProviderError):
    """The account's daily (free) quota is used up; retrying today won't help."""


def _post(url: str, *, headers: dict, payload: dict, params: dict | None = None, retries: int = 3) -> dict:
    """POST with retry on rate limits and server errors, waiting as long as the API asks."""
    for attempt in range(retries):
        wait = 2 ** (attempt + 1)
        try:
            resp = requests.post(url, headers=headers, json=payload, params=params, timeout=TIMEOUT)
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise ProviderError(str(exc)) from exc
        else:
            if resp.status_code < 400:
                return resp.json()
            body = resp.text[:300]
            if resp.status_code == 429 and ("PerDay" in resp.text or "per day" in resp.text.lower()):
                raise QuotaExhausted(f"HTTP 429: daily quota used up. {body}")
            if resp.status_code != 429 and resp.status_code < 500 or attempt == retries - 1:
                raise ProviderError(f"HTTP {resp.status_code}: {body}")
            wait = min(_retry_delay(resp) or wait, 65)
        time.sleep(wait)
    raise ProviderError("unreachable")


def _env_key(*names: str) -> str:
    for name in names:
        if os.environ.get(name):
            return os.environ[name]
    raise ProviderError(f"set {' or '.join(names)} to use this provider")


class OpenAIProvider:
    name = "openai"

    def __init__(self, city: str | None = None, model: str | None = None):
        self.key = _env_key("OPENAI_API_KEY")
        self.model = model or os.environ.get("LENS_OPENAI_MODEL", DEFAULT_MODELS["openai"])
        self.city = city

    def ask(self, prompt: str) -> Answer:
        tool = {"type": "web_search"}
        if self.city:
            tool["user_location"] = {"type": "approximate", "country": "IN", "city": self.city}
        data = _post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.key}"},
            payload={"model": self.model, "input": prompt, "tools": [tool]},
        )
        return parse_openai(data, self.model)


def parse_openai(data: dict, model: str) -> Answer:
    texts, citations = [], []
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if part.get("type") == "output_text":
                texts.append(part.get("text", ""))
                citations += [a["url"] for a in part.get("annotations", []) if a.get("url")]
    if not texts:
        raise ProviderError("OpenAI returned no text")
    return Answer("\n".join(texts), data.get("model", model), list(dict.fromkeys(citations)))


class GeminiProvider:
    """Gemini with Google Search grounding. Works on Google AI Studio's free tier (no card needed).

    Free-tier keys allow only a few requests a minute, so calls are spaced out across all threads
    (LENS_GEMINI_MIN_INTERVAL seconds, default 6.5, about 9 a minute). Set it to 0 on a paid key."""
    name = "gemini"
    _lock = threading.Lock()
    _last = 0.0

    def __init__(self, model: str | None = None):
        self.key = _env_key("GEMINI_API_KEY", "GOOGLE_API_KEY")
        self.model = model or os.environ.get("LENS_GEMINI_MODEL", DEFAULT_MODELS["gemini"])
        self.min_interval = float(os.environ.get("LENS_GEMINI_MIN_INTERVAL", "6.5"))
        self.exhausted: QuotaExhausted | None = None   # once the daily quota is gone, stop calling

    def _pace(self) -> None:
        with GeminiProvider._lock:
            gap = GeminiProvider._last + self.min_interval - time.monotonic()
            if gap > 0:
                time.sleep(gap)
            GeminiProvider._last = time.monotonic()

    def ask(self, prompt: str) -> Answer:
        if self.exhausted:
            raise self.exhausted
        self._pace()
        try:
            data = _post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                headers={"x-goog-api-key": self.key},
                payload={"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]},
                retries=4,
            )
        except QuotaExhausted as exc:
            self.exhausted = exc
            raise
        return parse_gemini(data, self.model)


def parse_gemini(data: dict, model: str) -> Answer:
    candidates = data.get("candidates") or []
    if not candidates:
        raise ProviderError(f"Gemini returned no candidates: {data.get('promptFeedback', '')}")
    cand = candidates[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    if not text:
        raise ProviderError("Gemini returned no text")
    chunks = cand.get("groundingMetadata", {}).get("groundingChunks", [])
    citations = [c["web"]["uri"] for c in chunks if c.get("web", {}).get("uri")]
    return Answer(text, data.get("modelVersion", model), citations)


class PerplexityProvider:
    name = "perplexity"

    def __init__(self, model: str | None = None):
        self.key = _env_key("PERPLEXITY_API_KEY")
        self.model = model or os.environ.get("LENS_PERPLEXITY_MODEL", DEFAULT_MODELS["perplexity"])

    def ask(self, prompt: str) -> Answer:
        data = _post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            payload={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
        )
        return parse_perplexity(data, self.model)


def parse_perplexity(data: dict, model: str) -> Answer:
    choices = data.get("choices") or []
    if not choices:
        raise ProviderError("Perplexity returned no choices")
    citations = data.get("citations") or [r.get("url") for r in data.get("search_results", []) if r.get("url")]
    return Answer(choices[0]["message"]["content"], data.get("model", model), citations)


class MockProvider:
    """Offline stand-in that writes plausible answers, for demos and tests.

    `mention_rate` is the chance the client appears in an answer. Results are
    deterministic for a given provider, prompt and seed.
    """

    model = "mock"

    def __init__(self, name: str, client: Client, mention_rate: float | None = None, seed: str = ""):
        self.name = name
        self.client = client
        # demos can set LENS_MOCK_RATE to show a particular month; seeded history passes its own rate
        self.mention_rate = mention_rate if mention_rate is not None else float(os.environ.get("LENS_MOCK_RATE", "0.4"))
        self.seed = seed

    def ask(self, prompt: str) -> Answer:
        delay = float(os.environ.get("LENS_MOCK_DELAY", "0"))  # demos: pace sample answers like real ones
        if delay:
            time.sleep(delay)
        rng = random.Random(f"{self.name}|{prompt}|{self.seed}")
        c = self.client
        rate = self.mention_rate
        # regional-language answers mention small local businesses less often
        if not prompt.isascii():
            rate *= 0.6
        # and every third service is a weak spot, so the demo has gaps to fix
        weak = [w for s in c.services[2::3] for w in (s.name, s.bn) if w]
        if any(w.lower() in prompt.lower() for w in weak):
            rate *= 0.25
        pool = [comp.name for comp in c.competitors] or ["Another local business"]
        picks = rng.sample(pool, k=min(len(pool), rng.randint(2, 3)))
        if rng.random() < rate:
            picks.insert(rng.randint(0, len(picks)), rng.choice(c.brand_names))
        lines = [f"Here are some options people in {c.city} often recommend:\n"]
        for i, name in enumerate(picks, 1):
            reason = rng.choice(["well reviewed on Google", "experienced specialists",
                                 "convenient location", "good value", "open 24 hours"])
            lines.append(f"{i}. **{name}** – {reason}.")
        lines.append("\nCheck recent reviews and call ahead before visiting.")
        return Answer("\n".join(lines), self.model)


def get_provider(name: str, client: Client | None = None) -> Provider:
    if name == "openai":
        return OpenAIProvider(city=client.city if client else None)
    if name == "gemini":
        return GeminiProvider()
    if name == "perplexity":
        return PerplexityProvider()
    raise ValueError(f"unknown provider '{name}' (choose from {', '.join(PROVIDERS)})")


def available_providers() -> list[str]:
    """Providers whose API key is set in the environment."""
    keys = {"openai": ["OPENAI_API_KEY"], "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "perplexity": ["PERPLEXITY_API_KEY"]}
    return [p for p, names in keys.items() if any(os.environ.get(n) for n in names)]
