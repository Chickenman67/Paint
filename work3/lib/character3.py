# character3.py -- the v3 presenter: a stickman with a FACE.
#
# WHY THIS FILE EXISTS (the single biggest visual gap, measured against the
# reference):
#   Our v2 character rendered as a blank mannequin -- two dot eyes, no
#   eyebrows, a small perfect-circle head, no shading. Side by side with the
#   reference it reads as a shop dummy, not a person reacting.
#
#   The reference character is built from these parts, measured off frames:
#     - head is a WOBBLY BLOB, wider than tall, ~1/3 of total figure height
#     - eyes are LARGE white circles with heavy black rings and pupils
#       OFFSET to one side (he looks where he is going)
#     - EYEBROWS are thick angled strokes and they carry most of the emotion
#     - nose is a soft grey smudge, never a line
#     - mouth is a wavy stroke; the expression library is the whole vocabulary
#     - the head carries a soft volume gradient (grey low-left, highlight top)
#     - limbs are thin sticks with blob hands/feet
#
#   That construction is what makes him legible as a reaction at a glance, so
#   this is a reconstruction of the *technique* (big eyes, angled brows, blob
#   head, volume) -- the art is ours, drawn from primitives, per CLAUDE.md S1.2.
#
# All drawing is deterministic: every random wobble is seeded from the pose
# name, so re-rendering a beat gives byte-identical output (see engine3's
# determinism test).

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# The painterly layer lives in work/lib alongside v2subjects, which engine3 has
# already put on sys.path. Imported defensively so this module still loads (and
# still draws) if it is ever imported on its own -- the PAINTRY path degrades to
# a plain blurred fill and a plain line, which is exactly the round-2 behaviour.
try:
    import v2paint as PA
except ImportError:                                    # pragma: no cover
    PA = None

# --- palette ---------------------------------------------------------------
INK = (26, 26, 30)
FACE_HI = (252, 252, 250)
FACE_LO = (206, 206, 212)
BODY = (26, 26, 30)
WHITE = (255, 255, 255)

# ROUND 4 -- the eye ring. It used to be pure INK at lw*0.78, and at the finale
# close-up (head r=235, lw=31) that is a 24px black hoop around a 141px white
# disc: the whole frame read as a pair of googly eyes stuck on a smooth oval.
# Two changes, both about the ring rather than the eye:
#   * EYE_RING is a dark WARM grey, not the keyline ink. A drawn eye socket is
#     never the same black as the outline that draws the head; making it a
#     separate, slightly lighter tone is what stops the ring reading as a
#     plastic bead seated in a hole.
#   * The ring width is a fraction of the head's own line weight, scaled DOWN
#     as the head grows past a certain size. At the small full-body scale the
#     ring needs to be heavy enough to survive at 25px of head; at close-up it
#     needs to get out of the way. One formula, both reads.
#
# ROUND 5 -- "GOOGLY" IS THREE CONCENTRIC CIRCLES, NOT A BIG EYE. At the finale
# close-up the eye was: a heavy full ring, a white sclera inside it, and a small
# dark pupil in the middle. Three nested circles of decreasing size, all
# perfectly round and all centred on each other, is the exact geometry the word
# "googly" names -- the eye stops being an eye and becomes a bead. Measured on
# the r=235 head: ring 10px, sclera 233px, pupil 93px.
#
# The cure is NOT a smaller eye (that loses the expression at ship size). It is
# to break the concentricity and the symmetry, which is what a real drawn eye
# does and a bead cannot:
#   * NO RING AT ALL above CLOSEUP_R. The sclera is bounded by the heavy TOP
#     LID alone (see below), which is asymmetric by construction. The ring was
#     the only perfectly-circular element left on the head, and removing it at
#     close-up is free: the lid already closes the top of the eye and the
#     shadowed lower rim closes the bottom.
#   * The eye is an ALMOND, not a circle -- 1.10 wide by 0.88 tall, with the
#     widest point above centre. A drawn eye is a lens shape.
#   * The TOP LID is a heavy tapered stroke across the upper third of the eye,
#     thickest at the centre and tapering to nothing at both corners. This is
#     the single strongest de-googly move: it makes the eye read as an eye
#     looking at something rather than as a disc, and it is what carries the
#     expression above the brow.
#   * The pupil is BIGGER (0.46 of the eye radius, up from 0.40) and carries a
#     small white catchlight. A big pupil with a catchlight is unmistakably an
#     illustration of an eye; a small pupil in a big white hole is a bead.
#   * The lower rim is a thin soft shadow arc, not a ring, so the eye still
#     closes at the bottom without becoming a hoop.
EYE_RING = (58, 54, 58)
EYE_SCLERA = (246, 244, 238)   # warm paper-white, not pure #ffffff
EYE_PUPIL = (34, 32, 36)
EYE_CATCH = (252, 251, 246)
EYE_LID_SHADOW = (120, 114, 116)

# Above this head radius the eye loses its ring and gains the almond+lid
# construction. Below it (the full-body figures, head r ~33-50) the old round
# construction is kept: at 90px of head a lid is 5px of noise and the ring is
# what makes the eye read at all.
CLOSEUP_R = 105.0

# ROUND 5 -- HAIR. The head was "a large low-information pale oval": a 502x442
# blob of near-white with four marks on it. Whatever else is true, that is the
# shape of a blank, and blank is what reads as a mannequin. A hairline is the
# cheapest possible cure -- it costs one filled shape, it adds a strong dark
# value to the top of the head (the face is otherwise the lightest thing on the
# frame), and it is the feature a viewer uses to tell a drawn CHARACTER from a
# drawn SHAPE.
HAIR = (58, 48, 46)

# Below this head radius the hair is not drawn. The full-body figures have a
# head radius of 33-50px, where a 0.74-radius cap is a 25px dark band sitting
# directly on top of the brows; at that size it eats the brow -- which is the
# part of the face that carries the expression -- to add a feature the viewer
# cannot resolve. The hair is a CLOSE-UP device, so that is where it is used.
HAIR_MIN_R = 78.0

# Expression table. Each entry drives the FACE only; the body is pose-driven.
# brow: (left_tilt, right_tilt) in degrees, positive = outer edge raised.
# pupil: (dx, dy) as a fraction of eye radius -- the "look where you go" offset.
# mouth: a function name resolved in MOUTHS.
EXPRESSIONS = {
    'neutral':    dict(brow=(2, -2),   pupil=(0.0, 0.0), mouth='flat',      lid=0.0),
    'skeptic':    dict(brow=(14, -14), pupil=(0.30, -0.10), mouth='skeptical', lid=0.10),
    'worried':    dict(brow=(-12, -12), pupil=(0.0, 0.22), mouth='worried',  lid=0.0),
    'scared':     dict(brow=(-20, -20), pupil=(0.0, 0.30), mouth='oval',     lid=0.0),
    'awed':       dict(brow=(-6, -6),  pupil=(0.0, -0.18), mouth='oval',    lid=0.0),
    'deadpan':    dict(brow=(1, -1),   pupil=(0.0, 0.10),  mouth='flat',     lid=0.40),
    'smirk':      dict(brow=(8, -6),   pupil=(0.26, -0.06), mouth='smirk',  lid=0.08),
    'grim':       dict(brow=(-8, -8),  pupil=(0.0, 0.10), mouth='frown',    lid=0.0),
    'shock':      dict(brow=(-24, -24), pupil=(0.0, 0.0), mouth='oval',     lid=0.0),
    'disgust':    dict(brow=(-4, 16),  pupil=(0.18, 0.12), mouth='zigzag',  lid=0.18),
    'confused':   dict(brow=(16, -6),  pupil=(-0.24, 0.10), mouth='flat',   lid=0.12),
}


