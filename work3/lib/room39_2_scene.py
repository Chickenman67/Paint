"""room39_2_scene -- the PERSISTENT-STAGE rebuild of chapter 9 (Object 739).

WHY THIS FILE EXISTS. room39_scene.py (v1) was built on "one card per beat, each
card paints its own whole frame": 37 sentences, 37 `card(i, j, draw)` windows,
each one filling background-to-subject, which makes it structurally impossible
for one card's art to survive into the next. Every ~2.4s the film cut to a
brand-new full-frame image. room39 v1's own docstring says the chapter is
"still-dominant, one hard cut per sentence (37 cuts in 89s)" and that "no
element carries a motion track" -- 100% still and 100% of the frame repainted
every other sentence. The viewer complaint this rebuild exists to answer is
"every sentence has a cut with a completely new image... there are no animations
or changes to the visual."

THE MODEL HERE. Seven PERSISTENT STAGES on the narration's own acts, exactly as
recorded in work3/plans/STAGE_PLANS.md:

    A  b01-b06  (15.2s)  under the Kremlin; Object 739; Stalin's own refuge
    B  b07-b13  (17.5s)  sinking ground; hardened steel; the doors
    C  b14-b16  ( 6.5s)  he never went in; the lead-lined corridors
    D  b17-b21  (12.2s)  the control room and the one console
    E  b22-b26  (12.7s)  never filmed; an ordinary fence on an ordinary street
    F  b27-b29  ( 4.0s)  the steel doors; rumour of a code
    G  b30-b37  (18.3s)  the system outlives its builder; the red light; finale

The frame repaints SEVEN times in 89s instead of thirty-seven, and inside a
stage the art ACCUMULATES: the cross-section is drawn once, then the door lands
in it, then the desk, then the man. v1 rebuilt the whole frame for each of
those; here each is one arriving layer on a place the viewer already knows.

TWO RULES THAT TOOK TWO ROUNDS TO LEARN IN THE PILOT (pinegap2_scene.py) --
both measured, both kept here so they are not relearned the hard way.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Accruing everything is also wrong. The
   pilot's first version let every layer live to stage end and got pile-ups:
   three text elements 30px apart rendering as one unreadable line, the globe
   underneath the five-eye row. Here: the ground, the walls, the door leaf, the
   chamber, the trees, the fence ACCRUE; every element carrying text, and every
   pair of elements sharing a region of the frame, REPLACE via SC.layer with an
   explicit j. Each in-art label below says in a comment whether it is holding
   the stage or handing off to the next one.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces motion at a rate the
   reference does not have (measured 22.5% against the reference's 7%) and every
   moving frame trips the picture-change counter -- 82 changes, one per 0.85s,
   which is WORSE than the 30 it was meant to fix. The reference is 83% still.
   So: TWELVE arrivals move in this chapter, each 0.45-0.55s, each on a small
   subject -- a door leaf coming down, a drafting board dropping, a truck
   arriving, a weld bead running, a switch throwing, a lamp lighting. Nothing
   large and continuous drifts. Popping in IS the reveal.

CAPTIONS. Fifteen of 37 beats (41%), never two in a row, and every one of them
earns its place: the hook, the code name, the 1950s, the refuge, the door, the
one-console reveal, the ordinary street, the code that was never published, the
red light, the finale. The other 22 beats let the art speak -- and where the art
already PRINTS the words ("one system", "still listening", "left blank",
"open to visitors", "HUNDREDS OF TONNES") the caption was dropped rather than
printed twice. That drops v1's 100% caption density to 41%, which is the
target in the brief.

CHARACTER. Three stages carry the presenter, and two of them change his
expression mid-stage via SC.expr_swap (stage A at b06, stage D at b20), because
the expression is baked into the tile at build time and so needs two elements at
one position rather than a mutated one. Stage A's man is the presenter standing
in the cutaway, which also pays off stage C's "Stalin reportedly never went
inside" -- the figure who ordered the place is shown standing in it, and the
narration then says he never went in.

ART AND PALETTE ARE v1's, REUSED NOT COPIED. Every primitive (_sky, _dark_bg,
_strata, _blast_door, _lock_wheel, _rivet_row, _sensor, _fence, _tree, _car,
_console, _switch_bank, _keypad, _figure) and every colour comes from
room39_scene. Nothing here redraws art or invents a palette; this file only
decides WHEN each piece is on screen.

Run:  python lib/room39_2_scene.py --preview
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import engine3 as E3
import scene_common as SC
import v2paint as PA
import v2subjects as S
import v2draw as D
import v2type as T

import room39_scene as R39          # art primitives + palette, reused not copied

# The v1 module's identity, imported rather than restated.
SEG = R39.SEG
TITLE = R39.TITLE
BEATS = R39.BEATS
TITLE_BACKDROP = R39.TITLE_BACKDROP

# palette, reused from v1
INK = R39.INK
CONCRETE = R39.CONCRETE
CONCRETE_L = R39.CONCRETE_L
CONCRETE_D = R39.CONCRETE_D
STEEL = R39.STEEL
STEEL_D = R39.STEEL_D
LEAD = R39.LEAD
LEAD_L = R39.LEAD_L
CLAY = R39.CLAY
CLAY_D = R39.CLAY_D
WATER = R39.WATER
PARK = R39.PARK
PARK_D = R39.PARK_D
RED = R39.RED
DARK = R39.DARK
DARKER = R39.DARKER
LAMP = R39.LAMP
SNOW = R39.SNOW
PAPERW = R39.PAPERW
BRICK = R39.BRICK

W, H = R39.W, R39.H
HZ = R39.HZ

# art primitives, reused from v1
_sky = R39._sky
_night = R39._night
_dark_bg = R39._dark_bg
_soil_bg = R39._soil_bg
_strata = R39._strata
_blast_door = R39._blast_door
_lock_wheel = R39._lock_wheel
_rivet_row = R39._rivet_row
_sensor = R39._sensor
_fence = R39._fence
_tree = R39._tree
_car = R39._car
_console = R39._console
_switch_bank = R39._switch_bank
_keypad = R39._keypad
_figure = R39._figure

# ---------------------------------------------------------------------------
# STRUCTURE PRIMITIVES  (the flat-vector fix)
#
# WHY THESE EXIST HERE. The label-blind critic scored this film 5/18 and across
# five of six clean losses named ONE gap: our frames read as flat vector and
# under-filled. A per-beat pigment measurement put 34 of this chapter's 37 beats
# under the paint threshold, worst 2.11 against an eye-calibrated bar of 8.0.
#
# Looking at the rendered frames says what the number cannot: the "flat" is not
# the paint engine (PA.fill_* already lays down value drift + brush banding) and
# it is not missing tooth. It is COMPOSITION. A chamber interior is one smooth
# 900x300 trapezoid in DARK; a corridor is eight thin lines on a smooth field; a
# street is three grey bands under a blank sky. Few large smooth shapes, with
# dead space around them, is exactly what "flat" means in this project's
# vocabulary.
#
# The reference frames that score do so by STACKING MANY SMALL OUTLINED SHAPES
# -- fortknox's gold wall scores because it is ~40 little slabs, not because it
# is noisier. So the lever is structure, not paint constants: do NOT raise
# PA.VALUE / PAPER_GRAIN (that is the road the last two rounds walked, and it
# moves the number without moving the picture), and do NOT rewrite v2paint.
#
# Every helper here is a small outlined component that stacks. They all take an
# explicit integer seed so a re-render is byte-identical.
# ---------------------------------------------------------------------------

def _slab_floor(tile, d, y_far, y_near, half_far, half_near, vpx, seed,
                col=CONCRETE_D, col_lit=CONCRETE, joint=STEEL_D, n=7,
                slabs=4, w=4, x_off=0.0):
    """A floor of slabs in one-point perspective, courses deepening forward.

    This is the single highest-yield primitive here: it converts a smooth
    trapezoid floor into n courses x `slabs` outlined quads, and because the
    courses get TALLER as they come forward it reads as depth rather than as a
    chequered rug. Rows are value-stepped (far rows darker, near rows catching
    the lamp) so the eye gets a light gradient as a by-product of the structure.

    `half_far`/`half_near` are the floor's half-width at the far and near edges,
    centred on `vpx` -- the vanishing point, which is also what staggers the
    vertical joints when cols do not divide evenly.
    """
    img = PA.img_of(d)
    rows = []
    for k in range(n + 1):
        u = (k / float(n)) ** 1.85
        y = y_far + (y_near - y_far) * u
        half = half_far + (half_near - half_far) * u
        rows.append((y, half))
    for k in range(n):
        y0, h0 = rows[k]
        y1, h1 = rows[k + 1]
        if y1 - y0 < 5:
            continue
        # courses nearer the viewer catch more light
        t = k / float(max(1, n - 1))
        c = _mix(col_lit, col, t)
        # vertical joints, staggered course to course so the pattern does not
        # line up into columns
        cuts = [0.0]
        step = 1.0 / slabs
        off = (k % 2) * step * 0.5
        j = 0
        while j < slabs + 1:
            cuts.append((j * step + off) % 1.0)
            j += 1
        cuts = sorted(set(round(c, 4) for c in cuts if 0.0 <= c <= 1.0))
        for a, b in zip(cuts[:-1], cuts[1:]):
            if b - a < 0.04:
                continue
            q = []
            for tt, yy, hh in ((a, y0, h0), (b, y0, h0),
                               (b, y1, h1), (a, y1, h1)):
                q.append((vpx + x_off - hh + 2.0 * hh * tt, yy))
            PA.fill_poly(img, q, c, seed=seed + k * 31 + int(a * 97),
                         value=0.08)
            PA.hand_stroke(d, q, joint, w, closed=True,
                           seed=seed + k * 37 + int(a * 89),
                           wavelength=110.0, vary=0.35)
    # the near lip of the floor, a lit nosing so the ground plane terminates
    PA.hand_stroke(d, [(vpx + x_off - half_near, y_near),
                       (vpx + x_off + half_near, y_near)], INK, 6,
                   closed=False, seed=seed + 7, wavelength=180.0)


def _mix(c0, c1, t):
    """Blend two RGB tuples; t=0 -> c0. Deterministic, no rounding drift."""
    t = max(0.0, min(1.0, t))
    return (int(round(c0[0] + (c1[0] - c0[0]) * t)),
            int(round(c0[1] + (c1[1] - c0[1]) * t)),
            int(round(c0[2] + (c1[2] - c0[2]) * t)))


def _rib_wall(tile, d, x0, x1, y_top, y_bot, n, seed, col=CONCRETE,
              col_dk=STEEL_D, w=5, taper=0.0, y_top_far=None, rivet=True):
    """A run of vertical structural ribs -- columns, wall studs, pilasters.

    Each rib is a three-face block (lit face, front, shadowed side) rather than a
    rectangle, because a flat bar reads as a stripe and a three-face block reads
    as a thing with an edge. `taper` shrinks the ribs toward the vanishing
    point, which is what turns a flat wall into a receding one.
    """
    img = PA.img_of(d)
    step = (x1 - x0) / float(n)
    for k in range(n):
        cx = x0 + step * (k + 0.5)
        bw = step * (0.42 - 0.16 * taper)
        if bw < 3:
            continue
        ytf = y_top if y_top_far is None else (y_top + (y_top_far - y_top) * taper)
        ybf = y_bot - (y_bot - ytf) * 0.18 * taper
        f = [(cx - bw, ytf), (cx + bw, ytf), (cx + bw * 0.86, ybf),
             (cx - bw * 0.86, ybf)]
        PA.fill_poly(img, f, col, seed=seed + k * 11, value=0.09)
        PA.hand_stroke(d, f, INK, w, closed=True, seed=seed + k * 13,
                       wavelength=130.0, vary=0.38)
        # the shadowed return face, offset toward the far side
        off = bw * 0.55
        s = [(cx + bw, ytf), (cx + bw + off, ytf + 4),
             (cx + bw * 0.86 + off, ybf), (cx + bw * 0.86, ybf)]
        PA.fill_poly(img, s, col_dk, seed=seed + k * 17, value=0.07)
        PA.hand_stroke(d, [(cx + bw, ytf), (cx + bw * 0.86, ybf)], INK, 3,
                       closed=False, seed=seed + k * 19, wavelength=110.0,
                       vary=0.4)
        if rivet:
            _rivet_row(d, cx - bw * 0.5, ytf + 12, cx - bw * 0.5,
                       ytf + 12, 1, seed + k * 23, colour=col_dk, r=4)


def _panel_wall(tile, d, x0, y0, x1, y1, cols, rows, seed, col,
                col_seam=STEEL_D, w=4, rivet=True, seam=(0, 0, 0)):
    """A wall of bolted panels -- the surface that says "built", not "painted".

    Seams alone are nearly invisible at ship size; seams PLUS a rivet at each
    seam crossing is what reads as a fabricated wall at 1280x720. `seam` lets a
    caller pass a second colour to every other course so the courses separate.
    """
    img = PA.img_of(d)
    for r in range(rows):
        ya = y0 + (y1 - y0) * r / float(rows)
        yb = y0 + (y1 - y0) * (r + 1) / float(rows)
        for c in range(cols):
            xa = x0 + (x1 - x0) * c / float(cols)
            xb = x0 + (x1 - x0) * (c + 1) / float(cols)
            q = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
            cc = col if (r + c) % 2 == 0 else _mix(col, seam, 0.30)
            PA.fill_poly(img, q, cc, seed=seed + r * 53 + c * 7, value=0.08)
            PA.hand_stroke(d, q, INK, w, closed=True,
                           seed=seed + r * 59 + c * 11, wavelength=120.0,
                           vary=0.35)
            if rivet and (c + r) % 2 == 0:
                for k, (px, py) in enumerate(((xa + 9, ya + 9),
                                               (xb - 9, ya + 9),
                                               (xa + 9, yb - 9),
                                               (xb - 9, yb - 9))):
                    # int(k) in the seed: px is a float and v2paint XORs the
                    # seed, so a float seed is a TypeError, not a wobble.
                    PA.fill_poly(img, PA.ellipse_pts(px, py, 4, 4, n=8),
                                 col_seam, seed=seed + r * 61 + c * 13 + k,
                                 value=0.05)


def _brick_bond(d, x0, y0, x1, y1, seed, col=BRICK, col_m=(140, 106, 90),
                mortar=(176, 176, 172), bw=92, bh=34, w=3):
    """A running-bond brick wall: courses of offset bricks with mortar lines.

    The old f_wall drew NINE full-width horizontal lines on one flat field --
    nine strokes across 1280px of one colour. A bond gives ~8 courses x ~14
    bricks of individually valued brick, which is the fortknox density the
    gold-slab frame gets from its bullion, for the price of one loop.
    """
    img = PA.img_of(d)
    row = 0
    y = y0
    while y < y1:
        yb = min(y + bh, y1)
        off = (row % 2) * (bw * 0.5)
        x = x0 - off - bw
        k = 0
        while x < x1:
            xa = max(x, x0 - 2)
            xb = min(x + bw - 4, x1 + 2)
            if xb - xa > 6:
                c = _mix(col, col_m, ((row * 7 + k * 13) % 5) / 4.0)
                q = [(xa, y + 2), (xb, y + 2), (xb, yb - 2), (xa, yb - 2)]
                PA.fill_poly(img, q, c, seed=seed + row * 71 + k * 17,
                             value=0.10)
                PA.hand_stroke(d, q, mortar, w, closed=True,
                               seed=seed + row * 73 + k * 19,
                               wavelength=90.0, vary=0.4)
            x += bw
            k += 1
        y += bh
        row += 1


def _crate_stack(tile, d, x0, base_y, seed, col=(122, 106, 82),
                 col_dk=(94, 80, 60), n=3, w_=104, h_=62, gap=6, lid=True):
    """A short stack of banded crates -- furniture for a chamber floor.

    Chamber interiors in this chapter were empty because nothing was ever put
    IN them. A crate stack is the cheapest honest way to say 'this room is
    used', and it stacks three outlined boxes per stack.
    """
    img = PA.img_of(d)
    for k in range(n):
        y1 = base_y - k * (h_ + gap)
        y0 = y1 - h_
        xa = x0 + (k % 2) * 10
        xb = xa + w_
        q = [(xa, y0), (xb, y0), (xb, y1), (xa, y1)]
        PA.fill_poly(img, q, col if k % 2 == 0 else col_dk, seed=seed + k * 9,
                     value=0.09)
        PA.hand_stroke(d, q, INK, 5, closed=True, seed=seed + k * 11,
                       wavelength=110.0, vary=0.38)
        # the banding strap across the lid
        PA.hand_stroke(d, [(xa + 6, y0 + h_ * 0.34), (xb - 6, y0 + h_ * 0.34)],
                       col_dk, 7, closed=False, seed=seed + k * 13,
                       wavelength=80.0, vary=0.4)
        if lid:
            PA.hand_stroke(d, [(xa + 6, y0 + 9), (xb - 6, y0 + 9)], INK, 3,
                           closed=False, seed=seed + k * 15, wavelength=70.0)


def _cable_tray(d, pts, seed, col=STEEL_D, w=7, rungs=9, sag=0.0):
    """A cable tray with visible rungs, run along a wall or ceiling.

    Horizontal runs are the cheapest way to break a long smooth band: a tray
    crossing the chamber at two heights reads as services, and its rungs are
    ~9 more small outlined shapes for almost no code.
    """
    img = PA.img_of(d)
    PA.hand_stroke(d, pts, INK, w + 4, closed=False, seed=seed,
                   wavelength=150.0, vary=0.3)
    PA.hand_stroke(d, pts, col, w, closed=False, seed=seed + 1,
                   wavelength=150.0, vary=0.35)
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    for k in range(1, rungs):
        t = k / float(rungs)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
        PA.hand_stroke(d, [(x, y - 9), (x, y + 9)], col, 4, closed=False,
                       seed=seed + k * 5, wavelength=50.0, vary=0.4)


def _window_grid(d, x0, y0, x1, y1, cols, rows, seed, col=(46, 52, 66),
                 frame=INK, lit_col=None, lit_every=4, w=4):
    """A facade of windows -- the thing that makes a flat block a BUILDING.

    Stage E's street had a blank 300px sky band with four trees in front of it.
    Every window is a small outlined rect and every lit window is the only
    warm note in a cold register, so this both densifies and lights.
    """
    img = PA.img_of(d)
    cw = (x1 - x0) / float(cols)
    chh = (y1 - y0) / float(rows)
    k = 0
    for r in range(rows):
        for c in range(cols):
            xa = x0 + cw * c + cw * 0.24
            xb = x0 + cw * (c + 1) - cw * 0.24
            ya = y0 + chh * r + chh * 0.22
            yb = y0 + chh * (r + 1) - chh * 0.22
            lit = (k % lit_every == 0)
            cc = lit_col if (lit and lit_col) else col
            q = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
            PA.fill_poly(img, q, cc, seed=seed + k * 7, value=0.07)
            PA.hand_stroke(d, q, frame, w, closed=True, seed=seed + k * 11,
                           wavelength=80.0, vary=0.35)
            # a mullion, so each window is two panes rather than one tile
            PA.hand_stroke(d, [(xa + (xb - xa) * 0.5, ya),
                               (xa + (xb - xa) * 0.5, yb)], frame, 3,
                           closed=False, seed=seed + k * 13, wavelength=60.0,
                           vary=0.4)
            k += 1

# ---------------------------------------------------------------------------
# ROUND-2 STRUCTURE PRIMITIVES  (dead sky, dead clay, dead road)
#
# WHY THESE EXIST HERE, MEASURED. After round 1 the per-beat pigment table left
# seventeen flat beats, and rendering them at 1280x720 says exactly why, and it
# is NOT the chamber interiors -- round 1 already rebuilt those. It is the bands
# AROUND them:
#
#     b02-b06  6.70-7.67   stage A: 200px of empty sky above the park, and a
#                                  clay band of four smooth ribbons between the
#                                  park and the chamber roof
#     b07-b09  3.30-3.79   stage B: four BLANK grey building trapezoids, no
#                                  windows, under another dead sky; and a 300px
#                                  smooth black chamber under the plate
#     b13      4.10        the hero door: rivets and a wheel, and 520px of one
#                                  smooth blue-grey between them
#     b14-b16  2.65-2.99   the corridor: the ribs are STROKES on a smooth
#                                  field, so eight lines radiate out of a blur
#     b22-b26  2.60-4.63   the street: three smooth grey bands under a blank
#                                  sky, four tree trunks, one small dark rect
#
# So: a skyline that is actually buildings, clay that is actually layered,
# corridor ribs that are FILLED panels with a ceiling and a floor, a street that
# is a street, and a hero door with the same stiffener grammar the finale
# already has. All of it is small outlined shapes, which is the only thing the
# fortknox gold-slab frame does that a gradient cannot fake.
# ---------------------------------------------------------------------------

def _skyline(tile, d, seed, y_base, h_min=70, h_max=150, n=7, x0=-60,
             x1=W + 60, body=(158, 160, 166), top=84, lit=(214, 200, 150),
             cols=3, rows=3, roof='flat', col_dk=None):
    """A run of city blocks filling the band above a horizon, each one a
    windowed facade.

    Stage A had four trees and 190px of empty grey sky; stage B had four blank
    grey trapezoids. A city block is the unit that fixes both, because a block is
    a body plus a grid of small dark rectangles, and _window_grid is already
    written -- it just was never called. `x0`/`x1` run PAST the frame edges so
    the row crops rather than floating with daylight at either side.

    Building tops are clamped to `top` (84) because rows 10-73 are
    TITLE_BACKDROP and a block intruding into the band is a gate failure, not a
    style choice.
    """
    img = PA.img_of(d)
    col_dk = col_dk or _mix(body, INK, 0.35)
    slot = (x1 - x0) / float(n)
    for k in range(n):
        bx = x0 + slot * k + slot * 0.10
        bw = slot * 0.84
        bh = h_min + ((h_max - h_min) *
                      (((k * 37 + seed) % 11) / 10.0))
        ytop = max(top, y_base - bh)
        # the body: a three-face block, so it reads as a mass with a lit face and
        # a shadowed return rather than as one flat rectangle
        PA.fill_poly(img, [(bx, y_base), (bx + bw, y_base - 4),
                           (bx + bw, ytop), (bx, ytop + 5)], body,
                     seed=seed + k * 17, value=0.09)
        PA.hand_stroke(d, [(bx, y_base), (bx + bw, y_base - 4), (bx + bw, ytop),
                           (bx, ytop + 5)], INK, 5, closed=True,
                       seed=seed + k * 19, wavelength=110.0, vary=0.35)
        # the shadowed return face on the right, which is what gives the row
        # depth instead of a picket fence of identical rectangles
        ret = [(bx + bw, y_base - 4), (bx + bw + slot * 0.13, y_base),
               (bx + bw + slot * 0.13, ytop + 4), (bx + bw, ytop)]
        PA.fill_poly(img, ret, col_dk, seed=seed + k * 23, value=0.08)
        PA.hand_stroke(d, [(bx + bw, ytop), (bx + bw, y_base - 4)], INK, 3,
                       closed=False, seed=seed + k * 29, wavelength=90.0)
        # the windows -- the part that actually densifies the band
        _window_grid(d, bx + slot * 0.11, ytop + 16, bx + bw - slot * 0.11,
                     y_base - 22, cols, rows, seed + k * 31,
                     col=(58, 64, 78), frame=INK, lit_col=lit, lit_every=5, w=3)
        # a parapet cap, one more outlined shape per block and the thing that
        # separates roof from sky when the two values are close
        PA.hand_stroke(d, [(bx - 4, ytop + 5), (bx + bw + 4, ytop)], INK, 6,
                       closed=False, seed=seed + k * 37, wavelength=80.0)
        if roof == 'step':
            PA.fill_poly(img, [(bx + bw * 0.24, ytop + 5), (bx + bw * 0.72,
                                                           ytop + 2),
                                (bx + bw * 0.72, ytop - 16),
                                (bx + bw * 0.24, ytop - 12)], col_dk,
                         seed=seed + k * 41, value=0.08)
            PA.hand_stroke(d, [(bx + bw * 0.24, ytop + 5), (bx + bw * 0.72,
                                                           ytop + 2),
                               (bx + bw * 0.72, ytop - 16),
                               (bx + bw * 0.24, ytop - 12)], INK, 4,
                           closed=True, seed=seed + k * 43, wavelength=60.0)


def _clay_bands(d, seed, y0, y1, n=7, cols=None, x0=-60, x1=W + 60, w=3):
    """Thick, VALUE-STEPPED clay with pebble and root detail per course.

    v1's _strata draws n full-width ribbons of near-identical colour separated by
    one thin line -- four horizontal strokes across 1280px, which is the
    textbook flat band. This keeps the ribbon idea and adds what makes soil read
    as soil: each course steps further in value from its neighbour, and each
    carries small inclusions, so a 150px band is eight distinguishable courses
    instead of four identical ones.
    """
    img = PA.img_of(d)
    cols = cols or [CLAY, CLAY_D, (158, 132, 104), (126, 106, 84),
                    (146, 120, 96), (172, 144, 112)]
    h = (y1 - y0) / float(n)
    for k in range(n):
        ya = y0 + h * k
        yb = ya + h
        c = cols[k % len(cols)]
        pts = [(x0, ya), (x1, ya - 7), (x1, yb), (x0, yb + 6)]
        PA.fill_poly(img, pts, c, seed=seed + k * 13, value=0.09)
        PA.hand_stroke(d, [(x0, ya), (x1, ya - 7)], (104, 92, 78), w,
                       closed=False, seed=seed + 31 + k, wavelength=180.0,
                       vary=0.25)
        # inclusions: small stones and clay lenses INSIDE the course. These are
        # what stop a 60px band from reading as one painted stripe.
        per = 7 + (k % 3)
        for j in range(per):
            px = x0 + ((j * 137 + k * 61 + seed) % int(x1 - x0))
            py = ya + h * (0.22 + 0.58 * (((j * 53 + k * 29) % 7) / 6.0))
            rr = 5 + ((j * 7 + k * 3) % 9)
            stone = _mix(c, INK, 0.30) if (j + k) % 3 == 0 else _mix(c, SNOW, 0.16)
            PA.fill_poly(img, PA.ellipse_pts(px, py, rr * 1.5, rr * 0.7, n=12),
                         stone, seed=seed + k * 47 + j * 7, value=0.10)
        # root / hairline cracks running down the course face
        if k % 2 == 0:
            for j in range(3):
                rx = x0 + 90 + ((j * 211 + k * 83 + seed) % int(x1 - x0 - 200))
                PA.hand_stroke(d, [(rx, ya + 4), (rx + 12, ya + h * 0.55),
                                   (rx - 6, yb - 2)], (92, 80, 68), 2,
                               closed=False, seed=seed + k * 59 + j * 5,
                               wavelength=45.0, vary=0.4)


def _corridor_rib(tile, d, y_far, y_near, half_far, half_near, col_lit,
                  col_dk, seed, vx, w=5):
    """ONE corridor rib as a filled, value-separated panel pair.

    Round 1's corridor called _rib() eight times and each call filled a trapezoid
    barely a shade off the background and then stroked only its two converging
    edges -- so the render was eight pairs of black lines over a smooth grey
    blur, measured 2.65. What makes a rib read is that its face is a DIFFERENT
    value from the face beside it, and that it carries a lit edge on one side
    and a dark one on the other. Three faces per side, six small shapes, and the
    perspective finally exists.
    """
    img = PA.img_of(d)
    for sgn in (-1, 1):
        # the recessed face between this rib and the previous one
        face = [(vx + sgn * half_far, y_far), (vx + sgn * half_near, y_near),
                (vx + sgn * (half_near + (half_near - half_far) * 0.42),
                 y_near), (vx + sgn * (half_far + (half_near - half_far) * 0.42),
                           y_far)]
        PA.fill_poly(img, face, col_dk, seed=seed + (0 if sgn < 0 else 3),
                     value=0.08)
        PA.hand_stroke(d, [(vx + sgn * half_far, y_far),
                           (vx + sgn * half_near, y_near)], INK, w,
                       closed=False, seed=seed + (1 if sgn < 0 else 4),
                       wavelength=150.0, vary=0.35)
        # the lit arris along the near edge of the face -- this is the highlight
        # that makes a folded steel panel rather than a painted stripe
        PA.hand_stroke(d,
                       [(vx + sgn * (half_near + (half_near - half_far) * 0.42),
                         y_near),
                        (vx + sgn * (half_far + (half_near - half_far) * 0.42),
                         y_far)], _mix(col_lit, SNOW, 0.30), 4, closed=False,
                       seed=seed + (2 if sgn < 0 else 5), wavelength=150.0,
                       vary=0.35)
        # a rib course band on the face, one small outlined shape per rib
        for b in range(2):
            ty = y_far + (y_near - y_far) * (0.34 + b * 0.30)
            tf = half_far + (half_near - half_far) * (0.34 + b * 0.30)
            tn = half_near + (half_near - half_far) * (0.34 + b * 0.30)
            PA.hand_stroke(d, [(vx + sgn * tf, ty + 5), (vx + sgn * tn, ty)],
                           _mix(col_dk, INK, 0.35), 4, closed=False,
                           seed=seed + 11 + (0 if sgn < 0 else 1) + b * 3,
                           wavelength=95.0, vary=0.35)


def _pavement(tile, d, seed, y0, y1, x0=-60, x1=W + 60, n=14, col=(154, 154,
                150), joint=(96, 96, 94), kerb=True, kerb_col=(178, 178, 174)):
    """A pavement of setts with a kerb line -- the ground under the street.

    Stage E's ground was fill_rect of one colour from y=560 to the frame bottom:
    160px of nothing across 1280. Setts give two courses of individually valued
    blocks and the kerb gives the road a horizontal to terminate against.
    """
    img = PA.img_of(d)
    courses = 2
    for r in range(courses):
        ya = y0 + (y1 - y0) * r / courses
        yb = y0 + (y1 - y0) * (r + 1) / courses
        step = (x1 - x0) / float(n)
        for c in range(n + 1):
            xa = x0 + step * c + (r * step * 0.5 if r % 2 else 0.0)
            xb = xa + step - 5
            if xb > x1:
                xb = x1
            if xb - xa < 8:
                continue
            q = [(xa, ya + 2), (xb, ya), (xb, yb - 2), (xa, yb)]
            cc = _mix(col, joint, ((r * 3 + c * 5) % 4) / 3.0 * 0.30)
            PA.fill_poly(img, q, cc, seed=seed + r * 53 + c * 11, value=0.09)
            PA.hand_stroke(d, q, joint, 3, closed=True,
                           seed=seed + r * 59 + c * 13, wavelength=95.0,
                           vary=0.35)
    if kerb:
        PA.fill_rect(img, [x0, y0 - 16, x1, y0 + 2], kerb_col, seed=seed + 3,
                     value=0.07)
        PA.hand_stroke(d, [(x0, y0 - 14), (x1, y0 - 16)], INK, 6, closed=False,
                       seed=seed + 5, wavelength=200.0)


def _facade(tile, d, seed, x0, y0, x1, y1, body=(172, 170, 166),
            body_dk=(138, 136, 134), cols=4, rows=4, lit=(226, 208, 152),
            shop=True, shop_col=(96, 92, 88), w=5):
    """A street-front facade: wall, window grid, and a shopfront at the foot.

    This is the unit that makes stage E read as a PLACE. A blank block with a
    dark rectangle on it says "there is a door somewhere"; a facade with a
    glazing bar, a lit window, a shopfront and a canopy says "this is an
    ordinary street, and the door is on it".
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [x0, y0, x1, y1], body, seed=seed, value=0.08)
    PA.hand_stroke(d, [(x0, y0), (x1, y0)], INK, w, closed=False, seed=seed + 1,
                   wavelength=140.0)
    PA.hand_stroke(d, [(x0, y0), (x0, y1)], INK, w, closed=False, seed=seed + 2,
                   wavelength=140.0)
    PA.hand_stroke(d, [(x1, y0), (x1, y1)], INK, w, closed=False, seed=seed + 3,
                   wavelength=140.0)
    # the shadowed return on one side, so the facade has a corner
    PA.fill_poly(img, [(x1, y0), (x1 + 26, y0 + 12), (x1 + 26, y1 + 8),
                       (x1, y1)], body_dk, seed=seed + 5, value=0.09)
    PA.hand_stroke(d, [(x1 + 26, y0 + 12), (x1 + 26, y1 + 8)], INK, 4,
                   closed=False, seed=seed + 7, wavelength=90.0)
    # a string course between the shopfront and the upper floors
    _sy = y1 - (y1 - y0) * 0.40
    PA.fill_rect(img, [x0, _sy - 8, x1 + 26, _sy + 8], body_dk, seed=seed + 9,
                 value=0.08)
    PA.hand_stroke(d, [(x0, _sy - 6), (x1 + 26, _sy - 6)], INK, 4,
                   closed=False, seed=seed + 11, wavelength=130.0)
    _window_grid(d, x0 + 22, y0 + 24, x1 - 22, _sy - 20, cols, rows,
                 seed + 13, col=(52, 58, 72), frame=INK, lit_col=lit,
                 lit_every=6, w=4)
    if shop:
        # the shopfront: a deep stall riser, a fascia band, and a glazed front
        PA.fill_rect(img, [x0 + 18, _sy + 22, x1 - 18, y1 - 4], shop_col,
                     seed=seed + 15, value=0.07)
        PA.hand_stroke(d, [(x0 + 18, _sy + 22), (x1 - 18, _sy + 22)], INK, 5,
                       closed=False, seed=seed + 17, wavelength=120.0)
        PA.fill_rect(img, [x0 + 18, y1 - 4, x1 - 18, y1 + 26], _mix(body_dk, INK,
                     0.4), seed=seed + 19, value=0.07)
        for j in range(4):
            gx = x0 + 34 + (x1 - x0 - 68) * j / 4.0
            PA.hand_stroke(d, [(gx, _sy + 30), (gx, y1 - 6)], INK, 4,
                           closed=False, seed=seed + 21 + j, wavelength=70.0)
        # an awning, the one soft shape on an otherwise hard facade
        PA.fill_poly(img, [(x0 + 8, _sy + 14), (x1 + 18, _sy + 14),
                           (x1 + 30, _sy + 34), (x0 - 4, _sy + 34)],
                    (150, 74, 66), seed=seed + 27, value=0.08)
        PA.hand_stroke(d, [(x0 + 8, _sy + 14), (x1 + 18, _sy + 14),
                           (x1 + 30, _sy + 34), (x0 - 4, _sy + 34)], INK, 4,
                       closed=True, seed=seed + 29, wavelength=90.0)


