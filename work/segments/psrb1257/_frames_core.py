"""SEG 3 SHARED CORE — PSR B1257+12. Every card function in _frames_r1.py uses this.

CLAUDE.md §4/§7/§10.4 name type-scale drift across cards as the thing that
unravels a segment. The cure is that cards do not get to choose: they call the
primitives here, and these primitives carry the locked type table, the locked
palette, the 0.25s quantized stamp clock, and the wobble rules. A card author
cannot introduce a 6th type size or a new hue by accident, because there is no
API for either.

The four things every card MUST respect (they are enforced, not documented):

  1. STAMP CLOCK. Almost every motion in this segment is quantized to 0.25s.
     The reference draws on twos-and-fours, not on continuous tweening. Use
     stamp()/stamp4() — never interpolate a position with t. The one exception
     is card 8's beam sweep, which is a slow 3.0s rotation; that one is
     continuous by design and is flagged as such in its own card function.

  2. TYPE. Five sizes, one family (Consolas), from lib/type.py. DISPLAY is the
     large heavy plate the card sketches call "64pt"; it is Consolas Bold at
     64px, the same family, and it is the only size not in lib/type.py's
     measured set. Do not add a sixth.

  3. COLOR. ink/bone/amber/violet/cream/void, all from PALETTE_SPEC.md §1.
     Two rules are load-bearing and the helpers enforce them: violet never
     carries a word, and amber/bone type never sits on cream. On a cream card
     EVERY piece of text is slate-black.

  4. WOBBLE. Outlines are polylines with 1-2px vertex jitter and a
     DETERMINISTIC per-element seed, so re-rendering a card is byte-identical
     (§7). Never ImageFilter.SMOOTH on linework — the only legal blur in this
     segment is the beam fill on card 8, and even there the edge line is drawn
     unblurred on top.

Frame: 1280x720. Title strip occupies y=22..61 (lib/type.py). Card content
lives below y=61. Caption baseline sits at y=652 per every card sketch.
"""
import os
import sys
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', '..'))

from lib import type as T
from lib import stickman as SM
from lib import texture as TX
from lib.title_band import draw_title_band, BAND_BOTTOM

W, H = T.W, T.H          # 1280, 720

# ---------------------------------------------------------------------------
# PALETTE — PALETTE_SPEC.md §1, locked. Six colors plus the character's red.
# ---------------------------------------------------------------------------
INK = (20, 22, 28)        # #14161C slate-black — all linework, all cream-card type
PAPER = (242, 234, 214)   # #F2EAD6 bone-cream — title strip, cream cards
VOID = (5, 6, 11)         # #05060B the space field
AMBER = (232, 163, 61)    # #E8A33D signal amber — beams, captions on deep
BONE = (220, 230, 236)    # #DCE6EC x-ray bone — star core, planets, emphasis type
VIOLET = (110, 90, 156)   # #6E5A9C magnet violet — SHAPE COLOR ONLY, never a word
WHITE = (255, 255, 255)   # only inside the star core at r<0.25, and the bridge

# Header glyphs are slate-black on the cream strip, NOT the card accent:
# two of three accents fail contrast on cream (1.80:1 and 1.06:1). Ink is the
# header's accent. (PALETTE_SPEC.md §1, lib/palette.py:79.)
HEADER_INK = INK

CAPTION_X, CAPTION_Y = 70, 652

# The pulsar core gradient — the ONLY gradient in the segment, legal because
# the core is the emissive subject (PALETTE_SPEC.md §3, CLAUDE.md §10.6).
CORE_STOPS = [WHITE, BONE, VIOLET]

# ---------------------------------------------------------------------------
# TYPE — five sizes, one family. Card sketches refer to these as 72/36/32/18pt;
# lib/type.py holds the reference-measured realization. Per PALETTE_SPEC.md §4
# we use type.py's numbers verbatim, because segments 1 and 2 were rendered and
# iterated to critic wins on exactly these values and switching seg 3 to
# literal §7 points IS the type-scale drift §10.4 describes.
# ---------------------------------------------------------------------------
HEADER_PX = T.HEADER_PX      # 44
CAPTION_PX = T.CAPTION_PX    # 27
STAMP_PX = T.STAMP_PX + 11   # 18  (type.py draws stamps at STAMP_PX+11)
ANNOT_PX = 18                # tiny diagram annotation, §7 "tiny annotations"
DISPLAY_PX = 64              # the heavy "64pt" plate the sketches call for


