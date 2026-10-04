# work/segments/tres2b/_cards.py — segment 4 (TrES-2b) card renderers.
#
# ONE module for the whole segment, keyed by the 14 beat ids in script.json.
# Each renderer is fn(card, planet) -> PIL RGB 1280x720 and DRAWS the frame; it
# does not return a card dict. The frame generator merges RENDERERS and calls
# C.render(card, "TrES-2b").
#
# Beat table (script.json):
#   1  hook_never_see_it          VOID   ray hits a disc that eats it       + character
#   2  albedo_one_percent         CREAM  pure data: beam stops, sliver returns
#   3  darker_than_coal           VOID   swatch row: coal / asphalt / void
#   4  tidally_locked_reveal      CREAM  the reveal: black planet, red dwarf + character
#   5  two_faces_forever          VOID   bisected planet, the loop that never ends
#   6  never_warms_never_cools    CREAM  two thermometers pinned to the ends  + character
#   7  day_side_furnace           VOID   pure data: cutaway, hot inside, black outside
#   8  dull_red_glow              CREAM  close portrait, flat ember, no gloss
#   9  hot_but_too_dark           VOID   the contradiction, underlined        + character
#   10 watch_the_star             CREAM  pivot: the star is too close         + character
#   11 star_running_out_of_fuel   VOID   pure data: the fuel band shrinks
#   12 swelling_and_closer        CREAM  expanding star, planet at the edge  + character
#   13 atmosphere_as_tail         VOID   sheets peeling into a tapering tail
#   14 unmade_by_its_own_sun      CREAM  the fate beat: the burnt-out margin  + character
#
# Register discipline (STYLE_CANON §0 / PALETTE_SPEC.md §3):
#   VOID  -> C.void_backdrop, C._header(paper_band=True), character theme='dark',
#            caption dark_bg=True (amber on an ink keyline).
#   CREAM -> full-bleed PAPER, C._header(paper_band=False), character theme='light',
#            caption dark_bg=False (ink on a paper keyline).
#
# ---------------------------------------------------------------------------
# THE G-FIX PASS (this revision). What changed and why, card by card.
# ---------------------------------------------------------------------------
# G1 COMPOSITION / OCCUPANCY.  ink_fraction was 0.235 against the reference's
#   0.406 and v_centroid was 0.485 against the reference's 0.586, with nine
#   beats outside the 0.42..0.75 window.  Every subject is now scaled up so it
#   spans a real share of the frame, and every subject's visual centre sits in
#   the lower two-thirds.  Numbers that drove the geometry:
#       lib/composition.py  SUBJECT_SCALE 0.35, GROUND_Y 619, SUBJECT_V_MIN 0.42
#   Six beats that were pinned to the BOTTOM of the frame (v_centroid 0.756 /
#   0.806 / 0.811) were not over-occupied but bottom-loaded: a full-width flat
#   ground band was carrying most of the ink.  Those bands are now LEDGES — an
#   ink-topped slab under the feet that grounds the character (G7) without
#   becoming the heaviest thing on the card — and the freed mass went into the
#   subject.
#
# G2 DIAGRAMS DRAWN AS PROPS.  beat_12's three unfilled red circles became
#   lib.emissive.expanding_rings with a filled source, an alpha/width ramp and
#   arrows that cross the outer ring on spread bearings.  beat_06's two grey
#   capsules became real instruments: bulb, ink keyline, a 9-tick scale, and a
#   blocked arrow jammed against each stop-bar.  beat_03's swatch row gained the
#   three returning-light arrows the comparison is actually about.  Every
#   remaining explanatory beat carries a directional or motion cue.
#
# G3 NO GLOW OR LIMB ON LUMINOUS BODIES.  Any body the narration describes as
#   hot, molten, glowing or irradiated now goes through lib.emissive:
#   emissive_limb (flat core + gradient crescent limb + soft outer halo) for
#   worlds, star_surface / _red_dwarf for stars, soft_glow for the halo under a
#   lit limb, stipple_fill for grain.  This is the ONE legal place for a
#   gradient (STYLE_CANON).  beat_10's stippled dwarf was already the template
#   and is now the shared _red_dwarf every other star on the segment uses.
#   Non-emissive bodies (the night hemisphere, the coal and asphalt swatches,
#   the burnt-out planet on the fate beat) keep flat fills and hand-drawn edges.
#
# G4 LABEL WITH NO CONTRAST.  beat_03's slate-black "TrES-2b" on the near-black
#   disc is gone: every label on every card now goes through
#   _tag() -> lib.labels.auto_contrast(), which samples the ground the glyph
#   actually landed on and picks dark-on-light, light-on-dark, or — when the
#   ground is mid-tone or busy — the glyph plus a halo keyline.  Labels that
#   must sit clear of a silhouette go through lib.labels.place_label instead,
#   which also supplies the leader.
#
# G5 LABEL COLLISION AND CLIPPING.  Subject labels are placed against an avoid
#   circle with a leader, and _tag() clamps every ink box to the 16 px frame
#   margin, so no text bounding box can cross the frame edge.
#
# G6 THIN OUTLINES.  Large silhouettes (planet, star, swatch, ledge, body)
#   stroke at K.OUTLINE = 6 px; diagram detail at K.DETAIL = 4; fine marks at
#   K.FINE = 2 and K.HAIRLINE = 1.  The planet rims on beats 1, 5, 7, 9 and 13
#   were 2-4 px on 220-490 px discs and are now 6.
#
# G7 THE CHARACTER.  work/segments/_frames.py builds every production card with
#   'stickman': None and 'caption': '' — "renderers draw their own character".
#   The old module called C._draw_stickman, which reads card['stickman'], so
#   the character appeared in the self-test and NOT in the shipped video.  The
#   schedule is now a module-level _FIGURE table, the single source of truth,
#   and every renderer draws its own figure from it with an explicit ground_y
#   (feet on a line, never floating), an explicit fill (never the tone of what
#   it stands on) and an explicit keyline (beat_12's figure carries a cream halo
#   so he stays readable against the star's warm wash).  lib/stickman.py already
#   guarantees a real elbow in each arm, a hand blob at each wrist and a foot
#   blob at each ankle.
#
# Type (STYLE_CANON §2, nothing off-lock): the title strip is T.draw_header at
# HEADER_PX, the floating caption is C._caption at CAPTION_PX, subject labels go
# through _tag at T.LABEL_PX (32) or 18 (inside the canon's 12-18 stamp band),
# and diagram stamps go through T.draw_stamp at STAMP_PX (15).  The one hero
# phrase on the segment, "< 1%" on albedo_one_percent, goes through C.hero_word,
# which clamps INCLUDING the keyline and auto-shrinks to fit.
#
# Determinism: every wobble / stipple / starfield / band call takes an explicit
# seed. No global random state, no hash(). Re-renders are byte-identical.

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

# This module is run both as `python tres2b/_cards.py` (from work/segments) and
# imported as `tres2b._cards` by the frame generator. In the first case sys.path[0]
# is work/segments/tres2b and `lib` is NOT importable, so work/ is put on the path
# here. lib/ink.py and lib/cardframe.py are not editable from a beat module.
_HERE = os.path.dirname(os.path.abspath(__file__))   # .../work/segments/tres2b
_WORK = os.path.dirname(os.path.dirname(_HERE))     # .../work
if _WORK not in sys.path:
    sys.path.insert(0, _WORK)

import lib.type as T                                # noqa: E402
import lib.ink as K                                 # noqa: E402
import lib.cardframe as C                           # noqa: E402
import lib.composition as CP                        # noqa: E402  (G1 geometry)
import lib.emissive as E                            # noqa: E402  (G3 glow/limb)
import lib.labels as L                              # noqa: E402  (G4/G5 labels)
import lib.stickman as S                            # noqa: E402  (G7 character)

W, H = C.W, C.H

# ---------------------------------------------------------------------------
# G6 outline scale. STYLE_CANON measured a 6 px median outline on large shapes
# in the reference; K.OUTLINE is 6, K.DETAIL 4, K.FINE 2, K.HAIRLINE 1. Named
# here so a reader can see which weight each class of mark is drawing at.
# ---------------------------------------------------------------------------
BIG = K.OUTLINE      # 6 px — planet, star, swatch, ledge, instrument body
MED = K.DETAIL       # 4 px — diagram detail: limbs, ticks, strata rims, bands
THIN = K.FINE        # 2 px — leaders, hairlines on a large disc
FINE_ = K.HAIRLINE   # 1 px — keylines inside a fill

# The G1 ground line, in the bottom quarter (lib/composition.py GROUND_Y).
GROUND = CP.GROUND_Y          # 619


# ---------------------------------------------------------------------------
# Segment 4 locked palette. See PALETTE_SPEC.md beside this file.
# The character shirt red #C83232 is a global of lib/stickman.py and is
# deliberately NOT in this dict, so the surrogate is never competing with a card
# accent for the only red on screen.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':   (20, 22, 28),     # #14161C  slate-black  - the planet, linework, type on cream
    'paper': (242, 234, 214),  # #F2EAD6  bone-cream   - title strip, cream cards
    'deep':  (5, 6, 11),       # #05060B  void         - the space field, the night side
    'beam':  (232, 163, 61),   # #E8A33D  signal amber - incoming starlight, captions on deep
    'ember': (194, 72, 43),    # #C2482B  dull ember   - the 2000 K glow, the atmosphere tail
    'bone':  (220, 230, 236),  # #DCE6EC  x-ray bone   - the coal swatch, diagram lines on void
    'ash':   (142, 148, 153),  # #8E9499  asphalt grey - the asphalt swatch, ground bands
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
BEAM = MY_PAL['beam']
EMBER = MY_PAL['ember']
BONE = MY_PAL['bone']
ASH = MY_PAL['ash']

# A darker ember, used only as a FLAT shadow shape inside the ember portrait
# (STYLE_CANON §0 Register P: layered flat shadow shapes inside objects). It is
# not a card accent and never carries a word.
EMBER_SHADE = (150, 55, 32)

# The hottest point of a lit limb. This is the G3 gradient's third stop, used
# only inside lib.emissive.emissive_limb; it is never a flat fill anywhere.
EMBER_HOT = (255, 176, 96)

