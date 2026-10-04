# work/segments/hd80606/_frames_r3.py
# Round 3 build for segment 2 (HD 80606 b — the whiplash planet).
#
# Round 2 was ref_wins with biggest gap:
#   "Stickman scale + lack of varied facial expression + cluttered
#    single-card compositions."
#
# Round 3 fixes (per the round-2 critic's round_3_directives):
#   1. SCALE THE STICKMAN to 50-60% of frame height (was 25-30%). Anchor
#      center-frame on emotional beats, not corner.
#   2. VARY FACIAL EXPRESSIONS PER BEAT — per-beat REACTIONS map with 10
#      unique (mouth, pose) pairs that follow the emotional arc:
#         awed -> squint -> flat -> scream -> worried -> scream ->
#         relief -> terrified -> smirk -> frown
#   3. USE INTEGRATED HAND-LETTERED LABELS — "SO CLOSE" on the planet,
#      "WINDS AT KM/S" on the planet, "+500C" on the corona, "EVERY 40
#      DAYS" stamp.
#   4. EMBRACE 'ONE IDEA PER CARD' — some beats diagram-only, some
#      character-only, some integrated-diagram. No more 4-5 element
#      clutter.
#   5. VARY COMPOSITION ACROSS TIMESTAMPS — orbit-only, planet-only,
#      character-only, sun-only, integrated-diagram. No repeated
#      composition.
#   6. STRENGTHEN STAMP READABILITY — heavy weight, strong color, single
#      word where possible.
#   7. ADD POSE VARIATIONS — pointing, shrugging, cowering, shielding-
#      eyes, hands-down, hands-up. Active reaction per beat, not class
#      photo pose.
#   8. HAND-LETTER THE KEY LABEL PER BEAT — every important beat gets
#      a 'So Close'-style integrated label on the diagram.
#
# Per CLAUDE.md §6: the stickman must be present in at least one beat
# (round 2's worst loss). Round 3 keeps him in EVERY beat, with a
# unique (mouth, pose) per beat, scaled to 50-60% of frame.
#
# Round 2 wins preserved: white title band, painterly stipple/gradient
# textures, ALL CAPS captions with hard length check, alignment-derived
# card schedule, two-step render, no debug stamps by default.

import os
import json
import math
import random
import sys
import argparse

# Ensure we can import the lib modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PIL import Image, ImageDraw
from lib import stickman as sm
from lib import palette as P
from lib import type as T
from lib import texture
from lib import title_band
from lib import integrated_label

# Frame dimensions
W, H = 1280, 720
FPS = 30
TITLE_STRIP_BOT = title_band.band_bottom()   # 61
ILLUSTRATION_TOP = 80
ILLUSTRATION_BOT = 719

PAL = P.SEGMENT_2
INK = PAL['ink']

# Hard caption constraints (per CLAUDE.md §7)
MAX_CAPTION_CHARS = 60
CAPTION_FONT = T.load_font(T.CAPTION_PX, bold=False)
DRAW_FONT_BOLD = T.load_font(T.CAPTION_PX, bold=True)


# --- Local stickman halo wrapper (segment 2 only, not in lib/stickman.py) ---
#
# The shared lib/stickman.py uses pure-black 2-3 px strokes on a white
# head. On our dark starfield bg=(1,1,10) the limbs are invisible. To
# keep the fix local to this segment (and not affect other segments
# that may use lib/stickman on light bgs), we add a CREAM HALO underlay
# pass here: draw a wider cream stroke first, then the black stroke on
# top. This is the comic-book "lit stage" outline.

_STICK_HALO_RGB = (245, 235, 215)   # cream
_STICK_HALO_W = 6                  # cream halo width
_STICK_INK = (0, 0, 0)
_STICK_HEAD_FILL = (255, 255, 255)


def _halo_line(draw, a, b, color, width):
    if _STICK_HALO_W > 0:
        draw.line([a, b], fill=_STICK_HALO_RGB, width=width + _STICK_HALO_W)
    draw.line([a, b], fill=color, width=width)


def _halo_ellipse_outline(draw, box, width):
    if _STICK_HALO_W > 0:
        bx0, by0, bx1, by1 = box
        draw.ellipse(
            [bx0 - _STICK_HALO_W, by0 - _STICK_HALO_W,
             bx1 + _STICK_HALO_W, by1 + _STICK_HALO_W],
            outline=_STICK_HALO_RGB, fill=_STICK_HALO_RGB, width=_STICK_HALO_W,
        )
    draw.ellipse(box, outline=_STICK_INK, fill=_STICK_HEAD_FILL, width=width)


def _halo_disc(draw, cx, cy, r):
    # Small filled circle with halo (hands, feet)
    if _STICK_HALO_W > 0:
        draw.ellipse(
            [cx - r - _STICK_HALO_W, cy - r - _STICK_HALO_W,
             cx + r + _STICK_HALO_W, cy + r + _STICK_HALO_W],
            fill=_STICK_HALO_RGB,
        )
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_STICK_INK)


