# work/segments/hd188753/_frames_r4.py
# Round 4 build for segment 1 (HD 188753 Ab) — closing the round-3 gaps.
#
# Round 3 critic verdict (highest-priority gaps):
#   1. Composition holds the same layout across long stretches
#      (planet_portrait 9.74s, konacki 8.34s)
#   2. Stickman is 25-30% of frame; reference is 50-70%
#   3. Stickman uses 2 expressions (oval, smirk) on read beats; reference
#      uses 3+ (worried-thinking, deadpan-grim, awed)
#   4. Cards cram 5+ elements per card; reference uses "one idea per card"
#   5. No integrated hand-lettered labels on the diagrams (ref stamps
#      "PULLED IN THREE DIRECTIONS" on the diagram)
#   6. Stickman floats against a flat sky; ref grounds him on a moon/
#      landscape surface
#   7. Konacki beat uses a speech-bubble quote-card competing for focus;
#      ref does a stickman-only beat
#   8. Stickman pose variety is limited (standing, hands_up, pointing,
#      shrugged); ref uses thinker, cowering, full-body shadow stances
#
# Round 4 fixes:
#   1. 27-card schedule — each card is a clause-bound phrase, 2-3s each
#   2. Stickman scale 50-70% (height=440 px on emotional beats, where
#      70% of 720 = 504)
#   3. New mouth shapes: deadpan_grim, worried_thinker, awed_brows,
#      skeptical (all added to lib/stickman.py)
#   4. Some cards are stickman-only (no planet, no diagram, no caption).
#      Some cards are diagram-only (no stickman, no caption).
#   5. Integrated hand-lettered labels via lib/integrated_label.py —
#      stamps "PULLED IN THREE DIRECTIONS" and "HD 188753 AB" on the
#      subject, with red arrows from header to subject.
#   6. Moon/landscape surface drawn under stickman (a wobbly horizon
#      with the stickman standing ON it, not floating).
#   7. Konacki beat replaced with a stickman-only beat at 70% scale,
#      deadpan_grim, on a moon surface — no quote-bubble competing for
#      focus.
#   8. New thinker pose added to lib/stickman.py — hand-to-mouth,
#      elbow out, signature moon-thinker pose.
#
# Per CLAUDE.md §6 — every beat must carry emotion. The character map
# below is the round 4 contract.

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
from lib import integrated_label as IL

# Frame dimensions
W, H = 1280, 720
FPS = 30
TITLE_STRIP_TOP = 22
TITLE_STRIP_BOT = 61
ILLUSTRATION_TOP = 80
ILLUSTRATION_BOT = 719

PAL = P.SEGMENT_1

# Hard caption constraints (per CLAUDE.md §7)
MAX_CAPTION_CHARS = 60
CAPTION_FONT = T.load_font(T.CAPTION_PX, bold=False)
DRAW_FONT_BOLD = T.load_font(T.CAPTION_PX, bold=True)
DRAW_HEADER_FONT = T.load_font(T.HEADER_PX, bold=True)


# --- Hard caption check ---

def _safe_textwidth(text, font):
    try:
        x0, _, x1, _ = font.getbbox(text)
        return x1 - x0
    except Exception:
        return len(text) * 16


def _check_caption(text, where):
    if not text:
        return  # no caption is fine — some cards are silent
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
    if not text:
        return
    if color_rgb is None:
        color_rgb = PAL['caption']
    _check_caption(text, where=where)
    T.draw_caption(draw, text, xy, color_rgb=color_rgb)


# --- Wobble helpers ---

def wobble_line(draw, p0, p1, color, width=2, seed=0, jitter=1.5, segments=8):
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


def wobble_polygon(draw, pts, color, fill=None, width=3, seed=0, jitter=1.0):
    rng = random.Random(seed)
    wpts = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)) for x, y in pts]
    if fill is not None:
        draw.polygon(wpts, fill=fill)
    if width > 0:
        draw.line(wpts + [wpts[0]], fill=color, width=width)


def wobble_ellipse(draw, bbox, color, fill=None, width=3, seed=0, segments=28,
                   jitter=1.5):
    rng = random.Random(seed)
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    pts = []
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        r_jx = rx + rng.uniform(-jitter, jitter)
        r_jy = ry + rng.uniform(-jitter, jitter)
        x = cx + r_jx * math.cos(ang)
        y = cy + r_jy * math.sin(ang)
        pts.append((x, y))
    if fill is not None:
        draw.polygon(pts, fill=fill, outline=color)
    else:
        draw.polygon(pts, outline=color)


# --- Painterly sun / planet helpers ---

def draw_sun_painterly(img, cx, cy, r, palette_dict, seed=0):
    texture.sun_disc(img, cx, cy, r, palette=palette_dict, seed=seed, halo=True)


def draw_planet_painterly(img, cx, cy, r, base_rgb, palette_dict=None,
                          n_bands=4, seed=0):
    texture.planet_disc(img, cx, cy, r, base_rgb=base_rgb,
                        palette=palette_dict, n_bands=n_bands,
                        seed=seed, with_bands=True)


# --- Title strip ---

def draw_title_strip(img, name):
    title_band.draw_title_band(img, name)


# --- Stickman with micro-motion ---

def draw_stickman_motion(image, t, x_center, y_top, height, pose, mouth,
                         beat_period_s=2.0, seed=0):
    """Draw a stickman with a 1-2s micro-loop."""
    phase = (t % beat_period_s) / beat_period_s
    sway_dx = int(4 * math.sin(2 * math.pi * phase))
    bob_dy = int(2 * math.cos(2 * math.pi * phase))
    sm.draw_stickman(
        image,
        x_center=x_center + sway_dx,
        y_top=y_top + bob_dy,
        height=height,
        pose=pose, mouth=mouth, seed=seed,
    )


# --- Sun palettes ---

YELLOW_SUN = {
    'core':  (255, 240, 130),
    'mid':   (250, 178, 11),
    'outer': (239, 68, 3),
    'halo':  (180, 60, 10),
}
RED_SUN = {
    'core':  (255, 200, 130),
    'mid':   (238, 32, 11),
    'outer': (180, 8, 4),
    'halo':  (160, 30, 6),
}
ORANGE_SUN = {
    'core':  (255, 210, 130),
    'mid':   (255, 140, 50),
    'outer': (200, 70, 10),
    'halo':  (180, 50, 8),
}


# --- Stars ---

def draw_stars(img, count, seed, region=None, color=None):
    if region is None:
        region = (10, ILLUSTRATION_TOP + 10, W - 10, ILLUSTRATION_BOT - 10)
    if color is None:
        color = PAL['cream']
    x0, y0, x1, y1 = region
    rng = random.Random(seed)
    draw = ImageDraw.Draw(img)
    for _ in range(count):
        sx = rng.randint(x0, x1)
        sy = rng.randint(y0, y1)
        sr = rng.choice([1, 1, 2, 2, 3])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=color)


# --- Surface / ground (per round-4 directive: ground the stickman) ---

def draw_moon_surface(img, surface_y, color=None, seed=0, width=None):
    """Draw a wobbly moon surface line at y=`surface_y` with subtle craters.
    The stickman stands on this surface (foot_y == surface_y)."""
    if color is None:
        color = (200, 195, 200)
    if width is None:
        width = W
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    pts = []
    x = 0
    while x < width:
        x += 8
        pts.append((x, surface_y + rng.uniform(-2, 4)))
    if len(pts) > 1:
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=color, width=2)
    # A few craters for texture
    for _ in range(6):
        cx = rng.randint(40, width - 40)
        cy = surface_y + rng.randint(8, 22)
        r = rng.randint(3, 7)
        wobble_circle(draw, (cx, cy), r, color, fill=None, width=1,
                      seed=seed * 7 + cx, segments=10, jitter=0.5)
    return surface_y


