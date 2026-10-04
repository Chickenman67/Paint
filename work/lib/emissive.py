# work/lib/emissive.py — luminous bodies and expansion cues.
#
# WHY THIS EXISTS. Three of the six gaps in the round-1 critic pass were the same
# mistake wearing different clothes: we drew LUMINOUS things as if they were
# painted objects.
#
#   G3  A body described as hot / molten / glowing / irradiated was drawn as a
#       flat disc. TrES-2b's whole signature is a matte-black disc with a GLOWING
#       red-orange crescent limb and a soft halo. A flat disc is a sticker.
#   G2  Explanatory beats were drawn as props. tres2b beat_12 was three unfilled
#       red circles with two small arrows on one diagonal -- it read as a
#       dartboard, not as a star expanding. The missing ingredient is a DIRECTION
#       cue, and a cue has to be a *source* + *asymmetric outward arrows*, not
#       concentric circles.
#
# The reference-quality example already in this codebase is tres2b beat_10
# (`work/segments/tres2b/cardsheet/beat_10.png`): a stippled emissive red dwarf
# with a real soft glow halo. That card is built from cardframe._radial_core +
# cardframe.add_glow + ink.stipple. This module is the generalised, standalone
# version of that triple, plus the two things beat_10 did not need.
#
# STYLE_CANON §0: smooth gradient + glow is legal for EMISSIVE BODIES ONLY. A
# planet is not emissive in the gradient sense -- a planet gets surface
# treatment. So every function here takes a color and an intensity, never a
# "paint this shape" flag; a non-emissive body should never call into this
# module at all.
#
# DETERMINISM. Every function takes an explicit `seed` and uses only
# `random.Random(seed)` or closed-form numpy. No global random state, no
# `hash()`. Two renders with the same seed and arguments are byte-identical --
# this is the property the per-segment re-render loop depends on, so a fix to
# beat_12 does not silently restyle beat_11.
#
# IMPORTS. `lib.ink` is used for the hand-wobbled ring/silhouette strokes, but it
# is imported lazily and the module degrades to an internal equivalent if it is
# unavailable, so this file stays usable standalone (`python work/lib/emissive.py`
# renders the demo sheet).
#
# COORDINATE / ANGLE CONVENTION. Screen space: y grows DOWNWARD. Angles are
# PIL/compass screen angles in degrees -- 0 = 3 o'clock, 90 = bottom (6 o'clock),
# 180 = 9 o'clock, 270 = top (12 o'clock). This matches
# `lib.ink._smooth_open`, `segments/tres2b/_cards.py::_arc_pts`, and every other
# angle in this codebase. `light_deg` therefore reads naturally: 315 = the star
# is up and to the right.

import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

try:
    import lib.ink as K
except ImportError:                                   # pragma: no cover
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _WORK = os.path.dirname(_HERE)
    if _WORK not in sys.path:
        sys.path.insert(0, _WORK)
    try:
        import lib.ink as K
    except ImportError:
        K = None


# --- Canonical colours -------------------------------------------------------
# TrES-2b's segment palette, so a demo of this module is a recognisable card and
# not three grey circles on white. Every colour is a segment's choice; pass your
# own.
EMBER_CORE = (18, 10, 12)       # the unlit disc: matte black, never pure #000
EMBER_LIMB = (226, 78, 34)      # the lit limb
EMBER_HOT = (255, 176, 96)      # the hottest part of the limb
VOID = (9, 10, 22)              # register-S field
PAPER = (244, 236, 216)         # register-P paper

# Supersample factor for the crescent overlay. 2 is enough: the limb is a smooth
# low-frequency field and PIL's downsample gives the edge its anti-aliasing.
SS = 2


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _as_draw(target):
    """Accept a PIL Image, an ImageDraw, or anything exposing ._image/.im.

    Returns (image, ImageDraw). The returned ImageDraw is bound to `image`, so
    every function here draws in place and returns the draw for chaining.
    """
    if isinstance(target, ImageDraw.ImageDraw):
        img = target._image
        return img, target
    if isinstance(target, Image.Image):
        return target, ImageDraw.Draw(target)
    img = getattr(target, "_image", None) or getattr(target, "im", None)
    if isinstance(img, Image.Image):
        return img, ImageDraw.Draw(img)
    raise TypeError("emissive: expected a PIL Image or ImageDraw, got %r"
                    % type(target).__name__)


def _rgb(color):
    """Normalise a colour to a 3-tuple of ints. Accepts (r,g,b) or (r,g,b,a)."""
    c = tuple(color)
    return (int(c[0]), int(c[1]), int(c[2]))