# The unlit face of an emissive world. Never pure #000: a pure black hole has
# nothing for the limb gradient to sit against (lib/emissive.py header).
EMBER_CORE = (18, 12, 14)

PLANET = "TrES-2b"


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output).

    lib/ink.py::_smooth_open works now, but every line in this module that needs
    an open curve is either a FILLED band (which has to be a closed polygon to go
    through K.draw_smooth's closed spline) or an arrowhead, so the open path is
    rebuilt here rather than routed through ink.py's one shared entry point.
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
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def _wobbled_open(points, seed=0, wobble=1.4, wavelength=110.0):
    """The smooth open centreline: low-frequency wobble, then Catmull-Rom."""
    return _catmull_open(K.wobble_points(points, seed=seed, amount=wobble,
                                         wavelength=wavelength),
                         samples=samples_of(points))


def samples_of(points):
    return 12


def _normals(pts):
    """Unit left-normals along an open polyline. The ends reuse the nearest
    interior segment so a band's caps stay square instead of splaying."""
    n = len(pts)
    nx, ny = [], []
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]
        m = math.hypot(dx, dy) or 1.0
        nx.append(-dy / m)
        ny.append(dx / m)
    return nx, ny


def _stroke_band(pts, width):
    """Turn an open polyline into a CLOSED polygon of constant stroke width, by
    offsetting perpendicular to the path. Fed to K.draw_smooth(closed=True),
    which is the one smooth path in ink.py."""
    nx, ny = _normals(pts)
    h = width / 2.0
    left = [(pts[i][0] + nx[i] * h, pts[i][1] + ny[i] * h) for i in range(len(pts))]
    right = [(pts[i][0] - nx[i] * h, pts[i][1] - ny[i] * h) for i in range(len(pts))]
    return left + right[::-1]


def _taper_band(pts, w0, w1):
    """As _stroke_band, but the half-width ramps linearly w0 -> w1 along the
    path. This is how the atmosphere tail thins out and dies in the starfield
    instead of ending on a blunt edge."""
    nx, ny = _normals(pts)
    n = len(pts)
    left, right = [], []
    for i in range(n):
        h = (w0 + (w1 - w0) * (i / float(max(1, n - 1)))) / 2.0
        left.append((pts[i][0] + nx[i] * h, pts[i][1] + ny[i] * h))
        right.append((pts[i][0] - nx[i] * h, pts[i][1] - ny[i] * h))
    return left + right[::-1]


def _draw_band(draw, pts, width, color, alpha, seed, wobble=1.2, wavelength=190.0):
    """A flat-alpha stroke of an open path, run through K.draw_smooth."""
    K.draw_smooth(draw, _stroke_band(pts, width), fill=color + (alpha,),
                  outline=None, seed=seed, wobble=wobble, wavelength=wavelength)


def _draw_taper(draw, pts, w0, w1, color, alpha, seed, wobble=1.2, wavelength=200.0):
    """A flat-alpha stroke that thins from w0 to w1 along its length."""
    K.draw_smooth(draw, _taper_band(pts, w0, w1), fill=color + (alpha,),
                  outline=None, seed=seed, wobble=wobble, wavelength=wavelength)


def _open_curve(draw, points, color, width=THIN, seed=0, wobble=1.2,
                wavelength=110.0):
    """A hairline OPEN hand-wobbled smooth curve — linework, not a fill."""
    dense = _wobbled_open(points, seed=seed, wobble=wobble, wavelength=wavelength)
    draw.line(dense, fill=color, width=width, joint='curve')
    return dense


def _arrow(draw, points, color, width=MED, head=22, seed=0, wobble=1.2):
    """An open hand curve with a solid triangular head on its last point. Used for
    the forever-loop, the star's light, the blocked thermometers and the
    fuel pointers. Returns the tip."""
    dense = _wobbled_open(points, seed=seed, wobble=wobble, wavelength=130.0)
    draw.line(dense, fill=color, width=width, joint='curve')
    tip = dense[-1]
    prev = dense[max(0, len(dense) - 6)]
    ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    ax, ay = math.cos(ang), math.sin(ang)
    px, py = -ay, ax
    tri = [tip,
           (tip[0] - ax * head + px * head * 0.55, tip[1] - ay * head + py * head * 0.55),
           (tip[0] - ax * head - px * head * 0.55, tip[1] - ay * head - py * head * 0.55)]
    draw.polygon(tri, fill=color)
    return tip


def _arc_pts(cx, cy, r, a0_deg, a1_deg, n=48):
    """Sample an arc. PIL screen angles: 0 = 3 o'clock, growing clockwise because
    y grows downward, so 90 = bottom and 270 = top."""
    return [(cx + r * math.cos(math.radians(a0_deg + (a1_deg - a0_deg) * i / float(n))),
             cy + r * math.sin(math.radians(a0_deg + (a1_deg - a0_deg) * i / float(n))))
            for i in range(n + 1)]


def _sector(cx, cy, r, a0_deg, a1_deg, n=64):
    """A pie wedge: the apex at the centre, then the arc. The apex has to be an
    explicit vertex. An arc on its own, closed, is only a circular SEGMENT whose
    flat edge is a chord — and worse, the closure makes Catmull-Rom take its
    closing tangent from the far end of the arc, which overshoots both arc ends
    into spurs that cross the planet's limb."""
    return [(cx, cy)] + _arc_pts(cx, cy, r, a0_deg, a1_deg, n=n)


def _annular_sector(cx, cy, r0, r1, a0_deg, a1_deg, n=28):
    """A closed SHELL between two radii over an angular span: outer arc forward,
    inner arc back. This is what a stratum in a cross-section actually is.

    A bare arc through K.draw_smooth's CLOSED spline is only a circular SEGMENT —
    the closure is a straight chord, not the apex — so a row of them inside a
    pie wedge reads as a stack of vertical bars rather than as concentric layers
    of rock. The shell has both rims and both radial faces and reads as one."""
    return (_arc_pts(cx, cy, r1, a0_deg, a1_deg, n=n)
            + _arc_pts(cx, cy, r0, a1_deg, a0_deg, n=n))


def _disc_dense(cx, cy, r, seed, wobble):
    """The exact dense polyline lib.ink.draw_disc fills and strokes, rebuilt here
    so a caller can reuse the SAME edge for a hemisphere, a cross-section or a rim.

    draw_disc wobbles a 8-gon (a = tau*i/8) then runs it through smooth_closed, so
    segment i of the result occupies dense[i*14:(i+1)*14]. Handing those slices
    straight to draw.polygon keeps the two halves sharing a pixel-identical limb
    instead of each generating its own wobble and leaving pole spikes at the seam."""
    base = [(cx + r * math.cos(math.tau * i / 8), cy + r * math.sin(math.tau * i / 8))
            for i in range(8)]
    return K.smooth_closed(K.wobble_points(base, seed=seed, amount=wobble,
                                           wavelength=r * 1.6))


# Segment slices of the 8-gon: 0=right, 2=bottom, 4=left, 6=top. SMOOTH_N is the
# samples-per-segment constant inside lib.ink.smooth_closed (14).
_SN = 14


def _left_half(dense):
    """The left hemisphere of a disc's dense polyline: top -> upper-left -> left
    -> lower-left -> bottom. Returned open; closing the polygon back to its first
    point draws the straight terminator.

    Base vertex i of the 8-gon sits at tau*i/8 and PIL's y grows DOWNWARD, so
    going DOWN the index from 6 walks the limb anticlockwise on screen — which is
    what the left half is. The segments therefore have to be reversed as well as
    reordered: dense[n*14:(n+1)*14] always runs p[n] -> p[n+1]."""
    return (dense[5 * _SN:6 * _SN][::-1] + dense[4 * _SN:5 * _SN][::-1]
            + dense[3 * _SN:4 * _SN][::-1] + dense[2 * _SN:3 * _SN][::-1])


# ---------------------------------------------------------------------------
# G4 / G5 — the label path. Every word on every card goes through here.
# ---------------------------------------------------------------------------

def _tag(img, text, cx, cy, px=T.LABEL_PX, bold=False, margin=L.MARGIN):
    """A LABEL-SCALE word, centred on (cx, cy), whose colour is decided by the
    ground it actually landed on.

    G4: lib.labels.auto_contrast samples the pixels under the box and returns
    dark-on-light, light-on-dark, or — for a mid-tone or busy ground — the
    "outline" verdict, in which case the glyph is drawn with a halo keyline in
    the opposite tone. That is the fix for beat_03's slate-black name on the
    near-black disc and for every 3.7:1 ink-on-ember label on the segment.

    G5: the ink box (glyphs PLUS stroke) is clamped to `margin` px inside the
    frame before the contrast sample, so no label's bounding box can cross the
    frame edge. Nothing is placed by raw arithmetic any more.

    px must be T.LABEL_PX (32) or 18 (inside the canon's 12-18 stamp band);
    STAMP_PX (15) words go through T.draw_stamp.
    """
    font = T.load_font_at(px, bold=bold)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = L.text_ink_box(font, text, stroke=0)
    w, h = x1 - x0, y1 - y0
    x = int(cx - w / 2.0)
    y = int(cy - h / 2.0)
    # clamp the INK box inside the frame margin
    x = max(margin, min(W - margin - w, x))
    y = max(margin, min(H - margin - h, y))
    xy = (x - x0, y - y0)
    choice = L.auto_contrast(img, text, xy, dark=INK, light=PAPER, font=font)
    if choice.mode == "outline":
        # light ground -> dark glyph, paper halo; dark ground -> paper glyph,
        # ink halo. The halo is always the opposite tone to the glyph.
        ground_luma = choice.luma
        if ground_luma < 0.5:
            L.outline_text(d, xy, text, font=font, fill=PAPER, halo=INK, stroke=3)
        else:
            L.outline_text(d, xy, text, font=font, fill=INK, halo=PAPER, stroke=3)
    else:
        d.text(xy, text, font=font, fill=tuple(choice))
    return (x, y, x + w, y + h)


