"""Dashboard page: this month's numbers, trend, fixes and every answer."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lens.metrics import latest_results, periods, summarize, traffic, trend
from lens.prompts import build_prompts
from lens.providers import PROVIDERS, MockProvider, ProviderError, available_providers, get_provider
from lens.report import build_report
from lens.runner import run_check, seed_demo
from lens.store import current_period
from lens.suggest import suggest
from ui.common import LANG_NAMES, TOOL_NAMES, client_picker, get_store, pct
from ui.theme import (INK, LINE, MUTED, SERIES, change_text, cta, fixes, gap, heading, identity, month_label, rows,
                      rule, stats)

store = get_store()
LANG_LABEL = {"en": "English", "bn": "Bengali", "banglish": "Banglish"}


@st.dialog("Run a check", width="medium")
def run_dialog(client) -> None:
    keyed = available_providers()
    st.caption(f"Lens asks each AI tool the customer questions for {client.name} and records who it recommends.")
    use_mock = st.toggle("Use sample answers", value=not keyed,
                         help="Generated answers instead of real API calls, for demos and testing.")
    if not keyed and not use_mock:
        st.warning("No AI tool is connected yet. Add an API key in Settings, or use sample answers.",
                   icon=":material/key:")
    chosen = st.pills("AI tools", PROVIDERS, selection_mode="multi", format_func=TOOL_NAMES.get,
                      default=list(PROVIDERS) if use_mock else keyed)
    total = len(build_prompts(client))
    a, b = st.columns(2)
    limit = a.number_input("Questions per tool", 1, total, total)
    run_period = b.text_input("Month", current_period(), help="Format YYYY-MM")
    calls = len(chosen or []) * int(limit)
    st.caption(f"{calls} AI requests" + ("" if use_mock else " · usually a few minutes"))
    if st.button("Start check", type="primary", width="stretch", disabled=not chosen or (not keyed and not use_mock)):
        try:
            providers = [MockProvider(n, client) if use_mock else get_provider(n, client) for n in chosen]
        except (ValueError, ProviderError) as exc:
            st.error(str(exc))
            return
        bar = st.progress(0.0, "Starting")
        run_check(client, providers, store, period=run_period, limit=int(limit),
                  progress=lambda done, total, label: bar.progress(done / total, label[:56]))
        st.session_state["period"] = run_period
        st.rerun()


def explain(error: str) -> str:
    """Plain-language reason and fix for a provider error."""
    e = error.lower()
    if any(code in e for code in ("401", "403", "api key not valid", "invalid api key", "permission")):
        return "The API key was rejected. Check it is copied in full and active, then update it in Settings."
    if "429" in e or "quota" in e or "rate limit" in e or "resource_exhausted" in e:
        return ("The tool's rate limit or free quota was reached. Wait a minute and run fewer questions, "
                "or enable billing on the API account.")
    if "404" in e or "not found" in e:
        return "The model name isn't available on this account. Clear the Model field in Settings to use the default."
    if "timed out" in e or "timeout" in e or "connection" in e:
        return "The tool didn't respond in time. This is usually temporary; try again."
    return "The tool returned an error. The details below can help."


def failure_panel(title: str, expanded: bool) -> None:
    failures = store.query(
        "SELECT provider, error, COUNT(*) AS n FROM results WHERE client_id = ? AND period = ? "
        "AND error IS NOT NULL GROUP BY provider, error ORDER BY n DESC LIMIT 5", (client.id, period))
    with st.expander(title, expanded=expanded, icon=":material/error:"):
        for i, row in enumerate(failures):
            if i:
                st.divider()
            st.markdown(f"**{TOOL_NAMES.get(row['provider'], row['provider'])}** · {row['n']} "
                        f"{'request' if row['n'] == 1 else 'requests'}")
            st.markdown(explain(row["error"]))
            st.code(row["error"][:500], language=None, wrap_lines=True)
        st.page_link("ui/settings.py", label="Open Settings", icon=":material/arrow_forward:")


# ---- No client yet -------------------------------------------------------------
client = client_picker()
if client is None:
    identity("Varaxis Lens", ["AI visibility tracking"])
    rule()
    cta("Add your first business",
        "Lens builds the questions customers actually ask AI assistants from the business name, "
        "location and services, then tracks who gets recommended.")
    st.page_link("ui/clients.py", label="Add a client", icon=":material/arrow_forward:")
    st.stop()

# ---- Sidebar -------------------------------------------------------------------
months = periods(store, client.id)
with st.sidebar:
    period = None
    if months:
        options = list(reversed(months))
        wanted = st.session_state.get("period")
        period = st.selectbox("Month", options, index=options.index(wanted) if wanted in options else 0,
                              format_func=month_label)
        st.session_state["period"] = period

# ---- Header --------------------------------------------------------------------
location = ", ".join(x for x in [client.city, client.area] if x)
languages = " · ".join(LANG_LABEL[l] for l in client.active_languages)
head, actions = st.columns([3, 2], vertical_alignment="center")
with head:
    identity(client.name, [client.category.title(), location, languages,
                           month_label(period) if period else ""])
with actions:
    if period:
        x, y = st.columns(2)
        report_slot = x.empty()
        if y.button("Run check", type="primary", icon=":material/play_arrow:", width="stretch"):
            run_dialog(client)
rule()

if not period:
    prompts = build_prompts(client)
    cta("Run your first check",
        f"Lens will ask ChatGPT, Gemini and Perplexity {len(prompts)} questions customers ask about "
        f"{client.category}s in {client.city}, and show whether {client.name} is recommended, who is "
        "recommended instead, and what to fix.")
    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button("Run first check", type="primary", width="stretch"):
        run_dialog(client)
    if c2.button("Explore sample data", width="stretch",
                 help="Five months of generated answers so you can see a full dashboard."):
        with st.spinner("Generating sample months"):
            seed_demo(client, store)
        st.rerun()
    gap()
    heading("Questions Lens will ask", f"{len(prompts)} total")
    st.dataframe(pd.DataFrame([{"Language": LANG_NAMES.get(p.language, p.language), "Question": p.text}
                               for p in prompts]), hide_index=True, width="stretch")
    st.stop()

summary = summarize(store, client.id, period)
results = latest_results(store, client.id, period)
suggestions = sorted(suggest(client, results), key=lambda s: s.priority)
idx = months.index(period)
previous = month_label(months[idx - 1]).split()[0] if idx > 0 else "last month"
report_slot.download_button("Export PDF", build_report(client, summary, suggestions, store),
                            file_name=f"{client.id}-{period}.pdf", mime="application/pdf",
                            icon=":material/download:", width="stretch")

if summary.answers == 0:
    cta("This check didn't get any answers",
        f"All {summary.errors} requests to the AI tools failed, so there is nothing to measure for "
        f"{month_label(period)} yet. The reason is below. Fix it, then run the check again.")
    gap()
    failure_panel("What went wrong", expanded=True)
    st.stop()

# ---- Headline numbers ----------------------------------------------------------
stats([
    {"label": "Mention rate", "value": pct(summary.mention_rate), "foot": change_text(summary.change, previous)},
    {"label": "Questions tested", "value": summary.prompts_tested,
     "foot": f"{summary.answers} answers from {len(summary.by_provider)} AI tools"},
    {"label": "Top competitor", "value": summary.top_competitor or "None", "text": True,
     "foot": (f"In {pct(summary.top_competitors[0][2])} of answers" if summary.top_competitors else "No competitors named")},
    {"label": "Visits from AI", "value": "–" if summary.ai_visits is None else f"{summary.ai_visits:,.0f}",
     "foot": "GA4 AI Assistant users" if summary.ai_visits is not None else "Add GA4 numbers in Settings"},
])

if summary.errors:
    failure_panel(f"{summary.errors} requests failed and are left out of the mention rate", expanded=False)

# ---- Trend and fixes -----------------------------------------------------------
left, right = st.columns([7, 5], gap="large")
with left:
    h, t = st.columns([3, 2], vertical_alignment="bottom")
    with h:
        heading("Mention rate by month")
    view = t.segmented_control("View", ["Overall", "By tool"], default="Overall",
                               label_visibility="collapsed") or "Overall"
    df = pd.DataFrame(trend(store, client.id), columns=["period", "overall", *TOOL_NAMES])
    df = df.rename(columns={**TOOL_NAMES, "overall": "All tools"})
    df["month"] = df["period"].map(lambda p: month_label(p)[:3] + " " + p[2:4])
    cols = ["All tools"] if view == "Overall" else [c for c in TOOL_NAMES.values() if df[c].notna().any()]
    long = df.melt(id_vars=["period", "month"], value_vars=cols, var_name="Tool", value_name="rate").dropna()
    order = list(df["month"])
    enc = dict(
        x=alt.X("month:O", sort=order, title=None, axis=alt.Axis(labelAngle=0, ticks=False, domainColor=LINE, labelPadding=8)),
        y=alt.Y("rate:Q", title=None, scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format="%", tickCount=4, domain=False, ticks=False, gridColor="#F4F4F5", labelPadding=8)),
        tooltip=[alt.Tooltip("month:O", title="Month"), alt.Tooltip("Tool:N"),
                 alt.Tooltip("rate:Q", format=".0%", title="Mention rate")],
    )
    if view == "Overall":
        base = alt.Chart(long).encode(**enc)
        chart = (base.mark_area(color=INK, opacity=0.05, interpolate="linear")
                 + base.mark_line(color=INK, strokeWidth=1.75) + base.mark_point(color=INK, filled=True, size=28))
    else:
        scale = alt.Scale(domain=cols, range=[SERIES[c] for c in cols])
        base = alt.Chart(long).encode(**enc, color=alt.Color("Tool:N", scale=scale,
                                      legend=alt.Legend(orient="top-left", title=None, symbolType="stroke")))
        chart = base.mark_line(strokeWidth=1.75) + base.mark_point(filled=True, size=24)
    st.altair_chart(chart.properties(height=260).configure_view(stroke=None)
                    .configure_axis(labelColor=MUTED, labelFont="Inter", labelFontSize=11)
                    .configure_legend(labelColor=MUTED, labelFont="Inter", labelFontSize=11), width="stretch")
with right:
    heading("Suggested fixes", f"{len(suggestions)} open" if suggestions else "")
    if suggestions:
        with st.container(height=300, border=False):
            fixes([(s.title, s.detail, s.priority) for s in suggestions])
    else:
        st.caption("Nothing needs attention this month.")

gap()

# ---- Breakdown -----------------------------------------------------------------
a, b, c = st.columns(3, gap="large")
with a:
    heading("By AI tool")
    rows([(TOOL_NAMES.get(k, k), v, pct(v)) for k, v in sorted(summary.by_provider.items(), key=lambda kv: -kv[1])])
with b:
    heading("By language")
    rows([(LANG_NAMES.get(k, k), v, pct(v)) for k, v in sorted(summary.by_language.items(), key=lambda kv: -kv[1])])
with c:
    heading("Recommended instead", "share of answers")
    rows([(n, share, pct(share)) for n, _, share in summary.top_competitors[:5]])

# ---- Traffic -------------------------------------------------------------------
history = traffic(store, client.id)
if history:
    gap()
    heading("Website traffic", "GA4 and Search Console")
    labels = {"ga4.ai_assistant_users": "AI Assistant users", "ga4.organic_users": "Organic users",
              "gsc.clicks": "Search clicks", "gsc.impressions": "Search impressions"}
    table = pd.DataFrame(history).T.sort_index(ascending=False).rename(columns=labels)
    table.index = [month_label(p) for p in table.index]
    st.dataframe(table.style.format("{:,.0f}"), width="stretch")

# ---- Answers -------------------------------------------------------------------
gap()
heading("Answers", f"{len(results)} this month")
f1, f2, f3 = st.columns([1, 1, 2])
tool = f1.selectbox("AI tool", ["All", *summary.by_provider], format_func=lambda k: "All tools" if k == "All" else TOOL_NAMES.get(k, k))
status = f2.selectbox("Result", ["All", "Mentioned", "Not mentioned"])
query = f3.text_input("Search", placeholder="Filter by question")
shown = [r for r in results
         if (tool == "All" or r["provider"] == tool)
         and (status == "All" or bool(r["mentioned"]) == (status == "Mentioned"))
         and query.lower() in r["prompt"].lower()]
if len(shown) != len(results):
    st.caption(f"Showing {len(shown)} of {len(results)}")
for r in sorted(shown, key=lambda r: (r["prompt"], r["provider"])):
    icon = ":material/check:" if r["mentioned"] else ":material/close:"
    with st.expander(f"{r['prompt']}  ·  {TOOL_NAMES.get(r['provider'], r['provider'])}", icon=icon):
        facts = []
        if r["mentioned"]:
            facts.append(f"Matched “{r['matched_alias']}” ({r['match_score']:.2f})")
        comps = ", ".join(c["name"] for c in r["competitors"])
        if comps:
            facts.append(f"Also named: {comps}")
        facts.append(f"{r['model']} · {r['created_at'][:16]}")
        st.caption("  \n".join(facts))
        st.markdown(r["answer"])
