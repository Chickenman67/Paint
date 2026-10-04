"""tomb scene -- the Terracotta Army / the Tomb of Qin Shi Huang, outside Xi'an.

Chapter 3 of the bunker-and-vault film. 45 beats, 118.1s.

STRUCTURE. Everything structural comes from scene_common (caption handoff,
cropped close-up, phrase clock, render drivers); this file declares only the
Tomb's 45 cards. beats.json gives every sentence an exact [start,end] and
MAX_PHRASE_WORDS is 8, so `clock.ph('bNN', 0)[1]` is always the whole caption
and there is never a reason to guess a card boundary.

ONE CARD PER BEAT, EACH CARD PAINTS ITS OWN WHOLE FRAME. Every card function
fills background-to-subject, which makes it structurally impossible for one
card's art to survive into the next.

TWO REGISTERS (the brief asks for both):
  * the ancient register -- warm clay orange, earthen brown, pit black. Used
    for the army, the emperor, the mound, the sealed chamber.
  * the modern-record register -- cooler paper, blueprint blue, acid green.
    Used for 1974 and the acid damage, i.e. the beats where the *record* is the
    subject rather than the tomb.

FRAME-FILL. The recurring defect in this project is a subject parked small in
the middle of an empty field. So the ranks run past both side edges, the
soldier's shoulder is cropped by the right edge, the mound is cropped by the
bottom, and the mercury pool runs off the left.

CHARACTER. closeup() on the four emotional beats the brief names (b02, b16,
b26, b45) and fullbody() on b09, b24, b29 and b41 -- seven beats, with the
expression varied (awed, deadpan, shocked, grim, worried) rather than one
default face.

Run:  python lib/tomb_scene.py --preview
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
import v2type as T

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'tomb'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'The Terracotta Army'

# The dark cards of the pit carry an intentional lit stone course across the
# title band, so the engine's hardcoded near-black title has something to read
# against; band_intrusions exempts exactly those rows (see its TITLE_BACKDROP
# handling). Only the part inside the band is declared: rows below it are
# ordinary art and must still be checked.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette: the ancient / earthen register -------------------------------
INK = SC.INK
CLAY = (196, 118, 66)        # fired terracotta, the lit face
CLAY_D = (150, 82, 46)       # the shadowed side of a figure
CLAY_L = (222, 158, 104)     # the dusty, un-fired tone
EARTH = (146, 106, 70)       # the pit walls
EARTH_D = (104, 72, 46)      # earth in shadow
PIT = (34, 28, 24)           # the black the ranks recede into
PALE = (238, 226, 206)       # the dust the army is wearing
GOLD = (206, 158, 74)        # the one warm accent: imperial, and mercury
FIRE = (222, 118, 48)        # b17, the burning books
BRONZE = (150, 132, 84)      # the cranes

# --- palette: the modern-record register ------------------------------------
PAPER2 = (236, 234, 226)
BLUE = (78, 106, 138)        # survey blue, the 1974 well + the map plans
BLUE_L = (150, 174, 196)
ACID = (168, 200, 96)        # the acid, b36
GREY = (176, 176, 172)       # the grey a damaged figure goes
GREY_D = (128, 128, 126)
SILVER = (198, 206, 212)     # mercury

HZ = int(H * 0.70)            # the dirt line on the exterior cards


# ---------------------------------------------------------------------------
# backgrounds
# ---------------------------------------------------------------------------

def _pit(tile, seed, deep=PIT, wall=EARTH_D):
    """A full-frame EARTHEN PIT: the black the ranks recede into, with a lit
    near wall along the bottom. No sky -- we are underground."""
    PA.fill_rect(tile, [0, 0, W, H], deep, seed=seed, value=0.10)
    PA.fill_rect(tile, [0, int(H * 0.78), W, H], wall, seed=seed + 1,
                 value=0.08)
    PA.paper_overlay(tile, seed=seed + 2)


def _earth_field(tile, seed, sky=(206, 214, 222), ground=EARTH,
                 hz=HZ):
    """Exterior: a flat empty dirt field, low horizon."""
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.09)
    PA.paper_overlay(tile, seed=seed + 2)


def _interior(tile, seed, col):
    """A flat wall of one colour -- the register's plain ground."""
    PA.fill_rect(tile, [0, 0, W, H], col, seed=seed, value=0.09)
    PA.paper_overlay(tile, seed=seed + 2)


# ---------------------------------------------------------------------------
# the soldier
# ---------------------------------------------------------------------------

