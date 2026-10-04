# _cards.py — segment 7, Gliese 436 b ("the burning ice"). One module, all 10 beats.
#
# CONTRACT (matches work/segments/psrb1257/_cards_b*.py):
#   * module-level RENDERERS dict, keyed by EVERY beat id in script.json
#   * every fn signature fn(card, planet="Gliese 436 b") -> PIL RGB 1280x720
#   * layout A: rows 0..83 paper title strip via C._header, full-bleed art 84..719,
#     NO caption band; the floating caption is drawn by C._caption(...,70,652)
#   * 'void'  cards: C.void_backdrop + C._header(paper_band=True)  + theme='dark'
#   * 'cream' cards: full-bleed paper    + C._header(paper_band=False)+ theme='light'
#   * the character comes ONLY from card['stickman'] via C._draw_stickman
#   * every hero phrase goes through C.hero_word (it clamps INCLUDING the stroke)
#   * every wobble/stipple/starfield call takes an explicit seed -> byte-identical
#     re-renders. No global random state anywhere in this file.
#
# REGISTER: this segment is VOID (Register S) for 7 beats and CREAM (Register P)
# for 3, so BOTH themes appear. The character is cream-on-dark in space and
# dark-on-cream on the paint cards — never hardcoded black.
#
# GRADIENT DISCIPLINE: the single legal gradient in the whole segment is
# C._radial_core on the star (an emissive body). The ice planet, the ice cube,
# the pressure arrows, the gas streams, the phase diagram, the surface and the
# character are all FLAT fills + thick hand outlines.

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

# Path bootstrap so the module imports cleanly both under the frame generator
# (which puts work/ on sys.path itself) and standalone, as `python _cards.py`.
# work/ is two levels up from this file; this directory is one level up.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))   # .../work — the package root
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib.type as T
import lib.ink as K
import lib.cardframe as C

W, H = C.W, C.H

# ---------------------------------------------------------------------------
# The locked segment palette. See PALETTE_SPEC.md in this directory.
# cardframe.C.PAL belongs to segment 3 (PSR B1257+12) — this segment carries its
# own. Only genuinely generic helpers (void_backdrop / space_body / add_glow /
# _radial_core) are borrowed from the lib.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':   (18, 24, 30),     # #12181E frost-slate : all linework, header glyphs
    'paper': (240, 236, 220),  # #F0ECDC bone-cream  : title strip, cream cards
    'deep':  (6, 10, 16),      # #060A10 void        : every space field
    'frost': (168, 216, 232),  # #A8D8E8 glacier     : the ice, captions on deep
    'steam': (250, 252, 255),  # #FAFCFF white-blue  : supercritical core, starfield
    'ember': (240, 158, 52),   # #F09E34 hot amber   : the burning, the tail, alerts
    'abyss': (46, 62, 96),     # #2E3E60 deep indigo : pressure + gas, shapes only
}
INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
FROST = MY_PAL['frost']
STEAM = MY_PAL['steam']
EMBER = MY_PAL['ember']
ABYSS = MY_PAL['abyss']


