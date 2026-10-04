# work/segments/hd80606/_frames_r4.py
# Round 4 build for segment 2 (HD 80606 b — the whiplash planet).
#
# Round 3 was ref_wins with biggest gap:
#   "Caption-on-diagram integration and palette discipline. Ref overlays
#    huge yellow ALL-CAPS text as the visual event itself. Ours leaves
#    multiple diagram beats (t14, t20, t28) caption-less against empty
#    black starfields, which kills the beat rhythm."
#
# Round 4 fixes (per the round-3 critic's round_4_directives):
#   1. INTEGRATE CAPTIONS ONTO DIAGRAMS. Overlay heavy ALL-CAPS text
#      (60-80pt, thick black outline) directly on the planet, the sun,
#      the orbit line.
#   2. LOCK PALETTE TO ORANGE / YELLOW / BLACK / CREAM. Five hues max.
#      Sun=yellow/orange, planet=orange/red, orbit=cream, bg=black,
#      text=yellow or orange with black outline.
#   3. ADD FIRE / SPIKE AURA around the close-pass planet in t14/t20/t28
#      (and the t02 intro). Visual code for 'this planet is being cooked'.
#   4. ADD HEADER BAND ('HD 80606 B') on every frame, 72pt wobbly
#      hand-lettered, segment accent color.
#   5. ADD PAINTERLY STIPPLE to the planet portrait — banded gas-giant
#      with hand-drawn striations and 1-2px black stipple dots. NOT a
#      smooth gradient.
#   6. PUT STICKMAN IN MORE BEATS — target >=4 of 6 frames. Round 3 had
#      stickman in 3 of 6. Round 4 has stickman in 13 of 15 cards.
#   7. UPGRADE TYPE WEIGHT — heavy black-outlined ALL CAPS that read
#      against any background, or 60pt+ with 3-4px black outline.
#   8. SNAP-CUT ON 'EVERY 40 DAYS' — keep ours_t36 stamp card pattern.
#      Round 4 has snap cuts at every clause break (15 cards now, was 10).
#   9. DIAGRAM HOLDS MUST CARRY INFORMATION — snap-cut to a new diagram
#      card at the clause break. No static 6-second holds.
#
# Per CLAUDE.md §6: the stickman must be present in at least one beat.
# Round 4 has him in 13 of 15 cards.
#
# Round 3 wins preserved: white title band, painterly stipple/gradient
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

from PIL import Image, ImageDraw, ImageFont
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

# Round 4 PALETTE: LOCKED to orange / yellow / black / cream
# Five hues max. No blue, no red/blue gradient, no cyan.
PAL = {
    'name': 'HD 80606 b',
    'ink': (0, 0, 0),                       # black ink
    'paper': (250, 232, 200),               # warm cream paper
    'bg': (10, 4, 2),                       # very dark brown-black (not pure blue-black)
    'accent1': (255, 200, 60),              # warm yellow — the day side / caption
    'accent2': (255, 110, 25),              # orange — the heat
    'accent3': (255, 240, 180),             # cream highlights
    'deep': (60, 18, 4),                    # dark red-brown
    'alert': (255, 70, 10),                 # bright red — for "worse is coming" beats
    'planet': (255, 140, 40),               # warm orange — the planet
    'planet_cool': (200, 130, 60),          # dim cool tone (NOT blue) — cold side
    'planet_dark': (160, 60, 20),           # dark red — deep heat
    'caption': (255, 215, 60),              # yellow floating captions
}

INK = PAL['ink']

# Hard caption constraints (per CLAUDE.md §7)
MAX_CAPTION_CHARS = 60
CAPTION_FONT = T.load_font(T.CAPTION_PX, bold=False)
DRAW_FONT_BOLD = T.load_font(T.CAPTION_PX, bold=True)

# Heavy-caption font (for integrated diagram labels, 60-80pt)
HEAVY_CAPTION_PX = 64
HEAVY_CAPTION_FONT = T.load_font(HEAVY_CAPTION_PX, bold=True)


# --- Local stickman halo wrapper (segment 2 only) ---
# Same as round 3: cream halo under black stroke for dark-bg visibility.

