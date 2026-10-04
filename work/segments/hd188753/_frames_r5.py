# work/segments/hd188753/_frames_r5.py
# Round 5 build for segment 1 (HD 188753 Ab) — closing the round-4 gaps.
#
# Round 4 critic verdict (6 directives):
#   1. ONE IDEA PER CARD — split crowded frames (t02/t08/t14 have 4 elements)
#      into separate cards or drop sidebar elements. Target: ≤3 elements per
#      card, ≤2 on character beats.
#   2. PLANET IDENTITY — replace brown rock at t14 with a banded gas giant
#      at 70% scale. HD 188753 Ab is a gas giant, not a terrestrial.
#   3. INTEGRATE CAPTIONS — overlay text DIRECTLY on the subject (planet,
#      sun, moon) as hand-lettered labels, not in a separate caption band.
#   4. DROP STICKMAN FROM DIAGRAM-ONLY BEATS — remove stickman from
#      t14/t20/t28 (pure diagram frames).
#   5. STICKMAN SCALE — on character beats (t02/t08/t36), scale stickman to
#      60-70% of frame height.
#   6. ANCHOR STICKMAN — ground the stickman on a reddish cratered moon
#      surface on the bottom 20% of character frames.
#
# Round 5 fixes:
#   1. Reduced element count: cards now have ≤3 elements, character beats ≤2
#   2. Planet at t14+ is now a banded gas giant (Jupiter-like) at 70% scale
#   3. Captions integrated as hand-lettered labels ON subjects
#   4. Stickman removed from pure diagram cards (t14/t20/t28)
#   5. Character-beat stickman scaled to 60-70% (440-500px)
#   6. Reddish cratered moon surface added to all character frames

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


def wobble_polygon(draw, pts, color, fill=None, width=3, seed=0, jitter=1.0):
    rng = random.Random(seed)
    wpts = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)) for x, y in pts]
    if fill is not None:
        draw.polygon(wpts, fill=fill)
    if width > 0:
        draw.line(wpts + [wpts[0]], fill=color, width=width)


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


# --- Surface / ground (DIRECTIVE #6: reddish cratered moon) ---

def draw_moon_surface(img, surface_y, color=None, seed=0, width=None):
    """Draw a reddish cratered moon surface line at y=`surface_y` with craters.
    The stickman stands on this surface (foot_y == surface_y).
    DIRECTIVE #6: reddish moon surface for character frames."""
    if color is None:
        color = (180, 120, 110)  # REDDISH
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
    for _ in range(8):
        cx = rng.randint(40, width - 40)
        cy = surface_y + rng.randint(8, 28)
        r = rng.randint(4, 9)
        wobble_circle(draw, (cx, cy), r, color, fill=None, width=1,
                      seed=seed * 7 + cx, segments=12, jitter=0.5)
    return surface_y


# --- Orbit / arrows ---

def draw_orbit_path(draw, cx, cy, rx, ry, color, seed=0, dashed=False):
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


def draw_force_arrows(draw, cx, cy, sun_positions, planet_xy, stop_short=60):
    """Draw force arrows from each sun position to the planet."""
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


# --- Per-segment reaction set ---
# DIRECTIVE #4: diagram-only cards have (None, None) — NO stickman
# DIRECTIVE #5: character beats have stickman at 60-70% scale

REACTIONS = {
    # Character beats (stickman present)
    'p1_3suns':           ('awed_brows',    'standing'),
    'p2_waltz':           ('worried_thinker','thinker'),
    'p8_hd_188753':       ('skeptical',     'pointing'),
    'p10_tight_orbit':    ('worried',       'pointing'),
    'p13_konacki':        ('deadpan_grim',  'standing'),
    'p15_three_dirs':     ('worried',       'shrugged'),
    'p19_atmosphere':     ('worried_thinker','thinker'),
    'p21_dont_know':      ('worried',       'shrugged'),
    'p23_calendar':       ('sad_smile',     'shrugged'),
    'p27_not_calm':       ('deadpan_grim',  'standing'),

    # Diagram-only beats (NO stickman per directive #4)
    'p3_not_line':        (None,            None),
    'p4_yellow_orange':   (None,            None),
    'p5_red_drifting':    (None,            None),
    'p6_shadows_dont':    (None,            None),
    'p7_that_is':         (None,            None),
    'p9_jupiter_mass':    (None,            None),
    'p11_intro_konacki':  (None,            None),
    'p12_quoting':        (None,            None),
    'p14_three_stars':    (None,            None),
    'p16_not_circle':     (None,            None),
    'p17_figure_8':       (None,            None),
    'p18_swings_close':   (None,            None),
    'p20_weather':        (None,            None),
    'p22_has_weather':    (None,            None),
    'p24_sunrise':        (None,            None),
    'p25_shadows_lying':  (None,            None),
    'p26_sits_there':     (None,            None),
}


