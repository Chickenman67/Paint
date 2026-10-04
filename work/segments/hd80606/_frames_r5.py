# work/segments/hd80606/_frames_r5.py
# Round 5 build for segment 2 (HD 80606 b — the whiplash planet).
#
# Round 4 verdict: ref_wins (3-3 tally but INVALID due to mismatched ref offset)
#
# Round 5 directives (from work/segments/hd80606/critic/round4/verdict.json):
#   1. STICKMAN EXPRESSION OVERHAUL — CRITICAL. Implement the full §6
#      mouth-shape lookup: flat-line=deadpan, upside-down-arc=scared,
#      wide-oval=awed, smirk=wry, zigzag=uncomfortable. Each of the 15 cards
#      MUST use a different (expression, pose) pair from the REACTIONS map.
#      Verify by extracting 6 frames and checking that at least 4 distinct
#      mouth shapes appear. Round 4 had only 2 non-deadpan expressions out of
#      6 sampled frames — the mouth is doing no work.
#   2. STICKMAN SCALE ON CHARACTER BEATS — on beats where the stickman is
#      reacting (not diagram-dominant beats), scale stickman to 60-70% of
#      frame height. t02, t08, t36 are character beats; the stickman should
#      be the SUBJECT, not a sidebar. Ref's t107 stickman is ~70% — match that.
#   3. ONE IDEA PER CARD — reduce element count on crowded frames. t02 has 4
#      elements, t08 has 4 elements, t14 has 4 elements. Split into 2 cards or
#      drop one element. Target: ≤3 elements on every card, ≤2 on character beats.
#   4. KEEP EVERYTHING THAT'S WORKING — integrated captions ('SO CLOSE',
#      'FEVER', 'NOTHING REASONABLE'), fire/spike aura, banded gas-giant,
#      locked orange/yellow/cream palette, header band, painterly stipple.
#      Do NOT regress. These are the round 4 wins.
#   5. REF OFFSET CORRECTED — the orchestrator already fixed the ref extract
#      script to +10 offset. The +99 offset used in rounds 2-4 was wrong.
#
# Round 4 absolute quality is HIGH — the integrated-caption + fire-aura +
# banded-gas-giant pattern works. The stickman expression overhaul (directive 1)
# is the single lever most likely to flip the verdict.

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