_STICK_HALO_RGB = (250, 232, 200)   # cream
_STICK_HALO_W = 6
_STICK_INK = (0, 0, 0)
_STICK_HEAD_FILL = (255, 245, 220)


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
    if _STICK_HALO_W > 0:
        draw.ellipse(
            [cx - r - _STICK_HALO_W, cy - r - _STICK_HALO_W,
             cx + r + _STICK_HALO_W, cy + r + _STICK_HALO_W],
            fill=_STICK_HALO_RGB,
        )
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_STICK_INK)


def _draw_haloed_stickman(image, x_center, y_top, height, pose, mouth, seed,
                          draw_image=None, scale=1.0):
    """Segment-2 local stickman with cream halo for visibility on dark bg."""
    if draw_image is None:
        draw_image = image
    d = ImageDraw.Draw(draw_image)
    # Geometry
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
        _halo_line(d, (x_center, neck_y + 4),
                   (x_center - int(head_r * 0.9), hip_y - 4), _STICK_INK, 2)
        _halo_disc(d, x_center - int(head_r * 0.9), hip_y - 4, 2)
        point_x = x_center + int(height * 0.5)
        point_y = neck_y + int(height * 0.1)
        _halo_line(d, (x_center, neck_y), (point_x, point_y), _STICK_INK, 2)
        _halo_disc(d, point_x, point_y, 2)
    elif pose == 'cowering':
        arm_y = neck_y + int(head_r * 0.5)
        arm_dx = int(head_r * 0.4)
        _halo_line(d, (x_center, arm_y),
                   (x_center + arm_dx, arm_y - int(head_r * 0.3)), _STICK_INK, 2)
        _halo_disc(d, x_center + arm_dx, arm_y - int(head_r * 0.3), 2)
        _halo_line(d, (x_center, arm_y),
                   (x_center - arm_dx, arm_y - int(head_r * 0.3)), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_dx, arm_y - int(head_r * 0.3), 2)
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

    # Mouth
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
        w = int(6 * scale)
        d.arc([x_center - w, mouth_cy - int(2 * scale),
               x_center + w, mouth_cy + int(4 * scale)],
              180, 360, fill=_STICK_INK, width=2)
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
        w = int(7 * scale)
        d.arc([x_center - w, mouth_cy - int(2 * scale),
               x_center + w, mouth_cy + int(2 * scale)],
              0, 180, fill=_STICK_INK, width=2)
    elif mouth == 'terrified':
        w, h = 10, 8
        d.ellipse([x_center - w, mouth_cy - h, x_center + w, mouth_cy + h],
                  outline=_STICK_INK, width=3)
    return {'head_cy': head_cy, 'head_r': head_r, 'foot_y': foot_y}


# --- Per-beat REACTIONS map (round 4 character contract) ---
# HD 80606 b emotional arc: awed -> awed -> squint (overwhelmed) -> scream
# (so close!) -> terrified (4 days from cooked!) -> worried (fever starts) ->
# scream (+500C) -> scream (Five Hundred!) -> relief (back out) ->
# terrified (atmosphere can't) -> scream (km/s!) -> terrified (supersonic!) ->
# smirk (every 40 days) -> scream (cooked.frozen.cooked) -> frown (finale)

REACTIONS = {
    'intro':           ('oval',      'hands_up'),
    'planet_intro':    ('oval',      'standing'),
    'cold_orbit':      ('squint',    'pointing'),
    'so_close_part1':  ('scream',    'cowering'),
    'so_close_part2':  ('terrified', 'cowering'),
    'fever_intro':     ('worried',   'shielding_eyes'),
    'fever_spike':     ('scream',    'cowering'),
    'pure_stickman':   ('scream',    'cowering'),
    'cold_again':      ('relief',    'shrugged'),
    'shock_waves':     ('terrified', 'cowering'),
    'km_per_sec':      ('scream',    'cowering'),
    'supersonic':      ('terrified', 'cowering'),
    'every_40':        ('smirk',     'shrugged'),
    'cooked_frozen':   ('scream',    'cowering'),
    'finale':          ('frown',     'hands_down'),
}


def lookup_reaction(card_id):
    """Return (expression, pose) for a given card id, defaulting to a
    deadpan/standing pair if not mapped."""
    return REACTIONS.get(card_id, ('flat', 'standing'))


def draw_stickman_motion(image, t, x_center, y_top, height, pose, mouth,
                         seed=0, beat_period_s=2.0):
    """Draw the stickman with a 1-2s micro-loop based on `t`."""
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
    """Hard check: fail the build if the caption violates §7."""
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


