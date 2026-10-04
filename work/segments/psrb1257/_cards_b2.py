# _cards_b2.py — B2 THE PULSAR, 7 cards for segment 3 (PSR B1257+12).
#
# Register discipline (the #1 critic complaint, per PALETTE_SPEC.md §3):
#   - a radial gradient is legal ONLY on the pulsar CORE, and only on the cards
#     the beat's gradient_rule names: psr_size, psr_collapse, psr_beams,
#     psr_name. psr_spin and psr_rate draw their core FLAT.
#   - no gradient on the debris, the streaks, the rings, the arcs, the beams'
#     surroundings, the starfield, the strip, or the character.
#   - nothing in this file imports numpy (lib/texture.py does, and the brief
#     forbids numpy paths) — the core ramp is lib/cardframe._radial_core, the
#     grain is deterministic scatter.
#
# Soft-edge discipline (the round-N art fix): every light wash, beam cone and
# halo contour goes through _soft_wash / _soft_strobe, whose alpha field falls
# to zero BEFORE the geometry does. Nothing here paints a filled triangle or a
# crisp rectangle and calls it light.
#
# Every wobble/stipple/starfield call takes an explicit seed. No global random.

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

# work/ has to be importable as the `lib` package. The frame generator normally
# puts it there; this makes the module runnable standalone for the self-check
# without any other import-time behaviour (no rendering, no global state).
_WORK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _WORK not in sys.path:
    sys.path.insert(0, _WORK)

import lib.type as T          # noqa: E402
import lib.ink as K           # noqa: E402
import lib.cardframe as C     # noqa: E402

INK = C.PAL['ink']
PAPER = C.PAL['paper']
DEEP = C.PAL['deep']
AMBER = C.PAL['amber']
BONE = C.PAL['bone']
VIOLET = C.PAL['violet']

# #FFFFFF -> #DCE6EC -> #6E5A9C, verbatim from PALETTE_SPEC.md §3.
CORE_STOPS = [(255, 255, 255), BONE, VIOLET]

# The magnetic axis is tilted 30 deg off vertical on EVERY card in this beat, so
# the spin arcs, the beam cones and the beam cones' halo all agree.
AXIS_DEG = 30.0                 # tilt of the pole axis from +y
N_POLE = math.radians(AXIS_DEG - 90.0)   # direction of the north beam
S_POLE = N_POLE + math.pi

# The bottom of every hero phrase in this beat. The floating caption sits at
# y=652, so nothing dominant is allowed to reach past this.
HERO_Y_MAX = 620


# ---------------------------------------------------------------------------
# small local helpers (all deterministic, all PIL-only)
# ---------------------------------------------------------------------------

def _lerp(a, b, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def _alpha(c, a):
    return (c[0], c[1], c[2], int(a))


def _core(img, cx, cy, r, seed=0, gradient=True,
          flat=(246, 249, 252), grain=(210, 222, 232)):
    """The pulsar. gradient=True -> the segment's one legal radial ramp.
    gradient=False -> a flat disc (use on the cards the gradient_rule omits).
    Either way it carries a deterministic spray grain inside the limb."""
    if gradient:
        C._radial_core(img, cx, cy, r, CORE_STOPS)
    else:
        ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], fill=flat)
    rnd = random.Random(seed)
    n = int(math.pi * r * r * 0.05)
    px = img.load()
    for _ in range(n):
        a = rnd.uniform(0.0, math.tau)
        rr = r * 0.92 * math.sqrt(rnd.random())
        x, y = int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a))
        px[x, y] = grain if rnd.random() < 0.55 else (255, 255, 255)
    return img