def _lamp_post(d, x, base_y, h, seed, col=(72, 76, 84), lit=(226, 214, 168),
               arm=54):
    """A street lamp, cropped-in friendly: post, arm, head, and a light pool.

    `lit` is a desaturated daylight-warm, NOT LAMP. LAMP is the interior-stage
    lamp colour and at street scale it painted two opaque yellow wedges over the
    pavement that read as spotlights pasted onto the render.
    """
    PA.hand_stroke(d, [(x, base_y), (x, base_y - h)], col, 8, closed=False,
                   seed=seed, wavelength=110.0, vary=0.3)
    PA.hand_stroke(d, [(x - 6, base_y), (x - 6, base_y - h)], INK, 3,
                   closed=False, seed=seed + 1, wavelength=110.0)
    PA.hand_stroke(d, [(x, base_y - h), (x + arm, base_y - h + 12)], col, 7,
                   closed=False, seed=seed + 2, wavelength=80.0)
    PA.fill_poly(PA.img_of(d), [(x + arm - 22, base_y - h + 8),
                                (x + arm + 22, base_y - h + 8),
                                (x + arm + 30, base_y - h + 30),
                                (x + arm - 30, base_y - h + 30)], lit,
                 seed=seed + 3, value=0.05)
    PA.hand_stroke(d, [(x + arm - 22, base_y - h + 8), (x + arm + 22,
                                                       base_y - h + 8),
                       (x + arm + 30, base_y - h + 30),
                       (x + arm - 30, base_y - h + 30)], INK, 4, closed=True,
                   seed=seed + 4, wavelength=60.0)
    # The pool. DAYLIGHT street, so this is not a visible cone -- the first pass
    # painted LAMP at full strength and it rendered as two opaque yellow
    # triangles standing on the pavement, which is the single most artificial
    # thing on the frame. What a daytime street actually shows is a faint warm
    # wash on the setts and nothing in the air, so the pool is a near-neutral
    # 12%-lighter-than-sett value, not the lamp's own colour.
    PA.fill_poly(PA.img_of(d), [(x + arm - 20, base_y - h + 30),
                                (x + arm + 20, base_y - h + 30),
                                (x + arm + 62, base_y + 30),
                                (x + arm - 62, base_y + 30)],
                 (214, 208, 186), seed=seed + 5, value=0.04)
    PA.hand_stroke(d, [(x + arm - 62, base_y + 30), (x + arm + 62, base_y + 30)],
                   (150, 148, 140), 3, closed=False, seed=seed + 6,
                   wavelength=70.0)


