"""fortknox2_scene -- the PERSISTENT-STAGE rebuild of chapter 2 (Fort Knox).

WHY THIS FILE EXISTS. fortknox_scene.py (v1) was built on "one card per beat,
each card paints its own whole frame". Forty-four short sentences (see
_plan_fortknox.py), beats.json giving each an exact [start, end], and therefore
forty-four complete repaints of a 1280x720 frame in 108 seconds. Nothing
survived between beats: every cut was a brand-new image, which is the exact
complaint the whole rebuild exists to fix ("every sentence has a cut with a
completely new image... there are no animations or changes to the visual").

THE MODEL HERE. EIGHT PERSISTENT STAGES instead of forty-four cards, grouped on
the narration's own acts (boundaries fixed in plans/STAGE_PLANS.md, not
re-invented here):

    A  b01-b07  (15.9s)  the Kentucky hills; a low brick building on them
    B  b08-b13  (14.1s)  it looks like a school; it is not; 1939-1944
    C  b14-b16  ( 7.6s)  the gothic hall -- the roof, and Europe in Kentucky
    D  b17-b25  (23.3s)  the door; 56 tons; steel/concrete/steel; walls > doors
    E  b26-b30  (13.3s)  gold on nine floors; 12,000 tonnes; whole wings
    F  b31-b36  (14.7s)  other nations' gold; only a few hundred tonnes left
    G  b37-b41  (12.2s)  the visitor counter; the school trips; above the gold
    H  b42-b44  ( 6.6s)  never below; bolted; nobody alive has seen inside

The frame repaints eight times in 108s instead of forty-four (longest gap
23.3s), and inside a stage the art ACCUMULATES: a layer that arrives stays
until the stage turns over (SC.accrue). The viewer's eye gets one recognisable
place to look while the next thing is added to it.

The clearest single demonstration is STAGE D. v1 drew the vault door four
times, at four sizes, on four full frames (b17 r=290, b18 r=470, b19 r=450,
b20 r=760) -- four repaints to say one thing. Here the door is drawn ONCE at
r=290 on b17 and then simply covered by the SAME routine at r=470 on b18 and
r=760 on b20, each disc wholly containing the last. The door appears to swell
into the frame over three beats without a single cut, which is both truer to
the narration ("the doors mattered more than the roof" -> "56 tons" -> "a round
steel face, cropped by the frame") and the reason a viewer will believe the
mass.

TWO RULES THAT TOOK TWO ROUNDS TO LEARN in the pinegap pilot, both kept:

1. ACCRUE THE WORLD, REPLACE THE LABELS. Accruing everything is also wrong --
   you get text pile-ups and objects stacked on objects. fortknox is the worst
   case in the chapter set: national flags above a vault door, a visitor
   ledger, a stamp, a ledger column of billions, two stone WALL/DOOR labels and
   a speech bubble, all text-bearing. Everything carrying text here REPLACES
   (SC.layer) or arrives as the last thing in its region, and anything sharing
   a region with something already down REPLACES. Only scenery accrues.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces motion at a rate the
   reference does not have and every moving frame trips the picture-change
   counter. The reference is 83% still. So eleven arrivals move, briefly
   (0.45-0.6s), on small subjects: the presenter walking in, a row of flags, a
   map inset, the round door, a date stamp, three figures crossing a hall, a
   car, a truck, a ledger page. Nothing big drifts.

CAPTIONS. Seventeen of forty-four beats (39%), never two in a row. v1 captioned
all 44 (100%), which is why its frames read as a wall of words. The test applied
to every beat: DOES THE DRAWN ART ALREADY SAY IT? Kept when the words carry
something the art cannot -- the hook, the misdirection that the red X then
strikes out, the name, five years of concrete, arches over corridors, the door,
the hinge, walls thicker than doors, nine floors, whole wings, the few hundred
tonnes that remain, the trucks going out, the visitors, the deck, the last line.
Dropped when the art already prints the words -- the "1939"/"1944" stamps, the
STEEL/CONCRETE/STEEL legend, the "A FEW HUNDRED" legend, the ledger column of
billions, "EUROPE, IN KENTUCKY", "NEVER BELOW IT" -- or when the picture is
simply self-explanatory. Every drop carries a one-line comment saying which.

THE ART IS v1's, REUSED NOT COPIED. Every primitive (_hills, _facade,
_vault_door, _bar_hall, _bar_wall, _floors_section, _arch_hall, _pointed,
_wall_section, _hinge_column, _inner_door, _counter, _page, _stamp,
_corridor, _deck_section, _castle, _kentucky, _car, _bus, _person, _truck,
_flag, _flag_row, _shell, _scaffold, _crane, ...) and every palette value is
referenced through `FK.` rather than restated, so a fix to the v1 routine
propagates here. The comments explaining WHY those primitives are shaped the
way they are stay in v1 and are not duplicated.

Run:  python lib/fortknox2_scene.py --preview
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
    # ONE Kentucky hillside held across seven beats. v1 gave this run seven  #
    # full frames -- a facade, then a close-up, then a gate, then a gold hall,#
    # then a map, then the facade again -- six different pictures for one     #
    # location. Here the hills and the building are painted once and the rest #
    # ARRIVES on top of them: the gate goes up in front, a lit arch opens in  #
    # the wall, flags rise beside it, a locator inset drops into the sky.     #
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
    # STAGE B  b08-b13  "From the road it looks like a school. It is not a  #
    #                 school at all. This is Fort Knox, Kentucky. Work began #
    #                 there in 1939. The building was finished in 1944. Five #
    #                 years of poured concrete and stone."                    #
    # The argument of this stage is that ONE building changes its mind twice: #
    # school (b08), not a school (b09), and then a building on site from 1939 #
    # (b11). So the stage keeps one hillside and swaps the WALL in place of it #
    # rather than cutting to a new location: the brick box goes up at b08, a  #
    # steel plate is laid over the same footprint at b09 and a red X is struck #
    # through the school reading, and the construction shell replaces it again #
    # at b11 with the 1939 stamp landing on the same patch of sky.            #
    # ===================================================================== #
    def b_hills(tile, fw, fh):
        _hills(tile, 28)
    els.append(SC.stage(clock, 8, b_hills, j=14))

    def b_school(tile, fw, fh):
        # THE SAME _facade() WITH windows=8 -- provably the same building the
        # narrator has just called brick. It lives only b08-b10: it has to be
        # GONE by b11, because b12 re-draws a facade in the same footprint and
        # two brick boxes in one frame is the pile-up rule 1 exists to stop.
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
    els.append(SC.accrue(clock, 8, 11, b_school, kind='character'))

    # b09 THE UNDERCUT. REPLACES the brick, because it is the same walls
    # described rather than a second building beside the first: a riveted steel
    # plate over the same footprint, with the school tower's ghost still
    # implied by the plate's height. The red X is drawn LAST so it lies over
    # both the plate and the round door.
    def b_notschool(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        body = [(-60, 640), (-60, 320), (1340, 320), (1340, 640)]
        PA.fill_poly(tile, body, (122, 128, 136), seed=39, value=0.08)
        PA.hand_stroke(d, body, INK, 6, closed=True, seed=40, wavelength=160.0)
        for k in range(9):
            y = 344 + k * 32
            PA.hand_stroke(d, [(-40, y), (1320, y)], (100, 106, 114), 3,
                           closed=False, seed=41 + k, wavelength=150.0)
        plate = [(400, 168), (1200, 168), (1200, 640), (400, 640)]
        PA.fill_poly(tile, plate, STEEL, seed=42, value=0.08)
        PA.hand_stroke(d, plate, INK, 6, closed=True, seed=43, wavelength=140.0)
        for r in range(4):
            for c in range(9):
                bx, by = 438 + c * 90, 202 + r * 108
                if bx > 1160:
                    continue
                PA.hand_stroke(d, PA.ellipse_pts(bx, by, 9, 9, n=12), INK, 3,
                               closed=True, seed=50 + r * 9 + c, wavelength=30.0)
    els.append(SC.layer(clock, 9, b_notschool, j=11, kind='shape',
                        eid='b_notschool'))

    def b_rounddoor(tile, fw, fh):
        # MOVING, and small: a 400px door arriving 140px from the left edge in
        # half a second. It is the thing the red X is aimed at, so it gets the
        # arrival rather than the plate behind it.
        d = ImageDraw.Draw(tile)
        _vault_door(d, 110, 470, 200, 44, hinge=True, wheel=True, rings=2,
                    bolts=12)
        D.draw_red_x(tile, [660, 300, 1060, 560])
    els.append(SC.accrue(clock, 9, 11, b_rounddoor, kind='shape',
                         motion=SC.enter(clock, 9, dx=-140, dur=ARRIVE)))
    els.append(cap(8, 640, 700, size=32))

    # NO caption at b09. "It is not a school at all" is exactly what the red X
    # over the school facade says, and the frame already carries the words.
    # b10 is the name beat and the CAPTION is the reveal: a drawn "FORT KNOX"
    # would put the engine's own chapter title on screen a third time, which is
    # the stutter the v1 comment on this beat was written to avoid. So nothing
    # is drawn at b10 and the narrator's line is the only text.

    els.append(cap(10, 640, 686, size=36))

    # b11 WORK BEGAN. The bare concrete frame with the crane's jib running OFF
    # the right edge, so the site is bigger than the picture.
    def b_1939_site(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _scaffold(d, -60, 620, 600, 300, 53, bays=5)
        _shell(d, 560, 1400, 600, 330, 54, floors=4, roofed=True)
        _crane(d, 300, 600, 330, 55, jib=760, hook_x=980)
    els.append(SC.accrue(clock, 11, 12, b_1939_site, kind='shape'))

    def b_1939_stamp(tile, fw, fh):
        # The date as its own element so it can ARRIVE: 86px of type dropping
        # 24px into the one clear patch of sky. Big drifting art is what the
        # motion rule forbids; a date stamping down is not that.
        D.draw_label(tile, '1939', center=(210, 176), color=TY.LABEL_INK,
                     size=86)
    els.append(SC.accrue(clock, 11, 12, b_1939_stamp, kind='shape',
                         motion=SC.enter(clock, 11, dx=0, dy=-24, dur=0.45)))

    # b12 FINISHED 1944. REPLACES the shell rather than cladding it: the new
    # facade covers the same footprint, so leaving the concrete frame accruing
    # underneath would put a brick box inside a brick box.
    def b_1944(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _facade(d, 520, 1420, 610, 350, 57, windows=7)
        _scaffold(d, -60, 430, 610, 330, 58, bays=3)
        D.draw_label(tile, '1944', center=(200, 176), color=TY.LABEL_INK,
                     size=86)
    els.append(SC.layer(clock, 12, b_1944, j=13, kind='shape', eid='b_1944'))
    # NO caption at b12: the drawn 1944 stamp IS the sentence.

    # b13 FIVE YEARS OF POURED CONCRETE. Drawn explicitly rather than through
    # `_concrete_pour` for the reason v1 recorded: that primitive's internal
    # rebar grid plus a thin ribbon read as cross-hatched wires over pale haze
    # at this framing. Here the chute hangs in the clear sky, a fat solid
    # column falls from it and lands in a DARK pour mass that fills the bottom
    # band and runs off three edges. The mass is the subject -- five years of
    # it -- so it is the darkest thing in frame. The presenter stands ON the
    # crest, watching it.
    def b_pour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        crest = [(-40, 430), (240, 402), (620, 424), (940, 452), (W + 40, 436),
                 (W + 40, H + 40), (-40, H + 40)]
        PA.fill_poly(tile, crest, (112, 108, 106), seed=62, value=0.04)
        PA.hand_stroke(d, [(-40, 430), (240, 402), (620, 424), (940, 452),
                           (W + 40, 436)], (26, 24, 26), 9, closed=False,
                       seed=63, wavelength=170.0)
        # the chute, cropped by the TOP edge exactly as v1 had it
        ch = [(200, -20), (452, -20), (416, 96), (236, 96)]
        PA.fill_poly(tile, ch, STEEL_DK, seed=64, value=0.06)
        PA.hand_stroke(d, ch, INK, 8, closed=True, seed=65, wavelength=90.0)
        col = [(250, 96), (404, 96), (430, 260), (452, 430), (196, 430),
               (216, 260)]
        PA.fill_poly(tile, col, (150, 146, 142), seed=66, value=0.06)
        PA.hand_stroke(d, [(250, 96), (216, 260), (196, 430)], (26, 24, 26), 8,
                       closed=False, seed=67, wavelength=90.0)
        PA.hand_stroke(d, [(404, 96), (430, 260), (452, 430)], (26, 24, 26), 8,
                       closed=False, seed=68, wavelength=90.0)
        for k in range(14):
            fx = 240 + (k * 61) % 170
            fy = 130 + (k * 97) % 280
            PA.fill_poly(tile, [(fx, fy), (fx + 13, fy + 4), (fx + 6, fy + 15)],
                         (86, 82, 80), seed=70 + k, value=0.0)
        SC.fullbody(d, 1000, 448, 400, pose='pointing', expression='deadpan',
                    seed=91)
    els.append(SC.layer(clock, 13, b_pour, j=14, kind='character', eid='b_pour'))
    # The caption sits HIGH and LEFT, in the pale sky the pour leaves clear --
    # v1 put it at y=664, which is on top of the dark pour mass, where an INK
    # fill measures about 1.3:1 and is effectively invisible.
    els.append(cap(13, 700, 232, size=34))

    # ===================================================================== #
    # STAGE C  b14-b16  "The roof was modelled on Gothic halls. Vaulted stone #
    #                 arches above the corridors. Europe, rebuilt in the      #
    #                 middle of Kentucky."                                    #
    # THREE beats, 7.6s, one hall. v1 treated these as three separate cards   #
    # precisely because they are three consecutive beats, and drew a hall,    #
    # then a side-on arcade, then a hall again with lancets lit -- three     #
    # images in seven seconds. Here the hall down its LENGTH is painted once #
    # and stays, and what arrives is what the words add: figures on the floor #
    # (so "vaulted" has something to be vaulted OVER), and the two nearest    #
    # arch heads brought forward into the foreground so the frame is inside   #
    # an arcade rather than beside a diagram of one.                          #
    # ===================================================================== #
    def c_hall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pale(tile, 71, FK.GRANITE_DK)
        _arch_hall(d, 71, bays=5, floor_y=700, lancets=0)
    els.append(SC.stage(clock, 14, c_hall, j=17))

    def c_figures(tile, fw, fh):
        # MOVING. Three figures CROSS the floor rather than standing on it:
        # "arches above the corridors" is a claim about circulation, and a
        # drift of 170px across one 2.5s beat is about 68px/s -- just over the
        # threshold motion_profile registers, on 190px-tall subjects.
        d = ImageDraw.Draw(tile)
        for i, fx in enumerate((300.0, 640.0, 980.0)):
            _person(d, fx, 672, 190, 170 + i, arms=True,
                    facing=1 if i % 2 else -1)
    els.append(SC.accrue(clock, 15, 17, c_figures, kind='shape',
                         motion=SC.drift(clock, 15, 16, dx=170, dy=0)))
    els.append(cap(15, 640, 122, size=34))

    def c_forearch(tile, fw, fh):
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
    els.append(SC.accrue(clock, 16, 17, c_forearch, kind='shape'))

    # ===================================================================== #
    # STAGE D  b17-b25  "The doors mattered more than the roof. The main door #
    #                 weighs about 56 tons. It is reportedly the heaviest    #
    #                 vault door made. A round steel face, cropped by the     #
    #                 frame. It swings on a solid steel hinge. Steel plate,   #
    #                 then concrete, then more steel. The concrete runs right #
    #                 through the walls. The walls are thicker than the doors.#
    #                 A castle built to outlast a siege."                     #
    # The longest stage, 23.3s, and the one the persistent model was built    #
    # for. v1 spent NINE full frames here. The door alone took four of them  #
    # at four sizes; here it is drawn ONCE and simply covered twice by the    #
    # SAME routine at a larger radius, each disc wholly containing the last,   #
    # so the door SWELLS into the frame across b17/b18/b20 with no cut at all.#
    # That is the chapter's argument (mass) rendered as accumulation instead  #
    # of replacement. The wall section at b22-b24 then accrues the same way:   #
    # three layers, then the concrete revealed as continuous through them.    #
    # ===================================================================== #
    def d_hills(tile, fw, fh):
        _hills(tile, 101, grass=(120, 132, 108))
    els.append(SC.stage(clock, 17, d_hills, j=26))

    def d_firstdoor(tile, fw, fh):
        # The roofline squeezed to a 78px band and the door taking everything
        # under it -- "the doors mattered more than the roof" as one image. The
        # door is small here and stays on the stage; b18 and b20 grow it.
        d = ImageDraw.Draw(tile)
        _facade(d, -70, 1350, 690, 78, 102, roof_h=26, courses=False)
        _vault_door(d, 640, 470, 290, 103, hinge=True, wheel=True, rings=3,
                    bolts=16)
    els.append(SC.accrue(clock, 17, 22, d_firstdoor, kind='shape'))
    # NO caption at b17: a roofline crushed to a sliver under a great steel
    # disc IS "the doors mattered more than the roof", and the frame says it
    # without a line of type. b18 keeps its caption because 56 TONS is a
    # NUMBER the drawing cannot make -- v1 stamped it as a drawn label there
    # AND captioned it, which is why both had to go.

    def b_huge_door(tile, fw, fh):
        # MOVING is deliberately NOT applied here despite this being the
        # chapter's biggest reveal. A 940px disc sliding even 40px reads as
        # the whole picture shifting; the growth is carried by the cut from
        # r=290 to r=470 instead, which is instantaneous and honest.
        d = ImageDraw.Draw(tile)
        _vault_door(d, 620, 580, 470, 112, hinge=True, wheel=True, rings=3,
                    bolts=22)
    els.append(SC.accrue(clock, 18, 22, b_huge_door, kind='shape'))
    els.append(cap(18, 300, 664, size=34))

    def b_car(tile, fw, fh):
        # MOVING, small: a 210px car rolling 90px in from the left at the door's
        # foot, for the scale "the heaviest vault door made" is claiming. The
        # car is the only small object on this stage, so it is the only thing
        # here allowed to move.
        _car(ImageDraw.Draw(tile), 290, 706, 210, 123)
    els.append(SC.accrue(clock, 19, 22, b_car, kind='shape',
                         motion=SC.enter(clock, 19, dx=-90, dur=0.5)))

    def b_roundface(tile, fw, fh):
        # r=760: the circle is past all four edges, so no part of its outline is
        # visible -- which is exactly what the line says. It wholly contains the
        # r=470 disc, so the frame reads as the SAME door, closer.
        _vault_door(ImageDraw.Draw(tile), 640, 870, 760, 132, hinge=True,
                    wheel=True, rings=4, bolts=30)
    els.append(SC.accrue(clock, 20, 22, b_roundface, kind='shape'))
    # NO caption at b20. The disc has just swollen past all four edges with no
    # outline visible, which is the literal content of "cropped by the frame",
    # and b21 immediately follows, so a caption here would also put two
    # captioned beats back to back.

    def b_hinge(tile, fw, fh):
        # REPLACES the door. The hinge column is a DIFFERENT subject filling a
        # different part of the frame; left accruing it would sit on top of the
        # r=760 disc and neither would read. The hinge is cropped hard by the
        # left edge, with only the door's shoulder visible past it.
        d = ImageDraw.Draw(tile)
        _hinge_column(d, 250, 380, 300, 142, blocks=3)
        ring = PA.ellipse_pts(560, 380, 470, 470, n=72)
        PA.fill_poly(tile, ring, STEEL, seed=143, value=0.08)
        PA.hand_stroke(d, ring, INK, 10, closed=True, seed=144, wavelength=190.0)
    els.append(SC.layer(clock, 21, b_hinge, j=22, kind='shape', eid='b_hinge'))
    els.append(cap(21, 900, 690, size=32))

    def b_wallsection(tile, fw, fh):
        # The wall as a CUT: steel / concrete / steel edge to edge across the
        # whole frame, cropped left and right so the wall runs past the picture.
        # DARK on purpose -- the pale version read as three bright panels in a
        # white field. DARK layers passed explicitly for the reason v1 recorded.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (36, 34, 38), seed=151, value=0.05)
        SC.title_backdrop(tile, 1151, col=TITLE_COURSE)
        _wall_section(d, 640, 350, 1440, 470, 153,
                      layers=[(0.16, (96, 100, 110), 'STEEL'),
                              (0.52, (74, 71, 68), 'CONCRETE'),
                              (0.16, (72, 76, 86), 'STEEL')])
        _bolts(d, 40, 190, 1240, 520, 150, seed=154, r=16, col=(38, 40, 46))
        D.draw_label(tile, 'STEEL', center=(120, 626), color=PAPERW, size=44)
        D.draw_label(tile, 'CONCRETE', center=(660, 626), color=PAPERW, size=44)
        D.draw_label(tile, 'STEEL', center=(1180, 626), color=PAPERW, size=44)
    els.append(SC.layer(clock, 22, b_wallsection, j=24, kind='shape',
                        eid='b_wallsection'))
    # NO caption at b22: the drawn STEEL / CONCRETE / STEEL legend under the
    # three bands IS the sentence, and a caption above them would be the same
    # six words twice inside one frame.

    def b_throughwall(tile, fw, fh):
        # ACCRUES onto the b22 section: one continuous aggregate-speckled mass
        # filling the frame between two steel skins, laid over the three
        # separate bands so the concrete is revealed as RUNNING THROUGH them
        # rather than sitting between two plates.
        d = ImageDraw.Draw(tile)
        core = [(-40, 170), (W + 40, 170), (W + 40, 610), (-40, 610)]
        PA.fill_poly(tile, core, (128, 124, 118), seed=163, value=0.07)
        for k in range(70):
            x = -30 + (k * 197) % 1340
            y = 200 + (k * 113) % 400
            PA.fill_poly(tile, [(x, y), (x + 20, y + 7), (x + 8, y + 16)],
                         (168, 164, 156), seed=165 + k, value=0.0)
        for k in range(18):
            x = 40 + (k * 331) % 1200
            y = 210 + (k * 227) % 380
            PA.fill_poly(tile, PA.ellipse_pts(x, y, 17, 13, n=18),
                         (86, 84, 80), seed=200 + k, value=0.05)
        for yy in (170, 610):
            PA.fill_rect(tile, [-40, yy - 34, W + 40, yy], STEEL, seed=220,
                         value=0.08)
            PA.hand_stroke(d, [(-40, yy - 34), (W + 40, yy - 34)], INK, 8,
                           closed=False, seed=221, wavelength=190.0)
            PA.hand_stroke(d, [(-40, yy), (W + 40, yy)], INK, 8, closed=False,
                           seed=222, wavelength=190.0)
    els.append(SC.accrue(clock, 23, 24, b_throughwall, kind='shape'))
    # NO caption at b23: a full-width concrete mass with steel skins top and
    # bottom, cropped at both edges, is the picture of "runs right through".

    def b_thicker(tile, fw, fh):
        # REPLACES the section: a THICK wall block cropped by the left and
        # bottom edges beside a visibly SMALLER door slab, and the size gap is
        # the whole argument, so the presenter stands ON the slab for scale.
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
            y = 116 + (k * 137) % 528          # hatch stays on the slab, y>=104
            PA.hand_stroke(d, [(x, y), (x + 30, y + 10)], (128, 124, 118), 7,
                           closed=False, seed=235 + k, wavelength=50.0, vary=0.25)
        PA.fill_rect(tile, [-40, 596, 700, 660], STEEL, seed=260, value=0.08)
        slab = [(760, 170), (1200, 170), (1200, 560), (760, 560)]
        PA.fill_poly(tile, slab, STEEL_DK, seed=261, value=0.08)
        PA.hand_stroke(d, slab, INK, 8, closed=True, seed=262, wavelength=140.0)
        D.draw_label(tile, 'WALL', center=(300, 640), color=PAPERW, size=48)
        D.draw_label(tile, 'DOOR', center=(980, 640), color=PAPERW, size=48)
        SC.fullbody(d, 980, 556, 260, pose='shrug', expression='skeptic',
                    seed=263)
    els.append(SC.layer(clock, 24, b_thicker, j=26, kind='character',
                        eid='b_thicker'))
    els.append(cap(24, 640, 150, size=32, fill=TY.LABEL_YELLOW))

    def b_castle(tile, fw, fh):
        # The toy castle, cropped by the bottom, with arrows coming in over the
        # left and the red X on the comparison. The stage's last beat: a plain
        # pale card is the right register for a comparison, not a place.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 202, 194), seed=271, value=0.05)
        PA.paper_overlay(tile, seed=272)
        _castle(d, 640, 720, 660, 320, 273)
        for x0, y0 in ((60, 60), (180, 20), (300, 70)):
            D.draw_arrow(tile, (x0, y0), (x0 + 210, y0 + 160), color=RED,
                         width=9, head=44)
        D.draw_red_x(tile, [960, 120, 1230, 300])
        SC.fullbody(d, 1130, 720, 400, pose='recoil', expression='shock',
                    seed=274)
    els.append(SC.layer(clock, 25, b_castle, j=26, kind='character',
                        eid='b_castle'))
    # NO caption at b25: a cartoon castle under arrow fire with a red X through
    # it is the whole comparison, and the presenter recoiling beside it says
    # "built to outlast a siege" without a line of type.

    # ===================================================================== #
    # STAGE E  b26-b30  "The gold sits on nine floors. Rows of bars stacked   #
    #                 to the ceiling. The reserve ran into the hundreds of    #
    #                 billions. At its peak it weighed 12,000 tonnes. The     #
    #                 stacks filled whole wings of it."                       #
    # The stage TURNS FROM OUTSIDE TO INSIDE at b27, and that turn is the     #
    # honest shape of the narration: b26 is a cutaway of the building against #
    # the sky, and from b27 the viewer is IN the storey with the gold. So the #
    # dark interior ground arrives at b27 as an ACCRUING layer and every later #
    # beat lands on it -- the wall of bars, then the ledger column beside it, #
    # then the number band across it -- and the frame fills up in one place   #
    # instead of cutting four times.                                          #
    # ===================================================================== #
    def e_sky(tile, fw, fh):
        _hills(tile, 281, sky=(198, 210, 222))
    els.append(SC.stage(clock, 26, e_sky, j=31))

    def e_section(tile, fw, fh):
        # The building cut open on its flank: NINE storeys, each carrying gold,
        # the cut face and the storeys spanning -111..1292 so the section is
        # cropped by the left, right AND bottom edges. The top 140px is left as
        # sky, which is where the caption goes rather than lying on the gold.
        _floors_section(ImageDraw.Draw(tile), 1726, 150, 780, 9, 282,
                        half_w=1670)
    els.append(SC.accrue(clock, 26, 27, e_section, kind='shape'))
    els.append(cap(26, 640, 128, size=34))

    def e_storey(tile, fw, fh):
        # FROM HERE THE DARK GROUND IS THE STAGE. This layer paints the vault
        # interior and then stacks bars from the near ceiling to the bottom
        # edge, both sides cropped, so "rows of bars stacked to the ceiling" is
        # shown rather than claimed. It accrues: every later beat in this stage
        # is a different thing standing in front of this same wall of gold.
        d = ImageDraw.Draw(tile)
        _dark(tile, 291)
        SC.title_backdrop(tile, 1291, col=TITLE_COURSE)
        _bar_wall(d, -80, 104, W + 80, H + 60, 292, bw=150, bh=54, gap=6,
                  stagger=True)
    els.append(SC.accrue(clock, 27, 31, e_storey, kind='shape'))

    def e_ledger(tile, fw, fh):
        # A paper ledger column cropped by the top and right edges, standing in
        # FRONT of the bars on the right and leaving the left half of the gold
        # visible. This is a text-bearing element, so it REPLACES the wall's
        # right side for its own beat rather than accruing over the bars --
        # two figures in one column is the pile-up rule 1 exists to prevent.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [880, -40, W + 40, H + 40], (234, 228, 212),
                     seed=303, value=0.06)
        PA.hand_stroke(d, [(880, -40), (880, H + 40)], INK, 6, closed=False,
                       seed=304, wavelength=190.0)
        for k in range(7):
            y = 70 + k * 92
            PA.hand_stroke(d, [(908, y + 30), (1230, y + 24)], (176, 170, 152),
                           4, closed=False, seed=305 + k, wavelength=90.0)
            D.draw_number(tile, '%d B' % (28 * (k + 1)), center=(1090, y),
                          color=INK, size=54)
    els.append(SC.layer(clock, 28, e_ledger, j=29, kind='shape', eid='e_ledger'))
    # NO caption at b28: the ledger column PRINTS the billions, 28 B through
    # 196 B, in 54px numerals. v1 captioned this beat too, so the frame said
    # "hundreds of billions" twice at once.

    def e_tonnes(tile, fw, fh):
        # 12,000 TONNES as the frame: a dark band across a cropped bar field
        # with one truck at the bottom edge for the scale. The number is drawn
        # at 178px -- the largest type in the chapter -- which is why there is
        # NO caption on this beat; the sentence and the numeral are the same
        # object, and printing both is how a frame ends up with two competing
        # centres of gravity.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 200, W, 396], (34, 30, 34), seed=313, value=0.05)
        D.draw_number(tile, '12,000', center=(540, 298), color=GOLD_HI, size=178)
        D.draw_label(tile, 'TONNES', center=(1070, 298), color=GOLD_HI, size=64)
    # NO motion on this element even though it is the chapter's biggest reveal.
    # The band spans the full frame, so a 150px arrival slides the WHOLE picture
    # for half a second -- exactly the churn rule 2 exists to prevent. It pops
    # in; the truck in front of it is the thing allowed to move.
    els.append(SC.layer(clock, 29, e_tonnes, j=30, kind='shape', eid='e_tonnes'))

    def e_truck(tile, fw, fh):
        # MOVING, small: one loaded truck at the bottom edge, running in from
        # the right. 350px over 0.55s, and it is the scale that makes 12,000
        # tonnes mean anything.
        _truck(ImageDraw.Draw(tile), 1010, 740, 350, 314)
    els.append(SC.accrue(clock, 29, 30, e_truck, kind='shape',
                         motion=SC.enter(clock, 29, dx=150, dur=0.55)))

    def e_wings(tile, fw, fh):
        # FOUR ranks marching away, each running off both side edges, so the
        # stacks fill whole wings of a building the frame never shows whole.
        _bar_hall(ImageDraw.Draw(tile), 321, fill_frac=1.0, floor_y=700, back=4)
    els.append(SC.layer(clock, 30, e_wings, j=31, kind='shape', eid='e_wings'))
    els.append(cap(30, 640, 690, size=32, fill=GOLD_HI))

    # ===================================================================== #
    # STAGE F  b31-b36  "Much of that gold belongs to other governments.      #
    #                 Small national flags above one vault door. The vault    #
    #                 holds their gold as well. Only a small share stays on   #
    #                 site. Only a few hundred tonnes remain. The rest was    #
    #                 moved out years ago."                                  #
    # One vault interior held across six beats, and the flags are the thing   #
    # that makes it cohere: they go up at b32 and stay up while the door, the #
    # presenter and the emptying floor happen underneath them. v1 gave the     #
    # flags a whole full frame at b32 and then redrew the same flags inside a #
    # different frame at b33; here there is one row, planted once.            #
    # ===================================================================== #
    def f_vault(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 331)
        SC.title_backdrop(tile, 1331, col=TITLE_COURSE)
        # The near rank, kept low (from y=250) so the upper third of the vault
        # stays clear for the flags and the door head -- the same reason v1
        # started this wall at 250 rather than at the ceiling.
        _bar_wall(d, -70, 250, W + 70, 700, 332, bw=138, bh=48, gap=6,
                  stagger=True)
    els.append(SC.stage(clock, 31, f_vault, j=37))

    def f_door(tile, fw, fh):
        # The door pushed low and cropped by the bottom edge, so the flags
        # genuinely sit ABOVE it rather than beside it.
        _vault_door(ImageDraw.Draw(tile), 560, 560, 300, 342, hinge=True,
                    wheel=True, rings=3, bolts=18)
    els.append(SC.accrue(clock, 32, 37, f_door, kind='shape'))

    def f_flags(tile, fw, fh):
        # MOVING, small: a row of 54px flags rising 28px into the dark above
        # the door. Flags are the smallest repeated object in the chapter, so
        # they are the right subject for the one moving beat in this stage.
        _flag_row(ImageDraw.Draw(tile), 120, 1180, 200, 343, n=6, h=54)
    els.append(SC.accrue(clock, 32, 37, f_flags, kind='shape',
                         motion=SC.enter(clock, 32, dx=0, dy=-28, dur=ARRIVE)))
    # NO captions at b31, b32 or b33. "Much of that gold belongs to other
    # governments" is what a row of national flags standing on foreign gold
    # says; "small national flags above one vault door" describes the picture
    # exactly; and "the vault holds their gold as well" is carried by the door
    # standing IN the bars with the flags over it. v1 captioned all three.

    def f_in_gold(tile, fw, fh):
        # The presenter standing IN the gold at the right of the door, cropped
        # by the bottom, shrugging at the arrangement. He lives to b34 only,
        # because b04's version of him stands in a different gap in a different
        # hall and two presenters in one frame is the pile-up rule again.
        SC.fullbody(ImageDraw.Draw(tile), 980, 726, 400, pose='shrug',
                    expression='skeptic', seed=354)
    els.append(SC.accrue(clock, 33, 34, f_in_gold, kind='character'))

    def f_mostly_empty(tile, fw, fh):
        # THE SAME HALL ROUTINE, with fill_frac<1 so the right of the floor is
        # BARE and the presenter stands in the gap at 470px. The empty floor is
        # the point of the beat, so it is real bare floor -- not a dark overlay
        # pretending to be absence. REPLACES the vault above it: the hall is a
        # different room from the flag vault and cannot share the frame.
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 361, fill_frac=0.52, floor_y=690, back=3)
        SC.fullbody(d, 1010, 690, 470, pose='shrug', expression='skeptic',
                    seed=362)
    els.append(SC.layer(clock, 34, f_mostly_empty, j=35, kind='character',
                        eid='f_mostly_empty'))
    els.append(cap(34, 990, 140, size=32, fill=TY.LABEL_RED, max_w=560))

    def f_few_hundred(tile, fw, fh):
        # Two short ranks, a lot of bare floor, and the small number stamped on
        # the empty floor where the gold is not.
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 371, fill_frac=0.40, floor_y=700, back=2)
        D.draw_label(tile, 'A FEW HUNDRED', center=(930, 430),
                     color=(250, 232, 168), size=42)
    els.append(SC.layer(clock, 35, f_few_hundred, j=36, kind='shape',
                        eid='f_few_hundred'))
    # NO caption at b35: the drawn A FEW HUNDRED legend sits on the bare floor
    # and says the line. A caption under it printed the same four words twice.

    def f_moving_out(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 202, 208), seed=381, value=0.05)
        PA.fill_rect(tile, [0, 520, W, H], (166, 168, 172), seed=382, value=0.07)
        PA.paper_overlay(tile, seed=383)
        _truck(d, 850, 662, 300, 385, col=(150, 74, 60))
        _truck(d, 1150, 634, 190, 386, col=(140, 70, 58))
        D.draw_arrow(tile, (700, 268), (250, 268), color=RED, width=12, head=54)
    els.append(SC.layer(clock, 36, f_moving_out, j=37, kind='shape',
                        eid='f_moving_out'))

    def f_near_truck(tile, fw, fh):
        # MOVING, and the only place a fast arrival is right in this stage: the
        # narrator says the gold was MOVED OUT, and the loaded truck running off
        # the left edge is the clearest read of that. 540px wide over 0.55s is
        # the fastest element in the chapter and still only ~490px/s for half a
        # second.
        _truck(ImageDraw.Draw(tile), 180, 704, 540, 384)
    els.append(SC.accrue(clock, 36, 37, f_near_truck, kind='shape',
                         motion=SC.enter(clock, 36, dx=-170, dur=0.55)))
    els.append(cap(36, 640, 560, size=34, fill=TY.LABEL_RED))

    # ===================================================================== #
    # STAGE G  b37-b41  "A visitor counter, a ledger, a stamp. Thousands of   #
    #                 people tour it every year. School field trips arrive    #
    #                 each spring. A line of children in a corridor. They     #
    #                 walk above the stored gold."                           #
    # The public side of the building, and the one stage where a PILE of      #
    # people is the subject. b37-b38 genuinely accumulate -- the counter is   #
    # built, then the crowd arrives in front of it -- because a queue at a     #
    # desk and the desk itself are the same place. b39-b40 change location    #
    # (road, then corridor) and b41 is the diagram the whole chapter has been #
    # walking toward, so those three REPLACE. The faces stay blank: v1's      #
    # comment on `_person` records that a queue of tooned heads turns a crowd  #
    # into a row of staring portraits, and this chapter has exactly one real  #
    # face to spend.                                                          #
    # ===================================================================== #
    def g_wall(tile, fw, fh):
        _pale(tile, 391, (216, 212, 202))
    els.append(SC.stage(clock, 37, g_wall, j=42))

    def g_counter(tile, fw, fh):
        # The counter running off BOTH edges, so the queue it serves has
        # somewhere to come from. The ledger and the stamp sit on it: three
        # props, one beat, and the props are what the line is naming.
        d = ImageDraw.Draw(tile)
        _counter(d, -60, 1340, 700, 240, 392)
        _page(d, 300, 432, 700, 596, 393, lines=5)
        _stamp(d, 880, 516, 64, 394)
    els.append(SC.accrue(clock, 37, 38, g_counter, kind='shape'))
    # NO caption at b37 and NO drawn "VISITORS" label. The counter, the ruled
    # ledger with its red margin rule, and the ink stamp are the three things
    # the sentence names, in that order, in one frame; v1 printed a caption AND
    # a VISITORS label over them.
    # It ends at j=38, NOT j=39: the crowd at b38 stands at the same counter in
    # the same band, and a queue drawn on top of the ledger buries the ledger
    # (verified on the b38 frame -- the page survived as a white sliver with
    # its red rule showing through). The props are b37's subject; when the
    # crowd arrives they leave. See g_crowd.

    def g_crowd(tile, fw, fh):
        # REPLACES the counter and its props. The queue is the subject at b38,
        # and rule 1 says anything sharing a region of the frame replaces
        # rather than accrues -- the ledger and the stamp would be unreadable
        # underneath a rank of bodies (verified on the first b38 frame: the
        # page survived only as a white sliver with its red rule showing).
        # The props are b37's subject; when the crowd arrives they leave.
        #
        # Thirteen figures in three ranks, positioned by explicit x lists
        # rather than even division. Even division was tried and rejected: it
        # either packs the band edge to edge (v1, sixteen figures -- the
        # over-populated frame that is this project's recurring critic loss) or
        # spaces them into a picket fence. These lists let the front rank run
        # the full width while the ranks behind stagger into the gaps, so the
        # eye reads depth instead of a row.
        d = ImageDraw.Draw(tile)
        _counter(d, -60, 1340, 700, 240, 392)
        # The presenter keeps the left third: his pointing arm ends near x=300,
        # so the queue starts at x=370.
        cols = ((70, 96, 168), (188, 96, 72), (96, 150, 116), (168, 152, 96))
        ranks = ((700, 232, (370, 600, 830, 1060, 1270)),
                 (656, 202, (478, 712, 946, 1180)),
                 (614, 174, (418, 655, 892, 1128)))
        for r, (y, h, xs) in enumerate(ranks):
            for i, x in enumerate(xs):
                _person(d, x, y, h, 410 + r * 20 + i, col=cols[(i + r) % 4])
    els.append(SC.layer(clock, 38, g_crowd, j=39, kind='character',
                        eid='g_crowd'))
    # The caption sits in the dark grille opening ABOVE the counter (y 160-434),
    # which is the one region of this frame with nothing in it. Laid over the
    # front rank it fought a dozen coloured torsos for legibility; at y=128 it
    # fouled the title band.
    els.append(cap(38, 640, 300, size=32))

    def g_man_a(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 132, 700, 440, pose='pointing', expression='neutral',
                    seed=396)
    els.append(E3.E('g_man_a', 'character', g_man_a, at=T(37), until=T(38),
                    motion=SC.enter(clock, 37, dx=-130, dur=0.55)))

    def g_man_b(tile, fw, fh):
        # He changes expression at b38 as the crowd arrives: pointing at the
        # ledger becomes open-handed surprise at the thousands of people. Two
        # elements at the same position, the first ending where the second
        # starts, because the expression is baked into the rasterised tile.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 132, 700, 440, pose='wave', expression='impressed',
                    seed=396)
    els.append(E3.E('g_man_b', 'character', g_man_b, at=T(38), until=T(39)))

    def g_buses(tile, fw, fh):
        # REPLACES the hall: two buses on the road, the near one cropped by the
        # left edge so it is ARRIVING rather than parked, with the presenter
        # waving from the kerb. NO caption -- the drawn EVERY SPRING legend says
        # the line, and the buses are the answer to it.
        d = ImageDraw.Draw(tile)
        _hills(tile, 421)
        _bus(d, 220, 694, 480, 422)
        _bus(d, 880, 706, 480, 423, col=(216, 170, 40))
        D.draw_label(tile, 'EVERY SPRING', center=(640, 176),
                     color=TY.LABEL_INK, size=48)
        SC.fullbody(d, 1140, 700, 340, pose='wave', expression='smirk',
                    seed=424)
    els.append(SC.layer(clock, 39, g_buses, j=40, kind='character',
                        eid='g_buses'))
    # NO caption at b39 or b40. "School field trips arrive each spring" is two
    # yellow buses and a legend; "a line of children in a corridor" is a line
    # of small figures receding to a lit far end, which is the only depth cue a
    # flat frame has and needs no words to work.

    def g_children(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 640, 392, 431, floor_y=580, w0=1420)
        spots = ((170, 700, 340), (430, 664, 300), (660, 634, 262),
                 (856, 610, 226), (1010, 590, 194), (1136, 574, 168),
                 (1236, 562, 146))
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, (x, y, h) in enumerate(spots):
            _person(d, x, y, h, 440 + i, col=cols[i % 4])
    els.append(SC.layer(clock, 40, g_children, j=41, kind='shape',
                        eid='g_children'))

    def g_deck(tile, fw, fh):
        # THE SECTION THE CHAPTER HAS BEEN WALKING TOWARD: the public corridor
        # deck carried on a slab directly over the gold storey, with the
        # visitors walking on top and the bars visible in the storey below their
        # feet. Both halves cropped by the frame, so the building continues
        # past the picture.
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
    els.append(SC.layer(clock, 41, g_deck, j=42, kind='character',
                        eid='g_deck'))
    els.append(cap(41, 640, 686, size=32))

    # ===================================================================== #
    # STAGE H  b42-b44  "They never walk below the gold. The inner doors stay #
    #                 bolted shut. Almost nobody alive has seen inside."     #
    # Three beats, 6.6s, the shortest stage, and the only one whose job is to  #
    # stop: b42 flips the deck's lower storey from open to barred, b43 goes    #
    # to the bolted inner door, b44 pulls back to a corridor with nobody in it.#
    # Each REPLACES -- they are three different rooms and no two of them can   #
    # share a frame without one becoming unreadable.                           #
    # ===================================================================== #
    def h_vault(tile, fw, fh):
        # The deepest the chapter goes: one dark vault ground for the last three
        # beats. The layers above it each repaint their own room, but the
        # register underneath them is the same night stone, so the stage turn
        # reads as descending rather than as three unrelated cards.
        _dark(tile, 481, top=(44, 44, 52), bot=(30, 30, 36))
    els.append(SC.stage(clock, 42, h_vault, j=45))
    def h_sealed(tile, fw, fh):
        # The SAME _deck_section with sealed=True, so the only difference from
        # b41 is whether the lower storey is lit and open or barred. That the
        # two beats are visibly the SAME diagram is the entire argument of the
        # pair: the public route above, the sealed route below.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (214, 210, 200), seed=471, value=0.05)
        PA.paper_overlay(tile, seed=472)
        _deck_section(d, 473, deck_y=470, sealed=True)
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, x in enumerate((40, 190, 340, 490, 640, 790, 940, 1090, 1240)):
            _person(d, x, 452, 210, 480 + i, col=cols[i % 4])
        D.draw_label(tile, 'NEVER BELOW IT', center=(640, 146),
                     color=TY.LABEL_INK, size=40)
    els.append(SC.layer(clock, 42, h_sealed, j=43, kind='shape', eid='h_sealed'))
    # NO caption at b42: the drawn NEVER BELOW IT legend is the line, and v1
    # printed it a second time underneath as a caption.

    def h_bolted(tile, fw, fh):
        # The innermost door: a flat steel slab in a thick frame, barred by
        # heavy horizontal bolt bars. NO WHEEL, on purpose -- the main door's
        # wheel is the thing that says "this can be opened", and a mechanism
        # here would argue against the line.
        d = ImageDraw.Draw(tile)
        _dark(tile, 491, top=(44, 44, 52), bot=(30, 30, 36))
        _inner_door(d, 640, 360, 1000, 720, 492, bolt=6)
    els.append(SC.layer(clock, 43, h_bolted, j=44, kind='shape', eid='h_bolted'))
    # NO caption at b43: six bolt bars across a steel slab IS "the inner doors
    # stay bolted shut", and it is the last thing before the finale, which wants
    # the frame to itself.

    def h_nobody(tile, fw, fh):
        # THE LAST FRAME. A close-up in an EMPTY corridor -- the walls converge
        # on a lit end with nobody standing in it, and he is the only person in
        # the picture, which is the line. The bubble is his, not the narrator's:
        # "nobody alive" is what he is thinking, and the caption underneath is
        # what the narrator says. Two different texts, so they do not collide --
        # and they are 470px apart vertically.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (48, 48, 56), seed=501, value=0.10)
        PA.paper_overlay(tile, seed=502)
        SC.title_backdrop(tile, 1501, col=TITLE_COURSE)
        for s in (-1, 1):
            x = s * (W / 2.0 + 60)
            x0 = x + (900.0 - x) * (144.0 / 340.0)
            wall = [(x0, 104), (900, 300), (900, 470), (x, H + 40)]
            PA.fill_poly(tile, wall, (66, 66, 74), seed=503 + s, value=0.07)
            PA.hand_stroke(d, wall, INK, 7, closed=False, seed=505 + s,
                           wavelength=180.0)
        PA.fill_poly(tile, [(-60, H + 40), (900, 470), (900, 470),
                            (W + 60, H + 40)], (58, 58, 66), seed=507, value=0.07)
        SC.closeup(d, 330, 400, 235, 'worried', 508)
        D.draw_bubble(tile, 'nobody alive', xy=(880, 190), tail_to=(640, 300),
                      font_size=38, max_w=420)
    els.append(SC.layer(clock, 44, h_nobody, j=45, kind='character',
                        eid='h_nobody'))
    els.append(cap(44, 950, 656, size=34, fill=TY.LABEL_YELLOW, max_w=520))

    # STAGES are appended below, in order.
    return SC.finish(els, TITLE, clock, title_seed=7)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