def _halo(img, cx, cy, rings, colour):
    """Soft concentric halo rings (no gradient) — magnet violet on a void card.
    Each ring is stroked through _soft_stroke, so the ring's own edge fades into
    the field instead of sitting on it as a hard CAD circle.
    rings: [(radius, alpha, width), ...] outer-first so the inner one lands on top.

    _soft_stroke returns a NEW image (RGBA compositing is not in-place), and this
    helper has always been called for side effects, so it composites each ring
    back onto the caller's own image object via paste. That keeps every existing
    `_halo(img, ...)` call correct without each one having to rebind `img`."""
    for r, a, w in rings:
        pts = [(cx + r * math.cos(math.tau * i / 28),
                cy + r * math.sin(math.tau * i / 28)) for i in range(29)]
        ring = _soft_stroke(img, pts, colour, w, seed=1400 + r, wobble=1.8,
                            wavelength=300.0, alpha=a, blur=3)
        img.paste(ring, (0, 0))          # in-place; ring is same size as img
    return img


def _circle_pts(cx, cy, r, n=24, phase=0.0):
    return [(cx + r * math.cos(phase + math.tau * i / n),
             cy + r * math.sin(phase + math.tau * i / n)) for i in range(n)]


def _arc_pts(cx, cy, r, a0, a1, n=15):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)),
             cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def _text_w(text, size, bold=True):
    bb = T.load_font(size, bold=bold).getbbox(text)
    return bb[2] - bb[0], bb


