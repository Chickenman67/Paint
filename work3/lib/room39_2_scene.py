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
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (86, 88, 96), seed=600, value=0.06)
        # the dark throat at the far end -- the corridor's destination
        PA.fill_rect(tile, [VX - 40, VY - 40, VX + 40, VY + 40], DARKER,
                     seed=601, value=0.08)
        # eight ribs marching in from the near edge to the throat, each a
        # trapezoid. Near ribs are tall and wide; far ribs collapse onto the
        # vanishing point. This is the depth the first pass was missing.
        for k in range(8):
            t = k / 7.0                       # 0 = nearest, 1 = at the throat
            half = 1180 * (1.0 - t) ** 1.35 + 44
            y0 = 700 - 360 * (1.0 - t) ** 0.9  # top edge of the rib at the near side
            y1 = -40 + 380 * (1.0 - t) ** 0.9  # bottom edge (negative = above frame)
            _rib(d, VY - (VY - y1) * 0.0, y0, 44, half,
                 (100, 102, 112) if k % 2 == 0 else (112, 114, 124), 610 + k * 4,
                 w=5 if k < 5 else 4)
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
        # "Floor to ceiling, plate over plate." TWO lead leaves swing in from
        # the LEFT and cover the left third of the corridor -- you still see
        # the ribs and the far door down the right. The first pass drew nine
        # full-height leaves at a 344px pitch, which tiled edge to edge and
        # buried the entire corridor behind a flat striped wall.
        d = ImageDraw.Draw(tile)
        for k, (x0, wleaf) in enumerate(((-40, 300), (280, 260))):
            leaf = [(x0, -40), (x0 + wleaf, -40), (x0 + wleaf, H + 40),
                    (x0, H + 40)]
            PA.fill_poly(PA.img_of(d), leaf,
                         LEAD_L if k == 0 else LEAD, seed=630 + k,
                         value=0.07)
            PA.hand_stroke(d, [(x0, -40), (x0, H + 40)], INK, 6,
                           closed=False, seed=640 + k, wavelength=170.0)
            PA.hand_stroke(d, [(x0 + wleaf, -40), (x0 + wleaf, H + 40)],
                           INK, 5, closed=False, seed=650 + k,
                           wavelength=170.0)
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
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 204, 208), seed=800,
                     value=0.04)
        PA.fill_rect(tile, [0, 300, W, 470], CONCRETE, seed=801, value=0.07)
        PA.hand_stroke(d, [(0, 302), (W, 300)], INK, 7, closed=False,
                       seed=802, wavelength=220.0)
        PA.fill_rect(tile, [0, 470, W, 560], (150, 150, 148), seed=803,
                     value=0.05)
        PA.fill_rect(tile, [0, 560, W, H], (86, 86, 88), seed=804, value=0.06)
        PA.hand_stroke(d, [(0, 560), (W, 562)], (232, 232, 228), 8,
                       closed=False, seed=805, wavelength=220.0)
        # Big trees cropped by the top edge -- the ordinary street trees.
        # _tree's 4th arg is a HEIGHT in pixels (v1 uses 150-420), not a scale.
        for k, x in enumerate((90, 300, 980, 1180)):
            _tree(d, x, 302, 330, 810 + k)
    els.append(SC.stage(clock, 22, e_street, j=27))

    def e_queue(tile, fw, fh):
        # The v1 seven-figure visitor queue. 'standing' is the only narrow
        # pose, so the line stays a line and not a picket fence.
        for i in range(7):
            SC.fullbody(ImageDraw.Draw(tile), 200 + i * 150, 556,
                        335 - (i % 3) * 40, 'standing', 'neutral', 820 + i)
        # SNOW, not INK, despite this being the daylight stage. The label sits on
        # the dark road band at line 768 -- fill_rect(tile, [0, 560, W, H],
        # (86, 86, 88)) -- whose measured ring median luminance is 83.9, so
        # INK (24, 24, 28) gave a 3.52:1 label that reads as a smudge: 2074
        # pure-black keyline px + 1864 near-ink fill px and not one light pixel
        # in the letterforms. Room39's INK is not T.INK, so draw_label already
        # takes this as non-INK and supplies a 4px keyline; SNOW keeps that
        # keyline and makes the FILL carry the contrast, which is what the
        # in-art SNOW labels above (NO RECORD, and 'surface only' below) do.
        D.draw_label(tile, 'open to visitors', center=(640, 604), color=SNOW,
                     size=28)
    els.append(SC.layer(clock, 22, e_queue, j=23,
                        motion=SC.enter(clock, 22, dx=120, dur=0.50)))

    def e_entrance(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the leaf set into the facade, plus a short line of people cut off by
        # the right edge
        PA.fill_rect(tile, [880, 330, 1030, 462], (62, 66, 74), seed=830,
                     value=0.07)
        PA.hand_stroke(d, [(880, 330), (1030, 330), (1030, 462), (880, 462)],
                       INK, 6, closed=True, seed=831, wavelength=110.0)
        for i in range(3):
            SC.fullbody(d, 1100 + i * 120, 560, 300, 'standing', 'neutral',
                        840 + i)
        PA.hand_stroke(d, [(1050, 560), (W, 560)], RED, 7, closed=False,
                       seed=845, wavelength=160.0)
    els.append(SC.accrue(clock, 23, 27, e_entrance, kind='shape'))
    els.append(cap(23, 640, 690, size=32, fill=INK))

    def e_surface_only(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(240, 340), (900, 340), (900, 430), (240, 430)],
                       RED, 8, closed=True, seed=850, wavelength=150.0)
        D.draw_label(tile, 'surface only', center=(570, 486), color=SNOW,
                     size=28)
    els.append(SC.layer(clock, 24, e_surface_only, j=25))

    def e_fence(tile, fw, fh):
        _fence(ImageDraw.Draw(tile), -30, W + 30, 540, 150, 695,
               col=(154, 156, 152))
    els.append(SC.accrue(clock, 25, 27, e_fence, kind='shape'))

    def e_bus_stop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(150, 560), (150, 380)], (96, 100, 106), 9,
                       closed=False, seed=860, wavelength=60.0)
        PA.fill_rect(tile, [110, 360, 250, 400], (72, 118, 150), seed=861,
                     value=0.05)
        _car(d, 820, 566, 240, 862)
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
        PA.fill_rect(tile, [0, 0, W, H], BRICK, seed=900, value=0.08)
        for k in range(9):
            PA.hand_stroke(d, [(0, 40 + k * 62), (W, 40 + k * 62)],
                           CLAY_D, 4, closed=False, seed=902 + k,
                           wavelength=220.0)
        PA.fill_rect(tile, [0, 560, W, H], (92, 92, 90), seed=920,
                     value=0.06)
    els.append(SC.stage(clock, 27, f_wall, j=30))

    def f_doors(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [540, 220, 1010, 600], STEEL, seed=930, value=0.08)
        PA.hand_stroke(d, [(540, 220), (1010, 220), (1010, 600), (540, 600)],
                       INK, 8, closed=True, seed=931, wavelength=140.0)
        PA.hand_stroke(d, [(775, 220), (775, 600)], INK, 7, closed=False,
                       seed=932, wavelength=140.0)
        _lock_wheel(d, 660, 420, 90, 933)
    els.append(SC.accrue(clock, 27, 30, f_doors,
                         motion=SC.enter(clock, 27, dx=90, dur=0.50)))

    def f_keypad(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _keypad(d, 620, 400, 260, 340, 768, cols=3, rows=4)
        PA.hand_stroke(d, [(880, 300), (880, 220)], (86, 90, 96), 8,
                       closed=False, seed=940, wavelength=60.0)
        PA.fill_poly(PA.img_of(d),
                     [(880, 220), (880, 300), (1040, 340), (900, 300)],
                     (216, 208, 168), seed=941, value=0.05)
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
        PA.fill_rect(tile, [480, 520, 700, 596], (66, 70, 78), seed=1100,
                     value=0.07)
        PA.hand_stroke(d, [(480, 520), (700, 520)], (96, 98, 110), 6,
                       closed=False, seed=1101, wavelength=90.0)
        D.draw_label(tile, 'no one in decades', center=(640, 646), color=SNOW,
                     size=26)
    els.append(SC.layer(clock, 36, g_chair, j=37))

    def g_presenter(tile, fw, fh):
        # The FIRST character in this stage. b30-b37 is eight beats -- a third
        # of the chapter and the whole night cross-section -- with no presenter
        # at all, so every one of those frames was pure diagram. He arrives on
        # the "no one in decades" beat, which is the emptiest line in the
        # chapter and the one a surrogate is for.
        # Cropped into the RIGHT so he does not sit on the chair or the 'no one
        # in decades' label at (640,646); cream because the chamber is dark.
        # pose 'shrug' because the line is a shrug of the room.
        SC.fullbody(ImageDraw.Draw(tile), 1030, 660, 380, 'shrug',
                    'deadpan', 1112, ink=(238, 236, 228))
    els.append(SC.accrue(clock, 36, 38, g_presenter, kind='character',
                         motion=SC.enter(clock, 36, dx=90, dy=0, dur=0.50)))

    def g_final_door(tile, fw, fh):
        # The finale. One door filling the frame, the way the chapter opened
        # on one door filling the frame at b13 -- the bookend is deliberate.
        d = ImageDraw.Draw(tile)
        _blast_door(d, 560, 380, 980, 940, 1023, wheel=True, plates=4,
                    lamp=False, seam_floor=96)
        d.ellipse([1080, 300, 1116, 336], fill=RED)
        PA.fill_rect(tile, [1160, -40, W + 60, 760], (66, 70, 78), seed=1110,
                     value=0.08)
        PA.hand_stroke(d, [(1160, -40), (1160, 760)], INK, 13, closed=False,
                       seed=1111, wavelength=210.0)
        D.draw_label(tile, 'still shut', center=(560, 646), color=RED,
                     size=34)
    els.append(SC.accrue(clock, 37, 38, g_final_door, kind='shape'))
    els.append(cap(37, 640, 690, size=32, fill=INK))

    return SC.finish(els, TITLE, clock, title_seed=39)