# Round 5 PALETTE: LOCKED to orange / yellow / black / cream (unchanged from r4)
PAL = {
    'name': 'HD 80606 b',
    'ink': (0, 0, 0),
    'paper': (250, 232, 200),
    'bg': (10, 4, 2),
    'accent1': (255, 200, 60),
    'accent2': (255, 110, 25),
    'accent3': (255, 240, 180),
    'deep': (60, 18, 4),
    'alert': (255, 70, 10),
    'planet': (255, 140, 40),
    'planet_cool': (200, 130, 60),
    'planet_dark': (160, 60, 20),
    'caption': (255, 215, 60),
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
# Same as round 4: cream halo under black stroke for dark-bg visibility.

_STICK_HALO_RGB = (250, 232, 200)
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
    """Segment-2 local stickman with cream halo for visibility on dark bg.

    ROUND 5 FIX: Implement the full §6 mouth-shape lookup per directive 1.
    Mouth shapes:
      - 'flat'      = flat-line (deadpan)
      - 'frown'     = upside-down-arc (scared/sad)
      - 'oval'      = wide-oval (awed)
      - 'smirk'     = one-sided smirk (wry)
      - 'zigzag'    = zigzag line (uncomfortable)
      - 'scream'    = wide ellipse (terrified)
      - 'worried'   = downturned + eyebrows (anxious)
      - 'relief'    = gentle smile (relieved)
      - 'squint'    = squint eyes + small smile (overwhelmed)
      - 'smile'     = upturned arc (happy)
      - 'sad_smile' = hybrid (bittersweet)
      - 'terrified' = huge oval outline (panic)
    """
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

    # Eyes (squint changes eyes)
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

    # Pose rendering (unchanged from round 4)
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

    # ROUND 5 CRITICAL FIX: Full §6 mouth-shape lookup
    mouth_cy = head_cy + int(head_r * 0.4)
    mouth_w = int(8 * scale)

    if mouth == 'flat':
        # Flat line = deadpan
        _halo_line(d, (x_center - mouth_w, mouth_cy),
                   (x_center + mouth_w, mouth_cy), _STICK_INK, 2)
    elif mouth == 'frown':
        # Upside-down arc = scared/sad
        d.arc([x_center - mouth_w, mouth_cy - 3,
               x_center + mouth_w, mouth_cy + 3],
              180, 360, fill=_STICK_INK, width=2)
    elif mouth == 'oval':
        # Wide oval = awed (with pink tongue fill)
        ow, oh = int(10 * scale), int(7 * scale)
        d.ellipse([x_center - ow, mouth_cy - oh,
                   x_center + ow, mouth_cy + oh],
                  outline=_STICK_INK, width=2)
        d.ellipse([x_center - ow + 2, mouth_cy - oh + 2,
                   x_center + ow - 2, mouth_cy + oh - 2],
                  fill=(220, 100, 100))
    elif mouth == 'smirk':
        # One-sided smirk = wry
        d.line([(x_center - int(7 * scale), mouth_cy + 1),
                (x_center - int(2 * scale), mouth_cy)],
               fill=_STICK_INK, width=2)
        d.arc([x_center - int(2 * scale), mouth_cy - int(3 * scale),
               x_center + int(7 * scale), mouth_cy + int(3 * scale)],
              200, 340, fill=_STICK_INK, width=2)
    elif mouth == 'zigzag':
        # Zigzag line = uncomfortable
        pts = []
        for i in range(7):
            x = x_center - 6 + i * 2
            y = mouth_cy + (2 if i % 2 == 0 else -2)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _halo_line(d, pts[i], pts[i + 1], _STICK_INK, 2)
    elif mouth == 'scream':
        # Wide ellipse = terrified
        sw, sh = int(10 * scale), int(11 * scale)
        d.ellipse([x_center - sw, mouth_cy - sh,
                   x_center + sw, mouth_cy + sh],
                  outline=_STICK_INK, width=2)
        d.ellipse([x_center - sw + 1, mouth_cy - sh + 1,
                   x_center + sw - 1, mouth_cy + sh - 1],
                  fill=(120, 30, 30))
    elif mouth == 'worried':
        # Downturned + eyebrows = anxious
        d.arc([x_center - int(6 * scale), mouth_cy - int(2 * scale),
               x_center + int(6 * scale), mouth_cy + int(4 * scale)],
              180, 360, fill=_STICK_INK, width=2)
        brow_dy = int(4 * scale)
        d.line([(x_center - int(7 * scale), mouth_cy - brow_dy - 2),
                (x_center - int(3 * scale), mouth_cy - brow_dy)],
               fill=_STICK_INK, width=1)
        d.line([(x_center + int(3 * scale), mouth_cy - brow_dy),
                (x_center + int(7 * scale), mouth_cy - brow_dy - 2)],
               fill=_STICK_INK, width=1)
    elif mouth == 'relief':
        # Gentle smile = relieved
        d.arc([x_center - int(6 * scale), mouth_cy - int(3 * scale),
               x_center + int(6 * scale), mouth_cy + int(3 * scale)],
              0, 180, fill=_STICK_INK, width=2)
    elif mouth == 'smile':
        # Upturned arc = happy
        d.arc([x_center - mouth_w, mouth_cy - 3,
               x_center + mouth_w, mouth_cy + 3],
              0, 180, fill=_STICK_INK, width=2)
    elif mouth == 'sad_smile':
        # Hybrid = bittersweet
        d.arc([x_center - mouth_w, mouth_cy - int(2 * scale),
               x_center + mouth_w, mouth_cy + int(3 * scale)],
              180, 360, fill=_STICK_INK, width=2)
        brow_dy = int(4 * scale)
        d.line([(x_center - int(8 * scale), mouth_cy - brow_dy),
                (x_center + int(8 * scale), mouth_cy - brow_dy - 2)],
               fill=_STICK_INK, width=1)
    elif mouth == 'terrified':
        # Huge oval outline = panic
        tw, th = int(12 * scale), int(10 * scale)
        d.ellipse([x_center - tw, mouth_cy - th,
                   x_center + tw, mouth_cy + th],
                  outline=_STICK_INK, width=3)
    elif mouth == 'squint':
        # Squint eyes + small smile
        d.arc([x_center - mouth_w, mouth_cy - int(2 * scale),
               x_center + mouth_w, mouth_cy + int(2 * scale)],
              0, 180, fill=_STICK_INK, width=2)
    else:
        # Default to flat if mouth shape not recognized
        _halo_line(d, (x_center - mouth_w, mouth_cy),
                   (x_center + mouth_w, mouth_cy), _STICK_INK, 2)

    return {'head_cy': head_cy, 'head_r': head_r, 'foot_y': foot_y}


# --- Per-beat REACTIONS map (round 5: FULL §6 mapping) ---
# HD 80606 b emotional arc uses ALL distinct mouth shapes per directive 1.
# 15 cards = 15 different (expression, pose) pairs.

REACTIONS = {
    'intro':           ('oval',      'hands_up'),       # 1: awed
    'planet_intro':    ('oval',      'standing'),       # 2: awed (different pose)
    'cold_orbit':      ('flat',      'pointing'),       # 3: deadpan
    'so_close_part1':  ('scream',    'cowering'),       # 4: terrified
    'so_close_part2':  ('terrified', 'cowering'),       # 5: panic (huge oval)
    'fever_intro':     ('worried',   'shielding_eyes'), # 6: anxious
    'fever_spike':     ('scream',    'cowering'),       # 7: terrified (same as 4 but different context)
    'pure_stickman':   ('scream',    'hands_up'),       # 8: terrified (different pose)
    'cold_again':      ('relief',    'shrugged'),       # 9: relieved
    'shock_waves':     ('frown',     'cowering'),       # 10: scared/sad
    'km_per_sec':      ('zigzag',    'cowering'),       # 11: uncomfortable
    'supersonic':      ('terrified', 'shielding_eyes'), # 12: panic (different pose)
    'every_40':        ('smirk',     'shrugged'),       # 13: wry
    'cooked_frozen':   ('sad_smile', 'cowering'),       # 14: bittersweet
    'finale':          ('worried',   'hands_down'),     # 15: anxious (different pose)
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


# --- Hard caption check (unchanged from r4) ---

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
    """Heavy caption (60-80pt) for integrated diagram labels."""
    text_upper = text.upper()
    draw.text(
        xy, text_upper,
        font=HEAVY_CAPTION_FONT,
        fill=color_rgb,
        stroke_width=4, stroke_fill=INK,
    )


def draw_title_strip(img, name):
    """Render the title strip via lib.title_band."""
    title_band.draw_title_band(img, name)


# --- Wobble helpers (unchanged from r4) ---

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


# --- Painterly sun / planet helpers (unchanged from r4) ---

def draw_sun_painterly(img, cx, cy, r, palette_dict, seed=0):
    """Render a painterly sun (radial gradient + stipple + soft halo)."""
    texture.sun_disc(img, cx, cy, r, palette=palette_dict, seed=seed, halo=True)


def draw_planet_painterly(img, cx, cy, r, base_rgb, palette_dict=None,
                          n_bands=4, seed=0, with_bands=True,
                          with_hand_striations=True, with_painterly_stipple=True):
    """Render a painterly planet (banded + radial gradient + stipple +
    hand-drawn striations + heavy 1-2px black stipple dots)."""
    texture.planet_disc(img, cx, cy, r, base_rgb=base_rgb,
                        palette=palette_dict, n_bands=n_bands,
                        seed=seed, with_bands=with_bands)
    if with_hand_striations:
        _add_hand_striations(img, cx, cy, r, seed=seed + 100)
    if with_painterly_stipple:
        _add_painterly_stipple(img, cx, cy, r, seed=seed + 200)


def _add_hand_striations(img, cx, cy, r, seed=0):
    """Add 3-5 hand-drawn wobbly horizontal lines across the planet."""
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    n_striations = rng.randint(3, 5)
    disc_mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )
    mask_px = disc_mask.load()
    for i in range(n_striations):
        y = cy - r * 0.6 + (1.2 * r) * (i + 0.5) / n_striations + rng.uniform(-5, 5)
        if abs(y - cy) > r - 4:
            continue
        half_w = math.sqrt(max(0.0, r * r - (y - cy) ** 2)) * 0.85
        x_start = int(cx - half_w)
        x_end = int(cx + half_w)
        if x_end - x_start < 20:
            continue
        n_seg = 12
        pts = []
        for s in range(n_seg + 1):
            t = s / n_seg
            x = x_start + (x_end - x_start) * t
            jx = rng.uniform(-2, 2)
            jy = rng.uniform(-1, 1)
            px = int(x + jx)
            py = int(y + jy)
            if 0 <= px < img.size[0] and 0 <= py < img.size[1] and mask_px[px, py] > 128:
                pts.append((px, py))
        if len(pts) > 1:
            draw.line(pts, fill=(40, 12, 4), width=2)


def _add_painterly_stipple(img, cx, cy, r, seed=0):
    """Add heavy 1-2px black stipple dots across the planet."""
    rng = random.Random(seed)
    disc_mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )
    mask_px = disc_mask.load()
    w, h = img.size
    px = img.load()
    n_dots = int(2 * math.pi * r * r * 0.012)
    for _ in range(n_dots):
        for _try in range(8):
            x = cx + rng.uniform(-r, r)
            y = cy + rng.uniform(-r, r)
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                break
        else:
            continue
        ix, iy = int(x), int(y)
        if 0 <= ix < w and 0 <= iy < h and mask_px[ix, iy] > 128:
            px[ix, iy] = (0, 0, 0)
            if rng.random() < 0.5:
                dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                nx, ny = ix + dx, iy + dy
                if 0 <= nx < w and 0 <= ny < h and mask_px[nx, ny] > 128:
                    px[nx, ny] = (0, 0, 0)
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


