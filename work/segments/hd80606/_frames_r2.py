# work/segments/hd80606/_frames_r2.py
# Round 2 build for segment 2 (HD 80606 b — the whiplash planet).
#
# Round 1 was a ref-loss on:
#   1. STICKMAN SCALE AND FRAMING (biggest gap) — 10% corner-placed vs
#      ref 40-50% subject-of-frame, and missing the pure-stickman beat.
#   2. PAINTERLY RADIAL GRADIENT ON THE SUN AND PLANETS — flat yellow disc
#      vs ref's smooth yellow->orange->red gradient. Ref gas giant has
#      interior structure (multi-color radial gradient).
#   3. MISSING 'SO CLOSE' INTEGRATED HAND-LETTERED LABEL BEAT — ref t5 has
#      the planet engulfed in a red-orange flame halo, with "So Close" in
#      yellow-on-black integrated ON TOP of the planet.
#   4. WRONG HEADER TYPEFACE — ref uses clean sans-serif ALL CAPS in a
#      WHITE band; ours had wobbly yellow text in a black band.
#   5. §7 TWO-LINE CAPTION ON T5 — must be single line per CLAUDE.md §7.
#   6. ALL CAPS CASING VIOLATIONS ON T0, T3 — must be ALL CAPS.
#
# Round 2 fix per gap (1->6):
#   1. Every beat that includes the stickman: scale 40-50% of frame height
#      (height=320..380 px), place central or left-central. Add a
#      pure-stickman beat (sole subject, no diagram) for the "Five Hundred"
#      beat. Use the painterly PAL['bg'] for the bg so the black-limbed
#      stickman reads cleanly (per seg 1 round 2 lesson).
#   2. Use lib.texture.sun_disc() and lib.texture.planet_disc() for every
#      star/planet render. Painterly radial gradient + stipple + halo.
#   3. Add a card_so_close() that draws the planet with a red-orange flame
#      halo (draw_flame_halo) and an integrated "SO CLOSE" label
#      (draw_integrated_label) sitting on the planet's surface.
#   4. Use lib.title_band.draw_title_band() everywhere (white rect 0..60px,
#      Consolas Bold ALL CAPS, BLACK fill, NO STROKE).
#   5. Compress shock_waves caption to "WINDS AT KM/S. SUPERSONIC SHOCK WAVES."
#      (39 chars) and add a hard check in the caption renderer.
#   6. Enforce .upper() pass in the caption renderer (the new draw_caption()
#      wrapper does this and a hard char-count / pixel-width check).

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

# Hard caption constraints (per CLAUDE.md §7 + the round-1 verdict)
MAX_CAPTION_CHARS = 60
CAPTION_FONT = T.load_font(T.CAPTION_PX, bold=False)
DRAW_FONT_BOLD = T.load_font(T.CAPTION_PX, bold=True)


# --- Local stickman halo wrapper (segment 2 only, not in lib/stickman.py) ---
#
# The shared lib/stickman.py uses pure-black 2-3 px strokes on a white
# head. On our dark starfield bg=(1,1,10) the limbs are invisible. To
# keep the round-2 fix local to this segment (and not affect other
# segments that may use lib/stickman on light bgs), we add a CREAM
# HALO underlay pass here: draw a wider cream stroke first, then the
# black stroke on top. This is the comic-book "lit stage" outline.

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