def _lerp3(a, b, t):
    a = _rgb(a)
    b = _rgb(b)
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


def _mix(c0, c1, c2, t):
    """Three-stop ramp. t in [0,1]: 0 -> c0, 0.5 -> c1, 1 -> c2."""
    if t <= 0.5:
        return _lerp3(c0, c1, t * 2.0)
    return _lerp3(c1, c2, (t - 0.5) * 2.0)


def _smoothstep(x, lo, hi):
    """Hermite ramp, zero below lo and one above hi. Used for the terminator so
    the crescent's inner edge is soft instead of a hard cut."""
    if hi <= lo:
        return np.where(x >= hi, 1.0, 0.0)
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _luma(img):
    """Rec.601 luma of a pixel, 0-255."""
    c = _rgb(img)
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _bg_luma(img, cx, cy, r):
    """Mean luma of the annulus at ~1.15r around (cx, cy). Sampled BEFORE the body
    is drawn, so it is pure background and the halo can pick a mode from it."""
    r = max(4, int(r))
    x0, y0 = int(cx - r), int(cy - r)
    x1, y1 = int(cx + r) + 1, int(cy + r) + 1
    region = img.crop((max(0, x0), max(0, y0), min(img.width, x1),
                       min(img.height, y1)))
    if region.width < 2 or region.height < 2:
        return 128.0
    a = np.asarray(region.convert("L"), dtype=np.float32)
    if a.size == 0:
        return 128.0
    # The corner of the box is background too (the body is not drawn yet), so the
    # plain mean is a good enough read and costs nothing.
    return float(a.mean())


# ---------------------------------------------------------------------------
# 2. soft_glow -- the halo, composited UNDER the body
# ---------------------------------------------------------------------------

