# work/segments/wasp127b/_cards.py — ALL 14 beats of segment 6 (WASP-127b).
#
# WASP-127b: a puffy, near-empty gas giant on a violent ultra-short orbit. The
# fastest winds ever measured on an exoplanet, an atmosphere that leaves upward
# and never comes back, and a sky with a leak that has no bottom. Tone target:
# hot star, screaming wind, nothing holding together.
#
# CONTRACT (this module is the whole beat set; the frame generator does
# `C.register(_cards.RENDERERS)` then `C.render(card, "WASP-127b")` per card):
#   * Layout A per work/STYLE_CANON.md §1 — rows 0..83 paper title strip
#     (C._header), full-bleed art rows 84..719, NO caption band. The caption
#     floats on the art at the fixed call C._caption(..., 70, 652).
#   * Every renderer has the signature fn(card, planet) -> 1280x720 RGB Image,
#     dispatches on card['id'], never mutates card.
#   * Character ONLY via C._draw_stickman(img, card, theme), which reads the
#     schedule's own x_center / y_top / height / pose / expression. Nothing
#     about the figure is hardcoded here. theme='dark' (cream on space) on
#     every void card, 'light' (dark ink on cream) on every cream card.
#   * Narration is NEVER printed. card['caption'] is the only text that comes
#     from the script, and the art never restates it — the hero words here add
#     a fact the caption does not say.
#   * Type: work/lib/type.py only (comicbd.ttf bold / comic.ttf regular) via
#     T.load_font / T.draw_stamp, and C.hero_word for every dominant phrase.
#     Never a hardcoded font file, never a font size off the locked set.
#   * Strokes: K.OUTLINE 6px on large shapes, K.DETAIL 4 on diagram detail,
#     K.FINE 2 on specks, K.HAIRLINE 1 on keylines. Lines are smooth hand
#     curves with LOW-frequency wobble (K.wobble_points), never per-vertex
#     jitter on straight polylines.
#   * No gradients anywhere except the emissive stellar core on read_the_star
#     (C._radial_core), which is a sun. Planets are matte: flat bands plus a
#     keyline. No gradient on any diagram, ring, ribbon, caption or the figure.
#   * Determinism: every wobble / stipple / starfield / spiral call takes an
#     explicit integer seed. No global random state, so re-renders are
#     byte-identical.
#
# The palette below is THIS SEGMENT'S locked set (see PALETTE_SPEC.md beside
# this file). cardframe.PAL is segment 3's palette and is deliberately not used
# for card colour here; only its generic helpers (void_backdrop, space_body,
# _radial_core, add_glow, hero_word, _header, _caption, _draw_stickman) are.

import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# `lib.*` must import absolutely. The frame generator puts work/ on sys.path
# before it imports this module, but the self-test has to run standalone from
# the segments directory, so do it here idempotently.
_WORK = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))          # .../work
if _WORK not in sys.path:
    sys.path.insert(0, _WORK)

import lib.type as T
import lib.ink as K
import lib.cardframe as C

# G-fix shared libs. emissive = the G3 luminous-body helpers, labels = the G4/G5
# contrast + placement helpers, composition = the G1 occupancy geometry,
# stickman = the G7 anchored figure with elbowed arms and hand blobs.
import lib.emissive as E
import lib.labels as Lb
import lib.composition as P
import lib.stickman as S

W, H = C.W, C.H

# G1 numeric composition targets, taken from work/lib/composition.py (which
# ADOPTS the same thresholds as work/segments/_gate.py rather than re-deriving
# them, so there is one set of numbers in the project).
GROUND_Y = P.GROUND_Y          # 619 — feet line, bottom quarter
SUBJECT_V_MIN = P.SUBJECT_V_MIN  # 0.42 — subject centre must sit at/below this


# ---------------------------------------------------------------------------
# THE LOCKED PALETTE (work/segments/wasp127b/PALETTE_SPEC.md §1)
# ---------------------------------------------------------------------------
# 6 card colours: 1 ink, 1 paper, 1 deep, 3 accents. Plus the character's shirt
# red, which is a stickman.py global identical across all 12 segments and is
# therefore the ONLY red permitted on screen — no card accent in this segment
# is red (PALETTE_SPEC §1).

MY_PAL = {
    'ink':    (20, 22, 28),      # #14161C slate-black — all linework, all type on cream
    'paper':  (242, 234, 214),   # #F2EAD6 bone-cream — title strip, every cream card
    'deep':   (5, 6, 11),        # #05060B void — the space field, every dark card
    'amber':  (232, 163, 61),    # #E8A33D signal amber — the star, hot accents, captions on deep
    'bone':   (220, 230, 236),   # #DCE6EC x-ray bone — wind ribbons, diagram linework
    'teal':   (46, 127, 134),    # #2E7F86 storm teal — the wind, the escaping air
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
AMBER = MY_PAL['amber']
BONE = MY_PAL['bone']
TEAL = MY_PAL['teal']

# The canonical olive GROUND BAND. STYLE_CANON.md's 2026-09-30 addendum asks for
# a wavy olive/dark-green ground plane under any card where the character is the
# subject rather than a scale figure — beats 6 and 12 are exactly that. It is a
# stage colour, not a card accent, so it sits outside the accent cycle.
OLIVE = (96, 112, 70)           # #6B7046 mid olive — a painted ground band, not a
                                # dark stripe. Against the bone-cream sky it has
                                # to read as a surface, so it sits mid-value.

# The spectrum bar is the one subject in the segment that is SUPPOSED to be a
# ramp, so it carries seven flat DISCRETE swatches (never a gradient). They are
# derived from the locked set so the card still reads as this segment's art:
# amber -> bone -> teal -> deep. Diagram-only; never a card background, never
# type. A "bitten" or crossed-out slice is knocked down toward slate-black
# rather than drawn in red, because red is reserved for the character
# (PALETTE_SPEC §1 / hard rule 10).
SPECTRUM = [
    (238, 176, 74),
    (246, 208, 128),
    (220, 230, 236),
    (150, 200, 200),
    (46, 127, 134),
    (40, 78, 100),
    (28, 44, 62),
]

# Accent cycle, strict 4-cycle over {bone, amber, teal} plus the two card-value
# registers. Documented per-card in PALETTE_SPEC.md §2; no two adjacent cards
# share an accent.
ACCENT_CYCLE = ('bone', 'amber', 'teal')


# ---------------------------------------------------------------------------
# Local helpers. All of them sit on lib/ink.py primitives; none re-derive a lib
# constant and none call a broken lib path.
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output).

    Local rather than K._smooth_open so this module never depends on the state
    of that function (the psrb1257 beat modules were written against a broken
    version and carry their own copy for exactly this reason).
    """
    p = list(pts)
    if len(p) < 3:
        return list(p)
    ext = [p[0], p[0]] + p + [p[-1], p[-1]]
    out = []
    for i in range(len(p)):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(samples):
            t = s / float(samples)
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p1[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(p[-1])
    return out


def _open_curve(draw, points, color, width=K.DETAIL, seed=0, wobble=1.2,
                wavelength=90.0):
    """An OPEN hand-wobbled smooth curve at hairline/medium weight."""
    pts = K.wobble_points(points, seed=seed, amount=wobble,
                          wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    draw.line(dense, fill=color, width=width, joint='curve')
    return dense


def _vline(draw, x, y0, y1, color, width=K.DETAIL, seed=0, wobble=1.0):
    """A short hand-wobbled vertical rule."""
    return _open_curve(draw, [(x, y0), (x, (y0 + y1) / 2.0), (x, y1)], color,
                       width, seed=seed, wobble=wobble, wavelength=60.0)


def _hrule(draw, y, x0, x1, color, width=K.DETAIL, seed=0, wobble=1.2):
    """A short hand-wobbled horizontal rule."""
    return _open_curve(draw, [(x0, y), ((x0 + x1) / 2.0, y), (x1, y)], color,
                       width, seed=seed, wobble=wobble, wavelength=90.0)


def _thick_curve(draw, points, fill, seed=0, width=20, wobble=2.0,
                 wavelength=150.0):
    """An OPEN hand-wobbled curve stroked to a real width.

    WHY draw.line(joint='curve') AND NOT A POLYGON RAIL. The obvious build is to
    offset the dense centreline by +/- half-width along its normal and weld the
    two rails into one closed polygon (psrb1257/_cards_b4.py does this). That
    works only where the path is gently curved. Where the curvature radius drops
    below half-width — which is most of this segment, because the wind ribbons
    and the spiral arms ARE tight curves — the outer rail folds over itself,
    the rail polygon self-intersects, and PIL's fill punches scalloped holes
    along the inside of every bend. Beat 1's spiral arms came out looking like
    torn paper.

    draw.line with joint='curve' draws a proper thick path (segment bodies plus
    round joints) and is continuous through exactly that case. The b4 comment
    warns that a WIDE PIL line grows hairy nubs at near-duplicate vertices; that
    was measured at width 24-36. Every stroke here is 5-12 px, where the joint
    ellipses sit on the path and are invisible. Verified both ways side by side.
    """
    pts = K.wobble_points(points, seed=seed, amount=wobble,
                          wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    draw.line(dense, fill=fill, width=max(1, int(round(width))), joint='curve')
    return dense


def _soft_wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=170.0,
               blur=20):
    """A painterly FLAT-colour region with soft edges. Never a gradient.

    Every stage field in this segment (the wind wash on beat 1, the teal stage
    under the spectrum on 8/9, the escape column on 10) is a wobbled flat fill
    drawn on its own RGBA layer and blurred, so nothing ever leaves a crisp
    rectangle or a square corner on the frame. Returns a new RGB image.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=rgb + (int(alpha),), outline=None,
                  width=0, seed=seed, wobble=wobble, wavelength=wavelength,
                  closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _keyline(draw, cx, cy, r, color=INK, width=K.OUTLINE, seed=0):
    """The organic wobbly circle outline. K.draw_disc is a wobbled 8-gon run
    through a spline, so the edge is an organic circle, not a perfect one."""
    return K.draw_disc(draw, cx, cy, r, fill=None, outline=color, width=width,
                       seed=seed, wobble=3.0)