def draw_heavy_caption(draw, text, xy, color_rgb, where='heavy_caption'):
    """Heavy caption (60-80pt) for integrated diagram labels. NO max-length
    check — these are diagram elements, not caption-band text."""
    text_upper = text.upper()
    draw.text(
        xy, text_upper,
        font=HEAVY_CAPTION_FONT,
        fill=color_rgb,
        stroke_width=4, stroke_fill=INK,
    )


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
    """Render a painterly sun (radial gradient + stipple + soft halo).
    LOCKED PALETTE: yellow / orange / red / dark red only."""
    texture.sun_disc(img, cx, cy, r, palette=palette_dict, seed=seed, halo=True)


def draw_planet_painterly(img, cx, cy, r, base_rgb, palette_dict=None,
                          n_bands=4, seed=0, with_bands=True,
                          with_hand_striations=True, with_painterly_stipple=True):
    """Render a painterly planet (banded + radial gradient + stipple +
    hand-drawn striations + heavy 1-2px black stipple dots).

    Round 4 fix per directive 5: ADD PAINTERLY STIPPLE + HAND STRIATIONS.
    """
    texture.planet_disc(img, cx, cy, r, base_rgb=base_rgb,
                        palette=palette_dict, n_bands=n_bands,
                        seed=seed, with_bands=with_bands)
    if with_hand_striations:
        _add_hand_striations(img, cx, cy, r, seed=seed + 100)
    if with_painterly_stipple:
        _add_painterly_stipple(img, cx, cy, r, seed=seed + 200)


def _add_hand_striations(img, cx, cy, r, seed=0):
    """Add 3-5 hand-drawn wobbly horizontal lines across the planet
    (the 'gas-giant striation' signature from the reference)."""
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    n_striations = rng.randint(3, 5)
    disc_mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )
    mask_px = disc_mask.load()
    for i in range(n_striations):
        # y position within the disc
        y = cy - r * 0.6 + (1.2 * r) * (i + 0.5) / n_striations + rng.uniform(-5, 5)
        if abs(y - cy) > r - 4:
            continue
        # build a wobbly horizontal line
        half_w = math.sqrt(max(0.0, r * r - (y - cy) ** 2)) * 0.85
        x_start = int(cx - half_w)
        x_end = int(cx + half_w)
        if x_end - x_start < 20:
            continue
        # wobbly polylines
        n_seg = 12
        pts = []
        for s in range(n_seg + 1):
            t = s / n_seg
            x = x_start + (x_end - x_start) * t
            jx = rng.uniform(-2, 2)
            jy = rng.uniform(-1, 1)
            px = int(x + jx)
            py = int(y + jy)
            # clip to disc
            if 0 <= px < img.size[0] and 0 <= py < img.size[1] and mask_px[px, py] > 128:
                pts.append((px, py))
        if len(pts) > 1:
            # Pick line color: dark brown/black for contrast
            draw.line(pts, fill=(40, 12, 4), width=2)


def _add_painterly_stipple(img, cx, cy, r, seed=0):
    """Add heavy 1-2px black stipple dots across the planet (the painterly
    'spray-paint grain' the reference uses on planet portraits)."""
    rng = random.Random(seed)
    disc_mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )
    mask_px = disc_mask.load()
    w, h = img.size
    px = img.load()
    # Number of black stipple dots scales with disc area
    n_dots = int(2 * math.pi * r * r * 0.012)  # ~1.2% of disc area
    for _ in range(n_dots):
        # Reject-sample inside the disc
        for _try in range(8):
            x = cx + rng.uniform(-r, r)
            y = cy + rng.uniform(-r, r)
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                break
        else:
            continue
        ix, iy = int(x), int(y)
        if 0 <= ix < w and 0 <= iy < h and mask_px[ix, iy] > 128:
            # 1-2px black dot
            px[ix, iy] = (0, 0, 0)
            if rng.random() < 0.5:
                # also dot a neighbor
                dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                nx, ny = ix + dx, iy + dy
                if 0 <= nx < w and 0 <= ny < h and mask_px[nx, ny] > 128:
                    px[nx, ny] = (0, 0, 0)
    # A few bright cream highlights too (the paint-explainer's spray-paint
    # grain is bi-tonal: light AND dark).
    n_hl = int(2 * math.pi * r * r * 0.005)
    for _ in range(n_hl):
        for _try in range(8):
            x = cx + rng.uniform(-r, r)
            y = cy + rng.uniform(-r, r)
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r * 0.7 * 0.7:
                break
        else:
            continue
        ix, iy = int(x), int(y)
        if 0 <= ix < w and 0 <= iy < h and mask_px[ix, iy] > 128:
            px[ix, iy] = (255, 240, 200)


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


