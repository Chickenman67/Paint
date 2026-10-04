# work/segments/psrb1257/_cards_b6.py — B6 FATE card renderers.
#
# Beat: B6 FATE (schedule cards n=27..31)
#   close_bother      violet  void  motion haze_swell
#   close_no_burn     bone    void  motion flame_extinguish
#   close_formed      amber   void  motion debris_accumulate
#   close_radiation   violet  void  motion veil_stripes   (banner RADIATION BATH)
#   close_finale      bone    void  motion spin_step_0.25s (never decelerates)
#
# Every card in this beat is a VOID card, so every one uses:
#   - Layout A: 84 px paper title strip (C._header(..., paper_band=True)),
#     full-bleed art below, NO caption band, caption floating ON the art.
#   - theme='dark' for the character (cream limbs on the space field).
#   - C._caption(img, card['caption'], 70, 652, dark_bg=True) — identical call on
#     all five so the caption sits in the same place and colour across the beat.
#
# Register discipline (PALETTE_SPEC §3): the ONLY gradient legal in this segment is
# on an emissive pulsar core, and the beat's gradient_rule enumerates the cards that
# may use one — close_radiation and close_finale are NOT on that list, so both draw
# their core FLAT (flat fill + a flat inner disc). Everything else on every card here
# is flat fill, flat linework, or C.space_body's matte painterly bands. The washes
# and the beam field below are ALPHA FALLOFFS (a blurred L-mask composited through
# a colour layer), not colour ramps — that is the difference between a soft
# painterly veil and a gradient, and it is what keeps a wash from reading as a
# translucent rectangle with a visible box edge.
#
# Determinism: every wobble/stipple/starfield/random draw below takes an explicit
# seed; there is no module-level random state. Re-renders are byte-identical.
#
# Coordinate convention for annotation text: in this segment the schedule's
# annotation coordinates are TEXT CENTRES (planet_periods puts '25 D' at (640,262),
# exactly the centre-x of the inner orbit apex at x=640; how_grave says "centred at
# (900,300)"). Every stamp and every hero word below is therefore centred on the
# coordinate the sketch gives, not left-aligned to it.
#
# STICKMAN POSE OVERRIDE (close_bother only). The schedule asks for pose
# 'thinker'. lib.stickman's 'thinker' starts BOTH upper arms at cx ± 0.25*head_r
# while the 6 px spine only covers cx ± 3, so at h=480 the arms float ~12 px clear
# of the shoulder — measured by flood fill from the head, 699 px of the 480-tall
# figure is an unconnected component. The same gap exists in 'standing',
# 'hands_down', 'hands_up' and 'shrugged' (their `sx` offsets are 0.30–0.35
# head_r), so none of them is a valid substitute; only 'pointing', 'cowering' and
# 'shielding_eyes' start their arms on the spine. close_bother therefore uses
# 'shielding_eyes', which resolves to the SAME mouth_worried face as the
# schedule's 'worried_thinker', so the beat's expression is untouched and only the
# broken arm changes. See _with_pose().

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import lib.type as T
import lib.ink as K
import lib.cardframe as C

PAL = C.PAL

# Beat constants (single source of truth for the beat).
VIOLET = PAL['violet']
BONE = PAL['bone']
AMBER = PAL['amber']
INK = PAL['ink']
PAPER = PAL['paper']       # bone-cream, used as the flat inner disc of both cores

# Peak alpha of the feathered washes. These are the alpha at the wash's centre;
# every pixel falls off from there, so no wash has an edge.
VEIL_ALPHA = 34      # close_radiation's irradiated zone
HEARTH_ALPHA = 32    # close_no_burn's settled-ash glow
ACCRETION_ALPHA = 32 # close_formed's accretion glow

