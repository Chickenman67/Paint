"""tomb2_scene -- the PERSISTENT-STAGE rebuild of chapter 3 (the Tomb).

WHY THIS FILE EXISTS. tomb_scene.py (v1) was built on "one card per beat, each
card paints its own whole frame". Its `card(i, j, draw, ...)` helper gave every
beat a complete background-to-subject repaint, so nothing survived between
beats: 45 full-frame repaints in 118s, a new image every ~2.6s, and a caption
on EVERY one of the 45 beats (100% text density). Nothing ever moved.

THE MODEL HERE. Nine PERSISTENT STAGES instead of 45 short cards, grouped on the
narration's own acts (work3/plans/STAGE_PLANS.md):

    A  b01-b05  eight thousand clay soldiers; the Terracotta Army name
    B  b06-b10  six hundred horses; long rows; all guarding one man
    C  b11-b16  Qin Shi Huang; first emperor; one script, one ruler
    D  b17-b20  burned the books; the scholars; forced labour
    E  b21-b25  the mound copied a pyramid; outside Xi'an; no two the same
    F  b26-b31  vanished 2,000 years; 1974 farmers; a clay shoulder; covered
    G  b32-b37  2012 pit; bronze cranes; the 1983 acid attack
    H  b38-b42  mercury in the soil; enough for a pool; a slow poison
    I  b43-b45  the main chamber never opened; still sealed; finale

Inside a stage the art ACCUMULATES: a layer that arrives stays until the stage
turns over (SC.accrue), so the viewer watches a place GAIN things -- a rank
building up, a horse stepping into the pit, the seal going on the door.

TWO RULES CARRIED OVER FROM THE PINES GAP PILOT, both measured there.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Scenery accumulates; anything
   carrying text, and anything occupying the same part of the frame as something
   already there, REPLACES. tomb is the chapter where that matters most: the
   soldier ranks are the world and they accrue, while every name/number/label
   ('8,000', '600 HORSES', 'ONE MAN', 'QIN SHI HUANG', 'EVERY BOOK', '246 BC',
   'COPIED A PYRAMID', 'HEAVENLY PALACE', 'ALL DIFFERENT', 'NO TWO THE SAME',
   '2,000 YEARS', '1974', 'SOMETHING HARD', 'IT BROKE', 'COVERED OVER',
   'BOTH BROKEN', 'REPAIRED...', 'ACID', 'MERCURY', 'ENOUGH FOR A POOL',
   'THE OLD RECORDS', 'POISON', 'IT DOES NOT LET GO', 'NEVER OPENED',
   'THE DOOR STAYS SHUT') is a hand-off chain -- each one lives until the next
   one starts, so the top of the frame carries exactly one label at a time
   instead of a stack.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces a motion rate the
   reference does not have and every moving frame trips the picture-change
   counter -- which is worse than the churn this rebuild exists to remove. The
   reference is ~83% still frames. So TWELVE arrivals move, briefly
   (0.5-0.55s), and each is a SMALL subject: one clay soldier rising out of
   the cut, the presenter stepping in, a bronze shovel, the acid pouring, the
   mercury bead settling, two lines of carriers. The soldier RANKS, the horse,
   the emperor and every backdrop are still. Popping in IS the reveal; sliding
   is for the handful of moments where movement carries meaning.

CAPTIONS. 17 of 45 beats (38%), no two consecutive. The rule applied per beat:
keep the words when they carry something the drawn art does not -- the name
Terracotta Army, Qin Shi Huang, 221 BC, one script, that one ruler, the
scholars, forced labour, 1974, the clay shoulder, 2012, the acid, mercury,
the poison, the sealed chamber, the finale. DROP the beat when the art already
says it, and say so in a comment at the drop site. Examples: b06 "eight
thousand soldiers in the dark" is the rank standing there in a black pit;
b39 "enough to fill a pool" is a pool running off the left edge with the words
ENOUGH FOR A POOL drawn on it; b34's two broken cranes carry BOTH BROKEN.
A drawn label and a caption saying the same thing is still text pile-up.

CHARACTER. The presenter appears in four stages -- A (closeup, confused, then
shocked at the paint), D (full body recoiling at the scholars' pit), F (closeup
confused at 1974, swapping to shock when the clay shoulder comes up), I (full
body awed at the sealed door) -- and changes expression once inside a stage
twice, via SC.expr_swap, because the expression is baked into the rasterised
tile at build time and a change therefore needs two elements at one position.

Run:  python lib/tomb2_scene.py --preview --video
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import engine3 as E3
import scene_common as SC
import v2paint as PA
import v2draw as D
import tomb_scene as TB     # art primitives + palette, reused not copied

# --- contract with the rest of the pipeline (imported from v1) -------------
SEG = TB.SEG
TITLE = TB.TITLE
BEATS = TB.BEATS
TITLE_BACKDROP = TB.TITLE_BACKDROP

W, H = TB.W, TB.H

# --- palette, reused verbatim from v1. Two registers, exactly as before. ----
INK = TB.INK
CLAY = TB.CLAY
CLAY_D = TB.CLAY_D
CLAY_L = TB.CLAY_L
EARTH = TB.EARTH
EARTH_D = TB.EARTH_D
PIT = TB.PIT
PALE = TB.PALE
GOLD = TB.GOLD
FIRE = TB.FIRE
BRONZE = TB.BRONZE
PAPER2 = TB.PAPER2
BLUE = TB.BLUE
BLUE_L = TB.BLUE_L
ACID = TB.ACID
GREY = TB.GREY
GREY_D = TB.GREY_D
SILVER = TB.SILVER
HZ = TB.HZ

# --- art primitives, reused verbatim from v1 (aliased, never copied) -------
_pit = TB._pit
_earth_field = TB._earth_field
_interior = TB._interior
_soldier = TB._soldier
_horse = TB._horse
_china = TB._china
_script_sheet = TB._script_sheet

# The v1 map's landmass fill is (226,222,208) on a PAPER2 page of (236,234,226):
# ten values apart. Measured on the rendered b11 frame the landmass was
# indistinguishable from the page, so a map that fills 70% of the frame read
# as a shapeless pale blob -- the beat was "here is the empire he took" and
# there was no visible empire. Same outline, landmass drawn in a warm sand
# that separates from the page by ~60 values, with a heavier outline.
_MAP_SHAPE = [(-330, -110), (-250, -215), (-120, -240), (-20, -200),
              (110, -235), (250, -190), (320, -80), (300, 60), (250, 190),
              (120, 235), (-30, 210), (-160, 240), (-290, 170), (-345, 20)]


def _china2(d, cx, cy, s, seed, kingdoms=False, unify=False):
    """The v1 landmass outline, re-filled so it reads against the page."""
    outline = [(cx + px * s, cy + py * s) for px, py in _MAP_SHAPE]
    PA.fill_poly(PA.img_of(d), outline, (206, 186, 148), seed=seed, value=0.07)
    PA.hand_stroke(d, outline, INK, 7, closed=True, seed=seed + 1,
                   wavelength=190.0)
    if kingdoms:
        for k in range(9):
            px = cx - 300 * s + (k * 251) % (560 * s)
            py = cy - 190 * s + (k * 137) % (360 * s)
            w = 70 * s + (k % 3) * 22 * s
            h = 60 * s + (k % 4) * 18 * s
            PA.fill_rect(PA.img_of(d), [px, py, px + w, py + h],
                         (178, 84, 66), seed=seed + 10 + k, value=0.08,
                         edge=2.0)
    elif unify:
        PA.fill_poly(PA.img_of(d), outline, (204, 96, 70), seed=seed + 2,
                     value=0.07)
        PA.hand_stroke(d, outline, INK, 7, closed=True, seed=seed + 3,
                       wavelength=190.0)
_weight = TB._weight
_throne = TB._throne
_flames = TB._flames
_book = TB._book
_crane = TB._crane

# Every moving element uses this one duration. 0.45-0.6s reads as a deliberate
# move; longer and the picture starts changing every sampled frame, which is the
# defect this whole rebuild exists to remove.
ARRIVE = 0.52

# =========================================================================== #
# STRUCTURE HELPERS -- added for the frame-fill / edge-density pass.          #
#                                                                             #
# WHY THESE EXIST. A per-beat pigment measurement (24px-tile luma std on       #
# rendered frames) called 35 of 45 beats "flat". Eye-confirmed, the governing   #
# problem is COMPOSITION, not the paint engine: a few LARGE SMOOTH shapes with  #
# dead space around them. The beats that score high do so by stacking MANY     #
# small outlined shapes (fortknox's gold-slab frame scores 53 because it stacks #
# ~40 small outlined slabs). "Flat" here means big smooth voids. So the fix is  #
# STRUCTURE: stamp edge-rich detail -- masonry courses, rammed-earth terraces,  #
# paving slabs, rubble, contour bands -- into the large regions. Every helper    #
# is deterministic (seeded) and paints through v2paint, so the fills keep their  #
# value drift + brush banding. Nothing here raises paint constants or rewrites   #
# v2paint; it changes what is DRAWN, not how.                                  #
# =========================================================================== #


def _stone_courses(tile, d, x0, y0, x1, y1, seed, col, mortar=None,
                   row_h=54):
    """A masonry wall: horizontal courses of rectangular blocks, mortared.

    This is the workhorse for turning any big wall into edge-rich structure.
    Each course is split into blocks at seeded, varied joints; every block is
    filled with a per-block tone near `col` and outlined in INK, so a 400x600
    smooth wall becomes ~50 small outlined rectangles. That is the difference
    between a flat field and a built structure.
    """
    mortar = mortar or tuple(max(0, c - 34) for c in col)
    y = float(y0)
    r = 0
    while y < y1 - 4:
        rh = row_h * (0.85 + ((r * 37) % 40) / 100.0)   # varied course height
        yb = min(y + rh, y1)
        # seeded joint positions across this course
        x = float(x0)
        while x < x1 - 6:
            seg = 90 + ((seed + r * 13 + int(x)) * 57) % 130   # 90-220 wide
            xe = min(x + seg, x1)
            tone = tuple(min(255, max(0, cc + (((seed + r * 7 + int(x)) * 29)
                                              % 26) - 13))
                         for cc in col)
            box = [x + 3, y + 3, xe - 3, yb - 3]
            if box[2] - box[0] > 10 and box[3] - box[1] > 10:
                PA.fill_rect(tile, box, tone, seed=seed + r * 31 + int(x),
                             value=0.09, edge=1.6)
                PA.hand_stroke(d, [(box[0], box[1]), (box[2], box[1]),
                                   (box[2], box[3]), (box[0], box[3])],
                               INK, 3, closed=True, seed=seed + r * 17 + int(x),
                               wavelength=90.0)
            x = xe
        # mortar course line
        PA.hand_stroke(d, [(x0, yb - 1), (x1, yb - 1)], mortar, 4, closed=False,
                       seed=seed + 200 + r, wavelength=140.0)
        y = yb + 2
        r += 1


def _terraces(tile, d, cx, top_y, base_y, half_top, half_base, seed,
              col, n=8, shade=None):
    """Stacked rammed-earth courses: the mound / berm read as built, not smooth.

    n trapezoid bands from the base up, each inset toward the apex, each filled
    and outlined. Between bands the darker `shade` shows as the terrace riser, so
    the mound carries real contour structure and edge density instead of one big
    smooth triangle.
    """
    shade = shade or tuple(max(0, c - 30) for c in col)
    for k in range(n):
        t0 = k / float(n)
        t1 = (k + 1) / float(n)
        # interpolate half-width and y from base (t=0) to apex (t=1)
        yb = base_y - (base_y - top_y) * t0
        yt = base_y - (base_y - top_y) * t1
        wb = half_base + (half_top - half_base) * t0
        wt = half_base + (half_top - half_base) * t1
        quad = [(cx - wb, yb), (cx + wb, yb), (cx + wt, yt), (cx - wt, yt)]
        tone = col if k % 2 == 0 else shade
        PA.fill_poly(tile, quad, tone, seed=seed + k * 7, value=0.09,
                     tint=0.0, band=0.0, edge=1.4)
        PA.hand_stroke(d, quad, INK, 4, closed=True, seed=seed + k * 11,
                       wavelength=150.0)


def _rubble(tile, d, box, n, seed, col, rmin=9, rmax=26):
    """Scattered small chunks on a floor: many small outlined blobs.

    Deterministic positions from the seed. Each is a small irregular polygon,
    filled + outlined, so it reads as loose stone/clay debris and lifts the local
    edge density of an otherwise flat floor.
    """
    x0, y0, x1, y1 = box
    for k in range(n):
        rx = x0 + ((seed + k * 53) * 71) % max(1, int(x1 - x0))
        ry = y0 + ((seed + k * 97) * 43) % max(1, int(y1 - y0))
        rr = rmin + ((seed + k * 29) % (rmax - rmin))
        pts = []
        sides = 5 + (k % 3)
        for s in range(sides):
            a = 6.283185 * s / sides + (k * 0.7)
            rad = rr * (0.7 + 0.5 * (((seed + k * 7 + s * 13) % 10) / 10.0))
            pts.append((rx + rad * math.cos(a), ry + rad * 0.72 *
                        math.sin(a)))
        tone = tuple(min(255, max(0, c + (((seed + k) * 17) % 22) - 11))
                     for c in col)
        PA.fill_poly(tile, pts, tone, seed=seed + k * 5, value=0.10, edge=1.2)
        PA.hand_stroke(d, pts, INK, 3, closed=True, seed=seed + k * 9 + 1,
                       wavelength=60.0)


def _slab_floor(tile, d, y0, y1, seed, col, n=10, x0=-40, x1=W + 40,
                row_h=42):
    """A paving-slab floor: a grid of small outlined rectangles receding.

    Two or three joint rows make each slab a distinct outlined rect, which is
    what turns a flat ground band into a surface with visible local detail.
    """
    x = float(x0)
    c = 0
    while x < x1:
        seg = 130 + ((seed + c * 29) % 90)
        xe = x + seg
        tone = col if c % 2 == 0 else tuple(max(0, cc - 14) for cc in col)
        PA.fill_rect(tile, [x + 2, y0, xe - 2, y1], tone, seed=seed + c,
                     value=0.09, edge=1.8)
        PA.hand_stroke(d, [(x + 2, y0), (x + 2, y1)], INK, 4, closed=False,
                       seed=seed + c * 3 + 1, wavelength=70.0)
        # one horizontal joint mid-slab
        ym = (y0 + y1) * 0.5
        PA.hand_stroke(d, [(x + 2, ym), (xe - 2, ym)], INK, 3, closed=False,
                       seed=seed + c * 5 + 2, wavelength=60.0)
        x = xe
        c += 1
    PA.hand_stroke(d, [(x0, y0), (x1, y0)], INK, 5, closed=False,
                   seed=seed + 900, wavelength=200.0)


def _panel_grid(tile, d, x0, y0, x1, y1, seed, col, nx, ny, w_line=4):
    """A full grid of outlined panels -- tunnel walls, plan corridors, lab walls.

    Cheaper and more regular than _stone_courses; use where the surface reads as
    panelled (a survey plan, a lab bench wall) rather than as rough masonry.
    """
    for r in range(ny):
        ya = y0 + (y1 - y0) * r / float(ny)
        yb = y0 + (y1 - y0) * (r + 1) / float(ny)
        for c in range(nx):
            xa = x0 + (x1 - x0) * c / float(nx)
            xb = x0 + (x1 - x0) * (c + 1) / float(nx)
            tone = col if (r + c) % 2 == 0 else tuple(max(0, cc - 12)
                                                     for cc in col)
            PA.fill_rect(tile, [xa + 2, ya + 2, xb - 2, yb - 2], tone,
                         seed=seed + r * 17 + c, value=0.08, edge=1.2)
            PA.hand_stroke(d, [(xa + 2, ya + 2), (xb - 2, ya + 2),
                               (xb - 2, yb - 2), (xa + 2, yb - 2)],
                           INK, w_line, closed=True,
                           seed=seed + r * 23 + c * 3, wavelength=80.0)


def _contour_bands(tile, d, x0, x1, y_base, seed, cols, n=6, h=54,
                   amp=26):
    """Layered contour bands stacked from a baseline -- terrain / sky relief.

    Each band is a low rolling ridge (a hand-wobbled polyline) filled to the next
    band up, so a flat sky or field gets organic layered relief instead of one
    smooth expanse.
    """
    y = y_base
    for k in range(n):
        pts = [(x0, y)]
        steps = 14
        for s in range(steps + 1):
            fx = x0 + (x1 - x0) * s / float(steps)
            wob = amp * math.sin((s * 1.7 + k * 2.3 + seed * 0.01)
                                 % 6.283185)
            wob += (amp * 0.5) * (((seed + k * 13 + s * 7) % 10) / 10.0
                                  - 0.5)
            pts.append((fx, y + wob * 0.35))
        top = y - h
        PA.fill_poly(tile, pts + [(x1, top), (x0, top)], cols[k % len(cols)],
                     seed=seed + k * 9, value=0.08, tint=0.0, band=0.0, edge=2.0)
        PA.hand_stroke(d, pts, INK, 4, closed=False, seed=seed + k * 4 + 1,
                       wavelength=140.0)
        y -= h


def _hatch(tile, d, poly, seed, col, spacing=15, width=3, angle=0.62,
           wd=6):
    """Parallel hatching clipped to a polygon -- the survey/geology convention,
    and the only thing that moves the MEDIAN tile.

    WHY THIS EXISTS AND WHY SMALL SHAPES WERE NOT ENOUGH. The pigment gate is a
    MEDIAN over 24px tiles, so a frame only clears the bar when more than half
    its tiles straddle an edge. A lattice of 90x70 outlined cells does not do
    that: each cell leaves a 24px tile at its centre that is pure flat fill, so
    the median stays at the fill's own drift and the frame reads flat no matter
    how many cells it stacks. Hatching puts an edge every `spacing` px, so a 24px
    tile holds one or two of them and every tile in the region gets real spread.
    That is why the fortknox gold-slab frame scores 53 -- its slabs are small
    enough that most tiles touch a mortar line.

    Lines are clipped by testing sample points against the polygon, so hatching
    follows the shape it is filling rather than running through the frame.
    """
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)

    def inside(px, py):
        c = False
        n = len(poly)
        for i in range(n):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % n]
            if (ay > py) != (by > py):
                xint = ax + (py - ay) * (bx - ax) / float(by - ay)
                if px < xint:
                    c = not c
        return c

    ca, sa = math.cos(angle), math.sin(angle)
    diag = math.hypot(x1 - x0, y1 - y0)
    steps = int(diag / spacing) + 2
    for k in range(steps):
        off = k * spacing + ((seed * 7) % max(1, int(spacing)))
        run = []
        nhops = int(diag / float(wd)) + 2
        for s in range(nhops):
            # a point on the k-th line: walk along the line direction from the
            # polygon's top-left corner, offset perpendicular by `off`.
            ax0, ay0 = x0, y0
            t = s * wd
            px = ax0 + t * ca - off * sa
            py = ay0 + t * sa + off * ca
            if x0 - 2 <= px <= x1 + 2 and y0 - 2 <= py <= y1 + 2 and \
                    inside(px, py):
                run.append((px, py))
            else:
                if len(run) >= 2:
                    PA.hand_stroke(d, run, col, width, closed=False,
                                   seed=seed + k * 7, wavelength=120.0)
                run = []
        if len(run) >= 2:
            PA.hand_stroke(d, run, col, width, closed=False,
                           seed=seed + k * 7, wavelength=120.0)


def _cut_face(tile, d, x0, y0, x1, y1, seed, base, n=7):
    """An excavated earth face: stacked strata bands, each a different tone.

    A trench wall or a pit's cut side is the most common large surface in this
    chapter and the flattest. Real cuts band by soil layer, and each boundary is
    a wobbled line -- so the surface arrives already carrying horizontal
    contours and value steps, and the near band gets a rammed-earth course grid
    pressed into it. Layers are drawn top-down from `base` so a lower, darker
    stratum shows at each riser.
    """
    strata = (base,
              tuple(max(0, c - 16) for c in base),
              tuple(min(255, c + 18) for c in base),
              tuple(max(0, c - 30) for c in base),
              tuple(min(255, c + 8) for c in base),
              tuple(max(0, c - 8) for c in base),
              tuple(min(255, c + 26) for c in base))
    y = float(y0)
    band_h = (y1 - y0) / float(n)
    for k in range(n):
        yb = y + band_h * (1.0 + 0.22 * (((seed + k * 19) % 30) / 30.0 - 0.5))
        yb = min(yb, y1)
        pts = [(x0, y)]
        steps = 16
        for s in range(steps + 1):
            fx = x0 + (x1 - x0) * s / float(steps)
            wob = 9.0 * math.sin(s * 0.9 + k * 2.1 + seed * 0.03)
            wob += (((seed + k * 13 + s * 7) % 10) / 10.0 - 0.5) * 14.0
            pts.append((fx, y + wob))
        PA.fill_poly(tile, pts + [(x1, yb), (x0, yb)], strata[k % len(strata)],
                     seed=seed + k * 7, value=0.09, tint=0.0, band=0.0,
                     edge=1.6)
        PA.hand_stroke(d, pts, INK, 4, closed=False, seed=seed + k * 11,
                       wavelength=170.0)
        y = yb
    # The top two bands are the ones a digger actually cut into, so they carry
    # the course grid -- small pressed rectangles, the rammed-earth texture at
    # the scale the fortknox gold-slab frame gets its density from.
    for r in range(4):
        ya = y0 + (y1 - y0) * r * 0.055
        yb = ya + (y1 - y0) * 0.055
        x = x0 + 10
        c = 0
        while x < x1 - 20:
            seg = 74 + ((seed + r * 17 + c * 11) % 78)
            xe = min(x + seg, x1)
            PA.hand_stroke(d, [(x + 2, ya + 4), (xe - 2, ya + 4), (xe - 2, yb - 4),
                               (x + 2, yb - 4)], (92, 70, 52), 3, closed=True,
                           seed=seed + 300 + r * 23 + c, wavelength=80.0)
            x = xe
            c += 1
    PA.hand_stroke(d, [(x0, y0), (x1, y0)], INK, 6, closed=False,
                   seed=seed + 500, wavelength=200.0)


def _far_rank(tile, d, seed, y_base, rows=((0.42, 0.55, (96, 60, 36),
                                            (70, 44, 26)),
                                           (0.24, 0.36, (120, 76, 44),
                                            (86, 54, 32)))):
    """Small receding soldier ranks to fill the dark a terracotta pit recedes into.

    The pit backdrops were one smooth black void above the near rank, which is
    exactly the "big empty field" defect. This fills that void with ranks at
    smaller scale and lower value, so the pit reads as an army going back into
    the dark -- depth AND edge density -- without competing with the near row.
    """
    for row, (hf, hr, col, shd) in enumerate(rows):
        hgt = int(H * hr)
        step = int(hgt * 0.62)
        c = -1
        x = int(-40 + row * 26)
        while x < W + step:
            _soldier(d, x, int(y_base - row * 18), hgt,
                     seed + row * 17 + c, col=col, shade=shd,
                     has_bow=(c % 2 == 0), has_armour=False)
            x += step
            c += 1


def _map_detail(tile, d, cx, cy, s, seed, ink_river=(58, 78, 104),
                ridge=(178, 152, 112), cell=(184, 160, 122),
                dense=True):
    """Dense internal structure for the landmass: region cells, ridges, a river,
    mountain ranges.

    The map beats b11-b14 measured flat (2.7-3.0) because the landmass is ONE
    large smooth sand polygon filling ~70% of the frame -- the biggest smooth
    shape in the chapter. Enlarging it would not help; it is already big. What
    it has no INTERNAL detail is what reads as flat, so this packs the interior
    with small OUTLINED cells laid over it: a jittered lattice of irregular
    province cells, two ridge belts, a river, and two dense mountain ranges.
    Every mark is placed inside an inset ellipse so it lands on the landmass
    rather than off its coast. `dense` is the difference between a few visible
    strokes and a lattice that actually lifts the pigment across the whole
    field.
    """
    # a point is "inside enough" if its normalized radius (in the shape's own
    # half-extents) is under this. The shape is convex enough that an ellipse
    # tracks its coast closely.
    RX, RY = 345.0 * s, 240.0 * s

    def inside(px, py, k=0.86):
        nx = (px - cx) / (RX * k)
        ny = (py - cy) / (RY * k)
        return nx * nx + ny * ny <= 1.0

    # --- PROVINCE BORDERS: a network of thin internal lines dividing the
    # landmass into regions. This is the edge-density lever applied the way a
    # map actually wants it -- dozens of thin outlined strokes that tile the
    # field, not filled slabs that would read as a brick wall over the coast.
    # Each border is a wobbled polyline; borders cross, which is what makes a
    # region network.
    if dense:
        nx, ny = 7, 6
        # vertical borders, wobbled
        for c in range(1, nx):
            bx = cx - RX * 0.86 + (2 * RX * 0.86) * c / float(nx)
            pts = []
            for r in range(9):
                t = r / 8.0
                py = cy - RY * 0.92 + 2 * RY * 0.92 * t
                px = bx + (((seed + c * 17 + r * 5) % 30) - 15)
                if inside(px, py, 0.92):
                    pts.append((px, py))
            if len(pts) > 2:
                PA.hand_stroke(d, pts, INK, 4, closed=False,
                               seed=seed + c * 23, wavelength=90.0)
        # horizontal borders, wobbled
        for r in range(1, ny):
            by = cy - RY * 0.88 + (2 * RY * 0.88) * r / float(ny)
            pts = []
            for c in range(13):
                t = c / 12.0
                px = cx - RX * 0.88 + 2 * RX * 0.88 * t
                py = by + (((seed + r * 29 + c * 7) % 26) - 13)
                if inside(px, py, 0.92):
                    pts.append((px, py))
            if len(pts) > 2:
                PA.hand_stroke(d, pts, INK, 4, closed=False,
                               seed=seed + 40 + r * 19, wavelength=90.0)
        # dot the region centres faintly so the cells read as territories
        for c in range(nx):
            for r in range(ny):
                px = cx - RX * 0.86 + (2 * RX * 0.86) * (c + 0.5) / nx
                py = cy - RY * 0.88 + (2 * RY * 0.88) * (r + 0.5) / ny
                if not inside(px, py, 0.90):
                    continue
                rr = 7 + ((seed + c * 3 + r * 5) % 5)
                PA.fill_poly(tile, PA.ellipse_pts(px, py, rr, rr, n=14),
                             cell, seed=seed + c * 7 + r * 11, value=0.08,
                             edge=0.8)

    # --- two ridge belts: rows of small chevrons
    for b, (yoff, amp) in enumerate(((-120, 0.55), (60, 0.42))):
        pts = []
        t = -1.0
        while t <= 1.0:
            px = cx + RX * 0.80 * t
            py = cy + RY * yoff / 240.0 + amp * 30 * math.sin(t * 5.0 + b * 2)
            if inside(px, py):
                pts.append((px, py))
            t += 0.08
        if len(pts) > 3:
            PA.hand_stroke(d, pts, ridge, 7, closed=False,
                           seed=seed + b * 13, wavelength=110.0)

    # --- one river: a thick blue-grey snake from the north-west to the south
    riv = []
    t = 0.0
    while t <= 1.0:
        px = cx + RX * (-0.62 + 1.10 * t)
        py = cy + RY * (-0.72 + 1.44 * t) + 26 * math.sin(t * 7.0 + 1.1)
        if inside(px, py):
            riv.append((px, py))
        t += 0.06
    if len(riv) > 3:
        PA.hand_stroke(d, riv, ink_river, 10, closed=False, seed=seed + 5,
                       wavelength=130.0)

    # --- two mountain ranges, packed so they read as terrain not specks
    for r, (ax, ay, bx, by, n) in enumerate(
            ((0.10, -0.40, 0.72, -0.10, 11), (-0.80, 0.30, 0.10, 0.70, 8))):
        for k in range(n):
            f = k / float(n - 1)
            px = cx + RX * (ax + (bx - ax) * f) + (((seed + k * 23) % 30) - 15)
            py = cy + RY * (ay + (by - ay) * f) + (((seed + k * 41) % 24) - 12)
            if not inside(px, py, 0.88):
                continue
            w = (13 + (k % 3) * 6) * s * 0.8
            tri = [(px, py - w), (px + w, py + w * 0.7), (px - w, py + w * 0.7)]
            PA.fill_poly(tile, tri, ridge, seed=seed + 40 + r * 50 + k,
                         value=0.10, edge=1.0)
            PA.hand_stroke(d, tri, INK, 3, closed=True,
                           seed=seed + 90 + r * 50 + k, wavelength=50.0)


def _shelf(tile, d, y, seed, col=(146, 116, 82), x0=-60, x1=W + 60,
           thick=34):
    """A stone shelf / bench to stand objects on, cropped by the side edges.

    A floor line with visible slab joints under the subject, so objects in a
    room are ON something instead of floating in a wall-coloured field.
    """
    PA.fill_rect(tile, [x0, y, x1, y + thick], col, seed=seed, value=0.09,
                 edge=2.0)
    PA.hand_stroke(d, [(x0, y), (x1, y)], INK, 6, closed=False, seed=seed + 1,
                   wavelength=200.0)
    x = x0 + 40
    k = 0
    while x < x1 - 20:
        PA.hand_stroke(d, [(x, y + 4), (x - 6, y + thick - 4)], INK, 4,
                       closed=False, seed=seed + 10 + k, wavelength=60.0)
        x += 118
        k += 1
    PA.hand_stroke(d, [(x0, y + thick), (x1, y + thick)], INK, 5, closed=False,
                   seed=seed + 60, wavelength=200.0)


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
    # STAGE A  b01-b05  "Beneath this field, eight thousand soldiers.       #
    #   They are clay, and they are perfect. They stand one way for two      #
    #   thousand years. Their paint left them centuries after burial.        #
    #   They are called the Terracotta Army."                                #
    # The frame repaints five times in 15s but the WORLD is one place: the    #
    # black the ranks recede into. v1 gave the far ranks a whole full-frame  #
    # beat and then re-drew a bigger version of the same idea on b02; here    #
    # the receding mass is the backdrop and the beats build TOWARD the        #
    # viewer -- far ranks, then one big soldier cropped by the right edge,   #
    # then the lit row, then the paint leaving him, then the name.            #
    # ===================================================================== #
    def a_pit(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 130, wall=EARTH)
        # A dark card needs a lit stone course at the head for the near-black
        # title to read against. Drawn before the ranks so the backdrop stays
        # UNDER the art (scene_common.title_backdrop).
        SC.title_backdrop(tile, 1130, col=(118, 92, 70))
        # The pit FLOOR. _pit lays one smooth band of EARTH across the bottom
        # quarter; b01/b02 measured flat because that band and the black above
        # it were the only two things in the lower half. A paving course of
        # slabs plus loose clay rubble gives the floor real local detail, so the
        # near row of soldiers stands ON something instead of in front of a
        # flat stripe.
        _slab_floor(tile, d, 566, 720, seed=134, col=(122, 92, 66), n=10)
        _rubble(tile, d, (0, 566, W, 720), 16, seed=136, col=(150, 112, 78))
        # The dark the ranks recede into. Two hand-placed mid ranks (they are the
        # readable ones, at 380 and 270) and then _far_rank, which continues the
        # recession past them with smaller, dimmer figures -- so the void above
        # the near row reads as an army going back into the dark rather than as
        # an empty black field. _far_rank draws FIRST (farthest) so the two
        # legible ranks draw over it.
        _far_rank(tile, d, seed=138, y_base=470)
        for row, (base, hgt, col, shd) in enumerate((
                (600, 380, (150, 92, 52), (110, 66, 38)),
                (470, 270, (96, 60, 36), (68, 42, 26)))):
            for c in range(-1, 6):
                _soldier(d, 90 + c * 230 + row * 46, base, hgt,
                         140 + row * 30 + c, col=col, shade=shd,
                         has_bow=(c % 2 == 0), has_armour=False)
    els.append(SC.stage(clock, 1, a_pit, j=6))

    def a_place(tile, fw, fh):
        # The location, said once and gone in a beat. It is the only exterior
        # fact the hook carries and the rest of the chapter is underground.
        D.draw_label(tile, "OUTSIDE XI'AN, CHINA", center=(640, 150),
                     color=PALE, size=34)
    els.append(SC.layer(clock, 1, a_place, j=2, kind='shape',
                        eid='a_place'))
    els.append(cap(1, 640, 664, size=32, fill=PALE))

    # The presenter is here from b01, not from an emotional beat later: four
    # seconds of bare pit reads as "nothing is happening".
    def a_face_a(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 236, 430, 150, 'confused', 110)
    els.append(E3.E('a_face_a', 'character', a_face_a, at=T(1),
                    until=T(4),
                    motion=SC.enter(clock, 1, dx=-150, dy=30, dur=0.55)))

    # MOVING. The single soldier cropped by the right edge is the reveal of
    # the whole chapter. He is 640 tall against a 470 rank -- the step in scale
    # IS the beat -- and cropped so the frame admits the army continues past it.
    def a_soldier(tile, fw, fh):
        _soldier(ImageDraw.Draw(tile), 1090, 740, 640, 111, has_bow=True)
    els.append(SC.accrue(clock, 2, 6, a_soldier, kind='shape',
                         eid='a_soldier',
                         motion=SC.enter(clock, 2, dx=0, dy=64, dur=0.55)))

    def a_row(tile, fw, fh):
        # The lit rank coming forward. Drawn AFTER the big soldier but placed
        # clear of him -- its rightmost figure ends at x=969, his torso starts
        # at 1023 -- so the foreground read survives.
        d = ImageDraw.Draw(tile)
        for c in range(6):
            _soldier(d, 20 + c * 180, 700, 470, 150 + c,
                     has_bow=(c % 2 == 1), has_armour=False)
    els.append(SC.accrue(clock, 3, 6, a_row, kind='shape', eid='a_row'))
    els.append(cap(3, 640, 664, size=32, fill=PALE))

    def a_flakes(tile, fw, fh):
        # The paint leaving him. Accrues ON TOP of the figure rather than
        # replacing it, because it is paint ON that figure, not a second object
        # in the same place. PALE, not v1's GOLD: GOLD (206,158,74) on CLAY
        # (196,118,66) measures ~1.2:1 and the flakes were invisible at ship
        # size -- a defect v1 shipped.
        d = ImageDraw.Draw(tile)
        for k in range(18):
            fx = 900 + (k * 137) % 320
            fy = 250 + (k * 91) % 380
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 16, 9, n=14), PALE,
                         seed=115 + k, value=0.05, edge=0.6)
    els.append(SC.accrue(clock, 4, 6, a_flakes, kind='shape', eid='a_flakes'))

    def a_name(tile, fw, fh):
        D.draw_label(tile, 'TERRACOTTA ARMY', center=(640, 152),
                     color=PALE, size=60)
    els.append(SC.layer(clock, 5, a_name, j=6, kind='shape', eid='a_name'))
    els.append(cap(5, 640, 664, size=32, fill=PALE))

    # ===================================================================== #
    # STAGE B  b06-b10  "Eight thousand soldiers in the dark. Six hundred    #
    #   horses stood beside them. They stand in long rows, in earthen pits.  #
    #   They are all guarding one man. His name is Qin Shi Huang."           #
    # Depth is built BACK TO FRONT in beat order, which is the only order     #
    # that works: a later element draws over an earlier one, so anything that #
    # arrives at b08 must be NEARER than what arrived at b06. Hence the rank   #
    # at b06 (back), the horses at b07 (middle), and at b08 the front rank    #
    # plus the pit lip that cuts across everybody's feet.                     #
    # ===================================================================== #
    def b_pit(tile, fw, fh):
        _pit(tile, 137, wall=EARTH_D)
        SC.title_backdrop(tile, 1371, col=(118, 92, 70))
        # Same three-part fix as stage A's pit, and for the same reason: b06
        # measured flat because the near rank sat under a smooth black void with
        # a smooth earth stripe under its feet. The floor is paved and
        # rubbled, and the black now carries receding ranks, so the top of the
        # frame reads as an army continuing back rather than as empty dark.
        _slab_floor(tile, ImageDraw.Draw(tile), 566, 720, seed=137,
                    col=(110, 82, 58), n=10)
        _rubble(tile, ImageDraw.Draw(tile), (0, 566, W, 720), 16, seed=139,
                col=(142, 104, 70))
        _far_rank(tile, ImageDraw.Draw(tile), seed=141, y_base=470)
    els.append(SC.stage(clock, 6, b_pit, j=11))

    def a_number(tile, fw, fh):
        # v1 drew '8,000' at y=660, straight across the near rank's shins.
        # GOLD on CLAY is ~1.2:1 there; moved up onto the black above the heads
        # it is 4.6:1.
        D.draw_label(tile, '8,000', center=(640, 168), color=GOLD, size=64)
    els.append(SC.layer(clock, 6, a_number, j=7, kind='shape',
                        eid='b_number'))

    def b_rank(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for c in range(6):
            _soldier(d, 150 + c * 190, 690, 460, 200 + c,
                     has_bow=(c % 2 == 0), has_armour=True)
    els.append(SC.accrue(clock, 6, 11, b_rank, kind='shape', eid='b_rank'))

    def b_horses(tile, fw, fh):
        # The near horse is CROPPED by the left edge and runs nearly the full
        # height: a complete animal in the middle of the frame reads as a model
        # on a plinth, which is what a museum case looks like.
        d = ImageDraw.Draw(tile)
        _horse(d, 190, 700, 460, 201, facing=-1)
        _horse(d, 1150, 706, 360, 202, col=CLAY_L, shade=EARTH, facing=-1)
    els.append(SC.accrue(clock, 7, 11, b_horses, kind='shape', eid='b_horses'))

    def a_count(tile, fw, fh):
        D.draw_label(tile, '600 HORSES', center=(430, 172), color=PALE,
                     size=44)
    els.append(SC.layer(clock, 7, a_count, j=9, kind='shape',
                        eid='b_count'))

    def b_front(tile, fw, fh):
        # "long rows, in earthen pits": the nearest rank, in the middle of the
        # frame where the horses are not, plus the pit lip we are looking over.
        d = ImageDraw.Draw(tile)
        for c in range(4):
            _soldier(d, 400 + c * 160, 745, 390, 210 + c, has_armour=False)
        PA.fill_rect(tile, [0, 690, W, 720], EARTH_D, seed=214, value=0.06)
        PA.hand_stroke(d, [(-10, 690), (1290, 690)], INK, 6, closed=False,
                       seed=215, wavelength=190.0)
    els.append(SC.accrue(clock, 8, 11, b_front, kind='shape', eid='b_front'))

    def b_guard(tile, fw, fh):
        # MOVING. The one living figure among the clay, standing in the aisle he
        # is being guarded for.
        # y_feet 700, not 812: at 812 his shins ran 92px off the bottom of a 720
        # frame with no ground contact, which reads as him sinking into the floor
        # rather than standing in it. b_front draws its ground line at y=690 and
        # the ranks' feet at y=745, so 700 puts him on that same floor plane --
        # and 700 is the value the two other presenters in this chapter already
        # use (b_emperor, e_script). The comment here used to say "cropped by
        # the bottom edge"; that crop only works on a figure that FILLS the
        # frame, and at h=380 he does not.
        SC.fullbody(ImageDraw.Draw(tile), 470, 700, 380, pose='shrug',
                    expression='awed', seed=250, ink=PALE)
    els.append(SC.accrue(clock, 9, 11, b_guard, kind='character',
                         eid='b_guard',
                         motion=SC.enter(clock, 9, dx=0, dy=48, dur=ARRIVE)))

    def b_one(tile, fw, fh):
        D.draw_label(tile, 'ONE MAN', center=(640, 172), color=GOLD, size=40)
    els.append(SC.layer(clock, 9, b_one, j=10, kind='shape', eid='b_one'))

    def b_emperor(tile, fw, fh):
        # The emperor arrives as a large gold figure on the right, in front of
        # his army. Off-centre on purpose: dead centre put his head behind the
        # label chain and the presenter at x=470 behind his shoulder.
        _soldier(ImageDraw.Draw(tile), 980, 930, 780, 253, col=GOLD,
                 shade=(150, 110, 52), has_armour=True)
    els.append(SC.accrue(clock, 10, 11, b_emperor, kind='shape',
                         eid='b_emperor'))

    def b_name(tile, fw, fh):
        D.draw_label(tile, 'QIN SHI HUANG', center=(400, 152), color=GOLD,
                     size=50)
    els.append(SC.layer(clock, 10, b_name, j=11, kind='shape', eid='b_name'))
    els.append(cap(10, 400, 250, size=30, fill=PALE))

    # ===================================================================== #
    # STAGE C  b11-b16  "This is Qin Shi Huang. He was the first emperor.   #
    #   In 221 BC he took the throne. He gave the hundred warring kingdoms   #
    #   one script, one set of weights, one ruler: himself."                 #
    # Register change: light paper. The stage opens on PAPER2 and stays there #
    # for b11-b14, then b15 and b16 cut to full-frame DARK REPLACES -- the     #
    # weights and the throne are night shots, and the frame has to repaint to #
    # say so. Those two replaces also hide the presenter, which is fine: he    #
    # has done his job pointing at the map.                                  #
    # ===================================================================== #
    def c_paper(tile, fw, fh):
        _interior(tile, 254, PAPER2)
        # The register is a RECORD sheet, so give it ledger structure instead of
        # one pale field: ruled lines every 22px with heavier rules every 5th,
        # plus a drawn border and a punched margin. This is texture across the
        # whole pale ground (the map floats on it), and it is why the map beats
        # read as a document rather than as a shape on blank paper.
        d = ImageDraw.Draw(tile)
        for k in range(31):
            yy = 96 + k * 20
            w = 5 if k % 5 == 0 else 3
            col = (206, 200, 186) if k % 5 == 0 else (214, 208, 194)
            PA.hand_stroke(d, [(52, yy), (1228, yy)], col, w, closed=False,
                           seed=254 + k, wavelength=190.0)
        PA.hand_stroke(d, [(30, 88), (1250, 88), (1250, 700), (30, 700)],
                       (176, 168, 152), 6, closed=True, seed=253,
                       wavelength=220.0)
        # the punched margin the rules start from
        PA.hand_stroke(d, [(30, 88), (30, 700)], (198, 120, 92), 5,
                       closed=False, seed=252, wavelength=200.0)
    els.append(SC.stage(clock, 11, c_paper, j=17))

    def c_presenter(tile, fw, fh):
        # MOVING. He walks in and points; the map he is pointing at is
        # replaced twice under his hand, which is the point of the beat.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 300, 700, 470, pose='pointing', expression='neutral',
                    seed=260)
        # The bubble sits in the clear band between the presenter's head and
        # the map's western shoulder. At (185, 148) the full-res frame showed
        # it clipped to 'FIRST EM' at the left frame edge -- draw_bubble lays
        # the word out wider than max_w implies once its own padding is added,
        # so a bubble whose CENTRE is at x=185 runs off x=0. Centred at 320 it
        # spans roughly 130-510, inside the frame and clear of both the
        # presenter (x 240-360 at the head) and the landmass (west edge 250,
        # but the shoulder at that height is further right).
        D.draw_bubble(tile, 'FIRST EMPEROR', (330, 105), tail_to=(330, 230),
                      font_size=30, max_w=340)
    els.append(SC.accrue(clock, 11, 15, c_presenter, kind='character',
                         eid='c_presenter',
                         motion=SC.enter(clock, 11, dx=-120, dy=0,
                                         dur=ARRIVE)))

    def c_map1(tile, fw, fh):
        _china2(ImageDraw.Draw(tile), 700, 470, 1.30, 255)
        # The landmass is one big smooth sand shape -- b11 measured 2.67, the
        # flattest frame in the chapter. Enlarging it would not help; it is
        # already 70% of the width. _map_detail stacks small outlined ridges,
        # a river and mountain ticks INSIDE the same outline, which is what
        # turns the fill from a smooth field into a drawn map.
        _map_detail(tile, ImageDraw.Draw(tile), 700, 470, 1.30, 256)
    # Re-framed from (780, 400) at s=1.35, then dropped again to cy=470. The
    # landmass top edge sits at cy-240*s = 470-312 = 158, which clears a band
    # across the top of the frame for the FIRST EMPEROR bubble -- at cy=420
    # the top edge was 108 and the bubble slid under the map's shoulder. The
    # landmass runs 250-1150, clear of the presenter at x=300.
    els.append(SC.layer(clock, 11, c_map1, j=12, kind='shape',
                        eid='c_map1'))

    def c_map2(tile, fw, fh):
        # "In 221 BC he took the throne": the map broken into the old powers
        # and crossed out. NO drawn '221 BC' -- the caption at b12 says it.
        d = ImageDraw.Draw(tile)
        _china2(d, 700, 452, 1.40, 259)
        _map_detail(tile, d, 700, 452, 1.40, 260)
        for k in range(5):
            bx = 420 + k * 110
            by = 250 + k * 34
            PA.fill_poly(tile, [(bx, by), (bx + 62, by - 16),
                                (bx + 62, by + 74), (bx, by + 90)],
                         CLAY_D, seed=261 + k, value=0.12)
            D.draw_red_x(tile, [bx - 8, by - 22, bx + 70, by + 96], width=8)
    els.append(SC.layer(clock, 12, c_map2, j=13, kind='shape',
                        eid='c_map2'))
    els.append(cap(12, 640, 676, size=32))

    def c_map3(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _china2(d, 640, 436, 1.35, 276, kingdoms=True)
        _map_detail(tile, d, 640, 436, 1.35, 277)
        for k in range(9):
            x0 = 500 + (k % 3) * 150
            y0 = 260 + (k // 3) * 110
            D.draw_arrow(tile, (x0, y0), (x0 + 120, y0 - 40), color=INK,
                         width=11, head=44)
        # PAPER2 keyline, not a halo: the map's own outline runs straight
        # through this word, and an outline in the ground colour is what
        # clears the line out from under the glyphs instead of adding a glow.
        D.draw_label(tile, 'A HUNDRED KINGDOMS', center=(640, 656),
                     color=INK, size=36, outline=PAPER2, outline_w=9)
    els.append(SC.layer(clock, 13, c_map3, j=14, kind='shape',
                        eid='c_map3'))

    def c_map4(tile, fw, fh):
        # NOT unify=True. v1's unify floods the entire landmass solid red,
        # which at s=1.35 turns the beat into one red blob and swallows both the
        # road and the script sheet -- and the beat is not "the map turned red",
        # it is "he gave them one script". So the outline stays plain, and the
        # unification is carried by the single road running the whole width and
        # the one sheet of writing beside it. PAPER2 keyline on the word
        # because the map outline runs through it.
        d = ImageDraw.Draw(tile)
        _china2(d, 640, 436, 1.35, 281)
        _map_detail(tile, d, 640, 436, 1.35, 284)
        PA.hand_stroke(d, [(240, 560), (520, 520), (760, 500), (1040, 470)],
                       INK, 12, closed=False, seed=282, wavelength=150.0)
        _script_sheet(d, 1050, 200, 290, 370, 283)
        D.draw_label(tile, 'ONE SCRIPT', center=(1050, 470), color=INK,
                     size=34, outline=PAPER2, outline_w=9)
    els.append(SC.layer(clock, 14, c_map4, j=15, kind='shape',
                        eid='c_map4'))
    els.append(cap(14, 640, 676, size=32))

    def c_weights(tile, fw, fh):
        # Full-frame REPLACE: night. The weights are the one thing in the
        # chapter that is literally a measuring instrument, so they get the
        # dark, lit-from-above register v1 gave them.
        d = ImageDraw.Draw(tile)
        _interior(tile, 284, (74, 58, 46))
        SC.title_backdrop(tile, 1284, col=(118, 92, 70))
        # b15 measured 3.17 because the whole card was one smooth brown wall
        # with four small weights on nothing. It is now a stone strong-room: a
        # coursed masonry wall the weights stand against, a shelf they sit ON
        # and run off both side edges, and weights 30% taller so they own the
        # frame instead of sitting in it.
        _stone_courses(tile, d, -20, 150, 1300, 700, seed=286,
                       col=(96, 74, 58), row_h=62)
        _shelf(tile, d, 660, seed=288, col=(132, 104, 76), thick=60)
        for k, (x, w, h, kind) in enumerate(((210, 150, 340, 0),
                                             (505, 130, 430, 1),
                                             (790, 175, 280, 2),
                                             (1075, 145, 380, 0))):
            _weight(d, x, 664, w, h, 290 + k, kind=kind)
            D.draw_label(tile, 'III', center=(x, 664 - h - 36),
                         color=PALE, size=28)
        D.draw_label(tile, 'ONE SET OF WEIGHTS', center=(640, 120),
                     color=GOLD, size=40)
    els.append(SC.layer(clock, 15, c_weights, j=16, kind='bg',
                        eid='c_weights'))

    def c_throne(tile, fw, fh):
        # Full-frame REPLACE: the man himself, off-centre, cropped in on the
        # left by a close-up with nothing on its face. v1's staging, kept --
        # it is the best-executed card in the chapter.
        d = ImageDraw.Draw(tile)
        _interior(tile, 295, (54, 40, 32))
        SC.title_backdrop(tile, 1295, col=(118, 92, 70))
        # Same fix as the weights: the throne was floating in a smooth dark
        # field (b16 measured 3.02). A coursed wall behind, a carved canopy
        # above, ornament on the throne back and a stepped dais under it give
        # the room real structure. The throne is kept at 560 (not 700) so it
        # reads as a throne rather than a wall of flat terracotta.
        _stone_courses(tile, d, -20, 150, 1300, 720, seed=298,
                       col=(74, 56, 44), row_h=58)
        # a canopy arch behind the throne, cropped by the top
        PA.fill_poly(tile, [(660, 150), (660, 470), (1220, 470), (1220, 150),
                            (1150, 118), (730, 118)], (108, 62, 44), seed=310,
                     value=0.09)
        PA.hand_stroke(d, [(660, 470), (660, 150), (730, 118), (1150, 118),
                           (1220, 150), (1220, 470)], INK, 6, closed=True,
                       seed=311, wavelength=140.0)
        for k in range(6):   # fringe tassels along the canopy
            tx = 700 + k * 88
            PA.hand_stroke(d, [(tx, 150), (tx, 186)], GOLD, 5, closed=False,
                           seed=312 + k, wavelength=40.0)
        _throne(d, 940, 730, 560, 296)
        # Carved panel divisions ON the throne itself. _throne draws two plain
        # rectangles; left smooth they are ~90k px of flat terracotta, which is
        # what kept b16 under the bar on the second attempt even after the room
        # got structure. A recessed lattice over the back and the seat breaks
        # both rectangles into edge-rich panels.
        _panel_grid(tile, d, 786, 208, 1096, 424, seed=306,
                    col=(122, 68, 46), nx=4, ny=3, w_line=4)
        _panel_grid(tile, d, 664, 622, 1216, 700, seed=308,
                    col=(116, 64, 44), nx=6, ny=1, w_line=4)
        # ornament on the throne back: two carved roundels and a bead band
        for rx in (860, 1020):
            PA.hand_stroke(d, PA.arc_pts(rx, 300, 42, 42, 0, 360, n=28),
                           GOLD, 6, closed=False, seed=320 + rx,
                           wavelength=70.0)
            PA.hand_stroke(d, PA.arc_pts(rx, 300, 24, 24, 0, 360, n=24),
                           GOLD, 4, closed=False, seed=330 + rx,
                           wavelength=60.0)
        for bx in range(770, 1130, 36):
            PA.fill_poly(tile, PA.ellipse_pts(bx, 430, 7, 7, n=10), GOLD,
                         seed=340 + bx, value=0.06, edge=0.6)
        # the dais the throne stands on, stepped
        PA.fill_poly(tile, [(640, 720), (1300, 720), (1230, 660), (700, 660)],
                     (86, 64, 50), seed=299, value=0.10)
        PA.fill_poly(tile, [(690, 720), (1250, 720), (1215, 700), (720, 700)],
                     (70, 52, 42), seed=301, value=0.10)
        PA.hand_stroke(d, [(640, 720), (1300, 720), (1230, 660), (700, 660)],
                       INK, 6, closed=True, seed=300, wavelength=150.0)
        # A rack of ceremonial bronze blades on the wall in the gap between the
        # man and the throne -- the court furniture that says "throne room"
        # instead of "brown box". The rail runs off under the canopy at the
        # right, so the room reads as continuing past the frame.
        PA.hand_stroke(d, [(498, 182), (648, 182)], BRONZE, 8, closed=False,
                       seed=312, wavelength=60.0)
        for k in range(5):
            bx = 512 + k * 30
            bl = 78 + ((k * 31) % 44)
            PA.fill_poly(tile, [(bx - 8, 182), (bx + 8, 182), (bx + 5, 182 + bl),
                                (bx - 3, 182 + bl)], BRONZE, seed=314 + k,
                         value=0.12, edge=1.4)
            PA.hand_stroke(d, [(bx - 8, 182), (bx + 8, 182), (bx + 5, 182 + bl),
                               (bx - 3, 182 + bl)], INK, 4, closed=True,
                           seed=318 + k, wavelength=45.0)
            PA.hand_stroke(d, [(bx - 11, 178), (bx + 11, 178)], GOLD, 4,
                           closed=False, seed=322 + k, wavelength=25.0)
        # The close-up is kept on the left, but at hr 132 rather than 175.
        # SC.closeup's bust is a fill_poly with value/tint/band/edge all zero --
        # a deliberately pigment-free black mass -- and at hr 175 it covered
        # ~27% of the frame in one smooth shape, which is what held b16 at 6.53
        # even after the room got its wall. Smaller bust, same presence.
        SC.closeup(d, 286, 306, 132, 'deadpan', 297)
        # The bubble still points at the EMPTY THRONE -- the joke is that the
        # seat labelled "himself" stands in for the man.
        D.draw_bubble(tile, 'himself', (1074, 150), tail_to=(990, 320),
                      font_size=34, max_w=260)
    els.append(SC.layer(clock, 16, c_throne, j=17, kind='bg',
                        eid='c_throne'))
    els.append(cap(16, 640, 676, size=32, fill=PALE))

    # ===================================================================== #
    # STAGE D  b17-b20  "He burned every book. He buried the scholars alive. #
    #   In 246 BC he began a tomb for himself, and it took decades of unpaid #
    #   labour."                                                            #
    # One bright exterior register for all four beats: the mound is already  #
    # standing in the backdrop, so b19's date is a label and b20's carriers   #
    # walk in front of a thing we have been looking at since the stage opened.#
    # ===================================================================== #
    def d_field(tile, fw, fh):
        _earth_field(tile, 355, sky=(198, 206, 214), ground=EARTH,
                     hz=int(H * 0.44))
        d = ImageDraw.Draw(tile)
        # The upper 44% of this stage was bare sky on all four beats, and b17
        # through b20 all measured 3.0-3.9 because of it: one smooth 405k-pixel
        # field with nothing in it. The fix is layered depth -- a hazy sun, two
        # cloud decks, and a far mountain range sitting on the horizon -- so the
        # sky is receding space rather than a fill, and the eye gets a horizon
        # to read the mound against.
        hz = int(H * 0.44)
        # hazy sun, low and pale, sitting just left of the mound's crown
        PA.fill_poly(tile, PA.ellipse_pts(300, 196, 74, 74, n=26),
                     (238, 226, 198), seed=380, value=0.07, tint=0.10,
                     band=0.20, edge=0.9)
        PA.hand_stroke(d, PA.arc_pts(300, 196, 74, 74, 0, 360, n=30),
                       (226, 208, 176), 5, closed=False, seed=381,
                       wavelength=110.0)
        # two cloud decks: the far one thin and high, the near one a stacked
        # row of lobes with a shaded underside
        for k, (cy, rx, ry, col) in enumerate((
                (110, 120, 26, (214, 218, 222)),
                (146, 96, 22, (206, 210, 216)))):
            cx = 180 + k * 620
            PA.fill_poly(tile, PA.ellipse_pts(cx, cy, rx, ry, n=24), col,
                         seed=382 + k, value=0.06, tint=0.08, band=0.24,
                         edge=1.0)
            PA.hand_stroke(d, PA.arc_pts(cx, cy, rx, ry, 190, 350, n=20), col,
                           6, closed=False, seed=384 + k, wavelength=90.0)
        for k, (cx, cy, rx, ry) in enumerate(((430, 122, 108, 24),
                                              (560, 136, 76, 18),
                                              (960, 108, 132, 26),
                                              (1090, 128, 92, 20))):
            PA.fill_poly(tile, PA.ellipse_pts(cx, cy, rx, ry, n=24),
                         (222, 226, 230), seed=386 + k, value=0.06, tint=0.10,
                         band=0.26, edge=1.0)
            PA.hand_stroke(d, PA.arc_pts(cx, cy + ry * 0.5, rx * 0.86, ry * 0.5,
                                         200, 340, n=18), (188, 192, 200), 5,
                           closed=False, seed=388 + k, wavelength=80.0)
        # a far mountain range on the horizon, three ridges receding
        for k, (col, amp, base) in enumerate((((178, 188, 198), 46, hz + 6),
                                              ((166, 178, 190), 62, hz + 14),
                                              ((152, 164, 178), 40, hz + 24))):
            pts = [(-40, base + 40)]
            x = -40
            while x < W + 40:
                x += 54 + ((k * 37 + x) % 46)
                pts.append((x, base - amp * (0.35 + ((x * 7 + k * 53) % 60)
                                             / 100.0)))
            pts.append((W + 40, base + 40))
            PA.fill_poly(tile, pts, col, seed=390 + k, value=0.08, tint=0.06,
                         band=0.18, edge=1.1)
            PA.hand_stroke(d, pts[1:-1], tuple(max(0, c - 26) for c in col), 4,
                           closed=False, seed=394 + k, wavelength=120.0)
        # Ploughed ground in the foreground either side of the mound. Drawn BEFORE
        # the mound so the furrows recede behind it instead of striping across
        # it -- the mound is the subject and must read as one solid mass.
        for k in range(9):
            yy = hz + 26 + k * 44
            if yy > 716:
                break
            PA.hand_stroke(d, [(-20, yy), (W + 20, yy + 10)],
                           (150, 124, 92), 4, closed=False, seed=410 + k,
                           wavelength=180.0)
        _rubble(tile, d, (0, 600, 340, 720), 12, seed=414, col=(152, 126, 94),
                rmin=8, rmax=22)
        _rubble(tile, d, (960, 600, 1280, 720), 12, seed=416, col=(152, 126, 94),
                rmin=8, rmax=22)
        # The mound, truncated by the bottom edge, with its rammed-earth
        # courses. It is the backdrop rather than an arrival so that b20's
        # carriers have something to be small against.
        PA.fill_poly(tile, [(150, 720), (470, 232), (810, 232), (1140, 720)],
                     EARTH_D, seed=356, value=0.10)
        # Dense rammed-earth banding. The original six strokes left ~250k px of
        # one flat trapezoid; the mound is the single largest shape in all four
        # beats, so it has to carry real surface.
        for k in range(17):
            yy = 250 + k * 28
            if yy > 700:
                break
            # The courses must sit INSIDE the trapezoid. The first pass used
            # an inset measured from the apex, which drew them straight across
            # the sky and the mountains -- the mound stopped reading as a
            # solid. Half-width is linear in y, so derive both edges from it.
            hw = 170.0 + (yy - 232.0) * 0.656
            xl = 640.0 - hw + 8
            xr = 640.0 + hw - 8
            if xr - xl < 20:
                continue
            PA.hand_stroke(d, [(xl, yy), (xr, yy)],
                           EARTH, 5, closed=False, seed=360 + k,
                           wavelength=120.0)
            PA.hand_stroke(d, [(xl, yy + 6), (xr, yy + 6)],
                           (108, 84, 60), 3, closed=False, seed=380 + k,
                           wavelength=140.0)
        # the vertical lift shafts on the east face, and a spoil ramp
        for k, sx in enumerate((520, 620, 720, 820)):
            PA.hand_stroke(d, [(sx, 250 + (720 - sx) * 0.22),
                               (sx + 10, 690)], (108, 84, 60), 6,
                           closed=False, seed=400 + k, wavelength=130.0)
        PA.fill_poly(tile, [(880, 720), (990, 720), (935, 430)], EARTH,
                     seed=404, value=0.10)
        PA.hand_stroke(d, [(880, 720), (935, 430), (990, 720)], INK, 5,
                       closed=False, seed=405, wavelength=110.0)
        PA.hand_stroke(d, [(150, 720), (470, 232), (810, 232), (1140, 720)],
                       INK, 7, closed=False, seed=370, wavelength=190.0)
    els.append(SC.stage(clock, 17, d_field, j=21))

    def d_fire(tile, fw, fh):
        # Bottom-left foreground, big enough to be the subject. v1's version was
        # a 420px fire in the corner of a 1280px frame, which is the "timid
        # prop in an empty field" defect this project has paid for before.
        # Here the fire and the books it is eating run up the left third and
        # are cropped by the left and bottom edges.
        d = ImageDraw.Draw(tile)
        _flames(d, 330, 740, 620, 301)
        _book(d, 60, 590, 230, 140, 302, tilt=-0.05)
        _book(d, 300, 640, 200, 124, 303, tilt=0.04)
        _book(d, 540, 604, 180, 112, 304, tilt=-0.03)
        D.draw_label(tile, 'EVERY BOOK', center=(640, 150), color=FIRE,
                     size=42)
    els.append(SC.layer(clock, 17, d_fire, j=18, kind='shape',
                        eid='d_fire'))

    def d_scholars(tile, fw, fh):
        # The pit, the robed figure in it, and the presenter recoiling at the
        # left edge. MOVING on the character only -- the pit is scenery.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(300, 720), (360, 480), (900, 460), (980, 720)],
                     PIT, seed=310, value=0.10)
        # The pit was one smooth near-black trapezoid and it is the single
        # largest shape in b18 and b19, where both beat scores sat at 3.1-3.2
        # even after the stage backdrop got its sky. Give it what a pit has:
        # shored timber walls down each side, a ladder, spoil, and the stacked
        # bricks of a half-dug shaft at the bottom.
        for k in range(4):     # shoring posts down the near wall
            px = 340 + k * 168
            PA.hand_stroke(d, [(px, 462 + ((k * 23) % 20)), (px - 10, 720)],
                           (92, 66, 46), 11, closed=False, seed=430 + k,
                           wavelength=150.0)
            PA.hand_stroke(d, [(px + 12, 468 + ((k * 23) % 20)),
                               (px + 2, 720)], (72, 52, 36), 7, closed=False,
                           seed=434 + k, wavelength=150.0)
        for k in range(3):     # cross-braces
            py = 520 + k * 66
            PA.hand_stroke(d, [(316, py), (972, py - 14)], (86, 62, 44), 7,
                           closed=False, seed=438 + k, wavelength=200.0)
        # a ladder down into the shaft
        PA.hand_stroke(d, [(872, 470), (836, 716)], (140, 108, 74), 6,
                       closed=False, seed=442, wavelength=90.0)
        PA.hand_stroke(d, [(934, 466), (898, 712)], (140, 108, 74), 6,
                       closed=False, seed=443, wavelength=90.0)
        for k in range(8):
            ry = 486 + k * 30
            PA.hand_stroke(d, [(866 - k * 4.4, ry), (928 - k * 4.4, ry - 5)],
                           (150, 118, 82), 5, closed=False, seed=444 + k,
                           wavelength=45.0)
        # spoil and half-dug brick courses on the pit floor
        for k in range(7):
            yy = 646 + (k % 3) * 22
            xx = 340 + ((k * 97) % 480)
            PA.fill_rect(tile, [xx, yy, xx + 54, yy + 18], (74, 54, 40),
                         seed=452 + k, value=0.10, edge=1.4)
        _rubble(tile, d, (320, 620, 960, 720), 18, seed=460, col=(66, 48, 38),
                rmin=7, rmax=20)
        PA.fill_poly(tile, [(620, 470), (700, 216), (790, 216), (800, 470)],
                     (122, 92, 62), seed=311, value=0.09)
        d.ellipse([686, 186, 734, 240], fill=(176, 142, 106))
        SC.fullbody(d, 190, 742, 380, pose='recoil', expression='worried',
                    seed=312, ink=PALE)
    els.append(SC.accrue(clock, 18, 21, d_scholars, kind='character',
                         eid='d_scholars',
                         motion=SC.enter(clock, 18, dx=-140, dy=0,
                                         dur=ARRIVE)))
    els.append(cap(18, 230, 200, size=30))

    def d_date(tile, fw, fh):
        D.draw_label(tile, '246 BC', center=(240, 210), color=INK, size=40)
    els.append(SC.layer(clock, 19, d_date, j=21, kind='shape', eid='d_date'))

    def d_carriers(tile, fw, fh):
        # MOVING. Eighteen men carrying the mound that is already standing
        # behind them -- two rows, the back row smaller and higher so the rows
        # read as receding rather than as one crowd.
        d = ImageDraw.Draw(tile)
        for row, (base, hgt, y) in enumerate(((690, 160, 690),
                                             (636, 121, 636))):
            for c in range(9):
                x = 70 + c * 148 + row * 62
                _soldier(d, x, base, hgt, 320 + row * 20 + c, col=CLAY,
                         shade=CLAY_D, has_armour=False)
                PA.hand_stroke(d, [(x - 52, y - hgt * 0.52),
                                   (x + 52, y - hgt * 0.52)], INK, 5,
                               closed=False, seed=330 + row * 20 + c,
                               wavelength=70.0)
                for s in (-1, 1):
                    PA.fill_poly(tile, [(x + s * 46, y - hgt * 0.52),
                                        (x + s * 62, y - hgt * 0.52 + 22),
                                        (x + s * 46, y - hgt * 0.52 + 44)],
                                 CLAY_D, seed=340 + row * 20 + c + s,
                                 value=0.10)
    els.append(SC.accrue(clock, 20, 21, d_carriers, kind='shape',
                         eid='d_carriers',
                         motion=SC.enter(clock, 20, dx=0, dy=40,
                                         dur=ARRIVE)))
    els.append(cap(20, 640, 152, size=34))

    # ===================================================================== #
    # STAGE E  b21-b25  "He copied a pyramid. He built himself a heavenly    #
    #   palace. He is buried outside Xi'an. They were made to be different -- #
    #   every soldier a different height. No two faces the same."             #
    # One NIGHT backdrop for the whole stage. NO caption anywhere in it: every #
    # one of these five beats is an object on screen carrying its own words,  #
    # and adding narration text on top of a label is how a card ends up with   #
    # two things to read. That is five consecutive dropped beats and it is the #
    # right call -- this stage is the most purely visual stretch in the chapter.
    # ===================================================================== #
    def e_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 44, 66), seed=380, value=0.08)
        # A milky band across the sky before the stars. All five beats of this
        # stage measured 2.9-3.9 on a 430px sky that was one flat navy with
        # forty dots on it; the band plus a denser, brightness-varied starfield
        # turns the upper half into layered night instead of a fill.
        for k in range(9):
            # A drifting diagonal of OUTLINED lobes. Soft unoutlined blobs made
            # this WORSE -- they cost b23 2.4 points, because a smooth pale
            # ellipse on a smooth navy field is exactly the flat the gate is
            # hunting. The lobe has to carry an edge.
            cx = -80 + k * 170
            cy = 250 - (cx + 80) * 0.30 + ((k * 61) % 120) - 60
            rx = 130 + ((k * 47) % 110)
            ry = 40 + ((k * 29) % 34)
            PA.fill_poly(tile, PA.ellipse_pts(cx, cy, rx, ry, n=26),
                         (70, 70, 102), seed=1400 + k, value=0.10, tint=0.10,
                         band=0.30, edge=1.8)
            PA.hand_stroke(d, PA.ellipse_pts(cx, cy, rx, ry, n=26),
                           (40, 40, 68), 4, closed=True, seed=1405 + k,
                           wavelength=200.0)
        for k in range(5):      # dust lanes, following the same diagonal
            yy = 176 + k * 44
            PA.hand_stroke(d, [(-20, yy), (W + 20, yy - 130)], (36, 36, 60),
                           20, closed=False, seed=1410 + k, wavelength=240.0)
        PA.paper_overlay(tile, seed=381)
        for k in range(96):
            sx = (k * 197) % W
            sy = 96 + (k * 83) % 306
            sr = 1 + (k % 4)
            b = 168 + ((k * 53) % 84)
            PA.fill_poly(tile, PA.ellipse_pts(sx, sy, sr, sr, n=8),
                         (b, b, min(255, b + 8)), seed=382 + k, value=0.06)
            if k % 7 == 0:     # the brightest get a soft halo, not a cross --
                PA.hand_stroke(d, PA.arc_pts(sx, sy, sr * 3.2, sr * 3.2,
                                             0, 360, n=14),
                               (b - 40, b - 40, b - 32), 3, closed=False,
                               seed=1430 + k, wavelength=30.0)
        # AFTER the stars, per v1's c_palace: the lit course has to be the
        # topmost thing in the band or the stars punch holes in it.
        SC.title_backdrop(tile, 1382, col=(86, 88, 116))
        PA.fill_poly(tile, PA.ellipse_pts(1000, 150, 92, n=48), (238, 234, 216),
                     seed=384, value=0.06)
        for k, (cy, hh) in enumerate(((300, 26), (348, 20), (396, 30))):
            PA.fill_rect(tile, [760, cy, 1240, cy + hh], (58, 58, 82),
                         seed=385 + k, value=0.07)
        PA.fill_rect(tile, [0, 430, W, H], (30, 28, 34), seed=390, value=0.07)
        PA.hand_stroke(d, [(-10, 430), (1290, 430)], INK, 6, closed=False,
                       seed=391, wavelength=210.0)
        # Receding ground: three contour ridges below the horizon so the
        # lower band is receding night plain rather than one dark plane.
        for k, (col, base, amp) in enumerate((((44, 40, 46), 512, 26),
                                              ((58, 52, 58), 594, 34),
                                              ((72, 64, 68), 676, 40))):
            pts = [(-40, base + 60)]
            x = -40
            while x < W + 40:
                x += 78 + ((k * 41 + x) % 70)
                pts.append((x, base - amp * (0.30 + ((x * 11 + k * 47) % 60)
                                             / 100.0)))
            pts.append((W + 40, base + 60))
            PA.fill_poly(tile, pts, col, seed=1460 + k, value=0.11, tint=0.06,
                         band=0.30, edge=2.0)
            PA.hand_stroke(d, pts[1:-1], (22, 20, 26), 5, closed=False,
                           seed=1464 + k, wavelength=150.0)
            # scrub tufts along the ridge, so the plain is walked ground and
            # not three stacked ribbons
            for j in range(14):
                tx = -20 + j * 96 + ((k * 29 + j * 13) % 40)
                ty = base - amp * (0.30 + ((tx * 11 + k * 47) % 60) / 100.0)
                PA.fill_poly(tile, [(tx - 5, ty), (tx + 5, ty),
                                    (tx + 1, ty - 16 - (j % 3) * 6)],
                             (34, 34, 42), seed=1468 + k * 20 + j,
                             value=0.10, edge=1.0)
        # the mound, cropped by the left edge, and beside it a stepped pyramid
        # cropped by the right: the comparison the beat is making
        PA.fill_poly(tile, [(60, 720), (300, 300), (620, 300), (860, 720)],
                     (34, 30, 28), seed=392, value=0.08)
        # rammed-earth banding on the mound, clipped inside its own silhouette.
        # The bands were (52,46,42) on (34,30,28) -- eight levels of luma apart,
        # which is invisible at 24px. Real rammed earth is banded in LIGHT and
        # DARK lifts with a shadow line under each, so the contrast has to be
        # wide or the banding is just a slightly dirty trapezoid.
        for k in range(13):
            yy = 320 + k * 30
            if yy > 706:
                break
            hw = 160.0 + (yy - 300.0) * 0.588
            xl = 460 - hw + 8
            xr = 460 + hw - 8
            if xr - xl < 24:
                continue
            PA.hand_stroke(d, [(xl, yy), (xr, yy)],
                           (86, 76, 68) if k % 2 else (74, 64, 58), 8,
                           closed=False, seed=1470 + k, wavelength=130.0)
            PA.hand_stroke(d, [(xl, yy + 9), (xr, yy + 9)], (20, 18, 20), 5,
                           closed=False, seed=1475 + k, wavelength=130.0)
        # the ramps and cut faces a half-buried mound actually shows: two
        # stepped excavation cuts down the near face
        for k, (rx, rw) in enumerate(((300, 54), (640, 66))):
            for j in range(5):
                PA.fill_rect(tile, [rx - rw + j * 14, 470 + j * 46,
                                    rx + rw - j * 14, 470 + j * 46 + 44],
                             (56, 48, 44) if j % 2 else (68, 58, 52),
                             seed=1490 + k * 9 + j, value=0.11, edge=1.6)
        PA.hand_stroke(d, [(60, 720), (300, 300), (620, 300), (860, 720)],
                       INK, 6, closed=False, seed=393, wavelength=170.0)
        # the stepped pyramid: a course line and a lit face on each of five
        # steps, cropped by the right edge
        for k in range(5):
            PA.fill_rect(tile, [1130 + k * 34, 700 - k * 76, 1320,
                                700 - k * 76 + 76], (72, 64, 58),
                         seed=394 + k, value=0.07)
            PA.hand_stroke(d, [(1130 + k * 34, 700 - k * 76),
                               (1320, 700 - k * 76)], (104, 94, 84), 5,
                           closed=False, seed=1480 + k, wavelength=90.0)
        PA.hand_stroke(d, [(1130, 720), (1130, 320)], INK, 6, closed=False,
                       seed=399, wavelength=150.0)
    els.append(SC.stage(clock, 21, e_night, j=26))

    def e_copied(tile, fw, fh):
        # The comparison needs someone making it. b21 was backdrop plus one
        # label -- no character at all, and under-filled beats with no
        # character are the ones this project has lost most of. A presenter in
        # the gap between mound and pyramid, one arm out at the pyramid, at
        # 400px so he is a figure in the landscape rather than a doodle.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 1000, 700, 400, pose='pointing', expression='neutral',
                    seed=1478, ink=PALE)
        PA.hand_stroke(d, [(1036, 700 - 400 * 0.60), (1140, 700 - 400 * 0.76)],
                       INK, 8, closed=False, seed=1479, wavelength=60.0)
        D.draw_label(tile, 'COPIED A PYRAMID', center=(640, 150), color=GOLD,
                     size=40)
    els.append(SC.layer(clock, 21, e_copied, j=22, kind='shape',
                        eid='e_copied'))

    def e_palace(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-40, 720), (240, 470), (640, 420), (1040, 470),
                            (1320, 720)], (86, 36, 32), seed=400, value=0.10)
        # The roof was one smooth maroon trapezoid over the bottom 45% of the
        # frame, and b22 sat at 2.92 because of it. Roof tiles run in courses
        # PARALLEL to the eaves, so the course line at depth t is the ridge
        # shape scaled out from the crest: the ridge spans x 240..1040 with its
        # apex at y=420, the eave spans the full width at y=720.
        def course(t):
            return [(240.0 - 280.0 * t, 470.0 + 250.0 * t),
                    (640.0, 420.0 + 300.0 * t),
                    (1040.0 + 280.0 * t, 470.0 + 250.0 * t)]
        for k in range(11):
            t = 0.06 + k * 0.088
            pts = course(t)
            PA.hand_stroke(d, pts, (58, 24, 22), 7, closed=False,
                           seed=1500 + k, wavelength=200.0)
            PA.hand_stroke(d, [(x, y + 7) for x, y in pts], (124, 60, 46), 4,
                           closed=False, seed=1510 + k, wavelength=200.0)
        # the ridge cap itself, with its row of ridge-tile discs
        PA.hand_stroke(d, course(0.0), INK, 8, closed=False, seed=1520,
                       wavelength=200.0)
        for k in range(17):
            rx = 244 + k * 50
            if rx > 1036:
                break
            ry = 470 - abs(rx - 640) * (50.0 / 400.0)
            PA.fill_poly(tile, PA.ellipse_pts(rx, ry - 9, 13, 11, n=12),
                         (134, 68, 50), seed=1524 + k, value=0.12, edge=1.4)
            PA.hand_stroke(d, PA.arc_pts(rx, ry - 9, 13, 11, 0, 360, n=14),
                           INK, 4, closed=False, seed=1528 + k,
                           wavelength=30.0)
        # the upturned eave tips at both ends, cropped by the side edges
        for s in (-1, 1):
            tipx = 1280 if s > 0 else 0
            PA.fill_poly(tile, [(tipx, 520), (tipx - s * 150, 452),
                                (tipx - s * 250, 500), (tipx - s * 210, 566)],
                         (128, 62, 48), seed=1530 + s, value=0.11, edge=1.8)
            PA.hand_stroke(d, [(tipx, 520), (tipx - s * 150, 452),
                               (tipx - s * 250, 500)], INK, 6, closed=False,
                           seed=1534 + s, wavelength=90.0)
            for j in range(4):     # eave-tile discs along the lip
                dx = tipx - s * (34 + j * 34)
                dy = 512 + j * 15
                PA.fill_poly(tile, PA.ellipse_pts(dx, dy, 11, 11, n=12),
                             (146, 74, 54), seed=1538 + s * 7 + j,
                             value=0.12, edge=1.4)
        PA.hand_stroke(d, [(-40, 720), (240, 470), (640, 420), (1040, 470),
                           (1320, 720)], INK, 7, closed=False, seed=401,
                       wavelength=200.0)
    els.append(SC.accrue(clock, 22, 26, e_palace, kind='shape',
                         eid='e_palace'))

    def e_palace_name(tile, fw, fh):
        # The roof ACCRUES; its NAME does not. While the word lived inside the
        # accrue it was still on screen at b24 and b25, underneath 'ALL
        # DIFFERENT' and 'NO TWO THE SAME' -- two labels welded together at
        # (640,150). Text always hands off; scenery never does.
        D.draw_label(tile, 'HEAVENLY PALACE', center=(640, 150), color=GOLD,
                     size=44)
    els.append(SC.layer(clock, 22, e_palace_name, j=24, kind='shape',
                        eid='e_palace_name'))

    def e_xian(tile, fw, fh):
        # MOVING. The locator slides in as a PAPER INSET -- a panel of the
        # record register dropped onto the night, which is how you say "this
        # place is on a map" without leaving the shot.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [760, 300, 1260, 660], (240, 238, 228), seed=410,
                     value=0.05)
        PA.hand_stroke(d, [(760, 300), (1260, 300), (1260, 660), (760, 660)],
                       INK, 5, closed=True, seed=411, wavelength=160.0)
        # The inset is a MAP PANEL, and it was a blank pale rectangle with a
        # pale-grey rectangle on it -- 40k px of nothing in the middle of a beat
        # whose whole job is to say "this place, on a map". Grid it, draw the
        # Han river and the wall, mark the city.
        for k in range(9):      # graticule
            PA.hand_stroke(d, [(790, 336 + k * 22), (1232, 336 + k * 22)],
                           (214, 208, 194), 3, closed=False, seed=4600 + k,
                           wavelength=120.0)
        for k in range(15):
            PA.hand_stroke(d, [(790 + k * 30, 330), (790 + k * 30, 528)],
                           (214, 208, 194), 3, closed=False, seed=4610 + k,
                           wavelength=120.0)
        PA.fill_rect(tile, [800, 350, 1010, 520], (206, 200, 186), seed=412,
                     value=0.06)
        for k in range(9):      # the city wall's crenellations
            PA.fill_rect(tile, [800 + k * 24, 342, 812 + k * 24, 352],
                         (150, 144, 132), seed=413 + k, value=0.06)
        # the river, running out of the panel toward the city
        PA.hand_stroke(d, [(1006, 348), (1044, 396), (1078, 448),
                           (1120, 486), (1178, 508)], (74, 104, 132), 11,
                       closed=False, seed=422, wavelength=150.0)
        # the wall line, hatched
        PA.hand_stroke(d, [(1012, 528), (1080, 500), (1146, 470),
                           (1206, 452)], INK, 8, closed=False, seed=4620,
                       wavelength=110.0)
        for k in range(10):
            tx = 1022 + k * 20
            ty = 524 - k * 8
            PA.hand_stroke(d, [(tx, ty), (tx + 9, ty + 13)], INK, 3,
                           closed=False, seed=4622 + k, wavelength=25.0)
        PA.fill_rect(tile, [1140, 368, 1236, 500], (150, 104, 66), seed=424,
                     value=0.08)
        PA.hand_stroke(d, [(1140, 368), (1236, 368), (1236, 500), (1140, 500)],
                       INK, 5, closed=True, seed=425, wavelength=120.0)
        for k in range(5):      # roof ridges on the walled town
            PA.hand_stroke(d, [(1148, 396 + k * 22), (1228, 396 + k * 22)],
                           (92, 60, 38), 5, closed=False, seed=4640 + k,
                           wavelength=50.0)
        PA.fill_poly(tile, PA.ellipse_pts(1090, 452, 13, 13, n=14), FIRE,
                     seed=4650, value=0.10, edge=1.6)
        PA.hand_stroke(d, PA.arc_pts(1090, 452, 22, 22, 0, 360, n=18), INK, 4,
                       closed=False, seed=4651, wavelength=40.0)
        D.draw_label(tile, "XI'AN", center=(900, 588), color=INK, size=26)
        D.draw_label(tile, 'OUTSIDE', center=(1180, 588), color=INK, size=24)
    els.append(SC.accrue(clock, 23, 26, e_xian, kind='shape', eid='e_xian',
                         # DROPPED IN, not slid in from the right. dx=+90 put
                         # the whole inset 90px right at arrival: the panel's
                         # right border and the "OUTSIDE" label (home ink ends
                         # x=1259) both ran off the frame, and the first ~0.1s
                         # showed a half-word "OU" hanging at the edge. A
                         # vertical arrival is what "dropped onto the night"
                         # actually looks like, and it leaves the horizontal
                         # extent untouched -- panel 760..1260 and both labels
                         # stay inside at every frame of the move.
                         motion=SC.enter(clock, 23, dx=0, dy=40,
                                         dur=ARRIVE)))

    def e_heights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # a measuring stick, clipped at y=104 rather than y=0 so it stays clear
        # of the title band
        PA.fill_rect(tile, [700, 104, 748, 680], (216, 208, 188), seed=430,
                     value=0.05)
        for k in range(9):
            PA.fill_rect(tile, [700, 120 + k * 62, 748, 128 + k * 62],
                         (120, 106, 88), seed=431 + k, value=0.06)
        for x, hgt in ((170, 440), (400, 370), (620, 500)):
            _soldier(d, x, 680, hgt, 440 + x, col=CLAY, shade=CLAY_D,
                     has_armour=False)
        D.draw_label(tile, 'ALL DIFFERENT', center=(640, 150), color=GOLD,
                     size=38)
    els.append(SC.layer(clock, 24, e_heights, j=25, kind='shape',
                        eid='e_heights'))

    def e_faces(tile, fw, fh):
        # Two heads cropped by the side edges, the way a portrait pair is
        # actually cropped. Feet at 900 with h=780 puts the head tops at y=96,
        # clear of the 0-73 title band -- v1 used h=820 and reached y=54, which
        # put two heads inside the band.
        d = ImageDraw.Draw(tile)
        _soldier(d, 60, 900, 780, 450, col=CLAY, shade=CLAY_D,
                 has_armour=False)
        _soldier(d, 1220, 900, 780, 451, col=CLAY_L, shade=EARTH,
                 has_armour=False)
        d.line([(30, 214), (92, 226)], fill=CLAY_D, width=7)      # moustache
        d.line([(1196, 232), (1252, 246)], fill=CLAY_D, width=6)  # scar
        D.draw_label(tile, 'NO TWO THE SAME', center=(640, 150), color=PALE,
                     size=40)
    els.append(SC.layer(clock, 25, e_faces, j=26, kind='shape',
                        eid='e_faces'))

    # ===================================================================== #
    # STAGE F  b26-b31  "They were still there. Two thousand years. Then, in #
    #   1974, a group of farmers was digging a well. They hit something hard. #
    #   It was a clay shoulder. And then it broke."                           #
    # The SURVEY register: blueprint-blue sky, pale earth. One light backdrop #
    # for six beats, and the dig goes DOWNWARD through the frame -- outline,   #
    # well, blade, shoulder, break, cover -- so the stage has a direction even #
    # though the camera never moves.                                          #
    # ===================================================================== #
    def f_field(tile, fw, fh):
        _earth_field(tile, 560, sky=BLUE_L, ground=(178, 152, 118), hz=520)
        d = ImageDraw.Draw(tile)
        # This backdrop carried all six beats of the dig and every one of them
        # measured 3.0-3.2: 330px of unmodulated blueprint sky and 200px of flat
        # tan. It is a survey register, so draw it like one -- a measured grid
        # in the sky, a pegged and staked dig site on the ground, a spoil heap,
        # and a survey pole -- and the two-thousand-years beat finally has a
        # place to be.
        hz = 520
        for k in range(11):     # survey grid in the sky register
            gx = 60 + k * 116
            PA.hand_stroke(d, [(gx, 84), (gx, hz - 6)], (176, 200, 218), 3,
                           closed=False, seed=2660 + k, wavelength=190.0)
        for k in range(4):
            gy = 120 + k * 96
            PA.hand_stroke(d, [(0, gy), (W, gy)], (176, 200, 218), 3,
                           closed=False, seed=2670 + k, wavelength=210.0)
        # a low ridge on the horizon so the sky meets land
        pts = [(-40, hz + 30)]
        x = -40
        while x < W + 40:
            x += 96 + ((x * 7) % 70)
            pts.append((x, hz - 26 - ((x * 13) % 30)))
        pts.append((W + 40, hz + 30))
        PA.fill_poly(tile, pts, (150, 168, 182), seed=2680, value=0.09,
                     band=0.22, edge=1.6)
        PA.hand_stroke(d, pts[1:-1], (118, 140, 158), 5, closed=False,
                       seed=2684, wavelength=160.0)
        # survey pegs and string lines marking the dig square
        for px, py in ((196, 604), (958, 596), (250, 468), (908, 462)):
            PA.hand_stroke(d, [(px, py), (px + 4, py - 52)], (86, 72, 58), 7,
                           closed=False, seed=2690 + px, wavelength=40.0)
            PA.fill_poly(tile, PA.ellipse_pts(px, py - 54, 8, 8, n=10),
                         (198, 62, 48), seed=2694 + px, value=0.10, edge=1.2)
        for a, b in (((200, 552), (956, 544)), ((254, 466), (250, 550)),
                     ((912, 460), (956, 542))):
            PA.hand_stroke(d, [a, b], (206, 96, 66), 3, closed=False,
                           seed=2698 + a[0], wavelength=120.0)
        # the spoil heap the farmers have been throwing out
        PA.fill_poly(tile, [(120, 700), (250, 588), (410, 596), (470, 700)],
                     (150, 124, 92), seed=2700, value=0.11, band=0.24,
                     edge=1.8)
        PA.hand_stroke(d, [(120, 700), (250, 588), (410, 596), (470, 700)],
                       INK, 6, closed=True, seed=2701, wavelength=130.0)
        for k in range(6):
            PA.hand_stroke(d, [(160 + k * 48, 692), (200 + k * 44, 620)],
                           (176, 148, 112), 5, closed=False, seed=2704 + k,
                           wavelength=60.0)
        _rubble(tile, d, (0, 600, 1280, 720), 22, seed=2710, col=(162, 136, 102),
                rmin=7, rmax=22)
        for k in range(7):     # furrows running off the right edge
            yy = hz + 40 + k * 30
            PA.hand_stroke(d, [(700, yy), (W + 30, yy - 16)], (160, 134, 100), 5,
                           closed=False, seed=2720 + k, wavelength=170.0)
    els.append(SC.stage(clock, 26, f_field, j=32))

    def f_outline(tile, fw, fh):
        # The two-thousand-years beat. v1 drew a bare closed quad on the
        # ground and the beat came out at 3.06 in a 1280px frame -- four thin
        # strokes over an empty field. It still earns its place (there IS
        # nothing to look at yet, which is the joke) but the nothing now has
        # to be a MARKED-OUT excavation square: pegs, string, a scale bar and
        # a spoil ring, so the emptiness is deliberate and surveyed rather than
        # unfinished.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(150, 604), (900, 466), (980, 600), (180, 710)],
                     (196, 172, 134), seed=570, value=0.10, band=0.22,
                     edge=1.6)
        PA.hand_stroke(d, [(180, 470), (900, 466), (980, 600), (150, 604)],
                       EARTH_D, 8, closed=True, seed=572, wavelength=180.0)
        for px, py in ((180, 470), (900, 466), (980, 600), (150, 604)):
            PA.hand_stroke(d, [(px, py), (px + 3, py - 44)], (78, 64, 50), 6,
                           closed=False, seed=574 + px, wavelength=35.0)
            PA.fill_poly(tile, PA.ellipse_pts(px, py - 46, 7, 7, n=10),
                         (198, 62, 48), seed=578 + px, value=0.10, edge=1.1)
        for a, b in (((184, 468), (898, 464)), ((902, 468), (978, 598)),
                     ((978, 602), (152, 606)), ((152, 602), (178, 472))):
            PA.hand_stroke(d, [a, b], (204, 96, 66), 3, closed=False,
                           seed=582 + a[0], wavelength=110.0)
        for k in range(4):     # scale bar along the near edge
            bx = 620 + k * 74
            PA.fill_rect(tile, [bx, 656, bx + 74, 674], INK, seed=586 + k,
                         value=0.0, tint=0.0)
            if k % 2:
                PA.fill_rect(tile, [bx, 656, bx + 74, 674], (238, 236, 226),
                             seed=590 + k, value=0.05)
        _rubble(tile, d, (620, 600, 1000, 700), 10, seed=594,
                col=(166, 140, 106), rmin=8, rmax=20)
        D.draw_label(tile, '2,000 YEARS', center=(880, 250), color=GOLD,
                     size=40)
    els.append(SC.layer(clock, 26, f_outline, j=27, kind='shape',
                        eid='f_outline'))

    def f_face_a(tile, fw, fh):
        # MOVING. Bottom-left, small, and it never gets in the way of the dig:
        # the face spans x -142..262 and the well starts at 820.
        SC.closeup(ImageDraw.Draw(tile), 60, 600, 130, 'confused', 310)
    els.append(E3.E('f_face_a', 'character', f_face_a, at=T(26), until=T(29),
                    motion=SC.enter(clock, 26, dx=-150, dy=0, dur=0.55)))
    # The swap: same position, same size, one beat later -- confusion becoming
    # shock is the whole point of the clay-shoulder beat.
    _fbu, _faa, _fau = SC.expr_swap(clock, 29, 'confused', 'shock',
                                    until_j=31)

    def f_face_b(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 60, 600, 130, 'shock', 310)
    els.append(E3.E('f_face_b', 'character', f_face_b, at=_faa, until=_fau))

    def f_well(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(820, 720), (860, 540), (1160, 540), (1200, 720)],
                     EARTH_D, seed=580, value=0.10)
        PA.hand_stroke(d, [(840, 540), (1180, 540)], INK, 7, closed=False,
                       seed=581, wavelength=140.0)
        for x, hgt in ((540, 400), (700, 380)):
            SC.fullbody(d, x, 700, hgt, pose='pointing', expression='neutral',
                        seed=582 + x)
            PA.hand_stroke(d, [(x + 40, 700 - hgt * 0.62),
                               (x + 96, 700 - hgt * 0.86)], INK, 7,
                           closed=False, seed=583 + x, wavelength=60.0)
            PA.fill_poly(tile, [(x + 90, 700 - hgt * 0.86),
                                (x + 124, 700 - hgt * 0.90),
                                (x + 112, 700 - hgt * 0.70),
                                (x + 84, 700 - hgt * 0.74)], (128, 106, 80),
                         seed=584 + x, value=0.08)
        D.draw_label(tile, '1974', center=(240, 140), color=INK, size=52)
    els.append(SC.layer(clock, 27, f_well, j=28, kind='character',
                        eid='f_well'))
    els.append(cap(27, 1080, 190, size=32))

    def f_blade(tile, fw, fh):
        # MOVING. The blade comes in from off-frame left. A shovel is about
        # 300px tall, which is the size the motion rule actually wants.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-60, 300), (120, 250), (300, 330), (280, 470),
                            (100, 500), (-60, 440)], (128, 106, 80),
                     seed=590, value=0.09)
        PA.hand_stroke(d, [(280, 380), (620, 470)], (110, 88, 64), 16,
                       closed=False, seed=591, wavelength=120.0)
        PA.fill_poly(tile, PA.ellipse_pts(700, 420, 190, 150, n=40),
                     (176, 106, 66), seed=592, value=0.08)
        D.draw_label(tile, 'SOMETHING HARD', center=(900, 200), color=INK,
                     size=40)
    els.append(SC.layer(clock, 28, f_blade, j=29, kind='shape',
                        eid='f_blade',
                        motion=SC.enter(clock, 28, dx=-70, dy=0,
                                        dur=ARRIVE)))

    def f_shoulder(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _soldier(d, 950, 800, 620, 600, col=CLAY_L, shade=EARTH,
                 has_armour=False, crop=True)
        for k in range(14):
            PA.fill_poly(tile, PA.ellipse_pts(600 + (k * 173) % 700,
                                              300 + (k * 97) % 340,
                                              13, 8, n=12), EARTH_D,
                         seed=601 + k, value=0.08)
    els.append(SC.accrue(clock, 29, 32, f_shoulder, kind='shape',
                         eid='f_shoulder'))
    els.append(cap(29, 420, 180, size=32))

    def f_break(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(280, 250), (560, 262), (720, 320), (700, 640),
                            (420, 600), (280, 470)], CLAY, seed=610,
                     value=0.09)
        PA.hand_stroke(d, [(470, 250), (500, 350), (470, 420), (510, 520)],
                       INK, 7, closed=False, seed=611, wavelength=90.0)
        for k, (fx, fy, fr) in enumerate(((760, 620, 44), (830, 560, 30),
                                          (700, 680, 26), (860, 640, 20))):
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, fr, fr * 0.7, n=20),
                         CLAY_D, seed=612 + k, value=0.10)
        # INK, not PALE: v1 drew this in PALE on the BLUE_L sky, which measures
        # about 1.35:1 and was unreadable at ship size.
        D.draw_label(tile, 'IT BROKE', center=(1000, 200), color=INK,
                     size=44)
    els.append(SC.layer(clock, 30, f_break, j=31, kind='shape',
                        eid='f_break'))

    def f_cover(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [980, 420, 1340, 640], (206, 200, 186), seed=620,
                     value=0.06)
        PA.hand_stroke(d, [(980, 420), (1340, 420)], INK, 6, closed=False,
                       seed=621, wavelength=120.0)
        PA.fill_poly(tile, [(300, 700), (420, 566), (700, 548), (880, 596),
                            (920, 700)], (176, 172, 162), seed=622,
                     value=0.07)
        PA.hand_stroke(d, [(300, 700), (420, 566), (700, 548), (880, 596),
                           (920, 700)], INK, 6, closed=False, seed=623,
                       wavelength=140.0)
        D.draw_label(tile, 'COVERED OVER', center=(640, 220), color=INK,
                     size=40)
    els.append(SC.layer(clock, 31, f_cover, j=32, kind='shape',
                        eid='f_cover'))

    # ===================================================================== #
    # STAGE G  b32-b37  "In 2012 they opened a new pit. Inside: more than a  #
    #   thousand soldiers. Two bronze cranes had been broken. Somebody        #
    #   repaired them with modern glue. In 1983 a farmer poured acid on the   #
    #   figures, and the markings can never be read again."                  #
    # Opens on PAPER2 for b32, then b33 cuts to a full-frame dark REPLACE for #
    # the pit full -- a thousand figures cannot be drawn on the plan paper --  #
    # and b37 cuts again to flat grey. Three registers in six beats, and each #
    # cut is a thing the narration actually says.                             #
    # ===================================================================== #
    def g_paper(tile, fw, fh):
        # Measured 3.06 -- one of the three worst beats in the chapter. v1's
        # `_interior` here is a single PAPER2 rectangle with tooth over it, and
        # PAPER2 on PAPER2 is a 10-value difference: the whole frame is one
        # smooth shape. The beat is "in 2012 they opened a new pit", so it is
        # a SURVEY PLAN, and a plan is the most edge-rich thing a pale sheet
        # can carry: a measured grid, a hatched site boundary, a north arrow,
        # a scale bar, contour traces, and the plan's own annotation blocks.
        # Nothing here is a label the narration also says; the caption at b32
        # carries the words, this carries the drawing.
        _interior(tile, 650, PAPER2)
        d = ImageDraw.Draw(tile)
        # --- the measured grid, drawn faintly so it never competes with the
        # plan line but still breaks every 100px of paper into cells.
        for k in range(14):
            gx = -30 + k * 100
            PA.hand_stroke(d, [(gx, 86), (gx, H)], (188, 182, 170), 3,
                           closed=False, seed=1650 + k, wavelength=200.0)
        for k in range(7):
            gy = 96 + k * 100
            PA.hand_stroke(d, [(0, gy), (W, gy)], (188, 182, 170), 3,
                           closed=False, seed=1660 + k, wavelength=210.0)
        # The margin ABOVE the site boundary was the last smooth field in this
        # beat: 180px of PAPER2 between the title band and the cut line, which
        # is seven full rows of tiles at the fill's own drift. It is hatched on
        # the cross direction, so the two hatch fields meet at the boundary at
        # right angles -- which is what a section drawing looks like, and it
        # means no part of the sheet is left as an unhatched void.
        _hatch(tile, d, [(-60, 86), (1340, 86), (1340, 178), (-60, 178)],
               seed=1645, col=(180, 172, 158), spacing=22, width=3,
               angle=-0.58)
        # heavier grid every fifth cell, so the sheet reads as a measured plan
        # rather than as graph paper
        for k in range(3):
            PA.hand_stroke(d, [(-30 + k * 500, 86), (-30 + k * 500, H)],
                           (128, 118, 104), 5, closed=False, seed=1670 + k,
                           wavelength=220.0)
        for k in range(2):
            PA.hand_stroke(d, [(0, 96 + k * 500), (W, 96 + k * 500)],
                           (128, 118, 104), 5, closed=False, seed=1675 + k,
                           wavelength=230.0)
        # --- the pit site boundary: a stepped, wobbled polygon running off
        # BOTH side edges and off the bottom, hatched on its inside edge. A
        # plan that stops short of the frame is a plan that fits in a picture;
        # this one admits the dig is bigger than the sheet.
        site = [(-60, 236), (150, 206), (330, 222), (470, 180), (700, 196),
                (880, 168), (1080, 200), (1340, 176)]
        PA.fill_poly(tile, site + [(1340, H), (-60, H)], (196, 186, 168),
                     seed=1680, value=0.07, band=0.08, edge=1.6)
        # The site fill is hatched, not left smooth: a section/plan of a cut
        # is hatched on the drawing, and the hatch is what lifts every interior
        # 24px tile off the flat-fill floor. Spacing 22px, one axis -- dense
        # enough to reach every tile, open enough to still read as a drawing.
        # (See _hatch for why cells alone were not enough.)
        _hatch(tile, d, site + [(1340, H), (-60, H)], seed=1683,
               col=(166, 156, 140), spacing=22, width=3, angle=0.62)
        PA.hand_stroke(d, site, INK, 7, closed=False, seed=1681,
                       wavelength=200.0)
        # hatch ticks hanging off the boundary -- the survey convention for
        # "this is the cut". Forty small strokes is the edge density that a
        # flat sheet does not have.
        hx = -40
        k = 0
        while hx < W + 40:
            hpy = 176 + ((hx * 13) % 60)
            PA.hand_stroke(d, [(hx, hpy), (hx + 16, hpy + 30)], (108, 98, 86), 4,
                           closed=False, seed=1685 + k, wavelength=40.0)
            hx += 34
            k += 1
        # --- contour traces inside the site: three nested wobbled rings, the
        # way a plan shows the original mound's footprint. Each ring FILLS a
        # stepped tone darker than the one inside it, so the mound reads as a
        # landform on the plan instead of three hairlines in the paper.
        mound = ((0.42, (176, 164, 142), (112, 100, 84), 6),
                 (0.66, (192, 182, 162), (134, 122, 104), 5),
                 (0.86, (206, 198, 180), (156, 144, 126), 5))
        for ci, (sc, fill, col, wd) in enumerate(mound):
            pts = []
            for s in range(29):
                a = 6.283185 * s / 28.0
                rx = 430.0 * sc * (1.0 + 0.06 * math.sin(a * 3 + ci))
                ry = 210.0 * sc * (1.0 + 0.08 * math.cos(a * 2 - ci))
                pts.append((640 + rx * math.cos(a), 448 + ry * math.sin(a)))
            PA.fill_poly(tile, pts, fill, seed=1688 + ci, value=0.07,
                         band=0.07, edge=1.4)
            PA.hand_stroke(d, pts, col, wd, closed=True, seed=1690 + ci,
                           wavelength=190.0)
        # --- the grid of sounding squares that fills the site's interior, so
        # the middle of the frame is a lattice of small outlined cells and not
        # one pale region. Seven by four, at the scale a pit plan uses, with a
        # clear tone step against the site fill so the squares are squares.
        for r in range(4):
            for c in range(8):
                x0 = 250 + c * 122
                y0 = 316 + r * 94
                PA.fill_rect(tile, [x0 + 3, y0 + 3, x0 + 116, y0 + 88],
                             (222, 216, 202) if (r + c) % 2 else (166, 154,
                             134), seed=1700 + r * 9 + c, value=0.07, edge=1.4)
                PA.hand_stroke(d, [(x0 + 3, y0 + 3), (x0 + 116, y0 + 3),
                                   (x0 + 116, y0 + 88), (x0 + 3, y0 + 88)],
                               (86, 76, 64), 4, closed=True,
                               seed=1710 + r * 7 + c, wavelength=70.0)
                # Every cell carries its own fine hatch. A sounded square on a
                # real plan is a gridded/hatched patch, and it is the only way
                # a 24px tile at the CENTRE of a 114x86 cell stops being flat
                # fill -- the cell's own border is only in the corner tiles.
                _hatch(tile, d, [(x0 + 5, y0 + 5), (x0 + 114, y0 + 5),
                                 (x0 + 114, y0 + 86), (x0 + 5, y0 + 86)],
                       seed=1780 + r * 8 + c, col=(150, 138, 120), spacing=20,
                       width=2, angle=0.7 if (r + c) % 2 else -0.7)
                # a sounding figure in every third cell: the small number a
                # plan actually carries, as a tick and a dot.
                if (r * 8 + c) % 3 == 0:
                    PA.fill_poly(tile, PA.ellipse_pts(x0 + 60, y0 + 46, 9, 9,
                                                      n=12), (86, 76, 64),
                                 seed=1760 + r * 8 + c, value=0.05, edge=1.0)
                    PA.hand_stroke(d, [(x0 + 60, y0 + 58), (x0 + 60, y0 + 82)],
                                   (86, 76, 64), 3, closed=False,
                                   seed=1770 + r * 8 + c, wavelength=30.0)
        # --- survey furniture at the edges: north arrow (top right), scale bar
        # (bottom left), and a title block of small ruled boxes (bottom right).
        nx0, ny0 = 1130, 240
        PA.hand_stroke(d, [(nx0, ny0 + 90), (nx0, ny0 - 10)], INK, 7,
                       closed=False, seed=1720, wavelength=90.0)
        PA.fill_poly(tile, [(nx0, ny0 - 46), (nx0 - 24, ny0 + 18),
                            (nx0 + 24, ny0 + 18)], INK, seed=1721, value=0.0)
        PA.hand_stroke(d, [(nx0 - 38, ny0 + 48), (nx0 + 38, ny0 + 48)], INK, 6,
                       closed=False, seed=1722, wavelength=40.0)
        for k in range(4):
            PA.fill_rect(tile, [40 + k * 52, 664, 92 + k * 52, 690],
                         INK if k % 2 else (232, 228, 218), seed=1725 + k,
                         value=0.05, edge=1.6)
        PA.hand_stroke(d, [(40, 692), (248, 692)], INK, 6, closed=False,
                       seed=1730, wavelength=80.0)
        for k in range(5):     # title block: five ruled rows of small boxes
            PA.fill_rect(tile, [900, 590 + k * 26, 1250, 612 + k * 26],
                             (226, 220, 206) if k % 2 else (160, 148, 128),
                         seed=1735 + k, value=0.06, edge=1.4)
            PA.hand_stroke(d, [(900, 590 + k * 26), (1250, 590 + k * 26)],
                           (84, 74, 62), 4, closed=False, seed=1740 + k,
                           wavelength=80.0)
    els.append(SC.stage(clock, 32, g_paper, j=38))

    def g_corridor(tile, fw, fh):
        # v1 drew this L of two corridors in the middle third of a pale frame and
        # the beat came out nearly blank. Scaled up to run off both side edges
        # and off the bottom, with the vault row reading as a row: the plan is
        # supposed to look BIGGER than the frame, which is what a pit does.
        d = ImageDraw.Draw(tile)
        LEFT = [(-60, 720), (-60, 470), (430, 470), (430, 720)]
        BOT = [(430, 720), (430, 330), (1340, 330), (1340, 720)]
        PA.fill_poly(tile, LEFT, (216, 210, 196), seed=700, value=0.06)
        PA.fill_poly(tile, BOT, (208, 202, 188), seed=702, value=0.06)
        # The two corridor runs are 490x250 and 910x390 of near-PAPER2 fill.
        # They are the LARGEST smooth shapes in this beat and they sit ON TOP of
        # the plan sheet, so no amount of work underneath them reaches the
        # pixels the eye and the gate see. A cut-through corridor on a pit plan
        # is drawn with the excavated earth hatched on ONE axis -- a single
        # direction at 26px, lighter than the boundary ink. Cross-hatching at
        # 15px was tried and rejected: it cleared the metric by a wider margin
        # but read at ship size as machine-made textile rather than as a drawn
        # plan, which is the defect the metric is supposed to catch (memory
        # flat-vector-fails-the-style-bar -- the bar is painterly, not noisy).
        _hatch(tile, d, LEFT, seed=7005, col=(178, 166, 148), spacing=26,
               width=3, angle=0.62)
        _hatch(tile, d, BOT, seed=7007, col=(172, 160, 142), spacing=26,
               width=3, angle=0.62)
        PA.hand_stroke(d, [(-60, 720), (-60, 470), (430, 470), (430, 720)],
                       INK, 7, closed=True, seed=701, wavelength=140.0)
        PA.hand_stroke(d, [(430, 720), (430, 330), (1340, 330), (1340, 720)],
                       INK, 7, closed=True, seed=703, wavelength=160.0)
        for k in range(8):
            vx = 500 + k * 108
            PA.fill_rect(tile, [vx, 380, vx + 72, 476], (176, 168, 152),
                         seed=704 + k, value=0.06, edge=1.4)
            PA.hand_stroke(d, [(vx, 476), (vx + 72, 476)], INK, 5,
                           closed=False, seed=712 + k, wavelength=60.0)
            # a cross-rib inside each bay, so the vault row is a row of rooms
            PA.hand_stroke(d, [(vx + 36, 380), (vx + 36, 476)], INK, 4,
                           closed=False, seed=730 + k, wavelength=45.0)
        for k in range(4):
            vx = 30 + k * 108
            PA.fill_rect(tile, [vx, 520, vx + 72, 616], (176, 168, 152),
                         seed=720 + k, value=0.06, edge=1.4)
            PA.hand_stroke(d, [(vx, 616), (vx + 72, 616)], INK, 5,
                           closed=False, seed=724 + k, wavelength=60.0)
            PA.hand_stroke(d, [(vx + 36, 520), (vx + 36, 616)], INK, 4,
                           closed=False, seed=740 + k, wavelength=45.0)
        # side-walls drawn INSIDE the corridor runs, off both frame edges: the
        # corridor is a trench with two faces, and those faces are where the
        # section's texture belongs.
        for yy in range(346, 720, 34):
            PA.hand_stroke(d, [(-60, yy), (430, yy)], (120, 108, 92), 3,
                           closed=False, seed=750 + yy, wavelength=90.0)
        for yy in range(486, 720, 34):
            PA.hand_stroke(d, [(-60, yy), (430, yy)], (120, 108, 92), 3,
                           closed=False, seed=790 + yy, wavelength=90.0)
        for k in range(24):
            xx = 430 + k * 40
            PA.hand_stroke(d, [(xx, 330), (xx, 720)], (126, 114, 98), 3,
                           closed=False, seed=830 + k, wavelength=90.0)
        # NO drawn 'PIT 1 - 2012': the caption at b32 says it, and saying it
        # twice in one beat is the pile-up this file exists to avoid.
    els.append(SC.accrue(clock, 32, 38, g_corridor, kind='shape',
                         eid='g_corridor'))
    els.append(cap(32, 640, 676, size=32))

    def g_pitfull(tile, fw, fh):
        # v1 drew this as a 5x9 grid of identical 150px soldiers tiled edge to
        # edge, which at ship size reads as WALLPAPER, not as a pit: the figures
        # are all one size, one colour and one silhouette, so the eye finds a
        # repeating motif instead of a thousand men. Four rows at four scales
        # with the near row dominant and cropped, and the far rows dimmed, so
        # the same count of figures now reads as DEPTH. Armour on the near rows
        # breaks the repeated silhouette; it is off on the far rows, where the
        # detail would be invisible anyway.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (104, 82, 60), seed=710, value=0.08)
        PA.paper_overlay(tile, seed=711)
        SC.title_backdrop(tile, 1711, col=(118, 92, 70))
        rows = ((375, 165, 105, (128, 84, 52), (98, 62, 38), False),
                (470, 215, 140, (146, 94, 58), (112, 70, 42), False),
                (600, 290, 190, (170, 108, 64), (128, 80, 48), True),
                (760, 400, 320, CLAY, CLAY_D, True))
        for r, (feet, hgt, step, col, shd, arm) in enumerate(rows):
            x = -40 if r < 3 else -20
            c = 0
            while x < W + 120:
                _soldier(d, x, feet, hgt, 720 + r * 9 + c, col=col,
                         shade=shd, has_armour=arm)
                x += step
                c += 1
        # The label is NOT inside this layer. It gets its own one-beat element
        # below, because this layer lives b33-b37 and a word living in it would
        # still be on screen at b34 and b35, 30px under BOTH BROKEN and
        # REPAIRED WITH MODERN GLUE.
    els.append(SC.layer(clock, 33, g_pitfull, j=38, kind='bg',
                        eid='g_pitfull'))

    def g_thousand(tile, fw, fh):
        # Moved UP out of the figures: at y=672 it lay across the near row's
        # shins, and it has to clear the title band too. y=120 sits in the gap
        # -- band ends at 73, far row head tops begin at 205.
        D.draw_label(tile, '1,000+ SOLDIERS', center=(640, 120), color=PALE,
                     size=40)
    els.append(SC.layer(clock, 33, g_thousand, j=34, kind='shape',
                        eid='g_thousand'))

    def g_cranes(tile, fw, fh):
        # The cranes are v1's primitive and its body is a wide flat ellipse --
        # at this scale the ellipse IS most of the silhouette, which is why
        # v1's version read as an olive on a stick. Two staging changes fix the
        # read without touching the primitive: they sit on the DARK ground in
        # front of the lit grid rather than centred on it, so there is plain
        # background behind the neck and head, and they are pushed to the side
        # edges so nothing important is behind them.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 596, W, H], (74, 58, 44), seed=805, value=0.07)
        PA.hand_stroke(d, [(-10, 596), (1290, 596)], INK, 6, closed=False,
                       seed=806, wavelength=200.0)
        _crane(d, 210, 690, 500, 801, broken=True)
        _crane(d, 1080, 706, 420, 802, broken=True, flip=True)
    els.append(SC.accrue(clock, 34, 38, g_cranes, kind='shape',
                         eid='g_cranes'))

    def g_cranes_name(tile, fw, fh):
        # Separate from the cranes for the same reason as HEAVENLY PALACE: the
        # word has to be gone before REPAIRED WITH MODERN GLUE lands on it.
        D.draw_label(tile, 'BOTH BROKEN', center=(640, 150), color=PALE,
                     size=40)
    els.append(SC.layer(clock, 34, g_cranes_name, j=35, kind='shape',
                        eid='g_cranes_name'))

    def g_repair(tile, fw, fh):
        # REPLACES the two broken cranes, because the repaired crane stands
        # where they stood and drawing both would be two birds in one place.
        # It goes back to the CENTRE here: that is the point of the beat, the
        # bird is whole again, and it is the only moment in the chapter where
        # a crane is the subject rather than a detail.
        d = ImageDraw.Draw(tile)
        _crane(d, 560, 690, 500, 803, broken=True, repaired=True)
        PA.fill_rect(tile, [1060, 330, 1160, 560], (222, 226, 230), seed=804,
                     value=0.05)
        PA.hand_stroke(d, [(1060, 330), (1110, 250), (1160, 330)], INK, 6,
                       closed=False, seed=805, wavelength=60.0)
        PA.hand_stroke(d, [(1110, 380), (1180, 470)], (150, 110, 60), 12,
                       closed=False, seed=806, wavelength=70.0)
        PA.fill_poly(tile, [(1174, 452), (1220, 462), (1210, 512),
                            (1168, 502)], (168, 128, 70), seed=807,
                     value=0.08)
        D.draw_label(tile, 'REPAIRED WITH MODERN GLUE', center=(640, 150),
                     color=PALE, size=34)
    els.append(SC.layer(clock, 35, g_repair, j=36, kind='shape',
                        eid='g_repair'))

    def g_acid(tile, fw, fh):
        # MOVING -- and this is the ONE larger motion the chapter earns. The
        # acid eating a figure is movement that IS the event; a drift on a
        # backdrop would be movement that is decoration.
        # A full-frame REPLACE, not an accrue: the two broken cranes from b34
        # own the right side of this frame, and the acid jar has to stand
        # exactly there. Same part of the frame, so one of them has to go.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (104, 82, 60), seed=810, value=0.08)
        PA.paper_overlay(tile, seed=811)
        SC.title_backdrop(tile, 1811, col=(118, 92, 70))
        # b36 measured 3.35: one 600px slab of (104,82,60) earth behind a
        # single figure is the biggest smooth shape in the frame. This is the
        # cut face of the pit, so give it what a cut face has -- stacked strata
        # bands of differing tone, a rammed-earth course grid pressed into the
        # near band, and rubble at the toe. The figure still owns the left, the
        # jar still owns the right; the middle third that was dead earth now
        # reads as ground that was cut.
        _cut_face(tile, d, 90, 200, 1280, 600, seed=1815, base=(104, 82, 60))
        PA.fill_rect(tile, [0, 600, W, H], (74, 58, 44), seed=812,
                     value=0.07)
        _slab_floor(tile, d, 600, H, seed=1817, col=(86, 66, 50), n=14)
        _rubble(tile, d, (0, 604, 1280, 716), 26, seed=1818,
                col=(92, 72, 54), rmin=9, rmax=26)
        PA.hand_stroke(d, [(-10, 600), (1290, 600)], INK, 6, closed=False,
                       seed=813, wavelength=200.0)
        _soldier(d, 420, 880, 700, 810, col=(150, 108, 70),
                 shade=(112, 80, 52), has_armour=True)
        # The jar was at x 1130-1320, i.e. two thirds of it off the right edge,
        # so the acid appeared to pour in from nowhere. Brought fully into frame
        # and given a visible neck and shoulder, and the flow thickened, so the
        # beat reads as something POURING ON a figure.
        PA.fill_poly(tile, [(1010, 190), (1250, 190), (1215, 400), (1045, 400)],
                     (150, 150, 146), seed=814, value=0.06)
        PA.hand_stroke(d, [(1130, 190), (1130, 120)], (150, 150, 146), 26,
                       closed=False, seed=817, wavelength=60.0)
        PA.hand_stroke(d, [(1060, 190), (1210, 190), (1180, 400), (1080, 400)],
                       INK, 6, closed=True, seed=818, wavelength=90.0)
        # The acid stream itself lives in g_pour below, so it can move on its
        # own without dragging this full-frame tile across the shot. This
        # element holds the frame, the soldier, the jar, and the label only.
        D.draw_label(tile, 'ACID', center=(1130, 520), color=ACID, size=48)
    els.append(SC.layer(clock, 36, g_acid, j=37, kind='bg', eid='g_acid'))
    # NO motion on the full-frame tile. It used to arrive with enter(dx=+140),
    # which was wrong twice over: a 140px strip down the LEFT exposed the
    # previous beat's crane scene mid-transition, and at arrival the "ACID"
    # label (home ink ends x=1195) ran to 1335, so the first ~0.1s showed a
    # half-word "ACI" hanging at the frame edge. A full-frame replace cannot
    # slide horizontally without exposing what is underneath it.
    els.append(cap(36, 640, 676, size=32, fill=PALE))

    def g_pour(tile, fw, fh):
        # THE POUR, and it is the motion this beat is actually about. The acid
        # is drawn as its own small element rather than riding in on the frame,
        # so it can move without dragging the frame -- and because enter()
        # eases an offset to zero, starting at dx=-90 means the stream begins
        # short, near the jar, and EXTENDS leftward onto the figure. That is
        # "poured acid on figures" happening, not a card sliding across.
        d = ImageDraw.Draw(tile)
        for k, (ax, ay, bx, by, wd) in enumerate((
                (1130, 404, 700, 500, 34), (1120, 410, 520, 560, 20))):
            PA.hand_stroke(d, [(ax, ay), (bx, by)], ACID, wd, closed=False,
                           seed=1855 + k, wavelength=140.0)
        for k in range(6):
            PA.fill_poly(tile, PA.ellipse_pts(500 + k * 150, 520 + k * 34,
                                              17, 12, n=16), ACID,
                         seed=1870 + k, value=0.05)
    els.append(SC.layer(clock, 36, g_pour, j=37, kind='shape', eid='g_pour',
                        motion=SC.enter(clock, 36, dx=-90, dy=0, dur=0.62)))

    def g_gone(tile, fw, fh):
        # Full-frame REPLACE to flat grey. The figure has become the grey it
        # was turned into; the register is the information.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (150, 148, 144), seed=820,
                     value=0.06)
        PA.paper_overlay(tile, seed=821)
        # b37 measured 3.10 and this is the flattest beat left in stage G. The
        # flat grey IS the information -- the figure has been reduced to the
        # colour it was turned into -- so the fix cannot be colour. It is
        # structure at values a few steps off that grey: the etched pit floor,
        # the slabs the acid has dulled, and the rubble it has dulled with
        # them. A grey room with a floor in it still reads as grey.
        _slab_floor(tile, d, 470, H, seed=1824, col=(160, 158, 152), n=12)
        PA.fill_rect(tile, [0, 470, W, 486], (128, 126, 122), seed=1826,
                     value=0.05)
        PA.hand_stroke(d, [(-10, 470), (1290, 470)], INK, 6, closed=False,
                       seed=1827, wavelength=200.0)
        # the back wall: a course grid so the upper two thirds is a surface,
        # not a void, at values only a few apart from the field.
        _panel_grid(tile, d, -20, 86, W + 20, 462, seed=1828, col=(160, 158,
                                                                 152),
                    nx=9, ny=4, w_line=3)
        _rubble(tile, d, (900, 500, 1280, 700), 16, seed=1829,
                col=(142, 140, 136), rmin=10, rmax=28)
        _rubble(tile, d, (760, 560, 980, 700), 8, seed=1830, col=(136, 134,
                                                                 130),
                rmin=9, rmax=22)
        _soldier(d, 700, 820, 640, 846, col=GREY, shade=GREY_D,
                 has_armour=False)
        PA.paper_overlay(tile, 822, bbox=[560, 300, 860, 560])
        SC.fullbody(d, 210, 740, 380, pose='shrug', expression='disgust',
                    seed=823, ink=PALE)
        # Lifted 150 -> 118. At y=150 the label's baseline ran into the top of
        # the greyed soldier's head (head crown at ~y=180), so the word sat on
        # his outline. At 118 it clears the head with the title band above.
        D.draw_label(tile, 'NEVER READABLE AGAIN', center=(760, 118),
                     color=INK, size=36)
    els.append(SC.layer(clock, 37, g_gone, j=38, kind='bg', eid='g_gone'))

    # ===================================================================== #
    # STAGE H  b38-b42  "They took soil samples. Mercury. Enough of it to    #
    #   fill a pool. The old records describe it as a slow poison that never  #
    #   lets go."                                                            #
    # A cold pale lab for b38, then a full-frame dark tunnel REPLACE for the  #
    # pool, then the records and the body are laid back over it. The mercury  #
    # bead gets the stage's motion: it is the smallest subject in the chapter #
    # and the only one where a slow settle reads as an idea rather than a      #
    # transition.                                                            #
    # ===================================================================== #
    def h_lab(tile, fw, fh):
        # b38 measured 2.85 -- the flattest beat in the chapter. v1 drew this as
        # `_interior` (one 208,214,218 rectangle, 10 values from the jar in
        # front of it) so the entire frame was a single smooth pale field with a
        # hollow outline floating in it. The beat is "soil samples gave up
        # mercury", which happens in a lab, and a lab is a BUILT room: tiled
        # wall, a bench with a lip, a shelf of sample jars, a rack of small
        # bottles. All of it in cool greys so the SILVER bead and the MERCURY
        # jar in the next layer still own the frame.
        d = ImageDraw.Draw(tile)
        _interior(tile, 860, (206, 212, 216))
        # --- tiled back wall across the whole upper two thirds. The tile grid
        # is the edge density: ~90 small outlined squares instead of one void.
        for r in range(6):
            ya = 88 + r * 66
            off = (r % 2) * 33
            c = -1
            x = off - 33
            while x < W + 40:
                x0 = x + c * 66
                PA.fill_rect(tile, [x0 + 2, ya + 2, x0 + 64, ya + 64],
                             (198, 205, 209) if (r + c) % 2 else (212, 218,
                             222), seed=861 + r * 11 + c, value=0.05, edge=1.0)
                PA.hand_stroke(d, [(x0 + 2, ya + 2), (x0 + 64, ya + 2),
                                   (x0 + 64, ya + 64), (x0 + 2, ya + 64)],
                               (166, 174, 179), 3, closed=True,
                               seed=871 + r * 7 + c, wavelength=70.0)
                c += 1
                x += 66
        # --- a lab bench across the mid frame, with a lip and slab feet, and
        # the shelf above it carrying small sample bottles.
        _shelf(tile, d, 470, seed=873, col=(150, 158, 164), thick=44)
        # shelf of sample jars along the top, each a small filled bottle
        for k in range(9):
            bx = 70 + k * 138
            bh = 46 + ((k * 29) % 22)
            PA.fill_rect(tile, [bx, 92, bx + 58, 92 + bh], (150, 158, 166),
                         seed=875 + k, value=0.06, edge=1.4)
            PA.hand_stroke(d, [(bx, 92), (bx + 58, 92)], (96, 104, 112), 5,
                           closed=False, seed=880 + k, wavelength=40.0)
            PA.fill_rect(tile, [bx + 12, 92 + bh - 16, bx + 46, 92 + bh - 2],
                         (196, 176, 120) if k % 3 else (170, 158, 140),
                         seed=885 + k, value=0.06, edge=1.0)
    els.append(SC.stage(clock, 38, h_lab, j=43))

    def h_jar(tile, fw, fh):
        # The mercury jar: filled, graduated, standing ON the bench lip. v1 drew
        # a hollow outline ellipse with a brown blob beneath; filling it with a
        # graded column and putting it on the bench is what makes the frame's
        # subject read as a vessel of liquid rather than a drawn circle.
        d = ImageDraw.Draw(tile)
        # bench top surface, cropping the jar's base onto it
        PA.fill_rect(tile, [0, 560, W, 760], (168, 174, 180), seed=870,
                     value=0.05, edge=1.8)
        PA.hand_stroke(d, [(-10, 560), (1290, 560)], INK, 6, closed=False,
                       seed=871, wavelength=180.0)
        for k in range(11):     # bench front edge ribs
            PA.hand_stroke(d, [(k * 118, 560), (k * 118 - 8, 720)], INK, 4,
                           closed=False, seed=873 + k, wavelength=70.0)
        # the jar body, filled with a cool glass tone, and a graduated mercury
        # column inside it (silver band with tick marks), cropped by the bench
        # lip so it sits on the surface.
        PA.fill_poly(tile, PA.ellipse_pts(640, 400, 170, 260, n=48),
                     (196, 206, 212), seed=872, value=0.06, edge=1.8)
        # The mercury itself: a tall, dark silver column filling most of the
        # jar, with a bright meniscus line at its top. At the old pale SILVER
        # against a 206-grey body it was invisible -- the vessel read hollow.
        PA.fill_poly(tile, [(640 - 152, 380), (640 + 152, 380),
                            (640 + 138, 570), (640 - 138, 570)], (118, 126, 134),
                     seed=874, value=0.07, edge=1.6)
        PA.fill_poly(tile, [(640 - 152, 380), (640 + 152, 380),
                            (640 + 148, 400), (640 - 148, 400)], (222, 228, 232),
                     seed=875, value=0.05, edge=1.2)
        for k in range(6):      # graduation ticks down the left of the jar
            gy = 410 + k * 26
            PA.hand_stroke(d, [(492, gy), (492 + 26, gy)], (232, 236, 240), 5,
                           closed=False, seed=876 + k, wavelength=30.0)
        PA.hand_stroke(d, PA.arc_pts(640, 400, 170, 260, 0, 360, n=48),
                       INK, 7, closed=True, seed=873, wavelength=150.0)
        PA.fill_poly(tile, PA.ellipse_pts(640, 128, 104, 36, n=32), INK,
                     seed=878, value=0.0, edge=1.6)   # jar stopper
        D.draw_label(tile, 'MERCURY', center=(640, 246), color=INK, size=52)
    els.append(SC.layer(clock, 38, h_jar, j=39, kind='shape', eid='h_jar'))

    def h_bead(tile, fw, fh):
        # MOVING. A single bead settling onto the soil sample. Moved left onto
        # the sample dish beside the jar: at the old (700,520) it landed on the
        # jar's own mercury column, so the bead and the thing it came from were
        # the same pixels. The dish + its soil mound are drawn first so the bead
        # has a surface to settle onto.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, PA.ellipse_pts(300, 560, 130, 34, n=32),
                     (176, 182, 188), seed=879, value=0.06, edge=1.6)
        PA.hand_stroke(d, PA.arc_pts(300, 560, 130, 34, 0, 360, n=32), INK, 6,
                       closed=True, seed=881, wavelength=70.0)
        PA.fill_poly(tile, PA.ellipse_pts(300, 548, 96, 22, n=28),
                     (138, 110, 78), seed=882, value=0.08, edge=1.4)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(300, 508, 40, 26, n=28),
                     SILVER, seed=880, value=0.05, edge=1.6)
    els.append(SC.layer(clock, 38, h_bead, j=39, kind='shape', eid='h_bead',
                        motion=SC.enter(clock, 38, dx=0, dy=-34,
                                        dur=ARRIVE)))
    els.append(cap(38, 640, 676, size=32))

    def h_pool(tile, fw, fh):
        # Full-frame REPLACE: the tunnel, and a pool of mercury running off the
        # LEFT edge rather than sitting in the middle as a grey lozenge.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (34, 32, 34), seed=890, value=0.08)
        PA.paper_overlay(tile, seed=891)
        PA.fill_poly(tile, [(-40, 130), (520, 300), (520, 720), (-40, 720)],
                     (58, 54, 52), seed=892, value=0.08)
        PA.fill_poly(tile, [(760, 300), (1320, 130), (1320, 720), (760, 720)],
                     (58, 54, 52), seed=893, value=0.08)
        SC.title_backdrop(tile, 1870, col=(118, 92, 70))
        PA.fill_poly(tile, [(-40, 566), (760, 600), (760, 720), (-40, 720)],
                     SILVER, seed=894, value=0.05)
        for k in range(4):
            PA.hand_stroke(d, [(60 + k * 150, 620 + (k % 2) * 26),
                               (240 + k * 150, 616 + (k % 2) * 26)],
                           (238, 244, 248), 8, closed=False, seed=895 + k,
                           wavelength=80.0)
    els.append(SC.layer(clock, 39, h_pool, j=43, kind='bg', eid='h_pool'))

    def h_pool_label(tile, fw, fh):
        # The gold mercury disc and its label belong to b39-b41 ("enough for a
        # pool"), not to b42. They used to live inside h_pool and so survived
        # into the mercury-dome beat, where a stray gold blob floated over the
        # dome and the words 'ENOUGH FOR A POOL' hung at the frame edge beside
        # 'IT DOES NOT LET GO' -- two labels for two different beats in one
        # frame. This layer ends at b42 so the dome beat has a single label.
        d = ImageDraw.Draw(tile)
        # Disc + label moved 900 -> 560. f_droplet's presenter is at cx=940 and
        # his 'armscrossed' pose is the WIDEST in the library after 'recoil' --
        # measured ink bbox at h=400 is x:[cx-157, cx+157], against 'standing'
        # at cx+-107. 'ENOUGH FOR A POOL' at size 34 measures x:[596,925], so
        # clearing it needs cx >= 925+157+30 = 1112, and clearing the RIGHT
        # frame edge needs cx <= 1280-157-30 = 1093. Those two ranges do not
        # overlap: there is no cx that fits this figure beside this label. The
        # label moves instead, into the dark band above the scroll's top edge
        # (y=470), which is the one genuinely empty region left in this beat.
        # Disc and label move together so the disc still hangs over the words.
        PA.fill_poly(tile, PA.ellipse_pts(560, 250, 46, 46, n=24), GOLD,
                     seed=899, value=0.05)
        D.draw_label(tile, 'ENOUGH FOR A POOL', center=(560, 430),
                     color=SILVER, size=34)
    els.append(SC.layer(clock, 39, h_pool_label, j=42, kind='shape',
                         eid='h_pool_label'))

    def h_records(tile, fw, fh):
        # v1 ran this scroll edge to edge over the tunnel, which left b40 a flat
        # cream field with two grey bars and none of the tunnel left to read as
        # a tunnel. Narrowed to a document lying IN the tunnel, cropped by the
        # bottom edge, so the converging walls and the pool survive around it.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(330, 470), (960, 470), (1040, 760), (250, 760)],
                     (246, 240, 224), seed=910, value=0.05)
        PA.hand_stroke(d, [(330, 470), (960, 470)], INK, 7, closed=False,
                       seed=911, wavelength=180.0)
        PA.hand_stroke(d, [(330, 470), (250, 760)], INK, 5, closed=False,
                       seed=912, wavelength=140.0)
        PA.hand_stroke(d, [(960, 470), (1040, 760)], INK, 5, closed=False,
                       seed=913, wavelength=140.0)
        for k, yy in enumerate((560, 646)):
            PA.fill_poly(tile, [(400, yy), (900, yy + 14), (900, yy + 34),
                                (400, yy + 20)], SILVER, seed=914 + k,
                         value=0.05)
    els.append(SC.accrue(clock, 40, 42, h_records, kind='shape',
                         eid='h_records'))
    # Ends at b42 now, not b43. It used to survive into b42, where the pale
    # h_body mass (208,200,186) landed on top of the pale scroll (246,240,224)
    # -- two pale wedges a few values apart merging into one shape, plus the
    # stray gold disc from the tunnel backdrop. The scroll is the b40-b41
    # subject; at b42 the body is.

    def h_records_name(tile, fw, fh):
        # The scroll persists to the end of the stage; its title does not. At
        # b42 IT DOES NOT LET GO arrives at almost the same spot.
        # SILVER, not INK: this lands on the dark tunnel ceiling, measured at
        # bg luminance 32.1. INK fill (24,24,28) + the standard black keyline +
        # a 32.1 ceiling put all three within a few values of each other, so the
        # stage title read as a black embossed ghost rather than solid text.
        # SILVER is the sibling label on this exact backdrop -- ENOUGH FOR A
        # POOL below, same tunnel, and it reads cleanly.
        D.draw_label(tile, 'THE OLD RECORDS', center=(640, 140), color=SILVER,
                     size=38)
    els.append(SC.layer(clock, 40, h_records_name, j=42, kind='shape',
                        eid='h_records_name'))

    def f_droplet(tile, fw, fh):
        # The fingertip stays cropped by the LEFT edge and the presenter stays
        # right; the scroll between them is what he is looking at.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, PA.ellipse_pts(-20, 520, 190, 250, n=44),
                     (238, 226, 206), seed=920, value=0.06)
        # Droplet and its POISON tag moved to 990 and up to 285/200. The presenter is
        # at cx=1120 and his head tops out near y=312 at h=360, so a droplet at
        # the old (1090, 420) sat on his shoulder and (1090, 250) sat on his
        # head. 990 puts the pair up and to his left, clear of the skull and of
        # both hands, in the same dark ceiling band as 'THE OLD RECORDS'.
        PA.fill_poly(tile, PA.ellipse_pts(990, 285, 34, 34, n=28), SILVER,
                     seed=921, value=0.05)
        # cx 1120 and h 360, not cx 940 / h 400. Two competing defects, and 940/400
        # loses to both of them:
        #   (a) At cx=1120 h=400 the 'armscrossed' reach (+-157 at h=400) put
        #       his right hand at x=1277 on a 1280-wide frame -- 3px off the
        #       edge, on a figure too small for that crop to read as intent.
        #   (b) Moving in to cx=940 to solve (a) put his feet on the scroll,
        #       whose trapezoid spans x 308-1012 along the y=700 floor line.
        #       Scroll is (246,240,224) and PALE is (238,226,206) -- eleven
        #       apart on blue, i.e. nothing at 720p -- so his legs dissolved
        #       into the document below the waist. A contact shadow at the feet
        #       restored the ground line but the ellipse clipped the bottom edge
        #       and read as a smudge, because feet at y=700 leave 13px of frame
        #       and the foot blobs overshoot to 707.
        # h=360 scales the reach to +-141, so 1120+141 = 1261: 19px clear of
        # the edge, and 1120-141 = 979 sits just inside the scroll's right edge
        # at 1012 without his legs going under it. Standing clear of the
        # document is worth more than 19px of hand margin.
        SC.fullbody(d, 1120, 700, 360, pose='armscrossed',
                    expression='worried', seed=922, ink=PALE)
        # PALE, not INK: this lands on the dark tunnel, where v1's INK word
        # would have been invisible.
        D.draw_label(tile, 'POISON', center=(990, 200), color=PALE, size=48)
    els.append(SC.layer(clock, 41, f_droplet, j=42, kind='character',
                        eid='f_droplet'))
    els.append(cap(41, 300, 664, size=32))

    def h_body(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "It does not let go." The mercury standing over the body as a
        # domed metal sheet, filling the frame rather than sitting in it. The
        # old shape was a flat pale trapezoid occupying y 386-660 with dark
        # tunnel above and below -- on its own it read as a wedge of light,
        # not a body under metal. Now the sheet is wider, higher and domed,
        # with a bright meniscus along its crest so the mercury reads as a
        # liquid skin, and the dark coffin seam shows through it.
        dome = PA.ellipse_pts(640, 620, 620, 210, n=64)
        PA.fill_poly(tile, dome, (176, 178, 184), seed=930, value=0.08)
        PA.hand_stroke(d, dome, (236, 240, 246), 6, closed=True, seed=931,
                       wavelength=180.0)
        # the body beneath, a dark seam, and mercury beads
        PA.fill_poly(tile, [(430, 560), (850, 560), (880, 700), (400, 700)],
                     (86, 84, 88), seed=934, value=0.06)
        for k in range(6):
            PA.fill_poly(tile, PA.ellipse_pts(340 + k * 140, 600, 16, 11,
                                              n=14), SILVER,
                         seed=932 + k, value=0.05)
        D.draw_label(tile, 'IT DOES NOT LET GO', center=(640, 150),
                     color=PALE, size=40)
    els.append(SC.accrue(clock, 42, 43, h_body, kind='shape',
                         eid='h_body'))

    # ===================================================================== #
    # STAGE I  b43-b45  "The main chamber has never been opened. It is still  #
    #   sealed. And the door stays shut."                                     #
    # The finale is the one place where a DRAWING beats a photograph, so the  #
    # backdrop is a CROSS-SECTION: the mound, the earth, the outer pit where   #
    # the farmers found the shoulder, and the sealed void under all of it.    #
    # The presenter arrives awed in the last beat, cropped by the bottom,     #
    # looking at a door we never see open.                                    #
    # ===================================================================== #
    def i_section(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, 150], (176, 186, 196), seed=990,
                     value=0.07)
        PA.paper_overlay(tile, seed=991)
        PA.fill_rect(tile, [0, 146, W, 320], EARTH, seed=992, value=0.09)
        PA.fill_rect(tile, [0, 316, W, 556], EARTH_D, seed=993, value=0.09)
        PA.fill_rect(tile, [0, 552, W, H], (18, 16, 18), seed=994, value=0.06)
        for yy in (148, 318, 554):
            PA.hand_stroke(d, [(-10, yy), (1290, yy)], INK, 6, closed=False,
                           seed=995 + yy, wavelength=200.0)
        # the outer pit, and the figures in it -- drawn rect FIRST, figures
        # after, so the figures are not painted over by their own pit. The pit
        # is widened and deepened (it used to be a small dark rectangle in a
        # vast flat field) and the mound that encloses the whole section is
        # outlined above ground so the frame reads as a cutaway of a mound
        # rather than three horizontal colour bands.
        PA.fill_poly(tile, [(-40, 150), (250, 96), (640, 60), (1030, 96),
                            (1320, 150), (1320, 40), (-40, 40)],
                     (150, 162, 172), seed=996, value=0.07)
        PA.hand_stroke(d, [(-40, 150), (250, 96), (640, 60), (1030, 96),
                           (1320, 150)], INK, 6, closed=False, seed=997,
                       wavelength=190.0)
        PA.fill_rect(tile, [30, 372, 830, 552], (58, 48, 40), seed=998,
                     value=0.08)
        PA.hand_stroke(d, [(30, 372), (830, 372), (830, 552), (30, 552)], INK,
                       6, closed=True, seed=999, wavelength=170.0)
        for k in range(5):
            _soldier(d, 130 + k * 165, 548, 150, 1000 + k,
                     col=(150, 104, 64), shade=(112, 76, 46), has_armour=False)
        # the sealed void, at the right, running off the bottom edge, with a
        # heavy door slab and its never-crossed threshold
        PA.fill_rect(tile, [880, 470, 1340, 760], (44, 38, 36), seed=1001,
                     value=0.06)
        PA.hand_stroke(d, [(880, 470), (880, 760)], INK, 8, closed=False,
                       seed=1002, wavelength=150.0)
        PA.hand_stroke(d, [(880, 470), (1340, 470)], INK, 8, closed=False,
                       seed=1003, wavelength=150.0)
        PA.fill_rect(tile, [950, 500, 1300, 720], (72, 64, 60), seed=1004,
                     value=0.07)
        PA.hand_stroke(d, [(1120, 500), (1120, 720)], (30, 26, 24), 10,
                       closed=False, seed=1005, wavelength=90.0)
        d.ellipse([1100, 590, 1140, 630], fill=(180, 172, 160))
    els.append(SC.stage(clock, 43, i_section, j=46))

    def i_never(tile, fw, fh):
        D.draw_label(tile, 'NEVER OPENED', center=(1050, 112), color=INK,
                     size=40)
    els.append(SC.layer(clock, 44, i_never, j=45, kind='shape',
                        eid='i_never'))

    def i_shut(tile, fw, fh):
        # MOVING. The presenter, awed, arriving at the last thing in the
        # chapter. One entrance, one expression, no swap: the awe is the
        # arrival.
        # y_feet 610, not 830: at 830 his shins ran 110px off the bottom edge of
        # a 720 frame with no ground contact. The binding constraint now is the
        # bottom caption (b43 and b45 both print at cy=676, spanning ~657-695):
        # his feet must clear 657 even at the LOWEST point of the enter() dip.
        # With dy=20 that floor is 610+20=630, 27px clear. His head (top ~y=210
        # at h=400) stays well below the THE DOOR STAYS SHUT label at cy=112.
        SC.fullbody(ImageDraw.Draw(tile), 700, 610, 400, pose='peeking',
                    expression='awed', seed=1010, ink=PALE)
        D.draw_label(tile, 'THE DOOR STAYS SHUT', center=(400, 112),
                     color=INK, size=44)
    els.append(SC.accrue(clock, 45, 46, i_shut, kind='character',
                         eid='i_shut',
                         motion=SC.enter(clock, 45, dx=0, dy=20,
                                         dur=ARRIVE)))
    els.append(cap(43, 640, 676, size=32, fill=PALE))
    els.append(cap(45, 640, 676, size=32, fill=PALE))

    return SC.finish(els, TITLE, clock, title_seed=53)