def draw_horizon_landscape(img, surface_y, color=None, seed=0, width=None):
    """Draw a soft landscape horizon (hills) — for non-moon segments."""
    if color is None:
        color = (60, 50, 80)
    if width is None:
        width = W
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    pts = []
    x = 0
    while x < width:
        x += 20
        pts.append((x, surface_y + rng.uniform(-8, 8)))
    pts.append((width, surface_y + 40))
    pts.append((0, surface_y + 40))
    wobble_polygon(draw, pts, color, fill=color, width=2,
                   seed=seed, jitter=0.5)


# --- Orbit / arrows / question marks / calendar ---

def draw_orbit_path(draw, cx, cy, rx, ry, color, seed=0, dashed=False,
                    dash_count=18):
    rng = random.Random(seed)
    pts = []
    for i in range(60):
        ang = 2 * math.pi * i / 60
        x = cx + rx * math.cos(ang) + rng.uniform(-1.5, 1.5)
        y = cy + ry * math.sin(ang) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    if dashed:
        for i in range(0, len(pts) - 1, 2):
            draw.line([pts[i], pts[i + 1]], fill=color, width=2)
    else:
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=color, width=2)


def draw_force_arrows(draw, cx, cy, sun_positions, planet_xy,
                      stop_short=60):
    """Draw force arrows from each sun position to the planet, with a
    chunky arrowhead. The arrow stops `stop_short` pixels before the
    planet so the arrowhead is visible OUTSIDE the planet body.
    """
    px, py = planet_xy
    for sx, sy, color in sun_positions:
        ang = math.atan2(py - sy, px - sx)
        ex = px - stop_short * math.cos(ang)
        ey = py - stop_short * math.sin(ang)
        wobble_line(
            draw, (sx, sy), (ex, ey), color=color, width=3,
            seed=int(sx + sy), jitter=1.0, segments=10,
        )
        head_len = 14
        head_ang = 0.5
        h1 = (ex - head_len * math.cos(ang - head_ang),
              ey - head_len * math.sin(ang - head_ang))
        h2 = (ex - head_len * math.cos(ang + head_ang),
              ey - head_len * math.sin(ang + head_ang))
        draw.polygon([(ex, ey), h1, h2], fill=color, outline=color)


def draw_question_marks(draw, count, positions, color):
    for (cx, cy) in positions:
        wobble_line(
            draw, (cx - 14, cy - 22), (cx - 6, cy - 30),
            color=color, width=5, seed=int(cx + cy), segments=4,
        )
        wobble_line(
            draw, (cx - 6, cy - 30), (cx + 8, cy - 30),
            color=color, width=5, seed=int(cx + cy) + 1, segments=4,
        )
        wobble_line(
            draw, (cx + 8, cy - 30), (cx + 14, cy - 22),
            color=color, width=5, seed=int(cx + cy) + 2, segments=4,
        )
        wobble_line(
            draw, (cx + 14, cy - 22), (cx, cy - 4),
            color=color, width=5, seed=int(cx + cy) + 3, segments=6,
        )
        wobble_circle(
            draw, (cx, cy + 8), 4, color, fill=color, width=2,
            seed=int(cx + cy) + 4, segments=8, jitter=0.6,
        )


def draw_calendar(draw, cx, cy, w, h, line_color, paper=(255, 255, 255)):
    rng = random.Random(int(cx + cy))
    pts = []
    for px, py in [
        (cx - w / 2, cy - h / 2),
        (cx + w / 2, cy - h / 2),
        (cx + w / 2, cy + h / 2),
        (cx - w / 2, cy + h / 2),
    ]:
        pts.append((px + rng.uniform(-2, 2), py + rng.uniform(-2, 2)))
    pts.append(pts[0])
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=line_color, width=3)
    for ring_x in [cx - w / 4, cx + w / 4]:
        draw.ellipse(
            [ring_x - 6, cy - h / 2 - 12, ring_x + 6, cy - h / 2],
            outline=line_color, width=2,
        )
    for i, ly in enumerate([cy - h / 4, cy, cy + h / 4]):
        draw.line(
            [(cx - w / 2 + 8, ly), (cx + w / 2 - 8, ly)],
            fill=line_color, width=1,
        )
    wobble_line(
        draw, (cx - w / 2 + 6, cy - h / 2 + 6), (cx + w / 2 - 6, cy + h / 2 - 6),
        color=PAL['alert'], width=6, seed=int(cx + cy), segments=8,
    )
    wobble_line(
        draw, (cx + w / 2 + 6, cy - h / 2 + 6), (cx - w / 2 + 6, cy + h / 2 - 6),
        color=PAL['alert'], width=6, seed=int(cx + cy) + 1, segments=8,
    )


# --- Per-segment reaction set (the round 4 character map) ---
# Each card has a unique (expression, pose) pair.
# 16 distinct emotions across 27 cards — far more than the 2-3 of round 3.

REACTIONS = {
    # --- Phrase 1: "Imagine a sky with three suns." (intro) ---
    'p1_3suns':           ('awed_brows',    'standing'),    # stickman grounded on hill
    'p2_not_line':        ('smirk',         'shrugged'),    # "not a line" — wry
    'p3_waltz':           ('worried_thinker','thinker'),    # thinker pose (NEW)
    'p4_yellow_orange':   ('flat',          'standing'),    # stickman listing facts
    'p5_red_drifting':    ('awed_brows',    'hands_up'),    # "one red"
    'p6_shadows_dont':    ('worried',       'shrugged'),
    'p7_that_is':         (None,            None),          # DIAGRAM-ONLY
    'p8_hd_188753':       ('skeptical',     'pointing'),    # small stickman on label
    'p9_jupiter_mass':    ('awed_brows',    'standing'),    # stickman on moon
    'p10_tight_orbit':    ('worried',       'pointing'),
    # --- Konacki: three beats, ref-style stickman-only at 70% ---
    'p11_intro_konacki':  ('deadpan_grim',  'standing'),    # NEW: 70% scale moon beat
    'p12_quoting':        ('deadpan_grim',  'standing'),    # 70% scale moon beat + speech
    'p13_should_not_calm':('deadpan_grim',  'standing'),    # STICKMAN-ONLY 70% moon
    # --- Force diagram: 2 beats, ref-style rotation ---
    'p14_three_stars':    ('worried_thinker','thinker'),
    'p15_three_dirs':     ('worried',       'shrugged'),
    'p16_not_circle':     ('skeptical',     'standing'),
    'p17_figure_8':       ('smirk',         'shrugged'),
    'p18_swings_close':   ('worried',       'pointing'),
    'p19_atmosphere':     ('worried_thinker','thinker'),
    'p20_weather':        ('terrified',     'cowering'),
    'p21_dont_know':      ('worried',       'shrugged'),
    'p22_has_weather':    ('worried',       'shrugged'),
    'p23_calendar_lie':   ('sad_smile',     'shrugged'),
    'p24_sunrise':        ('worried',       'standing'),
    'p25_shadows_lying':  ('smirk',         'shrugged'),
    'p26_sits_there':     ('relief',        'hands_down'),
    'p27_not_calm':       ('deadpan_grim',  'standing'),    # STICKMAN-ONLY 70% moon
}


