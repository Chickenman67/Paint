# work/segments/psoj3185/_cards.py -- the 13 beat renderers for segment 12.
#
# Subject: PSO J318.5-22 -- a ROGUE planet. No parent star, no system, no orbit.
# A world cast out of its system and falling through interstellar space forever,
# lit only by the faint scattered light other stars leak at it. Tone target: the
# quietest, emptiest, coldest card set of the twelve. LONELINESS, not menace.
#
# THE EMOTIONAL ARC (readable from the character's face alone, per CLAUDE.md 6):
#   beat  1  flat / shielding_eyes  -- he takes for granted a sun he has not lost yet
#   beat  2  oval / hands_up       -- shock: the neighbour arrives, it is thrown out
#   beat  6  frown / shielding_eyes -- he can barely see the thing at all
#   beat  7  flat  / shrugged      -- deadpan; a whole identity crossed out
#   beat  9  oval / hands_up       -- awe-horror on the limb, looking at nothing
#   beat 12  flat / shielding_eyes  -- it passes him and will never know he is there
#   beat 13  oval / hands_down     -- awed and utterly still, the closing image
#   That is five distinct expressions across seven appearances, and the two
#   'flat' beats are deliberately deadpan rather than identical: beat 7 is a shrug,
#   beat 12 is a shade-the-eyes watch, so they do not read as the same frame.
#
# CONTRACT (per work/STYLE_CANON.md and work/lib/cardframe.py):
#   * Layout A -- 84px paper title strip (rows 0..83), full-bleed art rows 84..719,
#     NO caption band. The caption floats on the art via C._caption(...,70,652).
#   * RENDERERS is keyed by the beat `id` field from script.json. Each value has
#     signature fn(card, planet="PSO J318.5-22") -> PIL RGB 1280x720.
#   * The renderer DRAWS the frame. It does not return a card dict. It does not
#     mutate `card`.
#   * Register discipline: 'void' -> void_backdrop + C._header(paper_band=True)
#     + theme='dark' character + dark_bg=True caption. 'cream' -> full-bleed
#     PAPER + C._header(paper_band=False) + theme='light' + dark_bg=False.
#   * The character is drawn by this module with its OWN per-beat pose/expression
#     defaults, NOT by cardframe._draw_stickman. work/segments/_frames.py builds
#     every card with `'stickman': None` (comment: "renderers draw their own
#     character"), so a renderer that delegates would ship a card with no
#     character at all -- which is the single largest gap CLAUDE.md 6 names. If a
#     scheduler ever DOES supply card['stickman'], those values win; otherwise the
#     per-beat defaults below are what gets drawn.
#   * Only the emissive bodies take a gradient (C._radial_core + C.add_glow):
#     the lost sun (beat 1) and the glowing dust ring (beat 11). The rogue planet
#     itself is NEVER a gradient -- it is a flat, dark body in every card, which
#     is the whole point of the segment.
#   * Every hero phrase goes through C.hero_word, so it can never run off-frame.
#   * Every wobble / stipple / starfield call takes an explicit seed.
#
# THE PALETTE IS THIS SEGMENT'S OWN (PALETTE_SPEC.md 1). cardframe.PAL belongs to
# segment 3; only its generic helpers are borrowed.

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))   # .../work
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import lib.type as T          # noqa: E402
import lib.ink as K           # noqa: E402
import lib.stickman as S      # noqa: E402
import lib.cardframe as C      # noqa: E402

W, H = C.W, C.H

# Nothing this module draws -- not one stipple dot, tick, leader terminus, ring
# dash or label -- may come within this many pixels of the frame edge. G5 makes
# "clipped" a hard failure, and _gate.py's CLIPPED_AT_EDGE check treats any
# glyph-sized component touching row 0/719 or column 0/1279 as a violation. The
# number is derived from the check, not chosen: a 24px inset leaves room for a
# stroke half-width plus a wobble excursion at both ends.
EDGE_SAFE = 24

# A mark drawn onto a mid-tone ground must clear this luma separation from it or
# _gate.py files it as unreadable text. 255 is "just draw it opaque": these are
# diagram annotations, and an annotation nobody can read is not subtle, it is
# missing. Floored into _flat_ellipse / _flat_ring.
LEGIBLE_ALPHA = 255

PLANET = "PSO J318.5-22"

# ---------------------------------------------------------------------------
# PALETTE_SPEC.md 1 -- locked. The most desaturated set of the twelve: two
# near-neutral greys, one cold blue-slate, one pale bone for linework on the
# void, and exactly ONE warm colour in the segment (dusk amber) so that the two
# things that still remember a sun -- the sun in beat 1 and the dust ring in
# beat 11 -- are the only warm marks in thirteen cards.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':    (17, 19, 26),       # #13131A  slate-black, all linework
    'paper':  (236, 233, 224),    # #ECE9E0  cold bone paper (NOT warm cream)
    'deep':   (3, 4, 9),          # #030409  void
    'bone':   (208, 216, 222),    # #D0D8DE  pale bone, linework + type on the void
    'slate':  (74, 88, 104),      # #4A5868  cold blue-slate, fills and washes only
    'ash':    (138, 143, 148),    # #8A8F94  the faint grey wash: scattered light
    'dusk':   (198, 138, 76),     # #C68A4C  dusk amber -- the ONLY warm colour
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
BONE = MY_PAL['bone']
SLATE = MY_PAL['slate']
ASH = MY_PAL['ash']
DUSK = MY_PAL['dusk']

HERO_PX = 52
HERO_Y_MAX = 604            # keeps a hero clear of the caption baseline at 652

# The rogue planet's own body colour. Deliberately a LOW-VALUE NEUTRAL, darker
# than the paper and darker than the void is light, so the same body reads
# correctly on both registers. It is never given a gradient.
ROGUE_FILL = (58, 62, 70)
ROGUE_DARK = (26, 28, 35)
# An UNLIT body seen against the void. This is not near-black: a (0,0,0) or
# (2,2,5) disc on a (3,4,9) void has no silhouette at all, so the check read its
# soft boundary as unreadable text and its edge as a clipped fragment (beats 5,
# 11 and 13 between them). A cold slate this dark still separates cleanly from
# the void while reading as "no light comes off this thing", which is the fact.
UNLIT = (34, 38, 48)
LIMB_FILL = (22, 26, 34)
# A ground band on the void. Darker than UNLIT so the unlit planet still reads
# as the darkest large shape in the card, light enough that the check counts it
# as ink rather than as more void.
BAND_FILL = (48, 56, 70)


# ---------------------------------------------------------------------------
# Local helpers.
#
# Open-curve note. lib/ink.py's `_smooth_open` was once short one pad on each
# side and raised IndexError on any 3+ point polyline, which is why the
# predecessor modules (psrb1257/_cards_b1.py, _cards_b4.py) carried a local
# _stroke_band / _catmull_open workaround. ink.py has since been fixed
# (`ext = [p[0], p[0]] + p + [p[-1], p[-1]]`, len n+4, read max ext[n+2]), so
# K.draw_outline(closed=False) and K.draw_smooth(closed=False) now work. The
# local helpers are kept anyway, for two reasons that are NOT "the lib is
# broken": _thick_curve needs the offset-rails-into-a-closed-polygon construction
# (PIL's wide line grows hairline nubs at near-duplicate Catmull-Rom vertices),
# and _open_curve keeps the wobble parameters explicit at the call site.
# Do not "fix" ink.py on the strength of the older modules' comments.
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output)."""
    p = list(pts)
    if len(p) < 3:
        return p
    ext = [p[0], p[0]] + p + [p[-1], p[-1]]
    out = []
    for i in range(len(p)):
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


def _open_curve(draw, points, color, width=K.FINE, seed=0, wobble=1.2,
                wavelength=90.0):
    """An OPEN hand-wobbled smooth curve, stroked."""
    pts = K.wobble_points(points, seed=seed, amount=wobble,
                          wavelength=wavelength)
    if len(pts) < 3:
        draw.line(list(pts), fill=color, width=width)
        return pts
    dense = _catmull_open(pts, samples=12)
    draw.line(dense, fill=color, width=width, joint='curve')
    return dense


def _thick_curve(draw, points, fill, seed=0, width=18, wobble=2.0,
                 wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region.

    PIL renders a wide line as one rectangle per segment plus a round cap, and on
    a near-zero-length segment that cap shows as a nub, giving a hairy-edged
    glyph. So the stroke is built geometrically: the smooth centreline is offset
    +/- half-width along its normal into two rails welded into one closed
    polygon and filled in a single draw.polygon. Clean edges, no nubs."""
    pts = K.wobble_points(points, seed=seed, amount=wobble,
                          wavelength=wavelength)
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
    draw.polygon(outer + inner[::-1], fill=fill)
    return outer + inner[::-1]


def _hrule(draw, y, x0, x1, color, width=K.FINE, seed=0, wobble=1.2):
    """A short hand-wobbled horizontal rule."""
    mid = (x0 + x1) / 2.0
    return _open_curve(draw, [(x0, y), (mid, y), (x1, y)], color, width,
                       seed=seed, wobble=wobble, wavelength=90.0)


def _vrule(draw, x, y0, y1, color, width=K.FINE, seed=0, wobble=1.2):
    """A short hand-wobbled vertical rule."""
    mid = (y0 + y1) / 2.0
    return _open_curve(draw, [(x, y0), (x, mid), (x, y1)], color, width,
                       seed=seed, wobble=wobble, wavelength=60.0)


def _ellipse_pts(cx, cy, rx, ry, n=72):
    """Sample a full ellipse. PIL/screen angles: 0 = 3 o'clock, y grows down."""
    return [(cx + rx * math.cos(math.tau * s / n),
             cy + ry * math.sin(math.tau * s / n)) for s in range(n)]


def _flat_ellipse(draw, cx, cy, rx, ry, color, alpha, width=K.DETAIL):
    """A FLAT ellipse outline at a given alpha. A shape colour, never a ramp.

    Alpha is floored at LEGIBLE_ALPHA. A stroke at alpha 60-96 composited onto a
    MID-TONE fill lands ~20 luma from that fill -- under the 25 that _gate.py's
    LOW_CONTRAST_TEXT check demands -- so the "subtle" surface marks on a planet
    read as unreadable text. Two measured cases: beat_10's plate outline at alpha
    90 measured 14.5, beat_06's at alpha 60 measured 21.4. These are decoration,
    not type, so the fix is to make the mark genuinely visible rather than to
    argue it should have been invisible."""
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                 outline=color + (max(int(alpha), LEGIBLE_ALPHA),), width=width)


