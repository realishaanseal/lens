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
from ui.theme import ACCENT, INK, MUTED, TOOL_COLORS, bars, delta_badge, empty_state, fixes, hero, kpis, section

store = get_store()

# ---- Sidebar: client, month, run a check --------------------------------------
client = client_picker()
if client is None:
    hero("Welcome", "Varaxis Lens", "Track whether ChatGPT, Gemini and Perplexity recommend your business.")
    empty_state("🏥", "Add your first business",
                "Tell Lens the business name, city, services and competitors. It writes the questions for you.")
    st.page_link("ui/clients.py", label="Add a client", icon=":material/add_circle:")
    st.stop()

with st.sidebar:

    months = periods(store, client.id)
    period = st.selectbox("Month", list(reversed(months))) if months else None

    st.divider()
    st.markdown("**Run a check**")
    keyed = available_providers()
    use_mock = st.toggle("Offline mock answers", value=not keyed,
                         help="Use generated answers instead of real API calls. Handy for demos.")
    chosen = st.multiselect("AI tools", PROVIDERS, default=list(PROVIDERS) if use_mock else keyed,
                            format_func=TOOL_NAMES.get)
    limit = st.number_input("Questions", 1, client.max_prompts, client.max_prompts)
    run_period = st.text_input("File under month", current_period())
    if st.button("Run check", type="primary", disabled=not chosen, icon=":material/play_arrow:", width="stretch"):
        try:
            providers = [MockProvider(n, client) if use_mock else get_provider(n, client) for n in chosen]
        except (ValueError, ProviderError) as exc:
            st.error(str(exc))
        else:
            bar = st.progress(0.0, "Starting…")
            run_check(client, providers, store, period=run_period, limit=int(limit),
                      progress=lambda done, total, label: bar.progress(done / total, label[:60]))
            st.rerun()
    if not months and st.button("Load demo data", help="Five months of mock answers, to look around"):
        seed_demo(client, store)
        st.rerun()

location = " · ".join(x for x in [client.category.title(), client.city, client.area] if x)
hero("AI visibility report", client.name, location,
     chip=f"Report for {period}" if period else None)

if not period:
    empty_state("🔍", "No checks yet",
                "Lens will ask ChatGPT, Gemini and Perplexity the questions your customers ask, "
                "and show whether they recommend you.",
                [("Add API keys", "On Settings. No keys? Turn on mock answers in the sidebar."),
                 ("Run a check", "Press Run check in the sidebar. A full check takes a few minutes."),
                 ("Act on fixes", "See who AI recommends instead and what to change.")])
    section("Questions that will be asked", f"{len(build_prompts(client))} questions")
    st.dataframe(pd.DataFrame([{"Language": LANG_NAMES.get(p.language, p.language), "Question": p.text}
                               for p in build_prompts(client)]), hide_index=True, width="stretch")
    st.stop()

summary = summarize(store, client.id, period)
results = latest_results(store, client.id, period)
suggestions = suggest(client, results)

# ---- KPI row -------------------------------------------------------------------
kpis([
    {"label": "Mention rate", "value": pct(summary.mention_rate), "hero": True,
     "progress": summary.mention_rate or 0,
     "foot": f"{delta_badge(summary.change)} &nbsp;vs last month"},
    {"label": "Questions tested", "value": summary.prompts_tested,
     "foot": f"{summary.answers} AI answers across {len(summary.by_provider)} tools"},
    {"label": "Top competitor", "value": summary.top_competitor or "–", "small": True,
     "foot": "Named most often instead of you"},
    {"label": "AI visits", "value": "–" if summary.ai_visits is None else f"{summary.ai_visits:,.0f}",
     "foot": "GA4 'AI Assistant' users" if summary.ai_visits is not None else "Add GA4 numbers in Settings"},
])
if summary.errors:
    failures = store.query(
        "SELECT provider, error, COUNT(*) AS n FROM results WHERE client_id = ? AND period = ? "
        "AND error IS NOT NULL GROUP BY provider, error ORDER BY n DESC LIMIT 5", (client.id, period))
    with st.expander(f"{summary.errors} AI calls failed this month and are left out of the mention rate",
                     icon=":material/warning:"):
        for row in failures:
            st.markdown(f"**{TOOL_NAMES.get(row['provider'], row['provider'])}** ({row['n']}×)")
            st.code(row["error"][:400], language=None)
        if any("401" in row["error"] or "403" in row["error"] for row in failures):
            st.info("Looks like an API key problem. Check your keys on the **Settings** page.")

