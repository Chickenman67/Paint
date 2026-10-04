"""room39 scene -- Object 739, the sealed nuclear bunker under the Moscow Kremlin.

Chapter 9 of the bunker film. Narration is FINAL (audio.wav + beats.json) and
every card below is phrase-timed off it through scene_common.BeatClock.

ONE CARD PER BEAT, AND EVERY CARD PAINTS ITS OWN WHOLE FRAME. The chapter is 37
short sentences and beats.json gives each one an exact [start,end], so there is
nothing to guess. Each card function fills tile background-to-subject, which
makes it structurally impossible for one card's art to survive into the next.

THE HERO IS THE DOOR (b10-b13). The narration names it four times and says of
b13 "one closed door, filling the whole frame", so the steel leaf is drawn past
all four frame edges with the wheel lock at the centre. Never parked inside an
empty field.

FRAME-FILL IS THE PROJECT'S #1 RECURRING DEFECT, so every card here either puts
its subject past a frame edge or crops a secondary body at one. A small subject
centred in a large empty page is the failure mode this file is written against.

PALETTE. Cold, heavy, concrete: grey concrete, steel blue, lead grey, one dark
green for the park, and a single red spent only on the things the narration
calls live -- the red lamp, the big button, the lit sensor. Interiors are dark
because they are underground.

CADENCE. Still-dominant, one hard cut per sentence (37 cuts in 89s). No element
carries a motion track: engine3's `motion` is a list of (t,x,y,scale,rot)
keyframes rather than a preset name, and the reference measures 96% still with
hard cuts, so "still" is the faithful choice and also the safe one. The b32
"still listening" beat sells itself through the lit lamp and the radiating
sound rings rather than through animation.

Run:  python lib/room39_scene.py --preview
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

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'room39'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Object 739'

# The title band carries an intentional lit concrete course on the dark cards,
# so band_intrusions exempts exactly those rows (see its TITLE_BACKDROP
# handling). Only the part inside the band is declared: rows below it are
# ordinary art and must still be checked.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# COLD + HEAVY + CONCRETE. One accent family; red is rationed.
INK = SC.INK
CONCRETE = (170, 170, 164)        # the mass of the thing
CONCRETE_L = (206, 205, 197)      # lit concrete face
CONCRETE_D = (124, 126, 126)      # shadowed concrete
STEEL = (132, 146, 162)           # steel blue
STEEL_D = (84, 96, 114)           # steel in shadow
LEAD = (96, 100, 112)             # lead plate lining
LEAD_L = (128, 132, 146)
CLAY = (146, 122, 96)             # Moscow subsoil
CLAY_D = (112, 92, 72)
WATER = (84, 122, 142)            # standing groundwater
PARK = (72, 112, 74)              # dark green, the small park
PARK_D = (54, 86, 58)
RED = (198, 46, 42)               # THE one accent: live things only
DARK = (36, 38, 46)               # interior dark
DARKER = (23, 25, 31)
LAMP = (240, 202, 142)            # the one warm note: a bulb still working
SNOW = (238, 238, 232)
PAPERW = (216, 210, 196)
BRICK = (150, 118, 100)

HZ = int(H * 0.68)                # horizon / street line for exterior cards

C3 = SC.C3                          # the character primitive module


def _figure(d, x, feet_y, h, pose='standing', expression='neutral', seed=0,
            ink=(238, 232, 214)):
    """A full-body figure whose STROKES ARE CREAM, for dark interiors.

    character3 draws the body in near-black by default. On a dark interior
    card that makes the figure vanish into the background -- it reads as a
    smudge, not a person. The project's style canon is explicit that the
    character is CREAM on dark/space backgrounds, so this forwards a cream ink
    to the same primitive scene_common.fullbody() wraps. On light exteriors,
    use SC.fullbody (black on paper is correct there).
    """
    C3.draw_character(PA.img_of(d), x, feet_y, h, pose=pose,
                       expression=expression, seed=seed, ink=ink)


# ---------------------------------------------------------------------------
# backgrounds
# ---------------------------------------------------------------------------

def _sky(tile, seed, sky=SNOW, ground=None, hz=HZ):
    """Full-frame exterior ground. Call at the TOP of every exterior card.

    Two OVERLAPPING fills, never two abutting rects: fill_rect wobbles each of
    its own edges on its own seed, so abutting rects leave a pale seam where
    their wobbles disagree. Sky over the WHOLE frame, ground on top starting
    above the nominal horizon -- the horizon becomes the single wobbled edge.
    """
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    if ground is not None:
        PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


def _night(tile, seed, sky=(34, 40, 54), ground=(26, 30, 40)):
    _sky(tile, seed, sky=sky, ground=ground, hz=int(H * 0.70))


def _dark_bg(tile, seed, col=DARK, floor=None):
    """A full-frame underground interior. `floor` is the y of the floor line."""
    PA.fill_rect(tile, [0, 0, W, H], col, seed=seed, value=0.08)
    if floor is not None:
        PA.fill_rect(tile, [0, floor, W, H], DARKER, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


def _soil_bg(tile, seed, top_col=CLAY, hz=250, water_y=None):
    """A cross-section of Moscow ground: clay bands, optionally water below."""
    PA.fill_rect(tile, [0, 0, W, hz], (168, 176, 180), seed=seed, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], top_col, seed=seed + 1, value=0.09)
    if water_y is not None:
        PA.fill_rect(tile, [0, water_y - 6, W, H], WATER, seed=seed + 7,
                     value=0.08)
    PA.paper_overlay(tile, seed=seed + 2)


def _strata(d, seed, y0, y1, cols=None, n=4, x0=-30, x1=W + 30):
    """Horizontal clay bands across a cross-section, each a wobbled ribbon."""
    cols = cols or [CLAY, CLAY_D, (158, 132, 104), (126, 106, 84)]
    for k in range(n):
        t = k / float(n)
        yy = y0 + (y1 - y0) * t
        h = (y1 - y0) / float(n) * 0.62
        pts = [(x0, yy), (x1, yy - 6), (x1, yy + h), (x0, yy + h + 5)]
        PA.fill_poly(PA.img_of(d), pts, cols[k % len(cols)], seed=seed + k,
                     value=0.08)
        PA.hand_stroke(d, [(x0, yy), (x1, yy - 6)], (108, 100, 88), 3,
                       closed=False, seed=seed + 20 + k, wavelength=170.0,
                       vary=0.25)


# ---------------------------------------------------------------------------
# the steel door -- the hero of the chapter
# ---------------------------------------------------------------------------

def _blast_door(d, cx, cy, w, h, seed, wheel=True, plates=4, lamp=False,
                seam_floor=None):
    """A armoured steel door leaf, drawn PAST the frame edges.

    Frame-fill is the whole point of this helper: callers pass w/h that run off
    the left, right, top or bottom edge, so the leaf always reads as bigger than
    the picture. `plates` lays the horizontal plate seams across it, `wheel`
    hangs the lock wheel at the centre, `lamp` puts the one red live indicator
    beside it.

    `seam_floor` stops the lit/shadowed face split at a y. It exists for the
    finale, whose leaf is cropped by the top edge so the seam ran the full
    height of the door -- and therefore the full height of the title band,
    straight through the title. The two face FILLS still meet above the floor,
    so the split stays readable; only the drawn line stops short.
    """
    img = PA.img_of(d)
    body = [(cx - w / 2.0, cy - h / 2.0), (cx + w / 2.0, cy - h / 2.0 - 5),
            (cx + w / 2.0, cy + h / 2.0), (cx - w / 2.0, cy + h / 2.0 + 6)]
    PA.fill_poly(img, body, STEEL, seed=seed, value=0.09)
    PA.hand_stroke(d, body, INK, 9, closed=True, seed=seed + 1, wavelength=200.0)

    # a lit left face and a shadowed right face, split down a vertical seam
    seam = cx + w * 0.04
    lit = [(cx - w / 2.0, cy - h / 2.0), (seam, cy - h / 2.0 - 3),
           (seam, cy + h / 2.0 + 3), (cx - w / 2.0, cy + h / 2.0 + 6)]
    PA.fill_poly(img, lit, (150, 162, 176), seed=seed + 2, value=0.07)
    seam_top = cy - h / 2.0 - 3
    if seam_floor is not None:
        seam_top = max(seam_top, seam_floor)
    PA.hand_stroke(d, [(seam, seam_top), (seam, cy + h / 2.0 + 3)],
                   STEEL_D, 5, closed=False, seed=seed + 3, wavelength=140.0)

    # horizontal plate seams -- the leaf reads as plate, not as a slab
    for k in range(1, plates):
        yy = cy - h / 2.0 + h * k / float(plates)
        PA.hand_stroke(d, [(cx - w / 2.0, yy + 4), (cx + w / 2.0, yy - 3)],
                       STEEL_D, 6, closed=False, seed=seed + 10 + k,
                       wavelength=160.0)
        PA.hand_stroke(d, [(cx - w / 2.0, yy + 10), (cx + w / 2.0, yy + 3)],
                       (170, 180, 192), 3, closed=False, seed=seed + 30 + k,
                       wavelength=160.0)

    # rivets down both stiles. edge=0 and an ink rim: see _rivet_row -- a 9px
    # fill with the default 4.6px wobble comes out as a star, and a field of
    # stars reads as dirt on the lens rather than as bolts.
    for k in range(9):
        yy = cy - h / 2.0 + h * (k + 0.5) / 9.0
        for side in (-1, 1):
            rx = cx + side * (w / 2.0 - 34)
            _rivet_row(d, rx, yy, rx, yy, 1,
                       seed + 60 + k * 2 + (1 if side > 0 else 0),
                       colour=(176, 184, 194), r=11)

    if wheel:
        _lock_wheel(d, cx, cy, min(w, h) * 0.22, seed + 80)

    if lamp:
        lx = cx + w / 2.0 - 96
        ly = cy - h / 2.0 + 120
        glow = PA.ellipse_pts(lx, ly, 74, 74, n=36)
        PA.fill_poly(img, glow, (120, 44, 42), seed=seed + 110, value=0.10)
        PA.fill_poly(img, PA.ellipse_pts(lx, ly, 26, 26, n=24), RED,
                     seed=seed + 111, value=0.06)
        PA.hand_stroke(d, PA.ellipse_pts(lx, ly, 26, 26, n=24), INK, 5,
                       closed=True, seed=seed + 112, wavelength=50.0)


def _lock_wheel(d, cx, cy, r, seed):
    """A heavy DOGGING LOCK -- not a ship's helm.

    The first b13 pass drew six thin spokes and it read as a bank-vault dial
    sitting on a flat wall: a small circle with a handle, which is the opposite
    of "one closed door filling the whole frame". What makes a blast-door lock
    read as blast-door hardware is MASS and CHUNKNESS -- a thick rim, four
    short arms with squared ends rather than six thin ones, and a big square
    hub. Four arms is also what stops it reading as a helm.
    """
    img = PA.img_of(d)
    # the recessed collar the wheel is mounted in
    PA.fill_poly(img, PA.ellipse_pts(cx, cy, r * 1.34, r * 1.34, n=44),
                 (104, 114, 128), seed=seed, value=0.07, edge=0.0)
    PA.hand_stroke(d, PA.ellipse_pts(cx, cy, r * 1.34, r * 1.34, n=44), INK,
                   10, closed=True, seed=seed + 1, wavelength=110.0)
    # the rim: a THICK ring, drawn as two concentric fills so it has real width
    PA.fill_poly(img, PA.ellipse_pts(cx, cy, r, r, n=48), STEEL_D, seed=seed + 2,
                 value=0.07, edge=0.0)
    PA.fill_poly(img, PA.ellipse_pts(cx, cy, r * 0.80, r * 0.80, n=44),
                 (74, 82, 96), seed=seed + 3, value=0.06, edge=0.0)
    PA.hand_stroke(d, PA.ellipse_pts(cx, cy, r, r, n=48), INK, 12, closed=True,
                   seed=seed + 4, wavelength=110.0)
    PA.hand_stroke(d, PA.ellipse_pts(cx, cy, r * 0.80, r * 0.80, n=44), INK, 8,
                   closed=True, seed=seed + 5, wavelength=90.0)
    # four arms, thick, each ending in a squared pad that grips the rim
    for k in range(4):
        a = math.radians(45 + k * 90)
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa, ca                       # perpendicular, for the width
        aw = r * 0.105                         # half-width of the arm
        arm = [(cx + ca * r * 0.34 - px * aw, cy + sa * r * 0.34 - py * aw),
               (cx + ca * r * 0.86 - px * aw, cy + sa * r * 0.86 - py * aw),
               (cx + ca * r * 0.86 + px * aw, cy + sa * r * 0.86 + py * aw),
               (cx + ca * r * 0.34 + px * aw, cy + sa * r * 0.34 + py * aw)]
        PA.fill_poly(img, arm, (128, 138, 152), seed=seed + 10 + k, value=0.06,
                     edge=0.0)
        PA.hand_stroke(d, arm, INK, 7, closed=True, seed=seed + 20 + k,
                       wavelength=60.0)
    # the square hub
    hub = r * 0.26
    PA.fill_poly(img, [(cx - hub, cy - hub), (cx + hub, cy - hub),
                       (cx + hub, cy + hub), (cx - hub, cy + hub)],
                 (52, 56, 66), seed=seed + 30, value=0.05, edge=0.0)
    PA.hand_stroke(d, [(cx - hub, cy - hub), (cx + hub, cy - hub),
                       (cx + hub, cy + hub), (cx - hub, cy + hub)], INK, 9,
                   closed=True, seed=seed + 31, wavelength=50.0)


def _rivet_row(d, x0, y0, x1, y1, n, seed, colour=STEEL_D, r=8):
    """A run of rivets along a line.

    EDGE=0 IS LOAD-BEARING HERE. PA.fill_poly wobbles a polygon's boundary by
    PA.EDGE (4.6px) to make fills look hand-painted. On a large shape that is
    the painterly look; on a 9px rivet it is 50% of the radius, so every rivet
    is deformed into a four-pointed star. A column of those reads as scattered
    white dust on the wall, not as hardware -- it was the single most
    complained-about artifact in the first b13 pass. Small filled detail gets
    edge=0; only shapes big enough to absorb it keep the wobble.
    """
    for k in range(n):
        t = (k + 0.5) / float(n)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(x, y, r, r, n=16), colour,
                     seed=seed + k, value=0.05, edge=0.0)
        PA.hand_stroke(d, PA.ellipse_pts(x, y, r, r, n=16), (86, 92, 104), 3,
                       closed=True, seed=seed + 40 + k, wavelength=24.0,
                       vary=0.12)


# ---------------------------------------------------------------------------
# small local subjects
# ---------------------------------------------------------------------------

def _sensor(d, cx, cy, s, seed, lit=False, stalk=1.0):
    """A small sensor box with a whip antenna; `lit` puts the red lamp on it."""
    img = PA.img_of(d)
    body = [(cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7),
            (cx + s, cy + s * 0.8), (cx - s, cy + s * 0.8)]
    PA.fill_poly(img, body, CONCRETE_D, seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1, wavelength=60.0)
    PA.hand_stroke(d, [(cx + s * 0.4, cy - s * 0.7),
                       (cx + s * 0.4, cy - s * (0.7 + 2.4 * stalk))],
                   INK, 4, closed=False, seed=seed + 2, wavelength=50.0)
    if lit:
        glow = PA.ellipse_pts(cx, cy + s * 0.05, s * 1.5, s * 1.5, n=28)
        PA.fill_poly(img, glow, (128, 46, 44), seed=seed + 3, value=0.10)
        PA.fill_poly(img, PA.ellipse_pts(cx, cy + s * 0.05, s * 0.42, s * 0.42,
                                         n=18), RED, seed=seed + 4, value=0.05)
    PA.fill_poly(img, PA.ellipse_pts(cx, cy + s * 0.05, s * 0.42, s * 0.42,
                                     n=18),
                 RED if lit else (72, 76, 84), seed=seed + 5, value=0.05)


def _fence(d, x0, x1, base_y, h, seed, col=CONCRETE, n=None, rail=True):
    """An ordinary palisade fence. `n` pales the run past the frame edges."""
    img = PA.img_of(d)
    n = n or int((x1 - x0) / 26)
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / float(max(1, n))
        PA.fill_poly(img, [(x - 7, base_y), (x + 7, base_y),
                           (x + 7, base_y - h), (x - 7, base_y - h)],
                     col, seed=seed + k, value=0.07)
    PA.hand_stroke(d, [(x0, base_y), (x1, base_y)], INK, 5, closed=False,
                   seed=seed + 60, wavelength=150.0)
    if rail:
        PA.hand_stroke(d, [(x0, base_y - h * 0.82), (x1, base_y - h * 0.86)],
                       INK, 4, closed=False, seed=seed + 61, wavelength=150.0)


def _tree(d, x, base_y, h, seed, col=PARK, crown=0.62):
    """A round-crowned park tree, cropped by the frame edge where it sits."""
    img = PA.img_of(d)
    PA.hand_stroke(d, [(x, base_y), (x - h * 0.04, base_y - h * crown)],
                   (86, 68, 52), int(h * 0.10), closed=False, seed=seed,
                   wavelength=70.0)
    cpts = PA.ellipse_pts(x - h * 0.04, base_y - h * (crown + 0.20),
                          h * 0.42, h * 0.34, n=40)
    PA.fill_poly(img, cpts, col, seed=seed + 1, value=0.09)
    PA.hand_stroke(d, cpts, INK, 5, closed=True, seed=seed + 2, wavelength=90.0)


def _car(d, x, base_y, w, seed, col=(126, 130, 140)):
    """A plain parked car, seen side on. Deliberately undramatic."""
    img = PA.img_of(d)
    body = [(x, base_y - w * 0.30), (x + w * 0.18, base_y - w * 0.32),
            (x + w * 0.32, base_y - w * 0.56), (x + w * 0.74, base_y - w * 0.56),
            (x + w * 0.88, base_y - w * 0.32), (x + w, base_y - w * 0.30),
            (x + w, base_y), (x, base_y)]
    PA.fill_poly(img, body, col, seed=seed, value=0.07)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1, wavelength=90.0)
    PA.fill_poly(img, [(x + w * 0.36, base_y - w * 0.52),
                       (x + w * 0.70, base_y - w * 0.52),
                       (x + w * 0.70, base_y - w * 0.36),
                       (x + w * 0.36, base_y - w * 0.36)],
                 (172, 186, 196), seed=seed + 2, value=0.05)
    for wf in (0.22, 0.80):
        PA.fill_poly(img, PA.ellipse_pts(x + w * wf, base_y, w * 0.13,
                                         w * 0.13, n=16), INK, seed=seed + 3,
                     value=0.03)


def _console(d, cx, base_y, w, h, seed, col=(96, 104, 116), screen=True):
    """A blocky control console: a sloped desk with one bank on top."""
    img = PA.img_of(d)
    body = [(cx - w / 2.0, base_y), (cx - w * 0.40, base_y - h),
            (cx + w * 0.40, base_y - h), (cx + w / 2.0, base_y)]
    PA.fill_poly(img, body, col, seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1, wavelength=90.0)
    PA.fill_rect(img, [cx - w * 0.44, base_y - h - h * 0.42,
                       cx + w * 0.44, base_y - h + h * 0.06],
                 (78, 86, 98), seed=seed + 2, value=0.07)
    PA.hand_stroke(d, [(cx - w * 0.44, base_y - h - h * 0.42),
                       (cx + w * 0.44, base_y - h - h * 0.42)], INK, 5,
                   closed=False, seed=seed + 3, wavelength=80.0)
    if screen:
        PA.fill_poly(img, PA.ellipse_pts(cx, base_y - h * 1.18, w * 0.22,
                                         h * 0.22, n=28), (74, 96, 96),
                     seed=seed + 4, value=0.08)
        PA.hand_stroke(d, PA.ellipse_pts(cx, base_y - h * 1.18, w * 0.22,
                                          h * 0.22, n=28), INK, 5, closed=True,
                       seed=seed + 5, wavelength=60.0)


def _switch_bank(d, x0, y0, x1, y1, seed, n=6, big_at=None, big_col=RED):
    """A row of toggle switches; `big_at` puts one large button in the row."""
    img = PA.img_of(d)
    PA.fill_rect(img, [x0, y0, x1, y1], (72, 80, 92), seed=seed, value=0.07)
    PA.hand_stroke(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], INK, 6,
                   closed=True, seed=seed + 1, wavelength=90.0)
    step = (x1 - x0) / float(n)
    for k in range(n):
        x = x0 + step * (k + 0.5)
        if big_at is not None and k == big_at:
            PA.fill_poly(img, PA.ellipse_pts(x, (y0 + y1) / 2.0 - 8,
                                             step * 0.40, step * 0.40, n=26),
                         (110, 40, 38), seed=seed + 20 + k, value=0.09)
            PA.fill_poly(img, PA.ellipse_pts(x, (y0 + y1) / 2.0 - 8,
                                             step * 0.30, step * 0.30, n=24),
                         big_col, seed=seed + 40 + k, value=0.06)
            PA.hand_stroke(d, PA.ellipse_pts(x, (y0 + y1) / 2.0 - 8,
                                              step * 0.30, step * 0.30, n=24),
                           INK, 5, closed=True, seed=seed + 60 + k,
                           wavelength=50.0)
            continue
        PA.fill_poly(img, [(x - 9, y1 - 16), (x + 9, y1 - 16),
                           (x + 9, (y0 + y1) / 2.0), (x - 9, (y0 + y1) / 2.0)],
                     (150, 156, 166), seed=seed + 20 + k, value=0.06)
        PA.hand_stroke(d, [(x, (y0 + y1) / 2.0), (x - 5, y1 - 20)], INK, 5,
                       closed=False, seed=seed + 40 + k, wavelength=40.0)


def _keypad(d, cx, cy, w, h, seed, cols=3, rows=4):
    """A blank access panel: a grid of unmarked keys, no numbers legible."""
    img = PA.img_of(d)
    body = [(cx - w / 2.0, cy - h / 2.0), (cx + w / 2.0, cy - h / 2.0 - 3),
            (cx + w / 2.0, cy + h / 2.0), (cx - w / 2.0, cy + h / 2.0 + 3)]
    PA.fill_poly(img, body, (88, 96, 108), seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1, wavelength=70.0)
    kw = w * 0.82 / cols
    kh = h * 0.78 / rows
    for r in range(rows):
        for c in range(cols):
            kx = cx - w * 0.41 + kw * (c + 0.5)
            ky = cy - h * 0.39 + kh * (r + 0.5)
            PA.fill_rect(img, [kx - kw * 0.38, ky - kh * 0.36,
                               kx + kw * 0.38, ky + kh * 0.36],
                         (146, 152, 160), seed=seed + 10 + r * cols + c,
                         value=0.06)


def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def card(i, j, draw, kind='subject', seed=0, motion=None):
        """A complete card: its own background, live beats i..j-1."""
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        return E3.E('card%02d' % i, kind, draw, at=T(i), until=end,
                    motion=motion)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ===== b01  the cross-section: a bunker under the park ================ #
    def c_under_kremlin(tile, fw, fh):
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
        # THE chamber: a deep concrete box cut into the clay, running off the
        # bottom edge -- the subject owns the lower half of the frame
        ch = [(340, 450), (960, 440), (1060, 720), (300, 720)]
        PA.fill_poly(PA.img_of(d), ch, DARK, seed=118, value=0.10)
        PA.hand_stroke(d, [(340, 450), (960, 440), (1060, 720)], INK, 9,
                       closed=False, seed=119, wavelength=170.0)
        PA.fill_rect(tile, [298, 450, 1002, 512], CONCRETE_D, seed=120,
                     value=0.08)
        PA.hand_stroke(d, [(340, 450), (960, 440)], CONCRETE_L, 12,
                       closed=False, seed=121, wavelength=150.0)
        _rivet_row(d, 360, 482, 950, 474, 11, 122)
        D.draw_label(tile, 'under the park', center=(660, 384), color=INK,
                     size=38, outline=None, outline_w=0)
    els.append(card(1, 2, c_under_kremlin))
    els.append(cap(1, W // 2, 664, size=32, fill=RED))

    # ===== b02  nobody has ever walked through it (character) ============ #
    def c_locked_out(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 131, CONCRETE_D, floor=600)
        # the door, cropped hard left and right: it is bigger than the frame
        _blast_door(d, 470, 400, 900, 620, 132, wheel=True, plates=3)
        # the character, cropped INTO the right of frame, looking up at it
        SC.closeup(d, 1030, 350, 200, 'skeptic', 133)
        D.draw_bubble(tile, 'nobody goes in', (830, 150),
                      tail_to=(1010, 268), font_size=32, max_w=330)
    els.append(card(2, 3, c_locked_out, kind='character'))
    els.append(cap(2, W // 2, 686, size=32, fill=SNOW))

    # ===== b03  the title: OBJECT 739 on a blueprint ===================== #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (58, 74, 92), seed=141, value=0.07)
        PA.paper_overlay(tile, seed=142)
        # A dark card needs a lit concrete course at the head for the
        # near-black title to read against (see scene_common.title_backdrop).
        # Drawn before the blueprint grid so the backdrop stays UNDER the art.
        SC.title_backdrop(tile, 1141, col=(96, 98, 110))
        for k in range(13):
            x = 60 + k * 96
            PA.hand_stroke(d, [(x, 0), (x, H)], (86, 104, 122), 2,
                           closed=False, seed=143 + k, wavelength=140.0)
        for k in range(8):
            y = 50 + k * 92
            PA.hand_stroke(d, [(0, y), (W, y)], (86, 104, 122), 2,
                           closed=False, seed=160 + k, wavelength=140.0)
        # the bunker drawn as a plan, running off both edges
        plan = [(190, 250), (1180, 214), (1240, 560), (150, 600)]
        PA.fill_poly(PA.img_of(d), plan, (72, 92, 112), seed=170, value=0.08)
        PA.hand_stroke(d, plan, (196, 214, 228), 7, closed=True, seed=171,
                       wavelength=190.0)
        PA.hand_stroke(d, [(190, 250), (400, 420), (760, 400), (1180, 214)],
                       (196, 214, 228), 4, closed=False, seed=172,
                       wavelength=150.0)
        # NOT D.draw_title: the scene title strip already reads "Object 739"
        # across the top of every frame, so a hero word there collided with it
        # and both became illegible. The hero word goes mid-frame instead.
        D.draw_label(tile, 'OBJECT 739', center=(640, 392),
                     color=(238, 226, 172), size=78, outline=(18, 26, 38),
                     outline_w=6)
        D.draw_label(tile, 'SEALED', center=(640, 596), color=(206, 220, 234),
                     size=36, outline=(18, 26, 38), outline_w=4)
    els.append(card(3, 4, c_title))
    els.append(cap(3, W // 2, 700, size=30, fill=SNOW))

    # ===== b04  Stalin ordered it: a plain portrait sketch ================ #
    def c_stalin(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], PAPERW, seed=151, value=0.06)
        PA.paper_overlay(tile, seed=152)
        cx, cy, r = 470, 330, 168
        # shoulders, cropped by the left edge so the sitter fills the frame
        sh = [(cx - 300, 720), (cx - 250, 520), (cx - 120, 452),
              (cx + 120, 452), (cx + 250, 520), (cx + 320, 720)]
        PA.fill_poly(PA.img_of(d), sh, (92, 92, 96), seed=153, value=0.07)
        PA.hand_stroke(d, sh, INK, 7, closed=True, seed=154, wavelength=150.0)
        head = PA.ellipse_pts(cx, cy, r, r * 1.10, n=48)
        PA.fill_poly(PA.img_of(d), head, (216, 202, 186), seed=155, value=0.06)
        PA.hand_stroke(d, head, INK, 7, closed=True, seed=156, wavelength=110.0)
        # hair, swept back
        PA.hand_stroke(d, [(cx - r * 0.98, cy - r * 0.42),
                           (cx - r * 0.60, cy - r * 1.02),
                           (cx + r * 0.30, cy - r * 1.10),
                           (cx + r * 0.86, cy - r * 0.66)],
                       INK, 16, closed=False, seed=157, wavelength=90.0)
        # moustache + mouth
        PA.hand_stroke(d, [(cx - r * 0.42, cy + r * 0.30),
                           (cx, cy + r * 0.24),
                           (cx + r * 0.42, cy + r * 0.30)], INK, 13,
                       closed=False, seed=158, wavelength=50.0)
        # eyes, brow, nose: three marks, no shading -- a sketch, not a portrait
        for s in (-1, 1):
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(cx + s * r * 0.36,
                                                     cy - r * 0.14, 13, 10,
                                                     n=14), INK, seed=159,
                         value=0.03)
            PA.hand_stroke(d, [(cx + s * r * 0.56, cy - r * 0.40),
                               (cx + s * r * 0.18, cy - r * 0.46)], INK, 7,
                           closed=False, seed=160, wavelength=40.0)
        PA.hand_stroke(d, [(cx, cy - r * 0.06), (cx + r * 0.14, cy + r * 0.16),
                           (cx - r * 0.06, cy + r * 0.18)], (110, 110, 114), 6,
                       closed=False, seed=161, wavelength=50.0)
        D.draw_label(tile, 'the 1950s', center=(1000, 300), color=INK,
                     size=44, outline=None, outline_w=0)
        PA.hand_stroke(d, [(840, 360), (1170, 352)], RED, 8, closed=False,
                       seed=162, wavelength=140.0)
    els.append(card(4, 5, c_stalin))
    els.append(cap(4, W // 2, 668, size=32, fill=RED))

    # ===== b05  one refuge of his own: one man, one desk ================== #
    def c_one_man(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 171, (58, 58, 62), floor=None)
        # A dark card needs a lit concrete course at the head for the near-black
        # title to read against (see scene_common.title_backdrop).
        SC.title_backdrop(tile, 1171, col=(96, 98, 110))
        # a single pool of lamp light, the only lit thing. The pool and its
        # shade start at y=104 so the lit shade does not grow up through the
        # persistent title band.
        pool = [(300, 104), (1000, 104), (1180, 560), (140, 560)]
        PA.fill_poly(PA.img_of(d), pool, (110, 104, 88), seed=172, value=0.08)
        # the flex, dropping from BEHIND the course rather than through it
        PA.hand_stroke(d, [(622, 88), (640, 104)], INK, 6, closed=False,
                       seed=173, wavelength=60.0)
        PA.fill_poly(PA.img_of(d), [(560, 104), (700, 104), (740, 160),
                                    (520, 160)], (206, 196, 168), seed=174,
                     value=0.07)
        # the desk, cropped by the bottom edge and running past both sides
        desk = [(-40, 470), (W + 40, 470), (W + 40, 720), (-40, 720)]
        PA.fill_poly(PA.img_of(d), desk, (118, 96, 72), seed=175, value=0.08)
        PA.hand_stroke(d, [(-40, 470), (W + 40, 470)], INK, 7, closed=False,
                       seed=176, wavelength=190.0)
        # the plan he is drawing: a small bunker cross-section on the paper
        pl = [(470, 500), (860, 494), (900, 600), (450, 606)]
        PA.fill_poly(PA.img_of(d), pl, (236, 232, 222), seed=177, value=0.05)
        PA.hand_stroke(d, pl, INK, 4, closed=True, seed=178, wavelength=90.0)
        PA.hand_stroke(d, [(520, 560), (830, 552)], (120, 120, 126), 3,
                       closed=False, seed=179, wavelength=60.0)
        PA.hand_stroke(d, [(540, 580), (700, 574)], (120, 120, 126), 3,
                       closed=False, seed=180, wavelength=60.0)
        _figure(d, 320, 470, 380, pose='pointing', expression='grim', seed=181)
    els.append(card(5, 6, c_one_man, kind='character'))
    els.append(cap(5, W // 2, 668, size=32, fill=SNOW))

    # ===== b06  it sits below a small park ================================ #
    def c_park_over(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 191, sky=(178, 190, 198), ground=CLAY, hz=300)
        _strata(d, 192, 320, 560, n=3)
        # the park band, and the ceiling slab under it
        PA.fill_rect(tile, [0, 236, W, 302], PARK, seed=193, value=0.08)
        PA.hand_stroke(d, [(-20, 244), (W + 20, 238)], INK, 6, closed=False,
                       seed=194, wavelength=190.0)
        # x=520 sits under the persistent "Object 739" title, so its crown is
        # kept short enough that the canopy top stays below the title band. The
        # other four clear the band horizontally and keep full height.
        for k, (x, th) in enumerate(((120, 150), (300, 150), (520, 120),
                                      (1080, 150), (1230, 150))):
            _tree(d, x, 240, th, 195 + k)
        slab = [(-40, 302), (W + 40, 296), (W + 40, 372), (-40, 380)]
        PA.fill_poly(PA.img_of(d), slab, CONCRETE, seed=200, value=0.08)
        PA.hand_stroke(d, [(-40, 302), (W + 40, 296)], INK, 7, closed=False,
                       seed=201, wavelength=200.0)
        _rivet_row(d, -10, 340, W + 10, 334, 14, 202)
        # the chamber below, running off the bottom edge
        ch = [(240, 420), (1050, 410), (1130, 720), (180, 720)]
        PA.fill_poly(PA.img_of(d), ch, DARK, seed=203, value=0.10)
        PA.hand_stroke(d, [(240, 420), (1050, 410), (1130, 720)], INK, 9,
                       closed=False, seed=204, wavelength=180.0)
        D.draw_label(tile, 'the park above', center=(340, 200), color=INK,
                     size=34, outline=None, outline_w=0)
    els.append(card(6, 7, c_park_over))
    els.append(cap(6, W // 2, 672, size=32, fill=SNOW))

    # ===== b07  Moscow was built on sinking ground ======================= #
    def c_sinking(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _soil_bg(tile, 211, top_col=CLAY, hz=210, water_y=560)
        # buildings on top, thin and tilted -- the surface is not stable.
        # The x=760 block is the only one wide enough to reach under the
        # persistent title, so it is the only one shortened; its neighbours
        # clear the band horizontally and keep their full height.
        for k, (x, w, h) in enumerate(((80, 190, 150), (330, 150, 200),
                                       (760, 210, 100), (1030, 160, 210))):
            b0 = 214
            bd = [(x, b0), (x + w, b0 - 8), (x + w - 6, b0 - h),
                  (x + 8, b0 - h + 6)]
            PA.fill_poly(PA.img_of(d), bd, (172, 174, 178), seed=212 + k,
                         value=0.07)
            PA.hand_stroke(d, bd, INK, 5, closed=True, seed=216 + k,
                           wavelength=90.0)
        _strata(d, 220, 240, 540, n=4)
        # standing groundwater pooling in the clay, the reason it sinks
        PA.fill_rect(tile, [0, 556, W, 720], WATER, seed=225, value=0.09)
        PA.hand_stroke(d, [(-20, 558), (W + 20, 552)], (58, 92, 112), 5,
                       closed=False, seed=226, wavelength=180.0)
        for k in range(6):
            xx = 60 + k * 210
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(xx, 630 + (k % 3) * 24,
                                                      44, 14, n=20),
                         (120, 158, 174), seed=230 + k, value=0.06)
        D.draw_label(tile, 'sinking ground', center=(640, 486), color=INK,
                     size=36, outline=None, outline_w=0)
    els.append(card(7, 8, c_sinking))
    els.append(cap(7, W // 2, 672, size=32, fill=RED))

    # ===== b08  everything above the ceiling is hardened steel =========== #
    def c_slab(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 241, (52, 54, 60), floor=None)
        # lit course at the head so the near-black title reads on this dark card
        SC.title_backdrop(tile, 1241, col=(96, 98, 110))
        # the slab: an enormous steel plate past both edges, off the top too
        slab = [(-60, 150), (W + 60, 126), (W + 60, 470), (-60, 494)]
        PA.fill_poly(PA.img_of(d), slab, STEEL, seed=242, value=0.09)
        PA.hand_stroke(d, [(-60, 150), (W + 60, 126)], CONCRETE_L, 10,
                       closed=False, seed=243, wavelength=210.0)
        PA.hand_stroke(d, [(-60, 494), (W + 60, 470)], INK, 9, closed=False,
                       seed=244, wavelength=210.0)
        _rivet_row(d, -20, 210, W + 20, 188, 16, 245, colour=(176, 186, 198))
        _rivet_row(d, -20, 400, W + 20, 378, 16, 262, colour=(176, 186, 198))
        PA.hand_stroke(d, [(-60, 300), (W + 60, 278)], STEEL_D, 6,
                       closed=False, seed=280, wavelength=200.0)
        # the character stands ON the slab, for scale
        _figure(d, 620, 496, 350, pose='armscrossed',
                expression='confused', seed=281)
        D.draw_label(tile, 'hardened steel', center=(300, 566), color=INK,
                     size=38, outline=None, outline_w=0)
        PA.hand_stroke(d, [(300, 516), (520, 490)], RED, 8, closed=False,
                       seed=282, wavelength=120.0)
    els.append(card(8, 9, c_slab, kind='character'))
    els.append(cap(8, W // 2, 674, size=32, fill=SNOW))

    # ===== b09  ordinary buildings rest on thin foundations =============== #
    def c_thin_foundations(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 291, sky=(184, 192, 198), ground=CLAY, hz=250)
        _strata(d, 292, 268, 500, n=3)
        # LEFT: an ordinary building on a wafer-thin foundation. The roof line
        # is held at y=112 so it clears the persistent title band; the window
        # band moves with it to keep the same proportion of the facade.
        PA.fill_rect(tile, [-40, 112, 600, 250], (176, 178, 182), seed=293,
                     value=0.07)
        PA.hand_stroke(d, [(-40, 112), (600, 112)], INK, 6, closed=False,
                       seed=294, wavelength=150.0)
        for k in range(5):
            PA.fill_rect(tile, [10 + k * 116, 142, 96 + k * 116, 198],
                         (140, 146, 154), seed=295 + k, value=0.06)
        thin = [(-40, 250), (600, 246), (600, 268), (-40, 274)]
        PA.fill_poly(PA.img_of(d), thin, (206, 202, 192), seed=300,
                     value=0.06)
        PA.hand_stroke(d, [(-40, 250), (600, 246)], INK, 5, closed=False,
                       seed=301, wavelength=150.0)
        D.draw_label(tile, 'ordinary', center=(280, 330), color=INK, size=36,
                     outline=None, outline_w=0)
        # RIGHT: the same ground, the bunker slab -- four times the thickness
        slab = [(660, 246), (W + 40, 240), (W + 40, 400), (660, 410)]
        PA.fill_poly(PA.img_of(d), slab, STEEL, seed=302, value=0.08)
        PA.hand_stroke(d, [(660, 246), (W + 40, 240)], CONCRETE_L, 8,
                       closed=False, seed=303, wavelength=150.0)
        _rivet_row(d, 680, 330, W + 20, 324, 9, 304)
        D.draw_label(tile, 'Object 739', center=(980, 200), color=INK,
                     size=36, outline=None, outline_w=0)
        # the dividing line: the contrast IS the card. It runs from just below
        # the persistent title band to the bottom edge, so it still splits both
        # masses top to bottom without striking through the title.
        PA.hand_stroke(d, [(630, 118), (630, 720)], RED, 9, closed=False,
                       seed=305, wavelength=180.0)
    els.append(card(9, 10, c_thin_foundations))
    els.append(cap(9, W // 2, 676, size=32, fill=RED))

    # ===== b10  the doors were made to close forever ======================= #
    def c_close_forever(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 321, CONCRETE_D, floor=None)
        # The leaf, cropped by the left edge and by the bottom edge. cy=514
        # starts the leaf -- and the lock wheel whose collar arc reached up to
        # y=58 -- at y=104, so nothing crosses the title band. cx=760 also puts
        # the vertical seam (cx + w*0.04 = 803) clear of the band's right edge.
        _blast_door(d, 760, 514, 1080, 820, 322, wheel=True, plates=4)
        # concrete jamb closing on the right, starting level with the leaf
        jamb = [(900, 104), (W + 60, 104), (W + 60, 760), (900, 760)]
        PA.fill_poly(PA.img_of(d), jamb, (150, 150, 146), seed=324,
                     value=0.09)
        PA.hand_stroke(d, [(900, 104), (900, 760)], INK, 9, closed=False,
                       seed=325, wavelength=190.0)
        D.draw_label(tile, 'made to close', center=(300, 620), color=INK,
                     size=42, outline=None, outline_w=0)
    els.append(card(10, 11, c_close_forever))
    els.append(cap(10, W // 2, 674, size=32, fill=RED))

    # ===== b11  each leaf weighs hundreds of tonnes (truck for scale) ==== #
    def c_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 341, sky=(180, 188, 196), ground=(158, 158, 154))
        # The door leaf standing on the ground, cropped by the bottom edge.
        # h=616 with cy=412 lands the top edge exactly on y=104, so the leaf's
        # closed INK outline and its full-height seam (cx + w*0.04 = 696) both
        # start below the title band. The lock wheel drops to y=412 with it.
        _blast_door(d, 660, 412, 900, 616, 342, wheel=True, plates=4)
        # an ordinary truck at its foot, tiny -- the whole point of the card.
        # Light enough to read against the shadowed ground: a dark truck on a
        # dark base just made a smudge at the foot of the door.
        tx, ty = 236, 590
        PA.fill_poly(PA.img_of(d), [(tx, ty - 82), (tx + 100, ty - 86),
                                    (tx + 106, ty - 48), (tx + 224, ty - 44),
                                    (tx + 228, ty)], (188, 192, 198),
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
        # the label rides UP on the door face, clear of the caption at the foot
        D.draw_label(tile, 'hundreds', center=(880, 566), color=INK,
                     size=40, outline=None, outline_w=0)
        D.draw_label(tile, 'of tonnes', center=(880, 610), color=INK,
                     size=40, outline=None, outline_w=0)
        PA.hand_stroke(d, [(700, 500), (450, 556)], RED, 8, closed=False,
                       seed=347, wavelength=110.0)
    els.append(card(11, 12, c_tonnes))
    els.append(cap(11, W // 2, 674, size=32, fill=RED))

    # ===== b12  they are sealed, and never opened ========================= #
    def c_welded(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 361, (140, 140, 136), floor=None)
        # the door edge, cropped hard: only the seam and the leaf face show.
        # cx is shifted right so the leaf's vertical seam (cx + w*0.04) clears
        # the persistent title band; the leaf is still cropped hard at the weld.
        _blast_door(d, 776, 340, 860, 760, 362, wheel=False, plates=3)
        # the weld bead: bright, uneven, running the full height
        seam = []
        for k in range(15):
            seam.append((470 + (k % 3) * 7 - 4, 300 + k * 30))
        PA.hand_stroke(d, seam, (222, 216, 190), 15, closed=False, seed=364,
                       wavelength=48.0, vary=0.45)
        PA.hand_stroke(d, [(470, 300), (470, 720)], (250, 244, 220), 5,
                       closed=False, seed=365, wavelength=48.0, vary=0.5)
        for k in range(11):
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(470 + (k % 2) * 6 - 3,
                                                      312 + k * 38, 13, 9,
                                                      n=12), (240, 234, 208),
                         seed=366 + k, value=0.05)
        D.draw_label(tile, 'welded shut', center=(980, 566), color=INK,
                     size=44, outline=None, outline_w=0)
    els.append(card(12, 13, c_welded))
    els.append(cap(12, W // 2, 674, size=32, fill=RED))

    # ===== b13  ONE CLOSED DOOR, FILLING THE WHOLE FRAME ================= #
    def c_one_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], STEEL, seed=381, value=0.10)
        PA.paper_overlay(tile, seed=382)
        # THE LEAF, off all four edges. The narration says the door fills the
        # frame, so nothing here is allowed to sit inside a margin.
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
        # a second, inner panel line -- armour is plate over plate
        PA.hand_stroke(d, [(120, 150), (1160, 142)], (86, 96, 110), 6,
                       closed=False, seed=388, wavelength=200.0)
        PA.hand_stroke(d, [(120, 596), (1160, 588)], (86, 96, 110), 6,
                       closed=False, seed=389, wavelength=200.0)

        # RIVETS as a deliberate border round the panel. Same positions, top
        # and bottom, evenly spaced -- hardware, not scatter.
        for k in range(16):
            rx = 40 + k * 80
            _rivet_row(d, rx, 128, rx, 128, 1, 400 + k,
                       colour=(180, 190, 202), r=12)
            _rivet_row(d, rx, 612, rx, 612, 1, 440 + k,
                       colour=(180, 190, 202), r=12)

        # THE LOCK, big enough to belong to a slab this size but still fully
        # inside the recessed panel -- a lock clipped by the frame edge reads
        # as a mistake, and this one is the only thing the eye should land on.
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
    els.append(card(13, 14, c_one_door))
    els.append(cap(13, W // 2, 674, size=34, fill=SNOW))

    # ===== b14  Stalin never went inside (character) ====================== #
    def c_never_went_in(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 401, (62, 64, 70), floor=596)
        # The door behind him, closed, cropped right. It is sized so its left
        # edge (x=420) and its left stile of rivets (x=454) both sit clear to
        # the left of the persistent title band, and the leaf covers the band
        # rather than leaving a strip of dark background showing through. The
        # character is drawn after it, so he still reads in front of the leaf.
        _blast_door(d, 920, 360, 1000, 720, 402, wheel=True, plates=3)
        # the character, cropped INTO the left of frame, shrugging at it
        SC.closeup(d, 350, 372, 210, 'skeptic', 403)
        PA.hand_stroke(d, [(250, 470), (330, 500)], INK, 9, closed=False,
                       seed=404, wavelength=50.0)
        PA.hand_stroke(d, [(450, 470), (370, 500)], INK, 9, closed=False,
                       seed=405, wavelength=50.0)
        D.draw_bubble(tile, 'he never went in', (620, 150),
                      tail_to=(400, 280), font_size=34, max_w=340)
    els.append(card(14, 15, c_never_went_in, kind='character'))
    els.append(cap(14, W // 2, 682, size=32, fill=SNOW))

    # ===== b15  the corridors were lined with lead ======================== #
    def c_corridor_cut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (108, 110, 118), seed=421, value=0.09)
        PA.paper_overlay(tile, seed=422)
        # the corridor void, running off both side edges
        PA.fill_rect(tile, [0, 150, W, 570], DARKER, seed=423, value=0.06)
        # lead plates: floor, walls, ceiling -- each a thick band
        for k, (y0, y1) in enumerate(((0, 150), (570, 720))):
            PA.fill_rect(tile, [-40, y0, W + 40, y1], LEAD, seed=424 + k,
                         value=0.08)
            PA.hand_stroke(d, [(-40, y0 + (0 if k else 0)),
                               (W + 40, y0)], (66, 70, 82), 6,
                           closed=False, seed=430 + k, wavelength=200.0)
        for k in range(9):
            x = -40 + k * 170
            PA.fill_poly(PA.img_of(d), [(x, 150), (x + 150, 150),
                                        (x + 150, 570), (x, 570)],
                         LEAD_L if k % 2 else LEAD, seed=440 + k, value=0.07)
            PA.hand_stroke(d, [(x, 150), (x, 570)], (66, 70, 82), 4,
                           closed=False, seed=450 + k, wavelength=150.0)
        # the far end of the corridor, small and dark
        end = [(560, 250), (720, 250), (720, 470), (560, 470)]
        PA.fill_poly(PA.img_of(d), end, (18, 19, 24), seed=460, value=0.05)
        PA.hand_stroke(d, end, (150, 154, 164), 5, closed=True, seed=461,
                       wavelength=80.0)
    els.append(card(15, 16, c_corridor_cut))
    els.append(cap(15, W // 2, 674, size=32, fill=SNOW))

    # ===== b16  floor to ceiling, plate over plate ======================= #
    def c_plates(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], LEAD, seed=471, value=0.10)
        PA.paper_overlay(tile, seed=472)
        # one long continuous band of plate running off both edges, floor to ceiling.
        #
        # The pitch is 344 and the leaf is 330, not 240 and 226, and that is a
        # band calculation rather than a taste one. The title column is 312 wide
        # (x=484..796), so at the old 240 pitch no phase could keep a plate seam
        # out of it: one seam always landed inside, and a seam between two plate
        # values makes every band row non-uniform, which is what the band gate
        # reads as art striking through the title. At 344 the leaves are wider
        # than the column, so exactly one leaf spans it and no seam can fall
        # inside. x0=-210 puts that leaf at 478..808, clearing both edges of the
        # column by a few px.
        for k in range(5):
            x = -210 + k * 344
            PA.fill_poly(PA.img_of(d), [(x, -60), (x + 330, -60),
                                        (x + 330, H + 60), (x, H + 60)],
                         LEAD_L if k % 2 else LEAD, seed=473 + k, value=0.08)
            PA.hand_stroke(d, [(x + 330, -60), (x + 330, H + 60)],
                           (62, 66, 78), 6, closed=False, seed=479 + k,
                           wavelength=200.0)
            _rivet_row(d, x + 52, 60, x + 52, 690, 7, 486 + k,
                       colour=(64, 68, 80), r=10)
        PA.hand_stroke(d, [(-40, 150), (W + 40, 146)], (168, 172, 184), 5,
                       closed=False, seed=500, wavelength=200.0)
        PA.hand_stroke(d, [(-40, 572), (W + 40, 568)], (168, 172, 184), 5,
                       closed=False, seed=501, wavelength=200.0)
        D.draw_label(tile, 'lead lined', center=(640, 330), color=SNOW,
                     size=48, outline=(30, 32, 40), outline_w=4)
    els.append(card(16, 17, c_plates))
    els.append(cap(16, W // 2, 676, size=32, fill=SNOW))

    # ===== b17  below that, a control room waits ============================ #
    def c_control_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 521, (48, 50, 58), floor=596)
        # lit course at the head so the near-black title reads on this dark card
        SC.title_backdrop(tile, 1521, col=(96, 98, 110))
        # the chamber at the end of the corridor, low and wide
        room = [(-40, 210), (760, 190), (900, 596), (-40, 596)]
        PA.fill_poly(PA.img_of(d), room, (58, 62, 72), seed=522, value=0.09)
        PA.hand_stroke(d, [(-40, 210), (760, 190), (900, 596)], INK, 8,
                       closed=False, seed=523, wavelength=170.0)
        # ONE lamp, the only light in the chapter so far. The cone and its
        # shade start at y=104 so the lit shade does not grow up through the
        # persistent title band.
        lamp = [(520, 104), (700, 104), (900, 300), (320, 300)]
        PA.fill_poly(PA.img_of(d), lamp, (96, 92, 74), seed=524, value=0.05)
        PA.fill_poly(PA.img_of(d), [(540, 104), (690, 104), (740, 182),
                                    (490, 182)], LAMP, seed=525, value=0.05)
        # the console under it, small in the corner of a big room
        _console(d, 470, 590, 340, 130, 526)
        # the character, tiny, awed -- scale is the point of this card
        _figure(d, 880, 594, 330, pose='pointing', expression='awed',
                seed=527)
    els.append(card(17, 18, c_control_room, kind='character'))
    els.append(cap(17, W // 2, 674, size=32, fill=SNOW))

    # ===== b18  the room is said to hold one console ===================== #
    def c_said_to_exist(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 46, 54), seed=531, value=0.09)
        PA.paper_overlay(tile, seed=532)
        # a cutaway: the rock hatched away, the room drawn inside it
        PA.fill_rect(tile, [-40, -40, W + 40, 250], (120, 118, 112), seed=533,
                     value=0.08)
        for k in range(14):
            x = -40 + k * 104
            PA.hand_stroke(d, [(x, 250), (x + 90, 150)], (86, 84, 80), 4,
                           closed=False, seed=534 + k, wavelength=60.0,
                           vary=0.2)
        PA.fill_rect(tile, [-40, 250, W + 40, 640], (58, 62, 72), seed=548,
                     value=0.08)
        PA.fill_rect(tile, [-40, 640, W + 40, 760], DARKER, seed=549,
                     value=0.06)
        # the one console, blocky, under a hanging lamp
        lamp = [(560, 190), (740, 190), (860, 330), (440, 330)]
        PA.fill_poly(PA.img_of(d), lamp, (104, 98, 78), seed=550, value=0.05)
        PA.fill_poly(PA.img_of(d), [(580, 214), (716, 214), (752, 274),
                                    (546, 274)], LAMP, seed=551, value=0.05)
        _console(d, 640, 640, 420, 168, 552)
        # the uncertainty, marked not hidden: a dashed question ring
        ring = PA.ellipse_pts(640, 520, 330, 200, n=54)
        for k in range(0, 54, 3):
            PA.hand_stroke(d, [ring[k], ring[(k + 2) % 54]], (150, 146, 130),
                           4, closed=False, seed=560 + k, wavelength=40.0,
                           vary=0.2)
        D.draw_label(tile, 'said to exist', center=(1000, 420), color=INK,
                     size=38, outline=None, outline_w=0)
    els.append(card(18, 19, c_said_to_exist))
    els.append(cap(18, W // 2, 684, size=32, fill=SNOW))

    # ===== b19  a console drawn small, in the dark ======================= #
    def c_small_in_dark(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (26, 27, 33), seed=571, value=0.10)
        PA.paper_overlay(tile, seed=572)
        # lit course at the head so the near-black title reads on this card,
        # which is the darkest in the chapter
        SC.title_backdrop(tile, 1571, col=(96, 98, 110))
        # one small warm pool, and the console alone inside it
        pool = PA.ellipse_pts(640, 530, 250, 140, n=44)
        PA.fill_poly(PA.img_of(d), pool, (56, 54, 46), seed=573, value=0.07)
        # the beam, with a lamp fixture at its apex so the hard triangle edge
        # reads as a shade rather than as a rendering seam. Both start at
        # y=104: on this near-black card the lit fixture is far brighter than
        # its background, so above the band it is a title-obscuring blob.
        PA.fill_poly(PA.img_of(d), [(604, 104), (676, 104), (770, 340),
                                    (510, 340)], (60, 58, 50), seed=574,
                     value=0.05)
        PA.fill_poly(PA.img_of(d), [(560, 104), (716, 104), (770, 190),
                                    (506, 190)], (92, 88, 74), seed=578,
                     value=0.06)
        PA.fill_poly(PA.img_of(d), [(596, 168), (682, 168), (700, 192),
                                    (578, 192)], LAMP, seed=579, value=0.05)
        _console(d, 640, 610, 280, 104, 575, screen=False)
        # the console's own lit face: one warm strip, ON the desk front
        PA.fill_poly(PA.img_of(d), [(536, 556), (744, 554), (744, 580),
                                    (536, 582)], (188, 158, 112), seed=576,
                     value=0.07)
        PA.hand_stroke(d, [(536, 582), (744, 580)], INK, 4, closed=False,
                       seed=580, wavelength=70.0)
        # the floor line, barely there
        PA.hand_stroke(d, [(-40, 606), (W + 40, 602)], (52, 52, 58), 5,
                       closed=False, seed=577, wavelength=200.0)
    els.append(card(19, 20, c_small_in_dark))
    els.append(cap(19, W // 2, 680, size=32, fill=LAMP))

    # ===== b20  one row of switches, one big button ====================== #
    def c_switches(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (46, 48, 56), seed=581, value=0.08)
        PA.paper_overlay(tile, seed=582)
        # a hinged cover, propped open across the top of the frame
        cover = [(-40, -20), (W + 40, -20), (W + 40, 190), (-40, 200)]
        PA.fill_poly(PA.img_of(d), cover, (86, 92, 104), seed=583, value=0.08)
        PA.hand_stroke(d, [(-40, 200), (W + 40, 190)], INK, 9, closed=False,
                       seed=584, wavelength=200.0)
        PA.hand_stroke(d, [(980, 200), (1100, 190)], INK, 10, closed=False,
                       seed=585, wavelength=60.0)
        # the bank: six switches, one of them big and red
        _switch_bank(d, 130, 300, W - 60, 540, 586, n=6, big_at=4)
        # the one lit indicator, the only red in the room
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(300, 610, 62, 62, n=28),
                     (116, 42, 40), seed=600, value=0.09)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(300, 610, 26, 26, n=20),
                     RED, seed=601, value=0.05)
        D.draw_label(tile, 'one big button', center=(900, 596), color=INK,
                     size=36, outline=None, outline_w=0)
    els.append(card(20, 21, c_switches))
    els.append(cap(20, W // 2, 690, size=32, fill=SNOW))

    # ===== b21  no official record confirms it (character) =============== #
    def c_no_record(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], PAPERW, seed=611, value=0.06)
        PA.paper_overlay(tile, seed=612)
        # a desk, cropped by the bottom edge
        desk = [(-40, 520), (W + 40, 520), (W + 40, 760), (-40, 760)]
        PA.fill_poly(PA.img_of(d), desk, (128, 106, 80), seed=613, value=0.08)
        PA.hand_stroke(d, [(-40, 520), (W + 40, 520)], INK, 7, closed=False,
                       seed=614, wavelength=200.0)
        # an EMPTY file folder, open, with nothing in it
        PA.fill_poly(PA.img_of(d), [(700, 430), (1090, 424), (1120, 540),
                                    (680, 548)], (198, 186, 158), seed=615,
                     value=0.07)
        PA.hand_stroke(d, [(700, 430), (1090, 424), (1120, 540), (680, 548)],
                       INK, 6, closed=True, seed=616, wavelength=90.0)
        PA.fill_poly(PA.img_of(d), [(700, 430), (1090, 424), (1096, 380),
                                    (716, 386)], (176, 164, 138), seed=617,
                     value=0.07)
        PA.hand_stroke(d, [(716, 386), (1096, 380)], INK, 5, closed=False,
                       seed=618, wavelength=80.0)
        SC.closeup(d, 360, 340, 196, 'deadpan', 619)
        D.draw_bubble(tile, 'no record', (170, 110), tail_to=(340, 250),
                      font_size=36, max_w=250)
    els.append(card(21, 22, c_no_record, kind='character'))
    els.append(cap(21, W // 2, 664, size=32, fill=RED))

    # ===== b22  other bunkers from that era were documented ============== #
    def c_other_bunker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # FRAME-FILLED. The first pass left the top 45% as empty sky and the
        # queue crammed into the bottom-left corner at 190px, where the figures
        # degenerated into hollow wire outlines. It read as an unfinished plate
        # and the opposite of the point: this beat is a BUSTLING PUBLIC SITE.
        _sky(tile, 631, sky=(190, 198, 204), ground=(158, 158, 152),
             hz=int(H * 0.56))
        PA.fill_rect(tile, [-40, 404, W + 40, 490], (162, 162, 158), seed=632,
                     value=0.07)
        PA.fill_rect(tile, [-40, 490, W + 40, 760], (140, 140, 136), seed=637,
                     value=0.07)
        PA.hand_stroke(d, [(-40, 490), (W + 40, 486)], INK, 6, closed=False,
                       seed=638, wavelength=200.0)
        # a concrete entrance block running off both edges, lit inside
        blk = [(-60, 150), (W + 60, 132), (W + 60, 490), (-60, 490)]
        PA.fill_poly(PA.img_of(d), blk, (176, 176, 170), seed=639, value=0.07)
        PA.hand_stroke(d, [(-60, 150), (W + 60, 132)], INK, 8, closed=False,
                       seed=640, wavelength=200.0)
        # the opening: a wide lit mouth with both door leaves swung back
        mouth = [(300, 250), (1020, 236), (1020, 490), (300, 490)]
        PA.fill_poly(PA.img_of(d), mouth, LAMP, seed=641, value=0.06)
        PA.hand_stroke(d, mouth, INK, 8, closed=True, seed=642, wavelength=140.0)
        PA.fill_poly(PA.img_of(d), [(300, 250), (440, 268), (440, 490),
                                    (300, 490)], (72, 78, 88), seed=643,
                     value=0.06)
        PA.fill_poly(PA.img_of(d), [(1020, 236), (1140, 254), (1140, 490),
                                    (1020, 490)], (72, 78, 88), seed=644,
                     value=0.06)
        # a lamp over the mouth: this is a site that is OPEN, and it shows
        PA.fill_poly(PA.img_of(d), [(580, 120), (740, 116), (790, 186),
                                    (530, 190)], (92, 88, 76), seed=645,
                     value=0.06)
        PA.fill_poly(PA.img_of(d), [(606, 158), (716, 155), (740, 190),
                                    (580, 194)], LAMP, seed=646, value=0.05)
        # THE QUEUE: seven figures RECEDING left to right, the first cropped by the
        # left edge and the last by the right, so the line of visitors
        # continues past the frame -- a public site, not four people.
        # DARK ink, not cream: this is a daylight exterior, and the canon puts
        # the character dark on light. Cream figures on a mid-grey ground read
        # as washed-out ghosts.
        #
        # NOT a ruler-straight row, and NOT the "tucked" poses. Two rounds of
        # guessing here both failed, so the geometry is now measured instead:
        # ink width at 330px tall is standing 175, armscrossed 259, peeking 221,
        # pointing 250, shrug 281. `armscrossed` is the WIDEST of the lot --
        # la=(38,78) puts the forearm at 116 deg, i.e. flung up and OUT, not
        # across the chest, so "tucking" the arms made every figure shrug and
        # read as the horizontal-T-arm defect. The only narrow pose is
        # `standing`. So: standing everywhere, spacing opened to 200+ so the
        # 175px reach cannot reach a neighbour's hand (the first pass at 158px
        # joined them into a conga line of held hands), heights shrinking
        # 335 -> 250 so the line RECEDES instead of parading, one `pointing`
        # figure at a locally-widened gap because he is gesturing at the door,
        # and jitter on the baseline and expressions so it is a queue of
        # individuals rather than eight copies of one model.
        QUEUE = ((-30, 335, 'standing', 'neutral'),
                 (180, 320, 'standing', 'skeptic'),
                 (395, 305, 'pointing', 'neutral'),
                 (610, 290, 'standing', 'worried'),
                 (820, 278, 'standing', 'neutral'),
                 (1030, 265, 'standing', 'deadpan'),
                 (1240, 250, 'standing', 'neutral'))
        for k, (qx, qh, qp, qe) in enumerate(QUEUE):
            # a few px of baseline jitter so the feet are not a ruled line
            SC.fullbody(d, qx, 700 + (4 if k % 2 else -4), qh, pose=qp,
                        expression=qe, seed=650 + k)
        # label rides high on the concrete lintel, clear of the queue below and
        # the caption beneath -- it was at y=612 before and cut through them
        D.draw_label(tile, 'open to visitors', center=(640, 196), color=INK,
                     size=40, outline=None, outline_w=0)
    els.append(card(22, 23, c_other_bunker, kind='character'))
    els.append(cap(22, W // 2, 686, size=32, fill=RED))

    # ===== b23  this one has never been filmed inside ==================== #
    def c_never_filmed(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 651, (130, 130, 126), floor=None)
        # the shut door, cropped hard left. Widened to 1100 so its right-hand
        # edge (x=850) exits past the title band rather than drawing a hard
        # vertical INK line across it; still cropped hard on the left.
        _blast_door(d, 300, 340, 1100, 760, 652, wheel=True, plates=3)
        # The visitor line, CUT OFF at the RIGHT frame edge -- it stops here. Same
        # measured geometry as b22: standing is the only narrow pose, so the
        # spacing (200) is opened past its 175px reach at 330px tall rather than
        # reaching for armscrossed, which is the widest pose in the table.
        for k, (qx, qh, qp) in enumerate(((840, 320, 'standing'),
                                          (1040, 300, 'standing'),
                                          (1240, 282, 'peeking'))):
            _figure(d, qx, 700, qh, pose=qp, expression='neutral',
                    seed=653 + k)
        PA.hand_stroke(d, [(760, 120), (760, 720)], RED, 10, closed=False,
                       seed=660, wavelength=170.0)
        D.draw_label(tile, 'never filmed inside', center=(980, 130),
                     color=INK, size=40, outline=None, outline_w=0)
    els.append(card(23, 24, c_never_filmed, kind='character'))
    els.append(cap(23, W // 2, 672, size=32, fill=RED))

    # ===== b24  satellite images show only the surface =================== #
    def c_satellite(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 62, 84), seed=671, value=0.08)
        PA.paper_overlay(tile, seed=672)
        # lit course at the head so the near-black title reads; the sky is too
        # dark on its own once the rooftop stack was moved below the band
        SC.title_backdrop(tile, 1671, col=(96, 98, 110))
        # a straight-down view: rooftops, trees, one wall -- no chamber.
        # The stack starts at y=96 rather than y=40: a rooftop band's top edge
        # is a light-on-dark wobbled line, and at y=40 that edge landed inside
        # the title band. Nine bands at 82 pitch still run off the bottom.
        for k in range(9):
            y = 96 + k * 82
            PA.fill_rect(tile, [-40, y, W + 40, y + 66], (108, 116, 108),
                         seed=673 + k, value=0.07)
        # The second block is the only one that reaches into the title column, so
        # it is the only one held down; the others clear the band sideways.
        for k, (x, y, w, h) in enumerate(((80, 80, 260, 130), (420, 108, 220, 150),
                                          (720, 100, 300, 120), (1060, 70, 200, 140))):
            PA.fill_poly(PA.img_of(d), [(x, y), (x + w, y - 8),
                                        (x + w - 10, y + h), (x + 6, y + h + 8)],
                         (166, 122, 100), seed=682 + k, value=0.08)
            PA.hand_stroke(d, [(x, y), (x + w, y - 8), (x + w - 10, y + h),
                               (x + 6, y + h + 8)], INK, 5, closed=True,
                           seed=686 + k, wavelength=90.0)
        for k, x in enumerate((340, 690, 1040)):
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(x, 330 + k * 40, 66, 58,
                                                      n=32), PARK_D,
                         seed=690 + k, value=0.09)
        # the camera frame: what the satellite CAN see, and nothing else.
        # The top edge is at y=112, not y=40. draw_red_box is a closed
        # hand_stroke with vary=0.32, so an edge nominally at y=40 wanders up
        # to y~16 and struck straight through the title -- the red datum line
        # the band gate flags.
        D.draw_red_box(tile, [100, 112, 1180, 690], width=7)
        D.draw_label(tile, 'surface only', center=(640, 380), color=SNOW,
                     size=48, outline=(24, 34, 48), outline_w=4)
    els.append(card(24, 25, c_satellite))
    els.append(cap(24, W // 2, 700, size=30, fill=SNOW))

    # ===== b25  the entrance sits behind an ordinary fence ================== #
    def c_fence_street(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 691, sky=(200, 206, 210), ground=(150, 150, 148))
        # an ordinary street: kerb, parked cars, a wall behind
        PA.fill_rect(tile, [-40, 470, W + 40, 560], (168, 168, 164), seed=692,
                     value=0.07)
        PA.hand_stroke(d, [(-40, 470), (W + 40, 466)], INK, 5, closed=False,
                       seed=693, wavelength=200.0)
        PA.fill_rect(tile, [-40, 560, W + 40, 760], (128, 128, 126), seed=694,
                     value=0.07)
        # the fence: dull, uncrowded, spanning the frame and running off it
        _fence(d, -30, W + 30, 500, 150, 695, col=(154, 156, 152))
        for k, x in enumerate((90, 560, 1050)):
            _car(d, x, 556, 190, 700 + k)
        # the caption carries "The entrance sits behind an ordinary fence", so
        # no second copy of "ordinary fence" is drawn on the art
    els.append(card(25, 26, c_fence_street))
    els.append(cap(25, W // 2, 682, size=32, fill=RED))

    # ===== b26  an ordinary fence on an ordinary street =================== #
    def c_ordinary_street(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # PULLED IN, not pulled back. The first version put the horizon at 500
        # with small trees, which left two thirds of the frame as empty sky and
        # read as an unfinished plate. The street is the subject, so the
        # camera is close: big trees cropped by the top edge, a tall fence, and
        # the pavement band across the bottom third.
        _sky(tile, 711, sky=(204, 210, 214), ground=(156, 156, 152),
             hz=int(H * 0.52))
        PA.fill_rect(tile, [-40, 372, W + 40, 520], (168, 168, 162), seed=712,
                     value=0.07)
        PA.fill_rect(tile, [-40, 520, W + 40, 760], (132, 132, 128), seed=713,
                     value=0.07)
        PA.hand_stroke(d, [(-40, 520), (W + 40, 516)], INK, 6, closed=False,
                       seed=717, wavelength=200.0)
        # big trees BEHIND the fence, crowns cropped by the top edge
        # The x=1006 tree is nudged right of the persistent title band: at 940
        # its crown (about 350px wide) reached back to x=730 and grew up
        # through the title. It is still cropped by the top edge, which is what
        # this card wants -- just not across the title.
        for k, x in enumerate((-40, 170, 1006, 1140, 1310)):
            _tree(d, x, 400, 420, 715 + k)
        # the fence, tall and close, running off both edges
        _fence(d, -30, W + 30, 540, 210, 714, col=(158, 160, 156))
        # a bus stop: pole and plate, big enough to read at this distance
        PA.hand_stroke(d, [(280, 540), (280, 250)], (90, 90, 94), 11,
                       closed=False, seed=720, wavelength=80.0)
        PA.fill_poly(PA.img_of(d), [(214, 246), (350, 240), (350, 336),
                                    (214, 342)], (68, 88, 128), seed=721,
                     value=0.07)
        PA.hand_stroke(d, [(214, 246), (350, 240), (350, 336), (214, 342)],
                       INK, 6, closed=True, seed=722, wavelength=70.0)
        # a bench, and a car at the kerb -- the mundane props
        seat = [(660, 540), (830, 536), (830, 578), (660, 582)]
        PA.fill_poly(PA.img_of(d), seat, (150, 132, 100), seed=723, value=0.07)
        PA.hand_stroke(d, seat, INK, 6, closed=True, seed=724, wavelength=60.0)
        _car(d, 380, 604, 250, 725)
        # No in-art label here. The caption at the bottom already reads "an
        # ordinary fence on an ordinary street", and a second copy of the same
        # words 60px above it collided into an unreadable double line.
    els.append(card(26, 27, c_ordinary_street))
    els.append(cap(26, W // 2, 700, size=32, fill=RED))

    # ===== b27  it ends at a set of steel doors =========================== #
    def c_entrance(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 731, sky=(198, 204, 208), ground=(154, 154, 150))
        PA.fill_rect(tile, [-40, 500, W + 40, 760], (150, 150, 146), seed=732,
                     value=0.07)
        # a brick wall running off the right edge
        wall = [(700, 210), (W + 40, 190), (W + 40, 520), (700, 520)]
        PA.fill_poly(PA.img_of(d), wall, BRICK, seed=733, value=0.08)
        PA.hand_stroke(d, [(700, 210), (W + 40, 190), (W + 40, 520),
                           (700, 520)], INK, 7, closed=True, seed=734,
                       wavelength=170.0)
        for r_ in range(7):
            y = 240 + r_ * 42
            PA.hand_stroke(d, [(700, y), (W + 40, y - 6)], (112, 84, 70), 3,
                           closed=False, seed=735 + r_, wavelength=140.0)
        # the fence line running left into it
        _fence(d, -30, 700, 520, 140, 742, col=(158, 160, 156))
        # THE steel doors, set into the wall, cropped by the top edge
        dr = [(830, 60), (1180, 40), (1180, 520), (830, 520)]
        PA.fill_poly(PA.img_of(d), dr, STEEL, seed=743, value=0.09)
        PA.hand_stroke(d, dr, INK, 9, closed=True, seed=744, wavelength=130.0)
        PA.hand_stroke(d, [(1005, 40), (1005, 520)], STEEL_D, 6, closed=False,
                       seed=745, wavelength=150.0)
        for side, cxk in ((-1, 918), (1, 1092)):
            PA.hand_stroke(d, [(cxk, 280), (cxk + side * 46, 280)], INK, 9,
                           closed=False, seed=746, wavelength=50.0)
        D.draw_label(tile, 'entrance', center=(1000, 600), color=INK,
                     size=42, outline=None, outline_w=0)
    els.append(card(27, 28, c_entrance))
    els.append(cap(27, W // 2, 678, size=32, fill=RED))

    # ===== b28  rumour says they open on a code ========================== #
    def c_keypad_camera(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (120, 118, 116), seed=751, value=0.08)
        PA.paper_overlay(tile, seed=752)
        # the wall, cropped everywhere
        for r_ in range(14):
            y = 40 + r_ * 52
            PA.hand_stroke(d, [(-40, y), (W + 40, y - 8)], (98, 96, 94), 3,
                           closed=False, seed=753 + r_, wavelength=170.0)
        # the steel door edge, cropped left. cx=120 puts the leaf's right-hand
        # stile at x=470, clear of the title band, so its full-height INK
        # edge line does not run down through the title.
        _blast_door(d, 120, 360, 700, 760, 767, wheel=False, plates=3)
        # the keypad beside the frame
        _keypad(d, 620, 400, 260, 340, 768, cols=3, rows=4)
        # a small camera on a stalk above it, looking down at whoever comes
        PA.hand_stroke(d, [(900, 240), (900, 130), (1030, 130)], INK, 8,
                       closed=False, seed=769, wavelength=70.0)
        cam = [(1030, 106), (1180, 118), (1180, 174), (1030, 162)]
        PA.fill_poly(PA.img_of(d), cam, (78, 84, 94), seed=770, value=0.08)
        PA.hand_stroke(d, cam, INK, 6, closed=True, seed=771, wavelength=60.0)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(1186, 146, 24, 22, n=18),
                     (26, 26, 30), seed=772, value=0.04)
        # the beam it watches with, drawn as a thin wedge
        PA.fill_poly(PA.img_of(d), [(1186, 146), (1290, 40), (1290, 300)],
                     (74, 78, 86), seed=773, value=0.06)
    els.append(card(28, 29, c_keypad_camera))
    els.append(cap(28, W // 2, 682, size=32, fill=SNOW))

    # ===== b29  no code has ever been published (character) =============== #
    def c_no_code(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 781, (54, 56, 62), floor=None)
        # lit course at the head so the near-black title reads on this dark card
        SC.title_backdrop(tile, 1781, col=(96, 98, 110))
        # the keypad filling the frame, cropped all round, keys unmarked.
        # cy=460 puts the panel's top edge at y=110, clear of the title band;
        # it still runs off the bottom edge and past both sides.
        _keypad(d, 700, 460, 760, 700, 782, cols=3, rows=4)
        # the character, cropped into the left, flat and unimpressed
        SC.closeup(d, 260, 340, 200, 'deadpan', 783)
        D.draw_bubble(tile, 'no code, ever', (620, 130), tail_to=(330, 250),
                      font_size=34, max_w=300)
        # No in-art label on this card. A blank strip with "no numbers" on it
        # was tried here and sat at y=670 against a caption at y=690 -- a 20px
        # gap between two text elements, which rendered as one unreadable
        # double line. The unmarked keypad IS the point of the card; the
        # bubble already carries the verdict.
    els.append(card(29, 30, c_no_code, kind='character'))
    els.append(cap(29, W // 2, 690, size=32, fill=SNOW))

    # ===== b30  the whole site is a system =============================== #
    def c_system(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 791, sky=(196, 202, 208), ground=(150, 150, 148))
        PA.fill_rect(tile, [-40, 480, W + 40, 760], (144, 146, 142), seed=792,
                     value=0.07)
        # the block as one drawn object: fence, door, chamber, sensors
        block = [(120, 170), (1160, 150), (1210, 500), (90, 520)]
        PA.fill_poly(PA.img_of(d), block, (176, 176, 170), seed=793,
                     value=0.07)
        PA.hand_stroke(d, block, INK, 7, closed=True, seed=794, wavelength=180.0)
        _fence(d, 100, 1200, 500, 120, 795, col=(150, 152, 148), rail=True)
        # the chamber below, cropped by the bottom edge
        PA.fill_poly(PA.img_of(d), [(420, 520), (900, 512), (960, 760),
                                    (380, 760)], DARK, seed=796, value=0.09)
        PA.hand_stroke(d, [(420, 520), (900, 512), (960, 760)], INK, 8,
                       closed=False, seed=797, wavelength=160.0)
        for k, x in enumerate((200, 400, 900, 1100)):
            _sensor(d, x, 470, 26, 800 + k)
        # the ONE dashed line that ties the whole site together
        for k in range(22):
            t0 = k / 22.0
            t1 = t0 + 0.5 / 22.0
            if t0 < 0.5:
                p0 = (120 + t0 * 2 * 1040, 470)
                p1 = (120 + t1 * 2 * 1040, 470)
            else:
                u = (t0 - 0.5) / 0.5
                p0 = (1160 - u * 240, 470 + u * 250)
                p1 = (1160 - (t1 - 0.5) / 0.5 * 240, 470 + (t1 - 0.5) / 0.5 * 250)
            PA.hand_stroke(d, [p0, p1], RED, 5, closed=False, seed=810 + k,
                           wavelength=50.0, vary=0.1)
        D.draw_label(tile, 'one system', center=(640, 600), color=INK,
                     size=42, outline=None, outline_w=0)
    els.append(card(30, 31, c_system))
    els.append(cap(30, W // 2, 678, size=32, fill=RED))

    # ===== b31  a line of sensors ringing the block ====================== #
    def c_sensor_ring(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _night(tile, 821, sky=(40, 48, 62), ground=(32, 36, 44))
        # lit course at the head so the near-black title reads on this night card
        SC.title_backdrop(tile, 1821, col=(96, 98, 110))
        # the block in plan, small and dark, ringed by the sensor line
        block = [(430, 300), (850, 292), (880, 460), (410, 468)]
        PA.fill_poly(PA.img_of(d), block, (58, 60, 68), seed=822, value=0.07)
        PA.hand_stroke(d, block, (108, 112, 122), 6, closed=True, seed=823,
                       wavelength=120.0)
        # sensors spaced around it on a ring, each with its antenna
        for k in range(11):
            a = math.radians(-96 + k * 19.2)
            sx = 640 + math.cos(a) * 480
            sy = 400 + math.sin(a) * 250
            _sensor(d, sx, sy, 22, 830 + k, lit=False)
        # the connecting line, dim red, all the way round
        pts = []
        for k in range(49):
            a = math.radians(-96 + k * 4.0)
            pts.append((640 + math.cos(a) * 480, 400 + math.sin(a) * 250))
        for k in range(0, 48, 2):
            PA.hand_stroke(d, [pts[k], pts[k + 1]], (128, 52, 50), 5,
                           closed=False, seed=850 + k, wavelength=50.0,
                           vary=0.1)
        # No in-art label here. "ringing the block" sat 30px above a caption
        # that already says "A line of sensors ringing the block" -- two text
        # elements 30px apart render as one line, and the duplication made it
        # worse. The sensor ring reads on its own.
    els.append(card(31, 32, c_sensor_ring))
    els.append(cap(31, W // 2, 690, size=32, fill=SNOW))

    # ===== b32  something out there is still listening ====================== #
    # STILL, like every other card. A pulsing lamp was tried here -- it is the
    # one beat whose narration invites motion ("STILL listening") -- but
    # engine3's `motion` is a list of (t,x,y,scale,rot) keyframes, not a name,
    # and the reference measures 96% still with hard cuts (memory:
    # cadence-must-be-compared-at-same-fps). The "listening" reads off the
    # radiating rings and the lit lamp instead, which is also what the
    # still-frame critic can actually judge.
    def c_listening(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _night(tile, 861, sky=(30, 34, 44), ground=(24, 26, 32))
        # lit course at the head so the near-black title reads on this night card
        SC.title_backdrop(tile, 1861, col=(96, 98, 110))
        # the sensor box, close, filling the left of frame
        s = 120
        PA.fill_poly(PA.img_of(d), [(300 - s, 300), (300 + s, 300),
                                    (300 + s, 480), (300 - s, 480)],
                     CONCRETE_D, seed=862, value=0.08)
        PA.hand_stroke(d, [(300 - s, 300), (300 + s, 300), (300 + s, 480),
                           (300 - s, 480)], INK, 8, closed=True, seed=863,
                       wavelength=90.0)
        PA.hand_stroke(d, [(330, 300), (330, 120)], INK, 7, closed=False,
                       seed=864, wavelength=60.0)
        # THE RED LAMP, lit, with a soft glow
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(300, 390, 132, 132, n=34),
                     (104, 36, 34), seed=865, value=0.10)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(300, 390, 46, 46, n=26),
                     RED, seed=866, value=0.05)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(300, 390, 18, 18, n=16),
                     (250, 178, 156), seed=867, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(300, 390, 46, 46, n=26), INK, 6,
                       closed=True, seed=868, wavelength=50.0)
        # sound rings leaving it -- three dashed rings, widening. The spacing is
        # 75, not 140: at 140 the outer ring's crown crossed the title band
        # between x=484 and x=796, which is the red datum line the band gate
        # flags. At 75 the widest ring clears the band by ~30px at its highest
        # point inside the title column.
        for k in range(3):
            rr = 190 + k * 75
            ring = PA.ellipse_pts(300, 390, rr, rr, n=40)
            for j in range(0, 40, 2):
                PA.hand_stroke(d, [ring[j], ring[(j + 1) % 40]],
                               (118, 48, 46), 5, closed=False,
                               seed=870 + k * 20 + j, wavelength=50.0,
                               vary=0.15)
        # what it is listening TO: the block, dark, on the right
        block = [(760, 250), (1180, 236), (1220, 470), (740, 484)]
        PA.fill_poly(PA.img_of(d), block, (44, 46, 54), seed=880, value=0.07)
        PA.hand_stroke(d, block, (96, 100, 110), 6, closed=True, seed=881,
                       wavelength=140.0)
        D.draw_label(tile, 'still listening', center=(960, 556), color=SNOW,
                     size=42, outline=(20, 22, 28), outline_w=4)
    els.append(card(32, 33, c_listening))
    els.append(cap(32, W // 2, 682, size=32, fill=SNOW))

    # ===== b33  the system may have outlived its builder ================= #
    def c_outlived(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 891, sky=(190, 196, 200), ground=(146, 146, 142))
        PA.fill_rect(tile, [-40, 500, W + 40, 760], (140, 140, 136), seed=892,
                     value=0.07)
        # the block, but eaten: rust patches, weeds, the fence half gone
        block = [(120, 180), (1160, 160), (1210, 500), (90, 520)]
        PA.fill_poly(PA.img_of(d), block, (160, 152, 140), seed=893,
                     value=0.08)
        PA.hand_stroke(d, block, INK, 7, closed=True, seed=894, wavelength=190.0)
        for k in range(16):
            rx = 150 + (k * 71) % 980
            ry = 200 + (k * 53) % 280
            PA.fill_poly(PA.img_of(d), PA.ellipse_pts(rx, ry, 30 + (k % 4) * 14,
                                                      18 + (k % 3) * 8, n=18),
                         (138, 92, 62), seed=895 + k, value=0.09)
        # weeds breaking through, densest at the edges
        for k in range(22):
            wx = 40 + (k * 67) % 1220
            PA.hand_stroke(d, [(wx, 520), (wx - 8 + (k % 3) * 8, 452),
                               (wx + 12 - (k % 4) * 8, 424)], (86, 104, 66),
                           5, closed=False, seed=912 + k, wavelength=50.0,
                           vary=0.4)
        _fence(d, 100, 700, 500, 110, 935, col=(142, 140, 132))
        # the dashed line still running through the decay -- it still works
        for k in range(16):
            x0 = 120 + k * 62
            PA.hand_stroke(d, [(x0, 478), (x0 + 34, 478)], RED, 5,
                           closed=False, seed=940 + k, wavelength=50.0,
                           vary=0.1)
        D.draw_label(tile, 'still running', center=(1000, 600), color=INK,
                     size=40, outline=None, outline_w=0)
    els.append(card(33, 34, c_outlived))
    els.append(cap(33, W // 2, 680, size=32, fill=RED))

    # ===== b34  under the park, a red light waits ======================== #
    def c_red_light(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (24, 30, 44), seed=951, value=0.08)
        PA.paper_overlay(tile, seed=952)
        # lit course at the head so the near-black title reads on this night card
        SC.title_backdrop(tile, 1951, col=(96, 98, 110))
        # the park at night, cross-section, running off both edges
        PA.fill_rect(tile, [0, 240, W, 300], PARK_D, seed=953, value=0.09)
        PA.hand_stroke(d, [(-20, 248), (W + 20, 242)], (36, 58, 40), 5,
                       closed=False, seed=954, wavelength=200.0)
        for k, x in enumerate((120, 340, 980, 1180)):
            _tree(d, x, 244, 170, 955 + k, col=(38, 62, 44))
        _strata(d, 960, 320, 620, n=3,
                cols=[(46, 44, 42), (38, 36, 36), (50, 48, 46), (34, 32, 32)])
        # the chamber, and the ONE red light in it
        ch = [(360, 500), (960, 490), (1050, 760), (300, 760)]
        PA.fill_poly(PA.img_of(d), ch, (20, 21, 26), seed=966, value=0.09)
        PA.hand_stroke(d, [(360, 500), (960, 490), (1050, 760)], INK, 8,
                       closed=False, seed=967, wavelength=170.0)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(660, 570, 300, 300, n=40),
                     (96, 32, 30), seed=968, value=0.10)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(660, 570, 96, 96, n=28),
                     RED, seed=969, value=0.05)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(660, 570, 34, 34, n=20),
                     (250, 170, 150), seed=970, value=0.05)
        PA.hand_stroke(d, [(660, 490), (660, 420)], (60, 62, 70), 8,
                       closed=False, seed=971, wavelength=60.0)
    els.append(card(34, 35, c_red_light))
    els.append(cap(34, W // 2, 690, size=32, fill=RED))

    # ===== b35  Russia has never confirmed what remains =================== #
    def c_no_confirmation(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], PAPERW, seed=981, value=0.06)
        PA.paper_overlay(tile, seed=982)
        desk = [(-40, 540), (W + 40, 540), (W + 40, 760), (-40, 760)]
        PA.fill_poly(PA.img_of(d), desk, (128, 106, 80), seed=983, value=0.08)
        PA.hand_stroke(d, [(-40, 540), (W + 40, 540)], INK, 7, closed=False,
                       seed=984, wavelength=200.0)
        # an official document, filling the frame and cropped left and right
        doc = [(100, 120), (1180, 108), (1210, 560), (80, 574)]
        PA.fill_poly(PA.img_of(d), doc, (246, 244, 238), seed=985, value=0.05)
        PA.hand_stroke(d, doc, INK, 6, closed=True, seed=986, wavelength=180.0)
        for k in range(9):
            y = 180 + k * 34
            PA.hand_stroke(d, [(160, y), (1120 - (k % 3) * 180, y - 6)],
                           (126, 126, 130), 4, closed=False, seed=987 + k,
                           wavelength=130.0)
        # the one line that matters, left BLANK
        PA.fill_poly(PA.img_of(d), [(160, 480), (900, 476), (900, 508),
                                    (160, 512)], (238, 236, 230), seed=996,
                     value=0.04)
        PA.hand_stroke(d, [(160, 496), (900, 492)], RED, 6, closed=False,
                       seed=997, wavelength=110.0)
        D.draw_label(tile, 'left blank', center=(1030, 470), color=RED,
                     size=34, outline=None, outline_w=0)
    els.append(card(35, 36, c_no_confirmation))
    els.append(cap(35, W // 2, 680, size=32, fill=RED))

    # ===== b36  no one has gone down in decades ========================== #
    def c_empty_helmet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark_bg(tile, 1001, (32, 34, 40), floor=606)
        # lit course at the head so the near-black title reads on this dark card
        SC.title_backdrop(tile, 2001, col=(96, 98, 110))
        # one chair, cropped at the left, and on it an empty helmet
        chair = [(-40, 380), (330, 372), (350, 606), (-40, 606)]
        PA.fill_poly(PA.img_of(d), chair, (56, 58, 66), seed=1002, value=0.08)
        PA.hand_stroke(d, [(-40, 380), (330, 372), (350, 606), (-40, 606)],
                       INK, 8, closed=True, seed=1003, wavelength=140.0)
        PA.fill_poly(PA.img_of(d), [(150, 620), (196, 620), (190, 720),
                                    (156, 720)], (48, 50, 58), seed=1004,
                     value=0.07)
        # the helmet: a dome with a dark visor, nothing behind it
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(150, 356, 96, 104, n=36),
                     (108, 114, 124), seed=1005, value=0.08)
        PA.hand_stroke(d, PA.ellipse_pts(150, 356, 96, 104, n=36), INK, 7,
                       closed=True, seed=1006, wavelength=80.0)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(150, 380, 78, 62, n=32),
                     (24, 26, 32), seed=1007, value=0.05)
        PA.hand_stroke(d, [(100, 348), (204, 340)], (154, 160, 170), 6,
                       closed=False, seed=1008, wavelength=70.0)
        # decades of dust: horizontal fall-lines, nothing moving
        for k in range(16):
            x = 420 + (k * 79) % 780
            PA.hand_stroke(d, [(x, 150 + (k % 5) * 90), (x + 6, 250 + (k % 4) * 90)],
                           (54, 56, 62), 4, closed=False, seed=1010 + k,
                           wavelength=60.0, vary=0.3)
        D.draw_label(tile, 'decades', center=(800, 320), color=(120, 122, 130),
                     size=44, outline=None, outline_w=0)
    els.append(card(36, 37, c_empty_helmet))
    els.append(cap(36, W // 2, 686, size=32, fill=SNOW))

    # ===== b37  the door is still shut, and still waiting ================ #
    def c_finale(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DARKER, seed=1021, value=0.11)
        PA.paper_overlay(tile, seed=1022)
        # the door, cropped by every edge, and the red lamp beside it
        _blast_door(d, 560, 380, 980, 940, 1023, wheel=True, plates=4,
                    lamp=False, seam_floor=96)
        # the red lamp: SMALL and set into the door edge like a status light.
        # The first pass used a 210px glow and it read as a giant red disc
        # owning half the frame -- the accent has to be rationed (see palette).
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(880, 430, 96, 96, n=32),
                     (84, 32, 30), seed=1027, value=0.10)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(880, 430, 30, 30, n=24),
                     RED, seed=1028, value=0.05)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(880, 430, 13, 13, n=16),
                     (250, 178, 156), seed=1029, value=0.05)
        # the character, cream on the dark, cropped by the RIGHT edge, standing
        # back from the light. Drawn AFTER the lamp so the glow rims him.
        _figure(d, 1120, 720, 430, pose='standing', expression='worried',
                seed=1024)
        # the jamb, closing the frame on the right and cropping him into it
        jamb = [(1236, -40), (W + 60, -40), (W + 60, 760), (1236, 760)]
        PA.fill_poly(PA.img_of(d), jamb, (58, 60, 68), seed=1031, value=0.09)
        PA.hand_stroke(d, [(1236, -40), (1236, 760)], INK, 10, closed=False,
                       seed=1032, wavelength=210.0)
        D.draw_label(tile, 'still shut', center=(360, 610), color=RED,
                     size=42, outline=(20, 20, 24), outline_w=4)
    els.append(card(37, 38, c_finale, kind='character'))
    els.append(cap(37, W // 2, 686, size=32, fill=SNOW))

    return SC.finish(els, TITLE, clock, title_seed=39)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))