# work/lib/v2subjects.py -- the recurring SUBJECT drawings for the v2 exoplanet
# cards, composed from work/lib/ink.py primitives on the white v2 page.
#
# These are the things a card needs over and over: a planet (plain, cracked, lava,
# ringed, or tidally split), a star, an orbit path, a comet/atmosphere tail, a
# wind/spectrum bar, a thermometer, a comparison swatch, and the character. Cards
# compose these into layers; the engine (v2engine) times when each pops in.
#
# EVERYTHING here is flat-vector on a near-white page (#fdfdfd) with pure black
# 6px hand-drawn outlines (STYLE_CANON2 §1-2, ink.py defaults). No gradients on
# shapes, no anti-aliased smoothness on linework, deterministic wobble per seed.
#
# The subject-scale rule (CLAUDE.md §7 FRAME-FILL) is the caller's job -- these
# helpers default to a size that reads as the DOMINANT subject, and the frame-fill
# note tells card authors to scale up and crop secondary bodies at a frame edge.

import math

from PIL import Image, ImageDraw

try:
    from . import v2draw as D
    from . import v2type as T
    from . import ink
    from . import v2paint as PA
except ImportError:
    import v2draw as D            # noqa: E402
    import v2type as T            # noqa: E402
    import ink                    # noqa: E402
    import v2paint as PA          # noqa: E402

try:
    from . import stickman as SM
except ImportError:
    import stickman as SM         # noqa: E402


# Marker / planet fill colours (flat, saturated, on white). Chosen to read at a
# glance and to sit beside the yellow/red/blue label palette.
C = {
    'rock':    (168, 158, 148),   # grey-brown rocky world
    'rock_dk': (128, 118, 108),
    'lava':    (214, 92, 48),     # molten
    'lava_dk': (150, 52, 28),
    'ice':     (176, 208, 224),   # frozen
    'gas':     (206, 150, 96),    # banded gas giant base
    'gas_lt':  (232, 186, 132),
    'metal':   (140, 150, 160),   # metallic
    'red':     T.RED,
    'gold':    (222, 168, 66),
    'white':   (252, 252, 252),
    'night':   (58, 60, 72),      # the dark hemisphere
    'day':     (250, 214, 120),   # the lit hemisphere
    'star':    (250, 196, 70),
    'star_hot': (250, 120, 60),
}


# ---------------------------------------------------------------------------
# planets
# ---------------------------------------------------------------------------

def planet(d, cx, cy, r, base='rock', seed=0, width=6, fill=None, rim=False):
    """A plain round planet: flat fill, 6px black outline, gentle hand wobble."""
    col = fill or C.get(base, C['rock'])
    ink.draw_disc(d, cx, cy, r, fill=col, outline=T.INK, width=width,
                  seed=seed, wobble=3.0)
    return (cx - r, cy - r, cx + r, cy + r)


def banded_gas(img, cx, cy, r, seed=0, width=6, base='gas'):
    """A gas giant: flat base disc + hand-painted horizontal bands + the 6px outline.

    PAINTERLY (round-2 critic): the first pass drew the bands as `bd.rectangle`
    with hard horizontal edges, which is the single most vector-looking thing a
    gas giant can do -- it reads as a barcode. The bands now have SMOOTHLY WANDERING
    boundaries (a smooth random walk, i.e. a hand-dragged brush edge) and are
    composited at partial alpha so they blend into the base instead of sitting on
    it. The whole disc is clipped by a painterly-edged mask so the silhouette
    matches ink.draw_disc's, and the outline goes on top last.
    """
    import numpy as np
    col = C.get(base, C['gas'])
    lt = C.get(base + '_lt', C['gas_lt'])
    side = int(2 * r) + 8
    d0 = ImageDraw.Draw(img)
    ink.draw_disc(d0, cx, cy, r, fill=col, outline=None, width=0, seed=seed,
                  wobble=3.0)

    # Band boundaries: a smooth wander down the disc. `walk` is low-frequency by
    # construction, so each edge drifts rather than wobbles per-pixel.
    n_bands = max(3, int(r / 26))
    edges = np.linspace(-1.0, 1.0, n_bands + 1) * r          # -r .. +r in disc space
    band_img = Image.new('RGBA', (side, side), col + (255,))
    bd = ImageDraw.Draw(band_img)
    for i in range(n_bands):
        walk = PA.smooth_walk(side, seed=seed ^ (0xB4D + i * 7919), cells=3,
                              octaves=2)
        amp = r * 0.075
        top = edges[i] + 4 + walk * amp
        bot = edges[i + 1] + 4 + walk * amp
        # Colour-emphasise a subset so it does not rule perfectly even.
        if i % 2 == 0:
            bcol = lt
        else:
            bcol = tuple(int(c * 0.88) for c in col)
        poly = []
        for x in range(side):
            poly.append((x, 4 + r + top[x]))
        for x in range(side - 1, -1, -1):
            poly.append((x, 4 + r + bot[x]))
        # ~78% alpha: the band reads as paint over paint, not as a solid stripe.
        PA.fill_poly(band_img, poly, bcol, seed=seed ^ (0xB4D + i),
                     value=0.085, edge=0.0)

    # Clip to the disc with a soft, painterly-edged mask so the outer silhouette
    # is the same hand-drawn circle the outline traces.
    mask = Image.new('L', (side, side), 0)
    ImageDraw.Draw(mask).polygon(
        PA.wobble_edge(PA.ellipse_pts(4 + r, 4 + r, r, r, n=40), seed=seed,
                       amount=max(0.8, r * 0.012), wavelength=r * 1.5),
        fill=255)
    img.paste(band_img, (int(cx - r) - 4, int(cy - r) - 4), mask)
    # re-outline on top
    d = ImageDraw.Draw(img)
    ink.draw_disc(d, cx, cy, r, fill=None, outline=T.INK, width=width,
                  seed=seed, wobble=3.0)
    return (cx - r, cy - r, cx + r, cy + r)