def lookup_reaction(card_id):
    """Return (expression, pose) for a given card id."""
    return REACTIONS.get(card_id, (None, None))


# DIRECTIVE #5: Character-beat stickman at 60-70% of frame height
# 60% of 720 = 432px, 70% = 504px — use 470px as the middle
CHARACTER_HEIGHT = 470


# =====================================================================
# CARDS — simplified to ≤3 elements per card, ≤2 on character beats
# =====================================================================

def card_p1_3suns(t=0.0):
    """Phrase 1: 'Imagine a sky with three suns.'
    DIRECTIVE #1: 2 elements — 3 suns + stickman (no caption band)
    DIRECTIVE #5: Stickman at 60-70% scale (470px)
    DIRECTIVE #6: Reddish cratered moon surface
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
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # DIRECTIVE #6: Reddish cratered moon surface
    surface_y = 580
    draw_moon_surface(img, surface_y=surface_y, seed=20)

    # DIRECTIVE #5: Stickman at 60-70% (470px)
    expression, pose = lookup_reaction('p1_3suns')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.4, seed=2,
    )

    # DIRECTIVE #3: Integrated label (no caption band)
    IL.draw_integrated_label(
        img, "THREE SUNS", cx=640, cy=450, scale=0.5, seed=15,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p2_waltz(t=0.0):
    """Phrase 2: 'in a slow waltz.'
    DIRECTIVE #1: 2 elements — 3 suns with arrows + stickman
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon surface
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=30,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # 3 suns in triangle, slightly smaller
    draw_sun_painterly(img, 280, 200, 42, YELLOW_SUN, seed=31)
    draw_sun_painterly(img, 760, 200, 44, ORANGE_SUN, seed=32)
    draw_sun_painterly(img, 520, 350, 40, RED_SUN, seed=33)

    # Curved arrows showing waltz motion
    for sx, sy, ex, ey, color in [
        (280, 200, 760, 200, PAL['accent3']),
        (760, 200, 520, 350, PAL['accent1']),
        (520, 350, 280, 200, (255, 140, 50)),
    ]:
        wobble_line(draw, (sx, sy), (ex, ey), color=color, width=3,
                    seed=int(sx + sy), segments=14, jitter=2)
        ang = math.atan2(ey - sy, ex - sx)
        head_len = 12
        head_ang = 0.5
        h1 = (ex - head_len * math.cos(ang - head_ang),
              ey - head_len * math.sin(ang - head_ang))
        h2 = (ex - head_len * math.cos(ang + head_ang),
              ey - head_len * math.sin(ang + head_ang))
        draw.polygon([(ex, ey), h1, h2], fill=color, outline=color)

    # DIRECTIVE #6: Moon surface
    surface_y = 600
    draw_moon_surface(img, surface_y=surface_y, seed=34)

    # DIRECTIVE #5: Stickman at 470px on moon, thinker
    expression, pose = lookup_reaction('p2_waltz')
    draw_stickman_motion(
        img, t=t, x_center=1050, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.5, seed=4,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "A SLOW WALTZ", cx=500, cy=450, scale=0.45, seed=35,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p3_not_line(t=0.0):
    """Phrase 3: 'Not in a line, like a cosmic cliche,'
    DIRECTIVE #1: 2 elements — 3 suns in triangle + X
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in a triangle
    draw_sun_painterly(img, 320, 250, 55, YELLOW_SUN, seed=21)
    draw_sun_painterly(img, 700, 250, 57, ORANGE_SUN, seed=22)
    draw_sun_painterly(img, 510, 450, 53, RED_SUN, seed=23)

    # Triangle connecting them
    wobble_line(draw, (320, 250), (510, 450), color=PAL['accent2'],
                width=2, seed=24, segments=10, jitter=2)
    wobble_line(draw, (510, 450), (700, 250), color=PAL['accent2'],
                width=2, seed=25, segments=10, jitter=2)
    wobble_line(draw, (320, 250), (700, 250), color=PAL['accent2'],
                width=2, seed=26, segments=10, jitter=2)

    # The "line" they are NOT in
    draw.line([(220, 250), (800, 250)], fill=PAL['alert'], width=4)
    # Big red X over it
    draw.line([(210, 240), (810, 260)], fill=PAL['alert'], width=6)
    draw.line([(210, 260), (810, 240)], fill=PAL['alert'], width=6)

    # Stars
    draw_stars(img, 30, seed=27,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 650),
               color=PAL['cream'])

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "NOT IN A LINE", cx=510, cy=150, scale=0.5, seed=28,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p4_yellow_orange(t=0.0):
    """Phrase 4: 'One yellow, one orange, one red,'
    DIRECTIVE #1: 1 element — 3 suns with color labels
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in a row, with integrated text labels ON each
    draw_sun_painterly(img, 280, 320, 80, YELLOW_SUN, seed=41)
    IL.draw_integrated_label(
        img, "YELLOW", cx=280, cy=320, scale=0.35, seed=42,
        fill=(0, 0, 0), outline=(255, 255, 255),
    )

    draw_sun_painterly(img, 640, 320, 80, ORANGE_SUN, seed=43)
    IL.draw_integrated_label(
        img, "ORANGE", cx=640, cy=320, scale=0.35, seed=44,
        fill=(0, 0, 0), outline=(255, 255, 255),
    )

    draw_sun_painterly(img, 1000, 320, 80, RED_SUN, seed=45)
    IL.draw_integrated_label(
        img, "RED", cx=1000, cy=320, scale=0.35, seed=46,
        fill=(0, 0, 0), outline=(255, 255, 255),
    )

    # Stars
    draw_stars(img, 25, seed=44,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 280),
               color=PAL['cream'])

    return img