# ---------------------------------------------------------------------------
# Curve helpers. lib.ink._smooth_open is documented as unusable in this codebase
# (its Catmull-Rom pad is short and it raises IndexError on 3+ point polylines),
# so every OPEN curve here is rebuilt locally from the same K.wobble_points
# engine and the same Catmull-Rom math, exactly as _cards_b4.py does.
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output)."""
    p = list(pts)
    if len(p) < 3:
        return list(p)
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
    """An OPEN hand-wobbled smooth curve. Returns the dense path."""
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    if len(dense) >= 2:
        draw.line(dense, fill=color, width=width, joint='curve')
    return dense


def _thick_curve(draw, points, fill, seed=0, width=24, wobble=2.0,
                 wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region.

    PIL wide lines grow hairline nubs at every near-duplicate Catmull-Rom vertex,
    so the stroke is built geometrically: offset the dense centreline by
    +/- half-width along its normal and fill the welded polygon.
    """
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    n = len(dense)
    hw = width / 2.0
    outer, inner = [], []
    for i in range(n):
        a = dense[max(0, i - 1)]
        b = dense[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        outer.append((dense[i][0] + nx * hw, dense[i][1] + ny * hw))
        inner.append((dense[i][0] - nx * hw, dense[i][1] - ny * hw))
    region = outer + inner[::-1]
    draw.polygon(region, fill=fill)
    return region


def _vline(draw, x, y0, y1, color, width=2, seed=0, wobble=1.0):
    """A short hand-wobbled vertical rule."""
    mid = (y0 + y1) / 2.0
    return _open_curve(draw, [(x, y0), (x, mid), (x, y1)], color, width,
                       seed=seed, wobble=wobble, wavelength=60.0)


def _hrule(draw, y, x0, x1, color, width=2, seed=0, wobble=1.0):
    """A short hand-wobbled horizontal rule."""
    mid = (x0 + x1) / 2.0
    return _open_curve(draw, [(x0, y), (mid, y), (x1, y)], color, width,
                       seed=seed, wobble=wobble, wavelength=90.0)


def _arrow(draw, tip, ang_deg, length, color, width=K.DETAIL, seed=0,
           head=16.0):
    """A hand-drawn arrow: a wobbled shaft with two barbs. Open curves only."""
    a = math.radians(ang_deg)
    tail = (tip[0] - length * math.cos(a), tip[1] - length * math.sin(a))
    _open_curve(draw, [tail, ((tail[0] + tip[0]) / 2.0,
                              (tail[1] + tip[1]) / 2.0), tip],
                color, width, seed=seed, wobble=1.0, wavelength=70.0)
    for sgn in (1, -1):
        b = math.radians(ang_deg + sgn * 148.0)
        _open_curve(draw, [(tip[0] - head * math.cos(b),
                            tip[1] - head * math.sin(b)), tip],
                    color, width, seed=seed + (7 if sgn > 0 else 11),
                    wobble=0.6, wavelength=40.0)


def _hard_edges(draw, pts, color, width, seed=0, waver=1.6, closed=False):
    """Draw a polygon as CRISP straight edges with a faint hand waver.

    K.draw_smooth runs a closed Catmull-Rom through its input points, so a
    hexagon always comes out as a rounded blob — right for an organic silhouette,
    wrong for a cube. And routing each edge through the spline adds overshoot
    loops. So this draws each edge as a plain two-segment line (corner, a
    perpendicularly-displaced midpoint, next corner) with NO spline: the box
    keeps hard corners while every edge still carries a slight hand bow.
    """
    n = len(pts)
    last = n if closed else n - 1
    rnd = random.Random(seed)
    for i in range(last):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        off = rnd.uniform(-waver, waver)
        mx, my = (x0 + x1) / 2.0 + nx * off, (y0 + y1) / 2.0 + ny * off
        draw.line([(x0, y0), (mx, my)], fill=color, width=width)
        draw.line([(mx, my), (x1, y1)], fill=color, width=width)


def _soft_wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=170.0,
               blur=18, outline=None, width=0):
    """A painterly FLAT-colour region with soft edges, on its own RGBA layer.

    Flat fill + blur, never a gradient: a crisp rectangle here is the CAD read
    the reference never has. Returns a new RGB image.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=rgb + (int(alpha),), outline=outline,
                  width=width, seed=seed, wobble=wobble,
                  wavelength=wavelength, closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _tiny(draw, text, cx, cy, fill, px=18):
    """Locked-family REGULAR annotation, centred, no stroke. Diagram labels only."""
    font = T.load_font_at(px, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    draw.text((cx - w / 2.0 - x0, cy - h / 2.0 - y0), text, font=font, fill=fill)


def _arc_pts(cx, cy, r, a0_deg, a1_deg, n=40):
    """Sample a circular arc. PIL angles: 0 = 3 o'clock, growing clockwise."""
    return [(cx + r * math.cos(math.radians(a0_deg + (a1_deg - a0_deg) * i / n)),
             cy + r * math.sin(math.radians(a0_deg + (a1_deg - a0_deg) * i / n)))
            for i in range(n + 1)]


# ---------------------------------------------------------------------------
# The one object this segment is about, drawn two ways.
# ---------------------------------------------------------------------------

def _stipple_disc(draw, cx, cy, r, color, seed=0, density=0.008, r_dot=1):
    """Deterministic stipple MASKED to a circle.

    K.stipple scatters over a rect, so its corner grains land outside a round
    body and read as confetti floating in space. This clips to the disc.
    """
    rnd = random.Random(seed)
    n = int(max(1, (2 * r) * (2 * r) * density))
    for _ in range(n):
        a = rnd.uniform(0, math.tau)
        rr = r * math.sqrt(rnd.random())
        draw.ellipse([cx + rr * math.cos(a) - r_dot, cy + rr * math.sin(a) - r_dot,
                      cx + rr * math.cos(a) + r_dot, cy + rr * math.sin(a) + r_dot],
                     fill=color)


def _ice_planet(draw, cx, cy, r, seed, melt=0.0, ring=True):
    """The burning-ice planet. FLAT glacier fill + thick ink keyline + wide
    latitude bands + a light clipped stipple. `melt` in 0..1 flattens and fades
    the bands toward the equator — `melt=1.0` is the supercritical card's no
    seam. Never a gradient (PALETTE_SPEC denylist).

    The bands are drawn as WIDE, nearly full-width horizontal ellipses at
    different latitudes, not as concentric rings: a set of concentric ellipses
    inside a circle reads as a pond ripple / bullseye target, which is the
    defect the canon warns about, not a planet.
    """
    K.draw_disc(draw, cx, cy, r, fill=FROST, outline=INK, width=K.OUTLINE,
                seed=seed, wobble=2.4)
    rnd = random.Random(seed + 5)
    for b, (yr, hh) in enumerate(((-0.34, 0.075), (0.04, 0.085), (0.40, 0.065))):
        pts = []
        for s in range(48):
            a = math.tau * s / 48.0
            wob = 1.0 + 0.035 * math.sin(2 * a + rnd.uniform(0, 3))
            pts.append((cx + r * 0.86 * math.cos(a) * wob,
                        cy + r * (yr + hh * math.sin(a) * (1.0 - 0.5 * melt))))
        shade = ABYSS if melt < 0.5 else STEAM
        _open_curve(draw, pts, shade, width=K.DETAIL if melt < 0.5 else K.FINE,
                    seed=seed + 20 + b, wobble=1.0, wavelength=140.0)
    # re-stroke the keyline on top of the bands so their ends never poke past
    # the limb
    K.draw_disc(draw, cx, cy, r, fill=None, outline=INK, width=K.OUTLINE,
                seed=seed + 1, wobble=2.4)
    # a lit crescent hugging the upper-left limb — a FLAT shape, not a gradient.
    # Built as a true crescent: the outer edge rides the planet's own circle
    # (0.86r arc, upper-left quadrant) and the inner edge is a shallower arc
    # pulled toward the centre, so the shape tapers to points at both ends
    # instead of rounding into the leaf/almond a 5-point blob gave.
    a0, a1 = math.radians(202.0), math.radians(276.0)
    outer = [(cx + r * 0.94 * math.cos(a0 + (a1 - a0) * s / 16.0),
              cy + r * 0.94 * math.sin(a0 + (a1 - a0) * s / 16.0))
             for s in range(17)]
    inner = [(cx + r * 0.80 * math.cos(a1 - (a1 - a0) * s / 16.0),
              cy + r * 0.80 * math.sin(a1 - (a1 - a0) * s / 16.0))
             for s in range(17)]
    K.draw_smooth(draw, outer + inner, fill=STEAM, outline=None, seed=seed + 40,
                  wobble=1.8, wavelength=110.0)
    # sparse grain — painterly tooth, not dirt. High-contrast dark stipple at
    # any real density reads as mould, so it stays well under 1 grain per 400px.
    _stipple_disc(draw, cx, cy, r * 0.88, ABYSS, seed=seed + 60, density=0.0012)
    if ring:
        draw.ellipse([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5],
                     outline=EMBER + (200,), width=K.FINE)


