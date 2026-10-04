"""fortknox scene -- chapter 2 of the bunker film.

FORT KNOX, KENTUCKY. The US Bullion Depository: a long low brick building with a
green roof on top of a hill, and under it a steel-and-concrete box holding gold
that mostly belongs to other countries.

ONE CARD PER BEAT, AND EACH CARD PAINTS ITS OWN WHOLE FRAME. 44 short sentences
(see _plan_fortknox.py) and beats.json gives each an exact [start, end], so there
is no reason to guess at card boundaries. Every card function fills the tile
background-to-subject. beats.json splits every one of the 44 beats into exactly
ONE phrase, so there is 44 cards and 44 captions and no card ever has to hold a
second idea.

FRAME-FILL. The recurring defect in this project's history is a subject parked
small in the middle of an empty field. Every card here is authored against that:
the building runs off both side edges, the gothic arch hall fills the frame, the
vault door is drawn BIGGER than the frame is tall so the frame crops it, the bar
stacks run off the top and both sides, and the corridors converge past the left
and right edges. Nothing is parked.

THE CHAPTER'S THREE HEROES, each given two or three frames so the beat has
somewhere to go:
  b14-b16  the gothic arch hall (b14/b15/b16 are consecutive, so the same
           construction is redrawn closer each time rather than repeated)
  b18-b24  the vault door, including the hero at b20 -- a round steel face whose
           radius is larger than the frame is tall, so the frame cuts it
  b26-b30  the gold: a nine-floor cross-section, then bar walls to the ceiling

CADENCE. Still-dominant, one cut per sentence (44 cuts in 108s). The single
motion track is b36, the one beat where the narrator says the gold was moved.

Run:  python lib/fortknox_scene.py --preview --video
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
import v2type as TY

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'fortknox'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Fort Knox'

# The engine stamps the title LAST and hardcodes its fill to near-black, so on
# the vault-interior night cards it is invisible. Those cards get one lit
# gunmetal course across the head (SC.title_backdrop) for it to read against,
# and band_intrusions exempts exactly those rows. Only the part inside the band
# is declared: rows below it are ordinary art and must still be checked.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# Gold is the subject, so the gold family gets three steps and everything else
# is granite and brick. ONE deep red accent, used only for the turn in each
# little group (the twist, the warning, the number that matters).
INK = SC.INK
RED = TY.RED                       # (208, 30, 32) -- the single accent
GOLD = (226, 172, 58)             # a bar's lit face
GOLD_HI = (246, 212, 116)         # a bar's top face, catching the lamps
GOLD_DK = (170, 122, 38)          # a bar's shadowed end / a lower row
GRANITE = (152, 148, 142)         # the building's stone
GRANITE_DK = (108, 106, 104)      # its shadowed courses
BRICK = (166, 100, 78)            # the long facade
BRICK_DK = (136, 78, 60)
ROOF = (74, 104, 78)              # the green roof
GRASS = (146, 168, 126)           # the Kentucky hills
SKY = (200, 212, 224)
SHADOW = (44, 42, 44)             # vault interior
SHADOW_DK = (28, 27, 30)
STEEL = (150, 156, 166)
STEEL_DK = (100, 106, 118)
PAPERW = (238, 232, 218)          # ledger / calendar pages
NIGHT = (24, 26, 38)

# The lit gunmetal course the near-black title reads on, for the night cards.
# Warm steel, clearly lighter than SHADOW (44,42,44) but still interior-night:
# it is the head of a vault wall catching the lamps, not a UI bar.
TITLE_COURSE = (100, 96, 92)

HZ = int(H * 0.62)                # horizon; sky_bg uses the same fraction


# ---------------------------------------------------------------------------
# background grounds
# ---------------------------------------------------------------------------

def _hills(tile, seed, sky=SKY, grass=GRASS, hz=HZ):
    """Full-frame exterior: sky, then rolling hills laid over the bottom."""
    d = ImageDraw.Draw(tile)
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    # The hills are ONE wobbled polygon that overshoots both side edges, so the
    # skyline reads as land the frame cuts through rather than a pasted strip.
    ridge = [(-40, hz + 96), (150, hz + 6), (420, hz + 74), (720, hz - 18),
             (1010, hz + 62), (1320, hz + 10)]
    PA.fill_poly(tile, ridge + [(W + 40, H + 40), (-40, H + 40)], grass,
                 seed=seed + 1, value=0.07)
    PA.hand_stroke(d, ridge, (108, 128, 92), 4, closed=False, seed=seed + 2,
                   wavelength=180.0)
    PA.paper_overlay(tile, seed=seed + 3)


def _dark(tile, seed, top=SHADOW, bot=SHADOW_DK):
    """Vault interior: a dark painted ground with paper tooth over it."""
    PA.fill_rect(tile, [0, 0, W, H], top, seed=seed, value=0.10)
    PA.fill_rect(tile, [0, HZ - 4, W, H], bot, seed=seed + 1, value=0.10)
    PA.paper_overlay(tile, seed=seed + 2)


def _pale(tile, seed, col=(232, 230, 224)):
    """A plain painted page ground, for the diagram cards."""
    PA.fill_rect(tile, [0, 0, W, H], col, seed=seed, value=0.05)
    PA.paper_overlay(tile, seed=seed + 1)


# ---------------------------------------------------------------------------
# architecture
# ---------------------------------------------------------------------------

def _arch_pts(cx, base_y, w, h, seg=26):
    """A round-headed arch opening: two jambs and a semicircular head.

    WHY ONE SHAPE AND NOT A RECT PLUS A HALF-CIRCLE STROKED SEPARATELY. The
    jamb tops have to MEET the springing line of the arch exactly or the
    opening shows a notch at each shoulder. Building the whole outline as one
    point list makes that impossible to get wrong.
    """
    r = w / 2.0
    spring = base_y - h + r          # where the head starts
    pts = [(cx - r, base_y), (cx - r, spring)]
    for i in range(seg + 1):
        a = math.pi - math.pi * i / float(seg)
        pts.append((cx + r * math.cos(a), spring + r * math.sin(a)))
    pts.append((cx + r, base_y))
    return pts


def _archway(d, cx, base_y, w, h, seed, lit=True, jamb=None):
    """An arched opening in a wall. `lit` fills it with the gold glow.

    THE JAMBS GO DOWN FIRST, THEN THE ARCH. Drawn the other way round the jamb
    rectangles sit ON TOP of the arch's springing and the opening reads as a
    gold arch with two grey posts stuck across its shoulders.

    THE GLOW CORE IS ITSELF AN ARCH. An earlier version filled a plain
    rectangle inside the opening; because the arch head curves away above the
    rectangle's top edge, the rectangle's corners stuck out past the arch and
    the whole opening read as a cream box with gold crescents either side of
    it. The inner glow is `_arch_pts` again, narrower and shorter, so it can
    never leave the opening it is supposed to be inside.
    """
    img = PA.img_of(d)
    if jamb:
        for s in (-1, 1):
            x0 = cx + s * (w / 2.0)
            x1 = x0 + s * jamb
            PA.fill_rect(img, [min(x0, x1), base_y - h - 14, max(x0, x1),
                               base_y + 12], GRANITE, seed=seed + 3 + s,
                         value=0.07)
            PA.hand_stroke(d, [(x0, base_y - h - 14), (x0, base_y + 12)], INK,
                           5, closed=False, seed=seed + 4 + s, wavelength=90.0)
            PA.hand_stroke(d, [(x1, base_y - h - 14), (x1, base_y + 12)], INK,
                           5, closed=False, seed=seed + 6 + s, wavelength=90.0)

    pts = _arch_pts(cx, base_y, w, h)
    PA.fill_poly(img, pts, (244, 200, 108) if lit else SHADOW, seed=seed,
                 value=0.10)
    if lit:
        inner = _arch_pts(cx, base_y - h * 0.04, w * 0.50, h * 0.86)
        PA.fill_poly(img, inner, (252, 234, 176), seed=seed + 2, value=0.06)
    PA.hand_stroke(d, pts, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)


def _brick_field(d, x0, y0, x1, y1, seed, col=BRICK, mortar=(196, 178, 158),
                 course=34, brick_w=76):
    """Brick courses over a wall region -- mortar lines, staggered per course.

    The mortar is drawn THIN and in a light value. An early version stroked
    every course at 4px in near-black, and at this density the wall read as a
    dark grid drawn over the frame rather than as masonry.
    """
    n = 0
    y = y0
    while y < y1:
        off = (brick_w / 2.0) if (n % 2) else 0.0
        x = x0 - off
        while x < x1:
            if not (y < 0 and False):
                PA.hand_stroke(d, [(x, y), (x + brick_w, y)], mortar, 3,
                               closed=False, seed=seed + n * 97 + int(x),
                               wavelength=140.0)
            x += brick_w
        y += course
        n += 1
    for x in range(int(x0) - int(brick_w), int(x1) + int(brick_w), int(brick_w)):
        PA.hand_stroke(d, [(x, y0), (x, y1)], mortar, 2, closed=False,
                       seed=seed + 4001 + x, wavelength=170.0)


def _gothic_arch(d, cx, base_y, w, h, seed, col=GRANITE, width=6):
    """A POINTED arch -- the Gothic hall motif (b14, b15, b16).

    Two circular arcs struck from the OPPOSITE jamb meet at a point; that
    intersection is the apex, so the curve is computed, not eyeballed. A
    round-topped arch here would say nothing about Gothic.
    """
    img = PA.img_of(d)
    r = w * 1.32
    # arc centres at the two springing points, each swung the OTHER way
    a = (cx - w / 2.0, base_y)
    b = (cx + w / 2.0, base_y)
    pts = [(a[0], base_y)]
    n = 30
    # left arc: centre at b, from the left jamb up to the apex
    for i in range(n + 1):
        t = i / float(n)
        ang = math.pi + (math.pi / 2.0) * (1.0 - t) * 0.62
        pts.append((b[0] + r * math.cos(ang), b[1] + r * math.sin(ang)))
    for i in range(n + 1):
        t = i / float(n)
        ang = math.pi / 2.0 - (math.pi / 2.0) * 0.62 * t
        pts.append((a[0] + r * math.cos(ang), a[1] + r * math.sin(ang)))
    pts.append((b[0], base_y))
    PA.fill_poly(img, pts, col, seed=seed, value=0.07)
    PA.hand_stroke(d, pts, INK, width, closed=True, seed=seed + 1,
                   wavelength=120.0)
    return pts


# ---------------------------------------------------------------------------
# the vault door -- the chapter's key object
# ---------------------------------------------------------------------------

def _vault_door(d, cx, cy, r, seed, hinge=True, wheel=True, rings=3,
                face=STEEL, face_dk=STEEL_DK, bolts=16):
    """A circular steel vault door: plate face, concentric rings, bolt circle,
    wheel handle, hinge blocks.

    WHY RINGS AND BOLTS AND NOT JUST A DISC. A plain grey circle with an ink
    outline reads as a porthole or a washer. What says "vault door" is the
    EVIDENCE OF MASS: raised concentric rings stepping back toward the centre,
    a circle of bolt heads on the outer ring, and a spoked wheel breaking the
    symmetry so the eye has something to hang on.

    `r` is meant to be large. At b18-b20 the door is drawn bigger than the
    frame is tall and cropped left, right and top.
    """
    img = PA.img_of(d)

    # the plate itself, with a darker crescent low-left so it is not a flat disc
    ring = PA.ellipse_pts(cx, cy, r, r, n=96)
    PA.fill_poly(img, ring, face, seed=seed, value=0.08)
    shade = PA.arc_pts(cx, cy, r * 0.995, r * 0.995, 62, 168, n=44)
    PA.hand_stroke(d, [(cx + (p[0] - cx) * 0.995, cy + (p[1] - cy) * 0.995)
                       for p in shade], face_dk, 10, closed=False,
                   seed=seed + 1, wavelength=r * 0.5)

    # concentric raised rings, stepping in
    for k in range(rings):
        rr = r * (1.0 - 0.16 * (k + 1))
        c = face if k % 2 == 0 else (face_dk if k % 2 else face)
        PA.hand_stroke(d, PA.ellipse_pts(cx, cy, rr, rr, n=72), c,
                       max(4, int(r * 0.045)), closed=True, seed=seed + 10 + k,
                       wavelength=r * 0.45)
        PA.hand_stroke(d, PA.ellipse_pts(cx, cy, rr * 0.955, rr * 0.955, n=72),
                       INK, 3, closed=True, seed=seed + 20 + k,
                       wavelength=r * 0.45)

    # the bolt circle, on the outer ring
    br = r * 0.885
    for k in range(bolts):
        a = 2.0 * math.pi * k / bolts + 0.11
        bx, by = cx + br * math.cos(a), cy + br * math.sin(a)
        s = max(5.0, r * 0.028)
        PA.fill_poly(img, PA.ellipse_pts(bx, by, s, s, n=12), face_dk,
                     seed=seed + 40 + k, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(bx, by, s, s, n=14), INK,
                       max(2, int(r * 0.012)), closed=True, seed=seed + 70 + k,
                       wavelength=40.0)

    # the wheel handle: a hub, four spokes and a rim, offset from dead centre so
    # the face is not a set of concentric bullseyes
    if wheel:
        wx, wy, wr = cx - r * 0.10, cy + r * 0.06, r * 0.42
        PA.hand_stroke(d, PA.ellipse_pts(wx, wy, wr, wr, n=48), INK,
                       max(5, int(r * 0.035)), closed=True, seed=seed + 90,
                       wavelength=r * 0.4)
        PA.hand_stroke(d, PA.ellipse_pts(wx, wy, wr * 0.80, wr * 0.80, n=40),
                       face_dk, max(3, int(r * 0.018)), closed=True,
                       seed=seed + 91, wavelength=r * 0.4)
        for k in range(4):
            a = math.pi * k / 4.0 + 0.4
            PA.hand_stroke(d, [(wx, wy), (wx + wr * math.cos(a),
                                          wy + wr * math.sin(a))], INK,
                           max(4, int(r * 0.026)), closed=False,
                           seed=seed + 92 + k, wavelength=r * 0.4)
        PA.fill_poly(img, PA.ellipse_pts(wx, wy, r * 0.085, r * 0.085, n=16),
                     face_dk, seed=seed + 96, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(wx, wy, r * 0.085, r * 0.085, n=16),
                       INK, max(2, int(r * 0.014)), closed=True, seed=seed + 97,
                       wavelength=40.0)

    # the rim keyline LAST, so nothing draws over the silhouette
    PA.hand_stroke(d, ring, INK, max(6, int(r * 0.035)), closed=True,
                   seed=seed + 100, wavelength=r * 0.5)

    # hinge blocks on the left jamb, OUTSIDE the disc
    if hinge:
        for k, hy in enumerate((cy - r * 0.46, cy + r * 0.20)):
            bw, bh = r * 0.30, r * 0.34
            bx = cx - r - bw * 0.62
            box = [(bx, hy - bh / 2), (bx + bw, hy - bh / 2),
                   (bx + bw, hy + bh / 2), (bx, hy + bh / 2)]
            PA.fill_poly(img, box, STEEL_DK, seed=seed + 110 + k, value=0.07)
            PA.hand_stroke(d, box, INK, max(4, int(r * 0.022)), closed=True,
                           seed=seed + 111 + k, wavelength=r * 0.4)
            PA.hand_stroke(d, [(bx + bw * 0.5, hy - bh * 0.62),
                               (bx + bw * 0.5, hy + bh * 0.62)], INK,
                           max(5, int(r * 0.030)), closed=False,
                           seed=seed + 112 + k, wavelength=r * 0.3)


# ---------------------------------------------------------------------------
# the gold
# ---------------------------------------------------------------------------

def _gold_bar(d, x0, y0, w, h, seed, top=GOLD_HI, face=GOLD, side=GOLD_DK):
    """One bullion bar, drawn as a shallow 3-D brick: a lit top face, a front
    face, and a darker right end.

    WHY THE TOP FACE. A flat gold rectangle reads as a sticky note. The thin
    lighter parallelogram along the top edge is the whole cue that says "a
    solid ingot you could pick up", and it costs four points.
    """
    img = PA.img_of(d)
    skew = h * 0.42
    top_pts = [(x0, y0), (x0 + w, y0), (x0 + w - skew, y0 - skew),
               (x0 + skew, y0 - skew)]
    front = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]
    side_pts = [(x0 + w, y0), (x0 + w - skew, y0 - skew),
                (x0 + w - skew, y0 + h - skew), (x0 + w, y0 + h)]
    PA.fill_poly(img, top_pts, top, seed=seed, value=0.07)
    PA.fill_poly(img, front, face, seed=seed + 1, value=0.08)
    PA.fill_poly(img, side_pts, side, seed=seed + 2, value=0.07)
    PA.hand_stroke(d, front, INK, 4, closed=True, seed=seed + 3, wavelength=90.0)
    PA.hand_stroke(d, top_pts, INK, 4, closed=True, seed=seed + 4,
                   wavelength=90.0)
    PA.hand_stroke(d, side_pts, INK, 3, closed=True, seed=seed + 5, wavelength=80.0)


def _bar_wall(d, x0, y0, x1, y1, seed, bw=118, bh=44, gap=6,
              stagger=True, dim=0.0):
    """A field of stacked bars filling a rectangle, row by row.

    ROWS ARE DARKER AS THEY GO DOWN. A stack lit evenly top to bottom reads as
    a printed pattern; darkening the lower courses is what makes it read as a
    pile with depth. `dim` (0..1) pushes the WHOLE field toward the shadow
    colour, which is how b35 gets a nearly bare floor from the same routine.
    """
    img = PA.img_of(d)
    rows = int(math.ceil((y1 - y0) / float(bh + gap))) + 1
    for r in range(rows):
        fy = y0 + r * (bh + gap)
        if fy - bh > y1:
            break
        depth = min(1.0, r / float(max(1, rows - 1)))
        # three-step value ladder down the pile
        base = GOLD if depth < 0.34 else (GOLD_DK if depth < 0.7 else (150, 110, 44))
        # the lit top face lifts toward white as the pile comes forward, so the
        # top row catches the lamps and the lower rows go dull
        top_c = tuple(int(c * (1.0 - dim) * (0.62 + 0.38 * (1.0 - depth)))
                      for c in GOLD_HI)
        f_c = tuple(int(c * (1.0 - dim)) for c in base)
        s_c = tuple(int(c * (1.0 - dim) * 0.80) for c in base)
        off = (bw / 2.0) if (stagger and r % 2) else 0.0
        x = x0 - off
        k = 0
        while x < x1:
            PA_x0 = x + 3
            PA_x1 = min(x + bw - 3, x1 + 40)
            if PA_x1 - PA_x0 > 24:
                _gold_bar(d, PA_x0, fy, PA_x1 - PA_x0, bh, seed + r * 131 + k,
                          top=top_c, face=f_c, side=s_c)
            x += bw
            k += 1


def _bar_hall(d, seed, fill_frac=1.0, floor_y=690, ceil_y=104, back=3):
    """The gold hall: a receding stack of bar ranks, nearest rank biggest.

    `fill_frac` < 1 leaves the RIGHT of the floor bare (b35) -- the empty floor
    is the point of that beat, so the bars are pushed to one side and the
    character stands in the gap.

    WHY ceil_y IS 104 AND NOT -40. It used to default to -40, so the ranks ran
    off the TOP of the frame. That obeys the frame-fill rule (the subject owns
    the frame and is cropped by an edge) but it ignored the one region of the
    canvas that is not ours: engine3 stamps the persistent chapter title LAST,
    over everything, in roughly y 14..68. On b30 the bars came up through the
    whole band and left "Fort Knox" as black-on-gold mush -- unreadable. Caught
    by _coverage_gate.band_intrusions(), which found 15 offending beats in this
    chapter alone. 104 keeps the hall floor-to-near-ceiling and still running off
    both side edges (which is what actually sells the scale) while leaving the
    title legible.
    """
    img = PA.img_of(d)
    # the back wall and its floor line, so the ranks have something to recede to
    PA.fill_rect(img, [0, ceil_y, W, floor_y], (58, 52, 46), seed=seed,
                 value=0.10)
    PA.paper_overlay(img, seed=seed + 1)
    span = W * (1.0 if fill_frac >= 1.0 else 0.52)
    x0 = -60 if fill_frac >= 1.0 else -60
    for b in range(back):
        depth = 1.0 - b / float(back)
        sc = 0.42 + 0.58 * depth
        by0 = floor_y - (floor_y - ceil_y) * (0.30 + 0.70 * depth)
        by1 = floor_y - (floor_y - ceil_y) * 0.02 * (1.0 - depth)
        _bar_wall(d, x0, by0, x0 + span * (0.72 + 0.28 * depth), by1,
                  seed + 40 * b, bw=int(96 * sc) + 30, bh=int(34 * sc) + 12,
                  gap=int(6 * sc) + 3, stagger=bool(b % 2),
                  dim=0.0 if b == 0 else 0.18 + 0.14 * (back - b))
    PA.fill_rect(img, [0, floor_y - 26, W, H], (72, 62, 52), seed=seed + 90,
                 value=0.08)
    PA.hand_stroke(d, [(0, floor_y - 26), (W, floor_y - 26)], (44, 38, 34), 5,
                   closed=False, seed=seed + 91, wavelength=160.0)


def _flag(d, x, y, w, seed, cols=None, pole=True):
    """A small national flag on a short pole."""
    img = PA.img_of(d)
    h = w * 0.62
    if pole:
        PA.hand_stroke(d, [(x, y), (x, y - h - w * 0.34)], INK, 5,
                       closed=False, seed=seed, wavelength=60.0)
    if cols is None:
        cols = [(198, 40, 44), (250, 250, 248), (52, 74, 150)]
    n = len(cols)
    for i, c in enumerate(cols):
        x0 = x + i * (w / n)
        PA.fill_rect(img, [x0, y - h - w * 0.34, x0 + w / n, y - w * 0.34], c,
                     seed=seed + 1 + i, value=0.06)
    PA.hand_stroke(d, [(x, y - h - w * 0.34), (x + w, y - h - w * 0.34),
                       (x + w, y - w * 0.34), (x, y - w * 0.34)], INK, 4,
                   closed=True, seed=seed + 9, wavelength=70.0)


# ---------------------------------------------------------------------------
# the building
# ---------------------------------------------------------------------------

def _facade(d, x0, x1, base_y, wall_h, seed, wall=BRICK, roof=ROOF,
            roof_h=None, roof_over=26, courses=True, windows=0, win_cols=None,
            label_strip=None):
    """The long low building: a brick box, a shallow green roof overhanging it.

    `windows` > 0 turns it into the SCHOOL reading (b08): evenly spaced tall
    openings in two rows. Keeping one facade routine with a flag means b07 and
    b08 are provably the SAME building, which is what the narration claims.
    """
    img = PA.img_of(d)
    roof_h = roof_h or wall_h * 0.20
    body = [(x0, base_y), (x0, base_y - wall_h), (x1, base_y - wall_h),
            (x1, base_y)]
    PA.fill_poly(img, body, wall, seed=seed, value=0.07)
    if courses:
        _brick_field(d, x0, base_y - wall_h, x1, base_y, seed + 1,
                     col=wall, course=max(20, wall_h / 9.0),
                     brick_w=max(56, wall_h / 3.4))
    # the roof: a shallow trapezoid overhanging both ends, so the building has
    # a real eave shadow instead of a line
    ov = roof_over
    top_y = base_y - wall_h - roof_h
    rpts = [(x0 - ov, base_y - wall_h), (x1 + ov, base_y - wall_h),
            (x1 + ov - 10, top_y), (x0 - ov + 10, top_y)]
    PA.fill_poly(img, rpts, roof, seed=seed + 3, value=0.07)
    PA.hand_stroke(d, rpts, INK, 6, closed=True, seed=seed + 4, wavelength=150.0)
    PA.fill_rect(img, [x0 - ov, base_y - wall_h - 3, x1 + ov, base_y - wall_h + 12],
                 (52, 46, 44), seed=seed + 5, value=0.06)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 6, wavelength=160.0)

    if windows:
        wc = win_cols or [(250, 246, 232), (86, 122, 168)]
        n = windows
        span = (x1 - x0 - 120) / float(n)
        for i in range(n):
            cx = x0 + 60 + span * (i + 0.5)
            for row, (wy, wh) in enumerate(((base_y - wall_h * 0.72, wall_h * 0.26),
                                            (base_y - wall_h * 0.34, wall_h * 0.22))):
                ww = span * 0.44
                _archway(d, cx, wy, ww, wh, seed + 20 + i * 7 + row,
                         lit=(row == 1), jamb=None)
    return body


def _kentucky(d, cx, cy, s, seed, col=(150, 168, 130)):
    """A hand-drawn Kentucky: the long west edge, the big north-east bend of the
    Cumberland/Tennessee line, and the pointy south-west tip.

    It is a rough polygon, not a traced border. What has to be right is the
    SILHOUETTE a viewer already carries -- a tall north, a notch, and a tail
    running down-left -- so the dot reads as "in the north-central hills".
    """
    img = PA.img_of(d)
    u = [(0.02, 0.34), (0.10, 0.16), (0.34, 0.06), (0.56, 0.10), (0.62, 0.00),
         (0.74, 0.14), (0.90, 0.22), (0.98, 0.42), (0.86, 0.58), (0.70, 0.52),
         (0.58, 0.70), (0.44, 0.86), (0.28, 0.98), (0.18, 0.80), (0.08, 0.60)]
    pts = [(cx + (px - 0.5) * s, cy + (py - 0.5) * s) for px, py in u]
    PA.fill_poly(img, pts, col, seed=seed, value=0.08)
    PA.hand_stroke(d, pts, INK, 7, closed=True, seed=seed + 1, wavelength=140.0)
    return pts


def _castle(d, cx, base_y, w, h, seed):
    """A small toy castle: two corner towers, a curtain wall, one arrow slit.

    It is deliberately a CARTOON castle -- the beat is a comparison, not a
    reconstruction, so it is drawn as the thing everyone pictures.
    """
    img = PA.img_of(d)
    tw = w * 0.24
    wall = [(cx - w / 2, base_y), (cx - w / 2, base_y - h),
            (cx + w / 2, base_y - h), (cx + w / 2, base_y)]
    PA.fill_poly(img, wall, GRANITE, seed=seed, value=0.07)
    PA.hand_stroke(d, wall, INK, 6, closed=True, seed=seed + 1, wavelength=130.0)
    for k, y in enumerate((base_y - h, base_y - h * 0.66)):
        step = tw / 3.0
        x = cx - w / 2 - 4
        while x < cx + w / 2 + 4:
            merlon = [(x, y), (x, y - h * 0.09), (x + step * 1.5, y - h * 0.09),
                      (x + step * 1.5, y)]
            PA.fill_poly(img, merlon, GRANITE, seed=seed + 10 + k + int(x),
                         value=0.06)
            PA.hand_stroke(d, merlon, INK, 4, closed=True,
                           seed=seed + 30 + k + int(x), wavelength=60.0)
            x += step * 2.0
    for s in (-1, 1):
        tx = cx + s * (w / 2.0 + tw * 0.30)
        th = h * 1.30
        tower = [(tx - tw / 2, base_y), (tx - tw / 2, base_y - th),
                 (tx, base_y - th - tw * 0.42), (tx + tw / 2, base_y - th),
                 (tx + tw / 2, base_y)]
        PA.fill_poly(img, tower, GRANITE, seed=seed + 60 + s, value=0.07)
        PA.hand_stroke(d, tower, INK, 6, closed=True, seed=seed + 61 + s,
                       wavelength=120.0)
        cone = [(tx - tw * 0.60, base_y - th), (tx, base_y - th - tw * 0.58),
                (tx + tw * 0.60, base_y - th)]
        PA.fill_poly(img, cone, ROOF, seed=seed + 62 + s, value=0.07)
        PA.hand_stroke(d, cone, INK, 5, closed=True, seed=seed + 63 + s,
                       wavelength=90.0)
    # the arrow slit: a black keyhole, the one thing that says "siege"
    PA.fill_rect(img, [cx - w * 0.022, base_y - h * 0.62,
                       cx + w * 0.022, base_y - h * 0.34], INK,
                 seed=seed + 80, value=0.0)


# ---------------------------------------------------------------------------
# small props and people
# ---------------------------------------------------------------------------

def _person(d, x, feet_y, h, seed, col=(96, 122, 168), head_col=(238, 206, 172),
            arms=True, facing=1):
    """A flat crowd figure: body block, round head, no face.

    Faces are DELIBERATELY ABSENT on the crowd beats (b38-b40). A queue of
    tooned heads turns a crowd into a row of staring portraits; blank ovals read
    as "people, en masse" and keep the one real character the only face in the
    chapter.
    """
    img = PA.img_of(d)
    bw = h * 0.34
    body = [(x - bw / 2, feet_y), (x - bw / 2, feet_y - h * 0.78),
            (x + bw / 2, feet_y - h * 0.78), (x + bw / 2, feet_y)]
    PA.fill_poly(img, body, col, seed=seed, value=0.07)
    PA.hand_stroke(d, body, INK, 4, closed=True, seed=seed + 1, wavelength=70.0)
    hr = h * 0.155
    PA.fill_poly(img, PA.ellipse_pts(x, feet_y - h * 0.86, hr, hr, n=24),
                 head_col, seed=seed + 2, value=0.06)
    PA.hand_stroke(d, PA.ellipse_pts(x, feet_y - h * 0.86, hr, hr, n=24), INK,
                   4, closed=True, seed=seed + 3, wavelength=50.0)
    if arms:
        for s in (-1, 1):
            PA.hand_stroke(d, [(x + s * bw / 2, feet_y - h * 0.70),
                               (x + s * (bw / 2 + h * 0.09), feet_y - h * 0.40)],
                           INK, 5, closed=False, seed=seed + 4 + s,
                           wavelength=50.0)


def _car(d, cx, base_y, w, seed, col=(176, 62, 52)):
    """A small car, for the weight comparison at b29."""
    img = PA.img_of(d)
    h = w * 0.40
    lower = [(cx - w / 2, base_y), (cx - w / 2, base_y - h * 0.52),
             (cx + w / 2, base_y - h * 0.52), (cx + w / 2, base_y)]
    cabin = [(cx - w * 0.24, base_y - h * 0.52), (cx - w * 0.16, base_y - h),
             (cx + w * 0.18, base_y - h), (cx + w * 0.28, base_y - h * 0.52)]
    PA.fill_poly(img, lower, col, seed=seed, value=0.07)
    PA.fill_poly(img, cabin, col, seed=seed + 1, value=0.07)
    PA.hand_stroke(d, lower, INK, 5, closed=True, seed=seed + 2, wavelength=80.0)
    PA.hand_stroke(d, cabin, INK, 5, closed=True, seed=seed + 3, wavelength=80.0)
    for k, wx in enumerate((cx - w * 0.28, cx + w * 0.30)):
        PA.fill_poly(img, PA.ellipse_pts(wx, base_y, w * 0.13, w * 0.13, n=18),
                     (40, 38, 40), seed=seed + 4 + k, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(wx, base_y, w * 0.13, w * 0.13, n=18),
                       INK, 4, closed=True, seed=seed + 5 + k, wavelength=40.0)


def _bus(d, cx, base_y, w, seed, col=(222, 176, 44)):
    """A school bus, side on, cropped by an edge if it needs to be."""
    img = PA.img_of(d)
    h = w * 0.56
    body = [(cx - w / 2, base_y), (cx - w / 2, base_y - h),
            (cx + w / 2, base_y - h), (cx + w / 2, base_y)]
    PA.fill_poly(img, body, col, seed=seed, value=0.07)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    n = 5
    for i in range(n):
        x0 = cx - w * 0.42 + i * (w * 0.80 / n)
        win = [x0, base_y - h * 0.86, x0 + w * 0.80 / n - 10, base_y - h * 0.34]
        PA.fill_rect(img, win, (140, 176, 200), seed=seed + 2 + i, value=0.06)
        PA.hand_stroke(d, [(win[0], win[1]), (win[2], win[1]), (win[2], win[3]),
                           (win[0], win[3])], INK, 4, closed=True,
                       seed=seed + 8 + i, wavelength=60.0)
    for k, wx in enumerate((cx - w * 0.32, cx + w * 0.30)):
        PA.fill_poly(img, PA.ellipse_pts(wx, base_y, w * 0.10, w * 0.10, n=18),
                     (40, 38, 40), seed=seed + 14 + k, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(wx, base_y, w * 0.10, w * 0.10, n=18),
                       INK, 4, closed=True, seed=seed + 15 + k, wavelength=40.0)


def _page(d, x0, y0, x1, y1, seed, col=PAPERW, lines=6, ruled=True):
    """A ledger / calendar page: paper block, ruled lines, a red margin rule."""
    img = PA.img_of(d)
    PA.fill_rect(img, [x0, y0, x1, y1], col, seed=seed, value=0.05)
    PA.hand_stroke(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], INK, 5,
                   closed=True, seed=seed + 1, wavelength=120.0)
    if ruled:
        for i in range(lines):
            y = y0 + (y1 - y0) * (i + 1) / float(lines + 1)
            PA.hand_stroke(d, [(x0 + 26, y), (x1 - 26, y)], (172, 162, 146), 3,
                           closed=False, seed=seed + 2 + i, wavelength=110.0)
    PA.hand_stroke(d, [(x0 + 66, y0 + 8), (x0 + 66, y1 - 8)], RED, 3,
                   closed=False, seed=seed + 30, wavelength=140.0)


def _stamp(d, cx, cy, s, seed):
    """An ink stamp: a wooden handle on a rubber pad, tilted."""
    img = PA.img_of(d)
    pad = [(cx - s, cy), (cx - s * 0.78, cy - s * 0.52), (cx + s * 0.78, cy - s * 0.52),
           (cx + s, cy)]
    PA.fill_poly(img, pad, (52, 50, 54), seed=seed, value=0.05)
    PA.hand_stroke(d, pad, INK, 5, closed=True, seed=seed + 1, wavelength=70.0)
    knob = PA.ellipse_pts(cx, cy - s * 0.86, s * 0.30, s * 0.36, n=24)
    PA.fill_poly(img, knob, (128, 84, 52), seed=seed + 2, value=0.07)
    PA.hand_stroke(d, knob, INK, 5, closed=True, seed=seed + 3, wavelength=60.0)


# ---------------------------------------------------------------------------
# b11-b13  the construction site
# ---------------------------------------------------------------------------

def _shell(d, x0, x1, base_y, wall_h, seed, wall=GRANITE, floors=4,
           open_top=True, roofed=True):
    """The building UNDER construction: a bare concrete frame with the floors
    standing and NO brick skin, so it reads as a shell.

    The floors are drawn as receding slabs with an open bay at each end, which
    is what makes it a structure rather than a stack of planks: you can see
    THROUGH the building.
    """
    img = PA.img_of(d)
    if roofed:
        roof = [(x0 - 30, base_y - wall_h), (x1 + 30, base_y - wall_h),
                (x1 + 30, base_y - wall_h - 34), (x0 - 30, base_y - wall_h - 34)]
        PA.fill_poly(img, roof, (150, 148, 142), seed=seed, value=0.08)
        PA.hand_stroke(d, roof, INK, 5, closed=True, seed=seed + 1,
                       wavelength=150.0)
    body = [(x0, base_y), (x0, base_y - wall_h), (x1, base_y - wall_h),
            (x1, base_y)]
    PA.fill_poly(img, body, wall, seed=seed + 2, value=0.08)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 3, wavelength=170.0)
    # floor slabs, each a darker band with a lit top edge
    fh = wall_h / float(floors)
    for k in range(1, floors):
        yy = base_y - wall_h + k * fh
        PA.fill_rect(img, [x0 + 6, yy - 16, x1 - 6, yy + 6], (132, 130, 126),
                     seed=seed + 10 + k, value=0.06)
        PA.hand_stroke(d, [(x0 + 6, yy - 16), (x1 - 6, yy - 16)], INK, 4,
                       closed=False, seed=seed + 30 + k, wavelength=170.0)
    # the column grid: what actually makes it a frame
    n = 9
    for i in range(n + 1):
        xx = x0 + (x1 - x0) * i / float(n)
        PA.hand_stroke(d, [(xx, base_y - wall_h), (xx, base_y)], (172, 170, 164),
                       7, closed=False, seed=seed + 60 + i, wavelength=120.0)
    if open_top:
        PA.fill_rect(img, [x0 + 4, base_y - wall_h - 4, x1 - 4,
                           base_y - wall_h + 26], (48, 46, 48), seed=seed + 90,
                     value=0.05)


def _scaffold(d, x0, x1, base_y, top_y, seed, bays=6, col=(120, 116, 106)):
    """A run of scaffolding: standards, ledgers, diagonal braces, planks."""
    img = PA.img_of(d)
    step = (x1 - x0) / float(bays)
    for i in range(bays + 1):
        x = x0 + i * step
        PA.hand_stroke(d, [(x, top_y - 30), (x, base_y)], col, 8,
                       closed=False, seed=seed + i, wavelength=120.0)
    for k in range(4):
        yy = top_y + (base_y - top_y) * k / 4.0
        PA.hand_stroke(d, [(x0, yy), (x1, yy)], col, 7, closed=False,
                       seed=seed + 20 + k, wavelength=170.0)
        if k < 3:
            PA.hand_stroke(d, [(x0 + step * k * 0.5, yy),
                               (x0 + step * (k + 2) * 0.5,
                                yy + (base_y - top_y) / 4.0)], col, 5,
                           closed=False, seed=seed + 40 + k, wavelength=140.0)
    # planks on the top two lifts
    for k in (2, 3):
        yy = top_y + (base_y - top_y) * k / 4.0
        PA.fill_rect(img, [x0, yy - 4, x1, yy + 16], (172, 140, 96),
                     seed=seed + 60 + k, value=0.07)
        PA.hand_stroke(d, [(x0, yy + 16), (x1, yy + 16)], INK, 4, closed=False,
                       seed=seed + 70 + k, wavelength=170.0)


def _crane(d, cx, base_y, h, seed, jib=300, hook_x=None, col=STEEL_DK):
    """A tower crane: mast, slewing cab, jib, counter-jib, a hanging hook block."""
    img = PA.img_of(d)
    w = h * 0.075
    for s in (-1, 1):
        PA.hand_stroke(d, [(cx + s * w, base_y), (cx + s * w * 0.62, base_y - h)],
                       col, 7, closed=False, seed=seed + s, wavelength=140.0)
    for k in range(6):
        u0, u1 = k / 6.0, (k + 1) / 6.0
        y0, y1 = base_y - h * u0, base_y - h * u1
        wv0 = w * (1.0 - 0.38 * u0)
        wv1 = w * (1.0 - 0.38 * u1)
        PA.hand_stroke(d, [(cx - wv0, y0), (cx + wv1, y1)], col, 4,
                       closed=False, seed=seed + 10 + k, wavelength=90.0)
        PA.hand_stroke(d, [(cx + wv0, y0), (cx - wv1, y1)], col, 4,
                       closed=False, seed=seed + 20 + k, wavelength=90.0)
        PA.hand_stroke(d, [(cx - wv0, y0), (cx + wv0, y0)], col, 4,
                       closed=False, seed=seed + 30 + k, wavelength=60.0)
    top = base_y - h
    cab = [(cx - w * 1.5, top), (cx + w * 1.5, top), (cx + w * 1.5, top - 52),
           (cx - w * 1.5, top - 52)]
    PA.fill_poly(img, cab, (168, 172, 178), seed=seed + 40, value=0.07)
    PA.hand_stroke(d, cab, INK, 5, closed=True, seed=seed + 41, wavelength=80.0)
    PA.hand_stroke(d, [(cx - w * 0.4, top - 52), (cx - w * 0.4, top - 150)],
                   col, 6, closed=False, seed=seed + 42, wavelength=90.0)
    # the jib runs OFF the frame edge -- frame-fill, not a model on a table
    PA.hand_stroke(d, [(cx - w * 0.4, top - 140), (cx + jib, top - 122)], col, 8,
                   closed=False, seed=seed + 43, wavelength=170.0)
    PA.hand_stroke(d, [(cx - w * 0.4, top - 140), (cx - jib * 0.36, top - 150)],
                   col, 8, closed=False, seed=seed + 44, wavelength=140.0)
    for k in range(6):
        t = k / 5.0
        x = cx + jib * t
        PA.hand_stroke(d, [(x, top - 122 - 20 * t), (x, top - 66 - 14 * t)], col,
                       3, closed=False, seed=seed + 50 + k, wavelength=60.0)
    if hook_x is not None:
        PA.hand_stroke(d, [(hook_x, top - 128), (hook_x, top + 130)], INK, 4,
                       closed=False, seed=seed + 60, wavelength=140.0)
        blk = [(hook_x - 26, top + 130), (hook_x + 26, top + 130),
               (hook_x + 26, top + 186), (hook_x - 26, top + 186)]
        PA.fill_poly(img, blk, (64, 66, 74), seed=seed + 61, value=0.07)
        PA.hand_stroke(d, blk, INK, 5, closed=True, seed=seed + 62,
                       wavelength=70.0)


def _concrete_pour(d, cx, top_y, drop_y, spread, seed, col=(196, 194, 188)):
    """Concrete coming out of a chute: a thick falling ribbon that SPREADS into
    a fresh pour at the bottom, with rebar standing in it.

    STATUS: NOT USED by the current b13 card, which draws its pour explicitly
    (see `c_pour`) because this primitive's internal rebar grid read as
    cross-hatched wires over pale haze at the framing b13 wanted. Kept because
    it is a correct, reusable chute-and-pour primitive for any future beat that
    needs one at a wider framing.
    """
    img = PA.img_of(d)
    # the chute at the top, cropped by the frame edge
    ch = [(cx - 96, top_y - 60), (cx + 96, top_y - 60), (cx + 74, top_y),
          (cx - 74, top_y)]
    PA.fill_poly(img, ch, STEEL_DK, seed=seed, value=0.07)
    PA.hand_stroke(d, ch, INK, 6, closed=True, seed=seed + 1, wavelength=90.0)
    # the falling ribbon, narrowing as it leaves the chute then fanning out
    pts_l, pts_r = [], []
    n = 20
    for i in range(n + 1):
        t = i / float(n)
        y = top_y + (drop_y - top_y) * t
        wdt = 62 + t * spread * 1.7
        pts_l.append((cx - wdt * 0.5 - 10 * t, y))
        pts_r.append((cx + wdt * 0.5 + 10 * t, y))
    stream = pts_l + pts_r[::-1]
    PA.fill_poly(img, stream, col, seed=seed + 2, value=0.09)
    PA.hand_stroke(d, pts_l, INK, 5, closed=False, seed=seed + 3, wavelength=110.0)
    PA.hand_stroke(d, pts_r, INK, 5, closed=False, seed=seed + 4, wavelength=110.0)
    # the fresh pour at the bottom, running off both side edges
    pool = [(-40, drop_y + 40), (-40, drop_y - 30 + 26), (W + 40, drop_y - 46 + 26),
            (W + 40, drop_y + 40)]
    PA.fill_poly(img, pool, col, seed=seed + 5, value=0.09)
    PA.hand_stroke(d, [(-40, drop_y - 30 + 26), (300, drop_y - 34),
                       (760, drop_y - 52), (W + 40, drop_y - 46 + 26)], INK, 6,
                   closed=False, seed=seed + 6, wavelength=190.0)
    # rebar: a grid of thin rungs standing out of the pour
    for k in range(6):
        x = 120 + k * 210
        PA.hand_stroke(d, [(x, drop_y - 30), (x, drop_y - 168)], (96, 92, 88), 6,
                       closed=False, seed=seed + 20 + k, wavelength=90.0)
    for k in range(3):
        yy = drop_y - 60 - k * 52
        PA.hand_stroke(d, [(60, yy), (W - 60, yy - 12)], (96, 92, 88), 5,
                       closed=False, seed=seed + 40 + k, wavelength=140.0)


# ---------------------------------------------------------------------------
# b14-b16  the gothic arch hall -- the first hero
# ---------------------------------------------------------------------------

def _arch_hall(d, seed, bays=5, floor_y=690, vx=640, vy=430, lancets=0,
               col=GRANITE, shade=GRANITE_DK):
    """A vaulted gothic hall seen DOWN its length: nested pointed arches, each
    one the same profile scaled toward a vanishing point, opening onto a lit far
    wall.

    WHY IT IS NEAR-TO-FAR AND EACH FILL IS THE WHOLE ARCH SHAPE. Read down the
    length of a vault you see CONCENTRIC arches, not a row side by side, and the
    band of masonry between one arch and the next is the thickness of the wall.
    The cheapest honest way to draw that is to fill each arch's full silhouette,
    biggest first, in a stone value that gets LIGHTER and warmer toward the far
    end -- so each nearer arch's darker fill covers the ones behind it and the
    only thing left visible of each is the ring around the next. Every fill is
    ONE simple arch polygon, so nothing self-intersects.

    The nearest arch is scaled to 1.34, which puts its springing below the floor
    and its jambs past both side edges, so it is cropped by the frame on three
    sides: the frame is a piece of the hall, not a model of one in an empty field.

    Each arch is ONE closed outline from `_pointed` -- jamb up, two struck arcs
    meeting at a point, jamb down -- rather than a rectangle with an arc stroked
    on top, which is what leaves a notch at each shoulder.
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [-20, -20, W + 20, H + 20], shade, seed=seed, value=0.06)

    SPRING_OFF, HALF_W_OFF = 300.0, 350.0
    lit = (242, 230, 200)                          # the lit far wall

    def bay(sc):
        """`_pointed` scaled by `sc` about the vanishing point (vx, vy)."""
        raw = _pointed(0.0, SPRING_OFF, HALF_W_OFF * 2.0)
        return [(vx + x * sc, vy + y * sc) for x, y in raw]

    # NEAREST FIRST, and the value climbs from dark at the near end to lit at the
    # far end. That ordering is the whole trick: each smaller, lighter arch is
    # painted OVER the dark near one, so what survives of each is a bright ring
    # of masonry with a shadowed reveal inside it -- a colonnade marching away.
    # Draw them small-to-large instead and the last (largest) fill covers the lot
    # and you get a single arch in an empty field.
    scales = [1.10 - 0.20 * k for k in range(bays)]
    for b, sc in enumerate(scales):
        pts = bay(sc)
        t = b / float(max(1, len(scales) - 1))
        base = tuple(int(shade[i] + (lit[i] - shade[i]) * t) for i in range(3))
        PA.fill_poly(img, pts, base, seed=seed + 10 + b, value=0.08)
        PA.hand_stroke(d, pts, INK, max(4, int(4 + 5 * sc)), closed=True,
                       seed=seed + 40 + b, wavelength=150.0)
        # the dark reveal just inside each arch is what makes the ring read as
        # the thickness of a wall rather than as a drawn line
        void = [(vx + (x - vx) / 1.10, vy + (y - vy) / 1.10) for x, y in pts]
        PA.fill_poly(img, void, tuple(int(v * 0.42) for v in base),
                     seed=seed + 70 + b, value=0.07)

        if lancets and 0 < b < len(scales) - 1:
            # tall lit windows in the bay wall, seen through this bay's opening
            for j in range(lancets):
                lx = vx - 250 * sc + 500 * sc * (j + 0.5) / float(lancets)
                PA.fill_poly(img, _pointed(lx, vy + 300 * sc, 90 * sc),
                             (250, 232, 184), seed=seed + 110 + b * 7 + j,
                             value=0.06)
                PA.hand_stroke(d, _pointed(lx, vy + 300 * sc, 90 * sc), INK, 4,
                               closed=True, seed=seed + 140 + b * 7 + j,
                               wavelength=70.0)

    # the floor, cropped left and right, so the hall has a ground to stand on
    PA.fill_rect(img, [-30, floor_y, W + 30, H + 20], (128, 124, 118),
                 seed=seed + 200, value=0.08)
    PA.hand_stroke(d, [(-30, floor_y), (W + 30, floor_y - 6)], INK, 5,
                   closed=False, seed=seed + 201, wavelength=190.0)


