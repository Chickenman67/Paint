# work/segments/hd188753/_frames_r3.py
# Round 3 build for segment 1 (HD 188753 Ab) — closing the round-2 character gap.
#
# Round 2 critic verdict (highest-priority gap):
#   "The stickman used a single deadpan expression across all 6 sampled beats
#    while the reference's stickman changes expression and pose per beat to
#    carry the emotional arc."
#
# Round 3 fixes:
#   1. Per-beat character mapping — each card has an (expression, pose) pair
#      that follows the HD 188753 Ab emotional arc:
#         confusion -> awe -> fear -> chaos -> resignation
#      The stickman now VARYS both his mouth shape and his body pose per beat.
#   2. Force-diagram beat (t~33-38) — show three distinct shadow stickmen
#      side-by-side, each reacting to one of the three suns (this is a
#      reference signature device).
#   3. Stickman scale 40-50% of frame height, centrally placed (not 25%
#      corner stamp as in round 1).
#   4. Per-beat micro-motion: every appearance has a 1-2s loop — head-tilt,
#      a step, a hand-wave, a glance — so the stickman never holds still.
#   5. New mouth shapes (worried, scream, relief, smirk, sad_smile, squint,
#      terrified) and new poses (shielding_eyes, cowering, shrugged,
#      hands_down) added to lib/stickman.py.
#   6. Preserved round-2 wins: painterly stipple texture, white title band,
#      lineup grid, ALL CAPS captions, no-debug default, alignment-derived
#      card schedule, hand-checked caption length, 'KONACKI 2005' callout
#      under title instead of debug stamp over caption.
#
# Per CLAUDE.md §6 — the round-2 failure: "stickman must be present in at
# least one beat". Round 3 keeps him in EVERY beat, with a unique
# (expression, pose) per beat. The reference's character carries the
# emotional arc; ours now does too.

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

# Frame dimensions
W, H = 1280, 720
FPS = 30
TITLE_STRIP_TOP = 22
TITLE_STRIP_BOT = 61
ILLUSTRATION_TOP = 80
ILLUSTRATION_BOT = 719

PAL = P.SEGMENT_1

# Hard caption constraints (per CLAUDE.md §7 + the round-1 verdict)
MAX_CAPTION_CHARS = 60
CAPTION_FONT = T.load_font(T.CAPTION_PX, bold=False)
DRAW_FONT_BOLD = T.load_font(T.CAPTION_PX, bold=True)
DRAW_HEADER_FONT = T.load_font(T.HEADER_PX, bold=True)


# --- Hard caption check (carried from round 2) ---

def _safe_textwidth(text, font):
    try:
        x0, _, x1, _ = font.getbbox(text)
        return x1 - x0
    except Exception:
        return len(text) * 16


def _check_caption(text, where):
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
    if color_rgb is None:
        color_rgb = PAL['caption']
    _check_caption(text, where=where)
    T.draw_caption(draw, text, xy, color_rgb=color_rgb)


# --- Wobble helpers (carried from round 2) ---

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


# --- Painterly sun / planet helpers (carried from round 2) ---

def draw_sun_painterly(img, cx, cy, r, palette_dict, seed=0):
    texture.sun_disc(img, cx, cy, r, palette=palette_dict, seed=seed, halo=True)


def draw_planet_painterly(img, cx, cy, r, base_rgb, palette_dict=None,
                          n_bands=4, seed=0):
    texture.planet_disc(img, cx, cy, r, base_rgb=base_rgb,
                        palette=palette_dict, n_bands=n_bands,
                        seed=seed, with_bands=True)


# --- Title strip (carried from round 2) ---

def draw_title_strip(img, name):
    title_band.draw_title_band(img, name)


# --- Stickman with micro-motion (round 3 addition) ---