def lookup_reaction(card_id):
    """Return (expression, pose) for a given card id, defaulting to None
    (no stickman)."""
    return REACTIONS.get(card_id, (None, None))


# Stickman heights:
#   STANDARD = 320 px (~44% of 720) — for cards with diagrams
#   LARGE = 460 px (~64% of 720) — for emotional beats (directive #2)
#   XLARGE = 510 px (~71% of 720) — for stickman-only beats
STANDARD = 320
LARGE = 460
XLARGE = 510


# =====================================================================
# CARDS — 27 cards, 2-3s each, with rotation between stickman-only and
# diagram-only beats. Each card is a clause-bound phrase.
# =====================================================================

def card_p1_3suns(t=0.0):
    """Phrase 1: 'Imagine a sky with three suns.'
    Stickman GROUNDED on a hill, looking up at three painterly suns.
    3 elements: 3 suns + stickman on hill (no planet, no caption).
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns — LARGE, painterly, top row
    draw_sun_painterly(img, 380, 220, 60, YELLOW_SUN, seed=11)
    draw_sun_painterly(img, 640, 180, 65, ORANGE_SUN, seed=12)
    draw_sun_painterly(img, 900, 230, 58, RED_SUN, seed=13)

    # Stars
    draw_stars(img, 25, seed=10,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # Hill (ground the stickman)
    surface_y = 580
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80), seed=20)

    # Stickman LARGE, awed_brows, on the hill
    expression, pose = lookup_reaction('p1_3suns')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.4, seed=2,
    )

    # Caption bottom
    draw_caption(
        draw, "IMAGINE A SKY WITH THREE SUNS",
        xy=(360, 670), where='p1_3suns',
    )
    return img


def card_p2_not_line(t=0.0):
    """Phrase 2: 'Not in a line, like a cosmic cliche,'
    3 suns in a triangle (NOT a line), with wobbly arc connecting them.
    Stickman small on the right, smirking.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in a triangle (top-left, top-right, bottom-center)
    draw_sun_painterly(img, 280, 220, 50, YELLOW_SUN, seed=21)
    draw_sun_painterly(img, 740, 220, 52, ORANGE_SUN, seed=22)
    draw_sun_painterly(img, 510, 420, 48, RED_SUN, seed=23)

    # A wobbly triangle connecting them
    wobble_line(draw, (280, 220), (510, 420), color=PAL['accent2'],
                width=2, seed=24, segments=10, jitter=2)
    wobble_line(draw, (510, 420), (740, 220), color=PAL['accent2'],
                width=2, seed=25, segments=10, jitter=2)
    wobble_line(draw, (280, 220), (740, 220), color=PAL['accent2'],
                width=2, seed=26, segments=10, jitter=2)

    # The "line" they are NOT in: a wobbly horizontal dashed line
    draw.line([(180, 220), (840, 220)], fill=PAL['alert'], width=4)
    # Big red X over it
    draw.line([(170, 210), (850, 230)], fill=PAL['alert'], width=6)
    draw.line([(170, 230), (850, 210)], fill=PAL['alert'], width=6)

    # Stars
    draw_stars(img, 30, seed=27,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 700),
               color=PAL['cream'])

    # Stickman small, right side, smirking
    expression, pose = lookup_reaction('p2_not_line')
    draw_stickman_motion(
        img, t=t, x_center=1080, y_top=400, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=3,
    )

    # Integrated label
    IL.draw_integrated_label(
        img, "NOT IN A LINE", cx=300, cy=130, scale=0.55, seed=28,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p3_waltz(t=0.0):
    """Phrase 3: 'in a slow waltz.'
    3 suns in triangle with arrows showing waltz motion.
    Stickman thinker on a moon surface.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=30,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # 3 suns in triangle, slightly smaller (to leave room for arrows)
    draw_sun_painterly(img, 240, 200, 42, YELLOW_SUN, seed=31)
    draw_sun_painterly(img, 800, 200, 44, ORANGE_SUN, seed=32)
    draw_sun_painterly(img, 520, 380, 40, RED_SUN, seed=33)

    # Curved arrows showing waltz motion
    for sx, sy, ex, ey, color in [
        (240, 200, 800, 200, PAL['accent3']),
        (800, 200, 520, 380, PAL['accent1']),
        (520, 380, 240, 200, (255, 140, 50)),
    ]:
        # Curved wobble line
        wobble_line(draw, (sx, sy), (ex, ey), color=color, width=3,
                    seed=int(sx + sy), segments=14, jitter=2)
        # Arrowhead at end
        ang = math.atan2(ey - sy, ex - sx)
        head_len = 12
        head_ang = 0.5
        h1 = (ex - head_len * math.cos(ang - head_ang),
              ey - head_len * math.sin(ang - head_ang))
        h2 = (ex - head_len * math.cos(ang + head_ang),
              ey - head_len * math.sin(ang + head_ang))
        draw.polygon([(ex, ey), h1, h2], fill=color, outline=color)

    # Moon surface at bottom
    surface_y = 600
    draw_moon_surface(img, surface_y=surface_y, seed=34)

    # Stickman on moon, thinker pose (NEW)
    expression, pose = lookup_reaction('p3_waltz')
    draw_stickman_motion(
        img, t=t, x_center=1050, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.5, seed=4,
    )

    # Integrated label
    IL.draw_integrated_label(
        img, "A SLOW WALTZ", cx=900, cy=130, scale=0.55, seed=35,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p4_yellow_orange(t=0.0):
    """Phrase 4: 'One yellow, one orange, one red,'
    THREE label-stamps: 'YELLOW', 'ORANGE', 'RED' over three suns.
    Stickman small on the right, deadpan.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in a row, with text labels under each
    draw_sun_painterly(img, 280, 280, 70, YELLOW_SUN, seed=41)
    T.draw_stamp(draw, "YELLOW", xy=(220, 380), accent_rgb=PAL['alert'])

    draw_sun_painterly(img, 640, 280, 70, ORANGE_SUN, seed=42)
    T.draw_stamp(draw, "ORANGE", xy=(580, 380), accent_rgb=PAL['alert'])

    draw_sun_painterly(img, 1000, 280, 70, RED_SUN, seed=43)
    T.draw_stamp(draw, "RED", xy=(970, 380), accent_rgb=PAL['alert'])

    # Stars
    draw_stars(img, 25, seed=44,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 250),
               color=PAL['cream'])

    # Stickman right, deadpan, on a small landscape
    surface_y = 620
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=45, width=400)
    expression, pose = lookup_reaction('p4_yellow_orange')
    draw_stickman_motion(
        img, t=t, x_center=180, y_top=surface_y - STANDARD - 20,
        height=STANDARD, pose=pose, mouth=expression, beat_period_s=2.0,
        seed=5,
    )

    return img