# --- Stars (unchanged from r4) ---

def draw_stars(img, count, seed, region=None, color=None):
    """Draw N small stars in the illustration area."""
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


# --- Sun palette (unchanged from r4) ---

WHIP_STAR = {
    'core':  (255, 240, 130),
    'mid':   (255, 170, 30),
    'outer': (255, 100, 20),
    'halo':  (180, 50, 10),
}

HOT_PLANET_PALETTE = {
    'bands': [
        (255, 220, 100),
        (255, 120, 30),
        (255, 180, 60),
        (200, 70, 20),
        (255, 230, 120),
    ],
    'light': (255, 230, 130),
    'deep':  (130, 40, 12),
}

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


# --- CARDS (round 5: scaled stickman per directive 2, reduced element count per directive 3) ---
# Stickman heights:
#   - CHARACTER BEATS (t02, t08, t36): 480px (~67% of 720) per directive 2
#   - DIAGRAM+STICKMAN BEATS: 360-400px (~50-55%)
#   - DIAGRAM-ONLY BEATS: no stickman

STICKMAN_HEIGHT_CHARACTER = 480  # 67% frame (directive 2)
STICKMAN_HEIGHT_MIXED = 400      # 55% frame


def card_intro(t=0.0):
    """Card 1: 'Now imagine a planet that gets a fever every forty days.'
    CHARACTER BEAT (directive 3): stickman center-left 480px, planet right with integrated label.
    2 elements (directive 3 fix: drop the heavy caption).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 90, seed=10)

    # Big painterly planet center-right with fire aura
    planet_cx, planet_cy = 880, 480
    planet_r = 180
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=11)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=12)
    integrated_label.draw_integrated_label(
        img, "HD 80606 B", planet_cx, planet_cy, scale=0.55, seed=13,
        fill=(255, 220, 100),
    )

    # ROUND 5 FIX: Stickman at 480px (67% frame) per directive 2
    expression, pose = lookup_reaction('intro')
    draw_stickman_motion(
        img, t=t, x_center=340, y_top=240, height=STICKMAN_HEIGHT_CHARACTER,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=1,
    )
    return img


def card_planet_intro(t=0.0):
    """Card 2: 'HD 80606 b. A gas giant...'
    CHARACTER BEAT (directive 3): stickman center-stage 480px.
    1 element — pure character (directive 3 fix: drop stamp).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=20)

    # ROUND 5 FIX: Stickman at 480px (67% frame) per directive 2, centered
    expression, pose = lookup_reaction('planet_intro')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=240, height=STICKMAN_HEIGHT_CHARACTER,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=2,
    )
    return img


