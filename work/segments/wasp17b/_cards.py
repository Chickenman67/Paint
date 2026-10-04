# work/segments/wasp17b/_cards.py — the 13 beat renderers for segment 5.
#
# Subject: WASP-17b — a retrograde, ultra-puffy, ultra-hot gas giant. Every beat
# is about a WRONGNESS: the backwards spin, the near-emptiness, the endless wind.
#
# CONTRACT (per work/STYLE_CANON.md and work/lib/cardframe.py):
#   * Layout A — 84px paper title strip (rows 0..83), full-bleed art rows 84..719,
#     NO caption band. The caption floats on the art via C._caption(...,70,652).
#   * RENDERERS is keyed by the beat `id` field from script.json. Each value has
#     signature fn(card, planet="WASP-17b") -> PIL RGB 1280x720.
#   * The renderer DRAWS the frame. It does not return a card dict. It does not
#     mutate `card`.
#   * Register discipline: 'void' -> void_backdrop + C._header(paper_band=True)
#     + theme='dark' character + dark_bg=True caption. 'cream' -> full-bleed
#     PAPER + C._header(paper_band=False) + theme='light' + dark_bg=False.
#   * The ONLY legal gradient is the emissive host star (C._radial_core). The
#     gas giant, orbit ellipses, arrows, wind ribbons, cloud bands, temperature
#     column, starfield, title strip, caption and the character are all FLAT.
#   * Every hero phrase goes through C.hero_word, which measures the stroked box,
#     so a phrase can never run off-frame or ride into the title strip.
#   * Every hero phrase must ADD a fact, not restate the caption.
#   * Every wobble / stipple / starfield call takes an explicit seed. No global
#     random state, so re-renders are byte-identical.
#
# The palette is this segment's own (PALETTE_SPEC.md §1). cardframe.PAL is segment
# 3's palette and is NOT used for segment colors — only its generic helpers
# (void_backdrop, _radial_core, add_glow, space_body, _header, _caption,
# hero_word, _draw_stickman) are borrowed.

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
import lib.cardframe as C      # noqa: E402

W, H = C.W, C.H

PLANET = "WASP-17b"

# ---------------------------------------------------------------------------
# PALETTE_SPEC.md §1 — locked. 6 colors + the character's global shirt red,
# which is deliberately NOT an accent here.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':    (20, 22, 28),       # #14161C  slate-black
    'paper':  (242, 234, 214),    # #F2EAD6  bone-cream
    'deep':   (7, 7, 14),         # #07070E  void
    'amber':  (232, 163, 61),     # #E8A33D  signal amber
    'bone':   (220, 230, 236),    # #DCE6EC  x-ray bone
    'teal':   (62, 124, 140),     # #3E7C8C  cold teal (shapes only)
    'ember':  (122, 46, 18),      # #7A2E12  deep red-brown, the star's limb
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
AMBER = MY_PAL['amber']
BONE = MY_PAL['bone']
TEAL = MY_PAL['teal']
EMBER = MY_PAL['ember']

# The hero phrase is capped at 72 so a long phrase auto-shrinks rather than
# shouting; hero_word still enforces the frame margin including its keyline.
HERO_PX = 64
HERO_Y_MAX = 604            # keeps the hero clear of the caption baseline at 652


# ---------------------------------------------------------------------------
# Local helpers — open hand-wobbled curves and flat strokes.
#
# lib/ink.py's `_smooth_open` is broken: its Catmull-Rom extension buffer is two
# elements short and raises IndexError for any polyline of 3+ points, so
# K.draw_outline(closed=False) / K.draw_smooth(closed=False) are unusable. The
# closed path (K.draw_smooth / K.draw_outline / K.smooth_closed) works fine, so
# every open curve here is rebuilt locally on the same wobble engine.
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
    """An OPEN hand-wobbled smooth curve, stroked. Mirrors what
    K.draw_outline(closed=False) was meant to do, on the same wobble engine."""
    pts = K.wobble_points(points, seed=seed, amount=wobble,
                          wavelength=wavelength)
    if len(pts) < 3:
        draw.line(list(pts), fill=color, width=width)
        return pts
    dense = _catmull_open(pts, samples=12)
    draw.line(dense, fill=color, width=width, joint='curve')
    return dense


def _thick_curve(draw, points, fill, seed=0, width=24, wobble=2.0,
                 wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region.

    WHY NOT draw.line(..., width=24, joint='curve'): the Catmull-Rom output has
    many near-duplicate consecutive points; PIL renders each segment as a
    rectangle plus a round cap, and on a zero-length segment the cap shows up as
    a nub, giving a hairy-edged glyph. So the stroke is built geometrically: the
    smooth centreline is offset +/- half-width along its normal into two rails
    welded into one closed polygon, filled with a single draw.polygon. Clean
    edges, no nubs."""
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
    region = outer + inner[::-1]
    draw.polygon(region, fill=fill)
    return region


def _vline(draw, x, y0, y1, color, width=K.FINE, seed=0, wobble=1.2):
    """A short hand-wobbled vertical rule."""
    mid = (y0 + y1) / 2.0
    return _open_curve(draw, [(x, y0), (x, mid), (x, y1)], color, width,
                       seed=seed, wobble=wobble, wavelength=60.0)


def _hrule(draw, y, x0, x1, color, width=K.FINE, seed=0, wobble=1.2):
    """A short hand-wobbled horizontal rule."""
    mid = (x0 + x1) / 2.0
    return _open_curve(draw, [(x0, y), (mid, y), (x1, y)], color, width,
                       seed=seed, wobble=wobble, wavelength=90.0)


def _arc_pts(cx, cy, rx, ry, a0_deg, a1_deg, n=64):
    """Sample an elliptical arc. PIL angles: 0 = 3 o'clock, increasing clockwise
    (screen y grows downward), so 180 = 9 o'clock (screen-left), 270 = 12."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / float(n))
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _ellipse_pts(cx, cy, rx, ry, n=64):
    """Sample a full ellipse (used for orbit rings)."""
    return _arc_pts(cx, cy, rx, ry, 0.0, 360.0, n)


def _flat_ellipse(draw, cx, cy, rx, ry, color, alpha, width=K.DETAIL):
    """A FLAT ellipse outline at a given alpha. A shape color, never a gradient."""
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                 outline=color + (alpha,), width=width)