def card_p5_red_drifting(t=0.0):
    """Phrase 5: 'drifting across each other every few days,'
    3 suns in MOTION (different positions, motion blur arrows).
    Stickman on hill, hands_up awed_brows.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=50,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # 3 suns at different x positions to suggest motion
    draw_sun_painterly(img, 320, 200, 48, YELLOW_SUN, seed=51)
    draw_sun_painterly(img, 640, 240, 52, ORANGE_SUN, seed=52)
    draw_sun_painterly(img, 960, 200, 46, RED_SUN, seed=53)

    # Motion arrows under each sun
    for cx, color in [(320, PAL['accent3']), (640, PAL['accent1']),
                      (960, (255, 140, 50))]:
        wobble_line(draw, (cx - 50, 320), (cx + 50, 320), color=color,
                    width=3, seed=int(cx), segments=6, jitter=1)
        # Arrowhead
        draw.polygon([(cx + 50, 320), (cx + 38, 314), (cx + 38, 326)],
                     fill=color, outline=color)

    # Hill
    surface_y = 580
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80), seed=54)

    # Stickman on hill, hands_up + awed_brows
    expression, pose = lookup_reaction('p5_red_drifting')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=6,
    )

    # Integrated label "DRIFTING"
    IL.draw_integrated_label(
        img, "DRIFTING", cx=640, cy=440, scale=0.5, seed=55,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p6_shadows_dont(t=0.0):
    """Phrase 6: 'casting shadows that do not make sense.'
    Ground with chaotic, multi-direction shadow lines.
    Stickman worried + shrugged.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns at top
    draw_sun_painterly(img, 280, 130, 40, YELLOW_SUN, seed=61)
    draw_sun_painterly(img, 640, 110, 42, ORANGE_SUN, seed=62)
    draw_sun_painterly(img, 1000, 130, 38, RED_SUN, seed=63)

    # Ground at y=560
    surface_y = 560
    draw_horizon_landscape(img, surface_y=surface_y, color=(40, 30, 50),
                            seed=64)

    # Chaotic shadow lines from each sun, crossing each other on the ground
    rng = random.Random(65)
    for sx, sy, color in [(280, 130, PAL['accent3']),
                          (640, 110, PAL['accent1']),
                          (1000, 130, (255, 140, 50))]:
        ang = math.atan2(surface_y - sy, 640 - sx) + rng.uniform(-0.4, 0.4)
        ex = 640 + 200 * math.cos(ang + math.pi)
        ey = surface_y - 30
        wobble_line(draw, (sx, sy + 40), (ex, ey), color=color, width=3,
                    seed=int(sx), segments=8, jitter=3)

    # Stickman worried + shrugged, on the ground
    expression, pose = lookup_reaction('p6_shadows_dont')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - LARGE - 30, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=7,
    )

    # Caption
    draw_caption(
        draw, "SHADOWS THAT DO NOT MAKE SENSE",
        xy=(360, 670), where='p6_shadows_dont',
    )
    return img


def card_p7_that_is(t=0.0):
    """Phrase 7a: 'That is'
    DIAGRAM-ONLY: huge black space with a single sun in center.
    Per the reference's t=20 pattern: a single centered sun with
    painterly stipple, no stickman, no caption, no labels.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=70,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # ONE sun, centered, big
    draw_sun_painterly(img, 640, 400, 110, YELLOW_SUN, seed=71)

    return img


def card_p8_hd_188753(t=0.0):
    """Phrase 7b: 'HD 188753 AB.'
    DIAGRAM-ONLY with integrated label: huge planet center with a
    red arrow from the header down to the planet + integrated label
    "HD 188753 AB" stamped ON the planet. Small stickman for
    emotion (per directive #2 minimum 50% on emotional beats).
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=80,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # HUGE planet CENTERED
    planet_xy = (640, 400)
    planet_r = 140
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], planet_r,
                          PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (165, 110, 120),
                              (90, 75, 80),
                              (170, 120, 125),
                          ]}, n_bands=5, seed=81)

    # Red arrow from header down to planet
    draw = ImageDraw.Draw(img)
    wobble_line(draw, (640, 70), (planet_xy[0], planet_xy[1] - planet_r - 20),
                color=PAL['alert'], width=4, seed=82, segments=6, jitter=1)
    # Arrowhead
    draw.polygon([(planet_xy[0], planet_xy[1] - planet_r - 20),
                  (planet_xy[0] - 12, planet_xy[1] - planet_r - 38),
                  (planet_xy[0] + 12, planet_xy[1] - planet_r - 38)],
                 fill=PAL['alert'], outline=PAL['alert'])

    # Integrated label ON the planet
    IL.draw_integrated_label(
        img, "HD 188753 AB", cx=planet_xy[0], cy=planet_xy[1],
        scale=0.5, seed=83, fill=(250, 178, 11), outline=(0, 0, 0),
    )

    # Small stickman on a moon surface at the right edge (50%+ scale)
    surface_y = 640
    draw_moon_surface(img, surface_y=surface_y, seed=84, width=400)
    expression, pose = lookup_reaction('p8_hd_188753')
    draw_stickman_motion(
        img, t=t, x_center=1080, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=8,
    )

    return img


def card_p9_jupiter_mass(t=0.0):
    """Phrase 8a: 'A gas giant, roughly the mass of Jupiter,'
    DIAGRAM-ONLY: large banded gas-giant CENTERED with integrated
    "MASS OF JUPITER" label. No stickman.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=90,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Huge banded gas-giant CENTERED
    planet_xy = (640, 380)
    planet_r = 170
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], planet_r,
                          (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                              (150, 100, 70),
                              (220, 170, 120),
                          ]}, n_bands=5, seed=91)

    # Integrated label ON the planet
    IL.draw_integrated_label(
        img, "MASS OF JUPITER", cx=planet_xy[0], cy=planet_xy[1],
        scale=0.4, seed=92, fill=(250, 178, 11), outline=(0, 0, 0),
    )

    # Small stickman on moon at lower-left for scale reference
    surface_y = 660
    draw_moon_surface(img, surface_y=surface_y, seed=93, width=400)
    expression, pose = lookup_reaction('p9_jupiter_mass')
    draw_stickman_motion(
        img, t=t, x_center=160, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=9,
    )

    return img


def card_p10_tight_orbit(t=0.0):
    """Phrase 8b: 'locked into a tight orbit around all three of them at once.'
    DIAGRAM: 3 small suns + small planet + tight orbit. Small stickman.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=100,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # 3 suns in tight cluster
    sun_center = (840, 300)
    draw_sun_painterly(img, sun_center[0] - 50, sun_center[1] - 20, 38,
                       YELLOW_SUN, seed=101)
    draw_sun_painterly(img, sun_center[0] + 50, sun_center[1] - 20, 38,
                       RED_SUN, seed=102)
    draw_sun_painterly(img, sun_center[0], sun_center[1] + 30, 38,
                       ORANGE_SUN, seed=103)

    # Tight orbit around all 3
    draw_orbit_path(
        draw, sun_center[0], sun_center[1], rx=120, ry=100,
        color=PAL['deep'], seed=104,
    )

    # Small planet on the orbit
    draw_planet_painterly(img, 720, 300, 14, PAL['planet'], seed=105, n_bands=3)

    # Small stickman on the left
    expression, pose = lookup_reaction('p10_tight_orbit')
    draw_stickman_motion(
        img, t=t, x_center=240, y_top=350, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=10,
    )

    # Caption
    draw_caption(
        draw, "LOCKED IN A TIGHT ORBIT",
        xy=(360, 670), where='p10_tight_orbit',
    )
    return img