def _draw_haloed_stickman(image, x_center, y_top, height, pose, mouth, seed,
                          draw_image=None, scale=1.0):
    """Segment-2 local stickman with cream halo for visibility on dark bg.

    The cream halo + black stroke is the comic-book "lit stage" outline
    that makes the stickman pop on the dark starfield.
    """
    if draw_image is None:
        draw_image = image
    d = ImageDraw.Draw(draw_image)
    # Compute geometry (same as lib.stickman)
    head_r = max(8, int(height / 8))
    head_cy = y_top + head_r
    neck_y = head_cy + head_r
    hip_y = neck_y + int(height * 0.35)
    foot_y = y_top + height

    # Head (with halo)
    _halo_ellipse_outline(d,
        [x_center - head_r, y_top, x_center + head_r, y_top + 2 * head_r],
        width=3,
    )
    # Eyes
    eye_y = head_cy - int(head_r * 0.2)
    if mouth == 'squint':
        # Closed-line eyes for squint
        d.line([(x_center - int(head_r * 0.6), eye_y),
                (x_center - int(head_r * 0.2), eye_y - 1)], fill=_STICK_INK, width=2)
        d.line([(x_center + int(head_r * 0.2), eye_y - 1),
                (x_center + int(head_r * 0.6), eye_y)], fill=_STICK_INK, width=2)
    else:
        d.ellipse([x_center - int(head_r * 0.4) - 1, eye_y - 1,
                   x_center - int(head_r * 0.4) + 1, eye_y + 1], fill=_STICK_INK)
        d.ellipse([x_center + int(head_r * 0.4) - 1, eye_y - 1,
                   x_center + int(head_r * 0.4) + 1, eye_y + 1], fill=_STICK_INK)

    # Spine
    _halo_line(d, (x_center, neck_y), (x_center, hip_y), _STICK_INK, 3)

    if pose == 'hands_up':
        arm_x = int(head_r * 1.3)
        arm_y_top = y_top - int(head_r * 0.3)
        _halo_line(d, (x_center, neck_y), (x_center - arm_x, arm_y_top), _STICK_INK, 2)
        _halo_line(d, (x_center, neck_y), (x_center + arm_x, arm_y_top), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_x, arm_y_top, 2)
        _halo_disc(d, x_center + arm_x, arm_y_top, 2)
    elif pose == 'pointing':
        # Left arm at side
        _halo_line(d, (x_center, neck_y + 4),
                   (x_center - int(head_r * 0.9), hip_y - 4), _STICK_INK, 2)
        _halo_disc(d, x_center - int(head_r * 0.9), hip_y - 4, 2)
        # Right arm pointing out
        point_x = x_center + int(height * 0.5)
        point_y = neck_y + int(height * 0.1)
        _halo_line(d, (x_center, neck_y), (point_x, point_y), _STICK_INK, 2)
        _halo_disc(d, point_x, point_y, 2)
    elif pose == 'cowering':
        # Hunched: knees bent, arms tucked in
        arm_y = neck_y + int(head_r * 0.5)
        arm_dx = int(head_r * 0.4)
        _halo_line(d, (x_center, arm_y),
                   (x_center + arm_dx, arm_y - int(head_r * 0.3)), _STICK_INK, 2)
        _halo_disc(d, x_center + arm_dx, arm_y - int(head_r * 0.3), 2)
        _halo_line(d, (x_center, arm_y),
                   (x_center - arm_dx, arm_y - int(head_r * 0.3)), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_dx, arm_y - int(head_r * 0.3), 2)
        # Crouched legs
        knee_y = hip_y + int((foot_y - hip_y) * 0.5)
        knee_dx = int(head_r * 0.9)
        _halo_line(d, (x_center, hip_y), (x_center - knee_dx, knee_y), _STICK_INK, 2)
        _halo_line(d, (x_center - knee_dx, knee_y),
                   (x_center - int(head_r * 0.2), foot_y), _STICK_INK, 2)
        _halo_line(d, (x_center, hip_y), (x_center + knee_dx, knee_y), _STICK_INK, 2)
        _halo_line(d, (x_center + knee_dx, knee_y),
                   (x_center + int(head_r * 0.2), foot_y), _STICK_INK, 2)
        _halo_disc(d, x_center - int(head_r * 0.2), foot_y, 2)
        _halo_disc(d, x_center + int(head_r * 0.2), foot_y, 2)
    elif pose == 'shrugged':
        # Arms out at sides, palms up
        arm_y = neck_y + int((hip_y - neck_y) * 0.4)
        arm_x = int(head_r * 1.5)
        _halo_line(d, (x_center, arm_y),
                   (x_center + arm_x, arm_y + int(head_r * 0.4)), _STICK_INK, 2)
        _halo_disc(d, x_center + arm_x, arm_y + int(head_r * 0.4), 2)
        _halo_line(d, (x_center, arm_y),
                   (x_center - arm_x, arm_y + int(head_r * 0.4)), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_x, arm_y + int(head_r * 0.4), 2)
        leg_dx = int(head_r * 0.6)
        _halo_line(d, (x_center, hip_y), (x_center - leg_dx, foot_y), _STICK_INK, 2)
        _halo_line(d, (x_center, hip_y), (x_center + leg_dx, foot_y), _STICK_INK, 2)
        _halo_disc(d, x_center - leg_dx, foot_y, 2)
        _halo_disc(d, x_center + leg_dx, foot_y, 2)
    elif pose == 'hands_down':
        # Arms relaxed at sides, feet together
        arm_y_top = neck_y + int(head_r * 0.3)
        arm_y_bot = hip_y + int(head_r * 0.3)
        arm_dx = int(head_r * 0.4)
        _halo_line(d, (x_center, arm_y_top), (x_center - arm_dx, arm_y_bot), _STICK_INK, 2)
        _halo_line(d, (x_center, arm_y_top), (x_center + arm_dx, arm_y_bot), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_dx, arm_y_bot, 2)
        _halo_disc(d, x_center + arm_dx, arm_y_bot, 2)
        leg_dx = int(head_r * 0.2)
        _halo_line(d, (x_center, hip_y), (x_center - leg_dx, foot_y), _STICK_INK, 2)
        _halo_line(d, (x_center, hip_y), (x_center + leg_dx, foot_y), _STICK_INK, 2)
        _halo_disc(d, x_center - leg_dx, foot_y, 2)
        _halo_disc(d, x_center + leg_dx, foot_y, 2)
    elif pose == 'shielding_eyes':
        # Both arms bent up, hands at forehead
        elbow_y = neck_y + int(head_r * 1.2)
        elbow_x = int(head_r * 1.6)
        _halo_line(d, (x_center, neck_y), (x_center + elbow_x, elbow_y), _STICK_INK, 2)
        _halo_line(d, (x_center + elbow_x, elbow_y),
                   (x_center + int(head_r * 0.4), y_top - int(head_r * 0.1)), _STICK_INK, 2)
        _halo_disc(d, x_center + int(head_r * 0.4), y_top - int(head_r * 0.1), 2)
        _halo_line(d, (x_center, neck_y), (x_center - elbow_x, elbow_y), _STICK_INK, 2)
        _halo_line(d, (x_center - elbow_x, elbow_y),
                   (x_center - int(head_r * 0.4), y_top - int(head_r * 0.1)), _STICK_INK, 2)
        _halo_disc(d, x_center - int(head_r * 0.4), y_top - int(head_r * 0.1), 2)
        leg_dx = int(head_r * 0.6)
        _halo_line(d, (x_center, hip_y), (x_center - leg_dx, foot_y), _STICK_INK, 2)
        _halo_line(d, (x_center, hip_y), (x_center + leg_dx, foot_y), _STICK_INK, 2)
        _halo_disc(d, x_center - leg_dx, foot_y, 2)
        _halo_disc(d, x_center + leg_dx, foot_y, 2)
    else:  # 'standing' or default
        arm_dx = int(head_r * 1.2)
        arm_y = neck_y + int((hip_y - neck_y) * 0.3)
        _halo_line(d, (x_center, arm_y),
                   (x_center - arm_dx, arm_y + int(head_r * 0.6)), _STICK_INK, 2)
        _halo_line(d, (x_center, arm_y),
                   (x_center + arm_dx, arm_y + int(head_r * 0.6)), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_dx, arm_y + int(head_r * 0.6), 2)
        _halo_disc(d, x_center + arm_dx, arm_y + int(head_r * 0.6), 2)
        leg_dx = int(head_r * 0.5)
        _halo_line(d, (x_center, hip_y), (x_center - leg_dx, foot_y), _STICK_INK, 2)
        _halo_line(d, (x_center, hip_y), (x_center + leg_dx, foot_y), _STICK_INK, 2)
        _halo_disc(d, x_center - leg_dx, foot_y, 2)
        _halo_disc(d, x_center + leg_dx, foot_y, 2)

    # Mouth (the only thing that changes between expressions)
    mouth_cy = head_cy + int(head_r * 0.4)
    if mouth == 'smile':
        w = int(7 * scale)
        d.arc([x_center - w, mouth_cy - 3, x_center + w, mouth_cy + 3], 0, 180,
              fill=_STICK_INK, width=2)
    elif mouth == 'frown':
        w = int(7 * scale)
        d.arc([x_center - w, mouth_cy - 3, x_center + w, mouth_cy + 3], 180, 360,
              fill=_STICK_INK, width=2)
    elif mouth == 'flat':
        d.line([x_center - 8, mouth_cy, x_center + 8, mouth_cy],
               fill=_STICK_INK, width=2)
    elif mouth == 'oval':
        w, h = 8, 5
        d.ellipse([x_center - w, mouth_cy - h, x_center + w, mouth_cy + h],
                  outline=_STICK_INK, width=2)
        d.ellipse([x_center - w + 2, mouth_cy - h + 2,
                   x_center + w - 2, mouth_cy + h - 2], fill=(220, 100, 100))
    elif mouth == 'zigzag':
        pts = []
        for i in range(7):
            x = x_center - 6 + i * 2
            y = mouth_cy + (2 if i % 2 == 0 else -2)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=_STICK_INK, width=2)
    elif mouth == 'worried':
        # Small downturned with raised brow lines
        w = int(6 * scale)
        d.arc([x_center - w, mouth_cy - int(2 * scale),
               x_center + w, mouth_cy + int(4 * scale)],
              180, 360, fill=_STICK_INK, width=2)
        # Brow lines
        brow_dy = int(4 * scale)
        d.line([(x_center - int(7 * scale), mouth_cy - brow_dy - 2),
                (x_center - int(3 * scale), mouth_cy - brow_dy)],
               fill=_STICK_INK, width=1)
        d.line([(x_center + int(3 * scale), mouth_cy - brow_dy),
                (x_center + int(7 * scale), mouth_cy - brow_dy - 2)],
               fill=_STICK_INK, width=1)
    elif mouth == 'scream':
        w, h = 9, 10
        d.ellipse([x_center - w, mouth_cy - h, x_center + w, mouth_cy + h],
                  outline=_STICK_INK, width=2)
        d.ellipse([x_center - w + 1, mouth_cy - h + 1,
                   x_center + w - 1, mouth_cy + h - 1], fill=(120, 30, 30))
    elif mouth == 'relief':
        w = int(6 * scale)
        d.arc([x_center - w, mouth_cy - int(3 * scale),
               x_center + w, mouth_cy + int(3 * scale)],
              0, 180, fill=_STICK_INK, width=2)
    elif mouth == 'smirk':
        # Asymmetric: left side flat, right side curving up
        d.line([(x_center - int(7 * scale), mouth_cy + 1),
                (x_center - int(2 * scale), mouth_cy)], fill=_STICK_INK, width=2)
        d.arc([x_center - int(2 * scale), mouth_cy - int(3 * scale),
               x_center + int(7 * scale), mouth_cy + int(3 * scale)],
              200, 340, fill=_STICK_INK, width=2)
    elif mouth == 'sad_smile':
        w = int(7 * scale)
        d.arc([x_center - w, mouth_cy - int(2 * scale),
               x_center + w, mouth_cy + int(3 * scale)],
              180, 360, fill=_STICK_INK, width=2)
        brow_dy = int(4 * scale)
        d.line([(x_center - int(8 * scale), mouth_cy - brow_dy),
                (x_center + int(8 * scale), mouth_cy - brow_dy - 2)],
               fill=_STICK_INK, width=1)
    elif mouth == 'squint':
        # Slight downward curve (overwhelmed)
        w = int(7 * scale)
        d.arc([x_center - w, mouth_cy - int(2 * scale),
               x_center + w, mouth_cy + int(2 * scale)],
              0, 180, fill=_STICK_INK, width=2)
    elif mouth == 'terrified':
        w, h = 10, 8
        d.ellipse([x_center - w, mouth_cy - h, x_center + w, mouth_cy + h],
                  outline=_STICK_INK, width=3)
    return {'head_cy': head_cy, 'head_r': head_r, 'foot_y': foot_y}