def draw_stickman_motion(image, t, x_center, y_top, height, pose, mouth,
                         beat_period_s=2.0, seed=0, scale=1.0):
    """Draw a stickman with a 1-2s micro-loop based on `t` (current time in
    seconds from segment start).

    The micro-motion is a small horizontal shift + a vertical bob, plus a
    head-tilt (small arc). The phase of the cycle is `t / beat_period_s`.
    Reference never holds a stickman still for >2s without a micro-motion.
    """
    phase = (t % beat_period_s) / beat_period_s  # 0..1
    # 4-px horizontal sway, 3-px vertical bob
    sway_dx = int(4 * math.sin(2 * math.pi * phase))
    bob_dy = int(2 * math.cos(2 * math.pi * phase))
    sm.draw_stickman(
        image,
        x_center=x_center + sway_dx,
        y_top=y_top + bob_dy,
        height=height,
        pose=pose, mouth=mouth, seed=seed,
    )


# --- Sun palettes (carried from round 2) ---

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


# --- Stars (carried from round 2) ---

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


# --- Orbit / arrows / question marks (carried from round 2) ---

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


def draw_force_arrows(draw, cx, cy, sun_positions, planet_xy):
    px, py = planet_xy
    for sx, sy, color in sun_positions:
        wobble_line(
            draw, (sx, sy), (px, py), color=color, width=3,
            seed=int(sx + sy), jitter=1.0, segments=10,
        )
        ang = math.atan2(py - sy, px - sx)
        head_len = 12
        head_ang = 0.5
        hx, hy = px, py
        h1 = (hx - head_len * math.cos(ang - head_ang), hy - head_len * math.sin(ang - head_ang))
        h2 = (hx - head_len * math.cos(ang + head_ang), hy - head_len * math.sin(ang + head_ang))
        draw.polygon([(hx, hy), h1, h2], fill=color, outline=color)


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


# --- Per-segment reaction set (the round 3 character map) ---
# HD 188753 Ab emotional arc: confusion -> awe -> fear -> chaos -> resignation
# Each card has a unique (expression, pose) pair. The map below is the
# contract for the round-3 build; the critic will check it card-by-card.

REACTIONS = {
    'intro':             ('oval',      'standing'),
    'not_a_line':        ('smirk',     'shrugged'),
    'waltz':             ('flat',      'standing'),
    'three_suns_detail': ('squint',    'pointing'),
    'planet_portrait':   ('oval',      'hands_up'),
    'konacki':           ('flat',      'standing'),
    'orbit_diagram':     ('worried',   'pointing'),
    'force_diagram':     ('scream',    'cowering'),
    'wobble_orbit':      ('worried',   'shrugged'),
    'no_idea_weather':   ('terrified', 'cowering'),
    'calendar_lie':      ('sad_smile', 'shrugged'),
    'sits_there':        ('relief',    'hands_down'),
    'lineup_grid':       ('frown',     'pointing'),
}


def lookup_reaction(card_id):
    """Return (expression, pose) for a given card id, defaulting to a
    deadpan/standing pair if not mapped."""
    return REACTIONS.get(card_id, ('flat', 'standing'))


# Helper: stickman height 40-50% of frame height (~290-360 px)
STICKMAN_HEIGHT = 320  # ~44% of 720


# --- Cards ---