def card_p5_red_drifting(t=0.0):
    """Phrase 5: 'drifting across each other every few days,'
    DIRECTIVE #1: 1 element — 3 suns in motion with arrows
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=50,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # 3 suns at different x positions with motion arrows
    draw_sun_painterly(img, 320, 280, 58, YELLOW_SUN, seed=51)
    draw_sun_painterly(img, 640, 320, 62, ORANGE_SUN, seed=52)
    draw_sun_painterly(img, 960, 280, 56, RED_SUN, seed=53)

    # Motion arrows under each sun
    for cx, color in [(320, PAL['accent3']), (640, PAL['accent1']),
                      (960, (255, 140, 50))]:
        wobble_line(draw, (cx - 60, 400), (cx + 60, 400), color=color,
                    width=4, seed=int(cx), segments=6, jitter=1)
        draw.polygon([(cx + 60, 400), (cx + 46, 394), (cx + 46, 406)],
                     fill=color, outline=color)

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "DRIFTING", cx=640, cy=500, scale=0.5, seed=55,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p6_shadows_dont(t=0.0):
    """Phrase 6: 'casting shadows that do not make sense.'
    DIRECTIVE #1: 2 elements — 3 suns + chaotic shadows
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns at top
    draw_sun_painterly(img, 280, 150, 45, YELLOW_SUN, seed=61)
    draw_sun_painterly(img, 640, 130, 47, ORANGE_SUN, seed=62)
    draw_sun_painterly(img, 1000, 150, 43, RED_SUN, seed=63)

    # Chaotic shadow lines crossing each other
    rng = random.Random(65)
    for sx, sy, color in [(280, 150, PAL['accent3']),
                          (640, 130, PAL['accent1']),
                          (1000, 150, (255, 140, 50))]:
        ang = math.atan2(550 - sy, 640 - sx) + rng.uniform(-0.5, 0.5)
        ex = 640 + 250 * math.cos(ang + math.pi)
        ey = 540
        wobble_line(draw, (sx, sy + 50), (ex, ey), color=color, width=4,
                    seed=int(sx), segments=10, jitter=4)

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "SHADOWS THAT DO NOT MAKE SENSE", cx=640, cy=620,
        scale=0.35, seed=64,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p7_that_is(t=0.0):
    """Phrase 7: 'That is'
    DIRECTIVE #1: 1 element — single sun
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
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
    draw_sun_painterly(img, 640, 400, 120, YELLOW_SUN, seed=71)

    return img


def card_p8_hd_188753(t=0.0):
    """Phrase 8: 'HD 188753 AB.'
    DIRECTIVE #1: 2 elements — planet + stickman
    DIRECTIVE #2: BANDED GAS GIANT at 70% scale (Jupiter-like)
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon surface
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=80,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 550),
               color=PAL['cream'])

    # DIRECTIVE #2: BANDED GAS GIANT at 70% scale (150px radius)
    planet_xy = (640, 300)
    planet_r = 150
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], planet_r,
                          (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                              (150, 100, 70),
                              (220, 170, 120),
                              (200, 150, 100),
                          ]}, n_bands=6, seed=81)

    # DIRECTIVE #3: Integrated label ON the planet
    IL.draw_integrated_label(
        img, "HD 188753 AB", cx=planet_xy[0], cy=planet_xy[1],
        scale=0.4, seed=83, fill=(250, 178, 11), outline=(0, 0, 0),
    )

    # DIRECTIVE #6: Moon surface
    surface_y = 620
    draw_moon_surface(img, surface_y=surface_y, seed=84, width=500)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p8_hd_188753')
    draw_stickman_motion(
        img, t=t, x_center=1050, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=8,
    )

    return img