def _door_ribs(d, x0, x1, y0, y1, seed, rib_col=(134, 146, 160),
               n=None, w=5, rivet_every=None):
    """Vertical stiffener ribs across a big steel leaf, each a three-face block.

    b13 is the chapter's hero frame and it measured 4.10 -- rivets top and
    bottom, a lock wheel, and 520px of ONE blue-grey fill between them. The
    finale at b37 measured 16.56 doing exactly this same job with the same
    primitives, so this is the finale's grammar lifted to the hero: ribs down
    every stile, dog-bolt bosses across the centre, and a rivet line at head
    and foot. Frame-fill is unchanged -- the leaf still runs off all four
    edges -- because ribs ADD edge to a full frame, they do not replace one.
    """
    img = PA.img_of(d)
    span = x1 - x0
    n = n or max(3, int(span / 190))
    for k in range(n):
        rx = x0 + span * (k + 0.5) / n
        bw = span / n * 0.19
        PA.fill_rect(img, [rx - bw, y0, rx + bw, y1], rib_col,
                     seed=seed + k * 17, value=0.08)
        PA.hand_stroke(d, [(rx - bw, y0), (rx - bw, y1)], STEEL_D, w,
                       closed=False, seed=seed + k * 19, wavelength=190.0)
        PA.hand_stroke(d, [(rx + bw, y0), (rx + bw, y1)], (178, 188, 200), 3,
                       closed=False, seed=seed + k * 23, wavelength=190.0)
        if rivet_every and k % rivet_every == 0:
            _rivet_row(d, rx, y0 + 46, rx, y1 - 46, 5, seed + k * 29,
                       colour=(184, 192, 202), r=9)
    # dog-bolt bosses across the meeting stile -- the round hardware that says
    # "this leaf is held shut", and one more small shape per station
    for j in range(5):
        by = y0 + (y1 - y0) * (0.14 + 0.18 * j)
        for sgn in (-1, 1):
            bx = (x0 + x1) * 0.5 + sgn * 116
            PA.fill_poly(img, PA.ellipse_pts(bx, by, 20, 15, n=14),
                         (120, 132, 146), seed=seed + 200 + j * 7 +
                         (0 if sgn < 0 else 3), value=0.07)
            PA.hand_stroke(d, PA.ellipse_pts(bx, by, 20, 15, n=14), INK, 4,
                           closed=True, seed=seed + 210 + j * 7,
                           wavelength=55.0, vary=0.3)


# The arrival duration used by every moving element. 0.45-0.55s reads as a
# deliberate move; longer and it becomes the picture changing every sample,
# which is the defect this whole rebuild exists to remove.
ARRIVE = 0.5