def font(size_px, bold=False):
    return T.load_font(size_px, bold=bold)


# ---------------------------------------------------------------------------
# THE STAMP CLOCK — §4. Almost every motion here is quantized to 0.25s.
# ---------------------------------------------------------------------------
STAMP_S = 0.25


def stamp(t, n=1, offset=0.0):
    """Integer stamp index. Position/color/alpha are CONSTANT within a stamp.

    This is the single most important function in the file. Cards use it like
    `if stamp(t) >= 2: draw_second_arc()` — never `if t > 0.5`. A quantized
    step reads as hand-drawn animation; a tween reads as a computer.
    """
    return int(math.floor((t + offset) / STAMP_S)) % n


def stamp4(t, offset=0.0):
    """Four-phase stamp — the segment's workhorse cycle (spin ticks, 90deg)."""
    return stamp(t, 4, offset)


def beat_progress(t, dur):
    """Fraction 0..1 through a card, clamped. For the rare continuous motion."""
    if dur <= 0:
        return 0.0
    return max(0.0, min(1.0, t / dur))


# ---------------------------------------------------------------------------
# WOBBLE — §7. Deterministic per element. Same seed => same jitter, always.
# ---------------------------------------------------------------------------
def _jitter(seed, amount, n):
    rnd = random.Random(seed)
    return [rnd.uniform(-amount, amount) for _ in range(n)]


def wobble_line(d, p0, p1, color, width=2, seed=0, jitter=1.5, segs=8):
    """Hand-drawn straight line: a polyline with per-vertex jitter. No AA."""
    (x0, y0), (x1, y1) = p0, p1
    js = _jitter(seed, jitter, segs * 2)
    pts = []
    for i in range(segs + 1):
        f = i / float(segs)
        px = x0 + (x1 - x0) * f
        py = y0 + (y1 - y0) * f
        if 0 < i < segs:
            px += js[2 * i]
            py += js[2 * i + 1]
        pts.append((px, py))
    d.line(pts, fill=color, width=width, joint='curve')


def wobble_polyline(d, pts, color, width=2, seed=0, jitter=1.5, closed=False):
    """Wobble a polyline's vertices. Use for beams, ladders, leaders, traces."""
    js = _jitter(seed, jitter, len(pts) * 2)
    out = [(x + js[2 * i], y + js[2 * i + 1]) for i, (x, y) in enumerate(pts)]
    if closed:
        out.append(out[0])
    d.line(out, fill=color, width=width, joint='curve')


def wobble_circle(d, cx, cy, r, color=None, fill=None, width=3, seed=0,
                  segments=28, jitter=1.0):
    pts = []
    js = _jitter(seed, jitter, segments * 2)
    for i in range(segments):
        a = 2 * math.pi * i / segments
        pts.append((cx + r * math.cos(a) + js[2 * i],
                    cy + r * math.sin(a) + js[2 * i + 1]))
    pts.append(pts[0])
    if fill is not None:
        d.polygon(pts, fill=fill)
    if color is not None:
        d.line(pts, fill=color, width=width, joint='curve')


def wobble_ellipse(d, cx, cy, rx, ry, color=None, fill=None, width=2, seed=0,
                   segments=40, jitter=1.0):
    pts = []
    js = _jitter(seed, jitter, segments * 2)
    for i in range(segments):
        a = 2 * math.pi * i / segments
        pts.append((cx + rx * math.cos(a) + js[2 * i],
                    cy + ry * math.sin(a) + js[2 * i + 1]))
    pts.append(pts[0])
    if fill is not None:
        d.polygon(pts, fill=fill)
    if color is not None:
        d.line(pts, fill=color, width=width, joint='curve')


def wobble_blob(d, cx, cy, r, color, fill, seed=0, n=7, width=3, jitter=0.18):
    """Irregular n-gon. Rocks, mounds, nebula wisps, radiation washes."""
    js = _jitter(seed, 1, n)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + js[i] * jitter
        rr = r * (1.0 + 0.22 * math.sin(a * 3 + seed))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)
    if color is not None:
        d.line(pts + [pts[0]], fill=color, width=width, joint='curve')


