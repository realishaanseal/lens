"""The simple monthly PDF a client reads: one page, no jargon."""

from __future__ import annotations

from fpdf import FPDF

from .config import Client
from .metrics import Summary, trend
from .store import Store
from .suggest import Suggestion

INK = (17, 17, 17)
MUTED = (110, 110, 110)
ACCENT = (232, 78, 27)
CARD = (243, 243, 243)


def _latin(text: str) -> str:
    """Core PDF fonts are Latin-1 only; swap common typography and drop the rest."""
    for a, b in {"—": "-", "–": "-", "…": "...", "’": "'", "‘": "'", "“": '"', "”": '"', "→": "->", "·": "-"}.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.0%}"


class _Report(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=7)
        self.set_text_color(*MUTED)
        self.cell(0, 5, "VARAXIS LENS  -  Know if AI recommends you.", align="L")
        self.cell(0, 5, f"{self.page_no()}", align="R")


def build_report(client: Client, summary: Summary, suggestions: list[Suggestion], store: Store) -> bytes:
    pdf = _Report(format="A4")
    pdf.set_auto_page_break(True, margin=16)
    pdf.add_page()
    pdf.set_margins(16, 16, 16)
    width = pdf.w - 32

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 5, _latin(f"AI VISIBILITY REPORT  -  {summary.period}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*INK)
    pdf.cell(0, 10, _latin(client.name), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, _latin(f"Does AI name you when people in {client.city} ask?"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # KPI tiles
    change = summary.change
    tiles = [
        (_pct(summary.mention_rate), "MENTION RATE",
         "" if change is None else f"{change * 100:+.0f} pts vs last month"),
        (str(summary.prompts_tested), "QUESTIONS TESTED", f"{summary.answers} AI answers"),
        (summary.top_competitor or "-", "TOP COMPETITOR",
         f"in {summary.top_competitors[0][2]:.0%} of answers" if summary.top_competitors else ""),
        ("-" if summary.ai_visits is None else f"{summary.ai_visits:.0f}", "AI VISITS", "GA4 AI Assistant users"),
    ]
    gap, top = 4, pdf.get_y()
    tile_w = (width - gap * 3) / 4
    for i, (value, label, note) in enumerate(tiles):
        x = pdf.l_margin + i * (tile_w + gap)
        dark = i == 0
        pdf.set_fill_color(*(INK if dark else CARD))
        pdf.rect(x, top, tile_w, 26, style="F")
        pdf.set_xy(x + 3, top + 3)
        pdf.set_text_color(*((255, 255, 255) if dark else INK))
        size = 14
        pdf.set_font("Helvetica", "B", size)
        while size > 7 and pdf.get_string_width(_latin(value)) > tile_w - 6:
            size -= 0.5
            pdf.set_font("Helvetica", "B", size)
        pdf.cell(tile_w - 6, 8, _latin(value))
        pdf.set_xy(x + 3, top + 12)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*(ACCENT if dark else MUTED))
        pdf.cell(tile_w - 6, 4, label)
        pdf.set_xy(x + 3, top + 17)
        pdf.set_font("Helvetica", size=7)
        pdf.set_text_color(*((210, 210, 210) if dark else MUTED))
        pdf.cell(tile_w - 6, 4, _latin(note))
    pdf.set_y(top + 32)

    # Trend chart
    rows = [r for r in trend(store, client.id) if r["period"] <= summary.period][-6:]
    _section(pdf, "MENTIONS IN AI ANSWERS BY MONTH")
    chart_top, chart_h = pdf.get_y() + 2, 38
    bar_gap = 6
    bar_w = (width - bar_gap * (max(len(rows), 1) - 1)) / max(len(rows), 1)
    bar_w = min(bar_w, 22)
    scale = max([r["overall"] or 0 for r in rows] + [0.01])
    for i, row in enumerate(rows):
        value = row["overall"] or 0
        h = max(value / scale * (chart_h - 6), 0.5)
        x = pdf.l_margin + i * (bar_w + bar_gap)
        pdf.set_fill_color(*(ACCENT if row["period"] == summary.period else INK))
        pdf.rect(x, chart_top + chart_h - h, bar_w, h, style="F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*INK)
        pdf.set_xy(x, chart_top + chart_h - h - 5)
        pdf.cell(bar_w, 4, _pct(value), align="C")
        pdf.set_font("Helvetica", size=7)
        pdf.set_text_color(*MUTED)
        pdf.set_xy(x, chart_top + chart_h + 1)
        pdf.cell(bar_w, 4, row["period"], align="C")
    pdf.set_y(chart_top + chart_h + 9)

    # By AI tool + competitors, side by side
    col_w = (width - 8) / 2
    top = pdf.get_y()
    _section(pdf, "BY AI TOOL", w=col_w)
    names = {"openai": "ChatGPT", "gemini": "Gemini", "perplexity": "Perplexity"}
    for provider, value in summary.by_provider.items():
        _row(pdf, names.get(provider, provider), _pct(value), col_w)
    left_end = pdf.get_y()

    pdf.set_xy(pdf.l_margin + col_w + 8, top)
    _section(pdf, "WHO AI RECOMMENDS INSTEAD", w=col_w, x=pdf.l_margin + col_w + 8)
    for name, n, share in summary.top_competitors[:5]:
        pdf.set_x(pdf.l_margin + col_w + 8)
        _row(pdf, name, f"{share:.0%} of answers", col_w)
    pdf.set_y(max(left_end, pdf.get_y()) + 4)

    _section(pdf, "WHAT TO FIX NEXT")
    if not suggestions:
        pdf.set_font("Helvetica", size=9)
        pdf.cell(0, 6, "Nothing urgent this month.", new_x="LMARGIN", new_y="NEXT")
    for i, s in enumerate(suggestions[:6], 1):
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*INK)
        pdf.cell(0, 5.5, _latin(f"{i}. {s.title}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=8.5)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 4.2, _latin(s.detail), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 3.6, _latin(
        f"Mention rate = AI answers that name {client.name} / AI answers checked, for "
        f"{summary.prompts_tested} customer-style questions in English, Bengali and Banglish. "
        "AI answers change over time; these are dated snapshots."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def _section(pdf: FPDF, title: str, w: float = 0, x: float | None = None):
    if x is not None:
        pdf.set_x(x)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*ACCENT)
    pdf.cell(w, 6, title, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x if x is not None else pdf.l_margin)


def _row(pdf: FPDF, label: str, value: str, w: float):
    x = pdf.get_x()
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(*INK)
    pdf.cell(w * 0.62, 5.5, _latin(label)[:42])
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w * 0.38, 5.5, _latin(value), align="R", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x)
