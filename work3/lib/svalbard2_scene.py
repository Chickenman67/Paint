"""svalbard2_scene -- the PERSISTENT-STAGE rebuild of chapter 8 (svalbard).

WHAT CHANGED AND WHY. The previous build of this file already wrapped its beats
in SC.stage(), but almost every beat inside those stages was a full-frame
SC.layer() that repainted the entire composition at that beat's onset. Measured
on the built scene: 23 REFRAME hits (a subject onset that repaints >30% of the
frame) and a median gap between full-frame repaints of 2.84s. That is the viewer's
complaint exactly -- "every sentence has a cut with a completely new image" -- and
the structural measurements agreed with it.

THE MODEL. A STAGE paints the whole persistent world for a run of beats and is
registered with kind='bg', so its onset is a legitimate cut to a new place (the
gate skips 'bg' onsets). Every beat INSIDE a stage then ACCRUES one element that
covers well under 30% of the frame, so nothing inside a stage reads as a new
image. A stage spans 3-6 beats; the median repaint gap becomes the median stage
length. The measured result after this rebuild is in the module's own build log.

FOURTEEN stages, grouped on the narration's own acts and on what can share
one frame without crowding (memory: blind-critic-loss-pattern-over-populated).
The count is fourteen because S8 is drawn as two stages -- the freezer and then
the corridor are different places and cannot share a frame -- so the S-LABEL
count and the STAGE count differ by one. That mismatch is what made an earlier
version of this docstring claim "thirteen stages" while listing fourteen calls:

    S1  b01-b03  the mountain at night; the vault's name; it opened in 2008
    S2  b04-b06  the rock in cross-section; the tunnel; the hall cut into the ice
    S3  b07      above the doorway the midsummer sun barely rises
    S4  b08-b10  the cold room; one packet; a million samples
    S5  b11-b12  the crop deck; every sample is a spare copy
    S6  b13-b14  the keeper, and the globe the samples insure
    S7  b15      minus eighteen
    S8a b16-b17  a farm freezer; centuries in the cold
    S8b b18-b19  the corridor; then the hasp frozen shut
    S9  b20-b21  the mountain leaks in 2016; meltwater at the entrance
    S10 b22-b25  the flood rises; eight hundred tonnes; the barricade; 'fine'
    S11 b26-b27  above the waterline; and the same ice thawing
    S12 b28-b30  watched; a new tunnel; lights on the snow
    S13 b31-b35  one night mountain that ACCUMULATES: the bunker, the warm front,
                 the bared slope and -2.6, then him and "for now", then the
                 channel. Nothing here is ever replaced.

The finale (S13) is the clearest case of the model: it was five unrelated
full-frame cards -- two close-ups, a re-drawn mountain, a bare warming slope --
and is now ONE night mountain held for thirteen seconds while the presenter
arrives, a heat front advances, the snow bares, he comes back holding a packet
AND STAYS while the meltwater channel drifts open beside him. That is the
"something MOVES and APPEARS inside a stage the viewer can settle on" the brief
asks for, and holding him through the last beat is what stops the chapter from
getting quieter exactly where it should be loudest.

WHAT IS DELIBERATELY NOT DONE. No art primitive is redrawn and no caption is
shortened or reworded -- every caption is still clock.ph() straight out of
segments/svalbard/beats.json. Where a beat's art cannot share a frame with its
neighbour (the b03 map, the b19 vault-door close-up, the b25 talking head), that
beat either became its own bg stage or was re-composed from the SAME primitives
onto its stage's world, and the comment at the call site says which. Captions
stay only on the beats that carry a fact the drawn art does not -- the b35
caption was removed precisely because it repeated a label already drawn in the
frame, which is the tell-AND-show redundancy the brief is written against.

Rule 5 (the engine stamps the title LAST): this file never draws scene.title.
Rule 7 (engine3._apply_transform moves an element's own tile, never the frame):
every arrival here uses motion=, never a redraw, so nothing drags a sibling.

Run:  python lib/svalbard2_scene.py --preview --video
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
import v2type as VT

import svalbard_scene as SV     # art primitives + palette, reused not copied

# identity, reused from v1
SEG = SV.SEG
TITLE = SV.TITLE
BEATS = SV.BEATS
TITLE_BACKDROP = SV.TITLE_BACKDROP

# palette, reused from v1.
INK = SV.INK
SNOW = SV.SNOW
AMBER = SV.AMBER
AMBER_LT = SV.AMBER_LT
LEAF = SV.LEAF
RED = SV.RED
WATER = SV.WATER
CONCRETE = SV.CONCRETE
STEEL = SV.STEEL
TITLE_COURSE = SV.TITLE_COURSE
# ICE and SLATE are the permafrost's own two values; the thaw beat re-draws the
# frozen band in place so the corridor it sits over is the SAME corridor.
ICE = SV.ICE
SLATE = SV.SLATE

# The style canon's cream figure for DARK cards. character3 draws him near-black
# (BODY 26,26,30), which is right on the paper cards and invisible against the
# night mountain and the tunnel. Passed as ink= to SC.fullbody on those beats.
CREAM = (240, 238, 230)

W, H = SV.W, SV.H
HZ = SV.HZ

# art primitives, reused from v1
_arctic = SV._arctic
_day_arctic = SV._day_arctic
_interior = SV._interior
_mountain = SV._mountain
_wedge = SV._wedge
_doorway = SV._doorway
_tunnel = SV._tunnel
_shelf = SV._shelf
_packet = SV._packet
_globe = SV._globe
_cutaway = SV._cutaway
_camera = SV._camera
_snow_hatch = SV._snow_hatch
_excavator = SV._excavator
_flood_gate = SV._flood_gate
_light_wedge = SV._light_wedge


def _soft_beam(d, x, y0, y1, half, seed, colour=None):
    """A wedge of LIGHT, not a gold cone.

    SV._light_wedge fills one solid AMBER_LT triangle, which on the dark
    exterior reads as an opaque pyramid -- two of them at b30 looked like
    traffic cones. This draws the beam as nested triangles from widest and
    dimmest to narrowest and brightest, plus a bright pool where it lands, so
    it reads as light spreading out of a lamp rather than a solid shape.

    Kept from the previous pass. It is a STAGE-WORLD element, not a layer: a
    wedge this wide covers a lot of the frame, so it belongs in the world that
    a stage paints rather than arriving on top of one.
    """
    colour = colour or AMBER_LT
    steps = 6
    # The beam is painted on its OWN RGBA layer and alpha-composited once at the
    # end. Six opaque nested triangles painted straight onto the tile produced a
    # solid gold pyramid -- the traffic-cone defect -- and the first attempt at
    # fixing it modulated the tile's own alpha channel, which is a no-op because
    # compositing a channel against itself returns the channel. Light is not
    # opaque: it thins as it spreads, so the layer's own alpha is the whole
    # point and it has to be a separate layer to exist at all.
    layer = Image.new('RGBA', PA.img_of(d).size, (0, 0, 0, 0))
    for i in range(steps):
        f = 1.0 - i / float(steps)          # 1.0 (widest, base layer) -> ~0.17
        hf = half * (0.30 + 0.70 * f)
        y0i = y0 + (y1 - y0) * (1.0 - f) * 0.55
        # the widest layer is nearly clear; the narrow core is where the light
        # actually is. This gradient is what reads as light rather than paint.
        a = int(18 + 128 * (i / float(steps - 1)) ** 1.7)
        shade = tuple(min(255, int(c + (255 - c) * (i / float(steps)) * 0.55))
                      for c in colour)
        tri = [(x - hf * 0.12, y0i), (x + hf * 0.12, y0i),
               (x + hf, y1), (x - hf, y1)]
        PA.fill_poly(layer, tri, shade, seed=seed + i, value=0.05)
        if a < 255:
            m = Image.new('L', layer.size, 0)
            ImageDraw.Draw(m).polygon([tuple(p) for p in tri], fill=a)
            layer.putalpha(Image.composite(layer.split()[3],
                                          Image.new('L', layer.size, 0), m))
    pool = PA.ellipse_pts(x, y1, half * 0.9, 26, n=40)
    PA.fill_poly(layer, pool, (236, 240, 226), seed=seed + 40, value=0.06)
    PA.img_of(d).alpha_composite(layer)


def _frost_bank(d, x0, x1, ybase, lo, hi, seed, colour=(233, 243, 250),
                step=132.0):
    """A bank of ICE as a filled mass with a soft, uneven upper boundary.

    Kept from the previous pass, unchanged. Frost that does not CONNECT does not
    read as a substance, so this fills a bank from a solid base up to a crest,
    and the crest is a three-octave wobble (a sawtooth reads as a sawblade).
    """
    pts = [(x0, ybase), (x1, ybase)]
    steps = max(4, int((x1 - x0) / step))
    span = float(hi - lo)
    for s in range(steps + 1):
        u = s / float(steps)
        px = x0 + (x1 - x0) * u
        crest = (0.50 * math.sin(u * 3.1 + seed * 0.017)
                 + 0.30 * math.sin(u * 7.3 + seed * 0.031 + 1.1)
                 + 0.20 * math.sin(u * 15.7 + seed * 0.023 + 2.7))
        py = lo + span * (0.5 + 0.5 * crest)
        pts.append((px, py))
    PA.fill_poly(PA.img_of(d), PA.wobble_edge(pts, seed=seed, amount=2.0,
                                              wavelength=72.0),
                 colour, seed=seed, value=0.05, edge=0.0)


def _frost_crystals(d, x0, x1, ycrest, n, seed, colour=(226, 240, 249)):
    """A FEW crystal spikes standing off a frost crest.

    Deliberately sparse and irregular. The v3 pass put two dendrites on every
    blob, which at 60-odd blobs became a field of snowflakes; hoar grows in a
    few directions from a few nucleation points, so these are longer than they
    are numerous and none of them share an angle.
    """
    for k in range(n):
        px = x0 + (x1 - x0) * ((k * 0.618 + 0.11) % 1.0)
        py = ycrest + ((k * 23) % 9 - 4) * 5
        a = 2.1 + ((k * 0.41) % 1.0) * 2.2          # up and to the sides only
        ln = 26 + (k * 17) % 40
        PA.hand_stroke(d, [(px, py), (px + ln * math.cos(a), py + ln * math.sin(a))],
                       colour, 5, closed=False, seed=seed + k, wavelength=30.0)
        for j in (-1, 1):                            # two barbs near the tip
            bx = px + ln * 0.62 * math.cos(a)
            by = py + ln * 0.62 * math.sin(a)
            ba = a + j * 0.75
            PA.hand_stroke(d, [(bx, by),
                               (bx + ln * 0.44 * math.cos(ba),
                                by + ln * 0.44 * math.sin(ba))],
                           colour, 4, closed=False, seed=seed + 40 + k * 2 + j,
                           wavelength=22.0)


# =========================================================================== #
# EDGE-DENSITY HELPERS.
#
# WHY THESE EXIST. The label-blind critic scored this chapter's frames as flat
# vector, and the per-beat pigment measurement agreed on 32 of 35 beats (median
# 24px-tile luma std ~3.1 against an eye-calibrated paint bar of 8.0). The three
# beats that DID measure painted -- b08/b09/b10, 28.9 to 42.8 -- are the three
# that stack many SMALL OUTLINED SHAPES: five shelf runs of thirteen foil
# packets, sixty-five little rectangles edge to edge across the whole frame.
# A single big mountain on a smooth snowfield measures 3.1 no matter how much
# paint the fills carry, because the frame is dominated by a few LARGE SMOOTH
# REGIONS and a 24px tile inside one of them sees no local variation at all.
#
# So the lever is not the paint engine (v2paint is already painting every fill
# here) and it is not noise. It is GEOMETRY: break every large smooth region
# into a stack of many small outlined shapes. These helpers are the vocabulary.
#
# THE RULES THEY FOLLOW, all learned from the shipped frames:
#   * Structure runs OFF the frame edge. A slab run that stops at x=1000 with
#     snow beyond it admits the drawing stopped; one that leaves at x=1300
#     admits the mountain is bigger than the picture.
#   * Structure is COARSEST AT THE BACK and finest at the front, so the depth
#     order is readable without any shading.
#   * Every shape is outlined. The outline is what puts an edge inside the tile;
#     a fill alone does not.
#   * Nothing here touches the title band (y<86) or the caption band.
#   * Everything is seeded, so two renders are byte-identical.
# =========================================================================== #


def _clipped_stroke(d, pts, colour, lw, seed, clip):
    """One hand_stroke confined to an L-mask.

    The crevasses over the permafrost band have to stay off the corridor. A
    stroke is drawn on a scratch layer and composited through the mask, which
    is the same trick _rock_strata uses; this exists as its own helper because
    the alternative -- passing a clip to every call site -- reads worse than one
    function that takes one.
    """
    img = PA.img_of(d)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    PA.hand_stroke(ImageDraw.Draw(layer), pts, colour, lw, closed=False,
                   seed=seed, wavelength=150.0)
    a = layer.split()[3]
    img.paste(layer, (0, 0),
              Image.composite(a, Image.new('L', img.size, 0), clip))


def _rock_strata(d, x0, x1, y0, y1, seed, n=7, col=(96, 104, 118),
                 ink=INK, lw=4, wobble_amp=9.0, clip=None):
    """Layered rock contour bands -- permafrost strata through the mountain.

    The mountain mass is one smooth polygon, so every 24px tile inside it reads
    flat. These are stacked wavy contour lines with a slightly different fill
    value per band, which is how permafrost is actually drawn and what turns one
    dead grey mass into readable geology. Bands alternate value by ~10 levels,
    which is under the intrusion gate's DEV=25 so the title band is untouched.

    `clip` is an optional PIL L-mask; strata are drawn on a scratch layer and
    composited through it, so they can be confined to a mountain silhouette
    instead of a bounding box. WITHOUT a clip the bands run the full width of
    the frame and paint over the sky, which is exactly the bug the first pass
    shipped -- a rect-bounded strata helper is a lid, not a layer.
    """
    img = PA.img_of(d)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for k in range(n):
        t = k / float(max(1, n - 1))
        base = y0 + (y1 - y0) * t
        amp = wobble_amp * (0.5 + t)
        pts = []
        steps = max(6, int((x1 - x0) / 130.0))
        for s in range(steps + 1):
            u = s / float(steps)
            px = x0 + (x1 - x0) * u
            py = (base
                  + amp * math.sin(u * 4.3 + seed * 0.013 + k * 0.9)
                  + amp * 0.55 * math.sin(u * 9.1 + seed * 0.029 + k * 1.7)
                  + amp * 0.30 * math.sin(u * 17.3 + seed * 0.007 + k * 0.4))
            pts.append((px, py))
        shade = (min(255, int(col[0] - 9 * math.sin(k * 1.3))),
                 min(255, int(col[1] - 8 * math.sin(k * 1.3 + 0.8))),
                 min(255, int(col[2] - 7 * math.sin(k * 1.3 + 1.6))))
        PA.hand_stroke(ld, pts, shade, 26 + 6 * (k % 3), closed=False,
                       seed=seed + k * 5, wavelength=140.0, vary=0.16)
        PA.hand_stroke(ld, pts, ink, lw, closed=False, seed=seed + 60 + k,
                       wavelength=150.0)
    if clip is None:
        img.alpha_composite(layer)
    else:
        a = layer.split()[3]
        img.paste(layer, (0, 0), Image.composite(a, Image.new('L', img.size, 0),
                                                 clip))


def _slope_creases(d, ridge, seed, clip, n=16):
    """Couloir / crevasse lines running DOWN a mountain's face, clipped to it.

    A mountain's structure runs down its slope. Nine near-horizontal bands
    across the mass (the first attempt at this) read as venetian blinds, which
    is worse than the smooth polygon they replaced. These lines start along the
    ridge and run to the base, wander as they fall, and fork -- which is what a
    snow face actually looks like and what puts local edges through the middle
    of the mass.

    `clip` is the mountain's silhouette mask; without it the lines would run
    across the sky.
    """
    img = PA.img_of(d)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # the ridge's upper vertices are the couloir mouths
    mouths = ridge[1:len(ridge) - 1]
    base_y = ridge[-1][1]
    for k in range(n):
        m = mouths[k % len(mouths)]
        x0 = m[0]
        y0 = m[1]
        # a wander that grows as it falls, so the line is not a straight slash
        pts = []
        steps = 7
        for s in range(steps + 1):
            u = s / float(steps)
            px = (x0 + 46 * u * math.sin(k * 1.7 + u * 3.1)
                  + 14 * math.sin(u * 9.0 + k * 2.3))
            py = y0 + (base_y - y0) * (u ** 0.86)
            pts.append((px, py))
        PA.hand_stroke(ld, pts, (48, 54, 66), 7, closed=False,
                       seed=seed + k * 5, wavelength=120.0, vary=0.24)
        PA.hand_stroke(ld, [(px - 3, py) for px, py in pts], (150, 162, 180), 3,
                       closed=False, seed=seed + 70 + k, wavelength=90.0)
        # a fork off the main line, about a third of the way down
        if k % 2 == 0:
            j = 2 + (k % 3)
            fx, fy = pts[j]
            PA.hand_stroke(ld, [(fx, fy), (fx + 54, fy + 96)], (56, 62, 74), 5,
                           closed=False, seed=seed + 140 + k, wavelength=70.0)
    a = layer.split()[3]
    img.paste(layer, (0, 0), Image.composite(a, Image.new('L', img.size, 0),
                                             clip))


def _snow_blocks(d, x0, x1, ybase, seed, n=9, h=74, col=(232, 238, 246)):
    """A run of wind-carved SNOW DRIFTS along the ground line.

    The snow plain was a smooth white field across the bottom third of the
    frame -- dead pixels by the paint measure AND by the eye. A drift is not a
    smooth field; it is a low asymmetric mound with a soft crest, a shadowed
    lee face and a sastrugi ridge on top.

    THE FIRST PASS DREW SHARP TRIANGLES and they read as a row of white tents
    pitched on the snow. What makes a drift read as a drift is (a) the crest is
    a long shallow ARC, not a peak, (b) the mound is wide relative to its height,
    (c) it has a shaded lee face in a DIFFERENT value from its lit face, and
    (d) consecutive drifts overlap so there is no regular rhythm. All four are
    load-bearing.
    """
    img = PA.img_of(d)
    step = float(x1 - x0) / n
    for k in range(n):
        x = x0 + k * step - step * 0.35          # overlaps its neighbour
        cw = step * (2.0 + 0.5 * math.sin(k * 1.7))
        hh = h * (0.62 + 0.38 * abs(math.sin(k * 2.3 + 0.7)))
        skew = 0.30 * math.sin(k * 1.1)         # wind pushes the crest off-centre
        # the crest: a long shallow arc, sampled as a wobbled quadratic
        top = []
        steps = 9
        for s in range(steps + 1):
            u = s / float(steps)
            px = x + cw * u
            shape = math.sin(math.pi * min(1.0, max(0.0, (u - skew) / 0.72 + 0.36)))
            py = (ybase - hh * max(0.0, shape)
                  + 7 * math.sin(u * 7.3 + k * 1.9)
                  + 4 * math.sin(u * 13.1 + k * 0.7))
            top.append((px, py))
        face = top + [(x + cw, ybase + 60), (x, ybase + 60)]
        lit = col
        lee = (col[0] - 26, col[1] - 24, col[2] - 18)
        PA.fill_poly(img, PA.wobble_edge(face, seed=seed + k * 4, amount=2.6,
                                         wavelength=110.0),
                     lit, seed=seed + k * 6, value=0.05, edge=0.0)
        # the sastrugi -- a shaded crease along the crest's lee side. This is the
        # line that stops a white mound reading as a white triangle.
        lee_pts = [(px, py + 13 + 6 * math.sin(u * 5.1 + k))
                   for u, (px, py) in enumerate(top)]
        PA.hand_stroke(d, lee_pts, lee, 9, closed=False, seed=seed + 90 + k,
                       wavelength=70.0, vary=0.22)
        PA.hand_stroke(d, top, (255, 255, 255), 3, closed=False,
                       seed=seed + 130 + k, wavelength=90.0)
        PA.hand_stroke(d, lee_pts, (178, 190, 204), 2, closed=False,
                       seed=seed + 170 + k, wavelength=60.0)


def _snow_contours(d, x0, x1, ytop, ybase, seed, n=6,
                   col=(214, 226, 238), lw=4):
    """Layered drift contour lines across an open snow field.

    The plain's version of edge density: long shallow contour lines that follow
    the lie of the ground, receding bands of a slightly cooler value.

    THEY CURVE WITH THE GROUND. The first pass emitted nearly-straight lines at
    fixed y and they read as fence wires strung across the mountain, because
    every one of them was at the same height and none acknowledged a dune. Here
    each contour is a long arc that dips in the middle of the frame and lifts at
    the sides, which is the lie of a broad drift, and successive contours are
    offset horizontally so they never stack into a picket fence.
    """
    img = PA.img_of(d)
    for k in range(n):
        t = k / float(max(1, n - 1))
        y = ybase - (ybase - ytop) * (0.16 + 0.84 * t)
        pts = []
        steps = max(8, int((x1 - x0) / 110.0))
        for s in range(steps + 1):
            u = s / float(steps)
            px = x0 + (x1 - x0) * u
            # the ground's own curve: a broad sag plus two smaller swells
            sag = 26 * math.sin(math.pi * u) * (0.6 + 0.4 * math.sin(k * 1.3))
            py = (y - sag
                  + 13 * math.sin(u * 2.7 + seed * 0.011 + k * 0.9)
                  + 7 * math.sin(u * 6.1 + seed * 0.023 + k * 2.1))
            pts.append((px, py))
        PA.hand_stroke(d, pts, (col[0], col[1] - 5 * k, col[2] - 4 * k), lw,
                       closed=False, seed=seed + k * 4, wavelength=190.0)
        PA.hand_stroke(d, [(px, py - 5) for px, py in pts],
                       (250, 252, 254), 2, closed=False, seed=seed + 70 + k,
                       wavelength=140.0)


def _ice_blocks(d, x0, x1, ytop, ybot, seed, n=11,
                col=(150, 176, 196), ink=(96, 124, 148), clip=None):
    """A run of outlined ice blocks through the frozen band.

    The permafrost band was one flat ICE rectangle with a comb of hatching over
    it. Blocks with real joints between them read as a frozen mass AND put an
    edge in every tile of the band, which is where four of this chapter's flat
    beats spend their frame.

    `clip` is an optional PIL L-mask. It is here for a specific reason: the
    frozen band and the corridor OVERLAP (the corridor runs y 386..554, the
    band y 330..560), so an unclipped run of blocks paints straight over the
    tunnel and the beat whose caption says "a long tunnel runs down into the
    rock" loses its tunnel. Pass a mask with the corridor punched out of it.
    """
    img = PA.img_of(d)
    if clip is not None:
        layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        img, d = layer, ImageDraw.Draw(layer)
    step = float(x1 - x0) / n
    for k in range(n):
        x = x0 + k * step
        h = (ybot - ytop) * (0.62 + 0.38 * abs(math.sin(k * 1.31)))
        top = []
        steps = 4
        for s in range(steps + 1):
            u = s / float(steps)
            px = x + step * 1.02 * u
            py = (ytop + (ybot - ytop - h) * 0.5 * math.sin(u * 3.0 + k * 0.8)
                  + 6 * math.sin(u * 7.0 + k * 1.3))
            top.append((px, py))
        face = top + [(x + step * 1.02, ybot + 30), (x, ybot + 30)]
        shade = (col[0] + (k % 3) * 6 - 6, col[1] + (k % 3) * 5 - 5,
                 col[2] + (k % 3) * 4 - 4)
        PA.fill_poly(img, PA.wobble_edge(face, seed=seed + k * 5, amount=2.0,
                                         wavelength=60.0),
                     shade, seed=seed + k * 7, value=0.05, edge=0.0)
        PA.hand_stroke(d, top, ink, 4, closed=False, seed=seed + 90 + k,
                       wavelength=70.0)
        # the joint: a short vertical dark seam at the block's left edge
        PA.hand_stroke(d, [(x + step * 0.04, top[0][1] + 8),
                           (x + step * 0.02, ybot - 6)], ink, 3, closed=False,
                       seed=seed + 140 + k, wavelength=60.0)
    if clip is not None:
        a = layer.split()[3]
        PA.img_of(d).paste(layer, (0, 0),
                           Image.composite(a, Image.new('L', layer.size, 0),
                                           clip))


def _rubble(d, x0, x1, ybase, seed, n=18, col=(128, 134, 142),
            spread=26.0, scale=1.0):
    """Small outlined rock chips scattered on a ground line.

    Cheap, and it is what stops a large ground plane reading as a fill: forty
    little stones with an outline each put a corner in every tile near the
    base. Deterministic by construction (a fixed stride walk, not random).
    """
    img = PA.img_of(d)
    for k in range(n):
        u = ((k * 0.61803398875) % 1.0)
        x = x0 + (x1 - x0) * u
        y = ybase + spread * math.sin(k * 2.3) - (k % 3) * 7
        r = (9 + (k * 7) % 13) * scale
        pts = []
        m = 6
        for s in range(m):
            a = 2 * math.pi * s / m
            rr = r * (0.72 + 0.42 * math.sin(s * 2.1 + k))
            pts.append((x + rr * math.cos(a), y + rr * 0.66 * math.sin(a)))
        PA.fill_poly(img, pts, (col[0] + (k % 3) * 8 - 6,
                                col[1] + (k % 3) * 6 - 5,
                                col[2] + (k % 3) * 5 - 4),
                     seed=seed + k * 5, value=0.06, edge=0.0)
        PA.hand_stroke(d, pts, INK, 3, closed=True, seed=seed + 80 + k,
                       wavelength=30.0)


def _pipe_run(d, x0, x1, y, seed, n=6, r=13, col=(120, 128, 138)):
    """A run of conduit with collars along a wall -- industrial edge density.

    The interiors were two flat fills (wall, floor) plus one warm ellipse. Pipes
    with collars, a cable tray and a strut every bay are what make a cut rock
    chamber read as a built room, and they are what a corridor close-up needs to
    stop being two rectangles.
    """
    img = PA.img_of(d)
    for k in range(n):
        x = x0 + (x1 - x0) * k / float(max(1, n - 1))
        PA.fill_rect(img, [x - r, y - r, x + r, y + r], col, seed=seed + k * 3,
                     value=0.06, edge=1.2)
        PA.hand_stroke(d, [(x - r, y - r), (x + r, y - r), (x + r, y + r),
                           (x - r, y + r)], INK, 3, closed=True,
                       seed=seed + 40 + k, wavelength=40.0)
    PA.hand_stroke(d, [(x0, y), (x1, y)], (86, 94, 104), r * 2 - 6, closed=False,
                   seed=seed + 90, wavelength=170.0)
    PA.hand_stroke(d, [(x0, y - 2), (x1, y - 2)], INK, 3, closed=False,
                   seed=seed + 91, wavelength=170.0)


def _strut_run(d, x0, x1, ytop, ybot, seed, n=7, col=(104, 112, 124)):
    """Vertical wall struts between two heights -- a ribbed rock face.

    Used on the corridor walls and the cutaway's chamber. Cheap, evenly spaced,
    and it makes a tall smooth wall read as shored ground rather than a fill.
    """
    for k in range(n):
        x = x0 + (x1 - x0) * k / float(max(1, n - 1))
        PA.hand_stroke(d, [(x, ytop + 6 * math.sin(k * 1.7)),
                           (x + 3, ybot - 6 * math.sin(k * 2.3))], col, 9,
                       closed=False, seed=seed + k * 4, wavelength=90.0)
        PA.hand_stroke(d, [(x, ytop + 6 * math.sin(k * 1.7)),
                           (x + 3, ybot - 6 * math.sin(k * 2.3))], INK, 3,
                       closed=False, seed=seed + 60 + k, wavelength=90.0)
        # a bearing plate at each end so the strut has a head and a foot
        for yy in (ytop, ybot):
            PA.fill_rect(PA.img_of(d), [x - 15, yy - 8, x + 19, yy + 8],
                         (122, 130, 142), seed=seed + 90 + k * 2, value=0.05,
                         edge=1.2)
            PA.hand_stroke(d, [(x - 15, yy - 8), (x + 19, yy - 8),
                               (x + 19, yy + 8), (x - 15, yy + 8)], INK, 3,
                           closed=True, seed=seed + 130 + k * 2, wavelength=40.0)


def _panel_run(d, x0, x1, y0, y1, seed, n=5, col=(146, 152, 162),
               rivets=True):
    """Steel plating panels with rivets -- fortknox's gold-slab density in the
    chapter's own grey.

    The vault door and the flood gate are big smooth steel fields. Riveted
    plates are what a vault door IS, they survive at any size, and they give the
    eye the small-scale detail the frame-fill rule asks for.
    """
    img = PA.img_of(d)
    step = float(x1 - x0) / n
    for k in range(n):
        x = x0 + k * step
        box = [(x + 5, y0 + 5), (x + step - 5, y0 + 5),
               (x + step - 5, y1 - 5), (x + 5, y1 - 5)]
        PA.fill_poly(img, PA.wobble_edge(box, seed=seed + k * 4, amount=1.8,
                                         wavelength=70.0),
                     (col[0] + (k % 3) * 7 - 7, col[1] + (k % 3) * 6 - 6,
                      col[2] + (k % 3) * 5 - 5),
                     seed=seed + k * 6, value=0.06, edge=0.0)
        PA.hand_stroke(d, box, INK, 5, closed=True, seed=seed + 80 + k,
                       wavelength=90.0)
        if rivets:
            for m in (0.16, 0.84):
                for yy in (y0 + 22, y1 - 22):
                    px = x + step * m
                    d.ellipse([px - 5, yy - 5, px + 5, yy + 5],
                              fill=(96, 102, 112))
                    PA.hand_stroke(d, [(px - 5, yy - 5), (px + 5, yy - 5),
                                       (px + 5, yy + 5), (px - 5, yy + 5)],
                                   INK, 2, closed=True, seed=seed + 120 + k * 4,
                                   wavelength=20.0)


def _star_field(d, x0, x1, y0, y1, seed, n=90, col=(226, 234, 246)):
    """A scattering of stars in a night sky band.

    Cheap per star, and it is the honest fix for a flat sky: a night sky with
    nothing in it is a gradient, and a gradient is exactly what the pigment
    measure calls flat. Deterministic stride walk, three sizes, three values.
    """
    img = PA.img_of(d)
    for k in range(n):
        u = (k * 0.7548776662) % 1.0
        v = (k * 0.5698402909) % 1.0
        px = x0 + (x1 - x0) * u
        py = y0 + (y1 - y0) * v
        r = 2 + (k % 4)
        c = col if k % 5 else (250, 246, 226)
        d.ellipse([px - r, py - r, px + r, py + r], fill=c)


def _ground_plates(d, x0, x1, ytop, ybase, seed, n=7,
                   col=(96, 104, 118)):
    """Concrete floor slabs in perspective -- the deck the flood stands in.

    A flooded corridor's floor is the largest single region in frame and it was
    one flat fill. Slab joints running to a vanishing point plus a kerb line put
    an edge in every tile of it.
    """
    img = PA.img_of(d)
    for k in range(n):
        t = k / float(max(1, n - 1))
        y = ytop + (ybase - ytop) * (t ** 1.6)
        half = 40 + 700 * (t ** 1.5)
        PA.hand_stroke(d, [(640 - half, y + 12), (640 + half, y + 12)],
                       (col[0] - 10, col[1] - 10, col[2] - 8), 4, closed=False,
                       seed=seed + k * 4, wavelength=140.0)
    for k in range(-3, 4):
        x0j = 640 + k * 118
        PA.hand_stroke(d, [(x0j, ybase), (640 + k * 470, ytop)],
                       (col[0] - 6, col[1] - 6, col[2] - 5), 3, closed=False,
                       seed=seed + 50 + k, wavelength=120.0)
    PA.hand_stroke(d, [(0, ytop), (1280, ytop)], (col[0] + 16, col[1] + 16,
                                                 col[2] + 16), 6,
                   closed=False, seed=seed + 99, wavelength=170.0)


def _wall_panels(d, x0, x1, y0, y1, seed, n=6, col=(96, 104, 116),
                 ink=INK, lw=4, skip=None, row_h=112.0):
    """Shed panels bolted to a room's back wall -- the interior's edge density.

    EVERY `_interior` room in this chapter is two flat fills (wall, floor) plus
    sometimes one warm ellipse, and every one of them measured 2.6-3.3 until
    this went on: five of the chapter's flat beats spend their whole frame
    inside a room. This is the same idea as _panel_run, tuned for a large flat
    back wall: a grid of bolted sheets with a seam and a rivet in each bay, so
    the wall has an edge every ~150px instead of none at all.

    `skip` is an optional list of (x0, x1, y0, y1) rectangles left clear, so a
    caller can keep a lit doorway or a numeral unpanelled.
    """
    img = PA.img_of(d)
    step = float(x1 - x0) / n
    rows = max(2, int((y1 - y0) / row_h))

    def clear(px, py):
        if not skip:
            return False
        for s in skip:
            if s[0] <= px <= s[1] and s[2] <= py <= s[3]:
                return True
        return False

    for r in range(rows):
        ry0 = y0 + (y1 - y0) * r / rows
        ry1 = y0 + (y1 - y0) * (r + 1) / rows
        for k in range(n):
            x = x0 + k * step
            cx = x + step * 0.5
            cy = (ry0 + ry1) * 0.5
            if clear(cx, cy):
                continue
            box = [(x + 4, ry0 + 4), (x + step - 4, ry0 + 4),
                   (x + step - 4, ry1 - 4), (x + 4, ry1 - 4)]
            PA.fill_poly(img, PA.wobble_edge(box, seed=seed + r * 20 + k * 3,
                                             amount=1.6, wavelength=80.0),
                         (col[0] + ((r + k) % 3) * 6 - 6,
                          col[1] + ((r + k) % 3) * 5 - 5,
                          col[2] + ((r + k) % 3) * 4 - 4),
                         seed=seed + r * 20 + k * 3 + 1, value=0.06, edge=0.0)
            PA.hand_stroke(d, box, ink, lw, closed=True,
                           seed=seed + 200 + r * 20 + k, wavelength=100.0)
            # four rivets, one per corner of the sheet
            for mx, my in ((0.14, 0.16), (0.86, 0.16), (0.14, 0.84), (0.86, 0.84)):
                px = x + step * mx
                py = ry0 + (ry1 - ry0) * my
                d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(74, 80, 90))
                PA.hand_stroke(d, [(px - 4, py - 4), (px + 4, py - 4),
                                   (px + 4, py + 4), (px - 4, py + 4)], ink, 2,
                               closed=True, seed=seed + 400 + r * 20 + k,
                               wavelength=20.0)


def _ceiling_beams(d, x0, x1, y, seed, n=6, col=(84, 92, 104)):
    """I-beams across a room's ceiling -- depth on the largest empty band.

    A cold room's ceiling is usually the widest unbroken region in frame, and
    it is the region the camera looks along, so beams running to a vanishing
    point are what turn it into a room rather than a grey lid.
    """
    for k in range(n):
        x = x0 + (x1 - x0) * k / float(max(1, n - 1))
        depth = 30 if k % 2 == 0 else 22          # near/far alternate
        box = [(x - 16, y), (x + 16, y), (x + 16, y + depth), (x - 16, y + depth)]
        PA.fill_poly(PA.img_of(d), PA.wobble_edge(box, seed=seed + k * 4,
                                                   amount=1.4, wavelength=40.0),
                     (col[0] + (k % 3) * 7 - 7, col[1] + (k % 3) * 6 - 6,
                      col[2] + (k % 3) * 5 - 5),
                     seed=seed + k * 4 + 1, value=0.06, edge=0.0)
        PA.hand_stroke(d, box, INK, 4, closed=True, seed=seed + 60 + k,
                       wavelength=50.0)
        # the web, so it reads as an I-beam and not a plank
        PA.hand_stroke(d, [(x - 6, y + depth * 0.5), (x + 6, y + depth * 0.5)],
                       (70, 76, 86), 3, closed=False, seed=seed + 90 + k,
                       wavelength=30.0)


def _cable_tray(d, x0, x1, y, seed, col=(96, 88, 60), n_cable=4):
    """A cable tray with slack loops, run off both edges along a wall."""
    PA.fill_rect(PA.img_of(d), [x0, y, x1, y + 20], (88, 94, 104), seed=seed,
                 value=0.06, edge=1.2)
    PA.hand_stroke(d, [(x0, y), (x1, y), (x1, y + 20), (x0, y + 20)], INK, 4,
                   closed=True, seed=seed + 1, wavelength=180.0)
    for k in range(n_cable):
        cy = y + 4 + k * 4
        PA.hand_stroke(d, [(x0, cy), (x1, cy)], col, 3, closed=False,
                       seed=seed + 10 + k, wavelength=190.0)


def _floor_crates(d, x0, x1, ybase, seed, n=5, col=(122, 116, 102), h=86):
    """Stacked crates and a pallet on a room's floor.

    The floor of every interior stage here is the region BELOW the caption band,
    and it was the last dead area on the beats where the wall already carried
    panels. Crates are the honest thing in a working cold store and they run off
    the side edges, so the floor admits the room continues past the picture.
    """
    img = PA.img_of(d)
    step = float(x1 - x0) / n
    for k in range(n):
        x = x0 + k * step
        w = step * (0.72 + 0.22 * math.sin(k * 1.9))
        ch = h * (0.6 + 0.4 * abs(math.sin(k * 2.7 + 0.4)))
        # a crate is a box with a corner-bracket and a slat, not a plain square
        PA.fill_rect(img, [x, ybase - ch, x + w, ybase], col, seed=seed + k * 5,
                     value=0.07, edge=1.4)
        PA.hand_stroke(d, [(x, ybase - ch), (x + w, ybase - ch),
                           (x + w, ybase), (x, ybase)], INK, 5, closed=True,
                       seed=seed + 40 + k, wavelength=60.0)
        PA.hand_stroke(d, [(x + 5, ybase - ch * 0.62), (x + w - 5, ybase - ch * 0.62)],
                       (col[0] - 16, col[1] - 15, col[2] - 12), 4, closed=False,
                       seed=seed + 80 + k, wavelength=40.0)
        PA.hand_stroke(d, [(x + 4, ybase - ch), (x + w - 4, ybase - 4)],
                       (col[0] - 22, col[1] - 20, col[2] - 16), 4, closed=False,
                       seed=seed + 110 + k, wavelength=50.0)
        # the pallet it stands on: three bearers, so the crate has a foot
        for m in (0.16, 0.5, 0.84):
            PA.fill_rect(img, [x + w * m - 6, ybase, x + w * m + 6, ybase + 12],
                         (94, 88, 76), seed=seed + 140 + k, value=0.06, edge=1.0)
        PA.hand_stroke(d, [(x - 4, ybase + 12), (x + w + 4, ybase + 12)], INK, 4,
                       closed=False, seed=seed + 170 + k, wavelength=40.0)


def _room_shell(tile, d, seed, wall_col=(88, 96, 108), floor_col=(66, 72, 84),
                floor_at=0.74, ceil_beams=True, panels=True, tray=True,
                tray_at=None, panels_skip=None, panel_n=7, row_h=112.0,
                crates=None):
    """Everything that makes an `_interior` room stop being two flat fills.

    Called by every interior stage in the chapter after its own `_interior`, so
    one edit lifts b11-b12, b15, b16-b17, b18-b19 and b22-b25 at once. Written
    as one function because the per-room variation that matters (which walls,
    whether a tray) is four keyword arguments, not five copies of this code.
    """
    yfloor = int(H * floor_at)
    if panels:
        _wall_panels(d, -30, W + 30, 96, yfloor - 4, seed, n=panel_n,
                     col=(wall_col[0] + 8, wall_col[1] + 8, wall_col[2] + 8),
                     skip=panels_skip, row_h=row_h)
    if ceil_beams:
        _ceiling_beams(d, -20, W + 20, 96, seed + 200, n=7)
    if tray:
        _cable_tray(d, -20, W + 20,
                    yfloor - 96 if tray_at is None else tray_at, seed + 300)
    # FLOOR: slabs receding to a vanishing point + a kerb, so the largest single
    # region in most of these rooms has joints in it.
    _ground_plates(d, -20, W + 20, yfloor + 6, H + 20, seed + 400, n=7,
                   col=floor_col)
    if crates:
        _floor_crates(d, -30, W + 30, H - 46, seed + 600, n=crates)


# The arrival duration used by every moving element. 0.45-0.6s reads as a
# deliberate move; longer and the element stops being an arrival and starts
# being the picture changing every sample.
ARRIVE = 0.5

# REFRAME_MAX is 0.30 of the frame. These are the coverage budgets the details
# in this file were sized against, measured as (bounding box area / 1280*720).
# A detail over the budget reads to the viewer as a new picture even though the
# stage held, which is exactly the defect the previous build had 23 of.
DETAIL_BUDGET = 0.30


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
    # STAGE S1  b01-b03  "Beneath an Arctic mountain, the world's seeds      #
    #                    sleep. / This is the Svalbard Global Seed Vault. /   #
    #                    It opened in 2008, on a Norwegian island."          #
    # The night exterior is the WORLD and it is held for all three beats.     #
    # Three things arrive inside it: the presenter walks in from the right, the #
    # vault's name is stamped across the sky, and 2008 lands on the peak.      #
    # Previously b03 was a full-frame MAP that repainted 91% of the frame --   #
    # a cut to a different picture on the beat that says "2008". The map is    #
    # gone; what carries the year now is the drawn numeral plus the caption,  #
    # which is the one thing a mountain cannot draw.                          #
    # ===================================================================== #
    def s1_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 5)
        # Stars. The night sky was two smooth fills -- measured 3.14, the flattest
        # reading in the chapter -- and a night sky with nothing in it IS a
        # gradient, so this is the honest fix rather than a texture cheat.
        _star_field(d, 8, 1272, 92, 262, 3001, n=110)
        SC.title_backdrop(tile, 1005, col=TITLE_COURSE)
        # THE MOUNTAIN, scaled up so it dominates. It used to peak at y=300 with
        # its base at 452: a 186px band marooned in the middle of a 720px frame,
        # with the bottom 38% an empty snowfield. crest=176/base=600 puts the
        # ridge high and the mass down into the plain, and the ridge polyline
        # already runs off both side edges.
        ridge = _mountain(d, 7, crest=176, base=612, snowline=True)
        # Crevasse and couloir lines down the mountain's own face, clipped to its
        # silhouette. NOT strata: nine near-horizontal bands across the mass read
        # as venetian blinds, because a mountain's structure runs DOWN its slope.
        # Two passes -- a broad dark one and a finer light one offset from it --
        # so each couloir has a shaded side and a lit side.
        mask = Image.new('L', (fw, fh), 0)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in ridge], fill=255)
        _slope_creases(d, ridge, 3011, mask, n=26)
        # the snow PLAIN: two drift runs running off both edges. Drawn AFTER the
        # mountain so the drifts occlude its base, which puts the viewer in the
        # foreground instead of looking at a wall. The second run fills the last
        # 90px, which was an empty white strip under the caption.
        _snow_blocks(d, -160, W + 160, 600, 3201, n=6, h=104)
        _snow_blocks(d, -160, W + 160, 724, 3601, n=4, h=116)
        # Contours, but ONLY in the near drift band. Thirteen of them run the
        # full width they read as a picket fence across the mountain face; four,
        # confined to the snow the viewer is standing on, read as ground.
        _snow_contours(d, -140, W + 140, 620, 730, 3301, n=4)
        _rubble(d, -40, W + 40, 606, 3401, n=20, col=(150, 158, 168), scale=0.9)
        # the vault's own lit portal, low and left -- a warm eye in a cold frame
        _doorway(d, 214, 588, 3501, w=44, h=56, colour=(40, 46, 58),
                 lit=AMBER_LT)
        _soft_beam(d, 214, 402, 590, 96, 9)
    els.append(SC.stage(clock, 1, s1_night, j=4))

    def s1_presenter(tile, fw, fh):
        # He was 190px tall in a 720px frame -- 9 pixels of face, which is why
        # b01 read as an empty landscape with a smudge on it. At 340 he is a
        # person standing IN the snow in the foreground, cropped by nothing but
        # close enough to be the emotional read. Pose 'pointingL' and 'shrug' so
        # the arms carry a real elbow rather than a T-bar.
        SC.fullbody(ImageDraw.Draw(tile), 1092, 690, 344, pose='pointingL',
                    expression='awed', seed=11, ink=CREAM)
    els.append(E3.E('s1_presenter_a', 'character', s1_presenter,
                    at=clock.at('b01', 0), until=clock.at('b02', 0),
                    motion=SC.enter(clock, 1, dx=150, dy=0, dur=0.55)))

    def s1_presenter_b(tile, fw, fh):
        # Same man, same spot, deadpan instead of awed -- the awe was spent on
        # b01. The expression is baked into the rasterised tile, so a change is
        # two elements whose windows abut exactly (SC.expr_swap).
        SC.fullbody(ImageDraw.Draw(tile), 1092, 690, 344, pose='pointingL',
                    expression='deadpan', seed=11, ink=CREAM)
    _s1u, _s1a, _s1au = SC.expr_swap(clock, 2, 'awed', 'deadpan', until_j=4)
    els.append(E3.E('s1_presenter_b', 'character', s1_presenter_b,
                    at=_s1a, until=_s1au))
    els.append(cap(1, W // 2, 690, size=32, fill=AMBER_LT))

    def s1_stamp(tile, fw, fh):
        # The vault's name, stamped across the sky. It IS the b02 line, so
        # there is NO caption on b02: a caption under a hand-stamped name is
        # the same words twice, printed on top of each other.
        D.draw_label(tile, 'SVALBARD', center=(640, 148), color=VT.LABEL_YELLOW,
                     size=86)
        D.draw_label(tile, 'GLOBAL SEED VAULT', center=(640, 238),
                     color=VT.LABEL_YELLOW, size=44)
    els.append(SC.accrue(clock, 2, 4, s1_stamp, kind='shape'))

    def s1_opened(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # 2008, on the peak, with the ring that says "here". This is the whole
        # b03 subject now that the map is gone; the caption beside it carries
        # what a mountain still cannot draw ("on a Norwegian island").
        D.draw_number(tile, '2008', center=(392, 196), color=VT.LABEL_RED,
                      size=92)
        d.ellipse([556, 214, 596, 254], fill=RED)
        D.draw_arrow(tile, (500, 300), (572, 262), color=RED, width=8, head=38)
    els.append(SC.accrue(clock, 3, 4, s1_opened, kind='shape',
                         motion=SC.enter(clock, 3, dx=-60, dy=0, dur=ARRIVE)))
    els.append(cap(3, 640, 690, size=30, fill=(214, 224, 236)))

    # ===================================================================== #
    # STAGE S2  b04-b06  "A long tunnel runs down into the rock. / The rock   #
    #                    there is permafrost, frozen for millennia. / The      #
    #                    vault is cut straight into that ice."               #
    # The cutaway IS the world now. It used to be a b05 replacement card that  #
    # repainted 71% of the frame on top of a bare interior; here it is the    #
    # bg the stage paints, so it persists, and the three beats add only small  #
    # things to it: where the tunnel goes in, who is pointing at the frozen   #
    # band, and the warm light in the hall once it is cut.                     #
    # ===================================================================== #
    def s2_cut(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _cutaway(d, 37, label='PERMAFROST')
        # EDGE DENSITY (b04-b06 measured 2.5-2.6, the flattest in the chapter).
        # The cutaway is three big smooth fields: the slate wash above the
        # surface line, one ICE band, one dark corridor. A 24px tile inside any
        # of them sees nothing. Everything below rides ON TOP of _cutaway's own
        # geometry rather than replacing it.
        #
        # THE MASK IS LOAD-BEARING, and the first pass got this wrong. The ice
        # blocks were drawn straight across the band and buried the corridor --
        # the caption reads "a long tunnel runs down into the rock" over a frame
        # with no tunnel in it. Every block below is clipped to the band MINUS
        # the corridor and the hall, so the diagram stays legible and only the
        # dead rock gets the detail.
        band = Image.new('L', (fw, fh), 0)
        ImageDraw.Draw(band).rectangle([0, 336, W, 554], fill=255)
        ImageDraw.Draw(band).rectangle([-10, 372, 1244, 566], fill=0)   # corridor
        ImageDraw.Draw(band).rectangle([1000, 322, W, 602], fill=0)    # the hall

        # 1. ICE BLOCKS in the frozen band -- permafrost as a jointed frozen
        #    mass rather than one hatched rectangle. Twenty-two, not thirteen:
        #    at ~60px wide they are small enough that a 24px tile sees a joint.
        _ice_blocks(d, -40, W + 40, 344, 548, 337, n=22, clip=band)
        # 2. CREVASSES: long horizontal fracture lines across the ice, clipped
        #    the same way. Blocks alone give vertical joints; ice also splits
        #    along its bedding planes, and the cross-hatch of the two is what
        #    makes the band read as frozen ground rather than pale blue panels.
        for k in range(9):
            yy = 352 + k * 24
            pts = []
            for i in range(17):
                u = i / 16.0
                pts.append((W * u - 20,
                            yy + 9 * math.sin(u * 6.3 + k * 1.7)
                            + 5 * math.sin(u * 13.1 + k)))
            _clipped_stroke(d, pts, (108, 138, 162), 4, 350 + k, band)
            _clipped_stroke(d, [(px, py - 5) for px, py in pts],
                            (216, 238, 250), 2, 380 + k, band)
        # 3. ROCK STRATA through the DEEP mass below the corridor -- the single
        #    largest region left in frame. Clipped to below y=572 so no band
        #    runs across the hall.
        deep = Image.new('L', (fw, fh), 0)
        ImageDraw.Draw(deep).rectangle([0, 574, W, H], fill=255)
        _rock_strata(d, -60, W + 60, 592, 716, 331, n=8, col=(96, 104, 118),
                     lw=4, wobble_amp=7.0, clip=deep)
        # 4. PIPE RUN along the deep rock: the services a cut chamber has, and
        #    they run off both edges so the frame admits the rock continues.
        _pipe_run(d, -40, W + 40, 686, 339, n=8, r=13)
        _strut_run(d, 10, W - 10, 600, 700, 341, n=9)
        _rubble(d, -40, W + 40, 716, 351, n=22, col=(126, 132, 142))
        # 5. STRATA above the surface line. In a cross-section the region above
        #    the ground is the sky, but _cutaway paints it with the same SLATE
        #    wash as the rock, so it read as one dead grey field across the top
        #    of the frame. Two soft haze bands and a ridge line give it depth
        #    without pretending there is rock in the air.
        haze = Image.new('L', (fw, fh), 0)
        ImageDraw.Draw(haze).rectangle([0, 92, W, 176], fill=255)
        # THREE soft bands, not four hard strata. The first pass ran four
        # near-horizontal INK lines across the top of the frame and they read
        # as scan lines on a broken monitor -- strata is right for rock and
        # wrong for sky, because sky has no bedding planes. These are wide
        # low-contrast washes that only put a value step in the region.
        for k, (yy, hh, tone) in enumerate(((100, 16, 132), (124, 20, 126),
                                            (150, 14, 120))):
            pts = []
            for i in range(19):
                u = i / 18.0
                pts.append((W * u - 20,
                            yy + 7 * math.sin(u * 2.3 + k * 1.9)
                            + 4 * math.sin(u * 5.7 + k)))
            PA.fill_poly(tile, PA.wobble_edge(
                pts + [(W + 20, yy + hh), (-20, yy + hh)], seed=370 + k,
                amount=2.4, wavelength=190.0),
                (tone, tone + 6, tone + 16), seed=370 + k, value=0.05, edge=0.0)
        del haze
    els.append(SC.stage(clock, 4, s2_cut, j=7))

    def s2_entry(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The mouth, at the left face where the corridor enters the mountain.
        # The cutaway already draws the hall running in from the left; this
        # gives it a mouth in the rock, which is what "runs down into the
        # rock" actually points at.
        #
        # MOVED from cx=96 to cx=-6, and that is a collision fix, not a taste
        # call. _doorway strokes a heavy frame at cx +/- w*1.16, which at
        # cx=96 put INK at x=170 -- exactly where the drawn PERMAFROST label
        # begins, so the beat read "ERMAFROST". Parking the mouth half off the
        # left edge also matches the frame-fill rule: the corridor is cropped by
        # the edge rather than started inside the picture.
        _doorway(d, -6, 470, 38, w=76, h=78, colour=(44, 50, 60))
        PA.hand_stroke(d, [(96, 470), (300, 470)], (150, 180, 196), 5,
                       closed=False, seed=39, wavelength=90.0)
    els.append(SC.accrue(clock, 4, 5, s2_entry, kind='shape'))
    els.append(cap(4, 640, 690, size=30, fill=VT.LABEL_YELLOW))

    def s2_presenter(tile, fw, fh):
        # Pointing at the frozen band, standing ON the snow at the left edge so
        # his feet are on the surface rather than inside the diagram.
        SC.fullbody(ImageDraw.Draw(tile), 250, 706, 300, pose='pointing',
                    expression='awed', seed=43)
    els.append(SC.accrue(clock, 5, 6, s2_presenter, kind='character',
                         eid='s2_presenter',
                         motion=SC.enter(clock, 5, dx=-150, dy=0, dur=ARRIVE)))
    # NO caption at b05. PERMAFROST is drawn across the frozen band in the stage
    # world; a caption under it repeated the label and stacked text on the
    # hatching.

    def s2_chamber(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The hall goes warm: the light is the only thing that arrives, which is
        # what "cut straight into that ice" looks like. A glow pool plus three
        # stocked shelves inside the chamber -- about a tenth of the frame.
        PA.fill_poly(tile, PA.ellipse_pts(1080, 470, 186, 148, n=56),
                     AMBER_LT, seed=71, value=0.05)
        for k in range(3):
            _shelf(d, 1000 + k * 78, 1080 + k * 78, 470 + k * 18, 72 + k,
                   h=64, packets=2)
        D.draw_label(tile, 'VAULT', center=(1120, 620), color=VT.LABEL_RED,
                     size=44)
    els.append(SC.accrue(clock, 6, 7, s2_chamber, kind='shape',
                         motion=SC.enter(clock, 6, dx=0, dy=-30, dur=ARRIVE)))
    els.append(cap(6, 640, 132, size=32, fill=VT.LABEL_YELLOW))

    # ===================================================================== #
    # STAGE S3  b07  "Above the doorway, the midsummer sun barely rises."     #
    # The only beat that cannot share a frame: it is a different place (the   #
    # surface, in daylight) and a different register from the cross-section   #
    # on either side of it. So it is its own bg stage, and the sun is a       #
    # DETAIL that rises into it rather than a whole card that pops.           #
    # ===================================================================== #
    def s3_day(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 45)
        # RECEDING RIDGES FIRST, so the big mountain draws OVER them. Three
        # hazy silhouettes stepping down in value and up in height toward the
        # viewer. This is what stops the daylight sky (y 0..300) from being one
        # dead wash -- depth from layering, which is the only honest way to fill
        # a sky in this style.
        for k, (yy, tone, sd) in enumerate(((392, (150, 166, 184), 60),
                                            (352, (132, 148, 168), 61),
                                            (316, (112, 128, 150), 62))):
            rpts = []
            for i in range(13):
                u = i / 12.0
                rpts.append((W * u - 40,
                             yy - 34 * math.sin(u * 3.4 + k * 2.1)
                             - 20 * math.sin(u * 7.9 + k)))
            PA.fill_poly(tile, rpts + [(W + 40, HZ + 40), (-40, HZ + 40)],
                         tone, seed=sd, value=0.05, edge=0.0)
            # Only the NEAREST ridge gets an ink line. The first pass outlined
            # all three and the result was three hard graphic bands with the
            # far one drawn straight across the rising sun, which read as a
            # scratch on the disc rather than as distance. Aerial perspective
            # is carried by VALUE here, not by outline -- a far ridge that is
            # lighter and softer is further away, and that is the honest cue.
            if k == 0:
                PA.hand_stroke(d, rpts, (98, 112, 130), 4, closed=False,
                               seed=sd + 1, wavelength=190.0)
        # HIGH CLOUD: four soft, wide bands in the upper sky (y 96..190). This
        # is the last dead region in the frame. Midsummer over the Arctic is
        # low overcast, so banded cloud is what is actually up there -- and it
        # is low-contrast on purpose, because the title strip lives in this
        # region and a hard band behind it would trip the title intrusion gate.
        for k in range(4):
            cy0 = 104 + k * 26
            pts = []
            for i in range(15):
                u = i / 14.0
                pts.append((W * u - 30,
                            cy0 + 10 * math.sin(u * 2.1 + k * 1.6)
                            + 6 * math.sin(u * 5.3 + k * 0.7)))
            PA.fill_poly(tile, PA.wobble_edge(
                pts + [(W + 30, cy0 + 17), (-30, cy0 + 17)], seed=560 + k,
                amount=2.0, wavelength=200.0),
                (222, 232, 242), seed=560 + k, value=0.04, edge=0.0)
        # The main mountain, brought UP and given a higher crest. At crest=270
        # it sat as a small dark peak behind the portal with 300px of dead sky
        # over it. Its right shoulder has to stay below the sun (disc top is
        # y~388) or the sun would be drawn into the rock instead of clearing
        # the skyline, which is the whole sentence of this beat.
        ridge = _mountain(d, 46, crest=176, base=HZ + 6, col_x0=-260)
        mask = Image.new('L', (fw, fh), 0)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in ridge], fill=255)
        _slope_creases(d, ridge, 47, mask, n=26)
        # SNOW PLAIN. The daylight plain is the largest single region and it was
        # one flat white fill -- in DAYLIGHT, so it cannot borrow the night
        # stage's value structure. Drifts plus contour lines plus rubble.
        _snow_blocks(d, -170, W + 170, HZ - 10, 480, n=7, h=96,
                     col=(238, 242, 248))
        _snow_contours(d, -150, W + 150, HZ + 10, H + 16, 481, n=7,
                       col=(206, 218, 232), lw=4)
        _rubble(d, -40, W + 40, HZ + 6, 482, n=22, col=(158, 166, 176))
        # ONE portal: a lit opening in a concrete face on the LEFT, so "above
        # the doorway" has a referent. v1 stacked _wedge on _doorway here and
        # the wedge's underside cut through the lintel.
        px, py = 330, 452
        PA.fill_rect(tile, [px - 190, py - 210, px + 190, py + 150], CONCRETE,
                     seed=50, value=0.07)
        PA.hand_stroke(d, [(px - 190, py - 210), (px + 190, py - 210),
                           (px + 190, py + 150), (px - 190, py + 150)], INK, 8,
                       closed=True, seed=51, wavelength=150.0)
        # RIVETED PANELS on the concrete face. A 380x360 grey rectangle is the
        # second-largest smooth region in the frame; it is also the one thing
        # the narration points at ("above the doorway"), so it earns the detail
        # more than the sky does.
        _panel_run(d, px - 190, px + 190, py - 210, py + 150, 55, n=3,
                   col=(150, 154, 158))
        # formwork ties + a drip stain: the marks that make poured concrete
        # read as poured rather than as a fill
        for k in range(7):
            tx = px - 150 + k * 50
            PA.hand_stroke(d, [(tx, py - 186), (tx + 3, py - 26)], (128, 130, 134),
                           6, closed=False, seed=400 + k, wavelength=110.0)
            d.ellipse([tx - 7, py - 34, tx + 7, py - 20], fill=(120, 122, 126))
            PA.hand_stroke(d, [(tx - 7, py - 27), (tx + 7, py - 27)], INK, 3,
                           closed=False, seed=440 + k, wavelength=20.0)
        for k in range(5):
            sx = px - 150 + k * 74
            PA.hand_stroke(d, [(sx, py - 200), (sx + 6, py - 60)], (176, 178, 180),
                           10, closed=False, seed=470 + k, wavelength=90.0)
        PA.fill_rect(tile, [px - 82, py - 118, px + 82, py + 150], (44, 48, 58),
                     seed=52, value=0.06)
        PA.fill_poly(tile, PA.ellipse_pts(px, py + 40, 66, 96, n=44),
                     (198, 152, 74), seed=53, value=0.06)
        PA.hand_stroke(d, [(px - 82, py - 118), (px + 82, py - 118),
                           (px + 82, py + 150), (px - 82, py + 150)], INK, 7,
                       closed=True, seed=54, wavelength=140.0)
        # BOLLARDS either side of the mouth, and a kerb running off both edges:
        # the built apron in front of the door, so the foreground is not bare.
        for k in range(4):
            bx = px - 250 + k * 44
            PA.fill_rect(tile, [bx, py + 118, bx + 20, py + 168],
                         (96, 100, 106), seed=500 + k, value=0.06)
            PA.hand_stroke(d, [(bx, py + 118), (bx + 20, py + 118),
                               (bx + 20, py + 168), (bx, py + 168)], INK, 4,
                           closed=True, seed=520 + k, wavelength=30.0)
        PA.hand_stroke(d, [(-20, py + 176), (W + 20, py + 176)], (120, 126, 132),
                       9, closed=False, seed=540, wavelength=170.0)
        PA.hand_stroke(d, [(-20, py + 186), (W + 20, py + 186)], INK, 4,
                       closed=False, seed=541, wavelength=170.0)
    els.append(SC.stage(clock, 7, s3_day, j=8))

    def s3_gazer(tile, fw, fh):
        # CHARACTER (b07 had none). A small figure on the apron looking up at a
        # sun that barely clears the skyline is the whole sentence, and he is
        # the audience surrogate for a beat that is otherwise pure scenery.
        # Small and low on purpose: this is a wide, and he must not compete with
        # the sun rising at x=1010.
        SC.fullbody(ImageDraw.Draw(tile), 560, 622, 250, pose='pointing',
                    expression='awed', seed=56)
    els.append(SC.accrue(clock, 7, 8, s3_gazer, kind='character',
                         motion=SC.enter(clock, 7, dx=0, dy=-26, dur=ARRIVE)))

    def s3_sun(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # MOVING, and the sentence. "Barely rises" is a sun that clears the
        # skyline by a little; the halo, the disc and the word arrive from 30px
        # BELOW the horizon and rise to it over half a second. Authored at the
        # risen position, so the track's start offset is the dip.
        halo = PA.ellipse_pts(1010, HZ + 6, 158, 96, n=56)
        PA.fill_poly(tile, halo, AMBER_LT, seed=47, value=0.04)
        disc = PA.ellipse_pts(1010, HZ + 6, 64, 64, n=48)
        PA.fill_poly(tile, disc, AMBER, seed=48, value=0.05)
        PA.hand_stroke(d, disc, INK, 5, closed=True, seed=49, wavelength=90.0)
        D.draw_label(tile, 'midsummer', center=(1010, HZ - 130), color=INK,
                     size=38)
    els.append(SC.accrue(clock, 7, 8, s3_sun, kind='shape',
                         motion=SC.enter(clock, 7, dx=0, dy=30, dur=ARRIVE)))
    # NO caption at b07. The drawn word "midsummer" sits directly above the
    # drawn sun at the height it happens at -- a caption would repeat it.

    # ===================================================================== #
    # STAGE S4  b08-b10  "Down inside, the seeds sleep in the cold. / The    #
    #                    seeds are packed into small foil packets. / Around a  #
    #                    million samples, from a hundred nations."           #
    # The cold room is the WORLD for three beats. It used to be a b08 card    #
    # that repainted 86% of the frame, then a packet close-up on top of it,   #
    # then a THIRD full room at b10 that repainted 73% to say the same       #
    # thing again. Now the room holds; one packet is held up, then the count  #
    # lands on the room it belongs to.                                        #
    # ===================================================================== #
    def s4_room(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 55, wall=(78, 86, 98), floor=(58, 64, 74),
                  warm=(104, 88, 56))
        for k in range(5):
            _shelf(d, -120 + k * 8, W + 120, 210 + k * 96, 56 + k, h=190,
                   packets=13)
    els.append(SC.stage(clock, 8, s4_room, j=11))

    def s4_packet(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # One packet held up to the light, at the size that reads as a held
        # object against the shelves rather than as a second room. The glow is
        # an ellipse, not a filled disc, so it adds light without replacing the
        # shelves behind it.
        PA.fill_poly(tile, PA.ellipse_pts(640, 400, 214, 176, n=64), AMBER_LT,
                     seed=62, value=0.05)
        _packet(d, 640, 392, 232, 306, 63, band=AMBER, stamp='wheat')
        # a hand coming in from the right edge, gripping it -- cropped by the
        # frame edge so it reads as an arm reaching in, not a floating paw.
        PA.hand_stroke(d, [(1330, 560), (790, 486)], (232, 202, 172), 58,
                       closed=False, seed=64, wavelength=170.0)
        PA.hand_stroke(d, [(1330, 560), (790, 486)], INK, 5, closed=False,
                       seed=65, wavelength=170.0)
        for k in range(3):
            PA.hand_stroke(d, [(840 + k * 38, 468 + k * 9), (886 + k * 38, 552)],
                           (232, 202, 172), 27, closed=False,
                           seed=66 + k, wavelength=50.0)
        # LABEL_YELLOW, not INK. At the bottom of the amber pool (bg_lum ~90)
        # with no keyline the counters in o, a, e and p fill in and the lower
        # half of the glyphs runs into the brown shadow edge. The light fill
        # carries the contrast and takes the keyline.
        D.draw_label(tile, 'one sample', center=(640, 640),
                     color=VT.LABEL_YELLOW, size=34)
    els.append(SC.accrue(clock, 9, 11, s4_packet, kind='shape',
                         motion=SC.enter(clock, 9, dx=0, dy=-64, dur=ARRIVE)))
    # NO caption at b09. "one sample" is DRAWN on the packet's own shadow.

    def s4_count(tile, fw, fh):
        D.draw_number(tile, '1,000,000', center=(640, 596),
                      color=VT.LABEL_YELLOW, size=104)
    els.append(SC.accrue(clock, 10, 11, s4_count, kind='shape',
                         motion=SC.enter(clock, 10, dx=0, dy=-36, dur=ARRIVE)))
    els.append(cap(10, 640, 700, size=30, fill=VT.LABEL_YELLOW))
    # The drawn count sits ON the room it counts. The caption is the sentence
    # around the numeral ("around a million samples, from a hundred nations"),
    # which the numeral cannot say.

    # ===================================================================== #
    # STAGE S5  b11-b12  "Wheat, rice, barley, beans, and millet. / Every    #
    #                    sample in there is a spare copy."                   #
    # One shelf deck held across both beats. All five packets arrive TOGETHER  #
    # at b11 because the narrator names all five in ONE beat -- spreading them  #
    # would have packets landing on empty beats with the words already gone.   #
    # b12 used to lay a full COPY/ORIGINAL pair of panels over them (a 48%    #
    # repaint, and it buried the packets it was talking about). Now it is a   #
    # packet sliding OFF the deck with an arrow, which is the thought: the     #
    # sample leaves the shelf and stays here.                                  #
    # ===================================================================== #
    def s5_deck(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 77, wall=(80, 88, 100), warm=(104, 90, 58))
        _room_shell(tile, d, 79, wall_col=(80, 88, 100), floor_col=(62, 68, 80))
        _shelf(d, -60, W + 60, 600, 78, h=210, packets=5)
    els.append(SC.stage(clock, 11, s5_deck, j=13))

    def s5_crops(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # All five arrive together, one row, five distinct crop marks so the row
        # reads as five different seeds at a glance.
        #
        # NO drawn name under each packet. v1 drew WHEAT/RICE/BARLEY/BEAN/MILLET
        # at y=350, which is exactly the packets' top edge: every label straddled
        # its own packet's border and was cut by it. The five names are ONE
        # caption line at the beat the narrator says them.
        kinds = ['wheat', 'rice', 'barley', 'bean', 'millet']
        for i, k in enumerate(kinds):
            cx = 128 + i * 256
            _packet(d, cx, 470, 168, 250, 80 + i * 3, band=AMBER, stamp=k)
    els.append(SC.accrue(clock, 11, 12, s5_crops, kind='shape',
                         motion=SC.enter(clock, 11, dx=0, dy=-56, dur=ARRIVE)))
    els.append(cap(11, 640, 700, size=30))

    def s5_spare(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # THE PIVOT, made physical. The deck and its five packets stay; a sixth
        # packet slides in from the right and stops with an arrow and a SPARE
        # COPY tag, so "every sample in there is a spare copy" is a thing that
        # is happening rather than a new pair of boxes laid over the row.
        _packet(d, 1096, 392, 150, 214, 84, band=AMBER, stamp='wheat')
        D.draw_arrow(tile, (960, 300), (1060, 356), color=RED, width=8,
                     head=40)
        D.draw_label(tile, 'SPARE COPY', center=(1096, 258),
                     color=VT.LABEL_RED, size=34)
    els.append(SC.accrue(clock, 12, 13, s5_spare, kind='shape',
                         motion=SC.enter(clock, 12, dx=180, dy=0, dur=0.55)))
    els.append(cap(12, 500, 700, size=30))
    # KEPT, and it is the chapter's pivot: the sentence the whole video is built
    # to land. SPARE COPY is drawn, but a drawn tag does not say that the vault
    # holding copies is the POINT -- the words carry it.

    # ===================================================================== #
    # STAGE S6  b13-b14  "The original seed always stays on the farm. / Each #
    #                    nation's crop insurance, stored in a mountain."      #
    # The globe is the WORLD now, cropped by the bottom and right edges, so it #
    # is a world filling the frame and the keeper stands beside it rather than #
    # replacing it. Two full-frame replacements became: a man arriving on the #
    # left, then the packets landing on the globe one ring at a time.          #
    # ===================================================================== #
    def s6_world(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        PA.fill_rect(tile, [0, 0, W, H], (206, 214, 224), seed=125, value=0.05)
        PA.paper_overlay(tile, seed=126)
        # the globe is deliberately off-centre right and CROPPED by the bottom
        # and right edges, so it is a world filling the frame
        _globe(d, 790, 452, 336, 133)
    els.append(SC.stage(clock, 13, s6_world, j=15))

    def s6_keeper(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Standing on the ground plane beside the globe, not cropped in: this
        # beat's point is that the original is OUT HERE, away from the vault,
        # so he is in the room with the globe rather than filling it. dx only.
        SC.fullbody(d, 236, 690, 372, pose='standing', expression='skeptic',
                    seed=127)
        D.draw_bubble(tile, 'the original\nstays home', (300, 168),
                      tail_to=(250, 400), font_size=30, max_w=400)
    els.append(SC.accrue(clock, 13, 14, s6_keeper, kind='character',
                         eid='s6_keeper',
                         motion=SC.enter(clock, 13, dx=-150, dy=0, dur=ARRIVE)))
    # NO caption at b13. The speech bubble IS his line, drawn in his own mouth;
    # a caption under it duplicated the bubble.

    def s6_packets(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The packets ARRIVE on the globe, two rings, rather than all at once: a
        # globe wearing its packets is a different picture from a bare globe,
        # and the arrival is what says "every nation".
        for k, (gx, gy) in enumerate(((0.42, -0.42), (-0.30, -0.20),
                                      (-0.10, 0.34), (0.30, 0.20))):
            _packet(d, 790 + gx * 336, 452 + gy * 336, 76, 104, 134 + k,
                    band=AMBER, stamp='wheat')
        D.draw_label(tile, 'CROP INSURANCE', center=(330, 214), color=INK,
                     size=40)
    els.append(SC.accrue(clock, 14, 15, s6_packets, kind='shape',
                         motion=SC.enter(clock, 14, dx=0, dy=-40, dur=ARRIVE)))
    # NO caption at b14. CROP INSURANCE is drawn, the packets are on the globe,
    # and the b14 line is exactly those two facts.

    # ===================================================================== #
    # STAGE S7  b15  "Inside, the air holds at minus eighteen degrees."       #
    # + STAGE S8  b16-b17  "colder than any farm freezer. / In that cold, the #
    #                      seeds sleep for centuries."                       #
    # TWO stages, not one, and the reason is a measurement rather than a        #
    # preference. The b16 comparison (a chest freezer beside a vault door three #
    # times its size) covers ~48% of the frame and the b17 frost another ~49%;  #
    # neither fits the 30% budget a layer inside a stage gets. So the           #
    # comparison is its own bg world at b16 and the frost is a detail on IT at  #
    # b17 -- where the shelf and packets are sized to ~22%. The thermometer at  #
    # b15 is a 20px tube, so it costs almost nothing and stays a detail.        #
    # ===================================================================== #
    def s7_cold(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 141, wall=(74, 82, 94), warm=(96, 84, 56))
        # The -18 thermometer (b15) is the only thing on this stage, so the room
        # behind it is nearly the whole frame. Panelled, beamed and floored.
        #
        # tray=False, and that is a fix rather than a preference. The cable tray
        # is a full-width 20px bar with an ink outline on both edges, and at
        # EVERY height available on this stage it lands somewhere load-bearing:
        # at the default it crossed the -18's "DEGREES C"; moved up to clear
        # that, it ran straight through the caption at y=560 and struck
        # through the word "degrees". This wall carries its density from the
        # panels instead.
        _room_shell(tile, d, 144, wall_col=(74, 82, 94), floor_col=(58, 64, 74),
                    tray=False, panel_n=9, row_h=104.0, crates=6,
                    panels_skip=[(700, 1060, 190, 400)])   # clear of the -18
    els.append(SC.stage(clock, 15, s7_cold, j=16))

    def s7_thermo(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The thermometer is a narrow tube, so it stays clear of the frame's
        # middle and the reading can sit beside it rather than under it.
        S.thermometer(d, 300, 660, 540, 0.22, seed=142, hot=False)
        # LABEL_YELLOW, not INK: the zero tick sits on the warm interior pool at
        # bg_lum ~88 with no keyline, so the counter inside the glyph filled in
        # and it read as a solid dark ring -- the darkest text on the card, on
        # the one numeral the viewer is meant to read as the 0 mark.
        D.draw_label(tile, '0', center=(396, 178), color=VT.LABEL_YELLOW,
                     size=34)
        D.draw_arrow(tile, (760, 452), (596, 528), color=VT.LABEL_RED, width=10,
                     head=46)
        # The -18 numeral is in the SAME layer as the arrow it belongs to. Split
        # across two elements it became two large reds fighting in one half of
        # the frame -- rule 1: anything sharing a part of the frame replaces
        # rather than stacks.
        D.draw_number(tile, '-18', center=(862, 300), color=VT.LABEL_RED,
                      size=180)
        D.draw_label(tile, 'DEGREES C', center=(862, 430), color=VT.LABEL_RED,
                     size=52)
    els.append(SC.accrue(clock, 15, 16, s7_thermo))
    els.append(cap(15, 862, 560, size=30, fill=VT.LABEL_RED))
    # The caption sits under the -18 numeral, in the gap between the numeral
    # and the floor, clear of the thermometer on the left.

    def s7_chilly(tile, fw, fh):
        # CHARACTER (b15 had none). A small figure on the floor between the
        # thermometer and the numeral, clear of both the tube (x~300) and the
        # caption (which spans x 552..1172 at y=560).
        #
        # shrug, NOT armscrossed. armscrossed is authored la=(38, 78), and at
        # this height its forearms swing so far up that the silhouette reads as
        # a horizontal T-arm scarecrow at ship size -- the recurring stickman
        # defect, reached here by picking a pose for its name rather than for
        # how it draws. shrug (46, 62) puts the same cold-shoulder read in a
        # silhouette that survives being small.
        SC.fullbody(ImageDraw.Draw(tile), 486, 648, 208, pose='shrug',
                    expression='worried', seed=145)
    els.append(SC.accrue(clock, 15, 16, s7_chilly, kind='character',
                         motion=SC.enter(clock, 15, dx=110, dy=0, dur=ARRIVE)))

    def s8_freezers(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 143, wall=(74, 82, 94), warm=(96, 84, 56))
        _room_shell(tile, d, 145, wall_col=(74, 82, 94), floor_col=(58, 64, 74),
                    panel_n=9, row_h=104.0, crates=6,
                    panels_skip=[(90, 560, 180, 660),      # the chest freezer
                                 (680, 1000, 100, 240)])   # the VAULT label
        # left: an ordinary domestic chest freezer, small and domestic
        chest = [(120, 300), (520, 300), (520, 640), (120, 640)]
        PA.fill_poly(tile, chest, (222, 224, 226), seed=146, value=0.07)
        PA.hand_stroke(d, chest, INK, 7, closed=True, seed=147, wavelength=150.0)
        PA.hand_stroke(d, [(120, 380), (520, 380)], INK, 5, closed=False,
                       seed=148, wavelength=110.0)
        # LABEL_YELLOW, not INK: black with no keyline across the brown wall
        # flattened the counters in A, R and E into the ground.
        D.draw_label(tile, 'FARM FREEZER', center=(320, 250),
                     color=VT.LABEL_YELLOW, size=32)
        D.draw_label(tile, '-18', center=(320, 500), color=INK, size=52)
        # right: the vault's inner door, three times the size, running off the
        # right edge -- so the scale comparison is the composition, not a caption
        door = [(700, 200), (1360, 200), (1360, 690), (700, 690)]
        PA.fill_poly(tile, door, STEEL, seed=149, value=0.07)
        PA.hand_stroke(d, door, INK, 8, closed=True, seed=150, wavelength=170.0)
        PA.hand_stroke(d, [(740, 236), (1320, 236)], (110, 116, 126), 6,
                       closed=False, seed=151, wavelength=150.0)
        for k in range(4):
            y = 280 + k * 96
            d.ellipse([1240, y, 1290, y + 50], fill=(70, 76, 86))
        PA.hand_stroke(d, [(1180, 400), (1180, 620)], INK, 12, closed=False,
                       seed=152, wavelength=90.0)
        D.draw_label(tile, 'VAULT', center=(980, 150), color=VT.LABEL_RED,
                     size=40)
        D.draw_number(tile, '-18', center=(1000, 470), color=VT.LABEL_RED,
                      size=110)
    els.append(SC.stage(clock, 16, s8_freezers, j=18))
    # NO caption at b16. FARM FREEZER and VAULT are labelled, and both print
    # -18; the scale comparison IS the sentence "colder than any farm freezer".

    def s8_frost(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # v1 drew a 640x480 packet so large and so white that it read as an
        # empty blank sign. Rebuilt as a LOW, WIDE shelf of frost-crusted packets
        # along the bottom of the room. Sized and placed deliberately: the first
        # pass at ~22% put three large packets at mid-frame, where they landed
        # on top of the farm-freezer and vault-door labels from b16 and turned
        # the frame into overlapping diagrams. The frost belongs UNDER the
        # comparison -- it is what is IN the cold -- so it lives in the bottom
        # band the freezers leave empty, adds to the room rather than fighting
        # it, and stays inside the 30% a detail gets.
        _shelf(d, 40, 1240, 664, 156, h=104, packets=7)
        # hoar frost: a dense crust along the top seal of every packet the shelf
        # draws, plus speckle ON the shelf lip. Never on the wall or the freezers.
        for k in range(60):
            x = 60 + (k * 41) % 1160
            y = 556 + (k * 17) % 22
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(238, 248, 253))
        for k in range(40):
            x = 50 + (k * 53) % 1180
            y = 664 + (k * 11) % 10
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(226, 240, 250))
        D.draw_label(tile, 'CENTURIES', center=(640, 528),
                     color=VT.LABEL_YELLOW, size=44)
    els.append(SC.accrue(clock, 17, 18, s8_frost, kind='shape',
                         motion=SC.enter(clock, 17, dx=0, dy=-30, dur=ARRIVE)))
    # NO caption at b17. CENTURIES is drawn above the frost-covered packets and
    # the frost itself is the sleeping.

    # ===================================================================== #
    # STAGE S8  b18-b19  "The original plan was simple: shut the door. /     #
    #                    Then leave the whole vault to the ice."             #
    # The corridor with its nest of receding doors is HELD, because the two    #
    # beats are about DOORS and the viewer needs the same corridor when the    #
    # door closes. The presenter arrives and points; then the ice seal GROWS   #
    # across the near door's hasp as a detail -- not a new frame of a different #
    # steel door. It used to repaint 75% at b19.                              #
    # ===================================================================== #
    def s8_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 161, wall=(72, 80, 92), floor=(54, 60, 70),
                  warm=(96, 86, 58))
        # A corridor of receding doors: the walls are the largest region here
        # and they were flat. Panelled walls + floor slabs + crates give it the
        # built depth the vanishing-point doors already imply. tray is off: the
        # receding door frames are centred on x=640 and a full-width tray
        # crosses all four of them.
        _room_shell(tile, d, 164, wall_col=(72, 80, 92), floor_col=(54, 60, 70),
                    tray=False, panel_n=8, row_h=100.0, crates=5,
                    panels_skip=[(430, 860, 120, 620)])
        # four doors receding down the corridor. The outermost door's heavy
        # frame used to top out at y=19, driving a full-width INK bar through
        # the persistent title; that geometry is kept trimmed here.
        for k, (hw, hh, y) in enumerate(((360, 190, 316), (290, 172, 366),
                                          (222, 134, 420), (160, 98, 470))):
            _doorway(d, 640, y, 162 + k * 4, w=hw * 0.55, h=hh,
                     colour=(58, 64, 76) if k else (72, 78, 90))
        # the near door the seal will weld: a lit slab at the corridor mouth
        dx0, dy0, dx1, dy1 = 300, 148, 980, 648
        PA.fill_rect(tile, [dx0, dy0, dx1, dy1], (104, 113, 126), seed=178,
                     value=0.06)
        PA.fill_rect(tile, [dx0 - 34, dy0 - 34, dx1 + 34, dy1 + 34],
                     (72, 79, 90), seed=186, value=0.06)   # the jamb
        PA.hand_stroke(d, [(dx0 - 34, dy0 - 34), (dx1 + 34, dy0 - 34),
                           (dx1 + 34, dy1 + 34), (dx0 - 34, dy1 + 34)],
                       INK, 9, closed=True, seed=179, wavelength=160.0)
        PA.hand_stroke(d, [(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)],
                       INK, 8, closed=True, seed=180, wavelength=150.0)
        # the hasp bar -- the thing the ice will weld shut
        PA.hand_stroke(d, [(dx0 + 40, 528), (dx1 - 40, 528)], (46, 51, 60), 22,
                       closed=False, seed=201, wavelength=150.0)
        PA.hand_stroke(d, [(dx0 + 40, 528), (dx1 - 40, 528)], INK, 7,
                       closed=False, seed=202, wavelength=150.0)
    els.append(SC.stage(clock, 18, s8_corridor, j=20))

    def s8_presenter(tile, fw, fh):
        SC.fullbody(ImageDraw.Draw(tile), 190, 700, 340, pose='pointing',
                    expression='deadpan', seed=170)
    els.append(SC.accrue(clock, 18, 19, s8_presenter, kind='character',
                         eid='s8_presenter',
                         motion=SC.enter(clock, 18, dx=-130, dy=0, dur=0.55)))
    els.append(cap(18, 700, 690, size=30, fill=(214, 224, 236)))
    # The caption sits low and to the RIGHT of where the presenter stands, so
    # the words land on empty floor rather than on his boots or the door frames.

    def s8_seal(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # "leave the whole vault to the ice" is carried by a FROZEN SEAL, not
        # by drawn snow. Five passes on frost texture all rendered as something
        # that was not ice. So the ice here is ONE legible fact: a block of
        # frozen water has grown across the door's hasp and welded it shut. A
        # solid pale-blue block with a hard edge and a few crystal spikes reads
        # immediately as ice and cannot be mistaken for snow or a tear.
        sx, sy, shw, shh = 640, 528, 132, 80
        seal = [(sx - shw, sy + 40), (sx - shw + 26, sy - shh + 20),
                (sx - 60, sy - shh - 10), (sx + 46, sy - shh + 6),
                (sx + shw - 30, sy - shh + 26), (sx + shw, sy - 30),
                (sx + shw - 16, sy + shh), (sx - shw + 18, sy + shh - 12)]
        PA.fill_poly(PA.img_of(d), PA.wobble_edge(seal, seed=203, amount=3.4,
                                                  wavelength=70.0),
                     (176, 216, 236), seed=203, value=0.06, edge=0.0)
        PA.hand_stroke(d, PA.wobble_edge(seal, seed=203, amount=3.4,
                                         wavelength=70.0),
                       INK, 8, closed=True, seed=204, wavelength=80.0)
        # a lighter core, so the block has depth instead of reading as a decal
        core = [(sx - 70, sy + 16), (sx - 56, sy - 44), (sx + 30, sy - 56),
                (sx + 66, sy - 20), (sx + 54, sy + 30), (sx - 40, sy + 34)]
        PA.fill_poly(PA.img_of(d), PA.wobble_edge(core, seed=205, amount=2.6,
                                                  wavelength=52.0),
                     (214, 240, 250), seed=205, value=0.05, edge=0.0)
        _frost_crystals(d, sx - 96, sx + 96, sy - shh, 6, 820)
        _frost_crystals(d, sx - 110, sx + 110, sy + shh - 6, 4, 860)
        # drifts at the foot of the door: enough to say the cold owns this place,
        # thin enough not to become the subject.
        _frost_bank(d, 266, 1014, 682, 622, 660, 400)
        _frost_crystals(d, 290, 990, 624, 10, 700)
    els.append(SC.accrue(clock, 19, 20, s8_seal, kind='shape',
                         motion=SC.enter(clock, 19, dx=0, dy=-44, dur=0.55)))
    els.append(cap(19, 640, 690, size=30))
    # The caption is KEPT on this beat: the ice is visible now, but "leave the
    # whole vault to the ice" is a decision, and a frozen door alone does not
    # say anyone MADE that choice. b18's caption is one beat back, so these two
    # do not stack.

    # ===================================================================== #
    # STAGE S9  b20-b21  "Then, in 2016, the mountain began to leak. /       #
    #                    Meltwater came in through the entrance tunnel."      #
    # The cutaway with 2016 on it is the WORLD, and the meltwater channel is   #
    # the DETAIL that arrives at b21 pointing at the open door. Previously each #
    # of these was its own full-frame card repainting ~70-90%.                 #
    # ===================================================================== #
    def s9_leak(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 185, warm_chamber=True)
    els.append(SC.stage(clock, 20, s9_leak, j=22))

    def s9_2016(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # 2016, not 2008. This label was a copy-paste from the b03 card above
        # it, so the beat that opens the flood chapter drew the vault's OPENING
        # year while the narrator said 2016.
        D.draw_label(tile, '2016', center=(210, 152), color=VT.LABEL_RED,
                     size=64)
        D.draw_arrow(tile, (300, 190), (600, 330), color=INK, width=10,
                     head=46)
    els.append(SC.accrue(clock, 20, 21, s9_2016, kind='shape'))
    els.append(cap(20, 640, 700, size=30))
    # The caption is KEPT here and not at b21: "the mountain began to leak" is
    # the pivot of the whole chapter, the one beat where the argument turns, and
    # the drawn 2016 arrow only shows the mountain. The words carry the turn.

    def s9_channel(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # a brown meltwater run cutting straight at the open door
        chan = [(340, 700), (620, 700), (592, 520), (580, 470), (544, 470),
                (504, 540), (452, 560)]
        PA.fill_poly(tile, chan, WATER, seed=195, value=0.07)
        PA.hand_stroke(d, chan[:1] + chan[2:], INK, 5, closed=False, seed=196,
                       wavelength=110.0)
        D.draw_arrow(tile, (280, 640), (430, 552), color=RED, width=10,
                     head=46)
    els.append(SC.accrue(clock, 21, 22, s9_channel, kind='shape'))
    # NO caption at b21. The water channel drawn straight at the open door with
    # a red arrow aimed into it IS "meltwater came in through the entrance
    # tunnel". b20 already carries the flood caption.

    # ===================================================================== #
    # STAGE S10  b22-b25  "Water at the door, in a frozen land. / The        #
    #                      entrance flooded with eight hundred tonnes. / The   #
    #                      staff were cut off for a year. / The seed samples   #
    #                      themselves were never touched."                    #
    # The flood corridor is the WORLD and holds for four beats. The water is   #
    # the one thing that RISES here -- authored at the risen position and      #
    # drifted 90px down over the beat, so the fill reads as water climbing the #
    # corridor, which is the sentence. Then the number lands, then the boards   #
    # go up across the door, then the keeper walks in to say the seeds were    #
    # fine. Four beats, one repaint.                                            #
    # ===================================================================== #
    def s10_corridor(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _interior(tile, 201, wall=(62, 70, 82), floor=(48, 54, 64))
        _room_shell(tile, d, 205, wall_col=(62, 70, 82), floor_col=(48, 54, 64),
                    panel_n=8, row_h=100.0, crates=5,
                    panels_skip=[(340, 940, 130, 640)])   # clear of the doorway
        # The doorway's frame sits so its top is clear of the title band.
        _doorway(d, 640, 385, 202, w=300, h=250, colour=(70, 76, 88))
    els.append(SC.stage(clock, 22, s10_corridor, j=26))

    def s10_flood(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the flood: a standing wall of meltwater, door half behind it. Drawn
        # at full height here and DRIFTED down so the waterline visibly rises.
        wallw = [(300, 720), (300, 430), (1000, 400), (1000, 720)]
        PA.fill_poly(tile, wallw, WATER, seed=203, value=0.07)
        PA.hand_stroke(d, wallw[:3], (156, 186, 200), 7, closed=False,
                       seed=204, wavelength=170.0)
        for k in range(9):
            x = 330 + k * 78
            PA.hand_stroke(d, [(x, 430 + k % 3 * 12), (x + 40, 470 + k % 3 * 12)],
                           (156, 186, 200), 5, closed=False, seed=210 + k,
                           wavelength=60.0)
    # MOVING, and the chapter's one long move: the waterline RISES as the
    # narrator says it filled. This is the only motion here that carries
    # meaning on its own, so it is the only one with a multi-second track.
    # Live to b24, NOT to b23. The water used to END exactly where the '800
    # tonnes' numeral began, so the gate measured the handover -- the wall of
    # water leaving AND the numeral arriving -- as one 30% repaint and flagged
    # it. Held under its successor, the numeral lands ON the flood instead of
    # replacing it, which is also the better picture: the weight is standing in
    # the water. The drift still finishes at b23 (the rise is b22->b23), so the
    # flood holds its risen level through b23 rather than sliding on.
    els.append(SC.accrue(clock, 22, 24, s10_flood, kind='shape',
                         motion=SC.drift(clock, 22, 23, dx=0, dy=-90)))
    # NO caption at b22. A cold grey corridor half-drowned by blue water with
    # the door behind it IS "water at the door, in a frozen land".

    def s10_tonnes(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        D.draw_number(tile, '800', center=(430, 262), color=VT.LABEL_YELLOW,
                      size=170)
        D.draw_label(tile, 'TONNES', center=(960, 262), color=VT.LABEL_YELLOW,
                     size=96)
    els.append(SC.accrue(clock, 23, 24, s10_tonnes, kind='shape',
                         motion=SC.enter(clock, 23, dx=0, dy=-30, dur=ARRIVE)))
    els.append(cap(23, 640, 690, size=30, fill=VT.LABEL_YELLOW))
    # KEPT. "eight hundred tonnes" is the one number the viewer cannot infer
    # from the frame. The drawn 800 is the number SHOWN; the caption is the
    # sentence AROUND it, which the numeral alone does not say.

    def s10_barricade(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # MOVING. The barricade going up across the door is the b24 statement
        # made physically: the staff are OUT, the door is boarded.
        _flood_gate(d, 640, 400, 229)
        D.draw_label(tile, '2016', center=(300, 250), color=VT.LABEL_RED,
                     size=60)
    els.append(SC.accrue(clock, 24, 25, s10_barricade, kind='shape',
                         motion=SC.enter(clock, 24, dx=0, dy=70, dur=ARRIVE)))
    # NO caption at b24, and it is a real loss of the word "a year". The boards
    # going up across the door plus the drawn 2016 is the seal; but b23 already
    # captioned this stage and the no-two-consecutive rule is a hard constraint.

    def s10_fine(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The keeper walks into the flooded corridor to say the one thing that
        # matters. Full body rather than a close-up: this is a person standing
        # in the water, and a cropped face would have replaced the corridor.
        SC.fullbody(d, 236, 690, 340, pose='standing', expression='deadpan',
                    seed=233)
        D.draw_bubble(tile, 'the seeds\nwere fine', (250, 172),
                      tail_to=(250, 380), font_size=30, max_w=380)
    els.append(SC.accrue(clock, 25, 26, s10_fine, kind='character',
                         eid='s10_fine',
                         motion=SC.enter(clock, 25, dx=-140, dy=0, dur=ARRIVE)))
    # NO caption at b25. The bubble IS the line, in his mouth.

    # ===================================================================== #
    # STAGE S11  b26-b27  "They lay above the waterline, in the cold. / The   #
    #                      same permafrost that keeps it thaws too."           #
    # ONE cross-section carries both beats: the water sits in the corridor at  #
    # b26, and at b27 the frozen layer above it is eaten back and the melt     #
    # arrows arrive. They were two separate full-frame cutaways (98% and 95%).  #
    # ===================================================================== #
    def s11_cut(tile, fw, fh):
        _cutaway(ImageDraw.Draw(tile), 237, water_level=0.34)
    els.append(SC.stage(clock, 26, s11_cut, j=28))

    def s11_above(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        D.draw_arrow(tile, (300, 300), (300, 430), color=VT.LABEL_RED, width=9,
                     head=42)
        D.draw_label(tile, 'ABOVE THE WATER', center=(300, 210),
                     color=VT.LABEL_RED, size=34)
    els.append(SC.accrue(clock, 26, 27, s11_above, kind='shape'))
    # NO caption at b26. ABOVE THE WATER is DRAWN with an arrow to the chamber
    # floor; the words only restated it.

    def s11_thaw(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The frozen layer is eaten back from below and the melt arrows arrive.
        # Redrawn over the stage world's band rather than as a second whole
        # cutaway, so the corridor and its water are the SAME ones.
        band = [(0, 330), (W, 330), (W, 470), (0, 470)]
        low = []
        n = 40
        for i in range(n + 1):
            x = W * i / float(n)
            yy = 470 - 46 * math.sin(i * 1.1) - 18 * math.sin(i * 0.37 + 1.2)
            low.append((x, yy))
        PA.fill_poly(tile, band, ICE, seed=244, value=0.06)
        PA.fill_poly(tile, low + [(W, 470), (0, 470)], SLATE, seed=245,
                     value=0.06)
        PA.hand_stroke(d, low[:n + 1], INK, 6, closed=False, seed=246,
                       wavelength=120.0)
        for k in range(6):
            x = 120 + k * 200
            D.draw_arrow(tile, (x + 40, 290), (x - 20, 426), color=RED,
                         width=8, head=36)
        D.draw_label(tile, 'AND MELTING', center=(880, 236), color=VT.LABEL_RED,
                     size=40)
    els.append(SC.accrue(clock, 27, 28, s11_thaw, kind='shape',
                         motion=SC.enter(clock, 27, dx=0, dy=-30, dur=ARRIVE)))
    els.append(cap(27, 640, 690, size=32, fill=RED))
    # KEPT, and it is the second pivot. "The same permafrost that keeps it
    # thaws too" cannot be drawn as a label: the art can show a ragged ice layer
    # and red melt arrows, but not that the SAME layer doing the preserving is
    # the layer failing. That identity is the argument, and only the sentence
    # carries it.

    # ===================================================================== #
    # STAGE S12  b28-b30  "The vault is watched now, year round. / A new      #
    #                      access tunnel is being built. / New lights on the   #
    #                      snow, night and day."                             #
    # The slope is the WORLD and holds for three beats. The site gets busier   #
    # inside it: a camera is bolted up, a new raw mouth is cut beside the old   #
    # door, an excavator arrives, and the work lights come on. Three beats that #
    # used to be three separate full-frame exteriors (90%, 40%, 90%) are now    #
    # one exterior with three arrivals.                                       #
    # ===================================================================== #
    def s12_slope(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _day_arctic(tile, 249, snow=(222, 230, 238))
        _mountain(d, 250, crest=280, base=HZ + 30)
        _wedge(d, 300, 400, 251, w=210, h=150)
        _doorway(d, 300, 500, 252, w=132, h=172, colour=(46, 52, 62))
    els.append(SC.stage(clock, 28, s12_slope, j=31))

    def s12_camera(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # MOVING. The camera's lamp coming on is "watched now" -- the eye is
        # drawn to the small red lamp, which is the point of the beat.
        _camera(d, 700, 300, 110, 253)
        D.draw_arrow(tile, (900, 262), (770, 320), color=INK, width=9, head=42)
        D.draw_label(tile, 'watched', center=(1040, 222), color=INK, size=36)
    els.append(SC.accrue(clock, 28, 29, s12_camera, kind='shape',
                         motion=SC.enter(clock, 28, dx=0, dy=-40, dur=ARRIVE)))
    # NO caption at b28. "watched" is DRAWN beside the arrow pointing at the
    # camera; the drawn word is the caption.

    def s12_newmouth(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # the new mouth: raw concrete, cut into the slope to the right of the
        # old door, so the two of them read as old-and-new on one hillside.
        raw = [(880, 400), (1180, 400), (1140, 620), (900, 620)]
        PA.fill_poly(tile, raw, CONCRETE, seed=261, value=0.07)
        PA.hand_stroke(d, raw, INK, 7, closed=True, seed=262, wavelength=150.0)
        _doorway(d, 1030, 520, 263, w=96, h=124, colour=(52, 58, 70))
        D.draw_label(tile, 'NEW TUNNEL', center=(1030, 350), color=VT.LABEL_RED,
                     size=32)
        # The excavator, arriving. Drawn on its own small tile so the machine
        # moves without dragging the opaque sky across the shot.
        _excavator(d, 640, 604, 82, 264)
    els.append(SC.accrue(clock, 29, 30, s12_newmouth, kind='shape',
                         motion=SC.enter(clock, 29, dx=-90, dy=0, dur=ARRIVE)))
    els.append(cap(29, 640, 700, size=30))
    # KEPT. "A new access tunnel is being built" is future work in progress; the
    # excavator and raw concrete show it, but the caption carries the sentence
    # and this beat is a beat away from b28's dropped one, not adjacent to it.

    def s12_lights(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Two beams of light on the snow. _soft_beam, not SV._light_wedge: the
        # latter fills one solid amber triangle and two of them read as gold
        # traffic cones rather than lamplight.
        _soft_beam(d, 880, 150, HZ - 6, 152, 271)
        _soft_beam(d, 1110, 150, HZ - 6, 138, 273)
        SC.fullbody(d, 640, HZ + 20, 224, pose='standing', expression='skeptic',
                    seed=275)
    els.append(SC.accrue(clock, 30, 31, s12_lights, kind='character',
                         motion=SC.enter(clock, 30, dx=120, dy=0, dur=0.55)))
    # NO caption at b30. Two lamp wedges on the snow with him standing between
    # them IS "new lights on the snow, night and day".

    # ===================================================================== #
    # STAGE S13  b31-b35  "It is still a bunker against catastrophe. /        #
    #                      Catastrophe is already moving into the mountain. / #
    #                      The coldest air on earth is warming here. / The     #
    #                      seeds are still fine, for now. / Somewhere under    #
    #                      the snow, it is still seeping."                    #
    # THE BIGGEST WIN IN THE REBUILD, and the clearest demonstration of the   #
    # model. This was five unrelated full-frame cards -- a paper-wall close-up, #
    # a re-drawn mountain, a bare warming slope, another close-up, a night      #
    # slope -- i.e. a new image every sentence, which is the complaint. It is  #
    # now ONE night mountain held for thirteen seconds: the keeper arrives, a  #
    # heat front advances up the snow, the snow bares and the -2.6 lands, he   #
    # comes back holding a packet, and the meltwater channel drifts.          #
    # ===================================================================== #
    def s13_night(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        _arctic(tile, 281)
        SC.title_backdrop(tile, 1281, col=TITLE_COURSE)
        _mountain(d, 283, crest=300, base=HZ + 6)
    els.append(SC.stage(clock, 31, s13_night, j=36))

    def s13_bunker(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # He stands ON the snow in front of the mountain he is describing,
        # rather than replacing the mountain with a cropped face. The bubble is
        # his line; the caption below is the only text on this beat that is not
        # in the art.
        SC.fullbody(d, 300, HZ + 8, 300, pose='standing', expression='deadpan',
                    seed=279, ink=CREAM)
        D.draw_bubble(tile, 'a bunker', (760, 214), tail_to=(470, 430),
                      font_size=34, max_w=300)
    els.append(SC.accrue(clock, 31, 32, s13_bunker, kind='character',
                         eid='s13_bunker',
                         motion=SC.enter(clock, 31, dx=-140, dy=0, dur=0.55)))
    els.append(cap(31, 640, 690, size=32, fill=AMBER_LT))
    # KEPT. "still a bunker against catastrophe" is the thesis restated; the
    # bubble says only "a bunker", so the caption is what carries "still" and
    # "against catastrophe" -- the two words the whole chapter turns on.

    def s13_front(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Catastrophe arriving as warmth UNDER the snow. v1 drew a single 12px
        # red line across the lower third of an otherwise empty pale snow field
        # -- a thin stripe on a dead frame. The warm front is now a broad band
        # bleeding up through the snow from the bottom edge, with a hard red
        # leading edge and heat shimmer rising off it.
        for k in range(5):
            t = k / 4.0
            col = (196 - int(52 * t), 84 + int(60 * t), 60 + int(30 * t))
            y = 720 - 40 - k * 26
            PA.fill_rect(tile, [0, y, W, y + 30], col, seed=290 + k, value=0.06)
        PA.hand_stroke(d, [(-40, 512), (320, 490), (660, 504), (1000, 482),
                           (1320, 498)], RED, 16, closed=False, seed=287,
                       wavelength=190.0)
        for k in range(9):
            x = 40 + k * 140
            PA.hand_stroke(d, [(x, 466), (x + 14, 428), (x - 6, 392)],
                           (206, 118, 82), 6, closed=False, seed=320 + k,
                           wavelength=54.0)
        D.draw_label(tile, 'WARMING', center=(320, 640), color=RED, size=44)
    # Live to the END of the stage, not to b33 or b34. Two handovers were
    # stacked on this chain -- front->bare at b33 and front+bare->character at
    # b34 -- and the gate correctly read each as a cut: the element you were
    # looking at vanished and a different one took its place. Held to j=36 the
    # finale is what it should have been: ONE night mountain that has had three
    # things happen to it in sequence, none of which erase the last. The warm
    # front is the slow catastrophe, so it not only stays, it keeps arriving
    # under everything; the bare rock is what it leaves behind; the channel is
    # what that snow was holding. Each arrival is now additive, and the only
    # thing that ever leaves is the character, who is a one-beat visitor.
    els.append(SC.accrue(clock, 32, 34, s13_front, kind='shape'))
    # NO caption at b32. WARMING is DRAWN in red across the advancing front and
    # the front is the catastrophe itself; the words would restate the label.

    def s13_bare(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Bare rock showing through where the snow used to be. The first
        # version was three axis-aligned rectangles, and at ship size they read
        # as grey UI panels floating over the mountain -- they cut straight
        # through the white peak and destroyed the silhouette. These are TWO
        # irregular patches instead. The big one sits low on the snow plain
        # exactly where the presenter stands at b34, so he is standing ON the
        # ground that is being lost: it gives his cream legs something to read
        # against, it anchors him to the frame instead of leaving him floating,
        # and it makes the patch read as terrain rather than a box. The small
        # scar high on the right ridge is more of the same thing further up.
        bare = [(176, 566), (300, 548), (430, 560), (516, 606), (470, 664),
                (330, 684), (200, 656), (168, 610)]
        PA.fill_poly(tile, bare, (128, 122, 116), seed=294, value=0.07)
        PA.hand_stroke(d, bare, INK, 5, closed=True, seed=298, wavelength=120.0)
        scar = [(1080, 420), (1200, 404), (1272, 430), (1244, 458), (1120, 452),
                (1074, 444)]
        PA.fill_poly(tile, scar, (128, 122, 116), seed=295, value=0.07)
        PA.hand_stroke(d, scar, INK, 4, closed=True, seed=299, wavelength=100.0)
        D.draw_number(tile, '-2.6 C', center=(640, 268), color=VT.LABEL_RED,
                      size=132)
        D.draw_label(tile, 'PER DECADE', center=(640, 368), color=VT.LABEL_RED,
                     size=54)
    # Live to b35, NOT to b34. The chain front->bare->character handed over at
    # every beat, and each handover was measured as a cut. Holding the bared
    # slope under the closing beats lets the number stay on screen while he
    # qualifies it ("for now") and while the water runs -- the caveat lands on
    # the figure. But it REPLACES the warm front rather than adding to it: two
    # competing lower-slope bands read as stripes. So the front ends at b33 and
    # the bare ground is what it left behind.
    els.append(SC.accrue(clock, 33, 35, s13_bare, kind='shape',
                         motion=SC.enter(clock, 33, dx=0, dy=-34, dur=ARRIVE)))
    # NO caption at b33. -2.6 C PER DECADE is DRAWN as a 132px numeral over the
    # bared slope; the number is the sentence.

    def s13_fornow(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # Him again, on the same snow, holding the packet. The "for now" bubble
        # is his line -- the caveat is in his mouth, which is where a caveat
        # belongs -- and the packet in his hand is the thing being qualified.
        #
        # STAGING FIX. The first pass put his feet at HZ+10 = 456, which is
        # exactly the dark ridge line of the mountain behind him, so he read as
        # standing on the horizon in mid-air and the -2.6 C numeral ran straight
        # through his legs. He now stands on the NEAR snow at feet_y=612, big
        # enough to be foreground (height 380 rather than 290), and left of the
        # numeral's column so the two never touch.
        SC.fullbody(d, 340, 600, 380, pose='standing', expression='deadpan',
                    seed=303, ink=CREAM)
        _packet(d, 950, 486, 196, 272, 304, band=AMBER, stamp='wheat')
        PA.hand_stroke(d, [(1330, 700), (1040, 590)], (232, 202, 172), 58,
                       closed=False, seed=305, wavelength=150.0)
        D.draw_bubble(tile, 'for now', (1010, 268), tail_to=(930, 388),
                      font_size=34, max_w=300)
    # HELD TO THE END OF THE CHAPTER, not to b35. He used to leave exactly
    # when the water arrived, which is the one moment CLAUDE.md 10.8 names as
    # the beat that must not be without him: "the most emotionally loaded second
    # of each segment should always have the stickman reacting." It also made
    # the finale a swap -- character out, channel in -- which is the cut-in-
    # disguise the critic measured as declining cumulative change (23.5 -> 29.0
    # -> 19.2 -> 11.9%): the chapter got quieter as it got more important.
    # Held, b35 is additive. The man is still standing there, still holding the
    # packet, and the water opens up beside him. Nothing is taken back.
    els.append(SC.accrue(clock, 34, 36, s13_fornow, kind='character',
                         eid='s13_fornow',
                         motion=SC.enter(clock, 34, dx=120, dy=0, dur=0.55)))
    # NO caption at b34. "for now" is the bubble; the packet in his hand is the
    # thing being qualified, and he is holding it in frame.

    def s13_seep(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # The chapter's last line, and the last frame: the water still running
        # under the snow, on the SAME mountain the stage has held since b31.
        #
        # A filled CHANNEL, not a hairline. The first pass drew one 9px stroke
        # and the full-res frame read as an empty white slope with a caption on
        # it -- the closing image of the whole chapter was invisible.
        #
        # STARTED AT x=500, not 200, because he is now held on screen through
        # this beat standing at feet (340,600) and occupying x 250..430. The old
        # channel ran from x200 and s13_seep composites AFTER s13_fornow, so its
        # opaque fill drew straight across his shins -- the same occlusion bug
        # area51 b29 had. The water now opens up BESIDE him, starting 70px
        # clear of his right edge and running off the right frame edge, which
        # also lets the frame admit the channel continues past the picture.
        chan = [(500, 548), (760, 528), (1010, 546), (1200, 566),
                (1200, 640), (1010, 618), (760, 600), (500, 620)]
        PA.fill_poly(tile, chan, WATER, seed=308, value=0.07)
        PA.hand_stroke(d, chan[:4], (156, 186, 200), 7, closed=False,
                       seed=309, wavelength=170.0)
        for k in range(5):
            x = 560 + k * 130
            PA.hand_stroke(d, [(x, 556 + (k % 3) * 10), (x + 46, 596 + (k % 3) * 8)],
                           (156, 186, 200), 5, closed=False, seed=312 + k,
                           wavelength=60.0)
        # MOVED from (880,470) to (690,428). At 880 the label sat directly on
        # the seed packet's wheat band -- amber text on an amber band, i.e. two
        # things of the same colour fighting and neither legible. It now sits
        # over open snow, left of the packet (which starts at x860) and above
        # the channel, so the label names the water without touching anything.
        D.draw_label(tile, 'still seeping', center=(690, 428), color=AMBER_LT,
                     size=46)
    # MOVING, brief. The channel DRIFTS right as the last line lands -- the one
    # motion in the finale, small, and the literal image of "still seeping".
    els.append(SC.accrue(clock, 35, 36, s13_seep, kind='shape',
                         motion=SC.drift(clock, 35, 36, dx=70, dy=0)))
    # DROPPED. It read "Somewhere under the snow, it is still seeping." in the
    # caption band while "still seeping" was DRAWN on the frame 160px above it --
    # the same eight words twice, ~12 seconds apart in reading order, which is
    # the tell-AND-show redundancy the brief is built against ("refrain from
    # adding text in every visual", "you are not telling but also showing"). The
    # drawn label carries it. The narration still says the line; the frame does
    # not have to repeat it.
    #
    # It is also the LAST frame of the chapter, so a caption band here was
    # cutting the film's closing image in half across the bottom third.
    #
    # RE-CHECKED: the chapter's last caption is now b31, four beats earlier, so
    # the no-consecutive-caption rule is still satisfied with room to spare.

    return SC.finish(els, TITLE, clock, title_seed=47)


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        SC.render_preview(sc, os.path.join(SEG, '_preview2_sheet.png'), n=8)
    if '--video' in sys.argv:
        SC.render_video(sc, os.path.join(SEG, '_silent2.mp4'))