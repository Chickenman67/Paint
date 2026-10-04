# work/segments/psrb1257/_cards_b1.py — B1 HOOK card renderers.
#
# Beat: "Here is a star that has already died. / It is still spinning, and it is
# still talking. / And it is not spinning alone. A neutron star."
#
# All three cards are VOID (Register S): near-black sky, one emissive body at
# (980, 300) r=46, the character at the schedule's own x/y/height/pose/expression.
# Continuity of the star's position across the three cards is deliberate — it is
# the same object, annotated three ways (dead -> talking -> named).
#
# Register discipline (PALETTE_SPEC §3): the ONLY gradient is C._radial_core on
# the pulsar core. Halo rings, radio arcs, the limb ring, the nebula wisp and the
# starfield are all FLAT fills at low alpha. No body gets a black outline. Nothing
# here is tweened; the quantized 0.25 s stamp variants are layered on by the frame
# generator as small variations of these stills.
#
# Determinism: every wobble / stipple / starfield call takes an explicit seed.
# No global random state, so re-renders are byte-identical.

import math
import random

from PIL import Image, ImageDraw

import lib.type as T
import lib.ink as K
import lib.cardframe as C


# The pulsar core — same on every card in the beat. The gradient here is the one
# legal gradient in the segment.
STAR_CX, STAR_CY, STAR_R = 980, 300, 46


# ---------------------------------------------------------------------------
# Shared helpers (private to this beat module; no lib constants re-derived)
# ---------------------------------------------------------------------------

def _void_field(img, seed, stars=130):
    """Register-S space field. A distinct seed per card so the three starfields in
    the beat are not literally the same frame with the same stars."""
    return C.void_backdrop(img, seed=seed, stars=stars)


def _pulsar_core(img, cx, cy, r, seed, grain=0.03):
    """The emissive core: a 3-stop radial gradient (the only legal gradient in this
    segment) plus a light deterministic stipple so it keeps the spray-paint grain
    instead of reading as a clean CG ramp (PALETTE_SPEC §3)."""
    C._radial_core(img, cx, cy, r, [(255, 255, 255), C.PAL['bone'], (60, 52, 92)])
    d = ImageDraw.Draw(img, 'RGBA')
    K.stipple(d, cx - r * 0.95, cy - r * 0.95, cx + r * 0.95, cy + r * 0.95,
              (86, 74, 122), seed=seed, density=grain, r=1, spread=1)
    return d


def _flat_ring(draw, cx, cy, r, color, alpha, width):
    """A FLAT concentric ring (no gradient) — the magnetic halo, or the limb ring."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=color + (alpha,), width=width)


def _stroke_band(pts, width):
    """Turn an open polyline into a CLOSED polygon of the given stroke width by
    offsetting perpendicular to the path.

    This exists because ``K.draw_outline(..., closed=False)`` cannot be used: it
    routes to ``lib.ink._smooth_open``, whose Catmull-Rom extension buffer is two
    elements short and raises IndexError for any polyline of 3 or more points
    (inherited here from lib/ink.py:114, not editable from a beat module). Running
    the same wobble + Catmull-Rom through the CLOSED path -- which does work --
    gives the identical low-frequency hand curve, as a flat filled band instead of
    a stroked one. Filled, not gradient, and outline=None, so it stays Register S
    with no black edge on a space element.
    """
    h = width / 2.0
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        m = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / m, dx / m
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    return left + right[::-1]


def _draw_band(draw, pts, width, color, alpha, seed, wobble=1.2, wavelength=190.0):
    """A flat-alpha stroke of an open path, drawn through K.draw_smooth."""
    K.draw_smooth(draw, _stroke_band(pts, width), fill=color + (alpha,),
                  outline=None, seed=seed, wobble=wobble, wavelength=wavelength)


def _arc_pts(cx, cy, r, a0_deg, a1_deg, n=72):
    """Sample a circular arc. PIL angles: 0 = 3 o'clock, increasing clockwise
    (y grows downward), so 180 = 9 o'clock (screen-left)."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _radio_arc(draw, cx, cy, r, a0, a1, color, alpha, width, seed):
    """A radio-emission arc: a smooth, low-frequency-wobbled curve at a flat
    alpha. Opening left (128..232 deg) so the beam points at the character, who
    stands at x=400."""
    _draw_band(draw, _arc_pts(cx, cy, r, a0, a1), width, color, alpha, seed,
               wobble=1.4, wavelength=190.0)


