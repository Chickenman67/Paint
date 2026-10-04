# fomalhautb/_cards.py — segment 10, Fomalhaut b (Dagon), all 14 beats.
#
# The locked palette for this segment lives in PALETTE_SPEC.md; MY_PAL below is
# the single source of truth in code. cardframe.PAL is segment 3's palette — I do
# NOT use it for accents, only for genuinely generic helpers (void_backdrop,
# add_glow, _radial_core, _header, _caption, _draw_stickman, hero_word).
#
# Contract: RENDERERS is keyed by the beat id from script.json; every fn is
# fn(card, planet) -> 1280x720 RGB. No import side effects. Deterministic seeds
# everywhere, no global random state.
#
# THE THREE RULES THIS MODULE EXISTS TO NOT BREAK
#   1. Nothing bone-coloured is drawn on cream. Bone on paper is 1.06:1 — the
#      ice chunks on `the_ring` and `maybe_world` were literally invisible until
#      this was fixed. Cream-card diagram elements are MID or PALE teal.
#   2. The card must actually show what its label says. `the_orbit` and
#      `the_ring` both claim the belt runs off the frame edge, so the drawn
#      geometry now genuinely exceeds 1280 px instead of stopping short.
#   3. A gradient is only ever on the emissive star. Teal `wash`/`ground` fills
#      on cream are FLAT tints, and a flat tint at 40% over paper reads as a
#      thumbprint, not a field.

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# Path bootstrap BEFORE the lib imports: this module lives in
# work/segments/fomalhautb/, so the segment dir, work/segments and work/ must
# all be on sys.path for `import lib.*` to resolve -- whether run directly or
# imported by a frame generator that has not set the path up itself.
_HERE = os.path.dirname(os.path.abspath(__file__))     # .../work/segments/fomalhautb
_SEGMENTS = os.path.dirname(_HERE)                     # .../work/segments
_ROOT = os.path.dirname(_SEGMENTS)                     # .../work  (holds lib/)
for _p in (_HERE, _SEGMENTS, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib.type as T
import lib.ink as K
import lib.cardframe as C
import lib.stickman as S  # noqa: F401  (expressions/poses referenced in docstrings)

W, H = C.W, C.H
TOP = T.ART_TOP                 # 84 — first art row, below the paper title strip
BOT = H                         # 720

# ---------------------------------------------------------------------------
# Locked palette — see PALETTE_SPEC.md §1. 6 locked colours, plus two DERIVED
# teal tints that exist only to make teal readable on cream. The tints are
# arithmetic blends of two locked colours, not new hues, so the segment still
# runs on one discipline.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':    (18, 20, 30),      # #12141E  slate-black — all linework, cream-card type
    'paper':  (243, 236, 219),   # #F3ECDB  bone-cream — cream cards, title strip
    'deep':   (4, 6, 14),        # #04060E  void — every space field
    'amber':  (240, 176, 74),    # #F0B04A  signal amber — the star, captions on deep
    'bone':   (222, 232, 238),   # #DEE8EE  x-ray bone — DEEP cards only
    'teal':   (64, 122, 138),    # #407A8A  cold teal — the belt, the path, VOID cards
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
AMBER = MY_PAL['amber']
BONE = MY_PAL['bone']
TEAL = MY_PAL['teal']


def _tint(base, toward, t):
    """Blend `base` toward `toward` by t. Used only to derive cream-card tints
    from locked colours — a flat tint, never a gradient."""
    return tuple(int(base[k] + (toward[k] - base[k]) * t) for k in range(3))


# Cream-card tints. MID carries drawn linework and chunks on paper; PALE is the
# wash/ground field. Neither is a new hue — both are TEAL walked toward PAPER.
MID = _tint(TEAL, PAPER, 0.45)     # #8AA9B0 — visible on paper, still recessive
PALE = _tint(TEAL, PAPER, 0.78)    # #C3D6D4 — a field, never a line

SEGMENT_PLANET = 'FOMALHAUT b'

# One off-scale type size, used consistently for every subject label that sits
# ON the thing it names. Everything else is T.STAMP_PX or a hero_word. Off-scale
# sizes still go through T.load_font_at, so the family stays locked.
SUB = 20

# The belt, shared by the beats that draw it. The star sits at the ring's CENTRE
# and the ring is deliberately WIDER than the frame (430 +/- 900 = -470..1330)
# so the drawn geometry really does leave both edges — the card admits the belt
# is bigger than the picture.
RING_CX, RING_CY, RING_RX, RING_RY = 430, 404, 900, 176

# The eccentric orbit, shared by the_orbit / one_bad_pass. A real ellipse with
# the star at its left focus: a=620, e=0.75 => c=465, so the centre sits at
# 300+465=765 and the far vertex lands at 765+620=1385, past the right edge.
ORB_CX, ORB_CY, ORB_A, ORB_BY = 765, 424, 620, 252
STAR_X, STAR_Y = 300, 424
CLOSE_X, CLOSE_Y = 145, 424          # the perihelion vertex, near the star


# ---------------------------------------------------------------------------
# Local curve helpers. K's open-curve path is unusable (its Catmull-Rom pad is
# two short and raises IndexError for any polyline of 3+ points), so the open
# path is reconstructed here from the same K.wobble_points engine — the approach
# _cards_b4.py already established.
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    p = list(pts)
    ext = [p[0]] + p + [p[-1]]
    out = []
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(samples):
            t = s / float(samples)
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(p[-1])
    return out


def _open_curve(draw, points, color, width=2, seed=0, wobble=1.2, wavelength=90.0):
    """An OPEN hand-wobbled smooth curve."""
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    if len(pts) < 3:
        draw.line(list(pts), fill=color, width=width)
        return pts
    out = _catmull_open(pts, samples=12)
    draw.line(out, fill=color, width=width, joint='curve')
    return out


def _hrule(draw, y, x0, x1, color, width=2, seed=0, wobble=1.2):
    return _open_curve(draw, [(x0, y), ((x0 + x1) / 2.0, y), (x1, y)], color,
                       width, seed=seed, wobble=wobble, wavelength=90.0)


def _vline(draw, x, y0, y1, color, width=2, seed=0, wobble=1.2):
    return _open_curve(draw, [(x, y0), (x, (y0 + y1) / 2.0), (x, y1)], color,
                       width, seed=seed, wobble=wobble, wavelength=60.0)


def _dash_pts(points, dash=26, gap=18, seed=0, wobble=1.0, wavelength=90.0):
    """Split one open curve into dash SEGMENTS of real points, so the dashes
    still read as one hand-drawn line rather than as a dotted approximation."""
    dense = _catmull_open(K.wobble_points(points, seed=seed, amount=wobble,
                                           wavelength=wavelength), samples=12)
    segs, run, runlen, want, on = [], [], 0.0, dash, True
    for i in range(1, len(dense)):
        run.append(dense[i])
        runlen += math.hypot(dense[i][0] - dense[i - 1][0],
                             dense[i][1] - dense[i - 1][1])
        if on and runlen >= want:
            if len(run) > 1:
                segs.append(list(run))
            run, runlen, want, on = [], 0.0, gap, False
        elif (not on) and runlen >= want:
            run, runlen, want, on = [], 0.0, dash, True
    if on and len(run) > 1:
        segs.append(run)
    return segs


def _dashed(draw, points, color, width, dash=26, gap=18, seed=0, wobble=1.0,
            wavelength=90.0):
    for seg in _dash_pts(points, dash, gap, seed, wobble, wavelength):
        draw.line(seg, fill=color, width=width, joint='curve')


def _tiny(draw, text, x, y, fill, px=None, center=False):
    """Tiny diagram annotation in the locked regular hand. px defaults to the
    locked T.STAMP_PX; SUB for the labels that sit on their subject."""
    font = T.load_font_at(px or T.STAMP_PX, bold=False)
    bb = font.getbbox(text)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(((x - w / 2.0 if center else x) - bb[0], y - bb[1]), text,
              font=font, fill=fill)
    return w, h


def _ellipse_pts(cx, cy, a, by, n=48, a0=0.0, a1=360.0):
    return [(cx + a * math.cos(math.radians(a0 + (a1 - a0) * i / float(n))),
             cy + by * math.sin(math.radians(a0 + (a1 - a0) * i / float(n))))
            for i in range(n + 1)]


# ---------------------------------------------------------------------------
# The star. Two entirely different treatments, because it is drawn in two
# different registers and mixing them is the recurring defect this module is
# guarding against.
# ---------------------------------------------------------------------------

def _star_cream(d, cx, cy, r, seed):
    """Register P: a flat painted disc, thick ink outline, and ONE flat darker
    crescent for form. No gradient, no glow, no light spikes — spikes are a
    Register S signature and they vanish on paper anyway."""
    K.draw_disc(d, cx, cy, r, fill=AMBER, outline=INK, width=K.OUTLINE,
                seed=seed, wobble=2.2)
    K.draw_smooth(d, K.wobble_points(
        [(cx + r * .16, cy - r * .80), (cx + r * .74, cy - r * .34),
         (cx + r * .70, cy + r * .52), (cx + r * .18, cy + r * .82),
         (cx - r * .10, cy + r * .30), (cx - r * .08, cy - r * .40)],
        seed=seed + 1, amount=2.0, wavelength=r),
        fill=_tint(AMBER, INK, 0.22), outline=None, seed=seed + 1,
        wobble=2.0, wavelength=r, closed=True)
    return d


def _halo(img, cx, cy, r, color, strength=70, power=2.3):
    """An additive halo whose intensity falls to EXACTLY zero at the rim.

    ``C.add_glow`` cannot be used here: on a near-black sky its hard circular
    cutoff is plainly visible, and it was drawing a grey disc of radius r*2.1
    with a definite edge around the star — the single most conspicuous artefact
    on the first build's hook card. Here the rim ring is written as 0, so the
    box edge is 0 and the falloff is a smooth power ramp to nothing.
    """
    r, cx, cy = int(r), int(cx), int(cy)
    small = max(12, r // 5)
    mask = Image.new('L', (small * 2, small * 2), 0)
    md = ImageDraw.Draw(mask)
    steps = 40
    for i in range(steps, 0, -1):
        t = i / float(steps)                    # 1 at the rim, ~0 at the centre
        rr = small * t
        md.ellipse([small - rr, small - rr, small + rr, small + rr],
                   fill=int(strength * ((1.0 - t) ** power)))
    mask = mask.filter(ImageFilter.GaussianBlur(small * 0.12))
    mask = mask.resize((r * 2, r * 2), Image.BILINEAR)
    halo = Image.new('RGB', mask.size, color)
    halo = ImageChops.multiply(halo, Image.merge('RGB', (mask, mask, mask)))
    box = (cx - r, cy - r, cx + r, cy + r)
    img.paste(ImageChops.add(img.crop(box).convert('RGB'), halo), (box[0], box[1]))
    return img


def _star_void(img, cx, cy, r, seed, glow=1.0):
    """Register S: the emissive core — the ONE legal gradient in this segment —
    a halo that dies to nothing, and four BLURRED light spikes on their own RGBA
    layer.

    The spikes used to be closed K.draw_smooth polygons, which gave hard polygon
    edges and wobble-spiked tips: they read as a grey crosshair laid over the
    frame, not as light. Blurring the layer is what makes them light.
    """
    C._radial_core(img, int(cx), int(cy), int(r),
                   [(255, 252, 240), AMBER, (176, 106, 40)], glow=0)
    _halo(img, cx, cy, int(r * 3.4), AMBER, strength=int(58 * glow))

    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for k, ang in enumerate((38, 128, 218, 308)):
        a = math.radians(ang)
        L = r * 2.9
        w0, w1 = r * 0.36, r * 0.05
        nx, ny = -math.sin(a), math.cos(a)
        ld.polygon([
            (cx + nx * w0, cy + ny * w0),
            (cx + (L * math.cos(a)) + nx * w1, cy + (L * math.sin(a)) + ny * w1),
            (cx + (L * math.cos(a)) - nx * w1, cy + (L * math.sin(a)) - ny * w1),
            (cx - nx * w0, cy - ny * w0)],
            fill=BONE + (54,))
    lay = lay.filter(ImageFilter.GaussianBlur(max(3, int(r * 0.20))))
    img.paste(Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB'))

    d = ImageDraw.Draw(img, 'RGBA')
    K.stipple(d, cx - r * .85, cy - r * .85, cx + r * .85, cy + r * .85,
              (196, 142, 74), seed=seed, density=0.005, r=1, spread=1)
    return d


# ---------------------------------------------------------------------------
# Fields, the ground band, and the one shared finish.
# ---------------------------------------------------------------------------

def _void(seed, stars=118):
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars)
    return img


def _wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=170.0,
          blur=22):
    """A painterly FLAT region with soft edges. Never a gradient. On cream the
    tint is PALE, never raw TEAL — raw teal at 40% over paper is mud."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    K.draw_smooth(ImageDraw.Draw(lay), points, fill=rgb + (int(alpha),),
                  outline=None, seed=seed, wobble=wobble, wavelength=wavelength,
                  closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _ground_cream(d, y_top, seed=None, x0=-20, x1=None):
    """The cream-card ground: a FLAT PALE teal field with a wobbled top edge,
    always full-bleed from past the left edge to past the right edge.

    It used to be drawn only under the character, which put a hard vertical
    edge at x=980 on every cream card — a saturated CAD-looking blob. A ground
    that runs the whole width of the frame has no such edge."""
    K.draw_ground(d, x0, W + 20 if x1 is None else x1, y_top, H, PALE,
                  seed=int(y_top if seed is None else seed),
                  width=K.HAIRLINE, roughness=3.0)


def _ground_void(d, x0, x1, y_top, alpha=180):
    """The void-card ground band. A dark field is invisible against the void, so
    the band is carried by its bone RULE plus a whisper of stipple below it —
    dense stipple down here read as television static, not ground."""
    K.draw_ground(d, x0, x1, y_top, H, DEEP, seed=int(y_top),
                  width=K.HAIRLINE, roughness=3.0)
    _hrule(d, y_top, max(0, x0), min(W, x1), BONE + (alpha,), width=K.FINE,
           seed=int(y_top) + 1, wobble=1.6)
    K.stipple(d, max(0, x0), y_top + 10, min(W, x1), y_top + 66,
              (30, 38, 56), seed=int(y_top) + 2, density=0.0016, r=1)


def _chunks(d, cx, cy, rx, ry, seed, n=54, color=None, jitter=16, rmin=3,
            rmax=6):
    """Scattered ice chunks riding the belt: small flat discs and small flat
    bars. `color` must be visible on the card's register — BONE on deep, MID on
    cream. Getting this wrong is what made the first build's belt invisible.

    The bar branch used to be a hard `d.rectangle`. At the first build's chunk
    sizes (rmax 8) that read as a small chip, but once the assembly critic
    pushed rmax to 20 for a frame-filling belt, the same rectangle scaled to a
    72x39px slab and the belt read as a row of UI blocks. It is now a wobbly
    hand-drawn shard with an ink outline, and its length is capped independently
    of the disc radius, so raising rmax makes the CHUNKS bigger without turning
    the bars into furniture.
    """
    rnd = random.Random(seed)
    col = color if color is not None else BONE
    for i in range(n):
        a = math.tau * rnd.random()
        px = cx + rx * math.cos(a)
        py = cy + ry * math.sin(a) + rnd.uniform(-jitter, jitter)
        r = rnd.choice([rmin, rmin + 1, rmin + 1, rmax])
        if rnd.random() < 0.30:
            # a shard: long, flat, hand-drawn, and never longer than 26px
            s = min(r * 0.9, 13.0)
            h = s * rnd.uniform(0.34, 0.52)
            K.draw_smooth(
                d, K.wobble_points(
                    [(px - s, py - h), (px + s * .6, py - h * 1.15),
                     (px + s, py + h * .3), (px - s * .5, py + h)],
                    seed=seed + 400 + i, amount=1.6, wavelength=s * 2.4),
                fill=col, outline=INK, width=2, seed=seed + 400 + i,
                wobble=1.2, wavelength=s * 2.4, closed=True)
        else:
            d.ellipse([px - r, py - r * .8, px + r, py + r * .8], fill=col)


def _blob(d, cx, cy, seed, scale=1.0):
    """The faint thing inside the ring: a cluster of overlapping FLAT discs, so
    it stays deliberately un-emissive. This is the object the whole segment is
    about, so it is drawn the same way on every card that shows it."""
    for r, a in ((30 * scale, 62), (20 * scale, 100), (12 * scale, 150),
                 (6 * scale, 210)):
        d.ellipse([cx - r, cy - r * .92, cx + r, cy + r * .92],
                  fill=BONE + (a,))
    return d


def _pickout(d, cx, cy, r, seed, color=None, width=None):
    """The hand-drawn circle that picks the blob out of the dark."""
    K.draw_disc(d, cx, cy, r, fill=None, outline=color or AMBER,
                width=width or K.DETAIL, seed=seed, wobble=1.8)


def _sm(horizon, x, height, pose, expression):
    """A stickman spec whose FEET LAND EXACTLY ON the horizon. Sizing a figure
    by y_top and hoping it meets the ground is how the first build left him
    hovering 10px above the line he was supposed to be standing on."""
    return dict(pose=pose, expression=expression, x_center=int(x),
                y_top=int(horizon) - int(height), height=int(height))


def _finish(img, card, planet, dark_bg):
    """Layout-A tail, identical on every card: title strip, then the schedule's
    character in the right theme, then the one floating caption."""
    C._header(img, planet, paper_band=dark_bg)
    C._draw_stickman(img, card, theme='dark' if dark_bg else 'light')
    C._caption(img, card['caption'], 70, 652, dark_bg=dark_bg)
    return img


# ---------------------------------------------------------------------------
# B1 HOOK — the brightest star in the autumn sky. VOID + character.
# ---------------------------------------------------------------------------

def render_hook_brightest_star(card, planet=SEGMENT_PLANET):
    """B1/1 — VOID. One hot amber star upper-left, blurred bone spikes, real
    additive halo: the only light in frame. AUTUMN / BRIGHTEST-1 carry the
    superlative in type, placed clear of the character. The character stands at
    frame right on a bone horizon, feet on it, flat/deadpan, looking up."""
    img = _void(101, stars=132)
    d = _star_void(img, 300, 262, 70, seed=101, glow=1.15)

    d = ImageDraw.Draw(img)
    _ground_void(d, -20, W + 20, 598)

    # type, in the free span between the star's halo and the figure
    C.hero_word(d, 'BRIGHTEST-1', 700, 262, BONE, px=56, y_max=344)
    _tiny(d, 'IN THE AUTUMN SKY', 700, 336, BONE, px=SUB, center=True)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B2 SETUP — the ring. CREAM + character.
# ---------------------------------------------------------------------------

def render_the_ring(card, planet=SEGMENT_PLANET):
    """B2/2 — CREAM, Register P, one subject: the belt. A flat amber star at the
    ring's CENTRE, encircled by a flat oval of MID-teal ice chunks wide enough
    that its geometry leaves both frame edges (430 +/- 900 = -470..1330), so the
    frame admits the belt is bigger than the picture. The character stands on a
    full-bleed PALE ground, shrugging flat — too wide to be a planet's ring.

    SCALE, from the assembly critic (p07, round 1). At the first build the star
    was r=46 and the chunks were 4-8px dots, so the whole card read as a small
    tan coin in a large empty cream field with a thin dashed line across it —
    the under-filled-frame failure. The reference fills its frame with the
    subject; ours was using about a tenth of the width on the one thing the
    card is about. The star is now r=150 (300px across, ~23% of frame width)
    and the chunks are 9-20px, which is what makes the belt read as a belt
    rather than as a dotted rule.
    """
    img = _cream_field(RING_CX, RING_CY, seed=201)
    d = ImageDraw.Draw(img)
    _star_cream(d, RING_CX, RING_CY, 150, seed=202)
    d = ImageDraw.Draw(img)
    _chunks(d, RING_CX, RING_CY, RING_RX, RING_RY, seed=203, n=150,
            color=MID, jitter=14, rmin=9, rmax=20)
    _ground_cream(d, 590)
    d = ImageDraw.Draw(img)
    _tiny(d, 'THE BELT RUNS OFF FRAME', RING_CX, 626, INK, px=SUB, center=True)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


def _cream_field(cx, cy, seed, extent=(0.10, 0.86, 1.30, 0.62)):
    """A cream card with one soft PALE field behind the diagram — wide, flat and
    recessive, so it reads as a stage for the subject rather than a smudge.
    The alpha is deliberately low: PALE teal stacked on cream and then blurred
    turns grey-green fast, and a grey-green thumbprint is worse than no field."""
    img = Image.new('RGB', (W, H), PAPER)
    ex0, ey0, ex1, ey1 = extent
    return _wash(img,
                 [(cx + (ex0 - .5) * W, cy + (ey0 - .5) * H),
                  (cx + (ex1 - .5) * W * .5, cy + (ey0 - .5) * H * .72),
                  (cx + (ex1 - .5) * W, cy + (ey1 - .5) * H * .78),
                  (cx + (ex1 - .5) * W * .5, cy + (ey1 - .5) * H),
                  (cx + (ex0 - .5) * W * .5, cy + (ey1 - .5) * H * .74)],
                 PALE, 86, seed=seed, wobble=16.0, blur=40)


# ---------------------------------------------------------------------------
# B3 REVEAL — light in the ring. VOID + character.
# ---------------------------------------------------------------------------

def render_light_in_the_ring(card, planet=SEGMENT_PLANET):
    """B3/3 — VOID. At the belt's edge: the amber limb of the star clipped by the
    LEFT frame edge, a bone arc sweeping across as the near edge of the ring,
    and one small fuzzy blob sitting ON that arc, picked out by a hand-drawn
    amber circle with a thin leader running to a label. The blob is a cluster of
    flat discs, never emissive — the whole point is that it is faint."""
    img = _void(301, stars=104)
    d = _star_void(img, 74, 404, 84, seed=302, glow=1.0)

    # the near edge of the ring, as one smooth bone arc across the whole frame
    arc = [(x, 452 + 150 * math.sin(math.radians(194 + 152 * (x - 20) / 1260.0)))
           for x in range(20, 1301, 30)]
    d = ImageDraw.Draw(img)
    _open_curve(d, arc, BONE + (210,), width=K.DETAIL, seed=303, wobble=1.4,
                wavelength=200.0)
    _chunks(d, 660, 452, 560, 118, seed=304, n=34, color=BONE, jitter=8,
            rmin=3, rmax=5)

    # THE BLOB, on the arc, picked out
    bx, by = 792, 456
    _blob(d, bx, by, seed=310, scale=1.0)
    _pickout(d, bx, by, 48, seed=314)
    _open_curve(d, [(bx + 44, by - 28), (bx + 116, by - 96), (bx + 168, by - 124)],
                AMBER, width=K.FINE, seed=315, wobble=1.0, wavelength=70.0)
    _tiny(d, 'SOMETHING IN HERE', bx + 176, by - 132, BONE, px=SUB)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B4 REVEAL2 — first planet. CREAM + character.
# ---------------------------------------------------------------------------

def render_first_visible_planet(card, planet=SEGMENT_PLANET):
    """B4/4 — CREAM. The beat's word IS the subject: FIRST PLANET stamped large
    in ink with a paper keyline over a soft PALE field, underlined by a hand rule.
    A drawn telescope at lower left points up-right at one small INK dot, with
    its label immediately beside it. The character stands at the right margin,
    hands up, awed."""
    img = _cream_field(560, 300, seed=401, extent=(0.06, 0.20, 0.94, 0.90))
    d = ImageDraw.Draw(img)

    C.hero_word(d, 'FIRST PLANET', 640, 214, INK, stroke_rgb=PAPER, px=64,
                y_max=286)
    _hrule(d, 272, 250, 1030, AMBER, width=K.DETAIL, seed=410, wobble=1.6)

    # the telescope, and the dot it found
    ax, ay, tx, ty = 306, 520, 380, 428
    _open_curve(d, [(ax, ay), (tx, ty)], INK, width=K.OUTLINE, seed=402,
                wobble=1.0, wavelength=60.0)
    _open_curve(d, [(ax + 15, ay - 11), (tx + 15, ty - 11)], AMBER,
                width=K.DETAIL, seed=403, wobble=1.0, wavelength=60.0)
    for k, leg in enumerate(((ax - 26, 596), (ax + 38, 596), (ax + 6, 604))):
        _open_curve(d, [(ax + 4, ay + 20), leg], INK, width=K.DETAIL,
                    seed=404 + k, wobble=0.8, wavelength=50.0)
    dx, dy = tx + 138, ty - 100
    K.draw_disc(d, dx, dy, 14, fill=INK, outline=INK, width=K.FINE,
                seed=409, wobble=1.2)
    _tiny(d, 'NOT OUR SUN', dx + 28, dy - 10, INK, px=SUB)

    _ground_cream(d, 574)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


# ---------------------------------------------------------------------------
# B5 TURN — the headline. VOID + character.
# ---------------------------------------------------------------------------

def render_the_headline(card, planet=SEGMENT_PLANET):
    """B5/5 — VOID. The blob alone at centre-left inside its amber pick-out ring,
    the leader running down-left to a label: THAT WAS THE HEADLINE. The
    character stands at frame right, feet on the horizon, flat deadpan, facing it
    across empty space. The beat is the pause, so the card is mostly void and the
    figure is small inside it."""
    img = _void(501, stars=112)
    d = ImageDraw.Draw(img)
    _ground_void(d, -20, W + 20, 600, alpha=170)

    bx, by = 430, 392
    _blob(d, bx, by, seed=504, scale=1.05)
    _pickout(d, bx, by, 54, seed=508)
    _open_curve(d, [(bx - 50, by + 28), (bx - 126, by + 98), (bx - 172, by + 140)],
                AMBER, width=K.FINE, seed=509, wobble=1.0, wavelength=70.0)
    _tiny(d, 'THAT WAS THE HEADLINE', bx - 176, by + 158, BONE, px=SUB)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B6 DOUBT — the same blob as a smudge. CREAM + character.
# ---------------------------------------------------------------------------

def render_not_the_end(card, planet=SEGMENT_PLANET):
    """B6/6 — CREAM. The blob redrawn as a shapeless smudge, and the smudge is
    built the way a smudge actually looks: a cluster of low-alpha GREY ellipses
    on their own layer, blurred, with no hard rim anywhere. Drawn straight onto
    the card in flat teal it read as a stack of opaque stickers, which is the
    opposite of the doubt this beat is about. A bracket-framed region marks it
    and ONE solid ink dot sits inside where the pick-out ring used to be. The
    character is dark on cream, shrugging with a zigzag mouth — asking, not
    telling."""
    img = Image.new('RGB', (W, H), PAPER)

    # the smudge: soft, shapeless, deliberately formless. Grey, not teal.
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    rnd = random.Random(601)
    grey = _tint(INK, PAPER, 0.42)
    for _ in range(30):
        px = 496 + rnd.uniform(-150, 150)
        py = 410 + rnd.uniform(-80, 80)
        rx = rnd.uniform(30, 84)
        ry = rx * rnd.uniform(0.44, 0.70)
        ld.ellipse([px - rx, py - ry, px + rx, py + ry],
                   fill=grey + (rnd.randint(26, 54),))
    lay = lay.filter(ImageFilter.GaussianBlur(11))
    img.paste(Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB'))

    d = ImageDraw.Draw(img)
    K.draw_disc(d, 496, 414, 11, fill=INK, outline=INK, width=K.FINE,
                seed=602, wobble=1.0)

    # corner brackets around the region
    bx0, by0, bx1, by1 = 286, 288, 706, 548
    for k, pts in enumerate((((bx0, by0 + 46), (bx0, by0), (bx0 + 46, by0)),
                             ((bx1 - 46, by0), (bx1, by0), (bx1, by0 + 46)),
                             ((bx0, by1 - 46), (bx0, by1), (bx0 + 46, by1)),
                             ((bx1 - 46, by1), (bx1, by1), (bx1, by1 - 46)))):
        _open_curve(d, list(pts), INK, width=K.DETAIL, seed=603 + k, wobble=0.8,
                    wavelength=50.0)
    _tiny(d, 'SAME REGION', bx0 + 4, by0 - 28, INK, px=SUB)
    _tiny(d, 'SOME CALL IT A CLOUD', bx0 + 4, by1 + 14, INK, px=SUB)

    _ground_cream(d, 596)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


# ---------------------------------------------------------------------------
# B7 HYPOTHESIS_A — dust. VOID + character.
# ---------------------------------------------------------------------------

def render_maybe_dust(card, planet=SEGMENT_PLANET):
    """B7/7 — VOID. A dashed teal path crosses the frame down-right; where it
    meets the bone ring arc there is a bulge of pale flat dust, the one
    non-emissive cloud in the segment. The path continues off the right edge, so
    the intruder is on its way OUT. Labels sit on their subjects. The character
    stands at frame left, feet on the horizon, flat, watching it leave."""
    img = _void(701, stars=126)
    d = ImageDraw.Draw(img)
    _ground_void(d, -20, W + 20, 604, alpha=150)

    arc = [(x, 400 + 94 * math.sin(math.radians(190 + 158 * (x - 20) / 1260.0)))
           for x in range(20, 1301, 30)]
    _open_curve(d, arc, BONE + (185,), width=K.DETAIL, seed=704, wobble=1.4,
                wavelength=200.0)
    _chunks(d, 660, 400, 560, 92, seed=705, n=36, color=BONE, jitter=7,
            rmin=3, rmax=5)

    # the dust bulge where the path meets the ring — soft, like everything else
    # that is dust in this segment
    bx, by = 828, 398
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for r, ry, a in ((96, 40, 20), (70, 30, 30), (46, 20, 44), (24, 11, 66)):
        ld.ellipse([bx - r, by - ry, bx + r, by + ry], fill=BONE + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(7))
    img.paste(Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB'))
    _tiny(d, 'DUST', bx + 108, by - 44, BONE, px=SUB)

    # the path: long dashes so it reads as ONE trajectory rather than as a
    # scatter of tick marks, and it leaves the right edge
    _dashed(d, [(30, 190), (300, 250), (560, 312), (828, 392), (1080, 448),
                (1310, 506)], TEAL, K.DETAIL, dash=54, gap=28, seed=707,
            wobble=1.6, wavelength=170.0)
    _tiny(d, 'PATH IN', 108, 178, BONE, px=SUB)
    _tiny(d, 'ON ITS WAY OUT', 1010, 528, BONE, px=SUB)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B8 HYPOTHESIS_B — a real world. CREAM + character.
# ---------------------------------------------------------------------------

def render_maybe_world(card, planet=SEGMENT_PLANET):
    """B8/8 — CREAM. The competing reading: one flat amber world at centre with a
    ring of MID ice chunks tidied into an oval AROUND it, and three curved amber
    arrows showing that oval being pulled into shape. Gravity shepherding the
    belt, in one picture. The character stands at the right margin, considering
    it."""
    img = _cream_field(500, 424, seed=801)
    d = ImageDraw.Draw(img)

    cx, cy = 470, 424
    _chunks(d, cx, cy, 300, 120, seed=802, n=54, color=MID, jitter=5,
            rmin=4, rmax=7)
    _star_cream(d, cx, cy, 72, seed=803)   # the world: flat amber + ink outline
    d = ImageDraw.Draw(img)
    _tiny(d, 'A REAL WORLD', cx, cy + 92, INK, px=SUB, center=True)

    # three curved arrows pulling the belt into the tidied oval
    for k, (a0, a1, rr) in enumerate(((198, 252, 348), (300, 346, 340),
                                      (26, 76, 344))):
        pts = _ellipse_pts(cx, cy, rr, rr * .40, n=9, a0=a0, a1=a1)
        _open_curve(d, pts, AMBER, width=K.DETAIL, seed=810 + k, wobble=1.0,
                    wavelength=110.0)
        hx, hy = pts[-1]
        d.polygon([(hx + 16, hy), (hx - 6, hy - 11), (hx - 6, hy + 11)], fill=AMBER)
    _tiny(d, 'IT HOLDS THE BELT', 500, 600, INK, px=SUB, center=True)

    _ground_cream(d, 566)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


# ---------------------------------------------------------------------------
# B9 PARADOX — two identical frames. VOID + character.
# ---------------------------------------------------------------------------

def render_two_things_same_pixels(card, planet=SEGMENT_PLANET):
    """B9/9 — VOID. ONE data frame shown twice, byte-identical: same chunk
    offsets, same blob, same seeds. That sameness IS the beat, so it is drawn
    rather than said. Under the left a bone label: A CLOUD. Under the right, in
    amber: A WORLD. The character stands between them, feet on the horizon, hands
    up and mouth a wide oval — two pictures he cannot tell apart."""
    img = _void(901, stars=96)
    d = ImageDraw.Draw(img)
    _ground_void(d, -20, W + 20, 606, alpha=150)

    for px0 in (176, 704):
        seed = 910                      # THE SAME SEED — the two frames are one frame
        fx0, fy0, fx1, fy1 = px0, 150, px0 + 400, 452
        K.draw_smooth(d, [(fx0 + 40, fy0), (fx1 - 40, fy0), (fx1, fy0 + 40),
                          (fx1, fy1 - 40), (fx1 - 40, fy1), (fx0 + 40, fy1),
                          (fx0, fy1 - 40), (fx0, fy0 + 40)],
                      fill=None, outline=BONE, width=K.DETAIL, seed=seed,
                      wobble=1.2, wavelength=160.0, closed=True)
        _chunks(d, px0 + 200, 300, 168, 124, seed=seed + 1, n=15, color=BONE,
                jitter=5, rmin=3, rmax=5)
        _blob(d, px0 + 200, 300, seed=seed + 2, scale=0.66)
        _tiny(d, '2008', fx0 + 4, fy0 - 28, BONE, px=SUB)

    _tiny(d, 'A CLOUD', 376, 496, BONE, px=SUB, center=True)
    _tiny(d, 'A WORLD', 904, 496, AMBER, px=SUB, center=True)
    _hrule(d, 518, 262, 490, BONE, width=K.FINE, seed=905, wobble=1.2)
    _hrule(d, 518, 790, 1018, AMBER, width=K.FINE, seed=906, wobble=1.2)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B10 ORBIT — the wild ellipse. CREAM + character.
# ---------------------------------------------------------------------------

def render_the_orbit(card, planet=SEGMENT_PLANET):
    """B10/10 — CREAM. The orbit drawn as a real eccentric ellipse with the star
    at its LEFT FOCUS: the loop dives to a CLOSE PASS on the star, then its far
    vertex lands at x=1385, past the right edge, so 'far out into the cold' is a
    fact about the frame rather than a claim about the drawing. The character
    stands at frame right on a PALE band, flat, watching it leave."""
    img = _cream_field(430, 424, seed=1001)
    d = ImageDraw.Draw(img)

    _star_cream(d, STAR_X, STAR_Y, 40, seed=1002)
    d = ImageDraw.Draw(img)
    _open_curve(d, _ellipse_pts(ORB_CX, ORB_CY, ORB_A, ORB_BY, n=48), INK,
                width=K.OUTLINE, seed=1003, wobble=2.4, wavelength=280.0)

    # the close pass, ON the dive, with its tick and label
    _vline(d, CLOSE_X, CLOSE_Y - 36, CLOSE_Y + 36, AMBER, width=K.DETAIL,
           seed=1004, wobble=0.8)
    _tiny(d, 'CLOSE PASS', CLOSE_X + 22, CLOSE_Y - 58, INK, px=SUB)

    # the far end, escaped past the frame edge (kept clear of the figure's head)
    _tiny(d, 'FAR OUT', 1168, 232, INK, px=SUB, center=True)
    _open_curve(d, [(1170, 254), (1206, 264), (1244, 272)], INK, width=K.FINE,
                seed=1006, wobble=0.8, wavelength=50.0)

    _ground_cream(d, 566)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


# ---------------------------------------------------------------------------
# B11 ORBIT_BAD — the ellipse frays. VOID, no character.
# ---------------------------------------------------------------------------

def render_orbit_not_tidy(card, planet=SEGMENT_PLANET):
    """B11/11 — DIAGRAM ONLY, no character. The same ellipse as the_orbit drawn
    three times at rising wobble amplitude and alpha, so the line visibly comes
    off registration as it swings wide — a pencil line losing its way. The amber
    core and its glow stay at the focus, so the loop still has something to swing
    around. One label."""
    img = _void(1101, stars=104)
    d = _star_void(img, 300, 424, 32, seed=1100, glow=0.9)

    for amp, alpha, wd, sd in ((2.0, 90, K.DETAIL, 1102),
                               (7.0, 150, K.DETAIL, 1103),
                               (17.0, 235, K.OUTLINE, 1104)):
        _open_curve(d, _ellipse_pts(300, 424, 470, 190, n=44), BONE + (alpha,),
                    width=wd, seed=sd, wobble=amp,
                    wavelength=280.0 if sd == 1102 else 120.0)

    C.hero_word(d, 'NOT TIDY', 920, 372, BONE, px=64, y_max=470)
    _tiny(d, 'IT COMES BACK OFF REGISTRATION', 920, 452, BONE, px=SUB,
          center=True)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B12 WARNING — one bad pass. CREAM + character.
# ---------------------------------------------------------------------------

def render_one_bad_pass(card, planet=SEGMENT_PLANET):
    """B12/12 — CREAM. The warning beat. The same loop as the_orbit, but the
    planet dot is drawn ONLY at the close pass — flashing there inside an amber
    ring — and ABSENT from the rest of the loop, where a hollow ghost dot marks
    the place it should have been. The character at frame right shrugs flat: he
    does not know either."""
    img = _cream_field(430, 424, seed=1201)
    d = ImageDraw.Draw(img)

    _star_cream(d, STAR_X, STAR_Y, 40, seed=1202)
    d = ImageDraw.Draw(img)
    _open_curve(d, _ellipse_pts(ORB_CX, ORB_CY, ORB_A, ORB_BY, n=48), INK,
                width=K.OUTLINE, seed=1203, wobble=2.4, wavelength=280.0)

    # the ghost: a point on the loop where the dot is NOT. Placed at the TOP of
    # the ellipse, on the curve and well clear of the figure — at the far right
    # it used to land square on the character's head.
    gx, gy = 766, 174
    K.draw_disc(d, gx, gy, 18, fill=None, outline=MID, width=K.DETAIL,
                seed=1204, wobble=1.2)
    _hrule(d, gy + 32, gx - 44, gx + 44, MID, width=K.FINE, seed=1205, wobble=0.8)
    _tiny(d, 'NOT ON THE LOOP', gx, gy + 46, INK, px=SUB, center=True)

    # the one place it IS
    K.draw_disc(d, CLOSE_X, CLOSE_Y, 18, fill=INK, outline=AMBER,
                width=K.OUTLINE, seed=1206, wobble=1.2)
    _tiny(d, 'ONE BAD PASS', CLOSE_X + 24, CLOSE_Y - 60, INK, px=SUB)

    _ground_cream(d, 566)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


# ---------------------------------------------------------------------------
# B13 FATE — the long fall. VOID + character.
# ---------------------------------------------------------------------------

def render_the_long_fall(card, planet=SEGMENT_PLANET):
    """B13/13 — VOID, and the fate beat (CLAUDE.md §10.8): the character is IN
    frame, small, feet on a bone horizon at frame left, mouth a small awed oval,
    watching. The system is small in the upper right — amber core plus its belt —
    and ONE bone dot trails a long thin line off the right edge into empty
    black. There is nothing left to catch it."""
    img = _void(1301, stars=136)
    d = ImageDraw.Draw(img)

    sx, sy, sr = 946, 210, 22
    d = _star_void(img, sx, sy, sr, seed=1300, glow=0.8)
    d = ImageDraw.Draw(img)
    _open_curve(d, _ellipse_pts(sx, sy, 92, 24, n=34), BONE + (185,),
                width=K.FINE, seed=1302, wobble=1.0, wavelength=90.0)

    # the fall: one bone dot, and the long thin line it is leaving on
    fx, fy = sx + 222, sy + 36
    for r, a in ((9, 235), (17, 68), (27, 24)):
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=BONE + (a,))
    _open_curve(d, [(fx, fy), (fx + 78, fy + 16), (fx + 152, fy + 28)],
                BONE + (225,), width=K.DETAIL, seed=1303, wobble=1.0,
                wavelength=120.0)
    _open_curve(d, [(fx + 162, fy + 30), (fx + 224, fy + 42), (fx + 286, fy + 52)],
                BONE + (115,), width=K.FINE, seed=1304, wobble=1.0, wavelength=90.0)
    _tiny(d, 'OUT OF FRAME', fx + 128, fy - 46, BONE, px=SUB)

    _ground_void(d, -20, 520, 604, alpha=170)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=True)


# ---------------------------------------------------------------------------
# B14 CLOSE — cloud, world, gone. CREAM + character.
# ---------------------------------------------------------------------------

def _left_word(draw, text, x, cy, fill, stroke_rgb, px=64):
    """A hero-scale word anchored at its LEFT edge — this stack reads top to
    bottom, so its words are not centred. Clamped so the 3px keyline always
    stays on-screen and below the title strip."""
    font = T.load_font_at(px, bold=True)
    bb = font.getbbox(text)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    pad = 3 * 2 + 2
    y = max(TOP + 40, min(H - 120 - h - pad, int(cy - h / 2)))
    x = max(40, min(W - 200 - w - pad, int(x)))
    T.draw_outlined_text(draw, (x - bb[0], y - bb[1]), text, font, fill=fill,
                         stroke=stroke_rgb, stroke_width=3)
    return w


def render_cloud_world_or_gone(card, planet=SEGMENT_PLANET):
    """B14/14 — CREAM. The close, as three wobbly underlined words stacked down
    the LEFT: CLOUD, WORLD, GONE. The middle word is amber with an ink keyline —
    it is the one the beat is about; the outer two are ink. Each word carries its
    own hand-drawn underline, set clear of the glyphs. The character stands beside
    them, flat deadpan. No hero_word: the three words ARE the card, and stacking
    them is the reference's own closing device."""
    img = _cream_field(300, 380, seed=1401, extent=(0.04, 0.28, 0.56, 0.94))
    d = ImageDraw.Draw(img)

    for label, y, col, key in (('CLOUD', 232, INK, INK),
                               ('WORLD', 358, AMBER, INK),
                               ('GONE', 484, INK, INK)):
        w = _left_word(d, label, 104, y, col, key)
        # the underline, 22px clear of the glyph bottom so it never touches
        _hrule(d, y + 46, 104, 104 + w, AMBER if label == 'WORLD' else INK,
               width=K.DETAIL, seed=1410 + y, wobble=1.8)

    _ground_cream(d, 566)
    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, dark_bg=False)