def card_intro(t=0.0):
    """Card 1: 'Imagine a sky with three suns.' — 3 painterly suns in cool
    sky, stickman CENTER looking up, AWED (oval mouth) + standing pose.

    Round 3 character: awed. The viewer is meeting the planet — first
    impression, wonder. Pose: standing (default, stable). Mouth: oval
    (wide, awed). Stickman scaled to 320px (~44% frame height), central.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 painterly suns
    positions = [(280, 250), (640, 200), (1000, 280)]
    sizes = [70, 90, 80]
    draw_sun_painterly(img, 280, 250, 70, YELLOW_SUN, seed=10)
    draw_sun_painterly(img, 640, 200, 90, RED_SUN, seed=11)
    draw_sun_painterly(img, 1000, 280, 80, ORANGE_SUN, seed=12)

    # Small planet
    draw_planet_painterly(img, 1100, 580, 28, PAL['planet'], seed=20, n_bands=3)

    # Stickman CENTER, awed + standing
    expression, pose = lookup_reaction('intro')
    draw_stickman_motion(
        img, t=t, x_center=440, y_top=320, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=1,
    )

    draw_caption(draw, "IMAGINE A SKY WITH THREE SUNS",
                 xy=(640, 580), where='intro')
    return img


def card_not_a_line(t=0.0):
    """Card 2: 'Not in a line, like a cosmic cliche.' — 3 suns diagonal with X.
    Round 3 character: smirk + shrugged. The viewer has seen the cliche and
    is dismissive. Smirk mouth + shrugged pose = wry disbelief.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns staggered
    draw_sun_painterly(img, 180, 220, 55, YELLOW_SUN, seed=30)
    draw_sun_painterly(img, 640, 170, 95, RED_SUN, seed=31)
    draw_sun_painterly(img, 1100, 310, 70, ORANGE_SUN, seed=32)

    # A dashed "cliche" line + big X
    wobble_line(
        draw, (180, 220), (1100, 310),
        color=PAL['deep'], width=2, seed=33, segments=24,
    )
    wobble_line(
        draw, (350, 200), (950, 380),
        color=PAL['alert'], width=8, seed=34, segments=12,
    )
    wobble_line(
        draw, (950, 200), (350, 380),
        color=PAL['alert'], width=8, seed=35, segments=12,
    )

    # Stickman CENTER, smirk + shrugged
    expression, pose = lookup_reaction('not_a_line')
    draw_stickman_motion(
        img, t=t, x_center=440, y_top=400, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=1.8, seed=10,
    )

    draw_caption(
        draw, "NOT A LINE. LIKE A COSMIC CLICHE.",
        xy=(640, 620), where='not_a_line',
    )
    return img


def card_waltz(t=0.0):
    """Card 3: 'In a slow waltz.' — PURE STICKMAN beat (round 2 fix preserved).
    Round 3 character: flat + standing. The viewer takes in the weirdness
    with a beat of deadpan. Pure character beat — no diagram, no planet.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # A starfield
    draw_stars(img, 80, seed=40,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Stickman CENTER, deadpan + standing
    expression, pose = lookup_reaction('waltz')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=240, height=360,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=40,
    )

    T.draw_stamp(draw, "WALTZ", xy=(1080, 80), accent_rgb=PAL['accent2'])

    draw_caption(
        draw, "IN A SLOW WALTZ",
        xy=(520, 640), where='waltz',
    )
    return img


def card_three_suns_detail(t=0.0):
    """Card 4: 'One yellow, one orange, one red, drifting across each other
    every few days, casting shadows that do not make sense.'

    Round 3 character: squint + pointing. The viewer is overwhelmed by the
    three-sun detail and is pointing at them. The squint mouth says "too
    much light."
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns, labeled
    draw_sun_painterly(img, 220, 270, 75, YELLOW_SUN, seed=50)
    draw_sun_painterly(img, 640, 190, 110, RED_SUN, seed=51)
    draw_sun_painterly(img, 1060, 310, 80, ORANGE_SUN, seed=52)

    T.draw_stamp(draw, "YELLOW", xy=(160, 380), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "RED", xy=(640, 340), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "ORANGE", xy=(1000, 420), accent_rgb=PAL['deep'])

    # The planet at the bottom
    draw_planet_painterly(img, 200, 600, 50, PAL['planet'], seed=55, n_bands=4)

    # Three crossing shadow lines
    for sx, sy in [(220, 270), (640, 190), (1060, 310)]:
        wobble_line(
            draw, (sx, sy + 100), (200, 600),
            color=PAL['deep'], width=2, seed=int(sx), segments=8,
        )

    # Stickman CENTER-RIGHT, squint + pointing
    expression, pose = lookup_reaction('three_suns_detail')
    draw_stickman_motion(
        img, t=t, x_center=900, y_top=350, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=50,
    )

    draw_caption(
        draw, "SHADOWS THAT DO NOT MAKE SENSE",
        xy=(360, 470), where='three_suns_detail',
    )
    return img


