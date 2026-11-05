"""Website check page: the signals AI assistants rely on, read from the client's own site. Free."""

from __future__ import annotations

from html import escape

import streamlit as st

from lens.audit import FAIL, INFO, PASS, WARN, Audit, run_audit
from ui.common import client_picker, get_store
from ui.theme import cta, gap, header, heading, rule, stats

STATUS = {PASS: ("Pass", "#15803D", "#F0FDF4", "#DCFCE7"), WARN: ("Improve", "#9A5A12", "#FDF6EC", "#F5E1C8"),
          FAIL: ("Fix", "#B91C1C", "#FEF2F2", "#FEE2E2"), INFO: ("Optional", "#52525B", "#FAFAFA", "#ECECEE")}
AREAS = ["Access", "Structured data", "Content", "Consistency"]

store = get_store()
client = client_picker()
head, action = st.columns([4, 1], vertical_alignment="bottom")
with head:
    header("Website check", "What AI assistants can read on the site, and what to fix. Free: no AI key needed.")
if client is None:
    rule(); st.caption("Add a client first."); st.stop()

run = action.button("Check website", type="primary", icon=":material/travel_explore:", width="stretch",
                    disabled=not client.website)
rule()

if run:
    with st.spinner(f"Reading {client.website}"):
        audit = run_audit(client)
    store.save_audit(client.id, audit.score, audit.to_json())
    st.rerun()

row = store.last_audit(client.id)
if not client.website:
    cta("Add the website first", f"Lens needs {client.name}'s website address to check it. Add it on the Clients page.")
    st.page_link("ui/clients.py", label="Open Clients", icon=":material/arrow_forward:")
    st.stop()
if row is None:
    cta("Check how AI-ready the website is",
        "Lens reads the site the way AI crawlers do: whether they're allowed in, whether the pages say what the "
        f"business is and that it's in {client.city}, whether each service has a page, and whether the phone "
        "number matches the listings. It takes a few seconds and costs nothing.")
    st.stop()

audit = Audit.from_json(row["data"])
if audit.error:
    cta("Couldn't check the website", audit.error)
    st.stop()

counts = {s: sum(c.status == s for c in audit.checks) for s in (PASS, WARN, FAIL)}
stats([
    {"label": "AI readiness", "value": f"{audit.score}%" if audit.score is not None else "–",
     "foot": f"{audit.url.split('//')[-1].rstrip('/')}"},
    {"label": "Passed", "value": counts[PASS], "foot": f"of {len([c for c in audit.checks if c.status != INFO])} checks"},
    {"label": "To improve", "value": counts[WARN], "foot": "worth doing"},
    {"label": "To fix", "value": counts[FAIL], "foot": "do these first"},
])
st.caption(f"Checked {row['created_at'].replace('T', ' ')[:16]} UTC")


def badge(status: str) -> str:
    label, color, bg, border = STATUS[status]
    return (f'<span class="lx-tag" style="color:{color};background:{bg};border-color:{border}">{label}</span>')


order = {FAIL: 0, WARN: 1, PASS: 2, INFO: 3}
for area in AREAS:
    items = sorted([c for c in audit.checks if c.area == area], key=lambda c: (order[c.status], -c.weight))
    if not items:
        continue
    gap()
    heading(area, f"{sum(c.status == PASS for c in items)} of {len(items)} passing")
    html = ""
    for c in items:
        fix = (f'<div class="d" style="color:#3F3F46;margin-top:4px">{escape(c.fix)}</div>'
               if c.fix and c.status in (FAIL, WARN, INFO) else "")
        html += (f'<div class="lx-fix"><div class="t">{escape(c.name)} {badge(c.status)}</div>'
                 f'<div class="d">{escape(c.detail)}</div>{fix}</div>')
    st.html(html)