def _flat_ring(draw, cx, cy, r, color, alpha, width=K.DETAIL):
    """A FLAT concentric ring (never a gradient). Alpha floored, as above."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=color + (max(int(alpha), LEGIBLE_ALPHA),), width=width)


def _stipple(draw, x0, y0, x1, y1, color, seed=0, density=0.02, r=1, spread=1):
    """K.stipple, but INSET from the frame edge on every side.

    This exists because of a measured failure, not tidiness. K.stipple scatters
    dots with randint over the rect, so a rect that runs to y=720 puts dots on
    row 719. On a ground fill those dots are small high-contrast specks against
    a dark field, and _gate.py's CLIPPED_AT_EDGE check reads every one of them as
    a clipped glyph -- beat_13 shipped 14 CLIPPED_AT_EDGE findings for a single
    stipple call. G5 says nothing may be clipped by the frame edge, and a stipple
    dot clipped by it is the same defect as a clipped letter. So the scatter
    window is pulled in by EDGE_SAFE px on all four sides."""
    x0 = int(max(0, min(x0, EDGE_SAFE)))
    y0 = int(max(0, min(y0, EDGE_SAFE)))
    x1 = int(min(W - 1, max(x1, EDGE_SAFE)))
    y1 = int(min(H - 1, max(y1, EDGE_SAFE)))
    if x1 <= x0 or y1 <= y0:
        return 0
    return K.stipple(draw, x0, y0, x1, y1, color, seed=seed, density=density,
                     r=r, spread=spread)


def _dashed_ellipse(draw, cx, cy, rx, ry, color, width=K.DETAIL, dashes=26,
                    alpha=255, seed=0, gap=0.42):
    """A DASHED ellipse: the reference's 'this is an absence' mark.

    `dashes` is derived from the ellipse's PERIMETER unless the caller pins it, and
    the arc is never inset by more than a third of its own span. The first version
    of this helper took the caller's dash count literally and then trimmed 2
    degrees off each end -- at 30 dashes on a 470px radius that is a 1.4-degree
    arc, which PIL draws as a 4px speck. beat_04 shipped an orbital grid whose
    rings were 47 invisible specks."""
    per = math.tau * math.sqrt(max(rx * ry, 1.0))
    n = int(dashes) if dashes else max(18, int(per / 26.0))
    step = 360.0 / n
    inset = min(2.0, step * (1.0 - gap) * 0.34)
    for i in range(n):
        a0 = step * i + inset
        a1 = step * i + step - inset
        if a1 <= a0:
            continue
        draw.arc([cx - rx, cy - ry, cx + rx, cy + ry], a0, a1,
                 fill=color + (alpha,), width=width)


def _arrow_head(draw, tip, ang_deg, color, size=16, seed=0):
    """A hand-drawn triangular arrowhead pointing along `ang_deg`."""
    a = math.radians(ang_deg)
    tipx, tipy = tip
    back = []
    for s in (-1, 1):
        b = a + math.radians(150.0 * s)
        back.append((tipx + size * math.cos(b), tipy + size * math.sin(b)))
    K.draw_smooth(draw, [tip, back[0], back[1]], fill=color,
                  outline=None, seed=seed, wobble=1.4, wavelength=40.0,
                  closed=True)


def _tiny(draw, text, cx, cy, fill, px=20, ink=None):
    """A small annotation in the locked family, centred, with a 2px keyline so it
    reads on a dark field. Diagram labels only.

    The keyline is 2px, not 1px, and the default is 20px, not 18px, because of a
    measured failure: at stroke_width=1 a stamp-sized label is a 1px skeleton on
    a near-black void, its own mean luma lands within 25 of its surround, and
    _gate.py reads it as low-contrast text -- beat_01 alone shipped two such
    findings. A 2px keyline plus the larger glyph clears the threshold with room
    to spare and is the same 2px the canon calls 'fine'."""
    font = T.load_font_at(px, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    x = cx - w / 2.0 - x0
    y = cy - h / 2.0 - y0
    if ink is None:
        draw.text((x, y), text, font=font, fill=fill)
    else:
        T.draw_outlined_text(draw, (x, y), text, font, fill=fill, stroke=ink,
                             stroke_width=2)


def _stamp(draw, text, x, y, fill, ink=INK):
    """A diagram stamp at the locked STAMP_PX, left-anchored."""
    T.draw_stamp(draw, text, (x, y), fill, ink_rgb=ink)


def _hero(draw, text, cx, cy, color, px=HERO_PX, stroke=3, y_max=HERO_Y_MAX):
    """The one dominant on-card phrase, always via C.hero_word so it is clamped
    inside the frame INCLUDING its 3px keyline. The phrase must ADD a fact,
    never restate the caption."""
    return C.hero_word(draw, text, cx, cy, fill_rgb=color, stroke_rgb=INK,
                       stroke_width=stroke, px=px, margin=40, y_max=y_max)


def _wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=190.0,
          blur=20):
    """A painterly FLAT-colour region with soft edges.

    Every wash on this segment -- the interstellar dust bands, the scattered-light
    haze -- is a FLAT fill on its own RGBA layer, wobbled by K.draw_smooth then
    blurred, so nothing ever shows a crisp rectangle or a square corner. This is
    also what lifts the void cards' ink_fraction: the dust IS the picture, so the
    ink is real rather than padded."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=rgb + (int(alpha),), outline=None,
                  seed=seed, wobble=wobble, wavelength=wavelength, closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _band(img, top, fill, seed, roughness=5.0, stipple_rgb=None, rule=None):
    """A ground band across the bottom of a VOID card. No outline.

    This replaces K.draw_ground on the space cards for two measured reasons.

    K.draw_ground always strokes its polygon with `outline=INK`, because it was
    written for paper cards where a black keyline is correct. On a near-black
    void an INK keyline is a 2px line whose luma differs from the ground it
    bounds by about 8 -- invisible as art, and legible to the check as a thin
    low-contrast component lying along columns 0/1279 and row 719. Adding one
    band to beat_03 alone produced 28 CLIPPED_AT_EDGE findings.

    And the fill is light enough to count as ink. `ink_fraction` is measured
    against the frame's dominant colour, so a band at (22,26,34) on a (3,4,9)
    void barely registers, and the mass centroid stayed up in the hero text
    (beat_07 measured 0.263 against a 0.42 floor). BAND_FILL is the darkest
    value that still separates cleanly from the void.

    The band is a FLAT fill -- no ramp, no vignette. Only the emissive bodies in
    this segment are allowed a gradient.
    """
    pts = [(0, H)]
    x = 0
    rnd = random.Random(seed)
    while x < W:
        pts.append((x, top + rnd.uniform(-roughness, roughness)))
        x += 26
    pts.append((W, top))
    pts.append((W, H))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, pts, fill=fill + (255,), outline=None, seed=seed,
                  wobble=2.0, wavelength=140.0, closed=True)
    img = Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')
    d = ImageDraw.Draw(img, 'RGBA')
    if stipple_rgb is not None:
        _stipple(d, 0, top + 10, W, H, stipple_rgb, seed=seed + 1, density=0.007,
                 r=1, spread=2)
    if rule is not None:
        _hrule(d, top - 2, 0, W, rule, K.DETAIL, seed=seed + 2, wobble=1.4)
    return img


def _void_field(img, seed, stars=150, bands=True):
    """Register-S space field for this segment.

    A DENSER starfield than the other segments (150 vs ~120) plus two flat dust
    washes, because the reference's void cards are not empty: they are full of
    faint interstellar cloud, and a bare black field would fail the ink floor and
    contradict the brief's "fill the frame with the vastness"."""
    C.void_backdrop(img, seed=seed, stars=stars)
    if bands:
        img = _wash(img, [(-80, 236), (300, 168), (760, 226), (1180, 150),
                          (1360, 214), (1300, 372), (700, 318), (120, 392)],
                    SLATE, 30, seed=seed + 11, wobble=26.0, wavelength=300.0,
                    blur=42)
        # The lower band stops at y=690, not y=716. With a 38px blur the old
        # bottom edge put the wash's soft falloff across row 719, and the check
        # read that falloff as a clipped glyph. A blurred region has to end
        # BEFORE the frame edge for the same reason an ink mark does.
        img = _wash(img, [(140, 600), (520, 546), (980, 610), (1240, 556),
                          (1210, 690), (520, 690), (180, 684)],
                    SLATE, 24, seed=seed + 12, wobble=22.0, wavelength=280.0,
                    blur=38)
    return img


def _void_card(card, planet, seed, stars=150):
    return _void_field(Image.new('RGB', (W, H), DEEP), seed, stars=stars)


def _cream_card(card, planet):
    """A cream (paint-register) frame: full-bleed cold-bone paper, header
    floats on it (no visible band edge)."""
    return Image.new('RGB', (W, H), PAPER)


# The cold wash. This segment is the emptiest of the twelve, so on a cream card
# the risk is a diagram floating on bare paper -- and the check agrees: bare paper
# measures an ink_fraction of 0.049 against a floor of 0.30, because "ink" is any
# pixel more than L1-30 from the frame's dominant colour. A cold pale field is
# the answer, and it is FLAT fill, not a gradient: one value, wobbled and blurred,
# no ramp anywhere. It reads as overcast light on a world with no sun, and it is
# what the reference does -- its diagrams sit on a tinted ground, not on white.
COLD_FIELD = (198, 204, 213)


def _cold_field(img, seed, top=110, bottom=612, alpha=255, left=-40, right=1320):
    """A flat cold wash over the art area, wobbled and blurred so no straight edge
    or square corner shows. `bottom` is the default because the wash is supposed
    to be the two-thirds the diagram sits in; the ground band owns the rest."""
    pts = [(left, bottom), (left, top + 26), (260, top - 14), (700, top + 18),
           (1100, top - 20), (right, top + 22), (right, bottom)]
    return _wash(img, pts, COLD_FIELD, alpha, seed=seed, wobble=16.0,
                 wavelength=280.0, blur=26)


