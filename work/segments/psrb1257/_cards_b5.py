# work/segments/psrb1257/_cards_b5.py
# B5 THE NAMING — card renderers for segment 3 (PSR B1257+12).
#
# Follows work/segments/psrb1257/_BUILD_BRIEF.md exactly:
#   - Layout A: 84 px paper title strip (C._header), full-bleed art below, no
#     caption band. Void cards get a visible paper band; cream cards are already
#     full-bleed cream and the header floats.
#   - Caption via C._caption at (70, 652) on every card, dark_bg by card_value.
#   - Character ONLY via C._draw_stickman(img, card, theme=...) — the schedule
#     owns x/y/height/pose/expression. Never hardcoded.
#   - Register discipline: gradient ONLY on the emissive pulsar core (name_star);
#     the haze, the silhouettes, the star chart and the digit frames are FLAT.
#     Cream cards are flat paint — on name_just_digits the flatness IS the point.
#   - Deterministic: every wobble/stipple/starfield call takes an explicit seed.
#   - Outline weight: 6 px large shapes, 4 px medium, 2 px fine/hairlines.
#
# ROUND-2 ART FIX (this file only):
#   - name_why: the haze band was a stroked 9-gon and read as a hard-edged BOX
#     around five unreadable dark slabs. It is now `_soft_wash` - overlapping
#     soft ellipses blurred well past their own edge and composited ADDITIVELY,
#     so the alpha reaches zero gradually in every direction and there is no
#     boundary to see. The five occupants are now `_ghost` figures: a round
#     head over a tapering, hem-scalloped body, still UNNAMED (no faces, no
#     type). Two of them are slumped and dimmed (the DEAD pair); the third
#     stands tall and full-strength (the THIRD). The 2-dead-and-a-third idea
#     is now legible from the silhouettes alone.
#   - All four remaining hero plates now go through C.hero_word, so the clamp
#     knows about the stroke keyline and nothing can clip an edge or ride up
#     into the title strip.
#
# LAYOUT NOTE (the three deviations forced by the schedule, not by taste):
#   The schedule puts the character at x_center=400 on all five cards. At
#   height=400 his shrug/pointing pose reaches x=323..477, and the caption
#   occupies x=70..~1070 at y=652..676. Three of the sketches place art inside
#   one of those two regions, which is physically impossible to draw cleanly:
#     1. name_three  — three 64 px names total 1071 px of glyph; centred on the
#        sketched plate x's (330/700/1070) POLTERGEIST runs 17 px off the right
#        edge and PHOBETOR runs straight through the character. The three
#        skull+name pairs are therefore laid out as a three-row LEDGER in the
#        right two-thirds and the character keeps the left third. Same elements,
#        same order, same one-per-stamp reveal; nothing clips, nothing collides.
#     2. name_coordinates — the sketch's 'SKY COORDINATES' (860,600) and
#        'A SPOT ON THE SKY' (860,640) both land on the mandatory caption. The
#        annotation moves up to become the chart's title rule at (560,128) and
#        the heavy plate rises to cy=608, clearing the caption by 18 px.
#     3. name_just_digits — the sketched first frame (500,300) overlaps the
#        character's shrug. The four frames shift to 580/740/900/1060 and the
#        heavy plate to cx=850 so both clear him.
#   On name_why the five ghost figures sit at x=596..1060 for the same reason:
#   the sketched 200 px pitch put one figure on top of the character at bx=420.
#   The mist wash is full-bleed and has no left edge to clear.
#
# Register into the dispatch table with C.register(RENDERERS) or import RENDERERS.
# No import-time side effects.

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import lib.type as T
import lib.ink as K
import lib.cardframe as C

# --- Locked segment palette (PALETTE_SPEC.md section 1) ---------------------
INK = C.PAL['ink']        # slate-black
PAPER = C.PAL['paper']    # bone-cream
DEEP = C.PAL['deep']      # void
AMBER = C.PAL['amber']    # signal amber
BONE = C.PAL['bone']      # x-ray bone
VIOLET = C.PAL['violet']  # magnet violet
WHITE = (255, 255, 255)   # star-core centre stop only

# --- Locked type sizes (round_1 type_scale / PALETTE_SPEC.md section 4) -----
# The 64 px heavy display plate is set through C.hero_word, which owns the size
# clamp; the 18 px annotations below use _text_wh for centring.


