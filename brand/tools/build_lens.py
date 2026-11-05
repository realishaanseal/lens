"""Generate the Lens masters in ../masters, on the same system as the Varaxis brand masters.

Lockup rules, type and colour follow the Varaxis brand toolchain (brand/tools/build_masters.py in
the varaxis repo); only the mark geometry (lens_geometry.py) and the accent are Lens's own."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from geometry import f
from lens_geometry import lens_geom
from svgpath import path_polys
from wordmark import wordmark

INK = '#0B1118'; POR = '#E7EEF2'
ACC = {'light': '#C9761A', 'dark': '#E6A04F'}      # Lens amber: the light that passes through the lens
WM = dict(weight=600, tracking=0.20)
EN = dict(weight=500, tracking=0.80, ratio=0.30)
NAME, WORD = 'Lens by Varaxis', 'LENS'


def bbox_of(ds):
    xs = []; ys = []
    for d in ds:
        for poly in path_polys(d):
            xs += [p[0] for p in poly]; ys += [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def tx(d, s, dx, dy):
    """Uniform scale + translate of an M/L/A/Z/Q/C path (arc radii scale too)."""
    toks = re.findall(r'[MLAZCQHVT]|-?\d*\.?\d+(?:e-?\d+)?', d); out = []; i = 0; cmd = None
    while i < len(toks):
        t = toks[i]
        if t in 'MLAZCQHVT': cmd = t; out.append(t); i += 1; continue
        if cmd in 'MLT': out += [f(float(toks[i]) * s + dx), f(float(toks[i + 1]) * s + dy)]; i += 2
        elif cmd == 'H': out += [f(float(toks[i]) * s + dx)]; i += 1
        elif cmd == 'V': out += [f(float(toks[i]) * s + dy)]; i += 1
        elif cmd == 'C':
            for _ in range(3): out += [f(float(toks[i]) * s + dx), f(float(toks[i + 1]) * s + dy)]; i += 2
        elif cmd == 'Q':
            for _ in range(2): out += [f(float(toks[i]) * s + dx), f(float(toks[i + 1]) * s + dy)]; i += 2
        elif cmd == 'A':
            rx, ry, ph, la, sw, x, y = toks[i:i + 7]
            out += [f(float(rx) * s), f(float(ry) * s), ph, la, sw, f(float(x) * s + dx), f(float(y) * s + dy)]; i += 7
    return re.sub(r' ?([MLAZCQHVT]) ?', r'\1', ' '.join(out))


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" width="{f(w)}" height="{f(h)}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


def build(form, theme, mono=False, endorse=True):
    base = INK if theme == 'light' else POR
    acc = base if mono else ACC[theme]
    parts = lens_geom(); mb = bbox_of([d for d, _ in parts]); mw, mh = mb[2] - mb[0], mb[3] - mb[1]

    def mark_at(x, y, height):
        s = height / mh
        return ''.join(f'<path fill="{acc if role == "accent" else base}" fill-rule="evenodd" '
                       f'd="{tx(d, s, x - mb[0] * s, y - mb[1] * s)}"/>' for d, role in parts)

    if form == 'mark':
        return svg(mw, mh, mark_at(0, 0, mh), NAME)
    C = 150.0
    wd, (wl, wr) = wordmark(WORD, WM['weight'], C, WM['tracking']); ww = wr - wl
    if endorse:
        Ce = C * EN['ratio']; ed, (el, er) = wordmark('BY VARAXIS', EN['weight'], Ce, EN['tracking']); ew = er - el
    word = lambda x, y: ''.join(f'<path fill="{base}" d="{tx(d, 1, x - wl, y)}"/>' for d in wd)
    endo = lambda x, y: ''.join(f'<path fill="{base}" d="{tx(d, 1, x - el, y)}"/>' for d in ed)
    if form == 'wordmark':
        return svg(ww, C, word(0, C), NAME)
    if form == 'wordmark-endorsed':                       # the wordmark over "BY VARAXIS", no symbol
        egap = 0.5 * C; W = max(ww, ew)
        return svg(W, C + egap + Ce, word((W - ww) / 2, C) + endo((W - ew) / 2, C + egap + Ce), NAME)
    if form == 'stacked':
        MH = 4.0 * C; gap = 0.6 * C; egap = 0.5 * C
        W = max(MH, ww, ew if endorse else 0); H = MH + gap + C + ((egap + Ce) if endorse else 0)
        body = mark_at((W - MH) / 2, 0, MH) + word((W - ww) / 2, MH + gap + C)
        if endorse: body += endo((W - ew) / 2, MH + gap + C + egap + Ce)
        return svg(W, H, body, NAME)
    if form == 'horizontal':
        if endorse:
            MH = 2.6 * C; g1 = 0.62 * C; dvw = 0.05 * C; block = C + 0.45 * C + Ce
            xdiv = MH + g1; xt = xdiv + dvw + g1; ty = (MH - block) / 2
            body = mark_at(0, 0, MH) + f'<rect fill="{base}" x="{f(xdiv)}" y="0" width="{f(dvw)}" height="{f(MH)}"/>'
            bw = max(ww, ew)   # "LENS" is narrower than "BY VARAXIS": centre both lines in the wider one
            body += word(xt + (bw - ww) / 2, ty + C) + endo(xt + (bw - ew) / 2, ty + C + 0.45 * C + Ce)
            return svg(xt + bw, MH, body, NAME)
        MH = 2.4 * C; g1 = 0.75 * C
        return svg(MH + g1 + ww, MH, mark_at(0, 0, MH) + word(MH + g1, (MH - C) / 2 + C), NAME)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'masters')
    os.makedirs(out, exist_ok=True); files = []
    for form in ['mark', 'stacked', 'horizontal', 'wordmark']:
        for theme in ['light', 'dark']:
            fn = f"lens-{form}{'' if theme == 'light' else '-reverse'}.svg"
            open(os.path.join(out, fn), 'w').write(build(form, theme)); files.append(fn)
    for theme in ['light', 'dark']:
        fn = f"lens-wordmark-endorsed{'' if theme == 'light' else '-reverse'}.svg"
        open(os.path.join(out, fn), 'w').write(build('wordmark-endorsed', theme)); files.append(fn)
        fn = f"lens-mark-mono{'' if theme == 'light' else '-reverse'}.svg"
        open(os.path.join(out, fn), 'w').write(build('mark', theme, mono=True)); files.append(fn)
        fn = f"lens-horizontal-compact{'' if theme == 'light' else '-reverse'}.svg"
        open(os.path.join(out, fn), 'w').write(build('horizontal', theme, endorse=False)); files.append(fn)
    print(len(files), 'files'); print('\n'.join(files))
