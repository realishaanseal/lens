"""Clients for the AI tools we check: ChatGPT (OpenAI), Gemini and Perplexity.

Each provider sends the question exactly as a customer would type it, with web
search switched on where the API supports it, because that is how these tools
answer "best X near me" questions for real users.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from typing import Protocol

import requests

from .config import Client

PROVIDERS = ("openai", "gemini", "perplexity")
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


def _post(url: str, *, headers: dict, payload: dict, params: dict | None = None, retries: int = 3) -> dict:
    """POST with retry on rate limits and server errors."""
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, params=params, timeout=TIMEOUT)
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise ProviderError(str(exc)) from exc
        else:
            if resp.status_code < 400:
                return resp.json()
            if resp.status_code != 429 and resp.status_code < 500 or attempt == retries - 1:
                raise ProviderError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        time.sleep(2 ** (attempt + 1))
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
    name = "gemini"

    def __init__(self, model: str | None = None):
        self.key = _env_key("GEMINI_API_KEY", "GOOGLE_API_KEY")
        self.model = model or os.environ.get("LENS_GEMINI_MODEL", DEFAULT_MODELS["gemini"])

    def ask(self, prompt: str) -> Answer:
        data = _post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            headers={"x-goog-api-key": self.key},
            payload={"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]},
        )
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

    def __init__(self, name: str, client: Client, mention_rate: float = 0.4, seed: str = ""):
        self.name = name
        self.client = client
        self.mention_rate = mention_rate
        self.seed = seed

    def ask(self, prompt: str) -> Answer:
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
        pool = [comp.name for comp in c.competitors] or ["City Care Hospital"]
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