def _soldier(d, x, feet_y, h, seed, col=CLAY, shade=CLAY_D, facing=1,
             has_bow=False, has_armour=True, crop=False):
    """A standing clay soldier, `h` px tall, feet on `feet_y`.

    PROPORTIONS ARE THE WHOLE THING. The first pass used a head radius of
    0.135h, which makes the head a quarter of the figure -- at ship size the
    army read as a row of lollipops on posts, which is the one thing a
    terracotta warrior must not read as. A standing human is roughly seven and
    a half heads tall, so the head radius is 0.068h and everything else is
    derived from it. Judge any change here at 1280x720, not in a thumbnail:
    the thumbnail is exactly the size at which this defect is invisible.

    The figure is deliberately ABSTRACT -- this is fired clay, not a person, so
    there is no face and no skin tone. The topknot is the detail that says
    "Qin" rather than "person".
    """
    r = h * 0.068                         # head radius
    hy = feet_y - h + r                   # head centre
    sh_y = hy + r * 1.90                  # shoulder line (a head, not a post)
    hip_y = feet_y - h * 0.47             # waist
    bw = h * 0.105                        # half-width of the torso
    lw = h * 0.030                        # half-width of a limb
    img = PA.img_of(d)

    # --- legs, splayed a little, with a shoe at the bottom of each
    for sgn in (-1, 1):
        lx = x + sgn * bw * 0.46
        ank = lx + sgn * h * 0.014
        leg = [(lx - lw, hip_y - 4), (lx + lw, hip_y - 4),
               (ank + lw, feet_y - h * 0.012), (ank - lw, feet_y - h * 0.012)]
        PA.fill_poly(img, leg, col if sgn < 0 else shade, seed=seed + 11 + sgn,
                     value=0.07, tint=0.0, band=0.0, edge=0.0, grow=2)
        PA.hand_stroke(d, leg, INK, max(4, int(h * 0.011)), closed=True,
                       seed=seed + 21 + sgn, wavelength=60.0)
        shoe = [(ank - lw * 1.5, feet_y - h * 0.014),
                (ank + lw * 1.5, feet_y - h * 0.014),
                (ank + lw * 1.9 + sgn * h * 0.012, feet_y),
                (ank - lw * 1.7 + sgn * h * 0.012, feet_y)]
        PA.fill_poly(img, shoe, INK, seed=seed + 25 + sgn, value=0.02,
                     edge=0.6)

    # --- torso: a tapered slab, wider at the shoulders than the waist
    torso = [(x - bw, sh_y), (x + bw, sh_y), (x + bw * 0.78, hip_y + 3),
             (x - bw * 0.78, hip_y + 3)]
    PA.fill_poly(img, torso, col, seed=seed + 31, value=0.09,
                 tint=0.0, band=0.0, edge=0.0, grow=2)
    PA.hand_stroke(d, torso, INK, max(4, int(h * 0.013)), closed=True,
                   seed=seed + 32, wavelength=100.0)

    # the shadowed half -- what stops the figure reading as a flat decal
    sh = [(x + bw * 0.12 * facing, sh_y - 2), (x + bw, sh_y),
          (x + bw * 0.78, hip_y + 3), (x + bw * 0.12 * facing, hip_y + 3)]
    PA.fill_poly(img, sh, shade, seed=seed + 33, value=0.06,
                 tint=0.0, band=0.0, edge=0.0, grow=1)

    # --- armour: lamellar plates in courses of four. LOW CONTRAST ON PURPOSE.
    # The first pass alternated PALE against CLAY_L and the result read as a
    # checked picnic blanket rather than a scale corselet. Two clays a step
    # apart from the body tone read as armour at ship size; a checkerboard
    # reads as a tablecloth at any size.
    if has_armour:
        row_h = (hip_y - sh_y) * 0.155
        for row in range(5):
            yy = sh_y + (hip_y - sh_y) * (0.06 + 0.175 * row)
            for c in range(4):
                xx = x - bw * 0.72 + c * bw * 0.40 + (bw * 0.20
                                                     if row % 2 else 0)
                if abs(xx - x) > bw * 0.74:
                    continue
                tone = CLAY_L if (row + c) % 2 else (206, 132, 84)
                PA.fill_rect(img, [xx - bw * 0.16, yy, xx + bw * 0.16,
                                   yy + row_h], tone,
                             seed=seed + 40 + row * 4 + c, value=0.06,
                             edge=0.5)

    # --- the belt, and the collar above it
    PA.fill_rect(img, [x - bw * 0.88, hip_y - h * 0.024,
                       x + bw * 0.88, hip_y - h * 0.004], INK,
                 seed=seed + 51, value=0.02, edge=0.5)
    PA.fill_poly(img, [(x - bw * 0.42, sh_y + 1), (x + bw * 0.42, sh_y + 1),
                       (x, sh_y + h * 0.045)], INK, seed=seed + 52,
                 value=0.02, edge=0.5)

    # --- arms. Each has a real elbow (memory: an elbow that exists but does
    # not show still reads as one stroke), so upper arm and forearm are two
    # separate segments at different angles.
    aw = max(4, int(h * 0.013))
    if has_bow:
        # left arm up and out holding a bow; right arm across the chest
        PA.hand_stroke(d, [(x - bw * 0.88, sh_y + h * 0.02),
                           (x - bw * 1.30, sh_y + h * 0.05)], col, aw + 3,
                       closed=False, seed=seed + 61, wavelength=50.0)
        PA.hand_stroke(d, [(x - bw * 1.30, sh_y + h * 0.05),
                           (x - bw * 1.46, sh_y - h * 0.10)], col, aw + 3,
                       closed=False, seed=seed + 62, wavelength=50.0)
        PA.hand_stroke(d, [(x + bw * 0.88, sh_y + h * 0.03),
                           (x + bw * 0.40, sh_y + h * 0.09)], col, aw + 3,
                       closed=False, seed=seed + 63, wavelength=50.0)
        # the bow itself: an arc plus its string
        bxx, byy = x - bw * 1.52, sh_y - h * 0.015
        PA.hand_stroke(d, PA.arc_pts(bxx, byy, h * 0.055, h * 0.13,
                                     108, 252, n=26), GOLD, 7, closed=False,
                       seed=seed + 64, wavelength=60.0)
        PA.hand_stroke(d, [(bxx - h * 0.050, byy - h * 0.070),
                           (bxx - h * 0.050, byy + h * 0.070)], PALE, 3,
                       closed=False, seed=seed + 65, wavelength=40.0)
    else:
        # The elbow sits at 1.34bw -- well OUTSIDE the torso silhouette -- and
        # the forearm returns to 1.06bw. The first pass put the elbow at 1.10bw
        # and the forearm at 0.98bw, i.e. the bend was 0.12bw, which at ship
        # size is two pixels of angle: the arm merged into the torso edge and
        # read as no arm at all. A visible elbow needs the angle, not just the
        # joint (memory: elbow-existence-is-not-elbow-visibility).
        for sgn in (-1, 1):
            sx = x + sgn * bw * 0.88
            PA.hand_stroke(d, [(sx, sh_y + h * 0.02),
                               (x + sgn * bw * 1.34, hip_y - h * 0.07)], col,
                           aw + 3, closed=False, seed=seed + 64 + sgn,
                           wavelength=60.0)
            PA.hand_stroke(d, [(x + sgn * bw * 1.34, hip_y - h * 0.07),
                               (x + sgn * bw * 1.06, hip_y + h * 0.03)], col,
                           aw + 3, closed=False, seed=seed + 66 + sgn,
                           wavelength=60.0)

    # --- neck, then head over it, then the topknot. The neck is WIDE (0.55r)
    # and short: at 0.36r it read as a stake under the head and the figure
    # looked like a lollipop on a post rather than a person with a neck.
    PA.fill_rect(img, [x - r * 0.55, hy + r * 0.40, x + r * 0.55, sh_y + 2],
                 shade, seed=seed + 74, value=0.05, edge=0.5)
    head = PA.ellipse_pts(x, hy, r, r * 1.12, n=30)
    PA.fill_poly(img, head, col, seed=seed + 71, value=0.08,
                 tint=0.0, band=0.0, edge=0.0, grow=2)
    PA.hand_stroke(d, head, INK, max(4, int(h * 0.012)), closed=True,
                   seed=seed + 72, wavelength=70.0)
    PA.fill_poly(img, [(x - r * 0.34, hy - r * 0.80), (x + r * 0.34,
                     hy - r * 0.80), (x + r * 0.30, hy - r * 1.30),
                     (x, hy - r * 1.46), (x - r * 0.30, hy - r * 1.30)],
                 INK, seed=seed + 73, value=0.02, edge=0.5)
    return hy, r


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def card(i, j, draw, kind='subject', seed=0, motion=None):
        """A complete card: its own background, live beats i..j-1."""
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        return E3.E('card%02d' % i, kind, draw, at=T(i), until=end,
                    motion=motion)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ---- b01  the hook: the field, and a rank under it ------------------- #
    # FRAME-FILL: the dirt runs past the bottom edge and the sky past the top,
    # so the frame is the field rather than a view of it.
    def c_field(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _earth_field(tile, 101, ground=EARTH)
        D.draw_label(tile, 'OUTSIDE XI\'AN, CHINA', center=(640, 596),
                     color=INK, size=34)
    els.append(card(1, 2, c_field))
    els.append(cap(1, 640, 668, size=34))

    # ---- b02  the reveal: one soldier standing in the cut ---------------- #
    # CROP: the figure is scaled so its shoulder runs off the right edge --
    # a complete figure in the middle of the frame reads as a prop.
    def c_reveal(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (176, 190, 202), seed=105,
                     value=0.05)
        PA.fill_rect(tile, [0, 420, W, H], EARTH, seed=106, value=0.09)
        PA.paper_overlay(tile, seed=107)
        # the cut in the earth the figure stands in
        PA.fill_poly(tile, [(0, 720), (0, 470), (330, 430), (620, 452),
                            (900, 470), (1280, 452), (1280, 720)],
                     EARTH_D, seed=108, value=0.08)
        PA.hand_stroke(d, [(0, 470), (330, 430), (620, 452), (900, 470),
                           (1280, 452)], INK, 6, closed=False, seed=109,
                       wavelength=170.0)
        _soldier(d, 900, 700, 560, 110, has_bow=True)
        D.draw_label(tile, '2,000 YEARS', center=(300, 150), color=GOLD,
                     size=40)
    els.append(card(2, 3, c_reveal))
    els.append(cap(2, 640, 672, size=32))

    # ---- b03  the face, cropped in --------------------------------------- #
    def c_face(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 112, (150, 88, 48))
        hy, hw = _soldier(d, 640, 900, 780, 114, has_bow=False)
        # the paint leaving: flakes of the original pigment on the shoulder
        for k in range(16):
            fx = 300 + (k * 137) % 680
            fy = 250 + (k * 91) % 300
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 16, 9, n=14), GOLD,
                         seed=115 + k, value=0.06, edge=0.6)
    els.append(card(3, 4, c_face))
    els.append(cap(3, 640, 672, size=32))

    # ---- b04  the paint, gone -------------------------------------------- #
    def c_flaking(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 118, (118, 70, 40))
        _soldier(d, 640, 900, 780, 119)
        for k in range(14):
            fx = 260 + (k * 173) % 760
            fy = 230 + (k * 109) % 330
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 22, 12, n=14),
                         (92, 58, 34), seed=125 + k, value=0.06, edge=0.6)
        D.draw_label(tile, 'PAINT LOST', center=(300, 150), color=PALE,
                     size=38)
    els.append(card(4, 5, c_flaking))
    els.append(cap(4, 640, 672, size=32, fill=PALE))

    # ---- b05  TITLE: the army -------------------------------------------- #
    # NO draw_title HERE. engine3 composites the scene title LAST, on top of
    # every element, so an in-card draw_title lands underneath it and the two
    # overlap into an illegible smear. The chapter title is already on screen
    # every frame; the hero word goes in as a hand-lettered label placed clear
    # of the strip.
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 130)
        # A dark card needs a lit stone course at the head for the near-black
        # title to read against (see scene_common.title_backdrop). Drawn before
        # the ranks so the backdrop stays UNDER the art.
        SC.title_backdrop(tile, 1130, col=(118, 92, 70))
        # five in a rank; the outer two are CROPPED by the side edges, which is
        # what admits the army continues past the picture
        _soldier(d, -140, 690, 520, 129, has_armour=False)
        _soldier(d, 220, 700, 520, 130)
        _soldier(d, 640, 700, 520, 131, has_bow=True)
        _soldier(d, 1060, 700, 520, 132)
        _soldier(d, 1420, 690, 520, 133, has_armour=False)
        D.draw_label(tile, 'TERRACOTTA ARMY', center=(640, 152), color=PALE,
                     size=60)
    els.append(card(5, 6, c_title))
    els.append(cap(5, 640, 676, size=32, fill=PALE))

    # ---- b06  eight thousand, in the dark ------------------------------- #
    def c_dark(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], PIT, seed=137, value=0.12)
        PA.paper_overlay(tile, seed=138)
        SC.title_backdrop(tile, 1131, col=(118, 92, 70))
        # three ranks receding: near and lit, mid dimmer, far nearly black
        for row, (base, hgt, col, shd) in enumerate((
                (700, 470, CLAY, CLAY_D),
                (560, 360, (150, 92, 52), (110, 66, 38)),
                (452, 250, (96, 60, 36), (68, 42, 26)))):
            for c in range(-1, 6):
                _soldier(d, 90 + c * 230 + row * 46, base, hgt,
                         140 + row * 30 + c, col=col, shade=shd,
                         has_bow=(c % 2 == 0), has_armour=False)
        D.draw_label(tile, '8,000', center=(640, 660), color=GOLD, size=64)
    els.append(card(6, 7, c_dark))
    els.append(cap(6, 640, 672, size=32, fill=PALE))

    # ---- b07  the six hundred horses ------------------------------------ #
    # The near horse is CROPPED by the left edge and runs nearly the full
    # height: a complete animal in the middle of the frame reads as a model on
    # a stand, which is precisely what a museum plinth looks like.
    def c_horses(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 200, wall=EARTH)
        SC.title_backdrop(tile, 1200, col=(118, 92, 70))
        _horse(d, 330, 700, 580, 201, facing=-1)
        _horse(d, 1130, 706, 430, 202, col=CLAY_L, shade=EARTH, facing=-1)
        D.draw_label(tile, '600 HORSES', center=(430, 150), color=PALE,
                     size=44)
    els.append(card(7, 8, c_horses))
    els.append(cap(7, 640, 676, size=32, fill=PALE))

    # ---- b08  long rows in earthen pits --------------------------------- #
    def c_rows(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 210)
        SC.title_backdrop(tile, 1210, col=(118, 92, 70))
        # the pit walls converging, the rank running out past both edges
        PA.fill_poly(tile, [(0, 720), (0, 250), (150, 210), (0, 150)],
                     EARTH, seed=211, value=0.09)
        PA.fill_poly(tile, [(1280, 720), (1280, 250), (1130, 210),
                            (1280, 150)], EARTH, seed=212, value=0.09)
        for c in range(-1, 8):
            _soldier(d, 60 + c * 165, 700, 500, 213 + c, has_armour=True)
        PA.fill_poly(tile, [(520, 720), (760, 720), (700, 300), (580, 300)],
                     (24, 20, 18), seed=230, value=0.05)
    els.append(card(8, 9, c_rows))
    els.append(cap(8, 640, 676, size=32, fill=PALE))

    # ===== b09-b16  the emperor they guard ================================ #
    # ---- b09  every face turned the same way: the character among them --- #
    def c_guard(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 240)
        SC.title_backdrop(tile, 1240, col=(118, 92, 70))
        for c in range(-1, 5):
            _soldier(d, 40 + c * 210, 700, 470, 241 + c, has_armour=False)
        # the one living figure among them, cropped by the bottom edge
        SC.fullbody(d, 640, 810, 400, pose='shrug', expression='awed',
                    seed=250)
        D.draw_label(tile, 'ONE MAN', center=(640, 150), color=GOLD,
                     size=40)
    els.append(card(9, 10, c_guard, kind='character'))
    els.append(cap(9, 640, 676, size=32, fill=PALE))

    # ---- b10  the name stamp --------------------------------------------- #
    def c_name(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 251, (60, 44, 34))
        SC.title_backdrop(tile, 1251, col=(118, 92, 70))
        D.draw_label(tile, 'QIN SHI HUANG', center=(640, 150), color=GOLD,
                     size=54)
        _soldier(d, 640, 900, 700, 253, col=GOLD, shade=(150, 110, 52),
                 has_armour=True)
        D.draw_label(tile, 'FIRST EMPEROR', center=(640, 660), color=GOLD,
                     size=34)
    els.append(card(10, 11, c_name))
    els.append(cap(10, 640, 676, size=32, fill=PALE))

    # ---- b11  the character full body before the map --------------------- #
    def c_emperor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 254, PAPER2)
        _china(d, 780, 400, 1.35, 255)
        SC.fullbody(d, 300, 700, 470, pose='pointing', expression='neutral',
                    seed=256)
        D.draw_bubble(tile, 'FIRST EMPEROR', (250, 92), tail_to=(300, 250),
                      font_size=36, max_w=420)
    els.append(card(11, 12, c_emperor, kind='character'))
    els.append(cap(11, 640, 676, size=30))

    # ---- b12  221 BC: the war ends --------------------------------------- #
    def c_221(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 258, PAPER2)
        # The map's northern coast used to reach y=20 and struck through the
        # persistent "Tomb" title (band_intrusions: b12 = 454px). Pulled down
        # and trimmed to s=1.40/cy=452, which puts the coast at y=116 -- clear
        # of the band -- while the outline still runs off both sides
        # (x 217..1183, 75% of the frame width) so the card stays frame-filling.
        _china(d, 700, 452, 1.40, 259, kingdoms=False)
        # the broken banners
        for k in range(5):
            bx = 180 + k * 220
            PA.hand_stroke(d, [(bx, 200), (bx, 400)], INK, 8, closed=False,
                           seed=260 + k, wavelength=70.0)
            PA.fill_poly(tile, [(bx, 200), (bx + 96, 220), (bx + 60, 260),
                                (bx, 250)], (168, 76, 60), seed=270 + k,
                         value=0.07, edge=0.6)
            D.draw_red_x(tile, [bx - 10, 190, bx + 100, 262], width=8)
        D.draw_label(tile, '221 BC', center=(640, 620), color=INK, size=52)
    els.append(card(12, 13, c_221))
    els.append(cap(12, 640, 676, size=32))

    # ---- b13  a hundred separate kingdoms ------------------------------- #
    def c_kingdoms(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 275, PAPER2)
        # The map's northern coast at s=1.70/cy=360 reached y=-48 -- off the
        # top of the frame -- and the outline between the northern vertices
        # cut straight across the persistent "Tomb" title (band_intrusions:
        # b13 = 232px). Rescaled to s=1.35/cy=436, which lands the coast at
        # y=112, clear of the band, and keeps the outline running off both
        # sides (x 174..1106, 73% of frame width) so the card stays
        # frame-filling. The arrows are independent of the map and their
        # apexes top out at y=106, so they were left alone.
        _china(d, 640, 436, 1.35, 276, kingdoms=True)
        # fighting arrows between them
        for k in range(9):
            ax = 240 + (k * 173) % 800
            ay = 180 + (k * 97) % 380
            D.draw_arrow(tile, (ax, ay), (ax + 130, ay - 60), color=INK,
                         width=7, head=30)
        D.draw_label(tile, 'A HUNDRED KINGDOMS', center=(640, 656),
                     color=INK, size=36)
    els.append(card(13, 14, c_kingdoms))
    els.append(cap(13, 640, 676, size=30))

    # ---- b14  one script, one ruler ------------------------------------- #
    def c_one(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 280, PAPER2)
        # This used the same s=1.7 geometry that put the map's northern vertices
        # at y=-48 on b13, so the outline ran straight through the persistent
        # "The Terracotta Army" title and left it black-on-terracotta. It slipped
        # past the band gate because this card reads as a DARK card to it: the
        # title rect is filled by the terracotta map, whose greyscale luminance
        # (~110) falls under the gate's light-background threshold, so the check
        # was skipped rather than run. Fixed the same way as b12/b13 -- smaller
        # scale, pushed down -- so the outline's top edge lands at y~112.
        _china(d, 640, 436, 1.35, 281, kingdoms=False, unify=True)
        # a road across it, and a sheet of script
        PA.hand_stroke(d, [(180, 560), (520, 470), (900, 520), (1180, 450)],
                       INK, 10, closed=False, seed=282, wavelength=170.0)
        _script_sheet(d, 1050, 200, 290, 370, 283)
        D.draw_label(tile, 'ONE SCRIPT', center=(1050, 500), color=INK,
                     size=34)
    els.append(card(14, 15, c_one))
    els.append(cap(14, 640, 676, size=32))

    # ---- b15  one set of weights ----------------------------------------- #
    def c_weights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 284, (74, 58, 46))
        SC.title_backdrop(tile, 1284, col=(118, 92, 70))
        shapes = [(220, 560, 150, 120, 0), (500, 590, 110, 160, 1),
                  (740, 555, 190, 100, 2), (1030, 600, 120, 150, 3)]
        for k, (wx, wy, ww, wh, kind) in enumerate(shapes):
            _weight(d, wx, wy, ww, wh, 290 + k, kind)
            D.draw_label(tile, 'III', center=(wx, wy + wh * 0.5 + 40),
                         color=GOLD, size=34)
        D.draw_label(tile, 'ONE SET OF WEIGHTS', center=(640, 120),
                     color=GOLD, size=40)
    els.append(card(15, 16, c_weights))
    els.append(cap(15, 640, 676, size=32, fill=PALE))

    # ---- b16  that one ruler was himself: the character, deadpan -------- #
    # The throne is OFF-CENTRE and the character is cropped in on the left.
    # Centring both put the throne's back panel directly behind the head, so
    # the two together read as a face inside a box; and the speech bubble sat
    # at y=620 where the caption renders at 676, so the two overlapped.
    def c_himself(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 295, (54, 40, 32))
        SC.title_backdrop(tile, 1295, col=(118, 92, 70))
        _throne(d, 930, 760, 620, 296)
        SC.closeup(d, 400, 330, 175, 'deadpan', 297)
        D.draw_bubble(tile, 'himself', (930, 200), tail_to=(830, 380),
                      font_size=42, max_w=280)
    els.append(card(16, 17, c_himself, kind='character'))
    els.append(cap(16, 640, 676, size=32, fill=PALE))

    # ===== b17-b18  the grim pair ======================================== #
    # ---- b17  the books go into the fire -------------------------------- #
    def c_burn(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 300, (48, 36, 30))
        SC.title_backdrop(tile, 1300, col=(118, 92, 70))
        _flames(d, 640, 720, 620, 301)
        for k, (bx, by, bw_, bh) in enumerate(((240, 470, 150, 46),
                                               (330, 500, 170, 46),
                                               (820, 460, 160, 46),
                                               (900, 500, 150, 46))):
            _book(d, bx, by, bw_, bh, 310 + k, tilt=-18 if k % 2 else 14)
        D.draw_label(tile, 'EVERY BOOK', center=(640, 150), color=FIRE,
                     size=42)
    els.append(card(17, 18, c_burn))
    els.append(cap(17, 640, 676, size=32, fill=PALE))

    # ---- b18  the scholars go down too ---------------------------------- #
    def c_scholars(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (58, 44, 34), seed=320, value=0.09)
        PA.fill_rect(tile, [0, 430, W, H], EARTH, seed=321, value=0.08)
        PA.paper_overlay(tile, seed=322)
        SC.title_backdrop(tile, 1320, col=(118, 92, 70))
        # the pit, cropped by the bottom edge
        PA.fill_poly(tile, [(300, 720), (360, 480), (900, 460), (980, 720)],
                     PIT, seed=323, value=0.05)
        PA.hand_stroke(d, [(360, 480), (900, 460)], INK, 6, closed=False,
                       seed=324, wavelength=140.0)
        # the robed figure being lowered in
        PA.fill_poly(tile, [(620, 250), (760, 250), (800, 470), (580, 470)],
                     (86, 74, 96), seed=325, value=0.08)
        PA.hand_stroke(d, [(620, 250), (760, 250), (800, 470), (580, 470)],
                       INK, 6, closed=True, seed=326, wavelength=110.0)
        PA.fill_poly(tile, PA.ellipse_pts(690, 216, 44, 48, n=28), PALE,
                     seed=327, value=0.06)
        PA.hand_stroke(d, PA.ellipse_pts(690, 216, 44, 48, n=28), INK, 5,
                       closed=True, seed=328, wavelength=70.0)
        # the character recoiling at the left edge
        SC.fullbody(d, 190, 720, 400, pose='recoil', expression='worried',
                    seed=329)
    els.append(card(18, 19, c_scholars, kind='character'))
    els.append(cap(18, 640, 676, size=32, fill=PALE))

    # ===== b19-b23  the mound ============================================ #
    # ---- b19  the plan of the complex, dated ---------------------------- #
    def c_plan(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 330, PAPER2)
        # the drawn-on-wall plan: corridors and vaults as ink rectangles
        for k in range(9):
            x0 = 120 + (k % 3) * 340
            y0 = 150 + (k // 3) * 170
            PA.fill_rect(tile, [x0, y0, x0 + 250, y0 + 110],
                         (222, 214, 196), seed=331 + k, value=0.05)
            PA.hand_stroke(d, [(x0, y0), (x0 + 250, y0), (x0 + 250, y0 + 110),
                               (x0, y0 + 110)], INK, 4, closed=True,
                           seed=340 + k, wavelength=80.0)
        for k in range(4):
            PA.hand_stroke(d, [(120 + k * 250, 150), (120 + k * 250, 640)],
                           INK, 3, closed=False, seed=350 + k,
                           wavelength=120.0)
        D.draw_red_box(tile, [640, 400, 890, 510], width=6)
        D.draw_label(tile, '246 BC', center=(765, 596), color=INK, size=40)
    els.append(card(19, 20, c_plan))
    els.append(cap(19, 640, 676, size=32))

    # ---- b20  the forced labour, to the horizon -------------------------- #
    # The labourers read by their burden, not by a pose. character3's arms at
    # 150px end up a horizontal stick, which reads as a scarecrow; a shoulder
    # pole with two hanging baskets says "carrying earth" at any size.
    def c_labour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _earth_field(tile, 355, sky=(198, 206, 214), ground=EARTH,
                     hz=int(H * 0.44))
        # THE MOUND IS A TRUNCATED, TERRACED PYRAMID, NOT A TRIANGLE. That is
        # what the Qin mound actually is, and drawing it flat-topped here makes
        # b21's "it copied a pyramid" land: by the time the narrator names the
        # shape the viewer has already been looking at it. A triangular mound
        # reads as a mountain, which is a different building entirely.
        apex_l, apex_r, top_y = 470, 810, 232
        PA.fill_poly(tile, [(180, 720), (apex_l, top_y), (apex_r, top_y),
                            (1100, 720)], EARTH_D, seed=356, value=0.08)
        PA.hand_stroke(d, [(180, 720), (apex_l, top_y), (apex_r, top_y),
                           (1100, 720)], INK, 6, closed=False, seed=357,
                       wavelength=150.0)
        # the rammed-earth courses, which is how the mound was actually built
        for k in range(6):
            t = k / 6.0
            yy = int(top_y + (720 - top_y) * (t ** 1.5))
            lx = int(apex_l + (180 - apex_l) * (t ** 1.5))
            rx = int(apex_r + (1100 - apex_r) * (t ** 1.5))
            PA.hand_stroke(d, [(lx, yy), (rx, yy)], (120, 86, 54), 4,
                           closed=False, seed=380 + k, wavelength=120.0)
        # Two lines of carriers. The BACK line is HIGHER on the frame (smaller
        # y) and smaller: the first pass put it lower, which inverted the depth
        # and made the back row read as nearer than the front one.
        for r in range(2):
            for c in range(9):
                s = 1.0 - r * 0.24
                x = 70 + c * 148 + r * 62
                y = 690 - r * 54
                fh_ = int(160 * s)
                SC.fullbody(d, x, y, fh_, pose='standing',
                            expression='neutral', seed=360 + r * 9 + c)
                # The pole across the shoulder and its two baskets. The
                # baskets hang BELOW the pole end from a short rope; the first
                # pass drew them straddling the pole line, which put two opaque
                # tan slabs across the carrier's chest and read as cardboard
                # boxes strapped to him.
                PY = y - fh_ * 0.74
                hang = 12 * s
                PA.hand_stroke(d, [(x - 36 * s, PY), (x + 36 * s, PY)], INK,
                               max(3, int(6 * s)), closed=False,
                               seed=370 + r * 9 + c, wavelength=30.0)
                for sgn in (-1, 1):
                    bx = x + sgn * 30 * s
                    PA.hand_stroke(d, [(bx, PY), (bx, PY + hang)], INK, 3,
                                   closed=False, seed=372 + r * 9 + c,
                                   wavelength=20.0)
                    PA.fill_poly(tile,
                                 [(bx - 14 * s, PY + hang),
                                  (bx + 14 * s, PY + hang),
                                  (bx + 11 * s, PY + hang + 26 * s),
                                  (bx - 11 * s, PY + hang + 26 * s)],
                                 (188, 150, 100), seed=373 + r * 9 + c,
                                 value=0.07, edge=0.6)
        D.draw_label(tile, 'DECADES. UNPAID.', center=(640, 140), color=INK,
                     size=38)
    els.append(card(20, 21, c_labour, kind='character'))
    els.append(cap(20, 640, 676, size=32))

    # ---- b21  the mound beside a pyramid -------------------------------- #
    def c_pyramid(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _earth_field(tile, 372, sky=(212, 218, 224), ground=(186, 166, 132),
                     hz=int(H * 0.58))
        # the mound, left and cropped by the left edge
        PA.fill_poly(tile, [(-40, 700), (120, 300), (330, 190), (520, 320),
                            (560, 700)], EARTH, seed=373, value=0.09)
        PA.hand_stroke(d, [(-40, 700), (120, 300), (330, 190), (520, 320),
                           (560, 700)], INK, 6, closed=False, seed=374,
                       wavelength=150.0)
        # a small stepped pyramid beside it
        base_y, top = 700, 320
        for k in range(4):
            inset = k * 82
            PA.fill_poly(tile, [(700 + inset, base_y - k * 95),
                                (700 + inset + 330, base_y - k * 95),
                                (700 + inset + 330, base_y - k * 95 - 8),
                                (700 + inset, base_y - k * 95 - 8)],
                         (206, 190, 158), seed=375 + k, value=0.07)
        PA.hand_stroke(d, [(700, base_y), (866, base_y), (866, base_y - 380),
                           (700, base_y - 380)], INK, 5, closed=True,
                       seed=379, wavelength=90.0)
        PA.fill_poly(tile, [(1166, base_y), (1280, base_y - 380),
                            (1280, base_y - 380)], (206, 190, 158),
                     seed=380, value=0.07)
        D.draw_label(tile, 'COPIED A PYRAMID', center=(980, 190), color=INK,
                     size=34)
    els.append(card(21, 22, c_pyramid))
    els.append(cap(21, 640, 676, size=32))

    # ---- b22  the heavenly palace --------------------------------------- #
    def c_palace(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 44, 66), seed=382, value=0.08)
        PA.paper_overlay(tile, seed=383)
        for k in range(40):
            sx = (k * 197) % 1280
            sy = (k * 91) % 420
            PA.fill_poly(tile, PA.ellipse_pts(sx, sy, 3, 3, n=8),
                         (226, 222, 200), seed=384 + k, value=0.04, edge=0.4)
        # The night sky needs the lit course too, so the near-black title reads.
        # Drawn after the stars so the backdrop stays the topmost thing in the
        # band and the intrusion gate's uniform-row test still holds.
        SC.title_backdrop(tile, 1382, col=(86, 88, 116))
        # the moon disc
        PA.fill_poly(tile, PA.ellipse_pts(1000, 150, 92, 92, n=40),
                     (238, 232, 206), seed=430, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(1000, 150, 92, 92, n=40), INK, 5,
                       closed=True, seed=431, wavelength=110.0)
        # cloud bands
        for k in range(3):
            PA.hand_stroke(d, [(0, 300 + k * 70), (300, 280 + k * 70),
                               (640, 312 + k * 70), (980, 282 + k * 70),
                               (1280, 304 + k * 70)], (150, 152, 176), 12,
                           closed=False, seed=440 + k, wavelength=170.0)
        # the palace roof, cropped by the bottom
        PA.fill_poly(tile, [(-40, 720), (240, 470), (640, 420), (1040, 470),
                            (1320, 720)], (128, 52, 44), seed=450,
                     value=0.08)
        PA.hand_stroke(d, [(-40, 720), (240, 470), (640, 420), (1040, 470),
                           (1320, 720)], INK, 6, closed=False, seed=451,
                       wavelength=170.0)
        D.draw_label(tile, 'HEAVENLY PALACE', center=(640, 150), color=GOLD,
                     size=48)
    els.append(card(22, 23, c_palace))
    els.append(cap(22, 640, 676, size=32, fill=PALE))

    # ---- b23  outside Xi'an: the map plan ------------------------------- #
    def c_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 453, PAPER2)
        # a walled city as a square, and the complex as a dot EAST of it
        PA.fill_rect(tile, [120, 220, 520, 620], (206, 200, 186), seed=454,
                     value=0.06)
        for k in range(9):
            PA.fill_rect(tile, [120 + k * 44, 220, 152 + k * 44, 244],
                         (150, 144, 132), seed=455 + k, value=0.05, edge=0.5)
            PA.fill_rect(tile, [120 + k * 44, 596, 152 + k * 44, 620],
                         (150, 144, 132), seed=464 + k, value=0.05, edge=0.5)
        PA.hand_stroke(d, [(120, 220), (520, 220), (520, 620), (120, 620)],
                       INK, 6, closed=True, seed=474, wavelength=110.0)
        D.draw_label(tile, "XI'AN", center=(320, 660), color=INK, size=32)
        # the road out to the complex
        PA.hand_stroke(d, [(520, 420), (760, 400), (980, 420)], INK, 8,
                       closed=False, seed=475, wavelength=170.0)
        # the complex itself, cropped by the right edge
        PA.fill_rect(tile, [1010, 300, 1340, 560], (188, 128, 84), seed=476,
                     value=0.08)
        PA.hand_stroke(d, [(1010, 300), (1340, 300), (1340, 560),
                           (1010, 560)], INK, 6, closed=True, seed=477,
                       wavelength=110.0)
        PA.fill_poly(tile, PA.ellipse_pts(1140, 430, 34, 34, n=24), INK,
                     seed=478, value=0.02, edge=0.6)
        D.draw_label(tile, 'OUTSIDE', center=(1170, 620), color=INK, size=30)
    els.append(card(23, 24, c_map))
    els.append(cap(23, 640, 676, size=32))

    # ===== b24-b26  no two alike ========================================= #
    # ---- b24  three soldiers, three heights, against a measuring stick --- #
    def c_heights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 480, (176, 152, 128))
        PA.fill_rect(tile, [0, 620, W, H], EARTH, seed=481, value=0.07)
        PA.paper_overlay(tile, seed=482)
        # the stick, cropped by the top edge
        PA.fill_rect(tile, [980, 0, 1030, 660], (250, 246, 236), seed=483,
                     value=0.04)
        PA.hand_stroke(d, [(980, 0), (980, 660)], INK, 4, closed=False,
                       seed=484, wavelength=120.0)
        for k in range(11):
            PA.hand_stroke(d, [(980, 60 + k * 56), (1012, 60 + k * 56)], INK,
                           4, closed=False, seed=485 + k, wavelength=40.0)
        _soldier(d, 250, 660, 460, 500, has_bow=False)
        _soldier(d, 550, 660, 390, 501, col=CLAY_L, shade=EARTH)
        _soldier(d, 830, 660, 520, 502, has_bow=True)
        D.draw_label(tile, 'ALL DIFFERENT', center=(640, 130), color=INK,
                     size=38)
    els.append(card(24, 25, c_heights))
    els.append(cap(24, 640, 676, size=32))

    # ---- b25  two faces, cropped tight ---------------------------------- #
    def c_faces(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 510, (132, 78, 44))
        # two heads, each cropped by a side edge -- no complete pair of objects
        for sx, seed in ((180, 520), (1060, 530)):
            _soldier(d, sx, 900, 820, seed, col=CLAY if seed == 520 else
                     CLAY_L, shade=CLAY_D)
        # the difference marked: one has a moustache line, one a scar
        PA.hand_stroke(d, [(140, 300), (232, 306)], INK, 7, closed=False,
                       seed=540, wavelength=40.0)
        PA.hand_stroke(d, [(1010, 250), (1058, 340)], (86, 52, 32), 7,
                       closed=False, seed=541, wavelength=50.0)
        D.draw_label(tile, 'NO TWO THE SAME', center=(640, 120), color=PALE,
                     size=40)
    els.append(card(25, 26, c_faces))
    els.append(cap(25, 640, 676, size=32, fill=PALE))

    # ---- b26  the army vanishes: the empty field, the character small --- #
    def c_vanish(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _earth_field(tile, 545, sky=(200, 208, 216), ground=EARTH)
        # the empty pit outline, barely there
        PA.hand_stroke(d, [(300, 620), (330, 540), (980, 530), (1010, 620)],
                       EARTH_D, 6, closed=False, seed=546, wavelength=150.0)
        SC.closeup(d, 250, 480, 165, 'shock', 547)
        D.draw_label(tile, '2,000 YEARS', center=(880, 250), color=GOLD,
                     size=40)
    els.append(card(26, 27, c_vanish, kind='character'))
    els.append(cap(26, 640, 676, size=32))

    # ===== b27-b31  1974: the modern-record register ====================== #
    # The register shifts here on purpose: the subject is no longer the tomb but
    # the RECORD of it, so the ground goes to survey paper blue and the line
    # work gets thin and technical.
    # ---- b27  farmers digging a well ------------------------------------ #
    def c_dig(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _earth_field(tile, 560, sky=BLUE_L, ground=(178, 152, 118), hz=520)
        # the half-dug well in the right half, cropped by the bottom edge
        PA.fill_poly(tile, [(820, 720), (860, 540), (1160, 540), (1200, 720)],
                     EARTH_D, seed=561, value=0.08)
        PA.hand_stroke(d, [(860, 540), (1160, 540)], INK, 6, closed=False,
                       seed=562, wavelength=100.0)
        PA.fill_rect(tile, [820, 528, 1200, 552], (120, 108, 96), seed=563,
                     value=0.06)
        # the diggers, one mid-swing, both cropped by the bottom
        for k, (fx, fy, fsz, fs) in enumerate(((250, 700, 400, 0),
                                               (560, 700, 380, 9))):
            SC.fullbody(d, fx, fy, fsz, pose='pointing',
                        expression='neutral', seed=fs)
            PA.hand_stroke(d, [(fx + 40, fy - fsz * 0.62),
                               (fx + 96, fy - fsz * 0.86)], INK, 8,
                           closed=False, seed=fs + 1, wavelength=40.0)
            PA.fill_poly(tile, [(fx + 88, fy - fsz * 0.90),
                                (fx + 136, fy - fsz * 0.78),
                                (fx + 84, fy - fsz * 0.68)], (150, 152, 158),
                         seed=fs + 2, value=0.07, edge=0.6)
        D.draw_label(tile, '1974', center=(180, 140), color=INK, size=52)
    els.append(card(27, 28, c_dig, kind='character'))
    els.append(cap(27, 640, 676, size=32))

    # ---- b28  the shovel strikes something hard ------------------------- #
    # FRAME-FILL on the shovel: the blade comes in from the left edge and is
    # the biggest thing in the picture, because it is what the beat is about.
    def c_strike(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 570, (140, 104, 70))
        # the shovel blade, cropped by the left edge, driven down
        blade = [(-60, 150), (520, 250), (640, 350), (470, 440), (-60, 380)]
        PA.fill_poly(tile, blade, (154, 158, 164), seed=571, value=0.07)
        PA.hand_stroke(d, blade, INK, 7, closed=True, seed=572,
                       wavelength=130.0)
        PA.hand_stroke(d, [(-60, 230), (560, 320)], INK, 10, closed=False,
                       seed=573, wavelength=150.0)
        # the hard thing it struck, chipped at the edge
        PA.fill_poly(tile, PA.ellipse_pts(700, 420, 190, 150, n=30), CLAY,
                     seed=574, value=0.08)
        PA.hand_stroke(d, PA.ellipse_pts(700, 420, 190, 150, n=30), INK, 6,
                       closed=True, seed=575, wavelength=120.0)
        for k in range(9):
            cx_ = 640 + (k * 113) % 220
            cy_ = 400 + (k * 71) % 120
            PA.fill_poly(tile, PA.ellipse_pts(cx_, cy_, 18, 12, n=14),
                         CLAY_D, seed=576 + k, value=0.06, edge=0.6)
        D.draw_label(tile, 'SOMETHING HARD', center=(900, 200), color=INK,
                     size=40)
    els.append(card(28, 29, c_strike))
    els.append(cap(28, 640, 676, size=32))

    # ---- b29  a clay shoulder, then a face: the character, shocked ------- #
    def c_emerge(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 590, (128, 94, 62))
        PA.fill_rect(tile, [0, 560, W, H], EARTH_D, seed=591, value=0.08)
        PA.paper_overlay(tile, seed=592)
        # the figure coming up out of the dirt, cropped by the right edge
        _soldier(d, 950, 800, 620, 593, col=CLAY_L, shade=EARTH,
                 has_armour=False)
        # the loose soil falling off it
        for k in range(14):
            fx = 700 + (k * 131) % 480
            fy = 620 + (k * 83) % 90
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 15, 10, n=12),
                         EARTH_D, seed=594 + k, value=0.06, edge=0.6)
        # the character, cropped by the left edge, mouth open
        SC.closeup(d, 190, 380, 175, 'shock', 610)
    els.append(card(29, 30, c_emerge, kind='character'))
    els.append(cap(29, 640, 676, size=32))

    # ---- b30  the clay breaks as they raise it -------------------------- #
    def c_break(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pit(tile, 620, wall=(120, 88, 60))
        SC.title_backdrop(tile, 1620, col=(118, 92, 70))
        # two hands' worth of arm, lifted, snapped across a break
        arm = [(300, 640), (360, 470), (620, 400), (760, 330), (700, 250),
               (520, 320), (350, 400), (280, 560)]
        PA.fill_poly(tile, arm, CLAY, seed=621, value=0.08)
        PA.hand_stroke(d, arm, INK, 6, closed=True, seed=622,
                       wavelength=130.0)
        # the break: a jagged white gap
        PA.hand_stroke(d, [(760, 330), (800, 300), (760, 268), (810, 236)],
                       SC.PAGE, 12, closed=False, seed=623, wavelength=50.0)
        # fragments dropping back
        for k in range(11):
            fx = 340 + (k * 149) % 560
            fy = 560 + (k * 61) % 150
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 20, 13, n=14), CLAY_D,
                         seed=624 + k, value=0.06, edge=0.6)
        D.draw_label(tile, 'IT BROKE', center=(1000, 200), color=PALE,
                     size=44)
    els.append(card(30, 31, c_break))
    els.append(cap(30, 640, 676, size=32, fill=PALE))

    # ---- b31  the hole is covered over ---------------------------------- #
    def c_cover(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _earth_field(tile, 640, sky=(188, 196, 206), ground=EARTH)
        # the small building over it, cropped by the right edge
        PA.fill_rect(tile, [760, 420, 1340, 640], (176, 168, 152), seed=641,
                     value=0.07)
        PA.fill_poly(tile, [(720, 420), (1050, 300), (1380, 420)],
                     (128, 84, 62), seed=642, value=0.08)
        PA.hand_stroke(d, [(760, 420), (1050, 300), (1380, 420)], INK, 6,
                       closed=False, seed=643, wavelength=130.0)
        PA.fill_rect(tile, [960, 500, 1080, 640], (86, 72, 60), seed=644,
                     value=0.06)
        PA.hand_stroke(d, [(760, 640), (1340, 640)], INK, 5, closed=False,
                       seed=645, wavelength=110.0)
        # the tarp over the filled hole, foreground left
        PA.fill_poly(tile, [(-40, 700), (140, 560), (420, 540), (660, 590),
                            (700, 700)], (94, 106, 118), seed=646,
                     value=0.08)
        PA.hand_stroke(d, [(-40, 700), (140, 560), (420, 540), (660, 590),
                           (700, 700)], INK, 6, closed=False, seed=647,
                       wavelength=130.0)
        D.draw_label(tile, 'COVERED OVER', center=(300, 250), color=INK,
                     size=40)
    els.append(card(31, 32, c_cover))
    els.append(cap(31, 640, 676, size=32))

    # ===== b32-b35  2012 and the cranes ================================== #
    # ---- b32  the plan of the L-shaped pit ------------------------------ #
    def c_lshape(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 650, PAPER2)
        # an L-shaped corridor of vaults, cropped by two edges
        band = [(0, 240), (900, 210), (960, 300), (960, 470), (1280, 470),
                (1280, 620), (420, 620), (420, 470), (0, 470)]
        PA.fill_poly(tile, band, (206, 214, 220), seed=651, value=0.06)
        PA.hand_stroke(d, band, INK, 7, closed=True, seed=652,
                       wavelength=170.0)
        for k in range(6):
            vx = 90 + k * 140
            PA.hand_stroke(d, [(vx, 250), (vx, 470)], INK, 3, closed=False,
                           seed=653 + k, wavelength=70.0)
            PA.fill_poly(tile, PA.ellipse_pts(vx + 70, 360, 26, 26, n=20),
                         BLUE, seed=659 + k, value=0.06, edge=0.6)
        PA.hand_stroke(d, [(420, 540), (1200, 540)], INK, 3, closed=False,
                       seed=665, wavelength=90.0)
        D.draw_label(tile, 'PIT 1  -  2012', center=(640, 680), color=INK,
                     size=40)
    els.append(card(32, 33, c_lshape))
    els.append(cap(32, 640, 676, size=32))

    # ---- b33  the pit from above, full of figures, cropped both sides ---- #
    def c_fromabove(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (104, 82, 60), seed=670,
                     value=0.09)
        PA.paper_overlay(tile, seed=671)
        # The grid started at y=90 with a row half-height of 46, so the first
        # rank's heads reached y=44 -- inside the persistent title band, where a
        # dense field of terracotta discs reads as a smear behind the words. The
        # grid now starts at y=150 (first rank tops out at y=104) and the rows
        # are spaced 108 rather than 116 so the last rank still lands at y=582
        # and the '1,000+ SOLDIERS' label at y=672 keeps its clear space.
        rows, cols = 5, 9
        for r in range(rows):
            for c in range(cols):
                x = -30 + c * 160 + (40 if r % 2 else 0)
                y = 150 + r * 108
                PA.fill_poly(tile, PA.ellipse_pts(x, y, 62, 46, n=22), CLAY,
                             seed=672 + r * 9 + c, value=0.08, edge=1.4)
                PA.fill_poly(tile, PA.ellipse_pts(x, y - 14, 22, 20, n=18),
                             CLAY_L, seed=730 + r * 9 + c, value=0.06,
                             edge=0.8)
        D.draw_label(tile, '1,000+ SOLDIERS', center=(640, 672), color=PALE,
                     size=40)
    els.append(card(33, 34, c_fromabove))
    els.append(cap(33, 640, 676, size=32, fill=PALE))

    # ---- b34  two broken bronze cranes ----------------------------------- #
    def c_cranes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 800, (118, 90, 62))
        _crane(d, 380, 640, 520, 801, broken=True)
        _crane(d, 980, 660, 420, 802, broken=True, flip=True)
        D.draw_label(tile, 'BOTH BROKEN', center=(640, 150), color=PALE,
                     size=40)
    els.append(card(34, 35, c_cranes))
    els.append(cap(34, 640, 676, size=32, fill=PALE))

    # ---- b35  modern glue, modern epoxy -------------------------------- #
    def c_glue(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 810, PAPER2)
        _crane(d, 560, 660, 520, 811, broken=True, repaired=True)
        # the glue bottle and brush, foreground right
        PA.fill_poly(tile, [(1000, 380), (1160, 380), (1130, 560),
                            (1030, 560)], (232, 232, 228), seed=812,
                     value=0.05)
        PA.fill_rect(tile, [1050, 330, 1110, 384], BLUE, seed=813,
                     value=0.07)
        PA.hand_stroke(d, [(1000, 380), (1160, 380), (1130, 560),
                           (1030, 560)], INK, 5, closed=True, seed=814,
                       wavelength=80.0)
        PA.hand_stroke(d, [(1050, 330), (1110, 330)], INK, 6, closed=False,
                       seed=815, wavelength=40.0)
        D.draw_label(tile, 'MODERN GLUE', center=(1080, 630), color=INK,
                     size=32)
        D.draw_label(tile, 'REPAIRED ANYWAY', center=(560, 660), color=INK,
                     size=32)
    els.append(card(35, 36, c_glue))
    els.append(cap(35, 640, 676, size=32))

    # ===== b36-b37  the acid ============================================= #
    # ---- b36  acid poured on terracotta armour ------------------------- #
    def c_acid(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 820, (128, 96, 66))
        # the figure, cropped by the left edge, filling the frame
        _soldier(d, 420, 820, 760, 821)
        # the jar, tilted, cropped by the right edge
        jar = [(1140, 200), (1300, 220), (1320, 380), (1130, 360)]
        PA.fill_poly(tile, jar, (236, 236, 230), seed=822, value=0.05)
        PA.hand_stroke(d, jar, INK, 6, closed=True, seed=823,
                       wavelength=90.0)
        # the pour: the one green in the chapter
        for k in range(5):
            PA.hand_stroke(d, [(1180 - k * 34, 360), (900 - k * 60, 470 + k * 34)],
                           ACID, 26, closed=False, seed=824 + k,
                           wavelength=60.0)
        for k in range(12):
            fx = 300 + (k * 127) % 560
            fy = 420 + (k * 89) % 320
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, 26, 15, n=14), ACID,
                         seed=830 + k, value=0.05, edge=0.6)
        D.draw_label(tile, 'ACID', center=(1180, 520), color=ACID, size=48)
    els.append(card(36, 37, c_acid))
    els.append(cap(36, 640, 676, size=32, fill=PALE))

    # ---- b37  the markings are gone; the character looks away ----------- #
    def c_gone(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 845, (150, 148, 144))
        # cy=820 with h=740 put the figure's head at y=80 -- eight pixels into
        # the title band, so a grey helmet crossed "The Terracotta Army" on b37.
        # h is 640 now, so the head tops out at y=180 and the figure still runs
        # off the bottom edge.
        _soldier(d, 700, 820, 640, 846, col=GREY, shade=GREY_D,
                 has_armour=False)
        # the armour plate rubbed off, and what was written on it, gone
        PA.fill_rect(tile, [430, 380, 980, 470], (134, 132, 130), seed=847,
                     value=0.07)
        PA.hand_stroke(d, [(430, 380), (980, 380)], (112, 110, 108), 4,
                       closed=False, seed=848, wavelength=90.0)
        # the character at the left edge, turned away
        SC.fullbody(d, 210, 740, 380, pose='shrug', expression='disgust',
                    seed=849)
        D.draw_label(tile, 'NEVER READABLE AGAIN', center=(760, 150),
                     color=INK, size=36)
    els.append(card(37, 38, c_gone, kind='character'))
    els.append(cap(37, 640, 676, size=30))

    # ===== b38-b42  the mercury ========================================= #
    # ---- b38  the soil sample and the bead ------------------------------ #
    # This frame was rebuilt. The first pass drew a jar 600px wide floating in
    # a 1280x720 field of empty paper with a small grey lump inside it, which
    # is the project's #1 recurring defect stated exactly: a subject parked
    # small in the middle of an empty frame. Now the jar is 900px wide and
    # cropped by the bottom edge, the soil inside it fills most of the glass,
    # and the bead is the single brightest thing on screen.
    def c_sample(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # a COLD register for the lab beat -- the mercury section is the first
        # thing in the chapter that is not earth, and the palette should say so
        _interior(tile, 860, (208, 214, 218))
        # the lab bench, cropped by the bottom edge
        PA.fill_rect(tile, [-20, 500, 1300, 760], (176, 182, 186), seed=861,
                     value=0.06)
        PA.hand_stroke(d, [(-20, 500), (1300, 500)], INK, 6, closed=False,
                       seed=862, wavelength=170.0)
        # THE JAR: 900px wide, its base cropped off the bottom of the frame.
        jar = [(190, 560), (1090, 560), (1040, 120), (240, 120)]
        PA.fill_poly(tile, jar, (226, 234, 238), seed=863, value=0.05)
        PA.hand_stroke(d, [(190, 560), (240, 120), (1040, 120), (1090, 560)],
                       INK, 8, closed=False, seed=864, wavelength=150.0)
        # the soil inside: packed against the glass, its own coarse texture
        soil = [(214, 556), (1066, 556), (1020, 300), (260, 300)]
        PA.fill_poly(tile, soil, (118, 92, 62), seed=865, value=0.09)
        PA.hand_stroke(d, [(214, 556), (1066, 556)], INK, 5, closed=False,
                       seed=866, wavelength=130.0)
        for k in range(30):
            gx = 240 + (k * 137) % 800
            gy = 320 + (k * 89) % 220
            PA.fill_poly(tile, PA.ellipse_pts(gx, gy, 13, 9, n=12),
                         (146, 116, 78) if k % 2 else (92, 70, 46),
                         seed=867 + k, value=0.06, edge=0.5)
        # THE BEAD: the fact of the beat, so it is the biggest, brightest
        # object in the picture and it sits proud of the soil.
        PA.fill_poly(tile, PA.ellipse_pts(640, 380, 132, 106, n=40), SILVER,
                     seed=900, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(640, 380, 132, 106, n=40), INK, 7,
                       closed=True, seed=901, wavelength=90.0)
        PA.fill_poly(tile, PA.ellipse_pts(596, 344, 42, 28, n=22),
                     (246, 250, 252), seed=902, value=0.03, edge=0.5)
        # the meniscus highlight along the top of the bead
        PA.hand_stroke(d, PA.arc_pts(640, 380, 120, 94, 190, 300, n=26),
                       (238, 244, 248), 8, closed=False, seed=903,
                       wavelength=60.0)
        D.draw_label(tile, 'MERCURY', center=(640, 170), color=INK,
                     size=52)
    els.append(card(38, 39, c_sample))
    els.append(cap(38, 640, 676, size=32))

    # ---- b39  enough of it to fill a pool: the pool runs off the left --- #
    def c_pool(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (34, 32, 34), seed=870,
                     value=0.09)
        PA.paper_overlay(tile, seed=871)
        SC.title_backdrop(tile, 1870, col=(118, 92, 70))
        # the low tunnel walls, converging
        PA.fill_poly(tile, [(-40, 720), (-40, 180), (380, 130), (520, 300),
                            (520, 720)], (58, 52, 48), seed=872, value=0.08)
        PA.fill_poly(tile, [(1320, 720), (1320, 180), (900, 130), (760, 300),
                            (760, 720)], (58, 52, 48), seed=873, value=0.08)
        PA.hand_stroke(d, [(-40, 180), (380, 130), (520, 300)], INK, 6,
                       closed=False, seed=874, wavelength=130.0)
        PA.hand_stroke(d, [(1320, 180), (900, 130), (760, 300)], INK, 6,
                       closed=False, seed=875, wavelength=130.0)
        # the pool: flat silver, cropped by the left edge
        PA.fill_poly(tile, [(-40, 600), (520, 566), (760, 600), (760, 720),
                            (-40, 720)], SILVER, seed=876, value=0.07)
        PA.hand_stroke(d, [(-40, 600), (520, 566), (760, 600)], INK, 6,
                       closed=False, seed=877, wavelength=150.0)
        for k in range(4):
            PA.hand_stroke(d, [(60 + k * 150, 620 + (k % 2) * 30),
                               (150 + k * 150, 614 + (k % 2) * 30)],
                           (238, 244, 248), 5, closed=False, seed=878 + k,
                           wavelength=60.0)
        # the lamp that lights it
        PA.fill_poly(tile, PA.ellipse_pts(900, 250, 44, 44, n=24),
                     (250, 216, 150), seed=885, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(900, 250, 44, 44, n=24), INK, 5,
                       closed=True, seed=886, wavelength=50.0)
        D.draw_label(tile, 'ENOUGH FOR A POOL', center=(880, 430),
                     color=SILVER, size=34)
    els.append(card(39, 40, c_pool))
    els.append(cap(39, 640, 676, size=32, fill=PALE))

    # ---- b40  the old record: rivers of mercury on a scroll ------------- #
    def c_scroll(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 890, (222, 214, 194))
        roll = [(-40, 220), (1320, 190), (1320, 620), (-40, 650)]
        PA.fill_poly(tile, roll, (246, 240, 224), seed=891, value=0.05)
        PA.hand_stroke(d, roll, INK, 6, closed=True, seed=892,
                       wavelength=180.0)
        # the shape the rivers run around
        shp = [(520, 320), (700, 280), (830, 360), (800, 500), (620, 530),
               (500, 430)]
        PA.fill_poly(tile, shp, (224, 212, 190), seed=893, value=0.06)
        PA.hand_stroke(d, shp, INK, 4, closed=True, seed=894,
                       wavelength=110.0)
        # two winding silver rivers around it
        for k in range(2):
            o = 60 * (k + 1)
            PA.hand_stroke(d, [(220 - o * 0.2, 420 + o * 0.3),
                               (430, 380 + o * 0.5), (640, 430 + o * 0.4),
                               (880, 370 + o * 0.5), (1120, 420 + o * 0.3)],
                           SILVER, 26, closed=False, seed=895 + k,
                           wavelength=140.0)
        D.draw_label(tile, 'THE OLD RECORDS', center=(640, 140), color=INK,
                     size=38)
    els.append(card(40, 41, c_scroll))
    els.append(cap(40, 640, 676, size=32))

    # ---- b41  a slow poison: the character, wiping his mouth ----------- #
    def c_droplet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 900, (238, 234, 226))
        # the fingertip and the droplet, cropped by the LEFT edge -- the
        # figure's own hand, so the beat lands on a body
        PA.fill_poly(tile, [(-40, 470), (280, 430), (420, 500), (300, 590),
                            (-40, 560)], (238, 226, 206), seed=901,
                     value=0.06)
        PA.hand_stroke(d, [(-40, 470), (280, 430), (420, 500), (300, 590),
                           (-40, 560)], INK, 6, closed=True, seed=902,
                       wavelength=110.0)
        PA.fill_poly(tile, PA.ellipse_pts(400, 350, 74, 96, n=30), SILVER,
                     seed=903, value=0.06)
        PA.hand_stroke(d, PA.ellipse_pts(400, 350, 74, 96, n=30), INK, 5,
                       closed=True, seed=904, wavelength=60.0)
        PA.fill_poly(tile, PA.ellipse_pts(378, 326, 22, 28, n=18),
                     (246, 250, 252), seed=905, value=0.03, edge=0.5)
        # the character, cropped by the bottom edge, wiping his mouth
        SC.fullbody(d, 950, 820, 420, pose='armscrossed', expression='worried',
                    seed=906)
        D.draw_label(tile, 'POISON', center=(950, 250), color=INK, size=48)
    els.append(card(41, 42, c_droplet, kind='character'))
    els.append(cap(41, 640, 676, size=32))

    # ---- b42  the body never lets it go --------------------------------- #
    def c_body(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 910, (226, 222, 212))
        # a flat diagram: a laid-out outline with the silver still in it
        body = [(250, 620), (230, 470), (300, 400), (470, 386), (560, 430),
                (700, 428), (790, 386), (960, 402), (1020, 480), (1000, 620),
                (820, 660), (430, 660)]
        PA.fill_poly(tile, body, (214, 208, 198), seed=911, value=0.05)
        PA.hand_stroke(d, body, INK, 5, closed=True, seed=912,
                       wavelength=150.0)
        head = PA.ellipse_pts(1100, 500, 130, 140, n=34)
        PA.fill_poly(tile, head, (214, 208, 198), seed=913, value=0.05)
        PA.hand_stroke(d, head, INK, 5, closed=True, seed=914,
                       wavelength=110.0)
        # the mercury still lodged in it, drawn as droplets
        for k in range(9):
            fx = 320 + (k * 137) % 640
            fy = 430 + (k * 79) % 180
            r = 12 + (k % 4) * 7
            PA.fill_poly(tile, PA.ellipse_pts(fx, fy, r, r * 0.82, n=20),
                         SILVER, seed=915 + k, value=0.06)
        PA.hand_stroke(d, [(250, 620), (230, 470), (300, 400), (470, 386)],
                       INK, 5, closed=False, seed=925, wavelength=100.0)
        D.draw_label(tile, 'IT DOES NOT LET GO', center=(640, 150),
                     color=INK, size=40)
    els.append(card(42, 43, c_body))
    els.append(cap(42, 640, 676, size=32))

    # ===== b43-b45  the sealed chamber ================================== #
    # ---- b43  the stone door, shut, with one flat guard beside it ------- #
    def c_door(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (26, 24, 24), seed=930,
                     value=0.10)
        PA.paper_overlay(tile, seed=931)
        SC.title_backdrop(tile, 1930, col=(118, 92, 70))
        # the door, filling the frame and cropped top and bottom
        # It used to start at y=-40. Full-bleed is right, but the top edge is the
        # one edge the title owns, so the door and its three ink strokes are
        # clipped at y=104 instead of -40. The door is 620px of a 616px-tall
        # drawable area, so it still crops at the bottom and still reads as
        # bigger than the frame.
        PA.fill_rect(tile, [340, 104, 960, 760], (86, 80, 76), seed=932,
                     value=0.08)
        PA.hand_stroke(d, [(340, 104), (340, 760)], INK, 7, closed=False,
                       seed=933, wavelength=170.0)
        PA.hand_stroke(d, [(960, 104), (960, 760)], INK, 7, closed=False,
                       seed=934, wavelength=170.0)
        # the seam down the middle and the bosses
        PA.hand_stroke(d, [(650, 104), (650, 760)], INK, 6, closed=False,
                       seed=935, wavelength=190.0)
        for r in range(3):
            for c in range(2):
                PA.fill_poly(tile, PA.ellipse_pts(500 + c * 300,
                                                  180 + r * 230, 24, 24,
                                                  n=18), INK, seed=940 + r * 2 + c,
                             value=0.02, edge=0.6)
        # the painted guard, flat, standing beside it -- cropped by the bottom
        _soldier(d, 1130, 760, 460, 950, col=(168, 128, 96),
                 shade=(120, 90, 66), has_armour=False)
        D.draw_label(tile, 'SEALED', center=(650, 620), color=SILVER,
                     size=44)
    els.append(card(43, 44, c_door))
    els.append(cap(43, 640, 676, size=32, fill=PALE))

    # ---- b44  the mound in cross-section: earth, then the void ---------- #
    def c_section(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (40, 36, 34), seed=960,
                     value=0.08)
        # sky line, then the earth in three bands, then a black void
        PA.fill_rect(tile, [0, 0, W, 130], (176, 186, 196), seed=961,
                     value=0.05)
        PA.fill_rect(tile, [0, 126, W, 320], EARTH, seed=962, value=0.09)
        PA.fill_rect(tile, [0, 316, W, 560], EARTH_D, seed=963, value=0.09)
        PA.fill_rect(tile, [0, 556, W, H], (18, 16, 16), seed=964,
                     value=0.05)
        for y in (128, 318, 558):
            PA.hand_stroke(d, [(-10, y), (1290, y)], INK, 6, closed=False,
                           seed=965 + y, wavelength=190.0)
        # the outer pit, drawn in section with its figures
        for k in range(4):
            _soldier(d, 190 + k * 130, 548, 130, 970 + k, col=(150, 100, 64),
                     shade=(112, 74, 46), has_armour=False)
        PA.fill_rect(tile, [60, 380, 700, 552], (58, 48, 40), seed=975,
                     value=0.06)
        PA.hand_stroke(d, [(60, 380), (700, 380), (700, 552), (60, 552)], INK,
                       5, closed=True, seed=976, wavelength=130.0)
        # the sealed void, cropped by the bottom edge
        PA.fill_rect(tile, [780, 600, 1340, 760], (10, 10, 12), seed=977,
                     value=0.02)
        PA.hand_stroke(d, [(780, 600), (1340, 600)], INK, 7, closed=False,
                       seed=978, wavelength=150.0)
        D.draw_label(tile, 'NEVER OPENED', center=(1050, 520), color=SILVER,
                     size=40)
    els.append(card(44, 45, c_section))
    els.append(cap(44, 640, 676, size=32, fill=PALE))

    # ---- b45  FINALE: the wide dark cutaway, the door, the character ---- #
    def c_finale(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (18, 16, 18), seed=990, value=0.10)
        PA.paper_overlay(tile, seed=991)
        SC.title_backdrop(tile, 1990, col=(118, 92, 70))
        # the near rank, cropped hard by the left edge -- the army we came in on
        for k in range(2):
            _soldier(d, 60 + k * 200, 800, 620, 992 + k, col=(120, 78, 48),
                     shade=(88, 56, 36), has_armour=False)
        # the ground between us and the chamber
        PA.fill_poly(tile, [(-40, 720), (300, 560), (900, 600), (1340, 540),
                            (1340, 720)], (46, 38, 34), seed=995,
                     value=0.07)
        PA.hand_stroke(d, [(-40, 720), (300, 560), (900, 600), (1340, 540)],
                       INK, 6, closed=False, seed=996, wavelength=170.0)
        # the sealed door itself, far off and small, lit from one side
        PA.fill_rect(tile, [920, 380, 1180, 600], (58, 54, 52), seed=997,
                     value=0.08)
        PA.hand_stroke(d, [(920, 380), (1180, 380), (1180, 600),
                           (920, 600)], INK, 6, closed=True, seed=998,
                       wavelength=120.0)
        PA.fill_poly(tile, [(920, 380), (1180, 380), (1180, 600),
                            (1090, 600), (1090, 380)], (20, 20, 24), seed=999,
                     value=0.04, edge=1.6)
        # the character, cropped by the bottom edge, awed, facing the door
        SC.fullbody(d, 700, 830, 400, pose='peeking', expression='awed',
                    seed=1000)
        D.draw_label(tile, 'THE DOOR STAYS SHUT', center=(640, 150),
                     color=GOLD, size=52)
    els.append(card(45, 46, c_finale, kind='character'))
    els.append(cap(45, 640, 680, size=32, fill=PALE))

    return SC.finish(els, TITLE, clock)


