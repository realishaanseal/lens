"""Visual layer: global CSS and small HTML components shared by the pages."""

from __future__ import annotations

import calendar
from html import escape
from pathlib import Path

import streamlit as st

INK = "#18181B"
MUTED = "#71717A"
LINE = "#E4E4E7"
ACCENT = "#2563EB"
GOOD = "#16A34A"
BAD = "#DC2626"
SERIES = {"All tools": INK, "ChatGPT": INK, "Gemini": ACCENT, "Perplexity": "#A1A1AA"}

_ASSETS = Path(__file__).parent / "assets"

_CSS = """
<style>
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none !important; }
.block-container { padding-top:2.5rem; padding-bottom:5rem; max-width:1200px; }
h1, h2, h3, h4 { letter-spacing:-0.015em; font-weight:600 !important; }
[data-testid="stSidebar"] { border-right:1px solid #E4E4E7; }
[data-testid="stSidebar"] label p { font-size:12px; color:#52525B; font-weight:500; }
[data-testid="stForm"] { border-color:#E4E4E7; padding:1.5rem; }
[data-testid="stForm"] h3 { font-size:15px !important; padding:1rem 0 0; }
[data-testid="stExpander"] details { border-color:#E4E4E7; }
[data-testid="stExpander"] summary p { font-size:13.5px; }
.tnum { font-variant-numeric:tabular-nums; }

.lx-head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap;
  padding-bottom:20px; margin-bottom:28px; border-bottom:1px solid #E4E4E7; }
.lx-head h1 { font-size:24px; margin:0; padding:0; line-height:1.25; }
.lx-head .sub { color:#71717A; font-size:13.5px; margin-top:4px; }
.lx-head .meta { color:#71717A; font-size:13px; font-variant-numeric:tabular-nums; }

.lx-stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); border:1px solid #E4E4E7;
  border-radius:8px; margin-bottom:36px; }
.lx-stat { padding:18px 20px; min-width:0; }
.lx-stat + .lx-stat { border-left:1px solid #E4E4E7; }
@media (max-width: 860px) { .lx-stats { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .lx-stat:nth-child(3) { border-left:0; } .lx-stat:nth-child(n+3) { border-top:1px solid #E4E4E7; } }
.lx-stat .k { font-size:12.5px; color:#71717A; font-weight:500; }
.lx-stat .v { font-size:26px; font-weight:600; letter-spacing:-0.02em; margin:6px 0 4px; line-height:1.2;
  font-variant-numeric:tabular-nums; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.lx-stat .v.text { font-size:17px; margin:10px 0 7px; }
.lx-stat .f { font-size:12.5px; color:#71717A; font-variant-numeric:tabular-nums; }
.lx-up { color:#16A34A; font-weight:500; } .lx-down { color:#DC2626; font-weight:500; }

.lx-h { display:flex; justify-content:space-between; align-items:baseline; margin:0 0 14px; }
.lx-h h3 { font-size:14px; margin:0; padding:0; }
.lx-h span { font-size:12.5px; color:#71717A; }

.lx-rows { display:flex; flex-direction:column; }
.lx-row { display:grid; grid-template-columns:minmax(0,1fr) 88px 44px; align-items:center; gap:12px;
  padding:9px 0; border-bottom:1px solid #F4F4F5; font-size:13.5px; }
.lx-row:last-child { border-bottom:0; }
.lx-row .n { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.lx-row .t { height:4px; background:#F4F4F5; border-radius:2px; overflow:hidden; }
.lx-row .t i { display:block; height:100%; background:#18181B; }
.lx-row .p { text-align:right; color:#52525B; font-variant-numeric:tabular-nums; }

.lx-fix { padding:12px 0; border-bottom:1px solid #F4F4F5; }
.lx-fix:first-child { padding-top:2px; } .lx-fix:last-child { border-bottom:0; }
.lx-fix .t { font-size:13.5px; font-weight:500; display:flex; gap:8px; align-items:center; }
.lx-fix .d { font-size:13px; color:#71717A; line-height:1.5; margin-top:3px; }
.lx-tag { font-size:11px; font-weight:500; padding:1px 6px; border-radius:4px; border:1px solid #E4E4E7; color:#52525B; }
.lx-tag.hi { border-color:#FECACA; color:#B91C1C; background:#FEF2F2; }

.lx-empty { border:1px solid #E4E4E7; border-radius:8px; padding:28px; }
.lx-empty h3 { font-size:15px; margin:0 0 6px; padding:0; }
.lx-empty p { color:#71717A; font-size:13.5px; margin:0; max-width:560px; }
.lx-empty ol { margin:18px 0 0; padding-left:18px; color:#3F3F46; font-size:13.5px; line-height:1.9; }
.lx-gap { height:36px; }
</style>
"""