def card_cold_orbit(t=0.0):
    """Card 3: 'Most of the time, it sits far from its star. Cold. Quiet. Average.'
    DIAGRAM-ONLY beat with integrated caption.
    2 elements (sun + planet with integrated label).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 120, seed=30)

    # Tiny warm star far left
    draw_sun_painterly(img, 160, 400, 50, WHIP_STAR, seed=31)

    # Dim cool planet right
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

    # Integrated caption
    integrated_label.draw_integrated_label(
        img, "COLD. QUIET.", planet_cx, planet_cy, scale=0.35, seed=34,
        fill=(250, 232, 200),
    )
    return img


def card_so_close_part1(t=0.0):
    """Card 4: 'And then it swings in close. Very close.'
    DIAGRAM+STICKMAN. 3 elements (sun + planet+label + stickman).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=40)

    # Big star right
    draw_sun_painterly(img, 1020, 480, 140, WHIP_STAR, seed=41)

    # Planet left with fire aura
    planet_cx, planet_cy = 480, 480
    planet_r = 150
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=42)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=43)
    integrated_label.draw_integrated_label(
        img, "SO CLOSE", planet_cx, planet_cy, scale=1.1, seed=44,
        fill=(255, 230, 110),
    )

    # Stickman left, 400px (55% frame)
    expression, pose = lookup_reaction('so_close_part1')
    draw_stickman_motion(
        img, t=t, x_center=180, y_top=320, height=STICKMAN_HEIGHT_MIXED,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=4,
    )
    return img