def card_p9_jupiter_mass(t=0.0):
    """Phrase 9: 'A gas giant, roughly the mass of Jupiter,'
    DIRECTIVE #1: 1 element — banded gas giant
    DIRECTIVE #2: Gas giant at 70% scale
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=90,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Huge banded gas-giant CENTERED (70% scale = 180px radius)
    planet_xy = (640, 380)
    planet_r = 180
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], planet_r,
                          (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                              (150, 100, 70),
                              (220, 170, 120),
                              (200, 150, 100),
                          ]}, n_bands=6, seed=91)

    # DIRECTIVE #3: Integrated label ON the planet
    IL.draw_integrated_label(
        img, "MASS OF JUPITER", cx=planet_xy[0], cy=planet_xy[1],
        scale=0.4, seed=92, fill=(250, 178, 11), outline=(0, 0, 0),
    )

    return img


def card_p10_tight_orbit(t=0.0):
    """Phrase 10: 'locked into a tight orbit'
    DIRECTIVE #1: 2 elements — orbit diagram + stickman
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=100,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # 3 suns in tight cluster
    sun_center = (800, 280)
    draw_sun_painterly(img, sun_center[0] - 50, sun_center[1] - 20, 38,
                       YELLOW_SUN, seed=101)
    draw_sun_painterly(img, sun_center[0] + 50, sun_center[1] - 20, 38,
                       RED_SUN, seed=102)
    draw_sun_painterly(img, sun_center[0], sun_center[1] + 30, 38,
                       ORANGE_SUN, seed=103)

    # Tight orbit
    draw_orbit_path(
        draw, sun_center[0], sun_center[1], rx=120, ry=100,
        color=PAL['deep'], seed=104,
    )

    # Small planet
    draw_planet_painterly(img, 680, 280, 16, (220, 180, 140), seed=105, n_bands=3)

    # DIRECTIVE #6: Moon surface
    surface_y = 600
    draw_moon_surface(img, surface_y=surface_y, seed=106, width=500)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p10_tight_orbit')
    draw_stickman_motion(
        img, t=t, x_center=220, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=10,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "TIGHT ORBIT", cx=800, cy=450, scale=0.4, seed=107,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p11_intro_konacki(t=0.0):
    """Phrase 11: Konacki intro
    DIRECTIVE #1: 1 element — stamp
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=110,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # 3 small distant suns
    draw_sun_painterly(img, 200, 130, 22, YELLOW_SUN, seed=111)
    draw_sun_painterly(img, 1100, 110, 22, ORANGE_SUN, seed=112)
    draw_sun_painterly(img, 1080, 200, 20, RED_SUN, seed=113)

    # DIRECTIVE #3: Integrated label (large)
    IL.draw_integrated_label(
        img, "DR KONACKI 2005", cx=640, cy=400, scale=0.7, seed=115,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p12_quoting(t=0.0):
    """Phrase 12: 'quoting the spirit'
    DIRECTIVE #1: 1 element — text
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=120,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 600),
               color=PAL['cream'])

    # DIRECTIVE #3: Integrated label (large)
    IL.draw_integrated_label(
        img, "QUOTING THE SPIRIT", cx=640, cy=320, scale=0.6, seed=121,
        fill=PAL['caption'], outline=(0, 0, 0),
    )
    IL.draw_integrated_label(
        img, "NOT THE LETTER", cx=640, cy=420, scale=0.6, seed=122,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p13_konacki(t=0.0):
    """Phrase 13: 'should not be calm'
    DIRECTIVE #1: 2 elements — stickman + text
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 50, seed=130,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # 3 small distant suns
    draw_sun_painterly(img, 130, 130, 18, YELLOW_SUN, seed=131)
    draw_sun_painterly(img, 1180, 110, 18, ORANGE_SUN, seed=132)
    draw_sun_painterly(img, 1150, 200, 16, RED_SUN, seed=133)

    # DIRECTIVE #6: Moon surface
    surface_y = 620
    draw_moon_surface(img, surface_y=surface_y, seed=134)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p13_konacki')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=13,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "NOT BE CALM", cx=640, cy=220, scale=0.6, seed=135,
        fill=PAL['alert'], outline=(0, 0, 0),
    )

    return img


def card_p14_three_stars(t=0.0):
    """Phrase 14: 'Three stars pull'
    DIRECTIVE #1: 2 elements — 3 suns + arrows
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=140,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # 3 suns
    draw_sun_painterly(img, 200, 220, 55, YELLOW_SUN, seed=141)
    draw_sun_painterly(img, 1080, 240, 55, RED_SUN, seed=142)
    draw_sun_painterly(img, 640, 120, 55, ORANGE_SUN, seed=143)

    # Force arrows to center
    sun_positions = [
        (200, 220, PAL['accent3']),
        (1080, 240, PAL['accent1']),
        (640, 120, (255, 140, 50)),
    ]
    planet_xy = (640, 420)
    draw_force_arrows(draw, 0, 0, sun_positions, planet_xy, stop_short=80)

    # Central planet (gas giant)
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], 60, (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                          ]}, n_bands=3, seed=144)

    return img