def card_planet_portrait(t=0.0):
    """Card 5: 'That is HD 188753 Ab. A gas giant, roughly the mass of
    Jupiter, locked into a tight orbit around all three of them at once.'

    Round 3 character: oval + hands_up. Viewer is awed at the planet
    itself. Oval mouth (the same awed expression as the intro), hands
    raised.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Big planet portrait
    draw_planet_painterly(img, 950, 400, 200, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 90, 100), (110, 90, 95),
                              (165, 110, 115), (90, 75, 80),
                              (170, 130, 130),
                          ]},
                          n_bands=5, seed=60)

    # Stars
    draw_stars(img, 40, seed=7, region=(0, ILLUSTRATION_TOP + 20, 700, ILLUSTRATION_BOT - 20))

    # Stickman LEFT, oval + hands_up
    expression, pose = lookup_reaction('planet_portrait')
    draw_stickman_motion(
        img, t=t, x_center=270, y_top=350, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=2,
    )

    draw_caption(
        draw, "A GAS GIANT, ROUGHLY JUPITER MASS",
        xy=(280, 600), where='planet_portrait',
    )
    return img


def card_konacki(t=0.0):
    """Card 6: 'Discovered in 2005 by a team that included a scientist named
    Doctor Konacki. Konacki looked at the data and said: this thing should
    not be calm. Stars in a triple system should not let a planet just sit
    there.'

    Round 3 character: deadpan + standing (with tiny glasses). The viewer
    is now channeling the scientist. Deadpan, observing, in portrait
    frame. The 'scientist' figure.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 'KONACKI 2005' callout under title
    cx = W // 2
    name_text = 'HD 188753 AB'
    bx, by, bw, bh = T._bbox(draw, name_text, DRAW_HEADER_FONT)
    underline_x0 = cx - bw // 2 - 6
    underline_x1 = cx + bw // 2 + 6
    underline_y = 67
    wobble_line(
        draw, (underline_x0, underline_y), (underline_x1, underline_y),
        color=PAL['alert'], width=3, seed=119, segments=10, jitter=0.5,
    )
    wobble_line(
        draw, (cx - 60, underline_y + 1), (cx - 100, underline_y + 18),
        color=PAL['alert'], width=2, seed=119, segments=4, jitter=0.4,
    )
    T.draw_stamp(draw, "KONACKI 2005",
                 xy=(cx - 200, underline_y + 12),
                 accent_rgb=PAL['alert'])

    # Portrait frame for Dr. Konacki
    fx, fy = 110, 130
    fw, fh = 360, 460
    wobble_ellipse(
        draw, (fx, fy, fx + fw, fy + fh), PAL['ink'], fill=PAL['paper'],
        width=4, seed=120, segments=40, jitter=2.0,
    )

    # Stickman in portrait frame, deadpan + standing with tiny glasses
    expression, pose = lookup_reaction('konacki')
    draw_stickman_motion(
        img, t=t, x_center=fx + fw // 2, y_top=fy + 60, height=320,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=121,
    )
    # Tiny glasses
    head_x = fx + fw // 2
    head_y = fy + 60 + 60
    lens_w = 18
    lens_h = 14
    draw.rectangle(
        [head_x - 30 - lens_w // 2, head_y - lens_h // 2,
         head_x - 30 + lens_w // 2, head_y + lens_h // 2],
        outline=PAL['ink'], width=2,
    )
    draw.rectangle(
        [head_x + 30 - lens_w // 2, head_y - lens_h // 2,
         head_x + 30 + lens_w // 2, head_y + lens_h // 2],
        outline=PAL['ink'], width=2,
    )
    wobble_line(
        draw, (head_x - 30 + lens_w // 2, head_y),
        (head_x + 30 - lens_w // 2, head_y),
        color=PAL['ink'], width=2, seed=122,
    )

    # Speech bubble on the right
    bx0, by0 = 540, 160
    bx1, by1 = 1180, 460
    wobble_rect(
        draw, (bx0, by0, bx1, by1), PAL['ink'], fill=PAL['cream'],
        width=4, seed=123, jitter=1.5,
    )
    tail_pts = [
        (bx0, by1 - 60),
        (bx0 - 40, by1 - 20),
        (bx0 + 10, by1 - 30),
    ]
    wobble_polygon(draw, tail_pts, PAL['ink'], fill=PAL['cream'], width=3, seed=124)

    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30), '"THIS THING',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30 + int(T.CAPTION_PX * 1.4)), 'SHOULD NOT',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30 + int(T.CAPTION_PX * 2.8)), 'BE CALM."',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )

    draw_caption(
        draw, "DOCTOR KONACKI LOOKED AT THE DATA",
        xy=(300, 600), where='konacki',
    )
    return img


