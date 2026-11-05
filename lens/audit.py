"""Website check: the signals AI assistants rely on, read straight from the client's site.

Free to run (plain HTTP, no AI API). It checks whether AI crawlers may read the site, whether
the pages carry the structured data and wording that let an assistant connect the business
to its city and services, and whether the details agree with the client's listings.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

from .config import Client

USER_AGENT = "Mozilla/5.0 (compatible; VaraxisLens/1.0; website check)"
TIMEOUT = 15

# Crawlers that feed AI answers: (user agent, the product it feeds)
AI_CRAWLERS = [
    ("OAI-SearchBot", "ChatGPT search"),
    ("ChatGPT-User", "ChatGPT browsing"),
    ("GPTBot", "OpenAI models"),
    ("Google-Extended", "Gemini"),
    ("Googlebot", "Google Search and AI Overviews"),
    ("PerplexityBot", "Perplexity"),
    ("ClaudeBot", "Claude"),
    ("Bingbot", "Bing and Copilot"),
]

# schema.org types that tell an assistant what kind of business this is
SCHEMA_TYPES = {
    "hospital": {"Hospital", "MedicalOrganization", "MedicalClinic", "MedicalBusiness"},
    "clinic": {"MedicalClinic", "MedicalBusiness", "Physician", "Dentist", "MedicalOrganization"},
    "coaching": {"EducationalOrganization", "School", "CollegeOrUniversity", "TutoringService"},
    "restaurant": {"Restaurant", "FoodEstablishment", "CafeOrCoffeeShop", "BarOrPub"},
}
GENERIC_TYPES = {"LocalBusiness", "Organization", "Place"}

PASS, WARN, FAIL, INFO = "pass", "warn", "fail", "info"


@dataclass
class Check:
    area: str          # Access | Structured data | Content | Consistency
    name: str
    status: str        # pass | warn | fail | info
    detail: str
    fix: str = ""
    weight: int = 1


@dataclass
class Audit:
    url: str
    checks: list[Check] = field(default_factory=list)
    error: str | None = None

    @property
    def score(self) -> int | None:
        """0-100: passes count fully, warnings half; info items don't count."""
        scored = [c for c in self.checks if c.status != INFO]
        total = sum(c.weight for c in scored)
        if not total:
            return None
        got = sum(c.weight * (1 if c.status == PASS else 0.5 if c.status == WARN else 0) for c in scored)
        return round(100 * got / total)

    def to_json(self) -> str:
        return json.dumps({"url": self.url, "error": self.error, "checks": [asdict(c) for c in self.checks]})

    @classmethod
    def from_json(cls, text: str) -> "Audit":
        data = json.loads(text)
        return cls(data["url"], [Check(**c) for c in data["checks"]], data.get("error"))


@dataclass
class Page:
    url: str
    status: int
    text: str


Fetcher = Callable[[str], Page]


def http_fetch(url: str) -> Page:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return Page(url, 0, str(exc))
    ctype = resp.headers.get("content-type", "")
    text = resp.text if ("html" in ctype or "text" in ctype or "xml" in ctype or not ctype) else ""
    return Page(resp.url, resp.status_code, text)