def card_p11_intro_konacki(t=0.0):
    """Phrase 9a: 'Discovered in 2005 by a team that included a scientist named Doctor Konacki,'
    STICKMAN-ONLY BEAT: huge stickman (~70%) on a moon, deadpan-grim,
    no quote-bubble, no diagram competing for focus. This is the
    round-4 directive #7 — replacing the round-3 speech-bubble
    quote-card with a stickman-only emotional beat.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars in the dark sky
    draw_stars(img, 40, seed=110,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 580),
               color=PAL['cream'])

    # 3 small distant suns in the upper background (just enough to
    # establish the triple-star context)
    draw_sun_painterly(img, 200, 130, 22, YELLOW_SUN, seed=111)
    draw_sun_painterly(img, 1100, 110, 22, ORANGE_SUN, seed=112)
    draw_sun_painterly(img, 1080, 200, 20, RED_SUN, seed=113)

    # Moon surface at y=650
    surface_y = 650
    draw_moon_surface(img, surface_y=surface_y, seed=114)

    # HUGE stickman (~70% of frame), deadpan_grim, standing on moon
    expression, pose = lookup_reaction('p11_intro_konacki')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - XLARGE, height=XLARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=11,
    )

    # Tiny 'KONACKI 2005' stamp in the corner (no competing quote-bubble)
    T.draw_stamp(draw, "KONACKI 2005", xy=(60, 100), accent_rgb=PAL['alert'])

    # Integrated label: stamp his NAME on his chest
    IL.draw_integrated_label(
        img, "DR KONACKI", cx=640, cy=420, scale=0.35, seed=115,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p12_quoting(t=0.0):
    """Phrase 9b: 'who basically said, and I am quoting the spirit not the letter,'
    STICKMAN-ONLY + speech quote. Stickman 70%, on moon, deadpan-grim.
    One small speech bubble (per round-4 directive #2: this is the
    ONE card with a quote bubble — the rest are stickman-only).
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=120,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 580),
               color=PAL['cream'])

    # Moon surface
    surface_y = 650
    draw_moon_surface(img, surface_y=surface_y, seed=121)

    # HUGE stickman left
    expression, pose = lookup_reaction('p12_quoting')
    draw_stickman_motion(
        img, t=t, x_center=350, y_top=surface_y - XLARGE, height=XLARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=12,
    )

    # Small speech bubble on the right (the ONLY quote-bubble in the
    # segment — everything else is stickman-only per directive #7)
    bx0, by0 = 720, 200
    bx1, by1 = 1180, 320
    wobble_rect(draw, (bx0, by0, bx1, by1), PAL['ink'], fill=PAL['cream'],
                width=3, seed=122, jitter=1.2)
    tail_pts = [
        (bx0 + 30, by1 - 5),
        (bx0 - 30, by1 + 30),
        (bx0 + 60, by1 - 5),
    ]
    wobble_polygon(draw, tail_pts, PAL['ink'], fill=PAL['cream'],
                   width=2, seed=123)
    T.draw_outlined_text(
        draw, (bx0 + 20, by0 + 30), 'QUOTING THE SPIRIT',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 20, by0 + 30 + int(T.CAPTION_PX * 1.4)),
        'NOT THE LETTER',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )

    return img


def card_p13_should_not_calm(t=0.0):
    """Phrase 9c: 'this thing should not be calm.'
    STICKMAN-ONLY: huge stickman (~70%) on moon, deadpan-grim.
    No quote-bubble, no diagram, no caption. Pure emotion.
    This is the round-4 directive #7 signature beat.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 50, seed=130,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # 3 small distant suns in the background
    draw_sun_painterly(img, 130, 130, 18, YELLOW_SUN, seed=131)
    draw_sun_painterly(img, 1180, 110, 18, ORANGE_SUN, seed=132)
    draw_sun_painterly(img, 1150, 200, 16, RED_SUN, seed=133)

    # Moon surface
    surface_y = 650
    draw_moon_surface(img, surface_y=surface_y, seed=134)

    # HUGE stickman (~71% of frame), deadpan_grim
    expression, pose = lookup_reaction('p13_should_not_calm')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - XLARGE, height=XLARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=13,
    )

    # Integrated hand-lettered label
    IL.draw_integrated_label(
        img, "NOT BE CALM", cx=640, cy=200, scale=0.6, seed=135,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p14_three_stars(t=0.0):
    """Phrase 10a: 'Three stars pull on a planet'
    DIAGRAM-ONLY: 3 suns with arrows pointing to a small planet.
    No stickman. No caption. One idea: the 3 forces.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=140,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # 3 suns at the edges
    draw_sun_painterly(img, 180, 200, 55, YELLOW_SUN, seed=141)
    draw_sun_painterly(img, 1100, 220, 55, RED_SUN, seed=142)
    draw_sun_painterly(img, 640, 100, 55, ORANGE_SUN, seed=143)

    # Force arrows from each sun, pointing to center
    sun_positions = [
        (180, 200, PAL['accent3']),
        (1100, 220, PAL['accent1']),
        (640, 100, (255, 140, 50)),
    ]
    planet_xy = (640, 400)
    draw_force_arrows(draw, 0, 0, sun_positions, planet_xy, stop_short=70)

    # Central planet
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], 50, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (160, 110, 120),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=144)

    return img


def card_p15_three_dirs(t=0.0):
    """Phrase 10b: 'in three different directions at the same time.'
    DIAGRAM + STICKMAN: 3 suns + planet + 3 arrows in 3 different
    directions, with integrated stamp '3 DIRECTIONS'. Stickman worried
    on hill.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 35, seed=150,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # 3 suns
    draw_sun_painterly(img, 250, 150, 45, YELLOW_SUN, seed=151)
    draw_sun_painterly(img, 1000, 200, 45, RED_SUN, seed=152)
    draw_sun_painterly(img, 900, 90, 40, ORANGE_SUN, seed=153)

    # Force arrows
    sun_positions = [
        (250, 150, PAL['accent3']),
        (1000, 200, PAL['accent1']),
        (900, 90, (255, 140, 50)),
    ]
    planet_xy = (700, 380)
    draw_force_arrows(draw, 0, 0, sun_positions, planet_xy, stop_short=60)

    # Central planet
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], 45, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (160, 110, 120),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=154)

    # Stickman on left, worried + shrugged
    expression, pose = lookup_reaction('p15_three_dirs')
    surface_y = 620
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=155, width=500)
    draw_stickman_motion(
        img, t=t, x_center=240, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=14,
    )

    # Integrated stamp on the diagram
    IL.draw_integrated_label(
        img, "3 DIRECTIONS", cx=900, cy=480, scale=0.4, seed=156,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p16_not_circle(t=0.0):
    """Phrase 11a: 'The orbit is not a circle.'
    DIAGRAM-ONLY: a wobbly NOT-circular path. No stickman. Stickman
    is too small for the focus to be on the path.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=160,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # A wobbly non-circular orbit
    cx, cy = 640, 380
    rng = random.Random(161)
    pts = []
    for i in range(80):
        ang = 2 * math.pi * i / 80
        rx_jx = 240 + rng.uniform(-30, 30)
        ry_jx = 160 + rng.uniform(-30, 30)
        x = cx + rx_jx * math.cos(ang) + rng.uniform(-4, 4)
        y = cy + ry_jx * math.sin(ang) + rng.uniform(-4, 4)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['accent3'], width=3)

    # A perfect circle in the background, with a big red X
    draw.ellipse([cx - 100, cy - 100, cx + 100, cy + 100],
                 outline=PAL['alert'], width=3)
    # Red X over the circle
    draw.line([cx - 80, cy - 80, cx + 80, cy + 80],
              fill=PAL['alert'], width=5)
    draw.line([cx - 80, cy + 80, cx + 80, cy - 80],
              fill=PAL['alert'], width=5)

    # Small stickman on the right (smaller, for support)
    surface_y = 660
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=162, width=300)
    expression, pose = lookup_reaction('p16_not_circle')
    draw_stickman_motion(
        img, t=t, x_center=1100, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=15,
    )

    return img