# ---- Trend + suggestions -----------------------------------------------------
left, right = st.columns([3, 2], gap="large")
with left:
    with st.container(border=True):
        head, toggle = st.columns([3, 2], vertical_alignment="center")
        with head:
            section("Mention rate over time", "")
        view = toggle.segmented_control("Show", ["All tools", "By AI tool"], default="All tools",
                                        label_visibility="collapsed") or "All tools"
        df = pd.DataFrame(trend(store, client.id)).rename(columns={**TOOL_NAMES, "overall": "All tools"})
        cols = ["All tools"] if view == "All tools" else [c for c in df.columns if c in TOOL_NAMES.values()]
        long = df.melt(id_vars="period", value_vars=cols, var_name="Tool", value_name="rate").dropna()
        scale = alt.Scale(domain=list(TOOL_COLORS), range=list(TOOL_COLORS.values()))
        base = alt.Chart(long).encode(
            x=alt.X("period:O", title=None, axis=alt.Axis(labelAngle=0, ticks=False, domain=False)),
            y=alt.Y("rate:Q", title=None, scale=alt.Scale(domain=[0, 1]),
                    axis=alt.Axis(format="%", tickCount=5, domain=False, ticks=False, gridColor="#EEECE8")),
            color=alt.Color("Tool:N", scale=scale, legend=alt.Legend(orient="top", title=None)
                            if view != "All tools" else None),
            tooltip=[alt.Tooltip("period:O", title="Month"), "Tool:N", alt.Tooltip("rate:Q", format=".0%", title="Mention rate")],
        )
        if view == "All tools":
            chart = base.mark_area(line={"color": ACCENT, "strokeWidth": 2.5}, opacity=0.16, color=ACCENT,
                                   interpolate="monotone") + base.mark_point(filled=True, size=70, color=ACCENT)
        else:
            chart = base.mark_line(strokeWidth=2.5, interpolate="monotone") + base.mark_point(filled=True, size=55)
        st.altair_chart(chart.properties(height=290).configure_view(stroke=None)
                        .configure_axis(labelColor=MUTED, labelFont="Inter"), width="stretch")
with right:
    with st.container(border=True, height=376):
        section("Suggested fixes", f"{len(suggestions)} this month" if suggestions else "")
        if not suggestions:
            st.success("Nothing urgent this month.", icon=":material/check_circle:")
        fixes([(s.title, s.detail) for s in suggestions])

# ---- Breakdown -----------------------------------------------------------------
a, b, c = st.columns(3, gap="medium")
with a, st.container(border=True, height=330):
    section("By AI tool")
    bars([(TOOL_NAMES.get(k, k), v, pct(v)) for k, v in summary.by_provider.items()], colors=TOOL_COLORS)
with b, st.container(border=True, height=330):
    section("By language")
    bars([(LANG_NAMES.get(k, k), v, pct(v)) for k, v in summary.by_language.items()], color="#F59E0B")
with c, st.container(border=True, height=330):
    section("Who AI recommends instead")
    bars([(n, share, f"{cnt} · {pct(share)}") for n, cnt, share in summary.top_competitors[:6]], color=INK)

# ---- Traffic -------------------------------------------------------------------
history = traffic(store, client.id)
if history:
    section("Website traffic", "GA4 + Search Console")
    labels = {"ga4.ai_assistant_users": "AI Assistant users", "ga4.organic_users": "Organic users",
              "gsc.clicks": "Search clicks", "gsc.impressions": "Search impressions"}
    table = pd.DataFrame(history).T.sort_index().rename(columns=labels)
    st.dataframe(table.style.format("{:,.0f}"), width="stretch")

# ---- Answers explorer ----------------------------------------------------------
section("Every answer", "Exactly what each AI said")
f1, f2, f3 = st.columns(3)
tool = f1.selectbox("AI tool", ["All", *summary.by_provider], format_func=lambda k: TOOL_NAMES.get(k, k))
status = f2.selectbox("Named you?", ["All", "Yes", "No"])
query = f3.text_input("Search questions")
rows = [r for r in results
        if (tool == "All" or r["provider"] == tool)
        and (status == "All" or bool(r["mentioned"]) == (status == "Yes"))
        and query.lower() in r["prompt"].lower()]
st.caption(f"{len(rows)} of {len(results)} answers · :green[●] named you · :red[●] did not")
for r in sorted(rows, key=lambda r: (r["prompt"], r["provider"])):
    mark = ":green[●]" if r["mentioned"] else ":red[●]"
    with st.expander(f"{mark}  **{TOOL_NAMES.get(r['provider'], r['provider'])}** · {r['prompt']}"):
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
                       file_name=f"{client.id}-{period}.pdf", mime="application/pdf",
                       icon=":material/download:", width="stretch", type="secondary")