# --- mouth strokes ---------------------------------------------------------
def _mouth(d, cx, cy, w, kind, painterly=False, seed=0):
    """Draw the mouth. `w` is mouth width; shapes are normalized to it.

    ROUND 4 -- when `painterly`, the two shapes that were mathematically exact
    at close-up scale (the `oval` shock mouth was `d.ellipse(outline=INK,
    width=lw)`, a perfect ellipse of constant weight) go through
    v2paint.hand_stroke over a wobbled path instead. At the small full-body
    scale lw is 11px on a 122px mouth and nobody can tell; at the finale
    close-up lw is 31px on a 310px mouth and the perfect ellipse was one of the
    few remaining machine-exact curves on the head.
    """
    hw = w / 2.0
    lw = max(2, int(round(w * 0.10)))

    if kind == 'oval':
        if painterly and PA is not None:
            pts = PA.wobble_edge(
                PA.ellipse_pts(cx, cy, hw * 0.52, w * 0.34, n=48),
                seed=seed ^ 0x3B1, amount=max(0.6, w * 0.022),
                wavelength=w * 1.1)
            _thick_ink(PA.img_of(d), pts, INK, lw, seed=seed ^ 0x3B2,
                       wavelength=max(10.0, w * 0.9), vary=0.20, closed=True)
        else:
            d.ellipse([cx - hw * 0.52, cy - w * 0.34,
                       cx + hw * 0.52, cy + w * 0.34],
                      outline=INK, width=lw)
        return

    if kind == 'flat':
        # WHY PAINTERLY, NOT d.line. A hard d.line of width w*0.10 is, at
        # close-up scale, a solid horizontal BLACK SLAB -- the deadpan face read
        # as wearing a censor bar. A flat mouth should be a THIN closed line with
        # a hand waver. Draw it as a multi-point stroke so it tapers and wavers
        # like every other ink line, at a lighter weight.
        if painterly and PA is not None:
            # ROUND 6 -- THE SPLIT DEADPAN MOUTH. This used to be FOUR points
            # whose inner pair sat at cy -0.012w then cy +0.010w: a shallow
            # S-wobble. On a nearly-straight path _thick_ink's offset band
            # degenerates -- it rendered the flat mouth as TWO short thin dashes
            # with a gap between them, not a closed line. Every other mouth kind
            # (wavy/frown/smirk/worried/zigzag) was solid, because their paths
            # CURVE, and a curving path keeps the band well-conditioned. The fix
            # is not a different width, it is a better-conditioned PATH: sample
            # a shallow SINGLE-curvature arc (one bow, no S) densely enough that
            # the offset curves never cross. Same stroke, now it connects.
            pts = []
            for i in range(9):
                u = i / 8.0
                pts.append((cx - hw + 2.0 * hw * u,
                            cy + w * 0.018 * math.sin(math.pi * u)))
            _thick_ink(PA.img_of(d), pts, INK, max(4, int(w * 0.058)),
                       seed=seed ^ 0x5A1, wavelength=max(12.0, w * 0.9),
                       vary=0.16)
        else:
            d.line([(cx - hw, cy), (cx + hw, cy)], fill=INK,
                   width=max(2, int(round(w * 0.055))))
    elif kind == 'wavy':
        pts = [(cx - hw, cy), (cx - hw * 0.5, cy + w * 0.10),
               (cx, cy - w * 0.06), (cx + hw * 0.5, cy + w * 0.06),
               (cx + hw, cy)]
        d.line(pts, fill=INK, width=lw, joint='curve')
    elif kind == 'skeptical':
        # asymmetric: flat then a downturn on the right -- the "hmm" mouth
        pts = [(cx - hw, cy), (cx - hw * 0.2, cy - w * 0.05),
               (cx + hw * 0.45, cy + w * 0.06), (cx + hw, cy + w * 0.26)]
        d.line(pts, fill=INK, width=lw, joint='curve')
        # the small lower mark under it
        d.line([(cx - hw * 0.30, cy + w * 0.26), (cx + hw * 0.28, cy + w * 0.24)],
               fill=INK, width=max(2, lw - 1))
    elif kind == 'worried':
        pts = [(cx - hw, cy + w * 0.14), (cx - hw * 0.35, cy - w * 0.10),
               (cx + hw * 0.35, cy - w * 0.10), (cx + hw, cy + w * 0.14)]
        d.line(pts, fill=INK, width=lw, joint='curve')
    elif kind == 'frown':
        pts = [(cx - hw, cy + w * 0.16), (cx, cy - w * 0.10),
               (cx + hw, cy + w * 0.16)]
        d.line(pts, fill=INK, width=lw, joint='curve')
    elif kind == 'smile':
        pts = [(cx - hw, cy - w * 0.10), (cx, cy + w * 0.20),
               (cx + hw, cy - w * 0.10)]
        d.line(pts, fill=INK, width=lw, joint='curve')
    elif kind == 'smirk':
        pts = [(cx - hw * 0.9, cy + w * 0.06), (cx + hw * 0.1, cy - w * 0.02),
               (cx + hw, cy - w * 0.14)]
        d.line(pts, fill=INK, width=lw, joint='curve')
    elif kind == 'zigzag':
        pts = [(cx - hw, cy + w * 0.12), (cx - hw * 0.5, cy - w * 0.10),
               (cx, cy + w * 0.12), (cx + hw * 0.5, cy - w * 0.10),
               (cx + hw, cy + w * 0.12)]
        d.line(pts, fill=INK, width=lw, joint='curve')
    else:
        d.line([(cx - hw, cy), (cx + hw, cy)], fill=INK, width=lw)


MOUTH_ALIASES = {
    'flat': 'flat', 'skeptical': 'skeptical', 'worried': 'worried',
    'frown': 'frown', 'oval': 'oval', 'smile': 'smile', 'smirk': 'smirk',
    'zigzag': 'zigzag', 'deadpan': 'flat',
}


# --- head ------------------------------------------------------------------
def _unit(x, y):
    """A unit vector in the direction (x, y); (0, 0) if degenerate."""
    L = math.hypot(x, y)
    if L < 1e-9:
        return (0.0, 0.0)
    return (x / L, y / L)


