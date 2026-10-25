"""Varaxis Lens dashboard.  Run:  streamlit run app.py"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lens.config import list_client_files, load_client
from lens.metrics import latest_results, periods, summarize, traffic, trend
from lens.prompts import build_prompts
from lens.providers import PROVIDERS, MockProvider, ProviderError, available_providers, get_provider
from lens.report import build_report
from lens.runner import run_check, seed_demo
from lens.store import Store, current_period
from lens.suggest import suggest

TOOL_NAMES = {"openai": "ChatGPT", "gemini": "Gemini", "perplexity": "Perplexity"}
LANG_NAMES = {"en": "English", "bn": "Bengali", "banglish": "Banglish", "custom": "Custom"}

st.set_page_config(page_title="Varaxis Lens", page_icon="🔍", layout="wide")


@st.cache_resource
def get_store() -> Store:
    return Store()


def pct(value: float | None) -> str:
    return "–" if value is None else f"{value:.0%}"


store = get_store()

# ---- Sidebar: client, month, run a check --------------------------------------
files = list_client_files()
if not files:
    st.error("No client configs found in clients/. Copy clients/sshri.yaml to get started.")
    st.stop()

with st.sidebar:
    st.title("Varaxis Lens")
    st.caption("Know if AI recommends you.")
    path = st.selectbox("Client", files, format_func=lambda p: load_client(p).name)
    client = load_client(path)

    months = periods(store, client.id)
    period = st.selectbox("Month", list(reversed(months))) if months else None

    st.divider()
    st.subheader("Run a check")
    keyed = available_providers()
    use_mock = st.toggle("Offline mock answers", value=not keyed,
                         help="Use generated answers instead of real API calls. Handy for demos.")
    chosen = st.multiselect("AI tools", PROVIDERS, default=list(PROVIDERS) if use_mock else keyed,
                            format_func=TOOL_NAMES.get)
    limit = st.number_input("Questions", 1, client.max_prompts, client.max_prompts)
    run_period = st.text_input("File under month", current_period())
    if st.button("Run check", type="primary", disabled=not chosen):
        try:
            providers = [MockProvider(n, client) if use_mock else get_provider(n, client) for n in chosen]
        except (ValueError, ProviderError) as exc:
            st.error(str(exc))
        else:
            bar = st.progress(0.0, "Starting…")
            run_check(client, providers, store, period=run_period, limit=int(limit),
                      progress=lambda done, total, label: bar.progress(done / total, label[:60]))
            st.rerun()
    if not months and st.button("Load demo data"):
        seed_demo(client, store)
        st.rerun()

st.title(client.name)
st.caption(f"{client.category.title()} · {client.city}" + (f" · {client.area}" if client.area else ""))

if not period:
    st.info("No checks yet. Run a check from the sidebar, or load demo data to look around.")
    with st.expander("Questions that will be asked"):
        st.dataframe(pd.DataFrame([{"Language": LANG_NAMES.get(p.language, p.language), "Question": p.text}
                                   for p in build_prompts(client)]), hide_index=True, width="stretch")
    st.stop()

summary = summarize(store, client.id, period)
results = latest_results(store, client.id, period)
suggestions = suggest(client, results)

# ---- KPI row -------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mention rate", pct(summary.mention_rate),
          None if summary.change is None else f"{summary.change * 100:+.0f} pts")
c2.metric("Questions tested", summary.prompts_tested, help=f"{summary.answers} AI answers")
c3.metric("Top competitor", summary.top_competitor or "–",
          help="Business AI names most often in this month's answers")
c4.metric("AI visits", "–" if summary.ai_visits is None else f"{summary.ai_visits:.0f}",
          help="GA4 'AI Assistant' users this month (import with `python -m lens import-traffic`)")
if summary.errors:
    st.warning(f"{summary.errors} AI calls failed this month and are left out of the mention rate.")

# ---- Trend + suggestions -----------------------------------------------------
left, right = st.columns([3, 2])
with left:
    st.subheader("Mentions in AI answers by month")
    df = pd.DataFrame(trend(store, client.id)).set_index("period")
    df = df.rename(columns={**TOOL_NAMES, "overall": "All tools"}) * 100
    view = st.radio("Show", ["All tools", "By AI tool"], horizontal=True, label_visibility="collapsed")
    if view == "All tools":
        st.bar_chart(df[["All tools"]], y_label="% of answers naming you", color="#E84E1B")
    else:
        st.line_chart(df.drop(columns="All tools"), y_label="% of answers naming you")
with right:
    st.subheader("Suggested fixes")
    if not suggestions:
        st.success("Nothing urgent this month.")
    for s in suggestions:
        with st.container(border=True):
            st.markdown(f"**{s.title}**")
            st.caption(s.detail)

# ---- Breakdown -----------------------------------------------------------------
a, b, c = st.columns(3)
with a:
    st.subheader("By AI tool")
    st.dataframe(pd.DataFrame([{"AI tool": TOOL_NAMES.get(k, k), "Mention rate": pct(v)}
                               for k, v in summary.by_provider.items()]), hide_index=True, width="stretch")
with b:
    st.subheader("By language")
    st.dataframe(pd.DataFrame([{"Language": LANG_NAMES.get(k, k), "Mention rate": pct(v)}
                               for k, v in summary.by_language.items()]), hide_index=True, width="stretch")
with c:
    st.subheader("Who AI recommends instead")
    st.dataframe(pd.DataFrame([{"Business": n, "Answers": cnt, "Share": pct(share)}
                               for n, cnt, share in summary.top_competitors[:10]]),
                 hide_index=True, width="stretch")

# ---- Traffic -------------------------------------------------------------------
history = traffic(store, client.id)
if history:
    st.subheader("Website traffic (GA4 + Search Console)")
    labels = {"ga4.ai_assistant_users": "AI Assistant users", "ga4.organic_users": "Organic users",
              "gsc.clicks": "Search clicks", "gsc.impressions": "Search impressions"}
    table = pd.DataFrame(history).T.sort_index().rename(columns=labels)
    st.dataframe(table.style.format("{:,.0f}"), width="stretch")

# ---- Answers explorer ----------------------------------------------------------
st.subheader("Every answer, dated")
f1, f2, f3 = st.columns(3)
tool = f1.selectbox("AI tool", ["All", *summary.by_provider], format_func=lambda k: TOOL_NAMES.get(k, k))
status = f2.selectbox("Named you?", ["All", "Yes", "No"])
query = f3.text_input("Search questions")
rows = [r for r in results
        if (tool == "All" or r["provider"] == tool)
        and (status == "All" or bool(r["mentioned"]) == (status == "Yes"))
        and query.lower() in r["prompt"].lower()]
st.caption(f"{len(rows)} answers")
for r in sorted(rows, key=lambda r: (r["prompt"], r["provider"])):
    mark = "✅" if r["mentioned"] else "❌"
    with st.expander(f"{mark}  {TOOL_NAMES.get(r['provider'], r['provider'])} — {r['prompt']}"):
        if r["mentioned"]:
            st.markdown(f"Matched **{r['matched_alias']}** (score {r['match_score']:.2f})")
        comps = ", ".join(c["name"] for c in r["competitors"])
        if comps:
            st.markdown(f"Also named: {comps}")
        st.caption(f"{r['model']} · {r['created_at']}")
        st.markdown(r["answer"])

# ---- Report download -----------------------------------------------------------
with st.sidebar:
    st.divider()
    st.download_button("Download monthly PDF", build_report(client, summary, suggestions, store),
                       file_name=f"{client.id}-{period}.pdf", mime="application/pdf")
