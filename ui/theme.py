"""Visual layer: global CSS and small HTML components used across pages."""

from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

ACCENT = "#E84E1B"
INK = "#16130F"
MUTED = "#6B665E"
GOOD = "#15803D"
BAD = "#B91C1C"
TOOL_COLORS = {"ChatGPT": "#10A37F", "Gemini": "#4F7BF7", "Perplexity": "#20808D", "All tools": ACCENT}

_CSS = """
<style>
:root { --accent:#E84E1B; --ink:#16130F; --muted:#6B665E; --line:#E7E5E0; --card:#FFFFFF; }
#MainMenu, footer, [data-testid="stDecoration"] { display:none !important; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1280px; }
h1, h2, h3 { letter-spacing: -0.02em; }
[data-testid="stForm"] h3 { font-size:1.1rem !important; font-weight:650; padding-top:.8rem; }
[data-testid="stForm"] { background:#fff; }
[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
.stButton button, .stDownloadButton button, .stFormSubmitButton button {
  font-weight: 600; transition: transform .12s ease, box-shadow .12s ease; }
.stButton button:hover, .stDownloadButton button:hover, .stFormSubmitButton button:hover {
  transform: translateY(-1px); box-shadow: 0 4px 14px rgba(232,78,27,.18); }
[data-testid="stExpander"] details { border-radius: 10px; background: var(--card); }
[data-testid="stVerticalBlockBorderWrapper"] { transition: box-shadow .15s ease; }
@keyframes lensFade { from { opacity:0; transform: translateY(6px);} to { opacity:1; transform:none; } }

.lens-brand { display:flex; align-items:center; gap:.6rem; padding:.2rem 0 .8rem; }
.lens-logo { width:34px; height:34px; border-radius:9px; background:linear-gradient(135deg,#E84E1B,#F59E0B);
  display:grid; place-items:center; color:#fff; font-weight:700; box-shadow:0 4px 12px rgba(232,78,27,.3); }
.lens-brand b { display:block; font-size:1rem; color:var(--ink); }
.lens-brand span { font-size:.78rem; color:var(--muted); }

.lens-hero { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; flex-wrap:wrap;
  margin-bottom:1.4rem; animation: lensFade .35s ease both; }
.lens-eyebrow { font-size:.75rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); }
.lens-hero h1 { margin:.15rem 0 .2rem; padding:0; font-size:2rem; font-weight:700; }
.lens-sub { color:var(--muted); font-size:.95rem; }
.lens-chip { display:inline-flex; align-items:center; gap:.35rem; padding:.28rem .7rem; border-radius:999px;
  background:#fff; border:1px solid var(--line); font-size:.8rem; color:var(--muted); font-weight:500; }
.lens-dot { width:7px; height:7px; border-radius:50%; background:#22C55E; box-shadow:0 0 0 3px rgba(34,197,94,.18); }

.lens-kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-bottom:1.6rem; }
@media (max-width: 900px) { .lens-kpis { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.lens-kpi { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:1.05rem 1.15rem;
  box-shadow:0 1px 2px rgba(22,19,15,.04); animation: lensFade .4s ease both; min-width:0; }
.lens-kpi.hero { background:linear-gradient(135deg,#1C1712 0%,#2B1E15 100%); border-color:#2B1E15; color:#fff; }
.lens-kpi .lbl { font-size:.78rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
.lens-kpi.hero .lbl { color:#D6CFC6; }
.lens-kpi .val { font-size:2rem; font-weight:700; letter-spacing:-.03em; margin:.25rem 0 .1rem; line-height:1.15;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.lens-kpi .val.sm { font-size:1.25rem; padding:.45rem 0 .2rem; }
.lens-kpi .foot { font-size:.82rem; color:var(--muted); }
.lens-kpi.hero .foot { color:#BDB4A9; }
.lens-delta { font-weight:600; padding:.05rem .45rem; border-radius:6px; font-size:.8rem; }
.lens-delta.up { color:#15803D; background:#DCFCE7; } .lens-delta.down { color:#B91C1C; background:#FEE2E2; }
.lens-delta.flat { color:var(--muted); background:#F3F2EF; }
.lens-ring { height:6px; border-radius:99px; background:rgba(255,255,255,.14); margin-top:.6rem; overflow:hidden; }
.lens-ring i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#E84E1B,#F59E0B); }

.lens-section { display:flex; align-items:baseline; justify-content:space-between; margin:1.4rem 0 .6rem; }
[data-testid="stVerticalBlockBorderWrapper"] .lens-section { margin:.1rem 0 .5rem; }
[data-testid="stLogo"] { height:2.2rem; max-width:100%; }
.lens-section h3 { margin:0; padding:0; font-size:1.08rem; font-weight:650; }
.lens-section span { color:var(--muted); font-size:.83rem; }

.lens-bars { display:flex; flex-direction:column; gap:.7rem; }
.lens-bar .row { display:flex; justify-content:space-between; font-size:.88rem; margin-bottom:.28rem; gap:.5rem; }
.lens-bar .row b { font-weight:600; color:var(--ink); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.lens-bar .row span { color:var(--muted); font-variant-numeric:tabular-nums; flex-shrink:0; }
.lens-track { height:8px; border-radius:99px; background:#F0EEEA; overflow:hidden; }
.lens-track i { display:block; height:100%; border-radius:99px; transition:width .6s ease; }

.lens-fix { display:flex; gap:.75rem; padding:.85rem 0; border-bottom:1px solid var(--line); }
.lens-fix:last-child { border-bottom:0; padding-bottom:.2rem; }
.lens-fix .n { flex-shrink:0; width:24px; height:24px; border-radius:7px; background:#FDEDE6; color:var(--accent);
  font-weight:700; font-size:.78rem; display:grid; place-items:center; }
.lens-fix b { font-size:.92rem; display:block; margin-bottom:.15rem; }
.lens-fix p { margin:0; font-size:.84rem; color:var(--muted); line-height:1.45; }

.lens-empty { text-align:center; padding:3.2rem 1.5rem; background:#fff; border:1px dashed #D9D5CE;
  border-radius:16px; animation: lensFade .4s ease both; }
.lens-empty .ic { font-size:2.2rem; } .lens-empty h3 { margin:.5rem 0 .3rem; }
.lens-empty p { color:var(--muted); max-width:520px; margin:0 auto; }
.lens-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:1.6rem; text-align:left; }
@media (max-width: 760px) { .lens-steps { grid-template-columns:1fr; } }
.lens-step { border:1px solid var(--line); border-radius:12px; padding:.9rem 1rem; background:#FAFAF9; }
.lens-step i { font-style:normal; font-size:.72rem; font-weight:700; color:var(--accent); letter-spacing:.06em; }
.lens-step b { display:block; margin:.2rem 0; } .lens-step span { font-size:.84rem; color:var(--muted); }
.lens-pill { display:inline-block; padding:.08rem .5rem; border-radius:6px; font-size:.75rem; font-weight:600; }
.lens-pill.yes { background:#DCFCE7; color:#15803D; } .lens-pill.no { background:#FEE2E2; color:#B91C1C; }
</style>
"""