# ============================================================================
# Beat-local helpers. These wrap lib primitives; they do not re-derive the
# locked constants (widths, fonts and colours all come from lib/type, lib/ink
# and lib/cardframe).
# ============================================================================

def _soft_wash(img, cx, cy, rx, ry, color, peak, seed):
    """A feathered, edgeless atmosphere wash, composited ADDITIVELY in place.

    WHY THIS REPLACED THE OLD STROKED BAND. The previous band was a filled 9-gon
    with a 2 px outline, so the eye found a straight closed border and read the
    card as "a box with things in it". A wash must have no boundary at all.

    So: six overlapping ellipses (a broad body, four offset density lobes and a
    low mist floor) are drawn into a QUARTER-RESOLUTION mask, blurred by a
    radius larger than the ellipses themselves, then upsampled. After a blur
    wider than the source shape the alpha has no edge to find, and the offset
    lobes keep the field from reading as one clean ellipse. Additive compositing
    keeps the starfield visible through the mist instead of painting over it.
    """
    s = 4
    mask = Image.new('L', (C.W // s, C.H // s), 0)
    md = ImageDraw.Draw(mask)
    rnd = random.Random(seed)
    # (x-fraction, y-fraction, mask value, vertical offset as a fraction of ry)
    lobes = ((0.88, 0.92, 255, 0.00), (0.72, 0.70, 232, 0.10),
             (0.56, 0.52, 214, -0.22), (0.64, 0.40, 198, 0.36),
             (0.44, 0.30, 182, -0.40), (1.00, 0.24, 205, 0.74))
    for fx, fy, val, oy in lobes:
        ox = rnd.uniform(-0.09, 0.09) * rx
        px, py = cx + ox, cy + ry * oy
        ax, ay = rx * fx, ry * fy
        md.ellipse([(px - ax) / s, (py - ay) / s,
                    (px + ax) / s, (py + ay) / s], fill=val)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(2.0, rx / s * 0.20)))
    mask = mask.resize((C.W, C.H), Image.BILINEAR)
    mask = mask.point(lambda v: int(v * peak / 255))
    layer = Image.new('RGB', (C.W, C.H), tuple(color))
    lit = ImageChops.multiply(layer, Image.merge('RGB', (mask, mask, mask)))
    img.paste(ImageChops.add(img, lit), (0, 0))
    return img


def _ghost(d, cx, feet_y, h, seed, slump=0.0, alpha=255):
    """One flat, UNNAMED ghost: a round head over a tapering body with a soft
    scalloped hem. No face, no type — the naming lands on the NEXT card.

    `slump` (0..1) sinks the head toward the shoulders, closes the neck gap and
    splays the hem wider, which is what makes a figure read as DEAD rather than
    merely shorter. A 4 px violet keyline separates the slate-black body from
    the violet wash behind it; without it the figures dissolve into the mist.
    """
    head_r = h * (0.180 - 0.030 * slump)
    neck = h * (0.030 - 0.026 * slump)          # head sits ON the shoulders
    head_cx = cx + slump * h * 0.070           # the dead ones slump forward
    head_cy = feet_y - h + head_r + slump * h * 0.170
    sh_y = head_cy + head_r + neck              # shoulder line
    w_sh = h * (0.250 - 0.020 * slump)
    w_hem = h * (0.310 + 0.110 * slump)         # the dead ones splay on the ground
    body_h = max(8.0, feet_y - sh_y)

    body = [(cx - w_sh, sh_y + body_h * 0.04),
            (cx - w_sh * 1.01, sh_y + body_h * 0.42),
            (cx - w_hem * 0.92, feet_y - h * 0.17),
            (cx - w_hem, feet_y - h * 0.05),
            (cx - w_hem * 0.74, feet_y),
            (cx - w_hem * 0.24, feet_y - h * 0.085),
            (cx, feet_y),
            (cx + w_hem * 0.24, feet_y - h * 0.085),
            (cx + w_hem * 0.74, feet_y),
            (cx + w_hem, feet_y - h * 0.05),
            (cx + w_hem * 0.92, feet_y - h * 0.17),
            (cx + w_sh * 1.01, sh_y + body_h * 0.42),
            (cx + w_sh, sh_y + body_h * 0.04),
            (cx + w_sh * 0.56, sh_y - h * 0.115),
            (cx, sh_y - h * 0.150),              # rounded dome, head nests in it
            (cx - w_sh * 0.56, sh_y - h * 0.115)]
    K.draw_smooth(d, body, fill=INK + (alpha,),
                  outline=VIOLET + (min(255, alpha + 40),), width=K.DETAIL,
                  seed=seed, wobble=h * 0.016, wavelength=h * 0.55)
    K.draw_disc(d, head_cx, head_cy, head_r, fill=INK + (alpha,),
                outline=VIOLET + (min(255, alpha + 40),), width=K.DETAIL,
                seed=seed + 1, wobble=h * 0.010)
    return (cx, feet_y - h)