def _haloed_stickman(image, x_center, y_top, height, pose, mouth, seed):
    """Segment-2 local stickman with cream halo for visibility on dark bg."""
    d = ImageDraw.Draw(image)
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
    # Eyes (no halo — they sit on the white head)
    eye_y = head_cy - int(head_r * 0.2)
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
    else:  # 'standing' or default
        arm_dx = int(head_r * 1.2)
        arm_y = neck_y + int((hip_y - neck_y) * 0.3)
        _halo_line(d, (x_center, arm_y),
                   (x_center - arm_dx, arm_y + int(head_r * 0.6)), _STICK_INK, 2)
        _halo_line(d, (x_center, arm_y),
                   (x_center + arm_dx, arm_y + int(head_r * 0.6)), _STICK_INK, 2)
        _halo_disc(d, x_center - arm_dx, arm_y + int(head_r * 0.6), 2)
        _halo_disc(d, x_center + arm_dx, arm_y + int(head_r * 0.6), 2)

    # Legs
    leg_dx = int(head_r * 0.5)
    _halo_line(d, (x_center, hip_y), (x_center - leg_dx, foot_y), _STICK_INK, 2)
    _halo_line(d, (x_center, hip_y), (x_center + leg_dx, foot_y), _STICK_INK, 2)
    _halo_disc(d, x_center - leg_dx, foot_y, 2)
    _halo_disc(d, x_center + leg_dx, foot_y, 2)

    # Mouth
    mouth_cy = head_cy + int(head_r * 0.4)
    if mouth == 'smile':
        w = int(7)
        d.arc([x_center - w, mouth_cy - 3, x_center + w, mouth_cy + 3], 0, 180,
              fill=_STICK_INK, width=2)
    elif mouth == 'frown':
        w = int(7)
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
    return {'head_cy': head_cy, 'head_r': head_r, 'foot_y': foot_y}


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
    # Width check: at 27 px Consolas, even the longest 60-char caption
    # must fit within the illustration area (1280 px wide). A safe ceiling
    # is 1100 px; anything beyond that would clip.
    w = _safe_textwidth(text, CAPTION_FONT)
    if w > 1100:
        raise ValueError(
            f"[{where}] caption is {w}px wide (>1100), would wrap: {text!r}"
        )


def draw_caption(draw, text, xy, color_rgb=None, where='caption'):
    """Caption renderer with the §7 hard check + force .upper().

    Forces ALL CAPS (the round-1 verdict's gap-6 fix) and runs the hard
    char-count / pixel-width check (gap-5 fix).
    """
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


def wobble_circle(draw, center, radius, color, fill=None, width=3, seed=0, segments=24, jitter=1.5):
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
# Schedule is derived from the alignment file. Every card draws the white
# title band on its own (Layout A: white band + dark illustration area).

def card_intro(t=0.0):
    """Card 1: 'Now imagine a planet that gets a fever every forty days.'
    The intro beat: a SINGLE BIG PAINTERLY PLANET center-right, stickman
    center-left at 45% of frame height with hands-up + oval mouth (awed).

    Round 2 fix: stickman is the SUBJECT, not corner decoration.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)

    # Starfield
    draw_stars(img, 90, seed=10)

    # Big painterly planet on the right (warm day side)
    draw_planet_painterly(img, 920, 380, 180, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=11)

    # Round 2 fix: stickman at 360 px (50% of frame) center-left.
    # Hands-up + oval mouth = awed/struck.
    _haloed_stickman(
        img, x_center=320, y_top=320, height=360,
        pose='hands_up', mouth='oval', seed=1,
    )

    # Caption (single line, ALL CAPS, hard-checked)
    draw_caption(draw, "A FEVER EVERY FORTY DAYS",
                 xy=(180, 130), where='intro')

    # Subtitle stamp — "+500C" warning in the upper right
    T.draw_stamp(draw, "+500C", xy=(1020, 110), accent_rgb=PAL['alert'])
    return img


def card_planet_intro(t=0.0):
    """Card 2: 'HD 80606 b. A gas giant about four times the mass of Jupiter,
    on an orbit so stretched out it looks like someone drew it with a ruler
    and then bent the ruler.'
    The 'planet + stretched orbit' diagram, with the stickman pointing at
    the orbit (the audience surrogate noticing the weird orbit).
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=20)

    # Star (sun) on the left
    draw_sun_painterly(img, 220, 380, 90, WHIP_STAR, seed=21)

    # Stretched orbit (very elliptical, looking ruler-bent)
    rng = random.Random(22)
    a, b = 480, 130
    cx, cy = 220, 380
    pts = []
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x = cx + a * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = cy + b * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['accent1'], width=2)

    # Planet at the far end of the orbit
    draw_planet_painterly(img, 700, 380, 32, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=4, seed=23)

    # Stickman pointing at the orbit (left side, big — 380 px = 53% frame)
    _haloed_stickman(
        img, x_center=1080, y_top=320, height=380,
        pose='pointing', mouth='oval', seed=2,
    )

    # A 'ruler' stamp to call out the bent-ruler metaphor
    T.draw_stamp(draw, "BENT RULER ORBIT", xy=(860, 110), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "4 x JUPITER", xy=(620, 460), accent_rgb=PAL['deep'])

    # Caption
    draw_caption(draw, "A GAS GIANT 4 x JUPITER ON A WILD ORBIT",
                 xy=(120, 130), where='planet_intro')
    return img


