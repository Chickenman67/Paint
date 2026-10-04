# work/lib/ink.py — the reference's line and fill primitives, per work/STYLE_CANON.md.
#
# WHY THIS EXISTS: two measured defects dominated every round up to 6.
#
#   1. STROKE TOO THIN. Median outline width measured on verified ref frames is
#      6 px. Ours was 3 px (work/study/stroke_cmp.py). At 3 px a hand-drawn figure
#      reads as a wire, not as a painted one. Every large shape wants 5-8 px.
#
#   2. WRONG LINE QUALITY. CLAUDE.md §4 prescribed "wobbly polylines, no bezier
#      curves, 1-2 px vertex jitter." That is wrong. The reference's Register-P
#      ridgelines and limbs are SMOOTH curves with LOW-FREQUENCY organic variation —
#      you can see this on the mountain silhouettes at t=5. High-frequency per-vertex
#      jitter on straight segments looks like static/noise, not like a hand.
#
# So: smooth curves, wobbled at low frequency, stroked thick.

import math
import random

from PIL import Image, ImageDraw

try:
    from . import v2paint as PA
except ImportError:
    import v2paint as PA           # noqa: E402  (flat import when on sys.path)

# --- Locked stroke scale (STYLE_CANON.md §3) ---
OUTLINE = 6      # large shapes: planets, mountains, figure body, object rims
DETAIL = 4       # contour lines on planets, medium objects
FINE = 2         # star specks, ticks, stipple
HAIRLINE = 1     # grid lines, keylines

INK = (0, 0, 0)


# ---------------------------------------------------------------------------
# Wobble: smooth, low-frequency, deterministic.
# ---------------------------------------------------------------------------

def wobble_points(pts, seed=0, amount=3.0, wavelength=90.0):
    """Displace a polyline with low-frequency, smooth, deterministic noise.

    amount     - peak displacement in px
    wavelength - approximate wavelength in px of the displacement (large = slow)

    Two sine components at incommensurate wavelengths avoid an obvious repeat while
    staying perfectly deterministic for a given seed. The result reads as a hand
    wobble; per-vertex random jitter does not.
    """
    rnd = random.Random(seed)
    ph1 = rnd.uniform(0, math.tau)
    ph2 = rnd.uniform(0, math.tau)
    k1 = math.tau / max(1.0, wavelength)
    k2 = math.tau / max(1.0, wavelength * 0.37)

    out = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        # taper the wobble at the endpoints so shapes still meet cleanly
        t = i / max(1, n - 1)
        taper = math.sin(math.pi * t) ** 0.5
        dx = amount * taper * (0.68 * math.sin(k1 * x + ph1) + 0.32 * math.sin(k2 * y + ph2))
        dy = amount * taper * (0.68 * math.cos(k1 * y + ph2) + 0.32 * math.cos(k2 * x + ph1))
        out.append((x + dx, y + dy))
    return out


def smooth_closed(points, samples=14):
    """Catmull-Rom through `points` -> a dense smooth polyline, then closed.

    Use this for organic silhouettes (mountains, planets, blobs). The result is a
    genuine smooth curve, which is what the reference actually draws.
    """
    p = list(points)
    if len(p) < 3:
        return p
    ext = [p[-1]] + p + [p[0], p[1]]
    out = []
    for i in range(len(p)):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


# ---------------------------------------------------------------------------
# Stroked primitives
# ---------------------------------------------------------------------------

def draw_smooth(draw, points, fill=None, outline=INK, width=OUTLINE,
                seed=0, wobble=3.0, wavelength=90.0, closed=True):
    """Draw a smooth, hand-wobbled, THICK-outlined shape. The workhorse for
    Register P: mountains, planets, the ground plane, any organic silhouette.

    PAINTERLY (round-2 critic): the fill goes through v2paint.fill_poly and the
    keyline through v2paint.hand_stroke, so a shape carries pigment variation and
    a width-varying edge instead of one flat RGB value and a constant-width curve.
    That is the difference between vector clip-art and hand-drawn art. Both paths
    are seeded from `seed`, so renders stay byte-identical across runs.
    """
    pts = wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = smooth_closed(pts) if closed else _smooth_open(pts)
    if fill is not None:
        # Grow the fill under the keyline so its own edge wobble can't leave a
        # pale crescent inside the rim (see v2paint.fill_poly). Round 3: this was
        # width*0.4 (2-3px) while v2paint.EDGE went 1.6 -> 4.6px, so the fill
        # could fall up to 2px short of the stroke and the crescent came back.
        # The dilation now covers the fill's own irregularity plus the keyline's
        # half-width, with a floor of EDGE+2 so raising EDGE cannot reintroduce
        # the defect.
        grow = 0
        if outline and width > 0:
            grow = max(int(round(width * 0.5)), int(PA.EDGE) + 2)
        PA.fill_poly(PA.img_of(draw), dense, fill, seed=seed ^ 0x51A3, grow=grow)
    if outline is not None and width > 0:
        PA.hand_stroke(draw, dense, outline, width, closed=closed,
                       seed=seed ^ 0x77B1, wavelength=max(24.0, wavelength * 0.8))
    return dense