def soft_glow(img, cx, cy, r, color, strength=110, mode="auto", power=2.2,
              spread=1.0):
    """A soft radial glow around a luminous body. Draw this BEFORE the body, so
    the body sits on top of its own halo and the halo only reads where it escapes
    past the limb. That ordering is the whole trick: a halo painted on top of the
    disc flattens the disc, a halo behind it reads as light coming from behind.

        r         - the halo's OUTER radius, px. The falloff reaches exactly zero
                    here with zero slope, so there is no visible ring edge.
        strength  - peak alpha 0-255.
        power     - falloff exponent. 1.0 is a wide soft wash, 2.2 (default) is a
                    tight corona, 3.5+ is a hard bright core.
        mode      - "add"  additive (ImageChops.add). Right on a dark field: the
                           sky picks up light without washing out.
                    "wash" alpha-blended colour paste. Right on cream/paper: an
                           additive halo there saturates the whole disc to a pale
                            blob and the body stops reading as a body.
                    "auto" sample the background and choose (default).
        spread    - multiply r, so callers can write halo_spread=2.4 against the
                    body's own r.

    Edits `img` in place AND returns it (matches cardframe.soft_glow).

    Built at quarter resolution and upscaled: a halo is a low-frequency field, so
    this is visually identical and ~16x cheaper. The frame generator renders
    91 s x 30 fps of stamps, so this cost matters.
    """
    img = img if isinstance(img, Image.Image) else _as_draw(img)[0]
    cx, cy = int(round(cx)), int(round(cy))
    r = max(2, int(round(r * spread)))
    if strength <= 0:
        return img

    if mode == "auto":
        mode = "add" if _bg_luma(img, cx, cy, r) < 110.0 else "wash"

    size = r * 2
    small = max(8, r // 2)
    # Normalised distance from centre on the small grid: 0 at the middle, 1 at the
    # halo's outer edge, ~1.41 at the box corners.
    j = (np.arange(small, dtype=np.float32) + 0.5) / float(small) * 2.0 - 1.0
    d2 = j[None, :] ** 2 + j[:, None] ** 2
    # (1 - d^2)^power: exactly zero AT d=1 AND with zero slope there, which is
    # what guarantees no hard ring. Do NOT gate this with an extra smoothstep --
    # that would erase the bright centre and leave only an outer band.
    prof = np.clip(1.0 - d2, 0.0, 1.0) ** float(power)

    mask = Image.fromarray((prof * 255.0).astype(np.uint8), "L")
    mask = mask.resize((size, size), Image.BICUBIC)
    # Hard circular cutoff. On a near-black sky ANY nonzero contribution shows,
    # so a value threshold is not enough -- bilinear upsample leaves a faint
    # floor in the corners that a threshold misses. Multiply by an ellipse.
    cut = Image.new("L", (size, size), 0)
    ImageDraw.Draw(cut).ellipse([1, 1, size - 2, size - 2], fill=255)
    mask = ImageChops.multiply(mask, cut)
    if mask.getextrema()[1] == 0:
        return img

    box = (cx - r, cy - r, cx + r, cy + r)
    # Scale the mask by peak strength ONCE, then use it either as a light amount
    # (add) or as a paste alpha (wash). Applying it twice would square the falloff.
    a_mask = mask.point(lambda v, s=strength: int(v * s / 255))
    m3 = Image.merge("RGB", (a_mask, a_mask, a_mask))

    if mode == "add":
        region = img.crop(box).convert("RGB")
        if region.size != (size, size):
            region = region.resize((size, size), Image.BILINEAR)
        # The halo's COLOUR must be modulated by the mask, or `add` lifts the whole
        # square box uniformly and the paste region shows as a bright rectangle.
        halo = ImageChops.multiply(Image.new("RGB", (size, size), _rgb(color)), m3)
        img.paste(ImageChops.add(region, halo), (box[0], box[1]))
    else:  # wash
        patch = Image.new("RGB", (size, size), _rgb(color))
        img.paste(patch, (box[0], box[1]), a_mask)
    return img


# ---------------------------------------------------------------------------
# 3. stipple_fill -- the emissive grain
# ---------------------------------------------------------------------------

def stipple_fill(draw, cx, cy, r, color, seed=0, count=48, dot_r=1,
                 spread=0, half=0.62, alpha=None, jitter=0.0):
    """The dotted grain on a luminous body. This is the reference's painterly
    signature at the gradient seam (STYLE_CANON §0) and the thing that stops an
    airbrushed disc reading as vector art.

    `count` is a CONSTANT dot count, not a density: beat_10 solves density from
    the radius so the same ~48 speckles read identically on a 44 px dwarf and a
    132 px swollen star. A fixed density put ~160 black dots on the big star
    (measles) and ~18 on the small one (clean). Keep it constant.

    Dots go in the inscribed square of half-side `half`*r, never a box at 0.9r:
    that box's corners land at 1.27r, outside the limb, as measles. At the
    default 0.62 the corners sit at 0.877r -- inside, with margin for the wobble.

    `alpha` (0-255) sets a uniform per-dot opacity; without it the dots are fully
    opaque. `spread` widens the per-dot radius range, `jitter` (px) displaces
    each dot off its sampled point for a less regular hand-scatter.

    Accepts an Image or an ImageDraw. Returns the ImageDraw.
    """
    img, d = _as_draw(draw)
    r = float(r)
    if r <= 0 or count <= 0:
        return d
    rnd = random.Random(seed)
    h = r * half
    col = tuple(_rgb(color)) + (255 if alpha is None else int(alpha),)

    for _ in range(int(count)):
        x = cx + rnd.uniform(-h, h)
        y = cy + rnd.uniform(-h, h)
        if jitter:
            x += rnd.uniform(-jitter, jitter)
            y += rnd.uniform(-jitter, jitter)
        rr = rnd.randint(max(1, int(dot_r)), int(dot_r) + int(spread))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
    return d


# ---------------------------------------------------------------------------
# 1. emissive_limb -- the G3 fix
# ---------------------------------------------------------------------------

def emissive_limb(target, cx, cy, r, core_color, limb_color,
                  light_deg=315.0, limb_band=0.22, limb_gain=1.0,
                  ambient=0.10, terminator=0.12, hot=None, hot_stop=0.62,
                  rim_outer=0.035, halo=True, halo_spread=2.4,
                  halo_strength=120, halo_color=None, halo_mode="auto",
                  halo_power=2.2, stipple_color=None, stipple_seed=None,
                  stipple_count=48, outline=None, outline_width=6,
                  outline_seed=0, glow=0.0):
    """A dark body with a GLOWING crescent limb on the side facing an implied
    star, plus a soft halo underneath. This is the G3 fix and the reusable form of
    what tres2b beat_10 hand-rolled.

        target      PIL Image or ImageDraw. Drawn in place.
        core_color  the unlit disc -- matte black, never pure #000 (a pure black
                    hole has nothing for the limb gradient to sit against).
        limb_color  the lit limb's outer colour.
        light_deg   screen bearing of the implied star (see the module header).
                    315 = up and to the right.
        limb_band   thickness of the limb band as a fraction of r. 0.22 is a
                    crescent hugging the edge; 0.5 and up is a half-lit body.
        limb_gain   0..1 clamp on the limb's peak brightness.
        ambient     how much light spills into the unlit disc. 0 leaves it flat
                    (correct for a tidally locked world); 0.25+ starts to read as
                    a self-luminous body, which is what a STAR wants.
        terminator  where the lit/unlit split sits. 0 = half lit. -0.4 = a thin
                    crescent. +0.5 = a gibbous body.
        hot         optional third stop for the hottest part of the limb, so the
                    limb goes limb_color -> hot as it approaches the sub-stellar
                    point. hot_stop is the intensity at which hot takes over.
        rim_outer   how far the glow spills PAST the silhouette, as a fraction of
                    r. This is what makes it read as light rather than paint. It
                    fades to zero alpha at its own edge, so there is no hard ring.
        halo        False to skip; True/strength 0 to tune. halo_spread is in
                    units of r.
        halo_mode   "auto" (default) picks additive on a dark field and a blurred
                    wash on cream, because an additive halo on near-white paper
                    saturates the disc to a flat pale blob.
        stipple_color  grain colour on the body, or None for no grain.
        outline     optional keyline colour. Usually None: Register S bodies have
                    no hard outline, and a keyline on a glowing limb reads as a
                    sticker.

    Order matters and is handled here: halo first (so it escapes past the limb),
    then the flat core disc, then the crescent layer over it, then grain, then the
    optional keyline.

    The crescent composites as color = lerp(core, limb, I) with alpha = I. That
    pairing is deliberate: where the intensity falls to zero the colour falls to
    the core, which is exactly what is underneath, so the filter can never pull a
    dark fringe out of the limb edge. Premultiplying instead would require
    un-premultiplying on the way out and rings.

    Returns the ImageDraw bound to the target image.
    """
    img, d = _as_draw(target)
    cx, cy, r = float(cx), float(cy), float(r)
    if r <= 0:
        return d
    core = _rgb(core_color)
    limb = _rgb(limb_color)
    hotc = _rgb(hot) if hot is not None else None

    # --- 1. halo, UNDER the body ------------------------------------------
    if halo:
        hc = halo_color if halo_color is not None else (hotc if hotc else limb)
        soft_glow(img, cx, cy, r * halo_spread, hc,
                  strength=int(halo_strength), mode=halo_mode, power=halo_power)

    # --- geometry -------------------------------------------------------
    ux = math.cos(math.radians(light_deg))
    uy = math.sin(math.radians(light_deg))
    edge = 1.0 + max(0.0, rim_outer)
    half = int(math.ceil(r * edge)) + 2
    side = half * 2 + 1
    j = (np.arange(side * SS, dtype=np.float32) + 0.5) / SS - 0.5
    X = j[None, :] + (cx - half)
    Y = j[:, None] + (cy - half)

    nx = (X - cx) / r
    ny = (Y - cy) / r
    dist = np.sqrt(nx * nx + ny * ny)
    cosang = nx * ux + ny * uy          # 1 at the sub-stellar point

    lit = _smoothstep(cosang, terminator, 1.0)
    limb_prof = np.exp(-(((dist - 1.0) / max(1e-3, limb_band)) ** 2))
    inner = np.clip(1.0 - dist, 0.0, 1.0) ** 1.5

    I = ambient * inner * lit + limb_gain * limb_prof * lit
    I = np.clip(I, 0.0, 1.0)
    # anti-aliased silhouette, zero exactly at `edge`
    aa = 1.4 / (r * SS)
    alpha_disc = np.clip((edge - dist) / aa, 0.0, 1.0)

    # --- 2. the flat core disc -------------------------------------------
    mask = Image.fromarray((alpha_disc * 255.0).astype(np.uint8), "L")
    mask = mask.resize((side, side), Image.LANCZOS)
    img.paste(Image.new("RGB", (side, side), core), (int(cx - half), int(cy - half)),
              mask)

    # --- 3. the crescent layer -------------------------------------------
    if hotc is not None:
        t = np.clip((I - hot_stop) / max(1e-3, 1.0 - hot_stop), 0.0, 1.0)
        rgb = np.empty(I.shape + (3,), dtype=np.float32)
        for k in range(3):
            base = core[k] + (limb[k] - core[k]) * np.clip(I / max(hot_stop, 1e-3),
                                                           0.0, 1.0)
            rgb[..., k] = base + (hotc[k] - base) * t
    else:
        rgb = np.empty(I.shape + (3,), dtype=np.float32)
        for k in range(3):
            rgb[..., k] = core[k] + (limb[k] - core[k]) * I

    A = alpha_disc * I
    layer = np.dstack([np.clip(rgb, 0, 255), np.clip(A, 0.0, 1.0) * 255.0])
    layer_im = Image.fromarray(layer.astype(np.uint8), "RGBA")
    layer_im = layer_im.resize((side, side), Image.LANCZOS)
    # The crescent layer is pasted THROUGH ITS OWN ALPHA. An unmasked paste here
    # stamps the whole side x side square over the frame, and the LANCZOS resample
    # drives the RGB of the fully-transparent corners toward 0 -- which painted a
    # hard black box on top of the halo. The corners must stay transparent so the
    # soft_glow underneath survives. (Premultiplying before the resample keeps the
    # halo's smooth radial falloff intact; a flat unmasked paste does not.)
    pm = layer_im.getchannel("A").point(lambda v: v)
    rgb_pm = Image.merge("RGB", [
        Image.fromarray(
            (np.asarray(layer_im.getchannel(c), dtype=np.float32)
             * np.asarray(pm, dtype=np.float32) / 255.0).astype(np.uint8), "L")
        for c in "RGB"])
    img.paste(rgb_pm, (int(cx - half), int(cy - half)), pm)

    d = ImageDraw.Draw(img)

    # --- 4. grain ---------------------------------------------------------
    if stipple_color is not None:
        stipple_fill(d, cx, cy, r, stipple_color,
                     seed=(seed_for(outline_seed) if outline_seed else 0)
                     if stipple_seed is None else stipple_seed,
                     count=stipple_count)

    # --- 5. optional keyline ---------------------------------------------
    if outline is not None and outline_width > 0:
        _hand_disc(d, cx, cy, r, color=_rgb(outline), width=outline_width,
                   seed=outline_seed)

    # --- 6. optional full-body bloom (for a star, not a planet) ----------
    if glow > 0:
        _radial_bloom(img, cx, cy, r, limb if hotc is None else hotc, glow)
    return d


def seed_for(x):
    return int(x)


def _hand_disc(d, cx, cy, r, color, width, seed=0, wobble=None):
    """A hand-drawn circle. Uses lib.ink when available (an 8-gon run through a
    smooth spline, so the edge is an organic circle rather than a vector one);
    otherwise wobbles a 64-gon directly."""
    if K is not None:
        return K.draw_disc(d, cx, cy, r, fill=None, outline=color, width=width,
                           seed=seed, wobble=(wobble if wobble is not None else 3.0))
    pts = []
    rnd = random.Random(seed)
    ph = rnd.uniform(0, math.tau)
    for i in range(64):
        a = math.tau * i / 64
        rr = r * (1.0 + 0.012 * math.sin(2 * a + ph))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.line(pts + [pts[0]], fill=color, width=width, joint="curve")
    return pts


def _radial_bloom(img, cx, cy, r, color, strength):
    """A full-body smooth gradient -- what turns a crescent-lit body into a
    radiating one. Legitimate only where the body is genuinely emissive."""
    cx, cy, r = int(cx), int(cy), int(r)
    steps = 48
    d = ImageDraw.Draw(img, "RGBA")
    stops = [_lerp3(color, (255, 255, 255), 0.35), color,
             _lerp3(color, (0, 0, 0), 0.55)]
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rr = max(1, int(r * t))
        c = _mix(stops[0], stops[1], stops[2], t)
        c = tuple(max(0, min(255, int(v))) for v in c)
        a = int(255 * min(1.0, strength))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c + (a,))
    return d