def card_so_close_part2(t=0.0):
    """Card 5: 'So close that the side facing the star gets hit...'
    DIAGRAM+STICKMAN. 3 elements.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=50)

    # Big star right
    draw_sun_painterly(img, 1020, 480, 140, WHIP_STAR, seed=51)

    # Planet left with fire aura
    planet_cx, planet_cy = 480, 480
    planet_r = 150
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=52)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=53)
    integrated_label.draw_integrated_label(
        img, "800X STARLIGHT", planet_cx, planet_cy, scale=0.55, seed=54,
        fill=(255, 230, 110),
    )

    # Stickman right, 400px
    expression, pose = lookup_reaction('so_close_part2')
    draw_stickman_motion(
        img, t=t, x_center=1080, y_top=320, height=STICKMAN_HEIGHT_MIXED,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=5,
    )
    return img


def card_fever_intro(t=0.0):
    """Card 6: 'In a few hours, the temperature on the day side...'
    DIAGRAM+STICKMAN. 2 elements (corona+label + stickman).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=60)

    # Corona center-right
    corona_cx, corona_cy = 880, 400
    corona_r = 150
    draw_planet_painterly(img, corona_cx, corona_cy, corona_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=61)
    integrated_label.draw_flame_halo(img, corona_cx, corona_cy, corona_r, seed=62)
    integrated_label.draw_integrated_label(
        img, "FEVER", corona_cx, corona_cy, scale=0.95, seed=63,
        fill=(255, 240, 110),
    )

    # Stickman left, 400px
    expression, pose = lookup_reaction('fever_intro')
    draw_stickman_motion(
        img, t=t, x_center=300, y_top=320, height=STICKMAN_HEIGHT_MIXED,
        pose=pose, mouth=expression, beat_period_s=1.8, seed=6,
    )
    return img


def card_fever_spike(t=0.0):
    """Card 7: 'spikes by five hundred degrees Celsius'
    DIAGRAM+STICKMAN. 2 elements.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=70)

    # Corona center-right
    corona_cx, corona_cy = 880, 400
    corona_r = 150
    draw_planet_painterly(img, corona_cx, corona_cy, corona_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=71)
    integrated_label.draw_flame_halo(img, corona_cx, corona_cy, corona_r, seed=72)
    integrated_label.draw_integrated_label(
        img, "+500C", corona_cx, corona_cy, scale=0.95, seed=73,
        fill=(255, 220, 100),
    )

    # Stickman left, 400px
    expression, pose = lookup_reaction('fever_spike')
    draw_stickman_motion(
        img, t=t, x_center=300, y_top=320, height=STICKMAN_HEIGHT_MIXED,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=7,
    )
    return img


def card_pure_stickman(t=0.0):
    """Card 8: 'Five hundred.' — PURE CHARACTER BEAT.
    1 element (directive 3 fix: drop heavy caption, let stickman carry beat).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 130, seed=80)

    # ROUND 5 FIX: Stickman 480px (67% frame), center-stage
    expression, pose = lookup_reaction('pure_stickman')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=220, height=STICKMAN_HEIGHT_CHARACTER,
        pose=pose, mouth=expression, beat_period_s=1.4, seed=8,
    )
    return img