def card_cold_orbit(t=0.0):
    """Card 3: 'Most of the time, it sits far from its star. Cold. Quiet. Average.'
    The 'cold far-orbit' beat. Small cool blue planet on the right, far from
    a tiny warm star on the left. Stickman center, deadpan, looking at it.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=30)

    # Tiny warm star on the far left
    draw_sun_painterly(img, 130, 380, 50, WHIP_STAR, seed=31)

    # Cool blue planet on the right (far from the star)
    draw_planet_painterly(img, 1000, 380, 110, PAL['planet_cool'],
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=32)

    # Stickman in the center, deadpan, watching — 360 px (50% frame)
    _haloed_stickman(
        img, x_center=560, y_top=320, height=360,
        pose='standing', mouth='flat', seed=3,
    )

    # 'COLD' and 'QUIET' stamps next to the planet
    T.draw_stamp(draw, "COLD", xy=(960, 510), accent_rgb=PAL['planet_cool'])
    T.draw_stamp(draw, "QUIET", xy=(960, 540), accent_rgb=PAL['planet_cool'])

    # Caption
    draw_caption(draw, "MOSTLY FAR. COLD. QUIET. AVERAGE.",
                 xy=(120, 130), where='cold_orbit')
    return img


def card_so_close(t=0.0):
    """Card 4: 'And then it swings in close. Very close. So close that the
    side facing the star gets hit with about eight hundred times more
    starlight than the side facing away.'

    THE CLIMAX BEAT. Planet engulfed in a red-orange flame halo, with
    the integrated hand-lettered 'SO CLOSE' label sitting ON TOP of the
    planet. Stickman right-side, hands-up + oval (scared/awed), 45% frame.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=40)

    # The big star (sun) on the right — close, hot
    draw_sun_painterly(img, 1020, 380, 130, WHIP_STAR, seed=41)

    # The planet on the left, engulfed in flame halo (the climax moment)
    planet_cx, planet_cy = 540, 380
    planet_r = 130
    # Painterly planet base
    draw_planet_painterly(img, planet_cx, planet_cy, planet_r, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=42)
    # Flame halo around the planet (round-2 critic gap-2 fix)
    integrated_label.draw_flame_halo(img, planet_cx, planet_cy, planet_r, seed=43)

    # Integrated hand-lettered 'SO CLOSE' label ON the planet (gap-3 fix)
    integrated_label.draw_integrated_label(
        img, "SO CLOSE", planet_cx, planet_cy, scale=1.1, seed=44,
    )

    # '+500C' warning stamp — upper-right (clear of stickman + caption)
    T.draw_stamp(draw, "+500C", xy=(960, 100), accent_rgb=PAL['alert'])
    T.draw_stamp(draw, "800 x STARLIGHT", xy=(60, 100), accent_rgb=PAL['accent1'])

    # Stickman bottom-LEFT, hands-up + oval (scared/awed), 280 px.
    # y_top=340 + height=280 => feet at y=620, which is ABOVE the caption
    # band at y=640. The stickman is shifted slightly right (x_center=200)
    # so its left leg/foot clear the frame edge and don't overlap the
    # caption text that starts at x=120.
    _haloed_stickman(
        img, x_center=200, y_top=340, height=280,
        pose='hands_up', mouth='oval', seed=4,
    )

    # Caption at the bottom — caption band area (y=640), now clear of both
    # the stickman (feet end at y=620) and the SO CLOSE integrated label
    # (which sits on the planet at y=380).
    draw_caption(draw, "SWINGS IN. VERY CLOSE.",
                 xy=(320, 640), where='so_close')
    return img


