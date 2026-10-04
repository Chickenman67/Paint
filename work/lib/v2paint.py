# work/lib/v2paint.py -- the PAINTERLY layer: pigment, hand-drawn strokes, paper.
#
# WHY THIS EXISTS (round-2 blind critic, 9 of 10 frames lost)
#   Our frames read as clean VECTOR CLIPART. The bar reads as PAINTERLY HAND-DRAWN
#   ART. Three concrete tells, all of them properties of a machine-drawn fill/stroke:
#
#     1. FILLS ARE MATHEMATICALLY FLAT. `ImageDraw.polygon(pts, fill=col)` lays down
#        one exact RGB value per pixel. The bar's shapes carry value drift, hue drift
#        and faint brush banding inside a single flat region.
#     2. OUTLINES ARE MACHINE-PERFECT. `ImageDraw.line(..., width=W)` is constant
#        width along a Catmull-Rom curve. A real keyline swells and thins as the hand
#        moves, and its edge is not a perfect circle.
#     3. THE PAGE IS DEAD. A flat #fdfdfd field has no tooth at all.
#
# WHAT THIS MODULE PROVIDES
#   img_of(draw)        -- recover the PIL Image an ImageDraw is bound to.
#   fbm(...)            -- seeded low-frequency value field (numpy, deterministic).
#   fill_poly(...)      -- painterly fill: pigment variation + edge irregularity.
#   hand_stroke(...)    -- variable-width keyline drawn as overlapping segments.
#   paper_overlay(...)  -- very low contrast page tooth.
#
# DETERMINISM
#   Every random source is seeded. `np.random.default_rng(seed)` is stable for a
#   given seed across runs on the same numpy version, and the PIL upsample path is
#   deterministic, so the same scene renders byte-identical twice. There is no
#   unseeded global randomness anywhere in this file.
#
# ESCAPE HATCH
#   Set GAUNTLET_PLAIN=1 in the environment to turn every painterly path into the
#   original flat PIL call. That exists so a bad render can be bisected without
#   reverting code, and so the v1 pipeline (work/segments/*, which shares ink.py)
#   has a one-env-var opt-out if it ever needs the old machine-flat look back.

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Global on/off. Read once at import; PAINTERLY is the intended default.
PAINTERLY = os.environ.get('GAUNTLET_PLAIN', '') not in ('1', 'true', 'yes')

# --- Texture strength knobs ------------------------------------------------
# ROUND 3. Round 2 set these so they would be obvious on a close-up crop and
# "felt, not seen" at 1280x720. The round-2 blind critic still read 9/10 frames as
# clean vector clipart, and looking at the full frames confirms why: a +-7.5%
# MULTIPLICATIVE drift on a near-black fill (the night side is RGB 38,38,44) is
# +-3 levels, which is invisible; on a 450px disc a 1.6px edge wobble is 0.35%
# of the radius; and a 57px brush-band period averages out to nothing once the
# frame is viewed at 1:1. So these are roughly DOUBLED, and -- more importantly --
# the fill now carries an ADDITIVE term scaled by how DARK the colour is, because
# multiplicative modulation is exactly wrong for dark paint (a painter cannot
# make black much blacker, but they can and do leave it uneven and slightly warm).
#
# The ceilings that still hold: none of these touch TEXT. Every text element is
# composited AFTER the art it sits on, so paint texture cannot hurt legibility;
# and the page tooth is laid down in the bg element, under the type.
VALUE = 0.150     # +-15% brightness drift inside a fill (broad, low-frequency)
VALUE_FINE = 0.055  # +-5.5 levels of brush-scale tooth on top of the broad wash
DARK = 9.0        # additive levels on a pure-black fill, tapering to ~0 on white
TINT = 8.0        # +-8 levels of red/blue counter-drift (hue wobble)
BAND = 6.5        # +-6.5 levels of brush banding
BAND_FREQ = 0.055  # radians/px -> ~114px period. Round 2 used 0.11 (57px), which
                   # is fine-tooth at ship size; broader bands read as a BRUSH.
EDGE = 4.6        # px of low-frequency edge irregularity on filled shapes
STROKE_VARY = 0.42  # +-42% keyline width variation
PAPER_GRAIN = 2.2  # levels of per-pixel page tooth. DELIBERATELY not raised much in
                   # round 3: per-pixel UNIFORM noise is the one texture that
                   # always reads as digital dither / video noise rather than as
                   # paper, and at 5.5 the white page looked like a bad scan.
                   # Judge paper on the blotch term, not this one.
