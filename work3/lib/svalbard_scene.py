"""svalbard scene -- chapter 8 of the bunker film.

SVALBARD GLOBAL SEED VAULT: the arctic seed repository cut into a permafrost
mountain. The chapter's argument is that the vault works -- the seeds are fine
-- and that is exactly the problem, because the permafrost that keeps it frozen
is the same permafrost that is thawing. So the arc runs cold-and-safe at the
top, leak in the middle, and "the seeds are still fine, for now" at the bottom,
with the last line landing on water still moving under the snow.

Structure is identical to pinegap_scene.py: every card paints its OWN WHOLE
FRAME (background -> subject), one card per beat or beat group, so one card's
art can never bleed into the next. Captions go through `cap()`, which hands off
at the next phrase, and every narration line here is <=8 words so each beat is
exactly one caption.

FRAME-FILL. The recurring defect in this project's history is a small subject
parked in an empty field. Every card below scales its subject until it is
cropped by a frame edge: the mountain runs off both sides, the tunnel fills the
frame and recedes past it, the shelving runs out past both edges, the globe is
cropped bottom-right, the frost-covered packet is drawn large enough to bleed.

CADENCE. Still-dominant, one cut per sentence (~35 cuts in ~97s). `motion=` is
passed on exactly two cards, where the narrator describes something moving: the
meltwater creeping at b21 and the dark line of water still running through the
frozen layer at b35.

Run:  python lib/svalbard_scene.py --preview --video
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import engine3 as E3
import scene_common as SC
import v2paint as PA
import v2subjects as S
import v2draw as D
import v2type as VT

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'svalbard'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Svalbard'

# Rows the engine's near-black title is given a lit course to read against, on
# the night cards only. band_intrusions() excuses exactly these rows, and only
# where a row is uniform end to end, so it cannot hide art (see the
# scene_common.title_backdrop note).
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# One ink, one paper/snow, two accents (amber = the seeds, red = the threat),
# one deep cold. Snow and slate carry every exterior; the warm amber is the ONLY
# warm colour in the chapter and it is spent on the seeds and the lit chamber,
# so "the seeds are fine" and "the warm light inside the rock" read as the same
# idea and the reds read as the only danger.
INK = SC.INK
SNOW = (238, 242, 246)          # lit snow
SNOW_SH = (206, 216, 228)       # snow in shadow / drift
SLATE = (108, 116, 128)         # permafrost / rock, lit
SLATE_DK = (66, 72, 84)         # rock, deep
ICE = (150, 176, 196)           # the frozen layer
COLD = (36, 44, 60)             # night sky
COLD_DK = (22, 28, 40)
AMBER = (214, 150, 52)          # the seeds / the lit chamber. THE warm accent.
AMBER_LT = (238, 196, 120)
LEAF = (108, 150, 74)           # sprout / growing
RED = (188, 46, 40)             # meltwater warning / camera lamp
WATER = (86, 116, 132)          # meltwater
CONCRETE = (206, 202, 192)      # the wedge of concrete over the doorway
STEEL = (146, 152, 162)         # shelving, doors

# The lit course at the head of a night card, so the engine's near-black title
# reads. A cold polar blue-grey: clearly lighter than COLD (36, 44, 60) and
# SLATE_DK (66, 72, 84) so it lifts the band, but still night and still in the
# chapter's own family rather than a grey UI bar.
TITLE_COURSE = (96, 112, 140)

HZ = int(H * 0.62)              # horizon; exterior bases sit on it


# ---------------------------------------------------------------------------
# backgrounds
# ---------------------------------------------------------------------------

def _arctic(tile, seed, sky_top=COLD, sky_bot=(96, 112, 136), snow=SNOW,
            night=True, hz=HZ):
    """Full-frame arctic exterior: cold sky over a flat snow plain.

    The sky is painted over the WHOLE frame first and the snow laid on top
    starting slightly above the nominal horizon, so the wobbling edges overlap
    instead of leaving a seam (see SC.sky_bg's note on the same bug).
    """
    PA.fill_rect(tile, [0, 0, W, H], sky_top, seed=seed, value=0.06)
    if night:
        PA.fill_rect(tile, [0, int(H * 0.34), W, int(hz + 24)],
                     sky_bot, seed=seed + 1, value=0.07)
    PA.fill_rect(tile, [0, hz - 6, W, H], snow, seed=seed + 2, value=0.06)
    PA.paper_overlay(tile, seed=seed + 3)


def _day_arctic(tile, seed, snow=SNOW, hz=HZ):
    """Midsummer exterior: a pale washed sky and blinding white. No night band."""
    PA.fill_rect(tile, [0, 0, W, H], (176, 198, 218), seed=seed, value=0.05)
    PA.fill_rect(tile, [0, int(H * 0.30), W, int(hz + 24)],
                 (206, 220, 232), seed=seed + 1, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], snow, seed=seed + 2, value=0.05)
    PA.paper_overlay(tile, seed=seed + 3)


def _interior(tile, seed, wall=(92, 100, 112), floor=(70, 76, 88),
              warm=None):
    """The cold room / tunnel interior: walls, floor, and a warm pool of light
    at the vanishing point when `warm` is set (the lit chamber, the doorway)."""
    PA.fill_rect(tile, [0, 0, W, H], wall, seed=seed, value=0.07)
    PA.fill_rect(tile, [0, int(H * 0.74), W, H], floor, seed=seed + 1,
                 value=0.07)
    if warm is not None:
        g = PA.ellipse_pts(W * 0.5, H * 0.52, W * 0.34, H * 0.42, n=64)
        PA.fill_poly(tile, g, warm, seed=seed + 2, value=0.05)
    PA.paper_overlay(tile, seed=seed + 3)


def _snow_hatch(d, x0, y0, x1, y1, seed, col=ICE, step=17, width=3):
    """Dense vertical hatching -- the permafrost's frozen texture.

    Vertical, not random scribble: real permafrost ice in a cutaway is drawn as
    a comb. Stepping in x and running each line slightly off-square gives the
    drawn texture that says "frozen ground" rather than "grey box".
    """
    x = x0
    i = 0
    while x < x1:
        j = (i * 37) % 23 - 11                  # deterministic per-line offset
        PA.hand_stroke(d, [(x, y0 + j), (x + 2, y1 + j)], col, width,
                       seed=seed + i, wavelength=90.0)
        x += step
        i += 1


# ---------------------------------------------------------------------------
# subject primitives
# ---------------------------------------------------------------------------

def _mountain(d, seed, crest=340, base=760, colour=SLATE_DK, snowline=True,
              col_x0=None):
    """A dark permafrost mountain filling the frame, cropped at both sides.

    Built from a ridge polyline that is deliberately wider than the frame and a
    couple of secondary peaks, so the mass bleeds off the left and right edges
    instead of sitting inside them. The snow cap is a separate lighter polygon
    riding the ridge, which is what makes it read as snow-covered rock rather
    than a grey triangle.
    """
    img = PA.img_of(d)
    x0 = col_x0 if col_x0 is not None else -220
    ridge = [(x0, base), (x0 + 150, crest + 150), (x0 + 380, crest - 20),
             (x0 + 620, crest + 110), (x0 + 880, crest + 40),
             (W + 220, crest + 190), (W + 220, base)]
    PA.fill_poly(img, ridge, colour, seed=seed, value=0.07)
    PA.hand_stroke(d, ridge[:6], INK, 7, closed=False, seed=seed + 1,
                   wavelength=170.0)
    if snowline:
        cap = [(x0 + 150, crest + 150), (x0 + 380, crest - 20),
               (x0 + 620, crest + 110), (x0 + 760, crest + 92),
               (x0 + 640, crest + 150), (x0 + 380, crest + 60),
               (x0 + 210, crest + 200)]
        PA.fill_poly(img, cap, SNOW, seed=seed + 2, value=0.05)
    return ridge


def _wedge(d, cx, cy, seed, w=210, h=150, colour=CONCRETE):
    """The wedge of concrete set into the rock above the doorway."""
    img = PA.img_of(d)
    wedge = [(cx - w, cy - h), (cx + w, cy - h), (cx + w * 0.74, cy + h * 0.5),
             (cx - w * 0.74, cy + h * 0.5)]
    PA.fill_poly(img, wedge, colour, seed=seed, value=0.07)
    PA.hand_stroke(d, wedge, INK, 6, closed=True, seed=seed + 1,
                   wavelength=140.0)
    for k in range(3):
        y = cy - h * 0.5 + k * h * 0.34
        PA.hand_stroke(d, [(cx - w * 0.82, y), (cx + w * 0.82, y)],
                       (178, 174, 166), 4, seed=seed + 2 + k, wavelength=90.0)


def _doorway(d, cx, cy, seed, w=140, h=190, colour=(46, 52, 64), lit=None):
    """The tunnel mouth: a dark rectangular opening, optionally lit from within."""
    img = PA.img_of(d)
    box = [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
    PA.fill_poly(img, box, colour, seed=seed, value=0.05)
    PA.hand_stroke(d, box, INK, 7, closed=True, seed=seed + 1, wavelength=150.0)
    if lit is not None:
        inner = [(cx - w * 0.62, cy - h * 0.62), (cx + w * 0.62, cy - h * 0.62),
                 (cx + w * 0.62, cy + h * 0.62), (cx - w * 0.62, cy + h * 0.62)]
        PA.fill_poly(img, inner, lit, seed=seed + 2, value=0.05)
    # a heavy frame so it reads as an engineered mouth, not a hole
    PA.hand_stroke(d, [(cx - w * 1.16, cy - h * 1.10), (cx + w * 1.16, cy - h * 1.10),
                       (cx + w * 1.16, cy + h * 1.04), (cx - w * 1.16, cy + h * 1.04)],
                   INK, 9, closed=True, seed=seed + 3, wavelength=150.0)


def _tunnel(d, cx, cy, seed, mouth=470, depth=210, ribs=9, wall=(70, 76, 88),
            floor=(52, 58, 70), dark=(30, 34, 42)):
    """A one-point-perspective corridor receding into black -- the key image.

    Four nested trapezoids (wall band, ceiling, floor, then the black far end),
    each smaller and each with its own stroke, plus ceiling ribs that shrink
    with depth. The perspective is solved from ONE vanishing point rather than
    eyeballed: every rectangle shares (cx, cy) as its far corners, which is what
    makes the ribs converge instead of drifting.
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [0, 0, W, H], wall, seed=seed, value=0.06)

    def quad(k):
        """Rectangle k of the corridor: k=0 is the mouth (offscreen), last is
        the far end. Half-width and half-height both shrink by a fixed ratio."""
        t = k / float(ribs)
        hw = mouth * (1.0 - t) ** 1.35
        hh = depth * (1.0 - t) ** 1.35
        return [(cx - hw, cy - hh), (cx + hw, cy - hh),
                (cx + hw, cy + hh), (cx - hw, cy + hh)]

    # ceiling / floor bands: the wall colour above and below each ring
    for k in range(ribs - 1):
        a, b = quad(k), quad(k + 1)
        PA.fill_poly(img, [(a[0][0], a[0][1]), (a[1][0], a[1][1]),
                           (b[1][0], b[1][1]), (b[0][0], b[0][1])],
                     floor, seed=seed + 10 + k, value=0.06)          # ceiling
        PA.fill_poly(img, [(a[3][0], a[3][1]), (a[2][0], a[2][1]),
                           (b[2][0], b[2][1]), (b[3][0], b[3][1])],
                     floor, seed=seed + 40 + k, value=0.06)          # floor
        PA.hand_stroke(d, [a[0], a[1]], (44, 48, 58), 6, closed=False,
                       seed=seed + 70 + k, wavelength=120.0)
        PA.hand_stroke(d, [a[3], a[2]], (44, 48, 58), 6, closed=False,
                       seed=seed + 90 + k, wavelength=120.0)
        # the ring itself -- the ribs
        PA.hand_stroke(d, a, INK, 7, closed=True, seed=seed + 110 + k,
                       wavelength=130.0)
        PA.hand_stroke(d, [(a[0][0], a[0][1]), (b[0][0], b[0][1])],
                       (52, 58, 68), 5, closed=False, seed=seed + 130 + k,
                       wavelength=100.0)
        PA.hand_stroke(d, [(a[1][0], a[1][1]), (b[1][0], b[1][1])],
                       (52, 58, 68), 5, closed=False, seed=seed + 150 + k,
                       wavelength=100.0)
    end = quad(ribs)
    PA.fill_poly(img, end, dark, seed=seed + 3, value=0.0)
    return quad


