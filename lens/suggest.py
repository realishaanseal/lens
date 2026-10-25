"""Rule-based fix suggestions: what to improve when AI leaves the brand out."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import Client

REVIEW_TARGET = 100


@dataclass
class Suggestion:
    title: str
    detail: str
    priority: int  # 1 = do first


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", phone)[-10:]


def suggest(client: Client, results: list[dict]) -> list[Suggestion]:
    out: list[Suggestion] = []

    # Services where no AI tool named the client for any question
    by_service: dict[str, list[dict]] = {}
    for r in results:
        if r.get("service"):
            by_service.setdefault(r["service"], []).append(r)
    pages = {s.name: s.page for s in client.services}
    for service, rows in sorted(by_service.items()):
        hit = sum(r["mentioned"] for r in rows) / len(rows)
        if hit < 0.25:
            missed = next((r["prompt"] for r in rows if not r["mentioned"] and r["language"] == "en"), rows[0]["prompt"])
            page = f" ({pages[service]})" if pages.get(service) else ""
            out.append(Suggestion(
                f"Add FAQs to the {service} page",
                f"Named in {hit:.0%} of {service} answers. Answer questions like \"{missed}\" "
                f"directly on the {service} page{page}.",
                1 if hit == 0 else 2,
            ))

    if client.category in ("hospital", "clinic") and client.has_physician_schema is False:
        out.append(Suggestion(
            "Add Physician schema",
            "Mark up each doctor's page with schema.org Physician (name, specialty, hospital) "
            "so AI tools can connect doctors to the hospital.",
            2,
        ))

    phones = {(l.source, _digits(l.phone)) for l in client.listings if _digits(l.phone)}
    if len({p for _, p in phones}) > 1:
        sources = ", ".join(f"{s}: …{p[-4:]}" for s, p in sorted(phones))
        out.append(Suggestion(
            "Fix phone number mismatch",
            f"Listings show different numbers ({sources}). Use one number everywhere.",
            1,
        ))

    # Regional-language gap
    def lang_rate(langs):
        rows = [r for r in results if r.get("language") in langs]
        return (sum(r["mentioned"] for r in rows) / len(rows), len(rows)) if rows else (None, 0)

    en, _ = lang_rate({"en"})
    regional, n_regional = lang_rate({"bn", "banglish"})
    if en is not None and regional is not None and n_regional and regional < en - 0.1:
        out.append(Suggestion(
            "Add Bengali content",
            f"Named in {en:.0%} of English answers but only {regional:.0%} of Bengali/Banglish ones. "
            "Add a Bengali page or FAQ section and Bengali text on the Google profile.",
            2,
        ))

    # Competitors AI names when it leaves the client out
    missing = [r for r in results if not r["mentioned"]]
    if missing:
        counts: dict[str, int] = {}
        for r in missing:
            for name in {c["name"] for c in r.get("competitors", [])}:
                counts[name] = counts.get(name, 0) + 1
        if counts:
            name, n = max(counts.items(), key=lambda kv: kv[1])
            if n / len(missing) >= 0.3:
                out.append(Suggestion(
                    f"Study {name}",
                    f"AI named {name} in {n} of {len(missing)} answers that left you out. "
                    "Compare their pages, reviews and listings with yours.",
                    3,
                ))

    if client.google_reviews is not None and client.google_reviews < REVIEW_TARGET:
        out.append(Suggestion(
            "Collect more reviews",
            f"{client.google_reviews} Google reviews today. AI tools favour well-reviewed businesses; "
            f"aim for {REVIEW_TARGET}+.",
            3,
        ))

    return sorted(out, key=lambda s: s.priority)