PAPER_BLOTCH = 9.0  # levels of large-scale page unevenness. This is the term that
                    # actually reads as paper: broad, soft, low-frequency drift.


# ---------------------------------------------------------------------------
# plumbing
# ---------------------------------------------------------------------------

def img_of(draw):
    """Recover the PIL Image behind an ImageDraw.

    ink.py's primitives are all handed an ImageDraw, but painterly work needs the
    pixel buffer. Pillow stores it as `_image`; `im` is the ImagingCore and is not
    an Image. We check both attribute names and validate the type rather than
    trusting one, because this is the only place we reach into Pillow internals.
    """
    if isinstance(draw, Image.Image):
        return draw
    for attr in ('_image', 'image'):
        v = getattr(draw, attr, None)
        if isinstance(v, Image.Image):
            return v
    raise TypeError('cannot recover an Image from %r' % (type(draw),))


def _seed(seed):
    """numpy wants a non-negative int; our seeds are small ints but may be xor'd."""
    return int(seed) & 0x7FFFFFFF


def _f_image(arr):
    """float32 (h,w) -> PIL 'F' image (for BICUBIC upsampling)."""
    return Image.fromarray(np.ascontiguousarray(arr, dtype=np.float32), mode='F')


def _luma(rgb):
    """Rec. 709 luma of an RGB triplet. Used to weight the additive paint tooth
    so dark colours get visible texture and near-white colours get none."""
    r, g, b = (float(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ---------------------------------------------------------------------------
# seeded low-frequency noise
# ---------------------------------------------------------------------------

def fbm(w, h, seed=0, cells=5, octaves=3, persist=0.55):
    """A seamless-ish low-frequency value field in roughly [-1, 1], shape (h, w).

    Built by summing upsampled random grids at doubling frequencies -- value noise.
    This is the "mottling" scale: broad soft patches, not pixel dust. Per-pixel
    noise is PAPER_GRAIN's job, not this function's.
    """
    if w <= 0 or h <= 0:
        return np.zeros((max(0, h), max(0, w)), np.float32)
    rng = np.random.default_rng(_seed(seed))
    out = np.zeros((h, w), np.float32)
    amp, total, c = 1.0, 0.0, float(max(2, cells))
    for _ in range(max(1, octaves)):
        gw = max(2, int(round(c)))
        gh = max(2, int(round(c * h / float(max(1, w)))) + 1)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        up = np.asarray(_f_image(g).resize((w, h), Image.BICUBIC), np.float32)
        out += up * amp
        total += amp
        amp *= persist
        c *= 2.0
    out /= max(1e-6, total)
    sd = float(out.std())
    if sd > 1e-6:
        out /= sd * 2.1
    return np.clip(out, -1.0, 1.0)


def smooth_walk(n, seed=0, cells=4, octaves=2):
    """A smooth 1-D offset profile of length n in roughly [-1, 1] (mean removed).

    Used for brush-band boundaries and stroke-width profiles: it needs to wander
    slowly, like a hand dragging a brush, not vibrate.
    """
    if n <= 0:
        return np.zeros(0, np.float32)
    if n == 1:
        return np.zeros(1, np.float32)
    rng = np.random.default_rng(_seed(seed))
    out = np.zeros(n, np.float32)
    amp, total, c = 1.0, 0.0, float(max(2, cells))
    for _ in range(max(1, octaves)):
        gw = max(2, int(round(c)))
        g = rng.standard_normal((1, gw)).astype(np.float32)
        up = np.asarray(_f_image(g).resize((n, 1), Image.BICUBIC), np.float32)[0]
        out += up * amp
        total += amp
        amp *= 0.5
        c *= 2.0
    out /= max(1e-6, total)
    sd = float(out.std())
    if sd > 1e-6:
        out -= out.mean()
        out /= sd * 1.9
    return np.clip(out, -1.0, 1.0).astype(np.float32)


def wobble_edge(pts, seed=0, amount=EDGE, wavelength=110.0, closed=True):
    """Displace a polygon along its own normals with a low-frequency profile.

    This is the "edge irregularity" half of the hand-drawn read. ink.wobble_points
    already wobbles the control points before splining; this adds a second, coarser
    displacement directly on the rasterised edge so the silhouette never reads as a
    mathematically exact circle even where the spline happens to be smooth.
    """
    pts = [(float(p[0]), float(p[1])) for p in pts]
    n = len(pts)
    if amount <= 0.0 or n < 3:
        return pts

    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                    pts[i][1] - pts[i - 1][1]))
    total = s[-1]
    if closed:
        total += math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
    total = max(1.0, total)

    rnd = random.Random(_seed(seed) ^ 0x3E7D)
    ph1 = rnd.uniform(0.0, math.tau)
    ph2 = rnd.uniform(0.0, math.tau)
    k1 = math.tau / max(1.0, wavelength)
    k2 = math.tau / max(1.0, wavelength * 0.43)

    out = []
    for i in range(n):
        x, y = pts[i]
        ip = (i - 1) % n
        jn = (i + 1) % n
        tx = pts[jn][0] - pts[ip][0]
        ty = pts[jn][1] - pts[ip][1]
        L = math.hypot(tx, ty)
        if L < 1e-6:
            out.append((x, y))
            continue
        nx, ny = -ty / L, tx / L
        if closed:
            taper = 1.0
        else:
            u = s[i] / total
            taper = math.sin(math.pi * min(1.0, max(0.0, u))) ** 0.35
        d = amount * taper * (0.70 * math.sin(k1 * s[i] + ph1)
                              + 0.30 * math.sin(k2 * s[i] + ph2))
        out.append((x + nx * d, y + ny * d))
    if not closed:
        # Pin the ends so strokes still meet their neighbours exactly.
        out[0] = pts[0]
        out[-1] = pts[-1]
    return out