# ---------------------------------------------------------------------------
# Dispatch — one key per beat id in script.json, all 14.
# ---------------------------------------------------------------------------

RENDERERS = {
    'hook_brightest_star': render_hook_brightest_star,
    'the_ring': render_the_ring,
    'light_in_the_ring': render_light_in_the_ring,
    'first_visible_planet': render_first_visible_planet,
    'the_headline': render_the_headline,
    'not_the_end': render_not_the_end,
    'maybe_dust': render_maybe_dust,
    'maybe_world': render_maybe_world,
    'two_things_same_pixels': render_two_things_same_pixels,
    'the_orbit': render_the_orbit,
    'orbit_not_tidy': render_orbit_not_tidy,
    'one_bad_pass': render_one_bad_pass,
    'the_long_fall': render_the_long_fall,
    'cloud_world_or_gone': render_cloud_world_or_gone,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table."""
    C.register(mapping if mapping is not None else RENDERERS)
    return RENDERERS


# ---------------------------------------------------------------------------
# Self-test. Renders every beat to cardsheet/beat_<NN>.png, one line per beat.
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import json

    with open(os.path.join(_HERE, 'script.json'), 'r', encoding='utf-8') as fh:
        SCRIPT = json.load(fh)

    OUT = os.path.join(_HERE, 'cardsheet')
    os.makedirs(OUT, exist_ok=True)

    # beat id -> (self-test caption, stickman spec or None). The specs use the
    # same _sm() feet-on-horizon rule the renderers' own geometry implies.
    SELF = {
        'hook_brightest_star': ('THE BRIGHTEST STAR IN THE SKY',
                                _sm(598, 1122, 280, 'standing', 'flat')),
        'the_ring': ('A RING OF ICE, WAY OUT THERE',
                     _sm(566, 1122, 260, 'shrugged', 'flat')),
        'light_in_the_ring': ('SOMETHING IN THERE CAUGHT THE LIGHT',
                              _sm(618, 1080, 254, 'pointing', 'awed_brows')),
        'first_visible_planet': ('THE FIRST ONE EVER IMAGED',
                                 _sm(574, 1116, 264, 'hands_up', 'oval')),
        'the_headline': ('THE WHOLE FIELD SAT BACK',
                         _sm(600, 1000, 250, 'standing', 'flat')),
        'not_the_end': ('SOME CALL IT A DUST CLOUD',
                        _sm(596, 1120, 258, 'shrugged', 'zigzag')),
        'maybe_dust': ('JUST DUST, KICKED UP ON THE WAY OUT',
                       _sm(604, 214, 246, 'standing', 'flat')),
        'maybe_world': ('A WORLD, HOLDING THE BELT IN ITS GRAVITY',
                        _sm(566, 1108, 262, 'thinker', 'flat')),
        'two_things_same_pixels': ('TWO THINGS. ONE PICTURE.',
                                   _sm(606, 640, 232, 'hands_up', 'oval')),
        'the_orbit': ('CLOSE IN, THEN THROWN FAR OUT',
                      _sm(566, 1122, 258, 'shrugged', 'flat')),
        'orbit_not_tidy': ('AN ELLIPSE THAT WILD DOES NOT LAST', None),
        'one_bad_pass': ('ONE BAD PASS AND IT NEVER COMES BACK',
                         _sm(566, 1112, 256, 'shrugged', 'flat')),
        'the_long_fall': ('NOTHING LEFT TO CATCH IT',
                          _sm(604, 226, 238, 'pointing', 'oval')),
        'cloud_world_or_gone': ('MAYBE A CLOUD. MAYBE A WORLD.',
                                _sm(566, 1100, 262, 'hands_up', 'flat')),
    }

    register()   # merge into cardframe's dispatch table so C.render resolves

    beats = SCRIPT['beats']
    missing = [b['id'] for b in beats if b['id'] not in RENDERERS]
    if missing:
        raise SystemExit('no renderer for beat id(s): %s' % ', '.join(missing))
    extra = [k for k in RENDERERS if k not in {b['id'] for b in beats}]
    if extra:
        raise SystemExit('renderer(s) with no beat in script.json: %s'
                         % ', '.join(sorted(extra)))

    for b in beats:
        bid = b['id']
        caption, sm = SELF[bid]
        img = C.render({'id': bid, 'caption': caption, 'stickman': sm},
                       SEGMENT_PLANET)
        if img.size != (W, H) or img.mode != 'RGB':
            raise SystemExit('%s rendered %s/%s, expected 1280x720/RGB'
                             % (bid, img.size, img.mode))
        name = 'beat_%02d.png' % b['n']
        img.save(os.path.join(OUT, name))
        print('beat %2d  %-26s %-5s  stickman:%s  -> %s'
              % (b['n'], bid, b['register'], 'yes' if sm else 'no ', name))

    print('OK  %d beats rendered to %s' % (len(beats), OUT))