def _text_wh(text, font, stroke=0):
    """(w, h) of a text bbox in the locked family."""
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    return w + 2 * stroke, h + 2 * stroke


def _plate_l(draw, text, x, cy, fill_rgb, px=64):
    """A HEAVY display plate LEFT-anchored at x, vertically centred on cy.

    A thin wrapper over C.hero_word, which is centre-anchored: the width is
    measured with the SAME font/size the helper will pick, so `x + w/2` puts the
    left edge back where the layout wants it. The point of routing through
    hero_word at all is that its clamp accounts for the stroke keyline (pad),
    so a long name can never run off the right edge the way a raw
    draw_outlined_text could.
    """
    w = T._bbox(draw, text, T.load_font_at(px, bold=True))[2]
    return C.hero_word(draw, text, x + w / 2.0, cy, fill_rgb,
                       stroke_rgb=fill_rgb, stroke_width=0, px=px, margin=40)


def _tiny(draw, text, x, y, color_rgb, on_cream=False):
    """18 px tiny diagram annotation, left-anchored at (x, y)."""
    T.draw_stamp(draw, text, (x, y), INK if on_cream else color_rgb,
                 ink_rgb=PAPER if on_cream else INK)


# ============================================================================
# Card 22 - name_why  (void / violet / worried + shrugged)
#   Five flat ghost figures standing in a feathered violet mist. DELIBERATELY
#   UNNAMED: a round head over a tapering body, no faces and no type, because
#   the names land on the NEXT card. Violet is a SHAPE colour and carries no
#   word (3.48:1 on void - never type).
#   The reading is in the postures: indices 0 and 1 are the DEAD pair (slumped,
#   dimmed, hem splayed), index 2 is THE THIRD (tall, full strength, standing
#   clear of the mist floor), 3 and 4 are the rest of the unnamed crowd.
#   Focal element: the five figures in the wash. Nothing else competes.
# ============================================================================

# (centre x, height, slump, alpha, feet y). The height spread is deliberately
# exaggerated: the DEAD pair stand 112/104 tall so their heads sit 60+ px below
# THE THIRD's, which is what makes "two dead and a third" read from silhouette
# alone rather than from the caption.
_GHOST_ROW = ((596, 112, 1.00, 122, 596),
              (712, 104, 1.00, 112, 601),
              (828, 172, 0.00, 255, 596),
              (944, 150, 0.20, 196, 598),
              (1060, 146, 0.30, 180, 600))


def render_name_why(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=2200, stars=120)

    # edgeless violet mist the figures stand in (never a stroked band)
    _soft_wash(img, 650, 512, 610, 118, VIOLET, peak=122, seed=111)

    d = ImageDraw.Draw(img, 'RGBA')

    # the five nameless figures, evenly spaced, alternating +/- 3 px on the
    # in-card 0.25 s stamp offset
    for k, (bx, gh, slump, alpha, feet) in enumerate(_GHOST_ROW):
        _ghost(d, bx + (3 if k % 2 == 0 else -3), feet, gh,
               seed=2210 + k, slump=slump, alpha=alpha)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ============================================================================
# Card 23 — name_three  (cream / cream / awed_brows + pointing)
#   The reveal. Three cartoon-flat skull plates with three heavy slate-black
#   names — laid out as a three-row ledger in the right two-thirds so the
#   64 px names fit, the character keeps the left third, and the mandatory
#   caption stays clear. Cartoon-flat means flat: no gradients, no texture, and
#   NO teeth-and-tongue mouth (the reference's is copyrighted character
#   design and is deliberately not copied) — two eye slots and a jaw rule.
# ============================================================================

_SKULL_ROWS = (('DRAUGR', 200), ('PHOBETOR', 360), ('POLTERGEIST', 520))
_SKULL_CX = 700
_SKULL_NAME_X = 780