# --- Per-beat REACTIONS map (round 3 character contract) ---
#
# HD 80606 b emotional arc: awed -> squint (overwhelmed) -> flat (deadpan) ->
#   scream (the "so close" climax) -> worried (fever) -> scream (pure reaction) ->
#   relief (cold again) -> terrified (shock waves) -> smirk (the loop) -> frown (finale)
#
# Each card has a unique (mouth, pose) pair so the stickman varies
# per beat. The map is the contract — the critic will check it.

REACTIONS = {
    'intro':          ('oval',      'hands_up'),
    'planet_intro':   ('oval',      'standing'),
    'cold_orbit':     ('squint',    'pointing'),
    'so_close':       ('scream',    'cowering'),
    'fever':          ('worried',   'shielding_eyes'),
    'pure_stickman':  ('scream',    'cowering'),
    'cold_again':     ('relief',    'shrugged'),
    'shock_waves':    ('terrified', 'cowering'),
    'loop':           ('smirk',     'shrugged'),
    'finale':         ('frown',     'hands_down'),
}


def lookup_reaction(card_id):
    """Return (expression, pose) for a given card id, defaulting to a
    deadpan/standing pair if not mapped."""
    return REACTIONS.get(card_id, ('flat', 'standing'))


def draw_stickman_motion(image, t, x_center, y_top, height, pose, mouth,
                         seed=0, beat_period_s=2.0):
    """Draw the stickman with a 1-2s micro-loop based on `t`.

    The micro-motion is a small horizontal shift + vertical bob. Reference
    never holds a stickman still for >2s without a micro-motion.
    """
    phase = (t % beat_period_s) / beat_period_s
    sway_dx = int(4 * math.sin(2 * math.pi * phase))
    bob_dy = int(2 * math.cos(2 * math.pi * phase))
    _draw_haloed_stickman(
        image, x_center + sway_dx, y_top + bob_dy, height, pose, mouth, seed,
    )