def _thick_ink(img, pts, color, width, seed=0, vary=0.20, wavelength=120.0,
               closed=True):
    """A variable-width hand-drawn keyline drawn as a FILLED RING, not as
    per-segment lines.

    WHY THIS EXISTS (round 4). v2paint.hand_stroke walks a centreline and draws
    each segment with its own integer width, dotting a round join only where the
    line turns more than 14 degrees. At the segment widths this file normally
    uses (6-9px on 40-56 point paths) that is invisible. The finale close-up
    has a 31px head rim, and there hand_stroke breaks down: PIL renders each
    thick `line()` as a polygon with very slightly inset ends, so consecutive
    segments that differ in width or angle leave a small WHITE WEDGE at every
    join. On a dense path that is a row of nicks cut into the keyline -- it
    rendered as a chewed, dashed rim that read as a rendering fault, and it was
    the single worst artifact introduced by routing the rim through hand_stroke
    in the first place.

    The fix is to stop thinking of a thick stroke as a sequence of segments. The
    stroke is a BAND: for every sample we know the centreline point and the
    local half-width, so the band is exactly two offset curves -- centre +
    normal*halfwidth, and centre - normal*halfwidth -- joined into one closed
    ring polygon and filled in a single pass. One polygon means one fill, which
    means no joins and no nicks, and the width still swells and thins along its
    length because half-width is a smooth function of arclength. This is the
    same variable-width read as hand_stroke, with the segment artefact removed.

    End caps are rounded by pushing the offset curves past the endpoints and
    letting the polygon close across them, which is what a brush lifting off
    looks like at this scale.

    `img` may be RGB or RGBA; the alpha is taken from the fill's own mask.
    """
    pts = [(float(p[0]), float(p[1])) for p in pts]
    n = len(pts)
    if n < 3 or width <= 0:
        return
    if PA is None or not getattr(PA, 'PAINTERLY', False):
        dd = ImageDraw.Draw(img)
        dd.line(list(pts) + ([pts[0]] if closed else []), fill=color,
                width=max(1, int(round(width))), joint='curve')
        return

    # arclength so the width profile is spatially anchored, not per-index
    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                    pts[i][1] - pts[i - 1][1]))
    if closed:
        s.append(s[-1] + math.hypot(pts[0][0] - pts[-1][0],
                                    pts[0][1] - pts[-1][1]))
    total = max(1.0, s[-1])

    rnd = random.Random(int(seed) & 0x7FFFFFFF ^ 0x5B17)
    ph1 = rnd.uniform(0.0, math.tau)
    ph2 = rnd.uniform(0.0, math.tau)
    wl = max(12.0, float(wavelength))
    k1 = math.tau / wl
    k2 = math.tau / (wl * 0.41)

    m = n if closed else n          # number of samples to walk, one per point
    half = []
    for i in range(m):
        if closed:
            u = s[i] / total
            taper = 1.0
        else:
            u = s[i] / total
            taper = 0.80 + 0.20 * math.sin(math.pi * min(1.0, max(0.0, u)))
        prof = vary * (0.64 * math.sin(k1 * s[i] + ph1)
                       + 0.36 * math.sin(k2 * s[i] + ph2))
        half.append(max(0.8, width * 0.5 * taper * (1.0 + prof)))

    # centreline normals. For a closed loop use the neighbour on each side
    # (wrapping); for an open stroke use one-sided differences at the ends.
    #
    # SIGN MATTERS, and getting it wrong is silent. The tangent-derived normal
    # (-ty, tx) points INWARD for a loop wound one way and OUTWARD for a loop
    # wound the other, and this file's paths are not all wound the same way
    # (ellipse_pts winds one way, PA.wobble_edge can flip nothing but callers
    # build arcs and blobs by hand). If the sign is wrong then `outer` is the
    # inner curve and `inner` is the outer one, the ring polygon self-crosses,
    # and PIL's even-odd polygon fill resolves the overlap into a HOLE -- which
    # rendered as a clean pie-wedge bitten out of every eye ring and out of the
    # mouth. So the winding is measured (signed area) and the normal is oriented
    # to match. For an open stroke the sign is taken from the first non-degenerate
    # sample, the same way.
    area2 = 0.0
    for i in range(n):
        j = (i + 1) % n
        area2 += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    if closed:
        orient = -1.0 if area2 >= 0.0 else 1.0
    else:
        # For an open stroke the shoelace over the endpoints alone is nearly
        # zero and its sign is unstable. Orient against the chord instead: the
        # normal must be consistent (all left or all right of travel) so the
        # outer and inner offset curves never swap sides mid-stroke, which is
        # the self-crossing that produced the bitten-out rings. Take the sign
        # from the summed cross of the overall chord with the mid normal.
        tx = pts[-1][0] - pts[0][0]
        ty = pts[-1][1] - pts[0][1]
        mid = n // 2
        ip, jn = max(0, mid - 1), min(n - 1, mid + 1)
        mx = pts[jn][0] - pts[ip][0]
        my = pts[jn][1] - pts[ip][1]
        orient = 1.0 if (tx * my - ty * mx) <= 0.0 else -1.0

    normals = []
    for i in range(n):
        ip = (i - 1) % n if closed else max(0, i - 1)
        jn = (i + 1) % n if closed else min(n - 1, i + 1)
        tx = pts[jn][0] - pts[ip][0]
        ty = pts[jn][1] - pts[ip][1]
        L = math.hypot(tx, ty)
        if L < 1e-6:
            normals.append((0.0, 0.0))
        else:
            normals.append((-ty / L * orient, tx / L * orient))

    outer, inner = [], []
    for i in range(n):
        nx, ny = normals[i]
        hw = half[i]
        outer.append((pts[i][0] + nx * hw, pts[i][1] + ny * hw))
        inner.append((pts[i][0] - nx * hw, pts[i][1] - ny * hw))

    if closed:
        # CLOSED RINGS ARE BUILT AS A DISC MINUS A DISC, NOT AS ONE ANNULUS
        # POLYGON.
        #
        # The obvious construction -- one polygon that walks the outer offset
        # all the way round and then the inner offset back -- is geometrically
        # correct and renders WRONG. PIL's ImageDraw.polygon scanline fill
        # mishandles the polygon's implicit closing edge: the closing segment
        # from the last inner point back to the first outer point is a radial
        # seam, and the fill leaves a gap along it. Reproduced with no drawing
        # code involved at all: ImageDraw.polygon(outer_ring + inner_ring[::-1])
        # on a clean 72-point circle pair leaves a wedge bitten out of the ring
        # at the seam, and rotating the circle moves the bite with it. It is not
        # a winding problem and not a normal-orientation problem; the polygon is
        # simply the wrong primitive for a ring.
        #
        # So: fill the OUTER loop solid, then knock the INNER loop out of the
        # same mask. Two independent simple polygons, no seam between them,
        # result guaranteed by the fill rule rather than by traversal order.
        xs = [p[0] for p in outer]
        ys = [p[1] for p in outer]
        x0 = int(math.floor(min(xs))) - 3
        y0 = int(math.floor(min(ys))) - 3
        x1 = int(math.ceil(max(xs))) + 4
        y1 = int(math.ceil(max(ys))) + 4
        W_, H_ = img.size
        x0c, y0c = max(0, x0), max(0, y0)
        x1c, y1c = min(W_, x1), min(H_, y1)
        if x1c <= x0c or y1c <= y0c:
            return
        mask = Image.new('L', (x1c - x0c, y1c - y0c), 0)
        md = ImageDraw.Draw(mask)
        md.polygon([(p[0] - x0c, p[1] - y0c) for p in outer], fill=255)
        md.polygon([(p[0] - x0c, p[1] - y0c) for p in inner], fill=0)
        patch = Image.new('RGBA', mask.size, tuple(color[:3]) + (255,))
        img.paste(patch, (x0c, y0c), mask)
    else:
        # OPEN STROKE: a band with two round caps, traversed so the polygon's
        # implicit closing edge is DEGENERATE (its first and last points
        # coincide). The traversal is:
        #     start cap arc (outer[0] side round to inner[0] side)
        #     -> inner curve forward to inner[n-1]
        #     -> end cap arc (inner[n-1] round to outer[n-1])
        #     -> outer curve backward to outer[0]
        # The polygon then closes from outer[0] straight back to the first cap
        # point, which IS outer[0]. A zero-length closing edge cannot leak,
        # which is exactly the seam problem that made the closed ring render a
        # pie-wedge (see the closed branch above). This is the same reason the
        # brow's inner end used to show a white notch: the old cap code built
        # the two cap fans as separate arcs and the fill left a gap where they
        # met the offset curves.
        CAP = 9

        def _cap(center, nrm, tan, hw, sign):
            # A half-disc of radius hw swept from +nrm to -nrm through
            # sign*tan. sign=-1 caps the start (bulge backward), +1 the end.
            cx_, cy_ = center
            nx_, ny_ = nrm
            tx_, ty_ = tan
            out = []
            for i in range(CAP + 1):
                a = math.pi * i / CAP
                ca, sa = math.cos(a), math.sin(a)
                # from +n, rotate toward sign*tan, ending at -n
                vx = nx_ * ca + tx_ * sa * sign
                vy = ny_ * ca + ty_ * sa * sign
                out.append((cx_ + vx * hw, cy_ + vy * hw))
            return out

        # tangents at the two ends (pointing along travel)
        t0 = _unit(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1])
        t1 = _unit(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
        hw0, hw1 = half[0], half[-1]

        start_cap = _cap(pts[0], normals[0], t0, hw0, -1.0)   # outer->inner
        end_cap = _cap(pts[-1], normals[-1], t1, hw1, +1.0)    # inner->outer
        # start_cap[0] == outer[0] and end_cap[-1] == outer[-1]; build the
        # loop so the polygon begins and ends at the same point.
        poly = start_cap + inner[1:] + end_cap + outer[-2::-1]
        PA.fill_poly(img, poly, color, seed=int(seed) & 0x7FFFFFFF,
                     value=0.0, tint=0.0, band=0.0, edge=0.0)


def _blob(cx, cy, rx, ry, seed, n=44, wobble=0.045):
    """A wobbly closed blob -- wider than tall, never a perfect circle."""
    rnd = random.Random(seed)
    phase = rnd.random() * math.tau
    pts = []
    for i in range(n):
        a = i / n * math.tau
        r = 1.0 + wobble * (math.sin(3 * a + phase) * 0.6
                            + math.sin(5 * a + phase * 1.7) * 0.4)
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return pts


def _painterly_face(layer, base, seed, w, h, r):
    """ROUND 4. Paint the face fill the way the rest of the art is painted.

    Replaces the two-ellipse-plus-GaussianBlur ramp. The construction:

      base colour
        * broad value drift          (fbm, cells 4)          -- paint sitting unevenly
        * volume shadow, NOISED      (see below)             -- form, not a gradient
        * highlight, NOISED
        * brush-scale tooth          (fbm, cells 13)         -- bristle texture
        * hue counter-drift          (fbm, cells 5)          -- the warm/cool wobble
        * one broad brush band       (a low-frequency wave)  -- a loaded-brush pass

    The shadow is the whole trick. A smooth darkening toward the lower-left is
    a gradient no matter how it is computed; a smooth darkening whose STRENGTH
    is itself a noise field is a brush that was loaded unevenly, which is what
    paint actually does. So the shadow term is multiplied by a second, coarser
    fbm -- the darkening arrives in patches and misses in others, and the eye
    stops reading a sprayed surface.

    Written into `layer` in place. All randomness comes from PA.fbm, which is
    seeded, so this is deterministic across processes.
    """
    sd = int(seed) & 0x7FFFFFFF
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx / max(1.0, float(w - 1)))          # 0..1 across
    v = (yy / max(1.0, float(h - 1)))          # 0..1 down

    broad = PA.fbm(w, h, seed=sd ^ 0x11, cells=4, octaves=3)
    tooth = PA.fbm(w, h, seed=sd ^ 0x2D, cells=13, octaves=2)
    hue = PA.fbm(w, h, seed=sd ^ 0x77, cells=5, octaves=2)
    # A SEPARATE coarse field for the shadow. Reusing `broad` here would put the
    # shadow exactly where the value drift already is, which cancels the
    # variation instead of breaking the ramp up.
    shuf = PA.fbm(w, h, seed=sd ^ 0x3B9, cells=3, octaves=2)

    b = np.array([float(c) for c in base[:3]], np.float32)

    # --- volume: shadow pools lower-left, highlight rides the upper-right ---
    # Both are soft radial fields, but each is GATED by its own noise field, so
    # the terminator between lit and shaded is ragged rather than a clean arc.
    dcx, dcy = w * 0.14, h * 0.52
    hcx, hcy = w * 0.62, h * 0.10
    dr = float(max(w, h)) * 0.92
    d2s = ((xx - dcx) ** 2 + (yy - dcy) ** 2) / (dr * dr)
    d2h = ((xx - hcx) ** 2 + (yy - hcy) ** 2) / (dr * dr * 0.82)
    shadow = np.clip(1.0 - d2s, 0.0, 1.0) ** 1.5
    highlt = np.clip(1.0 - d2h, 0.0, 1.0) ** 1.6

    # Gate the shadow by a coarse field: 0.55..1.15 of the nominal amount, so
    # some of the head gets a full pass of the shadow and some barely any.
    gate = 0.85 + 0.42 * shuf
    shadow = np.clip(shadow * gate, 0.0, 1.0)
    highlt = np.clip(highlt * (1.20 - 0.34 * shuf), 0.0, 1.0)

    # The shadow DARKENS and slightly cools; the highlight LIGHTENS and warms.
    # Both scale with the head's own size so the effect is a percentage of the
    # face colour rather than a fixed number of levels -- which is what would
    # otherwise make a small head's shadow a five-level nothing and a big head's
    # a grey wash.
    lo = np.array([float(c) for c in FACE_LO], np.float32)
    hi = np.array([float(c) for c in FACE_HI], np.float32)
    out = np.empty((h, w, 3), np.float32)
    sh3 = shadow[..., None]
    hl3 = highlt[..., None]
    out[:] = b[None, None, :]
    out -= (b - lo)[None, None, :] * sh3
    out += (hi - out) * hl3 * 0.9

    # --- paint texture on top, in absolute LEVELS, not percent ---------------
    # v2paint's own fill uses percentages plus an additive dark-weighted tooth.
    # A face is a near-white shape, so a percentage tooth is ~4 levels and an
    # airbrush is exactly what 4 levels of even noise looks like. The tooth
    # here is therefore fixed-size, in LEVELS, independent of the base colour,
    # which is what makes a 500px head and a 60px head carry the same kind of
    # texture. Levels are sized against the head's own radius so the effect is
    # proportional at both ends of the scale.
    k = max(0.30, min(1.0, r / 235.0))    # 1.0 at the close-up, 0.30 small
    out += (k * (5.2 * broad + 4.0 * tooth))[..., None]

    # hue counter-drift: a couple of levels of red up / blue down. This is the
    # one term that DOES look wrong if overdone on a near-white -- at the
    # close-up the sclera showed visible pink/blue speckle -- so it stays small
    # and, unlike the fill above, is centred on zero so the face's mean
    # temperature does not drift.
    out[..., 0] += k * 2.6 * hue
    out[..., 2] -= k * 2.6 * hue

    # Two brush passes, phase-wandered by the value field so neither rules a
    # straight stripe. The period is tied to the HEAD, not to the tile: at
    # r=235 a ~180px period is a loaded-brush width, at r=50 the same formula
    # gives ~40px, which is still a couple of brush widths across a small face.
    # (v2paint.BAND_FREQ is tuned for 450px discs; this is the same idea at
    # whatever size the caller asked for.)
    bandf = math.tau / max(26.0, r * 0.80)
    out += (k * 6.2 * np.sin(xx * bandf + yy * bandf * 0.31
                             + 2.6 * broad))[..., None]
    bandf2 = math.tau / max(18.0, r * 0.34)
    out += (k * 3.4 * np.sin(xx * bandf2 * 0.7 - yy * bandf2
                             + 2.2 * broad + 1.1))[..., None]

    # Keep a little of the paper's own tooth visible through the paint.
    out += k * 1.8 * PA.fbm(w, h, seed=sd ^ 0x5D1, cells=26, octaves=1)[..., None]

    np.clip(out, 0.0, 255.0, out=out)
    layer.paste(Image.fromarray(out.astype(np.uint8), mode='RGB'), (0, 0))