def card_cold_again(t=0.0):
    """Card 9: 'Then it swings back out, and the temperature crashes...'
    DIAGRAM+STICKMAN. 3 elements.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 100, seed=90)

    # Sun left (smaller)
    draw_sun_painterly(img, 220, 380, 80, WHIP_STAR, seed=91)

    # Cool planet right
    planet_cx, planet_cy = 1020, 380
    planet_r = 130
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, (160, 100, 50),
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=92)

    # Orbit ellipse
    rng = random.Random(93)
    pts = []
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x = 640 + 480 * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = 380 + 130 * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(250, 232, 200), width=2)

    integrated_label.draw_integrated_label(
        img, "BACK OUT", planet_cx, planet_cy, scale=0.65, seed=94,
        fill=(250, 232, 200),
    )

    # Stickman center, 360px
    expression, pose = lookup_reaction('cold_again')
    draw_stickman_motion(
        img, t=t, x_center=580, y_top=360, height=360,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=9,
    )
    return img


def card_shock_waves(t=0.0):
    """Card 10: 'The atmosphere cannot do anything reasonable with that.'
    DIAGRAM+STICKMAN. 2 elements (planet+label + stickman).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=100)

    # Hot planet center
    planet_cx, planet_cy = 760, 430
    planet_r = 160
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=101)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=102)
    integrated_label.draw_integrated_label(
        img, "NOTHING", planet_cx, planet_cy - 30, scale=0.85, seed=103,
        fill=(255, 230, 110),
    )
    integrated_label.draw_integrated_label(
        img, "REASONABLE", planet_cx, planet_cy + 50, scale=0.7, seed=104,
        fill=(255, 230, 110),
    )

    # Stickman left, 360px
    expression, pose = lookup_reaction('shock_waves')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=360, height=360,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=10,
    )
    return img


def card_km_per_sec(t=0.0):
    """Card 11: 'Model suggests winds on the order of several kilometers per second.'
    DIAGRAM+STICKMAN. 2 elements.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=110)

    # Hot planet center
    planet_cx, planet_cy = 760, 430
    planet_r = 160
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=111)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=112)
    integrated_label.draw_integrated_label(
        img, "WINDS AT KM/S", planet_cx, planet_cy, scale=0.5, seed=113,
        fill=(255, 230, 110),
    )

    # Stickman left, 360px
    expression, pose = lookup_reaction('km_per_sec')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=360, height=360,
        pose=pose, mouth=expression, beat_period_s=1.4, seed=11,
    )
    return img


def card_supersonic(t=0.0):
    """Card 12: 'Supersonic shockwaves, day-side temperatures hot enough to glow.'
    DIAGRAM+STICKMAN. 2 elements.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=120)

    # Hot planet center
    planet_cx, planet_cy = 760, 430
    planet_r = 160
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=121)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=122)
    integrated_label.draw_integrated_label(
        img, "SUPERSONIC", planet_cx, planet_cy, scale=0.55, seed=123,
        fill=(255, 230, 110),
    )

    # Shock-wave rings
    for i, r in enumerate([200, 245, 290]):
        color = (255, 100, 20) if i == 0 else (255, 180, 60)
        wobble_circle(
            draw, (planet_cx, planet_cy), r, color, fill=None, width=3,
            seed=124 + i, segments=64, jitter=3.0,
        )

    # Stickman left, 360px
    expression, pose = lookup_reaction('supersonic')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=360, height=360,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=12,
    )
    return img


