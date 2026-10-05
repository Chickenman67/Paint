"""svalbard2_scene -- the PERSISTENT-STAGE rebuild of chapter 8 (svalbard).

WHY THIS FILE EXISTS. svalbard_scene.py (v1) was built on "one card per beat,
each card paints its own whole frame": its local `card(i, j, draw, ...)` made
an exclusive-window element whose draw closure repainted background + subject +
labels for beats i..j-1, so nothing survived between beats. The frame was
repainted every ~2.7s and 35 captions on 35 beats (100% text density) made
every sentence a cut AND a new wall of words.

THE MODEL HERE. Seven PERSISTENT STAGES, grouped on the narration's own acts,
using the boundaries already fixed in plans/STAGE_PLANS.md:

    A  b01-b05   arctic mountain; the tunnel down into the rock
    B  b06-b10   the vault cut into permafrost; foil packets
    C  b11-b17   a million samples; minus eighteen; the seeds sleep
    D  b18-b21   the original plan was to shut the door
    E  b22-b26   the 2016 flood; 800 tonnes; cut off for a year
    F  b27-b30   the same permafrost thaws; watched; new tunnel
    G  b31-b35   still a bunker against catastrophe; finale

Inside a stage the art ACCUMULATES: SC.accrue() layers arrive and stay to the
stage end, SC.layer() replaces. Scenery accrues; anything carrying text and
anything sharing a part of the frame replaces. That is the first of the two
pilot rules, and v1's b19/b24 show why -- a caption sat on the frozen layer it
was describing.

TEXT DENSITY. v1 captioned all 35 beats. Here 13 of 35 (37%), never two
consecutive, each placed in its stage's clear zone and timed to the beat whose
words it carries. The captioned beats are b01, b04, b06, b10, b12, b15, b18,
b20, b23, b27, b29, b31, b35 -- the hook, the tunnel, the vault reveal, the
million, the two PIVOTS (b12 "every sample is a spare copy", b27 "the same
permafrost that keeps it thaws too"), the numbers (b10, b15, b23), the flood
turn (b20), and the last three beats. The test applied per beat: does the drawn
art already say the words, or does the viewer need them? Where the art carries
it -- the stamped SVALBARD label, the five drawn crop names, CROP INSURANCE,
the -18 numeral, FARM FREEZER vs VAULT, WARMING, -2.6 C PER DECADE, "a bunker"
-- the caption is DROPPED and the comment says why. A caption that repeats a
drawn label is a pile-up, not clarity.

MOTION. Ten moving elements, each 0.45-0.6s, each on a SMALL subject: a foil
packet, the sun's rays, the presenter entering, a camera lamp, a flood gate, an
excavator. Nothing on a backdrop, and nothing on a full-frame replace -- the
map, the split copy/original field, the globe and the tonnes wall all POP,
because a moving full-frame picture is the image churn this rebuild exists to
remove. The one larger move is the flood waterline RISING across b22-b23, and
the finale's channel DRIFTING right on b35; those are the two beats where the
narration describes something continuously moving.

THE ART is not redrawn. Every primitive (_arctic, _mountain, _tunnel, _cutaway,
_packet, _shelf, _doorway, _globe, ...) and the whole palette come from
svalbard_scene, imported and aliased, so this file cannot drift from v1's
look by accident.

Run:  python lib/svalbard2_scene.py --preview --video

THE WEDGE DEFECT IS NOW FIXED. SV._light_wedge fills an OPAQUE AMBER_LT
triangle, so on the dark night mountain it read as a solid gold pyramid rather
than a beam of light -- most visibly in the OPENING frame, where the stage
backdrop holds it for all of stage A. This file now draws its own _soft_beam()
(nested translucent wedges plus a landing pool) at both call sites, b01 and b30.
The v1 primitive is still aliased below for anything that wants the hard-edged
original. Fixing it inside v2paint.fill_poly (a real alpha) is still the general
answer and is not done.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import ImageDraw

import engine3 as E3
import scene_common as SC
import v2paint as PA
import v2subjects as S
import v2draw as D
import v2type as VT

import svalbard_scene as SV     # art primitives + palette, reused not copied

# identity, reused from v1
SEG = SV.SEG
TITLE = SV.TITLE
BEATS = SV.BEATS
TITLE_BACKDROP = SV.TITLE_BACKDROP

# palette, reused from v1. Only the entries this module actually draws with are
# aliased; the full set stays reachable as SV.<name> if a later pass needs it.
INK = SV.INK
SNOW = SV.SNOW
AMBER = SV.AMBER
AMBER_LT = SV.AMBER_LT
LEAF = SV.LEAF
RED = SV.RED
WATER = SV.WATER
CONCRETE = SV.CONCRETE
STEEL = SV.STEEL
TITLE_COURSE = SV.TITLE_COURSE

# The style canon's cream figure for DARK cards. character3 draws him near-black
# (BODY 26,26,30), which is right on the paper cards and invisible against the
# night mountain and the tunnel. Passed as ink= to SC.fullbody on those beats.
CREAM = (240, 238, 230)

W, H = SV.W, SV.H
HZ = SV.HZ

# art primitives, reused from v1
_arctic = SV._arctic
_day_arctic = SV._day_arctic
_interior = SV._interior
_mountain = SV._mountain
_wedge = SV._wedge
_doorway = SV._doorway
_tunnel = SV._tunnel
_shelf = SV._shelf
_packet = SV._packet
_globe = SV._globe
_cutaway = SV._cutaway
_camera = SV._camera


def _soft_beam(d, x, y0, y1, half, seed, colour=None):
    """A wedge of LIGHT, not a gold cone.

    SV._light_wedge fills one solid AMBER_LT triangle, which on the dark
    exterior reads as an opaque pyramid -- two of them at b30 looked like
    traffic cones, and the file's own b32 comment already said so about the
    same primitive. This draws the beam as nested triangles from widest and
    dimmest to narrowest and brightest, plus a bright pool where it lands, so
    it reads as light spreading out of a lamp rather than a solid shape.
    """
    colour = colour or AMBER_LT
    steps = 6
    for i in range(steps):
        f = 1.0 - i / float(steps)          # 1.0 (widest, base layer) -> ~0.17
        hf = half * (0.30 + 0.70 * f)
        y0i = y0 + (y1 - y0) * (1.0 - f) * 0.55
        shade = tuple(min(255, int(c + (255 - c) * (i / float(steps)) * 0.55))
                      for c in colour)
        tri = [(x - hf * 0.12, y0i), (x + hf * 0.12, y0i),
               (x + hf, y1), (x - hf, y1)]
        PA.fill_poly(PA.img_of(d), tri, shade, seed=seed + i, value=0.05)
    pool = PA.ellipse_pts(x, y1, half * 0.9, 26, n=40)
    PA.fill_poly(PA.img_of(d), pool, (236, 240, 226), seed=seed + 40,
                 value=0.06)
_excavator = SV._excavator
_flood_gate = SV._flood_gate
_light_wedge = SV._light_wedge

# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and the element stops being an arrival and starts
# being the picture changing every sample.
ARRIVE = 0.5


def _frost_bank(d, x0, x1, ybase, lo, hi, seed, colour=(233, 243, 250),
                step=132.0):
    """A bank of ICE as a filled mass with a soft, uneven upper boundary.

    Two earlier passes at the b19 door failed here in instructive ways. v1 put
    ~70 short white ticks on a golden-angle spiral, which read as scratches on
    the lens. v2 laid evenly-spaced perpendicular strokes along each edge, which
    read as a dashed white BORDER -- and its long parallel icicles above that
    read as a bar code. v3 replaced the ticks with jittered blobs, which read as
    snowflakes: discrete white stars with spikes, arranged in a rectangle. All
    three shared one flaw -- frost that does not CONNECT does not read as a
    substance. This one fills a bank from a solid base up to a crest.

    The crest is the whole art problem. It is sampled at `step` px with three
    octaves of wobble rather than alternating lo/hi at every vertex: v4 used a
    per-vertex alternation and rendered as a row of sharp white triangles, a
    sawblade standing on the door. Snow banks roll. So the boundary is a smooth
    spline-ish sequence with a long swell, a medium lobe and a little tooth, and
    it is what you read as "drift" rather than "zigzag".
    """
    pts = [(x0, ybase), (x1, ybase)]
    steps = max(4, int((x1 - x0) / step))
    span = float(hi - lo)
    for s in range(steps + 1):
        u = s / float(steps)
        px = x0 + (x1 - x0) * u
        # three octaves: the swell of the drift, a lobe, then fine tooth. No
        # hard alternation, so no sawtooth.
        crest = (0.50 * math.sin(u * 3.1 + seed * 0.017)
                 + 0.30 * math.sin(u * 7.3 + seed * 0.031 + 1.1)
                 + 0.20 * math.sin(u * 15.7 + seed * 0.023 + 2.7))
        py = lo + span * (0.5 + 0.5 * crest)
        pts.append((px, py))
    PA.fill_poly(PA.img_of(d), PA.wobble_edge(pts, seed=seed, amount=2.0,
                                              wavelength=72.0),
                 colour, seed=seed, value=0.05, edge=0.0)


def _frost_crystals(d, x0, x1, ycrest, n, seed, colour=(226, 240, 249)):
    """A FEW crystal spikes standing off a frost crest.

    Deliberately sparse and irregular. The v3 pass put two dendrites on every
    blob, which at 60-odd blobs became a field of snowflakes; hoar grows in a few
    directions from a few nucleation points, so these are longer than they are
    numerous and none of them share an angle.
    """
    for k in range(n):
        px = x0 + (x1 - x0) * ((k * 0.618 + 0.11) % 1.0)
        py = ycrest + ((k * 23) % 9 - 4) * 5
        a = 2.1 + ((k * 0.41) % 1.0) * 2.2          # up and to the sides only
        ln = 26 + (k * 17) % 40
        PA.hand_stroke(d, [(px, py), (px + ln * math.cos(a), py + ln * math.sin(a))],
                       colour, 5, closed=False, seed=seed + k, wavelength=30.0)
        for j in (-1, 1):                            # two barbs near the tip
            bx = px + ln * 0.62 * math.cos(a)
            by = py + ln * 0.62 * math.sin(a)
            ba = a + j * 0.75
            PA.hand_stroke(d, [(bx, by),
                               (bx + ln * 0.44 * math.cos(ba),
                                by + ln * 0.44 * math.sin(ba))],
                           colour, 4, closed=False, seed=seed + 40 + k * 2 + j,
                           wavelength=22.0)


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
    # STAGE A  b01-b05  "Beneath an Arctic mountain, the world's seeds      #
    #                 sleep. / This is the Svalbard Global Seed Vault. /    #
    #                 It opened in 2008, on a Norwegian island. / A long    #
    #                 tunnel runs down into the rock. / The rock there is   #
    #                 permafrost, frozen for millennia."                     #
    # The night exterior is HELD across all five beats and the mountain is    #
    # the subject from the first frame. The presenter stands on the snow     #
    # from b01 -- four seconds of bare backdrop reads as a dead opening --   #
    # and the light wedge he stands in is the only warm thing on the slope.  #
    # Then the map (b03) and the corridor (b04) REPLACE the whole frame,      #
    # because a map inset over the mountain read as two pictures at once     #
    # and the corridor is a full-frame subject.                               #
    # ===================================================================== #
    def a_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 5)
        SC.title_backdrop(tile, 1005, col=TITLE_COURSE)
        _mountain(d, 7, crest=300, base=HZ + 6)
        _soft_beam(d, 760, 120, HZ - 4, 190, 9)
    els.append(SC.stage(clock, 1, a_night, j=6))

    def a_presenter(tile, fw, fh):
        # Cropped by nothing but standing SMALL against a big mountain: he is
        # a person looking at a mountain, which is the whole relationship in
        # one frame. Expression swaps to 'awed' at b03 for "It opened in 2008"
        # being replaced by the map -- he stays, the world turns over beneath
        # him, which is the cheapest way to say "then, somewhere else".
        SC.fullbody(ImageDraw.Draw(tile), 1150, HZ + 4, 190, pose='standing',
                    expression='deadpan', seed=11, ink=CREAM)
    _bu, _aa, _au = SC.expr_swap(clock, 2, 'deadpan', 'awed', until_j=3)
    els.append(E3.E('a_presenter_a', 'character', a_presenter,
                    at=clock.at('b01', 0), until=_bu,
                    motion=SC.enter(clock, 1, dx=140, dy=0, dur=0.55)))

    def a_presenter_b(tile, fw, fh):
        # The same man at the same spot, awed instead of blank: two elements,
        # the first ending exactly where the second starts (the expression is
        # baked into the rasterised tile, so a change needs two elements).
        SC.fullbody(ImageDraw.Draw(tile), 1150, HZ + 4, 190, pose='standing',
                    expression='awed', seed=11, ink=CREAM)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))
    els.append(cap(1, W // 2, 690, size=32, fill=AMBER_LT))

    def a_stamp(tile, fw, fh):
        # The vault's name, stamped across the sky. It IS the b02 line, so
        # there is NO caption on b02: a caption under a hand-stamped name is
        # the same words twice, printed on top of each other.
        D.draw_label(tile, 'SVALBARD', center=(640, 148), color=VT.LABEL_YELLOW,
                     size=86)
        D.draw_label(tile, 'GLOBAL SEED VAULT', center=(640, 238),
                     color=VT.LABEL_YELLOW, size=44)
    els.append(SC.accrue(clock, 2, 3, a_stamp, kind='shape'))

    def a_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (176, 202, 222), seed=21, value=0.05)
        PA.paper_overlay(tile, seed=22)
        land = [(-40, 720), (-40, 470), (150, 430), (280, 380), (360, 300),
                (470, 268), (520, 300), (430, 350), (500, 400), (430, 470),
                (560, 520), (470, 720)]
        PA.fill_poly(tile, land, (222, 226, 214), seed=23, value=0.07)
        PA.hand_stroke(d, land, INK, 7, closed=True, seed=24, wavelength=170.0)
        isle = [(690, 250), (790, 226), (880, 244), (900, 288), (800, 306),
                (704, 292)]
        PA.fill_poly(tile, isle, (222, 226, 214), seed=25, value=0.07)
        PA.hand_stroke(d, isle, INK, 6, closed=True, seed=26, wavelength=110.0)
        D.draw_label(tile, 'SPITSBERGEN', center=(795, 360), color=INK, size=32)
        D.draw_arrow(tile, (300, 200), (760, 250), color=RED, width=9, head=42,
                     bow=0.12)
        d.ellipse([905, 250, 929, 274], fill=RED)
        D.draw_number(tile, '2008', center=(1035, 430), color=VT.LABEL_RED,
                      size=76)
    # POPS, deliberately. The map is a full-frame replace; a moving full-frame
    # picture is the image churn this rebuild exists to remove (rule 2).
    els.append(SC.layer(clock, 3, a_map, j=4))
    # NO caption at b03. The red pin on the island plus a hand-drawn 2008 is
    # the b03 line shown; the words "Norwegian island" would sit on the map.

    def a_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 31, wall=(64, 70, 82))
        _tunnel(d, W // 2, 372, 33, mouth=760, depth=290, ribs=8)
        # He walks in ahead of the tunnel rather than standing in front of it:
        # at 200px on the corridor floor he is a person in the corridor, and the
        # ribs still converge past him to the vanishing point.
        SC.fullbody(d, W // 2 - 34, 560, 200, pose='standing',
                    expression='neutral', seed=35, ink=CREAM)
    els.append(SC.layer(clock, 4, a_corridor, j=5))
    els.append(cap(4, W // 2, 690, size=30, fill=(214, 224, 236)))

    def a_perma(tile, fw, fh):
        # The chapter's diagram, first appearance: the permafrost band hatched
        # between the surface rock and the hall. REPLACES the corridor because
        # both are full-frame subjects occupying the same centre.
        _cutaway(ImageDraw.Draw(tile), 37, label='PERMAFROST')
    els.append(SC.layer(clock, 5, a_perma, j=6))
    # NO caption at b05. "PERMAFROST" is DRAWN across the frozen layer; a
    # caption under it repeated the label and stacked text on the hatching.

    # ===================================================================== #
    # STAGE B  b06-b10  "The vault is cut straight into that ice. / Above    #
    #                 the doorway, the midsummer sun barely rises. / Down    #
    #                 inside, the seeds sleep in the cold. / The seeds are   #
    #                 packed into small foil packets. / Around a million      #
    #                 samples, from a hundred nations."                       #
    # The cross-section is the stage and it PERSISTS: the same cutaway the    #
    # viewer was just looking at at b05, now with the hall lit warm and the  #
    # corridor driven in from the left. The midsummer door (b07) is a        #
    # full-frame exterior so it replaces; the cold room (b08), the held      #
    # packet (b09) and the million (b10) are all INSIDE the rock, so they    #
    # accrue into the cold-room room rather than replacing the diagram.      #
    # ===================================================================== #
    def b_cut(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 41, warm_chamber=True)
    els.append(SC.stage(clock, 6, b_cut, j=8))

    def b_presenter(tile, fw, fh):
        # Pointing INTO the cutaway at the hall he is about to go inside. He
        # stands on the rock, not on the diagram, so the pointing reads as
        # "down there" rather than as an annotation.
        SC.fullbody(ImageDraw.Draw(tile), 250, 700, 300, pose='pointing',
                    expression='awed', seed=43)
    els.append(E3.E('b_presenter', 'character', b_presenter,
                    at=clock.at('b06', 0), until=clock.at('b07', 0),
                    motion=SC.enter(clock, 6, dx=-150, dy=0, dur=ARRIVE)))
    els.append(cap(6, W // 2, 132, size=32, fill=AMBER_LT))

    def b_midsummer(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 45)
        _mountain(d, 46, crest=270, base=HZ + 6)
        # "Above the doorway, the midsummer sun barely rises." Two things, kept
        # well apart so neither is a jumble: a concrete portal set into the rock
        # on the LEFT (so "above the doorway" has a referent), and a LOW amber
        # sun on the RIGHT sitting on the horizon with a soft halo.
        #
        # v1 drew S.sun_rays() here, whose long INK spikes around an amber disc
        # read as a black-petalled flower, and stacked _wedge + _doorway on top
        # of each other -- the wedge's underside (y~405) cut through the
        # doorway's lintel (y~270) and the left half became grey trapezoids
        # around a tan square. Drawn as ONE portal here: a lit opening in a
        # concrete face, sized to sit on the snow line.
        px, py = 330, 452                       # portal centre, on the horizon
        PA.fill_rect(tile, [px - 190, py - 210, px + 190, py + 150], CONCRETE,
                     seed=50, value=0.07)
        PA.hand_stroke(d, [(px - 190, py - 210), (px + 190, py - 210),
                           (px + 190, py + 150), (px - 190, py + 150)], INK, 8,
                       closed=True, seed=51, wavelength=150.0)
        # the dark opening, with warm light at the far end of it
        PA.fill_rect(tile, [px - 82, py - 118, px + 82, py + 150], (44, 48, 58),
                     seed=52, value=0.06)
        glow = PA.ellipse_pts(px, py + 40, 66, 96, n=44)
        PA.fill_poly(tile, glow, (198, 152, 74), seed=53, value=0.06)
        PA.hand_stroke(d, [(px - 82, py - 118), (px + 82, py - 118),
                           (px + 82, py + 150), (px - 82, py + 150)], INK, 7,
                       closed=True, seed=54, wavelength=140.0)
        halo = PA.ellipse_pts(1010, HZ + 6, 158, 96, n=56)
        PA.fill_poly(tile, halo, AMBER_LT, seed=47, value=0.04)
        disc = PA.ellipse_pts(1010, HZ + 6, 64, 64, n=48)
        PA.fill_poly(tile, disc, AMBER, seed=48, value=0.05)
        PA.hand_stroke(d, disc, INK, 5, closed=True, seed=49, wavelength=90.0)
        D.draw_label(tile, 'midsummer', center=(1010, HZ - 130), color=INK,
                     size=38)
    els.append(SC.layer(clock, 7, b_midsummer, j=8,
                        motion=SC.enter(clock, 7, dx=0, dy=30, dur=ARRIVE)))
    # MOVING. The sun slides UP off the horizon by 30px over 0.5s: "barely
    # rises" is a sun that clears the skyline by a little, and watching it do
    # so is the whole sentence. Small subject, one arrival.
    # NO caption at b07. The drawn word "midsummer" sits directly above the
    # drawn sun at the height it happens at -- a caption would repeat it.

    def b_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 55, wall=(78, 86, 98), floor=(58, 64, 74),
                  warm=(104, 88, 56))
        for k in range(5):
            _shelf(d, -120 + k * 8, W + 120, 210 + k * 96, 56 + k, h=190,
                   packets=13)
    els.append(SC.layer(clock, 8, b_room, j=11))
    # NO caption at b08. "the seeds sleep in the cold" is the mood the cold blue
    # room already carries; the words would sit on the only warm patch in it.

    def b_packet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # One packet held up to the light, drawn large enough to bleed off the
        # right edge. The glow sits at cy=400 so its top edge is y=140, clear of
        # the title band -- v1 learned this the hard way.
        g = PA.ellipse_pts(640, 400, 300, 260, n=64)
        PA.fill_poly(tile, g, AMBER_LT, seed=62, value=0.05)
        _packet(d, 640, 350, 300, 400, 63, band=AMBER, stamp='wheat')
        # a hand coming in from the right edge, gripping it -- cropped by the
        # frame edge so it reads as an arm reaching in, not a floating paw.
        PA.hand_stroke(d, [(1330, 560), (820, 470)], (232, 202, 172), 66,
                       closed=False, seed=64, wavelength=170.0)
        PA.hand_stroke(d, [(1330, 560), (820, 470)], INK, 5, closed=False,
                       seed=65, wavelength=170.0)
        for k in range(3):
            PA.hand_stroke(d, [(880 + k * 42, 452 + k * 10), (930 + k * 42, 546)],
                           (232, 202, 172), 30, closed=False,
                           seed=66 + k, wavelength=50.0)
        D.draw_label(tile, 'one sample', center=(640, 640), color=INK, size=34)
    els.append(SC.layer(clock, 9, b_packet, j=11,
                        motion=SC.enter(clock, 9, dx=0, dy=-70, dur=ARRIVE)))
    # NO caption at b09. "one sample" is DRAWN on the packet's own shadow.

    def b_million(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 69, wall=(66, 72, 84), floor=(48, 54, 64))
        # the corridor of shelves narrowing into the dark -- this is the SAME
        # cold room as b08, pushed back, so the room recedes instead of being
        # replaced by an unrelated picture.
        for k in range(6):
            t = k / 5.0
            hw = 700 - 460 * t
            _shelf(d, 640 - hw, 640 + hw, 250 + k * 74, 70 + k, h=120,
                   packets=max(3, 11 - k * 2))
        g = PA.ellipse_pts(640, 480, 130, 96, n=48)
        PA.fill_poly(tile, g, (26, 30, 38), seed=76, value=0.0)
    els.append(SC.layer(clock, 10, b_million, j=11))

    def b_count(tile, fw, fh):
        D.draw_number(tile, '1,000,000', center=(640, 470),
                      color=VT.LABEL_YELLOW, size=104)
    els.append(E3.E('b_count', 'shape', b_count, at=clock.at('b10', 0),
                    until=clock.at('b11', 0)))
    els.append(cap(10, W // 2, 700, size=30, fill=VT.LABEL_YELLOW))

    # ===================================================================== #
    # STAGE C  b11-b17  "Wheat, rice, barley, beans, and millet. / Every     #
    #                 sample in there is a spare copy. / The original seed   #
    #                 always stays on the farm. / Each nation's crop         #
    #                 insurance, stored in a mountain. / Inside, the air     #
    #                 holds at minus eighteen degrees. / That is colder than  #
    #                 any farm freezer. / In that cold, the seeds sleep for  #
    #                 centuries."                                            #
    # SEVEN beats, 17.4s, one held room -- the longest stage in the chapter. #
    # The shelf run PERSISTS from b11 and the five named packets ARRIVE on it  #
    # together, so "wheat, rice, barley, beans, millet" is one row filling    #
    # rather than five new full frames. The spare-copy thought (b12-b14) moves #
    # OUT of the room to the field, the talking head and the globe, and the    #
    # temperature comes back inside. Each of those subjects is a full-frame   #
    # replace, so the stage's through-line is the shelf deck, not any one      #
    # picture.                                                                #
    # ===================================================================== #
    def c_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 77, wall=(80, 88, 100), warm=(104, 90, 58))
        _shelf(d, -60, W + 60, 600, 78, h=210, packets=5)
    els.append(SC.stage(clock, 11, c_room, j=12))

    def c_crops(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # All five arrive together, because the narrator names all five in ONE
        # beat ("Wheat, rice, barley, beans, and millet"). Spreading them over
        # five beats would have five packets landing on empty beats with the
        # words already gone, which reads as the picture lagging the narration.
        # One row, one arrival, five distinct crop marks so the row reads as
        # five different seeds at a glance.
        #
        # NO drawn name under each packet. v1 drew WHEAT/RICE/BARLEY/BEAN/MILLET
        # at y=350, which is exactly the packets' top edge (cy 470 - h/2 125 =
        # 345): every label straddled its own packet's border and was cut by it.
        # The five names are now ONE caption line, spoken-worded at b11, which
        # is also the "one important phrase, not five scattered words" rule.
        kinds = ['wheat', 'rice', 'barley', 'bean', 'millet']
        for i, k in enumerate(kinds):
            cx = 128 + i * 256
            _packet(d, cx, 470, 168, 250, 80 + i * 3, band=AMBER, stamp=k)
    els.append(SC.accrue(clock, 11, 12, c_crops, kind='shape',
                         motion=SC.enter(clock, 11, dx=0, dy=-56, dur=ARRIVE)))
    els.append(cap(11, 640, 700, size=30))
    # The five crop names live here, as one line, at the beat the narrator says
    # them. It replaces five drawn labels that were colliding with the packets.

    # ===================================================================== #
    # STAGE C1b  b12  "Every sample in there is a spare copy."               #
    # Its OWN stage, and the split is the fix. v1 ran c_crops for b11-b13 and   #
    # laid the COPY/ORIGINAL panels on top at b12; rendered, the COPY box       #
    # buried the WHEAT and RICE packets, the drawn crop stalks grew straight     #
    # through the BEAN and MILLET packets, and a loose packet floated in front   #
    # of another. Two complete compositions sharing one frame is the            #
    # over-population defect, not a reveal -- so b12 gets a clean stage of its   #
    # own and the crops hand off to it.                                          #
    # ===================================================================== #
    def c1b_room(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, W, H], (74, 82, 94), seed=91, value=0.06)
        PA.fill_rect(tile, [0, 470, W, H], (58, 64, 74), seed=92, value=0.07)
        PA.paper_overlay(tile, seed=93)
    els.append(SC.stage(clock, 12, c1b_room, j=13))

    def c_copy(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # left: the vault copy, in its cold box
        PA.fill_rect(tile, [40, 210, 560, 660], (96, 106, 120), seed=94,
                     value=0.07)
        PA.hand_stroke(d, [(40, 210), (560, 210), (560, 660), (40, 660)], INK,
                       7, closed=True, seed=95, wavelength=160.0)
        D.draw_label(tile, 'COPY', center=(300, 262), color=VT.LABEL_YELLOW,
                     size=46)
        _packet(d, 300, 450, 200, 290, 96, band=AMBER, stamp='wheat')
        # right: the original, still standing in its own rows of leaves. The
        # stalks are drawn INSIDE the right panel's own x-range and stop at its
        # baseline, so nothing crosses into the left box.
        for k in range(6):
            x = 706 + k * 88
            top = 560 - (k % 3) * 34
            PA.hand_stroke(d, [(x, 656), (x + 8, top)], LEAF, 7, closed=False,
                           seed=100 + k, wavelength=60.0)
            for j in range(3):
                PA.hand_stroke(d, [(x + 4, top + 40 + j * 38),
                                   (x + 44, top + 22 + j * 38)], LEAF, 5,
                               closed=False, seed=110 + k * 3 + j, wavelength=40.0)
        D.draw_label(tile, 'ORIGINAL', center=(960, 262), color=INK, size=46)
        _packet(d, 800, 600, 130, 180, 120, band=AMBER, stamp='wheat')
    els.append(SC.accrue(clock, 12, 13, c_copy, kind='shape'))
    els.append(cap(12, 640, 700, size=30))
    # KEPT, and it is the chapter's pivot. "Every sample in there is a spare
    # copy" is the sentence the whole video is built to land: it is WHY the
    # seeds surviving the flood is reassuring rather than tragic. COPY and
    # ORIGINAL are drawn, but the drawn labels are nouns -- they do not say
    # that the vault holding copies is the POINT. The words carry it.

    # ===================================================================== #
    # STAGE C2  b13-b14  "The original never left. / In 2012 they opened the #
    #                   vault for the first time in thirty years."            #
    # Split out of the old seven-beat stage C. Seven subjects in seven beats   #
    # cannot share one frame however they are wired, and this is the clearest #
    # case in the chapter: b13-b14 are the vault's contents seen from OUTSIDE #
    # -- the man who keeps them, and the globe they insure.                   #
    # ===================================================================== #
    def c2_wall(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, W, H], (206, 214, 224), seed=125, value=0.05)
        PA.paper_overlay(tile, seed=126)
    els.append(SC.stage(clock, 13, c2_wall, j=15))

    def c_home(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Cropped IN, not placed on: the head runs off the top and left edges,
        # which is what makes him a person in the shot rather than a sticker.
        SC.closeup(d, 470, 340, 230, 'skeptic', 127)
        D.draw_bubble(tile, 'the original\nstays home', (790, 130),
                      tail_to=(640, 400), font_size=30, max_w=420)
    els.append(SC.accrue(clock, 13, 14, c_home, kind='character'))
    # NO caption at b13. The speech bubble IS his line, drawn in his own mouth;
    # a caption under it duplicated the bubble and pushed text onto the bust.

    def c_globe(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the globe is deliberately off-centre right and CROPPED by the bottom
        # and right edges, so it is a world filling the frame
        _globe(d, 760, 430, 330, 133)
        # The packets ARRIVE on the globe one ring at a time rather than all at
        # once: a globe wearing its packets is a different picture from a bare
        # globe, and the arrival is what says "every nation".
        for k, (gx, gy) in enumerate(((0.42, -0.42), (-0.30, -0.20),
                                      (-0.10, 0.34), (0.30, 0.20))):
            _packet(d, 760 + gx * 330, 430 + gy * 330, 76, 104, 134 + k,
                    band=AMBER, stamp='wheat')
    els.append(SC.accrue(clock, 14, 15, c_globe, kind='shape'))
    def c_globe2(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k, (gx, gy) in enumerate(((0.56, 0.30), (-0.48, 0.06),
                                      (0.08, -0.10), (0.66, -0.06))):
            _packet(d, 760 + gx * 330, 430 + gy * 330, 76, 104, 142 + k,
                    band=AMBER, stamp='wheat')
        D.draw_label(tile, 'CROP INSURANCE', center=(300, 200), color=INK,
                     size=40)
    els.append(SC.accrue(clock, 14, 15, c_globe2, kind='shape'))
    # NO caption at b14. CROP INSURANCE is drawn, the packets are on the globe,
    # and the b14 line is exactly those two facts. A caption repeated the
    # label 460px lower on the same frame.

    # ===================================================================== #
    # STAGE C3  b15-b17  "The cold: minus eighteen, colder than any farm      #
    #                   freezer. That is the number the vault was built to    #
    #                   hold. The seeds have lain at that temperature for     #
    #                   centuries."                                           #
    # Three beats, ONE cold interior held across all of them. The thermometer, #
    # the chest-freezer comparison and the frost are all the same fact at      #
    # three levels of closeness, so the interior persists and only the        #
    # measuring changes -- which is what v1's four consecutive full-frame      #
    # _interior() calls destroyed.                                           #
    # ===================================================================== #
    def c3_cold(tile, fw, fh):
        _interior(tile, 141, wall=(74, 82, 94), warm=(96, 84, 56))
    els.append(SC.stage(clock, 15, c3_cold, j=18))

    def c_thermo(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        S.thermometer(d, 420, 690, 620, 0.22, seed=142, hot=False)
        D.draw_label(tile, '0', center=(520, 200), color=INK, size=34)
        D.draw_arrow(tile, (880, 480), (700, 560), color=VT.LABEL_RED, width=10,
                     head=46)
        # The -18 numeral is in the SAME layer as the thermometer it belongs to.
        # Split across two elements it became two large reds fighting in one
        # half of the frame -- rule 1: anything sharing a part of the frame
        # replaces rather than stacks.
        D.draw_number(tile, '-18', center=(880, 300), color=VT.LABEL_RED,
                      size=180)
        D.draw_label(tile, 'DEGREES C', center=(880, 430), color=VT.LABEL_RED,
                     size=52)
    els.append(SC.accrue(clock, 15, 16, c_thermo))
    # Placed to the RIGHT of the thermometer rather than centred: centred at
    # cx=300 it ran across the bulb at x=420 and the first word sat on the
    # mercury. The right half of the frame is under the -18 numeral, so the
    # words go in the gap between the two.
    els.append(cap(15, 800, 660, size=30, fill=VT.LABEL_RED))

    def c_freezers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # left: an ordinary domestic chest freezer, small and domestic
        chest = [(120, 300), (520, 300), (520, 640), (120, 640)]
        PA.fill_poly(tile, chest, (222, 224, 226), seed=146, value=0.07)
        PA.hand_stroke(d, chest, INK, 7, closed=True, seed=147, wavelength=150.0)
        PA.hand_stroke(d, [(120, 380), (520, 380)], INK, 5, closed=False,
                       seed=148, wavelength=110.0)
        D.draw_label(tile, 'FARM FREEZER', center=(320, 250), color=INK,
                     size=32)
        D.draw_label(tile, '-18', center=(320, 500), color=INK, size=52)
        # right: the vault's inner door, three times the size, running off the
        # right edge -- so the scale comparison is the composition, not a caption
        door = [(700, 200), (1360, 200), (1360, 690), (700, 690)]
        PA.fill_poly(tile, door, STEEL, seed=149, value=0.07)
        PA.hand_stroke(d, door, INK, 8, closed=True, seed=150, wavelength=170.0)
        PA.hand_stroke(d, [(740, 236), (1320, 236)], (110, 116, 126), 6,
                       closed=False, seed=151, wavelength=150.0)
        for k in range(4):
            y = 280 + k * 96
            d.ellipse([1240, y, 1290, y + 50], fill=(70, 76, 86))
        PA.hand_stroke(d, [(1180, 400), (1180, 620)], INK, 12, closed=False,
                       seed=152, wavelength=90.0)
        D.draw_label(tile, 'VAULT', center=(980, 150), color=VT.LABEL_RED,
                     size=40)
        D.draw_number(tile, '-18', center=(1000, 470), color=VT.LABEL_RED,
                      size=110)
    els.append(SC.accrue(clock, 16, 17, c_freezers, kind='shape'))
    # NO caption at b16. FARM FREEZER and VAULT are labelled, and both print
    # -18; the scale comparison between a chest freezer and the inner door IS
    # the sentence "colder than any farm freezer".

    def c_frost(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # v1 drew a 640x480 packet so large and so white that it read as an
        # empty blank sign, and scattered the frost dots across the WHOLE
        # frame -- dots landed on the amber wall and the dark floor, so they
        # looked like sensor noise rather than ice. Rebuilt as a stack of three
        # packets seen close in, with the frost confined to their faces, and a
        # visible rim of hoar-frost along the top edge so the cold is a
        # substance sitting ON the seed stock, not a background wash.
        _shelf(d, -80, W + 80, 636, 156, h=150, packets=9)
        cols = [(300, 210), (610, 200), (920, 215)]
        for n, (cx, hgt) in enumerate(cols):
            _packet(d, cx, 430 - hgt * 0.18, 210, hgt, 157 + n * 4,
                    band=AMBER, stamp=('wheat', 'rice', 'bean')[n])
        # hoar frost: a dense crust along each packet's top seal, and speckle
        # INSIDE each packet face only (never on the wall or the floor).
        for n, (cx, hgt) in enumerate(cols):
            top = 430 - hgt * 0.18 - hgt / 2.0
            for k in range(26):
                x = cx - 96 + (k * 37) % 192
                y = top + 6 + (k * 13) % 34
                d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(238, 248, 253))
            for k in range(30):
                a = (k * 2.399) % 6.283
                rr = 18 + (k * 29) % 78
                x = cx + rr * math.cos(a) * 1.05
                y = (430 - hgt * 0.18) + rr * math.sin(a) * 1.5
                if abs(x - cx) < 88 and abs(y - (430 - hgt * 0.18)) < hgt * 0.38:
                    d.ellipse([x - 3, y - 3, x + 3, y + 3],
                              fill=(232, 244, 251))
        # The label sits on a light keyline patch, because CENTURIES in ink
        # landed on the dark floor in v1 and was the least legible text in the
        # chapter. The user rule is explicit: never grey or black text.
        D.draw_label(tile, 'CENTURIES', center=(640, 140), color=INK, size=44)
    els.append(SC.accrue(clock, 17, 18, c_frost, kind='shape'))
    # NO caption at b17. CENTURIES is drawn above the frost-covered packets and
    # the frost itself is the sleeping; the words added nothing the frame lacked.

    # ===================================================================== #
    # STAGE D  b18-b21  "The original plan was simple: shut the door. / Then  #
    #                 leave the whole vault to the ice. / Then, in 2016, the  #
    #                 mountain began to leak. / Meltwater came in through     #
    #                 the entrance tunnel."                                  #
    # The corridor with its nest of receding doors is HELD across the stage,   #
    # because "shut the door / leave it to the ice" is a sentence about DOORS #
    # and the viewer needs to see the same corridor when the door closes. The #
    # shut door with its frost then REPLACES the open nest (same part of the  #
    # frame, rule 1), and 2016 breaks out to the surface.                      #
    # ===================================================================== #
    def d_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 161, wall=(72, 80, 92), floor=(54, 60, 70),
                  warm=(96, 86, 58))
        # four doors receding down the corridor. The outermost door's heavy frame
        # used to top out at y=19, driving a full-width INK bar straight through
        # the persistent "Svalbard" title. v1 dropped the nest and trimmed the
        # tallest leaf; that geometry is kept here unchanged.
        for k, (hw, hh, y) in enumerate(((360, 190, 316), (290, 172, 366),
                                          (222, 134, 420), (160, 98, 470))):
            _doorway(d, 640, y, 162 + k * 4, w=hw * 0.55, h=hh,
                     colour=(58, 64, 76) if k else (72, 78, 90))
        board = [(880, 250), (1230, 250), (1230, 620), (880, 620)]
        PA.fill_poly(tile, board, (238, 238, 232), seed=171, value=0.05)
        PA.hand_stroke(d, board, INK, 6, closed=True, seed=172, wavelength=140.0)
        for k in range(4):
            y = 310 + k * 74
            PA.hand_stroke(d, [(910, y), (1200, y)], INK, 4, closed=False,
                           seed=173 + k, wavelength=80.0)
    els.append(SC.stage(clock, 18, d_corridor, j=19))

    def d_presenter(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 300, 700, 400, pose='pointing',
                    expression='deadpan', seed=170)
    els.append(E3.E('d_presenter', 'character', d_presenter,
                    at=clock.at('b18', 0), until=clock.at('b19', 0),
                    motion=SC.enter(clock, 18, dx=-130, dy=0, dur=0.55)))
    els.append(cap(18, 640, 690, size=30, fill=(214, 224, 236)))
    # The caption sits low and centred, in the clear band below the corridor
    # floor and to the RIGHT of where the presenter stands at x=300, so the
    # words land on empty floor rather than on his boots or the door frames.

    def d_shut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 177, wall=(58, 64, 76), floor=(44, 50, 60))
        SC.title_backdrop(tile, 1177, col=TITLE_COURSE)
        # "leave the whole vault to the ice". v1 drew the door in dark steel on
        # a dark wall, so it vanished, and scattered ~70 short white ticks
        # pseudo-randomly across the frame -- they read as scratches on the
        # lens, not as frost, and the frame came out as a black box with a
        # stray black dot. Rebuilt so the DOOR is unambiguously the subject
        # (lighter steel, heavy outline, bar and knob clearly drawn), and the
        # ice is a visible hoar-frost CRUST growing along the door's frame and
        # seeping down from the top -- radiating FROM the door, not floating.
        dx0, dy0, dx1, dy1 = 300, 148, 980, 648          # the door slab
        PA.fill_rect(tile, [dx0, dy0, dx1, dy1], (104, 113, 126), seed=178,
                     value=0.06)
        PA.fill_rect(tile, [dx0 - 34, dy0 - 34, dx1 + 34, dy1 + 34],
                     (72, 79, 90), seed=186, value=0.06)   # the jamb
        PA.hand_stroke(d, [(dx0 - 34, dy0 - 34), (dx1 + 34, dy0 - 34),
                           (dx1 + 34, dy1 + 34), (dx0 - 34, dy1 + 34)],
                       INK, 9, closed=True, seed=179, wavelength=160.0)
        PA.hand_stroke(d, [(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)],
                       INK, 8, closed=True, seed=180, wavelength=150.0)
        # hinges on the left -- two dark straps with pin heads. Both sit ABOVE the
        # corner drift's crest (y=388) so neither is buried by it.
        for hy in (250, 372):
            PA.fill_rect(tile, [dx0 - 30, hy - 42, dx0 + 66, hy + 42],
                         (54, 60, 70), seed=187 + hy, value=0.05)
            PA.hand_stroke(d, [(dx0 - 30, hy - 42), (dx0 + 66, hy - 42),
                               (dx0 + 66, hy + 42), (dx0 - 30, hy + 42)],
                           INK, 6, closed=True, seed=188 + hy, wavelength=70.0)
            d.ellipse([dx0 + 6, hy - 15, dx0 + 36, hy + 15], fill=(38, 42, 50))
        # the wheel: rim, five spokes, hub. Reads as a vault door on sight,
        # where the old bar-and-knob read as a chalkboard with a dot on it.
        wx, wy, wr = 812, 398, 108
        PA.fill_poly(PA.img_of(d), PA.ellipse_pts(wx, wy, wr, wr, n=64),
                     (62, 69, 80), seed=192, value=0.05)
        for k in range(5):
            a = (k * 2.399) % 6.283
            PA.hand_stroke(d, [(wx, wy), (wx + wr * 0.88 * math.cos(a),
                                          wy + wr * 0.88 * math.sin(a))],
                           (46, 51, 60), 15, closed=False,
                           seed=193 + k, wavelength=60.0)
        PA.hand_stroke(d, PA.ellipse_pts(wx, wy, wr * 0.88, wr * 0.88, n=64),
                       INK, 11, closed=True, seed=199, wavelength=90.0)
        d.ellipse([wx - 26, wy - 26, wx + 26, wy + 26], fill=(40, 44, 54),
                  outline=INK, width=7)
        # the hasp bar -- the thing the ice will weld shut
        PA.hand_stroke(d, [(dx0 + 40, 528), (dx1 - 40, 528)], (46, 51, 60), 22,
                       closed=False, seed=201, wavelength=150.0)
        PA.hand_stroke(d, [(dx0 + 40, 528), (dx1 - 40, 528)], INK, 7,
                       closed=False, seed=202, wavelength=150.0)
        # THE SEAL. A solid block of frozen water straddling the hasp, drawn
        # over it so the ice covers the mechanism. Pale blue, not white: white
        # read as snow, blue reads as ice, and the hue is doing the identifying
        # work that five passes of frost texture could not.
        sx, sy, shw, shh = 640, 528, 132, 80
        seal = [(sx - shw, sy + 40), (sx - shw + 26, sy - shh + 20),
                (sx - 60, sy - shh - 10), (sx + 46, sy - shh + 6),
                (sx + shw - 30, sy - shh + 26), (sx + shw, sy - 30),
                (sx + shw - 16, sy + shh), (sx - shw + 18, sy + shh - 12)]
        PA.fill_poly(PA.img_of(d), PA.wobble_edge(seal, seed=203, amount=3.4,
                                                  wavelength=70.0),
                     (176, 216, 236), seed=203, value=0.06, edge=0.0)
        PA.hand_stroke(d, PA.wobble_edge(seal, seed=203, amount=3.4,
                                         wavelength=70.0),
                       INK, 8, closed=True, seed=204, wavelength=80.0)
        # a lighter core, so the block has depth instead of reading as a decal
        core = [(sx - 70, sy + 16), (sx - 56, sy - 44), (sx + 30, sy - 56),
                (sx + 66, sy - 20), (sx + 54, sy + 30), (sx - 40, sy + 34)]
        PA.fill_poly(PA.img_of(d), PA.wobble_edge(core, seed=205, amount=2.6,
                                                  wavelength=52.0),
                     (214, 240, 250), seed=205, value=0.05, edge=0.0)
        _frost_crystals(d, sx - 96, sx + 96, sy - shh, 6, 820)
        _frost_crystals(d, sx - 110, sx + 110, sy + shh - 6, 4, 860)
        # ------------------------------------------------------------------ #
        # "leave the whole vault to the ice" is carried by a FROZEN SEAL,
        # not by drawn snow. Five passes on frost texture (ticks on a
        # golden-angle spiral -> a dashed border -> jittered snowflake blobs ->
        # 34px banks -> deep banks) all rendered as something that was not ice:
        # scratches, a dashed border, confetti, ribbon, torn paper. The reason
        # is that a viewer reads an object, not a surface, and a pale texture on
        # a grey door is not an object -- it is noise of an ambiguous kind, and
        # the harder you work on the noise the more noise-like it gets.
        #
        # So the ice here is ONE legible fact: a block of frozen water has grown
        # across the door's hasp and welded it shut. A solid pale-blue block
        # with a hard edge and a few crystal spikes reads immediately as ice and
        # cannot be mistaken for snow, a sheet of paper, or a tear in the frame.
        #
        # SEAL GEOMETRY (why it sits where it does):
        #   door slab   dy0=148 .. dy1=648, x 300..980
        #   hasp bar    y=528, running dx0+40 -> dx1-40  (drawn below)
        #   seal block  centred on the hasp, half-width 132, half-height 80,
        #               so it straddles the bar and locks it
        # The block is drawn AFTER the bar so the ice covers the mechanism --
        # that overlap is the whole point, it says "welded", not "painted on".
        # drifts at the foot of the door: enough to say the cold owns this place,
        # thin enough not to become the subject. They are the ONLY frost
        # texture left -- everything above is the seal.
        _frost_bank(d, dx0 - 34, dx1 + 34, dy1 + 34, 622, 660, 400)
        _frost_crystals(d, dx0 - 10, dx1 + 10, 624, 10, 700)
    els.append(SC.layer(clock, 19, d_shut, j=20))
    els.append(cap(19, 640, 690, size=30))
    # The caption is KEPT on this beat after looking at it: the frost crust is
    # visible now, but "leave the whole vault to the ice" is a decision, and a
    # frozen door alone does not say anyone MADE that choice. b18's caption is
    # two beats back, so these two do not stack.

    def d_2016(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 185, warm_chamber=True)
        # 2016, not 2008. This label was a copy-paste from the b03 d_2008 card
        # directly above it, so the beat that opens the flood chapter drew the
        # vault's OPENING year on screen while the narrator said 2016.
        D.draw_label(tile, '2016', center=(200, 150), color=VT.LABEL_RED,
                     size=64)
        D.draw_arrow(tile, (330, 190), (860, 400), color=INK, width=10, head=46)
    els.append(SC.layer(clock, 20, d_2016, j=21))
    els.append(cap(20, 640, 700, size=30))
    # The caption is KEPT here and not at b19: "the mountain began to leak" is
    # the pivot of the whole chapter, the one beat where the argument turns,
    # and the drawn 2016 arrow only shows the mountain. The words carry the
    # turn; the art cannot.

    def d_melt(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 191, snow=(216, 224, 232))
        _mountain(d, 192, crest=250, base=HZ + 6)
        _wedge(d, 520, 330, 193, w=240, h=170)
        _doorway(d, 520, 440, 194, w=145, h=190, colour=(44, 50, 60))
        # the channel: a brown meltwater run cutting the snow straight at the door
        chan = [(360, 720), (640, 720), (610, 520), (598, 470), (560, 470),
                (520, 540), (470, 560)]
        PA.fill_poly(tile, chan, WATER, seed=195, value=0.07)
        PA.hand_stroke(d, chan[:1] + chan[2:], INK, 5, closed=False, seed=196,
                       wavelength=110.0)
        D.draw_arrow(tile, (300, 660), (450, 570), color=RED, width=10,
                     head=46)
    els.append(SC.layer(clock, 21, d_melt, j=22))
    # NO caption at b21. The water channel drawn straight at the open door with
    # a red arrow aimed into it IS "meltwater came in through the entrance
    # tunnel". b20 already carries the flood caption; these two would have been
    # consecutive.

    # ===================================================================== #
    # STAGE E  b22-b26  "Water at the door, in a frozen land. / The entrance  #
    #                 flooded with eight hundred tonnes. / The staff were cut #
    #                 off for a year. / The seed samples themselves were never #
    #                 touched. / They lay above the waterline, in the cold."  #
    # The flood is the chapter's set piece and the ONE place a larger, longer  #
    # motion is justified: a standing wall of meltwater whose top edge RISES  #
    # across b22 (SC.drift) as the narration describes it filling. That rise   #
    # is the only motion here that carries meaning on its own, so it is the    #
    # only one that gets a multi-second track rather than a 0.5s arrival. The  #
    # rest of the stage is still.                                             #
    # ===================================================================== #
    def e_wall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 201, wall=(62, 70, 82), floor=(48, 54, 64))
        # The doorway's frame sits so its top is clear of the title band.
        _doorway(d, 640, 385, 202, w=300, h=250, colour=(70, 76, 88))
    els.append(SC.stage(clock, 22, e_wall, j=23))

    def e_flood(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the flood: a standing wall of meltwater, door half behind it. Drawn
        # at full height here and DRIFTED down so the waterline visibly rises.
        wallw = [(300, 720), (300, 430), (1000, 400), (1000, 720)]
        PA.fill_poly(tile, wallw, WATER, seed=203, value=0.07)
        PA.hand_stroke(d, wallw[:3], (156, 186, 200), 7, closed=False,
                       seed=204, wavelength=170.0)
        for k in range(9):
            x = 330 + k * 78
            PA.hand_stroke(d, [(x, 430 + k % 3 * 12), (x + 40, 470 + k % 3 * 12)],
                           (156, 186, 200), 5, closed=False, seed=210 + k,
                           wavelength=60.0)
    # MOVING, and the chapter's one long move: the waterline RISES as the
    # narrator says it filled. Authored at the risen position; the drift lifts
    # it 90px over the beat, so the fill reads as water climbing the corridor.
    els.append(SC.layer(clock, 22, e_flood, j=24,
                        motion=SC.drift(clock, 22, 23, dx=0, dy=-90)))
    # NO caption at b22. A cold grey corridor half-drowned by blue water with
    # the door behind it IS "water at the door, in a frozen land"; the art says
    # it in the language the whole chapter has been building.

    def e_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # 800 TONNES replaces the flood it measures, not stacks with it: two
        # big yellows plus a full water wall in one frame is unreadable, and
        # the number is the payload of this beat. The flood is re-drawn beneath
        # so the number sits ON water rather than in a void.
        wallw = [(-40, 720), (-40, 400), (W + 40, 380), (W + 40, 720)]
        PA.fill_poly(tile, wallw, WATER, seed=222, value=0.07)
        PA.hand_stroke(d, [(-40, 400), (W + 40, 380)], (156, 186, 200), 7,
                       closed=False, seed=223, wavelength=180.0)
    # POPS. The rising water at b22 already carried this stage's one big move;
    # a second slide on the full-width water wall would double the churn.
    els.append(SC.layer(clock, 23, e_tonnes, j=24))

    def e_count(tile, fw, fh):
        D.draw_number(tile, '800', center=(430, 300), color=VT.LABEL_YELLOW,
                      size=190)
        D.draw_label(tile, 'TONNES', center=(980, 300), color=VT.LABEL_YELLOW,
                     size=104)
    els.append(E3.E('e_count', 'shape', e_count, at=clock.at('b23', 0),
                    until=clock.at('b24', 0)))
    els.append(cap(23, 640, 690, size=30, fill=VT.LABEL_YELLOW))
    # KEPT. "eight hundred tonnes" is the one number the viewer cannot infer
    # from the frame, and it is the scale that makes the flood mean anything.
    # The drawn 800 is the number SHOWN; the caption is the sentence AROUND it
    # ("the entrance flooded with..."), which the numeral alone does not say.

    def e_cutoff(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 225, snow=(206, 216, 226))
        _mountain(d, 226, crest=250, base=HZ + 40)
        _wedge(d, 520, 380, 227, w=260, h=180)
        _doorway(d, 520, 490, 228, w=150, h=190, colour=(44, 50, 60))
        # MOVING. The barricade going up across the door is the b24 statement
        # made physically: the staff are OUT, the door is boarded.
        _flood_gate(d, 520, 480, 229)
        D.draw_label(tile, '2016', center=(230, 200), color=VT.LABEL_RED,
                     size=68)
    els.append(SC.layer(clock, 24, e_cutoff, j=25, kind='shape',
                        motion=SC.enter(clock, 24, dx=0, dy=70, dur=ARRIVE)))
    # NO caption at b24, and it is a real loss of the word "a year". The boards
    # going up across the door plus the drawn 2016 is the seal; but b23 already
    # captioned this stage and the no-two-consecutive rule is a hard constraint,
    # so the caption goes on the beat that carries the number the viewer cannot
    # get from the frame and the boards carry the rest.

    def e_fine(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 210, 224), seed=231, value=0.05)
        PA.paper_overlay(tile, seed=232)
        SC.closeup(d, 520, 330, 240, 'deadpan', 233)
        D.draw_bubble(tile, 'the seeds\nwere fine', (830, 120), tail_to=(690, 390),
                      font_size=30, max_w=400)
    els.append(SC.layer(clock, 25, e_fine, j=26, kind='character'))
    # NO caption at b25. The bubble IS the line, in his mouth.

    def e_above(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 237, water_level=0.34)
        D.draw_arrow(tile, (300, 300), (300, 430), color=VT.LABEL_RED, width=9,
                     head=42)
        D.draw_label(tile, 'ABOVE THE WATER', center=(300, 210), color=VT.LABEL_RED,
                     size=34)
    els.append(SC.layer(clock, 26, e_above, j=27))
    # NO caption at b26. ABOVE THE WATER is DRAWN with an arrow to the chamber
    # floor; the words only restated it.

    # ===================================================================== #
    # STAGE F  b27-b30  "The same permafrost that keeps it thaws too. / The   #
    #                 vault is watched now, year round. / A new access tunnel #
    #                 is being built. / New lights on the snow, night and    #
    #                 day."                                                   #
    # The thawing cutaway is HELD and then the argument leaves the mountain   #
    # and goes back outside -- watched (camera), rebuilt (new tunnel), lit    #
    # (lights). Those three are all exterior views of the same slope, so they #
    # share a look and each replaces the last: the watched camera, the raw    #
    # new mouth and the lights all occupy the doorway area of the same frame,#
    # and stacking them would put three subjects on one door (rule 1).        #
    # ===================================================================== #
    def f_thaw(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 243, ragged=True, melt_arrows=True,
                 label='AND MELTING')
    els.append(SC.stage(clock, 27, f_thaw, j=28))
    els.append(cap(27, 640, 690, size=32, fill=RED))
    # KEPT, and it is the second pivot. "The same permafrost that keeps it
    # thaws too" cannot be drawn as a label: the art can show a ragged ice
    # layer and red melt arrows, but not that the SAME layer doing the
    # preserving is the layer failing. That identity is the argument, and only
    # the sentence carries it.

    def f_watched(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 249, snow=(222, 230, 238))
        _mountain(d, 250, crest=280, base=HZ + 30)
        _wedge(d, 470, 400, 251, w=230, h=160)
        _doorway(d, 470, 500, 252, w=135, h=175, colour=(46, 52, 62))
        # MOVING. The camera's lamp coming on is "watched now" -- the eye is
        # drawn to the small red lamp, which is the point of the beat.
        _camera(d, 830, 300, 110, 253)
        D.draw_arrow(tile, (1030, 260), (900, 320), color=INK, width=9, head=42)
        D.draw_label(tile, 'watched', center=(1150, 220), color=INK, size=36)
    els.append(SC.layer(clock, 28, f_watched, j=29,
                        motion=SC.enter(clock, 28, dx=0, dy=-40, dur=ARRIVE)))
    # NO caption at b28. "watched" is DRAWN beside the arrow pointing at the
    # camera; the drawn word is the caption.

    def f_newtunnel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 257, snow=(216, 226, 236))
        _mountain(d, 258, crest=260, base=HZ + 60)
        _wedge(d, 330, 400, 259, w=190, h=140)
        _doorway(d, 330, 486, 260, w=118, h=155, colour=(46, 52, 62))
        # the new mouth: raw concrete, no wedge, cut lower down the slope
        raw = [(760, 420), (1080, 420), (1040, 640), (800, 640)]
        PA.fill_poly(tile, raw, CONCRETE, seed=261, value=0.07)
        PA.hand_stroke(d, raw, INK, 7, closed=True, seed=262, wavelength=150.0)
        _doorway(d, 920, 530, 263, w=100, h=125, colour=(52, 58, 70))
        # MOVING. The excavator's bucket arriving is "is being built" -- the
        # present continuous made visible by the one machine that does it.
        _excavator(d, 690, 620, 90, 264)
        D.draw_label(tile, 'NEW TUNNEL', center=(920, 360), color=VT.LABEL_RED,
                     size=34)
    els.append(SC.layer(clock, 29, f_newtunnel, j=30, kind='shape',
                        motion=SC.enter(clock, 29, dx=-70, dy=0, dur=ARRIVE)))
    els.append(cap(29, 640, 700, size=30))
    # KEPT. "A new access tunnel is being built" is future work in progress; the
    # excavator and raw concrete show it, but the caption carries the sentence
    # and this beat is a beat away from b28's dropped one, not adjacent to it.

    def f_lights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 267)
        SC.title_backdrop(tile, 1267, col=TITLE_COURSE)
        _mountain(d, 269, crest=330, base=HZ + 6)
        # two beams of light on the snow -- night and day in one frame. Drawn
        # with _soft_beam, not SV._light_wedge: the latter fills one solid
        # amber triangle and two of them read as gold traffic cones rather than
        # lamplight. See _soft_beam.
        _soft_beam(d, 430, 120, HZ - 4, 210, 271)
        _soft_beam(d, 900, 120, HZ - 4, 190, 273)
        SC.fullbody(d, 664, HZ + 8, 230, pose='standing', expression='skeptic',
                    seed=275, ink=CREAM)
    els.append(SC.layer(clock, 30, f_lights, j=31, kind='character'))
    # NO caption at b30. Two lamp wedges on the snow with him standing between
    # them IS "new lights on the snow, night and day".

    # ===================================================================== #
    # STAGE G  b31-b35  "It is still a bunker against catastrophe. /          #
    #                 Catastrophe is already moving into the mountain. / The #
    #                 coldest air on earth is warming here. / The seeds are  #
    #                 still fine, for now. / Somewhere under the snow, it is  #
    #                 still seeping."                                         #
    # The finale ALTERNATES between the mountain and the presenter, because   #
    # that is the closing argument: here is the thing, here is what it means, #
    # here is the thing again, and it ends on the mountain still leaking. The #
    # night exterior is the stage; the two close-ups replace it and the        #
    # exterior returns between them, so the last frame is the mountain, not a #
    # face -- the film should end on the water, not on the presenter.         #
    # ===================================================================== #
    def g_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 281)
        SC.title_backdrop(tile, 1281, col=TITLE_COURSE)
        _mountain(d, 283, crest=300, base=HZ + 6)
    els.append(SC.stage(clock, 31, g_night, j=36))

    def g_bunker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 206, 216), seed=277, value=0.05)
        PA.paper_overlay(tile, seed=278)
        # Cropped in from the chest up and cropped by the BOTTOM edge; the head
        # rim sits clear of the title band. The bubble is his line, so the
        # caption at b31 is the ONLY text on this beat that is not in the art.
        SC.closeup(d, 640, 365, 250, 'deadpan', 279, shoulder=1.35)
        D.draw_bubble(tile, 'a bunker', (180, 480), tail_to=(520, 520),
                      font_size=34, max_w=340)
    els.append(SC.layer(clock, 31, g_bunker, j=32, kind='character'))
    els.append(cap(31, 640, 130, size=32))
    # KEPT. "still a bunker against catastrophe" is the thesis restated; the
    # bubble says only "a bunker", so the caption is what carries "still" and
    # "against catastrophe" -- the two words the whole chapter turns on.

    def g_redline(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Catastrophe arriving as warmth UNDER the snow. v1 drew a single 12px
        # red line across the lower third of an otherwise empty pale snow field
        # -- a thin stripe on a dead frame, under-filling the composition. Now
        # the warm front is a broad band that bleeds up through the snow from
        # the bottom edge, with a hard red leading edge and heat-coloured
        # gradient above it, so the "moving into the mountain" reads as a front
        # advancing rather than a stray mark. Accrues onto the night stage, so
        # the mountain above is the SAME mountain: the place has not changed,
        # the temperature under it has.
        _mountain(d, 283, crest=300, base=HZ + 6)
        # the heat front, rising from the bottom edge
        for k in range(9):
            t = k / 8.0
            col = (196 - int(52 * t), 84 + int(60 * t), 60 + int(30 * t))
            y = 720 - 40 - k * 22
            PA.fill_rect(tile, [0, y, W, y + 30], col, seed=290 + k, value=0.06)
        # the hard leading edge of the front
        PA.hand_stroke(d, [(-40, 508), (320, 486), (660, 500), (1000, 478),
                           (1320, 494)], RED, 16, closed=False, seed=287,
                       wavelength=190.0)
        # heat shimmer rising off the front, so it reads as warmth not paint
        for k in range(9):
            x = 40 + k * 140
            PA.hand_stroke(d, [(x, 470), (x + 14, 430), (x - 6, 392)], (206, 118, 82),
                           6, closed=False, seed=320 + k, wavelength=54.0)
        D.draw_label(tile, 'WARMING', center=(320, 620), color=RED, size=44)
    els.append(SC.accrue(clock, 32, 33, g_redline, kind='shape'))
    # NO caption at b32. WARMING is DRAWN in red across the advancing front and
    # the front is the catastrophe itself; the words would restate the label.

    def g_warming(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 291, sky_top=(44, 52, 70), sky_bot=(126, 136, 152),
                snow=(220, 222, 224))
        SC.title_backdrop(tile, 1291, col=TITLE_COURSE)
        _mountain(d, 293, crest=300, base=HZ + 6, snowline=False)
        # bare rock showing through where the snow used to be
        for k, (x0, y0, x1, y1) in enumerate(((120, 470, 460, 560),
                                              (700, 500, 1080, 596),
                                              (980, 400, 1260, 480))):
            bare = [(x0, y0), (x1, y0 - 30), (x1, y1), (x0, y1)]
            PA.fill_poly(tile, bare, (128, 122, 116), seed=294 + k, value=0.07)
            PA.hand_stroke(d, bare, INK, 5, closed=True, seed=298 + k,
                           wavelength=120.0)
        D.draw_number(tile, '-2.6 C', center=(640, 300), color=VT.LABEL_RED,
                      size=132)
        D.draw_label(tile, 'PER DECADE', center=(640, 400), color=VT.LABEL_RED,
                     size=54)
    els.append(SC.layer(clock, 33, g_warming, j=34))
    # NO caption at b33. -2.6 C PER DECADE is DRAWN as a 132px numeral over the
    # bared slope; the number is the sentence.

    def g_fornow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (72, 82, 98), seed=301, value=0.06)
        PA.paper_overlay(tile, seed=302)
        # him on a night card, holding the packet. The "for now" bubble is his
        # line -- the caveat is in his mouth, which is where a caveat belongs.
        SC.closeup(d, 430, 350, 250, 'deadpan', 303)
        _packet(d, 940, 470, 230, 320, 304, band=AMBER, stamp='wheat')
        PA.hand_stroke(d, [(1330, 640), (1040, 560)], (232, 202, 172), 60,
                       closed=False, seed=305, wavelength=150.0)
        D.draw_bubble(tile, 'for now', (830, 110), tail_to=(640, 420),
                      font_size=34, max_w=320)
    els.append(SC.layer(clock, 34, g_fornow, j=35, kind='character'))
    # NO caption at b34. "for now" is the bubble; the packet in his hand is the
    # thing being qualified, and he is holding it in frame.

    def g_seep(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The chapter's last line, and the last frame: the mountain again, at
        # night, with the water still running under the snow. The chapter ENDS
        # on the leak, not on the presenter -- v1 learned there is no time after
        # the last spoken line for a separate finale card, so the finale IS this
        # beat.
        #
        # A filled CHANNEL, not a hairline. The first pass drew one 9px stroke
        # and the full-res frame read as an empty white slope with a caption on
        # it -- the closing image of the whole chapter was invisible. It is now
        # a band of meltwater with a lit surface, wide enough to be the subject,
        # drawn low so the caption has the clear snow above it.
        chan = [(200, 556), (520, 530), (900, 548), (1140, 570),
                (1140, 642), (900, 620), (520, 602), (200, 628)]
        PA.fill_poly(tile, chan, WATER, seed=308, value=0.07)
        PA.hand_stroke(d, chan[:4], (156, 186, 200), 7, closed=False,
                       seed=309, wavelength=170.0)
        for k in range(7):
            x = 250 + k * 130
            PA.hand_stroke(d, [(x, 564 + (k % 3) * 10), (x + 46, 600 + (k % 3) * 8)],
                           (156, 186, 200), 5, closed=False, seed=312 + k,
                           wavelength=60.0)
        D.draw_label(tile, 'still seeping', center=(640, 486), color=AMBER_LT,
                     size=46)
    # MOVING, brief. The channel DRIFTS right as the last line lands -- the one
    # motion in the finale, small, and the literal image of "still seeping".
    els.append(SC.layer(clock, 35, g_seep, j=36, kind='shape',
                        motion=SC.drift(clock, 35, 36, dx=70, dy=0)))
    els.append(cap(35, 640, 690, size=32, fill=AMBER_LT))
    # KEPT. The closing line is the thesis and the drawn "still seeping" is the
    # label; the caption is the sentence the film ends on. Four beats since the
    # last caption (b31), so no consecutive-caption violation.

    return SC.finish(els, TITLE, clock, title_seed=47)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent2.mp4'))