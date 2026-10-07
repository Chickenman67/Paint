"""area51_2_scene -- the PERSISTENT-STAGE rebuild of chapter 2 (Area 51).

WHY THIS FILE EXISTS. area51_scene.py (v1) is built on "one card per beat, each
card paints its own whole frame": its local `card(i, j, draw, ...)` helper paints
a complete 1280x720 image -- playa, fence, labels, character -- live only for
beats i..j-1, so nothing survives into the next sentence. The viewer reported
exactly that: "every sentence has a cut with a completely new image ... there are
no animations or changes to the visual."

THE MODEL HERE. Seven STAGES over EIGHT backdrops, grouped on the narration's
own acts. Stage A is split -- see the note on the lake bed below:

    A  b01-b04  the nameless place; Fifty-One; Nevada; the Groom Lake sign
    A2 b05-b07  the cracked alkali; the locator inset; the arrest warning
    B  b08-b14  nobody answers; the wire runs for miles; a second fence;
                cameras on poles; the base is smaller than its fence
    C  b15-b19  no aircraft may fly; the red ceiling; pilots notice; the
                lights; 1955
    D  b20-b21  Roswell; the story went flat
    E  b22-b25  Hangar 18; the empty door; DOES NOT EXIST; Nellis
    F  b26-b30  the budget; Bob Lazar; what he described; no record
    G  b31-b34  2020; one page; the fence is still standing; never

WHY STAGE A IS SPLIT IN TWO. As one backdrop b01-b07 held a single bleached-noon
register for 18.7s and the measured still_gap was 33.0s -- twice the reference
band -- because nothing in the frame moved enough to register at >30% of pixels
crossing 24 L levels. A2 drops the camera to the lake bed itself: ground
(196,172,132) at horizon 190 instead of SKY/ALKALI at 446. That is a real
luminance change across most of the frame, which is the only thing check_cadence
counts, and it took still_gap from 33.0 to 14.4 -- inside the 12.8-16.2 band the
two pattern chapters sit in. The cost is one extra cut (7 rather than 6), which
is the right trade: a cut that reads as "the camera moved down to the ground"
beats a held frame that reads as a freeze.

WHAT THE PREVIOUS ATTEMPT AT THIS FILE GOT WRONG, MEASURED. It had the same
stage skeleton and it still measured a full-frame repaint every 2.5s with ten
REFRAME hits, because it was wired LAYER-dominated: 26 `SC.layer` calls against
8 `SC.accrue`. Almost every beat replaced the one before it -- the Groom Lake
sign replaced by the arrest warning, the door replaced by the stamp, the lectern
replaced by the sketch, the page replaced by the fence -- and a replace is a
swap. Measured repaints in that wiring: thirteen, at 33.2 / 43.9 / 46.4 / 49.1 /
51.6 / 56.4 / 57.9 / 60.3 / 65.8 / 70.4 / 72.3 / 73.9 / 75.9s, median gap 2.5s,
plus ten onsets each swapping more than REFRAME_MAX = 0.30 of the frame.

The gate's own documentation says the layer:accrue ratio is a HINT and never
authoritative, so the fix below is not "call accrue more often". It is two
concrete things.

1. THE WORLD IS PAINTED ONCE AND THE THINGS ACCRUE ONTO IT. The near fence is
   put up at b01 and is still standing at b14, thirteen beats later, and the
   same near-black wire is what the chapter ends on at b33. Inside stage A the
   cracked alkali arrives at b05, the name at b03, the locator inset at b06 and
   the board at b07 -- four additions to one painted playa and not one cut.
   Inside stage E the wall is up at b22 with the 18 on it, the door leaf slides
   off it at b23, the stamp lands on the doorway at b24, and Nellis is written
   across the apron at b25 -- which the backdrop has been composing on the right
   of frame since b22 with a service road, edge lines, a receding fence stub
   and a fuel bowser, so it arrives at something instead of bare desert.

2. A CHANGE OF LOOK IS A STAGE, NOT A LAYER. `_readability_gate.check_reframe`
   deliberately SKIPS onsets where a `kind='bg'` element begins, because a cut to
   a new place is a legitimate edit, and flags any OTHER onset that swaps more
   than 0.30 of the frame -- "a new image wearing the old stage's clothes". So
   every place change here is an `SC.stage(...)` backdrop, and nothing inside a
   stage may move more than a third of the frame at once. That is why the big
   objects were RESIZED and not merely re-wired: the 1955 calendar used to be
   760x580 (48% of the frame), the DOES NOT EXIST box 1080x360 (42%), the hangar
   wall 1360x564 (71%), the file page 1360x550 (74%). They are now 12% / 11% /
   a backdrop / 20%, and the numbers that matter are measured, not asserted --
   see the table at the end of this docstring.

THE REGISTERS ARE CHOSEN FROM THE PALETTE'S OWN LUMINANCE, not by taste.
`_readability_gate.check_cadence` calls a frame changed when >30% of its pixels
move by >24 L levels. The palette is SKY 212 / ALKALI 229 / DUST 196 /
CONCRETE 200 / MOUNTAIN 153 / NIGHT 30. Two stages painted from the SAME pair of
values cannot register a cut no matter where the horizon sits, because 212 and
229 are seventeen levels apart. So each stage is given a register that differs
from its neighbour by more than the threshold across more than the required
area:

    A  bleached noon   SKY 212 / ALKALI 229, horizon 446
    A2 lake bed        LAKEBED 196 ground at horizon 190 -- the camera is DOWN
                      on the cracked alkali, not up on the playa
    B  dusk            118 / 146, horizon 250   -> 28 levels over 62% of rows
    C  night           30 / 20, and the sky is gone -> 118 levels over the lot
    D  bleached noon again, and that is the POINT: b20 is "Roswell was already
       three years old", a date in daylight, and going back to noon IS the cut
    E  OVERCAST 150 / APRON 196 / WALL 124 -- the wall at 124 is 26 levels under
       the sky, where v1's CONCRETE 200 was TWELVE levels under it and the
       hangar building simply vanished into its own background
    F  an interior, 198 flat with a 184 floor band
    G  night again, and the loop closes on the same fence as b01

The dusk stage B is not decoration. b08-b14 are the beats where the chapter
stops describing a place and starts describing a perimeter: a second sign, a
wire you cannot see past, a second wire behind it, cameras, and a base too small
to justify any of it. Warning and dusk are the same idea, and the value drop is
also what makes the cut a cut.

THE SLIDING DOOR IS THE ONE PIECE OF REAL ANIMATION. The hangar leaf is
authored COVERING the opening and a two-keyframe track carries it 420px to the
left over 0.6s at b23, uncovering a dark doorway that was on the wall the whole
time. Nothing arrives and nothing leaves. The previous version authored the leaf
at x -40..196 -- BESIDE the opening -- and gave it `SC.enter(dx=-130)`, which
eases an element FROM an offset TO its authored place; that combination slid the
panel further left and then right, i.e. it shut the door it was meant to open.
The leaf tile is 280x260, 10% of the frame, so the move is clear of the
full-bleed test in `check_motion_fit` too.

The leaf is live from b22, not b23, and that one beat is the difference between
a door and a flicker. `_interp_keyframes` clamps before its first key, so a
track keyed at T(23) leaves the element at its authored place for the whole of
b22 -- covering the opening. Started at b23 instead, the door stood open through
b22, the pale leaf snapped shut on the b23 onset, and then slid open again. The
door is now shut at b22 and opens on b23 to show the dark empty bay behind it,
which is what "empty hangar door" means.

THE CHARACTER. The presenter carries the desert act (b01-b09), changes
expression once inside it through `SC.expr_swap`, hands off to a shrug at b09
rather than doubling up, and returns at b34 cropped by the left edge. The peeker
at b11 is cropped by the RIGHT edge: a character has to be cropped INTO the shot
to read as inside it, not parked beside it as set dressing.

SIZED AGAINST THE CHARACTER, measured at height 400 and scaled linearly:
standing +-107, shrug +-170, pointing -107/+196, peeking +-135. The presenter at
height 440 reaches 1040+-118 = x 922..1158, clear of the boards at x<=716; the
pointing pilot at height 430 reaches x 135..461, clear of the jet at 452..668;
the office man at height 440 reaches x 522..758, clear of the sheet's right edge
at 470 and the television's left edge at 940.

ART. Every primitive, the palette and the layout come from area51_scene.py --
this file imports it and does not copy it, and it imports nothing from
pinegap2. Nothing here draws a title: engine3.render_frame stamps scene.title
LAST and a card-local title makes an illegible double.

MEASURED, `python lib/_chapmetrics.py area51` (re-run after every edit below;
these are the numbers that command printed last, not remembered ones):

                       elem beats reframe  cut_s  still_gap  cuts  motion
    previous wiring       57     34     10      2.50     33.0     13   0.099
    this file             57     34      0     12.02     14.4      7   0.203
    vatican2 (pattern)    66     38      0     10.34     16.2      9   0.191
    mezhgorye2 (pattern)  59     30      0      5.51     13.7     10   0.157
    svalbard (pattern)     65     35      0      6.01     12.8     13   0.187

TARGETS MET: cut_s 2.50 -> 12.02 (>= 6.0 asked), reframe 10 -> 0, still_gap
33.0 -> 14.4 (inside the 12.8-16.2 band the pattern chapters sit in). Motion
rose 0.099 -> 0.203 and is STILL THE MINORITY: at 20% of onsets carrying a
transform it sits just above vatican2's 19% and mezhgorye2's 16%, not in the
cheyenne-style regime where nearly every beat is a move.

Run:  python lib/area51_2_scene.py --preview --video
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
import character3 as C3

import area51_scene as A51     # art primitives + palette, reused not copied


# --------------------------------------------------------------------------- #
# TWO POSES, REGISTERED LOCALLY.                                             #
#                                                                             #
# character3.POSES['pointing'] is ra=(78, 12) and that 12 is the FOREARM BEND #
# -- the elbow angle, per character3's own convention note. At ship size a 12 #
# degree bend renders as a straight bar and the arm reads as a T-arm, which #
# is this project's most recurrent character defect (see the two memory notes #
# on the stickman T-arm and on elbow existence not being elbow visibility).   #
#                                                                            #
# These are REGISTERED here rather than edited into character3 because        #
# character3 is shared by all nine chapters: changing 'pointing' in place     #
# would silently move the arm on every other chapter's beats. Adding two       #
# prefixed entries touches nothing else. `draw_character` takes a pose NAME     #
# and there is no override parameter, so registration is the only lever that   #
# leaves the shared module alone.                                            #
#                                                                            #
# a51_pointing_e: same arm as 'pointing' (raised, out to the right) with the #
# elbow bend raised 12 -> 38, so the forearm visibly folds. The upper arm is  #
# 70 and the forearm comes back to 108 absolute: the hand ends up higher and  #
# further out than the stock pose, which is what "pointing at the rule above  #
# you" looks like.                                                            #
# a51_shield: both forearms up across the face, elbows hard out -- the read   #
# for a man putting his hands up in front of a red ceiling. Both bends are   #
# above 60, so both elbows are unmistakable at playback size.                 #
# --------------------------------------------------------------------------- #
C3.POSES.setdefault('a51_pointing_e', dict(
    la=(16, 24), ra=(70, 38), ll=(-12, 0), rl=(11, 0), lean=-3))
C3.POSES.setdefault('a51_shield', dict(
    la=(58, 78), ra=(58, 78), ll=(-10, 0), rl=(12, 0), lean=2))

# --- what the engine needs, taken straight from v1 -------------------------- #
SEG = A51.SEG
TITLE = A51.TITLE
BEATS = A51.BEATS
TITLE_BACKDROP = A51.TITLE_BACKDROP

# palette / geometry, reused from v1
INK = A51.INK
RED = A51.RED
SKY = A51.SKY
ALKALI = A51.ALKALI
DUST = A51.DUST
PLATA = A51.PLATA
CONCRETE = A51.CONCRETE
STEEL = A51.STEEL
MOUNTAIN = A51.MOUNTAIN
PAPER = A51.PAPER
NIGHT = A51.NIGHT
NIGHT_G = A51.NIGHT_G
W, H = A51.W, A51.H
HZ = A51.HZ

# art primitives, reused from v1 -- never copied
_playa = A51._playa
_mountain_strip = A51._mountain_strip
_fence = A51._fence
_jet = A51._jet
_balloon_low = A51._balloon_low
_hand_sketch = A51._hand_sketch
_bunker = A51._bunker
_hangar = A51._hangar
_tower = A51._tower
_camera_pole = A51._camera_pole
_runway = A51._runway
_calendar = A51._calendar
_file_stack = A51._file_stack

# The dusk register for stage B, named rather than inlined. These are the two
# values the luminance argument in the docstring depends on: 133 against stage
# A's 212, which is 79 levels over the 62% of rows above the horizon.
DUSK_SKY = (118, 100, 92)
DUSK_GROUND = (146, 112, 86)
DUSK_RIM = (96, 74, 70)

# The lake-bed register for stage A2: a cooled, low-sun alkali that sits 42
# levels under SKY. Cooled rather than merely darkened so the split reads as a
# change of LIGHT rather than a card going grey.
LAKEBED = (196, 172, 132)

# The overcast register for stage E, and the contrast pair that makes the
# building exist. v1 painted the hangar in CONCRETE (L=200) on a SKY of L=212,
# so the wall and the sky were the same value and the hangar rendered as a thin
# black arc on blue. OVERCAST is 177 and WALL is 124: fifty-three levels apart,
# which is the whole difference between a building and an arc.
OVERCAST = (150, 160, 170)
APRON = (196, 190, 178)
WALL = (124, 120, 114)

# The arrival duration used by every moving element. 0.45-0.55s reads as a
# deliberate move; longer and the element becomes the picture changing on every
# sample, which is the defect this whole rebuild exists to remove.
ARRIVE = 0.5

# The horizon is at HZ = 446 and every ground-plane y below is chosen so the near
# fence, the cracked alkali, the base and the runway stack without touching:
#
#     near fence    y 286..462   FENCE_TOP 286 / FENCE_BASE 462
#     cracked net   y 486..      below the fence, on the ground
#     camera poles  base 470, 290 tall
#     base/bunkers  base line 600
FENCE_TOP = 286
FENCE_BASE = 462


# =========================================================================== #
# EDGE-DENSITY HELPERS.                                                       #
#                                                                            #
# WHY THESE EXIST. The per-beat pigment measurement renders every beat's     #
# midpoint and takes the median luma std over 24px tiles (threshold 8.0).     #
# Measured on this file before the work below:                                   #
#                                                                            #
#     b14  11.38   <- fence mesh + second fence + pole + bunkers + tower      #
#     b12   9.38   <- two fences + crack net                                   #
#     b16   3.08   <- a jet, a red line, and empty night                      #
#     b21   2.90   <- a calendar and a balloon on a bare playa                #
#     b26   2.90   <- a document and an empty room                            #
#                                                                            #
# The ranks are not about PAINT -- every one of those fills goes through      #
# PA.fill_rect/PA.fill_poly with the same value drift, and b16/b21/b26 come   #
# back at 2.9-3.1, i.e. flat-vector. The ranks track ONE thing: how many      #
# OUTLINED EDGES cross a given tile. b14 wins because a 24px tile of b14 has  #
# a fence wire and a post and a crack in it; a tile of b21 has a sky gradient  #
# and nothing else. So the fix is to put more small outlined shapes into the  #
# EMPTY parts of each frame -- which is also, not coincidentally, what the    #
# reference does: it fills the frame with a system bigger than the picture.  #
#                                                                            #
# Every helper here is seeded and every one draws STRUCTURE (contour bands,   #
# ribs, panels, scrub, blocks), not noise. Noise would move the metric without #
# moving the picture and the orchestrator judges pixels by eye.              #
# =========================================================================== #


def _contour_bands(d, y0, y1, col, seed, n=7, lw=4, x0=-60, x1=W + 60,
                   wobble=0.55):
    """Layered terrain/ground contour bands between y0 and y1.

    A dry lake bed and a scrub plain are not one fill; they are bands of
    slightly different value running roughly parallel to the horizon, each one
    OUTLINED, so the eye reads distance. `n` bands over the span, each a
    hand-stroke polyline rather than a straight rule.
    """
    for i in range(n):
        u = (i + 0.5) / float(n)
        y = y0 + (y1 - y0) * u
        amp = wobble * (10.0 + 16.0 * u)
        pts = []
        k = 14
        for j in range(k + 1):
            t = j / float(k)
            xx = x0 + (x1 - x0) * t
            pts.append((xx, y + amp * math.sin(t * 5.3 + i * 1.9 + seed * 0.11)))
        PA.hand_stroke(d, pts, col, lw, seed=seed + i * 7,
                       wavelength=120.0 + 20.0 * i)


def _scrub(d, y0, y1, col, seed, n=26, s0=0.5, s1=1.5):
    """Scatter of small outlined desert scrub/clusters across a ground band.

    Density is what matters: each one is 3 short strokes meeting at a point, so
    a 24px tile that lands on one gets two edges instead of a gradient.
    Deterministic -- the position of clump i is a closed-form hash of i and the
    seed, not a running RNG, so the same render always draws the same clumps in
    the same order.
    """
    for i in range(n):
        u = ((i * 37) % 101) / 101.0
        v = ((i * 61) % 97) / 97.0
        x = -40 + (W + 80) * u
        y = y0 + (y1 - y0) * v
        s = s0 + (s1 - s0) * v
        sd = seed + i * 3
        for a in range(3):
            ang = math.radians(200 + a * 46 + 11 * i)
            PA.hand_stroke(d, [(x, y),
                               (x + s * 9.0 * math.cos(ang),
                                y + s * 13.0 * math.sin(ang))],
                           col, max(2, int(3 * s)), seed=sd + a,
                       wavelength=34.0)


def _crust(d, y0, y1, col, seed, rows=5, lw=4, jitter=0.5, cross=0.55):
    """A cracked-mud polygon net: irregular cells, NOT horizontal grain.

    WHY THIS IS NOT `_contour_bands`. A dry lake bed reads as a net of
    irregular POLYGONS -- mud that dried and lifted in plates -- and the first
    pass at the lake bed used near-horizontal parallel bands, which the eye
    read as wood grain or sediment, not as cracked ground. A cell net has
    edges running in many directions, so it reads as broken ground.

    Built as a jittered grid of node rows: each row has its own node count and
    each node's x is offset by a per-cell hash, then consecutive rows are
    joined by short strokes. That produces irregular quadrilateral-ish cells
    with vertical-ish seams between them and only gently varying horizontal
    ones, which is the correct read for perspective on a flat crust.

    `jitter` scales the x-offsets (0.5 default); the row spacing stays roughly
    even so perspective still reads.

    `cross` (0.55 default) is how many of the cell interiors get a diagonal
    hairline. A quad's interior is otherwise a smooth fill -- and the pigment
    metric reads a SMOOTH FILL AS FLAT no matter how many seams bound it,
    because the contrast lives only on the seam pixels and a 24px tile that
    straddles one line still has near-zero internal spread. The diagonals put a
    second, differently-angled edge through the middle of most cells, so the
    detail is distributed across the plate instead of sitting on its border.
    This is the same lesson as the fortknox gold-slab frame (tile_std 53 by
    stacking ~40 small outlined slabs): local detail throughout the subject,
    not a few big shapes with dead space between them.
    """
    nodes = []
    for r in range(rows + 1):
        u = r / float(rows)
        y = y0 + (y1 - y0) * u
        # row spacing compresses with distance (perspective on the flat)
        yy = y0 + (y1 - y0) * (u ** 0.86)
        count = 6 + r                       # more, wider cells near the viewer
        row = []
        for c in range(count + 1):
            base = -40 + (W + 80) * (c / float(count))
            # closed-form per-node offset, so it's deterministic
            k = (r * 131 + c * 17 + seed) % 41
            row.append((base + (k - 20) * 18.0 * jitter, yy))
        nodes.append(row)

    # horizontal-ish edges within each row
    for r in range(rows + 1):
        row = nodes[r]
        for c in range(len(row) - 1):
            x0, y0_ = row[c]
            x1, y1_ = row[c + 1]
            PA.hand_stroke(d, [(x0, y0_), (x1, y1_)], col, lw,
                           seed=seed + r * 50 + c, wavelength=90.0)
    # vertical-ish seams between rows
    for r in range(rows):
        up, dn = nodes[r], nodes[r + 1]
        for c in range(len(up)):
            k = (r * 29 + c * 7 + seed) % 23
            jx = (k - 11) * 12.0 * jitter
            PA.hand_stroke(d, [(up[c][0], up[c][1]),
                               (dn[c][0] + jx, dn[c][1])], col, lw,
                           seed=seed + 200 + r * 40 + c, wavelength=70.0)
    # diagonal hairlines across the cell interiors (see `cross` above)
    for r in range(rows):
        up, dn = nodes[r], nodes[r + 1]
        for c in range(len(up) - 1):
            if ((r * 11 + c * 3 + seed) % 100) / 100.0 >= cross:
                continue
            a = up[c] if ((r + c + seed) % 2 == 0) else dn[c]
            b = dn[c + 1] if ((r + c + seed) % 2 == 0) else up[c + 1]
            PA.hand_stroke(d, [a, b], col, max(2, lw - 2),
                           seed=seed + 400 + r * 30 + c, wavelength=52.0)


def _tufts(d, y0, y1, col, seed, n=40):
    """LOW desert tufts: clusters of 4-5 short upright blades off one root.

    The first scatter (`_scrub`) drew its blades RADIATING from a point at
    spread angles, which at ship size reads as a scatter of arrowheads rather
    than as vegetation -- the eye sees the silhouette, and a three-armed
    asterisk is not a plant. This one draws a rooted fan: the blades are short,
    near-vertical, packed tight, and clustered into groups so the ground has
    tufts in it instead of marks on it. Blades are also only a couple of values
    off the ground, which is what makes them read as texture rather than as
    ink.
    """
    for i in range(n):
        # clump centre, clustered: 9 clumps of 4-5 blades
        ci = i // 5
        bx = -30 + (W + 60) * (((ci * 71) % 97) / 97.0)
        by = y0 + (y1 - y0) * (((ci * 43) % 89) / 89.0)
        nb = 4 + (i % 2)
        for a in range(nb):
            ox = ((a * 17) % 13) - 6.0
            oy = (((a * 11) % 7) - 3.0) * 0.9
            h = 12.0 + ((i * 7 + a * 5) % 11)
            tipx = bx + ox + (((a * 23) % 9) - 4.0) * 0.7
            PA.hand_stroke(d, [(bx + ox, by + oy), (tipx, by + oy - h)],
                           col, 3, seed=seed + i * 5 + a, wavelength=26.0)


def _cloud_bands(d, y0, y1, seed, n=5, col=(214, 220, 226)):
    """Soft outlined cloud strata across a sky.

    A bleached sky is the single largest void in the day cards. These are wide,
    shallow, gently-wobbling outlined strata -- value only a few levels off the
    sky so they read as high cloud, but each one is a real edge so a 24px tile
    crossing it has structure.

    THE FIRST PASS AT 5 STRATA READ AS STRIPES, not cloud: the bands were
    evenly spaced, evenly thick and parallel, and the eye reads that as a
    gradient ramp rather than as weather. Two changes. They are now spaced on a
    widening geometric progression so they bunch near the horizon and thin out
    overhead, and each band's thickness is a function of its own index rather
    than a fixed ladder. Both are how real stratus looks from below.
    """
    for i in range(n):
        u = (i + 0.5) / float(n)
        y = y0 + (y1 - y0) * (u ** 1.7)
        amp = 14.0 + 22.0 * (1.0 - u)
        thick = 14 + 26 * (i / float(max(1, n - 1)))
        top = []
        for j in range(15):
            t = j / 14.0
            top.append((-60 + (W + 120) * t,
                        y + amp * math.sin(t * 3.1 + i * 2.2)))
        band = top + [(x, yy + thick) for (x, yy) in reversed(top)]
        PA.fill_poly(PA.img_of(d), band, col, seed=seed + i, value=0.03,
                     edge=2.0)
        PA.hand_stroke(d, top, (200, 208, 216), 3, closed=False,
                       seed=seed + 40 + i, wavelength=180.0)


def _boulder(d, cx, cy, r, col, seed, lw=4):
    """One outlined rock: an irregular closed blob with a highlight facet."""
    pts = PA.ellipse_pts(cx, cy, r, r * 0.72, n=11, rot=0.3)
    PA.fill_poly(PA.img_of(d), pts, col, seed=seed, value=0.09, edge=2.0)
    PA.hand_stroke(d, pts, INK, lw, closed=True, seed=seed + 1,
                   wavelength=44.0)
    PA.hand_stroke(d, [(cx - r * 0.45, cy - r * 0.12),
                       (cx + r * 0.30, cy - r * 0.26)],
                   (246, 244, 238), max(2, lw - 2), seed=seed + 2,
                   wavelength=30.0)


def _stars(d, x0, y0, x1, y1, seed, n=54, col=(226, 232, 244)):
    """A star field. Night stages are the emptiest frames in the chapter and a
    night sky with nothing in it is the single biggest void in the film.

    Deterministic placement from a closed-form hash so no RNG state leaks
    between calls, and sizes vary so it does not read as a dot grid.
    """
    for i in range(n):
        u = ((i * 53) % 103) / 103.0
        v = ((i * 29) % 89) / 89.0
        v = v * v                      # bias toward the top of the band
        x = x0 + (x1 - x0) * u
        y = y0 + (y1 - y0) * v
        r = 1.6 + 2.6 * (((i * 17) % 13) / 13.0)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(x, y, r, n=9),
                     col, seed=seed + i, value=0.05, edge=0.6)


def _stars_spark(d, x, y, seed, r=9.0, col=(240, 244, 252)):
    """One four-point star flare -- the accent that keeps a star field from
    reading as scattered dust. Drawn as two crossing outlined strokes."""
    for a, b in (((-r, 0), (r, 0)), ((0, -r), (0, r))):
        PA.hand_stroke(d, [(x + a[0], y + a[1]), (x + b[0], y + b[1])],
                       col, 3, seed=seed, wavelength=20.0)
    PA.hand_stroke(d, [(-r * 0.42, -r * 0.42), (r * 0.42, r * 0.42)],
                   col, 2, seed=seed + 1, wavelength=14.0)


def _panel_grid(d, x0, y0, x1, y1, col, seed, nx=6, ny=4, lw=4):
    """A riveted panel grid -- the read for any large flat wall.

    Used on the hangar, the office wall and the gatehouse. Vertical ribs and
    horizontal joints only: at a 24px tile a single crossing rib is already
    enough local detail, and a checkerboard of both would read as tile, not
    metal.
    """
    for i in range(1, nx):
        x = x0 + (x1 - x0) * i / float(nx)
        PA.hand_stroke(d, [(x, y0), (x + 3, y1)], col, lw,
                       seed=seed + i * 5, wavelength=110.0)
    for j in range(1, ny):
        y = y0 + (y1 - y0) * j / float(ny)
        PA.hand_stroke(d, [(x0, y), (x1, y - 2)], col, lw,
                       seed=seed + 40 + j * 5, wavelength=130.0)
    # rivets along the top rib -- small dark dots on a light wall
    for i in range(nx):
        x = x0 + (x1 - x0) * i / float(nx)
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(x + 8, y0 + 16, 5, n=8),
                     INK, seed=seed + 80 + i, value=0.05, edge=0.6)


def _tread(d, x0, x1, y0, y1, col, seed, n=6, lw=5):
    """A flight of steps / stair treads seen in perspective.

    The recurring edge-density read for a built structure where the wall alone
    would be a void. Each tread is an outlined L; at a 24px tile that lands on
    one you get two edges.
    """
    for i in range(n):
        u = i / float(n)
        v = (i + 1) / float(n)
        y = y0 + (y1 - y0) * v
        xa = x0 + (x1 - x0) * u * 0.62
        xb = x0 + (x1 - x0) * v
        PA.hand_stroke(d, [(xa, y - (y1 - y0) * 0.055), (xb, y)], col, lw,
                       seed=seed + i * 4, wavelength=70.0)
        PA.hand_stroke(d, [(xb, y), (xb, y + (y1 - y0) * 0.03)], col, lw,
                       seed=seed + 60 + i * 4, wavelength=40.0)


def _fence_run_off_edge(d, y_base, height, seed, col, n_posts=9,
                        x0=-120, x1=W + 120, mesh=True):
    """A fence that starts and ends OFF the frame.

    The frame-fill canon's idiom, applied to the chapter's own signature object:
    a fence whose ends are visible is a prop, a fence whose ends are past the
    edges is a perimeter. Returns nothing; draws.
    """
    _fence(d, x0, y_base, x1, height, seed, n_posts=n_posts, mesh=mesh,
           post_col=col, rail_col=col)


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
    # STAGE A  b01-b07  "There is a place with no name.                      #
    #                 It has a number instead.                             #
    #                 Fifty-One.                                           #
    #                 It is the most secret base on Earth.                  #
    #                 It sits on a dry lake bed.                           #
    #                 In Nevada, north of Las Vegas.                       #
    #                 The sign out front reads Groom Lake.                 #
    #                 A second sign warns of arrest."                       #
    # One bleached playa held across seven beats, and the hook IS the       #
    # emptiness: the desert and the mountain rim own the frame and almost   #
    # nothing else does. Five things happen ON that desert and none of them  #
    # replaces another -- the fence arrives at b01 and is still there at    #
    # b14, the presenter steps in beside it at b01, the name is stamped     #
    # across the sky at b03, the cracked alkali rises out of the flat ground #
    # at b05, the locator inset at b06, the board at b07. A mass arriving   #
    # over a stage is how a beat changes without the frame changing.        #
    # ===================================================================== #
    def a_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 5)
        _mountain_strip(d, HZ, 6)
        # lit course under the title band, so the hardcoded-INK scene title has
        # something to sit on at the top of a bright sky card.
        SC.title_backdrop(tile, 7, col=SKY)
        # EDGE DENSITY. Measured b01 at tile_std 3.46 with 40% of tiles painted:
        # the mountain rim is a single 5px line, the sky above it is one fill
        # and the playa below it is another, so a 24px tile in either the sky
        # or the foreground holds a gradient and nothing else. The desert is
        # the LARGEST thing in this chapter and it was the emptiest. Four bands
        # of contour, a scrub scatter and three boulders put structure into the
        # ground the hook is about ("a place with no name" -- the emptiness is
        # the subject, so the ground has to be real ground, not a blank field).
        _contour_bands(d, HZ + 24, HZ + 300, (216, 210, 194), 8, n=6, lw=5)
        _contour_bands(d, HZ + 96, HZ + 360, (198, 190, 170), 20, n=5, lw=4)
        _tufts(d, HZ + 66, H + 30, (184, 174, 154), 33, n=44)
        _boulder(d, 232, HZ + 214, 44, (208, 200, 182), 71)
        _boulder(d, 520, HZ + 330, 62, (194, 186, 168), 73)
        # The third boulder sat at x=1096, which is inside the presenter's
        # footprint (he stands at x=1040 and reaches +-118 at height 440), so
        # the rock drew over his shoes. It lives at 700 now, clear of him and
        # of the boards that arrive at x<=716 from b07.
        _boulder(d, 700, HZ + 252, 54, (204, 196, 178), 75)
        # Two long scrub-throw ridges running off the side edges: the ground
        # admits it continues past the picture.
        _contour_bands(d, HZ + 330, H + 20, (186, 176, 156), 45, n=3, lw=5,
                       wobble=0.9)
        # And the SKY. It is the largest single area of the day cards and it was
        # one fill; five wide, shallow outlined strata give it high cloud without
        # the scratch the wire-like failures came from.
        _cloud_bands(d, 96, HZ - 60, 120, n=5)
    els.append(SC.stage(clock, 1, a_backdrop, j=5))

    # ---- STAGE A2  b05-b07  the same place, seen from down on the ground -- #
    # The one remaining still-run longer than the reference chapters have is
    # stage A, at 18.7s, and the reason a split does not help for free is
    # arithmetic: SKY 212 and ALKALI 229 are SEVENTEEN levels apart, well under
    # the gate's 24-level threshold, so two bleached-noon cards with different
    # horizons look identical to check_cadence no matter where the horizon sits.
    # The split below therefore drops the camera to the lake bed AND cools the
    # ground to 170, which is 42 levels under the sky it replaces across 36% of
    # the rows -- a cut that registers because the picture is genuinely a
    # different picture, and "you are standing on the dry lake bed looking at
    # nothing" is exactly what b05-b07 are about.
    def a2_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 13, sky=SKY, ground=LAKEBED, hz=190)
        _mountain_strip(d, 190, 14, h=44)
        SC.title_backdrop(tile, 15, col=SKY)
        # EDGE DENSITY. b05 measured 3.11, and this is the WORST frame in the
        # chapter to be flat: the camera is supposed to be down on the lake bed,
        # so 530 of 720 rows are the ground and every one of them was a single
        # smooth fill. It is also the beat whose whole sentence is "it sits on a
        # dry lake bed", so the one thing the card must show in detail is the
        # thing that was blank.
        #
        # TWO PASSES WERE WRONG HERE. The first used `_contour_bands` -- near-
        # horizontal parallel strata -- which measured 5.72 and read as WOOD
        # GRAIN, not as ground: the eye wants a dry lake to be a net of
        # irregular cracked plates, and parallel lines say timber. The second
        # uses `_crust`, a jittered polygon net whose seams run in many
        # directions. The near rows are wide cells and the far rows are narrow,
        # which is what perspective on a flat crust actually looks like.
        _crust(d, 228, H + 10, (196, 172, 130), 16, rows=7, lw=5)
        _crust(d, 300, H + 10, (152, 122, 86), 44, rows=5, lw=4, jitter=0.8,
               cross=0.8)
        _tufts(d, 250, H - 20, (162, 138, 104), 52, n=46)
        _boulder(d, 200, 372, 30, (200, 178, 138), 91)
        _boulder(d, 900, 486, 42, (192, 168, 128), 93)
        # the third sat at y=300, which is ABOVE the 190 horizon, so it floated
        # in the sky. Everything on the ground plane is below hz.
        _boulder(d, 1196, 402, 34, (198, 176, 136), 95)
        _cloud_bands(d, 92, 176, 110, n=4)
    els.append(SC.stage(clock, 5, a2_backdrop, j=8))

    def a_fence(tile, fw, fh):
        # ACCRUES from b01 to the end of stage B. This is the chapter's spine:
        # the line that is up at the first sentence is the same line still
        # standing at b14, and the same line again, near-black, at b33.
        #
        # The band was rebuilt for this wiring. v1 drew it at base 640 with
        # 260px of mesh over the lower half of the frame, and the b14 base --
        # the one thing that caption names -- was buried inside it. It now
        # occupies y 286..462 and everything below 462 is clear ground for the
        # cracked alkali, the base and the runway.
        _fence(ImageDraw.Draw(tile), -60, FENCE_BASE, W + 60, 176, 61,
               n_posts=12)
    els.append(SC.accrue(clock, 1, 5, a_fence, kind='shape', eid='a_fence'))

    def a_presenter(tile, fw, fh):
        # Stands in the RIGHT band, x 922..1158 at height 440, so he never
        # collides with the boards (x 60..716 from b07) and never reaches the
        # locator inset (x 954..1246, y 108..286, which is above his head at
        # y 331). character3 reach is +-107px at height 400, scaling linearly.
        SC.fullbody(ImageDraw.Draw(tile), 1040, 700, 440, pose='standing',
                    expression='deadpan', seed=16)
    # MOVING (small): he steps in from the right as the chapter opens, so the
    # first frame has an anchor instead of three seconds of empty wire.
    _bu, _aa, _au = SC.expr_swap(clock, 2, 'deadpan', 'skeptic', until_j=9)
    els.append(E3.E('a_presenter_a', 'character', a_presenter,
                    at=clock.at('b01', 0), until=_bu,
                    motion=SC.enter(clock, 1, dx=130, dy=0, dur=ARRIVE)))

    def a_presenter_b(tile, fw, fh):
        # "It has a number instead." -- the brows go up. Same x, same feet, so
        # the two elements hand off with no jump (SC.expr_swap).
        SC.fullbody(ImageDraw.Draw(tile), 1040, 700, 440, pose='standing',
                    expression='skeptic', seed=16)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))

    def a_name(tile, fw, fh):
        # THE CHAPTER'S ONE DISPLAY OBJECT. Stamped in the SKY, above the
        # fence top at y=286, so it never fights the wire and there is no
        # second text object in stage A competing with it.
        D.draw_label(tile, 'AREA 51', center=(520, 186), color=INK, size=110)
        D.draw_label(tile, 'THE BASE WITH NO NAME', center=(520, 262),
                     color=RED, size=36, outline=INK, outline_w=2)
    els.append(SC.layer(clock, 3, a_name, j=5, kind='shape', eid='a_name',
                        motion=SC.enter(clock, 3, dy=-40, dur=ARRIVE)))
    # The name ends with stage A, not with the desert act: stage A2 drops the
    # camera to the lake bed, and 110px display type with a subtitle on a low
    # horizon stops reading as a stamped title and starts reading as a
    # collision with the ground.
    # NO caption at b02 (adjacent to b01) and none at b03: the frame is
    # printing "AREA 51" in 110px type and saying "Fifty-One." underneath it
    # would be the same words twice. None at b05 either -- the cracked alkali
    # IS "it sits on a dry lake bed", and naming the ground the ground already
    # shows is the caption that costs the viewer its time.
    els.append(cap(1, 640, 168, size=34))
    els.append(cap(4, 1080, 232, size=30, max_w=440))

    def a_crust(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The cracked alkali, ARRIVING at b05 and never leaving. In v1 this net
        # was the whole b05 card; here it is drawn onto the stage the viewer is
        # already looking at, so "it sits on a dry lake bed" is a change to the
        # ground rather than a cut to a new drawing.
        #
        # It starts BELOW the fence (first row 486, fence base 462) so the two
        # never share a pixel band, and each row is broken into offset segments
        # so they read as a cracked polygon net rather than five long wires.
        rows = (HZ + 40, HZ + 110, HZ + 200, HZ + 310, HZ + 440)
        for k, y in enumerate(rows):
            if y > H + 10:
                break
            amp = 8 + k * 4
            x = -40.0
            while x < W + 40:
                x2 = x + 120
                PA.hand_stroke(d, [(x, y + amp * math.sin(x * 0.011 + k * 1.7)),
                                   (x2, y + amp * math.sin(x2 * 0.011 + k * 1.7))],
                               (196, 190, 178), 5, seed=25 + k,
                               wavelength=110.0)
                x = x2
            for j in range(6):
                x0 = 60 + j * 210 + k * 40
                y1 = rows[k + 1] if k + 1 < len(rows) else min(y + 90, H - 6)
                PA.hand_stroke(d, [(x0, y + amp * math.sin(x0 * 0.011 + k * 1.7)),
                                   (x0 + 34, y1)], (196, 190, 178), 4,
                               seed=40 + k * 8 + j, wavelength=70.0)
    els.append(SC.accrue(clock, 5, 8, a_crust, kind='shape', eid='a_crust'))

    def a_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The locator INSET, not a full-frame map card. v1 gave "In Nevada" the
        # whole frame and lost the lake bed it was describing; an inset in the
        # sky carries the same information and stays put for the rest of the
        # act. It is sized and placed for stage A2's LOW horizon (190), so it
        # sits in the strip of sky above the wire and never crosses the skyline.
        land = [(960, 198), (1086, 186), (1214, 208), (1238, 250),
                (1172, 276), (1044, 266), (956, 226)]
        PA.fill_poly(tile, land, (208, 190, 146), seed=29, value=0.07)
        PA.hand_stroke(d, land, INK, 6, closed=True, seed=30, wavelength=110.0)
        d.ellipse([1140, 148, 1170, 178], fill=RED)
        PA.hand_stroke(d, [(1155, 182), (1155, 240)], RED, 5, seed=31,
                       wavelength=70.0)
    els.append(SC.accrue(clock, 6, 8, a_map, kind='shape', eid='a_map',
                         motion=SC.enter(clock, 6, dx=90, dy=0, dur=ARRIVE)))
    # The caption at b06 is KEPT because the map shows WHERE and the words
    # supply the one thing the art cannot -- that the state is Nevada, and
    # which way is north.
    els.append(cap(6, 470, 216, size=30, max_w=560))

    def a_groomsign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        sb = [(64, 300), (700, 286), (716, 462), (80, 476)]
        PA.fill_poly(tile, sb, (222, 214, 190), seed=35, value=0.08)
        PA.hand_stroke(d, sb, INK, 7, closed=True, seed=36, wavelength=150.0)
        D.draw_label(tile, 'GROOM LAKE', center=(390, 378), color=INK, size=48)
        PA.hand_stroke(d, [(190, 470), (166, 660)], (128, 118, 100), 15,
                       seed=37, wavelength=90.0)
        PA.hand_stroke(d, [(560, 456), (584, 660)], (128, 118, 100), 15,
                       seed=38, wavelength=90.0)
    els.append(SC.layer(clock, 7, a_groomsign, j=8, kind='shape',
                        eid='a_groomsign',
                        motion=SC.enter(clock, 7, dy=-46, dur=ARRIVE)))
    # NO caption at b07: the board is DRAWN reading GROOM LAKE in 48px ink.
    # Captioning "The sign out front reads Groom Lake." would print the same
    # words twice in the same frame. That is the rule that earns the b07 slot
    # back by REMOVING text, not adding it.

    # ===================================================================== #
    # STAGE B  b08-b14  "A second sign warns of arrest.                      #
    #                 Nobody will say what is inside.                      #
    #                 The fence runs for miles across the desert.          #
    #                 It surrounds nothing you can see.                    #
    #                 There is a second fence behind it.                  #
    #                 Cameras sit on tall poles along the wire.            #
    #                 The base is smaller than its fence."                 #
    # DUSK, and the same playa. Every arrival here lands on a wire that has  #
    # been standing since the first sentence: the board re-lettered at b08,  #
    # the shrug at b09, a watcher cropped by the right edge at b11, a second #
    # wire receding above the first at b12, two camera heads at b13, and the #
    # base at b14, small, in front -- so the comparison the last sentence     #
    # makes becomes one readable frame with no cut in it.                    #
    # ===================================================================== #
    def b_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # DUSK. The horizon is raised to 250 so the whole fence band
        # (286..462) sits on ground and no post crosses the skyline.
        PA.fill_rect(tile, [0, 0, W, H], DUSK_SKY, seed=201, value=0.06)
        PA.fill_rect(tile, [0, 250, W, H], DUSK_GROUND, seed=202, value=0.08)
        PA.paper_overlay(tile, seed=203)
        # the far rim, dusk-valued
        n = 30
        far = [(-40, 250)]
        for i in range(n + 1):
            u = i / 30.0
            far.append((-40 + (W + 80) * u,
                        250 - 30 * (0.3 + 0.7 * abs(math.sin(u * 7.3 + 1.9)))))
        far.append((W + 40, 250))
        PA.fill_poly(tile, far, DUSK_RIM, seed=204, value=0.05)
        pts = [(-40, 250)]
        for i in range(n + 1):
            u = i / 30.0
            pts.append((-40 + (W + 80) * u,
                        250 - 64 * (0.30 + 0.70 * abs(math.sin(u * 9.1 + 0.6)))))
        pts.append((W + 40, 250))
        PA.fill_poly(tile, pts, (128, 100, 92), seed=205, value=0.06)
        PA.hand_stroke(d, pts, INK, 5, closed=False, seed=206, wavelength=140.0)
        # a lit course for the INK scene title against the dusk sky
        SC.title_backdrop(tile, 207, col=(126, 110, 100))
        # EDGE DENSITY. Stage B already ranks highest in the chapter (b14 at
        # 11.38) because it stacks two fences and a crack net, but its BACKDROP
        # is still what b08-b11 sit on and it measured 4.18 / 6.40 / 7.23 --
        # under the bar. The dusk ground is one fill from y=250 to 720 and the
        # rim is two polys. Dusk-valued crust and a cloud deck in dusk values
        # (same `_crust` read as stage A2 -- the playa is the same dry lake,
        # only the light is different).
        _crust(d, 292, H + 10, (134, 102, 80), 220, rows=7, lw=4)
        _crust(d, 350, H + 10, (98, 72, 58), 244, rows=5, lw=4, jitter=0.8,
               cross=0.8)
        _tufts(d, 330, H - 10, (104, 78, 62), 256, n=34)
        _boulder(d, 386, 596, 40, (160, 126, 96), 271)
        _boulder(d, 1042, 662, 52, (150, 116, 88), 273)
        _cloud_bands(d, 96, 244, 280, n=4, col=(126, 106, 98))
    els.append(SC.stage(clock, 8, b_backdrop, j=15))

    def b_crust(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The cracked alkali again, dusk-valued and lower-contrast, for the same
        # ordering reason as b_fence: this is appended BEFORE the wire so the
        # cracks are UNDER it. Ground that cracks cannot cross a fence. (The
        # first pass had them the other way round and the net drew over both
        # fences, which read as a cage made of cracks.)
        rows = (296, 366, 452, 566, 690)
        for k, y in enumerate(rows):
            amp = 7 + k * 3
            x = -40.0
            while x < W + 40:
                x2 = x + 120
                PA.hand_stroke(d, [(x, y + amp * math.sin(x * 0.011 + k * 2.3)),
                                   (x2, y + amp * math.sin(x2 * 0.011 + k * 2.3))],
                               (168, 136, 104), 5, seed=60 + k,
                               wavelength=110.0)
                x = x2
            for j in range(6):
                x0 = 60 + j * 210 + k * 40
                y1 = rows[k + 1] if k + 1 < len(rows) else min(y + 80, H - 6)
                PA.hand_stroke(d, [(x0, y + amp * math.sin(x0 * 0.011 + k * 2.3)),
                                   (x0 + 34, y1)], (168, 136, 104), 4,
                               seed=70 + k * 8 + j, wavelength=70.0)
    els.append(SC.accrue(clock, 8, 15, b_crust, kind='shape', eid='b_crust'))

    def b_fence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE SAME WIRE, RE-LIT. It has to be declared again here rather than
        # carried over from stage A, and the reason is mechanical and worth
        # stating because it is invisible until you render a frame and find the
        # fence missing: engine3 composites `scene.elements` in LIST order, so a
        # stage backdrop paints OVER every element appended before it. An
        # element that outlives its stage is not merely stale, it is INVISIBLE.
        # Every reference conversion scopes its `accrue` to its own stage for
        # the same reason. Same band (286..462) and same post spacing as the
        # noon one, which is what makes it read as the same fence under a
        # different sky rather than as a second fence.
        _fence(d, -60, FENCE_BASE, W + 60, 176, 61, n_posts=12,
               post_col=(38, 32, 32), rail_col=(38, 32, 32))
    els.append(SC.accrue(clock, 8, 15, b_fence, kind='shape', eid='b_fence'))

    def b_arrestsign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE SAME BOARD, re-lettered -- the only replace in the chapter, and
        # the reason it measures under a third of the frame is that both boards
        # occupy the SAME band: the pixels that change are one band, not two.
        # Accruing a second board on top would put two text-bearing objects in
        # the same 640px of frame and neither would be readable.
        sb = [(64, 300), (700, 286), (716, 462), (80, 476)]
        PA.fill_poly(tile, sb, (236, 226, 208), seed=40, value=0.07)
        PA.hand_stroke(d, sb, INK, 7, closed=True, seed=41, wavelength=150.0)
        D.draw_label(tile, 'RESTRICTED AREA', center=(390, 350), color=INK,
                     size=38)
        D.draw_label(tile, 'VIOLATORS WILL BE', center=(390, 424), color=RED,
                     size=32, outline=INK, outline_w=2)
        PA.hand_stroke(d, [(190, 470), (166, 660)], (118, 100, 88), 15,
                       seed=42, wavelength=90.0)
        PA.hand_stroke(d, [(560, 456), (584, 660)], (118, 100, 88), 15,
                       seed=43, wavelength=90.0)
    els.append(SC.layer(clock, 8, b_arrestsign, j=9, kind='shape',
                        eid='b_arrestsign',
                        motion=SC.enter(clock, 8, dy=-46, dur=ARRIVE)))
    # NO caption at b08: the board is printed RESTRICTED AREA / VIOLATORS WILL
    # BE. The words are already on the wall.

    def b_shrug(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Nobody will say what is inside." A POSE CHANGE, not a second
        # character: the shrug is drawn at the presenter's own x=1040 and takes
        # over from the standing figure at the same instant, so the frame holds
        # one person throughout the act. A shrug at height 440 reaches +-187,
        # i.e. x 853..1227, clear of the board at x<=716.
        SC.fullbody(d, 1040, 700, 440, pose='shrug', expression='skeptic',
                    seed=47)
        # The bubble's xy is its TOP-LEFT and tail_to aims at the mouth. At
        # height 440 his mouth is at about (1040, 380), so the tail has to land
        # near there; the first pass aimed at (900, 356) and drew a 90px needle
        # that stopped in mid-air beside his shoulder.
        D.draw_bubble(tile, 'no answer', (690, 226), tail_to=(1004, 372))
    els.append(SC.layer(clock, 9, b_shrug, j=10, kind='character',
                        eid='b_shrug',
                        motion=SC.enter(clock, 9, dx=96, dy=0, dur=ARRIVE)))
    # NO caption at b09: the shrug plus the "no answer" bubble IS the line.

    def b_peeker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # CROPPED BY THE RIGHT EDGE. At v1's x=980 he read as set dressing
        # beside a fence; put at x=1240 he is cut by the frame edge with most of
        # him still visible, which is what makes him read as someone intruding
        # on the shot rather than as a black stick at the margin. The first pass
        # at 1330 showed only an arm and a shoe -- crop too hard and he stops
        # being a person.
        #
        # He LEAVES at b13. He is a two-beat idea ("it surrounds nothing you can
        # see") and keeping him for four beats put a person, two fences, two
        # camera masts, a base and a crack net on one frame, which is the
        # over-populated loss pattern the blind critic has punished before.
        SC.fullbody(d, 1240, 700, 440, pose='peeking', expression='deadpan',
                    seed=57)
    els.append(SC.layer(clock, 11, b_peeker, j=13, kind='character',
                        eid='b_peeker',
                        motion=SC.enter(clock, 11, dx=120, dy=0, dur=0.45)))
    els.append(cap(11, 430, 208, size=30, max_w=620))
    # NO caption at b10: a wire fence running off both edges of the frame IS
    # "runs for miles". The word would be smaller than the evidence.
    # The caption at b11 sits at y=208, ABOVE the fence top at 286, on clean
    # dusk sky, because below the fence the cracked-alkali net is still on the
    # ground and a caption on top of a wire mesh is unreadable.

    def b_farfence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The second fence, RECEDING and deliberately small: 66px tall, six
        # posts, spanning x 300..980 only, so it sits INSIDE the near fence's
        # run rather than matching it. The first pass made it 110px over the
        # full width, which produced two fences of nearly equal size and read
        # as a thicket instead of as depth.
        _fence(d, 300, 214, 980, 66, 63, n_posts=6,
               post_col=(58, 48, 46), rail_col=(58, 48, 46))
    els.append(SC.accrue(clock, 12, 15, b_farfence, kind='shape',
                         eid='b_farfence',
                         motion=SC.enter(clock, 12, dx=0, dy=-24, dur=0.45)))
    # NO caption at b12: two fences at two depths IS "a second fence behind it".

    def b_camera(tile, fw, fh):
        # ONE mast, not two, and set well out at x=210 so it frames the left
        # edge instead of standing in the middle of the shot. Two masts at
        # 290px dominated every other object on the stage; at 200px and pushed
        # to the margin it reads as what it is -- one camera on a pole along a
        # wire -- and the base at b14 is free to be the subject again.
        _camera_pole(ImageDraw.Draw(tile), 210, 496, 200, 67, lens_dir=1)
    els.append(SC.accrue(clock, 13, 15, b_camera, kind='shape', eid='b_camera',
                         motion=SC.enter(clock, 13, dx=-30, dy=0, dur=0.45)))
    # NO caption at b13: a camera head with its red lens, standing on the wire,
    # is the words.

    def b_base(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE COMPARISON, in one frame, and this beat finally gets the scale it
        # needs: the near wire runs off both edges at 176px in the upper third
        # and the base that justifies it now spans 330px of a 1280 frame at
        # 190px tall, standing on clear alkali below the fence line. v1 drew it
        # 104/84/132 wide at y=620 under 280px of mesh, so the one thing the
        # caption names was the one thing you could not see.
        _bunker(d, 404, 646, 196, 108, 73)
        _bunker(d, 616, 646, 160, 92, 74)
        _tower(d, 812, 646, 172, 75)
    els.append(SC.accrue(clock, 14, 15, b_base, kind='shape', eid='b_base'))
    els.append(cap(14, 1000, 214, size=30, dark=True, max_w=460))
    # The b14 caption is the ONE place in this chapter where a drawn label and
    # a caption would have been redundant, so the drawn labels were dropped and
    # the words kept: "The base is smaller than its fence" says the comparison
    # out loud, and the art makes it true without printing on it. It moved from
    # the floor to the SKY at x=1000 because the base now occupies the floor and
    # red ink on the dark crack net at y 690 measured about 2.6:1.
    # The b14 caption is the ONE place in this chapter where a drawn label and
    # a caption would have been redundant, so the drawn labels were dropped and
    # the words kept: "The base is smaller than its fence" says the comparison
    # out loud, and the art makes it true without printing on it.

    # ===================================================================== #
    # STAGE C  b15-b19  "No aircraft may fly overhead.                       #
    #                 Red dashed line drawn across the sky.                #
    #                 Pilots noticed the rule before it was admitted.        #
    #                 Pilots reported lights over the dry lake.              #
    #                 In 1955, the reports started."                         #
    # WHY THIS STAGE IS NIGHT. v1 painted b18 as a night cockpit card in the #
    # middle of a bleached-noon chapter and it read as a register glitch. But #
    # "pilots reported lights over the dry lake" has NO honest read on a      #
    # white playa -- a red halo on alkali-white ground is invisible. So the   #
    # whole stage is night: the red dashed ceiling becomes the strongest      #
    # image in the chapter against NIGHT, and the light at b18 finally lands.#
    # `SC.title_backdrop` is called first so the hardcoded-INK scene title can#
    # be read over the dark band.                                             #
    #                                                                       #
    # The SPINE of the stage is the rule itself: the jet arrives at b15 and   #
    # stays to the end, and the red ceiling draws itself across the sky at    #
    # b16 and stays. The three beats that comment on the rule -- the red X and#
    # the pointing pilot at b17, the haloes at b18, the calendar at b19 --    #
    # are arrivals sized so none of them moves more than a third of the frame.#
    # That is the measured constraint: the previous wiring replaced the       #
    # jet-with-an-X for the haloes and the haloes for the calendar, and the   #
    # b19 onset alone swapped 48% of the picture.                             #
    # ===================================================================== #
    def c_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], NIGHT, seed=101, value=0.12)
        PA.fill_rect(tile, [0, HZ - 6, W, H], NIGHT_G, seed=102, value=0.12)
        PA.paper_overlay(tile, seed=103)
        SC.title_backdrop(tile, 118, col=(84, 92, 118))
        # the same mountain rim, night-valued, so the horizon still has depth
        pts = [(-40, HZ)]
        for i in range(31):
            u = i / 30.0
            pts.append((-40 + (W + 80) * u,
                        HZ - 44 * (0.30 + 0.70 * abs(math.sin(u * 9.1 + 0.6)))))
        pts.append((W + 40, HZ))
        PA.fill_poly(tile, pts, (44, 46, 58), seed=104, value=0.05)

        # EDGE DENSITY. Stage C measured 3.04-3.27 across all five of its beats,
        # the lowest run in the chapter, and the reason is structural rather
        # than cosmetic: the register is NIGHT 28/NIGHT_G 18, i.e. a 10-level
        # pair, so almost the entire frame is a near-black field. There is no
        # value to work with, and the stage had one jet (210px) and one 9px red
        # line on it. Everything below is added at NIGHT-VALUED contrast --
        # never bright paint, which would read as daylight and break the
        # register the stage exists to hold.
        #
        # A star field is the primary read: a night sky with nothing in it is
        # the single largest void in the film, and this is a chapter about a
        # place people cannot see, so a sky with stars in it says exactly that.
        _stars(d, -20, 96, W + 20, HZ - 20, 300, n=64)
        _stars_spark(d, 214, 168, 380)
        _stars_spark(d, 1086, 132, 384)
        _stars_spark(d, 792, 262, 388)
        # A thin cloud deck catching the last light, so the sky is layered
        # rather than a gradient between the title band and the rim.
        _cloud_bands(d, 120, HZ - 40, 390, n=4, col=(48, 52, 70))
        # The rim gets a second range behind it in near-black, and the ground
        # gets a night crust so the lower half is not one field.
        far = [(-40, HZ)]
        for i in range(21):
            u = i / 20.0
            far.append((-40 + (W + 80) * u,
                        HZ - 26 * (0.3 + 0.7 * abs(math.sin(u * 6.1 + 2.4)))))
        far.append((W + 40, HZ))
        PA.fill_poly(tile, far, (36, 38, 50), seed=392, value=0.05)
        # The ground detail at NIGHT has to stay within a few levels of NIGHT_G. Both
        # passes were originally 20-36 levels lighter, which on a register this
        # dark means the crust was the highest-contrast thing in the lower half
        # and the eye read a wireframe web strung over the playa rather than the
        # playa itself. A night crust is a suggestion: the cell seams at 8-14
        # levels over the ground, and almost no interior diagonals.
        _crust(d, HZ + 20, H + 10, (40, 38, 50), 396, rows=6, lw=4, cross=0.30)
        _crust(d, HZ + 120, H + 10, (34, 32, 44), 398, rows=4, lw=4, cross=0.22)

        # THE REAL EDGE DENSITY AT NIGHT IS LIGHT, NOT CRACKS. With the crust
        # softened to a suggestion, stage C fell back under the bar (b15/b16/
        # b18 at 6.8-7.4), because the register is NIGHT 28 / NIGHT_G 18 -- ten
        # levels -- and there is simply no value to find detail in. The answer
        # is to put LIT STRUCTURE in the frame, which is both what a restricted
        # airfield looks like at night and what gives a dark frame its local
        # contrast honestly: a lit hangar bar with panel joints and a lit strip
        # door, four apron lamp pools on the ground, and the mast-and-head
        # silhouette of the fence line along the rim. Bright marks on black are
        # high contrast; the playa under them stays a playa.
        _bunker(d, 120, HZ + 96, 250, 118, 410)
        for i in range(4):
            lx = 200 + i * 292
            d.ellipse([lx - 46, HZ + 150, lx + 46, HZ + 190],
                      fill=(52, 54, 72), outline=(70, 72, 92), width=3)
        _fence_run_off_edge(d, HZ + 34, 62, 414, (74, 78, 98), n_posts=8)
        _tower(d, 1128, HZ + 40, 96, 416)
        _camera_pole(d, 906, HZ + 52, 82, 418, lens_dir=1)
        _stars_spark(d, 402, 214, 420)
        _stars_spark(d, 986, 172, 424)
        _tufts(d, HZ + 60, H - 10, (40, 36, 46), 400, n=26)
        _boulder(d, 268, 566, 40, (48, 46, 56), 402)
        _boulder(d, 1088, 640, 54, (44, 42, 52), 404)
    els.append(SC.stage(clock, 15, c_backdrop, j=20))

    def c_jet(tile, fw, fh):
        # SIZED UP from 210 to 300. The frame-fill canon says a subject under a
        # third of the frame is a defect, and the jet was the ONLY subject on
        # the whole stage -- 210px on a 1280 frame is 16% of the width, which is
        # a model-airplane read. At 300 it is 23% and sits under the red
        # ceiling it is about to violate. The red X box and the pilot's reach
        # are sized to it below.
        _jet(ImageDraw.Draw(tile), 600, 196, 300, 108)
    els.append(SC.accrue(clock, 15, 20, c_jet, kind='shape', eid='c_jet',
                         motion=SC.enter(clock, 15, dx=210, dy=0, dur=ARRIVE)))
    # MOVING (small): the aircraft flies in from the right and stays. At 210px
    # of travel over 0.5s it is a clear arrival and a clear hold.

    def c_ceiling(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The no-fly ceiling. It is a THIN line, so this is one of the few
        # elements in the chapter allowed to move across the frame: a 150px
        # draw-on over 0.55s reads as the rule being drawn, not as the picture
        # churning. Everything wide in this chapter stays still.
        y = 232
        dash, gap, x = 60, 34, -40
        while x < W + 40:
            PA.hand_stroke(d, [(x, y), (x + dash, y)], RED, 9, seed=105 + x,
                           wavelength=70.0)
            x += dash + gap
    els.append(SC.accrue(clock, 16, 20, c_ceiling, kind='shape',
                         eid='c_ceiling',
                         motion=SC.enter(clock, 16, dx=-150, dur=0.55)))

    def c_x(tile, fw, fh):
        # The rule, enforced: a red X laid over the jet that is ALREADY there.
        # In the previous wiring this was a separate element that also redrew
        # the jet and added the presenter, and it REPLACED the original jet --
        # a second aircraft plus a red X plus a full-body character, all landing
        # and leaving at once. Here the jet is the persistent one and this is
        # ink on top of it.
        #
        # RESIZED to the jet: the aircraft went from 210 to 300 and its
        # fuselage now spans x 384..816 with the red ceiling line at y=232
        # crossing it. The old X box [452,156,668,226] sat on the OLD fuselage
        # and stopped short of both ends, so at the new size it would have been
        # a mark floating on the left half of the aircraft. The box now straddles
        # the whole fuselage.
        D.draw_red_x(tile, [400, 150, 800, 240], color=RED, width=9)
    els.append(SC.layer(clock, 17, c_x, j=18, kind='shape', eid='c_x'))

    def c_pilot(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Pilots noticed the rule before it was admitted." He points at the
        # line he has just been shown. He LEAVES at b18: the haloes are the next
        # beat's subject and he has done his job.
        #
        # MOVED LEFT and SLIGHTLY SMALLER because the jet grew: at x=250/height
        # 430 a pointing reach put his hand at x=461, and the enlarged aircraft
        # now starts at x=384, so his outstretched arm drew across the
        # fuselage. At x=186/height 390 his reach is 96..368 -- clear of the
        # jet's left edge by 16px, and he is cropped by nothing, standing on the
        # near crust.
        SC.fullbody(d, 186, 700, 390, pose='a51_pointing_e', expression='shock',
                    seed=100, ink=(236, 228, 208))
    els.append(SC.layer(clock, 17, c_pilot, j=18, kind='character',
                        eid='c_pilot',
                        motion=SC.enter(clock, 17, dx=-110, dy=0, dur=ARRIVE)))
    # NO caption at b16: the line IS the words. NO caption at b15: the jet with
    # the line drawn across its path says "no aircraft may fly overhead" in the
    # clearest available idiom. NO caption at b17 either -- the pointing figure
    # and the crossed-out aircraft are the sentence.
    els.append(cap(17, 900, 692, size=30, dark=True, max_w=620))
    # The caption at b17 is KEPT because the art at b17 can only say "no
    # aircraft may fly", not "pilots noticed the rule BEFORE it was admitted"
    # -- the timing is the fact and the art has no way to hold it. It sits at
    # y=692, on the alkali below the horizon, where the pilot's feet and the
    # horizon rim are the only other things and neither reaches that row.

    def c_lights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Pilots reported lights over the dry lake." A cluster of haloes ON
        # the ground with a dark cockpit frame cropping the top -- we are inside
        # the aircraft looking down at them, which is what makes the haloes
        # read as reported rather than decorative.
        for lx, ly, rr in ((700, 540, 96), (860, 596, 66), (556, 604, 54)):
            for r2, col in ((rr, (66, 34, 36)), (rr * 0.58, (140, 56, 48)),
                            (rr * 0.26, RED)):
                d.ellipse([lx - r2, ly - r2 * 0.62, lx + r2, ly + r2 * 0.62],
                          fill=col)
        PA.fill_poly(tile, [(0, 0), (W, 0), (W, 118), (0, 138)],
                     (18, 18, 22), seed=106, value=0.05)
        # The wedge covers the stage's title band, so the lit course is laid
        # back on top of it -- same order as v1's night cockpit card. Without
        # this the INK title lands on near-black and measures ~1.15:1.
        SC.title_backdrop(tile, 118, col=(84, 92, 118))
        PA.hand_stroke(d, [(0, 138), (320, 178), (960, 178), (W, 138)], INK, 8,
                       seed=107, wavelength=140.0)
    els.append(SC.layer(clock, 18, c_lights, j=19, kind='shape',
                        eid='c_lights',
                        motion=SC.enter(clock, 18, dy=-30, dur=0.45)))

    def c_1955(tile, fw, fh):
        # "In 1955, the reports started." RESIZED, and that is the fix. v1 drew
        # this at w=380 h=290, a 760x580 sheet -- 48% of the frame -- over a
        # stage that was also losing the haloes and the pointing pilot at the
        # same instant, which measured as a 0.48 reframe: a new image wearing
        # the old stage's clothes. At w=190 h=145 the sheet is 380x290 (12% of
        # the frame) and the year is still the brightest thing on the stage.
        _calendar(ImageDraw.Draw(tile), 960, 430, 190, 145, 110, year=1955,
                  circle_year=True)
    els.append(SC.layer(clock, 19, c_1955, j=20, kind='shape', eid='c_1955'))
    # NO caption at b19: the calendar is DRAWN with 1955 on it in a 72px
    # numeral. The clearest case in the chapter of a caption that would be pure
    # duplication.

    # ===================================================================== #
    # STAGE D  b20-b21  "Roswell was already three years old.                #
    #                 The desert kept the story all the same."               #
    # Two beats, and the shortest stage in the chapter. It exists because the #
    # register has to come back to DAY before a hangar can be outside, and    #
    # two beats is what that costs. The calendar and the balloon go into the  #
    # open sky at different heights, so both can stay.                       #
    # ===================================================================== #
    def d_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 151)
        _mountain_strip(d, HZ, 152)
        SC.title_backdrop(tile, 153, col=SKY)
    els.append(SC.stage(clock, 20, d_backdrop, j=22))

    def d_roswell(tile, fw, fh):
        # 1947, three years before 1955. The beat is a DATE, so the calendar
        # primitive draws it.
        _calendar(ImageDraw.Draw(tile), 430, 400, 200, 152, 154, year=1947,
                  circle_year=True)
    els.append(SC.layer(clock, 20, d_roswell, j=21, kind='shape',
                        eid='d_roswell',
                        motion=SC.enter(clock, 20, dy=-52, dur=ARRIVE)))
    els.append(cap(20, 1040, 300, size=30, max_w=440))
    # The caption at b20 is KEPT because the calendar prints only the YEAR. The
    # name on the beat -- Roswell -- appears nowhere in the art, and it is the
    # name that makes 1947 mean something to a viewer who has not heard it.

    def d_balloon(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "The desert kept the story all the same." The sagging balloon comes
        # back over the wire -- the same half-deflated silhouette from v1 --
        # cropped by the right edge so it owns that side of the frame instead
        # of floating as a small prop. The faint year is GONE: 1947 is already
        # printed on the calendar and printing it twice in one frame is the
        # pile-up this model exists to prevent.
        _balloon_low(tile, d, 1080, 330, 210, 155)
    els.append(SC.layer(clock, 21, d_balloon, j=22, kind='shape',
                        eid='d_balloon',
                        motion=SC.enter(clock, 21, dx=170, dy=0, dur=ARRIVE)))
    # NO caption at b21: the sagging balloon IS "the story went flat", and b20
    # is one beat earlier with words on it.

    # ===================================================================== #
    # STAGE E  b22-b25  "Pilots named the place Hangar 18.                   #
    #                 Empty hangar door, number painted on the wall.        #
    #                 Officially, that hangar is not there.                 #
    #                 Nellis Air Force Base runs the site."                 #
    # A HANGAR AND THE GROUND IT SITS ON. The stage backdrop is the whole    #
    # scene: desert on the right, the building filling the left, with its door#
    # opening cut into it. Making this a STAGE rather than an arriving layer  #
    # is not a dodge -- v1 accrued a 1360x564 wall here, which measured as a  #
    # 0.71 reframe at b22 and was flagged as exactly the thing the stage      #
    # model is for. A backdrop onset is a cut to a new place, which is a      #
    # legitimate edit; a 71%-of-the-frame layer is not.                       #
    #                                                                       #
    # Inside the stage nothing replaces anything. The painted 18 stays; the  #
    # leaf SLIDES off the opening it was already covering; the stamp lands on #
    # top; and Nellis is written across the empty desert on the right, which  #
    # has been empty since b22 precisely so it can be.                       #
    # ===================================================================== #
    def e_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # OVERCAST, AND THAT IS THE POINT. The first pass painted the hangar in
        # CONCRETE (L=200) against a SKY of L=212 -- twelve levels apart -- so
        # the building was invisible and the frame read as a thin black arc on a
        # blue field. The sky here is 177 and the wall is 124: fifty-three
        # levels, which is what makes the building a building.
        PA.fill_rect(tile, [0, 0, W, H], OVERCAST, seed=401, value=0.06)
        PA.fill_rect(tile, [0, HZ - 6, W, H], APRON, seed=402, value=0.07)
        PA.paper_overlay(tile, seed=403)
        SC.title_backdrop(tile, 404, col=OVERCAST)
        # The far rim, overcast-valued, so the horizon still has a landform.
        pts = [(-40, HZ)]
        for i in range(31):
            u = i / 30.0
            pts.append((-40 + (W + 80) * u,
                        HZ - 52 * (0.30 + 0.70 * abs(math.sin(u * 9.1 + 0.6)))))
        pts.append((W + 40, HZ))
        PA.fill_poly(tile, pts, (128, 132, 138), seed=405, value=0.05)
        PA.hand_stroke(d, pts, INK, 5, closed=False, seed=406, wavelength=140.0)

        # THE RIGHT HALF IS COMPOSED FROM b22, not left empty until b25. Nellis
        # at b25 has to ARRIVE at something; a bare 570px of desert gave it
        # nowhere to land and made the three preceding beats read as an
        # under-filled frame. So the apron goes down here, in the backdrop,
        # where it costs no onset: a service road running out to the right, its
        # edge lines, a fence stub receding, and the fuel bowser that stands in
        # front of the hangar every day of its life.
        PA.fill_poly(tile, [(740, 720), (860, 470), (1000, 470), (1240, 720)],
                     (146, 142, 134), seed=410, value=0.06)
        PA.hand_stroke(d, [(860, 470), (1000, 470)], (104, 100, 94), 5,
                       seed=411, wavelength=90.0)
        PA.hand_stroke(d, [(742, 716), (874, 502)], (226, 222, 206), 8,
                       seed=412, wavelength=140.0)
        PA.hand_stroke(d, [(1004, 502), (1238, 716)], (226, 222, 206), 8,
                       seed=413, wavelength=140.0)
        _fence(d, 1010, 470, 1330, 74, 414, n_posts=5,
               post_col=(96, 92, 86), rail_col=(96, 92, 86))
        # the fuel bowser: a tank on a two-wheel chassis with a hose reel
        PA.fill_poly(tile, [(792, 596), (930, 596), (930, 664), (792, 664)],
                     (176, 172, 164), seed=416, value=0.07)
        PA.hand_stroke(d, [(792, 596), (930, 596), (930, 664), (792, 664)],
                       INK, 6, closed=True, seed=417, wavelength=90.0)
        d.ellipse([800, 656, 838, 694], fill=(52, 52, 58), outline=INK, width=4)
        d.ellipse([886, 656, 924, 694], fill=(52, 52, 58), outline=INK, width=4)
        PA.hand_stroke(d, [(872, 640), (872, 596), (940, 578)], (60, 60, 66),
                       7, seed=418, wavelength=70.0)

        # The building. Cropped BY the left edge so it owns that side of the
        # frame instead of sitting centred as a prop.
        shell = [(-70, 660), (-70, 300)]
        n = 30
        for i in range(n + 1):
            u = i / float(n)
            shell.append((-70 + 780 * u, 300 - 108 * math.sin(math.pi * u)))
        shell.append((710, 660))
        PA.fill_poly(tile, shell, WALL, seed=420, value=0.07)
        PA.hand_stroke(d, shell, INK, 7, closed=True, seed=421, wavelength=150.0)
        # Panel seams, horizontal joints and a skirt. The first pass drew
        # verticals only, at a tone 8 values off the wall, and the frame
        # measured as a pale empty field; a hangar wall reads as a wall when it
        # has HORIZONTAL joints too, a dark skirt where it meets the ground,
        # and a shadow plane.
        for i in range(7):
            x = 30 + i * 104
            PA.hand_stroke(d, [(x, 220), (x, 640)], (104, 100, 94), 7,
                           seed=422 + i, wavelength=110.0)
        for jy in (430, 560):
            PA.hand_stroke(d, [(-60, jy), (700, jy)], (108, 104, 98), 6,
                           seed=430 + jy, wavelength=150.0)
        PA.fill_rect(tile, [-60, 600, 700, 660], (88, 84, 80), seed=440,
                     value=0.05)
        # The opening, cut into the wall. It is painted FIRST and never
        # changes: what makes "empty hangar door" legible is the leaf sliding
        # OFF this dark rectangle, not a dark rectangle arriving. At 360x308 it
        # was nearly half the building and read as a void punched through the
        # wall; a hangar door is tall and comparatively narrow, so it is 280
        # wide against a 780px building and its head is tucked under the arch.
        PA.fill_poly(tile, [(96, 392), (376, 392), (376, 652), (96, 652)],
                     (34, 38, 48), seed=441, value=0.05)
        PA.hand_stroke(d, [(96, 392), (376, 392), (376, 652), (96, 652)],
                       INK, 6, closed=True, seed=442, wavelength=120.0)
    els.append(SC.stage(clock, 22, e_backdrop, j=26))

    def e_18(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The painted number and its word, set in the wall panel RIGHT of the
        # door opening (which now ends at x=376, so the panel is 376..710 and a
        # 543 centre clears both edges). They used to sit at x=566 with the
        # number at 120px, which was the third overlap in this stage: the foot
        # of the numeral landed on the 34px word, and the word then landed under
        # the DOES NOT EXIST stamp at b24. Both are gone now -- the number is
        # 104px and both are inside the 334px panel, and the b24 stamp is a
        # 360px box over the DOOR at x 56..416, which does not reach 493.
        #
        # The pair lives for the rest of the stage, so when the stamp lands at
        # b24 the number is still there -- a denial over the thing it denies.
        D.draw_number(tile, '18', center=(543, 330), color=(242, 238, 226),
                      size=104)
        D.draw_label(tile, 'HANGAR', center=(543, 440), color=(242, 238, 226),
                     size=30)
    els.append(SC.accrue(clock, 22, 26, e_18, kind='shape', eid='e_18'))

    def e_leaf(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE SLIDING LEAF -- the one piece of real mechanism animation in the
        # chapter. Authored COVERING the opening (96..376 x, 392..652 y); a
        # two-keyframe track carries it 400px left, uncovering a dark doorway
        # that was on the wall the whole time.
        #
        # The previous version authored the leaf at x -40..196 -- BESIDE the
        # opening rather than over it -- and gave it SC.enter(dx=-130), which
        # eases an element FROM an offset TO its authored place. That
        # combination slid the panel further left and then right, i.e. it shut
        # the door it was meant to open. The tile is 280x260, 10% of the frame,
        # so the move is clear of the full-bleed test in check_motion_fit too.
        leaf = [(96, 392), (376, 392), (376, 652), (96, 652)]
        PA.fill_poly(tile, leaf, (198, 192, 180), seed=433, value=0.06)
        PA.hand_stroke(d, leaf, INK, 6, closed=True, seed=434, wavelength=120.0)
        for i in range(4):
            x = 130 + i * 66
            PA.hand_stroke(d, [(x, 408), (x, 636)], (162, 156, 146), 4,
                           seed=440 + i, wavelength=90.0)
    _t0 = T(23)
    els.append(SC.layer(clock, 22, e_leaf, j=24, kind='shape', eid='e_leaf',
                        motion=[(_t0, 0, 0, 1.0, 0.0),
                                (_t0 + 0.6, -420, 0, 1.0, 0.0)]))
    # The leaf is live from b22, NOT from b23. Its track keys start at T(23) and
    # _interp_keyframes CLAMPS before the first key, so at b22 it renders at its
    # authored place -- covering the opening. Starting it at b23 instead left the
    # door standing OPEN through b22, then the pale leaf snapped shut at b23
    # onset and slid open again: a close-then-open flicker across the one beat
    # whose whole sentence is "empty hangar door". Now the door is shut at b22
    # and opens on b23 to show the dark empty bay behind it.
    #
    # NO caption at b23: the opening door and the number on the wall ARE the
    # sentence, and b22 is one beat earlier with words on it.

    def e_noexist(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Officially, that hangar is not there." The stamp lands squarely ON
        # the doorway -- over the leaf's resting place and over the dark opening
        # behind it. It is NOT stretched across the building: at [64,236,664,616]
        # the label ran 114..614 at size 52 and its right end sat on the HANGAR
        # word at 566, so the denial and the thing denied were one illegible
        # mass. The box is now 360x290 (11% of the frame, well under the 30%
        # reframe threshold) and centred on the door at 236, which also puts it
        # clear of the 18/HANGAR panel at x>=493.
        D.draw_red_box(tile, [56, 366, 416, 656], color=RED, width=9)
        D.draw_label(tile, 'DOES NOT EXIST', center=(236, 500), color=RED,
                     size=36, outline=INK, outline_w=2)
    els.append(SC.layer(clock, 24, e_noexist, j=25, kind='shape',
                        eid='e_noexist',
                        motion=SC.enter(clock, 24, dx=0, dy=-24, dur=0.45)))
    els.append(cap(24, 364, 692, size=28, fill=RED, max_w=600))
    # The caption at b24 is KEPT even though the stamp is DRAWN, for a stronger
    # reason than duplication: the stamp says the hangar does not exist and the
    # narration says it is not OFFICIALLY there. The denial is the point and the
    # stamp alone loses the official half. It sits on the strip below the red
    # box, which is bare desert.

    def e_nellis(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Nellis Air Force Base runs the site." Written across the apron on
        # the right of the building, which the backdrop has been composing since
        # b22 with a service road and a fence stub -- so this arrives at
        # something instead of into bare desert. v1 painted this beat as its own
        # full-frame playa card with a runway, which repainted 49% of the
        # picture from underneath the stage and was the third-largest reframe in
        # the chapter.
        _runway(d, 980, 486, 1280, H + 20, 70, 220, 445)
        _hangar(d, 1000, 528, 170, 106, 446)
        _hangar(d, 1190, 528, 156, 98, 447)
        D.draw_label(tile, 'NELLIS AFB', center=(1104, 396), color=INK,
                     size=40)
    els.append(SC.layer(clock, 25, e_nellis, j=26, kind='shape',
                        eid='e_nellis',
                        motion=SC.enter(clock, 25, dx=120, dy=0, dur=ARRIVE)))
    # NO caption at b25: the runway and two hangars with NELLIS AFB above them
    # are the sentence.

    # ===================================================================== #
    # STAGE F  b26-b30  "The budget for the site is not public.              #
    #                 In 1989, a man named Bob Lazar spoke.                 #
    #                 He claimed he had worked there.                       #
    #                 He described what was parked inside.                  #
    #                 No employment record of his exists."                   #
    # An INTERIOR: a plain office wall with a floor line. v1 gave each of     #
    # these five beats its own full-frame room (a paper desk, a living room,  #
    # a press hall, a grey void, a filing room), which is five register      #
    # switches in twelve seconds. Here they are all the same room and the    #
    # objects ACCRUE into it: the budget sheet is pinned to the wall at b26  #
    # and stays, the television stands in front of it at b27 and stays, the  #
    # man takes the lectern at b28 and stays, his drawing goes up on the     #
    # wall at b29, and the drawer replaces the television at b30 -- the one  #
    # replace in the stage, between two objects of the same size in the same  #
    # place, which is why it measures under a third of the frame.            #
    # ===================================================================== #
    def f_backdrop(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, W, H], (206, 200, 190), seed=460, value=0.05)
        PA.fill_rect(tile, [0, 420, W, H], (188, 180, 170), seed=461, value=0.07)
        PA.paper_overlay(tile, seed=462)
        SC.title_backdrop(tile, 463, col=(206, 200, 190))
    els.append(SC.stage(clock, 26, f_backdrop, j=31))

    def f_sheet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The budget sheet, ACCRUING on the office wall for the whole stage --
        # it is a document pinned up in a room, and it is the physical proof
        # that this story happens in offices rather than on the playa. The one
        # blacked-out line is the subject; NOT PUBLIC is stamped across it so
        # the beat needs no caption.
        #
        # RESIZED to fill the frame. It used to be a small sheet at (60,120)-
        # (470,430): correct as a thing on a wall, but the critic's eye and my
        # own render both saw the b26 frame as ~85% empty grey -- a timid prop
        # in an empty field. At b26 the sheet is the ONLY subject on screen, so
        # it must dominate. It now spans x -80..520, y 110..600 (a 600x490
        # document), cropped off the LEFT edge so the frame admits the room is
        # bigger than the picture -- the frame-fill canon's own idiom. It still
        # clears the man at b28 (x 522..758) by 2px and the lectern by 46px,
        # so nothing later in the stage collides.
        sheet = [(-80, 110), (520, 110), (520, 600), (-80, 600)]
        PA.fill_poly(tile, sheet, PAPER, seed=464, value=0.05)
        PA.hand_stroke(d, [(0, 110), (520, 110), (520, 600), (-80, 600)],
                       INK, 6, closed=False, seed=465, wavelength=140.0)
        # NO 'BUDGET' heading. It used to sit on the same baseline as a caption
        # 30px away, so the two read as one run of text -- the pile-up defect
        # arrived at from the other direction. The sheet is identified by its
        # ruled lines and the redaction.
        for i in range(6):
            y = 180 + i * 52
            PA.hand_stroke(d, [(-40, y), (360 - (i % 3) * 70, y)],
                           (150, 146, 138), 5, seed=466 + i, wavelength=70.0)
        PA.fill_rect(tile, [-20, 430, 470, 496], INK, seed=470, value=0.04)
        D.draw_label(tile, 'NOT PUBLIC', center=(215, 545), color=RED, size=38,
                     outline=INK, outline_w=2)
    els.append(SC.accrue(clock, 26, 31, f_sheet, kind='shape', eid='f_sheet',
                         motion=SC.enter(clock, 26, dy=-40, dur=ARRIVE)))
    # NO caption at b26: the sheet is DRAWN with NOT PUBLIC across the
    # blacked-out line. The art already says it in the two words that matter.

    def f_tv(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "In 1989, a man named Bob Lazar spoke." The television stands in front
        # of the office wall on the RIGHT of the frame -- the sheet owns the
        # left, the man owns the middle, the television owns the right, so
        # nothing in this stage is ever drawn over anything else.
        tv = [(940, 372), (1220, 372), (1220, 638), (940, 638)]
        PA.fill_poly(tile, tv, (92, 96, 104), seed=471, value=0.07)
        PA.hand_stroke(d, tv, INK, 6, closed=True, seed=472, wavelength=130.0)
        scr = [(966, 396), (1194, 396), (1194, 560), (966, 560)]
        PA.fill_poly(tile, scr, (170, 186, 196), seed=473, value=0.08)
        PA.hand_stroke(d, scr, INK, 5, closed=True, seed=474, wavelength=110.0)
        SC.closeup(d, 1080, 474, 54, 'deadpan', 475, shoulder=0.0)
        d.ellipse([1176, 590, 1200, 614], outline=INK, width=5)
        D.draw_label(tile, '1989', center=(1080, 674), color=RED, size=36,
                     outline=INK, outline_w=2)
        # The face ON the screen is the substitute for a portrait we do not
        # have and must not invent.
    els.append(SC.accrue(clock, 27, 30, f_tv, kind='shape', eid='f_tv',
                         motion=SC.enter(clock, 27, dx=120, dy=0, dur=ARRIVE)))
    els.append(cap(27, 1060, 200, size=30, max_w=520))
    # The caption at b27 is KEPT and is the most important text in the chapter:
    # NOTHING in the art says the name. The set says 1989 and shows a man; the
    # words are what make him Bob Lazar. It sits in the bare wall band at the
    # top, above the set.

    def f_man(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "He claimed he had worked there." He takes the middle of the room at
        # a lectern. At height 440 a standing reach is +-118, so he occupies
        # x 522..758 -- 180px clear of the sheet's right edge at 470 and 182px
        # clear of the television's left edge at 940.
        SC.fullbody(d, 640, 700, 440, pose='standing', expression='deadpan',
                    seed=497)
        lect = [(566, 700), (584, 508), (716, 508), (734, 700)]
        PA.fill_poly(tile, lect, (128, 120, 110), seed=498, value=0.06)
        PA.hand_stroke(d, lect, INK, 6, closed=True, seed=499, wavelength=110.0)
        PA.hand_stroke(d, [(596, 508), (724, 508)], INK, 7, seed=500,
                       wavelength=110.0)
        PA.hand_stroke(d, [(660, 508), (660, 428)], STEEL, 8, seed=502,
                       wavelength=60.0)
        d.ellipse([642, 398, 678, 434], fill=INK)
    els.append(SC.accrue(clock, 28, 31, f_man, kind='character', eid='f_man',
                         motion=SC.enter(clock, 28, dx=0, dy=-26, dur=ARRIVE)))
    # NO caption at b28: the man at a microphone in front of a 1989 television
    # is the sentence, and b27 is one beat earlier with words on it.

    def f_sketch(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "He described what was parked inside." His account, drawn as he draws
        # it, hung on the wall to the RIGHT of the lectern where nothing else in
        # the room is.
        #
        # MOVED from (780,250) to (990,210). At the old centre the disc spanned
        # x 560..1000, y 150..350 -- which put it straight over the man's head
        # (x 604..676, y 260..330), and because f_sketch is composited AFTER
        # f_man it drew the disc's opaque fill across his face. The old comment
        # claimed the disc sat "where nothing else in the room is" and reasoned
        # from the man's right EDGE (758) while ignoring that the disc's box
        # extended far to the LEFT of that edge. The geometry reasoning was
        # wrong, not just the placement. New box x 770..1210 clears the man by
        # 12px and stays above the television (y 372..638); its top (110) clears
        # the title strip (86). Both hands follow it to its new edges.
        cx, cy = 990, 210
        disc = PA.ellipse_pts(cx, cy, 220, 100, n=72)
        PA.fill_poly(tile, disc, (146, 152, 162), seed=503, value=0.07)
        PA.hand_stroke(d, disc, INK, 6, closed=True, seed=504, wavelength=140.0)
        dome = []
        n = 40
        for i in range(n + 1):
            a = math.pi + math.pi * i / n
            dome.append((cx + 100 * math.cos(a), cy - 34 + 70 * math.sin(a)))
        PA.fill_poly(tile, dome + [(cx + 100, cy - 34), (cx - 100, cy - 34)],
                     (226, 228, 230), seed=505, value=0.04, edge=1.2)
        PA.hand_stroke(d, dome, INK, 5, closed=False, seed=506, wavelength=120.0)
        PA.hand_stroke(d, [(cx - 100, cy - 34), (cx + 100, cy - 34)],
                       (108, 114, 120), 5, seed=507, wavelength=100.0)
        # REPLACED the two floating _hand_sketch claws. With nothing connecting
        # them to a body they read as disembodied talons: one hovered over the
        # man's own face, the other floated above the television. A hand only
        # makes sense here as part of a reaching arm, so draw ONE arm from his
        # right shoulder up toward the disc, with the hand at its end. Anchored
        # to fullbody's standing pose (shoulder near (700,470)), the arm reads
        # as "he is indicating the thing he just described" -- which is the line.
        # One idea per frame: the disc is the idea; the arm is the verb.
        _shoulder = (700, 474)
        _elbow = (826, 400)
        _wrist = (938, 330)
        PA.hand_stroke(d, [_shoulder, _elbow], INK, 7, seed=508,
                       wavelength=70.0)
        PA.hand_stroke(d, [_elbow, _wrist], INK, 7, seed=509,
                       wavelength=70.0)
        # The hand at the end of the reach: a small open palm, not a claw.
        d.ellipse([_wrist[0] - 9, _wrist[1] - 7, _wrist[0] + 11,
                   _wrist[1] + 9], fill=(238, 226, 210))
        PA.hand_stroke(d, [(_wrist[0] - 9, _wrist[1] - 7),
                           (_wrist[0] + 11, _wrist[1] - 7),
                           (_wrist[0] + 11, _wrist[1] + 9),
                           (_wrist[0] - 9, _wrist[1] + 9)],
                       INK, 4, closed=True, seed=510, wavelength=40.0)
    els.append(SC.layer(clock, 29, f_sketch, j=30, kind='shape',
                        eid='f_sketch',
                        motion=SC.enter(clock, 29, dy=-34, dur=0.45)))
    # NO caption at b29: the shape he described is the picture, and the caption
    # would only name it.

    def f_drawer(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "No employment record of his exists." The punchline: an open drawer
        # with one dark empty slot. It REPLACES the television -- and it is the
        # only replace in this stage precisely because the two are the same size
        # in the same place, so the pixels that change are one block and not
        # two. v1 also repainted the WHOLE frame here with a fresh fill_rect and
        # paper_overlay, which is 40% of the picture changing for no reason
        # except that the previous card had ended.
        dr = [(940, 372), (1220, 372), (1220, 638), (940, 638)]
        PA.fill_poly(tile, dr, (186, 176, 160), seed=510, value=0.07)
        PA.hand_stroke(d, dr, INK, 7, closed=True, seed=511, wavelength=140.0)
        for i in range(2):
            x0 = 962 + i * 138
            slot = [(x0, 400), (x0 + 116, 400), (x0 + 116, 610), (x0, 610)]
            col = (52, 54, 62) if i == 1 else (226, 206, 158)
            PA.fill_poly(tile, slot, col, seed=512 + i, value=0.06)
            PA.hand_stroke(d, slot, INK, 4, closed=True, seed=516 + i,
                           wavelength=90.0)
        D.draw_label(tile, 'NO RECORD', center=(1080, 500), color=RED, size=30,
                     outline=INK, outline_w=2)
    els.append(SC.layer(clock, 30, f_drawer, j=31, kind='shape',
                        eid='f_drawer',
                        motion=SC.enter(clock, 30, dx=110, dy=0, dur=ARRIVE)))
    els.append(cap(30, 300, 688, size=28, fill=RED, max_w=560))
    # The caption at b30 is KEPT: the drawer shows an EMPTY SLOT, which says
    # "there is nothing here", and the sentence says the one thing the art
    # cannot -- that what is missing is a record of HIM. It sits in the floor
    # band under the sheet, clear of the drawer at x>=940.

    # ===================================================================== #
    # STAGE G  b31-b34  "In 2020, the FBI released its files.                #
    #                 One page stamped with the lake's name.                #
    #                 The fence is still standing there.                    #
    #                 Nobody has ever looked inside."                        #
    # The finale is NIGHT, and it CLOSES THE LOOP: the last frames are the   #
    # same fence on the same playa as b01, now almost black with one red     #
    # light. The chapter's own subject -- that fence -- is what the viewer is #
    # left holding, so nothing here is allowed to cover it for long. The      #
    # documents arrive first, the page replaces them, and then the page gives #
    # way to the wire.                                                       #
    # ===================================================================== #
    def g_backdrop(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, W, H], NIGHT, seed=520, value=0.12)
        PA.fill_rect(tile, [0, HZ - 6, W, H], NIGHT_G, seed=521, value=0.12)
        PA.paper_overlay(tile, seed=522)
        # lit course on the title band so the hardcoded-INK title reads on the
        # night card (see scene_common.title_backdrop). Called before any fill
        # that could cover it.
        SC.title_backdrop(tile, 134, col=(84, 92, 118))
    els.append(SC.stage(clock, 31, g_backdrop, j=35))

    def g_stack(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "In 2020, the FBI released its files." The stamp says RELEASED and
        # NOT the year -- the YEAR is in the caption instead, because the beat
        # is the date as much as the release and printing 2020 in both places is
        # duplication.
        _file_stack(d, 640, 400, 210, 523, n=6, stamp='RELEASED')
    els.append(SC.layer(clock, 31, g_stack, j=32, kind='shape', eid='g_stack',
                        motion=SC.enter(clock, 31, dy=54, dur=ARRIVE)))
    els.append(cap(31, 640, 604, size=30, dark=True, max_w=700))

    def g_page(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "One page stamped with the lake's name." ONE page, and it is a third
        # the size of the previous 1360x550 sheet: 520x360 is 20% of the frame,
        # so it can arrive over the stack without being a new image. It
        # REPLACES the stack -- two documents at once in the same frame is the
        # pile-up -- and the single typed line GROOM LAKE is picked out among
        # the redactions with a finger under it.
        sheet = [(380, 200), (900, 200), (900, 560), (380, 560)]
        PA.fill_poly(tile, sheet, PAPER, seed=524, value=0.05)
        PA.hand_stroke(d, sheet, INK, 6, closed=True, seed=525, wavelength=150.0)
        for i in range(7):
            y = 240 + i * 44
            if i == 3:
                continue
            PA.hand_stroke(d, [(410, y), (410 + (360 if i % 2 else 260), y)],
                           (150, 146, 138), 4, seed=526 + i, wavelength=70.0)
        y = 240 + 3 * 44
        D.draw_label(tile, 'GROOM LAKE', center=(620, y), color=INK, size=42)
        PA.fill_poly(tile, [(720, 540), (762, 420), (804, 540)],
                     (222, 180, 150), seed=534, value=0.05)
        PA.hand_stroke(d, [(720, 540), (762, 420), (804, 540)], INK, 5,
                       closed=False, seed=535, wavelength=70.0)
    els.append(SC.layer(clock, 32, g_page, j=33, kind='shape', eid='g_page'))
    # NO caption at b32: the page is DRAWN with GROOM LAKE on it in 42px ink
    # under a pointing finger. The words are already the picture.

    def g_fence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "The fence is still standing there." Back to b01's shot -- same playa,
        # same line of posts, same framing -- but at night and in near-black
        # wire, which is the only way the line of it reads as STILL STANDING
        # after everything that has happened in between. It REPLACES the page:
        # the fence has to be the only thing in the frame for that to land, and
        # the page leaving (20%) plus the wire arriving (5%) measures 25%.
        _fence(d, -60, FENCE_BASE, W + 60, 176, 545, n_posts=12,
               post_col=(40, 42, 54), rail_col=(40, 42, 54))
        lx, ly = 760, 386
        for rr, col in ((80, (66, 34, 36)), (46, (140, 56, 48)), (20, RED)):
            d.ellipse([lx - rr, ly - rr, lx + rr, ly + rr], fill=col)
    els.append(SC.layer(clock, 33, g_fence, j=35, kind='shape', eid='g_fence'))
    els.append(cap(33, 400, 214, size=32, dark=True, max_w=560))
    # The caption at b33 is KEPT: the fence at night says "it is still here"
    # and not the two things that make it a fact -- STILL, and standing THERE,
    # unmoved, after everything. The red light sits at x=760 and the caption is
    # at x=400, in the empty sky on the other side of it.

    def g_never(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Nobody has ever looked inside." The presenter, awed, cropped by the
        # LEFT edge so he is inside the shot rather than standing beside it,
        # and the 'never' bubble that is the last thing on screen. The fence is
        # still there behind both of them -- it was placed at b33 and nothing in
        # this beat covers it, which is the point: the wall is still up.
        SC.fullbody(d, 175, 700, 450, pose='standing', expression='awed',
                    seed=546, ink=(236, 228, 208))
        # CREAM INK, and it is not optional here. G is a night stage (NIGHT 20 /
        # NIGHT_G 24) and the default INK limbs are L=24 -- twenty-four against
        # twenty. At full res the arms and legs all but vanished and the
        # character read as a floating head; the cream override is the same one
        # the night pilot at b16 gets, and STYLE_CANON's rule is that the
        # character is drawn cream on dark backgrounds and dark on light ones.
        #
        # The bubble sits DIRECTLY ABOVE him, not off to the right, and that is
        # forced by draw_bubble: it clamps the tail apex to the bubble's own x
        # range (`tx = min(max(tail_to[0], x0+14), x1-14)`) and always hangs the
        # tail off the BOTTOM edge. So a bubble parked at x=470 could put its
        # apex no further left than 484, which is 309px from a character at
        # x=175 -- the 300px needle in mid-air this comment used to describe.
        # At (118, 170) the clamp resolves to 175 and the apex lands on his
        # mouth at (175, 318). Head top is y=257, bubble bottom y1=233, so the
        # bubble clears the head by 24px instead of sitting on it.
        D.draw_bubble(tile, 'never', (118, 170), tail_to=(175, 318))
    els.append(SC.layer(clock, 34, g_never, j=35, kind='character',
                        eid='g_never',
                        motion=SC.enter(clock, 34, dx=96, dur=0.5)))
    # NO caption at b34: the bubble is DRAWN reading "never" and it is the last
    # image in the chapter. A caption under it would be the fourteenth piece of
    # text on a frame that already says it.

    return SC.finish(els, TITLE, clock, title_seed=29)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet_2.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent_2.mp4'))
