"""Exact construction of the Lens mark, on the Varaxis system.

Lens is a lens: a ring (the rim) around an aperture. Every straight cut uses the Varaxis V angle
(3:2 slope) or its mirror, pieces are separated by one equal gap, and every curve is a true
circular arc. Nothing is traced. See ../README.md for the rules these numbers encode."""
import math
from geometry import f, rounded_path

K = math.sqrt(13)          # |(3, 2)|: cut lines are 3x + 2y = c, which run at the V angle ("/")
P = lambda p: f"{f(p[0])} {f(p[1])}"


def _chord(cx, cy, r, c):
    """Where the line 3x + 2y = c meets the circle; top point first."""
    n = (3 / K, 2 / K); d = c / K - (n[0] * cx + n[1] * cy)
    h = math.sqrt(max(r * r - d * d, 0)); p0 = (cx + n[0] * d, cy + n[1] * d); t = (-n[1], n[0])
    a = (p0[0] + t[0] * h, p0[1] + t[1] * h); b = (p0[0] - t[0] * h, p0[1] - t[1] * h)
    return (a, b) if a[1] < b[1] else (b, a)


def _arc(cx, cy, r, p, q, lo, hi):
    """Arc from p to q on the circle, along the side that stays between the cut lines lo and hi."""
    a0 = math.atan2(p[1] - cy, p[0] - cx); a1 = math.atan2(q[1] - cy, q[0] - cx)
    for sweep in (1, 0):
        span = (a1 - a0) % (2 * math.pi) if sweep else -((a0 - a1) % (2 * math.pi))
        if all(lo - 1e-6 <= 3 * (cx + r * math.cos(a0 + span * t)) + 2 * (cy + r * math.sin(a0 + span * t)) <= hi + 1e-6
               for t in (0.1, 0.3, 0.5, 0.7, 0.9)):
            return f"A{f(r)} {f(r)} 0 {1 if abs(span) > math.pi else 0} {sweep} {P(q)}"
    raise ValueError("no arc")


def disc_strip(cx, cy, r, lo, hi):
    """The part of a disc between the cut lines lo and hi (either may lie outside the disc)."""
    cmin, cmax = 3 * cx + 2 * cy - r * K, 3 * cx + 2 * cy + r * K
    lo, hi = max(lo, cmin), min(hi, cmax)
    if hi <= lo:
        return ""
    if lo <= cmin + 1e-9 and hi >= cmax - 1e-9:      # the whole disc
        return f"M{P((cx - r, cy))}A{f(r)} {f(r)} 0 1 1 {P((cx + r, cy))}A{f(r)} {f(r)} 0 1 1 {P((cx - r, cy))}Z"
    if lo <= cmin + 1e-9:
        a, b = _chord(cx, cy, r, hi); return f"M{P(a)}L{P(b)}{_arc(cx, cy, r, b, a, cmin, hi)}Z"
    if hi >= cmax - 1e-9:
        a, b = _chord(cx, cy, r, lo); return f"M{P(a)}{_arc(cx, cy, r, a, b, lo, cmax)}Z"
    (a1, b1), (a2, b2) = _chord(cx, cy, r, lo), _chord(cx, cy, r, hi)
    return f"M{P(a1)}L{P(b1)}{_arc(cx, cy, r, b1, b2, lo, hi)}L{P(a2)}{_arc(cx, cy, r, a2, a1, lo, hi)}Z"


def ring_strip(cx, cy, R, r, lo, hi):
    """The part of a ring between the cut lines lo and hi. Draw with fill-rule evenodd."""
    return disc_strip(cx, cy, R, lo, hi) + disc_strip(cx, cy, r, lo, hi)


def cut_at(cx, cy, along):
    """The cut line through the point `along` units from the centre, measured perpendicular to the cut."""
    return 3 * cx + 2 * cy + along * K


# ---------- the approved Lens mark (viewBox 600 x 600) ----------
LENS = dict(R=300, r=150, G=30)


def lens_geom(c=LENS):
    """Aperture: a ring split by one crease at the V angle, around an accent pupil.

    - Ring: outer R = 300, inner r = 150 (half the radius).
    - Crease: through the centre, along the V angle (3:2, drawn "/"), as a G-unit gap.
    - Pupil: the accent, radius r - G, so it sits G units inside the ring on every side.
    """
    R, r, G = c['R'], c['r'], c['G']
    cx = cy = R; mid = cut_at(cx, cy, 0); half = G / 2 * K
    inf = 1e9
    return [
        (ring_strip(cx, cy, R, r, -inf, mid - half), 'base'),
        (ring_strip(cx, cy, R, r, mid + half, inf), 'base'),
        (disc_strip(cx, cy, r - G, -inf, inf), 'accent'),
    ]
