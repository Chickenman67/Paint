# work/segments/koi55/_cards.py — the whole KOI-55 beat set as one module.
#
# Segment 8: KOI-55 — "the planet that survived being eaten". Twelve beats from
# work/segments/koi55/script.json, alternating void (space register) and cream
# (paint register) cards, exactly as the script's `register` field asks.
#
# CONTRACT (identical to the psrb1257 beat modules, so the frame generator can
# treat this segment exactly like segment 3):
#   * module-level RENDERERS dict, keyed by every beat id in script.json
#   * every renderer is fn(card, planet="KOI-55") -> PIL RGB 1280x720
#   * renderers DRAW the frame; they never return a card dict
#   * Layout A: 84px paper title strip (C._header), full-bleed art rows 84..719,
#     NO caption band - the caption floats on the art at (70, 652)
#   * 'void'  -> void_backdrop + C._header(paper_band=True) + dark stickman
#     'cream' -> full-bleed paper + C._header(paper_band=False) + light stickman
#   * hard snap cuts between beats; nothing here is tweened. The quantized 0.25 s
#     stamp motion is layered on by the frame generator on top of these stills.
#
# CANON RULES THIS MODULE KEEPS
#   1. Type is comicbd.ttf / comic.ttf via lib.type only, at the five locked sizes.
#      No Consolas anywhere.
#   2. 6px outlines on large shapes (K.OUTLINE), 4px detail, 2px fine, 1px hairline.
#   3. Smooth hand curves with LOW-FREQUENCY wobble (lib.ink), never per-vertex
#      jitter on straight polylines.
#   4. The character is CREAM on void (theme='dark') and INK on cream
#      (theme='light'). Hardcoding black made him vanish into every space card.
#   5. Gradients are legal ONLY on emissive bodies (the star core) and the space
#      field. Rocks, diagrams, orbit paths, arrows, panels and the character are
#      FLAT fills.
#   6. Every wobble / stipple / starfield call takes an explicit seed. No global
#      random state anywhere, so re-renders are byte-identical.
#   7. One focal point per card.
#   8. The narration is audio only. Nothing here prints a narration line.
#
# This module has no import side effects beyond sys.path setup. The frame
# generator does C.register(module.RENDERERS) and then C.render(card, planet).

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
_SEGMENTS = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_SEGMENTS)
for _p in (_HERE, _SEGMENTS, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib.type as T            # noqa: E402
import lib.ink as K             # noqa: E402
import lib.cardframe as C       # noqa: E402
import lib.stickman as S        # noqa: E402

W, H = C.W, C.H

# ---------------------------------------------------------------------------
# THE LOCKED KOI-55 PALETTE (see PALETTE_SPEC.md in this directory)
#
# Six colors. Two of them are tints of Slag grey, not new hues — they are
# labeled as tints in the spec and exist so a Register-P card can have a
# ground plane / cut face / panel fill that is still legibly "slag".
#
# The stickman's shirt red #C83232 is deliberately NOT in this palette. It is a
# global of the character and is the only red on screen in all 12 segments, so
# no card accent here may be red or the character dissolves into the card.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':   (21, 23, 30),     # #15171E  slate-black  - all linework, header glyphs
    'paper': (242, 234, 214),   # #F2EAD6  bone-cream   - title strip, cream cards
    'deep':  (5, 6, 11),        # #05060B  void         - the space field
    'ember': (232, 118, 43),    # #E8762B  signal ember - the star, heat, molten
    'gold':  (242, 180, 65),    # #F2B441  ember-gold   - captions on void, daylight
    'slag':  (140, 131, 120),   # #8C8378  slag grey    - rock, cinder, dusk
}

SLAG_LIGHT = (178, 168, 155)   # tint of slag: ground planes, cut faces, panels
SLAG_PALE = (214, 206, 193)    # tint of slag: dial faces, hollow interiors
SHIRT_RED = (200, 50, 50)      # the character only - never a card accent

# Borrowed from the segment-3 scale, used in this segment for exactly one job:
# the rim of a dark object on a near-black field. Ink-on-void is 1.2:1, so a
# rock drawn in plain ink with no rim is literally invisible. Bone never appears
# as a caption on a void card (that is gold) and never on cream (1.06:1).
BONE = (220, 230, 236)

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
EMBER = MY_PAL['ember']
GOLD = MY_PAL['gold']
SLAG = MY_PAL['slag']

# Caption anchor. Identical to the C._caption convention used by every other
# segment module; drawn here rather than via C._caption only so the void-card
# caption uses THIS segment's gold instead of lib amber.
CAP_X, CAP_Y = 70, 652


# ---------------------------------------------------------------------------
# Card scaffolding
# ---------------------------------------------------------------------------

def _void_frame(seed, stars=118):
    """A Register-S space field. Gradient legal here (the backdrop is the one
    always-legal gradient). A distinct seed per card so no two cards in the
    segment are literally the same frame with the same stars."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars)
    return img


def _cream_frame():
    """A Register-P paint/scene card. Full-bleed bone-cream, no strip edge."""
    return Image.new('RGB', (W, H), PAPER)


def _finish(img, card, planet, paper_band, dark_bg):
    """Layout-A tail, identical on every card: title strip, then the
    schedule-driven character, then the one floating caption."""
    C._header(img, planet, paper_band=paper_band)
    C._draw_stickman(img, card, theme=('dark' if dark_bg else 'light'))
    _caption(img, card.get('caption', ''), dark_bg=dark_bg)
    return img


def _caption(img, text, dark_bg=True):
    """The floating caption on the art. Same glyph treatment and anchor as
    C._caption (28px comicbd, 3px keyline) with this segment's own colors."""
    if not text:
        return
    d = ImageDraw.Draw(img)
    if dark_bg:
        T.draw_caption(d, text, (CAP_X, CAP_Y), color_rgb=GOLD, ink_rgb=INK)
    else:
        T.draw_caption(d, text, (CAP_X, CAP_Y), color_rgb=INK, ink_rgb=PAPER)


# ---------------------------------------------------------------------------
# Typography helpers. Every one of these routes through lib.type, so the whole
# segment stays in the locked rounded-hand family at the locked sizes.
# ---------------------------------------------------------------------------

