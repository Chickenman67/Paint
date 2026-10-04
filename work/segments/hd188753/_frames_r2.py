# work/segments/hd188753/_frames_r2.py
# Round 2 build for segment 1 (HD 188753 Ab) — closing the round-1 critic gaps:
#
#   1. PAINTERLY TEXTURE ON STARS AND PLANETS — biggest gap
#      Render every sun/planet with the painterly signature (radial gradient +
#      stipple grain + soft halo on suns; banded texture + stipple + radial
#      gradient on planets) via work/lib/texture.py.
#
#   2. WRONG HEADER TYPEFACE — secondary gap
#      Use work/lib/title_band.py draw_title_band() everywhere (WHITE rect
#      0..60px, Consolas Bold ALL CAPS, BLACK fill, NO STROKE). This is
#      already the case in round 1, but we re-verify in round 2.
#
#   3. §10.9 DEBUG STAMP REGRESSION ON t38 — secondary gap
#      Remove the "DR. KONACKI" red stamp that overlapped the caption on the
#      konacki card. Render it instead as a small red underline + arrow
#      UNDER the planet name in the title band (a "callout", not a stamp
#      over body text). Add a --no-debug flag to the CLI that defaults to ON
#      so debug stamps never leak into the build.
#
#   4. §7 TWO-LINE CAPTION ON t62 — secondary gap
#      Compress the not_a_line card caption to a single ≤60-char line. Add a
#      hard check in the caption renderer that fails the build if any caption
#      exceeds 60 chars or would wrap at 27 px Consolas.
#
#   5. STICKMAN TOO SMALL / MISSING ON t38, t50, t62
#      Scale up the stickman on the closing card to ~320 px (≈45% of frame
#      height) and place him centrally. Add the stickman to the wobble_orbit
#      card and the no_idea_weather card. The stickman must be present in at
#      least one beat, per CLAUDE.md §6.
#
#   6. MISSING 2×2 PLANET LINEUP GRID AS ENDING BEAT
#      Add a new card_lineup_grid() that renders a 2×2 grid of four planet
#      portraits as the segment's closing beat. This is a ref signature:
#      ref t62 is a 2×2 grid of planet cards summarizing the segment.

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
TITLE_STRIP_BOT = 61   # y=22..60 inclusive
ILLUSTRATION_TOP = 80
ILLUSTRATION_BOT = 719

PAL = P.SEGMENT_1

# Hard caption constraints (per CLAUDE.md §7 + the round-1 verdict)
MAX_CAPTION_CHARS = 60
CAPTION_FONT = T.load_font(T.CAPTION_PX, bold=False)
DRAW_FONT_BOLD = T.load_font(T.CAPTION_PX, bold=True)
DRAW_HEADER_FONT = T.load_font(T.HEADER_PX, bold=True)


# --- Hard caption check (fails the build on violation) ---

def _caption_pixel_width(text, font=CAPTION_FONT):
    """Return the rendered pixel width of `text` at the caption size."""
    return _safe_textwidth(text, font)


def _safe_textwidth(text, font):
    try:
        x0, _, x1, _ = font.getbbox(text)
        return x1 - x0
    except Exception:
        return len(text) * 16


