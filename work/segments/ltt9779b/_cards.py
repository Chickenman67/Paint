# work/segments/ltt9779b/_cards.py — ALL 14 beats of segment 9 (LTT 9779 b).
#
# Subject: a super-Earth so reflective it is the brightest thing in its own
# system — it swallows almost no starlight and hands nearly all of it back.
# Tone target: quiet star, loud planet; borrowed light; a mirror, not a coal.
#
# ONE module, not one per beat: the frame generator registers RENDERERS from
# whatever modules it finds, and the segment is authored as a single
# `_cards.py` per the build brief. The module-level RENDERERS dict is the
# load-bearing name; `register()` is a convenience wrapper.
#
# CANON COMPLIANCE (work/STYLE_CANON.md overrides CLAUDE.md §4/§7):
#   * Layout A — rows 0..83 paper title strip (C._header), full-bleed art rows
#     84..719, NO caption band. The caption floats on the art at (70, 652).
#   * Type — T.HEADER_PX / T.LABEL_PX / T.CAPTION_PX / T.STAMP_PX only, all via
#     lib.type (comicbd.ttf / comic.ttf). Consolas is retired. No new sizes:
#     the only off-scale size used is the hero-word ramp inside C.hero_word.
#   * Stroke — K.OUTLINE (6) on large shapes, K.DETAIL (4) on mid detail,
#     K.FINE (2) on specks/ticks. Never 3 px on a large shape.
#   * Lines — smooth curves with LOW-frequency wobble (K.wobble_points +
#     Catmull-Rom), never per-vertex jitter.
#   * Two registers — 'void' cards are near-black starfields with a CREAM
#     character; 'cream' cards are paper with a DARK-ink character. The theme is
#     chosen per card, never defaulted.
#   * The character is GROUNDED on a wobbled horizon band (K.draw_ground) on
#     every cream card where he is a subject rather than a scale figure
#     (STYLE_CANON addendum "the character is usually GROUNDED").
#   * Labels sit ON or immediately BESIDE their subject (same addendum). Overlap
#     between a label and its subject is authentic, not a defect.
#   * Deterministic — every wobble/stipple/starfield/blend call takes an explicit
#     seed=. No global random state, no builtin hash(). Re-renders are identical.
#
# REGISTER DISCIPLINE (PALETTE_SPEC §3):
#   * The ONLY smooth gradients are C._radial_core on emissive bodies: the
#     little M-dwarf on `name_card` / `planet_is_loud`, and nothing else.
#     Gradients are legal on emissive bodies and the space field, never on a
#     planet, an orbit ellipse, a diagram, a character, a caption or the strip.
#   * Planets use C.space_body (painterly, no black outline) on void cards and
#     flat fill + 6 px ink keyline on cream cards.
#   * Soft light is drawn with `_soft_halo`, NEVER `C.add_glow`. add_glow fills
#     an inner ellipse at full `strength` and blurs by only 0.40 * size, then
#     multiplies by a HARD circular cutoff — a broad SATURATED PLATEAU with an
#     abrupt rim. Correct for a white core on black, and on this segment's
#     near-black fields it shipped a visible tinted DISC behind the subject on
#     eight of the fourteen cards. `_soft_halo` is a true radial falloff to
#     zero at r.
#
# NO RED ON A CARD. The character's shirt #C83232 is the only red in the whole
# show, so he never dissolves into a background. The single documented exception
# is `the_bad_number`, which has NO character on it (so no collision is
# physically possible) and whose whole subject, per the script, is a number
# circled twice in red pen. See PALETTE_SPEC §4.
#
# NO import side effects. The frame generator merges RENDERERS via
# C.register(m.RENDERERS).

import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

