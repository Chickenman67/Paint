"""tomb2_scene -- the PERSISTENT-STAGE rebuild of chapter 3 (the Tomb).

WHY THIS FILE EXISTS. tomb_scene.py (v1) was built on "one card per beat, each
card paints its own whole frame". Its `card(i, j, draw, ...)` helper gave every
beat a complete background-to-subject repaint, so nothing survived between
beats: 45 full-frame repaints in 118s, a new image every ~2.6s, and a caption
on EVERY one of the 45 beats (100% text density). Nothing ever moved.

THE MODEL HERE. Nine PERSISTENT STAGES instead of 45 short cards, grouped on the
narration's own acts (work3/plans/STAGE_PLANS.md):

    A  b01-b05  eight thousand clay soldiers; the Terracotta Army name
    B  b06-b10  six hundred horses; long rows; all guarding one man
    C  b11-b16  Qin Shi Huang; first emperor; one script, one ruler
    D  b17-b20  burned the books; the scholars; forced labour
    E  b21-b25  the mound copied a pyramid; outside Xi'an; no two the same
    F  b26-b31  vanished 2,000 years; 1974 farmers; a clay shoulder; covered
    G  b32-b37  2012 pit; bronze cranes; the 1983 acid attack
    H  b38-b42  mercury in the soil; enough for a pool; a slow poison
    I  b43-b45  the main chamber never opened; still sealed; finale

Inside a stage the art ACCUMULATES: a layer that arrives stays until the stage
turns over (SC.accrue), so the viewer watches a place GAIN things -- a rank
building up, a horse stepping into the pit, the seal going on the door.

TWO RULES CARRIED OVER FROM THE PINES GAP PILOT, both measured there.

1. ACCRUE THE WORLD, REPLACE THE LABELS. Scenery accumulates; anything
   carrying text, and anything occupying the same part of the frame as something
   already there, REPLACES. tomb is the chapter where that matters most: the
   soldier ranks are the world and they accrue, while every name/number/label
   ('8,000', '600 HORSES', 'ONE MAN', 'QIN SHI HUANG', 'EVERY BOOK', '246 BC',
   'COPIED A PYRAMID', 'HEAVENLY PALACE', 'ALL DIFFERENT', 'NO TWO THE SAME',
   '2,000 YEARS', '1974', 'SOMETHING HARD', 'IT BROKE', 'COVERED OVER',
   'BOTH BROKEN', 'REPAIRED...', 'ACID', 'MERCURY', 'ENOUGH FOR A POOL',
   'THE OLD RECORDS', 'POISON', 'IT DOES NOT LET GO', 'NEVER OPENED',
   'THE DOOR STAYS SHUT') is a hand-off chain -- each one lives until the next
   one starts, so the top of the frame carries exactly one label at a time
   instead of a stack.

2. MOTION IS RARE AND IT IS ON SMALL THINGS. motion_profile only registers
   motion above ~60px/s, so animating everything produces a motion rate the
   reference does not have and every moving frame trips the picture-change
   counter -- which is worse than the churn this rebuild exists to remove. The
   reference is ~83% still frames. So TWELVE arrivals move, briefly
   (0.5-0.55s), and each is a SMALL subject: one clay soldier rising out of
   the cut, the presenter stepping in, a bronze shovel, the acid pouring, the
   mercury bead settling, two lines of carriers. The soldier RANKS, the horse,
   the emperor and every backdrop are still. Popping in IS the reveal; sliding
   is for the handful of moments where movement carries meaning.

CAPTIONS. 17 of 45 beats (38%), no two consecutive. The rule applied per beat:
keep the words when they carry something the drawn art does not -- the name
Terracotta Army, Qin Shi Huang, 221 BC, one script, that one ruler, the
scholars, forced labour, 1974, the clay shoulder, 2012, the acid, mercury,
the poison, the sealed chamber, the finale. DROP the beat when the art already
says it, and say so in a comment at the drop site. Examples: b06 "eight
thousand soldiers in the dark" is the rank standing there in a black pit;
b39 "enough to fill a pool" is a pool running off the left edge with the words
ENOUGH FOR A POOL drawn on it; b34's two broken cranes carry BOTH BROKEN.
A drawn label and a caption saying the same thing is still text pile-up.

CHARACTER. The presenter appears in four stages -- A (closeup, confused, then
shocked at the paint), D (full body recoiling at the scholars' pit), F (closeup
confused at 1974, swapping to shock when the clay shoulder comes up), I (full
body awed at the sealed door) -- and changes expression once inside a stage
twice, via SC.expr_swap, because the expression is baked into the rasterised
tile at build time and a change therefore needs two elements at one position.

Run:  python lib/tomb2_scene.py --preview --video
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
import tomb_scene as TB     # art primitives + palette, reused not copied

# --- contract with the rest of the pipeline (imported from v1) -------------
SEG = TB.SEG
TITLE = TB.TITLE
BEATS = TB.BEATS
TITLE_BACKDROP = TB.TITLE_BACKDROP

W, H = TB.W, TB.H

# --- palette, reused verbatim from v1. Two registers, exactly as before. ----
INK = TB.INK
CLAY = TB.CLAY
CLAY_D = TB.CLAY_D
CLAY_L = TB.CLAY_L
EARTH = TB.EARTH
EARTH_D = TB.EARTH_D
PIT = TB.PIT
PALE = TB.PALE
GOLD = TB.GOLD
FIRE = TB.FIRE
BRONZE = TB.BRONZE
PAPER2 = TB.PAPER2
BLUE = TB.BLUE
BLUE_L = TB.BLUE_L
ACID = TB.ACID
GREY = TB.GREY
GREY_D = TB.GREY_D
SILVER = TB.SILVER
HZ = TB.HZ

# --- art primitives, reused verbatim from v1 (aliased, never copied) -------
_pit = TB._pit
_earth_field = TB._earth_field
_interior = TB._interior
_soldier = TB._soldier
_horse = TB._horse
_china = TB._china
_script_sheet = TB._script_sheet

# The v1 map's landmass fill is (226,222,208) on a PAPER2 page of (236,234,226):
# ten values apart. Measured on the rendered b11 frame the landmass was
# indistinguishable from the page, so a map that fills 70% of the frame read
# as a shapeless pale blob -- the beat was "here is the empire he took" and
# there was no visible empire. Same outline, landmass drawn in a warm sand
# that separates from the page by ~60 values, with a heavier outline.
_MAP_SHAPE = [(-330, -110), (-250, -215), (-120, -240), (-20, -200),
              (110, -235), (250, -190), (320, -80), (300, 60), (250, 190),
              (120, 235), (-30, 210), (-160, 240), (-290, 170), (-345, 20)]


def _china2(d, cx, cy, s, seed, kingdoms=False, unify=False):
    """The v1 landmass outline, re-filled so it reads against the page."""
    outline = [(cx + px * s, cy + py * s) for px, py in _MAP_SHAPE]
    PA.fill_poly(PA.img_of(d), outline, (206, 186, 148), seed=seed, value=0.07)
    PA.hand_stroke(d, outline, INK, 7, closed=True, seed=seed + 1,
                   wavelength=190.0)
    if kingdoms:
        for k in range(9):
            px = cx - 300 * s + (k * 251) % (560 * s)
            py = cy - 190 * s + (k * 137) % (360 * s)
            w = 70 * s + (k % 3) * 22 * s
            h = 60 * s + (k % 4) * 18 * s
            PA.fill_rect(PA.img_of(d), [px, py, px + w, py + h],
                         (178, 84, 66), seed=seed + 10 + k, value=0.08,
                         edge=2.0)
    elif unify:
        PA.fill_poly(PA.img_of(d), outline, (204, 96, 70), seed=seed + 2,
                     value=0.07)
        PA.hand_stroke(d, outline, INK, 7, closed=True, seed=seed + 3,
                       wavelength=190.0)
_weight = TB._weight
_throne = TB._throne
_flames = TB._flames
_book = TB._book
_crane = TB._crane

# Every moving element uses this one duration. 0.45-0.6s reads as a deliberate
# move; longer and the picture starts changing every sampled frame, which is the
# defect this whole rebuild exists to remove.
ARRIVE = 0.52


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
    # STAGE A  b01-b05  "Beneath this field, eight thousand soldiers.       #
    #   They are clay, and they are perfect. They stand one way for two      #
    #   thousand years. Their paint left them centuries after burial.        #
    #   They are called the Terracotta Army."                                #
    # The frame repaints five times in 15s but the WORLD is one place: the    #
    # black the ranks recede into. v1 gave the far ranks a whole full-frame  #
    # beat and then re-drew a bigger version of the same idea on b02; here    #
    # the receding mass is the backdrop and the beats build TOWARD the        #
    # viewer -- far ranks, then one big soldier cropped by the right edge,   #
    # then the lit row, then the paint leaving him, then the name.            #
    # ===================================================================== #
    def a_pit(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 130, wall=EARTH)
        # A dark card needs a lit stone course at the head for the near-black
        # title to read against. Drawn before the ranks so the backdrop stays
        # UNDER the art (scene_common.title_backdrop).
        SC.title_backdrop(tile, 1130, col=(118, 92, 70))
        # two receding ranks already standing in the dark when we arrive: this
        # is the "eight thousand" the hook caption talks over, and it stops b01
        # from being four seconds of bare black (which the coverage gate called
        # NO ART, correctly).
        for row, (base, hgt, col, shd) in enumerate((
                (600, 380, (150, 92, 52), (110, 66, 38)),
                (470, 270, (96, 60, 36), (68, 42, 26)))):
            for c in range(-1, 6):
                _soldier(d, 90 + c * 230 + row * 46, base, hgt,
                         140 + row * 30 + c, col=col, shade=shd,
                         has_bow=(c % 2 == 0), has_armour=False)
    els.append(SC.stage(clock, 1, a_pit, j=6))

    def a_place(tile, fw, fh):
        # The location, said once and gone in a beat. It is the only exterior
        # fact the hook carries and the rest of the chapter is underground.
        D.draw_label(tile, "OUTSIDE XI'AN, CHINA", center=(640, 150),
                     color=PALE, size=34)
    els.append(SC.layer(clock, 1, a_place, j=2, kind='shape',
                        eid='a_place'))
    els.append(cap(1, 640, 664, size=32, fill=PALE))

    # The presenter is here from b01, not from an emotional beat later: four
    # seconds of bare pit reads as "nothing is happening".
    def a_face_a(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 236, 430, 150, 'confused', 110)
    els.append(E3.E('a_face_a', 'character', a_face_a, at=T(1),
                    until=T(4),
                    motion=SC.enter(clock, 1, dx=-150, dy=30, dur=0.55)))

    # MOVING. The single soldier cropped by the right edge is the reveal of
    # the whole chapter. He is 640 tall against a 470 rank -- the step in scale
    # IS the beat -- and cropped so the frame admits the army continues past it.
    def a_soldier(tile, fw, fh):
        _soldier(ImageDraw.Draw(tile), 1090, 740, 640, 111, has_bow=True)
    els.append(SC.accrue(clock, 2, 6, a_soldier, kind='shape',
                         eid='a_soldier',
                         motion=SC.enter(clock, 2, dx=0, dy=64, dur=0.55)))

    def a_row(tile, fw, fh):
        # The lit rank coming forward. Drawn AFTER the big soldier but placed
        # clear of him -- its rightmost figure ends at x=969, his torso starts
        # at 1023 -- so the foreground read survives.
        d = ImageDraw.Draw(tile)
        for c in range(6):
            _soldier(d, 20 + c * 180, 700, 470, 150 + c,
                     has_bow=(c % 2 == 1), has_armour=False)
    els.append(SC.accrue(clock, 3, 6, a_row, kind='shape', eid='a_row'))
    els.append(cap(3, 640, 664, size=32, fill=PALE))

    def a_flakes(tile, fw, fh):
        # The paint leaving him. Accrues ON TOP of the figure rather than
        # replacing it, because it is paint ON that figure, not a second object
        # in the same place. PALE, not v1's GOLD: GOLD (206,158,74) on CLAY
        # (196,118,66) measures ~1.2:1 and the flakes were invisible at ship
        # size -- a defect v1 shipped.
        d = ImageDraw.Draw(tile)
        for k in range(18):
            fx = 900 + (k * 137) % 320
            fy = 250 + (k * 91) % 380
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 16, 9, n=14), PALE,
                         seed=115 + k, value=0.05, edge=0.6)
    els.append(SC.accrue(clock, 4, 6, a_flakes, kind='shape', eid='a_flakes'))

    def a_name(tile, fw, fh):
        D.draw_label(tile, 'TERRACOTTA ARMY', center=(640, 152),
                     color=PALE, size=60)
    els.append(SC.layer(clock, 5, a_name, j=6, kind='shape', eid='a_name'))
    els.append(cap(5, 640, 664, size=32, fill=PALE))

    # ===================================================================== #
    # STAGE B  b06-b10  "Eight thousand soldiers in the dark. Six hundred    #
    #   horses stood beside them. They stand in long rows, in earthen pits.  #
    #   They are all guarding one man. His name is Qin Shi Huang."           #
    # Depth is built BACK TO FRONT in beat order, which is the only order     #
    # that works: a later element draws over an earlier one, so anything that #
    # arrives at b08 must be NEARER than what arrived at b06. Hence the rank   #
    # at b06 (back), the horses at b07 (middle), and at b08 the front rank    #
    # plus the pit lip that cuts across everybody's feet.                     #
    # ===================================================================== #
    def b_pit(tile, fw, fh):
        _pit(tile, 137, wall=EARTH_D)
        SC.title_backdrop(tile, 1371, col=(118, 92, 70))
    els.append(SC.stage(clock, 6, b_pit, j=11))

    def a_number(tile, fw, fh):
        # v1 drew '8,000' at y=660, straight across the near rank's shins.
        # GOLD on CLAY is ~1.2:1 there; moved up onto the black above the heads
        # it is 4.6:1.
        D.draw_label(tile, '8,000', center=(640, 168), color=GOLD, size=64)
    els.append(SC.layer(clock, 6, a_number, j=7, kind='shape',
                        eid='b_number'))

    def b_rank(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        for c in range(6):
            _soldier(d, 150 + c * 190, 690, 460, 200 + c,
                     has_bow=(c % 2 == 0), has_armour=True)
    els.append(SC.accrue(clock, 6, 11, b_rank, kind='shape', eid='b_rank'))

    def b_horses(tile, fw, fh):
        # The near horse is CROPPED by the left edge and runs nearly the full
        # height: a complete animal in the middle of the frame reads as a model
        # on a plinth, which is what a museum case looks like.
        d = ImageDraw.Draw(tile)
        _horse(d, 190, 700, 460, 201, facing=-1)
        _horse(d, 1150, 706, 360, 202, col=CLAY_L, shade=EARTH, facing=-1)
    els.append(SC.accrue(clock, 7, 11, b_horses, kind='shape', eid='b_horses'))

    def a_count(tile, fw, fh):
        D.draw_label(tile, '600 HORSES', center=(430, 172), color=PALE,
                     size=44)
    els.append(SC.layer(clock, 7, a_count, j=9, kind='shape',
                        eid='b_count'))

    def b_front(tile, fw, fh):
        # "long rows, in earthen pits": the nearest rank, in the middle of the
        # frame where the horses are not, plus the pit lip we are looking over.
        d = ImageDraw.Draw(tile)
        for c in range(4):
            _soldier(d, 400 + c * 160, 745, 390, 210 + c, has_armour=False)
        PA.fill_rect(tile, [0, 690, W, 720], EARTH_D, seed=214, value=0.06)
        PA.hand_stroke(d, [(-10, 690), (1290, 690)], INK, 6, closed=False,
                       seed=215, wavelength=190.0)
    els.append(SC.accrue(clock, 8, 11, b_front, kind='shape', eid='b_front'))

    def b_guard(tile, fw, fh):
        # MOVING. The one living figure among the clay, cropped by the bottom
        # edge, standing in the aisle he is being guarded for.
        SC.fullbody(ImageDraw.Draw(tile), 470, 812, 380, pose='shrug',
                    expression='awed', seed=250)
    els.append(SC.accrue(clock, 9, 11, b_guard, kind='character',
                         eid='b_guard',
                         motion=SC.enter(clock, 9, dx=0, dy=48, dur=ARRIVE)))

    def b_one(tile, fw, fh):
        D.draw_label(tile, 'ONE MAN', center=(640, 172), color=GOLD, size=40)
    els.append(SC.layer(clock, 9, b_one, j=10, kind='shape', eid='b_one'))

    def b_emperor(tile, fw, fh):
        # The emperor arrives as a large gold figure on the right, in front of
        # his army. Off-centre on purpose: dead centre put his head behind the
        # label chain and the presenter at x=470 behind his shoulder.
        _soldier(ImageDraw.Draw(tile), 980, 930, 780, 253, col=GOLD,
                 shade=(150, 110, 52), has_armour=True)
    els.append(SC.accrue(clock, 10, 11, b_emperor, kind='shape',
                         eid='b_emperor'))

    def b_name(tile, fw, fh):
        D.draw_label(tile, 'QIN SHI HUANG', center=(400, 152), color=GOLD,
                     size=50)
    els.append(SC.layer(clock, 10, b_name, j=11, kind='shape', eid='b_name'))
    els.append(cap(10, 400, 250, size=30, fill=PALE))

    # ===================================================================== #
    # STAGE C  b11-b16  "This is Qin Shi Huang. He was the first emperor.   #
    #   In 221 BC he took the throne. He gave the hundred warring kingdoms   #
    #   one script, one set of weights, one ruler: himself."                 #
    # Register change: light paper. The stage opens on PAPER2 and stays there #
    # for b11-b14, then b15 and b16 cut to full-frame DARK REPLACES -- the     #
    # weights and the throne are night shots, and the frame has to repaint to #
    # say so. Those two replaces also hide the presenter, which is fine: he    #
    # has done his job pointing at the map.                                  #
    # ===================================================================== #
    def c_paper(tile, fw, fh):
        _interior(tile, 254, PAPER2)
    els.append(SC.stage(clock, 11, c_paper, j=17))

    def c_presenter(tile, fw, fh):
        # MOVING. He walks in and points; the map he is pointing at is
        # replaced twice under his hand, which is the point of the beat.
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 300, 700, 470, pose='pointing', expression='neutral',
                    seed=260)
        # The bubble sits in the clear band between the presenter's head and
        # the map's western shoulder. At (185, 148) the full-res frame showed
        # it clipped to 'FIRST EM' at the left frame edge -- draw_bubble lays
        # the word out wider than max_w implies once its own padding is added,
        # so a bubble whose CENTRE is at x=185 runs off x=0. Centred at 320 it
        # spans roughly 130-510, inside the frame and clear of both the
        # presenter (x 240-360 at the head) and the landmass (west edge 250,
        # but the shoulder at that height is further right).
        D.draw_bubble(tile, 'FIRST EMPEROR', (330, 105), tail_to=(330, 230),
                      font_size=30, max_w=340)
    els.append(SC.accrue(clock, 11, 15, c_presenter, kind='character',
                         eid='c_presenter',
                         motion=SC.enter(clock, 11, dx=-120, dy=0,
                                         dur=ARRIVE)))

    def c_map1(tile, fw, fh):
        _china2(ImageDraw.Draw(tile), 700, 470, 1.30, 255)
    # Re-framed from (780, 400) at s=1.35, then dropped again to cy=470. The
    # landmass top edge sits at cy-240*s = 470-312 = 158, which clears a band
    # across the top of the frame for the FIRST EMPEROR bubble -- at cy=420
    # the top edge was 108 and the bubble slid under the map's shoulder. The
    # landmass runs 250-1150, clear of the presenter at x=300.
    els.append(SC.layer(clock, 11, c_map1, j=12, kind='shape',
                        eid='c_map1'))

    def c_map2(tile, fw, fh):
        # "In 221 BC he took the throne": the map broken into the old powers
        # and crossed out. NO drawn '221 BC' -- the caption at b12 says it.
        d = ImageDraw.Draw(tile)
        _china2(d, 700, 452, 1.40, 259)
        for k in range(5):
            bx = 420 + k * 110
            by = 250 + k * 34
            PA.fill_poly(tile, [(bx, by), (bx + 62, by - 16),
                                (bx + 62, by + 74), (bx, by + 90)],
                         CLAY_D, seed=261 + k, value=0.12)
            D.draw_red_x(tile, [bx - 8, by - 22, bx + 70, by + 96], width=8)
    els.append(SC.layer(clock, 12, c_map2, j=13, kind='shape',
                        eid='c_map2'))
    els.append(cap(12, 640, 676, size=32))

    def c_map3(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _china2(d, 640, 436, 1.35, 276, kingdoms=True)
        for k in range(9):
            x0 = 500 + (k % 3) * 150
            y0 = 260 + (k // 3) * 110
            D.draw_arrow(tile, (x0, y0), (x0 + 120, y0 - 40), color=INK,
                         width=11, head=44)
        # PAPER2 keyline, not a halo: the map's own outline runs straight
        # through this word, and an outline in the ground colour is what
        # clears the line out from under the glyphs instead of adding a glow.
        D.draw_label(tile, 'A HUNDRED KINGDOMS', center=(640, 656),
                     color=INK, size=36, outline=PAPER2, outline_w=9)
    els.append(SC.layer(clock, 13, c_map3, j=14, kind='shape',
                        eid='c_map3'))

    def c_map4(tile, fw, fh):
        # NOT unify=True. v1's unify floods the entire landmass solid red,
        # which at s=1.35 turns the beat into one red blob and swallows both the
        # road and the script sheet -- and the beat is not "the map turned red",
        # it is "he gave them one script". So the outline stays plain, and the
        # unification is carried by the single road running the whole width and
        # the one sheet of writing beside it. PAPER2 keyline on the word
        # because the map outline runs through it.
        d = ImageDraw.Draw(tile)
        _china2(d, 640, 436, 1.35, 281)
        PA.hand_stroke(d, [(240, 560), (520, 520), (760, 500), (1040, 470)],
                       INK, 12, closed=False, seed=282, wavelength=150.0)
        _script_sheet(d, 1050, 200, 290, 370, 283)
        D.draw_label(tile, 'ONE SCRIPT', center=(1050, 470), color=INK,
                     size=34, outline=PAPER2, outline_w=9)
    els.append(SC.layer(clock, 14, c_map4, j=15, kind='shape',
                        eid='c_map4'))
    els.append(cap(14, 640, 676, size=32))

    def c_weights(tile, fw, fh):
        # Full-frame REPLACE: night. The weights are the one thing in the
        # chapter that is literally a measuring instrument, so they get the
        # dark, lit-from-above register v1 gave them.
        d = ImageDraw.Draw(tile)
        _interior(tile, 284, (74, 58, 46))
        SC.title_backdrop(tile, 1284, col=(118, 92, 70))
        for k, (x, w, h, kind) in enumerate(((300, 120, 250, 0),
                                             (560, 100, 320, 1),
                                             (760, 140, 200, 2),
                                             (990, 110, 280, 0))):
            _weight(d, x, 700, w, h, 290 + k, kind=kind)
            D.draw_label(tile, 'III', center=(x, 700 - h - 34),
                         color=PALE, size=28)
        D.draw_label(tile, 'ONE SET OF WEIGHTS', center=(640, 120),
                     color=GOLD, size=40)
    els.append(SC.layer(clock, 15, c_weights, j=16, kind='bg',
                        eid='c_weights'))

    def c_throne(tile, fw, fh):
        # Full-frame REPLACE: the man himself, off-centre, cropped in on the
        # left by a close-up with nothing on its face. v1's staging, kept --
        # it is the best-executed card in the chapter.
        d = ImageDraw.Draw(tile)
        _interior(tile, 295, (54, 40, 32))
        SC.title_backdrop(tile, 1295, col=(118, 92, 70))
        _throne(d, 930, 760, 620, 296)
        SC.closeup(d, 400, 330, 175, 'deadpan', 297)
        D.draw_bubble(tile, 'himself', (930, 200), tail_to=(830, 380),
                      font_size=34, max_w=260)
    els.append(SC.layer(clock, 16, c_throne, j=17, kind='bg',
                        eid='c_throne'))
    els.append(cap(16, 640, 676, size=32, fill=PALE))

    # ===================================================================== #
    # STAGE D  b17-b20  "He burned every book. He buried the scholars alive. #
    #   In 246 BC he began a tomb for himself, and it took decades of unpaid #
    #   labour."                                                            #
    # One bright exterior register for all four beats: the mound is already  #
    # standing in the backdrop, so b19's date is a label and b20's carriers   #
    # walk in front of a thing we have been looking at since the stage opened.#
    # ===================================================================== #
    def d_field(tile, fw, fh):
        _earth_field(tile, 355, sky=(198, 206, 214), ground=EARTH,
                     hz=int(H * 0.44))
        d = ImageDraw.Draw(tile)
        # The mound, truncated by the bottom edge, with its rammed-earth
        # courses. It is the backdrop rather than an arrival so that b20's
        # carriers have something to be small against.
        PA.fill_poly(tile, [(150, 720), (470, 232), (810, 232), (1140, 720)],
                     EARTH_D, seed=356, value=0.10)
        for k in range(6):
            yy = 262 + k * 66
            inset = int((yy - 232) * 0.55)
            PA.hand_stroke(d, [(180 + inset, yy), (1110 - inset, yy)],
                           EARTH, 7, closed=False, seed=360 + k,
                           wavelength=170.0)
        PA.hand_stroke(d, [(150, 720), (470, 232), (810, 232), (1140, 720)],
                       INK, 7, closed=False, seed=370, wavelength=190.0)
    els.append(SC.stage(clock, 17, d_field, j=21))

    def d_fire(tile, fw, fh):
        # Bottom-left foreground, big enough to be the subject. v1's version was
        # a 420px fire in the corner of a 1280px frame, which is the "timid
        # prop in an empty field" defect this project has paid for before.
        # Here the fire and the books it is eating run up the left third and
        # are cropped by the left and bottom edges.
        d = ImageDraw.Draw(tile)
        _flames(d, 330, 740, 620, 301)
        _book(d, 60, 590, 230, 140, 302, tilt=-0.05)
        _book(d, 300, 640, 200, 124, 303, tilt=0.04)
        _book(d, 540, 604, 180, 112, 304, tilt=-0.03)
        D.draw_label(tile, 'EVERY BOOK', center=(640, 150), color=FIRE,
                     size=42)
    els.append(SC.layer(clock, 17, d_fire, j=18, kind='shape',
                        eid='d_fire'))

    def d_scholars(tile, fw, fh):
        # The pit, the robed figure in it, and the presenter recoiling at the
        # left edge. MOVING on the character only -- the pit is scenery.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(300, 720), (360, 480), (900, 460), (980, 720)],
                     PIT, seed=310, value=0.10)
        PA.fill_poly(tile, [(620, 470), (700, 216), (790, 216), (800, 470)],
                     (122, 92, 62), seed=311, value=0.09)
        d.ellipse([686, 186, 734, 240], fill=(176, 142, 106))
        SC.fullbody(d, 190, 742, 380, pose='recoil', expression='worried',
                    seed=312)
    els.append(SC.accrue(clock, 18, 21, d_scholars, kind='character',
                         eid='d_scholars',
                         motion=SC.enter(clock, 18, dx=-140, dy=0,
                                         dur=ARRIVE)))
    els.append(cap(18, 230, 200, size=30))

    def d_date(tile, fw, fh):
        D.draw_label(tile, '246 BC', center=(240, 210), color=INK, size=40)
    els.append(SC.layer(clock, 19, d_date, j=21, kind='shape', eid='d_date'))

    def d_carriers(tile, fw, fh):
        # MOVING. Eighteen men carrying the mound that is already standing
        # behind them -- two rows, the back row smaller and higher so the rows
        # read as receding rather than as one crowd.
        d = ImageDraw.Draw(tile)
        for row, (base, hgt, y) in enumerate(((690, 160, 690),
                                             (636, 121, 636))):
            for c in range(9):
                x = 70 + c * 148 + row * 62
                _soldier(d, x, base, hgt, 320 + row * 20 + c, col=CLAY,
                         shade=CLAY_D, has_armour=False)
                PA.hand_stroke(d, [(x - 52, y - hgt * 0.52),
                                   (x + 52, y - hgt * 0.52)], INK, 5,
                               closed=False, seed=330 + row * 20 + c,
                               wavelength=70.0)
                for s in (-1, 1):
                    PA.fill_poly(tile, [(x + s * 46, y - hgt * 0.52),
                                        (x + s * 62, y - hgt * 0.52 + 22),
                                        (x + s * 46, y - hgt * 0.52 + 44)],
                                 CLAY_D, seed=340 + row * 20 + c + s,
                                 value=0.10)
    els.append(SC.accrue(clock, 20, 21, d_carriers, kind='shape',
                         eid='d_carriers',
                         motion=SC.enter(clock, 20, dx=0, dy=40,
                                         dur=ARRIVE)))
    els.append(cap(20, 640, 152, size=34))

    # ===================================================================== #
    # STAGE E  b21-b25  "He copied a pyramid. He built himself a heavenly    #
    #   palace. He is buried outside Xi'an. They were made to be different -- #
    #   every soldier a different height. No two faces the same."             #
    # One NIGHT backdrop for the whole stage. NO caption anywhere in it: every #
    # one of these five beats is an object on screen carrying its own words,  #
    # and adding narration text on top of a label is how a card ends up with   #
    # two things to read. That is five consecutive dropped beats and it is the #
    # right call -- this stage is the most purely visual stretch in the chapter.
    # ===================================================================== #
    def e_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 44, 66), seed=380, value=0.08)
        PA.paper_overlay(tile, seed=381)
        for k in range(40):
            sx = (k * 197) % W
            sy = 96 + (k * 83) % 300
            sr = 2 + (k % 3)
            PA.fill_poly(tile, PA.ellipse_pts(sx, sy, sr, sr, n=10),
                         (226, 228, 236), seed=382 + k, value=0.05)
        # AFTER the stars, per v1's c_palace: the lit course has to be the
        # topmost thing in the band or the stars punch holes in it.
        SC.title_backdrop(tile, 1382, col=(86, 88, 116))
        PA.fill_poly(tile, PA.ellipse_pts(1000, 150, 92, n=48), (238, 234, 216),
                     seed=384, value=0.06)
        for k, (cy, hh) in enumerate(((300, 26), (348, 20), (396, 30))):
            PA.fill_rect(tile, [760, cy, 1240, cy + hh], (58, 58, 82),
                         seed=385 + k, value=0.07)
        PA.fill_rect(tile, [0, 430, W, H], (30, 28, 34), seed=390, value=0.07)
        PA.hand_stroke(d, [(-10, 430), (1290, 430)], INK, 6, closed=False,
                       seed=391, wavelength=210.0)
        # the mound, cropped by the left edge, and beside it a stepped pyramid
        # cropped by the right: the comparison the beat is making
        PA.fill_poly(tile, [(60, 720), (300, 300), (620, 300), (860, 720)],
                     (34, 30, 28), seed=392, value=0.08)
        PA.hand_stroke(d, [(60, 720), (300, 300), (620, 300), (860, 720)],
                       INK, 6, closed=False, seed=393, wavelength=170.0)
        for k in range(5):
            PA.fill_rect(tile, [1130 + k * 34, 700 - k * 76, 1320,
                                700 - k * 76 + 76], (72, 64, 58),
                         seed=394 + k, value=0.07)
        PA.hand_stroke(d, [(1130, 720), (1130, 320)], INK, 6, closed=False,
                       seed=399, wavelength=150.0)
    els.append(SC.stage(clock, 21, e_night, j=26))

    def e_copied(tile, fw, fh):
        D.draw_label(tile, 'COPIED A PYRAMID', center=(640, 150), color=GOLD,
                     size=40)
    els.append(SC.layer(clock, 21, e_copied, j=22, kind='shape',
                        eid='e_copied'))

    def e_palace(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-40, 720), (240, 470), (640, 420), (1040, 470),
                            (1320, 720)], (86, 36, 32), seed=400, value=0.10)
        PA.hand_stroke(d, [(-40, 720), (240, 470), (640, 420), (1040, 470),
                           (1320, 720)], INK, 7, closed=False, seed=401,
                       wavelength=200.0)
    els.append(SC.accrue(clock, 22, 26, e_palace, kind='shape',
                         eid='e_palace'))

    def e_palace_name(tile, fw, fh):
        # The roof ACCRUES; its NAME does not. While the word lived inside the
        # accrue it was still on screen at b24 and b25, underneath 'ALL
        # DIFFERENT' and 'NO TWO THE SAME' -- two labels welded together at
        # (640,150). Text always hands off; scenery never does.
        D.draw_label(tile, 'HEAVENLY PALACE', center=(640, 150), color=GOLD,
                     size=44)
    els.append(SC.layer(clock, 22, e_palace_name, j=24, kind='shape',
                        eid='e_palace_name'))

    def e_xian(tile, fw, fh):
        # MOVING. The locator slides in as a PAPER INSET -- a panel of the
        # record register dropped onto the night, which is how you say "this
        # place is on a map" without leaving the shot.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [760, 300, 1260, 660], (240, 238, 228), seed=410,
                     value=0.05)
        PA.hand_stroke(d, [(760, 300), (1260, 300), (1260, 660), (760, 660)],
                       INK, 5, closed=True, seed=411, wavelength=160.0)
        PA.fill_rect(tile, [800, 350, 1010, 520], (206, 200, 186), seed=412,
                     value=0.06)
        for k in range(9):
            PA.fill_rect(tile, [800 + k * 24, 342, 812 + k * 24, 352],
                         (150, 144, 132), seed=413 + k, value=0.06)
        PA.hand_stroke(d, [(1010, 430), (1200, 404)], INK, 8, closed=False,
                       seed=422, wavelength=110.0)
        PA.fill_rect(tile, [1150, 370, 1260, 500], (150, 104, 66), seed=424,
                     value=0.08)
        PA.hand_stroke(d, [(1150, 370), (1260, 370), (1260, 500), (1150, 500)],
                       INK, 5, closed=True, seed=425, wavelength=120.0)
        D.draw_label(tile, "XI'AN", center=(900, 588), color=INK, size=26)
        D.draw_label(tile, 'OUTSIDE', center=(1205, 588), color=INK, size=24)
    els.append(SC.accrue(clock, 23, 26, e_xian, kind='shape', eid='e_xian',
                         motion=SC.enter(clock, 23, dx=90, dy=0,
                                         dur=ARRIVE)))

    def e_heights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # a measuring stick, clipped at y=104 rather than y=0 so it stays clear
        # of the title band
        PA.fill_rect(tile, [700, 104, 748, 680], (216, 208, 188), seed=430,
                     value=0.05)
        for k in range(9):
            PA.fill_rect(tile, [700, 120 + k * 62, 748, 128 + k * 62],
                         (120, 106, 88), seed=431 + k, value=0.06)
        for x, hgt in ((170, 440), (400, 370), (620, 500)):
            _soldier(d, x, 680, hgt, 440 + x, col=CLAY, shade=CLAY_D,
                     has_armour=False)
        D.draw_label(tile, 'ALL DIFFERENT', center=(640, 150), color=GOLD,
                     size=38)
    els.append(SC.layer(clock, 24, e_heights, j=25, kind='shape',
                        eid='e_heights'))

    def e_faces(tile, fw, fh):
        # Two heads cropped by the side edges, the way a portrait pair is
        # actually cropped. Feet at 900 with h=780 puts the head tops at y=96,
        # clear of the 0-73 title band -- v1 used h=820 and reached y=54, which
        # put two heads inside the band.
        d = ImageDraw.Draw(tile)
        _soldier(d, 60, 900, 780, 450, col=CLAY, shade=CLAY_D,
                 has_armour=False)
        _soldier(d, 1220, 900, 780, 451, col=CLAY_L, shade=EARTH,
                 has_armour=False)
        d.line([(30, 214), (92, 226)], fill=CLAY_D, width=7)      # moustache
        d.line([(1196, 232), (1252, 246)], fill=CLAY_D, width=6)  # scar
        D.draw_label(tile, 'NO TWO THE SAME', center=(640, 150), color=PALE,
                     size=40)
    els.append(SC.layer(clock, 25, e_faces, j=26, kind='shape',
                        eid='e_faces'))

    # ===================================================================== #
    # STAGE F  b26-b31  "They were still there. Two thousand years. Then, in #
    #   1974, a group of farmers was digging a well. They hit something hard. #
    #   It was a clay shoulder. And then it broke."                           #
    # The SURVEY register: blueprint-blue sky, pale earth. One light backdrop #
    # for six beats, and the dig goes DOWNWARD through the frame -- outline,   #
    # well, blade, shoulder, break, cover -- so the stage has a direction even #
    # though the camera never moves.                                          #
    # ===================================================================== #
    def f_field(tile, fw, fh):
        _earth_field(tile, 560, sky=BLUE_L, ground=(178, 152, 118), hz=520)
    els.append(SC.stage(clock, 26, f_field, j=32))

    def f_outline(tile, fw, fh):
        # An empty rectangle of ground. v1's beat, and it earns its place: it
        # is the two-thousand-years beat and there is nothing to look at yet,
        # which IS the joke.
        d = ImageDraw.Draw(tile)
        PA.hand_stroke(d, [(180, 470), (900, 466), (980, 600), (150, 604)],
                       EARTH_D, 8, closed=True, seed=570, wavelength=180.0)
        D.draw_label(tile, '2,000 YEARS', center=(880, 250), color=GOLD,
                     size=40)
    els.append(SC.layer(clock, 26, f_outline, j=27, kind='shape',
                        eid='f_outline'))

    def f_face_a(tile, fw, fh):
        # MOVING. Bottom-left, small, and it never gets in the way of the dig:
        # the face spans x -142..262 and the well starts at 820.
        SC.closeup(ImageDraw.Draw(tile), 60, 600, 130, 'confused', 310)
    els.append(E3.E('f_face_a', 'character', f_face_a, at=T(26), until=T(29),
                    motion=SC.enter(clock, 26, dx=-150, dy=0, dur=0.55)))
    # The swap: same position, same size, one beat later -- confusion becoming
    # shock is the whole point of the clay-shoulder beat.
    _fbu, _faa, _fau = SC.expr_swap(clock, 29, 'confused', 'shock',
                                    until_j=31)

    def f_face_b(tile, fw, fh):
        SC.closeup(ImageDraw.Draw(tile), 60, 600, 130, 'shock', 310)
    els.append(E3.E('f_face_b', 'character', f_face_b, at=_faa, until=_fau))

    def f_well(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(820, 720), (860, 540), (1160, 540), (1200, 720)],
                     EARTH_D, seed=580, value=0.10)
        PA.hand_stroke(d, [(840, 540), (1180, 540)], INK, 7, closed=False,
                       seed=581, wavelength=140.0)
        for x, hgt in ((540, 400), (700, 380)):
            SC.fullbody(d, x, 700, hgt, pose='pointing', expression='neutral',
                        seed=582 + x)
            PA.hand_stroke(d, [(x + 40, 700 - hgt * 0.62),
                               (x + 96, 700 - hgt * 0.86)], INK, 7,
                           closed=False, seed=583 + x, wavelength=60.0)
            PA.fill_poly(tile, [(x + 90, 700 - hgt * 0.86),
                                (x + 124, 700 - hgt * 0.90),
                                (x + 112, 700 - hgt * 0.70),
                                (x + 84, 700 - hgt * 0.74)], (128, 106, 80),
                         seed=584 + x, value=0.08)
        D.draw_label(tile, '1974', center=(240, 140), color=INK, size=52)
    els.append(SC.layer(clock, 27, f_well, j=28, kind='character',
                        eid='f_well'))
    els.append(cap(27, 1080, 190, size=32))

    def f_blade(tile, fw, fh):
        # MOVING. The blade comes in from off-frame left. A shovel is about
        # 300px tall, which is the size the motion rule actually wants.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-60, 300), (120, 250), (300, 330), (280, 470),
                            (100, 500), (-60, 440)], (128, 106, 80),
                     seed=590, value=0.09)
        PA.hand_stroke(d, [(280, 380), (620, 470)], (110, 88, 64), 16,
                       closed=False, seed=591, wavelength=120.0)
        PA.fill_poly(tile, PA.ellipse_pts(700, 420, 190, 150, n=40),
                     (176, 106, 66), seed=592, value=0.08)
        D.draw_label(tile, 'SOMETHING HARD', center=(900, 200), color=INK,
                     size=40)
    els.append(SC.layer(clock, 28, f_blade, j=29, kind='shape',
                        eid='f_blade',
                        motion=SC.enter(clock, 28, dx=-70, dy=0,
                                        dur=ARRIVE)))

    def f_shoulder(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _soldier(d, 950, 800, 620, 600, col=CLAY_L, shade=EARTH,
                 has_armour=False, crop=True)
        for k in range(14):
            PA.fill_poly(tile, PA.ellipse_pts(600 + (k * 173) % 700,
                                              300 + (k * 97) % 340,
                                              13, 8, n=12), EARTH_D,
                         seed=601 + k, value=0.08)
    els.append(SC.accrue(clock, 29, 32, f_shoulder, kind='shape',
                         eid='f_shoulder'))
    els.append(cap(29, 420, 180, size=32))

    def f_break(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(280, 250), (560, 262), (720, 320), (700, 640),
                            (420, 600), (280, 470)], CLAY, seed=610,
                     value=0.09)
        PA.hand_stroke(d, [(470, 250), (500, 350), (470, 420), (510, 520)],
                       INK, 7, closed=False, seed=611, wavelength=90.0)
        for k, (fx, fy, fr) in enumerate(((760, 620, 44), (830, 560, 30),
                                          (700, 680, 26), (860, 640, 20))):
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, fr, fr * 0.7, n=20),
                         CLAY_D, seed=612 + k, value=0.10)
        # INK, not PALE: v1 drew this in PALE on the BLUE_L sky, which measures
        # about 1.35:1 and was unreadable at ship size.
        D.draw_label(tile, 'IT BROKE', center=(1000, 200), color=INK,
                     size=44)
    els.append(SC.layer(clock, 30, f_break, j=31, kind='shape',
                        eid='f_break'))

    def f_cover(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [980, 420, 1340, 640], (206, 200, 186), seed=620,
                     value=0.06)
        PA.hand_stroke(d, [(980, 420), (1340, 420)], INK, 6, closed=False,
                       seed=621, wavelength=120.0)
        PA.fill_poly(tile, [(300, 700), (420, 566), (700, 548), (880, 596),
                            (920, 700)], (176, 172, 162), seed=622,
                     value=0.07)
        PA.hand_stroke(d, [(300, 700), (420, 566), (700, 548), (880, 596),
                           (920, 700)], INK, 6, closed=False, seed=623,
                       wavelength=140.0)
        D.draw_label(tile, 'COVERED OVER', center=(640, 220), color=INK,
                     size=40)
    els.append(SC.layer(clock, 31, f_cover, j=32, kind='shape',
                        eid='f_cover'))

    # ===================================================================== #
    # STAGE G  b32-b37  "In 2012 they opened a new pit. Inside: more than a  #
    #   thousand soldiers. Two bronze cranes had been broken. Somebody        #
    #   repaired them with modern glue. In 1983 a farmer poured acid on the   #
    #   figures, and the markings can never be read again."                  #
    # Opens on PAPER2 for b32, then b33 cuts to a full-frame dark REPLACE for #
    # the pit full -- a thousand figures cannot be drawn on the plan paper --  #
    # and b37 cuts again to flat grey. Three registers in six beats, and each #
    # cut is a thing the narration actually says.                             #
    # ===================================================================== #
    def g_paper(tile, fw, fh):
        _interior(tile, 650, PAPER2)
    els.append(SC.stage(clock, 32, g_paper, j=38))

    def g_corridor(tile, fw, fh):
        # v1 drew this L of two corridors in the middle third of a pale frame and
        # the beat came out nearly blank. Scaled up to run off both side edges
        # and off the bottom, with the vault row reading as a row: the plan is
        # supposed to look BIGGER than the frame, which is what a pit does.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(-60, 720), (-60, 470), (430, 470), (430, 720)],
                     (222, 218, 208), seed=700, value=0.05)
        PA.hand_stroke(d, [(-60, 720), (-60, 470), (430, 470), (430, 720)],
                       INK, 6, closed=True, seed=701, wavelength=140.0)
        PA.fill_poly(tile, [(430, 720), (430, 330), (1340, 330), (1340, 720)],
                     (216, 212, 202), seed=702, value=0.05)
        PA.hand_stroke(d, [(430, 720), (430, 330), (1340, 330), (1340, 720)],
                       INK, 6, closed=True, seed=703, wavelength=160.0)
        for k in range(8):
            vx = 500 + k * 108
            PA.fill_rect(tile, [vx, 380, vx + 72, 476], (196, 190, 178),
                         seed=704 + k, value=0.05)
            PA.hand_stroke(d, [(vx, 476), (vx + 72, 476)], INK, 5,
                           closed=False, seed=712 + k, wavelength=60.0)
        for k in range(4):
            vx = 30 + k * 108
            PA.fill_rect(tile, [vx, 520, vx + 72, 616], (196, 190, 178),
                         seed=720 + k, value=0.05)
            PA.hand_stroke(d, [(vx, 616), (vx + 72, 616)], INK, 5,
                           closed=False, seed=724 + k, wavelength=60.0)
        # NO drawn 'PIT 1 - 2012': the caption at b32 says it, and saying it
        # twice in one beat is the pile-up this file exists to avoid.
    els.append(SC.accrue(clock, 32, 38, g_corridor, kind='shape',
                         eid='g_corridor'))
    els.append(cap(32, 640, 676, size=32))

    def g_pitfull(tile, fw, fh):
        # v1 drew this as a 5x9 grid of identical 150px soldiers tiled edge to
        # edge, which at ship size reads as WALLPAPER, not as a pit: the figures
        # are all one size, one colour and one silhouette, so the eye finds a
        # repeating motif instead of a thousand men. Four rows at four scales
        # with the near row dominant and cropped, and the far rows dimmed, so
        # the same count of figures now reads as DEPTH. Armour on the near rows
        # breaks the repeated silhouette; it is off on the far rows, where the
        # detail would be invisible anyway.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (104, 82, 60), seed=710, value=0.08)
        PA.paper_overlay(tile, seed=711)
        SC.title_backdrop(tile, 1711, col=(118, 92, 70))
        rows = ((375, 165, 105, (128, 84, 52), (98, 62, 38), False),
                (470, 215, 140, (146, 94, 58), (112, 70, 42), False),
                (600, 290, 190, (170, 108, 64), (128, 80, 48), True),
                (760, 400, 320, CLAY, CLAY_D, True))
        for r, (feet, hgt, step, col, shd, arm) in enumerate(rows):
            x = -40 if r < 3 else -20
            c = 0
            while x < W + 120:
                _soldier(d, x, feet, hgt, 720 + r * 9 + c, col=col,
                         shade=shd, has_armour=arm)
                x += step
                c += 1
        # The label is NOT inside this layer. It gets its own one-beat element
        # below, because this layer lives b33-b37 and a word living in it would
        # still be on screen at b34 and b35, 30px under BOTH BROKEN and
        # REPAIRED WITH MODERN GLUE.
    els.append(SC.layer(clock, 33, g_pitfull, j=38, kind='bg',
                        eid='g_pitfull'))

    def g_thousand(tile, fw, fh):
        # Moved UP out of the figures: at y=672 it lay across the near row's
        # shins, and it has to clear the title band too. y=120 sits in the gap
        # -- band ends at 73, far row head tops begin at 205.
        D.draw_label(tile, '1,000+ SOLDIERS', center=(640, 120), color=PALE,
                     size=40)
    els.append(SC.layer(clock, 33, g_thousand, j=34, kind='shape',
                        eid='g_thousand'))

    def g_cranes(tile, fw, fh):
        # The cranes are v1's primitive and its body is a wide flat ellipse --
        # at this scale the ellipse IS most of the silhouette, which is why
        # v1's version read as an olive on a stick. Two staging changes fix the
        # read without touching the primitive: they sit on the DARK ground in
        # front of the lit grid rather than centred on it, so there is plain
        # background behind the neck and head, and they are pushed to the side
        # edges so nothing important is behind them.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 596, W, H], (74, 58, 44), seed=805, value=0.07)
        PA.hand_stroke(d, [(-10, 596), (1290, 596)], INK, 6, closed=False,
                       seed=806, wavelength=200.0)
        _crane(d, 210, 690, 500, 801, broken=True)
        _crane(d, 1080, 706, 420, 802, broken=True, flip=True)
    els.append(SC.accrue(clock, 34, 38, g_cranes, kind='shape',
                         eid='g_cranes'))

    def g_cranes_name(tile, fw, fh):
        # Separate from the cranes for the same reason as HEAVENLY PALACE: the
        # word has to be gone before REPAIRED WITH MODERN GLUE lands on it.
        D.draw_label(tile, 'BOTH BROKEN', center=(640, 150), color=PALE,
                     size=40)
    els.append(SC.layer(clock, 34, g_cranes_name, j=35, kind='shape',
                        eid='g_cranes_name'))

    def g_repair(tile, fw, fh):
        # REPLACES the two broken cranes, because the repaired crane stands
        # where they stood and drawing both would be two birds in one place.
        # It goes back to the CENTRE here: that is the point of the beat, the
        # bird is whole again, and it is the only moment in the chapter where
        # a crane is the subject rather than a detail.
        d = ImageDraw.Draw(tile)
        _crane(d, 560, 690, 500, 803, broken=True, repaired=True)
        PA.fill_rect(tile, [1060, 330, 1160, 560], (222, 226, 230), seed=804,
                     value=0.05)
        PA.hand_stroke(d, [(1060, 330), (1110, 250), (1160, 330)], INK, 6,
                       closed=False, seed=805, wavelength=60.0)
        PA.hand_stroke(d, [(1110, 380), (1180, 470)], (150, 110, 60), 12,
                       closed=False, seed=806, wavelength=70.0)
        PA.fill_poly(tile, [(1174, 452), (1220, 462), (1210, 512),
                            (1168, 502)], (168, 128, 70), seed=807,
                     value=0.08)
        D.draw_label(tile, 'REPAIRED WITH MODERN GLUE', center=(640, 150),
                     color=PALE, size=34)
    els.append(SC.layer(clock, 35, g_repair, j=36, kind='shape',
                        eid='g_repair'))

    def g_acid(tile, fw, fh):
        # MOVING -- and this is the ONE larger motion the chapter earns. The
        # acid eating a figure is movement that IS the event; a drift on a
        # backdrop would be movement that is decoration.
        # A full-frame REPLACE, not an accrue: the two broken cranes from b34
        # own the right side of this frame, and the acid jar has to stand
        # exactly there. Same part of the frame, so one of them has to go.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (104, 82, 60), seed=810, value=0.08)
        PA.paper_overlay(tile, seed=811)
        SC.title_backdrop(tile, 1811, col=(118, 92, 70))
        PA.fill_rect(tile, [0, 600, W, H], (74, 58, 44), seed=812,
                     value=0.07)
        PA.hand_stroke(d, [(-10, 600), (1290, 600)], INK, 6, closed=False,
                       seed=813, wavelength=200.0)
        _soldier(d, 420, 880, 700, 810, col=(150, 108, 70),
                 shade=(112, 80, 52), has_armour=True)
        # The jar was at x 1130-1320, i.e. two thirds of it off the right edge,
        # so the acid appeared to pour in from nowhere. Brought fully into frame
        # and given a visible neck and shoulder, and the flow thickened, so the
        # beat reads as something POURING ON a figure.
        PA.fill_poly(tile, [(1010, 190), (1250, 190), (1215, 400), (1045, 400)],
                     (150, 150, 146), seed=814, value=0.06)
        PA.hand_stroke(d, [(1130, 190), (1130, 120)], (150, 150, 146), 26,
                       closed=False, seed=817, wavelength=60.0)
        PA.hand_stroke(d, [(1060, 190), (1210, 190), (1180, 400), (1080, 400)],
                       INK, 6, closed=True, seed=818, wavelength=90.0)
        for k, (ax, ay, bx, by, wd) in enumerate((
                (1130, 404, 700, 500, 34), (1120, 410, 520, 560, 20))):
            PA.hand_stroke(d, [(ax, ay), (bx, by)], ACID, wd, closed=False,
                           seed=815 + k, wavelength=140.0)
        for k in range(6):
            PA.fill_poly(tile, PA.ellipse_pts(500 + k * 150, 520 + k * 34,
                                              17, 12, n=16), ACID,
                         seed=830 + k, value=0.05)
        D.draw_label(tile, 'ACID', center=(1130, 520), color=ACID, size=48)
    els.append(SC.layer(clock, 36, g_acid, j=37, kind='bg', eid='g_acid',
                        motion=SC.enter(clock, 36, dx=140, dy=0,
                                        dur=0.55)))
    els.append(cap(36, 640, 676, size=32, fill=PALE))

    def g_gone(tile, fw, fh):
        # Full-frame REPLACE to flat grey. The figure has become the grey it
        # was turned into; the register is the information.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (150, 148, 144), seed=820,
                     value=0.06)
        PA.paper_overlay(tile, seed=821)
        _soldier(d, 700, 820, 640, 846, col=GREY, shade=GREY_D,
                 has_armour=False)
        PA.paper_overlay(tile, 822, bbox=[560, 300, 860, 560])
        SC.fullbody(d, 210, 740, 380, pose='shrug', expression='disgust',
                    seed=823)
        D.draw_label(tile, 'NEVER READABLE AGAIN', center=(760, 150),
                     color=INK, size=36)
    els.append(SC.layer(clock, 37, g_gone, j=38, kind='bg', eid='g_gone'))

    # ===================================================================== #
    # STAGE H  b38-b42  "They took soil samples. Mercury. Enough of it to    #
    #   fill a pool. The old records describe it as a slow poison that never  #
    #   lets go."                                                            #
    # A cold pale lab for b38, then a full-frame dark tunnel REPLACE for the  #
    # pool, then the records and the body are laid back over it. The mercury  #
    # bead gets the stage's motion: it is the smallest subject in the chapter #
    # and the only one where a slow settle reads as an idea rather than a      #
    # transition.                                                            #
    # ===================================================================== #
    def h_lab(tile, fw, fh):
        _interior(tile, 860, (208, 214, 218))
    els.append(SC.stage(clock, 38, h_lab, j=43))

    def h_jar(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 500, W, 760], (176, 182, 186), seed=870,
                     value=0.05)
        PA.hand_stroke(d, [(-10, 500), (1290, 500)], INK, 6, closed=False,
                       seed=871, wavelength=180.0)
        PA.fill_poly(tile, PA.ellipse_pts(640, 300, 180, 300, n=48),
                     (222, 228, 232), seed=872, value=0.05)
        PA.hand_stroke(d, PA.arc_pts(640, 300, 180, 300, 0, 360, n=48) +
                       [(820, 600), (460, 600)], INK, 7, closed=False,
                       seed=873, wavelength=150.0)
        PA.fill_poly(tile, PA.ellipse_pts(640, 560, 160, 40, n=40),
                     (138, 110, 78), seed=874, value=0.08)
        D.draw_label(tile, 'MERCURY', center=(640, 170), color=INK, size=52)
    els.append(SC.layer(clock, 38, h_jar, j=39, kind='shape', eid='h_jar'))

    def h_bead(tile, fw, fh):
        # MOVING. A single bead settling onto the soil sample.
        PA.fill_poly(PA.img_of(ImageDraw.Draw(tile)),
                     PA.ellipse_pts(700, 520, 40, 26, n=28), SILVER,
                     seed=880, value=0.05)
    els.append(SC.layer(clock, 38, h_bead, j=39, kind='shape', eid='h_bead',
                        motion=SC.enter(clock, 38, dx=0, dy=-34,
                                        dur=ARRIVE)))
    els.append(cap(38, 640, 676, size=32))

    def h_pool(tile, fw, fh):
        # Full-frame REPLACE: the tunnel, and a pool of mercury running off the
        # LEFT edge rather than sitting in the middle as a grey lozenge.
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (34, 32, 34), seed=890, value=0.08)
        PA.paper_overlay(tile, seed=891)
        PA.fill_poly(tile, [(-40, 130), (520, 300), (520, 720), (-40, 720)],
                     (58, 54, 52), seed=892, value=0.08)
        PA.fill_poly(tile, [(760, 300), (1320, 130), (1320, 720), (760, 720)],
                     (58, 54, 52), seed=893, value=0.08)
        SC.title_backdrop(tile, 1870, col=(118, 92, 70))
        PA.fill_poly(tile, [(-40, 566), (760, 600), (760, 720), (-40, 720)],
                     SILVER, seed=894, value=0.05)
        for k in range(4):
            PA.hand_stroke(d, [(60 + k * 150, 620 + (k % 2) * 26),
                               (240 + k * 150, 616 + (k % 2) * 26)],
                           (238, 244, 248), 8, closed=False, seed=895 + k,
                           wavelength=80.0)
    els.append(SC.layer(clock, 39, h_pool, j=43, kind='bg', eid='h_pool'))

    def h_pool_label(tile, fw, fh):
        # The gold mercury disc and its label belong to b39-b41 ("enough for a
        # pool"), not to b42. They used to live inside h_pool and so survived
        # into the mercury-dome beat, where a stray gold blob floated over the
        # dome and the words 'ENOUGH FOR A POOL' hung at the frame edge beside
        # 'IT DOES NOT LET GO' -- two labels for two different beats in one
        # frame. This layer ends at b42 so the dome beat has a single label.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, PA.ellipse_pts(900, 250, 46, 46, n=24), GOLD,
                     seed=899, value=0.05)
        D.draw_label(tile, 'ENOUGH FOR A POOL', center=(900, 430),
                     color=SILVER, size=34)
    els.append(SC.layer(clock, 39, h_pool_label, j=42, kind='shape',
                         eid='h_pool_label'))

    def h_records(tile, fw, fh):
        # v1 ran this scroll edge to edge over the tunnel, which left b40 a flat
        # cream field with two grey bars and none of the tunnel left to read as
        # a tunnel. Narrowed to a document lying IN the tunnel, cropped by the
        # bottom edge, so the converging walls and the pool survive around it.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, [(330, 470), (960, 470), (1040, 760), (250, 760)],
                     (246, 240, 224), seed=910, value=0.05)
        PA.hand_stroke(d, [(330, 470), (960, 470)], INK, 7, closed=False,
                       seed=911, wavelength=180.0)
        PA.hand_stroke(d, [(330, 470), (250, 760)], INK, 5, closed=False,
                       seed=912, wavelength=140.0)
        PA.hand_stroke(d, [(960, 470), (1040, 760)], INK, 5, closed=False,
                       seed=913, wavelength=140.0)
        for k, yy in enumerate((560, 646)):
            PA.fill_poly(tile, [(400, yy), (900, yy + 14), (900, yy + 34),
                                (400, yy + 20)], SILVER, seed=914 + k,
                         value=0.05)
    els.append(SC.accrue(clock, 40, 42, h_records, kind='shape',
                         eid='h_records'))
    # Ends at b42 now, not b43. It used to survive into b42, where the pale
    # h_body mass (208,200,186) landed on top of the pale scroll (246,240,224)
    # -- two pale wedges a few values apart merging into one shape, plus the
    # stray gold disc from the tunnel backdrop. The scroll is the b40-b41
    # subject; at b42 the body is.

    def h_records_name(tile, fw, fh):
        # The scroll persists to the end of the stage; its title does not. At
        # b42 IT DOES NOT LET GO arrives at almost the same spot.
        D.draw_label(tile, 'THE OLD RECORDS', center=(640, 140), color=INK,
                     size=38)
    els.append(SC.layer(clock, 40, h_records_name, j=42, kind='shape',
                        eid='h_records_name'))

    def f_droplet(tile, fw, fh):
        # The fingertip stays cropped by the LEFT edge and the presenter stays
        # right; the scroll between them is what he is looking at.
        d = ImageDraw.Draw(tile)
        PA.fill_poly(tile, PA.ellipse_pts(-20, 520, 190, 250, n=44),
                     (238, 226, 206), seed=920, value=0.06)
        PA.fill_poly(tile, PA.ellipse_pts(1090, 420, 34, 34, n=28), SILVER,
                     seed=921, value=0.05)
        SC.fullbody(d, 1120, 820, 400, pose='armscrossed',
                    expression='worried', seed=922)
        # PALE, not INK: this lands on the dark tunnel, where v1's INK word
        # would have been invisible.
        D.draw_label(tile, 'POISON', center=(1090, 250), color=PALE, size=48)
    els.append(SC.layer(clock, 41, f_droplet, j=42, kind='character',
                        eid='f_droplet'))
    els.append(cap(41, 300, 664, size=32))

    def h_body(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "It does not let go." The mercury standing over the body as a
        # domed metal sheet, filling the frame rather than sitting in it. The
        # old shape was a flat pale trapezoid occupying y 386-660 with dark
        # tunnel above and below -- on its own it read as a wedge of light,
        # not a body under metal. Now the sheet is wider, higher and domed,
        # with a bright meniscus along its crest so the mercury reads as a
        # liquid skin, and the dark coffin seam shows through it.
        dome = PA.ellipse_pts(640, 620, 620, 210, n=64)
        PA.fill_poly(tile, dome, (176, 178, 184), seed=930, value=0.08)
        PA.hand_stroke(d, dome, (236, 240, 246), 6, closed=True, seed=931,
                       wavelength=180.0)
        # the body beneath, a dark seam, and mercury beads
        PA.fill_poly(tile, [(430, 560), (850, 560), (880, 700), (400, 700)],
                     (86, 84, 88), seed=934, value=0.06)
        for k in range(6):
            PA.fill_poly(tile, PA.ellipse_pts(340 + k * 140, 600, 16, 11,
                                              n=14), SILVER,
                         seed=932 + k, value=0.05)
        D.draw_label(tile, 'IT DOES NOT LET GO', center=(640, 150),
                     color=PALE, size=40)
    els.append(SC.accrue(clock, 42, 43, h_body, kind='shape',
                         eid='h_body'))

    # ===================================================================== #
    # STAGE I  b43-b45  "The main chamber has never been opened. It is still  #
    #   sealed. And the door stays shut."                                     #
    # The finale is the one place where a DRAWING beats a photograph, so the  #
    # backdrop is a CROSS-SECTION: the mound, the earth, the outer pit where   #
    # the farmers found the shoulder, and the sealed void under all of it.    #
    # The presenter arrives awed in the last beat, cropped by the bottom,     #
    # looking at a door we never see open.                                    #
    # ===================================================================== #
    def i_section(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, 150], (176, 186, 196), seed=990,
                     value=0.07)
        PA.paper_overlay(tile, seed=991)
        PA.fill_rect(tile, [0, 146, W, 320], EARTH, seed=992, value=0.09)
        PA.fill_rect(tile, [0, 316, W, 556], EARTH_D, seed=993, value=0.09)
        PA.fill_rect(tile, [0, 552, W, H], (18, 16, 18), seed=994, value=0.06)
        for yy in (148, 318, 554):
            PA.hand_stroke(d, [(-10, yy), (1290, yy)], INK, 6, closed=False,
                           seed=995 + yy, wavelength=200.0)
        # the outer pit, and the figures in it -- drawn rect FIRST, figures
        # after, so the figures are not painted over by their own pit. The pit
        # is widened and deepened (it used to be a small dark rectangle in a
        # vast flat field) and the mound that encloses the whole section is
        # outlined above ground so the frame reads as a cutaway of a mound
        # rather than three horizontal colour bands.
        PA.fill_poly(tile, [(-40, 150), (250, 96), (640, 60), (1030, 96),
                            (1320, 150), (1320, 40), (-40, 40)],
                     (150, 162, 172), seed=996, value=0.07)
        PA.hand_stroke(d, [(-40, 150), (250, 96), (640, 60), (1030, 96),
                           (1320, 150)], INK, 6, closed=False, seed=997,
                       wavelength=190.0)
        PA.fill_rect(tile, [30, 372, 830, 552], (58, 48, 40), seed=998,
                     value=0.08)
        PA.hand_stroke(d, [(30, 372), (830, 372), (830, 552), (30, 552)], INK,
                       6, closed=True, seed=999, wavelength=170.0)
        for k in range(5):
            _soldier(d, 130 + k * 165, 548, 150, 1000 + k,
                     col=(150, 104, 64), shade=(112, 76, 46), has_armour=False)
        # the sealed void, at the right, running off the bottom edge, with a
        # heavy door slab and its never-crossed threshold
        PA.fill_rect(tile, [880, 470, 1340, 760], (44, 38, 36), seed=1001,
                     value=0.06)
        PA.hand_stroke(d, [(880, 470), (880, 760)], INK, 8, closed=False,
                       seed=1002, wavelength=150.0)
        PA.hand_stroke(d, [(880, 470), (1340, 470)], INK, 8, closed=False,
                       seed=1003, wavelength=150.0)
        PA.fill_rect(tile, [950, 500, 1300, 720], (72, 64, 60), seed=1004,
                     value=0.07)
        PA.hand_stroke(d, [(1120, 500), (1120, 720)], (30, 26, 24), 10,
                       closed=False, seed=1005, wavelength=90.0)
        d.ellipse([1100, 590, 1140, 630], fill=(180, 172, 160))
    els.append(SC.stage(clock, 43, i_section, j=46))

    def i_never(tile, fw, fh):
        D.draw_label(tile, 'NEVER OPENED', center=(1050, 112), color=INK,
                     size=40)
    els.append(SC.layer(clock, 44, i_never, j=45, kind='shape',
                        eid='i_never'))

    def i_shut(tile, fw, fh):
        # MOVING. The presenter, awed, cropped by the bottom edge, arriving at
        # the last thing in the chapter. One entrance, one expression, no
        # swap: the awe is the arrival.
        SC.fullbody(ImageDraw.Draw(tile), 700, 830, 400, pose='peeking',
                    expression='awed', seed=1010)
        D.draw_label(tile, 'THE DOOR STAYS SHUT', center=(400, 112),
                     color=INK, size=44)
    els.append(SC.accrue(clock, 45, 46, i_shut, kind='character',
                         eid='i_shut',
                         motion=SC.enter(clock, 45, dx=0, dy=44,
                                         dur=ARRIVE)))
    els.append(cap(43, 640, 676, size=32, fill=PALE))
    els.append(cap(45, 640, 676, size=32, fill=PALE))

    return SC.finish(els, TITLE, clock, title_seed=53)