# ---------------------------------------------------------------------------
# 4. expanding_rings -- the G2 directional cue
# ---------------------------------------------------------------------------

def expanding_rings(target, cx, cy, radii, color, width=6, seed=0, arrows=3,
                    bearings=None, phase=0.0, head=30, arrow_width=None,
                    alpha_ramp=(1.0, 0.62, 0.34), width_ramp=1.0,
                    core_color=None, core_r=None, arrow_color=None,
                    core_stipple=0, glow=0.0):
    """Concentric wobbled rings that read as something EXPANDING, not as a target.

    This replaces the beat_12 failure: three equal, unfilled, identically-weighted
    red circles with two small arrows on one shared diagonal read as a dartboard.
    Four things make it a direction instead of a bullseye, and all four matter:

      1. A SOURCE. `core_color` draws a filled, glowing centre. Rings without an
         origin have nothing to be outward FROM.
      2. A WEIGHT RAMP. `alpha_ramp`/`width_ramp` make the inner rings solid and
         thick and the outer ones thin and faint, so energy visibly dissipates.
         Equal-weight rings read as geometry; a ramp reads as emission.
      3. ARROWS THAT CROSS THE OUTER RING. Heads sit in the outer annulus, tips
         beyond the outermost ring, so the eye follows them out of the frame.
      4. SPREAD BEARINGS. beat_12 put both arrows on the same upper-left diagonal,
         where the inner shaft crossed the outer head and the two heads read as one
         bad double-headed dart. Default bearings are evenly spread with a
         half-step phase offset, so no two arrows share a diagonal.

        radii       radii in px, innermost first. An int is read as a count and
                    expanded geometrically.
        alpha_ramp  per-ring alpha, innermost first. Short lists are extrapolated
                    toward the last value rather than wrapping, so a 3-ring call
                    with a 2-entry ramp still fades outward.
        core_r      core radius; defaults to 0.42 x the innermost ring.
        arrows      how many outward arrowheads. 0 disables them.
        bearings    explicit screen bearings in degrees; overrides `arrows`.
        phase       rotates the default bearing set, to move arrows off the
                    frame's diagonals or off the title strip.
        core_stipple  grain dots on the core (count), matching emissive_limb.

    Returns the ImageDraw bound to the target image.
    """
    img, d = _as_draw(target)
    cx, cy = float(cx), float(cy)

    if isinstance(radii, int):
        base = width * 2.2 + 18.0
        radii = [base * (1.62 ** i) for i in range(max(1, radii))]
    radii = [float(x) for x in radii if x and x > 1]
    if not radii:
        return d
    n = len(radii)

    def _ramp(ramp, i):
        """ramp[0] is the innermost ring. Clamp/extrapolate the tail flat."""
        if not ramp:
            return 1.0
        if i < len(ramp):
            return float(ramp[i])
        return float(ramp[-1])

    col = _rgb(color)

    # --- the source -------------------------------------------------------
    if core_color is not None:
        cr = core_r if core_r else max(6.0, radii[0] * 0.42)
        soft_glow(img, cx, cy, cr * 2.6, core_color,
                  strength=min(150, 40 + int(cr * 1.5)), mode="auto")
        _radial_bloom(img, cx, cy, cr, _rgb(core_color), 1.0)
        if core_stipple:
            stipple_fill(d, cx, cy, cr, _lerp3(core_color, (0, 0, 0), 0.45),
                         seed=seed + 91, count=core_stipple)
        d = ImageDraw.Draw(img, "RGBA")

    # --- the rings, innermost first ---------------------------------------
    for i, rr in enumerate(radii):
        a = _ramp(alpha_ramp, i)
        if a <= 0.02:
            continue
        w = max(1, int(round(width * (_ramp_width(width_ramp, i)))))
        c = col + (int(255 * a),)
        _ring(d, cx, cy, rr, c, w, seed=seed + i * 13, wobble=max(1.6, rr * 0.012))

    # --- the arrows -------------------------------------------------------
    if arrows or bearings:
        acol = _rgb(arrow_color) if arrow_color is not None else col
        # Heads live in the OUTER ANNULUS, tips past the outermost ring: that
        # crossing is what makes the direction unambiguous.
        r_in = radii[-2] if n >= 2 else radii[0] * 0.55
        r_out = radii[-1]
        r_mid = (r_in + r_out) * 0.5
        span = (r_out - r_in) * 0.52
        aw = arrow_width or max(3, width - 2)
        if bearings is None:
            bearings = [phase + 360.0 * k / float(arrows) for k in range(arrows)]
        for k, ang in enumerate(bearings):
            a = math.radians(ang)
            ca, sa = math.cos(a), math.sin(a)
            p0 = (cx + (r_mid - span) * ca, cy + (r_mid - span) * sa)
            p1 = (cx + (r_mid + span) * ca, cy + (r_mid + span) * sa)
            _arrow(d, [p0, p1], acol, width=aw, head=head,
                   seed=seed + 400 + k * 7, wobble=1.0)
    return d