def _flat_star(draw, cx, cy, r, color, seed, rays=9, ray_len=0.55,
               ray_w=0.16, keyline=INK):
    """A painted sun: a FLAT disc with flat ray spokes and a 6px keyline.

    Register P on a cream card. The star is emissive so a gradient is legal, but
    on a cream field an airbrushed ramp plus a warm halo reads as mud, and
    texture.sun_disc's opaque warm halo is worse. Flat paint + spokes is what
    the reference draws when a sun shares a frame with the character.
    """
    _keyline(draw, cx, cy, r, color=keyline, width=K.OUTLINE, seed=seed)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    for i in range(rays):
        a = math.tau * i / rays
        ca, sa = math.cos(a), math.sin(a)
        inner, outer = r * 1.12, r * (1.12 + ray_len * (0.72 + 0.28 *
                                                       ((i * 7) % 5) / 4.0))
        pts = [
            (cx + inner * ca - sa * r * ray_w, cy + inner * sa + ca * r * ray_w),
            (cx + outer * ca, cy + outer * sa),
            (cx + inner * ca + sa * r * ray_w, cy + inner * sa - ca * r * ray_w),
        ]
        _thick_curve(draw, pts, color, seed=seed + 11 + i, width=r * 0.15,
                     wobble=1.6, wavelength=70.0)


def _banded_giant(img, cx, cy, r, colors, seed, outline_rgb=INK,
                  width=K.OUTLINE, n_bands=None):
    """A matte gas giant: flat horizontal bands, hand-wobbled, plus a 6px
    organic keyline. Register P.

    The bands are painted flat on an RGBA layer and clipped to the disc by a
    mask rather than by arithmetic, so the wobble of each band edge survives
    while the silhouette stays a clean circle. NO gradient: a planet is not an
    emissive body (STYLE_CANON §0 / PALETTE_SPEC §3 denylist).
    """
    n = n_bands if n_bands is not None else len(colors)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colors[0] + (255,))
    bh = (2.0 * r) / n
    for i in range(1, n):
        y = cy - r + i * bh
        amp = bh * 0.20
        pts = []
        k = 0
        x = cx - r - 2
        while x <= cx + r + 2:
            pts.append((x, y + amp * math.sin(k * 0.9 + i * 1.7)))
            x += r * 0.16
            k += 1
        band_pts = ([(cx - r - 2, cy - r - 2), (cx + r + 2, cy - r - 2)]
                    + pts + [(cx + r + 2, cy + r + 2), (cx - r - 2, cy + r + 2)])
        K.draw_smooth(ld, band_pts, fill=colors[i % len(colors)] + (255,),
                      outline=None, width=0, seed=seed + 20 + i, wobble=1.8,
                      wavelength=r * 1.1, closed=True)
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    lay.putalpha(ImageChops.multiply(lay.split()[-1], mask))
    img = Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')
    d = ImageDraw.Draw(img)
    _keyline(d, cx, cy, r, color=outline_rgb, width=width, seed=seed + 40)
    return img


def _arrow(draw, x0, y0, x1, y1, color, width=K.OUTLINE, seed=0, head=26):
    """A hand-wobbled arrow: a filled shaft that stops short of the tip, plus
    two gently-bowed barbs forming an open V head.

    The first version drew each barb as tip -> outer -> back-along-the-axis, so
    both barbs looped into the shaft and the head rendered as a bird-foot
    scribble (worst on beat 10's long steep diagonal). An open V of two straight
    -ish barbs off the tip reads as a clean arrowhead at every size; the shaft
    now ends head*0.9 back so the V alone defines the point.
    """
    ang = math.atan2(y1 - y0, x1 - x0)
    # shaft, stopping head*0.9 short of the tip
    sx = x1 - head * 0.9 * math.cos(ang)
    sy = y1 - head * 0.9 * math.sin(ang)
    _thick_curve(draw, [(x0, y0), ((x0 + sx) / 2.0, (y0 + sy) / 2.0), (sx, sy)],
                 color, seed=seed, width=width, wobble=1.6, wavelength=120.0)
    # open-V head: two barbs off the tip, each with a small perpendicular bow
    for sgn, sd in ((1, seed + 7), (-1, seed + 8)):
        a2 = ang + sgn * math.radians(140)
        ox = x1 + head * math.cos(a2)
        oy = y1 + head * math.sin(a2)
        mx = (x1 + ox) / 2.0 - math.sin(a2) * 2.0
        my = (y1 + oy) / 2.0 + math.cos(a2) * 2.0
        _thick_curve(draw, [(x1, y1), (mx, my), (ox, oy)],
                     color, seed=sd, width=width * 0.85, wobble=0.8,
                     wavelength=40.0)


def _spiral_pts(cx, cy, r0, r1, a0_deg, a1_deg, n=40, drift=0.0):
    """Sample an arm of a spiral. `drift` bows the radius so the arm is not a
    plain logarithmic curve — this segment's wind is drawn, not plotted."""
    pts = []
    for i in range(n + 1):
        u = i / float(n)
        a = math.radians(a0_deg + (a1_deg - a0_deg) * u)
        rr = r0 + (r1 - r0) * u
        rr *= 1.0 + drift * math.sin(math.pi * u)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _spectrum_bar(draw, x, y, w, h, seed, bites=(), crosses=(), flat=None):
    """The spectrum bar: `len(SPECTRUM)` FLAT swatches side by side.

    `bites` are slice indices knocked down toward slate-black — a colour the
    atmosphere swallowed on the way in. `crosses` are slice indices marked with
    an ink X. Both are deletions, so both are drawn in ink, never in red.
    """
    n = len(SPECTRUM)
    sw = w / float(n)
    for i in range(n):
        x0 = x + i * sw
        col = SPECTRUM[i]
        if i in bites:
            col = (18, 22, 28)
        draw.rectangle([x0, y, x0 + sw, y + h], fill=col)
        if i in crosses:
            draw.rectangle([x0, y, x0 + sw, y + h], fill=(10, 12, 16))
    # keyline around the whole bar — hairline, so it reads as one object
    draw.rectangle([x, y, x + w, y + h], outline=INK, width=K.DETAIL)
    # hairline separators between swatches
    for i in range(1, n):
        _vline(draw, x + i * sw, y, y + h, INK, width=K.HAIRLINE,
               seed=seed + i, wobble=0.4)
    for i in sorted(set(bites) | set(crosses)):
        cx = x + i * sw + sw / 2.0
        if i in crosses:
            for sgn, sd in ((1, seed + 30 + i), (-1, seed + 40 + i)):
                _thick_curve(draw,
                             [(cx - 0.34 * sw, y + h * 0.5 - sgn * h * 0.30),
                              (cx, y + h * 0.5),
                              (cx + 0.34 * sw, y + h * 0.5 + sgn * h * 0.30)],
                             BONE if flat else AMBER, seed=sd,
                             width=K.DETAIL, wobble=1.0, wavelength=40.0)
        else:
            _tiny(draw, 'GONE', cx, y + h / 2.0, BONE, px=13)
    return sw