def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # ---- persistent page tooth under everything --------------------------- #
    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ===================================================================== #
    # STAGE A  b01-b06  "Under the Kremlin, a nuclear bunker waits.          #
    #                 Nobody has ever walked through its door. Its code      #
    #                 name is Object 739. Stalin ordered it built in the     #
    #                 1950s. He wanted one refuge of his own. It sits       #
    #                 below a small park."                                  #
    # The cross-section IS the chapter's opening idea and it holds all six   #
    # beats. v1 redrew it three times (b01, b06, and again inside b07) as    #
    # three different full frames; here it is drawn once and the things that #
    # live in it arrive: the sealed leaf, the desk, the man, the marker.    #
    # ===================================================================== #
    def a_cross(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (176, 184, 190), seed=101, value=0.05)
        # the ground, banded, running off both side edges
        PA.fill_rect(tile, [0, 250, W, H], CLAY, seed=102, value=0.09)
        _strata(d, 103, 300, 660, n=4)
        # the park surface on top
        PA.fill_rect(tile, [0, 214, W, 256], PARK, seed=107, value=0.08)
        PA.hand_stroke(d, [(-20, 220), (W + 20, 214)], INK, 6, closed=False,
                       seed=108, wavelength=190.0)
        for k, x in enumerate((90, 250, 1090, 1210)):
            _tree(d, x, 220, 150, 109 + k)
        # the Kremlin wall sitting on the surface, cropped left
        wall = [(-40, 220), (300, 206), (300, 214), (-40, 228)]
        PA.fill_poly(PA.img_of(d), wall, (176, 118, 96), seed=115, value=0.08)
        PA.hand_stroke(d, [(-40, 220), (300, 206), (300, 250), (-40, 264)],
                       INK, 7, closed=True, seed=116, wavelength=140.0)
        _rivet_row(d, -20, 232, 290, 219, 9, 117)
        # THE chamber: a deep concrete box cut into the clay. Widened from v1
        # (x=300..1060) to x=190..1280 and its ceiling RAISED from y=448 to
        # y=400, because two things now have to fit inside it that did not fit
        # in v1: the leaf that lands at b02, and the man who stands in front of
        # the desk at b05. At v1's 272px ceiling a 250px figure's head sat
        # inside the ceiling slab and his shins stood on the clay OUTSIDE the
        # chamber -- a cream figure on brown earth, which is the one thing the
        # canon's cream-on-dark rule exists to prevent.
        ch = [(300, 400), (1180, 388), (1280, 720), (190, 720)]
        PA.fill_poly(PA.img_of(d), ch, DARK, seed=118, value=0.10)
        PA.hand_stroke(d, [(300, 400), (1180, 388), (1280, 720)], INK, 9,
                       closed=False, seed=119, wavelength=170.0)
        PA.fill_rect(tile, [290, 400, 1190, 458], CONCRETE_D, seed=120,
                     value=0.08)
        PA.hand_stroke(d, [(300, 400), (1180, 388)], CONCRETE_L, 12,
                       closed=False, seed=121, wavelength=150.0)
        _rivet_row(d, 370, 432, 1170, 422, 13, 122)
        # The one working lamp, in the ROOM rather than on the desk. This is a
        # deliberate move: v1 had no light in this chamber at all, so b01-b03
        # were 8 seconds of black box, and the lamp had to be painted onto the
        # b04 card -- which put it ON TOP of the presenter when he arrived at
        # b05 and buried his head under an opaque tan cone. Built into the
        # stage, it is behind everything for the rest of the chapter and the
        # chamber reads as a lit room from its first frame.
        PA.fill_poly(PA.img_of(d), [(284, 458), (466, 458), (512, 596),
                                    (248, 596)], (110, 104, 88), seed=181,
                     value=0.08)
        PA.fill_poly(PA.img_of(d), [(300, 458), (450, 458), (482, 504),
                                    (268, 504)], LAMP, seed=182, value=0.05)
        # ---- THE CHAMBER INTERIOR (the flat-vector fix) -------------------- #
        # Everything below used to be one 900x300 DARK trapezoid with a tan
        # lamp cone on it and nothing else -- a large smooth shape with dead
        # space, which is exactly the composition the critic named. The chamber
        # is the SUBJECT of stage A, so it now gets built: a ribbed back wall,
        # a slab floor in perspective, a cable tray and two crate stacks. Each
        # is a stack of small outlined shapes, and together they fill the lower
        # half of the frame with local detail instead of one void. All seeded,
        # all persistent -- they accrue with the stage, so b01-b06 gain this.
        _rib_wall(tile, d, 300, 1180, 402, 604, 7, 300, col=(84, 88, 98),
                  col_dk=(50, 53, 61), w=5, taper=0.10, y_top_far=396)
        _slab_floor(tile, d, 604, 720, 430, 560, 700, 320, n=6, slabs=5,
                    col=(62, 66, 76), col_lit=(92, 96, 106), joint=(44, 47, 55),
                    w=4)
        _cable_tray(d, [(318, 470), (1170, 458)], 340, col=(88, 92, 102),
                    w=7, rungs=11, sag=10)
        _crate_stack(tile, d, 344, 616, 360, n=3, w_=104, h_=58)
        _crate_stack(tile, d, 1006, 610, 380, n=2, w_=96, h_=54)
        # NO in-art label here. v1 printed "under the park" at (660,384) on
        # every frame of this stage, and the b01 and b06 captions both say the
        # same thing -- three copies of one fact. The caption carries it once.
    els.append(SC.stage(clock, 1, a_cross, j=7))
    # LEFT of centre, not centre. The leaf that lands at b02 owns x=580..1200,
    # so a centred caption spends half its width on the steel and picks up the
    # leaf's rivet rows. At x=410 the whole string sits on the unlit chamber.
    els.append(cap(1, 410, 640, size=32, fill=SNOW))

    # ---- b02  the sealed leaf, standing in the chamber ------------------- #
    # MOVING (1 of 12). "Nobody has ever walked through its door" -- the door
    # coming down into its frame IS the sentence, and it is the chapter's
    # subject arriving 40 seconds early, so it earns the first arrival.
    def a_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _blast_door(d, 890, 570, 620, 380, 132, wheel=True, plates=3)
        # the jamb it closes against, cropping the leaf's right-hand edge
        jamb = [(1160, 396), (W + 60, 396), (W + 60, 760), (1160, 760)]
        PA.fill_poly(PA.img_of(d), jamb, (150, 150, 146), seed=134,
                     value=0.09)
        PA.hand_stroke(d, [(1160, 396), (1160, 760)], INK, 9, closed=False,
                       seed=135, wavelength=190.0)
    els.append(SC.accrue(clock, 2, 7, a_door, kind='shape',
                         motion=SC.enter(clock, 2, dx=0, dy=-70, dur=0.55)))
    # NO caption at b02. A shut steel leaf in a sealed chamber is the whole
    # sentence; printing "Nobody has ever walked through its door" underneath a
    # picture of a shut door says it twice.

    # ---- the presenter, in the cutaway ------------------------------------ #
    # He is the audience surrogate and the reason the opening has an anchor at
    # all: stage A's first two beats are a cross-section and a door, and four
    # seconds of bare backdrop reads as "nothing is happening". He stands at
    # the chamber's left, cropped by the chamber wall, pointing at the leaf --
    # and at b06 he changes expression, which is where the sentence turns from
    # the room to what the room is for.
    def a_presenter_a(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _figure(d, 268, 716, 262, pose='pointing', expression='confused',
                seed=181)
    _bu, _aa, _au = SC.expr_swap(clock, 6, 'confused', 'neutral', until_j=7)
    els.append(E3.E('a_presenter_a', 'character', a_presenter_a,
                    at=clock.at('b02', 0), until=_bu))

    # ---- b03  the name ---------------------------------------------------- #
    # NO new art, and NO caption pile-up. The scene's persistent title strip
    # already reads "Object 739" across the head of EVERY frame, so v1's
    # mid-frame hero word (drawn at 78px in c_title) was a second copy of the
    # title 300px below the first. b03 therefore carries the name ONCE, in the
    # caption, and the beat's visual is the held cross-section -- which is the
    # point of a persistent stage.
    els.append(cap(3, 410, 690, size=32, fill=SNOW))

    # ---- b04  the desk he ordered it at ----------------------------------- #
    # REPLACES (text). The board carries "1950s", so it may not live to stage
    # end -- it would sit on top of nothing at b05 but it IS a text element and
    # the only safe rule for those is hand-off. j=5.
    def a_desk(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the desk, cropped by the frame bottom and sitting INSIDE the chamber
        # (its left edge at y=600 is x=229, so 236 is the first legal column)
        desk = [(236, 596), (664, 596), (664, 760), (222, 760)]
        PA.fill_poly(PA.img_of(d), desk, (118, 96, 72), seed=183, value=0.08)
        PA.hand_stroke(d, [(236, 596), (664, 596)], INK, 7, closed=False,
                       seed=184, wavelength=190.0)
        # the plan he is drawing: a small bunker cross-section on the paper
        pl = [(312, 618), (566, 612), (592, 686), (292, 692)]
        PA.fill_poly(PA.img_of(d), pl, (236, 232, 222), seed=185, value=0.05)
        PA.hand_stroke(d, pl, INK, 4, closed=True, seed=186, wavelength=90.0)
        PA.hand_stroke(d, [(352, 636), (512, 632)], (120, 120, 126), 3,
                       closed=False, seed=189, wavelength=60.0)
        # the desk lamp's own pool, so the man and the plan share one light
        PA.fill_poly(PA.img_of(d), [(232, 592), (668, 592), (682, 640),
                                    (218, 640)], (150, 126, 92), seed=188,
                     value=0.07)
    # ACCRUES, because it is furniture. This is the split that rule 1 asks
    # for: v1 drew the desk, the man and the 1950s on the plan as ONE card, so
    # the desk could not still be there on b05 when the man arrived in front
    # of it. Splitting the layer is what lets the room persist and the words
    # hand off.
    els.append(SC.accrue(clock, 4, 7, a_desk, kind='shape',
                         motion=SC.enter(clock, 4, dx=0, dy=-48, dur=ARRIVE)))

    # REPLACES (text). "1950s" ON the drawing rather than on the wall is the
    # whole reason this label works -- the paper is the one light surface in a
    # dark chamber, so ink on it measures 17:1 where the same ink on the clay
    # above measures 4.4:1. It hands off at b06 so the beat after it does not
    # carry a date it has moved past.
    def a_date(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        D.draw_label(tile, '1950s', center=(432, 644), color=INK, size=34,
                     outline=None, outline_w=0)
        PA.hand_stroke(d, [(372, 674), (492, 671)], RED, 6, closed=False,
                       seed=187, wavelength=80.0)
    els.append(SC.layer(clock, 4, a_date, j=5, kind='shape', eid='a_date'))
    # NO caption at b04. The board PRINTS "1950s" in a 34px label with a red
    # underline, which is the drawn form of the only fact in this sentence the
    # art could not show on its own. A caption here would read "Stalin ordered
    # it built in the 1950s" directly above the words "1950s". j=5 and not j=6
    # for a second reason: at j=6 the date stayed up under b05's caption and
    # the two rendered as one two-line block 50px apart.

    # ---- b05  one refuge of his own --------------------------------------- #
    # The man arrives in the room he ordered. This is the beat the caption
    # survives for: the words carry the intent ("one refuge of his OWN"),
    # which is exactly what a figure standing in a bunker cannot say.
    els.append(cap(5, 410, 690, size=32, fill=SNOW))

    # ---- b06  it sits below a small park ---------------------------------- #
    # A red marker post on the park surface with a dashed line dropping to the
    # chamber roof: the link between the green strip you can see and the dark
    # box you cannot. It arrives without motion -- twelve movers is the budget
    # and this is the least informative of the candidates.
    def a_marker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [632, 196, 648, 258], (150, 118, 78), seed=188,
                     value=0.07)
        PA.fill_rect(tile, [604, 186, 676, 210], RED, seed=189, value=0.07)
        PA.hand_stroke(d, [(604, 186), (676, 186), (676, 210), (604, 210)],
                       INK, 4, closed=True, seed=190, wavelength=50.0)
        for k in range(6):
            y0 = 268 + k * 30
            PA.hand_stroke(d, [(640, y0), (640, y0 + 16)], RED, 6,
                           closed=False, seed=191 + k, wavelength=40.0,
                           vary=0.1)
    els.append(SC.accrue(clock, 6, 7, a_marker, kind='shape'))
    # NO caption at b06. "It sits below a small park" is a spatial relation and
    # the frame IS that relation -- green park band across the top, clay, then
    # the chamber, with a red line now joining them. v1 spent a whole beat on a
    # second cross-section to say it.

    def a_presenter_b(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _figure(d, 268, 716, 262, pose='pointing', expression='neutral',
                seed=181)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))

    # ===================================================================== #
    # STAGE B  b07-b13  "Moscow itself was built on sinking ground.          #
    #                 Everything above the ceiling is hardened steel.         #
    #                 Ordinary buildings nearby rest on thin foundations.     #
    #                 The doors were made to close forever. Each leaf weighs #
    #                 hundreds of tonnes. They are sealed, and never opened.  #
    #                 One closed door, filling the whole frame."             #
    # SEVEN beats, 17.5s -- the longest stage in the chapter, and the one    #
    # that carries the hero. v1 gave b07, b08, b09, b10, b11, b12 and b13    #
    # seven unrelated full frames; here it is ONE cross-section, read top    #
    # down: the city on clay, the water under the city, the steel plate,     #
    # and the chamber with the door standing in it. Each beat adds the one   #
    # thing it is about.                                                     #
    # ===================================================================== #
    def b_section(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (176, 184, 190), seed=211,
                     value=0.05)
        PA.fill_rect(tile, [0, 150, W, H], CLAY, seed=212, value=0.09)
        # the city on the surface, thin and close together. The TITLES BAND is
        # rows 10-73, so every building top must stay below y=73 or it collides
        # with the chapter title: the first pass put these tops at y=22 and four
        # blocks sat inside the band, two of them hard against "Object 739".
        for k, (x, w, h) in enumerate(((80, 190, 44), (330, 150, 66),
                                       (760, 210, 40), (1030, 160, 66))):
            bd = [(x, 160), (x + w, 152), (x + w - 6, 160 - h),
                  (x + 8, 154 - h + 6)]
            PA.fill_poly(PA.img_of(d), bd, (172, 174, 178), seed=216 + k,
                         value=0.07)
            PA.hand_stroke(d, bd, INK, 5, closed=True, seed=220 + k,
                           wavelength=90.0)
        _strata(d, 268, 182, 214, n=3)
        # standing groundwater pooling in the clay. This is the whole of
        # "Moscow was built on sinking ground" and it is in the FIRST frame of
        # the stage, so b07's caption names it rather than leaving the viewer
        # to infer it from a blue patch.
        PA.fill_rect(tile, [0, 200, W, 252], WATER, seed=232, value=0.09)
        PA.hand_stroke(d, [(-20, 202), (W + 20, 196)], (58, 92, 112), 5,
                       closed=False, seed=233, wavelength=180.0)
        for k in range(6):
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(60 + k * 210,
                                                      228 + (k % 3) * 10,
                                                      44, 10, n=20),
                         (120, 158, 174), seed=236 + k, value=0.06)
        # THE STEEL PLATE. 122px of riveted steel between the clay and the
        # chamber, running off both edges: "everything above the ceiling is
        # hardened steel" is a thickness claim and the only way to make it is
        # to draw it thick.
        slab = [(-60, 290), (W + 60, 278), (W + 60, 400), (-60, 414)]
        PA.fill_poly(PA.img_of(d), slab, STEEL, seed=240, value=0.09)
        PA.hand_stroke(d, [(-60, 290), (W + 60, 278)], CONCRETE_L, 10,
                       closed=False, seed=241, wavelength=210.0)
        PA.hand_stroke(d, [(-60, 414), (W + 60, 400)], INK, 9, closed=False,
                       seed=242, wavelength=210.0)
        _rivet_row(d, -20, 330, W + 20, 318, 16, 245, colour=(176, 186, 198))
        _rivet_row(d, -20, 384, W + 20, 372, 16, 262, colour=(176, 186, 198))
        PA.hand_stroke(d, [(-60, 356), (W + 60, 344)], STEEL_D, 6,
                       closed=False, seed=280, wavelength=200.0)
        # the chamber below the plate, cropped by the bottom edge
        ch = [(190, 414), (1150, 402), (1270, 720), (130, 720)]
        PA.fill_poly(PA.img_of(d), ch, DARK, seed=283, value=0.10)
        PA.hand_stroke(d, [(190, 414), (1150, 402), (1270, 720)], INK, 9,
                       closed=False, seed=284, wavelength=190.0)
        # NO "hardened steel" label here. v1 printed it at (300,566) with a red
        # leader. The plate is 122px of riveted steel between two masses of
        # clay; naming it put a text element in the middle of the only part of
        # the frame that was already unambiguous.
    els.append(SC.stage(clock, 7, b_section, j=14))
    # "Moscow itself was built on sinking ground" -- the pooled water under the
    # city is on screen from this beat's first frame, but a still blue patch
    # does not say SINKING on its own, so the words stay here.
    els.append(cap(7, 640, 690, size=32, fill=SNOW))

    # ---- b08  a man on the plate, for scale ------------------------------ #
    # MOVING (2 of 12). The arrival is the scale statement: he walks onto the
    # steel and the plate turns out to be twice his height. He is DARK ink
    # here, not cream -- the v1 note about cream-on-dark applies to the dark
    # interior cards, and this stage's register is a lit cross-section.
    def b_figure(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 620, 286, 195, pose='armscrossed',
                    expression='confused', seed=281)
    els.append(SC.accrue(clock, 8, 14, b_figure, kind='character',
                         motion=SC.enter(clock, 8, dx=-90, dur=ARRIVE)))
    # NO caption at b08. The steel plate is 122px thick with two rivet rows and
    # a man standing on top of it; that is the sentence.

    # ---- b09  thin foundations, beside a thick plate --------------------- #
    # REPLACES (text). Two red bars of the same width, one 16px tall and one
    # 136px tall, side by side: the comparison is geometric, not verbal. Only
    # this beat carries the label, and it hands off at b10.
    def b_foundations(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the wafer under the city
        PA.fill_rect(tile, [-40, 118, W + 40, 134], (206, 202, 192),
                     seed=293, value=0.06)
        PA.hand_stroke(d, [(-40, 118), (W + 40, 118)], INK, 5, closed=False,
                       seed=294, wavelength=150.0)
        PA.fill_poly(PA.img_of(d), [(416, 118), (436, 118), (436, 134),
                                    (416, 134)], RED, seed=295, value=0.07)
        PA.fill_poly(PA.img_of(d), [(456, 278), (476, 278), (476, 414),
                                    (456, 414)], RED, seed=296, value=0.07)
        PA.hand_stroke(d, [(426, 134), (426, 278)], (198, 46, 42), 3,
                       closed=False, seed=297, wavelength=90.0)
        D.draw_label(tile, 'thin foundation', center=(250, 216), color=INK,
                     size=30, outline=None, outline_w=0)
    els.append(SC.layer(clock, 9, b_foundations, j=10, kind='shape'))
    # NO caption at b09. "Ordinary buildings nearby rest on thin foundations"
    # is exactly what the two red bars and the wafer say. v1 captioned this beat
    # AND printed "ordinary" on the art AND drew a red divider line.

    # ---- b10  the leaf ---------------------------------------------------- #
    # MOVING (3 of 12). The chapter's subject arriving. It is drawn with
    # wheel=False and the lock hung separately at head height, because the
    # default wheel sits at the leaf's centre -- which here is y=620, where a
    # b10 caption would have to go, and text over the lock is unreadable.
    def b_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _blast_door(d, 690, 620, 920, 420, 322, wheel=False, plates=4)
        _lock_wheel(d, 690, 530, 86, 336)
    els.append(SC.accrue(clock, 10, 13, b_door, kind='shape',
                         motion=SC.enter(clock, 10, dx=0, dy=-88, dur=0.55)))
    # MOVED from (640,674) with fill=INK to (640,694) with fill=SNOW, for two
    # measured reasons. (1) STRADDLE: at cy=674 the glyph box was y670-691 and
    # the door's base line -- a full-width near-black edge at y=683 (measured
    # lum drops 155 -> 34 across that row) -- ran straight through the bottom of
    # the letters, so the outer glyphs sat on black while the rest sat on the
    # mid door (gate: 1.35:1). (2) COLOUR: INK is near-black, and the brief is
    # explicit that text must never be gray or black because it is hard to see.
    # The door face itself is a uniform mid-tone (lum ~155), and on a mid-tone no
    # chromatic fill clears the 4.5 bar, so the resolver would keep forcing INK
    # there. The base below the door IS dark (lum 34), so SNOW resolves and is
    # KEPT: cream on near-black is the most legible pairing on this frame and is
    # not a black caption. cy=694 puts the whole box (y688-713) inside the dark
    # strip, single register, ~7px clear of the frame bottom.
    els.append(cap(10, 640, 694, size=32, fill=SNOW))

    # ---- b11  hundreds of tonnes ------------------------------------------ #
    # An ordinary truck at the foot of the leaf, and the weight PRINTED. This
    # is the one number the art cannot carry, so it is drawn rather than
    # captioned -- which is also what keeps b10 and b11 from being two
    # consecutive captioned beats. The truck is the smallest moving thing in
    # the chapter (120px) and the only motion in this beat.
    def b_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        tx, ty = 292, 700
        PA.fill_poly(PA.img_of(d), [(tx, ty - 82), (tx + 100, ty - 86),
                                    (tx + 106, ty - 48), (tx + 224, ty - 44),
                                    (tx + 224, ty), (tx, ty)], (188, 192, 198),
                     seed=344, value=0.06)
        PA.hand_stroke(d, [(tx, ty - 82), (tx + 100, ty - 86), (tx + 106, ty - 48),
                           (tx + 224, ty - 44), (tx + 224, ty), (tx, ty)],
                       INK, 5, closed=True, seed=345, wavelength=70.0)
        PA.fill_poly(PA.img_of(d), [(tx + 22, ty - 74), (tx + 92, ty - 76),
                                    (tx + 96, ty - 54), (tx + 22, ty - 52)],
                     (150, 172, 188), seed=348, value=0.05)
        for wf in (0.18, 0.52, 0.90):
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(tx + 224 * wf, ty,
                                                      20, 20, n=16), INK,
                         seed=346, value=0.03)
        D.draw_label(tile, 'HUNDREDS OF TONNES', center=(300, 546), color=INK,
                     size=30, outline=None, outline_w=0)
    els.append(SC.accrue(clock, 11, 13, b_tonnes, kind='shape',
                         motion=SC.enter(clock, 11, dx=-120, dur=0.55)))
    # NO caption at b11. The words are on the door in 30px type with the truck
    # underneath them for scale; the sentence would be the label again.

    # ---- b12  sealed, and never opened ----------------------------------- #
    # MOVING (4 of 12). A weld bead running DOWN the leaf's leading stile is
    # the only motion in the chapter where movement is the meaning rather than
    # a reveal, and it is 210px over 0.55s.
    def b_weld(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        seam = [(248 + (k % 3) * 7 - 4, 424 + k * 30) for k in range(11)]
        PA.hand_stroke(d, seam, (222, 216, 190), 15, closed=False, seed=364,
                       wavelength=48.0, vary=0.45)
        PA.hand_stroke(d, [(248, 424), (248, 720)], (250, 244, 220), 5,
                       closed=False, seed=365, wavelength=48.0, vary=0.5)
        for k in range(9):
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(248 + (k % 2) * 6 - 3,
                                                      436 + k * 38, 13, 9,
                                                      n=12), (240, 234, 208),
                         seed=366 + k, value=0.05)
    els.append(SC.accrue(clock, 12, 13, b_weld, kind='shape',
                         motion=SC.enter(clock, 12, dx=0, dy=-210, dur=0.55)))
    # NO caption at b12, and no "welded shut" label either. A bright uneven
    # bead running the full height of the leading edge is the fact; v1 wrote
    # "welded shut" across the middle of the same leaf.

    # ---- b13  ONE CLOSED DOOR, FILLING THE WHOLE FRAME ------------------ #
    # The one full-frame beat in the chapter, and it is the one the narration
    # explicitly asks for: "One closed door, filling the whole frame." A
    # REPLACE, not an accrue -- nothing may survive underneath a leaf that runs
    # off all four edges. It lives exactly one beat and the stage ends with it.
    def b_one_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], STEEL, seed=381, value=0.10)
        PA.paper_overlay(tile, seed=382)
        _blast_door(d, 640, 360, 1700, 1240, 383, wheel=False, plates=5)
        # A DEEP RECESSED PANEL. Without it a full-frame steel field with a
        # circle on it reads as a wall with a dial; the inset is what makes
        # the eye read "one leaf of a door" rather than "a surface".
        PA.fill_poly(PA.img_of(d), [(-40, 96), (W + 40, 88), (W + 40, 640),
                                    (-40, 652)], (108, 120, 136), seed=384,
                     value=0.07)
        PA.hand_stroke(d, [(-40, 96), (W + 40, 88)], INK, 9, closed=False,
                       seed=385, wavelength=210.0)
        PA.hand_stroke(d, [(-40, 652), (W + 40, 640)], INK, 9, closed=False,
                       seed=386, wavelength=210.0)
        PA.hand_stroke(d, [(-40, 104), (W + 40, 96)], (176, 188, 202), 5,
                       closed=False, seed=387, wavelength=210.0)
        PA.hand_stroke(d, [(120, 150), (1160, 142)], (86, 96, 110), 6,
                       closed=False, seed=388, wavelength=200.0)
        PA.hand_stroke(d, [(120, 596), (1160, 588)], (86, 96, 110), 6,
                       closed=False, seed=389, wavelength=200.0)
        for k in range(16):
            rx = 40 + k * 80
            _rivet_row(d, rx, 128, rx, 128, 1, 400 + k,
                       colour=(180, 190, 202), r=12)
            _rivet_row(d, rx, 612, rx, 612, 1, 440 + k,
                       colour=(180, 190, 202), r=12)
        _lock_wheel(d, 640, 368, 186, 480)
        # THE FRAME. A door running off all four edges with nothing around it
        # reads as an abstract field. The jamb and lintel give it an edge to be
        # shut against, and both are themselves cropped.
        jamb = [(1150, -40), (W + 60, -40), (W + 60, 760), (1150, 760)]
        PA.fill_poly(PA.img_of(d), jamb, (66, 70, 78), seed=500, value=0.09)
        PA.hand_stroke(d, [(1150, -40), (1150, 760)], INK, 13, closed=False,
                       seed=501, wavelength=210.0)
        lint = [(-60, -40), (W + 60, -40), (W + 60, 84), (-60, 92)]
        PA.fill_poly(PA.img_of(d), lint, (66, 70, 78), seed=502, value=0.09)
        PA.hand_stroke(d, [(-60, 92), (W + 60, 84)], INK, 13, closed=False,
                       seed=503, wavelength=210.0)
    els.append(SC.layer(clock, 13, b_one_door, j=14))
    els.append(cap(13, 640, 690, size=34, fill=INK))
    # The caption sits at y=690, BELOW the recessed panel's lower edge at
    # 640..652, so it lands on the mid-value steel body where ink measures
    # 5.6:1. Inside the panel the same ink measures 3.9:1, which is why it is
    # not at 560 the way v1 put it.

    # ===================================================================== #
    # STAGE C  b14-b16  "Stalin reportedly never went inside. The corridors   #
    #                  were lined with lead. Floor to ceiling, plate over     #
    #                  plate."  6.5s.                                        #
    # A ONE-POINT corridor: the vanishing point sits at (640, 340) and every  #
    # rib is a trapezoid converging on it. The first attempt drew only a dark  #
    # band with two wedges and it read as a flat wall with a door on it, not a #
    # corridor -- at full res the perspective was simply absent. Drawing the  #
    # ribs is what makes the depth legible.                                    #
    # ===================================================================== #
    VX, VY = 640, 340           # the vanishing point every rib converges on

    def _rib(d, y_far, y_near, half_far, half_near, col, seed, w=5):
        """One corridor rib: a trapezoid from a near edge to the far throat."""
        near_y0 = y_near - (y_near - y_far) * 0.0
        pts = [(VX - half_far, y_far), (VX + half_far, y_far),
               (VX + half_near, near_y0), (VX - half_near, near_y0)]
        PA.fill_poly(PA.img_of(d), pts, col, seed=seed, value=0.06)
        PA.hand_stroke(d, [(VX - half_near, near_y0),
                           (VX - half_far, y_far)], INK, w, closed=False,
                       seed=seed + 1, wavelength=150.0)
        PA.hand_stroke(d, [(VX + half_near, near_y0),
                           (VX + half_far, y_far)], INK, w, closed=False,
                       seed=seed + 2, wavelength=150.0)
        return pts

    def c_corridor(tile, fw, fh):
        # THE CORRIDOR, REBUILT. This is the single worst frame in the chapter:
        # round 1 measured 2.17-2.65, the joint-worst in the film, and the
        # render showed why. It drew eight nested trapezoids NEAREST FIRST, so
        # each painted over the last and only the narrowest survived -- sixteen
        # black lines radiating out of a smooth grey blur. A lens flare, not a
        # corridor.
        #
        # TWO WRONG FIXES WERE TRIED BEFORE THIS ONE, both recorded here so the
        # next pass does not walk them again:
        #
        #   (1) Painter's algorithm, "frame minus this portal", FARTHEST FIRST.
        #       The throat's outside IS the entire frame, so it covered
        #       everything and the corridor went black.
        #   (2) The same, but drawing the annulus between adjacent portals
        #       NEAREST FIRST. The geometry is right and the ring widths were
        #       right, but the five band values sat within ten of each other,
        #       so it rendered as a grey blur with visible diagonal seams --
        #       2.17, no better.
        #
        # WHAT WORKS. Five nested bands (ceiling / wall / floor / wall / ceiling)
        # laid throat-outward, with each band a WIDE outlined MEMBER rather than
        # a thin line, a rib frame at every station, slab courses on the floor,
        # coffers on the ceiling and services on the walls. And the value steps
        # are LARGE on purpose: the point of a corridor is that the far end is
        # far darker than the near end, and a corridor drawn in five values
        # within ten of each other is a grey blur again, however well drawn.
        d = ImageDraw.Draw(tile)
        img = PA.img_of(d)
        PA.fill_rect(tile, [0, 0, W, H], (54, 56, 66), seed=600, value=0.06)

        JN = 8
        st = []
        for k in range(JN + 1):
            u = k / float(JN)
            s = 0.075 + 0.925 * (1.0 - u) ** 1.22
            st.append((56.0 + 1520.0 * s,
                       VY + (-86.0 - VY) * s,
                       VY + (800.0 - VY) * s))
        st.append((58.0, VY - 28.0, VY + 34.0))       # the throat

        # ---- lay the bands NEAREST FIRST, throat LAST ---------------------- #
        # st[0] is the LARGEST portal (it runs off all four frame edges) and
        # st[-1] is the throat. Painter's algorithm needs farthest drawn first
        # so nearer things overwrite it -- for a tunnel that means the big
        # near portal goes down FIRST and each successively smaller portal is
        # painted on top of it. Drawing throat-first (attempt 3) was exactly
        # backwards: every fill covered the one before it and the last fill,
        # which is the whole frame, buried all nine stations. The render was a
        # uniform grey blur -- 2.21.
        for idx in range(len(st)):
            h, t, b = st[idx]
            v = idx / float(len(st) - 1)
            sd = 620 + idx * 41
            # the corridor body seen THROUGH this opening: darker with depth
            PA.fill_rect(tile, [int(VX - h), int(t), int(VX + h), int(b)],
                         _mix((122, 124, 134), (26, 28, 34), v ** 0.9),
                         seed=sd, value=0.08)
            # ---- THE RIBS: the four members of the portal frame ---------- #
            # A rib is a MEMBER with thickness, not a line. Four outlined bars
            # per station, each with a lit arris on its near face, is what makes
            # the eye read a series of frames receding instead of a starburst.
            # idx 0 has no predecessor -- st[-1] would wrap round to the throat
            # and give a negative, nonsense ring width -- so it gets a
            # hand-picked 88px jamb, which is also what fills the frame edges.
            hn, tn, bn = st[idx - 1] if idx > 0 else (h + 88.0, t - 88.0,
                                                      b + 88.0)
            mh = max(4.0, (hn - h) * 0.34)
            mv = max(4.0, (tn - t) * 0.34)
            mb = max(4.0, (b - bn) * 0.34)
            lit = _mix((150, 152, 162), (34, 36, 44), v ** 0.9)
            dk = _mix((78, 80, 90), (18, 20, 26), v ** 0.9)
            # ceiling member
            PA.fill_rect(img, [VX - h - mh, t - mv, VX + h + mh, t], dk,
                         seed=sd + 1, value=0.07)
            PA.hand_stroke(d, [(VX - h - mh, t - mv), (VX + h + mh, t - mv)],
                           INK, 4 if idx < 6 else 3, closed=False,
                           seed=sd + 2, wavelength=170.0, vary=0.3)
            PA.hand_stroke(d, [(VX - h - mh, t), (VX + h + mh, t)], lit, 4,
                           closed=False, seed=sd + 3, wavelength=170.0,
                           vary=0.3)
            # floor member
            PA.fill_rect(img, [VX - h - mh, b, VX + h + mh, b + mb], dk,
                         seed=sd + 4, value=0.07)
            PA.hand_stroke(d, [(VX - h - mh, b + mb), (VX + h + mh, b + mb)],
                           INK, 4 if idx < 6 else 3, closed=False,
                           seed=sd + 5, wavelength=170.0, vary=0.3)
            PA.hand_stroke(d, [(VX - h - mh, b), (VX + h + mh, b)], lit, 4,
                           closed=False, seed=sd + 6, wavelength=170.0,
                           vary=0.3)
            # the two jambs, three-face blocks so they read as folded plate
            for _s in (-1, 1):
                PA.fill_rect(img, [VX + _s * h - mh, t - mv,
                                   VX + _s * h + mh, b + mb], lit,
                             seed=sd + 7 + (0 if _s < 0 else 3), value=0.07)
                PA.fill_rect(img, [VX + _s * h + mh * 0.15, t - mv,
                                   VX + _s * h + mh, b + mb], dk,
                             seed=sd + 8 + (0 if _s < 0 else 3), value=0.06)
                PA.hand_stroke(d, [(VX + _s * h - mh, t - mv),
                                   (VX + _s * h - mh, b + mb)], INK,
                               5 if idx < 6 else 3, closed=False,
                               seed=sd + 9 + (0 if _s < 0 else 3),
                               wavelength=160.0, vary=0.32)
                PA.hand_stroke(d, [(VX + _s * h + mh, t - mv),
                                   (VX + _s * h + mh, b + mb)],
                               _mix(lit, SNOW, 0.30), 3, closed=False,
                               seed=sd + 10 + (0 if _s < 0 else 3),
                               wavelength=160.0, vary=0.32)
                # three bolt bosses up each jamb: the small repeated shape
                # Radius is CAPPED. Scaled straight off the member thickness the
                # near stations (mh up to 88px) grew 90px decagons that read as
                # black scorch marks smeared down the walls, not fixings. A
                # dog-bolt is the size of a bolt at any distance.
                #
                # They are also pushed OUTWARD off the jamb centreline by their
                # own radius. This loop runs nearest-first, so the next
                # (farther, smaller) station's fill lands on the inner half of
                # anything standing exactly on the boundary x = VX +/- h --
                # which left every boss half-buried and reading as confetti
                # floating on the wall. Offsetting by br puts the whole boss in
                # the visible ring between this portal and the next.
                br = min(max(4.0, mh * 0.5), 13.0)
                bx = VX + _s * (h + br * 0.9)
                for _b in range(3):
                    by = t + (b - t) * (0.22 + 0.28 * _b)
                    PA.fill_poly(img, PA.ellipse_pts(bx, by, br, br, n=10),
                                 _mix(lit, SNOW, 0.30), seed=sd + 11 + _b * 3 +
                                 (0 if _s < 0 else 1), value=0.06)
                    PA.fill_poly(img, PA.ellipse_pts(bx, by,
                                                      br * 0.52, br * 0.52,
                                                      n=8),
                                 _mix(lit, INK, 0.45), seed=sd + 12 + _b * 3 +
                                 (0 if _s < 0 else 1), value=0.05)
            # ---- FLOOR COURSES ------------------------------------------- #
            # Joints across the floor, converging. Without them the floor is a
            # smooth grey band 250px deep and the whole lower half of the frame
            # reads flat no matter how good the ribs are.
            if idx < len(st) - 2:
                for _c in range(3):
                    u2 = 0.18 + 0.30 * _c
                    PA.hand_stroke(d, [(VX - h + (hn - h) * u2,
                                        b + (bn - b) * u2),
                                       (VX + h - (hn - h) * u2,
                                        b + (bn - b) * u2)],
                                   _mix(lit, INK, 0.34), 4, closed=False,
                                   seed=sd + 20 + _c, wavelength=130.0,
                                   vary=0.3)
            # ---- CEILING COFFERS ------------------------------------------ #
            if idx < len(st) - 2:
                for _c in range(2):
                    u2 = 0.26 + 0.34 * _c
                    PA.hand_stroke(d, [(VX - h + (hn - h) * u2,
                                        t - (t - tn) * u2),
                                       (VX + h - (hn - h) * u2,
                                        t - (t - tn) * u2)],
                                   _mix(lit, INK, 0.42), 3, closed=False,
                                   seed=sd + 24 + _c, wavelength=110.0,
                                   vary=0.3)
            # ---- WALL SERVICES --------------------------------------------- #
            # A conduit and a dado line each side. Two long converging strokes
            # per station; they are what a real corridor has and this one did
            # not, and they cross the wall's smooth value with two more edges.
            if idx < len(st) - 3:
                for _s in (-1, 1):
                    PA.hand_stroke(d, [(VX + _s * (h + (hn - h) * 0.34),
                                        t + (b - t) * 0.26),
                                       (VX + _s * (h + (hn - h) * 0.30),
                                        t + (b - t) * 0.26)],
                                   _mix(lit, STEEL_D, 0.50), 6, closed=False,
                                   seed=sd + 28 + (0 if _s < 0 else 2),
                                   wavelength=150.0, vary=0.3)
                    PA.hand_stroke(d, [(VX + _s * (h + (hn - h) * 0.60),
                                        t + (b - t) * 0.66),
                                       (VX + _s * (h + (hn - h) * 0.56),
                                        t + (b - t) * 0.66)],
                                   _mix(lit, INK, 0.38), 4, closed=False,
                                   seed=sd + 29 + (0 if _s < 0 else 2),
                                   wavelength=150.0, vary=0.3)

        # ---- the throat, the destination, and the one working light ------- #
        PA.fill_rect(tile, [int(VX - 58), int(VY - 28), int(VX + 58),
                            int(VY + 34)], DARKER, seed=596, value=0.08)
        PA.fill_rect(img, [VX - 116, VY - 40, VX + 116, VY - 26], LAMP,
                     seed=597, value=0.05)
        PA.hand_stroke(d, [(VX - 116, VY - 40), (VX + 116, VY - 40)], INK, 5,
                       closed=False, seed=598, wavelength=100.0)
        PA.fill_poly(img, [(VX - 116, VY - 40), (VX + 116, VY - 40),
                           (VX + 54, VY - 6), (VX - 54, VY - 6)],
                     (128, 124, 106), seed=599, value=0.05)
    els.append(SC.stage(clock, 14, c_corridor, j=17))

    def c_door_end(tile, fw, fh):
        # The door sits AT the vanishing point, small, so the corridor reads
        # as leading somewhere. Scale is deliberate -- a big door here flattens
        # the depth it is supposed to be the destination of.
        _blast_door(ImageDraw.Draw(tile), VX, VY + 10, 150, 190, 401,
                    wheel=True, plates=3)
    els.append(SC.accrue(clock, 14, 17, c_door_end, kind='shape'))

    def c_stalin(tile, fw, fh):
        # Cropped by the LEFT edge, standing IN the corridor. b15 is the line
        # that says he never went in, so having a figure in the corridor the
        # whole time is the irony the beat needs.
        SC.closeup(ImageDraw.Draw(tile), 130, 400, 165, 'skeptic', 403)
    els.append(SC.layer(clock, 14, c_stalin, j=16))
    els.append(cap(15, 700, 660, size=32, fill=SNOW))

    def c_lead_plates(tile, fw, fh):
        # "Floor to ceiling, plate over plate." Lead leaves swing in from the
        # LEFT and wall off the corridor -- you still see the ribs and the far
        # door down the right.
        #
        # ROUND-2 REBUILD. Pass 1 drew NINE full-height leaves at a 344px pitch,
        # which tiled edge to edge and buried the corridor behind a flat striped
        # wall. Pass 2 pulled back to TWO leaves -- which overshot: b16 measured
        # 6.25 and the render showed why. Two 300px rectangles with one outline
        # each is exactly the "few large smooth shapes with dead space" the
        # pigment gate exists to catch, and the left 42% of the frame was one
        # flat blue-grey field.
        #
        # A lead plate is not a rectangle. It is a stack of sheets: a bevelled
        # edge catching the light, a seam where the next sheet laps it, a row of
        # dog-bolts through the lap, and a shallow swage line pressed into the
        # face. Five sheets at staggered x, each carrying all four of those, fill
        # the left of the frame with edge-rich small shapes while still reading
        # as one continuous wall of lead coming in.
        d = ImageDraw.Draw(tile)
        img = PA.img_of(d)
        # Each sheet: (x_left, x_right, face colour, seed offset). The stack
        # runs right-to-left in draw order so each sheet laps the one before it
        # and its lit bevel stays visible -- the overlap is the whole point.
        sheets = ((150, 452, LEAD, 0), (36, 366, LEAD_L, 1),
                  (-96, 250, LEAD, 2), (-232, 122, LEAD_L, 3),
                  (-360, -6, LEAD, 4))
        for k, (x0, x1, col, so) in enumerate(sheets):
            sd = 660 + so * 17
            y0, y1 = -40, H + 40
            PA.fill_rect(img, [x0, y0, x1, y1], col, seed=sd, value=0.07)
            # the lapped under-sheet, a hair darker, peeking out at the seam
            PA.fill_rect(img, [x1 - 16, y0, x1, y1],
                         _mix(col, INK, 0.30), seed=sd + 1, value=0.06)
            # the bevel: a lit chamfer along the top and bottom of the sheet
            PA.fill_rect(img, [x0 + 10, y0, x1 - 16, y0 + 15],
                         _mix(col, SNOW, 0.34), seed=sd + 2, value=0.05)
            PA.fill_rect(img, [x0 + 10, y1 - 15, x1 - 16, y1],
                         _mix(col, INK, 0.34), seed=sd + 3, value=0.05)
            # the sheet's own outline: heavy on the leading edge
            PA.hand_stroke(d, [(x0, y0), (x0, y1)], INK, 6, closed=False,
                           seed=sd + 4, wavelength=180.0)
            PA.hand_stroke(d, [(x0, y0), (x1, y0)], INK, 5, closed=False,
                           seed=sd + 5, wavelength=180.0)
            PA.hand_stroke(d, [(x0, y1), (x1, y1)], INK, 5, closed=False,
                           seed=sd + 6, wavelength=180.0)
            # a swage line pressed across the face, and two more below it: the
            # shallow ribs that stop a lead sheet reading as a flat panel
            for j, fy in enumerate((0.24, 0.53, 0.81)):
                yy = y0 + (y1 - y0) * fy
                PA.hand_stroke(d, [(x0 + 22, yy), (x1 - 26, yy)],
                               _mix(col, INK, 0.26), 4, closed=False,
                               seed=sd + 7 + j, wavelength=150.0, vary=0.28)
                PA.hand_stroke(d, [(x0 + 22, yy + 5), (x1 - 26, yy + 5)],
                               _mix(col, SNOW, 0.22), 3, closed=False,
                               seed=sd + 10 + j, wavelength=150.0, vary=0.28)
            # a column of dog-bolts down the lapped seam
            for j in range(5):
                yy = y0 + 96 + j * 122
                PA.fill_poly(img, PA.ellipse_pts(x1 - 8, yy, 11, 11, n=10),
                             _mix(col, SNOW, 0.40), seed=sd + 13 + j,
                             value=0.05)
                PA.fill_poly(img, PA.ellipse_pts(x1 - 8, yy, 5, 5, n=8),
                             _mix(col, INK, 0.50), seed=sd + 18 + j,
                             value=0.05)
    # MOVING: the plates swinging in is the one moment here where movement IS
    # the information -- the lead arrives, and the corridor is walled off.
    els.append(SC.accrue(clock, 16, 17, c_lead_plates,
                         motion=SC.enter(clock, 16, dx=-220, dy=0, dur=0.55)))

    # ===================================================================== #
    # STAGE D  b17-b21  "Below that, a control room waits. The room is said   #
    #                  to hold one console. A console drawn small, in the     #
    #                  dark. One row of switches, one big button. No official #
    #                  record confirms the console."  12.2s.                 #
    # The dark room, lit by ONE lamp cone. Darkness is the subject here, so   #
    # the ONE element that must not be over-stuffed is the lit area: the      #
    # console sits in the cone and everything else stays black.              #
    # ===================================================================== #
    def d_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (48, 50, 58), seed=700, value=0.06)
        PA.fill_rect(tile, [0, 596, W, H], DARKER, seed=701, value=0.07)
        room = [(-40, 210), (760, 190), (900, 596), (-40, 596)]
        PA.fill_poly(PA.img_of(d), room, (58, 60, 70), seed=702, value=0.07)
        PA.hand_stroke(d, [(-40, 210), (760, 190)], (86, 88, 98), 6,
                       closed=False, seed=703, wavelength=200.0)
        # ---- ROOM STRUCTURE (the flat-vector fix) -------------------------- #
        # This stage is the darkest in the chapter and it measured 2.11 -- the
        # worst frame in the film. The cause was not darkness: it was that the
        # darkness was EMPTY. Two thirds of the frame were one smooth fill with
        # nothing in it. Darkness stays the subject; it just stops being a void.
        # Every value below sits within a few steps of its ground so the frame
        # still reads as unlit -- the structure is legibility at low contrast,
        # not a second light source.
        #
        # Back wall: panel courses + rivet columns, in a value only ~8 up off
        # the fill. Enough edge to break the plane, not enough to lift it.
        _panel_wall(tile, d, -40, 232, 452, 592, 6, 5, 760, col=(68, 70, 80),
                    col_seam=(44, 46, 54), w=3, seam=(86, 88, 98))
        # Floor: courses running away from the viewer toward the console, each
        # stepping up in value so the plane reads as a floor and not a wedge.
        # y_near is H (720), not the 596 wall foot: the old floor stopped at the
        # wall line and left a 124px dead band across the bottom of the frame,
        # which is 17% of the picture doing nothing.
        _slab_floor(tile, d, 470, H, 400, 560, 640, 790, n=7, slabs=6,
                    col=(64, 66, 76), col_lit=(88, 90, 100), joint=(40, 42, 50),
                    w=3, x_off=0.0)
        # Services down the left wall: a pipe run and a cable tray, the two
        # things that are always in a real plant room and always missing here.
        PA.hand_stroke(d, [(38, 246), (38, 592)], (86, 88, 100), 9,
                       closed=False, seed=764, wavelength=150.0)
        PA.hand_stroke(d, [(74, 252), (74, 592)], (72, 74, 86), 6,
                       closed=False, seed=765, wavelength=150.0)
        for _i, _y in enumerate((272, 330, 388, 446, 504, 562)):
            PA.fill_rect(PA.img_of(d), [30, _y - 6, 82, _y + 6],
                         (100, 102, 114), seed=766 + _i, value=0.07)
        _cable_tray(d, [(96, 262), (470, 250)], 772, col=(74, 76, 88), w=6,
                    rungs=8, sag=7)
        # A crate + drum pair in the near-left dark, cropped by the frame edge.
        # Dead space is what made this frame flat; something has to sit in it.
        _crate_stack(tile, d, 96, 594, 780, n=2, w_=96, h_=54)
        # Ceiling services across the top band: two downstand beams and a duct
        # run. Rows 10-73 belong to TITLE_BACKDROP, so this starts at row 78 and
        # the band above it stays uniform -- memory
        # verify-a-remedy-does-not-trip-the-gate-that-flags-it, the backdrop's
        # own seam is what the intrusion gate catches.
        PA.fill_rect(PA.img_of(d), [0, 78, W, 128], (40, 42, 50), seed=790,
                     value=0.06)
        for _i, _bx in enumerate((0, 300, 640, 980, 1240)):
            PA.fill_rect(PA.img_of(d), [_bx, 128, _bx + 62, 176],
                         (58, 60, 70), seed=792 + _i, value=0.07)
            PA.hand_stroke(d, [(_bx, 128), (_bx + 62, 128)], (96, 98, 110), 4,
                           closed=False, seed=796 + _i, wavelength=70.0)
        _cable_tray(d, [(-20, 92), (1300, 86)], 798, col=(66, 68, 80), w=6,
                    rungs=14, sag=6)
        # Duct + hangers down the upper right, the dark quarter of the frame.
        PA.fill_rect(PA.img_of(d), [880, 176, 1280, 232], (52, 54, 64),
                     seed=802, value=0.07)
        PA.hand_stroke(d, [(880, 176), (1280, 176)], (84, 86, 98), 5,
                       closed=False, seed=803, wavelength=110.0)
        for _i, _hx in enumerate((930, 1050, 1170, 1270)):
            PA.hand_stroke(d, [(_hx, 128), (_hx, 176)], (78, 80, 92), 4,
                           closed=False, seed=806 + _i, wavelength=60.0)
        # The right-hand wall, cropped by the frame edge: a doorway jamb with a
        # recessed leaf and its own rivets. The presenter stands here from b17
        # on, so this is what he is standing in front of -- before it he was a
        # cream figure on an unmodulated field.
        _rib_wall(tile, d, 900, 1280, 200, 590, 4, 810, col=(64, 66, 76),
                  col_dk=(42, 44, 52), w=5, taper=0.06, y_top_far=196)
        PA.fill_rect(PA.img_of(d), [1010, 250, 1180, 590], (38, 40, 48),
                     seed=814, value=0.06)
        PA.hand_stroke(d, [(1010, 250), (1180, 250), (1180, 590), (1010, 590)],
                       (92, 94, 106), 6, closed=True, seed=815, wavelength=120.0)
        _rivet_row(d, 1010, 1018, 1180, 272, 8, seed=816)
        _rivet_row(d, 1010, 1018, 1180, 568, 6, seed=817)
        # ONE lamp cone. Two cones were drawn first and they flattened the
        # room into a lit box; a single cone leaves the dark legible.
        PA.fill_poly(PA.img_of(d),
                     [(520, 104), (700, 104), (900, 300), (320, 300)],
                     (176, 172, 146), seed=704, value=0.05)
        SC.title_backdrop(tile, 1521, col=(96, 98, 110))
    els.append(SC.stage(clock, 17, d_room, j=22))

    def d_console(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # _console takes a trailing seed; omitting it silently shifted every
        # later positional arg, which is how the first pass drew the console
        # with no screen and no rivets.
        #
        # SCALED. 380x200 in a 1280x720 frame is a prop, not a subject, and the
        # brief's frame-fill rule says anything under a third of the frame width
        # is a defect. 460x250 at base_y 520 puts its lit crown in the lamp cone
        # and its foot on the near floor course, so the console is the largest
        # object in the composition instead of one of three small grey shapes.
        _console(d, 600, 520, 460, 250, 710)
        # ---- CONSOLE FACE (the flat-vector fix) --------------------------- #
        # _console draws one smooth 460x250 wedge. Scaled up it now dominates
        # the frame, which means its flatness dominates too -- the metric went
        # UP while the middle of the picture got worse. So articulate it the
        # way a real desk is: a kicked plinth, three ribs across the slope, a
        # knee recess, a louvred vent and a rivet line at each cheek.
        _cx, _by, _cw, _ch = 600, 520, 460, 250
        _top = _by - _ch
        PA.fill_rect(PA.img_of(d), [_cx - _cw * 0.50, _by - 26, _cx + _cw * 0.50,
                                     _by + 6], (56, 58, 68), seed=730,
                     value=0.07)
        PA.hand_stroke(d, [(_cx - _cw * 0.50, _by - 26), (_cx + _cw * 0.50,
                                                           _by - 26)],
                       INK, 5, closed=False, seed=731, wavelength=100.0)
        # Knee recess: the dark notch a desk has where a person sits.
        PA.fill_rect(PA.img_of(d), [_cx - 66, _by - 96, _cx + 66, _by - 24],
                     (44, 46, 54), seed=732, value=0.06)
        PA.hand_stroke(d, [(_cx - 66, _by - 96), (_cx + 66, _by - 96)], INK, 5,
                       closed=False, seed=733, wavelength=80.0)
        # Ribs across the slope, following its rake.
        for _i, _u in enumerate((0.26, 0.50, 0.74)):
            _xa = _cx - _cw * 0.40 + _cw * 0.80 * _u
            _xb = _cx - _cw * 0.50 + _cw * 1.00 * _u
            PA.hand_stroke(d, [(_xa, _top + 4), (_xb, _by - 30)], (72, 74, 86), 6,
                           closed=False, seed=736 + _i, wavelength=90.0)
            PA.hand_stroke(d, [(_xa + 7, _top + 4), (_xb + 7, _by - 30)],
                           (122, 124, 136), 3, closed=False, seed=740 + _i,
                           wavelength=90.0)
        # Louvre slots on the left cheek of the slope.
        for _i in range(4):
            _y = _top + 54 + _i * 30
            PA.fill_rect(PA.img_of(d), [_cx - _cw * 0.44, _y,
                                         _cx - _cw * 0.44 + 96, _y + 12],
                         (38, 40, 48), seed=744 + _i, value=0.05)
        _rivet_row(d, _cx - _cw * 0.44, _top + 26, _cx + _cw * 0.44,
                   _top + 26, 7, seed=750, r=6)
        # "said to exist" -- v1 set this in INK on this dark ground, which
        # measures 1.32:1 and is invisible. SNOW is the fix.
        D.draw_label(tile, 'said to exist', center=(610, 268), color=SNOW,
                     size=30)
    els.append(SC.accrue(clock, 18, 20, d_console, kind='shape',
                         motion=SC.enter(clock, 18, dx=0, dy=-40, dur=0.50)))

    def d_warm(tile, fw, fh):
        # The lamp actually pooling on the console at b19. No caption: the
        # light finding the console is the sentence.
        # Value dropped 222->186: at 222 the pool was brighter than the console
        # it is supposed to be revealing, so the screen and the switch bank
        # vanished into their own light. A lamp that erases its subject is the
        # opposite of "the light finds the console".
        d = ImageDraw.Draw(tile)
        PA.fill_poly(PA.img_of(d),
                     [(520, 120), (700, 120), (860, 430), (360, 430)],
                     (186, 180, 150), seed=710, value=0.04)
    els.append(SC.accrue(clock, 19, 22, d_warm, kind='bg'))

    def d_switches(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Bank re-spanned to sit ON the scaled console (cx 600, w 460 -> 370..830,
        # top row y ~300). The old 380..800 overhung a 460-wide console by a
        # pixel each side and read as a separate shelf floating in the light.
        _switch_bank(d, 404, 352, 796, 424, 586, n=5, big_at=3)
        d.ellipse([768, 348, 794, 374], fill=RED)
    els.append(SC.accrue(clock, 20, 22, d_switches, kind='shape',
                         motion=SC.enter(clock, 20, dx=0, dy=-46, dur=0.45)))

    def d_presenter_a(tile, fw, fh):
        # CREAM on dark. The default ink is INK (24,24,28); against this room
        # (48,50,58) that is a 1.4:1 read and he was a silhouette with a pale
        # head, not a character. ink=(238,236,228) is the STYLE_CANON rule for
        # the space register.
        # x 1120 -> 1076 with height 330 -> 372: at the old x his pointing arm
        # ran off the right edge, and memory resize-figure-check-neighbors says
        # check the neighbours after every bump, so the taller figure is pulled
        # back inboard to keep the whole gesture inside the frame.
        SC.fullbody(ImageDraw.Draw(tile), 1076, 600, 372, 'pointing',
                    'awed', 590, ink=(238, 236, 228))
    def d_presenter_b(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 1076, 600, 372, 'pointing',
                    'worried', 590, ink=(238, 236, 228))
    _bu, _aa, _au = SC.expr_swap(clock, 20, 'awed', 'worried', until_j=22)
    els.append(E3.E('d_presenter_a', 'character', d_presenter_a,
                    at=clock.at('b17', 0), until=_bu))
    els.append(E3.E('d_presenter_b', 'character', d_presenter_b,
                    at=_aa, until=_au))

    def d_folder(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [430, 470, 810, 570], (196, 190, 168), seed=720,
                     value=0.06)
        PA.hand_stroke(d, [(430, 470), (810, 470), (810, 570), (430, 570)],
                       INK, 5, closed=True, seed=721, wavelength=90.0)
        PA.hand_stroke(d, [(430, 522), (810, 522)], INK, 4, closed=False,
                       seed=722, wavelength=120.0)
        D.draw_label(tile, 'NO RECORD', center=(620, 626), color=SNOW,
                     size=30)
    # REPLACES the console: the open empty folder is the same region of the
    # frame, so both living at once is a pile-up.
    els.append(SC.layer(clock, 21, d_folder, j=22))

    # ===================================================================== #
    # STAGE E  b22-b26  "Other bunkers from that era were documented. This   #
    #                  one has never been filmed inside. Satellite images    #
    #                  show only the surface. The entrance sits behind an    #
    #                  ordinary fence. An ordinary fence on an ordinary       #
    #                  street."  12.7s.                                      #
    # DAYLIGHT, and deliberately so: after two dark stages the point of this #
    # stage is that the place looks like nothing. A dark card would say      #
    # "secret" in the viewer's gut before the picture says it.                #
    # ===================================================================== #
    def e_street(tile, fw, fh):
        # THE STREET, REBUILT. v1 drew this as FOUR horizontal fills -- sky,
        # concrete, kerb band, road -- with four tree trunks in front of them and
        # a 1280x160 blank sky. Per-beat pigment put b23 at 2.60, the joint-worst
        # frame in the chapter, and the render shows why: it is not a street, it
        # is a value chart. Five smooth bands across the full width.
        #
        # What the narration needs is the OPPOSITE of a threat -- an ordinary
        # street with shops and traffic, so the entrance has nothing to hide
        # behind. So this is now a proper street frontage, cropped at both
        # edges: two shopfront facades with window grids, a gap of railings and
        # a lamp between them, a paved sidewalk and a kerb, and the road running
        # off the bottom of the frame with a bus shelter on it. The bus shelter
        # is load-bearing: it is the single object that says "people wait here
        # for buses", and without it the road is just a grey band.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 204, 208), seed=800,
                     value=0.04)
        # Two facades, cropped left and right so the block runs off frame. The
        # gap between them at x=620..900 is where the fence and the entrance go
        # at b25, and it is deliberately the LOWEST built mass on the street.
        _facade(tile, d, 810, -80, 96, 560, 470, body=(174, 170, 164),
                body_dk=(140, 136, 132), cols=4, rows=3, lit=(228, 210, 154))
        _facade(tile, d, 830, 900, 110, 1400, 470, body=(166, 164, 160),
                body_dk=(132, 130, 128), cols=4, rows=3, lit=(224, 206, 150))
        # the gap: a low wall and a railing behind it, so the entrance recess is
        # a piece of the street rather than a hole cut in a backdrop
        PA.fill_rect(tile, [560, 300, 900, 470], (156, 152, 148), seed=851,
                     value=0.08)
        PA.hand_stroke(d, [(560, 302), (900, 300)], INK, 6, closed=False,
                       seed=852, wavelength=180.0)
        for _i in range(7):
            rx = 580 + _i * 46
            PA.hand_stroke(d, [(rx, 300), (rx, 300)], (108, 106, 104), 5,
                           closed=False, seed=854 + _i, wavelength=40.0)
        # sidewalk: setts + kerb, the two courses round to the road
        _pavement(tile, d, 860, 470, 560, col=(158, 158, 154),
                  joint=(108, 108, 106), n=16)
        PA.fill_rect(tile, [0, 560, W, H], (86, 86, 88), seed=804, value=0.06)
        PA.hand_stroke(d, [(0, 560), (W, 562)], (232, 232, 228), 8,
                       closed=False, seed=805, wavelength=220.0)
        # The road. Not one fill: a carriageway of worn tarmac with a dashed
        # centre line, and two drain gratings. 160px of one grey across 1280 is
        # the flat-band the gate keeps catching.
        for _i, _ry in enumerate((596, 640)):
            for _j in range(9):
                dx = 20 + _j * 150
                PA.fill_rect(PA.img_of(d), [dx, _ry, dx + 78, _ry + 9],
                             (198, 198, 194), seed=866 + _i * 9 + _j,
                             value=0.05)
        for _i, _gx in enumerate((150, 980)):
            for _j in range(6):
                PA.fill_rect(PA.img_of(d), [_gx + _j * 20, 686, _gx + _j * 20 + 13,
                                            712], (60, 60, 58),
                             seed=880 + _i * 6 + _j, value=0.06)
            PA.hand_stroke(d, [(_gx - 4, 684), (_gx + 124, 684),
                               (_gx + 124, 714), (_gx - 4, 714)], INK, 4,
                           closed=True, seed=886 + _i, wavelength=80.0)
        # Big trees standing ON the pavement, cropped by the top edge -- the
        # ordinary street trees. They sit IN FRONT of the facades now, at the
        # kerb, which is both correct for a street tree and what puts a soft
        # dark mass over the window grid -- without that, the facade reads as a
        # flat elevation. base_y is the pavement (470), not the old horizon
        # (300), because they are planted at the kerb now. Two sit in the gap
        # so they do not cover the shopfronts.
        for k, x in enumerate((70, 300, 1010, 1210)):
            _tree(d, x, 470, 300 - (k % 2) * 30, 810 + k)
        # Street lamps, one per block, cropped in. Each is a light source in
        # frame, and each throws a pool onto the sidewalk -- the pools are what
        # break up the pavement's setts.
        _lamp_post(d, 640, 470, 300, 893, arm=54)
        _lamp_post(d, 1180, 470, 280, 899, arm=-54)
    els.append(SC.stage(clock, 22, e_street, j=27))

    def e_queue(tile, fw, fh):
        # The visitor queue. 'standing' is the only narrow pose, so the line
        # stays a line and not a picket fence. Feet at 556, on the pavement
        # (470-560), and the x-run is set so the figures stand clear of the
        # lamp posts and the entrance gap -- memory resize-figure-check-neighbors:
        # at the old 200..1100 they stood on top of the new facades' shopfronts.
        for i in range(7):
            SC.fullbody(ImageDraw.Draw(tile), 176 + i * 118, 556,
                        300 - (i % 3) * 34, 'standing', 'neutral', 820 + i)
        # SNOW, not INK, despite this being the daylight stage. The label sits on
        # the dark road band -- fill_rect(tile, [0, 560, W, H], (86, 86, 88)) --
        # whose measured ring median luminance is 83.9, so INK (24, 24, 28) gave
        # a 3.52:1 label that reads as a smudge. Room39's INK is not T.INK, so
        # draw_label already takes this as non-INK and supplies a 4px keyline;
        # SNOW keeps that keyline and makes the FILL carry the contrast, which is
        # what the in-art SNOW labels above (NO RECORD, 'surface only') do.
        D.draw_label(tile, 'open to visitors', center=(640, 604), color=SNOW,
                     size=28)
    els.append(SC.layer(clock, 22, e_queue, j=23,
                        motion=SC.enter(clock, 22, dx=120, dur=0.50)))

    def e_entrance(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The leaf set into the low wall in the gap between the facades -- the
        # entrance is UNDRAWN as a gate, it is a dark slab in an ordinary wall,
        # which is the point: it gives no sign of what is behind it.
        PA.fill_rect(tile, [700, 300, 850, 466], (62, 66, 74), seed=830,
                     value=0.07)
        PA.hand_stroke(d, [(700, 300), (850, 300), (850, 466), (700, 466)],
                       INK, 6, closed=True, seed=831, wavelength=110.0)
        # a short line of people cut off by the right edge, on the pavement
        for i in range(3):
            SC.fullbody(d, 1030 + i * 118, 556, 280 - (i % 2) * 30,
                        'standing', 'neutral', 840 + i)
        PA.hand_stroke(d, [(900, 556), (W, 556)], RED, 7, closed=False,
                       seed=845, wavelength=160.0)
    els.append(SC.accrue(clock, 23, 27, e_entrance, kind='shape'))
    els.append(cap(23, 640, 690, size=32, fill=INK))

    def e_surface_only(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # A red rectangle laid over the entrance wall: the satellite image, and
        # the fact that it covers a surface and nothing more. Sized to the wall
        # in the gap so it sits ON the entrance rather than floating mid-street.
        PA.hand_stroke(d, [(560, 320), (900, 320), (900, 470), (560, 470)],
                       RED, 8, closed=True, seed=850, wavelength=150.0)
        D.draw_label(tile, 'surface only', center=(730, 500), color=SNOW,
                     size=28)
    els.append(SC.layer(clock, 24, e_surface_only, j=25))

    def e_fence(tile, fw, fh):
        # The palisade runs along the top of the low wall in the gap, cropping
        # off both edges -- so the fence is what you look ACROSS to see the
        # entrance, which is the whole sentence.
        _fence(ImageDraw.Draw(tile), -30, W + 30, 300, 118, 695,
               col=(154, 156, 152))
    els.append(SC.accrue(clock, 25, 27, e_fence, kind='shape'))

    def e_bus_stop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # A bus shelter on the road side of the pavement, with a bench, a
        # timetable panel and a lit sign -- the object that makes the street
        # ordinary and, incidentally, the only 3-D-ish silhouette on it.
        PA.hand_stroke(d, [(150, 560), (150, 380)], (96, 100, 106), 9,
                       closed=False, seed=860, wavelength=60.0)
        PA.hand_stroke(d, [(250, 560), (250, 380)], (96, 100, 106), 9,
                       closed=False, seed=861, wavelength=60.0)
        # the glazed back and side
        PA.fill_rect(tile, [150, 380, 252, 560], (96, 122, 148), seed=862,
                     value=0.05)
        PA.hand_stroke(d, [(150, 380), (252, 380), (252, 560), (150, 560)],
                       INK, 5, closed=True, seed=863, wavelength=80.0)
        PA.hand_stroke(d, [(201, 380), (201, 560)], INK, 4, closed=False,
                       seed=864, wavelength=70.0)
        # the roof and its fascia
        PA.fill_poly(PA.img_of(d), [(132, 356), (286, 356), (300, 380),
                                    (120, 380)], (108, 112, 118), seed=865,
                     value=0.07)
        PA.hand_stroke(d, [(132, 356), (286, 356), (300, 380), (120, 380)],
                       INK, 5, closed=True, seed=866, wavelength=70.0)
        # the bench, in front of the glazing
        PA.fill_rect(PA.img_of(d), [164, 500, 246, 514], (128, 96, 68),
                     seed=867, value=0.08)
        PA.hand_stroke(d, [(164, 500), (246, 500)], INK, 4, closed=False,
                       seed=868, wavelength=60.0)
        # the timetable panel
        PA.fill_rect(tile, [112, 404, 146, 470], (216, 210, 190), seed=869,
                     value=0.05)
        PA.hand_stroke(d, [(112, 404), (146, 404), (146, 470), (112, 470)],
                       INK, 4, closed=True, seed=870, wavelength=60.0)
        # the park sign on a post
        PA.hand_stroke(d, [(430, 560), (430, 424)], (84, 88, 94), 7,
                       closed=False, seed=871, wavelength=50.0)
        PA.fill_rect(tile, [402, 388, 470, 424], (72, 118, 150), seed=872,
                     value=0.05)
        PA.hand_stroke(d, [(402, 388), (470, 388), (470, 424), (402, 424)],
                       INK, 4, closed=True, seed=873, wavelength=60.0)
        _car(d, 820, 566, 240, 862)
        _car(d, -60, 640, 210, 866)
    els.append(SC.accrue(clock, 26, 27, e_bus_stop, kind='shape',
                         motion=SC.enter(clock, 26, dx=0, dy=-50, dur=0.50)))
    els.append(cap(26, 640, 700, size=32, fill=INK))

    # ===================================================================== #
    # STAGE F  b27-b29  "It ends at a set of steel doors. Rumour says they   #
    #                  open on a code. No code has ever been published."     #
    # 4.0s -- the shortest stage in the chapter, and deliberately so: three  #
    # beats, one door, one keypad.                                           #
    # ===================================================================== #
    def f_wall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE FLAT-VECTOR FIX, measured: b27 read tile_std 2.97 on nine
        # full-width single strokes -- 1280px of one colour per line, with
        # half the frame a single unmodulated fill. A running bond gives ~15
        # courses x ~15 individually valued bricks (the fortknox gold-slab
        # density) for the price of one loop, and the kerb + lamp + drain
        # crop the wall off the left edge so the composition is a PLACE the
        # viewer is standing in front of, not a flat backdrop.
        PA.fill_rect(tile, [0, 0, W, H], BRICK, seed=900, value=0.08)
        _brick_bond(d, -20, 0, W + 20, 556, 902, col=BRICK,
                    col_m=(146, 108, 88), mortar=(174, 170, 160),
                    bw=104, bh=36, w=3)
        # pilasters -- vertical breaks so the wall has a rhythm, not a field
        for _i, _px in enumerate((96, 402, 1108)):
            PA.fill_rect(PA.img_of(d), [_px, 74, _px + 74, 560],
                         (150, 112, 92), seed=906 + _i, value=0.09)
            PA.hand_stroke(d, [(_px, 74), (_px + 74, 74), (_px + 74, 560),
                               (_px, 560)], INK, 5, closed=True,
                           seed=910 + _i, wavelength=120.0, vary=0.35)
            for _j in range(4):
                PA.fill_rect(PA.img_of(d),
                             [_px + 12, 140 + _j * 96, _px + 62, 168 + _j * 96],
                             (128, 94, 78), seed=916 + _i * 4 + _j, value=0.08)
        # kerb + pavement -- the wall has to stand ON something
        PA.fill_rect(tile, [0, 556, W, 596], (150, 146, 138), seed=920,
                     value=0.07)
        PA.hand_stroke(d, [(0, 558), (W, 558)], INK, 5, closed=False,
                       seed=921, wavelength=200.0)
        PA.fill_rect(tile, [0, 596, W, H], (92, 92, 90), seed=922,
                     value=0.06)
        for _i, _sx in enumerate((0, 168, 336, 504, 672, 840, 1008, 1176)):
            PA.hand_stroke(d, [(_sx, 596), (_sx - 46, H)], (66, 66, 66), 3,
                           closed=False, seed=924 + _i, wavelength=110.0)
        PA.hand_stroke(d, [(0, 664), (W, 664)], (70, 70, 70), 3, closed=False,
                       seed=932, wavelength=220.0)
        # gooseneck lamp cropped in at the left -- a light source in frame
        PA.hand_stroke(d, [(-10, 556), (34, 470), (96, 430), (188, 424)],
                       INK, 9, closed=False, seed=934, wavelength=130.0,
                       vary=0.3)
        PA.fill_poly(PA.img_of(d), [(168, 396), (222, 396), (236, 436),
                                    (154, 436)], (58, 58, 60), seed=935,
                     value=0.06)
        PA.hand_stroke(d, [(168, 396), (222, 396), (236, 436), (154, 436)],
                       INK, 5, closed=True, seed=936, wavelength=70.0)
        # The cone MONOTONICALLY widens. The first pass pinched it to a waist
        # at y=520 and it rendered as a pale bowtie on the brick, not a wash.
        PA.fill_poly(PA.img_of(d), [(156, 438), (234, 438), (318, 652),
                                    (62, 652)], LAMP, seed=937, value=0.05)
        # drain grating at the wall foot, clear of the cone -- small repeated
        # shapes, cheap density
        for _i in range(7):
            PA.fill_rect(PA.img_of(d), [1126 + _i * 21, 566, 1126 + _i * 21 + 13,
                                        592], (58, 58, 56), seed=938 + _i,
                         value=0.06)
        PA.hand_stroke(d, [(1122, 564), (1276, 564), (1276, 594), (1122, 594)],
                       INK, 4, closed=True, seed=946, wavelength=80.0)
    els.append(SC.stage(clock, 27, f_wall, j=30))

    def f_doors(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE FLAT-VECTOR FIX, measured: b28 read 3.09 on one smooth steel
        # rectangle. Two leaves split by one seam is still two smooth
        # rectangles, so the leaf is now articulated the way the b37 leaf
        # is -- jamb stiles, three hinge blocks, a rivet course top and
        # bottom, and raised louvre plates -- and it is scaled to fill the
        # frame between its own jambs instead of floating in the brick.
        PA.fill_rect(tile, [470, 150, 1090, 690], (74, 78, 84), seed=929,
                     value=0.07)
        PA.hand_stroke(d, [(470, 150), (1090, 150), (1090, 690), (470, 690)],
                       INK, 11, closed=True, seed=928, wavelength=170.0,
                       vary=0.3)
        PA.fill_rect(tile, [500, 178, 1062, 664], STEEL, seed=930, value=0.08)
        PA.hand_stroke(d, [(500, 178), (1062, 178), (1062, 664), (500, 664)],
                       INK, 8, closed=True, seed=931, wavelength=140.0)
        PA.hand_stroke(d, [(781, 178), (781, 664)], INK, 7, closed=False,
                       seed=932, wavelength=140.0)
        # jamb stiles -- a lit edge and a dark edge on each stile, so the
        # leaf reads as folded steel rather than a fill
        for _i, _sx in enumerate((500, 743, 781, 1024)):
            PA.fill_rect(PA.img_of(d), [_sx, 178, _sx + 38, 664],
                         (136, 146, 158), seed=960 + _i, value=0.08)
            PA.hand_stroke(d, [(_sx, 178), (_sx, 664)], STEEL_D, 5,
                           closed=False, seed=964 + _i, wavelength=200.0)
            PA.hand_stroke(d, [(_sx + 38, 178), (_sx + 38, 664)], (170, 180,
                                                                 192), 3,
                           closed=False, seed=968 + _i, wavelength=200.0)
        # Left leaf carries the keypad, so it gets raised side ribs instead of
        # plates -- the keypad itself is the plate there.
        for _i, _rx in enumerate((504, 738)):
            PA.fill_rect(PA.img_of(d), [_rx, 186, _rx + 34, 656],
                         (136, 146, 158), seed=972 + _i, value=0.08)
            PA.hand_stroke(d, [(_rx, 186), (_rx, 656)], STEEL_D, 5,
                           closed=False, seed=976 + _i, wavelength=200.0)
            for _j in range(6):
                PA.fill_rect(PA.img_of(d), [_rx + 8, 226 + _j * 68,
                                            _rx + 26, 244 + _j * 68],
                             (86, 92, 102), seed=980 + _i * 6 + _j,
                             value=0.06)
        # Right leaf carries the lock wheel, so its plates flank the wheel
        # rather than stacking under it. First pass ran FOUR plates down the
        # whole leaf and the wheel landed on top of two of them.
        for _i, _ly in enumerate((196, 546)):
            PA.fill_rect(PA.img_of(d), [820, _ly, 1042, _ly + 100],
                         (104, 112, 124), seed=990 + _i, value=0.08)
            PA.hand_stroke(d, [(820, _ly), (1042, _ly), (1042, _ly + 100),
                               (820, _ly + 100)], INK, 5, closed=True,
                           seed=994 + _i, wavelength=90.0)
            for _m in range(4):
                PA.hand_stroke(d, [(832, _ly + 18 + _m * 22),
                                   (1030, _ly + 18 + _m * 22)], (70, 76, 86),
                               4, closed=False, seed=998 + _i * 4 + _m,
                               wavelength=70.0)
        _rivet_row(d, 512, 190, 1050, 190, 11, 1010)
        _rivet_row(d, 512, 652, 1050, 652, 11, 1011)
        _lock_wheel(d, 930, 420, 100, 933)
    els.append(SC.accrue(clock, 27, 30, f_doors,
                         motion=SC.enter(clock, 27, dx=90, dur=0.50)))

    def f_keypad(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _keypad(d, 620, 400, 260, 340, 768, cols=3, rows=4)
        # Conduit + junction box, run up the RIGHT of the panel into the brick.
        # The first pass dropped a pale wedge straight over the door's louvre
        # plates and read as a rendering fault rather than as hardware.
        PA.hand_stroke(d, [(1010, 470), (1010, 150), (940, 150)], (86, 90, 96),
                       8, closed=False, seed=940, wavelength=70.0)
        PA.fill_rect(PA.img_of(d), [944, 118, 1078, 178], (216, 208, 168),
                     seed=941, value=0.05)
        PA.hand_stroke(d, [(944, 118), (1078, 118), (1078, 178), (944, 178)],
                       INK, 5, closed=True, seed=942, wavelength=70.0)
        for _i, _sx in enumerate((968, 1000, 1032)):
            PA.hand_stroke(d, [(_sx, 134), (_sx, 162)], (86, 90, 96), 6,
                           closed=False, seed=943 + _i, wavelength=40.0)
    els.append(SC.accrue(clock, 28, 30, f_keypad,
                         motion=SC.enter(clock, 28, dx=0, dy=-40, dur=0.45)))

    def f_presenter(tile, fw, fh):
        # Cropped into the LEFT edge: he is standing at the doors, close to
        # the viewer, looking at a keypad that never got published.
        SC.closeup(ImageDraw.Draw(tile), 150, 400, 200, 'deadpan', 950)
    els.append(SC.accrue(clock, 29, 30, f_presenter, kind='character'))
    els.append(cap(29, 780, 690, size=32, fill=INK))

    # ===================================================================== #
    # STAGE G  b30-b37  "The whole site is a system... Under the park, a    #
    #                  red light waits... The door is still shut, and still   #
    #                  waiting."  18.3s -- the longest stage.                  #
    # A NIGHT cross-section of the park: the surface ringed by sensors at the #
    # top, the chamber at the bottom, and the red light the only colour.      #
    # ===================================================================== #
    def g_park_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (24, 30, 44), seed=1000, value=0.07)
        SC.title_backdrop(tile, 1951, col=(96, 98, 110))
        PA.fill_rect(tile, [0, 240, W, 300], PARK_D, seed=1001, value=0.06)
        PA.hand_stroke(d, [(0, 242), (W, 240)], (14, 18, 26), 6,
                       closed=False, seed=1002, wavelength=220.0)
        # dark trees along the surface line; v1 uses height 170 for the same
        # register, and the cold crown colour keeps them in the night palette.
        for k, x in enumerate((150, 430, 760, 1090)):
            _tree(d, x, 244, 170, 1010 + k, col=(38, 62, 44))
        # Night strata. _strata's 4th arg is `cols`, a LIST of band colours --
        # v1's warm clay defaults read as daylight soil on a night card, so
        # the bands are pushed cold here to stay inside the night register.
        _strata(d, 330, 372, 416,
                cols=[(44, 40, 46), (38, 36, 42), (50, 46, 52)], n=3)
        # THE CHAMBER is the subject of this stage, so it is scaled to fill
        # the lower frame and cropped at the sides -- the first pass drew it as
        # a small faint trapezoid and the bottom two-thirds of every frame read
        # as empty dark field (the frame-fill-subject-scale defect). Now it is
        # a lit concrete room occupying the bottom 60% and running off both
        # edges, so the frame admits the system is bigger than the picture.
        chamber = [(150, 470), (1130, 462), (1280, 720), (0, 720)]
        PA.fill_poly(PA.img_of(d), chamber, (74, 78, 90), seed=1013,
                     value=0.08)
        # a warmer pool inside the chamber so it reads as an interior, not a
        # slab -- without this the fill is a flat grey shape on dark ground
        PA.fill_poly(PA.img_of(d),
                     [(430, 500), (900, 494), (1010, 720), (330, 720)],
                     (104, 104, 112), seed=1016, value=0.06)
        PA.hand_stroke(d, [(150, 470), (1130, 462)], (128, 132, 144), 8,
                       closed=False, seed=1014, wavelength=180.0)
        PA.hand_stroke(d, [(1130, 462), (1280, 720)], (108, 112, 124), 7,
                       closed=False, seed=1015, wavelength=180.0)
        PA.hand_stroke(d, [(150, 470), (0, 720)], (108, 112, 124), 7,
                       closed=False, seed=1017, wavelength=180.0)
        # a heavy concrete lintel so the chamber has a readable top edge
        PA.fill_rect(tile, [120, 448, 1160, 486], (96, 100, 112), seed=1018,
                     value=0.07)
        PA.hand_stroke(d, [(120, 486), (1160, 486)], INK, 6, closed=False,
                       seed=1019, wavelength=200.0)
        # ---- CHAMBER INTERIOR (the flat-vector fix) ------------------------ #
        # The chamber was scaled up to fill the lower 60% and it stayed flat,
        # because filling a frame with one smooth trapezoid is the defect the
        # frame-fill rule warns about, not the cure for it. Stage D's cure
        # applies here too, in the cold night register: rib the side walls,
        # slab the floor, run the services. The chamber now holds the eye.
        _rib_wall(tile, d, 60, 470, 486, 690, 5, 1020, col=(66, 70, 80),
                  col_dk=(44, 47, 55), w=5, taper=0.08, y_top_far=482)
        _rib_wall(tile, d, 810, 1240, 482, 690, 5, 1030, col=(66, 70, 80),
                  col_dk=(44, 47, 55), w=5, taper=0.08, y_top_far=482)
        _slab_floor(tile, d, 500, H, 420, 520, 640, 800, n=6, slabs=5,
                    col=(58, 61, 71), col_lit=(84, 88, 100), joint=(38, 40, 48),
                    w=4)
        _cable_tray(d, [(120, 500), (1180, 494)], 1040, col=(70, 74, 86), w=7,
                    rungs=12, sag=9)
        _crate_stack(tile, d, 210, 660, 1050, n=2, w_=92, h_=52)
        _crate_stack(tile, d, 940, 654, 1060, n=2, w_=88, h_=50)
    els.append(SC.stage(clock, 30, g_park_night, j=38))

    def g_system(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(6):
            x = 130 + k * 200
            _sensor(d, x, 214, 26, 1020 + k)
        PA.hand_stroke(d, [(130, 190), (1130, 190)], RED, 7, closed=False,
                       seed=1030, wavelength=240.0)
        D.draw_label(tile, 'one system', center=(640, 150), color=SNOW,
                     size=28)
    els.append(SC.layer(clock, 30, g_system, j=32))

    def g_ring(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(14):
            x = 70 + k * 88
            _sensor(d, x, 216, 20, 1040 + k)
    els.append(SC.accrue(clock, 31, 34, g_ring, kind='shape'))

    def g_listening(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The hero sensor, big enough to be the subject of the frame.
        _sensor(d, 640, 200, 44, 1060, lit=True)
        for k, r in enumerate((70, 120, 170)):
            arc = [(640 + r * math.cos(a), 200 + r * math.sin(a) * 0.55)
                   for a in [math.pi * (1.06 + 0.88 * j / 20.0)
                             for j in range(21)]]
            PA.hand_stroke(d, arc, RED, 6, seed=1061 + k, wavelength=110.0)
        D.draw_label(tile, 'still listening', center=(640, 340), color=SNOW,
                     size=26)
    els.append(SC.layer(clock, 32, g_listening, j=33))
    els.append(cap(32, 640, 664, size=30, fill=SNOW))

    def g_decayed(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k, x in enumerate((300, 640, 980)):
            PA.fill_rect(tile, [x - 54, 170, x + 54, 214], (54, 56, 62),
                         seed=1070 + k, value=0.07)
            PA.hand_stroke(d, [(x - 54, 170), (x + 54, 170)], (34, 36, 42),
                           5, closed=False, seed=1073 + k, wavelength=90.0)
        D.draw_label(tile, 'still running', center=(640, 130), color=SNOW,
                     size=26)
    els.append(SC.layer(clock, 33, g_decayed, j=34))

    def g_red_light(tile, fw, fh):
        # The red light IS the subject and the hero of the chapter's last act,
        # so it is large and centred in the chamber with a stalk down to the
        # chamber floor. The first pass drew a 36px dot off to the left with a
        # small label; at full res it read as a stray pixel in an empty field.
        d = ImageDraw.Draw(tile)
        # stalk from the chamber floor up to the lamp head at (640, 560)
        PA.hand_stroke(d, [(640, 700), (640, 566)], (86, 90, 100), 11,
                       closed=False, seed=1080, wavelength=60.0)
        # a dim halo so the lamp reads as emitting
        for k, r in enumerate((120, 170, 220)):
            PA.hand_stroke(d,
                           [(640 + r * math.cos(a), 560 + r * math.sin(a) * 0.9)
                            for a in [(-1.6 + 3.2 * j / 22.0)
                                      for j in range(23)]],
                           (120, 34, 30), 8, seed=1085 + k, wavelength=120.0)
        # the lamp head itself
        d.ellipse([604, 524, 676, 596], fill=RED)
        d.ellipse([620, 540, 660, 580], fill=(255, 150, 140))
        for k, r in enumerate((150, 210, 270)):
            PA.hand_stroke(d,
                           [(640 + r * math.cos(a), 560 + r * math.sin(a))
                            for a in [(-1.5 + 3.0 * j / 22.0)
                                      for j in range(23)]],
                           RED, 6, seed=1081 + k, wavelength=110.0)
        # NO drawn label here: the b34 caption already says "Under the park, a
        # red light waits." and printing "the red light" as well was the same
        # words twice on one frame.
    els.append(SC.accrue(clock, 34, 38, g_red_light, kind='shape',
                         motion=SC.enter(clock, 34, dx=0, dy=-36, dur=0.45)))
    els.append(cap(34, 640, 660, size=30, fill=SNOW))

    def g_dossier(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [420, 440, 860, 570], (188, 184, 164), seed=1090,
                     value=0.06)
        PA.hand_stroke(d, [(420, 440), (860, 440), (860, 570), (420, 570)],
                       INK, 5, closed=True, seed=1091, wavelength=110.0)
        PA.hand_stroke(d, [(450, 492), (740, 492)], INK, 4, closed=False,
                       seed=1092, wavelength=140.0)
        D.draw_label(tile, 'left blank', center=(640, 610), color=SNOW,
                     size=26)
    els.append(SC.layer(clock, 35, g_dossier, j=36))

    def g_chair(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Moved off centre. At 480-700 the chair sat directly under the
        # 'no one in decades' label AND directly under the presenter, so the
        # beat read as a person sitting in it -- the exact opposite of the
        # line. Left of centre, it reads as an empty chair with someone
        # standing well away from it.
        PA.fill_rect(tile, [386, 496, 606, 572], (66, 70, 78), seed=1100,
                     value=0.07)
        PA.hand_stroke(d, [(386, 496), (606, 496)], (96, 98, 110), 6,
                       closed=False, seed=1101, wavelength=90.0)
        PA.hand_stroke(d, [(386, 496), (386, 420), (430, 420)], (96, 98, 110),
                       6, closed=False, seed=1102, wavelength=90.0)
        for _i, _lx in enumerate((410, 470, 530, 590)):
            PA.hand_stroke(d, [(_lx, 500), (_lx, 540)], (48, 51, 59), 4,
                           closed=False, seed=1104 + _i, wavelength=60.0)
        D.draw_label(tile, 'no one in decades', center=(640, 646), color=SNOW,
                     size=26)
    els.append(SC.layer(clock, 36, g_chair, j=37))

    def g_presenter(tile, fw, fh):
        # The FIRST character in this stage. b30-b37 is eight beats -- a third
        # of the chapter and the whole night cross-section -- with no presenter
        # at all, so every one of those frames was pure diagram. He arrives on
        # the "no one in decades" beat, which is the emptiest line in the
        # chapter and the one a surrogate is for.
        # Stand-off at the right, feet on the chamber's near floor course, well
        # clear of the empty chair -- memory resize-figure-check-neighbors:
        # the first pass at x=1030 put him astride the chair and the beat lost
        # its meaning. Cream because the chamber is dark; 'shrug' because the
        # line is a shrug of the room.
        SC.fullbody(ImageDraw.Draw(tile), 1092, 700, 400, 'shrug',
                    'deadpan', 1112, ink=(238, 236, 228))
    els.append(SC.accrue(clock, 36, 38, g_presenter, kind='character',
                         motion=SC.enter(clock, 36, dx=90, dy=0, dur=0.50)))

    def g_final_door(tile, fw, fh):
        # The finale. One door filling the frame, the way the chapter opened
        # on one door filling the frame at b13 -- the bookend is deliberate.
        d = ImageDraw.Draw(tile)
        # FULL BLEED. At 980 wide centred on 560 the leaf stopped at x=1050 and
        # a 130px strip of the night cross-section showed down the right side --
        # a tree, the park band and the red light, all of them from b34. The
        # finale was showing the previous act. Widened to 1420 so the leaf runs
        # off both edges and the strip is gone.
        _blast_door(d, 620, 360, 1420, 1000, 1023, wheel=True, plates=5,
                    lamp=False, seam_floor=96)
        d.ellipse([1080, 300, 1116, 336], fill=RED)
        PA.fill_rect(tile, [1160, -40, W + 60, 760], (66, 70, 78), seed=1110,
                     value=0.08)
        PA.hand_stroke(d, [(1160, -40), (1160, 760)], INK, 13, closed=False,
                       seed=1111, wavelength=210.0)
        D.draw_label(tile, 'still shut', center=(560, 646), color=RED,
                     size=34)
        # ---- LEAF STRUCTURE (the flat-vector fix) -------------------------- #
        # Four plate courses across 1280px is four big smooth shapes, which is
        # the flat-vector failure wearing plate seams as a disguise. A real
        # blast leaf is stiffened: vertical ribs down every stile, hinge
        # blocks up the left edge, dog-bolt bosses across the meeting stile,
        # and a hazard chevron band at head height.
        for _i, _rx in enumerate((146, 262, 378, 862, 978, 1094)):
            PA.fill_rect(PA.img_of(d), [_rx - 17, -40, _rx + 17, 760],
                         (134, 146, 160), seed=1120 + _i, value=0.08)
            PA.hand_stroke(d, [(_rx - 17, -40), (_rx - 17, 760)], STEEL_D, 5,
                           closed=False, seed=1130 + _i, wavelength=200.0)
            PA.hand_stroke(d, [(_rx + 17, -40), (_rx + 17, 760)], (176, 186, 198),
                           3, closed=False, seed=1140 + _i, wavelength=200.0)
        for _i, _hy in enumerate((196, 300, 480, 660)):
            PA.fill_rect(PA.img_of(d), [-40, _hy - 26, 122, _hy + 26],
                         (120, 132, 146), seed=1150 + _i, value=0.08)
            PA.hand_stroke(d, [(-40, _hy - 26), (122, _hy - 26)], STEEL_D, 5,
                           closed=False, seed=1160 + _i, wavelength=140.0)
            for _j in range(3):
                PA.fill_poly(PA.img_of(d),
                             PA.ellipse_pts(18 + _j * 36, _hy, 9, 9, n=10),
                             (176, 184, 194), seed=1170 + _i * 3 + _j,
                             value=0.05)
        # Hazard chevrons on the head beam: the one saturated note on an
        # all-steel frame. Placed at y 86-128 rather than across the middle --
        # the first pass ran them at 214 and they cut straight through the lock
        # wheel, which is the one thing on this leaf the eye must land on.
        for _i in range(11):
            _cx0 = 106 + _i * 76
            PA.fill_poly(PA.img_of(d),
                         [(_cx0, 86), (_cx0 + 40, 86), (_cx0 + 76, 128),
                          (_cx0 + 36, 128)], (46, 44, 48), seed=1190 + _i,
                         value=0.06)
            PA.fill_poly(PA.img_of(d),
                         [(_cx0 + 40, 86), (_cx0 + 76, 86), (_cx0 + 112, 128),
                          (_cx0 + 76, 128)], (188, 152, 44), seed=1201 + _i,
                         value=0.07)
        PA.hand_stroke(d, [(100, 80), (946, 80)], INK, 6, closed=False,
                       seed=1215, wavelength=180.0)
        PA.hand_stroke(d, [(100, 134), (946, 134)], INK, 6, closed=False,
                       seed=1216, wavelength=180.0)
    els.append(SC.accrue(clock, 37, 38, g_final_door, kind='shape'))
    els.append(cap(37, 640, 690, size=32, fill=INK))

    return SC.finish(els, TITLE, clock, title_seed=39)