def terminator_curve(cx, cy, r, a, seed=0, amp_frac=0.075, n=49):
    """The day/night dividing curve for a terminator at angle `a` (the light
    direction), as a centre->rim polyline bowed off-axis by a smooth wander.

    ROUND 3. This used to be two exact radii sharing a common centre, i.e. a
    ruled line through the middle of the disc -- a pie chart, and the loudest
    remaining vector tell once the fills had texture. It is now a curve, and it
    lives here rather than inline in split_planet so there is exactly one
    implementation to keep honest.

    Tapers to zero at the centre and at the rim so the two halves still meet.
    """
    nx, ny = -math.sin(a), math.cos(a)
    AMP = r * amp_frac
    walk = PA.smooth_walk(n, seed=seed ^ 0x3A7, cells=6, octaves=2)
    out = []
    for i in range(n):
        u = i / float(n - 1)
        tp = math.sin(math.pi * u) ** 0.8
        off = AMP * tp * float(walk[i])
        out.append((cx - nx * r * (2.0 * u - 1.0) + nx * off,
                    cy - ny * r * (2.0 * u - 1.0) + ny * off))
    return out


def crescent_light(d, cx, cy, r, a0_deg, a1_deg, colour, seed=0,
                   thickness=0.34, edge=2.2):
    """A lit crescent hugging one edge of a dark disc, with a BOWED inner edge.

    ROUND 3. The hook card drew this as `d.polygon([centre] + arc_points)`,
    which is a pie wedge: two exact straight radii plus a circular arc. On the
    near-black hook planet that rendered as a hard-edged flat yellow slice
    running from the centre of the disc out to the rim -- a quarter of the
    planet lit, which is also the wrong astronomy for a "thin crescent".

    A crescent is a LENS: the rim arc out, and a second arc back that bows
    INWARD from the chord, so the lit region is a thin sliver hugging the edge.
    That is what this builds. The inner arc is the rim arc scaled toward the
    wedge's mid-radius by `1 - thickness` and then displaced by a low-frequency
    seeded walk (which is what makes the sliver's inner boundary wander like a
    brush instead of ruling a second circle concentric with the first).

    `thickness` is the sliver's depth as a fraction of the radius at the wedge's
    middle; 0.34 of a 225px radius is a ~75px crescent.
    """
    img = PA.img_of(d)
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    n = 40
    rim = []
    inner = []
    walk = PA.smooth_walk(n + 1, seed=seed ^ 0x2E, cells=4, octaves=2)
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / float(n)
        rim.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        # inner arc: a smaller circle sharing the same wedge, bowed off-axis
        rr = r * (1.0 - thickness)
        # displacement is perpendicular to the radius, tapering to 0 at both
        # ends of the sliver so the two arcs meet cleanly
        taper = math.sin(math.pi * i / float(n)) ** 0.8
        off = r * 0.10 * taper * float(walk[i])
        rad = rr + off
        inner.append((cx + rad * math.cos(t), cy + rad * math.sin(t)))
    poly = rim + list(reversed(inner))
    PA.fill_poly(img, poly, colour, seed=seed ^ 0x2E, edge=edge)
    return poly