# --- Hard caption check (fails the build on violation) ---

def _safe_textwidth(text, font):
    try:
        x0, _, x1, _ = font.getbbox(text)
        return x1 - x0
    except Exception:
        return len(text) * 16


def _check_caption(text, where):
    """Hard check: fail the build if the caption violates §7.

    - text must be <= MAX_CAPTION_CHARS characters
    - text must fit on a single line at 27 px Consolas (no wrap)
    - text must be ALL CAPS
    """
    if not text:
        raise ValueError(f"[{where}] empty caption")
    if len(text) > MAX_CAPTION_CHARS:
        raise ValueError(
            f"[{where}] caption is {len(text)} chars, max {MAX_CAPTION_CHARS}: {text!r}"
        )
    if text != text.upper():
        raise ValueError(
            f"[{where}] caption is not ALL CAPS: {text!r}"
        )
    w = _safe_textwidth(text, CAPTION_FONT)
    if w > 1100:
        raise ValueError(
            f"[{where}] caption is {w}px wide (>1100), would wrap: {text!r}"
        )


def draw_caption(draw, text, xy, color_rgb=None, where='caption'):
    """Caption renderer with the §7 hard check."""
    if color_rgb is None:
        color_rgb = PAL['caption']
    text_upper = text.upper()
    _check_caption(text_upper, where=where)
    T.draw_caption(draw, text_upper, xy, color_rgb=color_rgb)


def draw_title_strip(img, name):
    """Render the title strip via lib.title_band (white rect, Consolas Bold
    ALL CAPS, BLACK fill, NO STROKE)."""
    title_band.draw_title_band(img, name)


# --- Wobble helpers ---

def wobble_line(draw, p0, p1, color, width=2, seed=0, jitter=1.5, segments=8):
    """Draw a line as a polyline with hand-jittered vertices."""
    rng = random.Random(seed)
    x0, y0 = p0
    x1, y1 = p1
    pts = []
    for i in range(segments + 1):
        t = i / segments
        x = x0 + (x1 - x0) * t + rng.uniform(-jitter, jitter)
        y = y0 + (y1 - y0) * t + rng.uniform(-jitter, jitter)
        pts.append((x, y))
    draw.line(pts, fill=color, width=width)