def _star(img, cx, cy, r, seed):
    """The host star: an EMISSIVE body, so C._radial_core is the one legal
    gradient in this segment. Soft glow kept low so its circular cutoff edge
    does not read as a bubble; two flat halo rings carry the rest."""
    C._radial_core(img, int(cx), int(cy), int(r),
                   [(255, 255, 255), EMBER, (120, 48, 8)], glow=0.42)
    d = ImageDraw.Draw(img, 'RGBA')
    # one hand-wobbled open arc, not two perfect concentric circles — a pair of
    # true circles around a disc reads as a targeting reticle, which is the
    # opposite of the painterly reference.
    rr = int(r * 1.38)
    _open_curve(d, [(cx + rr * math.cos(math.radians(a)),
                     cy + rr * math.sin(math.radians(a)))
                    for a in range(-118, 119, 16)],
                EMBER + (52,), width=K.DETAIL, seed=seed + 9, wobble=2.6,
                wavelength=190.0)
    return d


# ---------------------------------------------------------------------------
# Card scaffolding
# ---------------------------------------------------------------------------

def _void_card(seed, stars=126):
    """A void (space-register) frame. The starfield gradient is the only
    background gradient and it is built into C.void_backdrop."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars)
    return img


def _finish(img, card, planet, paper_band, dark_bg):
    """Layout-A tail: title strip, the schedule-driven character, one caption."""
    C._header(img, planet, paper_band=paper_band)
    C._draw_stickman(img, card, theme='dark' if dark_bg else 'light')
    C._caption(img, card['caption'], 70, 652, dark_bg=dark_bg)
    return img


# ===========================================================================
# B1 HOOK — hook_burning_ice.  VOID.  "Here is a planet made of ice. / And it
# is on fire, and it does not melt."  One focal point: the ice planet, sitting
# in a cold blue wash while a hot ember ring marks the burning. The character
# (deadpan, one hand out toward it) is at the schedule's own position.
# ===========================================================================

def render_hook_burning_ice(card, planet="Gliese 436 b"):
    img = _void_card(seed=101, stars=126)

    # a cold halo wash behind the planet so it sits IN the field, not on it
    img = _soft_wash(img,
                     [(700, 150), (960, 132), (1148, 250), (1140, 468),
                      (900, 546), (688, 452), (664, 268)],
                     FROST, 34, seed=1101, wobble=18.0, blur=28)
    d = ImageDraw.Draw(img, 'RGBA')

    # the planet, lit from the upper left, with a thin ember limb ring
    _ice_planet(d, 900, 330, 168, seed=101)

    # the fire: three flat ember licks licking up off the lit limb
    for i, (ox, hh, sd) in enumerate(((-96, 74, 1110), (-16, 104, 1111), (72, 62, 1112))):
        _thick_curve(d, [(900 + ox, 330 + 132), (900 + ox - 6, 330 + 132 - hh * 0.6),
                         (900 + ox + 10, 330 + 132 - hh)],
                     EMBER, seed=sd, width=15, wobble=4.0, wavelength=70.0)

    d = ImageDraw.Draw(img, 'RGBA')
    _tiny(d, 'ICE', 900, 96, FROST, px=20)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# B2 THE WORLD — world_size.  VOID.  "about the size of Neptune / a giant world,
# made almost entirely of water."  The planet is the SUBJECT at full size, with
# a bone scale bar and a NEPTUNE stamp; the character is awed, hands up.
# ===========================================================================

def render_world_size(card, planet="Gliese 436 b"):
    img = _void_card(seed=201, stars=118)

    img = _soft_wash(img,
                     [(560, 130), (900, 108), (1120, 250), (1112, 500),
                      (860, 580), (588, 470), (546, 268)],
                     ABYSS, 62, seed=2101, wobble=20.0, blur=30)
    d = ImageDraw.Draw(img, 'RGBA')

    # the Neptune-sized world, banded like a gas giant, drawn flat
    _ice_planet(d, 848, 336, 218, seed=201)

    # a scale bar under the planet: one bone rule with end ticks
    _hrule(d, 596, 636, 1060, FROST, width=K.DETAIL, seed=2110)
    for sx in (636, 848, 1060):
        _vline(d, sx, 584, 608, FROST, width=K.DETAIL, seed=2120 + sx % 7)
    _tiny(d, 'ONE NEPTUNE', 848, 630, FROST, px=20)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# B3 THE PARADOX — hook_no_sense.  CREAM / Register P.  "Now here is the part
# that makes no sense. / Ice should melt."  A hand-drawn CUBE of ice with a
# drip running off it, flat fills and thick outlines, on a cream ground. The
# character (shrugging, zigzag mouth) stands on the cream at his own position.
# ===========================================================================

def render_hook_no_sense(card, planet="Gliese 436 b"):
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # a cool wash behind the cube so the card has a stage, not an empty field
    img = _soft_wash(img,
                     [(700, 140), (1010, 128), (1150, 270), (1128, 486),
                      (900, 544), (690, 452)],
                     ABYSS, 34, seed=3101, wobble=18.0, blur=26)
    d = ImageDraw.Draw(img)

    # the ice cube. A cube is a HARD-EDGED object, so it is drawn as three flat
    # polygons with individually-stroked edges (see _hard_edges) — a closed
    # Catmull-Rom through a hexagon rounds it into a barrel every time.
    #   A B C   top-back-left, top, top-back-right
    #    \ /    M = front-top corner
    #   E M F   bottom-left, front, bottom-right
    #   / \
    #  D
    cx, cy, s = 900, 306, 158
    A = (cx - s, cy - s * 0.46)
    B = (cx, cy - s * 0.74)
    Cc = (cx + s, cy - s * 0.46)
    M = (cx, cy - s * 0.10)
    E = (cx - s, cy + s * 0.50)
    D = (cx, cy + s * 0.84)
    F = (cx + s, cy + s * 0.50)
    # top face fill (light) then the two side faces (glacier)
    d.polygon([A, B, Cc, M], fill=STEAM)
    d.polygon([A, M, D, E], fill=FROST)
    d.polygon([M, Cc, F, D], fill=FROST)
    # silhouette + the three inner edges, all sharing their corner points
    _hard_edges(d, [A, B, Cc, F, D, E], INK, K.OUTLINE, seed=3102, closed=True)
    _hard_edges(d, [A, M, Cc], INK, K.OUTLINE, seed=3103)
    _hard_edges(d, [M, D], INK, K.OUTLINE, seed=3104)

    # the drip: it should NOT be able to leave — a fat drop off the bottom-right
    # corner and a flat pool it lands in, both tucked clear of the hero word.
    drip = [(F[0] - 6, F[1] + 6), (F[0] + 14, F[1] + 34), (F[0] + 10, F[1] + 50)]
    _open_curve(d, drip, FROST, width=K.OUTLINE, seed=3105, wobble=0.8)
    K.draw_smooth(d, [(F[0] + 2, F[1] + 48), (F[0] + 20, F[1] + 44),
                      (F[0] + 32, F[1] + 58), (F[0] + 8, F[1] + 66)],
                  fill=FROST, outline=INK, width=K.DETAIL, seed=3106, wobble=1.6)
    K.draw_smooth(d, [(cx + s * 0.30, cy + s * 1.28), (cx + s * 0.86, cy + s * 1.18),
                      (cx + s * 1.26, cy + s * 1.34), (cx + s * 0.76, cy + s * 1.48)],
                  fill=ABYSS, outline=INK, width=K.DETAIL, seed=3107, wobble=2.4,
                  wavelength=90.0)

    C.hero_word(d, 'ICE MELTS', 640, 596, ABYSS, stroke_rgb=INK, stroke_width=3,
                px=64, margin=40, y_max=624)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# B4 THE CRUSH — pressure_and_heat.  VOID.  "under crushing pressure from its
# own gravity / its star keeps cooking it from close range."  TWO forces, one
# picture: six ABYSS pressure arrows crush inward from every side while the host
# star glares from the right and throws three EMBER heat arrows back at it.
# The character shields his eyes.
# ===========================================================================

def render_pressure_and_heat(card, planet="Gliese 436 b"):
    img = _void_card(seed=401, stars=120)

    px, py, pr = 560, 372, 158

    # the star first, so the planet and arrows sit on top of its halo
    d = _star(img, 1096, 232, 74, seed=401)

    # --- PRESSURE: six flat FROST arrows inward. Cold crush vs hot heat is the
    # card's whole colour code; the arrows are thin lines, so they take the
    # high-contrast cold accent rather than the deep indigo (which vanished
    # into the void field). ---
    for ang in (150, 210, 90, 270, 30, 330):
        a = math.radians(ang)
        tip = (px + (pr + 22) * math.cos(a), py + (pr + 22) * math.sin(a))
        _arrow(d, tip, (ang + 180) % 360, 96, FROST, width=K.DETAIL,
               seed=4100 + ang % 97, head=18.0)
    _tiny(d, 'CRUSH', px, py - pr - 58, FROST, px=20)

    # --- HEAT: three flat EMBER arrows running from the star's limb to the
    # planet's limb. The earlier version aimed them along absolute angles
    # (196/152/174) and laid the tails at a fixed 128px from the star, which
    # parked the whole set in the empty void on the FAR side of the planet —
    # heat visibly flowing away from its source. These are derived from the
    # actual star->planet vector instead. ---
    sx0, sy0 = 1096, 232
    base = math.degrees(math.atan2(py - sy0, px - sx0))
    for k, off in enumerate((-11.0, 0.0, 11.0)):
        a = math.radians(base + off)
        ux, uy = math.cos(a), math.sin(a)
        # u points star -> planet, so BOTH ends step back along -u: the tail
        # off the star's near limb, the head onto the planet's near limb.
        # Stepping along +u put the heads on the planet's FAR side.
        tail = (sx0 - 86 * ux, sy0 - 86 * uy)
        tip = (px - (pr + 34) * ux, py - (pr + 34) * uy)
        run = math.hypot(tip[0] - tail[0], tip[1] - tail[1])
        _arrow(d, tip, base + off, run, EMBER, width=K.DETAIL,
               seed=4200 + k, head=22.0)
    _tiny(d, 'HEAT', 1214, 372, EMBER, px=20)

    d = ImageDraw.Draw(img, 'RGBA')
    _ice_planet(d, px, py, pr, seed=401)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# B5 THE TRAP — no_choice.  CREAM / Register P.  "The water never gets to
# choose. / It cannot be solid. It cannot be liquid."  The subject is a PHASE
# DIAGRAM: SOLID and LIQUID lines that climb, cross, and dissolve into a blur
# band — a drawn diagram, not a UI widget. The character points at the crossing.
# ===========================================================================

def render_no_choice(card, planet="Gliese 436 b"):
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    ox, oy = 560, 540           # diagram origin (axes corner)

    # a soft frost wash behind the crossing so the card has a stage
    img = _soft_wash(img,
                     [(700, 180), (1000, 168), (1140, 320), (1116, 520),
                      (860, 566), (688, 460)],
                     FROST, 62, seed=5101, wobble=18.0, blur=40)
    d = ImageDraw.Draw(img)

    # axes
    _hrule(d, oy, 560, 1150, INK, width=K.DETAIL, seed=5110)
    _vline(d, ox, 560, 160, INK, width=K.DETAIL, seed=5111)

    # SOLID line — climbs hard then bends flat
    solid = [(ox + 40, oy - 10), (ox + 150, oy - 130), (ox + 250, oy - 250),
             (ox + 330, oy - 300), (ox + 390, oy - 308)]
    _open_curve(d, solid, INK, width=K.OUTLINE, seed=5120, wobble=2.0,
                wavelength=170.0)

    # LIQUID line — climbs gently then runs into the same place
    liq = [(ox + 40, oy - 10), (ox + 150, oy - 70), (ox + 250, oy - 160),
           (ox + 330, oy - 258), (ox + 390, oy - 300)]
    _open_curve(d, liq, ABYSS, width=K.OUTLINE, seed=5130, wobble=2.0,
                wavelength=170.0)

    # The blur band where the two stop being two things. This was a single
    # outlined polygon, and a hard-edged FROST shape floating on the diagram
    # read as a random amoeba rather than a dissolve. It is now a soft,
    # outline-free smear: overlapping blurred blobs plus a light disc field.
    img = _soft_wash(img,
                     [(ox + 430, oy - 350), (ox + 520, oy - 306),
                      (ox + 590, oy - 250), (ox + 540, oy - 190),
                      (ox + 440, oy - 200)],
                     FROST, 150, seed=5160, wobble=14.0, blur=34)
    d = ImageDraw.Draw(img)
    rnd = random.Random(5140)
    for i in range(20):
        bx = ox + 470 + rnd.randint(-56, 56)
        by = oy - 288 + rnd.randint(-52, 52)
        K.draw_disc(d, bx, by, rnd.randint(8, 16), fill=FROST, outline=None,
                    width=0, seed=5150 + i, wobble=1.4)

    _tiny(d, 'SOLID', ox + 210, oy - 336, INK, px=20)
    _tiny(d, 'LIQUID', ox + 128, oy - 150, ABYSS, px=20)
    _tiny(d, 'NEITHER', ox + 500, oy - 118, INK, px=20)

    C.hero_word(d, 'NO CHOICE', 1010, 604, EMBER, stroke_rgb=INK, stroke_width=3,
                px=64, margin=40, y_max=630)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# B6 THE STATE — supercritical.  VOID.  "Scientists call it supercritical. / No
# boundary between ice and steam."  ONE planet, drawn with melt=1.0: its strata
# have smeared into a single horizontal band with no seam, and the lit crescent
# has bloomed into a white-hot patch. A dashed EMBER ring cuts around the limb to
# mark where the boundary USED to be — the thing that is gone.
# ===========================================================================

def render_supercritical(card, planet="Gliese 436 b"):
    img = _void_card(seed=601, stars=124)

    # a soft atmospheric halo CONCENTRIC with the planet. This was a hexagon,
    # and even heavily blurred its straight sides read as a grey panel behind
    # the disc rather than as air around it.
    img = _soft_wash(img,
                     [(748 + 300 * math.cos(math.tau * s / 24.0),
                       336 + 300 * math.sin(math.tau * s / 24.0))
                      for s in range(24)],
                     FROST, 26, seed=6101, wobble=22.0, blur=52)
    d = ImageDraw.Draw(img, 'RGBA')

    cx, cy, r = 748, 336, 186
    _ice_planet(d, cx, cy, r, seed=601, melt=1.0, ring=False)

    # where the ice/steam boundary would have been: a dashed ember ring, no fill
    dd = ImageDraw.Draw(img, 'RGBA')
    for k in range(34):
        if k % 2:
            continue
        a0 = math.tau * k / 34.0
        a1 = math.tau * (k + 1) / 34.0
        rr = r + 14
        _open_curve(dd,
                    [(cx + rr * math.cos(a0), cy + rr * math.sin(a0)),
                     (cx + rr * math.cos(a1), cy + rr * math.sin(a1))],
                    EMBER + (215,), width=K.DETAIL, seed=6110 + k, wobble=0.5,
                    wavelength=40.0)

    _tiny(d, 'SUPERCRITICAL', cx, 108, FROST, px=20)
    _tiny(d, 'NO SEAM', cx, cy + r + 62, EMBER, px=20)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# B7 THE SURFACE — burning_torch.  CREAM / Register P.  "ice that flows like
# water and burns like a torch."  The subject is the SURFACE: a rippling
# half-solid half-liquid sea in flat EMBER and FROST, with a small ship
# half-sunk in it. The character stands on the cream at the left, awed.
# ===========================================================================

def render_burning_torch(card, planet="Gliese 436 b"):
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # the rippling surface: a FLAT ember sea. It runs OFF the bottom of the
    # frame on all three sides, so no polygon outline ever appears along the
    # bottom edge as a black band.
    crest = [(-90, 470), (60, 428), (210, 466), (370, 424), (520, 470),
             (690, 432), (850, 468), (1010, 426), (1170, 464), (1370, 432)]
    K.draw_smooth(d, crest + [(1370, 820), (-90, 820)],
                  fill=EMBER, outline=INK, width=K.OUTLINE, seed=7102,
                  wobble=5.0, wavelength=240.0)
    # frost crests riding the wave tops — the "ice" half of the surface.
    # Each one gets its own width, height, tilt and lean, or the row reads as
    # nine identical tents stamped along the horizon.
    rnd = random.Random(7103)
    for i in range(8):
        cxx = -20 + i * 172 + rnd.randint(-46, 46)
        cyy = 452 + rnd.randint(-26, 26)
        hw = rnd.randint(38, 96)
        hh = rnd.randint(16, 40)
        tilt = rnd.uniform(-0.30, 0.30)
        K.draw_smooth(d, [(cxx - hw, cyy + hh * 0.5),
                          (cxx - hw * 0.55, cyy - hh * 0.7 + tilt * hw),
                          (cxx + hw * 0.30, cyy - hh),
                          (cxx + hw, cyy + hh * 0.4),
                          (cxx + hw * 0.30, cyy + hh * 0.9)],
                      fill=FROST, outline=INK, width=K.DETAIL, seed=7110 + i,
                      wobble=5.0, wavelength=90.0)
    # flow strokes so it reads as liquid, not rock
    for i, (sx, sy, sw) in enumerate(((730, 520, 180), (940, 546, 150),
                                      (1130, 506, 140), (470, 588, 200))):
        _open_curve(d, [(sx, sy), (sx + sw * 0.5, sy + 18), (sx + sw, sy + 6)],
                    ABYSS, width=K.DETAIL, seed=7130 + i, wobble=1.6)

    # the half-sunk ship, bow up, right of centre
    sx, sy = 986, 470
    K.draw_smooth(d, [(sx - 62, sy + 26), (sx - 54, sy - 12), (sx + 10, sy - 20),
                      (sx + 62, sy + 2), (sx + 40, sy + 28)],
                  fill=ABYSS, outline=INK, width=K.OUTLINE, seed=7140,
                  wobble=2.4, wavelength=120.0)
    K.draw_smooth(d, [(sx - 6, sy - 18), (sx - 2, sy - 74), (sx + 24, sy - 76),
                      (sx + 20, sy - 16)],
                  fill=PAPER, outline=INK, width=K.DETAIL, seed=7141,
                  wobble=2.0, wavelength=90.0)
    _tiny(d, 'SHIP', sx, sy + 54, INK, px=18)

    C.hero_word(d, 'CANNOT STAND ON IT', 640, 158, EMBER, stroke_rgb=INK,
                stroke_width=3, px=58, margin=40, y_max=210)

    d = ImageDraw.Draw(img)
    img = _finish(img, card, planet, paper_band=False, dark_bg=False)

    # The character is waist-deep in the sea (the card's point is that he can
    # not stand on it). At the heights the schedule uses, the library's two leg
    # strokes merge into one solid black wedge; a foreground wave drawn OVER him
    # eats the lower half of that wedge so it reads as submerged legs in liquid
    # instead of a black post. Position comes from the schedule, so the lapping
    # crest is centred on wherever he was actually placed.
    sm = card.get('stickman')
    if sm:
        sx = int(sm['x_center'])
        feet = int(sm['y_top']) + int(sm['height'])
        lap = max(feet - 70, 468)
        lap = min(lap, 600)
        dd = ImageDraw.Draw(img, 'RGBA')
        wave = [(sx - 128, lap + 14), (sx - 52, lap - 9), (sx + 26, lap + 12),
                (sx + 104, lap - 7), (sx + 146, lap + 9),
                (sx + 146, 780), (sx - 128, 780)]
        # fill only — an outlined polygon drops two ink verticals through the
        # caption row. The waterline gets its own open stroke instead.
        K.draw_smooth(dd, wave, fill=EMBER, outline=None, width=0,
                      seed=7160, wobble=4.0, wavelength=110.0)
        _open_curve(dd, wave[:5], INK, width=K.OUTLINE, seed=7161, wobble=4.0,
                    wavelength=110.0)
    # re-lay the caption over the lapping wave
    C._caption(img, card['caption'], 70, 652, dark_bg=False)
    return img


# ===========================================================================
# B8 THE ESCAPE — losing_mass.  VOID.  "Hydrogen and helium are escaping from
# it, right now."  Thin gas streams peel off the planet's limb and peel AWAY into
# the dark — flat tapered bands, no gradient. The character shrugs.
# ===========================================================================

def render_losing_mass(card, planet="Gliese 436 b"):
    img = _void_card(seed=801, stars=120)

    img = _soft_wash(img,
                     [(380, 170), (700, 140), (860, 280), (838, 470),
                      (620, 546), (386, 430)],
                     ABYSS, 40, seed=8101, wobble=18.0, blur=28)
    d = ImageDraw.Draw(img, 'RGBA')

    cx, cy, r = 620, 336, 156
    _ice_planet(d, cx, cy, r, seed=801, ring=False)

    # the escaping gas: five tapered ribbons peeling off the upper-right limb
    for i in range(5):
        a0 = math.radians(-64 + i * 21)
        sx = cx + (r - 4) * math.cos(a0)
        sy = cy + (r - 4) * math.sin(a0)
        pts = [(sx, sy),
               (sx + 92, sy - 42 + i * 12),
               (sx + 186, sy - 52 + i * 26),
               (sx + 268, sy - 34 + i * 40)]
        _thick_curve(d, pts, ABYSS if i % 2 == 0 else FROST,
                     seed=8110 + i, width=13 - i * 1.6, wobble=3.0,
                     wavelength=140.0)
        # a bright leading edge on each ribbon — the gas that has actually left
        _open_curve(d, pts, FROST, width=K.FINE, seed=8130 + i, wobble=2.0,
                    wavelength=140.0)

    _tiny(d, 'H  +  He', 1030, 148, FROST, px=20)
    _tiny(d, 'LEAVING NOW', 1030, 176, EMBER, px=20)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# B9 THE TAIL — glowing_tail.  VOID.  "a long comet-like tail ... it glows in
# the dark."  The subject is the TAIL: a long EMBER-and-FROST plume sweeping
# right and off-frame off the tiny planet. The character stands at the left,
# deadpan, watching it go.
# ===========================================================================

def render_glowing_tail(card, planet="Gliese 436 b"):
    img = _void_card(seed=901, stars=132)

    d = ImageDraw.Draw(img, 'RGBA')
    # the tail, in nested tapered bands, widest at the planet and thinning out
    ty = 322
    for i in range(9):
        t = i / 8.0
        x0 = 372 + t * 120
        hh = (86 - 62 * t)
        band = [(x0, ty - hh), ((x0 + 1280) / 2.0, ty - hh * 0.86), (1280, ty - 6),
                ((x0 + 1280) / 2.0, ty + hh * 0.86), (x0, ty + hh)]
        col = EMBER if i % 2 == 0 else FROST
        K.draw_smooth(d, band, fill=col + (34 if i % 2 else 46,), outline=None,
                      seed=9110 + i, wobble=6.0, wavelength=260.0)
    # bright filaments running down the middle of the plume
    for i in range(4):
        yy = ty - 40 + i * 26
        _open_curve(d, [(392, yy), (700, yy - 8 + i * 5), (1010, yy + 6),
                        (1276, yy + 16)],
                    FROST + (150,), width=K.FINE, seed=9130 + i, wobble=2.2,
                    wavelength=240.0)

    # the tiny planet, at the tail's root. Glow goes UNDER it — added on top it
    # hazes over the disc and reads as a murky shadow rather than escaping light.
    C.add_glow(img, 322, ty, 128, EMBER, 34)
    d = ImageDraw.Draw(img, 'RGBA')
    _ice_planet(d, 322, ty, 74, seed=901, melt=0.6, ring=False)
    # a sparse ember spray hugging the planet's trailing limb — a thin wisp of
    # escaping gas, not a wide confetti field (an earlier wide rect-scatter
    # read as orange litter all over the void).
    d = ImageDraw.Draw(img, 'RGBA')
    for i in range(7):
        a = math.radians(-46 + i * 15)
        rr = 82 + (i % 3) * 22
        px_, py_ = 322 + rr * math.cos(a), ty + rr * math.sin(a)
        K.draw_disc(d, px_, py_, 3 + (i % 3), fill=EMBER + (190,),
                    outline=None, width=0, seed=9150 + i, wobble=1.0)

    _tiny(d, 'HYDROGEN + HELIUM', 830, 176, FROST, px=20)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# B10 FATE — closing_impossible.  VOID, wide shot.  "one of the strangest
# things in the galaxy / just sitting there. Burning its ice. Quietly.
# Forever."  The whole system: the star at the right, the planet whipping a
# long tail around it on a flat orbit ellipse. The character is small in the
# corner, deadpan, hands down. One focal point: the planet.
# ===========================================================================

def render_closing_impossible(card, planet="Gliese 436 b"):
    img = _void_card(seed=1001, stars=136)

    # SCALE, from the assembly critic (p05, round 1). Round 1 put the planet at
    # r=62 and the star at r=52 on an orbit 330x132, so both subjects occupied
    # under a fifth of the frame width and the card read as two small objects
    # adrift in a large empty sky -- the under-filled-frame failure. The
    # reference fills the frame and CROPS a body at the edge, so the orbit is
    # now 560x168 (it exits both side edges, admitting the system is larger
    # than the picture) and the star is pushed off the right edge rather than
    # parked inside it.
    cx, cy = 770, 352
    d = ImageDraw.Draw(img, 'RGBA')

    # the orbit ellipse — flat FROST, no gradient
    K.draw_outline(d, [(cx + 560 * math.cos(math.tau * i / 40),
                        cy + 168 * math.sin(math.tau * i / 40)) for i in range(40)],
                   color=FROST, width=K.DETAIL, closed=True, seed=10010,
                   wobble=1.0)

    # the host star, glaring on the orbit's right edge — the one legal gradient.
    # Its centre sits at x=1200 with r=132, so a third of it is off the right
    # edge: the frame-crop the reference uses on this beat.
    d = _star(img, 1200, 322, 132, seed=1001)

    # the tail, streaming away from the star. Rooted AT the planet and tapering to
    # a point at its far end; the earlier version rooted the bands 250px to the
    # right of the planet with a shared blunt tip, which read as a cigar lying
    # THROUGH the planet rather than a tail leaving it. It now runs off the left
    # edge, which is the same frame-crop gesture as the star at the right.
    px, py = 400, 300
    for i in range(8):
        t = i / 7.0
        hh = 130 - 51 * t
        tipx = px - 150 - 364 * t
        band = [(px + 68, py - hh), ((px + tipx) / 2.0, py - hh * 0.70),
                (tipx, py), ((px + tipx) / 2.0, py + hh * 0.70),
                (px + 68, py + hh)]
        K.draw_smooth(d, band,
                      fill=(EMBER if i % 2 == 0 else FROST) + (34 - 3 * i,),
                      outline=None, seed=10020 + i, wobble=6.0, wavelength=220.0)
    for i in range(3):
        yy = py - 28 + i * 29
        _open_curve(d, [(px + 34, yy), (px - 255, yy - 12), (px - 425, yy + 10),
                        (px - 503, yy + 24)],
                    FROST + (130,), width=K.FINE, seed=10040 + i, wobble=2.0,
                    wavelength=200.0)

    # the planet on its orbit, mid-left, half-melted
    px, py = 400, 300
    # glow goes UNDER the planet: drawn on top it reads as a murky blob across
    # the face rather than as light escaping from it.
    C.add_glow(img, px, py, 240, EMBER, 40)
    d = ImageDraw.Draw(img, 'RGBA')
    _ice_planet(d, px, py, 126, seed=1001, melt=0.6, ring=False)
    # a few ember grains hugging the limb, trailing down the orbit — kept local
    # so the tail reads as gas, not as scatter.
    for i in range(6):
        a = math.radians(148 + i * 16)
        rr = 146 + (i % 3) * 34
        gx, gy = px + rr * math.cos(a), py + rr * math.sin(a)
        K.draw_disc(d, gx, gy, 6 + (i % 2) * 3, fill=EMBER + (185,), outline=None,
                    width=0, seed=10060 + i, wobble=1.0)

    # the tail's own label — a fact the caption does not carry, so it does not
    # restate the caption the way 'BURNING ITS ICE' did. Sits low-left, clear of
    # the widened tail.
    _tiny(d, 'HYDROGEN + HELIUM', 268, 618, FROST, px=20)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# Dispatch — keyed by EVERY beat id in script.json.
# ===========================================================================

RENDERERS = {
    'hook_burning_ice': render_hook_burning_ice,
    'world_size': render_world_size,
    'hook_no_sense': render_hook_no_sense,
    'pressure_and_heat': render_pressure_and_heat,
    'no_choice': render_no_choice,
    'supercritical': render_supercritical,
    'burning_torch': render_burning_torch,
    'losing_mass': render_losing_mass,
    'glowing_tail': render_glowing_tail,
    'closing_impossible': render_closing_impossible,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table. The frame
    generator may instead read RENDERERS directly; both are supported."""
    C.register(mapping if mapping is not None else RENDERERS)
    return RENDERERS


