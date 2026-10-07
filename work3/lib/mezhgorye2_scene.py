"""mezhgorye2_scene -- the PERSISTENT-STAGE rebuild of chapter 2.

WHY THIS FILE EXISTS. mezhgorye_scene.py (v1) was built on "one full-frame card
per beat, and each card paints its own whole frame". Its own `card(i, j, ...)`
helper opened an exclusive window and the draw closure filled
background-to-subject every time, so NOTHING survived from one beat to the
next: thirty repaints of the whole 1280x720 picture in 76.6 seconds, a new
image every ~2.5s. The viewer complaint this rebuild exists to answer is
"every sentence has a cut with a completely new image... there are no
animations or changes to the visual."

THE MODEL HERE. Seven PERSISTENT STAGES instead of thirty short cards, grouped
on the narration's own acts rather than on beats:

    A  b01-b05   the mountain, the sealed door, the name, the frozen valley
    B  b06-b09   the 1930s plans on the wall, then the prisoners digging
    C  b10-b12   the hand drill, the abandoned drift, the unmarked lids
    D  b13-b16   the buried complex in section, 120 km, the chambers
    E  b17-b21   the fortress above, the slit, the rail, the road that stops
    F  b22-b26   the page forgets it: CLOSED, two rumours, nothing on paper
    G  b27-b30   the fortress still standing, and the door nobody has opened

The frame repaints its backdrop seven times in 76s instead of thirty, and
inside a stage the art ACCUMULATES: a layer that arrives STAYS until the stage
turns over (SC.accrue). The viewer gets one recognisable place to look while
the next thing is added to it.

ONE REGISTER PER STAGE, WHICH IS THE HARD PART HERE. v1 could change register
freely because every beat was a fresh card; a stage cannot, because the
backdrop is painted once. So where a stage's beats span two looks in v1, the
change is made INSIDE the stage by an arriving mass rather than by a card swap:
    - stage A ends winter, so the SNOW GROUND ACCRUES over the green field at
      b04 -- the sky stays sky, only the ground turns white;
    - stage B opens on a drafting sheet, so the sheet is a panel that ARRIVES
      on the rock face at b06 and is replaced by the digging at b08;
    - stage D cuts underground at b15, so the cutaway is a rock mass that
      rises over the section at b15 -- and it stops at y=104, which also keeps
      the sky strip (and therefore a readable title) above it;
    - stage F's stage IS the page. The two rumours are two panels ACCRUING
      side by side on that page -- the nuclear doodle left, the table right --
      and at b26 a paper wash WIPES both, because "no document has ever
      confirmed any of it" is the sentence that takes them off the record.
    - stage G ends underground at b29 and back outside at b30, so each is a
      mass that arrives over the snow.

TWO RULES THAT TOOK THE PILOT TWO ROUNDS TO LEARN; both are kept here.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Accruing everything is also wrong.
   Two elements that occupy the SAME part of the frame must REPLACE (SC.layer)
   or they stack into a pile-up -- the sheet at b06 is replaced by the b07
   drawing, the b13 section is replaced by the flatter b14 section that makes
   room for the 120 km ruler, the b17 fortress is replaced by the b18 wall, the
   b19 tunnel is replaced by the b20 bore, the ghost page is replaced by the
   CLOSED form. Art that is scenery accrues; art that carries words, and two
   things that share a region, do not.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces motion at a rate the
   reference does not have (the reference is 83% still) and every moving frame
   trips the picture-change counter -- which is WORSE than the churn it was
   meant to fix. So exactly twelve arrivals move, each 0.45-0.9s, each on a
   SMALL subject: the steel door, the presenter, the stamp, the drill bit, the
   coat on its stake, the ruler, the cold coming through the slit, the
   CLOSED stamp slamming down, the rumour doodle, the little fortress. No
   backdrop ever moves. The rock at b10 is a separate STATIC layer precisely
   because a moving full-bleed layer slides its own top edge and uncovers the
   page (v1's documented bug); only the drill carries the track.

CAPTIONS. Eleven of thirty beats (37%), each timed to the beat whose words it
carries. A caption is DROPPED whenever the drawn art already prints the words:
'1930s', 'CLOSED', '120 KILOMETRES', 'NO ROAD', 'NUCLEAR?', 'MAGADAN
REGION' and the drawn name are all already on the picture, and repeating them
in a caption is the text-on-text pile-up the pilot hit. No two captioned beats
are adjacent. scene_common.caption() picks the fill by measured WCAG contrast
against the paper the caption actually lands on, and the two drawn labels that
could not clear 4.5:1 in RED ('NO ROAD', 'no door') were moved to INK --
legibility on the grey wall beats outranks the one-red-accent rationing, and a
red label at 1.6:1 is a label nobody reads.

Run:  python lib/mezhgorye2_scene.py --preview --video
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
import mezhgorye_scene as MG     # art primitives + palette, reused not copied

# --- palette / geometry, reused from v1 verbatim ---------------------------
INK = MG.INK
SKY = MG.SKY
SNOW = MG.SNOW
SNOW_SH = MG.SNOW_SH
FIELD = MG.FIELD
FIELD_D = MG.FIELD_D
ROCK = MG.ROCK
ROCK_D = MG.ROCK_D
EARTH = MG.EARTH
EARTH_D = MG.EARTH_D
CONCRETE = MG.CONCRETE
CONC_D = MG.CONC_D
STEEL = MG.STEEL
STEEL_D = MG.STEEL_D
DARK = MG.DARK
BLUE_W = MG.BLUE_W
RED = MG.RED
RED_L = MG.RED_L
LAMP = MG.LAMP
PAPER = MG.PAPER
BLUE_INK = MG.BLUE_INK
HZ = MG.HZ
W, H = MG.W, MG.H

TITLE = MG.TITLE
BEATS = MG.BEATS
SEG = MG.SEG
TITLE_BACKDROP = MG.TITLE_BACKDROP

# --- art primitives, reused from v1 verbatim -------------------------------
_exterior = MG._exterior
_winter = MG._winter
_underground = MG._underground
_page = MG._page
_rock_face = MG._rock_face
_mass = MG._mass
_ridgeline = MG._ridgeline
_snow_cap = MG._snow_cap
_mountain = MG._mountain
_archway = MG._archway
_steel_door = MG._steel_door
_bunker = MG._bunker
_chamber = MG._chamber
_bore = MG._bore
_rail = MG._rail
_fortress = MG._fortress
_worker = MG._worker
_hand_drill = MG._hand_drill
_coil_icon = MG._coil_icon
_tank_icon = MG._tank_icon
_bunk_icon = MG._bunk_icon
_table_and_chairs = MG._table_and_chairs
_mushroom_cloud = MG._mushroom_cloud
_stamp = MG._stamp
_ghost_lines = MG._ghost_lines

# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and it becomes the picture changing every sample,
# which is the defect this whole rebuild exists to remove. The one exception is
# the drill bit at 0.9s, which is v1's: a drill stroke is slower than a door.
ARRIVE = 0.5


# ---------------------------------------------------------------------------
# STRUCTURE HELPERS -- why these exist, and what they are NOT.
# ---------------------------------------------------------------------------
# The blind critic called the whole film flat vector, and the per-beat pigment
# measurement agreed: every one of this chapter's thirty beats measured a median
# 24px-tile luma std of 2-5 (the flat cluster), never the 8+ of a painted frame.
# Root cause, confirmed by measuring a synthetic strip (bare fill 2.83; add 26
# thin contour bands 8.71; add a masonry/panel grid 21.07): the median is set by
# the LARGEST shapes in the frame, and v2paint's paint drift inside one flat
# mass is deliberately subtle (a +-15% wash on a grey fill is a couple of levels
# at 24px). So a single big smooth ROCK mountain or EARTH slab -- no matter how
# many levers and rivets sit on top of it -- drags the median down. The fix is
# NOT more paint constants (v2paint already works) and NOT noise (the brief
# forbids faking it). It is COMPOSITION: break every large void into MANY small
# outlined, edge-rich forms -- strata, courses, panels, ribs, scree, contour
# bands -- so a typical 24px tile contains an ink edge. That is exactly how the
# reference draws a built subject (fortknox's ~40 gold slabs score 53 for this
# reason), and it is what these helpers are for.
#
# Every helper here is deterministic (explicit seed), draws only inside a box or
# along a supplied polyline so it never disturbs layout, and returns nothing.
# They are drawn AFTER a mass and BEFORE any text/caption so they never fight
# the type or the title strip (which engine3 stamps last).

def _strata(d, y_top, y_bot, col, seed, n=None, wobble=22, x0=-60, x1=1340,
            width=5, broken=True):
    """Broken contour bands across a rock/earth mass -- bedding planes.

    The reference's mountains and cutaway sections are built from stacked
    strata, not one smooth wash. Each band is a slow low-frequency wave so it
    reads as rock bedding. `broken=True` splits each band into several short
    segments with gaps: a CONTINUOUS full-width band reads as a ruled line
    ruled across the sky (the first draft did exactly that and looked like
    lined paper), while broken segments read as bedding. Callers must pass a
    box that lies INSIDE the mass -- strata that run past its silhouette cross
    the sky and are the same defect one band up.
    """
    if n is None:
        n = max(3, int((y_bot - y_top) / 26.0))
    for k in range(n):
        u = k / float(max(1, n - 1))
        y = y_top + (y_bot - y_top) * u
        pts = []
        m = 9
        for i in range(m + 1):
            t = i / float(m)
            x = x0 + (x1 - x0) * t
            pts.append((x, y + wobble * math.sin(t * 4.2 + k * 0.8 + seed * 0.01)))
        if broken:
            # three or four segments per band, each with its own seed
            segs = 3 + (k % 2)
            for sgi in range(segs):
                a = int(m * sgi / float(segs))
                b = int(m * (sgi + 1) / float(segs))
                if b - a >= 2:
                    PA.hand_stroke(d, pts[a:b + 1], col, width,
                                   seed=seed + k * 7 + sgi, wavelength=140.0,
                                   vary=0.25)
        else:
            PA.hand_stroke(d, pts, col, width, seed=seed + k, wavelength=160.0,
                           vary=0.25)


def _facets(d, x0, y0, x1, y1, col_a, col_b, seed, n=22, rmin=34, rmax=90,
            edges=3, ink_w=4):
    """Scattered COMPACT angular shaded PLANES over a large mass -- low-poly.

    Each facet is a small convex-ish polygon whose vertices all lie within
    `r` of ONE scattered centre point, so it stays a compact chip instead of a
    shard stretching across the frame (the first draft randomised every vertex
    independently and produced glass-shard spaghetti). Neighbouring facets
    differ in value across an INK keyline, so a typical 24px tile spans a fill,
    an ink edge and a second fill -- high local std with no per-pixel noise.
    Drawn over a base mass it reads as faceted rock or wind-carved snow.
    """
    def rnd(state):
        s = (state * 1103515245 + 12345) & 0x7fffffff
        return s, (s >> 8 & 0xffff) / 65535.0

    st = seed
    for k in range(n):
        st, fx = rnd(st)
        st, fy = rnd(st)
        st, fr = rnd(st)
        st, fa = rnd(st)
        px = x0 + (x1 - x0) * fx
        py = y0 + (y1 - y0) * fy
        r = rmin + (rmax - rmin) * fr
        m = edges + (k % 2)                 # 3..4 sided chips
        pts = []
        for j in range(m):
            st, fj = rnd(st)
            a = fa * 6.283 + j * (6.283 / m)
            # vertices sit at 0.6r..1.0r from the CENTRE, never scattered
            rr = r * (0.6 + 0.4 * fj)
            pts.append((px + rr * math.cos(a), py + rr * math.sin(a) * 0.82))
        col = col_a if (k % 2) else col_b
        PA.fill_poly(PA.img_of(d), pts, col, seed=seed + k, value=0.05, edge=1.4)
        PA.hand_stroke(d, pts, INK, ink_w, closed=True, seed=seed + 40 + k,
                       wavelength=60.0)


def _flank_strata(d, cx, peak_y, base_y, col, seed, n=9, spread=680, width=5,
                  x0=-60, x1=1340):
    """Contour bands that hug a mountain's concave flank.

    A mountain silhouette is high in the middle and falls to `base_y` at both
    edges, so a STRAIGHT horizontal band leaves the rock near the edges and
    crosses the sky -- which is the ruled-line defect again. This curves each
    band down toward the edges by a parabola centred on `cx`, so the bands
    follow the flank and stay under the silhouette across the whole width.
    `spread` is the half-width over which the band has dropped to `base_y`.
    """
    for k in range(n):
        u = k / float(max(1, n - 1))
        y_mid = peak_y + (base_y - peak_y) * u
        pts = []
        m = 17
        for i in range(m + 1):
            x = x0 + (x1 - x0) * (i / float(m))
            dx = (x - cx) / float(spread)
            drop = (base_y - y_mid) * (dx * dx)     # 0 at centre, max at edges
            pts.append((x, y_mid + drop))
        segs = 4
        for sgi in range(segs):
            a = int(m * sgi / float(segs))
            b = int(m * (sgi + 1) / float(segs))
            if b - a >= 2:
                PA.hand_stroke(d, pts[a:b + 1], col, width,
                               seed=seed + k * 9 + sgi, wavelength=150.0,
                               vary=0.25)


def _courses(d, x0, y0, x1, y1, col, seed, rows=None, cols=None, width=4,
             stagger=True):
    """A masonry / panel grid: horizontal courses plus short vertical joints.

    This is the fortknox-density primitive for BUILT subjects (concrete walls,
    the drafting sheet, the gate, chamber faces). Staggered verticals read as
    masonry; aligned ones read as panelling, so `stagger` picks per subject.
    """
    if rows is None:
        rows = max(2, int((y1 - y0) / 44.0))
    if cols is None:
        cols = max(2, int((x1 - x0) / 68.0))
    rh = (y1 - y0) / float(rows)
    cw = (x1 - x0) / float(cols)
    for r in range(rows + 1):
        y = y0 + r * rh
        PA.hand_stroke(d, [(x0, y), (x1, y)], col, width, seed=seed + r,
                       wavelength=140.0, vary=0.20)
    for r in range(rows):
        y = y0 + r * rh
        off = (cw * 0.5 if (stagger and r % 2) else 0.0)
        c = 0
        x = x0 + off - cw
        while x < x1 + cw:
            PA.hand_stroke(d, [(x, y), (x, y + rh)], col, width,
                           seed=seed + 200 + r * 40 + c, wavelength=110.0,
                           vary=0.20)
            x += cw
            c += 1


def _scree(d, x0, y0, x1, y1, col, seed, n=26, rmin=4, rmax=13):
    """Scattered small angular stones over a ground or scree slope.

    Terrain reads as terrain when it is littered; a smooth coloured field reads
    as vector. Each stone is a tiny closed ANGULAR outline (not an ellipse --
    the ellipse version read as bubbles), so at 24px it is a crisp ink speck
    that lifts the local tile std.
    """
    rng_seed = seed
    for k in range(n):
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        fx = (rng_seed >> 7 & 0xffff) / 65535.0
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        fy = (rng_seed >> 7 & 0xffff) / 65535.0
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        fr = (rng_seed >> 7 & 0xffff) / 65535.0
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        fa = (rng_seed >> 7 & 0xffff) / 65535.0
        x = x0 + (x1 - x0) * fx
        y = y0 + (y1 - y0) * fy
        r = rmin + (rmax - rmin) * fr
        # an angular chip: 5 points around a jittered radius, no ellipse
        pts = []
        m = 5
        for i in range(m):
            a = fa * 6.283 + i * (6.283 / m)
            rr = r * (0.7 + 0.5 * ((i * 37 + k) % 7) / 6.0)
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a) * 0.72))
        PA.hand_stroke(d, pts, col, 3, closed=True, seed=seed + k,
                       wavelength=40.0)


def _ribs(d, x0, y0, x1, y1, col, seed, n=8, width=5):
    """Parallel ribs across a tunnel bore / pipe interior -- support arches.

    The bore is the biggest smooth void in the underground beats. Ribs across
    it read as a lined tunnel and give the tile grid high-frequency ink.
    """
    for k in range(n + 1):
        u = k / float(n)
        x = x0 + (x1 - x0) * u
        PA.hand_stroke(d, [(x, y0), (x, y1)], col, width, seed=seed + k,
                       wavelength=120.0, vary=0.20)


def _speckle(d, x0, y0, x1, y1, col, seed, n=18, width=3):
    """Short tick marks -- scree shadow, tool marks, hand-drawn hatching."""
    rng_seed = seed
    for k in range(n):
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        fx = (rng_seed >> 7 & 0xffff) / 65535.0
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        fy = (rng_seed >> 7 & 0xffff) / 65535.0
        x = x0 + (x1 - x0) * fx
        y = y0 + (y1 - y0) * fy
        PA.hand_stroke(d, [(x, y), (x + 8, y + 5)], col, width,
                       seed=seed + k, wavelength=40.0)


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
    # STAGE A  b01-b05  "Beneath this mountain lies a secret city. No       #
    #                 outsider has ever reached the tunnels. This is        #
    #                 Mezhgorye... It sits above Magadan, in frozen hills.  #
    #                 The winters here are brutal, and long."                #
    # One mountain held across five beats. The mountain IS the hook, so it #
    # is the backdrop: sky strip, the big cropped mass, and the dark       #
    # archway cut into it. The steel door ARRIVES at b02 into the archway.  #
    # The name is DRAWN at b03 (the reveal is the drawn word, not a caption#
    # that repeats it). The valley TURNS TO SNOW at b04: a white mass      #
    # accrues over the green, which is the one register change inside the   #
    # stage -- so it is an arriving element, not a card swap. The presenter #
    # stands right from b01 and swaps expression at b05 (brutal winters).   #
    # ===================================================================== #
    # THE SNOW IS PAINTED BY THE STAGE, NOT ARRIVED AT b04. It used to be a
    # beat-04 accrual -- a full-width white mass down to y=780 -- which the
    # gate measured as a 39% full-frame swap INSIDE the stage: a cut to a new
    # picture on the beat that says "frozen hills". The chapter is a winter
    # chapter; the stage is born white. Register changes that ARE the stage
    # belong in the stage.
    def a_back(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 5, sky=SKY, ground=SNOW)
        _mountain(d, 560, HZ + 30, 620, 118, 6)
        # The mountain is the single largest mass in the frame and it was one
        # smooth grey wash -- exactly the "a few big smooth shapes with dead
        # space" the critic named. DENSE FACETS overlay it: many small angular
        # planes in three stepped rock values, each keylined INK, so a typical
        # tile spans fill / ink / fill. Density matters more than chip size --
        # 26 sparse chips left half the pale left flank flat, so the passes are
        # dense and use clearly darker rock values so they read as terrain
        # rather than as pale confetti. Drawn before the archway covers them.
        _facets(d, 20, 200, 700, 470, (150, 154, 160), (116, 120, 128),
                210, n=48, rmin=24, rmax=54)
        _facets(d, 700, 200, 1300, 470, (150, 154, 160), (116, 120, 128),
                260, n=42, rmin=24, rmax=54)
        _facets(d, 20, 120, 430, 210, (238, 240, 244), (198, 206, 216),
                400, n=22, rmin=22, rmax=46)
        _flank_strata(d, 560, 220, HZ + 18, ROCK_D, 320, n=9, spread=780)
        # a few soft broken cloud bands in the clear sky, above and below the
        # b01/b04 caption band at y=95 so they never collide with the type.
        _strata(d, 30, 66, (216, 226, 236), 480, n=3, wobble=12, width=4)
        _strata(d, 150, 196, (216, 226, 236), 500, n=3, wobble=12, width=4)
        # a big dark archway low in the mountain, the "secret" the hook names.
        # h=360 (not 380) so the arch's apex lands at y=116, clear of the
        # persistent title band; h=380 pushed it to y=96, close enough that
        # the 7px keyline grazed the band.
        _archway(d, 560, HZ + 30, 300, 360, 8)
        # the frozen valley, part of the world from the first frame
        _ridgeline(d, 500, 470, 20, col=SNOW_SH, width=5)
        _ridgeline(d, HZ + 10, 150, 21, col=(198, 210, 222), width=5)
        valley = [(-60, 700), (-60, 596), (200, 560), (520, 542), (860, 560),
                  (1160, 610), (1340, 654), (1340, 780), (-60, 780)]
        _mass(d, valley, SNOW, 22, width=6)
        # wind-carved snow: shallow facets + contour bands, all light-value so
        # the valley stays the pale register it is in every winter beat.
        _facets(d, -40, 560, 660, 720, (250, 250, 252), (226, 232, 238),
                340, n=20, rmin=30, rmax=74)
        _facets(d, 660, 560, 1330, 720, (250, 250, 252), (226, 232, 238),
                380, n=18, rmin=30, rmax=74)
        # contour bands run the whole height of the valley snow, up over the
        # crest: the y 456-528 strip between the mountain foot and the valley
        # crest measured the flattest band in the frame (row mean 8-9).
        _strata(d, 468, 716, (198, 210, 222), 240, n=11, wobble=14, width=4)
        _scree(d, 60, 500, 1240, 716, (186, 198, 210), 250, n=34)
    els.append(SC.stage(clock, 1, a_back, j=6))

    # The presenter arrives on b01 and stands through the whole stage. He is
    # small at the right edge and cropped by it -- the line is about the
    # mountain, not about him, but four seconds with no character reads as
    # "nothing is happening."
    def a_presenter_a(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 1090, 715, 440, pose='pointing',
                    expression='awed', seed=9)
    _bu, _aa, _au = SC.expr_swap(clock, 5, 'awed', 'worried', until_j=6)
    els.append(E3.E('a_presenter_a', 'character', a_presenter_a,
                    at=clock.at('b01', 0), until=_bu,
                    motion=SC.enter(clock, 1, dx=-90, dy=0, dur=ARRIVE)))

    # At b05 the same figure changes expression on "brutal, and long" -- two
    # elements at the same position, the first ending where the second starts.
    def a_presenter_b(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 1090, 715, 440, pose='pointing',
                    expression='worried', seed=9)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))
    # cy 128 -> 95. At 128 the caption ran straight across the crown of the dark
    # mountain: rows y=90-110 measure a uniform pale sky (spread 24-27) but from
    # y=114 down the dome's dark mass begins (spread jumps to 218 and the median
    # falls to 0 at y=130). So "Beneath this mountain lies a secret city." had
    # its middle words -- "mountain lies" -- drawn in INK-black ON the near-black
    # dome, at 1.36:1. Eye-checked at 2x and unreadable; this is the user's
    # complaint verbatim. The straddle gate (check_straddle) catches exactly this
    # class: one fill cannot serve both halves of the surface the glyphs sit on.
    #
    # cy=95 puts the whole 32-36px line inside the clear sky band (y 79-111),
    # just above the crown and just below the title strip.
    els.append(cap(1, 640, 95, size=36))

    # ---- the sealed door, arriving into the archway at b02 ---------------- #
    # MOVING. The door dropping into the archway is the one arrival worth
    # animating in this stage: "No outsider has ever reached the tunnels" is
    # about this door, and it arriving IS the sentence.
    def a_door(tile, fw, fh):
        _steel_door(ImageDraw.Draw(tile), 560, HZ + 30 - 150, 200, 300, 13,
                    handle=False)
    els.append(SC.accrue(clock, 2, 6, a_door, kind='shape',
                         motion=SC.enter(clock, 2, dx=0, dy=64, dur=ARRIVE)))
    # NO caption at b02. The door is drawn shut with its wheel struck through;
    # the words "no outsider has ever reached" would only name what the image
    # already states.

    # ---- b03  the name, DRAWN across the sky ------------------------------ #
    # The reveal IS this word. A caption repeating it would be text-on-text.
    def a_name(tile, fw, fh):
        D.draw_label(tile, 'MEZHGORYE', center=(640, 236), color=INK, size=88)
    els.append(SC.accrue(clock, 3, 6, a_name, kind='shape',
                         motion=SC.enter(clock, 3, dx=0, dy=-40, dur=0.45)))

    # ---- b04  a drift banked against the archway -------------------------- #
    # BOUNDED, and the whole point of the change. This used to be the full
    # valley turning white -- a full-width mass to y=780 -- which is a new
    # picture on the beat that says "frozen hills". Now the valley is white
    # from the first frame (see a_back) and b04 adds what actually changes the
    # beat: snow BANKED against the foot of the archway, a low band across the
    # bottom third, plus two mounds. ~19% of frame height, under the 30% that
    # makes the gate call it a cut.
    def a_snow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        bank = [(-60, 690), (120, 648), (360, 634), (600, 646), (840, 668),
                (1080, 686), (1340, 692), (1340, 780), (-60, 780)]
        _mass(d, bank, (250, 250, 252), 22, width=6)
        _mass(d, [(250, 646), (318, 596), (386, 646)], (250, 250, 252), 23,
              width=5)
        _mass(d, [(820, 668), (884, 622), (948, 670)], (250, 250, 252), 24,
              width=5)
    # DRIFTING, slowly across b04-b05: snow that moves a little for two beats
    # is the cheapest honest motion in the chapter, and the chapter's motion
    # budget had no continuous track in it at all before this.
    els.append(SC.accrue(clock, 4, 6, a_snow, kind='shape', eid='a_snowbank',
                         motion=SC.drift(clock, 4, 6, dx=0, dy=-26)))
    # cy 128 -> 95, same reason and same measurement as b01: at 128 this caption
    # ran across the dark mountain crown and "above Magadan," was INK-black on
    # near-black (1.36:1, eye-checked unreadable at 2x). The clear sky band is
    # y 90-110, so 95 keeps the whole line above the crown.
    els.append(cap(4, 640, 95, size=32))

    # ---- b05  the gale ---------------------------------------------------- #
    # Long shallow wind curves, all leaning the same way. Wind drawn as short
    # dashes reads as rain; these read as a gale across a valley.
    def a_wind(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(7):
            y = 560 + k * 26
            pts = []
            for i in range(9):
                u = i / 8.0
                pts.append((-40 + (W + 120) * u,
                            y + 20 * math.sin(u * 4.0 + k * 0.9)))
            PA.hand_stroke(d, pts, (176, 190, 202), 5, seed=29 + k,
                           wavelength=150.0)
    els.append(SC.accrue(clock, 5, 6, a_wind))
    # NO caption at b05. The white valley, the wind and the presenter's shifted
    # expression carry "brutal, and long" together.

    # ===================================================================== #
    # STAGE B  b06-b09  "Stalin ordered it built in the 1930s. The design   #
    #                 came from Soviet engineers. Gulag prisoners did most   #
    #                 of the digging. North Korean workers were brought in   #
    #                 too."                                                #
    # The world here is the dig face -- a rock wall. The PLAN is pinned to   #
    # that wall for b06-b07 (a drafting sheet that arrives, then is         #
    # re-stamped), and at b08 the sheet's window ENDS and the prisoners     #
    # take the frame. The rock face underneath never changes, so the stage  #
    # is one place: the wall being dug, with the drawing on it. Two things #
    # that share the centre replace (sheet -> workers), which is why the    #
    # sheet's window closes at b08 rather than the workers being added on   #
    # top of it.                                                           #
    # ===================================================================== #
    def b_face(tile, fw, fh):
        _rock_face(tile, 57)
        # The dig face is a full-frame ROCK wall and _rock_face gives it only
        # four cracks -- one of the largest flat masses in the chapter. Dense
        # facets turn it into broken rock face, and the extra fracture strokes
        # read as the split stone the diggers are working.
        d = ImageDraw.Draw(tile)
        _facets(d, -40, 110, 700, 720, (146, 150, 156), (108, 112, 120),
                620, n=44, rmin=26, rmax=60)
        _facets(d, 700, 110, 1330, 720, (146, 150, 156), (108, 112, 120),
                660, n=40, rmin=26, rmax=60)
    els.append(SC.stage(clock, 6, b_face, j=10))

    # ---- b06  the plan, pinned to the wall --------------------------------- #
    # A drafting sheet panel: grey card, faint grid, the bunker sketched in
    # pencil. The GEOMETRY is drawn (mountain + bunker); the words are not,
    # because the b06 caption supplies "Stalin / 1930s" and drawing "1930s"
    # as well would be the same words twice.
    def b_sheet_v1(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [150, 128, 780, 396], (206, 214, 222), seed=40,
                     value=0.05, edge=2.4)
        PA.hand_stroke(d, [(150, 128), (780, 128), (780, 396), (150, 396)],
                       INK, 6, closed=True, seed=41, wavelength=150.0)
        for x in range(160, 780, 56):        # faint drafting grid
            PA.hand_stroke(d, [(x, 132), (x, 392)], (192, 202, 210), 2,
                           seed=42, wavelength=180.0, vary=0.10)
        for y in range(140, 396, 56):
            PA.hand_stroke(d, [(154, y), (776, y)], (192, 202, 210), 2,
                           seed=43, wavelength=180.0, vary=0.10)
        _mountain(d, 460, 340, 240, 190, 44, col=(150, 164, 178))
        _bunker(d, 460, 300, 108, 45, decks=3, deck_h=34, tunnel_dy=[96],
                lamps=False)
        # The sheet is the SUBJECT of this beat and it was a mostly blank card
        # with one small sketch parked in it -- the "small subject marooned in
        # an empty field" the critic names. It now carries what a real drafting
        # sheet carries: a centre line through the section, dimension arrows
        # across the width and down the height, a hatched ground band, and a
        # ruled title block in the lower right. All thin INK/pencil, so the
        # sheet still reads as drawing, not as a chart.
        PA.hand_stroke(d, [(465, 134), (465, 390)], (150, 160, 172), 3,
                       seed=45, wavelength=140.0)          # centre line
        for yy in (232, 288):                               # horizontal dims
            PA.hand_stroke(d, [(196, yy), (724, yy)], (128, 138, 150), 3,
                           seed=46 + yy, wavelength=140.0)
            PA.hand_stroke(d, [(196, yy - 8), (196, yy + 8)], (128, 138, 150),
                           3, seed=50 + yy, wavelength=50.0)
            PA.hand_stroke(d, [(724, yy - 8), (724, yy + 8)], (128, 138, 150),
                           3, seed=54 + yy, wavelength=50.0)
        PA.hand_stroke(d, [(706, 172), (706, 356)], (128, 138, 150), 3,
                       seed=58, wavelength=140.0)           # vertical dim
        for k in range(7):                                   # hatched ground
            hx = 178 + k * 34
            PA.hand_stroke(d, [(hx, 384), (hx + 26, 356)], (140, 150, 162), 3,
                           seed=60 + k, wavelength=50.0)
        # the title block, ruled off in the lower right of the sheet
        PA.hand_stroke(d, [(560, 300), (772, 300), (772, 388), (560, 388)],
                       (96, 106, 118), 4, closed=True, seed=70, wavelength=110.0)
        PA.hand_stroke(d, [(560, 344), (772, 344)], (96, 106, 118), 3,
                       seed=71, wavelength=110.0)
        for k in range(4):                                   # scribbled entries
            PA.hand_stroke(d, [(568, 314 + k * 0), (700 + k * 12, 322)],
                           (96, 106, 118), 3, seed=72 + k, wavelength=60.0)
        PA.hand_stroke(d, [(566, 362), (716, 362)], (96, 106, 118), 3,
                       seed=78, wavelength=60.0)
    els.append(SC.accrue(clock, 6, 10, b_sheet_v1, kind='shape',
                         motion=SC.enter(clock, 6, dx=0, dy=-36, dur=ARRIVE)))
    els.append(cap(6, 640, 664, size=32))

    # ---- b07  the same sheet, stamped GIPRONIKOM -------------------------- #
    # REPLACES b06's sheet rather than accruing onto it: two drawings of the
    # same plan in the same rectangle is the object-on-object pile-up. The
    # stamp is the reveal -- it names the design bureau, which is all b07 says.
    def b_sheet_v2(tile, fw, fh):
        b_sheet_v1(tile, fw, fh)
        d = ImageDraw.Draw(tile)
        _stamp(d, 645, 300, 190, 88, -7, 51)
        D.draw_label(tile, 'GIPRONIKOM', center=(645, 300), color=INK,
                     size=24)
    els.append(SC.layer(clock, 7, b_sheet_v2, kind='shape', eid='b_sheet_stamp'))
    # NO caption at b07. The GIPRONIKOM stamp IS the words. No motion either:
    # b06's panel already slid in, and sliding the same rectangle again on the
    # next beat would make a replace read as a second animation.

    # ---- b08-b09  the prisoners, filling the width ------------------------- #
    # The sheet's window has closed (it ran to the end of b07), so the workers
    # own the frame here. Big enough to fill it -- the line of hunched figures
    # is the subject now.
    def b_workers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for i, x in enumerate((-40, 250, 540, 830)):
            _worker(d, x, 700, 300, 60 + i, coat=(80, 88, 100))
    els.append(SC.accrue(clock, 8, 10, b_workers, eid='b_workers_a'))
    # cy 132 -> 180. At 132 the caption straddled the top edge of the pale
    # building: rows y=40..120 measure luma ~120 (dark sky) and rows y=130..220
    # measure ~213 (pale wall), so a caption centred at 132 sat half on each and
    # its dark-ink fill disappeared into the dark half -- 'Gulag prisoners did
    # most of the digging' was half-unreadable at 1280x720. The background
    # resolver cannot rescue this: whichever register it picks, the other half
    # of the glyphs is unreadable, because the glyphs genuinely straddle an
    # edge. 180 is wholly inside the pale band, where INK is correct.
    els.append(cap(8, 640, 180, size=32))
    # NO caption at b09. A closer second line of workers arrives and the
    # presenter joins them -- "workers were brought in too" is exactly what
    # more workers arriving says, and b08 already carried the reveal.

    def b_more_workers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for i, x in enumerate((960, 1150, 1330)):
            _worker(d, x, 700, 290, 90 + i, coat=(70, 78, 90))
        # The presenter, cropped by the top edge and looking down at the line.
        # He is inset at the upper right, clear of the workers' heads, because
        # a worker-sized copy of him would turn the presenter into just another
        # body in the line.
        SC.fullbody(d, 1160, 320, 210, pose='standing', expression='skeptic',
                    seed=99)
    els.append(SC.accrue(clock, 9, 10, b_more_workers, kind='character'))

    # ===================================================================== #
    # STAGE C  b10-b12  "They cut the rock with hand drills. Many of the   #
    #                 workers never left the mountain. The dead were        #
    #                 buried inside the rock."                             #
    # The rock face is the backdrop for all three beats and never changes.  #
    # ON TOP of it: the drill (b10), then the drift of snow with the single #
    # coat on its stake (b11), then the niche of unmarked lids (b12). Each #
    # is an ACCRUING layer in its own region of the face, so the stage reads #
    # as one wall being worked rather than three separate cards.            #
    #                                                                         #
    # THE DRILL IS ITS OWN MOTION LAYER, NOT THE ROCK. engine3 composites a  #
    # moving element by cropping it to its ink and pasting at ink-origin +  #
    # offset; a FULL-BLEED background that moves slides its own top edge and #
    # uncovers the paper page (v1's documented bug). So the rock is static   #
    # and only the drill -- the thing being driven -- carries the track,     #
    # along its own shaft axis so the two gripping hands stay still.         #
    # ===================================================================== #
    def c_face(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _winter(tile, 101)
        # The cut rock face the drill is going into. This is a DARK mass, not a
        # pale one: at s=190 the drill was a small brown T lost against a pale
        # winter field, and the beat read as an empty frame. A dark face gives
        # the drill something to bite into and the frame a subject.
        face = [(-60, 300), (240, 236), (560, 214), (900, 228), (1340, 268),
                (1340, 780), (-60, 780)]
        _mass(d, face, (86, 82, 92), 102, width=7)
    els.append(SC.stage(clock, 10, c_face, j=13))

    # ---- b10  the hand drill, actually cutting --------------------------- #
    # MOVING. "They cut the rock with hand drills" is the only line in the
    # chapter that describes something happening, so it gets the arrival.
    # _hand_drill's 4th arg is a SCALE, and the primitive's own docstring says
    # "drawn LARGE and cropped" -- at s=190 the crosspiece was 350px on a 1280
    # frame and the drill read as a stray mark. At s=380 it is the subject.
    def c_drill(tile, fw, fh):
        _hand_drill(ImageDraw.Draw(tile), 640, 400, 380, 103)
    els.append(SC.accrue(clock, 10, 11, c_drill,
                         motion=SC.enter(clock, 10, dx=0, dy=30, dur=0.58)))
    # NO caption at b10. The drill, its bit buried in the rock and its dust
    # falling, is the sentence.

    # ---- b11  the empty drift, one coat on a stake ------------------------ #
    def c_drift(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        drift = [(-60, 720), (-60, 616), (200, 580), (520, 562), (860, 580),
                 (1160, 630), (1340, 674), (1340, 780), (-60, 780)]
        _mass(d, drift, SNOW, 104, width=6)
    els.append(SC.accrue(clock, 11, 13, c_drift, eid='c_drift'))

    # MOVING, and small: a single coat on a stake is the emptiest object in
    # the chapter and the one worth sliding in. No footprints -- the absence
    # is the subject, so nothing may be drawn where they would be.
    def c_coat(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(640, 610), (640, 452)], (104, 84, 60), 9,
                       seed=106, wavelength=70.0)
        coat = [(596, 452), (684, 452), (694, 556), (586, 556)]
        PA.fill_poly(tile, coat, (92, 80, 72), seed=107, value=0.08, edge=1.8)
        PA.hand_stroke(d, coat, INK, 6, closed=True, seed=108, wavelength=80.0)
        PA.hand_stroke(d, [(596, 462), (584, 500)], INK, 5, seed=109,
                       wavelength=50.0)
        PA.hand_stroke(d, [(684, 462), (696, 500)], INK, 5, seed=110,
                       wavelength=50.0)
    els.append(SC.accrue(clock, 11, 13, c_coat, eid='c_coat'))
    # No motion here, deliberately. The drill already moves in this stage, and a
    # stake settling by 40px is the least informative move in the chapter -- it
    # reads the same standing still, and holding the beat still is worth more
    # than a twelfth entrance.
    els.append(cap(11, 400, 240, size=32))

    # ---- b12  four plain lids in the rock, no names ----------------------- #
    def c_lids(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        niche = [(380, 310), (860, 310), (860, 486), (380, 486)]
        PA.fill_poly(tile, niche, (128, 120, 106), seed=112, value=0.08,
                     edge=2.0)
        PA.hand_stroke(d, niche, INK, 7, closed=True, seed=113, wavelength=130.0)
        for i in range(4):
            x0 = 396 + i * 114
            lid = [(x0, 326), (x0 + 100, 326), (x0 + 100, 466), (x0, 466)]
            PA.fill_poly(tile, lid, CONC_D, seed=120 + i, value=0.07, edge=1.8)
            PA.hand_stroke(d, lid, INK, 6, closed=True, seed=130 + i,
                           wavelength=90.0)
            PA.hand_stroke(d, [(x0 + 12, 314), (x0 + 128, 314)], INK, 4,
                           seed=140 + i, wavelength=60.0)
            PA.hand_stroke(d, [(x0 + 12, 460), (x0 + 128, 460)], INK, 4,
                           seed=150 + i, wavelength=60.0)
            d.ellipse([x0 + 62, 384, x0 + 74, 396], fill=INK)   # no name plate
    els.append(SC.accrue(clock, 12, 13, c_lids))
    # The presenter, cropped by the right edge, looking at the lids. A closeup
    # rather than a full body: this is the beat where the chapter turns, and a
    # small standing figure beside four lids reads as set dressing.
    def c_presenter(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 1146, 356, 138, 'grim', 159)
    els.append(SC.accrue(clock, 12, 13, c_presenter, kind='character', eid='c_presenter'))
    # NO caption at b12. Four lids with blank plates and a grim face carry it.

    # ===================================================================== #
    # STAGE D  b13-b16  "The tunnels run for a hundred kilometres. Some      #
    #                 accounts say a hundred and twenty. Wide chambers      #
    #                 branch off on both sides. Power, water, and housing    #
    #                 were all underground."                               #
    # The stage is a CUTAWAY: sky band, the green hill on top, earth below. #
    # The hill is the backdrop; the bunker inside it accrues at b13. At b14  #
    # the section is REPLACED by a flatter one (same primitive, cap_h=170)   #
    # so the red 120 km ruler gets its own band at the bottom instead of     #
    # hanging off the frame edge -- two drawings of the same structure in    #
    # the same rectangle is the object-on-object pile-up. At b15 the view    #
    # cuts UNDERGROUND: a rock mass rises over the section, stopping at      #
    # y=130, which also keeps a sky strip (and so a readable title) above it.#
    # ===================================================================== #
    def d_section(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], SKY, seed=161, value=0.05)
        PA.fill_rect(tile, [0, 150, W, H], EARTH, seed=162, value=0.09)
        PA.paper_overlay(tile, seed=163)
        # TOP EDGE RULE: nothing in a card may start above y=104 -- engine3
        # draws the persistent title over the top of every finished frame.
        hill = [(-60, 156), (200, 128), (520, 112), (900, 120), (1180, 140),
                (1340, 158), (1340, 158), (-60, 158)]
        _mass(d, hill, FIELD, 164, width=6)
        PA.hand_stroke(d, [(-60, 156), (200, 128), (520, 112), (900, 120),
                           (1180, 140), (1340, 158)], INK, 7, seed=165,
                       wavelength=170.0)
    els.append(SC.stage(clock, 13, d_section, j=17))

    # ---- b13  THE HERO: the buried complex in section --------------------- #
    # tunnel_dy is [200, 290] rather than v1's [250, 340]: that drops the
    # lower bore clear of the bottom of the frame and leaves a clean band of
    # earth at y~690 for the caption, which at v1's spacing sat on the bore.
    def d_bunker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # cap_y 356 puts the dome's apex at 132 (356 - 430*0.52), i.e. ~16px of
        # earth over the blast cap, which is what "buried" has to look like.
        _bunker(d, 640, 356, 430, 166, decks=4, deck_h=76,
                tunnel_dy=[200, 290], lamps=True)
        for k in range(5):                       # depth marks, left margin
            y = 356 + k * 76
            PA.hand_stroke(d, [(36, y), (92, y)], INK, 4, seed=170 + k,
                           wavelength=60.0)
    els.append(SC.accrue(clock, 13, 17, d_bunker, eid='d_bunker'))
    els.append(cap(13, 640, 700, size=32, max_w=860))

    # ---- b14  the ruler: 120 km ------------------------------------------- #
    # REPLACES the b13 section. Same hill (it is the backdrop), flatter cap.

    # MOVING, and small: the ruler is a band of numbers, not a backdrop. This
    # is the chapter's one measurement beat, so the measurement arriving is the
    # only arrival here.
    def d_ruler(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        y = 706
        PA.hand_stroke(d, [(120, y), (1160, y)], RED, 8, seed=187,
                       wavelength=180.0)
        for k in range(11):
            x = 120 + k * 104
            PA.hand_stroke(d, [(x, y - 14), (x, y + 14)], RED, 5,
                           seed=190 + k, wavelength=60.0)
        D.draw_arrow(tile, (120, y), (1160, y), color=RED, width=8, head=36)
        D.draw_number(tile, '120', center=(392, 686), color=RED, size=64)
        D.draw_label(tile, 'KILOMETRES', center=(760, 686), color=INK,
                     size=34)
    els.append(SC.accrue(clock, 14, 17, d_ruler, kind='shape',
                         motion=SC.enter(clock, 14, dx=0, dy=-34, dur=0.45)))
    # NO caption at b14. A 130px red "120" over "KILOMETRES" IS the sentence;
    # a caption under it repeated the number and stacked text on text.

    # ---- b15  the cut underground ------------------------------------------ #
    # A rock mass ARRIVES over the section instead of the card being replaced.
    # It stops at y=130 so the sky strip survives and the title stays legible
    # on it, and it is EARTH rather than EARTH_D so the "chambers" label below
    # clears 4.5:1 against it.
    def d_deep(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-60, 150), (240, 132), (560, 126), (900, 134),
                            (1340, 152), (1340, 214), (-60, 214)], EARTH_D,
                     seed=201, value=0.07, edge=2.0)
    els.append(SC.accrue(clock, 14, 17, d_deep, eid='d_strata'))

    def d_chambers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        y = 326
        bore = [(-60, y - 82), (1340, y - 82), (1340, y + 82), (-60, y + 82)]
        PA.fill_poly(tile, bore, DARK, seed=202, value=0.03, edge=1.8)
        PA.hand_stroke(d, [(-60, y - 82), (1340, y - 82)], INK, 7, seed=203,
                       wavelength=180.0)
        PA.hand_stroke(d, [(-60, y + 82), (1340, y + 82)], INK, 7, seed=204,
                       wavelength=180.0)
        _chamber(d, 190, y, 280, 250, 205, door_side=1)
        _chamber(d, 1090, y, 280, 250, 206, door_side=-1)
        # the third chamber's floor runs down INTO the bore, which is also what
        # a chamber off this tunnel is supposed to look like.
        _chamber(d, 640, 204, 250, 188, 207, door_side=1)
        D.draw_label(tile, 'chambers', center=(640, 466), color=INK, size=34)
    els.append(SC.accrue(clock, 15, 17, d_chambers, kind='shape',
                         eid='d_chambers'))
    # NO caption at b15. The drawn "chambers" label over three of them IS the
    # words; a caption beside it repeated the label.

    # ---- b16  power, water, housing ---------------------------------------- #
    # REPLACES the b15 chambers: the same bore with three service chambers on
    # it. Two chamber-rows in the same rectangle would stack.
    def d_services(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-60, 470), (1340, 470), (1340, 534), (900, 548),
                            (400, 548), (-60, 534)], EARTH_D, seed=210,
                     value=0.08, edge=2.0)
        PA.hand_stroke(d, [(-60, 534), (400, 548), (900, 548), (1340, 534)],
                       INK, 7, seed=211, wavelength=170.0)
        for i, x in enumerate((250, 640, 1030)):
            _chamber(d, x, 616, 250, 240, 220 + i, door_side=1)
        _coil_icon(d, 250, 616, 84, 230)
        _tank_icon(d, 640, 616, 84, 231)
        _bunk_icon(d, 1030, 616, 80, 232)
        SC.fullbody(d, 90, 714, 320, pose='pointing', expression='awed',
                    seed=233)
    els.append(SC.accrue(clock, 16, 17, d_services, kind='character'))
    # NO caption at b16, and this one is forced, not chosen: b17 is captioned
    # and no two captioned beats may sit next to each other. It also loses
    # nothing -- a coil, a tank and a bunk are three pictograms of the sentence,
    # and the b13 caption has already named the length and the depth.

    # ===================================================================== #
    # STAGE E  b17-b18  "Above ground, they raised a stone fortress. Thick  #
    #                 walls, narrow slits, no doors out."                   #
    # TWO beats, one place: the snowy ridge with the fortress built on it.   #
    # b18 pushes in on one wall of that same fortress -- the close-up keeps   #
    # the building's own coping and snow cap along the top, so it reads as   #
    # nearer, not elsewhere. v1 made b18 a full-frame concrete card that     #
    # replaced the fortress; the gate measured that as a 52% full-frame     #
    # swap INSIDE a stage, which is the "cut every sentence" defect wearing  #
    # a stage's clothes.                                                     #
    # ===================================================================== #
    def e_ridge(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 239, sky=SKY, ground=SNOW)
        ridge = [(-60, 640), (240, 590), (640, 560), (1040, 596), (1340, 640),
                 (1340, 780), (-60, 780)]
        _mass(d, ridge, ROCK, 240, width=7)
        _snow_cap(d, ridge[:5], 600, 241)
        # The fortress IS the stage now. b17 and b18 are the same wall at two
        # distances, so it is painted once, here, and never repainted: b18 is a
        # detail opening in a wall that is already standing.
        _fortress(d, 640, 596, 900, 420, 242, slits=6)
    els.append(SC.stage(clock, 17, e_ridge, j=19))

    # ---- b17  the fortress above ground ------------------------------------ #
    els.append(cap(17, 640, 690, size=32))

    # ---- b18  one slit, and no door anywhere ------------------------------ #
    # A PUSH-IN ON THE SAME FORTRESS, not a new building. v1 replaced the
    # fortress with an abstract concrete slab + a lone triangle, which shared
    # nothing with b17 and read as a cut to a new place (the gate measured a 52%
    # full-frame swap; the frames confirmed it -- a bare slab where a fortress
    # had been). This redraws the SAME fortress much larger so it runs off both
    # sides and the bottom -- the viewer is closer to the wall they just saw,
    # with its masonry courses and arrow slits still the same language -- and
    # then opens ONE splayed embrasure in it with "no door" beside it. Same
    # place, closer, one new fact.
    def e_wall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # No wall is drawn here. The stage already carries the fortress, and
        # redrawing it wider was the full-frame swap this beat was meant not
        # to be. What arrives is the DETAIL: one embrasure, cut into the wall
        # that is already standing.
        # the one big embrasure, cut deep into the near wall
        sx, sy = 640, 470
        slit = [(sx - 30, sy - 165), (sx + 30, sy - 165), (sx + 74, sy + 165),
                (sx - 74, sy + 165)]
        PA.fill_poly(tile, slit, (46, 44, 48), seed=266, value=0.03, edge=1.6)
        PA.hand_stroke(d, slit, INK, 8, closed=True, seed=267, wavelength=110.0)
        # INK, not RED: a red label on this concrete measures 2.5:1, and the
        # whole point of the beat is that the viewer reads "no door".
        D.draw_label(tile, 'no door', center=(1000, 660), color=INK, size=46)
    els.append(SC.accrue(clock, 18, 19, e_wall, eid='e_wall'))

    # MOVING, and small: the cold coming through the slit, sliding in from the
    # embrasure and out to the right. The wall itself does NOT move -- a moving
    # full-bleed layer slides its own top edge and uncovers the page.
    def e_cold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        sx, sy = 640, 470
        for k in range(5):
            y = sy - 110 + k * 56
            pts = [(sx + 60, y), (sx + 300, y - 26 + k * 6),
                   (sx + 540, y - 44 + k * 10)]
            PA.hand_stroke(d, pts, BLUE_W, 7, seed=270 + k, wavelength=150.0)
    els.append(SC.accrue(clock, 18, 19, e_cold, eid='e_cold',
                         motion=SC.enter(clock, 18, dx=-150, dy=0, dur=0.6)))
    # NO caption at b18. One slit in a very thick wall, with "no door" drawn
    # beside it, is the sentence; a caption under the label repeated it.

    # ===================================================================== #
    # STAGE E2  b19-b21  "The only way in was by rail. A narrow gauge line   #
    #                   ran deep inward. No road ever reached the front     #
    #                   gate."                                              #
    # A SEPARATE stage from E, and that is the whole point of the split. The #
    # rail is a different place from the fortress wall, so the move between  #
    # them is a STAGE change -- a backdrop swap, which the gate correctly    #
    # forgives -- rather than a subject swap inside a stage that never       #
    # changed, which it does not.                                           #
    # Inside this stage the three beats are ONE journey: the mine mouth at    #
    # b19 is drawn, the side-on bore is REVEALED onto it at b20 (13.5% of the #
    # frame changes -- a detail arriving, not a new picture), and the rail   #
    # that stops at a cliff at b21 is the end of the same line. The presenter #
    # sits on the sleepers for both b19 and b20.                            #
    # ===================================================================== #
    def e2_railhall(tile, fw, fh):
        # The persistent world for the rail beats: dark rock overhead and a
        # snow floor at the very bottom, so the tunnel never full-wipes the
        # frame and the winter register survives the change of place.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DARK, seed=279, value=0.06)
        PA.paper_overlay(tile, seed=280)
        SC.title_backdrop(tile, 1279, col=(98, 94, 106))
        floor = [(-60, 700), (240, 686), (640, 678), (1040, 686), (1340, 700),
                 (1340, 780), (-60, 780)]
        _mass(d, floor, (206, 214, 224), 2795, width=6)
    els.append(SC.stage(clock, 19, e2_railhall, j=21))

    # ---- b19+b20  the only way in: the rail, held across BOTH beats -------- #
    # These two beats were two separate full-frame tunnel cards (b19 a dark
    # mine-mouth, b20 a lighter side-on bore) and the gate measured them as
    # back-to-back 96% and 78% repaints -- the exact "cut every sentence" the
    # user complained about, sitting inside a stage that never changed. They are
    # ONE idea ("the only way in was by rail") seen from two angles, so they are
    # now ONE card held across both beats. The b19 mouth is drawn first and the
    # b20 side-on bore is REVEALED onto it (a second accrual, not a wipe), with
    # the mine-mouth's dark arch still framing the left of the b20 frame. b19's
    # presenter sits on the sleepers and stays for both.
    def e_tunnel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        mouth = 520
        # The mine mouth cut into the rail hall's dark rock. No full-frame fill
        # here -- the stage already painted the dark; this beat only adds the
        # mouth, so it reveals onto the hall instead of replacing it.
        PA.fill_poly(tile, [(-60, 86), (mouth - 150, 86), (mouth - 190, 690),
                            (-60, 690)], (52, 50, 54), seed=281, value=0.05,
                     edge=1.6)
        PA.hand_stroke(d, [(-60, 86), (mouth - 150, 86)], INK, 8, seed=2815,
                       wavelength=150.0)
        _bore(d, mouth + 130, 400, W + 40, 300, 400, 180, 282, lamps=2)
        _rail(d, 380, 690, 300, mouth + 150, 400, 60, 283, ties=9)
    els.append(SC.accrue(clock, 19, 21, e_tunnel, eid='e_tunnel'))
    # The b20 side-on bore, REVEALED onto the b19 mouth (arrives, then stays).
    def e_bore_detail(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bore(d, -40, 400, 900, 380, 300, 210, 290, lamps=2)
        _rail(d, 60, 560, 220, 900, 380, 54, 291, ties=10)
        # SNOW, not INK: this is the b20 bore, the one dark register in the
        # chapter, and the rock behind this label measures a median luminance of
        # ~40 -- INK (24,24,28) sits at essentially the same value, so the glyphs
        # read as an unreadable smudge with no lift from the outline either.
        # SNOW (238,241,244) measures 6.0:1 against that rock on the real render,
        # and because it is not INK, draw_label gives it the default black
        # keyline, which is what keeps it off the lighter rock further left.
        D.draw_label(tile, 'the only line', center=(1050, 610), color=SNOW,
                     size=36)
    els.append(SC.accrue(clock, 20, 21, e_bore_detail, kind='shape', eid='e_bore'))
    # MOVING, and small: the presenter sitting on the sleepers, sliding in and
    # settling. He holds for both beats now.
    def e_sitter(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 250, 660, 400, pose='sitting',
                    expression='deadpan', seed=284)
    els.append(SC.accrue(clock, 19, 21, e_sitter, kind='character',
                         motion=SC.enter(clock, 19, dx=-80, dy=0, dur=ARRIVE)))
    els.append(cap(19, 980, 660, size=32, dark=True))

    # ---- b21  the road that stops at a cliff ------------------------------ #
    # The last beat of the rail stage and a deliberate step back OUTSIDE: the
    # narrator has followed the rail in, and b21 shows the road that never got
    # there. Because it leaves the tunnel, this beat DOES change the register
    # -- bright sky over the dark hall -- and that change is the point ("no
    # road ever reached the front gate"). It sits at the end of the stage so
    # the one full-frame change in E2 is the exit from the tunnel, not a cut
    # between two things the viewer was supposed to compare. The road, the
    # cliff and "NO ROAD" are unchanged from v1 and still land on snow.
    def e_noroad(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], SKY, seed=299, value=0.05)
        PA.paper_overlay(tile, seed=300)
        # The ground stops dead at x=900 and falls away. Snow, matching stage.
        ground = [(-60, 300), (240, 268), (560, 252), (900, 268), (900, 780),
                  (-60, 780)]
        _mass(d, ground, (222, 230, 238), 301, width=7)
        road = [(-60, 330), (300, 306), (620, 292), (880, 306), (880, 366),
                (620, 352), (300, 366), (-60, 390)]
        PA.fill_poly(tile, road, (146, 140, 132), seed=302, value=0.07, edge=2.0)
        PA.hand_stroke(d, [(-60, 330), (300, 306), (620, 292), (880, 306)],
                       INK, 6, seed=303, wavelength=170.0)
        PA.hand_stroke(d, [(-60, 390), (300, 366), (620, 352), (880, 366)],
                       INK, 6, seed=304, wavelength=170.0)
        for k in range(7):
            u = k / 6.0
            x = -20 + u * 880
            y = 330 + (306 - 330) * u
            PA.hand_stroke(d, [(x, y), (x + 60, y + 2)], SNOW, 5,
                           seed=305 + k, wavelength=60.0)
        drop = [(900, 268), (980, 420), (940, 560), (900, 780)]
        _mass(d, drop, (188, 200, 212), 306, width=6)
        PA.hand_stroke(d, [(880, 262), (880, 372)], RED, 11, seed=307,
                       wavelength=60.0)
        # INK, not RED: RED on this snow measures 2.6:1, which is a signpost
        # nobody can read from the back row.
        D.draw_label(tile, 'NO ROAD', center=(500, 560), color=INK, size=76)
    els.append(SC.stage(clock, 21, e_noroad, j=22))
    # NO caption at b21. "NO ROAD" is drawn at 76px across the empty half of
    # the frame, and the road that visibly stops at nothing says the rest.

    # ===================================================================== #
    # STAGE F  b22-b26  "Then the country decided to forget it. The site    #
    #                 was formally closed, on paper. Rumours spread of a    #
    #                 nuclear bunker down there. Others say a refuge for     #
    #                 the leadership. No document has ever confirmed it."   #
    # THE STAGE IS THE PAGE. v1 gave b22 and b23 and b26 a bare-paper card #
    # each; here that page is the persistent backdrop for five beats, and   #
    # the two rumours ACCRUE onto it as two panels side by side -- the      #
    # nuclear doodle left, the empty table right -- because they are two    #
    # claims competing for the same record, not two consecutive pictures.   #
    # At b26 a paper wash WIPES both, because "no document has ever         #
    # confirmed any of it" is the sentence that takes them off the file.     #
    # ===================================================================== #
    def f_page(tile, fw, fh):
        _page(tile, 309)
    els.append(SC.stage(clock, 22, f_page, j=27))

    # ---- b22  the page forgets it ------------------------------------------ #
    # The road and the cliff, one shade off the paper -- present, gone.
    def f_ghost(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _ghost_lines(d, [(-60, 330), (300, 306), (620, 292), (880, 306)], 310)
        _ghost_lines(d, [(-60, 390), (300, 366), (620, 352), (880, 366)], 311)
        _ghost_lines(d, [(900, 268), (980, 420), (940, 560), (900, 780)], 312)
        D.draw_label(tile, 'NO ROAD', center=(500, 560), color=(214, 208, 194),
                     size=76)
        SC.fullbody(d, 1080, 700, 470, pose='shrug', expression='deadpan',
                    seed=313)
    els.append(SC.accrue(clock, 22, 23, f_ghost, kind='character'))
    # NO caption at b22. The road and the cliff are still there and almost
    # gone, and the presenter shrugs at them; "the country decided to forget
    # it" is what a page with a ghost on it already says.

    # ---- b23  the CLOSED stamp -------------------------------------------- #
    # REPLACES the ghost: a form with most of its lines blanked, then the
    # stamp. Two documents in the same rectangle is the pile-up.
    def f_form(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(6):
            y = 150 + k * 66
            PA.hand_stroke(d, [(160, y), (1120, y)], (216, 210, 196), 4,
                           seed=320 + k, wavelength=150.0)
    els.append(SC.accrue(clock, 23, 27, f_form, eid='f_form'))

    # MOVING, and small: the stamp slamming down is the beat. INK for the word
    # (RED on paper measures 2.9:1); the stamp's own box stays RED, which is
    # what makes it read as a stamp rather than as type.
    def f_stamp(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _stamp(d, 640, 246, 700, 208, -8, 330)
        D.draw_label(tile, 'CLOSED', center=(640, 246), color=INK, size=96)
    els.append(SC.accrue(clock, 23, 27, f_stamp, kind='shape',
                         motion=SC.enter(clock, 23, dx=0, dy=56, dur=0.45)))
    # NO caption at b23. "CLOSED" is stamped across the middle of the page at
    # 120px. That is the word.

    # ---- b24  rumour one: the nuclear doodle, struck out ------------------ #
    # The panel is (120,114,106), not v1's darker wall, so the label on it
    # clears 4.5:1 against INK.
    def f_nuclear_panel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [180, 396, 560, 636], (120, 114, 106), seed=340,
                     value=0.07, edge=2.0)
        PA.hand_stroke(d, [(180, 396), (560, 396), (560, 636), (180, 636)],
                       INK, 7, closed=True, seed=341, wavelength=150.0)
    els.append(SC.accrue(clock, 24, 27, f_nuclear_panel, kind='shape',
                         eid='f_nuclear_panel'))

    # MOVING, and small: the doodle arriving on the panel it is drawn on. The
    # panel underneath stays still, so nothing full-bleed ever moves.
    def f_rumour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _mushroom_cloud(d, 370, 552, 104, 357, col=RED_L)
        D.draw_label(tile, 'NUCLEAR?', center=(370, 430), color=INK, size=34)
        # half of it struck out -- the rumour is denied, not deleted
        PA.hand_stroke(d, [(250, 498), (490, 608)], INK, 13, seed=360,
                       wavelength=140.0)
        PA.hand_stroke(d, [(490, 498), (250, 608)], INK, 13, seed=361,
                       wavelength=140.0)
    els.append(SC.accrue(clock, 24, 27, f_rumour, kind='shape', eid='f_rumour',
                         motion=SC.enter(clock, 24, dx=0, dy=-44, dur=0.5)))
    els.append(cap(24, 370, 676, size=30))
    # KEEP the b24 caption: the panel says "NUCLEAR?" and strikes it out, but
    # only the narrator says the rumours SPREAD and that they were down there.

    # ---- b25  rumour two: the empty table, no one in it -------------------- #
    def f_refuge_panel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [720, 396, 1100, 636], (120, 114, 106), seed=370,
                     value=0.07, edge=2.0)
        PA.hand_stroke(d, [(720, 396), (1100, 396), (1100, 636), (720, 636)],
                       INK, 7, closed=True, seed=371, wavelength=150.0)
        _table_and_chairs(d, 910, 556, 330, 220)
        D.draw_label(tile, 'REFUGE?', center=(910, 430), color=INK, size=34)
    els.append(SC.accrue(clock, 25, 27, f_refuge_panel, kind='shape'))
    # NO caption at b25. The second panel ACCRUES beside the first -- two claims
    # on one page, which is what "others say" means -- so this beat needs no
    # words of its own and must not have any, or it would sit next to b24's.

    # ---- b26  a wash of paper, and nothing on it --------------------------- #
    # REPLACES both panels with the page they were drawn on. The panels are
    # wiped rather than deleted: the beat is that the record has nothing left
    # on it, and the presenter is left standing in the cleared space.
    def f_wash(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [180, 396, 560, 636], PAPER, seed=391, value=0.05)
        PA.fill_rect(tile, [720, 396, 1100, 636], PAPER, seed=392, value=0.05)
        PA.hand_stroke(d, [(180, 396), (560, 396), (560, 636), (180, 636)],
                       (222, 216, 202), 5, closed=True, seed=393,
                       wavelength=150.0)
        PA.hand_stroke(d, [(720, 396), (1100, 396), (1100, 636), (720, 636)],
                       (222, 216, 202), 5, closed=True, seed=394,
                       wavelength=150.0)
        SC.fullbody(d, 640, 730, 360, pose='shrug', expression='deadpan',
                    seed=395)
        # xy=(925,...), not 980: the bubble is max text width + 2*BUBBLE_PAD
        # wide (273+44=317), so at 980 its right edge landed at 1297 -- 17px
        # past the frame, and "paper" sat 5px off the right edge. draw_bubble
        # has no frame clamp (unlike SC.caption). 925 leaves a 38px gap.
        D.draw_bubble(tile, 'nothing on paper', xy=(300, 500),
                      tail_to=(470, 590), font_size=34, max_w=460)
    els.append(SC.accrue(clock, 26, 27, f_wash, kind='character'))
    # NO caption at b26, and this one is forced as well as chosen: b27 is the
    # next captioned beat and no two captioned beats may be adjacent. The beat
    # does not lose anything -- the SPEECH BUBBLE reads "nothing on paper" in
    # the art, which is the sentence, and a caption under it would be the same
    # words a third time on a page that is supposed to be blank.

    # ===================================================================== #
    # STAGE G  b27-b30  "The stone fortress still stands above it. Snow      #
    #                 buries that gate for months. The tunnels are still    #
    #                 down there, unchanged. And no outsider has ever gone   #
    #                 in."                                                 #
    # The snowy rock face is the backdrop. The fortress accrues on it, then  #
    # the gate and the drift that buries it, then the view cuts UNDER the    #
    # hill for the tunnel, and finally comes back out to the buried door.    #
    # Each of those is a MASS arriving over the last, which is what keeps    #
    # this a place rather than four cards.                                   #
    # ===================================================================== #
    def g_winter(tile, fw, fh):
        _winter(tile, 429)
    els.append(SC.stage(clock, 27, g_winter, j=29))

    def g_cliff(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        cliff = [(-60, 120), (300, 110), (700, 124), (1000, 114), (1340, 122),
                 (1340, 780), (-60, 780)]
        _mass(d, cliff, ROCK, 430, width=7)
        _snow_cap(d, cliff[:5], 136, 431)
        for k in range(6):
            y = 180 + k * 96
            pts = []
            for i in range(7):
                u = i / 6.0
                pts.append((140 + 900 * u, y + 18 * math.sin(u * 5 + k)))
            PA.hand_stroke(d, pts, ROCK_D, 5, seed=440 + k, wavelength=120.0)
    els.append(SC.accrue(clock, 27, 29, g_cliff, eid='g_cliff'))

    # MOVING, and small: the fortress is the last thing that gets built in the
    # film, so it arrives rather than pops.
    def g_fortress(tile, fw, fh):
        _fortress(ImageDraw.Draw(tile), 700, 285, 340, 150, 450, slits=4,
                  wall_only=True)
    els.append(SC.accrue(clock, 27, 29, g_fortress, eid='g_fortress',
                         motion=SC.enter(clock, 27, dx=0, dy=-48, dur=0.55)))

    def g_label(tile, fw, fh):
        D.draw_label(tile, 'STILL STANDING', center=(214, 214), color=INK,
                     size=40)
    els.append(SC.accrue(clock, 27, 29, g_label, kind='shape', eid='g_label'))
    els.append(cap(27, 980, 618, size=32, max_w=520))

    # ---- b28  the drift buries the gate ------------------------------------ #
    def g_gate(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # A gate block standing on the ridge: bounded, so the cliff the stage
        # already painted keeps showing either side of it.
        wall = [(392, 322), (888, 322), (888, 596), (392, 596)]
        _mass(d, wall, CONCRETE, 460, width=7)
        for i in range(3):
            PA.hand_stroke(d, [(404, 386 + i * 62), (876, 386 + i * 62)],
                           CONC_D, 4, seed=461 + i, wavelength=150.0)
        for i in range(5):
            x = 440 + i * 100
            sl = [(x - 14, 350), (x + 14, 350), (x + 14, 432), (x - 14, 432)]
            PA.fill_poly(tile, sl, (46, 44, 48), seed=470 + i, value=0.03,
                         edge=1.2)
            PA.hand_stroke(d, sl, INK, 4, closed=True, seed=480 + i,
                           wavelength=50.0)
        drift = [(300, 700), (300, 616), (470, 566), (700, 548), (930, 578),
                 (1000, 640), (1000, 780), (300, 780)]
        _mass(d, drift, SNOW, 490, width=7)
        _snow_cap(d, drift[:6], 560, 491, col=(250, 250, 252))
    els.append(SC.accrue(clock, 28, 29, g_gate, eid='g_gate'))
    # NO caption at b28. Snow taking the bottom half of the frame over a gate
    # with five slits in it IS "snow buries that gate for months".

    # ---- b29  the tunnels, still down there -------------------------------- #
    # A rock mass rises over the face and the bore is cut into it. Its top
    # stops at y=124, so the sky strip survives above it and the title stays
    # legible there -- no lintel is needed on this card.
    def g_cutaway(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        deep = [(-60, 140), (300, 124), (700, 138), (1000, 128), (1340, 136),
                (1340, 780), (-60, 780)]
        _mass(d, deep, (98, 94, 90), 500, width=7)
        _bore(d, 180, 430, 1180, 400, 560, 210, 503, lamps=3)
        SC.closeup(d, 1150, 340, 158, 'grim', 504)
    els.append(SC.stage(clock, 29, g_cutaway, j=30))
    # NO caption at b29. A lit bore going away from the viewer, unchanged, with
    # the presenter looking into it, is the sentence.

    # ---- b30  the door again, and nobody has gone in ----------------------- #
    # The last mass. Same ROCK as the cliff behind it, so the crest does not
    # read as a second hill; the title band above it is plain sky, which is why
    # this card needs no title_backdrop the way the b19 tunnel does.
    def g_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        rock = [(-60, 150), (300, 130), (700, 142), (1000, 130), (1340, 140),
                (1340, 780), (-60, 780)]
        _mass(d, rock, ROCK, 510, width=7)
        _snow_cap(d, [(60, 150), (300, 130), (700, 142), (980, 130),
                      (1220, 140)], 166, 511)
        _archway(d, 640, 500, 420, 340, 512)
        _steel_door(d, 640, 350, 200, 300, 513, handle=False)
        SC.fullbody(d, 300, 720, 420, pose='standing', expression='deadpan',
                    seed=514)
    els.append(SC.stage(clock, 30, g_door, j=31))
    els.append(cap(30, 1010, 640, size=32, max_w=520))

    return SC.finish(els, TITLE, clock, title_seed=41)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent2.mp4'))