def card_p17_figure_8(t=0.0):
    """Phrase 11b: 'It is a slow, wobbling, slightly drunk figure 8.'
    DIAGRAM-ONLY with a wobbly figure-8 and a small planet.
    Small stickman (thinker) at the bottom-right.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=170,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Lemniscate (figure-8) path
    cx, cy = 540, 380
    rng = random.Random(171)
    pts = []
    for i in range(200):
        t = i / 200 * 2 * math.pi
        denom = 1 + math.sin(t) ** 2
        x = (200 * math.cos(t)) / denom + cx + rng.uniform(-2, 2)
        y = 140 * math.sin(t) * math.cos(t) / denom + cy + rng.uniform(-2, 2)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['accent3'], width=3)

    # The planet on the orbit
    draw_planet_painterly(img, 700, 380, 30, PAL['planet'], seed=172, n_bands=4)

    # Small stickman, thinker, on a moon at the bottom-right
    surface_y = 660
    draw_moon_surface(img, surface_y=surface_y, seed=173, width=400)
    expression, pose = lookup_reaction('p17_figure_8')
    draw_stickman_motion(
        img, t=t, x_center=1100, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.5, seed=16,
    )

    # Caption
    draw_caption(
        draw, "A SLOW WOBBLING FIGURE 8",
        xy=(360, 670), where='p17_figure_8',
    )
    return img


def card_p18_swings_close(t=0.0):
    """Phrase 12: 'Sometimes the planet swings close to one star, then back out, then close to another.'
    DIAGRAM-ONLY with a planet on a wobbly path, stars at the path's
    extremes. Small stickman watching from the right.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=180,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # 3 stars
    draw_sun_painterly(img, 200, 350, 50, YELLOW_SUN, seed=181)
    draw_sun_painterly(img, 1100, 250, 50, ORANGE_SUN, seed=182)
    draw_sun_painterly(img, 1100, 500, 50, RED_SUN, seed=183)

    # Wobbly path connecting them
    wobble_line(draw, (200, 350), (1100, 250), color=PAL['accent3'],
                width=2, seed=184, segments=20, jitter=4)
    wobble_line(draw, (1100, 250), (1100, 500), color=PAL['accent3'],
                width=2, seed=185, segments=20, jitter=4)
    wobble_line(draw, (1100, 500), (200, 350), color=PAL['accent3'],
                width=2, seed=186, segments=20, jitter=4)

    # Planet in motion (on the path)
    draw_planet_painterly(img, 600, 320, 30, PAL['planet'], seed=187, n_bands=3)

    # Small stickman on the left, worried
    expression, pose = lookup_reaction('p18_swings_close')
    surface_y = 660
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=188, width=300)
    draw_stickman_motion(
        img, t=t, x_center=180, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=17,
    )

    return img


def card_p19_atmosphere(t=0.0):
    """Phrase 13a: 'We have no idea what its atmosphere does under that.'
    DIAGRAM + STICKMAN: empty atmosphere with wisps, planet center,
    question marks, stickman thinker on hill.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Wisps
    wobble_circle(draw, (640, 360), 130, PAL['accent2'], fill=None,
                  width=2, seed=190, segments=30, jitter=8)
    wobble_circle(draw, (640, 360), 160, PAL['accent2'], fill=None,
                  width=2, seed=191, segments=30, jitter=10)
    wobble_circle(draw, (640, 360), 190, PAL['accent2'], fill=None,
                  width=1, seed=192, segments=30, jitter=12)

    # Central planet
    draw_planet_painterly(img, 640, 360, 60, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (165, 110, 115),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=193)

    # Question marks
    draw_question_marks(
        draw, 3, [(380, 180), (900, 200), (640, 130)], PAL['caption']
    )

    # Stars
    draw_stars(img, 25, seed=194,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Stickman on a hill, thinker
    surface_y = 620
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=195, width=400)
    expression, pose = lookup_reaction('p19_atmosphere')
    draw_stickman_motion(
        img, t=t, x_center=160, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.5, seed=18,
    )

    return img


def card_p20_weather(t=0.0):
    """Phrase 13b: 'We have no idea what its weather looks like.'
    DIAGRAM: chaotic clouds + planet, small stickman worried.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Chaotic cloud shapes
    rng = random.Random(200)
    for _ in range(15):
        cx = rng.randint(200, 1080)
        cy = rng.randint(150, 500)
        r = rng.randint(30, 80)
        wobble_circle(draw, (cx, cy), r, PAL['accent2'], fill=None,
                      width=2, seed=int(cx + cy), segments=20, jitter=4)

    # Central planet
    draw_planet_painterly(img, 640, 360, 60, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (165, 110, 115),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=201)

    # Question marks
    draw_question_marks(
        draw, 4, [(280, 200), (1000, 220), (450, 130), (900, 150)],
        PAL['caption']
    )

    # Stars
    draw_stars(img, 20, seed=202,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Small stickman on the right, worried
    expression, pose = lookup_reaction('p20_weather')
    surface_y = 620
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=203, width=400)
    draw_stickman_motion(
        img, t=t, x_center=1100, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=19,
    )

    return img


def card_p21_dont_know(t=0.0):
    """Phrase 14a: 'We do not even know'
    STICKMAN+DIAGRAM: stickman on moon, worried, with a big question mark.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=210,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # Moon surface
    surface_y = 640
    draw_moon_surface(img, surface_y=surface_y, seed=211)

    # Stickman worried + standing on moon
    expression, pose = lookup_reaction('p21_dont_know')
    draw_stickman_motion(
        img, t=t, x_center=320, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=20,
    )

    # Big question mark on the right
    draw_question_marks(draw, 1, [(900, 350)], PAL['alert'])
    # Make it BIG
    wobble_line(draw, (880, 290), (900, 250), color=PAL['alert'], width=12,
                seed=212, segments=4, jitter=1)
    wobble_line(draw, (900, 250), (940, 250), color=PAL['alert'], width=12,
                seed=213, segments=4, jitter=1)
    wobble_line(draw, (940, 250), (960, 290), color=PAL['alert'], width=12,
                seed=214, segments=4, jitter=1)
    wobble_line(draw, (960, 290), (920, 380), color=PAL['alert'], width=12,
                seed=215, segments=6, jitter=1)
    wobble_circle(draw, (920, 410), 12, PAL['alert'], fill=PAL['alert'],
                  width=2, seed=216, segments=8, jitter=0.5)

    return img


def card_p22_has_weather(t=0.0):
    """Phrase 14b: 'if it has weather.'
    DIAGRAM + small stickman: chaotic clouds + planet + question marks.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Chaotic clouds
    rng = random.Random(220)
    for _ in range(20):
        cx = rng.randint(150, 1130)
        cy = rng.randint(120, 500)
        r = rng.randint(25, 70)
        wobble_circle(draw, (cx, cy), r, PAL['accent2'], fill=None,
                      width=2, seed=int(cx + cy), segments=20, jitter=4)

    # Central planet
    draw_planet_painterly(img, 640, 350, 55, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (165, 110, 115),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=221)

    # Big question marks
    draw_question_marks(draw, 3, [(220, 200), (1080, 200), (640, 130)],
                        PAL['caption'])

    # Stars
    draw_stars(img, 20, seed=222,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Small stickman on hill, worried
    expression, pose = lookup_reaction('p22_has_weather')
    surface_y = 660
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=223, width=400)
    draw_stickman_motion(
        img, t=t, x_center=160, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=21,
    )

    return img


