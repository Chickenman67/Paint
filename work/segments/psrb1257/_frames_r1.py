# work/segments/psrb1257/_frames_r1.py
# Round 1 frame generator — segment 3, PSR B1257+12 (the pulsar planets).
#
# BUILDER FIREWALL: this file was written without reading work/ref_full.mp4,
# anything under work/ref/, any reference transcript, or any critic_blind*
# directory. Every drawing decision below comes from CLAUDE.md sections 4/6/7,
# this segment's PALETTE_SPEC.md, and the `sketch` prose carried in
# round_1_card_schedule.json. `work/ref/` appears in PALETTE_SPEC.md as a
# citation only; it is not read here.
#
# WHAT THIS FILE IS
#   A pure function of (card, time). Read the card schedule at RUN TIME, look
#   up the renderer by card id, render PNG frames. The schedule is re-snapped
#   by _align_r1.py before every render, so timings are read, never computed.
#
# LOCKED INPUTS (do not re-derive here)
#   type scale   : 44 header / 64 heavy / 27 caption / 18 stamp+tiny
#                  (round_1_card_schedule.json `type_scale`, the reference-
#                  measured realization of the CLAUDE.md section 7 table, as
#                  mandated by PALETTE_SPEC.md section 4)
#   palette      : 6 colors + the one banned red. See LOCKED below.
#   geometry     : title strip y=22..60, art y=61..719, caption x=70
#
# THE RED RULE
#   work/lib/stickman.py SHIRT = (200,50,50) is the only red on screen. No card
#   accent, banner, limb, glow or caption in this segment may be red; the alert
#   color is amber. `assert_locked_color` plus the `--verify` red-pixel audit
#   enforce it mechanically.
#
# MOTION
#   Every motion is quantized to 0.25 s stamps (schedule geometry.motion_rule).
#   No smooth tweens anywhere, including the stickman — he never holds still
#   for more than one stamp.

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from lib import stickman as sm
from lib import texture
from lib import title_band
from lib import type as T

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 720
FPS = 30

# --- Card anatomy (CLAUDE.md section 7, from the schedule geometry) ---------
ART_TOP = 61
ART_BOT = 719
CAPTION_X = 70
CAPTION_Y = 652
CAPTION_MAX_W = 1100

# The schedule gives every stickman feet_y 680 or 700, which is INSIDE the
# caption band. Drawing him there would put his legs through the caption text
# and break the three-band rule, so feet are clamped to 626 (the top of the
# caption band) and the figure keeps the schedule's HEIGHT, which is what the
# sketches actually care about ("the biggest figure so far"). TOP_LIMIT keeps
# his head clear of the title strip. Max drawable height = 560 = the largest
# height the schedule asks for, so no card loses scale.
FEET_LIMIT = 626
TOP_LIMIT = 66

STAMP = 0.25   # seconds — the quantization period for every motion


def stamp_index(t):
    """Quantized motion clock. Everything animated keys off this, never off a
    continuous t, per the schedule's motion_rule."""
    return int(math.floor(t / STAMP))


# --- The locked palette (PALETTE_SPEC.md section 1) --------------------------
INK = (20, 22, 28)          # slate-black   #14161C
PAPER = (242, 234, 214)     # bone-cream    #F2EAD6
DEEP = (5, 6, 11)           # void          #05060B
AMBER = (232, 163, 61)      # signal amber  #E8A33D
BONE = (220, 230, 236)      # x-ray bone    #DCE6EC
VIOLET = (110, 90, 156)     # magnet violet #6E5A9C
SHIRT = sm.SHIRT            # (200,50,50) — the character's, never a card's
WHITE = (255, 255, 255)     # star-core centre stop only (r < 0.25)

LOCKED = (INK, PAPER, DEEP, AMBER, BONE, VIOLET, WHITE)

ACCENTS = {
    'cream': PAPER,
    'bone': BONE,
    'amber': AMBER,
    'violet': VIOLET,
}


def assert_locked_color(rgb, where):
    """Fail loudly on an off-palette color. Cheaper than finding a stray hue in
    the critic's frame diff and cheaper than shipping it."""
    c = tuple(int(v) for v in rgb[:3])
    if c not in LOCKED:
        raise ValueError(
            '[%s] %r is not one of the six locked segment colors %r '
            '(red is reserved for the stickman shirt)'
            % (where, c, LOCKED))
    return c


# --- Fonts: the five locked sizes, one family (CLAUDE.md section 7) ---------
F_HEADER = T.load_font(T.HEADER_PX, bold=True)     # 44
F_HEAVY = T.load_font(64, bold=True)               # 64
F_CAPTION = T.load_font(T.CAPTION_PX, bold=False)  # 27
F_CAPTION_B = T.load_font(T.CAPTION_PX, bold=True)
F_STAMP = T.load_font(18, bold=True)               # 18
F_TINY = T.load_font(18, bold=False)               # 18

HEADER_TEXT = 'PSR B1257+12'


# --- Text helpers ------------------------------------------------------------

def _text_w(font, text):
    x0, _, x1, _ = font.getbbox(text)
    return x1 - x0


def draw_header_band(img):
    """Title strip: slate-black on bone-cream, no stroke. Ink is the header's
    accent because two of the three card accents are illegible on cream
    (1.80:1 and 1.06:1) — PALETTE_SPEC.md section 1."""
    title_band.draw_title_band(img, HEADER_TEXT, color=INK, band_color=PAPER)


def draw_caption(draw, text, on_cream=False):
    """One line, 27px, 4px ink outline (type.py's measured caption style).
    Amber on void, slate-black on cream — the two the spec allows."""
    if not text:
        return
    if len(text) > 60:
        raise ValueError('caption is %d chars, max 60: %r' % (len(text), text))
    if len(text.split()) > 12:
        raise ValueError('caption is %d words, max 12: %r'
                         % (len(text.split()), text))
    w = _text_w(F_CAPTION, text)
    if w > CAPTION_MAX_W:
        raise ValueError('caption is %dpx wide, budget %d: %r'
                         % (w, CAPTION_MAX_W, text))
    fill = INK if on_cream else AMBER
    T.draw_caption(draw, text, (CAPTION_X, CAPTION_Y), color_rgb=fill)


def draw_heavy(draw, text, cx, cy, fill, outline_px=3, rot=0.0, scale=1.0):
    """64pt Consolas Bold with a 3px slate-black outline. rot/scale are used by
    the stamp-settle beats; they snap between values on one stamp, never tween."""
    assert_locked_color(fill, 'heavy/%s' % text[:12])
    size = 64
    if scale != 1.0:
        size = int(round(64 * scale))
    font = T.load_font(size, bold=True)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    px, py = cx - w / 2 - x0, cy - h / 2 - y0
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC,
                             center=(cx, cy))
        ld = ImageDraw.Draw(layer)
    ld.text((px, py), text, font=font, fill=fill + (255,),
            stroke_width=outline_px, stroke_fill=INK + (255,))
    layer.putalpha(layer.split()[3])
    return layer


def draw_stamp(draw, text, cx, cy, fill, on_cream=False):
    """18pt all-caps Consolas Bold, 1px ink outline. Amber on void, ink on
    cream. Never violet (3.48:1) — assert_locked_color does not stop that, so
    the call sites do."""
    if fill is VIOLET:
        raise ValueError('violet never carries a word (3.48:1): %r' % text)
    assert_locked_color(fill, 'stamp/%s' % text[:12])
    font = F_STAMP
    x0, y0, x1, y1 = font.getbbox(text)
    w, h = x1 - x0, y1 - y0
    T.draw_outlined_text(draw, (cx - w / 2 - x0, cy - h / 2 - y0), text, font,
                         fill=fill, stroke=INK, stroke_width=1)


def draw_tiny(draw, text, cx, cy, fill=None, on_cream=False):
    """18pt Consolas Regular, no stroke. Tiny annotations on diagrams.
    Bone on void, ink on cream. Never violet."""
    fill = INK if on_cream else (fill or BONE)
    if fill is VIOLET:
        raise ValueError('violet never carries a word (3.48:1): %r' % text)
    assert_locked_color(fill, 'tiny/%s' % text[:12])
    x0, y0, x1, y1 = F_TINY.getbbox(text)
    w, h = x1 - x0, y1 - y0
    draw.text((cx - w / 2 - x0, cy - h / 2 - y0), text, font=F_TINY, fill=fill)


def draw_tiny_at(draw, text, x, y, fill=None, on_cream=False):
    fill = INK if on_cream else (fill or BONE)
    if fill is VIOLET:
        raise ValueError('violet never carries a word: %r' % text)
    assert_locked_color(fill, 'tiny/%s' % text[:12])
    x0, y0, _, _ = F_TINY.getbbox(text)
    draw.text((x - x0, y - y0), text, font=F_TINY, fill=fill)


# --- Wobble primitives (CLAUDE.md section 7: 3px figure / 2px diagram / 1px
# fine; deterministic per-element seed; no anti-aliasing on linework) --------

def seed_of(*parts):
    """Deterministic seed from a string. Python's str hash is salted per
    process, so use a stable digest instead — re-renders must be byte-stable."""
    import hashlib
    return int(hashlib.md5('|'.join(str(p) for p in parts).encode('utf-8'))
               .hexdigest()[:8], 16)