def _shelf(d, x0, x1, y, seed, h=150, colour=STEEL, packets=9, depth=13):
    """A run of metal shelving. Used stacked, so it draws the uprights, the
    deck line, and a row of small foil packets standing on it.

    Packets are drawn as flat upright rectangles with a stamped band -- at this
    size that band is what makes them read as labelled sample packets rather
    than as a row of books.
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [x0, y, x1, y + 16], colour, seed=seed, value=0.07)
    PA.hand_stroke(d, [(x0, y + 16), (x1, y + 16)], INK, 6, closed=False,
                   seed=seed + 1, wavelength=150.0)
    for ux in (x0, x1):
        PA.hand_stroke(d, [(ux, y), (ux, y + h)], INK, 8, closed=False,
                       seed=seed + 2 + int(ux), wavelength=120.0)
    step = (x1 - x0) / float(packets)
    pw = step * 0.72
    for i in range(packets):
        x = x0 + i * step + (step - pw) * 0.5
        ph = h * 0.46
        box = [(x, y - ph), (x + pw, y - ph), (x + pw, y), (x, y)]
        PA.fill_poly(img, box, (222, 224, 226), seed=seed + 10 + i, value=0.06)
        PA.hand_stroke(d, box, INK, 4, closed=True, seed=seed + 40 + i,
                       wavelength=60.0)
        PA.hand_stroke(d, [(x + pw * 0.18, y - ph * 0.62),
                           (x + pw * 0.82, y - ph * 0.62)], AMBER, 5,
                       closed=False, seed=seed + 70 + i, wavelength=40.0)


def _packet(d, cx, cy, w, h, seed, band=AMBER, fill=(224, 226, 228),
            stamp='crop'):
    """One foil sample packet: a flat upright rectangle with a stamped band and
    a tiny crop mark on the front. `stamp` selects the crop drawing."""
    img = PA.img_of(d)
    box = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
           (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    PA.fill_poly(img, box, fill, seed=seed, value=0.06)
    PA.hand_stroke(d, box, INK, 6, closed=True, seed=seed + 1,
                   wavelength=min(w, h) * 0.5)
    # crimped top seal -- foil, not paper
    PA.hand_stroke(d, [(cx - w / 2, cy - h / 2 + h * 0.10),
                       (cx + w / 2, cy - h / 2 + h * 0.10)],
                   (168, 172, 178), 5, closed=False, seed=seed + 2,
                   wavelength=50.0)
    PA.fill_rect(img, [cx - w / 2 + w * 0.12, cy - h * 0.16,
                       cx + w / 2 - w * 0.12, cy - h * 0.02], band,
                 seed=seed + 3, value=0.05)
    _crop_mark(d, cx, cy + h * 0.18, w * 0.34, seed + 4, stamp)


def _crop_mark(d, cx, cy, s, seed, kind):
    """The little crop drawing stamped on a packet face: wheat ear, rice
    panicle, barley, a bean pod, or a millet sprig. Five distinct silhouettes so
    the five-packet row reads as five different crops at a glance."""
    img = PA.img_of(d)
    col = INK
    if kind == 'wheat':                      # an ear on a stalk
        PA.hand_stroke(d, [(cx, cy + s * 0.6), (cx, cy - s * 0.5)], col, 4,
                       closed=False, seed=seed, wavelength=40.0)
        for k in range(4):
            yy = cy - s * 0.42 + k * s * 0.26
            for sx in (-1, 1):
                PA.hand_stroke(d, [(cx, yy), (cx + sx * s * 0.34, yy - s * 0.16)],
                               col, 3, closed=False, seed=seed + 1 + k,
                               wavelength=30.0)
    elif kind == 'rice':                     # a drooping panicle
        PA.hand_stroke(d, [(cx - s * 0.3, cy + s * 0.5), (cx, cy - s * 0.5),
                           (cx + s * 0.34, cy + s * 0.2)], col, 4, closed=False,
                       seed=seed, wavelength=50.0)
        for k in range(5):
            t = k / 4.0
            px = cx + s * (0.34 * t)
            py = cy - s * 0.5 + s * (0.7 * t)
            d.ellipse([px - s * 0.09, py - s * 0.16, px + s * 0.09, py + s * 0.05],
                      fill=col)
    elif kind == 'barley':                   # a fat head with long awns
        for k in range(6):
            a = -0.9 + k * 0.36
            PA.hand_stroke(d, [(cx, cy + s * 0.2),
                               (cx + math.sin(a) * s * 0.6, cy - s * 0.55)],
                           col, 3, closed=False, seed=seed + 1 + k,
                           wavelength=30.0)
        e = PA.ellipse_pts(cx, cy + s * 0.12, s * 0.24, s * 0.40, n=32)
        PA.fill_poly(img, e, col, seed=seed, value=0.0, tint=0.0, band=0.0,
                     edge=0.0)
    elif kind == 'bean':                     # a pod with two beans
        pod = PA.ellipse_pts(cx, cy, s * 0.46, s * 0.22, n=40, rot=-0.35)
        PA.fill_poly(img, pod, (250, 250, 248), seed=seed, value=0.0)
        PA.hand_stroke(d, pod, col, 4, closed=True, seed=seed + 1,
                       wavelength=40.0)
        for k in (-1, 1):
            d.ellipse([cx + k * s * 0.16 - s * 0.09, cy - s * 0.09,
                       cx + k * s * 0.16 + s * 0.09, cy + s * 0.09], fill=col)
    else:                                    # millet: a fat bristly head
        PA.hand_stroke(d, [(cx, cy + s * 0.62), (cx, cy - s * 0.3)], col, 4,
                       closed=False, seed=seed, wavelength=40.0)
        e = PA.ellipse_pts(cx, cy - s * 0.36, s * 0.20, s * 0.34, n=32)
        PA.fill_poly(img, e, col, seed=seed + 2, value=0.0, tint=0.0,
                     band=0.0, edge=0.0)
        for k in range(7):
            a = -1.1 + k * 0.36
            PA.hand_stroke(d, [(cx, cy - s * 0.5),
                               (cx + math.sin(a) * s * 0.34, cy - s * 0.86)],
                           col, 2, closed=False, seed=seed + 3 + k,
                           wavelength=24.0)


def _sprout(d, cx, cy, s, seed, col=LEAF):
    """A seedling: two leaves on a stem, in a little mound of soil. The
    'future farmers' gag."""
    img = PA.img_of(d)
    PA.hand_stroke(d, [(cx, cy + s * 0.5), (cx, cy - s * 0.34)], col, 6,
                   closed=False, seed=seed, wavelength=50.0)
    for sx in (-1, 1):
        leaf = PA.ellipse_pts(cx + sx * s * 0.26, cy - s * 0.40, s * 0.30,
                              s * 0.15, n=36, rot=sx * -0.5)
        PA.fill_poly(img, leaf, col, seed=seed + 1 + sx, value=0.06)
        PA.hand_stroke(d, leaf, INK, 4, closed=True, seed=seed + 3 + sx,
                       wavelength=50.0)
    soil = PA.ellipse_pts(cx, cy + s * 0.56, s * 0.62, s * 0.16, n=40)
    PA.fill_poly(img, soil, (120, 96, 70), seed=seed + 6, value=0.07)
    PA.hand_stroke(d, soil, INK, 4, closed=True, seed=seed + 7, wavelength=50.0)


def _polar_bear(d, cx, cy, s, seed, col=(250, 250, 248)):
    """A polar bear as a simple white silhouette -- the Svalbard 'insurance
    policy'. Body, head, four legs, tail. White on snow, so it is separated by
    its INK outline and a slate shadow belly rather than by value alone."""
    img = PA.img_of(d)
    body = PA.ellipse_pts(cx, cy, s * 0.62, s * 0.30, n=44)
    PA.fill_poly(img, body, col, seed=seed, value=0.05)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1,
                   wavelength=90.0)
    head = PA.ellipse_pts(cx + s * 0.68, cy - s * 0.26, s * 0.26, s * 0.20,
                          n=36)
    PA.fill_poly(img, head, col, seed=seed + 2, value=0.05)
    PA.hand_stroke(d, head, INK, 6, closed=True, seed=seed + 3,
                   wavelength=70.0)
    PA.hand_stroke(d, [(cx + s * 0.86, cy - s * 0.30), (cx + s * 1.02, cy - s * 0.22)],
                   INK, 5, closed=False, seed=seed + 4, wavelength=40.0)   # snout
    d.ellipse([cx + s * 0.74, cy - s * 0.36, cx + s * 0.80, cy - s * 0.30],
              fill=INK)
    for k, lx in enumerate((-0.40, -0.16, 0.22, 0.44)):
        PA.hand_stroke(d, [(cx + s * lx, cy + s * 0.18),
                           (cx + s * lx, cy + s * 0.56)], INK, 9,
                       closed=False, seed=seed + 5 + k, wavelength=40.0)
    PA.hand_stroke(d, [(cx - s * 0.60, cy - s * 0.06), (cx - s * 0.80, cy - s * 0.22)],
                   INK, 6, closed=False, seed=seed + 10, wavelength=40.0)


def _globe(d, cx, cy, r, seed, colour=(120, 152, 176)):
    """A globe with hand-drawn continents, cropped by the frame edge on the
    caller's side so it dominates rather than floats.

    Two things were wrong here, both found by rendering this primitive alone
    and looking at it at ship size:

      1. Z-ORDER. The meridian hoops were drawn AFTER the continents, so every
         hoop crossed straight over the land. That single line of ordering is
         what stopped the land reading as land -- a globe's grid is a property
         of the SPHERE and sits on the water, not on top of the countries.
      2. KEYLINE. The continents were filled AND given a 5px ink keyline, so at
         r=336 they read as four pale stickers pasted on the sphere rather
         than as landmass. Real continents meet the water with no outline at
         all; the value break alone is the boundary.
    """
    img = PA.img_of(d)
    g = PA.ellipse_pts(cx, cy, r, r, n=80)
    PA.fill_poly(img, g, colour, seed=seed, value=0.07)

    # Hoops FIRST, so the land sits on top of the grid.
    for k, ry in enumerate((0.30, 0.62, 0.88)):
        hoop = PA.ellipse_pts(cx, cy, r * ry, r, n=48)
        PA.hand_stroke(d, hoop, (96, 124, 146), 3, closed=True,
                       seed=seed + 40 + k, wavelength=140.0)
    # ...and they stop at the terminator rather than crossing the frame edge.
    PA.hand_stroke(d, g, INK, 7, closed=True, seed=seed + 1, wavelength=170.0)

    # Continents last, no keyline: the value break against the water IS the
    # coastline, which is what makes them read as land rather than as shapes.
    #
    # The coastlines are DENSELY RESAMPLED before they are drawn. With only the
    # five control points of each landmass, PA.fill_poly produced clean convex
    # pentagons, and at r=336 four convex pentagons read as four green stickers
    # on a ball -- which is the defect this whole function exists to avoid. A
    # real coast is ragged: bays, peninsulas, a few offshore islands. So each
    # edge is split into segments, pulled off its chord by a deterministic
    # pseudo-random amount, and given a few inlets.
    lands = [[(-0.62, -0.42), (-0.30, -0.56), (-0.10, -0.34), (-0.24, -0.10),
              (-0.52, -0.14)],
             [(-0.16, 0.02), (0.06, 0.10), (0.02, 0.40), (-0.14, 0.46),
              (-0.22, 0.22)],
             [(0.16, -0.40), (0.56, -0.44), (0.66, -0.18), (0.40, -0.02),
              (0.18, -0.14)],
             [(0.22, 0.06), (0.52, 0.02), (0.58, 0.34), (0.36, 0.52),
              (0.20, 0.30)]]

    def _coast(ctrl, sd, per_edge=9, amp=0.055):
        """Resample a closed control polygon into a ragged coastline.

        Two things this got wrong before, both visible only by rendering it:

        1. The perpendicular offset was a fraction of the GLOBE RADIUS rather
           than of the edge it displaces. At r=336 that moved each sample ~18px
           across segments shorter than that, so the polygon self-intersected
           and filled as a starburst.
        2. The wobble keyed off the SAMPLE INDEX, so it flipped sign every
           sample and turned each edge into a sawtooth -- coastlines came out
           as spiky stars. A coast is a low-frequency wobble along the edge,
           so the phase now advances with distance travelled, not with j.

        The offset is clamped to the edge length, which makes self-intersection
        impossible by construction rather than by luck.
        """
        out = []
        n = len(ctrl)
        # running arc-length phase, so the wobble is continuous across the join
        run = 0.0
        for i in range(n):
            ax, ay = ctrl[i]
            bx, by = ctrl[(i + 1) % n]
            dx, dy = bx - ax, by - ay
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            lim = amp * ln
            for j in range(per_edge):
                u = j / float(per_edge)
                s = run + u * ln
                # three octaves of low-frequency noise, phase on arc length
                w = (math.sin(s * 0.9 + sd * 0.11) * 0.6
                     + math.sin(s * 2.3 + sd * 0.37) * 0.28
                     + math.sin(s * 4.7 + sd * 0.73) * 0.12)
                t = math.sin(math.pi * u)          # zero at the control corners
                k = max(-lim, min(lim, w * lim * t))
                out.append((ax + dx * u + nx * k, ay + dy * u + ny * k))
            run += ln
        return out

    for k, poly in enumerate(lands):
        pts = [(cx + u * r, cy + v * r)
               for u, v in _coast(poly, seed + k)]
        PA.fill_poly(img, pts, (146, 160, 116), seed=seed + 10 + k, value=0.10)

    # Offshore islands, so the coast is not the only land detail and the eye
    # reads "shoreline" rather than "four objects on a disc".
    isl = [(-0.44, 0.20, 0.030), (0.44, -0.30, 0.022), (0.06, 0.56, 0.026),
           (-0.74, 0.02, 0.018), (0.70, 0.44, 0.020)]
    for k, (u, v, rr) in enumerate(isl):
        ix, iy = cx + u * r, cy + v * r
        PA.fill_poly(img, PA.ellipse_pts(ix, iy, rr * r, rr * r * 0.78, n=14),
                     (146, 160, 116), seed=seed + 70 + k, value=0.10)


def _cutaway(d, seed, warm_chamber=False, water_level=None, ragged=False,
             melt_arrows=False, label=None):
    """The mountain in cross-section: rock above, the frozen layer as a hatched
    band, and the vault hall cut into it. This is the chapter's diagram and it
    recurs four times, so it is built once and varied.

    `water_level` (0..1 of the tunnel) floods the corridor from the bottom.
    `ragged` thins and notches the frozen layer -- the "it thaws too" beat.
    `melt_arrows` drives red arrows down into it.
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [0, 0, W, H], SLATE, seed=seed, value=0.07)

    surface = [(0, 250), (300, 205), (640, 178), (980, 200), (W, 244),
               (W, 330), (0, 330)]
    PA.fill_poly(img, surface, SLATE_DK, seed=seed + 1, value=0.07)
    PA.hand_stroke(d, surface[:5], INK, 6, closed=False, seed=seed + 2,
                   wavelength=180.0)
    # the snow cap riding the surface line
    cap = [(0, 250), (300, 205), (640, 178), (980, 200), (W, 244),
           (W, 258), (980, 214), (640, 192), (300, 219), (0, 264)]
    PA.fill_poly(img, cap, SNOW, seed=seed + 3, value=0.05)

    # the frozen layer -- the permafrost band
    fy0, fy1 = 330, 560
    if ragged:
        fy1 = 470                                    # thinner, and it varies
    band = [(0, fy0), (W, fy0), (W, fy1), (0, fy1)]
    PA.fill_poly(img, band, ICE, seed=seed + 4, value=0.06)
    PA.hand_stroke(d, [(0, fy0), (W, fy0)], INK, 6, closed=False,
                   seed=seed + 5, wavelength=180.0)
    if ragged:
        # a notched lower boundary: the ice layer eaten from below
        low = []
        n = 40
        for i in range(n + 1):
            x = W * i / float(n)
            yy = fy1 - 46 * math.sin(i * 1.1) - 18 * math.sin(i * 0.37 + 1.2)
            low.append((x, yy))
        low = low + [(W, fy1), (0, fy1)]
        PA.fill_poly(img, band, ICE, seed=seed + 4, value=0.06)
        PA.fill_poly(img, low, SLATE, seed=seed + 6, value=0.06)
        PA.hand_stroke(d, low[:n + 1], INK, 6, closed=False, seed=seed + 7,
                       wavelength=120.0)
    else:
        PA.hand_stroke(d, [(0, fy1), (W, fy1)], INK, 6, closed=False,
                       seed=seed + 6, wavelength=180.0)
    _snow_hatch(d, 0, fy0 + 8, W, fy1 - 6, seed + 8, col=(120, 146, 168),
                step=19, width=3)

    # the corridor: a long straight hall driven in from the left face
    cx0, cy0 = -40, 470
    cx1, cy1 = 1010, 470
    ch = 84
    corr = [(cx0, cy0 - ch), (cx1, cy1 - ch), (cx1, cy1 + ch), (cx0, cy0 + ch)]
    PA.fill_poly(img, corr, (58, 64, 74), seed=seed + 9, value=0.06)
    PA.hand_stroke(d, corr, INK, 6, closed=True, seed=seed + 10,
                   wavelength=170.0)
    for k in range(1, 7):                            # support ribs
        x = cx0 + (cx1 - cx0) * k / 7.0
        PA.hand_stroke(d, [(x, cy0 - ch), (x, cy0 + ch)], (86, 92, 102), 5,
                       closed=False, seed=seed + 20 + k, wavelength=90.0)
    # the seed chamber at the far end, lit warm
    hx0, hx1 = cx1, 1230
    hall = [(hx0, cy1 - ch * 1.5), (hx1, cy1 - ch * 1.5),
            (hx1, cy1 + ch * 1.5), (hx0, cy1 + ch * 1.5)]
    PA.fill_poly(img, hall, (70, 76, 88) if not warm_chamber else (128, 96, 46),
                 seed=seed + 30, value=0.06)
    PA.hand_stroke(d, hall, INK, 6, closed=True, seed=seed + 31, wavelength=150.0)
    if warm_chamber:
        gl = PA.ellipse_pts(1080, 470, 190, 150, n=56)
        PA.fill_poly(img, gl, AMBER_LT, seed=seed + 32, value=0.05)
        for k in range(3):
            _shelf(d, 1000 + k * 78, 1080 + k * 78, 470 + k * 18, seed + 40 + k,
                   h=64, packets=2)
    else:
        for k in range(3):
            _shelf(d, 1000 + k * 78, 1080 + k * 78, 470 + k * 18, seed + 40 + k,
                   h=64, packets=2)

    if water_level:
        wy = cy0 + ch - 2 * ch * water_level
        flood = [(cx0, cy0 + ch), (cx1, cy1 + ch), (cx1, wy), (cx0, wy)]
        PA.fill_poly(img, flood, WATER, seed=seed + 50, value=0.07)
        PA.hand_stroke(d, [(cx0, wy), (cx1, wy)], (150, 180, 196), 6,
                       closed=False, seed=seed + 51, wavelength=170.0)
        for k in range(9):
            x = cx0 + 90 + k * 120
            PA.hand_stroke(d, [(x, wy + 26), (x + 34, wy + 46)],
                           (150, 180, 196), 4, closed=False,
                           seed=seed + 60 + k, wavelength=50.0)

    if melt_arrows:
        for k in range(6):
            x = 120 + k * 200
            D.draw_arrow(img, (x + 40, fy0 - 40), (x - 20, fy0 + 96),
                         color=RED, width=8, head=36)

    if label:
        D.draw_label(img, label, center=(250, fy0 + 70), color=VT.LABEL_BLUE,
                     size=34)


