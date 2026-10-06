"""cheyenne2_scene -- the PERSISTENT-STAGE rebuild of chapter 2 (Cheyenne).

WHY THIS FILE EXISTS. cheyenne_scene.py (v1) painted a whole frame per beat:
38 cards, each `card(i, j, draw)` filling background-to-subject for beats
i..j-1, so nothing survived between sentences and the frame repainted 38 times
in 89s. Text was on ALL 38 beats (100% density). This file rebuilds the chapter
as EIGHT persistent stages with art that ACCRUES, and cuts text to 16 of 38
beats (42%) with no two captioned beats adjacent.

    A b01-b04  the mountain that is not a mountain; the CMC reveal
    B b05-09  granite, fifteen tunnels, fifteen buildings
    C b10-16  steel springs, and the 700-ton door (the point of it)
    D b17-21  cold interior, 200 people, its own power
    E b22-25  self-sufficiency: no power line, springs, water tanks
    F b26-29  the space defence centre, the warning clocks
    G b30-33  the painted concrete forest on the roof
    H b34-38  nobody confirms; still staffed; the ninety percent figure

Every backdrop is the v1 module's own `_sky` / `_rock_bg` / `_cross_section`
with v1's own seeds, so the wobble is unchanged from the baseline and the stage
boundaries do not make the mountain jump. The art primitives (`_massif`,
`_portal`, `_blast_door`, `_cross_section`, `_console_bank`, `_radar`, `_spring`,
`_water_tank`, `_drum`, `_generator`, `_pylon`, `_painted_tree`, `_vent_tower`,
`_norad_badge`, `_sat`, `_scratch`) and the whole palette are IMPORTED from
cheyenne_scene, never copied: this file declares only the staging.

THE TWO RULES THIS REBUILD KEEPS (both measured in the pinegap pilot)

1. ACCRUE THE WORLD, REPLACE THE LABELS. Scenery accumulates -- the massif, the
   granite face, the floor slab, the road, the slab rows. Anything carrying text,
   and any two elements sharing one region of the frame, REPLACE. Where a beat
   is captioned the redundant in-art label was DROPPED rather than printed twice
   (b11, b19, b21, b24, b32) -- the caption is the sentence and it hands off by
   itself, while a `draw_label` inside an accrued layer would sit there for the
   rest of the stage.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. Twelve moving elements in 38 beats
   (the pilot had nine in 34), each 0.45-0.6s, each on a small subject: a
   head arriving, a globe sliding in from the frame edge, a figure stepping in, a
   shock arrow landing, a ceiling settling, a door swinging down, a breath puff
   drifting, a machine bank arriving, one satellite crossing, one clock hand
   jumping, a pointing arm. Nothing drifts. The reference is 83% still frames
   and a slow drift on a big backdrop reads as image churn, not animation.

CAPTIONS. Sixteen of 38 beats, never two in a row. The test applied per beat was
"does the drawn art already say the words, or does the viewer need them?" -- so
'EARLY 1960s', 'SOLID GRANITE', 'STEEL SPRINGS', '700 TONS', 'SEALS COMPLETELY',
'ITS OWN POWER', 'SPRINGS IN THE ROCK', 'THEY HIDE THE VENTS', 'PAINTED
CONCRETE' and 'WARNING' are all still printed by the art, and those beats carry
no caption. Two judgment calls are recorded in the build() body: b04 drops its
caption because engine3 stamps the scene title "Cheyenne Mountain" over that
exact frame, and b14 drops its caption because the art prints the number as a
210px '700'.

Run:  python lib/cheyenne2_scene.py --preview
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

# The v1 baseline: art primitives + palette, reused not copied.
import cheyenne_scene as CH

SEG = CH.SEG
TITLE = CH.TITLE
BEATS = CH.BEATS
TITLE_BACKDROP = CH.TITLE_BACKDROP

INK = CH.INK
RED = CH.RED
ROCK = CH.ROCK
ROCK_SH = CH.ROCK_SH
ROCK_PK = CH.ROCK_PK
SNOW = CH.SNOW
STEEL = CH.STEEL
STEEL_D = CH.STEEL_D
CONCRETE = CH.CONCRETE
CONCRETE_D = CH.CONCRETE_D
DEEP = CH.DEEP
DEEPER = CH.DEEPER
SKY = CH.SKY
LAMP = CH.LAMP
GREEN = CH.GREEN
HZ = CH.HZ
W, H = CH.W, CH.H

_sky = CH._sky
_rock_bg = CH._rock_bg
_scratch = CH._scratch
_massif = CH._massif
_portal = CH._portal
_blast_door = CH._blast_door
_cross_section = CH._cross_section
_console_bank = CH._console_bank
_radar = CH._radar
_spring = CH._spring
_water_tank = CH._water_tank
_drum = CH._drum
_generator = CH._generator
_pylon = CH._pylon
_painted_tree = CH._painted_tree
_vent_tower = CH._vent_tower
_norad_badge = CH._norad_badge
_sat = CH._sat

# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and it becomes the picture changing every sample,
# which is the churn this rebuild exists to remove.
ARRIVE = 0.5


def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # CAPTION FILL RULE, applied to every caption in this file. v1 filled its
    # captions with the chapter accent RED, which scene_common documents as
    # measuring 2.5:1 on sand -- one of the two caption fills that are actually
    # failing the readability gate. So: default INK on a light card, and
    # dark=True on a dark card (which resolves to the light amber). Nothing
    # here prints a gray or a low-contrast accent.

    # ---- persistent page tooth under everything --------------------------- #
    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ===================================================================== #
    # STAGE A  b01-b04  "Look at this mountain. It is not a mountain at    #
    #                 all. It is a very large hiding place. This is the     #
    #                 Cheyenne Mountain Complex."                          #
    # One exterior held across four beats. The mountain itself is the stage #
    # backdrop; the construction scratch goes on at b02, and at b03 the     #
    # flank is CUT OPEN -- a wedge of dark rock with the floors stacked     #
    # inside it -- while the presenter arrives and looks at it.              #
    # ===================================================================== #
    def a_site(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 5, ground=(170, 170, 174))
        _massif(d, 640, HZ + 30, 900, 112, 6)
    els.append(SC.stage(clock, 1, a_site, j=5))

    def a_scratch(tile, fw, fh):
        # "a very large hiding place" starts here: the survey scratch is the
        # first mark anyone made on it. It ARRIVES and STAYS.
        _scratch(ImageDraw.Draw(tile), 210, 420, 700, 300, 9)
    els.append(SC.accrue(clock, 2, 5, a_scratch, kind='shape'))
    # NO caption at b02. The scratch plus the bubble that arrives at b03 say
    # "this is not a natural mountain"; b01 already carries the opening line.

    def a_cut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        cut = [(60, 720), (60, 300), (360, 210), (470, 330), (520, 720)]
        PA.fill_poly(tile, cut, (56, 58, 68), seed=13, value=0.06)
        PA.hand_stroke(d, [(60, 300), (360, 210), (470, 330), (520, 720)],
                       INK, 7, closed=False, seed=14, wavelength=150.0)
        # the floors stacked inside the cut rock
        for k in range(4):
            yy = 330 + k * 78
            PA.hand_stroke(d, [(70, yy), (400, yy - 20)], DEEPER, 30,
                           closed=False, seed=15 + k, wavelength=90.0,
                           vary=0.05)
    els.append(SC.accrue(clock, 3, 5, a_cut, kind='shape'))

    # The presenter. Two elements at the SAME position, the first ending where
    # the second starts: deadpan while the flank opens ("it is not a mountain
    # at all"), then shock on "it is a very large hiding place".
    def a_presenter_a(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        SC.closeup(d, 880, 440, 195, 'deadpan', 17)
        D.draw_bubble(tile, 'not a mountain', (700, 206), tail_to=(880, 330),
                      font_size=40, max_w=330)
    _bu, _aa, _au = SC.expr_swap(clock, 4, 'deadpan', 'shock', until_j=5)
    els.append(E3.E('a_presenter_a', 'character', a_presenter_a,
                    at=T(3), until=_bu,
                    motion=SC.enter(clock, 3, dx=150, dur=0.55)))

    def a_presenter_b(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 880, 440, 195, 'shock', 17)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))
    # NO caption at b04. engine3 stamps the scene title "Cheyenne Mountain"
    # across y 10..73 of THIS frame, so "This is the Cheyenne Mountain
    # Complex." would be the chapter's name printed twice on top of itself
    # (the same defect as the v1 in-card draw_title overprint). The name is on
    # screen for the whole beat without a caption.

    els.append(cap(1, 640, 662, size=34))
    els.append(cap(3, 640, 690, size=32))

    # ===================================================================== #
    # STAGE B  b05-b09  "Work began there in the early sixties. The Cold   #
    #                 War set the whole schedule. Granite sat under the     #
    #                 entire site. Crews drilled out fifteen long tunnels. #
    #                 Fifteen separate buildings went in there."           #
    # The exterior massif is held for the first two beats and the plant     #
    # stays on it; at b07 the frame goes INSIDE the mountain -- a granite   #
    # face with the drill coming in from the left edge -- and the fifteen   #
    # galleries then ACCRUE onto that same rock face at b08. The hero        #
    # cross-section at b09 replaces the lot.                               #
    # ===================================================================== #
    def b_site(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 5, ground=(170, 170, 174))
        _massif(d, 640, HZ + 30, 900, 112, 6)
    els.append(SC.stage(clock, 5, b_site, j=10))

    def b_plant(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _portal(d, 380, 400, 130, 150, 29, open_frac=0.2, doors=3)
        # plant on the shelf above the mouth
        for k, x in enumerate((760, 900, 1040)):
            PA.hand_stroke(d, [(x, 560), (x, 470)], STEEL_D, 6,
                           closed=False, seed=30 + k, wavelength=60.0)
            PA.hand_stroke(d, [(x - 34, 470), (x + 34, 470)], STEEL_D, 6,
                           closed=False, seed=40 + k, wavelength=60.0)
        heap = [(560, 660), (640, 570), (740, 662)]
        PA.fill_poly(tile, heap, (176, 170, 158), seed=29, value=0.08)
        PA.hand_stroke(d, heap, INK, 5, closed=True, seed=30, wavelength=90.0)
        PA.fill_rect(tile, [880, 620, 1120, 672], (168, 84, 62), seed=31,
                     value=0.07)
        PA.hand_stroke(d, [(880, 620), (1120, 620), (1120, 672), (880, 672)],
                       INK, 5, closed=True, seed=32, wavelength=70.0)
    els.append(SC.accrue(clock, 5, 10, b_plant, kind='shape'))
    # NO caption at b05. The portal, the spoil heap, the plant and the truck
    # already say "somebody built something here".

    def b_early(tile, fw, fh):
        D.draw_label(tile, 'EARLY 1960s', center=(300, 150), color=INK,
                     size=34)
    # REPLACES and lasts one beat only: it carries text, and b06/b08 are the
    # captioned beats either side of it, so it must hand off rather than sit
    # under them.
    els.append(SC.layer(clock, 5, b_early, j=6, kind='shape', eid='b_early'))

    def b_coldwar(tile, fw, fh):
        # MOVING, and small: a globe the size of a fist on the flank, sliding
        # in from the left edge. The Cold War beat is connective glue, so it
        # gets a caption and one moving accent rather than a full frame.
        d = ImageDraw.Draw(tile)
        g = PA.ellipse_pts(210, 300, 150, 150, n=64)
        PA.fill_poly(tile, g, (150, 172, 196), seed=40, value=0.07)
        PA.hand_stroke(d, g, INK, 7, closed=True, seed=41, wavelength=170.0)
        for k, ry in enumerate((0.32, 0.66)):
            PA.hand_stroke(d, PA.ellipse_pts(210, 300, 150 * ry, 150, n=48),
                           (116, 138, 162), 4, closed=True, seed=42 + k,
                           wavelength=120.0)
        PA.hand_stroke(d, [(70, 300), (350, 300)], (116, 138, 162), 4,
                       closed=False, seed=44, wavelength=120.0)
        for i, (ox, oy) in enumerate(((-56, -50), (86, 38))):
            c = PA.ellipse_pts(210 + ox, 300 + oy, 66, 54, n=36)
            PA.fill_poly(tile, c, (176, 158, 128), seed=45 + i, value=0.07)
            PA.hand_stroke(d, c, INK, 5, closed=True, seed=47 + i,
                           wavelength=100.0)
        # the confrontation: a red arc across the sky, the only accent spent
        PA.hand_stroke(d, [(330, 196), (660, 132), (1010, 196)], RED, 6,
                       closed=False, seed=50, wavelength=170.0)
    els.append(SC.accrue(clock, 6, 7, b_coldwar, kind='shape',
                         motion=SC.enter(clock, 6, dx=-190, dur=ARRIVE)))
    els.append(cap(6, 640, 664, size=30))
    # The globe accrues only to b07: at b07 the granite panel covers the left
    # two thirds of the frame, so a globe left standing there would be stacked
    # under the rock face.

    def b_granite(tile, fw, fh):
        # THE GRANITE. The frame goes inside the mountain and the exposed rock
        # face fills it -- cropped at every edge, so the site reads as solid
        # rock all the way past the picture. The crack and the drill are the
        # v1 art, re-registered to the left so the fifteen galleries have room.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [-40, -40, W + 40, H + 40], (176, 158, 158),
                     seed=53, value=0.09)
        PA.paper_overlay(tile, seed=54)
        for k in range(26):
            x = 60 + (k * 137) % 1160
            y = 80 + (k * 91) % 560
            PA.hand_stroke(d, [(x, y), (x + 60, y + 22)], (156, 136, 138), 6,
                           closed=False, seed=54 + k, wavelength=50.0, vary=0.2)
        for k in range(18):
            x = 30 + (k * 211) % 1220
            y = 130 + (k * 137) % 520
            PA.hand_stroke(d, [(x, y), (x + 40, y - 14)], (204, 190, 188), 6,
                           closed=False, seed=90 + k, wavelength=50.0, vary=0.2)
        # TOP EDGE RULE: engine3 stamps the persistent chapter title over
        # y 10..73, so the crack opens at y=116 instead of off the top edge.
        PA.hand_stroke(d, [(520, 116), (560, 200), (530, 340), (600, 520),
                           (570, 720)], DEEPER, 8, closed=False, seed=120,
                       wavelength=140.0)
        # the drill, boring in from the left, cropped by the edge
        bit = [(0, 300), (300, 330), (470, 366), (300, 402), (0, 430)]
        PA.fill_poly(tile, bit, STEEL_D, seed=121, value=0.08)
        PA.hand_stroke(d, bit, INK, 6, closed=True, seed=122, wavelength=120.0)
        for k in range(7):
            x = 40 + k * 62
            PA.hand_stroke(d, [(x, 300 - k * 3), (x, 430 + k * 3)], STEEL, 5,
                           closed=False, seed=130 + k, wavelength=60.0)
        D.draw_label(tile, 'SOLID GRANITE', center=(900, 620), color=SNOW,
                     size=44)
    els.append(SC.layer(clock, 7, b_granite, j=9, kind='shape',
                        eid='b_granite'))
    # NO caption at b07. The drill coming in, the crack it is chasing and the
    # printed SOLID GRANITE all say it; b06 and b08 are the captioned beats
    # either side of this one.
    #
    # This is a REPLACE rather than an accrue: it fills the whole frame, and
    # leaving the exterior mountain standing under it would put a silhouette
    # through the rock.

    def b_galleries(tile, fw, fh):
        # FIFTEEN GALLERIES, cut into the granite face already on screen. They
        # arrive and stay: this is the one place in the chapter where the world
        # visibly gains a thing without anything else changing.
        d = ImageDraw.Draw(tile)
        ty = 470
        PA.hand_stroke(d, [(-30, ty), (560, ty - 10)], DEEPER, 66,
                       closed=False, seed=139, wavelength=130.0, vary=0.05)
        PA.hand_stroke(d, [(-30, ty), (560, ty - 10)], INK, 4, closed=False,
                       seed=140, wavelength=130.0)
        for i in range(15):
            t = i / 14.0
            x0 = 580 + t * 480
            y0 = 190 + t * 280
            x1 = x0 + 130 + (1 - t) * 96
            y1 = y0 + 42 + (1 - t) * 32
            PA.hand_stroke(d, [(x0, y0), (x1, y1)], DEEPER, 30 - t * 14,
                           closed=False, seed=150 + i, wavelength=90.0,
                           vary=0.06)
            PA.hand_stroke(d, [(x0, y0), (x1, y1)], STEEL_D, 4, closed=False,
                           seed=200 + i, wavelength=90.0)
        D.draw_number(tile, '15', center=(1120, 560), color=RED, size=190)
    els.append(SC.accrue(clock, 8, 10, b_galleries, kind='shape',
                         eid='b_galleries'))

    def b_driller(tile, fw, fh):
        # MOVING, small: the presenter walks in and looks at what they drilled.
        SC.fullbody(ImageDraw.Draw(tile), 300, 640, 380, pose='standing',
                    expression='awed', seed=205)
    els.append(SC.accrue(clock, 8, 10, b_driller, kind='character',
                         motion=SC.enter(clock, 8, dx=-140, dur=ARRIVE)))
    els.append(cap(8, 790, 150, size=32))
    # The caption sits high and right of the galleries, clear of the drill
    # coming in from the left and of the presenter's head.

    def b_hero(tile, fw, fh):
        # HERO: the complex stacked inside the mountain. Replaces everything --
        # it is a different composition, cropped by all four edges, so nothing
        # from the granite face may survive under it.
        d = ImageDraw.Draw(tile)
        _sky(tile, 211, sky=(200, 206, 216), ground=(168, 168, 172))
        _cross_section(d, 960, H + 80, 1180, 40, 212, chambers=False)
        for i in range(15):
            col_i, row_i = i % 5, i // 5
            bx = 20 + col_i * 104 + row_i * 22
            by = 336 + row_i * 152
            bw, bh = 88, 116
            b = [(bx, by), (bx + bw, by - 16), (bx + bw, by + bh - 16),
                 (bx, by + bh)]
            PA.fill_poly(tile, b, CONCRETE if i % 2 else (184, 186, 190),
                         seed=230 + i, value=0.07)
            PA.hand_stroke(d, b, INK, 5, closed=True, seed=250 + i,
                           wavelength=80.0)
            PA.hand_stroke(d, [(bx + 10, by + 26), (bx + bw - 10, by + 16)],
                           LAMP if i % 3 else STEEL, 7, closed=False,
                           seed=270 + i, wavelength=50.0)
            PA.hand_stroke(d, [(bx + bw * 0.40, by + bh - 16),
                               (bx + bw * 0.40, by + bh - 56),
                               (bx + bw * 0.66, by + bh - 58),
                               (bx + bw * 0.66, by + bh - 16)],
                           DEEPER, 5, closed=True, seed=290 + i,
                           wavelength=40.0)
        D.draw_number(tile, '15', center=(1090, 500), color=RED, size=230)
        D.draw_label(tile, 'BUILDINGS INSIDE', center=(1090, 650), color=SNOW,
                     size=40)
    els.append(SC.layer(clock, 9, b_hero, j=10, kind='subject', eid='b_hero'))
    # NO caption at b09. The 230px '15' and BUILDINGS INSIDE are the sentence.

    # ===================================================================== #
    # STAGE C  b10-b16  "Each building rests on steel springs. The springs  #
    #                 swallow the shock themselves. Then the mountain above #
    #                 does the rest. The entrance has one very large door.  #
    #                 It weighs roughly seven hundred tons. It was built to #
    #                 seal completely. That door is the whole point of it."#
    # The longest stage in the chapter and the one it exists for. The ROOM   #
    # is the persistent thing: a rock interior with a floor slab overspanning#
    # the frame and a second floor cropped at the top. The springs stand on  #
    # it, then get replaced squashed-flat under the shock, then the whole     #
    # room is replaced by the overhang pressing down, and the portal and the #
    # 700-ton door carry the last four beats.                                #
    # ===================================================================== #
    def c_room(tile, fw, fh):
        _rock_bg(tile, 291, rock=(160, 158, 158), deep=(96, 94, 96))
    els.append(SC.stage(clock, 10, c_room, j=17))

    def c_slab(tile, fw, fh):
        # THE ROOM, and the one element in this stage that accrues: the floor
        # slab overspans left and right, the slab above is cropped by the top
        # edge, and both stay standing under every beat that follows.
        d = ImageDraw.Draw(tile)
        slab = [(-30, 250), (W + 30, 210), (W + 30, 330), (-30, 380)]
        PA.fill_poly(tile, slab, CONCRETE, seed=292, value=0.08)
        PA.hand_stroke(d, [(-30, 250), (W + 30, 210), (W + 30, 330),
                           (-30, 380)], INK, 8, closed=True, seed=293,
                       wavelength=190.0)
        PA.fill_rect(tile, [-20, -20, W + 20, 120], CONCRETE_D, seed=310,
                     value=0.07)
    els.append(SC.accrue(clock, 10, 17, c_slab, kind='shape', eid='c_slab'))

    def c_springs(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(4):
            _spring(d, 160 + k * 330, 380, 210, 250, 300 + k)
        D.draw_label(tile, 'STEEL SPRINGS', center=(640, 620), color=SNOW,
                     size=44)
    # REPLACES at b11: the squashed springs occupy the same four footprints, so
    # leaving the standing ones underneath would stack two springs in one hole.
    els.append(SC.layer(clock, 10, c_springs, j=11, kind='shape',
                        eid='c_springs'))
    # NO caption at b10. The printed STEEL SPRINGS is the words.

    def c_shock(tile, fw, fh):
        # MOVING, and it is the point of the stage: three thick red arrows
        # driving DOWN onto the slab. 0.5s of arrival, then still.
        d = ImageDraw.Draw(tile)
        for k, x in enumerate((230, 640, 1050)):
            _spring(d, x, 370, 320, 150, 330 + k, squash=0.42)
            PA.hand_stroke(d, [(x - 170, 372), (x + 170, 372)], STEEL_D, 6,
                           closed=False, seed=340 + k, wavelength=70.0)
        for k, x in enumerate((230, 640, 1050)):
            D.draw_arrow(tile, (x, 150), (x, 244), color=RED, width=26,
                         head=58)
    els.append(SC.layer(clock, 11, c_shock, j=12, kind='shape',
                        motion=SC.enter(clock, 11, dx=0, dy=-40, dur=ARRIVE)))
    els.append(cap(11, 640, 646, size=34))
    # NO 'SWALLOWS THE SHOCK' label here. The caption IS that sentence, and
    # printing both put the same words twice in the lower third.

    def c_overhang(tile, fw, fh):
        # The mountain itself: a huge rock ceiling pressing down from the top
        # edge over the room that is already on screen.
        d = ImageDraw.Draw(tile)
        ceil = [(-30, -20), (W + 30, -20), (W + 30, 190), (900, 250),
                (520, 300), (180, 240), (-30, 160)]
        PA.fill_poly(tile, ceil, ROCK, seed=352, value=0.09)
        PA.hand_stroke(d, ceil, INK, 8, closed=True, seed=353, wavelength=190.0)
        PA.fill_rect(tile, [-20, 300, W + 20, 720], DEEP, seed=354, value=0.06)
        PA.hand_stroke(d, [(520, 300), (520, 720)], INK, 6, closed=False,
                       seed=355, wavelength=140.0)
    els.append(SC.layer(clock, 12, c_overhang, j=13, kind='shape',
                        eid='c_overhang'))

    def c_shrugger(tile, fw, fh):
        # MOVING, small: the presenter steps in under the overhang and asks the
        # question the caption cannot -- if the springs took the shock, what
        # stops the rest?
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 380, 690, 420, pose='shrug', expression='skeptic',
                    seed=356)
        D.draw_bubble(tile, 'then what stops the rest?', (470, 380),
                      tail_to=(400, 500), font_size=34, max_w=340)
    els.append(SC.layer(clock, 12, c_shrugger, j=13, kind='character',
                        motion=SC.enter(clock, 12, dx=-130, dur=ARRIVE)))
    # NO caption at b12. The bubble is the line, and the overhang drawing itself
    # down over the room is the answer's setup.

    def c_portal(tile, fw, fh):
        # THE ENTRANCE: the tunnel mouth with one very large slab door in it.
        # Accrues -- the 700-ton door at b14 is drawn LARGER over the top of it
        # and covers this arch completely, so it does not need replacing.
        d = ImageDraw.Draw(tile)
        _portal(d, 470, 400, 190, 260, 363, open_frac=0.2, doors=0)
        D.draw_label(tile, 'ONE DOOR', center=(470, 190), color=SNOW, size=40)
    els.append(SC.accrue(clock, 13, 17, c_portal, kind='shape', eid='c_portal'))
    els.append(cap(13, 950, 662, size=32))

    def c_tons(tile, fw, fh):
        # MOVING: the door comes DOWN into the frame. One 0.55s arrival on a
        # subject that fills the frame -- the one moment in the chapter where
        # the object's weight is the information, so it gets the movement.
        # TOP EDGE RULE: cy - h*0.56 = 116, clear of the title band, and the
        # door still runs off the bottom edge.
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 391, rock=(158, 156, 156), deep=(90, 88, 90))
        _blast_door(d, 560, 430, 900, 560, 392, closed=True)
        D.draw_number(tile, '700', center=(560, 400), color=RED, size=210)
        D.draw_label(tile, 'TONS', center=(560, 600), color=RED, size=90)
    els.append(SC.layer(clock, 14, c_tons, j=15, kind='subject',
                        motion=SC.enter(clock, 14, dx=0, dy=64, dur=0.55)))
    # NO caption at b14. The art prints the number as a 210px '700' over a
    # 90px TONS -- that IS the sentence, and a caption saying "roughly seven
    # hundred tons" underneath it would be the same fact twice.

    def c_seal(tile, fw, fh):
        # The door swung open on its hinge with the red arrows shoving it shut.
        # It HOLDS for b15 AND b16 -- the payoff line lands on the same held
        # frame, which is what a persistent stage is for.
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 401, rock=(158, 156, 156), deep=(90, 88, 90))
        # cx=520 w=1240, not cx=470 w=1000. The narrower door left its right
        # jamb at x=1090 -- a hard 8px black vertical line with 190px of dead
        # rock to its right, so the door read as a small object parked in a big
        # empty field instead of a thing that fills the frame. Widening pushes
        # the jamb to 1289 (off-frame) and the dark void out to -50..1090, so
        # the opening IS the frame and both jambs exit the edges.
        _blast_door(d, 520, 380, 1240, 680, 402, closed=False)
        # The label moved UP onto the void. It used to sit at (1010, 620) --
        # down where the b16 caption also lives (that caption spans y 655-687),
        # so the two ran together as one text block. Up here it reads as printed
        # across the door and leaves the bottom band to the caption alone.
        # cy=200, not 240: the top shove-arrow sits at y=271 and at cy=240 the
        # label's descenders ran straight through it.
        D.draw_label(tile, 'SEALS COMPLETELY', center=(620, 200), color=RED,
                     size=50)
        # POINTING LEFT. He used to be at x=1180 in the stock 'pointing' pose,
        # which raises the RIGHT arm -- so he pointed away from the door, and
        # that arm ran 155px off the right edge (measured bbox 1042..1435 on a
        # 1280 frame) leaving a cut stub. 'pointingL' is the same arm on the
        # left, which aims at the door. x=1140 puts his rightmost ink at 1273,
        # 7px clear: at x=1150 it was 1283 and his dangling right arm was
        # guillotined by the edge, which reads as a bug rather than as a figure
        # cropped into the shot.
        SC.fullbody(d, 1140, 690, 500, pose='pointingL', expression='awed',
                    seed=403)
    els.append(SC.layer(clock, 15, c_seal, j=17, kind='subject', eid='c_seal'))
    # NO caption at b15. SEALS COMPLETELY is printed on the door.
    # cx=520, not 880: at 880 the caption spanned x 644-1115 and ran under the
    # figure (who occupies 905-1283), striking through his legs.
    els.append(cap(16, 520, 664, size=32))
# ===================================================================== #
    # STAGE D  b17-b21  "Inside the mountain, the air stays cold. The cold  #
    #                 keeps the machines stable. Roughly two hundred people #
    #                 work down there. The complex runs on its own power.   #
    #                 Diesel generators sit far below ground."              #
    # The MACHINE HALL is the persistent thing -- one dark rock room, five  #
    # cabinets against the back wall with their green lamps lit, holding    #
    # for all five beats. b17 adds the thermometer and the breath; b18 adds #
    # the STABLE label over the same cabinets. Only b19 (the corridor) and  #
    # b20 (the two cross-sections) repaint the frame, and b21 re-cuts HALF  #
    # of it -- the underground panel zooming in on the generators.          #
    # ===================================================================== #
    def d_hall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 461, rock=(146, 146, 150), deep=(70, 72, 80))
        # A near-black room needs the lit stone course for the engine's
        # hardcoded-INK title to read against. Called FIRST, before any fill
        # that would cover it.
        SC.title_backdrop(tile, 1461, col=(100, 104, 120))
        PA.fill_poly(tile, [(-30, 160), (W + 30, 150), (W + 30, 720),
                            (-30, 720)], (92, 94, 102), seed=462, value=0.07)
        # FIVE cabinets, not six: the sixth footprint is left empty so the
        # thermometer has somewhere to stand on the right without colliding.
        for k in range(5):
            x = 60 + k * 210
            b = [(x, 300), (x + 160, 288), (x + 160, 600), (x, 600)]
            PA.fill_poly(tile, b, STEEL_D, seed=470 + k, value=0.07)
            PA.hand_stroke(d, b, INK, 5, closed=True, seed=480 + k,
                           wavelength=90.0)
            for r in range(4):
                yy = 320 + r * 44
                PA.hand_stroke(d, [(x + 16, yy), (x + 144, yy - 8)],
                               (104, 112, 124), 4, closed=False,
                               seed=490 + k * 5 + r, wavelength=60.0)
            # STEADY indicator lights -- the "stable" the line is about
            for c in range(3):
                PA.fill_poly(tile, PA.ellipse_pts(x + 40 + c * 42, 570, 11, 11,
                                                  n=20), GREEN,
                             seed=500 + k * 3 + c, value=0.05)
        PA.hand_stroke(d, [(-30, 600), (W + 30, 596)], CONCRETE_D, 12,
                       closed=False, seed=510, wavelength=200.0)
    els.append(SC.stage(clock, 17, d_hall, j=22))

    def d_cold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        S.thermometer(d, 1150, 630, 430, 0.18, seed=440, hot=False)
        D.draw_label(tile, 'COLD', center=(1150, 205), color=SNOW, size=48)
    els.append(SC.layer(clock, 17, d_cold, j=18, kind='shape', eid='d_cold'))

    def d_breath(tile, fw, fh):
        # MOVING, small, and it is the only motion in the stage: the breath
        # drifting across the cold room is what makes a still frame read as
        # freezing. One beat of drift, then still.
        d = ImageDraw.Draw(tile)
        for k in range(4):
            x = 520 + k * 40
            y = 400 + (k % 2) * 26
            PA.hand_stroke(d, [(x, y), (x + 54, y - 18), (x + 100, y + 6)],
                           (196, 200, 210), 6, closed=False, seed=450 + k,
                           wavelength=70.0, vary=0.15)
    els.append(SC.layer(clock, 17, d_breath, j=18, kind='shape',
                        motion=SC.drift(clock, 17, 18, dx=64, dy=-26),
                        eid='d_breath'))
    # NO caption at b17: b16 is captioned and two captioned beats in a row is
    # a talking-heads rhythm, not a film. The machine hall is already the
    # standing room, so v1's separate cold-chamber full frame is gone too --
    # the frost breath and the thermometer carry "the air is cold and fixed"
    # on their own.

    def d_stable(tile, fw, fh):
        D.draw_label(tile, 'STABLE', center=(560, 205), color=GREEN, size=54)
    # REPLACES the COLD label: one word in the one clear space above the
    # cabinets, handed off rather than printed underneath itself.
    els.append(SC.layer(clock, 18, d_stable, j=19, kind='shape',
                        eid='d_stable'))
    # NO caption at b18. The green STABLE label over cabinets whose lamps are
    # already lit IS the sentence, and a caption under it repeats the word.

    def d_corridor(tile, fw, fh):
        # REPLACES the hall: a different room. The corridor vanishing to a lit
        # far door, coat hooks along both walls, and small figures in coats --
        # the room says "people live down here" and the caption supplies how
        # many.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (96, 98, 106), seed=521, value=0.08)
        PA.paper_overlay(tile, seed=522)
        PA.fill_poly(tile, [(560, 240), (720, 240), (760, 560), (520, 560)],
                     LAMP, seed=523, value=0.05)
        PA.hand_stroke(d, [(560, 240), (520, 560), (760, 560), (720, 240)],
                       INK, 6, closed=True, seed=524, wavelength=120.0)
        PA.fill_poly(tile, [(-30, 60), (560, 240), (520, 560), (-30, 720)],
                     (118, 120, 128), seed=525, value=0.07)
        PA.fill_poly(tile, [(W + 30, 60), (720, 240), (760, 560), (W + 30, 720)],
                     (118, 120, 128), seed=526, value=0.07)
        PA.fill_rect(tile, [-30, 560, W + 30, 720], (86, 88, 96), seed=527,
                     value=0.07)
        # coat hooks in a row: the wall furniture of a staffed post
        for k in range(9):
            x = 70 + k * 142
            PA.hand_stroke(d, [(x, 260), (x, 190)], STEEL_D, 6,
                           closed=False, seed=530 + k, wavelength=60.0)
            if k % 2 == 0:
                coat = [(x - 26, 260), (x + 26, 260), (x + 20, 400),
                        (x - 20, 400)]
                PA.fill_poly(tile, coat, (84, 96, 116), seed=540 + k,
                             value=0.07)
                PA.hand_stroke(d, coat, INK, 4, closed=True, seed=550 + k,
                               wavelength=70.0)
        for k, x in enumerate((200, 470, 810, 1080)):
            SC.fullbody(d, x, 700 - k % 2 * 18, 330, pose='standing',
                        expression='neutral', seed=560 + k)
    els.append(SC.layer(clock, 19, d_corridor, j=20, kind='character',
                        eid='d_corridor'))
    els.append(cap(19, 640, 664, size=32, dark=True))
    # "roughly two hundred" is a NUMBER the drawing cannot say, so this beat is
    # captioned even though the corridor is full of people. v1's 'ABOUT 200
    # STAFF' label is dropped: the caption is that sentence, and printing both
    # stacked the same claim twice in one frame.

    def d_power(tile, fw, fh):
        # Two cross-sections in one frame: the surface city with power on the
        # left, the underground machine hall on the right, and the cable
        # between them SEVERED -- which is the whole of "it runs on its own
        # power" without a word.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 204, 214), seed=571, value=0.05)
        PA.paper_overlay(tile, seed=572)
        PA.fill_rect(tile, [-20, 330, 800, 740], (166, 176, 188), seed=573,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 330), (800, 330)], INK, 6, closed=False,
                       seed=574, wavelength=150.0)
        for k in range(7):
            x = 20 + k * 88
            hh = 90 + (k * 47) % 150
            PA.fill_rect(tile, [x, 330 - hh, x + 62, 332], (146, 156, 172),
                         seed=575 + k, value=0.07)
            PA.hand_stroke(d, [(x, 330 - hh), (x + 62, 330 - hh),
                               (x + 62, 332), (x, 332)], INK, 4, closed=True,
                           seed=580 + k, wavelength=60.0)
        # the severed cable: it comes down from the city and STOPS in mid-air
        PA.hand_stroke(d, [(600, 300), (700, 400), (800, 470)], STEEL_D, 10,
                       closed=False, seed=593, wavelength=110.0)
        D.draw_arrow(tile, (860, 520), (760, 452), color=RED, width=9, head=44)
        D.draw_red_x(tile, [712, 402, 812, 502])
        # TOP EDGE RULE: the underground panel starts at x=812, clear of the
        # rect engine3 stamps the title into (x 484..796).
        PA.fill_rect(tile, [812, 0, 1300, 740], (58, 60, 68), seed=594,
                     value=0.07)
        PA.hand_stroke(d, [(812, 0), (812, 740)], INK, 6, closed=False,
                       seed=595, wavelength=140.0)
        PA.hand_stroke(d, [(812, 200), (1300, 200)], INK, 6, closed=False,
                       seed=596, wavelength=170.0)
        _generator(d, 1000, 690, 340, 260, 597)
        D.draw_label(tile, 'ITS OWN POWER', center=(1020, 130), color=SNOW,
                     size=44)
    els.append(SC.layer(clock, 20, d_power, j=21, kind='subject', eid='d_power'))
    # NO caption at b20. The severed cable with the red X is the sentence, and
    # ITS OWN POWER is printed at the head of the underground panel.

    def d_generators(tile, fw, fh):
        # HALF a repaint, not a whole one: the underground panel from b20 is
        # re-cut as the deep generator hall -- rock, a row of generator sets
        # cropped left and right, fuel drums along the floor -- while the
        # surface city on the left of the frame stays exactly as it was. The
        # label hands off from ITS OWN POWER to DEEP UNDERGROUND.
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 601, rock=(150, 146, 146), deep=(64, 64, 72))
        PA.fill_poly(tile, [(770, 0), (1300, 0), (1300, 740), (770, 740)],
                     (84, 84, 92), seed=602, value=0.07)
        PA.hand_stroke(d, [(770, 250), (1300, 240)], INK, 8, closed=False,
                       seed=603, wavelength=200.0)
        for k in range(5):
            x = 830 + k * 100
            PA.hand_stroke(d, [(x, 250), (x, 210)], INK, 8, closed=False,
                           seed=610 + k, wavelength=60.0)
        for k in range(2):
            _generator(d, 880 + k * 300, 720, 300, 250, 620 + k)
        for k in range(4):
            _drum(d, 800 + k * 130, 736, 84, 118, 650 + k)
        D.draw_label(tile, 'DEEP UNDERGROUND', center=(1035, 165), color=SNOW,
                     size=40)
    els.append(SC.layer(clock, 21, d_generators, j=22, kind='subject',
                        eid='d_generators'))
    els.append(cap(21, 330, 640, size=32))
    # The caption sits on the surface half, which is still the b20 card: the
    # words belong to the underground half but the words are on the light
    # ground, because ink on the dark machine hall measures about 1.3:1.

    # ===================================================================== #
    # STAGE E  b22-b25  "No power line ever reaches the mountain. Water     #
    #                 rises from springs in the rock. The tanks hold        #
    #                 thousands of gallons daily. Nothing from outside      #
    #                 reaches this place."                                 #
    # Each of these four beats is a different place -- outside on the        #
    # hillside, inside on the water, inside on the tanks, inside on the      #
    # sealed room -- so the stage backdrop is the exterior hillside and each #
    # beat replaces it. The stage still earns its keep: the mountain in the #
    # backdrop is the SAME crop and seed as stages A and B, so the three     #
    # exterior stages read as one continuous place, and the b23/b24 water    #
    # and tanks both come out of the same rock.                             #
    # ===================================================================== #
    def e_hill(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 661, sky=(186, 196, 210), ground=(158, 162, 166))
        _massif(d, 900, HZ + 40, 900, 112, 662, snow=False)
    els.append(SC.stage(clock, 22, e_hill, j=26))

    def e_noline(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k, x in enumerate((80, 320, 560)):
            _pylon(d, x, HZ + 40, 300, 670 + k)
        # the catenary runs between the first two pylons and then BREAKS --
        # two dangling ends with a gap, which is the whole beat
        for k in range(2):
            x0 = 80 + k * 240
            PA.hand_stroke(d, [(x0, HZ - 260), (x0 + 120, HZ - 190),
                               (x0 + 240, HZ - 260)], STEEL_D, 5, closed=False,
                           seed=680 + k, wavelength=120.0)
        PA.hand_stroke(d, [(560, HZ - 260), (620, HZ - 232)], STEEL_D, 5,
                       closed=False, seed=682, wavelength=80.0)
        D.draw_red_x(tile, [596, HZ - 300, 700, HZ - 196])
    els.append(SC.layer(clock, 22, e_noline, j=23, kind='shape', eid='e_noline'))
    # NO caption at b22. The severed catenary with the red X says it, and the
    # presenter's bubble will say it again at b23 in the character's own voice.

    def e_nobody_in(tile, fw, fh):
        # MOVING, small: the presenter steps in and points at the dead line.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 880, 700, 420, pose='pointing', expression='skeptic',
                    seed=684)
        D.draw_bubble(tile, 'no line in', (1040, 480), tail_to=(980, 540),
                      font_size=34, max_w=240)
    els.append(SC.layer(clock, 22, e_nobody_in, j=23, kind='character',
                        motion=SC.enter(clock, 22, dx=-120, dur=ARRIVE),
                        eid='e_nobody_in'))

    def e_springs(tile, fw, fh):
        # Water coming OUT of the rock: the granite crack, the drips, the pool
        # cropped by the bottom edge. REPLACES the hillside.
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 691, rock=(168, 152, 152), deep=(96, 92, 96))
        # TOP EDGE RULE: the crack opens at y=110, clear of the title band.
        crack = [(700, 110), (742, 220), (700, 380), (770, 560), (748, 640)]
        PA.hand_stroke(d, crack, DEEPER, 14, closed=False, seed=692,
                       wavelength=150.0)
        PA.hand_stroke(d, [(660, 110), (700, 220), (660, 380)], (200, 186, 184),
                       8, closed=False, seed=693, wavelength=120.0)
        for k in range(4):
            y = 250 + k * 110
            PA.fill_poly(tile, PA.ellipse_pts(716 + k * 12, y, 10, 15, n=20),
                         (128, 172, 190), seed=694 + k, value=0.05)
        # the pool, cropped by the bottom edge
        PA.fill_rect(tile, [-30, 640, W + 30, 740], (108, 150, 172), seed=700,
                     value=0.07)
        PA.hand_stroke(d, [(-30, 640), (W + 30, 636)], (70, 110, 136), 8,
                       closed=False, seed=701, wavelength=200.0)
        for k in range(6):
            yy = 668 + k * 16
            PA.hand_stroke(d, [(180 + k * 150, yy), (280 + k * 150, yy)],
                           (140, 178, 198), 4, closed=False, seed=710 + k,
                           wavelength=60.0)
        for k, r in enumerate((70, 110, 150)):
            PA.hand_stroke(d, PA.ellipse_pts(742, 640, r, r * 0.24, n=40),
                           (168, 202, 220), 4, closed=True, seed=720 + k,
                           wavelength=90.0)
        D.draw_label(tile, 'SPRINGS IN THE ROCK', center=(300, 200),
                     color=SNOW, size=42)
    els.append(SC.layer(clock, 23, e_springs, j=24, kind='shape',
                        eid='e_springs'))
    # NO caption at b23. SPRINGS IN THE ROCK is printed on the rock face.

    def e_tanks(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 731, rock=(150, 148, 148), deep=(74, 76, 84))
        # low ceiling with a strip light
        PA.fill_rect(tile, [-20, -20, W + 20, 190], (108, 108, 116), seed=732,
                     value=0.07)
        for k in range(3):
            PA.hand_stroke(d, [(120 + k * 400, 120), (420 + k * 400, 116)],
                           LAMP, 16, closed=False, seed=740 + k,
                           wavelength=110.0)
        PA.hand_stroke(d, [(-20, 190), (W + 20, 184)], INK, 7, closed=False,
                       seed=745, wavelength=190.0)
        PA.fill_rect(tile, [-20, 600, W + 20, 740], (92, 94, 100), seed=746,
                     value=0.07)
        for k in range(5):
            x0 = 30 + k * 268
            _water_tank(d, x0, 260, x0 + 200, 600, 750 + k, level=0.55 + 0.08 * k)
        D.draw_label(tile, 'THOUSANDS OF GALLONS', center=(640, 664),
                     color=SNOW, size=42)
    els.append(SC.layer(clock, 24, e_tanks, j=25, kind='shape', eid='e_tanks'))
    # NO caption at b24, and this is the correction. A previous pass added
    # cap(24, 640, 224) on the reasoning that the caption was the sentence and
    # the drawn label should go -- but it left BOTH in place, and the comment
    # below claimed the label had been dropped. Rendered, the frame carried the
    # same line twice, once as a caption straddling four tank arches where it
    # was unreadable and once as a label on the floor. Saying a thing twice in
    # one frame is the telling-AND-showing redundancy, not emphasis.
    # The drawn label wins: it is legible, it sits in clear floor, and it is
    # the sentence. The caption is dropped.

    def e_sealed(tile, fw, fh):
        # THE SEALED ROOM: a wall of concrete with ONE sealed hatch, the
        # presenter small and alone inside it. The chapter's argument closing
        # its own loop -- "nothing from outside reaches this place".
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DEEPER, seed=761, value=0.10)
        PA.paper_overlay(tile, seed=762)
        SC.title_backdrop(tile, 1761, col=(100, 104, 120))
        PA.fill_rect(tile, [-20, 140, W + 20, 700], (78, 80, 88), seed=763,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 140), (W + 20, 132)], INK, 8, closed=False,
                       seed=764, wavelength=190.0)
        _blast_door(d, 900, 420, 480, 400, 765, closed=True)
        SC.closeup(d, 320, 400, 205, 'worried', 766)
        D.draw_bubble(tile, 'nothing gets in', (470, 130), tail_to=(330, 300),
                      font_size=38, max_w=300)
    els.append(SC.layer(clock, 25, e_sealed, j=26, kind='character',
                        eid='e_sealed'))
    # NO caption at b25. The bubble "nothing gets in" is the sentence, in the
    # character's own voice, which is exactly where a caption would be redundant.

    # ===================================================================== #
    # STAGE F  b26-b29  "This was the space defence centre. Satellites passed#
    #                 directly over the roof. Sensors in here watched for   #
    #                 launches. The warning clocks started in this room."    #
    # The stage backdrop is the chapter's SECOND HERO: the same cross-      #
    # section construction as b09, so the two hero frames are visibly the    #
    # same place -- except the exposed face now carries the OPERATIONS FLOOR #
    # instead of the fifteen buildings, and the badge is stamped on the      #
    # solid rock to the right. It is held for the first beat only, because    #
    # the next three beats are what the room is FOR and they all happen at   #
    # night over the roof.                                                  #
    # ===================================================================== #
    def f_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 771, sky=(200, 206, 216), ground=(168, 168, 172))
        _cross_section(d, 980, H + 80, 1180, 30, 772, chambers=False)
        room = [(-30, 330), (560, 292), (560, 800), (-30, 800)]
        PA.fill_poly(tile, room, (58, 60, 70), seed=773, value=0.06)
        PA.hand_stroke(d, [(-30, 330), (560, 292)], INK, 7, closed=False,
                       seed=774, wavelength=170.0)
        _console_bank(d, 10, 560, 720, 775, rows=2, green=True)
        _norad_badge(d, 990, 420, 190, 776)
        # No in-card draw_title: engine3 stamps the scene title last, on top of
        # every element, so a card-local title overprints the title strip.
    els.append(SC.stage(clock, 26, f_room, j=30))
    els.append(cap(26, 990, 176, size=32))
    # b26 is captioned because it is the room's own introduction and the
    # badge carries no words -- the crest says "military command post" without
    # saying what the post was FOR.

    def f_night(tile, fw, fh):
        # REPLACES: the same roof, at night, from above. Stars, the massif
        # cropped by the bottom edge, three orbit arcs, three satellites with
        # beams crossing down onto the roof, and the radar scope over the lot.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 52, 74), seed=781, value=0.10)
        PA.paper_overlay(tile, seed=782)
        SC.title_backdrop(tile, 1781, col=(100, 104, 120))
        for k in range(60):
            a = (k * 2.399) % 6.283
            rr = 40 + (k * 83) % 700
            x = 640 + rr * math.cos(a) * 1.25
            y = 320 + rr * math.sin(a) * 0.7
            if 0 < x < W and 0 < y < 560:
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(226, 232, 244))
        _massif(d, 640, 760, 1000, 470, 783, snow=True, rock=(88, 92, 106),
                shade=(66, 70, 84))
        for k in range(3):
            orb = PA.arc_pts(640, 900, 420 + k * 150, 560 + k * 90,
                             208, 332, n=48)
            PA.hand_stroke(d, orb, (108, 130, 176), 4, closed=False,
                           seed=790 + k, wavelength=180.0)
        # only the two STATIC satellites are drawn here; the third is the
        # moving element f_sat, added at b27, so it is not drawn twice
        for k, (sx, sy) in enumerate(((620, 150), (1000, 220))):
            _sat(d, sx, sy, 66, 800 + k)
            D.draw_arrow(tile, (sx, sy + 90), (sx + 130, 620), color=RED,
                         width=7, head=40)
    els.append(SC.layer(clock, 27, f_night, j=28, kind='subject', eid='f_night'))

    def f_sat(tile, fw, fh):
        # MOVING: ONE satellite crossing the sky, 300px over a beat (~94px/s,
        # over the 60px/s floor motion_profile needs). It is 132px wide, so a
        # moving satellite does not read as a repainted frame. The other two
        # stay put -- one moving thing per beat is the rule, not three. Its
        # beam crosses with it, because a satellite with no beam to the roof
        # is just a dot in the sky.
        d = ImageDraw.Draw(tile)
        _sat(d, 240, 210, 66, 800)
        D.draw_arrow(tile, (240, 300), (370, 620), color=RED, width=7, head=40)
    els.append(SC.layer(clock, 27, f_sat, j=28, kind='subject',
                        motion=SC.drift(clock, 27, 28, dx=300, dy=0),
                        eid='f_sat'))
    # NO caption at b27. b26 and b28 are both captioned, and three captioned
    # beats running would turn the sequence into a slide deck. The single
    # crossing satellite WITH its beam landing on the summit is the sentence:
    # one object, in motion, arriving overhead, is a thing passing directly
    # over the roof -- which is the only thing this beat needed to say.

    def f_radar(tile, fw, fh):
        # REPLACES the sky: we are inside now. The scope dominates and runs
        # off the BOTTOM edge (cy=410 puts the rim at y=76, clear of the title
        # band), with the console bank to its right.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (56, 58, 68), seed=811, value=0.08)
        PA.paper_overlay(tile, seed=812)
        SC.title_backdrop(tile, 1811, col=(100, 104, 120))
        _radar(d, 520, 410, 330, 813, sweep=-40, blips=4)
        PA.hand_stroke(d, [(900, 84), (900, 720)], INK, 7, closed=False,
                       seed=814, wavelength=180.0)
        _console_bank(d, 930, 1330, 700, 815, rows=1, green=True)
    els.append(SC.layer(clock, 28, f_radar, j=29, kind='subject', eid='f_radar'))
    els.append(cap(28, 300, 664, size=32, dark=True))
    # b28 IS captioned: the scope is a green circle and four blips, and nothing
    # in the drawing distinguishes watching for launches from watching for
    # anything else. This is the one beat in the stage where the picture
    # genuinely cannot carry the sentence.

    def f_warn(tile, fw, fh):
        # THE ESCALATION. The same room, the same scope, the same console --
        # and the lights have gone red. One thing changes and that is the
        # whole beat. MOVING: the clock hand jumps, small and on its own.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (74, 44, 46), seed=821, value=0.11)
        PA.paper_overlay(tile, seed=822)
        SC.title_backdrop(tile, 1821, col=(100, 104, 120))
        _radar(d, 500, 410, 330, 823, sweep=-30, arc=120, blips=3, warm=True)
        PA.hand_stroke(d, [(880, 84), (880, 720)], INK, 7, closed=False,
                       seed=824, wavelength=180.0)
        _console_bank(d, 910, 1330, 700, 825, rows=1, lamps=False, green=True)
        face = PA.ellipse_pts(1090, 300, 140, 140, n=48)
        PA.fill_poly(tile, face, (250, 246, 236), seed=826, value=0.04)
        PA.hand_stroke(d, face, INK, 7, closed=True, seed=827, wavelength=110.0)
        for k in range(12):
            a = k * math.pi / 6.0
            PA.hand_stroke(d, [(1090 + 108 * math.cos(a), 300 + 108 * math.sin(a)),
                               (1090 + 122 * math.cos(a), 300 + 122 * math.sin(a))],
                           INK, 4, closed=False, seed=828 + k, wavelength=40.0)
        PA.hand_stroke(d, [(1090, 300), (1090, 218)], INK, 7, closed=False,
                       seed=841, wavelength=60.0)
        D.draw_label(tile, 'WARNING', center=(1090, 500), color=RED, size=48)
    els.append(SC.layer(clock, 29, f_warn, j=30, kind='subject', eid='f_warn'))

    def f_hand(tile, fw, fh):
        # MOVING, small: the hand jumping to the warning position. 0.45s, and
        # it is 96px long, so nothing else in the frame changes while it moves.
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(1090, 300), (1090 + 96, 300 - 78)], RED, 9,
                       closed=False, seed=840, wavelength=70.0)
    els.append(SC.layer(clock, 29, f_hand, j=30, kind='shape',
                        motion=SC.enter(clock, 29, dx=0, dy=-44, dur=0.45),
                        eid='f_hand'))
    # NO caption at b29. WARNING is printed under the clock and the room has
    # gone red; the sentence is carried.

    # ===================================================================== #
    # STAGE G  b30-b33  "Outside, the mountain wears a painted forest. The  #
    #                 trees are painted concrete slabs. They hide the       #
    #                 ventilation towers behind them. From the air, nothing #
    #                 stands out at all."                                   #
    # The AERIAL SLOPE is the persistent thing: sky over a grey hillside    #
    # cropped by the bottom edge, held across two beats while the rows of   #
    # painted slabs ARRIVE on it and then one single slab is cut into,      #
    # close. b32 puts the vents behind the same slabs; b33 pulls all the    #
    # way back to the whole massif from the air.                            #
    # ===================================================================== #
    def g_slope(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 851, sky=(206, 212, 222), ground=(160, 162, 166))
        slope = [(-30, 300), (400, 250), (900, 300), (W + 30, 380),
                 (W + 30, 740), (-30, 740)]
        PA.fill_poly(tile, slope, (150, 152, 156), seed=852, value=0.09)
        PA.hand_stroke(d, [(-30, 300), (400, 250), (900, 300), (W + 30, 380)],
                       INK, 6, closed=False, seed=853, wavelength=190.0)
    els.append(SC.stage(clock, 30, g_slope, j=34))
    els.append(cap(30, 640, 140, size=32))
    # b30 is captioned: the whole conceit of the stage is a forest that is not
    # a forest, and the first beat has to name what you are looking at before
    # the close-up explains it.

    def g_rows(tile, fw, fh):
        # THE PAINTED FOREST ACCRUES: two ranks of concrete slabs marching
        # down the slope, the near ones cropped by the bottom edge. They
        # arrive and stay -- the hillside gains a forest.
        d = ImageDraw.Draw(tile)
        for k in range(9):
            t = k / 8.0
            x = -20 + t * 1340
            y = 300 + t * 120
            _painted_tree(d, x, y + 40, 210 - t * 90, 860 + k, col=CONCRETE)
        for k in range(7):
            t = k / 6.0
            _painted_tree(d, 40 + t * 1220, 730 - t * 40, 250 + t * 60,
                          880 + k, col=CONCRETE_D)
    els.append(SC.accrue(clock, 30, 32, g_rows, kind='shape', eid='g_rows'))
    # The rows accrue only as far as b31: at b31 one single slab is cut into,
    # close, and a forest of small slabs behind a giant one would be a crowd.

    def g_slab(tile, fw, fh):
        # ONE SLAB, huge, cropped by both side edges -- it IS the frame. The
        # close-up conceit: the painted tree is now a dark CONCRETE_D mass
        # filling most of the frame, so its stepped conifer silhouette and the
        # drip marks are unmistakable. It used to be light CONCRETE on a light
        # grey fill -- barely 50 levels apart -- so the "tree" vanished into the
        # background and the nine white brush strokes over it became the most
        # prominent thing in frame, reading as random scratches. Now the slab
        # is the darkest mass on screen and the strokes are gone.
        # h=660, not 880: _painted_tree's silhouette runs to base_y - h*0.98,
        # so at h=880 the top two of its three conifer tiers sat at NEGATIVE y
        # and the "tree" cropped to a single wide trapezoid with no apex. At
        # h=660 the apex lands at y=123, just under the title band, so all
        # three tiers and the drip marks are on screen.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (168, 170, 174), seed=891, value=0.09)
        PA.paper_overlay(tile, seed=892)
        # A dark backdrop behind the slab silhouette so the light drips and
        # outline read against it.
        PA.fill_rect(tile, [0, 0, W, H], (128, 130, 134), seed=895, value=0.10)
        _painted_tree(d, 640, 770, 660, 893, w=560, col=(96, 98, 102), drips=True)
        SC.title_backdrop(tile, 894, col=(168, 170, 174))
        # Label across the top of the slab. Light (SNOW), not INK -- the user
        # rule is text is never gray or black, and this slab is a dark mass.
        D.draw_label(tile, 'PAINTED CONCRETE', center=(560, 130), color=SNOW,
                     size=44)
    els.append(SC.layer(clock, 31, g_slab, j=32, kind='shape', eid='g_slab'))
    # NO caption at b31. PAINTED CONCRETE is printed across the slab.

    def g_pointer(tile, fw, fh):
        # MOVING, small: the presenter steps in and points at the slab he is
        # standing next to. He used to stand at x=1090 in the stock 'pointing'
        # pose (right arm raised) with enter(dx=+110) -- so he pointed AWAY from
        # the slab, the entry motion shoved him 110px further right on arrival,
        # and the already-long right arm ran off the frame edge entirely.
        # 'pointingL' aims him at the slab (which is centre-left); the arrival
        # is now a short vertical drop so nothing is pushed off the right edge.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 1010, 700, 430, pose='pointingL', expression='awed',
                    seed=910)
    els.append(SC.layer(clock, 31, g_pointer, j=32, kind='character',
                        motion=SC.enter(clock, 31, dx=0, dy=40, dur=ARRIVE),
                        eid='g_pointer'))
    # NO caption at b31 -- the label on the slab says it.

    def g_vents(tile, fw, fh):
        # The vents BEHIND the same slabs: the towers are drawn first, then
        # the slabs go in front of them. That ordering is the whole reveal.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (158, 160, 164), seed=921, value=0.09)
        PA.paper_overlay(tile, seed=922)
        slope = [(-30, 340), (W + 30, 300), (W + 30, 740), (-30, 740)]
        PA.fill_poly(tile, slope, (146, 148, 152), seed=923, value=0.09)
        PA.hand_stroke(d, [(-30, 340), (W + 30, 300)], INK, 6, closed=False,
                       seed=924, wavelength=190.0)
        for k, x in enumerate((250, 620, 990)):
            _vent_tower(d, x, 330 - k * 8, 210, 930 + k, col=(128, 130, 136))
        for k in range(7):
            t = k / 6.0
            _painted_tree(d, 90 + t * 1120, 720 - t * 30, 230 + t * 70,
                          940 + k, col=CONCRETE_D)
    els.append(SC.layer(clock, 32, g_vents, j=33, kind='shape', eid='g_vents'))
    els.append(cap(32, 640, 664, size=32))
    # b32 IS captioned, and v1's THEY HIDE THE VENTS label is dropped -- the
    # caption is that sentence and the two of them together said it twice.

    def g_air(tile, fw, fh):
        # THE PULL-BACK: the whole massif from the air, its painted trees now
        # a scatter of grey specks. The presenter stands small on the flank.
        # TOP EDGE RULE: peak_y 112 keeps the summit clear of the title band.
        d = ImageDraw.Draw(tile)
        _sky(tile, 951, sky=(190, 200, 214), ground=(162, 164, 168))
        _massif(d, 640, 780, 1300, 112, 952, snow=False, rock=(158, 160, 164),
                shade=(140, 142, 148))
        for k in range(11):
            t = k / 10.0
            _painted_tree(d, -40 + t * 1360, 640 + (k % 3) * 90,
                          90 + (k % 4) * 26, 960 + k, col=CONCRETE_D,
                          drips=False)
        SC.fullbody(d, 1120, 315, 190, pose='shrug', expression='neutral',
                    seed=975)
    els.append(SC.layer(clock, 33, g_air, j=34, kind='character', eid='g_air'))
    # NO caption at b33. The whole massif camouflaged into its own hillside IS
    # "from the air, nothing stands out at all" -- the most self-explaining
    # frame in the chapter.

    # ===================================================================== #
    # STAGE H  b34-b38  "Now for the part nobody confirms. People say it     #
    #                 still stays staffed. People say the government still  #
    #                 goes down. They quote one number about survival.      #
    #                 Ninety percent, though nobody has confirmed it."      #
    # The closing movement is RUMOUR, and the staging says so: the hillside #
    # is the last daylight frame and it stays the stage backdrop for the    #
    # whole stage, so the road at b36 ACCRUES onto the same sky the massif  #
    # stood in at b34 rather than arriving as a new place. The corridor,    #
    # the chalkboard and the finale door replace it in turn.                 #
    # ===================================================================== #
    def h_hill(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 981, sky=(206, 212, 222), ground=(172, 172, 176))
    els.append(SC.stage(clock, 34, h_hill, j=39))

    def h_massif(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _massif(d, 900, H + 60, 900, 240, 982, snow=True)
        SC.closeup(d, 360, 380, 215, 'deadpan', 983)
        D.draw_bubble(tile, 'nobody confirms this part', (620, 110),
                      tail_to=(430, 300), font_size=34, max_w=380)
    els.append(SC.layer(clock, 34, h_massif, j=35, kind='character',
                        eid='h_massif'))
    # NO caption at b34. The bubble is the line, and the presenter's deadpan
    # close-up is the tone -- this is the beat where the film admits it is
    # repeating hearsay.

    def h_corridor(tile, fw, fh):
        # The corridor from b19 comes BACK at b35, same art, same seeds -- the
        # same room the "two hundred people" lived in, so the staffing claim
        # lands on a room the viewer already knows.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (104, 106, 114), seed=991, value=0.08)
        PA.paper_overlay(tile, seed=992)
        PA.fill_poly(tile, [(-30, 80), (560, 240), (520, 580), (-30, 740)],
                     (126, 128, 136), seed=993, value=0.07)
        PA.fill_poly(tile, [(W + 30, 80), (760, 240), (800, 580), (W + 30, 740)],
                     (126, 128, 136), seed=994, value=0.07)
        PA.fill_poly(tile, [(560, 240), (760, 240), (800, 580), (520, 580)],
                     LAMP, seed=995, value=0.05)
        PA.fill_rect(tile, [-30, 580, W + 30, 740], (92, 94, 100), seed=996,
                     value=0.07)
        PA.hand_stroke(d, [(560, 240), (520, 580), (800, 580), (760, 240)],
                       INK, 6, closed=True, seed=997, wavelength=120.0)
        # The console bank is the subject, so it is drawn at working size and
        # the staff are clustered AROUND it rather than spread to the frame
        # edges. v1 stood four figures at 340px on the far left and right with
        # a small console between them, and the frame read as two groups of
        # bystanders watching a diagram.
        _console_bank(d, 360, 940, 700, 998, rows=2, green=True)
        # POSES, NOT 'standing'. Four 'standing' figures render as four
        # coat-hangers -- arms straight down and out with no elbow break --
        # and a corridor of coat-hangers reads as an empty corridor. Each of
        # these four has a real elbow and a different silhouette.
        crew = [(95, 430, 'pointing', 'neutral'),
                (370, 415, 'armscrossed', 'deadpan'),
                (930, 425, 'shrug', 'skeptic'),
                (1195, 440, 'handsup', 'neutral')]
        for k, (x, hgt, pose, expr) in enumerate(crew):
            SC.fullbody(d, x, 700, hgt, pose=pose, expression=expr,
                        seed=1000 + k * 7)
    els.append(SC.layer(clock, 35, h_corridor, j=36, kind='character',
                        eid='h_corridor'))
    # NO caption at b35. A corridor with people at the consoles IS "still
    # staffed", and the sentence is a rumour the picture is illustrating, not
    # a fact being asserted.

    def h_cars(tile, fw, fh):
        # THE PLAIN CARS. Four identical pale bodies in a queue and one black
        # one bigger than the rest and CROPPED BY THE RIGHT EDGE. The sameness
        # is the point, so nobody has to be named, and the odd one out is the
        # one you cannot see into. FRAME-FILL: the queue runs the full width at
        # working size, the nearest car is cut by the frame instead of parked
        # inside it, and every wheel is cut by the bottom edge. It accrues onto
        # the stage's own sky, so the road arrives at the same hillside the
        # massif was standing in at b34 rather than in a new place.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [-20, 300, W + 20, 740], (112, 114, 120), seed=1012,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 302), (W + 20, 296)], INK, 8, closed=False,
                       seed=1013, wavelength=210.0)
        # ONE row of dashes, sitting low and just above the queue, so it reads
        # as the centre line running away behind the cars. Three receding rows
        # were tried first and scattered white marks all over the empty road,
        # which read as debris rather than as a road.
        for j in range(-1, 9):
            xx = -60 + j * 240
            PA.hand_stroke(d, [(xx, 430), (xx + 118, 428)], SNOW, 9,
                           closed=False, seed=1014 + j, wavelength=80.0)

        def car(x, w, ybase, pale, seed):
            bh = int(w * 0.30)
            ch = int(w * 0.26)
            col = (150, 154, 162) if pale else (34, 36, 42)
            glass = (96, 104, 116) if pale else (20, 22, 28)
            body = [(x, ybase), (x + w, ybase), (x + w, ybase - bh),
                    (x, ybase - bh)]
            PA.fill_poly(tile, body, col, seed=seed, value=0.06)
            PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1,
                           wavelength=90.0)
            cabin = [(x + w * 0.22, ybase - bh), (x + w * 0.34, ybase - bh - ch),
                     (x + w * 0.70, ybase - bh - ch), (x + w * 0.80, ybase - bh)]
            PA.fill_poly(tile, cabin, glass, seed=seed + 2, value=0.05)
            PA.hand_stroke(d, cabin, INK, 6, closed=True, seed=seed + 3,
                           wavelength=80.0)
            # tyres drawn solid, NOT painted: PA.fill_poly on a shape this
            # small bursts it into a star splat and it stops reading as a wheel
            r = int(w * 0.115)
            for cx in (x + w * 0.24, x + w * 0.78):
                d.ellipse([cx - r, ybase - r, cx + r, ybase + r], fill=INK)
                d.ellipse([cx - r * 0.42, ybase - r * 0.42,
                           cx + r * 0.42, ybase + r * 0.42], fill=col)

        for k, x in enumerate((-150, 110, 370, 630)):
            car(x, 300, 700, True, 1030 + k * 10)
        car(900, 470, 706, False, 1060)
    els.append(SC.accrue(clock, 36, 39, h_cars, kind='shape', eid='h_cars'))
    els.append(cap(36, 640, 180, size=32))
    # b36 IS captioned and it is the one beat in the stage where the words are
    # the ONLY signal -- a row of unremarkable cars says nothing about who is
    # in them, and the sentence "the government still goes down" is the whole
    # content of the rumour.

    def h_chalkboard(tile, fw, fh):
        # THE QUOTED NUMBER. A chalkboard filling the frame with 90% and a red
        # question mark, and a chalk line rubbed half out -- the same fact,
        # half-erased. The board's top rail sits at y=112, clear of the title.
        d = ImageDraw.Draw(tile)
        SC.title_backdrop(tile, 2071, col=(100, 104, 120))
        PA.fill_rect(tile, [0, 86, W, H], (58, 66, 60), seed=1071, value=0.09)
        PA.paper_overlay(tile, seed=1072)
        board = [(-30, 122), (W + 30, 112), (W + 30, 700), (-30, 690)]
        PA.fill_poly(tile, board, (44, 62, 54), seed=1073, value=0.07)
        PA.hand_stroke(d, board, (150, 122, 90), 18, closed=True, seed=1074,
                       wavelength=210.0)
        D.draw_number(tile, '90%', center=(430, 380), color=SNOW, size=280)
        D.draw_number(tile, '?', center=(980, 380), color=RED, size=280)
        # a chalk line half-erased: the same fact, rubbed out
        PA.hand_stroke(d, [(180, 560), (900, 548)], SNOW, 7, closed=False,
                       seed=1075, wavelength=160.0, vary=0.3)
        for k in range(8):
            x = 880 + k * 34
            PA.hand_stroke(d, [(x, 556), (x + 12, 556)], (150, 158, 148), 6,
                           closed=False, seed=1080 + k, wavelength=40.0,
                           vary=0.2)
    els.append(SC.layer(clock, 37, h_chalkboard, j=38, kind='subject',
                        eid='h_chalkboard'))
    # NO caption at b37. A 280px '90%' beside a 280px red '?' IS the claim and
    # the doubt at the same time; a sentence over it would add nothing.

    def h_finale(tile, fw, fh):
        # THE FINALE: the sealed door again, the one image the chapter has
        # been building to, held still and alone in a near-black frame with
        # one cold light on it. TOP EDGE RULE: the door's own top edge lands at
        # y=150, well clear of the title band, and the unlit outer frame closes
        # off all four sides and still owns them. The title band keeps most of its
        # value (dim=0.9): at the original dim=0.45 the backdrop resolved to
        # (45,47,54) and the INK title landed on it at roughly 1.2:1 -- the
        # full-res b38 frame showed 'Cheyenne Mountain' as a dark smudge, and
        # the coverage gate's TITLE UNREADABLE check caught it. The finale's
        # darkness is carried by the frame below the band and the closed door;
        # the title has to stay legible.
        d = ImageDraw.Draw(tile)
        SC.title_backdrop(tile, 2091, col=(100, 104, 120), dim=0.9)
        PA.fill_rect(tile, [0, 86, W, H], DEEPER, seed=1091, value=0.11)
        PA.paper_overlay(tile, seed=1092)
        _blast_door(d, 640, 480, 900, 660, 1093, closed=True)
        # THE COLD LIGHT. A wedge falling from the lamp onto the door. It is
        # drawn AFTER the door and it is BRIGHTER than the door: a beam darker
        # than what it falls on reads as a shadow occluding the door, which is
        # the opposite of the intended one light in a dark room.
        beam = [(596, 104), (652, 104), (846, 320), (416, 320)]
        PA.fill_poly(tile, beam, (168, 176, 194), seed=1094, value=0.03)
        PA.hand_stroke(d, [(540, 108), (720, 108)], (232, 236, 244), 16,
                       closed=False, seed=1095, wavelength=110.0)
        PA.hand_stroke(d, [(-30, 118), (W + 30, 100), (W + 30, 706), (-30, 716)],
                       INK, 30, closed=True, seed=1096, wavelength=220.0)
    els.append(SC.layer(clock, 38, h_finale, j=39, kind='subject', eid='h_finale'))
    els.append(cap(38, 640, 664, size=36, dark=True))
    # b38 IS captioned, and it is the last line of the chapter: the number and
    # the disclaimer are the content, and neither is drawn.

    return SC.finish(els, TITLE, clock, title_seed=47)


_pylon = CH._pylon
_painted_tree = CH._painted_tree
_vent_tower = CH._vent_tower
_norad_badge = CH._norad_badge
_sat = CH._sat
