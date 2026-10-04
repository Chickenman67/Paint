# _cards_b4.py — beat B4 THE SEARCH, segment 3 (PSR B1257+12)
#
# One renderer per card in _beats/b4.json, plus the RENDERERS dispatch dict.
# Renderer signature is exactly (card, planet="PSR B1257+12") -> PIL RGB 1280x720.
#
# CONTRACT (per _BUILD_BRIEF.md):
#   * Layout A — rows 0..83 paper title strip (via C._header), full-bleed art
#     rows 84..719, NO caption band; the caption floats on the art via C._caption.
#   * card_value 'void'  -> void_backdrop + C._header(paper_band=True)
#     card_value 'cream' -> full-bleed paper + C._header(paper_band=False)
#   * caption drawn on EVERY card with the fixed helper call C._caption(...,70,652).
#   * character drawn ONLY via C._draw_stickman(img, card, theme) from the
#     schedule's pose/expression/size/position — nothing hardcoded.
#   * register discipline: smooth gradients ONLY on emissive bodies (the pulsar
#     core on how_tug / how_first) and the starfield backdrop; space planets get
#     C.space_body (painterly, no black outline). No gradient on diagrams, rings,
#     beams, tally, mounds, washes or the character.
#   * every hero phrase goes through C.hero_word, so it is clamped inside the
#     frame INCLUDING its stroke and can never ride up into rows 0..83.
#   * every dominant on-card phrase is NON-redundant with the caption.
#   * all wobble/stipple/starfield calls take an explicit seed=; no global random
#     state, so re-renders are byte-identical.
#
# This module has NO import side effects. The frame generator merges RENDERERS
# via register() (or calls RENDERERS[cid] directly).

import math

from PIL import Image, ImageDraw, ImageFilter

import lib.type as T
import lib.ink as K
import lib.cardframe as C

W, H = C.W, C.H

INK = C.PAL['ink']
PAPER = C.PAL['paper']
DEEP = C.PAL['deep']
AMBER = C.PAL['amber']
BONE = C.PAL['bone']
VIOLET = C.PAL['violet']


# ---------------------------------------------------------------------------
# Local helpers (built on the lib API only; the locked type family via T)
# ---------------------------------------------------------------------------

def _open_curve(draw, points, color, width=2, seed=0, wobble=1.2, wavelength=90.0):
    """An OPEN hand-wobbled smooth curve.

    This mirrors K.draw_outline(closed=False) — same K.wobble_points engine,
    same Catmull-Rom math as K._smooth_open — because K's open path is
    unusable: ink._smooth_open builds ext = [p[0]] + p + [p[-1]] (len n+2) and
    then reads ext[i+3] for i up to n-1, which raises IndexError for every
    curve of 3+ points. lib/ink.py is read-only per the brief (hard rule 2),
    so the open curve is reconstructed here rather than patched in the lib.
    """
    pts = K.wobble_points(points, seed=seed, amount=wobble,
                          wavelength=wavelength)
    if len(pts) < 3:
        draw.line(list(pts), fill=color, width=width)
        return pts
    out = _catmull_open(pts, samples=12)
    draw.line(out, fill=color, width=width, joint='curve')
    return out


def _vline(draw, x, y0, y1, color, width=2, seed=0, wobble=1.2):
    """A short hand-wobbled vertical rule."""
    mid = (y0 + y1) / 2.0
    pts = [(x, y0), (x, mid), (x, y1)]
    return _open_curve(draw, pts, color, width, seed=seed, wobble=wobble,
                       wavelength=60.0)


def _hrule(draw, y, x0, x1, color, width=2, seed=0, wobble=1.2):
    """A short hand-wobbled horizontal rule."""
    mid = (x0 + x1) / 2.0
    pts = [(x0, y), (mid, y), (x1, y)]
    return _open_curve(draw, pts, color, width, seed=seed, wobble=wobble,
                       wavelength=90.0)