def inject() -> None:
    st.html(_CSS)


def brand() -> None:
    st.logo(str(_ASSETS / "logo.svg"), size="large", icon_image=str(_ASSETS / "icon.svg"))


def month_label(period: str | None) -> str:
    """'2026-11' -> 'November 2026'."""
    try:
        year, month = period.split("-")
        return f"{calendar.month_name[int(month)]} {year}"
    except (AttributeError, ValueError, IndexError):
        return period or ""


def header(title: str, subtitle: str = "", meta: str = "") -> None:
    st.html(f'<div class="lx-head"><div><h1>{escape(title)}</h1><div class="sub">{escape(subtitle)}</div></div>'
            f'<div class="meta">{escape(meta)}</div></div>')


def heading(title: str, note: str = "") -> None:
    st.html(f'<div class="lx-h"><h3>{escape(title)}</h3><span>{escape(note)}</span></div>')


def gap() -> None:
    st.html('<div class="lx-gap"></div>')


def change_text(change: float | None, previous: str = "last month") -> str:
    if change is None:
        return "No earlier month to compare"
    pts = round(change * 100)
    if pts == 0:
        return f"No change from {previous}"
    cls = "lx-up" if pts > 0 else "lx-down"
    return f'<span class="{cls}">{pts:+d} pts</span> from {escape(previous)}'


def stats(cards: list[dict]) -> None:
    """cards: {label, value, foot (trusted html), text? (smaller value for names)}."""
    cells = "".join(
        f'<div class="lx-stat"><div class="k">{escape(c["label"])}</div>'
        f'<div class="v{" text" if c.get("text") else ""}" title="{escape(str(c["value"]))}">{escape(str(c["value"]))}</div>'
        f'<div class="f">{c.get("foot", "")}</div></div>' for c in cards)
    st.html(f'<div class="lx-stats">{cells}</div>')


def rows(items: list[tuple[str, float | None, str]]) -> None:
    """Ranked list with a thin bar: (label, fraction 0-1, value text)."""
    if not items:
        st.caption("No data for this month.")
        return
    out = "".join(
        f'<div class="lx-row"><div class="n" title="{escape(label)}">{escape(label)}</div>'
        f'<div class="t"><i style="width:{0 if frac is None else max(0.0, min(1.0, frac)) * 100:.1f}%"></i></div>'
        f'<div class="p">{escape(value)}</div></div>' for label, frac, value in items)
    st.html(f'<div class="lx-rows">{out}</div>')


HIGH = '<span class="lx-tag hi">High</span>'


def fixes(items: list[tuple[str, str, int]]) -> None:
    """(title, detail, priority) with priority 1 = do first."""
    out = "".join(
        f'<div class="lx-fix"><div class="t">{escape(t)}'
        f'{HIGH if p == 1 else ""}</div><div class="d">{escape(d)}</div></div>'
        for t, d, p in items)
    st.html(out)


def empty(title: str, body: str, steps: list[str] | None = None) -> None:
    steps_html = "<ol>" + "".join(f"<li>{escape(s)}</li>" for s in steps) + "</ol>" if steps else ""
    st.html(f'<div class="lx-empty"><h3>{escape(title)}</h3><p>{escape(body)}</p>{steps_html}</div>')
