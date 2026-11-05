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
.block-container { padding-top:4.75rem; padding-bottom:6rem; max-width:1180px; }
[data-testid="stHeader"] { background:rgba(255,255,255,.82); backdrop-filter:saturate(180%) blur(12px);
  -webkit-backdrop-filter:saturate(180%) blur(12px); border-bottom:1px solid rgba(228,228,231,.7); }
[data-testid="stSidebarHeader"] { padding-top:1.25rem; }
[data-testid="stMainBlockContainer"] .stButton button, [data-testid="stMainBlockContainer"] .stDownloadButton button {
  border-radius:8px; font-weight:500; min-height:38px; padding:0 14px; }
[data-testid="stDialog"] [role="dialog"] { border-radius:12px; }
[data-testid="stDataFrame"] { border:1px solid #E4E4E7; border-radius:8px; }
input, textarea, [data-baseweb="select"] > div { background:#FFFFFF !important; }
h1, h2, h3, h4 { letter-spacing:-0.015em; font-weight:600 !important; }
[data-testid="stSidebar"] { border-right:1px solid #E4E4E7; }
[data-testid="stSidebar"] label p { font-size:12px; color:#52525B; font-weight:500; }
[data-testid="stForm"] { border:0; padding:0; }
[data-testid="stForm"] h3 { font-size:15px !important; padding:1rem 0 0; }
[data-testid="stExpander"] details { border-color:#E4E4E7; }
[data-testid="stExpander"] summary p { font-size:13.5px; }
.tnum { font-variant-numeric:tabular-nums; }

.lx-head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; }
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
.lx-hr { border:0; border-top:1px solid #E4E4E7; margin:22px 0 30px; }
.lx-id { display:flex; align-items:center; gap:14px; min-width:0; }
.lx-av { flex-shrink:0; width:46px; height:46px; border-radius:11px; background:#18181B; color:#FAFAFA;
  display:grid; place-items:center; font-weight:600; font-size:15px; letter-spacing:.02em; }
.lx-av.sm { width:34px; height:34px; border-radius:8px; font-size:12px; background:#F4F4F5; color:#3F3F46;
  border:1px solid #E4E4E7; }
.lx-id h1 { font-size:22px; margin:0; padding:0; line-height:1.25; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.lx-meta { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
.lx-pill { font-size:12px; color:#52525B; background:#F4F4F5; border-radius:999px; padding:2px 9px; white-space:nowrap; }
.lx-sec h4 { font-size:14px; margin:0 0 4px; padding:0; }
.lx-sec p { font-size:13px; color:#71717A; line-height:1.55; margin:0; }
.lx-crow { display:flex; align-items:center; gap:12px; min-width:0; }
.lx-crow b { font-size:14px; font-weight:500; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.lx-crow span { font-size:12.5px; color:#71717A; }
.lx-cta { border:1px solid #E4E4E7; border-radius:10px; padding:28px 28px 8px; }
.lx-cta h3 { font-size:16px; margin:0 0 6px; padding:0; }
.lx-cta p { color:#71717A; font-size:13.5px; margin:0; max-width:620px; line-height:1.55; }
/* Loading: thin progress line while the app works, shown only if work takes over 250ms */
.stApp[data-test-script-state="running"]::before { content:""; position:fixed; top:0; left:0; height:2px;
  width:32%; background:#18181B; z-index:1000020; opacity:0;
  animation: lxSlide 1.1s cubic-bezier(.45,0,.25,1) .25s infinite, lxIn .2s ease .25s forwards; }
@keyframes lxSlide { 0% { transform:translateX(-100%); } 100% { transform:translateX(320%); } }
@keyframes lxIn { to { opacity:1; } }

/* ---- Motion system: expo-out easing, staggered reveals, blur-to-sharp "focus pulls" ---- */
:root { --e-out:cubic-bezier(.16,1,.3,1); --e-io:cubic-bezier(.65,0,.35,1); }
@keyframes lxRise { from { opacity:0; transform:translateY(10px); filter:blur(6px); } to { opacity:1; transform:none; filter:none; } }
@keyframes lxFocusIn { from { opacity:0; filter:blur(12px); transform:translateY(4px) scale(.98); } to { opacity:1; filter:none; transform:none; } }
@keyframes lxGrow { from { transform:scaleX(0); } to { transform:scaleX(1); } }
@keyframes lxPop { 0% { opacity:0; transform:scale(.6) rotate(-8deg); filter:blur(8px); }
  60% { opacity:1; filter:none; } 100% { opacity:1; transform:none; } }
@keyframes lxSpin { to { transform:rotate(360deg); } }
@keyframes lxIris { 0%, 100% { transform:scale(1); filter:none; } 45% { transform:scale(.78); filter:blur(1px); } }
@keyframes lxTrack { 0% { transform:translateX(-100%) scaleX(.4); } 50% { transform:translateX(60%) scaleX(.9); }
  100% { transform:translateX(260%) scaleX(.4); } }

.lx-id { animation: lxFocusIn .9s var(--e-out) both; }
.lx-stat { animation: lxRise .8s var(--e-out) both; }
.lx-stat:nth-child(2) { animation-delay:.07s; } .lx-stat:nth-child(3) { animation-delay:.14s; }
.lx-stat:nth-child(4) { animation-delay:.21s; }
.lx-h, .lx-cta, .lx-empty { animation: lxRise .8s var(--e-out) .1s both; }
.lx-row, .lx-fix, .lx-crow { animation: lxRise .7s var(--e-out) both; }
.lx-row:nth-child(2), .lx-fix:nth-child(2) { animation-delay:.06s; } .lx-row:nth-child(3), .lx-fix:nth-child(3) { animation-delay:.12s; }
.lx-row:nth-child(4), .lx-fix:nth-child(4) { animation-delay:.18s; } .lx-row:nth-child(5), .lx-fix:nth-child(5) { animation-delay:.24s; }
.lx-row .t i { transform-origin:left center; animation: lxGrow 1.3s var(--e-out) .25s both; }
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] { animation: lxRise 1s var(--e-out) .15s both; }
.stButton button:active, .stDownloadButton button:active, .stFormSubmitButton button:active { transform:scale(.98); }
.stButton button, .stDownloadButton button, .stFormSubmitButton button {
  transition: background-color .2s var(--e-out), border-color .2s var(--e-out), transform .15s var(--e-out), box-shadow .2s; }
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primaryFormSubmit"]:hover {
  box-shadow:0 6px 20px -8px rgba(24,24,27,.55); }

/* Numbers count up */
@property --n { syntax:"\\3c integer\\3e "; inherits:false; initial-value:0; }
@keyframes lxCount { from { --n:0; } to { --n:var(--to); } }
.lx-count { --n:var(--to); counter-reset:n var(--n); animation: lxCount 1.4s var(--e-out) .15s both; }
.lx-count::before { content:counter(n); }

/* Loading screen */
.lx-boot { position:fixed; inset:0; z-index:1000010; background:#FFFFFF; display:grid; place-items:center;
  pointer-events:none; animation: lxBootOut .9s var(--e-out) forwards; }
.stApp[data-test-script-state="running"] .lx-boot { animation:none; opacity:1; visibility:visible; }
[data-stale="true"] .lx-boot { display:none !important; }
@keyframes lxBootOut { 0%, 25% { opacity:1; visibility:visible; transform:none; filter:none; }
  100% { opacity:0; visibility:hidden; transform:scale(1.04); filter:blur(10px); } }
.lx-boot-inner { display:flex; flex-direction:column; align-items:center; }
.lx-lens { position:relative; width:84px; height:84px; animation: lxPop 1s var(--e-out) both; }
.lx-ring { position:absolute; inset:0; border-radius:50%; border:1.5px solid #EDEDEF; }
.lx-ring.spin { border-color:transparent; border-top-color:#18181B; animation: lxSpin 1.4s var(--e-io) infinite; }
.lx-ring.spin.two { inset:7px; border-top-color:#A1A1AA; animation-duration:2.1s; animation-direction:reverse; }
.lx-mark { position:absolute; inset:22px; border-radius:11px; background:#18181B; display:grid; place-items:center;
  box-shadow:0 10px 30px -12px rgba(24,24,27,.6); }
.lx-glass { position:relative; width:17px; height:17px; margin:-3px 0 0 -3px; border:3px solid #FFFFFF;
  border-radius:50%; animation: lxIris 2.2s var(--e-io) .6s infinite; }
.lx-glass::after { content:""; position:absolute; width:7px; height:3px; background:#FFFFFF; border-radius:2px;
  right:-7px; bottom:-4px; transform:rotate(45deg); }
.lx-word { margin-top:26px; font-size:17px; font-weight:600; letter-spacing:-.02em; color:#18181B; white-space:pre; }
.lx-word span { display:inline-block; animation: lxFocusIn .9s var(--e-out) both;
  animation-delay:calc(.35s + var(--i) * .035s); }
.lx-bar { position:relative; width:148px; height:2px; margin-top:20px; border-radius:2px; background:#F4F4F5;
  overflow:hidden; animation: lxRise .8s var(--e-out) .6s both; }
.lx-bar i { position:absolute; inset:0; width:40%; border-radius:2px; background:#18181B;
  animation: lxTrack 1.5s var(--e-io) infinite; }
.lx-steps { position:relative; height:18px; width:260px; margin-top:16px; text-align:center; font-size:13px; color:#71717A; }
.lx-steps span { position:absolute; inset:0; opacity:0; animation: lxStep 3.6s var(--e-io) .8s infinite; }
.lx-steps span:nth-child(2) { animation-delay:2s; } .lx-steps span:nth-child(3) { animation-delay:3.2s; }
@keyframes lxStep { 0% { opacity:0; transform:translateY(6px); filter:blur(4px); } 10%, 28% { opacity:1; transform:none; filter:none; }
  36%, 100% { opacity:0; transform:translateY(-6px); filter:blur(4px); } }


/* ---- Surfaces: tokens, cards, fields, chips (refinement layer) ---- */
:root { --line:#ECECEE; --line-2:#E2E2E5; --r-sm:8px; --r:12px; --r-lg:14px;
  --sh-xs:0 1px 2px rgba(16,16,20,.04);
  --sh-sm:0 1px 2px rgba(16,16,20,.04), 0 2px 10px -4px rgba(16,16,20,.06);
  --sh-md:0 1px 2px rgba(16,16,20,.05), 0 14px 34px -14px rgba(16,16,20,.18);
  --ring:0 0 0 3.5px rgba(24,24,27,.07); }

/* Cards: headline numbers, notices, bordered containers, expanders, tables */
.lx-stats { border:1px solid var(--line); border-radius:var(--r-lg); background:#FFFFFF; box-shadow:var(--sh-sm);
  overflow:hidden; }
.lx-stat { position:relative; transition:background-color .25s var(--e-out); }
.lx-stat + .lx-stat { border-left:1px solid var(--line); }
.lx-stat:hover { background:#FCFCFC; }
.lx-stat .k { display:flex; align-items:center; gap:7px; }
.lx-stat .k::before { content:""; width:6px; height:6px; border-radius:2px; background:#D4D4D8; }
.lx-stat:first-child .k::before { background:#18181B; }
.lx-cta, .lx-empty { border:1px solid var(--line); border-radius:var(--r-lg); background:#FFFFFF; box-shadow:var(--sh-sm); }
[data-testid="stVerticalBlock"][data-test-scroll-behavior] { border-color:var(--line) !important;
  border-radius:var(--r-lg) !important; background:#FFFFFF; box-shadow:var(--sh-sm);
  transition:box-shadow .3s var(--e-out), border-color .3s var(--e-out); }
[data-testid="stVerticalBlock"][data-test-scroll-behavior]:hover { box-shadow:var(--sh-md); border-color:var(--line-2) !important; }
[data-testid="stExpander"] details { border:1px solid var(--line) !important; border-radius:var(--r) !important;
  background:#FFFFFF; box-shadow:var(--sh-xs); overflow:hidden; }
[data-testid="stExpander"] summary { transition:background-color .2s var(--e-out); border-radius:0; }
[data-testid="stExpander"] summary:hover { background:#FAFAFA; }
[data-testid="stExpander"] details[open] summary { border-bottom:1px solid var(--line); }
[data-testid="stDataFrame"] { border:1px solid var(--line) !important; border-radius:var(--r) !important;
  overflow:hidden; box-shadow:var(--sh-xs); }
[data-testid="stCode"] pre, .stCode pre { border-radius:var(--r-sm) !important; border:1px solid var(--line); background:#FAFAFA !important; }

/* Fields */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  border-radius:10px !important; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  border-color:var(--line-2) !important; box-shadow:var(--sh-xs);
  transition:border-color .2s var(--e-out), box-shadow .2s var(--e-out) !important; }
[data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover, [data-baseweb="select"] > div:hover { border-color:#D4D4D8 !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {
  border-color:#18181B !important; box-shadow:var(--ring) !important; }
[data-testid="stNumberInputContainer"] { border-radius:10px !important; }
[data-testid="stNumberInputContainer"] button { border-radius:0 !important; }
[data-baseweb="tag"] { border-radius:999px !important; padding-left:10px !important; }
[data-baseweb="popover"] > div, [data-baseweb="menu"] { border-radius:var(--r) !important; box-shadow:var(--sh-md) !important;
  border:1px solid var(--line) !important; overflow:hidden; }
[data-baseweb="menu"] li { border-radius:8px; margin:2px 4px; transition:background-color .15s; }

/* Buttons */
[data-testid="stMainBlockContainer"] .stButton button, [data-testid="stMainBlockContainer"] .stDownloadButton button,
.stFormSubmitButton button, [data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] .stDownloadButton button {
  border-radius:10px !important; }
button[kind="secondary"], button[kind="secondaryFormSubmit"] { background:#FFFFFF !important; border-color:var(--line-2) !important;
  box-shadow:var(--sh-xs); }
button[kind="secondary"]:hover, button[kind="secondaryFormSubmit"]:hover { background:#FAFAFA !important; border-color:#D4D4D8 !important;
  color:#18181B !important; }
button[kind="primary"], button[kind="primaryFormSubmit"] {
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12), 0 1px 2px rgba(16,16,20,.2), 0 4px 12px -6px rgba(16,16,20,.5); }
button:focus-visible { outline:none !important; box-shadow:var(--ring) !important; }

/* Chips: segmented controls and pills in a soft track */
[data-testid="stButtonGroup"] > div { background:#F4F4F5; padding:3px; border-radius:11px; gap:2px !important;
  display:inline-flex !important; width:auto !important; }
[data-testid="stButtonGroup"] button { border:0 !important; background:transparent !important; border-radius:8px !important;
  color:#52525B !important; box-shadow:none !important; min-height:30px; padding:0 12px !important;
  transition:background-color .25s var(--e-out), color .25s var(--e-out), box-shadow .25s var(--e-out) !important; }
[data-testid="stButtonGroup"] button:hover { color:#18181B !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[data-selected="true"] {
  background:#FFFFFF !important; color:#18181B !important;
  box-shadow:0 1px 2px rgba(16,16,20,.08), 0 1px 1px rgba(16,16,20,.04) !important; }
[data-testid="stButtonGroup"] button[data-variant="pills"] { gap:7px; }
[data-testid="stButtonGroup"] button[data-variant="pills"]::before { content:""; width:7px; height:7px; border-radius:50%;
  border:1.5px solid #A1A1AA; transition:background-color .25s var(--e-out), border-color .25s var(--e-out); }
[data-testid="stButtonGroup"] button[data-variant="pills"][data-selected="true"]::before { background:#18181B; border-color:#18181B; }
[data-testid="InputInstructions"] { display:none !important; }
[data-testid="stNumberInputContainer"] button { background:#FFFFFF !important; border-left:1px solid var(--line) !important;
  color:#52525B !important; transition:background-color .15s; }
[data-testid="stNumberInputContainer"] button:hover { background:#FAFAFA !important; color:#18181B !important; }
[data-baseweb="input"] > div, [data-baseweb="input"] button { background:#FFFFFF !important; }
[data-testid="stDialog"] [role="dialog"] h2 { font-size:19px !important; font-weight:600 !important; letter-spacing:-.015em; }

/* Tags, pills, avatars */
.lx-pill { background:#FFFFFF; border:1px solid var(--line); box-shadow:var(--sh-xs); color:#3F3F46; font-weight:500;
  padding:3px 10px; display:inline-flex; align-items:center; gap:6px; }
.lx-pill:first-child::before { content:""; width:6px; height:6px; border-radius:50%; background:#18181B; }
.lx-tag { display:inline-flex; align-items:center; gap:5px; border-radius:999px; padding:1px 8px 1px 7px; font-weight:500;
  background:#FAFAFA; border-color:var(--line); }
.lx-tag::before { content:""; width:5px; height:5px; border-radius:50%; background:currentColor; opacity:.8; }
.lx-tag.hi { background:#FEF2F2; border-color:#FEE2E2; color:#B91C1C; }
.lx-av { border-radius:12px; box-shadow:inset 0 1px 0 rgba(255,255,255,.14), 0 8px 20px -10px rgba(16,16,20,.6); }
.lx-av.sm { border-radius:9px; background:#FAFAFA; border-color:var(--line); box-shadow:var(--sh-xs); }

/* Lists */
.lx-row { border-bottom-color:#F4F4F5; transition:background-color .2s var(--e-out); border-radius:6px; }
.lx-row .t { height:5px; border-radius:99px; }
.lx-row .t i { border-radius:99px; }
.lx-fix { border-bottom-color:#F4F4F5; }

/* Dialog and sidebar */
[data-testid="stDialog"] [role="dialog"] { border-radius:18px !important; border:1px solid var(--line);
  box-shadow:0 24px 64px -16px rgba(16,16,20,.28), 0 2px 6px rgba(16,16,20,.06) !important; }
[data-testid="stSidebarNavLink"] { border-radius:8px; transition:background-color .2s var(--e-out); }
[data-testid="stSidebarNavLink"][aria-current="page"] { background:#FFFFFF !important; box-shadow:var(--sh-xs);
  border:1px solid var(--line); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.001s !important; animation-iteration-count:1 !important;
    animation-delay:0s !important; transition-duration:.001s !important; }
  .lx-steps span:first-child { opacity:1; }
}
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
    """cards: {label, value, foot (trusted html), text? (smaller value for names)}.

    Whole-number values such as "46%" or "19" count up from zero when they appear.
    """
    def value_html(value) -> str:
        text = str(value)
        digits = text.rstrip("%")
        if digits.isdigit() and int(digits) < 100000:
            return f'<span class="lx-count" style="--to:{int(digits)}" aria-hidden="true"></span>{text[len(digits):]}'
        return escape(text)

    cells = "".join(
        f'<div class="lx-stat"><div class="k">{escape(c["label"])}</div>'
        f'<div class="v{" text" if c.get("text") else ""}" title="{escape(str(c["value"]))}" '
        f'aria-label="{escape(str(c["value"]))}">{value_html(c["value"])}</div>'
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


def initials(name: str) -> str:
    words = [w for w in name.replace("&", " ").split() if w[:1].isalnum()]
    return "".join(w[0] for w in words[:2]).upper() or "?"


def identity(name: str, pills: list[str]) -> None:
    """Page title with an initials mark and small metadata pills."""
    pills_html = "".join(f'<span class="lx-pill">{escape(p)}</span>' for p in pills if p)
    st.html(f'<div class="lx-id"><div class="lx-av">{escape(initials(name))}</div><div style="min-width:0">'
            f'<h1 title="{escape(name)}">{escape(name)}</h1><div class="lx-meta">{pills_html}</div></div></div>')


def client_row(name: str, detail: str) -> None:
    st.html(f'<div class="lx-crow"><div class="lx-av sm">{escape(initials(name))}</div>'
            f'<div style="min-width:0"><b>{escape(name)}</b><span>{escape(detail)}</span></div></div>')


def rule() -> None:
    st.html('<hr class="lx-hr">')


def section(title: str, description: str, first: bool = False):
    """Settings-style section: description on the left, returns the right-hand column for fields."""
    if not first:
        rule()
    left, right = st.columns([1, 2.1], gap="large")
    left.html(f'<div class="lx-sec"><h4>{escape(title)}</h4><p>{escape(description)}</p></div>')
    return right


def cta(title: str, body: str) -> None:
    st.html(f'<div class="lx-cta"><h3>{escape(title)}</h3><p>{escape(body)}</p></div>')


_LOADER = """
<div class="lx-boot" role="status" aria-live="polite" aria-label="Loading"><div class="lx-boot-inner">
  <div class="lx-lens"><div class="lx-ring"></div><div class="lx-ring spin"></div><div class="lx-ring spin two"></div>
    <div class="lx-mark"><div class="lx-glass"></div></div></div>
  <div class="lx-word" aria-hidden="true"><span style="--i:0">V</span><span style="--i:1">a</span><span style="--i:2">r</span><span style="--i:3">a</span><span style="--i:4">x</span><span style="--i:5">i</span><span style="--i:6">s</span><span style="--i:7"> </span><span style="--i:8">L</span><span style="--i:9">e</span><span style="--i:10">n</span><span style="--i:11">s</span></div>
  <div class="lx-bar"><i></i></div>
  <div class="lx-steps"><span>Loading your clients</span><span>Reading the latest answers</span><span>Preparing your dashboard</span></div>
</div></div>
"""


def loading_screen() -> None:
    """Full-screen loader, shown while the current run builds the page, then faded out."""
    st.html(_LOADER)