def _thick_curve(draw, points, fill, seed=0, width=24, wobble=2.0,
                 wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region, not as a
    PIL wide line.

    WHY NOT draw.line(..., width=24, joint='curve'). At this scale the Catmull-Rom
    output has many near-duplicate consecutive points; PIL renders each segment as
    a rectangle plus a round cap, and on a zero-length segment the cap shows up as
    a nub. The result is a hairy-edged glyph — visible as spikes all along the
    question mark on how_find.

    So the stroke is built geometrically instead: the smooth centreline is offset
    by +/- half-width along its normal into an outer and an inner rail, and the
    two rails are welded into one closed polygon that is filled with a single
    draw.polygon. Clean edges, no nubs, and it obeys the "smooth curve, organic
    outline" rule exactly the way K.draw_smooth does for closed shapes.
    """
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


def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output).

    Shared by _open_curve and _thick_curve. K._smooth_open exists but this keeps
    the two callers in lockstep so a curve drawn as a hairline and the same curve
    drawn as a fat glyph trace exactly the same path.
    """
    p = list(pts)
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


def _soft_wash(img, points, rgb, alpha, seed=0, wobble=12.0, wavelength=170.0,
               blur=18, outline=None, width=0):
    """A painterly flat-colour region with SOFT edges.

    Every wash on this beat (the violet plate, the 'wait' field, the glow under
    the grave) is a FLAT fill drawn on its own RGBA layer, wobbled by
    K.draw_smooth and then blurred. Nothing here ever leaves a crisp rectangle
    or a square corner on the frame — that is the CAD read the brief forbids.
    Returns a new RGB image.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    K.draw_smooth(ld, points, fill=rgb + (int(alpha),), outline=outline,
                  width=width, seed=seed, wobble=wobble,
                  wavelength=wavelength, closed=True)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _soft_beam(img, ox, oy, ang, length, half_deg, rgb, a0=150, steps=18,
               seed=0, blur=16, taper=0.62, wobble=4.0):
    """A beam / veil with alpha falloff ALONG its length and a soft wobbled edge.

    Built from nested cones of decreasing alpha and then blurred, so the shape
    feathers out at its distal end and never shows a hard triangular corner. The
    two faint side lines are drawn with _open_curve at low alpha — a hand hint
    at the cone, not a CAD rule.
    """
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for i in range(steps):
        t = i / float(steps - 1)
        L = 30.0 + t * (length - 30.0)
        half = math.radians(half_deg) * (1.0 - taper * 0.45 * t)
        a = int(a0 * (1.0 - 0.72 * t) ** 1.15) + 4
        p1 = (ox + L * math.cos(ang - half), oy + L * math.sin(ang - half))
        p2 = (ox + L * math.cos(ang + half), oy + L * math.sin(ang + half))
        ld.polygon([(ox, oy), p1, p2], fill=rgb + (a,))
    for sgn, sd in ((-1, seed), (1, seed + 1)):
        pts = []
        for i in range(9):
            u = 0.12 + 0.88 * i / 8.0
            L = 30.0 + u * (length - 30.0)
            hh = math.radians(half_deg) * (1.0 - taper * 0.45 * u)
            pts.append((ox + L * math.cos(ang + sgn * hh),
                        oy + L * math.sin(ang + sgn * hh)))
        _open_curve(ld, pts, rgb + (86,), width=2, seed=sd, wobble=wobble,
                    wavelength=150.0)
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')


def _spike_train(draw, x0, x1, y, n, displace=(), seed=0, color=BONE, width=2,
                 h=34, wobble=1.0, amp=6):
    """The wobble made visible: `n` evenly spaced pulse ticks rising from the
    baseline y, with the peaks whose index is in `displace` shifted sideways.
    Returns the list of (x, y) tip positions."""
    step = (x1 - x0) / float(n)
    tips = []
    for k in range(n):
        cx = x0 + step * (k + 0.5)
        dx = amp if k in displace else 0
        _vline(draw, cx + dx, y, y - h, color, width=width, seed=seed + k,
               wobble=wobble)
        tips.append((cx + dx, y - h))
    return tips


def _tiny(draw, text, cx, cy, fill, px=18):
    """Locked-family REGULAR annotation, centered, no stroke. Diagram labels
    only (the beat's tiny_px=18 is the default here)."""
    font = T.load_font_at(px, bold=False)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    draw.text((cx - w / 2.0 - x0, cy - h / 2.0 - y0), text, font=font, fill=fill)


def _void_card(card, planet, seed):
    """Create a void (space-register) frame and return it. Gradient legal only
    via the starfield backdrop built into void_backdrop; the emissive core, if
    any, is added by the caller with C._radial_core."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=120)
    return img


def _finish(img, card, planet, paper_band, dark_bg):
    """Layout-A tail: title strip, then the schedule-driven character, then the
    one caption call every card in the segment shares."""
    C._header(img, planet, paper_band=paper_band)
    theme = 'dark' if dark_bg else 'light'
    C._draw_stickman(img, card, theme=theme)
    C._caption(img, card['caption'], 70, 652, dark_bg=dark_bg)
    return img


# ---------------------------------------------------------------------------
# 14. how_find — the question beat. CREAM, one dominant subject: the question.
# ---------------------------------------------------------------------------

def render_how_find(card, planet="PSR B1257+12"):
    """CREAM, Register P. The card's ONE subject is a large painted question mark
    — a violet glyph with a 6px ink keyline, built the way the reference builds
    its big drawn marks: thick keyline pass, narrower flat fill pass. It stands
    right of the fixed character (x_center=400) on a soft, blurred violet wash so
    the card reads as a composed illustration rather than three stray marks. The
    old card's 2px '?' + ')' ear + rounded rectangle read as an empty cream field
    with confetti; all three are gone."""
    img = Image.new('RGB', (W, H), PAPER)

    # soft painterly wash behind the glyph (flat violet, blurred — not a gradient)
    img = _soft_wash(img,
                     [(880, 138), (1032, 232), (1056, 424), (938, 584),
                      (760, 560), (700, 378), (772, 208)],
                     VIOLET, 42, seed=82, wobble=18.0, blur=26)
    d = ImageDraw.Draw(img)

    # the question mark: bowl swept 190deg -> 400deg, then the tail into the stem
    qx, qy, R = 880, 300, 112
    glyph = []
    for i in range(15):
        a = math.radians(190.0 + 210.0 * i / 14.0)
        glyph.append((qx + R * math.cos(a), qy + R * math.sin(a)))
    glyph += [(qx + 0.42 * R, qy + 1.02 * R),
              (qx + 0.10 * R, qy + 1.34 * R),
              (qx + 0.02 * R, qy + 1.48 * R)]
    # 36px ink keyline pass, then a 24px flat violet fill pass -> 6px outline.
    # Both are FILLED regions, not wide PIL lines: a wide line on this dense
    # Catmull-Rom path grows hairline nubs at every near-duplicate vertex.
    _thick_curve(d, glyph, INK, seed=83, width=36, wobble=3.0)
    _thick_curve(d, glyph, VIOLET, seed=83, width=24, wobble=3.0)
    K.draw_disc(d, qx, qy + R * 1.48 + 48, 26, fill=VIOLET, outline=INK,
                width=K.OUTLINE, seed=84, wobble=2.0)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# 15. how_signature — the wobble diagram. VOID, no character.
# ---------------------------------------------------------------------------

def render_how_signature(card, planet="PSR B1257+12"):
    """DIAGRAM-ONLY, no character. A bone timing trace: nine evenly spaced
    K.DETAIL spikes, the 4th and 7th peaks displaced 10px right — the wobble
    drawn, not labelled — each with an amber bracket, leader and 'TUG' label,
    over a full-width bone baseline.

    The hero plate is 'SAME EVERY TIME', not 'WOBBLE = TUG': the old line restated
    the caption and the two TUG labels already carry the word. The new line adds
    the fact the card is actually about — the wobble repeats identically, which
    is WHY it can be read as a planet and not as noise."""
    img = _void_card(card, planet, seed=15)
    d = ImageDraw.Draw(img)

    tips = _spike_train(d, 120, 1180, 300, 9, displace=(3, 6), seed=1500,
                        color=BONE, width=K.DETAIL, h=42, wobble=1.0, amp=10)
    # amber bracket + leader under each displaced peak, TUG label beneath
    for k, tip in ((3, tips[3]), (6, tips[6])):
        px = tip[0]
        _hrule(d, 326, px - 28, px + 28, AMBER, width=K.DETAIL, seed=1510 + k)
        _vline(d, px, 320, 300, AMBER, width=K.DETAIL, seed=1520 + k, wobble=0.5)
        _tiny(d, 'TUG', px, 356, BONE)

    _hrule(d, 396, 60, 1220, BONE, width=K.DETAIL, seed=1530, wobble=1.5)
    C.hero_word(d, 'SAME EVERY TIME', 640, 528, BONE, px=64, y_max=620)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 16. how_1990 — the discovery year. VOID + character.
# ---------------------------------------------------------------------------

def render_how_1990(card, planet="PSR B1257+12"):
    """VOID. A bone waveform panel with the wobbled pulse train re-stamped inside
    it, a 64pt '1990' plate (bone fill, 3px ink outline) via C.hero_word, and a
    small VLA stamp. The pulsar was discovered 9 Feb 1990; the two-year gap on
    the next card is the 1990 -> 1992 wait."""
    img = _void_card(card, planet, seed=16)
    d = ImageDraw.Draw(img)

    # waveform panel — midpoints on each edge so the Catmull-Rom rounds the
    # corners instead of ballooning the whole rectangle into a potato
    K.draw_outline(d, [(600, 190), (880, 190), (1160, 190),
                       (1160, 355), (1160, 520), (880, 520),
                       (600, 520), (600, 355)],
                   color=BONE, width=K.DETAIL, closed=True, seed=1600,
                   wobble=1.6, wavelength=140.0)
    # the wobble inside the panel, 0.7 scale
    _spike_train(d, 630, 1130, 452, 6, displace=(2, 5), seed=1602,
                 color=BONE, width=K.DETAIL, h=30, amp=7)
    # the plate
    C.hero_word(d, '1990', 880, 322, BONE, px=64, y_max=500)
    _tiny(d, 'VLA', 1105, 492, BONE)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 17. how_two_years — the wait, and the return. VOID + character.
# ---------------------------------------------------------------------------

def render_how_two_years(card, planet="PSR B1257+12"):
    """VOID. THE WAIT IS THE SUBJECT: two blocks of twelve bone ticks — a year
    each — with an empty, violet-washed gap between them. The gap is the two
    years; nothing is drawn inside it. The 1992 block's final tick is amber with
    a soft wash behind it, so the return is a picture and not a sentence.

    The old 64pt 'IT CAME BACK' plate is gone: it overlapped the bottom of the
    title strip AND it restated the caption's last three words. '1990' / '1992'
    under the two blocks carry the beat with no text redundancy at all."""
    img = _void_card(card, planet, seed=17)
    d = ImageDraw.Draw(img)

    # soft violet wash over the 1990 block only: the waiting half is dimmer
    img = _soft_wash(img,
                     [(616, 386), (846, 372), (862, 470), (832, 492),
                      (628, 480), (598, 432)],
                     VIOLET, 60, seed=1701, wobble=9.0, blur=17)
    # soft amber wash behind the returning tick
    img = _soft_wash(img,
                     [(1168, 396), (1228, 396), (1240, 462), (1186, 480),
                      (1150, 452)],
                     AMBER, 88, seed=1702, wobble=7.0, blur=15)
    d = ImageDraw.Draw(img)

    # two blocks of twelve, y=400..456, K.DETAIL ticks, 20px pitch
    y0, y1, pitch = 400, 456, 20
    for k in range(12):
        x = 630 + k * pitch
        _vline(d, x, y0, y1, BONE, width=K.DETAIL, seed=1710 + k, wobble=0.6)
    for k in range(12):
        x = 1000 + k * pitch
        last = (k == 11)
        _vline(d, x, y0, y1, AMBER if last else BONE, width=K.DETAIL,
               seed=1730 + k, wobble=0.6)

    # the empty wait: two faint amber rules bracketing the gap between the blocks.
    # They are inset toward the middle of the 170px gap and run only 60% of the
    # ticks' height, so they read as brackets rather than as two more ticks.
    for gx, sd in ((898, 1750), (952, 1751)):
        _vline(d, gx, y0 + 8, y1 - 8, AMBER, width=K.FINE, seed=sd, wobble=0.8)

    _tiny(d, '1990', 740, 500, BONE, px=22)
    _tiny(d, '1992', 1100, 500, AMBER, px=22)
    C.hero_word(d, '2 YEARS', 880, 246, BONE, px=72, y_max=340)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 18. how_grave — the dread beat. VOID + the biggest figure so far.
# ---------------------------------------------------------------------------

def render_how_grave(card, planet="PSR B1257+12"):
    """VOID, amber. THE GRAVE IS A REAL OBJECT NOW: one large slate-black mound
    with a bone rim, and a slab marker standing in it, both built from smooth
    wobbled silhouettes with K.OUTLINE keylines. Bone stipple reads as turned
    dirt on the mound.

    The old card was three flat black ellipses that read as spilled ink, plus an
    empty amber ring sitting behind the words like a stray smiley. Both are gone;
    the ring was the one element that competed with the grave for the eye."""
    img = _void_card(card, planet, seed=18)
    d = ImageDraw.Draw(img)

    # a smaller mound further back and right, for depth only
    K.draw_smooth(d, [(1058, 640), (1132, 600), (1224, 590), (1268, 620),
                      (1268, 640)],
                  fill=INK, outline=BONE, width=K.DETAIL, seed=94, wobble=5.0,
                  wavelength=170.0, closed=True)
    # the mound: a smooth dome, flat slate-black fill, bone rim. Its base stops
    # at y=634 so it never runs under the floating caption at y=652.
    K.draw_smooth(d, [(660, 634), (744, 566), (860, 502), (972, 488),
                      (1074, 528), (1150, 588), (1186, 634)],
                  fill=INK, outline=BONE, width=K.OUTLINE, seed=91, wobble=6.0,
                  wavelength=210.0, closed=True)
    # the slab marker, standing in the mound
    K.draw_smooth(d, [(878, 552), (878, 452), (908, 412), (942, 404),
                      (976, 416), (1002, 454), (1002, 552)],
                  fill=INK, outline=BONE, width=K.OUTLINE, seed=92, wobble=3.0,
                  wavelength=150.0, closed=True)
    # turned dirt on the mound — sparse and dim, so it reads as soil not snow
    K.stipple(d, 760, 520, 1080, 610, (110, 118, 124), seed=95, density=0.006,
              r=1, spread=1)

    C.hero_word(d, 'A GRAVE', 940, 300, AMBER, px=64, y_max=400)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 19. how_steady — the metronome. VOID, no character.
# ---------------------------------------------------------------------------

def render_how_steady(card, planet="PSR B1257+12"):
    """DIAGRAM-ONLY, no character. A metronome in bone linework; the pendulum is
    caught mid-swing (+14deg) inside its +/-26deg sweep arc, so the card reads as
    never pausing. It stands on a soft, blurred violet wash — the old hard
    8%-alpha RECTANGLE there was a CAD primitive with square corners, which the
    brief forbids.

    The hero plate is 'NO DRIFT', not 'STEADY AND RHYTHMIC': the old phrase ran
    off the right edge (the hand-rolled _heavy never knew about the 3px keyline)
    and repeated the caption verbatim. hero_word fixes the edge; the new words add
    the fact instead of restating it."""
    img = _void_card(card, planet, seed=19)

    # The wash sits BEHIND the metronome, not beside it — it is the violet stage
    # the metronome stands on. A crisp rectangle here was the CAD read the brief
    # forbids; this is a wobbled, blurred flat field.
    img = _soft_wash(img,
                     [(452, 268), (676, 246), (884, 306), (900, 512),
                      (778, 586), (528, 578), (438, 424)],
                     VIOLET, 62, seed=1900, wobble=16.0, blur=26)
    d = ImageDraw.Draw(img)

    # metronome body (trapezoid), K.OUTLINE
    K.draw_outline(d, [(560, 560), (760, 560), (720, 300), (600, 300)],
                   color=BONE, width=K.OUTLINE, closed=True, seed=1902,
                   wobble=2.2, wavelength=180.0)

    px, py = 660, 320
    # the swing arc: the bob's path from -26deg to +26deg off vertical
    arc_pts = []
    for i in range(13):
        a = math.radians(-26 + 52 * i / 12.0)
        arc_pts.append((px + 210 * math.sin(a), py + 210 * math.cos(a)))
    _open_curve(d, arc_pts, BONE, width=K.FINE, seed=1905, wobble=1.0,
                wavelength=80.0)
    # the pendulum itself, caught mid-swing (+14deg) so it reads as in-motion
    a = math.radians(14)
    bx, by = px + 210 * math.sin(a), py + 210 * math.cos(a)
    _open_curve(d, [(px, py), (px + (bx - px) / 2, py + (by - py) / 2), (bx, by)],
                BONE, width=K.DETAIL, seed=1903, wobble=0.8)
    K.draw_disc(d, px, py, 10, fill=None, outline=BONE, width=K.DETAIL, seed=1904)
    K.draw_disc(d, bx, by, 13, fill=BONE, outline=BONE, width=K.DETAIL, seed=1906)

    # hero sits right of the whole metronome assembly (which ends at x~760)
    C.hero_word(d, 'NO DRIFT', 1032, 424, BONE, px=64, y_max=600)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 20. how_tug — the tug made visible. VOID + character.
# ---------------------------------------------------------------------------

def render_how_tug(card, planet="PSR B1257+12"):
    """VOID. THE BEAM IS THE SUBJECT, and it now has a source: an emissive
    pulsar core (the one legal gradient on this beat) at the left, firing a
    feathered amber beam down-right, with a small painterly planet riding in it.
    The old card was a hard-edged crisp triangle floating in space with nothing
    emitting it — the CAD read the brief calls out by name. Here the beam is
    nested alpha cones + a Gaussian blur, so it dissolves at its distal end.

    The schedule ladder moves to x=60..300, clear of the character's pointing arm."""
    img = _void_card(card, planet, seed=20)

    # The emissive core that fires the beam — gradient is legal here and only
    # here. It sits high and well LEFT (x=210) so the character's head and its
    # glow never sit on top of it.
    core_x, core_y = 210, 258

    # beam wedge: soft, feathered, alpha-falling along its length. Its axis is
    # aimed straight down the core->planet line so the beam reads as the thing
    # the planet is pulling on. a0 is high enough that the beam is the card's
    # dominant shape, not a faint smudge.
    img = _soft_beam(img, core_x, core_y, math.radians(13.6), 860.0, 14.0,
                     AMBER, a0=190, steps=22, seed=2001, blur=22, taper=0.70)
    d = ImageDraw.Draw(img)

    C._radial_core(img, core_x, core_y, 40,
                   [(255, 255, 255), BONE, (60, 52, 92)])

    # the tug: a small painterly planet riding in the beam, lurched 8px upstream
    px, py = 1010, 452
    dx, dy = px - core_x, py - core_y
    n = math.hypot(dx, dy)
    ox, oy = 8 * dx / n, 8 * dy / n
    img = C.space_body(img, int(round(px + ox)), int(round(py + oy)), 19,
                       seed=2002, bands=2)
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse([px + ox - 26, py + oy - 26, px + ox + 26, py + oy + 26],
              outline=AMBER + (215,), width=K.DETAIL)

    # schedule ladder, well left of the character's pointing arm; five rungs,
    # one lit amber
    d = ImageDraw.Draw(img)
    for k in range(5):
        x = 60 + k * 60
        _vline(d, x, 546, 592, AMBER if k == 2 else BONE, width=K.DETAIL,
               seed=2010 + k, wobble=0.6)
    _hrule(d, 569, 60, 300, BONE, width=K.FINE, seed=2020)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 21. how_first — the payoff. VOID + character.
# ---------------------------------------------------------------------------

def render_how_first(card, planet="PSR B1257+12"):
    """THE PAYOFF. The only B4 card with the full 3-stop gradient, because it is
    the only one where the star is good news. The three planets sit on the two
    inner orbit rings as painterly space bodies (C.space_body, no black
    outline), each with a flat amber ring highlight. The heavy 'FIRST EVER'
    plate goes through C.hero_word so it can never ride up into the strip."""
    img = _void_card(card, planet, seed=21)
    d = ImageDraw.Draw(img)

    cx, cy = 880, 320
    # two inner orbit rings (K.DETAIL bone, flat — never a gradient)
    for rx, ry in ((170, 58), (300, 100)):
        pts = [(cx + rx * math.cos(math.tau * i / 40),
                cy + ry * math.sin(math.tau * i / 40)) for i in range(40)]
        K.draw_outline(d, pts, color=BONE, width=K.DETAIL, closed=True,
                       seed=2110 + int(rx), wobble=1.0)

    # The emissive core — the one legal gradient in this beat. Integer cx/cy:
    # cardframe's glow pass crops/pastes with these, and PIL needs ints.
    C._radial_core(img, int(cx), int(cy), 40,
                   [(255, 255, 255), BONE, (60, 52, 92)])

    # three painterly planets on the two inner rings (no black outline)
    spots = [(200, 170, 58, 18, 2120), (20, 170, 58, 22, 2121),
             (320, 300, 100, 34, 2122)]
    for ang_deg, rx, ry, r, sd in spots:
        a = math.radians(ang_deg)
        px = int(round(cx + rx * math.cos(a)))
        py = int(round(cy + ry * math.sin(a)))
        bands = 2 if r < 20 else 3
        img = C.space_body(img, px, py, r, seed=sd, bands=bands)
        dd = ImageDraw.Draw(img, 'RGBA')
        dd.ellipse([px - r - 5, py - r - 5, px + r + 5, py + r + 5],
                   outline=AMBER + (255,), width=K.FINE)

    d = ImageDraw.Draw(img)
    C.hero_word(d, 'FIRST EVER', cx, 152, AMBER, px=64, y_max=280)

    d = ImageDraw.Draw(img)
    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

RENDERERS = {
    'how_find': render_how_find,
    'how_signature': render_how_signature,
    'how_1990': render_how_1990,
    'how_two_years': render_how_two_years,
    'how_grave': render_how_grave,
    'how_steady': render_how_steady,
    'how_tug': render_how_tug,
    'how_first': render_how_first,
}


def register(mapping=None):
    """Merge this beat's renderers into the shared dispatch table. No import
    side effects: the frame generator calls this (or uses RENDERERS directly)."""
    C.RENDERERS.update(RENDERERS if mapping is None else mapping)
    return C.RENDERERS