def _smooth_open(points, samples=12):
    if len(points) < 3:
        return list(points)
    p = list(points)
    # Catmull-Rom needs one control point of padding on EACH side so that
    # ext[i+3] is in range for every i in range(len(p)). One pad per side (the
    # old [p[0]] + p + [p[-1]]) gives len(p)+2 entries and overruns by one.
    ext = [p[0], p[0]] + p + [p[-1], p[-1]]
    out = []
    for i in range(len(p)):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def draw_outline(draw, points, color=INK, width=OUTLINE, closed=True, seed=0,
                 wobble=2.0, wavelength=110.0):
    """Stroked-only version of draw_smooth (no fill)."""
    return draw_smooth(draw, points, fill=None, outline=color, width=width,
                       seed=seed, wobble=wobble, wavelength=wavelength, closed=closed)


def draw_disc(draw, cx, cy, r, fill=None, outline=INK, width=OUTLINE, seed=0, wobble=3.0):
    """A hand-drawn circle. Built from a wobbled 8-gon run through a smooth spline
    so the edge is an organic circle, not a perfect one.

    ROUND 3 -- the silhouette is now radius-relative. This is the fix for the
    critic's "the circle is too perfect": `wobble` was an absolute px figure and
    every caller in v2subjects passes 2.5-3.0, so a r=225 planet got 3px of
    deviation on a 450px diameter -- 0.7%, invisible. The control points now
    also take a displacement proportional to the radius, which is how a hand
    actually draws a big circle (bigger loop, bigger error) and which is what
    makes a large disc read as drawn rather than plotted. Small shapes are
    essentially unaffected: at r=40 the extra term is under 1px.

    EDGE (v2paint) adds a second, independent displacement on the rasterised
    edge, so the fill and the keyline are each irregular and the two still
    agree at the scale that matters because draw_smooth feeds both the SAME
    dense polyline.
    """
    pts = []
    for i in range(8):
        a = math.tau * i / 8
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    amp = wobble + r * 0.024
    return draw_smooth(draw, pts, fill=fill, outline=outline, width=width,
                       seed=seed, wobble=amp, wavelength=r * 1.6)


def draw_ridge(draw, x0, x1, y_base, height, seed=0, fill=None,
               segments=5, outline=INK, width=OUTLINE, roughness=0.35):
    """A mountain / horizon silhouette spanning x0..x1. This is the single most
    common Register-P element and the one our builds kept leaving out (empty
    lavender fields)."""
    rnd = random.Random(seed)
    pts = []
    span = x1 - x0
    for i in range(segments + 1):
        x = x0 + span * i / segments
        # peaks higher in the middle, tapering at the edges
        env = math.sin(math.pi * i / segments) ** 0.7
        h = height * env * rnd.uniform(1 - roughness, 1 + roughness)
        pts.append((x, y_base - h))
    pts = [(x0, y_base)] + pts + [(x1, y_base)]
    return draw_smooth(draw, pts, fill=fill, outline=outline, width=width,
                       seed=seed + 1, wobble=2.5, wavelength=span * 0.45)


def draw_ground(draw, x0, x1, y_top, y_bottom, fill, seed=0, width=OUTLINE,
                roughness=4.0):
    """A ground plane with a hand-wobbled top edge."""
    rnd = random.Random(seed)
    pts = []
    x = x0
    while x < x1:
        pts.append((x, y_top + rnd.uniform(-roughness, roughness)))
        x += 26
    pts.append((x1, y_top))
    pts = [(x0, y_bottom), (x0, y_top)] + pts + [(x1, y_bottom)]
    return draw_smooth(draw, pts, fill=fill, outline=INK, width=width,
                       seed=seed + 2, wobble=2.0, wavelength=140.0)


# ---------------------------------------------------------------------------
# Fills
# ---------------------------------------------------------------------------

def flat_fill(draw, shape_bbox, color, seed=0, softness=1):
    """A flat color region. Register P default -- no gradients on objects.

    Still painterly: the region gets the same low-frequency pigment drift as every
    other fill, so a large flat block does not read as a UI panel. No falloff, no
    highlight -- the value stays even, only the pigment moves."""
    PA.fill_rect(PA.img_of(draw), shape_bbox, color, seed=seed)
    return shape_bbox


def stipple(draw, x0, y0, x1, y1, color, seed=0, density=0.06, r=1, spread=1):
    """Scatter dots inside a rect. The reference's painterly texture signature
    (visible in the ground at t=5 and the gradient seam at t=20)."""
    rnd = random.Random(seed)
    area = max(1, (x1 - x0) * (y1 - y0))
    n = int(area * density)
    for _ in range(n):
        x = rnd.randint(int(x0), int(x1))
        y = rnd.randint(int(y0), int(y1))
        rr = rnd.randint(max(1, r), r + spread)
        draw.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color)
    return n


def starfield(img, seed=0, n=90, x0=0, y0=0, x1=1280, y1=720, color=(255, 255, 255)):
    """Anti-aliased star dots on a dark field (Register S). The reference's stars
    are clean soft circles of varied size, not wobbly marks."""
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.randint(x0, x1)
        y = rnd.randint(y0, y1)
        r = rnd.choice([0, 0, 1, 1, 1, 2, 2, 3])
        if r == 0:
            d.point((x, y), fill=color)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    return d