# ---------------------------------------------------------------------------
# painterly fill
# ---------------------------------------------------------------------------

def fill_poly(img, pts, color, seed=0, value=VALUE, tint=TINT, band=BAND,
              band_angle=0.0, edge=EDGE, bbox=None, grow=0):
    """Fill a polygon with `color`, but painted rather than plotted.

    Inside the shape: low-frequency brightness mottling (fbm), a small hue
    counter-drift on a second field, and faint directional brush banding. Outside:
    untouched. The overall colour is unchanged on average, so flat-fill readability
    survives -- the drift is only ever a few percent.

    `grow` dilates the fill mask by N px so the fill always tucks UNDER a keyline
    stroked on the same path. Without it the fill's own edge wobble (seeded
    independently of the outline's) can fall a pixel or two short of the stroke and
    leave a pale crescent inside the rim, which reads as a rendering error rather
    than as paint that missed the line.

    `img` may be RGB or RGBA; the original alpha is preserved inside the shape.
    Returns the bbox actually painted, or None if the shape was off-canvas.
    """
    pts = [(float(p[0]), float(p[1])) for p in pts]
    if len(pts) < 3:
        return None
    if not PAINTERLY:
        ImageDraw.Draw(img).polygon(pts, fill=color)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    if edge > 0.0:
        # Wavelength tracks the shape's own size so a big disc and a small swatch
        # get the same *relative* amount of irregularity.
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        pts = wobble_edge(pts, seed=seed ^ 0x2B4F, amount=edge,
                          wavelength=max(18.0, span * 0.42), closed=True)

    if bbox is None:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    # Pad by the dilation radius so MaxFilter never clips against the region edge
    # (a clipped dilation would leave a hard notch on the rim).
    gp = int(grow or 0) + 3
    x0 = int(math.floor(bbox[0])) - gp
    y0 = int(math.floor(bbox[1])) - gp
    x1 = int(math.ceil(bbox[2])) + gp + 1
    y1 = int(math.ceil(bbox[3])) + gp + 1
    W_, H_ = img.size
    x0c, y0c = max(0, x0), max(0, y0)
    x1c, y1c = min(W_, x1), min(H_, y1)
    if x1c <= x0c or y1c <= y0c:
        return None
    bw, bh = x1c - x0c, y1c - y0c

    mask = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(mask).polygon([(p[0] - x0c, p[1] - y0c) for p in pts], fill=255)
    if grow and grow > 0:
        # Dilation via MaxFilter so the fill slides under the keyline. Size must
        # be odd; 2*grow+1 px of spread.
        k = int(grow) * 2 + 1
        if k <= 9:
            mask = mask.filter(ImageFilter.MaxFilter(k))
        else:
            # PIL MaxFilter degrades badly above 9; do it in repeated 9px passes.
            mask = mask
            rem = int(grow)
            while rem > 0:
                step = min(4, rem)
                mask = mask.filter(ImageFilter.MaxFilter(step * 2 + 1))
                rem -= step

    # The TARGET's alpha is irrelevant here and must NOT be carried over: a fill
    # PAINTS, it does not tint. engine3 draws every element onto a fresh
    # transparent RGBA tile, so preserving the tile's alpha (0) made every fill
    # come out transparent and each shape rendered hollow -- white page showing
    # through the keyline. The mask IS the alpha.

    sd = _seed(seed)
    m = fbm(bw, bh, seed=sd ^ 0x11, cells=5, octaves=3)
    # Paint `color`, then modulate IT. (Modulating the pixels already under the
    # shape -- the earlier bug here -- means a fill drawn over the white page
    # comes out white, and only a fill drawn over another fill shows its colour.)
    base = np.array([float(c) for c in color[:3]], np.float32)
    out = base[None, None, :] * (1.0 + value * m)[..., None]

    # ROUND 3 -- brush-scale tooth, ADDITIVE, weighted toward dark colours.
    # Two reasons this is additive and not another multiplicative term:
    #   1. On a near-black fill (the night hemisphere of a tidally-locked planet
    #      is 38,38,44) ANY multiplicative term is +-3 levels, i.e. invisible.
    #      The round-2 frames prove it: the night side came out dead flat black.
    #   2. Real paint on a dark ground shows unevenness as a change in how much
    #      light the surface RETURNS, not as a change in the pigment itself --
    #      so an additive drift is both stronger and more truthful here.
    # The weight (1.22 - luma/255) makes it strong on black and ~nil on the white
    # page, so this can never make a light fill look dirty, and it is zeroed
    # entirely when value==0 (ink shapes -- arrowheads, star rays -- pass that).
    if value > 0.0:
        tooth_w = VALUE_FINE + DARK * (1.22 - float(_luma(base)) / 255.0)
        if tooth_w > 1e-3:
            m2 = fbm(bw, bh, seed=sd ^ 0x2D, cells=13, octaves=2)
            out += tooth_w * m2[..., None]
    if tint > 0.0:
        t = fbm(bw, bh, seed=sd ^ 0x77, cells=4, octaves=2)
        out[..., 0] += tint * t
        out[..., 2] -= tint * t
    if band > 0.0:
        # Directional banding: a wave across the shape, phase-nudged by the
        # low-frequency field so it wanders instead of ruling straight lines.
        # Round 3: BAND_FREQ dropped 0.11 -> 0.055, i.e. a ~114px period. At the
        # old 57px the stripes were fine tooth and averaged to nothing when the
        # frame was viewed at 1:1; a period wider than a head reads as a brush
        # stroke, which is what the bar's fills actually look like.
        yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
        ca, sa = math.cos(band_angle), math.sin(band_angle)
        u = xx * ca + yy * sa
        phase = 2.4 * fbm(bw, bh, seed=sd ^ 0xA5, cells=3, octaves=2)
        out += band * np.sin(u * BAND_FREQ + phase)[..., None]
    out = np.clip(out, 0.0, 255.0).astype(np.uint8)

    if img.mode != 'RGBA':
        patch = Image.fromarray(out, mode='RGB')
        img.paste(patch, (x0c, y0c), mask)
    else:
        patch = Image.fromarray(
            np.dstack([out, np.asarray(mask, np.uint8)[..., None]]), mode='RGBA')
        img.paste(patch, (x0c, y0c), mask)
    return (x0c, y0c, x1c, y1c)