def _flat_ring(draw, cx, cy, r, color, alpha, width=K.DETAIL):
    """A FLAT concentric ring (no gradient)."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=color + (alpha,), width=width)


def _arrow_head(draw, tip, ang_deg, color, size=16, seed=0):
    """A small hand-drawn triangular arrowhead pointing along `ang_deg` (screen
    degrees, same convention as PIL arcs). Filled flat."""
    a = math.radians(ang_deg)
    tipx, tipy = tip
    back = []
    for s in (-1, 1):
        b = a + math.radians(150.0 * s)
        back.append((tipx + size * math.cos(b), tipy + size * math.sin(b)))
    K.draw_smooth(draw, [tip, back[0], back[1]], fill=color,
                  outline=None, seed=seed, wobble=1.4, wavelength=40.0,
                  closed=True)


def _tiny(draw, text, cx, cy, fill, px=18, ink=None):
    """A small annotation in the locked family, centered, with an optional 1px
    keyline so it reads on a dark field. Diagram labels only."""
    font = T.load_font_at(px, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    x = cx - w / 2.0 - x0
    y = cy - h / 2.0 - y0
    if ink is None:
        draw.text((x, y), text, font=font, fill=fill)
    else:
        T.draw_outlined_text(draw, (x, y), text, font, fill=fill, stroke=ink,
                             stroke_width=1)


def _stamp(draw, text, x, y, fill, ink=INK, px=None, bold=False):
    """Left-anchored diagram text. Defaults to the locked STAMP_PX regular face.

    `px` may be raised to CAPTION_PX or LABEL_PX when a card needs one of the
    locked sizes to carry an actual IDEA rather than annotate the diagram — beat
    12's three checklist items, which at 15px were unreadable. The size is always
    one of the five in work/lib/type.py; this never invents a sixth."""
    if px is None or (not bold and px == T.STAMP_PX):
        T.draw_stamp(draw, text, (x, y), fill, ink_rgb=ink)
        return
    font = T.load_font_at(px, bold=bold)
    draw.text((x, y), text, font=font, fill=fill)


def _soft_wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=170.0,
               blur=18):
    """A painterly FLAT-color region with soft edges.

    Every wash on this segment (the empty-field wash, the heat haze) is a FLAT
    fill on its own RGBA layer, wobbled by K.draw_smooth then blurred, so nothing
    ever shows a crisp rectangle or a square corner. Returns a new RGB image."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=rgb + (int(alpha),), outline=None,
                  seed=seed, wobble=wobble, wavelength=wavelength, closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _void_field(img, seed, stars=124):
    """Register-S space field. A distinct seed per card so no two cards in the
    segment are literally the same frame with the same stars."""
    return C.void_backdrop(img, seed=seed, stars=stars)


def _star(img, cx, cy, r, seed, stops=None):
    """The host star: the ONE legal gradient in the segment. 3-stop radial
    gradient (white -> amber -> ember limb) via C._radial_core, which also adds
    the soft circular halo the STYLE_CANON addendum requires. A deterministic
    stipple is added so it keeps the spray-paint grain instead of reading as a
    clean CG ramp."""
    if stops is None:
        stops = [(255, 255, 255), AMBER, EMBER]
    C._radial_core(img, int(cx), int(cy), int(r), stops)
    d = ImageDraw.Draw(img, 'RGBA')
    K.stipple(d, cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9,
              EMBER, seed=seed, density=0.03, r=1, spread=1)
    return d


def _gas_giant(img, cx, cy, r, seed, band_count=5, warm=False):
    """The gas giant: FLAT horizontal cloud strata on a flat disc, with a dark
    keyline and a flat terminator crescent. Returns the new image.

    WHY THIS IS NOT C.space_body. `space_body` builds its base as a soft RADIAL
    GRADIENT and then sweeps CONCENTRIC elliptical bands at 0.24..0.86 of the
    radius. Two problems, both canon violations:
      * a gradient on the planet is on the explicit denylist (PALETTE_SPEC §3 —
        the planets take flat fill plus surface treatment, never a ramp); and
      * concentric bands at that spacing read as a BULLSEYE, i.e. a target, not
        a sphere — the exact defect the STYLE_CANON addendum names for small
        planets, which here is worse because the giant is the largest body in the
        segment and it was the hero of five beats.
    A gas giant is horizontal STRATA, so that is what is drawn: full-width
    wobbled bands on an RGBA layer, clipped to a hard disc mask, so the body is
    flat paint with hand-wobbled cloud edges and a dark keyline. The only thing
    giving it roundness is a flat crescent terminator, not a ramp.
    warm=True shifts the strata toward the amber/ember heat end."""
    cx, cy, r = int(cx), int(cy), int(r)

    base = (176, 152, 120) if warm else (128, 140, 148)
    light = (226, 206, 172) if warm else (216, 226, 230)
    dark = (120, 92, 68) if warm else (84, 98, 110)
    shade = (58, 34, 22) if warm else (34, 46, 58)

    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)

    # full-width strata, bottom to top, alternating light / base / dark. The
    # tonal spread is deliberately WIDE: at close to one value the bands merge
    # into a single grey mass and the giant stops reading as a gas giant at all.
    n = max(2, int(band_count))
    span = 2.0 * r
    h = span / n
    tones = [light, base, dark, light, base, dark]
    for i in range(n):
        y0 = cy - r + i * h
        # a wobbled cloud edge: a long, low-frequency wave across the full width
        edge = []
        for j in range(11):
            x = -40 + (W + 80) * j / 10.0
            edge.append((x, y0 + 6.0 * math.sin(1.1 * j + i * 1.7 + seed)))
        edge += [(W + 40, y0 + h + 40), (-40, y0 + h + 40)]
        ld.polygon(edge, fill=tones[i % len(tones)] + (255,))

    # clip every stratum to a hard disc — this is what makes it a SPHERE
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    lay.putalpha(ImageChops.multiply(lay.split()[3], mask))
    img = Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

    # the flat terminator: a crescent of shadow on the lower-left, hand-wobbled.
    # Flat paint, no ramp — it is a shadow SHAPE, which is Register P language.
    tlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tlay)
    crescent = []
    for j in range(19):
        a = math.radians(108.0 + 204.0 * j / 18.0)
        crescent.append((cx + r * 1.02 * math.cos(a),
                         cy + r * 1.02 * math.sin(a)))
    inner = []
    for j in range(19):
        a = math.radians(108.0 + 204.0 * j / 18.0)
        rr = r * 0.60
        inner.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    K.draw_smooth(td, crescent + inner[::-1], fill=shade + (58,), outline=None,
                  seed=seed + 3, wobble=5.0, wavelength=200.0, closed=True)
    tlay.putalpha(ImageChops.multiply(tlay.split()[3], mask))
    img = Image.alpha_composite(img.convert('RGBA'), tlay).convert('RGB')

    # spray-paint grain inside the disc. Density is deliberately tiny: at 0.02 over
    # a body this size it stopped reading as paint speckle and started reading as
    # digital noise, which flattened the strata it was meant to sit on top of.
    d = ImageDraw.Draw(img, 'RGBA')
    K.stipple(d, cx - r * 0.92, cy - r * 0.92, cx + r * 0.92, cy + r * 0.92,
              shade, seed=seed + 5, density=0.0022, r=1, spread=1)

    # the dark keyline the reference keeps on every planet
    K.draw_disc(d, cx, cy, r, fill=None, outline=INK, width=K.OUTLINE,
                seed=seed + 7, wobble=2.6)
    return img