def _stamp_centred(d, text, cx, y_top, colour, ink_rgb=INK):
    """An 18pt-class tiny annotation, centred on cx, via the locked stamp style."""
    w, bb = _text_w(text, T.STAMP_PX, bold=False)
    T.draw_stamp(d, text, (cx - w // 2 - bb[0], y_top), colour, ink_rgb=ink_rgb)
    return w


def _wobbly_arc(d, cx, cy, r, a0, a1, colour, width, seed, wobble=4.0, wl=220.0):
    _stroke_open(d, _arc_pts(cx, cy, r, a0, a1), colour, width, seed=seed,
                 wobble=wobble, wavelength=wl)


def _catmull_open(p, samples=12):
    """Catmull-Rom through an OPEN polyline.

    lib/ink.py's K._smooth_open indexes ext[len(p)+2] on a list of len(p)+2 and
    so raises on every open curve, which makes K.draw_outline(closed=False)
    unusable. The libs are read-only for this beat, so the same spline (same
    control math as K.smooth_closed) is reproduced here and the open strokes go
    through _stroke_open. Line quality is unchanged: the displacement still comes
    from K.wobble_points, i.e. low-frequency hand wobble, not vertex jitter.
    """
    p = list(p)
    if len(p) < 4:
        p = [p[0]] + p + [p[-1], p[-1]] if p else p
    ext = [p[0]] + p + [p[-1], p[-1]]
    out = []
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(p[-1])
    return out


def _stroke_open(d, pts, colour, width, seed=0, wobble=2.0, wavelength=200.0):
    """A hand-wobbled OPEN stroke (streaks, cone edges, arc sweeps)."""
    w = K.wobble_points(pts, seed=seed, amount=wobble, wavelength=wavelength)
    d.line(_catmull_open(w), fill=colour, width=width, joint='curve')


def _soft_stroke(img, pts, colour, width, seed=0, wobble=2.4, wavelength=220.0,
                 alpha=170, blur=3):
    """A hand-wobbled open stroke composited THROUGH a blur.

    The line quality is identical to _stroke_open — the wobble is lib/ink's
    low-frequency hand wobble, not vertex jitter — but it lands on the card as a
    soft painterly line rather than a crisp vector edge. This is what the beam
    contours and the halo rings use: a hard stroke on a light wash is exactly
    the "hard-edged geometric primitive" the brief forbids.
    """
    pad = int(wobble) + int(width) + blur + 4
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    bx0, by0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    bw = int(math.ceil(max(xs))) - bx0 + pad
    bh = int(math.ceil(max(ys))) - by0 + pad
    if bw < 2 or bh < 2:
        return img
    layer = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    _stroke_open(ImageDraw.Draw(layer), [(x - bx0, y - by0) for x, y in pts],
                 _alpha(colour, alpha), width, seed=seed, wobble=wobble,
                 wavelength=wavelength)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base = img.convert('RGBA')
    base.alpha_composite(layer, dest=(bx0, by0))
    return base.convert('RGB')


def _soft_wash(img, apex, ang, length, half_deg=13.0, colour=AMBER, peak=150,
               along=1.15, across=1.7, ss=4):
    """One translucent light wash with NO hard edge.

    The alpha field is the product of two falloffs — one along the axis measured
    from the apex, one ACROSS the wedge from its centreline — and both reach zero
    BEFORE the geometry does. That is what stops a beam reading as a filled
    triangle with square corners: there is no pixel at the cone's boundary, so
    there is no boundary to see.

    The field is evaluated on a 1/ss grid and upscaled. It is a smooth
    low-frequency field, so the coarse grid is visually identical to a
    per-pixel loop and about ss^2 times cheaper (lib/cardframe.add_glow uses the
    same trick for the same reason).
    """
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa, ca
    half = math.tan(math.radians(half_deg))
    L = float(length)
    ex, ey = apex[0] + ca * L, apex[1] + sa * L

    pad = int(L * half) + 6
    bx0 = int(math.floor(min(apex[0], ex) - pad))
    by0 = int(math.floor(min(apex[1], ey) - pad))
    bw = int(math.ceil(max(apex[0], ex) + pad)) - bx0
    bh = int(math.ceil(max(apex[1], ey) + pad)) - by0
    if bw < 2 or bh < 2:
        return img

    mw, mh = max(2, bw // ss), max(2, bh // ss)
    ax, ay = apex[0] - bx0, apex[1] - by0
    mask = Image.new('L', (mw, mh), 0)
    mp = mask.load()
    for j in range(mh):
        y = (j * ss + ss * 0.5) - ay
        for i in range(mw):
            x = (i * ss + ss * 0.5) - ax
            u = x * ca + y * sa
            if u <= 1.0 or u >= L:
                continue
            v = abs(x * nx + y * ny) / (half * u)
            if v >= 1.0:
                continue
            mp[i, j] = int(255 * ((1.0 - u / L) ** along) * ((1.0 - v * v) ** across))
    mask = mask.resize((bw, bh), Image.BILINEAR)

    layer = Image.new('RGBA', (bw, bh), tuple(colour) + (0,))
    layer.putalpha(mask.point(lambda v: int(v * peak / 255.0)))
    base = img.convert('RGBA')
    base.alpha_composite(layer, dest=(bx0, by0))
    return base.convert('RGB')


# (half-angle deg, peak alpha, axial falloff, transverse falloff) per wash layer.
# Wide-and-dim under narrow-and-hot: that ordering is what makes the funnel read
# as layered light rather than as one vector triangle.
BEAM_LAYERS = ((13.0, 62, 1.50, 1.5),
               (8.0, 105, 1.25, 1.7),
               (3.4, 150, 1.00, 2.0))


def _beam(img, apex, ang, length, layers=BEAM_LAYERS, colour=AMBER):
    """One beam: N nested washes of decreasing half-angle, all feathered."""
    for half_deg, peak, along, across in layers:
        img = _soft_wash(img, apex, ang, length, half_deg=half_deg, colour=colour,
                         peak=peak, along=along, across=across)
    return img


def _wedge_contour(img, apex, ang, length, half_deg, colour, seed, alpha=110):
    """The hand-drawn boundary of a wash, blurred into the wash.

    'The gradient is the fill, the hand-drawn line is the line' still holds — the
    line is simply no longer a hard edge, because it is composited through a
    blur rather than stroked onto the card.
    """
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa, ca
    half = math.tan(math.radians(half_deg))

    def edge(s):
        return [(apex[0] + ca * length * t + nx * half * length * t * s,
                 apex[1] + sa * length * t + ny * half * length * t * s)
                for t in (0.10, 0.34, 0.62, 0.86)]

    for s, k in ((-1.0, 0), (1.0, 1)):
        pts = edge(s)
        img = _soft_stroke(img, pts, colour, 3, seed=seed + k, wobble=3.0,
                           wavelength=260.0, alpha=alpha, blur=4)
    return img


# ---------------------------------------------------------------------------
# 4. psr_size — VOID / bone. THE size beat: a city-sized dead star with a
#    measurement callout. One focal point (the core), the bracket is support.
# ---------------------------------------------------------------------------

def render_psr_size(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=404, stars=120)

    cx, cy, r = 900, 330, 54
    _halo(img, cx, cy, [(118, 26, 4), (96, 40, 4)], VIOLET)
    _core(img, cx, cy, r, seed=41, gradient=True)          # the legal gradient

    # measurement bracket under the star. _soft_stroke composites into a NEW
    # image and returns it, so the result has to be assigned — a bare call
    # silently draws into a copy that is thrown away.
    by = 448
    img = _soft_stroke(img, [(762, by), (900, by + 2), (1038, by)], BONE, K.DETAIL,
                       seed=1201, wobble=2.0, wavelength=240.0, alpha=225, blur=2)
    for tx, s in ((762, 1), (1038, -1)):
        img = _soft_stroke(img, [(tx, by - 14), (tx, by + 14)], BONE, K.DETAIL,
                           seed=1202 + s, wobble=1.2, wavelength=120.0,
                           alpha=225, blur=2)

    d = ImageDraw.Draw(img)
    _stamp_centred(d, "20 KM ACROSS", cx, 400, BONE)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# 5. psr_collapse — VOID / amber. The core has already SNAPPED down to r=30 and
#    blown its material outward: streaks, a debris ring, a flat white-hot core.
# ---------------------------------------------------------------------------

def render_psr_collapse(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=505, stars=110)

    cx, cy = 900, 330
    d = ImageDraw.Draw(img, 'RGBA')

    # starfield streaks, three quantized length steps
    lens = (110, 180, 250)
    for i in range(24):
        ang = math.tau * i / 24 + 0.13
        step = i % 3
        L = lens[step]
        a = int((34, 52, 70)[step])
        ca, sa = math.cos(ang), math.sin(ang)
        p0 = (cx + 34 * ca, cy + 34 * sa)
        p2 = (cx + L * ca, cy + L * sa)
        p1 = (cx + (34 + L) * 0.36 * ca, cy + (34 + L) * 0.36 * sa)
        p1b = (cx + (34 + L) * 0.68 * ca, cy + (34 + L) * 0.68 * sa)
        _stroke_open(d, [p0, p1, p1b, p2], _alpha(AMBER, a), K.FINE,
                     seed=600 + i, wobble=3.0, wavelength=200.0)

    # debris ring: 9 amber rock blobs on an ellipse, deterministic placement
    for i in range(9):
        ang = math.tau * i / 9 + 0.22
        bx = cx + 300 * math.cos(ang)
        by = cy + 90 * math.sin(ang)
        rr = (6, 9, 14, 8, 11, 7, 13, 10, 6)[i]
        K.draw_disc(d, bx, by, rr, fill=_alpha(_lerp(AMBER, INK, 0.45), 235),
                    outline=_alpha(AMBER, 255), width=3, seed=700 + i, wobble=1.6)

    _halo(img, cx, cy, [(104, 30, 4), (82, 44, 4)], VIOLET)
    _core(img, cx, cy, 30, seed=505, gradient=True)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# 6. psr_spin — VOID / violet. The spin beat. Core is FLAT (this card is not on
#    the gradient_rule list); the motion is carried by the limb tick + its blur
#    trail, and the magnetic poles get two lofted violet field arcs.
# ---------------------------------------------------------------------------

def render_psr_spin(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=606, stars=115)

    cx, cy = 900, 320
    _halo(img, cx, cy, [(86, 32, 4), (66, 42, 4)], VIOLET)

    d = ImageDraw.Draw(img, 'RGBA')
    # magnetic field arcs, lofting above and below the poles on the shared axis
    for k, (base, rr, a, w) in enumerate(((N_POLE, 116, 195, K.DETAIL),
                                          (S_POLE, 116, 195, K.DETAIL),
                                          (N_POLE, 158, 100, 3),
                                          (S_POLE, 158, 100, 3))):
        _wobbly_arc(d, cx, cy, rr, base - 0.62, base + 0.62,
                    _alpha(VIOLET, a), w, seed=52 + k, wobble=5.0, wl=240.0)

    _core(img, cx, cy, 30, seed=606, gradient=False)

    # amber spin tick on the limb + a three-step trail (the blur)
    tick = math.radians(35.0)
    for k, (a, al, w) in enumerate(((tick, 70, 2), (tick - 0.30, 110, 2),
                                    (tick - 0.58, 150, 2), (tick, 255, 3))):
        ca, sa = math.cos(a), math.sin(a)
        d.line([(cx + 32 * ca, cy + 32 * sa), (cx + (48 if k == 3 else 44) * ca,
               cy + (48 if k == 3 else 44) * sa)], fill=_alpha(AMBER, al), width=w)

    # the period stamp sits BELOW the outer field arc (which reaches y ~= 486),
    # so no glyph ever lands on the linework
    _stamp_centred(d, "6.2 MS PER TURN", cx, 528, BONE)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# 7. psr_rate — VOID / bone. DIAGRAM-ONLY (no character, per the schedule).
#    The hero is the number, set through C.hero_word so it cannot clip, inside a
#    60-tick stopwatch ring whose amber hand chases the ring. The ring is drawn
#    LAST-but-one and the type is clamped to stay clear of it.
# ---------------------------------------------------------------------------

def render_psr_rate(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=707, stars=100)

    cx, cy, R = 520, 348, 232
    d = ImageDraw.Draw(img, 'RGBA')

    # hand-drawn stopwatch ring (never a perfect CAD circle)
    K.draw_outline(d, _circle_pts(cx, cy, R, 26), color=BONE, width=K.DETAIL,
                   closed=True, seed=811, wobble=2.6, wavelength=340.0)
    # 60 tick marks, every 5th a major
    for i in range(60):
        ang = math.tau * i / 60
        major = (i % 5 == 0)
        r0 = R - (17 if major else 9)
        r1 = R - 1
        w = 3 if major else K.FINE
        d.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)),
                (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))],
               fill=BONE, width=w)

    # the chasing hand: amber arc over three radii = 160 turns/s reading as a blur
    for k, (rr, a) in enumerate(((R - 1, 70), (R - 13, 110), (R - 25, 150))):
        _stroke_open(d, _arc_pts(cx, cy, rr, -0.95, 0.35), _alpha(AMBER, a),
                     3 if k == 2 else 2, seed=820 + k, wobble=2.0, wavelength=200.0)
    # the spoke runs only over the OUTER band. Drawn from the hub it crossed the
    # hero's own box, and a diagram line through the number reads as a mistake.
    _stroke_open(d, _arc_pts(cx, cy, R - 46, -0.95, -0.28), AMBER, 3,
                 seed=826, wobble=2.0, wavelength=200.0)

    _core(img, cx, cy, 30, seed=707, gradient=False)   # not on the gradient list

    # --- the hero, ABOVE the hub, with the unit stack cleanly BELOW it ---
    # C.hero_word owns the clamp: it measures the stroked box (not the advance
    # box), shrinks long phrases, and refuses to sit in rows 0..83.
    C.hero_word(d, "6.2", cx, cy - 112, BONE, stroke_rgb=INK, stroke_width=4,
                px=92, margin=48, y_max=HERO_Y_MAX)
    _stamp_centred(d, "MILLISECONDS", cx, cy + 56, BONE)
    _stamp_centred(d, "PER TURN", cx, cy + 80, BONE)

    # the frequency reading is a SIDE annotation, outside the ring, so it never
    # lands on a tick mark or on the chasing hand
    img = _soft_stroke(img, [(cx + R + 34, cy - 74), (cx + R + 34, cy + 74)], BONE,
                       K.FINE, seed=840, wobble=1.6, wavelength=180.0,
                       alpha=150, blur=2)
    d2 = ImageDraw.Draw(img, 'RGBA')
    _stamp_centred(d2, "161", 1000, 258, AMBER)
    _stamp_centred(d2, "TURNS / SEC", 1000, 288, AMBER)
    _stamp_centred(d2, "EACH 6.2 MS", 1000, 340, BONE)

    C._header(img, planet, paper_band=True)
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# 8. psr_beams — VOID / amber. The two opposed beams off the magnetic poles, on
#    the shared 30-deg axis. Each beam is THREE nested feathered washes plus a
#    blurred contour, so the funnel is painterly and has no hard cone edge.
# ---------------------------------------------------------------------------

