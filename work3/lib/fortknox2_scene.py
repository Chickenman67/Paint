
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import engine3 as E3
import scene_common as SC
import v2paint as PA
import v2draw as D
import v2type as TY
import fortknox_scene as FK     # art primitives + palette, reused not copied

SEG = FK.SEG
TITLE = FK.TITLE
BEATS = FK.BEATS
TITLE_BACKDROP = FK.TITLE_BACKDROP

W, H = FK.W, FK.H

# palette, referenced from v1 rather than restated
INK = FK.INK
RED = FK.RED
GOLD = FK.GOLD
GOLD_HI = FK.GOLD_HI
GOLD_DK = FK.GOLD_DK
GRANITE = FK.GRANITE
BRICK = FK.BRICK
BRICK_DK = FK.BRICK_DK
ROOF = FK.ROOF
SKY = FK.SKY
STEEL = FK.STEEL
STEEL_DK = FK.STEEL_DK
PAPERW = FK.PAPERW
TITLE_COURSE = FK.TITLE_COURSE

# art primitives, referenced from v1 rather than restated
_hills = FK._hills
_dark = FK._dark
_pale = FK._pale
_facade = FK._facade
_vault_door = FK._vault_door
_hinge_column = FK._hinge_column
_inner_door = FK._inner_door
_bar_hall = FK._bar_hall
_bar_wall = FK._bar_wall
_gold_bar = FK._gold_bar
_flag = FK._flag
_flag_row = FK._flag_row
_floors_section = FK._floors_section
_arch_hall = FK._arch_hall
_pointed = FK._pointed
_wall_section = FK._wall_section
_bolts = FK._bolts
_castle = FK._castle
_kentucky = FK._kentucky
_person = FK._person
_car = FK._car
_bus = FK._bus
_page = FK._page
_stamp = FK._stamp
_shell = FK._shell
_scaffold = FK._scaffold
_crane = FK._crane
_truck = FK._truck
_counter = FK._counter
_corridor = FK._corridor
_deck_section = FK._deck_section

# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and it becomes the picture changing every sample,
# which is the defect this whole rebuild exists to remove.
ARRIVE = 0.5


