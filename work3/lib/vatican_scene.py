"""vatican scene -- the Vatican Archives, sealed under Vatican City.

Chapter 9 of the bunker film. Everything structural -- caption handoff, one
card per beat, phrase clock, the cropped character close-up, the render drivers
-- comes from scene_common; this file declares only the Vatican's 38 cards.

ONE CARD PER BEAT, AND EACH CARD PAINTS ITS OWN WHOLE FRAME. beats.json gives
every one of the 38 sentences an exact [start,end] and every line is short
enough (<=8 words) that the phrase splitter leaves it as ONE phrase, so the
card boundary and the caption boundary are the same instant. Every card
function fills its tile background-first, which makes it structurally
impossible for one card's art to survive into the next.

THE CHAPTER IS ALL INTERIOR AND ALL DIM, SO THE CHARACTER IS DRAWN CREAM-ON-
DARK. The v3 presenter is dark-ink by default, which is right for a bright
exterior and wrong here -- a black stickman in a black archive is a hole in the
frame, not a person. `figure()` below wraps character3 the same way
scene_common.fullbody does but passes the ink and face fills explicitly, so the
figure reads as a cream silhouette against near-black on every card. This is the
same rule CLAUDE.md STYLE_CANON states: the character is drawn light-on-dark in
the dark register. Cards that use the bright PAPER register (documents, index
cards, the microfilm reel) get the dark-ink figure instead, so there is one
local `figure(...)` and every card names its own theme.

FRAME-FILL. Every interior card lets the room, the shelf run, or the document run
past a frame edge; the subject is scaled to dominate and is CROPPED BY an edge
rather than parked small in the middle. The recurring defect in this project is
a small subject centred in empty space.

THE HERO IMAGES. (b08) the shelves receding for kilometres, (b30) a lone reader
lost between two towering shelf runs -- the emotional image of the chapter, the
figure dwarfed and cropped by both shelf edges -- and (b38) the finale, the
character swallowed by the absolute dark with only the eyes holding out.

CADENCE. Still-dominant, one cut per sentence (38 cuts in 92s). No motion
tracks; the reference is still-dominant and the single thing the narrator calls
moving (a ladder sliding, a hand offering a key) is drawn as a held pose.

Run:  python lib/vatican_scene.py --preview
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import engine3 as E3
import scene_common as SC
import character3 as C3
import v2paint as PA
import v2subjects as S
import v2draw as D
import v2type as T

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'vatican'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'The Vatican Archives'

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# The register is DIM AND WARM. One ink, one aged-paper cream, one dark wood,
# one oxblood accent, one lamp-gold note, and a near-black the whole chapter
# lives in. The red is spent only on the things the narration calls forbidden:
# the sealed door's seal, the refused camera, the 1939 stamp, the key.
INK = SC.INK
NIGHT = (26, 21, 20)            # the near-black the archive lives in
DEEP = (40, 32, 30)             # a lifted black, for the far end of a corridor
DEEPER = (18, 15, 15)           # the darkest value, for door voids and the finale
CREAM = (238, 228, 206)         # aged paper cream -- the LIGHT-on-dark colour
PAPER = (246, 240, 224)         # a brighter document page
PAPER_D = (216, 206, 186)       # a shaded page / cardboard
WOOD = (92, 68, 52)             # dark shelf wood
WOOD_L = (122, 92, 68)          # the lit face of a shelf plank
WOOD_D = (62, 46, 38)           # the shadowed side of a shelf
OXBLOOD = (132, 34, 40)         # the one deep accent (the seal, the NO)
LAMP = (238, 198, 122)          # the one warm light note
STONE = (118, 106, 96)          # the tunnel / stonework
STONE_D = (86, 78, 72)          # shadowed stone

FLOOR = int(H * 0.80)           # the interior floor line for most cards

# Declared to _coverage_gate.band_intrusions. This chapter's title backdrop IS
# the lintel: the engine stamps the chapter title in hardcoded INK on every frame
# and cannot be changed for one chapter, so on a near-black card the art has to
# supply something for that ink to read against. The lintel is that something,
# and it necessarily occupies the title band. Only the part of the lintel inside
# the band is declared, and the gate still fires on any row with structure in it,
# so this cannot be used to excuse art. See _lintel's docstring.
TITLE_BACKDROP = (10, 73)


# ---------------------------------------------------------------------------
# the character, themed for the register (see the module docstring)
# ---------------------------------------------------------------------------

def figure(d, x, feet_y, height, pose='standing', expression='neutral', seed=0,
           dark=False, shoulder_ink=None):
    """The v3 presenter, cream-on-dark or ink-on-light.

    Mirrors scene_common.fullbody (character3's primitives take an Image, so
    the caller's Draw is recovered with PA.img_of) but adds the two fill
    overrides the dim register needs. `dark=True` means "the frame around this
    figure is the light PAPER register", so the figure goes back to dark ink.
    """
    ink = INK if dark else CREAM
    face = PAPER if dark else CREAM
    C3.draw_character(PA.img_of(d), x, feet_y, height, pose=pose,
                      expression=expression, seed=seed, ink=ink,
                      head_fill=ink, face_fill=face)


def face(d, cx, cy, r, expression, seed, shoulder=1.0, dark=False):
    """A cropped head-and-shoulders, themed to match `figure`.

    scene_common.closeup hardcodes the INK bust, which is right on the bright
    register and wrong here: on a near-black card an ink bust is a hole in the
    frame. So the bust mass is drawn here in the register's own figure colour
    and the head is handed to character3 with the matching face fill.
    """
    if shoulder > 0:
        img = PA.img_of(d)
        jy = cy + r * 0.92
        w = r * 1.55 * shoulder
        top = []
        n = 33
        for i in range(n + 1):
            u = i / float(n)
            bx = cx - w + 2.0 * w * u
            t = (u - 0.5) * 2.0
            top.append((bx, jy + r * (0.30 * (t ** 2) + 0.10 * abs(t))))
        bust = top + [(cx + w, 830), (cx - w, 830)]
        PA.fill_poly(img, bust, INK if dark else CREAM, seed=seed + 48,
                     value=0.0, tint=0.0, band=0.0, edge=0.0, grow=2)
        PA.hand_stroke(ImageDraw.Draw(img), top, INK if dark else CREAM,
                       max(5, int(r * 0.05)), closed=False, seed=seed + 49,
                       wavelength=160.0, vary=0.30)
    C3.draw_head(PA.img_of(d), cx, cy, r, expression=expression, seed=seed,
                 lw=max(5, int(round(r * 0.13))),
                 face_fill=PAPER if dark else CREAM)


# ---------------------------------------------------------------------------
# backgrounds
# ---------------------------------------------------------------------------

def _lintel(tile, seed, col=(104, 92, 78), x0=0, x1=W, dim=1.0):
    """A lit stone lintel across the top of a dark card.

    NOW A THIN WRAPPER over scene_common.title_backdrop. It used to be a local
    two-course beam (a full-value head course plus a 0.55x course below it). That
    richer version has a value seam at y=58 -- INSIDE the title band -- and the
    two courses differ by ~45 levels, far past the intrusion gate's DEV=25. So
    every band row failed the "uniform end to end" test that TITLE_BACKDROP's
    exemption relies on, and the gate reported the lintel itself as art striking
    through the title on31 of 38 beats. The shared helper paints ONE uniform
    low-texture course, which is what makes the exemption work without weakening
    it. The masonry joints below the band still carry the cut-stone read.

    Keep the local name: several card functions call `_lintel` directly (see
    _dark, c_manyrecords, c_absolute), and they should not each have to change.
    """
    SC.title_backdrop(tile, seed, col=col, x0=x0, x1=x1, dim=dim)


def _dark(tile, seed, top=NIGHT, floor_col=DEEP, hz=FLOOR, lintel=True):
    """The default dim interior: warm near-black above, a lifted dark floor.

    Two overlapping fills, never two abutting rects (fill_rect wobbles its own
    edges, so abutting rects leave a pale seam -- see cheyenne's _sky).

    The lintel goes on FIRST, so a card that paints its own architecture over
    the top of the frame has to re-raise it with an explicit `_lintel(...)`
    after its own fills -- see c_manyrecords and c_absolute for the pattern.
    """
    PA.fill_rect(tile, [0, 0, W, H], top, seed=seed, value=0.10)
    PA.fill_rect(tile, [0, hz - 6, W, H], floor_col, seed=seed + 1, value=0.09)
    if lintel:
        _lintel(tile, seed + 3)
    PA.paper_overlay(tile, seed=seed + 2)


def _light(tile, seed, base=PAPER):
    """The bright PAPER register, for document/index-card cards."""
    PA.fill_rect(tile, [0, 0, W, H], base, seed=seed, value=0.05)
    PA.paper_overlay(tile, seed=seed + 1)


# ---------------------------------------------------------------------------
# signature objects
# ---------------------------------------------------------------------------

def _stock_row(d, x0, x1, top, bot, seed, count):
    """One shelf slot packed with a row of archive boxes.

    WHY AN IRREGULAR TOP EDGE. A flat band of colour with vertical ticks reads
    as a painted stripe; the same band under a STEPPED, hand-drawn top profile
    reads as a row of boxes of different heights, and that is the thing which
    says "archive" at a glance. The stepped profile is stroked as one polyline,
    so every box's top edge AND every gap between boxes come out of a single
    stroke -- a full slot costs two operations however many boxes are in it.

    WHY THE BOXES SIT LOW IN THE SLOT. Filling the slot wall to wall left no
    dark recess above them and the whole run read as one wall of tan mush
    rather than as shadowed shelving (the first b03 render). Real boxes stand
    on the plank and the shadow sits above them, so the row occupies the lower
    ~60% and the slot keeps its darkness.
    """
    img = PA.img_of(d)
    h = bot - top
    if h < 16 or x1 - x0 < 60:
        return
    base = bot - 2.0
    bh = h * 0.58
    span = (x1 - x0) / float(max(1, count))
    prof = [(x0, base)]
    for k in range(max(1, count)):
        bx0 = x0 + span * k
        bx1 = bx0 + span * 0.84          # a real gap between boxes
        ty = base - bh * (0.74 + 0.13 * ((k * 5) % 3))
        prof.append((bx0, ty))
        prof.append((bx1, ty))
        prof.append((bx1, base))
        if k + 1 < count:
            prof.append((x0 + span * (k + 1), base))
    prof.append((x1, base))
    PA.fill_poly(img, prof + [(x1, bot), (x0, bot)], (150, 140, 124),
                 seed=seed, value=0.08)
    PA.hand_stroke(d, prof, INK, 4, closed=False, seed=seed + 1,
                   wavelength=60.0)


def _shelf_run(d, x_left, x_right, base_y, top_y, seed, shelves=7, depth=0,
               stock=0):
    """A wall of shelving: uprights + horizontal planks, cropped by the frame.

    The plank rhythm is what says "archive" -- evenly spaced horizontals with a
    vertical upright every couple of bays and dark slots between them.

    `stock` turns on `_stock_row` in each slot. WITHOUT IT a shelf run reads as
    SCAFFOLD rather than as an archive: evenly spaced horizontals with dark gaps
    and nothing at all in the gaps, which was the b03 finding. It is left off
    where the shelves are meant to read as bare structure -- the two runs in
    c_lost, which run away into near-darkness faster than anything on them could
    be read, and the empty run behind the index card in c_whole_record.

    GEOMETRY WORTH KNOWING BEFORE CALLING IT. The first plank sits AT `top_y`
    and each slot is the gap ABOVE its plank, so the topmost boxes reach up to
    `top_y - step + 10` -- i.e. they sit ABOVE `top_y` by nearly a full step.
    With a short, tall run (`top_y` small next to `step`) that row lands in the
    top ~100px of the frame and buries the engine's INK chapter title. Every
    call whose run reaches the title band either sets `top_y` high enough to
    clear it, or re-raises `_lintel` afterwards (see c_manyrecords,
    c_absolute). b20 lost its whole bright register to this before it dropped
    the shelf run entirely.

    THE CLAMP AT THE TOP OF THE BODY IS THE FIX, AND IT IS HERE RATHER THAN AT
    EACH CALL SITE because the uprights had their own separate path. The planks
    are called out in the paragraph above, so callers learned to pass a high
    `top_y`; but the uprights are drawn from `top_y - 6` independently, and four
    call sites (b10, b16, b17, b35) still ran them from the very top of the
    frame. Those four verticals crossed the persistent title band, and on a dark
    archive card the band is dark brown already, so a dark stroke on it is very
    low contrast -- "The Vatican Archives" was legible but muddy, with shelf
    posts running through it. Clamping once, here, means a caller cannot
    reintroduce the bug by forgetting a parameter it did not know was load
    bearing.
    """
    top_y = max(int(top_y), 104)
    img = PA.img_of(d)
    span = x_right - x_left
    # back panel, a touch darker than the wall, so the slots read as recesses
    PA.fill_rect(img, [x_left, top_y, x_right, base_y], WOOD_D, seed=seed,
                 value=0.06)
    step = (base_y - top_y) / float(shelves)
    n_box = max(6, min(26, int(span / 46.0)))
    for i in range(shelves + 1):
        yy = top_y + i * step
        PA.hand_stroke(d, [(x_left, yy), (x_right, yy - depth)], WOOD_L, 9,
                       closed=False, seed=seed + 10 + i, wavelength=140.0)
        # the dark slot above each plank: the recess the boxes sit in
        if i < shelves:
            PA.fill_rect(img, [x_left + 4, yy - step + 6, x_right - 4,
                               yy - step * 0.18], DEEPER, seed=seed + 30 + i,
                         value=0.05)
            if stock:
                _stock_row(d, x_left + 8, x_right - 8, yy - step + 10,
                           yy - step * 0.22, seed + 60 + i, n_box)
    # uprights
    n_up = max(2, int(span / 150))
    for k in range(n_up + 1):
        ux = x_left + span * k / float(n_up)
        PA.hand_stroke(d, [(ux, top_y - 6), (ux - depth, base_y)], WOOD, 12,
                       closed=False, seed=seed + 50 + k, wavelength=120.0)


def _corridor(d, cx, vp_y, seed, warm=DEEP):
    """A one-point-perspective corridor: two converging wall/ceiling/floor runs
    converging on a lit far end, which is what says "the stacks run deep".

    The walls and the floor are four filled trapezoids meeting at the vanishing
    point, cropped by all four frame edges, so the corridor IS the frame."""
    img = PA.img_of(d)
    # the far end, a small lit rectangle at the vanishing point
    PA.fill_poly(img, [(cx - 70, vp_y - 80), (cx + 70, vp_y - 80),
                       (cx + 70, vp_y + 80), (cx - 70, vp_y + 80)],
                 LAMP, seed=seed, value=0.06)
    # ceiling, floor, and the two walls, each a converging trapezoid
    PA.fill_poly(img, [(-40, -30), (W + 40, -30), (cx + 70, vp_y - 80),
                       (cx - 70, vp_y - 80)], (52, 42, 40), seed=seed + 1,
                 value=0.07)
    PA.fill_poly(img, [(-40, 740), (W + 40, 740), (cx + 70, vp_y + 80),
                       (cx - 70, vp_y + 80)], warm, seed=seed + 2, value=0.07)
    PA.fill_poly(img, [(-40, -30), (cx - 70, vp_y - 80), (cx - 70, vp_y + 80),
                       (-40, 740)], (56, 45, 42), seed=seed + 3, value=0.07)
    PA.fill_poly(img, [(W + 40, -30), (cx + 70, vp_y - 80),
                       (cx + 70, vp_y + 80), (W + 40, 740)], (44, 35, 34),
                 seed=seed + 4, value=0.07)
    # the four converging corner lines, drawn heavy
    corners = [((-40, -30), (cx - 70, vp_y - 80)),
               ((W + 40, -30), (cx + 70, vp_y - 80)),
               ((-40, 740), (cx - 70, vp_y + 80)),
               ((W + 40, 740), (cx + 70, vp_y + 80))]
    for k, (a, b) in enumerate(corners):
        PA.hand_stroke(d, [a, b], INK, 5, closed=False, seed=seed + 10 + k,
                       wavelength=150.0)
    PA.hand_stroke(d, [(cx - 70, vp_y - 80), (cx + 70, vp_y - 80),
                       (cx + 70, vp_y + 80), (cx - 70, vp_y + 80)],
                   INK, 6, closed=True, seed=seed + 14, wavelength=110.0)
    # The near architrave across the mouth of the corridor. It has to go on
    # AFTER the ceiling trapezoid, which paints over the whole top of the frame
    # and would otherwise bury the lintel -- and the engine's INK chapter title
    # needs it (see _lintel). Architecturally it is also the right thing: a beam
    # across the near end of a corridor makes the run behind it read as deeper.
    _lintel(img, seed + 20)
    return (cx, vp_y)


def _big_door(d, cx, cy, w, h, seed, open_frac=1.0):
    """The archive door: a heavy slab in a stone frame. `open_frac` < 1 leaves a
    dark gap where it has swung/shut, which is the only thing that reads as
    sealing or opening."""
    img = PA.img_of(d)
    # the stone frame
    frame = [(cx - w * 0.60, cy - h * 0.58), (cx + w * 0.60, cy - h * 0.58),
             (cx + w * 0.60, cy + h * 0.60), (cx - w * 0.60, cy + h * 0.60)]
    PA.fill_poly(img, frame, STONE_D, seed=seed, value=0.08)
    PA.hand_stroke(d, frame, INK, 8, closed=True, seed=seed + 1, wavelength=150.0)
    # the void behind, and the door slab(s)
    if open_frac < 0.55:
        # OPEN: a dark gap in the middle where the slab has slid/swung aside
        void = [(cx - w * 0.30, cy - h * 0.44), (cx + w * 0.30, cy - h * 0.44),
                (cx + w * 0.30, cy + h * 0.44), (cx - w * 0.30, cy + h * 0.44)]
        PA.fill_poly(img, void, DEEPER, seed=seed + 2, value=0.06)
        PA.hand_stroke(d, void, INK, 5, closed=True, seed=seed + 3,
                       wavelength=100.0)
        # a warm sliver of lit room beyond the gap
        PA.fill_rect(img, [cx - w * 0.06, cy - h * 0.36, cx + w * 0.06,
                           cy + h * 0.36], LAMP, seed=seed + 4, value=0.06)
    else:
        # CLOSED: the slab fills the opening, ribbed, with the seal line
        slab = [(cx - w * 0.44, cy - h * 0.44), (cx + w * 0.44, cy - h * 0.44),
                (cx + w * 0.44, cy + h * 0.44), (cx - w * 0.44, cy + h * 0.44)]
        PA.fill_poly(img, slab, WOOD, seed=seed + 2, value=0.08)
        PA.hand_stroke(d, slab, INK, 7, closed=True, seed=seed + 3,
                       wavelength=140.0)
        for k in range(5):
            yy = cy - h * 0.32 + k * h * 0.16
            PA.hand_stroke(d, [(cx - w * 0.38, yy), (cx + w * 0.38, yy)],
                           WOOD_L, 5, closed=False, seed=seed + 10 + k,
                           wavelength=60.0)
        # THE SEAL: a heavy oxblood gasket down the middle
        PA.hand_stroke(d, [(cx, cy - h * 0.44), (cx, cy + h * 0.44)], OXBLOOD,
                       8, closed=False, seed=seed + 20, wavelength=120.0)
        PA.hand_stroke(d, [(cx - w * 0.44, cy), (cx + w * 0.44, cy)], OXBLOOD,
                       7, closed=False, seed=seed + 21, wavelength=120.0)


def _page(d, cx, cy, w, h, seed, lines=6, torn=False, folded=False):
    """A document page: a cream sheet with typed lines, cropped or whole."""
    img = PA.img_of(d)
    sheet = [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h),
             (cx - w, cy + h)]
    PA.fill_poly(img, sheet, PAPER, seed=seed, value=0.05)
    PA.hand_stroke(d, sheet, INK, 5, closed=True, seed=seed + 1,
                   wavelength=110.0)
    for i in range(lines):
        yy = cy - h * 0.72 + i * (h * 1.44 / float(max(1, lines)))
        wfrac = 0.78 if i % 3 != 2 else 0.52
        PA.hand_stroke(d, [(cx - w * 0.82, yy), (cx - w * 0.82 + 2 * w * wfrac,
                                                yy)],
                       (150, 142, 130), 4, closed=False, seed=seed + 10 + i,
                       wavelength=70.0)
    if folded:
        # a vertical crease, the give-away that a sheet has been handled
        PA.hand_stroke(d, [(cx + w * 0.1, cy - h), (cx + w * 0.1, cy + h)],
                       (196, 186, 168), 4, closed=False, seed=seed + 30,
                       wavelength=90.0)
    if torn:
        # a ragged bite out of the lower-right corner: this paper is falling
        # apart and must not be opened
        bite = [(cx + w, cy + h * 0.3), (cx + w * 0.82, cy + h * 0.44),
                (cx + w * 0.9, cy + h * 0.62), (cx + w * 0.72, cy + h * 0.78),
                (cx + w * 0.86, cy + h)]
        PA.fill_poly(img, bite, PAPER_D, seed=seed + 40, value=0.06)
        PA.hand_stroke(d, bite, INK, 4, closed=False, seed=seed + 41,
                       wavelength=70.0)


def _archive_box(d, cx, base_y, w, h, seed, open_lid=False, label_strip=True):
    """A grey archival storage box with a lid, cropped by the frame edge when
    the caller pushes it off-centre."""
    img = PA.img_of(d)
    body = [(cx - w / 2.0, base_y - h), (cx + w / 2.0, base_y - h),
            (cx + w / 2.0, base_y), (cx - w / 2.0, base_y)]
    PA.fill_poly(img, body, STONE, seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1,
                   wavelength=110.0)
    if open_lid:
        lid = [(cx - w * 0.56, base_y - h), (cx + w * 0.56, base_y - h),
               (cx + w * 0.44, base_y - h * 1.34), (cx - w * 0.44,
                                                    base_y - h * 1.34)]
        PA.fill_poly(img, lid, STONE_D, seed=seed + 2, value=0.07)
        PA.hand_stroke(d, lid, INK, 5, closed=True, seed=seed + 3,
                       wavelength=90.0)
        PA.hand_stroke(d, [(cx - w * 0.5, base_y - h), (cx + w * 0.5,
                                                        base_y - h)],
                       INK, 6, closed=False, seed=seed + 4, wavelength=110.0)
    if label_strip:
        strip = [(cx - w * 0.28, base_y - h * 0.66), (cx + w * 0.28,
                                                       base_y - h * 0.66),
                 (cx + w * 0.28, base_y - h * 0.42), (cx - w * 0.28,
                                                       base_y - h * 0.42)]
        PA.fill_poly(img, strip, PAPER_D, seed=seed + 5, value=0.05)
        PA.hand_stroke(d, [(cx - w * 0.22, base_y - h * 0.54),
                           (cx + w * 0.22, base_y - h * 0.54)],
                       (120, 110, 98), 4, closed=False, seed=seed + 6,
                       wavelength=60.0)


def _lamp_glow(d, cx, cy, r, seed, strength=1.0):
    """A warm lamp pool: concentric soft rings, the one light note. On the dim
    cards this is what tells the viewer where to look."""
    for rr, col in ((r * 1.5, (58, 44, 30)), (r * 1.0, (108, 80, 44)),
                    (r * 0.5, LAMP)):
        pts = PA.ellipse_pts(cx, cy, rr, rr * 0.72, n=40)
        PA.fill_poly(PA.img_of(d), pts, col, seed=seed + int(rr),
                     value=0.05 * strength)


def _floor_pool(d, cx, cy, rx, ry, seed):
    """A soft warm wash ON THE FLOOR, with no hot core.

    WHY NOT `_lamp_glow` FOR FLOOR LIGHT. That lays down concentric ellipses
    ending in a bright LAMP centre, which is right for a bulb hanging in a
    dark room and wrong for light spilling across a floor: at floor scale the
    bright core read as a fried egg stuck on the shelves (the first b09).

    WHY EIGHT RINGS AND NOT THREE. Three wide, close-valued rings were tried
    and on a near-black floor (b38) the eye read the three boundaries as three
    separate shapes -- the pool came out as a stepped polygon, a coffee stain.
    A gradient drawn in PAINT is bands, so the band count is the smoothness:
    the step from one ring to the next has to be a couple of RGB counts, not
    twenty. Rings run DARKEST (largest) to BRIGHTEST (smallest) so each one
    paints over the last and the visible edge is always the faint one.
    """
    img = PA.img_of(d)
    N = 8
    lo = (44, 34, 26)
    hi = (104, 80, 48)
    for k in range(N):
        u = (k + 1) / float(N)                     # 1.0 outermost -> 0.125 core
        col = tuple(int(lo[c] + (hi[c] - lo[c]) * (1.0 - u)) for c in range(3))
        PA.fill_poly(img, PA.ellipse_pts(cx, cy, rx * u, ry * u, n=56), col,
                     seed=seed + k, value=0.03, edge=0.0)




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

    # ===== b01  beneath the hill: the archive carved under the city ======= #
    def c_underhill(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (58, 50, 44), seed=5, value=0.07)
        # the lintel goes on BEFORE the hill, so the hill's ink crest line --
        # which sweeps up to y=110 -- is drawn over it and the two read as one
        # piece of masonry rather than a band with a line across it
        _lintel(tile, 4)
        PA.paper_overlay(tile, seed=6)
        # the hill: a broad rock mass filling the frame, cropped both sides and
        # running off the bottom, with the archive stacked inside it
        hill = [(-60, 760), (-60, 300), (300, 150), (640, 110), (980, 150),
                (1340, 300), (1340, 760)]
        PA.fill_poly(tile, hill, STONE, seed=7, value=0.09)
        PA.hand_stroke(d, [(-60, 300), (300, 150), (640, 110), (980, 150),
                           (1340, 300)], INK, 7, closed=False, seed=8,
                       wavelength=180.0)
        # the lit archive rooms cut into the rock, deep and low
        for i in range(4):
            x0 = 210 + i * 220
            y0 = 380 + (i % 2) * 70
            room = [(x0, y0), (x0 + 150, y0 - 22), (x0 + 150, y0 + 96),
                    (x0, y0 + 118)]
            PA.fill_poly(tile, room, DEEP, seed=20 + i, value=0.07)
            PA.hand_stroke(d, room, INK, 5, closed=True, seed=30 + i,
                           wavelength=90.0)
            PA.hand_stroke(d, [(x0 + 12, y0 + 26), (x0 + 138, y0 + 8)],
                           LAMP if i % 2 == 0 else STONE_D, 7, closed=False,
                           seed=40 + i, wavelength=50.0)
        D.draw_label(tile, 'ARCHIVE', center=(300, 620), color=LAMP, size=54)
    els.append(card(1, 2, c_underhill))
    els.append(cap(1, W // 2, 96, size=32, fill=LAMP))

    # ===== b02  the windowless room ====================================== #
    def c_nowindow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 11)
        # a bare room: walls converging slightly, a lamp, and the walls where a
        # window would be -- bricked up, i.e. a flat brick patch
        PA.fill_rect(tile, [-20, 120, W + 20, FLOOR], (54, 46, 44), seed=12,
                     value=0.08)
        PA.hand_stroke(d, [(-20, 120), (W + 20, 120)], INK, 6, closed=False,
                       seed=13, wavelength=180.0)
        PA.fill_rect(tile, [-20, FLOOR - 4, W + 20, H + 20], DEEP, seed=14,
                     value=0.07)
        PA.hand_stroke(d, [(-20, FLOOR), (W + 20, FLOOR)], INK, 6,
                       closed=False, seed=15, wavelength=180.0)
        # the bricked-up window: a patch of pale brick where glass would be
        win = [(430, 190), (760, 190), (760, 340), (430, 340)]
        PA.fill_poly(tile, win, STONE, seed=16, value=0.08)
        PA.hand_stroke(d, win, INK, 5, closed=True, seed=17, wavelength=100.0)
        for r in range(3):
            yy = 190 + 50 + r * 50
            PA.hand_stroke(d, [(430, yy), (760, yy)], STONE_D, 3, closed=False,
                           seed=18 + r, wavelength=80.0)
            for c in range(4):
                xx = 430 + 40 + c * 88 + (52 if r % 2 else 0)
                PA.hand_stroke(d, [(xx, yy - 50), (xx, yy)], STONE_D, 3,
                               closed=False, seed=24 + r * 4 + c,
                               wavelength=60.0)
        D.draw_label(tile, 'NO WINDOWS', center=(595, 385), color=LAMP, size=40)
        _lamp_glow(d, 300, 520, 90, 30)
    els.append(card(2, 3, c_nowindow))
    els.append(cap(2, W // 2, 96, size=32, fill=LAMP))

    # ===== b03  the title beat =========================================== #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 41, top=(22, 18, 17), floor_col=(34, 27, 26))
        # a great shelf wall behind, receding. Stocked: without boxes in the
        # slots an evenly-spaced plank run reads as SCAFFOLD, not as an
        # archive (the b03 finding).
        _shelf_run(d, -40, W + 40, 660, 180, 42, shelves=6, stock=1)
        # No in-card draw_title here. The engine already paints the persistent
        # chapter title over every frame at the same position, so a second one
        # on this card only collided with it -- two wobbly INK renders of the
        # same words on the same rows.
        figure(d, 300, 660, 400, pose='pointing', expression='awed', seed=44)
    els.append(card(3, 4, c_title, kind='character'))
    els.append(cap(3, W // 2, 700, size=32, fill=LAMP))

    # ===== b04  the doors opened in 1939 ================================= #
    def c_1939(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 47)
        _big_door(d, 640, 380, 620, 480, 48, open_frac=1.0)
        D.draw_number(tile, '1939', center=(640, 380), color=LAMP, size=170)
    els.append(card(4, 5, c_1939))
    els.append(cap(4, W // 2, 118, size=32, fill=LAMP))

    # ===== b05  opened once, for outside scholars ======================== #
    def c_scholars(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 57)
        _big_door(d, 700, 380, 560, 440, 58, open_frac=0.0)
        # three scholar figures passing through the lit gap
        figure(d, 430, FLOOR, 250, pose='standing', expression='neutral',
               seed=59)
        figure(d, 540, FLOOR + 10, 235, pose='pointing', expression='confused',
               seed=60)
        figure(d, 900, FLOOR, 240, pose='standing', expression='neutral',
               seed=61)
        D.draw_label(tile, 'ONCE', center=(640, 180), color=LAMP, size=48,
                     outline=INK, outline_w=3)
    els.append(card(5, 6, c_scholars, kind='character'))
    els.append(cap(5, W // 2, 700, size=30, fill=LAMP))

    # ===== b06  the doors closed again, quietly ========================== #
    def c_closed(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 67, top=(16, 13, 13), floor_col=(28, 22, 21))
        _big_door(d, 640, 380, 700, 540, 68, open_frac=1.0)
        # the slab's stone frame reaches up to y=67, level with the bottom of
        # the engine's chapter title, so the lintel is raised again over it
        _lintel(tile, 695)
        # the slab pressed shut, heavy, filling the frame -- frame-fill
        PA.hand_stroke(d, [(300, 140), (980, 130)], INK, 10, closed=False,
                       seed=69, wavelength=200.0)
        D.draw_label(tile, 'CLOSED', center=(640, 610), color=LAMP, size=52)
    els.append(card(6, 7, c_closed))
    els.append(cap(6, W // 2, 96, size=32, fill=LAMP))

    # ===== b07  the rooms run deep under the hill ======================== #
    def c_deep(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 77, top=(30, 24, 23), floor_col=(44, 36, 34))
        # a stair running down and away into the rock
        for k in range(9):
            t = k / 8.0
            y = 200 + t * 470
            wdt = 420 - t * 200
            cxk = 640 - t * 30
            step = [(cxk - wdt, y), (cxk + wdt, y), (cxk + wdt - 20, y + 46),
                    (cxk - wdt - 20, y + 46)]
            PA.fill_poly(tile, step, STONE_D, seed=80 + k, value=0.07)
            PA.hand_stroke(d, step, INK, 5, closed=True, seed=90 + k,
                           wavelength=90.0)
        D.draw_label(tile, 'DEEP DOWN', center=(640, 172), color=LAMP, size=48,
                     outline=INK, outline_w=3)
    els.append(card(7, 8, c_deep))
    els.append(cap(7, W // 2, 118, size=32, fill=LAMP))

    # ===== b08  HERO: the shelves receding for kilometres ================= #
    def c_shelves(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 660, 350, 101)
        # shelf runs lining both corridor walls, cropped by the frame edges
        _shelf_run(d, -40, 520, 640, 200, 111, shelves=8, depth=-30, stock=1)
        _shelf_run(d, 800, W + 40, 640, 200, 131, shelves=8, depth=30, stock=1)
        D.draw_label(tile, 'KILOMETRES', center=(640, 180), color=LAMP, size=52,
                     outline=INK, outline_w=3)
    els.append(card(8, 9, c_shelves))
    els.append(cap(8, W // 2, 118, size=32, fill=LAMP))

    # ===== b09  a wooden ladder on a rail ================================ #
    # THE LADDER IS THE SUBJECT, NOT THE SHELVES. The first pass laid one
    # full-width shelf wall and hung a thin 10px ladder on top of it, and the
    # card read as a TV aerial bolted to a bookcase -- no focus, no depth, and
    # the beat ("a ladder slides along a rail") invisible. So: two shelf runs
    # cropped by the side edges with a gap between them, and the ladder big,
    # close, and running OUT THROUGH THE TOP of the frame on its rail, which is
    # both what a rolling library ladder looks like and the frame-fill rule.
    def c_ladder(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 141)
        # floor light first, so the ladder stands in it. Kept to roughly the
        # ladder's own footprint: at rx=420 the outermost ring was 840px wide
        # and its edge drew a visible arc across the whole bottom of the frame,
        # which read as a stain rather than as light.
        _floor_pool(d, 660, 630, 250, 74, 146)
        _shelf_run(d, -60, 400, 616, 214, 142, shelves=6, depth=34, stock=1)
        _shelf_run(d, 900, W + 60, 616, 214, 152, shelves=6, depth=-34, stock=1)
        # the rail, cropped left and right, with the ladder hung off it
        PA.hand_stroke(d, [(-30, 176), (W + 30, 158)], WOOD, 20, closed=False,
                       seed=143, wavelength=190.0)
        PA.hand_stroke(d, [(-30, 158), (W + 30, 141)], WOOD_L, 7,
                       closed=False, seed=147, wavelength=180.0)
        # the ladder: two heavy stiles and real rungs, leaning into the rail
        # and cropped by the top edge so it reads as taller than the frame
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
        # the roller shoes that make it a ladder ON A RAIL rather than a
        # ladder propped against a wall
        for side in (-1, 1):
            PA.hand_stroke(d, [(660 + side * 92, 168), (660 + side * 116, 176)],
                           INK, 15, closed=False, seed=180 + side,
                           wavelength=40.0)
    els.append(card(9, 10, c_ladder))
    els.append(cap(9, W // 2, 118, size=32, fill=LAMP))

    # ===== b10  no electric light ======================================== #
    def c_nolight(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 151, top=(18, 15, 15), floor_col=(26, 21, 20))
        # a bare bulb on a cord, switched off -- dead grey, no glow
        # The cord used to start at y=0, so it hung straight down the middle of
        # the frame and through the persistent title band -- one 5px line at
        # x=640, dead centre, sitting exactly where "The Vatican Archives" is
        # set. Clipped to 104: the cord still reads as coming from off the top of
        # the frame, it just starts at the band edge instead of the frame edge.
        PA.hand_stroke(d, [(640, 104), (640, 180)], INK, 5, closed=False,
                       seed=152, wavelength=90.0)
        bulb = PA.ellipse_pts(640, 210, 40, 48, n=32)
        PA.fill_poly(tile, bulb, (96, 92, 88), seed=153, value=0.05)
        PA.hand_stroke(d, bulb, INK, 5, closed=True, seed=154, wavelength=90.0)
        D.draw_label(tile, 'NO ELECTRIC LIGHT', center=(640, 320), color=LAMP,
                     size=46)
        figure(d, 300, FLOOR, 280, pose='shrug', expression='confused',
               seed=155)
    els.append(card(10, 11, c_nolight, kind='character'))
    els.append(cap(10, W // 2, 118, size=32, fill=LAMP))

    # ===== b11  every window walled up =================================== #
    def c_walledup(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 161)
        # a row of three windows, every one bricked up; the row runs off the
        # right edge so the room reads as bigger than the frame
        for k in range(3):
            x0 = -30 + k * 400
            win = [(x0, 200), (x0 + 260, 200), (x0 + 260, 400), (x0, 400)]
            PA.fill_poly(tile, win, STONE, seed=162 + k, value=0.08)
            PA.hand_stroke(d, win, INK, 5, closed=True, seed=172 + k,
                           wavelength=110.0)
            for r in range(4):
                yy = 200 + 50 * r
                PA.hand_stroke(d, [(x0, yy), (x0 + 260, yy)], STONE_D, 3,
                               closed=False, seed=182 + k * 4 + r,
                               wavelength=80.0)
        D.draw_label(tile, 'BRICKED UP', center=(560, 500), color=LAMP, size=48)
    els.append(card(11, 12, c_walledup))
    els.append(cap(11, W // 2, 118, size=32, fill=LAMP))

    # ===== b12  nobody may photograph a page ============================ #
    def c_nophoto(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 191)
        _lamp_glow(d, 640, 400, 130, 192)
        _page(d, 640, 420, 260, 320, 193, lines=7)
        # a big camera raised over the page, and a red NO bar slashing across
        cam = [(430, 120), (850, 120), (850, 300), (430, 300)]
        PA.fill_poly(tile, cam, (60, 56, 56), seed=194, value=0.07)
        PA.hand_stroke(d, cam, INK, 6, closed=True, seed=195, wavelength=110.0)
        lens = PA.ellipse_pts(640, 300, 70, 70, n=32)
        PA.fill_poly(tile, lens, STONE_D, seed=196, value=0.06)
        PA.hand_stroke(d, lens, INK, 5, closed=True, seed=197, wavelength=90.0)
        D.draw_red_x(tile, [420, 260, 860, 560], color=OXBLOOD, width=16)
        D.draw_label(tile, 'NO PHOTOS', center=(640, 620), color=OXBLOOD,
                     size=52, outline=INK, outline_w=2)
    els.append(card(12, 13, c_nophoto))
    els.append(cap(12, W // 2, 118, size=32, fill=LAMP))

    # ===== b13  not even a phone screen ================================ #
    def c_nophone(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 201)
        _lamp_glow(d, 500, 380, 120, 202)
        _page(d, 500, 430, 200, 250, 203, lines=6)
        # a phone held up, its bright screen over the page
        ph = [(760, 220), (940, 220), (940, 460), (760, 460)]
        PA.fill_poly(tile, ph, (52, 50, 54), seed=204, value=0.06)
        scr = [(778, 248), (922, 248), (922, 420), (778, 420)]
        PA.fill_poly(tile, scr, (188, 200, 210), seed=205, value=0.08)
        PA.hand_stroke(d, scr, INK, 4, closed=True, seed=206, wavelength=90.0)
        D.draw_red_x(tile, [740, 200, 960, 480], color=OXBLOOD, width=14)
        figure(d, 260, FLOOR, 280, pose='armscrossed', expression='skeptic',
               seed=207)
    els.append(card(13, 14, c_nophone, kind='character'))
    els.append(cap(13, W // 2, 118, size=32, fill=LAMP))

    # ===== b14  a flash would harm the paper ============================ #
    def c_flash(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 211)
        _page(d, 640, 440, 300, 340, 212, lines=8)
        # a burst of flash light from the upper left, aimed at the page
        _lamp_glow(d, 260, 180, 110, 213)
        for k in range(7):
            a = 0.5 + k * 0.34
            PA.hand_stroke(d, [(300, 200),
                               (300 + 420 * math.cos(a), 200 + 420 * math.sin(a))],
                           LAMP, 6, closed=False, seed=214 + k,
                           wavelength=120.0)
        D.draw_label(tile, 'FLASH BURNS THE PAPER', center=(640, 178),
                     color=OXBLOOD, size=48, outline=INK, outline_w=3)
    els.append(card(14, 15, c_flash))
    els.append(cap(14, W // 2, 118, size=32, fill=LAMP))

    # ===== b15  some paper cannot be opened ============================= #
    def c_cannotopen(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 221)
        _lamp_glow(d, 500, 400, 120, 222)
        _page(d, 500, 430, 220, 280, 223, lines=6, torn=True)
        # a red circle-with-slash over the page: do not open
        ring = PA.ellipse_pts(500, 430, 300, 330, n=48)
        PA.hand_stroke(d, ring, OXBLOOD, 12, closed=True, seed=224,
                       wavelength=170.0)
        PA.hand_stroke(d, [(280, 620), (720, 240)], OXBLOOD, 12, closed=False,
                       seed=225, wavelength=140.0)
        figure(d, 950, FLOOR, 290, pose='recoil', expression='worried',
               seed=226)
    els.append(card(15, 16, c_cannotopen, kind='character'))
    els.append(cap(15, W // 2, 118, size=32, fill=LAMP))

    # ===== b16  the old pages have fused =============================== #
    def c_fused(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 231)
        _lamp_glow(d, 500, 400, 120, 232)
        # two pages pressed into one thick fused block, edges merged
        fused = [(360, 300), (640, 300), (640, 560), (360, 560)]
        PA.fill_poly(tile, fused, PAPER_D, seed=233, value=0.06)
        PA.hand_stroke(d, fused, INK, 5, closed=True, seed=234, wavelength=110.0)
        # the tell: page edges running together into one solid mass
        for k in range(3):
            PA.hand_stroke(d, [(360 + 10 + k * 16, 300), (360 + 10 + k * 16, 560)],
                           (188, 178, 160), 3, closed=False, seed=235 + k,
                           wavelength=70.0)
        D.draw_label(tile, 'FUSED', center=(500, 610), color=LAMP, size=46)
    els.append(card(16, 17, c_fused))
    els.append(cap(16, W // 2, 118, size=32, fill=LAMP))

    # ===== b17  open them and the paper tears ========================== #
    def c_tears(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 241)
        _lamp_glow(d, 500, 400, 120, 242)
        # a page being pulled apart: two halves peeling away from each other
        _page(d, 400, 400, 190, 260, 243, lines=5)
        _page(d, 820, 430, 170, 250, 244, lines=4)
        # the jagged tear edge between them
        tear = [(610, 200), (640, 300), (620, 380), (660, 470), (630, 560)]
        PA.hand_stroke(d, tear, OXBLOOD, 7, closed=False, seed=245,
                       wavelength=90.0, vary=0.2)
        D.draw_label(tile, 'IT TEARS', center=(640, 640), color=OXBLOOD,
                     size=48, outline=INK, outline_w=2)
    els.append(card(17, 18, c_tears))
    els.append(cap(17, W // 2, 118, size=32, fill=LAMP))

    # ===== b18  so most boxes stay shut ================================ #
    def c_boxshut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 251)
        # a row of boxes on a shelf, lids all closed, cropped both sides
        for k in range(4):
            _archive_box(d, -40 + k * 360, FLOOR + 20, 300, 200, 260 + k)
        D.draw_label(tile, 'SHUT', center=(640, 178), color=LAMP, size=52,
                     outline=INK, outline_w=3)
    els.append(card(18, 19, c_boxshut))
    els.append(cap(18, W // 2, 118, size=32, fill=LAMP))

    # ===== b19  never consulted again =================================== #
    def c_neverconsulted(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 271)
        _shelf_run(d, -40, W + 40, FLOOR + 30, 200, 272, shelves=5, stock=1)
        # a cobwebbed, dusty box wedged deep on a high shelf, half in shadow,
        # resting on the plank at y=444 (top_y 200 + 3 steps of 81)
        _archive_box(d, 800, 444, 220, 150, 273)
        for k in range(5):
            PA.hand_stroke(d, [(700 + k * 40, 294), (760 + k * 30, 364)],
                           (110, 106, 100), 3, closed=False, seed=280 + k,
                           wavelength=60.0)
        D.draw_label(tile, 'NEVER OPENED AGAIN', center=(420, 560), color=LAMP,
                     size=44)
    els.append(card(19, 20, c_neverconsulted))
    els.append(cap(19, W // 2, 118, size=32, fill=LAMP))

    # ===== b20  catalogued once, then shelved ========================== #
    # BRIGHT REGISTER. This is the one beat that happens in daylight -- a hand
    # writing a catalogue line -- and putting it on the near-black archive
    # ground made the whole card read as the same dim room as its neighbours.
    # So: a pale page, a band of empty shelving across the top that stops BELOW
    # the engine's chapter title (which is INK and needs light behind it), and
    # the open catalogue book filling the frame under it.
    def c_catalogued(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _light(tile, 291)
        # Just the open catalogue book, seen from above, filling the frame and
        # cropped by the left and right edges. No shelf run here: an earlier
        # pass put a band of shelving across the top, but _shelf_run's topmost
        # boxes sit ABOVE its first plank (up to top_y - step*0.82), which at
        # this height reached up over the engine's INK chapter title and turned
        # the bright card dark. The beat is the catalogue line, so the book is
        # the whole frame.
        _page(d, 640, 400, 560, 260, 293, lines=9, folded=True)
        D.draw_label(tile, 'CATALOGUED ONCE', center=(640, 596), color=INK,
                     size=44)
    els.append(card(20, 21, c_catalogued))
    els.append(cap(20, W // 2, 686, size=30, fill=INK))

    # ===== b21  a single index card, one line ========================== #
    def c_indexcard(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _light(tile, 301, base=(232, 226, 210))
        # ONE index card, huge, centred and cropped by nothing -- it IS the
        # frame, because the beat is "this one card is the whole record"
        card = [(280, 220), (1000, 220), (1000, 520), (280, 520)]
        PA.fill_poly(tile, card, PAPER, seed=302, value=0.05)
        PA.hand_stroke(d, card, INK, 6, closed=True, seed=303, wavelength=130.0)
        # one single typed line, dead centre
        PA.hand_stroke(d, [(340, 372), (940, 372)], (90, 84, 76), 5,
                       closed=False, seed=304, wavelength=90.0)
        D.draw_label(tile, 'ONE LINE', center=(640, 372), color=INK, size=40)
        D.draw_label(tile, 'INDEX CARD', center=(640, 460), color=OXBLOOD,
                     size=36)
    els.append(card(21, 22, c_indexcard))
    els.append(cap(21, W // 2, 660, size=30, fill=INK))

    # ===== b22  that one line is the whole record ====================== #
    # A MATCH-CUT onto b21. The same index card, now scaled up until it spans
    # the frame and is cropped by BOTH side edges, with a band of empty dark
    # shelving above it standing for everything else in the archive. The old
    # version put a small card inside a full-height shelf run, which left a
    # three-pixel strip of light at the bottom and put the caption on a dark
    # shelf -- the bright register vanished and the label was unreadable.
    def c_whole_record(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _light(tile, 311, base=(236, 230, 214))
        _shelf_run(d, -40, W + 40, 372, 170, 312, shelves=3, stock=1)
        # the card, edge to edge: the record IS the frame
        big = [(-70, 372), (W + 70, 372), (W + 70, 656), (-70, 656)]
        PA.fill_poly(tile, big, PAPER, seed=313, value=0.05)
        PA.hand_stroke(d, big, INK, 7, closed=True, seed=314, wavelength=130.0)
        # and the ONE line on it, running the width of the card. It has to be
        # heavy and dark: at 5px in a pale grey it read as a scratch on blank
        # paper, not as the single line the whole archive reduces to.
        PA.hand_stroke(d, [(70, 452), (1210, 452)], (58, 52, 46), 9,
                       closed=False, seed=315, wavelength=90.0)
        D.draw_label(tile, 'THE WHOLE RECORD', center=(640, 552), color=OXBLOOD,
                     size=48)
    els.append(card(22, 23, c_whole_record))
    els.append(cap(22, W // 2, 690, size=30, fill=INK))

    # ===== b23  fragile pages are filmed =============================== #
    def c_filmed(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 321)
        _lamp_glow(d, 640, 380, 130, 322)
        # a microfilm camera on a stand, shooting a page instead of a hand
        page = [(430, 260), (850, 260), (850, 540), (430, 540)]
        PA.fill_poly(tile, page, PAPER, seed=323, value=0.05)
        PA.hand_stroke(d, page, INK, 5, closed=True, seed=324, wavelength=110.0)
        cam = [(560, 150), (720, 150), (720, 260), (560, 260)]
        PA.fill_poly(tile, cam, (60, 56, 56), seed=325, value=0.06)
        PA.hand_stroke(d, cam, INK, 5, closed=True, seed=326, wavelength=90.0)
        PA.hand_stroke(d, [(640, 260), (640, 300)], INK, 6, closed=False,
                       seed=327, wavelength=60.0)
        # the film strip running out of the camera
        PA.hand_stroke(d, [(640, 300), (1080, 380)], LAMP, 10, closed=False,
                       seed=328, wavelength=140.0)
        D.draw_label(tile, 'FILMED, NOT OPENED', center=(640, 620), color=LAMP,
                     size=46)
    els.append(card(23, 24, c_filmed))
    els.append(cap(23, W // 2, 118, size=32, fill=LAMP))

    # ===== b24  other pages stay closed for ever ======================= #
    def c_forever(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 331, top=(18, 15, 15), floor_col=(28, 22, 21))
        _shelf_run(d, -40, W + 40, FLOOR + 20, 210, 332, shelves=6, stock=1)
        # a long untouched shelf, and one closed box with a chain across it
        _archive_box(d, 640, 640, 320, 190, 333)
        for k in range(3):
            PA.hand_stroke(d, [(480, 560 - k * 20), (800, 560 - k * 20)],
                           OXBLOOD, 5, closed=False, seed=340 + k,
                           wavelength=90.0)
        D.draw_label(tile, 'FOR EVER', center=(640, 178), color=LAMP, size=52,
                     outline=INK, outline_w=3)
    els.append(card(24, 25, c_forever))
    els.append(cap(24, W // 2, 118, size=32, fill=LAMP))

    # ===== b25  a microfilm reel beside a sealed box =================== #
    def c_reel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 351)
        _lamp_glow(d, 640, 420, 120, 352)
        # a big film reel, wound full, the dominant subject
        reel = PA.ellipse_pts(420, 420, 220, 220, n=64)
        PA.fill_poly(tile, reel, (46, 42, 44), seed=353, value=0.06)
        PA.hand_stroke(d, reel, INK, 7, closed=True, seed=354, wavelength=170.0)
        hub = PA.ellipse_pts(420, 420, 70, 70, n=40)
        PA.fill_poly(tile, hub, STONE, seed=355, value=0.06)
        PA.hand_stroke(d, hub, INK, 5, closed=True, seed=356, wavelength=90.0)
        for k in range(3):
            PA.hand_stroke(d, [(420, 420),
                               (420 + 150 * math.cos(k * 2.1),
                                420 + 150 * math.sin(k * 2.1))],
                           INK, 4, closed=False, seed=357 + k,
                           wavelength=70.0)
        # the sealed box beside it
        _archive_box(d, 960, FLOOR + 20, 320, 220, 360)
        PA.hand_stroke(d, [(800, 480), (1120, 480)], OXBLOOD, 6, closed=False,
                       seed=365, wavelength=120.0)
    els.append(card(25, 26, c_reel))
    els.append(cap(25, W // 2, 118, size=32, fill=LAMP))

    # ===== b26  the shelving system kept quiet ======================== #
    def c_quietshelf(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 371)
        # a shelf system seen from above -- a plan of the stacks, abstracted
        for r in range(4):
            for c in range(5):
                x0 = 60 + c * 240
                y0 = 160 + r * 130
                cell = [(x0, y0), (x0 + 180, y0), (x0 + 180, y0 + 90),
                        (x0, y0 + 90)]
                PA.fill_poly(tile, cell, WOOD_D, seed=372 + r * 5 + c,
                             value=0.06)
                PA.hand_stroke(d, cell, WOOD, 5, closed=True,
                               seed=392 + r * 5 + c, wavelength=90.0)
        D.draw_label(tile, 'THE SYSTEM IS KEPT QUIET', center=(640, 700),
                     color=LAMP, size=40)
    els.append(card(26, 27, c_quietshelf))
    els.append(cap(26, W // 2, 118, size=32, fill=LAMP))

    # ===== b27  few people know how the stacks run ==================== #
    def c_fewknow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 640, 340, 401)
        _shelf_run(d, -40, 480, 640, 200, 411, shelves=8, depth=-30, stock=1)
        _shelf_run(d, 800, W + 40, 640, 200, 431, shelves=8, depth=30, stock=1)
        # ONE figure at the far end of it, small against the depth -- but not so
        # small he is a smudge. A first pass drew him at 90px, well under the
        # ~320px at which a fullbody stops reading as a person, and he was a
        # pale tick on the floor. He also stands clear BELOW the lit far end
        # (which spans y 260..420): he is CREAM, so any overlap put his head
        # and shoulders into LAMP and dissolved his outline.
        figure(d, 640, 636, 212, pose='standing',
               expression='deadpan', seed=451)
        # NO 'FEW KNOW' HERO WORD. The caption is "Few people know how the
        # stacks run." and the label printed its own first two words again.
    els.append(card(27, 28, c_fewknow, kind='character'))
    els.append(cap(27, W // 2, 118, size=32, fill=LAMP))

    # ===== b28  the plan is filed elsewhere, upstairs ================= #
    # A SECTION THROUGH THE BUILDING: the archive you are standing in on the
    # bottom two thirds, and one lit room above the deck line with the plan in
    # it. The first pass drew the two decks as two flat bands of colour with a
    # caption, an "UPSTAIRS" label AT THE CAPTION'S OWN Y (they collided), and
    # a third label saying the caption's second half again. There are now no
    # in-art labels at all -- the drawer and the sheet say "plan" -- and the
    # cabinet is cropped by both side edges instead of floating in a dead wall.
    def c_planupstairs(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 461)
        # THE DECK at y=430: everything above the line is one lit room upstairs,
        # everything below is the archive you are standing in. The lintel goes
        # down first so this card's own full-width fills cannot bury the INK
        # title (see _lintel), and the lit room starts at y=128 so it clears it.
        _lintel(tile, 493)
        PA.fill_rect(tile, [-20, 128, W + 20, 430], (70, 60, 52), seed=462,
                     value=0.07)
        # The upstairs room seen STRAIGHT ON, not in perspective. A one-point
        # floor trapezoid was tried and its diagonals read as a grey ramp
        # filling the top of the frame; a straight elevation is what a section
        # drawing does and it stays legible at this size.
        PA.hand_stroke(d, [(-20, 430), (W + 20, 430)], INK, 9, closed=False,
                       seed=463, wavelength=190.0)
        # THE CABINET is the subject of this band, so it is cropped by BOTH side
        # edges rather than parked in the middle of a big empty wall (memory:
        # frame-fill-subject-scale). It stops short of the deck so a strip of
        # LIT FLOOR shows under it -- without that the band reads as one wall of
        # wood and "upstairs" stops being a place. One drawer is pulled open
        # toward the viewer and the plan lies in it, the brightest thing here.
        PA.fill_poly(tile, [(-40, 396), (1320, 396), (1320, 412), (-40, 412)],
                     (44, 37, 31), seed=480, value=0.05)     # contact shadow
        cab = [(-40, 172), (1320, 172), (1320, 402), (-40, 402)]
        PA.fill_poly(tile, cab, WOOD, seed=466, value=0.08)
        PA.hand_stroke(d, cab, INK, 7, closed=True, seed=467, wavelength=150.0)
        # the open drawer's dark interior, so the bright page reads as lit paper
        op = [(322, 190), (1006, 190), (1006, 288), (322, 288)]
        PA.fill_poly(tile, op, DEEPER, seed=473, value=0.05)
        PA.hand_stroke(d, op, INK, 6, closed=True, seed=474, wavelength=120.0)
        # the plan, a tilted sheet lying in the drawer
        pg = [(368, 210), (952, 224), (938, 282), (352, 268)]
        PA.fill_poly(tile, pg, PAPER, seed=468, value=0.05)
        PA.hand_stroke(d, pg, INK, 4, closed=True, seed=469, wavelength=90.0)
        for k in range(4):
            yy = 228 + k * 13
            PA.hand_stroke(d, [(392 + k * 3, yy), (900 - k * 14, yy + 3)],
                           (58, 52, 46), 5, closed=False, seed=475 + k,
                           wavelength=60.0)
        # the drawer front, hanging in front of the opening now it is pulled out
        dr = [(296, 284), (1032, 284), (1032, 352), (296, 352)]
        PA.fill_poly(tile, dr, WOOD_L, seed=476, value=0.08)
        PA.hand_stroke(d, dr, INK, 7, closed=True, seed=477, wavelength=120.0)
        PA.hand_stroke(d, [(596, 318), (732, 318)], INK, 11, closed=False,
                       seed=478, wavelength=40.0)
        # the drawer still shut below it: one face line and its handle
        PA.hand_stroke(d, [(-40, 378), (1320, 378)], WOOD_D, 6, closed=False,
                       seed=479, wavelength=120.0)
        PA.hand_stroke(d, [(600, 366), (700, 366)], INK, 8, closed=False,
                       seed=489, wavelength=40.0)
        # downstairs: the stacks this reader is actually standing in
        _shelf_run(d, -60, W + 60, 730, 490, 470, shelves=4, stock=1)
    els.append(card(28, 29, c_planupstairs))
    els.append(cap(28, W // 2, 118, size=32, fill=LAMP))

    # ===== b29  nobody has ever carried it down ======================= #
    def c_nevercarried(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 471)
        _shelf_run(d, -40, W + 40, 720, 230, 472, shelves=4)
        # A stair going down into the rock, in one-point perspective so it reads
        # as a STAIR and not as slabs floating in a void: a solid wedge of
        # stringer under the treads, both side walls converging on the same
        # vanishing point as the steps, and the whole run cropped by the floor
        # edge. The earlier version drew the treads alone with nothing behind
        # them, and they hung in the frame like floating planks.
        cxk, vy = 640, 250
        # the void the stair descends into
        PA.fill_poly(tile, [(150, 250), (1130, 250), (900, 700), (380, 700)],
                     DEEPER, seed=473, value=0.05)
        for side in (-1, 1):
            wall = [(cxk + side * 490, 250), (cxk + side * 170, 620),
                    (cxk + side * 130, 700), (cxk + side * 330, 700),
                    (cxk + side * 330, 250)]
            PA.fill_poly(tile, wall, STONE_D, seed=474 + side, value=0.07)
            PA.hand_stroke(d, [(cxk + side * 490, 250), (cxk + side * 170, 620),
                               (cxk + side * 130, 700)], INK, 6, closed=False,
                           seed=478 + side, wavelength=140.0)
        # the treads, widening toward the viewer
        for k in range(8):
            t = k / 7.0
            y = 262 + t * 400
            wdt = 180 + t * 320
            step = [(cxk - wdt, y), (cxk + wdt, y), (cxk + wdt + 26, y + 52),
                    (cxk - wdt - 26, y + 52)]
            PA.fill_poly(tile, step, STONE, seed=480 + k, value=0.07)
            PA.hand_stroke(d, step, INK, 5, closed=True, seed=490 + k,
                           wavelength=90.0)
        # the way down, stopped. The cross sits ON the fourth tread rather than
        # half off the bottom of the frame, and it is the only red in the shot.
        D.draw_red_x(tile, [470, 452, 810, 640], color=OXBLOOD, width=14)
    els.append(card(29, 30, c_nevercarried))
    els.append(cap(29, W // 2, 118, size=32, fill=LAMP))

    # ===== b30  HERO: a reader lost between two tall shelves =========== #
    # FRAME-FILL + DWARF. The two shelf runs are CROPPED by the left and right
    # edges and run the full height, and the figure is small between them --
    # that smallness IS the beat ("lost"), so here the deliberate exception to
    # the big-figure rule is the subject.
    def c_lost(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 501)
        # two towering shelf runs converging slightly, cropped by both edges
        _shelf_run(d, -60, 480, 740, -60, 511, shelves=12, depth=-40)
        _shelf_run(d, 800, W + 60, 740, -60, 531, shelves=12, depth=40)
        # Depth down the corridor. This USED to be a hard fill_rect of DEEP,
        # which in the dark read as a flat grey BOX floating between the
        # shelves -- a visible rectangle where the eye expects the corridor to
        # just recede. A soft vertical wash (many thin strips, each a little
        # lighter, no hard edge) gives the same depth cue without the box.
        for i in range(14):
            yy = 300 + i * 19
            PA.fill_rect(tile, [480, yy, 800, yy + 20], DEEP, seed=545 + i,
                         value=0.03, edge=0.0)
        # the lost reader, small enough to be dwarfed by the stacks but big
        # enough that his face reads (was 210 -- too small, he was a smudge)
        figure(d, 640, 700, 340, pose='peeking', expression='worried',
               seed=546)
        # No lamp glow on this card. _lamp_glow lays down OPAQUE concentric
        # ellipses, so at any size big enough to light the reader it also
        # paints a tan slab over his legs and reads as a puddle on the floor.
        # This chapter ends on "the dark down there is absolute" -- the
        # darkness is the point, so let the stacks carry it alone.
        D.draw_label(tile, 'LOST', center=(640, 130), color=LAMP, size=52)
    els.append(card(30, 31, c_lost, kind='character'))
    els.append(cap(30, W // 2, 118, size=32, fill=LAMP))

    # ===== b31  many older records shelved ============================ #
    def c_manyrecords(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 551)
        _shelf_run(d, -60, W + 60, 720, -40, 552, shelves=10, depth=-20, stock=1)
        _shelf_run(d, -60, W + 60, 470, 40, 562, shelves=5, depth=-10, stock=1)
        # both runs start above y=0, so they bury _dark's lintel; raise it again
        _lintel(tile, 573)
        D.draw_label(tile, 'CENTURIES OF RECORDS', center=(640, 640),
                     color=LAMP, size=44, outline=INK, outline_w=3)
    els.append(card(31, 32, c_manyrecords))
    els.append(cap(31, W // 2, 118, size=32, fill=LAMP))

    # ===== b32  some shut for years =================================== #
    def c_shutyears(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 571, top=(18, 15, 15), floor_col=(28, 22, 21))
        # one box, deep on a dark shelf, a thick dust layer on its lid
        _archive_box(d, 640, 660, 420, 240, 572)
        # the dust: a pale band along the top of the lid
        PA.fill_poly(tile, [(440, 440), (840, 440), (840, 470), (440, 470)],
                     (120, 114, 106), seed=575, value=0.05)
        # a calendar, many years crossed off, on the shelf face
        cal = [(520, 500), (760, 500), (760, 640), (520, 640)]
        PA.fill_poly(tile, cal, PAPER_D, seed=576, value=0.05)
        PA.hand_stroke(d, cal, INK, 4, closed=True, seed=577, wavelength=100.0)
        D.draw_label(tile, 'YEARS', center=(640, 570), color=INK, size=44)
        D.draw_label(tile, 'SHUT', center=(640, 178), color=LAMP, size=52,
                     outline=INK, outline_w=3)
    els.append(card(32, 33, c_shutyears))
    els.append(cap(32, W // 2, 118, size=32, fill=LAMP))

    # ===== b33  open for a chosen few only ============================ #
    def c_chosenfew(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 581)
        _lamp_glow(d, 640, 360, 110, 582)
        # one door, ajar, a sliver of light; a red rope keeping the rest out
        _big_door(d, 640, 400, 600, 480, 583, open_frac=0.0)
        PA.hand_stroke(d, [(200, 620), (1080, 600)], OXBLOOD, 8, closed=False,
                       seed=590, wavelength=170.0)
        for k in range(2):
            PA.hand_stroke(d, [(300 + k * 680, 600), (300 + k * 680, 700)],
                           (52, 48, 50), 10, closed=False, seed=592 + k,
                           wavelength=80.0)
        D.draw_label(tile, 'A CHOSEN FEW', center=(640, 178), color=LAMP,
                     size=48, outline=INK, outline_w=3)
    els.append(card(33, 34, c_chosenfew))
    els.append(cap(33, W // 2, 118, size=32, fill=LAMP))

    # ===== b34  access is a favour, not a right ====================== #
    def c_favour(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 601)
        # the character, close and centred, in the middle of the dark --
        # the beat is personal, so the face IS the frame
        face(d, 640, 360, 210, 'deadpan', 602, shoulder=1.4, dark=False)
        # the bubble ADDS to the caption rather than repeating it -- when it
        # read "a favour, not a right" it was the caption's own second half
        # printed twice on one frame
        D.draw_bubble(tile, "you'd need a friend in there", (640, 150),
                      tail_to=(640, 250), font_size=30, max_w=420)
    els.append(card(34, 35, c_favour, kind='character'))
    els.append(cap(34, W // 2, 700, size=30, fill=LAMP))

    # ===== b35  a hand holding out a small key ======================== #
    def c_key(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _dark(tile, 611)
        _lamp_glow(d, 640, 400, 110, 612)
        # a large open hand, palm up, offering a key above it
        # the hand: a rounded palm mass
        palm = [(520, 480), (760, 480), (740, 600), (540, 600)]
        PA.fill_poly(tile, palm, CREAM, seed=613, value=0.04, edge=2.0)
        PA.hand_stroke(d, palm, INK, 5, closed=True, seed=614, wavelength=90.0)
        # fingers, spread
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
    els.append(card(35, 36, c_key))
    els.append(cap(35, W // 2, 118, size=32, fill=LAMP))

    # ===== b36  the stacks hold unread centuries ======================= #
    def c_unread(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _corridor(d, 660, 350, 631)
        _shelf_run(d, -40, 520, 640, 200, 641, shelves=8, depth=-30, stock=1)
        _shelf_run(d, 800, W + 40, 640, 200, 651, shelves=8, depth=30, stock=1)
        D.draw_label(tile, 'NOBODY HAS READ THEM', center=(640, 180),
                     color=LAMP, size=46, outline=INK, outline_w=3)
    els.append(card(36, 37, c_unread))
    els.append(cap(36, W // 2, 118, size=32, fill=LAMP))

    # ===== b37  nobody knows the lowest shelves ======================= #
    def c_lowest(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the lowest shelf: the floor of the archive, almost entirely dark,
        # with the figure small and lost at the bottom of the frame
        _dark(tile, 661, top=(16, 13, 13), floor_col=(24, 19, 18))
        # a low shelf running the floor, mostly swallowed by the dark
        _shelf_run(d, -60, W + 60, 700, 560, 662, shelves=2, depth=0, stock=1)
        # only the faintest lamp reaches the lowest shelf
        _lamp_glow(d, 640, 640, 60, 672)
        figure(d, 640, 690, 180, pose='standing', expression='awed',
               seed=673)
        D.draw_label(tile, 'THE LOWEST SHELVES', center=(640, 178),
                     color=LAMP, size=44, outline=INK, outline_w=3)
    els.append(card(37, 38, c_lowest, kind='character'))
    els.append(cap(37, W // 2, 118, size=32, fill=LAMP))

    # ===== b38  THE FINALE: the dark is absolute ======================= #
    # The frame is swallowed. The character is a cream silhouette almost lost in
    # black, only the eyes catching the last light -- the darkness IS the
    # subject, so the background is the darkest value in the chapter and the
    # shelves are barely-there outlines.
    def c_absolute(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], DEEPER, seed=681, value=0.12)
        PA.paper_overlay(tile, seed=682)
        # barely-there shelf outlines, just enough to place the figure
        _shelf_run(d, -60, 380, 740, 120, 683, shelves=6, depth=0)
        _shelf_run(d, 900, W + 60, 740, 120, 693, shelves=6, depth=0)
        # THE TITLE. Even this frame gets a lintel -- on the finale the darkness
        # is the subject, but the engine draws the INK chapter title here
        # unconditionally and without a lit course of stone behind it the words
        # are dark-on-dark and simply not on screen. An earlier pass used
        # dim=0.34 to keep the frame dark; that is below the contrast the title
        # needs and the words vanished. The lintel is only a 122px band at the
        # very top, so the frame still reads black; FULL WIDTH like every other
        # card, because a narrower band left hard vertical edges at x=280 and
        # x=1000 and read as a floating grey UI panel.
        _lintel(tile, 702, dim=0.95)
        # the figure, centre, standing on a faint warm floor wash. `_floor_pool`
        # and NOT `_lamp_glow`: the lamp lays down opaque concentric ellipses,
        # so at floor scale the bright core reads as a fried egg stuck to the
        # boards. The pool is centred on his FEET (660) -- a first pass put it
        # at 706, 46px below them, which made it a separate blob half-cropped by
        # the frame edge instead of light he is standing in.
        _floor_pool(d, 640, 662, 168, 50, 704)
        figure(d, 640, 660, 400, pose='standing', expression='deadpan',
               seed=703)
        # NO HERO WORD HERE. An 'ABSOLUTE' label was tried and it is the
        # caption's own last word printed twice. The upper half of the frame is
        # left empty on purpose: two barely-lit stacks, one small man, and
        # nothing at all where the light would be.
    els.append(card(38, 39, c_absolute, kind='character'))
    els.append(cap(38, W // 2, 118, size=34, fill=LAMP))

    return SC.finish(els, TITLE, clock, title_seed=61)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))