def wob_line(draw, p0, p1, color, width=2, seed=0, jitter=1.5, segs=8):
    rng = random.Random(seed)
    x0, y0 = p0
    x1, y1 = p1
    pts = []
    for i in range(segs + 1):
        t = i / segs
        pts.append((x0 + (x1 - x0) * t + rng.uniform(-jitter, jitter),
                    y0 + (y1 - y0) * t + rng.uniform(-jitter, jitter)))
    draw.line(pts, fill=color, width=width)
    return pts


def wob_poly(draw, pts, color, fill=None, width=2, seed=0, jitter=1.2,
             close=True):
    rng = random.Random(seed)
    wp = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter))
          for x, y in pts]
    if fill is not None:
        draw.polygon(wp, fill=fill)
    if width > 0:
        draw.line(wp + ([wp[0]] if close else []), fill=color, width=width)
    return wp


def wob_circle(img, cx, cy, r, color, fill=None, width=2, seed=0, segs=28,
               jitter=1.2, fill_alpha=None):
    """Flat-fill wobbly disc. fill_alpha composites the fill through an RGBA
    layer so a translucent violet/amber shape can sit on the void without a
    gradient (flat only — the denylist forbids a wash gradient)."""
    rng = random.Random(seed)
    pts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rr = r + rng.uniform(-jitter, jitter)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    if fill is not None and fill_alpha is not None:
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).polygon(pts, fill=tuple(fill) + (255,))
        layer.putalpha(layer.split()[3].point(
            lambda v: int(v * fill_alpha)))
        img.paste(layer, (0, 0), layer)
    elif fill is not None:
        ImageDraw.Draw(img).polygon(pts, fill=fill)
    if width > 0 and color is not None:
        ImageDraw.Draw(img).line(pts + [pts[0]], fill=color, width=width)
    return pts


def wob_ellipse_pts(cx, cy, rx, ry, seed=0, segs=32, jitter=1.0):
    rng = random.Random(seed)
    pts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        pts.append((cx + (rx + rng.uniform(-jitter, jitter)) * math.cos(a),
                    cy + (ry + rng.uniform(-jitter, jitter)) * math.sin(a)))
    return pts


def wob_ellipse(draw, cx, cy, rx, ry, color, width=2, seed=0, segs=32,
                jitter=1.0, fill=None):
    pts = wob_ellipse_pts(cx, cy, rx, ry, seed, segs, jitter)
    if fill is not None:
        draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=color, width=width)
    return pts


def wob_rect(draw, bbox, color, fill=None, width=3, seed=0, jitter=1.5):
    x0, y0, x1, y1 = bbox
    return wob_poly(draw, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                    color, fill=fill, width=width, seed=seed, jitter=jitter)


def flat_ghost(img, bbox, color, alpha, seed=0):
    """A flat translucent plate — used for the radiation wash and the
    irradiated zone. Flat fill, hard wobble edge, 2px outline on top. Never a
    gradient (PALETTE_SPEC.md section 3 denylist)."""
    x0, y0, x1, y1 = bbox
    rng = random.Random(seed)
    wp = []
    n = 10
    for i in range(n):
        f = i / float(n)
        # walk the rectangle perimeter, roughened
        px = x0 + (x1 - x0) * (f * 2.0 if f < 0.5 else 2.0 - f * 2.0)
        py = y0 + (y1 - y0) * (0.0 if f < 0.25 else
                              (0.5 if f < 0.5 else
                               (1.0 if f < 0.75 else 0.5)))
        wp.append((px + rng.uniform(-4, 4), py + rng.uniform(-4, 4)))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon(wp, fill=tuple(color) + (255,))
    layer.putalpha(layer.split()[3].point(lambda v: int(v * alpha)))
    img.paste(layer, (0, 0), layer)
    return wp


# --- Backgrounds -------------------------------------------------------------

def bg_void(img, seed, count=90):
    """The space field: flat void plus bone starfield dots. No gradient, no
    vignette (denylist)."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ART_TOP, W - 1, ART_BOT], fill=DEEP)
    rng = random.Random(seed)
    for _ in range(count):
        x = rng.randint(4, W - 5)
        y = rng.randint(ART_TOP + 4, ART_BOT - 4)
        r = 1 if rng.random() < 0.82 else 2
        c = BONE if rng.random() < 0.72 else VIOLET
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)


def bg_cream(img, seed=None):
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ART_TOP, W - 1, ART_BOT], fill=PAPER)


# --- The pulsar core: the segment's only legal gradient ----------------------

def star_core(img, cx, cy, r, seed, limb=None, limb_px=2, gradient=True):
    """Emissive subject. 3-stop radial #FFFFFF -> BONE -> VIOLET plus a
    deterministic stipple. Legal ONLY here (PALETTE_SPEC.md section 3).
    r<0.25 is the sole pure white in the segment."""
    draw = ImageDraw.Draw(img)
    if gradient:
        side = 2 * r + 6
        grad = texture.radial_gradient(
            side, colors=[WHITE, BONE, VIOLET], stops=[0.0, 0.55, 1.0],
            center=(side / 2.0, side / 2.0))
        mask = Image.new('L', grad.size, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, side - 1, side - 1], fill=255)
        texture.stipple_overlay(grad, density=0.02, color=WHITE, seed=seed)
        img.paste(grad, (int(cx - side / 2), int(cy - side / 2)), mask)
    else:
        wob_circle(img, cx, cy, r, INK, fill=WHITE, width=2, seed=seed)
    if limb is not None:
        assert_locked_color(limb, 'core limb')
        wob_circle(img, cx, cy, r, limb, fill=None, width=limb_px, seed=seed + 5)
    return wob_circle(img, cx, cy, r, INK, fill=None, width=2, seed=seed + 9)


def halo_rings(img, cx, cy, seed, alphas=(0.12, 0.22), radii=(1.42, 1.70)):
    """Two FLAT concentric violet rings. Flat, no gradient — this is the
    'dead star with a magnetic field around it' read."""
    for k, (a, rr) in enumerate(zip(alphas, radii)):
        r = 46 * rr
        wob_circle(img, cx, cy, r, None, fill=VIOLET, width=0,
                   seed=seed + k, fill_alpha=a)


def beam_cone(img, cx, cy, r, angle_deg, length, half_angle_deg, seed):
    """One beam cone: axis ramp alpha 1.0 -> 0.0, apex BONE shifting to AMBER
    at ~70% of the length, MAX 6px blur on the FILL layer only, then the 2px
    AMBER edges drawn UNBLURRED on top. The gradient is the fill; the
    hand-drawn line is the line. This is the one legal gradient in the
    segment (PALETTE_SPEC.md section 3)."""
    import numpy as np
    a = math.radians(angle_deg)
    ha = math.radians(half_angle_deg)
    side = 2 * length + 8
    ox, oy = int(cx - side / 2), int(cy - side / 2)
    apex = (side / 2.0, side / 2.0)

    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32)
    dx, dy = xx - apex[0], yy - apex[1]
    dist = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    # inside the cone? within half_angle of the axis, and forward of the apex
    diff = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi)
    half_w = np.clip(dist, 0, None) * math.tan(ha)
    mask = ((dist <= length) & (diff <= ha + 1e-3) & (dy * math.cos(a) -
            dx * math.sin(a) >= -1e-3)).astype(np.float32)
    t = np.clip(dist / float(length), 0.0, 1.0)
    alpha = mask * (1.0 - t)
    k = np.clip((t - 0.35) / 0.35, 0.0, 1.0)[..., None]
    cols = np.array(BONE, np.float32) * (1 - k) + np.array(AMBER, np.float32) * k

    rgba = np.zeros((side, side, 4), np.float32)
    rgb = np.where(alpha[..., None] > 0, cols, 0.0)
    rgba[..., :3] = np.clip(rgb, 0, 255)
    rgba[..., 3] = np.clip(alpha * 255.0, 0, 255)
    layer = Image.fromarray(rgba.astype(np.uint8), 'RGBA')
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    img.paste(layer, (ox, oy), layer)

    # the hand-drawn edges, unblurred, on top
    draw = ImageDraw.Draw(img)
    e0 = (cx + r * math.cos(a - ha), cy + r * math.sin(a - ha))
    e1 = (cx + (r + length) * math.cos(a - ha), cy + (r + length) * math.sin(a - ha))
    e2 = (cx + (r + length) * math.cos(a + ha), cy + (r + length) * math.sin(a + ha))
    e3 = (cx + r * math.cos(a + ha), cy + r * math.sin(a + ha))
    wob_line(draw, e0, e1, AMBER, width=2, seed=seed + 1, jitter=2.0, segs=14)
    wob_line(draw, e3, e2, AMBER, width=2, seed=seed + 2, jitter=2.0, segs=14)
    wob_line(draw, e1, e2, AMBER, width=1, seed=seed + 3, jitter=2.5, segs=14)


def spin_tick(draw, cx, cy, r, stamp, color=AMBER, n_per_rev=4, width=3,
              seed=0, phase=0.0):
    """A meridian tick advancing n_per_rev steps per revolution, quantized.
    4 stamps per rev unless told otherwise."""
    ang = 2 * math.pi * ((stamp % n_per_rev) / float(n_per_rev) + phase)
    x0 = cx - r * math.cos(ang)
    y0 = cy - r * math.sin(ang)
    x1 = cx + r * math.cos(ang)
    y1 = cy + r * math.sin(ang)
    wob_line(draw, (x0, y0), (x1, y1), color, width=width, seed=seed + stamp,
             jitter=1.0, segs=5)


# --- The stickman -----------------------------------------------------------
# Rendered AFTER the card, BEFORE the caption (section 6). He is positioned and
# scaled from the schedule and never substituted.

def stick_geom(card):
    """(x_center, y_top, height) with feet clamped to the caption band and the
    schedule's height preserved."""
    s = card['stickman']
    h = min(int(s['height']), FEET_LIMIT - TOP_LIMIT)
    x = int(s['x_center'])
    y = FEET_LIMIT - h
    return x, y, h