def _pointed(cx, spring, w, n=20):
    """One closed EQUILATERAL gothic-arch outline: springings at
    `(cx -/+ w/2, spring)`, apex `0.866*w` above, drawn as two circular arcs of
    radius = the span, each struck from the OPPOSITE springing through 60deg.

    WHY THE RADIUS IS THE SPAN AND NOT A FREE `rise`. A two-centre arch only
    closes on the centre line when both arcs have radius equal to the span: the
    left arc, centred on the RIGHT springing, must pass through the LEFT
    springing, which is exactly `w` away. Any other radius makes the arc start
    somewhere other than the springing and PIL closes the gap with a straight
    chord -- which reads as a stray diagonal line across the opening. Fixing
    R = w makes the apex height a consequence (0.866*w) instead of a parameter,
    and guarantees the outline starts and ends exactly on the springings.

    Y IS DOWN IN IMAGE SPACE, so arcs are traced with `spring - R*sin(a)`; the
    left arc runs from 180deg to 120deg and the right from 0deg to 60deg.
    """
    left, right = cx - w / 2.0, cx + w / 2.0
    R = max(2.0, w)
    a60, a120 = math.radians(60.0), math.radians(120.0)

    def arc(ccx, a0, a1):
        return [(ccx + R * math.cos(a0 + (a1 - a0) * i / float(n)),
                 spring - R * math.sin(a0 + (a1 - a0) * i / float(n)))
                for i in range(n + 1)]

    left_pts = arc(right, math.pi, a120)            # left springing -> apex
    right_pts = arc(left, 0.0, a60)                 # right springing -> apex
    return ([(left, spring)] + left_pts + list(reversed(right_pts))
            + [(right, spring)])