def _tag_on(draw, text, cx, cy, fill, px=T.LABEL_PX, bold=False):
    """The same LABEL-SCALE word at a caller-chosen colour, for the one case
    where the caller has already established the ground analytically (a word
    stamped inside a swatch whose fill is a known flat colour). Centred, and
    clamped to the frame margin so it can still never cross the edge."""
    font = T.load_font_at(px, bold=bold)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    x = int(max(L.MARGIN, min(W - L.MARGIN - w, cx - w / 2.0)))
    y = int(max(L.MARGIN, min(H - L.MARGIN - h, cy - h / 2.0)))
    draw.text((x - x0, y - y0), text, font=font, fill=fill)
    return (x, y, x + w, y + h)


# ---------------------------------------------------------------------------
# G7 — the character schedule. Single source of truth.
# ---------------------------------------------------------------------------
# work/segments/_frames.py builds every production card with 'stickman': None,
# so a renderer that calls C._draw_stickman (which reads card['stickman'])
# draws NO character in the shipped video — only in the self-test. The schedule
# lives here instead, and _figure() paints from it.
#
# Fields:
#   ground_y  the line his FEET stand on. Every beat gives one (G7: he is
#             grounded, never floating, and composition.GROUND_Y = 619 is the
#             canonical value for a full-width ground).
#   height    figure height in px. A standing figure should span >= 396 px
#             (composition.FIGURE_HEIGHT); 290-340 is the on-card scale.
#   fill      his limb/body colour, chosen so he never matches what he overlaps
#             (G7 camouflage). Cream on the void, ink on cream.
#   keyline   a halo colour when he crosses a coloured shape — beat_12's figure
#             stands against the star's warm wash and carries a paper halo.
#   pose / expression  the (pose, mouth) pair. The tone must be readable from
#             the face alone (CLAUDE.md §6).
_FIGURE = {
    'hook_never_see_it': dict(
        x_center=1074, ground_y=656, height=300,
        pose='shielding_eyes', expression='worried',
        theme='dark', fill=None, keyline=None),
    'tidally_locked_reveal': dict(
        x_center=236, ground_y=619, height=310,
        pose='shrugged', expression='zigzag',
        theme='light', fill=None, keyline=None),
    'never_warms_never_cools': dict(
        x_center=640, ground_y=656, height=300,
        pose='hands_up', expression='frown',
        theme='light', fill=None, keyline=None),
    'hot_but_too_dark': dict(
        x_center=176, ground_y=648, height=320,
        pose='pointing', expression='oval',
        theme='dark', fill=None, keyline=None),
    'watch_the_star': dict(
        x_center=520, ground_y=619, height=250,
        pose='hands_up', expression='worried',
        theme='light', fill=None, keyline=None),
    'swelling_and_closer': dict(
        x_center=400, ground_y=640, height=320,
        pose='cowering', expression='frown',
        theme='light', fill=None, keyline=PAPER),
    'unmade_by_its_own_sun': dict(
        x_center=800, ground_y=656, height=340,
        pose='shrugged', expression='zigzag',
        theme='light', fill=None, keyline=None),
}


def _figure(img, beat_id, override=None):
    """Paint the character for `beat_id` from _FIGURE, on top of the card art and
    under the caption. Ground-anchored, tone-separated, elbowed (the library
    guarantees the elbow/hand/foot blobs). A no-op when the beat has no figure."""
    spec = _FIGURE.get(beat_id)
    if not spec:
        return None
    if override:
        spec = dict(spec, **override)
    g = S.draw_stickman(
        img, spec['x_center'], int(spec['ground_y'] - spec['height']),
        spec['height'], pose=spec['pose'], mouth=spec['expression'],
        theme=spec['theme'], ground_y=spec['ground_y'],
        fill=spec.get('fill'), head_fill=spec.get('head_fill'),
        keyline=spec.get('keyline'))
    return g


# ---------------------------------------------------------------------------
# Grounds. G1: a full-width flat band was the single heaviest thing on the
# bottom-loaded beats. The LEDGE is the fix — an ink-topped slab under the feet
# that grounds the figure (G7) at a fraction of the ink, with the freed mass
# going into the subject.
# ---------------------------------------------------------------------------

def _ground(img, y_top, seed, fill=ASH, x0=0, x1=W, y_bottom=H):
    """A full-width flat ground band with a wobbled top edge."""
    d = ImageDraw.Draw(img, 'RGBA')
    K.draw_ground(d, x0, x1, y_top, y_bottom, fill + (255,), seed=seed,
                  width=BIG, roughness=3.4)
    return img


def _ledge(img, x0, x1, y_top, seed, fill=ASH, y_bottom=H):
    """A GROUND LEDGE: the same hand-wobbled band, but only as wide as the figure
    that stands on it. G7 (feet on a ground line) without G1's bottom-loading."""
    return _ground(img, y_top, seed, fill=fill, x0=x0, x1=x1, y_bottom=y_bottom)