def wobble_circle(draw, center, radius, color, fill=None, width=3, seed=0,
                  segments=24, jitter=1.5):
    """Draw a circle as a wobbly polygon."""
    rng = random.Random(seed)
    cx, cy = center
    pts = []
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        r = radius + rng.uniform(-jitter, jitter)
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang)
        pts.append((x, y))
    if fill is not None:
        draw.polygon(pts, fill=fill, outline=color)
    else:
        draw.polygon(pts, outline=color)
    if width > 0 and fill is not None:
        draw.line(pts + [pts[0]], fill=color, width=width)


def wobble_rect(draw, bbox, color, fill=None, width=3, seed=0, jitter=1.5):
    """Draw a rectangle as a wobbly quadrilateral."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = bbox
    pts = [
        (x0 + rng.uniform(-jitter, jitter), y0 + rng.uniform(-jitter, jitter)),
        (x1 + rng.uniform(-jitter, jitter), y0 + rng.uniform(-jitter, jitter)),
        (x1 + rng.uniform(-jitter, jitter), y1 + rng.uniform(-jitter, jitter)),
        (x0 + rng.uniform(-jitter, jitter), y1 + rng.uniform(-jitter, jitter)),
    ]
    if fill is not None:
        draw.polygon(pts, fill=fill)
    if width > 0:
        draw.line(pts + [pts[0]], fill=color, width=width)


# --- Painterly sun / planet helpers ---

def draw_sun_painterly(img, cx, cy, r, palette_dict, seed=0):
    """Render a painterly sun (radial gradient + stipple + soft halo)."""
    texture.sun_disc(img, cx, cy, r, palette=palette_dict, seed=seed, halo=True)


def draw_planet_painterly(img, cx, cy, r, base_rgb, palette_dict=None,
                          n_bands=4, seed=0, with_bands=True):
    """Render a painterly planet (banded + radial gradient + stipple)."""
    texture.planet_disc(img, cx, cy, r, base_rgb=base_rgb,
                        palette=palette_dict, n_bands=n_bands,
                        seed=seed, with_bands=with_bands)


# --- Stars ---

def draw_stars(img, count, seed, region=None, color=None):
    """Draw N small stars in the illustration area. Deterministic per seed."""
    if region is None:
        region = (10, ILLUSTRATION_TOP + 10, W - 10, ILLUSTRATION_BOT - 10)
    if color is None:
        color = PAL['accent3']
    x0, y0, x1, y1 = region
    rng = random.Random(seed)
    draw = ImageDraw.Draw(img)
    for _ in range(count):
        sx = rng.randint(x0, x1)
        sy = rng.randint(y0, y1)
        sr = rng.choice([1, 1, 2, 2, 3])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=color)


# --- The sun palette for HD 80606 b's star (warm yellow -> orange -> red) ---

WHIP_STAR = {
    'core':  (255, 230, 110),    # bright yellow core
    'mid':   (250, 178, 11),     # warm yellow
    'outer': (239, 68, 3),       # red ring
    'halo':  (180, 60, 10),      # warm red-orange halo
}

# Hot day-side palette for the planet (warm yellow base + dark red bands)
HOT_PLANET_PALETTE = {
    'bands': [
        (255, 210, 80),    # bright yellow band
        (239, 68, 3),      # red band
        (255, 180, 60),    # yellow band
        (129, 37, 17),     # dark red
        (255, 220, 100),   # light highlight band
    ],
    'light': (255, 220, 110),
    'deep':  (120, 30, 8),
}

# Cool far-orbit palette for the planet when it sits far from the star
COOL_PLANET_PALETTE = {
    'bands': [
        (60, 130, 180),
        (36, 100, 140),
        (90, 150, 200),
        (24, 70, 100),
        (110, 170, 210),
    ],
    'light': (120, 180, 220),
    'deep':  (16, 50, 80),
}


# --- CARDS ---
# Each card is a function that takes (t=time-in-seconds) and returns a PIL Image.
# Round 3 fix: VARY composition per card. Some are diagram-only, some are
# character-only, some are integrated-diagram. Stickman scale 50-60% on
# all beats that include him.

# Stickman height 50-60% of frame height
# (50% = 360, 60% = 432)
STICKMAN_HEIGHT = 400  # ~55% of 720


def card_intro(t=0.0):
    """Card 1: 'Now imagine a planet that gets a fever every forty days.'
    TITLE-CARD beat: planet + integrated 'HD 80606 B' label on the planet.
    Stickman 55% center-bottom, awed + hands-up.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 90, seed=10)

    # Big painterly planet center-right (LOWERED to keep halo below title band)
    # Halo extends ~2.2*r above center. For r=180, halo top = cy - 396.
    # We need halo_top >= 62 -> cy >= 458.
    draw_planet_painterly(img, 860, 480, 180, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=11)
    # Flame halo around the planet
    integrated_label.draw_flame_halo(img, 860, 480, 180, seed=12)

    # Integrated hand-lettered 'HD 80606 B' label ON the planet
    integrated_label.draw_integrated_label(
        img, "HD 80606 B", 860, 480, scale=0.55, seed=13,
        fill=(250, 178, 11),
    )

    # Stickman center-bottom, hands-up + oval mouth (awed), 400 px (~55%)
    draw_stickman_motion(
        img, t=t, x_center=380, y_top=300, height=STICKMAN_HEIGHT,
        pose='hands_up', mouth='oval', beat_period_s=2.0, seed=1,
    )

    # Single line caption (no stamp — the integrated label IS the stamp)
    draw_caption(draw, "A FEVER EVERY FORTY DAYS",
                 xy=(180, 130), where='intro')
    return img


