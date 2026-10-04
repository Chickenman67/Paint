"""mezhgorye scene -- chapter 2 of the bunker film.

Mezhgorye: the Soviet leadership bunker buried under a hillside near Kostenki,
east of Magadan. A green field, grey concrete, one deep red accent.

Structure is entirely scene_common's (caption handoff, cropped close-up, phrase
clock, render drivers); this file declares only Mezhgorye's cards.

ONE CARD PER BEAT, AND EACH CARD PAINTS ITS OWN WHOLE FRAME. beats.json gives
all 30 beats an exact [start, end] from the real WAV, so card boundaries are
measured, not guessed. Every card function fills background-to-subject, which
makes it structurally impossible for one card's art to bleed into the next --
and it matters more here than in any earlier chapter, because most of this
chapter lives UNDERGROUND and a leaked sky band would read instantly as a bug.

TWO REGISTERS, and the card must stay inside one. Exterior cards are sky over
green field; interior/cutaway cards are earth and concrete with no sky at all;
blueprint beats are a grey sheet; the page beats (forget / closed) are bare
paper. Mixing them inside a card is the failure mode to watch for.

FRAME-FILL. The recurring defect in this project's history is a small subject
parked in a large empty field. Every card here lets the dominant subject own
the frame and crop BY an edge -- the mountain runs off both sides, the
cross-section runs off both sides, the steel door runs off the top.

CADENCE. Still-dominant, one cut per sentence (~30 cuts in 77s). Only b10
(the hand drill actually cutting) gets a `motion` keyframe track, because it
is the only line in the chapter that describes something happening. A
reference compared at a common 6fps is ~2/3 still; our v2 was motion-dominated
at 44% once.

Run:  python lib/mezhgorye_scene.py --preview --video
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
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'mezhgorye'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Mezhgorye'

# The title band carries an intentional lit stone course on the two night cards
# (b19 tunnel, b30 rock face), so band_intrusions exempts exactly those rows --
# see its TITLE_BACKDROP handling and scene_common.title_backdrop. Only the part
# inside the band is declared: rows below it are ordinary art and stay checked.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# GREEN FIELD + GREY CONCRETE + ONE DEEP RED. Red is rationed hard: it marks
# the three things this chapter is actually about -- the secrecy (the sealed
# door), the measurement (the 120 km ruler), and the paperwork lie (the CLOSED
# stamp). Nothing decorative is ever red.
INK = SC.INK
SKY = (196, 210, 222)
SNOW = (238, 241, 244)
SNOW_SH = (206, 216, 226)
FIELD = (124, 152, 92)
FIELD_D = (90, 116, 66)
ROCK = (128, 132, 138)          # above-ground mountain rock
ROCK_D = (90, 94, 100)
EARTH = (150, 142, 126)         # underground mass in section
EARTH_D = (116, 108, 94)
CONCRETE = (206, 202, 192)
CONC_D = (166, 162, 152)
STEEL = (150, 156, 164)
STEEL_D = (102, 108, 118)
DARK = (44, 42, 46)             # a bored tunnel's interior
BLUE_W = (146, 176, 196)        # the frozen river
RED = (176, 42, 34)             # THE accent
RED_L = (206, 88, 76)
LAMP = (240, 202, 112)
PAPER = (244, 242, 234)
BLUE_INK = (92, 104, 122)       # blueprint pencil

HZ = int(H * 0.62)


# ---------------------------------------------------------------------------
# bases -- one per register. Call the matching one at the TOP of every card.
# ---------------------------------------------------------------------------

def _exterior(tile, seed, sky=SKY, ground=FIELD, hz=HZ):
    """Sky over a green field. The base for every above-ground beat."""
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


def _winter(tile, seed):
    """The same valley under deep snow -- beats 04, 05, 11, 28."""
    PA.fill_rect(tile, [0, 0, W, H], SKY, seed=seed, value=0.05)
    PA.fill_rect(tile, [0, HZ - 6, W, H], SNOW, seed=seed + 1, value=0.06)
    PA.paper_overlay(tile, seed=seed + 2)


def _underground(tile, seed, base=EARTH):
    """Solid earth, NO SKY. Beats that live underground must never show one."""
    PA.fill_rect(tile, [0, 0, W, H], base, seed=seed, value=0.08)
    PA.paper_overlay(tile, seed=seed + 2)


def _page(tile, seed):
    """Bare paper for the two beats about the site being forgotten on paper."""
    PA.fill_rect(tile, [0, 0, W, H], PAPER, seed=seed, value=0.04)
    PA.paper_overlay(tile, seed=seed + 1)


def _blueprint(tile, seed):
    """A grey drafting sheet with a faint grid -- beats 06 and 07."""
    PA.fill_rect(tile, [0, 0, W, H], (176, 190, 202), seed=seed, value=0.06)
    d = ImageDraw.Draw(tile)
    for x in range(0, W + 1, 64):
        PA.hand_stroke(d, [(x, 0), (x, H)], (166, 180, 192), 2, seed=seed + 1,
                       wavelength=180.0, vary=0.10)
    for y in range(0, H + 1, 64):
        PA.hand_stroke(d, [(0, y), (W, y)], (166, 180, 192), 2, seed=seed + 2,
                       wavelength=180.0, vary=0.10)
    PA.paper_overlay(tile, seed=seed + 3)


def _rock_face(tile, seed, base=ROCK):
    """A close rock wall -- the backdrop for the digging beats (08-10, 12)."""
    PA.fill_rect(tile, [0, 0, W, H], base, seed=seed, value=0.09)
    d = ImageDraw.Draw(tile)
    # cracks. Drawn as short broken polylines, never as long straight rules,
    # or they read as masonry courses on a wall rather than split rock.
    for k, (x0, y0, x1, y1) in enumerate(((150, 40, 240, 300),
                                          (520, 620, 470, 700),
                                          (900, 20, 980, 260),
                                          (1180, 380, 1240, 560))):
        pts = []
        for i in range(7):
            u = i / 6.0
            pts.append((x0 + (x1 - x0) * u + 14 * math.sin(u * 7 + k),
                        y0 + (y1 - y0) * u))
        PA.hand_stroke(d, pts, ROCK_D, 5, seed=seed + 10 + k, wavelength=90.0)
    PA.paper_overlay(tile, seed=seed + 3)


# ---------------------------------------------------------------------------
# mass helper -- the workhorse for every silhouette in the chapter
# ---------------------------------------------------------------------------

def _mass(d, pts, col, seed, width=7, stroke=True, closed=False,
          value=0.06, edge=2.0):
    """Fill a silhouette and keyline it.

    `closed` is deliberately FALSE by default. A mountain cropped by the frame
    has no bottom edge to draw, and stroking one puts a black rule across the
    bottom of the picture where there is nothing but fill.
    """
    img = PA.img_of(d)
    PA.fill_poly(img, pts, col, seed=seed, value=value, edge=edge)
    if stroke:
        PA.hand_stroke(d, pts, INK, width, closed=closed, seed=seed + 1,
                       wavelength=170.0)


# ---------------------------------------------------------------------------
# subjects
# ---------------------------------------------------------------------------

def _ridgeline(d, y_base, amp, seed, col=ROCK, x0=-60, x1=None, width=7,
               closed=False):
    """A rolling hill / ridge silhouette running the full width of the frame.

    `amp` is peak-to-trough. The line starts and ends OFF-frame so the mass
    always crops at both edges -- a ridge that stops inside the picture reads
    as a prop, not as terrain.
    """
    if x1 is None:
        x1 = W + 60
    pts = [(x0, y_base)]
    n = 9
    span = x1 - x0
    for i in range(1, n):
        u = i / float(n)
        x = x0 + span * u
        y = y_base - amp * (0.55 + 0.45 * math.sin(u * 5.1 + seed * 0.7))
        pts.append((x, y))
    pts.append((x1, y_base))
    pts.append((x1, y_base + (H - y_base) + 80))
    pts.append((x0, y_base + (H - y_base) + 80))
    _mass(d, pts, col, seed, width=width, closed=closed)
    return pts


def _snow_cap(d, pts, y_top, seed, col=SNOW):
    """Snow lying on a ridge: a thin band hugging the ridge line, clipped to it.

    Drawn as a run of the SAME curve offset downward, offset by only a few px,
    so it reads as lying ON the rock. A big white blob offset far below the
    ridge reads as a separate object hanging in the sky.
    """
    top = [p for p in pts if p[1] < y_top + 4]
    if len(top) < 2:
        return
    band = list(top) + [(p[0], p[1] + 34) for p in reversed(top)]
    PA.fill_poly(PA.img_of(d), band, col, seed=seed, value=0.05, edge=1.6)


def _mountain(d, cx, base_y, half_w, peak_y, seed, col=ROCK):
    """The hero mass of beat 01: a big cold-grey mountain, cropped at the sides.

    The peak is deliberately OFF CENTRE. A centred pyramid reads as a triangle;
    an off-centre summit with a long shoulder reads as terrain.
    """
    pts = [(-60, base_y)]
    n = 13
    for i in range(n + 1):
        u = i / float(n)
        x = -60 + (W + 120) * u
        # two summits, the taller left of centre
        h = (math.sin(u * math.pi) ** 0.7)
        shoulder = 0.55 + 0.45 * math.exp(-((u - 0.38) ** 2) / 0.02)
        y = base_y - (base_y - peak_y) * h * shoulder
        pts.append((x, y))
    pts.append((W + 60, base_y))
    pts.append((W + 60, H + 60))
    pts.append((-60, H + 60))
    _mass(d, pts, col, seed, width=7)
    _snow_cap(d, pts, peak_y + 92, seed + 3)
    return pts


def _archway(d, cx, base_y, w, h, seed, fill=DARK):
    """A doorway arch cut into the rock -- dark, sealed, no light inside."""
    img = PA.img_of(d)
    r = w / 2.0
    body = [(cx - r, base_y), (cx - r, base_y - h + r)]
    body += PA.arc_pts(cx, base_y - h + r, r, r, 180, 360, n=32)
    body += [(cx + r, base_y)]
    PA.fill_poly(img, body, fill, seed=seed, value=0.05, edge=2.0)
    PA.hand_stroke(d, body, INK, 7, closed=True, seed=seed + 1,
                   wavelength=110.0)
    return body


def _steel_door(d, cx, cy, w, h, seed, handle=True, col=STEEL):
    """A heavy blast door: arched top, ribs, rivets, and a spoked wheel.

    WHY THE RIBS AND RIVETS ARE DRAWN BEFORE THE WHEEL. An earlier door was
    three grey bars on a grey field and read as a filing cabinet. What says
    "blast door" is the hardware: horizontal ribs, a ring of rivets down each
    stile, and one big spoked wheel. Those three cues carry it at any size.

    `handle=False` draws the wheel as a DASHED ring with a red slash across it,
    which is how beats 02 and 30 say "there is nothing on this side to open."
    """
    img = PA.img_of(d)
    r = w / 2.0
    body = [(cx - r, cy + h / 2.0), (cx - r, cy - h / 2.0 + r)]
    body += PA.arc_pts(cx, cy - h / 2.0 + r, r, r, 180, 360, n=36)
    body += [(cx + r, cy + h / 2.0)]
    PA.fill_poly(img, body, col, seed=seed, value=0.07, edge=2.2)
    PA.hand_stroke(d, body, INK, 8, closed=True, seed=seed + 1,
                   wavelength=130.0)

    # horizontal ribs across the leaf
    for i in range(4):
        y = cy - h * 0.28 + i * h * 0.19
        PA.hand_stroke(d, [(cx - r * 0.84, y), (cx + r * 0.84, y)], STEEL_D, 6,
                       seed=seed + 10 + i, wavelength=100.0)
    # rivets down both stiles
    for i in range(6):
        y = cy - h * 0.34 + i * h * 0.135
        for sx in (-1, 1):
            px = cx + sx * r * 0.90
            d.ellipse([px - 7, y - 7, px + 7, y + 7], fill=INK)

    if handle:
        wr = w * 0.22
        PA.hand_stroke(d, PA.ellipse_pts(cx, cy, wr, wr, n=40), INK, 7,
                       closed=True, seed=seed + 20, wavelength=90.0)
        for k in range(4):
            a = math.pi * k / 4.0 + 0.4
            PA.hand_stroke(d, [(cx - wr * math.cos(a), cy - wr * math.sin(a)),
                               (cx + wr * math.cos(a), cy + wr * math.sin(a))],
                           INK, 5, seed=seed + 30 + k, wavelength=70.0)
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=INK)
    else:
        # no handle on this side: a dashed ghost wheel with a red bar across it
        ring = PA.ellipse_pts(cx, cy, w * 0.22, w * 0.22, n=64)
        m = len(ring)
        i = 0
        while i < m:
            seg = [ring[(i + k) % m] for k in range(min(6, m - i))]
            if len(seg) > 1:
                PA.hand_stroke(d, seg, STEEL_D, 4, seed=seed + 40 + i,
                               wavelength=80.0)
            i += 10
        wr = w * 0.22
        PA.hand_stroke(d, [(cx - wr * 1.25, cy + wr * 1.25),
                           (cx + wr * 1.25, cy - wr * 1.25)], RED, 9,
                       seed=seed + 50, wavelength=60.0)


def _bunker(d, cx, cap_y, rw, seed, decks=4, deck_h=64, deck_w=None,
            tunnel_dy=None, lamps=True, doors=1, cap_h=None):
    """THE HERO: a mushroom-cap blast shell in cross-section, with deep levels.

    This is the image the whole chapter is built to deliver, so it gets a real
    construction rather than a metaphor:

      * a wide DOME (the blast cap) -- a half-ellipse of CONCRETE with a
        matching DARK chamber hollowed inside it, so what you see between the
        two arcs is a THICK SHELL, which is what a blast shell is;
      * a STEM of stacked DECK SLABS hanging under the cap -- the deep levels,
        getting progressively NARROWER going down, which is what makes the
        stack read as descending into the rock rather than as a grid of boxes;
      * a CENTRAL SHAFT linking the decks, the one vertical in the chapter;
      * horizontal BORES leaving the stem both ways and running off the frame
        edges, which is what fills the frame and says "network";
      * an optional blast DOOR on each level, offset so they do not stack.

    *** THE FIRST DRAFT OF THIS FUNCTION WAS WRONG IN THREE WAYS, and each one
    is a lesson worth keeping. ***

    1. It filled a dome-shaped VOID and left the concrete as a fat white
       crescent around it. At ship size that read as a rainbow arch over a
       black hole -- the eye went to the black half-ellipse, not to a bunker.
       THE FIX: fill the OUTER arc CONCRETE first and hollow a SMALLER inner
       arc DARK on top of it. The shell is then the visible ring between the
       two arcs, which is exactly how a shell looks, and the dark chamber is
       now a modest void rather than the subject.
    2. It placed the dome's springing line ABOVE the ground surface, so the
       bunker erupted out of the hillside into the sky. cap_y is the y of the
       SPRINGING LINE (the flat underside), and the dome's apex is cap_y minus
       its height -- so cap_y MUST be well below the ground line. The hero card
       now sets cap_y=300 with the ground at ~100.
    3. It drew the bores starting at stem_w*0.92 while the decks were only
       stem_w wide, leaving a visible gap of bare earth between the deck stack
       and the tunnels -- the whole structure fell apart into floating pieces.
       THE FIX: the bores start at the stem edge and the deck slabs are as wide
       as the bore mouth, so the parts touch.
    """
    img = PA.img_of(d)
    stem_w = deck_w if deck_w else rw * 0.50
    # `cap_h` overrides the default dome height. It exists because the dome's
    # APEX is cap_y - cap_h, and engine3 stamps the persistent chapter title
    # over y 9..73 of every frame: a card that lets the dome climb above ~104
    # drives its keyline straight through the title. Flattening the cap buys
    # the vertical room the bores need without shrinking rw, so the structure
    # still spans the frame.
    cap_h = cap_h if cap_h else rw * 0.52
    shell_t = max(16.0, rw * 0.09)      # the shell's thickness

    # --- the dome: concrete shell, dark chamber hollowed inside -----------
    outer = PA.arc_pts(cx, cap_y, rw, cap_h, 180, 360, n=64)
    outer += [(cx + rw, cap_y), (cx - rw, cap_y)]
    PA.fill_poly(img, outer, CONCRETE, seed=seed, value=0.06, edge=2.4)
    PA.hand_stroke(d, PA.arc_pts(cx, cap_y, rw, cap_h, 180, 360, n=64), INK,
                   8, closed=False, seed=seed + 1, wavelength=150.0)

    ir = rw - shell_t * 2.0
    ih = cap_h - shell_t * 1.6
    inner = PA.arc_pts(cx, cap_y - shell_t * 0.5, ir, ih, 180, 360, n=56)
    inner += [(cx + ir, cap_y - shell_t * 0.5), (cx - ir, cap_y - shell_t * 0.5)]
    PA.fill_poly(img, inner, DARK, seed=seed + 3, value=0.04, edge=1.4)
    # the underside of the cap, where the shell meets the stem
    PA.hand_stroke(d, [(cx - rw, cap_y), (cx - stem_w, cap_y)], INK, 7,
                   seed=seed + 4, wavelength=120.0)
    PA.hand_stroke(d, [(cx + stem_w, cap_y), (cx + rw, cap_y)], INK, 7,
                   seed=seed + 5, wavelength=120.0)

    # --- the stem: stacked decks, narrowing downward ---------------------
    top = cap_y
    for k in range(decks):
        w_k = stem_w * (1.0 - 0.08 * k)
        y0 = top + k * deck_h
        y1 = y0 + deck_h - 14
        slab = [(cx - w_k, y0), (cx + w_k, y0), (cx + w_k, y1), (cx - w_k, y1)]
        PA.fill_poly(img, slab, CONC_D if k % 2 else CONCRETE, seed=seed + 10 + k,
                     value=0.06, edge=2.0)
        PA.hand_stroke(d, slab, INK, 6, closed=True, seed=seed + 20 + k,
                       wavelength=110.0)
        if k and doors:
            # a single blast door on each level, offset so they do not stack
            dx = cx + (w_k * 0.30 if k % 2 else -w_k * 0.30)
            dw = w_k * 0.28
            dh = (y1 - y0) * 0.58
            door = [(dx - dw / 2, y0 + (y1 - y0) * 0.20),
                    (dx + dw / 2, y0 + (y1 - y0) * 0.20),
                    (dx + dw / 2, y0 + (y1 - y0) * 0.20 + dh),
                    (dx - dw / 2, y0 + (y1 - y0) * 0.20 + dh)]
            PA.fill_poly(img, door, STEEL_D, seed=seed + 30 + k, value=0.05,
                         edge=1.6)
            PA.hand_stroke(d, door, INK, 5, closed=True, seed=seed + 40 + k,
                           wavelength=70.0)

    stem_bottom = top + decks * deck_h
    # --- the central shaft ------------------------------------------------
    sw = stem_w * 0.18
    shaft = [(cx - sw, top), (cx + sw, top), (cx + sw, stem_bottom),
             (cx - sw, stem_bottom)]
    PA.fill_poly(img, shaft, (186, 182, 172), seed=seed + 50, value=0.06,
                 edge=1.6)
    PA.hand_stroke(d, shaft, INK, 5, closed=True, seed=seed + 51,
                   wavelength=120.0)

    # --- the bores, starting AT the stem edge so nothing floats ----------
    if tunnel_dy is None:
        tunnel_dy = [deck_h * 1.5]
    for k, dy in enumerate(tunnel_dy):
        y = top + dy
        th = deck_h * 0.58
        for side in (-1, 1):
            x_in = cx + side * stem_w
            x_out = cx + side * (W * 0.95)
            bore = [(x_in, y - th / 2), (x_out, y - th / 2),
                    (x_out, y + th / 2), (x_in, y + th / 2)]
            PA.fill_poly(img, bore, DARK, seed=seed + 60 + k * 2 + side,
                         value=0.03, edge=1.6)
            PA.hand_stroke(d, [(x_in, y - th / 2), (x_out, y - th / 2)],
                           INK, 5, seed=seed + 70 + k * 2 + side,
                           wavelength=170.0)
            PA.hand_stroke(d, [(x_in, y + th / 2), (x_out, y + th / 2)],
                           INK, 5, seed=seed + 80 + k * 2 + side,
                           wavelength=170.0)
            # ribs every so often, so a long bore reads as a lined tunnel
            nb = 5
            for i in range(1, nb):
                u = i / float(nb)
                x = x_in + (x_out - x_in) * u
                PA.hand_stroke(d, [(x, y - th / 2), (x, y + th / 2)],
                               CONC_D, 4, seed=seed + 90 + k * 20 + i * 2 + side,
                               wavelength=90.0)

    if lamps:
        for k, dy in enumerate(tunnel_dy or []):
            y = top + dy
            for side in (-1, 1):
                lx = cx + side * W * 0.34
                PA.fill_poly(img, PA.ellipse_pts(lx, y, 20, 20, n=20), LAMP,
                             seed=seed + 120 + k * 2 + side, value=0.10,
                             edge=1.2)
    return stem_bottom


def _chamber(d, cx, cy, w, h, seed, door_side=1, col=CONCRETE):
    """A wide side chamber off a bore, with one door. Beat 15."""
    img = PA.img_of(d)
    body = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
            (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    PA.fill_poly(img, body, col, seed=seed, value=0.06, edge=2.2)
    PA.hand_stroke(d, body, INK, 7, closed=True, seed=seed + 1,
                   wavelength=130.0)
    dx = cx + door_side * w * 0.30
    dw, dh = w * 0.16, h * 0.62
    door = [(dx - dw / 2, cy - dh / 2 + 6), (dx + dw / 2, cy - dh / 2 + 6),
            (dx + dw / 2, cy + dh / 2 - 6), (dx - dw / 2, cy + dh / 2 - 6)]
    PA.fill_poly(img, door, STEEL_D, seed=seed + 2, value=0.05, edge=1.6)
    PA.hand_stroke(d, door, INK, 5, closed=True, seed=seed + 3,
                   wavelength=70.0)


def _bore(d, x0, y0, x1, y1, h0, h1, seed, col=DARK, lamps=0):
    """A tunnel in perspective: a dark quad from a near mouth to a far end."""
    img = PA.img_of(d)
    poly = [(x0, y0 - h0 / 2), (x1, y1 - h1 / 2), (x1, y1 + h1 / 2),
            (x0, y0 + h0 / 2)]
    PA.fill_poly(img, poly, col, seed=seed, value=0.03, edge=1.8)
    PA.hand_stroke(d, [(x0, y0 - h0 / 2), (x1, y1 - h1 / 2)], INK, 7,
                   seed=seed + 1, wavelength=150.0)
    PA.hand_stroke(d, [(x0, y0 + h0 / 2), (x1, y1 + h1 / 2)], INK, 7,
                   seed=seed + 2, wavelength=150.0)
    if lamps:
        for i in range(lamps):
            u = (i + 1) / float(lamps + 1)
            lx = x0 + (x1 - x0) * u
            ly = y0 + (y1 - y0) * u
            rr = 26 * (1.0 - 0.45 * u)
            PA.fill_poly(img, PA.ellipse_pts(lx, ly, rr, rr, n=20), LAMP,
                         seed=seed + 10 + i, value=0.10, edge=1.2)
            for k in range(8):                       # a soft glow, painted not glowed
                a = math.pi * 2 * k / 8.0
                g = [(lx, ly),
                     (lx + rr * 2.6 * math.cos(a - 0.3), ly + rr * 2.6 * math.sin(a - 0.3)),
                     (lx + rr * 2.6 * math.cos(a + 0.3), ly + rr * 2.6 * math.sin(a + 0.3))]
                PA.fill_poly(img, g, (206, 176, 116), seed=seed + 20 + i * 8 + k,
                             value=0.05, edge=1.0)


def _rail(d, xn, yn, wn, xf, yf, wf, seed, ties=7, col=STEEL_D):
    """Narrow-gauge track in perspective: two rails plus sleepers.

    `wn` is the near gauge (rail-centre to rail-centre), `wf` the far one.
    The rails converge because the gauge narrows with distance, and that
    convergence is the whole cue that says "this line goes somewhere deep."
    """
    img = PA.img_of(d)
    for i in range(ties):
        u = (i + 0.5) / float(ties)
        u2 = u ** 1.55
        tx = xn + (xf - xn) * u2
        ty = yn + (yf - yn) * u2
        tw = wn + (wf - wn) * u2
        th = max(3.0, 20.0 * (1.0 - u) + 4.0)
        PA.hand_stroke(d, [(tx - tw / 2, ty), (tx + tw / 2, ty)], (92, 84, 72),
                       int(th), seed=seed + i, wavelength=80.0)
    for side in (-1, 1):
        pts = []
        n = 22
        for i in range(n + 1):
            u = (i / float(n)) ** 1.55
            pts.append((xn + (xf - xn) * u + side * (wn + (wf - wn) * u) / 2.0,
                        yn + (yf - yn) * u))
        PA.hand_stroke(d, pts, col, 11, seed=seed + 20 + side,
                       wavelength=130.0)


def _fortress(d, cx, base_y, w, h, seed, slits=5, col=CONCRETE, wall_only=False):
    """The stone fortress: a thick trapezoid block with tiny slit windows.

    WHY THE SLITS ARE TINY AND THE WALLS THICK. A fortress drawn to scale --
    windows you could walk through -- reads as an apartment block. The
    recognisable thing is the ratio: a wall so thick the window is a scratch,
    and NO second opening anywhere on the face.
    """
    img = PA.img_of(d)
    top_w = w * 0.88
    body = [(cx - w / 2, base_y), (cx + w / 2, base_y),
            (cx + top_w / 2, base_y - h), (cx - top_w / 2, base_y - h)]
    PA.fill_poly(img, body, col, seed=seed, value=0.07, edge=2.4)
    PA.hand_stroke(d, body, INK, 8, closed=True, seed=seed + 1,
                   wavelength=150.0)
    # course lines so the mass reads as masonry, not as a grey wedge
    for i in range(1, 5):
        y = base_y - h * i / 5.0
        u = 0.5 + 0.5 * (i / 5.0)
        x0 = cx - (w / 2 + (top_w - w) / 2 * (1 - u))
        x1 = cx + (w / 2 + (top_w - w) / 2 * (1 - u))
        PA.hand_stroke(d, [(x0, y), (x1, y)], CONC_D, 4, seed=seed + 10 + i,
                       wavelength=140.0)
    # slit windows -- short, tall, thin, and the ONLY openings
    for i in range(slits):
        u = (i + 0.5) / float(slits)
        y = base_y - h * 0.58
        x = cx + (u - 0.5) * w * 0.68
        sw, sh = w * 0.016, h * 0.20
        sl = [(x - sw, y - sh / 2), (x + sw, y - sh / 2),
              (x + sw, y + sh / 2), (x - sw, y + sh / 2)]
        PA.fill_poly(img, sl, (52, 50, 54), seed=seed + 20 + i, value=0.03,
                     edge=1.2)
        PA.hand_stroke(d, sl, INK, 4, closed=True, seed=seed + 30 + i,
                       wavelength=60.0)
    if not wall_only:
        # a heavy closed gate, only on the inward face
        gw, gh = w * 0.20, h * 0.34
        g = [(cx - gw / 2, base_y), (cx + gw / 2, base_y),
             (cx + gw / 2, base_y - gh), (cx - gw / 2, base_y - gh)]
        PA.fill_poly(img, g, STEEL_D, seed=seed + 40, value=0.06, edge=2.0)
        PA.hand_stroke(d, g, INK, 7, closed=True, seed=seed + 41,
                       wavelength=90.0)
        for i in range(3):
            y = base_y - gh * (0.25 + i * 0.25)
            PA.hand_stroke(d, [(cx - gw / 2 + 8, y), (cx + gw / 2 - 8, y)],
                           (72, 78, 88), 5, seed=seed + 50 + i,
                           wavelength=60.0)


def _worker(d, x, feet_y, h, seed, coat=(84, 92, 104), cap=True, hunch=0.16):
    """A hunched labourer in a cap -- beats 08, 09, 11.

    NOT SC.fullbody. The presenter has to stay ONE identifiable person for the
    whole film; a crowd of copies of him turns him into a texture and the
    audience surrogate is lost. So the labourer is a separate, simpler mark:
    a filled hunched mass with a cap, drawn small enough to read as a person
    in a line rather than as a character.
    """
    img = PA.img_of(d)
    hr = h * 0.115
    hx = x + h * hunch * 0.55
    hy = feet_y - h * 0.86
    # torso: shoulders narrow to the hips, leaning forward
    torso = [(hx - h * 0.15, hy + hr * 0.9), (hx + h * 0.15, hy + hr * 0.9),
             (hx + h * 0.19, feet_y - h * 0.42),
             (hx - h * 0.17, feet_y - h * 0.42)]
    PA.fill_poly(img, torso, coat, seed=seed, value=0.07, edge=1.8)
    PA.hand_stroke(d, torso, INK, 5, closed=True, seed=seed + 1,
                   wavelength=80.0)
    # legs
    for side in (-1, 1):
        PA.hand_stroke(d, [(hx + side * h * 0.07, feet_y - h * 0.44),
                           (x + side * h * 0.08, feet_y)], INK, 6,
                       seed=seed + 10 + side, wavelength=70.0)
    # arms, hanging forward with the drill posture
    for side in (-1, 1):
        PA.hand_stroke(d, [(hx + side * h * 0.13, hy + hr * 1.5),
                           (x + side * h * 0.17, feet_y - h * 0.50)], INK, 5,
                       seed=seed + 20 + side, wavelength=70.0)
    # head
    PA.fill_poly(img, PA.ellipse_pts(hx, hy, hr, hr * 1.05, n=28),
                 (196, 176, 152), seed=seed + 30, value=0.05, edge=1.4)
    PA.hand_stroke(d, PA.ellipse_pts(hx, hy, hr, hr * 1.05, n=28), INK, 5,
                   closed=True, seed=seed + 31, wavelength=60.0)
    if cap:
        crown = PA.arc_pts(hx, hy, hr * 1.10, hr * 1.05, 180, 360, n=20)
        crown += [(hx + hr * 1.30, hy - hr * 0.10), (hx - hr * 1.30, hy - hr * 0.10)]
        PA.fill_poly(img, crown, coat, seed=seed + 40, value=0.06, edge=1.4)
        PA.hand_stroke(d, crown, INK, 4, closed=True, seed=seed + 41,
                       wavelength=50.0)


def _hand_drill(d, cx, cy, s, seed):
    """A hand drill and the two hands on it -- beat 10.

    The drill is a T: a crosspiece to grip, a shaft, and a bit going into the
    rock. Drawn LARGE and cropped so the bit visibly disappears INTO the
    stone -- that contact point is the subject of the line.
    """
    img = PA.img_of(d)
    PA.hand_stroke(d, [(cx - s * 0.92, cy - s * 0.62), (cx + s * 0.92, cy - s * 0.62)],
                   (128, 84, 52), 22, seed=seed, wavelength=110.0)
    PA.hand_stroke(d, [(cx, cy - s * 0.62), (cx, cy + s * 0.92)], (110, 74, 46),
                   20, seed=seed + 1, wavelength=110.0)
    PA.hand_stroke(d, [(cx, cy + s * 0.86), (cx, cy + s * 1.34)], (86, 88, 92),
                   12, seed=seed + 2, wavelength=70.0)
    # two hands gripping the crosspiece
    for side in (-1, 1):
        hxp = cx + side * s * 0.62
        PA.fill_poly(img, PA.ellipse_pts(hxp, cy - s * 0.52, s * 0.20,
                                         s * 0.15, n=24),
                     (198, 178, 154), seed=seed + 10 + side, value=0.05,
                     edge=1.4)
        PA.hand_stroke(d, PA.ellipse_pts(hxp, cy - s * 0.52, s * 0.20,
                                         s * 0.15, n=24), INK, 5,
                       closed=True, seed=seed + 20 + side, wavelength=60.0)
    # dust falling off the bit
    for k in range(9):
        u = (k * 37 % 17) / 17.0
        x = cx + (u - 0.5) * s * 2.1
        y = cy + s * (1.5 + u * 1.5)
        r = 4 + (k % 3) * 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(212, 200, 176))


def _coil_icon(d, cx, cy, s, seed):
    """A generator coil -- beat 16. Windings, core, and two leads."""
    img = PA.img_of(d)
    for k in range(4):
        rx = s * (0.34 + k * 0.13)
        PA.hand_stroke(d, PA.ellipse_pts(cx, cy, rx, s * 0.52, n=36), RED, 6,
                       closed=True, seed=seed + k, wavelength=70.0)
    PA.hand_stroke(d, [(cx - s * 0.10, cy - s * 0.52), (cx - s * 0.10, cy + s * 0.52)],
                   INK, 10, seed=seed + 10, wavelength=60.0)
    PA.hand_stroke(d, [(cx + s * 0.10, cy - s * 0.52), (cx + s * 0.10, cy + s * 0.52)],
                   INK, 10, seed=seed + 11, wavelength=60.0)


def _tank_icon(d, cx, cy, s, seed):
    """A water tank -- beat 16. A cylinder on end, with a feed pipe."""
    img = PA.img_of(d)
    body = [(cx - s * 0.46, cy - s * 0.30), (cx + s * 0.46, cy - s * 0.30),
            (cx + s * 0.46, cy + s * 0.42), (cx - s * 0.46, cy + s * 0.42)]
    PA.fill_poly(img, body, STEEL, seed=seed, value=0.07, edge=1.8)
    PA.hand_stroke(d, body, INK, 6, closed=True, seed=seed + 1, wavelength=80.0)
    PA.fill_poly(img, PA.ellipse_pts(cx, cy - s * 0.30, s * 0.46, s * 0.14, n=32),
                 (178, 184, 190), seed=seed + 2, value=0.06, edge=1.4)
    PA.hand_stroke(d, PA.ellipse_pts(cx, cy - s * 0.30, s * 0.46, s * 0.14, n=32),
                   INK, 5, closed=True, seed=seed + 3, wavelength=70.0)
    PA.hand_stroke(d, [(cx + s * 0.46, cy + s * 0.06), (cx + s * 0.86, cy + s * 0.06),
                       (cx + s * 0.86, cy + s * 0.42)], INK, 6, seed=seed + 4,
                   wavelength=70.0)


def _bunk_icon(d, cx, cy, s, seed):
    """A bunk bed -- beat 16. Two bunks, four posts, one pillow."""
    img = PA.img_of(d)
    for sx in (-1, 1):
        for sy in (-1, 1):
            PA.hand_stroke(d, [(cx + sx * s * 0.54, cy + sy * s * 0.48),
                               (cx + sx * s * 0.54, cy + sy * s * 0.48 + s * 0.22)],
                           INK, 7, seed=seed + (sx * 2 + sy) * 5, wavelength=50.0)
    for k, sy in enumerate((-1, 1)):
        y = cy + sy * s * 0.26
        PA.hand_stroke(d, [(cx - s * 0.54, y), (cx + s * 0.54, y)], STEEL, 9,
                       seed=seed + 20 + k, wavelength=70.0)
        PA.fill_poly(img, [(cx - s * 0.54, y - s * 0.10), (cx + s * 0.54, y - s * 0.10),
                           (cx + s * 0.54, y), (cx - s * 0.54, y)],
                     (150, 156, 164), seed=seed + 30 + k, value=0.06, edge=1.4)
    PA.fill_poly(img, [(cx - s * 0.46, cy - s * 0.34), (cx - s * 0.10, cy - s * 0.34),
                       (cx - s * 0.12, cy - s * 0.20), (cx - s * 0.46, cy - s * 0.20)],
                 (246, 244, 236), seed=seed + 40, value=0.04, edge=1.2)


def _table_and_chairs(d, cx, cy, w, seed, n_chairs=7):
    """A long table ringed by empty chairs -- beat 25.

    WHY THE CHAIRS ARE DRAWN SMALL AND TILTED. Chairs at table height read as
    a row of headstones. Seats that sit BELOW the table top with a back that
    stops short of it read as furniture immediately, and nobody in any of them
    is the entire point of the card.
    """
    img = PA.img_of(d)
    tw = w * 0.52
    top = [(cx - tw, cy), (cx + tw, cy - w * 0.06),
           (cx + tw, cy + w * 0.10), (cx - tw, cy + w * 0.16)]
    PA.fill_poly(img, top, (168, 128, 86), seed=seed, value=0.07, edge=1.8)
    PA.hand_stroke(d, top, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    for sx in (-1, 1):
        lx = cx + sx * tw * 0.74
        PA.hand_stroke(d, [(lx, cy + w * 0.13), (lx, cy + w * 0.34)], INK, 8,
                       seed=seed + 10 + sx, wavelength=60.0)
    # chairs: far side first (behind the table), then near side
    for i in range(n_chairs):
        u = (i + 0.5) / float(n_chairs)
        x = cx + (u - 0.5) * w * 1.02
        for far in (True, False):
            ch = w * (0.115 if far else 0.150)
            yy = cy - w * (0.115 if far else 0.175)
            seat = [(x - ch, yy), (x + ch, yy), (x + ch, yy + ch * 0.28),
                    (x - ch, yy + ch * 0.28)]
            col = CONC_D if far else CONCRETE
            if far:
                PA.fill_poly(img, seat, col, seed=seed + 30 + i, value=0.06,
                             edge=1.6)
                PA.hand_stroke(d, seat, INK, 4, closed=True, seed=seed + 40 + i,
                               wavelength=50.0)
                PA.hand_stroke(d, [(x - ch, yy), (x - ch, yy - ch * 0.80)],
                               INK, 4, seed=seed + 50 + i, wavelength=50.0)
                PA.hand_stroke(d, [(x + ch, yy), (x + ch, yy - ch * 0.80)],
                               INK, 4, seed=seed + 60 + i, wavelength=50.0)
            else:
                PA.fill_poly(img, seat, col, seed=seed + 70 + i, value=0.06,
                             edge=1.6)
                PA.hand_stroke(d, seat, INK, 6, closed=True, seed=seed + 80 + i,
                               wavelength=60.0)
                PA.hand_stroke(d, [(x - ch, yy), (x - ch, yy - ch * 0.86)],
                               INK, 6, seed=seed + 90 + i, wavelength=60.0)
                PA.hand_stroke(d, [(x + ch, yy), (x + ch, yy - ch * 0.86)],
                               INK, 6, seed=seed + 100 + i, wavelength=60.0)
                for sx in (-1, 1):
                    PA.hand_stroke(d, [(x + sx * ch, yy + ch * 0.28),
                                       (x + sx * ch, yy + ch * 0.86)], INK, 5,
                                   seed=seed + 110 + i * 2 + sx, wavelength=50.0)


def _mushroom_cloud(d, cx, cy, s, seed, col=RED):
    """A rough mushroom cloud doodle -- beat 24. Scrawled, not rendered."""
    img = PA.img_of(d)
    cap = PA.arc_pts(cx, cy, s, s * 0.86, 180, 360, n=28)
    stem = [(cx - s * 0.30, cy), (cx + s * 0.30, cy),
            (cx + s * 0.16, cy + s * 0.92), (cx - s * 0.16, cy + s * 0.92)]
    PA.fill_poly(img, cap, col, seed=seed, value=0.10, edge=1.4)
    PA.fill_poly(img, stem, col, seed=seed + 1, value=0.10, edge=1.4)
    PA.hand_stroke(d, cap, INK, 5, closed=False, seed=seed + 2,
                   wavelength=90.0)
    PA.hand_stroke(d, stem, INK, 5, closed=True, seed=seed + 3,
                   wavelength=80.0)
    for side in (-1, 1):                             # the skirt
        pts = [(cx + side * s * 0.92, cy + s * 0.06)]
        for i in range(1, 6):
            u = i / 5.0
            pts.append((cx + side * s * (0.92 + 0.30 * u),
                        cy + s * (0.06 + 0.34 * u * u)))
        PA.hand_stroke(d, pts, INK, 4, seed=seed + 10 + side, wavelength=70.0)


def _stamp(d, cx, cy, w, h, rot_deg, seed, col=RED):
    """A rubber stamp, drawn rotated -- beat 23.

    The box is rotated and the WORD is not. That looks like a hand slamming a
    stamp crooked onto a page, which is exactly what the line says; rotating
    the type too would need a rotated text blit and would read as a printed
    logo instead.
    """
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)

    def rot(px, py):
        return (cx + px * ca - py * sa, cy + px * sa + py * ca)

    box = [rot(-w / 2, -h / 2), rot(w / 2, -h / 2), rot(w / 2, h / 2),
           rot(-w / 2, h / 2)]
    PA.hand_stroke(d, box, col, 9, closed=True, seed=seed, wavelength=130.0)
    inner = [rot(-w / 2 + 16, -h / 2 + 16), rot(w / 2 - 16, -h / 2 + 16),
             rot(w / 2 - 16, h / 2 - 16), rot(-w / 2 + 16, h / 2 - 16)]
    PA.hand_stroke(d, inner, col, 4, closed=True, seed=seed + 1,
                   wavelength=130.0)


def _ghost_lines(d, pts, seed, col=(216, 210, 196), width=5):
    """A shape left behind on the page, nearly gone -- beat 22."""
    PA.hand_stroke(d, pts, col, width, seed=seed, wavelength=150.0)


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

    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ---- b01  the hook: a mountain with a door in it --------------------- #
    # FRAME-FILL: the mountain is the whole frame and runs off both sides and
    # off the bottom; the character is deliberately small at the bottom edge,
    # pointing up, because the line is about the mountain, not about him.
    def c_mountain(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 5)
        pts = _mountain(d, 560, HZ + 30, 620, 96, 6)
        _archway(d, 560, HZ + 30, 150, 190, 8)
        SC.fullbody(d, 1010, 700, 430, pose='pointing', expression='awed',
                    seed=9)
    els.append(card(1, 2, c_mountain, kind='character'))
    els.append(cap(1, W // 2, 130, size=36))

    # ---- b02  the door that has no handle on this side ------------------- #
    def c_nohandle(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 11, sky=SKY, ground=ROCK)
        rock = [(-60, 720), (-60, 150), (240, 96), (700, 74), (1120, 130),
                (1340, 190), (1340, 720)]
        _mass(d, rock, ROCK, 12, width=7)
        _steel_door(d, 600, 400, 300, 470, 13, handle=False)
        SC.closeup(d, 1110, 350, 200, 'deadpan', 14)
    els.append(card(2, 3, c_nohandle, kind='character'))
    els.append(cap(2, W // 2, 660, size=32))

    # ---- b03  the name, stamped across the sky --------------------------- #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 15)
        _ridgeline(d, 520, 190, 16, col=ROCK)
        _snow_cap(d, [], 0, 17)          # no-op: keep the helper's contract clear
        D.draw_label(tile, 'MEZHGORYE', center=(640, 250), color=INK, size=96)
    els.append(card(3, 4, c_title))
    els.append(cap(3, W // 2, 690, size=30))

    # ---- b04  the frozen valley ------------------------------------------ #
    def c_valley(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _winter(tile, 19)
        _ridgeline(d, 430, 130, 20, col=SNOW_SH, width=5)
        _ridgeline(d, HZ - 10, 70, 21, col=(188, 200, 212), width=5)
        # the frozen river, a thin ribbon receding toward the horizon
        river = [(330, 720), (520, 640), (640, 560), (700, 500), (716, 462)]
        PA.fill_poly(tile, river, BLUE_W, seed=22, value=0.07, edge=1.6)
        PA.hand_stroke(d, [(330, 720), (520, 640), (640, 560), (700, 500),
                           (716, 462)], INK, 4, seed=23, wavelength=110.0)
        D.draw_label(tile, 'MAGADAN REGION', center=(950, 640), color=INK,
                     size=36)
    els.append(card(4, 5, c_valley))
    els.append(cap(4, W // 2, 140, size=32))

    # ---- b05  the winters -------------------------------------------------- #
    def c_winter(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _winter(tile, 27)
        _ridgeline(d, 400, 110, 28, col=SNOW_SH, width=5)
        # wind: long shallow curves, all leaning the same way. Wind drawn as
        # short dashes reads as rain; these read as a gale across a valley.
        for k in range(7):
            y = 440 + k * 42
            pts = []
            for i in range(9):
                u = i / 8.0
                pts.append((-40 + (W + 120) * u,
                            y + 26 * math.sin(u * 4.0 + k * 0.9)))
            PA.hand_stroke(d, pts, (176, 190, 202), 5, seed=29 + k,
                           wavelength=150.0)
        SC.fullbody(d, 260, 700, 430, pose='armscrossed', expression='scared',
                    seed=36)
    els.append(card(5, 6, c_winter, kind='character'))
    els.append(cap(5, 880, 660, size=32))

    # ---- b06-b07  the blueprint ------------------------------------------ #
    def c_blueprint_a(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _blueprint(tile, 39)
        _mountain(d, 560, 470, 520, 190, 40, col=(150, 164, 178))
        _bunker(d, 560, 300, 150, 41, decks=3, deck_h=44, tunnel_dy=[120],
                lamps=False)
        D.draw_label(tile, '1930s', center=(980, 600), color=INK, size=84)
    els.append(card(6, 7, c_blueprint_a))
    els.append(cap(6, W // 2, 690, size=30))

    def c_blueprint_b(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _blueprint(tile, 47)
        _bunker(d, 640, 220, 250, 48, decks=4, deck_h=52,
                tunnel_dy=[190, 320], lamps=False)
        # pencil dimensions: a few thin ticks along the deepest bore
        y = 220 + 12 + 320
        PA.hand_stroke(d, [(120, y + 62), (1160, y + 62)], BLUE_INK, 3,
                       seed=49, wavelength=160.0)
        for i in range(9):
            x = 140 + i * 120
            PA.hand_stroke(d, [(x, y + 48), (x, y + 76)], BLUE_INK, 3,
                           seed=50 + i, wavelength=60.0)
        _stamp(d, 1090, 600, 210, 96, -6, 51)
        D.draw_label(tile, 'GIPRONIKOM', center=(1090, 600), color=INK,
                     size=30)
    els.append(card(7, 8, c_blueprint_b))
    els.append(cap(7, W // 2, 690, size=30))

    # ---- b08  the line of prisoners, filling the width -------------------- #
    def c_line(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_face(tile, 57)
        for i, x in enumerate((-40, 150, 340, 530, 720, 910, 1100, 1290)):
            _worker(d, x, 700, 360, 60 + i, coat=(80, 88, 100))
    els.append(card(8, 9, c_line))
    els.append(cap(8, W // 2, 130, size=32))

    # ---- b09  a second line behind the first ----------------------------- #
    def c_twolines(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _rock_face(tile, 79)
        for i, x in enumerate((-30, 190, 410, 630, 850, 1070, 1290)):
            _worker(d, x, 620, 270, 80 + i, coat=(104, 96, 84))
        for i, x in enumerate((60, 300, 540, 780, 1020, 1260)):
            _worker(d, x, 730, 360, 90 + i, coat=(74, 82, 94))
        SC.fullbody(d, 1180, 250, 210, pose='standing', expression='skeptic',
                    seed=99)
    els.append(card(9, 10, c_twolines, kind='character'))
    els.append(cap(9, W // 2, 120, size=32))

    # ---- b10  the hand drill. The only beat that gets motion. ----------- #
    # WHY THE ROCK IS ITS OWN STATIC LAYER. engine3 composites a moving element
    # by rendering it to a tile, cropping to its ink, and pasting that tile at
    # (its ink origin + the motion offset). A full-bleed BACKGROUND card that
    # moves down 26px therefore slides its own top edge to y=26 and uncovers the
    # chapter's paper page for rows 0..25 -- a white strip across the top of
    # the frame, and dead centre on the band the persistent title occupies.
    # band_intrusions() reads it as a full-width bright edge crossing the title.
    # The fix is structural, not positional: the rock no longer moves. It is a
    # separate static element underneath, and only the drill -- the thing that
    # is actually being driven -- carries the motion.
    def c_rock_b10(tile, fw, fh):
        _rock_face(tile, 101)

    # THE MOTION IS THE BIT, not the whole tool. A track that translates the
    # entire drill drifts the crosspiece off the two hands that are gripping
    # it, which reads as the hands failing. Driving the drill along its own
    # shaft axis keeps the grip still and the bit working.
    def c_drill(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _hand_drill(d, 640, 400, 190, 102)
    els.append(E3.E('rock10', 'subject', c_rock_b10, at=T(10), until=T(11)))
    els.append(card(10, 11, c_drill, motion=[
        (T(10), 0, 0, 1.0, 0.0),
        (T(10) + 0.9, 0, 26, 1.0, 0.0),
        (clock.bend_of('b10'), 0, 26, 1.0, 0.0),
    ]))
    els.append(cap(10, W // 2, 690, size=32))

    # ---- b11  the empty drift and one coat on a stake --------------------- #
    def c_empty(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _winter(tile, 103)
        _ridgeline(d, 380, 80, 104, col=SNOW_SH, width=5)
        drift = [(-60, 640), (200, 596), (520, 578), (860, 596), (1160, 646),
                 (1340, 690), (1340, 780), (-60, 780)]
        _mass(d, drift, SNOW, 105, width=6)
        # a single coat on a stake, and nothing else. No footprints: the
        # absence is the subject, so nothing may be drawn where they would be.
        PA.hand_stroke(d, [(640, 600), (640, 452)], (104, 84, 60), 9,
                       seed=106, wavelength=70.0)
        coat = [(596, 452), (684, 452), (694, 556), (586, 556)]
        PA.fill_poly(tile, coat, (92, 80, 72), seed=107, value=0.08, edge=1.8)
        PA.hand_stroke(d, coat, INK, 6, closed=True, seed=108, wavelength=80.0)
        PA.hand_stroke(d, [(596, 462), (584, 500)], INK, 5, seed=109,
                       wavelength=50.0)
        PA.hand_stroke(d, [(684, 462), (696, 500)], INK, 5, seed=110,
                       wavelength=50.0)
    els.append(card(11, 12, c_empty))
    els.append(cap(11, W // 2, 250, size=32))

    # ---- b12  the plain boxes in the rock, no names ----------------------- #
    def c_boxes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 111)
        # a niche cut into the rock, holding four plain lids
        niche = [(120, 300), (900, 300), (900, 620), (120, 620)]
        PA.fill_poly(tile, niche, (128, 120, 106), seed=112, value=0.08,
                     edge=2.0)
        PA.hand_stroke(d, niche, INK, 7, closed=True, seed=113, wavelength=130.0)
        for i in range(4):
            x0 = 150 + i * 190
            lid = [(x0, 330), (x0 + 160, 330), (x0 + 160, 600), (x0, 600)]
            PA.fill_poly(tile, lid, CONC_D, seed=120 + i, value=0.07, edge=1.8)
            PA.hand_stroke(d, lid, INK, 6, closed=True, seed=130 + i,
                           wavelength=90.0)
            PA.hand_stroke(d, [(x0 + 14, 352), (x0 + 146, 352)], INK, 4,
                           seed=140 + i, wavelength=60.0)
            PA.hand_stroke(d, [(x0 + 14, 578), (x0 + 146, 578)], INK, 4,
                           seed=150 + i, wavelength=60.0)
            d.ellipse([x0 + 74, 440, x0 + 86, 452], fill=INK)   # no name plate
        SC.fullbody(d, 1130, 700, 380, pose='standing', expression='grim',
                    seed=159)
    els.append(card(12, 13, c_boxes, kind='character'))
    els.append(cap(12, W // 2, 690, size=32))

    # ---- b13  THE HERO: the buried complex in section --------------------- #
    # THE CARD THIS CHAPTER EXISTS TO DELIVER. The hill is cropped off both
    # sides so the mass is bigger than the picture; the bores run out of
    # frame so the network is bigger still. Nothing floats in dead space.
    def c_crosssection(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], SKY, seed=161, value=0.05)
        PA.fill_rect(tile, [0, 150, W, H], EARTH, seed=162, value=0.09)
        PA.paper_overlay(tile, seed=163)
        # the green hill sitting on the section, cropped at both edges.
        # TOP EDGE RULE: nothing in a card may start above y=104. engine3 draws
        # the persistent "Mezhgorye" title over the top of every finished frame,
        # so a crest at y=62 -- where this used to be -- put the hill keyline
        # straight through the word. The ground line is dropped to y=150 and the
        # crest held at 112; the section below it grew to take the space, so the
        # card is fuller than before rather than emptier.
        hill = [(-60, 156), (200, 128), (520, 112), (900, 120), (1180, 140),
                (1340, 158), (1340, 158), (-60, 158)]
        _mass(d, hill, FIELD, 164, width=6)
        PA.hand_stroke(d, [(-60, 156), (200, 128), (520, 112), (900, 120),
                           (1180, 140), (1340, 158)], INK, 7, seed=165,
                       wavelength=170.0)
        # cap_y 356 puts the dome's apex at 132 (356 - 430*0.52), i.e. 28 px of
        # earth over the blast cap, which is what "buried" has to look like.
        _bunker(d, 640, 356, 430, 166, decks=4, deck_h=76,
                tunnel_dy=[250, 340], lamps=True)
        # depth marks down the left margin, so the scale is explicit
        for k in range(5):
            y = 356 + k * 76
            PA.hand_stroke(d, [(36, y), (92, y)], INK, 4, seed=170 + k,
                           wavelength=60.0)
    els.append(card(13, 14, c_crosssection))
    els.append(cap(13, W // 2, 690, size=32, fill=RED))

    # ---- b14  the ruler: 120 km ------------------------------------------- #
    def c_ruler(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], SKY, seed=181, value=0.05)
        PA.fill_rect(tile, [0, 150, W, H], EARTH, seed=182, value=0.09)
        PA.paper_overlay(tile, seed=183)
        # Same ground line and same >=104 crest rule as b13 -- this card used to
        # run its hill keyline through the title too.
        hill = [(-60, 156), (520, 112), (1340, 158), (1340, 158), (-60, 158)]
        _mass(d, hill, FIELD, 184, width=6)
        PA.hand_stroke(d, [(-60, 156), (520, 112), (1340, 158)], INK, 7,
                       seed=185, wavelength=170.0)
        # cap_h=170 flattens the dome so its apex sits at 130 instead of 26, and
        # cap_y=300 keeps the whole shell under the new ground line. The shallower
        # deck stack is what buys the red ruler its own band at the bottom of the
        # frame instead of hanging it off the bottom edge, where it used to sit.
        _bunker(d, 640, 300, 430, 186, decks=4, deck_h=62, cap_h=170,
                tunnel_dy=[90, 175], lamps=False)
        y = 700
        PA.hand_stroke(d, [(70, y), (1210, y)], RED, 8, seed=187,
                       wavelength=180.0)
        for k in range(13):
            x = 70 + k * 95
            PA.hand_stroke(d, [(x, y - 16), (x, y + 16)], RED, 5,
                           seed=190 + k, wavelength=60.0)
        D.draw_arrow(tile, (70, y), (1210, y), color=RED, width=8, head=40)
        D.draw_number(tile, '120', center=(640, 585), color=RED, size=130)
        D.draw_label(tile, 'KILOMETRES', center=(640, 665), color=INK,
                     size=40)
    els.append(card(14, 15, c_ruler))
    els.append(cap(14, 300, 160, size=32, fill=RED))

    # ---- b15  the wide chambers, both sides ------------------------------- #
    def c_chambers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 201)
        y = 380
        bore = [(-60, y - 90), (1340, y - 90), (1340, y + 90), (-60, y + 90)]
        PA.fill_poly(tile, bore, DARK, seed=202, value=0.03, edge=1.8)
        PA.hand_stroke(d, [(-60, y - 90), (1340, y - 90)], INK, 7, seed=203,
                       wavelength=180.0)
        PA.hand_stroke(d, [(-60, y + 90), (1340, y + 90)], INK, 7, seed=204,
                       wavelength=180.0)
        _chamber(d, 210, y, 320, 300, 205, door_side=1)
        _chamber(d, 1070, y, 320, 300, 206, door_side=-1)
        # The third chamber hung at cy=130 with its lid at y=5 -- off the top of
        # the frame and straight through the title -- and it floated 35 px clear
        # of the bore anyway. Dropped to cy=250/h=230 so its roof is at y=135
        # and its floor runs down INTO the bore, which is also what a chamber
        # off this tunnel is supposed to look like.
        _chamber(d, 640, 250, 280, 230, 207, door_side=1)
        D.draw_label(tile, 'chambers', center=(640, 640), color=INK, size=38)
    els.append(card(15, 16, c_chambers))
    els.append(cap(15, W // 2, 700, size=32))

    # ---- b16  power, water, housing --------------------------------------- #
    def c_services(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 209)
        rock = [(-60, 0), (1340, 0), (1340, 150), (900, 168), (400, 168),
                (-60, 150)]
        PA.fill_poly(tile, rock, EARTH_D, seed=210, value=0.08, edge=2.0)
        PA.hand_stroke(d, [(-60, 150), (400, 168), (900, 168), (1340, 150)],
                       INK, 7, seed=211, wavelength=170.0)
        for i, x in enumerate((250, 640, 1030)):
            _chamber(d, x, 430, 300, 330, 220 + i, door_side=1)
        _coil_icon(d, 250, 430, 105, 230)
        _tank_icon(d, 640, 430, 105, 231)
        _bunk_icon(d, 1030, 430, 100, 232)
        SC.fullbody(d, 90, 720, 400, pose='pointing', expression='awed',
                    seed=233)
    els.append(card(16, 17, c_services, kind='character'))
    els.append(cap(16, W // 2, 690, size=32))

    # ---- b17  the fortress above ground ------------------------------------ #
    def c_fortress(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 239, sky=SKY, ground=SNOW)
        ridge = [(-60, 640), (240, 590), (640, 560), (1040, 596), (1340, 640),
                 (1340, 780), (-60, 780)]
        _mass(d, ridge, ROCK, 240, width=7)
        _snow_cap(d, ridge[:5], 600, 241)
        _fortress(d, 620, 592, 900, 420, 242, slits=6)
    els.append(card(17, 18, c_fortress))
    els.append(cap(17, W // 2, 690, size=32))

    # ---- b18  the slit, and no door anywhere ----------------------------- #
    def c_slit(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _exterior(tile, 249, sky=SKY, ground=SNOW)
        # The wall's coping used to start at y=30, so its 8 px keyline crossed
        # the whole title. Dropped to a 122 coping and the masonry courses moved
        # down with it; the wall still runs off both sides and the bottom, so it
        # owns more of the frame than before, not less.
        wall = [(-60, 780), (-60, 152), (400, 122), (1340, 140), (1340, 780)]
        _mass(d, wall, CONCRETE, 250, width=8)
        for i in range(6):
            y = 200 + i * 100
            PA.hand_stroke(d, [(-60, y), (1340, y + 18)], CONC_D, 5,
                           seed=260 + i, wavelength=150.0)
        # one slit, cut deep: a splayed embrasure, dark all the way through
        sx, sy = 640, 360
        slit = [(sx - 26, sy - 150), (sx + 26, sy - 150), (sx + 66, sy + 150),
                (sx - 66, sy + 150)]
        PA.fill_poly(tile, slit, (46, 44, 48), seed=266, value=0.03, edge=1.6)
        PA.hand_stroke(d, slit, INK, 8, closed=True, seed=267, wavelength=110.0)
        # cold coming through it
        for k in range(5):
            y = sy - 110 + k * 56
            pts = [(sx + 60, y), (sx + 300, y - 26 + k * 6),
                   (sx + 560, y - 44 + k * 10)]
            PA.hand_stroke(d, pts, BLUE_W, 7, seed=270 + k, wavelength=150.0)
        D.draw_label(tile, 'no door', center=(980, 640), color=RED, size=44)
    els.append(card(18, 19, c_slit))
    els.append(cap(18, 250, 640, size=32, fill=RED))

    # ---- b19  the only way in: rail --------------------------------------- #
    def c_railin(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DARK, seed=279, value=0.06)
        PA.paper_overlay(tile, seed=280)
        # A tunnel card is near-black to the top edge, so the near-black title
        # has nothing to read against (see scene_common.title_backdrop). A lit
        # stone course goes down first so the art stays ON TOP of it.
        SC.title_backdrop(tile, 1279, col=(98, 94, 106))
        mouth = 520
        PA.fill_poly(tile, [(-60, 0), (mouth - 150, 0), (mouth - 190, 720),
                            (-60, 720)], (52, 50, 54), seed=281, value=0.05,
                     edge=1.6)
        _bore(d, mouth + 130, 400, W + 40, 300, 400, 180, 282, lamps=2)
        _rail(d, 380, 720, 300, mouth + 150, 400, 60, 283, ties=9)
        SC.fullbody(d, 250, 660, 400, pose='sitting', expression='deadpan',
                    seed=284)
    els.append(card(19, 20, c_railin, kind='character'))
    els.append(cap(19, 950, 640, size=32))

    # ---- b20  the same line from the side ---------------------------------- #
    def c_raildeep(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 289, base=(112, 106, 94))
        _bore(d, -40, 400, 900, 380, 300, 210, 290, lamps=2)
        _rail(d, 60, 560, 220, 900, 380, 54, 291, ties=10)
        # and nothing else anywhere -- no road, no second line
        D.draw_label(tile, 'the only line', center=(1050, 560), color=INK,
                     size=36)
    els.append(card(20, 21, c_raildeep))
    els.append(cap(20, W // 2, 690, size=32))

    # ---- b21  the road that stops at a cliff ------------------------------ #
    def c_noroad(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], SKY, seed=299, value=0.05)
        PA.paper_overlay(tile, seed=300)
        # the ground stops dead at x=900 and falls away
        ground = [(-60, 300), (240, 268), (560, 252), (900, 268), (900, 780),
                  (-60, 780)]
        _mass(d, ground, FIELD, 301, width=7)
        # the road, drawn on top, running right and stopping at the edge
        road = [(-60, 330), (300, 306), (620, 292), (880, 306), (880, 366),
                (620, 352), (300, 366), (-60, 390)]
        PA.fill_poly(tile, road, (146, 140, 132), seed=302, value=0.07, edge=2.0)
        PA.hand_stroke(d, [(-60, 330), (300, 306), (620, 292), (880, 306)],
                       INK, 6, seed=303, wavelength=170.0)
        PA.hand_stroke(d, [(-60, 390), (300, 366), (620, 352), (880, 366)],
                       INK, 6, seed=304, wavelength=170.0)
        for k in range(7):
            u = k / 6.0
            x = -20 + u * 880
            y = 330 + (306 - 330) * u
            PA.hand_stroke(d, [(x, y), (x + 60, y + 2)], SNOW, 5,
                           seed=305 + k, wavelength=60.0)
        # the drop, and the blunt stop-mark where the road ends
        drop = [(900, 268), (980, 420), (940, 560), (900, 780)]
        _mass(d, drop, FIELD_D, 306, width=6)
        PA.hand_stroke(d, [(880, 262), (880, 372)], RED, 11, seed=307,
                       wavelength=60.0)
        D.draw_label(tile, 'NO ROAD', center=(520, 540), color=RED, size=76)
    els.append(card(21, 22, c_noroad))
    els.append(cap(21, W // 2, 690, size=32, fill=RED))

    # ---- b22  the page forgets it ------------------------------------------ #
    def c_forgot(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _page(tile, 309)
        # the road and the cliff, one shade off the paper -- present, gone
        _ghost_lines(d, [(-60, 330), (300, 306), (620, 292), (880, 306)], 310)
        _ghost_lines(d, [(-60, 390), (300, 366), (620, 352), (880, 366)], 311)
        _ghost_lines(d, [(900, 268), (980, 420), (940, 560), (900, 780)], 312)
        D.draw_label(tile, 'NO ROAD', center=(520, 540), color=(214, 208, 194),
                     size=76)
        SC.fullbody(d, 1010, 700, 480, pose='shrug', expression='deadpan',
                    seed=313)
    els.append(card(22, 23, c_forgot, kind='character'))
    els.append(cap(22, 380, 660, size=32))

    # ---- b23  the stamp ---------------------------------------------------- #
    def c_stamp(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _page(tile, 319)
        # a form with most of its lines blanked out, then the stamp on top
        for k in range(7):
            y = 120 + k * 62
            PA.hand_stroke(d, [(140, y), (1140, y)], (216, 210, 196), 4,
                           seed=320 + k, wavelength=150.0)
        _stamp(d, 640, 360, 720, 300, -8, 330)
        D.draw_label(tile, 'CLOSED', center=(640, 360), color=RED, size=120)
    els.append(card(23, 24, c_stamp))
    els.append(cap(23, W // 2, 660, size=32, fill=RED))

    # ---- b24  the rumour on the tunnel wall -------------------------------- #
    def c_rumour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 339, base=(104, 100, 94))
        wall = [(-60, 0), (1340, 0), (1340, 720), (-60, 720)]
        _mass(d, wall, (120, 114, 106), 340, width=7)
        for k, (x0, y0, x1, y1) in enumerate(((200, 40, 300, 300),
                                              (760, 460, 840, 700))):
            pts = []
            for i in range(7):
                u = i / 6.0
                pts.append((x0 + (x1 - x0) * u + 16 * math.sin(u * 6 + k),
                            y0 + (y1 - y0) * u))
            PA.hand_stroke(d, pts, (92, 88, 82), 5, seed=350 + k,
                           wavelength=90.0)
        _mushroom_cloud(d, 640, 300, 190, 353)
        D.draw_label(tile, 'NUCLEAR?', center=(300, 300), color=RED_L,
                     size=54)
        # half of it struck out -- the rumour is denied, not deleted
        PA.hand_stroke(d, [(760, 190), (1120, 400)], INK, 16, seed=360,
                       wavelength=140.0)
        PA.hand_stroke(d, [(1120, 190), (760, 400)], INK, 16, seed=361,
                       wavelength=140.0)
    els.append(card(24, 25, c_rumour))
    els.append(cap(24, W // 2, 640, size=32))

    # ---- b25  the empty table ---------------------------------------------- #
    def c_table(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 369, base=(96, 92, 88))
        room = [(-60, 120), (1340, 120), (1340, 700), (-60, 700)]
        PA.fill_poly(tile, room, (122, 116, 108), seed=370, value=0.08,
                     edge=2.0)
        PA.hand_stroke(d, [(-60, 120), (1340, 120)], INK, 8, seed=371,
                       wavelength=180.0)
        for k in range(4):
            # TOP EDGE RULE. These lamps were at cy=66, which put their tops at
            # y=40 -- inside the band engine3 stamps the persistent title into.
            # They were also drawn ABOVE the room's ceiling line at y=120, so
            # they floated in the rock rather than hanging in the room. cy=176
            # fixes both: the lamps now hang just under the ceiling they light,
            # and their tops are at y=150.
            PA.fill_poly(tile, PA.ellipse_pts(240 + k * 270, 176, 26, 26, n=20),
                         LAMP, seed=372 + k, value=0.10, edge=1.2)
        _table_and_chairs(d, 640, 440, 900, 380)
        SC.fullbody(d, 1120, 690, 340, pose='standing', expression='awed',
                    seed=390)
    els.append(card(25, 26, c_table, kind='character'))
    els.append(cap(25, W // 2, 690, size=32))

    # ---- b26  nothing on paper --------------------------------------------- #
    def c_nothing(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _page(tile, 391)
        SC.fullbody(d, 430, 740, 620, pose='shrug', expression='deadpan',
                    seed=392)
        D.draw_bubble(tile, 'nothing on paper', xy=(1010, 250),
                      tail_to=(640, 380), font_size=34, max_w=520)
    els.append(card(26, 27, c_nothing, kind='character'))
    els.append(cap(26, W // 2, 700, size=32))

    # ---- b27  the fortress from far below ---------------------------------- #
    # The rock owns the frame; the fortress is small against it, which is the
    # point of "seen from far below". Frame-fill comes from the rock, not from
    # the fortress, so nothing is left floating in an empty sky.
    def c_farbelow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], SKY, seed=401, value=0.05)
        PA.paper_overlay(tile, seed=402)
        cliff = [(-60, 90), (300, 84), (700, 96), (1000, 88), (1340, 96),
                 (1340, 780), (-60, 780)]
        _mass(d, cliff, ROCK, 403, width=7)
        _snow_cap(d, cliff[:5], 100, 404)
        for k in range(6):
            y = 180 + k * 96
            pts = []
            for i in range(7):
                u = i / 6.0
                pts.append((140 + 900 * u, y + 18 * math.sin(u * 5 + k)))
            PA.hand_stroke(d, pts, ROCK_D, 5, seed=410 + k, wavelength=120.0)
        _fortress(d, 700, 260, 340, 140, 420, slits=4, wall_only=True)
        D.draw_label(tile, 'STILL STANDING', center=(330, 600), color=RED,
                     size=40)
    els.append(card(27, 28, c_farbelow))
    els.append(cap(27, 1000, 620, size=32, fill=RED))

    # ---- b28  the drift over the gate --------------------------------------- #
    def c_buried(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _winter(tile, 429)
        wall = [(-60, 430), (240, 400), (640, 386), (1040, 402), (1340, 430),
                (1340, 700), (-60, 700)]
        _mass(d, wall, CONCRETE, 430, width=7)
        for i in range(3):
            y = 300 + i * 54
            PA.hand_stroke(d, [(-60, y), (1340, y + 10)], CONC_D, 4,
                           seed=440 + i, wavelength=150.0)
        for i in range(5):
            u = (i + 0.5) / 5.0
            x = 640 + (u - 0.5) * 700
            sl = [(x - 12, 330), (x + 12, 330), (x + 12, 400), (x - 12, 400)]
            PA.fill_poly(tile, sl, (46, 44, 48), seed=450 + i, value=0.03,
                         edge=1.2)
            PA.hand_stroke(d, sl, INK, 4, closed=True, seed=460 + i,
                           wavelength=50.0)
        # the drift: it takes the bottom two thirds and only the top shows
        drift = [(-60, 700), (-60, 600), (180, 540), (480, 512), (800, 528),
                 (1080, 570), (1340, 624), (1340, 780), (-60, 780)]
        _mass(d, drift, SNOW, 470, width=7)
        _snow_cap(d, drift[:7], 540, 471, col=(250, 250, 252))
    els.append(card(28, 29, c_buried))
    els.append(cap(28, W // 2, 180, size=32))

    # ---- b29  the tunnel, unchanged ---------------------------------------- #
    def c_unchanged(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _underground(tile, 479, base=(98, 94, 90))
        PA.fill_rect(tile, [0, 0, W, H], DARK, seed=480, value=0.06)
        PA.paper_overlay(tile, seed=481)
        rock = [(-60, 0), (1340, 0), (1340, 90), (-60, 90)]
        _mass(d, rock, (116, 110, 102), 482, width=6)
        _bore(d, 180, 430, 1180, 400, 560, 210, 483, lamps=3)
        SC.fullbody(d, 300, 700, 420, pose='standing', expression='grim',
                    seed=484)
    els.append(card(29, 30, c_unchanged, kind='character'))
    els.append(cap(29, W // 2, 690, size=32))

    # ---- b30  the door again, and nobody has gone in ----------------------- #
    def c_still_shut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _winter(tile, 489)
        rock = [(-60, 780), (-60, 0), (1340, 0), (1340, 780)]
        _mass(d, rock, ROCK, 490, width=7)
        _snow_cap(d, [(60, 96), (300, 74), (640, 92), (980, 72), (1220, 94)],
                  110, 491)
        _archway(d, 640, 500, 480, 620, 492)
        _steel_door(d, 640, 400, 300, 470, 493, handle=False)
        # THE TITLE, and it has to go UNDER nothing and OVER the archway. The
        # archway's DARK fill is 620 tall on a 500 base, so it runs from y=-120
        # straight through the whole title band and swallows a backdrop laid
        # down with the background fills -- measured, the band still read 1.44
        # with one there. Same re-raise vatican uses after its own architecture
        # (see _dark). It lands as a concrete roof slab over the buried door,
        # which is what the mass would be anyway, and the snow line and the
        # rock either side of the arch are untouched: the course is 86 tall and
        # their edge is at y=74-110.
        SC.title_backdrop(tile, 1489, col=(98, 94, 106))
        SC.fullbody(d, 320, 720, 420, pose='standing', expression='deadpan',
                    seed=494)
    els.append(card(30, 31, c_still_shut, kind='character'))
    els.append(cap(30, 1000, 660, size=32, fill=RED))

    return SC.finish(els, TITLE, clock, title_seed=29)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))