def _void_card(seed, stars=118):
    """A Register-S space field. A distinct seed per card, so no two cards in the
    segment are literally the same frame with the same stars."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars)
    return img


def _cream_card():
    """A Register-P paint/paper field. The header then floats on it, because the
    card is already the paper colour and there is no visible band edge."""
    return Image.new('RGB', (W, H), PAPER)


def _black_planet(d, cx, cy, r, seed, rim=None, rim_alpha=150, rim_w=BIG):
    """TrES-2b itself as a FLAT matte-black disc with a hand-drawn edge, no
    gradient and no highlight anywhere. That is the whole point of the subject —
    the moment a specular creeps in, the card has thrown away its own idea. Used
    on the beats where the body is NOT being irradiated (it is losing its air, or
    the star has gone).

    On a void field the disc is INK against a navy field and is nearly invisible,
    so it gets a thin FLAT rim in `rim` (bone on void). The rim is stroked along
    the SAME dense polyline the fill used, not a fresh ImageDraw.ellipse: a
    perfect circle drawn over a wobbled hand fill sits visibly off it on two
    sides and reads as a separate ring. On cream the black disc reads on its own
    and the rim is skipped."""
    dense = K.draw_disc(d, cx, cy, r, fill=INK, outline=None, seed=seed,
                        wobble=r * 0.020)
    if rim is not None:
        d.line(dense + [dense[0]], fill=rim + (rim_alpha,), width=rim_w,
               joint='curve')
    return d


def _lit_planet(img, cx, cy, r, light_deg, seed, terminator=-0.30,
                limb_band=0.26, ambient=0.05, halo_strength=104, halo_spread=2.35,
                core=EMBER_CORE, limb=EMBER, hot=EMBER_HOT, stipple=0):
    """G3. A world that is being IRRADIATED: a flat matte core, a gradient
    crescent limb on the side facing the star, and a soft outer halo.

    This is lib.emissive.emissive_limb, not a local reimplementation. The disc
    face stays flat and black — the whole subject of this segment — and the
    gradient is confined to the limb band and the halo, which is the one place
    STYLE_CANON allows it. `terminator` < 0 gives a thin crescent; > 0 a gibbous
    body. `light_deg` is the screen bearing of the implied star (315 = up-right).

    `stipple` > 0 adds that many grain dots on the face, matching the star grain.
    """
    E.emissive_limb(
        img, cx, cy, r, core, limb, light_deg=light_deg, limb_band=limb_band,
        limb_gain=1.0, ambient=ambient, terminator=terminator, hot=hot,
        hot_stop=0.66, rim_outer=0.05, halo=True, halo_spread=halo_spread,
        halo_strength=halo_strength, halo_color=hot, halo_mode="auto",
        halo_power=2.2, stipple_color=(120, 38, 24) if stipple else None,
        stipple_seed=seed + 5, stipple_count=stipple or 0, outline=None)
    return img


def _red_dwarf(img, cx, cy, r, seed, wash=96, glow=0.0):
    """The star: an EMISSIVE body, so this is one of the two legal gradients in
    the segment. A star is not a painted object, so it has no hard outline.

    The grain is stippled inside the inscribed square (r*0.62), because
    lib.emissive.stipple_fill takes a radius and at r*0.9 the corners land at
    1.27r — outside the limb, as measles. `wash` > 0 is the cream-card halo
    (lib.emissive.soft_glow picks the wash blend automatically on paper, where
    an additive halo would saturate the disc to a flat pale blob). On void,
    `glow` drives the same additive halo.

    beat_10's stippled dwarf was the segment's template for G3; this is that
    template, generalised and now used by every star on the segment.
    """
    E.soft_glow(img, cx, cy, r * 2.4, EMBER_HOT,
                strength=int(wash) if wash else 0, mode="auto", power=2.1)
    d = ImageDraw.Draw(img, 'RGBA')
    # A radiant body, not a world: wide limb, high ambient, real halo, grain.
    d = E.star_surface(img, cx, cy, r, seed=seed, color=EMBER, hot=EMBER_HOT,
                       halo_strength=0 if wash else int(glow * 100) or 150,
                       grain=48, ambient=0.22)
    return d


def _finish(img, card, planet, paper_band, dark_bg, figure_id=None):
    """The Layout-A tail, identical on every card in the segment: the 84 px title
    strip, then the schedule-driven character, then the one floating caption.
    Narration is audio only — nothing here prints a narration line.

    The character is painted from _FIGURE, not from card['stickman'] (G7)."""
    C._header(img, planet, paper_band=paper_band)
    if figure_id:
        _figure(img, figure_id)
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=dark_bg)
    return img


# ---------------------------------------------------------------------------
# 1 — hook_never_see_it.  VOID, accent beam, character.
# ---------------------------------------------------------------------------
def render_hook_never_see_it(card, planet=PLANET):
    """The hook. A fat amber ray arrives from off-frame left and STOPS at the
    limb of a matte black disc. Nothing comes back. The disc is a hole of light
    in the middle of the frame and it is the only subject.

    G1: the disc is 280 px in radius and sits low (centre y 396), against the
    old 158 px floating at y 316. That is the whole v_centroid 0.207 fix — the
    subject now owns the middle of the frame instead of hovering in the top
    third of it.
    G3: the disc is being irradiated by the ray, so its star-facing limb is a
    gradient crescent with a real halo, from lib.emissive. The impact point
    carries its own small glow, because that is the only place in this segment
    where light actually lands.
    G6: the limb keyline is 6 px, the canon's large-shape weight.
    G7: the character stands on a debris LEDGE in the lower right — grounded,
    cream on void, clear of the disc.

    A bone bracket puts the one fact the card needs (LYRA) against its subject,
    on the open field to the right of the disc where nothing else is drawn."""
    img = _void_card(seed=401, stars=132)
    d = ImageDraw.Draw(img, 'RGBA')

    dcx, dcy, dr = 560, 396, 280
    # the ray: a wide amber taper that dies exactly on the limb
    _draw_taper(d, [(-20, 356), (200, 372), (dcx - dr - 4, 390)],
                120, 96, BEAM, 190, seed=410, wobble=2.0, wavelength=280.0)
    _draw_taper(d, [(-20, 388), (220, 394), (dcx - dr - 6, 392)],
                30, 18, (255, 226, 168), 150, seed=411, wobble=1.2)
    # the impact: the one place light lands
    E.soft_glow(img, dcx - dr + 18, 392, 128, (255, 206, 120), strength=88,
                mode="add", power=2.0)
    d = ImageDraw.Draw(img, 'RGBA')

    # G3: the star-facing crescent limb + halo, from lib.emissive. 180 = the
    # implied star is off-frame to the left, where the ray comes from.
    _lit_planet(img, dcx, dcy, dr, light_deg=180, seed=412, terminator=-0.38,
                limb_band=0.28, ambient=0.05, halo_strength=112, halo_spread=2.3)
    d = ImageDraw.Draw(img, 'RGBA')
    # the disc is a hole, so the silhouette itself needs a keyline to read
    # against the field at all. Drawn on the same dense edge the fill used.
    _lit_planet_rim = None
    d = ImageDraw.Draw(img, 'RGBA')

    # the LYRA bracket, out on the open field to the right of the disc
    bx = dcx + dr + 34
    _open_curve(d, [(bx, dcy - 54), (bx + 18, dcy), (bx, dcy + 54)], BONE,
                width=THIN, seed=413, wobble=0.8, wavelength=60.0)
    _tag(img, "LYRA", bx + 96, dcy, px=18)

    # G7: the debris ledge the character stands on. Narrow, so it grounds him
    # without becoming the heaviest mass on the card.
    _ledge(img, 872, W, 656, seed=414, fill=ASH)
    d = ImageDraw.Draw(img, 'RGBA')

    return _finish(img, card, planet, paper_band=True, dark_bg=True,
                   figure_id='hook_never_see_it')


# ---------------------------------------------------------------------------
# 2 — albedo_one_percent.  CREAM, accent ink.  PURE DATA, no character.
# ---------------------------------------------------------------------------
def render_albedo_one_percent(card, planet=PLANET):
    """Pure data beat. The incoming light is a wide amber beam that stops dead
    against the matte black disc, and a single hair-thin sliver peels back off
    the upper limb. The sliver is the whole card, so it is drawn at full amber
    and everything else is deliberately quiet.

    G1: the disc is 270 px in radius against the old 176, and sits low. The
    returned-light sliver and the hero number have the whole left half.
    G2: the beam carries seven short photon ticks along its length, so the light
    reads as ARRIVING rather than as a static amber wedge.
    G3: the disc is irradiated, so its left limb is a gradient crescent with a
    halo — and the crescent is thin, because that is all the light this world
    ever gets.

    The hero phrase is '< 1%' in SYMBOLS, not the caption's words, so it is not a
    restatement of the caption. Amber is a SHAPE on a cream card and never a word
    (1.80:1), so the number is slate-black on a paper keyline. C.hero_word
    measures the same call it makes and clamps INCLUDING the 4 px keyline, so it
    can neither run off the edge nor ride up into the title strip."""
    img = _cream_card()
    d = ImageDraw.Draw(img, 'RGBA')

    pcx, pcy, pr = 838, 388, 270
    _draw_taper(d, [(-20, 320), (250, 344), (pcx - pr - 3, 372)],
                120, 94, BEAM, 205, seed=420, wobble=2.0, wavelength=280.0)
    _draw_taper(d, [(-20, 366), (260, 374), (pcx - pr - 5, 376)],
                26, 16, (255, 228, 172), 170, seed=421, wobble=1.0)
    # G2: photon ticks riding the beam — the light is arriving, in pieces.
    for i in range(7):
        tx = 210 + i * 52
        ty = 352 + i * 3
        d.line([(tx, ty - 16), (tx + 10, ty + 16)], fill=(255, 226, 168, 190),
               width=THIN)
    # the return: off the upper-left limb, shallow, and very thin
    _draw_taper(d, [(pcx - 186, 202), (pcx - 330, 154), (470, 130)],
                16, 5, EMBER, 226, seed=422, wobble=1.4, wavelength=190.0)

    # G3: thin irradiated crescent on the beam-facing limb, over a flat black face
    _lit_planet(img, pcx, pcy, pr, light_deg=180, seed=423, terminator=-0.46,
                limb_band=0.24, ambient=0.04, halo_strength=76, halo_spread=2.1)
    d = ImageDraw.Draw(img)

    C.hero_word(d, "< 1%", 300, 452, INK, stroke_rgb=PAPER, stroke_width=4,
                px=104, margin=60, y_max=560)
    d = ImageDraw.Draw(img)
    T.draw_stamp(d, "ALBEDO", (152, 578), INK, ink_rgb=PAPER)
    _open_curve(d, [(150, 566), (300, 566), (438, 566)], INK, width=THIN,
                seed=424, wobble=1.0, wavelength=160.0)

    C._header(img, planet, paper_band=False)
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 3 — darker_than_coal.  VOID, accent bone.
# ---------------------------------------------------------------------------
def render_darker_than_coal(card, planet=PLANET):
    """Three swatches in a row: coal (x-ray bone), asphalt (ash), and TrES-2b —
    a rectangle of the field's own void with a bone keyline, because the whole
    joke is that there is nothing behind it.

    G1: the swatches are 340 x 360 and sit low (y 236..596). The old 272 x 238
    row left the whole lower third of the frame empty.
    G2: the comparison now has a DIRECTION. Three arrows above the row show how
    much light each surface sends BACK — long over coal, medium over asphalt, a
    stub over the void — under a "LIGHT REFLECTED BACK" label. That is the
    albedo comparison as a picture, not three rectangles side by side.
    G4: the third block no longer eats its own label. "TrES-2b" is drawn in bone
    on the near-black block through the same auto-contrast path as every other
    label, and the rhetorical point is carried by a separate amber stamp below
    it rather than by an illegible word.

    Coal and asphalt are labelled inside, each at the contrast its own fill
    needs."""
    img = _void_card(seed=501, stars=104)
    d = ImageDraw.Draw(img)

    top, bot = 236, 596
    blocks = ((260, BONE, "COAL", INK), (640, ASH, "ASPHALT", INK),
              (1020, DEEP, "TrES-2b", BONE))
    for i, (cx, fill, label, inkc) in enumerate(blocks):
        # wobble 1.0 over a 340 px wavelength: enough that no two edges are dead
        # straight, little enough that the corners stay corners. At the 2.4/210
        # this used to run, Catmull-Rom through four near-right angles rounds
        # them off and the swatches read as pillows, not as paint chips.
        K.draw_smooth(d, [(cx - 170, top), (cx + 170, top),
                          (cx + 170, bot), (cx - 170, bot)],
                      fill=fill, outline=INK, width=BIG, seed=510 + i,
                      wobble=1.0, wavelength=340.0)
        # G4: the name is drawn on the fill it names, at the contrast that fill
        # needs. The void block's own colour is its argument, so the word on it
        # is bone, not slate-black.
        _tag_on(d, label, cx, (top + bot) // 2, inkc, px=T.LABEL_PX)

    # the block that ate its label gets named from outside instead, straight
    # down off its own underside so the leader touches the thing it names
    _open_curve(d, [(1020, bot + 8), (1020, 616), (1020, 630)], BONE,
                width=THIN, seed=502, wobble=0.7, wavelength=70.0)
    _tag(img, "NOTHING BEHIND IT", 1020, 648, px=18)

    d = ImageDraw.Draw(img, 'RGBA')
    # G2: the returning-light arrows. Same star, three surfaces, three answers.
    # Length IS the albedo; the third is a stub, which is the point.
    for i, (cx, length) in enumerate(((260, 150), (640, 78), (1020, 34))):
        y = 190
        x0 = cx - length / 2.0
        _arrow(d, [(x0, y), (x0 + length - 22, y)], BEAM, width=MED, head=22,
               seed=520 + i, wobble=0.6)
    d = ImageDraw.Draw(img)
    _tag_on(d, "LIGHT REFLECTED BACK", 640, 140, BONE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 4 — tidally_locked_reveal.  CREAM, accent ember, character.
# ---------------------------------------------------------------------------
def render_tidally_locked_reveal(card, planet=PLANET):
    """The reveal. The black planet is centred and enormous; the red dwarf is a
    small flat disc far off to one side with a thin amber line between them, so
    the card states its fact — one side, one star — before a word is read.

    G1: the planet is 210 px in radius at centre y 386, and the character is
    large (310 px) and grounded on the 619 line at the left, so the mass is in
    the lower two-thirds rather than the upper third.
    G2/G3: the planet is EMISSIVE on ONE SIDE. Its right limb faces the star and
    carries a gradient crescent (lib.emissive), which is the directional cue the
    beat was missing: you can SEE which hemisphere is locked to the star.
    G6: the limb keyline is 6 px.
    G7: the character stands on the ground line, shrugging with both palms up
    and a zigzag mouth — the 'how is this even a thing' beat."""
    img = _cream_card()
    img = _ground(img, GROUND, seed=520, fill=ASH, x0=0, x1=W)

    pcx, pcy, pr = 690, 386, 210
    sx, sy, sr = 1150, 176, 52
    d = ImageDraw.Draw(img, 'RGBA')
    # the line from the star to the planet: the only light that ever lands
    _draw_taper(d, [(sx - sr - 4, sy + 18), (1080, 262), (pcx + pr - 6, 344)],
                16, 6, BEAM, 205, seed=522, wobble=1.6, wavelength=200.0)

    # G3: the star, from the shared _red_dwarf template (soft glow + stipple).
    _red_dwarf(img, sx, sy, sr, seed=521, wash=104)
    # G2/G3: the planet, lit on the side that faces the star (bearing ~ -25 deg
    # from planet to star, i.e. 335), gibbous rather than crescent so the locked
    # hemisphere is unmistakable.
    _lit_planet(img, pcx, pcy, pr, light_deg=335, seed=523, terminator=0.30,
                limb_band=0.34, ambient=0.06, halo_strength=96, halo_spread=2.0)
    d = ImageDraw.Draw(img, 'RGBA')
    # G6: the silhouette keyline, 6 px, on the same dense edge as the fill.
    _open_curve(d, _arc_pts(pcx, pcy, pr, 0, 360, n=64)[:1], INK, width=BIG,
                seed=524, wobble=0.0, wavelength=1.0)
    d = ImageDraw.Draw(img)
    T.draw_stamp(d, "ONE SIDE ONLY", (pcx - 96, pcy - pr - 34), INK, ink_rgb=PAPER)

    C._header(img, planet, paper_band=False)
    _figure(img, 'tidally_locked_reveal')
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 5 — two_faces_forever.  VOID, accent beam.  DIAGRAM, no character.
# ---------------------------------------------------------------------------
def render_two_faces_forever(card, planet=PLANET):
    """The planet bisected. The lit hemisphere is flat ember — a 2000 K surface is
    a dull red whatever the narration calls light — and the night hemisphere is the
    field's own void, so the two halves meet on a bone terminator with no blend at
    all. That hard vertical seam IS the tidally locked planet.

    G1: the disc is 244 px in radius at centre y 400, so the subject fills the
    middle of the frame instead of floating small in the top third. It is now
    the largest mass on the card by a wide margin.

    The accent on this card is the amber forever-loop: a band that leaves the lit
    limb, goes all the way round the planet and spirals back into the same limb,
    with a solid head on the end. One rotation, no exit. 'DAY' and 'NIGHT' are
    drawn on their own halves through the auto-contrast path, each at the
    contrast its own side needs, and each well inside the half it names."""
    img = _void_card(seed=601, stars=96)
    d = ImageDraw.Draw(img, 'RGBA')

    pcx, pcy, pr = 600, 400, 244
    # the whole disc in the field's void first, so the night side has no fill
    dense = K.draw_disc(d, pcx, pcy, pr, fill=DEEP, outline=None, seed=601,
                        wobble=3.2)
    # the lit hemisphere is a SLICE of that same dense polyline, so the two
    # halves share a pixel-identical limb. Generating the half from its own
    # wobbled 8-gon (as this used to) left red spikes at both poles, where the
    # two independent wobbles disagreed at the 90 deg and 270 deg vertices.
    half = _left_half(dense)
    d.polygon(half, fill=EMBER)
    # the terminator: one straight bone rule straight down the seam
    d.line([half[-1], half[0]], fill=BONE + (230,), width=MED)
    # G6: the limb, 6 px, stroked along the same dense edge the two fills used
    d.line(dense + [dense[0]], fill=BONE + (185,), width=BIG, joint='curve')

    # The loop. Held to ONE TURN at pr+70 rather than pr+92: at pr+92 the band
    # was a ring 108 px clear of the limb and read as an orbit, not as an arrow
    # that keeps going. The last third of the path spirals in through 70 -> 18 px
    # so the end visibly returns to the limb it left, which is the entire claim
    # this card makes.
    lr = pr + 70
    loop = (_arc_pts(pcx, pcy, lr, 168, 300, n=30)
            + _arc_pts(pcx, pcy, lr - 2, 300, 430, n=26)
            + _arc_pts(pcx, pcy, lr - 26, 430, 486, n=14)
            + _arc_pts(pcx, pcy, lr - 50, 486, 502, n=8))
    _draw_band(d, loop, 8, BEAM, 226, seed=604, wobble=1.0, wavelength=600.0)
    _arrow(d, loop[-5:], BEAM, width=MED, head=26, seed=605, wobble=0.4)
    _tag(img, "FOREVER", pcx - pr - 14, pcy + pr + 46, px=18)

    d = ImageDraw.Draw(img)
    # G4: DAY on the ember, NIGHT on the void, each auto-contrasted so the word
    # reads on whichever side of the terminator it actually landed on.
    _tag(img, "DAY", pcx - pr // 2, pcy, px=T.LABEL_PX)
    _tag(img, "NIGHT", pcx + pr // 2 + 12, pcy, px=T.LABEL_PX)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 6 — never_warms_never_cools.  CREAM, accent ash, character.
# ---------------------------------------------------------------------------
def render_never_warms_never_cools(card, planet=PLANET):
    """Two thermometers flank the character and they are PINNED. The left column
    is jammed to the ceiling with a stop-bar at the top; the right one has no
    column at all and a stop-bar at the floor. Nothing is in between and nothing
    moves — the instrument is the argument.

    G1: both tubes are now 96 px wide and 410 px tall (the old pair were 68 px
    and 334 px), and the ground is a LEDGE under the character rather than a
    full-width band. That is the v_centroid 0.756 -> in-window fix: the old card
    was bottom-loaded because the flat ground band, not the instruments, was the
    heaviest thing on it.

    G2: the instruments are now INSTRUMENTS, not capsules. Each has a bulb, a
    6 px ink keyline, a 9-tick scale up its outer side, and — the cue that makes
    the argument — a short arrow jammed into its stop-bar with a blocked cross
    through the head: it cannot move up, and it cannot move down.

    Both tubes are ash with ink keylines and their columns are beam amber, so
    on cream every WORD stays slate-black and the amber is a fill, never a letter.
    He is grounded on the ledge, per the t=205-271 addendum."""
    img = _cream_card()
    img = _ledge(img, 470, 810, 656, seed=610, fill=ASH)
    d = ImageDraw.Draw(img)

    top_y, bot_y = 150, 560

    def thermometer(cx, column, blocked_up, seed):
        """A flat glass tube, a bulb, an ink keyline, a mercury column, a tick
        scale, and a stop-bar at whichever end the column is jammed against. The
        blocked arrow is the directional cue: the value is PINNED there and the
        arrowhead is struck through, so it can go neither way."""
        tw, bulb_r = 48, 74
        K.draw_smooth(d, [(cx - tw, top_y), (cx + tw, top_y),
                          (cx + tw, bot_y - bulb_r * 0.4),
                          (cx + bulb_r, bot_y - bulb_r * 0.2),
                          (cx + bulb_r, bot_y + bulb_r * 0.7),
                          (cx - bulb_r, bot_y + bulb_r * 0.7),
                          (cx - bulb_r, bot_y - bulb_r * 0.2),
                          (cx - tw, bot_y - bulb_r * 0.4)],
                      fill=ASH, outline=INK, width=BIG, seed=seed,
                      wobble=1.6, wavelength=180.0)
        col_top = bot_y - (bot_y - top_y) * column
        # the column has to be wide enough to read as MERCURY and not as a
        # hairline. The bulb only fills when the column does: an always-on bulb
        # put amber mercury in the night-side tube that this card's whole
        # argument says is permanently empty.
        if column > 0.05:
            d.rectangle([cx - 34, col_top, cx + 34, bot_y], fill=BEAM)
            d.ellipse([cx - bulb_r + 16, bot_y - bulb_r + 16,
                       cx + bulb_r - 16, bot_y + bulb_r - 16], fill=BEAM)
        bar_y = top_y if blocked_up else bot_y - 18
        d.rectangle([cx - tw - 22, bar_y, cx + tw + 22, bar_y + 18], fill=INK)

        # G2: the tick scale up the outer side — a scale is what makes a column
        # read as a measurement rather than a bar of paint.
        for k in range(9):
            ty = top_y + (bot_y - 40 - top_y) * k / 8.0
            long_tick = (k % 2 == 0)
            d.line([(cx + tw + 26, ty), (cx + tw + (46 if long_tick else 36), ty)],
                   fill=INK, width=FINE_ if not long_tick else THIN)

        # G2: the blocked arrow. It points at the stop-bar and a cross is struck
        # through its head, so the reading is jammed and cannot travel.
        if blocked_up:
            ay0, ay1, head = top_y - 118, top_y - 22, 1
        else:
            ay0, ay1, head = bot_y + 116, bot_y + 20, -1
        ax = cx - tw - 4
        tip = _arrow(ImageDraw.Draw(img, 'RGBA'),
                     [(ax, ay0), (ax, ay1)], EMBER, width=MED, head=24,
                     seed=seed + 7, wobble=0.5)
        d.line([(tip[0] - 20, tip[1] - 20 * head), (tip[0] + 20, tip[1] + 20 * head)],
               fill=INK, width=MED)

    thermometer(268, 1.0, True, 620)     # day side: jammed at max, can never cool
    thermometer(1012, 0.0, False, 640)   # night side: empty, can never warm
    # G5 LABEL COLLISION FIX: these two tags used to sit at y=116, which is
    # exactly where the blocked arrow's stem runs (ay0=top_y-118, tip near
    # top_y-22) and on the same x as the left thermometer -- the red arrow and
    # its struck-through head were drawn straight through "DAY SIDE" and the
    # gate could not tell the overlap from texture. The day-side tag moves up
    # to y=96, clear of the arrowhead, and both are nudged off the arrow column.
    _tag(img, "DAY SIDE", 268, 96, px=T.LABEL_PX)
    _tag(img, "NIGHT SIDE", 1012, 116, px=T.LABEL_PX)

    C._header(img, planet, paper_band=False)
    _figure(img, 'never_warms_never_cools')
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 7 — day_side_furnace.  VOID, accent bone.  PURE DATA, no character.
# ---------------------------------------------------------------------------
def render_day_side_furnace(card, planet=PLANET):
    """Pure data beat, and the contradiction is the drawing. The planet is a full
    matte-black disc with a 124 degree wedge cut into its right side, and the
    interior of that wedge is flat ember with three darker strata. Everything
    still standing is black with a 6 px bone limb and not one highlight anywhere
    on it.

    G1: the disc is 250 px in radius at centre y 400 — the largest single mass on
    the card, in the lower two-thirds.
    G2: the cutaway is a STATIC WEDGE without a cue, which is the G2 defect. The
    beat now shows WHERE THE HEAT COMES FROM: a tapering beam runs in from
    off-frame right, the direction the star is in, and terminates in an arrowhead
    inside the hot interior. The energy has a source and a direction.
    G3: the exposed interior is emissive (2000 K), so it gets a soft warm halo
    bleeding out past the planet's limb through the cut. That is the light the
    surface refuses to reflect, escaping where the rock is missing.

    The annotations are the argument, and there are only two: '2000+ K' out on
    the empty field with a leader into the hot interior, and 'NOT VISIBLE' out on
    the other side pointing at the cold black face. The gap between them is the
    planet."""
    img = _void_card(seed=701, stars=90)
    d = ImageDraw.Draw(img, 'RGBA')

    pcx, pcy, pr = 600, 400, 250
    # G2: the incoming starlight, from the off-frame star on the right, into the
    # exposed furnace. Drawn under the planet so the limb cuts its end cleanly.
    _draw_taper(d, [(1300, 250), (980, 300), (pcx + pr - 40, 360)],
                34, 20, BEAM, 200, seed=705, wobble=1.6, wavelength=220.0)
    _arrow(d, [(pcx + pr - 60, 356), (pcx + 120, 380)], BEAM, width=MED, head=26,
           seed=706, wobble=0.5)
    d = ImageDraw.Draw(img, 'RGBA')

    # G3: the exposed interior is emissive, so it throws a soft halo that escapes
    # past the limb through the cut. Drawn under the disc, so only the part that
    # spills past the silhouette is visible — light coming from inside the rock.
    E.soft_glow(img, pcx + pr * 0.72, pcy, pr * 0.5, EMBER_HOT, strength=118,
                mode="add", power=2.0)
    d = ImageDraw.Draw(img, 'RGBA')

    # The whole planet as matte black FIRST, then the hot interior dropped into a
    # bite in its right side. Drawing the wedge first and the remainder second is
    # what turned this into a Pac-Man: the remainder was a 232 deg ARC, not a disc,
    # so its two straight edges converged on the centre and overshot as spikes.
    dense = K.draw_disc(d, pcx, pcy, pr, fill=DEEP, outline=None, seed=701,
                        wobble=3.0)
    # the wedge, pulled 10 px inside the limb: the gap left over IS the crust, so
    # it does not need to be drawn and cannot be drawn wrong
    K.draw_smooth(d, _sector(pcx, pcy, pr - 10, -62, 62, n=40),
                  fill=EMBER, outline=None, seed=702, wobble=1.4, wavelength=pr * 1.6)
    # three darker SHELLS inside it. As bare arcs they closed into circular
    # segments whose chords are vertical lines, and three of those side by side
    # read as bars standing in the furnace; as annular sectors they are layers.
    core = pr - 10
    for i, (f0, f1) in enumerate(((0.30, 0.46), (0.58, 0.72), (0.84, 0.96))):
        K.draw_smooth(d, _annular_sector(pcx, pcy, core * f0, core * f1, -62, 62),
                      fill=EMBER_SHADE + (255,), outline=None, seed=703 + i,
                      wobble=1.4, wavelength=pr)
    # the limb LAST, so nothing the cut drew can cross it. G6: 6 px on a 500 px
    # disc.
    d.line(dense + [dense[0]], fill=BONE + (200,), width=BIG, joint='curve')

    d = ImageDraw.Draw(img)
    # both labels live OUTSIDE the disc (which spans x 350..850) and point in at
    # the thing each one names. Stamping them on the body was what put NOT VISIBLE
    # straddling the limb, half on black and half on the starfield.
    _open_curve(d, [(966, 420), (866, 400)], EMBER, width=THIN, seed=710,
                wobble=0.7, wavelength=60.0)
    _open_curve(d, [(300, 268), (392, 306)], BONE, width=THIN, seed=711,
                wobble=0.7, wavelength=90.0)
    _tag(img, "2000+ K", 1062, 420, px=T.LABEL_PX)
    _tag(img, "NOT VISIBLE", 232, 244, px=T.LABEL_PX)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 8 — dull_red_glow.  CREAM, accent ember.  PORTRAIT, no character.
# ---------------------------------------------------------------------------
def render_dull_red_glow(card, planet=PLANET):
    """The close portrait, in the paint register: one large FLAT ember disc with
    a 6 px ink keyline and two darker ember shadow shapes laid inside it. No
    gloss, no shine, no highlight — the brief for this beat is a glow that does
    not look like a glow, and the moment this disc gets a specular it stops
    being the darkest planet in the catalogue.

    G1: the disc is 288 px in radius against the old 244, so the subject owns
    the frame. It is now roughly a third of the whole card.

    G2: a portrait with a label and no motion cue reads as a prop. The disc now
    throws short heat RAYS off its upper-left limb, which is the direction the
    heat leaves from and the only cue this beat needs — this is what a 2000 K
    surface looks like when you are close enough to see it.

    G3: the body is described as glowing, so it gets a soft warm halo. It is
    drawn OUTSIDE the disc only (the face stays flat), which is the one legal
    gradient on a register-P card and the only way the beat's own claim — it
    glows, BARELY — can be true of a flat-painted disc.

    The temperature is stamped ACROSS the disc, which is where the reference puts
    its labels: on the thing they name — auto-contrasted, because slate-black on
    flat ember is 3.7:1 and does not read."""
    img = _cream_card()
    # G3: the halo, UNDER the disc so it only reads where it escapes the limb.
    E.soft_glow(img, 640, 372, 288 * 1.9, EMBER_HOT, strength=104, mode="wash",
                power=2.3)
    d = ImageDraw.Draw(img)
    pcx, pcy, pr = 640, 372, 288

    K.draw_disc(d, pcx, pcy, pr, fill=EMBER, outline=INK, width=BIG,
                seed=801, wobble=4.0)
    d = ImageDraw.Draw(img, 'RGBA')
    # The shadow is a CRESCENT hugging the lower-left limb, not a free-floating
    # blob: at 0.62r across the middle of the disc it read as a separate brown
    # object sitting on the planet. A terminator that follows the limb is a
    # shadow; a shape that does not is a second planet.
    _draw_taper(d, _arc_pts(pcx, pcy, pr * 0.90, 128, 232, n=26),
                38, 30, EMBER_SHADE, 235, seed=802, wobble=1.6, wavelength=220.0)
    # K.stipple takes a RECT. At pr*0.9 its corners sit at 1.27r — off the limb,
    # as black measles on the paper. The inscribed square is pr*0.62; at density
    # 0.004 that box was also throwing ~770 dots at a 488 px disc, so the grain
    # is thinned to 0.0012 and the dots pinned to a single pixel.
    K.stipple(d, pcx - pr * 0.62, pcy - pr * 0.62, pcx + pr * 0.62, pcy + pr * 0.62,
              (120, 38, 24), seed=803, density=0.0012, r=1, spread=0)

    # G2: the heat rays. Short, tapered, and evenly spread across the upper-left
    # quadrant — the direction the warmth leaves the surface. They are a SHAPE
    # in ember, never a word, and they never touch the disc keyline.
    d = ImageDraw.Draw(img, 'RGBA')
    for i in range(9):
        a = math.radians(196 + i * 17)
        ca, sa = math.cos(a), math.sin(a)
        x0 = pcx + (pr + 16) * ca
        y0 = pcy + (pr + 16) * sa
        _draw_taper(d, [(x0, y0), (x0 + 34 * ca, y0 + 34 * sa)],
                    16, 4, EMBER, 168, seed=810 + i, wobble=0.6, wavelength=40.0)

    d = ImageDraw.Draw(img)
    _tag(img, "DULL RED", pcx, pcy - pr + 74, px=18)
    _tag(img, "2000 K", pcx, pcy - 16, px=T.LABEL_PX)

    C._header(img, planet, paper_band=False)
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 9 — hot_but_too_dark.  VOID, accent beam, character.
# ---------------------------------------------------------------------------
def render_hot_but_too_dark(card, planet=PLANET):
    """The contradiction, and it is one drawing: the left limb of the planet is
    flat ember at 2000 K, the right limb is the void, and a single heavy amber
    hand-drawn rule is underlined beneath the whole body — one line under two
    opposite facts. '2000 K' and 'NOTHING' are stamped on their own halves,
    auto-contrasted, because one contrast will will not serve both.

    G1: the disc is 238 px in radius at centre y 386, and the character is large
    (320 px) on a debris LEDGE in the lower left. That is the v_centroid 0.282
    fix — the mass is now in the lower two-thirds.

    G2/G3: the lit hemisphere is EMISSIVE, so it goes through lib.emissive with
    a real gradient limb and halo rather than a flat ember polygon with a bone
    seam. The halo is the only thing that says the light exists at all, which is
    the beat's whole argument: hot, and you still cannot see it.

    Character: cream, lower left, wide oval awed mouth, pointing up at the glow
    with the arm aimed along the real diagonal."""
    img = _void_card(seed=901, stars=112)
    d = ImageDraw.Draw(img, 'RGBA')

    pcx, pcy, pr = 700, 386, 238
    # G3: the lit hemisphere. core = the field's void, limb = ember, light_deg
    # 180 = the star is off-frame left. terminator 0.0 = exactly half lit, which
    # is the hard seam this card is about.
    _lit_planet(img, pcx, pcy, pr, light_deg=180, seed=901, terminator=0.0,
                limb_band=0.42, ambient=0.10, halo_strength=126, halo_spread=2.2,
                core=DEEP)
    d = ImageDraw.Draw(img, 'RGBA')
    # the terminator, and the 6 px limb on the same dense edge
    dense = _disc_dense(pcx, pcy, pr, seed=901, wobble=3.2)
    d.line([(pcx, pcy - pr), (pcx, pcy + pr)], fill=BONE + (230,), width=MED)
    d.line(dense + [dense[0]], fill=BONE + (185,), width=BIG, joint='curve')

    # the underline: one hand-drawn amber rule under both halves, close enough
    # that it reads as underlining THIS disc rather than floating in the field
    _draw_band(d, [(pcx - 268, 620), (pcx - 90, 632), (pcx + 90, 628),
                   (pcx + 266, 618)], 12, BEAM, 232, seed=904, wobble=2.2,
               wavelength=240.0)

    # NOTHING cannot sit on a 476 px disc — at LABEL_PX it is 130 px wide and was
    # running off the limb — so it goes outside on the empty field with a leader
    # back to the dead half it names. 2000 K sits on the ember and is
    # auto-contrasted, which is the only honest way to put a word on a body that
    # is half ember and half void.
    _open_curve(d, [(972, 208), (900, 252)], BONE, width=THIN, seed=906,
                wobble=0.7, wavelength=70.0)
    _tag(img, "2000 K", pcx - 118, pcy - 92, px=T.LABEL_PX)
    _tag(img, "NOTHING", 1090, 190, px=T.LABEL_PX)

    # G7: the debris ledge under the character, lower left. Narrow so it grounds
    # him without dominating; ink-topped so his cream limbs read against it.
    _ledge(img, 0, 430, 648, seed=908, fill=ASH)

    C._header(img, planet, paper_band=True)
    _figure(img, 'hot_but_too_dark')
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# 10 — watch_the_star.  CREAM, accent ember, character.
# ---------------------------------------------------------------------------
def render_watch_the_star(card, planet=PLANET):
    """The pivot. The framing is the point, so the composition is deliberately
    tight: a swollen star fills the upper-right corner and runs off three edges,
    and the black planet is shoved down into the lower-left corner and sits ON the
    ground line. The amber line between them is short, because there is no room
    for it to be long.

    The star is emissive, so the second and last gradient in this segment is legal
    here, with a real halo and no outline. The planet is a flat black disc with a
    6 px ink keyline and one flat ember crescent hugging the limb that faces the
    star — that crescent is the only light that ever lands on this planet, and it
    is a sliver.

    G7: the character is grounded on the 619 line, small, hands up, worried — a
    scale figure for a star that is too close. This beat was already carrying
    the frame's ink (0.492) and passing both gates; the changes here are the
    character's grounding and the crescent, not a re-composition."""
    img = _cream_card()
    img = _ground(img, 619, seed=1001, fill=ASH, x0=0, x1=W)

    sx, sy, sr = 1074, 178, 132
    _red_dwarf(img, sx, sy, sr, seed=1002, wash=84)
    d = ImageDraw.Draw(img, 'RGBA')
    _draw_taper(d, [(sx - sr - 6, sy + 78), (700, 420), (376, 508)],
                5, 3, BEAM, 214, seed=1003, wobble=1.8, wavelength=230.0)

    # the planet: flat matte black, sitting ON the ground line, with the only
    # light it will ever get as a sliver on the star-facing limb
    d = ImageDraw.Draw(img, 'RGBA')
    pcx, pcy, pr = 268, 508, 96
    K.draw_disc(d, pcx, pcy, pr, fill=INK, outline=None, seed=1004, wobble=2.2)
    # the flat ember crescent on the star-facing limb, thinning at both ends.
    # 26 px at the belly of a 104 px disc was a red rim standing proud of the
    # limb and overshooting at the top-right; at 14 it is a sliver, which is all
    # the light this planet ever gets.
    _draw_taper(d, _arc_pts(pcx, pcy, pr - 5, -82, 74, n=30),
                14, 3, EMBER, 224, seed=1005, wobble=1.2, wavelength=170.0)

    C._header(img, planet, paper_band=False)
    _figure(img, 'watch_the_star')
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 11 — star_running_out_of_fuel.  VOID, accent bone.  PURE DATA, no character.
# ---------------------------------------------------------------------------
def render_star_running_out_of_fuel(card, planet=PLANET):
    """Pure data beat. A cutaway of the star with three concentric bands of fuel,
    each one DARKER than the core and each one THINNER than the last: 34 px
    outside, 22 px in the middle, 12 px at the core. The band widths are the data.
    No label is doing work the drawing could do.

    G2: the three rings were a static cutaway with no cue. The beat now has two
    short curved arrows on the upper-left running INWARD, from the outer band to
    the core — fuel being burned from the outside in, which is the direction the
    star is losing it. The rings' widths are the data; the arrows are the claim.

    'NOW' and 'THEN' sit out on short bone leaders, each against the ring it is
    about; 18 px is inside the canon's 12-18 stamp band. No character."""
    img = _void_card(seed=1101, stars=86)
    pcx, pcy = 596, 372
    C._radial_core(img, pcx, pcy, 230, [(255, 214, 150), EMBER, (96, 30, 20)],
                   glow=0.55)

    d = ImageDraw.Draw(img, 'RGBA')
    for i, (rr, fw) in enumerate(((222, 34), (164, 22), (122, 12))):
        d.ellipse([pcx - rr, pcy - rr, pcx + rr, pcy + rr],
                  outline=INK + (234,), width=fw)
        edge = BONE + (206 - i * 48,)
        d.ellipse([pcx - rr, pcy - rr, pcx + rr, pcy + rr], outline=edge,
                  width=FINE_)
        d.ellipse([pcx - rr + fw, pcy - rr + fw, pcx + rr - fw, pcy + rr - fw],
                  outline=edge, width=FINE_)

    # G2: the inward arrows — the fuel is being burned from the outside in. Both
    # sit on the upper-left, at different radii, so neither crosses the other.
    d2 = ImageDraw.Draw(img, 'RGBA')
    for i, (r0, r1) in enumerate(((268, 206), (196, 140))):
        pts = _arc_pts(pcx, pcy, (r0 + r1) / 2.0, 196, 232, n=12)
        _arrow(d2, pts, BONE + (240,), width=MED, head=24, seed=1105 + i, wobble=0.5)

    d = ImageDraw.Draw(img)
    _open_curve(d, [(352, 224), (398, 240)], BONE, width=THIN, seed=1102,
                wobble=0.8, wavelength=70.0)
    _open_curve(d, [(424, 508), (488, 462)], BONE, width=THIN, seed=1103,
                wobble=0.8, wavelength=70.0)
    _tag(img, "NOW", 296, 208, px=18)
    _tag(img, "THEN", 380, 528, px=18)
    T.draw_stamp(d, "THE FUEL LAYER", (884, 366), BONE, ink_rgb=INK)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 12 — swelling_and_closer.  CREAM, accent ember, character.