def card_fever(t=0.0):
    """Card 5: 'In a few hours, the temperature on the day side spikes by
    five hundred degrees Celsius.'
    The thermometer beat, but rendered as a big number '+500C' on a planet
    on fire, with the stickman observing.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=50)

    # The planet on the right, looking like it's on fire
    draw_planet_painterly(img, 920, 380, 170, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=51)
    integrated_label.draw_flame_halo(img, 920, 380, 170, seed=52)

    # Stickman center-left, hands-up + oval, big (340 px ~ 47% frame)
    _haloed_stickman(
        img, x_center=300, y_top=340, height=340,
        pose='hands_up', mouth='oval', seed=5,
    )

    # Big '+500C' stamp
    T.draw_stamp(draw, "+500 C", xy=(640, 130), accent_rgb=PAL['alert'])

    # Caption
    draw_caption(draw, "FEVER. FIVE HUNDRED DEGREES.",
                 xy=(180, 640), where='fever')
    return img


def card_pure_stickman(t=0.0):
    """Card 6: 'Five hundred.' — PURE STICKMAN BEAT.
    Round 2 fix: this is the SOLE-SUBJECT stickman beat that the round-1
    critic demanded. The beat is just a big shocked stickman against an
    empty starfield. No diagram, no planet. The audience surrogate reacting
    to the absurdity of the number.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)

    # Just stars — no planet, no diagram
    draw_stars(img, 120, seed=60)

    # Big shocked stickman — 420 px (58% of frame) center-stage
    _haloed_stickman(
        img, x_center=640, y_top=260, height=420,
        pose='hands_up', mouth='oval', seed=6,
    )

    # A tiny '500' stamp next to him as the visual anchor of the number
    T.draw_stamp(draw, "500", xy=(1080, 130), accent_rgb=PAL['alert'])

    # Single line caption
    draw_caption(draw, "FIVE. HUNDRED.",
                 xy=(500, 600), where='pure_stickman')
    return img


def card_cold_again(t=0.0):
    """Card 7: 'Then it swings back out, and the temperature crashes just
    as fast.' The 'swing back out' beat — the planet now receding from
    the star, with an arrow showing the trajectory. Stickman left, looking.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=70)

    # Sun on the left (smaller — receded)
    draw_sun_painterly(img, 180, 380, 70, WHIP_STAR, seed=71)

    # Planet on the right, halfway between hot and cool (transitioning)
    # Use a cooler base for the swing-back
    draw_planet_painterly(img, 1000, 380, 130, PAL['planet_cool'],
                          palette_dict=COOL_PLANET_PALETTE, n_bands=5, seed=72)
    # A small red hot patch fading on the day side
    draw = ImageDraw.Draw(img)
    wobble_circle(
        draw, (1000 - 50, 380 - 20), 30, PAL['alert'],
        fill=PAL['alert'], width=2, seed=73, segments=18, jitter=1.5,
    )

    # Arrow showing the trajectory — from left to right (planet receding)
    wobble_line(
        draw, (480, 380), (820, 380), color=PAL['accent1'],
        width=4, seed=74, segments=20, jitter=1.0,
    )
    # Arrowhead
    ang = 0
    head_len = 18
    h1 = (820 - head_len * math.cos(ang - 0.5), 380 - head_len * math.sin(ang - 0.5))
    h2 = (820 - head_len * math.cos(ang + 0.5), 380 - head_len * math.sin(ang + 0.5))
    draw.polygon([(820, 380), h1, h2], fill=PAL['accent1'], outline=INK, width=1)

    # Stickman left, deadpan, watching — 340 px (47% frame)
    _haloed_stickman(
        img, x_center=400, y_top=320, height=340,
        pose='standing', mouth='frown', seed=7,
    )

    # Caption
    draw_caption(draw, "BACK OUT. TEMPERATURE CRASHES.",
                 xy=(120, 600), where='cold_again')
    return img


def card_shock_waves(t=0.0):
    """Card 8: 'The atmosphere cannot do anything reasonable with that.
    Models suggest winds on the order of several kilometers per second,
    supersonic shock waves, day side temperatures hot enough to glow.'
    The shock-wave beat. Big planet center, with concentric shock-wave
    rings and wind arrows. Stickman left, awed, BIG.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 80, seed=80)

    # The big hot planet center-right
    draw_planet_painterly(img, 800, 380, 150, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=5, seed=81)
    integrated_label.draw_flame_halo(img, 800, 380, 150, seed=82)

    # Shock-wave rings (3 concentric wobbly circles)
    for i, r in enumerate([195, 240, 285]):
        color = PAL['alert'] if i == 0 else PAL['accent2']
        wobble_circle(
            draw, (800, 380), r, color, fill=None, width=3,
            seed=83 + i, segments=64, jitter=3.0,
        )

    # Wind arrows (chaotic)
    rng = random.Random(87)
    for i in range(8):
        x0 = 800 + rng.randint(-260, 260)
        y0 = 380 + rng.randint(-220, 220)
        x1 = x0 + rng.randint(-80, 80)
        y1 = y0 + rng.randint(-80, 80)
        wobble_line(
            draw, (x0, y0), (x1, y1),
            color=PAL['accent1'], width=3,
            seed=88 + i, segments=6, jitter=1.0,
        )

    # Stickman left, hands-up + oval (awed at the chaos), 380 px (53% frame)
    _haloed_stickman(
        img, x_center=200, y_top=320, height=380,
        pose='hands_up', mouth='oval', seed=8,
    )

    # Caption (gap-5 fix: SINGLE line, 39 chars)
    draw_caption(draw, "WINDS AT KM/S. SUPERSONIC SHOCK WAVES.",
                 xy=(120, 130), where='shock_waves')
    return img


