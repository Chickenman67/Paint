"""area51_2_scene -- the PERSISTENT-STAGE rebuild of chapter 2 (Area 51).

WHY THIS FILE EXISTS. area51_scene.py (v1) is built on "one card per beat, each
card paints its own whole frame": its local `card(i, j, draw, ...)` helper paints
a complete 1280x720 image -- playa, fence, labels, character -- live only for
beats i..j-1, so nothing survives into the next sentence. The result is a new
full-frame image every ~2.3s and a caption on all 34 beats (100% text density).

THE MODEL HERE. Seven PERSISTENT STAGES, grouped on the narration's own acts
(boundaries fixed in work3/plans/STAGE_PLANS.md):

    A  b01-b04  a place with no name; Fifty-One; the most secret base
    B  b05-b09  dry lake bed, Nevada; the Groom Lake sign; the arrest warning
    C  b10-b14  the fence runs for miles; a second fence; cameras; the base is
                smaller than its fence
    D  b15-b19  no aircraft may fly; red dashed line; pilots noticed first
    E  b20-b25  Roswell; Hangar 18; that hangar is not officially there
    F  b26-b30  Nellis runs the site; the budget is not public; Bob Lazar
    G  b31-b34  2020 FBI files; the fence is still standing; finale

The frame repaints seven times in ~80s instead of thirty-four, and inside a
stage the art ACCUMULATES: a layer that arrives stays until the stage turns
over (SC.accrue), so the viewer gets one recognisable place to look while the
next thing is added to it.

TWO RULES THAT TOOK THE PILOT TWO ROUNDS TO LEARN -- both measured, both kept.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Accruing everything is also wrong: the
   pilot left every layer live to stage end and got text pile-ups and objects
   stacked on objects. Scenery accumulates; anything carrying text, and any two
   elements that share the same region of the frame, REPLACE (SC.layer).
   area51 is desert + fence + signs, so the fence and the lake bed ACCRUE, while
   the Groom Lake sign, the arrest warning and the DOES NOT EXIST stamp REPLACE
   one another -- three text-bearing objects that would otherwise land on top of
   each other in the middle of one stage.

   The same rule decides the CAPTIONS. A caption is dropped whenever the frame
   already prints the same words in a legible place: the Groom Lake sign is
   DRAWN reading GROOM LAKE, so b07 gets no caption; the arrest board is DRAWN
   reading RESTRICTED AREA / VIOLATORS WILL BE ARRESTED, so b08 gets none; the
   budget sheet is DRAWN with NOT PUBLIC on it, so b26 gets none. Where the art
   only shows a thing and not the fact, the caption stays -- and where a drawn
   object could have carried a word, the word was removed from the art and given
   to the caption instead (the hangar wall paints a bare '18' and the CAPTION
   says "Hangar 18"; the file stack is stamped RELEASED and the CAPTION says
   "In 2020, the FBI released its files"). Thirteen captions on 34 beats (38%),
   never two in a row.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces motion at a rate the
   reference does not have and every moving frame trips the picture-change
   counter -- which is worse than the churn this rebuild exists to remove. The
   reference is 83% still frames. So eleven arrivals MOVE, briefly (0.45-0.55s),
   and all of them are small subjects: the presenter stepping in, a sign, a
   camera head, the red dashed ceiling line drawing on, a jet, a single halo
   light, the hangar door leaf, the file stack. Nothing drifts. The fence line
   and the backdrops are static -- a 1300px-wide fence sliding across the frame
   is exactly the large continuous motion that reads as image churn.

THE CHARACTER. The presenter carries three stages (A, E, G) and changes
expression once inside two of them via SC.expr_swap -- two elements at the same
position, the first ending exactly where the second starts.

THE REGISTER SWITCHES. Stages A, B, C and E are the bleached alkali day
register; D and G are the night register and call SC.title_backdrop() first so
the hardcoded-INK scene title can be read over them; F is the warm interior
register. A night stage is not decoration: "pilots reported lights over the dry
lake" (b18) has no honest read on a bleached noon playa, so stage D is night
and the red halo finally carries.

ART. Every primitive, the palette and the layout are reused verbatim from
area51_scene.py -- this file imports it, it does not copy it. Nothing is
imported from pinegap2.

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

import area51_scene as A51     # art primitives + palette, reused not copied

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

# night-register type colour. scene_common already defines this as the only fill
# that reads on a night card; a RED or INK label on NIGHT measures ~1.3:1. It is
# the shared constant, not a new colour.
NIGHT_TYPE = SC.CAPTION_ON_NIGHT

# art primitives, reused
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

# The arrival duration used by every moving element. 0.45-0.55s reads as a
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

    # ===================================================================== #
    # STAGE A  b01-b04  "There is a place with no name.                     #
    #                 It has a number instead.                             #
    #                 Fifty-One.                                           #
    #                 It is the most secret base on Earth."                 #
    # One empty playa held across four beats. The hook IS the emptiness, so #
    # the desert and the mountain rim own the frame and nothing else does. #
    # The fence arrives on b01 and stays -- it is the only thing out here, #
    # which is the point -- and the presenter steps in beside it so four    #
    # seconds of bare backdrop never happens.                               #
    # ===================================================================== #
    def a_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 5)
        _mountain_strip(d, HZ, 6)
    els.append(SC.stage(clock, 1, a_backdrop, j=5))

    def a_fence(tile, fw, fh):
        # ACCRUES. The fence is the world's own object and it is the same
        # fence the chapter ends on, so it stays standing from here to b04.
        _fence(ImageDraw.Draw(tile), -40, 640, W + 40, 260, 7, n_posts=9)
    els.append(SC.accrue(clock, 1, 5, a_fence, kind='shape'))

    def a_presenter_a(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 200, 700, 430, pose='standing',
                    expression='deadpan', seed=16)
    # MOVING (small): he steps in from the left as the chapter opens, so the
    # first frame has an anchor instead of four seconds of empty wire.
    _bu, _aa, _au = SC.expr_swap(clock, 2, 'deadpan', 'skeptic', until_j=5)
    els.append(E3.E('a_presenter_a', 'character', a_presenter_a,
                    at=clock.at('b01', 0), until=_bu,
                    motion=SC.enter(clock, 1, dx=-120, dy=0, dur=ARRIVE)))

    def a_presenter_b(tile, fw, fh):
        # "It has a number instead." -- the brows go up. Same position, so the
        # two elements hand off with no jump (SC.expr_swap).
        SC.fullbody(ImageDraw.Draw(tile), 200, 700, 430, pose='standing',
                    expression='skeptic', seed=16)
    els.append(E3.E('a_presenter_b', 'character', a_presenter_b,
                    at=_aa, until=_au))

    def a_name(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        D.draw_label(tile, 'AREA 51', center=(660, 250), color=INK, size=120)
        D.draw_label(tile, 'THE BASE WITH NO NAME', center=(660, 350),
                     color=RED, size=40, outline=INK, outline_w=2)
    # A LAYER, not an accrue: this is the chapter's one text object and it must
    # not be joined by any other text in the same region. It arrives on b03 on
    # the word "Fifty-One."
    els.append(SC.layer(clock, 3, a_name, j=5, kind='shape', eid='a_name',
                        motion=SC.enter(clock, 3, dy=-40, dur=ARRIVE)))
    # NO caption at b03: the frame is printing "AREA 51" in 120px type. Saying
    # "Fifty-One." underneath it would be the same words twice.
    els.append(cap(1, 640, 170, size=34))
    # NO caption at b02 (adjacent to b01, and the fence-and-number beat is
    # carried by the name arriving at b03).
    els.append(cap(4, 1060, 250, size=30, max_w=440))

    # ===================================================================== #
    # STAGE B  b05-b09  "It sits on a dry lake bed.                         #
    #                 In Nevada, north of Las Vegas.                        #
    #                 The sign out front reads Groom Lake.                  #
    #                 A second sign warns of arrest.                        #
    #                 Nobody will say what is inside."                      #
    # The cracked playa is the stage backdrop -- it IS this beat, so it is   #
    # painted once and held for five beats instead of being repainted on    #
    # every sentence. Then: the locator map, then the Groom Lake sign, then #
    # the arrest warning in the SAME PLACE, then the presenter shrugging.    #
    # ===================================================================== #
    def b_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 23)
        _mountain_strip(d, HZ, 24)
        # polygonal salt-crust cracks on the near ground. These were the
        # SUBJECT at b05 in v1, so they are drawn dark and thick and each row
        # is broken into offset segments so they read as a cracked polygon net.
        # See area51_scene._playa's b05 card for why 3px pale lines failed.
        rows = (HZ + 40, HZ + 110, HZ + 200, HZ + 310, HZ + 440)
        for k, y in enumerate(rows):
            if y > H + 10:
                break
            amp = 8 + k * 4
            seg = []
            x = -40.0
            while x < W + 40:
                seg.append((x, y + amp * math.sin(x * 0.011 + k * 1.7)))
                x += 120
            PA.hand_stroke(d, seg, (176, 172, 162), 5, seed=25 + k,
                           wavelength=110.0)
            for j in range(6):
                x0 = 60 + j * 210 + k * 40
                PA.hand_stroke(d, [(x0, y + amp * math.sin(x0 * 0.011 + k * 1.7)),
                                   (x0 + 34, rows[k + 1] if k + 1 < len(rows)
                                    else y + 90)],
                               (176, 172, 162), 4, seed=40 + k * 8 + j,
                               wavelength=70.0)
    els.append(SC.stage(clock, 5, b_backdrop, j=10))

    def b_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The locator INSET, not a full-frame map card. v1 gave "In Nevada"
        # the whole frame and lost the lake bed it was describing; an inset
        # carries the same information and stays put for the whole stage.
        land = [(922, 128), (1054, 106), (1188, 152), (1216, 244),
                (1136, 300), (1000, 286), (908, 210)]
        PA.fill_poly(tile, land, (208, 190, 146), seed=29, value=0.07)
        PA.hand_stroke(d, land, INK, 6, closed=True, seed=30, wavelength=110.0)
        d.ellipse([1104, 148, 1136, 180], fill=RED)
        PA.hand_stroke(d, [(1120, 184), (1120, 246)], RED, 5, seed=31,
                       wavelength=70.0)
    els.append(SC.accrue(clock, 6, 10, b_map, kind='shape'))
    els.append(cap(6, 460, 210, size=30, max_w=560))
    # NO caption at b05: the cracked alkali under a bleached sky IS "it sits on
    # a dry lake bed". The caption on this beat would only name what the ground
    # already shows. b06 keeps one because the map inset shows WHERE and the
    # words supply the one thing the art does not -- that the state is Nevada.

    def b_groomsign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        sb = [(120, 300), (820, 282), (840, 478), (140, 496)]
        PA.fill_poly(tile, sb, (222, 214, 190), seed=35, value=0.08)
        PA.hand_stroke(d, sb, INK, 7, closed=True, seed=36, wavelength=150.0)
        D.draw_label(tile, 'GROOM LAKE', center=(470, 384), color=INK, size=56)
        PA.hand_stroke(d, [(280, 486), (250, 660)], (128, 118, 100), 16,
                       seed=37, wavelength=90.0)
        PA.hand_stroke(d, [(700, 470), (730, 660)], (128, 118, 100), 16,
                       seed=38, wavelength=90.0)
    els.append(SC.layer(clock, 7, b_groomsign, j=8, kind='shape',
                        eid='b_groomsign',
                        motion=SC.enter(clock, 7, dy=-50, dur=0.5)))
    # NO caption at b07. The sign is DRAWN reading GROOM LAKE in 56px ink --
    # captioning "The sign out front reads Groom Lake." would print the same
    # words twice in the same frame. This is the rule that earns the b07 slot
    # back by REMOVING text, not adding it.

    def b_arrestsign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE SAME BOARD, re-lettered. A second sign ACCRUING on top of the
        # first would put two text-bearing boards in the same 700px of frame
        # and neither would be readable -- this is exactly the pile-up the
        # pilot hit. So the arrest warning REPLACES the Groom Lake sign.
        sb = [(120, 320), (820, 300), (838, 520), (138, 540)]
        PA.fill_poly(tile, sb, (228, 222, 206), seed=40, value=0.07)
        PA.hand_stroke(d, sb, INK, 7, closed=True, seed=41, wavelength=150.0)
        D.draw_label(tile, 'RESTRICTED AREA', center=(470, 384), color=INK,
                     size=42)
        D.draw_label(tile, 'VIOLATORS WILL BE ARRESTED', center=(470, 476),
                     color=RED, size=34, outline=INK, outline_w=2)
        PA.hand_stroke(d, [(250, 534), (230, 670)], (128, 118, 100), 14,
                       seed=42, wavelength=80.0)
        PA.hand_stroke(d, [(720, 514), (750, 670)], (128, 118, 100), 14,
                       seed=43, wavelength=80.0)
    els.append(SC.layer(clock, 8, b_arrestsign, j=9, kind='shape',
                        eid='b_arrestsign'))
    # NO caption at b08 either: the board is printed RESTRICTED AREA /
    # VIOLATORS WILL BE ARRESTED. The words are already on the wall.

    def b_nobody(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 620, 700, 470, pose='shrug', expression='skeptic',
                    seed=47)
        D.draw_bubble(tile, 'no answer', (320, 250), tail_to=(520, 380))
    els.append(SC.layer(clock, 9, b_nobody, j=10, kind='character',
                        eid='b_nobody'))
    # NO caption at b09: the shrug plus the "no answer" bubble IS the line.

    # ===================================================================== #
    # STAGE C  b10-b14  "The fence runs for miles across the desert.         #
    #                 It surrounds nothing you can see.                     #
    #                 There is a second fence behind it.                   #
    #                 Cameras sit on tall poles along the wire.             #
    #                 The base is smaller than its fence."                  #
    # Five beats of ONE perimeter. The near fence goes up at b10 and STAYS  #
    # -- it is the chapter's running subject, and the b33 finale stands on #
    # the same line of posts. The second fence ACCRUES BEHIND it at b12,    #
    # the camera poles ACCRUE on the wire at b13, and at b14 the base      #
    # itself arrives -- small, in front, so the comparison the sentence    #
    # makes becomes a single readable frame.                                #
    # ===================================================================== #
    def c_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 49)
        _mountain_strip(d, HZ, 50)
    els.append(SC.stage(clock, 10, c_backdrop, j=15))

    def c_nearfence(tile, fw, fh):
        # ACCRUES, and it ACCRUES LOW: a 12-post run from off the left edge to
        # off the right one, so it reads as "miles" without a caption. Its base
        # sits at y=640 with a 280px fence, leaving the lower band clear for
        # the base and the presenter at b11-b14.
        _fence(ImageDraw.Draw(tile), -60, 452, W + 60, 176, 61, n_posts=12)
    # The fence band moved UP into the upper third and came DOWN in height
    # (280 -> 176). At the old geometry its base sat at y=640 with 280px of
    # mesh over the lower half of the frame, and the b14 base -- drawn at
    # y=620, inside that band -- was lost in the mesh: the beat's whole
    # subject was "the base is smaller than its fence" and the base could
    # not be seen. The fence now occupies y 276-452 and the strip from 452
    # down is clear alkali for the base and the caption.
    els.append(SC.accrue(clock, 10, 15, c_nearfence, kind='shape',
                         eid='c_nearfence'))

    def c_peeker(tile, fw, fh):
        # CROPPED BY THE RIGHT EDGE. Placed inside the frame at v1's x=980 he
        # read as set dressing beside a fence; cropped he reads as someone
        # intruding on the shot, which is what "surrounds nothing you can see"
        # is about.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 1330, 700, 440, pose='peeking', expression='deadpan',
                    seed=57)
    els.append(SC.layer(clock, 11, c_peeker, j=12, kind='character',
                        eid='c_peeker'))
    els.append(cap(11, 420, 210, size=30, max_w=620))
    # NO caption at b10: a wire fence running off both edges of the frame IS
    # "runs for miles". The word would be smaller than the evidence.

    def c_farfence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The second fence, higher and smaller -- RECEDING, not stacked. Drawn
        # after the near one so it overlays, which is why it is placed well
        # ABOVE the near fence's top rail: the two never share a pixel band and
        # the eye reads depth instead of a pile.
        _fence(d, 60, 286, W - 60, 118, 60, n_posts=8)
    # Receding, not stacked: the far fence occupies y 168-286 and the near
    # fence starts at 276, so the two bands abut with a 10px gap and the eye
    # reads depth. They must not overlap -- two meshes crossing read as a
    # pile, which is the b29 defect all over again.
    els.append(SC.accrue(clock, 12, 15, c_farfence, kind='shape',
                         eid='c_farfence'))
    # NO caption at b12: two fences at two depths IS "a second fence behind it".

    def c_cameras_l(tile, fw, fh):
        # The two poles ACCRUE onto the near fence's top rail, not beside it.
        # In v1 these were a separate full-frame card and the fence underneath
        # was repainted to make room; here they stand on the wire that is
        # already there, which is what the sentence describes.
        #
        # SPLIT INTO TWO ELEMENTS so each pole can carry its own small arrival.
        # One element holding both heads could only be moved as a pair, and a
        # 640px pair sliding in reads as the picture changing -- which is the
        # defect this rebuild exists to remove. A single head nudging 34px
        # reads as a camera panning along the wire.
        _camera_pole(ImageDraw.Draw(tile), 300, 470, 300, 67, lens_dir=1)
    els.append(SC.accrue(clock, 13, 15, c_cameras_l, kind='shape',
                         eid='c_cameras_l',
                         motion=SC.enter(clock, 13, dx=-34, dur=0.45)))

    def c_cameras_r(tile, fw, fh):
        _camera_pole(ImageDraw.Draw(tile), 940, 470, 300, 68, lens_dir=-1)
    # Pole bases moved 630 -> 470 with the fence band. The poles stand in the
    # alkali in FRONT of both fences and rise past their tops, which is what
    # a camera mast on the near side of a perimeter actually looks like.
    els.append(SC.accrue(clock, 13, 15, c_cameras_r, kind='shape',
                         eid='c_cameras_r',
                         motion=SC.enter(clock, 13, dx=34, dur=0.45)))
    # NO caption at b13: the camera heads with their red lenses, standing on the
    # wire, are the words. v1 captioned this beat and it only added a caption
    # under two poles that were already unmistakable.
    els.append(cap(14, 640, 690, size=28, fill=RED, max_w=620))

    def c_smallbase(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE COMPARISON, in one frame. The near fence runs off both edges at
        # 176px in the upper third; the base that justifies it stands on
        # clear alkali BEHIND the fence line, and is drawn ~1.6x larger than
        # the first pass. It was 104/84/132 wide on a 1280 frame -- a
        # third of the width in three small blocks, sitting at y=620 with
        # 280px of mesh over it, so the one thing the caption names was the
        # one thing you could not see. Now the base line is at y=468 (just
        # above the near fence's base, reading as behind it), the blocks run
        # 430-710, and the strip below y=560 is empty alkali for the words.
        _bunker(d, 430, 468, 150, 80, 73)
        _bunker(d, 592, 468, 120, 66, 74)
        _tower(d, 748, 468, 176, 75)
    els.append(SC.layer(clock, 14, c_smallbase, j=15, kind='shape',
                        eid='c_smallbase'))
    # The b14 caption is the ONE place in this chapter where a drawn label and
    # a caption would have been redundant, so the drawn labels were dropped and
    # the words kept instead: "The base is smaller than its fence" says the
    # comparison out loud, and the art makes it true without printing on it.

    # ===================================================================== #
    # STAGE D  b15-b19  "No aircraft may fly overhead.                       #
    #                 Red dashed line drawn across the sky.                #
    #                 Pilots noticed the rule before it was admitted.        #
    #                 Pilots reported lights over the dry lake.              #
    #                 In 1955, the reports started."                         #
    # WHY THIS STAGE IS NIGHT. v1 painted b18 as a night cockpit card in the #
    # middle of a bleached-noon chapter and it read as a register glitch.   #
    # But "pilots reported lights over the dry lake" has NO honest read on a #
    # white playa -- a red halo on alkali-white ground is invisible. So the  #
    # whole stage is night: the red dashed ceiling line becomes the strongest#
    # image in the chapter against NIGHT, and the light at b18 finally lands.#
    # SC.title_backdrop() is called first so the hardcoded-INK scene title   #
    # can be read over the dark band.                                        #
    # ===================================================================== #
    def d_backdrop(tile, fw, fh):
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
    els.append(SC.stage(clock, 15, d_backdrop, j=20))

    def d_jet(tile, fw, fh):
        _jet(ImageDraw.Draw(tile), 560, 190, 210, 80)
    els.append(SC.accrue(clock, 15, 17, d_jet, kind='shape', eid='d_jet'))

    def d_ceiling(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The no-fly ceiling. It is a THIN line, so this is one of the few
        # elements in the chapter allowed to move across the frame: a 150px
        # draw-on over 0.55s reads as the rule being drawn, not as the picture
        # churning. Everything wide in this chapter stays still.
        y = 300
        dash, gap, x = 60, 34, -40
        while x < W + 40:
            PA.hand_stroke(d, [(x, y), (x + dash, y)], RED, 9, seed=105 + x,
                           wavelength=70.0)
            x += dash + gap
    els.append(SC.layer(clock, 16, d_ceiling, j=20, kind='shape',
                        eid='d_ceiling',
                        motion=SC.enter(clock, 16, dx=-150, dur=0.55)))

    def d_pilot(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The rule, enforced: the SAME jet, now BELOW the line, with a red X
        # over it. It REPLACES the b15 jet rather than joining it -- two jets
        # and a ceiling in one frame would be the diagram-equivalent of a
        # pile-up.
        _jet(d, 620, 470, 190, 99)
        D.draw_red_x(tile, [556, 410, 690, 500], color=RED, width=9)
        SC.fullbody(d, 250, 700, 430, pose='pointing', expression='shock',
                    seed=100)
    els.append(SC.layer(clock, 17, d_pilot, j=19, kind='character',
                        eid='d_pilot',
                        motion=SC.enter(clock, 17, dy=-58, dur=0.5)))
    # NO caption at b16: the line IS the words. NO caption at b15: the jet with
    # the line drawn across its path says "no aircraft may fly overhead" in the
    # clearest available idiom, and b17's caption carries the actual new fact.
    els.append(cap(17, 900, 650, size=30, max_w=620, dark=True))
    # The caption at b17 was at (880, 300) -- exactly the y of the red dashed
    # ceiling line, so the rule struck straight through the words. It now sits
    # at y=650, on the alkali below the horizon, where d_pilot's jet (y
    # 410-500) and the horizon rim are the only other things and neither
    # reaches that row. dark=True: this is a night card.

    def d_lights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Pilots reported lights over the dry lake." A cluster of haloes ON the
        # ground with a dark cockpit frame cropping the top of the frame -- we
        # are inside the aircraft looking down at them, which is what makes the
        # haloes read as reported rather than decorative.
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
    els.append(SC.layer(clock, 18, d_lights, j=19, kind='shape',
                        eid='d_lights',
                        motion=SC.enter(clock, 18, dy=-34, dur=0.45)))

    def d_1955(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "In 1955, the reports started." The calendar is scaled to OWN the
        # night frame -- it is the one bright thing on a dark stage, so it does
        # not need a card of its own. An earlier draft filled the whole frame
        # with a separate ground colour here, which was two mistakes: it
        # repainted the stage from underneath (the whole point of the model is
        # that the frame does not change inside a stage) and it covered the
        # SC.title_backdrop() the stage had drawn, so the title went unreadable.
        _calendar(d, 640, 400, 380, 290, 110, year=1955, circle_year=True)
    els.append(SC.layer(clock, 19, d_1955, j=20, kind='shape', eid='d_1955'))
    # NO caption at b19: the calendar is DRAWN with 1955 on it in a 125px
    # numeral. This is the clearest case in the chapter of a caption that would
    # be pure duplication.

    # ===================================================================== #
    # STAGE E  b20-b25  "Roswell was already three years old.                #
    #                 The desert kept the story all the same.               #
    #                 Pilots named the place Hangar 18.                     #
    #                 Empty hangar door, number painted on the wall.        #
    #                 Officially, that hangar is not there.                 #
    #                 Nellis Air Force Base runs the site."                 #
    # Back to the day register, and back to a place: the playa, then the     #
    # HANGSAR WALL, which is the largest object in the chapter and which     #
    # ACCRUES at b22 and stays for the rest of the stage. Everything that    #
    # follows is a change TO that wall, so each one replaces rather than     #
    # stacking -- the door state and the DOES NOT EXIST stamp are both text- #
    # bearing and both want the same middle of the frame.                    #
    # ===================================================================== #
    def e_backdrop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 151)
        _mountain_strip(d, HZ, 152)
    els.append(SC.stage(clock, 20, e_backdrop, j=26))

    def e_roswell(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # 1947, three years before 1955. The beat is a DATE, and the calendar
        # primitive draws the date, so there is no caption here -- but the
        # calendar ACCRUES rather than replacing, because the wall has not
        # arrived yet and the desert is still the ground.
        _calendar(d, 430, 380, 300, 240, 153, year=1947, circle_year=True)
    els.append(SC.layer(clock, 20, e_roswell, j=21, kind='shape',
                        eid='e_roswell'))
    els.append(cap(20, 1020, 300, size=30, max_w=440))
    # The caption at b20 is KEPT because the calendar prints only the YEAR. The
    # name on the beat -- Roswell -- appears nowhere in the art, and it is the
    # name that makes 1947 mean something to a viewer who has not heard it yet.
    # It sits in the open desert to the right of the page.

    def e_balloon(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "The desert kept the story all the same." The sagging balloon comes
        # back over the wire -- the same half-deflated silhouette from b21 in
        # v1 -- cropped by the right edge so it owns the frame instead of
        # floating as a small prop. The faint year is GONE: 1947 is already
        # printed on the calendar behind it and printing it twice in one frame
        # is the pile-up this model exists to prevent.
        _balloon_low(tile, d, 1080, 320, 210, 154)
    els.append(SC.layer(clock, 21, e_balloon, j=22, kind='shape',
                        eid='e_balloon'))
    # NO captions at b20 or b21: the calendar is DRAWN reading 1947, and the
    # sagging balloon IS "the story went flat". Both sentences are carried by
    # the art and neither gains from a caption.

    def e_wall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE WALL. ACCRUES -- it is the biggest piece of the world in this
        # stage and it does not move again. Scaled to own the frame and cropped
        # BY the left and right edges, per the frame-fill rule; v1's version
        # sat centred with desert on both sides and read as a prop. No text on
        # it: everything that gets PRINTED on this wall arrives as its own
        # replaceable layer below, because text on an accruing surface is
        # exactly how you end up with two '18's on one hangar.
        wall = [(-60, 660), (-60, 96), (1340, 96), (1340, 660)]
        PA.fill_poly(tile, wall, CONCRETE, seed=155, value=0.07)
        PA.hand_stroke(d, wall, INK, 7, closed=True, seed=156, wavelength=150.0)
        # Panel seams. The first pass drew 11 vertical seams at (188,182,170)
        # 5px, which measured as present and read as nothing: the tone is 8
        # values off the wall fill and the frame came out a pale empty field.
        # A hangar wall reads as a wall when it has HORIZONTAL panel joints as
        # well as vertical ones, a dark skirt where it meets the ground, and a
        # cast shadow to give the plane a light direction. Drawn darker
        # (146,142,134) and 7px, with the horizontals at a wider spacing so
        # the two directions do not read as a grid.
        for i in range(11):
            x = 20 + i * 118
            PA.hand_stroke(d, [(x, 126), (x, 636)], (146, 142, 134), 7,
                           seed=157 + i, wavelength=110.0)
        for jy in (250, 430):
            PA.hand_stroke(d, [(-40, jy), (1320, jy)], (150, 146, 138), 6,
                           seed=180 + jy, wavelength=150.0)
        PA.fill_rect(tile, [-40, 556, 1320, 660], (128, 124, 116), seed=186,
                     value=0.05)
        PA.hand_stroke(d, [(-40, 556), (1320, 556)], (96, 92, 86), 6,
                       seed=187, wavelength=150.0)
        PA.fill_poly(tile, [(-40, 96), (1320, 96), (1320, 250), (-40, 330)],
                     (178, 172, 160), seed=188, value=0.06)
    els.append(SC.accrue(clock, 22, 26, e_wall, kind='shape', eid='e_wall'))

    def e_18(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The painted number, 230px so it reads across the frame. It is a LAYER
        # living only to b23, not an accrue, so that when the door opens at b23
        # this number leaves with it instead of hanging beside the new one.
        D.draw_number(tile, '18', center=(360, 330), color=INK, size=230)
        D.draw_label(tile, 'HANGAR', center=(360, 520), color=INK, size=64)
    els.append(SC.layer(clock, 22, e_18, j=23, kind='shape', eid='e_18'))
    els.append(cap(22, 1000, 300, size=30, max_w=460))
    # The caption at b22 is KEPT, and this is the one place in the chapter
    # where art-prints-the-words and caption-says-the-words are not in conflict:
    # the caption supplies the ATTRIBUTION the paint cannot -- that PILOTS named
    # the place -- and it is placed in the bare wall to the RIGHT of the
    # painted number, so the two never overlap.

    def e_doorhole(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Empty hangar door, number painted on the wall." The dark opening is
        # cut into the wall that is already standing -- so this is a state
        # change, not a new wall. The leaf that covers it is a SEPARATE element
        # because the leaf is the one thing in this chapter whose movement
        # carries information: a door sliding open is the reveal, exactly as the
        # radome cover lifting was in the pilot.
        PA.fill_poly(tile, [(340, 250), (860, 250), (860, 656), (340, 656)],
                     (40, 44, 56), seed=170, value=0.05)
        PA.hand_stroke(d, [(340, 250), (860, 250), (860, 656), (340, 656)],
                       INK, 6, closed=True, seed=171, wavelength=120.0)
        D.draw_number(tile, '18', center=(1090, 320), color=INK, size=160)
    # Re-centred. The opening used to span x 196-620 with the painted 18 at
    # x=1170, which left the whole right half of a 1280 frame carrying a
    # single number and the left third carrying the door: the composition
    # had its subject off-centre with a void beside it. Door at 340-860 and
    # number at 1090 puts the two masses either side of the midline.

    els.append(SC.layer(clock, 23, e_doorhole, j=24, kind='shape',
                        eid='e_doorhole'))

    def e_leaf(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The sliding leaf, authored ACROSS the opening (340-860) and carried
        # left off it. The old leaf was authored at -40..196 -- beside the
        # opening, not over it -- and given SC.enter(dx=-130), which eases an
        # element FROM an offset TO its authored place. That combination slid
        # the panel further left and then right, i.e. it shut. This one starts
        # covering the opening and travels 600px clear of it.
        leaf = [(340, 250), (860, 250), (860, 656), (340, 656)]
        PA.fill_poly(tile, leaf, (198, 192, 180), seed=172, value=0.06)
        PA.hand_stroke(d, leaf, INK, 6, closed=True, seed=173, wavelength=120.0)
        for i in range(6):
            x = 380 + i * 78
            PA.hand_stroke(d, [(x, 268), (x, 638)], (162, 156, 146), 4,
                           seed=180 + i, wavelength=90.0)
    _t0 = T(23)
    els.append(SC.layer(clock, 23, e_leaf, j=24, kind='shape', eid='e_leaf',
                        motion=[(_t0, 0, 0, 1.0, 0.0),
                                (_t0 + 0.55, -600, 0, 1.0, 0.0)]))
    # NO caption at b23: the open door and the number at the frame edge ARE the
    # sentence, and a caption here would sit adjacent to b22's with nothing in
    # between.

    def e_noexist(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Officially, that hangar is not there." The stamp lands ON the wall
        # and covers the door, so this REPLACES the door state. A stamp drawn
        # over a still-open door would say "and here it is, officially not
        # there" in the same frame. The hangar box is redrawn because the
        # stamp needs a plain surface to sit on, and _hangar's dark door slot
        # is exactly the kind of detail that would fight the red box.
        _hangar(d, 120, 660, 1040, 560, 174)
        D.draw_red_box(tile, [100, 210, 1180, 570], color=RED, width=9)
        D.draw_label(tile, 'DOES NOT EXIST', center=(640, 390), color=RED,
                     size=80, outline=INK, outline_w=2)
    els.append(SC.layer(clock, 24, e_noexist, j=25, kind='shape',
                        eid='e_noexist'))
    els.append(cap(24, 640, 690, size=30, fill=RED, max_w=700))
    # The caption at b24 is KEPT even though the stamp is DRAWN, for the same
    # reason as b22 and for a stronger one: the stamp says the hangar does not
    # exist, and the narration says it is not OFFICIALLY there. The denial is
    # the point of the beat and the stamp alone would lose the official half.
    # It sits in the strip below the red box, which is bare hangar wall.

    def e_nellis(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Nellis Air Force Base runs the site." The wall cannot be un-drawn,
        # so this is the one beat in the stage that must repaint its own ground
        # -- and it repaints it IDENTICALLY (same seeds and fills as
        # e_backdrop), so the transition reads as the wall leaving rather than
        # as a cut to somewhere else. Then the runway runs off the bottom edge
        # with two hangars at the far end.
        _playa(tile, 151)
        _mountain_strip(d, HZ, 152)
        _runway(d, 500, 540, 790, H + 30, 20, 132, 175)
        _hangar(d, 545, 546, 300, 190, 176)
        _hangar(d, 890, 546, 290, 182, 177)
        D.draw_label(tile, 'NELLIS AFB', center=(900, 250), color=INK, size=48)
    els.append(SC.layer(clock, 25, e_nellis, j=26, kind='shape', eid='e_nellis'))
    # NO caption at b25: the runway and two hangars with NELLIS AFB above them
    # are the sentence.

    # ===================================================================== #
    # STAGE F  b26-b30  "The budget for the site is not public.              #
    #                 In 1989, a man named Bob Lazar spoke.                 #
    #                 He claimed he had worked there.                       #
    #                 He described what was parked inside.                  #
    #                 No employment record of his exists."                   #
    # An INTERIOR: a plain office wall with a floor line. v1 gave each of     #
    # these five beats its own full-frame room (a paper desk, a living room, #
    # a press hall, a grey void, a filing room), which is five register      #
    # switches in six seconds. Here they are all the same room and the      #
    # objects ACCRUE into it: the budget sheet goes up on the wall, the TV   #
    # arrives in front of it, the man replaces the TV at the lectern, and    #
    # his description is sketched in the air beside him.                     #
    # ===================================================================== #
    def f_backdrop(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, W, H], (206, 200, 190), seed=175, value=0.05)
        PA.fill_rect(tile, [0, 420, W, H], (188, 180, 170), seed=176, value=0.07)
        PA.paper_overlay(tile, seed=177)
    els.append(SC.stage(clock, 26, f_backdrop, j=31))

    def f_budget(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The budget sheet, ACCRUING on the office wall for the whole stage --
        # it is a document pinned up in a room, and it is the physical proof
        # that this story happens in offices rather than on the playa. The one
        # blacked-out line is the subject; NOT PUBLIC is stamped across it so
        # the beat needs no caption.
        sheet = [(430, 150), (1200, 150), (1200, 600), (430, 600)]
        PA.fill_poly(tile, sheet, PAPER, seed=164, value=0.05)
        PA.hand_stroke(d, sheet, INK, 6, closed=True, seed=165, wavelength=140.0)
        # NO 'BUDGET' heading. It was at (640, 186), which put it on the same
        # baseline as the b27 caption at (1000, 200) -- 30px apart, so the two
        # read as one run of text: the pile-up defect, arrived at from the
        # other direction. The sheet is identified by its ruled lines and the
        # redaction, and NOT PUBLIC is the only word on it that carries
        # meaning, which is what this file already said was the point.
        for i in range(5):
            y = 250 + i * 50
            PA.hand_stroke(d, [(300, y), (560 - (i % 3) * 40, y)],
                           (150, 146, 138), 4, seed=166 + i, wavelength=70.0)
        # The redaction bar starts at x=498, not 300. At 300 it ran under the
        # seated presenter (x=430) and read as a bench he was sitting on.
        PA.fill_rect(tile, [498, 486, 980, 530], INK, seed=173, value=0.04)
        # NOT PUBLIC sits in the strip BELOW the blacked-out line, at y=655.
        # It was at y=570, which is inside the television's rectangle (y
        # 300-610) and inside the lectern's -- so at b27 the set sliced the
        # word and at b29 the sketch disc sat on top of it. Nothing else in
        # stage F reaches below y=630, so this row is the only clear band in
        # the stage.
        D.draw_label(tile, 'NOT PUBLIC', center=(640, 655), color=RED, size=40,
                     outline=INK, outline_w=2)
    # The sheet is a LAYER, not an accrue. It is the b26 subject, and it is
    # gone by b28 because the room becomes the subject there: keeping it
    # accruing to b31 meant the b28 lectern was drawn in front of a document
    # nobody was reading, and the b30 drawer was painted onto the same wall.
    # Persistence in this stage is carried by f_backdrop, which really is the
    # same room for all five beats, and by the television motif returning at
    # b27 and b28 -- a rhyme, not a leftover.
    els.append(SC.layer(clock, 26, f_budget, j=28, kind='shape', eid='f_budget'))
    # NO caption at b26: the sheet is DRAWN with NOT PUBLIC across the
    # blacked-out line. The art already says it in the two words that matter.

    def f_tv(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "In 1989, a man named Bob Lazar spoke." The television stands in
        # front of the budget sheet -- ACCRUING art in front of accruing art,
        # which is the right order here because they do not share a region: the
        # sheet is the wall behind, the set is a solid object in the room.
        tv = [(700, 300), (1160, 300), (1160, 610), (700, 610)]
        PA.fill_poly(tile, tv, (92, 96, 104), seed=178, value=0.07)
        PA.hand_stroke(d, tv, INK, 6, closed=True, seed=179, wavelength=130.0)
        scr = [(730, 328), (1130, 328), (1130, 546), (730, 546)]
        PA.fill_poly(tile, scr, (170, 186, 196), seed=180, value=0.08)
        PA.hand_stroke(d, scr, INK, 5, closed=True, seed=181, wavelength=110.0)
        SC.closeup(d, 930, 436, 78, 'deadpan', 182, shoulder=0.0)
        d.ellipse([1090, 486, 1120, 516], outline=INK, width=5)
        D.draw_label(tile, '1989', center=(930, 652), color=RED, size=44,
                     outline=INK, outline_w=2)
        # the presenter, leaned in, watching. The face ON the screen is the
        # substitute for a portrait we do not have and must not invent.
        SC.fullbody(d, 430, 700, 430, pose='sitting', expression='awed',
                    seed=183)
    # A LAYER ending at b28, not an accrue to b31. This single change is what
    # the b29 pile-up was made of: while f_tv was accruing, the b28 lectern
    # drew a SECOND television beside it and a SECOND stickman opposite it
    # (the double-character defect this module is at pains to avoid
    # elsewhere), and at b29 the sketch disc landed squarely on this set with
    # the closeup face peeking out from under it. The television's job is
    # done at b27 -- f_lectern redraws its own at b28, which is the visual
    # rhyme -- so it leaves.
    els.append(SC.layer(clock, 27, f_tv, j=28, kind='character', eid='f_tv'))
    els.append(cap(27, 1000, 200, size=30, max_w=520))
    # The caption at b27 is KEPT and is the most important text in the chapter:
    # NOTHING in the art says the name. The set says 1989 and shows a man; the
    # words are what make him Bob Lazar. It sits in the bare wall band at the
    # top right, above the set -- the left-hand placement it had at (420,215)
    # overlapped the sheet's BUDGET heading at y=186.

    def f_lectern(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "He claimed he had worked there." The room's occupant changes: the
        # seated viewer is replaced by the speaker standing behind a lectern,
        # which is the same room and the same wall from a different angle. He
        # REPLACES the presenter because two stickmen in one frame is the
        # double-character defect, and the TV goes with him -- a lectern in
        # front of a television reads as two stages in one room.
        PA.fill_poly(tile, [(60, 300), (620, 300), (620, 610), (60, 610)],
                     (92, 96, 104), seed=184, value=0.07)
        PA.hand_stroke(d, [(60, 300), (620, 300), (620, 610), (60, 610)],
                       INK, 6, closed=True, seed=185, wavelength=130.0)
        scr = [(90, 328), (590, 328), (590, 546), (90, 546)]
        PA.fill_poly(tile, scr, (170, 186, 196), seed=186, value=0.08)
        PA.hand_stroke(d, scr, INK, 5, closed=True, seed=187, wavelength=110.0)
        SC.closeup(d, 340, 436, 78, 'deadpan', 188, shoulder=0.0)
        D.draw_label(tile, '1989', center=(340, 652), color=RED, size=44,
                     outline=INK, outline_w=2)
        SC.fullbody(d, 1000, 700, 440, pose='standing', expression='deadpan',
                    seed=197)
        lect = [(908, 700), (926, 492), (1074, 492), (1092, 700)]
        PA.fill_poly(tile, lect, (128, 120, 110), seed=196, value=0.06)
        PA.hand_stroke(d, lect, INK, 6, closed=True, seed=198, wavelength=110.0)
        PA.hand_stroke(d, [(920, 492), (1080, 492)], INK, 7, seed=199,
                       wavelength=110.0)
        PA.hand_stroke(d, [(1006, 492), (1006, 412)], STEEL, 8, seed=201,
                       wavelength=60.0)
        d.ellipse([988, 382, 1024, 418], fill=INK)
    els.append(SC.layer(clock, 28, f_lectern, j=29, kind='character',
                        eid='f_lectern'))
    # NO caption at b28: the man at a microphone in front of a 1989 television
    # is the sentence, and b27 is one beat earlier with words on it.

    def f_sketch(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "He described what was parked inside." His account, drawn as he draws
        # it: the disc-with-a-dome, framed by two sketching hands.
        # It is CENTRED and scaled up. At cx=940 with rx=320 the disc occupied
        # the right half of the frame and left 300px of bare wall to its left;
        # that was a too-small-subject-in-an-empty-field frame, the recurring
        # defect this project keeps finding. At rx=400 it spans 200 of 1280px
        # either side of centre, and the hands flank it inside the frame.
        cx, cy = 640, 350
        disc = PA.ellipse_pts(cx, cy, 400, 140, n=72)
        PA.fill_poly(tile, disc, (146, 152, 162), seed=201, value=0.07)
        PA.hand_stroke(d, disc, INK, 7, closed=True, seed=202, wavelength=150.0)
        dome = []
        n = 40
        for i in range(n + 1):
            a = math.pi + math.pi * i / n
            dome.append((cx + 176 * math.cos(a), cy - 48 + 124 * math.sin(a)))
        PA.fill_poly(tile, dome + [(cx + 176, cy - 48), (cx - 176, cy - 48)],
                     (226, 228, 230), seed=203, value=0.04, edge=1.2)
        PA.hand_stroke(d, dome, INK, 6, closed=False, seed=204, wavelength=120.0)
        PA.hand_stroke(d, [(cx - 176, cy - 48), (cx + 176, cy - 48)],
                       (108, 114, 120), 5, seed=205, wavelength=100.0)
        _hand_sketch(d, 300, 560, 232, flip=1)
        _hand_sketch(d, 985, 560, 236, flip=-1)
        # A horizon rule under the disc so the drawing sits on the office
        # floor line rather than floating in the middle of the wall.
        PA.hand_stroke(d, [(150, 560), (1130, 560)], (176, 172, 164), 4,
                       seed=214, wavelength=140.0)
    els.append(SC.layer(clock, 29, f_sketch, j=30, kind='shape',
                        eid='f_sketch'))
    # NO caption at b29: the shape he described is the picture, and the caption
    # would only name it.

    def f_drawer(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "No employment record of his exists." The punchline: an open drawer
        # with one dark empty slot and a red arrow on it. It REPLACES the
        # sketch -- the sketch's disc is 640px wide in the same right half, and
        # a drawer drawn over it would leave the dome's arc showing through the
        # slot. The television has already gone at b28; the budget sheet is
        # still on the wall behind, which is fine: a filing cabinet in an
        # office is against a wall that has things on it.
        PA.fill_rect(tile, [0, 0, W, H], (214, 208, 196), seed=208, value=0.05)
        PA.paper_overlay(tile, seed=209)
        dr = [(330, 210), (1010, 210), (1010, 590), (330, 590)]
        PA.fill_poly(tile, dr, (186, 176, 160), seed=210, value=0.07)
        PA.hand_stroke(d, dr, INK, 7, closed=True, seed=211, wavelength=140.0)
        for i in range(4):
            x0 = 370 + i * 158
            slot = [(x0, 250), (x0 + 134, 250), (x0 + 134, 550), (x0, 550)]
            empty = (i == 2)
            col = (52, 54, 62) if empty else (226, 206, 158)
            PA.fill_poly(tile, slot, col, seed=212 + i, value=0.06)
            PA.hand_stroke(d, slot, INK, 4, closed=True, seed=216 + i,
                           wavelength=90.0)
        PA.hand_stroke(d, [(820, 590), (820, 636)], RED, 5, seed=220,
                       wavelength=60.0)
        D.draw_label(tile, 'NO RECORD', center=(1080, 442), color=RED, size=34,
                     outline=INK, outline_w=2)
        SC.fullbody(d, 175, 660, 400, pose='armscrossed', expression='deadpan',
                    seed=221)
    els.append(SC.layer(clock, 30, f_drawer, j=31, kind='character',
                        eid='f_drawer'))
    els.append(cap(30, 620, 668, size=30, fill=RED, max_w=700))
    # The caption at b30 is KEPT: the drawer shows an EMPTY SLOT, which says
    # "there is nothing here", and the sentence says the one thing the art
    # cannot -- that what is missing is a record of HIM. It sits in the strip
    # below the drawer, clear of the red arrow at x=820.

    # ===================================================================== #
    # STAGE G  b31-b34  "In 2020, the FBI released its files.                #
    #                 One page stamped with the lake's name.                #
    #                 The fence is still standing there.                    #
    #                 Nobody has ever looked inside."                        #
    # The finale is NIGHT, and it CLOSES THE LOOP: the last frame is the same #
    # fence on the same playa as b01, now almost black with one red light.   #
    # The chapter's own subject -- that fence -- is what the viewer is left   #
    # holding, so nothing in this stage is allowed to cover it for long.      #
    # The documents arrive first, replace each other, and then clear.        #
    # ===================================================================== #
    def g_backdrop(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, W, H], NIGHT, seed=247, value=0.12)
        PA.fill_rect(tile, [0, HZ - 6, W, H], NIGHT_G, seed=248, value=0.12)
        PA.paper_overlay(tile, seed=249)
        # lit course on the title band so the hardcoded-INK title reads on the
        # night card (see scene_common.title_backdrop). Called before any fill
        # that could cover it.
        SC.title_backdrop(tile, 134, col=(84, 92, 118))
    els.append(SC.stage(clock, 31, g_backdrop, j=35))

    def g_stack(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "In 2020, the FBI released its files." The stamp says RELEASED and
        # NOT the year -- the YEAR is in the caption instead, because the beat
        # is the date as much as the release and printing 2020 in both places
        # is duplication. The stack is the brightest thing on the night stage,
        # so it is scaled to own the frame rather than floated in the middle.
        _file_stack(d, 640, 400, 400, 224, n=6, stamp='RELEASED')
    els.append(SC.layer(clock, 31, g_stack, j=32, kind='shape', eid='g_stack',
                        motion=SC.enter(clock, 31, dy=54, dur=ARRIVE)))
    els.append(cap(31, 640, 596, size=30, dark=True, max_w=700))

    def g_page(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "One page stamped with the lake's name." One sheet, cropped left and
        # right so it fills the frame, with the typed line GROOM LAKE picked
        # out among the redactions and a finger under it. It REPLACES the stack
        # -- two documents at once in the same frame is the pile-up.
        sheet = [(-40, 110), (1320, 110), (1320, 660), (-40, 660)]
        PA.fill_poly(tile, sheet, PAPER, seed=227, value=0.05)
        PA.hand_stroke(d, sheet, INK, 6, closed=True, seed=228, wavelength=150.0)
        for i in range(8):
            y = 158 + i * 48
            if i == 4:
                continue
            PA.hand_stroke(d, [(140, y), (140 + (860 if i % 2 else 640), y)],
                           (150, 146, 138), 4, seed=229 + i, wavelength=70.0)
        y = 158 + 4 * 48
        D.draw_label(tile, 'GROOM LAKE', center=(470, y), color=INK, size=52)
        PA.fill_poly(tile, [(600, 620), (650, 470), (712, 620)],
                     (222, 180, 150), seed=240, value=0.05)
        PA.hand_stroke(d, [(600, 620), (650, 470), (712, 620)], INK, 5,
                       closed=False, seed=241, wavelength=70.0)
    els.append(SC.layer(clock, 32, g_page, j=33, kind='shape', eid='g_page'))
    # NO caption at b32: the page is DRAWN with GROOM LAKE on it in 52px ink
    # under a pointing finger. The words are already the picture.

    def g_fence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "The fence is still standing there." Back to b01's shot -- same playa,
        # same line of posts, same framing -- but at night and in near-black
        # wire, which is the only way the line of it reads as still standing
        # after everything that has happened in between. It REPLACES the page:
        # the fence has to be the only thing in the frame for that to land.
        _fence(d, -40, 640, W + 40, 260, 245, n_posts=9,
               post_col=(40, 42, 54), rail_col=(40, 42, 54))
        lx, ly = 760, 386
        for rr, col in ((80, (66, 34, 36)), (46, (140, 56, 48)), (20, RED)):
            d.ellipse([lx - rr, ly - rr, lx + rr, ly + rr], fill=col)
    els.append(SC.layer(clock, 33, g_fence, j=35, kind='shape', eid='g_fence'))
    els.append(cap(33, 430, 220, size=32, dark=True, max_w=560))
    # The caption at b33 is KEPT: the fence at night says "it is still here" and
    # not the two things that make it a fact -- STILL, and standing THERE,
    # unmoved, after everything. The red light sits at x=760 and the caption is
    # placed at x=430 in the empty sky on the other side of it.

    def g_never(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "Nobody has ever looked inside." The presenter, awed, cropped by the
        # LEFT edge so he is inside the shot rather than standing beside it, and
        # the 'never' bubble that is the last thing on screen. The fence is
        # still there behind both of them -- it was placed at b33 and nothing in
        # this beat covers it, which is the point: the wall is still up.
        SC.fullbody(d, 175, 700, 450, pose='standing', expression='awed',
                    seed=251)
        D.draw_bubble(tile, 'never', (940, 250), tail_to=(420, 350))
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
