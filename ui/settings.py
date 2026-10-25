"""Settings page: API keys, models, and GA4 / Search Console numbers."""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import streamlit as st

from lens.providers import DEFAULT_MODELS
from lens.settings import KEYS, save_env
from lens.store import current_period
from lens.traffic import import_csv
from ui.common import client_picker, get_store

st.title("Settings")

# ---- API keys ------------------------------------------------------------------
st.subheader("AI tools")
st.caption("Keys are saved to a .env file on this computer only. Leave a key blank to keep it; "
           "tick Remove to delete it.")

with st.form("keys"):
    updates: dict[str, str] = {}
    for key, provider, link in [
        ("OPENAI_API_KEY", "openai", "https://platform.openai.com/api-keys"),
        ("GEMINI_API_KEY", "gemini", "https://aistudio.google.com/apikey"),
        ("PERPLEXITY_API_KEY", "perplexity", "https://www.perplexity.ai/account/api/keys"),
    ]:
        is_set = bool(os.environ.get(key) or (key == "GEMINI_API_KEY" and os.environ.get("GOOGLE_API_KEY")))
        a, b, d = st.columns([3, 2, 1])
        value = a.text_input(f"{KEYS[key]}{' ✅' if is_set else ''}", type="password",
                             placeholder="saved" if is_set else "not set", help=f"Get one at {link}")
        model_key = f"LENS_{provider.upper()}_MODEL"
        model = b.text_input("Model", os.environ.get(model_key, ""), placeholder=DEFAULT_MODELS[provider],
                             key=model_key)
        remove = d.checkbox("Remove", key=f"rm-{key}", disabled=not is_set)
        if value.strip():
            updates[key] = value
        elif remove:
            updates[key] = ""
        updates[model_key] = model
    if st.form_submit_button("Save", type="primary"):
        save_env(updates)
        st.success("Saved.")
        st.rerun()

# ---- Traffic -------------------------------------------------------------------
st.divider()
st.subheader("Website traffic")
client = client_picker()
if client is None:
    st.info("Add a client first.")
    st.stop()
store = get_store()

st.caption(f"Monthly numbers for **{client.name}** from GA4 and Search Console, shown next to AI mentions.")
with st.form("traffic"):
    period = st.text_input("Month (YYYY-MM)", current_period())
    a, b, c, d = st.columns(4)
    ai = a.number_input("GA4 'AI Assistant' users", 0, step=1)
    organic = b.number_input("GA4 organic users", 0, step=1)
    clicks = c.number_input("Search Console clicks", 0, step=1)
    impressions = d.number_input("Search Console impressions", 0, step=1)
    if st.form_submit_button("Save month"):
        if len(period) != 7 or period[4] != "-" or not period.replace("-", "").isdigit():
            st.error("Month must look like 2026-10.")
        else:
            for source, metric, value in [("ga4", "ai_assistant_users", ai), ("ga4", "organic_users", organic),
                                          ("gsc", "clicks", clicks), ("gsc", "impressions", impressions)]:
                store.set_traffic(client.id, period, source, metric, value)
            st.success(f"Saved {period}.")

upload = st.file_uploader("Or upload a CSV (period, source, metric, value)", type="csv")
if upload is not None and st.button("Import CSV"):
    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as fh:
        fh.write(upload.getvalue())
    try:
        st.success(f"Imported {import_csv(store, client.id, fh.name)} rows.")
    except ValueError as exc:
        st.error(str(exc))
    finally:
        os.unlink(fh.name)

rows = store.query("SELECT period, source, metric, value FROM traffic WHERE client_id = ? ORDER BY period DESC",
                   (client.id,))
if rows:
    df = pd.DataFrame([dict(r) for r in rows])
    st.dataframe(df.pivot_table(index="period", columns=["source", "metric"], values="value").sort_index(ascending=False),
                 width="stretch")