def card_loop(t=0.0):
    """Card 9: 'Every forty days, the same thing. The planet gets cooked,
    then frozen, then cooked again.'
    The loop beat — a calendar with '40' circled, and a cycle of
    red->cool->red planets. Stickman center, deadpan, BIG.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 70, seed=90)

    # Calendar with circled 40
    cx_cal, cy_cal = 900, 360
    cw, ch = 240, 280
    # Wobbly calendar outline
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
    # Paper background
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

    # Cycle diagram on the left: hot -> cool -> hot planets in a triangle
    cx1, cy1 = 200, 200
    cx2, cy2 = 200, 480
    cx3, cy3 = 440, 340
    # Hot planets
    draw_planet_painterly(img, cx1, cy1, 35, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=4, seed=92)
    # Cool planet
    draw_planet_painterly(img, cx2, cy2, 35, PAL['planet_cool'],
                          palette_dict=COOL_PLANET_PALETTE, n_bands=4, seed=93)
    # Hot planet again
    draw_planet_painterly(img, cx3, cy3, 35, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=4, seed=94)
    # Arrows
    wobble_line(
        draw, (235, 200), (435, 320),
        color=PAL['accent1'], width=3, seed=95, segments=10, jitter=1.0,
    )
    wobble_line(
        draw, (235, 460), (415, 360),
        color=PAL['accent1'], width=3, seed=96, segments=10, jitter=1.0,
    )
    wobble_line(
        draw, (470, 340), (235, 220),
        color=PAL['accent1'], width=3, seed=97, segments=10, jitter=1.0,
    )

    # Stickman center-bottom, deadpan, looking at the cycle, 320 px (44% frame)
    _haloed_stickman(
        img, x_center=640, y_top=380, height=320,
        pose='standing', mouth='frown', seed=9,
    )

    # Caption
    draw_caption(draw, "EVERY 40 DAYS. COOKED. FROZEN. COOKED.",
                 xy=(120, 640), where='loop')
    return img


def card_finale(t=0.0):
    """Card 10: 'It is, as far as we can tell, the most violent routine in
    the galaxy. A fever, on a loop. With no medicine, and no off switch.'
    The finale — stickman center-stage, big and awed, with the planet
    in the distance. The 'closing emotional beat'.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)
    draw_stars(img, 110, seed=100)

    # Small planet in the distance (upper-right)
    draw_planet_painterly(img, 1020, 220, 70, PAL['planet'],
                          palette_dict=HOT_PLANET_PALETTE, n_bands=4, seed=101)

    # Stickman center-stage, awed, 420 px (58% frame)
    _haloed_stickman(
        img, x_center=560, y_top=260, height=420,
        pose='hands_up', mouth='oval', seed=10,
    )

    # Caption at the top — the 'most violent routine' line
    draw_caption(draw, "THE MOST VIOLENT ROUTINE IN THE GALAXY",
                 xy=(120, 130), where='finale_top')

    # Final bottom line
    draw_caption(draw, "A FEVER ON A LOOP. NO MEDICINE. NO OFF SWITCH.",
                 xy=(120, 640), where='finale_bottom')
    return img