def render_psr_beams(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=808, stars=100)

    cx, cy = 900, 330
    r = 30
    apex_n = (cx + r * 0.5 * math.cos(N_POLE), cy + r * math.sin(N_POLE))
    apex_s = (cx - r * 0.5 * math.cos(N_POLE), cy - r * math.sin(N_POLE))

    # wide and dim first, then narrower and hotter: a layered funnel, not a wedge
    for apex, ang, sd in ((apex_s, math.degrees(S_POLE), 830),
                          (apex_n, math.degrees(N_POLE), 840)):
        img = _beam(img, apex, ang, 262)
        img = _wedge_contour(img, apex, ang, 262, 13.0, AMBER, sd, alpha=95)

    _halo(img, cx, cy, [(78, 66, 4), (64, 40, 4)], VIOLET)
    _core(img, cx, cy, r, seed=808, gradient=True)       # legal on this card

    d = ImageDraw.Draw(img)
    # NOT "MAGNETIC POLES" — that is the caption's own words. The stamp names
    # what the beams are, which the caption does not.
    _stamp_centred(d, "RADIO BEAMS", cx, 596, AMBER)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# 9. psr_lighthouse — CREAM / cream. Register P: flat fills, THICK organic
#    outlines, every word slate-black (amber-on-cream and bone-on-cream are
#    both forbidden by PALETTE_SPEC.md §1). No gradient anywhere on this card.
#
#    The tower is NOT a smoothed closed polygon. K.draw_smooth runs every shape
#    through a Catmull-Rom spline, which rounds all four corners of the tower
#    quad into a capsule — that is what read as a bowling pin. Instead the tower
#    is a FLAT-fill polygon (crisp, square base on the ground line) with its two
#    sides stroked as separate open wobbled lines, and a gallery deck and lantern
#    room above it so the silhouette is unmistakably a lighthouse.
# ---------------------------------------------------------------------------