class _Reader(HTMLParser):
    """Pulls the title, meta description, JSON-LD blocks and visible text out of a page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""; self.description = ""; self.jsonld: list[str] = []; self.text: list[str] = []
        self._in = None; self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in = "title"
        elif tag == "meta" and (a.get("name") or "").lower() == "description":
            self.description = a.get("content") or ""
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in = "jsonld"; self.jsonld.append("")
        elif tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("title", "script") and self._in:
            self._in = None
        elif tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in == "title":
            self.title += data
        elif self._in == "jsonld":
            self.jsonld[-1] += data
        elif not self._skip:
            self.text.append(data)


def _read(html: str) -> _Reader:
    r = _Reader()
    try:
        r.feed(html)
    except Exception:  # malformed HTML: keep whatever was read
        pass
    return r


def _schema_nodes(blocks: list[str]) -> list[dict]:
    nodes: list[dict] = []

    def walk(x):
        if isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, dict):
            nodes.append(x)
            for v in x.values():
                if isinstance(v, (dict, list)):
                    walk(v)
    for b in blocks:
        try:
            walk(json.loads(b))
        except ValueError:
            continue
    return nodes


def _types(nodes: list[dict]) -> set[str]:
    out: set[str] = set()
    for n in nodes:
        t = n.get("@type")
        for v in t if isinstance(t, list) else [t]:
            if isinstance(v, str):
                out.add(v.split("/")[-1])
    return out


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)[-10:]


def _has(text: str, needle: str) -> bool:
    return bool(needle) and needle.lower() in text.lower()


def run_audit(client: Client, fetch: Fetcher = http_fetch) -> Audit:
    if not client.website:
        return Audit("", error="Add the client's website on the Clients page to run the website check.")
    base = client.website.strip()
    if not urlparse(base).scheme:
        base = "https://" + base
    audit = Audit(base)
    add = audit.checks.append

    home = fetch(base)
    if home.status == 0 or home.status >= 400:
        audit.error = f"Couldn't open {base} ({'no response' if home.status == 0 else f'HTTP {home.status}'})."
        return audit
    root = f"{urlparse(home.url).scheme}://{urlparse(home.url).netloc}"
    page = _read(home.text)
    text = " ".join(" ".join(page.text).split())
    nodes = _schema_nodes(page.jsonld)
    types = _types(nodes)

    # ---- Access -------------------------------------------------------------------
    add(Check("Access", "Secure address (HTTPS)", PASS if home.url.startswith("https://") else FAIL,
              "The site loads over HTTPS." if home.url.startswith("https://") else "The site loads over plain HTTP.",
              "Serve the site over HTTPS; assistants and browsers trust secure pages more."))
    robots = fetch(urljoin(root, "/robots.txt"))
    if robots.status == 200 and robots.text.strip():
        rp = RobotFileParser(); rp.parse(robots.text.splitlines())
        blocked = [f"{agent} ({product})" for agent, product in AI_CRAWLERS if not rp.can_fetch(agent, home.url)]
        add(Check("Access", "AI crawlers allowed", FAIL if blocked else PASS,
                  ("robots.txt blocks: " + ", ".join(blocked)) if blocked else "robots.txt lets every major AI crawler read the site.",
                  "Remove the Disallow rules for these crawlers in robots.txt so they can read and cite the site.",
                  weight=3))
        sitemap_listed = "sitemap:" in robots.text.lower()
    else:
        add(Check("Access", "AI crawlers allowed", PASS, "No robots.txt rules, so crawlers may read the site.", weight=3))
        sitemap_listed = False
    sm = fetch(urljoin(root, "/sitemap.xml"))
    has_sitemap = sitemap_listed or (sm.status == 200 and ("<urlset" in sm.text or "<sitemapindex" in sm.text))
    add(Check("Access", "Sitemap", PASS if has_sitemap else WARN,
              "A sitemap lists the site's pages." if has_sitemap else "No sitemap found at /sitemap.xml or in robots.txt.",
              "Publish /sitemap.xml and list it in robots.txt so every service page gets found."))
    llms = fetch(urljoin(root, "/llms.txt"))
    add(Check("Access", "llms.txt", PASS if llms.status == 200 and llms.text.strip() else INFO,
              "An llms.txt summary is published." if llms.status == 200 and llms.text.strip()
              else "No /llms.txt. Optional: a short plain-text summary some AI tools read.",
              "Optionally add /llms.txt with the business name, location, services and key pages."))

    # ---- Structured data ----------------------------------------------------------
    wanted = SCHEMA_TYPES.get(client.category, set())
    specific = types & wanted; generic = types & GENERIC_TYPES
    add(Check("Structured data", "Business type in schema.org",
              PASS if specific else WARN if generic else FAIL,
              (f"Marked up as {', '.join(sorted(specific))}." if specific else
               f"Only generic types ({', '.join(sorted(generic))})." if generic else "No schema.org business markup on the home page."),
              f"Add JSON-LD with @type {sorted(wanted)[0] if wanted else 'LocalBusiness'}, name, address, telephone and url.",
              weight=3))
    biz = next((n for n in nodes if _types([n]) & (wanted | GENERIC_TYPES)), {})
    addr = json.dumps(biz.get("address", "")) if biz else ""
    add(Check("Structured data", "Address and phone in schema",
              PASS if biz and _has(addr, client.city) and biz.get("telephone") else WARN if biz else FAIL,
              ("Schema includes the address in " + client.city + " and a phone number.") if biz and _has(addr, client.city) and biz.get("telephone")
              else ("Schema is missing the city in the address or the telephone." if biz else "No business schema to hold them."),
              f"Include a PostalAddress with addressLocality \"{client.city}\" and a telephone in the business schema.",
              weight=2))
    if client.category in ("hospital", "clinic"):
        add(Check("Structured data", "Doctors marked up (Physician)", PASS if "Physician" in types else WARN,
                  "Physician schema found." if "Physician" in types else "No Physician schema on the home page.",
                  "Give each doctor a page with schema.org Physician: name, specialty, and the hospital as their workplace."))
    faq = "FAQPage" in types or re.search(r"\b(faq|frequently asked)", text, re.I)
    add(Check("Structured data", "FAQs", PASS if "FAQPage" in types else WARN if faq else FAIL,
              "FAQPage schema found." if "FAQPage" in types else "FAQs are on the page but not marked up." if faq else "No FAQs found.",
              "Answer the questions customers ask AI on your pages, and mark them up as FAQPage."))

    # ---- Content ------------------------------------------------------------------
    names = client.brand_names
    title_ok = any(_has(page.title, n) for n in names)
    add(Check("Content", "Business name in the page title", PASS if title_ok else FAIL,
              f"Title: \"{page.title.strip()[:80]}\"" if page.title.strip() else "The home page has no title.",
              f"Put \"{client.name}\" in the home page title.", weight=2))
    city_in_title = _has(page.title, client.city) or _has(page.description, client.city)
    add(Check("Content", "City in the title or description", PASS if city_in_title else WARN,
              f"{client.city} appears in the title or meta description." if city_in_title
              else f"{client.city} isn't in the title or meta description.",
              f"Write a title and meta description like \"{client.name} | {client.category.title()} in {client.city}\".",
              weight=2))
    add(Check("Content", "City on the home page", PASS if _has(text, client.city) else FAIL,
              f"The page mentions {client.city}." if _has(text, client.city) else f"The page never mentions {client.city}.",
              f"Say where you are in the page text: \"{client.category.title()} in {client.city}\", plus the full address."))
    add(Check("Content", "Meta description", PASS if len(page.description.strip()) >= 50 else WARN,
              "Has a meta description." if len(page.description.strip()) >= 50 else "Missing or very short meta description.",
              "Add a 120-160 character description naming the business, city and main services."))
    for svc in client.services:
        if not svc.page:
            continue
        p = fetch(urljoin(root, svc.page))
        if p.status == 0 or p.status >= 400:
            add(Check("Content", f"{svc.name} page", FAIL, f"{svc.page} doesn't open ({p.status or 'no response'}).",
                      f"Publish a page at {svc.page} about {svc.name} in {client.city}.", weight=2))
            continue
        pr = _read(p.text); ptext = " ".join(pr.text)
        good = _has(ptext, svc.name) and _has(ptext, client.city)
        add(Check("Content", f"{svc.name} page", PASS if good else WARN,
                  f"{svc.page} covers {svc.name} and names {client.city}." if good
                  else f"{svc.page} doesn't mention both {svc.name} and {client.city}.",
                  f"On {svc.page}, say plainly that you offer {svc.name} in {client.city}, with FAQs.", weight=2))

    # ---- Consistency --------------------------------------------------------------
    known = {_digits(p) for p in client.phones + [l.phone for l in client.listings] if _digits(p)}
    found = {_digits(m) for m in re.findall(r"\+?\d[\d\s\-()]{8,}\d", text) if len(_digits(m)) == 10}
    if known:
        match = known & found
        add(Check("Consistency", "Phone number matches listings", PASS if match else WARN,
                  "The phone number on the site matches a listing." if match
                  else "None of the listed phone numbers appear on the home page.",
                  "Show the same phone number on the site, Google Business Profile and directories.", weight=2))
    return audit