def _balloon_strata(img, cx, cy, r, seed, alpha=52, n=4):
    """Faint horizontal cloud strata clipped inside a disc, WITHOUT the keyline.

    Used by beat 5's balloon, which must read as a body too thin to have surface
    detail worth an outline. Deliberately built on the same full-width-wobbled-
    band-then-clip trick as `_gas_giant`, so it can never produce the concentric
    rings that would make a small disc read as a target."""
    cx, cy, r = int(cx), int(cy), int(r)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    h = 2.0 * r / n
    for i in range(n):
        y0 = cy - r + i * h
        edge = []
        for j in range(11):
            x = -40 + (W + 80) * j / 10.0
            edge.append((x, y0 + 3.2 * math.sin(1.1 * j + i * 1.7 + seed)))
        edge += [(W + 40, y0 + h + 40), (-40, y0 + h + 40)]
        ld.polygon(edge, fill=BONE + (alpha,))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    lay.putalpha(ImageChops.multiply(lay.split()[3], mask))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _hero(draw, text, cx, cy, color, px=HERO_PX, stroke=3, y_max=HERO_Y_MAX):
    """The one dominant on-card phrase. Always via C.hero_word, so it is clamped
    inside the frame INCLUDING its 3px keyline and auto-shrinks a long phrase
    rather than running off. The phrase must add a fact, never restate the
    caption."""
    return C.hero_word(draw, text, cx, cy, fill_rgb=color, stroke_rgb=INK,
                       stroke_width=stroke, px=px, margin=40, y_max=y_max)


def _void_card(card, planet, seed, stars=124):
    """A void (space-register) frame. Gradient legal only via the starfield
    backdrop built into void_backdrop and the emissive _star added by callers."""
    img = Image.new('RGB', (W, H), DEEP)
    _void_field(img, seed=seed, stars=stars)
    return img


def _cream_card(card, planet):
    """A cream (paint-register) frame: full-bleed bone-cream paper, header
    floats on it (no visible band edge)."""
    return Image.new('RGB', (W, H), PAPER)


def _finish(img, card, planet, paper_band, dark_bg):
    """Layout-A tail shared by every card: the 84px title strip, then the
    schedule-driven character, then the one floating caption call."""
    C._header(img, planet, paper_band=paper_band)
    theme = 'dark' if dark_bg else 'light'
    C._draw_stickman(img, card, theme=theme)
    C._caption(img, card['caption'], 70, 652, dark_bg=dark_bg)
    return img


# ===========================================================================
# BEAT 1 — backwards_hook (VOID). The opening: the giant and the wrong-way arrow
# ===========================================================================

def render_backwards_hook(card, planet=PLANET):
    """VOID. The gas giant fills the right half as a painterly marbled sphere
    (C.space_body, no black outline) and one FAT hand-drawn arrow curls
    BACKWARDS around it — the arrowhead at the tail, pointing the wrong way, is
    the whole beat. The character stands at lower left, flat/deadpan, watching
    the arrow.

    The arrow is a filled region (via _thick_curve), not a wide PIL line, so it
    has clean edges and no nubs. Retrograde spins counter-clockwise in math, which
    on screen (y growing downward) is CLOCKWISE; the arrowhead is placed at the
    end of the sweep so the reversal is unmistakable against the caption."""
    img = _void_card(card, planet, seed=101, stars=128)

    gx, gy, gr = 838, 344, 188
    img = _gas_giant(img, gx, gy, gr, seed=101, band_count=5)
    d = ImageDraw.Draw(img, 'RGBA')
    # a flat limb ring so the giant's edge reads against the starfield
    _flat_ring(d, gx, gy, gr + 3, BONE, 150, K.FINE)

    # the backwards spin arrow: a wide arc curling around the giant's equator,
    # swept clockwise on screen — the retrograde direction.
    arrow = []
    for i in range(37):
        a = math.radians(16.0 + 306.0 * i / 36.0)
        arrow.append((gx + (gr + 66) * math.cos(a),
                      gy + (gr + 66) * 0.56 * math.sin(a)))
    _thick_curve(d, arrow, AMBER, seed=102, width=13, wobble=2.0)
    _arrow_head(d, arrow[-1], 128.0, AMBER, size=26, seed=103)
    # a short tick at the start of the sweep marks where it begins, so the
    # direction reads even without tracing the head
    _vline(d, arrow[0][0], arrow[0][1] - 15, arrow[0][1] + 15, AMBER,
           width=K.DETAIL, seed=104, wobble=0.8)

    # NO hero plate on this beat. The caption already says "the wrong way", so a
    # plate saying THE WRONG WAY would merely restate it — the defect the canon
    # addendum calls out by name. What the caption does NOT say is the word for
    # it, so that is the annotation: RETROGRADE, stamped on the arrow itself.
    _stamp(d, 'RETROGRADE', 214, 566, BONE, ink=INK)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 2 — everyone_else_turns (CREAM). The normal case, drawn for contrast
# ===========================================================================