def _ramp_width(width_ramp, i):
    if width_ramp == 1.0:
        return 1.0
    return max(0.18, width_ramp ** i)


def _ring(d, cx, cy, r, color, width, seed=0, wobble=2.0):
    """One hand-wobbled ring.

    Drawn as a FILLED ANNULUS (outer wobbled polygon minus inner wobbled
    polygon), not a stroke. A semi-transparent `draw.line(..., joint='curve')`
    on an RGBA context composites each segment separately and leaves hairline
    gaps at the joints, so an alpha-ramped ring renders as a string of beads. A
    filled band has no interior seams. At full alpha the annulus is visually
    identical to a stroke of the same width.
    """
    r_out = r + width / 2.0
    r_in = max(0.5, r - width / 2.0)

    def band(ro, ri, n=64, ph=0.0):
        pts = []
        for i in range(n):
            a = math.tau * i / n
            # low-frequency organic variation, matching lib.ink's wobble feel
            rr = ro * (1.0 + (wobble / max(8.0, ro)) * 0.5 *
                       (0.7 * math.sin(2 * a + ph) + 0.3 * math.sin(5 * a + ph * 1.7)))
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        return pts

    ph = random.Random(seed).uniform(0, math.tau)
    outer = band(r_out, r_in, ph=ph)
    inner = band(r_in, r_out, ph=ph)
    # inner ring reversed so the band is a simple polygon (no even-odd needed)
    d.polygon(outer + inner[::-1], fill=color)
    return outer


