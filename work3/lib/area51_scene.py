"""area51 scene -- chapter 2 of the bunker film (Groom Lake / the base with no name).

Mirrors the proven structure of pinegap_scene.py end to end. Everything
structural -- caption handoff, one-card-per-beat, phrase clock, the cropped
character close-up, the render drivers -- comes from scene_common; this file
declares only Area 51's cards.

ONE CARD PER BEAT, AND EACH CARD PAINTS ITS OWN WHOLE FRAME. 34 beats, each a
single short sentence, and beats.json gives each an exact [start, end], so the
card boundaries are never guessed. Every card function fills its own background
first, then its subject, so one card's art cannot survive into the next.

SUBJECTS (all drawn from primitives; none reproduced):
  the flat alkali playa, the fence + warning signs, the bunkers/hangars, the
  runway, the white observation tower, the Groom Lake sign, a Nevada map, the
  black ambiguous delta craft, a calendar, the Hangar 18 door, a budget sheet,
  a 1989 TV, a microphone, the FBI file stack, guards and spotlights.

FRAME-FILL. The dominant subject owns the frame and is cropped BY an edge. The
recurring defect in this project is a small subject centred in empty space; each
card below scales its subject up and lets supporting geometry exit the sides.

CADENCE. Still-dominant, one cut per sentence (34 cuts in ~80s). No motion
tracks -- the one thing the narrator describes as moving (a blinking light) is
drawn as a static bright halo, matching pinegap's proven still-dominant approach.

Run:  python lib/area51_scene.py --preview --video
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
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'area51'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Area 51'

# The two night cards carry an intentional lit stone course on the title band, so
# band_intrusions exempts exactly those rows (see its TITLE_BACKDROP handling).
# Only the part inside the band is declared: rows below it are ordinary art and
# must still be checked.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# Nevada high desert at noon. Bleached sky, alkali-white ground, ONE strong
# warning accent (red/orange) plus a deep shadow. Flat painterly fills.
INK = SC.INK
RED = (198, 48, 40)            # the single warning accent: signs, stamps, red line
SKY = (206, 214, 220)          # bleached, washed sky
ALKALI = (232, 230, 222)       # alkali-white dry-lake ground
DUST = (208, 196, 172)         # slightly warmer sand for depth bands
PLATA = (198, 202, 200)        # the playa's pale crust
CONCRETE = (206, 200, 188)     # bunkers / hangar walls
STEEL = (150, 158, 168)        # poles, rails, structure
MOUNTAIN = (150, 154, 160)      # the thin dark mountain strip on the horizon
PAPER = (246, 244, 238)        # documents, calendar, budget sheet
NIGHT = (28, 30, 42)           # night sky
NIGHT_G = (18, 20, 28)         # night ground
CRAFT = (46, 48, 58)           # the black ambiguous delta craft

HZ = int(H * 0.62)             # horizon; sky_bg uses the same fraction


# ---------------------------------------------------------------------------
# background / ground primitives
# ---------------------------------------------------------------------------

def _playa(tile, seed, sky=SKY, ground=ALKALI, hz=HZ):
    """Full-frame desert exterior. Call at the TOP of every exterior card."""
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


def _mountain_strip(d, y, seed, h=52):
    """A dark mountain range riding the horizon -- the far rim of the lake.

    The first version used h=26, which rendered as a thin grey wire rather than
    a landform: at 26px the peaks barely cleared the horizon line and the strip
    read as a scratch. h=52 plus a second, paler range behind it gives the
    horizon real depth, and it is now dark enough to hold its own against the
    bleached sky.
    """
    far = []
    n = 30
    for i in range(n + 1):
        u = i / float(n)
        x = -40 + (W + 80) * u
        far.append((x, y - h * 0.42 * (0.3 + 0.7 * abs(math.sin(u * 7.3 + 1.9)))))
    PA.fill_poly(PA.img_of(d), far, (176, 180, 184), seed=seed + 3, value=0.04)

    pts = [(-40, y)]
    for i in range(n + 1):
        u = i / float(n)
        x = -40 + (W + 80) * u
        yy = y - h * (0.30 + 0.70 * abs(math.sin(u * 9.1 + 0.6)))
        pts.append((x, yy))
    pts.append((W + 40, y))
    PA.fill_poly(PA.img_of(d), pts, MOUNTAIN, seed=seed, value=0.05)
    PA.hand_stroke(d, pts, INK, 5, closed=False, seed=seed + 1, wavelength=140.0)


# ---------------------------------------------------------------------------
# the fence (this chapter's signature object)
# ---------------------------------------------------------------------------

def _fence(d, x0, y_base, x1, height, seed, n_posts=7, mesh=True,
           post_col=INK, rail_col=INK):
    """A wire fence standing on `y_base` running x0 -> x1.

    Same construction as pinegap (dense vertical wires crossed by three rails)
    so it reads as security mesh, with the rail/post colours parameterised so
    the NIGHT cards can pass a near-black wire.
    """
    top = y_base - height
    PA.hand_stroke(d, [(x0, top), (x1, top)], rail_col, 7, seed=seed,
                   wavelength=130.0)
    PA.hand_stroke(d, [(x0, y_base), (x1, y_base)], rail_col, 7, seed=seed + 1,
                   wavelength=130.0)
    step = (x1 - x0) / float(n_posts)
    for i in range(n_posts + 1):
        x = x0 + i * step
        PA.hand_stroke(d, [(x, top - 26), (x, y_base + 16)], post_col, 11,
                       seed=seed + 2 + i, wavelength=100.0)
        PA.hand_stroke(d, [(x - 14, top + 16), (x + 14, top - 8)], post_col, 5,
                       seed=seed + 40 + i, wavelength=70.0)
    if mesh:
        step_v = 26
        n_v = int(abs(x1 - x0) / step_v)
        wire = (108, 116, 126) if post_col == INK else (58, 62, 74)
        for i in range(n_v):
            x = x0 + i * step_v
            PA.hand_stroke(d, [(x, top), (x, y_base)], wire, 3,
                           seed=seed + 90 + i, wavelength=90.0)
        for k in range(1, 4):
            y = top + (y_base - top) * k / 4.0
            PA.hand_stroke(d, [(x0, y), (x1, y)], wire, 3,
                           seed=seed + 160 + k, wavelength=110.0)


# ---------------------------------------------------------------------------
# the craft -- an AMBIGUOUS dark delta/diamond, never spaceship clipart
# ---------------------------------------------------------------------------

def _delta(d, cx, cy, s, seed, colour=CRAFT, accent=RED):
    """A wide, flat delta/diamond silhouette with a faint red glint beneath.

    WHY A DELTA AND NOT A SPACESHIP. The brief forbids spaceship clipart; the
    shape that reads as "unidentified" is a wide, thin, ambiguous delta with no
    windows, no engines, and a slightly domed centre -- a silhouette you cannot
    quite place. The faint red glow under the belly is the only colour on it,
    and it doubles as the "lights" motif on later cards.
    """
    top = [(cx, cy - s * 0.34), (cx + s * 0.42, cy - s * 0.20),
           (cx + s * 1.00, cy + s * 0.18), (cx + s * 0.66, cy + s * 0.30),
           (cx, cy + s * 0.36), (cx - s * 0.66, cy + s * 0.30),
           (cx - s * 1.00, cy + s * 0.18), (cx - s * 0.42, cy - s * 0.20)]
    PA.fill_poly(PA.img_of(d), top, colour, seed=seed, value=0.05)
    PA.hand_stroke(d, top, INK, 6, closed=True, seed=seed + 1, wavelength=140.0)
    # a domed centre line so the top isn't a flat facet
    PA.hand_stroke(d, [(cx - s * 0.40, cy - s * 0.19),
                       (cx, cy - s * 0.33), (cx + s * 0.40, cy - s * 0.19)],
                   (78, 82, 96), 3, seed=seed + 2, wavelength=90.0)
    # faint red under-glow
    PA.hand_stroke(d, [(cx - s * 0.30, cy + s * 0.32),
                       (cx + s * 0.30, cy + s * 0.32)], accent, 5,
                   seed=seed + 3, wavelength=60.0)


def _jet(d, cx, cy, s, seed, colour=(126, 134, 146)):
    """A small jet airliner seen from the side, nose to the right.

    WHY IT WAS REBUILT. The first attempt drew the fuselage as a thin quadrilateral
    and the wing as a separate quad that overlapped it; the two merged into one
    grey lozenge that read as a paper dart, not an aircraft. An airliner silhouette
    is carried by three things and only three: a long LENS-shaped fuselage that
    tapers to a point at the nose, a swept wing that sits clearly BELOW and BEHIND
    the fuselage line, and a tall tail fin at the back. Each is now separated in
    value and in position so the eye reads them as three parts.
    """
    img = PA.img_of(d)
    # fuselage: a lens, pointed at the nose (right), rounded at the tail
    fus = []
    n = 26
    for i in range(n + 1):
        u = i / float(n)                       # 0 = tail, 1 = nose
        x = cx - s * 0.72 + s * 1.44 * u
        # half-thickness: fat amidships, pinched at both ends
        th = s * 0.17 * math.sin(math.pi * min(1.0, u * 1.12)) ** 0.55
        fus.append((x, cy - th))
    for i in range(n + 1):
        u = 1.0 - i / float(n)
        x = cx - s * 0.72 + s * 1.44 * u
        th = s * 0.17 * math.sin(math.pi * min(1.0, u * 1.12)) ** 0.55
        fus.append((x, cy + th))
    PA.fill_poly(img, fus, colour, seed=seed, value=0.06)
    PA.hand_stroke(d, fus, INK, 5, closed=True, seed=seed + 1, wavelength=110.0)
    # a darker belly stripe so the tube reads as round, not flat
    PA.hand_stroke(d, [(cx - s * 0.56, cy + s * 0.11), (cx + s * 0.44, cy + s * 0.10)],
                   (96, 104, 116), 5, seed=seed + 2, wavelength=80.0)
    # swept wing, clearly below the fuselage and set back from the nose
    wing = [(cx - s * 0.14, cy + s * 0.10), (cx - s * 0.40, cy + s * 0.40),
            (cx - s * 0.10, cy + s * 0.42), (cx + s * 0.16, cy + s * 0.12)]
    PA.fill_poly(img, wing, (108, 116, 128), seed=seed + 3, value=0.06)
    PA.hand_stroke(d, wing, INK, 5, closed=True, seed=seed + 4, wavelength=80.0)
    # tail fin, tall, at the very back
    fin = [(cx - s * 0.66, cy - s * 0.06), (cx - s * 0.66, cy - s * 0.42),
           (cx - s * 0.44, cy - s * 0.40), (cx - s * 0.42, cy - s * 0.08)]
    PA.fill_poly(img, fin, colour, seed=seed + 5, value=0.06)
    PA.hand_stroke(d, fin, INK, 5, closed=True, seed=seed + 6, wavelength=70.0)
    # cockpit window
    d.ellipse([cx + s * 0.44, cy - s * 0.08, cx + s * 0.60, cy - s * 0.01],
              fill=INK)


def _runway(d, x0, y_far, x1, y_near, w_far, w_near, seed):
    """A paved runway receding to a vanishing point, painted ON the ground.

    The first version drew the runway as one 40px hand_stroke, which rendered as
    a grey pipe with a round cap lying on the desert -- it read as a length of
    hose, not a runway. A runway is a flat trapezoid on the ground plane: wide at
    the near end, narrow at the far end, with a dashed centreline. That shape is
    what says "airstrip"; the round cap was the whole tell that it wasn't one.
    """
    img = PA.img_of(d)
    trap = [(x0 - w_near, y_near), (x0 + w_near, y_near),
            (x1 + w_far, y_far), (x1 - w_far, y_far)]
    PA.fill_poly(img, trap, (128, 130, 134), seed=seed, value=0.05)
    PA.hand_stroke(d, trap, INK, 5, closed=True, seed=seed + 1, wavelength=120.0)
    # dashed centreline, dashes widening toward the viewer
    n = 7
    for i in range(n):
        u0, u1 = i / float(n), (i + 0.55) / float(n)
        w0 = w_far + (w_near - w_far) * u0
        w1 = w_far + (w_near - w_far) * u1
        yy0 = y_far + (y_near - y_far) * u0
        yy1 = y_far + (y_near - y_far) * u1
        cx0 = x0 + (x1 - x0) * u0
        cx1 = x0 + (x1 - x0) * u1
        PA.fill_poly(img, [(cx0 - w0 * 0.06, yy0), (cx0 + w0 * 0.06, yy0),
                           (cx1 + w1 * 0.06, yy1), (cx1 - w1 * 0.06, yy1)],
                     (238, 234, 224), seed=seed + 2 + i, value=0.03)


def _balloon_low(tile, d, cx, cy, r, seed, colour=(196, 84, 70)):
    """A HALF-DEFLATED balloon sagging over the fence.

    The first version drew a full circle plus a few sag strokes, and a circle
    cannot say "deflated" -- it read as a beach ball. A sagging balloon is
    pear-shaped: wide and taut across the TOP, pinched where the gas has gone
    out, with a drooping point at the bottom. The outline is generated as a
    radius that varies with angle so the silhouette itself carries the deflation.
    """
    pts = []
    n = 72
    for i in range(n):
        a = 2.0 * math.pi * i / n
        # fat and round across the top (a ~ -pi/2), pinched at the bottom
        squash = 1.0 + 0.22 * math.sin(a)          # fatter on top
        pinch = 1.0 - 0.30 * max(0.0, math.sin(a)) ** 2   # squeezed low down
        rr = r * squash * pinch
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 1.06))
    PA.fill_poly(tile, pts, colour, seed=seed, value=0.08)
    PA.hand_stroke(d, pts, INK, 6, closed=True, seed=seed + 1, wavelength=140.0)
    # the sagging point and its tether
    PA.hand_stroke(d, [(cx - r * 0.10, cy + r * 0.72),
                       (cx + r * 0.04, cy + r * 0.96),
                       (cx + r * 0.10, cy + r * 1.16)], (150, 60, 52), 5,
                   seed=seed + 2, wavelength=70.0)


def _hand_sketch(d, hx, hy, seed, flip=1):
    """A loose sketching hand: a rounded palm with three long spread fingers.

    The first version drew a small hexagonal palm against thick stubby finger
    strokes; at ship size the fingers overwhelmed the palm and the whole thing
    read as a claw/scribble rather than a hand. A hand reads from the palm
    FIRST -- so the palm is now the largest, fully-filled form and the fingers
    are thin, long, and clearly separate from its top edge.
    """
    # palm: a rounded quad, the dominant mass
    palm = [(hx - flip * 34, hy + 52), (hx - flip * 40, hy + 6),
            (hx - flip * 22, hy - 30), (hx + flip * 22, hy - 30),
            (hx + flip * 40, hy + 6), (hx + flip * 34, hy + 52)]
    PA.fill_poly(PA.img_of(d), palm, (228, 190, 160), seed=seed, value=0.04,
                 edge=2.0)
    PA.hand_stroke(d, palm, INK, 5, closed=True, seed=seed + 1, wavelength=90.0)
    # three long fingers rising from the palm's top edge, splayed apart
    for k, (bx, tip_dx, tip_dy) in enumerate(((-24, -34, -104),
                                              (0, 0, -118),
                                              (24, 32, -100))):
        base = (hx + flip * bx, hy - 26)
        tip = (hx + flip * (bx + tip_dx), hy + tip_dy)
        PA.hand_stroke(d, [base, tip], (228, 190, 160), 15, seed=seed + 2 + k,
                       wavelength=70.0)
        PA.hand_stroke(d, [base, tip], INK, 5, seed=seed + 6 + k, wavelength=70.0)
    # thumb, angled off the palm's lower-left
    tb = (hx - flip * 34, hy + 18)
    tt = (hx - flip * 74, hy - 12)
    PA.hand_stroke(d, [tb, tt], (228, 190, 160), 14, seed=seed + 10,
                   wavelength=60.0)
    PA.hand_stroke(d, [tb, tt], INK, 5, seed=seed + 11, wavelength=60.0)


# ---------------------------------------------------------------------------
# buildings
# ---------------------------------------------------------------------------

def _bunker(d, x, y_base, w, h, seed, colour=CONCRETE, roof=True):
    """A low flat-roofed bunker/hangar block. Half in shadow on the right."""
    body = [(x, y_base), (x, y_base - h), (x + w, y_base - h), (x + w, y_base)]
    PA.fill_poly(PA.img_of(d), body, colour, seed=seed, value=0.07)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    if roof:
        PA.hand_stroke(d, [(x, y_base - h), (x + w, y_base - h)], INK, 4,
                       seed=seed + 2, wavelength=110.0)
    # shadow side: a darker right-hand band
    sh = [(x + w * 0.72, y_base - h), (x + w, y_base - h),
          (x + w, y_base), (x + w * 0.72, y_base)]
    PA.fill_poly(PA.img_of(d), sh, (178, 172, 160), seed=seed + 3, value=0.05)


def _hangar(d, x, y_base, w, h, seed, colour=CONCRETE):
    """A big barrel-roof hangar seen head-on (or three-quarter): curved roof,
    dark open door slot."""
    roof = []
    n = 30
    for i in range(n + 1):
        u = i / float(n)
        xx = x + w * u
        yy = y_base - h * (0.42 + 0.58 * math.sin(math.pi * u) ** 0.6)
        roof.append((xx, yy))
    wall = [(x, y_base), (x, roof[0][1])] + roof + [(x + w, y_base)]
    PA.fill_poly(PA.img_of(d), wall, colour, seed=seed, value=0.07)
    PA.hand_stroke(d, roof, INK, 6, closed=False, seed=seed + 1, wavelength=140.0)
    PA.hand_stroke(d, [(x, roof[0][1]), (x, y_base)], INK, 6, seed=seed + 2,
                   wavelength=100.0)
    PA.hand_stroke(d, [(x + w, roof[-1][1]), (x + w, y_base)], INK, 6,
                   seed=seed + 3, wavelength=100.0)
    PA.hand_stroke(d, [(x, y_base), (x + w, y_base)], INK, 6, seed=seed + 4,
                   wavelength=140.0)
    # dark door slot in the middle
    dw = w * 0.34
    dx0 = x + w * 0.5 - dw * 0.5
    door = [(dx0, y_base), (dx0, y_base - h * 0.62),
            (dx0 + dw, y_base - h * 0.62), (dx0 + dw, y_base)]
    PA.fill_poly(PA.img_of(d), door, (58, 62, 74), seed=seed + 5, value=0.04)
    PA.hand_stroke(d, door, INK, 5, closed=True, seed=seed + 6, wavelength=100.0)


def _tower(d, cx, y_base, h, seed):
    """The tall white observation tower -- a tapered lattice mast with a small
    glazed cab near the top."""
    w_bot = 34
    w_top = 20
    # four splayed legs from the ground up to the cab
    for sx in (-1, 1):
        for sy_off in (0,):
            PA.hand_stroke(d, [(cx + sx * w_bot, y_base),
                               (cx + sx * w_top, y_base - h)], INK, 6,
                           seed=seed + (7 if sx > 0 else 8), wavelength=120.0)
    # cross bracing
    n_b = 6
    for i in range(n_b):
        u0 = i / float(n_b)
        u1 = (i + 1) / float(n_b)
        y0 = y_base - h * u0
        y1 = y_base - h * u1
        xw0 = w_bot + (w_top - w_bot) * u0
        xw1 = w_bot + (w_top - w_bot) * u1
        PA.hand_stroke(d, [(cx - xw0, y0), (cx + xw1, y1)], (140, 148, 158), 3,
                       seed=seed + 20 + i, wavelength=90.0)
        PA.hand_stroke(d, [(cx + xw0, y0), (cx - xw1, y1)], (140, 148, 158), 3,
                       seed=seed + 30 + i, wavelength=90.0)
    # the cab
    cw = 56
    cy = y_base - h
    cab = [(cx - cw, cy), (cx - cw, cy - 62), (cx + cw, cy - 62), (cx + cw, cy)]
    PA.fill_poly(PA.img_of(d), cab, (236, 236, 232), seed=seed + 9, value=0.05)
    PA.hand_stroke(d, cab, INK, 6, closed=True, seed=seed + 10, wavelength=90.0)
    # cab glazing
    gl = [(cx - cw + 8, cy - 8), (cx - cw + 8, cy - 54),
          (cx + cw - 8, cy - 54), (cx + cw - 8, cy - 8)]
    PA.fill_poly(PA.img_of(d), gl, (128, 156, 168), seed=seed + 11, value=0.06)
    PA.hand_stroke(d, gl, INK, 4, closed=True, seed=seed + 12, wavelength=70.0)
    PA.hand_stroke(d, [(cx, cy - 62), (cx + 4, cy - 96)], INK, 5, seed=seed + 13,
                   wavelength=60.0)


def _camera_pole(d, cx, y_base, h, seed, lens_dir=1):
    """A security camera on a tall pole, lens angled down along the wire."""
    PA.hand_stroke(d, [(cx, y_base), (cx, y_base - h)], STEEL, 10, seed=seed,
                   wavelength=110.0)
    top_y = y_base - h
    PA.hand_stroke(d, [(cx, top_y), (cx + lens_dir * 26, top_y - 6)], INK, 6,
                   seed=seed + 1, wavelength=60.0)
    # camera body
    bw, bh = 44, 26
    bx = cx + lens_dir * 26
    by = top_y - 6 - bh * 0.5
    body = [(bx - lens_dir * bw * 0.4, by - bh * 0.5),
            (bx + lens_dir * bw * 0.6, by - bh * 0.5 + 6),
            (bx + lens_dir * bw * 0.6, by + bh * 0.5 + 6),
            (bx - lens_dir * bw * 0.4, by + bh * 0.5)]
    PA.fill_poly(PA.img_of(d), body, (168, 172, 176), seed=seed + 2, value=0.06)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 3, wavelength=60.0)
    # lens hood pointing down/out
    lens = [(bx + lens_dir * bw * 0.5, by - 6), (bx + lens_dir * bw * 0.86, by + 4),
            (bx + lens_dir * bw * 0.86, by + 16), (bx + lens_dir * bw * 0.5, by + 12)]
    PA.fill_poly(PA.img_of(d), lens, INK, seed=seed + 4, value=0.03)
    PA.hand_stroke(d, lens, INK, 4, closed=True, seed=seed + 5, wavelength=50.0)
    d.ellipse([bx + lens_dir * bw * 0.62 - 5, by + 6, bx + lens_dir * bw * 0.62 + 5,
               by + 16], fill=RED)


def _spotlight(d, cx, cy, s, seed, on=True):
    """A guard/searchlight: a cone of light with a lamp head. If `on`, a bright
    core; if off, just the housing."""
    img = PA.img_of(d)
    cone = [(cx, cy), (cx - s * 0.5, cy + s * 1.5), (cx + s * 0.7, cy + s * 1.5)]
    PA.fill_poly(img, cone, (232, 226, 208), seed=seed, value=0.05)
    lamp = [(cx - s * 0.28, cy - s * 0.2), (cx + s * 0.28, cy - s * 0.2),
            (cx + s * 0.18, cy + s * 0.12), (cx - s * 0.18, cy + s * 0.12)]
    PA.fill_poly(img, lamp, (140, 146, 154), seed=seed + 1, value=0.06)
    PA.hand_stroke(d, lamp, INK, 5, closed=True, seed=seed + 2, wavelength=50.0)
    if on:
        d.ellipse([cx - s * 0.16, cy + s * 0.02, cx + s * 0.16, cy + s * 0.3],
                  fill=RED)


# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------

def _calendar(d, cx, cy, w, h, seed, year, circle_year=None):
    """A calendar page: a paper sheet, a red header band, a grid of day boxes, a
    big year. If `circle_year`, a red pencil circle is drawn around the year."""
    sheet = [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
    PA.fill_poly(PA.img_of(d), sheet, PAPER, seed=seed, value=0.05)
    PA.hand_stroke(d, sheet, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    # header band + rings
    PA.fill_rect(PA.img_of(d), [cx - w, cy - h, cx + w, cy - h + h * 0.22], RED,
                 seed=seed + 2, value=0.06)
    for k in (-1, 1):
        rx = cx + k * w * 0.5
        PA.hand_stroke(d, [(rx, cy - h - 12), (rx, cy - h + h * 0.30)], INK, 5,
                       seed=seed + 3 + k, wavelength=50.0)
    # day grid
    gx0, gy0 = cx - w * 0.86, cy - h * 0.62
    gw, gh = w * 1.72, h * 1.20
    for c in range(7):
        for r in range(4):
            x0 = gx0 + gw * c / 7.0
            y0 = gy0 + gh * r / 4.0
            PA.hand_stroke(d, [(x0, y0), (x0 + gw / 7.0, y0),
                               (x0 + gw / 7.0, y0 + gh / 4.0), (x0, y0 + gh / 4.0)],
                           (198, 196, 188), 2, seed=seed + 10 + r * 7 + c,
                           wavelength=60.0)
    # the year, big
    D.draw_number(PA.img_of(d), str(year), center=(cx, cy + h * 0.30), color=INK,
                  size=int(h * 0.5))
    if circle_year:
        ring = PA.ellipse_pts(cx, cy + h * 0.30, w * 0.72, h * 0.40, n=48)
        PA.hand_stroke(d, ring, RED, 7, closed=True, seed=seed + 5,
                       wavelength=140.0)


def _file_stack(d, cx, cy, w, seed, n=5, stamp=None):
    """A stack of manila pages seen slightly from above, with a red stamp on the
    top sheet if given."""
    img = PA.img_of(d)
    hh = 16
    for i in range(n):
        y = cy + i * hh
        off = (i % 2) * 10 - 5
        sheet = [(cx - w + off, y), (cx + w + off, y),
                 (cx + w + off - 6, y - hh), (cx - w + off - 6, y - hh)]
        PA.fill_poly(img, sheet, (238, 232, 214) if i % 2 else (232, 226, 206),
                     seed=seed + i, value=0.05)
        PA.hand_stroke(d, sheet, INK, 4, closed=True, seed=seed + n + i,
                       wavelength=80.0)
    if stamp:
        top = cy + (n - 1) * hh - hh
        D.draw_label(img, stamp, center=(cx, top + hh * 0.5), color=RED, size=34,
                     outline=INK, outline_w=2)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def card(i, j, draw, kind='subject', seed=0, motion=None):
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        return E3.E('card%02d' % i, kind, draw, at=T(i), until=end,
                    motion=motion)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # page tooth under everything
    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ---- b01  the hook: a fence across nothing --------------------------- #
    def c_empty(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 5)
        _mountain_strip(d, HZ, 6)
        _fence(d, -40, 640, W + 40, 260, 7, n_posts=9)
    els.append(card(1, 2, c_empty))
    els.append(cap(1, W // 2, 240, size=32))

    # ---- b02  close on a blank fence panel, nothing behind --------------- #
    def c_blankpanel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 9)
        _fence(d, -40, 700, W + 40, 560, 10, n_posts=4)
    els.append(card(2, 3, c_blankpanel))
    els.append(cap(2, W // 2, 240, size=32))

    # ---- b03  TITLE: AREA 51 stamped over the fence ---------------------- #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 13)
        _mountain_strip(d, HZ, 14)
        _fence(d, -40, 660, W + 40, 220, 15, n_posts=8)
        D.draw_label(tile, 'AREA 51', center=(660, 300), color=INK, size=120)
        D.draw_label(tile, 'THE BASE WITH NO NAME', center=(660, 400), color=RED,
                     size=40, outline=INK, outline_w=2)
        SC.fullbody(d, 200, 700, 430, pose='standing', expression='deadpan',
                    seed=16)
    els.append(card(3, 4, c_title, kind='character'))
    els.append(cap(3, 300, 300, size=34, fill=RED))

    # ---- b04  character close-up: the name that is not a name ----------- #
    def c_noname(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 19)
        SC.closeup(d, 300, 360, 210, 'skeptic', 20)
        D.draw_bubble(tile, 'no name', (900, 260), tail_to=(520, 380))
    els.append(card(4, 5, c_noname, kind='character'))
    els.append(cap(4, 940, 620, size=30, fill=RED))

    # ---- b05  the dry lake bed, cracked, to the horizon ------------------ #
    def c_lake(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 23)
        _mountain_strip(d, HZ, 24)
        # polygonal salt-crust cracks on the near ground. The first pass used a
        # 3px pale line, which the painterly fill washed out almost entirely --
        # the ground read as blank paper. The cracks are the SUBJECT here, so
        # they are drawn dark and thick, and each row is broken into offset
        # segments so they read as a cracked polygon network, not as stripes.
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
            # short cross-links between rows -> the polygonal net
            for j in range(6):
                x0 = 60 + j * 210 + k * 40
                PA.hand_stroke(d, [(x0, y + amp * math.sin(x0 * 0.011 + k * 1.7)),
                                   (x0 + 34, rows[k + 1] if k + 1 < len(rows)
                                    else y + 90)],
                               (176, 172, 162), 4, seed=40 + k * 8 + j,
                               wavelength=70.0)
        D.draw_label(tile, 'DRY LAKE BED', center=(640, 230), color=INK, size=44)
    els.append(card(5, 6, c_lake))
    els.append(cap(5, W // 2, 660, size=32))

    # ---- b06  map of Nevada, dot in the north-east ---------------------- #
    def c_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=27, value=0.05)
        PA.paper_overlay(tile, seed=28)
        # Nevada-ish blob, cropped large so it owns the frame
        land = [(500, 122), (762, 138), (944, 236), (984, 424), (902, 616),
                (640, 676), (470, 562), (432, 316)]
        PA.fill_poly(tile, land, (208, 190, 146), seed=29, value=0.07)
        PA.hand_stroke(d, land, INK, 7, closed=True, seed=30, wavelength=150.0)
        D.draw_label(tile, 'NEVADA', center=(600, 380), color=INK, size=54)
        # a dot north-east of centre, with a stem down to a label
        dx, dy = 830, 260
        d.ellipse([dx - 16, dy - 16, dx + 16, dy + 16], fill=RED)
        PA.hand_stroke(d, [(dx, dy + 18), (dx, dy + 90)], RED, 5, seed=31,
                       wavelength=70.0)
        D.draw_label(tile, 'Groom Lake', center=(1010, 360), color=RED, size=32,
                     outline=INK, outline_w=2)
    els.append(card(6, 7, c_map))
    els.append(cap(6, W // 2, 700, size=32))

    # ---- b07  the GROOM LAKE sign on a leaning post ---------------------- #
    def c_groomsign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 33)
        _mountain_strip(d, HZ, 34)
        # sign board
        sb = [(180, 240), (900, 200), (920, 400), (200, 440)]
        PA.fill_poly(tile, sb, (222, 214, 190), seed=35, value=0.08)
        PA.hand_stroke(d, sb, INK, 7, closed=True, seed=36, wavelength=150.0)
        D.draw_label(tile, 'GROOM LAKE', center=(550, 320), color=INK, size=56)
        # leaning post
        PA.hand_stroke(d, [(300, 430), (270, 660)], (128, 118, 100), 16,
                       seed=37, wavelength=90.0)
        PA.hand_stroke(d, [(760, 410), (790, 660)], (128, 118, 100), 16,
                       seed=38, wavelength=90.0)
    els.append(card(7, 8, c_groomsign))
    els.append(cap(7, W // 2, 200, size=32))

    # ---- b08  a second sign: one word in red, ARRESTED ------------------ #
    def c_arrestsign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 39)
        # a second, smaller sign nailed below
        sb = [(140, 320), (860, 300), (876, 520), (156, 540)]
        PA.fill_poly(tile, sb, (228, 222, 206), seed=40, value=0.07)
        PA.hand_stroke(d, sb, INK, 7, closed=True, seed=41, wavelength=150.0)
        D.draw_label(tile, 'RESTRICTED AREA', center=(508, 380), color=INK,
                     size=42)
        D.draw_label(tile, 'VIOLATORS WILL BE ARRESTED', center=(508, 470),
                     color=RED, size=34, outline=INK, outline_w=2)
        PA.hand_stroke(d, [(260, 530), (240, 680)], (128, 118, 100), 14,
                       seed=42, wavelength=80.0)
        PA.hand_stroke(d, [(740, 520), (770, 680)], (128, 118, 100), 14,
                       seed=43, wavelength=80.0)
    els.append(card(8, 9, c_arrestsign))
    els.append(cap(8, W // 2, 660, size=30))

    # ---- b09  nobody will say: character shrugging at the fence ---------- #
    def c_nobody(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 45)
        _fence(d, -40, 660, W + 40, 240, 46, n_posts=8)
        SC.fullbody(d, 620, 700, 470, pose='shrug', expression='shrug'
                    if False else 'skeptic', seed=47)
        D.draw_bubble(tile, 'no answer', (320, 250), tail_to=(520, 380))
    els.append(card(9, 10, c_nobody, kind='character'))
    els.append(cap(9, 960, 250, size=30, fill=RED))

    # ---- b10  the fence runs for miles, off both edges ------------------- #
    def c_miles(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 49)
        _mountain_strip(d, HZ, 50)
        _fence(d, -120, 700, W + 120, 300, 51, n_posts=12)
    els.append(card(10, 11, c_miles))
    els.append(cap(10, W // 2, 230, size=32))

    # ---- b11  it surrounds nothing: fence from behind, character back --- #
    def c_nothing(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 55)
        _fence(d, -60, 700, W + 60, 420, 56, n_posts=7)
        SC.fullbody(d, 980, 700, 450, pose='peeking', expression='deadpan',
                    seed=57)
    els.append(card(11, 12, c_nothing, kind='character'))
    els.append(cap(11, W // 2, 210, size=32))

    # ---- b12  a second fence behind the first, receding ----------------- #
    def c_secondfence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 59)
        # far fence, smaller and higher up the frame (receding)
        _fence(d, 60, 520, W - 60, 150, 60, n_posts=8)
        # near fence, taller and lower (foreground)
        _fence(d, -60, 720, W + 60, 300, 61, n_posts=6)
    els.append(card(12, 13, c_secondfence))
    els.append(cap(12, W // 2, 200, size=30))

    # ---- b13  cameras on tall poles along the wire ----------------------- #
    def c_cameras(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 65)
        _fence(d, -60, 690, W + 60, 220, 66, n_posts=8)
        _camera_pole(d, 300, 600, 300, 67, lens_dir=1)
        _camera_pole(d, 980, 600, 300, 68, lens_dir=-1)
    els.append(card(13, 14, c_cameras))
    els.append(cap(13, W // 2, 240, size=30))

    # ---- b14  the base is smaller than its fence ------------------------- #
    def c_smallhuge(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 71)
        # The fence is a huge band across the upper-middle, running off both
        # edges. The first version drew it full-height so the wire mesh covered
        # the entire frame and the tiny base was lost behind it -- the very
        # comparison the line is making became unreadable. The fence now sits
        # BEHIND, as a band, and the base stands on clear alkali in front of it,
        # so both read at a glance.
        _fence(d, -80, 470, W + 80, 260, 72, n_posts=10)
        # the base, small, on the clear ground below the fence line
        _bunker(d, 520, 610, 96, 54, 73)
        _bunker(d, 646, 610, 76, 44, 74)
        _tower(d, 610, 610, 130, 75)
        D.draw_label(tile, 'HUGE FENCE', center=(640, 250), color=RED, size=44,
                     outline=INK, outline_w=2)
        D.draw_label(tile, 'SMALL', center=(610, 660), color=INK, size=38)
    els.append(card(14, 15, c_smallhuge))
    # The caption was at (640, 640), which collided with the 'SMALL' label and
    # the fence base. The very bottom band is clear ground.
    els.append(cap(14, 640, 700, size=28, fill=RED))

    # ---- b15  no aircraft may fly overhead ------------------------------- #
    def c_nojet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 79)
        _jet(d, 640, 200, 200, 80)
        D.draw_label(tile, 'NO AIRCRAFT OVERHEAD', center=(640, 340), color=RED,
                     size=42, outline=INK, outline_w=2)
    els.append(card(15, 16, c_nojet))
    els.append(cap(15, W // 2, 640, size=32, fill=RED))

    # ---- b16  a red dashed ceiling line drawn across the sky ------------ #
    def c_redline(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 83)
        # the ceiling: a red dashed horizontal across the upper sky
        y = 210
        dash, gap, x = 60, 34, -40
        while x < W + 40:
            PA.hand_stroke(d, [(x, y), (x + dash, y)], RED, 9, seed=84 + x,
                           wavelength=70.0)
            x += dash + gap
        # the base, far below the line
        _bunker(d, 560, 600, 120, 60, 90)
        _tower(d, 760, 600, 140, 91)
    els.append(card(16, 17, c_redline))
    els.append(cap(16, W // 2, 620, size=30, fill=RED))

    # ---- b17  a plane pushed back from the red line, character points up - #
    def c_pushback(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 93)
        y = 210
        dash, gap, x = 60, 34, -40
        while x < W + 40:
            PA.hand_stroke(d, [(x, y), (x + dash, y)], RED, 9, seed=94 + x,
                           wavelength=70.0)
            x += dash + gap
        # the plane, pushed DOWN below the line
        _jet(d, 700, 380, 170, 99)
        D.draw_red_x(tile, [640, 340, 760, 420], color=RED, width=9)
        SC.fullbody(d, 260, 700, 440, pose='pointing', expression='shock',
                    seed=100)
    els.append(card(17, 18, c_pushback, kind='character'))
    # The caption was at (300, 240), which put it straight through the red
    # dashed line at y=210 and clipped the left frame edge. It belongs in the
    # clear alkali ground at the bottom-right, clear of both the character and
    # the crossed-out jet.
    els.append(cap(17, 820, 660, size=30, fill=RED))

    # ---- b18  night: cockpit silhouette with a light blinking below ------ #
    def c_cockpit(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], NIGHT, seed=101, value=0.12)
        PA.fill_rect(tile, [0, HZ - 6, W, H], NIGHT_G, seed=102, value=0.12)
        PA.paper_overlay(tile, seed=103)
        # the light on the ground below, with a halo
        lx, ly = 700, 520
        for rr, col in ((90, (70, 40, 40)), (54, (140, 60, 50)), (24, RED)):
            d.ellipse([lx - rr, ly - rr * 0.6, lx + rr, ly + rr * 0.6], fill=col)
        # the dark cockpit frame across the bottom/edges (we are inside)
        PA.fill_poly(tile, [(0, 0), (W, 0), (W, 130), (0, 150)],
                     (18, 18, 22), seed=104, value=0.05)
        # lit course on the canopy head so the hardcoded-INK title reads on this
        # night card (see scene_common.title_backdrop). It goes ON TOP of the
        # frame fill -- that fill is a near-black canopy wedge across the whole
        # band, so a backdrop drawn under it is completely hidden and the title
        # scores 1.14. The frame's sloping lower edge (86..150) and its outline
        # stroke still draw over it, so the cockpit silhouette is unchanged.
        SC.title_backdrop(tile, 118, col=(84, 92, 118))
        PA.hand_stroke(d, [(0, 150), (320, 190), (960, 190), (W, 150)], INK, 8,
                       seed=105, wavelength=140.0)
        # the pilot, a dark silhouette at the left
        SC.fullbody(d, 240, 700, 400, pose='armscrossed', expression='deadpan',
                    seed=106)
    els.append(card(18, 19, c_cockpit, kind='character'))
    els.append(cap(18, 700, 300, size=32, fill=RED))

    # ---- b19  a calendar, 1955 circled ---------------------------------- #
    def c_1955(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=107, value=0.05)
        PA.paper_overlay(tile, seed=108)
        _calendar(d, 640, 360, 320, 240, 109, year=1955, circle_year=True)
    els.append(card(19, 20, c_1955))
    els.append(cap(19, W // 2, 660, size=30))

    # ---- b20  two calendars, 1947 and 1955, a line between them --------- #
    def c_twoyears(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=111, value=0.05)
        PA.paper_overlay(tile, seed=112)
        _calendar(d, 360, 360, 220, 200, 113, year=1947, circle_year=True)
        _calendar(d, 920, 360, 220, 200, 114, year=1955, circle_year=True)
        # an arrow from the older to the newer
        PA.hand_stroke(d, [(600, 360), (680, 360)], INK, 6, seed=115,
                       wavelength=70.0)
        PA.hand_stroke(d, [(680, 360), (656, 344)], INK, 6, seed=116,
                       wavelength=40.0)
        PA.hand_stroke(d, [(680, 360), (656, 376)], INK, 6, seed=117,
                       wavelength=40.0)
    els.append(card(20, 21, c_twoyears))
    els.append(cap(20, W // 2, 660, size=30))

    # ---- b21  a balloon drifting low over the fence ---------------------- #
    def c_balloon(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 119)
        _fence(d, -60, 700, W + 60, 220, 120, n_posts=8)
        # a half-deflated balloon sagging low over the fence, scaled up and
        # CROPPED BY THE RIGHT EDGE so it owns the frame rather than floating
        # as a small prop in the middle of a wide empty sky.
        _balloon_low(tile, d, 1075, 300, 195, 121)
        # the faint old year, in the clear sky at the top-left
        D.draw_label(tile, '1947', center=(220, 205), color=(172, 164, 154),
                     size=70)
    els.append(card(21, 22, c_balloon))
    # The caption was at (640, 640), which landed ON the fence's lower rail and
    # posts and rendered as an unreadable smear over the mesh. It now sits in
    # the open sky on the LEFT, in the band the balloon no longer occupies.
    els.append(cap(21, 400, 400, size=30, max_w=620))

    # ---- b22  Hangar 18: the wall with the painted 18, character shrug --- #
    def c_hangar18(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 127)
        # a big hangar wall, head-on
        wall = [(80, 140), (1200, 140), (1200, 640), (80, 640)]
        PA.fill_poly(tile, wall, CONCRETE, seed=128, value=0.07)
        PA.hand_stroke(d, wall, INK, 7, closed=True, seed=129, wavelength=150.0)
        # corrugated ribs
        for i in range(9):
            x = 140 + i * 118
            PA.hand_stroke(d, [(x, 170), (x, 620)], (188, 182, 170), 5,
                           seed=130 + i, wavelength=110.0)
        # the painted number
        D.draw_number(tile, '18', center=(640, 300), color=INK, size=170)
        D.draw_label(tile, 'HANGAR', center=(640, 470), color=INK, size=54)
        SC.fullbody(d, 260, 640, 380, pose='shrug', expression='skeptic',
                    seed=140)
    els.append(card(22, 23, c_hangar18, kind='character'))
    els.append(cap(22, 300, 250, size=32, fill=RED))

    # ---- b23  the hangar door slid half open, dark inside ---------------- #
    def c_dooropen(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=141, value=0.05)
        PA.paper_overlay(tile, seed=142)
        # hangar facade
        wall = [(60, 120), (1220, 120), (1220, 660), (60, 660)]
        PA.fill_poly(tile, wall, CONCRETE, seed=143, value=0.07)
        PA.hand_stroke(d, wall, INK, 7, closed=True, seed=144, wavelength=150.0)
        # the door: two leaves, the left slid open revealing a black interior
        interior = [(430, 200), (790, 200), (790, 660), (430, 660)]
        PA.fill_poly(tile, interior, (40, 44, 56), seed=145, value=0.05)
        PA.hand_stroke(d, interior, INK, 6, closed=True, seed=146,
                       wavelength=120.0)
        # the slid-open leaf, covering the left part
        leaf = [(180, 200), (430, 200), (430, 660), (180, 660)]
        PA.fill_poly(tile, leaf, (198, 192, 180), seed=147, value=0.06)
        PA.hand_stroke(d, leaf, INK, 6, closed=True, seed=148, wavelength=120.0)
        # the 18 at the frame edge
        D.draw_number(tile, '18', center=(1100, 300), color=INK, size=140)
    els.append(card(23, 24, c_dooropen))
    els.append(cap(23, W // 2, 690, size=30))

    # ---- b24  the same hangar stamped DOES NOT EXIST --------------------- #
    def c_noexist(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 151)
        # an empty bay (the hangar as a plain box, no interior visible)
        _hangar(d, 300, 620, 680, 420, 152)
        # a red stamp across it
        D.draw_red_box(tile, [200, 220, 1080, 560], color=RED, width=9)
        D.draw_label(tile, 'DOES NOT EXIST', center=(640, 390), color=RED,
                     size=76, outline=INK, outline_w=2)
    els.append(card(24, 25, c_noexist))
    els.append(cap(24, W // 2, 660, size=32, fill=RED))

    # ---- b25  Nellis AFB: two airfield hangars a drive away -------------- #
    def c_nellis(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 157)
        _mountain_strip(d, HZ, 158)
        # the runway, receding from the bottom-left toward the two hangars.
        # A trapezoid on the ground plane, not a stroke -- see _runway.
        _runway(d, 470, 556, 780, H + 30, 22, 130, 159)
        _hangar(d, 520, 560, 320, 200, 160)
        _hangar(d, 880, 560, 300, 190, 161)
        D.draw_label(tile, 'NELLIS AFB', center=(860, 250), color=INK, size=48)
    els.append(card(25, 26, c_nellis))
    # The caption was at (640, 640), directly on the runway, and rendered as a
    # smear across the tarmac. The upper-left sky is the only clear band.
    els.append(cap(25, 320, 250, size=30, max_w=600))

    # ---- b26  a budget sheet with one line blacked out ------------------ #
    def c_budget(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=162, value=0.05)
        PA.paper_overlay(tile, seed=163)
        sheet = [(240, 80), (1040, 80), (1040, 660), (240, 660)]
        PA.fill_poly(tile, sheet, PAPER, seed=164, value=0.05)
        PA.hand_stroke(d, sheet, INK, 6, closed=True, seed=165, wavelength=140.0)
        D.draw_label(tile, 'BUDGET', center=(640, 140), color=INK, size=48)
        # a column of line items
        for i in range(7):
            y = 200 + i * 58
            PA.hand_stroke(d, [(300, y), (560 - (i % 3) * 40, y)], (150, 146, 138),
                           4, seed=166 + i, wavelength=70.0)
        # one line, heavily blacked out
        by = 200 + 4 * 58
        PA.fill_rect(tile, [300, by - 14, 980, by + 14], INK, seed=173,
                     value=0.04)
        D.draw_label(tile, 'NOT PUBLIC', center=(640, 600), color=RED, size=40,
                     outline=INK, outline_w=2)
    els.append(card(26, 27, c_budget))
    els.append(cap(26, W // 2, 700, size=30, fill=RED))

    # ---- b27  1989: a television in a living room, character watches ----- #
    def c_tv(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 200, 190), seed=175, value=0.05)
        PA.fill_rect(tile, [0, HZ - 6, W, H], (188, 180, 170), seed=176,
                     value=0.07)
        PA.paper_overlay(tile, seed=177)
        # the TV set, shifted right and down so a clear wall band is left above it
        tv = [(500, 250), (1060, 250), (1060, 610), (500, 610)]
        PA.fill_poly(tile, tv, (92, 96, 104), seed=178, value=0.07)
        PA.hand_stroke(d, tv, INK, 6, closed=True, seed=179, wavelength=130.0)
        # the screen
        scr = [(530, 280), (1030, 280), (1030, 540), (530, 540)]
        PA.fill_poly(tile, scr, (170, 186, 196), seed=180, value=0.08)
        PA.hand_stroke(d, scr, INK, 5, closed=True, seed=181, wavelength=110.0)
        # a man's face on the screen (simple)
        SC.closeup(d, 780, 400, 86, 'deadpan', 182, shoulder=0.0)
        # dials + the year
        d.ellipse([1010, 500, 1040, 530], outline=INK, width=5)
        D.draw_label(tile, '1989', center=(780, 665), color=RED, size=44,
                     outline=INK, outline_w=2)
        # the character, leaned in, watching
        SC.fullbody(d, 230, 660, 430, pose='sitting', expression='awed',
                    seed=183)
    els.append(card(27, 28, c_tv, kind='character'))
    # The caption was at (950, 260), which ran across the TV's top bezel and
    # clipped the right frame edge. The clear wall band above the set is now
    # free, and the caption sits there.
    els.append(cap(27, 420, 210, size=30, fill=RED, max_w=760))

    # ---- b28  a man at a microphone, crowd silhouettes behind ----------- #
    def c_mic(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 200, 190), seed=184, value=0.05)
        PA.fill_rect(tile, [0, 420, W, H], (188, 180, 170), seed=185, value=0.07)
        PA.paper_overlay(tile, seed=186)
        # crowd silhouettes along the bottom
        for i in range(9):
            cx = 60 + i * 150
            d.ellipse([cx - 42, 470, cx + 42, 554], fill=(96, 96, 102))
            PA.fill_rect(tile, [cx - 52, 546, cx + 52, 660], (96, 96, 102),
                         seed=187 + i, value=0.04)
        # the speaker, standing on the floor BEHIND a lectern
        SC.fullbody(d, 640, 640, 400, pose='standing', expression='deadpan',
                    seed=197)
        # the lectern, in FRONT of him (was: a slab he stood on top of, which
        # made him float). Chest-high, tapered, with a top edge he leans over.
        lect = [(548, 660), (566, 452), (714, 452), (732, 660)]
        PA.fill_poly(tile, lect, (128, 120, 110), seed=196, value=0.06)
        PA.hand_stroke(d, lect, INK, 6, closed=True, seed=198, wavelength=110.0)
        PA.hand_stroke(d, [(560, 452), (720, 452)], INK, 7, seed=199,
                       wavelength=110.0)
        # the microphone on a short stand, rising to his mouth
        PA.hand_stroke(d, [(646, 452), (646, 372)], STEEL, 8, seed=201,
                       wavelength=60.0)
        d.ellipse([628, 342, 664, 378], fill=INK)
    els.append(card(28, 29, c_mic, kind='character'))
    els.append(cap(28, 300, 250, size=30))

    # ---- b29  his hands sketch a disc with a dome on top ---------------- #
    def c_discsketch(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=199, value=0.05)
        PA.paper_overlay(tile, seed=200)
        # a big disc, cropped, with a dome on top -- the shape he described
        cx, cy = 640, 420
        disc = PA.ellipse_pts(cx, cy, 340, 120, n=72)
        PA.fill_poly(tile, disc, (146, 152, 162), seed=201, value=0.07)
        PA.hand_stroke(d, disc, INK, 7, closed=True, seed=202, wavelength=150.0)
        # The dome is a clean filled half-ellipse. The first version appended two
        # diameter points to the arc and let fill_poly's default edge=4.6 wobble
        # the closing run, which rendered as a lumpy white slab with a hard
        # bottom -- not a dome. edge=1.2 keeps the silhouette a clean half-oval,
        # and a paler fill separates it from the disc beneath.
        dome = []
        n = 40
        for i in range(n + 1):
            a = math.pi + math.pi * i / n          # 180..360 deg = over the top
            dome.append((cx + 150 * math.cos(a), cy - 40 + 108 * math.sin(a)))
        dome_poly = dome + [(cx + 150, cy - 40), (cx - 150, cy - 40)]
        PA.fill_poly(tile, dome_poly, (226, 228, 230), seed=203, value=0.04,
                     edge=1.2)
        PA.hand_stroke(d, dome, INK, 6, closed=False, seed=204, wavelength=120.0)
        # the dome's diameter line, sitting on the disc
        PA.hand_stroke(d, [(cx - 150, cy - 40), (cx + 150, cy - 40)], (108, 114,
                       120), 5, seed=205, wavelength=100.0)
        # a pair of sketching hands framing the shape from both sides
        _hand_sketch(d, 210, 470, 206, flip=1)
        _hand_sketch(d, 1070, 470, 210, flip=-1)
        # sketch construction line through the disc
        PA.hand_stroke(d, [(cx - 340, cy), (cx + 340, cy)], (188, 190, 194), 3,
                       seed=214, wavelength=120.0)
    els.append(card(29, 30, c_discsketch))
    els.append(cap(29, W // 2, 680, size=30))

    # ---- b30  a file drawer, one folder missing, empty slot ------------- #
    def c_missingfile(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (214, 208, 196), seed=208, value=0.05)
        PA.paper_overlay(tile, seed=209)
        # an open drawer
        dr = [(280, 260), (1000, 260), (1000, 620), (280, 620)]
        PA.fill_poly(tile, dr, (186, 176, 160), seed=210, value=0.07)
        PA.hand_stroke(d, dr, INK, 7, closed=True, seed=211, wavelength=140.0)
        # folder slots inside; one empty (darker)
        for i in range(4):
            x0 = 320 + i * 165
            slot = [(x0, 300), (x0 + 140, 300), (x0 + 140, 580), (x0, 580)]
            empty = (i == 2)
            col = (52, 54, 62) if empty else (226, 206, 158)
            PA.fill_poly(tile, slot, col, seed=212 + i, value=0.06)
            PA.hand_stroke(d, slot, INK, 4, closed=True, seed=216 + i,
                           wavelength=90.0)
        # a small red arrow pointing at the empty slot
        PA.hand_stroke(d, [(820, 620), (820, 660)], RED, 5, seed=220,
                       wavelength=60.0)
        D.draw_label(tile, 'NO RECORD', center=(1010, 470), color=RED, size=34,
                     outline=INK, outline_w=2)
        SC.fullbody(d, 180, 640, 380, pose='armscrossed', expression='deadpan',
                    seed=221)
    els.append(card(30, 31, c_missingfile, kind='character'))
    els.append(cap(30, 640, 700, size=30, fill=RED))

    # ---- b31  declassified pages stamped RELEASED 2020 ------------------ #
    def c_fbi(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (214, 208, 196), seed=222, value=0.05)
        PA.paper_overlay(tile, seed=223)
        _file_stack(d, 640, 460, 300, 224, n=6, stamp='RELEASED 2020')
    els.append(card(31, 32, c_fbi))
    els.append(cap(31, W // 2, 660, size=30, fill=RED))

    # ---- b32  close on one page: GROOM LAKE, a finger under it ----------- #
    def c_pageclose(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=225, value=0.05)
        PA.paper_overlay(tile, seed=226)
        sheet = [(160, 118), (1120, 118), (1120, 660), (160, 660)]
        PA.fill_poly(tile, sheet, PAPER, seed=227, value=0.05)
        PA.hand_stroke(d, sheet, INK, 6, closed=True, seed=228, wavelength=150.0)
        # typed lines of text
        for i in range(8):
            y = 148 + i * 44
            if i == 4:
                continue
            PA.hand_stroke(d, [(220, y), (220 + (700 if i % 2 else 520), y)],
                           (150, 146, 138), 4, seed=229 + i, wavelength=70.0)
        # the revealed line: GROOM LAKE
        y = 148 + 4 * 44
        D.draw_label(tile, 'GROOM LAKE', center=(520, y), color=INK, size=44)
        # a finger pointing up under the words
        PA.fill_poly(tile, [(600, 620), (640, 480), (690, 620)], (222, 180, 150),
                     seed=240, value=0.05)
        PA.hand_stroke(d, [(600, 620), (640, 480), (690, 620)], INK, 5,
                       closed=False, seed=241, wavelength=70.0)
    els.append(card(32, 33, c_pageclose))
    els.append(cap(32, 300, 620, size=30, fill=RED))

    # ---- b33  the fence again, same framing as the opening --------------- #
    def c_stillstanding(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _playa(tile, 243)
        _mountain_strip(d, HZ, 244)
        _fence(d, -40, 640, W + 40, 260, 245, n_posts=9)
    els.append(card(33, 34, c_stillstanding))
    els.append(cap(33, W // 2, 240, size=32))

    # ---- b34  night, the fence almost black, one red light, character --- #
    def c_never(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], NIGHT, seed=247, value=0.12)
        PA.fill_rect(tile, [0, HZ - 6, W, H], NIGHT_G, seed=248, value=0.12)
        PA.paper_overlay(tile, seed=249)
        # lit course on the title band so the hardcoded-INK title reads on this
        # night card (see scene_common.title_backdrop).
        SC.title_backdrop(tile, 134, col=(84, 92, 118))
        _fence(d, -40, 650, W + 40, 280, 250, n_posts=9,
               post_col=(40, 42, 54), rail_col=(40, 42, 54))
        # one red light blinking on the fence
        lx, ly = 700, 400
        for rr, col in ((80, (66, 34, 36)), (46, (140, 56, 48)), (20, RED)):
            d.ellipse([lx - rr, ly - rr, lx + rr, ly + rr], fill=col)
        SC.fullbody(d, 260, 700, 440, pose='standing', expression='awed',
                    seed=251)
        D.draw_bubble(tile, 'never', (900, 260), tail_to=(520, 360))
    els.append(card(34, 35, c_never, kind='character'))
    els.append(cap(34, 900, 620, size=30, fill=RED))

    return SC.finish(els, TITLE, clock, title_seed=23)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))