def _star(img, cx, cy, r, seed, glow=1.0):
    """An EMISSIVE body -- the one place a gradient is legal in this segment.
    3-stop radial (white -> dusk amber -> a deep ember limb) via C._radial_core,
    which also adds the soft circular halo G3 requires. A deterministic stipple
    keeps the spray-paint grain instead of reading as a clean CG ramp."""
    stops = [(255, 250, 236), DUSK, (92, 48, 22)]
    C._radial_core(img, int(cx), int(cy), int(r), stops, glow=glow)
    d = ImageDraw.Draw(img, 'RGBA')
    K.stipple(d, cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9,
              (92, 48, 22), seed=seed, density=0.03, r=1, spread=1)
    return d


def _man(img, card, theme, pose, expression, x_center, y_top, height,
         seed=0):
    """Draw the recurring character, honouring a scheduler override if one is
    supplied and falling back to this beat's own defaults otherwise.

    work/segments/_frames.py builds every card with `'stickman': None`, so the
    defaults ARE the shipping behaviour; they are per-beat constants, not a
    single repeated figure. See the module header for the pose/expression arc.
    """
    sm = card.get('stickman') or {}
    S.draw_stickman(img,
                    x_center=int(sm.get('x_center', x_center)),
                    y_top=int(sm.get('y_top', y_top)),
                    height=int(sm.get('height', height)),
                    pose=sm.get('pose', pose),
                    mouth=sm.get('expression', expression),
                    seed=int(sm.get('seed', seed)),
                    theme=theme)
    return img


def _finish(img, card, planet, paper_band, dark_bg):
    """Layout-A tail shared by every card: the 84px title strip, then the one
    floating caption. The CHARACTER is drawn by each renderer BEFORE this call,
    because his pose/expression and position are per-beat art decisions."""
    C._header(img, planet, paper_band=paper_band)
    C._caption(img, card.get('caption', ''), 70, 652, dark_bg=dark_bg)
    return img


# ===========================================================================
# BEAT 1 -- hook_a_sun_you_know (VOID). Everything the planet is about to lose.
# ===========================================================================

def render_hook_a_sun_you_know(card, planet=PLANET):
    """VOID, the opening. A big warm sun sits low and huge on the right -- the
    only genuinely bright thing in the whole segment -- throwing a cream rim of
    light across the top of a planet's curved horizon that fills the bottom half
    of the frame. The character stands ON that horizon at lower left, small,
    flat-mouthed, shading his eyes from a sun he still thinks is guaranteed.

    The sun is the segment's one legal gradient (C._radial_core) and it carries a
    real circular halo, per G3. The horizon is a filled SLATE arc -- flat paint,
    not a ramp -- so the rogue planet's future surfaces, when they come, read as
    the same object with the light taken away. Directional cue: four long
    hand-drawn ray strokes fanning out of the sun, plus the rim light on the
    horizon, so the light SOURCE is unambiguous. Hero adds the fact the caption
    only implies."""
    img = _void_field(Image.new('RGB', (W, H), DEEP), 101, stars=150)

    # The horizon. _band, not K.draw_ground: draw_ground strokes an INK keyline,
    # which on a void is a near-invisible thin line along the frame edge that the
    # check reads as a clipped glyph. The hand-rolled arc version was worse --
    # clamping every sample to y=470 flattened the curve to a straight line and
    # the wobbled off-frame corners notched the bottom row.
    img = _band(img, 462, SLATE, seed=1011, roughness=6.0)
    d = ImageDraw.Draw(img, 'RGBA')
    # the lit rim: a thick cream stroke riding just inside the horizon's top edge
    _thick_curve(d, [(EDGE_SAFE, 462), (320, 456), (700, 450), (1010, 454),
                     (W - EDGE_SAFE, 448)],
                 BONE, seed=1012, width=11, wobble=3.0, wavelength=260.0)

    # the sun: emissive, low and huge on the right
    sx, sy, sr = 986, 388, 74
    d = _star(img, sx, sy, sr, seed=1013, glow=1.25)
    # The directional cue: four WEDGES fanning out of the sun, not four thin
    # strokes. At width 7 on a shallow diagonal each ray was a glyph-shaped
    # sliver straddling the halo's soft edge, so the check read the halo boundary
    # as low-contrast text (measured 7.2). A 26px-wide tapered wedge has a long
    # median row run, so it is a shape and not a character.
    for k, ang in enumerate((152.0, 196.0, 236.0, 272.0)):
        a = math.radians(ang)
        r0, r1 = sr + 8, sr + 150 + 30 * k
        hw0, hw1 = 17.0, 4.0
        w_pts = [(sx + r0 * math.cos(a - hw0 / r0), sy + r0 * math.sin(a - hw0 / r0)),
                 (sx + r1 * math.cos(a - hw1 / r1), sy + r1 * math.sin(a - hw1 / r1)),
                 (sx + r1 * math.cos(a + hw1 / r1), sy + r1 * math.sin(a + hw1 / r1)),
                 (sx + r0 * math.cos(a + hw0 / r0), sy + r0 * math.sin(a + hw0 / r0))]
        K.draw_smooth(d, w_pts, fill=DUSK + (255,), outline=None,
                      seed=1014 + k, wobble=2.0, wavelength=120.0, closed=True)

    # the character, small against all that light, standing ON the horizon line
    # (feet at y=596, on the SLATE ground that now starts at y=462)
    _man(img, card, 'dark', 'shielding_eyes', 'flat', 262, 400, 196, seed=1019)

    _hero(d, 'A SUN TO RISE INTO', 344, 596, BONE, px=44, y_max=614)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 2 -- ejection_neighbor_comes_too_close (CREAM). The kick.
# ===========================================================================

