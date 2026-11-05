# Lens brand masters

The official vector masters for **Lens by Varaxis**. Lens sits beside Scholar and ClinicOS, and is built on the same system as the Varaxis brand masters (`brand/` in the `varaxis` repo): the same ink and grounds, the same wordmark type and endorsement line, the same lockup proportions, and the same rule that a product colours exactly **one** piece.

Never trace, redraw or "fix" a mark by hand: change `tools/lens_geometry.py` and regenerate.

## Files (`masters/`)

| Pattern | What it is |
|---|---|
| `lens-mark.svg` | the symbol alone |
| `lens-stacked.svg` | the symbol above the wordmark, with the "BY VARAXIS" endorsement line |
| `lens-horizontal.svg` | the symbol beside the wordmark, with a vertical rule and the endorsement line |
| `lens-horizontal-compact.svg` | the symbol beside the wordmark, no endorsement, for small sizes (the app sidebar) |
| `lens-wordmark.svg` | the wordmark alone |
| `lens-wordmark-endorsed.svg` | the wordmark over the endorsement line, no symbol (the app's loading screen) |
| `lens-mark-mono*.svg` | one-colour symbol, for cases where colour is not available |
| `*-reverse.svg` | the same artwork for dark grounds |
| `png/` | PNG exports of the main files, for documents and the PDF report |

All text is outlined, so no font is needed to display these files.

## Colour

| Token | Light grounds | Dark grounds |
|---|---|---|
| Ink (mark and wordmark) | `#0B1118` | `#E7EEF2` |
| Lens accent: amber (the pupil) | `#C9761A` | `#E6A04F` |
| Official ground | `#E7EEF2` porcelain | `#0B1118` ink |

Amber is the light that passes through the lens. It sits beside Scholar indigo `#3F5AF3` and ClinicOS teal `#1B7786` without competing with either.

## Construction (units of the 600-unit ring)

The mark is a **search lens**: an aperture (a lens rim around a pupil) with a handle.

- **Ring:** outer R = 300, inner r = 150 (half the radius, the same half-radius used in the ClinicOS construction).
- **Crease:** one straight cut through the centre at the **Varaxis V angle** (3:2 slope, 56.31°), drawn rising to the right. It is a 30-unit gap, so the ring becomes two pieces.
- **Pupil:** the accent. A disc of radius 120 (r − 30), so it sits 30 units inside the ring on every side: every gap in the mark is the same width.
- **Handle:** leaves the ring towards the lower right along the **mirror of the V angle** (2:3 run to rise). It is as wide as the ring is thick (150), and runs 220 units. Its inner end is an arc concentric with the ring, 30 units outside it, so the gap matches every other gap. Its outer corners are softened with r = 50, the radius the V uses.
- Every curve is a true circular arc; the only straight lines run along the V angle or its mirror.
- The mark's viewBox is 648.1 × 779.745 (the ring is 600 across; the handle extends it).

## Wordmark and lockups

Exactly as the Varaxis masters:
- Montserrat SemiBold (600), tracking 0.20 em; **Λ** is the V glyph flipped about the cap height.
- "BY VARAXIS" in Montserrat Medium (500) at 30 % of the wordmark cap height, tracking 0.80 em.
- "LENS" is shorter than "BY VARAXIS", so in the horizontal lockup both lines are centred on the wider one.

## Usage

- **Clear space:** at least a quarter of the mark's height on every side.
- **Minimum size:** the symbol alone at 16 px; below a 24 px wordmark cap height drop the endorsement and use `lens-horizontal-compact`.
- **Do not:** rotate the crease or the handle, change the gaps, recolour the ring or handle, add effects, or set the wordmark in live text.

## Regenerating

```sh
cd brand/tools
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python fetch_fonts.py      # downloads Montserrat into tools/.fonts (git-ignored)
.venv/bin/python build_lens.py       # rewrites ../masters
node export_png.js                   # optional: PNG exports into ../masters/png (needs Playwright)
```

Then copy the files the app uses into `ui/assets/`: `lens-horizontal-compact.svg` → `logo.svg`, `lens-mark.svg` → `icon.svg`, `lens-horizontal.svg` → `logo-endorsed.svg`, `lens-wordmark-endorsed.svg` → `wordmark-endorsed.svg`.

`geometry.py`, `wordmark.py`, `svgpath.py` and `fetch_fonts.py` are copied unchanged from the Varaxis brand toolchain, so Lens is built exactly the same way as the other marks.