# ---------------------------------------------------------------------------
# b22-b24  the wall in cross-section
# ---------------------------------------------------------------------------

def _wall_section(d, cx, cy, w, h, seed, layers=None, hatch=True):
    """The wall as a CUT: three layers edge to edge across the whole frame --
    a steel plate, a concrete core, another steel plate -- cropped left and
    right so the section IS the picture.

    `layers` is [(thickness_fraction, colour, caption)] running left to right.
    """
    img = PA.img_of(d)
    if layers is None:
        layers = [(0.14, STEEL, 'STEEL'), (0.58, (198, 196, 188), 'CONCRETE'),
                  (0.14, STEEL_DK, 'STEEL')]
    x = cx - w / 2.0
    band_h = h * 0.42
    for i, (frac, col, _lab) in enumerate(layers):
        bw = w * frac
        box = [(x, cy - band_h), (x + bw, cy - band_h), (x + bw, cy + band_h),
               (x, cy + band_h)]
        PA.fill_poly(img, box, col, seed=seed + i, value=0.08)
        PA.hand_stroke(d, box, INK, 6, closed=True, seed=seed + 10 + i,
                       wavelength=140.0)
        x += bw
    if hatch:
        # aggregate speckle in the concrete band and a rolled edge on the plate
        for k in range(28):
            u = (k * 97) % 100 / 100.0
            hx = cx - w * 0.30 + u * w * 0.60
            hy = cy - band_h + ((k * 61) % 100 / 100.0) * band_h * 2.0
            PA.hand_stroke(d, [(hx, hy), (hx + 16, hy + 6)], (168, 166, 158), 5,
                           closed=False, seed=seed + 60 + k, wavelength=50.0,
                           vary=0.2)
    return band_h