def render_everyone_else_turns(card, planet=PLANET):
    """CREAM, Register P. One amber star at center with six small planets on tidy
    orbit ellipses, five carrying same-direction arrowheads and one — the last,
    nearest the camera — carrying a REVERSED arrowhead and a bone ring so it is
    findable without hunting. The character is at the right edge, shrugging,
    zigzag mouth, uncomfortable.

    The one thing wrong in the frame is one arrowhead out of six. That is the
    point of the card, so everything else stays quiet, flat and tidy. The star is
    a flat amber disc here — matte, small, and deliberately NOT the emissive
    gradient, which is reserved for the void cards."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    # The orbit system is sized to live ENTIRELY inside the art area: the outer
    # ring bottoms out at y ~ 596, clear of the caption at 652, and its right
    # edge stops at x ~ 930 so it never runs under the character, who stands at
    # the right edge per the beat's visual brief.
    cx, cy = 470, 372
    K.draw_disc(d, cx, cy, 42, fill=AMBER, outline=INK, width=K.OUTLINE,
                seed=201, wobble=2.0)

    # six planets, two per orbit ring, spread over the ellipse
    # The exception is the SECOND planet of the middle ring, placed low-left where
    # there is genuine empty cream to put its label and its leader, rather than
    # out on the outer ring where the arrowhead lands on the frame edge.
    planets = [(212, 34.0), (212, 214.0), (322, 146.0), (322, 300.0),
               (430, 46.0), (430, 210.0)]
    retro_px = retro_py = 0
    for k, (rad, ang_deg) in enumerate(planets):
        ry = rad * 0.52
        _flat_ellipse(d, cx, cy, rad, ry, INK, 185, K.DETAIL)
        a = math.radians(ang_deg)
        px = cx + rad * math.cos(a)
        py = cy + ry * math.sin(a)
        retro = (k == 3)                      # the one backwards world
        K.draw_disc(d, int(px), int(py), 18, fill=TEAL, outline=INK,
                    width=K.DETAIL, seed=210 + k, wobble=1.6)
        if retro:
            retro_px, retro_py = int(px), int(py)
            _flat_ring(d, retro_px, retro_py, 28, AMBER, 235, K.DETAIL)
        # arrowhead tangent to the ring: +90 = clockwise on screen (the norm),
        # -90 = the retrograde exception, which is the whole point of this card.
        # The tip sits BEHIND the planet along its own tangent, not ahead, so no
        # head is ever pushed off the near frame edge.
        sign = -1.0 if retro else 1.0
        tangent = ang_deg + (90.0 if not retro else -90.0)
        tip = (cx + rad * math.cos(a + math.radians(24) * sign),
               cy + ry * math.sin(a + math.radians(24) * sign))
        _arrow_head(d, tip, tangent, AMBER if retro else INK, size=19,
                    seed=220 + k)

    # the label sits ON the exception with a short leader, aimed down into the
    # empty cream below the system — the reference's habit of putting the word
    # against the thing it names, without a line crossing the art
    _open_curve(d, [(retro_px - 22, retro_py + 16), (retro_px - 40, retro_py + 56),
                    (retro_px - 52, retro_py + 96)], INK, K.FINE, seed=230)
    _tiny(d, 'WRONG WAY', retro_px - 52, retro_py + 118, INK, px=18)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 3 — not_made_here (VOID). The arrival: a streak and a ghosted birthplace
# ===========================================================================

def render_not_made_here(card, planet=PLANET):
    """VOID. The gas giant STREAKS in from off-frame upper right on a jagged
    amber diagonal, its birthplace ghosted far away as a DASHED empty circle. The
    character is at lower right pointing up the path, awed.

    The birthplace is a dashed circle of short flat arcs, so it reads as an
    absence rather than a planet. The streak is a jagged filled band — flat, no
    gradient — with a faint ember wake offset behind it. The hero adds the fact
    this card is actually about rather than restating the caption."""
    img = _void_card(card, planet, seed=301, stars=118)
    d = ImageDraw.Draw(img, 'RGBA')

    # the ghosted birthplace: short flat arcs around an empty circle, upper left
    bx, by, br = 268, 214, 88
    for i in range(14):
        a0 = 360.0 * i / 14.0 + 7.0
        d.arc([bx - br, by - br, bx + br, by + br], a0, a0 + 13.0,
              fill=BONE + (135,), width=K.DETAIL)
    _tiny(d, 'BIRTHPLACE', bx, by - br - 22, BONE, px=17, ink=INK)

    # the streak: a jagged amber band arriving from off-frame upper right
    streak = [(1290, 118), (1128, 196), (972, 252), (828, 330), (688, 372),
              (548, 436), (424, 478)]
    wake = [(p[0] + 24, p[1] + 28) for p in streak]
    _thick_curve(d, wake, EMBER, seed=303, width=9, wobble=3.0, wavelength=110.0)
    _thick_curve(d, streak, AMBER, seed=302, width=17, wobble=3.0, wavelength=110.0)

    # the giant, arriving at the head of the streak
    gx, gy, gr = 318, 502, 76
    img = _gas_giant(img, gx, gy, gr, seed=304, band_count=3)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, gx, gy, gr + 3, BONE, 160, K.FINE)

    # NO hero word on this card. The dashed BIRTHPLACE label, the streak and the
    # arriving giant already carry the one idea, and every free region of this
    # layout is either the character (lower right, per the visual brief) or the
    # streak itself. A plate stamped into one of those would either collide with
    # him or sit on the art it is describing. One idea per card.

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 4 — wrong_way_explained (CREAM). Two stamp boxes: CAPTURED, FLUNG
# ===========================================================================

def render_wrong_way_explained(card, planet=PLANET):
    """CREAM, Register P. Two rough INKED stamp boxes up top, labeled CAPTURED
    and FLUNG, each holding a tiny careless sketch — a world reeled in on a taut
    line, a world thrown off an escape arc — and the character below them
    pointing at the left box, deadpan.

    The boxes are smooth wobbled frames with the canonical K.OUTLINE keyline, not
    crisp CAD rectangles: midpoints sit on each edge so the closed Catmull-Rom
    rounds the corners instead of ballooning the rectangle into a potato.
    Everything inside is a flat fill. No hero word — the two box labels already
    carry the words and a third line would restate the caption."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    def box(cx, top, label, sketch_fn, seed):
        x0, x1 = cx - 224, cx + 224
        y0, y1 = top, top + 268
        K.draw_outline(d, [(x0 + 48, y0), (cx, y0), (x1 - 48, y0),
                           (x1, y0 + 48), (x1, (y0 + y1) / 2), (x1, y1 - 48),
                           (x1 - 48, y1), (cx, y1), (x0 + 48, y1),
                           (x0, y1 - 48), (x0, (y0 + y1) / 2), (x0, y0 + 48)],
                       color=INK, width=K.OUTLINE, closed=True, seed=seed,
                       wobble=2.4, wavelength=190.0)
        sketch_fn(cx, y0, y1, seed + 5)
        _stamp(d, label, cx - 56, y1 - 40, AMBER, ink=INK, px=T.LABEL_PX, bold=True)

    def sketch_captured(cx, y0, y1, sd):
        # a world reeled in on a taut line: star on the right, the planet hauled
        # toward it along a line with an arrowhead. Drawn large enough to fill the
        # box — the boxes ARE the subject of this card, so the sketches cannot be
        # incidental.
        K.draw_disc(d, cx + 118, y0 + 92, 30, fill=AMBER, outline=INK,
                    width=K.OUTLINE, seed=sd + 1, wobble=1.8)
        _open_curve(d, [(cx + 34, y0 + 112), (cx - 12, y0 + 122),
                        (cx - 66, y0 + 116)], INK, K.DETAIL, seed=sd + 2)
        _arrow_head(d, (cx + 34, y0 + 112), 168.0, INK, size=22, seed=sd + 3)
        K.draw_disc(d, cx - 116, y0 + 114, 40, fill=TEAL, outline=INK,
                    width=K.OUTLINE, seed=sd, wobble=1.8)

    def sketch_flung(cx, y0, y1, sd):
        # a world thrown off an escape arc: it leaves the star and climbs away.
        K.draw_disc(d, cx - 132, y0 + 104, 28, fill=AMBER, outline=INK,
                    width=K.OUTLINE, seed=sd, wobble=1.8)
        arc = [(cx - 78 + i * 19, y0 + 132 - i * i * 2.0) for i in range(9)]
        _open_curve(d, arc, INK, K.DETAIL, seed=sd + 1)
        _arrow_head(d, arc[-1], -44.0, INK, size=22, seed=sd + 3)
        K.draw_disc(d, cx + 122, y0 + 40, 36, fill=TEAL, outline=INK,
                    width=K.OUTLINE, seed=sd + 2, wobble=1.8)

    box(372, 118, 'CAPTURED', sketch_captured, 400)
    box(908, 118, 'FLUNG', sketch_flung, 420)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 5 — almost_nothing_there (VOID). A balloon inside its own oversized ring
# ===========================================================================