# ===========================================================================
# Self-test: render every beat to cardsheet/beat_NN.png, one line per beat.
# ===========================================================================

_SELF_TEST = [
    # (beat id, register, caption, stickman spec or None)
    ('hook_burning_ice', 'void', 'A PLANET OF ICE, AND IT IS ON FIRE',
     dict(x_center=330, y_top=250, height=430, pose='pointing', expression='flat')),
    ('world_size', 'void', 'ABOUT THE SIZE OF NEPTUNE',
     dict(x_center=250, y_top=236, height=444, pose='hands_up', expression='oval')),
    ('hook_no_sense', 'cream', 'ICE SHOULD MELT',
     dict(x_center=286, y_top=252, height=436, pose='shrugged', expression='zigzag')),
    ('pressure_and_heat', 'void', 'CRUSHED AND COOKED AT ONCE',
     dict(x_center=232, y_top=248, height=440, pose='shielding_eyes',
          expression='worried')),
    ('no_choice', 'cream', 'IT NEVER GETS TO CHOOSE',
     dict(x_center=262, y_top=250, height=438, pose='pointing', expression='skeptical')),
    ('supercritical', 'void', 'SUPERCRITICAL: NO SEAM',
     dict(x_center=234, y_top=244, height=442, pose='pointing', expression='flat')),
    ('burning_torch', 'cream', 'ICE THAT BURNS LIKE A TORCH',
     dict(x_center=250, y_top=234, height=448, pose='hands_up',
          expression='awed_brows')),
    ('losing_mass', 'void', 'MASS, LEAVING RIGHT NOW',
     dict(x_center=250, y_top=248, height=440, pose='shrugged', expression='zigzag')),
    ('glowing_tail', 'void', 'THE TAIL GLOWS IN THE DARK',
     dict(x_center=150, y_top=300, height=380, pose='standing', expression='flat')),
    ('closing_impossible', 'void', 'BURNING ITS ICE. QUIETLY. FOREVER.',
     dict(x_center=142, y_top=318, height=364, pose='hands_down',
          expression='deadpan_grim')),
]


def _self_test():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, 'cardsheet')
    os.makedirs(out, exist_ok=True)
    for n, (cid, reg, cap, sm) in enumerate(_SELF_TEST, start=1):
        card = {'id': cid, 'caption': cap, 'stickman': sm}
        img = RENDERERS[cid](card, "Gliese 436 b")
        path = os.path.join(out, 'beat_%02d.png' % n)
        img.save(path)
        print('beat %02d  %-22s %-5s %s  %s' % (n, cid, reg, img.size,
                                                'stickman' if sm else 'data-only'))
    return 0


if __name__ == '__main__':
    raise SystemExit(_self_test())