# --- Sun palette (LOCKED orange/yellow only, no red/blue) ---

WHIP_STAR = {
    'core':  (255, 240, 130),    # bright yellow core
    'mid':   (255, 170, 30),     # warm yellow-orange
    'outer': (255, 100, 20),     # red-orange
    'halo':  (180, 50, 10),      # dark red-orange halo
}

# Hot day-side palette for the planet (LOCKED warm tones, no blue/red)
HOT_PLANET_PALETTE = {
    'bands': [
        (255, 220, 100),    # bright yellow band
        (255, 120, 30),     # orange band
        (255, 180, 60),     # yellow band
        (200, 70, 20),      # dark red-orange
        (255, 230, 120),   # light highlight band
    ],
    'light': (255, 230, 130),
    'deep':  (130, 40, 12),
}

# Cool far-orbit palette — DULL warm tone (NOT blue, per directive 2)
# The "cool" planet is just a dimmer version of the warm palette.
COOL_PLANET_PALETTE = {
    'bands': [
        (180, 110, 50),
        (140, 80, 35),
        (200, 130, 60),
        (110, 60, 25),
        (210, 140, 70),
    ],
    'light': (200, 140, 70),
    'deep':  (80, 35, 12),
}


# --- CARDS ---
# Round 4: 15 cards (was 10). Snap cuts at every clause break.
# Stickman in 13 of 15 cards (was 10 of 10 in r3, but r3 only had 10 cards).
# Every card has a HEAVY INTEGRATED CAPTION on the diagram.

# Stickman height 50-60% of frame height
STICKMAN_HEIGHT = 400  # ~55% of 720


def card_intro(t=0.0):
    """Card 1: 'Now imagine a planet that gets a fever every forty days.'
    TITLE-CARD beat: planet + fire aura + integrated 'HD 80606 B' label.
    Stickman 55% center-left, awed + hands-up.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 90, seed=10)

    # Big painterly planet center-right with fire aura
    planet_cx, planet_cy = 860, 480
    planet_r = 180
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=11)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=12)

    # Integrated hand-lettered 'HD 80606 B' label ON the planet (heavy)
    integrated_label.draw_integrated_label(
        img, "HD 80606 B", planet_cx, planet_cy, scale=0.55, seed=13,
        fill=(255, 220, 100),
    )

    # Stickman center-left, hands-up + oval mouth (awed), 400 px (~55%)
    expression, pose = lookup_reaction('intro')
    draw_stickman_motion(
        img, t=t, x_center=380, y_top=300, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=1,
    )

    # Heavy integrated caption top-left: 'A FEVER EVERY FORTY DAYS'
    draw_heavy_caption(draw, "A FEVER EVERY 40 DAYS",
                       xy=(80, 130), color_rgb=(255, 220, 100),
                       where='intro_heavy')
    return img


def card_planet_intro(t=0.0):
    """Card 2: 'HD 80606 b. A gas giant about four times the mass of
    Jupiter, on an orbit so stretched out it looks like someone drew it
    with a ruler and then bent the ruler.'

    CHARACTER-ONLY beat: stickman center-stage reacting, with stamp card.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=20)

    # Heavy '4 X JUPITER' stamp — top-right, strong color
    T.draw_stamp(draw, "4 X JUPITER",
                 xy=(940, 110), accent_rgb=(255, 220, 100))

    # Heavy caption top-left
    draw_heavy_caption(draw, "A GAS GIANT ON A WILD ORBIT",
                       xy=(80, 130), color_rgb=(255, 220, 100),
                       where='planet_intro_heavy')

    # Stickman center, awed + standing, 400 px (55% frame)
    expression, pose = lookup_reaction('planet_intro')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=240, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=2,
    )
    return img