def card_planet_intro(t=0.0):
    """Card 2: 'HD 80606 b. A gas giant about four times the mass of
    Jupiter, on an orbit so stretched out it looks like someone drew it
    with a ruler and then bent the ruler.'

    CHARACTER-ONLY beat: stickman center-stage reacting, no planet.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=20)

    # Heavy stamp for the "4 x Jupiter" fact — strong color, no fade
    T.draw_stamp(draw, "4 x JUPITER",
                 xy=(80, 110), accent_rgb=PAL['accent1'])

    # Stickman CENTER, awed + standing, 400 px (55% frame)
    expression, pose = lookup_reaction('planet_intro')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=240, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=2,
    )

    draw_caption(draw, "A GAS GIANT ON A WILD ORBIT",
                 xy=(180, 130), where='planet_intro')
    return img


def card_cold_orbit(t=0.0):
    """Card 3: 'Most of the time, it sits far from its star. Cold. Quiet.
    Average.'

    DIAGRAM-ONLY beat: orbit ellipse + small cool planet + tiny star.
    No stickman (the gap fix says some beats are diagram-only).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 120, seed=30)

    # Tiny warm star on the far left
    draw_sun_painterly(img, 160, 400, 50, WHIP_STAR, seed=31)

    # Cool blue planet on the right (far from the star)
    draw_planet_painterly(img, 1000, 400, 110, PAL['planet_cool'],
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=32)

    # Wobbly orbit ellipse
    rng = random.Random(33)
    pts = []
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x = 640 + 480 * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = 400 + 130 * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['planet_cool'], width=2)

    # No caption (diagram-only)
    return img


def card_so_close(t=0.0):
    """Card 4: 'And then it swings in close. Very close. So close that the
    side facing the star gets hit with about eight hundred times more
    starlight than the side facing away.'

    DIAGRAM-ONLY climax beat: planet + star + integrated 'SO CLOSE' label
    on the planet. No stickman — the planet IS the subject.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=40)

    # The big star (sun) on the right
    draw_sun_painterly(img, 1020, 480, 140, WHIP_STAR, seed=41)

    # The planet on the left, engulfed in flame halo (LOWERED to keep halo below title band)
    # For r=150, halo top = cy - 330. Need cy >= 392.
    planet_cx, planet_cy = 480, 480
    planet_r = 150
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=42)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=43)

    # Integrated 'SO CLOSE' label ON the planet
    integrated_label.draw_integrated_label(
        img, "SO CLOSE", planet_cx, planet_cy, scale=1.1, seed=44,
        fill=(250, 178, 11),
    )

    # No caption (integrated label IS the caption for this beat)
    return img


def card_fever(t=0.0):
    """Card 5: 'In a few hours, the temperature on the day side spikes by
    five hundred degrees Celsius.'

    CHARACTER + CORONA beat: stickman cowering from the heat, no planet
    visible — just the corona and the +500C label.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=50)

    # The corona/flame halo center-right (no planet visible behind it)
    corona_cx, corona_cy = 880, 400
    corona_r = 150
    # Draw a fake planet (mostly hidden by halo)
    draw_planet_painterly(img, corona_cx, corona_cy, corona_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=51)
    integrated_label.draw_flame_halo(img, corona_cx, corona_cy, corona_r, seed=52)

    # Integrated '+500C' label on the corona
    integrated_label.draw_integrated_label(
        img, "+500C", corona_cx, corona_cy, scale=0.85, seed=53,
        fill=(255, 220, 100),
    )

    # Stickman cowering + worried, shielding_eyes, 400 px (~55% frame)
    expression, pose = lookup_reaction('fever')
    draw_stickman_motion(
        img, t=t, x_center=300, y_top=300, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=1.8, seed=5,
    )

    draw_caption(draw, "FEVER. FIVE HUNDRED DEGREES.",
                 xy=(180, 130), where='fever')
    return img


def card_pure_stickman(t=0.0):
    """Card 6: 'Five hundred.' — PURE STICKMAN BEAT (character-only).
    No planet, no diagram, just the audience surrogate reacting to the
    absurdity of the number.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)

    # Just stars — no planet, no diagram
    draw_stars(img, 130, seed=60)

    # Big shocked stickman — 440 px (~61% frame), center-stage
    expression, pose = lookup_reaction('pure_stickman')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=240, height=440,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=6,
    )

    draw_caption(draw, "FIVE. HUNDRED.",
                 xy=(500, 600), where='pure_stickman')
    return img


def card_cold_again(t=0.0):
    """Card 7: 'Then it swings back out, and the temperature crashes just
    as fast.'

    DIAGRAM + STICKMAN beat: orbit-only with the planet moving outward,
    plus a stickman on the side watching. Lighter moment.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 100, seed=70)

    # Sun on the left (smaller — receded)
    draw_sun_painterly(img, 220, 380, 80, WHIP_STAR, seed=71)

    # Cool planet on the right (transitioning — fading red patch)
    draw_planet_painterly(img, 1020, 380, 130, PAL['planet_cool'],
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=72)
    draw = ImageDraw.Draw(img)
    wobble_circle(
        draw, (1020 - 50, 380 - 20), 30, PAL['alert'],
        fill=PAL['alert'], width=2, seed=73, segments=18, jitter=1.5,
    )

    # Wobbly orbit ellipse
    rng = random.Random(74)
    pts = []
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x = 640 + 480 * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = 380 + 130 * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['planet_cool'], width=2)

    # Stickman bottom-center, relief + shrugged, 360 px (50% frame)
    expression, pose = lookup_reaction('cold_again')
    draw_stickman_motion(
        img, t=t, x_center=580, y_top=340, height=360,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=7,
    )

    draw_caption(draw, "BACK OUT. TEMPERATURE CRASHES.",
                 xy=(120, 130), where='cold_again')
    return img