def _hair_pts(cx, cy, rx, ry, seed, r, spread=128.0, depth=0.46):
    """The hairline: a closed polygon for a painted cap of hair over the crown.

    Built from the SAME blob radii the head rim uses, so the hair can never float
    off the head or cross its outline -- and because it is painted into the face
    LAYER before that layer is masked by the blob alpha, the wobbly silhouette
    clips it for free.

    Geometry: the outer edge is the head's own ellipse from `spread` degrees
    either side of the crown; the inner edge (the HAIRLINE) is a second walk of
    the same ellipse scaled toward the centre by a factor that VARIES along the
    walk. `depth` is that factor at the CROWN and the temples run out to ~1.0
    (no hair) at the ends of the spread.

    So the hair is a crescent: thick over the top of the skull, sweeping down
    into two points at the temples, with bare face below. This is the single
    change that stops the head reading as a blank pale oval -- it puts a big dark
    value on the crown (the face is otherwise the lightest thing on the frame)
    and gives the silhouette a hairline instead of a dome.

    ROUND 5 FOLTHROUGH. The first attempt used `spread=196, depth=0.74` with the
    OPPOSITE taper (thin at the crown, running to full radius at the temples).
    392 degrees of spread is the whole head, so the two temple points met under
    the chin and the crescent closed into a RING: it rendered as a dark hood
    framing a small pale hole, the exact opposite of the intent. The crown also
    ended up only 26% of the radius thick, i.e. a hairline perched at the top of
    the skull. Fixed by (a) cutting the spread to 142 degrees so the two points
    die on the temples well above the jaw, and (b) making the crown the THICK
    end (depth 0.46) tapering to nothing at the temples, which is how hair parts
    over a forehead.
    """
    n = 96
    outer, inner = [], []
    rnd = random.Random(seed ^ 0x4A11)
    ph = rnd.random() * math.tau
    # theta measured in PIL's convention: 0 deg = 3 o'clock, y grows DOWNWARD.
    # The crown is therefore 270 deg, and the cap runs symmetrically either side.
    for i in range(n + 1):
        u = i / float(n)
        th = math.radians(270.0 - spread + 2.0 * spread * u)
        ca, sa = math.cos(th), math.sin(th)
        # uneven, hand-cut temples: the two ends of the hairline do not mirror
        asym = 1.0 + 0.05 * math.sin(2.0 * math.pi * u + ph)
        # THICK at the crown, running out to no-hair at the temples:
        # s = 0 at the crown, 1 at each end.
        s = abs(2.0 * u - 1.0)
        f_crown = depth + (1.0 - depth) * (s ** 1.35)
        # a slow wave along the hairline so it is not a drawn arc.
        # Kept small: at 0.022+0.013 the third-harmonic lobe cut a visible
        # "M"/cowlick notch into the middle of the hairline, which read as a
        # crease in the skull rather than as hair. Amplitude halved.
        wl = (math.sin(math.pi * u * 3.0 + ph) * 0.011
              + math.sin(math.pi * u * 5.0 + ph * 1.7) * 0.006)
        f = (f_crown + wl) * asym
        outer.append((cx + ca * rx, cy + sa * ry))
        inner.append((cx + ca * rx * f, cy + sa * ry * f))
    return outer + inner[::-1]