def render_name_three(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), PAPER)
    d = ImageDraw.Draw(img)

    for k, (name, cy) in enumerate(_SKULL_ROWS):
        # skull plate: 96 px across, cartoon-flat, slate-black rim
        K.draw_disc(d, _SKULL_CX, cy, 48, fill=PAPER, outline=INK,
                    width=K.DETAIL, seed=2310 + k, wobble=1.2)
        # two eye slots
        K.draw_disc(d, _SKULL_CX - 16, cy - 22, 9, fill=INK, outline=INK,
                    width=K.DETAIL, seed=2320 + k, wobble=0.6)
        K.draw_disc(d, _SKULL_CX + 16, cy - 22, 9, fill=INK, outline=INK,
                    width=K.DETAIL, seed=2330 + k, wobble=0.6)
        # jaw rule: one slate-black rule across the lower plate, no teeth
        d.line([(_SKULL_CX - 22, cy + 12), (_SKULL_CX + 22, cy + 12)],
               fill=INK, width=K.DETAIL)
        # heavy 64 px name, slate-black on cream, settled
        _plate_l(d, name, _SKULL_NAME_X, cy, INK)

    C._header(img, planet, paper_band=False)
    C._draw_stickman(img, card, theme='light')
    C._caption(img, card['caption'], 70, 652, dark_bg=False)
    return img


# ============================================================================
# Card 24 — name_star  (void / amber / flat + pointing)
#   The skulls are GONE. The beat ends on the corpse, so the naming lands on
#   the star: an emissive pulsar core — the ONE legal gradient in this segment
#   — carrying the heavy 'PSR B1257+12' plate in amber, ringed by two FLAT
#   magnet-violet halo rings so the body still reads around the type. The
#   bone 'VIRGO' stamp sits top-right (fact flag E1: Virgo, not Vela).
#   Focal element: the name plate. The core is a supporting glow behind it.
# ============================================================================

_CORE_CX, _CORE_CY, _CORE_R = 880, 320, 36


def render_name_star(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=2400, stars=120)

    # emissive pulsar core: 3-stop radial gradient (white -> bone -> violet limb)
    C._radial_core(img, _CORE_CX, _CORE_CY, _CORE_R, [WHITE, BONE, VIOLET])

    d = ImageDraw.Draw(img, 'RGBA')
    # two FLAT magnet-violet halo rings (12% / 22%) — outside the gradient, so
    # they stay flat per PALETTE_SPEC section 3
    for rr, a in ((_CORE_R + 20, 30), (_CORE_R + 42, 56)):
        d.ellipse([_CORE_CX - rr, _CORE_CY - rr, _CORE_CX + rr, _CORE_CY + rr],
                  outline=VIOLET + (a,), width=K.DETAIL)
    # 2 px amber limb on the core edge
    d.ellipse([_CORE_CX - _CORE_R, _CORE_CY - _CORE_R,
               _CORE_CX + _CORE_R, _CORE_CY + _CORE_R],
              outline=AMBER + (190,), width=K.FINE)

    # the heavy name plate re-stamps over the core
    C.hero_word(d, 'PSR B1257+12', _CORE_CX, _CORE_CY, AMBER,
                stroke_rgb=INK, stroke_width=4, px=64, margin=40)

    # 18 px bone 'VIRGO' stamp, top-right
    _tiny(d, 'VIRGO', 1080, 120, BONE)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ============================================================================
# Card 25 — name_coordinates  (void / bone / smirk + shrugged)
#   A plain star chart: a bone sky GRID — seven vertical and five horizontal
#   2 px rules over x=560..1180, y=180..560, with 3 px edge ticks every 60 px
#   — and a crosshair at (860, 330) that LOCKS to the grid. 'SKY COORDINATES'
#   titles the chart; 'A SPOT ON THE SKY' is the heavy plate.
#   FACT FLAG E6 (APPLIED): this is a SEXAGESIMAL sky coordinate, 12h57m right
#   ascension and +12 deg declination. There is NO base-eight joke, none is
#   drawn, and none may appear in the narration or the type.
# ============================================================================

_GRID_X0, _GRID_X1, _GRID_Y0, _GRID_Y1 = 560, 1180, 180, 560