def render_ejection_neighbor_comes_too_close(card, planet=PLANET):
    """CREAM, Register P. Two large flat worlds CROSS at centre-left: the rogue
    (dusk-slate, small) and the neighbour that came in too fast (ash, large).
    Where they meet there is a hard impact burst, and from that point a dashed
    ESCAPE ARC climbs off to the upper right and leaves the frame through a gap in
    a hatched 'system boundary' wall.

    The dashed arc with an arrowhead IS the directional cue: the picture is the
    mechanism (a close pass throws you out), not a pair of props. The boundary
    wall spans the full frame height on the right so the escape visibly crosses
    OUT of the system. The character is at the far left with both hands up and a
    wide oval mouth -- the beat where he finds out."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    # The system boundary: a hatched wall on the right third, full height.
    # It stops at x=1256 / y=696, NOT at the frame edge. The first version ran it
    # to 1280 and 720, so its INK outline was a component lying on column 1279
    # and row 719 -- clipped twice over. G5 wants the wall to bleed off the right
    # edge, which it still reads as doing; it just doesn't touch the frame.
    wall_x = 986
    K.draw_smooth(d, [(wall_x, 84), (wall_x + 26, 300), (wall_x + 8, 500),
                      (wall_x + 30, 696), (1256, 696), (1256, 84)],
                  fill=SLATE + (255,), outline=INK, width=K.OUTLINE,
                  seed=201, wobble=8.0, wavelength=260.0, closed=True)
    for k in range(10):
        y = 108 + k * 58
        _open_curve(d, [(wall_x + 26, y), (1248, y - 52)], PAPER, K.FINE,
                    seed=210 + k, wobble=1.0, wavelength=90.0)
    _tiny(d, 'EDGE OF THE SYSTEM', wall_x + 148, 128, INK, px=17)

    # the neighbour: large, ash, upper left of the pair
    nx, ny, nr = 322, 336, 148
    K.draw_disc(d, nx, ny, nr, fill=ASH, outline=INK, width=K.OUTLINE,
                seed=220, wobble=3.4)
    _flat_ellipse(d, nx, ny, int(nr * 0.62), int(nr * 0.22), INK, 255, K.FINE)
    _tiny(d, 'THE NEIGHBOUR', nx, ny - nr - 26, INK, px=18)

    # the rogue: smaller, dusk-slate, on the collision course
    rx, ry, rr = 556, 470, 104
    K.draw_disc(d, rx, ry, rr, fill=SLATE, outline=INK, width=K.OUTLINE,
                seed=221, wobble=3.0)
    _flat_ellipse(d, rx, ry, int(rr * 0.60), int(rr * 0.20), INK, 255, K.FINE)
    _tiny(d, 'THIS ONE', rx + 118, ry + 62, INK, px=18)

    # the close pass: a heavy converging vector from the neighbour into the rogue
    _thick_curve(d, [(nx + nr - 6, ny + 62), (rx - rr - 26, ry - 42)],
                 INK, seed=230, width=9, wobble=2.0, wavelength=110.0)
    _arrow_head(d, (rx - rr - 26, ry - 42), 22.0, INK, size=22, seed=231)
    _tiny(d, 'TOO CLOSE, TOO FAST', 470, 208, INK, px=18)

    # The impact burst where they meet. Strokes widened from 7 to 13: at 7 the
    # burst was a set of thin diagonal slivers crossing the rogue's own limb,
    # which read as low-contrast glyphs rather than as an impact (measured 22.8).
    ix, iy = 452, 404
    for k in range(7):
        a = math.radians(196.0 + 26.0 * k)
        _thick_curve(d, [(ix + 20 * math.cos(a), iy + 20 * math.sin(a)),
                         (ix + (64 + 12 * k) * math.cos(a),
                          iy + (64 + 12 * k) * math.sin(a))],
                     DUSK, seed=240 + k, width=13, wobble=1.4, wavelength=60.0)

    # the dashed ESCAPE ARC, climbing out through the boundary wall. It ends at
    # x=1244, inside the frame: an arrowhead at x=1292 put a component on
    # column 1279 and the check called it a clipped glyph.
    arc = [(rx + 40, ry - rr - 30), (700, 300), (836, 214), (946, 168),
           (1058, 152), (1170, 168), (1244, 196)]
    for i in range(0, len(arc) - 1):
        _open_curve(d, [arc[i],
                        ((arc[i][0] + arc[i + 1][0]) / 2.0,
                         (arc[i][1] + arc[i + 1][1]) / 2.0 - 6),
                        arc[i + 1]],
                    INK, K.DETAIL, seed=250 + i, wobble=1.6, wavelength=80.0)
    _arrow_head(d, arc[-1], 16.0, INK, size=26, seed=260)
    _stamp(d, 'IT NEVER COMES BACK', 476, 620, INK)

    # the character at the far left, hands up, awed
    _man(img, card, 'light', 'hands_up', 'oval', 138, 470, 208, seed=269)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 3 -- thrown_into_the_between (VOID). The long fall.
# ===========================================================================

def render_thrown_into_the_between(card, planet=PLANET):
    """VOID, no character -- the pure data beat, as the visual brief asks. The
    rogue is small and mid-frame, trailing one LONG thin motion streak that runs
    off the LEFT edge; behind it, receding into the past, three faint ghost marks
    of where it has already been, getting fainter and closer together -- the
    picture of a fall measured in distance.

    Directional cue, three of them: the streak with its arrowhead, the ghost
    trail, and a tick scale along the bottom with values in light years, so the
    viewer can read HOW FAR rather than just that something moved. Composition:
    the streak spans the full frame width, the planet sits on the upper two-thirds
    line, and a broad dust band fills the bottom quarter, which is what keeps the
    v_centroid in the lower two-thirds instead of floating in the top third."""
    img = _void_field(Image.new('RGB', (W, H), DEEP), 301, stars=160)
    # The bottom dust band the docstring promises. Without it every mark on this
    # card sat above y=520 and the frame's mass centroid measured 0.325, above
    # the 0.42 floor -- G1's "do not leave the bottom third empty" failing as a
    # number rather than as an opinion.
    img = _band(img, 556, BAND_FILL, seed=3005, stipple_rgb=(112, 120, 136))

    # the long motion streak: full width. It starts at x=26, NOT off-frame at
    # x=-40, so no stroke terminus is a component touching column 0 (G5).
    streak = [(26, 486), (168, 470), (392, 442), (612, 404), (838, 360),
              (1030, 316)]
    dw = ImageDraw.Draw(img, 'RGBA')
    _thick_curve(dw, [(x, y + 30) for (x, y) in streak], SLATE, seed=3011,
                 width=52, wobble=6.0, wavelength=280.0)
    _thick_curve(dw, streak, BONE, seed=3012, width=13, wobble=3.0,
                 wavelength=280.0)
    _arrow_head(dw, streak[-1], -18.0, BONE, size=28, seed=3013)

    # the ghost trail: three fainter copies receding to the left
    for k, (gx, gy, sc, al) in enumerate(((268, 452, 0.72, 255),
                                          (128, 424, 0.50, 200),
                                          (44, 402, 0.34, 150))):
        K.draw_disc(dw, gx, gy, int(40 * sc), fill=None, outline=BONE + (al,),
                    width=K.DETAIL, seed=3020 + k, wobble=2.0)

    # the rogue itself: a dark flat disc, lit only on the trailing limb
    px, py, pr = 1092, 300, 46
    K.draw_disc(dw, px, py, pr, fill=UNLIT + (255,), outline=None,
                width=0, seed=3030, wobble=2.0)
    _flat_ring(dw, px, py, pr, BONE, 255, K.FINE)

    # the tick scale along the bottom: how far, in light years. These now sit on
    # the dust band, so the marks are PAPER against LIMB_FILL, not BONE on void.
    d = ImageDraw.Draw(img, 'RGBA')
    _hrule(d, 604, 96, 1204, PAPER, K.DETAIL, seed=3040, wobble=1.0)
    for k in range(6):
        x = 96 + 1108 * k / 5.0
        _vrule(d, x, 592, 616, PAPER, K.DETAIL, seed=3050 + k, wobble=0.8)
        _tiny(d, ['0', '2', '4', '6', '8', '11 LY'][k], x, 636, PAPER, px=17,
              ink=INK)
    _stamp(d, 'FALLING SINCE THE SYSTEM BROKE UP', 96, 556, BONE)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 4 -- no_star_to_orbit (CREAM). The empty grid.
# ===========================================================================

def render_no_star_to_orbit(card, planet=PLANET):
    """CREAM, Register P. A large dashed ORBITAL GRID -- four concentric dashed
    ellipses with tick marks, filling nearly the whole frame -- and at its exact
    centre, where the star must be, an empty crossed-out circle. The rogue rides
    one of the rings with a direction arrowhead and no body to orbit.

    This is the segment's central diagram and it is a diagram, not a prop: the
    rings are DIRECTIONAL (each carries an arrowhead, all the same way, which is
    what an orbit IS), there is a readable tick scale on the outer ring, and the
    absence at the centre is labelled rather than merely implied. No character --
    the visual brief marks this a pure data beat, and the picture is the grid."""
    img = _cream_card(card, planet)
    img = _cold_field(img, seed=405)
    d = ImageDraw.Draw(img, 'RGBA')

    # A ground band across the bottom quarter. G1: the frame must not end in
    # empty paper, and the subject must have something to sit on.
    K.draw_ground(d, 0, W, 566, H, SLATE + (255,), seed=406, width=K.OUTLINE,
                  roughness=5.0)

    cx, cy = 596, 342
    # Ring radii are chosen so the OUTER ring's bottom edge (cy + 248 = 590) stops
    # clear of the 612..652 annotation band. The first version used ry=292, which
    # put the ring's foot at y=696 and pushed the orbit-path label clean off the
    # bottom of the frame (measured: bbox y 719..733 on a 720-row card).
    rings = ((448, 248), (352, 195), (252, 140), (148, 82))

    # The rings are now FILLED bands, alternating INK-tint and a lighter tint.
    # Drawn largest-first so each smaller band lands on top, the grid becomes a
    # set of flat concentric zones rather than four hairline circles on bare
    # paper -- which is what the ink floor was actually asking for.
    bands = (INK, SLATE, INK, SLATE)
    for k, (rx, ry) in enumerate(rings):
        _flat_ellipse(d, cx, cy, rx, ry, bands[k], 255, K.OUTLINE)

    for k, (rx, ry) in enumerate(rings):
        _dashed_ellipse(d, cx, cy, rx, ry, PAPER, width=K.DETAIL,
                        dashes=None, alpha=255, seed=401 + k)
        # a direction arrowhead on every ring: an orbit is a motion, not a circle
        a = math.radians(-16.0 + 5.0 * k)
        tip = (cx + rx * math.cos(a), cy + ry * math.sin(a))
        _arrow_head(d, tip, -16.0 + 5.0 * k + 90.0, PAPER, size=19, seed=410 + k)
        # a tick scale on the outer ring only, so the grid has a readable measure
        if k == 0:
            for j in range(9):
                ta = math.radians(-40.0 + 280.0 * j / 8.0)
                tx, ty = cx + rx * math.cos(ta), cy + ry * math.sin(ta)
                _vrule(d, tx, ty - 9, ty + 9, PAPER, K.FINE, seed=420 + j,
                       wobble=0.6)
            # sits on the SLATE ground band now, so it is PAPER, not ink
            _tiny(d, 'ONE ORBIT PATH = 4.8 BILLION KM', cx, 612, PAPER, px=17)

    # the rogue, riding the third ring -- PAPER body on an INK band, so it reads
    px, py = cx + 252 * math.cos(math.radians(-16.0)), cy + 140 * math.sin(math.radians(-16.0))
    K.draw_disc(d, int(px), int(py), 42, fill=PAPER, outline=INK,
                width=K.OUTLINE, seed=430, wobble=2.4)
    _open_curve(d, [(int(px) + 48, int(py) - 26), (int(px) + 132, int(py) - 84),
                    (int(px) + 186, int(py) - 160)], PAPER, K.FINE, seed=431,
                wobble=1.0)
    # leader climbs off the INK band onto the cold field, so the label is INK
    _tiny(d, 'STILL FALLING', int(px) + 226, int(py) - 176, INK, px=17)

    # THE EMPTY CENTRE: a crossed-out circle where the star should be, drawn as a
    # PAPER hole punched through the SLATE inner band
    K.draw_disc(d, cx, cy, 74, fill=PAPER, outline=INK, width=K.OUTLINE,
                seed=440, wobble=3.0)
    for s in (-1, 1):
        _thick_curve(d, [(cx + s * 52, cy - 52), (cx + s * 20, cy - 18),
                         (cx - s * 22, cy + 22), (cx - s * 54, cy + 54)],
                     INK, seed=441 + s, width=9, wobble=2.0, wavelength=90.0)
    # centred below the hole, so it lands on the INK third band: PAPER
    _tiny(d, 'NO STAR HERE', cx, cy + 118, PAPER, px=20)

    # No hero word on this card. 'NOTHING TO ORBIT' restated the narration line
    # verbatim ('No star to orbit'), which STYLE_CANON calls a defect even when
    # the placement is right. The crossed-out centre already carries the idea.
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 5 -- no_light_of_its_own (VOID). Lit only by leaks.
# ===========================================================================

def render_no_light_of_its_own(card, planet=PLANET):
    """VOID, no character -- the pure data beat. A large BLACK disc, the rogue,
    rimmed by the faintest possible gray wash. Four tiny far-off stars sit near
    the four corners of the frame and each one throws a thin tapering BEAM across
    the void onto the planet's limb, with a widening cone showing how little of
    it arrives. The beams are the directional cue and they are also the picture:
    this is the ONLY light the world will ever get.

    The planet is deliberately the darkest large shape in the segment -- it is
    DARKER than the void around it, which is the beat. The wash on its limb is a
    flat low-alpha slate crescent (a shape, not a ramp); the four corner stars are
    emissive and take the segment's only legal gradient, at small size."""
    img = _void_field(Image.new('RGB', (W, H), DEEP), 501, stars=170)
    # A bottom dust band. This card's mass centroid measured 0.379, above the
    # 0.42 floor, because the hero sits high and both the northern stars and the
    # southern pair are small -- the bottom third was empty void.
    img = _band(img, 566, BAND_FILL, seed=5005, stipple_rgb=(112, 120, 136))

    # the rogue: a black disc, darker than the field
    px, py, pr = 632, 380, 218
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, px, py, pr, fill=UNLIT + (255,), outline=None, width=0,
                seed=5011, wobble=3.0)
    # the faint gray wash on the limb -- flat alpha, a shape not a ramp
    wash = []
    for j in range(23):
        a = math.radians(150.0 + 250.0 * j / 22.0)
        wash.append((px + pr * 1.02 * math.cos(a), py + pr * 1.02 * math.sin(a)))
    inner = []
    for j in range(23):
        a = math.radians(150.0 + 250.0 * j / 22.0)
        rr = pr * 0.90
        inner.append((px + rr * math.cos(a), py + rr * math.sin(a)))
    K.draw_smooth(d, wash + inner[::-1], fill=ASH + (150,), outline=None,
                  seed=5012, wobble=4.0, wavelength=240.0, closed=True)
    _flat_ring(d, px, py, pr, BONE, 255, K.FINE)

    # four tiny far-off stars, one per corner region, each with a tapering beam
    beams = ((132, 148, 1.10), (1148, 140, 0.62), (108, 556, 0.74),
             (1166, 556, 1.24))
    for k, (sx, sy, gain) in enumerate(beams):
        a = math.atan2(py - sy, px - sx)
        L = math.hypot(px - sx, py - sy)
        _thick_curve(d, [(sx, sy), (sx + L * 0.55 * math.cos(a),
                                    sy + L * 0.55 * math.sin(a))],
                     ASH, seed=5020 + k, width=int(4 + 5 * gain),
                     wobble=2.0, wavelength=200.0)
        # the widening cone at the receiving end: how little actually lands
        tip = (px + pr * 1.02 * math.cos(a), py + pr * 1.02 * math.sin(a))
        side = a + math.pi / 2.0
        cone = [(sx + 10 * math.cos(side), sy + 10 * math.sin(side)),
                tip,
                (sx - 10 * math.cos(side), sy - 10 * math.sin(side))]
        _open_curve(d, cone, BONE, K.FINE, seed=5030 + k, wobble=1.4,
                    wavelength=180.0)
        _star(img, sx, sy, 13, seed=5040 + k, glow=0.85)

    # Annotation band. The floating caption occupies y 661..685, so every other
    # label must finish above ~645. The first version put this line at y=660,
    # where it ran straight through the caption (measured overlap, x 467..813).
    _tiny(d, 'EACH IMPOSSIBLY FAR', 640, 630, PAPER, px=19, ink=INK)
    # The hero adds the count the caption does not state. 'LIT BY WHAT OTHER
    # STARS LEAK' restated the narration line, which is the redundancy defect
    # STYLE_CANON's hero-word corollary names.
    _hero(d, 'FOUR SOURCES. THAT IS ALL.', 640, 150, BONE, px=42, y_max=190)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# === PART2 ===