def draw_head(img, cx, cy, r, expression='neutral', seed=0,
              lw=None, face_fill=None):
    """The face. `r` is the head RADIUS; the head is 1.14x wider than tall."""
    d = ImageDraw.Draw(img)
    e = EXPRESSIONS.get(expression, EXPRESSIONS['neutral'])
    rx, ry = r * 1.07, r * 0.94
    lw = lw or max(3, int(round(r * 0.13)))

    # volume: soft grey low-left, bright highlight top-centre.
    # Build the shaded head on its own RGBA layer, masked by the blob alpha.
    pts = _blob(cx, cy, rx, ry, seed)
    w, h = int(rx * 2) + 4, int(ry * 2) + 4
    ox, oy = int(cx - rx) - 2, int(cy - ry) - 2

    layer = Image.new('RGB', (w, h), face_fill or FACE_HI)
    ld = ImageDraw.Draw(layer)
    # shadow pools low-left
    ld.ellipse([w * 0.42, h * 0.36, w * 1.95, h * 1.95], fill=FACE_LO)
    # highlight top-centre
    ld.ellipse([w * 0.70, h * 0.04, w * 1.75, h * 0.86],
               fill=face_fill or FACE_HI)
    layer = layer.filter(ImageFilter.GaussianBlur(max(1, int(r * 0.14))))

    # ROUND 4 -- THIS WAS THE AIRBRUSH. Two overlapping ellipses blurred by
    # r*0.14 is a textbook airbrush: at the finale close-up (r=235) that is a
    # 33px blur over a 500px head, so the fill came out as one perfectly smooth
    # white-to-grey ramp with a visible hard terminator where the shadow
    # ellipse's edge survived the blur. Sitting next to a planet that had just
    # been given real fbm mottling and brush banding, the face was the one
    # airbrushed object left on the frame.
    #
    # It is now built the way everything else in the segment is built: a base
    # colour, a seeded low-frequency value field, a hue counter-drift, and a
    # brush-scale tooth, all composited in numpy and then MASKED by the blob --
    # and the volume shadow is multiplied by that same noise field instead of
    # being composited as its own smooth ramp. That is the important part: a
    # painter laying in a shadow with a brush does not get an even gradient, so
    # multiplying the shadow by the paint field breaks the ramp into visible
    # loaded/unloaded patches and the face stops reading as sprayed.
    if PA is not None and getattr(PA, 'PAINTERLY', False):
        _painterly_face(layer, face_fill or FACE_HI, seed, w, h, r)
    else:
        ld.ellipse([w * 0.42, h * 0.36, w * 1.95, h * 1.95], fill=FACE_LO)
        ld.ellipse([w * 0.70, h * 0.04, w * 1.75, h * 0.86],
                   fill=face_fill or FACE_HI)
        layer = layer.filter(ImageFilter.GaussianBlur(max(1, int(r * 0.14))))

    # ---- ROUND 5: the hairline, painted INTO the face layer ----------------
    # Painting it into `layer` rather than onto `img` is deliberate and load
    # bearing: the layer is composited through the blob's alpha mask, so the
    # hair is CLIPPED to the head silhouette for free. Drawn straight onto `img`
    # it would spill past the wobbly rim wherever the hair's clean-ellipse outer
    # edge happened to sit outside the blob's 3rd/5th-harmonic silhouette, and
    # the spill is what reads as a rendering fault rather than as hair.
    if r >= HAIR_MIN_R:
        hp = _hair_pts(cx, cy, rx, ry, seed, r)
        hp = [(x - ox, y - oy) for x, y in hp]
        if PA is not None and getattr(PA, 'PAINTERLY', False):
            PA.fill_poly(layer, hp, HAIR, seed=seed ^ 0x4A22, value=0.13,
                         tint=5.0, band=5.0, edge=3.0, grow=2)
        else:
            ImageDraw.Draw(layer).polygon(hp, fill=HAIR)

    alpha = Image.new('L', (w, h), 0)
    ImageDraw.Draw(alpha).polygon([(x - ox, y - oy) for x, y in pts], fill=255)
    img.paste(layer, (ox, oy), alpha)

    # blob outline on top.
    # ROUND 4: this was a constant-width `d.line(..., joint='curve')`. Every
    # other outline in the segment goes through v2paint.hand_stroke and swells
    # and thins; the head rim did not, and at close-up a 31px constant-width
    # hoop is the most conspicuous machine edge on the frame. hand_stroke also
    # re-displaces the rim itself (wobble_edge), so the ink no longer sits on a
    # mathematically smooth blob.
    PA_hs = PA.hand_stroke if PA is not None else None
    if PA_hs is not None and getattr(PA, 'PAINTERLY', False):
        # The rim is drawn as a single filled ring by _thick_ink, NOT by
        # hand_stroke. See _thick_ink for the long version: hand_stroke draws a
        # thick line as a chain of per-segment polygons, and at this rim weight
        # (31px on the finale close-up) every one of those segments leaves a
        # small white wedge at its join -- 200 nicks cut into the keyline, which
        # read as a chewed, dashed contour rather than as a hand. _thick_ink
        # fills the whole band as ONE polygon, so there are no joins to leak and
        # the width still swells and thins along the rim.
        #
        # The rim path is the blob sampled DENSELY and NOT re-wobbled. Two
        # earlier attempts are recorded in _thick_ink's neighbourhood and in git
        # history for the same reason: a sparse 44-point blob gets square notch
        # dots where it turns sharply, and a dense blob that is THEN wobbled edge
        # gets high-frequency silhouette noise (the arclength step becomes much
        # shorter than the wobble wavelength). _blob's own low-frequency
        # 3rd/5th-harmonic silhouette is already the hand-drawn irregularity;
        # sampling it finely and stroking the band is enough.
        rim = _blob(cx, cy, rx, ry, seed, n=200)
        _thick_ink(img, rim, INK, lw, seed=seed ^ 0x5C2,
                   wavelength=max(30.0, r * 1.6), vary=0.20, closed=True)
    else:
        d.line(list(pts) + [pts[0]], fill=INK, width=lw, joint='curve')

    # --- eyes: big rings, offset pupils ---
    er = r * 0.30                     # eye radius -- LARGE, this is the fix
    ex = r * 0.48                      # wider eye spacing -> brows can't merge into a unibrow
    ey = cy - r * 0.02              # eyes near the vertical centre of the blob
    pdx, pdy = e['pupil']
    painterly = PA is not None and getattr(PA, 'PAINTERLY', False)
    closeup = r >= CLOSEUP_R

    # ROUND 4 -- THE GOOGLY READ. See EYE_RING above. The ring weight scales
    # DOWN with head size: at the small full-body figure (r~50) it is nearly
    # lw*0.78 as before, because a 4px ring is all a 60px eye has.
    #
    # ROUND 5 -- THE RING IS GONE AT CLOSE-UP, AND THE EYE IS AN ALMOND. See the
    # EYE_RING comment: "googly" is the GEOMETRY of three nested concentric
    # circles, so thinning the ring (round 4) was treating a symptom. At close-up
    # there is no ring at all; the eye is bounded above by a heavy tapered LID
    # and below by a thin shadow arc, which is asymmetric by construction and so
    # cannot read as a bead however large the sclera is.
    ring_w = max(1.5, lw * (0.78 - 0.46 * min(1.0, r / 150.0)))
    if closeup:
        erx, ery = er * 1.10, er * 0.88      # an almond, widest above centre
    else:
        erx, ery = er * 0.99, er * 0.99
    for si, sx in enumerate((-1, 1)):
        cx_e = cx + sx * ex
        k = si                                   # 0 = left eye, 1 = right eye
        if painterly:
            # Painted sclera: a wobbly disc carrying the same tooth as the face,
            # so the eye is a drawn mark and not a hole cut in the paper.
            #
            # ROUND 4 FOLTHROUGH. The first attempt sampled n=28 and wobbled by
            # 5% of the radius, which rendered as an obvious DECAGON -- an eye
            # with visible straight facets reads as a modelling error, not as a
            # drawn circle. So: sample densely (n=72), wobble far less (2.2%),
            # and wobble at a wavelength comparable to the eye's own size so the
            # displacement is a broad soft irregularity rather than a ring of
            # bumps. And tint MUST be zero: v2paint's default is +-8 levels of
            # red/blue counter-drift, which on a near-white sclera is visible
            # pink-and-blue chroma speckle, not a subtle hue wobble.
            eye_pts = PA.wobble_edge(
                PA.ellipse_pts(cx_e, ey, erx * 0.99, ery * 0.99, n=72),
                seed=seed ^ (0xE7E + k),
                amount=max(0.35, er * 0.022), wavelength=er * 2.6)
            PA.fill_poly(img, eye_pts, EYE_SCLERA,
                         seed=seed ^ (0xE11 + k),
                         value=0.055, tint=0.0, band=0.0, edge=0.0)
            if closeup:
                # --- THE TOP LID. The strongest de-googly mark there is.
                # An arc across the upper third of the eye, sampled at 0.965 of
                # the sclera radius so its outer half laps over the sclera's
                # edge and closes the eye against the face. It spans 196..344
                # deg in PIL's convention (0 = 3 o'clock, y down), i.e. from the
                # left corner, over the top, to the right corner. _thick_ink's
                # open-stroke taper (0.80 at each end, 1.0 mid) makes it
                # thickest at the centre of the lid and vanishing at the
                # corners, which is how a lid is drawn and is the opposite of
                # the constant-width hoop it replaces.
                lid = PA.arc_pts(cx_e, ey, erx * 0.965, ery * 0.965,
                                 196, 344, n=40)
                _thick_ink(img, lid, INK, lw * 0.62, seed=seed ^ (0xE33 + k),
                           wavelength=max(14.0, er * 1.5), vary=0.22,
                           closed=False)
                # --- the lower rim, as a soft shadow arc rather than a ring, so
                # the eye still closes at the bottom without becoming a hoop
                low = PA.arc_pts(cx_e, ey, erx * 0.99, ery * 0.99,
                                 24, 156, n=28)
                _thick_ink(img, low, EYE_LID_SHADOW, lw * 0.20,
                           seed=seed ^ (0xE44 + k),
                           wavelength=max(12.0, er * 1.3), vary=0.30,
                           closed=False)
            else:
                _thick_ink(img, eye_pts, EYE_RING, ring_w,
                           seed=seed ^ (0xE22 + k),
                           wavelength=max(10.0, er * 2.6), vary=0.20, closed=True)
        else:
            if closeup:
                d.ellipse([cx_e - erx, ey - ery, cx_e + erx, ey + ery],
                          fill=EYE_SCLERA)
                d.arc([cx_e - erx, ey - ery, cx_e + erx, ey + ery],
                      196, 344, fill=INK, width=max(2, int(lw * 0.62)))
                d.arc([cx_e - erx, ey - ery, cx_e + erx, ey + ery],
                      24, 156, fill=EYE_LID_SHADOW, width=max(2, int(lw * 0.20)))
            else:
                d.ellipse([cx_e - er, ey - er, cx_e + er, ey + er],
                          fill=EYE_SCLERA, outline=EYE_RING,
                          width=max(2, int(round(ring_w))))
        # ROUND 5 -- a BIGGER pupil with a catchlight. A small dark pupil
        # centred in a big white hole IS a bead; a pupil that fills 46% of the
        # eye and carries a small white highlight is unmistakably a drawn eye
        # looking at something. The catchlight is the tell -- no physical bead
        # has one.
        pr = er * (0.46 if closeup else 0.40)
        px = cx_e + pdx * er
        py = ey + pdy * er
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=EYE_PUPIL)
        if closeup:
            cr = pr * 0.30
            d.ellipse([px - pr * 0.36 - cr, py - pr * 0.40 - cr,
                       px - pr * 0.36 + cr, py - pr * 0.40 + cr], fill=EYE_CATCH)
        # eyelid for deadpan / half-lidded looks
        #
        # ROUND 5. This used to draw a filled EYE_RING chord across the top of
        # the eye and then a bright EYE_SCLERA line across the middle -- at
        # close-up scale that white band read as a BLINDFOLD. And because the
        # closeup path (above) already draws a proper tapered top-lid arc, the
        # deadpan lid stacked a second, cruder lid on top. Now: for CLOSE-UP we
        # only add a heavier ink lash arc a little lower than the existing lid --
        # no fill, no white -- which is how a heavier, more bored lid is drawn.
        # For the smaller full-body face the polygon lid (face-coloured, with a
        # lash line) still reads, so it is kept there.
        if e['lid'] > 0:
            drop = ery * e['lid'] * 1.30          # how far the lid descends
            lid_edge = ey - ery + drop             # its lower edge
            if closeup:
                lash = PA.arc_pts(cx_e, lid_edge + ery * 0.10,
                                  erx * 0.99, ery * 0.99, 200, 340, n=32)
                _thick_ink(img, lash, INK, lw * 0.72, seed=seed ^ (0xE55 + k),
                           wavelength=max(14.0, er * 1.5), vary=0.24,
                           closed=False)
            else:
                lid_pts = [(cx_e - erx * 1.02, ey - ery * 1.15),
                           (cx_e + erx * 1.02, ey - ery * 1.15),
                           (cx_e + erx * 1.02, lid_edge),
                           (cx_e - erx * 1.02, lid_edge)]
                d.polygon(lid_pts, fill=face_fill or FACE_HI)
                if painterly and PA is not None:
                    lash = PA.wobble_edge(
                        [(cx_e - erx * 0.98, lid_edge), (cx_e, lid_edge),
                         (cx_e + erx * 0.98, lid_edge)],
                        seed=seed ^ (0xE55 + k), amount=max(0.5, ery * 0.03),
                        wavelength=erx * 2.0)
                    _thick_ink(PA.img_of(d), lash, INK,
                               max(3, int(lw * 0.55)),
                               seed=seed ^ (0xE66 + k),
                               wavelength=max(12.0, erx * 1.4), vary=0.20)
                else:
                    d.line([(cx_e - erx * 0.98, lid_edge),
                            (cx_e + erx * 0.98, lid_edge)],
                           fill=INK, width=max(2, int(lw * 0.55)))

    # --- eyebrows: the emotion carriers ---
    # Each brow is a short thick stroke sitting just above its eye, tilted by
    # the expression. tilt>0 raises the OUTER end.
    #
    # ROUND 4. These used to be `d.line([inner, outer], width=bw)` plus a
    # round blob at each end -- a capsule of exactly constant width. At the
    # close-up that is a 29px x 122px SLAB of pure ink hanging in mid-face, and
    # because both ends are identical it has no gesture in it: it reads as a
    # piece of tape rather than as a drawn brow. They now go through
    # hand_stroke along a slightly ARCHED path, which gives three things at
    # once: the width swells and thins like a marker stroke, the arch gives the
    # brow a direction of travel, and the ends taper instead of stopping dead.
    # The emotional VALUES (lt/rt) are untouched -- the brows still carry the
    # expression, they just carry it with a drawn line now.
    lt, rt = e['brow']
    bw = max(2, int(round(lw * 0.90)))
    # `painterly` already computed by the eye block above; the brows, nose and
    # mouth all use the same paint path as the eyes.
    for si, (sx, tilt) in enumerate(((-1, lt), (1, rt))):
        cx_e = cx + sx * ex
        # ROUND 5 -- at close-up the eye's top boundary is the LID (which sits at
        # ery of the almond), not the ring, and the hair now covers the top of
        # the head. Lifting the brow line clears the lid by a real margin
        # instead of grazing it, which at the old `er` put the brow's lower
        # edge inside the lid stroke.
        brow_lift = ery if closeup else er
        by = ey - brow_lift - r * 0.15    # clear of the eye AND the hairline
        half = r * 0.26                   # brow half-length (short, so they stay separate)
        # raise the outer end: outer side is sx direction
        outer_dy = math.sin(math.radians(tilt)) * half * 0.9
        inner_dy = -math.sin(math.radians(tilt)) * half * 0.9
        inner = (cx_e - sx * half, by + inner_dy)
        outer = (cx_e + sx * half, by + outer_dy)
        if painterly:
            # Sample the straight chord as a shallow arc bowing AWAY from the
            # eye. The bow is what stops it reading as a ruled bar.
            #
            # ROUND 4 FOLTHROUGH: this first carried a smooth_walk lateral
            # wobble as well, at r*0.016 (3.8px at the close-up) over a
            # 3-cell walk across a 122px chord. That is a high-frequency
            # perturbation of a short span, and it rendered the brows as
            # SCRATCHY ZIGZAGS -- two scribbles over the eyes rather than two
            # drawn brows. The lesson is the same one the rim taught: a walk
            # whose wavelength is short relative to the span it covers is noise,
            # not a hand. So there is no lateral wobble here at all; the only
            # irregularity is hand_stroke's width profile along the arc.
            brow_pts = []
            for i in range(25):
                u = i / 24.0
                px_ = inner[0] + (outer[0] - inner[0]) * u
                py_ = inner[1] + (outer[1] - inner[1]) * u
                py_ -= math.sin(math.pi * u) * r * 0.034
                brow_pts.append((px_, py_))
            _thick_ink(img, brow_pts, INK, bw, seed=seed ^ (0xB41 + si),
                       wavelength=max(12.0, half * 1.6), vary=0.26,
                       closed=False)
        else:
            d.line([inner, outer], fill=INK, width=bw)
            rr = bw / 2.0
            for pt in (inner, outer):
                d.ellipse([pt[0] - rr, pt[1] - rr, pt[0] + rr, pt[1] + rr],
                          fill=INK)

    # --- nose: a soft smudge, never a line ---
    # ROUND 4: this was one flat #96969E ellipse, so on the painted face it was
    # a hard little grey pill -- the only remaining machine mark on the head. It
    # is now a blurred smudge (a real thumb-smudge of a nose) whose intensity
    # varies, so it fades out at the edges instead of ending on a boundary.
    ny = cy + r * 0.20
    nr = max(2.0, r * 0.105)
    if painterly:
        nw, nh = int(nr * 3.2), int(nr * 2.0)
        nl = Image.new('L', (nw, nh), 0)
        nd = ImageDraw.Draw(nl)
        nd.ellipse([nw * 0.12, nh * 0.22, nw * 0.88, nh * 0.78], fill=190)
        nl = nl.filter(ImageFilter.GaussianBlur(max(1, int(nr * 0.30))))
        # break the smudge up with the same tooth the face carries, so it is a
        # mark on painted skin rather than a decal sitting on top of it
        nlarr = np.asarray(nl).astype(np.float32)
        nlarr *= (0.72 + 0.30 * PA.fbm(nw, nh, seed=seed ^ 0xB7C, cells=3,
                                       octaves=2))
        # ROUND 6 -- THE SMUDGE READS AS DIRT. It was pasted in cool grey
        # (150,150,158) at alpha 190 over a warm near-white face, so at close-up
        # scale it was the only cool mark on the head and floated between the
        # eyes like a smudge. Warm it toward the skin and drop the opacity so it
        # reads as a soft shadow-nose, not a stain.
        img.paste(Image.new('RGBA', (nw, nh), (188, 180, 178, 255)),
                  (int(cx - nw / 2), int(ny - nh / 2)),
                  Image.fromarray(np.clip(nlarr * 0.62, 0, 255).astype(np.uint8), 'L'))
    else:
        d.ellipse([cx - r * 0.10, ny - r * 0.055, cx + r * 0.10, ny + r * 0.055],
                  fill=(188, 180, 178))

    # --- mouth ---
    _mouth(d, cx, cy + r * 0.52, r * 0.66,
           MOUTH_ALIASES.get(e['mouth'], e['mouth']),
           painterly=painterly, seed=seed ^ 0x4D5)
    return (cx, cy, rx, ry)