def render_name_coordinates(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=2500, stars=90)

    d = ImageDraw.Draw(img, 'RGBA')
    gx0, gx1, gy0, gy1 = _GRID_X0, _GRID_X1, _GRID_Y0, _GRID_Y1

    # seven vertical + five horizontal rules: 2 px bone, drawn plainly
    for k in range(7):
        x = gx0 + k * (gx1 - gx0) / 6.0
        d.line([(x, gy0), (x, gy1)], fill=BONE + (85,), width=K.FINE)
    for k in range(5):
        y = gy0 + k * (gy1 - gy0) / 4.0
        d.line([(gx0, y), (gx1, y)], fill=BONE + (85,), width=K.FINE)

    # 3 px ticks every 60 px along the bottom and left edge of the grid
    for gx in range(gx0, gx1 + 1, 60):
        d.line([(gx, gy1), (gx, gy1 + 11)], fill=BONE + (170,), width=K.DETAIL)
    for gy in range(gy0, gy1 + 1, 60):
        d.line([(gx0 - 11, gy), (gx0, gy)], fill=BONE + (170,), width=K.DETAIL)

    # crosshair at (860, 330): 3 px bone cross + a 2 px circle locking onto it
    cxp, cyp = 860, 330
    d.line([(cxp - 30, cyp), (cxp + 30, cyp)], fill=BONE, width=K.DETAIL)
    d.line([(cxp, cyp - 30), (cxp, cyp + 30)], fill=BONE, width=K.DETAIL)
    d.ellipse([cxp - 18, cyp - 18, cxp + 18, cyp + 18],
              outline=BONE, width=K.FINE)

    # chart title rule (the 'SKY COORDINATES' annotation, lifted clear of the
    # mandatory caption — see the layout note at the top of this file)
    _tiny(d, 'SKY COORDINATES', 560, 128, BONE)

    # heavy bone plate, below the grid, clearing both the grid's bottom tick row
    # (y=571) and the mandatory caption (y=652)
    C.hero_word(d, 'A SPOT ON THE SKY', 860, 606, BONE,
                stroke_rgb=INK, stroke_width=4, px=64, margin=40, y_max=643)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ============================================================================
# Card 26 — name_just_digits  (cream / cream / flat + hands_down)
#   CREAM, deliberately plain. Four slate-black digit frames 120 px square
#   holding '1' '2' '5' '7' in heavy 64 px, two 18 px annotations with 3 px
#   leaders up to their frame pair, and a heavy 'THAT IS THE NAME' plate.
#   No illustration, no texture, no gradient, nothing else — the flatness IS
#   the point: a dead star reduced to a row of numbers.
# ============================================================================

_DIGITS = (('1', 580), ('2', 740), ('5', 900), ('7', 1060))


def render_name_just_digits(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), PAPER)
    d = ImageDraw.Draw(img)

    for k, (digit, cx) in enumerate(_DIGITS):
        # 120 px square slate-black frame, smooth organic corners
        K.draw_smooth(d, [(cx - 60, 240), (cx + 60, 240),
                          (cx + 60, 360), (cx - 60, 360)],
                      fill=PAPER, outline=INK, width=K.DETAIL,
                      seed=2610 + k, wobble=0.8, wavelength=140.0)
        # heavy 64 px digit, slate-black on cream
        C.hero_word(d, digit, cx, 300, INK, stroke_rgb=INK,
                    stroke_width=0, px=64, margin=40)

    # 3 px leaders from each annotation up to its frame pair
    d.line([(660, 452), (660, 366)], fill=INK, width=K.DETAIL)
    d.line([(980, 452), (980, 366)], fill=INK, width=K.DETAIL)

    # 18 px slate-black annotations (on cream -> ink), centred on their pairs
    w1, _ = _text_wh('RIGHT ASCENSION', T.load_font_at(18, bold=True))
    _tiny(d, 'RIGHT ASCENSION', 660 - w1 / 2, 456, INK, on_cream=True)
    lab2 = '+12 DEGREES, UP AND NORTH'
    w2, _ = _text_wh(lab2, T.load_font_at(18, bold=True))
    _tiny(d, lab2, 980 - w2 / 2, 456, INK, on_cream=True)

    # heavy 'THAT IS THE NAME' plate, clear of the character on the left
    C.hero_word(d, 'THAT IS THE NAME', 850, 540, INK, stroke_rgb=INK,
                stroke_width=0, px=64, margin=40)

    C._header(img, planet, paper_band=False)
    C._draw_stickman(img, card, theme='light')
    C._caption(img, card['caption'], 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

RENDERERS = {
    'name_why': render_name_why,
    'name_three': render_name_three,
    'name_star': render_name_star,
    'name_coordinates': render_name_coordinates,
    'name_just_digits': render_name_just_digits,
}