_LX, _GY = 1000, 620            # lighthouse x, ground line y
_T_TOP, _T_BASE = 340, 626      # tower top / base (base tucked under the ground)
_T_HT, _T_HB = 31, 49           # half-width at the lantern / at the base


def _tower_half(t):
    """Half-width at taper fraction t (0 at the lantern, 1 at the base). The
    exponent makes the taper slightly concave — a lighthouse necks in toward the
    top — rather than the straight-sided cone a linear taper would give."""
    return _T_HT + (_T_HB - _T_HT) * (t ** 1.45)


def _tower_side(steps=18):
    """Dense samples down one side of the tower, top -> base. Dense enough that
    the flat fill's edge is already smooth before the outline goes on."""
    out = []
    for i in range(steps):
        t = i / (steps - 1.0)
        out.append((_LX - _tower_half(t), _T_TOP + (_T_BASE - _T_TOP) * t))
    return out


def render_psr_lighthouse(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), PAPER)

    lamp = (_LX, 292)            # the lit lamp inside the lantern room

    # --- the two light beams: soft feathered washes, NO hard cone edge ---
    # On cream the wash has to carry real luminance to read as light at all, so
    # these run a flatter axial falloff than the void-card beams: the energy has
    # to survive out to the frame edge instead of dying inside a quarter of it.
    # Both directions are mirrored about the horizontal so the pair stays rigid.
    for ang in (12.0, 168.0):
        img = _soft_wash(img, lamp, ang, 268, half_deg=18.0, colour=AMBER,
                         peak=92, along=0.95, across=1.35)
        img = _soft_wash(img, lamp, ang, 238, half_deg=10.0, colour=AMBER,
                         peak=118, along=0.90, across=1.60)
        img = _soft_wash(img, lamp, ang, 150, half_deg=4.0, colour=AMBER,
                         peak=104, along=0.85, across=2.00)
    # the hand-drawn beam boundary, blurred so it is a painterly line and not a
    # vector edge. It stops short of the frame edge so no stroke runs off-card.
    img = _wedge_contour(img, lamp, 12.0, 250, 18.0, AMBER, 940, alpha=48)
    img = _wedge_contour(img, lamp, 168.0, 250, 18.0, AMBER, 950, alpha=48)

    # --- ground: flat fill, thick hand-drawn slate-black top edge ---
    ground = [(0, C.H), (0, _GY)]
    for gx in range(0, C.W + 1, 40):
        ground.append((gx, _GY))
    ground += [(C.W, _GY), (C.W, C.H)]
    K.draw_smooth(ImageDraw.Draw(img), ground, fill=(228, 218, 196),
                  outline=INK, width=K.OUTLINE, seed=903, wobble=2.6, wavelength=300.0)

    d = ImageDraw.Draw(img)
    # three flat rocks on the ground for painterly texture
    for rx, ry, rr in ((170, 664, 22), (206, 686, 13), (352, 672, 17)):
        K.draw_disc(d, rx, ry, rr, fill=(214, 204, 180), outline=INK,
                    width=K.DETAIL, seed=910 + rx)

    # --- tower: FLAT fill with a square base, then open wobbled side strokes ---
    left = _tower_side()
    right = [(2 * _LX - x, y) for x, y in left]            # mirror about _LX
    d.polygon(left + right[::-1], fill=(238, 230, 210))
    # each side is its own OPEN stroke, run from the base up past the lantern, so
    # the spline never turns a base corner into a round cap
    _stroke_open(d, [( _LX - _T_HB, _T_BASE)] + left[::-1],
                 INK, K.OUTLINE, seed=920, wobble=2.0, wavelength=200.0)
    _stroke_open(d, [(_LX + _T_HB, _T_BASE)] + right[::-1],
                 INK, K.OUTLINE, seed=921, wobble=2.0, wavelength=200.0)
    # the base meets the ground line on one hand-drawn rule, not a round cap
    _stroke_open(d, [(_LX - _T_HB - 3, _T_BASE - 5), (_LX, _T_BASE - 2),
                     (_LX + _T_HB + 3, _T_BASE - 5)],
                 INK, K.OUTLINE, seed=922, wobble=1.6, wavelength=150.0)
    for by in (432, 500, 568):                              # course lines
        t = (by - _T_TOP) / float(_T_BASE - _T_TOP)
        half = _tower_half(t)
        _stroke_open(d, [(_LX - half + 4, by), (_LX, by + 2), (_LX + half - 4, by)],
                     INK, K.DETAIL, seed=930 + by, wobble=1.4, wavelength=160.0)

    # --- gallery deck: the shelf that says "lighthouse" and not "rocket" ---
    K.draw_smooth(d, [(_LX - 56, 344), (_LX - 56, 326), (_LX + 56, 326),
                      (_LX + 56, 344)],
                  fill=(224, 214, 192), outline=INK, width=K.OUTLINE, seed=940,
                  wobble=1.0, wavelength=140.0)

    # --- lantern room (silhouette) + the lamp inside it ---
    K.draw_smooth(d, [(_LX - 30, 326), (_LX - 30, 274), (_LX + 30, 274),
                      (_LX + 30, 326)],
                  fill=INK, outline=INK, width=K.OUTLINE, seed=941,
                  wobble=1.0, wavelength=140.0)
    # a shallow domed cap, not a sharp cone — the cone is what read as a rocket
    cap = [(_LX - 38 + 76 * (i / 12.0), 274 - 30 * math.sin(math.pi * (i / 12.0)) ** 0.70)
           for i in range(13)]
    K.draw_smooth(d, cap, fill=INK, outline=INK, width=K.OUTLINE, seed=942,
                  wobble=1.2, wavelength=140.0)
    # the lantern's glass + the lit lamp, so the housing reads as a lamp room
    d.rectangle([_LX - 20, 282, _LX + 20, 304], fill=PAPER)
    K.draw_disc(d, _LX, 293, 11, fill=AMBER, outline=INK, width=2, seed=943, wobble=1.2)

    # ON stamp, directly beneath the lamp (this still is the ON beat)
    _stamp_centred(d, "ON", _LX, 356, INK, ink_rgb=PAPER)

    C._header(img, planet, paper_band=False)
    C._draw_stickman(img, card, theme='light')
    C._caption(img, card['caption'], 70, 652, dark_bg=False)
    return img


