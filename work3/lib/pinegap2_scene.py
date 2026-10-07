"""pinegap2_scene -- the PERSISTENT-STAGE rebuild of chapter 1.

WHY THIS FILE EXISTS. pinegap_scene.py (v1) was built on "one card per beat, each
card paints its own whole frame". Every beat cut to a brand-new full-frame image
and nothing ever moved: measured 97.6% still / 0.2% motion, a new image every
~2.3s. A viewer reported exactly this -- "every sentence has a cut with a
completely new image... there are no animations or changes to the visual." Our
own measurements doc names the fix (REFERENCE_MEASUREMENTS.md): "Each reveal
adds/moves ONE element (no whole-card swaps)" and "There must be real per-frame
motion, not pop-and-hold stills."

THE MODEL HERE. Seven PERSISTENT STAGES instead of sixteen short ones, grouped on
the narration's own acts rather than on beats:

    A  b01-b03  (3.2s)   the empty desert -- "there is nothing here"
    B  b04-b09  (10.4s)  the wide desert; white spheres accumulate, wire goes up
    C  b10-b16  (14.2s)  "they are not buildings" -> PINE GAP -> flags -> the lie
    D  b17-b21  (10.6s)  the radome cutaway -- cover, dish, the hidden angle
    E  b22-b27  (16.2s)  globe -> FIVE EYES -> satellite crossing -> beams land
    F  b28-b30  (8.0s)   the signals, and the presenter recoiling
    G  b31-b34  (7.4s)   the perimeter: airspace, guards, seven years

The frame repaints seven times in 70s instead of sixteen times (longest gap
3.2s -> 16.2s), and inside a stage the art ACCUMULATES: a layer that arrives
stays until the stage turns over (SC.accrue). The viewer's eye gets one
recognisable place to look while the next thing is added to it.

TWO RULES THAT TOOK ME TWO ROUNDS TO LEARN -- both measured, both kept here so
they are not relearned the hard way.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Accruing everything is also wrong. The
   first version let every layer live to stage end and the result was pile-ups:
   "18,000 FEET" under "7 years in prison" under three guards, the globe
   underneath the five-eye row, "RADOME" sitting on top of its own caption.
   Layers that occupy the same part of the frame, and anything carrying text,
   still REPLACE. Only the environment and the running subject accrue.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces motion at a rate the
   reference does not have (measured 22.5% against the reference's 7%) and every
   moving frame trips the picture-change counter -- 82 changes, one per 0.85s,
   which is WORSE than the 30 it was meant to fix. The reference is 83% still.
   So: ~9 arrivals move, briefly (0.45-0.6s), on small subjects. Everything
   else pops in on its beat. Popping in IS the reveal; sliding is for the
   handful of moments where movement carries meaning (the sphere appearing, the
   cover lifting, the missile falling, the satellite crossing).

CAPTIONS. One short phrase on 14 of 34 beats (41%), each timed to the beat whose
words it carries, each placed in that stage's clear zone. A text-free beat is
the common case. Never gray or near-black: scene_common.caption() refuses a
low-chroma dark fill and resolves the on-paper/on-night pair by measured WCAG
contrast, because contrast is a property of the PAIR and no single-colour
threshold is right for both a cream page and a night card.

Run:  python lib/pinegap2_scene.py --preview --video
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
import pinegap_scene as PG     # art primitives + palette, reused not copied

# palette / geometry, reused from v1
INK = PG.INK
RED = PG.RED
DUNE = PG.DUNE
SKY = PG.SKY
DOME = PG.DOME
STEEL = PG.STEEL
CONCRETE = PG.CONCRETE
NIGHT = PG.NIGHT
NIGHT_G = PG.NIGHT_G
HZ = PG.HZ
W, H = PG.W, PG.H
TITLE = PG.TITLE
BEATS = PG.BEATS
SEG = PG.SEG
TITLE_BACKDROP = PG.TITLE_BACKDROP

_desert = PG._desert
_radome = PG._radome
_fence = PG._fence
_dish = PG._dish
_ghost_cover = PG._ghost_cover
_globe = PG._globe
_satellite = PG._satellite
_icon_phone = PG._icon_phone
_icon_radio = PG._icon_radio
_icon_missile = PG._icon_missile

# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and it becomes the picture changing every sample,
# which is the defect this whole rebuild exists to remove.
ARRIVE = 0.5


# =========================================================================== #
# LANDSCAPE SUBSTRATE -- added to close the flat-vector gap.               #
# =========================================================================== #
#
# WHAT WAS WRONG, MEASURED. The pigment gate read 29 of 34 pinegap beats
# "flat" (median 24px-tile luma std 2.9-3.5 against a threshold of 8.0), and
# rendering the frames explains it exactly: every exterior beat was ONE smooth
# sky wash on top of ONE smooth ground wash with a few wireframe outlines
# floating on them. The blind critic's complaint -- "flat vector and
# under-filled" -- is the same thing. Paint texture inside two giant fills
# cannot fix it; there are only two shapes and they are both enormous. The
# lever is COMPOSITION: break each void into many small outlined shapes that
# run OFF the frame edges, so the frame admits the system is bigger than the
# picture.
#
# So every exterior stage now paints a real substrate instead of two flat
# rectangles: stratified cloud bands in the sky, layered dune contour bands
# and mesas on the ground, and scrub/rock scatter for near-field tooth. Each
# helper is seeded (deterministic) and uses the painterly PA primitives so the
# new shapes get the same pigment the existing art gets -- we are adding
# STRUCTURE, not raising the paint constants.

def _wavy(seed, x0, x1, y, amp, n=26):
    """A deterministic wavy run of points from x0 to x1 about baseline y."""
    out = []
    for i in range(n + 1):
        u = i / float(n)
        x = x0 + (x1 - x0) * u
        # sum of two sines with seeded phases -> a smooth, non-repeating ridge
        w = (math.sin(u * 5.1 + seed * 0.7) * 0.6
             + math.sin(u * 11.3 + seed * 1.9) * 0.4)
        out.append((x, y + amp * w))
    return out


def _strata(tile, d, seed, y0, y1, col_hi, col_lo, n=7, amp=14.0):
    """Layered horizontal cloud/wind bands across the sky, full-bleed.

    Each band is a filled wavy strip whose TOP edge is stroked, so the sky is a
    stack of outlined strata rather than one wash. They span the full width and
    so run off BOTH side edges -- the frame reads as a slice of a bigger sky.
    """
    img = PA.img_of(d)
    span = float(y1 - y0)
    for i in range(n):
        u = i / float(max(1, n - 1))
        yc = y0 + span * u
        h = 12 + 22 * (1.0 - u)                 # thicker low down
        top = _wavy(seed + i * 3, -20, W + 20, yc, amp, n=30)
        band = top + [(W + 20, yc + h + amp), (-20, yc + h + amp)]
        col = col_hi if i % 2 == 0 else col_lo
        PA.fill_poly(img, band, col, seed=seed + 40 + i, value=0.06, edge=2.0)
        PA.hand_stroke(d, top, (150, 158, 168), 3, closed=False,
                       seed=seed + 80 + i, wavelength=140.0, vary=0.34)
        # a second, fainter ridge line inside the band -> two edges per stratum
        mid = _wavy(seed + i * 3 + 1, -20, W + 20, yc + h * 0.55, amp * 0.6, n=26)
        PA.hand_stroke(d, mid, (168, 176, 186), 2, closed=False,
                       seed=seed + 120 + i, wavelength=120.0, vary=0.30)


def _dunes(tile, d, seed, hz, n_bands=6, base=DUNE, deep=None):
    """Layered ground contour bands receding toward the horizon, full-bleed.

    The nearest band reaches past the BOTTOM edge and the far bands stack up
    near the horizon, so the ground is a run of outlined contours, not a flat
    slab. `deep` is the colour of the nearest/richest band. Neighbouring bands
    are deliberately pushed apart in VALUE (the walk is eased so each step is a
    visible step), because two adjacent fills of near-equal value read as one
    smooth region no matter how much pigment is inside them.
    """
    img = PA.img_of(d)
    deep = deep or tuple(max(0, c - 40) for c in base)
    for i in range(n_bands):
        u = i / float(n_bands)
        yc = hz + 22 + (H - hz) * (u ** 1.25) * 1.10
        amp = 18 + 26 * u
        # eased value walk: pale far band -> deep near band, each step visible
        t = u ** 0.85
        col = tuple(int(base[c] * (1 - t) + deep[c] * t) for c in range(3))
        ridge = _wavy(seed + i * 5, -30, W + 30, yc, amp, n=34)
        slab = ridge + [(W + 30, H + 40), (-30, H + 40)]
        PA.fill_poly(img, slab, col, seed=seed + 60 + i, value=0.07, edge=3.0)
        # the ridge line is the band's own top edge -- dark and heavy so the
        # boundary between two bands is a drawn line, not an inferred one
        PA.hand_stroke(d, ridge, (146, 100, 50), 4, closed=False,
                       seed=seed + 100 + i, wavelength=150.0, vary=0.36)
        # a crest highlight just below the ridge -> a second edge per band
        crest = _wavy(seed + i * 5 + 2, -30, W + 30, yc + 14 + 10 * u, amp * 0.7,
                      n=30)
        PA.hand_stroke(d, crest, (240, 222, 186), 3, closed=False,
                       seed=seed + 140 + i, wavelength=130.0, vary=0.30)


def _mesa(d, cx, base_y, w, h, seed, col=(178, 132, 84)):
    """A distant flat-topped mesa on the horizon, outlined with striations."""
    top = base_y - h
    prof = [(cx - w / 2.0, base_y), (cx - w * 0.42, top + h * 0.18),
            (cx - w * 0.30, top), (cx + w * 0.30, top),
            (cx + w * 0.44, top + h * 0.16), (cx + w / 2.0, base_y)]
    PA.fill_poly(PA.img_of(d), prof, col, seed=seed, value=0.06)
    PA.hand_stroke(d, prof, (150, 106, 62), 3, closed=True, seed=seed + 1,
                   wavelength=120.0)
    for k in range(2):
        y = top + h * (0.30 + 0.26 * k)
        PA.hand_stroke(d, [(cx - w * 0.40, y), (cx + w * 0.40, y)],
                       (156, 112, 66), 2, closed=False, seed=seed + 2 + k,
                       wavelength=90.0, vary=0.30)


def _scrub(d, cx, cy, s, seed, col=(146, 108, 62)):
    """A small spiky desert bush -- near-field tooth, outlined."""
    pts = [(cx - s, cy)]
    for k in range(5):
        u = (k + 0.5) / 5.0
        pts.append((cx - s + 2 * s * u, cy - s * (0.5 + 0.5 * math.sin(k * 2.1))))
    pts.append((cx + s, cy))
    PA.hand_stroke(d, pts, col, 2, closed=False, seed=seed, wavelength=40.0,
                   vary=0.40)


def _rock(d, cx, cy, s, seed, col=(160, 118, 70)):
    """A small angular outlined rock."""
    poly = [(cx - s, cy), (cx - s * 0.6, cy - s * 0.8), (cx + s * 0.2, cy - s),
            (cx + s * 0.8, cy - s * 0.5), (cx + s, cy)]
    PA.fill_poly(PA.img_of(d), poly, col, seed=seed, value=0.06)
    PA.hand_stroke(d, poly, (128, 92, 54), 2, closed=True, seed=seed + 1,
                   wavelength=40.0)


def _landscape(tile, fw, fh, seed, sky=SKY, ground=DUNE, hz=HZ,
               mesas=True, scatter=True, pale=False):
    """The full exterior substrate: sky + strata + ground + dunes + mesas.

    This REPLACES `_desert` for the beats that were measured flat. `_desert`
    painted two rectangles; this paints a landscape. It is the direct answer to
    the pigment gate: instead of 2-3 enormous smooth shapes it lays down a sky
    of ~7 outlined strata and a ground of ~6 outlined contour bands, plus two
    flat-topped mesas on the horizon and near-field scrub/rock scatter. Every
    band runs off the left and right edges, so the frame admits the terrain
    continues past the picture.

    `pale=True` is for the white-register stages (globe / five-eyes / radio /
    missile) whose sky and ground are near-white; there the structure is drawn
    in faint greys so it stays a light register (the caption resolver and the
    title both key off a light background there).
    """
    d = ImageDraw.Draw(tile)
    img = PA.img_of(d)
    # base sky + ground
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.07)

    if pale:
        strata_hi, strata_lo = (247, 249, 251), (222, 229, 236)
        dune_base = ground
        dune_deep = (196, 206, 216)
        mesa_col = (188, 200, 212)
        scatter_col = (168, 182, 196)
    else:
        strata_hi, strata_lo = (214, 224, 232), (176, 190, 202)
        dune_base = ground
        dune_deep = tuple(max(0, c - 30) for c in ground)
        mesa_col = (182, 134, 84)
        scatter_col = (146, 108, 62)

    # sky strata (well above the horizon, and clear of the title band at top)
    _strata(tile, d, seed + 5, hz * 0.22, hz * 0.90, strata_hi, strata_lo,
            n=7, amp=13.0)

    # ground contour bands (recede toward the horizon, reach past the bottom)
    _dunes(tile, d, seed + 7, hz, n_bands=6, base=dune_base, deep=dune_deep)

    if mesas:
        # two flat-topped mesas sitting on the horizon, full-bleed to the sides
        _mesa(d, 250, hz + 6, 300, 54, seed + 11, mesa_col)
        _mesa(d, 980, hz + 6, 380, 66, seed + 13, mesa_col)

    if scatter:
        # near-field tooth along the bottom band
        for k, (x, y, s) in enumerate(((150, H - 90, 26), (620, H - 60, 30),
                                       (1080, H - 100, 24), (420, H - 150, 20))):
            _rock(d, x, y, s, seed + 20 + k, scatter_col)
        for k, (x, y, s) in enumerate(((320, H - 40, 30), (900, H - 30, 26),
                                       (180, H - 170, 22), (760, H - 190, 24))):
            _scrub(d, x, y, s, seed + 40 + k, scatter_col)

    PA.paper_overlay(tile, seed=seed + 2)


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
    # STAGE A  b01-b03  "Look at this place. There is nothing here.         #
    #                 That is the point."                                   #
    # One empty desert held across three beats. The emptiness IS the        #
    # narration, so the desert dominates -- but the presenter stands in it   #
    # from b01 and changes expression at b03, because four seconds of bare   #
    # backdrop reads as "nothing is happening" (the coverage gate called it #
    # NO ART on b01-b02, which was correct).                                 #
    # ===================================================================== #
    def a_desert(tile, fw, fh):
        _landscape(tile, fw, fh, 5, mesas=True, scatter=True)
    els.append(SC.stage(clock, 1, a_desert, j=4))

    # The presenter arrives on b01, not b03. He stands in the empty desert and
    # LOOKS at nothing while the narrator says "Look at this place. There is
    # nothing here." -- the emptiness is still the subject (he is a small
    # closeup at the left, the desert fills the rest of the frame), but the
    # opening now has an anchor instead of four seconds of bare backdrop. At
    # b03 he changes expression on "That is the point.": two elements at the
    # same position, the first ending where the second starts.
    def a_presenter(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 300, 360, 210, 'deadpan', 3)
    _bu, _aa, _au = SC.expr_swap(clock, 3, 'deadpan', 'skeptic', until_j=4)
    els.append(E3.E('a_presenter_a', 'character', a_presenter,
                    at=clock.at('b01', 0), until=_bu,
                    motion=SC.enter(clock, 1, dx=-150, dy=40, dur=0.55)))

    def a_presenter_b(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 300, 360, 210, 'skeptic', 3)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))
    els.append(cap(1, 760, 300, size=40))
    els.append(cap(3, 940, 610, size=32, fill=RED))

    # ===================================================================== #
    # STAGE B  b04-b09  "It sits in central Australia. The desert runs out   #
    #                 for miles. Then you see the white spheres. A whole    #
    #                 cluster of them. They sit behind layers of wire.      #
    #                 They look like ordinary buildings."                    #
    # A wide desert held across SIX beats. The locator inset, then a survey #
    # stake, then one sphere, then the cluster, then the wire -- each ACCRUES#
    # onto the same horizon so the viewer watches a place gain things. v1   #
    # gave "central Australia" a whole full-frame beat of map; an inset      #
    # carries the same information and stays put for six beats.             #
    # ===================================================================== #
    def b_desert(tile, fw, fh):
        _landscape(tile, fw, fh, 9)
    els.append(SC.stage(clock, 4, b_desert, j=10))

    def b_locator(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        land = [(956, 74), (1096, 44), (1214, 84), (1230, 156), (1140, 200),
                (1030, 188), (946, 140)]
        PA.fill_poly(tile, land, (206, 186, 138), seed=7, value=0.07)
        PA.hand_stroke(d, land, INK, 4, closed=True, seed=8, wavelength=90.0)
        d.ellipse([1064, 108, 1086, 130], fill=RED)
    els.append(SC.accrue(clock, 4, 10, b_locator, kind='shape'))

    def b_stake(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(214, 604), (214, 486)], (150, 118, 78), 8, seed=31,
                       wavelength=90.0)
        PA.fill_rect(tile, [214, 470, 282, 500], RED, seed=32, value=0.06)
        PA.hand_stroke(d, [(214, 470), (282, 470), (282, 500), (214, 500)],
                       INK, 4, closed=True, seed=33, wavelength=70.0)
    els.append(SC.accrue(clock, 5, 10, b_stake, kind='shape'))
    els.append(cap(5, 700, 210, size=32))

    def b_one_sphere(tile, fw, fh):
        # MOVING. "Then you see the white spheres" is the reveal of the whole
        # chapter; the sphere rising out of the sand is the one arrival worth
        # animating in this stage.
        _radome(ImageDraw.Draw(tile), 430, 452, 168, 35)
    els.append(SC.accrue(clock, 6, 10, b_one_sphere,
                         motion=SC.enter(clock, 6, dx=0, dy=64, dur=0.55)))

    def b_cluster(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _radome(d, 800, 440, 190, 37)
        _radome(d, 1010, 470, 150, 38)
        _radome(d, 232, 470, 140, 39)
    els.append(SC.accrue(clock, 7, 10, b_cluster))

    def b_wire(tile, fw, fh):
        # "behind layers of wire" -- the fence goes up IN FRONT of the cluster,
        # so the spheres are still there, just fenced.
        PG._fence(ImageDraw.Draw(tile), -40, 720, W + 40, 430, 40, n_posts=9)
    els.append(SC.accrue(clock, 8, 10, b_wire,
                         motion=SC.enter(clock, 8, dx=0, dy=130, dur=ARRIVE)))
    els.append(cap(8, 330, 240, size=30))

    # ===================================================================== #
    # STAGE C  b10-b16  "They are not buildings. This is Pine Gap. It runs  #
    #                 under a secret agreement. America and Australia share #
    #                 it. For decades the public was told nothing. They     #
    #                 called it a space research facility."                 #
    # SEVEN beats, 14.2s, one backdrop -- the longest hold in the chapter.  #
    # The name lands, the two flags rise, then the shutter and the sign: the #
    # cover story built in front of the viewer, in one place.               #
    # ===================================================================== #
    def c_desert(tile, fw, fh):
        _landscape(tile, fw, fh, 37)
    els.append(SC.stage(clock, 10, c_desert, j=17))

    def c_radome(tile, fw, fh):
        _radome(ImageDraw.Draw(tile), 640, 430, 300, 41)
    els.append(SC.accrue(clock, 10, 17, c_radome))

    def c_notbuildings(tile, fw, fh):
        D.draw_red_box(tile, [318, 118, 962, 646])
    # REPLACES rather than accrues: the red box is a mark on the same radome,
    # and the caption for this beat sits beside it, not under it.
    els.append(SC.layer(clock, 11, c_notbuildings, j=13, kind='shape',
                        eid='c_notbuildings'))
    els.append(cap(10, 190, 205, size=30, fill=RED))

    def c_name(tile, fw, fh):
        D.draw_label(tile, 'PINE GAP', center=(640, 250), color=RED, size=104)
    els.append(SC.accrue(clock, 12, 17, c_name, kind='shape',
                         motion=SC.enter(clock, 12, dx=0, dy=-64, dur=0.45)))

    def c_flags(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for x, cols, sd in ((296, [(178, 34, 44), (250, 250, 248)], 45),
                            (1000, [(12, 48, 120), (250, 250, 248),
                                    (214, 34, 44)], 49)):
            for i, c in enumerate(cols):
                x0 = x + i * 66
                PA.fill_rect(tile, [x0, 300, x0 + 62, 450], c, seed=sd + i,
                             value=0.06)
                PA.hand_stroke(d, [(x0, 300), (x0 + 62, 300), (x0 + 62, 450),
                                   (x0, 450)], INK, 5, closed=True,
                               seed=sd + 4 + i, wavelength=100.0)
            PA.hand_stroke(d, [(x, 300), (x, 590)], INK, 8, seed=sd + 8,
                           wavelength=120.0)
    els.append(SC.accrue(clock, 13, 17, c_flags, kind='shape'))
    els.append(cap(13, 640, 108, size=30, fill=RED))

    def c_shutter(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        body = [(300, 470), (1000, 470), (1000, 640), (300, 640)]
        PA.fill_poly(tile, body, CONCRETE, seed=53, value=0.07)
        PA.hand_stroke(d, body, INK, 7, closed=True, seed=54, wavelength=140.0)
        for i in range(3):
            y = 505 + i * 46
            PA.hand_stroke(d, [(320, y), (980, y)], (196, 188, 172), 5,
                           seed=55 + i, wavelength=110.0)
    els.append(SC.accrue(clock, 14, 17, c_shutter))

    def c_sign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        sign = [(300, 560), (1000, 560), (1000, 672), (300, 672)]
        PA.fill_poly(tile, sign, (250, 250, 248), seed=56, value=0.05)
        PA.hand_stroke(d, sign, INK, 7, closed=True, seed=57, wavelength=140.0)
        D.draw_label(tile, 'SPACE RESEARCH FACILITY', center=(650, 616),
                     color=INK, size=38)
    els.append(SC.accrue(clock, 15, 17, c_sign, kind='shape'))
    els.append(cap(15, 640, 704, size=26))

    # ===================================================================== #
    # STAGE D  b17-b21  "We now know what the white balls are. They are     #
    #                 radomes. A radome is a protective cover. Inside each   #
    #                 one sits a satellite dish. The cover hides the dish's  #
    #                 exact angle. Nobody outside can tell who is watched." #
    # ONE radome held across five beats while it is taken apart. v1 cut to a #
    # fresh diagram on every one of these sentences; here the same sphere is #
    # named, ghosted, opened, and shown the angle it was hiding.            #
    # ===================================================================== #
    def d_base(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _landscape(tile, fw, fh, 81)
        _radome(d, 640, 410, 300, 82, detail=False)
    els.append(SC.stage(clock, 17, d_base, j=22))

    def d_word(tile, fw, fh):
        D.draw_label(tile, 'RADOME', center=(640, 232), color=RED, size=72)
    els.append(SC.accrue(clock, 17, 22, d_word, kind='shape'))
    els.append(cap(17, 186, 250, size=30, fill=RED))

    def d_ghost(tile, fw, fh):
        # MOVING. The cover lifting off is the one moment in this stage where
        # movement IS the information.
        _ghost_cover(ImageDraw.Draw(tile), 640, 410, 300, 84)
    els.append(SC.accrue(clock, 18, 22, d_ghost, kind='shape',
                         motion=SC.enter(clock, 18, dx=0, dy=-42, dur=0.55)))
    # NO caption at b18. "A radome is a protective cover" is definition glue --
    # and it collided with the lifting cover's own arrival at bottom-right.
    # The moving cover SHOWS the protective cover; the b17 "They are radomes."
    # reveal is the beat that needs the words.

    def d_dish(tile, fw, fh):
        _dish(ImageDraw.Draw(tile), 640, 470, 250, 86, tilt=0.30)
    els.append(SC.accrue(clock, 19, 22, d_dish))

    def d_beam(tile, fw, fh):
        # The angle the cover hides: a red wedge fanning out of the dish.
        d = ImageDraw.Draw(tile)
        gx, gy, gr = 600, 460, 320

        def to_shell(deg):
            a = math.radians(deg)
            vx, vy = math.cos(a), math.sin(a)
            ox, oy = 600.0 - gx, 470.0 - gy
            b = 2.0 * (ox * vx + oy * vy)
            c = ox * ox + oy * oy - gr * gr
            disc = b * b - 4.0 * c
            if disc <= 0:
                return (600 + vx * 400, 470 + vy * 400)
            t = (-b + math.sqrt(disc)) / 2.0
            return (600 + vx * t, 470 + vy * t)

        e1, e2 = to_shell(-56), to_shell(-14)
        cone = [(600, 470), e1, e2]
        PA.fill_poly(tile, cone, (228, 208, 172), seed=93, value=0.06)
        PA.hand_stroke(d, [(600, 470), e1], RED, 5, seed=94, wavelength=110.0)
        PA.hand_stroke(d, [(600, 470), e2], RED, 5, seed=95, wavelength=110.0)
        mid = ((e1[0] + e2[0]) / 2.0, (e1[1] + e2[1]) / 2.0)
        PA.hand_stroke(d, [(mid[0] - 16, mid[1] - 16), (mid[0] + 16, mid[1] + 16)],
                       RED, 6, seed=96, wavelength=40.0)
        PA.hand_stroke(d, [(mid[0] + 16, mid[1] - 16), (mid[0] - 16, mid[1] + 16)],
                       RED, 6, seed=97, wavelength=40.0)
        D.draw_label(tile, 'the angle it hides', center=(1064, 148), color=RED,
                     size=30)
    els.append(SC.accrue(clock, 20, 22, d_beam, kind='shape',
                         motion=SC.enter(clock, 20, dx=84, dur=ARRIVE)))
    els.append(cap(20, 186, 470, size=28, fill=RED))

    def d_peeker(tile, fw, fh):
        # "Nobody outside can tell who is watched" -- he leans in from the edge
        # and is CROPPED by it. Placed small in open space he reads as set
        # dressing; cropped he reads as someone intruding on the shot.
        SC.fullbody(ImageDraw.Draw(tile), 1310, 720, 640, pose='peeking',
                    expression='skeptic', seed=93)
    els.append(SC.accrue(clock, 21, 22, d_peeker, kind='character'))

    # ===================================================================== #
    # STAGE E  b22-b27  "This is a top level listening post. It belongs to   #
    #                 the Five Eyes group. Five Eyes shares the signal      #
    #                 between nations. Spy satellites pass overhead every   #
    #                 day. Their signals land at Pine Gap. The signals       #
    #                 include phone calls."                                  #
    # The longest stage, 16.2s, and the one that carries the chapter's one   #
    # piece of real motion: the satellite CROSSING THE SKY. It is a small   #
    # element at 320px over 3.2s (~100px/s), which is over the 60px/s floor  #
    # motion_profile needs -- and small enough that a moving satellite does  #
    # not read as a repainted frame.                                         #
    # ===================================================================== #
    def e_sky(tile, fw, fh):
        _landscape(tile, fw, fh, 95, sky=(226, 232, 238),
                   ground=(224, 230, 236), pale=True)
    els.append(SC.stage(clock, 22, e_sky, j=28))

    def e_globe(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        gx, gy, gr = 560, 412, 300
        # The _globe primitive is a bare sphere with latitude hoops. On its own
        # it read as an unidentified grey ball -- the "unclear object" complaint
        # -- so the continents go on it. Drawn as three landmass blobs clipped
        # to the sphere, which is enough for a viewer to read "Earth" at a
        # glance without pretending to be a real map.
        gpts = PA.ellipse_pts(gx, gy, gr, gr, n=72)
        PA.fill_poly(PA.img_of(d), gpts, (150, 168, 190), seed=96, value=0.07)
        for k, blob in enumerate((
                [(-0.42, -0.30), (-0.10, -0.44), (0.16, -0.26), (0.10, -0.02),
                 (-0.16, 0.04), (-0.40, -0.10)],
                [(-0.14, 0.10), (0.20, 0.06), (0.34, 0.34), (0.10, 0.58),
                 (-0.10, 0.40)],
                [(0.30, -0.52), (0.62, -0.34), (0.70, -0.06), (0.44, 0.02),
                 (0.28, -0.24)])):
            pts = [(gx + u * gr, gy + v * gr) for u, v in blob]
            PA.fill_poly(PA.img_of(d), pts, (108, 146, 96), seed=96 + 40 + k,
                         value=0.06)
            PA.hand_stroke(d, pts, (66, 96, 70), 4, closed=True,
                           seed=96 + 50 + k, wavelength=120.0)
        PA.hand_stroke(d, gpts, INK, 6, closed=True, seed=97, wavelength=140.0)
        for k, ry in enumerate((0.30, 0.62, 0.88)):
            hoop = PA.ellipse_pts(gx, gy, gr * ry, gr, n=48)
            PA.hand_stroke(d, hoop, (110, 128, 150), 3, closed=True,
                           seed=106 + k, wavelength=110.0)
        # SIGNALS FLOW IN. Arrowheads point inward, so the post is RECEIVING --
        # a listening station, not a transmitter.
        for k, ang in enumerate((200, 160, 20, 340)):
            a = math.radians(ang)
            sx, sy = gx + math.cos(a) * (gr + 320), gy + math.sin(a) * (gr + 320)
            ex, ey = gx + math.cos(a) * (gr + 26), gy + math.sin(a) * (gr + 26)
            PA.hand_stroke(d, [(sx, sy), (ex, ey)], (198, 120, 60), 5,
                           seed=97 + k, wavelength=130.0)
            tip = (gx + math.cos(a) * (gr + 4), gy + math.sin(a) * (gr + 4))
            PA.hand_stroke(d, [(tip[0] + math.sin(a) * 20,
                                tip[1] - math.cos(a) * 20), tip],
                           (198, 120, 60), 5, seed=110 + k, wavelength=40.0)
            PA.hand_stroke(d, [(tip[0] - math.sin(a) * 20,
                                tip[1] + math.cos(a) * 20), tip],
                           (198, 120, 60), 5, seed=120 + k, wavelength=40.0)
    # REPLACES: the globe is a full-height subject. Left accruing, the five-eye
    # row landed on top of it and both became unreadable.
    els.append(SC.layer(clock, 22, e_globe, j=23))
    els.append(cap(22, 1074, 668, size=28))

    def e_eyes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for i in range(5):
            x = 190 + i * 225
            e = PA.ellipse_pts(x, 300, 92, 56, n=44)
            PA.fill_poly(tile, e, (250, 250, 248), seed=100 + i, value=0.04)
            PA.hand_stroke(d, e, INK, 6, closed=True, seed=105 + i,
                           wavelength=100.0)
            d.ellipse([x - 26, 276, x - 2, 300], fill=INK)
            d.ellipse([x + 2, 276, x + 26, 300], fill=INK)
        D.draw_label(tile, 'FIVE EYES', center=(640, 520), color=INK, size=54)
    els.append(SC.accrue(clock, 23, 25, e_eyes, kind='shape'))
    # NO caption at b23. The drawn "FIVE EYES" label IS the words -- a caption
    # under it repeated the label and stacked text on text.

    def e_sat(tile, fw, fh):
        PG._satellite(ImageDraw.Draw(tile), 640, 168, 96, 112)
    els.append(SC.accrue(clock, 25, 28, e_sat, kind='shape',
                         motion=SC.drift(clock, 25, 26, dx=320, dy=0)))

    def e_beams(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dish(d, 640, 520, 290, 122, tilt=0.5)
        for k, a in enumerate((-0.7, -0.24, 0.24, 0.7)):
            x0 = 640 + 430 * math.tan(a)
            PA.hand_stroke(d, [(x0, 96), (640, 268)], (214, 132, 60), 5,
                           seed=123 + k, wavelength=130.0)
    # MOVING. "Their signals land at Pine Gap" -- the beams arriving is the
    # payload of this stage, so it gets the arrival.
    els.append(SC.accrue(clock, 26, 28, e_beams,
                         motion=SC.enter(clock, 26, dx=0, dy=-56, dur=0.55)))
    els.append(cap(26, 190, 430, size=28, fill=RED))

    def e_icon_phone(tile, fw, fh):
        PG._icon_phone(ImageDraw.Draw(tile), 1128, 590, 200, 132)
    els.append(SC.accrue(clock, 27, 28, e_icon_phone, kind='shape'))

    # ===================================================================== #
    # STAGE F  b28-b30  "They include radio traffic. They include missile   #
    #                 launch data. Getting close is nearly impossible."     #
    # ===================================================================== #
    def f_sky(tile, fw, fh):
        _landscape(tile, fw, fh, 131, sky=(226, 232, 238),
                   ground=(222, 228, 234), pale=True)
    els.append(SC.stage(clock, 28, f_sky, j=31))

    def f_radio(tile, fw, fh):
        # Not PG._icon_radio. That primitive is a grey box with three lines and
        # a stub, which read on screen as a blank card -- exactly the "unclear
        # object" complaint.
        #
        # The second attempt at this drew a lattice mast and a separate emitter
        # dot, which on screen read as a crucifix beside a target reticle --
        # two unrelated objects, and the arcs appeared to float free of the
        # thing emitting them. What makes a radio mast legible is ONE silhouette
        # with the wavefronts springing from its tip, so the arcs are centred on
        # the emitter itself and grow outward from it.
        d = ImageDraw.Draw(tile)
        bx, by = 560, 600            # base of the mast
        tipx, tipy = 560, 250        # emitter at the top of it
        # tapering lattice mast: two legs and three rungs
        PA.hand_stroke(d, [(bx - 54, by), (tipx - 16, tipy)], INK, 7, seed=139,
                       wavelength=110.0)
        PA.hand_stroke(d, [(bx + 54, by), (tipx + 16, tipy)], INK, 7, seed=140,
                       wavelength=110.0)
        for k in range(1, 4):
            u = k / 4.0
            y = by + (tipy - by) * u
            hw = 54 + (16 - 54) * u
            PA.hand_stroke(d, [(bx - hw, y), (bx + hw, y)], INK, 5,
                           seed=141 + k, wavelength=80.0)
        PA.hand_stroke(d, [(bx - 96, by), (bx + 96, by)], INK, 8, seed=145,
                       wavelength=90.0)
        d.ellipse([tipx - 26, tipy - 26, tipx + 26, tipy + 26], fill=RED)
        PA.hand_stroke(d, [(tipx, tipy - 26), (tipx, tipy - 62)], INK, 6,
                       seed=146, wavelength=60.0)
        # wavefronts, centred on the emitter, opening to the right
        for i, r in enumerate((96, 172, 248)):
            arc = [(tipx + r * math.cos(a), tipy + r * math.sin(a))
                   for a in [(-0.62 + 1.24 * k / 22.0) for k in range(23)]]
            PA.hand_stroke(d, arc, RED, 9, seed=147 + i, wavelength=120.0)
    els.append(SC.accrue(clock, 28, 29, f_radio, kind='shape'))

    def f_listener(tile, fw, fh):
        # CHARACTER. "They include radio traffic" is a dry, deadpan fact, so he
        # stands at the left edge -- CROPPED by it, not parked in open space --
        # pointing at the mast with a real elbow (ra=78deg), reading skeptical.
        # He is DARK on this pale register, which is the correct inverse of the
        # cream-on-dark rule the night cards use. He leaves at b30 so he does
        # not stand beside the recoiling figure that beat already has.
        SC.fullbody(ImageDraw.Draw(tile), 108, 700, 440, pose='pointing',
                    expression='skeptic', seed=150)
    els.append(SC.layer(clock, 28, f_listener, j=30, kind='character'))

    def f_missile(tile, fw, fh):
        PG._icon_missile(ImageDraw.Draw(tile), 900, 330, 320, 140)
    # MOVING, and the one place a fast arrival is right: the narrator says
    # "missile launch data" and a missile falling is the clearest read of it.
    els.append(SC.accrue(clock, 29, 31, f_missile,
                         motion=SC.enter(clock, 29, dx=0, dy=-280, dur=0.6)))
    els.append(cap(29, 640, 664, size=32, fill=RED))

    def f_recoil(tile, fw, fh):
        # handsup, not recoil: the recoil pose's arms sit level with the spine
        # and read as a scarecrow -- the documented horizontal-T-arm defect.
        # Here the pose is also the better read of "nearly impossible".
        SC.fullbody(ImageDraw.Draw(tile), 218, 700, 500, pose='handsup',
                    expression='worried', seed=148)
    els.append(SC.accrue(clock, 30, 31, f_recoil, kind='character'))
    # NO caption at b30. "Getting close is nearly impossible" is carried by the
    # hands-up worried presenter -- it is the character's whole job to be the
    # audience's reaction. b29 keeps its caption because the missile falls on
    # "missile launch data" and the viewer needs that word with the arrival.

    # ===================================================================== #
    # STAGE G  b31-b34  "Airspace is locked to eighteen thousand feet.       #
    #                 Armed guards walk the perimeter. Crossing the fence   #
    #                 means seven years in prison. No one goes inside."      #
    # The airspace column REPLACES at b32. Left accruing it stayed on screen #
    # under the fence and the guards, and "18,000 FEET" ended up printed     #
    # across "7 years in prison" -- the worst frame in the chapter.          #
    # ===================================================================== #
    def g_desert(tile, fw, fh):
        _landscape(tile, fw, fh, 161, sky=(200, 212, 226), ground=DUNE)
    els.append(SC.stage(clock, 31, g_desert, j=35))

    def g_column(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        col = [(330, 720), (330, 104), (910, 104), (910, 720)]
        PA.fill_poly(tile, col, (176, 190, 208), seed=153, value=0.08)
        # INTERNAL STRUCTURE. This slab is the single biggest flat area left in
        # the chapter: one smooth 580x600 fill under one number. Adding an
        # altitude LADDER -- evenly spaced horizontal rungs with tick marks
        # climbing the left post -- turns the no-fly box into a measured
        # airspace and gives the region the small outlined shapes the other
        # frames get from their contour bands. The 18,000 line is the one rung
        # drawn in red; the rest recede in value so the numeral stays the hero.
        for k in range(9):
            y = 132 + k * 64
            PA.hand_stroke(d, [(352, y), (888, y)], (150, 166, 186), 3,
                           closed=False, seed=180 + k, wavelength=130.0,
                           vary=0.28)
            PA.hand_stroke(d, [(352, y), (392, y)], (120, 136, 158), 4,
                           closed=False, seed=200 + k, wavelength=50.0)
        # the locked ceiling, drawn as the heaviest rung with a stop bar
        PA.hand_stroke(d, [(340, 104), (900, 104)], RED, 8, closed=False,
                       seed=214, wavelength=160.0)
        for x in (330, 910):
            PA.hand_stroke(d, [(x, 104), (x, 720)], RED, 7, seed=154 + x,
                           wavelength=160.0)
        PA.hand_stroke(d, [(330, 104), (910, 104)], RED, 7, seed=156,
                       wavelength=160.0)
        D.draw_number(tile, '18,000', center=(620, 274), color=RED, size=96)
        D.draw_label(tile, 'FEET', center=(620, 366), color=RED, size=44)
    els.append(SC.layer(clock, 31, g_column, j=32))
    # NO caption at b31. The column DRAWS "18,000 FEET" in a 96px red numeral --
    # that numeral is the spoken phrase, shown. The caption at cy=500 also sat
    # directly on top of the column it was describing.

    def g_guards(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PG._fence(d, -40, 660, W + 40, 330, 162, n_posts=9)
        for i, x in enumerate((300, 640, 980)):
            SC.fullbody(d, x, 690, 380, pose='standing',
                        expression='deadpan', seed=170 + i)
    els.append(SC.accrue(clock, 32, 35, g_guards, kind='character',
                         motion=SC.enter(clock, 32, dx=0, dy=54, dur=ARRIVE)))
    els.append(cap(32, 640, 130, size=28))

    def g_price(tile, fw, fh):
        # ONE line, high in the sky. The earlier version stacked a 250px "7",
        # "years" and "in prison" in three places at once; one clear line is
        # what the brief asks for -- "centre it around one important phrase".
        D.draw_label(tile, '7 YEARS IN PRISON', center=(700, 156), color=RED,
                     size=52)
    els.append(SC.accrue(clock, 33, 35, g_price, kind='shape'))
    els.append(cap(34, 200, 156, size=30, fill=RED))

    return SC.finish(els, TITLE, clock, title_seed=23)