def stick_offset(card, stamp):
    """The quantized micro-motion offset (dx, dy) for this card at this stamp.
    Shared by the renderer and the red audit so the two cannot drift. He is
    never still for more than one stamp (0.25 s), well inside the ~2 s ceiling
    in CLAUDE.md section 6, and the variant is chosen by pose so a thinking
    beat reads differently from a cowering one."""
    pose = card['stickman']['pose']
    ph = (stamp + seed_of(card['id'], 'sm')) % 8
    if pose == 'pointing':
        return [0, 0, 3, 0, 0, -3, 0, 0][ph], [0, 1, 0, 0, 0, 0, -1, 0][ph]
    if pose in ('shielding_eyes', 'cowering'):
        return [0, 2, 0, -2, 0, 2, 0, -2][ph], [0, 0, 1, 0, 0, 0, 1, 0][ph]
    if pose == 'hands_up':
        return [0, 0, 0, 0, 4, 0, 0, 0][ph], [0, -2, 0, 1, 0, 1, 0, -2][ph]
    if pose in ('shrugged', 'thinker'):
        return [0, 2, 3, 2, 0, -2, -3, -2][ph], [0, 0, 1, 1, 0, 1, 1, 0][ph]
    return [0, 1, 2, 2, 1, 0, -1, -2][ph], [0, 0, 1, 1, 1, 0, 0, 0][ph]


def draw_stickman_card(img, card, t, stamp):
    """Quantized micro-motion. Never still for more than one stamp (0.25 s),
    well inside the ~2 s ceiling in CLAUDE.md section 6. The variant is chosen
    by pose so a thinking beat reads differently from a cowering one.

    Also draws the RED SHIRT, which work/lib/stickman.py defines as
    SHIRT = (200,50,50) at line 24 but never actually paints: `_draw_stickman_body`
    draws head, spine, arms and legs and nothing else. Two of the eighteen mouth
    shapes in that module use a second, near-identical red —
    MOUTH_INTERIOR = (220,100,100) for mouth_oval and (120,30,30) for
    mouth_scream — and this segment's schedule uses `awed_brows` (which maps to
    mouth_oval) on cards 3, 10 and 23. So the shirt is drawn here rather than by
    editing a shared lib three other segments render through, and the two mouth
    interiors are re-filled INK on this segment only. See the report: this is
    the one place where a deviation from lib/stickman.py was required.
    """
    s = card['stickman']
    expression = s['expression']            # let resolve_mouth raise
    mouth_fn = sm.resolve_mouth(expression)  # loud failure, never a default
    pose = s['pose']
    x, y, h = stick_geom(card)
    dx, dy = stick_offset(card, stamp)
    cx, ytop = x + dx, y + dy
    draw_shirt(img, cx, ytop, h, seed=seed_of(card['id'], 'shirt'))

    # The lib draws the body AND the mouth in one call, and `draw_stickman`
    # paints the mouth LAST — so the flattened face has to go on top of the
    # body, not under it. Order below is load-bearing.
    sm.draw_stickman(img, x_center=cx, y_top=ytop, height=h,
                     pose=pose, mouth=expression,
                     seed=seed_of(card['id'], pose, 'body'))

    # Re-draw the face onto a scratch layer, flatten ANY interior fill to INK
    # (segment-local: keeps the shirt the only red), then composite on top.
    #
    # No sentinel is needed: the scratch is pure black everywhere the mouth did
    # not draw, so "max channel > 0" IS the mouth's mask, exactly. An earlier
    # per-channel sentinel approach reported the R channel as unused because
    # mouth_oval's MOUTH_INTERIOR is (220,100,100) — redder than the black
    # background it was being compared against. Taking the max over channels
    # avoids that comparison entirely.
    scratch = Image.new('RGB', (W, H), (0, 0, 0))
    sdraw = ImageDraw.Draw(scratch)
    head_r = int(h / 8.0)
    mouth_cy = ytop + head_r + int(head_r * 0.4)
    mouth_fn(sdraw, cx, mouth_cy, scale=max(0.8, h / float(sm.DEFAULT_HEIGHT)))
    pw, ph = 4 * head_r, 3 * head_r
    ox, oy = cx - 2 * head_r, mouth_cy - int(1.5 * head_r)
    patch = scratch.crop((ox, oy, ox + pw, oy + ph))
    r, g, b = patch.split()
    mask = ImageChops.lighter(ImageChops.lighter(r, g), b)
    patch.paste(INK, (0, 0, pw, ph), mask)
    img.paste(patch, (ox, oy))


def draw_shirt(img, cx, y_top, height, seed=0):
    """The canonical red shirt: a wobbly 2px-outlined trapezoid across the
    chest, slate-black outline, SHIRT fill. Same silhouette on every card so
    the audience can spot him (CLAUDE.md section 6). Its geometry is derived
    from the same head_r/hip_y the lib body uses, so it always sits on the
    chest and never on the arms."""
    head_r = int(height / 8.0)
    neck_y = y_top + 2 * head_r
    hip_y = neck_y + int(height * 0.35)
    half_top = int(head_r * 0.95)
    half_bot = int(head_r * 1.15)
    wob_poly(ImageDraw.Draw(img),
             [(cx - half_top, neck_y + int(head_r * 0.15)),
              (cx + half_top, neck_y + int(head_r * 0.15)),
              (cx + half_bot, hip_y),
              (cx - half_bot, hip_y)],
             INK, fill=SHIRT, width=2, seed=seed, jitter=1.2, close=True)




def card_psr_size(img, card, t, stamp):
    """4. City-sized. The 3-stop gradient core — legal here because the star is
    the emissive subject — with the 20 KM scale bracket and its annotation."""
    bg_void(img, 4)
    draw = ImageDraw.Draw(img)
    br = 54 + int(3 * math.sin(2 * math.pi * (stamp % 4) / 4.0))
    star_core(img, 900, 330, br, 41)
    draw_tiny(draw, '20 KM ACROSS', 900, 404)
    wob_line(draw, (760, 430), (1040, 430), BONE, width=3, seed=402)
    for x in (760, 1040):
        wob_line(draw, (x, 418), (x, 442), BONE, width=3, seed=403 + x)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_psr_collapse(img, card, t, stamp):
    """5. Fuel ran out, it exploded, the rest collapsed in here. Streaks
    radiate in three quantized length steps, a debris ring of amber blobs draws
    inward on its own stamp, the core flashes to full white at t=0.9 s and then
    SNAPS to r=30 on one stamp. He is shielding his eyes."""
    bg_void(img, 5)
    draw = ImageDraw.Draw(img)
    local = t - card['start']
    for k, length in enumerate((40, 90, 150)):
        if stamp < k:
            continue
        rng = random.Random(500 + k)
        for j in range(9):
            a = rng.uniform(0, 2 * math.pi)
            r0 = 90 + rng.uniform(0, 60)
            x0 = 900 + r0 * math.cos(a)
            y0 = 330 + r0 * math.sin(a)
            wob_line(draw, (x0, y0),
                     (x0 + length * math.cos(a), y0 + length * math.sin(a)),
                     AMBER, width=2, seed=510 + k * 10 + j, jitter=1.5)
    for k in range(9):
        if stamp < k:
            continue
        a = 2 * math.pi * k / 9 + 0.2
        pull = 1.0 - min(1.0, (stamp - k) / 6.0) * 0.45
        cx = 900 + 300 * pull * math.cos(a)
        cy = 330 + 90 * pull * math.sin(a)
        r = 6 + (k * 2) % 9
        wob_circle(img, cx, cy, r, AMBER, fill=AMBER, width=2,
                   seed=530 + k, jitter=1.0)
    r = 30 if local >= 0.9 else 54
    star_core(img, 900, 330, r, 540, gradient=(r > 30))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_psr_spin(img, card, t, stamp):
    """6. That collapse is what makes it spin. Two violet magnetic field arcs
    lofting above and below the poles, an amber tick advancing 90 deg a stamp.
    Visual pace only, not to scale — the narration says milliseconds and the
    discrepancy is the joke, so it is deliberately left unannotated."""
    bg_void(img, 6)
    draw = ImageDraw.Draw(img)
    star_core(img, 900, 330, 30, 601, gradient=False)
    for k, sgn in enumerate((1, -1)):
        pts = [(900 - 150 + 300 * (i / 8.0),
                330 + sgn * (95 - 70 * math.sin(math.pi * (i / 8.0))))
               for i in range(9)]
        wob_poly(draw, pts, VIOLET, width=2, seed=610 + k, jitter=1.5,
                 close=False)
    spin_tick(draw, 900, 330, 30, stamp, AMBER, n_per_rev=4, width=3, seed=620)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_psr_rate(img, card, t, stamp):
    """7. DIAGRAM-ONLY. A bone stopwatch ring carrying 60 ticks with one amber
    tick chasing it. 6.2 ms is the period; 161 is the frequency in Hz and is
    never labelled as a period."""
    bg_void(img, 7)
    draw = ImageDraw.Draw(img)
    cx, cy, rr = 560, 300, 190
    wob_ellipse(draw, cx, cy, rr, rr, BONE, width=2, seed=701)
    for k in range(60):
        a = 2 * math.pi * k / 60
        draw.line([(cx + (rr - 8) * math.cos(a), cy + (rr - 8) * math.sin(a)),
                   (cx + rr * math.cos(a), cy + rr * math.sin(a))],
                  fill=BONE, width=1)
    a = 2 * math.pi * ((stamp * 4 % 25) / 25.0)
    wob_line(draw, (cx + (rr - 16) * math.cos(a), cy + (rr - 16) * math.sin(a)),
             (cx + rr * math.cos(a), cy + rr * math.sin(a)),
             AMBER, width=3, seed=702, jitter=0.6, segs=3)
    star_core(img, cx, cy, 30, 703, gradient=False)
    paste_layer(img, draw_heavy(img, '6 MILLISECONDS', cx, cy, BONE))
    draw_tiny(draw, 'PER TURN', cx, 510)
    draw_caption(draw, card['caption'])