def card_cold_orbit(t=0.0):
    """Card 3: 'Most of the time, it sits far from its star. Cold. Quiet.
    Average.'

    DIAGRAM-ONLY beat with INTEGRATED CAPTION: cool planet on the right
    with 'COLD. QUIET. AVERAGE.' stamped ON the planet. No stickman —
    the diagram breathes.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 120, seed=30)

    # Tiny warm star on the far left
    draw_sun_painterly(img, 160, 400, 50, WHIP_STAR, seed=31)

    # Dim cool planet on the right (NO blue — warm dull tone per directive 2)
    planet_cx, planet_cy = 1000, 400
    planet_r = 110
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, (160, 100, 50),
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=32)

    # Wobbly cream orbit ellipse
    rng = random.Random(33)
    pts = []
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x = 640 + 480 * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = 400 + 130 * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(250, 232, 200), width=2)

    # INTEGRATED caption ON the planet: 'COLD. QUIET. AVERAGE.'
    integrated_label.draw_integrated_label(
        img, "COLD. QUIET. AVERAGE.", planet_cx, planet_cy, scale=0.32, seed=34,
        fill=(250, 232, 200),
    )
    return img


def card_so_close_part1(t=0.0):
    """Card 4: 'And then it swings in close. Very close.'

    DIAGRAM+STICKMAN. Star on right, planet on left with fire aura.
    Integrated 'SO CLOSE' label on planet. Stickman cowering left.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=40)

    # The big star (sun) on the right
    draw_sun_painterly(img, 1020, 480, 140, WHIP_STAR, seed=41)

    # The planet on the left, engulfed in flame halo
    planet_cx, planet_cy = 480, 480
    planet_r = 150
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=42)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=43)

    # Integrated 'SO CLOSE' label ON the planet
    integrated_label.draw_integrated_label(
        img, "SO CLOSE", planet_cx, planet_cy, scale=1.1, seed=44,
        fill=(255, 230, 110),
    )

    # Stickman left, cowering + scream, 380 px (~53% frame)
    expression, pose = lookup_reaction('so_close_part1')
    draw_stickman_motion(
        img, t=t, x_center=180, y_top=320, height=380,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=4,
    )
    return img


def card_so_close_part2(t=0.0):
    """Card 5: 'So close that the side facing the star gets hit with about
    eight hundred times more starlight than the side facing away.'

    DIAGRAM+STICKMAN. Same composition. Integrated '4 DAYS FROM COOKED'
    (the 800x more starlight = '4 days from cooked' is a rough
    equivalent — close enough to convey the message).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=50)

    # The big star (sun) on the right
    draw_sun_painterly(img, 1020, 480, 140, WHIP_STAR, seed=51)

    # The planet on the left, engulfed in flame halo
    planet_cx, planet_cy = 480, 480
    planet_r = 150
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=52)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=53)

    # Integrated '800 X STARLIGHT' label ON the planet
    integrated_label.draw_integrated_label(
        img, "800X STARLIGHT", planet_cx, planet_cy, scale=0.55, seed=54,
        fill=(255, 230, 110),
    )

    # Stickman right, terrified + cowering, 380 px (~53% frame)
    expression, pose = lookup_reaction('so_close_part2')
    draw_stickman_motion(
        img, t=t, x_center=1080, y_top=320, height=380,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=5,
    )

    # Heavy caption top
    draw_heavy_caption(draw, "PERIHELION",
                       xy=(80, 130), color_rgb=(255, 220, 100),
                       where='so_close_part2_heavy')
    return img


def card_fever_intro(t=0.0):
    """Card 6: 'In a few hours, the temperature on the day side...'

    DIAGRAM+STICKMAN. Corona on right + integrated 'FEVER' label.
    Stickman left, shielding eyes from heat, 380 px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=60)

    # The corona/flame halo center-right
    corona_cx, corona_cy = 880, 400
    corona_r = 150
    draw_planet_painterly(img, corona_cx, corona_cy, corona_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=61)
    integrated_label.draw_flame_halo(img, corona_cx, corona_cy, corona_r, seed=62)

    # Integrated 'FEVER' label on the corona
    integrated_label.draw_integrated_label(
        img, "FEVER", corona_cx, corona_cy, scale=0.95, seed=63,
        fill=(255, 240, 110),
    )

    # Stickman left, shielding_eyes + worried, 380 px (~53% frame)
    expression, pose = lookup_reaction('fever_intro')
    draw_stickman_motion(
        img, t=t, x_center=300, y_top=320, height=380,
        pose=pose, mouth=expression, beat_period_s=1.8, seed=6,
    )
    return img


