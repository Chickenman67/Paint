# work/segments/psrb1257/_cards_b3.py — B3 THE PLANETS card renderers.
#
# Beat B3 cards: planet_masses (cream), planet_minefield (void/amber),
#                planet_periods (void/bone, diagram-only).
#
# Contract: work/segments/psrb1257/_BUILD_BRIEF.md (hard rules 1-10) plus
# work/segments/psrb1257/PALETTE_SPEC.md. Layout A is mandatory: an 84 px paper
# title strip, full-bleed art from row 84, NO caption band, caption floating on
# the art via C._caption at (70, 652). The character is drawn ONLY through
# C._draw_stickman, which reads x/y/height/pose/expression off the schedule.
#
# Register discipline (PALETTE_SPEC §3 denylist): a gradient appears on card 12's
# pulsar core and card 13's pulsar core ONLY, and on the void backdrop's vertical
# ramp. Never on the planets-as-discs, the orbit ellipses, the radiation wash,
# the rocks, the starfield, the title strip or the character.
#
# Every wobble/stipple/starfield call takes an explicit seed. No global
# random.seed() state, so re-renders are byte-identical.

import math
import random

from PIL import Image, ImageDraw, ImageFilter

import lib.type as T
import lib.ink as K
import lib.cardframe as C

W, H = C.W, C.H
ART_TOP = T.ART_TOP          # 84
INK = C.PAL['ink']           # slate-black
PAPER = C.PAL['paper']       # bone-cream
AMBER = C.PAL['amber']       # signal amber
BONE = C.PAL['bone']         # x-ray bone
VIOLET = C.PAL['violet']     # magnet violet (shape colour only, never type)

# The locked heavy display size for this segment (beat type_scale: heavy_px 64,
# heavy_stroke 4). Off-scale use goes through T.load_font_at so the family stays
# the one wired into lib.type (rounded casual hand, NOT Consolas).
HEAVY_PX = 64
HEAVY_STROKE = 4

# The diagram micro-label size (PALETTE_SPEC §4 "tiny annotation", 18px).
TINY_PX = 18


# ---------------------------------------------------------------------------
# Small text helpers (right-align / vertical-centre). All go through
# lib.type so the family and the outline treatment stay locked.
# ---------------------------------------------------------------------------

def _measure(d, text, font):
    try:
        b = font.getbbox(text)
        return b[2] - b[0], b[3] - b[1]
    except Exception:
        sz = int(getattr(font, 'size', 16))
        return len(text) * int(sz * 0.62), int(sz * 1.25)


def _heavy_right(d, text, right_x, top_y, color_rgb, ink_rgb=INK,
                 sw=HEAVY_STROKE, size=HEAVY_PX):
    """One heavy display word, right-aligned to `right_x`, top at `top_y`."""
    font = T.load_font_at(size, bold=True)
    w, _h = _measure(d, text, font)
    x = right_x - w
    T.draw_outlined_text(d, (x, top_y), text, font, fill=color_rgb,
                         stroke=ink_rgb, stroke_width=sw)
    return x, w


def _tiny_left(d, text, left_x, top_y, color_rgb, ink_rgb=INK, sw=2,
               size=TINY_PX):
    """Small diagram annotation (ring labels). 18px, no paragraph type."""
    font = T.load_font_at(size, bold=True)
    T.draw_outlined_text(d, (left_x, top_y), text, font, fill=color_rgb,
                         stroke=ink_rgb, stroke_width=sw)
    w, _h = _measure(d, text, font)
    return w


# The annotation scale for THIS card. 20px sits deliberately between T.STAMP_PX
# (15, tiny tick labels) and T.CAPTION_PX (27, the floating caption): big enough
# to read as a word on a diagram row, far too small to shout. The b3 round-1
# card drew its mass figures at the 64px HEAVY scale, where "MOON-SIZE" ran off
# the top-right of the frame and the three figures read as three competing
# headlines instead of three rows of a ledger.
ANNO_PX = 20