def render_almost_nothing_there(card, planet=PLANET):
    """VOID. The reveal: the gas giant drawn as a THIN, FAINT balloon outline
    inside its own oversized orbit ring, with most of the ring's interior empty
    black. The emptiness IS the fact — the ring is where a Jupiter-sized world
    should be solid matter, and there is nearly nothing in it. The character is at
    lower left, hands up, scared.

    The balloon is a flat teal disc at low alpha with a thin bone limb ring: a
    shape color at a low alpha, never a gradient. Nothing is filled in the ring's
    empty interior. The hero states the measurement, not the caption's mood."""
    img = _void_card(card, planet, seed=501, stars=120)

    d = ImageDraw.Draw(img, 'RGBA')
    cx, cy = 760, 336
    # the oversized ring: most of its interior is left as empty starfield
    _flat_ellipse(d, cx, cy, 350, 214, BONE, 165, K.DETAIL)

    # the balloon: thin and faint — a low-alpha flat teal disc, deliberately
    # NOT a gradient, with a thin bone limb ring at the edge
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, cx, cy, 104, fill=TEAL + (78,), outline=None, width=0,
                seed=510, wobble=3.0)
    _flat_ring(d, cx, cy, 104, BONE, 205, K.DETAIL)
    # Faint horizontal strata clipped to the balloon, so it reads as a barely-
    # there body rather than a flat sticker — and, critically, NOT as a set of
    # concentric ellipses. Concentric rings inside a small disc are a bullseye,
    # which is the exact defect the STYLE_CANON addendum names for small bodies.
    img = _balloon_strata(img, cx, cy, 104, seed=510, alpha=86)
    d = ImageDraw.Draw(img, 'RGBA')   # _balloon_strata returns a NEW image; rebind

    # the label sits INSIDE the empty part of the ring, directly on the balloon's
    # upper limb, so it neither crosses the orbit ellipse nor approaches the frame
    # edge the way the old outboard leader did
    _tiny(d, 'ALMOST EMPTY', cx - 96, cy - 132, BONE, px=18, ink=INK)
    _open_curve(d, [(cx - 6, cy - 122), (cx + 2, cy - 104), (cx + 4, cy - 88)],
                BONE, K.FINE, seed=511, wobble=1.0)

    _hero(d, 'MADE OF ALMOST NOTHING', cx, 596, AMBER, px=48, y_max=614)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 6 — cork_density (CREAM). The seesaw
# ===========================================================================

def render_cork_density(card, planet=PLANET):
    """CREAM, Register P. A wine cork at left and a Jupiter-sized planet silhouette
    at right, both sitting on a thin seesaw beam that BARELY dips under the planet.
    The beam not dipping is the entire fact: the giant weighs almost nothing.

    Both objects are flat fills with the canonical K.OUTLINE keyline. The beam is a
    straight hand-wobbled plank on a triangular fulcrum, tipped only ~5 degrees — an
    obvious-but-shallow dip reads as weightless, a steep one would read as broken.

    The fulcrum sits well LEFT of center (x=470) because this beat's visual brief
    puts the character beside the beam and centred on the frame; at x=640 the
    triangle sat exactly where he stands and the two fought. It is also drawn
    BEFORE the beam so the plank reads as resting on top of it, not behind it."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    fulcrum_x, pivot_y = 470, 476

    # the fulcrum: a flat wedge, drawn first so the beam overlaps its apex. A
    # polygon, not K.draw_smooth — a 3-point closed spline rounds the apex into a
    # leaf/blade, which read as a shield rather than as the pivot of a seesaw.
    fulcrum = [(fulcrum_x - 66, pivot_y + 120), (fulcrum_x - 22, pivot_y),
               (fulcrum_x + 22, pivot_y), (fulcrum_x + 66, pivot_y + 120)]
    d.polygon(fulcrum, fill=TEAL + (255,))
    K.draw_outline(d, fulcrum, INK, K.OUTLINE, seed=601, wobble=2.0)

    # the beam: tipped only ~4 degrees, and it dips TOWARD the planet — the planet's
    # weight should press its end down, so the right end sits lower than the left.
    # (The first pass had it backwards, planet end high, which reads as the cork
    # being heavy.) Object heights are then derived from the real beam line.
    tip = math.radians(4.0)
    bx0, by0 = fulcrum_x - 392, pivot_y - 392 * math.tan(tip)   # left end, high
    bx1, by1 = fulcrum_x + 676, pivot_y + 676 * math.tan(tip)   # right end, low

    def beam_y(x):
        return pivot_y + (x - fulcrum_x) * math.tan(tip)

    _thick_curve(d, [(bx0, by0), (fulcrum_x, pivot_y), (bx1, by1)],
                 AMBER, seed=602, width=17, wobble=1.6, wavelength=200.0)

    # left: the cork. A real cork is a squat truncated cone — WIDE flat head on
    # top, tapering DOWN to a narrower rounded base, roughly 1:1 in width and
    # height. The first pass was a plain rounded rectangle (a pill), the second
    # put the taper the wrong way and made it read as a nail. Squat and wide at
    # the head is what separates it from both.
    cork_x = fulcrum_x - 320
    cork_y = beam_y(cork_x) - 56
    cork = [(cork_x - 46, cork_y - 56), (cork_x + 46, cork_y - 56),
            (cork_x + 38, cork_y - 34), (cork_x + 30, cork_y + 44),
            (cork_x + 16, cork_y + 58), (cork_x - 16, cork_y + 58),
            (cork_x - 30, cork_y + 44), (cork_x - 38, cork_y - 34)]
    d.polygon(cork, fill=TEAL + (255,))
    K.draw_outline(d, cork, INK, K.OUTLINE, seed=603, wobble=2.4)
    # the collar band a real cork has just under the head
    _hrule(d, cork_y - 26, cork_x - 40, cork_x + 40, INK, K.DETAIL, seed=604)
    _tiny(d, 'CORK', cork_x, cork_y + 86, INK, px=18)

    # right: a Jupiter-sized SILHOUETTE on the low end of the beam. The brief calls
    # it a silhouette, so it is a flat INK disc — dark against the cream paper,
    # which is the one thing that reads at a glance as a heavy body. Its surface
    # is horizontal strata clipped inside the disc, not concentric ellipses (the
    # bullseye trap), drawn in BONE so they read against the ink.
    jx, jr = fulcrum_x + 610, 78
    jy = beam_y(jx) - jr - 6
    K.draw_disc(d, jx, jy, jr, fill=INK, outline=INK, width=K.OUTLINE,
                seed=605, wobble=3.0)
    img = _balloon_strata(img, jx, jy, jr, seed=606, alpha=150, n=4)
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_disc(d, jx, jy, jr, fill=None, outline=INK, width=K.OUTLINE,
                seed=607, wobble=3.0)
    _tiny(d, 'JUPITER-SIZED', jx, jy + 100, INK, px=18)

    # INK, not amber. PALETTE_SPEC §1 fixes amber-on-cream at ~1.8:1 and lists it
    # as forbidden: on a cream card every glyph is slate-black.
    _hero(d, 'HEAVY PLANET, NO WEIGHT', fulcrum_x + 130, 196, INK, px=48, y_max=286)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 7 — should_have_collapsed (VOID). Torn onion contours on a hot core
# ===========================================================================

def render_should_have_collapsed(card, planet=PLANET):
    """VOID, the tension beat. The giant's outer layers are drawn as torn onion
    CONTOURS pressing inward on a small red-orange core, with cracks spidering
    across the shell. The character is at the far left shielding his eyes, scared.

    The core is the emissive body (C._radial_core, the one legal gradient): small,
    white-hot, with a real circular halo, which is what the STYLE_CANON addendum
    requires of an emissive core. The onion contours are closed smooth wobbled
    rings at low alpha — FLAT, never gradient — and each is cracked, so the shell
    reads as being squeezed rather than as clean shells. The hero states the
    reason, which the caption only implies."""
    img = _void_card(card, planet, seed=701, stars=104)

    cx, cy = 700, 330

    # the crushed core: the one legal gradient, and it is the SUBJECT here, so it
    # is big enough to read as a heat source rather than as an orange speck. The
    # old r=54 disc was dwarfed by five rings and read as dirt on the lens.
    d = ImageDraw.Draw(img, 'RGBA')
    _star(img, cx, cy, 96, seed=701)

    # the onion contours pressing inward. FOUR, not five, and each drawn at
    # K.DETAIL rather than as a hairline: five thin rings around a small core read
    # as a spiderweb/target. Fewer, heavier, more irregular arcs read as shell.
    d = ImageDraw.Draw(img, 'RGBA')
    for k, (rad, alpha, col) in enumerate(((146, 220, BONE), (206, 165, BONE),
                                           (266, 112, BONE), (322, 64, BONE))):
        # a wobbled closed ring, drawn as a thick curve around the circumference
        ring = []
        for s in range(24):
            a = math.tau * s / 24.0
            rr = rad * (1.0 + 0.075 * math.sin(3 * a + k * 1.3)
                        + 0.030 * math.sin(5 * a - k * 0.7))
            ring.append((cx + rr * math.cos(a), cy + rr * 0.94 * math.sin(a)))
        _thick_curve(d, ring + [ring[0]], BONE + (alpha,), seed=710 + k,
                     width=K.DETAIL, wobble=3.0, wavelength=200.0)
        # tear a wedge out of the ring so it reads as a torn shell rather than a
        # clean shell; two tears on the outer rings, one on the inner
        for tear in range(2 if k >= 2 else 1):
            ta = math.radians(58.0 + k * 47.0 + tear * 176.0)
            w = 0.17
            gap = []
            for j in range(7):
                a = ta - w + 2 * w * j / 6.0
                gap.append((cx + rad * 1.16 * math.cos(a),
                            cy + rad * 1.10 * math.sin(a)))
            _thick_curve(d, gap, DEEP + (255,), seed=740 + k * 3 + tear,
                         width=K.DETAIL + 3, wobble=1.2)

    # cracks spidering out of the core across the shell
    for k, (a_deg, ln) in enumerate(((28, 230), (140, 265), (250, 215))):
        a = math.radians(a_deg)
        crack = [(cx + 96 * math.cos(a), cy + 96 * 0.94 * math.sin(a))]
        for j in range(1, 6):
            t = j / 5.0
            rr = 96 + ln * t
            jag = math.radians(18 * math.sin(j * 1.7 + k))
            crack.append((cx + rr * math.cos(a + jag * 0.4),
                          cy + rr * 0.94 * math.sin(a + jag * 0.4)))
        _open_curve(d, crack, AMBER, K.DETAIL, seed=730 + k, wobble=1.6)

    # NO hero plate. Both caption lines already name the collapse and the heat, so
    # any plate here would restate them. The shell and the core are the argument.
    _stamp(d, 'HELD OPEN BY HEAT ALONE', cx, 596, BONE, ink=INK)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 8 — cloud_wall (CREAM). The towering stack
# ===========================================================================

def render_cloud_wall(card, planet=PLANET):
    """CREAM, Register P. A towering vertical stack of flat cloud bands fills
    nearly the whole frame, with small arrows drifting sideways along every band —
    the bands are the "wall of weather". The character is at bottom left, head
    tipped straight back, awed, looking up.

    The bands are alternating flat fills (teal / bone / amber) with K.OUTLINE
    keylines, stacked bottom to top, each one wider than it is tall so it reads as
    cloud strata and not as a stack of bricks. Every band carries a small drift
    arrow, which is what makes the stack read as MOVING air rather than as a layer
    cake. No hero word — the caption already says it and the band arrows are the
    picture.

    Each band is built as a POLYGON, not through K.draw_smooth. Feeding a slab to
    a closed Catmull-Rom rounds its four corners into points, so the bands came
    out as a stack of lens/blimp shapes with sharp spiky tips — a CAD read, not
    cloud. A polygon keeps the ends vertical and lets only the long top and bottom
    edges carry a low-frequency paint wobble."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    # the cloud stack: bands of alternating flat fill, widest at the bottom
    band_tops = [520, 462, 402, 340, 276, 212, 150, 108]
    cols = [TEAL, BONE, AMBER, TEAL, BONE, AMBER, TEAL, BONE]
    for k, (ytop, col) in enumerate(zip(band_tops, cols)):
        ybot = band_tops[k - 1] if k > 0 else 700
        inset = 26 + k * 22
        x0, x1 = inset, W - inset
        # only the long horizontal edges wobble, and only at low frequency; the
        # end caps stay vertical so the slab reads as a slab
        top_edge = [(x0 + (x1 - x0) * j / 8.0,
                     ytop + 7.0 * math.sin(j * 0.9 + k * 1.7)) for j in range(9)]
        bot_edge = [(x1 - (x1 - x0) * j / 8.0,
                     ybot - 7.0 * math.sin(j * 0.9 + k * 1.7 + 0.6))
                    for j in range(9)]
        slab = top_edge + [(x1, ytop + 4)] + bot_edge + [(x0, ybot - 4)]
        d.polygon(slab, fill=col + (255,))
        K.draw_outline(d, top_edge + [(x1, ytop + 4)] + bot_edge + [(x0, ybot - 4)],
                       INK, K.OUTLINE, seed=800 + k, wobble=2.2, closed=True)
        # a small drift arrow along each band — the motion that makes it air
        ymid = (ytop + ybot) / 2.0
        ax = 130 + k * 16
        _hrule(d, ymid, ax, ax + 84, INK, K.DETAIL, seed=820 + k, wobble=1.0)
        _arrow_head(d, (ax + 84, ymid), 0.0, INK, size=16, seed=840 + k)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 9 — endless_wind (VOID). The ribbon around the day side
