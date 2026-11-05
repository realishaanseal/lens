"""Settings page: AI tool connections and website traffic numbers."""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import streamlit as st

from lens.providers import DEFAULT_MODELS
from lens.settings import save_env
from lens.store import current_period
from lens.traffic import import_csv
from ui.common import client_picker, get_store
from ui.theme import gap, header, month_label, rule, section

PROVIDER_ROWS = [
    ("OPENAI_API_KEY", "openai", "ChatGPT", "https://platform.openai.com/api-keys"),
    ("GEMINI_API_KEY", "gemini", "Gemini", "https://aistudio.google.com/apikey"),
    ("PERPLEXITY_API_KEY", "perplexity", "Perplexity", "https://www.perplexity.ai/account/api/keys"),
]

CONNECTED = ('<div style="text-align:right"><span class="lx-tag" '
             'style="color:#15803D;border-color:#BBF7D0;background:#F0FDF4">Connected</span></div>')
NOT_CONNECTED = '<div style="text-align:right"><span class="lx-tag">Not connected</span></div>'

client = client_picker()
header("Settings", "Connect AI tools and add website traffic numbers.")
rule()

# ---- AI tools ------------------------------------------------------------------
with st.form("keys", border=False):
    f = section("AI tools", "API keys used to ask each tool. Leave a field blank to keep the saved key. "
                "On a hosted deployment, set keys in the host's secrets instead.", first=True)
    updates: dict[str, str] = {}
    for key, provider, label, link in PROVIDER_ROWS:
        is_set = bool(os.environ.get(key) or (key == "GEMINI_API_KEY" and os.environ.get("GOOGLE_API_KEY")))
        with f.container(border=True):
            top, status = st.columns([3, 1], vertical_alignment="center")
            top.markdown(f"**{label}**")
            status.html(CONNECTED if is_set else NOT_CONNECTED)
            a, b = st.columns([3, 2])
            value = a.text_input("API key", type="password", key=f"key-{key}",
                                 placeholder="Saved" if is_set else "Paste key", help=f"Get one at {link}")
            model_key = f"LENS_{provider.upper()}_MODEL"
            model = b.text_input("Model", os.environ.get(model_key, ""), placeholder=DEFAULT_MODELS[provider],
                                 key=model_key)
            remove = st.checkbox("Remove saved key", key=f"rm-{key}", disabled=not is_set) if is_set else False
        if value.strip():
            updates[key] = value
        elif remove:
            updates[key] = ""
        updates[model_key] = model
    _, save = f.columns([3, 1])
    if save.form_submit_button("Save", type="primary", width="stretch"):
        save_env(updates)
        st.toast("Settings saved", icon=":material/check:")
        st.rerun()

# ---- Traffic -------------------------------------------------------------------
if client is None:
    rule()
    st.caption("Add a client to record website traffic.")
    st.stop()
store = get_store()

with st.form("traffic", border=False):
    f = section("Website traffic", f"Monthly GA4 and Search Console numbers for {client.name}, shown next "
                "to AI mentions on the dashboard.")
    period = f.text_input("Month", current_period(), help="Format YYYY-MM")
    a, b = f.columns(2)
    ai = a.number_input("GA4 AI Assistant users", 0, step=1)
    organic = b.number_input("GA4 organic users", 0, step=1)
    a, b = f.columns(2)
    clicks = a.number_input("Search Console clicks", 0, step=1)
    impressions = b.number_input("Search Console impressions", 0, step=1)
    _, save = f.columns([3, 1])
    if save.form_submit_button("Save month", width="stretch"):
        if len(period) != 7 or period[4] != "-" or not period.replace("-", "").isdigit():
            st.error("Month must look like 2026-10.")
        else:
            for source, metric, value in [("ga4", "ai_assistant_users", ai), ("ga4", "organic_users", organic),
                                          ("gsc", "clicks", clicks), ("gsc", "impressions", impressions)]:
                store.set_traffic(client.id, period, source, metric, value)
            st.toast(f"Saved {month_label(period)}", icon=":material/check:")

f = section("Import from CSV", "Columns: period, source, metric, value. Useful for importing several months at once.")
upload = f.file_uploader("CSV file", type="csv", label_visibility="collapsed")
if upload is not None and f.button("Import"):
    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as fh:
        fh.write(upload.getvalue())
    try:
        f.success(f"Imported {import_csv(store, client.id, fh.name)} rows.")
    except ValueError as exc:
        f.error(str(exc))
    finally:
        os.unlink(fh.name)

rows = store.query("SELECT period, source, metric, value FROM traffic WHERE client_id = ? ORDER BY period DESC",
                   (client.id,))
if rows:
    gap()
    labels = {("ga4", "ai_assistant_users"): "AI Assistant users", ("ga4", "organic_users"): "Organic users",
              ("gsc", "clicks"): "Search clicks", ("gsc", "impressions"): "Search impressions"}
    df = pd.DataFrame([dict(r) for r in rows])
    table = df.pivot_table(index="period", columns=["source", "metric"], values="value").sort_index(ascending=False)
    table.columns = [labels.get(col, " ".join(col)) for col in table.columns]
    table.index = [month_label(p) for p in table.index]
    st.dataframe(table.style.format("{:,.0f}"), width="stretch")