def _meridian_tick(draw, cx, cy, r, angle_deg, seed):
    """The spin indicator: ONE meridian tick on the star limb. The frame generator
    advances angle_deg by 90 deg per 0.25 s stamp (4 stamps per revolution); this
    still is stamp 0. Faint slate on the bright core inside, bright bone on the
    limb so it actually reads against the core."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    inner, outer = [], []
    for i in range(5):
        t = 0.12 + (0.99 - 0.12) * i / 4.0
        px, py = cx + r * t * ca, cy + r * t * sa
        inner.append((px, py))
    _draw_band(draw, inner, 3, C.PAL['ink'], 115, seed, wobble=0.9, wavelength=60.0)
    # the tick head, straddling the limb
    lx, ly = cx + r * 0.99 * ca, cy + r * 0.99 * sa
    draw.ellipse([lx - 5, ly - 5, lx + 5, ly + 5], fill=C.PAL['bone'] + (235,))


# Where the banner word is stamped. The pulsar core sits at (STAR_CX, STAR_CY)
# with r=46 and an add_glow halo out to r*2.1 = 97, so the core column is busy
# down to y ~= 397. The banner therefore goes BELOW the core, still inside the
# right half of the art, stamped across the star's soft glow edge — the
# reference's over-the-art look without burying the one focal body.
BANNER_CY = 505
# Vertical ceiling: keeps the banner clear of the floating caption (baseline 652).
BANNER_Y_MAX = 606
# Horizontal centre of the free right-hand span. The character owns x < 540, so
# the banner is centred here rather than on the frame, and "A NEUTRON STAR"
# (608 px advance + 8 px of keyline at 64 px) lands with its right edge at
# ~1198, fully on-screen.
BANNER_CX = 890


def _heavy_word(draw, text, cx=BANNER_CX, cy=BANNER_CY, color=None,
                stroke=3, px=64, clamp=True):
    """The banner word at 64 px (the schedule's heavy_px) with the 3 px
    slate-black keyline the reference uses on every word it stamps over art.

    DELEGATES to ``C.hero_word``. The old local version clamped against
    ``T._bbox``'s ADVANCE width, which ignores the keyline that
    ``draw_outlined_text`` adds outside the glyphs on all four sides — so
    "A NEUTRON STAR" passed the clamp and still lost its final R off the right
    edge. ``hero_word`` measures the same call the renderer makes and clamps
    INCLUDING the stroke, and auto-shrinks a phrase too wide for the frame.
    """
    return C.hero_word(draw, text, cx, cy,
                       fill_rgb=color if color is not None else C.PAL['bone'],
                       stroke_rgb=C.PAL['ink'], stroke_width=stroke, px=px,
                       margin=40, y_max=BANNER_Y_MAX)


def _nebula_wisp(draw, seed, alpha=20):
    """A wobbly 9-gon violet wisp across the lower-left third at 8% alpha. Flat
    fill, no gradient — it is a wash, not a body."""
    rnd = random.Random(seed)
    cx, cy = 300, 620
    pts = []
    for i in range(9):
        a = math.tau * i / 9
        rad = rnd.uniform(170, 265)
        pts.append((cx + rad * math.cos(a) * 1.15, cy + rad * math.sin(a) * 0.52))
    K.draw_smooth(draw, pts, fill=C.PAL['violet'] + (alpha,), outline=None,
                  seed=seed, wobble=16.0, wavelength=150.0)


# ---------------------------------------------------------------------------
# Card 1 — hook_dead
# ---------------------------------------------------------------------------

def render_hook_dead(card, planet="PSR B1257+12"):
    """B1/1 — the dead star alone in the void: bone core, two FLAT violet halo
    rings, a faint nebula wisp, the word ALREADY DEAD stamped across the art
    BELOW the core (BANNER_CY), and the character standing flat/deadpan at his
    scheduled spot. One focal point: the star. Everything else is a whisper
    under it."""
    img = Image.new('RGB', (C.W, C.H), C.PAL['deep'])
    _void_field(img, seed=101, stars=130)

    d = _pulsar_core(img, STAR_CX, STAR_CY, STAR_R, seed=101)
    # faint nebula wisp, lower-left third, behind the character
    _nebula_wisp(d, seed=31, alpha=20)
    # two FLAT magnetic halo rings at 12% / 22% (PALETTE_SPEC §3)
    for rr, a in ((64, 30), (78, 56)):
        _flat_ring(d, STAR_CX, STAR_CY, rr, C.PAL['violet'], a, K.DETAIL)

    _heavy_word(d, "ALREADY DEAD", BANNER_CX, BANNER_CY, C.PAL['bone'], stroke=3)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# Card 2 — hook_talking
# ---------------------------------------------------------------------------

def render_hook_talking(card, planet="PSR B1257+12"):
    """B1/2 — the same star, now emitting: three violet radio arcs opening toward
    the character at 20/55/15% alpha, and one bone meridian tick on the limb that
    the frame generator steps 90 deg per 0.25 s stamp. The pointing pose aims the
    character's arm down the beam; the frame stays empty and vast."""
    img = Image.new('RGB', (C.W, C.H), C.PAL['deep'])
    _void_field(img, seed=202, stars=118)

    d = ImageDraw.Draw(img, 'RGBA')
    # radio arcs FIRST so the core sits on top of them — flat, no gradient
    for rr, a, wdt, sd in ((110, 51, 5, 202), (170, 140, 4, 203), (230, 38, 3, 204)):
        _radio_arc(d, STAR_CX, STAR_CY, rr, 128, 232,
                   C.PAL['violet'], a, wdt, seed=sd)

    d = _pulsar_core(img, STAR_CX, STAR_CY, STAR_R, seed=202, grain=0.02)
    _meridian_tick(d, STAR_CX, STAR_CY, STAR_R, angle_deg=0, seed=205)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# Card 3 — hook_not_alone
# ---------------------------------------------------------------------------

def render_hook_not_alone(card, planet="PSR B1257+12"):
    """B1/3 — the reveal. The violet halos are gone and a 2 px AMBER limb ring
    takes their place, the first hot colour in the segment, with the banner A
    NEUTRON STAR stamped across the art BELOW the core in amber (BANNER_CY) so
    the word is whole on-screen and the core still reads. The character is awed,
    hands up. Bare field otherwise: the name is the event."""
    img = Image.new('RGB', (C.W, C.H), C.PAL['deep'])
    _void_field(img, seed=303, stars=126)

    d = _pulsar_core(img, STAR_CX, STAR_CY, STAR_R, seed=303, grain=0.03)
    # the first hot colour in the segment — a fine amber ring on the limb
    _flat_ring(d, STAR_CX, STAR_CY, STAR_R + 3, C.PAL['amber'], 217, K.FINE)

    _heavy_word(d, "A NEUTRON STAR", BANNER_CX, BANNER_CY, C.PAL['amber'], stroke=3)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


RENDERERS = {
    'hook_dead': render_hook_dead,
    'hook_talking': render_hook_talking,
    'hook_not_alone': render_hook_not_alone,
}


def register(mapping=None):
    """Merge this beat's renderers into the shared dispatch table. Called by the
    frame generator; harmless if called twice."""
    C.register(mapping if mapping is not None else RENDERERS)
    return RENDERERS