def _bolts(d, x0, y0, x1, y1, step, seed, r=13, col=STEEL_DK):
    """A line of bolt heads -- the fastest way to say 'steel plate over steel'."""
    img = PA.img_of(d)
    n = int(max(0, (x1 - x0)) / float(step))
    for i in range(n + 1):
        x = x0 + i * step
        for j, y in enumerate((y0, y1)):
            yy = y + (26 if j and abs(y1 - y0) < 4 else 0)
            PA.fill_poly(img, PA.ellipse_pts(x, yy, r, r, n=12), col,
                         seed=seed + i * 3 + j, value=0.05)
            PA.hand_stroke(d, PA.ellipse_pts(x, yy, r, r, n=14), INK,
                           max(2, int(r * 0.30)), closed=True,
                           seed=seed + 40 + i * 3 + j, wavelength=30.0)


def _hinge_column(d, x, cy, r, seed, blocks=3):
    """The hinge stack, drawn LARGE and cropped by the left edge: this is b21's
    whole subject, so it is not a detail beside the door."""
    img = PA.img_of(d)
    for k in range(blocks):
        yy = cy - r * 0.62 + k * r * 0.86
        bh = r * 0.72
        box = [(-90, yy - bh / 2), (x + r * 0.10, yy - bh / 2),
               (x + r * 0.10, yy + bh / 2), (-90, yy + bh / 2)]
        PA.fill_poly(img, box, STEEL_DK if k % 2 else STEEL, seed=seed + k,
                     value=0.07)
        PA.hand_stroke(d, box, INK, 7, closed=True, seed=seed + 10 + k,
                       wavelength=140.0)
        # the pin: a big horizontal cylinder through the middle of the block
        pin = [(x - r * 0.30, yy), (x + r * 0.30, yy),
               (x + r * 0.30, yy + bh * 0.30), (x - r * 0.30, yy + bh * 0.30)]
        PA.fill_poly(img, pin, (72, 76, 86), seed=seed + 20 + k, value=0.07)
        PA.hand_stroke(d, pin, INK, 5, closed=True, seed=seed + 30 + k,
                       wavelength=80.0)


# ---------------------------------------------------------------------------
# b26  the building in section, nine floors of gold
# ---------------------------------------------------------------------------

def _floors_section(d, cx, y0, y1, floors, seed, half_w=760, lit_from=1):
    """The building cut open on its left flank: `floors` storeys stacked inside,
    each carrying gold, cropped by the left and bottom edges.

    WHY THE CUT IS A WEDGE IN THE SKY COLOUR. A section is not a diagram BESIDE
    a building; it is a building with its side removed. So a tall wedge of sky
    colour runs off the left edge, the exposed cut face is a paler stone value,
    and every storey is a dark room opening onto that face -- which is what puts
    the gold INSIDE the masonry instead of floating beside it.
    """
    img = PA.img_of(d)
    cut_x = cx - half_w * 0.30
    face = [(cut_x - half_w * 0.80, y1 + 60), (cut_x, y1 + 60),
            (cut_x, y0 + (y1 - y0) * 0.30),
            (cut_x - half_w * 0.30, y0 + (y1 - y0) * 0.06),
            (cut_x - half_w * 0.80, y0 + (y1 - y0) * 0.44)]
    PA.fill_poly(img, face, (184, 180, 172), seed=seed, value=0.08)
    PA.hand_stroke(d, face, INK, 6, closed=True, seed=seed + 1, wavelength=150.0)

    fh = (y1 - y0) / float(floors)
    for i in range(floors):
        y = y0 + (y1 - y0) - (i + 1) * fh
        x0 = cut_x - half_w * 0.70 + i * 6
        x1 = cut_x + half_w * 0.04 - i * 4
        room = [(x0, y), (x1, y - fh * 0.14), (x1, y + fh * 0.70), (x0, y + fh * 0.86)]
        PA.fill_poly(img, room, (62, 60, 66), seed=seed + 20 + i, value=0.06)
        PA.hand_stroke(d, room, INK, 5, closed=True, seed=seed + 40 + i,
                       wavelength=90.0)
        # gold on the floor: three bars, growing smaller toward the back
        for k in range(4):
            t = k / 3.0
            bw = (x1 - x0) * 0.20
            bx = x0 + (x1 - x0) * 0.06 + t * (x1 - x0) * 0.72
            by = y + fh * 0.40 - t * fh * 0.05
            _gold_bar(d, bx, by, bw, fh * 0.20, seed + 60 + i * 7 + k)
        # the slab under the floor
        PA.hand_stroke(d, [(x0 - 8, y + fh * 0.90), (x1 + 8, y + fh * 0.74)],
                       (156, 154, 148), 7, closed=False, seed=seed + 80 + i,
                       wavelength=80.0)
    return face