# --- body ------------------------------------------------------------------
POSES = {
    # Arm convention (see _limb): a1 = upper-arm angle, a2 = forearm bend ADDED
    # to a1, so the forearm's absolute angle is a1 + a2. 0 = straight down;
    # positive swings out and up. So (18, 22) = arm hanging slightly out with a
    # gentle elbow; (46, 62) = shrug, forearms up; (100, 52) = hands raised.
    # NOTE: an older comment here read "(95, -70) = forearm coming back up",
    # which is backwards for this convention and is exactly how handsup ended up
    # authored as surrender. Trust the shrug, not that line.
    'standing': dict(
        la=(19, 17), ra=(19, 17),
        ll=(-9, 0), rl=(9, 0), lean=0),
    'pointing': dict(
        la=(16, 24), ra=(78, 12),          # right arm raised, pointing out
        ll=(-12, 0), rl=(11, 0), lean=-3),
    # Pointing the OTHER way. draw_character negates the LEFT arm's angle
    # (`_limb(cx - head_r*0.5, sh_y, -p['la'][0], -p['la'][1], ...)`), so a
    # positive la swings that arm toward image-LEFT. 'pointing' raises ra; this
    # is the same arm angles on la, so the figure points left with no mirroring
    # code. Needed wherever the thing being indicated sits to the figure's left
    # and the stock 'pointing' would send the arm off the opposite frame edge.
    'pointingL': dict(
        la=(78, 12), ra=(16, 24),          # left arm raised, pointing out (left)
        ll=(-11, 0), rl=(12, 0), lean=3),
    'handsup': dict(
        # a2 is the FOREARM OFFSET ADDED to the upper-arm angle, so the
        # forearm's absolute angle is a1 + a2; positive swings it further
        # out/up (the shrug below relies on that). This pose was authored with
        # a2 NEGATIVE, which swung the forearm back DOWN and rendered as
        # surrender -- the exact opposite of the name. Now: upper arm out at
        # 100 deg, forearm continuing to 152 deg, i.e. up and slightly in.
        la=(100, 52), ra=(100, 52),        # both arms raised, palms up
        ll=(-11, 0), rl=(11, 0), lean=0),
    'shrug': dict(
        la=(46, 62), ra=(46, 62),          # elbows out, forearms up
        ll=(-9, 0), rl=(9, 0), lean=0),
    'recoil': dict(
        la=(74, 44), ra=(68, 40),          # arms flung up and back
        # was ll/rl = -3/+3, a 6 deg total splay: both legs left the hip within
        # a few pixels of each other and the whole lower body read as one pole.
        ll=(-12, 0), rl=(13, 0), lean=5),
    'peeking': dict(
        la=(20, 46), ra=(20, 46),
        ll=(-8, 0), rl=(8, 0), lean=9),
    'armscrossed': dict(
        la=(38, 78), ra=(38, 78),
        ll=(-10, 0), rl=(11, 0), lean=0),
    'wave': dict(
        la=(16, 22), ra=(72, -34),         # one arm up, waving
        ll=(-10, 0), rl=(10, 0), lean=-3),
    'sitting': dict(
        la=(18, 40), ra=(18, 40),
        ll=(-64, 0), rl=(64, 0), lean=0),
}