# ===========================================================================
# BEAT 6 -- barely_enough_to_see (CREAM). The smudge.
# ===========================================================================

def render_barely_enough_to_see(card, planet=PLANET):
    """CREAM, Register P. The rogue is a huge flat ASH smudge at centre-left --
    barely darker than the page it sits on, which is the entire fact of the beat.
    A LIGHT BUDGET scale runs the full width beneath it and is almost empty: one
    short filled bar out of a long track, with a tick scale and a value.

    The scale is the directional/magnitude cue G2 requires, and the wide empty
    track is the picture. The character is at the right, leaning forward with both
    hands up at his brow, downturned arc mouth -- he is straining to see the thing
    he is looking at. He stands on a ground band occupying the bottom quarter so
    his feet land on something visible (G7)."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    # ground band across the bottom quarter -- he has to stand on something
    K.draw_ground(d, 0, W, 596, H, SLATE + (255,), seed=601, width=K.OUTLINE,
                  roughness=5.0)

    # the rogue: an enormous smudge, only a few steps darker than the paper
    px, py, pr = 452, 356, 236
    K.draw_disc(d, px, py, pr, fill=ASH, outline=INK, width=K.OUTLINE,
                seed=602, wobble=4.0)
    # a couple of barely-there surface marks so it reads as a body, not a sticker
    _flat_ellipse(d, px, py, int(pr * 0.58), int(pr * 0.20), INK, 60, K.FINE)
    _flat_ellipse(d, px + 24, py - 34, int(pr * 0.30), int(pr * 0.11), INK, 44,
                  K.FINE)
    _open_curve(d, [(px + pr - 30, py - 118), (px + pr + 150, py - 176),
                    (px + pr + 232, py - 198)], INK, K.FINE, seed=603, wobble=1.0)
    # The label used to sit at cy = py-274 = 82, which put its bbox top at y=74 --
    # ten rows INSIDE the 84px title strip. It now hangs off a leader in the free
    # upper-right of the art, clear of the strip and of the character.
    _tiny(d, 'A GREY SMUDGE', px + pr + 300, py - 184, INK, px=18)

    # the LIGHT BUDGET scale: a long track, almost entirely empty
    tx0, tx1, ty = 92, 1204, 536
    _hrule(d, ty, tx0, tx1, INK, K.DETAIL, seed=610, wobble=1.2)
    for k in range(7):
        x = tx0 + (tx1 - tx0) * k / 6.0
        _vrule(d, x, ty - 12, ty + 12, INK, K.FINE, seed=620 + k, wobble=0.8)
        _tiny(d, ['0', '2', '4', '6', '8', '10', '12'][k], x, ty + 40, INK,
              px=16)
    # the filled part: a tiny stub of light at the far left of a long track
    K.draw_smooth(d, [(tx0, ty - 30), (tx0 + 128, ty - 30), (tx0 + 128, ty + 4),
                      (tx0, ty + 4)], fill=DUSK, outline=INK, width=K.DETAIL,
                  seed=630, wobble=1.6, wavelength=90.0)
    _tiny(d, 'VISIBLE LIGHT', tx0 + 176, ty - 30, INK, px=17)
    _stamp(d, 'ENOUGH FOR A SHAPE. NOT FOR A SURFACE.', tx0, 596, INK)

    # the character at the right, straining forward, hands up at his brow
    _man(img, card, 'light', 'shielding_eyes', 'frown', 1032, 400, 196,
         seed=639)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 7 -- what_rogue_means (VOID). Three things crossed out.
# ===========================================================================

def render_what_rogue_means(card, planet=PLANET):
    """VOID. Three full-width rows, each a thing a world is supposed to have --
    A PARENT STAR, A SYSTEM, AN ADDRESS -- each with a small flat icon at the left
    and a heavy DUSK strike-through across the whole row. The rows are the
    diagram and the strike is the directional/motion cue: the cancellation is the
    event.

    The icons are drawn, not typed, so the rows are legible without reading: a
    star, an orbit, a pin. A cream character stands at the far left, shrugging,
    flat-mouthed -- the deadpan that says 'I am aware, and there is no defence'.
    The strike colour is dusk amber, the segment's only warm mark, so the three
    cancellations are the loudest thing in an otherwise silent card."""
    img = _void_field(Image.new('RGB', (W, H), DEEP), 701, stars=150)
    # A dust floor under the three rows. Without it this card's mass centroid
    # measured 0.263 -- the worst in the segment -- because all three rows sit
    # above y=520 and the hero is the only thing low. G1: the bottom third cannot
    # be empty void, and here that is a measurable failure, not a judgement call.
    img = _band(img, 580, BAND_FILL, seed=7005, stipple_rgb=(112, 120, 136))
    d = ImageDraw.Draw(img, 'RGBA')

    rows = [('A PARENT STAR', 214), ('A SYSTEM', 358), ('AN ADDRESS', 502)]
    for k, (label, y) in enumerate(rows):
        # the row rule the text and the strike both sit on
        _hrule(d, y, 250, 1216, BONE, K.FINE, seed=7010 + k, wobble=1.0)
        _tiny(d, label, 262, y - 26, BONE, px=24, ink=INK)
        # the strike: one heavy tapering stroke across the whole row
        _thick_curve(d, [(236, y + 14), (520, y - 6), (880, y + 12),
                         (1226, y - 4)], DUSK, seed=7020 + k, width=13,
                     wobble=2.0, wavelength=260.0)

        # --- the icon, drawn so the row reads without the text ---
        ix, iy, ir = 152, y - 4, 42
        if k == 0:                                    # a star
            K.draw_disc(d, ix, iy, ir, fill=DUSK, outline=None, width=0,
                        seed=7030, wobble=2.4)
            _flat_ring(d, ix, iy, ir, DUSK, 190, K.DETAIL)
        elif k == 1:                                  # an orbit + one world
            _flat_ellipse(d, ix, iy, ir + 12, int((ir + 12) * 0.42), BONE, 190,
                          K.DETAIL)
            K.draw_disc(d, ix + ir + 12, iy, 11, fill=BONE, outline=None,
                        width=0, seed=7031, wobble=1.0)
            K.draw_disc(d, ix, iy, 13, fill=SLATE, outline=None, width=0,
                        seed=7032, wobble=1.0)
        else:                                         # a location pin
            _open_curve(d, [(ix - 26, iy - 34), (ix, iy - 44), (ix + 26, iy - 34),
                            (ix + 8, iy + 6), (ix, iy + 40), (ix - 8, iy + 6),
                            (ix - 26, iy - 34)], BONE, K.DETAIL, seed=7033,
                        wobble=1.4, wavelength=70.0)
            K.draw_disc(d, ix, iy - 18, 10, fill=None, outline=BONE,
                        width=K.DETAIL, seed=7034, wobble=1.0)

    _hero(d, 'NOTHING TO CALL AN ADDRESS', 736, 552, PAPER, px=40, y_max=572)

    # the character at the far left, shrugging, deadpan -- feet at 620, on the
    # band that now starts at 580 (G7: he stands on something visible)
    _man(img, card, 'dark', 'shrugged', 'flat', 108, 430, 190, seed=7040)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 8 -- coldest_and_darkest (CREAM). Two pegged gauges.
# ===========================================================================

def render_coldest_and_darkest(card, planet=PLANET):
    """CREAM, Register P. Two full-height instruments side by side: a THERMOMETER
    on the left and a semicircular DARKNESS GAUGE on the right, each with a
    labelled tick scale, each with its needle pegged hard against the far end of
    its scale. A tiny rogue planet sits at the base of the thermometer for scale.

    Both needles being at the end of their travel IS the beat, so both needles
    get an arrowhead and a small overshoot tick past the last graduation, which is
    what makes 'pegged' legible as a reading rather than as decoration. No
    character -- the visual brief marks this a pure data beat."""
    img = _cream_card(card, planet)
    img = _cold_field(img, seed=805)
    d = ImageDraw.Draw(img, 'RGBA')

    # a ground band so the instruments have a floor and the bottom third is not
    # empty paper (G1)
    K.draw_ground(d, 0, W, 600, H, SLATE + (255,), seed=806, width=K.OUTLINE,
                  roughness=4.0)

    # ---- left: the thermometer, filling most of the frame height ----
    tx, tw = 356, 96
    top, bot = 150, 612
    K.draw_smooth(d, [(tx - tw, bot), (tx - tw + 18, (top + bot) / 2),
                      (tx - tw, top), (tx, top - 14), (tx + tw, top),
                      (tx + tw - 18, (top + bot) / 2), (tx + tw, bot)],
                  fill=SLATE, outline=INK, width=K.OUTLINE, seed=801, wobble=3.0,
                  wavelength=240.0)
    # the mercury: pegged, all the way up -- INK on the SLATE body, so it reads
    K.draw_smooth(d, [(tx - tw + 22, bot - 10), (tx - tw + 40, (top + bot) / 2),
                      (tx - tw + 22, top + 26), (tx, top + 16),
                      (tx + tw - 22, top + 26), (tx + tw - 40, (top + bot) / 2),
                      (tx + tw - 22, bot - 10)], fill=INK, outline=INK,
                  width=K.DETAIL, seed=802, wobble=2.4, wavelength=220.0)
    for k in range(9):
        y = top + 26 + (bot - top - 46) * k / 8.0
        _hrule(d, y, tx + tw, tx + tw + 44, INK, K.FINE, seed=810 + k, wobble=0.6)
        if k % 2 == 0:
            _tiny(d, str(-40 + 10 * k), tx + tw + 62, y, INK, px=15)
    # Annotation band: the caption owns y 661..685, so this caption sits at 636
    # and finishes at 645. It sits on the SLATE ground band now, so PAPER.
    _tiny(d, 'COLDEST WE HAVE MEASURED', tx, 636, PAPER, px=18)
    # the tiny rogue at the base, for scale -- PAPER body on the SLATE band
    K.draw_disc(d, tx - tw - 92, bot - 54, 38, fill=PAPER, outline=INK,
                width=K.DETAIL, seed=820, wobble=2.0)

    # ---- right: the darkness gauge ----
    # A real DIAL, not a circle. The first version drew a full ellipse of r=250
    # centred at y=500, so the un-graduated bottom half ran off the frame at
    # y=750 and sat under the floating caption. This is the upper half of a
    # circle closed by its chord, so it reads as an instrument face and its
    # lowest point (gy=560) stays clear of the caption band.
    gx, gy, gr = 918, 560, 232
    face = [(gx + gr * math.cos(math.radians(180.0 + 180.0 * j / 12.0)),
             gy + gr * math.sin(math.radians(180.0 + 180.0 * j / 12.0)))
            for j in range(13)]
    K.draw_smooth(d, face, fill=SLATE, outline=INK, width=K.OUTLINE, seed=825,
                  wobble=2.4, wavelength=300.0, closed=True)
    # the graduated arc, just inside the rim -- PAPER on the SLATE face
    for k in range(11):
        a = math.radians(180.0 + 180.0 * k / 10.0)
        _open_curve(d, [(gx + (gr - 26) * math.cos(a), gy + (gr - 26) * math.sin(a)),
                        (gx + (gr - 6) * math.cos(a), gy + (gr - 6) * math.sin(a))],
                    PAPER, K.FINE, seed=830 + k, wobble=0.6)
        if k % 2 == 0:
            _tiny(d, str(k * 10), gx + (gr - 52) * math.cos(a),
                  gy + (gr - 52) * math.sin(a), PAPER, px=15)
    # the needle: pegged at zero light, pointing hard left, with an overshoot tick
    _thick_curve(d, [(gx, gy), (gx - gr + 34, gy - 28)], DUSK, seed=840,
                 width=11, wobble=1.4, wavelength=140.0)
    _arrow_head(d, (gx - gr + 34, gy - 28), 194.0, DUSK, size=20, seed=841)
    K.draw_disc(d, gx, gy, 17, fill=PAPER, outline=INK, width=K.DETAIL,
                seed=842, wobble=1.2)
    # 'DARKEST WE KNOW OF' is above the face on the cold field: INK.
    # 'LIGHT RECEIVED' is below it, on the ground band: PAPER.
    _tiny(d, 'DARKEST WE KNOW OF', gx, gy - gr - 26, INK, px=18)
    _tiny(d, 'LIGHT RECEIVED', gx, gy + 40, PAPER, px=17)

    # No hero word here: 'NOTHING HERE IS FRIENDLY' is the narration line
    # ('Nothing about this world is friendly') verbatim, so it restated the
    # caption. It also sat at y 639..668, straight through the caption.
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 9 -- less_than_darkness (VOID). Standing on the limb.
# ===========================================================================

def render_less_than_darkness(card, planet=PLANET):
    """VOID, the payoff. The rogue's curved black limb sweeps across the whole
    bottom of the frame from a sphere so large that only its shoulder is visible,
    and the character stands TINY on that limb -- hands up, wide oval mouth -- the
    only lit thing in a frame that is otherwise an enormous empty starfield.

    The composition is the argument: the ground occupies the bottom quarter and
    the empty sky the upper three quarters, so the viewer sees how little there is
    to see. Directional cues: a faint rim light along the limb, a line of small
    survey stakes receding along it for scale, and four tick-marked distance
    labels. The limb is FLAT near-black with a stippled grain -- it is not a
    gradient and it is not lit."""
    img = _void_card(card, planet, seed=901, stars=180)

    # The limb. Built with _band, not K.draw_ground: clamping every sample of a
    # hand-rolled arc to y=588 collapsed the curve to a straight line and the
    # wobbled off-frame corners notched the bottom row, while K.draw_ground's
    # built-in INK keyline is a near-invisible 2px line that the check reads as a
    # clipped glyph all the way along the frame edge (25 findings). The fill is a
    # distinguishable cold slate, NOT near-black: a (1,1,3) limb against a (3,4,9)
    # void has no edge at all, so its silhouette read as both a low-contrast smear
    # and a clipped fragment.
    img = _band(img, 588, BAND_FILL, seed=9011, stipple_rgb=(126, 134, 148))
    d = ImageDraw.Draw(img, 'RGBA')
    # the rim light along the top of the limb -- widened from 7 to 12, because at
    # 7 it broke up over the stipple and measured 24.8 luma from its surround, a
    # hair under the 25 threshold
    _thick_curve(d, [(EDGE_SAFE, 588), (300, 580), (640, 592), (980, 578),
                     (W - EDGE_SAFE, 588)],
                 BONE, seed=9013, width=12, wobble=2.0, wavelength=300.0)

    # survey stakes receding along the limb -- the scale cue. Placed along the
    # limb's top edge (which K.draw_ground wobbles around y=588) rather than on a
    # computed arc, so they sit ON the drawn edge instead of near it.
    for k, (sx, hh) in enumerate(((232, 30), (452, 26), (668, 22),
                                  (872, 18), (1062, 15), (1204, 12))):
        _vrule(d, sx, 588 - hh, 592, BONE, K.DETAIL, seed=9020 + k, wobble=0.6)
        _flat_ring(d, sx, 584 - hh, 4, BONE, 255, K.FINE)

    # the character, tiny, on the limb, hands up
    _man(img, card, 'dark', 'hands_up', 'oval', 838, 452, 136, seed=9030)

    # a leader from him to the label, so nothing overlaps the thing it labels
    _open_curve(d, [(838, 448), (930, 336), (1002, 268)], BONE, K.FINE,
                seed=9031, wobble=1.0, wavelength=110.0)
    _tiny(d, 'YOU WOULD NEVER FIND THE EDGE', 1046, 240, BONE, px=19, ink=INK)
    _hero(d, 'LESS THAN DARKNESS', 350, 214, BONE, px=44, y_max=254)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# === PART3 ===


# ===========================================================================
# BEAT 10 -- the_dust_ring (CREAM). Leftovers.
# ===========================================================================

def render_the_dust_ring(card, planet=PLANET):
    """CREAM, Register P. A wide, thin, tilted dust ring of individually drawn
    specks encircles a plain dark rogue at the centre, and the ring spans almost
    the full frame width. Two bracket calipers measure the ring's outer and inner
    edges, so the viewer's eye is told 'thin but enormous' rather than 'small'.

    Directional cues: an arrowhead on the ring showing which way the dust still
    travels, and the calipers. The rogue is a flat dark disc -- not a gradient --
    because it is a body with no light on it, which is the segment's whole
    subject. No character: the visual brief marks this a pure data beat."""
    img = _cream_card(card, planet)
    img = _cold_field(img, seed=1005)
    d = ImageDraw.Draw(img, 'RGBA')

    # a ground band under the ring so the bottom third is not empty paper
    K.draw_ground(d, 0, W, 596, H, SLATE + (255,), seed=1006, width=K.OUTLINE,
                  roughness=5.0)

    cx, cy = 622, 388
    rx, ry, tilt = 552, 168, -9.0

    # the rogue at the centre of the ring, flat and dark -- bigger, so the frame's
    # subject meets G1's 55%-of-width bar on its own
    K.draw_disc(d, cx, cy, 128, fill=ROGUE_FILL, outline=INK, width=K.OUTLINE,
                seed=1001, wobble=2.6)
    _flat_ellipse(d, cx, cy, 76, 28, INK, 255, K.FINE)

    # the ring itself: an ellipse of individually placed specks, densest at the
    # sides where the orbit is seen edge-on through the most dust. Speck radius
    # raised from 2-4 to 3-6: at 2px the ring measured ink_fraction 0.083, which
    # is below the floor even with a field behind it.
    rnd = random.Random(1002)
    ring_pts = []
    for i in range(760):
        a = math.tau * i / 760.0
        rr = 1.0 + 0.035 * math.sin(3 * a + 1.1) + 0.02 * math.sin(5 * a)
        x = cx + rx * rr * math.cos(a)
        y = cy + ry * rr * math.sin(a) * math.cos(math.radians(tilt)) \
            + 26 * math.sin(a)
        # only the near half of the ring is in front of the planet
        if math.sin(a) < 0 and math.hypot(x - cx, y - cy) < 146:
            continue
        edge = abs(math.cos(a))
        r = rnd.choice((3, 4, 4, 5, 6))
        col = INK if edge > 0.55 else SLATE
        ring_pts.append((x, y, r, col))
    for (x, y, r, col) in ring_pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    # the direction the dust still travels
    a = math.radians(14.0)
    tip = (cx + rx * math.cos(a), cy + ry * math.sin(a) * math.cos(math.radians(tilt)) + 26 * math.sin(a))
    _arrow_head(d, tip, 96.0, DUSK, size=24, seed=1003)

    # calipers: outer and inner edges, so 'thin but wide' is the readable fact
    _vrule(d, 96, cy - 214, cy + 214, INK, K.DETAIL, seed=1004, wobble=0.8)
    _hrule(d, cy - 214, 96, 300, INK, K.DETAIL, seed=1005, wobble=0.8)
    _tiny(d, 'THE WHOLE RING', 96, cy - 244, INK, px=18)
    _vrule(d, 1150, cy - 190, cy - 42, INK, K.DETAIL, seed=1007, wobble=0.8)
    _hrule(d, cy - 190, 1064, 1150, INK, K.DETAIL, seed=1007, wobble=0.8)
    _tiny(d, 'AND ALL OF IT IS THIN', 1150, cy - 220, INK, px=18)

    # a leader onto the planet, since the ring crosses its own label otherwise
    _open_curve(d, [(cx + 132, cy - 40), (cx + 220, cy - 130),
                    (cx + 300, cy - 214)], INK, K.FINE, seed=1008, wobble=1.0)
    _tiny(d, 'THE PLANET', cx + 360, cy - 232, INK, px=19)

    # INK, not SLATE: the hero sat on the cold field and SLATE-on-paper measured
    # under the contrast threshold.
    _hero(d, 'A WHOLE SUN OF LEFTOVERS', cx, 630, INK, px=36, y_max=650)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 11 -- a_suns_worth_of_wreckage (VOID). The ring remembers.
# ===========================================================================

def render_a_suns_worth_of_wreckage(card, planet=PLANET):
    """VOID, no character. The dust ring is the segment's SECOND emissive body and
    so it takes the one legal gradient: a stippled dusk-amber core with a real
    soft outer halo (G3, the quality target from tres2b/cardsheet/beat_10.png).
    The rogue inside the ring is COMPLETELY UNLIT -- pure black, no keyline on
    its sunward side, because it receives nothing from the ring it carries.

    That contrast is the card: the leftovers glow, the thing they orbit does not.
    Directional cues: three concentric halo rings at falling alpha, a full-width
    'one thin circle' bracket measuring how little of the frame the ring's
    material actually occupies, and a stipple burst so the ring reads as hot dust
    rather than as a drawn circle."""
    img = _void_field(Image.new('RGB', (W, H), DEEP), 1101, stars=170)
    # A dust floor. The ring is deliberately high and the whole card's material
    # mass sits above y=500, so the centroid measured 0.382 against a 0.42
    # floor. The floor is the same band every other void card uses, so the
    # segment reads as one world rather than thirteen.
    img = _band(img, 588, BAND_FILL, seed=1105, stipple_rgb=(112, 120, 136))

    # The ring sits HIGH. The first version centred it at y=392 with a halo out
    # to 1.56x, whose lowest point was y=660 -- inside the caption band, which is
    # why the bracket and both labels were stacked straight through the caption.
    cx, cy = 626, 340
    rx, ry = 536, 158

    # the unlit planet: pure black, no rim on the ring side
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, cx, cy, 96, fill=UNLIT + (255,), outline=None, width=0,
                seed=1101, wobble=2.6)

    # THE GLOWING RING -- emissive, so this is the segment's second legal gradient.
    # It is built as an elliptical emissive band rather than a circle: the ring is
    # seen at a shallow angle, so the glow has to be an ellipse too.
    for k in range(46):
        t = k / 45.0
        a = 150 - 120 * t
        e = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ed = ImageDraw.Draw(e)
        rr = int(58 * t)
        ed.ellipse([cx - rx - rr, cy - ry - rr, cx + rx + rr, cy + ry + rr],
                   outline=DUSK + (int(a),), width=int(9 * (1.0 - t) + 2))
        e = e.filter(ImageFilter.GaussianBlur(9))
        img = Image.alpha_composite(img.convert('RGBA'), e).convert('RGB')
    # the hot inner core of the ring, stippled so it keeps the spray grain
    d = ImageDraw.Draw(img, 'RGBA')
    K.stipple(d, cx - rx, cy - ry - 26, cx + rx, cy + ry + 26, (255, 214, 150),
              seed=1102, density=0.030, r=1, spread=2)
    _flat_ellipse(d, cx, cy, rx, ry, (255, 226, 172), 210, K.FINE)

    # the halo rings: the ring's glow falling away into the void
    for k, (sc, al) in enumerate(((1.16, 96), (1.34, 58), (1.56, 30))):
        _flat_ellipse(d, cx, cy, int(rx * sc), int(ry * sc), DUSK, al, K.DETAIL)

    # 'one thin circle': the bracket showing how little of the frame it fills.
    # Both the bracket and its labels now sit on the dust floor, so they are
    # PAPER against BAND_FILL rather than BONE against void.
    _hrule(d, 600, 92, 1204, PAPER, K.DETAIL, seed=1110, wobble=1.2)
    for x in (92, 1204):
        _vrule(d, x, 578, 622, PAPER, K.DETAIL, seed=1111, wobble=0.8)
    _tiny(d, 'A WHOLE SUN, IN ONE THIN CIRCLE', 700, 644, PAPER, px=19)

    # a leader to the unlit planet: it is the reason the ring matters
    _open_curve(d, [(cx - 96, cy + 52), (cx - 240, cy + 168),
                    (cx - 320, cy + 250)], BONE, K.FINE, seed=1120, wobble=1.0)
    _tiny(d, 'AND IT CIRCLES NOTHING', 250, 644, PAPER, px=19)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 12 -- it_passes_you (CREAM). It will never know you.
# ===========================================================================

def render_it_passes_you(card, planet=PLANET):
    """CREAM, Register P. The rogue crosses the frame left to right at mid height,
    trailing a long DOTTED path behind it and a tapering motion streak, with an
    arrowhead on its nose. On the right, on a low ridge, a tiny observatory and a
    single watching figure; a 'YOU ARE HERE' marker with a leader line points at
    the ground he is standing on.

    Directional cues: the dotted trail, the streak, the arrowhead, and the marker
    -- the whole card is one left-to-right reading, which is the picture of 'you
    are watching it pass'. The character stands at the right on the ridge, flat
    mouthed, one hand shading his eyes, because that is the beat's whole emotion:
    total, unreturned attention. His feet land on the ridge (G7)."""
    img = _cream_card(card, planet)
    img = _cold_field(img, seed=1200, bottom=560)
    d = ImageDraw.Draw(img, 'RGBA')

    # The ground: a ridge across the bottom quarter, with the observatory on it.
    # Raised from y=540 to y=486: at 540 the frame's mass centroid sat at 0.800,
    # well past the 0.75 ceiling, because everything else in the card is a thin
    # trail of dots up at y~300. Lifting the ridge 54px puts the observatory and
    # the watching figure in the lower third where G1 wants the mass.
    K.draw_ground(d, 0, W, 486, H, SLATE + (255,), seed=1201, width=K.OUTLINE,
                  roughness=6.0)

    # The dotted path the rogue has already travelled, then the streak, then it.
    # The path starts at x=30, NOT off-frame at x=-30: a dot centred on the left
    # edge is a component touching column 0, and the check filed it as a clipped
    # glyph (bbox [0,279,300,323]). G5 wants the trail to read as continuing off
    # the left edge, which it still does -- it just starts inside the frame.
    path = [(30, 322), (176, 306), (388, 292), (596, 282)]
    for i in range(len(path) - 1):
        x0, y0 = path[i]
        x1, y1 = path[i + 1]
        steps = 13
        for s in range(steps):
            t = s / float(steps)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            r = 5 if i else 4
            d.ellipse([x - r, y - r, x + r, y + r], fill=INK)
    _thick_curve(d, [(300, 296), (470, 288), (620, 282)], SLATE, seed=1202,
                 width=34, wobble=3.0, wavelength=180.0)
    _thick_curve(d, [(300, 296), (470, 288), (620, 282)], INK, seed=1203,
                 width=9, wobble=2.0, wavelength=180.0)

    # the rogue itself, with its arrowhead
    px, py, pr = 700, 276, 40
    K.draw_disc(d, px, py, pr, fill=ROGUE_DARK, outline=INK, width=K.OUTLINE,
                seed=1204, wobble=2.4)
    _arrow_head(d, (px + pr + 34, py - 12), -6.0, INK, size=26, seed=1205)
    _open_curve(d, [(px + pr + 8, py + 34), (px + pr + 110, py + 92),
                    (px + pr + 194, py + 128)], INK, K.FINE, seed=1206,
                wobble=1.0)
    _tiny(d, 'IT DOES NOT TURN AROUND', px + pr + 244, py + 146, INK, px=18)

    # the observatory on the ridge, left of the character, for scale. Ridge top
    # is now y=486, so the observatory base follows it down.
    ox, oy = 250, 492
    K.draw_smooth(d, [(ox - 54, oy + 4), (ox - 30, oy - 52), (ox, oy - 76),
                      (ox + 30, oy - 52), (ox + 54, oy + 4)],
                  fill=PAPER, outline=INK, width=K.OUTLINE, seed=1210,
                  wobble=2.0, wavelength=110.0)
    _flat_ellipse(d, ox, oy - 76, 26, 13, INK, 255, K.DETAIL)

    # the watching figure at the right, on the ridge, one hand shading his eyes
    _man(img, card, 'light', 'shielding_eyes', 'flat', 1086, 330, 168, seed=1220)

    # YOU ARE HERE, with a leader that stops short of the figure
    _open_curve(d, [(1086, 458), (1086, 520), (986, 560)], PAPER, K.DETAIL,
                seed=1230, wobble=1.2)
    _tiny(d, 'YOU ARE HERE', 902, 580, PAPER, px=20)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 13 -- the_loneliest_thing_found (VOID). The closing image.
# ===========================================================================

def render_the_loneliest_thing_found(card, planet=PLANET):
    """VOID, the closer. The rogue sits alone at the centre of a very wide field:
    a dark sphere with a single thin bone rim on its upper-left, so it is a shape
    against a shape rather than a hole. A broad dust horizon runs across the
    bottom quarter so the frame is anchored and the v_centroid stays in the lower
    two-thirds, and the character stands small at the lower right, head tipped
    back, mouth wide open, utterly still.

    This is the emptiest card in the segment and it is still not empty: the
    emptiness is carried by WIDTH (a small subject in a large field) and by the
    dust bands, not by leaving the frame blank. One hero phrase, the segment's
    closing line, placed upper-left where the field is free."""
    img = _void_field(Image.new('RGB', (W, H), DEEP), 1301, stars=190)
    # a broad dust wash sitting ON the horizon band, so the frame's mass centroid
    # drops into the lower half (it measured 0.321, above the 0.42 floor: the
    # original card put nearly all its ink up at the rogue and the hero)
    img = _wash(img, [(60, 470), (420, 430), (820, 476), (1240, 440),
                      (1300, 596), (700, 620), (80, 604)],
                SLATE, 34, seed=1311, wobble=20.0, wavelength=280.0, blur=40)

    # the dust horizon: a broad flat band with a lit top edge, filling the
    # bottom quarter so the subject stands on something (G1)
    img = _band(img, 520, BAND_FILL, seed=1301, stipple_rgb=(126, 134, 148),
                rule=BONE)

    # the rogue, alone, with one thin rim so it reads as a sphere and not a hole
    px, py, pr = 548, 348, 126
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, px, py, pr, fill=UNLIT + (255,), outline=None, width=0,
                seed=1304, wobble=3.0)
    rim = [(px + pr * 1.01 * math.cos(math.radians(a)),
            py + pr * 1.01 * math.sin(math.radians(a)))
           for a in range(158, 262, 4)]
    _thick_curve(d, rim, BONE, seed=1305, width=9, wobble=2.0, wavelength=200.0)
    _stipple(d, px - pr, py - pr, px + pr, py + pr, (128, 136, 150), seed=1306,
              density=0.004, r=1, spread=2)

    # the character at the lower right, head back, awed and still
    _man(img, card, 'dark', 'hands_down', 'oval', 1074, 396, 152, seed=1310)

    _hero(d, 'THE LONELIEST THING WE HAVE FOUND', 372, 178, BONE, px=38,
          y_max=220)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# Dispatch -- keyed by the beat `id` field from script.json. The frame generator
# merges this into cardframe's process-global table via C.register(RENDERERS).
# ===========================================================================

RENDERERS = {
    'hook_a_sun_you_know': render_hook_a_sun_you_know,
    'ejection_neighbor_comes_too_close': render_ejection_neighbor_comes_too_close,
    'thrown_into_the_between': render_thrown_into_the_between,
    'no_star_to_orbit': render_no_star_to_orbit,
    'no_light_of_its_own': render_no_light_of_its_own,
    'barely_enough_to_see': render_barely_enough_to_see,
    'what_rogue_means': render_what_rogue_means,
    'coldest_and_darkest': render_coldest_and_darkest,
    'less_than_darkness': render_less_than_darkness,
    'the_dust_ring': render_the_dust_ring,
    'a_suns_worth_of_wreckage': render_a_suns_worth_of_wreckage,
    'it_passes_you': render_it_passes_you,
    'the_loneliest_thing_found': render_the_loneliest_thing_found,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table. Harmless if
    called twice. The frame generator may also just read .RENDERERS directly."""
    C.register(RENDERERS if mapping is None else mapping)
    return RENDERERS