def _camera(d, cx, cy, s, seed):
    """A small camera on a stalk above the tunnel door, with its lamp lit."""
    img = PA.img_of(d)
    PA.hand_stroke(d, [(cx, cy + s * 0.55), (cx, cy + s * 1.6)], STEEL, 9,
                   closed=False, seed=seed, wavelength=60.0)
    body = [(cx - s * 0.5, cy - s * 0.5), (cx + s * 0.42, cy - s * 0.56),
            (cx + s * 0.52, cy + s * 0.16), (cx - s * 0.44, cy + s * 0.22)]
    PA.fill_poly(img, body, (206, 208, 210), seed=seed + 1, value=0.07)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 2, wavelength=60.0)
    lens = PA.ellipse_pts(cx + s * 0.30, cy - s * 0.16, s * 0.22, s * 0.22, n=32)
    PA.fill_poly(img, lens, (52, 58, 68), seed=seed + 3, value=0.0)
    PA.hand_stroke(d, lens, INK, 5, closed=True, seed=seed + 4, wavelength=40.0)
    PA.hand_stroke(d, [(cx - s * 0.52, cy - s * 0.5), (cx - s * 1.0, cy - s * 0.72)],
                   INK, 5, closed=False, seed=seed + 5, wavelength=40.0)
    lamp = PA.ellipse_pts(cx - s * 0.40, cy + s * 0.52, s * 0.16, s * 0.16, n=28)
    PA.fill_poly(img, lamp, RED, seed=seed + 6, value=0.05)
    PA.hand_stroke(d, lamp, INK, 4, closed=True, seed=seed + 7, wavelength=40.0)