# ---------------------------------------------------------------------------
# 10. psr_name — VOID / bone. The reveal is the THREE PLANETS, so the three
#     bone dots are the focal group and carry the hero phrase. The old giant
#     "PSR B1257+12" stamp is gone: it is already in the title strip on every
#     card and again in the caption, so it was pure restatement. VIRGO stays —
#     it is the one fact on this card the narration does not say.
# ---------------------------------------------------------------------------

def render_psr_name(card, planet="PSR B1257+12"):
    img = Image.new('RGB', (C.W, C.H), DEEP)
    C.void_backdrop(img, seed=909, stars=115)

    cx, cy = 900, 322
    _halo(img, cx, cy, [(86, 30, 4), (66, 44, 4)], VIOLET)
    _core(img, cx, cy, 34, seed=909, gradient=True)     # legal on this card

    # --- the three planets ride a WIDE tilted orbit that arcs over the star ---
    # An orbit tight enough to cross the core put all three dots inside its glow,
    # which turned the pulsar into a dark smudge and the planets into specks.
    # Widening it separates the group from the star and makes the core read again.
    orx, ory, tilt = 232, 92, math.radians(-9.0)
    ct, st = math.cos(tilt), math.sin(tilt)

    def orbit(a_deg):
        a = math.radians(a_deg)
        ex, ey = orx * math.cos(a), ory * math.sin(a)
        return (cx + ex * ct - ey * st, cy + ex * st + ey * ct)

    arc = [orbit(196 + 148 * (i / 30.0)) for i in range(31)]
    img = _soft_stroke(img, arc, BONE, K.FINE, seed=960, wobble=3.0,
                       wavelength=260.0, alpha=120, blur=3)
    for k, a_deg in enumerate((216, 270, 324)):
        px, py = orbit(a_deg)
        C.add_glow(img, int(px), int(py), 22, BONE, 34)
        K.draw_disc(ImageDraw.Draw(img, 'RGBA'), px, py, 13, fill=_alpha(BONE, 255),
                    outline=_alpha(INK, 210), width=3, seed=970 + k, wobble=1.6)

    # the hero names the group, and C.hero_word guarantees it cannot clip or
    # ride up into the title strip
    C.hero_word(ImageDraw.Draw(img), "THREE PLANETS", cx, 546, BONE,
                stroke_rgb=INK, stroke_width=4, px=64, margin=48,
                y_max=HERO_Y_MAX)

    d = ImageDraw.Draw(img)
    _stamp_centred(d, "VIRGO", 1160, 140, AMBER)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


RENDERERS = {
    'psr_size': render_psr_size,
    'psr_collapse': render_psr_collapse,
    'psr_spin': render_psr_spin,
    'psr_rate': render_psr_rate,
    'psr_beams': render_psr_beams,
    'psr_lighthouse': render_psr_lighthouse,
    'psr_name': render_psr_name,
}


def register(mapping=None):
    """Merge this beat's renderers into the shared dispatch table."""
    C.register(RENDERERS)
    if mapping:
        C.register(mapping)
    return RENDERERS


if __name__ == '__main__':
    import json
    import time
    here = os.path.dirname(os.path.abspath(__file__))
    beat = json.load(open(os.path.join(here, '_beats', 'b2.json')))
    for cd in beat['cards']:
        t0 = time.time()
        im = RENDERERS[cd['id']](cd, "PSR B1257+12")
        dt = time.time() - t0
        im.save(os.path.join(here, '_beats', 'preview_b2_%s.png' % cd['id']))
        print('%-16s %-5s %sx%s  %.2fs' % (cd['id'], im.mode, im.size[0],
                                           im.size[1], dt))