def draw_character(img, cx, y_feet, height, pose='standing',
                   expression='neutral', seed=0, ink=BODY,
                   head_fill=None, face_fill=None, scale_x=1.0):
    """Draw the full figure. `y_feet` is the ground line; `height` total."""
    p = POSES.get(pose, POSES['standing'])
    rnd = random.Random('%s|%s|%d' % (pose, expression, seed))

    # --- proportions ---------------------------------------------------------
    # THIRD ATTEMPT AT THIS, and the arithmetic finally matches the picture.
    #   attempt 1: head 25%, torso 21%  -> torso shorter than the head is tall
    #   attempt 2: head 21%, torso 26%  -> shoulders only 5% of height below the
    #              head, so the arms appeared to sprout from the NECK and no
    #              torso was visible at all
    # What is used now is a plain 5-head cartoon build, measured top-down:
    #     head   20%   (1.0 head)
    #     torso  30%   (shoulder line at 1 head, hips at 2.5 heads)
    #     legs   50%   (hips at 2.5, feet at 5)
    # The single lever that fixed it was dropping the SHOULDER LINE explicitly
    # rather than deriving it from the head radius. Deriving it couples the
    # torso length to the head size, so shrinking the head silently shortens
    # the torso and the figure collapses back into stilts.
    head_r = height * 0.100                      # head = 1/5 of the figure
    head_cy = y_feet - height + head_r * 1.05
    # THICKER INK. At height*0.022 a 430px figure got a 9px stroke, which at
    # playback reads as a wire -- the figure looked like a coat-hanger rather
    # than a person. The reference's presenter is drawn with a marker, roughly
    # 1/40th of his height. This is 1/34.
    lw = max(4, int(round(height * 0.029)))
    # The head rim is NOT the body stroke. Passing the body lw straight through
    # gave a 13px keyline on a 45px-radius head -- 29% of the radius -- and the
    # face collapsed into a small hole inside a dark ring, which is the
    # "bandit mask" read. The rim has to scale with the HEAD, not the figure,
    # so it is clamped here. This is the single change that makes the full-body
    # face legible; nothing else about the head needed fixing.
    head_lw = max(3, int(round(head_r * 0.115)))
    sh_y = y_feet - height * 0.80                # shoulder line, 20% down
    hip_y = y_feet - height * 0.50               # hips at 50%; legs = 50%
    lean = math.radians(p['lean'])

    def _limb(x0, y0, a1, a2, L1, L2, blob_end=True):
        """Two-segment limb with a real elbow.

        Angle convention: 0 = straight DOWN, positive swings the segment
        outward/away from the body (and can go negative to raise). This is what
        the POSES table is written in, so an arm at (52, 8) raises and points
        out rather than folding upward the wrong way.
        """
        d = ImageDraw.Draw(img)
        # upper segment
        a1r = math.radians(a1)
        ux, uy = math.sin(a1r), math.cos(a1r)
        mx = x0 + ux * L1
        my = y0 + uy * L1
        # forearm continues from the same absolute angle offset
        a2r = math.radians(a1 + a2)
        ex_ = mx + math.sin(a2r) * L2
        ey = my + math.cos(a2r) * L2
        # Hand-drawn segments rather than uniform d.line strokes: each segment
        # is sampled along its length (so _thick_ink can swell and taper it)
        # and the elbow is a filled joint blob. A constant-width d.line reads as
        # a wire; this reads as a drawn limb. The elbow ANGLE is what makes the
        # arm read as bent (memory elbow-existence-is-not-elbow-visibility), and
        # a rounded joint is what makes that bend visible at playback size.
        def _seg(xa, ya, xb, yb, sd):
            n = 10
            pts = [(xa + (xb - xa) * i / float(n),
                    ya + (yb - ya) * i / float(n)) for i in range(n + 1)]
            _thick_ink(img, pts, ink, lw, seed=sd, wavelength=max(40.0, L1),
                       vary=0.14, closed=False)
        _seg(x0, y0, mx, my, seed ^ 0x311)
        _seg(mx, my, ex_, ey, seed ^ 0x322)
        # elbow joint: a filled disc a touch larger than the stroke
        rr = lw * 0.62
        d.ellipse([mx - rr, my - rr, mx + rr, my + rr], fill=ink)
        if blob_end:
            # A hand, not a ball. At lw*1.6 this was a 21px-radius disc against
            # a 45px head -- the hands were HALF the size of his skull, which is
            # what made the figure read as a marionette. A hand is roughly the
            # head's sixth-to-eighth across, so the blob is scaled to the HEAD
            # and flattened, not scaled to the stroke.
            hr = max(lw * 0.85, head_r * 0.20)
            d.ellipse([ex_ - hr, ey - hr * 1.15, ex_ + hr, ey + hr * 1.15],
                      fill=ink)
        return mx, my, ex_, ey

    def _seg_leg(a, b, sd):
        """One leg segment, hand-drawn like the arm segments. a/b are (x, y)."""
        n = 8
        pts = [(a[0] + (b[0] - a[0]) * i / float(n),
                a[1] + (b[1] - a[1]) * i / float(n)) for i in range(n + 1)]
        _thick_ink(img, pts, ink, lw, seed=sd, wavelength=max(40.0, leg_len),
                   vary=0.12, closed=False)

    # Arm reach as a fraction of the TORSO span, so it tracks whatever the
    # proportions above are. With the 5-head build the torso is 30% of height,
    # so 0.72+0.68 carries the hands to just below the hip. Attempt 2 used
    # 0.62/0.62 against a 21% torso, which put the fingertips level with the
    # knees and made the figure read as four-legged.
    L1 = (hip_y - sh_y) * 0.72
    L2 = (hip_y - sh_y) * 0.68
    _limb(cx - head_r * 0.50, sh_y, -p['la'][0], -p['la'][1], L1, L2)
    _limb(cx + head_r * 0.50, sh_y, p['ra'][0], p['ra'][1], L1, L2)

    # Legs: hip -> foot, splayed so the stance reads. Feet are blobs.
    d = ImageDraw.Draw(img)
    leg_len = y_feet - hip_y
    # Both legs used to leave the SAME point (head_r*0.22 either side of centre),
    # so however wide the splay angle the two strokes shared a root and read as
    # one thick pole. The hips are now a real width apart -- scaled to the
    # figure, not the head -- which is what makes a narrow-stance pose read as
    # a person standing with their feet together rather than a broom handle.
    hip_half = height * 0.055
    knee_y = hip_y + leg_len * 0.52
    for sgn, ang in ((-1, p['ll'][0]), (1, p['rl'][0])):
        a = math.radians(abs(ang))
        fx = cx + sgn * math.sin(a) * leg_len
        kx = cx + sgn * hip_half
        # A knee. Two sticks from hip to foot read as stilts or a broom handle;
        # the break at knee_y is what makes it a leg. The break is small (a few
        # px) but it is a REAL direction change, which is the difference between
        # "two segments" and "a knee" -- memory elbow-existence-is-not-
        # elbow-visibility, same failure one level down.
        kx_out = kx + sgn * math.sin(a) * leg_len * 0.52
        _seg_leg((kx, hip_y), (kx_out, knee_y), seed ^ (0x41 + (0 if sgn < 0 else 7)))
        _seg_leg((kx_out, knee_y), (fx, y_feet), seed ^ (0x52 + (0 if sgn < 0 else 7)))
        # knee joint, same role as the elbow
        kr = lw * 0.55
        d.ellipse([kx_out - kr, knee_y - kr, kx_out + kr, knee_y + kr], fill=ink)
        # foot: a small horizontal blob, wider than it is tall, so the figure
        # has a base instead of ending in a point
        hr = lw * 1.9
        d.ellipse([fx - hr, y_feet - hr * 0.32, fx + hr, y_feet + hr * 0.32],
                  fill=ink)
    # torso: a filled TAPERED TRUNK, not a line. The spine alone left the figure
    # as a coat-hanger -- two arms and two legs on a pole. Shoulders wider than
    # hips gives the silhouette something to hang the arms off, which is what
    # makes the arms read as attached rather than floating.
    sh_half = head_r * 0.72
    hipw = height * 0.042
    torso = [(cx - sh_half, sh_y), (cx + sh_half, sh_y),
             (cx + hipw, hip_y), (cx - hipw, hip_y)]
    if PA is not None and getattr(PA, 'PAINTERLY', False):
        PA.fill_poly(img, torso, ink, seed=seed ^ 0x7C1, value=0.10,
                     tint=3.0, band=3.0, edge=2.0)
    else:
        d.polygon(torso, fill=ink)

    draw_head(img, cx, head_cy, head_r, expression=expression,
              seed=seed, lw=head_lw, face_fill=face_fill)
    return dict(cx=cx, head_r=head_r, head_cy=head_cy, hip_y=hip_y,
                shoulder_y=sh_y)