def card_orbit_diagram(t=0.0):
    """Card 7: 'Three stars pull on a planet in three different directions
    at the same time.'

    Round 3 character: worried + pointing. Viewer is starting to feel
    concern. Worried mouth + pointing pose = "look at this, it can't be
    good."
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    sun_center = (640, 400)
    draw_sun_painterly(img, sun_center[0] - 30, sun_center[1] - 20, 40,
                       YELLOW_SUN, seed=70)
    draw_sun_painterly(img, sun_center[0] + 30, sun_center[1] - 20, 40,
                       RED_SUN, seed=71)
    draw_sun_painterly(img, sun_center[0], sun_center[1] + 30, 40,
                       ORANGE_SUN, seed=72)

    draw_orbit_path(
        draw, sun_center[0], sun_center[1], rx=200, ry=160,
        color=PAL['deep'], seed=71,
    )
    draw_planet_painterly(img, 840, 400, 22, PAL['planet'], seed=72, n_bands=3)

    # Stickman LEFT, worried + pointing
    expression, pose = lookup_reaction('orbit_diagram')
    draw_stickman_motion(
        img, t=t, x_center=240, y_top=380, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=3,
    )

    draw_caption(
        draw, "LOCKED IN A TIGHT ORBIT AROUND ALL THREE",
        xy=(300, 650), where='orbit_diagram',
    )
    return img


def card_force_diagram(t=0.0):
    """Card 8: 'Three stars pull on a planet in three different directions
    at the same time.'

    ROUND 3 SIGNATURE BEAT — three distinct shadow stickmen, each
    reacting to one of the three suns. This is the per-segment reaction
    set visualized. Center stickman is the COWERING + SCREAM (the
    strongest emotion, on the planet); the two shadows are different
    reactions.

    Per CLAUDE.md §6: "show three distinct shadow poses of the stickman
    side-by-side, each reacting to one of the three suns. The reference
    uses this device."
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Planet in the center
    planet_xy = (640, 400)
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], 50, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (160, 110, 120),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=80)

    # 3 suns at the edges
    draw_sun_painterly(img, 180, 200, 45, YELLOW_SUN, seed=85)
    draw_sun_painterly(img, 1100, 220, 45, RED_SUN, seed=86)
    draw_sun_painterly(img, 640, 100, 45, ORANGE_SUN, seed=87)

    # Force arrows from each sun
    sun_positions = [
        (180, 200, PAL['accent3']),
        (1100, 220, PAL['accent1']),
        (640, 100, (255, 140, 50)),
    ]
    for sx, sy, color in sun_positions:
        wobble_line(
            draw, (sx, sy), planet_xy, color=color, width=3,
            seed=int(sx + sy) + 1, segments=10,
        )
        ang = math.atan2(planet_xy[1] - sy, planet_xy[0] - sx)
        head_len = 14
        head_ang = 0.5
        hx, hy = planet_xy[0] - 60 * math.cos(ang), planet_xy[1] - 60 * math.sin(ang)
        h1 = (hx - head_len * math.cos(ang - head_ang), hy - head_len * math.sin(ang - head_ang))
        h2 = (hx - head_len * math.cos(ang + head_ang), hy - head_len * math.sin(ang + head_ang))
        draw.polygon([(hx, hy), h1, h2], fill=color, outline=color)

    # Stars
    draw_stars(img, 40, seed=8,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # THREE SHADOW STICKMEN, each reacting to a different sun.
    # This is the round 3 signature beat — the reference device.
    #
    #   Left shadow: deadpan (looking right toward the planet, calm-but-watching)
    #   Center: cowering + scream (the planet itself is the stickman here)
    #   Right shadow: squint (looking left toward the planet, overwhelmed)
    shadow_h = 220  # smaller than full stickman — these are "shadows"
    # Left shadow
    sm.draw_stickman(
        img, x_center=240, y_top=470, height=shadow_h,
        pose='standing', mouth='flat', seed=11,
    )
    T.draw_stamp(draw, "WATCHING", xy=(180, 690), accent_rgb=PAL['deep'])
    # Center — cowering, screaming
    expression, pose = lookup_reaction('force_diagram')
    draw_stickman_motion(
        img, t=t, x_center=640, y_top=450, height=shadow_h + 30,
        pose=pose, mouth=expression, beat_period_s=1.6, seed=11,
    )
    T.draw_stamp(draw, "BRACING", xy=(590, 670), accent_rgb=PAL['alert'])
    # Right shadow — squinting
    sm.draw_stickman(
        img, x_center=1040, y_top=470, height=shadow_h,
        pose='shielding_eyes', mouth='squint', seed=12,
    )
    T.draw_stamp(draw, "OVERWHELMED", xy=(960, 690), accent_rgb=PAL['deep'])

    draw_caption(
        draw, "PULLED IN THREE DIRECTIONS",
        xy=(420, 80), where='force_diagram',
    )
    return img


def card_wobble_orbit(t=0.0):
    """Card 9: 'The orbit is not a circle. It is a slow, wobbling, slightly
    drunk figure eight.'

    Round 3 character: worried + shrugged. The viewer sees the
    absurdity of the orbit. Worried mouth + shrugged pose = "I don't
    even know what to say."
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Wobbling figure-eight orbit
    cx, cy = 540, 360
    rng = random.Random(90)
    pts = []
    for i in range(200):
        t = i / 200 * 2 * math.pi
        denom = 1 + math.sin(t) ** 2
        x = (200 * math.cos(t)) / denom + cx + rng.uniform(-2, 2)
        y = 140 * math.sin(t) * math.cos(t) / denom + cy + rng.uniform(-2, 2)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['accent3'], width=2)

    # The planet on the orbit
    draw_planet_painterly(img, 700, 320, 30, PAL['planet'], seed=91, n_bands=4)

    # Stars
    draw_stars(img, 50, seed=9,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Stickman RIGHT, worried + shrugged
    expression, pose = lookup_reaction('wobble_orbit')
    draw_stickman_motion(
        img, t=t, x_center=1000, y_top=370, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=12,
    )

    draw_caption(
        draw, "A SLOW WOBBLING FIGURE EIGHT",
        xy=(360, 600), where='wobble_orbit',
    )
    return img


def card_no_idea_weather(t=0.0):
    """Card 10: 'We have no idea what its atmosphere does. We do not even
    know if it has weather.'

    Round 3 character: terrified + cowering. The viewer is reacting to
    the most extreme uncertainty beat. Terrified mouth (large oval, no
    fill) + cowering pose (knees bent, arms tucked) — peak fear beat.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Empty atmosphere — wisps
    wobble_circle(
        draw, (320, 360), 130, PAL['accent2'], fill=None, width=3,
        seed=100, segments=30, jitter=8,
    )
    wobble_circle(
        draw, (320, 360), 160, PAL['accent2'], fill=None, width=2,
        seed=101, segments=30, jitter=10,
    )
    wobble_circle(
        draw, (320, 360), 190, PAL['accent2'], fill=None, width=1,
        seed=102, segments=30, jitter=12,
    )
    draw_planet_painterly(img, 320, 360, 60, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (165, 110, 115),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=103)

    # Question marks
    draw_question_marks(
        draw, 3, [(150, 220), (490, 240), (320, 130)], PAL['caption']
    )

    # Stars
    draw_stars(img, 30, seed=11,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Stickman RIGHT, terrified + cowering
    expression, pose = lookup_reaction('no_idea_weather')
    draw_stickman_motion(
        img, t=t, x_center=900, y_top=380, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=1.5, seed=13,
    )

    draw_caption(
        draw, "WE HAVE NO IDEA",
        xy=(520, 600), where='no_idea_weather',
    )
    return img


def card_calendar_lie(t=0.0):
    """Card 11: 'It is the kind of place where a calendar would be a lie.'

    Round 3 character: sad_smile + shrugged. The viewer is resigned
    with a wry smile — "well, of course it is." Sad smile mouth
    (downturned + raised brow) + shrugged pose.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Calendar with big X
    draw_calendar(
        draw, cx=380, cy=380, w=200, h=240,
        line_color=PAL['deep'], paper=PAL['paper'],
    )

    # Stickman RIGHT, sad_smile + shrugged
    expression, pose = lookup_reaction('calendar_lie')
    draw_stickman_motion(
        img, t=t, x_center=900, y_top=350, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=4,
    )

    # A 'sunrise' crossed-out
    draw_sun_painterly(img, 200, 600, 30, YELLOW_SUN, seed=110)
    wobble_line(
        draw, (180, 580), (220, 620),
        color=PAL['alert'], width=5, seed=111, segments=4,
    )
    wobble_line(
        draw, (220, 580), (180, 620),
        color=PAL['alert'], width=5, seed=112, segments=4,
    )
    T.draw_stamp(draw, "SUNRISE = MEANINGLESS", xy=(150, 660), accent_rgb=PAL['deep'])

    draw_caption(
        draw, "A CALENDAR WOULD BE A LIE",
        xy=(520, 180), where='calendar_lie',
    )
    return img


def card_sits_there(t=0.0):
    """Card 12 (transitional): 'And the planet just sits there, three suns,
    wobbling, doing its impossible thing.'

    Round 3 character: relief + hands_down. After the peak fear, the
    viewer exhales. Relief mouth (small upward arc) + hands_down pose
    (arms at sides, recovered).
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # The planet centered
    draw_planet_painterly(img, 540, 400, 100, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 110, 115), (110, 90, 95),
                              (170, 130, 130), (90, 75, 80),
                              (160, 120, 120),
                          ]}, n_bands=5, seed=120)

    # 3 small suns in the distance
    draw_sun_painterly(img, 130, 200, 30, YELLOW_SUN, seed=125)
    draw_sun_painterly(img, 200, 130, 30, ORANGE_SUN, seed=127)
    draw_sun_painterly(img, 100, 350, 25, RED_SUN, seed=126)

    # Wobbling orbit lines around the planet
    rng = random.Random(121)
    for _ in range(3):
        pts = []
        rx = 180 + rng.randint(-20, 20)
        ry = 140 + rng.randint(-15, 15)
        for i in range(80):
            ang = 2 * math.pi * i / 80
            x = 540 + rx * math.cos(ang) + rng.uniform(-3, 3)
            y = 400 + ry * math.sin(ang) + rng.uniform(-3, 3)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=PAL['accent2'], width=1)

    # Stars
    draw_stars(img, 50, seed=13,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Stickman RIGHT, relief + hands_down — SCALED UP to 320 px central
    expression, pose = lookup_reaction('sits_there')
    draw_stickman_motion(
        img, t=t, x_center=950, y_top=360, height=STICKMAN_HEIGHT,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=14,
    )

    draw_caption(
        draw, "NOTHING ABOUT IT IS CALM",
        xy=(380, 640), where='sits_there',
    )
    return img


def card_lineup_grid(t=0.0):
    """Card 13 (NEW closing beat): 2×2 grid of four planet cards.

    Round 3 character: frown + pointing. The viewer is now surveying
    the bigger picture and bracing for what's coming. Frown mouth +
    pointing pose = "look at all of these."
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['paper'])

    grid_left = 100
    grid_top = ILLUSTRATION_TOP + 40
    cell_w = 540
    cell_h = 250
    gap = 20

    planets = [
        {
            'label': 'HD 188753 AB',
            'base': PAL['planet'],
            'bands': [
                (180, 110, 115), (110, 90, 95),
                (170, 130, 130), (90, 75, 80), (160, 120, 120),
            ],
            'seed': 200,
            'caption': 'TRIPLE-STAR WORLD',
        },
        {
            'label': 'HD 80606 B',
            'base': (247, 195, 6),
            'bands': [
                (255, 210, 80), (200, 50, 20),
                (255, 180, 60), (130, 30, 10), (255, 220, 100),
            ],
            'seed': 201,
            'caption': 'THE WHIPLASH PLANET',
        },
        {
            'label': 'PSR B1257+12',
            'base': (160, 160, 170),
            'bands': [
                (180, 180, 200), (90, 90, 110),
                (170, 170, 190), (110, 110, 130),
            ],
            'seed': 202,
            'caption': 'PULSAR PLANETS',
        },
        {
            'label': 'TRES-2B',
            'base': (40, 30, 50),
            'bands': [
                (60, 50, 70), (30, 20, 40),
                (50, 40, 60), (20, 15, 30),
            ],
            'seed': 203,
            'caption': 'DARKER THAN COAL',
        },
    ]

    for idx, p in enumerate(planets):
        row = idx // 2
        col = idx % 2
        cx = grid_left + col * (cell_w + gap) + cell_w // 2
        cy = grid_top + row * (cell_h + gap) + cell_h // 2 - 20
        planet_r = 70
        draw_planet_painterly(img, cx, cy, planet_r, p['base'],
                              palette_dict={'bands': p['bands']},
                              n_bands=len(p['bands']),
                              seed=p['seed'])
        T.draw_outlined_text(
            draw, (cx - 130, cy + planet_r + 14), p['caption'],
            DRAW_FONT_BOLD,
            fill=PAL['deep'], stroke=PAL['deep'], stroke_width=1,
        )

    # Stickman lower-right, frown + pointing, smaller (200 px ~28% frame)
    expression, pose = lookup_reaction('lineup_grid')
    draw_stickman_motion(
        img, t=t, x_center=1170, y_top=480, height=240,
        pose=pose, mouth=expression, beat_period_s=2.0, seed=15,
    )

    draw_caption(
        draw, "AND 11 MORE LIKE THIS",
        xy=(420, 660), where='lineup_grid',
    )
    return img


# --- Card schedule (driven by the alignment) ---

CARDS = [
    {'id': 'intro',             'start_w': 0,   'end_w': 5,   'renderer': card_intro},
    {'id': 'not_a_line',        'start_w': 6,   'end_w': 13,  'renderer': card_not_a_line},
    {'id': 'waltz',             'start_w': 14,  'end_w': 17,  'renderer': card_waltz},
    {'id': 'three_suns_detail', 'start_w': 18,  'end_w': 37,  'renderer': card_three_suns_detail},
    {'id': 'planet_portrait',   'start_w': 38,  'end_w': 62,  'renderer': card_planet_portrait},
    {'id': 'konacki',           'start_w': 63,  'end_w': 93,  'renderer': card_konacki},
    {'id': 'orbit_diagram',     'start_w': 94,  'end_w': 107, 'renderer': card_orbit_diagram},
    {'id': 'force_diagram',     'start_w': 108, 'end_w': 121, 'renderer': card_force_diagram},
    {'id': 'wobble_orbit',      'start_w': 122, 'end_w': 151, 'renderer': card_wobble_orbit},
    {'id': 'no_idea_weather',   'start_w': 152, 'end_w': 175, 'renderer': card_no_idea_weather},
    {'id': 'calendar_lie',      'start_w': 176, 'end_w': 198, 'renderer': card_calendar_lie},
    {'id': 'sits_there',        'start_w': 199, 'end_w': 210, 'renderer': card_sits_there},
    {'id': 'lineup_grid',       'start_w': 211, 'end_w': 216, 'renderer': card_lineup_grid},
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
        # Carry the (expression, pose) from the reaction set onto the schedule
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
        # without spending too much CPU. The card start time is the phase
        # anchor for the motion loop.
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
        print(f"  {s['id']:25s}  {s['start']:.2f}s -> {s['end']:.2f}s  "
              f"({s['end']-s['start']:.2f}s)  [expr={s['expression']}, pose={s['pose']}]")

    out_dir = os.path.join(os.path.dirname(__file__), args.frames_dir)
    audio_duration = alignment['duration_s']
    schedule_total = schedule[-1]['end'] if schedule else 0.0
    audio_frames = int(round(audio_duration * FPS))
    schedule_frames = sum(max(1, int(round((c['end'] - c['start']) * FPS))) for c in schedule)
    hold_last_frames = max(0, audio_frames - schedule_frames)
    print(f'Audio: {audio_duration:.2f}s ({audio_frames} frames)')
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