# ---------------------------------------------------------------------------
def render_swelling_and_closer(card, planet=PLANET):
    """The star swells, and the drawing says DIRECTIONALLY that it is swelling.

    G2 (the named failure): three unfilled ember circles with two small arrows
    read as a dartboard, not as an expanding star. That is now
    lib.emissive.expanding_rings, which fixes it four ways at once — a filled,
    glowing SOURCE at the centre; an alpha/width ramp so the inner rings are
    solid and the outer ones thin and faint; arrowheads that sit in the outer
    annulus with their TIPS past the outermost ring; and three arrows on SPREAD
    bearings so no two share a diagonal and the inner shaft cannot cross the
    outer head.

    G1: this was the most bottom-loaded card in the segment (v_centroid 0.806)
    because a full-width flat ground band was carrying 64% of its ink. The band
    is now a ledge under the character, and the freed mass went into the star
    itself — a real emissive core at 170 px radius plus its halo, which is now
    the heaviest thing on the card.

    G7: the character is grounded on the ledge, cowering, and carries a PAPER
    keyline so his black limbs stay readable against the star's warm wash — the
    camouflage G7 exists to prevent, and the one place on this segment where the
    figure and a coloured shape would otherwise meet.

    The planet is shoved hard into the left frame edge — half of it is off screen
    — which is the whole claim: the star's edge is crossing the space where the
    planet was."""
    img = _cream_card()
    img = _ledge(img, 210, 640, 640, seed=1201, fill=ASH)

    scx, scy = 872, 322
    # G1/G2: the star's edge, crossing outward. Radii 232/300/372, innermost
    # first, with a filled emissive source at the centre.
    E.expanding_rings(
        img, scx, scy, [232, 300, 372], EMBER, width=8, seed=1205, arrows=3,
        bearings=(146, 254, 34), phase=0.0, head=32, arrow_width=5,
        alpha_ramp=(1.0, 0.66, 0.34), width_ramp=1.0,
        core_color=EMBER, core_r=150, core_stipple=48, arrow_color=EMBER)

    d = ImageDraw.Draw(img, 'RGBA')
    # the planet, shoved off the left edge. wobble 3.4 over a 210 px wavelength
    # on a shape this small turned it into a potato; 2.0 keeps it a sphere. It is
    # now larger (the old one was a 170 px blob) because the beat needs the two
    # bodies to be comparable in weight.
    d = ImageDraw.Draw(img)
    K.draw_smooth(d, [(0, 372), (96, 348), (184, 396), (218, 494),
                      (176, 588), (74, 620), (0, 598)],
                  fill=INK, outline=INK, width=BIG, seed=1220, wobble=2.0,
                  wavelength=300.0)

    C._header(img, planet, paper_band=False)
    _figure(img, 'swelling_and_closer')
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 13 — atmosphere_as_tail.  VOID, accent beam.  DIAGRAM, no character.
# ---------------------------------------------------------------------------
def render_atmosphere_as_tail(card, planet=PLANET):
    """Five flat sheets peel off the planet's limb spread across 120 degrees of it,
    each starting further round the limb than the last, and all five converge on
    one corridor off the right edge — so five bands arrive as ONE long tapering
    ember tail that dies in the starfield. Width and alpha fall together down the
    tail, so it thins out instead of stopping on a blunt edge.

    G1: the planet is 178 px in radius (the old 112) and the tail corridor is
    pushed DOWN into the lower two-thirds, which is the v_centroid 0.303 fix. The
    tail used to run dead level across the middle of the frame while the planet
    sat above it; now the whole mass sits low.

    G3: the tail is hot gas leaving a world, so it carries a soft warm glow along
    its root — the sheets are lit, and that is the only light on this card but
    one. The planet itself stays matte black and gains nothing: it is losing its
    air, not catching light. No character — the tail is the whole card."""
    img = _void_card(seed=1301, stars=124)
    d = ImageDraw.Draw(img, 'RGBA')

    pcx, pcy, pr = 300, 404, 178
    # G3: the escaping gas is emissive, so it throws a soft glow. Drawn BEFORE the
    # sheets, so the sheets sit on top of their own halo.
    E.soft_glow(img, pcx + 60, 470, 300, EMBER, strength=96, mode="add", power=2.2)
    d = ImageDraw.Draw(img, 'RGBA')

    # Five sheets leave the limb spread across 120 degrees of it — -66 to +54 —
    # and then CONVERGE on a single corridor off the right edge. The tail the
    # beat asks for is one tapering mass, and the only way five bands become one
    # mass is if they are heading for the same place. Letting them run parallel
    # (as this used to) is what made them read as a bundle of tubes, or a claw.
    for k in range(5):
        a = math.radians(-66 + k * 30)
        x0 = pcx + pr * math.cos(a) * 0.98
        y0 = pcy + pr * math.sin(a) * 0.98
        ey = 470 + k * 14
        path = [(x0, y0),
                (x0 + (1300 - x0) * 0.30, y0 + (ey - y0) * 0.46),
                (x0 + (1300 - x0) * 0.60, y0 + (ey - y0) * 0.76),
                (x0 + (1300 - x0) * 0.84, y0 + (ey - y0) * 0.93),
                (1300, ey)]
        _draw_taper(d, path, 22 + k * 6, 6, (EMBER if k >= 2 else BEAM),
                    212 - k * 24, seed=1310 + k, wobble=1.4, wavelength=420.0)

    d = ImageDraw.Draw(img)
    _black_planet(d, pcx, pcy, pr, seed=1301, rim=BONE, rim_alpha=120, rim_w=BIG)

    d = ImageDraw.Draw(img)
    # the label points at the topmost sheet's actual root on the limb
    _open_curve(d, [(420, 210), (368, 284)], BONE, width=THIN, seed=1320,
                wobble=0.8, wavelength=70.0)
    _tag(img, "AIR", 424, 196, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# 14 — unmade_by_its_own_sun.  CREAM, accent ash, character.  THE FATE BEAT.
# ---------------------------------------------------------------------------
def render_unmade_by_its_own_sun(card, planet=PLANET):
    """The fate beat, and it is now mostly NOTHING LEFT — but it fills the frame,
    because that is the only way the emptiness reads as a loss.

    G1: this was the emptiest and most bottom-loaded card in the segment
    (ink 0.186, v_centroid 0.811): a tiny 82 px planet, a thread-thin filament,
    and a full-width ground band that was carrying most of the ink. The planet is
    now 215 px, the ground is a LEDGE under the character rather than a
    full-width band, and the right half of the frame — which used to be bare
    paper — now carries what is actually left of the atmosphere: a drift of
    burnt chips and torn sheets, small and scattered, at mid-height. The picture
    says "emptied" instead of "unfinished".

    G7: the character is the largest he is anywhere in the segment (340 px),
    grounded on the ledge, shrugging with both palms up and a zigzag mouth, and
    he is the subject of the lower right — not a small figure pasted into a void.

    G3: the planet is NOT emissive here. Its star is going, not shining on it, so
    it keeps a flat matte black face and gains a dead grey rim instead of a
    glowing limb. The one warm mark left is the final ember filament, already off
    the frame edge.

    No hero word, no annotation, no second subject."""
    img = _cream_card()
    # G1: the ground is a LEDGE, not a full-width band. It grounds the character
    # without becoming the heaviest mass on the card (the old v_centroid 0.811).
    img = _ledge(img, 640, W, 656, seed=1401, fill=ASH)

    d = ImageDraw.Draw(img, 'RGBA')

    # the last of the tail, already off the frame. 18 px at 40% rather than 16 px
    # at 38%: it is drifting, not being delivered, and it has to sit behind the
    # character without competing with him for the frame.
    _draw_taper(d, [(300, 350), (452, 336), (760, 312), (1060, 292), (1248, 278)],
                18, 4, EMBER, 158, seed=1410, wobble=2.0, wavelength=320.0)
    d = ImageDraw.Draw(img)

    # G1: the planet is 215 px, a real subject, dead flat black. Its star is
    # going, so there is no glowing limb on it — that absence IS the beat.
    K.draw_disc(d, 320, 400, 215, fill=INK, outline=INK, width=BIG, seed=1411,
                wobble=3.4)
    d = ImageDraw.Draw(img, 'RGBA')
    # a dead grey rim, so the disc still separates from the paper it sits on
    _open_curve(d, _arc_pts(320, 400, 215, 0, 360, n=64), ASH, width=THIN,
                seed=1412, wobble=1.0, wavelength=200.0)

    # G1: what is LEFT. A drift of burnt chips and torn atmosphere sheets across
    # the emptied right half, small and scattered at mid-height so the mass sits
    # in the lower two-thirds without filling it. This is the beat's emptiness,
    # drawn as debris rather than as blank paper.
    d = ImageDraw.Draw(img, 'RGBA')
    chips = ((836, 232, 26, 15, 22), (952, 196, 20, 12, 18), (1046, 258, 30, 17, 24),
             (900, 372, 22, 13, 20), (1084, 402, 26, 15, 22), (836, 508, 20, 12, 18),
             (986, 540, 28, 16, 23), (1148, 322, 18, 11, 16), (742, 168, 17, 10, 15),
             (1188, 500, 22, 13, 19), (700, 560, 15, 9, 14), (1120, 596, 19, 11, 17))
    for i, (x, y, rw, rh, rot) in enumerate(chips):
        K.draw_smooth(d, [(x - rw, y - rh), (x + rw, y - rh),
                          (x + rw, y + rh), (x - rw, y + rh)],
                      fill=EMBER_SHADE + (170,), outline=EMBER + (210,),
                      width=FINE_, seed=1420 + i, wobble=1.8, wavelength=44.0)

    d = ImageDraw.Draw(img)
    _tag(img, "NO LIGHT LEFT", 936, 616, px=18)

    C._header(img, planet, paper_band=False)
    _figure(img, 'unmade_by_its_own_sun')
    C._caption(img, card.get('caption') or '', 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
RENDERERS = {
    'hook_never_see_it': render_hook_never_see_it,
    'albedo_one_percent': render_albedo_one_percent,
    'darker_than_coal': render_darker_than_coal,
    'tidally_locked_reveal': render_tidally_locked_reveal,
    'two_faces_forever': render_two_faces_forever,
    'never_warms_never_cools': render_never_warms_never_cools,
    'day_side_furnace': render_day_side_furnace,
    'dull_red_glow': render_dull_red_glow,
    'hot_but_too_dark': render_hot_but_too_dark,
    'watch_the_star': render_watch_the_star,
    'star_running_out_of_fuel': render_star_running_out_of_fuel,
    'swelling_and_closer': render_swelling_and_closer,
    'atmosphere_as_tail': render_atmosphere_as_tail,
    'unmade_by_its_own_sun': render_unmade_by_its_own_sun,
}


def register(mapping=None):
    """Merge this segment's renderers into the shared dispatch table. The frame
    generator reads the module attribute RENDERERS directly; this is the
    convenience wrapper, harmless to call twice."""
    C.register(RENDERERS if mapping is None else mapping)
    return RENDERERS


# ---------------------------------------------------------------------------
# Self-test. Builds a minimal card dict for every beat in script.json and bakes
# one still per beat into ./cardsheet/beat_<NN>.png.
#
# The card dicts carry a PLACEHOLDER caption only. The character is NOT supplied
# here: _FIGURE inside the module is the single source of truth for the cast, so
# what the self-test bakes and what the frame generator renders are the same
# drawing (G7 — the old table put the character in card['stickman'], which
# _frames.py sets to None, so the figure existed only in this test).
#
#   cd C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments && python tres2b/_cards.py
# ---------------------------------------------------------------------------
_SCRIPT = "script.json"

# beat id, register, self-test caption.
# Captions here are placeholders so the stills are readable; the real schedule
# supplies the aligned narration clause (and in production supplies ''). None of
# them is a narration line, and none of them restates the one hero word on the
# segment ('< 1%').
_SELFTEST = [
    ('hook_never_see_it', 'void', 'THE DARKEST PLANET EVER MEASURED'),
    ('albedo_one_percent', 'cream', 'WHAT COMES BACK IS ALMOST NOTHING'),
    ('darker_than_coal', 'void', 'COAL, ASPHALT, AND SOMETHING BEYOND BOTH'),
    ('tidally_locked_reveal', 'cream', 'AND THEN THE LOCK'),
    ('two_faces_forever', 'void', 'THE SAME HEMISPHERE, EVERY YEAR'),
    ('never_warms_never_cools', 'cream', 'PINNED AT BOTH ENDS'),
    ('day_side_furnace', 'void', 'A FURNACE WITH NO VISIBLE SURFACE'),
    ('dull_red_glow', 'cream', 'IT DOES GLOW, BARELY'),
    ('hot_but_too_dark', 'void', 'BURNING, AND STILL INVISIBLE'),
    ('watch_the_star', 'cream', 'THE STAR IS NOT WHERE IT WAS'),
    ('star_running_out_of_fuel', 'void', 'THREE BANDS, THREE AMOUNTS LEFT'),
    ('swelling_and_closer', 'cream', 'CLOSER WITH EVERY TURN'),
    ('atmosphere_as_tail', 'void', 'IT IS LOSING ITS AIR'),
    ('unmade_by_its_own_sun', 'cream', 'NOTHING IS ARRIVING ANY MORE'),
]


def _selftest():
    import json

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, 'cardsheet')
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(here, _SCRIPT), 'r', encoding='utf-8') as fh:
        script = json.load(fh)
    beat_ids = [b['id'] for b in script['beats']]

    missing = [b for b in beat_ids if b not in RENDERERS]
    extra = [b for b in RENDERERS if b not in beat_ids]
    if missing or extra:
        raise SystemExit('RENDERERS does not match script.json: missing=%s extra=%s'
                         % (missing, extra))

    chars = 0
    for n, (bid, register, caption) in enumerate(_SELFTEST, start=1):
        card = {
            'id': bid,
            'caption': caption,
            'beat': 'B%d' % n,
            'card_value': register,
            'stickman': None,      # the cast lives in _FIGURE, not here
        }
        img = RENDERERS[bid](card, PLANET)
        assert img.size == (W, H), (bid, img.size)
        assert img.mode == 'RGB', (bid, img.mode)
        path = os.path.join(out_dir, 'beat_%02d.png' % n)
        img.save(path)
        has_fig = bid in _FIGURE
        chars += 1 if has_fig else 0
        print('beat %02d  %-24s %-5s  %-4s  %s'
              % (n, bid, register, 'char' if has_fig else 'data', path))
    print('ok: %d beats rendered, %d with the character, %d total renderers'
          % (len(_SELFTEST), chars, len(RENDERERS)))


if __name__ == '__main__':
    _selftest()