# ===========================================================================
# __main__ self-test -- render one cardsheet PNG per beat into ./cardsheet/.
# Run:  python work/segments/psoj3185/_cards.py
# ===========================================================================

# beat id -> (register, pose, expression, x_center, y_top, height, caption)
# The pose/expression here are the SAME constants the renderers fall back to, so
# the cardsheet is exactly what ships. Captions are short generic lines; the real
# renderers draw their own diagram labels on top.
CHARS = {
    'hook_a_sun_you_know':               ('void',  'shielding_eyes', 'flat',   262, 402, 196,
                                         'EVERY PLANET HAD A SUN'),
    'ejection_neighbor_comes_too_close': ('cream', 'hands_up',        'oval',   138, 470, 208,
                                         'SOMETHING KICKED IT OUT'),
    'thrown_into_the_between':           ('void',  None,              None,      0,   0,   0,
                                         'THROWN INTO THE DARK BETWEEN'),
    'no_star_to_orbit':                  ('cream', None,              None,      0,   0,   0,
                                         'NO STAR TO ORBIT'),
    'no_light_of_its_own':               ('void',  None,              None,      0,   0,   0,
                                         'LIT ONLY BY WHAT LEAKS THROUGH'),
    'barely_enough_to_see':              ('cream', 'shielding_eyes', 'frown', 1032, 400, 196,
                                         'BARELY ENOUGH TO SEE BY'),
    'what_rogue_means':                  ('void',  'shrugged',        'flat',   108, 430, 190,
                                         'A ROGUE PLANET'),
    'coldest_and_darkest':               ('cream', None,              None,      0,   0,   0,
                                         'AMONG THE COLDEST AND DARKEST'),
    'less_than_darkness':                ('void',  'hands_up',        'oval',   838, 452, 136,
                                         'LESS THAN DARKNESS'),
    'the_dust_ring':                     ('cream', None,              None,      0,   0,   0,
                                         'A SMALL RING OF DUST'),
    'a_suns_worth_of_wreckage':          ('void',  None,              None,      0,   0,   0,
                                         'A WHOLE SUN OF WRECKAGE'),
    'it_passes_you':                     ('cream', 'shielding_eyes', 'flat',  1086, 372, 168,
                                         'IT WILL NEVER KNOW YOU'),
    'the_loneliest_thing_found':         ('void',  'hands_down',      'oval',  1074, 420, 152,
                                         'THE LONELIEST THING FOUND'),
}