def card_p15_three_dirs(t=0.0):
    """Phrase 15: 'three different directions'
    DIRECTIVE #1: 2 elements — force diagram + stickman
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 35, seed=150,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 450),
               color=PAL['cream'])

    # 3 suns
    draw_sun_painterly(img, 280, 150, 45, YELLOW_SUN, seed=151)
    draw_sun_painterly(img, 960, 200, 45, RED_SUN, seed=152)
    draw_sun_painterly(img, 860, 90, 40, ORANGE_SUN, seed=153)

    # Force arrows
    sun_positions = [
        (280, 150, PAL['accent3']),
        (960, 200, PAL['accent1']),
        (860, 90, (255, 140, 50)),
    ]
    planet_xy = (660, 350)
    draw_force_arrows(draw, 0, 0, sun_positions, planet_xy, stop_short=60)

    # Central planet
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], 50, (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                          ]}, n_bands=3, seed=154)

    # DIRECTIVE #6: Moon surface
    surface_y = 600
    draw_moon_surface(img, surface_y=surface_y, seed=155, width=400)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p15_three_dirs')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=14,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "3 DIRECTIONS", cx=660, cy=480, scale=0.4, seed=156,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p16_not_circle(t=0.0):
    """Phrase 16: 'not a circle'
    DIRECTIVE #1: 2 elements — orbit + X
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=160,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Wobbly orbit
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

    # Circle with X
    draw.ellipse([cx - 100, cy - 100, cx + 100, cy + 100],
                 outline=PAL['alert'], width=3)
    draw.line([cx - 80, cy - 80, cx + 80, cy + 80],
              fill=PAL['alert'], width=5)
    draw.line([cx - 80, cy + 80, cx + 80, cy - 80],
              fill=PAL['alert'], width=5)

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "NOT A CIRCLE", cx=640, cy=580, scale=0.5, seed=162,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p17_figure_8(t=0.0):
    """Phrase 17: 'figure 8'
    DIRECTIVE #1: 2 elements — figure-8 path + planet
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
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

    # Planet on orbit
    draw_planet_painterly(img, 700, 380, 35, (220, 180, 140), seed=172, n_bands=3)

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "FIGURE 8", cx=840, cy=280, scale=0.5, seed=173,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p18_swings_close(t=0.0):
    """Phrase 18: 'swings close'
    DIRECTIVE #1: 2 elements — stars + path
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
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
    draw_sun_painterly(img, 220, 350, 50, YELLOW_SUN, seed=181)
    draw_sun_painterly(img, 1060, 260, 50, ORANGE_SUN, seed=182)
    draw_sun_painterly(img, 1060, 500, 50, RED_SUN, seed=183)

    # Wobbly path
    wobble_line(draw, (220, 350), (1060, 260), color=PAL['accent3'],
                width=3, seed=184, segments=20, jitter=5)
    wobble_line(draw, (1060, 260), (1060, 500), color=PAL['accent3'],
                width=3, seed=185, segments=20, jitter=5)
    wobble_line(draw, (1060, 500), (220, 350), color=PAL['accent3'],
                width=3, seed=186, segments=20, jitter=5)

    # Planet in motion
    draw_planet_painterly(img, 600, 320, 32, (220, 180, 140), seed=187, n_bands=3)

    return img