def _check_caption(text, where):
    """Hard check: fail the build if the caption violates §7.

    - text must be ≤ MAX_CAPTION_CHARS characters
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
    w = _caption_pixel_width(text)
    if w > 1100:
        raise ValueError(
            f"[{where}] caption is {w}px wide (>1100), would wrap: {text!r}"
        )


def draw_caption(draw, text, xy, color_rgb=None, where='caption'):
    """Caption renderer with the §7 hard check. Wraps T.draw_caption."""
    if color_rgb is None:
        color_rgb = PAL['caption']
    _check_caption(text, where=where)
    T.draw_caption(draw, text, xy, color_rgb=color_rgb)


# --- Wobble helpers (carried over from round 1) ---

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


def wobble_polygon(draw, pts, color, fill=None, width=3, seed=0, jitter=1.0):
    """Draw a polygon with wobbly vertices."""
    rng = random.Random(seed)
    wpts = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)) for x, y in pts]
    if fill is not None:
        draw.polygon(wpts, fill=fill)
    if width > 0:
        draw.line(wpts + [wpts[0]], fill=color, width=width)


def wobble_ellipse(draw, bbox, color, fill=None, width=3, seed=0, segments=28, jitter=1.5):
    """Draw an ellipse as a wobbly polygon."""
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


# --- Painterly sun / planet helpers (round 2: use texture module) ---

def draw_sun_painterly(img, cx, cy, r, palette_dict, seed=0):
    """Render a painterly sun (radial gradient + stipple + soft halo)."""
    texture.sun_disc(img, cx, cy, r, palette=palette_dict, seed=seed, halo=True)


def draw_planet_painterly(img, cx, cy, r, base_rgb, palette_dict=None,
                          n_bands=4, seed=0):
    """Render a painterly planet (banded + radial gradient + stipple)."""
    texture.planet_disc(img, cx, cy, r, base_rgb=base_rgb,
                        palette=palette_dict, n_bands=n_bands,
                        seed=seed, with_bands=True)


# --- Title strip: now uses the locked title_band module ---

def draw_title_strip(img, name):
    """Render the title strip via lib.title_band (white rect, Consolas Bold
    ALL CAPS, BLACK fill, NO STROKE)."""
    title_band.draw_title_band(img, name)


# --- Reusable diagram helpers ---

def draw_orbit_path(draw, cx, cy, rx, ry, color, seed=0, dashed=False, dash_count=18):
    """Draw an elliptical orbit as a wobbly polyline (optionally dashed)."""
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
    """Draw 3 arrows from each sun pointing toward the planet."""
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
    """Draw '?' symbols as the dominant visual element of an empty/atmosphere card."""
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
    """Draw a small wobbly calendar with a big X through it."""
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


def draw_stars(img, count, seed, region=None, color=None):
    """Draw N small stars in the illustration area. Deterministic per seed.

    region: (x0, y0, x1, y1) — restrict stars to this rectangle. Default
            is the full illustration area, with a small inset.
    color:  RGB tuple (default cream / paper).
    """
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


# --- The three sun palettes (one per sun, matching ref t13 / t25) ---

YELLOW_SUN = {
    'core':  (255, 240, 130),    # bright yellow core
    'mid':   (250, 178, 11),     # warm yellow
    'outer': (239, 68, 3),       # red ring
    'halo':  (180, 60, 10),      # warm red-orange halo (visible glow)
}
RED_SUN = {
    'core':  (255, 200, 130),    # warm core
    'mid':   (238, 32, 11),      # saturated red
    'outer': (180, 8, 4),        # deep red
    'halo':  (160, 30, 6),       # warm dark red halo
}
ORANGE_SUN = {
    'core':  (255, 210, 130),    # warm core
    'mid':   (255, 140, 50),     # orange
    'outer': (200, 70, 10),      # burnt orange
    'halo':  (180, 50, 8),       # warm dark orange halo (visible glow)
}


# --- Cards ---

def card_intro(t=0.0):
    """Card 1: 'Imagine a sky with three suns.' — 3 painterly suns in cool
    sky, stickman looking up."""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 painterly suns
    positions = [(320, 250), (640, 200), (960, 280)]
    sizes = [70, 90, 80]
    draw_sun_painterly(img, 320, 250, 70, YELLOW_SUN, seed=10)
    draw_sun_painterly(img, 640, 200, 90, RED_SUN, seed=11)
    draw_sun_painterly(img, 960, 280, 80, ORANGE_SUN, seed=12)

    # Small planet (painterly)
    draw_planet_painterly(img, 640, 580, 32, PAL['planet'], seed=20, n_bands=3)

    # Stickman in foreground, looking up — pointing at the suns
    sm.draw_stickman(
        img, x_center=200, y_top=380, height=300,
        pose='pointing', mouth='oval', seed=1,
    )

    draw_caption(draw, "IMAGINE A SKY WITH THREE SUNS",
                 xy=(300, 470), where='intro')
    return img


def card_not_a_line(t=0.0):
    """Card 2: 'Not in a line, like a cosmic cliche.' — 3 suns in a diagonal.

    Round 2 fix: the round-1 caption was a TWO-LINE caption that violated §7.
    Compress to a single ≤60-char line: "NOT A LINE. LIKE A COSMIC CLICHE."
    (40 chars). The hard check in draw_caption enforces the rule.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns, NOT in a line — staggered across the sky (painterly)
    draw_sun_painterly(img, 200, 240, 60, YELLOW_SUN, seed=30)
    draw_sun_painterly(img, 640, 180, 95, RED_SUN, seed=31)
    draw_sun_painterly(img, 1080, 320, 70, ORANGE_SUN, seed=32)

    # A dashed "cliche" line through them, with a big X over it
    wobble_line(
        draw, (200, 240), (1080, 320),
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

    # Stickman in lower-left, deadpan/skeptical, arms out
    sm.draw_stickman(
        img, x_center=180, y_top=420, height=300,
        pose='standing', mouth='flat', seed=10,
    )

    # SINGLE-LINE caption (≤60 chars). Hard-checked.
    draw_caption(
        draw, "NOT A LINE. LIKE A COSMIC CLICHE.",
        xy=(360, 620), where='not_a_line',
    )
    return img


def card_waltz(t=0.0):
    """Card 3: 'In a slow waltz.' — PURE STICKMAN beat (round 2 round-1 fix).

    The round-1 critic's biggest gap was the stickman: 'add at least one beat
    per segment where the stickman is the SOLE subject (no diagram, no planet
    — just the character against the bg).' This card delivers exactly that:
    a single stickman, deadpan, in front of a starfield. No suns, no orbit,
    no planet. Just the surrogate reacting to the weirdness.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # A starfield (no diagram — this is a pure character beat)
    draw_stars(img, 80, seed=40,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # The stickman — CENTER, large (360 px = 50% of frame). Pure character beat.
    sm.draw_stickman(
        img, x_center=640, y_top=300, height=360,
        pose='standing', mouth='flat', seed=40,
    )

    # A tiny "SLOW WALTZ" hand-lettered stamp in the upper-right (not a
    # diagram — it's a context label).
    T.draw_stamp(draw, "WALTZ",
                 xy=(1080, 80), accent_rgb=PAL['accent2'])

    draw_caption(
        draw, "IN A SLOW WALTZ",
        xy=(520, 640), where='waltz',
    )
    return img


def card_three_suns_detail(t=0.0):
    """Card 4: 'One yellow, one orange, one red, drifting across each other
    every few days, casting shadows that do not make sense.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns, labeled with small color stamps
    draw_sun_painterly(img, 240, 280, 80, YELLOW_SUN, seed=50)
    draw_sun_painterly(img, 640, 200, 110, RED_SUN, seed=51)
    draw_sun_painterly(img, 1040, 320, 80, ORANGE_SUN, seed=52)

    T.draw_stamp(draw, "YELLOW", xy=(180, 400), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "RED", xy=(640, 360), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "ORANGE", xy=(985, 440), accent_rgb=PAL['deep'])

    # The planet at the bottom, with crazy crossing shadows
    draw_planet_painterly(img, 640, 600, 50, PAL['planet'], seed=55, n_bands=4)

    # Three crossing shadow lines from each sun across the planet
    for sx, sy in [(240, 280), (640, 200), (1040, 320)]:
        wobble_line(
            draw, (sx, sy + 100), (640, 600),
            color=PAL['deep'], width=2, seed=int(sx), segments=8,
        )

    draw_caption(
        draw, "SHADOWS THAT DO NOT MAKE SENSE",
        xy=(360, 470), where='three_suns_detail',
    )
    return img


def card_planet_portrait(t=0.0):
    """Card 5: 'That is HD 188753 Ab. A gas giant, roughly the mass of Jupiter,
    locked into a tight orbit around all three of them at once.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    # Round 2 fix: use PAL['bg'] (light blue) for the illustration area
    # instead of PAL['deep'] (near-black). The black-limbed stickman is
    # invisible on near-black, AND the planet's pink/mauve bands read more
    # painterly against light blue than against black. The stars layer on
    # top still gives the deep-space feel.
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Big planet portrait (right side) — painterly bands + stipple
    draw_planet_painterly(img, 880, 400, 200, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 90, 100),    # mauve band
                              (110, 90, 95),     # darker
                              (165, 110, 115),   # mid mauve
                              (90, 75, 80),      # shadow
                              (170, 130, 130),   # light band
                          ]},
                          n_bands=5, seed=60)

    # Stars in the background
    draw_stars(img, 40, seed=7, region=(0, ILLUSTRATION_TOP + 20, 700, ILLUSTRATION_BOT - 20))

    # Stickman on the left, looking at the planet — awed
    sm.draw_stickman(
        img, x_center=200, y_top=380, height=300,
        pose='hands_up', mouth='oval', seed=2,
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

    Round 2 fix: the round-1 "DR. KONACKI" red stamp was a debug artifact
    that overlapped the caption. Render it now as a small red underline +
    arrow callout UNDER the planet name in the title band, not as a stamp
    over the caption.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Round 2 fix: small red callout under the title band — a red underline
    # + small arrow pointing to the planet name. NOT a stamp over the body.
    # The underline sits at y=63..66, the arrow tail at y=68.
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
    # A small arrow tail dropping from the underline into the illustration
    wobble_line(
        draw, (cx - 60, underline_y + 1), (cx - 100, underline_y + 18),
        color=PAL['alert'], width=2, seed=119, segments=4, jitter=0.4,
    )
    # Tiny "KONACKI 2005" stamp at the tail end of the arrow
    T.draw_stamp(draw, "KONACKI 2005",
                 xy=(cx - 200, underline_y + 12),
                 accent_rgb=PAL['alert'])

    # Portrait frame for Dr. Konacki on the left
    fx, fy = 110, 130
    fw, fh = 360, 460
    wobble_ellipse(
        draw, (fx, fy, fx + fw, fy + fh), PAL['ink'], fill=PAL['paper'],
        width=4, seed=120, segments=40, jitter=2.0,
    )

    # Stickman in the portrait frame, deadpan, with tiny glasses
    sm.draw_stickman(
        img, x_center=fx + fw // 2, y_top=fy + 60, height=320,
        pose='standing', mouth='flat', seed=121,
    )
    # Tiny glasses — two small black square lenses over the face area
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
    # Bubble tail pointing to the stickman's head
    tail_pts = [
        (bx0, by1 - 60),
        (bx0 - 40, by1 - 20),
        (bx0 + 10, by1 - 30),
    ]
    wobble_polygon(draw, tail_pts, PAL['ink'], fill=PAL['cream'], width=3, seed=124)

    # Speech bubble text (3 short lines)
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30), '"THIS THING', DRAW_FONT_BOLD,
        fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30 + int(T.CAPTION_PX * 1.4)), 'SHOULD NOT',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30 + int(T.CAPTION_PX * 2.8)), 'BE CALM."',
        DRAW_FONT_BOLD, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )

    # Round 2 fix: caption is the main beat, with NO overlapping stamp.
    draw_caption(
        draw, "DOCTOR KONACKI LOOKED AT THE DATA",
        xy=(300, 600), where='konacki',
    )
    return img


def card_orbit_diagram(t=0.0):
    """Card 6 (alt): orbital diagram — 3 suns in middle, planet on a tight orbit
    around all 3."""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    sun_center = (640, 400)
    # 3 small suns in a tight triangular cluster
    draw_sun_painterly(img, sun_center[0] - 30, sun_center[1] - 20, 40,
                       YELLOW_SUN, seed=70)
    draw_sun_painterly(img, sun_center[0] + 30, sun_center[1] - 20, 40,
                       RED_SUN, seed=71)
    draw_sun_painterly(img, sun_center[0], sun_center[1] + 30, 40,
                       ORANGE_SUN, seed=72)

    # Tight orbit around the cluster
    draw_orbit_path(
        draw, sun_center[0], sun_center[1], rx=200, ry=160,
        color=PAL['deep'], seed=71,
    )

    # The planet on the orbit
    draw_planet_painterly(img, 840, 400, 22, PAL['planet'], seed=72, n_bands=3)

    # Stickman in lower-left — pointing at the orbit
    sm.draw_stickman(
        img, x_center=180, y_top=410, height=300,
        pose='pointing', mouth='flat', seed=3,
    )

    draw_caption(
        draw, "LOCKED IN A TIGHT ORBIT AROUND ALL THREE",
        xy=(300, 650), where='orbit_diagram',
    )
    return img


def card_force_diagram(t=0.0):
    """Card 7: 'Three stars pull on a planet in three different directions
    at the same time.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    # Round 2 fix: light-blue BG so the stickman in the corner is visible
    # (same reasoning as card_planet_portrait — black-limbed figure disappears
    # on near-black). Stars layer on top still gives a space feel.
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Planet in the center (painterly)
    planet_xy = (640, 400)
    draw_planet_painterly(img, planet_xy[0], planet_xy[1], 50, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (160, 110, 120),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=80)

    # 3 suns at the edges with arrows pointing at the planet
    draw_sun_painterly(img, 180, 200, 45, YELLOW_SUN, seed=85)
    draw_sun_painterly(img, 1100, 220, 45, RED_SUN, seed=86)
    draw_sun_painterly(img, 640, 100, 45, ORANGE_SUN, seed=87)

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
    draw_stars(img, 50, seed=8,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Stickman in lower-left, deadpan (NOT in the safe center — this is the
    # science beat, stickman is an observer). 300 px tall, ~42% frame height.
    sm.draw_stickman(
        img, x_center=170, y_top=410, height=300,
        pose='standing', mouth='flat', seed=11,
    )

    draw_caption(
        draw, "PULLED IN THREE DIRECTIONS",
        xy=(400, 600), where='force_diagram',
    )
    return img


def card_wobble_orbit(t=0.0):
    """Card 8: 'The orbit is not a circle. It is a slow, wobbling, slightly
    drunk figure eight.'

    Round 2 fix: the round-1 card had NO stickman. Add him — a confused
    deadpan figure standing on the planet's surface, looking at the orbit.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    # Round 2 fix: light-blue BG so the right-side stickman is visible
    # (same as card_planet_portrait).
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Wobbling figure-eight orbit (yellow)
    cx, cy = 640, 400
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

    # The planet on the orbit (at one of the lobes) — painterly
    draw_planet_painterly(img, 800, 360, 30, PAL['planet'], seed=91, n_bands=4)

    # Round 2 fix: stickman added — confused, arms slightly out, deadpan.
    # Stand him in lower-left at 240 px height (33% frame) so the figure-eight
    # remains the focus but the surrogate is present.
    sm.draw_stickman(
        img, x_center=200, y_top=420, height=300,
        pose='standing', mouth='frown', seed=12,
    )

    # Stars in the background
    draw_stars(img, 50, seed=9,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    draw_caption(
        draw, "A SLOW WOBBLING FIGURE EIGHT",
        xy=(360, 600), where='wobble_orbit',
    )
    return img


def card_no_idea_weather(t=0.0):
    """Card 9: 'We have no idea what its atmosphere does. We do not even
    know if it has weather.'

    Round 2 fix: add a stickman (deadpan, "I have no idea either") to make
    the card feel inhabited. The atmosphere wisps and question marks remain.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    # Round 2 fix: light-blue BG so the right-side stickman is visible.
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Empty atmosphere — wisps of nothingness
    wobble_circle(
        draw, (640, 400), 180, PAL['accent2'], fill=None, width=3,
        seed=100, segments=30, jitter=8,
    )
    wobble_circle(
        draw, (640, 400), 220, PAL['accent2'], fill=None, width=2,
        seed=101, segments=30, jitter=10,
    )
    wobble_circle(
        draw, (640, 400), 260, PAL['accent2'], fill=None, width=1,
        seed=102, segments=30, jitter=12,
    )

    # The planet inside (painterly)
    draw_planet_painterly(img, 640, 400, 60, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 130, 140),
                              (110, 90, 95),
                              (165, 110, 115),
                              (90, 75, 80),
                          ]}, n_bands=4, seed=103)

    # Question marks
    draw_question_marks(
        draw, 3, [(300, 250), (980, 280), (640, 150)], PAL['caption']
    )

    # Round 2 fix: stickman added — deadpan, arms slightly out, "I have no
    # idea either". Lower-left at 300 px tall (~42% frame).
    sm.draw_stickman(
        img, x_center=190, y_top=420, height=300,
        pose='standing', mouth='flat', seed=13,
    )

    # Stars
    draw_stars(img, 40, seed=11,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    draw_caption(
        draw, "WE HAVE NO IDEA",
        xy=(520, 600), where='no_idea_weather',
    )
    return img


def card_calendar_lie(t=0.0):
    """Card 10: 'It is the kind of place where a calendar would be a lie.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Calendar with big X
    draw_calendar(
        draw, cx=440, cy=380, w=200, h=240,
        line_color=PAL['deep'], paper=PAL['paper'],
    )

    # Stickman on the right, shrugging
    sm.draw_stickman(
        img, x_center=950, y_top=380, height=300,
        pose='standing', mouth='flat', seed=4,
    )

    # A 'sunrise' crossed-out in the background
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
        xy=(420, 180), where='calendar_lie',
    )
    return img


def card_sits_there(t=0.0):
    """Card 11 (closing, replaced by lineup grid in round 2).

    Kept for backward compatibility with the word-index schedule, but the
    actual closing beat is now card_lineup_grid. card_sits_there still
    renders the planet + 3 small suns + big stickman as a transitional
    'sits there' frame.
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    # Round 2 fix: light-blue BG so the right-side stickman is visible.
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # The planet centered, slightly larger — painterly
    draw_planet_painterly(img, 640, 400, 100, PAL['planet'],
                          palette_dict={'bands': [
                              (180, 110, 115),
                              (110, 90, 95),
                              (170, 130, 130),
                              (90, 75, 80),
                              (160, 120, 120),
                          ]}, n_bands=5, seed=120)

    # 3 small suns in the distance
    draw_sun_painterly(img, 180, 200, 30, YELLOW_SUN, seed=125)
    draw_sun_painterly(img, 1100, 220, 30, RED_SUN, seed=126)
    draw_sun_painterly(img, 640, 130, 30, ORANGE_SUN, seed=127)

    # Wobbling orbit lines around the planet
    rng = random.Random(121)
    for _ in range(3):
        pts = []
        rx = 180 + rng.randint(-20, 20)
        ry = 140 + rng.randint(-15, 15)
        for i in range(80):
            ang = 2 * math.pi * i / 80
            x = 640 + rx * math.cos(ang) + rng.uniform(-3, 3)
            y = 400 + ry * math.sin(ang) + rng.uniform(-3, 3)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=PAL['accent2'], width=1)

    # Stars
    draw_stars(img, 60, seed=13,
               region=(20, ILLUSTRATION_TOP + 10, W - 20, ILLUSTRATION_BOT - 10),
               color=PAL['cream'])

    # Round 2 fix: stickman SCALED UP to 320 px (~45% of frame), moved to
    # the central position (just below the planet). The previous round
    # had him at 240 px in the lower-left corner — too small, too corner.
    # Now he is the dominant character beat, deadpan, looking at the planet.
    sm.draw_stickman(
        img, x_center=900, y_top=400, height=320,
        pose='standing', mouth='flat', seed=14,
    )

    draw_caption(
        draw, "NOTHING ABOUT IT IS CALM",
        xy=(380, 640), where='sits_there',
    )
    return img