# ---------------------------------------------------------------------------
# the emperor and his apparatus (b10-b16)
# ---------------------------------------------------------------------------

def _china(d, cx, cy, s, seed, kingdoms=False, unify=False):
    """A hand-drawn outline of China, `s` scaled, centred on (cx, cy).

    Deliberately crude: the brief's register is a flat register map, not a
    survey. `kingdoms` splits it into many red patches with ink borders;
    `unify` collapses those to one outline so the "one" beat reads as a change
    of STATE rather than a change of map. The outline runs past the frame on
    both sides at s >= 1.35, which is what keeps it frame-filling.
    """
    shape = [(-330, -110), (-250, -215), (-120, -240), (-20, -200),
             (110, -235), (250, -190), (320, -80), (300, 60), (250, 190),
             (120, 235), (-30, 210), (-160, 240), (-290, 170), (-345, 20)]
    outline = [(cx + px * s, cy + py * s) for px, py in shape]
    PA.fill_poly(PA.img_of(d), outline, (226, 222, 208), seed=seed,
                 value=0.06)
    PA.hand_stroke(d, outline, INK, 6, closed=True, seed=seed + 1,
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


def _script_sheet(d, cx, cy, w, h, seed):
    """A sheet of paper with columns of invented brush-stroke marks."""
    PA.fill_rect(PA.img_of(d), [cx - w / 2, cy - h / 2, cx + w / 2,
                                cy + h / 2], (250, 248, 240), seed=seed,
                 value=0.05)
    PA.hand_stroke(d, [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                       (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
                   INK, 5, closed=True, seed=seed + 1, wavelength=90.0)
    for c in range(4):
        x = cx - w * 0.34 + c * w * 0.225
        for r in range(6):
            y = cy - h * 0.36 + r * h * 0.13
            PA.hand_stroke(d, [(x, y), (x + w * 0.13, y + 4),
                               (x + w * 0.04, y + h * 0.07)],
                           INK, 4, closed=False, seed=seed + 10 + c * 6 + r,
                           wavelength=26.0)


def _weight(d, cx, base_y, w, h, seed, kind=0):
    """One bronze weight of trade. `kind` picks the silhouette so a set reads
    as a set of DIFFERENT shapes carrying the same stamp."""
    if kind == 0:
        pts = [(cx - w / 2, base_y), (cx + w / 2, base_y),
               (cx + w * 0.40, base_y - h), (cx - w * 0.40, base_y - h)]
    elif kind == 1:
        pts = [(cx - w / 2, base_y), (cx + w / 2, base_y), (cx, base_y - h)]
    elif kind == 2:
        pts = [(cx - w / 2, base_y), (cx + w / 2, base_y),
               (cx + w * 0.5, base_y - h * 0.72), (cx + w * 0.20,
                base_y - h), (cx - w * 0.20, base_y - h),
               (cx - w * 0.5, base_y - h * 0.72)]
    else:
        pts = [(cx - w / 2, base_y), (cx + w / 2, base_y),
               (cx + w * 0.44, base_y - h * 0.86), (cx, base_y - h),
               (cx - w * 0.44, base_y - h * 0.86)]
    PA.fill_poly(PA.img_of(d), pts, BRONZE, seed=seed, value=0.09)
    PA.hand_stroke(d, pts, INK, 5, closed=True, seed=seed + 1,
                   wavelength=80.0)
    PA.fill_rect(PA.img_of(d), [cx - w * 0.22, base_y - h * 0.60,
                                cx + w * 0.22, base_y - h * 0.40], INK,
                 seed=seed + 2, value=0.02, edge=0.6)


def _throne(d, cx, base_y, w, seed):
    """A flat, frontal, very large throne -- cropped by the bottom edge."""
    seat_y = base_y - w * 0.42
    PA.fill_rect(PA.img_of(d), [cx - w * 0.52, seat_y, cx + w * 0.52,
                                base_y], (112, 62, 40), seed=seed, value=0.08)
    PA.fill_rect(PA.img_of(d), [cx - w * 0.30, seat_y - w * 0.62,
                                cx + w * 0.30, seat_y], (138, 80, 50),
                 seed=seed + 1, value=0.08)
    PA.hand_stroke(d, [(cx - w * 0.52, seat_y), (cx + w * 0.52, seat_y),
                       (cx + w * 0.52, base_y), (cx - w * 0.52, base_y)],
                   INK, 6, closed=True, seed=seed + 2, wavelength=110.0)
    PA.hand_stroke(d, [(cx - w * 0.30, seat_y), (cx - w * 0.30,
                       seat_y - w * 0.62), (cx + w * 0.30,
                       seat_y - w * 0.62), (cx + w * 0.30, seat_y)], INK, 6,
                   closed=False, seed=seed + 3, wavelength=100.0)


def _flames(d, cx, base_y, h, seed):
    """Hand-drawn flames: three nested tongues, ink-outlined, orange filled."""
    for k, sc_ in enumerate((1.0, 0.72, 0.44)):
        top = base_y - h * sc_
        pts = [(cx - 150 * sc_, base_y),
               (cx - 110 * sc_, base_y - h * 0.42 * sc_),
               (cx - 40 * sc_, top),
               (cx + 30 * sc_, base_y - h * 0.56 * sc_),
               (cx + 120 * sc_, top + h * 0.18 * sc_),
               (cx + 150 * sc_, base_y)]
        col = (232, 132, 52) if k == 0 else (
            (244, 186, 78) if k == 1 else (250, 226, 150))
        PA.fill_poly(PA.img_of(d), pts, col, seed=seed + k, value=0.07)
        PA.hand_stroke(d, pts, INK, 5, closed=True, seed=seed + 10 + k,
                       wavelength=90.0)


def _book(d, x, y, w, h, seed, tilt=0.0):
    """One flat book block, rotated by `tilt` degrees, falling into the fire."""
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    pts = []
    for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2),
                   (-w / 2, h / 2)):
        pts.append((x + px * ca - py * sa, y + px * sa + py * ca))
    PA.fill_poly(PA.img_of(d), pts, (206, 176, 132), seed=seed, value=0.08)
    PA.hand_stroke(d, pts, INK, 5, closed=True, seed=seed + 1,
                   wavelength=60.0)
    PA.hand_stroke(d, [(x - w / 2 + 6, y - 4 * sa),
                       (x + w / 2 - 6, y + 4 * sa)], INK, 3, closed=False,
                   seed=seed + 2, wavelength=60.0)


# ---------------------------------------------------------------------------
# the horse (b07)
# ---------------------------------------------------------------------------

def _horse(d, x, feet_y, h, seed, col=CLAY, shade=CLAY_D, facing=-1,
           crop=False):
    """A standing clay horse, `h` px tall at the withers, `facing` -1 = left.

    REWRITTEN. The first version hung the barrel VERTICALLY and threw a long
    triangular wedge up and off the top-left corner for a neck, which put the
    head outside the frame and left the animal reading as a lollipop on
    sticks. A horse is a horizontal barrel on four legs with the neck rising
    FORWARD from the shoulder and the head at the top of it, so the silhouette
    is built in that order and every part is sized off `h`.
    """
    L = h * 0.62                      # barrel length (nose to rump)
    bw = h * 0.20                     # half-depth of the barrel
    by = feet_y - h * 0.58            # barrel centre
    img = PA.img_of(d)

    # --- four legs, front pair and back pair, each with a hock. The leg
    # positions are OFFSETS FROM x and must be added to it: leaving them as
    # bare offsets put two legs off the left edge of the frame and detached the
    # other two from the barrel entirely.
    for k, lxo in enumerate((-L * 0.34, -L * 0.26, L * 0.28, L * 0.36)):
        lx = x + lxo
        knee_y = by + bw * 0.70
        PA.hand_stroke(d, [(lx, by + bw * 0.20), (lx + facing * 6, knee_y)],
                       col if k % 2 == 0 else shade, max(6, int(h * 0.038)),
                       closed=False, seed=seed + 5 + k, wavelength=40.0)
        PA.hand_stroke(d, [(lx + facing * 6, knee_y),
                           (lx + facing * 2, feet_y)], shade,
                       max(5, int(h * 0.030)), closed=False,
                       seed=seed + 15 + k, wavelength=40.0)
        PA.fill_poly(img, [(lx - h * 0.035, feet_y - h * 0.022),
                           (lx + h * 0.035, feet_y - h * 0.022),
                           (lx + h * 0.045 + facing * h * 0.020, feet_y),
                           (lx - h * 0.045 + facing * h * 0.020, feet_y)],
                     INK, seed=seed + 25 + k, value=0.02, edge=0.5)

    # --- the barrel: a horizontal rounded mass, deeper at the chest
    barrel = [(x - L * 0.50, by - bw * 0.55),
              (x - L * 0.24, by - bw * 0.86),
              (x + L * 0.26, by - bw * 0.80),
              (x + L * 0.50, by - bw * 0.42),
              (x + L * 0.50, by + bw * 0.52),
              (x + L * 0.22, by + bw * 0.88),
              (x - L * 0.28, by + bw * 0.84),
              (x - L * 0.50, by + bw * 0.40)]
    PA.fill_poly(img, barrel, col, seed=seed + 35, value=0.09, tint=0.0,
                 band=0.0, edge=0.0, grow=2)
    PA.hand_stroke(d, barrel, INK, max(5, int(h * 0.020)), closed=True,
                   seed=seed + 36, wavelength=110.0)
    # the belly shadow, which is what makes it read as a body not a slab
    PA.fill_poly(img, [(x - L * 0.34, by + bw * 0.34),
                       (x + L * 0.30, by + bw * 0.30),
                       (x + L * 0.22, by + bw * 0.86),
                       (x - L * 0.28, by + bw * 0.82)], shade, seed=seed + 37,
                 value=0.06, tint=0.0, band=0.0, edge=0.0, grow=1)

    # --- the neck: rises FORWARD from the shoulder, thick at the base
    sh_x = x + facing * L * 0.36
    neck = [(sh_x - facing * h * 0.075, by - bw * 0.42),
            (sh_x + facing * h * 0.075, by - bw * 0.42),
            (sh_x + facing * h * 0.215, by - h * 0.40),
            (sh_x + facing * h * 0.115, by - h * 0.30)]
    PA.fill_poly(img, neck, col, seed=seed + 40, value=0.08, tint=0.0,
                 band=0.0, edge=0.0, grow=2)
    PA.hand_stroke(d, neck, INK, max(5, int(h * 0.018)), closed=True,
                   seed=seed + 41, wavelength=70.0)

    # --- the mane, in ink along the top of the neck
    PA.hand_stroke(d, [(sh_x - facing * h * 0.030, by - bw * 0.58),
                       (sh_x + facing * h * 0.130, by - h * 0.32),
                       (sh_x + facing * h * 0.205, by - h * 0.40)], INK,
                   max(5, int(h * 0.020)), closed=False, seed=seed + 42,
                   wavelength=50.0)

    # --- the head: a long wedge at the top of the neck, muzzle pointing out
    hx = sh_x + facing * h * 0.165
    hy = by - h * 0.365
    head = [(hx - facing * h * 0.020, hy - h * 0.040),
            (hx + facing * h * 0.020, hy - h * 0.048),
            (hx + facing * h * 0.135, hy + h * 0.010),
            (hx + facing * h * 0.140, hy + h * 0.062),
            (hx + facing * h * 0.010, hy + h * 0.070)]
    PA.fill_poly(img, head, col, seed=seed + 45, value=0.08, tint=0.0,
                 band=0.0, edge=0.0, grow=2)
    PA.hand_stroke(d, head, INK, max(4, int(h * 0.015)), closed=True,
                   seed=seed + 46, wavelength=50.0)
    # the ear
    PA.fill_poly(img, [(hx - facing * h * 0.010, hy - h * 0.040),
                       (hx + facing * h * 0.030, hy - h * 0.036),
                       (hx + facing * h * 0.004, hy - h * 0.088)], col,
                 seed=seed + 47, value=0.07, edge=0.6)
    # the eye
    PA.fill_poly(img, PA.ellipse_pts(hx + facing * h * 0.036, hy - h * 0.014,
                                     h * 0.013, h * 0.013, n=14), INK,
                 seed=seed + 48, value=0.02, edge=0.4)

    # --- the tail, hanging at the rump
    PA.hand_stroke(d, [(x - facing * L * 0.48, by - bw * 0.30),
                       (x - facing * L * 0.62, by + bw * 0.30),
                       (x - facing * L * 0.55, by + bw * 0.95)], INK,
                   max(5, int(h * 0.022)), closed=False, seed=seed + 50,
                   wavelength=60.0)

    # --- the harness band over the barrel
    PA.hand_stroke(d, [(x - L * 0.10, by - bw * 0.84),
                       (x - L * 0.10, by + bw * 0.86)], INK,
                   max(5, int(h * 0.020)), closed=False, seed=seed + 51,
                   wavelength=40.0)


# ---------------------------------------------------------------------------
# the bronze cranes (b34-b35)
# ---------------------------------------------------------------------------

def _crane(d, x, base_y, h, seed, broken=False, repaired=False, flip=False):
    """A flat, frontal bronze crane, `h` px tall. `broken` lays it in pieces."""
    s = -1 if flip else 1
    bw = h * 0.34                       # half-span of the body
    by = base_y - h * 0.42

    # legs
    for lx in (x - h * 0.06, x + h * 0.06):
        PA.hand_stroke(d, [(lx, by + h * 0.22), (lx + s * 14, base_y)],
                       BRONZE, max(5, int(h * 0.030)), closed=False,
                       seed=seed + 1, wavelength=50.0)

    # body
    body = PA.ellipse_pts(x, by, bw, h * 0.19, n=36)
    PA.fill_poly(PA.img_of(d), body, BRONZE, seed=seed + 2, value=0.09)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 3,
                   wavelength=110.0)

    # neck + head, which is the whole silhouette of a crane
    neck = [(x + s * bw * 0.62, by - h * 0.06),
            (x + s * bw * 0.96, by - h * 0.40),
            (x + s * bw * 0.72, by - h * 0.56),
            (x + s * bw * 0.50, by - h * 0.34)]
    PA.fill_poly(PA.img_of(d), neck, BRONZE, seed=seed + 4, value=0.08)
    PA.hand_stroke(d, neck, INK, 5, closed=True, seed=seed + 5,
                   wavelength=70.0)
    headp = [(x + s * bw * 0.74, by - h * 0.54),
             (x + s * bw * 1.16, by - h * 0.60),
             (x + s * bw * 1.14, by - h * 0.48),
             (x + s * bw * 0.72, by - h * 0.42)]
    PA.fill_poly(PA.img_of(d), headp, BRONZE, seed=seed + 6, value=0.08)
    PA.hand_stroke(d, headp, INK, 4, closed=True, seed=seed + 7,
                   wavelength=50.0)
    # the wing, in flat plates
    PA.hand_stroke(d, [(x - s * bw * 0.5, by - h * 0.06),
                       (x - s * bw * 0.9, by - h * 0.20),
                       (x - s * bw * 0.4, by - h * 0.22)], INK, 5,
                   closed=False, seed=seed + 8, wavelength=60.0)

    if broken:
        # the pieces it broke into, on the dirt in front
        for k in range(5):
            px = x - bw + (k * 121) % (bw * 2)
            py = base_y + 10 + (k * 29) % 50
            PA.fill_poly(PA.img_of(d),
                         PA.ellipse_pts(px, py, 34, 17, n=18), BRONZE,
                         seed=seed + 20 + k, value=0.08)
            PA.hand_stroke(d, PA.ellipse_pts(px, py, 34, 17, n=18), INK, 4,
                           closed=True, seed=seed + 30 + k, wavelength=40.0)
        # the break in the neck
        PA.hand_stroke(d, [(x + s * bw * 0.70, by - h * 0.34),
                           (x + s * bw * 0.86, by - h * 0.26)], SC.PAGE, 9,
                       closed=False, seed=seed + 40, wavelength=30.0)
    if repaired:
        # the modern adhesive over the joins, deliberately a cool grey-blue
        for k in range(3):
            PA.hand_stroke(d, [(x + s * bw * (0.55 + 0.18 * k), by),
                               (x + s * bw * (0.70 + 0.18 * k), by)],
                           BLUE_L, 7, closed=False, seed=seed + 50 + k,
                           wavelength=30.0)


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    argv = sys.argv[1:]
    sc = build()
    print('%s: %d elements, %.1fs' % (TITLE, len(sc.elements), sc.duration))
    if '--preview' in argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview.png'), n=12)
    if '--frames' in argv:
        out = os.path.join(SEG, '_frames')
        os.makedirs(out, exist_ok=True)
        for i in [int(a) for a in argv[argv.index('--frames') + 1:]]:
            t = clock_t = SC.BeatClock(BEATS).at('b%02d' % i, 0) + 0.35
            E3.render_frame(sc, t).save(os.path.join(out, 'b%02d.png' % i))
            print('frame -> %s/b%02d.png' % (out, i))