def fill_rect(img, box, color, seed=0, edge=EDGE, **kw):
    """Painterly axis-aligned fill. Edge wobble is scaled to the box so a long
    thin bar does not get its corners rounded off into blobs."""
    x0, y0, x1, y1 = box
    w, h = max(1.0, abs(x1 - x0)), max(1.0, abs(y1 - y0))
    amt = edge * min(1.0, min(w, h) / 90.0)
    return fill_poly(img, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], color,
                     seed=seed, edge=amt, **kw)


def round_rect_pts(x0, y0, x1, y1, radius, steps=6):
    """A rounded rectangle as a polygon, so it can take the painterly fill."""
    radius = max(0.0, min(radius, min(abs(x1 - x0), abs(y1 - y0)) * 0.5))
    if radius <= 0.5:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    corners = [(x1 - radius, y0 + radius, -math.pi / 2, 0.0),
               (x1 - radius, y1 - radius, 0.0, math.pi / 2),
               (x0 + radius, y1 - radius, math.pi / 2, math.pi),
               (x0 + radius, y0 + radius, math.pi, 1.5 * math.pi)]
    for ccx, ccy, a0, a1 in corners:
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / float(steps)
            pts.append((ccx + radius * math.cos(a), ccy + radius * math.sin(a)))
    return pts