def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def cap(i, cx, cy, **kw):
        """Phrase-timed caption. beats.json gives all 44 beats exactly one
        phrase, so `until` hands off to the next beat cleanly -- captions can
        never pile up (scene_common invariant 1)."""
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # ---- persistent page tooth under everything --------------------------- #
    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ===================================================================== #
    # STAGE A  b01-b07  "This is the most secure building on Earth. Every-   #
    #                 one in the country knows the name. Almost nobody has   #
    #                 ever been inside. It holds the gold of other nations.  #
    #                 Not only the gold of America. It sits in the hills of  #
    #                 Kentucky. A long low building made of brick."           #
    # ONE Kentucky hillside held across seven beats, and this stage is the   #
    # model the whole chapter follows: the hills are the backdrop, the       #
    # building accrues onto them, and then everything else ARRIVES -- the     #
    # presenter walks in and swaps expression at b04, the barred gate lifts in#
    # front, a lit arch opens in the wall, flags rise beside it, a locator   #
    # inset drops into the clear sky. Six arrivals, no full-frame repaint.   #
    # ===================================================================== #
    def a_hills(tile, fw, fh):
        _hills(tile, 1)
    els.append(SC.stage(clock, 1, a_hills, j=8))

    def a_building(tile, fw, fh):
        # The long low brick box, running off BOTH side edges. Painted once and
        # kept for the whole stage: every later beat in this stage happens TO
        # this building, so nothing may cover it but the gate.
        _facade(ImageDraw.Draw(tile), -70, 1350, 600, 290, 2)
    els.append(SC.accrue(clock, 1, 8, a_building, kind='shape'))

    def a_presenter_a(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 300, 770, 330, pose='pointing', expression='awed', seed=3)
    els.append(E3.E('a_presenter_a', 'character', a_presenter_a,
                    at=T(1), until=T(4),
                    motion=SC.enter(clock, 1, dx=-130, dy=0, dur=0.55)))

    def a_presenter_b(tile, fw, fh):
        # He changes expression at b04 on "It holds the gold of other nations":
        # awe at the building becomes a shrug at the contents. Two elements at
        # the same position, the first ending exactly where the second starts.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 300, 770, 330, pose='shrug', expression='skeptic', seed=3)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=T(4), until=T(8)))
    els.append(cap(1, 880, 200, size=34))

    # b03 "Almost nobody has ever been inside" -- a chained bar gate rises in
    # FRONT of the building, so the building is still there, just shut. The
    # bars top out at 110, clear of the title band; the gate runs off the right
    # edge. This is one of the few stage-A elements that must occlude rather
    # than accumulate, and it arrives with a short lift: the gate CLOSING is
    # the meaning, and 130px over 0.5s is the only place in this stage where a
    # movement says something.
    def a_gate(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(9):
            x = 700 + k * 96
            PA.hand_stroke(d, [(x, 110), (x, 700)], (74, 80, 88), 15,
                           closed=False, seed=11 + k, wavelength=150.0)
        for yy, sd in ((196, 30), (580, 31)):
            PA.hand_stroke(d, [(660, yy), (W + 40, yy)], (74, 80, 88), 17,
                           closed=False, seed=sd, wavelength=160.0)
        for k in range(8):
            t = k / 7.0
            lx = 700 + t * 300
            ly = 250 + t * 250
            PA.hand_stroke(d, PA.ellipse_pts(lx, ly, 27, 15, n=20),
                           (58, 62, 70), 7, closed=True, seed=40 + k,
                           wavelength=40.0)
    els.append(SC.accrue(clock, 3, 8, a_gate, kind='shape',
                         motion=SC.enter(clock, 3, dx=0, dy=130, dur=ARRIVE)))
    els.append(cap(3, 250, 170, size=32))

    # b04 "It holds the gold of other nations" -- an arched entrance OPENS in
    # the wall, lit gold from inside. The gold is the subject, so the glow is
    # the one saturated thing in a brick-and-grass frame.
    def a_arch(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        FK._archway(d, 880, 600, 190, 250, 63, lit=True, jamb=22)
    els.append(SC.accrue(clock, 4, 8, a_arch, kind='shape'))

    # b05 "Not only the gold of America" -- the flags. They go along the wall
    # either side of the lit arch, at the scale of the building rather than
    # floating over it. No caption: the lit arch plus a row of national flags
    # IS the sentence, and this beat would otherwise be the second piece of
    # text in the same region as the arch.
    def a_flags(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k, (fx, cols) in enumerate((
                (232, [(52, 74, 150), (250, 250, 248), (198, 40, 44)]),
                (392, [(198, 40, 44), (250, 250, 248)]),
                (528, [(198, 40, 44), (250, 250, 248), (52, 74, 150)]),
                (1092, [(250, 250, 248), (52, 74, 150), (198, 40, 44)]),
                (1252, [(198, 40, 44), (250, 250, 248)]))):
            _flag(d, fx, 486 - (k % 2) * 26, 66, 90 + k * 7, cols=cols)
    els.append(SC.accrue(clock, 5, 8, a_flags, kind='shape',
                         motion=SC.enter(clock, 5, dx=0, dy=-28, dur=ARRIVE)))
    els.append(cap(5, 640, 700, size=32))

    # b06 "It sits in the hills of Kentucky" -- a locator inset in the one part
    # of the frame nothing else occupies: the upper-left sky. It is a MAP, so
    # it REPLACES nothing (it is additive and in clear air) but it does carry
    # the drawn word KENTUCKY, which is why there is no caption here -- the
    # label is the text. NO caption at b07 either: "A long low building made of
    # brick" is a description of the facade that has been on screen since b01.
    def a_locator(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _kentucky(d, 214, 208, 300, 25)
        dx, dy = 214 + 0.16 * 300, 208 - 0.10 * 300
        d.ellipse([dx - 15, dy - 15, dx + 15, dy + 15], fill=RED)
        D.draw_label(tile, 'KENTUCKY', center=(250, 372), color=TY.LABEL_INK,
                     size=40)
    els.append(SC.accrue(clock, 6, 8, a_locator, kind='shape',
                         motion=SC.enter(clock, 6, dx=-96, dy=0, dur=ARRIVE)))

    # ===================================================================== #
    # STAGE B  b08-b10  "From the road it looks like a school. It is not a  #
    #                 school at all. This is Fort Knox, Kentucky."           #
    # The same _facade() routine as stage A, now with windows=8. Provably the #
    # same building the narrator has just called brick. b09 is the undercut  #
    # and it is the beat this stage exists to make work: v1 answered "it is   #
    # not a school" with a full-frame riveted steel plate over everything.   #
    # Here the LEFT third of the wall gets clad in steel with a small vault  #
    # door set in it, and the school tower on the right is struck out.       #
    # Measured 0.179 of the frame, against 0.600 before.                     #
    # ===================================================================== #
    def b_hills(tile, fw, fh):
        _hills(tile, 28)
        d = ImageDraw.Draw(tile)
        _facade(d, -70, 1350, 620, 350, 32, windows=8)
        tw = [(1040, 300), (1040, 150), (1110, 150), (1110, 300)]
        PA.fill_poly(tile, tw, BRICK_DK, seed=33, value=0.07)
        PA.hand_stroke(d, tw, INK, 6, closed=True, seed=34, wavelength=110.0)
        cone = [(1020, 150), (1075, 84), (1130, 150)]
        PA.fill_poly(tile, cone, ROOF, seed=35, value=0.07)
        PA.hand_stroke(d, cone, INK, 5, closed=True, seed=36, wavelength=90.0)
        SC.fullbody(d, 620, 660, 260, pose='standing', expression='neutral',
                    seed=37)
    els.append(SC.stage(clock, 8, b_hills, j=11))

    # b09 THE UNDERCUT. Replaces nothing -- it is drawn ON TOP of the school
    # facade, which stays visible across the right two thirds of the frame the
    # whole stage. What changes is the left third: steel cladding where the
    # school windows were, and a vault door in it. That is the argument in one
    # picture, and because it is an overlay it costs 0.179 of the frame rather
    # than replacing one.
    def b_notschool(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        panel = [(-70, 268), (470, 268), (470, 622), (-70, 622)]
        PA.fill_poly(tile, panel, STEEL, seed=42, value=0.08)
        PA.hand_stroke(d, panel, INK, 6, closed=True, seed=43, wavelength=140.0)
        for r in range(3):
            for c in range(3):
                bx, by = 40 + c * 150, 300 + r * 120
                PA.hand_stroke(d, PA.ellipse_pts(bx, by, 9, 9, n=12), INK, 3,
                               closed=True, seed=50 + r * 3 + c, wavelength=30.0)
        _vault_door(d, 200, 450, 165, 44, hinge=True, wheel=True, rings=2,
                    bolts=12)
        D.draw_red_x(tile, [990, 100, 1160, 320])
    els.append(SC.accrue(clock, 9, 11, b_notschool, kind='shape',
                         motion=SC.enter(clock, 9, dx=-140, dur=ARRIVE)))
    els.append(cap(8, 640, 700, size=32))

    # NO caption at b09. "It is not a school at all" is exactly what the steel
    # panel and the struck-out tower say, and the frame already carries it.
    # b10 is the name beat and the CAPTION is the reveal: a drawn "FORT KNOX"
    # would put the engine's own chapter title on screen a third time, which is
    # the stutter the v1 comment on this beat was written to avoid.
    els.append(cap(10, 640, 686, size=36))


    # ===================================================================== #
    # STAGE C  b11-b13  "Work began there in 1939. The building was finished #
    #                 in 1944. Five years of poured concrete and stone."     #
    # The same act of building, in three states, on one site. The scaffold,   #
    # the bare concrete frame and the crane are the backdrop and never        #
    # change; what arrives is the skin (b12) and the pour (b13).              #
    #                                                                       #
    # b12's cladding is the instructive one. Drawing a whole finished        #
    # _facade over the shell measured 0.333 -- just over the ceiling --       #
    # because a facade brings a new ROOF with it and the silhouette changes. #
    # Cladding INSIDE the shell's own outline, keeping the scaffold and the  #
    # crane up, measures 0.255 and is the more honest picture anyway:        #
    # "finished" means the skin is on, not that the site vanished.            #
    # ===================================================================== #
    def c_site(tile, fw, fh):
        _hills(tile, 53)
        d = ImageDraw.Draw(tile)
        _scaffold(d, -60, 620, 600, 300, 53, bays=5)
        _shell(d, 560, 1400, 600, 330, 54, floors=4, roofed=True)
        _crane(d, 300, 600, 330, 55, jib=760, hook_x=980)
    els.append(SC.stage(clock, 11, c_site, j=14))

    # b11 WORK BEGAN. The date arrives as its own element so it can DROP: 86px
    # of type falling 24px into the one clear patch of sky. Big drifting art is
    # what the motion rule forbids; a date stamping down is not that.
    def c_1939(tile, fw, fh):
        D.draw_label(tile, '1939', center=(210, 176), color=TY.LABEL_INK,
                     size=86)
    els.append(SC.accrue(clock, 11, 14, c_1939, kind='shape',
                         motion=SC.enter(clock, 11, dx=0, dy=-24, dur=0.45)))

    # b12 FINISHED 1944. The brick skin goes on INSIDE the shell's outline, so
    # the concrete frame, the scaffold and the crane are all still there -- the
    # building being finished, on the site it was built on. The date swaps to
    # 1944 in the same patch of sky the 1939 occupied, which is the only way
    # the two dates can be read as a span.
    def c_1944(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        skin = [(560, 270), (1340, 270), (1340, 600), (560, 600)]
        PA.fill_poly(tile, skin, BRICK, seed=57, value=0.07)
        PA.hand_stroke(d, skin, INK, 6, closed=True, seed=58, wavelength=150.0)
        for i in range(5):
            cx = 560 + 78 * (i + 0.5)
            for row, (wy, wh) in enumerate(((378, 90), (475, 78))):
                FK._archway(d, cx, wy, 70, wh, 200 + i * 7 + row,
                            lit=(row == 1), jamb=None)
        D.draw_label(tile, '1944', center=(210, 176), color=TY.LABEL_INK,
                     size=86)
    els.append(SC.accrue(clock, 12, 14, c_1944, kind='shape',
                         motion=SC.enter(clock, 12, dx=0, dy=-20, dur=0.45)))
    # NO caption at b12: the drawn 1944 stamp IS the sentence.

    # b13 FIVE YEARS OF POURED CONCRETE. Drawn explicitly rather than through
    # `_concrete_pour` for the reason v1 recorded: that primitive's internal
    # rebar grid plus a thin ribbon read as cross-hatched wires over pale haze
    # at this framing. Here the chute hangs in the clear sky, a fat solid
    # column falls from it and lands in a HEAP -- a heap rather than the
    # full-width crest the previous pass drew, because a full-width crest is a
    # new ground plane and that is a repaint. Measured with the man standing
    # on it: 0.139 of the frame.
    def c_pour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        ch = [(240, -20), (452, -20), (416, 96), (276, 96)]
        PA.fill_poly(tile, ch, STEEL_DK, seed=64, value=0.06)
        PA.hand_stroke(d, ch, INK, 8, closed=True, seed=65, wavelength=90.0)
        col = [(280, 96), (404, 96), (420, 250), (300, 250)]
        PA.fill_poly(tile, col, (150, 146, 142), seed=66, value=0.06)
        PA.hand_stroke(d, [(280, 96), (300, 250)], (26, 24, 26), 8,
                       closed=False, seed=67, wavelength=90.0)
        PA.hand_stroke(d, [(404, 96), (420, 250)], (26, 24, 26), 8,
                       closed=False, seed=68, wavelength=90.0)
        heap = [(110, 704), (300, 520), (520, 566), (700, 640), (870, 704)]
        PA.fill_poly(tile, heap, (112, 108, 106), seed=62, value=0.04)
        PA.hand_stroke(d, heap, (26, 24, 26), 9, closed=False, seed=63,
                       wavelength=170.0)
        for k in range(14):
            fx = 240 + (k * 61) % 380
            fy = 566 + (k * 97) % 128
            PA.fill_poly(tile, [(fx, fy), (fx + 13, fy + 4), (fx + 6, fy + 15)],
                         (86, 82, 80), seed=70 + k, value=0.0)
        SC.fullbody(d, 1010, 626, 360, pose='pointing', expression='deadpan',
                    seed=91)
    els.append(SC.accrue(clock, 13, 14, c_pour, kind='character'))
    # The caption sits HIGH and LEFT, in the pale sky the pour leaves clear --
    # v1 put it at y=664, which is on top of the dark pour mass, where an INK
    # fill measures about 1.3:1 and is effectively invisible.
    els.append(cap(13, 700, 232, size=34))

    # ===================================================================== #
    # STAGE D  b14-b16  "The roof was modelled on Gothic halls. Vaulted stone #
    #                 arches above the corridors. Europe, rebuilt in the      #
    #                 middle of Kentucky."                                    #
    # THREE beats, 7.7s, one hall. v1 treated these as three separate cards   #
    # precisely because they are three consecutive beats, and drew a hall,    #
    # then a side-on arcade, then a hall again with lancets lit -- three     #
    # images in seven seconds. Here the hall down its LENGTH is painted once #
    # and stays, and what arrives is what the words add: figures on the floor #
    # (so "vaulted" has something to be vaulted OVER), and the two nearest    #
    # arch heads brought forward into the foreground so the frame is inside   #
    # an arcade rather than beside a diagram of one.                          #
    # ===================================================================== #
    def d_hall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pale(tile, 71, FK.GRANITE_DK)
        _arch_hall(d, 71, bays=5, floor_y=700, lancets=0)
    els.append(SC.stage(clock, 14, d_hall, j=17))

    def d_figures(tile, fw, fh):
        # MOVING. Three figures CROSS the floor rather than standing on it:
        # "arches above the corridors" is a claim about circulation, and a
        # drift of 170px across one 2.5s beat is about 68px/s -- just over the
        # threshold motion_profile registers, on 190px-tall subjects.
        d = ImageDraw.Draw(tile)
        for i, fx in enumerate((300.0, 640.0, 980.0)):
            _person(d, fx, 672, 190, 170 + i, arms=True,
                    facing=1 if i % 2 else -1)
    els.append(SC.accrue(clock, 15, 17, d_figures, kind='shape',
                         motion=SC.drift(clock, 15, 16, dx=170, dy=0)))
    els.append(cap(15, 640, 122, size=34))

    def d_forearch(tile, fw, fh):
        # The nearest arch heads, brought forward and CROPPED by both side
        # edges. Not a second hall: two pointed heads on the near jambs, so the
        # viewer's eye is inside the arcade instead of looking at a picture of
        # one. v1 stamped "EUROPE, IN KENTUCKY" on this beat and captioned it
        # too, which put the same seven words on screen twice; here the caption
        # at b15 carries the arches and this beat carries only the architecture.
        d = ImageDraw.Draw(tile)
        for ax in (86.0, 1194.0):
            PA.fill_poly(tile, _pointed(ax, 700, 470), (176, 172, 162),
                         seed=124 + int(ax), value=0.07)
            PA.hand_stroke(d, _pointed(ax, 700, 470), INK, 7, closed=True,
                           seed=134 + int(ax), wavelength=170.0)
            PA.fill_poly(tile, _pointed(ax, 694, 330), (104, 100, 96),
                         seed=144 + int(ax), value=0.07)
            PA.hand_stroke(d, _pointed(ax, 694, 330), (58, 56, 54), 5,
                           closed=True, seed=154 + int(ax), wavelength=110.0)
    els.append(SC.accrue(clock, 16, 17, d_forearch, kind='shape'))


    # ===================================================================== #
    # STAGE E  b17-b21  "The doors mattered more than the roof. The main door #
    #                 weighs about 56 tons. It is reportedly the heaviest    #
    #                 vault door made. A round steel face, cropped by the     #
    #                 frame. It swings on a solid steel hinge."               #
    # The longest stage, 12.9s, and the one the persistent model was built    #
    # for. v1 spent NINE full frames here and four of them were the door at   #
    # four sizes; the previous stage build drew three stacked discs, each     #
    # wholly containing the last, which reads as a steel door inflating.     #
    #                                                                       #
    # IT IS ONE ELEMENT WITH A SCALE TRACK. `_vault_door(r=640)` is drawn     #
    # once, at full size, and engine3's motion track carries scale 0.30 ->    #
    # 1.00 across b17-b20. That is not a trick: it is a camera pushing in,   #
    # which is what the narration describes, and a door that grows toward     #
    # you is a thing the eye reads as depth rather than as a cut. Measured:   #
    # reframe fraction at onset 0.088, worst per-sample change in flight     #
    # 0.153 -- under the 0.30 cut threshold, so the whole push registers as    #
    # MOTION. Two full seconds of continuous movement, where v1 had two cuts. #
    #                                                                       #
    # The tile is scaled about its INK CENTROID, so the door is authored     #
    # centred in the frame it must fill at scale 1.0 and it grows toward the #
    # middle of the picture, not off a corner. r=640 at (640, 430) is past    #
    # both the top and bottom edges at full scale, which is the line: "a      #
    # round steel face, cropped by the frame".                               #
    # ===================================================================== #
    def e_ground(tile, fw, fh):
        _hills(tile, 101, grass=(120, 132, 108))
        # The roofline squeezed to a 78px band -- "the doors mattered more
        # than the roof" as one image, before the door has pushed in at all.
        _facade(ImageDraw.Draw(tile), -70, 1350, 690, 78, 102, roof_h=26,
                courses=False)
    els.append(SC.stage(clock, 17, e_ground, j=22))

    def e_door(tile, fw, fh):
        _vault_door(ImageDraw.Draw(tile), 640, 430, 640, 112, hinge=True,
                    wheel=True, rings=4, bolts=26)
    # The camera push. 0.30 -> 1.00 over b17-b20, eased by the engine, so the
    # growth is slowest at both ends and fastest through the middle. The door
    # is authored at r=640 which is already cropped top and bottom at full
    # scale; at 0.30 it is a 192px disc sitting in the middle of the frame,
    # small enough that its arrival is not a repaint.
    els.append(E3.E('e_door', 'shape', e_door, at=T(17), until=T(22),
                    motion=[(T(17), 0.0, 0.0, 0.30, 0.0),
                            (T(20), 0.0, 0.0, 1.00, 0.0)]))
    # NO caption at b17: a roofline crushed to a sliver under a great steel
    # disc IS "the doors mattered more than the roof". b18 keeps its caption
    # because 56 TONS is a NUMBER the drawing cannot make.
    els.append(cap(18, 300, 664, size=34))

    # b19 the scale for "the heaviest vault door made": a 210px car rolling in
    # at the door's foot. MOVING, small, 90px over 0.5s. The car is the only
    # small object on this stage, so it is the only thing allowed to move --
    # except the door, which moves because the camera does.
    def e_car(tile, fw, fh):
        _car(ImageDraw.Draw(tile), 300, 706, 210, 123)
    els.append(SC.accrue(clock, 19, 22, e_car, kind='shape',
                         motion=SC.enter(clock, 19, dx=-90, dur=0.5)))

    # b20 NO caption. The disc has just swollen past the top and bottom edges
    # with no outline visible, which is the literal content of "cropped by the
    # frame", and b21 immediately follows.
    #
    # b21 THE HINGE. Accrues ON TOP of the door rather than replacing it: the
    # hinge is a detail on the same door, and the previous pass replaced the
    # whole composition here, which measured 0.357 for a picture that is really
    # just a new object in front of an old one. The column is cropped hard by
    # the left edge with the door's shoulder still visible past it.
    def e_hinge(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hinge_column(d, 250, 380, 300, 142, blocks=3)
    els.append(SC.accrue(clock, 21, 22, e_hinge, kind='shape',
                         motion=SC.enter(clock, 21, dx=-120, dur=ARRIVE)))
    # MOVED from (900,690) to (940,120). At cy=690 the caption ran along the
    # bottom of a frame-filling vault door, where the pale interior and the dark
    # cast shadow alternate band by band; the left of the line was drawn in
    # near-black on near-black and disappeared. The gate measured it as a
    # straddle at 1.19:1 on the dark half. cy=120 puts it on the smooth upper
    # bowl of the door, which is one pale register across its whole width, and
    # x=940 keeps it clear of the centred title.
    els.append(cap(21, 940, 120, size=32))


    # ===================================================================== #
    # STAGE F  b22-b23  "Steel plate, then concrete, then more steel. The    #
    #                 concrete runs right through the walls."                 #
    # A DIAGRAM beat, so the diagram is the backdrop rather than a picture    #
    # that arrives. The previous pass drew the wall section as a layer at     #
    # b22, which measured 0.956 -- a whole new picture on the beat that says  #
    # "steel plate, then concrete". Painting it as the stage instead makes    #
    # that beat the cut it genuinely is.                                      #
    #                                                                       #
    # b23 then adds the ONE thing the three-band section cannot show: the     #
    # concrete is a single mass running through, with a wall of bars standing #
    # in the storey below it. Drawing the sealed version over the open one    #
    # measured 0.325 -- over the ceiling, because `_deck_section` repaints    #
    # its whole frame. Drawing only the bars into the lower storey measures   #
    # 0.204 and says the same thing.                                         #
    # ===================================================================== #
    def f_wall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (36, 34, 38), seed=151, value=0.05)
        SC.title_backdrop(tile, 1151, col=TITLE_COURSE)
        _wall_section(d, 640, 350, 1440, 470, 153,
                      layers=[(0.16, (96, 100, 110), 'STEEL'),
                              (0.52, (74, 71, 68), 'CONCRETE'),
                              (0.16, (72, 76, 86), 'STEEL')])
        _bolts(d, 40, 190, 1240, 520, 150, seed=154, r=16, col=(38, 40, 46))
        D.draw_label(tile, 'STEEL', center=(120, 626), color=PAPERW, size=44)
        D.draw_label(tile, 'CONCRETE', center=(660, 626), color=PAPERW,
                     size=44)
        D.draw_label(tile, 'STEEL', center=(1180, 626), color=PAPERW, size=44)
    els.append(SC.stage(clock, 22, f_wall, j=24))
    # NO caption at b22: the drawn STEEL / CONCRETE / STEEL legend under the
    # three bands IS the sentence, and a caption above them would be the same
    # six words twice inside one frame.

    # b23 THE CONCRETE RUNS THROUGH. The storey below the section fills with
    # aggregate-speckled concrete between two steel skins, laid OVER the stage
    # rather than replacing it, so the section above is still the same section.
    #
    # The two steel skins are NOT redrawn here: the section already carries
    # them, and repeating them changed 0.509 of the frame -- half the picture,
    # and half the picture changing is by definition a new picture wearing the
    # old stage's clothes. What arrives instead is the AGGREGATE, stippled into
    # the band the section already has, so the concrete stops being a labelled
    # swatch and becomes a material with a running-through middle.
    def f_throughwall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for k in range(96):
            x = -30 + (k * 197) % 1340
            y = 206 + (k * 113) % 212
            PA.fill_poly(tile, [(x, y), (x + 20, y + 7), (x + 8, y + 16)],
                         (168, 164, 156), seed=165 + k, value=0.0)
        for k in range(26):
            x = 40 + (k * 331) % 1200
            y = 214 + (k * 227) % 196
            PA.fill_poly(tile, PA.ellipse_pts(x, y, 17, 13, n=18),
                         (86, 84, 80), seed=200 + k, value=0.05)
        # The running-through is stated by ONE heavy seam at the top of the
        # band, carried off BOTH side edges, so the concrete has no visible
        # beginning or end: 9px of ink instead of a repainted 360px of wall,
        # which measured 0.509 of the whole frame.
        PA.hand_stroke(d, [(-40, 252), (W + 40, 252)], (58, 56, 54), 9,
                       closed=False, seed=221, wavelength=190.0)
    els.append(SC.accrue(clock, 23, 24, f_throughwall, kind='shape'))
    # NO caption at b23: a full-width concrete mass with steel skins top and
    # bottom, cropped at both edges, is the picture of "runs right through".

    # ===================================================================== #
    # STAGE G  b24-b25  "The walls are thicker than the doors. A castle built #
    #                 to outlast a siege."                                    #
    # The size comparison is the whole argument, so the comparison IS the     #
    # backdrop: a wall block cropped by the left and bottom edges beside a    #
    # visibly SMALLER door slab, with the presenter standing ON the slab.     #
    # Measured 0.669 as a layer -- a repaint -- and 0 as a stage.             #
    #                                                                       #
    # b25's toy castle was a full pale card in v1 (0.961). It is now a SMALL  #
    # cartoon castle standing on the wall block in the left third, cropped by #
    # the left edge, with the arrows coming in over it and the red X on the   #
    # comparison. Measured 0.123. The point of a cartoon castle is that it is #
    # a cartoon, so making it small and putting it inside the real picture is #
    # a better joke than giving it its own screen.                           #
    # ===================================================================== #
    def g_compare(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (34, 32, 36), seed=231, value=0.05)
        SC.title_backdrop(tile, 1231, col=TITLE_COURSE)
        wall = [(-40, 104), (700, 104), (700, 596), (-40, 700)]
        PA.fill_poly(tile, wall, (58, 56, 54), seed=233, value=0.05)
        PA.hand_stroke(d, [(-40, 104), (700, 104)], INK, 8, closed=False,
                       seed=234, wavelength=190.0)
        PA.hand_stroke(d, [(-40, 104), (-40, 700)], INK, 8, closed=False,
                       seed=234, wavelength=190.0)
        PA.hand_stroke(d, [(-40, 700), (700, 596), (700, 104)], INK, 9,
                       closed=False, seed=236, wavelength=170.0)
        for k in range(46):
            x = -20 + (k * 211) % 700
            y = 116 + (k * 137) % 528
            PA.hand_stroke(d, [(x, y), (x + 30, y + 10)], (128, 124, 118), 7,
                           closed=False, seed=235 + k, wavelength=50.0, vary=0.25)
        PA.fill_rect(tile, [-40, 596, 700, 660], STEEL, seed=260, value=0.08)
        slab = [(760, 170), (1200, 170), (1200, 560), (760, 560)]
        PA.fill_poly(tile, slab, STEEL_DK, seed=261, value=0.08)
        PA.hand_stroke(d, slab, INK, 8, closed=True, seed=262, wavelength=140.0)
        D.draw_label(tile, 'WALL', center=(300, 640), color=PAPERW, size=48)
        D.draw_label(tile, 'DOOR', center=(980, 640), color=PAPERW, size=48)
    els.append(SC.stage(clock, 24, g_compare, j=26))

    def g_man(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 980, 556, 260, pose='shrug',
                    expression='skeptic', seed=263)
    els.append(SC.accrue(clock, 24, 26, g_man, kind='character'))
    els.append(cap(24, 640, 150, size=32, fill=TY.LABEL_YELLOW))

    def g_castle(tile, fw, fh):
        # MOVING, small: the cartoon castle drops 40px onto the wall block.
        # siege_by_arrival is the arrival track; the arrows and the X are the
        # comparison, and both are drawn with it so the whole gag arrives as
        # one movement.
        d = ImageDraw.Draw(tile)
        _castle(d, 250, 660, 400, 200, 273)
        for x0, y0 in ((60, 150), (150, 120)):
            D.draw_arrow(tile, (x0, y0), (x0 + 150, y0 + 110), color=RED,
                         width=8, head=38)
        D.draw_red_x(tile, [640, 210, 700, 330])
    els.append(SC.accrue(clock, 25, 26, g_castle, kind='shape',
                         motion=SC.enter(clock, 25, dx=0, dy=40, dur=0.55)))
    # NO caption at b25: a cartoon castle under arrow fire with a red X through
    # it is the whole comparison.

    # ===================================================================== #
    # STAGE H  b26-b27  "The gold sits on nine floors. Rows of bars stacked   #
    #                 to the ceiling."                                        #
    # The building cut open on its flank: NINE storeys, each carrying gold,   #
    # the cut face and the storeys spanning -111..1292 so the section is      #
    # cropped by the left, right AND bottom edges and the building is bigger  #
    # than the picture. Measured 0.765 -- it is a backdrop, not a layer.      #
    #                                                                       #
    # b27 does NOT cut inside. The previous pass replaced the section with a  #
    # dark vault interior, which measured 0.625 and is a new picture on the   #
    # beat that says "rows of bars". Instead the storeys of the section that  #
    # the line is about fill with gold bars, over the section, in place:      #
    # measured 0.262. The viewer keeps the nine floors -- which is the b26    #
    # fact they have not finished looking at -- and watches the bars arrive   #
    # in them.                                                              #
    # ===================================================================== #
    def h_section(tile, fw, fh):
        _hills(tile, 281, sky=(198, 210, 222))
        _floors_section(ImageDraw.Draw(tile), 1726, 150, 780, 9, 282,
                        half_w=1670)
    els.append(SC.stage(clock, 26, h_section, j=28))
    # MOVED from cy=128 to cy=96. The nine-shelf rack's top edge sits at y~140 and
    # the caption's descenders reached y~144, so the right-hand words ran onto
    # that near-black shelf lip while the left words sat on pale sky -- the gate
    # measured a straddle at 1.34:1. cy=96 puts the whole line in the pale band
    # between the title (bottom ~60) and the shelf (top ~140).
    els.append(cap(26, 640, 96, size=34))
    # b27 "Rows of bars stacked to the ceiling" -- the middle storeys of the
    # SAME section fill with bars, cropped by both side edges, so they run
    # past the picture. Drawn over the section rather than replacing it.
    def h_bars(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_wall(d, 40, 520, 1240, 700, 291, bw=118, bh=40, gap=6,
                  stagger=True)
    els.append(SC.accrue(clock, 27, 28, h_bars, kind='shape'))
    # NO caption at b27: nine floors of section with the near storeys now
    # packed with bars says the line, and b26 already carried the reveal.
    # ===================================================================== #
    # STAGE I  b28-b29  "The reserve ran into the hundreds of billions. At    #
    #                 its peak it weighed 12,000 tonnes."                      #
    # This is the stage that TURNS FROM OUTSIDE TO INSIDE, and the turn is    #
    # the honest shape of the narration: the section is above, and from here  #
    # the viewer is IN the storey with the gold. So the dark interior ground #
    # is the backdrop and every later beat in this act is a different thing   #
    # standing in front of that same wall of gold -- first the ledger beside #
    # it, then the number band across it -- and the frame fills up in one     #
    # place instead of cutting.                                               #
    # ===================================================================== #
    def i_storey(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 291)
        SC.title_backdrop(tile, 1291, col=TITLE_COURSE)
        _bar_wall(d, -80, 104, W + 80, H + 60, 292, bw=150, bh=54, gap=6,
                  stagger=True)
    els.append(SC.stage(clock, 28, i_storey, j=30))
    # b28 A paper ledger column cropped by the top and right edges, standing in
    # FRONT of the bars on the right and leaving the left half of the gold
    # visible. This is a text-bearing element, so it REPLACES the wall's right
    # side for its own beat rather than accruing over the bars -- two figures
    # in one column is the pile-up rule 1 exists to prevent. Narrowed to
    # x930..1280 from x880: measured 0.255, from 0.311.
    def i_ledger(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [930, -40, W + 40, H + 40], (234, 228, 212),
                     seed=303, value=0.06)
        PA.hand_stroke(d, [(930, -40), (930, H + 40)], INK, 6, closed=False,
                       seed=304, wavelength=190.0)
        for k in range(6):
            y = 90 + k * 108
            PA.hand_stroke(d, [(956, y + 30), (1240, y + 24)], (176, 170, 152),
                           4, closed=False, seed=305 + k, wavelength=90.0)
            D.draw_number(tile, '%d B' % (32 * (k + 1)), center=(1098, y),
                          color=INK, size=54)
    # It ACCRUES to the end of the stage rather than replacing at b29. As a
    # one-beat layer the ledger vanished exactly when the tonnage band arrived,
    # so b29 repainted both halves of the frame at once -- measured 0.408.
    # Held live, the only new thing at b29 is the band and the truck.
    els.append(SC.accrue(clock, 28, 30, i_ledger, kind='shape'))
    # NO caption at b28: the ledger column PRINTS the billions, 32 B through
    # 192 B, in 54px numerals. v1 captioned this beat too, so the frame said
    # "hundreds of billions" twice at once.
    # b29 12,000 TONNES as the frame: a dark band across the LEFT of the bar
    # field with one truck at the bottom edge for the scale. The band is
    # x0..800 rather than the full width so the gold still shows on the right,
    # and so the arrival is 0.288 of the frame rather than 0.473 -- the
    # numeral is drawn at 178px, the largest type in the chapter, which is why
    # there is NO caption on this beat; the sentence and the numeral are the
    # same object.
    def i_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 214, 800, 372], (34, 30, 34), seed=313,
                     value=0.05)
        D.draw_number(tile, '12,000', center=(400, 293), color=GOLD_HI,
                      size=178)
        D.draw_label(tile, 'TONNES', center=(1010, 293), color=GOLD_HI,
                     size=64)
    # NO motion on this element even though it is the chapter's biggest reveal.
    # The band is wide, so a 150px arrival slides the WHOLE picture for half a
    # second -- exactly the churn the motion rule exists to prevent. It pops in;
    # the truck in front of it is the thing allowed to move.
    els.append(SC.layer(clock, 29, i_tonnes, j=30, kind='shape', eid='i_tonnes'))
    # MOVING, small: one loaded truck at the bottom edge, running in from the
    # right. 350px over 0.55s, and it is the scale that makes 12,000 tonnes
    # mean anything. Arriving WITH the band, so the union is what is budgeted.
    def i_truck(tile, fw, fh):
        _truck(ImageDraw.Draw(tile), 1010, 740, 350, 314)
    els.append(SC.accrue(clock, 29, 30, i_truck, kind='shape',
                         motion=SC.enter(clock, 29, dx=150, dur=0.55)))
    # ===================================================================== #
    # STAGE K  b30-b33  "The stacks filled whole wings of it. / Much of that #
    #                 gold belongs to other governments. Small national      #
    #                 flags above one vault door. The vault holds their gold #
    #                 as well."                                             #
    # STAGES J AND K ARE ONE STAGE. They were two, and the seam between them #
    # was the chapter's shortest cut: b30 was a single-beat stage holding    #
    # nothing but `_bar_hall`, and b31 opened a different vault wall in the  #
    # same building one beat later.                                          #
    # `_bar_hall` is not a different room from `_bar_wall` -- both are the   #
    # gold-storage floor, one seen down its length and one seen across it -- #
    # so the hall is planted once at b30 and held for four beats. The door   #
    # arrives at b31, the flags at b32 and the presenter at b33, so every   #
    # beat in the run still gets its own change.                             #
    # ===================================================================== #
    def k_hall(tile, fw, fh):
        _bar_hall(ImageDraw.Draw(tile), 321, fill_frac=1.0, floor_y=700,
                  back=4)
    els.append(SC.stage(clock, 30, k_hall, j=34))
    els.append(cap(30, 640, 690, size=32, fill=GOLD_HI))
    def k_door(tile, fw, fh):
        # The door pushed low and cropped by the bottom edge, so the flags
        # genuinely sit ABOVE it rather than beside it.
        _vault_door(ImageDraw.Draw(tile), 560, 560, 300, 342, hinge=True,
                    wheel=True, rings=3, bolts=18)
    els.append(SC.accrue(clock, 31, 34, k_door, kind='shape'))
    def k_flags(tile, fw, fh):
        # MOVING, small: a row of 54px flags rising 28px into the dark above
        # the door. Flags are the smallest repeated object in the chapter
        # (0.026 of the frame), so they are the right subject for the one
        # moving beat in this stage.
        _flag_row(ImageDraw.Draw(tile), 120, 1180, 200, 343, n=6, h=54)
    els.append(SC.accrue(clock, 32, 34, k_flags, kind='shape',
                         motion=SC.enter(clock, 32, dx=0, dy=-28, dur=ARRIVE)))
    # NO captions at b31, b32 or b33. "Much of that gold belongs to other
    # governments" is what a row of national flags standing on foreign gold
    # says; "small national flags above one vault door" describes the picture
    # exactly; and "the vault holds their gold as well" is carried by the door
    # standing IN the bars with the flags over it. v1 captioned all three.
    def k_in_gold(tile, fw, fh):
        # The presenter standing IN the gold at the right of the door, cropped
        # by the bottom, shrugging at the arrangement. He lives to b34 only,
        # because the b04 version of him stands in a different gap in a
        # different hall and two presenters in one frame is the pile-up rule.
        SC.fullbody(ImageDraw.Draw(tile), 980, 726, 400, pose='shrug',
                    expression='skeptic', seed=354)
    els.append(SC.accrue(clock, 33, 34, k_in_gold, kind='character'))
    # ===================================================================== #
    # STAGE L  b34-b36  "Only a small share stays on site. Only a few hundred #
    #                 tonnes remain. The rest was moved out years ago."       #
    # ONE hall across all three beats, emptied in place. v1 cut away three    #
    # times: a 0.52-fill hall, then a 0.40-fill hall, then a flat grey road   #
    # with trucks. Here the full hall from stage J stays, its RIGHT half is   #
    # cleared to bare floor at b34 (0.182), the small number is stamped on the#
    # empty floor at b35, and the loaded trucks drive out across the same     #
    # cleared floor at b36 with the arrow. Whole union measured 0.193.        #
    #                                                                       #
    # The trucks do NOT get their own road. "The rest was moved out" is a     #
    # statement about THIS vault, and putting the trucks on the vault floor   #
    # is both the smaller change and the truer one: the gold left this room.  #
    # ===================================================================== #
    # The full hall is repainted as this stage's OWN backdrop rather than left
    # over from stage J's one-beat backdrop. Measured: with the hall live under
    # it the emptied right half is 0.182; inheriting stage K's vault instead
    # measured 0.977, because a grey rectangle drawn over a wall of gold is not
    # an emptying, it is a repaint. This is the one place in the chapter where a
    # stage turn is both the honest move and the cheap one.
    def l_hall(tile, fw, fh):
        _bar_hall(ImageDraw.Draw(tile), 321, fill_frac=1.0, floor_y=700,
                  back=4)
    els.append(SC.stage(clock, 34, l_hall, j=37))
    def l_empty_right(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [560, 470, W + 40, 704], (150, 140, 128), seed=491,
                     value=0.06)
        PA.hand_stroke(d, [(560, 470), (W + 40, 470)], (40, 36, 34), 6,
                       closed=False, seed=492, wavelength=180.0)
    els.append(SC.accrue(clock, 34, 37, l_empty_right, kind='shape'))
    # MOVED from (990,140) to the bare floor at (940,590). At cy=140 the line
    # ran across the top of the gold wall, where the bright top-face band and
    # the shadowed front faces alternate -- the resolver dropped it to INK for
    # the bright half and the glyphs vanished on the shadowed bars (gate:
    # straddle 1.19:1). The bare floor this stage paints at x560+ y470-704 is
    # ONE flat mid-grey, so the whole line lands on a single register and reads.
    # It is also the semantically right surface: "only a small share stays on
    # site" is the part left ON the floor, so it sits over the floor.
    els.append(cap(34, 940, 590, size=32, fill=TY.LABEL_RED, max_w=560))
    # b35 "Only a few hundred tonnes remain" -- the small number stamped on
    # the bare floor where the gold is not, and the presenter standing in the
    # gap at 1010 looking at it.
    #
    # The legend and the presenter are SEPARATE elements because they do not
    # share a lifetime. When both lived to b37, the trucks that arrive at b36
    # painted over the legend and all but one glyph column of it survived --
    # a single orphaned letter floating in the gap between the two trucks,
    # which reads to a viewer as a rendering fault rather than as a word. The
    # legend now lives exactly the one beat it was written for and leaves when
    # the trucks arrive; the presenter stays, because he is the through-line.
    def l_few_hundred_label(tile, fw, fh):
        D.draw_label(tile, 'A FEW HUNDRED', center=(785, 560),
                     color=(250, 232, 168), size=42)
    els.append(SC.accrue(clock, 35, 36, l_few_hundred_label, kind='shape'))
    def l_few_hundred(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 1010, 690, 400, pose='shrug',
                    expression='skeptic', seed=362)
    # NO caption at b35: the drawn A FEW HUNDRED legend sits on the bare floor
    # and says the line. A caption under it printed the same four words twice.
    # b36 "The rest was moved out years ago" -- MOVING, and the only place a
    # fast arrival is right in this stage: the narrator says the gold was MOVED
    # OUT, and the loaded trucks running off to the left across the emptied
    # floor are the clearest read of that. 170px over 0.55s for the near one.
    def l_moving_out(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _truck(d, 850, 690, 300, 385, col=(150, 74, 60))
        _truck(d, 1150, 660, 190, 386, col=(140, 70, 58))
        D.draw_arrow(tile, (700, 300), (300, 300), color=RED, width=12,
                     head=54)
    els.append(SC.accrue(clock, 36, 37, l_moving_out, kind='shape'))
    # The presenter is appended AFTER the trucks so he draws IN FRONT of them.
    # Appended before, the loaded gold painted over his torso and legs and left
    # a black smear wedged in the gap between the two trucks -- a figure half
    # buried by the things moving past him. He is the narrator; the trucks move
    # past him, not over him. One ordering fact, one line of comment.
    els.append(SC.accrue(clock, 35, 37, l_few_hundred, kind='character'))
    els.append(cap(36, 640, 560, size=34, fill=TY.LABEL_RED))


    # ===================================================================== #
    # STAGE M  b37-b38  "A visitor counter, a ledger, a stamp. Thousands of   #
    #                 people tour it every year."                             #
    # The public side of the building, and the one beat where a PILE of people #
    # is the subject. b37 and b38 are the SAME room, so this is a real two-   #
    # beat stage: the counter with its ledger and stamp is built first, then  #
    # the queue arrives in front of it.                                        #
    #                                                                       #
    # The props stay live to the end of the stage and the crowd is drawn ON   #
    # TOP of them rather than replacing them, because the b37 sentence names  #
    # three objects and the frame should still hold all three while the crowd #
    # fills in. The counter runs off BOTH side edges, so the queue has        #
    # somewhere to come from and the room is bigger than the picture.         #
    # ===================================================================== #
    def m_wall(tile, fw, fh):
        _pale(tile, 391, (216, 212, 202))
    els.append(SC.stage(clock, 37, m_wall, j=39))

    def m_counter(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _counter(d, -60, 1340, 700, 240, 392)
        _page(d, 300, 432, 700, 596, 393, lines=5)
        _stamp(d, 880, 516, 64, 394)
    els.append(SC.accrue(clock, 37, 39, m_counter, kind='shape'))
    # NO caption at b37 and NO drawn "VISITORS" label: the counter, the ruled
    # ledger with its red margin rule, and the ink stamp ARE the three things
    # the sentence names, in that order, in one frame.

    def m_crowd(tile, fw, fh):
        # Thirteen figures in three ranks, positioned by explicit x lists
        # rather than even division. Even division was tried and rejected: it
        # either packs the band edge to edge (the over-populated frame this
        # project keeps losing blind comparisons on) or spaces them into a
        # picket fence. These lists let the front rank run the full width while
        # the ranks behind stagger into the gaps, so the eye reads depth.
        d = ImageDraw.Draw(tile)
        cols = ((70, 96, 168), (188, 96, 72), (96, 150, 116), (168, 152, 96))
        ranks = ((700, 232, (370, 600, 830, 1060, 1270)),
                 (656, 202, (478, 712, 946, 1180)),
                 (614, 174, (418, 655, 892, 1128)))
        for r, (y, h, xs) in enumerate(ranks):
            for i, x in enumerate(xs):
                _person(d, x, y, h, 410 + r * 20 + i, col=cols[(i + r) % 4])
    els.append(SC.accrue(clock, 38, 39, m_crowd, kind='character'))
    # The caption sits in the dark grille opening ABOVE the counter (y 160-434),
    # the one region of this frame with nothing in it. Laid over the front rank
    # it fought a dozen coloured torsos for legibility; at y=128 it fouled the
    # title band.
    els.append(cap(38, 640, 300, size=32))

    def m_man_a(tile, fw, fh):
        # He keeps the left third: his pointing arm ends near x=300, so the
        # queue starts at x=370 and the two never collide.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 132, 700, 440, pose='pointing', expression='neutral',
                    seed=396)
    els.append(E3.E('m_man_a', 'character', m_man_a, at=T(37), until=T(38),
                    motion=SC.enter(clock, 37, dx=-130, dur=0.55)))

    def m_man_b(tile, fw, fh):
        # He changes expression at b38 as the crowd arrives: pointing at the
        # ledger becomes open-handed surprise at the thousands of people. Two
        # elements at the same position, the first ending where the second
        # starts, because the expression is baked into the rasterised tile and
        # cannot be swapped on a single element.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 132, 700, 440, pose='wave', expression='awed',
                    seed=396)
    els.append(E3.E('m_man_b', 'character', m_man_b, at=T(38), until=T(39)))

    # STAGE N  b39  "School field trips arrive each spring."
    # Its own stage: the buses are OUTSIDE and the visitor hall they just left
    # is still on screen. v1 drew them as a layer over the pale wall, measured
    # 0.903 -- nearly the whole frame repainting on a beat whose only content is
    # "a bus arrived". A backdrop onset is skipped by the reframe gate by
    # design: a cut to a new place IS a cut to a new place. The near bus is
    # cropped by the LEFT edge so it reads as ARRIVING rather than parked.
    def n_road(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 421)
        _bus(d, 220, 694, 480, 422)
        _bus(d, 880, 706, 480, 423, col=(216, 170, 40))
        D.draw_label(tile, 'EVERY SPRING', center=(640, 176),
                     color=TY.LABEL_INK, size=48)
        SC.fullbody(d, 1140, 700, 340, pose='wave', expression='smirk',
                    seed=424)
    els.append(SC.stage(clock, 39, n_road, j=40))
    # NO caption at b39: the drawn EVERY SPRING legend says the line.

    # STAGE O  b40  "A line of children in a corridor."
    # Its own backdrop, and the reason is depth: the corridor converges on a
    # lit far end with the figures receding along it, which is the only depth
    # cue a flat frame has. v1 measured 0.933 for it as a layer over the road.
    # It needs no caption and no words.
    def o_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 640, 392, 431, floor_y=580, w0=1420)
        spots = ((170, 700, 340), (430, 664, 300), (660, 634, 262),
                 (856, 610, 226), (1010, 590, 194), (1136, 574, 168),
                 (1236, 562, 146))
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, (x, y, h) in enumerate(spots):
            _person(d, x, y, h, 440 + i, col=cols[i % 4])
    els.append(SC.stage(clock, 40, o_corridor, j=41))

    # STAGE P  b41-b42  "They walk above the stored gold. / They never walk
    # below the gold."
    # THE SECTION THE CHAPTER HAS BEEN WALKING TOWARD, and the one beat pair
    # that must read as the SAME picture twice: the public corridor deck on a
    # slab directly over the gold storey, visitors on top, bars visible in the
    # storey below their feet. b42 is the SAME _deck_section with sealed=True,
    # so the only difference between the two beats is whether the lower storey
    # is lit and open or barred -- and that the two beats are visibly the same
    # diagram is the entire argument of the pair.
    def p_deck(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (222, 218, 208), seed=451, value=0.05)
        PA.paper_overlay(tile, seed=452)
        _deck_section(d, 453, deck_y=470, sealed=False)
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, x in enumerate((40, 190, 340, 490, 790, 940, 1240)):
            _person(d, x, 452, 210, 460 + i, col=cols[i % 4])
        # The presenter takes the 640 slot the crowd would otherwise fill, so he
        # is one of the people walking over the gold rather than a portrait
        # pasted beside the diagram.
        SC.fullbody(d, 640, 452, 300, pose='pointing', expression='awed',
                    seed=466)
    els.append(SC.stage(clock, 41, p_deck, j=44))
    # MOVED from (640,686) to (640,190). At cy=686 the line sat deep in the
    # storey of gold below the deck, crossing bright bar tops and dark
    # inter-bar gaps; RED reads on the bright bars and vanishes on the gaps
    # (gate: straddle 1.14:1). cy=190 lifts it onto the pale vault wall between
    # the title strip (bottom ~145) and the tops of the visitors' heads
    # (~235) -- one flat light register across the full width, so the resolver
    # keeps a single legible fill for the whole line. It also sits above the
    # walkers rather than buried among the bars, which is what the line says.
    els.append(cap(41, 980, 185, size=32, max_w=520))

    def p_sealed(tile, fw, fh):
        # b42: the SAME section with the lower storey barred, and one more
        # figure on the deck -- the rank grows by exactly one, so the change
        # between the two beats is a bar dropping and a person joining, not a
        # new picture. Drawn over the open section rather than replacing it, so
        # the pair reads as one diagram seen twice.
        d = ImageDraw.Draw(tile)
        _deck_section(d, 453, deck_y=470, sealed=True)
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, x in enumerate((40, 190, 340, 490, 790, 940, 1240)):
            _person(d, x, 452, 210, 460 + i, col=cols[i % 4])
        SC.fullbody(d, 640, 452, 300, pose='pointing', expression='awed',
                    seed=466)
        D.draw_label(tile, 'NEVER BELOW IT', center=(640, 146),
                     color=TY.LABEL_INK, size=40)
    els.append(SC.layer(clock, 42, p_sealed, j=44, kind='shape', eid='p_sealed'))
    # NO caption at b42: the drawn NEVER BELOW IT legend is the line, and v1
    # printed it a second time underneath as a caption.
    # ===================================================================== #
    # STAGE Q  b43-b44  "The inner doors stay bolted shut. / Almost nobody  #
    #                 alive has seen inside."                                #
    # THE LAST STAGE, and the two beats are ONE ROOM. They were two: b43   #
    # sat in a dark stone vault and b44 cut to an empty corridor, which was #
    # the chapter's shortest cut and, worse, said the viewer had left the   #
    # vault to look at a different corridor. But the line is about a door  #
    # that stays shut, so the door belongs at the END of the corridor the  #
    # viewer is looking down.                                              #
    #                                                                       #
    # b43 plants the corridor and the bolted door in it. b44 does not cut:  #
    # the same corridor, the same shut door, and the presenter cropped into #
    # it. The bubble is HIS, not the narrator's -- "nobody alive" is what   #
    # he is thinking and the caption underneath is what the narrator says, #
    # so the two texts are 470px apart and never collide.                   #
    # ===================================================================== #
    def q_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (48, 48, 56), seed=501, value=0.10)
        PA.paper_overlay(tile, seed=502)
        SC.title_backdrop(tile, 1501, col=TITLE_COURSE)
        xa = -(W / 2.0 + 60)
        xb = W / 2.0 + 60
        wa = [(xa + (900.0 - xa) * (144.0 / 340.0), 104), (900, 300),
              (900, 470), (xa, H + 40)]
        wb = [(xb + (900.0 - xb) * (144.0 / 340.0), 104), (900, 300),
              (900, 470), (xb, H + 40)]
        PA.fill_poly(tile, wa, (66, 66, 74), seed=503, value=0.07)
        PA.hand_stroke(d, wa, INK, 7, closed=False, seed=505,
                       wavelength=180.0)
        PA.fill_poly(tile, wb, (66, 66, 74), seed=504, value=0.07)
        PA.hand_stroke(d, wb, INK, 7, closed=False, seed=506,
                       wavelength=180.0)
        PA.fill_poly(tile, [(-60, H + 40), (900, 470), (900, 470),
                            (W + 60, H + 40)], (58, 58, 66), seed=507,
                     value=0.07)
    els.append(SC.stage(clock, 43, q_corridor, j=45))

    def q_bolted(tile, fw, fh):
        # A steel slab in a thick frame, barred by heavy horizontal bolts, set
        # at the LIT END of the corridor so it is what the corridor leads to.
        # No mechanism on purpose: the main door's wheel is what says this can
        # be opened, and one here would argue against the line.
        d = ImageDraw.Draw(tile)
        _inner_door(d, 900, 372, 300, 214, 492, bolt=4)
    els.append(SC.accrue(clock, 43, 45, q_bolted, kind='shape'))
    # NO caption at b43: the bolt bars ARE the line, and this is the last beat
    # before the finale, which wants the frame to itself.

    def q_closeup(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        SC.closeup(d, 330, 400, 235, 'worried', 508)
        D.draw_bubble(tile, 'nobody alive', xy=(880, 190), tail_to=(640, 300),
                      font_size=38, max_w=420)
    els.append(SC.accrue(clock, 44, 45, q_closeup, kind='character'))
    els.append(cap(44, 950, 656, size=34, fill=TY.LABEL_YELLOW, max_w=520))

    return SC.finish(els, TITLE, clock, title_seed=7)



if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
