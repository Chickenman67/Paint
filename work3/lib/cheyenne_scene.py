"""cheyenne scene -- the NORAD command bunker inside a mountain near Colorado
Springs. Chapter 2 of the bunker film.

Everything structural comes from scene_common (caption handoff, cropped
close-up, phrase clock, render drivers); this file declares only Cheyenne
Mountain's 38 cards.

ONE CARD PER BEAT, AND EACH CARD PAINTS ITS OWN WHOLE FRAME. The narration is
38 short sentences (see _plan_cheyenne.py) and beats.json gives each one an
exact [start,end], so there is no reason to guess at card boundaries. Every
card function fills the tile background-to-subject, which makes it structurally
impossible for one card's art to survive into the next.

THE HERO IS THE CROSS-SECTION (b09, b26). A side-cut of the massif with the
stacked floors of the complex drawn INSIDE the rock is the single image this
chapter exists to deliver, so it is drawn at full frame width with the
massif cropped by the left and right edges and the deepest floors running off
the bottom -- never parked in the middle of an empty page.

FRAME-FILL. Every exterior card puts the massif past the frame edges; every
interior card puts the room past the frame edges. The recurring defect in this
project's history is a subject parked small in the middle of an empty field.

CADENCE. Still-dominant, one cut per sentence (38 cuts in ~90s). Motion is
reserved for b29 (the warning clock -- the one beat where the narrator
explicitly says something starts) and b27 (the satellite beams crossing).

Run:  python lib/cheyenne_scene.py --preview
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
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'cheyenne'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Cheyenne Mountain'

# The sealed-complex cards are near-black, and engine3 stamps the title in
# hardcoded INK on every frame, so the title vanishes into them. Those cards
# carry a lit stone course at the head for it to read against (see
# scene_common.title_backdrop); band_intrusions exempts exactly those rows.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# ONE accent family. Grey granite massif, steel plant, snow white, and a single
# deep red that is spent only on the things the narration calls dangerous or
# forbidden: the seal, the shock arrow, the severed cable, the 90% claim.
INK = SC.INK
RED = (176, 32, 38)           # the one deep accent
ROCK = (146, 146, 152)        # lit granite
ROCK_SH = (104, 106, 116)     # shadowed granite
ROCK_PK = (162, 146, 146)     # mottled pink granite (b07 core sample)
SNOW = (238, 240, 244)
STEEL = (146, 154, 166)
STEEL_D = (96, 104, 118)
CONCRETE = (206, 204, 196)
CONCRETE_D = (162, 160, 152)
DEEP = (48, 50, 60)           # the dark interior / sealed door
DEEPER = (28, 29, 36)
SKY = (198, 208, 220)         # washed-out high-altitude sky
LAMP = (240, 206, 150)        # the one warm note, the Cold War lamp glow
GREEN = (86, 176, 120)        # radar phosphor, the only other colour

HZ = int(H * 0.66)            # horizon / ground line for exterior cards


# ---------------------------------------------------------------------------
# backgrounds
# ---------------------------------------------------------------------------

def _sky(tile, seed, sky=SKY, ground=None, hz=HZ):
    """Full-frame exterior ground. Call at the TOP of every exterior card.

    WHY TWO OVERLAPPING FILLS AND NOT TWO ABUTTING RECTS: fill_rect wobbles
    each of its own edges on its own seed, so two abutting rects leave a pale
    seam where their wobbles disagree. Painting the sky over the WHOLE frame
    and then laying the ground on top (starting above the nominal horizon)
    makes the horizon the single wobbled edge it should be.
    """
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    if ground is not None:
        PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


def _rock_bg(tile, seed, rock=ROCK, deep=DEEP, split=None):
    """A full-frame ROCK interior: solid stone, no sky.

    `split` is the y where the deep dark begins (the floor line / ceiling line);
    None paints the whole frame as rock.
    """
    PA.fill_rect(tile, [0, 0, W, H], rock, seed=seed, value=0.09)
    if split is not None:
        PA.fill_rect(tile, [0, split, W, H], deep, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


# ---------------------------------------------------------------------------
# the massif
# ---------------------------------------------------------------------------

def _massif(d, cx, base_y, half_w, peak_y, seed, snow=True, rock=ROCK,
            shade=ROCK_SH):
    """A grey granite peak whose FLANKS RUN PAST THE FRAME EDGES.

    Frame-fill is the point: `half_w` is normally larger than the distance to
    the nearest edge, so the mountain is cropped left and right and the frame
    admits the range continues past the picture.

    The silhouette is a hand-built point list (a summit, two shoulders, two
    feet), smoothed and wobbled by fill_poly, and then split into a lit left
    face and a shadowed right face along a ridge line running from the summit
    to the right foot -- that split is what makes it read as a solid mass
    rather than a flat triangle.
    """
    pts = [(cx - half_w, base_y),
           (cx - half_w * 0.72, base_y - (base_y - peak_y) * 0.30),
           (cx - half_w * 0.40, base_y - (base_y - peak_y) * 0.68),
           (cx - half_w * 0.15, peak_y + (base_y - peak_y) * 0.10),
           (cx, peak_y),
           (cx + half_w * 0.16, peak_y + (base_y - peak_y) * 0.07),
           (cx + half_w * 0.44, base_y - (base_y - peak_y) * 0.64),
           (cx + half_w * 0.78, base_y - (base_y - peak_y) * 0.26),
           (cx + half_w, base_y)]
    PA.fill_poly(PA.img_of(d), pts, rock, seed=seed, value=0.08)
    PA.hand_stroke(d, pts, INK, 7, closed=False, seed=seed + 1,
                   wavelength=180.0)

    # the shadow face: summit -> right shoulder -> right foot
    shadow = [(cx, peak_y),
              (cx + half_w * 0.16, peak_y + (base_y - peak_y) * 0.07),
              (cx + half_w * 0.44, base_y - (base_y - peak_y) * 0.64),
              (cx + half_w * 0.78, base_y - (base_y - peak_y) * 0.26),
              (cx + half_w, base_y), (cx + half_w * 0.18, base_y),
              (cx + half_w * 0.40, base_y - (base_y - peak_y) * 0.40),
              (cx + half_w * 0.10, base_y - (base_y - peak_y) * 0.55),
              (cx, peak_y + (base_y - peak_y) * 0.06)]
    PA.fill_poly(PA.img_of(d), shadow, shade, seed=seed + 2, value=0.07)
    # a ridge line so the two faces have an edge between them
    PA.hand_stroke(d, [(cx, peak_y),
                       (cx + half_w * 0.10, base_y - (base_y - peak_y) * 0.55),
                       (cx + half_w * 0.40, base_y - (base_y - peak_y) * 0.40),
                       (cx + half_w * 0.18, base_y)],
                   INK, 4, closed=False, seed=seed + 3, wavelength=140.0)

    if snow:
        cap = [(cx - half_w * 0.16, peak_y + (base_y - peak_y) * 0.11),
               (cx, peak_y),
               (cx + half_w * 0.17, peak_y + (base_y - peak_y) * 0.08),
               (cx + half_w * 0.09, peak_y + (base_y - peak_y) * 0.18),
               (cx - half_w * 0.02, peak_y + (base_y - peak_y) * 0.13),
               (cx - half_w * 0.11, peak_y + (base_y - peak_y) * 0.20)]
        PA.fill_poly(PA.img_of(d), cap, SNOW, seed=seed + 4, value=0.04)
        PA.hand_stroke(d, cap, INK, 4, closed=True, seed=seed + 5,
                       wavelength=90.0)
    return pts


def _scratch(d, x0, y0, x1, y1, seed, colour=(104, 104, 112)):
    """A faint construction scratch on the rock face (b02)."""
    PA.hand_stroke(d, [(x0, y0), (x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.55),
                       (x1, y1)], colour, 5, closed=False, seed=seed,
                   wavelength=150.0, vary=0.18)


# ---------------------------------------------------------------------------
# the portal: a camouflaged tunnel mouth with blast doors
# ---------------------------------------------------------------------------

def _portal(d, cx, cy, w, h, seed, open_frac=1.0, doors=0):
    """A concrete tunnel mouth cut into the flank, with `doors` blast doors.

    The mouth is a rounded arch (half a disc over a rectangle), which is what
    makes a hole in a mountain read as a tunnel rather than a doorway: a plain
    rectangle in rock reads as a window. `open_frac` shortens the interior
    depth, so at open_frac=0.35 the door is a heavy slab well inside the arch.
    """
    img = PA.img_of(d)
    arch = PA.arc_pts(cx, cy, w / 2.0, w / 2.0, 180, 360, n=28)
    body = [(cx - w / 2.0, cy)] + arch + [(cx + w / 2.0, cy + h)]
    inner = [(cx - w / 2.0, cy)] + list(reversed(arch)) + [(cx + w / 2.0, cy + h)]
    # cut the rock away with a DARK mouth, not a hole: the tunnel interior is
    # nearly black, which is what sells "cut into the mountain".
    PA.fill_poly(img, inner, DEEPER, seed=seed, value=0.05)
    PA.hand_stroke(d, body, INK, 7, closed=True, seed=seed + 1, wavelength=130.0)
    # the concrete collar around the mouth
    for i, k in enumerate((1.16, 1.28)):
        ring = ([(cx - w * k / 2.0, cy + h * (0.04 if i else -0.02))]
                + PA.arc_pts(cx, cy, w * k / 2.0, w * k / 2.0, 180, 360, n=28)
                + [(cx + w * k / 2.0, cy + h * 1.02)])
        PA.hand_stroke(d, ring, INK, 5 if i else 6, closed=True,
                       seed=seed + 10 + i, wavelength=140.0)

    if doors:
        # THE FIFTEEN BLAST DOORS (b08). Repeated heavy chevron slabs marching
        # INTO the mountain down the access tunnel. Drawn as receding
        # trapezoids -- each narrower than the last and each darker -- because a
        # row of identical rectangles reads as a bar chart, while a receding row
        # reads as depth. The chevron notch on each face is what says "blast
        # door" and not "drawer".
        for i in range(doors):
            t = i / float(max(1, doors - 1))
            dd = h * (0.86 - 0.50 * t)
            dw = w * (0.40 - 0.22 * t)
            dx = cx - dw / 2.0
            dy = cy + h * 0.10 + (h * 0.34) * t
            face = [(dx, dy), (dx + dw, dy), (dx + dw, dy + dd), (dx, dy + dd)]
            col = (STEEL_D if i % 2 == 0 else (110, 118, 130))
            PA.fill_poly(img, face, col, seed=seed + 20 + i, value=0.07)
            PA.hand_stroke(d, face, INK, 4, closed=True, seed=seed + 40 + i,
                           wavelength=70.0)
            # the chevron
            cyv = dy + dd * 0.5
            ch = dw * 0.34
            PA.hand_stroke(d, [(dx + dw * 0.14, cyv + ch),
                               (dx + dw * 0.5, cyv - ch * 0.35),
                               (dx + dw * 0.86, cyv + ch)],
                           RED if i == doors - 1 else INK, 5,
                           closed=False, seed=seed + 80 + i, wavelength=60.0)

    if open_frac < 0.9:
        # the slab door itself, sitting at `open_frac` of the way in
        dw = w * 0.40
        dd = h * 0.86
        dy = cy + h * 0.10
        PA.fill_rect(img, [cx - dw / 2.0, dy, cx + dw / 2.0, dy + dd],
                     STEEL_D, seed=seed + 100, value=0.08)
        PA.hand_stroke(d, [(cx - dw / 2.0, dy), (cx + dw / 2.0, dy),
                           (cx + dw / 2.0, dy + dd), (cx - dw / 2.0, dy + dd)],
                       INK, 6, closed=True, seed=seed + 101, wavelength=110.0)
        # hinge ribs + the red seal gasket that closes against the frame
        for k in range(4):
            yy = dy + dd * (0.16 + k * 0.22)
            PA.hand_stroke(d, [(cx - dw * 0.42, yy), (cx + dw * 0.42, yy)],
                           STEEL, 4, seed=seed + 110 + k, wavelength=60.0)
        PA.hand_stroke(d, [(cx - dw * 0.50, dy), (cx - dw * 0.50, dy + dd)],
                       RED, 6, closed=False, seed=seed + 120, wavelength=120.0)
        PA.hand_stroke(d, [(cx + dw * 0.50, dy), (cx + dw * 0.50, dy + dd)],
                       RED, 6, closed=False, seed=seed + 121, wavelength=120.0)


def _blast_door(d, cx, cy, w, h, seed, closed=True):
    """One blast door in cross-section, slab and frame, cropped by the frame.

    `closed` presses the slab against the frame's seal faces (the red gasket
    lines meet). `not closed` swings it on its hinge, so the dark gap it left
    is visible -- which is the ONLY thing that reads as "sealing".
    """
    img = PA.img_of(d)
    frame = [(cx - w * 0.62, cy - h * 0.56), (cx + w * 0.62, cy - h * 0.56),
             (cx + w * 0.62, cy + h * 0.56), (cx - w * 0.62, cy + h * 0.56)]
    PA.fill_poly(img, frame, CONCRETE_D, seed=seed, value=0.08)
    PA.hand_stroke(d, frame, INK, 8, closed=True, seed=seed + 1, wavelength=150.0)
    # the dark tunnel beyond the door -- the void the door is sealing
    void = [(cx - w * 0.46, cy - h * 0.40), (cx + w * 0.46, cy - h * 0.40),
            (cx + w * 0.46, cy + h * 0.40), (cx - w * 0.46, cy + h * 0.40)]
    PA.fill_poly(img, void, DEEPER, seed=seed + 2, value=0.05)

    if closed:
        slab = [(cx - w * 0.44, cy - h * 0.40), (cx + w * 0.44, cy - h * 0.40),
                (cx + w * 0.44, cy + h * 0.40), (cx - w * 0.44, cy + h * 0.40)]
        PA.fill_poly(img, slab, STEEL_D, seed=seed + 3, value=0.08)
        PA.hand_stroke(d, slab, INK, 7, closed=True, seed=seed + 4,
                       wavelength=140.0)
        # hinge ribs
        for k in range(5):
            yy = cy - h * 0.32 + k * h * 0.16
            PA.hand_stroke(d, [(cx - w * 0.38, yy), (cx + w * 0.38, yy)],
                           STEEL, 5, seed=seed + 10 + k, wavelength=60.0)
        # THE SEAL. Two red gasket faces pressed together down the middle: the
        # whole point of the door is the seal, so it gets the chapter's one
        # accent colour and a heavy weight.
        PA.hand_stroke(d, [(cx - w * 0.46, cy - h * 0.42), (cx - w * 0.46, cy + h * 0.42)],
                       RED, 7, closed=False, seed=seed + 20, wavelength=120.0)
        PA.hand_stroke(d, [(cx + w * 0.46, cy - h * 0.42), (cx + w * 0.46, cy + h * 0.42)],
                       RED, 7, closed=False, seed=seed + 21, wavelength=120.0)
        PA.hand_stroke(d, [(cx - w * 0.46, cy), (cx + w * 0.46, cy)], RED, 7,
                       closed=False, seed=seed + 22, wavelength=120.0)
    else:
        # swung open on its left hinge: a parallelogram leaning away, with the
        # seal face on its leading edge and the dark gap behind it
        slab = [(cx - w * 0.44, cy - h * 0.40), (cx - w * 0.10, cy - h * 0.52),
                (cx - w * 0.10, cy + h * 0.28), (cx - w * 0.44, cy + h * 0.40)]
        PA.fill_poly(img, slab, STEEL_D, seed=seed + 3, value=0.08)
        PA.hand_stroke(d, slab, INK, 7, closed=True, seed=seed + 4,
                       wavelength=120.0)
        PA.hand_stroke(d, [(cx - w * 0.10, cy - h * 0.52), (cx - w * 0.10, cy + h * 0.28)],
                       RED, 7, closed=False, seed=seed + 20, wavelength=100.0)
        # the arrows that shove it shut
        for k, dy in enumerate((-0.16, 0.0, 0.16)):
            D.draw_arrow(img, (cx + w * 0.56, cy + h * dy),
                         (cx + w * 0.16, cy + h * dy), color=RED, width=7,
                         head=34)


# ---------------------------------------------------------------------------
# the hero: the cross-section of the complex
# ---------------------------------------------------------------------------

def _cross_section(d, cx, base_y, half_w, peak_y, seed, floors=6, tunnels=4,
                   numbers=False, chambers=True, rock=ROCK, shade=ROCK_SH):
    """THE HERO IMAGE: the massif cut open on its LEFT flank, the complex
    stacked inside the rock, cropped by the frame edges.

    HOW THE CUT READS. The mountain's silhouette is filled; then a bite is
    taken out of the LEFT flank by filling a tall wedge in the SKY colour that
    runs off the left edge -- so the mountain is not "a diagram beside a
    mountain", it is a mountain with its side removed, which is what a
    cross-section IS. The exposed face of the cut is a flat paler rock value,
    and every chamber is a dark room opening onto that face, so the rooms read
    as INSIDE the rock instead of floating on it.

    Frame-fill: `half_w` is deliberately larger than the frame, and the
    deepest floors run past the bottom edge.
    """
    img = PA.img_of(d)
    _massif(d, cx, base_y, half_w, peak_y, seed, snow=False, rock=rock, shade=shade)

    # the cut face: a paler slab of exposed rock on the left flank
    cut_x = cx - half_w * 0.34
    face = [(cut_x - half_w * 0.70, base_y + 40), (cut_x, base_y + 40),
            (cut_x, peak_y + (base_y - peak_y) * 0.34),
            (cut_x - half_w * 0.34, peak_y + (base_y - peak_y) * 0.10),
            (cut_x - half_w * 0.70, peak_y + (base_y - peak_y) * 0.46)]
    PA.fill_poly(img, face, (178, 176, 178), seed=seed + 6, value=0.07)
    PA.hand_stroke(d, face, INK, 5, closed=True, seed=seed + 7, wavelength=130.0)

    # the chambers: stacked floors cut into the exposed face, deepest first so
    # a nearer floor overlaps the one behind it
    fh = (base_y - peak_y) * 0.085
    top = peak_y + (base_y - peak_y) * 0.40
    for i in range(floors if chambers else 0):
        t = i / float(max(1, floors - 1))
        y = top + i * fh * 1.62
        if y > base_y + fh * 0.5:
            break
        x0 = cut_x - half_w * 0.66 + t * half_w * 0.10
        x1 = cut_x + half_w * 0.02 - t * half_w * 0.14
        room = [(x0, y), (x1, y - fh * 0.16), (x1, y + fh * 0.62), (x0, y + fh * 0.80)]
        PA.fill_poly(img, room, DEEP, seed=seed + 20 + i, value=0.06)
        PA.hand_stroke(d, room, INK, 5, closed=True, seed=seed + 40 + i,
                       wavelength=90.0)
        # a lit strip inside: the reason the room is occupied
        PA.hand_stroke(d, [(x0 + 8, y + fh * 0.22), (x1 - 8, y + fh * 0.10)],
                       LAMP if i % 3 == 1 else STEEL, 4, closed=False,
                       seed=seed + 60 + i, wavelength=60.0)
        # the floor slab under it
        PA.hand_stroke(d, [(x0 - 6, y + fh * 0.86), (x1 + 6, y + fh * 0.68)],
                       CONCRETE_D, 7, closed=False, seed=seed + 80 + i,
                       wavelength=80.0)

    # the access tunnel running in from the left edge to the complex
    ty = base_y - (base_y - peak_y) * 0.16
    PA.hand_stroke(d, [(-30, ty - 34), (cut_x - half_w * 0.30, ty - 22),
                       (cut_x, ty - 6)], DEEPER, 62, closed=False,
                   seed=seed + 100, wavelength=120.0, vary=0.06)
    PA.hand_stroke(d, [(-30, ty - 34), (cut_x - half_w * 0.30, ty - 22),
                       (cut_x, ty - 6)], INK, 4, closed=False, seed=seed + 101,
                   wavelength=120.0)

    if numbers:
        for i in range(tunnels):
            yy = ty + 60 + i * 42
            PA.hand_stroke(d, [(cut_x - half_w * 0.20 - i * 26, yy),
                               (cut_x - half_w * 0.20 - i * 26, yy - 90)],
                           STEEL_D, 6, closed=False, seed=seed + 120 + i,
                           wavelength=70.0)
    return face


# ---------------------------------------------------------------------------
# interior furniture
# ---------------------------------------------------------------------------

def _console_bank(d, x0, x1, base_y, seed, rows=2, lamps=True, green=False):
    """A bank of operator consoles seen head-on: desks, screens, chair backs.

    The cue that says "operations room" is a REPEATING rhythm of small bright
    screens at eye height with dark chair backs in front of them -- the chairs
    are what say people sit here. Drawn large enough that the near row is
    cropped by the bottom edge.
    """
    img = PA.img_of(d)
    unit = (x1 - x0) / float(max(1, rows * 3))
    for r in range(rows):
        depth = 1.0 - r * 0.22
        dy = base_y - r * 96
        h = 168 * depth
        n = max(1, int((x1 - x0) / unit))
        for i in range(n):
            x = x0 + i * unit + unit * 0.5
            w = unit * 0.78
            desk = [(x - w / 2.0, dy), (x + w / 2.0, dy),
                    (x + w / 2.0, dy + h), (x - w / 2.0, dy + h)]
            PA.fill_poly(img, desk, (STEEL_D if r else CONCRETE_D),
                         seed=seed + r * 40 + i, value=0.07)
            PA.hand_stroke(d, desk, INK, 4, closed=True,
                           seed=seed + 200 + r * 40 + i, wavelength=70.0)
            # the screen: a bright rectangle set into the desk face
            sx0, sy0 = x - w * 0.36, dy + h * 0.16
            sx1, sy1 = x + w * 0.36, dy + h * 0.58
            PA.fill_rect(img, [sx0, sy0, sx1, sy1],
                         (40, 62, 58) if green else (52, 58, 70),
                         seed=seed + 300 + i, value=0.05)
            PA.hand_stroke(d, [(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)],
                           INK, 3, closed=True, seed=seed + 400 + i,
                           wavelength=60.0)
            # scan lines on the screen -- what says "display"
            for k in range(3):
                yy = sy0 + (sy1 - sy0) * (0.28 + k * 0.24)
                PA.hand_stroke(d, [(sx0 + 5, yy), (sx1 - 5, yy)],
                               GREEN if green else (108, 132, 150), 2,
                               closed=False, seed=seed + 500 + k * 7 + i,
                               wavelength=40.0)
            if lamps:
                col = GREEN if green else RED
                PA.fill_poly(img, PA.ellipse_pts(x + w * 0.30, dy + h * 0.80,
                                                  w * 0.09, w * 0.09, n=20),
                             col, seed=seed + 600 + i, value=0.05)


def _radar(d, cx, cy, r, seed, sweep=-35.0, arc=0, blips=3, warm=False):
    """A round radar scope: rings, cross hairs, a sweep wedge, and blips.

    The sweep is a FILLED PIE WEDGE in a translucent-looking phosphor value,
    not a line, because a scope's afterglow is what the eye reads as "live".
    `arc` adds a red threat arc climbing the rim (b29).
    """
    img = PA.img_of(d)
    disc = PA.ellipse_pts(cx, cy, r, r, n=72)
    PA.fill_poly(img, disc, (30, 44, 42) if not warm else (44, 40, 40),
                 seed=seed, value=0.06)
    PA.hand_stroke(d, disc, INK, 8, closed=True, seed=seed + 1, wavelength=170.0)
    for k, f in enumerate((0.34, 0.66)):
        ring = PA.ellipse_pts(cx, cy, r * f, r * f, n=48)
        PA.hand_stroke(d, ring, (70, 100, 92) if not warm else (100, 80, 80), 3,
                       closed=True, seed=seed + 10 + k, wavelength=110.0)
    PA.hand_stroke(d, [(cx - r, cy), (cx + r, cy)], (70, 100, 92), 3,
                   closed=False, seed=seed + 20, wavelength=110.0)
    PA.hand_stroke(d, [(cx, cy - r), (cx, cy + r)], (70, 100, 92), 3,
                   closed=False, seed=seed + 21, wavelength=110.0)

    a = math.radians(sweep)
    tip = (cx + r * 0.98 * math.cos(a), cy + r * 0.98 * math.sin(a))
    wedge = [(cx, cy), (cx + r * 0.30 * math.cos(a - 0.5),
                        cy + r * 0.30 * math.sin(a - 0.5)),
             tip, (cx + r * 0.30 * math.cos(a + 0.5),
                   cy + r * 0.30 * math.sin(a + 0.5))]
    PA.fill_poly(img, wedge, (48, 84, 72) if not warm else (78, 52, 46),
                 seed=seed + 30, value=0.06)
    PA.hand_stroke(d, [(cx, cy), tip], GREEN if not warm else RED, 5,
                   closed=False, seed=seed + 31, wavelength=120.0)

    for i in range(blips):
        ba = math.radians(sweep - 26.0 - i * 44.0)
        br = r * (0.34 + 0.20 * ((i * 7) % 3) / 2.0)
        bx, by = cx + br * math.cos(ba), cy + br * math.sin(ba)
        PA.fill_poly(img, PA.ellipse_pts(bx, by, r * 0.07, r * 0.07, n=20),
                     (198, 236, 210) if not warm else (238, 198, 190),
                     seed=seed + 40 + i, value=0.05)

    if arc:
        aa = math.radians(-arc * 0.5)
        ab = math.radians(arc * 0.5)
        rim = [(cx + r * 0.90 * math.cos(aa + (ab - aa) * k / 20.0),
                cy + r * 0.90 * math.sin(aa + (ab - aa) * k / 20.0))
               for k in range(21)]
        PA.hand_stroke(d, rim, RED, 9, closed=False, seed=seed + 50,
                       wavelength=90.0)
    # the bezel
    bez = PA.ellipse_pts(cx, cy, r * 1.14, r * 1.14, n=72)
    PA.hand_stroke(d, bez, STEEL_D, 7, closed=True, seed=seed + 60,
                   wavelength=170.0)


def _spring(d, cx, top_y, w, h, seed, squash=1.0, col=STEEL):
    """A coiled steel spring, drawn as a real coil.

    THE COIL IS A HELIX, NOT A ZIGZAG. A zigzag reads as a resistor symbol on a
    circuit diagram, which is the wrong register entirely. The helix is
    sampled as a sine in x against depth in y, offset per coil, which reads as
    wound steel immediately. `squash` < 1 flattens it (b11).
    """
    coils = 5
    pts = []
    n = coils * 26
    for i in range(n + 1):
        t = i / float(n)
        a = t * coils * 2.0 * math.pi
        x = cx + (w / 2.0) * math.sin(a) * 0.92
        y = top_y + h * squash * t
        pts.append((x, y))
    PA.hand_stroke(d, pts, INK, 9, closed=False, seed=seed, wavelength=70.0)
    PA.hand_stroke(d, pts, col, 5, closed=False, seed=seed + 1, wavelength=70.0)
    return pts


def _water_tank(d, x0, y0, x1, y1, seed, level=0.7):
    """A cylindrical water tank: a flat-topped cylinder with a level band."""
    img = PA.img_of(d)
    body = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    PA.fill_poly(img, body, STEEL, seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1, wavelength=110.0)
    # domed top
    top = PA.arc_pts((x0 + x1) / 2.0, y0, (x1 - x0) / 2.0, (y1 - y0) * 0.16,
                     180, 360, n=24)
    PA.fill_poly(img, [(x0, y0)] + top + [(x1, y0)], (172, 180, 190),
                 seed=seed + 2, value=0.06)
    PA.hand_stroke(d, [(x0, y0)] + top + [(x1, y0)], INK, 5, closed=True,
                   seed=seed + 3, wavelength=110.0)
    ly = y1 - (y1 - y0) * level
    PA.hand_stroke(d, [(x0 + 5, ly), (x1 - 5, ly)], (110, 150, 172), 7,
                   closed=False, seed=seed + 4, wavelength=90.0)
    # banding hoops
    for k in range(2):
        yy = y0 + (y1 - y0) * (0.34 + k * 0.30)
        PA.hand_stroke(d, [(x0 + 3, yy), (x1 - 3, yy)], STEEL_D, 4,
                       closed=False, seed=seed + 10 + k, wavelength=80.0)


def _drum(d, cx, base_y, w, h, seed):
    """A fuel drum: cylinder with two rolled hoops."""
    body = [(cx - w / 2.0, base_y - h), (cx + w / 2.0, base_y - h),
            (cx + w / 2.0, base_y), (cx - w / 2.0, base_y)]
    PA.fill_poly(PA.img_of(d), body, (168, 84, 62), seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1, wavelength=70.0)
    for k in (0.32, 0.68):
        yy = base_y - h * k
        PA.hand_stroke(d, [(cx - w / 2.0 + 3, yy), (cx + w / 2.0 - 3, yy)],
                       (118, 56, 40), 5, closed=False, seed=seed + 2 + int(k * 10),
                       wavelength=50.0)


def _generator(d, cx, base_y, w, h, seed):
    """A diesel generator set: engine block, exhaust stack, alternator drum."""
    img = PA.img_of(d)
    block = [(cx - w * 0.50, base_y - h * 0.78), (cx + w * 0.22, base_y - h * 0.78),
             (cx + w * 0.22, base_y), (cx - w * 0.50, base_y)]
    PA.fill_poly(img, block, STEEL_D, seed=seed, value=0.08)
    PA.hand_stroke(d, block, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    alt = PA.ellipse_pts(cx + w * 0.34, base_y - h * 0.40, w * 0.20, h * 0.40, n=40)
    PA.fill_poly(img, alt, STEEL, seed=seed + 2, value=0.08)
    PA.hand_stroke(d, alt, INK, 6, closed=True, seed=seed + 3, wavelength=90.0)
    # exhaust stack
    PA.hand_stroke(d, [(cx - w * 0.30, base_y - h * 0.78),
                       (cx - w * 0.30, base_y - h * 1.42)], INK, 12,
                   closed=False, seed=seed + 4, wavelength=80.0)
    PA.hand_stroke(d, [(cx - w * 0.30, base_y - h * 1.42),
                       (cx - w * 0.30, base_y - h * 1.56)], STEEL, 16,
                   closed=False, seed=seed + 5, wavelength=50.0)
    # radiator grille
    for k in range(4):
        yy = base_y - h * 0.66 + k * h * 0.15
        PA.hand_stroke(d, [(cx - w * 0.44, yy), (cx + w * 0.14, yy)], STEEL, 4,
                       closed=False, seed=seed + 10 + k, wavelength=60.0)


def _pylon(d, x, base_y, h, seed):
    """A lattice power pylon. The catenary between pylons is drawn by the
    caller, so a line can be made to STOP DEAD in mid-air (b22)."""
    half = h * 0.20
    for s in (-1, 1):
        PA.hand_stroke(d, [(x + s * half, base_y), (x + s * half * 0.34, base_y - h * 0.62),
                           (x + s * half * 0.22, base_y - h)],
                       STEEL_D, 7, closed=False, seed=seed + s, wavelength=90.0)
    for k in range(4):
        yy = base_y - h * (0.16 + k * 0.22)
        wv = half * (1.0 - 0.75 * (yy - base_y) / -h) if yy < base_y else half
        PA.hand_stroke(d, [(x - wv, yy), (x + wv, yy)], STEEL_D, 5,
                       closed=False, seed=seed + 10 + k, wavelength=60.0)
    for k in range(3):
        yy = base_y - h * (0.86 + k * 0.05)
        PA.hand_stroke(d, [(x - half * 0.5, yy), (x + half * 0.5, yy)], INK, 5,
                       closed=False, seed=seed + 20 + k, wavelength=50.0)
    return x


def _painted_tree(d, cx, base_y, h, seed, w=None, col=None, drips=True):
    """A CAMOUFLAGE TREE: the concrete slab the mountain wears.

    WHY IT IS A SLAB AND NOT A TREE. The narration's whole point is that these
    are painted concrete, not trees -- so the shape is a treelike CONE of
    flat grey with a hard-edged, slightly stepped silhouette and visible drip
    marks running DOWN off the branches. Real foliage would read as a tree and
    kill the beat. The drips are the tell.
    """
    img = PA.img_of(d)
    w = w or h * 0.62
    col = col or CONCRETE
    # a stepped conifer silhouette: three stacked trapezoids, hard edged
    tiers = []
    for k in range(3):
        t = k / 3.0
        y1 = base_y - h * (0.34 + 0.32 * k)
        y0 = base_y - h * (0.66 + 0.32 * k)
        ww = w * (1.0 - 0.26 * k)
        tiers += [(cx - ww / 2.0, y1), (cx + ww / 2.0, y1),
                  (cx + ww * 0.36, y0), (cx - ww * 0.36, y0)]
    trunk = [(cx - w * 0.09, base_y), (cx + w * 0.09, base_y),
             (cx + w * 0.09, base_y - h * 0.30), (cx - w * 0.09, base_y - h * 0.30)]
    PA.fill_poly(img, tiers + [(cx + w * 0.09, base_y), (cx - w * 0.09, base_y)],
                 col, seed=seed, value=0.09)
    PA.hand_stroke(d, tiers, INK, 5, closed=True, seed=seed + 1, wavelength=120.0)
    PA.hand_stroke(d, trunk, INK, 5, closed=True, seed=seed + 2, wavelength=90.0)
    if drips:
        for k in range(4):
            xx = cx + (k - 1.5) * w * 0.20
            yy = base_y - h * (0.40 + 0.16 * (k % 2))
            PA.hand_stroke(d, [(xx, yy), (xx + 3, yy + h * 0.22)], CONCRETE_D, 4,
                           closed=False, seed=seed + 10 + k, wavelength=40.0,
                           vary=0.10)


def _vent_tower(d, cx, base_y, h, seed, col=None):
    """A ventilation stack: a slim rectangular tower with a louvred cap."""
    img = PA.img_of(d)
    col = col or CONCRETE_D
    w = h * 0.26
    body = [(cx - w / 2.0, base_y), (cx + w / 2.0, base_y),
            (cx + w / 2.0, base_y - h), (cx - w / 2.0, base_y - h)]
    PA.fill_poly(img, body, col, seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1, wavelength=100.0)
    cap = [(cx - w * 0.74, base_y - h), (cx + w * 0.74, base_y - h),
           (cx + w * 0.60, base_y - h - h * 0.10),
           (cx - w * 0.60, base_y - h - h * 0.10)]
    PA.fill_poly(img, cap, STEEL, seed=seed + 2, value=0.07)
    PA.hand_stroke(d, cap, INK, 5, closed=True, seed=seed + 3, wavelength=80.0)
    for k in range(4):
        yy = base_y - h * (0.18 + k * 0.18)
        PA.hand_stroke(d, [(cx - w * 0.36, yy), (cx + w * 0.36, yy)], INK, 3,
                       closed=False, seed=seed + 10 + k, wavelength=50.0)


def _norad_badge(d, cx, cy, r, seed):
    """A shield stamp: the NORAD-style crest, our own drawing.

    A heraldic shield outline, a star-and-arrow motif inside it, and a banner
    across the bottom. This is our own generic military crest -- it is a STAMP
    that says "this is a command centre", not a reproduction of any badge.
    """
    img = PA.img_of(d)
    body = [(cx - r * 0.72, cy - r * 0.86), (cx + r * 0.72, cy - r * 0.86),
            (cx + r * 0.72, cy + r * 0.16), (cx, cy + r * 0.96),
            (cx - r * 0.72, cy + r * 0.16)]
    PA.fill_poly(img, body, (56, 78, 112), seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 7, closed=True, seed=seed + 1, wavelength=130.0)
    inner = [(cx - r * 0.54, cy - r * 0.66), (cx + r * 0.54, cy - r * 0.66),
             (cx + r * 0.54, cy + r * 0.10), (cx, cy + r * 0.72),
             (cx - r * 0.54, cy + r * 0.10)]
    PA.hand_stroke(d, inner, SNOW, 4, closed=True, seed=seed + 2, wavelength=110.0)
    # a five-point star
    star = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rad = r * (0.36 if k % 2 == 0 else 0.16)
        star.append((cx + rad * math.cos(a), cy - r * 0.18 + rad * math.sin(a)))
    PA.fill_poly(img, star, SNOW, seed=seed + 3, value=0.05)
    PA.hand_stroke(d, star, INK, 4, closed=True, seed=seed + 4, wavelength=60.0)
    # banner
    ban = [(cx - r * 0.92, cy + r * 0.42), (cx + r * 0.92, cy + r * 0.42),
           (cx + r * 0.84, cy + r * 0.92), (cx - r * 0.84, cy + r * 0.92)]
    PA.fill_poly(img, ban, RED, seed=seed + 5, value=0.08)
    PA.hand_stroke(d, ban, INK, 6, closed=True, seed=seed + 6, wavelength=90.0)


def _world_map(d, seed, cx=640, cy=380, s=1.0, missiles=True):
    """A flat hand-drawn world map -- the world the command centre watches.

    Continents are crude closed blobs; they do not need to be geographically
    good, they need to be IMMEDIATELY readable as "the world". Drawn on a
    pale ground so the red missile arcs pop.
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [0, 0, W, H], (222, 226, 232), seed=seed, value=0.04)
    PA.paper_overlay(img, seed=seed + 1)
    # a graticule so it reads as a map, not as blobs on a page
    for k in range(5):
        yy = cy - 210 * s + k * 105 * s
        PA.hand_stroke(d, [(cx - 620 * s, yy), (cx + 620 * s, yy)],
                       (200, 206, 214), 3, closed=False, seed=seed + 2 + k,
                       wavelength=140.0)
    for k in range(6):
        xx = cx - 560 * s + k * 224 * s
        PA.hand_stroke(d, [(xx, cy - 250 * s), (xx, cy + 250 * s)],
                       (200, 206, 214), 3, closed=False, seed=seed + 10 + k,
                       wavelength=140.0)

    blobs = [
        # (cx, cy, rx, ry)  -- Americas, Europe/Africa, Asia, Australia
        (-360, -30, 130, 190), (-330, 170, 96, 110), (-90, -110, 120, 84),
        (60, 30, 150, 150), (140, 170, 96, 120), (330, -110, 200, 130),
        (420, 90, 130, 90), (-70, 190, 96, 64),
    ]
    for i, (ox, oy, rx, ry) in enumerate(blobs):
        pts = PA.ellipse_pts(cx + ox * s, cy + oy * s, rx * s, ry * s, n=40)
        PA.fill_poly(img, pts, (150, 168, 148), seed=seed + 30 + i, value=0.07)
        PA.hand_stroke(d, pts, INK, 5, closed=True, seed=seed + 60 + i,
                       wavelength=150.0)

    if missiles:
        arcs = [(cx - 360 * s, cy - 30 * s, cx + 60 * s, cy - 40 * s),
                (cx - 330 * s, cy + 170 * s, cx + 140 * s, cy + 170 * s),
                (cx + 330 * s, cy - 110 * s, cx + 140 * s, cy + 40 * s)]
        for i, (x0, y0, x1, y1) in enumerate(arcs):
            pts = []
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            mz = min(x0, x1) * 0.42 + max(x0, x1) * 0.58
            myy = my - 170 * s
            for k in range(33):
                t = k / 32.0
                px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mz + t * t * x1
                py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * myy + t * t * y1
                pts.append((px, py))
            PA.hand_stroke(d, pts, RED, 6, closed=False, seed=seed + 90 + i,
                           wavelength=170.0)
            # the warhead: a blunt chevron at the END of the arc
            ax, ay = pts[-1]
            bx, by = pts[-4]
            vx, vy = ax - bx, ay - by
            n = math.hypot(vx, vy) or 1.0
            vx, vy = vx / n, vy / n
            px, py = -vy, vx
            PA.fill_poly(img, [(ax + vx * 26, ay + vy * 26),
                               (ax + px * 20, ay + py * 20),
                               (ax - px * 20, ay - py * 20)],
                         RED, seed=seed + 95 + i, value=0.05)


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

    # ===== b01-b02  the mountain, then the scratch ======================== #
    def c_massif(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 5, ground=(170, 170, 174))
        _massif(d, 640, HZ + 30, 900, 110, 6)
    els.append(card(1, 2, c_massif))
    els.append(cap(1, W // 2, 662, size=34))

    def c_scratch(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 7, ground=(170, 170, 174))
        _massif(d, 640, HZ + 30, 900, 110, 8)
        _scratch(d, 210, 420, 700, 300, 9)
    els.append(card(2, 3, c_scratch))
    els.append(cap(2, W // 2, 662, size=34, fill=RED))

    # ===== b03  the cut, and the character ================================ #
    def c_cut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 11, ground=(170, 170, 174))
        # the wedge of rock cut open -- the reveal
        _massif(d, 700, HZ + 30, 900, 110, 12)
        cut = [(60, 720), (60, 300), (360, 210), (470, 330), (520, 720)]
        PA.fill_poly(tile, cut, (56, 58, 68), seed=13, value=0.06)
        PA.hand_stroke(d, [(60, 300), (360, 210), (470, 330), (520, 720)],
                       INK, 7, closed=False, seed=14, wavelength=150.0)
        for k in range(4):
            yy = 330 + k * 78
            PA.hand_stroke(d, [(70, yy), (400, yy - 20)], DEEPER, 30,
                           closed=False, seed=15 + k, wavelength=90.0,
                           vary=0.05)
        SC.closeup(d, 900, 380, 200, 'deadpan', 17)
        D.draw_bubble(tile, 'not a mountain', (700, 90), tail_to=(900, 300),
                      font_size=40, max_w=330)
    els.append(card(3, 4, c_cut, kind='character'))
    els.append(cap(3, W // 2, 690, size=32, fill=RED))

    # ===== b04  the title beat =========================================== #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 19, ground=(170, 170, 174))
        _massif(d, 640, HZ + 40, 940, 80, 20)
        # a tiny state outline + town dot, as the plan asks
        st = [(980, 470), (1080, 442), (1150, 470), (1130, 540), (1180, 578),
              (1090, 600), (1000, 566), (952, 520)]
        PA.fill_poly(tile, st, (188, 194, 186), seed=21, value=0.07)
        PA.hand_stroke(d, st, INK, 5, closed=True, seed=22, wavelength=90.0)
        PA.fill_poly(tile, PA.ellipse_pts(1058, 512, 12, 12, n=20), RED,
                     seed=23, value=0.05)
        D.draw_label(tile, 'COLORADO SPRINGS', center=(1064, 626), color=INK,
                     size=26)
        # No D.draw_title HERE. engine3 composites the persistent scene title
        # LAST, on top of every element, so an in-card draw_title renders UNDER
        # the title strip and the two overprint into an unreadable smear --
        # confirmed on b04 at full res, where "CHEYENNE MOUNTAIN" (in-card,
        # caps) and "Cheyenne Mountain" (title strip) printed on top of each
        # other. The caption under this card already reads "This is the
        # Cheyenne Mountain Complex.", so the words are not missing without it.
    els.append(card(4, 5, c_title))
    els.append(cap(4, W // 2, 690, size=34, fill=RED))

    # ===== b05  the construction site, early sixties ====================== #
    # TOP EDGE RULE. engine3 stamps the persistent "Cheyenne Mountain" title
    # over the top of every finished frame, so no card may put ink above
    # y~104. Every _massif() summit in this chapter is therefore held at 112 or
    # below; this one was at 60, which drove the summit keyline straight through
    # the title. The flanks still run off both edges, so the mountain owns the
    # frame exactly as before -- it is 52 px shorter at the top, not smaller.
    def c_site(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 27, sky=(190, 198, 210), ground=(160, 158, 156))
        _massif(d, 700, HZ + 20, 920, 112, 28, snow=False)
        # the cut face with the tunnel mouth, and plant on the shelf
        _portal(d, 380, 400, 130, 150, 29, open_frac=0.2, doors=3)
        for k, x in enumerate((760, 900, 1040)):
            PA.hand_stroke(d, [(x, 560), (x, 470)], STEEL_D, 6,
                           closed=False, seed=30 + k, wavelength=60.0)
            PA.hand_stroke(d, [(x - 34, 470), (x + 34, 470)], STEEL_D, 6,
                           closed=False, seed=40 + k, wavelength=60.0)
        # a spoil heap and a truck
        heap = [(560, 660), (640, 570), (740, 662)]
        PA.fill_poly(tile, heap, (176, 170, 158), seed=29, value=0.08)
        PA.hand_stroke(d, heap, INK, 5, closed=True, seed=30, wavelength=90.0)
        PA.fill_rect(tile, [880, 620, 1120, 672], (168, 84, 62), seed=31,
                     value=0.07)
        PA.hand_stroke(d, [(880, 620), (1120, 620), (1120, 672), (880, 672)],
                       INK, 5, closed=True, seed=32, wavelength=70.0)
        D.draw_label(tile, 'EARLY 1960s', center=(300, 150), color=INK, size=34)
    els.append(card(5, 6, c_site))
    els.append(cap(5, W // 2, 690, size=32))

    # ===== b06  the Cold War globe ======================================== #
    def c_globe(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (214, 220, 228), seed=37, value=0.05)
        PA.paper_overlay(tile, seed=38)
        _massif(d, 640, H, 940, 470, 39, snow=False, rock=(178, 178, 182),
                shade=(146, 146, 152))
        # the globe, cropped by the left edge -- frame-fill on the map too
        g = PA.ellipse_pts(300, 330, 300, 300, n=72)
        PA.fill_poly(tile, g, (150, 172, 196), seed=40, value=0.07)
        PA.hand_stroke(d, g, INK, 7, closed=True, seed=41, wavelength=170.0)
        for k, ry in enumerate((0.32, 0.66)):
            PA.hand_stroke(d, PA.ellipse_pts(300, 330, 300 * ry, 300, n=48),
                           (116, 138, 162), 4, closed=True, seed=42 + k,
                           wavelength=120.0)
        PA.hand_stroke(d, [(0, 330), (600, 330)], (116, 138, 162), 4,
                       closed=False, seed=44, wavelength=120.0)
        for i, (ox, oy) in enumerate(((-60, -60), (110, 40))):
            c = PA.ellipse_pts(300 + ox, 330 + oy, 92, 76, n=36)
            PA.fill_poly(tile, c, (176, 158, 128), seed=45 + i, value=0.07)
            PA.hand_stroke(d, c, INK, 5, closed=True, seed=47 + i,
                           wavelength=100.0)
        # the confrontation, and the red line running under the mountain
        PA.hand_stroke(d, [(430, 250), (760, 180), (1090, 250)], RED, 6,
                       closed=False, seed=50, wavelength=170.0)
        D.draw_label(tile, 'THE COLD WAR SET THE SCHEDULE', center=(640, 660),
                     color=INK, size=32)
    els.append(card(6, 7, c_globe))
    els.append(cap(6, W // 2, 620, size=30))

    # ===== b07  granite, close ============================================ #
    def c_granite(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 53, rock=(176, 158, 158))
        # mottled inclusions: short strokes of darker and paler rock
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
        # the crack the water comes from. TOP EDGE RULE: engine3 stamps the
        # persistent chapter title over y 9..73 of every frame, so the crack now
        # opens at y=116 rather than running off the top edge -- it reads as a
        # fissure that starts inside the visible rock face, which is also what
        # the surrounding mottling implies.
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
        D.draw_label(tile, 'SOLID GRANITE', center=(900, 640), color=SNOW,
                     size=44)
    els.append(card(7, 8, c_granite))
    els.append(cap(7, W // 2, 100, size=32))

    # ===== b08  fifteen tunnels, drilled ================================== #
    def c_tunnels(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 137, sky=(196, 202, 212), ground=(168, 166, 164))
        _massif(d, 660, HZ + 30, 940, 90, 138, snow=False)
        # the access tunnel, then FIFTEEN parallel galleries receding into it
        ty = 470
        PA.hand_stroke(d, [(-30, ty), (430, ty - 10)], DEEPER, 66,
                       closed=False, seed=139, wavelength=130.0, vary=0.05)
        PA.hand_stroke(d, [(-30, ty), (430, ty - 10)], INK, 4, closed=False,
                       seed=140, wavelength=130.0)
        for i in range(15):
            t = i / 14.0
            x0 = 450 + t * 620
            y0 = 180 + t * 300
            x1 = x0 + 120 + (1 - t) * 90
            y1 = y0 + 40 + (1 - t) * 30
            PA.hand_stroke(d, [(x0, y0), (x1, y1)], DEEPER, 26 - t * 12,
                           closed=False, seed=150 + i, wavelength=90.0,
                           vary=0.06)
            PA.hand_stroke(d, [(x0, y0), (x1, y1)], STEEL_D, 4, closed=False,
                           seed=200 + i, wavelength=90.0)
        D.draw_number(tile, '15', center=(1150, 620), color=RED, size=200)
        SC.fullbody(d, 660, 620, 400, pose='standing', expression='awed',
                    seed=205)
    els.append(card(8, 9, c_tunnels))
    els.append(cap(8, W // 2, 118, size=32, fill=RED))

    # ===== b09  THE HERO: fifteen buildings inside the mountain =========== #
    # FRAME-FILL. The massif's feet run off the BOTTOM edge and its flanks run
    # off BOTH sides; the exposed cut face fills the left 44% of the frame from
    # its top edge to the bottom of the picture, and the fifteen buildings are
    # stacked on it big enough to read as BUILDINGS (a lit slot and a doorway),
    # not as hatching. cx is chosen so the cut line lands mid-frame: exposed
    # rock left, solid massif right.
    def c_hero(tile, fw, fh):
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
            # the lit slot inside -- the reason the building is occupied
            PA.hand_stroke(d, [(bx + 10, by + 26), (bx + bw - 10, by + 16)],
                           LAMP if i % 3 else STEEL, 7, closed=False,
                           seed=270 + i, wavelength=50.0)
            # a doorway, so the block reads as entered
            PA.hand_stroke(d, [(bx + bw * 0.40, by + bh - 16),
                               (bx + bw * 0.40, by + bh - 56),
                               (bx + bw * 0.66, by + bh - 58),
                               (bx + bw * 0.66, by + bh - 16)],
                           DEEPER, 5, closed=True, seed=290 + i,
                           wavelength=40.0)
        D.draw_number(tile, '15', center=(1090, 500), color=RED, size=230)
        D.draw_label(tile, 'BUILDINGS INSIDE', center=(1090, 650), color=SNOW,
                     size=40)
    els.append(card(9, 10, c_hero))
    els.append(cap(9, 1090, 130, size=32, fill=RED))

    # ===== b10  the spring under a floor ================================== #
    def c_spring(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 291, rock=(160, 158, 158), deep=(96, 94, 96))
        # the floor slab, cropped left and right -- it OVERSPANS the frame
        slab = [(-30, 250), (W + 30, 210), (W + 30, 330), (-30, 380)]
        PA.fill_poly(tile, slab, CONCRETE, seed=292, value=0.08)
        PA.hand_stroke(d, [( -30, 250), (W + 30, 210), (W + 30, 330),
                           (-30, 380)], INK, 8, closed=True, seed=293,
                       wavelength=190.0)
        for k in range(4):
            x = 160 + k * 330
            _spring(d, x, 380, 210, 250, 300 + k)
        # the floor it carries, cropped at the top edge
        PA.fill_rect(tile, [-20, -20, W + 20, 120], CONCRETE_D, seed=310,
                     value=0.07)
        D.draw_label(tile, 'STEEL SPRINGS', center=(640, 620), color=SNOW,
                     size=44)
    els.append(card(10, 11, c_spring))
    els.append(cap(10, W // 2, 690, size=32))

    # ===== b11  the springs swallow the shock ============================ #
    def c_shock(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 321, rock=(160, 158, 158), deep=(96, 94, 96))
        slab = [(-30, 250), (W + 30, 210), (W + 30, 330), (-30, 380)]
        PA.fill_poly(tile, slab, CONCRETE, seed=322, value=0.08)
        PA.hand_stroke(d, [(-30, 250), (W + 30, 210), (W + 30, 330),
                           (-30, 380)], INK, 8, closed=True, seed=323,
                       wavelength=190.0)
        PA.fill_rect(tile, [-20, -20, W + 20, 110], CONCRETE_D, seed=324,
                     value=0.07)
        # squashed springs: wide and flat, which is what "swallowing" looks like
        for k, x in enumerate((230, 640, 1050)):
            _spring(d, x, 370, 320, 150, 330 + k, squash=0.42)
            PA.hand_stroke(d, [(x - 170, 372), (x + 170, 372)], STEEL_D, 6,
                           closed=False, seed=340 + k, wavelength=70.0)
        # THE SHOCK: three thick red arrows driving down onto the floor
        for k, x in enumerate((230, 640, 1050)):
            D.draw_arrow(tile, (x, 150), (x, 244), color=RED, width=26,
                         head=58)
        D.draw_label(tile, 'SWALLOWS THE SHOCK', center=(640, 630), color=RED,
                     size=46)
    els.append(card(11, 12, c_shock))
    els.append(cap(11, W // 2, 692, size=32, fill=RED))

    # ===== b12  the mountain above does the rest ========================= #
    def c_overhang(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 351, rock=(160, 158, 158), deep=(90, 88, 90))
        # the overhang: a huge rock ceiling pressing down from the top edge
        ceil = [(-30, -20), (W + 30, -20), (W + 30, 190), (900, 250),
                (520, 300), (180, 240), (-30, 160)]
        PA.fill_poly(tile, ceil, ROCK, seed=352, value=0.09)
        PA.hand_stroke(d, ceil, INK, 8, closed=True, seed=353, wavelength=190.0)
        # the room under it
        PA.fill_rect(tile, [-20, 300, W + 20, 720], DEEP, seed=354, value=0.06)
        PA.hand_stroke(d, [(520, 300), (520, 720)], INK, 6, closed=False,
                       seed=355, wavelength=140.0)
        SC.fullbody(d, 380, 690, 420, pose='shrug', expression='skeptic',
                    seed=356)
        D.draw_bubble(tile, 'then what stops the rest?', (470, 380),
                      tail_to=(400, 500), font_size=34, max_w=340)
    els.append(card(12, 13, c_overhang, kind='character'))
    els.append(cap(12, 300, 690, size=32))

    # ===== b13  the entrance, one small doorway ========================== #
    def c_entrance(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 361, sky=(186, 194, 206), ground=(158, 158, 160))
        # the massif fills the frame and the doorway is a HOLE in it.
        # peak_y held at 112: at 40 the summit keyline struck through the
        # persistent title. Same mountain, 72 px shorter at the top, and the
        # flanks still run off both edges so it still dominates the frame.
        _massif(d, 560, HZ + 40, 1100, 112, 362, snow=False)
        _portal(d, 470, 400, 150, 210, 363, open_frac=0.2, doors=0)
        # the camouflage trees on the flank, painted concrete
        for k, (x, s) in enumerate(((830, 200), (980, 160), (1120, 190))):
            _painted_tree(d, x, HZ + 60, s, 370 + k, col=CONCRETE_D)
        SC.fullbody(d, 300, 700, 420, pose='standing', expression='shock',
                    seed=380)
    els.append(card(13, 14, c_entrance, kind='character'))
    els.append(cap(13, 880, 690, size=32, fill=RED))

    # ===== b14  seven hundred tons ======================================== #
    def c_tons(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 391, rock=(158, 156, 156), deep=(90, 88, 90))
        # TOP EDGE RULE. The frame's top edge is cy - h*0.56, so the original
        # cy=380 h=640 put it at y=22 -- straight through the persistent title.
        # cy=430 h=560 lands it at y=116 and the frame still runs off the
        # bottom edge (743 > 720), so the door is still cropped by the frame
        # and still dominates it. Only the top 94 px came off.
        _blast_door(d, 560, 430, 900, 560, 392, closed=True)
        D.draw_number(tile, '700', center=(560, 400), color=RED, size=210)
        D.draw_label(tile, 'TONS', center=(560, 600), color=RED, size=90)
    els.append(card(14, 15, c_tons))
    els.append(cap(14, W // 2, 692, size=32, fill=RED))

    # ===== b15  the door seals ============================================ #
    def c_seal(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 401, rock=(158, 156, 156), deep=(90, 88, 90))
        _blast_door(d, 470, 380, 1000, 680, 402, closed=False)
        D.draw_label(tile, 'SEALS COMPLETELY', center=(1000, 620), color=RED,
                     size=50)
    els.append(card(15, 16, c_seal))
    els.append(cap(15, W // 2, 692, size=32, fill=RED))

    # ===== b16  the sealed door, awed ===================================== #
    def c_awed(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DEEPER, seed=411, value=0.10)
        PA.paper_overlay(tile, seed=412)
        # A near-black card needs a lit course at the head for the engine's
        # hardcoded-INK title to read against (see scene_common.title_backdrop).
        # Drawn before the door, the light beam and the frame, so the art stays
        # on top of it.
        SC.title_backdrop(tile, 1411, col=(100, 104, 120))
        # the door SMALL in a huge dark frame: the frame is the subject too
        _blast_door(d, 640, 420, 760, 560, 413, closed=True)
        # TOP EDGE RULE (same rule, and the same two objects, as b38): the
        # unlit frame's top edge was at y=40->20 under a 26px stroke, so a
        # near-black bar ran the full width straight through the title. Dropped
        # to y=126->108, which is still "a huge dark frame" around a small door.
        PA.hand_stroke(d, [(-30, 126), (W + 30, 108), (W + 30, 700), (-30, 720)],
                       INK, 26, closed=True, seed=414, wavelength=220.0)
        # one cold light from above
        beam = [(606, 104), (674, 104), (816, 300), (464, 300)]
        PA.fill_poly(tile, beam, (66, 70, 82), seed=415, value=0.04)
        SC.closeup(d, 250, 420, 200, 'awed', 416)
    els.append(card(16, 17, c_awed, kind='character'))
    els.append(cap(16, 860, 668, size=32, fill=RED))

    # ===== b17  the cold chamber ========================================== #
    def c_cold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 421, rock=(146, 146, 150), deep=(70, 72, 80))
        # a narrow chamber: converging walls so it reads as a room
        PA.fill_poly(tile, [(0, 120), (430, 250), (430, 720), (0, 720)],
                     (128, 128, 134), seed=422, value=0.07)
        PA.fill_poly(tile, [(W, 120), (900, 250), (900, 720), (W, 720)],
                     (128, 128, 134), seed=423, value=0.07)
        PA.fill_rect(tile, [430, 250, 900, 720], (86, 88, 96), seed=424,
                     value=0.06)
        for k in range(4):
            yy = 300 + k * 96
            PA.hand_stroke(d, [(430, yy), (900, yy)], (66, 68, 76), 6,
                           closed=False, seed=430 + k, wavelength=110.0)
        # the thermometer -- the coldest reading on the scale
        S.thermometer(d, 1090, 620, 460, 0.18, seed=440, hot=False)
        D.draw_label(tile, 'COLD', center=(1090, 200), color=SNOW, size=52)
        # the breath: three cold puffs, which is what makes a room feel cold
        for k in range(4):
            x = 560 + k * 40
            y = 420 + (k % 2) * 26
            PA.hand_stroke(d, [(x, y), (x + 54, y - 18), (x + 100, y + 6)],
                           (196, 200, 210), 6, closed=False, seed=450 + k,
                           wavelength=70.0, vary=0.15)
    els.append(card(17, 18, c_cold))
    els.append(cap(17, 300, 680, size=32))

    # ===== b18  the machines stay stable ================================= #
    def c_machines(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 461, rock=(146, 146, 150), deep=(70, 72, 80))
        PA.fill_poly(tile, [(-30, 200), (W + 30, 160), (W + 30, 720),
                            (-30, 720)], (92, 94, 102), seed=462, value=0.07)
        for k in range(6):
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
                                                  n=20), GREEN, seed=500 + k * 3 + c,
                             value=0.05)
        PA.hand_stroke(d, [(-30, 600), (W + 30, 596)], CONCRETE_D, 12,
                       closed=False, seed=510, wavelength=200.0)
        D.draw_label(tile, 'STABLE', center=(640, 220), color=GREEN, size=54)
    els.append(card(18, 19, c_machines))
    els.append(cap(18, W // 2, 690, size=32))

    # ===== b19  the corridor, two hundred staff =========================== #
    def c_staff(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (96, 98, 106), seed=521, value=0.08)
        PA.paper_overlay(tile, seed=522)
        # the corridor vanishing to a lit far door
        PA.fill_poly(tile, [(560, 240), (720, 240), (760, 560), (520, 560)],
                     LAMP, seed=523, value=0.05)
        PA.hand_stroke(d, [(560, 240), (520, 560), (760, 560), (720, 240)],
                       INK, 6, closed=True, seed=524, wavelength=120.0)
        # converging walls
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
        # small figures in coats, big enough to read as people
        for k, x in enumerate((200, 470, 810, 1080)):
            SC.fullbody(d, x, 700 - k % 2 * 18, 330, pose='standing',
                        expression='neutral', seed=560 + k)
        D.draw_label(tile, 'ABOUT 200 STAFF', center=(640, 190), color=SNOW,
                     size=44)
    els.append(card(19, 20, c_staff, kind='character'))
    els.append(cap(19, W // 2, 692, size=32))

    # ===== b20  its own power: the severed cable ========================= #
    def c_own_power(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 204, 214), seed=571, value=0.05)
        PA.paper_overlay(tile, seed=572)
        # left half: the surface, with a city that has power
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
        PA.hand_stroke(d, [(60, 268), (60, 200), (200, 200)], STEEL_D, 5,
                       closed=False, seed=590, wavelength=80.0)
        PA.hand_stroke(d, [(200, 200), (420, 200)], STEEL_D, 5, closed=False,
                       seed=591, wavelength=90.0)
        PA.hand_stroke(d, [(420, 200), (420, 268)], STEEL_D, 5, closed=False,
                       seed=592, wavelength=60.0)
        # the severed cable: it comes down from the city and STOPS in mid-air
        PA.hand_stroke(d, [(600, 300), (700, 400), (800, 470)], STEEL_D, 10,
                       closed=False, seed=593, wavelength=110.0)
        D.draw_arrow(tile, (860, 520), (760, 452), color=RED, width=9, head=44)
        D.draw_red_x(tile, [712, 402, 812, 502])
        # right half: underground, its own generators.
        # TOP EDGE RULE. This dark panel used to start at x=660, which put a
        # 58-luminance fill inside the title rect (x 484..796) for its full
        # height -- engine3 stamps the persistent title over y 9..73 of every
        # frame, so the underground was painted straight through it. The panel
        # edge moves to x=812, clear of the rect, and the surface fill above
        # extends to meet it. The split still reads as two cross-sections: the
        # light city ground on the left, the dark machine hall on the right.
        PA.fill_rect(tile, [812, 0, 1300, 740], (58, 60, 68), seed=594,
                     value=0.07)
        PA.hand_stroke(d, [(812, 0), (812, 740)], INK, 6, closed=False,
                       seed=595, wavelength=140.0)
        PA.hand_stroke(d, [(812, 200), (1300, 200)], INK, 6, closed=False,
                       seed=596, wavelength=170.0)
        _generator(d, 1000, 690, 340, 260, 597)
        D.draw_label(tile, 'ITS OWN POWER', center=(1020, 130), color=SNOW,
                     size=44)
    els.append(card(20, 21, c_own_power))
    els.append(cap(20, 300, 690, size=32, fill=RED))

    # ===== b21  the generators, deep underground ========================== #
    def c_generators(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 601, rock=(150, 146, 146), deep=(64, 64, 72))
        PA.fill_rect(tile, [-20, 300, W + 20, 740], (84, 84, 92), seed=602,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 300), (W + 20, 292)], INK, 8, closed=False,
                       seed=603, wavelength=200.0)
        for k in range(6):
            x = 40 + k * 100
            PA.hand_stroke(d, [(x, 292), (x, 250)], INK, 8, closed=False,
                           seed=610 + k, wavelength=60.0)
        # a row of generator sets, cropped left and right
        for k in range(3):
            _generator(d, 200 + k * 440, 700, 330, 280, 620 + k)
        for k in range(6):
            _drum(d, 90 + k * 216, 716, 92, 128, 650 + k)
        D.draw_label(tile, 'DEEP UNDERGROUND', center=(640, 190), color=SNOW,
                     size=46)
    els.append(card(21, 22, c_generators))
    els.append(cap(21, W // 2, 690, size=32))

    # ===== b22  no power line reaches the mountain ======================= #
    def c_noline(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 661, sky=(186, 196, 210), ground=(158, 162, 166))
        _massif(d, 900, HZ + 40, 900, 90, 662, snow=False)
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
        SC.fullbody(d, 660, 700, 420, pose='pointing', expression='skeptic',
                    seed=684)
        D.draw_bubble(tile, 'no line in', (760, 520), tail_to=(700, 560),
                      font_size=36, max_w=250)
    els.append(card(22, 23, c_noline, kind='character'))
    els.append(cap(22, 240, 660, size=32, fill=RED))

    # ===== b23  water from the springs =================================== #
    def c_water(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 691, rock=(168, 152, 152), deep=(96, 92, 96))
        # the granite crack, running from the top edge down to the pool.
        # TOP EDGE RULE. This crack used to start at y=-20, off the top of the
        # frame, so it ran full-height through the band engine3 stamps the
        # persistent title into. It now opens at y=110 -- still "from above",
        # but clear of the title.
        crack = [(700, 110), (742, 220), (700, 380), (770, 560), (748, 640)]
        PA.hand_stroke(d, crack, DEEPER, 14, closed=False, seed=692,
                       wavelength=150.0)
        PA.hand_stroke(d, [(660, 110), (700, 220), (660, 380)], (200, 186, 184),
                       8, closed=False, seed=693, wavelength=120.0)
        # drips falling
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
        # the splash rings
        for k, r in enumerate((70, 110, 150)):
            PA.hand_stroke(d, PA.ellipse_pts(742, 640, r, r * 0.24, n=40),
                           (168, 202, 220), 4, closed=True, seed=720 + k,
                           wavelength=90.0)
        D.draw_label(tile, 'SPRINGS IN THE ROCK', center=(300, 200),
                     color=SNOW, size=42)
    els.append(card(23, 24, c_water))
    els.append(cap(23, 300, 260, size=32))

    # ===== b24  the water tanks =========================================== #
    def c_tanks(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_bg(tile, 731, rock=(150, 148, 148), deep=(74, 76, 84))
        # low ceiling with a strip light -- the "low ceiling light" of the plan
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
        # rows of tanks, cropped at both sides
        for k in range(5):
            x0 = 30 + k * 268
            _water_tank(d, x0, 260, x0 + 200, 600, 750 + k, level=0.55 + 0.08 * k)
        D.draw_label(tile, 'THOUSANDS OF GALLONS', center=(640, 664),
                     color=SNOW, size=42)
    els.append(card(24, 25, c_tanks))
    els.append(cap(24, W // 2, 120, size=32))

    # ===== b25  nothing gets in =========================================== #
    def c_nothing_in(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DEEPER, seed=761, value=0.10)
        PA.paper_overlay(tile, seed=762)
        # the lit course the near-black title reads against (see b16)
        SC.title_backdrop(tile, 1761, col=(100, 104, 120))
        # the SEALED room: a wall of concrete with ONE sealed hatch, and the
        # character small inside it -- alone
        PA.fill_rect(tile, [-20, 140, W + 20, 700], (78, 80, 88), seed=763,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 140), (W + 20, 132)], INK, 8, closed=False,
                       seed=764, wavelength=190.0)
        _blast_door(d, 900, 420, 480, 400, 765, closed=True)
        SC.closeup(d, 320, 400, 205, 'worried', 766)
        D.draw_bubble(tile, 'nothing gets in', (470, 130), tail_to=(330, 300),
                      font_size=38, max_w=300)
    els.append(card(25, 26, c_nothing_in, kind='character'))
    els.append(cap(25, W // 2, 692, size=32, fill=RED))

    # ===== b26  the space defence centre: HERO CARD #2 =================== #
    # The SAME cross-section construction as b09, so the chapter's two hero
    # frames are visibly the same place -- but here the exposed face carries the
    # OPERATIONS FLOOR: one long lit room with a bank of consoles, running off
    # the bottom edge. The badge is stamped on the solid rock to the right, so
    # the two halves of the frame read as "the room" and "what it is for".
    def c_defence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 771, sky=(200, 206, 216), ground=(168, 168, 172))
        _cross_section(d, 980, H + 80, 1180, 30, 772, chambers=False)
        room = [(-30, 330), (560, 292), (560, 800), (-30, 800)]
        PA.fill_poly(tile, room, (58, 60, 70), seed=773, value=0.06)
        PA.hand_stroke(d, [(-30, 330), (560, 292)], INK, 7, closed=False,
                       seed=774, wavelength=170.0)
        _console_bank(d, 10, 560, 720, 775, rows=2, green=True)
        _norad_badge(d, 990, 420, 190, 776)
        # No in-card draw_title here either (same overprint as b04). The
        # caption "This was the space defence centre." carries the line.
    els.append(card(26, 27, c_defence))
    els.append(cap(26, 990, 660, size=32, fill=RED))

    # ===== b27  the satellites overhead -- MOTION ======================== #
    def c_satellites(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (44, 52, 74), seed=781, value=0.10)
        PA.paper_overlay(tile, seed=782)
        # the lit course the near-black title reads against (see b16), under the
        # stars and the satellites
        SC.title_backdrop(tile, 1781, col=(100, 104, 120))
        for k in range(60):
            a = (k * 2.399) % 6.283
            rr = 40 + (k * 83) % 700
            x = 640 + rr * math.cos(a) * 1.25
            y = 320 + rr * math.sin(a) * 0.7
            if 0 < x < W and 0 < y < 560:
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(226, 232, 244))
        # the massif below, cropped by the bottom edge
        _massif(d, 640, 760, 1000, 470, 783, snow=True, rock=(88, 92, 106),
                shade=(66, 70, 84))
        # the orbits, arcing right over the roof
        for k in range(3):
            orb = PA.arc_pts(640, 900, 420 + k * 150, 560 + k * 90,
                             208, 332, n=48)
            PA.hand_stroke(d, orb, (108, 130, 176), 4, closed=False,
                           seed=790 + k, wavelength=180.0)
        for k, (sx, sy) in enumerate(((240, 210), (620, 150), (1000, 220))):
            _sat(d, sx, sy, 66, 800 + k)
            # beams crossing the roof -- the thing the narrator says happens
            D.draw_arrow(tile, (sx, sy + 90), (sx + 130, 620), color=RED,
                         width=7, head=40)
        _radar(d, 640, 400, 190, 806, sweep=-50, blips=2)
    els.append(card(27, 28, c_satellites))
    els.append(cap(27, W // 2, 692, size=32, fill=RED))

    # ===== b28  the sensors watching ===================================== #
    def c_radar_watch(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (56, 58, 68), seed=811, value=0.08)
        PA.paper_overlay(tile, seed=812)
        # the lit course the near-black title reads against (see b16), under the
        # scope, the console bank and the character
        SC.title_backdrop(tile, 1811, col=(100, 104, 120))
        # The scope dominates and runs off the BOTTOM edge -- frame-fill. It used
        # to sit at cy=350, which left a 20px margin at the top and put the dark
        # disc and its ink rim straight behind the title; cy=410 drops the rim to
        # y=76, clear of the band, and crops the disc at the bottom instead,
        # which is what the comment always claimed.
        _radar(d, 520, 410, 330, 813, sweep=-40, blips=4)
        PA.hand_stroke(d, [(900, 84), (900, 720)], INK, 7, closed=False,
                       seed=814, wavelength=180.0)
        _console_bank(d, 930, 1330, 700, 815, rows=1, green=True)
        SC.closeup(d, 1060, 250, 165, 'skeptic', 816)
    els.append(card(28, 29, c_radar_watch, kind='character'))
    els.append(cap(28, 300, 692, size=32))

    # ===== b29  the warning clocks start -- MOTION ======================== #
    def c_warn(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE ROOM LIGHTS SHIFT: the whole card is red-lit, which is the only
        # thing that changes and the only reason it reads as an escalation
        PA.fill_rect(tile, [0, 0, W, H], (74, 44, 46), seed=821, value=0.11)
        PA.paper_overlay(tile, seed=822)
        # the lit course the near-black title reads against (see b16). Kept the
        # same cool slate as the rest of the chapter so the red-lit room still
        # reads as the escalation, not as a different scene.
        SC.title_backdrop(tile, 1821, col=(100, 104, 120))
        # Same drop as b28: cy=410 keeps the scope's ink rim at y=76, clear of
        # the title band, and runs the disc off the bottom edge.
        _radar(d, 500, 410, 330, 823, sweep=-30, arc=120, blips=3, warm=True)
        PA.hand_stroke(d, [(880, 84), (880, 720)], INK, 7, closed=False,
                       seed=824, wavelength=180.0)
        _console_bank(d, 910, 1330, 700, 825, rows=1, lamps=False, green=True)
        # the clock, hand jumping
        face = PA.ellipse_pts(1090, 300, 140, 140, n=48)
        PA.fill_poly(tile, face, (250, 246, 236), seed=826, value=0.04)
        PA.hand_stroke(d, face, INK, 7, closed=True, seed=827, wavelength=110.0)
        for k in range(12):
            a = k * math.pi / 6.0
            PA.hand_stroke(d, [(1090 + 108 * math.cos(a), 300 + 108 * math.sin(a)),
                               (1090 + 122 * math.cos(a), 300 + 122 * math.sin(a))],
                           INK, 4, closed=False, seed=828 + k, wavelength=40.0)
        PA.hand_stroke(d, [(1090, 300), (1090 + 96, 300 - 78)], RED, 9,
                       closed=False, seed=840, wavelength=70.0)
        PA.hand_stroke(d, [(1090, 300), (1090, 218)], INK, 7, closed=False,
                       seed=841, wavelength=60.0)
        D.draw_label(tile, 'WARNING', center=(1090, 500), color=RED, size=48)
    els.append(card(29, 30, c_warn))
    els.append(cap(29, 300, 692, size=32, fill=RED))

    # ===== b30  the painted forest, from the air ========================= #
    def c_painted_forest(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 851, sky=(206, 212, 222), ground=(160, 162, 166))
        # a low aircraft angle: the slope is the whole lower frame
        slope = [(-30, 300), (400, 250), (900, 300), (W + 30, 380),
                 (W + 30, 740), (-30, 740)]
        PA.fill_poly(tile, slope, (150, 152, 156), seed=852, value=0.09)
        PA.hand_stroke(d, [( -30, 300), (400, 250), (900, 300), (W + 30, 380)],
                       INK, 6, closed=False, seed=853, wavelength=190.0)
        # rows of painted slabs, near ones cropped by the bottom edge
        for k in range(9):
            t = k / 8.0
            x = -20 + t * 1340
            y = 300 + t * 120
            _painted_tree(d, x, y + 40, 210 - t * 90, 860 + k, col=CONCRETE)
        for k in range(7):
            t = k / 6.0
            _painted_tree(d, 40 + t * 1220, 730 - t * 40, 250 + t * 60,
                          880 + k, col=CONCRETE_D)
    els.append(card(30, 31, c_painted_forest))
    els.append(cap(30, W // 2, 130, size=32))

    # ===== b31  a painted concrete tree, close =========================== #
    def c_slab_tree(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (156, 158, 162), seed=891, value=0.09)
        PA.paper_overlay(tile, seed=892)
        # THE SLAB, huge, cropped by both side edges -- it IS the frame
        _painted_tree(d, 620, 780, 900, 893, w=620, col=CONCRETE, drips=True)
        # A CONCRETE-TONE BAND across the title, laid AFTER the slab. This is a
        # light card and the title already reads against the pale concrete, but
        # the slab's stepped silhouette runs clean off the top of the frame, so
        # its two upper edges cross the title band. The slab must stay huge and
        # cropped -- that is the whole point of the card -- so rather than
        # shrink it we lay the same flat concrete tone across the head of the
        # frame AFTER the slab, hiding its outline where it would cross the
        # title. The band tone is within a few levels of the slab fill
        # (CONCRETE), so the silhouette emerges from below the band unchanged and
        # the band reads as more painted concrete rather than a UI bar.
        SC.title_backdrop(tile, 894, col=(168, 170, 174))
        # brush texture on the slab: broad flat strokes, not hatching
        for k in range(9):
            yy = 200 + k * 52
            PA.hand_stroke(d, [(200, yy), (560 + (k * 37) % 200, yy - 14)],
                           (222, 220, 212), 12, closed=False, seed=900 + k,
                           wavelength=140.0, vary=0.22)
        SC.fullbody(d, 1080, 780, 420, pose='pointing', expression='awed',
                    seed=910)
        D.draw_label(tile, 'PAINTED CONCRETE', center=(300, 140), color=INK,
                     size=44)
    els.append(card(31, 32, c_slab_tree, kind='character'))
    els.append(cap(31, W // 2, 690, size=32, fill=RED))

    # ===== b32  the vents behind the fake trees ========================= #
    def c_vents(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (158, 160, 164), seed=921, value=0.09)
        PA.paper_overlay(tile, seed=922)
        slope = [(-30, 340), (W + 30, 300), (W + 30, 740), (-30, 740)]
        PA.fill_poly(tile, slope, (146, 148, 152), seed=923, value=0.09)
        PA.hand_stroke(d, [(-30, 340), (W + 30, 300)], INK, 6, closed=False,
                       seed=924, wavelength=190.0)
        # the vents stand BEHIND the trees: draw them first, then the slabs
        for k, x in enumerate((250, 620, 990)):
            _vent_tower(d, x, 330 - k * 8, 210, 930 + k, col=(128, 130, 136))
        for k in range(7):
            t = k / 6.0
            _painted_tree(d, 90 + t * 1120, 720 - t * 30, 230 + t * 70,
                          940 + k, col=CONCRETE_D)
        D.draw_label(tile, 'THEY HIDE THE VENTS', center=(640, 170),
                     color=INK, size=42)
    els.append(card(32, 33, c_vents))
    els.append(cap(32, W // 2, 690, size=32))

    # ===== b33  from the air, nothing stands out ========================= #
    def c_air(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 951, sky=(190, 200, 214), ground=(162, 164, 168))
        # the whole massif, seen from above and filling the frame.
        # TOP EDGE RULE. peak_y 40 put the summit keyline (and the shrug's head,
        # at feet_y - height = -30) straight through the persistent title.
        # peak_y 112 keeps the summit clear, and the figure moves off the
        # summit onto the right flank -- standing ON the peak would put his head
        # back in the band. He is also 50 px TALLER than before, so he reads
        # better against the rock instead of being a speck at the top.
        _massif(d, 640, 780, 1300, 112, 952, snow=False, rock=(158, 160, 164),
                shade=(140, 142, 148))
        for k in range(11):
            t = k / 10.0
            _painted_tree(d, -40 + t * 1360, 640 + (k % 3) * 90, 90 + (k % 4) * 26,
                          960 + k, col=CONCRETE_D, drips=False)
        # the flank under him: at x=1120 the silhouette runs y~303, so his feet
        # at 315 sit just inside the rock rather than floating on the keyline.
        SC.fullbody(d, 1120, 315, 190, pose='shrug', expression='neutral',
                    seed=975)
    els.append(card(33, 34, c_air, kind='character'))
    els.append(cap(33, W // 2, 690, size=32, fill=RED))

    # ===== b34  nobody confirms this part ================================ #
    def c_nobody(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 981, sky=(206, 212, 222), ground=(172, 172, 176))
        _massif(d, 900, H + 60, 900, 240, 982, snow=True)
        SC.closeup(d, 360, 380, 215, 'deadpan', 983)
        D.draw_bubble(tile, 'nobody confirms this part', (620, 110),
                      tail_to=(430, 300), font_size=34, max_w=380)
    els.append(card(34, 35, c_nobody, kind='character'))
    els.append(cap(34, 300, 692, size=32, fill=RED))

    # ===== b35  still staffed ============================================= #
    def c_still_staffed(tile, fw, fh):
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
        _console_bank(d, 560, 900, 560, 998, rows=1)
        for k, x in enumerate((190, 380, 1000, 1170)):
            SC.fullbody(d, x, 720, 340, pose='standing', expression='neutral',
                        seed=1000 + k)
    els.append(card(35, 36, c_still_staffed, kind='character'))
    els.append(cap(35, W // 2, 140, size=32))

    # ===== b36  the plain cars on the highway ============================ #
    def c_cars(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _sky(tile, 1011, sky=(196, 204, 216), ground=(158, 160, 164))
        PA.fill_rect(tile, [-20, 470, W + 20, 740], (108, 110, 116), seed=1012,
                     value=0.07)
        PA.hand_stroke(d, [(-20, 470), (W + 20, 464)], INK, 7, closed=False,
                       seed=1013, wavelength=190.0)
        for k in range(7):
            xx = -20 + k * 200
            PA.hand_stroke(d, [(xx, 610), (xx + 110, 610)], SNOW, 8,
                           closed=False, seed=1014 + k, wavelength=80.0)
        # a line of PLAIN cars, no flags, all identical: that sameness is the
        # point. The black car at the end is the only one that differs.
        for k in range(5):
            x = 40 + k * 190
            body = [(x, 520), (x + 150, 520), (x + 138, 470), (x + 24, 470)]
            PA.fill_poly(tile, body, (146, 150, 158), seed=1030 + k,
                         value=0.07)
            PA.hand_stroke(d, body, INK, 5, closed=True, seed=1040 + k,
                           wavelength=70.0)
            for w in (0.22, 0.78):
                PA.fill_poly(tile, PA.ellipse_pts(x + 150 * w, 522, 20, 20, n=20),
                             INK, seed=1050 + k, value=0.05)
        body = [(1000, 520), (1180, 520), (1164, 452), (1016, 452)]
        PA.fill_poly(tile, body, (38, 40, 46), seed=1060, value=0.07)
        PA.hand_stroke(d, body, INK, 6, closed=True, seed=1061, wavelength=80.0)
        for w in (0.20, 0.80):
            PA.fill_poly(tile, PA.ellipse_pts(1000 + 180 * w, 522, 22, 22, n=20),
                         INK, seed=1062, value=0.05)
    els.append(card(36, 37, c_cars))
    els.append(cap(36, W // 2, 690, size=32))

    # ===== b37  the quoted number ========================================= #
    def c_chalkboard(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (58, 66, 60), seed=1071, value=0.09)
        PA.paper_overlay(tile, seed=1072)
        # the lit course the near-black title reads against (see b16), under the
        # chalkboard's top rail
        SC.title_backdrop(tile, 2071, col=(100, 104, 120))
        # the chalkboard fills the frame. TOP EDGE RULE: the board's tan frame rail
        # (L~127) sat at y=30, straight through the persistent title, so the top
        # edge moves to y=112. The area above it is the near-identical base
        # green, so the board still reads as filling the frame; only the rail
        # is out of the band.
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
    els.append(card(37, 38, c_chalkboard))
    els.append(cap(37, W // 2, 692, size=32, fill=RED))

    # ===== b38  the finale: the sealed door, held still =================== #
    def c_finale(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DEEPER, seed=1091, value=0.11)
        PA.paper_overlay(tile, seed=1092)
        # the lit course the near-black title reads against (see b16)
        SC.title_backdrop(tile, 2091, col=(100, 104, 120))
        # TOP EDGE RULE. The door frame's top edge is cy - h*0.56, so cy=400
        # h=660 put it at y=30 and the whole concrete frame -- L~160 against a
        # L~58 card -- filled the title band. cy=480 lands the frame edge at
        # y=110. Same 900x660 door, just lower: it still runs off the bottom
        # edge and still owns the frame. The light from above moves down with it.
        _blast_door(d, 640, 480, 900, 660, 1093, closed=True)
        # ONE cold light, from above and slightly left
        beam = [(580, 104), (668, 104), (860, 300), (420, 300)]
        PA.fill_poly(tile, beam, (58, 62, 74), seed=1094, value=0.04)
        PA.hand_stroke(d, [(520, 108), (740, 108)], (206, 210, 220), 14,
                       closed=False, seed=1095, wavelength=110.0)
        # The unlit frame closing round it. Same TOP EDGE RULE as the door
        # above: the OUTER frame's top edge was still at y=30->12 with a 30px
        # stroke, so it filled rows 0-45 of the band and its bottom edge cut
        # straight across the title. y=118->100 drops the whole stroke below the
        # band; the frame still closes off all four sides and still owns them.
        PA.hand_stroke(d, [(-30, 118), (W + 30, 100), (W + 30, 706), (-30, 716)],
                       INK, 30, closed=True, seed=1096, wavelength=220.0)
    els.append(card(38, 39, c_finale))
    els.append(cap(38, 640, 678, size=36, fill=RED))

    return SC.finish(els, TITLE, clock, title_seed=41)


# ---------------------------------------------------------------------------
# small local satellites (b27 needs a spacecraft; pinegap has one but this file
# must stand alone)
# ---------------------------------------------------------------------------

def _sat(d, cx, cy, s, seed):
    """A simple satellite: bus, two paneled wings, a dish, a whip antenna."""
    img = PA.img_of(d)
    for side in (-1, 1):
        x0, x1 = cx + side * s * 0.42, cx + side * s * 1.55
        PA.fill_rect(img, [min(x0, x1), cy - s * 0.28, max(x0, x1), cy + s * 0.28],
                     (110, 136, 176), seed=seed + (7 if side > 0 else 8),
                     value=0.06)
        PA.hand_stroke(d, [(min(x0, x1), cy - s * 0.28), (max(x0, x1), cy - s * 0.28),
                           (max(x0, x1), cy + s * 0.28), (min(x0, x1), cy + s * 0.28)],
                       INK, 6, closed=True, seed=seed + (9 if side > 0 else 10),
                       wavelength=110.0)
        for k in range(1, 5):
            x = min(x0, x1) + (max(x0, x1) - min(x0, x1)) * k / 5.0
            PA.hand_stroke(d, [(x, cy - s * 0.28), (x, cy + s * 0.28)], INK, 2,
                           closed=False, seed=seed + 20 + k, wavelength=70.0)
    bus = [(cx - s * 0.42, cy - s * 0.32), (cx + s * 0.42, cy - s * 0.32),
           (cx + s * 0.42, cy + s * 0.32), (cx - s * 0.42, cy + s * 0.32)]
    PA.fill_poly(img, bus, (168, 176, 184), seed=seed, value=0.08)
    PA.hand_stroke(d, bus, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    dish = PA.ellipse_pts(cx, cy, s * 0.24, s * 0.17, n=40)
    PA.fill_poly(img, dish, (206, 212, 218), seed=seed + 2, value=0.05)
    PA.hand_stroke(d, dish, INK, 4, closed=True, seed=seed + 3, wavelength=80.0)
    PA.hand_stroke(d, [(cx, cy - s * 0.32), (cx, cy - s * 0.74)], INK, 5,
                   closed=False, seed=seed + 4, wavelength=70.0)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))