def card_fever_spike(t=0.0):
    """Card 7: 'spikes by five hundred degrees Celsius'

    DIAGRAM+STICKMAN. Corona with integrated '+500C' label.
    Stickman cowering, 380px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=70)

    # The corona/flame halo center-right
    corona_cx, corona_cy = 880, 400
    corona_r = 150
    draw_planet_painterly(img, corona_cx, corona_cy, corona_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=71)
    integrated_label.draw_flame_halo(img, corona_cx, corona_cy, corona_r, seed=72)

    # Integrated '+500C' label on the corona
    integrated_label.draw_integrated_label(
        img, "+500C", corona_cx, corona_cy, scale=0.95, seed=73,
        fill=(255, 220, 100),
    )

    # Stickman left, cowering + scream, 380 px (~53% frame)
    expression, pose = lookup_reaction('fever_spike')
    draw_stickman_motion(
        img, t=t, x_center=300, y_top=320, height=380,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=7,
    )
    return img


def card_pure_stickman(t=0.0):
    """Card 8: 'Five hundred.' — PURE STICKMAN BEAT.
    No planet, no diagram, just the stickman reacting to the number.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 130, seed=80)

    # Big shocked stickman — 440 px (~61% frame), center-stage
    expression, pose = lookup_reaction('pure_stickman')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=220, height=440,
        pose=pose, mouth=expression, beat_period_s=1.4, seed=8,
    )

    # Heavy caption bottom-center
    draw_heavy_caption(draw, "FIVE. HUNDRED.",
                       xy=(440, 620), color_rgb=(255, 220, 100),
                       where='pure_stickman_heavy')
    return img


def card_cold_again(t=0.0):
    """Card 9: 'Then it swings back out, and the temperature crashes just
    as fast.'

    DIAGRAM+STICKMAN. Cool planet back to right side. Integrated 'BACK OUT'
    label on planet. Stickman relief/shrugged 360px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 100, seed=90)

    # Sun on the left (smaller — receded)
    draw_sun_painterly(img, 220, 380, 80, WHIP_STAR, seed=91)

    # Cool planet on the right (dim warm tone, NOT blue)
    planet_cx, planet_cy = 1020, 380
    planet_r = 130
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, (160, 100, 50),
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=92)

    # Wobbly cream orbit ellipse
    rng = random.Random(93)
    pts = []
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x = 640 + 480 * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = 380 + 130 * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(250, 232, 200), width=2)

    # Integrated 'BACK OUT' label on the planet
    integrated_label.draw_integrated_label(
        img, "BACK OUT", planet_cx, planet_cy, scale=0.65, seed=94,
        fill=(250, 232, 200),
    )

    # Stickman center, relief + shrugged, 360 px (50% frame)
    expression, pose = lookup_reaction('cold_again')
    draw_stickman_motion(
        img, t=t, x_center=580, y_top=340, height=360,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=9,
    )
    return img


def card_shock_waves(t=0.0):
    """Card 10: 'The atmosphere cannot do anything reasonable with that.'

    DIAGRAM+STICKMAN. Hot planet center with fire aura + integrated
    'NOTHING REASONABLE' label. Stickman cowering left 360px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=100)

    # The big hot planet center
    planet_cx, planet_cy = 760, 430
    planet_r = 160
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=101)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=102)

    # Integrated 'NOTHING REASONABLE' label on the planet
    integrated_label.draw_integrated_label(
        img, "NOTHING", planet_cx, planet_cy - 30, scale=0.85, seed=103,
        fill=(255, 230, 110),
    )
    integrated_label.draw_integrated_label(
        img, "REASONABLE", planet_cx, planet_cy + 50, scale=0.7, seed=104,
        fill=(255, 230, 110),
    )

    # Stickman left, terrified + cowering, 360 px
    expression, pose = lookup_reaction('shock_waves')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=340, height=360,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=10,
    )
    return img