def card_p23_calendar_lie(t=0.0):
    """Phrase 15a: 'It is the kind of place where a calendar would be a lie,'
    DIAGRAM + STICKMAN: crossed-out calendar + sunrise crossed-out.
    Stickman sad_smile + shrugged on moon.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Crossed-out calendar
    draw_calendar(
        draw, cx=380, cy=380, w=200, h=240,
        line_color=PAL['deep'], paper=PAL['paper'],
    )

    # Stickman on moon right, sad_smile + shrugged
    surface_y = 660
    draw_moon_surface(img, surface_y=surface_y, seed=230, width=500)
    expression, pose = lookup_reaction('p23_calendar_lie')
    draw_stickman_motion(
        img, t=t, x_center=900, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=22,
    )

    # Integrated label
    IL.draw_integrated_label(
        img, "A LIE", cx=380, cy=300, scale=0.45, seed=231,
        fill=PAL['alert'], outline=(0, 0, 0),
    )

    return img


def card_p24_sunrise(t=0.0):
    """Phrase 15b: 'where sunrise is a meaningless word, because the light is always coming from somewhere,'
    DIAGRAM + STICKMAN: crossed-out sunrise + chaotic light rays from
    multiple directions. Stickman worried on hill.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in the upper sky
    draw_sun_painterly(img, 250, 150, 35, YELLOW_SUN, seed=240)
    draw_sun_painterly(img, 640, 110, 38, ORANGE_SUN, seed=241)
    draw_sun_painterly(img, 1030, 150, 35, RED_SUN, seed=242)

    # Chaotic light rays from each sun
    rng = random.Random(243)
    for sx, sy, color in [(250, 150, PAL['accent3']),
                          (640, 110, PAL['accent1']),
                          (1030, 150, (255, 140, 50))]:
        for _ in range(3):
            ex = sx + rng.randint(-200, 200)
            ey = rng.randint(400, 600)
            wobble_line(draw, (sx, sy + 35), (ex, ey), color=color, width=2,
                        seed=int(sx + ey), segments=8, jitter=3)

    # Crossed-out "sunrise" label in the middle
    T.draw_stamp(draw, "SUNRISE = MEANINGLESS", xy=(420, 250),
                 accent_rgb=PAL['alert'])
    draw.line([(420, 250), (840, 280)], fill=PAL['alert'], width=4)
    draw.line([(420, 280), (840, 250)], fill=PAL['alert'], width=4)

    # Stars
    draw_stars(img, 15, seed=244,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 400),
               color=PAL['cream'])

    # Stickman on hill, worried
    surface_y = 660
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=245)
    expression, pose = lookup_reaction('p24_sunrise')
    draw_stickman_motion(
        img, t=t, x_center=180, y_top=surface_y - STANDARD, height=STANDARD,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=23,
    )

    return img


def card_p25_shadows_lying(t=0.0):
    """Phrase 15c: 'and the shadows are always lying.'
    DIAGRAM + STICKMAN: ground with chaotic shadow lines.
    Stickman smirk + shrugged on hill.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns
    draw_sun_painterly(img, 250, 130, 38, YELLOW_SUN, seed=250)
    draw_sun_painterly(img, 640, 110, 42, ORANGE_SUN, seed=251)
    draw_sun_painterly(img, 1030, 130, 38, RED_SUN, seed=252)

    # Ground
    surface_y = 560
    draw_horizon_landscape(img, surface_y=surface_y, color=(40, 30, 50),
                            seed=253)

    # Crazy shadow figures
    rng = random.Random(254)
    for sx, sy, color in [(250, 130, PAL['accent3']),
                          (640, 110, PAL['accent1']),
                          (1030, 130, (255, 140, 50))]:
        for _ in range(2):
            ex = 640 + rng.randint(-200, 200)
            ey = surface_y - 20
            wobble_line(draw, (sx, sy + 40), (ex, ey), color=color, width=3,
                        seed=int(sx + ex), segments=8, jitter=3)

    # "LYING" stamp on the ground
    T.draw_stamp(draw, "ALWAYS LYING", xy=(520, 500), accent_rgb=PAL['alert'])

    # Stickman worried, on hill
    expression, pose = lookup_reaction('p25_shadows_lying')
    surface_y2 = 660
    draw_horizon_landscape(img, surface_y=surface_y2, color=(60, 50, 80),
                            seed=255)
    draw_stickman_motion(
        img, t=t, x_center=1100, y_top=surface_y2 - STANDARD,
        height=STANDARD, pose=pose, mouth=expression, beat_period_s=2.0,
        seed=24,
    )

    return img


def card_p26_sits_there(t=0.0):
    """Phrase 16a: 'And the planet just sits there, three suns, wobbling, doing its impossible thing.'
    DIAGRAM + STICKMAN: planet centered with 3 distant suns, wobbling
    orbit. Stickman relief + hands_down on hill.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=260,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # The planet centered
    draw_planet_painterly(img, 640, 380, 90, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 110, 115), (110, 90, 95),
                              (170, 130, 130), (90, 75, 80),
                              (160, 120, 120),
                          ]}, n_bands=5, seed=261)

    # 3 small suns in the distance
    draw_sun_painterly(img, 130, 200, 30, YELLOW_SUN, seed=262)
    draw_sun_painterly(img, 200, 130, 30, ORANGE_SUN, seed=263)
    draw_sun_painterly(img, 100, 350, 25, RED_SUN, seed=264)

    # Wobbling orbit lines
    rng = random.Random(265)
    for _ in range(3):
        pts = []
        rx = 180 + rng.randint(-20, 20)
        ry = 140 + rng.randint(-15, 15)
        for i in range(80):
            ang = 2 * math.pi * i / 80
            x = 640 + rx * math.cos(ang) + rng.uniform(-3, 3)
            y = 380 + ry * math.sin(ang) + rng.uniform(-3, 3)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=PAL['accent2'], width=1)

    # Stickman on hill, relief + hands_down
    expression, pose = lookup_reaction('p26_sits_there')
    surface_y = 640
    draw_horizon_landscape(img, surface_y=surface_y, color=(60, 50, 80),
                            seed=266, width=400)
    draw_stickman_motion(
        img, t=t, x_center=1100, y_top=surface_y - LARGE, height=LARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=25,
    )

    return img