# ===========================================================================

def render_endless_wind(card, planet=PLANET):
    """VOID. Long looping wind streamlines wrap the giant's day side in a dense
    ribbon of arrowheads, ALL sweeping the same way — a closed circulation, which
    is what "the whole atmosphere just runs, endlessly, around the day side"
    looks like as a picture. The character braces at lower left, uncomfortable.

    The streamlines are open smooth curves (via _open_curve, since the lib's
    open path is broken) at K.FINE in bone, each ending in its own arrowhead, all
    packed into a band that hugs the planet's sunward limb. No gradient anywhere
    on this card: the planet is matte strata, the wind is linework."""
    img = _void_card(card, planet, seed=901, stars=96)
    d = ImageDraw.Draw(img, 'RGBA')

    gx, gy, gr = 730, 356, 172
    img = _gas_giant(img, gx, gy, gr, seed=901, band_count=5)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, gx, gy, gr + 3, BONE, 150, K.FINE)

    # The wind ribbon. The earlier passes kept building this as full nested ellipses
    # around the planet — seven of them, then four — and no matter how they were
    # spaced they read as a BULLSEYE: concentric rings are the target shape, and
    # the STYLE_CANON addendum names exactly that for a body this size. Reducing
    # the count made it cleaner but still concentric.
    #
    # What actually says "circulating air" is a set of streamlines at DIFFERENT
    # heights and tilts, each an OPEN arc that sweeps part-way around the sunward
    # limb and then leaves the frame — never a closed ring, never two at the same
    # radius. Four arcs, staggered vertically and each rotated a little further,
    # all pointing the same way (day-side flow), tails trailing off the night side.
    for k in range(4):
        ry = gr * (0.30 + k * 0.34)                 # four distinct heights
        tilt = math.radians(-13.0 + k * 9.0)        # each tilted a little more
        start = math.radians(196.0 - k * 11.0)
        sweep = math.radians(232.0 - k * 9.0)
        arc = []
        for s in range(26):
            a = start + sweep * s / 25.0
            lx = (gr + 62 + k * 30) * (1.0 + 0.16 * math.cos(a))
            arc.append((gx + lx * math.cos(a) * 0.94,
                        gy + ry * math.sin(a) + (lx * math.sin(a)) * math.tan(tilt)))
        _open_curve(d, arc, BONE, K.DETAIL, seed=910 + k, wobble=2.2,
                    wavelength=170.0)
        # the arrowhead rides the END of the arc, so all four heads sit at four
        # different points on the flow rather than piling on one spot
        _arrow_head(d, arc[-1], math.degrees(start + sweep) + 88.0, BONE,
                    size=19, seed=930 + k)

    # "NEVER STOPS" restated the caption's own words; this states the WRONGNESS
    # instead, which the caption only asserts ("faster than anything that size
    # should") without measuring.
    _hero(d, 'FASTER THAN IT SHOULD BE', gx, 596, BONE, px=48, y_max=614)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 10 — dayside_1700 (CREAM). The temperature column