def card_km_per_sec(t=0.0):
    """Card 11: 'Model suggests winds on the order of several kilometers
    per second.'

    DIAGRAM+STICKMAN. Hot planet with fire aura + integrated 'WINDS AT
    KM/S' label. Stickman cowering + screaming 360px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=110)

    # The big hot planet center
    planet_cx, planet_cy = 760, 430
    planet_r = 160
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=111)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=112)

    # Integrated 'WINDS AT KM/S' label on the planet
    integrated_label.draw_integrated_label(
        img, "WINDS AT KM/S", planet_cx, planet_cy, scale=0.5, seed=113,
        fill=(255, 230, 110),
    )

    # Stickman left, cowering + scream, 360 px
    expression, pose = lookup_reaction('km_per_sec')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=340, height=360,
        pose=pose, mouth=expression, beat_period_s=1.4, seed=11,
    )
    return img


def card_supersonic(t=0.0):
    """Card 12: 'Supersonic shockwaves, day-side temperatures hot enough
    to glow.'

    DIAGRAM+STICKMAN. Hot planet with shock-wave rings + integrated
    'SUPERSONIC' label. Stickman cowering 360px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=120)

    # The big hot planet center
    planet_cx, planet_cy = 760, 430
    planet_r = 160
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=121)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=122)

    # Integrated 'SUPERSONIC' label on the planet
    integrated_label.draw_integrated_label(
        img, "SUPERSONIC", planet_cx, planet_cy, scale=0.55, seed=123,
        fill=(255, 230, 110),
    )

    # Shock-wave rings (3 concentric wobbly circles)
    for i, r in enumerate([200, 245, 290]):
        color = (255, 100, 20) if i == 0 else (255, 180, 60)
        wobble_circle(
            draw, (planet_cx, planet_cy), r, color, fill=None, width=3,
            seed=124 + i, segments=64, jitter=3.0,
        )

    # Stickman left, terrified + cowering, 360 px
    expression, pose = lookup_reaction('supersonic')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=340, height=360,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=12,
    )
    return img


def card_every_40(t=0.0):
    """Card 13: 'Every 40 days, the same thing.'

    STAMP CARD. Calendar with circled '40'. Stickman left smirk/shrugged
    360px. Heavy 'EVERY 40 DAYS' caption top.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=130)

    # Calendar with circled 40
    cx_cal, cy_cal = 880, 380
    cw, ch = 240, 280
    rng = random.Random(131)
    cal_pts = []
    for px, py in [
        (cx_cal - cw / 2, cy_cal - ch / 2),
        (cx_cal + cw / 2, cy_cal - ch / 2),
        (cx_cal + cw / 2, cy_cal + ch / 2),
        (cx_cal - cw / 2, cy_cal + ch / 2),
    ]:
        cal_pts.append((px + rng.uniform(-3, 3), py + rng.uniform(-3, 3)))
    cal_pts.append(cal_pts[0])
    draw.polygon(cal_pts[:-1], fill=(250, 232, 200))
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
        outline=(255, 100, 20), width=6,
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
        fill=(255, 100, 20), stroke=INK, stroke_width=4,
    )

    # Stickman center-left, smirk + shrugged, 380 px (~53% frame)
    expression, pose = lookup_reaction('every_40')
    draw_stickman_motion(
        img, t=t, x_center=320, y_top=320, height=380,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=13,
    )

    # Heavy caption top
    draw_heavy_caption(draw, "EVERY 40 DAYS",
                       xy=(80, 130), color_rgb=(255, 220, 100),
                       where='every_40_heavy')
    return img


def card_cooked_frozen(t=0.0):
    """Card 14: 'The planet gets cooked, then frozen, then cooked again.'

    DIAGRAM+STICKMAN. Hot planet on left, cool planet on right
    (alternating — the 'fever' state). Integrated 'COOKED' on the
    hot one. Stickman cowering center 360px.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=140)

    # Hot planet (left, engulfed in flame halo)
    hot_cx, hot_cy, hot_r = 300, 440, 110
    draw_planet_painterly(img, hot_cx, hot_cy, hot_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=141)
    integrated_label.draw_flame_halo(img, hot_cx, hot_cy, hot_r, seed=142)
    integrated_label.draw_integrated_label(
        img, "COOKED", hot_cx, hot_cy, scale=0.7, seed=143,
        fill=(255, 240, 110),
    )

    # Cool planet (right, dim warm tone)
    cool_cx, cool_cy, cool_r = 980, 440, 110
    draw_planet_painterly(img, cool_cx, cool_cy, cool_r, (160, 100, 50),
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=144)
    integrated_label.draw_integrated_label(
        img, "FROZEN", cool_cx, cool_cy, scale=0.7, seed=145,
        fill=(250, 232, 200),
    )

    # Stickman center, cowering + scream, 360 px (~50% frame)
    expression, pose = lookup_reaction('cooked_frozen')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=320, height=360,
        pose=pose, mouth=expression, beat_period_s=1.4, seed=14,
    )
    return img