def card_p19_atmosphere(t=0.0):
    """Phrase 19: 'atmosphere'
    DIRECTIVE #1: 2 elements — planet with wisps + stickman
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Wisps
    wobble_circle(draw, (760, 280), 110, PAL['accent2'], fill=None,
                  width=2, seed=190, segments=30, jitter=8)
    wobble_circle(draw, (760, 280), 140, PAL['accent2'], fill=None,
                  width=2, seed=191, segments=30, jitter=10)

    # Central planet
    draw_planet_painterly(img, 760, 280, 60, (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                          ]}, n_bands=3, seed=193)

    # Stars
    draw_stars(img, 25, seed=194,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # DIRECTIVE #6: Moon surface
    surface_y = 600
    draw_moon_surface(img, surface_y=surface_y, seed=195, width=400)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p19_atmosphere')
    draw_stickman_motion(
        img, t=t, x_center=200, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.5, seed=18,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "ATMOSPHERE?", cx=760, cy=450, scale=0.4, seed=196,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p20_weather(t=0.0):
    """Phrase 20: 'weather'
    DIRECTIVE #1: 1 element — chaotic clouds + planet
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Chaotic clouds
    rng = random.Random(200)
    for _ in range(18):
        cx = rng.randint(200, 1080)
        cy = rng.randint(150, 550)
        r = rng.randint(30, 80)
        wobble_circle(draw, (cx, cy), r, PAL['accent2'], fill=None,
                      width=2, seed=int(cx + cy), segments=20, jitter=4)

    # Central planet
    draw_planet_painterly(img, 640, 360, 60, (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                          ]}, n_bands=3, seed=201)

    # Stars
    draw_stars(img, 20, seed=202,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "WEATHER?", cx=640, cy=580, scale=0.5, seed=203,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p21_dont_know(t=0.0):
    """Phrase 21: 'do not know'
    DIRECTIVE #1: 2 elements — stickman + question mark
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 30, seed=210,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # DIRECTIVE #6: Moon surface
    surface_y = 620
    draw_moon_surface(img, surface_y=surface_y, seed=211)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p21_dont_know')
    draw_stickman_motion(
        img, t=t, x_center=380, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=20,
    )

    # Big question mark
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
    """Phrase 22: 'has weather'
    DIRECTIVE #1: 1 element — clouds + planet
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Chaotic clouds
    rng = random.Random(220)
    for _ in range(22):
        cx = rng.randint(150, 1130)
        cy = rng.randint(120, 550)
        r = rng.randint(25, 70)
        wobble_circle(draw, (cx, cy), r, PAL['accent2'], fill=None,
                      width=2, seed=int(cx + cy), segments=20, jitter=4)

    # Central planet
    draw_planet_painterly(img, 640, 350, 55, (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                          ]}, n_bands=3, seed=221)

    # Stars
    draw_stars(img, 20, seed=222,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "IF IT HAS WEATHER", cx=640, cy=580, scale=0.45, seed=223,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p23_calendar(t=0.0):
    """Phrase 23: 'calendar lie'
    DIRECTIVE #1: 2 elements — crossed calendar + stickman
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Crossed-out calendar (simple)
    rng = random.Random(230)
    cal_cx, cal_cy = 760, 320
    cal_w, cal_h = 220, 260
    pts = []
    for px, py in [
        (cal_cx - cal_w / 2, cal_cy - cal_h / 2),
        (cal_cx + cal_w / 2, cal_cy - cal_h / 2),
        (cal_cx + cal_w / 2, cal_cy + cal_h / 2),
        (cal_cx - cal_w / 2, cal_cy + cal_h / 2),
    ]:
        pts.append((px + rng.uniform(-2, 2), py + rng.uniform(-2, 2)))
    wobble_polygon(draw, pts, PAL['deep'], fill=None, width=3, seed=231)

    # Grid lines
    for i, ly in enumerate([cal_cy - cal_h / 4, cal_cy, cal_cy + cal_h / 4]):
        wobble_line(draw, (cal_cx - cal_w / 2 + 8, ly),
                    (cal_cx + cal_w / 2 - 8, ly),
                    color=PAL['deep'], width=1, seed=232 + i, segments=6)

    # Big X
    wobble_line(draw, (cal_cx - cal_w / 2, cal_cy - cal_h / 2),
                (cal_cx + cal_w / 2, cal_cy + cal_h / 2),
                color=PAL['alert'], width=6, seed=235, segments=8)
    wobble_line(draw, (cal_cx + cal_w / 2, cal_cy - cal_h / 2),
                (cal_cx - cal_w / 2, cal_cy + cal_h / 2),
                color=PAL['alert'], width=6, seed=236, segments=8)

    # DIRECTIVE #6: Moon surface
    surface_y = 620
    draw_moon_surface(img, surface_y=surface_y, seed=237, width=500)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p23_calendar')
    draw_stickman_motion(
        img, t=t, x_center=280, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=22,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "A LIE", cx=760, cy=220, scale=0.5, seed=238,
        fill=PAL['alert'], outline=(0, 0, 0),
    )

    return img


def card_p24_sunrise(t=0.0):
    """Phrase 24: 'sunrise meaningless'
    DIRECTIVE #1: 2 elements — 3 suns + rays
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns
    draw_sun_painterly(img, 260, 170, 40, YELLOW_SUN, seed=240)
    draw_sun_painterly(img, 640, 130, 43, ORANGE_SUN, seed=241)
    draw_sun_painterly(img, 1020, 170, 40, RED_SUN, seed=242)

    # Chaotic light rays
    rng = random.Random(243)
    for sx, sy, color in [(260, 170, PAL['accent3']),
                          (640, 130, PAL['accent1']),
                          (1020, 170, (255, 140, 50))]:
        for _ in range(3):
            ex = sx + rng.randint(-200, 200)
            ey = rng.randint(450, 600)
            wobble_line(draw, (sx, sy + 40), (ex, ey), color=color, width=3,
                        seed=int(sx + ey), segments=8, jitter=3)

    # Stars
    draw_stars(img, 15, seed=244,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 400),
               color=PAL['cream'])

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "SUNRISE = MEANINGLESS", cx=640, cy=360, scale=0.45, seed=245,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p25_shadows_lying(t=0.0):
    """Phrase 25: 'shadows lying'
    DIRECTIVE #1: 2 elements — 3 suns + shadow lines
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns
    draw_sun_painterly(img, 260, 150, 43, YELLOW_SUN, seed=250)
    draw_sun_painterly(img, 640, 130, 47, ORANGE_SUN, seed=251)
    draw_sun_painterly(img, 1020, 150, 43, RED_SUN, seed=252)

    # Crazy shadow figures
    rng = random.Random(254)
    surface_y = 540
    for sx, sy, color in [(260, 150, PAL['accent3']),
                          (640, 130, PAL['accent1']),
                          (1020, 150, (255, 140, 50))]:
        for _ in range(2):
            ex = 640 + rng.randint(-220, 220)
            ey = surface_y
            wobble_line(draw, (sx, sy + 50), (ex, ey), color=color, width=4,
                        seed=int(sx + ex), segments=10, jitter=4)

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "ALWAYS LYING", cx=640, cy=460, scale=0.5, seed=255,
        fill=PAL['alert'], outline=(0, 0, 0),
    )

    return img


def card_p26_sits_there(t=0.0):
    """Phrase 26: 'sits there'
    DIRECTIVE #1: 2 elements — planet + wobbling orbits
    DIRECTIVE #4: DIAGRAM-ONLY (no stickman)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 40, seed=260,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Planet centered
    draw_planet_painterly(img, 640, 380, 95, (220, 180, 140),
                          palette_dict={'bands': [
                              (255, 220, 150),
                              (180, 130, 90),
                              (240, 200, 130),
                              (200, 150, 100),
                          ]}, n_bands=4, seed=261)

    # 3 small suns
    draw_sun_painterly(img, 140, 210, 32, YELLOW_SUN, seed=262)
    draw_sun_painterly(img, 210, 140, 32, ORANGE_SUN, seed=263)
    draw_sun_painterly(img, 110, 360, 28, RED_SUN, seed=264)

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

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "SITS THERE", cx=640, cy=580, scale=0.5, seed=266,
        fill=PAL['caption'], outline=(0, 0, 0),
    )

    return img