def card_psr_beams(img, card, t, stamp):
    """8. Two opposed beam cones from the poles, rotating as a rigid pair at one
    revolution per 3.0 s, quantized to the beat. He shields his eyes from his
    own punchline."""
    bg_void(img, 8)
    halo_rings(img, 900, 330, 801)
    star_core(img, 900, 330, 30, 802, gradient=False)
    ang = 360.0 * ((t - card['start']) / 3.0)
    for k in range(2):
        beam_cone(img, 900, 330, 30, ang + k * 180.0, 300, 22.0, 810 + k * 7)
    draw = ImageDraw.Draw(img)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_psr_lighthouse(img, card, t, stamp):
    """9. CREAM. A lighthouse in 3 px slate-black with two amber wedges hard
    on/off on a 1.1 s pulse train (a pulse train, not a fade), ON/OFF stamped
    beneath the lamp. Every word on this card is slate-black: amber on cream is
    1.80:1 and bone on cream is 1.06:1, both forbidden."""
    bg_cream(img)
    draw = ImageDraw.Draw(img)
    on = ((t - card['start']) % 1.1) < 0.55
    lx, ly = 1000, 300
    wob_poly(draw, [(lx - 26, 620), (lx + 26, 620),
                    (lx + 16, ly + 40), (lx - 16, ly + 40)],
             INK, fill=None, width=3, seed=901, jitter=1.5)
    wob_rect(draw, (lx - 30, ly - 6, lx + 30, ly + 44), INK, fill=PAPER,
             width=3, seed=902)
    for k in range(3):
        wob_line(draw, (lx - 28, ly + 8 + k * 12), (lx + 28, ly + 8 + k * 12),
                 INK, width=1, seed=903 + k)
    if on:
        for sgn in (1, -1):
            wob_poly(draw, [(lx, ly + 18),
                            (lx + sgn * 300, ly - 222),
                            (lx + sgn * 300, ly + 258)],
                     None, fill=AMBER, width=0, seed=904 + sgn, jitter=3.0)
    draw_stamp(draw, 'ON' if on else 'OFF', lx, 372, INK, on_cream=True)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'], on_cream=True)


def card_psr_name(img, card, t, stamp):
    """10. The name arrives as a STAMP: 64 pt, -3 deg, settling from 1.18 to
    1.00 on ONE stamp. VIRGO top-right, and three bone dots appearing one per
    word of 'three planets'."""
    bg_void(img, 10)
    draw = ImageDraw.Draw(img)
    star_core(img, 880, 300, 30, 1001, gradient=False)
    scale = 1.18 if stamp == 0 else 1.00
    paste_layer(img, draw_heavy(img, 'PSR B1257+12', 880, 300, BONE,
                                rot=-3.0, scale=scale))
    draw_stamp(draw, 'VIRGO', 1080, 120, AMBER)
    for k in range(3):
        if stamp < k:
            continue
        wob_circle(img, 1090 + k * 40, 180, 7, INK, fill=BONE, width=2,
                   seed=1010 + k)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def paste_layer(img, layer):
    """Composite an RGBA text/shape layer, honouring its alpha."""
    img.paste(layer, (0, 0), layer)


# =============================================================================
# CARD RENDERERS — one per card id, signature (img, card, t, stamp) -> None
#
# Every drawing decision traces to the card's own `sketch` string in
# round_1_card_schedule.json plus the palette rules. Nothing here reads the
# reference. The red shirt is the only red; the accents come from the card.
# =============================================================================

def card_hook_dead(img, card, t, stamp):
    """1. Far dead star, flat halo rings, a violet nebula wisp across the
    lower-left third at 8%, 'ALREADY DEAD' stamped ON the star. The first card
    is up at t=0.0 so the header never lands late (CLAUDE.md section 5.5)."""
    bg_void(img, 1)
    halo_rings(img, 980, 300, 101)
    star_core(img, 980, 300, 46, 102, gradient=False)
    flat_ghost(img, (0, 380, 520, 719), VIOLET, 0.08, seed=103)
    draw = ImageDraw.Draw(img)
    paste_layer(img, draw_heavy(img, 'ALREADY DEAD', 980, 300, BONE))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_hook_talking(img, card, t, stamp):
    """2. Still, somehow, talking. Three violet radio arcs at stepped opacity
    on a 0.25 s cycle, plus a meridian tick advancing 90 deg per stamp. He
    points at it."""
    bg_void(img, 2)
    draw = ImageDraw.Draw(img)
    ph = stamp % 3
    for k, (r, op) in enumerate([(110, 0.20), (170, 0.55), (230, 0.15)]):
        a = op if ph == k else op * 0.35
        wob_circle(img, 980, 300, r, None, fill=VIOLET, width=0,
                   seed=200 + k, fill_alpha=a)
    star_core(img, 980, 300, 46, 202, gradient=False)
    spin_tick(draw, 980, 300, 46, stamp, BONE, n_per_rev=4, width=3, seed=203)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_hook_not_alone(img, card, t, stamp):
    """3. The first hot color in the segment: a 2 px amber limb ring, so the eye
    registers the shift. 'A NEUTRON STAR' stamped on the star. Hands up."""
    bg_void(img, 3)
    draw = ImageDraw.Draw(img)
    star_core(img, 980, 300, 46, 302, limb=AMBER, limb_px=2, gradient=False)
    paste_layer(img, draw_heavy(img, 'A NEUTRON STAR', 980, 300, AMBER))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


# =============================================================================
# BEATS B1 HOOK (1-4) / B2 THE PULSAR (5-10) / B4 THE SEARCH (14-21)
# The B2 renderers sit at the top of this file and B4's `how_first` opens the
# B5 block below. The order here is presentational only; RENDERERS is the
# dispatch and does not care.
# =============================================================================

def card_planet_masses(img, card, t, stamp):
    """11. CREAM. A ledger — three 3px rules, one flat slate-black disc per row,
    so the SHAPE carries the fact: one speck, then two near-twin heavies.
    Draugr 0.020, Phobetor 3.9, Poltergeist 4.3 Earth masses; radii stay
    16/40/42. No gradient and no band texture — the three planets are on the
    PALETTE_SPEC.md section 3 denylist. Rows land one per 0.25 s stamp, and a
    row's label only appears once its disc has, so the count reads off the
    picture."""
    bg_cream(img)
    draw = ImageDraw.Draw(img)
    rows = [(620, 16, 'MOON-SIZE'), (860, 40, '4 EARTH'),
            (1120, 42, '4 EARTH')]
    for i, (cx, r, label) in enumerate(rows):
        cy = 180 + i * 120
        wob_line(draw, (560, cy), (1180, cy), INK, width=3, seed=1100 + i)
        if stamp < i:
            continue
        wob_circle(img, cx, cy, r, INK, fill=INK, width=3, seed=1110 + i,
                   jitter=1.0)
        draw_tiny(draw, label, cx, cy + r + 24, INK, on_cream=True)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'], on_cream=True)