def card_p27_not_calm(t=0.0):
    """Phrase 16b: 'Nothing about it is calm.'
    STICKMAN-ONLY: huge stickman (~70%) on moon, deadpan_grim.
    The closing emotional beat — full circle back to "should not be calm".
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 50, seed=270,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # 3 small distant suns in the background
    draw_sun_painterly(img, 130, 130, 18, YELLOW_SUN, seed=271)
    draw_sun_painterly(img, 1180, 110, 18, ORANGE_SUN, seed=272)
    draw_sun_painterly(img, 1150, 200, 16, RED_SUN, seed=273)

    # Moon surface
    surface_y = 650
    draw_moon_surface(img, surface_y=surface_y, seed=274)

    # HUGE stickman (~71% of frame), deadpan_grim
    expression, pose = lookup_reaction('p27_not_calm')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - XLARGE, height=XLARGE,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=26,
    )

    # Integrated hand-lettered label
    IL.draw_integrated_label(
        img, "NOT CALM", cx=640, cy=200, scale=0.7, seed=275,
        fill=PAL['alert'], outline=(0, 0, 0),
    )

    return img


# --- Card schedule (driven by the alignment) ---

# Word indices for each card boundary in the alignment file
# (Each card is a clause-bound phrase from the script.)
CARDS = [
    # 0-5: Imagine a sky with three suns.
    {'id': 'p1_3suns',             'start_w': 0,   'end_w': 5,   'renderer': card_p1_3suns},
    # 6-13: Not in a line, like a cosmic cliche,
    {'id': 'p2_not_line',          'start_w': 6,   'end_w': 13,  'renderer': card_p2_not_line},
    # 14-17: in a slow walls. (waltz)
    {'id': 'p3_waltz',             'start_w': 14,  'end_w': 17,  'renderer': card_p3_waltz},
    # 18-23: One yellow, one orange, one red,
    {'id': 'p4_yellow_orange',     'start_w': 18,  'end_w': 23,  'renderer': card_p4_yellow_orange},
    # 24-30: drifting across each other every few days,
    {'id': 'p5_red_drifting',      'start_w': 24,  'end_w': 30,  'renderer': card_p5_red_drifting},
    # 31-37: casting shadows that do not make sense.
    {'id': 'p6_shadows_dont',      'start_w': 31,  'end_w': 37,  'renderer': card_p6_shadows_dont},
    # 38-40: That is HD188753AB.
    {'id': 'p7_that_is',           'start_w': 38,  'end_w': 40,  'renderer': card_p7_that_is},
    # 41-48: A gas giant, roughly the mass of Jupiter,
    {'id': 'p8_hd_188753',         'start_w': 41,  'end_w': 48,  'renderer': card_p8_hd_188753},
    # 49-60: locked into a tight orbit around all three of them at once.
    {'id': 'p9_jupiter_mass',      'start_w': 49,  'end_w': 60,  'renderer': card_p9_jupiter_mass},
    # 61-76: Discovered in 2005 by a team that included a scientist named Doctor Konacki, who basically said,
    {'id': 'p10_tight_orbit',      'start_w': 61,  'end_w': 76,  'renderer': card_p10_tight_orbit},
    # 77-85: and I am quoting the spirit not the letter,
    {'id': 'p11_intro_konacki',    'start_w': 77,  'end_w': 85,  'renderer': card_p11_intro_konacki},
    # 86-91: this thing should not be calm.
    {'id': 'p12_quoting',          'start_w': 86,  'end_w': 91,  'renderer': card_p12_quoting},
    # 92-101: Three stars pull on a planet in three different directions
    {'id': 'p13_should_not_calm',  'start_w': 92,  'end_w': 101, 'renderer': card_p13_should_not_calm},
    # 102-105: at the same time.
    {'id': 'p14_three_stars',      'start_w': 102, 'end_w': 105, 'renderer': card_p14_three_stars},
    # 106-111: The orbit is not a circle.
    {'id': 'p15_three_dirs',       'start_w': 106, 'end_w': 111, 'renderer': card_p15_three_dirs},
    # 112-120: It is a slow, wobbling, slightly drunk figure 8.
    {'id': 'p16_not_circle',       'start_w': 112, 'end_w': 120, 'renderer': card_p16_not_circle},
    # 121-128: Sometimes the planet swings close to one star,
    {'id': 'p17_figure_8',         'start_w': 121, 'end_w': 128, 'renderer': card_p17_figure_8},
    # 129-135: then back out, then close to another.
    {'id': 'p18_swings_close',     'start_w': 129, 'end_w': 135, 'renderer': card_p18_swings_close},
    # 136-145: We have no idea what its atmosphere does under that.
    {'id': 'p19_atmosphere',       'start_w': 136, 'end_w': 145, 'renderer': card_p19_atmosphere},
    # 146-154: We have no idea what its weather looks like.
    {'id': 'p20_weather',          'start_w': 146, 'end_w': 154, 'renderer': card_p20_weather},
    # 155-163: We do not even know if it has weather.
    {'id': 'p21_dont_know',        'start_w': 155, 'end_w': 163, 'renderer': card_p21_dont_know},
    # 164-169: It is the kind of place
    {'id': 'p22_has_weather',      'start_w': 164, 'end_w': 169, 'renderer': card_p22_has_weather},
    # 170-176: where a calendar would be a lie,
    {'id': 'p23_calendar_lie',     'start_w': 170, 'end_w': 176, 'renderer': card_p23_calendar_lie},
    # 177-182: where sunrise is a meaningless word,
    {'id': 'p24_sunrise',          'start_w': 177, 'end_w': 182, 'renderer': card_p24_sunrise},
    # 183-190: because the light is always coming from somewhere,
    {'id': 'p25_shadows_lying',    'start_w': 183, 'end_w': 190, 'renderer': card_p25_shadows_lying},
    # 191-196: and the shadows are always lying.
    {'id': 'p26_sits_there',       'start_w': 191, 'end_w': 196, 'renderer': card_p26_sits_there},
    # 197-209: And the planet just sits there, three suns, wobbling, doing its impossible thing.
    {'id': 'p27_not_calm',         'start_w': 197, 'end_w': 209, 'renderer': card_p27_not_calm},
]


def build_card_schedule(alignment):
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

    Each card's renderer is called with `t=<card start time>` so the
    micro-motion loop has a stable phase per card. The card stays on
    screen for `n_frames` ticks of the renderer (PNG snapshot per
    frame), giving a slow 1-2s micro-loop visual.
    """
    os.makedirs(out_dir, exist_ok=True)
    total_frames = 0
    frame_map = []

    for card in schedule:
        n_frames = max(1, int(round((card['end'] - card['start']) * fps)))
        # Re-render every 6 frames (= 0.2s) so the micro-motion is visible
        # without spending too much CPU.
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
    print('Card schedule (round 4 — 27 cards):')
    for s in schedule:
        dur = s['end'] - s['start']
        marker = ' [STICKMAN-ONLY]' if (s['expression'] is None and s['pose'] is None) else ''
        print(f"  {s['id']:25s}  {s['start']:5.2f}s -> {s['end']:5.2f}s  "
              f"({dur:4.2f}s)  [expr={s['expression']}, pose={s['pose']}]{marker}")

    out_dir = os.path.join(os.path.dirname(__file__), args.frames_dir)
    audio_duration = alignment['duration_s']
    schedule_total = schedule[-1]['end'] if schedule else 0.0
    audio_frames = int(round(audio_duration * FPS))
    schedule_frames = sum(max(1, int(round((c['end'] - c['start']) * FPS))) for c in schedule)
    hold_last_frames = max(0, audio_frames - schedule_frames)
    print(f'\nAudio: {audio_duration:.2f}s ({audio_frames} frames)')
    print(f'Schedule cards sum to {schedule_frames} frames')
    print(f'Holding last card for {hold_last_frames} extra frames')
    n_frames, frame_map = render_segment(schedule, out_dir,
                                         hold_last_frames=hold_last_frames)
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