# ===========================================================================

def render_dayside_1700(card, planet=PLANET):
    """CREAM, Register P. One FAT hand-drawn temperature column, filled to the
    top, labelled 1700 C, with heat squiggles rising off it and a tiny planet
    pressed against its left edge. The character stands motionless beside it,
    scared.

    The column is a straight-sided wobbled slab filled flat amber with a
    K.OUTLINE keyline and a bone centre line, so it reads as a filled thermometer.
    It is built as a POLYGON for the same reason the cloud-wall bands are: run a
    rectangle through a closed Catmull-Rom with edge midpoints and the sides bow
    inward, which turned the column into a concave "vase". Only the long edges
    wobble here, at low frequency.

    The squiggles are clamped to the art area. The old ones started at y=136 and
    rose 150px, so the middle one left the top of the frame entirely. The 1700 C
    stamp sits ON the column, per the reference's label-on-subject habit."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    col_x, col_w = 620, 96
    top, bot = 214, 604
    # the outer column, filled to the top: vertical end caps, wobbled long edges.
    # Wound in ONE direction — down the left, across the bottom, up the right,
    # back across the top. The earlier order (left, TOP, right, bottom) made a
    # bowtie and left a notch at the base of the column.
    left = [(col_x - col_w + 4.0 * math.sin(j * 0.9 + 1.3),
             top + (bot - top) * j / 5.0) for j in range(6)]
    cap_b = [(col_x - col_w + (2 * col_w) * j / 6.0,
              bot - 5.0 * math.sin(j * 1.1 + 0.8)) for j in range(7)]
    right = [(col_x + col_w - 4.0 * math.sin(j * 0.9 + 0.4),
              bot - (bot - top) * j / 5.0) for j in range(6)]
    cap_t = [(col_x + col_w - (2 * col_w) * j / 6.0,
              top + 5.0 * math.sin(j * 1.1)) for j in range(7)]
    col_poly = left + cap_b + right + cap_t
    d.polygon(col_poly, fill=AMBER + (255,))
    K.draw_outline(d, col_poly, INK, K.OUTLINE, seed=1001, wobble=2.0, closed=True)

    # the mercury centre line, filled to the top too (it reads 1700, i.e. full)
    _vline(d, col_x, top + 14, bot - 14, BONE, width=K.OUTLINE, seed=1002, wobble=0.8)

    # tick marks up the right side of the column, so it reads as a scale
    for k in range(6):
        ty = bot - 22 - k * ((bot - top - 60) / 5.0)
        _hrule(d, ty, col_x + col_w - 30, col_x + col_w - 8, INK, K.FINE, seed=1005 + k)

    # heat squiggles rising off the top, all clamped to stay inside the art area
    for k, (sx, ln) in enumerate(((col_x - 52, 74), (col_x, 96), (col_x + 52, 74))):
        sq = []
        for j in range(7):
            t = j / 6.0
            sq.append((sx + 14 * math.sin(j * 1.3 + k), top - 12 - ln * t))
        _open_curve(d, sq, EMBER, K.DETAIL, seed=1010 + k, wobble=1.4)

    # the label ON the column, per the reference's label-on-subject habit
    _tiny(d, '1700 C', col_x, top + 56, INK, px=30)

    # a tiny planet pressed against the column's left edge, for scale
    K.draw_disc(d, col_x - col_w - 58, bot - 44, 34, fill=TEAL, outline=INK,
                width=K.OUTLINE, seed=1020, wobble=2.4)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 11 — you_would_not (VOID). The fate beat: almost empty
# ===========================================================================

def render_you_would_not(card, planet=PLANET):
    """VOID, the FATE beat per CLAUDE.md 10.8. Almost an empty starfield with one
    very SMALL planet far off-center and a lot of dead space around it — the
    absence of anything you could land on is the picture. The character is small,
    lower center, taking one step backward, hands up, scared.

    The emptiness is the composition: the planet is deliberately tiny and pushed
    far off-center so most of the frame is bare starfield. The one hero word is
    the smallest on the segment, because there is almost nothing to say about a
    place you would not go. Deliberately quiet, on the beat where the narrator
    stacks three "you would not"s."""
    img = _void_card(card, planet, seed=1101, stars=70)   # fewer stars: emptier

    # a very small planet, far off-center upper right
    gx, gy, gr = 980, 250, 40
    img = _gas_giant(img, gx, gy, gr, seed=1101, band_count=2)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, gx, gy, gr + 3, BONE, 150, K.FINE)

    # NO hero plate on the fate beat, deliberately. This is the emptiest card in the
    # segment and the narrator stacks three refusals on it; a title plate here
    # would fill the frame the beat exists to empty out, and at any size wide
    # enough to read it ran straight through the character. The dead space is the
    # picture — there is nothing here you could land on.

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# BEAT 12 — three_wrongs (CREAM). The checklist
# ===========================================================================

def render_three_wrongs(card, planet=PLANET):
    """CREAM, Register P. Three short checklist lines stacked at the left, each
    ticked off in ink, and the character at the right shrugging, deadpan. This is
    the recap, and it restates three facts deliberately — but it does so as
    CHECKMARKS on a list, not as a hero word, so it is a different idea from every
    preceding card rather than a title card restating them.

    The rules are K.OUTLINE, not K.DETAIL. At 4px on a cream card with cream
    showing through, three short rules under three short labels read as an
    under-scaled wire diagram against the canon's 6px large-shape linework. The
    item text is set at CAPTION_PX — the locked caption size — rather than at
    STAMP_PX, because these are the card's three ideas and not diagram
    annotations; a 15px stamp was unreadable at 720p."""
    img = _cream_card(card, planet)
    d = ImageDraw.Draw(img, 'RGBA')

    items = ['WRONG WAY', 'ALMOST NO WEIGHT', 'ENDLESS WIND']
    for k, txt in enumerate(items):
        y = 268 + k * 132
        # a hand-drawn tick: a short down stroke then a longer up stroke, in amber
        # so it reads as the "marked" state against the ink text
        tick = [(168, y - 34), (188, y - 12), (222, y - 58)]
        _thick_curve(d, tick, AMBER, seed=1210 + k, width=9, wobble=1.0)
        # the checklist rule, at full large-shape weight
        _hrule(d, y, 120, 620, INK, K.OUTLINE, seed=1200 + k, wobble=1.6)
        # the item text SITS ON its rule — the bottom of the 28px glyphs rests just
        # above it. At CAPTION_PX the earlier y-22 put the rule straight through
        # the middle of every word, which read as strikethrough rather than as a
        # list.
        _stamp(d, txt, 264, y - 36, INK, px=T.CAPTION_PX, bold=True)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ===========================================================================
# BEAT 13 — never_supposed_to_be_here (VOID). The closer
# ===========================================================================

def render_never_supposed_to_be_here(card, planet=PLANET):
    """VOID, the closer. The gas giant ALONE and SMALL at the center of a wide
    empty starfield, one faint retrograde arrow looping it, and the character at
    lower left standing with hands lowered, awed. The final image of the segment
    and of the planet's whole story: still there, still turning, wrong the whole
    time.

    The arrow is the same retrograde sweep as the opening beat but SMALLER and
    FAINTER — the same wrong motion, now seen from far enough away that it reads
    as the planet's permanent condition rather than as an event. A mostly-empty
    field and a small subject, because the closer is quiet."""
    img = _void_card(card, planet, seed=1301, stars=88)

    gx, gy, gr = 640, 348, 112
    img = _gas_giant(img, gx, gy, gr, seed=1301, band_count=4)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, gx, gy, gr + 3, BONE, 150, K.FINE)

    # one faint retrograde arrow looping the giant — same clockwise sweep as the
    # opening beat, scaled down, at lower alpha
    arrow = []
    for i in range(31):
        a = math.radians(20.0 + 300.0 * i / 30.0)
        arrow.append((gx + (gr + 56) * math.cos(a),
                      gy + (gr + 56) * 0.58 * math.sin(a)))
    _thick_curve(d, arrow, AMBER, seed=1310, width=7, wobble=2.0)
    _arrow_head(d, arrow[-1], 130.0, AMBER, size=18, seed=1311)

    # "STILL TURNING" repeated the caption's own second line. This is the fact the
    # caption does NOT state: nothing ever corrected it.
    _hero(d, 'NEVER CORRECTED', gx, 596, BONE, px=58, y_max=614)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ===========================================================================
# Dispatch — keyed by the beat `id` field from script.json. The frame generator
# merges this into cardframe's process-global table via C.register(RENDERERS).
# ===========================================================================

RENDERERS = {
    'backwards_hook': render_backwards_hook,
    'everyone_else_turns': render_everyone_else_turns,
    'not_made_here': render_not_made_here,
    'wrong_way_explained': render_wrong_way_explained,
    'almost_nothing_there': render_almost_nothing_there,
    'cork_density': render_cork_density,
    'should_have_collapsed': render_should_have_collapsed,
    'cloud_wall': render_cloud_wall,
    'endless_wind': render_endless_wind,
    'dayside_1700': render_dayside_1700,
    'you_would_not': render_you_would_not,
    'three_wrongs': render_three_wrongs,
    'never_supposed_to_be_here': render_never_supposed_to_be_here,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table. Harmless if
    called twice. The frame generator may also just read .RENDERERS directly."""
    C.register(RENDERERS if mapping is None else mapping)
    return RENDERERS