def card_outro(t=0.0):
    """Card 11: The closing beat — single stickman in a white oval, neutral
    mouth, against dark starfield. The 'thank you, goodnight' beat.
    """
    img = Image.new('RGB', (W, H), PAL['bg'])
    draw_title_strip(img, 'HD 80606 B')
    draw = ImageDraw.Draw(img)

    # A few quiet stars
    draw_stars(img, 80, seed=110)

    # A soft white oval halo around the stickman (the "spotlight" beat)
    draw = ImageDraw.Draw(img)
    wobble_circle(
        draw, (640, 380), 220, PAL['paper'], fill=PAL['paper'],
        width=2, seed=111, segments=64, jitter=8.0,
    )
    # Soft inner shadow on the oval
    wobble_circle(
        draw, (640, 380), 215, PAL['paper'], fill=None,
        width=1, seed=112, segments=64, jitter=6.0,
    )

    # Stickman in the oval, neutral, 360 px (50% frame)
    _haloed_stickman(
        img, x_center=640, y_top=320, height=360,
        pose='standing', mouth='flat', seed=11,
    )

    # Closing caption
    draw_caption(draw, "A FEVER, ON A LOOP.",
                 xy=(420, 620), where='outro')
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
        schedule.append({
            'id': card['id'],
            'start': start,
            'end': end,
            'renderer': card['renderer'],
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
        img = card['renderer'](t=card['start'])
        for i in range(n_frames):
            fpath = os.path.join(out_dir, f'frame_{total_frames:05d}.png')
            img.save(fpath)
            frame_map.append({'frame': total_frames, 'card': card['id'], 't': card['start'] + i / fps})
            total_frames += 1

    if hold_last_frames > 0:
        last_img = schedule[-1]['renderer'](t=schedule[-1]['end'])
        for i in range(hold_last_frames):
            fpath = os.path.join(out_dir, f'frame_{total_frames:05d}.png')
            last_img.save(fpath)
            frame_map.append({'frame': total_frames, 'card': schedule[-1]['id'], 't': schedule[-1]['end']})
            total_frames += 1

    return total_frames, frame_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-debug', dest='debug', action='store_false',
                        default=False,
                        help='Disable debug stamps (default: ON, debug off).')
    parser.add_argument('--frames-dir', default='frames_r2',
                        help='Output directory for rendered PNG frames.')
    parser.add_argument('--schedule-out', default='round_2_card_schedule.json',
                        help='Output card schedule JSON.')
    parser.add_argument('--align', default='round_1_alignment.json',
                        help='Input alignment JSON (round 1 is reused for round 2).')
    args = parser.parse_args()

    debug_on = args.debug
    if debug_on:
        print("[warning] --debug is ON; round 2 builds should default to --no-debug")
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
        print(f"  {s['id']:18s}  {s['start']:.2f}s -> {s['end']:.2f}s  ({s['end']-s['start']:.2f}s)")

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
            [{'id': s['id'], 'start': s['start'], 'end': s['end']} for s in schedule],
            f, indent=2,
        )
    print(f"Card schedule saved: {sched_path}")


if __name__ == '__main__':
    main()