def card_planet_minefield(img, card, t, stamp):
    """12. Not a solar system — rubble in a minefield. The pulsar is cropped by
    the title strip, an amber radiation wash spans the frame at 10%, and eleven
    slate-black rock blobs jitter 2 px on their own stamps. He stands INSIDE
    the wash so his black limbs keep full separation (PALETTE_SPEC.md
    section 1: no mid-tone accent may sit behind him). 'RUBBLE' is nudged left
    of the core so the heavy plate and the crop never collide."""
    bg_void(img, 12)
    flat_ghost(img, (340, 120, 1240, 660), AMBER, 0.10, seed=1201)
    draw = ImageDraw.Draw(img)
    for k in range(11):
        gx = 400 + (k % 4) * 200
        gy = 180 + (k // 4) * 130
        jx = 2 if (stamp + k) % 2 == 0 else -2
        jy = 2 if (stamp + k) % 3 == 0 else -2
        r = 8 + (k * 7) % 19
        pts = [(gx + jx + r * math.cos(2 * math.pi * i / 7 + k),
                gy + jy + r * math.sin(2 * math.pi * i / 7 + k) * 0.8)
               for i in range(7)]
        wob_poly(draw, pts, INK, fill=INK, width=2, seed=1220 + k, jitter=1.0)
    star_core(img, 900, 180, 26, 1202, gradient=False)
    draw = ImageDraw.Draw(img)
    paste_layer(img, draw_heavy(img, 'RUBBLE', 760, 400, AMBER))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_planet_periods(img, card, t, stamp):
    """13. DIAGRAM-ONLY. Three concentric BONE orbit ellipses — bone, not
    violet, because violet is a shape color and never carries a word. Inner to
    outer Draugr / Phobetor / Poltergeist at 25 / 67 / 98 days, one dot
    advancing one step per lap. This is the diagram the next three cards talk
    over, so it is drawn to be re-used."""
    bg_void(img, 13)
    draw = ImageDraw.Draw(img)
    cx, cy = 640, 330
    rings = [(170, 58, '25 D', 262), (300, 100, '67 D', 222),
             (430, 142, '98 D', 180)]
    for k, (rx, ry, label, ly) in enumerate(rings):
        wob_ellipse(draw, cx, cy, rx, ry, BONE, width=2, seed=1300 + k)
        pos = (stamp * (k + 1)) % 16
        a = 2 * math.pi * pos / 16.0
        wob_circle(img, cx + rx * math.cos(a), cy + ry * math.sin(a), 9,
                   INK, fill=BONE, width=2, seed=1310 + k)
        wob_line(draw, (cx, cy - ry), (cx, ly + 10), BONE, width=3,
                 seed=1320 + k, jitter=0.8, segs=3)
        draw_tiny(draw, label, cx, ly)
    star_core(img, cx, cy, 24, 1330, gradient=False)
    paste_layer(img, draw_heavy(img, '25 / 67 / 98 DAYS', cx, 510, BONE))
    draw_caption(draw, card['caption'])


def card_how_find(img, card, t, stamp):
    """14. CREAM, deliberately near-empty. A question mark as linework, a
    coffin outline for the 'corpse' half drawn plainly (no gore, no skull), and
    an ear with three concentric arcs for the 'listen' half. The emptiness IS
    the pacing. He thinks."""
    bg_cream(img)
    draw = ImageDraw.Draw(img)
    # question mark, 200 px tall, 2 px wobbly stroke
    qx, qy = 860, 300
    arc = [(qx - 45, qy - 80), (qx - 10, qy - 100), (qx + 40, qy - 88),
           (qx + 45, qy - 50), (qx + 5, qy - 20), (qx, qy + 10)]
    wob_line(draw, arc[0], arc[1], INK, width=2, seed=1401, jitter=2.0, segs=6)
    wob_line(draw, arc[1], arc[2], INK, width=2, seed=1402, jitter=2.0, segs=6)
    wob_line(draw, arc[2], arc[3], INK, width=2, seed=1403, jitter=2.0, segs=6)
    wob_line(draw, arc[3], arc[4], INK, width=2, seed=1404, jitter=2.0, segs=6)
    wob_line(draw, arc[4], arc[5], INK, width=2, seed=1405, jitter=2.0, segs=6)
    wob_circle(img, qx, qy + 52, 9, INK, fill=INK, width=2, seed=1406)
    # coffin outline — plainly, no skull
    wob_rect(draw, (300, 340, 420, 520), INK, fill=None, width=3, seed=1407)
    wob_line(draw, (300, 372), (420, 372), INK, width=3, seed=1408, segs=4)
    # ear + three arcs
    wob_poly(draw, [(1090, 250), (1120, 300), (1090, 350)],
             INK, fill=None, width=2, seed=1409, jitter=1.5)
    for k, r in enumerate((40, 70, 100)):
        wob_circle(img, 1150, 300, r, INK, fill=None, width=2, seed=1410 + k)
    draw = ImageDraw.Draw(img)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'], on_cream=True)


def wob_spike_train(draw, x0, x1, y, n, displace=(3, 6), seed=0, color=BONE,
                    width=2, stamp_shift=0):
    """The wobble made visible: evenly spaced pulses with a couple of peaks
    displaced sideways. Used by how_signature, how_1990 and how_two_years."""
    step = (x1 - x0) / float(n)
    out = []
    for k in range(n):
        cx = x0 + step * (k + 0.5)
        dx = 6 if k in displace else 0
        h = 34
        pts = [(cx + dx, y), (cx + dx, y - h)]
        wob_line(draw, pts[0], pts[1], color, width=width,
                 seed=seed + k + stamp_shift, jitter=0.7, segs=4)
        out.append((cx + dx, y - h))
    return out


def card_how_signature(img, card, t, stamp):
    """15. DIAGRAM-ONLY. A bone timing trace across the frame: nine evenly
    spaced spikes, the 4th and 7th peaks displaced — the wobble drawn rather
    than labelled, with an amber bracket and a TUG label under each."""
    bg_void(img, 15)
    draw = ImageDraw.Draw(img)
    peaks = wob_spike_train(draw, 120, 1180, 300, 9, displace=(3, 6),
                            seed=1500, stamp_shift=stamp)
    for k, px in ((3, peaks[3][0]), (6, peaks[6][0])):
        wob_line(draw, (px - 26, 320), (px + 26, 320), AMBER, width=3,
                 seed=1510 + k, jitter=0.7, segs=4)
        wob_line(draw, (px, 312), (px, 300), AMBER, width=3, seed=1520 + k,
                 jitter=0.5, segs=2)
        draw_tiny(draw, 'TUG', px, 360)
    wob_line(draw, (60, 380), (1220, 380), BONE, width=2, seed=1530)
    paste_layer(img, draw_heavy(img, 'WOBBLE = TUG', 640, 500, BONE))
    draw_caption(draw, card['caption'])


def card_how_1990(img, card, t, stamp):
    """16. A bone waveform panel with the wobbled pulse train re-stamped inside
    it, a 1990 plate settling from 1.15 to 1.00 on one stamp, and a VLA stamp.
    The pulsar was discovered 9 February 1990; the two-year gap on the next
    card is the 1990 -> 1992 wait, not a 'nobody believed him' beat."""
    bg_void(img, 16)
    draw = ImageDraw.Draw(img)
    wob_rect(draw, (560, 180, 1180, 520), BONE, fill=None, width=2, seed=1601)
    wob_spike_train(draw, 590, 1150, 480, 8, displace=(2, 5), seed=1602,
                    width=2, stamp_shift=stamp)
    scale = 1.15 if stamp == 0 else 1.00
    paste_layer(img, draw_heavy(img, '1990', 870, 350, BONE, scale=scale))
    draw_stamp(draw, 'VLA', 1080, 470, BONE)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_how_two_years(img, card, t, stamp):
    """17. A violet TALLY — 24 thin rules grouped 12|12 with a 40 px gap: two
    years of ticks and no words. The signature trace replays once across the
    top half on a 0.25 s stamp."""
    bg_void(img, 17)
    draw = ImageDraw.Draw(img)
    wob_spike_train(draw, 120, 1180, 300, 7, displace=(2, 5), seed=1700,
                    stamp_shift=stamp)
    for k in range(24):
        x = 600 + k * 23
        if k == 12:
            x += 40
        wob_line(draw, (x, 400), (x, 440), VIOLET, width=3, seed=1710 + k,
                 jitter=0.5, segs=2)
    draw_tiny(draw, '2 YEARS', 890, 470)
    paste_layer(img, draw_heavy(img, 'IT CAME BACK', 640, 120, BONE))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_how_grave(img, card, t, stamp):
    """18. The dread card. The core drawn as an ABSENCE — an empty amber ring
    with nothing inside it — over three flat mound shapes. No crosses, no
    headstones, no skulls. 'A GRAVE' sits inside the empty ring. He is the
    biggest figure so far, arms straight down, head six px lower: the slump
    reads without one new line. Per CLAUDE.md section 10.8 this is one of the
    two beats that must carry the stickman as the fate lands."""
    bg_void(img, 18)
    draw = ImageDraw.Draw(img)
    wob_circle(img, 900, 330, 44, AMBER, fill=None, width=2, seed=1801)
    for k, (mx, my, mr) in enumerate([(700, 600, 70), (900, 610, 86),
                                      (1100, 600, 64)]):
        pts = [(mx + mr * math.cos(2 * math.pi * i / 7 + k),
                my + mr * 0.42 * math.sin(2 * math.pi * i / 7 + k))
               for i in range(7)]
        wob_poly(draw, pts, INK, fill=INK, width=2, seed=1810 + k, jitter=1.5)
    paste_layer(img, draw_heavy(img, 'A GRAVE', 900, 300, AMBER))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_how_steady(img, card, t, stamp):
    """19. DIAGRAM-ONLY. A metronome in 2 px bone, pendulum swinging +/-26 deg
    in quantized 0.25 s steps and NEVER pausing — that is the whole meaning of
    the card. The violet plate behind the swing is a shape color and carries no
    word."""
    bg_void(img, 19)
    flat_ghost(img, (120, 280, 480, 560), VIOLET, 0.08, seed=1901)
    draw = ImageDraw.Draw(img)
    wob_poly(draw, [(560, 560), (760, 560), (720, 300), (600, 300)],
             BONE, fill=None, width=2, seed=1902)
    sw = [0, 13, 26, 13, 0, -13, -26, -13][stamp % 8]
    a = math.radians(sw)
    px, py = 660, 320
    ex = px + 210 * math.sin(a)
    ey = py + 210 * math.cos(a)
    wob_line(draw, (px, py), (ex, ey), BONE, width=3, seed=1903, jitter=0.8)
    wob_circle(img, px, py, 10, BONE, fill=None, width=2, seed=1904)
    draw_tiny(draw, 'STEADY', 300, 240)
    draw_tiny(draw, 'NEVER STOPS', 300, 600)
    paste_layer(img, draw_heavy(img, 'STEADY AND RHYTHMIC', 880, 420, BONE))
    draw_caption(draw, card['caption'])


def card_how_tug(img, card, t, stamp):
    """20. One amber beam wedge toward the lower-right over a 6 px-blurred
    fill, and a bone dot that lurches 8 px toward the beam and back on
    alternating stamps — the tug made visible. A schedule ladder with one rung
    lit amber."""
    bg_void(img, 20)
    draw = ImageDraw.Draw(img)
    beam_cone(img, 900, 300, 20, 40.0, 300, 16.0, 2001)
    lx = 1120 + (8 if stamp % 2 == 0 else -8)
    wob_circle(img, lx, 520, 11, BONE, fill=BONE, width=2, seed=2002)
    for k in range(5):
        x = 200 + k * 60
        c = AMBER if k == 2 else BONE
        wob_line(draw, (x, 500), (x, 540), c, width=3, seed=2010 + k,
                 jitter=0.5, segs=2)
    wob_line(draw, (200, 520), (500, 520), BONE, width=2, seed=2020)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


# =============================================================================
# BEAT B4/B5 — THE PAYOFF (21) AND THE NAMING (22-26)
# =============================================================================

def card_how_first(img, card, t, stamp):
    """21. THE PAYOFF. This is the only card that gets the full 3-stop
    gradient core, because it is the only card where the star is the good news.
    The three discs re-stamp out of the two inner orbit rings one per 0.25 s
    stamp, each with a flat 2 px amber ring highlight; 'FIRST EVER' is nudged to
    (880,150) so it does not sit on the core. He is AWE, not fear: relief,
    hands up, and the hands stamp up on the word 'confirmed'."""
    bg_void(img, 21)
    star_core(img, 880, 320, 40, 2101, gradient=True)
    draw = ImageDraw.Draw(img)
    cx, cy = 880, 320
    for k, (rx, ry, r) in enumerate([(170, 58, 18), (300, 100, 22),
                                     (430, 142, 34)]):
        wob_ellipse(draw, cx, cy, rx, ry, BONE, width=2, seed=2110 + k)
        if stamp < k:
            continue
        a = math.radians(200 + k * 40)
        px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
        wob_circle(img, px, py, r, INK, fill=BONE, width=2, seed=2120 + k,
                   jitter=1.0)
        wob_circle(img, px, py, r + 5, AMBER, fill=None, width=2,
                   seed=2130 + k)
    paste_layer(img, draw_heavy(img, 'FIRST EVER', 880, 150, AMBER))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_name_why(img, card, t, stamp):
    """22. The setup for the horror: a flat violet haze band at 9% and five
    flat slate-black 2 px silhouettes drifting 3 px inside it. DELIBERATELY
    ambiguous — they are NOT skulls yet. They resolve on the next card. Violet is
    a shape color and carries no word."""
    bg_void(img, 22)
    flat_ghost(img, (120, 420, 1180, 640), VIOLET, 0.09, seed=2201)
    draw = ImageDraw.Draw(img)
    for k in range(5):
        bx = 220 + k * 200
        by = 500
        d = 3 if (stamp + k) % 2 == 0 else -3
        wob_circle(img, bx + d, by - 40, 18, INK, fill=INK, width=2,
                   seed=2210 + k, jitter=1.0)
        wob_poly(draw, [(bx + d - 22, by + 60), (bx + d - 14, by - 24),
                        (bx + d + 14, by - 24), (bx + d + 22, by + 60)],
                 INK, fill=INK, width=2, seed=2220 + k, jitter=1.0)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_name_three(img, card, t, stamp):
    """23. CREAM. The reveal. Three skull plates — 3 px slate-black circles
    96 px across, two 3 px eye slots, a 3 px jaw rule. Cartoon-flat: no
    gradients, no teeth detail. The reference's detailed teeth-and-tongue mouth
    is copyrighted character design and is NOT copied. Each name settles from
    scale 1.18 to 1.00 on ONE 0.25 s stamp, and the sketch asks for the three
    stamps to land on the three word ONSETS, not on evenly spaced times — the
    schedule's per-card first_word_index is what supplies those, and this
    renderer only ever sees the local stamp, so the names still land one per
    stamp of the card."""
    bg_cream(img)
    draw = ImageDraw.Draw(img)
    for k, (cx, name) in enumerate([(300, 'DRAUGR'), (640, 'PHOBETOR'),
                                    (1000, 'POLTERGEIST')]):
        if stamp < k:
            continue
        wob_circle(img, cx, 280, 48, INK, fill=PAPER, width=3, seed=2310 + k)
        wob_circle(img, cx - 16, 272, 8, INK, fill=INK, width=3, seed=2320 + k,
                   jitter=0.8)
        wob_circle(img, cx + 16, 272, 8, INK, fill=INK, width=3, seed=2330 + k,
                   jitter=0.8)
        wob_line(draw, (cx - 22, 306), (cx + 22, 306), INK, width=3,
                 seed=2340 + k, jitter=1.0)
        wob_line(draw, (cx - 4, 320), (cx, 330), INK, width=3, seed=2350 + k,
                 jitter=0.8, segs=2)
        wob_line(draw, (cx, 330), (cx + 4, 320), INK, width=3, seed=2351 + k,
                 jitter=0.8, segs=2)
        wob_line(draw, (cx - 22, 352), (cx + 22, 352), INK, width=2,
                 seed=2360 + k, jitter=0.8, segs=3)
    draw = ImageDraw.Draw(img)
    for k, (cx, name) in enumerate([(300, 'DRAUGR'), (640, 'PHOBETOR'),
                                    (1000, 'POLTERGEIST')]):
        if stamp < k:
            continue
        paste_layer(img, draw_heavy(img, name, cx, 420, INK,
                                    scale=1.18 if stamp == k else 1.0))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'], on_cream=True)


def card_name_star(img, card, t, stamp):
    """24. The skulls are GONE. This beat ends on the corpse, so the naming lands
    on the star: the 64 pt plate re-stamps over the core, settling 1.18 -> 1.00
    on one stamp. VIRGO stamped top-right (E1, corrected from 'VELA')."""
    bg_void(img, 24)
    star_core(img, 880, 320, 36, 2401, limb=AMBER, limb_px=2, gradient=False)
    draw = ImageDraw.Draw(img)
    scale = 1.18 if stamp == 0 else 1.00
    paste_layer(img, draw_heavy(img, 'PSR B1257+12', 880, 320, AMBER,
                                rot=-3.0, scale=scale))
    draw_stamp(draw, 'VIRGO', 1080, 120, BONE)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_name_coordinates(img, card, t, stamp):
    """25. A star chart: seven vertical and five horizontal 2 px bone rules
    spanning x=560..1180, y=180..560, with 3 px ticks every 60 px. A 2 px
    circle r=18 drops to the crosshair on one 0.25 s stamp and LOCKS, then
    pulses on every stamp after — this is where the thing is. FACT FLAG E6
    (already applied in the schedule): PSR 1257+12 is a SEXAGESIMAL sky
    coordinate, 12h57m right ascension and +12 deg declination. There is no
    base-eight joke and none is drawn here."""
    bg_void(img, 25)
    draw = ImageDraw.Draw(img)
    for k in range(7):
        x = 560 + k * (620 / 6.0)
        wob_line(draw, (x, 180), (x, 560), BONE, width=1, seed=2501 + k,
                 jitter=1.0, segs=10)
    for k in range(5):
        y = 180 + k * 95
        wob_line(draw, (560, y), (1180, y), BONE, width=1, seed=2510 + k,
                 jitter=1.0, segs=10)
    for gx in range(560, 1181, 60):
        wob_line(draw, (gx, 556), (gx, 566), BONE, width=3, seed=2520 + gx,
                 jitter=0.6, segs=2)
    for gy in range(180, 561, 60):
        wob_line(draw, (556, gy), (566, gy), BONE, width=3, seed=2530 + gy,
                 jitter=0.6, segs=2)
    cxp, cyp = 860, 330
    wob_line(draw, (cxp - 30, cyp), (cxp + 30, cyp), BONE, width=3, seed=2540)
    wob_line(draw, (cxp, cyp - 30), (cxp, cyp + 30), BONE, width=3, seed=2541)
    pulse = 1.0 if stamp == 0 else (0.75 if stamp % 2 == 0 else 1.0)
    wob_circle(img, cxp, cyp, 18 * pulse, AMBER, fill=None, width=2, seed=2550)
    draw_tiny(draw, 'SKY COORDINATES', cxp, 600)
    paste_layer(img, draw_heavy(img, 'A SPOT ON THE SKY', cxp, 640, BONE))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_name_just_digits(img, card, t, stamp):
    """26. CREAM, deliberately plain. Four 3 px slate-black digit frames 120 px
    square holding 1 / 2 / 5 / 7 in heavy 64 pt, with 18 pt slate-black
    annotations and a 3 px leader from each annotation up to its frame pair.
    No illustration, no texture, no gradient, nothing else — the flatness IS the
    point: a dead star reduced to a row of numbers. Frames land one per 0.25 s
    stamp; the right ascension half takes 2, the declination half 2. The plate
    is nudged to (620,520) because POLTERGEIST-style widths and a centred plate
    would otherwise clear the caption band."""
    bg_cream(img)
    draw = ImageDraw.Draw(img)
    frames = [(500, '1'), (660, '2'), (820, '5'), (980, '7')]
    for k, (cx, digit) in enumerate(frames):
        if stamp < k:
            continue
        wob_rect(draw, (cx - 60, 240, cx + 60, 360), INK, fill=PAPER,
                 width=3, seed=2610 + k)
        paste_layer(img, draw_heavy(img, digit, cx, 300, INK, outline_px=0))
    draw = ImageDraw.Draw(img)
    wob_line(draw, (580, 452), (580, 370), INK, width=3, seed=2620, jitter=0.6,
             segs=3)
    wob_line(draw, (900, 452), (900, 370), INK, width=3, seed=2621, jitter=0.6,
             segs=3)
    draw_tiny(draw, 'RIGHT ASCENSION', 580, 470, INK, on_cream=True)
    draw_tiny(draw, '+12 DEGREES, UP AND NORTH', 900, 470, INK, on_cream=True)
    if stamp >= 4:
        paste_layer(img, draw_heavy(img, 'THAT IS THE NAME', 620, 540, INK,
                                    scale=1.18 if stamp == 4 else 1.0))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'], on_cream=True)


# =============================================================================
# BEAT B6 — FATE (cards 27-31)
# =============================================================================

def card_close_bother(img, card, t, stamp):
    """27. The violet radiation wash returns, swelling from 9% to 12% over four
    0.25 s stamps. Nothing else is added. The emptiness IS the warning — CLAUDE.md
    section 7, one idea per card."""
    bg_void(img, 27)
    alpha = min(0.12, 0.09 + 0.01 * stamp)
    flat_ghost(img, (200, 110, 1240, 670), VIOLET, alpha, seed=2701)
    draw = ImageDraw.Draw(img)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_close_no_burn(img, card, t, stamp):
    """28. Linework only — no fill, no gradient. A 2 px bone flame in three
    stacked lobes that EXTINGUISHES one lobe per 0.25 s stamp, bottom first over
    three stamps, leaving 6 px of ash. A flat slate-black disc r=20 appears
    inside the dead flame: the remnant star."""
    bg_void(img, 28)
    draw = ImageDraw.Draw(img)
    cx, cy = 1000, 300
    # three stacked lobes, widest at the base; a lobe is gone from stamp 3
    lobes = [(90, 60, cy - 110), (120, 40, cy - 20), (150, 20, cy + 90)]
    for k, (rx, ry, ly) in enumerate(lobes):
        alive = stamp < 3 - k
        if not alive:
            wob_line(draw, (cx - rx * 0.5, ly), (cx + rx * 0.5, ly), BONE,
                     width=2, seed=2810 + k, jitter=2.0, segs=5)
            continue
        pts = []
        for i in range(14):
            a = 2 * math.pi * i / 14
            pts.append((cx + rx * math.cos(a) * (0.55 + 0.45 * abs(math.cos(a))),
                        ly + ry * math.sin(a) * 1.7))
        wob_poly(draw, pts, BONE, fill=None, width=2, seed=2820 + k, jitter=2.0)
    if stamp >= 3:
        wob_circle(img, cx, cy, 20, INK, fill=INK, width=2, seed=2830,
                   jitter=1.0)
    draw_tiny(draw, 'WHAT WAS LEFT', cx, 460)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_close_formed(img, card, t, stamp):
    """29. Made here, not inherited. The remnant disc with its 2 px amber limb,
    a flat 2 px amber accretion ring at r=30, and rock blobs flying INWARD and
    sticking to the limb one per 0.25 s stamp — six of them. Amber outlines, not
    fills: the blobs stay slate-black so they read as rock, not as light."""
    bg_void(img, 29)
    cx, cy = 1000, 300
    draw = ImageDraw.Draw(img)
    wob_circle(img, cx, cy, 20, AMBER, fill=INK, width=2, seed=2900, jitter=1.0)
    wob_circle(img, cx, cy, 30, AMBER, fill=None, width=2, seed=2901)
    for k in range(6):
        if stamp < k:
            continue
        a = 2 * math.pi * k / 6.0 - math.pi / 2.0
        px = cx + 46 * math.cos(a)
        py = cy + 46 * math.sin(a)
        r = 9
        pts = [(px + r * math.cos(2 * math.pi * i / 6 + k),
                py + r * math.sin(2 * math.pi * i / 6 + k)) for i in range(6)]
        wob_poly(draw, pts, AMBER, fill=INK, width=2, seed=2910 + k, jitter=1.0)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_close_radiation(img, card, t, stamp):
    """30. RADIATION BATH, violet. Nine flat AMBER 3 px beam rays raking from
    the core across the left of frame at -18 deg, each blinking on a staggered
    0.25 s phase so the field shimmers. The flat violet rectangle is the
    irradiated zone — shape color, carries no word. Inside it a 3 px BONE
    ellipse and a concentric 2 px AMBER ellipse, BOTH on the same frame: the
    atmosphere, and what is left of it."""
    bg_void(img, 30)
    draw = ImageDraw.Draw(img)
    star_core(img, 1000, 300, 30, 3001, gradient=False)
    for k in range(9):
        if (stamp + k) % 3 == 2:
            continue                      # staggered blink
        a = math.radians(180.0 - 18.0 + (k - 4) * 3.4)
        wob_line(draw, (1000, 300),
                 (1000 - 300 * math.cos(a), 300 - 300 * math.sin(a)),
                 AMBER, width=3, seed=3010 + k, jitter=1.5, segs=10)
    flat_ghost(img, (140, 140, 820, 640), VIOLET, 0.10, seed=3020)
    draw = ImageDraw.Draw(img)
    wob_ellipse(draw, 480, 390, 110, 110, BONE, width=3, seed=3030)
    wob_ellipse(draw, 480, 390, 110, 110, AMBER, width=2, seed=3031)
    paste_layer(img, draw_heavy(img, 'IN AN AFTERNOON', 480, 560, BONE))
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


def card_close_finale(img, card, t, stamp):
    """31. FINAL CARD, bone — the only card that shows the whole system at
    once. The three orbit ellipses from planet_periods re-drawn at 0.75 scale,
    the three discs on them, 18 pt bone labels with 3 px leaders — bone, never
    violet at 3.48:1. ONE bone spin tick advancing 90 deg per 0.25 s stamp and
    NEVER slowing; that is the 'forever'. Every other motion on the card is
    frozen so the spin is the only thing moving. Hold 0.40 s past the last word
    (the schedule's TAIL), then the 3.75 s white bridge from lib/transition.py."""
    bg_void(img, 31)
    draw = ImageDraw.Draw(img)
    cx, cy = 900, 340
    rings = [(128, 44, 14, 250, 200), (225, 75, 17, 310, 150),
             (322, 106, 25, 370, 100)]
    for k, (rx, ry, r, lx, ly) in enumerate(rings):
        wob_ellipse(draw, cx, cy, rx, ry, BONE, width=2, seed=3100 + k)
        a = math.radians([250, 70, 160][k])
        px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
        wob_circle(img, px, py, r, INK, fill=BONE, width=2, seed=3110 + k,
                   jitter=1.0)
        wob_line(draw, (px, py), (lx, ly), BONE, width=3, seed=3120 + k,
                 jitter=1.0, segs=4)
        draw_tiny(draw, ['DRAUGR', 'PHOBETOR', 'POLTERGEIST'][k], lx + 70, ly)
    star_core(img, cx, cy, 26, 3130, gradient=False)
    spin_tick(draw, cx, cy, 26, stamp, BONE, n_per_rev=4, width=3, seed=3140)
    draw_stickman_card(img, card, t, stamp)
    draw_caption(draw, card['caption'])


# =============================================================================
# DISPATCH
# =============================================================================

RENDERERS = {
    'hook_dead': card_hook_dead,
    'hook_talking': card_hook_talking,
    'hook_not_alone': card_hook_not_alone,
    'psr_size': card_psr_size,
    'psr_collapse': card_psr_collapse,
    'psr_spin': card_psr_spin,
    'psr_rate': card_psr_rate,
    'psr_beams': card_psr_beams,
    'psr_lighthouse': card_psr_lighthouse,
    'psr_name': card_psr_name,
    'planet_masses': card_planet_masses,
    'planet_minefield': card_planet_minefield,
    'planet_periods': card_planet_periods,
    'how_find': card_how_find,
    'how_signature': card_how_signature,
    'how_1990': card_how_1990,
    'how_two_years': card_how_two_years,
    'how_grave': card_how_grave,
    'how_steady': card_how_steady,
    'how_tug': card_how_tug,
    'how_first': card_how_first,
    'name_why': card_name_why,
    'name_three': card_name_three,
    'name_star': card_name_star,
    'name_coordinates': card_name_coordinates,
    'name_just_digits': card_name_just_digits,
    'close_bother': card_close_bother,
    'close_no_burn': card_close_no_burn,
    'close_formed': card_close_formed,
    'close_radiation': card_close_radiation,
    'close_finale': card_close_finale,
}


# =============================================================================
# RENDER
# =============================================================================

def render_card(card, t, debug=False):
    """One 1280x720 RGB frame. The header band is drawn LAST so nothing can
    ever overprint the title strip."""
    img = Image.new('RGB', (W, H), DEEP)
    fn = RENDERERS.get(card['id'])
    if fn is None:
        raise KeyError('no renderer for card id %r' % card['id'])
    fn(img, card, t, stamp_index(t))
    draw_header_band(img)
    if debug:
        _draw_debug(img, card, t)
    return img


def _draw_debug(img, card, t):
    """Opt-in only (CLAUDE.md section 10.9: a debug-on-by-default mode left
    'SEGMENT 3 / round-1' stamps in a shipped build). Amber, top-left of the
    art area, never in the title strip."""
    draw = ImageDraw.Draw(img)
    draw_stamp(draw, 'SEGMENT 3 ROUND-1', 130, 84, AMBER)
    draw_stamp(draw, 'CARD %02d %s' % (card['n'], card['id']), 130, 110, AMBER)
    draw_stamp(draw, 'T=%.2f STAMP=%d' % (t, stamp_index(t)), 130, 136, AMBER)


# --- red audit (PALETTE_SPEC.md section 1: his shirt is the ONLY red) --------

def red_audit(img, where, shirt_bbox=None):
    """Fail the build if any pixel is red outside the shirt patch.

    A pixel counts as red when R is well above both G and B AND R is high
    enough to read as red rather than as amber (which is R232 G163 B61 and
    fails the G/R test at 0.70). The shirt is (200,50,50): R-G = 150.
    Threshold R-G > 90 and R-B > 60 isolates the shirt and nothing else in the
    locked palette."""
    px = img.load()
    bad = []
    x0, y0, x1, y1 = shirt_bbox or (0, 0, 0, 0)
    for y in range(ART_TOP, ART_BOT):
        for x in range(0, W):
            if x0 - 4 <= x <= x1 + 4 and y0 - 4 <= y <= y1 + 4:
                continue
            r, g, b = px[x, y][:3]
            if r - g > 90 and r - b > 60 and r > 90:
                bad.append((x, y, (r, g, b)))
    if bad:
        raise ValueError('[%s] %d red pixel(s) outside the stickman shirt, '
                         'first=%r' % (where, len(bad), bad[:4]))
    return 0


def shirt_bbox_for(card, stamp=0):
    """Where the shirt lands, so the audit can whitelist exactly it. Uses the
    same geometry as draw_shirt and the exact micro-motion offset for the given
    stamp, plus 3 px for the 2px wobbly outline and its jitter. It is derived,
    not guessed, so the whitelist cannot hide a red that is somewhere else."""
    s = card.get('stickman')
    if not s:
        return None
    x, y, h = stick_geom(card)
    dx, dy = stick_offset(card, stamp)
    cx, ytop = x + dx, y + dy
    head_r = int(h / 8.0)
    neck_y = ytop + 2 * head_r
    hip_y = neck_y + int(h * 0.35)
    half = int(head_r * 1.15)
    return (cx - half - 3, neck_y - 3, cx + half + 3, hip_y + 3)


def render_segment(schedule, out_dir, fps=FPS, hold_last_frames=0, debug=False,
                   verbose=True):
    """Render every frame of the segment, driven ONLY by the schedule's
    start/end. Hard cuts at every clause break (transition_in == 'snap');
    motion_xfade_s is within-card only, so there is no cross-card fade to
    implement here. Frames are re-rendered on each 0.25 s motion stamp rather
    than per frame — CLAUDE.md section 5 / the schedule's geometry.motion_rule
    forbids smooth tweens, so 4 identical frames per stamp is the intent, not
    an optimization."""
    import os
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    cards = schedule['cards']
    total = int(round(cards[-1]['end'] * fps)) + hold_last_frames
    written = 0
    n_red_checked = 0
    for idx, card in enumerate(cards):
        fn = RENDERERS[card['id']]
        f0 = int(round(card['start'] * fps))
        f1 = int(round(card['end'] * fps))
        for fi in range(f0, f1):
            t = fi / float(fps)
            img = render_card(card, t, debug=debug)
            path = os.path.join(out_dir, 'f%05d.png' % fi)
            img.save(path)
            written += 1
        if card.get('stickman'):
            img = render_card(card, (f0 + max(0, f1 - f0 - 1)) / float(fps),
                              debug=debug)
            red_audit(img, 'card %d %s' % (card['n'], card['id']),
                      shirt_bbox_for(card, stamp_index((f1 - 1) / float(fps))))
            n_red_checked += 1
        if verbose:
            print('  card %2d %-22s %6.2f-%6.2fs  %4d frames'
                  % (card['n'], card['id'], card['start'], card['end'],
                     f1 - f0))
        del fn
    if verbose:
        print('wrote %d frames to %s (%d stickman frames red-audited)'
              % (written, out_dir, n_red_checked))
    return written


def render_verify(schedule, out_dir, debug=False, audit=True):
    """ONE representative frame per card into a small dir, so the whole
    segment can be eyeballed without rendering 2000+ frames. The representative
    frame is chosen one motion stamp in, so cards that build in steps are
    shown at their final state."""
    import os
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    paths = []
    for card in schedule['cards']:
        t = min(card['start'] + 0.30, max(card['start'],
                                           card['end'] - 1.0 / FPS))
        img = render_card(card, t, debug=debug)
        p = os.path.join(out_dir, '%02d_%s.png' % (card['n'], card['id']))
        img.save(p)
        paths.append(p)
        if audit and card.get('stickman'):
            red_audit(img, 'verify %d %s' % (card['n'], card['id']),
                      shirt_bbox_for(card, stamp_index(t)))
    return paths


def main():
    ap = argparse.ArgumentParser(
        description='Segment 3 (PSR B1257+12) round-1 frame generator.')
    ap.add_argument('--schedule', default=os.path.join(
        HERE, 'round_1_card_schedule.json'))
    ap.add_argument('--outdir', default=os.path.join(HERE, 'round_1_frames'))
    ap.add_argument('--frames-dir', dest='frames_dir', default=None,
                    help='alias for --outdir, kept for the segment 1 CLI shape')
    ap.add_argument('--debug', action='store_true',
                    help='stamp SEGMENT 3 / card / time into each frame. OFF '
                         'by default (CLAUDE.md 10.9).')
    ap.add_argument('--verify', action='store_true',
                    help='render ONE representative frame per card and exit')
    ap.add_argument('--verify-dir', default=os.path.join(HERE, 'verify_r1'))
    ap.add_argument('--no-audit', action='store_true',
                    help='skip the red-pixel audit in --verify')
    args = ap.parse_args()

    with open(args.schedule, encoding='utf-8') as f:
        schedule = json.load(f)

    missing = [c['id'] for c in schedule['cards'] if c['id'] not in RENDERERS]
    if missing:
        raise SystemExit('no renderer for: %s' % ', '.join(missing))
    if len(schedule['cards']) != len(RENDERERS):
        print('WARNING: %d cards in the schedule, %d renderers'
              % (len(schedule['cards']), len(RENDERERS)))

    if args.verify:
        paths = render_verify(schedule, args.verify_dir, debug=args.debug,
                              audit=not args.no_audit)
        print('verify frames (%d):' % len(paths))
        for p in paths:
            print('  ' + p)
        return

    out = args.frames_dir or args.outdir
    print('rendering %d cards, %.2f-%0.2fs @ %dfps -> %s'
          % (len(schedule['cards']), schedule['cards'][0]['start'],
             schedule['cards'][-1]['end'], FPS, out))
    render_segment(schedule, out, fps=FPS, debug=args.debug)


if __name__ == '__main__':
    main()