def _excavator(d, cx, cy, s, seed):
    """A small tracked machine, drawn tiny on purpose -- it is at the scale the
    narrator means, 'machinery drawn small', next to the mountain."""
    img = PA.img_of(d)
    track = [(cx - s * 0.9, cy + s * 0.34), (cx + s * 0.9, cy + s * 0.34),
             (cx + s * 0.9, cy + s * 0.70), (cx - s * 0.9, cy + s * 0.70)]
    PA.fill_poly(img, track, (58, 62, 70), seed=seed, value=0.06)
    PA.hand_stroke(d, track, INK, 5, closed=True, seed=seed + 1, wavelength=60.0)
    for k in range(4):
        x = cx - s * 0.62 + k * s * 0.42
        d.ellipse([x - s * 0.09, cy + s * 0.42, x + s * 0.09, cy + s * 0.60],
                  fill=(120, 126, 134))
    cab = [(cx - s * 0.42, cy - s * 0.30), (cx + s * 0.30, cy - s * 0.34),
           (cx + s * 0.30, cy + s * 0.34), (cx - s * 0.42, cy + s * 0.34)]
    PA.fill_poly(img, cab, AMBER, seed=seed + 2, value=0.07)
    PA.hand_stroke(d, cab, INK, 5, closed=True, seed=seed + 3, wavelength=60.0)
    PA.hand_stroke(d, [(cx + s * 0.26, cy - s * 0.30), (cx + s * 1.5, cy - s * 0.72)],
                   INK, 6, closed=False, seed=seed + 4, wavelength=70.0)
    bk = [(cx + s * 1.5, cy - s * 0.78), (cx + s * 1.9, cy - s * 0.78),
          (cx + s * 1.86, cy - s * 0.52), (cx + s * 1.5, cy - s * 0.52)]
    PA.fill_poly(img, bk, (150, 154, 160), seed=seed + 5, value=0.06)
    PA.hand_stroke(d, bk, INK, 4, closed=True, seed=seed + 6, wavelength=40.0)