def _arrow(d, points, color, width=4, head=26, seed=0, wobble=1.0):
    """An open hand curve with a solid triangular head on its last point. Matches
    the segment-local _arrow in tres2b/_cards.py so the arrowhead reads the same
    everywhere. Returns the tip."""
    pts = list(points)
    if len(pts) == 2:
        (x0, y0), (x1, y1) = pts
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        # a slight bow so the shaft is not a ruler line
        nx, ny = -(y1 - y0), (x1 - x0)
        ln = math.hypot(nx, ny) or 1.0
        bow = rnd_offset(seed, wobble)
        pts = [(x0, y0), (mx + nx / ln * bow, my + ny / ln * bow), (x1, y1)]
    if K is not None:
        dense = K.wobble_points(pts, seed=seed, amount=wobble, wavelength=130.0)
        dense = K._smooth_open(dense, samples=10)
    else:
        dense = pts
    d.line(dense, fill=color, width=width, joint="curve")
    tip = dense[-1]
    prev = dense[max(0, len(dense) - 8)]
    ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    ax, ay = math.cos(ang), math.sin(ang)
    px, py = -ay, ax
    h = float(head)
    tri = [tip,
           (tip[0] - ax * h + px * h * 0.55, tip[1] - ay * h + py * h * 0.55),
           (tip[0] - ax * h - px * h * 0.55, tip[1] - ay * h - py * h * 0.55)]
    d.polygon(tri, fill=color)
    return tip