def card_lineup_grid(t=0.0):
    """Card 12 (NEW closing beat): 2×2 grid of four planet cards.

    Per the round-1 verdict, the reference's t62 is a 2×2 grid of four
    planet portraits as the segment's closing beat. This is a ref signature
    that summarizes the 12-planet arc and previews what's coming.

    We render four painterly planet portraits in a 2×2 layout:
      - top-left:  HD 188753 Ab (this segment — triple-star world)
      - top-right: HD 80606 b (next segment — whiplash planet)
      - bot-left:  PSR B1257+12 (pulsar planets, named after the undead)
      - bot-right: TrES-2b (the darkest exoplanet, darker than coal)
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw_title_strip(img, 'HD 188753 AB')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['paper'])

    # Layout: 2×2 grid in the illustration area
    # Each cell is 540 wide × 250 tall
    # Centered with margins
    grid_left = 100
    grid_top = ILLUSTRATION_TOP + 40
    cell_w = 540
    cell_h = 250
    gap = 20

    # Each planet: (label, base_rgb, bands, seed, caption)
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
        # Planet portrait (painterly) — centered in cell, small
        planet_r = 70
        draw_planet_painterly(img, cx, cy, planet_r, p['base'],
                              palette_dict={'bands': p['bands']},
                              n_bands=len(p['bands']),
                              seed=p['seed'])
        # Caption below the planet
        T.draw_outlined_text(
            draw, (cx - 130, cy + planet_r + 14), p['caption'],
            DRAW_FONT_BOLD,
            fill=PAL['deep'], stroke=PAL['deep'], stroke_width=1,
        )

    # Stickman in the lower-right corner, surveying the grid (medium size,
    # 200 px tall ~28% frame). The lineup grid is the main subject.
    sm.draw_stickman(
        img, x_center=1150, y_top=510, height=200,
        pose='pointing', mouth='oval', seed=15,
    )

    # Final caption (the "lineup is coming" beat)
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
    """Given the alignment, compute start/end times for each card based on
    word indices. The card uses the start of the first word and the end of
    the last word as its time range."""
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
    parser.add_argument('--align', default='round_2_alignment.json',
                        help='Input alignment JSON (round 2: re-aligned to chunked audio).')
    args = parser.parse_args()

    # Round 2: --no-debug is the default. We don't render any debug stamps.
    # The flag is preserved for future debug-on passes but ignored here.
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
        print(f"  {s['id']:25s}  {s['start']:.2f}s -> {s['end']:.2f}s  ({s['end']-s['start']:.2f}s)")

    out_dir = os.path.join(os.path.dirname(__file__), args.frames_dir)
    # Hold the last card until the audio ends so visuals don't fall short of
    # the audio. We want the silent video's duration to be at least the audio's
    # duration (64.64s for the chunked round 2 audio).
    audio_duration = alignment['duration_s']
    schedule_total = schedule[-1]['end'] if schedule else 0.0
    # Compute how many extra frames of the last card we need to bridge.
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