def _flood_gate(d, cx, cy, seed, w=210, h=170):
    """Boards and a steel beam barricading the entrance -- the 'cut off for a
    year' beat."""
    img = PA.img_of(d)
    for k in range(4):
        y = cy - h * 0.5 + k * h * 0.28
        PA.hand_stroke(d, [(cx - w, y), (cx + w, y)], (146, 116, 78), 12,
                       closed=False, seed=seed + k, wavelength=90.0)
    PA.hand_stroke(d, [(cx - w * 1.1, cy - h * 0.62), (cx + w * 1.1, cy + h * 0.60)],
                   STEEL, 11, closed=False, seed=seed + 6, wavelength=110.0)


def _light_wedge(d, x, y0, y1, half, seed, colour=AMBER_LT):
    """One wedge of light lying on the snow: a long triangle from a hidden
    source off the top of the frame, widening as it lands."""
    img = PA.img_of(d)
    tri = [(x - half * 0.12, y0), (x + half * 0.12, y0),
           (x + half, y1), (x - half, y1)]
    PA.fill_poly(img, tri, colour, seed=seed, value=0.05, edge=3.0)
    PA.hand_stroke(d, [(x - half, y1), (x + half, y1)], (222, 232, 240), 5,
                   closed=False, seed=seed + 1, wavelength=90.0)


