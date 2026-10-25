"""Client configuration: who we are tracking and how AI might refer to them."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CATEGORIES = ("hospital", "clinic", "coaching", "restaurant")


@dataclass
class Service:
    name: str
    bn: str | None = None  # Bengali name, used for Bengali-script prompts
    page: str | None = None  # page on the client's site that covers this service


@dataclass
class Competitor:
    name: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class Listing:
    source: str  # e.g. "Website", "Google Business Profile", "Justdial"
    phone: str


@dataclass
class Client:
    id: str
    name: str
    category: str
    city: str
    city_bn: str | None = None
    area: str | None = None
    website: str | None = None
    aliases: list[str] = field(default_factory=list)
    doctors: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    competitors: list[Competitor] = field(default_factory=list)
    listings: list[Listing] = field(default_factory=list)
    google_reviews: int | None = None
    has_physician_schema: bool | None = None
    max_prompts: int = 25
    extra_prompts: list[str] = field(default_factory=list)

    @property
    def brand_names(self) -> list[str]:
        """Every name AI could use for the business itself."""
        return [self.name, *self.aliases]


def _require(data: dict, key: str, path: Path):
    if not data.get(key):
        raise ValueError(f"{path}: missing required field '{key}'")
    return data[key]


def load_client(path: str | Path) -> Client:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    category = _require(data, "category", path)
    if category not in CATEGORIES:
        raise ValueError(f"{path}: category must be one of {', '.join(CATEGORIES)}")

    services = [
        Service(name=s) if isinstance(s, str) else Service(**s)
        for s in data.get("services", [])
    ]
    competitors = [
        Competitor(name=c) if isinstance(c, str) else Competitor(**c)
        for c in data.get("competitors", [])
    ]
    listings = [Listing(**item) for item in data.get("listings", [])]

    return Client(
        id=_require(data, "id", path),
        name=_require(data, "name", path),
        category=category,
        city=_require(data, "city", path),
        city_bn=data.get("city_bn"),
        area=data.get("area"),
        website=data.get("website"),
        aliases=list(data.get("aliases", [])),
        doctors=list(data.get("doctors", [])),
        phones=[str(p) for p in data.get("phones", [])],
        services=services,
        competitors=competitors,
        listings=listings,
        google_reviews=data.get("google_reviews"),
        has_physician_schema=data.get("has_physician_schema"),
        max_prompts=int(data.get("max_prompts", 25)),
        extra_prompts=list(data.get("extra_prompts", [])),
    )


def list_client_files(directory: str | Path = "clients") -> list[Path]:
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.y*ml") if p.is_file())