def rnd_offset(seed, amount):
    """A deterministic signed offset in [-amount, amount]."""
    return random.Random(seed).uniform(-amount, amount)


# ---------------------------------------------------------------------------
# Convenience: the two compositions the gaps actually asked for
# ---------------------------------------------------------------------------

def glowing_limb_planet(img, cx, cy, r, limb_color=EMBER_LIMB,
                        core_color=EMBER_CORE, light_deg=315.0, seed=0,
                        hot=EMBER_HOT, halo_strength=132, stipple=True):
    """TrES-2b's signature in one call: a matte black world with a red-orange
    crescent limb facing its star, a soft halo, and grain. `stipple=False` for a
    body too small for grain to read."""
    return emissive_limb(
        img, cx, cy, r, core_color, limb_color,
        light_deg=light_deg, hot=hot, limb_band=0.24, limb_gain=1.0,
        ambient=0.06, terminator=0.10, halo=True, halo_spread=2.5,
        halo_strength=halo_strength, halo_color=limb_color,
        stipple_color=(120, 38, 24) if stipple else None,
        stipple_seed=seed + 5, outline=None)


def star_surface(img, cx, cy, r, seed=0, color=EMBER_LIMB, hot=EMBER_HOT,
                 halo_strength=150, grain=48, ambient=0.22):
    """A radiating body (a star, not a world): wide limb, high ambient, real
    halo, grain. This is beat_10's `_red_dwarf` generalised."""
    return emissive_limb(
        img, cx, cy, r, _lerp3(color, (0, 0, 0), 0.35), color,
        light_deg=270.0, limb_band=0.85, limb_gain=1.0, ambient=ambient,
        terminator=-1.0, hot=hot, hot_stop=0.5, halo=True, halo_spread=2.1,
        halo_strength=halo_strength, halo_color=hot, halo_power=2.0,
        stipple_color=(120, 38, 24), stipple_seed=seed, stipple_count=grain,
        outline=None, glow=0.0)


# ---------------------------------------------------------------------------
# Demo sheet
# ---------------------------------------------------------------------------