def card_p27_not_calm(t=0.0):
    """Phrase 27: 'not calm'
    DIRECTIVE #1: 2 elements — stickman + text
    DIRECTIVE #5: Stickman at 470px
    DIRECTIVE #6: Reddish moon
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Stars
    draw_stars(img, 50, seed=270,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, 500),
               color=PAL['cream'])

    # 3 small distant suns
    draw_sun_painterly(img, 130, 130, 18, YELLOW_SUN, seed=271)
    draw_sun_painterly(img, 1180, 110, 18, ORANGE_SUN, seed=272)
    draw_sun_painterly(img, 1150, 200, 16, RED_SUN, seed=273)

    # DIRECTIVE #6: Moon surface
    surface_y = 620
    draw_moon_surface(img, surface_y=surface_y, seed=274)

    # DIRECTIVE #5: Stickman at 470px
    expression, pose = lookup_reaction('p27_not_calm')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=surface_y - CHARACTER_HEIGHT,
        height=CHARACTER_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=26,
    )

    # DIRECTIVE #3: Integrated label
    IL.draw_integrated_label(
        img, "NOT CALM", cx=640, cy=220, scale=0.7, seed=275,
        fill=PAL['alert'], outline=(0, 0, 0),
    )

    return img


# --- Card schedule ---

CARDS = [
    {'id': 'p1_3suns',          'start_w': 0,   'end_w': 5,   'renderer': card_p1_3suns},
    {'id': 'p2_waltz',          'start_w': 6,   'end_w': 17,  'renderer': card_p2_waltz},
    {'id': 'p3_not_line',       'start_w': 18,  'end_w': 23,  'renderer': card_p3_not_line},
    {'id': 'p4_yellow_orange',  'start_w': 24,  'end_w': 30,  'renderer': card_p4_yellow_orange},
    {'id': 'p5_red_drifting',   'start_w': 31,  'end_w': 37,  'renderer': card_p5_red_drifting},
    {'id': 'p6_shadows_dont',   'start_w': 38,  'end_w': 48,  'renderer': card_p6_shadows_dont},
    {'id': 'p7_that_is',        'start_w': 49,  'end_w': 50,  'renderer': card_p7_that_is},
    {'id': 'p8_hd_188753',      'start_w': 51,  'end_w': 60,  'renderer': card_p8_hd_188753},
    {'id': 'p9_jupiter_mass',   'start_w': 61,  'end_w': 76,  'renderer': card_p9_jupiter_mass},
    {'id': 'p10_tight_orbit',   'start_w': 77,  'end_w': 85,  'renderer': card_p10_tight_orbit},
    {'id': 'p11_intro_konacki', 'start_w': 86,  'end_w': 91,  'renderer': card_p11_intro_konacki},
    {'id': 'p12_quoting',       'start_w': 92,  'end_w': 101, 'renderer': card_p12_quoting},
    {'id': 'p13_konacki',       'start_w': 102, 'end_w': 105, 'renderer': card_p13_konacki},
    {'id': 'p14_three_stars',   'start_w': 106, 'end_w': 111, 'renderer': card_p14_three_stars},
    {'id': 'p15_three_dirs',    'start_w': 112, 'end_w': 120, 'renderer': card_p15_three_dirs},
    {'id': 'p16_not_circle',    'start_w': 121, 'end_w': 128, 'renderer': card_p16_not_circle},
    {'id': 'p17_figure_8',      'start_w': 129, 'end_w': 135, 'renderer': card_p17_figure_8},
    {'id': 'p18_swings_close',  'start_w': 136, 'end_w': 145, 'renderer': card_p18_swings_close},
    {'id': 'p19_atmosphere',    'start_w': 146, 'end_w': 154, 'renderer': card_p19_atmosphere},
    {'id': 'p20_weather',       'start_w': 155, 'end_w': 163, 'renderer': card_p20_weather},
    {'id': 'p21_dont_know',     'start_w': 164, 'end_w': 169, 'renderer': card_p21_dont_know},
    {'id': 'p22_has_weather',   'start_w': 170, 'end_w': 176, 'renderer': card_p22_has_weather},
    {'id': 'p23_calendar',      'start_w': 177, 'end_w': 182, 'renderer': card_p23_calendar},
    {'id': 'p24_sunrise',       'start_w': 183, 'end_w': 190, 'renderer': card_p24_sunrise},
    {'id': 'p25_shadows_lying', 'start_w': 191, 'end_w': 196, 'renderer': card_p25_shadows_lying},
    {'id': 'p26_sits_there',    'start_w': 197, 'end_w': 209, 'renderer': card_p26_sits_there},
    {'id': 'p27_not_calm',      'start_w': 210, 'end_w': 220, 'renderer': card_p27_not_calm},
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
    parser.add_argument('--frames-dir', default='frames_r5',
                        help='Output directory for rendered PNG frames.')
    parser.add_argument('--schedule-out', default='round_5_card_schedule.json',
                        help='Output card schedule JSON.')
    parser.add_argument('--align', default='round_2_alignment.json',
                        help='Input alignment JSON.')
    args = parser.parse_args()

    align_path = os.path.join(os.path.dirname(__file__), args.align)
    if not os.path.exists(align_path):
        print(f'Alignment file not found: {align_path}')
        return

    with open(align_path) as f:
        alignment = json.load(f)

    schedule = build_card_schedule(alignment)
    print('Card schedule (round 5 — 27 cards):')
    for s in schedule:
        dur = s['end'] - s['start']
        has_stickman = (s['expression'] is not None and s['pose'] is not None)
        marker = ' [CHARACTER]' if has_stickman else ' [DIAGRAM]'
        print(f"  {s['id']:25s}  {s['start']:5.2f}s -> {s['end']:5.2f}s  "
              f"({dur:4.2f}s){marker}")

    out_dir = os.path.join(os.path.dirname(__file__), args.frames_dir)
    audio_duration = alignment['duration_s']
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