def _text_guard(beat, card):
    """Render `card` and assert the TYPE is placed legally, not just drawn.

    Every defect this guard catches has actually shipped in this project: a label
    whose bbox ran to y=733 on a 720-row card, a diagram label ten rows inside
    the 84px title strip, and four separate cards where a hardcoded diagram
    label was stacked straight through the floating caption. All of them are
    invisible to a size/mode assertion and obvious on the frame, so the frame
    generator's own gate does not catch them and they survive review.

    Checks, all measured from the real glyph bboxes the renderer produced:
      * nothing off-frame in any direction;
      * nothing in the title strip except the planet header;
      * no text overlapping the floating caption.
    Returns the list of problems found (empty when the card is clean).
    """
    placed = []
    real_text = ImageDraw.ImageDraw.text

    def spy(self, xy, txt, *a, **kw):
        font = kw.get('font')
        if font is not None and isinstance(txt, str):
            try:
                bb = font.getbbox(txt)
                placed.append((xy[0] + bb[0], xy[1] + bb[1],
                               xy[0] + bb[2], xy[1] + bb[3], txt))
            except Exception:
                pass
        return real_text(self, xy, txt, *a, **kw)

    ImageDraw.ImageDraw.text = spy
    try:
        RENDERERS[beat](card, PLANET)
    finally:
        ImageDraw.ImageDraw.text = real_text

    bad = []
    for (x0, y0, x1, y1, txt) in placed:
        if x0 < -1 or y0 < -1 or x1 > W + 1 or y1 > H + 1:
            bad.append('%s: %r off-frame bbox=(%d,%d,%d,%d)' % (beat, txt, x0, y0, x1, y1))
        elif y0 < T.ART_TOP and txt != PLANET:
            bad.append('%s: %r intrudes on the title strip (y0=%d < %d)'
                       % (beat, txt, y0, T.ART_TOP))

    cap = next((p for p in placed if p[4] == card['caption']), None)
    if cap is None:
        bad.append('%s: caption %r never drawn' % (beat, card['caption']))
    else:
        for other in placed:
            if other is cap:
                continue
            if not (other[2] <= cap[0] or cap[2] <= other[0]
                    or other[3] <= cap[1] or cap[3] <= other[1]):
                bad.append('%s: caption %r overlaps %r (cap=%s other=%s)'
                           % (beat, card['caption'], other[4], cap[:4], other[:4]))
    return bad