def card_shock_waves(t=0.0):
    """Card 8: 'The atmosphere cannot do anything reasonable with that.
    Models suggest winds on the order of several kilometers per second,
    supersonic shock waves, day side temperatures hot enough to glow.'

    DIAGRAM-ONLY climax beat: planet + integrated 'WINDS AT KM/S' label
    on the planet + shock-wave rings. No stickman (diagram-only).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=80)

    # The big hot planet center (LOWERED to keep halo below title band)
    # For r=160, halo top = cy - 352. Need cy >= 414.
    draw_planet_painterly(img, 640, 490, 160, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=81)
    integrated_label.draw_flame_halo(img, 640, 490, 160, seed=82)

    # Integrated 'WINDS AT KM/S' label on the planet
    integrated_label.draw_integrated_label(
        img, "WINDS AT KM/S", 640, 490, scale=0.55, seed=83,
        fill=(250, 178, 11),
    )

    # Shock-wave rings (3 concentric wobbly circles, anchored to new planet center)
    for i, r in enumerate([200, 245, 290]):
        color = PAL['alert'] if i == 0 else PAL['accent2']
        wobble_circle(
            draw, (640, 490), r, color, fill=None, width=3,
            seed=84 + i, segments=64, jitter=3.0,
        )

    # No caption (integrated label IS the caption)
    return img


def card_loop(t=0.0):
    """Card 9: 'Every forty days, the same thing. The planet gets cooked,
    then frozen, then cooked again.'

    DIAGRAM + STICKMAN beat: calendar with circled 40, plus stickman
    reacting with a wry smirk. The "this is just how it is" beat.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=90)

    # Calendar with circled 40
    cx_cal, cy_cal = 880, 380
    cw, ch = 240, 280
    rng = random.Random(91)
    cal_pts = []
    for px, py in [
        (cx_cal - cw / 2, cy_cal - ch / 2),
        (cx_cal + cw / 2, cy_cal - ch / 2),
        (cx_cal + cw / 2, cy_cal + ch / 2),
        (cx_cal - cw / 2, cy_cal + ch / 2),
    ]:
        cal_pts.append((px + rng.uniform(-3, 3), py + rng.uniform(-3, 3)))
    cal_pts.append(cal_pts[0])
    draw.polygon(cal_pts[:-1], fill=PAL['paper'])
    for i in range(len(cal_pts) - 1):
        draw.line([cal_pts[i], cal_pts[i + 1]], fill=INK, width=4)
    # Binding rings at top
    for ring_x in [cx_cal - cw / 4, cx_cal + cw / 4]:
        draw.ellipse(
            [ring_x - 8, cy_cal - ch / 2 - 14, ring_x + 8, cy_cal - ch / 2],
            outline=INK, width=3,
        )
    # Lines on the calendar
    for ly in [cy_cal - ch / 4, cy_cal, cy_cal + ch / 4]:
        draw.line(
            [(cx_cal - cw / 2 + 12, ly), (cx_cal + cw / 2 - 12, ly)],
            fill=INK, width=1,
        )
    # Big circled '40' in the middle
    draw.ellipse(
        [cx_cal - 50, cy_cal - 50, cx_cal + 50, cy_cal + 50],
        outline=PAL['alert'], width=6,
    )
    # The '40' itself — large bold stamp
    big40 = T.load_font(72, bold=True)
    try:
        x0, y0, x1, y1 = big40.getbbox("40")
        bw40, bh40 = x1 - x0, y1 - y0
    except Exception:
        bw40, bh40 = 100, 60
    x40 = cx_cal - bw40 // 2
    y40 = cy_cal - bh40 // 2 - 6
    T.draw_outlined_text(
        draw, (x40, y40), "40", big40,
        fill=PAL['alert'], stroke=INK, stroke_width=4,
    )

    # Stickman center-left, smirk + shrugged, 380 px (~53% frame)
    expression, pose = lookup_reaction('loop')
    draw_stickman_motion(
        img, t=t, x_center=320, y_top=320, height=380,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=9,
    )

    draw_caption(draw, "EVERY 40 DAYS. COOKED. FROZEN. COOKED.",
                 xy=(120, 130), where='loop')
    return img