# ---------------------------------------------------------------------------
# b31-b33  flags
# ---------------------------------------------------------------------------

def _flag_row(d, x0, x1, y, seed, n=5, h=54, pole=True):
    """A row of small national flags on short poles above a door -- our own
    generic tricolours, deliberately unreadable at small size."""
    img = PA.img_of(d)
    step = (x1 - x0) / float(max(1, n - 1))
    for i in range(n):
        x = x0 + i * step
        w = h * 1.52
        cols = ((198, 40, 44), (250, 248, 240), (52, 74, 150))
        cols = cols[i % 3:] + cols[:i % 3]
        if pole:
            PA.hand_stroke(d, [(x, y), (x, y - h * 1.34)], INK, 5, closed=False,
                           seed=seed + i, wavelength=60.0)
        for k, c in enumerate(cols):
            x0f = x + k * (w / 3.0)
            PA.fill_rect(img, [x0f, y - h * 1.24, x0f + w / 3.0, y - h * 0.24],
                         c, seed=seed + 20 + i * 4 + k, value=0.06)
        PA.hand_stroke(d, [(x, y - h * 1.24), (x + w, y - h * 1.24),
                           (x + w, y - h * 0.24), (x, y - h * 0.24)], INK, 4,
                       closed=True, seed=seed + 60 + i, wavelength=70.0)


# ---------------------------------------------------------------------------
# b36  the gold leaving
# ---------------------------------------------------------------------------

def _truck(d, cx, base_y, w, seed, col=(168, 76, 56)):
    """A box truck loaded with gold bars, cropped by whichever edge it needs.
    The bars spill ABOVE the box line so the load reads as too much to be shut
    in, which is the whole point of b36."""
    img = PA.img_of(d)
    h = w * 0.52
    box = [(cx - w / 2, base_y - h), (cx + w / 2, base_y - h),
           (cx + w / 2, base_y - h * 0.20), (cx - w / 2, base_y - h * 0.20)]
    cab = [(cx - w / 2, base_y - h * 0.20), (cx - w / 2 + w * 0.24, base_y - h * 0.20),
           (cx - w / 2 + w * 0.24, base_y - h * 0.74),
           (cx - w / 2, base_y - h * 0.74)]
    PA.fill_poly(img, box, col, seed=seed, value=0.07)
    PA.fill_poly(img, cab, (196, 88, 62), seed=seed + 1, value=0.07)
    PA.hand_stroke(d, box, INK, 6, closed=True, seed=seed + 2, wavelength=120.0)
    PA.hand_stroke(d, cab, INK, 6, closed=True, seed=seed + 3, wavelength=90.0)
    PA.hand_stroke(d, [(cx - w / 2, base_y - h * 0.74),
                       (cx - w / 2 + w * 0.15, base_y - h * 0.74)], INK, 6,
                   closed=False, seed=seed + 4, wavelength=70.0)
    # the load: bars stacked above the box's top edge
    _bar_wall(d, cx - w * 0.44, base_y - h - 132, cx + w * 0.44,
              base_y - h + 10, seed + 10, bw=int(w * 0.19), bh=int(h * 0.34),
              gap=5, stagger=True)
    PA.fill_rect(img, [cx - w * 0.52, base_y - h * 0.28, cx + w * 0.52,
                       base_y], (58, 56, 60), seed=seed + 60, value=0.06)
    for k, wx in enumerate((cx - w * 0.32, cx + w * 0.28)):
        PA.fill_poly(img, PA.ellipse_pts(wx, base_y, w * 0.115, w * 0.115, n=18),
                     (40, 38, 40), seed=seed + 70 + k, value=0.05)
        PA.hand_stroke(d, PA.ellipse_pts(wx, base_y, w * 0.115, w * 0.115, n=18),
                       INK, 5, closed=True, seed=seed + 80 + k, wavelength=40.0)


# ---------------------------------------------------------------------------
# b37-b42  the public side: counter, corridors, the deck above the gold
# ---------------------------------------------------------------------------

def _counter(d, x0, x1, base_y, h, seed):
    """A visitor counter: a wood-and-steel desk running off both edges, with a
    raised transaction shelf and the pass-through window behind it."""
    img = PA.img_of(d)
    front = [(x0, base_y), (x0, base_y - h), (x1, base_y - h), (x1, base_y)]
    PA.fill_poly(img, front, (150, 122, 86), seed=seed, value=0.08)
    PA.hand_stroke(d, front, INK, 6, closed=True, seed=seed + 1, wavelength=170.0)
    # the shelf: a lighter slab that overhangs, so it reads as a counter
    shelf = [(x0 - 40, base_y - h), (x1 + 40, base_y - h),
             (x1 + 40, base_y - h - 26), (x0 - 40, base_y - h - 26)]
    PA.fill_poly(img, shelf, (178, 150, 108), seed=seed + 2, value=0.07)
    PA.hand_stroke(d, shelf, INK, 5, closed=True, seed=seed + 3, wavelength=170.0)
    # the pass-through grille: vertical bars in a dark opening above the counter
    open_top = base_y - h - 26
    dark = [(x0, open_top - 300), (x1, open_top - 300), (x1, open_top),
            (x0, open_top)]
    PA.fill_poly(img, dark, (58, 60, 68), seed=seed + 4, value=0.06)
    n = int((x1 - x0) / 62)
    for i in range(n + 1):
        xx = x0 + i * 62
        PA.hand_stroke(d, [(xx, open_top - 296), (xx, open_top)], (108, 114, 126),
                       6, closed=False, seed=seed + 10 + i, wavelength=110.0)
    PA.hand_stroke(d, [(x0, open_top), (x1, open_top)], INK, 5, closed=False,
                   seed=seed + 60, wavelength=170.0)


def _corridor(d, vx, vy, seed, floor_y=690, w0=1180, wall=(198, 196, 188),
              ceil=(150, 148, 144), lit=(240, 226, 190), top_y=104):
    """A corridor in one-point perspective, its walls running off BOTH frame
    edges so the frame admits the building continues past the picture.

    WHY EVERY LINE CONVERGES ON ONE VANISHING POINT. A corridor drawn with
    parallel walls reads as a corridor-shaped box; it is the single vanishing
    point that reads as depth.

    WHY top_y IS 104 AND NOT -60. The near end of both walls used to start at
    y=-60 so they ran off the top edge. The walls converge on the vanishing
    point at (vx, vy-110), which is well BELOW the band, so the near-vertical
    outer edge sits at x=+790 for the full frame height and the converging inner
    edge sweeps in from 790 to 544 -- both of them cross y 14..68, where
    engine3 stamps "Fort Knox". Clamping the near end to 104 leaves the flat
    `wall` fill above it (the corridor simply continues past the top of frame,
    which is what a corridor does) and every drawn stroke now starts below the
    band. The walls still run off BOTH side edges at x=+/-790, so the perspective
    and the sense of a building larger than the picture are untouched.
    """
    img = PA.img_of(d)
    PA.fill_rect(img, [-20, -20, W + 20, H + 20], wall, seed=seed, value=0.06)
    # the far end: a lit opening
    far = [(vx - 96, vy - 110), (vx + 96, vy - 110), (vx + 96, vy + 116),
           (vx - 96, vy + 116)]
    PA.fill_poly(img, far, lit, seed=seed + 1, value=0.06)
    PA.hand_stroke(d, far, INK, 5, closed=True, seed=seed + 2, wavelength=110.0)
    # converging walls
    for s in (-1, 1):
        x = s * (w0 / 2.0 + 40)
        poly = [(x, top_y), (vx + s * 96, vy - 110), (vx + s * 96, vy + 116),
                (x, H + 60)]
        PA.fill_poly(img, poly, ceil if s > 0 else wall, seed=seed + 3 + s,
                     value=0.07)
        PA.hand_stroke(d, [(x, top_y), (vx + s * 96, vy - 110),
                           (vx + s * 96, vy + 116), (x, H + 60)], INK, 6,
                       closed=True, seed=seed + 5 + s, wavelength=180.0)
    # the floor
    PA.fill_poly(img, [(-60, H + 40), (vx - 96, vy + 116), (vx + 96, vy + 116),
                       (W + 60, H + 40)], (168, 166, 158), seed=seed + 7,
                 value=0.07)
    PA.hand_stroke(d, [(vx - 96, vy + 116), (vx + 96, vy + 116)], INK, 5,
                   closed=False, seed=seed + 8, wavelength=100.0)
    # a ceiling strip light running to the vanishing point -- the depth cue
    PA.hand_stroke(d, [(vx - 40, vy - 96), (vx - 190, top_y)], (238, 226, 196), 10,
                   closed=False, seed=seed + 9, wavelength=140.0)
    PA.hand_stroke(d, [(vx + 40, vy - 96), (vx + 190, top_y)], (238, 226, 196), 10,
                   closed=False, seed=seed + 10, wavelength=140.0)
    return far


def _deck_section(d, seed, deck_y=470, cx=640, half=780, sealed=False):
    """The public corridor DECK carried on a slab directly over the gold storey:
    a row of small figures walking on top, the bar field visible in the storey
    below, and (when `sealed`) a red-bolted line on the lower level.

    This is the one diagram the chapter builds toward, so it is drawn ONCE at
    full width with both halves cropped, and b41/b42 differ only in whether the
    lower storey is lit and open or barred.
    """
    img = PA.img_of(d)
    # the upper storey: a lit corridor slab
    upper = [(cx - half, deck_y - 300), (cx + half, deck_y - 300),
             (cx + half, deck_y - 20), (cx - half, deck_y - 20)]
    PA.fill_poly(img, upper, (188, 184, 176), seed=seed, value=0.07)
    PA.hand_stroke(d, [(cx - half, deck_y - 300), (cx + half, deck_y - 300),
                       (cx + half, deck_y - 20), (cx - half, deck_y - 20)], INK,
                   6, closed=True, seed=seed + 1, wavelength=190.0)
    for k in range(7):
        x = cx - half + 60 + k * (half * 2 - 120) / 6.0
        PA.hand_stroke(d, [(x, deck_y - 290), (x, deck_y - 26)], (168, 166, 158),
                       5, closed=False, seed=seed + 10 + k, wavelength=110.0)
    # the slab: the whole point of the picture, so it is HEAVY
    slab = [(cx - half, deck_y - 20), (cx + half, deck_y - 20),
            (cx + half, deck_y + 56), (cx - half, deck_y + 56)]
    PA.fill_poly(img, slab, (140, 138, 132), seed=seed + 30, value=0.08)
    PA.hand_stroke(d, slab, INK, 8, closed=True, seed=seed + 31, wavelength=190.0)
    # the storey below
    below = [(cx - half, deck_y + 56), (cx + half, deck_y + 56),
             (cx + half, H + 40), (cx - half, H + 40)]
    if sealed:
        PA.fill_poly(img, below, (56, 54, 60), seed=seed + 40, value=0.07)
        # the bolted line: thick steel bars across the whole opening
        for k in range(9):
            x = cx - half + 20 + k * (half * 2 - 40) / 8.0
            PA.hand_stroke(d, [(x, deck_y + 62), (x, H + 40)], (96, 100, 112), 16,
                           closed=False, seed=seed + 50 + k, wavelength=150.0)
        PA.hand_stroke(d, [(cx - half, deck_y + 62), (cx + half, deck_y + 62)],
                       RED, 8, closed=False, seed=seed + 70, wavelength=190.0)
    else:
        PA.fill_poly(img, below, (58, 52, 46), seed=seed + 40, value=0.07)
        _bar_wall(d, cx - half + 10, deck_y + 66, cx + half - 10, H + 30,
                  seed + 45, bw=112, bh=40, gap=5, stagger=True)
    return slab


# ---------------------------------------------------------------------------
# b43  the bolted inner door
# ---------------------------------------------------------------------------

