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
    # One empty desert held across three beats. b02 is deliberately bare --  #
    # the emptiness IS the narration -- and the presenter arrives on b03 so  #
    # the "nothing here" beat lands before anything occupies the frame.     #
    # ===================================================================== #
    def a_desert(tile, fw, fh):
        _desert(tile, 5)
    els.append(SC.stage(clock, 1, a_desert, j=4))

    def a_presenter(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 300, 360, 210, 'deadpan', 3)
    els.append(SC.accrue(clock, 3, 4, a_presenter, kind='character',
                         motion=SC.enter(clock, 3, dx=-150, dy=40, dur=0.55)))
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
        _desert(tile, 9)
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
        _desert(tile, 37)
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
        _desert(tile, 81)
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
    els.append(cap(18, 1076, 660, size=26))

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
        _desert(tile, 95, sky=(226, 232, 238), ground=(226, 232, 238))
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
    els.append(cap(23, 640, 636, size=28))

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
        _desert(tile, 131, sky=(226, 232, 238), ground=(226, 232, 238))
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
    els.append(cap(30, 900, 620, size=28, fill=RED))

    # ===================================================================== #
    # STAGE G  b31-b34  "Airspace is locked to eighteen thousand feet.       #
    #                 Armed guards walk the perimeter. Crossing the fence   #
    #                 means seven years in prison. No one goes inside."      #
    # The airspace column REPLACES at b32. Left accruing it stayed on screen #
    # under the fence and the guards, and "18,000 FEET" ended up printed     #
    # across "7 years in prison" -- the worst frame in the chapter.          #
    # ===================================================================== #
    def g_desert(tile, fw, fh):
        _desert(tile, 161, sky=(200, 212, 226), ground=DUNE)
    els.append(SC.stage(clock, 31, g_desert, j=35))

    def g_column(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        col = [(330, 720), (330, 104), (910, 104), (910, 720)]
        PA.fill_poly(tile, col, (176, 190, 208), seed=153, value=0.08)
        for x in (330, 910):
            PA.hand_stroke(d, [(x, 104), (x, 720)], RED, 7, seed=154 + x,
                           wavelength=160.0)
        PA.hand_stroke(d, [(330, 104), (910, 104)], RED, 7, seed=156,
                       wavelength=160.0)
        D.draw_number(tile, '18,000', center=(620, 274), color=RED, size=96)
        D.draw_label(tile, 'FEET', center=(620, 366), color=RED, size=44)
    els.append(SC.layer(clock, 31, g_column, j=32))
    els.append(cap(31, 640, 500, size=26, fill=RED))

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