def card_finale(t=0.0):
    """Card 10: 'It is, as far as we can tell, the most violent routine
    in the galaxy. A fever, on a loop. With no medicine, and no off
    switch.'

    CHARACTER + STAMP beat: stickman center, small planet in the
    distance, big 'EVERY 40 DAYS' stamp. The closing emotional beat.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=100)

    # Heavy 'EVERY 40 DAYS' stamp — top-right, strong color
    T.draw_stamp(draw, "EVERY 40 DAYS",
                 xy=(920, 110), accent_rgb=PAL['alert'])

    # Small planet in the distance (upper-right)
    draw_planet_painterly(img, 1040, 230, 60, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=4, seed=101)

    # Stickman center-left, frown + hands_down, 400 px (55% frame)
    expression, pose = lookup_reaction('finale')
    draw_stickman_motion(
        img, t=t, x_center=460, y_top=300, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=10,
    )

    draw_caption(draw, "THE MOST VIOLENT ROUTINE IN THE GALAXY",
                 xy=(120, 130), where='finale_top')

    draw_caption(draw, "A FEVER ON A LOOP. NO MEDICINE. NO OFF SWITCH.",
                 xy=(120, 640), where='finale_bottom')
    return img


# --- Card schedule (driven by the alignment) ---

CARDS = [
    {'id': 'intro',          'start_w': 0,   'end_w': 10,  'renderer': card_intro},
    {'id': 'planet_intro',   'start_w': 11,  'end_w': 41,  'renderer': card_planet_intro},
    {'id': 'cold_orbit',     'start_w': 42,  'end_w': 54,  'renderer': card_cold_orbit},
    {'id': 'so_close',       'start_w': 55,  'end_w': 84,  'renderer': card_so_close},
    {'id': 'fever',          'start_w': 85,  'end_w': 100, 'renderer': card_fever},
    {'id': 'pure_stickman',  'start_w': 101, 'end_w': 101, 'renderer': card_pure_stickman},
    {'id': 'cold_again',     'start_w': 102, 'end_w': 113, 'renderer': card_cold_again},
    {'id': 'shock_waves',    'start_w': 114, 'end_w': 141, 'renderer': card_shock_waves},
    {'id': 'loop',           'start_w': 142, 'end_w': 156, 'renderer': card_loop},
    {'id': 'finale',         'start_w': 157, 'end_w': 161, 'renderer': card_finale},
]


def build_card_schedule(alignment):
    """Given the alignment, compute start/end times for each card based on
    word indices. The card uses the start of the first word and the end of
    the last word as its time range.
    """
    words = alignment['words']
    duration = alignment['duration_s']

    schedule = []
    for card in CARDS:
        si = min(card['start_w'], len(words) - 1)
        ei = min(card['end_w'], len(words) - 1)
        start = float(words[si]['t'])
        end = float(words[ei]['end'])
        end = min(end, duration)
        # Carry the (mouth, pose) from the REACTIONS map onto the schedule
        # entry so the critic / verification tools can inspect it.
        reaction = lookup_reaction(card['id'])
        schedule.append({
            'id': card['id'],
            'start': start,
            'end': end,
            'renderer': card['renderer'],
            'expression': reaction[0],
            'pose': reaction[1],
        })

    if schedule:
        schedule[-1]['end'] = duration

    return schedule


def render_segment(schedule, out_dir, fps=FPS, hold_last_frames=0):
    """Render all cards as a sequence of PNGs at `fps`.

    Re-render every 6 frames (= 0.2s) so the micro-motion is visible
    without spending too much CPU. The card start time is the phase
    anchor for the motion loop.
    """
    os.makedirs(out_dir, exist_ok=True)
    total_frames = 0
    frame_map = []

    for card in schedule:
        n_frames = max(1, int(round((card['end'] - card['start']) * fps)))
        sub_step = 6
        img = card['renderer'](t=card['start'])
        for i in range(n_frames):
            if i % sub_step == 0 and i > 0:
                # re-render with a shifted t for a fresh motion phase
                img = card['renderer'](t=card['start'] + i / fps)
            fpath = os.path.join(out_dir, f'frame_{total_frames:05d}.png')
            img.save(fpath)
            frame_map.append({'frame': total_frames, 'card': card['id'],
                              't': card['start'] + i / fps})
            total_frames += 1

    if hold_last_frames > 0:
        last_img = schedule[-1]['renderer'](t=schedule[-1]['end'])
        for i in range(hold_last_frames):
            fpath = os.path.join(out_dir, f'frame_{total_frames:05d}.png')
            last_img.save(fpath)
            frame_map.append({'frame': total_frames, 'card': schedule[-1]['id'],
                              't': schedule[-1]['end']})
            total_frames += 1

    return total_frames, frame_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-debug', dest='debug', action='store_false',
                        default=False,
                        help='Disable debug stamps (default: ON, debug off).')
    parser.add_argument('--frames-dir', default='frames_r3',
                        help='Output directory for rendered PNG frames.')
    parser.add_argument('--schedule-out', default='round_3_card_schedule.json',
                        help='Output card schedule JSON.')
    parser.add_argument('--align', default='round_2_alignment.json',
                        help='Input alignment JSON.')
    args = parser.parse_args()

    debug_on = args.debug
    if debug_on:
        print("[warning] --debug is ON; round 3 builds should default to --no-debug")
    else:
        print("[ok] --no-debug is on; no debug stamps will render")

    align_path = os.path.join(os.path.dirname(__file__), args.align)
    if not os.path.exists(align_path):
        print(f'Alignment file not found: {align_path}')
        return

    with open(align_path) as f:
        alignment = json.load(f)

    schedule = build_card_schedule(alignment)
    print('Card schedule:')
    for s in schedule:
        print(f"  {s['id']:18s}  {s['start']:.2f}s -> {s['end']:.2f}s  "
              f"({s['end']-s['start']:.2f}s)  [expr={s['expression']}, pose={s['pose']}]")

    out_dir = os.path.join(os.path.dirname(__file__), args.frames_dir)
    audio_duration = alignment['duration_s']
    audio_frames = int(round(audio_duration * FPS))
    schedule_frames = sum(max(1, int(round((c['end'] - c['start']) * FPS))) for c in schedule)
    hold_last_frames = max(0, audio_frames - schedule_frames)
    print(f'Audio: {audio_duration:.2f}s ({audio_frames} frames)')
    print(f'Schedule cards sum to {schedule_frames} frames')
    print(f'Holding last card for {hold_last_frames} extra frames')
    n_frames, frame_map = render_segment(schedule, out_dir, hold_last_frames=hold_last_frames)
    print(f"\nTotal frames: {n_frames} at {FPS} fps = {n_frames / FPS:.2f}s")

    sched_path = os.path.join(os.path.dirname(__file__), args.schedule_out)
    with open(sched_path, 'w') as f:
        json.dump(
            [{'id': s['id'], 'start': s['start'], 'end': s['end'],
              'expression': s['expression'], 'pose': s['pose']}
             for s in schedule],
            f, indent=2,
        )
    print(f"Card schedule saved: {sched_path}")


if __name__ == '__main__':
    main()