def inject() -> None:
    st.html(_CSS)


_ASSETS = Path(__file__).parent / "assets"


def brand() -> None:
    st.logo(str(_ASSETS / "logo.svg"), size="large", icon_image=str(_ASSETS / "icon.svg"))


def hero(eyebrow: str, title: str, subtitle: str = "", chip: str | None = None) -> None:
    chip_html = f'<span class="lens-chip"><span class="lens-dot"></span>{escape(chip)}</span>' if chip else ""
    st.html(f'<div class="lens-hero"><div><div class="lens-eyebrow">{escape(eyebrow)}</div>'
            f'<h1>{escape(title)}</h1><div class="lens-sub">{escape(subtitle)}</div></div>{chip_html}</div>')


def section(title: str, note: str = "") -> None:
    st.html(f'<div class="lens-section"><h3>{escape(title)}</h3><span>{escape(note)}</span></div>')


def delta_badge(change: float | None) -> str:
    if change is None:
        return '<span class="lens-delta flat">first month</span>'
    pts = change * 100
    kind = "up" if pts > 0.5 else "down" if pts < -0.5 else "flat"
    arrow = {"up": "▲", "down": "▼", "flat": "•"}[kind]
    return f'<span class="lens-delta {kind}">{arrow} {pts:+.0f} pts</span>'


def kpis(cards: list[dict]) -> None:
    """cards: {label, value, foot (html ok), hero?, small?, progress? (0-1)}"""
    out = []
    for c in cards:
        cls = "lens-kpi hero" if c.get("hero") else "lens-kpi"
        val_cls = "val sm" if c.get("small") else "val"
        bar = ""
        if c.get("progress") is not None:
            bar = f'<div class="lens-ring"><i style="width:{max(0, min(1, c["progress"])) * 100:.0f}%"></i></div>'
        out.append(f'<div class="{cls}"><div class="lbl">{escape(c["label"])}</div>'
                   f'<div class="{val_cls}" title="{escape(str(c["value"]))}">{escape(str(c["value"]))}</div>'
                   f'<div class="foot">{c.get("foot", "")}</div>{bar}</div>')
    st.html(f'<div class="lens-kpis">{"".join(out)}</div>')


def bars(items: list[tuple[str, float | None, str]], color: str = ACCENT, colors: dict | None = None) -> None:
    """items: (label, fraction 0-1, right-hand text)."""
    if not items:
        st.caption("No data yet.")
        return
    rows = []
    for label, frac, right in items:
        fill = (colors or {}).get(label, color)
        width = 0 if frac is None else max(0, min(1, frac)) * 100
        rows.append(f'<div class="lens-bar"><div class="row"><b title="{escape(label)}">{escape(label)}</b>'
                    f'<span>{escape(right)}</span></div><div class="lens-track">'
                    f'<i style="width:{width:.1f}%;background:{fill}"></i></div></div>')
    st.html(f'<div class="lens-bars">{"".join(rows)}</div>')


def fixes(items: list[tuple[str, str]]) -> None:
    st.html("".join(f'<div class="lens-fix"><div class="n">{i}</div><div><b>{escape(t)}</b>'
                    f'<p>{escape(d)}</p></div></div>' for i, (t, d) in enumerate(items, 1)))


def empty_state(icon: str, title: str, body: str, steps: list[tuple[str, str]] | None = None) -> None:
    steps_html = ""
    if steps:
        steps_html = '<div class="lens-steps">' + "".join(
            f'<div class="lens-step"><i>STEP {i}</i><b>{escape(t)}</b><span>{escape(d)}</span></div>'
            for i, (t, d) in enumerate(steps, 1)) + "</div>"
    st.html(f'<div class="lens-empty"><div class="ic">{icon}</div><h3>{escape(title)}</h3>'
            f'<p>{escape(body)}</p>{steps_html}</div>')
