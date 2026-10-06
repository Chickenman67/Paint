"""svalbard2_scene -- the PERSISTENT-STAGE rebuild of chapter 8 (svalbard).

WHAT CHANGED AND WHY. The previous build of this file already wrapped its beats
in SC.stage(), but almost every beat inside those stages was a full-frame
SC.layer() that repainted the entire composition at that beat's onset. Measured
on the built scene: 23 REFRAME hits (a subject onset that repaints >30% of the
frame) and a median gap between full-frame repaints of 2.84s. That is the viewer's
complaint exactly -- "every sentence has a cut with a completely new image" -- and
the structural measurements agreed with it.

THE MODEL. A STAGE paints the whole persistent world for a run of beats and is
registered with kind='bg', so its onset is a legitimate cut to a new place (the
gate skips 'bg' onsets). Every beat INSIDE a stage then ACCRUES one element that
covers well under 30% of the frame, so nothing inside a stage reads as a new
image. A stage spans 3-6 beats; the median repaint gap becomes the median stage
length. The measured result after this rebuild is in the module's own build log.

FOURTEEN stages, grouped on the narration's own acts and on what can share
one frame without crowding (memory: blind-critic-loss-pattern-over-populated).
The count is fourteen because S8 is drawn as two stages -- the freezer and then
the corridor are different places and cannot share a frame -- so the S-LABEL
count and the STAGE count differ by one. That mismatch is what made an earlier
version of this docstring claim "thirteen stages" while listing fourteen calls:

    S1  b01-b03  the mountain at night; the vault's name; it opened in 2008
    S2  b04-b06  the rock in cross-section; the tunnel; the hall cut into the ice
    S3  b07      above the doorway the midsummer sun barely rises
    S4  b08-b10  the cold room; one packet; a million samples
    S5  b11-b12  the crop deck; every sample is a spare copy
    S6  b13-b14  the keeper, and the globe the samples insure
    S7  b15      minus eighteen
    S8a b16-b17  a farm freezer; centuries in the cold
    S8b b18-b19  the corridor; then the hasp frozen shut
    S9  b20-b21  the mountain leaks in 2016; meltwater at the entrance
    S10 b22-b25  the flood rises; eight hundred tonnes; the barricade; 'fine'
    S11 b26-b27  above the waterline; and the same ice thawing
    S12 b28-b30  watched; a new tunnel; lights on the snow
    S13 b31-b35  one night mountain that ACCUMULATES: the bunker, the warm front,
                 the bared slope and -2.6, then him and "for now", then the
                 channel. Nothing here is ever replaced.

The finale (S13) is the clearest case of the model: it was five unrelated
full-frame cards -- two close-ups, a re-drawn mountain, a bare warming slope --
and is now ONE night mountain held for thirteen seconds while the presenter
arrives, a heat front advances, the snow bares, he comes back holding a packet
AND STAYS while the meltwater channel drifts open beside him. That is the
"something MOVES and APPEARS inside a stage the viewer can settle on" the brief
asks for, and holding him through the last beat is what stops the chapter from
getting quieter exactly where it should be loudest.

WHAT IS DELIBERATELY NOT DONE. No art primitive is redrawn and no caption is
shortened or reworded -- every caption is still clock.ph() straight out of
segments/svalbard/beats.json. Where a beat's art cannot share a frame with its
neighbour (the b03 map, the b19 vault-door close-up, the b25 talking head), that
beat either became its own bg stage or was re-composed from the SAME primitives
onto its stage's world, and the comment at the call site says which. Captions
stay only on the beats that carry a fact the drawn art does not -- the b35
caption was removed precisely because it repeated a label already drawn in the
frame, which is the tell-AND-show redundancy the brief is written against.

Rule 5 (the engine stamps the title LAST): this file never draws scene.title.
Rule 7 (engine3._apply_transform moves an element's own tile, never the frame):
every arrival here uses motion=, never a redraw, so nothing drags a sibling.

Run:  python lib/svalbard2_scene.py --preview --video
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

# palette, reused from v1.
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
# ICE and SLATE are the permafrost's own two values; the thaw beat re-draws the
# frozen band in place so the corridor it sits over is the SAME corridor.
ICE = SV.ICE
SLATE = SV.SLATE

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
_snow_hatch = SV._snow_hatch
_excavator = SV._excavator
_flood_gate = SV._flood_gate
_light_wedge = SV._light_wedge


def _soft_beam(d, x, y0, y1, half, seed, colour=None):
    """A wedge of LIGHT, not a gold cone.

    SV._light_wedge fills one solid AMBER_LT triangle, which on the dark
    exterior reads as an opaque pyramid -- two of them at b30 looked like
    traffic cones. This draws the beam as nested triangles from widest and
    dimmest to narrowest and brightest, plus a bright pool where it lands, so
    it reads as light spreading out of a lamp rather than a solid shape.

    Kept from the previous pass. It is a STAGE-WORLD element, not a layer: a
    wedge this wide covers a lot of the frame, so it belongs in the world that
    a stage paints rather than arriving on top of one.
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


def _frost_bank(d, x0, x1, ybase, lo, hi, seed, colour=(233, 243, 250),
                step=132.0):
    """A bank of ICE as a filled mass with a soft, uneven upper boundary.

    Kept from the previous pass, unchanged. Frost that does not CONNECT does not
    read as a substance, so this fills a bank from a solid base up to a crest,
    and the crest is a three-octave wobble (a sawtooth reads as a sawblade).
    """
    pts = [(x0, ybase), (x1, ybase)]
    steps = max(4, int((x1 - x0) / step))
    span = float(hi - lo)
    for s in range(steps + 1):
        u = s / float(steps)
        px = x0 + (x1 - x0) * u
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
    blob, which at 60-odd blobs became a field of snowflakes; hoar grows in a
    few directions from a few nucleation points, so these are longer than they
    are numerous and none of them share an angle.
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


# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and the element stops being an arrival and starts
# being the picture changing every sample.
ARRIVE = 0.5