# ===========================================================================
# __main__ self-test — render one cardsheet PNG per beat into ./cardsheet/.
# Run from work/segments:  python wasp17b/_cards.py
# ===========================================================================

def _self_test():
    """Build a minimal card dict for every beat and render it.

    Each beat gets the beat's own default character pose/expression (from the
    POSES/EXPRESSION the visual brief calls for) at a reasonable position, and a
    short generic caption. The renderers must all return a 1280x720 RGB frame."""
    import json
    import os as _os

    out_dir = _os.path.join(HERE, 'cardsheet')
    _os.makedirs(out_dir, exist_ok=True)

    # beat id -> (default pose, default expression, x_center, y_top, height,
    #             caption) — a generic but valid character per beat.
    chars = {
        'backwards_hook':           ('standing', 'flat', 300, 300, 300,
                                     'WRONG WAY ROUND'),
        'everyone_else_turns':      ('shrugged', 'zigzag', 1010, 300, 300,
                                     'EVERYBODY ELSE TURNS ONE WAY'),
        'not_made_here':            ('pointing', 'oval', 980, 360, 300,
                                     'IT WAS NEVER MADE HERE'),
        'wrong_way_explained':      ('pointing', 'flat', 640, 400, 260,
                                     'NO ORDINARY REASON'),
        'almost_nothing_there':     ('hands_up', 'frown', 240, 300, 300,
                                     'ALMOST NOTHING IN THERE'),
        'cork_density':             ('shrugged', 'zigzag', 640, 400, 240,
                                     'FLOATS LIKE A CORK'),
        'should_have_collapsed':    ('shielding_eyes', 'frown', 180, 300, 300,
                                     'SHOULD HAVE COLLAPSED'),
        'cloud_wall':               ('shrugged', 'oval', 300, 400, 280,
                                     'A WALL OF WEATHER'),
        'endless_wind':             ('shielding_eyes', 'zigzag', 240, 320, 300,
                                     'THE WIND NEVER STOPS'),
        'dayside_1700':             ('standing', 'frown', 980, 340, 300,
                                     'SEVENTEEN HUNDRED DEGREES'),
        'you_would_not':            ('hands_up', 'frown', 640, 380, 260,
                                     'YOU WOULD NOT GO HERE'),
        'three_wrongs':             ('shrugged', 'flat', 960, 300, 300,
                                     'EVERY PART OF IT WRONG'),
        'never_supposed_to_be_here': ('hands_down', 'oval', 260, 320, 300,
                                      'STILL THERE, STILL TURNING'),
    }

    beats = list(RENDERERS.keys())
    ok = 0
    for i, cid in enumerate(beats):
        pose, expr, xc, yt, hh, cap = chars[cid]
        card = {
            'id': cid,
            'caption': cap,
            'stickman': {
                'expression': expr, 'pose': pose, 'height': hh,
                'x_center': xc, 'y_top': yt,
            },
        }
        img = RENDERERS[cid](card, PLANET)
        assert img.size == (W, H), '%s returned %s not 1280x720' % (cid, img.size)
        assert img.mode == 'RGB', '%s returned mode %s not RGB' % (cid, img.mode)
        path = _os.path.join(out_dir, 'beat_%02d.png' % (i + 1))
        img.save(path)
        ok += 1
        print('beat %02d  %-26s  %dx%d  %s' % (i + 1, cid, img.size[0],
                                                img.size[1], _os.path.basename(path)))
    print('self-test OK: %d/%d beats rendered to %s' % (ok, len(beats), out_dir))
    return 0


if __name__ == '__main__':
    raise SystemExit(_self_test())
