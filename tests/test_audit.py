import json

from lens.audit import FAIL, PASS, Audit, Page, run_audit

SCHEMA = {"@context": "https://schema.org", "@graph": [
    {"@type": "Hospital", "name": "SSHRI Hospital", "telephone": "+91 90000 00001",
     "address": {"@type": "PostalAddress", "addressLocality": "Krishnanagar"}},
    {"@type": "FAQPage", "mainEntity": []},
    {"@type": "Physician", "name": "Dr. Ananya Roy"},
]}

GOOD_HOME = f"""<html><head><title>SSHRI Hospital | Hospital in Krishnanagar</title>
<meta name="description" content="SSHRI Hospital in Krishnanagar: cardiology, nephrology and 24 hour emergency care for the district.">
<script type="application/ld+json">{json.dumps(SCHEMA)}</script></head>
<body><h1>SSHRI Hospital</h1><p>Multispeciality hospital in Krishnanagar. Call +91 90000 00001.</p></body></html>"""


def site(pages):
    def fetch(url):
        for path, (status, text) in pages.items():
            if url.endswith(path):
                return Page(url, status, text)
        return Page(url, 404, "")
    return fetch


def by_name(audit):
    return {c.name: c for c in audit.checks}


def test_well_prepared_site_scores_high(client):
    client.website = "https://example.org"
    client.listings[0].phone = "+91 90000 00001"
    pages = {"example.org": (200, GOOD_HOME), "/robots.txt": (200, "User-agent: *\nAllow: /\nSitemap: https://example.org/sitemap.xml"),
             "/llms.txt": (200, "SSHRI Hospital"), "/cardiology": (200, "<p>Cardiology in Krishnanagar</p>")}
    for s in client.services:
        if s.page and s.page != "/cardiology":
            pages[s.page] = (200, f"<p>{s.name} at our hospital in Krishnanagar</p>")
    audit = run_audit(client, site(pages))
    checks = by_name(audit)
    assert audit.error is None
    assert checks["AI crawlers allowed"].status == PASS
    assert checks["Business type in schema.org"].status == PASS
    assert checks["Address and phone in schema"].status == PASS
    assert checks["Business name in the page title"].status == PASS
    assert audit.score >= 90


def test_blocked_crawlers_and_missing_markup_are_flagged(client):
    client.website = "example.org"   # no scheme: https is assumed
    robots = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: PerplexityBot\nDisallow: /\n"
    audit = run_audit(client, site({"example.org": (200, "<html><title>Home</title><body>Welcome</body></html>"),
                                    "/robots.txt": (200, robots)}))
    checks = by_name(audit)
    assert checks["AI crawlers allowed"].status == FAIL
    assert "GPTBot" in checks["AI crawlers allowed"].detail and "PerplexityBot" in checks["AI crawlers allowed"].detail
    assert checks["Business type in schema.org"].status == FAIL
    assert checks["City on the home page"].status == FAIL
    assert audit.score < 40


def test_unreachable_site_and_round_trip(client):
    client.website = "https://down.example"
    audit = run_audit(client, lambda url: Page(url, 0, "timed out"))
    assert audit.error and not audit.checks
    client.website = None
    assert run_audit(client).error
    again = Audit.from_json(run_audit(client, site({})).to_json())
    assert again.error