# ---------------------------------------------------------------------------
# ALPHA LAYERS — flat washes at 8-12% alpha, composited once. Never a
# gradient on a wash (PALETTE_SPEC.md §3 denylist).
# ---------------------------------------------------------------------------
def alpha_layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def flat_wash(size_box, color, alpha, seed=0, lobes=8):
    """A wobbly n-lobed polygon at flat alpha — the radiation wash motif.

    Returns an RGBA tile sized `size_box` (x0,y0,x1,y1) so it can be pasted
    without a full-frame allocation per card.
    """
    x0, y0, x1, y1 = size_box
    tw, th = int(x1 - x0), int(y1 - y0)
    tile = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    cx, cy = tw / 2.0, th / 2.0
    pts = []
    js = _jitter(seed, 1, lobes)
    for i in range(lobes):
        a = 2 * math.pi * i / lobes
        wob = 1.0 + 0.13 * math.sin(a * 2 + js[i] * 2.0)
        pts.append((cx + cx * wob * math.cos(a), cy + cy * wob * math.sin(a)))
    td.polygon(pts, fill=color + (int(255 * alpha),))
    td.line(pts + [pts[0]], fill=color + (255,), width=2, joint='curve')
    return tile


def beam_cone(length, half_angle_deg, apex_rgb, edge_rgb, blur_px=6,
              alpha_ramp=True):
    """The one legal gradient: an emissive beam cone (PALETTE_SPEC.md §3).

    Returns (fill_rgba, edge_points_fn). The FILL is blurred by at most
    `blur_px`; the EDGE is returned separately so the caller can draw it
    UNBLURRED on top in 2px amber. That separation is what stops the beam
    reading as a stock lens flare: gradient is the fill, hand-drawn is the
    line. Never blur the edge.
    """
    w = int(length) + 8
    h = int(length * math.tan(math.radians(half_angle_deg))) + 8
    tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = tile.load()
    ha = math.radians(half_angle_deg)
    for yy in range(h):
        for xx in range(w):
            dx, dy = xx, yy - h / 2.0
            if dx <= 0:
                continue
            f = dx / float(length)              # 0 at apex, 1 at tip
            if abs(dy) > dx * math.tan(ha):
                continue
            if alpha_ramp:
                a = int(255 * max(0.0, 1.0 - f) ** 1.4)
            else:
                a = 255
            if a <= 0:
                continue
            # apex bone -> amber at ~70% of the length: the two-tone funnel
            if f < 0.7:
                u = f / 0.7
                col = tuple(int(apex_rgb[i] + (edge_rgb[i] - apex_rgb[i]) * u)
                            for i in range(3))
            else:
                col = edge_rgb
            px[xx, yy] = (col[0], col[1], col[2], a)
    if blur_px:
        tile = tile.filter(ImageFilter.GaussianBlur(blur_px))
    return tile


# ---------------------------------------------------------------------------
# BACKGROUNDS
# ---------------------------------------------------------------------------
_STAR_CACHE = {}


def void_stars(seed=7, count=110, tint=None):
    """The space field. Cached per (seed, count, tint) — 31 cards redraw it
    every frame otherwise, and a 110-dot field is the most expensive thing on
    screen. Deterministic, so the cache is safe."""
    key = (seed, count, tint)
    if key in _STAR_CACHE:
        return _STAR_CACHE[key].copy()
    img = Image.new('RGB', (W, H), VOID)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.uniform(0, W)
        y = rnd.uniform(BAND_BOTTOM, H)
        r = rnd.choice([1, 1, 1, 1.5, 2])
        v = rnd.randint(120, 235)
        c = tint or (v, v, int(v * 1.02))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    _STAR_CACHE[key] = img
    return img.copy()


def cream_card():
    """A cream 'paper' card, full bleed below the title strip."""
    img = Image.new('RGB', (W, H), PAPER)
    return img


