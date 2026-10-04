"""pinegap scene -- chapter 1 of the bunker film.

THE FIRST CHAPTER BUILT ON THE REAL TOPIC. Everything structural comes from
scene_common (caption handoff, cropped close-up, phrase clock, render drivers);
this file declares only Pine Gap's cards.

ONE CARD PER BEAT, AND EACH CARD PAINTS ITS OWN WHOLE FRAME. The narration is
34 short sentences (see _plan_pinegap.py) and beats.json gives each one an exact
[start, end], so there is no reason to guess at card boundaries. Every card
function fills the tile background-to-subject, which makes it structurally
impossible for one card's art to survive into the next -- an earlier version
stacked independent elements over a permanent desert and the sky bled through
the cutaways.

FRAME-FILL. The dominant subject owns the frame and is cropped BY an edge. The
first pass drew a small satellite box and a small shutter floating in empty
sky, which is the recurring defect in this project's history.

CADENCE. Still-dominant, one cut per sentence (~34 cuts in ~70s). Motion is
reserved for the two beats where the narrator describes something moving
(the satellite's beams, the missile), because a reference compared at a common
6fps is ~2/3 still frames and our v2 was motion-dominated at 44%.

Run:  python lib/pinegap_scene.py --preview --video
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
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'pinegap'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'Pine Gap'

# The title band carries an intentional lit stone course on the night cards, so
# band_intrusions exempts exactly those rows (see its TITLE_BACKDROP handling).
# Only the part inside the band is declared: rows below it are ordinary art and
# must still be checked.
TITLE_BACKDROP = (10, 73)

W, H = SC.W, SC.H

# --- palette ---------------------------------------------------------------
# Central-Australia red desert. One accent family, used sparingly.
INK = SC.INK
RED = (198, 48, 40)          # alarm / prohibition / emphasis
DUNE = (214, 168, 96)        # desert sand
SKY = (198, 206, 214)        # pale washed sky
DOME = (245, 245, 243)       # radome cover, lit
DOME_SH = (178, 183, 194)    # radome cover, shadow. The first pass used
                             # (203,205,208), only 40 values off the lit side;
                             # the painterly fill washed that out entirely and
                             # the sphere read as uniformly white, so the
                             # terminator had nothing to divide.
STEEL = (150, 158, 168)
CONCRETE = (214, 206, 190)
NIGHT = (30, 34, 48)
NIGHT_G = (18, 20, 28)

HZ = int(H * 0.62)            # horizon; sky_bg uses the same fraction


# ---------------------------------------------------------------------------
# subject primitives
# ---------------------------------------------------------------------------

def _desert(tile, seed, sky=SKY, ground=DUNE, hz=HZ):
    """Full-frame exterior ground. Call at the TOP of every card function."""
    PA.fill_rect(tile, [0, 0, W, H], sky, seed=seed, value=0.05)
    PA.fill_rect(tile, [0, hz - 6, W, H], ground, seed=seed + 1, value=0.07)
    PA.paper_overlay(tile, seed=seed + 2)


def _lit_ball(d, cx, cy, r, seed, lit_col, dark_col, light_dir=(-0.8, -0.6),
              width=6):
    """A sphere split into a lit and a shadow hemisphere, terminator stroked.

    This is v2subjects.split_planet's construction, reimplemented because that
    one takes palette KEYS ('day'/'night' -> its fixed exoplanet yellows), and
    a radome needs white-and-grey. Same reliable recipe: build each half as
    centre -> terminator -> out along the rim on one side, then crisp the
    terminator by stroking the exact curve the fills were bounded by.
    """
    img = PA.img_of(d)
    a = math.atan2(light_dir[1], light_dir[0])
    lx, ly = math.cos(a), math.sin(a)          # light direction (toward light)
    nx, ny = -ly, lx                           # terminator normal

    def rim(sign, n=64):
        out = []
        a0, a1 = (a - math.pi / 2, a + math.pi / 2)
        if sign < 0:
            a0, a1 = a + math.pi / 2, a + 3 * math.pi / 2
        for i in range(n + 1):
            t = a0 + (a1 - a0) * i / float(n)
            out.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        return out

    # bowed terminator across the disc, from +normal rim to -normal rim.
    # The straight chord is p = centre + r*u*N; the bow offsets each point
    # ALONG the light direction by an amount that vanishes at the rim (k -> 0),
    # so the curve leaves and rejoins the silhouette exactly while bowing
    # toward the lit side. My first attempt multiplied by the light vector's
    # components instead of shifting along it, which cancelled the bow out
    # entirely and rendered a hard straight chord across the ball.
    term = []
    n = 44
    amp = 0.20
    for i in range(n + 1):
        u = -1.0 + 2.0 * i / n
        k = math.sqrt(max(0.0, 1.0 - u * u))
        px = cx + nx * r * u - lx * r * amp * k
        py = cy + ny * r * u - ly * r * amp * k
        term.append((px, py))

    lit_poly = [(cx, cy)] + term + list(reversed(rim(+1)))
    PA.fill_poly(img, lit_poly, lit_col, seed=seed ^ 0x2E, edge=1.8)
    dark_poly = [(cx, cy)] + term + rim(-1)
    PA.fill_poly(img, dark_poly, dark_col, seed=seed ^ 0x1D, edge=1.8)
    # The terminator is a SHADOW EDGE, not an outline. Stroking it in ink at
    # width//2 drew a hard black chord rim-to-rim and the ball read as a
    # cracked beach ball; the value change between the two fills already says
    # "sphere", so the line only needs to whisper along the boundary.
    PA.hand_stroke(d, term, (140, 146, 158), 2, closed=False,
                   seed=seed ^ 0x3F, vary=0.22, wavelength=r * 0.5)
    PA.hand_stroke(d, PA.ellipse_pts(cx, cy, r, r, n=72), INK, width,
                   closed=True, seed=seed + 7, wavelength=r * 0.5)


def _radome(d, cx, cy, r, seed, lit=True, detail=True):
    """A white radome sphere -- the signature subject of this chapter.

    THE FIRST VERSION OF THIS WAS A BUG and it is worth recording why. It drew
    the shadow side as an arc swept from a hand-rolled polar loop plus half of
    the rim polygon. The two curves did not share an angular range, so they met
    in a straight chord across the disc (a hard diagonal) and the unshared
    tail rendered as a white crescent sticking out past the rim like a claw.

    The fix is to stop hand-rolling the terminator: _lit_ball builds a correct
    one (centre -> bowed terminator -> out along the rim, both halves, then
    crisp the terminator). The two features that make it read as a radome
    rather than a ball are the pedestal drum it stands on and the meridional
    ribs a real radome cover is panelled in.
    """
    img = PA.img_of(d)
    if lit:
        _lit_ball(d, cx, cy, r, seed, DOME, DOME_SH, width=6)
    else:
        pts = PA.ellipse_pts(cx, cy, r, r, n=72)
        PA.fill_poly(img, pts, (58, 62, 76), seed=seed, value=0.05)
        PA.hand_stroke(d, pts, INK, 6, closed=True, seed=seed + 2,
                       wavelength=140.0)

    if not detail:
        return

    drum_w, drum_h = r * 1.12, r * 0.34
    drum = [(cx - drum_w, cy + r * 0.72), (cx + drum_w, cy + r * 0.72),
            (cx + drum_w * 0.92, cy + r * 0.72 + drum_h),
            (cx - drum_w * 0.92, cy + r * 0.72 + drum_h)]
    PA.fill_poly(img, drum, CONCRETE, seed=seed + 3, value=0.07)
    PA.hand_stroke(d, drum, INK, 5, closed=True, seed=seed + 4, wavelength=120.0)

    rib_col = DOME_SH if lit else (70, 74, 88)
    # WHY THE RIBS AND HOOP ARE NOW CLIPPED TO THE DISC. Unclipped, each rib ran
    # from the crown down to cy+0.82r -- which is BELOW the drum's top edge
    # (cy+0.72r) -- so its tail was drawn on top of the pedestal and read as a
    # stray line dangling out of the base. The hoop at half-width 0.90r poked
    # through the silhouette at its own height. Both are panel lines ON the
    # cover, so they may only exist where the cover is.
    # The visible cap runs from the crown to the drum line, and any point is
    # kept only if it is inside the disc: (dx/r)^2 + (dy/r)^2 <= 1.
    def inside(px, py):
        dx = (px - cx) / float(r)
        dy = (py - cy) / float(r)
        return dx * dx + dy * dy <= 1.0

    y_base = cy + r * 0.70                 # where the drum starts
    for k, frac in enumerate((-0.52, -0.20, 0.20, 0.52)):
        rib = []
        n = 30
        for i in range(n + 1):
            a = math.pi * i / n
            px = cx + r * 0.86 * math.sin(a) * abs(frac) * 1.25
            py = cy - r * 0.86 * math.cos(a)
            if py > y_base:
                continue
            if inside(px, py):
                rib.append((px, py))
            elif rib:
                PA.hand_stroke(d, rib, rib_col, 3, seed=seed + 10 + k,
                               wavelength=110.0)
                rib = []
        if len(rib) > 1:
            PA.hand_stroke(d, rib, rib_col, 3, seed=seed + 10 + k,
                           wavelength=110.0)

    # the hoop: keep only the run that is inside the disc
    hoop_full = PA.ellipse_pts(cx, cy + r * 0.16, r * 0.90, r * 0.20, n=48)
    hoop = []
    for p in hoop_full:
        if inside(*p):
            hoop.append(p)
        else:
            if len(hoop) > 2:
                PA.hand_stroke(d, hoop, rib_col, 3, closed=True,
                               seed=seed + 20, wavelength=110.0)
            hoop = []
    if len(hoop) > 2:
        PA.hand_stroke(d, hoop, rib_col, 3, closed=True, seed=seed + 20,
                       wavelength=110.0)


def _fence(d, x0, y_base, x1, height, seed, n_posts=7, mesh=True):
    """A wire fence standing on `y_base` and running x0 -> x1.

    THE MESH IS DARKER AND MORE LEGIBLE. It was STEEL at 2px, which over pale
    sky read as a faint scratch grid rather than security wire. Security mesh is
    a dense grid of VERTICAL wires crossed by a few horizontal rails; drawing it
    that way (verticals + 3 rails) reads as a fence immediately.
    """
    top = y_base - height
    PA.hand_stroke(d, [(x0, top), (x1, top)], INK, 7, seed=seed, wavelength=130.0)
    PA.hand_stroke(d, [(x0, y_base), (x1, y_base)], INK, 7, seed=seed + 1,
                   wavelength=130.0)
    step = (x1 - x0) / float(n_posts)
    for i in range(n_posts + 1):
        x = x0 + i * step
        PA.hand_stroke(d, [(x, top - 26), (x, y_base + 16)], INK, 11,
                       seed=seed + 2 + i, wavelength=100.0)
        PA.hand_stroke(d, [(x - 14, top + 16), (x + 14, top - 8)], INK, 5,
                       seed=seed + 40 + i, wavelength=70.0)
    if mesh:
        # dense vertical wires, then three horizontal rails -- reads as mesh
        step_v = 26
        n_v = int((x1 - x0) / step_v)
        for i in range(n_v):
            x = x0 + i * step_v
            PA.hand_stroke(d, [(x, top), (x, y_base)], (108, 116, 126), 3,
                           seed=seed + 90 + i, wavelength=90.0)
        for k in range(1, 4):
            y = top + (y_base - top) * k / 4.0
            PA.hand_stroke(d, [(x0, y), (x1, y)], (108, 116, 126), 3,
                           seed=seed + 160 + k, wavelength=110.0)


def _ghost_cover(d, cx, cy, r, seed, colour=(150, 156, 168)):
    """The removed radome cover as a DASHED SILHOUETTE, drawn over the dish.

    WHY A HELPER. Two earlier versions drew the ghost as a loop of 2-point
    hand_strokes. Each 2-point stroke gets its own wobble phase, so the "dash"
    didn't follow the circle at all -- it scattered as confetti across the frame
    and read as debris, not as "this shell was here and was lifted off." A dash
    must be a run of the SAME curve. So build the full circle once, then walk it
    emitting long arcs (dash) with short gaps, each arc still a multi-point
    polyline so the wobble is smooth along the ring.
    """
    ring = PA.ellipse_pts(cx, cy, r, r, n=96)
    m = len(ring)
    dash, gap = 9, 4                 # points on, points off
    i = 0
    while i < m:
        seg = [ring[(i + k) % m] for k in range(min(dash, m - i))]
        if len(seg) > 1:
            PA.hand_stroke(d, seg, colour, 4, closed=False,
                           seed=seed + i, wavelength=r * 0.9, vary=0.18)
        i += dash + gap


def _dish(d, cx, cy, r, seed, tilt=0.0, colour=(176, 184, 192)):
    """A satellite dish in NEAR-FRONT view: a SHALLOW rim ellipse with a
    crescent of shadow on its near inner wall, and a feed horn on a tripod.

    WHY SHALLOW AND WHY A CRESCENT. Two earlier passes both failed. A profile
    bowl (thin tilted lens) read as a surfboard -- no concavity. A near-circular
    front rim rotated by `tilt` read as a wheel or hoop, not a dish, because a
    circle has no "into it" cue. The cue that says "bowl" is seeing the SHADOWED
    inner wall: a crescent hugging the bottom-inside of the rim, in a darker
    value. So the rim is a wide, shallow ellipse (ry ~0.32r) -- unmistakably a
    bowl -- and the crescent supplies the depth. `tilt` leans the whole thing.
    """
    img = PA.img_of(d)
    rx, ry = r, r * 0.32
    rim = PA.ellipse_pts(cx, cy, rx, ry, n=72, rot=tilt)
    PA.fill_poly(img, rim, colour, seed=seed, value=0.06)
    PA.hand_stroke(d, rim, INK, 6, closed=True, seed=seed + 1,
                   wavelength=r * 0.5)
    # the concave face: a crescent = the inner ellipse shifted UP (away from the
    # viewer) and intersected with the rim, filled darker. Shifting it toward the
    # FAR rim is what reads as looking into a bowl.
    fx_off = math.cos(tilt + math.pi / 2)     # perpendicular to tilt, "up"
    fy_off = math.sin(tilt + math.pi / 2)
    inner = PA.ellipse_pts(cx + fx_off * r * 0.16, cy + fy_off * r * 0.16,
                           rx * 0.82, ry * 0.82, n=64, rot=tilt)
    PA.fill_poly(img, inner, (118, 126, 138), seed=seed + 2, value=0.05)
    PA.hand_stroke(d, inner, (86, 94, 104), 3, closed=True, seed=seed + 3,
                   wavelength=r * 0.5)
    # feed horn at the focus, on a short tripod rising from the rim
    fx = cx + fx_off * r * 0.16
    fy = cy + fy_off * r * 0.16
    horn_y = cy - r * 0.74                 # above the bowl
    for ang in (-0.5, 0.0, 0.5):
        lx = fx + ang * r * 0.46
        ly = fy + r * 0.10 * math.cos(ang)
        PA.hand_stroke(d, [(lx, ly), (fx, horn_y)], INK, 4,
                       seed=seed + 10 + int(ang * 10), wavelength=70.0)
    PA.hand_stroke(d, [(fx, horn_y), (fx, horn_y - r * 0.14)], INK, 6,
                   closed=False, seed=seed + 20, wavelength=60.0)
    d.ellipse([fx - 9, horn_y - r * 0.14 - 9, fx + 9, horn_y - r * 0.14 + 9],
              fill=INK)
    # pedestal: a drum under the bowl so it stands on the ground
    PA.hand_stroke(d, [(cx, cy + ry), (cx, cy + ry + r * 0.42)], STEEL, 12,
                   seed=seed + 30, wavelength=80.0)


def _icon_phone(d, cx, cy, s, seed, colour=INK):
    PA.hand_stroke(d, [(cx - s * 0.62, cy - s * 0.50),
                       (cx - s * 0.30, cy - s * 0.62),
                       (cx - s * 0.10, cy - s * 0.20),
                       (cx + s * 0.10, cy + s * 0.20),
                       (cx + s * 0.30, cy + s * 0.62),
                       (cx + s * 0.62, cy + s * 0.50)], colour, 14,
                   seed=seed, wavelength=90.0)


def _icon_radio(d, cx, cy, s, seed, colour=INK):
    body = [(cx - s * 0.42, cy - s * 0.55), (cx + s * 0.42, cy - s * 0.55),
            (cx + s * 0.42, cy + s * 0.70), (cx - s * 0.42, cy + s * 0.70)]
    PA.fill_poly(PA.img_of(d), body, STEEL, seed=seed, value=0.08)
    PA.hand_stroke(d, body, colour, 6, closed=True, seed=seed + 1, wavelength=90.0)
    # The whip antenna stops at cy - s*0.72, NOT cy - s*1.15. At the only call
    # site (cx=640, cy=350, s=330) the old 1.15 put its tip at y = -29 --
    # off the top of the frame -- and the stroke ran straight up through the
    # persistent "Pine Gap" title, striking through the "p". engine3 stamps that
    # title AFTER every element, so the antenna drew over it.
    #
    # This is the frame-fill rule colliding with the title band: making the
    # subject taller to fill the frame pushed it into the one region on the
    # canvas that is not ours. 0.72 tops out at y=112, clear of TITLE_BAND_BOTTOM
    # (68) with margin.
    PA.hand_stroke(d, [(cx + s * 0.24, cy - s * 0.55),
                       (cx + s * 0.30, cy - s * 0.72)], colour, 7,
                   seed=seed + 2, wavelength=70.0)
    for i in range(3):
        y = cy - s * 0.28 + i * s * 0.26
        PA.hand_stroke(d, [(cx - s * 0.26, y), (cx + s * 0.26, y)], INK, 4,
                       seed=seed + 3 + i, wavelength=60.0)


def _icon_missile(d, cx, cy, s, seed, colour=RED):
    body = [(cx - s * 0.16, cy + s * 0.70), (cx - s * 0.16, cy - s * 0.40),
            (cx, cy - s * 0.78), (cx + s * 0.16, cy - s * 0.40),
            (cx + s * 0.16, cy + s * 0.70)]
    PA.fill_poly(PA.img_of(d), body, colour, seed=seed, value=0.08)
    PA.hand_stroke(d, body, INK, 5, closed=True, seed=seed + 1, wavelength=90.0)
    PA.hand_stroke(d, [(cx - s * 0.16, cy + s * 0.30), (cx - s * 0.44, cy + s * 0.74)],
                   INK, 5, seed=seed + 2, wavelength=70.0)
    PA.hand_stroke(d, [(cx + s * 0.16, cy + s * 0.30), (cx + s * 0.44, cy + s * 0.74)],
                   INK, 5, seed=seed + 3, wavelength=70.0)


def _satellite(d, cx, cy, s, seed):
    """A recognisable satellite: bus, two paneled solar wings, a dish, antenna.

    The first version drew the bus and the wings as three unlabelled grey
    rectangles, which read as UI placeholder boxes rather than a spacecraft --
    the panels had no cell gridlines to say "solar" and nothing on the bus said
    "satellite". The gridlines and the dish are what make it legible at a
    glance, and they are cheap.
    """
    img = PA.img_of(d)
    # solar wings first so the bus sits in front of their roots
    for side in (-1, 1):
        x0 = cx + side * s * 0.42
        x1 = cx + side * s * 1.55
        PA.fill_rect(img, [min(x0, x1), cy - s * 0.30, max(x0, x1), cy + s * 0.30],
                     (118, 140, 176), seed=seed + (7 if side > 0 else 8),
                     value=0.06)
        PA.hand_stroke(d, [(min(x0, x1), cy - s * 0.30), (max(x0, x1), cy - s * 0.30),
                           (max(x0, x1), cy + s * 0.30), (min(x0, x1), cy + s * 0.30)],
                       INK, 6, closed=True, seed=seed + (9 if side > 0 else 10),
                       wavelength=110.0)
        # cell gridlines -- these are what say "solar panel"
        for k in range(1, 6):
            x = min(x0, x1) + (max(x0, x1) - min(x0, x1)) * k / 6.0
            PA.hand_stroke(d, [(x, cy - s * 0.30), (x, cy + s * 0.30)], INK, 2,
                           seed=seed + 20 + k + (30 if side > 0 else 0),
                           wavelength=80.0)
        PA.hand_stroke(d, [(min(x0, x1), cy), (max(x0, x1), cy)], INK, 2,
                       seed=seed + 40 + side, wavelength=80.0)
    # the bus
    bus = [(cx - s * 0.44, cy - s * 0.34), (cx + s * 0.44, cy - s * 0.34),
           (cx + s * 0.44, cy + s * 0.34), (cx - s * 0.44, cy + s * 0.34)]
    PA.fill_poly(img, bus, (168, 176, 184), seed=seed, value=0.08)
    PA.hand_stroke(d, bus, INK, 6, closed=True, seed=seed + 1, wavelength=110.0)
    # a dish on the front face
    dish = PA.ellipse_pts(cx, cy + s * 0.02, s * 0.26, s * 0.18, n=40)
    PA.fill_poly(img, dish, (206, 212, 218), seed=seed + 2, value=0.05)
    PA.hand_stroke(d, dish, INK, 4, closed=True, seed=seed + 3, wavelength=80.0)
    # whip antenna
    PA.hand_stroke(d, [(cx, cy - s * 0.34), (cx, cy - s * 0.78)], INK, 5,
                   seed=seed + 4, wavelength=70.0)
    d.ellipse([cx - 7, cy - s * 0.78 - 7, cx + 7, cy - s * 0.78 + 7], fill=INK)


def _globe(d, cx, cy, r, seed):
    img = PA.img_of(d)
    g = PA.ellipse_pts(cx, cy, r, r, n=72)
    PA.fill_poly(img, g, (150, 168, 190), seed=seed, value=0.07)
    PA.hand_stroke(d, g, INK, 6, closed=True, seed=seed + 1, wavelength=140.0)
    for k, ry in enumerate((0.30, 0.62, 0.88)):
        hoop = PA.ellipse_pts(cx, cy, r * ry, r, n=48)
        PA.hand_stroke(d, hoop, (110, 128, 150), 3, closed=True,
                       seed=seed + 10 + k, wavelength=110.0)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build():
    clock = SC.BeatClock(BEATS)
    els = []

    def T(i):
        return clock.at('b%02d' % i, 0)

    def card(i, j, draw, kind='subject', seed=0, motion=None):
        """A complete card: its own background, live beats i..j-1.

        The final card points past the last beat, so its `until` is the segment
        duration -- otherwise the last art would never be replaced and would
        simply hold, which is what we want anyway, but asking for a beat that
        does not exist raises instead.
        """
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        return E3.E('card%02d' % i, kind, draw, at=T(i), until=end,
                    motion=motion)

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # page tooth under everything
    els.append(E3.E('page', 'bg', SC.paper_bg(99), at=0.0))

    # ---- b01-b02  the hook: nothing at all ------------------------------- #
    # b03 gets its own card (the close-up), so this group ends at b03 --
    # appending cap(3) here as well rendered "That is the point." twice, once
    # behind the character's head.
    def c_empty(tile, fw, fh):
        _desert(tile, 5)
    els.append(card(1, 3, c_empty))
    els.append(cap(1, W // 2, 300, size=40))
    els.append(cap(2, W // 2, 300, size=40))

    def c_deadpan(tile, fw, fh):
        # A MEDIUM character shot, not a giant portrait. At hr=300 the head
        # filled the frame and the character primitives -- brows, lid, hair --
        # were exposed at a scale they were never tuned for. The reference shows
        # its presenter at medium distance; hr=210 keeps him a person in the
        # scene, cropped by the left edge so he still dominates (frame-fill).
        SC.closeup(ImageDraw.Draw(tile), 300, 360, 210, 'deadpan', 3)
    els.append(card(3, 4, c_deadpan, kind='character'))
    els.append(cap(3, 920, 610, size=32, fill=RED))

    # ---- b04  Australia ---------------------------------------------------- #
    def c_oz(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=7, value=0.05)
        PA.paper_overlay(tile, seed=8)
        land = [(210, 300), (430, 190), (760, 175), (1010, 265), (1060, 400),
                (880, 520), (560, 560), (320, 470), (190, 380)]
        PA.fill_poly(tile, land, (206, 186, 138), seed=31, value=0.07)
        PA.hand_stroke(d, land, INK, 7, closed=True, seed=32, wavelength=150.0)
        PA.hand_stroke(d, [(640, 300), (640, 520)], INK, 4, seed=33,
                       wavelength=110.0)
        PA.hand_stroke(d, [(640, 400), (790, 400)], INK, 4, seed=34,
                       wavelength=110.0)
        D.draw_label(tile, 'AUSTRALIA', center=(560, 610), color=INK, size=30)
        d.ellipse([652, 302, 672, 322], fill=RED)
        PA.hand_stroke(d, [(662, 322), (662, 372)], RED, 5, seed=36,
                       wavelength=80.0)
    els.append(card(4, 5, c_oz))
    els.append(cap(4, W // 2, 660, size=30))

    # ---- b05  the empty horizon ------------------------------------------- #
    def c_horizon(tile, fw, fh):
        _desert(tile, 9)
        for k, x in enumerate((180, 430, 700, 960, 1180)):
            PA.hand_stroke(ImageDraw.Draw(tile),
                           [(x, HZ - 40 - k % 2 * 22), (x + 26, HZ - 96)],
                           (186, 148, 92), 4, seed=41 + k, wavelength=80.0)
    els.append(card(5, 6, c_horizon))
    els.append(cap(5, W // 2, 240, size=32))

    # ---- b06-b08  the domes appear, then the fence ------------------------ #
    # FRAME-FILL: the domes own the upper frame and are cropped at the side
    # edges; the fence owns the bottom third as a foreground element.
    def c_domes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 11)
        # These radomes were centred too high and drawn so large that the top of
        # each arc exited the frame and cut through the persistent "Pine Gap"
        # title (centre: cy=300 r=320 -> top=-20). Caught by the band_intrusions()
        # gate. Every cy is now >= r + 100 so the arc's top clears y=100, below
        # the title band (68) with stroke margin. Radii trimmed a little so the
        # spheres still dominate the frame per the frame-fill rule.
        _radome(d, 200, 360, 230, 12)
        _radome(d, 640, 425, 320, 13)
        _radome(d, 1100, 360, 240, 17)
    els.append(card(6, 7, c_domes))
    els.append(cap(6, W // 2, 660, size=30))

    def c_cluster(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 19)
        # Same fix as b06: arcs were exiting the top of the frame through the
        # title. cy >= r + 100 everywhere.
        _radome(d, 300, 355, 250, 20)
        _radome(d, 700, 390, 285, 21)
        _radome(d, 1060, 360, 250, 22)
        _fence(d, -40, 690, W + 40, 210, 23, n_posts=8)
    els.append(card(7, 8, c_cluster))
    els.append(cap(7, W // 2, 640, size=30))

    def c_fence(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 27)
        # A CLUSTER behind the wire, with the front sphere scaled up and cropped
        # by the left edge. The first version put ONE small sphere centred, so
        # the fence -- which is what the line is about -- dominated an empty
        # frame and the domes read as a lonely prop.
        _radome(d, 980, 355, 250, 25)
        _radome(d, 640, 425, 320, 27)
        _radome(d, 120, 405, 300, 26)
        _fence(d, -40, 720, W + 40, 470, 29, n_posts=6)
    els.append(card(8, 9, c_fence))
    # The caption sat at y=170, straight across the middle of the sphere. The
    # only clear band is the very bottom, below the fence's lower region.
    els.append(cap(8, W // 2, 690, size=30))

    # ---- b09-b10  ordinary buildings / not buildings ----------------------- #
    # The pedestal is a clean plinth. It USED to carry a label reading "ordinary
    # buildings" at cy=640, but that (a) duplicated the caption sitting at the
    # top of the same card -- the frame said the same thing twice -- and (b) sat
    # dark-on-pale directly on the plinth's fill texture, where it read as a
    # smudge rather than a label. One idea per card: the caption owns the words.
    def c_ordinary(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 31)
        _radome(d, 640, 385, 280, 32)
    els.append(card(9, 10, c_ordinary))
    els.append(cap(9, W // 2, 130, size=30))

    def c_notb(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 33)
        _radome(d, 640, 385, 280, 34)
        # The red box top was y=60, which is INSIDE the persistent title band
        # (TITLE_BAND_BOTTOM=68) -- the box's top edge ran straight through the
        # bottom of "Pine Gap". Caught by the new band_intrusions() gate, which
        # looks for dark/red pixels in the title box that the title glyphs do not
        # explain. Moved to y=104, clear of the title, still framing the radome.
        D.draw_red_box(tile, [300, 104, 980, 660])
        D.draw_label(tile, 'not buildings', center=(640, 690), color=RED,
                     size=40)
    els.append(card(10, 11, c_notb))
    els.append(cap(10, W // 2, 140, size=32, fill=RED))

    # ---- b11  the title beat: the name, big and stamped ------------------- #
    def c_title(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 37)
        _radome(d, 300, 400, 200, 38, detail=False)
        _radome(d, 1000, 400, 200, 39, detail=False)
        # The stamp was INK (near-black) on a mid-grey sky: no keyline (INK
        # labels are never stroked) and almost no value contrast, so the letters
        # merged into a grey smear. RED is the chapter accent and carries a black
        # keyline, which is what makes it legible.
        D.draw_label(tile, 'PINE GAP', center=(650, 400), color=RED, size=96)
    els.append(card(11, 12, c_title))
    els.append(cap(11, W // 2, 620, size=32, fill=RED))

    # ---- b12-b13  two flags, a secret agreement --------------------------- #
    def c_flags(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 41)
        _radome(d, 640, 470, 150, 42, detail=False)
        for x, cols, sd in ((300, [(178, 34, 44), (250, 250, 248)], 43),
                            (760, [(12, 48, 120), (250, 250, 248),
                                   (214, 34, 44)], 47)):
            for i, c in enumerate(cols):
                x0 = x + i * 66
                PA.fill_rect(tile, [x0, 210, x0 + 62, 400], c, seed=sd + i,
                             value=0.06)
                PA.hand_stroke(d, [(x0, 210), (x0 + 62, 210), (x0 + 62, 400),
                                   (x0, 400)], INK, 5, closed=True,
                               seed=sd + 4 + i, wavelength=100.0)
            PA.hand_stroke(d, [(x, 210), (x, 560)], INK, 8, seed=sd + 8,
                           wavelength=120.0)
    els.append(card(12, 14, c_flags))
    els.append(cap(12, W // 2, 640, size=30))
    els.append(cap(13, W // 2, 640, size=30))

    # ---- b14-b15  a shutter, and a sign that tells you nothing ------------- #
    def c_shutter(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (226, 232, 238), seed=51, value=0.05)
        PA.paper_overlay(tile, seed=52)
        body = [(180, 150), (1100, 150), (1100, 600), (180, 600)]
        PA.fill_poly(tile, body, CONCRETE, seed=53, value=0.07)
        PA.hand_stroke(d, body, INK, 7, closed=True, seed=54, wavelength=140.0)
        for i in range(7):
            y = 210 + i * 52
            PA.hand_stroke(d, [(200, y), (1080, y)], (196, 188, 172), 5,
                           seed=55 + i, wavelength=110.0)
        PA.fill_rect(tile, [520, 430, 760, 600], STEEL, seed=62, value=0.08)
        PA.hand_stroke(d, [(520, 430), (760, 430), (760, 600), (520, 600)],
                       INK, 6, closed=True, seed=63, wavelength=110.0)
        d.ellipse([716, 496, 752, 532], fill=INK)
    els.append(card(14, 15, c_shutter))
    els.append(cap(14, W // 2, 660, size=30))

    def c_sign(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 65)
        sign = [(120, 250), (1160, 250), (1160, 430), (120, 430)]
        PA.fill_poly(tile, sign, (250, 250, 248), seed=66, value=0.05)
        PA.hand_stroke(d, sign, INK, 8, closed=True, seed=67, wavelength=140.0)
        D.draw_label(tile, 'SPACE RESEARCH FACILITY', center=(640, 340),
                     color=INK, size=42)
        for x in (280, 1000):
            PA.hand_stroke(d, [(x, 430), (x, 600)], INK, 12, seed=68 + x,
                           wavelength=100.0)
    els.append(card(15, 16, c_sign))
    els.append(cap(15, W // 2, 620, size=30))

    # ---- b16-b17  white ball -> RADOME ------------------------------------ #
    def c_ball(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 71)
        _radome(d, 640, 435, 330, 72)
    els.append(card(16, 17, c_ball))
    els.append(cap(16, W // 2, 660, size=30))

    def c_radome_word(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 73)
        _radome(d, 640, 405, 300, 74)
        D.draw_label(tile, 'RADOME', center=(640, 380), color=RED, size=88)
    els.append(card(17, 18, c_radome_word))
    els.append(cap(17, W // 2, 650, size=34, fill=RED))

    # ---- b18-b20  cutaway: cover off, dish under it ----------------------- #
    def c_cover(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 81)
        _radome(d, 640, 400, 300, 82, detail=False)
        D.draw_label(tile, 'protective cover', center=(640, 660), color=INK,
                     size=32)
    els.append(card(18, 19, c_cover))
    els.append(cap(18, W // 2, 130, size=30))

    def c_lift(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 83)
        # The dish on its pedestal, with the cover drawn directly over it in
        # DASHED outline -- the ghost of the shell that was just lifted. Two
        # earlier versions failed: an off-to-one-side ball said nothing about
        # where the cover came from, and a solid floating sphere read as a
        # second object. A dashed silhouette sitting exactly over the dish says
        # "was here, now removed." The dash is one continuous ring walked with
        # long arcs (see _ghost_cover) -- per-tick 2-point strokes scattered as
        # confetti instead of following the circle.
        _dish(d, 640, 500, 280, 86, tilt=0.30)
        _ghost_cover(d, 640, 450, 310, 88)
        # The arrow tail was y=60, inside the persistent title band -- the shaft ran up
        # between "Pine" and "Gap" and clipped the G. Caught by band_intrusions().
        # Tail moved to y=104; head to y=210 so the arrow keeps its length.
        D.draw_arrow(tile, (640, 104), (640, 210), color=INK, width=10,
                     head=46)
        # The label sits to the RIGHT of the arrow's shaft, not across it --
        # centred on the shaft the arrowhead ran straight through the text.
        D.draw_label(tile, 'cover lifted off', center=(880, 150), color=INK,
                     size=32)
    els.append(card(19, 20, c_lift))
    # Caption on the SAND at the very bottom; the label sits up near the arrow
    # so the two never stack (they collided at y=640/660 before).
    els.append(cap(19, W // 2, 700, size=30))

    def c_angle(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 87)
        _dish(d, 600, 500, 290, 90, tilt=0.42)
        gx, gy, gr = 600, 460, 320
        _ghost_cover(d, gx, gy, gr, 92)
        # THE BEAM IT CANNOT SEE. Two rays leave the dish's focus; each is
        # solved to the exact point where it meets the ghost shell, so the wedge
        # stops DEAD on the dashed circle instead of poking through it. That
        # truncation is the entire point of a radome, so it is computed, not
        # eyeballed.
        def to_shell(deg):
            a = math.radians(deg)
            vx, vy = math.cos(a), math.sin(a)
            ox, oy = 600.0 - gx, 500.0 - gy
            b = 2.0 * (ox * vx + oy * vy)
            c = ox * ox + oy * oy - gr * gr
            disc = b * b - 4.0 * c
            if disc <= 0:
                return (600 + vx * 400, 500 + vy * 400)
            t = (-b + math.sqrt(disc)) / 2.0
            return (600 + vx * t, 500 + vy * t)

        e1, e2 = to_shell(-52), to_shell(-18)
        cone = [(600, 500), e1, e2]
        PA.fill_poly(tile, cone, (228, 208, 172), seed=93, value=0.06)
        PA.hand_stroke(d, [(600, 500), e1], RED, 5, seed=94, wavelength=110.0)
        PA.hand_stroke(d, [(600, 500), e2], RED, 5, seed=95, wavelength=110.0)
        # a blunt stop-mark right where the beam meets the shell
        mid = ((e1[0] + e2[0]) / 2.0, (e1[1] + e2[1]) / 2.0)
        PA.hand_stroke(d, [(mid[0] - 16, mid[1] - 16), (mid[0] + 16, mid[1] + 16)],
                       RED, 6, seed=96, wavelength=40.0)
        PA.hand_stroke(d, [(mid[0] + 16, mid[1] - 16), (mid[0] - 16, mid[1] + 16)],
                       RED, 6, seed=97, wavelength=40.0)
        D.draw_label(tile, 'the angle it hides', center=(1010, 250), color=RED,
                     size=32)
    els.append(card(20, 21, c_angle))
    els.append(cap(20, W // 2, 700, size=30, fill=RED))

    # ---- b21  who is being watched -- the character earns the joke ------- #
    def c_peek(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 91)
        _radome(d, 640, 405, 300, 92, detail=False)
        SC.fullbody(d, 1130, 700, 470, pose='peeking', expression='skeptic',
                    seed=93)
    els.append(card(21, 22, c_peek, kind='character'))
    els.append(cap(21, W // 2, 660, size=32, fill=RED))

    # ---- b22-b24  one of the biggest, and the group ----------------------- #
    def c_globe1(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 95, sky=(226, 232, 238), ground=(226, 232, 238))
        gx, gy, gr = 560, 412, 300
        _globe(d, gx, gy, gr, 96)
        # SIGNALS FLOW IN. The first version drew plain lines radiating OUT of
        # the globe's centre and down, so it read as the post EMITTING, which is
        # backwards for a listening station. Now four arrows come from outside
        # the frame and terminate ON the globe's edge, arrowheads inward.
        #
        # gy was 400, putting the globe's top edge at y=100 -- four pixels into
        # the title band, so the dome's outline grazed "Pine Gap" on b22. It is
        # 412 now, which clears the band and still leaves the globe 308px tall at
        # the bottom, so it crops the same way.
        #
        # The angles matter for the same reason. They start at gr+320 = 620px out,
        # and the old 250 and 290 degrees put that start point at y = 400 - 583 =
        # -183, i.e. the two lines came from off the TOP of the frame and crossed
        # the whole title band on their way in. They now start at 160 and 20
        # degrees, which arrive from the lower flanks. Every one of the four
        # start points is now below y=188, and the "from outside the frame" read
        # survives because they still enter past the left and right edges.
        for k, ang in enumerate((200, 160, 20, 340)):
            a = math.radians(ang)
            # start well outside the globe, end just at its edge
            sx, sy = gx + math.cos(a) * (gr + 320), gy + math.sin(a) * (gr + 320)
            ex, ey = gx + math.cos(a) * (gr + 26), gy + math.sin(a) * (gr + 26)
            PA.hand_stroke(d, [(sx, sy), (ex, ey)], (198, 120, 60), 5,
                           seed=97 + k, wavelength=130.0)
            # arrowhead at the globe edge, pointing inward
            tip = (gx + math.cos(a) * (gr + 4), gy + math.sin(a) * (gr + 4))
            PA.hand_stroke(d, [(tip[0] + math.sin(a) * 20,
                                tip[1] - math.cos(a) * 20), tip],
                           (198, 120, 60), 5, seed=110 + k, wavelength=40.0)
            PA.hand_stroke(d, [(tip[0] - math.sin(a) * 20,
                                tip[1] + math.cos(a) * 20), tip],
                           (198, 120, 60), 5, seed=120 + k, wavelength=40.0)
        D.draw_number(tile, '1', center=(1090, 400), color=RED, size=200)
        D.draw_label(tile, 'biggest spy base', center=(1090, 560), color=INK,
                     size=28)
    els.append(card(22, 23, c_globe1))
    els.append(cap(22, 560, 690, size=30))

    def c_five(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 99, sky=(226, 232, 238), ground=(226, 232, 238))
        for i in range(5):
            x = 190 + i * 225
            e = PA.ellipse_pts(x, 340, 92, 56, n=44)
            PA.fill_poly(tile, e, (250, 250, 248), seed=100 + i, value=0.04)
            PA.hand_stroke(d, e, INK, 6, closed=True, seed=105 + i,
                           wavelength=100.0)
            d.ellipse([x - 26, 316, x - 2, 340], fill=INK)
            d.ellipse([x + 2, 316, x + 26, 340], fill=INK)
        D.draw_label(tile, 'FIVE EYES', center=(640, 560), color=INK, size=54)
    els.append(card(23, 25, c_five))
    els.append(cap(23, W // 2, 660, size=30))
    els.append(cap(24, W // 2, 660, size=30))

    # ---- b25-b26  the satellite overhead, and its beams landing ---------- #
    def c_sat(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 111, sky=(206, 216, 228), ground=(206, 216, 228))
        _satellite(d, 640, 190, 120, 112)
        _radome(d, 640, 600, 150, 116, detail=False)
        for k, a in enumerate((-0.62, -0.22, 0.22, 0.62)):
            x0 = 640 + 300 * math.tan(a)
            PA.hand_stroke(d, [(640, 300), (x0, 520)], (214, 132, 60), 5,
                           seed=117 + k, wavelength=130.0)
    els.append(card(25, 26, c_sat))
    els.append(cap(25, W // 2, 400, size=30))

    def c_land(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 121, sky=(206, 216, 228), ground=(206, 216, 228))
        _dish(d, 640, 470, 300, 122, tilt=0.5)
        # These four beams used to start at y=40, which is inside the persistent
        # title band -- they ran down through "Pine Gap" on b26. They are meant to
        # read as coming from off the top of the frame, and they still do: the run
        # is simply clipped at the band edge instead of starting inside it. Same
        # treatment as the fortknox bar hall, where clipping at y=104 turned a
        # full-frame fill into a legible title.
        for k, a in enumerate((-0.7, -0.2, 0.3, 0.8)):
            x0 = 640 + 420 * math.tan(a)
            PA.hand_stroke(d, [(x0, 104), (640, 250)], (214, 132, 60), 5,
                           seed=123 + k, wavelength=130.0)
    els.append(card(26, 27, c_land))
    els.append(cap(26, W // 2, 700, size=30))

    # ---- b27-b29  what the signals are: calls, radio, launches ----------- #
    def c_phone(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 131, sky=(226, 232, 238), ground=(226, 232, 238))
        _icon_phone(d, 640, 340, 300, 132)
    els.append(card(27, 28, c_phone))
    els.append(cap(27, W // 2, 620, size=34))

    def c_radio(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 135, sky=(226, 232, 238), ground=(226, 232, 238))
        _icon_radio(d, 640, 350, 330, 136)
    els.append(card(28, 29, c_radio))
    els.append(cap(28, W // 2, 660, size=34))

    def c_missile(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 139, sky=(210, 200, 210), ground=(214, 198, 186))
        # cy was 330; the nose tip sits at cy - s*0.78 = 65, inside the title
        # band. Lowered to 410 -> tip at 145, clear of the title.
        _icon_missile(d, 640, 410, 340, 140)
    els.append(card(29, 30, c_missile))
    els.append(cap(29, W // 2, 640, size=34, fill=RED))

    # ---- b30  close enough -- the character stops himself ---------------- #
    def c_stop(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 145)
        _radome(d, 950, 365, 260, 146, detail=False)
        _fence(d, 620, 720, W + 40, 380, 147, n_posts=4)
        SC.fullbody(d, 400, 700, 470, pose='recoil', expression='worried',
                    seed=148)
    els.append(card(30, 31, c_stop, kind='character'))
    els.append(cap(30, 300, 200, size=30, fill=RED))

    # ---- b31  the airspace column, cropped by the top edge --------------- #
    def c_airspace(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 151, sky=(200, 212, 226), ground=DUNE)
        _radome(d, 620, 620, 110, 152, detail=False)
        col = [(330, 720), (330, 104), (910, 104), (910, 720)]
        PA.fill_poly(tile, col, (176, 190, 208), seed=153, value=0.08)
        for x in (330, 910):
            PA.hand_stroke(d, [(x, 104), (x, 720)], RED, 7, seed=154 + x,
                           wavelength=160.0)
        # The column's top crossbar was y=40 (and the column ran to y=0), which
        # is INSIDE the persistent title band -- the red line struck straight
        # through "Pine Gap". Caught by band_intrusions(). The column still reads
        # as tall and cropped-looking, but now starts below the title at y=104.
        PA.hand_stroke(d, [(330, 104), (910, 104)], RED, 7, seed=156,
                       wavelength=160.0)
        D.draw_number(tile, '18,000', center=(620, 300), color=RED, size=110)
        D.draw_label(tile, 'FEET', center=(620, 400), color=RED, size=52)
    els.append(card(31, 32, c_airspace))
    els.append(cap(31, W // 2, 640, size=30, fill=RED))

    # ---- b32-b33  guards, and the price of the fence --------------------- #
    def c_guards(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 161)
        _fence(d, -40, 640, W + 40, 300, 162, n_posts=9)
        for i, x in enumerate((240, 620, 1000)):
            SC.fullbody(d, x, 660, 400, pose='standing',
                        expression='deadpan', seed=170 + i)
    els.append(card(32, 33, c_guards, kind='character'))
    els.append(cap(32, W // 2, 660, size=30))

    def c_price(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _desert(tile, 181)
        _fence(d, -40, 560, W + 40, 420, 182, n_posts=8)
        D.draw_number(tile, '7', center=(400, 300), color=RED, size=280)
        D.draw_label(tile, 'years', center=(760, 240), color=RED, size=92)
        D.draw_label(tile, 'in prison', center=(760, 360), color=RED, size=52)
    els.append(card(33, 34, c_price))
    els.append(cap(33, W // 2, 680, size=30, fill=RED))

    # ---- b34  the finale: the domes at night, and nobody knows ----------- #
    def c_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], NIGHT, seed=191, value=0.12)
        PA.fill_rect(tile, [0, HZ - 6, W, H], NIGHT_G, seed=192, value=0.12)
        PA.paper_overlay(tile, seed=193)
        # A dark card needs a lit course at the head for the near-black title to
        # read against (see scene_common.title_backdrop). Drawn before the stars
        # so the backdrop stays UNDER the art.
        SC.title_backdrop(tile, 194, col=(96, 104, 124))
        for k in range(40):
            a = (k * 2.399) % 6.283
            rr = 40 + (k * 53) % 620
            x = 640 + rr * math.cos(a) * 1.1
            y = 300 + rr * math.sin(a) * 0.62
            if 0 < x < W and 0 < y < HZ:
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(226, 232, 244))
        _radome(d, 760, 405, 300, 194, lit=False)
    els.append(card(34, 35, c_night))
    els.append(cap(34, 300, 620, size=36, fill=RED))

    return SC.finish(els, TITLE, clock, title_seed=23)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))