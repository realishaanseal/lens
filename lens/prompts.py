"""Builds the list of customer-style questions to ask for a client."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from importlib import resources
from itertools import zip_longest

import yaml

from .config import Client, Service

_FIELD = re.compile(r"{(\w+)}")


@dataclass(frozen=True)
class Prompt:
    id: str
    text: str
    language: str  # en | bn | banglish | custom
    service: str | None = None


def prompt_id(text: str) -> str:
    """Stable id, so the same question can be compared month to month."""
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()[:12]


def load_library() -> dict:
    text = resources.files("lens.data").joinpath("prompt_library.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _fill(template: str, client: Client, service: Service | None) -> str | None:
    values = {
        "city": client.city,
        "city_bn": client.city_bn or client.city,
        "area": client.area or client.city,
        "service": service.name if service else None,
        "service_bn": service.bn if service else None,
    }
    for field in _FIELD.findall(template):
        if values.get(field) is None:
            return None
    return template.format(**values)


def build_prompts(client: Client, library: dict | None = None) -> list[Prompt]:
    """Expand the category templates for this client, capped at client.max_prompts.

    Templates are interleaved before the cap is applied, so a cap keeps a mix of
    languages and question types instead of dropping whole languages.
    """
    library = library or load_library()
    by_language = library.get(client.category, {})

    groups: list[list[Prompt]] = []
    for language, templates in by_language.items():
        for template in templates:
            uses_service = "{service" in template
            group = []
            for service in client.services if uses_service else [None]:
                text = _fill(template, client, service)
                if text:
                    group.append(Prompt(prompt_id(text), text, language, service.name if service else None))
            if group:
                groups.append(group)

    interleaved = [p for row in zip_longest(*groups) for p in row if p is not None]
    custom = [Prompt(prompt_id(t), t, "custom") for t in client.extra_prompts]

    seen: set[str] = set()
    prompts: list[Prompt] = []
    for p in custom + interleaved:
        if p.id not in seen:
            seen.add(p.id)
            prompts.append(p)
    return prompts[: client.max_prompts]