# The finale's spin tick. The frame generator advances this by 90 deg per 0.25 s
# stamp; the still ships it at the canonical starting angle and never a smooth tween.
FINALE_TICK_DEG = 315.0


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _text_w(draw, text, font):
    """Width of `text` in px, with a conservative fallback."""
    try:
        return font.getbbox(text)[2]
    except Exception:
        try:
            return draw.textsize(text, font=font)[0]
        except Exception:
            return int(len(text) * font.size * 0.55)


def _draw_centered(draw, text, cx, cy, fill, font, stroke_rgb, stroke_w):
    """Draw `text` with its horizontal CENTRE at cx and its top edge at cy."""
    w = _text_w(draw, text, font)
    T.draw_outlined_text(draw, (cx - w // 2, cy), text, font, fill=fill,
                         stroke=stroke_rgb, stroke_width=stroke_w)


def _with_pose(card, pose):
    """Copy of `card` with ONLY the stickman pose replaced.

    Expression, x_center, y_top and height all still come from the schedule, and
    the card is still rendered through C._draw_stickman — nothing about the figure
    is drawn here. See the module header for why close_bother needs this.
    """
    out = dict(card)
    out['stickman'] = dict(card.get('stickman') or {})
    out['stickman']['pose'] = pose
    return out


def _ellipse_mask(size, shrink=0.55):
    """A blurred 'L' ellipse that reaches ZERO alpha before the edge of its box.

    The hard-cutout multiply at the end is what guarantees the pasted wash has no
    straight border: on a near-black sky a bilinear upsample leaves a faint floor,
    and that floor is a visible rectangle.
    """
    w, h = max(4, size[0]), max(4, size[1])
    mask = Image.new('L', (w, h), 0)
    ix, iy = int(w * shrink), int(h * shrink)
    if w - 2 * ix > 2 and h - 2 * iy > 2:
        ImageDraw.Draw(mask).ellipse([ix, iy, w - ix, h - iy], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(max(2.0, min(w, h) * 0.45)))
    cut = Image.new('L', (w, h), 0)
    ImageDraw.Draw(cut).ellipse([1, 1, w - 2, h - 2], fill=255)
    return ImageChops.multiply(mask, cut)


def _soft_wash(img, cx, cy, rx, ry, colour, peak=30):
    """A feathered translucent wash: soft radial alpha falloff, no straight border,
    no colour ramp. Built at 1/3 resolution and upscaled — a low-frequency field is
    visually identical and ~9x cheaper than the full-size pass."""
    rx, ry = max(8, int(rx)), max(8, int(ry))
    mask = _ellipse_mask((rx * 2 // 3, ry * 2 // 3))
    mask = mask.resize((rx * 2, ry * 2), Image.BILINEAR)
    mask = mask.point(lambda v, p=peak: int(v * p / 255.0))
    img.paste(Image.new('RGB', mask.size, colour), (int(cx) - rx, int(cy) - ry), mask)
    return img


def _radiation_wash(img, seed, bbox, alpha, colour, lobes=8):
    """The wobbly radiation wash that appears in planet_minefield and RETURNS in
    close_bother. Same element, same seed, so the reprise reads as a callback — but
    feathered: the lobe polygon is rendered into a blurred alpha mask rather than
    filled directly, so the wash has no critical outline to read as a shape."""
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    hw, hh = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    rx, ry = int(hw), int(hh)
    sx, sy = max(4, rx // 2), max(4, ry // 2)
    rnd = random.Random(seed)
    pts = []
    for i in range(lobes):
        a = math.tau * i / lobes + rnd.uniform(-0.12, 0.12)
        s = 1.0 + rnd.uniform(-0.055, 0.055)
        pts.append(((s * math.cos(a) + 1.0) * sx, (s * math.sin(a) + 1.0) * sy))
    mask = Image.new('L', (sx * 2, sy * 2), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(max(4.0, min(sx, sy) * 0.16)))
    mask = mask.resize((rx * 2, ry * 2), Image.BILINEAR)
    cut = Image.new('L', mask.size, 0)
    ImageDraw.Draw(cut).ellipse([1, 1, mask.size[0] - 2, mask.size[1] - 2], fill=255)
    mask = ImageChops.multiply(mask, cut)
    img.paste(Image.new('RGB', mask.size, colour), (int(cx) - rx, int(cy) - ry), mask)
    return img


def _beam_field(img, cx, cy, ang_deg, colour, count=9, pitch=6.0,
                start=26.0, reach=730.0, seed=0, bow=16.0):
    """The raking radiation field. Nine rays that BOW (so the field splays instead
    of running dead straight), TAPER in both width and alpha along their length,
    and are composited from a blurred RGBA layer so every edge is feathered. The
    old version was nine parallel 3 px lines of constant alpha with square ends —
    a striped plank, which is exactly the hard-edged primitive the brief bans."""
    layer = Image.new('RGBA', (C.W, C.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    th = math.radians(ang_deg)
    dxu, dyu = -math.cos(th), math.sin(th)      # travel direction (left, down)
    nx, ny = -math.sin(th), -math.cos(th)       # perpendicular (the pitch axis)
    rnd = random.Random(seed)
    half = count // 2
    for i in range(-half, half + 1):
        jitter = rnd.uniform(-0.35, 0.35) * pitch
        steps = 30
        pts = []
        for s in range(steps + 1):
            t = s / steps
            dist = start + t * reach
            b = math.sin(t * math.pi) * bow * (1.0 if i >= 0 else -1.0)
            off = i * pitch + jitter + b
            pts.append((cx + dxu * dist + nx * off, cy + dyu * dist + ny * off))
        for s in range(steps):
            t0 = s / steps
            a = int(170 * (1.0 - t0) ** 1.35) + 42
            d.line([pts[s], pts[s + 1]], fill=colour + (a,),
                   width=4 if t0 < 0.35 else 3)
    layer = layer.filter(ImageFilter.GaussianBlur(2.4))
    return Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')


def _ragged_circle(cx, cy, r, seed, h3=0.055, h5=0.030, n=48):
    """A circle with two incommensurate radial harmonics — a hand-torn edge, not a
    plotted one. Deterministic in `seed`."""
    rnd = random.Random(seed)
    p1, p2 = rnd.uniform(0, math.tau), rnd.uniform(0, math.tau)
    out = []
    for s in range(n):
        a = math.tau * s / n
        rr = r * (1.0 + h3 * math.sin(3 * a + p1) + h5 * math.sin(5 * a + p2))
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


def _flame_pts(cx, cy, r):
    """Control points for one teardrop flame lobe centred on (cx, cy) with nominal
    radius r. Returned as a small control polygon — K.draw_smooth splines it into a
    smooth curve, which is what the reference's linework actually is."""
    return [
        (cx, cy - 1.35 * r),
        (cx + 0.60 * r, cy - 0.10 * r),
        (cx + 0.74 * r, cy + 0.46 * r),
        (cx + 0.34 * r, cy + 0.80 * r),
        (cx - 0.34 * r, cy + 0.80 * r),
        (cx - 0.74 * r, cy + 0.46 * r),
        (cx - 0.60 * r, cy - 0.10 * r),
    ]


# ---------------------------------------------------------------------------
# Card 27 — close_bother (violet, void)
# ---------------------------------------------------------------------------

def render_close_bother(card, planet="PSR B1257+12"):
    """'HERE IS THE PART THAT SHOULD BOTHER YOU.' The violet radiation wash comes
    back and swallows the frame, and INSIDE it — at the right, clear of the
    character — sits the thing that should bother you: the collapsed core, its two
    flat halo rings, and two of the rocks still circling it. One focal element."""
    img = Image.new('RGB', (C.W, C.H), PAL['deep'])
    C.void_backdrop(img, seed=2700, stars=120)

    # The returning wash: planet_minefield's shape and seed, now full-frame and
    # feathered so it has no outline. Peak alpha 26 at centre, falling to zero
    # before the frame edge; the frame generator swells it over four 0.25 s stamps.
    _radiation_wash(img, seed=71, bbox=(110, 96, 1270, 690),
                    alpha=26, colour=VIOLET)

    dw = ImageDraw.Draw(img, 'RGBA')

    # THE FOCAL: the dead core the wash is coming off. Flat slate-black disc with a
    # 4 px bone limb — no gradient (this card is not on the beat's gradient list).
    cx, cy, cr = 962, 332, 34
    K.draw_disc(dw, cx, cy, cr, fill=INK, outline=BONE + (200,),
                width=K.DETAIL, seed=2720)

    # Two flat violet halo rings — the radiation it is still throwing.
    for rr, a in ((56, 95), (76, 48)):
        K.draw_outline(dw, _ragged_circle(cx, cy, rr, seed=2725 + rr, h3=0.02, h5=0.012),
                       color=VIOLET + (a,), width=K.FINE, closed=True,
                       seed=2730 + rr, wobble=2.0, wavelength=150.0)

    # Two of the rocks, still on the halo. C.space_body is the matte painterly
    # treatment — wavy contour bands, no black outline, no soft-focus halo.
    img = C.space_body(img, cx + 62, cy + 45, 13, seed=2740, bands=2)
    img = C.space_body(img, cx - 66, cy - 31, 10, seed=2750, bands=2)
    dw = ImageDraw.Draw(img, 'RGBA')

    C._header(img, planet, paper_band=True)
    # Pose swapped from the schedule's 'thinker' — see the module header. Expression,
    # x, y_top and height are all still the schedule's.
    C._draw_stickman(img, _with_pose(card, 'shielding_eyes'), theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# Card 28 — close_no_burn (bone, void)
# ---------------------------------------------------------------------------

def render_close_no_burn(card, planet="PSR B1257+12"):
    """'THESE DID NOT FORM AROUND A STAR THAT WAS BURNING.' A bone flame drawn as
    LINEWORK ONLY in three stacked lobes, with the dead core left behind inside it
    and a settled bed of ash on the hearth. Nothing in the frame is still on fire."""
    img = Image.new('RGB', (C.W, C.H), PAL['deep'])
    C.void_backdrop(img, seed=2800, stars=110)

    dx, cy, R = 1000, 300, 124
    # The hearth: a feathered bone wash behind the whole assembly. This is the focal
    # element's ground — the old card had a hard-edged INK disc sitting on bare sky,
    # which read as a black rectangle punched into the starfield.
    _soft_wash(img, dx, cy + 24, 250, 268, BONE, peak=HEARTH_ALPHA)
    d = ImageDraw.Draw(img, 'RGBA')   # RGBA so the low-alpha fills actually blend

    # The bed of ash — the thick stroke this card earns its weight from. A closed,
    # flattened heap (a wide lens) so it reads as settled ash and so it uses the
    # locked 6 px large-shape outline weight.
    K.draw_smooth(d, [
        (dx - 0.72 * R, cy + 0.80 * R),
        (dx - 0.36 * R, cy + 0.88 * R),
        (dx, cy + 0.92 * R),
        (dx + 0.36 * R, cy + 0.88 * R),
        (dx + 0.72 * R, cy + 0.80 * R),
        (dx + 0.38 * R, cy + 1.02 * R),
        (dx - 0.38 * R, cy + 1.02 * R),
    ], fill=BONE + (150,), outline=BONE, width=K.OUTLINE, seed=2811,
        wobble=2.5, wavelength=120.0, closed=True)

    # Three stacked flame lobes, linework only: no fill, no gradient. The outermost
    # is the 2 px ghost; the frame generator collapses each lobe to nothing on its
    # own 0.25 s stamp, bottom lobe first.
    for i, r in enumerate((R, 0.62 * R, 0.31 * R)):
        K.draw_outline(d, _flame_pts(dx, cy, r), color=BONE, width=K.FINE,
                       closed=True, seed=2820 + i * 7, wobble=3.5,
                       wavelength=100.0)

    # What was left: the focal element. A flat slate-black disc on the hearth wash,
    # so it separates from the sky by VALUE rather than by a hard black keyline.
    K.draw_disc(d, dx, cy, 36, fill=INK, outline=None, seed=2830)
    K.draw_disc(d, dx, cy, 36, fill=None, outline=BONE + (170,),
                width=K.DETAIL, seed=2831)
    K.draw_outline(d, _ragged_circle(dx, cy, 27, seed=2832, h3=0.10, h5=0.07),
                   color=BONE + (95,), width=K.FINE, closed=True, seed=2833,
                   wobble=2.0, wavelength=60.0)

    stamp = T.load_font(T.STAMP_PX, bold=False)
    _draw_centered(d, "WHAT WAS LEFT", dx, 468, BONE, stamp, INK, T.STAMP_STROKE)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# Card 29 — close_formed (amber, void)
# ---------------------------------------------------------------------------

def render_close_formed(card, planet="PSR B1257+12"):
    """'THEY FORMED HERE, OR THEY SURVIVED BEING MADE HERE.' The remnant and the
    rock that collected on it: amber-rimmed slate blobs welded to the limb inside a
    flat amber accretion ring, over a soft accretion glow. Made here, not inherited
    — which is what the hero word says, because the caption already says 'formed
    here' and restating it would be redundant."""
    img = Image.new('RGB', (C.W, C.H), PAL['deep'])
    C.void_backdrop(img, seed=2900, stars=105)

    dx, cy, R = 980, 336, 34
    # The accretion glow: a feathered amber wash so the assembly is the one thing
    # the eye lands on. Feathered alpha falloff, not a colour ramp, not a disc.
    _soft_wash(img, dx, cy, 236, 214, AMBER, peak=ACCRETION_ALPHA)
    d = ImageDraw.Draw(img, 'RGBA')

    # The remnant star: flat slate-black disc with its 2 px amber limb. No gradient.
    K.draw_disc(d, dx, cy, R, fill=INK, outline=AMBER, width=K.FINE, seed=2905)

    # Six rock blobs stuck to the circumference (planet_minefield's irregular 7-gon
    # rocks, flattened and rimmed). Deterministic angles + per-blob wobble seeds.
    rnd = random.Random(2910)
    for i in range(6):
        a = math.tau * i / 6.0 + 0.26
        bx = dx + R * math.cos(a)
        by = cy + R * math.sin(a)
        br = 9 + int(rnd.uniform(0, 4))
        pts = []
        for k in range(7):
            ang = math.tau * k / 7.0
            rr = br * (1.0 + 0.22 * math.sin(2 * ang + i))
            pts.append((bx + rr * math.cos(ang), by + rr * math.sin(ang)))
        K.draw_smooth(d, pts, fill=INK, outline=AMBER, width=K.FINE,
                      seed=2920 + i * 5, wobble=1.6, wavelength=26.0)

    # The accretion ring they landed in — flat 2 px amber, no gradient.
    K.draw_outline(d, _ragged_circle(dx, cy, 58, seed=2930, h3=0.018, h5=0.010),
                   color=AMBER + (215,), width=K.FINE, closed=True, seed=2931,
                   wobble=1.8, wavelength=160.0)

    # The ONE dominant phrase. C.hero_word clamps it inside the frame INCLUDING its
    # keyline and keeps it below the title strip, which is what the hand-rolled
    # placement in this module used to get wrong. It is not a restatement of the
    # caption: the caption says they formed here, this says what that rules out.
    dl = ImageDraw.Draw(img)
    C.hero_word(dl, "NOT INHERITED", dx, 520, AMBER, stroke_rgb=INK,
                stroke_width=4, px=48, margin=56)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# Card 30 — close_radiation (violet, void)
# ---------------------------------------------------------------------------

def render_close_radiation(card, planet="PSR B1257+12"):
    """'THE RADIATION WOULD TEAR AN ATMOSPHERE APART BY AFTERNOON.' A feathered
    violet irradiated zone, a bowed and feathered amber beam field raking in from
    the core at -18 deg, and inside the zone the atmosphere drawn twice: the whole
    envelope, and the ragged shell that is all that will be left of it.

    The 64 pt 'IN AN AFTERNOON' is GONE. It restated the caption's own last two
    words and it was stamped straight across the character's legs."""
    img = Image.new('RGB', (C.W, C.H), PAL['deep'])
    C.void_backdrop(img, seed=3000, stars=95)

    # The irradiated zone — a soft translucent wash, feathered to zero at every
    # edge. The old flat VIOLET rectangle showed all four of its straight sides.
    _soft_wash(img, 470, 390, 352, 252, VIOLET, peak=VEIL_ALPHA)

    # The beam field, under the core so the core's limb stays crisp.
    img = _beam_field(img, 1000, 300, 18.0, AMBER, count=9, pitch=6.0,
                      start=26.0, reach=730.0, seed=3020)
    d = ImageDraw.Draw(img, 'RGBA')

    # Core at the head of the field. Flat: this card is not on the beat's
    # gradient_rule list, so no radial ramp on it — a flat BONE disc with a flat
    # PAPER inner disc, both palette-locked, no hard black outline.
    cx, cy, cr = 1000, 300, 30
    K.draw_disc(d, cx, cy, cr, fill=BONE, outline=None, seed=3035)
    K.draw_disc(d, cx, cy, int(cr * 0.45), fill=PAPER, outline=None, seed=3036)

    # The atmosphere, and what is left of it. The two must NOT be concentric at the
    # same radius — the old card drew the ragged shell at ~1.0 r, so it landed on
    # top of the envelope and the pair read as one circle with a coloured rim.
    # The survivor is 0.60 r, so the loss is legible as loss.
    ex, ey, er = 480, 390, 110
    K.draw_outline(d, _ragged_circle(ex, ey, er, seed=3040, h3=0.030, h5=0.018),
                   color=BONE, width=K.DETAIL, closed=True, seed=3041,
                   wobble=2.2, wavelength=170.0)
    K.draw_outline(d, _ragged_circle(ex, ey, er * 0.60, seed=3045, h3=0.075, h5=0.048),
                   color=AMBER, width=K.DETAIL, closed=True, seed=3046,
                   wobble=2.4, wavelength=95.0)

    # Two diagram labels, placed clear of the character (whose limbs reach x=457)
    # and clear of the beam band. Neither restates the caption.
    stamp = T.load_font(T.STAMP_PX, bold=False)
    _draw_centered(d, "ATMOSPHERE", 618, 238, BONE, stamp, INK, T.STAMP_STROKE)
    _draw_centered(d, "ALL THAT'S LEFT", 612, 490, AMBER, stamp, INK, T.STAMP_STROKE)
    d.line([(573, 246), (509, 291)], fill=BONE + (170,), width=K.FINE)
    d.line([(550, 497), (527, 436)], fill=AMBER + (170,), width=K.FINE)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# ---------------------------------------------------------------------------
# Card 31 — close_finale (bone, void)
# ---------------------------------------------------------------------------

def render_close_finale(card, planet="PSR B1257+12"):
    """'THREE ROCKS AND ONE COLLAPSED CORE. TURNING, FOREVER.' The whole system at
    once: planet_periods' three orbits re-drawn at 0.75 scale, the three rocks on
    them, and one spin tick on the core limb. The tick is the only thing that moves
    and it never decelerates — that is the whole word 'forever'.

    The system sits at cx=800, not the schedule's 900: each name now sits directly
    ABOVE/BESIDE its own rock with a ~90 px leader, and at cx=900 the outer orbit's
    right edge (1223) left no room for a legible 'POLTERGEIST' to sit anywhere but
    back across the diagram. The character at x=400 is untouched and still clear of
    the inner orbit (leftmost 672)."""
    img = Image.new('RGB', (C.W, C.H), PAL['deep'])
    C.void_backdrop(img, seed=3100, stars=140)

    cx, cy, cr = 800, 340, 26
    d = ImageDraw.Draw(img, 'RGBA')

    # planet_periods' ellipses (rx 170/300/430, ry 58/100/142) at 0.75 scale about
    # the new core. Flat 2 px BONE — never a gradient, never violet type.
    rings = ((128.0, 44.0), (225.0, 75.0), (323.0, 107.0))
    for rx, ry in rings:
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                  outline=BONE + (190,), width=K.FINE)

    # The three rocks on their rings: Draugr inner, Phobetor middle, Poltergeist
    # outer. C.space_body is the matte painterly treatment — wavy contour bands, no
    # black outline, no soft-focus halo.
    placement = (
        (0, 80.0, 14, 2),    # Draugr     — innermost, 0.02 Earth, the Moon-ish speck
        (1, -10.0, 17, 3),   # Phobetor   — 3.9 Earth
        (2, -57.0, 25, 4),   # Poltergeist— 4.3 Earth
    )
    discs = []
    for ring, ang, r, bands in placement:
        a = math.radians(ang)
        px_ = cx + rings[ring][0] * math.cos(a)
        py_ = cy + rings[ring][1] * math.sin(a)
        discs.append((px_, py_, r))
        img = C.space_body(img, px_, py_, r, seed=3110 + ring * 13, bands=bands)
    d = ImageDraw.Draw(img, 'RGBA')

    # The collapsed core — FLAT. close_finale is not on the beat's gradient_rule
    # list, so it gets a flat disc and a flat inner disc, no radial ramp.
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=BONE)
    d.ellipse([cx - cr * 0.48, cy - cr * 0.48, cx + cr * 0.48, cy + cr * 0.48],
              fill=PAPER)

    # ONE spin tick on the core limb — 4 px (a medium mark), running from the limb
    # out to 1.45r. The frame generator steps it 90 deg per 0.25 s stamp and never
    # slows it; nothing else on this card moves.
    ta = math.radians(FINALE_TICK_DEG)
    d.line([(cx + cr * math.cos(ta), cy + cr * math.sin(ta)),
            (cx + cr * 1.45 * math.cos(ta), cy + cr * 1.45 * math.sin(ta))],
           fill=BONE, width=K.DETAIL)

    # Bone labels with short leaders, each one beside its OWN rock. C.hero_word
    # stamps them at the canon planet-label size with edge + title-strip clamping;
    # the leader is drawn from whichever corner of the returned box actually points
    # at the rock, so a clamped label still leads from the correct side.
    dl = ImageDraw.Draw(img)
    for text, (lx, ly), (tx, ty, _r) in zip(
            ("DRAUGR", "PHOBETOR", "POLTERGEIST"),
            ((822, 500), (1150, 420), (1120, 150)),
            discs):
        bx, by, bw, bh = C.hero_word(dl, text, lx, ly, BONE, stroke_rgb=INK,
                                     stroke_width=3, px=T.LABEL_PX, margin=40)
        ax = min(max(tx, bx), bx + bw)
        ay = min(max(ty, by), by + bh)
        d.line([(ax, ay), (tx, ty)], fill=BONE + (150,), width=K.FINE)

    C._header(img, planet, paper_band=True)
    C._draw_stickman(img, card, theme='dark')
    C._caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


RENDERERS = {
    'close_bother': render_close_bother,
    'close_no_burn': render_close_no_burn,
    'close_formed': render_close_formed,
    'close_radiation': render_close_radiation,
    'close_finale': render_close_finale,
}


def register(mapping=None):
    """Merge these renderers into lib.cardframe's dispatch table. Called by the
    frame generator, not at import time."""
    C.register(RENDERERS if mapping is None else mapping)
    return RENDERERS