def _inner_door(d, cx, cy, w, h, seed, bolt=6):
    """The innermost door: a flat steel slab in a thick frame, barred by heavy
    horizontal bolt bars driven across it, cropped by the frame.

    NO WHEEL HERE ON PURPOSE. The main door's wheel (b18-b20) is the thing that
    says "this can be opened". The inner door has no mechanism at all -- it is
    barred -- so giving it one would argue against the line.
    """
    img = PA.img_of(d)
    frame = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    PA.fill_poly(img, frame, (108, 106, 104), seed=seed, value=0.08)
    PA.hand_stroke(d, frame, INK, 9, closed=True, seed=seed + 1, wavelength=190.0)
    slab = [(cx - w * 0.40, cy - h * 0.42), (cx + w * 0.40, cy - h * 0.42),
            (cx + w * 0.40, cy + h * 0.42), (cx - w * 0.40, cy + h * 0.42)]
    PA.fill_poly(img, slab, STEEL_DK, seed=seed + 2, value=0.08)
    PA.hand_stroke(d, slab, INK, 7, closed=True, seed=seed + 3, wavelength=150.0)
    # the bolt bars, each with a heavy collar at its end
    for k in range(bolt):
        yy = cy - h * 0.34 + k * h * 0.68 / max(1, bolt - 1)
        PA.hand_stroke(d, [(cx - w * 0.60, yy), (cx + w * 0.60, yy)], (66, 68, 78),
                       22, closed=False, seed=seed + 20 + k, wavelength=150.0)
        for s in (-1, 1):
            col = [(cx + s * w * 0.46, yy - h * 0.075),
                   (cx + s * w * 0.60, yy - h * 0.055),
                   (cx + s * w * 0.60, yy + h * 0.055),
                   (cx + s * w * 0.46, yy + h * 0.075)]
            PA.fill_poly(img, col, (44, 46, 54), seed=seed + 40 + k * 2 + s,
                         value=0.06)
            PA.hand_stroke(d, col, INK, 5, closed=True,
                           seed=seed + 60 + k * 2 + s, wavelength=60.0)
    # a hard cold light from above, so the steel has a highlight to catch
    beam = [(cx - 150, cy - h * 0.62), (cx + 130, cy - h * 0.62),
            (cx + 300, cy - h * 0.16), (cx - 320, cy - h * 0.16)]
    PA.fill_poly(img, beam, (86, 92, 106), seed=seed + 90, value=0.05)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build():
    """44 cards for 44 beats, one idea each, snap-cut between.

    CAPTION COLOUR IS CHOSEN PER CARD, NOT PER CHAPTER. `SC.caption` gives INK
    captions a paper keyline and coloured ones a dark keyline. Over the gold that
    is a 50/50 call: a yellow highlighter on a gold bar with a dark keyline is
    muddy, while black-with-paper-keyline is the one combination that survives
    any background in this chapter. So every caption that lands on gold or on
    granite is INK, and colour is spent on the beats where the argument turns --
    the undercut (b09), the door (b17, b19), the empty floor (b34), the outbound
    truck (b36), the sealed deck (b42), the last line (b44).
    """
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def card(i, j, draw, kind='subject', seed=0, motion=None):
        """A complete card: paints its own background, live over beats i..j-1.

        The last card points past the final beat, so its `until` is the segment
        duration -- asking BeatClock for a beat that does not exist raises.
        """
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        return E3.E('card%02d' % i, kind, draw, at=T(i), until=end,
                    motion=motion)

    def cap(i, cx, cy, **kw):
        """Phrase-timed caption. beats.json gives all 44 beats exactly one
        phrase, so every card carries one caption and `until` hands off to the
        next beat cleanly -- captions can never pile up (invariant 1)."""
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ===== b01-b03  the hook: the building, the name, nobody inside ======== #
    # b01 FRAME-FILL: the facade runs off BOTH side edges and the hills run off
    # both edges too, so the frame is a piece of the building rather than a model
    # of it. The character stands at 330px with his feet at y=770 -- BELOW the
    # frame bottom -- which is what makes the wall read as taller than the picture.
    def c_exterior(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 1)
        _facade(d, -70, 1350, 600, 290, 2)
        SC.fullbody(d, 300, 770, 330, pose='pointing', expression='awed', seed=3)
    els.append(card(1, 2, c_exterior, kind='character'))
    els.append(cap(1, 880, 200, size=34))

    # b02 the name is known: a close-up cropped hard, with the thought in a
    # bubble as well as a caption -- the narrator says it AND he says it.
    def c_known(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pale(tile, 6, (222, 218, 210))
        SC.closeup(d, 400, 400, 225, 'skeptic', 7)
        D.draw_bubble(tile, 'everyone knows it', xy=(760, 150),
                      tail_to=(640, 300), font_size=32, max_w=400)
    els.append(card(2, 3, c_known, kind='character'))
    els.append(cap(2, 900, 656, size=32))

    # b03 nobody has been inside: a chained bar gate cropped top and right, and
    # the character at 480px shrugging in the open left third -- the only thing
    # in the frame that is not a bar.
    def c_gate(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (192, 198, 204), seed=8, value=0.05)
        PA.fill_rect(tile, [0, 470, W, H], (166, 172, 180), seed=9, value=0.06)
        PA.paper_overlay(tile, seed=10)
        for k in range(11):
            x = 460 + k * 96
            # TOP AT 110, NOT -20. The bars used to run off the top edge. That
            # obeys the frame-fill rule but ignores the one band that is not
            # ours: engine3 stamps "Fort Knox" over y 14..68 AFTER every element,
            # so bars through there left the title black-on-slate. The gate still
            # runs off BOTH side edges (x 460..1420 on a 1280 frame), which is
            # what actually sells the scale, and 590px of bar still owns the
            # frame. Caught by _coverage_gate.band_intrusions().
            PA.hand_stroke(d, [(x, 110), (x, 700)], (74, 80, 88), 15,
                           closed=False, seed=11 + k, wavelength=150.0)
        for yy, sd in ((196, 30), (580, 31)):
            PA.hand_stroke(d, [(420, yy), (W + 40, yy)], (74, 80, 88), 17,
                           closed=False, seed=sd, wavelength=160.0)
        # one run of alternating links so the chain actually interlocks
        for k in range(10):
            t = k / 9.0
            lx = 480 + t * 330
            ly = 250 + t * 250
            PA.hand_stroke(d, PA.ellipse_pts(lx, ly, 27, 15, n=20),
                           (58, 62, 70), 7, closed=True, seed=40 + k,
                           wavelength=40.0)
        SC.fullbody(d, 250, 700, 480, pose='shrug', expression='confused',
                    seed=12)
    els.append(card(3, 4, c_gate, kind='character'))
    els.append(cap(3, 250, 170, size=32))

    # ===== b04-b05  the gold: other nations, not only America ============= #
    # b04 HERO: ranks of bars receding to a back wall, cropped left and right,
    # so the field is bigger than the frame.
    def c_goldhall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 13)
    els.append(card(4, 5, c_goldhall))
    els.append(cap(4, W // 2, 620, size=34))

    def c_flags_gold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 17)
        # Flags only along the NEAR rank. A flag on every bar is noise; a row
        # along the front says "these are labelled" without repainting the hall.
        for k, (fx, cols) in enumerate((
                (80, [(52, 74, 150), (250, 250, 248), (198, 40, 44)]),
                (280, [(198, 40, 44), (250, 250, 248)]),
                (480, [(198, 40, 44), (250, 250, 248), (52, 74, 150)]),
                (680, [(250, 250, 248), (52, 74, 150), (198, 40, 44)]))):
            _flag(d, fx, 486 - (k % 2) * 26, 70, 90 + k * 7, cols=cols)
        SC.fullbody(d, 1090, 700, 400, pose='pointing', expression='neutral',
                    seed=22)
    els.append(card(5, 6, c_flags_gold, kind='character'))
    els.append(cap(5, W // 2, 620, size=34))

    # ===== b06  Kentucky: the map, cropped, one dot ======================= #
    # LABEL PLACEMENT IS THE WHOLE PROBLEM HERE. The state is drawn HIGH and
    # cropped by the left edge so the whole lower third is clear for the caption,
    # and the state name goes top-left in the one corner the polygon misses.
    def c_map(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pale(tile, 24, (214, 224, 212))
        # cy 448, not 288. The state's own top vertex sits at cy - 0.5*s, so at
        # 288 the whole northern third of Kentucky ran off the top edge and its
        # INK outline (line 508) cut straight through "Fort Knox". 448 puts that
        # vertex at 118 -- clear of the band -- while the state's southern tip
        # drops to ~765 and is cropped by the BOTTOM edge, which keeps the map
        # the dominant object instead of shrinking it.
        _kentucky(d, 470, 448, 660, 25)
        dx, dy = 470 + 0.16 * 660, 448 - 0.10 * 660      # north-central hills
        d.ellipse([dx - 18, dy - 18, dx + 18, dy + 18], fill=RED)
        PA.hand_stroke(d, [(dx, dy + 24), (dx, dy + 70)], RED, 6, seed=26,
                       wavelength=70.0)
        D.draw_label(tile, 'Fort Knox', center=(880, 200), color=TY.LABEL_RED,
                     size=34)
        PA.hand_stroke(d, [(846, 232), (dx + 28, dy + 42)], RED, 4, seed=27,
                       wavelength=110.0)
        D.draw_label(tile, 'KENTUCKY', center=(230, 168), color=TY.LABEL_INK,
                     size=54)
    els.append(card(6, 7, c_map))
    els.append(cap(6, W // 2, 656, size=34))

    # ===== b07-b09  the building, and the school that it is not =========== #
    def c_building(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 28)
        _facade(d, -70, 1350, 640, 320, 29)
        D.draw_label(tile, 'brick, a long low box', center=(640, 180),
                     color=TY.LABEL_INK, size=34)
    els.append(card(7, 8, c_building))
    els.append(cap(7, W // 2, 688, size=32))

    # THE SAME _facade() WITH windows=8 -- provably the same building as b07,
    # which is the entire point the narration is making.
    def c_school(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 31)
        _facade(d, -70, 1350, 620, 350, 32, windows=8)
        tw = [(1040, 300), (1040, 150), (1110, 150), (1110, 300)]
        PA.fill_poly(tile, tw, BRICK_DK, seed=33, value=0.07)
        PA.hand_stroke(d, tw, INK, 6, closed=True, seed=34, wavelength=110.0)
        cone = [(1020, 150), (1075, 84), (1130, 150)]
        PA.fill_poly(tile, cone, ROOF, seed=35, value=0.07)
        PA.hand_stroke(d, cone, INK, 5, closed=True, seed=36, wavelength=90.0)
        SC.fullbody(d, 620, 660, 260, pose='standing', expression='neutral',
                    seed=37)
    els.append(card(8, 9, c_school, kind='character'))
    els.append(cap(8, 640, 688, size=32))

    # b09 THE UNDERCUT. Same box, same hills, same horizon -- but steel: a
    # riveted plate and a round door at the LEFT edge, cropped, with a red cross
    # struck through the school reading.
    def c_notschool(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 38)
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
        _vault_door(d, 110, 470, 200, 44, hinge=True, wheel=True, rings=2,
                    bolts=12)
        D.draw_red_x(tile, [660, 300, 1060, 560])
        SC.fullbody(d, 300, 660, 250, pose='standing', expression='deadpan',
                    seed=45)
    els.append(card(9, 10, c_notschool, kind='character'))
    els.append(cap(9, 640, 688, size=32, fill=TY.LABEL_RED))

    # ===== b10  TITLE: FORT KNOX stamped across a gold bar ================ #
    # The bar is 1420px wide on a 1280 frame and 210 tall, cropped by BOTH side
    # edges and sitting across the lower third, so the title sits ON the subject
    # rather than beside it.
    #
    # ONLY "KENTUCKY" IS STAMPED HERE, NOT "FORT KNOX". engine3 draws the
    # chapter title "Fort Knox" across the top of EVERY frame in this chapter,
    # and the caption is the spoken line "This is Fort Knox, Kentucky." Stamping
    # "FORT KNOX" a third time put the place name on screen four times over. The
    # hero word here is the half of the name the engine title does not already
    # carry, so the card reads as a reveal rather than a stutter.
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pale(tile, 46, (222, 216, 206))
        _gold_bar(d, -70, 500, 1420, 210, 48, top=(252, 226, 150), face=GOLD)
        D.draw_label(tile, 'KENTUCKY', center=(640, 605), color=TY.LABEL_INK,
                     size=118)
    els.append(card(10, 11, c_title))
    els.append(cap(10, W // 2, 178, size=44))

    # ===== b11-b13  1939-1944: five years of concrete and stone ========== #
    # b11 WORK BEGAN. The shell, no skin, filling the frame width, with the
    # crane's jib running OFF the right edge so the site is bigger than the
    # picture. The 1939 stamp sits in the one clear patch of sky.
    def c_1939(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 52, sky=(196, 208, 220))
        _scaffold(d, -60, 620, 600, 300, 53, bays=5)
        _shell(d, 560, 1400, 600, 330, 54, floors=4, roofed=True)
        # h 330, not 470. _crane hangs its jib 140px ABOVE the mast top and its
        # tie-lines hang off the jib, so at h=470 the jib sat at y=-10 and the
        # ties ran through y 0..58 -- straight across "Fort Knox". The jib still
        # runs off the right edge at 760 long, which is what makes the crane read
        # as bigger than the frame; only its height came down.
        _crane(d, 300, 600, 330, 55, jib=760, hook_x=980)
        D.draw_label(tile, '1939', center=(210, 176), color=TY.LABEL_INK,
                     size=86)
    els.append(card(11, 12, c_1939))
    els.append(cap(11, 900, 690, size=32))

    # b12 FINISHED 1944: the same shell, but clad and roofed and pushed RIGHT,
    # with the old scaffold still standing on the left -- same building, five
    # years on, which is the only way "finished in 1944" reads as a fact.
    def c_1944(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 56)
        _facade(d, 520, 1420, 610, 350, 57, windows=7)
        _scaffold(d, -60, 430, 610, 330, 58, bays=3)
        D.draw_label(tile, '1944', center=(200, 176), color=TY.LABEL_INK,
                     size=86)
    els.append(card(12, 13, c_1944))
    els.append(cap(12, 900, 690, size=32))

    # b13 FIVE YEARS OF POURED CONCRETE. Drawn explicitly rather than through
    # `_concrete_pour`: that primitive draws its own internal rebar grid AND a
    # thin translucent ribbon, and at this framing the two together read as
    # cross-hatched wires over a pale haze instead of a mass of wet concrete.
    # Here the chute hangs cropped by the TOP edge, a FAT solid column falls
    # from it, and it lands in a DARK pour mass that fills the whole bottom
    # band and runs off the left, right and bottom edges. The mass is the
    # subject -- "five years" of it -- so it is the darkest thing in frame.
    # The character stands ON the pour, feet at the crest, watching it.
    def c_pour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (200, 202, 208), seed=61, value=0.07)
        # the pour mass: fills the bottom ~300px and every side edge
        crest = [(-40, 430), (240, 402), (620, 424), (940, 452), (W + 40, 436),
                 (W + 40, H + 40), (-40, H + 40)]
        PA.fill_poly(tile, crest, (112, 108, 106), seed=62, value=0.04)
        PA.hand_stroke(d, [(-40, 430), (240, 402), (620, 424), (940, 452),
                           (W + 40, 436)], (26, 24, 26), 9, closed=False,
                       seed=63, wavelength=170.0)
        # the chute, cropped by the TOP edge
        ch = [(200, -20), (452, -20), (416, 96), (236, 96)]
        PA.fill_poly(tile, ch, STEEL_DK, seed=64, value=0.06)
        PA.hand_stroke(d, ch, INK, 8, closed=True, seed=65, wavelength=90.0)
        # the falling column: fat, solid, narrowing slightly then flaring into
        # the pour. Drawn edge to edge so it cannot read as a thin wire.
        col = [(250, 96), (404, 96), (430, 260), (452, 430), (196, 430),
               (216, 260)]
        PA.fill_poly(tile, col, (150, 146, 142), seed=66, value=0.06)
        PA.hand_stroke(d, [(250, 96), (216, 260), (196, 430)], (26, 24, 26), 8,
                       closed=False, seed=67, wavelength=90.0)
        PA.hand_stroke(d, [(404, 96), (430, 260), (452, 430)], (26, 24, 26), 8,
                       closed=False, seed=68, wavelength=90.0)
        # a couple of aggregate flecks in the column so it reads as material
        for k in range(14):
            fx = 240 + (k * 61) % 170
            fy = 130 + (k * 97) % 280
            PA.fill_poly(tile, [(fx, fy), (fx + 13, fy + 4), (fx + 6, fy + 15)],
                         (86, 82, 80), seed=70 + k, value=0.0)
        # the character standing ON the pour crest, watching it
        SC.fullbody(d, 1000, 448, 400, pose='pointing', expression='deadpan',
                    seed=91)
    els.append(card(13, 14, c_pour, kind='character'))
    els.append(cap(13, 300, 664, size=32))

    # ===== b14-b16  THE GOTHIC HALL (hero #1) ============================ #
    # Three consecutive beats, so they must NOT be three repetitions of one
    # image. Each gets a different argument:
    #   b14 the HALL ITSELF, down its length -- the roof form, nothing else.
    #   b15 an ARCADE OVER A CORRIDOR -- the arches read as a ceiling you walk
    #        under, with figures on the floor for the scale the words imply.
    #   b16 the hall again, lancets lit and the punchline stamped over it.
    def c_archhall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arch_hall(d, 71, bays=5, floor_y=700, lancets=0)
    els.append(card(14, 15, c_archhall))
    els.append(cap(14, W // 2, 118, size=34))

    # b15 VAULTED ARCHES OVER THE CORRIDORS. A full-width arcade: four gothic
    # arches springing off piers, the nearest cropped by BOTH side edges so the
    # vault runs past the frame, and a lit walkway with three small figures
    # running under it. The figures are 190px -- deliberately small, because
    # "vaulted" only means anything next to something to be vaulted OVER.
    def c_ribs(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (150, 146, 138), seed=81, value=0.07)
        # the far corridor wall, seen through the arcade: brighter, so each
        # opening reads as a hole punched through to a lit space beyond
        PA.fill_rect(tile, [0, 300, W, 600], (206, 200, 188), seed=82, value=0.08)
        PA.hand_stroke(d, [(0, 600), (W, 600)], INK, 6, closed=False,
                       seed=83, wavelength=220.0)

        # piers first, so every arch head lands ON a pier rather than beside it
        for i, px in enumerate((-150.0, 210.0, 570.0, 930.0, 1290.0)):
            PA.fill_rect(tile, [px - 78, 168, px + 78, 600], GRANITE,
                         seed=84 + i, value=0.07)
            PA.hand_stroke(d, [(px - 78, 168), (px - 78, 600)], INK, 7,
                           closed=False, seed=94 + i, wavelength=150.0)
            PA.hand_stroke(d, [(px + 78, 168), (px + 78, 600)], INK, 7,
                           closed=False, seed=104 + i, wavelength=150.0)

        # springing line and the arcade of pointed heads above it
        PA.hand_stroke(d, [(-150, 430), (1290, 430)], INK, 6, closed=False,
                       seed=114, wavelength=200.0)
        for i, ax in enumerate((30.0, 390.0, 750.0, 1110.0)):
            PA.fill_poly(tile, _pointed(ax, 430, 300), (176, 172, 162),
                         seed=124 + i, value=0.07)
            PA.hand_stroke(d, _pointed(ax, 430, 300), INK, 7, closed=True,
                           seed=134 + i, wavelength=170.0)
            # the dark reveal inside each head, so the ring reads as wall
            # thickness rather than as a drawn line
            PA.fill_poly(tile, _pointed(ax, 424, 216), (104, 100, 96),
                         seed=144 + i, value=0.07)
            PA.hand_stroke(d, _pointed(ax, 424, 216), (58, 56, 54), 5,
                           closed=True, seed=154 + i, wavelength=110.0)

        # walkway: a bright band under the arcade, cropped by both edges
        PA.fill_rect(tile, [-40, 600, W + 40, H + 20], (186, 180, 168),
                     seed=164, value=0.08)
        for i, fx in enumerate((360.0, 640.0, 900.0)):
            _person(d, fx, 672, 190, 170 + i, arms=True, facing=1 if i % 2 else -1)
    els.append(card(15, 16, c_ribs))
    els.append(cap(15, W // 2, 128, size=34))

    def c_europe(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arch_hall(d, 91, bays=4, floor_y=700, vy=430, lancets=4)
        D.draw_label(tile, 'EUROPE, IN KENTUCKY', center=(640, 122),
                     color=TY.LABEL_INK, size=44)
    els.append(card(16, 17, c_europe))
    els.append(cap(16, W // 2, 690, size=32))

    # ===== b17-b25  THE VAULT DOOR (hero #2) ============================ #
    # b17 the doors mattered more than the roof: the roofline is squeezed to a
    # 78px band across the top and the door takes everything under it.
    def c_door_vs_roof(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 101)
        _facade(d, -70, 1350, 690, 78, 102, roof_h=26, courses=False)
        _vault_door(d, 640, 470, 290, 103, hinge=True, wheel=True, rings=3,
                    bolts=16)
    els.append(card(17, 18, c_door_vs_roof))
    els.append(cap(17, W // 2, 668, size=34, fill=TY.LABEL_RED))

    # b18 56 TONS. r=470 on a 720-tall frame, so the door is cropped top AND
    # bottom -- the mass IS the argument, and the number goes in the sky, which
    # is the only place left where it will not fight the steel.
    def c_56tons(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 111, grass=(120, 132, 108))
        # cy 580 = r + 110, not 430. The door's OUTER RIM keyline is drawn last
        # and darkest, so it is the stroke that crossed the title: at cy=430 the
        # disc's apex was y=-40 and the rim, the k=0 ring (at cy-0.84r) and the
        # bolt circle (at cy-0.913r) all landed inside y 14..68. Parking the apex
        # at exactly 110 puts the entire door -- rim, rings, bolts, wheel -- below
        # the band. r is untouched at 470, so the door is still 940px across and
        # cropped by the left, right and bottom edges: the mass is still the
        # argument, which is what this beat is for.
        _vault_door(d, 620, 580, 470, 112, hinge=True, wheel=True, rings=3,
                    bolts=22)
        D.draw_label(tile, '56 TONS', center=(960, 150), color=TY.LABEL_INK,
                     size=78)
    els.append(card(18, 19, c_56tons))
    els.append(cap(18, 300, 664, size=34))

    # b19 the heaviest made: the same cropped door with a CAR parked at its base
    # for the scale the words are actually making.
    def c_heaviest(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 121, grass=(118, 130, 106))
        # cy 560 = r + 110. Same reason as b18: the rim keyline is the stroke that
        # struck the title, and parking the apex at 110 drops rim, rings and bolts
        # clear of the band. The car stays at the door's base for scale.
        _vault_door(d, 740, 560, 450, 122, hinge=True, wheel=True, rings=3,
                    bolts=22)
        _car(d, 290, 706, 210, 123)
        D.draw_label(tile, 'HEAVIEST MADE', center=(280, 240),
                     color=TY.LABEL_RED, size=42)
    els.append(card(19, 20, c_heaviest, kind='character'))
    els.append(cap(19, 700, 690, size=32, fill=TY.LABEL_RED))

    # b20 HERO: a round steel face, cropped by the frame. r=760 on 1280x720 puts
    # the circle past all four edges, so no part of its outline is visible --
    # which is exactly what the line says.
    def c_roundface(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 131, grass=(112, 124, 100))
        # cy 870 = r + 110, not 360. This card's whole point is that the circle
        # is past all four edges so no outline is visible -- but at cy=360 the
        # disc's apex was y=-400 and the rings/bolt circle/wheel were stacked
        # right through the title band. Dropping the apex to 110 keeps every ring
        # arc below the band; the disc is still 1520px across on a 1280 frame and
        # still cropped left, right and bottom, so the read is unchanged.
        _vault_door(d, 640, 870, 760, 132, hinge=True, wheel=True, rings=4,
                    bolts=30)
    els.append(card(20, 21, c_roundface))
    els.append(cap(20, 640, 660, size=36))

    # b21 the hinge: the hinge column is the subject and is cropped hard by the
    # left edge, with only the door's right shoulder visible past it.
    def c_hinge(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 141, grass=(116, 128, 102))
        _hinge_column(d, 250, 380, 300, 142, blocks=3)
        ring = PA.ellipse_pts(560, 380, 470, 470, n=72)
        PA.fill_poly(tile, ring, STEEL, seed=143, value=0.08)
        PA.hand_stroke(d, ring, INK, 10, closed=True, seed=144, wavelength=190.0)
    els.append(card(21, 22, c_hinge))
    els.append(cap(21, 900, 690, size=32))

    # b22 steel / concrete / steel: the cut, three layers edge to edge across the
    # WHOLE frame, cropped left and right so the wall runs past the picture. DARK
    # register on purpose -- the pale version of this card read as three pale
    # rectangles floating in a white field, with no mass anywhere. The layers are
    # steel-dark / concrete / steel-dark against a near-black ground, the labels
    # reversed out in the light ink so nothing sits on a competing value, and the
    # bolts marching across the concrete say "plate" without a legend.
    def c_layers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (36, 34, 38), seed=151, value=0.05)
        SC.title_backdrop(tile, 1151, col=TITLE_COURSE)
        # DARK layers passed explicitly. The primitive's built-in defaults are
        # LIGHT (a 198 concrete core between two pale steels) and on a dark
        # ground they read as three bright panels rather than a wall in section.
        _wall_section(d, 640, 350, 1440, 470, 153,
                      layers=[(0.16, (96, 100, 110), 'STEEL'),
                              (0.52, (74, 71, 68), 'CONCRETE'),
                              (0.16, (72, 76, 86), 'STEEL')])
        _bolts(d, 40, 190, 1240, 520, 150, seed=154, r=16, col=(38, 40, 46))
        D.draw_label(tile, 'STEEL', center=(120, 626), color=PAPERW, size=44)
        D.draw_label(tile, 'CONCRETE', center=(660, 626), color=PAPERW, size=44)
        D.draw_label(tile, 'STEEL', center=(1180, 626), color=PAPERW, size=44)
    els.append(card(22, 23, c_layers))
    els.append(cap(22, W // 2, 690, size=32, fill=TY.LABEL_YELLOW))

    # b23 the concrete runs RIGHT THROUGH: one continuous aggregate-speckled mass
    # filling the frame between two steel skins at the top and bottom. Dark, so
    # the concrete reads as a solid block the steel is only skinned onto.
    def c_throughwall(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (30, 29, 32), seed=161, value=0.05)
        SC.title_backdrop(tile, 1161, col=TITLE_COURSE)
        core = [(-40, 170), (W + 40, 170), (W + 40, 610), (-40, 610)]
        PA.fill_poly(tile, core, (128, 124, 118), seed=163, value=0.07)
        # aggregate: the flecks are light on the dark mass, so "concrete" is
        # legible as material without a single label
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
        # steel skins top and bottom, running off both sides
        for yy in (170, 610):
            PA.fill_rect(tile, [-40, yy - 34, W + 40, yy], STEEL, seed=220,
                         value=0.08)
            PA.hand_stroke(d, [(-40, yy - 34), (W + 40, yy - 34)], INK, 8,
                           closed=False, seed=221, wavelength=190.0)
            PA.hand_stroke(d, [(-40, yy), (W + 40, yy)], INK, 8, closed=False,
                           seed=222, wavelength=190.0)
    els.append(card(23, 24, c_throughwall))
    els.append(cap(23, W // 2, 400, size=36, max_w=820, fill=TY.LABEL_YELLOW))

    # b24 the walls are thicker than the doors: a THICK wall block cropped by the
    # left and top edges, and a door slab beside it that is visibly the smaller
    # mass. The character stands on the slab at 250px, shrugging at the
    # comparison rather than at the camera.
    def c_thicker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (34, 32, 36), seed=231, value=0.05)
        SC.title_backdrop(tile, 1231, col=TITLE_COURSE)
        # the WALL: an enormous slab cropped by the LEFT and BOTTOM edges,
        # hatched, with a steel skin along its base. The top used to run from
        # y=-40 ("cropped by the TOP"), but the scatter-hatching below threw
        # light strokes (128,124,118) up into y 10..73 and, on this night card
        # (median ~51), each stroke deviates ~74 grey levels from the local
        # background -- straight through "Fort Knox". The slab now starts at
        # y=104 and the hatching is confined to the slab, so the top of the
        # frame is clean background above the title band. Starting the full-height
        # wall at 104 (not shrinking it) keeps it dominating and still cropped by
        # the left and bottom edges.
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
        # the DOOR: a visibly SMALLER steel slab beside it, and the size gap is
        # the whole argument, so the character stands ON it for scale
        slab = [(760, 170), (1200, 170), (1200, 560), (760, 560)]
        PA.fill_poly(tile, slab, STEEL_DK, seed=261, value=0.08)
        PA.hand_stroke(d, slab, INK, 8, closed=True, seed=262, wavelength=140.0)
        D.draw_label(tile, 'WALL', center=(300, 640), color=PAPERW, size=48)
        D.draw_label(tile, 'DOOR', center=(980, 640), color=PAPERW, size=48)
        SC.fullbody(d, 980, 556, 260, pose='shrug', expression='skeptic',
                    seed=263)
    els.append(card(24, 25, c_thicker, kind='character'))
    els.append(cap(24, W // 2, 132, size=32, fill=TY.LABEL_YELLOW))

    # b25 a castle built to outlast a siege: the toy castle cropped by the
    # bottom, arrows coming in over the left, and the character recoiling.
    def c_castle(tile, fw, fh):
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
    els.append(card(25, 26, c_castle, kind='character'))
    els.append(cap(25, 640, 132, size=34, fill=TY.LABEL_RED))

    # ===== b26-b33  THE GOLD (hero #3) ================================== #
    # b26 HERO: the building cut open, NINE storeys, each carrying gold. The cut
    # face and the storeys together span -111..1292, so the section is cropped by
    # the left, right AND bottom edges -- and the top 140px is left as sky, so the
    # caption has somewhere honest to sit instead of lying on top of the gold.
    def c_ninefloors(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 281, sky=(198, 210, 222))
        _floors_section(d, 1726, 150, 780, 9, 282, half_w=1670)
    els.append(card(26, 27, c_ninefloors))
    els.append(cap(26, 640, 128, size=34))

    # b27 bars stacked to the ceiling: one wall of bars whose top row is cut by
    # the top edge and whose bottom row is cut by the bottom, so "to the ceiling"
    # is shown rather than claimed.
    def c_toceiling(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 291)
        SC.title_backdrop(tile, 1291, col=TITLE_COURSE)
        # The wall ran from y=-120, so it filled the whole frame INCLUDING the
        # title band and left "Fort Knox" unreadable black-on-gold. The top is
        # now 104 -- still cropped-looking and floor-to-ceiling, but the title
        # stays legible. Caught by _coverage_gate.band_intrusions().
        _bar_wall(d, -80, 104, W + 80, H + 60, 292, bw=150, bh=54, gap=6,
                  stagger=True)
    els.append(card(27, 28, c_toceiling))
    els.append(cap(27, W // 2, 620, size=34))

    # b28 hundreds of billions: the bar field on the left, and a paper ledger
    # column cropped by the top and right edges carrying the figures.
    def c_billions(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 301)
        SC.title_backdrop(tile, 1301, col=TITLE_COURSE)
        # y0 104, not -60. _gold_bar skews each bar's lit top face 0.42*bh ABOVE
        # y0, so a field starting at -60 put its first rank's top edge near -84 and
        # every bar outline crossed "Fort Knox". 104 puts the topmost ink at ~80,
        # clear of the band, and is the same top b27 already uses. The field still
        # runs from x=-80 to 860 and off the bottom edge, and the ledger column
        # still runs off the TOP and right edges.
        _bar_wall(d, -80, 104, 860, H + 40, 302, bw=146, bh=52, gap=6,
                  stagger=True)
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
    els.append(card(28, 29, c_billions))
    els.append(cap(28, 440, 620, size=34))

    # b29 12,000 tonnes: the number IS the frame, stamped across a dark band over
    # a cropped bar field, with one truck at the bottom edge for the scale.
    def c_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 311)
        SC.title_backdrop(tile, 1311, col=TITLE_COURSE)
        # y0 104, not -40. Same reason as b28: the skewed top face lifts 0.42*bh
        # above y0, so -40 put the first rank's ink near -65, inside the title
        # band. 104 clears it and matches b27. The field still spans the full
        # width and runs off the bottom, and the dark number band still crosses
        # the frame at y 200.
        _bar_wall(d, -80, 104, W + 80, H + 40, 312, bw=152, bh=54, gap=6,
                  stagger=True)
        PA.fill_rect(tile, [0, 200, W, 396], (34, 30, 34), seed=313, value=0.05)
        D.draw_number(tile, '12,000', center=(540, 298), color=GOLD_HI, size=178)
        D.draw_label(tile, 'TONNES', center=(1070, 298), color=GOLD_HI, size=64)
        _truck(d, 1010, 740, 350, 314)
    els.append(card(29, 30, c_tonnes))
    els.append(cap(29, 300, 660, size=34))

    # b30 the stacks filled whole wings: the same hall as b04 but pulled further
    # back, so FOUR ranks march away, each running off both side edges.
    def c_wings(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 321, fill_frac=1.0, floor_y=700, back=4)
    els.append(card(30, 31, c_wings))
    els.append(cap(30, W // 2, 620, size=34))

    # b31 much of it belongs to other governments: the near rank with a full row
    # of flags above it, the whole field cropped left and right.
    def c_others(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 331)
        _flag_row(d, 70, 1230, 430, 332, n=7, h=60)
    els.append(card(31, 32, c_others))
    els.append(cap(31, W // 2, 620, size=32))

    # b32 HERO: the small national flags ABOVE one vault door. The door is pushed
    # low and cropped by the bottom edge so the flags genuinely sit above it, and
    # the caption takes the dark band at the top.
    def c_flagdoor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 341)
        SC.title_backdrop(tile, 1341, col=TITLE_COURSE)
        _vault_door(d, 560, 500, 310, 342, hinge=True, wheel=True, rings=3,
                    bolts=18)
        _flag_row(d, 120, 1180, 210, 343, n=6, h=54)
    els.append(card(32, 33, c_flagdoor))
    els.append(cap(32, 640, 128, size=32))

    # b33 their gold as well: inside the vault -- bars stacked behind the flags,
    # the flags planted along the top of the near rank, and the character standing
    # IN the gold, cropped by the bottom, shrugging at the arrangement.
    def c_vault_gold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 351)
        SC.title_backdrop(tile, 1351, col=TITLE_COURSE)
        _bar_wall(d, -70, 250, W + 70, 700, 352, bw=138, bh=48, gap=6,
                  stagger=True)
        _flag_row(d, 100, 1200, 236, 353, n=6, h=52)
        SC.fullbody(d, 640, 726, 420, pose='shrug', expression='skeptic',
                    seed=354)
    els.append(card(33, 34, c_vault_gold, kind='character'))
    els.append(cap(33, W // 2, 166, size=32, fill=TY.LABEL_YELLOW))

    # ===== b34-b36  only a small share stays ============================ #
    # b34 THE SAME HALL ROUTINE AS b04, but with fill_frac<1 so the right of the
    # floor is BARE, and the character standing in the gap at 470px. The empty
    # floor is the point of the beat, so it is real bare floor -- not a dark
    # overlay pretending to be absence.
    def c_mostly_empty(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 361, fill_frac=0.52, floor_y=690, back=3)
        SC.fullbody(d, 1010, 690, 470, pose='shrug', expression='skeptic',
                    seed=362)
    els.append(card(34, 35, c_mostly_empty, kind='character'))
    els.append(cap(34, 990, 132, size=32, fill=TY.LABEL_RED, max_w=560))

    # b35 only a few hundred tonnes: two short ranks, a lot of bare floor, and
    # the small number stamped on the empty floor where the gold is not.
    def c_few_hundred(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _bar_hall(d, 371, fill_frac=0.40, floor_y=700, back=2)
        D.draw_label(tile, 'A FEW HUNDRED', center=(930, 430),
                     color=(250, 232, 168), size=42)
    els.append(card(35, 36, c_few_hundred))
    els.append(cap(35, 930, 690, size=32, fill=TY.LABEL_YELLOW))

    # b36 the rest was moved out years ago. Three trucks on a road, the near one
    # cropped by the LEFT edge so it is leaving the frame rather than parked in
    # it, and the arrow pointing the same way the truck is going.
    def c_moving_out(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (198, 202, 208), seed=381, value=0.05)
        PA.fill_rect(tile, [0, 520, W, H], (166, 168, 172), seed=382, value=0.07)
        PA.paper_overlay(tile, seed=383)
        _truck(d, 180, 704, 540, 384)
        _truck(d, 850, 662, 300, 385, col=(150, 74, 60))
        _truck(d, 1150, 634, 190, 386, col=(140, 70, 58))
        D.draw_arrow(tile, (700, 268), (250, 268), color=RED, width=12, head=54)
        D.draw_label(tile, 'MOVED OUT', center=(920, 172), color=TY.LABEL_RED,
                     size=52)
    els.append(card(36, 37, c_moving_out))
    els.append(cap(36, 640, 690, size=34, fill=TY.LABEL_RED))

    # ===== b37-b42  the tours: above the gold, never below ============== #
    # b37 the counter, the ledger, the stamp: three props in one frame, the
    # counter running off BOTH edges so the queue it serves has somewhere to
    # come from, and the caption up in the clear wall above it.
    def c_counter(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _pale(tile, 391, (216, 212, 202))
        _counter(d, -60, 1340, 700, 240, 392)
        _page(d, 300, 432, 700, 596, 393, lines=5)
        _stamp(d, 880, 516, 64, 394)
        D.draw_label(tile, 'VISITORS', center=(880, 372), color=TY.LABEL_INK,
                     size=38)
    els.append(card(37, 38, c_counter))
    els.append(cap(37, 380, 190, size=32))

    # b38 thousands every year: a crowd of blank figures filling the frame,
    # cropped at every edge, standing in front of a corridor that converges
    # behind them. Four depth rows -- the row nearest the camera is the biggest.
    def c_crowd(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 640, 396, 401, floor_y=560, w0=1500)
        cols = ((70, 96, 168), (188, 96, 72), (96, 150, 116), (168, 152, 96))
        for r, (off, y, sc) in enumerate(((0, 250, 0.52), (3, 330, 0.72),
                                          (7, 430, 0.96), (12, 560, 1.28))):
            n = 7 + r * 2
            for i in range(n + 1):
                x = -60 + i * (W + 120) / float(n) + (off % 2) * 26
                _person(d, x, y, 250 * sc, 410 + r * 20 + i,
                        col=cols[(i + r) % 4])
        D.draw_label(tile, 'THOUSANDS A YEAR', center=(640, 104),
                     color=TY.LABEL_INK, size=44)
    els.append(card(38, 39, c_crowd))
    els.append(cap(38, 640, 676, size=32))

    # b39 school field trips each spring: two buses on the road, the near one
    # cropped by the left edge, with a wave from the character at the kerb.
    def c_fieldtrips(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hills(tile, 421)
        _bus(d, 220, 694, 480, 422)
        _bus(d, 880, 706, 480, 423, col=(216, 170, 40))
        D.draw_label(tile, 'EVERY SPRING', center=(640, 172),
                     color=TY.LABEL_INK, size=48)
        SC.fullbody(d, 1140, 700, 340, pose='wave', expression='smirk',
                    seed=424)
    els.append(card(39, 40, c_fieldtrips, kind='character'))
    els.append(cap(39, 640, 690, size=32))

    # b40 a line of children in a corridor: one-point perspective, the line
    # receding toward the lit far end with the figures getting SMALLER, which is
    # the only depth cue a flat frame has.
    def c_children(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 640, 392, 431, floor_y=580, w0=1420)
        spots = ((170, 700, 340), (430, 664, 300), (660, 634, 262),
                 (856, 610, 226), (1010, 590, 194), (1136, 574, 168),
                 (1236, 562, 146))
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, (x, y, h) in enumerate(spots):
            _person(d, x, y, h, 440 + i, col=cols[i % 4])
    els.append(card(40, 41, c_children))
    els.append(cap(40, 640, 676, size=32))

    # b41 / b42 THE SECTION, DRAWN ONCE AND RE-USED with the lower storey
    # flipped. Both halves are cropped by the frame, the figures walk on top of
    # the slab, and the gold is directly under their feet.
    def c_above_gold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (222, 218, 208), seed=451, value=0.05)
        PA.paper_overlay(tile, seed=452)
        _deck_section(d, 453, deck_y=470, sealed=False)
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, x in enumerate((40, 190, 340, 490, 640, 790, 940, 1090, 1240)):
            _person(d, x, 452, 210, 460 + i, col=cols[i % 4])
        D.draw_label(tile, 'THEY WALK ABOVE IT', center=(640, 140),
                     color=TY.LABEL_INK, size=40)
    els.append(card(41, 42, c_above_gold))
    els.append(cap(41, W // 2, 686, size=32))

    def c_never_below(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (214, 210, 200), seed=471, value=0.05)
        PA.paper_overlay(tile, seed=472)
        _deck_section(d, 473, deck_y=470, sealed=True)
        cols = ((196, 96, 76), (86, 122, 168), (96, 150, 116), (188, 152, 72))
        for i, x in enumerate((40, 190, 340, 490, 640, 790, 940, 1090, 1240)):
            _person(d, x, 452, 210, 480 + i, col=cols[i % 4])
        D.draw_label(tile, 'NEVER BELOW IT', center=(640, 140),
                     color=TY.LABEL_INK, size=40)
    els.append(card(42, 43, c_never_below))
    els.append(cap(42, W // 2, 686, size=32, fill=TY.LABEL_RED))

    # ===== b43-b44  the finale: bolted, and nobody has seen ============== #
    def c_bolted(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 491, top=(44, 44, 52), bot=(30, 30, 36))
        _inner_door(d, 640, 360, 1000, 720, 492, bolt=6)
    els.append(card(43, 44, c_bolted))
    els.append(cap(43, W // 2, 690, size=34, fill=TY.LABEL_YELLOW))

    # b44 THE LAST FRAME. A close-up in an EMPTY corridor -- the walls converge
    # on a lit end with nobody standing in it, and he is the only person in the
    # picture, which is the line.
    def c_nobody_seen(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (48, 48, 56), seed=501, value=0.10)
        PA.paper_overlay(tile, seed=502)
        SC.title_backdrop(tile, 1501, col=TITLE_COURSE)
        for s in (-1, 1):
            x = s * (W / 2.0 + 60)
            # The converging walls used to start at y=-40, so they ran straight
            # through the title band (caught by _coverage_gate.band_intrusions).
            # They now start at 104 on the SAME converging line -- the crop is
            # unchanged, only moved down out of the band -- which leaves the head
            # of the frame to the lit course the title reads on. Same remedy as
            # b24 / b27 / b28 in this chapter.
            x0 = x + (900.0 - x) * (144.0 / 340.0)
            wall = [(x0, 104), (900, 300), (900, 470), (x, H + 40)]
            PA.fill_poly(tile, wall, (66, 66, 74), seed=503 + s, value=0.07)
            PA.hand_stroke(d, wall, INK, 7, closed=False, seed=505 + s,
                           wavelength=180.0)
        PA.fill_poly(tile, [(-60, H + 40), (900, 470), (900, 470),
                            (W + 60, H + 40)], (58, 58, 66), seed=507, value=0.07)
        SC.closeup(d, 330, 400, 235, 'worried', 508)
        D.draw_bubble(tile, 'nobody alive', xy=(880, 186), tail_to=(640, 300),
                      font_size=38, max_w=420)
    els.append(card(44, 45, c_nobody_seen, kind='character'))
    els.append(cap(44, 950, 656, size=34, fill=TY.LABEL_YELLOW, max_w=520))

    return SC.finish(els, TITLE, clock, title_seed=7)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))