def _stamp(draw, text, cx, cy, fill_rgb, px=None, bold=False, keyline=None):
    """A small diagram annotation, CENTERED on (cx, cy), at STAMP_PX.
    `keyline` is the outline color; pass the same color as fill for no keyline
    (T.draw_stamp's own default is a 1px ink line)."""
    px = T.STAMP_PX if px is None else px
    font = T.load_font_at(px, bold=bold)
    x0, y0, x1, y1 = font.getbbox(text)
    bw, bh = x1 - x0, y1 - y0
    T.draw_outlined_text(draw, (cx - bw / 2.0 - x0, cy - bh / 2.0 - y0), text,
                         font, fill=fill_rgb,
                         stroke=fill_rgb if keyline is None else keyline,
                         stroke_width=1)
    return (cx - bw / 2.0, cy - bh / 2.0, bw, bh)


def _hand_label(draw, text, cx, cy, fill_rgb):
    """The SECOND type treatment: the light casual hand at LABEL_PX, centered.
    This is the reference's planet-label face, distinct from the bold header.
    Used once, on the outro's stamped catalog tag."""
    font = T.load_font_at(T.LABEL_PX, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    bw, bh = x1 - x0, y1 - y0
    T.draw_outlined_text(draw, (cx - bw / 2.0 - x0, cy - bh / 2.0 - y0), text,
                         font, fill=fill_rgb, stroke=fill_rgb, stroke_width=0)
    return (cx - bw / 2.0, cy - bh / 2.0, bw, bh)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output).

    K._smooth_open exists in lib/ink.py but this keeps the two callers below
    (a hairline curve and the same curve as a fat filled glyph) in lockstep, so
    they trace exactly the same path.
    """
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


def _open_curve(draw, points, color, width=2, seed=0, wobble=1.2,
                wavelength=90.0):
    """An OPEN hand-wobbled smooth curve at hairline/detail width."""
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    if len(pts) < 3:
        draw.line(list(pts), fill=color, width=width)
        return pts
    out = _catmull_open(pts, samples=12)
    draw.line(out, fill=color, width=width, joint='curve')
    return out


def _thick_curve(draw, points, fill, seed=0, width=20, wobble=2.0,
                 wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region, not as a wide
    PIL line.

    WHY NOT draw.line(..., width=24, joint='curve'): at this scale the
    Catmull-Rom output has many near-duplicate consecutive points, and PIL
    renders each segment as a rectangle plus a round cap - on a zero-length
    segment the cap shows up as a nub, so the glyph comes out hairy-edged. So
    the stroke is built geometrically: the smooth centreline is offset by
    +/- half-width along its normal into an outer and an inner rail, and the two
    rails are welded into one closed polygon filled with a single polygon call.
    Clean edges, no nubs, and it obeys the "smooth organic curve" rule the same
    way K.draw_smooth does for closed shapes.
    """
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    n = len(dense)
    hw = width / 2.0
    normals = []
    for i in range(n):
        a = dense[max(0, i - 1)]
        b = dense[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        normals.append((-dy / L, dx / L))
    outer = [(p[0] + nx * hw, p[1] + ny * hw)
             for p, (nx, ny) in zip(dense, normals)]
    inner = [(p[0] - nx * hw, p[1] - ny * hw)
             for p, (nx, ny) in zip(dense, normals)]
    region = outer + inner[::-1]
    draw.polygon(region, fill=fill)
    return region


def _arc_pts(cx, cy, r, a0_deg, a1_deg, n=48, yscale=1.0):
    """Sample a circular arc. PIL angles: 0 = 3 o'clock, increasing clockwise
    (y grows downward), so 180 = 9 o'clock (screen-left)."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / float(n))
        pts.append((cx + r * math.cos(a), cy + yscale * r * math.sin(a)))
    return pts


def _blob_pts(cx, cy, r, seed, n=9, irr=0.15, yscale=1.0):
    """An irregular closed silhouette - a hand-drawn rock / cinder / blob.
    Deterministic for a given seed."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = math.tau * i / n
        rr = r * (1.0 + rnd.uniform(-irr, irr))
        pts.append((cx + rr * math.cos(a), cy + yscale * rr * math.sin(a)))
    return pts


def _blob(draw, cx, cy, r, seed, fill, outline=None, width=K.OUTLINE,
          irr=0.15, yscale=1.0, n=9, wobble=2.0):
    """Fill a hand-drawn irregular blob. Register P: flat fill, thick organic
    outline. Register S: pass outline=None, width=0 for a body with no keyline."""
    return K.draw_smooth(draw, _blob_pts(cx, cy, r, seed, n=n, irr=irr,
                                         yscale=yscale),
                         fill=fill, outline=outline, width=width,
                         seed=seed + 1, wobble=wobble, wavelength=max(30.0, r * 1.6),
                         closed=True)


def _wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=170.0,
          blur=18):
    """A painterly FLAT-colour region with soft edges.

    Every wash on this segment is a flat fill on its own RGBA layer, wobbled by
    K.draw_smooth and then blurred - never a gradient, and never a crisp
    rectangle (a square-cornered CAD rectangle is the read the canon forbids).
    Returns a new RGB image.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=rgb + (int(alpha),), outline=None, width=0,
                  seed=seed, wobble=wobble, wavelength=wavelength, closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


# ---------------------------------------------------------------------------
# The star. The one place a gradient is legal in this segment, because it is
# the one EMISSIVE body. Everything else - rocks, panels, arrows, orbit paths -
# is flat.
# ---------------------------------------------------------------------------

def _star(img, cx, cy, r, seed, glow=0.7, shells=True, stipple=True):
    """A hot, close-in star: the 3-stop radial core (legal gradient) plus flat
    concentric emission shells, per the canon's read of how the reference
    paints an emissive body. No black outline - it is a light source, and a
    keyline on a light source reads as a hole."""
    cx, cy, r = int(cx), int(cy), int(r)
    C._radial_core(img, cx, cy, r,
                   [(255, 246, 222), GOLD, EMBER], glow=glow)
    d = ImageDraw.Draw(img, 'RGBA')
    if shells:
        for f, a, w, sd in ((0.94, 78, K.DETAIL, 1), (0.80, 60, K.DETAIL, 2),
                            (0.66, 46, K.DETAIL, 3), (0.52, 34, K.FINE, 4)):
            rr = r * f
            ring = [(cx + rr * math.cos(math.tau * i / 14.0),
                     cy + rr * math.sin(math.tau * i / 14.0)) for i in range(14)]
            K.draw_outline(d, ring, color=EMBER + (a,), width=w, closed=True,
                           seed=seed + 10 + sd, wobble=max(1.5, r * 0.018),
                           wavelength=max(40.0, r * 1.1))
    if stipple:
        # Spray grain, not static. Confined to the inner 42% of the disc so no
        # speck lands on the shells or off the body, and kept sparse: at 0.020
        # over 55% it read as dirt on the lens rather than paint overspray.
        d = ImageDraw.Draw(img, 'RGBA')
        K.stipple(d, cx - r * 0.42, cy - r * 0.42, cx + r * 0.42, cy + r * 0.42,
                  EMBER + (96,), seed=seed + 21, density=0.007, r=1, spread=1)
    return img


def _void_rock(draw, cx, cy, r, seed, rim=None):
    """A rock on a void card. The body is a dark keyline-fill; the RIM is bone
    so the silhouette separates from the space field. (Pure ink on the void is
    1.2:1 - literally invisible - which is why the transit silhouette on card 1
    is the one rock that is drawn without a rim: there it sits on the star.)"""
    rim = BONE if rim is None else rim
    return _blob(draw, cx, cy, r, seed, fill=INK, outline=rim,
                 width=K.DETAIL, irr=0.11, yscale=0.92, n=9, wobble=1.4)


# ---------------------------------------------------------------------------
# B1 — hook_closest_orbit. VOID. The opening card.
# ---------------------------------------------------------------------------

def render_hook_closest_orbit(card, planet="KOI-55"):
    """B1/1 - the tightest orbit we know.

    A huge banded star fills the right third and the planet is a pure-black
    disc pressed against its limb in transit - the closest orbit is the subject,
    and the transit silhouette is the only other thing allowed on the card.
    The character stands small at lower left, deadpan, looking up at it.

    Accent: EMBER. The one gradient on the card is the star's core, because the
    star is the one emissive body in the segment.
    """
    img = _void_frame(seed=101, stars=126)
    cx, cy, r = 986, 372, 250
    _star(img, cx, cy, r, seed=101, glow=0.65)

    # the transit silhouette. NO rim: it is ink pressed against a bright limb,
    # and a rim here would draw a bright halo round the black dot.
    d = ImageDraw.Draw(img, 'RGBA')
    _blob(d, 742, 372, 38, seed=102, fill=INK, outline=None, width=0,
          irr=0.07, n=10, wobble=1.2)
    # a short leader up into the void, where contrast is fine, so the label is
    # on its subject's side of the limb but still legible.
    _open_curve(d, [(742, 330), (742, 312)], BONE, width=K.FINE, seed=103,
                wobble=0.6)
    _stamp(d, "TRANSIT", 742, 300, BONE)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# B2 — hook_five_hours. CREAM. Pure data beat, no character.
# ---------------------------------------------------------------------------

def render_hook_five_hours(card, planet="KOI-55"):
    """B2/2 - the year.

    One idea: five hours forty minutes. A big drawn clock dial on the left and
    three stepped day/dusk bands on the right, so the dial is the number and the
    bands are what that number means. No character - the script calls this a pure
    data beat and CLAUDE.md says not to put him in every single card.

    Accent: GOLD. Dial face is a SLAG_PALE tint, ticks and outline are ink.
    """
    img = _cream_frame()
    d = ImageDraw.Draw(img)

    # --- the dial -----------------------------------------------------------
    dcx, dcy, dr = 372, 388, 202
    K.draw_disc(d, dcx, dcy, dr, fill=SLAG_PALE, outline=INK, width=K.OUTLINE,
                seed=201, wobble=3.0)
    for k in range(12):
        a = math.radians(-90 + 30 * k)
        ca, sa = math.cos(a), math.sin(a)
        r0, r1 = dr - 30, dr - 12
        _open_curve(d, [(dcx + r0 * ca, dcy + r0 * sa),
                        (dcx + r1 * ca, dcy + r1 * sa)],
                    INK, width=K.DETAIL, seed=210 + k, wobble=0.4,
                    wavelength=50.0)
    # the swept sector - 5h40m of a day, filled so the dial is not an empty face
    sweep_end = -90 + (5 * 60 + 40) / 720.0 * 360.0
    wedge = [(dcx, dcy)]
    for i in range(25):
        a = math.radians(-90 + (sweep_end + 90.0) * i / 24.0)
        wedge.append((dcx + (dr - 42) * math.cos(a), dcy + (dr - 42) * math.sin(a)))
    K.draw_smooth(d, wedge, fill=GOLD, outline=None, seed=205, wobble=1.4,
                  wavelength=170.0)
    _open_curve(d, wedge[1:], INK, width=K.FINE, seed=206, wobble=0.8,
                wavelength=150.0)
    # the hand, caught pointing right, plus a short counterweight tail
    _thick_curve(d, [(dcx - 46, dcy + 22), (dcx + 20, dcy + 6),
                     (dcx + dr - 54, dcy - 26)], EMBER, seed=230, width=13,
                 wobble=1.6)
    K.draw_disc(d, dcx, dcy, 17, fill=INK, outline=INK, width=K.DETAIL,
                seed=231, wobble=1.0)
    # the number, stamped where the hand does not reach
    _stamp(d, "5H 40M", dcx, dcy + 118, INK, keyline=SLAG_PALE)

    # --- three stepped cycles ----------------------------------------------
    # Each row is a drawn slice of sky: a GOLD sky over a SLAG ground with a
    # wobbly horizon between them and the sun disc straddling that horizon. The
    # three rows run dawn -> noon -> dusk and a return arc on the right closes
    # the loop. Fills and frames first, ALL labels after - otherwise a later
    # row's opaque fill paints over the previous row's caption.
    bx0, bx1 = 700, 1232
    bw = bx1 - bx0
    rows = (176, 288, 400)
    h = 92
    horizon_frac = (0.30, 0.52, 0.74)
    labels = ("DAWN", "NOON", "DUSK")
    # pass 1: fills, horizons, frames, suns
    for k, y in enumerate(rows):
        hz = y + int(h * horizon_frac[k])
        d.rectangle([bx0, y, bx1, hz], fill=GOLD)          # sky
        d.rectangle([bx0, hz, bx1, y + h], fill=SLAG)       # ground
        hz_pts = [(bx0 + bw * i / 4.0, hz + (0 if i in (0, 4) else (-4 + 8 * k)))
                  for i in range(5)]
        _open_curve(d, hz_pts, INK, width=K.DETAIL, seed=280 + k, wobble=1.2,
                    wavelength=150.0)
        # frame as four separate open edges so the panel stays rectangular
        # (a closed Catmull-Rom box bows its sides into a lozenge)
        _open_curve(d, [(bx0, y), ((bx0 + bx1) / 2.0, y), (bx1, y)],
                    INK, width=K.OUTLINE, seed=290 + k, wobble=1.4,
                    wavelength=170.0)
        _open_curve(d, [(bx1, y), (bx1, y + h / 2.0), (bx1, y + h)],
                    INK, width=K.OUTLINE, seed=291 + k, wobble=1.4,
                    wavelength=170.0)
        _open_curve(d, [(bx1, y + h), ((bx0 + bx1) / 2.0, y + h), (bx0, y + h)],
                    INK, width=K.OUTLINE, seed=292 + k, wobble=1.4,
                    wavelength=170.0)
        _open_curve(d, [(bx0, y + h), (bx0, y + h / 2.0), (bx0, y)],
                    INK, width=K.OUTLINE, seed=293 + k, wobble=1.4,
                    wavelength=170.0)
        # the sun, half up over the horizon and stepping right across the rows
        sun_x = bx0 + int(bw * (0.18 + 0.32 * k))
        K.draw_disc(d, sun_x, hz, 24, fill=EMBER, outline=INK,
                    width=K.DETAIL, seed=300 + k, wobble=1.6)
    # pass 2: labels. Placed INSIDE each panel's sky at its left edge - the 20px
    # gutter between rows is narrower than a stamp, so an under-row label
    # landed on the next panel's frame.
    for k, y in enumerate(rows):
        _stamp(d, labels[k], bx0 + 44, y + h // 2, INK)
    # the loop closing: a return arc tucked INSIDE the right edge, running from the
    # last row back up to the first
    _open_curve(d, [(1244, 452), (1226, 320), (1244, 214)],
                EMBER, width=K.DETAIL, seed=330, wobble=1.4, wavelength=140.0)
    _stamp(d, "AND AGAIN", 1150, 140, EMBER, keyline=PAPER)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# B3 — hook_breath. VOID. The same star, four times.
# ---------------------------------------------------------------------------

def render_hook_breath(card, planet="KOI-55"):
    """B3/3 - the repetition.

    Four copies of the same star marching down toward a horizon, each on its
    own orbit loop, so the eye reads "this happens over and over" without a
    single word of narration. The character stands on the horizon at lower right,
    awed, watching them go.

    Accent: EMBER (it is the same object as card 1, so it keeps card 1's color).
    The four stars are flat concentric discs, NOT gradients: only the first and
    largest one is emissive enough to justify the gradient, and four gradients
    on one card would make the card read as four focal points.
    """
    img = _void_frame(seed=301, stars=112)

    # the horizon first, so the stars sit ON it
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_ground(d, 0, W, 596, H, fill=INK, seed=305, width=K.OUTLINE,
                  roughness=5.0)

    spots = ((262, 250, 74, 105), (522, 320, 58, 115),
             (762, 386, 45, 125), (972, 442, 35, 135))
    for k, (sx, sy, sr, ang) in enumerate(spots):
        # its orbit loop, one half-turn behind it: where it came from
        orb = [(sx + (sr + 46) * math.cos(math.radians(a)),
               sy + (sr * 0.42) * math.sin(math.radians(a)))
               for a in [ang + j * 3 for j in range(0, 191)]]
        _open_curve(d, orb, BONE + (170,), width=K.FINE, seed=310 + k,
                    wobble=1.0, wavelength=120.0)
        if k == 0:
            img = _star(img, sx, sy, sr, seed=320 + k, glow=0.5)
        else:
            dd = ImageDraw.Draw(img, 'RGBA')
            C._radial_core(img, int(sx), int(sy), int(sr),
                           [(255, 246, 222), GOLD, EMBER], glow=0.35)
            dd = ImageDraw.Draw(img, 'RGBA')
            K.draw_outline(dd,
                           [(sx + sr * 0.72 * math.cos(math.tau * i / 12.0),
                             sy + sr * 0.72 * math.sin(math.tau * i / 12.0))
                            for i in range(12)],
                           color=EMBER + (150,), width=K.FINE, closed=True,
                           seed=330 + k, wobble=1.4, wavelength=sr * 1.2)
    d = ImageDraw.Draw(img, 'RGBA')
    _stamp(d, "ONE BREATH", 620, 616, BONE)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# B4 — bare_rock_world. CREAM. Cross-section of the shell.
# ---------------------------------------------------------------------------

def render_bare_rock_world(card, planet="KOI-55"):
    """B4/4 - what is actually up there.

    A grey rock in cross-section: a flat shell with a hollow dead core, and
    three arrows bouncing off the top of it labelled AIR / OCEAN / WEATHER. The
    shell being closed is the fact - nothing gets in and nothing gets out, which
    is exactly why the arrows turn around. The character shrugs at the empty
    shell, mouth zigzag.

    Accent: SLAG, with SLAG_LIGHT for the cut face and EMBER for the arrows.
    """
    img = _cream_frame()

    # ground band first: the character is grounded, not floating
    d = ImageDraw.Draw(img)
    K.draw_ground(d, 0, W, 620, H, fill=SLAG_LIGHT, seed=401, width=K.OUTLINE,
                  roughness=4.0)

    rcx, rcy, rr = 786, 400, 214
    # the shell, in cross-section: left half is the outside skin, right half is
    # the cut face
    shell = _blob_pts(rcx, rcy, rr, seed=402, n=11, irr=0.10, yscale=0.94)
    d.polygon(shell, fill=SLAG)
    K.draw_outline(d, shell, color=INK, width=K.OUTLINE, closed=True, seed=403,
                   wobble=2.4, wavelength=210.0)
    # the cut face: a lighter plane over the right half, same keyline
    cut = _blob_pts(rcx + 16, rcy, rr * 0.92, seed=404, n=11, irr=0.09,
                    yscale=0.94)
    cut = [(x, y) for (x, y) in cut if x >= rcx + 10] + \
          [(rcx + 10, rcy - rr * 0.92), (rcx + 10, rcy + rr * 0.92)]
    d.polygon(cut, fill=SLAG_LIGHT)
    _open_curve(d, [(rcx + 12, rcy - rr * 0.86), (rcx + 12, rcy + rr * 0.86)],
                INK, width=K.DETAIL, seed=405, wobble=1.6, wavelength=140.0)

    # two hairline strata inside the shell, so it reads as rock not as a disc
    for k, f in enumerate((0.78, 0.60)):
        _open_curve(d, _arc_pts(rcx + 16, rcy, rr * f, 268, 92, n=30,
                                yscale=0.94),
                    INK, width=K.FINE, seed=410 + k, wobble=1.2, wavelength=120.0)

    # the dead core: a hollow black heart, the card's one focal detail
    K.draw_disc(d, rcx + 44, rcy, 62, fill=INK, outline=INK, width=K.OUTLINE,
                seed=420, wobble=2.4)
    K.draw_outline(d, _arc_pts(rcx + 44, rcy, 78, 200, 340, n=26), color=EMBER,
                   width=K.DETAIL, closed=False, seed=421, wobble=1.6,
                   wavelength=90.0)

    # three arrows bouncing off the shell and turning away. Flat ember, no
    # gradient: they are a diagram, not a body.
    for k, (ax, ay) in enumerate(((rcx - 128, rcy - 214),
                                  (rcx + 10, rcy - 232),
                                  (rcx + 148, rcy - 196))):
        tip = (ax - 26 - 12 * k, ay - 96)
        _thick_curve(d, [(ax, ay - 8), (ax - 14 - 6 * k, ay - 56), tip],
                     EMBER, seed=430 + k, width=11, wobble=1.8)
        K.draw_disc(d, tip[0], tip[1], 8, fill=EMBER, outline=INK,
                    width=K.DETAIL, seed=440 + k, wobble=1.0)
    _stamp(d, "AIR", rcx - 166, rcy - 344, INK, keyline=PAPER)
    _stamp(d, "OCEAN", rcx + 4, rcy - 366, INK, keyline=PAPER)
    _stamp(d, "WEATHER", rcx + 156, rcy - 328, INK, keyline=PAPER)

    # the one word the card needs: the shell is shut. It sits INSIDE the shell
    # so it reads as stamped on the thing it names.
    C.hero_word(d, 'SHUT', rcx + 30, rcy + 148, INK, stroke_rgb=PAPER,
                stroke_width=3, px=64, margin=40, y_max=600)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# B5 — the_boiling. VOID. Heat coming down, nothing coming back up.
# ---------------------------------------------------------------------------

def render_the_boiling(card, planet="KOI-55"):
    """B5/5 - the boil.

    The star sits at the top right and pours thick ember heat lines down onto a
    small rock, and the lines CONTINUE PAST the rock as thin escaping wisps -
    that overshoot is the whole card: the rock gives back everything it gets and
    keeps nothing. The character is at frame left with both arms up over his
    eyes, mouth a scared down-arc.

    Accent: GOLD (heat). The star's core is the one legal gradient; the heat
    lines and the wisps are flat fills at two different alphas.
    """
    img = _void_frame(seed=501, stars=108)
    sx, sy, sr = 1006, 196, 186
    _star(img, sx, sy, sr, seed=501, glow=0.8)

    rx, ry, rr = 742, 470, 52
    d = ImageDraw.Draw(img, 'RGBA')
    # heat lines from the star down onto the rock: thick, flat, hand-wobbled
    for k, (x0, x1) in enumerate(((sx - 96, rx - 34), (sx - 6, rx + 4),
                                   (sx + 84, rx + 40))):
        _thick_curve(d, [(x0, sy + sr * 0.62),
                         ((x0 + x1) / 2.0, 372 + 14 * k),
                         (x1, ry - rr - 6)],
                     GOLD + (235,), seed=510 + k, width=15 - k, wobble=3.0)
    # and the overshoot: they pass the rock and thin out below it. Kept SHORT
    # and tapered so they fade away instead of ending abruptly, and kept to the
    # rock's column so they clear the HEAT label placed out on the left.
    for k, (x1, x2) in enumerate(((rx - 34, rx - 66), (rx + 4, rx + 26),
                                  (rx + 40, rx + 74))):
        _open_curve(d, [(x1, ry - rr + 4), (x2, 552 + 8 * k), (x2 - 16, 586)],
                    GOLD + (150,), width=K.DETAIL, seed=520 + k, wobble=2.2,
                    wavelength=110.0)
    d = ImageDraw.Draw(img, 'RGBA')
    _void_rock(d, rx, ry, rr, seed=530)
    _open_curve(d, [(rx - rr - 12, ry - rr + 4), (rx, ry - rr - 26),
                    (rx + rr + 12, ry - rr + 6)],
                GOLD + (205,), width=K.FINE, seed=531, wobble=1.4)
    # HEAT labels the INCOMING lines, out in the open void on the left, with a
    # short leader to the middle line - not under the rock where the overshoot
    # wisps pass through.
    _stamp(d, "HEAT", 556, 336, GOLD)
    _open_curve(d, [(616, 342), (676, 356), (700, 376)],
                GOLD + (170,), width=K.FINE, seed=534, wobble=0.9, wavelength=60.0)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# B6 — melted_and_hardened. CREAM. Three panels, no character.
# ---------------------------------------------------------------------------

def render_melted_and_hardened(card, planet="KOI-55"):
    """B6/6 - the three states of a cooked rock.

    MELTED -> DRAINED -> HARDENED, left to right, three panels of the same blob
    at the same size, so the only thing that changes is the fill. Flat fills and
    6px wobbly outlines throughout; no gradient anywhere, because nothing in
    this panel strip is a light source - the liquid is FLAT ember, not glowing.

    Accent: EMBER (the molten panel carries the card).
    """
    img = _cream_frame()
    d = ImageDraw.Draw(img)

    for k in range(3):
        px0 = 66 + k * 392
        px1 = px0 + 350
        # Fill the panel FIRST, then lay the hand-drawn frame on top. (The other
        # order lets the opaque fill erase the frame's top and bottom edges and
        # leaves two vertical stubs.)
        d.rectangle([px0, 158, px1, 442], fill=PAPER)
        frame = [(px0 + 20, 176), (px0 + 175, 170),
                 (px1 - 16, 178), (px1, 202),
                 (px1 - 6, 400), (px1 - 20, 424),
                 (px0 + 14, 430), (px0, 404), (px0 + 4, 204)]
        K.draw_outline(d, frame, color=INK, width=K.DETAIL, closed=True,
                       seed=540 + k, wobble=2.0, wavelength=170.0)

    # --- panel 1: melted, still glowing flat -------------------------------
    cx1 = 241
    _blob(d, cx1, 292, 86, seed=550, fill=EMBER, outline=INK, width=K.OUTLINE,
          irr=0.14, wobble=3.0)
    for k, (ox, oy) in enumerate(((-46, 42), (-6, 58), (38, 44))):
        _thick_curve(d, [(cx1 + ox, 356 + oy * 0.4),
                         (cx1 + ox + 6, 372 + oy), (cx1 + ox - 4, 384 + oy)],
                     EMBER, seed=552 + k, width=13, wobble=1.4)
    _stamp(d, "MELTED", cx1, 476, INK, keyline=PAPER)

    # --- panel 2: drained, the same blob with its bottom gone --------------
    cx2 = 633
    _blob(d, cx2, 268, 82, seed=560, fill=EMBER, outline=INK, width=K.OUTLINE,
          irr=0.14, wobble=3.0)
    # the drain: a stream out of the underside into a puddle
    _thick_curve(d, [(cx2 - 16, 336), (cx2 - 10, 372), (cx2 - 24, 402)],
                 EMBER, seed=562, width=15, wobble=2.0)
    K.draw_smooth(d, [(cx2 - 84, 410), (cx2 - 30, 396), (cx2 + 34, 400),
                      (cx2 + 82, 412), (cx2 + 30, 426), (cx2 - 40, 424)],
                  fill=EMBER, outline=INK, width=K.DETAIL, seed=563, wobble=2.0,
                  wavelength=120.0)
    _stamp(d, "DRAINED", cx2, 476, INK, keyline=PAPER)

    # --- panel 3: hardened, a dull cinder -----------------------------------
    cx3 = 1025
    _blob(d, cx3, 292, 84, seed=570, fill=INK, outline=INK, width=K.OUTLINE,
          irr=0.13, wobble=3.0)
    for k, (a0, a1) in enumerate(((200, 268), (268, 336), (336, 402))):
        _open_curve(d, _arc_pts(cx3 - 10 + 12 * k, 292, 62, a0, a1, n=14,
                                yscale=0.92),
                    SLAG, width=K.FINE, seed=572 + k, wobble=1.4,
                    wavelength=70.0)
    _stamp(d, "HARDENED", cx3, 476, INK, keyline=PAPER)

    # a small ember ember in the middle panel's gutter to carry the accent into
    # the dead panel - one stamp, so the card has one accent and not two.
    _stamp(d, "NO ATMOSPHERE LEFT", 640, 556, EMBER, keyline=PAPER)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# B7 — how_we_found_it. VOID. The light curve and the catalogue. No character.
# ---------------------------------------------------------------------------

def render_how_we_found_it(card, planet="KOI-55"):
    """B7/7 - how this thing was found at all.

    Kepler's method in one picture: a flat light curve with narrow regular dips,
    and a catalogue grid behind it with the 55th slot blanked. No character - the
    script calls it a pure data beat, and it is: this is paperwork.

    Accent: SLAG (grid). Bone carries the trace because it is the light.
    """
    img = _void_frame(seed=601, stars=96)

    # --- the grid of catalogue slots, behind everything -------------------
    d = ImageDraw.Draw(img, 'RGBA')
    # Seven rows so the 55th slot (index 54 = row 6, col 0 in a 9-wide grid)
    # lands INSIDE the grid. A six-row grid put it one row below the last cell,
    # where it hung off the block and collided with the stamp.
    gx0, gy0, cw, ch, gap = 726, 168, 44, 34, 8
    for row in range(7):
        for col in range(9):
            x = gx0 + col * (cw + gap)
            y = gy0 + row * (ch + gap)
            d.rectangle([x, y, x + cw, y + ch], outline=SLAG + (150,), width=2)
    # the 55th slot, inked over and left blank
    bx = gx0 + (54 % 9) * (cw + gap)
    by = gy0 + (54 // 9) * (ch + gap)
    d.rectangle([bx, by, bx + cw, by + ch], fill=DEEP)
    d.rectangle([bx, by, bx + cw, by + ch], outline=GOLD, width=K.DETAIL)
    _stamp(d, "55", bx + cw / 2.0, by + ch / 2.0, GOLD, px=22, bold=True)
    # a short leader from the 55 cell down to its label, clear of the axis
    lx, ly = bx + cw / 2.0, by + ch
    _open_curve(d, [(lx, ly + 4), (lx, ly + 30), (lx + 90, ly + 46)],
                GOLD, width=K.FINE, seed=605, wobble=0.8, wavelength=60.0)
    _stamp(d, "A SLOT NOBODY NAMED", lx + 210, ly + 50, GOLD)

    # --- the light curve, on a bone axis ----------------------------------
    ax0, ax1, ay = 96, 640, 470
    _open_curve(d, [(ax0, ay), ((ax0 + ax1) / 2.0, ay), (ax1, ay)],
                BONE, width=K.DETAIL, seed=610, wobble=0.8, wavelength=140.0)
    # four narrow dips, evenly spaced, each a small V notching the baseline
    n = 4
    span = (ax1 - ax0 - 120) / float(n)
    for k in range(n):
        cx = ax0 + 60 + span * (k + 0.5)
        _open_curve(d, [(cx - 16, ay), (cx, ay + 54), (cx + 16, ay)],
                    GOLD, width=K.DETAIL, seed=620 + k, wobble=0.8,
                    wavelength=40.0)
        _stamp(d, "DIP", cx, ay + 84, BONE)
    # the axis labels
    _stamp(d, "LIGHT", ax0 + 6, ay - 46, BONE)
    _stamp(d, "TIME", ax1 - 4, ay + 84, BONE)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# B8 — the_spiral_in. CREAM. Cutaway side-on.
# ---------------------------------------------------------------------------

def render_the_spiral_in(card, planet="KOI-55"):
    """B8/8 - the fall.

    A dotted spiral tightening into a flat ember half-disc at the right edge,
    with concentric depth rings behind it. The rings are the point: there is
    nothing under the path but more path. The character stands at lower left
    pointing straight down at the tightening line, mouth a scared down-arc.

    Accent: EMBER (the star edge). Rings are SLAG, path dots are INK.
    """
    img = _cream_frame()

    # concentric depth rings, deepest first
    d = ImageDraw.Draw(img)
    for k, rr in enumerate((392, 320, 252)):
        _open_curve(d, _arc_pts(1298, 400, rr, 92, 268, n=40), SLAG,
                    width=K.DETAIL, seed=650 + k, wobble=2.0, wavelength=190.0)
    # the star: a flat half-disc at the frame edge, INK keyline
    K.draw_disc(d, 1298, 400, 196, fill=EMBER, outline=INK, width=K.OUTLINE,
                seed=660, wobble=3.0)
    K.draw_disc(d, 1298, 400, 196, fill=None, outline=INK, width=K.OUTLINE,
                seed=661, wobble=3.0)

    # the dotted spiral, tightening inward. Sampled in polar coordinates around
    # the star so the path curves as it tightens instead of running straight at
    # the target. Dots shrink as they approach, and every other one is dropped
    # along the wide outer half so the path stays visibly DOTTED there instead
    # of closing up into a solid line.
    scx, scy = 1298, 400
    for i in range(150):
        t = i / 149.0
        if t < 0.55 and i % 2:
            continue
        R = 210 + 560 * (1.0 - t) ** 1.5
        a = math.radians(150 + 118 * t)
        x = scx + R * math.cos(a)
        y = scy + 0.45 * R * math.sin(a)
        rr = max(2, 5 - int(3 * t))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=INK)

    # DOWN labels the dive, so it sits beside the path's steep inner descent with a
    # leader onto it - not parked in the far corner where nothing is happening.
    _stamp(d, "DOWN", 1046, 200, INK, keyline=PAPER)
    _open_curve(d, [(1104, 216), (1146, 244), (1172, 280)],
                INK, width=K.FINE, seed=670, wobble=1.0, wavelength=70.0)
    _stamp(d, "NOTHING UNDER IT", 900, 604, INK, keyline=PAPER)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# B9 — it_survived_being_eaten. VOID. The uncertainty, drawn as uncertainty.
# ---------------------------------------------------------------------------

def render_it_survived_being_eaten(card, planet="KOI-55"):
    """B9/9 - it might have been here before.

    Two frames side by side, and the card is honest that it does not know which
    is which: LEFT, a swollen star edge drawn OVER the rock, so the rock is
    half-eaten; RIGHT, the same rock sitting just outside a thin arc, intact.
    Both are thin wobbly outlines rather than solid bodies - a solid pair would
    assert a fact the narration is careful not to assert. The character stands
    between them, hands up, palms out, mouth a zigzag.

    Accent: GOLD (the arc that both panels share).
    """
    img = _void_frame(seed=701, stars=104)

    # LEFT panel: the star's edge, swollen out over the rock
    d = ImageDraw.Draw(img, 'RGBA')
    lcx, lcy = 352, 404
    # a thick ember arc, bulging left, as the star's swollen limb
    arc = _arc_pts(lcx + 96, lcy, 250, 108, 252, n=44)
    _thick_curve(d, arc, EMBER + (215,), seed=710, width=26, wobble=3.0)
    _open_curve(d, arc, GOLD + (235,), width=K.DETAIL, seed=711, wobble=1.8,
                wavelength=150.0)
    # the rock, drawn UNDER the arc's inner edge so the edge covers half of it
    _void_rock(d, lcx + 156, lcy + 6, 56, seed=712)
    _stamp(d, "SWALLOWED", lcx, lcy + 268, GOLD)

    # RIGHT panel: the same rock, outside a thin arc, intact
    rcx, rcy = 936, 404
    arc2 = _arc_pts(rcx + 116, rcy, 250, 108, 252, n=44)
    _open_curve(d, arc2, GOLD + (170,), width=K.DETAIL, seed=720, wobble=2.2,
                wavelength=150.0)
    _void_rock(d, rcx + 128, rcy - 8, 56, seed=721)
    _stamp(d, "OR NOT", rcx, rcy + 268, GOLD)

    # the question mark between the two frames: thin, gold, wobbled. This is the
    # whole card, so it gets the card's largest drawn mark.
    C.hero_word(d, '?', 644, 330, GOLD, stroke_rgb=INK, stroke_width=3,
                px=180, margin=40, y_max=430)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# B10 — disturbing_part. CREAM. Near-empty. One rock, one man.
# ---------------------------------------------------------------------------

def render_disturbing_part(card, planet="KOI-55"):
    """B10/10 - it is allowed to die twice.

    The emptiest card in the segment on purpose. One small rock, almost nothing
    around it, and the character beside it with his finger raised and his mouth
    open. The card is quiet because the idea is quiet - this is not an action
    beat, it is the narrator stepping aside and letting you look at a small dead
    rock.

    Accent: SLAG (the rock). Almost nothing else on screen.
    """
    img = _cream_frame()

    # a soft washed halo so the small rock is not floating on dead paper, plus
    # one thin orbit line so it reads as a world and not as a pebble
    img = _wash(img, [(560, 302), (700, 268), (802, 330), (776, 438),
                      (628, 462), (528, 396)], SLAG_LIGHT, 74, seed=750,
                wobble=14.0, blur=26)

    d = ImageDraw.Draw(img)
    K.draw_disc(d, 664, 366, 78, fill=SLAG, outline=INK, width=K.OUTLINE,
                seed=751, wobble=3.0)
    # the single thin orbit line, fading out to the left
    _open_curve(d, _arc_pts(664, 366, 156, 152, 28, n=40), INK, width=K.FINE,
                seed=752, wobble=1.8, wavelength=150.0)

    # the character does the acting here. Nothing else on the card.
    # The orbit arc's lowest point is (664, 522), so the label clears it BELOW
    # at y=590 rather than sitting on the line.
    _stamp(d, "ONE SMALL ROCK", 664, 590, INK, keyline=PAPER)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# B11 — the_last_pass. VOID. The X.
# ---------------------------------------------------------------------------

def render_the_last_pass(card, planet="KOI-55"):
    """B11/11 - the next pass is the last one.

    The orbit path is drawn as a spiral that runs straight into a flat black
    wall at the star's surface, and one bold amber X is stamped over the final
    loop. The wall and the X are the card; nothing competes with them. The
    character is small at bottom centre, very still, scared.

    Accent: GOLD (the X, the wall's edge). The wall itself is INK - it is the
    absence of a path, not a light source.
    """
    img = _void_frame(seed=801, stars=104)

    # the star's surface as a hard wall on the right
    d = ImageDraw.Draw(img, 'RGBA')
    _star(img, 1150, 360, 214, seed=801, glow=0.7)
    d = ImageDraw.Draw(img, 'RGBA')
    # the wall: a flat INK slab over the star's left limb
    d.polygon([(1010, 84), (1140, 84), (1140, 720), (1006, 720),
               (992, 560), (1000, 340)], fill=INK)
    _open_curve(d, [(1010, 84), (1006, 340), (992, 560), (1006, 720)],
                GOLD, width=K.DETAIL, seed=802, wobble=2.0, wavelength=200.0)

    # the spiral path, ending AT the wall. Same dotted treatment as beat 8: thin
    # the wide outer half so it reads as a dotted orbit, not a painted line.
    scx, scy = 1010, 400
    for i in range(140):
        t = i / 139.0
        if t < 0.55 and i % 2:
            continue
        R = 200 + 540 * (1.0 - t) ** 1.5
        a = math.radians(160 + 110 * t)
        x = scx + R * math.cos(a)
        y = scy + 0.45 * R * math.sin(a)
        rr = max(2, 5 - int(3 * t))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=GOLD + (200,))

    # the X, stamped over the final loop
    C.hero_word(d, 'X', 792, 372, GOLD, stroke_rgb=INK, stroke_width=4,
                px=150, margin=40, y_max=520)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# B12 — outro_cinder. CREAM. The closing card.
# ---------------------------------------------------------------------------

def render_outro_cinder(card, planet="KOI-55"):
    """B12/12 - one fall left.

    The closing image: the catalogue name stamped large and dead across the top,
    a small grey cinder underneath with its orbit line faded almost to nothing,
    and the character at the right edge looking at it, flat-mouthed, arms down.
    No drama in the drawing - the drama was spent two cards ago.

    Accent: SLAG. The card is grey on cream, which is the point: nothing is
    coming back.
    """
    img = _cream_frame()

    d = ImageDraw.Draw(img)
    # The catalogue name, hand-lettered across the art. Offset LEFT of the
    # title strip's own centred KOI-55 and dropped onto the cinder's shoulder,
    # so it reads as a second deliberate stamp rather than a grey echo stacked
    # directly under the header.
    C.hero_word(d, 'KOI-55', 452, 268, SLAG,
                stroke_rgb=PAPER, stroke_width=3, px=76, margin=40, y_max=350)

    # the cinder, sitting under the hand-lettered name
    _blob(d, 430, 420, 66, seed=810, fill=SLAG, outline=INK, width=K.OUTLINE,
          irr=0.12, wobble=2.6)
    # its orbit line, faded right out - almost gone. Radius 120 keeps its lowest
    # point at y=540, well clear of the label below.
    _open_curve(d, _arc_pts(430, 420, 120, 168, 20, n=40), SLAG, width=K.FINE,
                seed=811, wobble=2.0, wavelength=150.0)
    _stamp(d, "ONE FALL LEFT", 430, 592, INK, keyline=PAPER)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Dispatch. Keys are the beat ids from work/segments/koi55/script.json.
# ---------------------------------------------------------------------------

RENDERERS = {
    'hook_closest_orbit': render_hook_closest_orbit,
    'hook_five_hours': render_hook_five_hours,
    'hook_breath': render_hook_breath,
    'bare_rock_world': render_bare_rock_world,
    'the_boiling': render_the_boiling,
    'melted_and_hardened': render_melted_and_hardened,
    'how_we_found_it': render_how_we_found_it,
    'the_spiral_in': render_the_spiral_in,
    'it_survived_being_eaten': render_it_survived_being_eaten,
    'disturbing_part': render_disturbing_part,
    'the_last_pass': render_the_last_pass,
    'outro_cinder': render_outro_cinder,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table. The frame
    generator reads the module attribute RENDERERS directly; this wrapper exists
    for convention and is safe to call twice."""
    C.register(mapping if mapping is not None else RENDERERS)
    return RENDERERS


# ---------------------------------------------------------------------------
# Self-test. Renders every beat to work/segments/koi55/cardsheet/beat_<NN>.png.
# Run:  cd work/segments && python koi55/_cards.py
# ---------------------------------------------------------------------------

# Beat -> (n, register, caption, stickman or None).
# The captions here are SHORT PLACEHOLDER tags for the contact sheet only - the
# real caption text is supplied by the frame generator's schedule at run time and
# is never the narration line.
SELFTEST = [
    (1, 'hook_closest_orbit', 'void',
     'CLOSER THAN WE THOUGHT',
     dict(pose='standing', expression='flat', height=290, x_center=250, y_top=352)),
    (2, 'hook_five_hours', 'cream',
     'THAT IS THE WHOLE YEAR',
     None),
    (3, 'hook_breath', 'void',
     'REPEATS BEFORE YOU FINISH',
     dict(pose='pointing', expression='oval', height=300, x_center=1096, y_top=330)),
    (4, 'bare_rock_world', 'cream',
     'A SHELL AND A DEAD CORE',
     dict(pose='shrugged', expression='zigzag', height=270, x_center=226, y_top=352)),
    (5, 'the_boiling', 'void',
     'HEAT DOWN, NOTHING BACK',
     dict(pose='shielding_eyes', expression='frown', height=280, x_center=238, y_top=346)),
    (6, 'melted_and_hardened', 'cream',
     'MELTED, DRAINED, HARDENED',
     None),
    (7, 'how_we_found_it', 'void',
     'KEPLER ONLY SAW A SHADOW',
     None),
    (8, 'the_spiral_in', 'cream',
     'FALLING INWARD, PASS BY PASS',
     dict(pose='pointing', expression='frown', height=270, x_center=372, y_top=366)),
    (9, 'it_survived_being_eaten', 'void',
     'IT MAY HAVE SURVIVED THIS',
     dict(pose='hands_up', expression='zigzag', height=280, x_center=644, y_top=352)),
    (10, 'disturbing_part', 'cream',
     'IT IS ALLOWED TO DIE TWICE',
     dict(pose='pointing', expression='oval', height=290, x_center=980, y_top=350)),
    (11, 'the_last_pass', 'void',
     'THE NEXT PASS IS THE LAST',
     dict(pose='standing', expression='frown', height=270, x_center=470, y_top=356)),
    (12, 'outro_cinder', 'cream',
     'ONE FALL LEFT',
     dict(pose='hands_down', expression='flat', height=300, x_center=1080, y_top=340)),
]


def _selftest():
    out_dir = os.path.join(_HERE, 'cardsheet')
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    assert set(bid for _, bid, _, _, _ in SELFTEST) == set(RENDERERS), \
        'self-test beats and RENDERERS keys disagree'
    for n, bid, reg, caption, sm in SELFTEST:
        card = {'id': bid, 'caption': caption, 'stickman': sm}
        img = RENDERERS[bid](card, 'KOI-55')
        assert img.size == (W, H), '%s rendered %s, not 1280x720' % (bid, img.size)
        assert img.mode == 'RGB', '%s rendered mode %s, not RGB' % (bid, img.mode)
        path = os.path.join(out_dir, 'beat_%02d.png' % n)
        img.save(path)
        print('%2d  %-26s %-5s  %s  ->  beat_%02d.png'
              % (n, bid, reg, ('%s/%s' % (sm['pose'], sm['expression']))
                 if sm else 'no-character', n))
    print('OK  %d beats rendered to %s' % (len(SELFTEST), out_dir))
    return 0


if __name__ == '__main__':
    sys.exit(_selftest())



