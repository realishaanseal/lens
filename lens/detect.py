"""Finds the client and its competitors in an AI answer."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from .config import Client

FUZZY_THRESHOLD = 0.88
# Short names fuzzy-match too much ("Care" vs "Cure"), so they must match exactly.
FUZZY_MIN_LENGTH = 8

# Words that end the name of a local business, per category. Used to pick out
# businesses the client never told us about.
ENTITY_SUFFIXES = {
    "hospital": ["Hospital", "Hospitals", "Nursing Home", "Medical Centre", "Medical Center",
                 "Medical College", "Healthcare", "Health Care", "Clinic", "Polyclinic",
                 "Diagnostics"],
    "clinic": ["Clinic", "Clinics", "Polyclinic", "Hospital", "Nursing Home", "Diagnostics",
               "Medical Centre", "Medical Center", "Dental Care", "Eye Care", "Skin Care"],
    "coaching": ["Academy", "Institute", "Coaching", "Coaching Centre", "Coaching Center",
                 "Classes", "Tutorials", "Tuition", "Study Circle", "Mission"],
    "restaurant": ["Restaurant", "Restaurants", "Cafe", "Café", "Dhaba", "Kitchen", "Biryani",
                   "Bistro", "Hotel", "Sweets", "Food Court", "Eatery", "Bakery"],
}

# Capitalised words that start sentences or list items rather than business names.
_LEADING_NOISE = {"the", "a", "an", "best", "top", "good", "visit", "try", "consider", "at", "in",
                  "near", "from", "and", "or", "also", "for", "is", "with", "of", "local", "nearby"}

_DOCTOR = re.compile(r"\bDr\.?\s+((?:[A-Z]\.\s*)*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})")
_MARKDOWN = re.compile(r"[*_`#>|]+")


@dataclass
class Mention:
    found: bool
    alias: str | None = None
    score: float = 0.0
    snippet: str | None = None


@dataclass(frozen=True)
class CompetitorHit:
    name: str
    kind: str  # "known" (from client config) | "business" | "doctor"


def normalize(text: str) -> str:
    """Lowercase, strip markdown/punctuation, keep letters of any script."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = _MARKDOWN.sub(" ", text)
    chars = [" " if unicodedata.category(ch)[0] in "PSZC" else ch for ch in text]
    return " ".join("".join(chars).split())


def _windows(tokens: list[str], size: int):
    for i in range(max(len(tokens) - size + 1, 0)):
        yield i, " ".join(tokens[i:i + size])


def find_name(text: str, names: list[str]) -> Mention:
    """Best match of any of `names` in `text`: exact first, then fuzzy."""
    norm_text = normalize(text)
    padded = f" {norm_text} "
    tokens = norm_text.split()

    best = Mention(False)
    for name in names:
        norm_name = normalize(name)
        if not norm_name:
            continue
        if f" {norm_name} " in padded:
            return Mention(True, name, 1.0, _snippet(text, name))
        if len(norm_name) < FUZZY_MIN_LENGTH:
            continue
        # Same word count, or one extra word inside the name ("SSHRI Hospital" vs
        # "SSHRI Multi Hospital"). Never fewer words: "Hospital" alone must not
        # match "Hospital B".
        size = len(norm_name.split())
        for width in (size, size + 1) if size > 1 else (size,):
            for _, window in _windows(tokens, width):
                score = SequenceMatcher(None, norm_name, window).ratio()
                if score >= FUZZY_THRESHOLD and score > best.score:
                    best = Mention(True, name, round(score, 3), _snippet(text, window))
    return best


def _snippet(text: str, needle: str, radius: int = 80) -> str:
    """The sentence-ish context around the match, for the dashboard."""
    flat = " ".join(text.split())
    idx = flat.lower().find(needle.lower())
    if idx < 0:
        # fuzzy match: locate by the first word of the matched window
        first = needle.split()[0].lower() if needle.split() else ""
        idx = flat.lower().find(first)
    if idx < 0:
        return flat[: radius * 2]
    start, end = max(idx - radius, 0), min(idx + len(needle) + radius, len(flat))
    return ("…" if start else "") + flat[start:end] + ("…" if end < len(flat) else "")


def detect_mention(client: Client, text: str) -> Mention:
    """Is the client named in the answer, by business name, alias, doctor or phone?"""
    mention = find_name(text, client.brand_names + client.doctors)
    if mention.found:
        return mention
    digits = re.sub(r"\D", "", text)
    for phone in client.phones:
        tail = re.sub(r"\D", "", phone)[-10:]
        if len(tail) == 10 and tail in digits:
            return Mention(True, phone, 1.0, _snippet(text, phone[-4:]))
    return Mention(False)


def _business_pattern(category: str) -> re.Pattern:
    suffixes = sorted(ENTITY_SUFFIXES.get(category, []), key=len, reverse=True)
    suffix = "|".join(re.escape(s) for s in suffixes)
    word = r"(?:[A-Z][\w'&.-]*|&)"
    return re.compile(rf"\b((?:{word}\s+){{1,5}}?(?:{suffix}))\b")


def _clean_business(name: str) -> str:
    words = name.split()
    while words and words[0].lower().strip(".,") in _LEADING_NOISE:
        words.pop(0)
    return " ".join(words)


def extract_competitors(client: Client, text: str) -> list[CompetitorHit]:
    """Every other business or doctor named in the answer."""
    own_names = client.brand_names + client.doctors
    hits: dict[str, CompetitorHit] = {}

    def add(name: str, kind: str):
        key = normalize(name)
        if not key or find_name(name, own_names).found:
            return
        # merge with a known competitor's canonical name if it is one
        for comp in client.competitors:
            if find_name(name, [comp.name, *comp.aliases]).found:
                name, kind, key = comp.name, "known", normalize(comp.name)
                break
        if key not in hits or (kind == "known" and hits[key].kind != "known"):
            hits[key] = CompetitorHit(name, kind)

    for comp in client.competitors:
        if find_name(text, [comp.name, *comp.aliases]).found:
            add(comp.name, "known")

    flat = _MARKDOWN.sub(" ", text)
    for match in _business_pattern(client.category).finditer(flat):
        name = _clean_business(match.group(1))
        if len(name.split()) >= 2:
            add(name, "business")

    if client.category in ("hospital", "clinic"):
        for match in _DOCTOR.finditer(flat):
            add("Dr. " + " ".join(match.group(1).split()), "doctor")

    return list(hits.values())