# ---------------------------------------------------------------------------
# named motion tracks -> (dx, dy) end offsets, resolved per-card in build().
# A name maps to a two-point track (start offset, end offset); card() spaces
# the keyframes across the card's own span so the drift is paced to the beat.
# ---------------------------------------------------------------------------
_MOTION = {
    'rise': ((0.0, 0.0), (0.0, -22.0)),   # meltwater creeping up
    'seep': ((0.0, 0.0), (0.0, 26.0)),    # the water line sliding down
}


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def card(i, j, draw, kind='subject', seed=0, motion=None):
        """A complete card: its own background, live beats i..j-1.

        `motion` is a NAME ('rise', 'seep') resolved to a real keyframe track
        below -- engine3 wants (t, dx, dy, scale, rot) tuples, and passing a
        bare string makes it sort characters and raise a float/str TypeError
        the moment the card renders.
        """
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        t0 = T(i)
        track = _MOTION.get(motion) if isinstance(motion, str) else motion
        if track is not None:
            # each _MOTION entry is ((dx0, dy0), (dx1, dy1)); the middle
            # element of a 5-tuple keyframe is dy, the third is scale
            track = [(t0, track[0][0], track[0][1], 1.0, 0.0),
                     (end, track[1][0], track[1][1], 1.0, 0.0)]
        return E3.E('card%02d' % i, kind, draw, at=t0, until=end,
                    motion=track)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ---- b01  the hook: an empty arctic night, one wedge of light ---------- #
    # FRAME-FILL: the mountain is the dominant mass, cropped at both edges, and
    # the light lies ON it. The first instinct -- a tiny lamp in a white void
    # -- is the exact defect this chapter's brief warns about.
    def c_hook(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 5)
        SC.title_backdrop(tile, 1005, col=TITLE_COURSE)
        _mountain(d, 7, crest=300, base=HZ + 6)
        _light_wedge(d, 760, 120, HZ - 4, 190, 9)
        SC.fullbody(d, 1150, HZ + 4, 190, pose='standing', expression='deadpan',
                    seed=11)
    els.append(card(1, 2, c_hook))
    els.append(cap(1, W // 2, 690, size=32, fill=AMBER_LT))

    # ---- b02  the title, stamped across the sky --------------------------- #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 13)
        SC.title_backdrop(tile, 1013, col=TITLE_COURSE)
        _mountain(d, 15, crest=380, base=HZ + 6)
        _light_wedge(d, 640, 120, HZ - 4, 170, 17)
        D.draw_label(tile, 'SVALBARD', center=(640, 150), color=VT.LABEL_YELLOW,
                     size=86)
        D.draw_label(tile, 'GLOBAL SEED VAULT', center=(640, 240),
                     color=VT.LABEL_YELLOW, size=44)
    els.append(card(2, 3, c_title))
    els.append(cap(2, W // 2, 700, size=30, fill=AMBER_LT))

    # ---- b03  where it is: the map ---------------------------------------- #
    def c_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (176, 202, 222), seed=21, value=0.05)
        PA.paper_overlay(tile, seed=22)
        # a stylised north-Atlantic landmass: Norway picked out, one island
        # north of it. The land runs off the bottom edge so it is a map corner,
        # not a floating blob.
        land = [(-40, 720), (-40, 470), (150, 430), (280, 380), (360, 300),
                (470, 268), (520, 300), (430, 350), (500, 400), (430, 470),
                (560, 520), (470, 720)]
        PA.fill_poly(tile, land, (222, 226, 214), seed=23, value=0.07)
        PA.hand_stroke(d, land, INK, 7, closed=True, seed=24, wavelength=170.0)
        isle = [(690, 250), (790, 226), (880, 244), (900, 288), (800, 306),
                (704, 292)]
        PA.fill_poly(tile, isle, (222, 226, 214), seed=25, value=0.07)
        PA.hand_stroke(d, isle, INK, 6, closed=True, seed=26, wavelength=110.0)
        D.draw_label(tile, 'SPITSBERGEN', center=(795, 360), color=INK, size=32)
        D.draw_arrow(tile, (300, 200), (760, 250), color=RED, width=9, head=42,
                     bow=0.12)
        d.ellipse([905, 250, 929, 274], fill=RED)
        D.draw_label(tile, '2008', center=(1035, 430), color=VT.LABEL_RED,
                     size=76)
    els.append(card(3, 4, c_map))
    els.append(cap(3, W // 2, 690, size=30))

    # ---- b04  the tunnel, in one-point perspective ------------------------ #
    # The corridor IS the frame: the mouth is wider than 1280, so the walls run
    # off both side edges and the ribs converge on a point above centre.
    def c_tunnel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 31, wall=(64, 70, 82))
        _tunnel(d, W // 2, 372, 33, mouth=760, depth=290, ribs=8)
        SC.fullbody(d, W // 2 - 34, 560, 200, pose='standing',
                    expression='neutral', seed=35)
    els.append(card(4, 5, c_tunnel))
    els.append(cap(4, W // 2, 690, size=30, fill=(214, 224, 236)))

    # ---- b05  permafrost, hatched ----------------------------------------- #
    def c_perma(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 37, label='PERMAFROST')
    els.append(card(5, 6, c_perma))
    els.append(cap(5, W // 2, 660, size=30, fill=(226, 238, 248)))

    # ---- b06  the vault, cut into it, lit warm ----------------------------- #
    # The single warm light in the whole chapter. It is the seeds, and it is the
    # only thing in a cold grey frame -- so it dominates by value contrast even
    # though it is a small area.
    def c_cut_in(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 41, warm_chamber=True)
        SC.fullbody(d, 250, 700, 300, pose='pointing', expression='awed',
                    seed=43)
    els.append(card(6, 7, c_cut_in, kind='character'))
    els.append(cap(6, W // 2, 130, size=32, fill=AMBER_LT))

    # ---- b07  the doorway, at midsummer ----------------------------------- #
    def c_midsummer(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 45)
        _mountain(d, 46, crest=270, base=HZ + 6)
        S.sun_rays(d, 1080, 452, 54, seed=47, col=AMBER, n=12, inner=1.2,
                   outer=2.2)
        g = PA.ellipse_pts(1080, 452, 56, 56, n=48)
        PA.fill_poly(tile, g, AMBER, seed=48, value=0.05)
        PA.hand_stroke(d, g, INK, 5, closed=True, seed=49, wavelength=90.0)
        _wedge(d, 520, 372, 50, w=250, h=180)
        _doorway(d, 520, 470, 51, w=150, h=200, lit=(96, 86, 62))
        D.draw_arrow(tile, (860, 300), (700, 420), color=INK, width=10, head=44)
        D.draw_label(tile, 'midsummer', center=(980, 220), color=INK, size=34)
    els.append(card(7, 8, c_midsummer))
    els.append(cap(7, W // 2, 700, size=30))

    # ---- b08  inside the cold room: shelving out past both edges ----------- #
    def c_cold_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 55, wall=(78, 86, 98), floor=(58, 64, 74),
                  warm=(104, 88, 56))
        for k in range(5):
            _shelf(d, -120 + k * 8, W + 120, 210 + k * 96, 56 + k, h=190,
                   packets=13)
    els.append(card(8, 9, c_cold_room))
    els.append(cap(8, W // 2, 690, size=30, fill=(214, 224, 236)))

    # ---- b09  one packet, held up to the light ----------------------------- #
    def c_packet_hand(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 61, wall=(70, 78, 90), warm=(96, 84, 56))
        # cy was 330 with ry=260, so the glow's top edge sat at y=70 -- inside
        # the persistent title band, and on this card the glow is a bright amber
        # wash, so it lit the band from behind and left "Global Seed Vault" sitting
        # on a pale smear. 400 puts the top at y=140, clear of the band, and the
        # packet below is unchanged.
        g = PA.ellipse_pts(640, 400, 300, 260, n=64)
        PA.fill_poly(tile, g, AMBER_LT, seed=62, value=0.05)
        _packet(d, 640, 350, 300, 400, 63, band=AMBER, stamp='wheat')
        # a hand coming in from the right edge, gripping it -- cropped by the
        # frame edge so it reads as an arm reaching in, not a floating paw.
        PA.hand_stroke(d, [(1330, 560), (820, 470)], (232, 202, 172), 66,
                       closed=False, seed=64, wavelength=170.0)
        PA.hand_stroke(d, [(1330, 560), (820, 470)], INK, 5, closed=False,
                       seed=65, wavelength=170.0)
        for k in range(3):
            PA.hand_stroke(d, [(880 + k * 42, 452 + k * 10), (930 + k * 42, 546)],
                           (232, 202, 172), 30, closed=False,
                           seed=66 + k, wavelength=50.0)
        D.draw_label(tile, 'one sample', center=(640, 640), color=INK, size=34)
    els.append(card(9, 10, c_packet_hand))
    els.append(cap(9, 300, 660, size=30))

    # ---- b10  a million of them -------------------------------------------- #
    def c_million(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 69, wall=(66, 72, 84), floor=(48, 54, 64))
        # the corridor of shelves narrowing into the dark
        for k in range(6):
            t = k / 5.0
            hw = 700 - 460 * t
            _shelf(d, 640 - hw, 640 + hw, 250 + k * 74, 70 + k, h=120,
                   packets=max(3, 11 - k * 2))
        g = PA.ellipse_pts(640, 480, 130, 96, n=48)
        PA.fill_poly(tile, g, (26, 30, 38), seed=76, value=0.0)
        D.draw_number(tile, '1,000,000', center=(640, 470), color=VT.LABEL_YELLOW,
                      size=104)
    els.append(card(10, 11, c_million))
    els.append(cap(10, W // 2, 700, size=30, fill=VT.LABEL_YELLOW))

    # ---- b11  five crops, five packets ------------------------------------- #
    def c_crops(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 77, wall=(80, 88, 100), warm=(104, 90, 58))
        _shelf(d, -60, W + 60, 600, 78, h=210, packets=5)
        kinds = ['wheat', 'rice', 'barley', 'bean', 'millet']
        names = ['WHEAT', 'RICE', 'BARLEY', 'BEAN', 'MILLET']
        for i, (k, nm) in enumerate(zip(kinds, names)):
            cx = 128 + i * 256
            _packet(d, cx, 470, 168, 250, 80 + i * 3, band=AMBER, stamp=k)
            D.draw_label(tile, nm, center=(cx, 350), color=INK, size=30)
    els.append(card(11, 12, c_crops))
    els.append(cap(11, W // 2, 700, size=30))

    # ---- b12  a copy, and the original still in the field ------------------ #
    def c_copy(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (150, 178, 202), seed=91, value=0.05)
        PA.fill_rect(tile, [0, 470, W, H], (150, 172, 128), seed=92, value=0.07)
        PA.paper_overlay(tile, seed=93)
        # left: the vault copy, in its cold box
        PA.fill_rect(tile, [40, 120, 560, 690], (96, 106, 120), seed=94,
                     value=0.07)
        PA.hand_stroke(d, [(40, 120), (560, 120), (560, 690), (40, 690)], INK,
                       7, closed=True, seed=95, wavelength=160.0)
        D.draw_label(tile, 'COPY', center=(300, 180), color=VT.LABEL_YELLOW,
                     size=46)
        _packet(d, 300, 400, 200, 290, 96, band=AMBER, stamp='wheat')
        # right: the original, still standing in its own field
        for k in range(7):
            x = 700 + k * 84
            PA.hand_stroke(d, [(x, 690), (x + 8, 520 - (k % 3) * 30)], LEAF, 7,
                           closed=False, seed=100 + k, wavelength=60.0)
            for j in range(3):
                PA.hand_stroke(d, [(x + 4, 560 - j * 40), (x + 44, 540 - j * 40)],
                               LEAF, 5, closed=False, seed=110 + k * 3 + j,
                               wavelength=40.0)
        D.draw_label(tile, 'ORIGINAL', center=(980, 180), color=INK, size=46)
        _packet(d, 960, 640, 150, 210, 120, band=AMBER, stamp='wheat')
    els.append(card(12, 13, c_copy))
    els.append(cap(12, W // 2, 700, size=30))

    # ---- b13  the character: the original stays home ----------------------- #
    # Cropped IN, not placed on: the head runs off the top and left edges.
    def c_stays_home(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 214, 224), seed=125, value=0.05)
        PA.paper_overlay(tile, seed=126)
        SC.closeup(d, 470, 340, 230, 'skeptic', 127)
        D.draw_bubble(tile, 'the original\nstays home', (790, 130),
                      tail_to=(640, 400), font_size=30, max_w=420)
    els.append(card(13, 14, c_stays_home, kind='character'))
    els.append(cap(13, 300, 660, size=32))

    # ---- b14  every nation has one on file --------------------------------- #
    def c_globe_packets(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 216, 228), seed=131, value=0.05)
        PA.paper_overlay(tile, seed=132)
        # the globe is deliberately off-centre right and CROPPED by the bottom
        # and right edges, so it is a world filling the frame
        _globe(d, 760, 430, 330, 133)
        for k, (gx, gy) in enumerate(((0.42, -0.42), (-0.30, -0.20),
                                      (-0.10, 0.34), (0.30, 0.20),
                                      (0.56, 0.30), (-0.48, 0.06),
                                      (0.08, -0.10), (0.66, -0.06))):
            _packet(d, 760 + gx * 330, 430 + gy * 330, 76, 104, 134 + k,
                    band=AMBER, stamp='wheat')
        D.draw_label(tile, 'CROP INSURANCE', center=(300, 200), color=INK,
                     size=40)
    els.append(card(14, 15, c_globe_packets))
    els.append(cap(14, 300, 660, size=30, fill=AMBER))

    # ---- b15  minus eighteen ------------------------------------------------ #
    def c_thermo(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 141, wall=(74, 82, 94), warm=(96, 84, 56))
        S.thermometer(d, 420, 690, 620, 0.22, seed=142, hot=False)
        D.draw_number(tile, '-18', center=(880, 300), color=VT.LABEL_RED,
                      size=180)
        D.draw_label(tile, 'DEGREES C', center=(880, 430), color=VT.LABEL_RED,
                     size=52)
        D.draw_label(tile, '0', center=(520, 200), color=INK, size=34)
        D.draw_arrow(tile, (880, 480), (700, 560), color=VT.LABEL_RED, width=10,
                     head=46)
    els.append(card(15, 16, c_thermo))
    els.append(cap(15, 300, 690, size=30, fill=VT.LABEL_RED))

    # ---- b16  colder than any farm freezer --------------------------------- #
    def c_freezers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 145, wall=(84, 92, 104), floor=(62, 68, 78))
        # left: an ordinary domestic chest freezer, small and domestic
        chest = [(120, 300), (520, 300), (520, 640), (120, 640)]
        PA.fill_poly(tile, chest, (222, 224, 226), seed=146, value=0.07)
        PA.hand_stroke(d, chest, INK, 7, closed=True, seed=147, wavelength=150.0)
        PA.hand_stroke(d, [(120, 380), (520, 380)], INK, 5, closed=False,
                       seed=148, wavelength=110.0)
        D.draw_label(tile, 'FARM FREEZER', center=(320, 250), color=INK,
                     size=32)
        D.draw_label(tile, '-18', center=(320, 500), color=INK, size=52)
        # right: the vault's inner door, three times the size, running off the
        # right edge -- so the scale comparison is the composition, not a caption
        door = [(700, 200), (1360, 200), (1360, 690), (700, 690)]
        PA.fill_poly(tile, door, STEEL, seed=149, value=0.07)
        PA.hand_stroke(d, door, INK, 8, closed=True, seed=150, wavelength=170.0)
        PA.hand_stroke(d, [(740, 236), (1320, 236)], (110, 116, 126), 6,
                       closed=False, seed=151, wavelength=150.0)
        for k in range(4):
            y = 280 + k * 96
            d.ellipse([1240, y, 1290, y + 50], fill=(70, 76, 86))
        PA.hand_stroke(d, [(1180, 400), (1180, 620)], INK, 12, closed=False,
                       seed=152, wavelength=90.0)
        D.draw_label(tile, 'VAULT', center=(980, 150), color=VT.LABEL_RED,
                     size=40)
        D.draw_number(tile, '-18', center=(1000, 470), color=VT.LABEL_RED,
                      size=110)
    els.append(card(16, 17, c_freezers))
    els.append(cap(16, W // 2, 700, size=30))

    # ---- b17  one packet, very large, in the cold -------------------------- #
    def c_frost_packet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 155, wall=(70, 78, 90), floor=(52, 58, 68))
        _shelf(d, -80, W + 80, 620, 156, h=230, packets=7)
        # the subject is drawn big enough to bleed off the right edge
        _packet(d, 760, 330, 640, 480, 157, band=AMBER, stamp='wheat')
        for k in range(46):
            a = (k * 2.399) % 6.283
            rr = 60 + (k * 41) % 300
            x = 760 + rr * math.cos(a) * 1.1
            y = 330 + rr * math.sin(a) * 0.62
            if 440 < x < 1080 and 100 < y < 560:
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(236, 246, 252))
        D.draw_label(tile, 'CENTURIES', center=(640, 690), color=INK, size=40)
    els.append(card(17, 18, c_frost_packet))
    els.append(cap(17, 300, 150, size=30))

    # ---- b18  the plan: four doors, and a man drawing them ---------------- #
    def c_plan(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 161, wall=(72, 80, 92), floor=(54, 60, 70),
                  warm=(96, 86, 58))
        # four doors receding down the corridor. The outermost door's heavy frame
        # used to top out at y=19, driving a full-width INK bar straight through
        # the persistent "Svalbard" title (band_intrusions read b18 at 2777px).
        # Dropping the nest and trimming the tallest leaf puts the top frame at
        # y=107, clear of the band; the receding rhythm is unchanged.
        for k, (hw, hh, y) in enumerate(((360, 190, 316), (290, 172, 366),
                                          (222, 134, 420), (160, 98, 470))):
            _doorway(d, 640, y, 162 + k * 4, w=hw * 0.55, h=hh,
                     colour=(58, 64, 76) if k else (72, 78, 90))
        SC.fullbody(d, 300, 700, 400, pose='pointing', expression='deadpan',
                    seed=170)
        board = [(880, 250), (1230, 250), (1230, 620), (880, 620)]
        PA.fill_poly(tile, board, (238, 238, 232), seed=171, value=0.05)
        PA.hand_stroke(d, board, INK, 6, closed=True, seed=172, wavelength=140.0)
        for k in range(4):
            y = 310 + k * 74
            PA.hand_stroke(d, [(910, y), (1200, y)], INK, 4, closed=False,
                           seed=173 + k, wavelength=80.0)
    els.append(card(18, 19, c_plan, kind='character'))
    els.append(cap(18, W // 2, 690, size=30, fill=(214, 224, 236)))

    # ---- b19  the doors shut, frost on them, held dead centre --------------- #
    def c_shut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 177, wall=(58, 64, 76), floor=(44, 50, 60))
        SC.title_backdrop(tile, 1177, col=TITLE_COURSE)
        # The shut door's heavy frame used to top out at y=41, cutting a full-width
        # INK bar straight through the persistent title (band_intrusions read b19
        # at 2241px). The whole door assembly -- frame, bar, knob and the frost
        # that radiates from its centre -- drops 50px as a unit, putting the top
        # frame at y=91, clear of the band, with the card still one composition.
        _doorway(d, 640, 410, 178, w=330, h=290, colour=(76, 82, 94))
        PA.hand_stroke(d, [(310, 410), (970, 410)], (44, 48, 58), 8,
                       closed=False, seed=179, wavelength=150.0)
        d.ellipse([910, 386, 962, 438], fill=INK)
        # frost creeping across the steel -- short radiating crystal strokes
        for k in range(70):
            a = (k * 2.399) % 6.283
            rr = 40 + (k * 29) % 300
            x = 640 + rr * math.cos(a) * 1.15
            y = 410 + rr * math.sin(a) * 0.70
            if abs(x - 640) < 320 and abs(y - 410) < 280:
                PA.hand_stroke(d, [(x, y), (x + 22 * math.cos(a + 0.7),
                                             y + 22 * math.sin(a + 0.7))],
                               (222, 236, 244), 4, closed=False,
                               seed=180 + k, wavelength=40.0)
    els.append(card(19, 20, c_shut))
    els.append(cap(19, W // 2, 690, size=30, fill=(214, 224, 236)))

    # ---- b20  the whole mountain, grey, one lit room ----------------------- #
    def c_mountain_grey(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 185, warm_chamber=True)
        # everything greyed back except the one chamber
        veil = [(0, 0), (W, 0), (W, 470), (0, 470)]
        PA.fill_poly(tile, veil, (120, 124, 130), seed=186, value=0.05,
                     alpha=140) if False else None
        D.draw_label(tile, '2008', center=(200, 150), color=VT.LABEL_RED,
                     size=64)
        D.draw_arrow(tile, (330, 190), (860, 400), color=INK, width=10, head=46)
    els.append(card(20, 21, c_mountain_grey))
    els.append(cap(20, W // 2, 700, size=30))

    # ---- b21  meltwater coming in at the door  [MOTION] -------------------- #
    # This is one of the two beats where the narrator says something MOVES, so
    # this card is the chapter's one motion beat. The flood pool rises slowly.
    def c_meltwater(tile, fw, fh, level=0.0):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 191, snow=(216, 224, 232))
        _mountain(d, 192, crest=250, base=HZ + 6)
        _wedge(d, 520, 330, 193, w=240, h=170)
        _doorway(d, 520, 440, 194, w=145, h=190, colour=(44, 50, 60))
        # the channel: a brown meltwater run cutting the snow straight at the door
        chan = [(360, 720), (640, 720), (610, 520), (598, 470), (560, 470),
                (520, 540), (470, 560)]
        PA.fill_poly(tile, chan, WATER, seed=195, value=0.07)
        PA.hand_stroke(d, chan[:1] + chan[2:], INK, 5, closed=False, seed=196,
                       wavelength=110.0)
        if level > 0.0:
            flood = [(520 - 145, 440 + 190 * (1.0 - level)),
                     (520 + 145, 440 + 190 * (1.0 - level)),
                     (520 + 145, 440 + 190), (520 - 145, 440 + 190)]
            PA.fill_poly(tile, flood, WATER, seed=197, value=0.07)
        D.draw_arrow(tile, (300, 660), (450, 570), color=RED, width=10,
                     head=46)
    els.append(card(21, 22, c_meltwater, motion='rise'))

    def c_melt_water(tile, fw, fh, level=1.0):
        return c_meltwater(tile, fw, fh, level=level)
    els.append(card(22, 23, c_melt_water, motion='rise'))
    els.append(cap(21, 980, 660, size=30, fill=RED))
    els.append(cap(22, 980, 660, size=30, fill=RED))

    # ---- b22  water standing inside the tunnel ----------------------------- #
    def c_water_wall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 201, wall=(62, 70, 82), floor=(48, 54, 64))
        # The doorway's heavy frame used to top out at y=55, clipping the persistent
        # title band (band_intrusions read b23 at 1203px). Dropping the door 55px
        # puts the frame top at y=110, clear of the band, and it stays half behind
        # the water wall exactly as before.
        _doorway(d, 640, 385, 202, w=300, h=250, colour=(70, 76, 88))
        # the flood: a standing wall of meltwater, door half behind it
        wallw = [(300, 720), (300, 430), (1000, 400), (1000, 720)]
        PA.fill_poly(tile, wallw, WATER, seed=203, value=0.07)
        PA.hand_stroke(d, wallw[:3], (156, 186, 200), 7, closed=False,
                       seed=204, wavelength=170.0)
        for k in range(9):
            x = 330 + k * 78
            PA.hand_stroke(d, [(x, 430 + k % 3 * 12), (x + 40, 470 + k % 3 * 12)],
                           (156, 186, 200), 5, closed=False, seed=210 + k,
                           wavelength=60.0)
    els.append(card(23, 24, c_water_wall))
    els.append(cap(23, W // 2, 200, size=32, fill=(198, 222, 236)))

    # ---- b23  eight hundred tonnes ----------------------------------------- #
    def c_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 221, wall=(58, 66, 78), floor=(46, 52, 62))
        wallw = [(-40, 720), (-40, 400), (W + 40, 380), (W + 40, 720)]
        PA.fill_poly(tile, wallw, WATER, seed=222, value=0.07)
        PA.hand_stroke(d, [(-40, 400), (W + 40, 380)], (156, 186, 200), 7,
                       closed=False, seed=223, wavelength=180.0)
        D.draw_number(tile, '800', center=(430, 300), color=VT.LABEL_YELLOW,
                      size=190)
        D.draw_label(tile, 'TONNES', center=(980, 300), color=VT.LABEL_YELLOW,
                     size=104)
    els.append(card(24, 25, c_tonnes))
    els.append(cap(24, W // 2, 690, size=30, fill=VT.LABEL_YELLOW))

    # ---- b25  cut off: barricaded, and one small figure above -------------- #
    def c_cut_off(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 225, snow=(206, 216, 226))
        _mountain(d, 226, crest=250, base=HZ + 40)
        _wedge(d, 520, 380, 227, w=260, h=180)
        _doorway(d, 520, 490, 228, w=150, h=190, colour=(44, 50, 60))
        _flood_gate(d, 520, 480, 229)
        SC.fullbody(d, 1010, 400, 150, pose='armsup', expression='worried',
                    seed=230)
        D.draw_label(tile, '2016', center=(230, 200), color=VT.LABEL_RED,
                     size=68)
    els.append(card(25, 26, c_cut_off, kind='character'))
    els.append(cap(25, 300, 690, size=30))

    # ---- b26  the character: the seeds were fine --------------------------- #
    def c_fine(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 210, 224), seed=231, value=0.05)
        PA.paper_overlay(tile, seed=232)
        SC.closeup(d, 520, 330, 240, 'deadpan', 233)
        D.draw_bubble(tile, 'the seeds\nwere fine', (830, 120), tail_to=(690, 390),
                      font_size=30, max_w=400)
    els.append(card(26, 27, c_fine, kind='character'))
    els.append(cap(26, 320, 660, size=32))

    # ---- b27  the chamber, dry, above the waterline ------------------------ #
    def c_waterline(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 237, water_level=0.34)
        D.draw_arrow(tile, (300, 300), (300, 430), color=VT.LABEL_RED, width=9,
                     head=42)
        D.draw_label(tile, 'ABOVE THE WATER', center=(300, 210), color=VT.LABEL_RED,
                     size=34)
    els.append(card(27, 28, c_waterline))
    els.append(cap(27, 980, 130, size=30, fill=VT.LABEL_RED))

    # ---- b28  the same permafrost, thinning -------------------------------- #
    def c_thawing(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 243, ragged=True, melt_arrows=True, label='AND MELTING')
    els.append(card(28, 29, c_thawing))
    els.append(cap(28, W // 2, 690, size=32, fill=RED))

    # ---- b29  watched now -------------------------------------------------- #
    def c_camera(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 249, snow=(222, 230, 238))
        _mountain(d, 250, crest=280, base=HZ + 30)
        _wedge(d, 470, 400, 251, w=230, h=160)
        _doorway(d, 470, 500, 252, w=135, h=175, colour=(46, 52, 62))
        _camera(d, 830, 300, 110, 253)
        D.draw_arrow(tile, (1030, 260), (900, 320), color=INK, width=9, head=42)
        D.draw_label(tile, 'watched', center=(1150, 220), color=INK, size=36)
    els.append(card(29, 30, c_camera))
    els.append(cap(29, 300, 690, size=30))

    # ---- b30  the new tunnel being cut ------------------------------------- #
    def c_new_tunnel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 257, snow=(216, 226, 236))
        _mountain(d, 258, crest=260, base=HZ + 60)
        _wedge(d, 330, 400, 259, w=190, h=140)
        _doorway(d, 330, 486, 260, w=118, h=155, colour=(46, 52, 62))
        # the new mouth: raw concrete, no wedge, cut lower down the slope
        raw = [(760, 420), (1080, 420), (1040, 640), (800, 640)]
        PA.fill_poly(tile, raw, CONCRETE, seed=261, value=0.07)
        PA.hand_stroke(d, raw, INK, 7, closed=True, seed=262, wavelength=150.0)
        _doorway(d, 920, 530, 263, w=100, h=125, colour=(52, 58, 70))
        _excavator(d, 690, 620, 90, 264)
        D.draw_label(tile, 'NEW TUNNEL', center=(920, 360), color=VT.LABEL_RED,
                     size=34)
    els.append(card(30, 31, c_new_tunnel))
    els.append(cap(30, W // 2, 700, size=30))

    # ---- b31  lights on the snow, night and day ---------------------------- #
    def c_lights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 267)
        SC.title_backdrop(tile, 1267, col=TITLE_COURSE)
        _mountain(d, 269, crest=330, base=HZ + 6)
        _light_wedge(d, 430, 120, HZ - 4, 210, 271)
        _light_wedge(d, 900, 120, HZ - 4, 190, 273)
        SC.fullbody(d, 664, HZ + 8, 230, pose='standing', expression='skeptic',
                    seed=275)
    els.append(card(31, 32, c_lights, kind='character'))
    els.append(cap(31, W // 2, 700, size=32, fill=AMBER_LT))

    # ---- b32  still a bunker ----------------------------------------------- #
    def c_bunker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 206, 216), seed=277, value=0.05)
        PA.paper_overlay(tile, seed=278)
        # Cropped in from the chest up and cropped by the BOTTOM edge. The head
        # used to run off the TOP edge (cy=300 put the rim's outer edge at
        # y=51), which drove the head arc straight through the persistent
        # "Svalbard" title -- band_intrusions() read b32 at 2012px. Dropping
        # the whole bust to cy=365 puts the rim's top at y=114, clear of the
        # band, and the crop now happens at the bottom, which is free.
        SC.closeup(d, 640, 365, 250, 'deadpan', 279, shoulder=1.35)
        D.draw_bubble(tile, 'a bunker', (180, 480), tail_to=(520, 520),
                      font_size=34, max_w=340)
    els.append(card(32, 33, c_bunker, kind='character'))
    els.append(cap(32, 300, 690, size=32))

    # ---- b33  catastrophe, moving in --------------------------------------- #
    # Deliberately almost unchanged from the b01 hook, except for the red line.
    def c_redline(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 281)
        SC.title_backdrop(tile, 1281, col=TITLE_COURSE)
        _mountain(d, 283, crest=300, base=HZ + 6)
        _light_wedge(d, 760, 120, HZ - 4, 190, 285)
        PA.hand_stroke(d, [(-40, 610), (320, 590), (660, 600), (1000, 580),
                           (1320, 596)], RED, 12, closed=False, seed=287,
                       wavelength=190.0)
        D.draw_label(tile, 'WARMING', center=(300, 500), color=RED, size=40)
    els.append(card(33, 34, c_redline))
    els.append(cap(33, W // 2, 700, size=32, fill=RED))

    # ---- b34  the slope, a few shades warmer ------------------------------- #
    def c_warming(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 291, sky_top=(44, 52, 70), sky_bot=(126, 136, 152),
                snow=(220, 222, 224))
        SC.title_backdrop(tile, 1291, col=TITLE_COURSE)
        _mountain(d, 293, crest=300, base=HZ + 6, snowline=False)
        # bare rock showing through where the snow used to be
        for k, (x0, y0, x1, y1) in enumerate(((120, 470, 460, 560),
                                              (700, 500, 1080, 596),
                                              (980, 400, 1260, 480))):
            bare = [(x0, y0), (x1, y0 - 30), (x1, y1), (x0, y1)]
            PA.fill_poly(tile, bare, (128, 122, 116), seed=294 + k, value=0.07)
            PA.hand_stroke(d, bare, INK, 5, closed=True, seed=298 + k,
                           wavelength=120.0)
        D.draw_number(tile, '-2.6 C', center=(640, 300), color=VT.LABEL_RED,
                      size=132)
        D.draw_label(tile, 'PER DECADE', center=(640, 400), color=VT.LABEL_RED,
                     size=54)
    els.append(card(34, 35, c_warming))
    els.append(cap(34, W // 2, 700, size=30, fill=RED))

    # ---- b35  for now: the packet in his hand ------------------------------ #
    def c_for_now(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (72, 82, 98), seed=301, value=0.06)
        PA.paper_overlay(tile, seed=302)
        SC.closeup(d, 430, 350, 250, 'deadpan', 303)
        _packet(d, 940, 470, 230, 320, 304, band=AMBER, stamp='wheat')
        PA.hand_stroke(d, [(1330, 640), (1040, 560)], (232, 202, 172), 60,
                       closed=False, seed=305, wavelength=150.0)
        D.draw_bubble(tile, 'for now', (830, 110), tail_to=(640, 420),
                      font_size=34, max_w=320)
    els.append(card(35, 36, c_for_now, kind='character'))
    els.append(cap(35, 300, 690, size=32))

    # There is deliberately NO post-beat finale card. An earlier version had
    # one -- card(36, 37, c_finale), a lit hall with the water line -- which
    # raised KeyError: 'b36' because the chapter has 35 beats. Placing it at
    # bend_of('b35') instead did not help: b35 ENDS AT duration_s, so the
    # element got at == until == 96.78 and a zero span, i.e. it still never
    # rendered. There is no time after the last spoken line to hold a visual,
    # so the chapter ends on b35 itself -- the presenter holding the seed
    # packet under the "for now" bubble, which is the stronger close anyway.

    return SC.finish(els, TITLE, clock, title_seed=41)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))