def card_finale(t=0.0):
    """Card 15: 'It is, as far as we can tell, the most violent routine
    in the galaxy. A fever, on a loop. With no medicine, and no off
    switch.'

    CHARACTER beat: stickman center 400px, frown/hands_down.
    Heavy 'THE MOST VIOLENT ROUTINE' top caption.
    Heavy 'A FEVER ON A LOOP' bottom caption.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=150)

    # Stickman center, frown + hands_down, 400 px (55% frame)
    expression, pose = lookup_reaction('finale')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=300, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=15,
    )

    # Heavy 'THE MOST VIOLENT ROUTINE' top caption
    draw_heavy_caption(draw, "THE MOST VIOLENT ROUTINE",
                       xy=(180, 110), color_rgb=(255, 220, 100),
                       where='finale_top_heavy')
    # Heavy 'A FEVER ON A LOOP' bottom caption
    draw_heavy_caption(draw, "A FEVER ON A LOOP",
                       xy=(360, 640), color_rgb=(255, 220, 100),
                       where='finale_bottom_heavy')
    return img


# --- Card schedule (driven by the alignment) ---

CARDS = [
    {'id': 'intro',           'start_w': 0,   'end_w': 10,  'renderer': card_intro},
    {'id': 'planet_intro',    'start_w': 11,  'end_w': 41,  'renderer': card_planet_intro},
    {'id': 'cold_orbit',      'start_w': 42,  'end_w': 54,  'renderer': card_cold_orbit},
    {'id': 'so_close_part1',  'start_w': 55,  'end_w': 62,  'renderer': card_so_close_part1},
    {'id': 'so_close_part2',  'start_w': 63,  'end_w': 84,  'renderer': card_so_close_part2},
    {'id': 'fever_intro',     'start_w': 85,  'end_w': 95,  'renderer': card_fever_intro},
    {'id': 'fever_spike',     'start_w': 96,  'end_w': 100, 'renderer': card_fever_spike},
    {'id': 'pure_stickman',   'start_w': 101, 'end_w': 101, 'renderer': card_pure_stickman},
    {'id': 'cold_again',      'start_w': 102, 'end_w': 113, 'renderer': card_cold_again},
    {'id': 'shock_waves',     'start_w': 114, 'end_w': 124, 'renderer': card_shock_waves},
    {'id': 'km_per_sec',      'start_w': 125, 'end_w': 137, 'renderer': card_km_per_sec},
    {'id': 'supersonic',      'start_w': 138, 'end_w': 145, 'renderer': card_supersonic},
    {'id': 'every_40',        'start_w': 146, 'end_w': 152, 'renderer': card_every_40},
    {'id': 'cooked_frozen',   'start_w': 153, 'end_w': 161, 'renderer': card_cooked_frozen},
    {'id': 'finale',          'start_w': 157, 'end_w': 161, 'renderer': card_finale},
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
    parser.add_argument('--frames-dir', default='frames_r4',
                        help='Output directory for rendered PNG frames.')
    parser.add_argument('--schedule-out', default='round_4_card_schedule.json',
                        help='Output card schedule JSON.')
    parser.add_argument('--align', default='round_2_alignment.json',
                        help='Input alignment JSON.')
    parser.add_argument('--verify-only', action='store_true',
                        help='Render only the 6 verification frames.')
    args = parser.parse_args()

    debug_on = args.debug
    if debug_on:
        print("[warning] --debug is ON; round 4 builds should default to --no-debug")
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
    os.makedirs(out_dir, exist_ok=True)

    if args.verify_only:
        # Render only the 6 verification frames at 2, 8, 14, 20, 28, 36s
        # Use a 0.2s nudge so we land inside cards (some have 0.2s gaps)
        verify_times = [2.0, 8.0, 14.5, 20.0, 28.0, 36.0]
        for vt in verify_times:
            # Find the card that contains vt
            card = None
            for s in schedule:
                if s['start'] <= vt < s['end']:
                    card = s
                    break
            if card is None:
                # Find the nearest card
                card = min(schedule, key=lambda s: abs(s['start'] - vt))
            t_label = f"{vt:.0f}"
            img = card['renderer'](t=vt)
            fpath = os.path.join(out_dir, f'verify_t{t_label}.png')
            img.save(fpath)
            print(f"  verify_t{t_label}.png  ({card['id']}, t={vt:.2f}s)")
        return

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