def split_planet(d, cx, cy, r, light_frac=0.5, light_dir=(1, 0), seed=0,
                 width=6, day='day', night='night'):
    """A tidally-locked planet: one lit hemisphere, one dark, hard terminator.

    The lit half is filled `day`, the dark half `night`, split by a terminator
    through the centre perpendicular to light_dir. Outline on top.
    `d` is an ImageDraw bound to the page.

    BOTH halves are drawn as half-disc POLYGONS. (The first pass filled a
    full-square of `night` then overlaid the lit half, which left the four
    corners of the bounding box dark grey -- the planet read as sitting on a
    dark card, exactly the wrong register for a white-page scene.)

    ROUND 3 -- THE TERMINATOR IS BOWED, NOT STRAIGHT. Both halves used to be
    pie wedges sharing two exact radii, so the boundary was a mathematically
    straight line through the centre and the planet read as a PIE CHART: that
    hard ruled edge was the loudest remaining vector tell on the frame after the
    fill texture was fixed. The dividing radius is now sampled along its length
    and displaced by a low-frequency seeded walk (a few px of drift, tapering to
    zero at the centre and at the rim so the two halves still meet cleanly), and
    the terminator STROKE is drawn along that SAME displaced curve -- so the
    paint edge and the ink edge are one edge, not two that disagree.
    """
    a = math.atan2(light_dir[1], light_dir[0])
    img = PA.img_of(d)

    # The terminator curve: centre -> rim, bowed off-axis by a smooth wander.
    # Shared with crescent_light so both "lit side" devices bow the same way.
    term = terminator_curve(cx, cy, r, a, seed=seed, amp_frac=0.075, n=49)

    # Build each half by walking the disc arc on one side and returning along
    # the terminator. `rim_pos` runs the rim from the terminator's +normal end
    # round to its -normal end; `rim_neg` is the mirror half.
    def _rim(sign, n=64):
        """Rim points from the terminator's +normal end, around, to its
        -normal end, on the given side."""
        out = []
        a0, a1 = (a - math.pi / 2, a + math.pi / 2)
        if sign < 0:
            a0, a1 = a + math.pi / 2, a + 3 * math.pi / 2
        for i in range(n + 1):
            t = a0 + (a1 - a0) * i / float(n)
            out.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        return out

    rim_pos = _rim(+1)
    rim_neg = _rim(-1)

    # LIT half: centre -> terminator -> out along the +normal rim, closed.
    lit = [(cx, cy)] + term + list(reversed(rim_pos))
    PA.fill_poly(img, lit, C[day], seed=seed ^ 0x2E, edge=1.8)
    # DARK half: centre -> terminator -> back along the -normal rim.
    dark = [(cx, cy)] + term + rim_neg
    PA.fill_poly(img, dark, C[night], seed=seed ^ 0x1D, edge=1.8)

    # crisp the terminator: stroke the SAME bowed curve the fills were bounded by
    PA.hand_stroke(d, term, T.INK, max(3, width // 2), closed=False, seed=seed ^ 0x3F,
                   vary=0.22, wavelength=r * 0.5)
    ink.draw_disc(d, cx, cy, r, fill=None, outline=T.INK, width=width,
                  seed=seed, wobble=3.0)
    return (cx, cy, r)


def ringed_planet(img, cx, cy, r, ring_w=1.7, seed=0, width=6, base='gas',
                  tilt=0.18, ring_col=None):
    """A planet with a flat elliptical ring around it (back half behind, front
    half overlapping). `img` is the page; we make our own draw for the bands."""
    d = ImageDraw.Draw(img)
    banded_gas(img, cx, cy, r, seed=seed, width=width, base=base)
    rc = ring_col or C['rock']
    rx, ry = r * ring_w, r * ring_w * tilt
    # PAINTERLY: the arcs used to be ImageDraw.arc, which is a mathematically
    # perfect ellipse of exactly constant width -- the most machine-looking stroke
    # in the file. Both ring halves are now sampled and stroked with hand_stroke,
    # so the ring swells and thins and its curve drifts.
    PA.hand_stroke(d, PA.arc_pts(cx, cy, rx, ry, 180, 360, n=56), T.INK, width,
                   closed=False, seed=seed ^ 0x41, wavelength=rx * 0.9)
    PA.hand_stroke(d, PA.arc_pts(cx - 0, cy, rx - width, ry - width * 0.4,
                                 180, 360, n=52), rc, max(2, width - 3),
                   closed=False, seed=seed ^ 0x42, wavelength=rx * 0.9, vary=0.22)
    # front half (below planet) drawn after so it overlaps
    PA.hand_stroke(d, PA.arc_pts(cx, cy, rx, ry, 0, 180, n=56), T.INK, width,
                   closed=False, seed=seed ^ 0x43, wavelength=rx * 0.9)
    PA.hand_stroke(d, PA.arc_pts(cx, cy, rx - width, ry - width * 0.4,
                                 0, 180, n=52), rc, max(2, width - 3),
                   closed=False, seed=seed ^ 0x44, wavelength=rx * 0.9, vary=0.22)
    return (cx, cy, r, rx, ry)


def cracked_rock(d, cx, cy, r, seed=0, width=6, n_crack=7, base='rock_dk'):
    """A bare scorched rock: flat fill + a few jagged crack lines."""
    box = planet(d, cx, cy, r, base=base, seed=seed, width=width)
    rnd = __import__('random').Random(seed ^ 0xC7AC)
    for _ in range(n_crack):
        a0 = rnd.uniform(0, 2 * math.pi)
        rr = r * rnd.uniform(0.1, 0.55)
        x, y = cx + math.cos(a0) * rr, cy + math.sin(a0) * rr
        pts = [(x, y)]
        for _ in range(3):
            x += rnd.uniform(-r * 0.3, r * 0.3)
            y += rnd.uniform(-r * 0.3, r * 0.3)
            pts.append((x, y))
        ink.draw_outline(d, pts, color=T.INK, width=max(2, width - 2),
                         closed=False, seed=rnd.randint(0, 999), wobble=1.5)
    return box


def lava_planet(d, cx, cy, r, seed=0, width=6):
    """A molten world: dark crust with bright lava cracks."""
    d_ = d
    planet(d_, cx, cy, r, base='lava_dk', seed=seed, width=width)
    rnd = __import__('random').Random(seed ^ 0x1A7A)
    for _ in range(8):
        a0 = rnd.uniform(0, 2 * math.pi)
        rr = r * rnd.uniform(0.0, 0.6)
        x, y = cx + math.cos(a0) * rr, cy + math.sin(a0) * rr
        pts = [(x, y)]
        for _ in range(3):
            x += rnd.uniform(-r * 0.28, r * 0.28)
            y += rnd.uniform(-r * 0.28, r * 0.28)
            pts.append((x, y))
        ink.draw_outline(d_, pts, color=C['lava'], width=max(3, width - 1),
                         closed=False, seed=rnd.randint(0, 999), wobble=1.5)
    return (cx - r, cy - r, cx + r, cy + r)


# ---------------------------------------------------------------------------
# stars
# ---------------------------------------------------------------------------

def _ray_pts(cx, cy, base, tip, ca, sa, px, py, hw, seed, n=26, waver=0.10,
             waver_n=3):
    """A densely sampled, hand-wobbled, TAPERED ray outline.

    ROUND 4. The rays used to be a THREE-point triangle handed straight to
    `PA.wobble_edge`. wobble_edge displaces each vertex along its own normal by
    a low-frequency profile evaluated at that vertex's ARC LENGTH -- with only
    three vertices there is no arc to speak of, so the "wobble" was three
    arbitrary corner offsets and the silhouette stayed three straight lines.
    On the star-swell beat that rendered as eight hard-edged black triangles,
    the most vector-like element left anywhere in the segment.

    So the triangle is now RESAMPLED first: both straight edges are walked at `n`
    points and only then does wobble_edge see a path long enough for its profile
    to mean anything. The width profile along the ray is what stops it reading
    as a wedge:

      * it TAPERS -- `hw` at the rim falling to ~12% of that at the tip -- so
        the silhouette is a spike, not a club. (The first attempt held the
        offset at `hw + bow` for the whole length and the rays rendered as fat
        black lumps stuck to the disc; tapering is the whole ball game.)
      * a small BOW (`waver`) displaces the edges sideways, largest mid-length
        and zero at both ends, so the sides are not ruled lines.
      * a low-frequency WANDER rides on top of both, seeded per edge, so the
        two sides of a ray are not mirror images. A flame is not a wedge.

    Returns a closed polygon. Ink only -- no pigment term -- because a ray is a
    solid dark shape and noise fill on solid ink reads as dirt (see the note in
    `star` about value=0.0).
    """
    bx, by = cx + ca * base, cy + sa * base          # base centre on the rim
    tx, ty = cx + ca * tip, cy + sa * tip            # tip
    span = tip - base
    # Two independent wander profiles, one per edge, so the two sides of the
    # ray are not mirror images.
    wa = PA.smooth_walk(n + 1, seed=seed ^ 0x11, cells=3, octaves=2)
    wb = PA.smooth_walk(n + 1, seed=seed ^ 0x12, cells=3, octaves=2)
    out = []
    for wob, sgn in ((wa, 1.0), (wb, -1.0)):
        rng = range(n + 1) if sgn > 0 else range(n, -1, -1)
        for i in rng:
            u = i / float(n)
            # taper: full at the rim, ~5% at the tip, with a slight belly just
            # off the rim so the ray has a shoulder rather than being a plain
            # cone. The exponent is <1 so the width stays near `hw` for most of
            # the length and then falls away fast -- that is what makes the
            # silhouette read as a long spike instead of a stubby lump.
            taper = (1.0 - u) ** 1.15 * (1.0 + 0.12 * math.sin(math.pi * u * 0.8))
            # sideways bow, zero at base and tip, max mid-length
            bow = math.sin(math.pi * u) * span * waver
            off = hw * taper + bow + float(wob[i]) * hw * 0.20 * (1.0 - u)
            out.append((bx + (tx - bx) * u + px * off * sgn,
                        by + (ty - by) * u + py * off * sgn))
    # one more gentle low-frequency edge irregularity on the whole outline
    return PA.wobble_edge(out, seed=seed ^ 0x13, amount=max(0.9, hw * 0.20),
                          wavelength=max(10.0, span * 0.55), closed=True)


def star(d, cx, cy, r, seed=0, width=6, col=None, spikes=8, spike_len=1.86,
         ray_w=2.0):
    """A star: flat disc + radiating rays ATTACHED to the disc edge.

    Rays start just inside the rim (0.88r) so they read as light growing out of
    the star, not as disconnected floating lines. Each ray is a TAPERED triangle
    -- wide at the rim, pointed at the tip -- because a constant-width hairline
    reads as a stray pen stroke next to a 6px keyline disc, which is exactly how
    the first pass looked. `ray_w` is the rim half-width as a multiple of `width`.

    ROUND 4: the ray outline is now built by `_ray_pts` (densely resampled and
    bowed) rather than as a bare 3-point triangle, so the rays read as painted
    flame instead of as hard vector wedges. See that function for why the
    3-point version could not be rescued by wobble_edge alone.
    """
    col = col or C['star']
    ink.draw_disc(d, cx, cy, r, fill=col, outline=T.INK, width=width,
                  seed=seed, wobble=2.5)
    base = r * 0.88
    hw = max(4.0, width * ray_w)
    tip = r * spike_len
    img = PA.img_of(d)
    for i in range(spikes):
        a = 2 * math.pi * i / spikes
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa, ca                        # perpendicular to the ray
        # The tips vary in length by hand (+-9%), which is what stops eight
        # identical copies reading as a stencil.
        jl = 1.0 + 0.09 * math.sin(i * 2.399 + seed)
        # The base half-width also varies a little, and the two sides of a ray
        # are not mirror images -- a flame is not a wedge.
        hwj = hw * (1.0 + 0.10 * math.sin(i * 1.771 + seed * 0.7))
        ray = _ray_pts(cx, cy, base, tip * jl, ca, sa, px, py, hwj,
                       seed=seed ^ (0xC0 + i))
        PA.fill_poly(img, ray, T.INK, value=0.0, tint=0.0, band=0.0, edge=0.0)
    return (cx - tip, cy - tip, cx + tip, cy + tip)


def sun_rays(d, cx, cy, r, seed=0, width=6, col=None, n=12, inner=1.2, outer=2.0):
    """A hotter star with longer alternating rays."""
    return star(d, cx, cy, r, seed=seed, width=width, col=col or C['star_hot'],
                spikes=n, spike_len=outer, ray_w=2.4)


def pulsar(d, cx, cy, r=70, seed=0, beams=2, beam_len=520, beam_half=26,
           col=None, blur=True):
    """A pulsar: a small hard point with two beams sweeping out of its poles.

    Deliberately NOT drawn with `star()`: a pulsar is a neutron star, so it is
    tiny and blindingly bright, not a big disc with rays. The first pass used a
    normal star, which made the segment read as "another star segment" and lost
    the whole point of the subject.

    `beams` is 2 (the poles) or 4. Each beam is a tapered wedge -- wide at the
    source, spread at the tip -- because a constant-width bar reads as a fence
    post rather than a beam of light. With `blur`, concentric halo rings sit
    under the point to sell the "smear of light" idea.
    """
    col = col or T.INK
    hw0 = max(5.0, r * 0.22)
    img = PA.img_of(d)
    for i in range(beams):
        if beams == 2:
            a = math.pi / 2 + i * math.pi          # two OPPOSITE beams
        else:
            a = math.pi * i / 2.0                  # four cardinal beams
        ca, sa = math.cos(a), math.sin(a)
        tip = r + beam_len
        spread = beam_half
        wedge = [
            (cx + ca * r * 0.6 - sa * hw0, cy + sa * r * 0.6 + ca * hw0),
            (cx + ca * tip - sa * spread, cy + sa * tip + ca * spread),
            (cx + ca * tip + sa * spread, cy + sa * tip - ca * spread),
            (cx + ca * r * 0.6 + sa * hw0, cy + sa * r * 0.6 - ca * hw0),
        ]
        # painterly edge on the beam so it does not read as a fence post
        PA.fill_poly(img, PA.wobble_edge(wedge, seed=seed ^ (0xBE + i),
                                         amount=3.0, wavelength=beam_len * 0.5),
                     col, value=0.0, tint=0.0, band=0.0, edge=0.0)
    if blur:
        for k, rr in enumerate([r * 2.0, r * 3.1, r * 4.2]):
            PA.hand_stroke(d, PA.ellipse_pts(cx, cy, rr, rr, n=72), col,
                           max(3, int(r * 0.10) - k), closed=True,
                           seed=seed ^ (0xBA0 + k), vary=0.34)
    ink.draw_disc(d, cx, cy, r, fill=col, outline=T.INK, width=6, seed=seed,
                  wobble=1.5)
    # Bright core: the point is a neutron star, blindingly bright. On a white
    # page that reads as a small white hole punched in the black disc, so the
    # subject still looks like a light source rather than a dark ball. (The
    # first pass drew the whole subject in white and it vanished into the page.)
    cr = max(3.0, r * 0.34)
    ink.draw_disc(d, cx, cy, cr, fill=C['white'], outline=None, width=0,
                  seed=seed + 1, wobble=0.6)
    return (cx - r - beam_len, cy - r - beam_len, cx + r + beam_len, cy + r + beam_len)


# ---------------------------------------------------------------------------
# orbits, paths, atmospheres
# ---------------------------------------------------------------------------

def orbit_path(d, cx, cy, rx, ry, seed=0, width=5, tilt=0.0, dashed=False):
    """A hand-drawn elliptical orbit. Optional tilt shears it for a 3/4 view."""
    pts = []
    for i in range(49):
        t = 2 * math.pi * i / 48
        x, y = rx * math.cos(t), ry * math.sin(t)
        # shear for tilt
        y += x * math.tan(tilt)
        pts.append((cx + x, cy + y))
    ink.draw_outline(d, pts, color=T.INK, width=width, closed=True, seed=seed,
                     wobble=3.0)


def atmosphere_tail(d, cx, cy, r, length, seed=0, width=5, col=None,
                    direction=(1, 0), spread=0.7, anchor_frac=0.68,
                    clear_radius=0.0):
    """A glowing atmosphere streaming off a planet as a widening, softening plume.

    `anchor_frac`  where the plume's axis BEGINS, as a fraction of `r` measured
                   from the centre. The historical value is 0.68, which starts
                   the plume INSIDE the body.
    `clear_radius` a radius, as a fraction of `r`, inside which the plume's alpha
                   is forced to ZERO. See ROUND 5 below.

    ROUND 3 replaced a single flat wedge with a slender streamer plus internal
    strands. On the TRES-2b finale even that rendered as a LITERAL ARROW, and
    this doc records why, because all four of the things that make an arrowhead
    were present at once:

      * it CONVERGED TO A POINT. The half-width was `r*SPREAD*(1-s)^0.8`, so at
        s=1 both edges met at one coordinate and the silhouette was a wedge tip.
        Gas leaving a planet does not converge; it spreads and dissipates.
      * it carried a HARD BLACK OUTLINE. `ink.draw_outline` ran along both
        boundary curves all the way to the tip, so two ruled lines met at a
        vertex. That vertex IS the arrowhead, and it was the single loudest
        vector tell on the frame.
      * the interior was ONE OPAQUE FIELD. No layering, no thinning, no fade.
      * the internal strands were constant-weight `hand_stroke` running the
        length of the axis -- the fletching on an arrow.

    What it is now:

      * The plume WIDENS through the first third (the bow shock leaving the
        limb) and only then tapers, and it never reaches a point: a per-pixel
        axial alpha falloff dissolves the far end instead. The silhouette is a
        soft lens, not a wedge.
      * There is NO ink outline anywhere. The edges are defined by the pigment
        running out, which is what a diffuse gas boundary looks like.
      * The body is three overlapping translucent lobes at different widths and
        alphas, so there is depth and the plume is not one flat shape.
      * The internal structure is thirteen short, seeded, wandering wisp
        strokes of varying weight that break up along their length, so they
        read as eddies rather than as lines.

    Drawn on its own RGBA layer per lobe and composited, so the falloff can be
    applied in alpha rather than by fading toward an arbitrary background
    colour (which is what a per-pixel multiply toward PAGE would have done --
    wrong the moment this is used on a dark card).

    ROUND 5 -- THE PLUME MUST NOT BLANKET THE BODY IT LEAVES.
    The alpha profile above is a function of the AXIAL station only. It has no
    term that knows where the body is, so a plume whose axis is anchored inside
    the disc (anchor_frac=0.68, the historical default) is already at full
    alpha by the time it reaches the limb: `fade_in` reaches 1.0 at u_ax=0.18,
    which for a 330px run is 59px past a start point already 153px in -- 212px
    from centre on a 225px disc, i.e. 13px INSIDE the rim. Combined with three
    stacked lobes the plume reached ~76% composite alpha over the body, and on
    TRES-2b (where the tail element is drawn after the star, so it composites on
    top) it measured 97.2% coverage of the star's inner disc at alpha 1.0. The
    star's disc was completely gone and all that survived was its black rays,
    which read as a yellow blob stuck on a sun.

    Two changes, both about WHERE the plume is allowed to paint:

      * `anchor_frac` now places the axis start. At 1.0 the plume begins exactly
        at the limb, so the widening bow-shock lobe (which is the widest thing
        in the plume) is outside the body instead of across it.
      * `clear_radius` is a hard guarantee rather than a tuning. Every pixel
        whose distance from (cx, cy) is below `clear_radius * r` gets its alpha
        multiplied to zero, whatever the axial profile says. That is what makes
        the fix measurable: the disc coverage is now structurally 0, not merely
        small, and it cannot drift back if the falloff constants are ever
        re-tuned. The mask edge is feathered over 6% of r so the plume does not
        begin on a hard circular cut.
    """
    import numpy as np

    col = col or C['gold']
    a = math.atan2(direction[1], direction[0])
    tx, ty = math.cos(a), math.sin(a)
    px, py = -ty, tx                       # perpendicular
    img = PA.img_of(d)
    SPREAD = spread * 0.42
    n = 40
    BOW = 0.30                             # fraction of the run spent widening
    ANCH = r * anchor_frac                 # where the axis leaves the centre

    def _halfwidth(s, wid):
        """The plume's half-width at normalised station `s`, scaled by lobe
        factor `wid`. Widens to full over BOW, then tapers -- and never quite
        reaches zero, because the ALPHA is what ends the plume, not the
        geometry. A shape that thins to a point is an arrow; a shape that
        thins while fading out is a gas."""
        widen = min(1.0, s / BOW)
        prof = (0.35 + 0.65 * widen) * (1.0 - s) ** 0.55
        return r * SPREAD * wid * prof + 2.0

    layers = []
    # back to front: broad and faint, then mid, then a narrow bright core
    for so, wid, af, colr in (
            (0x00, 1.62, 0.22, tuple(max(0, c - 34) for c in col)),
            (0x40, 1.02, 0.36, col),
            (0x80, 0.50, 0.52, tuple(min(255, c + 30) for c in col))):
        wl_t = PA.smooth_walk(n + 1, seed=seed ^ (0x51 + so), cells=4,
                              octaves=2)
        wl_b = PA.smooth_walk(n + 1, seed=seed ^ (0x52 + so), cells=4,
                              octaves=2)
        # A SHARED low-frequency drift on both boundaries. Without it the two
        # edges are independent, which is statistically symmetric and reads as
        # a vector almond; with it the plume leans and bellies like one body of
        # gas. This is the plume analogue of the hand-wobble rules.
        wl_s = PA.smooth_walk(n + 1, seed=seed ^ (0x53 + so), cells=2,
                              octaves=1)
        top, bot = [], []
        for i in range(n + 1):
            s = i / float(n)
            w = _halfwidth(s, wid)
            # the wander shrinks toward the tip, where the plume is dissolving
            j = (1.0 - s * 0.6) * r * 0.13
            drift = float(wl_s[i]) * r * 0.10 * math.sin(math.pi * s)
            bx = cx + tx * (ANCH + length * s)
            by = cy + ty * (ANCH + length * s)
            top.append((bx + px * (w + drift + float(wl_t[i]) * j),
                        by + py * (w + drift + float(wl_t[i]) * j)))
            bot.append((bx - px * (w + drift + float(wl_b[i]) * j),
                        by - py * (w + drift + float(wl_b[i]) * j)))
        layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        PA.fill_poly(layer, top + bot[::-1], colr, seed=seed ^ (0xA7 + so),
                     edge=2.2, value=0.10)
        layers.append([layer, af, wid])

    # --- the wisps: short wandering eddies, not ruled lines -----------------
    # Into the MID lobe, so they composite with it at its alpha.
    mid = layers[1]
    wd = ImageDraw.Draw(mid[0])
    n_wisp = 13
    for k in range(n_wisp):
        u0 = (k + 0.5) / n_wisp
        seg = 0.30 + 0.34 * (0.5 + 0.5 * math.sin(k * 2.399 + seed))
        wlen = 14
        wwalk = PA.smooth_walk(wlen, seed=seed ^ (0xE1 + k * 131), cells=4,
                               octaves=2)
        # lane position across the plume, in half-widths, scattered not ruled
        lane = (((k * 0.618) % 1.0) - 0.5) * 1.7
        pts = []
        for i in range(wlen):
            u = u0 + seg * (i / float(wlen - 1))
            if u > 1.0:
                break
            wpx = _halfwidth(u, 1.0)
            off = lane * wpx + float(wwalk[i]) * r * 0.055
            bx = cx + tx * (ANCH + length * u)
            by = cy + ty * (ANCH + length * u)
            pts.append((bx + px * off, by + py * off))
        if len(pts) >= 2:
            lcol = tuple(min(255, c + 40) for c in col)
            PA.hand_stroke(wd, pts, lcol, max(2, int(r * 0.024)),
                           closed=False, seed=seed ^ (0xC0 + k),
                           wavelength=max(14.0, length * 0.22), vary=0.44)

    # --- alpha shaping: fade in off the limb, dissolve at the far end, and
    # --- soften the lateral boundary so the plume has no hard silhouette edge
    yy, xx = np.mgrid[0:img.size[1], 0:img.size[0]].astype(np.float32)
    u_ax = (((xx - cx) * tx + (yy - cy) * ty) - ANCH) / max(1.0, length)
    u_perp = (xx - cx) * px + (yy - cy) * py

    fade_in = np.clip((u_ax - 0.02) / 0.16, 0.0, 1.0)
    # The dissolve used to start at u=0.64, which left the plume near-opaque
    # for the first half of its run -- a solid painted object rather than gas.
    # Starting it at u=0.24 means the plume is visibly thinning for most of its
    # length and never has a body.
    t = np.clip((1.02 - u_ax) / 0.78, 0.0, 1.0)
    fade_out = t * t * (3.0 - 2.0 * t)
    fall = fade_in * fade_out

    # ROUND 5 -- the hard body-clear guarantee. See the docstring: the axial
    # profile alone cannot know where the body is, so on its own it lets the
    # plume reach full alpha before it even reaches the limb. Everything inside
    # `clear_radius * r` of the centre is forced to zero alpha, feathered over
    # the last 6% of r so the plume does not begin on a visible circular cut.
    # With clear_radius=0.0 (the default, and what every pre-round-5 caller
    # gets) this multiplies by 1.0 everywhere and changes nothing at all.
    if clear_radius > 0.0:
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        rc = clear_radius * r
        feather = max(1e-3, 0.06 * r)
        keep = np.clip((dist - rc) / feather, 0.0, 1.0)
        fall = fall * (keep * keep * (3.0 - 2.0 * keep))

    def _hw_vec(wid):
        widen = np.clip(u_ax / BOW, 0.0, 1.0)
        prof = (0.35 + 0.65 * widen) * np.clip(1.0 - u_ax, 0.0, 1.0) ** 0.55
        return r * SPREAD * wid * prof + 2.0

    for layer, af, wid in layers:
        # lateral softening over the outer third of the half-width
        lat = np.clip(1.0 - np.abs(u_perp) / _hw_vec(wid), 0.0, 1.0)
        lat = lat * lat * (3.0 - 2.0 * lat)
        arr = np.asarray(layer).astype(np.float32)
        arr[..., 3] *= np.clip(fall * lat * af, 0.0, 1.0) * 255.0
        img.alpha_composite(Image.fromarray(
            np.clip(arr, 0, 255).astype(np.uint8), mode='RGBA'))


def star_close_and_planet(d, sx, sy, sr, px, py, pr, orbit_rx, orbit_ry, seed=0):
    """A star with a planet on a close orbit -- the 'day/night' setup."""
    star(d, sx, sy, sr, seed=seed)
    orbit_path(d, (sx + px) / 2, (sy + py) / 2, orbit_rx, orbit_ry, seed=seed + 1)
    planet(d, px, py, pr, base='rock', seed=seed + 2)


# ---------------------------------------------------------------------------
# diagram props (thermometer, gauge, bar, swatch)
# ---------------------------------------------------------------------------

def thermometer(d, x, y_bottom, height, level, seed=0, width=6, hot=True):
    """A vertical thermometer. level in 0..1 fills the tube."""
    bulb_r = 22
    tube_w = 20
    top = y_bottom - height
    img = PA.img_of(d)
    # tube (rounded rect via polygon so it takes the painterly fill)
    tube = PA.round_rect_pts(x - tube_w // 2, top, x + tube_w // 2, y_bottom,
                             tube_w // 2)
    PA.fill_poly(img, tube, T.PAPER, seed=seed ^ 0x61, edge=0.8)
    PA.hand_stroke(d, tube, T.INK, width, closed=True, seed=seed ^ 0x62)
    # bulb
    bulb = PA.ellipse_pts(x, y_bottom + bulb_r // 2, bulb_r, bulb_r * 3 // 4,
                          n=40)
    PA.fill_poly(img, bulb, T.PAPER, seed=seed ^ 0x63, edge=0.8)
    PA.hand_stroke(d, bulb, T.INK, width, closed=True, seed=seed ^ 0x64)
    # fill
    fh = height * max(0.0, min(1.0, level))
    col = C['red'] if hot else C['star']
    mercury = PA.round_rect_pts(x - (tube_w - 8) // 2, y_bottom - fh,
                                x + (tube_w - 8) // 2, y_bottom,
                                (tube_w - 8) // 2)
    PA.fill_poly(img, mercury, col, seed=seed ^ 0x65, edge=0.6)
    PA.fill_poly(img, PA.ellipse_pts(x, y_bottom + bulb_r // 2,
                                     bulb_r - 6, (bulb_r - 6) * 3 // 4, n=36),
                 col, seed=seed ^ 0x66, edge=0.6)
    return (x - bulb_r, top, x + bulb_r, y_bottom + bulb_r)


def gauge(img, cx, cy, r, frac, seed=0, width=6, label=None):
    """A circular fuel/state gauge. frac 0..1 fills clockwise from the left."""
    d = ImageDraw.Draw(img)
    ink.draw_disc(d, cx, cy, r, fill=T.PAPER, outline=T.INK, width=width,
                  seed=seed, wobble=2.0)
    if frac > 0:
        # PAINTERLY: pieslice -> wedge polygon, so the fill carries pigment.
        PA.fill_poly(img, PA.pie_pts(cx, cy, r - 8, 180,
                                     180 + 360 * min(1.0, frac)),
                     C['gold'], seed=seed ^ 0x71, edge=1.4)
    # re-outline so the fill never eats the rim
    ink.draw_disc(d, cx, cy, r, fill=None, outline=T.INK, width=width,
                  seed=seed, wobble=2.0)
    if label:
        D.draw_label(img, label, center=(cx, cy), color=T.INK, size=T.LABEL_SM_PX)


def bar(d, x0, y0, x1, y1, frac, seed=0, width=6, fill=None, segments=1):
    """A horizontal bar (wind / spectrum / intensity). Optionally segmented."""
    col = fill or C['star']
    img = PA.img_of(d)
    PA.fill_rect(img, [x0, y0, x1, y1], T.PAPER, seed=seed ^ 0x81, edge=0.8)
    PA.hand_stroke(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], T.INK, width,
                   closed=True, seed=seed ^ 0x82, vary=0.26)
    fw = (x1 - x0 - 2 * width) * max(0.0, min(1.0, frac))
    if fw > 0:
        if segments <= 1:
            PA.fill_rect(img, [x0 + width, y0 + width, x0 + width + fw, y1 - width],
                         col, seed=seed ^ 0x83, edge=0.6)
        else:
            sw = fw / segments
            for i in range(segments):
                PA.fill_rect(img, [x0 + width + i * sw + 2, y0 + width,
                                   x0 + width + (i + 1) * sw - 2, y1 - width],
                             col, seed=seed ^ (0x83 + i), edge=0.6)
    return (x0, y0, x1, y1)


def swatch(img, x0, y0, w, h, col, seed=0, width=6, label=None, label_below=True):
    """A flat comparison swatch (coal, asphalt, a planet, ...)."""
    d = ImageDraw.Draw(img)
    PA.fill_rect(img, [x0, y0, x0 + w, y0 + h], col, seed=seed, edge=1.0)
    PA.hand_stroke(d, [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
                   T.INK, width, closed=True, seed=seed ^ 0x91, vary=0.28)
    if label:
        ly = y0 + h + 6 if label_below else y0 - 30
        D.draw_label(img, label, center=(x0 + w // 2, ly + 10), color=T.INK,
                     size=T.LABEL_SM_PX)
    return (x0, y0, x0 + w, y0 + h)


# ---------------------------------------------------------------------------
# the character
# ---------------------------------------------------------------------------

def character(img, x_center, foot_y, height, expression='flat', pose='standing',
              seed=0):
    """Our stickman, ink-on-white (theme='light'), feet at foot_y.

    The reference shows its figure very large (40-50% of frame height); callers
    pass height in that range. expression in MOUTHS, pose in POSES.
    """
    y_top = foot_y - height
    SM.draw_stickman(img, x_center, y_top, height, pose=pose, mouth=expression,
                     seed=seed, theme='light', ground_y=None)


def character_closeup(img, cx, cy, height, expression='flat', seed=0):
    """A big head-and-shoulders character (the bar's reaction close-up)."""
    y_top = cy - height // 2
    character(img, cx, y_top + height, height, expression=expression,
              pose='standing', seed=seed)


# ---------------------------------------------------------------------------
# composition helpers
# ---------------------------------------------------------------------------

def subject_scale_hint(r, frame_w=1280, frame_h=720):
    """FRAME-FILL: a dominant subject should be a real share of the frame.

    Returns a suggested radius so the subject reads as the subject, not a prop.
    The rule (CLAUDE.md §7) is that subjects under ~1/5 frame width read as
    timid; aim for the subject to span a third to half the frame.
    """
    return max(r, int(min(frame_w, frame_h) * 0.22))