# REFRAME_MAX is 0.30 of the frame. These are the coverage budgets the details
# in this file were sized against, measured as (bounding box area / 1280*720).
# A detail over the budget reads to the viewer as a new picture even though the
# stage held, which is exactly the defect the previous build had 23 of.
DETAIL_BUDGET = 0.30


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
    # STAGE S1  b01-b03  "Beneath an Arctic mountain, the world's seeds      #
    #                    sleep. / This is the Svalbard Global Seed Vault. /   #
    #                    It opened in 2008, on a Norwegian island."          #
    # The night exterior is the WORLD and it is held for all three beats.     #
    # Three things arrive inside it: the presenter walks in from the right, the #
    # vault's name is stamped across the sky, and 2008 lands on the peak.      #
    # Previously b03 was a full-frame MAP that repainted 91% of the frame --   #
    # a cut to a different picture on the beat that says "2008". The map is    #
    # gone; what carries the year now is the drawn numeral plus the caption,  #
    # which is the one thing a mountain cannot draw.                          #
    # ===================================================================== #
    def s1_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 5)
        SC.title_backdrop(tile, 1005, col=TITLE_COURSE)
        _mountain(d, 7, crest=300, base=HZ + 6)
        _soft_beam(d, 760, 120, HZ - 4, 190, 9)
    els.append(SC.stage(clock, 1, s1_night, j=4))

    def s1_presenter(tile, fw, fh):
        # Small against a big mountain on purpose: he is a person looking at a
        # mountain, which is the whole relationship in one frame. dx only, no
        # dy -- SC.enter renders at its START offset, so a vertical offset
        # would put his feet below the snow line for the length of the move.
        SC.fullbody(ImageDraw.Draw(tile), 1150, HZ + 4, 190, pose='standing',
                    expression='deadpan', seed=11, ink=CREAM)
    els.append(E3.E('s1_presenter_a', 'character', s1_presenter,
                    at=clock.at('b01', 0), until=clock.at('b02', 0),
                    motion=SC.enter(clock, 1, dx=150, dy=0, dur=0.55)))

    def s1_presenter_b(tile, fw, fh):
        # Same man, same spot, awed instead of blank. The expression is baked
        # into the rasterised tile, so a change is two elements whose windows
        # abut exactly (SC.expr_swap).
        SC.fullbody(ImageDraw.Draw(tile), 1150, HZ + 4, 190, pose='standing',
                    expression='awed', seed=11, ink=CREAM)
    _s1u, _s1a, _s1au = SC.expr_swap(clock, 2, 'deadpan', 'awed', until_j=4)
    els.append(E3.E('s1_presenter_b', 'character', s1_presenter_b,
                    at=_s1a, until=_s1au))
    els.append(cap(1, W // 2, 690, size=32, fill=AMBER_LT))

    def s1_stamp(tile, fw, fh):
        # The vault's name, stamped across the sky. It IS the b02 line, so
        # there is NO caption on b02: a caption under a hand-stamped name is
        # the same words twice, printed on top of each other.
        D.draw_label(tile, 'SVALBARD', center=(640, 148), color=VT.LABEL_YELLOW,
                     size=86)
        D.draw_label(tile, 'GLOBAL SEED VAULT', center=(640, 238),
                     color=VT.LABEL_YELLOW, size=44)
    els.append(SC.accrue(clock, 2, 4, s1_stamp, kind='shape'))

    def s1_opened(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # 2008, on the peak, with the ring that says "here". This is the whole
        # b03 subject now that the map is gone; the caption beside it carries
        # what a mountain still cannot draw ("on a Norwegian island").
        D.draw_number(tile, '2008', center=(392, 196), color=VT.LABEL_RED,
                      size=92)
        d.ellipse([556, 214, 596, 254], fill=RED)
        D.draw_arrow(tile, (500, 300), (572, 262), color=RED, width=8, head=38)
    els.append(SC.accrue(clock, 3, 4, s1_opened, kind='shape',
                         motion=SC.enter(clock, 3, dx=-60, dy=0, dur=ARRIVE)))
    els.append(cap(3, 640, 690, size=30, fill=(214, 224, 236)))

    # ===================================================================== #
    # STAGE S2  b04-b06  "A long tunnel runs down into the rock. / The rock   #
    #                    there is permafrost, frozen for millennia. / The      #
    #                    vault is cut straight into that ice."               #
    # The cutaway IS the world now. It used to be a b05 replacement card that  #
    # repainted 71% of the frame on top of a bare interior; here it is the    #
    # bg the stage paints, so it persists, and the three beats add only small  #
    # things to it: where the tunnel goes in, who is pointing at the frozen   #
    # band, and the warm light in the hall once it is cut.                     #
    # ===================================================================== #
    def s2_cut(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 37, label='PERMAFROST')
    els.append(SC.stage(clock, 4, s2_cut, j=7))

    def s2_entry(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The mouth, at the left face where the corridor enters the mountain.
        # The cutaway already draws the hall running in from the left; this
        # gives it a mouth in the rock, which is what "runs down into the
        # rock" actually points at.
        _doorway(d, 96, 470, 38, w=64, h=78, colour=(44, 50, 60))
        PA.hand_stroke(d, [(150, 470), (300, 470)], (150, 180, 196), 5,
                       closed=False, seed=39, wavelength=90.0)
    els.append(SC.accrue(clock, 4, 5, s2_entry, kind='shape'))
    els.append(cap(4, 640, 690, size=30, fill=VT.LABEL_YELLOW))

    def s2_presenter(tile, fw, fh):
        # Pointing at the frozen band, standing ON the snow at the left edge so
        # his feet are on the surface rather than inside the diagram.
        SC.fullbody(ImageDraw.Draw(tile), 250, 706, 300, pose='pointing',
                    expression='awed', seed=43)
    els.append(SC.accrue(clock, 5, 6, s2_presenter, kind='character',
                         eid='s2_presenter',
                         motion=SC.enter(clock, 5, dx=-150, dy=0, dur=ARRIVE)))
    # NO caption at b05. PERMAFROST is drawn across the frozen band in the stage
    # world; a caption under it repeated the label and stacked text on the
    # hatching.

    def s2_chamber(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The hall goes warm: the light is the only thing that arrives, which is
        # what "cut straight into that ice" looks like. A glow pool plus three
        # stocked shelves inside the chamber -- about a tenth of the frame.
        PA.fill_poly(tile, PA.ellipse_pts(1080, 470, 186, 148, n=56),
                     AMBER_LT, seed=71, value=0.05)
        for k in range(3):
            _shelf(d, 1000 + k * 78, 1080 + k * 78, 470 + k * 18, 72 + k,
                   h=64, packets=2)
        D.draw_label(tile, 'VAULT', center=(1120, 620), color=VT.LABEL_RED,
                     size=44)
    els.append(SC.accrue(clock, 6, 7, s2_chamber, kind='shape',
                         motion=SC.enter(clock, 6, dx=0, dy=-30, dur=ARRIVE)))
    els.append(cap(6, 640, 132, size=32, fill=VT.LABEL_YELLOW))

    # ===================================================================== #
    # STAGE S3  b07  "Above the doorway, the midsummer sun barely rises."     #
    # The only beat that cannot share a frame: it is a different place (the   #
    # surface, in daylight) and a different register from the cross-section   #
    # on either side of it. So it is its own bg stage, and the sun is a       #
    # DETAIL that rises into it rather than a whole card that pops.           #
    # ===================================================================== #
    def s3_day(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 45)
        _mountain(d, 46, crest=270, base=HZ + 6)
        # ONE portal: a lit opening in a concrete face on the LEFT, so "above
        # the doorway" has a referent. v1 stacked _wedge on _doorway here and
        # the wedge's underside cut through the lintel.
        px, py = 330, 452
        PA.fill_rect(tile, [px - 190, py - 210, px + 190, py + 150], CONCRETE,
                     seed=50, value=0.07)
        PA.hand_stroke(d, [(px - 190, py - 210), (px + 190, py - 210),
                           (px + 190, py + 150), (px - 190, py + 150)], INK, 8,
                       closed=True, seed=51, wavelength=150.0)
        PA.fill_rect(tile, [px - 82, py - 118, px + 82, py + 150], (44, 48, 58),
                     seed=52, value=0.06)
        PA.fill_poly(tile, PA.ellipse_pts(px, py + 40, 66, 96, n=44),
                     (198, 152, 74), seed=53, value=0.06)
        PA.hand_stroke(d, [(px - 82, py - 118), (px + 82, py - 118),
                           (px + 82, py + 150), (px - 82, py + 150)], INK, 7,
                       closed=True, seed=54, wavelength=140.0)
    els.append(SC.stage(clock, 7, s3_day, j=8))

    def s3_sun(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # MOVING, and the sentence. "Barely rises" is a sun that clears the
        # skyline by a little; the halo, the disc and the word arrive from 30px
        # BELOW the horizon and rise to it over half a second. Authored at the
        # risen position, so the track's start offset is the dip.
        halo = PA.ellipse_pts(1010, HZ + 6, 158, 96, n=56)
        PA.fill_poly(tile, halo, AMBER_LT, seed=47, value=0.04)
        disc = PA.ellipse_pts(1010, HZ + 6, 64, 64, n=48)
        PA.fill_poly(tile, disc, AMBER, seed=48, value=0.05)
        PA.hand_stroke(d, disc, INK, 5, closed=True, seed=49, wavelength=90.0)
        D.draw_label(tile, 'midsummer', center=(1010, HZ - 130), color=INK,
                     size=38)
    els.append(SC.accrue(clock, 7, 8, s3_sun, kind='shape',
                         motion=SC.enter(clock, 7, dx=0, dy=30, dur=ARRIVE)))
    # NO caption at b07. The drawn word "midsummer" sits directly above the
    # drawn sun at the height it happens at -- a caption would repeat it.

    # ===================================================================== #
    # STAGE S4  b08-b10  "Down inside, the seeds sleep in the cold. / The    #
    #                    seeds are packed into small foil packets. / Around a  #
    #                    million samples, from a hundred nations."           #
    # The cold room is the WORLD for three beats. It used to be a b08 card    #
    # that repainted 86% of the frame, then a packet close-up on top of it,   #
    # then a THIRD full room at b10 that repainted 73% to say the same       #
    # thing again. Now the room holds; one packet is held up, then the count  #
    # lands on the room it belongs to.                                        #
    # ===================================================================== #
    def s4_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 55, wall=(78, 86, 98), floor=(58, 64, 74),
                  warm=(104, 88, 56))
        for k in range(5):
            _shelf(d, -120 + k * 8, W + 120, 210 + k * 96, 56 + k, h=190,
                   packets=13)
    els.append(SC.stage(clock, 8, s4_room, j=11))

    def s4_packet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # One packet held up to the light, at the size that reads as a held
        # object against the shelves rather than as a second room. The glow is
        # an ellipse, not a filled disc, so it adds light without replacing the
        # shelves behind it.
        PA.fill_poly(tile, PA.ellipse_pts(640, 400, 214, 176, n=64), AMBER_LT,
                     seed=62, value=0.05)
        _packet(d, 640, 392, 232, 306, 63, band=AMBER, stamp='wheat')
        # a hand coming in from the right edge, gripping it -- cropped by the
        # frame edge so it reads as an arm reaching in, not a floating paw.
        PA.hand_stroke(d, [(1330, 560), (790, 486)], (232, 202, 172), 58,
                       closed=False, seed=64, wavelength=170.0)
        PA.hand_stroke(d, [(1330, 560), (790, 486)], INK, 5, closed=False,
                       seed=65, wavelength=170.0)
        for k in range(3):
            PA.hand_stroke(d, [(840 + k * 38, 468 + k * 9), (886 + k * 38, 552)],
                           (232, 202, 172), 27, closed=False,
                           seed=66 + k, wavelength=50.0)
        # LABEL_YELLOW, not INK. At the bottom of the amber pool (bg_lum ~90)
        # with no keyline the counters in o, a, e and p fill in and the lower
        # half of the glyphs runs into the brown shadow edge. The light fill
        # carries the contrast and takes the keyline.
        D.draw_label(tile, 'one sample', center=(640, 640),
                     color=VT.LABEL_YELLOW, size=34)
    els.append(SC.accrue(clock, 9, 11, s4_packet, kind='shape',
                         motion=SC.enter(clock, 9, dx=0, dy=-64, dur=ARRIVE)))
    # NO caption at b09. "one sample" is DRAWN on the packet's own shadow.

    def s4_count(tile, fw, fh):
        D.draw_number(tile, '1,000,000', center=(640, 596),
                      color=VT.LABEL_YELLOW, size=104)
    els.append(SC.accrue(clock, 10, 11, s4_count, kind='shape',
                         motion=SC.enter(clock, 10, dx=0, dy=-36, dur=ARRIVE)))
    els.append(cap(10, 640, 700, size=30, fill=VT.LABEL_YELLOW))
    # The drawn count sits ON the room it counts. The caption is the sentence
    # around the numeral ("around a million samples, from a hundred nations"),
    # which the numeral cannot say.

    # ===================================================================== #
    # STAGE S5  b11-b12  "Wheat, rice, barley, beans, and millet. / Every    #
    #                    sample in there is a spare copy."                   #
    # One shelf deck held across both beats. All five packets arrive TOGETHER  #
    # at b11 because the narrator names all five in ONE beat -- spreading them  #
    # would have packets landing on empty beats with the words already gone.   #
    # b12 used to lay a full COPY/ORIGINAL pair of panels over them (a 48%    #
    # repaint, and it buried the packets it was talking about). Now it is a   #
    # packet sliding OFF the deck with an arrow, which is the thought: the     #
    # sample leaves the shelf and stays here.                                  #
    # ===================================================================== #
    def s5_deck(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 77, wall=(80, 88, 100), warm=(104, 90, 58))
        _shelf(d, -60, W + 60, 600, 78, h=210, packets=5)
    els.append(SC.stage(clock, 11, s5_deck, j=13))

    def s5_crops(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # All five arrive together, one row, five distinct crop marks so the row
        # reads as five different seeds at a glance.
        #
        # NO drawn name under each packet. v1 drew WHEAT/RICE/BARLEY/BEAN/MILLET
        # at y=350, which is exactly the packets' top edge: every label straddled
        # its own packet's border and was cut by it. The five names are ONE
        # caption line at the beat the narrator says them.
        kinds = ['wheat', 'rice', 'barley', 'bean', 'millet']
        for i, k in enumerate(kinds):
            cx = 128 + i * 256
            _packet(d, cx, 470, 168, 250, 80 + i * 3, band=AMBER, stamp=k)
    els.append(SC.accrue(clock, 11, 12, s5_crops, kind='shape',
                         motion=SC.enter(clock, 11, dx=0, dy=-56, dur=ARRIVE)))
    els.append(cap(11, 640, 700, size=30))

    def s5_spare(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE PIVOT, made physical. The deck and its five packets stay; a sixth
        # packet slides in from the right and stops with an arrow and a SPARE
        # COPY tag, so "every sample in there is a spare copy" is a thing that
        # is happening rather than a new pair of boxes laid over the row.
        _packet(d, 1096, 392, 150, 214, 84, band=AMBER, stamp='wheat')
        D.draw_arrow(tile, (960, 300), (1060, 356), color=RED, width=8,
                     head=40)
        D.draw_label(tile, 'SPARE COPY', center=(1096, 258),
                     color=VT.LABEL_RED, size=34)
    els.append(SC.accrue(clock, 12, 13, s5_spare, kind='shape',
                         motion=SC.enter(clock, 12, dx=180, dy=0, dur=0.55)))
    els.append(cap(12, 500, 700, size=30))
    # KEPT, and it is the chapter's pivot: the sentence the whole video is built
    # to land. SPARE COPY is drawn, but a drawn tag does not say that the vault
    # holding copies is the POINT -- the words carry it.

    # ===================================================================== #
    # STAGE S6  b13-b14  "The original seed always stays on the farm. / Each #
    #                    nation's crop insurance, stored in a mountain."      #
    # The globe is the WORLD now, cropped by the bottom and right edges, so it #
    # is a world filling the frame and the keeper stands beside it rather than #
    # replacing it. Two full-frame replacements became: a man arriving on the #
    # left, then the packets landing on the globe one ring at a time.          #
    # ===================================================================== #
    def s6_world(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 214, 224), seed=125, value=0.05)
        PA.paper_overlay(tile, seed=126)
        # the globe is deliberately off-centre right and CROPPED by the bottom
        # and right edges, so it is a world filling the frame
        _globe(d, 790, 452, 336, 133)
    els.append(SC.stage(clock, 13, s6_world, j=15))

    def s6_keeper(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Standing on the ground plane beside the globe, not cropped in: this
        # beat's point is that the original is OUT HERE, away from the vault,
        # so he is in the room with the globe rather than filling it. dx only.
        SC.fullbody(d, 236, 690, 372, pose='standing', expression='skeptic',
                    seed=127)
        D.draw_bubble(tile, 'the original\nstays home', (300, 168),
                      tail_to=(250, 400), font_size=30, max_w=400)
    els.append(SC.accrue(clock, 13, 14, s6_keeper, kind='character',
                         eid='s6_keeper',
                         motion=SC.enter(clock, 13, dx=-150, dy=0, dur=ARRIVE)))
    # NO caption at b13. The speech bubble IS his line, drawn in his own mouth;
    # a caption under it duplicated the bubble.

    def s6_packets(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The packets ARRIVE on the globe, two rings, rather than all at once: a
        # globe wearing its packets is a different picture from a bare globe,
        # and the arrival is what says "every nation".
        for k, (gx, gy) in enumerate(((0.42, -0.42), (-0.30, -0.20),
                                      (-0.10, 0.34), (0.30, 0.20))):
            _packet(d, 790 + gx * 336, 452 + gy * 336, 76, 104, 134 + k,
                    band=AMBER, stamp='wheat')
        D.draw_label(tile, 'CROP INSURANCE', center=(330, 214), color=INK,
                     size=40)
    els.append(SC.accrue(clock, 14, 15, s6_packets, kind='shape',
                         motion=SC.enter(clock, 14, dx=0, dy=-40, dur=ARRIVE)))
    # NO caption at b14. CROP INSURANCE is drawn, the packets are on the globe,
    # and the b14 line is exactly those two facts.

    # ===================================================================== #
    # STAGE S7  b15  "Inside, the air holds at minus eighteen degrees."       #
    # + STAGE S8  b16-b17  "colder than any farm freezer. / In that cold, the #
    #                      seeds sleep for centuries."                       #
    # TWO stages, not one, and the reason is a measurement rather than a        #
    # preference. The b16 comparison (a chest freezer beside a vault door three #
    # times its size) covers ~48% of the frame and the b17 frost another ~49%;  #
    # neither fits the 30% budget a layer inside a stage gets. So the           #
    # comparison is its own bg world at b16 and the frost is a detail on IT at  #
    # b17 -- where the shelf and packets are sized to ~22%. The thermometer at  #
    # b15 is a 20px tube, so it costs almost nothing and stays a detail.        #
    # ===================================================================== #
    def s7_cold(tile, fw, fh):
        _interior(tile, 141, wall=(74, 82, 94), warm=(96, 84, 56))
    els.append(SC.stage(clock, 15, s7_cold, j=16))

    def s7_thermo(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The thermometer is a narrow tube, so it stays clear of the frame's
        # middle and the reading can sit beside it rather than under it.
        S.thermometer(d, 300, 660, 540, 0.22, seed=142, hot=False)
        # LABEL_YELLOW, not INK: the zero tick sits on the warm interior pool at
        # bg_lum ~88 with no keyline, so the counter inside the glyph filled in
        # and it read as a solid dark ring -- the darkest text on the card, on
        # the one numeral the viewer is meant to read as the 0 mark.
        D.draw_label(tile, '0', center=(396, 178), color=VT.LABEL_YELLOW,
                     size=34)
        D.draw_arrow(tile, (760, 452), (596, 528), color=VT.LABEL_RED, width=10,
                     head=46)
        # The -18 numeral is in the SAME layer as the arrow it belongs to. Split
        # across two elements it became two large reds fighting in one half of
        # the frame -- rule 1: anything sharing a part of the frame replaces
        # rather than stacks.
        D.draw_number(tile, '-18', center=(862, 300), color=VT.LABEL_RED,
                      size=180)
        D.draw_label(tile, 'DEGREES C', center=(862, 430), color=VT.LABEL_RED,
                     size=52)
    els.append(SC.accrue(clock, 15, 16, s7_thermo))
    els.append(cap(15, 862, 560, size=30, fill=VT.LABEL_RED))
    # The caption sits under the -18 numeral, in the gap between the numeral
    # and the floor, clear of the thermometer on the left.

    def s8_freezers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 143, wall=(74, 82, 94), warm=(96, 84, 56))
        # left: an ordinary domestic chest freezer, small and domestic
        chest = [(120, 300), (520, 300), (520, 640), (120, 640)]
        PA.fill_poly(tile, chest, (222, 224, 226), seed=146, value=0.07)
        PA.hand_stroke(d, chest, INK, 7, closed=True, seed=147, wavelength=150.0)
        PA.hand_stroke(d, [(120, 380), (520, 380)], INK, 5, closed=False,
                       seed=148, wavelength=110.0)
        # LABEL_YELLOW, not INK: black with no keyline across the brown wall
        # flattened the counters in A, R and E into the ground.
        D.draw_label(tile, 'FARM FREEZER', center=(320, 250),
                     color=VT.LABEL_YELLOW, size=32)
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
    els.append(SC.stage(clock, 16, s8_freezers, j=18))
    # NO caption at b16. FARM FREEZER and VAULT are labelled, and both print
    # -18; the scale comparison IS the sentence "colder than any farm freezer".

    def s8_frost(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # v1 drew a 640x480 packet so large and so white that it read as an
        # empty blank sign. Rebuilt as a LOW, WIDE shelf of frost-crusted packets
        # along the bottom of the room. Sized and placed deliberately: the first
        # pass at ~22% put three large packets at mid-frame, where they landed
        # on top of the farm-freezer and vault-door labels from b16 and turned
        # the frame into overlapping diagrams. The frost belongs UNDER the
        # comparison -- it is what is IN the cold -- so it lives in the bottom
        # band the freezers leave empty, adds to the room rather than fighting
        # it, and stays inside the 30% a detail gets.
        _shelf(d, 40, 1240, 664, 156, h=104, packets=7)
        # hoar frost: a dense crust along the top seal of every packet the shelf
        # draws, plus speckle ON the shelf lip. Never on the wall or the freezers.
        for k in range(60):
            x = 60 + (k * 41) % 1160
            y = 556 + (k * 17) % 22
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(238, 248, 253))
        for k in range(40):
            x = 50 + (k * 53) % 1180
            y = 664 + (k * 11) % 10
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(226, 240, 250))
        D.draw_label(tile, 'CENTURIES', center=(640, 528),
                     color=VT.LABEL_YELLOW, size=44)
    els.append(SC.accrue(clock, 17, 18, s8_frost, kind='shape',
                         motion=SC.enter(clock, 17, dx=0, dy=-30, dur=ARRIVE)))
    # NO caption at b17. CENTURIES is drawn above the frost-covered packets and
    # the frost itself is the sleeping.

    # ===================================================================== #
    # STAGE S8  b18-b19  "The original plan was simple: shut the door. /     #
    #                    Then leave the whole vault to the ice."             #
    # The corridor with its nest of receding doors is HELD, because the two    #
    # beats are about DOORS and the viewer needs the same corridor when the    #
    # door closes. The presenter arrives and points; then the ice seal GROWS   #
    # across the near door's hasp as a detail -- not a new frame of a different #
    # steel door. It used to repaint 75% at b19.                              #
    # ===================================================================== #
    def s8_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 161, wall=(72, 80, 92), floor=(54, 60, 70),
                  warm=(96, 86, 58))
        # four doors receding down the corridor. The outermost door's heavy
        # frame used to top out at y=19, driving a full-width INK bar through
        # the persistent title; that geometry is kept trimmed here.
        for k, (hw, hh, y) in enumerate(((360, 190, 316), (290, 172, 366),
                                          (222, 134, 420), (160, 98, 470))):
            _doorway(d, 640, y, 162 + k * 4, w=hw * 0.55, h=hh,
                     colour=(58, 64, 76) if k else (72, 78, 90))
        # the near door the seal will weld: a lit slab at the corridor mouth
        dx0, dy0, dx1, dy1 = 300, 148, 980, 648
        PA.fill_rect(tile, [dx0, dy0, dx1, dy1], (104, 113, 126), seed=178,
                     value=0.06)
        PA.fill_rect(tile, [dx0 - 34, dy0 - 34, dx1 + 34, dy1 + 34],
                     (72, 79, 90), seed=186, value=0.06)   # the jamb
        PA.hand_stroke(d, [(dx0 - 34, dy0 - 34), (dx1 + 34, dy0 - 34),
                           (dx1 + 34, dy1 + 34), (dx0 - 34, dy1 + 34)],
                       INK, 9, closed=True, seed=179, wavelength=160.0)
        PA.hand_stroke(d, [(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)],
                       INK, 8, closed=True, seed=180, wavelength=150.0)
        # the hasp bar -- the thing the ice will weld shut
        PA.hand_stroke(d, [(dx0 + 40, 528), (dx1 - 40, 528)], (46, 51, 60), 22,
                       closed=False, seed=201, wavelength=150.0)
        PA.hand_stroke(d, [(dx0 + 40, 528), (dx1 - 40, 528)], INK, 7,
                       closed=False, seed=202, wavelength=150.0)
    els.append(SC.stage(clock, 18, s8_corridor, j=20))

    def s8_presenter(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 190, 700, 340, pose='pointing',
                    expression='deadpan', seed=170)
    els.append(SC.accrue(clock, 18, 19, s8_presenter, kind='character',
                         eid='s8_presenter',
                         motion=SC.enter(clock, 18, dx=-130, dy=0, dur=0.55)))
    els.append(cap(18, 700, 690, size=30, fill=(214, 224, 236)))
    # The caption sits low and to the RIGHT of where the presenter stands, so
    # the words land on empty floor rather than on his boots or the door frames.

    def s8_seal(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "leave the whole vault to the ice" is carried by a FROZEN SEAL, not
        # by drawn snow. Five passes on frost texture all rendered as something
        # that was not ice. So the ice here is ONE legible fact: a block of
        # frozen water has grown across the door's hasp and welded it shut. A
        # solid pale-blue block with a hard edge and a few crystal spikes reads
        # immediately as ice and cannot be mistaken for snow or a tear.
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
        # drifts at the foot of the door: enough to say the cold owns this place,
        # thin enough not to become the subject.
        _frost_bank(d, 266, 1014, 682, 622, 660, 400)
        _frost_crystals(d, 290, 990, 624, 10, 700)
    els.append(SC.accrue(clock, 19, 20, s8_seal, kind='shape',
                         motion=SC.enter(clock, 19, dx=0, dy=-44, dur=0.55)))
    els.append(cap(19, 640, 690, size=30))
    # The caption is KEPT on this beat: the ice is visible now, but "leave the
    # whole vault to the ice" is a decision, and a frozen door alone does not
    # say anyone MADE that choice. b18's caption is one beat back, so these two
    # do not stack.

    # ===================================================================== #
    # STAGE S9  b20-b21  "Then, in 2016, the mountain began to leak. /       #
    #                    Meltwater came in through the entrance tunnel."      #
    # The cutaway with 2016 on it is the WORLD, and the meltwater channel is   #
    # the DETAIL that arrives at b21 pointing at the open door. Previously each #
    # of these was its own full-frame card repainting ~70-90%.                 #
    # ===================================================================== #
    def s9_leak(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 185, warm_chamber=True)
    els.append(SC.stage(clock, 20, s9_leak, j=22))

    def s9_2016(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # 2016, not 2008. This label was a copy-paste from the b03 card above
        # it, so the beat that opens the flood chapter drew the vault's OPENING
        # year while the narrator said 2016.
        D.draw_label(tile, '2016', center=(210, 152), color=VT.LABEL_RED,
                     size=64)
        D.draw_arrow(tile, (300, 190), (600, 330), color=INK, width=10,
                     head=46)
    els.append(SC.accrue(clock, 20, 21, s9_2016, kind='shape'))
    els.append(cap(20, 640, 700, size=30))
    # The caption is KEPT here and not at b21: "the mountain began to leak" is
    # the pivot of the whole chapter, the one beat where the argument turns, and
    # the drawn 2016 arrow only shows the mountain. The words carry the turn.

    def s9_channel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # a brown meltwater run cutting straight at the open door
        chan = [(340, 700), (620, 700), (592, 520), (580, 470), (544, 470),
                (504, 540), (452, 560)]
        PA.fill_poly(tile, chan, WATER, seed=195, value=0.07)
        PA.hand_stroke(d, chan[:1] + chan[2:], INK, 5, closed=False, seed=196,
                       wavelength=110.0)
        D.draw_arrow(tile, (280, 640), (430, 552), color=RED, width=10,
                     head=46)
    els.append(SC.accrue(clock, 21, 22, s9_channel, kind='shape'))
    # NO caption at b21. The water channel drawn straight at the open door with
    # a red arrow aimed into it IS "meltwater came in through the entrance
    # tunnel". b20 already carries the flood caption.

    # ===================================================================== #
    # STAGE S10  b22-b25  "Water at the door, in a frozen land. / The        #
    #                      entrance flooded with eight hundred tonnes. / The   #
    #                      staff were cut off for a year. / The seed samples   #
    #                      themselves were never touched."                    #
    # The flood corridor is the WORLD and holds for four beats. The water is   #
    # the one thing that RISES here -- authored at the risen position and      #
    # drifted 90px down over the beat, so the fill reads as water climbing the #
    # corridor, which is the sentence. Then the number lands, then the boards   #
    # go up across the door, then the keeper walks in to say the seeds were    #
    # fine. Four beats, one repaint.                                            #
    # ===================================================================== #
    def s10_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 201, wall=(62, 70, 82), floor=(48, 54, 64))
        # The doorway's frame sits so its top is clear of the title band.
        _doorway(d, 640, 385, 202, w=300, h=250, colour=(70, 76, 88))
    els.append(SC.stage(clock, 22, s10_corridor, j=26))

    def s10_flood(tile, fw, fh):
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
    # narrator says it filled. This is the only motion here that carries
    # meaning on its own, so it is the only one with a multi-second track.
    # Live to b24, NOT to b23. The water used to END exactly where the '800
    # tonnes' numeral began, so the gate measured the handover -- the wall of
    # water leaving AND the numeral arriving -- as one 30% repaint and flagged
    # it. Held under its successor, the numeral lands ON the flood instead of
    # replacing it, which is also the better picture: the weight is standing in
    # the water. The drift still finishes at b23 (the rise is b22->b23), so the
    # flood holds its risen level through b23 rather than sliding on.
    els.append(SC.accrue(clock, 22, 24, s10_flood, kind='shape',
                         motion=SC.drift(clock, 22, 23, dx=0, dy=-90)))
    # NO caption at b22. A cold grey corridor half-drowned by blue water with
    # the door behind it IS "water at the door, in a frozen land".

    def s10_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        D.draw_number(tile, '800', center=(430, 262), color=VT.LABEL_YELLOW,
                      size=170)
        D.draw_label(tile, 'TONNES', center=(960, 262), color=VT.LABEL_YELLOW,
                     size=96)
    els.append(SC.accrue(clock, 23, 24, s10_tonnes, kind='shape',
                         motion=SC.enter(clock, 23, dx=0, dy=-30, dur=ARRIVE)))
    els.append(cap(23, 640, 690, size=30, fill=VT.LABEL_YELLOW))
    # KEPT. "eight hundred tonnes" is the one number the viewer cannot infer
    # from the frame. The drawn 800 is the number SHOWN; the caption is the
    # sentence AROUND it, which the numeral alone does not say.

    def s10_barricade(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # MOVING. The barricade going up across the door is the b24 statement
        # made physically: the staff are OUT, the door is boarded.
        _flood_gate(d, 640, 400, 229)
        D.draw_label(tile, '2016', center=(300, 250), color=VT.LABEL_RED,
                     size=60)
    els.append(SC.accrue(clock, 24, 25, s10_barricade, kind='shape',
                         motion=SC.enter(clock, 24, dx=0, dy=70, dur=ARRIVE)))
    # NO caption at b24, and it is a real loss of the word "a year". The boards
    # going up across the door plus the drawn 2016 is the seal; but b23 already
    # captioned this stage and the no-two-consecutive rule is a hard constraint.

    def s10_fine(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The keeper walks into the flooded corridor to say the one thing that
        # matters. Full body rather than a close-up: this is a person standing
        # in the water, and a cropped face would have replaced the corridor.
        SC.fullbody(d, 236, 690, 340, pose='standing', expression='deadpan',
                    seed=233)
        D.draw_bubble(tile, 'the seeds\nwere fine', (250, 172),
                      tail_to=(250, 380), font_size=30, max_w=380)
    els.append(SC.accrue(clock, 25, 26, s10_fine, kind='character',
                         eid='s10_fine',
                         motion=SC.enter(clock, 25, dx=-140, dy=0, dur=ARRIVE)))
    # NO caption at b25. The bubble IS the line, in his mouth.

    # ===================================================================== #
    # STAGE S11  b26-b27  "They lay above the waterline, in the cold. / The   #
    #                      same permafrost that keeps it thaws too."           #
    # ONE cross-section carries both beats: the water sits in the corridor at  #
    # b26, and at b27 the frozen layer above it is eaten back and the melt     #
    # arrows arrive. They were two separate full-frame cutaways (98% and 95%).  #
    # ===================================================================== #
    def s11_cut(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 237, water_level=0.34)
    els.append(SC.stage(clock, 26, s11_cut, j=28))

    def s11_above(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        D.draw_arrow(tile, (300, 300), (300, 430), color=VT.LABEL_RED, width=9,
                     head=42)
        D.draw_label(tile, 'ABOVE THE WATER', center=(300, 210),
                     color=VT.LABEL_RED, size=34)
    els.append(SC.accrue(clock, 26, 27, s11_above, kind='shape'))
    # NO caption at b26. ABOVE THE WATER is DRAWN with an arrow to the chamber
    # floor; the words only restated it.

    def s11_thaw(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The frozen layer is eaten back from below and the melt arrows arrive.
        # Redrawn over the stage world's band rather than as a second whole
        # cutaway, so the corridor and its water are the SAME ones.
        band = [(0, 330), (W, 330), (W, 470), (0, 470)]
        low = []
        n = 40
        for i in range(n + 1):
            x = W * i / float(n)
            yy = 470 - 46 * math.sin(i * 1.1) - 18 * math.sin(i * 0.37 + 1.2)
            low.append((x, yy))
        PA.fill_poly(tile, band, ICE, seed=244, value=0.06)
        PA.fill_poly(tile, low + [(W, 470), (0, 470)], SLATE, seed=245,
                     value=0.06)
        PA.hand_stroke(d, low[:n + 1], INK, 6, closed=False, seed=246,
                       wavelength=120.0)
        for k in range(6):
            x = 120 + k * 200
            D.draw_arrow(tile, (x + 40, 290), (x - 20, 426), color=RED,
                         width=8, head=36)
        D.draw_label(tile, 'AND MELTING', center=(880, 236), color=VT.LABEL_RED,
                     size=40)
    els.append(SC.accrue(clock, 27, 28, s11_thaw, kind='shape',
                         motion=SC.enter(clock, 27, dx=0, dy=-30, dur=ARRIVE)))
    els.append(cap(27, 640, 690, size=32, fill=RED))
    # KEPT, and it is the second pivot. "The same permafrost that keeps it
    # thaws too" cannot be drawn as a label: the art can show a ragged ice layer
    # and red melt arrows, but not that the SAME layer doing the preserving is
    # the layer failing. That identity is the argument, and only the sentence
    # carries it.

    # ===================================================================== #
    # STAGE S12  b28-b30  "The vault is watched now, year round. / A new      #
    #                      access tunnel is being built. / New lights on the   #
    #                      snow, night and day."                             #
    # The slope is the WORLD and holds for three beats. The site gets busier   #
    # inside it: a camera is bolted up, a new raw mouth is cut beside the old   #
    # door, an excavator arrives, and the work lights come on. Three beats that #
    # used to be three separate full-frame exteriors (90%, 40%, 90%) are now    #
    # one exterior with three arrivals.                                       #
    # ===================================================================== #
    def s12_slope(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 249, snow=(222, 230, 238))
        _mountain(d, 250, crest=280, base=HZ + 30)
        _wedge(d, 300, 400, 251, w=210, h=150)
        _doorway(d, 300, 500, 252, w=132, h=172, colour=(46, 52, 62))
    els.append(SC.stage(clock, 28, s12_slope, j=31))

    def s12_camera(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # MOVING. The camera's lamp coming on is "watched now" -- the eye is
        # drawn to the small red lamp, which is the point of the beat.
        _camera(d, 700, 300, 110, 253)
        D.draw_arrow(tile, (900, 262), (770, 320), color=INK, width=9, head=42)
        D.draw_label(tile, 'watched', center=(1040, 222), color=INK, size=36)
    els.append(SC.accrue(clock, 28, 29, s12_camera, kind='shape',
                         motion=SC.enter(clock, 28, dx=0, dy=-40, dur=ARRIVE)))
    # NO caption at b28. "watched" is DRAWN beside the arrow pointing at the
    # camera; the drawn word is the caption.

    def s12_newmouth(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the new mouth: raw concrete, cut into the slope to the right of the
        # old door, so the two of them read as old-and-new on one hillside.
        raw = [(880, 400), (1180, 400), (1140, 620), (900, 620)]
        PA.fill_poly(tile, raw, CONCRETE, seed=261, value=0.07)
        PA.hand_stroke(d, raw, INK, 7, closed=True, seed=262, wavelength=150.0)
        _doorway(d, 1030, 520, 263, w=96, h=124, colour=(52, 58, 70))
        D.draw_label(tile, 'NEW TUNNEL', center=(1030, 350), color=VT.LABEL_RED,
                     size=32)
        # The excavator, arriving. Drawn on its own small tile so the machine
        # moves without dragging the opaque sky across the shot.
        _excavator(d, 640, 604, 82, 264)
    els.append(SC.accrue(clock, 29, 30, s12_newmouth, kind='shape',
                         motion=SC.enter(clock, 29, dx=-90, dy=0, dur=ARRIVE)))
    els.append(cap(29, 640, 700, size=30))
    # KEPT. "A new access tunnel is being built" is future work in progress; the
    # excavator and raw concrete show it, but the caption carries the sentence
    # and this beat is a beat away from b28's dropped one, not adjacent to it.

    def s12_lights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Two beams of light on the snow. _soft_beam, not SV._light_wedge: the
        # latter fills one solid amber triangle and two of them read as gold
        # traffic cones rather than lamplight.
        _soft_beam(d, 880, 150, HZ - 6, 152, 271)
        _soft_beam(d, 1110, 150, HZ - 6, 138, 273)
        SC.fullbody(d, 640, HZ + 20, 224, pose='standing', expression='skeptic',
                    seed=275)
    els.append(SC.accrue(clock, 30, 31, s12_lights, kind='character',
                         motion=SC.enter(clock, 30, dx=120, dy=0, dur=0.55)))
    # NO caption at b30. Two lamp wedges on the snow with him standing between
    # them IS "new lights on the snow, night and day".

    # ===================================================================== #
    # STAGE S13  b31-b35  "It is still a bunker against catastrophe. /        #
    #                      Catastrophe is already moving into the mountain. / #
    #                      The coldest air on earth is warming here. / The     #
    #                      seeds are still fine, for now. / Somewhere under    #
    #                      the snow, it is still seeping."                    #
    # THE BIGGEST WIN IN THE REBUILD, and the clearest demonstration of the   #
    # model. This was five unrelated full-frame cards -- a paper-wall close-up, #
    # a re-drawn mountain, a bare warming slope, another close-up, a night      #
    # slope -- i.e. a new image every sentence, which is the complaint. It is  #
    # now ONE night mountain held for thirteen seconds: the keeper arrives, a  #
    # heat front advances up the snow, the snow bares and the -2.6 lands, he   #
    # comes back holding a packet, and the meltwater channel drifts.          #
    # ===================================================================== #
    def s13_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 281)
        SC.title_backdrop(tile, 1281, col=TITLE_COURSE)
        _mountain(d, 283, crest=300, base=HZ + 6)
    els.append(SC.stage(clock, 31, s13_night, j=36))

    def s13_bunker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # He stands ON the snow in front of the mountain he is describing,
        # rather than replacing the mountain with a cropped face. The bubble is
        # his line; the caption below is the only text on this beat that is not
        # in the art.
        SC.fullbody(d, 300, HZ + 8, 300, pose='standing', expression='deadpan',
                    seed=279, ink=CREAM)
        D.draw_bubble(tile, 'a bunker', (760, 214), tail_to=(470, 430),
                      font_size=34, max_w=300)
    els.append(SC.accrue(clock, 31, 32, s13_bunker, kind='character',
                         eid='s13_bunker',
                         motion=SC.enter(clock, 31, dx=-140, dy=0, dur=0.55)))
    els.append(cap(31, 640, 690, size=32, fill=AMBER_LT))
    # KEPT. "still a bunker against catastrophe" is the thesis restated; the
    # bubble says only "a bunker", so the caption is what carries "still" and
    # "against catastrophe" -- the two words the whole chapter turns on.

    def s13_front(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Catastrophe arriving as warmth UNDER the snow. v1 drew a single 12px
        # red line across the lower third of an otherwise empty pale snow field
        # -- a thin stripe on a dead frame. The warm front is now a broad band
        # bleeding up through the snow from the bottom edge, with a hard red
        # leading edge and heat shimmer rising off it.
        for k in range(5):
            t = k / 4.0
            col = (196 - int(52 * t), 84 + int(60 * t), 60 + int(30 * t))
            y = 720 - 40 - k * 26
            PA.fill_rect(tile, [0, y, W, y + 30], col, seed=290 + k, value=0.06)
        PA.hand_stroke(d, [(-40, 512), (320, 490), (660, 504), (1000, 482),
                           (1320, 498)], RED, 16, closed=False, seed=287,
                       wavelength=190.0)
        for k in range(9):
            x = 40 + k * 140
            PA.hand_stroke(d, [(x, 466), (x + 14, 428), (x - 6, 392)],
                           (206, 118, 82), 6, closed=False, seed=320 + k,
                           wavelength=54.0)
        D.draw_label(tile, 'WARMING', center=(320, 640), color=RED, size=44)
    # Live to the END of the stage, not to b33 or b34. Two handovers were
    # stacked on this chain -- front->bare at b33 and front+bare->character at
    # b34 -- and the gate correctly read each as a cut: the element you were
    # looking at vanished and a different one took its place. Held to j=36 the
    # finale is what it should have been: ONE night mountain that has had three
    # things happen to it in sequence, none of which erase the last. The warm
    # front is the slow catastrophe, so it not only stays, it keeps arriving
    # under everything; the bare rock is what it leaves behind; the channel is
    # what that snow was holding. Each arrival is now additive, and the only
    # thing that ever leaves is the character, who is a one-beat visitor.
    els.append(SC.accrue(clock, 32, 34, s13_front, kind='shape'))
    # NO caption at b32. WARMING is DRAWN in red across the advancing front and
    # the front is the catastrophe itself; the words would restate the label.

    def s13_bare(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Bare rock showing through where the snow used to be. The first
        # version was three axis-aligned rectangles, and at ship size they read
        # as grey UI panels floating over the mountain -- they cut straight
        # through the white peak and destroyed the silhouette. These are TWO
        # irregular patches instead. The big one sits low on the snow plain
        # exactly where the presenter stands at b34, so he is standing ON the
        # ground that is being lost: it gives his cream legs something to read
        # against, it anchors him to the frame instead of leaving him floating,
        # and it makes the patch read as terrain rather than a box. The small
        # scar high on the right ridge is more of the same thing further up.
        bare = [(176, 566), (300, 548), (430, 560), (516, 606), (470, 664),
                (330, 684), (200, 656), (168, 610)]
        PA.fill_poly(tile, bare, (128, 122, 116), seed=294, value=0.07)
        PA.hand_stroke(d, bare, INK, 5, closed=True, seed=298, wavelength=120.0)
        scar = [(1080, 420), (1200, 404), (1272, 430), (1244, 458), (1120, 452),
                (1074, 444)]
        PA.fill_poly(tile, scar, (128, 122, 116), seed=295, value=0.07)
        PA.hand_stroke(d, scar, INK, 4, closed=True, seed=299, wavelength=100.0)
        D.draw_number(tile, '-2.6 C', center=(640, 268), color=VT.LABEL_RED,
                      size=132)
        D.draw_label(tile, 'PER DECADE', center=(640, 368), color=VT.LABEL_RED,
                     size=54)
    # Live to b35, NOT to b34. The chain front->bare->character handed over at
    # every beat, and each handover was measured as a cut. Holding the bared
    # slope under the closing beats lets the number stay on screen while he
    # qualifies it ("for now") and while the water runs -- the caveat lands on
    # the figure. But it REPLACES the warm front rather than adding to it: two
    # competing lower-slope bands read as stripes. So the front ends at b33 and
    # the bare ground is what it left behind.
    els.append(SC.accrue(clock, 33, 35, s13_bare, kind='shape',
                         motion=SC.enter(clock, 33, dx=0, dy=-34, dur=ARRIVE)))
    # NO caption at b33. -2.6 C PER DECADE is DRAWN as a 132px numeral over the
    # bared slope; the number is the sentence.

    def s13_fornow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Him again, on the same snow, holding the packet. The "for now" bubble
        # is his line -- the caveat is in his mouth, which is where a caveat
        # belongs -- and the packet in his hand is the thing being qualified.
        #
        # STAGING FIX. The first pass put his feet at HZ+10 = 456, which is
        # exactly the dark ridge line of the mountain behind him, so he read as
        # standing on the horizon in mid-air and the -2.6 C numeral ran straight
        # through his legs. He now stands on the NEAR snow at feet_y=612, big
        # enough to be foreground (height 380 rather than 290), and left of the
        # numeral's column so the two never touch.
        SC.fullbody(d, 340, 600, 380, pose='standing', expression='deadpan',
                    seed=303, ink=CREAM)
        _packet(d, 950, 486, 196, 272, 304, band=AMBER, stamp='wheat')
        PA.hand_stroke(d, [(1330, 700), (1040, 590)], (232, 202, 172), 58,
                       closed=False, seed=305, wavelength=150.0)
        D.draw_bubble(tile, 'for now', (1010, 268), tail_to=(930, 388),
                      font_size=34, max_w=300)
    # HELD TO THE END OF THE CHAPTER, not to b35. He used to leave exactly
    # when the water arrived, which is the one moment CLAUDE.md 10.8 names as
    # the beat that must not be without him: "the most emotionally loaded second
    # of each segment should always have the stickman reacting." It also made
    # the finale a swap -- character out, channel in -- which is the cut-in-
    # disguise the critic measured as declining cumulative change (23.5 -> 29.0
    # -> 19.2 -> 11.9%): the chapter got quieter as it got more important.
    # Held, b35 is additive. The man is still standing there, still holding the
    # packet, and the water opens up beside him. Nothing is taken back.
    els.append(SC.accrue(clock, 34, 36, s13_fornow, kind='character',
                         eid='s13_fornow',
                         motion=SC.enter(clock, 34, dx=120, dy=0, dur=0.55)))
    # NO caption at b34. "for now" is the bubble; the packet in his hand is the
    # thing being qualified, and he is holding it in frame.

    def s13_seep(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The chapter's last line, and the last frame: the water still running
        # under the snow, on the SAME mountain the stage has held since b31.
        #
        # A filled CHANNEL, not a hairline. The first pass drew one 9px stroke
        # and the full-res frame read as an empty white slope with a caption on
        # it -- the closing image of the whole chapter was invisible.
        #
        # STARTED AT x=500, not 200, because he is now held on screen through
        # this beat standing at feet (340,600) and occupying x 250..430. The old
        # channel ran from x200 and s13_seep composites AFTER s13_fornow, so its
        # opaque fill drew straight across his shins -- the same occlusion bug
        # area51 b29 had. The water now opens up BESIDE him, starting 70px
        # clear of his right edge and running off the right frame edge, which
        # also lets the frame admit the channel continues past the picture.
        chan = [(500, 548), (760, 528), (1010, 546), (1200, 566),
                (1200, 640), (1010, 618), (760, 600), (500, 620)]
        PA.fill_poly(tile, chan, WATER, seed=308, value=0.07)
        PA.hand_stroke(d, chan[:4], (156, 186, 200), 7, closed=False,
                       seed=309, wavelength=170.0)
        for k in range(5):
            x = 560 + k * 130
            PA.hand_stroke(d, [(x, 556 + (k % 3) * 10), (x + 46, 596 + (k % 3) * 8)],
                           (156, 186, 200), 5, closed=False, seed=312 + k,
                           wavelength=60.0)
        # MOVED from (880,470) to (690,428). At 880 the label sat directly on
        # the seed packet's wheat band -- amber text on an amber band, i.e. two
        # things of the same colour fighting and neither legible. It now sits
        # over open snow, left of the packet (which starts at x860) and above
        # the channel, so the label names the water without touching anything.
        D.draw_label(tile, 'still seeping', center=(690, 428), color=AMBER_LT,
                     size=46)
    # MOVING, brief. The channel DRIFTS right as the last line lands -- the one
    # motion in the finale, small, and the literal image of "still seeping".
    els.append(SC.accrue(clock, 35, 36, s13_seep, kind='shape',
                         motion=SC.drift(clock, 35, 36, dx=70, dy=0)))
    # DROPPED. It read "Somewhere under the snow, it is still seeping." in the
    # caption band while "still seeping" was DRAWN on the frame 160px above it --
    # the same eight words twice, ~12 seconds apart in reading order, which is
    # the tell-AND-show redundancy the brief is built against ("refrain from
    # adding text in every visual", "you are not telling but also showing"). The
    # drawn label carries it. The narration still says the line; the frame does
    # not have to repeat it.
    #
    # It is also the LAST frame of the chapter, so a caption band here was
    # cutting the film's closing image in half across the bottom third.
    #
    # RE-CHECKED: the chapter's last caption is now b31, four beats earlier, so
    # the no-consecutive-caption rule is still satisfied with room to spare.

    return SC.finish(els, TITLE, clock, title_seed=47)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent2.mp4'))