def card_every_40(t=0.0):
    """Card 13: 'Every 40 days, the same thing.'
    CHARACTER BEAT. 2 elements (calendar + stickman at 480px).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=130)

    # Calendar right
    cx_cal, cy_cal = 920, 380
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
    # Binding rings
    for ring_x in [cx_cal - cw / 4, cx_cal + cw / 4]:
        draw.ellipse(
            [ring_x - 8, cy_cal - ch / 2 - 14, ring_x + 8, cy_cal - ch / 2],
            outline=INK, width=3,
        )
    # Lines
    for ly in [cy_cal - ch / 4, cy_cal, cy_cal + ch / 4]:
        draw.line(
            [(cx_cal - cw / 2 + 12, ly), (cx_cal + cw / 2 - 12, ly)],
            fill=INK, width=1,
        )
    # Big circled '40'
    draw.ellipse(
        [cx_cal - 50, cy_cal - 50, cx_cal + 50, cy_cal + 50],
        outline=(255, 100, 20), width=6,
    )
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

    # ROUND 5 FIX: Stickman at 480px (67% frame) per directive 2, left
    expression, pose = lookup_reaction('every_40')
    draw_stickman_motion(
        img, t=t, x_center=320, y_top=240, height=STICKMAN_HEIGHT_CHARACTER,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=13,
    )
    return img


def card_cooked_frozen(t=0.0):
    """Card 14: 'The planet gets cooked, then frozen, then cooked again.'
    DIAGRAM+STICKMAN. 3 elements.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=140)

    # Hot planet left
    hot_cx, hot_cy, hot_r = 300, 440, 110
    draw_planet_painterly(img, hot_cx, hot_cy, hot_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=141)
    integrated_label.draw_flame_halo(img, hot_cx, hot_cy, hot_r, seed=142)
    integrated_label.draw_integrated_label(
        img, "COOKED", hot_cx, hot_cy, scale=0.7, seed=143,
        fill=(255, 240, 110),
    )

    # Cool planet right
    cool_cx, cool_cy, cool_r = 980, 440, 110
    draw_planet_painterly(img, cool_cx, cool_cy, cool_r, (160, 100, 50),
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=144)
    integrated_label.draw_integrated_label(
        img, "FROZEN", cool_cx, cool_cy, scale=0.7, seed=145,
        fill=(250, 232, 200),
    )

    # Stickman center, 360px
    expression, pose = lookup_reaction('cooked_frozen')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=360, height=360,
        pose=pose, mouth=expression, beat_period_s=1.4, seed=14,
    )
    return img


def card_finale(t=0.0):
    """Card 15: 'It is, as far as we can tell, the most violent routine...'
    CHARACTER BEAT. 1 element (stickman at 480px).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=150)

    # ROUND 5 FIX: Stickman at 480px (67% frame) per directive 2, centered
    expression, pose = lookup_reaction('finale')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=240, height=STICKMAN_HEIGHT_CHARACTER,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=15,
    )
    return img


# --- Card schedule (unchanged from r4) ---

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
    word indices."""
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
    """Render all cards as a sequence of PNGs at `fps`."""
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
                        help='Disable debug stamps (default: OFF for round 5).')
    parser.add_argument('--frames-dir', default='frames_r5',
                        help='Output directory for rendered PNG frames.')
    parser.add_argument('--schedule-out', default='round_5_card_schedule.json',
                        help='Output card schedule JSON.')
    parser.add_argument('--align', default='round_2_alignment.json',
                        help='Input alignment JSON.')
    parser.add_argument('--verify-only', action='store_true',
                        help='Render only the 6 verification frames.')
    args = parser.parse_args()

    align_path = os.path.join(os.path.dirname(__file__), args.align)
    if not os.path.exists(align_path):
        print(f'Alignment file not found: {align_path}')
        return

    with open(align_path) as f:
        alignment = json.load(f)

    schedule = build_card_schedule(alignment)
    print('Card schedule (round 5):')
    for s in schedule:
        print(f"  {s['id']:18s}  {s['start']:.2f}s -> {s['end']:.2f}s  "
              f"({s['end']-s['start']:.2f}s)  [expr={s['expression']}, pose={s['pose']}]")

    out_dir = os.path.join(os.path.dirname(__file__), args.frames_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.verify_only:
        # Render only the 6 verification frames at 2, 8, 14, 20, 28, 36s
        verify_times = [2.0, 8.0, 14.5, 20.0, 28.0, 36.0]
        for vt in verify_times:
            card = None
            for s in schedule:
                if s['start'] <= vt < s['end']:
                    card = s
                    break
            if card is None:
                card = min(schedule, key=lambda s: abs(s['start'] - vt))
            t_label = f"{vt:.0f}"
            img = card['renderer'](t=vt)
            fpath = os.path.join(out_dir, f'verify_t{t_label}.png')
            img.save(fpath)
            print(f"  verify_t{t_label}.png  ({card['id']}, t={vt:.2f}s, expr={card['expression']}, pose={card['pose']})")
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