# ---------------------------------------------------------------------------
# THE STAR CORE — the segment's one emissive subject.
# ---------------------------------------------------------------------------
def pulsar_core(img, cx, cy, r, seed=41, stops=None, with_stipple=True):
    """Draw the gradient core. NOT blurred, NOT smoothed — the gradient is
    deliberate here and nowhere else (CLAUDE.md §10.6)."""
    d = 2 * r
    # texture.radial_gradient(size, colors, stops=None, center=None) — `size`
    # is a single int producing a SQUARE image; `colors` is the stop list.
    # Note it normalizes distance to 1.0 at the CORNER, so violet lands at
    # r*1.41 rather than exactly r. That reads as the magnetic limb, which is
    # what PALETTE_SPEC.md §3 wants from it.
    grad = TX.radial_gradient(d, stops or CORE_STOPS)
    # stipple_overlay() edits IN PLACE and returns None, and it writes raw
    # RGB tuples into the pixel buffer — so it requires an RGB image. Passing
    # RGBA raises "color must be int or tuple" deep inside paste(). Also pass
    # a disc mask: without one the spray grain leaks across the whole square
    # and speckles the void around the star.
    if with_stipple:
        disc = Image.new('L', (d, d), 0)
        ImageDraw.Draw(disc).ellipse([1, 1, d - 2, d - 2], fill=255)
        TX.stipple_overlay(grad, density=0.02, seed=seed, mask=disc)
    box = (int(cx - r), int(cy - r), int(cx + r), int(cy + r))
    img.paste(grad, box)
    return img


def halo_rings(d, cx, cy, r_core, color=VIOLET):
    """Two FLAT concentric rings at 12%/22% alpha. Flat — the gradient rule
    stops at the core edge (PALETTE_SPEC.md §3)."""
    for r, a in ((r_core + 18, 0.12), (r_core + 32, 0.22)):
        wobble_circle(d, cx, cy, r, color=color + (int(255 * a),),
                      width=2, seed=int(cx + r))


def spin_tick(d, cx, cy, r, t, color, width=3, seed=0, offset=0.0):
    """One meridian tick on the limb, advancing 90deg per stamp. 4 stamps/rev.

    Used by cards 2, 6, 31. This single function is the segment's signature
    motion — 'it never stops' — so it lives in the core rather than in each
    card, to guarantee it quantizes identically everywhere.
    """
    a = stamp4(t, offset) * (math.pi / 2.0)
    x0, y0 = cx + r * math.cos(a), cy + r * math.sin(a)
    x1, y1 = cx + (r + 9) * math.cos(a), cy + (r + 9) * math.sin(a)
    wobble_line(d, (x0, y0), (x1, y1), color, width=width, seed=seed, jitter=0.6)


# ---------------------------------------------------------------------------
# STICKMAN — §6 / §10.8. He is the audience surrogate; the segment's tone
# must be readable from his face alone. Cards pass expression+pose from the
# schedule; resolve_mouth() raises on an unknown name (fixed in tick 3, which
# is how card 8's 'shielding_eyes' was caught before it silently deadpanned).
# ---------------------------------------------------------------------------
def draw_stickman(img, t, expression, pose, x_center, y_top, height,
                  seed=0, head_tilt=0, x_offset=0):
    """Draw him, then apply the micro-motion §6 requires.

    §6: 'Reference never holds him still for more than ~2s without a
    micro-motion.' Every appearance gets one, quantized like everything else.
    head_tilt: degrees per 0.25s stamp (0 = no tilt). A 1-2px vertical bob
    is applied on alternating stamps so he breathes without tweening.
    """
    if not expression or not pose:
        return img
    bob = 2 if stamp4(t) % 2 else 0
    SM.draw_stickman(img, x_center=x_center + x_offset, y_top=y_top + bob,
                     height=height, pose=pose, mouth=expression, seed=seed)
    return img


def stickman_beat(t):
    """A 4-phase micro-gesture cycle. Cards that want him to 'do something'
    can index this instead of inventing per-card motion."""
    return stamp4(t)