def _demo(outdir):
    """Render one PNG per function plus a contact sheet. Returns the paths."""
    os.makedirs(outdir, exist_ok=True)
    paths = []

    def sheet(title):
        img = Image.new("RGB", (1280, 760), PAPER)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 1280, 60], fill=(252, 250, 246))
        d.text((28, 22), title, fill=(20, 20, 24))
        return img

    # -- 1/2. emissive_limb on a VOID field (additive halo) -----------------
    img = sheet("1+2  emissive_limb + soft_glow on a VOID field (auto -> additive)")
    img = Image.new("RGB", (1280, 720), VOID)
    d = ImageDraw.Draw(img)
    srnd = random.Random(77)
    for _ in range(150):
        x, y = srnd.randint(0, 1280), srnd.randint(84, 720)
        rr = srnd.choice([0, 1, 1, 2])
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(225, 228, 240))
    glowing_limb_planet(img, 420, 380, 150, light_deg=315.0, seed=11)
    star_surface(img, 900, 340, 118, seed=12)
    p = os.path.join(outdir, "demo_1_emissive_limb_void.png")
    img.save(p)
    paths.append(p)

    # -- the same on CREAM (auto -> blurred wash) ---------------------------
    img = sheet("1+2  emissive_limb on CREAM (auto -> wash halo)")
    img = Image.new("RGB", (1280, 720), PAPER)
    glowing_limb_planet(img, 420, 380, 150, light_deg=315.0, seed=11)
    star_surface(img, 900, 340, 118, seed=12)
    p = os.path.join(outdir, "demo_1b_emissive_limb_cream.png")
    img.save(p)
    paths.append(p)

    # -- light bearing sweep ----------------------------------------------
    img = sheet("1  emissive_limb: light_deg sweep 0 / 90 / 180 / 270")
    img = Image.new("RGB", (1280, 720), PAPER)
    for i, ld in enumerate((0.0, 90.0, 180.0, 270.0)):
        cx = 190 + i * 300
        d = ImageDraw.Draw(img)
        d.line([(cx - 210, 360), (cx + 210, 360)], fill=(205, 198, 182), width=2)
        d.line([(cx, 140), (cx, 580)], fill=(205, 198, 182), width=2)
        glowing_limb_planet(img, cx, 360, 118, light_deg=ld, seed=20 + i)
        d = ImageDraw.Draw(img)
        d.text((cx - 46, 596), "light_deg=%d" % int(ld), fill=(30, 28, 24))
    p = os.path.join(outdir, "demo_1c_emissive_limb_bearings.png")
    img.save(p)
    paths.append(p)

    # -- 3. stipple_fill ---------------------------------------------------
    img = Image.new("RGB", (1280, 720), VOID)
    d = ImageDraw.Draw(img)
    d.text((28, 22), "3  stipple_fill: constant 48-dot grain at r=60 / 120 / 210",
           fill=(240, 240, 245))
    for i, rr in enumerate((60, 120, 210)):
        cx = 240 + i * 400
        star_surface(img, cx, 420, rr, seed=30 + i, grain=48)
        d = ImageDraw.Draw(img)
        d.text((cx - 30, 620), "r=%d" % rr, fill=(235, 232, 224))
    p = os.path.join(outdir, "demo_3_stipple_fill.png")
    img.save(p)
    paths.append(p)

    # -- 4. expanding_rings: the beat_12 replacement -----------------------
    img = Image.new("RGB", (1280, 720), PAPER)
    expanding_rings(img, 640, 400, [86, 152, 222], EMBER_LIMB, width=7, seed=41,
                    arrows=3, phase=18.0, core_color=EMBER_HOT, core_r=34,
                    core_stipple=26)
    d = ImageDraw.Draw(img)
    d.text((28, 22), "4  expanding_rings: source + weight ramp + 3 spread arrows",
           fill=(20, 20, 24))
    d.text((28, 664), "the G2 fix for tres2b beat_12", fill=(60, 56, 50))
    p = os.path.join(outdir, "demo_4_expanding_rings.png")
    img.save(p)
    paths.append(p)

    # -- 4b. rings without arrows, vs with: the target vs the direction ----
    img = Image.new("RGB", (1280, 720), PAPER)
    d = ImageDraw.Draw(img)
    d.text((28, 22), "4b  LEFT: equal-weight rings (the beat_12 bullseye)   "
                     "RIGHT: ramped rings + arrows (a direction)",
           fill=(20, 20, 24))
    for i in range(3):
        rr = (86, 152, 222)[i]
        _ring(d, 320, 400, rr, EMBER_LIMB + (255,), 7, seed=50 + i)
    expanding_rings(img, 900, 400, [86, 152, 222], EMBER_LIMB, width=7, seed=41,
                    arrows=3, phase=18.0, core_color=EMBER_HOT, core_r=34)
    p = os.path.join(outdir, "demo_4b_rings_comparison.png")
    img.save(p)
    paths.append(p)

    return paths


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.environ.get("EMISSIVE_DEMO_DIR",
                         os.path.join(here, "_emissive_demo"))
    for q in _demo(out):
        print(q)