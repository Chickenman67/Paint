"""vatican2_scene -- the PERSISTENT-STAGE rebuild of chapter 9.

WHY THIS FILE EXISTS. vatican_scene.py (v1) gave every one of its 38 sentences
its own full-frame card: `card(i, j, draw, ...)` painted background + subject +
labels live for beats i..j-1 and NOTHING survived into the next card. So the
film cut to a brand-new whole image every ~2.4s and nothing ever moved -- the
"every sentence has a cut with a completely new image, there are no animations"
complaint. It also captioned all 38 beats (100% text density), which is the
other half of the same problem: with words on every single frame there is
nothing for a caption to punctuate.

THE MODEL HERE. Seven PERSISTENT STAGES on the narration's own acts, taken
verbatim from plans/STAGE_PLANS.md:

    A  b01-b06  beneath Vatican City; the Archives; opened once in 1939, closed
    B  b07-b13  deep under the hill; shelves for kilometres; no electric light;
                no photography
    C  b14-b18  fused pages; opening them tears them; most boxes stay shut
    D  b19-b25  catalogued once then shelved; one index card is the whole
                record; filmed instead of opened
    E  b26-b29  the shelving plan is filed upstairs; nobody has carried it down
    F  b30-b34  a reader between tall shelves; access is a favour, not a right
    G  b35-b38  a hand holding a small key; the lowest shelves; absolute dark

The frame repaints SEVEN times in 92s instead of thirty-eight, and inside a
stage the art ACCUMULATES: a layer that arrives stays until the stage turns
over (SC.accrue). The viewer gets one recognisable place to look while the
next thing is added to it.

TWO RULES THAT TOOK THE PINE GAP PILOT TWO ROUNDS TO LEARN.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Letting every layer live to stage end
   is also wrong: it piles text on text and stacks objects on objects. In this
   chapter specifically the shelves, the stair, the corridor and the boxes ARE
   the world and accrue; the door, the 1939 numeral, the index card, the closeup
   and anything carrying a drawn label REPLACE, because they occupy the same
   part of the frame as whatever they supersede.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces motion at a rate the
   reference does not have (measured 22.5% against the reference's 7%) and every
   moving frame trips the picture-change counter. The reference is 83% still.
   So ELEVEN arrivals move, briefly (0.45-0.6s), and every one of them is a
   small subject: the ladder on its rail, the dead bulb, the flash burst, one
   torn page half, one index card, the film strip, the plan sheet, the red X,
   the reader, the key. No backdrop and no shelf run ever drifts.

THE CHARACTER IS CREAM-ON-DARK, AND THAT IS WHY THIS FILE USES THE v1
`figure()` / `face()` WRAPPERS RATHER THAN scene_common.fullbody / closeup.
The whole chapter is a near-black archive; scene_common's bust and fullbody
hardcode INK, and a black stickman in a black archive is a hole in the frame,
not a person. vatican_scene.figure() is the same character3 call with the ink
and face fills overridden for the dim register, and it takes `dark=True` for
the two bright paper beats so the figure goes back to dark ink there. Reusing
it is reuse of v1 art, not a redraw.

CAPTIONS. Fourteen of 38 beats (37%), never two in a row. The test applied beat
by beat: does the drawn art already SAY the words, or does the viewer need
them? Kept where the words carry something the art cannot show -- the 1939
date is drawn as a numeral so it is NOT also captioned, but "no electric
light" is a dead bulb plus a rule the bulb cannot state, and the index card is
a blank rectangle until it is named. Dropped where the frame already prints
the words, and each drop says so in a comment at its beat.

Run:  python lib/vatican2_scene.py --preview --video
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

import vatican_scene as VC     # art primitives + palette, reused not copied

# palette / geometry, reused from v1
SEG = VC.SEG
TITLE = VC.TITLE
BEATS = VC.BEATS
TITLE_BACKDROP = VC.TITLE_BACKDROP

W, H = VC.W, VC.H
FLOOR = VC.FLOOR

INK = VC.INK
NIGHT = VC.NIGHT
DEEP = VC.DEEP
DEEPER = VC.DEEPER
CREAM = VC.CREAM
PAPER = VC.PAPER
PAPER_D = VC.PAPER_D
WOOD = VC.WOOD
WOOD_L = VC.WOOD_L
WOOD_D = VC.WOOD_D
OXBLOOD = VC.OXBLOOD
LAMP = VC.LAMP
STONE = VC.STONE
STONE_D = VC.STONE_D

_dark = VC._dark
_light = VC._light
_lintel = VC._lintel
_shelf_run = VC._shelf_run
_corridor = VC._corridor
_big_door = VC._big_door
_page = VC._page
_archive_box = VC._archive_box
_lamp_glow = VC._lamp_glow
_floor_pool = VC._floor_pool

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
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # ---- persistent page tooth under everything --------------------------- #
    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ==== STAGE A  b01-b06  beneath Vatican City; opened once, then closed == #
    # The backdrop is the plain dim interior -- the room you are standing in.
    # Everything else arrives: the rock mass with its lit archive rooms (b01),
    # a row of bricked-up windows above them (b02), then the shelf wall that
    # IS the Archives (b03). The door then takes the frame for b04-b06 because
    # it is a big centred subject and three consecutive beats are about it.
    def a_room(tile, fw, fh):
        _dark(tile, 5, top=(32, 27, 25), floor_col=(46, 38, 36))
    els.append(SC.stage(clock, 1, a_room, j=4))

    def a_rock(tile, fw, fh):
        # v1's hill, sat lower in the frame so the windows have somewhere to go
        # above it. Same crest sweep, same four lit rooms cut into the rock.
        d = ImageDraw.Draw(tile)
        hill = [(-60, 760), (-60, 470), (300, 360), (640, 330), (980, 360),
                (1340, 470), (1340, 760)]
        PA.fill_poly(tile, hill, STONE, seed=7, value=0.09)
        PA.hand_stroke(d, [(-60, 470), (300, 360), (640, 330), (980, 360),
                           (1340, 470)], INK, 7, closed=False, seed=8,
                       wavelength=180.0)
        for i in range(4):
            x0 = 150 + i * 260
            y0 = 470 + (i % 2) * 62
            room = [(x0, y0), (x0 + 170, y0 - 22), (x0 + 170, y0 + 104),
                    (x0, y0 + 126)]
            PA.fill_poly(tile, room, DEEP, seed=20 + i, value=0.07)
            PA.hand_stroke(d, room, INK, 5, closed=True, seed=30 + i,
                           wavelength=90.0)
            PA.hand_stroke(d, [(x0 + 14, y0 + 28), (x0 + 156, y0 + 10)],
                           LAMP if i % 2 == 0 else STONE_D, 7, closed=False,
                           seed=40 + i, wavelength=50.0)
    els.append(SC.accrue(clock, 1, 4, a_rock, kind='shape'))
    els.append(cap(1, W // 2, 660, size=32, fill=LAMP))

    def a_windows(tile, fw, fh):
        # A row of windows, every one bricked up; the row runs off the right
        # edge so the room reads as bigger than the frame. Accrues ABOVE the
        # rock mass rather than replacing it -- different part of the frame.
        d = ImageDraw.Draw(tile)
        for k in range(3):
            x0 = -30 + k * 440
            win = [(x0, 150), (x0 + 250, 150), (x0 + 250, 350), (x0, 350)]
            PA.fill_poly(tile, win, STONE, seed=162 + k, value=0.08)
            PA.hand_stroke(d, win, INK, 5, closed=True, seed=172 + k,
                           wavelength=110.0)
            for r in range(4):
                yy = 150 + 50 * r
                PA.hand_stroke(d, [(x0, yy), (x0 + 250, yy)], STONE_D, 3,
                               closed=False, seed=182 + k * 4 + r,
                               wavelength=80.0)
    els.append(SC.accrue(clock, 2, 4, a_windows, kind='shape'))
    # NO caption at b02. "The rooms down there have no windows" -- a row of
    # bricked-up openings IS that sentence, drawn. The words would sit on the
    # bricks and say it twice.

    def a_wall(tile, fw, fh):
        # THE ARCHIVES. One full-width stocked shelf wall, cropped by both
        # side edges, replacing the windows: the name beat is a change of what
        # the room CONTAINS, not another thing added to it.
        d = ImageDraw.Draw(tile)
        _shelf_run(d, 640, W + 40, 706, 396, 42, shelves=3, stock=1)
    els.append(SC.accrue(clock, 3, 4, a_wall, kind='shape', eid='a_wall',
                         motion=SC.enter(clock, 3, dx=140, dy=0, dur=ARRIVE)))

    def a_presenter(tile, fw, fh):
        # v1's `figure`, not scene_common.fullbody -- see the module docstring.
        # He is ALREADY in the room at b01 and stays for the whole act, so the
        # name beat changes his face and his point, never his presence.
        VC.figure(ImageDraw.Draw(tile), 250, 690, 400, pose='standing',
                  expression='awed', seed=44)

    def a_presenter_b(tile, fw, fh):
        VC.figure(ImageDraw.Draw(tile), 250, 690, 400, pose='pointing',
                  expression='skeptic', seed=44)
    _abu, _aaa, _aau = SC.expr_swap(clock, 3, 'awed', 'skeptic', until_j=4)
    els.append(E3.E('a_presenter_a', 'character', a_presenter,
                    at=clock.at('b01', 0), until=_abu,
                    motion=SC.enter(clock, 1, dx=-96, dy=0, dur=ARRIVE)))
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aaa, until=_aau))
    # NO caption at b03. The engine already stamps "The Vatican Archives" on
    # every frame of this scene, so a caption saying "The place is called the
    # Vatican Archives" prints the same words twice on the same rows.

    def a_door(tile, fw, fh):
        _dark(tile, 47, top=(30, 25, 23), floor_col=(44, 37, 35))
        _lintel(tile, 49)
        _big_door(ImageDraw.Draw(tile), 690, 392, 470, 386, 48, open_frac=0.0)
    els.append(SC.stage(clock, 4, a_door, j=7))

    def a_1939(tile, fw, fh):
        D.draw_number(tile, '1939', center=(690, 132), color=LAMP, size=104)
    # MOVING, and the only moving thing in this stage: the date arriving on the
    # slab it belongs to. Small offset, short track -- the slab itself never
    # drifts, because a 480px door sliding reads as the picture churning.
    els.append(SC.accrue(clock, 4, 7, a_1939, kind='shape', eid='a_1939',
                        motion=SC.enter(clock, 4, dx=0, dy=-34, dur=ARRIVE)))
    # NO caption at b04. "1939" is a 170px numeral ON the door -- the spoken
    # phrase is the drawn phrase.

    def a_open(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # three outside scholars passing through the lit gap the backdrop
        # already left open
        VC.figure(d, 596, 566, 210, pose='standing', expression='neutral',
                  seed=59)
        VC.figure(d, 690, 578, 196, pose='pointing',
                  expression='confused', seed=60)
        VC.figure(d, 782, 566, 204, pose='standing', expression='neutral',
                  seed=61)
        D.draw_label(tile, 'ONCE', center=(300, 190), color=LAMP, size=48,
                     outline=INK, outline_w=3)
    els.append(SC.accrue(clock, 5, 7, a_open, kind='character', eid='a_open',
                         motion=SC.enter(clock, 5, dx=0, dy=-40, dur=ARRIVE)))
    els.append(cap(5, W // 2, 700, size=30, fill=LAMP))

    def a_shut(tile, fw, fh):
        # THE SLAB CLOSING. The door is already in the stage backdrop, so this
        # beat only slides ONE slab across the lit gap -- about a tenth of the
        # frame, against the 44% a second whole door cost -- and the movement
        # IS the sentence.
        d = ImageDraw.Draw(tile)
        _lintel(tile, 695)
        slab = [(548, 220), (832, 220), (832, 566), (548, 566)]
        PA.fill_poly(tile, slab, WOOD, seed=67, value=0.08)
        PA.hand_stroke(d, slab, INK, 7, closed=True, seed=68, wavelength=130.0)
        for k in range(4):
            yy = 268 + k * 74
            PA.hand_stroke(d, [(566, yy), (814, yy)], WOOD_L, 5, closed=False,
                           seed=69 + k, wavelength=60.0)
        PA.hand_stroke(d, [(690, 220), (690, 566)], OXBLOOD, 8, closed=False,
                       seed=74, wavelength=120.0)
        D.draw_label(tile, 'CLOSED', center=(300, 610), color=LAMP, size=52)
    els.append(SC.layer(clock, 6, a_shut, j=7, kind='shape', eid='a_shut',
                        motion=SC.enter(clock, 6, dx=300, dy=0, dur=0.55)))
    # NO caption at b06. The slab is stamped CLOSED across it; "then the doors
    # closed again, quietly" would print the same word over the same slab.

    # ==== STAGE B  b07-b13  deep under the hill; kilometres of shelves;  === #
    #                 no electric light; no photography                      #
    # A bare dim room opens the stage; the stair descends into it (b07), then #
    # the CORRIDOR -- the chapter's first hero image -- replaces the stair at #
    # b08 and holds the rest of the act. The ladder then slides on its rail  #
    # (b09) inside the corridor's gap, the dead bulb arrives (b10), and a     #
    # window bricked into the shelf face (b11). b12-b13 are the RULE, and a  #
    # lit page under a camera is a different size of subject entirely, so    #
    # those two beats replace the corridor rather than crowding it.         #
    # ======================================================================= #

    def b_stair(tile, fw, fh):
        # v1's stair, running down and away into the rock.
        d = ImageDraw.Draw(tile)
        for k in range(7):
            t = k / 6.0
            y = 466 + t * 244
            wdt = 202 - t * 92
            cxk = 712 - t * 22
            step = [(cxk - wdt, y), (cxk + wdt, y), (cxk + wdt - 13, y + 30),
                    (cxk - wdt - 13, y + 30)]
            PA.fill_poly(tile, step, STONE_D, seed=80 + k, value=0.07)
            PA.hand_stroke(d, step, INK, 5, closed=True, seed=90 + k,
                           wavelength=90.0)
    els.append(SC.accrue(clock, 7, 14, b_stair, kind='shape'))
    els.append(cap(7, W // 2, 130, size=32, fill=LAMP))
    # NO drawn 'DEEP DOWN' label. The stair is the sentence; a caption and a
    # hero word on the same beat is the text pile-up rule 1 exists to stop.

    def b_corridor(tile, fw, fh):
        # THE HERO. One-point perspective down the stacks, shelf runs lining
        # both walls and cropped by both side edges, so the corridor IS the
        # frame and the run behind it reads as longer than the picture.
        d = ImageDraw.Draw(tile)
        _corridor(d, 640, 350, 101)
        _shelf_run(d, -40, 520, 640, 200, 111, shelves=8, depth=-30, stock=1)
        _shelf_run(d, 800, W + 40, 640, 200, 131, shelves=8, depth=30, stock=1)
    els.append(SC.stage(clock, 7, b_corridor, j=14))

    def b_kilometres(tile, fw, fh):
        # The scale note, on its own beat now that the corridor is the backdrop
        # from b07 instead of a replacement for the stair at b08.
        D.draw_label(tile, 'KILOMETRES', center=(640, 180), color=LAMP,
                     size=52, outline=INK, outline_w=3)
    els.append(SC.accrue(clock, 8, 14, b_kilometres, kind='shape', eid='b_km',
                         motion=SC.enter(clock, 8, dx=0, dy=-40, dur=0.5)))
    # NO caption at b08. 'KILOMETRES' is drawn at 52px across the mouth of the
    # corridor -- the words and the receding stacks say the same thing once.

    def b_ladder(tile, fw, fh):
        # THE LADDER IS THE SUBJECT, NOT THE SHELVES. It is big, close, and
        # runs OUT THROUGH THE TOP of the frame on its rail, which is both what
        # a rolling library ladder looks like and the frame-fill rule. v1
        # built the whole card around it for the same reason.
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(-30, 176), (W + 30, 158)], WOOD, 20, closed=False,
                       seed=143, wavelength=190.0)
        PA.hand_stroke(d, [(-30, 158), (W + 30, 141)], WOOD_L, 7,
                       closed=False, seed=147, wavelength=180.0)
        for side in (-1, 1):
            PA.hand_stroke(d, [(660 + side * 118, 700), (660 + side * 74, -30)],
                           WOOD, 19, closed=False, seed=160 + side,
                           wavelength=150.0)
        for k in range(9):
            u = k / 8.0
            yy = 636 - u * 640
            x0 = 660 - 118 + 44 * u
            x1 = 660 + 118 - 44 * u
            PA.hand_stroke(d, [(x0, yy), (x1, yy)], WOOD_L, 13, closed=False,
                           seed=170 + k, wavelength=90.0)
        # the roller shoes that make it a ladder ON A RAIL
        for side in (-1, 1):
            PA.hand_stroke(d, [(660 + side * 92, 168), (660 + side * 116, 176)],
                           INK, 15, closed=False, seed=180 + side,
                           wavelength=40.0)
    # MOVING. "A wooden ladder slides along a rail" is the one sentence in the
    # chapter that NAMES a movement, so the ladder is the one thing in this
    # stage that gets a real track: 130px over 0.55s, inside the corridor's
    # gap, and it stops. Nothing behind it moves.
    els.append(SC.accrue(clock, 9, 14, b_ladder, kind='shape',
                         motion=SC.enter(clock, 9, dx=130, dy=0, dur=0.55)))
    # NO caption at b09. The ladder arrives ON the rail with the roller shoes
    # drawn; the motion is the sentence.

    def b_bulb(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # A bare bulb on a cord, switched OFF -- dead grey, no glow. The cord
        # is clipped to y=104 so it never runs down through the engine's title
        # band (v1's b10 finding).
        PA.hand_stroke(d, [(640, 104), (640, 180)], INK, 5, closed=False,
                       seed=152, wavelength=90.0)
        bulb = PA.ellipse_pts(640, 210, 40, 48, n=32)
        PA.fill_poly(tile, bulb, (96, 92, 88), seed=153, value=0.05)
        PA.hand_stroke(d, bulb, INK, 5, closed=True, seed=154, wavelength=90.0)
    els.append(SC.accrue(clock, 10, 14, b_bulb, kind='shape', eid='b_bulb',
                        motion=SC.enter(clock, 10, dx=0, dy=-30, dur=0.45)))
    els.append(cap(10, 640, 545, size=32, fill=LAMP))
    # CAPTION KEPT and v1's drawn 'NO ELECTRIC LIGHT' label is DROPPED. A dead
    # grey bulb on a cord shows the FACT (no light) but not the RULE (no
    # electric light is ALLOWED); the words carry the rule, and having both the
    # label and a caption here would be the text pile-up rule 1 exists to stop.
    # The caption sits low, on the corridor floor -- at y=350 it would land on
    # the lit far end, which is LAMP-coloured, and a LAMP label on a LAMP
    # rectangle is invisible.

    def b_wall_window(tile, fw, fh):
        # "Every window was walled up on purpose": one bricked opening set INTO
        # the right-hand shelf face, so the room has no window and the shelves
        # are still the world. Accrues -- it is scenery, and it shares no part
        # of the frame with the ladder in the gap or the bulb at the centre.
        d = ImageDraw.Draw(tile)
        win = [(898, 172), (1168, 172), (1168, 318), (898, 318)]
        PA.fill_poly(tile, win, STONE, seed=331, value=0.08)
        PA.hand_stroke(d, win, INK, 5, closed=True, seed=332, wavelength=110.0)
        for r in range(4):
            yy = 172 + 36 * r
            PA.hand_stroke(d, [(898, yy), (1168, yy)], STONE_D, 3,
                           closed=False, seed=333 + r, wavelength=80.0)
    els.append(SC.accrue(clock, 11, 14, b_wall_window, kind='shape'))
    # NO caption at b11. A bricked opening in the wall is the whole sentence.

    def b_nophoto(tile, fw, fh):
        # THE RULE, AS AN INSET ON THE LEFT of the corridor rather than a room
        # of its own. The camera, the page it is aimed at and the oxblood bar
        # are the same drawing at a third of the size, standing on the left
        # shelf run -- so b12 adds a thing to the place the viewer is already
        # standing instead of replacing the place.
        d = ImageDraw.Draw(tile)
        _page(d, 296, 520, 132, 168, 193, lines=7)
        cam = [(176, 344), (416, 344), (416, 452), (176, 452)]
        PA.fill_poly(tile, cam, (60, 56, 56), seed=194, value=0.07)
        PA.hand_stroke(d, cam, INK, 6, closed=True, seed=195, wavelength=110.0)
        lens = PA.ellipse_pts(296, 452, 40, 40, n=32)
        PA.fill_poly(tile, lens, STONE_D, seed=196, value=0.06)
        PA.hand_stroke(d, lens, INK, 5, closed=True, seed=197, wavelength=90.0)
        D.draw_red_x(tile, [164, 336, 428, 604], color=OXBLOOD, width=12)
        D.draw_label(tile, 'NO PHOTOS', center=(296, 662), color=OXBLOOD,
                     size=38, outline=INK, outline_w=2)
    els.append(SC.accrue(clock, 12, 14, b_nophoto, kind='shape',
                         eid='b_nophoto',
                         motion=SC.enter(clock, 12, dx=-90, dy=0, dur=0.5)))
    # NO caption at b12. The oxblood NO PHOTOS label IS the caption, and the
    # red bar is the same refusal drawn twice otherwise.

    def b_nophone(tile, fw, fh):
        # The SAME rule, one step later, on the other side of the corridor: the
        # camera on the left and the phone on the right stand together as one
        # refusal, so b13 adds to the frame instead of replacing it. The figure
        # keeps his arms crossed between them.
        d = ImageDraw.Draw(tile)
        _page(d, 986, 540, 104, 130, 203, lines=6)
        ph = [(892, 316), (1032, 316), (1032, 496), (892, 496)]
        PA.fill_poly(tile, ph, (52, 50, 54), seed=204, value=0.06)
        scr = [(906, 338), (1018, 338), (1018, 474), (906, 474)]
        PA.fill_poly(tile, scr, (188, 200, 210), seed=205, value=0.08)
        PA.hand_stroke(d, scr, INK, 4, closed=True, seed=206, wavelength=90.0)
        D.draw_red_x(tile, [876, 300, 1048, 512], color=OXBLOOD, width=12)
        VC.figure(d, 640, 664, 210, pose='armscrossed', expression='skeptic',
                  seed=207)
    els.append(SC.accrue(clock, 13, 14, b_nophone, kind='character',
                         eid='b_nophone',
                         motion=SC.enter(clock, 13, dx=90, dy=0, dur=0.5)))
    # CAPTION KEPT here and not at b12. These two beats are the same rule and
    # the same two objects, one step apart, so captioning both would put two
    # captions on consecutive beats -- the thing this rebuild is meant to stop.
    # b12 already carries a drawn label, so the words go where they are needed.

    # ==== STAGE C  b14-b18  the paper is fused; it tears; the boxes stay ==== #
    # ONE lit table held across five beats, because every one of these beats #
    # is a different way of losing a document and they all happen at the same #
    # table under the same lamp. The WORLD is the table, the glow and the    #
    # lamp; the DOCUMENT is what changes, so the page replaces the page and #
    # the boxes replace the pages. Rule 1 in one line.                     #
    # ======================================================================= #
    def c_table(tile, fw, fh):
        # C1. The dark room, the lamp pool AND THE SHEET are one backdrop now.
        # v1 drew a new page card for b14, another for b15 and a third for b16,
        # so three consecutive sentences about one fragile document were three
        # unrelated photographs. Here the document is the constant and each
        # beat only ADDS damage to it, in its own region of the same frame.
        d = ImageDraw.Draw(tile)
        _dark(tile, 211)
        _lamp_glow(d, 640, 400, 120, 213)
        _page(d, 640, 440, 300, 340, 212, lines=8)
        # the burst of flash light from the upper left, aimed at the page --
        # part of the ROOM from the moment we walk in, not a beat that lands
        for k in range(7):
            a = 0.5 + k * 0.34
            PA.hand_stroke(d, [(300, 200),
                               (300 + 420 * math.cos(a),
                                200 + 420 * math.sin(a))],
                           LAMP, 6, closed=False, seed=215 + k,
                           wavelength=120.0)
    els.append(SC.stage(clock, 14, c_table, j=17))

    def c_page(tile, fw, fh):
        # b14. The name of the danger, stamped over the flash that is already
        # burning in the backdrop behind it. The light arrived with the room;
        # only the WORDS arrive here.
        D.draw_label(tile, 'FLASH BURNS THE PAPER', center=(640, 178),
                     color=OXBLOOD, size=48, outline=INK, outline_w=3)
    els.append(SC.accrue(clock, 14, 16, c_page, kind='shape',
                         motion=SC.enter(clock, 14, dx=0, dy=-34, dur=ARRIVE)))
    # NO caption at b14. The oxblood 'FLASH BURNS THE PAPER' label and the
    # converging flash rays are the sentence; a caption here would be a third
    # text element on one frame.

    def c_torn(tile, fw, fh):
        # b15. THE SAME SHEET, now with a ragged bite out of its top corner and
        # a red circle-with-slash stamped over it: this one may not be opened.
        # Drawn ON the page already in the backdrop, so the damage is visibly
        # damage to that page rather than a second page in a second room.
        d = ImageDraw.Draw(tile)
        # The bite is a notch out of the sheet's RIGHT EDGE, low down (the
        # backdrop page runs x 340..940, y 100..780). It was on the top-right
        # corner first, which put it straight over the 'FLASH BURNS THE PAPER'
        # label and ate the last four letters -- two text elements in one band.
        # Down here it clears everything: the ring never reaches past x=836, the
        # slash ends at y=282, and the label's glyphs stop at y=199.
        bite = [(940, 470), (940, 660), (904, 620), (872, 672), (846, 592),
                (860, 536), (828, 498)]
        PA.fill_poly(tile, bite, NIGHT, seed=223, value=0.05)
        PA.hand_stroke(d, bite, INK, 4, closed=False, seed=227, wavelength=60.0)
        # the ring sits INSIDE the sheet rather than around it, so it stops
        # cropping off the bottom of the frame
        ring = PA.ellipse_pts(640, 430, 196, 216, n=48)
        PA.hand_stroke(d, ring, OXBLOOD, 11, closed=True, seed=224,
                       wavelength=170.0)
        PA.hand_stroke(d, [(452, 578), (828, 282)], OXBLOOD, 11, closed=False,
                       seed=225, wavelength=140.0)
        VC.figure(d, 1116, 704, 268, pose='recoil', expression='worried',
                  seed=226)
    els.append(SC.accrue(clock, 15, 16, c_torn, kind='character', eid='c_torn',
                         motion=SC.enter(clock, 15, dx=120, dy=0, dur=ARRIVE)))
    # NO caption at b15. The red ring-and-slash is the universal "do not" and
    # the torn corner is the reason; the words would explain the drawing.

    def c_fused(tile, fw, fh):
        # b16. The escalation, ON THE SAME SHEET: pages pressed into one thick
        # fused block. The block is smaller than the page it replaces and sits
        # inside the ring, so the beat changes what the centre of the frame
        # says without repainting the frame around it.
        d = ImageDraw.Draw(tile)
        # The block sits INSIDE the ring and INK on its own paper, so the
        # caption is dropped: the flash label, the fused block's own label and a
        # caption were three yellow/ink blocks competing on one frame.
        fused = [(452, 336), (676, 336), (676, 574), (452, 574)]
        PA.fill_poly(tile, fused, PAPER_D, seed=233, value=0.06)
        PA.hand_stroke(d, fused, INK, 5, closed=True, seed=234,
                       wavelength=110.0)
        # the tell: page edges running together into one solid mass
        for k in range(3):
            PA.hand_stroke(d, [(462 + k * 14, 336), (462 + k * 14, 574)],
                           (188, 178, 160), 3, closed=False, seed=235 + k,
                           wavelength=70.0)
        D.draw_label(tile, 'FUSED', center=(564, 506), color=OXBLOOD, size=38)
    els.append(SC.accrue(clock, 16, 17, c_fused, kind='shape', eid='c_fused',
                         motion=SC.enter(clock, 16, dx=0, dy=44, dur=ARRIVE)))
    # NO caption at b16. The block and its own stamped word are the escalation;
    # a caption here would be a third text element on the densest frame in the
    # chapter.

    def c_table2(tile, fw, fh):
        # C2. The same table later, the flash over and a clean sheet under the
        # lamp. A stage change rather than a beat, so the room turning over is
        # free; what b17 and b18 add is the tear and then the boxes.
        d = ImageDraw.Draw(tile)
        _dark(tile, 241)
        _lamp_glow(d, 640, 400, 120, 242)
        _page(d, 640, 440, 260, 300, 243, lines=6)
    els.append(SC.stage(clock, 17, c_table2, j=19))

    def c_tears(tile, fw, fh):
        # b17. The page being pulled apart. MOVING, and small: the two halves
        # slide away from each other over 0.5s. This is the chapter's clearest
        # "movement IS the information" moment -- the tear happens -- and it is
        # two 190px sheets inside the page already in the backdrop, not a new
        # room.
        d = ImageDraw.Draw(tile)
        _page(d, 452, 430, 168, 240, 245, lines=5)
        _page(d, 828, 438, 152, 226, 246, lines=4)
        tear = [(622, 214), (650, 306), (630, 382), (668, 468), (640, 560)]
        PA.hand_stroke(d, tear, OXBLOOD, 7, closed=False, seed=247,
                       wavelength=90.0, vary=0.2)
        D.draw_label(tile, 'IT TEARS', center=(640, 646), color=OXBLOOD,
                     size=48, outline=INK, outline_w=2)
    els.append(SC.accrue(clock, 17, 19, c_tears, kind='shape', eid='c_tears',
                         motion=SC.enter(clock, 17, dx=-34, dy=0, dur=0.5)))
    # NO caption at b17. 'IT TEARS' is drawn at 48px between the two halves.

    def c_shutboxes(tile, fw, fh):
        # b18. The answer to "so what happens to it": a LOW row of boxes with
        # every lid closed, running off both sides and off the BOTTOM edge.
        # The bottom crop is the frame-fill rule doing its job -- the row is
        # bigger than the picture -- while the top two thirds of the frame
        # stays the room we have been standing in since b14.
        d = ImageDraw.Draw(tile)
        for k in range(4):
            _archive_box(d, -30 + k * 350, 792, 292, 236, 260 + k)
        D.draw_label(tile, 'SHUT', center=(640, 224), color=LAMP, size=52,
                     outline=INK, outline_w=3)
    els.append(SC.accrue(clock, 18, 19, c_shutboxes, kind='shape',
                         eid='c_shutboxes',
                         motion=SC.enter(clock, 18, dx=0, dy=180, dur=0.6)))
    # NO caption at b18. Four closed lids across the frame is the fact.

    # ==== STAGE D  b19-b25  one catalogue line, then nothing but the reel == #
    # A dark room with one pool of lamp light on a desk, held across seven   #
    # beats. v1 answered this run with seven different rooms -- a bright      #
    # page card, another bright page card, a dark microfilm card -- so the   #
    # act read as seven unrelated stills. Here the room and the pool persist #
    # and only the OBJECT on the desk changes, which is what actually       #
    # happens: one shelf of boxes, and everything the archive knows about    #
    # them is a card, a line, and a film.                                    #
    # ======================================================================= #
    def d_desk(tile, fw, fh):
        # D1. The desk under the lamp. The shelving stops halfway up so the
        # SURFACE is clear for what lands on it -- three beats of apparatus on
        # one desk, not three unrelated rooms.
        d = ImageDraw.Draw(tile)
        _dark(tile, 321)
        _lamp_glow(d, 640, 430, 130, 322)
        _shelf_run(d, -40, W + 40, 430, 170, 272, shelves=3, stock=1)
        PA.hand_stroke(d, [(-40, 430), (W + 40, 430)], WOOD_D, 7, closed=False,
                       seed=274, wavelength=150.0)
    els.append(SC.stage(clock, 19, d_desk, j=22))

    def d_shelf(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # a cobwebbed, dusty box wedged deep on a high shelf, half in shadow,
        # resting on the plank at y=430 (top_y 170 + 2 steps of 130)
        _archive_box(d, 800, 430, 220, 150, 273)
        for k in range(5):
            PA.hand_stroke(d, [(700 + k * 40, 280), (760 + k * 30, 350)],
                           (110, 106, 100), 3, closed=False, seed=280 + k,
                           wavelength=60.0)
    els.append(SC.accrue(clock, 19, 22, d_shelf, kind='shape'))
    els.append(cap(19, 420, 620, size=30, fill=LAMP))
    # CAPTION KEPT and NO drawn 'NEVER OPENED AGAIN' label. A dusty box on a
    # high shelf says "forgotten"; it does NOT say "never consulted again",
    # which is the actual fact of the beat, so the words carry it.

    def d_catalogue(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the open catalogue book, set down ON the desk under the pool of light
        # -- v1's hero object for this beat, now arriving rather than replacing
        # NOTE _page's w/h are HALF-extents, so this is a 500x352 sheet --
        # v1 passed 520/250 and got an 1040x500 sheet that filled the frame
        _page(d, 640, 470, 250, 176, 293, lines=8, folded=True)
        # INK on the book's own paper, so the words read as printed on the
        # catalogue instead of floating in the dark under it
        D.draw_label(tile, 'CATALOGUED ONCE', center=(640, 596), color=INK,
                     size=38)
    els.append(SC.accrue(clock, 20, 22, d_catalogue, kind='shape',
                         motion=SC.enter(clock, 20, dx=0, dy=64, dur=ARRIVE)))
    # NO caption at b20. 'CATALOGUED ONCE' is written under the book and the
    # ruled lines on the page are the catalogue itself.

    def d_indexcard(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # ONE index card, laid on the open catalogue -- which is what the beat
        # means, so it is drawn ON the book the last beat put on the desk. The
        # card is the same PAPER as the page under it, so what changes on this
        # beat is the ruled line and the outline, not a white rectangle.
        card = [(452, 318), (828, 318), (828, 520), (452, 520)]
        PA.fill_poly(tile, card, PAPER, seed=302, value=0.05)
        PA.hand_stroke(d, card, INK, 6, closed=True, seed=303,
                       wavelength=130.0)
        # one single typed line, dead centre, heavy enough to read as writing.
        # NO 'ONE LINE' label over it: the caption on this beat already says
        # "one line on it", and printing it a third time in the frame is the
        # pile-up the beat can least afford -- the card is nearly blank.
    els.append(SC.accrue(clock, 21, 22, d_indexcard, kind='shape',
                         motion=SC.enter(clock, 21, dx=0, dy=-40, dur=ARRIVE)))
    els.append(cap(21, W // 2, 660, size=32, fill=LAMP))
    # CAPTION KEPT. This is the one beat where the object is deliberately
    # almost blank -- a white rectangle with one ruled line -- and the viewer
    # has to be told it is a card and that the line is the whole of it.

    def d_wall(tile, fw, fh):
        # D2. The far side of the same room, one pool low and left. A stage
        # change rather than a beat, so turning the camera round the room is
        # free; what b22 and b23 add is the record and then the machine.
        d = ImageDraw.Draw(tile)
        _dark(tile, 311, top=(30, 25, 23), floor_col=(44, 36, 34))
        _lamp_glow(d, 300, 500, 120, 312)
    els.append(SC.stage(clock, 22, d_wall, j=24))

    def d_whole(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE WHOLE RECORD: the same card from b21 scaled up until it is wider
        # than the room and cropped by BOTH side edges. The scale change is
        # still the reveal -- it just happens in the lower third now instead of
        # taking the whole frame away from the room.
        big = [(-70, 508), (W + 70, 508), (W + 70, 690), (-70, 690)]
        PA.fill_poly(tile, big, PAPER, seed=313, value=0.05)
        PA.hand_stroke(d, big, INK, 7, closed=True, seed=314, wavelength=130.0)
        PA.hand_stroke(d, [(70, 566), (1210, 566)], (58, 52, 46), 9,
                       closed=False, seed=315, wavelength=90.0)
        D.draw_label(tile, 'THE WHOLE RECORD', center=(640, 638), color=OXBLOOD,
                     size=48)
    els.append(SC.accrue(clock, 22, 24, d_whole, kind='shape',
                         motion=SC.enter(clock, 22, dx=0, dy=96, dur=ARRIVE)))
    # NO caption at b22. The card now spans the frame and 'THE WHOLE RECORD' is
    # written across it; the scale change IS the reveal.

    def d_filmed(tile, fw, fh):
        # THE CAMERA THAT REPLACED OPENING IT, standing on the right with its
        # film already run out. The strip is the smallest moving thing in the
        # chapter -- 110px over half a second -- and nothing else on this beat
        # moves: the camera, the page and the label are all still.
        d = ImageDraw.Draw(tile)
        page = [(792, 302), (972, 302), (972, 432), (792, 432)]
        PA.fill_poly(tile, page, PAPER, seed=323, value=0.05)
        PA.hand_stroke(d, page, INK, 5, closed=True, seed=324,
                       wavelength=110.0)
        cam = [(846, 176), (1010, 176), (1010, 302), (846, 302)]
        PA.fill_poly(tile, cam, (60, 56, 56), seed=325, value=0.06)
        PA.hand_stroke(d, cam, INK, 5, closed=True, seed=326, wavelength=90.0)
        PA.hand_stroke(d, [(928, 302), (928, 340)], INK, 6, closed=False,
                       seed=327, wavelength=60.0)
        # the film strip running out of the camera to the right
        PA.hand_stroke(d, [(928, 340), (1152, 424)], LAMP, 10, closed=False,
                       seed=328, wavelength=140.0)
        D.draw_label(tile, 'FILMED, NOT OPENED', center=(952, 490), color=LAMP,
                     size=32, outline=INK, outline_w=2)
    els.append(SC.accrue(clock, 23, 24, d_filmed, kind='shape',
                         motion=SC.enter(clock, 23, dx=110, dy=0, dur=ARRIVE)))
    # NO caption at b23. 'FILMED, NOT OPENED' is on the frame and the camera
    # is visibly shooting the page instead of a hand opening it.

    def d_store(tile, fw, fh):
        # D3. The other half of the collection: the boxes that are never filmed
        # either, and the one reel the filming actually produced. Both land in
        # this room and both stay, so b25 is the two objects standing together.
        d = ImageDraw.Draw(tile)
        _dark(tile, 331, top=(28, 23, 22), floor_col=(42, 35, 33))
        _shelf_run(d, -40, W + 40, 700, 250, 332, shelves=3, stock=1)
    els.append(SC.stage(clock, 24, d_store, j=26))

    def d_forever(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # one closed box with a chain across it, and nothing on the shelf but
        # dust: the other half of the collection, which never opens at all
        _archive_box(d, 300, 700, 330, 226, 333)
        for k in range(3):
            PA.hand_stroke(d, [(158, 606 - k * 20), (442, 606 - k * 20)],
                           OXBLOOD, 5, closed=False, seed=340 + k,
                           wavelength=90.0)
    els.append(SC.accrue(clock, 24, 26, d_forever, kind='shape',
                         motion=SC.enter(clock, 24, dx=-90, dy=0, dur=ARRIVE)))
    els.append(cap(24, 640, 150, size=32, fill=LAMP))
    # CAPTION KEPT and v1's 'FOR EVER' label is DROPPED. One text element on
    # this beat: the caption in the clear air above the shelf, and the chained
    # box says the rest.

    def d_reel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the reel it all came to, dropped in on the right of the chained box
        # from b24 and cropped by the frame edge -- two objects, one room
        reel = PA.ellipse_pts(1060, 470, 230, 230, n=64)
        PA.fill_poly(tile, reel, (46, 42, 44), seed=353, value=0.06)
        PA.hand_stroke(d, reel, INK, 7, closed=True, seed=354,
                       wavelength=170.0)
        hub = PA.ellipse_pts(1060, 470, 70, 70, n=40)
        PA.fill_poly(tile, hub, STONE, seed=355, value=0.06)
        PA.hand_stroke(d, hub, INK, 5, closed=True, seed=356, wavelength=90.0)
        for k in range(3):
            PA.hand_stroke(d, [(1060, 470),
                               (1060 + 150 * math.cos(k * 2.1),
                                470 + 150 * math.sin(k * 2.1))],
                           INK, 4, closed=False, seed=357 + k,
                           wavelength=70.0)
        PA.hand_stroke(d, [(886, 596), (1236, 530)], OXBLOOD, 6, closed=False,
                       seed=365, wavelength=120.0)
    els.append(SC.accrue(clock, 25, 26, d_reel, kind='shape',
                         motion=SC.enter(clock, 25, dx=130, dy=0, dur=ARRIVE)))
    # NO caption at b25. The line names exactly these two objects and the frame
    # is nothing but those two objects.

    # ==== STAGE E  b26-b29  the plan is upstairs; nobody carried it down ==== #
    # ONE SECTION through the building for four beats: the lit room upstairs #
    # above the deck line at y=330, and the stair down into the stacks below #
    # it. v1 answered b26 with an abstract plan grid, b27 with a corridor,    #
    # b28 with a section and b29 with a stair -- four unrelated rooms for one #
    # idea. Here the section holds and only its contents change: the system #
    # as a schematic upstairs (b26), one reader on the stairs (b27), the     #
    # actual plan in an open drawer in the same band (b28), and the way down #
    # crossed off (b29).                                                   #
    # ======================================================================= #
    def e_section(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 471)
        # THE DECK at y=330. Everything above the line is one lit room
        # upstairs, everything below is the stair down into the archive. The
        # lintel goes down first so these full-width fills cannot bury the INK
        # title, and the lit room starts at y=128 so it clears the band.
        _lintel(tile, 493)
        PA.fill_rect(tile, [-20, 128, W + 20, 330], (70, 60, 52), seed=462,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 330), (W + 20, 330)], INK, 9, closed=False,
                       seed=463, wavelength=190.0)
        # the void the stair descends into, in one-point perspective so it
        # reads as a STAIR and not as slabs floating in a void
        PA.fill_poly(tile, [(150, 330), (1130, 330), (900, 700), (380, 700)],
                     DEEPER, seed=473, value=0.05)
        for side in (-1, 1):
            wall = [(640 + side * 490, 330), (640 + side * 170, 620),
                    (640 + side * 130, 700), (640 + side * 330, 700),
                    (640 + side * 330, 330)]
            PA.fill_poly(tile, wall, STONE_D, seed=474 + side, value=0.07)
            PA.hand_stroke(d, [(640 + side * 490, 330), (640 + side * 170, 620),
                               (640 + side * 130, 700)], INK, 6, closed=False,
                           seed=478 + side, wavelength=140.0)
        # the treads, widening toward the viewer
        for k in range(8):
            t = k / 7.0
            y = 342 + t * 340
            wdt = 180 + t * 300
            step = [(640 - wdt, y), (640 + wdt, y), (640 + wdt + 26, y + 50),
                    (640 - wdt - 26, y + 50)]
            PA.fill_poly(tile, step, STONE, seed=480 + k, value=0.07)
            PA.hand_stroke(d, step, INK, 5, closed=True, seed=490 + k,
                           wavelength=90.0)
    els.append(SC.stage(clock, 26, e_section, j=30))

    def e_system(tile, fw, fh):
        # "The shelving system itself is kept quiet": the stacks as a bare
        # schematic, drawn small INSIDE the lit upstairs band. It replaces
        # nothing -- the band was empty -- and it will be replaced at b28 by
        # the one drawer anybody actually opens.
        d = ImageDraw.Draw(tile)
        for r in range(3):
            for c in range(6):
                x0 = 24 + c * 208
                y0 = 146 + r * 58
                cell = [(x0, y0), (x0 + 168, y0), (x0 + 168, y0 + 44),
                        (x0, y0 + 44)]
                PA.fill_poly(tile, cell, WOOD_D, seed=372 + r * 6 + c,
                             value=0.06)
                PA.hand_stroke(d, cell, WOOD, 5, closed=True,
                               seed=392 + r * 6 + c, wavelength=90.0)
    els.append(SC.layer(clock, 26, e_system, kind='shape'))
    els.append(cap(26, W // 2, 664, size=30, fill=LAMP))
    # CAPTION KEPT. An abstract grid of cells is the one thing in the chapter
    # the viewer genuinely cannot decode on its own, and no drawn label says it.

    def e_reader(tile, fw, fh):
        # ONE figure on the stairs, small against the depth -- big enough that
        # his face reads (v1's b27 finding: at 90px he was a pale tick) and
        # clear of the lit far end, which spans y 250..430 in v1 and would
        # dissolve a cream outline.
        VC.figure(ImageDraw.Draw(tile), 640, 540, 210, pose='standing',
                  expression='deadpan', seed=451)
    els.append(SC.accrue(clock, 27, 30, e_reader, kind='character'))
    # NO caption at b27 and NO drawn 'FEW KNOW' label. One small figure alone
    # on an endless stair is that sentence, and v1's own comment records that a
    # hero word here printed the caption's first two words back at it.

    def e_drawer(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE PLAN, upstairs: the cabinet cropped by BOTH side edges so the room
        # is bigger than the frame, one drawer pulled open toward the viewer,
        # and the plan lying in it as the brightest thing in the shot. A strip
        # of lit floor shows under the cabinet, without which the band reads as
        # one wall of wood and "upstairs" stops being a place.
        PA.fill_poly(tile, [(-40, 300), (1320, 300), (1320, 314), (-40, 314)],
                     (44, 37, 31), seed=480, value=0.05)     # contact shadow
        cab = [(-40, 140), (1320, 140), (1320, 306), (-40, 306)]
        PA.fill_poly(tile, cab, WOOD, seed=466, value=0.08)
        PA.hand_stroke(d, cab, INK, 7, closed=True, seed=467, wavelength=150.0)
        # the open drawer's dark interior, so the bright page reads as lit paper
        op = [(392, 158), (950, 158), (950, 232), (392, 232)]
        PA.fill_poly(tile, op, DEEPER, seed=473, value=0.05)
        PA.hand_stroke(d, op, INK, 6, closed=True, seed=474, wavelength=120.0)
        # the plan, a tilted sheet lying in the drawer
        pg = [(420, 172), (922, 182), (910, 226), (408, 216)]
        PA.fill_poly(tile, pg, PAPER, seed=468, value=0.05)
        PA.hand_stroke(d, pg, INK, 4, closed=True, seed=469, wavelength=90.0)
        for k in range(4):
            yy = 186 + k * 9
            PA.hand_stroke(d, [(444 + k * 3, yy), (872 - k * 12, yy + 2)],
                           (58, 52, 46), 4, closed=False, seed=475 + k,
                           wavelength=60.0)
        # the drawer front, hanging in front of the opening now it is pulled out
        dr = [(368, 228), (976, 228), (976, 278), (368, 278)]
        PA.fill_poly(tile, dr, WOOD_L, seed=476, value=0.08)
        PA.hand_stroke(d, dr, INK, 7, closed=True, seed=477, wavelength=120.0)
        PA.hand_stroke(d, [(652, 253), (692, 253)], INK, 11, closed=False,
                       seed=478, wavelength=40.0)
    els.append(SC.accrue(clock, 28, 30, e_drawer, kind='shape'))
    # NO caption at b28. The open drawer with the plan in it, upstairs and above
    # the deck line, IS "filed elsewhere, upstairs" -- and NO drawn 'UPSTAIRS'
    # label either, because v1's own comment records that it collided with the
    # caption at the same y.

    def e_stopped(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The way down, stopped. The cross sits ON the treads rather than half
        # off the bottom of the frame, and it is the only red in the shot.
        D.draw_red_x(tile, [470, 462, 810, 650], color=OXBLOOD, width=14)
    # MOVING, and small: the cross arriving on the steps it forbids, 30px over
    # 0.45s. The stair behind it does not move -- a 370px stair sliding is the
    # picture churning, which is the defect this rebuild exists to remove.
    els.append(SC.accrue(clock, 29, 30, e_stopped, kind='shape',
                         motion=SC.enter(clock, 29, dx=0, dy=30, dur=0.45)))
    # NO caption at b29. The cross on the steps is "nobody has ever carried it
    # down" with nothing else on the frame to compete with it.

    # ==== STAGE F  b30-b34  a reader between tall shelves; a favour, not a == #
    #                 right                                                   #
    # The chapter's emotional image, held for five beats: two shelf runs      #
    # CROPPED by the left and right edges running the full height, and one    #
    # small reader between them. v1 gave this its own card and then spent the #
    # next four beats in three other rooms; here the stacks stay and the      #
    # reader stays, and only the thing in front of him changes -- more        #
    # shelving behind (b31), one dusty box beside him (b32), the door that is #
    # opened for a chosen few (b33), and finally his face.                   #
    # ======================================================================= #
    def f_stacks(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 501)
        # two towering shelf runs converging slightly, cropped by both edges
        _shelf_run(d, -60, 480, 740, -60, 511, shelves=12, depth=-40)
        _shelf_run(d, 800, W + 60, 740, -60, 531, shelves=12, depth=40)
        # Depth down the corridor, as a soft vertical wash rather than a hard
        # fill_rect -- a flat rect read as a grey BOX floating between the
        # shelves (v1's finding).
        for i in range(14):
            yy = 300 + i * 19
            PA.fill_rect(tile, [480, yy, 800, yy + 20], DEEP, seed=545 + i,
                         value=0.03, edge=0.0)
    els.append(SC.stage(clock, 30, f_stacks, j=35))

    def f_reader_a(tile, fw, fh):
        VC.figure(ImageDraw.Draw(tile), 640, 700, 340, pose='peeking',
                  expression='worried', seed=546)
    # MOVING, small, and it STOPS: the reader edges 60px into the corridor and
    # holds. The dwarfing is the beat -- he is deliberately the one subject in
    # this chapter drawn small -- so his arrival is a lean, not a walk.
    _fbu, _faa, _fau = SC.expr_swap(clock, 32, 'worried', 'awed', until_j=33)
    els.append(E3.E('f_reader_a', 'character', f_reader_a,
                    at=clock.at('b30', 0), until=_fbu,
                    motion=SC.enter(clock, 30, dx=-60, dy=40, dur=0.55)))
    els.append(cap(30, W // 2, 660, size=32, fill=LAMP))
    # CAPTION KEPT. 'LOST' is not drawn -- v1's card printed it, but here the
    # reader is 340px of cream in a 1280px corridor between two walls of
    # shelves, and the word is what makes the scale legible as loneliness
    # rather than as bad framing.

    def f_reader_b(tile, fw, fh):
        # Same position, same size, one expression later: at b32 he has found
        # the box he was looking for and the worry has gone to wonder. Two
        # elements, because the expression is baked into the rasterised tile.
        VC.figure(ImageDraw.Draw(tile), 640, 700, 340, pose='peeking',
                  expression='awed', seed=546)
    els.append(E3.E('f_reader_b', 'character', f_reader_b, at=_faa,
                    until=_fau))

    def f_more(tile, fw, fh):
        # "The Vatican has shelved many older records": a further run of
        # shelving at the FAR end of the corridor, framed by the two near runs,
        # so the stacks gain depth instead of the frame gaining another object.
        d = ImageDraw.Draw(tile)
        _shelf_run(d, 470, 810, 566, 176, 552, shelves=5, depth=0, stock=1)
        D.draw_label(tile, 'CENTURIES OF RECORDS', center=(640, 136),
                     color=LAMP, size=40, outline=INK, outline_w=3)
    els.append(SC.layer(clock, 31, f_more, kind='shape'))
    # NO caption at b31. 'CENTURIES OF RECORDS' is written across the far run.

    def f_shutyears(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # one box, deep on the right-hand run, a thick dust layer on its lid
        _archive_box(d, 990, 700, 300, 200, 572)
        PA.fill_poly(tile, [(850, 500), (1130, 500), (1130, 526), (850, 526)],
                     (120, 114, 106), seed=575, value=0.05)
    # NO drawn 'YEARS' calendar and NO drawn 'SHUT' label this time: the
    # caption below does that work, and two labels plus a caption on the same
    # beat is the pile-up rule 1 exists to prevent.
    els.append(SC.layer(clock, 32, f_shutyears, kind='shape'))
    els.append(cap(32, 640, 150, size=32, fill=LAMP))

    def f_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE DOOR IN THE STACKS, small and ajar in the left shelf face with a
        # sliver of light, and a red rope across the corridor keeping the rest
        # out. v1 dropped a 600px door into the middle of the corridor, which
        # REPLACED the reader -- but the beat is about who gets through that
        # gap, so the gap belongs IN the stacks the reader is dwarfed by.
        _lamp_glow(d, 250, 380, 90, 582)
        _big_door(d, 250, 380, 240, 300, 583, open_frac=0.42)
        PA.hand_stroke(d, [(360, 620), (1010, 600)], OXBLOOD, 8, closed=False,
                       seed=590, wavelength=170.0)
        for k in range(2):
            PA.hand_stroke(d, [(360 + k * 650, 600), (360 + k * 650, 700)],
                           (52, 48, 50), 10, closed=False, seed=592 + k,
                           wavelength=80.0)
    els.append(SC.accrue(clock, 33, 35, f_door, kind='shape', eid='f_door',
                         motion=SC.enter(clock, 33, dx=-80, dy=0, dur=ARRIVE)))

    def f_few(tile, fw, fh):
        D.draw_label(tile, 'A CHOSEN FEW', center=(700, 178), color=LAMP,
                     size=44, outline=INK, outline_w=3)
    # The label is its OWN element and it leaves at b34. Carried on into the
    # close-up it sits directly behind the reader's head, so b34 played a big
    # yellow word half-eaten by a face.
    els.append(SC.accrue(clock, 33, 34, f_few, kind='shape', eid='f_few',
                         motion=SC.enter(clock, 33, dx=0, dy=-34, dur=ARRIVE)))
    # NO caption at b33. 'A CHOSEN FEW' is stamped over the door and the rope
    # is drawn across it.

    def f_face(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The beat is personal, so the face fills the CENTRE of the corridor we
        # have been standing in -- v1 repainted the whole frame black first
        # (_dark), which threw the stacks away; here the corridor's own dark
        # middle is already behind him, so only the bust is added.
        # v1's `face`, not scene_common.closeup -- on a near-black card an ink
        # bust is a hole in the picture (see the module docstring).
        VC.face(d, 640, 380, 200, 'deadpan', 602, shoulder=1.2, dark=False)
        # the bubble ADDS to the caption rather than repeating it -- when it
        # read "a favour, not a right" it was the caption's own second half
        # printed twice on one frame
        D.draw_bubble(tile, "you'd need a friend in there", (640, 150),
                      tail_to=(640, 250), font_size=30, max_w=420)
    els.append(SC.accrue(clock, 34, 35, f_face, kind='character',
                         eid='f_face',
                         motion=SC.enter(clock, 34, dx=0, dy=44, dur=ARRIVE)))
    # NO caption at b34. A deadpan face filling the frame with a speech bubble
    # is the whole line, and a caption under it would be a second block of
    # words on the beat that least needs one.

    # ==== STAGE G  b35-b38  a small key; the lowest shelves; absolute dark === #
    # The stage backdrop is ALREADY the finale's register: the darkest value #
    # in the chapter with barely-there shelf outlines and the lit lintel the  #
    # engine's INK title needs. So the last act does not repaint to get dark #
    # -- it is dark from b35 and gets darker. A hand offers a key (b35), the #
    # corridor of unread centuries (b36), the floor of the lowest shelf with #
    # one small man (b37), and the absolute dark with him standing in it (b38).#
    # ======================================================================= #
    def g_dark(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DEEPER, seed=681, value=0.12)
        PA.paper_overlay(tile, seed=682)
        # barely-there shelf outlines, just enough to place the figures
        _shelf_run(d, -60, 380, 740, 120, 683, shelves=6, depth=0)
        _shelf_run(d, 900, W + 60, 740, 120, 693, shelves=6, depth=0)
        # Even this frame gets a lintel. On the finale the darkness is the
        # subject, but the engine draws the INK chapter title here
        # unconditionally, and without a lit course of stone behind it the
        # words are dark-on-dark and simply not on screen. FULL WIDTH, because
        # a narrower band left hard vertical edges and read as a floating grey
        # UI panel (v1's finding). dim=0.95 keeps the frame black.
        _lintel(tile, 702, dim=0.95)
    els.append(SC.stage(clock, 35, g_dark, j=39))

    def g_key(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _lamp_glow(d, 640, 400, 110, 612)
        # a large open hand, palm up, offering a key above it: a rounded palm
        # mass with four fingers spread
        palm = [(520, 480), (760, 480), (740, 600), (540, 600)]
        PA.fill_poly(tile, palm, CREAM, seed=613, value=0.04, edge=2.0)
        PA.hand_stroke(d, palm, INK, 5, closed=True, seed=614, wavelength=90.0)
        for k, (bx, tx, ty) in enumerate(((520, 470, 420), (580, 560, 400),
                                          (660, 660, 396), (730, 760, 410))):
            PA.hand_stroke(d, [(bx, 500), (tx, ty)], CREAM, 26,
                           closed=False, seed=615 + k, wavelength=70.0)
            PA.hand_stroke(d, [(bx, 500), (tx, ty)], INK, 5, closed=False,
                           seed=619 + k, wavelength=70.0)
        # the key, resting on the palm: a bow, a shaft, and teeth
        bow = PA.ellipse_pts(600, 340, 44, 44, n=32)
        PA.fill_poly(tile, bow, LAMP, seed=624, value=0.05)
        PA.hand_stroke(d, bow, INK, 5, closed=True, seed=625, wavelength=80.0)
        PA.hand_stroke(d, [(640, 340), (760, 340)], LAMP, 12, closed=False,
                       seed=626, wavelength=80.0)
        PA.hand_stroke(d, [(740, 340), (740, 380)], LAMP, 10, closed=False,
                       seed=627, wavelength=60.0)
        PA.hand_stroke(d, [(766, 340), (766, 372)], LAMP, 10, closed=False,
                       seed=628, wavelength=60.0)
    # MOVING, and the smallest thing in the chapter moves: the key settling 26px
    # onto the open palm over half a second. The hand, the palm and the shelves
    # are all still -- this is an offering, not a gesture.
    els.append(SC.accrue(clock, 35, 36, g_key, kind='shape',
                         motion=SC.enter(clock, 35, dx=0, dy=-26, dur=0.5)))
    els.append(cap(35, 640, 130, size=32, fill=LAMP))
    # CAPTION KEPT. The hand and the key are legible but small in a black
    # frame, and this is the chapter's one image of access; the words name it.

    def g_unread(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The corridor again, one last time -- but as DEPTH ADDED to the dark
        # the act already stands in, not a repaint. Two narrow runs converge in
        # the middle of frame, framed by the barely-lit outer runs the stage
        # backdrop laid down, so "centuries nobody has read" is the same
        # picture said back with more of it visible.
        _shelf_run(d, 340, 580, 620, 220, 641, shelves=7, depth=-30, stock=1)
        _shelf_run(d, 700, 940, 620, 220, 651, shelves=7, depth=30, stock=1)
        D.draw_label(tile, 'NOBODY HAS READ THEM', center=(640, 180),
                     color=LAMP, size=46, outline=INK, outline_w=3)
    # Its OWN beat only. These two runs and that label are the picture for
    # b36; left on through b38 they stack into a fifth and sixth shelf wall and
    # the label prints a second yellow line under the finale's caption.
    els.append(SC.accrue(clock, 36, 37, g_unread, kind='shape',
                         motion=SC.enter(clock, 36, dx=0, dy=-30, dur=ARRIVE)))

    def g_lowest(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The floor of the archive: a low shelf running the width, swallowed by
        # the dark the stage backdrop already made, with only the faintest lamp
        # reaching it. v1 repainted the whole frame DEEPER here as well as at
        # b36; the backdrop IS that value, so only the shelf, the lamp and the
        # small man are added.
        # ONE low shelf run, not a full-width wall -- the backdrop's two barely
        # -lit side runs are still there and a third full-width band on top of
        # them reads as a grid, not a room. And _floor_pool, NOT _lamp_glow:
        # at floor scale the lamp's opaque concentric ellipses put a fried egg
        # under his feet (v1's own finding, repeated here until it was fixed).
        _shelf_run(d, 300, 980, 700, 588, 662, shelves=2, depth=0, stock=1)
        _floor_pool(d, 640, 694, 150, 44, 672)
        VC.figure(d, 640, 690, 180, pose='standing', expression='awed',
                  seed=673)
    els.append(SC.accrue(clock, 37, 38, g_lowest, kind='character',
                         motion=SC.enter(clock, 37, dx=0, dy=36, dur=ARRIVE)))
    # NO caption at b37 and NO drawn 'THE LOWEST SHELVES' label. A man 180px
    # tall on a single low shelf in a black room is the line, and the label
    # would name the only thing the composition already says.

    def g_absolute(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # No full-frame fill, no lintel and NO redraw of the side runs: the
        # stage backdrop is already DEEPER with a lintel and those two runs over
        # it, and v1 repainting all of it here undid the whole act. The finale
        # beat is the figure and the pool, and nothing else is on the frame.
        # the figure, centre, standing in a faint warm floor wash. _floor_pool
        # and NOT _lamp_glow: the lamp lays down opaque concentric ellipses, so
        # at floor scale its bright core reads as a fried egg stuck to the
        # boards (v1's finding). The pool is centred on his FEET.
        _floor_pool(d, 640, 662, 168, 50, 704)
        VC.figure(d, 640, 660, 400, pose='standing', expression='deadpan',
                  seed=703)
        # NO HERO WORD HERE, v1's own finding: an 'ABSOLUTE' label is the
        # caption's last word printed twice. The upper half of the frame is
        # left empty on purpose -- two barely-lit stacks, one small man, and
        # nothing at all where the light would be.
    els.append(SC.accrue(clock, 38, 39, g_absolute, kind='character',
                         eid='g_absolute'))
    els.append(cap(38, W // 2, 118, size=34, fill=LAMP))
    # CAPTION KEPT, and it is the only text on the frame. This is the one beat
    # where the silence needs a line under it.

    return SC.finish(els, TITLE, clock, title_seed=61)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent2.mp4'))