def ellipse_pts(cx, cy, rx, ry=None, n=64, rot=0.0):
    """A sampled ellipse as a polygon (for hand_stroke / fill_poly)."""
    ry = rx if ry is None else ry
    ca, sa = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        a = math.tau * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def arc_pts(cx, cy, rx, ry, a0_deg, a1_deg, n=48):
    """A sampled elliptical arc as a polyline (for hand_stroke)."""
    pts = []
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / float(n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def pie_pts(cx, cy, r, a0_deg, a1_deg, n=48):
    """A pie/wedge as a closed polygon (centre + arc)."""
    pts = [(cx, cy)]
    pts.extend(arc_pts(cx, cy, r, r, a0_deg, a1_deg, n=n)[1:])
    return pts


# ---------------------------------------------------------------------------
# hand-drawn stroke
# ---------------------------------------------------------------------------

def _dot(d, p, r, color):
    """A round join/cap. Only used where the centreline actually turns -- see
    hand_stroke. Drawing one at EVERY spline sample beads the edge, because PIL
    rounds each line's width to an integer while the dot radius is the exact
    float half-width, so the dots protrude by up to half a pixel."""
    if r <= 0.9:
        d.point((int(round(p[0])), int(round(p[1]))), fill=color)
    else:
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def _turn(pts, i):
    """Absolute turn angle (radians) at pts[i], from the incoming/outgoing segs."""
    n = len(pts)
    ip = max(0, i - 1)
    jn = min(n - 1, i + 1)
    ax = pts[i][0] - pts[ip][0]
    ay = pts[i][1] - pts[ip][1]
    bx = pts[jn][0] - pts[i][0]
    by = pts[jn][1] - pts[i][1]
    la = math.hypot(ax, ay)
    lb = math.hypot(bx, by)
    if la < 1e-6 or lb < 1e-6:
        return 0.0
    c = (ax * bx + ay * by) / (la * lb)
    return math.acos(max(-1.0, min(1.0, c)))


def hand_stroke(draw, pts, color, width, closed=False, seed=0,
                vary=STROKE_VARY, wavelength=120.0, cap_round=True):
    """Stroke `pts` with a keyline whose WIDTH VARIES along its length.

    PIL's `line(width=W)` is the single biggest reason our outlines read as
    machine output: a real pen line swells where it slows and thins where it
    speeds up. We walk the (already smoothed + wobbled) centreline, give each
    point its own width from a smooth seeded profile, draw the segment at that
    width, and drop a round dot at every joint so the joins are round rather
    than notched.

    Returns the per-point half-width list, which callers can use to reason about
    how heavy the line ended up.
    """
    img = img_of(draw)
    d = draw if isinstance(draw, ImageDraw.ImageDraw) else ImageDraw.Draw(img)
    pts = [(float(p[0]), float(p[1])) for p in pts]
    n = len(pts)
    if n < 2 or width <= 0:
        return []

    if not PAINTERLY:
        d.line(list(pts) + ([pts[0]] if closed else []), fill=color,
               width=max(1, int(round(width))), joint='curve')
        return [width * 0.5] * n

    # arclength, so the width profile is spatially anchored rather than per-index
    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                    pts[i][1] - pts[i - 1][1]))
    total = max(1.0, s[-1])

    rnd = random.Random(_seed(seed) ^ 0xA17E)
    ph1 = rnd.uniform(0.0, math.tau)
    ph2 = rnd.uniform(0.0, math.tau)
    wl = max(12.0, wavelength)
    k1 = math.tau / wl
    k2 = math.tau / (wl * 0.41)

    hw = []
    for i in range(n):
        u = s[i] / total
        if closed:
            taper = 1.0
        else:
            # Slight taper at the two ends only -- a brush lifting off. Kept mild
            # so hairlines and crack lines do not fade out to nothing.
            taper = 0.80 + 0.20 * math.sin(math.pi * min(1.0, max(0.0, u)))
        prof = vary * (0.64 * math.sin(k1 * s[i] + ph1)
                       + 0.36 * math.sin(k2 * s[i] + ph2))
        hw.append(max(0.6, width * 0.5 * taper * (1.0 + prof)))

    # The dot radius must equal the RENDERED line's half-width. PIL rounds
    # line width to an integer; using the float half-width for the dot made every
    # join bulge by up to half a pixel and beaded the whole rim.
    def wr(h):
        return max(1, int(round(h * 2.0))) * 0.5

    # Join threshold: a dense Catmull-Rom sample turns by only a couple of
    # degrees, and dotting every one of those is what produced the gear-tooth
    # edge. A real corner turns much more than this.
    JOIN = math.radians(14.0)

    for i in range(n - 1):
        d.line([pts[i], pts[i + 1]], fill=color, width=max(1, int(round(hw[i] * 2.0))))
        if _turn(pts, i) >= JOIN:
            _dot(d, pts[i], wr(hw[i]), color)
    # caps always
    _dot(d, pts[-1], wr(hw[-1]), color)
    if closed:
        # the wrap-around joins are the same story
        d.line([pts[-1], pts[0]], fill=color, width=max(1, int(round(hw[-1] * 2.0))))
        if _turn(pts, 0) >= JOIN:
            _dot(d, pts[0], wr(hw[0]), color)
    elif cap_round:
        # extend a touch past the ends so the line does not stop dead
        for idx, nb in ((0, 1), (n - 1, n - 2)):
            dx, dy = pts[idx][0] - pts[nb][0], pts[idx][1] - pts[nb][1]
            L = math.hypot(dx, dy)
            if L > 1e-6:
                tip = (pts[idx][0] + dx / L * hw[idx] * 0.8,
                       pts[idx][1] + dy / L * hw[idx] * 0.8)
                _dot(d, tip, wr(hw[idx]) * 0.8, color)
    return hw


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------