def _droplet(draw, cx, cy, r, color, seed, keyline=None):
    """A small water drop: a teardrop silhouette, flat fill, thin keyline."""
    pts = [(cx, cy - r * 1.5)]
    for i in range(1, 17):
        a = math.radians(-90 + 200 * i / 16.0)
        pts.append((cx + r * math.sin(a) * (1.0 + 0.25 * math.cos(a * 0.5)),
                    cy + r * math.cos(a) * 0.95 + r * 0.25))
    K.draw_smooth(draw, pts, fill=color,
                  outline=keyline if keyline is not None else color,
                  width=K.HAIRLINE, seed=seed, wobble=1.0, wavelength=50.0)


def _tiny(draw, text, cx, cy, fill, px=None):
    """Locked-family REGULAR annotation, centred. Diagram labels only.

    Defaults to the locked STAMP_PX. Off-scale sizes are the caller's explicit
    choice (measured against the locked set) and never a font file.
    """
    font = T.load_font_at(px or T.STAMP_PX, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    draw.text((cx - w / 2.0 - x0, cy - h / 2.0 - y0), text, font=font, fill=fill)


def _hero(draw, text, cx, cy, fill_rgb=None, px=64, y_max=606, stroke=3):
    """Every dominant on-card phrase goes through C.hero_word.

    C.hero_word measures the SAME call the renderer makes and clamps INCLUDING
    the 3px keyline, so a phrase can never run off an edge or ride up into the
    title strip. Never clamp by hand against T._bbox (that is how "A NEUTRON
    STAR" once shipped with its final R cut off).
    """
    return C.hero_word(draw, text, cx, cy,
                       fill_rgb=fill_rgb if fill_rgb is not None else BONE,
                       stroke_rgb=INK, stroke_width=stroke, px=px,
                       margin=40, y_max=y_max)


def _void_field(seed, stars=120):
    """A Register-S space field with a per-card starfield seed, so no two void
    cards in the segment are the same frame with the same stars."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars)
    return img


def _cream_field(seed, grain=True):
    """A Register-P cream card: flat paper plus an OPTIONAL broad painterly wash.

    GATE NOTE — WHY THIS IS NO LONGER A STIPPLE. The old version added a fine
    1px stipple (density 0.0025) of near-paper dots. On a PAINT card the gate's
    ink mask treats any pixel >30 (summed RGB) from the dominant cream as ink, so
    those faint dots registered as INK, and — because they grouped into pairs with
    matched heights on an otherwise flat surround — the gate's LOW_CONTRAST_TEXT
    and CLIPPED_AT_EDGE checks fired on the GRAIN, not on real type. That was a
    measurement artefact, not a legibility defect, but it is indistinguishable
    from a defect downstream, so the grain had to go. The "not a dead swatch"
    intent is kept with a broad soft wash in (250,246,234), a value ~8 from the
    paper — below the ink threshold, so it textures the field without being ink.
    """
    img = Image.new('RGB', (W, H), PAPER)
    if grain:
        img = _soft_wash(img,
                         [(150, 130), (640, 108), (1130, 150), (1250, 300),
                          (900, 400), (420, 392), (90, 270)],
                         (250, 246, 234), 210, seed=seed, wobble=16.0, blur=32)
    return img


# ---------------------------------------------------------------------------
# G4 / G5 — label placement and contrast. Thin wrappers over lib/labels.py so no
# card re-derives contrast maths or edge-clamping locally.
# ---------------------------------------------------------------------------

def _label(img, text, anchor_xy, prefer="right", avoid=None, fill=None,
           size_px=None, bold=False, px=None, dark=None, light=None,
           leader=False, leader_color=None, seed=0):
    """Place one diagram label next to its subject.

    Delegates entirely to lib.labels.place_label, which (a) picks the text colour
    from auto_contrast against the ground it actually landed on (G4) and (b) keeps
    the ink box clear of the frame edge and of any `avoid` shape (G5). `px` is an
    alias for size_px so callers can be terse. On the dark register the default
    dark/light pair is cream/black rather than pure black/white so a label never
    shouts brighter than the paper the rest of the card uses."""
    kw = {}
    if dark is not None:
        kw['dark'] = dark
    if light is not None:
        kw['light'] = light
    return Lb.place_label(img, text, anchor_xy, prefer=prefer, avoid=avoid,
                          fill=fill, size_px=size_px or Lb.LABEL_PX, bold=bold,
                          leader=leader, leader_color=leader_color, seed=seed,
                          **kw)


def _note(img, text, xy, px=None, color=None, dark_bg=True):
    """A tiny annotation stamp, clamped and contrast-checked (G4/G5)."""
    col = color
    if col is None:
        col = (245, 240, 225) if dark_bg else INK
    return Lb.note(img, text, xy, size_px=px or T.STAMP_PX, color=col,
                   ink=INK if dark_bg else PAPER)


def _finish(img, card, planet, paper_band, dark_bg):
    """The Layout-A tail every card in this segment shares: title strip, then
    the schedule-driven character in the correct register theme, then the one
    floating caption call. Returns the frame."""
    C._header(img, planet, paper_band=paper_band)
    C._draw_stickman(img, card, theme=('dark' if dark_bg else 'light'))
    C._caption(img, card.get('caption', ''), 70, 652, dark_bg=dark_bg)
    return img


def _ground_figure(img, card, ground_y, dark_bg=True, width=5, seed=0):
    """G7 — draw the ground line the figure's feet stand on, BEFORE the figure.

    The schedule already pins the feet to y_top + height; this only guarantees a
    visible surface under them so he is not floating in an empty field. On the
    dark register the line is a mid bone so it reads on space; on cream it is
    ink. Delegates the wobble to S.draw_ground_line. Returns ground_y."""
    col = (170, 178, 186) if dark_bg else INK
    d = ImageDraw.Draw(img)
    S.draw_ground_line(d, int(ground_y), 0, W, color=col, width=width,
                       seed=seed)
    return ground_y


def _low_mass(img, seed, y0=540, rgb=None, alpha=70, rake=True, rake_y=None,
              rake_color=None, rake_width=None):
    """G1 — put real visual mass in the lower quarter of the frame.

    WHY A HELPER. Shifting a subject down is not enough on the void cards. The
    gate's ink mask counts every pixel that differs from the single dominant
    background colour by more than 30 (summed RGB), and the PAPER TITLE STRIP is
    1280x84 = 107k px sitting at y ~42, all of which counts as ink on a void card.
    That is a fixed mass at the very top of the frame. Raising v_centroid to the
    0.42 floor therefore needs roughly 50k px of NEW ink down at y ~600 — that is
    a full-width band, not a nudge. Shifting the old content down cannot do it:
    the title strip pulls the centroid up no matter where the rest sits.

    So this draws the band that was missing: a broad, soft, flat-colour wash
    across the bottom quarter (register-legal — flat colour, soft edge, no
    gradient), optionally under a heavy inked rule so the lower edge of the
    composition is drawn rather than implied. Both are register-correct: a wash
    is a painted field, and the rule is K.OUTLINE, the canon's large-shape stroke.

    `rake` draws that rule at `rake_y` (default: the wash's upper edge)."""
    rgb = rgb if rgb is not None else TEAL
    img = _soft_wash(img,
                     [(0, y0 + 26), (420, y0 - 12), (900, y0 + 20),
                      (1280, y0 - 28), (1280, 660), (700, 638), (0, 664)],
                     rgb, alpha, seed=seed, wobble=13.0, blur=24)
    if rake:
        d = ImageDraw.Draw(img, 'RGBA')
        _open_curve(d,
                    [(x, (rake_y if rake_y is not None else y0 + 30)
                      - 22 * math.sin(math.pi * x / float(W)))
                     for x in range(0, W + 1, 40)],
                    rake_color if rake_color is not None else rgb,
                    width=rake_width or K.OUTLINE, seed=seed + 1, wobble=1.6,
                    wavelength=400.0)
    return img


def _ground_band(img, y_top, seed, fill=OLIVE, sky=None):
    """A wavy olive ground plane across the lower third (STYLE_CANON's
    2026-09-30 addendum: ground the character where he is the subject).

    `roughness` sits at 6: K.draw_ground steps the top edge every 26px with
    +/-roughness jitter, so too little reads as a ruler-straight stripe and too
    much (13) reads as a cartoon sawtooth. 6 is a painted horizon. The ground is
    ONE value with one keyline — a second lighter band stacked under the lip
    doubles the sawtooth, which is the wrong read.
    """
    if sky is not None:
        d = ImageDraw.Draw(img)
        d.rectangle([0, T.ART_TOP, W, y_top + 40], fill=sky)
    d = ImageDraw.Draw(img)
    K.draw_ground(d, 0, W, y_top, H, fill, seed=seed, width=K.OUTLINE,
                  roughness=6.0)
    return img


# ---------------------------------------------------------------------------
# 1. hurricane_forget_it — HOOK. VOID / bone. Character: braced, deadpan.
# ---------------------------------------------------------------------------

def render_hurricane_forget_it(card, planet="WASP-127b"):
    """B1 HOOK. The comparison the segment opens on, and it has to be SMALL: a
    cream spiral of wind-lines arcing off the right edge over a void field, with
    the character braced at the left, planted on a ground line, deadpan. The
    line is that a hurricane you have all felt is nothing next to this — so the
    art is a whisper, and the starfield is most of the frame. The hero word is
    'FORGET IT', which is the beat's instruction rather than a restatement of the
    caption.

    G1 — the spiral is centred LOW (y 400) and its widest arms reach the bottom
    of the art area, and the figure is GROUNDED (G7) on a low ground line, so the
    frame's visual mass sits in the lower two-thirds (v_centroid was 0.269, i.e.
    upper-third heavy)."""
    img = _void_field(seed=601, stars=132)
    d = ImageDraw.Draw(img, 'RGBA')

    # a soft bone wash low-right: the wind is a pressure, not a wall
    img = _soft_wash(img,
                     [(1006, 470), (1180, 420), (1256, 300), (1210, 190),
                      (1050, 214), (952, 340)],
                     BONE, 26, seed=602, wobble=17.0, blur=30)
    d = ImageDraw.Draw(img, 'RGBA')

    # Five spiral arms, widening outward, all opening left toward the figure.
    # Centred at y 400 (was 340) and widened so the outer arms reach the lower
    # frame, moving mass down. Sampled DENSELY (n=110) with a gentle
    # low-frequency wobble (amount 1.0, wavelength 400): a coarse 34-point
    # polyline plus a 2.4px wobble made the arms zigzag, because the wobble sine
    # was evaluated at too few points and the spline amplified the alternation.
    for k, (r0, r1, a0, a1, a, w) in enumerate((
            (70, 160, 150, 300, 150, 6),
            (110, 250, 140, 292, 175, 7),
            (150, 350, 128, 286, 195, 8),
            (196, 455, 118, 278, 215, 8),
            (250, 575, 108, 268, 235, 8))):
        _thick_curve(d, _spiral_pts(1120, 452, r0, r1, a0, a1, n=110, drift=0.10),
                     BONE + (a,), seed=610 + k, width=w, wobble=1.0,
                     wavelength=400.0)

    # G1 - a broad foreground wind band across the bottom quarter, so the frame's
    # visual mass sits in the lower two-thirds (v_centroid was 0.297).
    img = _soft_wash(img,
                     [(0, 566), (420, 528), (900, 560), (1280, 512),
                      (1280, 660), (700, 638), (0, 664)],
                     TEAL, 68, seed=606, wobble=13.0, blur=24)
    d = ImageDraw.Draw(img)

    # G7 — the figure is planted: a mid bone ground line his feet sit on.
    _ground_figure(img, card, GROUND_Y, dark_bg=True, width=5, seed=651)

    d = ImageDraw.Draw(img)
    _hero(d, 'FORGET IT', 790, 556, BONE, px=64, y_max=606)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 2. name_the_planet — REVEAL. CREAM / amber. No character.
# ---------------------------------------------------------------------------

def render_name_the_planet(card, planet="WASP-127b"):
    """B2 REVEAL. The name and the situation in one picture: a fat flat gas giant
    crowded up against a huge sun at the right frame edge, with a wobbly arrow
    between them — the arrow is the whole beat, because the star is what is doing
    this to the planet. No character: the object is the subject, and the reveal
    should not compete with a face.

    Register P. Flat painted sun (no gradient on cream — see _flat_star), flat
    banded giant, 6px keylines. Hero word 'TOO CLOSE', which adds the situation
    the caption states in words.

    G1 — the planet is scaled up (r 176 -> 210) and dropped so its centre sits at
    v 0.56, a low elliptical orbit arc is inked across the lower third to give the
    frame bottom mass, and the hero word sits low. ink_fraction was 0.245."""
    img = _cream_field(seed=701)
    d = ImageDraw.Draw(img)

    # the star, half off the right edge, so it reads as a presence not an object
    _flat_star(d, 1196, 268, 158, AMBER, seed=710, rays=9, ray_len=0.42,
               ray_w=0.15)

    # G2 — three expanding heat rings between the star and the planet: a
    # directional cue (energy arriving), not a static object. Light amber, thin.
    for k, rr in enumerate((150, 205, 260)):
        _thick_curve(d, _spiral_pts(1006, 268, rr, rr, 96, 264, n=64)[:8],
                     AMBER, seed=726 + k, width=K.FINE, wobble=0.6,
                     wavelength=200.0)

    # the planet, crowded against it, scaled up and dropped into the lower frame
    img = _banded_giant(img, 560, 430, 210,
                        [(196, 206, 210), (168, 182, 190), (140, 158, 168),
                         (176, 190, 196), (150, 166, 176), (186, 198, 204)],
                        seed=711)

    # G1 — a low elliptical orbit arc the planet rides, inked across the lower
    # third. Gives the frame real bottom mass and reads as "this is its orbit".
    orbit = [(cx, 542 + 152 * math.sin(math.pi * (cx - 60) / (1160 - 60.0)))
             for cx in range(60, 1161, 40)]
    _open_curve(d, orbit, INK, width=K.DETAIL, seed=713, wobble=1.6,
                wavelength=300.0)

    # the arrow: star -> planet. It is the only thing on the card that moves the
    # eye, so it is the heaviest ink on the card.
    d = ImageDraw.Draw(img)
    _arrow(d, 980, 300, 800, 330, INK, width=K.OUTLINE, seed=712, head=40)

    d = ImageDraw.Draw(img)
    # G4 — the 'HEAT' label is placed off the shapes by lib.labels, auto-contrast
    # checked against the ground it lands on (it sat on cream and read fine before,
    # but going through place_label guarantees it never lands on the planet or the
    # star and never clips).
    _label(img, 'HEAT', (960, 236), prefer='above', avoid=(1196, 268, 175),
           dark=INK, light=PAPER, px=20, seed=714)
    _hero(d, 'TOO CLOSE', 350, 570, INK, px=60, y_max=606, stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 3. fastest_winds — DATA. VOID / teal. Character: pointing up, awed.
# ---------------------------------------------------------------------------

def render_fastest_winds(card, planet="WASP-127b"):
    """B3 DATA. The speed, made visible: three stacked teal speed bars to the
    right of the character, each longer than the one above it, with streaming
    wind ribbons behind them so the numbers have weather attached. The character
    points up at the top bar, awed.

    Void register, so the figure is theme='dark' — cream on space. The bars are
    flat teal fills with ink keylines: no gradient on a diagram.

    G1 — the whole bar stack is dropped lower (y 372..492 -> 396..552) and a
    foreground wind band sweeps across the bottom quarter, so the frame's mass
    sits in the lower two-thirds (v_centroid was 0.318). G7 — the figure is
    grounded on a low ground line."""
    img = _void_field(seed=801, stars=126)

    # Streaming ribbons: three long teal bands sweeping across the middle/right.
    # These are SOFT WASHES, not strokes. A 46px-wide semi-transparent curve
    # drawn with draw.line(joint='curve') over a shallow 11-point path combed
    # into visible stripes — each short segment's body and the round joint
    # ellipses overlap and stack up additively. A blurred flat fill is what a
    # wind ribbon actually looks like anyway, and it is register-legal (flat
    # colour, soft edge, no gradient, no outline).
    for k, (y, a, hgt) in enumerate(((232, 78, 58), (296, 58, 48), (356, 40, 38))):
        band = []
        for i in range(13):
            u = i / 12.0
            band.append((548 + u * 730, y - 26 * math.sin(math.pi * u * 1.6 + k)))
        lower = [(x, yy + hgt + 8 * math.sin(i * 0.7 + k))
                 for i, (x, yy) in enumerate(reversed(band))]
        img = _soft_wash(img, band + lower, TEAL, a, seed=810 + k, wobble=5.0,
                         wavelength=180.0, blur=13)

    # three speed bars, stacked, each with a flat teal fill and an ink keyline,
    # dropped lower so the stack occupies the middle/lower frame
    d = ImageDraw.Draw(img)
    bars = ((398, 300, 690), (466, 500, 1180), (534, 720, 1180))
    for k, (y, x0, x1) in enumerate(bars):
        d.rectangle([x0, y, x1, y + 44], fill=TEAL if k else BONE)
        d.rectangle([x0, y, x1, y + 44], outline=INK, width=K.DETAIL)
    # the fastest bar is the hot one — the only amber on the card
    d.rectangle([720, 534, 1180, 578], fill=AMBER)
    d.rectangle([720, 534, 1180, 578], outline=INK, width=K.DETAIL)

    # G1 — a broad foreground wind band low across the frame to seat the stack.
    img = _soft_wash(img,
                     [(0, 596), (420, 566), (900, 592), (1280, 560),
                      (1280, 660), (700, 636), (0, 660)],
                     TEAL, 74, seed=818, wobble=12.0, blur=22)
    d = ImageDraw.Draw(img)

    # G7 — ground the figure at the lower-left.
    _ground_figure(img, card, GROUND_Y, dark_bg=True, width=5, seed=851)

    d = ImageDraw.Draw(img)
    _note(img, 'FASTEST MEASURED', (952, 372), px=19, dark_bg=True)
    _hero(d, 'NO BRAKES', 950, 566, BONE, px=58, y_max=606)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 4. never_land — DATA. CREAM / bone. No character.
# ---------------------------------------------------------------------------

def render_never_land(card, planet="WASP-127b"):
    """B4 DATA. The fact that nothing ever touches down, drawn as the fact
    itself: a plain flat planet with five long wind arrows crossing it edge to
    edge, and NOT ONE of them stopping, turning, or touching the surface. Every
    arrow overshoots the disc on both sides — that overshoot IS the argument, so
    the arrows are inked heavier than the planet.

    No character: a diagram card, and the diagram has to be clean enough to read
    the overshoot at a glance.

    G1 — the planet is scaled up (r 152 -> 190) and the arrows thickened, and a
    low cloud-deck band anchors the bottom, so ink_fraction was 0.165 -> raised.
    The 'SURFACE' and 'NEVER LANDS' labels now go through lib.labels so they are
    contrast-checked and never clipped."""
    img = _cream_field(seed=901)
    d = ImageDraw.Draw(img)

    # G1 — a soft cloud-deck band low so the frame has bottom mass and a surface.
    img = _soft_wash(img,
                     [(0, 470), (430, 452), (900, 476), (1280, 448),
                      (1280, 720), (0, 720)],
                     (216, 224, 228), 190, seed=902, wobble=14.0, blur=30)
    d = ImageDraw.Draw(img)

    # the planet: a plain flat oval, minimal banding, scaled up — it is a stage
    # for the arrows, not a portrait
    img = _banded_giant(img, 640, 428, 190,
                        [(206, 214, 216), (184, 196, 200), (166, 180, 186),
                         (196, 206, 210), (176, 190, 196)],
                        seed=910, n_bands=5)
    d = ImageDraw.Draw(img)

    # five wind arrows crossing edge to edge, all overshooting, thicker
    #
    # EDGE-CLIP FIX: the tips used to run off the frame. _arrow's open-V barbs
    # extend head*cos(140) ~= 0.77*head PAST the tip (head=36 -> ~28px), plus
    # stroke width and the wobble, so x1=1170+k*10 put the top arrow's point at
    # ~1246 and the wobble pushed strokes past x=1279 -- the gate flagged five
    # CLIPPED_AT_EDGE hits on this frame at label scale. The overshoot IS the
    # argument, so it stays; it just has to finish INSIDE the frame. x1 tops out
    # at 1192 (tip+barb ~1220, ~60px of clearance) which still overshoots the
    # disc's right limb (~830) by 350px, so the beat reads identically.
    for k in range(5):
        y = 300 + k * 64
        x0, x1 = 90 + k * 6, 1152 + k * 10
        _arrow(d, x0, y, x1, y - 10 + k * 5, INK, width=K.OUTLINE,
               seed=920 + k, head=36)
    # and a dashed "surface" line inside the disc with NOTHING touching it, so the
    # never-lands idea has a visible surface to fail to reach
    _hrule(d, 552, 540, 740, BONE, width=K.DETAIL, seed=930, wobble=1.0)

    d = ImageDraw.Draw(img)
    _label(img, 'SURFACE', (640, 552), prefer='below', avoid=(640, 428, 195),
           dark=INK, light=PAPER, px=18, seed=931)
    _hero(d, 'NEVER LANDS', 640, 574, INK, px=58, y_max=606, stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 5. almost_empty — DATA. VOID / amber. No character. Pure data beat.
# ---------------------------------------------------------------------------

def render_almost_empty(card, planet="WASP-127b"):
    """B5 DATA, pure data card — no character, by the script's own instruction.

    The density comparison is the beat, so it is drawn as a comparison: a FULL
    banded giant on the left and a nearly HOLLOW one on the right at the same
    radius, the hollow one carrying only a thin rim and a couple of wisps where
    the other has solid strata. A low-density stamp ties them together. Void
    register, so both planets are matte discs with no gradient and no glow — a
    glow would read as mass.

    G1 — the pair is scaled up (r 132 -> 158) and dropped so the centres sit at
    v ~0.52, and a comparison baseline is inked low, so the mass sits in the lower
    two-thirds (v_centroid was 0.317)."""
    img = _void_field(seed=1001, stars=120)
    d = ImageDraw.Draw(img, 'RGBA')

    cx, cy, r = 316, 428, 158
    # LEFT: the full giant. Six solid strata, a real body.
    img = _banded_giant(img, cx, cy, r,
                        [(198, 208, 212), (166, 180, 188), (140, 156, 166),
                         (186, 196, 202), (150, 166, 174), (180, 192, 198)],
                        seed=1010)
    # RIGHT: the same radius, almost nothing inside. A thin rim and three wisps.
    cx2 = 964
    img = _banded_giant(img, cx2, cy, r,
                        [(58, 66, 74), (40, 46, 54), (26, 30, 36),
                         (48, 56, 64), (30, 35, 42), (44, 52, 60)],
                        seed=1011)
    d = ImageDraw.Draw(img, 'RGBA')
    for k in range(3):
        y = cy - 66 + k * 66
        pts = [(cx2 - r * 0.66 + i * (r * 1.32 / 8.0),
                y + 8 * math.sin(i * 0.8 + k * 1.6)) for i in range(9)]
        _open_curve(d, pts, BONE + (150,), width=K.DETAIL, seed=1020 + k,
                    wobble=1.6, wavelength=110.0)

    # G1 — a comparison baseline low under both, grounding the pair.
    d = ImageDraw.Draw(img)
    _hrule(d, 620, 200, 1080, BONE + (110,), width=K.DETAIL, seed=1030,
           wobble=1.6)

    d = ImageDraw.Draw(img)
    _label(img, 'FULL', (cx, cy), prefer='below', avoid=(cx, cy, r + 20),
           dark=INK, light=(245, 240, 225), px=22, seed=1031)
    _label(img, 'NEARLY EMPTY', (cx2, cy), prefer='below',
           avoid=(cx2, cy, r + 20), dark=INK, light=(245, 240, 225), px=22,
           seed=1032)
    _hero(d, 'A GIANT MADE OF AIR', 620, 566, AMBER, px=56, y_max=606)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 6. nothing_inside — PIVOT. CREAM / teal. Character: shrugged, uncomfortable.
# ---------------------------------------------------------------------------

def render_nothing_inside(card, planet="WASP-127b"):
    """B6 PIVOT, and the first beat where the character is the SUBJECT rather
    than a scale figure, so per STYLE_CANON's 2026-09-30 addendum he is GROUNDED:
    he stands on a wavy olive band under a plain cream sky, with the planet flat
    and banded behind him. Register P throughout — flat fills, 6px keylines, no
    gradient anywhere, including on the planet behind him.

    The shrug and the zigzag mouth carry the pivot: there is nothing to stand on
    and he knows it. The two dashed wind lines cross behind him at shoulder
    height so the wind is visibly going past a man who cannot stay put."""
    img = _cream_field(seed=1101, grain=False)
    # plain sky wash so the field is not a dead swatch behind the ground band
    img = _soft_wash(img,
                     [(180, 150), (640, 108), (1100, 156), (1230, 300),
                      (900, 380), (420, 372), (110, 268)],
                     (250, 246, 234), 200, seed=1102, wobble=16.0, blur=34)
    img = _ground_band(img, 552, seed=1103)
    d = ImageDraw.Draw(img)

    # the planet behind him: flat, banded, matte, 6px keyline. No glow — a glow
    # on a cream field reads as a soft-fantasy halo (CLAUDE.md §10.6).
    img = _banded_giant(img, 940, 300, 190,
                        [(188, 202, 208), (156, 174, 184), (128, 148, 160),
                         (176, 192, 200), (142, 162, 172), (170, 186, 196)],
                        seed=1104)
    d = ImageDraw.Draw(img, 'RGBA')
    # Two wind lines crossing BEHIND him at chest height. Sampled densely (24
    # points) with a gentle wobble: a shallow 11-point polyline drew as short
    # segments left a visible ladder of steps, because draw.line's per-segment
    # bodies show at near-zero segment angle. These pass behind the figure (it
    # is drawn later, in _finish) so the wind visibly goes past a man who cannot
    # stay put.
    for k, (y, a) in enumerate(((332, 165), (386, 120))):
        pts = [(150 + i * 41, y + 15 * math.sin(i * 0.26 + k * 1.4)
                + 5 * math.sin(i * 0.71 + k)) for i in range(25)]
        _thick_curve(d, pts, TEAL + (a,), seed=1110 + k, width=8, wobble=1.2,
                     wavelength=300.0)

    d = ImageDraw.Draw(img)
    _hero(d, 'NOTHING TO STAND ON', 400, 176, INK, px=46, y_max=232, stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 7. read_the_star — METHOD. VOID / bone. No character.
# ---------------------------------------------------------------------------

def render_read_the_star(card, planet="WASP-127b"):
    """B7 METHOD. The instrument, drawn left to right in one read: a small star
    at the left firing a bone light-arrow into a prism at the centre, which fans
    out into the flat spectrum bar. No character: this is a how-it-works diagram
    and a face in it would be noise.

    G3 — the star is a LUMINOUS body, so it is drawn with lib.emissive's
    emissive_limb + soft_glow (a real halo and a lit crescent), not the old
    hard radial core. G1 — the whole instrument is dropped lower (star y 356 ->
    400, prism and spectrum down) and a faint ground-rake is inked across the
    bottom, so the frame's mass sits in the lower two-thirds (v_centroid was
    0.299). Labels go through lib.labels (G4/G5)."""
    img = _void_field(seed=1201, stars=118)
    d = ImageDraw.Draw(img, 'RGBA')

    # the star — a luminous body (G3). C._radial_core needs INTEGER cx/cy.
    sx, sy = 176, 448
    # G3 — emissive_limb paints the halo first, then the core, then a lit
    # crescent and grain. That is the template tres2b beat_10 proved works.
    E.emissive_limb(img, sx, sy, 54,
                    core_color=(60, 44, 26), limb_color=AMBER,
                    light_deg=300, hot=(255, 236, 190),
                    halo=True, halo_spread=2.6, halo_strength=150,
                    stipple_color=(255, 220, 170), stipple_seed=1206,
                    stipple_count=40, outline=None)
    d = ImageDraw.Draw(img, 'RGBA')

    # the incoming light: a bone beam from the star to the prism
    _thick_curve(d, [(sx + 58, sy), (330, sy - 10), (470, sy - 22)],
                 BONE + (215,), seed=1210, width=10, wobble=1.8, wavelength=180.0)

    # the prism: a flat bone triangle with an ink keyline, apex right
    tri = [(560, sy - 100), (560, sy + 100), (700, sy)]
    K.draw_smooth(d, tri, fill=BONE, outline=INK, width=K.OUTLINE, seed=1211,
                  wobble=2.0, wavelength=150.0, closed=True)

    # the fan: four bone rays out of the prism to the spectrum bar
    for k in range(4):
        t = k / 3.0
        _thick_curve(d, [(704, sy), (860, 336 + t * 210)],
                     BONE + (200 - k * 24,), seed=1220 + k, width=7,
                     wobble=1.6, wavelength=150.0)

    # the spectrum bar, flat swatches, at the right, dropped lower
    d = ImageDraw.Draw(img)
    _spectrum_bar(d, 900, 372, 320, 138, seed=1230)

    # G1 — a faint ground-rake low to seat the instrument.
    _hrule(d, 590, 80, 1200, BONE + (70,), width=K.DETAIL, seed=1240, wobble=1.6)

    d = ImageDraw.Draw(img)
    _label(img, 'LIGHT IN', (300, sy - 40), prefer='above',
           dark=INK, light=(245, 240, 225), px=18, seed=1241)
    _label(img, 'COLOURS OUT', (1060, 336), prefer='above',
           dark=INK, light=(245, 240, 225), px=18, seed=1242)
    _hero(d, 'READ THE STAR', 640, 548, BONE, px=58, y_max=606)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 8. swallowed_colors — METHOD. CREAM / amber. Character: pointing, deadpan.
# ---------------------------------------------------------------------------

def render_swallowed_colors(card, planet="WASP-127b"):
    """B8 METHOD. The same bar from the last card, now with the atmosphere's
    fingerprints taken out of it: four slices knocked down to near-black with a
    GONE stamp over each, and the character at the right pointing straight at
    the bites, flat deadpan — he is reading, not reacting.

    Cream register, so the figure is theme='light'. A teal wash sits behind the
    bar so the card reads as a composed illustration rather than three marks on
    a field, and it is blurred so it never shows a corner."""
    img = _cream_field(seed=1301)
    img = _soft_wash(img,
                     [(300, 214), (700, 190), (980, 250), (1010, 430),
                      (760, 508), (400, 470), (270, 330)],
                     TEAL, 44, seed=1302, wobble=17.0, blur=28)
    d = ImageDraw.Draw(img)

    # the bar with four bites out of it
    _spectrum_bar(d, 120, 330, 720, 178, seed=1310, bites=(1, 3, 4, 6))
    # G4 — the caption over the bar goes through lib.labels so it is
    # contrast-checked against the teal wash behind it and never clipped.
    _label(img, 'WHAT THE AIR ATE', (480, 284), prefer='above',
           dark=INK, light=PAPER, px=20, seed=1311)

    d = ImageDraw.Draw(img)
    _hero(d, 'THE COLOURS THAT VANISHED', 640, 566, INK, px=50, y_max=606,
          stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 9. missing_tells_you — MECHANISM. VOID / teal. No character. Pure data beat.
# ---------------------------------------------------------------------------

def render_missing_tells_you(card, planet="WASP-127b"):
    """B9 MECHANISM, pure data card — no character by the script's instruction.

    The bar returns with three slices CROSSED OUT, and one small water drop
    drifting up off the top of the frame: that is the mechanism, and it is worth
    two objects. The crosses are drawn in bone over slate-black slices rather
    than in red, because red is the character's shirt and must be the only red
    on screen (hard rule 10).

    G1 — the bar is scaled up and dropped lower (centre y 405 -> 430, taller),
    the escaping drop is enlarged, and a low "the gaps name it" ground-rake is
    inked, so ink_fraction was 0.196 and v_centroid was 0.289; both rise into
    range. Labels go through lib.labels (G4/G5)."""
    img = _void_field(seed=1401, stars=116)
    d = ImageDraw.Draw(img)

    # the bar, three slices crossed out, dropped lower and taller
    _spectrum_bar(d, 130, 400, 760, 176, seed=1410, crosses=(2, 4, 5),
                  flat=True)

    # the answer, leaving: a teal drop climbing off the top of the art band,
    # enlarged so it reads as the subject
    d = ImageDraw.Draw(img)
    _droplet(d, 1044, 226, 34, TEAL, seed=1420)
    for k, y in enumerate((164, 116)):
        _vline(d, 1044 + (k * 10 - 5), y, y - 32, TEAL, width=K.DETAIL,
               seed=1421 + k, wobble=1.2)

    # G1 — a low ground-rake to seat the bar and give the frame bottom mass.
    _hrule(d, 592, 90, 1190, BONE + (70,), width=K.DETAIL, seed=1430, wobble=1.6)

    d = ImageDraw.Draw(img)
    _label(img, 'MISSING', (510, 400), prefer='above',
           dark=INK, light=(245, 240, 225), px=20, seed=1431)
    _label(img, 'WATER', (1044, 226), prefer='right',
           dark=INK, light=(245, 240, 225), px=19, seed=1432)
    _hero(d, 'THE GAPS NAME IT', 560, 556, TEAL, px=58, y_max=606)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 10. water_leaving — REVEAL. CREAM / bone. No character.
# ---------------------------------------------------------------------------

def render_water_leaving(card, planet="WASP-127b"):
    """B10 REVEAL. The escape, drawn as a path rather than a sentence: the planet
    low in frame with a dotted rising trail leaving its top limb, three burst
    marks where the air leaves, and one long arrow carrying it off the top edge.
    Nothing comes back down — there is deliberately no return stroke anywhere on
    this card, and that absence is the point.

    Cream register, flat fills, no gradient. The trail dots shrink as they climb
    so the air reads as thinning on its way out.

    G1 — the planet is scaled up (r 178 -> 220) and sunk further into the bottom
    of the frame so it FILLS the lower half; the trail is thickened and the
    up-arrow heavier. ink_fraction was 0.163. Labels go through lib.labels
    (G4/G5), and 'AND KEEPS GOING' is placed clear of the frame edge."""
    img = _cream_field(seed=1501)

    # the planet, low and large, so there is room above it for the escape
    img = _banded_giant(img, 470, 520, 220,
                        [(200, 210, 214), (170, 184, 192), (142, 160, 170),
                         (188, 200, 206), (152, 170, 180), (180, 194, 202)],
                        seed=1510)
    d = ImageDraw.Draw(img)

    # the dotted rising trail off the top limb, thickening then thinning as it
    # climbs — larger, denser dots so the escape reads as a real plume
    for k in range(13):
        u = k / 12.0
        x = 470 + 320 * u
        y = 300 - 210 * u
        rr = max(4, int(14 * (1.0 - 0.58 * u)))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=TEAL)

    # three burst marks at the exit point on the limb, thicker
    for k, ang in enumerate((198, 250, 302)):
        a = math.radians(ang)
        x0, y0 = 470 + 240 * math.cos(a), 520 + 240 * math.sin(a)
        _thick_curve(d, [(x0, y0), (x0 + 46 * math.cos(a), y0 + 46 * math.sin(a))],
                     INK, seed=1520 + k, width=9, wobble=1.4, wavelength=40.0)

    # the long up-arrow, off the top edge. No arrow comes back down.
    _arrow(d, 850, 566, 1096, 150, INK, width=K.OUTLINE, seed=1530, head=44)

    d = ImageDraw.Draw(img)
    _label(img, 'AND KEEPS GOING', (1096, 150), prefer='below-right',
           dark=INK, light=PAPER, px=19, seed=1531)
    _hero(d, 'UPWARD', 300, 178, INK, px=58, y_max=234, stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 11. grains_high_above — REVEAL. VOID / amber. No character.
# ---------------------------------------------------------------------------

def render_grains_high_above(card, planet="WASP-127b"):
    """B11 REVEAL. A close-up of the planet's upper LIMB across the bottom of the
    frame — a limb, not a full sphere, because the subject is how far the haze
    sits ABOVE the cloud deck — with a stippled band of tiny grains suspended far
    above it and a measured gap between them. The gap is drawn as two hairline
    rules so the altitude reads as a distance rather than a vibe.

    Void register. The limb is flat banded paint with a 6px keyline; the grains
    are deterministic K.stipple at two densities so the haze has a core and a
    fringe."""
    img = _void_field(seed=1601, stars=124)
    d = ImageDraw.Draw(img)

    # the upper limb: a wide flat arc entering from the bottom, banded
    img = _banded_giant(img, 640, 1010, 470,
                        [(178, 192, 200), (150, 168, 178), (122, 142, 156),
                         (168, 184, 194), (136, 156, 168), (162, 178, 188)],
                        seed=1610)

    d = ImageDraw.Draw(img, 'RGBA')
    # the suspended grain band: a dense core with a faint fringe, well clear of
    # the limb. Density and radius both fall off toward the top of the band.
    for k in range(5):
        y0 = 190 + k * 26
        a = (86, 78, 70, 60, 46)[k]
        K.stipple(d, 120, y0, 1180, y0 + 30, BONE + (a,), seed=1620 + k,
                  density=0.030 - 0.004 * k, r=1, spread=2)

    d = ImageDraw.Draw(img)
    # the two hairline rules measuring the gap, plus the label between them
    _hrule(d, 158, 120, 1180, BONE, width=K.HAIRLINE, seed=1630, wobble=1.2)
    _hrule(d, 360, 120, 1180, BONE, width=K.HAIRLINE, seed=1631, wobble=1.2)
    _vline(d, 120, 158, 360, BONE, width=K.HAIRLINE, seed=1632, wobble=1.0)
    _tiny(d, 'TOO HIGH', 176, 258, BONE, px=19)
    _tiny(d, 'CLOUD DECK', 120, 396, BONE, px=17)
    _hero(d, 'SMALL GRAINS', 900, 520, AMBER, px=54, y_max=580)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 12. throwing_its_away — PIVOT. CREAM / teal. Character: hands up, scared.
# ---------------------------------------------------------------------------

def render_throwing_its_away(card, planet="WASP-127b"):
    """B12 PIVOT, and the segment's thesis card. As beat 6: the character is the
    subject, so he is grounded on the wavy olive band under a plain cream sky,
    both hands up, downturned scared arc — and the planet is SLIDING OFF THE LEFT
    EDGE, more than half of it gone, with three escape marks still trailing off
    the frame.

    That composition is the argument: the thing that is leaving is already
    leaving the picture. The beat where a card would normally restate its caption
    in type does not do that here — the cropped planet carries it."""
    img = _cream_field(seed=1701, grain=False)
    img = _soft_wash(img,
                     [(150, 160), (620, 116), (1080, 170), (1214, 320),
                      (880, 388), (400, 376), (90, 262)],
                     (250, 246, 234), 200, seed=1702, wobble=16.0, blur=34)
    img = _ground_band(img, 556, seed=1703)
    d = ImageDraw.Draw(img)

    # the planet, cropped hard by the left edge, flat and banded
    img = _banded_giant(img, -70, 320, 226,
                        [(186, 200, 208), (154, 172, 182), (126, 146, 158),
                         (174, 190, 200), (140, 160, 172), (168, 184, 194)],
                        seed=1704)
    d = ImageDraw.Draw(img, 'RGBA')
    # three escape marks trailing off the frame to the left of the figure
    # Three escape streaks trailing off the planet's visible limb toward the
    # figure. These are SOFT WASHES (blurred flat fills) rather than strokes: a
    # shallow curve stroked with draw.line(joint='curve') combs into a visible
    # ladder where each short segment's body and its round joint overlap, which
    # is exactly how an escaping-atmosphere streak must NOT look. A soft flat
    # fill reads as moving air and is register-legal.
    for k, (y, ln, a) in enumerate(((258, 320, 200), (330, 360, 165),
                                    (402, 300, 130))):
        spine = [(168 + i * (ln / 16.0),
                  y + 26 * math.sin(math.pi * i / 16.0) - 26 * i / 16.0)
                 for i in range(17)]
        band = spine + [(x + 6, yy + 16 - 12 * (i / 16.0))
                        for i, (x, yy) in enumerate(reversed(spine))]
        img = _soft_wash(img, band, TEAL, a, seed=1710 + k, wobble=5.0,
                         wavelength=150.0, blur=11)
    d = ImageDraw.Draw(img)

    d = ImageDraw.Draw(img)
    _hero(d, 'THROWING IT AWAY', 860, 168, INK, px=52, y_max=224, stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 13. leak_no_bottom — LOADED. VOID / bone. Character: shielding eyes, awed.
# ---------------------------------------------------------------------------

def render_leak_no_bottom(card, planet="WASP-127b"):
    """B13 LOADED. The sky has nothing left in it - but the FRAME still has to be
    full. So the emptiness is in the AIR, not in the picture: a wide planet LIMB
    arcs across the bottom third (the surface the leak is escaping from, and the
    frame's bottom mass), the character is grounded at the left shading his eyes
    and looking off-frame right, and ONE thick leak-line falls down the right into
    that limb.

    G1 - ink_fraction was 0.140 and v_centroid 0.179, i.e. the frame was both
    too empty and top-heavy. The limb arc across the lower third plus a ground
    line for the figure puts the mass in the lower two-thirds and fills the
    picture. G7 - the figure is planted on the limb's top edge and is drawn last
    (in _finish), so no foreground shape occludes him.

    Void register: theme='dark', cream figure on black. The leak is a flat bone
    band, no gradient and no glow."""
    img = _void_field(seed=1801, stars=104)
    d = ImageDraw.Draw(img, 'RGBA')

    # G1 - the limb: a broad flat body filling the bottom of the frame, painted as
    # a soft wash so its top edge never shows a square corner.
    img = _soft_wash(img,
                     [(0, 648), (320, 604), (668, 632), (990, 600),
                      (1280, 636), (1280, 720), (0, 720)],
                     (44, 54, 72), 240, seed=1802, wobble=15.0, blur=24)
    d = ImageDraw.Draw(img, 'RGBA')
    # the limb's lit upper edge, a wobbled arc right across the frame
    edge = [(x, 640 - 30 * math.sin(math.pi * x / 1280.0))
            for x in range(0, 1281, 40)]
    _open_curve(d, edge, BONE + (155,), width=K.OUTLINE, seed=1803, wobble=1.8,
                wavelength=400.0)

    # G7 - the figure is planted on the limb's top edge; _finish draws him after
    # this, so his feet land ON the surface and nothing occludes him.
    _ground_figure(img, card, 626, dark_bg=True, width=5, seed=1804)

    d = ImageDraw.Draw(img, 'RGBA')
    # The leak: one long thick bone trickle down the right third that does not
    # stop inside the frame - it falls INTO the limb. Densely sampled with the
    # wobble nearly off: a leak is a steady fall, not a lightning bolt. Faint
    # dashes beside it mark where the air has already gone.
    spine = [(1020 + 16 * math.sin(i * 0.5) + 6 * math.sin(i * 0.21 + 1.0),
              92 + i * 42) for i in range(14)]
    _thick_curve(d, spine, BONE + (205,), seed=1810, width=12, wobble=0.5,
                 wavelength=520.0)
    for k, y in enumerate((216, 330, 444, 556)):
        _vline(d, 1064 + (k % 2) * 28, y, y + 44, BONE + (88,), width=K.DETAIL,
               seed=1820 + k, wobble=1.0)
    # the escape end, off the top
    for k in range(3):
        _thick_curve(d, [(1016 - k * 26, 100), (996 - k * 26, 56)],
                     BONE + (int(170 - k * 40),), seed=1830 + k, width=8,
                     wobble=1.0, wavelength=60.0)

    d = ImageDraw.Draw(img)
    # The word sits in the open sky BETWEEN the character and the leak, at the
    # foot of the leak so the two read as one object rather than two.
    _hero(d, 'NO BOTTOM', 700, 520, BONE, px=52, y_max=548)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 14. too_far_to_help — CLOSE. CREAM / amber. No character.
# ---------------------------------------------------------------------------

def render_too_far_to_help(card, planet="WASP-127b"):
    """B14 CLOSE. The closing card: the planet is far away and useless, but the
    FRAME is full. The scale argument is now made by DISTANCE, drawn as measured:
    a real, large flat planet set low-right, a big hand-drawn orbit circle around
    it, a tick-scaled range bar running out to the frame edge, and one long arrow
    that overshoots everything - the overshoot IS "too far to help".

    G1 - ink_fraction was 0.058 (a near-empty field); v_centroid was 0.526. The
    planet is scaled up (r 34 -> 120) and sunk into the lower-right, a 250px
    orbit circle and a full-width range scale are inked, so the subject fills a
    real share of frame width and the mass sits in the lower two-thirds. The
    labels go through lib.labels (G4/G5) so nothing clips at the edge."""
    img = _cream_field(seed=1901)
    d = ImageDraw.Draw(img)

    # G1 - a low wash so the field is composed, not dead.
    img = _soft_wash(img,
                     [(120, 470), (520, 420), (980, 460), (1230, 540),
                      (900, 640), (300, 620)],
                     (222, 216, 198), 120, seed=1902, wobble=14.0, blur=30)
    d = ImageDraw.Draw(img)

    # The one circle: a real orbit ring, still a hand-drawn wobble but now big
    # enough to be a shape. Densely sampled (128 pts) and modulated only by
    # LOW-order radial harmonics - canon wants LOW-frequency wobble; high
    # harmonics at low sample counts read as spikes, not as a hand.
    pcx, pcy, pr = 880, 430, 118
    pts = []
    for i in range(129):
        a = math.tau * i / 128.0
        rad = 250.0 + 14.0 * math.sin(2 * a + 0.7) + 8.0 * math.sin(3 * a)
        pts.append((pcx + rad * math.cos(a), pcy + rad * math.sin(a) * 0.94))
    _open_curve(d, pts, INK, width=K.FINE, seed=1910, wobble=1.4,
                wavelength=520.0)

    # the planet: scaled up, flat, banded, 6px keyline
    img = _banded_giant(img, pcx, pcy, pr,
                        [(198, 208, 212), (166, 180, 188), (138, 156, 166),
                         (186, 196, 202), (150, 166, 174)],
                        seed=1911, width=K.OUTLINE)

    d = ImageDraw.Draw(img)

    # G2 - a tick-scaled range bar running from the star-side out past the frame
    # edge, plus an overshooting arrow: the cue that makes this a diagram of
    # DISTANCE rather than a lone object in a field.
    _hrule(d, 596, 70, 1230, INK, width=K.DETAIL, seed=1912, wobble=1.4)
    for k in range(9):
        tx = 96 + k * 132
        _vline(d, tx, 596, 596 + (34 if k % 2 == 0 else 20), INK,
               width=K.DETAIL, seed=1913 + k, wobble=1.0)
    # the overshooting arrow: from inside the orbit out past the frame
    _arrow(d, 640, 596, 1252, 596, INK, width=K.OUTLINE, seed=1914, head=40)

    d = ImageDraw.Draw(img)
    # G4/G5 - the two range labels placed clear of the shapes and edges.
    _label(img, 'HERE', (pcx, pcy), prefer='left', avoid=(pcx, pcy, pr + 18),
           dark=INK, light=PAPER, px=20, seed=1915)
    _label(img, 'TOO FAR', (1252, 596), prefer='above', dark=INK, light=PAPER,
           px=20, seed=1916)
    _hero(d, 'TOO FAR TO HELP', 470, 578, INK, px=54, y_max=606, stroke=0)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Dispatch. RENDERERS is the load-bearing module attribute: the frame generator
# reads it directly and does C.register(_cards.RENDERERS).
# ---------------------------------------------------------------------------

RENDERERS = {
    'hurricane_forget_it': render_hurricane_forget_it,
    'name_the_planet': render_name_the_planet,
    'fastest_winds': render_fastest_winds,
    'never_land': render_never_land,
    'almost_empty': render_almost_empty,
    'nothing_inside': render_nothing_inside,
    'read_the_star': render_read_the_star,
    'swallowed_colors': render_swallowed_colors,
    'missing_tells_you': render_missing_tells_you,
    'water_leaving': render_water_leaving,
    'grains_high_above': render_grains_high_above,
    'throwing_its_away': render_throwing_its_away,
    'leak_no_bottom': render_leak_no_bottom,
    'too_far_to_help': render_too_far_to_help,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table."""
    C.register(RENDERERS if mapping is None else mapping)
    return RENDERERS


# ---------------------------------------------------------------------------
# Self-test. Renders one beat_<NN>.png per beat with a MINIMAL card dict — a
# short generic caption (never a narration line) and, where the script says the
# character appears, a default pose/expression at a workable position. Runs with
#   python wasp127b/_cards.py
# ---------------------------------------------------------------------------

# (pose, expression, x_center, y_top, height) per beat. None = no character.
# Chosen to match the script's 'visual' brief for each beat; positions keep the
# figure clear of the card's focal object and of the title strip / caption.
SELFTEST_STICKMEN = {
    'hurricane_forget_it': ('standing', 'flat', 330, 210, 430),
    'fastest_winds':       ('pointing', 'oval', 300, 200, 440),
    'nothing_inside':      ('shrugged', 'zigzag', 430, 258, 300),
    'swallowed_colors':    ('pointing', 'flat', 1050, 236, 340),
    'throwing_its_away':   ('hands_up', 'frown', 700, 262, 300),
    'leak_no_bottom':      ('shielding_eyes', 'oval', 300, 300, 300),
}

# A short generic caption for the contact sheet. Deliberately NOT the
# narration: the renderers must never print a narration line, and the sheet is
# only checking that the caption helper is wired.
SELFTEST_CAPTION = 'WASP-127B'


def _selftest(out_dir=None):
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = out_dir or os.path.join(here, 'cardsheet')
    os.makedirs(out_dir, exist_ok=True)
    for n, (cid, fn) in enumerate(
            [(cid, RENDERERS[cid]) for cid in _BEAT_ORDER], start=1):
        sm = SELFTEST_STICKMEN.get(cid)
        card = {
            'id': cid,
            'caption': SELFTEST_CAPTION,
            'stickman': ({'expression': sm[1], 'pose': sm[0],
                          'x_center': sm[2], 'y_top': sm[3], 'height': sm[4]}
                         if sm else None),
        }
        img = fn(card, 'WASP-127b')
        assert isinstance(img, Image.Image), cid
        assert img.size == (W, H), '%s returned %s' % (cid, img.size)
        assert img.mode == 'RGB', '%s returned mode %s' % (cid, img.mode)
        path = os.path.join(out_dir, 'beat_%02d.png' % n)
        img.save(path)
        print('beat %02d  %-22s %s' % (n, cid, os.path.basename(path)))
    print('OK  %d beats rendered to %s' % (len(_BEAT_ORDER), out_dir))
    return 0


# The script.json beat order. Kept as data so the sheet is numbered the way the
# narration runs, not alphabetically.
_BEAT_ORDER = [
    'hurricane_forget_it', 'name_the_planet', 'fastest_winds', 'never_land',
    'almost_empty', 'nothing_inside', 'read_the_star', 'swallowed_colors',
    'missing_tells_you', 'water_leaving', 'grains_high_above',
    'throwing_its_away', 'leak_no_bottom', 'too_far_to_help',
]

assert sorted(_BEAT_ORDER) == sorted(RENDERERS), \
    'RENDERERS must cover exactly the script beats'


if __name__ == '__main__':
    sys.exit(_selftest())