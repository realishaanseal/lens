"""API keys and model settings, kept in a local .env file (never committed)."""

from __future__ import annotations

import os
from pathlib import Path

ENV_FILE = Path(".env")
KEYS = {
    "OPENAI_API_KEY": "ChatGPT (OpenAI) API key",
    "GEMINI_API_KEY": "Gemini API key",
    "PERPLEXITY_API_KEY": "Perplexity API key",
    "LENS_OPENAI_MODEL": "ChatGPT model",
    "LENS_GEMINI_MODEL": "Gemini model",
    "LENS_PERPLEXITY_MODEL": "Perplexity model",
}


def read_env(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_env(path: Path = ENV_FILE) -> None:
    """Copy .env values into the environment; real environment variables win."""
    for key, value in read_env(path).items():
        if value:
            os.environ.setdefault(key, value)


def save_env(updates: dict[str, str], path: Path = ENV_FILE) -> None:
    """Merge updates into .env. An empty value removes the key."""
    values = read_env(path)
    for key, value in updates.items():
        value = value.strip()
        if value:
            values[key] = value
            os.environ[key] = value
        else:
            values.pop(key, None)
            os.environ.pop(key, None)
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