def paper_overlay(img, seed=0, grain=PAPER_GRAIN, blotch=PAPER_BLOTCH,
                  bbox=None):
    """Give the page a tooth. Felt, not seen: a couple of levels, no more.

    Two fields: per-pixel grain (paper fibre) and a broad low-frequency blotch
    (paint sitting unevenly). Both are additive and tiny, so text laid down
    afterwards is unaffected and the page never looks dirty.
    """
    if not PAINTERLY:
        return img
    W_, H_ = img.size
    if bbox is None:
        x0, y0, x1, y1 = 0, 0, W_, H_
    else:
        x0, y0, x1, y1 = bbox
    x0c, y0c = max(0, int(x0)), max(0, int(y0))
    x1c, y1c = min(W_, int(x1)), min(H_, int(y1))
    if x1c <= x0c or y1c <= y0c:
        return img

    bw, bh = x1c - x0c, y1c - y0c
    rng = np.random.default_rng(_seed(seed) ^ 0x9A17)
    fine = rng.standard_normal((bh, bw)).astype(np.float32)
    broad = fbm(bw, bh, seed=_seed(seed) ^ 0x31, cells=3, octaves=2)
    delta = grain * fine + blotch * broad
    # Round 3: the clip was a hard +-8, which round 2's +-3 sigma only grazed. At
    # grain 5.5 that truncated ~1% of pixels flat and left visible "shelf" pixels
    # where the grain hit the ceiling. Scale the ceiling off the actual sigma
    # instead so raising PAPER_GRAIN/PAPER_BLOTCH never reintroduces banding.
    delta = np.clip(delta, -3.0 * max(grain, blotch), 3.0 * max(grain, blotch))

    region = img.crop((x0c, y0c, x1c, y1c))
    arr = np.asarray(region).astype(np.float32)
    arr[..., :3] = np.clip(arr[..., :3] + delta[..., None], 0.0, 255.0)
    img.paste(Image.fromarray(arr.astype(np.uint8), mode=region.mode),
              (x0c, y0c))
    return img


def paper_page(img, base=None, seed=0, **kw):
    """Fill the whole page with `base` and lay the paper tooth over it."""
    from PIL import ImageDraw as _ID
    W_, H_ = img.size
    _ID.Draw(img).rectangle([0, 0, W_, H_],
                            fill=tuple(base) if base is not None
                            else img.getpixel((0, 0)))
    paper_overlay(img, seed=seed, **kw)
    return img