def _anno(d, text, left_x, mid_y, color_rgb, ink_rgb=INK, sw=2,
          size=ANNO_PX, bold=True):
    """Annotation-scale word, left edge at `left_x`, vertically centred on
    `mid_y` so it sits ON its ledger rule instead of floating above it."""
    font = T.load_font_at(size, bold=bold)
    w, h = _measure(d, text, font)
    T.draw_outlined_text(d, (left_x, mid_y - h // 2), text, font,
                         fill=color_rgb, stroke=ink_rgb, stroke_width=sw)
    return w, h


def _anno_right(d, text, right_x, mid_y, color_rgb, ink_rgb=INK, sw=2,
                size=ANNO_PX, bold=True):
    """Annotation-scale word, right edge at `right_x`, vertically centred on
    `mid_y`."""
    font = T.load_font_at(size, bold=bold)
    w, h = _measure(d, text, font)
    T.draw_outlined_text(d, (right_x - w, mid_y - h // 2), text, font,
                         fill=color_rgb, stroke=ink_rgb, stroke_width=sw)
    return w, h


# ===========================================================================
# Card 11 — planet_masses   (CREAM, Register P, flat fills, thick outlines)
# ===========================================================================
# FACT FLAG E3 (already applied upstream): ONE planet is Moon-ish (Draugr,
# 0.02 Earth) and TWO are ~4 Earths (Phobetor 3.9, Poltergeist 4.3). The disc
# radii 16 / 40 / 42 carry that: one speck, then two near-twin heavies. No
# gradient and no band texture — the three planets are on PALETTE_SPEC §3's
# denylist, so they are flat slate-black discs with a 6 px organic edge.
#
# LAYOUT. This is a LEDGER, so every word sits on its row's rule: the disc, then
# the mass figure, then the planet's name, all vertically centred on the same
# baseline. Round 1 broke that — the mass figures were 64px HEAVY words floated
# ~100px ABOVE their rules, right-aligned to the frame edge, which pushed
# "MOON-SIZE" up into the title strip and made three annotations read as three
# competing focal points. They are annotation scale now (ANNO_PX), on the row.

_MASS_RULES_Y = (210, 360, 540)
_MASS_RULE_X0, _MASS_RULE_X1 = 615, 1190
_MASS_DISCS = ((668, 210, 16), (668, 360, 40), (668, 540, 42))
_MASS_ANNO_X = 752          # clear of the widest disc (r=42 -> right edge 710)
_MASS_NAMES = ("DRAUGR", "PHOBETOR", "POLTERGEIST")
_MASS_FIGURES = ("MOON-SIZE", "4x EARTH", "4x EARTH")
_MASS_GUTTER = 16           # blank rule either side of a word, so no line strikes it


def render_planet_masses(card, planet="PSR B1257+12"):
    """The mass ledger. Three rules, three flat discs whose SIZES are the fact,
    and one annotation pair per row. No hero word — the discs are the subject."""
    img = Image.new('RGB', (W, H), PAPER)

    # Painterly paper grain over the art area only — keeps the cream from
    # reading as a clean vector fill. Deterministic.
    dg = ImageDraw.Draw(img)
    K.stipple(dg, 0, ART_TOP, W, H, (226, 216, 192), seed=1101,
              density=0.012, r=1, spread=1)

    d = ImageDraw.Draw(img)

    # Measure the row's words FIRST so the rule can be broken around them. A
    # ledger rule that strikes through its own label reads as a mistake; the
    # classic solution is a gap either side of each word, which is what the
    # round-1 card was missing (its words floated clear ABOVE the rule instead,
    # detached from the row they annotate).
    f_fig = T.load_font_at(ANNO_PX, bold=True)
    f_nam = T.load_font_at(T.STAMP_PX, bold=False)
    fig_w = [_measure(d, t, f_fig)[0] for t in _MASS_FIGURES]
    nam_w = [_measure(d, t, f_nam)[0] for t in _MASS_NAMES]

    # --- the ledger: three slate-black rules, one flat disc on each ----------
    for i, (ry, (dx, cy, rr)) in enumerate(zip(_MASS_RULES_Y, _MASS_DISCS)):
        # rule resumes past each word, with a gutter so no line touches type
        gap_a0 = _MASS_ANNO_X - _MASS_GUTTER
        gap_a1 = _MASS_ANNO_X + fig_w[i] + _MASS_GUTTER
        nam_left = _MASS_RULE_X1 - nam_w[i]
        gap_b1 = nam_left - _MASS_GUTTER
        for (x0, x1) in ((_MASS_RULE_X0, gap_a0), (gap_a1, gap_b1)):
            if x1 - x0 > 4:
                d.line([(x0, ry), (x1, ry)], fill=INK, width=3)
        K.draw_disc(d, dx, cy, rr, fill=INK, outline=INK, width=K.OUTLINE,
                    seed=1100 + i, wobble=1.6)

    # --- the character, in the world, before any type -----------------------
    C._draw_stickman(img, card, theme='light')

    # --- type on top --------------------------------------------------------
    C._header(img, planet, paper_band=False)

    # Both words are vertically centred ON their row's rule: the mass figure
    # fills the first gap, the planet's name rides the right end.
    for i, ry in enumerate(_MASS_RULES_Y):
        _anno(d, _MASS_FIGURES[i], _MASS_ANNO_X, ry, INK, INK, sw=2)
        _anno_right(d, _MASS_NAMES[i], _MASS_RULE_X1, ry, INK, PAPER,
                    sw=2, size=T.STAMP_PX, bold=False)

    C._caption(img, card['caption'], 70, 652, dark_bg=False)
    return img


# ===========================================================================
# Card 12 — planet_minefield   (VOID, Register S, amber accent)
# ===========================================================================
# One dominant element: the RUBBLE banner, sitting in an amber radiation field
# full of small discrete rocks. The pulsar core is the only emissive body (the
# ONE legal gradient on this card) and it is cropped by the opaque title strip,
# so the halo runs off the top of the frame.
#
# WHAT ROUND 1 GOT WRONG. The field was one closed 8-lobed polygon with a 2px
# amber keyline, and the "rubble" was 11 fat 8-26px blobs each carrying a long
# amber RIM ARC stroked along the arc that faced the pulsar. That arc pass is
# what turned every rock into a hard-edged crescent with a machined edge, and
# the closed keyline turned the field into a crisp vector oval — a mud smear
# with CAD trim. Rebuilt here as (a) a SOFT field: four wobbly lobes drawn on
# their own RGBA layer and Gaussian-blurred, so the boundary is a true alpha
# falloff nobody can trace (a stack of nested polygons still bands into visible
# concentric contours, which is its own kind of hard edge), and (b) MANY SMALL
# rocks — 8-20px pebbles plus 19-28px boulders — each a flat slate-black fill
# with a THIN 2px rim light on the pulsar-facing arc only. Long thick rim arcs
# read as machine cut; short thin ones read as a lit edge.

_WASH_CX, _WASH_CY, _WASH_RX, _WASH_RY = 790, 390, 450, 270   # x 340..1240, y 120..660
_WASH_BLUR = 34
# Four hand-written lobes (scale, alpha, cx, cy, phase). Fixed constants, not
# generated, so the field is byte-identical on every re-render.
_WASH_LOBES = ((1.00, 30, 790, 390, 0.0),
               (0.78, 22, 742, 432, 1.9),
               (0.60, 16, 856, 344, 3.4),
               (0.40, 12, 812, 404, 5.1))
_WASH_N = 11               # angular samples per lobe — enough for a soft blob
_CORE_CX, _CORE_CY, _CORE_R = 900, 180, 26

# The rubble lattice. Left edge starts at 640 so the field never crowds the
# character (x_center 400, half-width ~70).
_ROCK_ROWS = (196, 300, 392, 484, 574)
_ROCK_COLS = (656, 762, 868, 974, 1080, 1186)
_ROCK_SKIP = ((0, 1), (0, 2), (1, 5), (2, 0), (3, 4), (4, 3), (4, 5))
_BIG_ROCKS = ((656, 300, 26), (974, 392, 23), (868, 574, 28), (1186, 196, 20),
              (762, 484, 19))
# A second, finer pass so the field reads as DENSITY of rubble, not as a
# tidy lattice. Each entry is (x, y, r); all clear of the character.
_FINE_ROCKS = ((700, 246, 9), (830, 178, 11), (1120, 246, 8), (1030, 300, 10),
               (712, 348, 12), (900, 236, 8), (1230, 392, 11), (1058, 420, 9),
               (836, 452, 10), (1214, 500, 9), (700, 530, 8), (960, 520, 12),
               (1128, 566, 10), (836, 610, 9), (1006, 620, 8))


def _radiation_field(img):
    """Composite a soft amber radiation haze over `img` (RGB, in place).

    Built on its own RGBA layer — four low-alpha wobbly lobes, NO outline — and
    blurred before compositing, so the field's boundary is a genuine alpha
    falloff. Stacking nested polygons at low alpha instead is cheaper but bands
    into visible concentric contours, which is just a softer hard edge.

    Flat fills only: no gradient, and nothing here is a stroked boundary."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    for li, (scale, alpha, lcx, lcy, phase) in enumerate(_WASH_LOBES):
        pts = []
        for i in range(_WASH_N):
            a = math.tau * i / _WASH_N
            q = scale * (0.86 + 0.13 * math.sin(2 * a + phase)
                               + 0.08 * math.sin(3 * a - phase * 1.4)
                               + 0.04 * math.sin(5 * a + phase * 2.1))
            pts.append((lcx + _WASH_RX * q * math.cos(a),
                        lcy + _WASH_RY * q * math.sin(a)))
        K.draw_smooth(dl, pts, fill=AMBER + (alpha,), outline=None,
                      seed=1251 + li, wobble=12.0, wavelength=220.0)
    layer = layer.filter(ImageFilter.GaussianBlur(_WASH_BLUR))
    img.paste(Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB'))
    return img


def _rock(dw, px, py, rr, rnd, seed, core=(_CORE_CX, _CORE_CY)):
    """One painterly rock: irregular 6-gon, SOLID slate-black fill, and — on the
    larger stones — a THIN rim light on the arc facing the pulsar.

    Round 1 stroked that rim at K.DETAIL (4px) across 1.15 rad, which turned
    every blob into a machined crescent. Here the rim is K.FINE (2px) over a
    narrower arc and sits UNDER the fill pass order the other way round: the
    fill is opaque and the rim only survives where it falls outside it, so it
    reads as a lit edge on the rock rather than a ring drawn around it."""
    poly = []
    for k in range(6):
        a = math.tau * k / 6 + rnd.uniform(-0.22, 0.22)
        q = rr * rnd.uniform(0.60, 1.0)
        poly.append((px + q * math.cos(a), py + q * math.sin(a)))
    dense = K.draw_smooth(dw, poly, fill=INK, outline=None, seed=seed,
                          wobble=max(0.8, rr * 0.10),
                          wavelength=max(8.0, rr * 1.25))
    if rr >= 9:
        a_p = math.atan2(core[1] - py, core[0] - px)
        run = []
        for (x, y) in dense:
            da = (math.atan2(y - py, x - px) - a_p + math.pi) % math.tau - math.pi
            if abs(da) < 0.62:
                run.append((x, y))
        if len(run) >= 3:
            dw.line(run, fill=AMBER + (150,), width=K.FINE, joint='curve')
    return dense


def render_planet_minefield(card, planet="PSR B1257+12"):
    """Rubble in a minefield. Void field, soft amber haze, a dense scatter of
    small painterly rocks, the pulsar cropped by the strip, RUBBLE as focal."""
    img = Image.new('RGB', (W, H), C.PAL['deep'])
    C.void_backdrop(img, seed=1203, stars=120)
    _radiation_field(img)
    dw = ImageDraw.Draw(img, 'RGBA')

    # Painterly mottle over the blurred haze, so the field carries brush texture
    # instead of reading as an airbrushed blur. Kept very light: a heavy dark
    # stipple turns the haze into a gray speckled smear, which is the same mud
    # defect the stacked-polygon version had.
    K.stipple(dw, 420, 150, 1230, 640, AMBER + (16,), seed=1277,
              density=0.0012, r=2, spread=4)

    # Small rocks on a deterministic jittered lattice, with a few gaps so the
    # scatter is irregular rather than a visible grid. Everything sits clear of
    # the character (x < 640) so his cream limbs keep full separation.
    rnd = random.Random(1204)
    n = 0
    for ri, py in enumerate(_ROCK_ROWS):
        for ci, px in enumerate(_ROCK_COLS):
            if (ri, ci) in _ROCK_SKIP:
                continue
            _rock(dw,
                  px + rnd.randint(-20, 20),
                  py + rnd.randint(-24, 24),
                  rnd.randint(8, 20), rnd, seed=1210 + n)
            n += 1

    # A handful of boulders so the field has a size range, not one uniform grit.
    for (px, py, rr) in _BIG_ROCKS:
        _rock(dw, px + rnd.randint(-16, 16), py + rnd.randint(-18, 18),
              rr, rnd, seed=1290 + int(px))

    # A finer second scatter for density — irregular, so it reads as more rubble
    # rather than as a second grid.
    for k, (px, py, rr) in enumerate(_FINE_ROCKS):
        _rock(dw, px + rnd.randint(-18, 18), py + rnd.randint(-22, 22),
              rr, rnd, seed=1340 + k)

    # Fine grit between the stones: a handful of dust motes, cool and dim, so it
    # reads as dust in the beam rather than as sand piling into a smear.
    K.stipple(dw, 640, 150, 1240, 630, (74, 68, 84), seed=1271,
              density=0.0009, r=1, spread=1)

    # The pulsar: three FLAT violet halo rings (the outer one runs off the top
    # of the frame and is clipped by the title strip), then the emissive core —
    # the single legal gradient on this card.
    for hr, a in ((104, 14), (62, 30), (44, 48)):
        dw.ellipse([_CORE_CX - hr, _CORE_CY - hr, _CORE_CX + hr, _CORE_CY + hr],
                   outline=VIOLET + (a,), width=K.FINE)
    C._radial_core(img, _CORE_CX, _CORE_CY, _CORE_R,
                   [(255, 255, 255), BONE, (60, 52, 92)])

    # --- the character, in the world, before any type -----------------------
    C._draw_stickman(img, card, theme='dark')

    # --- type on top --------------------------------------------------------
    C._header(img, planet, paper_band=True)
    dtext = ImageDraw.Draw(img)
    C.hero_word(dtext, "RUBBLE", 890, 430, AMBER, INK, stroke_width=HEAVY_STROKE,
                px=HEAVY_PX, margin=60, y_max=630)
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ===========================================================================
# Card 13 — planet_periods   (VOID, Register S, bone accent, DIAGRAM ONLY)
# ===========================================================================
# FACT FLAG E4 (already applied upstream): the true periods are 25.262 / 66.5419
# / 98.2114 days — spoken "twenty-five days, sixty-seven, and ninety-eight". The
# earlier banner read 66 / 204 / 365, which is not this system. Inner-to-outer
# order is Draugr / Phobetor / Poltergeist, matching the numbers.
# stickman is null on this card, so no character is drawn — this is the diagram
# the following cards talk over, built to be re-used, not admired.

_ORB_CX, _ORB_CY = 640, 330
_ORB_RINGS = ((170, 58, "25 D"), (300, 100, "67 D"), (430, 142, "98 D"))
_ORB_DOT_ANG = (200, 20, 320)
_ORB_LEADER_GAP = 34          # label top sits this far above its ring apex


def render_planet_periods(card, planet="PSR B1257+12"):
    """Three nested period rings around the pulsar: the reusable diagram."""
    img = Image.new('RGB', (W, H), C.PAL['deep'])
    C.void_backdrop(img, seed=1301, stars=110)
    d = ImageDraw.Draw(img, 'RGBA')

    # Pulsar: flat violet halo rings, then the emissive core (legal gradient).
    for hr, a in ((56, 30), (40, 48)):
        d.ellipse([_ORB_CX - hr, _ORB_CY - hr, _ORB_CX + hr, _ORB_CY + hr],
                  outline=VIOLET + (a,), width=K.FINE)
    C._radial_core(img, _ORB_CX, _ORB_CY, 24,
                   [(255, 255, 255), BONE, (60, 52, 92)])

    # Three concentric orbit ellipses — thin luminous linework, never a
    # gradient, never a thick black outline.
    for rx, ry, _lab in _ORB_RINGS:
        d.ellipse([_ORB_CX - rx, _ORB_CY - ry, _ORB_CX + rx, _ORB_CY + ry],
                  outline=BONE + (200,), width=K.FINE)

    # One planet dot per ring. Flat bone, no outline (Register S).
    for (rx, ry, _lab), ang in zip(_ORB_RINGS, _ORB_DOT_ANG):
        a = math.radians(ang)
        px = _ORB_CX + rx * math.cos(a)
        py = _ORB_CY + ry * math.sin(a)
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=BONE + (255,))

    # Ring-apex labels with 3 px leader ticks. Bone type on void (15.98:1);
    # violet is never allowed to carry a word.
    dl = ImageDraw.Draw(img, 'RGBA')
    for rx, ry, lab in _ORB_RINGS:
        apex_y = _ORB_CY - ry
        top_y = apex_y - _ORB_LEADER_GAP
        _tiny_left(dl, lab, _ORB_CX, top_y, BONE, INK, sw=2)
        h = 22
        dl.line([(_ORB_CX, top_y + h + 2), (_ORB_CX, apex_y - 2)],
                fill=BONE + (200,), width=K.DETAIL)

    # --- type on top --------------------------------------------------------
    C._header(img, planet, paper_band=True)
    C.hero_word(dl, "25 / 67 / 98 DAYS", _ORB_CX, 553, BONE, INK,
                stroke_width=HEAVY_STROKE, px=HEAVY_PX, margin=60, y_max=634)
    C._draw_stickman(img, card, theme='dark')   # no-op: stickman is null
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


RENDERERS = {
    'planet_masses': render_planet_masses,
    'planet_minefield': render_planet_minefield,
    'planet_periods': render_planet_periods,
}