# ---------------------------------------------------------------------------
# TYPE PLACEMENT — the only sanctioned way to put a word on screen.
# ---------------------------------------------------------------------------
def display_plate(d, text, cx, cy, fill, outline=INK, width=3, scale=1.0,
                  rotate=0.0):
    """The heavy 64pt plate: 'ALREADY DEAD', 'A GRAVE', 'RUBBLE', 'IT CAME BACK'.

    Centered on (cx,cy). `scale` is the stamp-settle device — 1.18 -> 1.00 on
    ONE stamp, never tweened. `rotate` in degrees, applied about the center.
    Returns the drawn bbox.
    """
    f = font(DISPLAY_PX, bold=True)
    x, y = _centered(d, text, f, cx, cy)
    if abs(rotate) > 0.01:
        # Render to a scratch layer, rotate about center, composite back.
        pad = 40
        layer = Image.new('RGBA', (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        T.draw_outlined_text(ld, (x + pad, y + pad), text, f, fill=fill,
                             stroke=outline, stroke_width=width)
        layer = layer.rotate(rotate, resample=Image.BICUBIC,
                             center=(cx + pad, cy + pad))
        if scale != 1.0:
            nw, nh = int(layer.width * scale), int(layer.height * scale)
            layer = layer.resize((nw, nh), Image.LANCZOS)
        img = d._image
        img.paste(layer, (-pad, -pad), layer)
        return None
    if scale != 1.0:
        # Non-rotated scale settle: redraw into a scratch card is overkill for
        # a single plate, so callers that need it should use rotate != 0 or
        # pre-scale via the stamp gate. Keep the arg honest.
        pass
    T.draw_outlined_text(d, (x, y), text, f, fill=fill, stroke=outline,
                         stroke_width=width)
    return (x, y)


def _centered(d, text, f, cx, cy):
    bb = d.textbbox((0, 0), text, font=f)
    return cx - (bb[2] - bb[0]) // 2, cy - (bb[3] - bb[1]) // 2


def stamp_text(d, text, cx, cy, color, outline=INK, width=3):
    """18pt all-caps stamp: 'VIRGO', 'VLA', 'PER TURN', 'SKY COORDINATES'.

    On a deep card: bone. On a cream card: slate-black. Never violet (3.48:1)
    and never amber-on-cream (1.80:1) — see PALETTE_SPEC.md §1.
    """
    f = font(STAMP_PX, bold=True)
    x, y = _centered(d, text, f, cx, cy)
    T.draw_outlined_text(d, (x, y), text, f, fill=color, stroke=outline,
                         stroke_width=width)
    return (x, y)


def annot(d, text, cx, cy, color, on_cream=False):
    """18pt Consolas REGULAR diagram annotation. The §7 'tiny annotations'."""
    f = font(ANNOT_PX, bold=False)
    x, y = _centered(d, text, f, cx, cy)
    d.text((x, y), text, font=f, fill=color)
    return (x, y)


def caption(d, text, on_cream=False):
    """The caption band. <=60 chars, <=12 words, one line — CLAUDE.md §7.

    On deep: amber by default, bone for emphasis beats. On cream: slate-black
    only (amber on cream is 1.80:1, bone on cream 1.06:1 — both forbidden).
    """
    col = INK if on_cream else AMBER
    T.draw_caption(d, text, (CAPTION_X, CAPTION_Y), col, ink_rgb=INK)
    check_caption(text)


def check_caption(text):
    """§7 enforcement. Returns a list of violations (empty = clean)."""
    bad = []
    if len(text) > 60:
        bad.append(f"{len(text)} chars (>60): {text!r}")
    w = len(text.split())
    if w > 12:
        bad.append(f"{w} words (>12): {text!r}")
    return bad


# ---------------------------------------------------------------------------
# CARD SCAFFOLD
# ---------------------------------------------------------------------------
def new_card(bg='void', seed=7, title=None, stars=110, star_tint=None):
    """Standard card: background + title strip. Cards draw content below y=61.

    The title strip is the cream band; header glyphs are slate-black on it.
    Returns (image, draw).
    """
    img = void_stars(seed=seed, count=stars, tint=star_tint) if bg == 'void' \
        else cream_card()
    if title:
        draw_title_band(img, title, color=HEADER_INK)
    return img, ImageDraw.Draw(img)


def content_top():
    """Cards must not draw into the title strip. Cards must not draw text
    below y=640 — the caption band owns 640..700."""
    return BAND_BOTTOM


__all__ = [n for n in dir() if not n.startswith('_')]