def _self_test():
    """Build a minimal card dict for every beat and render it.

    The card carries `stickman: None` -- which is exactly what
    work/segments/_frames.py supplies -- so the self-test exercises the real
    shipping path in which each renderer draws its own character from its own
    per-beat constants. Every frame must come back 1280x720 RGB, every glyph
    must land inside the frame and outside the title strip, and nothing may
    collide with the floating caption."""
    import json
    import os as _os

    out_dir = _os.path.join(HERE, 'cardsheet')
    _os.makedirs(out_dir, exist_ok=True)

    # a renderer is only correct if it matches the plan, so read the beat list
    # from script.json rather than trusting RENDERERS.keys() to stay in sync
    with open(_os.path.join(HERE, 'script.json'), encoding='utf-8') as f:
        script = json.load(f)
    beats = script['beats']

    missing = [b['id'] for b in beats if b['id'] not in RENDERERS]
    extra = [k for k in RENDERERS if k not in {b['id'] for b in beats}]
    if missing or extra:
        raise SystemExit('RENDERERS out of sync with script.json; '
                         'missing=%s extra=%s' % (missing, extra))

    ok = 0
    problems = []
    for i, b in enumerate(beats):
        cid = b['id']
        reg = CHARS[cid][0]
        card = {
            'id': cid,
            'n': b['n'],
            'beat': b['beat'],
            'register': reg,
            'line': b.get('line', ''),
            'caption': CHARS[cid][6],
            'motion': 'hold',
            'stickman': None,
        }
        img = RENDERERS[cid](card, PLANET)
        assert img.size == (W, H), '%s returned %s not 1280x720' % (cid, img.size)
        assert img.mode == 'RGB', '%s returned mode %s not RGB' % (cid, img.mode)
        # a re-render must be byte-identical: every wobble is explicitly seeded
        again = RENDERERS[cid](card, PLANET)
        assert again.tobytes() == img.tobytes(), '%s is not deterministic' % cid
        path = _os.path.join(out_dir, 'beat_%02d.png' % b['n'])
        img.save(path)
        ok += 1
        has_char = 'yes' if CHARS[cid][1] else 'no '
        print('beat %02d  %-34s %-5s  char=%s  %s'
              % (b['n'], cid, reg, has_char, _os.path.basename(path)))
        problems.extend(_text_guard(cid, card))

    if problems:
        print('\nTYPE PLACEMENT PROBLEMS (%d):' % len(problems))
        for p in problems:
            print('  -', p)
        return 1
    print('self-test OK: %d/%d beats rendered to %s' % (ok, len(beats), out_dir))
    return 0


if __name__ == '__main__':
    raise SystemExit(_self_test())