# `work/` must be on sys.path before the lib.* imports below, so that running
# this file directly (`python ltt9779b/_cards.py`) resolves the same modules the
# frame generator resolves. The frame generator already puts both on the path;
# this is what makes the self-test standalone.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))   # .../work
for _p in (_HERE, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib.type as T
import lib.ink as K
import lib.cardframe as C

W, H = C.W, C.H

# ---------------------------------------------------------------------------
# SEGMENT 9 PALETTE — locked here, spec in PALETTE_SPEC.md.
# The mix-cardframe.PAL values (which are segment 3's) except where this
# segment needs its own identity: a SILVER planet, because the whole story is
# about a world that hands light back. Amber still carries every caption on the
# void cards; red is still the character's alone.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':    (20, 22, 28),      # #14161C slate-black  — all linework, header glyphs
    'paper':  (242, 234, 214),   # #F2EAD6 bone-cream  — title strip, cream cards
    'deep':   (5, 7, 14),        # #05070E void         — every space field
    'silver': (198, 212, 221),   # #C6D4DD mirror silver — the planet, cloud deck, glare
    'amber':  (232, 163, 61),    # #E8A33D signal amber — captions on deep, arrows, glint
    'steel':  (74, 116, 132),    # #4A7484 steel teal  — night side, metal depth, Earth
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
SILVER = MY_PAL['silver']
AMBER = MY_PAL['amber']
STEEL = MY_PAL['steel']
# The one legal red: the character's shirt. Never a card accent.
SHIRT = (200, 50, 50)

# BONE_ISH is the neutral line colour for a void card's non-accent marks (orbit
# lines, plot panels, trace 1). Held as a module constant so no card in this
# segment reaches for a colour by accident.
BONE_ISH = (208, 218, 226)

# SAND is NOT a seventh hue — it is a documented 70/30 blend of two palette
# colors (paper into amber) and is used only as the ground band on cream cards
# where the character is a subject. Derived, never hand-picked.
SAND = (int(PAPER[0] * 0.70 + AMBER[0] * 0.30),
        int(PAPER[1] * 0.70 + AMBER[1] * 0.30),
        int(PAPER[2] * 0.70 + AMBER[2] * 0.30))

# The near-white the blazing subject is painted in. It is the top of the silver
# ramp (0.88 toward white) — the same hue as SILVER, one value up, so a blazing
# dayside and a calm planet are visibly the same material at two exposures.
WHITE_HOT = (int(SILVER[0] + (255 - SILVER[0]) * 0.88),
             int(SILVER[1] + (255 - SILVER[1]) * 0.88),
             int(SILVER[2] + (255 - SILVER[2]) * 0.88))

# The fallback character placement, used only by the __main__ self-test. The
# live schedule supplies card['stickman']; C._draw_stickman reads the card.
SELF_TEST_SMITHMAN = {
    'hook_inverted':    dict(x_center=286, y_top=170, height=450,
                             pose='pointing', expression='flat'),
    # Feet at 612 = the _ground horizon on this card exactly (STYLE_CANON
    # "grounded on a horizon"). At y_top=250 the feet fell at 642 and were
    # buried in the sand.
    'metal_sky':        dict(x_center=206, y_top=220, height=392,
                             pose='hands_up', expression='oval'),
    'coin_in_the_dark': dict(x_center=1032, y_top=196, height=428,
                             pose='hands_up', expression='oval'),
    # Feet at 588 = the _ground horizon on this card exactly.
    'should_be_an_oven': dict(x_center=932, y_top=186, height=402,
                              pose='shrugged', expression='flat'),
    'no_survival':      dict(x_center=1016, y_top=166, height=456,
                             pose='hands_up', expression='frown'),
    # Feet land EXACTLY on the _ground horizon at y=606: y_top + height = 606.
    # At y_top=286 / height=354 the feet fell at 640, i.e. 34 px BELOW the
    # horizon, so his legs were buried in the sand and he read as a bust.
    # Height is 380 (y_top 226) rather than 430 so his head TOP clears the
    # incoming arrow's shaft, which now runs at y ~= 205 across x 962..1058.
    'borrowed_light':   dict(x_center=1010, y_top=226, height=380,
                             pose='cowering', expression='zigzag'),
}


# ---------------------------------------------------------------------------
# Shared geometry / drawing helpers
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output).

    Local rather than K._smooth_open so the open path is guaranteed correct and
    so `_open_curve` (a hairline) and `_thick_curve` (a filled glyph) always
    trace exactly the same centreline for the same seed.
    """
    p = list(pts)
    if len(p) < 3:
        return p
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
    """An OPEN hand-wobbled smooth curve, stroked. Mirrors K.draw_outline's line
    quality (smooth + low-frequency wobble) for paths that are not closed."""
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    if len(dense) < 2:
        return dense
    draw.line(dense, fill=color, width=width, joint='curve')
    return dense


def _thick_curve(draw, points, fill, seed=0, width=24, wobble=2.0, wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region.

    NOT draw.line(..., width=24, joint='curve'): at this density the Catmull-Rom
    output has near-duplicate consecutive points and PIL renders each as a
    rectangle plus a round cap, so a wide line grows hairline nubs along the
    whole path. The stroke is built geometrically instead — offset the smooth
    centreline by +/- half-width along its normal and weld the two rails into one
    closed polygon. Clean edges, and it obeys the smooth-curve rule exactly the
    way K.draw_smooth does for closed shapes.
    """
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    n = len(dense)
    if n < 2:
        return dense
    hw = width / 2.0
    normals = []
    for i in range(n):
        a = dense[max(0, i - 1)]
        b = dense[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        normals.append((-dy / L, dx / L))
    outer = [(p[0] + nx * hw, p[1] + ny * hw) for p, (nx, ny) in zip(dense, normals)]
    inner = [(p[0] - nx * hw, p[1] - ny * hw) for p, (nx, ny) in zip(dense, normals)]
    region = outer + inner[::-1]
    draw.polygon(region, fill=fill)
    return region


def _stroke_band(pts, width):
    """Turn an open polyline into a CLOSED polygon of the given stroke width by
    offsetting perpendicular to the path, so it can go through the working
    closed K.draw_smooth path at a flat alpha (no black keyline on a space
    element — Register S has no hard edge)."""
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


def _vline(draw, x, y0, y1, color, width=2, seed=0, wobble=1.0):
    """A short hand-wobbled vertical rule."""
    return _open_curve(draw, [(x, y0), (x, (y0 + y1) / 2.0), (x, y1)],
                       color, width, seed=seed, wobble=wobble, wavelength=60.0)


def _hrule(draw, y, x0, x1, color, width=2, seed=0, wobble=1.0):
    """A short hand-wobbled horizontal rule."""
    return _open_curve(draw, [(x0, y), ((x0 + x1) / 2.0, y), (x1, y)],
                       color, width, seed=seed, wobble=wobble, wavelength=90.0)


def _ellipse_pts(cx, cy, rx, ry, n=40):
    """Sample an ellipse as a closed polyline."""
    return [(cx + rx * math.cos(math.tau * i / n),
             cy + ry * math.sin(math.tau * i / n)) for i in range(n)]


def _arc_pts(cx, cy, r, a0_deg, a1_deg, n=40, ry=None):
    """Sample an arc. PIL angles: 0 = 3 o'clock, y grows downward, so 180 = left,
    270 = up, 360 = right."""
    ry = r if ry is None else ry
    pts = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        pts.append((cx + r * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _arrow_head(draw, tip, ang_deg, color, length, half_w, seed=0):
    """A solid triangular arrowhead pointing along `ang_deg` (PIL convention)."""
    a = math.radians(ang_deg)
    bx, by = tip[0] - length * math.cos(a), tip[1] - length * math.sin(a)
    px, py = -math.sin(a) * half_w, math.cos(a) * half_w
    draw.polygon([tip, (bx + px, by + py), (bx - px, by - py)], fill=color)


def _arrow(draw, x0, y0, x1, y1, color, width, head_len, head_half, seed=0,
           wobble=1.6):
    """A shaft (a filled thick curve) plus a solid head. Used for the
    reflected/absorbed beams and the incoming-light arrow."""
    _thick_curve(draw, [(x0, y0), ((x0 + x1) / 2.0, (y0 + y1) / 2.0), (x1, y1)],
                 color, seed=seed, width=width, wobble=wobble, wavelength=180.0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    _arrow_head(draw, (x1, y1), ang, color, head_len, head_half, seed=seed)
    return ang


def _tiny(draw, text, cx, cy, fill, px=T.STAMP_PX):
    """A locked-family REGULAR annotation, centred, 1 px keyline. Diagram labels
    only. px defaults to the locked STAMP_PX; the few cards that need a larger
    annotation go through T.LABEL_PX or T.draw_label instead, so the set of
    sizes stays closed."""
    font = T.load_font_at(px, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    T.draw_outlined_text(draw, (cx - w / 2.0 - x0, cy - h / 2.0 - y0), text, font,
                         fill=fill, stroke=fill, stroke_width=T.STAMP_STROKE)


def _label(draw, text, cx, cy, fill=None):
    """A planet/subject label in the light casual hand, centred on (cx, cy).
    T.LABEL_PX — the locked label size. Placed ON or immediately BESIDE its
    subject, per the STYLE_CANON addendum."""
    fill = INK if fill is None else fill
    font = T.load_font(T.LABEL_PX, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    T.draw_outlined_text(draw, (cx - w / 2.0 - x0, cy - h / 2.0 - y0), text, font,
                         fill=fill, stroke=fill, stroke_width=0)


def _soft_halo(img, cx, cy, r, color, strength=90, falloff=2.4):
    """A halo with a TRUE radial falloff to zero at r — no plateau, no hard rim.

    WHY NOT C.add_glow. It fills an inner ellipse at `strength` and blurs it by
    only 0.40*small, then multiplies by a hard circular cutoff. That is a broad
    SATURATED PLATEAU with an abrupt edge, which is exactly right for the
    pulsar core (a white core on a black field) and exactly wrong for a
    coloured halo. Every void card in this segment is near-black, so each
    add_glow call in it shipped a visible tinted DISC with a rim — a grey ball
    behind the crescent on smile_at_mild_star, a brown ball at the glint on
    hook_inverted, a huge grey plate behind the blazing world on no_survival.

    This mask is `(1 - t)**falloff` clamped at t<=1: 1 at the centre, exactly 0
    at r, and 0 in the corners (t > 1). No plateau, no cutoff, no rim. Built at
    quarter resolution and upscaled — a halo is a low-frequency field, so that
    is visually identical and cheap.

    Additive, so a dark field picks up light without washing out.
    """
    r = max(4, int(r))
    cx, cy = int(cx), int(cy)
    sw = max(6, r // 4)
    yy, xx = np.mgrid[0:sw, 0:sw].astype(np.float32)
    t = np.sqrt((xx - sw / 2.0) ** 2 + (yy - sw / 2.0) ** 2) / (sw / 2.0)
    a = np.clip(1.0 - t, 0.0, 1.0) ** falloff * float(strength)
    mask = Image.fromarray(a.astype(np.uint8), 'L').resize((r * 2, r * 2),
                                                           Image.BILINEAR)
    halo = Image.new('RGB', mask.size, tuple(color))
    halo = ImageChops.multiply(halo, Image.merge('RGB', (mask, mask, mask)))
    box = (cx - r, cy - r, cx + r, cy + r)
    region = img.crop(box).convert('RGB')
    img.paste(ImageChops.add(region, halo), (box[0], box[1]))
    return img


def _glare(img, cx, cy, r, color, a0=190, seed=0):
    """Light spiked straight at the viewer: nested alpha spikes along both axes
    with alpha and thickness falling along their length, feathered, plus a soft
    additive halo. Used only where the card's SUBJECT is light coming back off
    the planet.

    Each spike is built by drawing symmetric rectangles OUTWARD from the centre
    on BOTH sides, so the flare is centred on the body. (The first version
    mirrored the right-hand strip by subtracting an already-advanced x, which
    collapsed the whole left half of the flare onto the centre and left the
    glare visibly off-centre.)

    Built on its own RGBA layer and composited once, so the spikes feather at
    their distal ends and never show a hard rectangular corner.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    L = r * 4.6
    steps = 30
    for i in range(steps):
        t = i / float(steps - 1)
        half = max(2, int(r * 0.60 * (1.0 - t) ** 2.0) + 2)
        off = t * L
        a = int(a0 * (1.0 - t) ** 1.6) + 3
        step = L / steps + 2
        # horizontal, both directions
        ld.rectangle([cx + off, cy - half, cx + off + step, cy + half],
                     fill=color + (a,))
        ld.rectangle([cx - off - step, cy - half, cx - off, cy + half],
                     fill=color + (a,))
    # the vertical spike is shorter — a wide flare reads as a lens fault, a tall
    # one reads as a star
    LV = r * 2.6
    for i in range(steps):
        t = i / float(steps - 1)
        half = max(2, int(r * 0.48 * (1.0 - t) ** 2.0) + 2)
        off = t * LV
        a = int(a0 * 0.8 * (1.0 - t) ** 1.6) + 3
        step = LV / steps + 2
        ld.rectangle([cx - half, cy + off, cx + half, cy + off + step],
                     fill=color + (a,))
        ld.rectangle([cx - half, cy - off - step, cx + half, cy - off],
                     fill=color + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(max(5, int(r * 0.09))))
    img = Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')
    return _soft_halo(img, cx, cy, int(r * 2.4), color, strength=70, falloff=2.6)


def _crescent(draw, cx, cy, r, a0_deg, a1_deg, color, alpha, thick=26):
    """A luminous crescent hugging the limb between two angles, brightest AT the
    limb and tapering to a point at both tips.

    Built as ONE polygon, not a stack of nested arcs. The outer rail sits on the
    limb; the inner rail is offset inward by a width that follows a raised
    cosine along the arc. That gives a single smooth band with a smooth width
    profile. The previous version drew N nested thin arcs at decreasing alpha,
    which on screen read as a bundle of scratches over the planet — the single
    worst element on smile_at_mild_star.

    PIL screen angles: 0 = 3 o'clock, y grows downward, so 270 = up and the top
    limb is 180..360.
    """
    n = 96
    outer, inner = [], []
    for i in range(n + 1):
        t = i / float(n)
        a = math.radians(a0_deg + (a1_deg - a0_deg) * t)
        ca, sa = math.cos(a), math.sin(a)
        w = 0.5 * thick * (math.sin(math.pi * t) ** 0.55)
        outer.append((cx + r * ca, cy + r * sa))
        inner.append((cx + (r - w) * ca, cy + (r - w) * sa))
    draw.polygon(outer + inner[::-1], fill=color + (alpha,))


def _ray(draw, x0, y0, x1, y1, color, alpha, width, seed, core=0.34):
    """A star ray / light shaft: a soft flat-alpha band with a brighter thin core
    line down the middle.

    Drawn as ONE nearly-straight band with only a whisper of wobble. The first
    version used a wide band at high wobble and read as a fat orange WORM with
    round ends — six of them across irradiated_dayside looked like tentacles.
    A ray is straight and thin; the softness has to come from the alpha, not
    from the width.
    """
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    pts = [(x0, y0), (mx, my), (x1, y1)]
    _draw_band(draw, pts, width, color, alpha, seed, wobble=0.9, wavelength=260.0)
    _open_curve(draw, pts, color, width=max(K.FINE, int(width * core)), seed=seed + 1,
                wobble=0.9, wavelength=260.0)


def _soft_wash(img, points, rgb, alpha, seed=0, wobble=14.0, wavelength=180.0,
               blur=20):
    """A painterly FLAT-colour region with SOFT edges.

    Every wash on this segment (the sand field behind the cutaway, the sky patch
    behind the small gleaming world) is a flat fill on its own RGBA layer,
    wobbled by K.draw_smooth and then blurred. Drawn straight onto the card it
    leaves a hard organic edge and reads as a STICKER — the sky patch behind the
    world on borrowed_light came out as a visible pale bubble. Returns a new RGB
    image.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=tuple(rgb) + (int(alpha),), outline=None,
                  seed=seed, wobble=wobble, wavelength=wavelength, closed=True)
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _world(img, cx, cy, r, base, band, hi, seed=0, bands=3):
    """C.space_body with the band colour pulled IN toward the base colour.

    C.space_body's contour bands are drawn as concentric ellipses at
    `r*0.24 / 0.53 / 0.82` with alpha 150 and width `r*0.055`. When `band` is
    far from `base` those three ellipses read as a BULLSEYE — a painted target,
    not a planet. That is the exact failure STYLE_CANON's addendum names, and
    the first pass of this module hit it on coin_in_the_dark and
    smile_at_mild_star.

    The reference's planets are grey spheres with soft wavy strata, so strata
    are right; the contrast between them and the base is what is wrong. This
    wrapper mixes `band` 60% toward `base` before handing it over, which keeps
    the painterly marbling but drops it well below the threshold where it reads
    as rings. Below r=30 the band count is dropped too.
    """
    band = tuple(int(base[k] * 0.40 + band[k] * 0.60) for k in range(3))
    return C.space_body(img, cx, cy, r, base=base, band=band, hi=hi, seed=seed,
                        bands=(2 if r < 40 else bands))


def _ground(draw, y_top, fill=SAND, seed=0):
    """The wobbled horizon band the character stands on (STYLE_CANON addendum:
    ground him on any cream card where he is a subject). Flat fill, 6 px keyline."""
    return K.draw_ground(draw, 0, W, y_top, H, fill, seed=seed,
                         width=K.OUTLINE, roughness=5.0)


def _void_card(seed, stars=120):
    """A Register-S space field. A distinct seed per card so no two starfields in
    the segment are the same frame with the same stars."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars, top=(7, 9, 18), bot=(13, 16, 32))
    return img


def _finish(img, card, planet, paper_band, dark_bg):
    """The Layout-A tail every card in this segment shares: title strip, then the
    schedule-driven character, then the one floating caption at (70, 652)."""
    C._header(img, planet, paper_band=paper_band)
    C._draw_stickman(img, card, theme=('dark' if dark_bg else 'light'))
    C._caption(img, card['caption'], 70, 652, dark_bg=dark_bg)
    return img


# ---------------------------------------------------------------------------
# 1. hook_inverted — HOOK. VOID. The nearly-black world and one hard glint.
# ---------------------------------------------------------------------------

def render_hook_inverted(card, planet="LTT 9779 b"):
    """B1 — the inversion. A near-black planet fills the right two thirds of a
    near-black starfield with ONE hard amber glint burning on its upper-left limb
    and a thin silver crescent riding the same limb. The character stands at
    lower left, flat-line deadpan, holding out a dull pebble — he is offering the
    audience the thing this world is NOT.

    One focal point: the glint. The planet body is painted almost the colour of
    the sky on purpose, so the only thing the eye finds is the light coming
    back off it."""
    img = _void_card(seed=901, stars=128)
    cx, cy, r = 892, 360, 252

    # THE BODY: a near-black world, drawn as a FLAT disc with a single soft
    # upper-left sheen and a dark lower-right crescent. NO _world / space_body
    # here — its contour bands are stroked rings at alpha 150 and width 14 px at
    # this radius, which on a near-black planet read as a painted BULLSEYE. The
    # first pass shipped exactly that: three concentric dark rings, a dartboard.
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, cx, cy, r, fill=(23, 26, 34), outline=(52, 60, 74),
                width=K.DETAIL, seed=902, wobble=3.0)
    # the lit sheen: one soft arc hugging the upper-left limb
    _crescent(d, cx, cy, r - 5, 186, 268, (86, 100, 116), 150, thick=34)
    # the shadowed crescent on the lower right, so the sphere turns
    _crescent(d, cx, cy, r - 4, 18, 96, (11, 13, 18), 190, thick=44)

    # THE HARD GLINT: a small blazing lozenge on the limb with a soft falloff
    # halo behind it. _soft_halo, not add_glow — a coloured add_glow on a
    # near-black sky reads as a brown ball, and the first pass of this card
    # shipped exactly that.
    gx, gy = cx - int(r * 0.70), cy - int(r * 0.70)
    img = _soft_halo(img, gx, gy, 132, AMBER, strength=96, falloff=2.8)
    d = ImageDraw.Draw(img, 'RGBA')
    _crescent(d, gx, gy, 24, 202, 338, WHITE_HOT, 255, thick=15)
    d.ellipse([gx - 8, gy - 8, gx + 8, gy + 8], fill=WHITE_HOT + (255,))

    # the dull pebble in his outstretched hand. The hand position is derived
    # from the SCHEDULE's stickman block (lib.stickman 'pointing' puts the
    # pointing hand at cx + 0.5*height, neck_y + 0.1*height), so the pebble
    # travels with him instead of being nailed to a coordinate.
    sm = card.get('stickman') or SELF_TEST_SMITHMAN['hook_inverted']
    head_r = int(sm['height'] / 8)
    hx = int(sm['x_center'] + int(sm['height'] * 0.5))
    hy = int(sm['y_top'] + 2 * head_r + int(sm['height'] * 0.1))
    K.draw_disc(d, hx + 6, hy + 8, 21, fill=(96, 98, 102), outline=INK,
                width=K.OUTLINE, seed=903, wobble=2.6)
    K.stipple(d, hx - 14, hy - 12, hx + 26, hy + 24, (66, 68, 72), seed=904,
              density=0.02, r=1, spread=1)

    d = ImageDraw.Draw(img)
    # 'NOT A COAL' moved DOWN off the title strip: at gy-66 it landed at y=93,
    # straddling the 84 px strip edge.
    _tiny(d, 'NOT A COAL', gx - 30, gy + 74, AMBER)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 2. name_card — NAME. CREAM, no character. Pure data.
# ---------------------------------------------------------------------------

def render_name_card(card, planet="LTT 9779 b"):
    """B2 — the naming beat, and a data card: a DIM M-dwarf low right with a wide,
    almost empty orbit ellipse drawn around it and the planet as a small silver
    bead near the far side of that ellipse. The whole point of the picture is
    how much nothing is out there: one small quiet star, one wide lonely path.

    No character (the script marks this a pure data beat). The M-dwarf is
    emissive, so this is one of the two cards where C._radial_core is legal."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # The system is centred at x=782 with rx=396 so the WHOLE orbit is on-frame.
    # At sx=1035 / rx=442 the ellipse ran off the right edge and read as a
    # cropped ring rather than as one complete lonely path.
    sx, sy, sr = 782, 446, 40
    # the wide, nearly empty orbit — a FLAT ink ellipse, no gradient
    K.draw_outline(d, _ellipse_pts(sx, sy, 396, 150), color=INK,
                   width=K.DETAIL, closed=True, seed=911, wobble=2.0,
                   wavelength=260.0)
    # the planet, a small silver bead riding the far side of the ellipse
    px, py = sx - 396, sy
    K.draw_disc(d, px, py, 17, fill=SILVER, outline=INK, width=K.OUTLINE,
                seed=912, wobble=1.8)
    # a soft steel wash on the bead's lower half, so it reads as a lit sphere
    d.arc([px - 17, py - 17, px + 17, py + 17], 0, 180, fill=STEEL, width=K.DETAIL)

    # the star: the only emissive body on a cream card in this segment
    C._radial_core(img, sx, sy, sr, [(255, 250, 238), AMBER, (168, 92, 26)])

    d = ImageDraw.Draw(img)
    # a callout ON the star (labels sit on their subject — that overlap is
    # authentic per the canon addendum)
    _label(d, 'M-DWARF', sx, sy + 96)
    _tiny(d, 'FAINT', sx, sy + 136, STEEL)
    # 'ONE WORLD' lifted clear of the orbit keyline it used to sit on
    _tiny(d, 'ONE WORLD', px, py - 62, INK)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 3. planet_is_loud — ESCALATE. VOID, no character. Pure data.
# ---------------------------------------------------------------------------

def render_planet_is_loud(card, planet="LTT 9779 b"):
    """B3 — the tight orbit. A dull orange star with the gleaming planet on a
    CLOSE, steeply-eccentric wobbling ellipse and a faint motion trail of three
    diminishing beads behind it, so the path reads as a path and not a drawn
    ring. Close in, and it never gets the chance to cool down.

    No character (pure data beat). The star is emissive — C._radial_core is
    legal here and is the segment's second and last gradient."""
    img = _void_card(seed=921, stars=112)
    # Centre the system at 600, not 905: at 905 the orbit's far edge reached
    # x = 1241 and the planet sat half off-frame with the whole left half of
    # the art empty. The camera in the reference is not a corner crop.
    sx, sy = 604, 336
    rx, ry = 428, 142

    d = ImageDraw.Draw(img, 'RGBA')
    # the orbit, flat bone, 2 px — a line, not a glow
    K.draw_outline(d, _ellipse_pts(sx, sy, rx, ry), color=BONE_ISH, width=K.FINE,
                   closed=True, seed=922, wobble=1.4, wavelength=240.0)
    # the perihelion end of the path, marked with a short amber tick
    _vline(d, sx + rx, sy - 30, sy + 30, AMBER, width=K.DETAIL, seed=923, wobble=0.8)
    # ...and the far, slow end, so the ellipse reads as an ellipse
    _vline(d, sx - rx, sy - 24, sy + 24, STEEL, width=K.FINE, seed=924, wobble=0.8)

    # the planet at the near, fast end of the ellipse
    ang = math.radians(34)
    px = int(round(sx + rx * math.cos(ang)))
    py = int(round(sy + ry * math.sin(ang)))

    # the motion trail: three beads at the same phase, further back along the
    # path, dimmer and smaller — quantised, not tweened (canon §5). Drawn UNDER
    # the planet at a real alpha; at the old value they were invisible on black.
    for k, (da, f) in enumerate(((10, 0.62), (19, 0.40), (28, 0.24))):
        a2 = math.radians(34 + da)
        tx = int(round(sx + rx * math.cos(a2)))
        ty = int(round(sy + ry * math.sin(a2)))
        rr = int(19 * f) + 4
        ImageDraw.Draw(img, 'RGBA').ellipse(
            [tx - rr, ty - rr, tx + rr, ty + rr],
            fill=SILVER + (int(215 * f),))

    img = _world(img, px, py, 27, base=(196, 210, 220), band=(150, 172, 186),
                 hi=(238, 248, 252), seed=925, bands=2)
    img = _soft_halo(img, px, py, 96, SILVER, strength=54, falloff=2.6)
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse([px - 32, py - 32, px + 32, py + 32], outline=AMBER + (210,),
              width=K.FINE)

    # the star: emissive, so C._radial_core is legal here — and the segment's
    # second and last gradient. A SOFT amber falloff behind it, not add_glow:
    # a coloured add_glow on near-black reads as a flat grey plate with a rim.
    img = _soft_halo(img, sx, sy, 128, AMBER, strength=54, falloff=2.6)
    C._radial_core(img, sx, sy, 42, [(255, 246, 224), AMBER, (150, 74, 18)])

    d = ImageDraw.Draw(img)
    _tiny(d, 'CLOSE IN', sx + 268, sy + 196, SILVER)
    _tiny(d, 'DIM STAR', sx, sy + 84, AMBER)
    _tiny(d, 'NEVER COOLS', sx - 300, sy - 172, STEEL)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 4. metal_sky — REVEAL. CREAM + character. The cutaway.
# ---------------------------------------------------------------------------

def render_metal_sky(card, planet="LTT 9779 b"):
    """B4 — the reveal, and the first big paint-register cutaway. A cross-section
    of the world: a 6 px ink keyline disc with a high-altitude metallic cloud
    deck drawn as five stacked SILVER bands across its upper third, a bright
    atmosphere arc riding the limb, and a DEEP STEEL interior below the deck.
    The character stands at lower left, hands up, wide oval mouth, looking up at
    it.

    Flat fills and thick outlines only — a planet is not an emissive body, so no
    gradient anywhere on this card (PALETTE_SPEC §3 denylist)."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    cx, cy, r = 856, 400, 262
    # A GROUND BAND. The canon addendum requires the character to be GROUNDED on
    # a wavy horizon in the paint register, and he stands at lower left here. The
    # first pass of this card had him standing on bare paper with nothing under
    # his feet, which is the single fastest way to look unfinished.
    _ground(d, 612, fill=SAND, seed=930)

    # a soft sand field behind the disc so it is not floating on bare paper
    K.draw_smooth(d, [(cx - 320, cy + 160), (cx - 50, cy - 226),
                      (cx + 310, cy - 130), (cx + 344, cy + 210),
                      (cx - 70, cy + 274)],
                  fill=(236, 226, 205), outline=None, seed=931, wobble=22.0,
                  wavelength=200.0)

    # the interior: flat deep steel, then the keyline disc on top of it
    K.draw_disc(d, cx, cy, r, fill=STEEL, outline=INK, width=K.OUTLINE,
                seed=932, wobble=4.0)
    # NO inner "core" disc. It read as a flat dark hole rather than depth, and it
    # collided with the label block at cy+26 / cy+184, printing WORLD on top of
    # it. The strata plus the atmosphere arc carry the cross-section on their own.

    # THE METAL CLOUD DECK: five stacked silver bands across the upper third,
    # each clipped to the disc's own half-width at that height, each with a thin
    # ink separator so they read as distinct strata.
    deck_ys = (-150, -114, -78, -42, -6)
    for k, dy in enumerate(deck_ys):
        hw = math.sqrt(max(0.0, r * r - dy * dy)) - 6
        y0, y1 = cy + dy - 15, cy + dy + 15
        d.rectangle([cx - hw, y0, cx + hw, y1],
                    fill=(SILVER if k % 2 == 0 else (168, 186, 196)))
        _hrule(d, y0, cx - hw, cx + hw, INK, width=K.FINE, seed=940 + k,
               wobble=0.8)
    _hrule(d, cy - 166, cx - 178, cx + 178, INK, width=K.DETAIL, seed=946,
           wobble=1.0)
    # the atmosphere: a bright arc riding the top limb, outside the keyline
    _draw_band(d, _arc_pts(cx, cy, r + 16, 208, 332, n=40), 13, SILVER, 255,
               seed=947, wobble=1.6, wavelength=170.0)

    # THE LABEL CALL-OUT, moved OFF the bands and OFF the removed core disc. At
    # cy-96 it sat square on the silver strata (ink-on-silver at LABEL_PX is a
    # contrast failure plus a stripe through the word); at cy+26 the stacked
    # METAL / CLOUD DECK pair ran into the core. It now hangs in the empty steel
    # low-left, with a leader up to the deck it names.
    lx, ly = cx - 96, cy + 132
    _label(d, 'METAL', lx, ly, INK)
    _tiny(d, 'CLOUD DECK', lx, ly + 34, INK)
    _open_curve(d, [(lx + 62, ly - 6), (lx + 104, ly - 52), (lx + 82, ly - 108)],
                INK, K.FINE, seed=948, wobble=1.2, wavelength=80.0)
    _arrow_head(d, (lx + 78, ly - 120), -104, INK, 22, 10, seed=949)
    # a "high altitude" leader up the left limb
    _open_curve(d, [(cx - r - 34, cy + 70), (cx - r - 52, cy - 30),
                    (cx - r - 40, cy - 128)], INK, K.DETAIL, seed=9495,
                wobble=2.2)
    _arrow_head(d, (cx - r - 40, cy - 148), -84, INK, 26, 12, seed=9496)
    _tiny(d, 'MILES UP', cx - r - 54, cy + 104, INK)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 5. irradiated_dayside — ESCALATE. VOID, no character. Pure data.
# ---------------------------------------------------------------------------

def render_irradiated_dayside(card, planet="LTT 9779 b"):
    """B5 — the irradiation, and the contradiction. A FLAT near-white dayside
    filling the left half of the sphere against a flat deep-steel night side,
    split by a hard vertical TERMINATOR, with six steep amber star rays striking
    it out of the upper left. It is being cooked from the outside and the
    surface still will not warm — that contradiction is the card.

    No character (pure data beat). Flat halves and a hard keyline terminator:
    the subject is a lit hemisphere, not a gradient, so the denylist holds. The
    only glow is a soft silver halo on the lit half, because the light landing
    on it is emitted light."""
    img = _void_card(seed=951, stars=104)
    cx, cy, r = 700, 408, 240

    d = ImageDraw.Draw(img, 'RGBA')
    # the night side first: flat deep steel
    K.draw_disc(d, cx, cy, r, fill=(40, 66, 78), outline=None, seed=952, wobble=3.0)

    # the dayside: a FLAT near-white half-disc, hard at the terminator
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 90, 270, fill=WHITE_HOT)
    # a low-contrast steel wash on the night half so it is not one dead value
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 270, 450,
               fill=(26, 46, 56, 190))
    # the soft halo on the lit half — emitted light landing and bouncing.
    # _soft_halo, not add_glow: the old call put a saturated grey PLATE with a
    # hard rim on the sky and the lit hemisphere sat inside a visible disc.
    img = _soft_halo(img, cx - int(r * 0.50), cy, int(r * 1.55), SILVER,
                     strength=64, falloff=2.7)
    d = ImageDraw.Draw(img)
    # the terminator: one hard ink line straight down the middle, DETAIL width
    _vline(d, cx, cy - r + 4, cy + r - 4, INK, width=K.DETAIL, seed=953, wobble=0.6)
    # the keyline round the whole body
    K.draw_disc(d, cx, cy, r, fill=None, outline=INK, width=K.OUTLINE,
                seed=954, wobble=3.0)

    # Six steep star rays striking the LIMB, drawn with _ray: a nearly-straight
    # THIN band softened by alpha. The first pass used a 15 px _draw_band with
    # wobble 2.4, which rendered as fat orange worms — the width was carrying the
    # softness instead of the alpha. The second pass aimed every ray at a common
    # x INSIDE the disc, so all six ended on one hard vertical line across the
    # white hemisphere. Each ray now ends on its own point of the left limb, so
    # the bundle LANDS on the sphere instead of stopping in it.
    limb_x = cx - r + 6
    for k in range(6):
        ly = cy - 168 + k * 66
        _ray(d, 40, ly - 250, limb_x, ly, AMBER, 196 - k * 22, 7, seed=960 + k)

    d = ImageDraw.Draw(img)
    # 'DAY SIDE' moved DOWN onto the empty lower-left of the lit hemisphere,
    # clear of the ray bundle; at cy-34 it sat across a ray.
    _label(d, 'DAY SIDE', cx - 96, cy + 122, INK)
    _label(d, 'NIGHT SIDE', cx + 132, cy - 30, SILVER)
    # the TERMINATOR leader is SHORTENED so it stops clear of its own word — at
    # 110 px long it ran the whole way underneath the label.
    _tiny(d, 'TERMINATOR', cx + 178, cy + 76, AMBER)
    _open_curve(d, [(cx + 30, cy + 52), (cx + 62, cy + 58), (cx + 104, cy + 64)],
                AMBER, K.FINE, seed=970, wobble=1.0)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 6. nothing_absorbed — MECHANISM. CREAM, no character. Pure data.
# ---------------------------------------------------------------------------

def render_nothing_absorbed(card, planet="LTT 9779 b"):
    """B6 — the mechanism, in one picture and no words: a flat grey disc with a
    FAT amber arrow striking its upper left and bouncing straight back out, and
    a HAIR-THIN steel arrow sinking a short way in and stopping. The width
    contrast IS the fact — nearly everything leaves, almost nothing stays.

    No character (pure data beat). Flat fills, thick 6 px outlines, one filled
    arrowhead per arrow. No gradient on the disc: the reflection is shown by
    where the arrows go, not by shading the sphere."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    cx, cy, r = 640, 404, 188
    # the world: a flat grey disc, 6 px keyline, one soft steel crescent on the
    # lit side so it is a sphere and not a hole
    K.draw_disc(d, cx, cy, r, fill=(178, 186, 192), outline=INK, width=K.OUTLINE,
                seed=981, wobble=3.0)
    d.arc([cx - r, cy - r, cx + r, cy + r], 150, 300, fill=STEEL, width=K.DETAIL)

    # THE FAT ARROW: in from the upper left, bounces ON THE LIMB, out to the
    # upper right. The first pass drew two independent shafts that both stopped
    # short of the sphere, so the pair read as ONE amber band passing THROUGH
    # the planet rather than as light coming off it. Both shafts now terminate
    # at the SAME limb vertex, computed from r so they cannot drift off it.
    vx = cx + r * math.cos(math.radians(215))
    vy = cy + r * math.sin(math.radians(215))
    _arrow(d, 148, 148, vx, vy, AMBER, 30, 58, 30, seed=982, wobble=1.8)
    _arrow(d, vx, vy, 1094, 132, AMBER, 30, 58, 30, seed=983, wobble=1.8)

    # THE HAIR-THIN ARROW: the same direction, sunk a short way into the surface
    # and stopped. It is 5x thinner than the other arrow on purpose.
    _arrow(d, 250, 636, 566, 468, STEEL, 6, 26, 13, seed=984, wobble=1.2)

    d = ImageDraw.Draw(img)
    # The labels sit in the two clear quadrants, each ~55 px off its own arrow's
    # shaft. They used to land on the arrowhead, and ALMOST NONE was at y=726 —
    # below H=720, i.e. rendered off the bottom of the frame entirely.
    _label(d, 'REFLECTED', 1016, 250, INK)
    _tiny(d, 'ALMOST ALL OF IT', 1016, 286, STEEL)
    _label(d, 'ABSORBED', 300, 520, INK)
    _tiny(d, 'ALMOST NONE', 300, 556, STEEL)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 7. coin_in_the_dark — PUNCHLINE. VOID + character.
# ---------------------------------------------------------------------------

def render_coin_in_the_dark(card, planet="LTT 9779 b"):
    """B7 — the punchline. A small silver planet alone at the centre of a wide
    dark field, throwing a hard glare straight down the barrel at the viewer, so
    it reads as a coin catching a torch rather than a lit planet. The character
    is at lower right, awed, both hands up.

    This is the one card where the SUBJECT is light itself, so the glare and its
    halo are legal here (PALETTE_SPEC §3). The planet body is a flat-ish
    painterly sphere and takes no gradient of its own."""
    img = _void_card(seed=991, stars=136)
    cx, cy, r = 560, 340, 88

    img = _glare(img, cx, cy, r, SILVER, a0=200, seed=992)
    # the planet sits ON the glare's centre, so the spikes read as coming off it.
    # A FLAT bright disc, no space_body: its contour bands printed a visible
    # bullseye across a mirror-finish coin, which is the opposite of the point.
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, cx, cy, r, fill=(206, 222, 232), outline=None, seed=993,
                wobble=2.0)
    _crescent(d, cx, cy, r - 5, 186, 300, WHITE_HOT, 190, thick=26)
    # a bright limb ring so the sphere's edge survives the glare behind it
    d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4],
              outline=WHITE_HOT + (225,), width=K.FINE)

    d = ImageDraw.Draw(img)
    # 'A COIN' restated the caption verbatim; name the thing's MATERIAL, which
    # the caption does not say and which is the point.
    _tiny(d, 'MIRROR', cx, cy - r - 52, AMBER)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 8. the_bad_number — BEAT. CREAM, no character. Pure data.
# ---------------------------------------------------------------------------

def render_the_bad_number(card, planet="LTT 9779 b"):
    """B8 — the number nobody believed. A hand-lettered readout panel with a
    dial whose needle is pegged hard past the last MAX stop, circled TWICE in red
    pen, with two red margin arrows and a scatter of red scribbles crowding it.

    A dial rather than a printed figure: the card's subject is a value too high
    to accept, and a needle overshooting the end of its own scale says that
    without printing a fact this module cannot source.

    The red pen is the ONE documented exception to "no red on a card" — there
    is no character on this card, so his shirt can collide with nothing, and the
    script's whole visual is a number circled in red."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # the readout panel: a smooth wobbled rounded rectangle spanning most of the
    # frame. The first pass ran it from x=582 to 1214, which left the whole left
    # third of the art empty — the card had a subject parked in one corner.
    K.draw_smooth(d, [(300, 176), (700, 166), (1096, 180), (1206, 300),
                      (1194, 520), (760, 596), (380, 586), (288, 400)],
                  fill=(250, 245, 232), outline=INK, width=K.OUTLINE,
                  seed=1001, wobble=3.0, wavelength=240.0)

    dcx, dcy, dr = 902, 442, 146
    # the dial face: an arc from the MAX stop round to the other MAX stop
    _open_curve(d, _arc_pts(dcx, dcy, dr, 180, 360, n=40), INK, K.DETAIL,
                seed=1002, wobble=1.0, wavelength=200.0)
    # ticks every 30 degrees, the last one amber
    for k in range(13):
        a = math.radians(180 + 180 * k / 12.0)
        inner = dr - (20 if k % 3 == 0 else 12)
        p0 = (dcx + inner * math.cos(a), dcy + inner * math.sin(a))
        p1 = (dcx + dr * math.cos(a), dcy + dr * math.sin(a))
        _open_curve(d, [p0, p1], (AMBER if k == 12 else INK),
                    K.DETAIL if k % 3 == 0 else K.FINE, seed=1010 + k, wobble=0.4)
    # 'MAX' moved DOWN-LEFT of the dial. It sat at (dcx+dr+34, dcy-6), which is
    # exactly where the red circles land around the needle tip — the ink word and
    # the red pen stroke through each other.
    _tiny(d, 'MAX', dcx - dr - 46, dcy - 18, INK)

    # the needle: pegged hard past the last stop, at 352 deg, running BEYOND the
    # dial arc so it visibly overshoots its own scale
    a = math.radians(352)
    nx, ny = dcx + (dr + 26) * math.cos(a), dcy + (dr + 26) * math.sin(a)
    _open_curve(d, [(dcx, dcy), ((dcx + nx) / 2, (dcy + ny) / 2), (nx, ny)],
                INK, K.OUTLINE, seed=1030, wobble=0.8)
    K.draw_disc(d, dcx, dcy, 14, fill=INK, outline=INK, width=K.DETAIL, seed=1031)

    # RED PEN: two concentric circles around the needle tip, two margin arrows
    # and four scribbles. The scribbles are DETAIL-width open wobbled curves, not
    # FINE hairs — at 2 px on cream they read as dead pixels, not as pen.
    for rr, w in ((36, K.DETAIL), (48, K.FINE)):
        pts = _ellipse_pts(nx, ny, rr, rr * 0.88, n=28)
        _open_curve(d, pts + [pts[0]], SHIRT, w, seed=1040 + rr, wobble=2.6,
                    wavelength=90.0)
    # both red arrows are pulled INSIDE the panel keyline: at x=1148/1150 the
    # lower one started below the panel's bottom edge and read as a stroke
    # crossing the frame rather than as a margin arrow.
    _arrow(d, 1104, 300, nx + 62, ny - 52, SHIRT, 7, 30, 15, seed=1043, wobble=1.4)
    _arrow(d, 1100, 528, nx + 66, ny + 46, SHIRT, 7, 30, 15, seed=1044, wobble=1.4)
    # the scribbles crowd the LABEL COLUMN as well, so the eye is dragged across
    # the whole panel instead of sitting on the dial alone
    for k, (sx, sy) in enumerate(((392, 292), (416, 500), (352, 392), (600, 546))):
        _open_curve(d, [(sx, sy), (sx + 26, sy - 12), (sx + 52, sy + 8),
                        (sx + 78, sy - 6)], SHIRT, K.DETAIL, seed=1050 + k,
                    wobble=3.0, wavelength=60.0)

    d = ImageDraw.Draw(img)
    # the label block now occupies the panel's left column, where it belongs
    _label(d, 'BRIGHTNESS', 560, 300, INK)
    _tiny(d, 'READOUT', 560, 342, STEEL)
    _tiny(d, 'TOO HIGH TO BE TRUE', 560, 390, SHIRT)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 9. checked_twice — BEAT. VOID, no character. Pure data.
# ---------------------------------------------------------------------------

def render_checked_twice(card, planet="LTT 9779 b"):
    """B9 — the second look. Two plotted brightness traces inside a bone panel:
    the first in dim STEEL, the second in bright BONE drawn straight over it,
    both landing on exactly the same peak. Two independent checks, one answer.

    No character (pure data beat). Flat lines on a flat panel — no gradient on
    the plot, on the panel or on the field. The peak marker is the only amber,
    and it is the point of the card."""
    img = _void_card(seed=1011, stars=98)
    d = ImageDraw.Draw(img)

    # The panel is recentred on x=880 (it ran 582..1214 and left the whole left
    # third of the frame empty). It is a wobbled bone keyline rectangle, NO
    # fill — the starfield reads through it, so the plot never sits on a
    # different colour from the sky.
    K.draw_outline(d, [(356, 176), (700, 166), (1010, 184), (1030, 366),
                       (1014, 566), (720, 584), (420, 570), (344, 372)],
                   color=BONE_ISH, width=K.DETAIL, closed=True, seed=1012,
                   wobble=2.6, wavelength=240.0)
    # axes
    _hrule(d, 500, 392, 990, BONE_ISH, width=K.DETAIL, seed=1013, wobble=1.0)
    _vline(d, 410, 250, 508, BONE_ISH, width=K.DETAIL, seed=1014, wobble=1.0)

    def _bell(cx, y0, base, half, sharp, n=17):
        pts = []
        for i in range(n):
            t = -1.0 + 2.0 * i / (n - 1)
            y = base - (base - y0) * math.exp(-(abs(t) ** sharp) * 3.0)
            pts.append((cx + half * t, y))
        return pts

    # BOTH traces peak at the SAME y. The first pass gave them peak_y 288 and 244,
    # so the two "independent checks" landed on visibly DIFFERENT peaks — which
    # is the exact opposite of what this card says. The traces now differ in
    # width (broad vs narrow) and confidence (dim vs bright) and nothing else.
    # peak_x 690 / half 190 keeps both traces INSIDE the recentred panel
    # (x 344..1030); at peak_x 880 with half 236 the bright trace ran off the
    # panel's right edge.
    peak_x, peak_y = 690, 268
    # trace 1 — dim, broad, low confidence
    _open_curve(d, _bell(peak_x, peak_y, 496, 190, 1.5), STEEL, K.DETAIL,
                seed=1015, wobble=1.4, wavelength=200.0)
    # trace 2 — bright, narrow, straight over the first, SAME apex
    _open_curve(d, _bell(peak_x, peak_y, 496, 176, 2.4), BONE_ISH, K.OUTLINE,
                seed=1016, wobble=0.9, wavelength=200.0)

    # the peak marker: a dashed amber drop to the axis and an amber tick on it
    for k in range(5):
        y = 290 + k * 42
        _vline(d, peak_x, y, y + 20, AMBER, width=K.FINE, seed=1020 + k, wobble=0.5)
    _hrule(d, 500, peak_x - 26, peak_x + 26, AMBER, width=K.DETAIL, seed=1030)
    _tiny(d, 'TWO CHECKS', peak_x, 232, AMBER)

    d = ImageDraw.Draw(img)
    # 'SAME PEAK' dropped BELOW the panel keyline (which bottoms at y=596) so
    # it stops printing over the panel's own border.
    C.hero_word(d, 'SAME PEAK', 690, 630, AMBER, stroke_width=3, px=48,
                y_max=624)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 10. should_be_an_oven — BEAT. CREAM + character. The oven scene.
# ---------------------------------------------------------------------------

def render_should_be_an_oven(card, planet="LTT 9779 b"):
    """B10 — the unsettling part, staged as a scene. A small illustrated oven
    stands at the left on a wobbled sand ground band, its door glowing flat amber
    with a soft halo, and the character stands beside it, flat-line deadpan, both
    palms up in a shrug: the hottest worlds should look like ovens, and this one
    does not.

    Register P throughout: flat fills, 6 px organic keylines, the character
    GROUNDED on a horizon (STYLE_CANON addendum). The only glow is the oven
    mouth, which is emitted heat."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    _ground(d, 588, fill=SAND, seed=1041)

    # the oven body: a smooth wobbled box, flat paper-grey, 6 px keyline
    ox0, ox1, oy0, oy1 = 188, 604, 246, 592
    K.draw_smooth(d, [(ox0, oy0), (ox0 + 208, oy0 - 6), (ox1, oy0 + 4),
                      (ox1, oy1 - 8), (ox0 + 210, oy1), (ox0, oy1 - 4)],
                  fill=(214, 214, 210), outline=INK, width=K.OUTLINE, seed=1042,
                  wobble=2.4, wavelength=220.0)
    # the hot top plate
    K.draw_smooth(d, [(ox0 + 16, oy0), (ox0 + 200, oy0 - 6), (ox1 - 12, oy0 + 4),
                      (ox1 - 26, oy0 - 30), (ox0 + 30, oy0 - 26)],
                  fill=(178, 178, 174), outline=INK, width=K.DETAIL, seed=1043,
                  wobble=2.0, wavelength=180.0)
    # the door: a flat amber mouth, and a soft halo because it is emitted heat.
    # _soft_halo, not add_glow: the coloured add_glow filled a saturated plateau
    # with a hard rim, so the oven appeared to sit inside an amber disc.
    img = _soft_halo(img, 396, 424, 208, AMBER, strength=62, falloff=2.8)
    d = ImageDraw.Draw(img)
    K.draw_smooth(d, [(258, 336), (396, 330), (534, 338), (538, 512),
                      (396, 520), (254, 510)],
                  fill=AMBER, outline=INK, width=K.OUTLINE, seed=1044,
                  wobble=2.0, wavelength=170.0)
    # the glass: three hot bands inside the mouth, flat, so it reads as heat
    for k, dy in enumerate((-52, 0, 52)):
        _hrule(d, 424 + dy, 274, 518, (196, 122, 40), width=K.DETAIL,
               seed=1050 + k, wobble=1.4)
    # the handle and the knobs
    _hrule(d, 300, 300, 492, INK, width=K.OUTLINE, seed=1060, wobble=1.0)
    for k in range(3):
        K.draw_disc(d, 288 + k * 108, 566, 15, fill=(150, 150, 148),
                    outline=INK, width=K.DETAIL, seed=1070 + k, wobble=1.4)
    # the feet
    for fx in (216, 576):
        _vline(d, fx, 590, 610, INK, width=K.OUTLINE, seed=1080 + fx, wobble=0.6)

    d = ImageDraw.Draw(img)
    # 'AN OVEN' moved DOWN into the empty right half. At (396, 216) it sat
    # square on the oven's hot top plate (also y ~= 216) — ink on grey, and the
    # word was half-buried in the object it names.
    _label(d, 'AN OVEN', 900, 388, INK)
    _tiny(d, 'WHAT IT SHOULD LOOK LIKE', 900, 428, STEEL)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 11. smile_at_mild_star — REVEAL. VOID, no character. Pure data.
# ---------------------------------------------------------------------------

def render_smile_at_mild_star(card, planet="LTT 9779 b"):
    """B11 — the second reveal, told with a shape instead of a sentence. A dark
    world on navy whose ONLY bright feature is a tapering luminous crescent
    hugging its top limb, curving like a grin, with a tiny pale M-dwarf far off to
    the side to say how little star there is out there.

    No character (pure data beat). The crescent is the subject and it is emitted
    light, so the taper and its halo are legal (PALETTE_SPEC §3); the planet body
    itself is a flat painterly sphere with no gradient of its own."""
    img = _void_card(seed=1091, stars=142)
    cx, cy, r = 604, 408, 232

    # THE BODY: a dark world drawn FLAT, so the crescent is genuinely the only
    # bright feature. NO space_body — its contour bands are alpha-150 stroked
    # rings and on a dark sphere they read as a painted BULLSEYE (the first pass
    # shipped a four-ring dartboard with a grin lying across it). The only
    # modelling is one dim sheen arc on the upper-left and one shadow crescent
    # low-right.
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, cx, cy, r, fill=(27, 34, 44), outline=None, seed=1092,
                wobble=3.0)
    _crescent(d, cx, cy, r - 8, 186, 262, (58, 70, 84), 130, thick=40)
    _crescent(d, cx, cy, r - 4, 22, 104, (13, 17, 24), 200, thick=52)

    # THE GRIN: a tapering luminous crescent along the top limb. 196..344 deg is
    # the top of the sphere in PIL's screen-space angles. _soft_halo behind it,
    # not add_glow — the old call put a visible grey PLATE over the whole sky.
    img = _soft_halo(img, cx, cy - int(r * 0.72), int(r * 1.15), SILVER,
                     strength=60, falloff=2.8)
    d = ImageDraw.Draw(img, 'RGBA')
    _crescent(d, cx, cy, r - 2, 196, 344, WHITE_HOT, 255, thick=30)
    d = ImageDraw.Draw(img)
    # a faint keyline so the dark limb still reads as a sphere against the field
    K.draw_disc(d, cx, cy, r, fill=None, outline=(64, 78, 90), width=K.DETAIL,
                seed=1093, wobble=3.0)

    # the tiny pale star, far off to the side
    sx, sy = 1120, 200
    K.draw_disc(d, sx, sy, 13, fill=(246, 248, 250), outline=INK,
                width=K.DETAIL, seed=1094, wobble=1.2)
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse([sx - 22, sy - 22, sx + 22, sy + 22], outline=SILVER + (140,),
              width=K.FINE)
    d = ImageDraw.Draw(img)
    _tiny(d, 'MILD STAR', sx - 34, sy - 54, AMBER)
    _tiny(d, 'A GRIN', cx, cy + r + 44, SILVER)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 12. brilliant_and_bare — BEAT. CREAM, no character. Pure data.
# ---------------------------------------------------------------------------

def render_brilliant_and_bare(card, planet="LTT 9779 b"):
    """B12 — the scale strip, and it is deliberately unglamorous: a blazing
    SILVER world sitting on a hand-drawn baseline beside a small familiar STEEL
    Earth, with a dimension bar between them carrying the only number on the
    card. Big and bright, and still just under twice the size of home — and
    there is nothing to stand on and nothing to breathe.

    No character (pure data beat). Flat discs, thick 6 px keylines, one soft
    silver halo on the blazing one because the shine IS the subject."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # base_y lifted from 556 to 516 so the dimension bar and its label clear the
    # floating caption at y=652 by a real margin instead of by four pixels.
    base_y = 516
    big_r, small_r = 142, 94
    bx, sx = 398, 846

    # the baseline everything stands on
    _hrule(d, base_y, 150, 1150, INK, width=K.OUTLINE, seed=1101, wobble=1.6)

    # the small familiar world: flat steel, flat green-free, 6 px keyline
    K.draw_disc(d, sx, base_y - small_r, small_r, fill=STEEL, outline=INK,
                width=K.OUTLINE, seed=1102, wobble=2.4)
    d.arc([sx - small_r, base_y - 2 * small_r, sx + small_r, base_y],
          190, 350, fill=(44, 78, 92), width=K.DETAIL)

    # THE BLAZING WORLD: flat BONE, 6 px keyline, and a strong soft halo. The
    # first pass filled it WHITE_HOT (only ~4% off the cream card — it read as a
    # hole) and shaded it with a pieslice wedge whose straight edges read as a
    # pie chart. It is now a bright bone disc with a WIDE silver halo, a bright
    # upper-left rim arc, and NO wedge — the shine and the value carry it.
    # _soft_halo, not add_glow: add_glow shipped a huge pale DISC.
    img = _soft_halo(img, bx, base_y - big_r, 420, SILVER, strength=96,
                     falloff=2.2)
    img = _soft_halo(img, bx, base_y - big_r, 260, WHITE_HOT, strength=90,
                     falloff=2.4)
    d = ImageDraw.Draw(img)
    K.draw_disc(d, bx, base_y - big_r, big_r, fill=BONE_ISH, outline=INK,
                width=K.OUTLINE, seed=1103, wobble=3.0)
    # the bright rim on the lit side, so the sphere reads as shining
    d.arc([bx - big_r - 4, base_y - 2 * big_r - 4, bx + big_r + 4, base_y + 4],
          178, 300, fill=WHITE_HOT, width=K.OUTLINE)

    # the dimension bar: end caps up from the baseline, arrowheads inward
    for x in (bx, sx):
        _vline(d, x, base_y + 6, 578, INK, width=K.DETAIL, seed=1110 + x, wobble=0.8)
    _hrule(d, 574, bx, sx, AMBER, width=K.OUTLINE, seed=1112, wobble=1.0)
    _arrow_head(d, (bx - 6, 574), 180, AMBER, 28, 15, seed=1113)
    _arrow_head(d, (sx + 6, 574), 0, AMBER, 28, 15, seed=1114)

    d = ImageDraw.Draw(img)
    _label(d, 'THIS WORLD', bx, base_y - 2 * big_r - 52, INK)
    _label(d, 'EARTH', sx, base_y - 2 * small_r - 48, INK)
    # '1.5x WIDER' sat ON the dimension bar's amber rule — the word and its own
    # underline were one mark. It now rides just under the rule.
    _tiny(d, '1.5x WIDER', (bx + sx) // 2, 610, INK)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 13. no_survival — DREAD. VOID + character.
# ---------------------------------------------------------------------------

def render_no_survival(card, planet="LTT 9779 b"):
    """B13 — the dread beat, and the biggest object in the segment: the blazing
    world bleeds off the entire left of frame, flat near-white with a silver rim
    and a soft halo, with heat-shimmer lines rising off its right limb. The
    character is at the right, recoiling, both hands up, downturned arc mouth.
    He is CLOSE to it. That is the point.

    The halo and the shimmer are emitted light, so they are legal here
    (PALETTE_SPEC §3); the body itself is flat fill plus a 6 px keyline, never a
    gradient."""
    img = _void_card(seed=1121, stars=104)
    cx, cy, r = 322, 396, 300

    img = _soft_halo(img, cx, cy, int(r * 1.85), SILVER, strength=56, falloff=2.9)
    d = ImageDraw.Draw(img)
    K.draw_disc(d, cx, cy, r, fill=WHITE_HOT, outline=INK, width=K.OUTLINE,
                seed=1122, wobble=4.0)
    # a silver rim so the sphere's edge survives against the field
    d.arc([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5], 288, 72,
          fill=SILVER, width=K.OUTLINE)

    # HEAT SHIMMER: five SEPARATED rising curves off the right limb.
    # The first pass used a single _draw_band per line whose four control points
    # alternated left-right-left-right as they climbed; run through Catmull-Rom
    # and mirrored against the neighbouring lines, that interlaced into a
    # DNA double helix. The fix is not a thinner stroke — it is to stop the
    # path from crossing itself and to give each line its OWN column.
    for k in range(5):
        x0 = cx + r - 44 + k * 30
        y0 = 268 + k * 22
        _draw_band(d, [(x0, y0), (x0 + 16, y0 - 52),
                       (x0 - 6, y0 - 104), (x0 + 12, y0 - 152)],
                   7, SILVER, 138 - k * 20, seed=1130 + k, wobble=1.4,
                   wavelength=150.0)

    d = ImageDraw.Draw(img)
    # 'NO SURFACE' was AMBER on the blazing white limb at (cx+84, 620) — that
    # point is barely off the disc, and amber-on-near-white measures ~1.8:1.
    # A hard fail. It moves out onto the dark field below the limb, in AMBER
    # with the ink keyline, where it clears both the body and the character.
    C.hero_word(d, 'NO SURFACE', 744, 590, AMBER, stroke_rgb=INK,
                stroke_width=3, px=48, y_max=624)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 14. borrowed_light — CLOSER. CREAM + character. The closing beat.
# ---------------------------------------------------------------------------

def render_borrowed_light(card, planet="LTT 9779 b"):
    """B14 — the close. A cream card with the world small and gleaming at
    centre-left, a long amber arrow arriving from off-frame right to feed it —
    the light is coming from somewhere else, and it is not the world's own — and
    the character crouched at lower right on the ground, zigzag mouth, arms
    wrapped in, uncomfortable. The gleam is borrowed.

    Register P: flat fills, 6 px organic keylines, the character GROUNDED on a
    wobbled horizon (STYLE_CANON addendum). One soft silver halo, because the
    shine is the subject."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    _ground(d, 606, fill=SAND, seed=1141)
    # NO sky wash here. Two attempts failed: crisp, it read as a pale bubble
    # stuck on the card; blurred, its wobbled edge smeared into a grey
    # thumbprint ring that dirtied the paper. Bare cream is the correct answer
    # — a 6 px keyline already separates the world from the field.

    px, py, pr = 408, 356, 112
    # a LOW, WIDE falloff. strength=56 at falloff 2.8 still clamped to a plateau
    # and printed a visible grey disc around the world; the halo has to sit well
    # under the paper's own value or it is a smudge, not a shine.
    img = _soft_halo(img, px, py, 300, SILVER, strength=34, falloff=2.0)
    d = ImageDraw.Draw(img)
    K.draw_disc(d, px, py, pr, fill=SILVER, outline=INK, width=K.OUTLINE,
                seed=1143, wobble=3.0)
    # the lit limb and the shadowed limb, as FLAT arcs — no gradient on a body
    d.arc([px - pr, py - pr, px + pr, py + pr], 200, 340, fill=WHITE_HOT,
          width=K.DETAIL)
    d.arc([px - pr, py - pr, px + pr, py + pr], 20, 160, fill=STEEL, width=K.DETAIL)

    # THE INCOMING ARROW: from off-frame right, feeding the world. It enters the
    # frame at the right edge so its source is visibly somewhere else. It is
    # raised to y=214 so it passes ABOVE the character (y_top 286) instead of
    # grazing his skull, and it stops short of the keyline.
    # The arrow is raised to run at y ~= 205 across his column, which is ABOVE
    # his head top at y=226 — at y=232 it crossed his skull.
    _arrow(d, 1300, 186, px + pr + 34, py - 110, AMBER, 22, 48, 26, seed=1144,
           wobble=1.6)
    _label(d, 'INCOMING', 1150, 148, INK)
    _tiny(d, 'BORROWED', px, py + pr + 50, INK)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

RENDERERS = {
    'hook_inverted': render_hook_inverted,
    'name_card': render_name_card,
    'planet_is_loud': render_planet_is_loud,
    'metal_sky': render_metal_sky,
    'irradiated_dayside': render_irradiated_dayside,
    'nothing_absorbed': render_nothing_absorbed,
    'coin_in_the_dark': render_coin_in_the_dark,
    'the_bad_number': render_the_bad_number,
    'checked_twice': render_checked_twice,
    'should_be_an_oven': render_should_be_an_oven,
    'smile_at_mild_star': render_smile_at_mild_star,
    'brilliant_and_bare': render_brilliant_and_bare,
    'no_survival': render_no_survival,
    'borrowed_light': render_borrowed_light,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table. No import
    side effects: the frame generator calls this, or reads RENDERERS directly."""
    C.register(mapping if mapping is not None else RENDERERS)
    return RENDERERS


# ---------------------------------------------------------------------------
# Self-test — renders every beat to cardsheet/beat_NN.png and verifies the two
# hard contract properties: one 1280x720 RGB frame out, and no card mutating the
# dict it was handed. Run:  python ltt9779b/_cards.py
# ---------------------------------------------------------------------------

# A short generic caption per beat. Not the narration — the narration is audio
# only and is never printed (hard rule in the brief). Each is <60 chars, <=12
# words, one line, and none of them restates a hero word on the same card.
SELF_TEST_CAPTIONS = {
    'hook_inverted': 'SOME WORDS GIVE THE LIGHT BACK',
    'name_card': 'A QUIET STAR, A LONG PATH',
    'planet_is_loud': 'IT SITS CLOSE IN',
    'metal_sky': 'THE SKY ITSELF IS METAL',
    'irradiated_dayside': 'STRUCK ALL DAY, NEVER COOKING',
    'nothing_absorbed': 'ONE ARROW OUT, ONE IN',
    'coin_in_the_dark': 'A COIN IN THE DARK',
    'the_bad_number': 'THE NUMBER NOBODY BELIEVED',
    'checked_twice': 'TWO CHECKS, ONE ANSWER',
    'should_be_an_oven': 'THE HOTTEST WORLDS SHOULD OVEN',
    'smile_at_mild_star': 'A GRIN ON THE DARK SIDE',
    'brilliant_and_bare': 'BIGGER THAN HOME, STILL BARELY',
    'no_survival': 'NOT A SINGLE BREATH',
    'borrowed_light': 'THE LIGHT IS NOT ITS OWN',
}

# beat n -> card id, from script.json. The self-test walks this in narration
# order so the cardsheet is a contact sheet of the segment, not a dict dump.
BEAT_ORDER = [
    (1, 'hook_inverted'),
    (2, 'name_card'),
    (3, 'planet_is_loud'),
    (4, 'metal_sky'),
    (5, 'irradiated_dayside'),
    (6, 'nothing_absorbed'),
    (7, 'coin_in_the_dark'),
    (8, 'the_bad_number'),
    (9, 'checked_twice'),
    (10, 'should_be_an_oven'),
    (11, 'smile_at_mild_star'),
    (12, 'brilliant_and_bare'),
    (13, 'no_survival'),
    (14, 'borrowed_light'),
]


def _self_test():
    import copy
    import json

    here = _HERE
    out_dir = os.path.join(here, 'cardsheet')
    os.makedirs(out_dir, exist_ok=True)

    # the script is the source of truth for which beats must exist
    script_path = os.path.join(here, 'script.json')
    script_ids = []
    if os.path.exists(script_path):
        with open(script_path, 'r', encoding='utf-8') as fh:
            script_ids = [b['id'] for b in json.load(fh)['beats']]

    missing = [cid for cid in script_ids if cid not in RENDERERS]
    if missing:
        raise SystemExit('RENDERERS is missing beats: %s' % ', '.join(missing))
    extra = [cid for cid in RENDERERS if cid not in script_ids]
    if extra:
        raise SystemExit('RENDERERS claims beats not in script.json: %s'
                         % ', '.join(extra))

    for n, cid in BEAT_ORDER:
        card = {
            'id': cid,
            'caption': SELF_TEST_CAPTIONS[cid],
            'stickman': (dict(SELF_TEST_SMITHMAN[cid])
                         if cid in SELF_TEST_SMITHMAN else None),
        }
        before = copy.deepcopy(card)
        img = RENDERERS[cid](card, 'LTT 9779 b')
        if not isinstance(img, Image.Image):
            raise SystemExit('%s did not return an Image' % cid)
        if img.size != (W, H):
            raise SystemExit('%s returned %s, expected %s'
                             % (cid, img.size, (W, H)))
        if img.mode != 'RGB':
            raise SystemExit('%s returned mode %s, expected RGB' % (cid, img.mode))
        if card != before:
            raise SystemExit('%s mutated its card dict' % cid)
        path = os.path.join(out_dir, 'beat_%02d.png' % n)
        img.save(path)
        print('beat %02d  %-20s %dx%d  %s' % (n, cid, img.size[0], img.size[1],
                                              os.path.basename(path)))

    with_char = [cid for cid in RENDERERS if cid in SELF_TEST_SMITHMAN]
    print('%d beats rendered, %d with the character: %s'
          % (len(BEAT_ORDER), len(with_char), ', '.join(sorted(with_char))))
    return 0


if __name__ == '__main__':
    sys.exit(_self_test())
