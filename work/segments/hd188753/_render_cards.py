# work/segments/hd188753/_render_cards.py
# Renders the cards for segment 1 (HD 188753 Ab) based on a card schedule
# derived from the alignment JSON. The output is a sequence of PNG frames at
# 30 fps plus a card schedule JSON.
#
# Per CLAUDE.md §5 + ref_style_spec.md, cards are tied to phrases in the
# narration, not to predicted beat counts. We read the alignment to find
# phrase boundaries, then assign each phrase to a card.
#
# Per ref_style_spec.md Layout A: 39-px title strip at y=22..60, full-bleed
# illustration from y=80 to y=719. Captions are yellow floating text on the
# illustration (NOT a bottom band).
#
# Stickman: must appear in at least 1 card per CLAUDE.md §6. We cycle him
# through 3+ expressions across the segment (deadpan -> awed -> worried ->
# deadpan). The stickman is rendered at full-body framing ~280 px tall in
# the lower-left of the illustration area, OR close-up framing on the
# right side for the closing beat.

import os
import json
import math
import random
import sys

# Ensure we can import the lib modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PIL import Image, ImageDraw, ImageFilter
from lib import stickman as sm
from lib import palette as P
from lib import type as T

# Frame dimensions
W, H = 1280, 720
FPS = 30
TITLE_STRIP_TOP = 22
TITLE_STRIP_BOT = 61   # y=22..60 inclusive
ILLUSTRATION_TOP = 80
ILLUSTRATION_BOT = 719

PAL = P.SEGMENT_1

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
        # Re-stroke outline for crispness
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


# --- Card-level renderers ---

def draw_title_strip(img, name, accent_color=None, ink=(0, 0, 0), paper=(255, 255, 255), fill_color=None):
    """Render the title strip at y=22..60 with the planet name centered.

    Per the reference, the header is BLACK on a WHITE strip. We use a 3-px
    stroke for the outlined-letter look without overwhelming the letter shape.
    """
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, TITLE_STRIP_TOP, W - 1, TITLE_STRIP_BOT], fill=paper)
    # Use a simpler approach: black-on-white with a thin outline accent
    font = T.load_font(T.HEADER_PX, bold=True)
    bx, by, bw, bh = T._bbox(draw, name, font)
    x = (W - bw) // 2
    y = T.HEADER_STRIP_Y + (T.HEADER_STRIP_H - bh) // 2 - 2
    # Black fill with a 2px black stroke — keeps the hand-drawn look
    T.draw_outlined_text(draw, (x, y), name, font, fill=(0, 0, 0), stroke=(0, 0, 0), stroke_width=2)


def draw_3_suns(draw, positions, sizes, colors, seed=0, with_orbit=False):
    """Draw three suns at given positions with given sizes and colors.

    positions: list of (cx, cy) tuples
    sizes: list of radii
    colors: list of (outline_rgb, fill_rgb) tuples
    """
    for i, ((cx, cy), r, (outline, fill)) in enumerate(zip(positions, sizes, colors)):
        # Soft glow ring (a slightly bigger lighter ring behind)
        draw.ellipse(
            [cx - int(r * 1.35), cy - int(r * 1.35), cx + int(r * 1.35), cy + int(r * 1.35)],
            fill=tuple(min(255, c + 60) for c in fill),
        )
        # Sun body
        wobble_circle(
            draw, (cx, cy), r, outline, fill=fill, width=4,
            seed=seed + i * 13, segments=24, jitter=2.0,
        )


def draw_planet(draw, cx, cy, r, fill, outline=(0, 0, 0), seed=42):
    """Draw a small planet as a wobbly circle."""
    wobble_circle(
        draw, (cx, cy), r, outline, fill=fill, width=4,
        seed=seed, segments=28, jitter=1.5,
    )
    # A subtle horizontal band (gas giant feel)
    band_y = cy + r * 0.15
    wobble_line(
        draw, (cx - int(r * 0.85), band_y), (cx + int(r * 0.85), band_y),
        color=tuple(max(0, c - 30) for c in fill), width=2, seed=seed + 7,
    )


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
        # Draw dashes
        for i in range(0, len(pts) - 1, 2):
            draw.line([pts[i], pts[i + 1]], fill=color, width=2)
    else:
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=color, width=2)


def draw_force_arrows(draw, cx, cy, sun_positions, planet_xy):
    """Draw 3 arrows from each sun pointing toward the planet, indicating
    gravitational pull in 3 different directions."""
    px, py = planet_xy
    for sx, sy, color in sun_positions:
        # Arrow line from sun toward planet
        wobble_line(
            draw, (sx, sy), (px, py), color=color, width=3,
            seed=int(sx + sy), jitter=1.0, segments=10,
        )
        # Arrow head near planet
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
        # Big "?" — a top hook + a bottom dot, drawn as a wobbly path
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
        # Dot
        wobble_circle(
            draw, (cx, cy + 8), 4, color, fill=color, width=2,
            seed=int(cx + cy) + 4, segments=8, jitter=0.6,
        )


def draw_calendar(draw, cx, cy, w, h, line_color, paper=(255, 255, 255)):
    """Draw a small wobbly calendar with a big X through it."""
    # Frame
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
    # Hanging rings at the top
    for ring_x in [cx - w / 4, cx + w / 4]:
        draw.ellipse(
            [ring_x - 6, cy - h / 2 - 12, ring_x + 6, cy - h / 2],
            outline=line_color, width=2,
        )
    # A few horizontal date lines
    for i, ly in enumerate([cy - h / 4, cy, cy + h / 4]):
        draw.line(
            [(cx - w / 2 + 8, ly), (cx + w / 2 - 8, ly)],
            fill=line_color, width=1,
        )
    # Big red X across it
    wobble_line(
        draw, (cx - w / 2 + 6, cy - h / 2 + 6), (cx + w / 2 - 6, cy + h / 2 - 6),
        color=PAL['alert'], width=6, seed=int(cx + cy), segments=8,
    )
    wobble_line(
        draw, (cx + w / 2 - 6, cy - h / 2 + 6), (cx - w / 2 + 6, cy + h / 2 - 6),
        color=PAL['alert'], width=6, seed=int(cx + cy) + 1, segments=8,
    )


def render_card(card_id, frame_no_seed=0):
    """Render a single card. Returns a PIL Image at 1280x720.

    card_id: one of the card keys in CARDS (see below).
    """
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    return img, draw


# --- Card content renderers (one per card) ---

def card_intro(t=0.0):
    """Card 1: 'Imagine a sky with three suns.' — 3 suns in cool sky, stickman looking up."""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    # Sky background — light blue filling illustration area
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns, drifting in different positions
    positions = [(320, 250), (640, 200), (960, 280)]
    sizes = [70, 90, 80]
    colors = [
        (PAL['accent1'], PAL['accent3']),  # yellow sun (red outline)
        (PAL['accent1'], PAL['accent1']),  # red sun
        (PAL['accent1'], (255, 140, 50)),  # orange sun
    ]
    draw_3_suns(draw, positions, sizes, colors, seed=10)

    # Small planet in lower middle
    draw_planet(draw, 640, 580, 28, PAL['planet'], seed=20)

    # Stickman in foreground, looking up — pointing at the suns
    sm.draw_stickman(
        img, x_center=200, y_top=380, height=300,
        pose='pointing', mouth='oval', seed=1,
    )

    # Caption: "Imagine a sky with three suns." — yellow floating text
    T.draw_caption(
        draw, "IMAGINE A SKY WITH THREE SUNS",
        xy=(300, 470), color_rgb=PAL['caption'],
    )
    return img


def card_not_a_line(t=0.0):
    """Card 2: 'Not in a line, like a cosmic cliche.' — 3 suns in a diagonal."""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns, NOT in a line — staggered across the sky
    positions = [(200, 240), (640, 180), (1080, 320)]
    sizes = [60, 95, 70]
    colors = [
        (PAL['accent1'], PAL['accent3']),
        (PAL['accent1'], PAL['accent1']),
        (PAL['accent1'], (255, 140, 50)),
    ]
    draw_3_suns(draw, positions, sizes, colors, seed=30)

    # A dashed "cliche" line through them, with a big X over it
    wobble_line(
        draw, (200, 240), (1080, 320),
        color=PAL['deep'], width=2, seed=33, segments=24,
    )
    # Big red X over the line
    wobble_line(
        draw, (350, 200), (950, 380),
        color=PAL['alert'], width=8, seed=34, segments=12,
    )
    wobble_line(
        draw, (950, 200), (350, 380),
        color=PAL['alert'], width=8, seed=35, segments=12,
    )

    T.draw_caption(
        draw, "NOT IN A LINE",
        xy=(450, 600), color_rgb=PAL['caption'],
    )
    T.draw_caption(
        draw, "LIKE A COSMIC CLIche",
        xy=(420, 640), color_rgb=PAL['caption'],
    )
    return img


def card_waltz(t=0.0):
    """Card 3: 'In a slow waltz.' — 3 suns in waltz-like formation."""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in a loose triangular formation
    positions = [(420, 280), (640, 180), (860, 280)]
    sizes = [55, 75, 55]
    colors = [
        (PAL['accent1'], PAL['accent3']),
        (PAL['accent1'], PAL['accent1']),
        (PAL['accent1'], (255, 140, 50)),
    ]
    draw_3_suns(draw, positions, sizes, colors, seed=40)

    # Curved arrows showing the slow waltz motion
    # A swooping curve through the 3 suns
    pts = [
        (420, 280), (380, 350), (450, 420), (640, 460),
        (830, 420), (900, 350), (860, 280), (820, 200), (640, 140),
        (460, 200), (420, 280),
    ]
    for i in range(len(pts) - 1):
        wobble_line(
            draw, pts[i], pts[i + 1], color=PAL['deep'], width=2,
            seed=41 + i, segments=4,
        )

    T.draw_caption(
        draw, "IN A SLOW WALTZ",
        xy=(520, 540), color_rgb=PAL['caption'],
    )
    return img


def card_three_suns_detail(t=0.0):
    """Card 4: 'One yellow, one orange, one red, drifting across each other
    every few days, casting shadows that do not make sense.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns, labeled with small color stamps
    positions = [(240, 280), (640, 200), (1040, 320)]
    sizes = [80, 110, 80]
    colors = [
        (PAL['accent1'], PAL['accent3']),    # yellow
        (PAL['accent1'], PAL['accent1']),    # red
        (PAL['accent1'], (255, 140, 50)),    # orange
    ]
    draw_3_suns(draw, positions, sizes, colors, seed=50)

    # Color labels
    T.draw_stamp(draw, "YELLOW", xy=(195, 380), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "RED", xy=(670, 330), accent_rgb=PAL['deep'])
    T.draw_stamp(draw, "ORANGE", xy=(1000, 420), accent_rgb=PAL['deep'])

    # The planet at the bottom, with crazy crossing shadows
    draw_planet(draw, 640, 600, 50, PAL['planet'], seed=55)

    # Three crossing shadow lines from each sun across the planet
    for sx, sy in positions:
        wobble_line(
            draw, (sx, sy + 100), (640, 600),
            color=PAL['deep'], width=2, seed=int(sx), segments=8,
        )

    T.draw_caption(
        draw, "SHADOWS THAT DO NOT MAKE SENSE",
        xy=(360, 470), color_rgb=PAL['caption'],
    )
    return img


def card_planet_portrait(t=0.0):
    """Card 5: 'That is HD 188753 Ab. A gas giant, roughly the mass of Jupiter,
    locked into a tight orbit around all three of them at once.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['deep'])

    # Big planet portrait (right side)
    draw_planet(draw, 880, 400, 200, PAL['planet'], outline=PAL['accent3'], seed=60)

    # Stars in the background
    rng = random.Random(7)
    for _ in range(40):
        sx = rng.randint(50, 600)
        sy = rng.randint(ILLUSTRATION_TOP + 20, ILLUSTRATION_BOT - 20)
        sr = rng.choice([1, 1, 2, 2, 3])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=PAL['cream'])

    # Stickman on the left, looking at the planet — awed
    sm.draw_stickman(
        img, x_center=200, y_top=380, height=300,
        pose='hands_up', mouth='oval', seed=2,
    )

    T.draw_caption(
        draw, "A GAS GIANT, ROUGHLY JUPITER MASS",
        xy=(280, 600), color_rgb=PAL['caption'],
    )
    return img


def card_konacki(t=0.0):
    """Card 6: 'Discovered in 2005 by a team that included a scientist named
    Doctor Konacki. Konacki looked at the data and said: this thing should
    not be calm. Stars in a triple system should not let a planet just sit
    there.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    # Cream paper background full-bleed (no deep sky for this beat — it's
    # about a person, not the planet)
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Portrait frame for Dr. Konacki on the left
    fx, fy = 110, 130
    fw, fh = 360, 460
    # Frame outline (wobbly)
    wobble_ellipse(
        draw, (fx, fy, fx + fw, fy + fh), PAL['ink'], fill=PAL['paper'],
        width=4, seed=120, segments=40, jitter=2.0,
    )

    # Stickman in the portrait frame, deadpan, with tiny glasses (the
    # "scientist"). We use a 'standing' pose with a flat mouth, and draw
    # two small black square lenses over the face area.
    sm.draw_stickman(
        img, x_center=fx + fw // 2, y_top=fy + 60, height=320,
        pose='standing', mouth='flat', seed=121,
    )
    # Tiny glasses — two small black squares on the head
    head_x = fx + fw // 2
    head_y = fy + 60 + 60  # roughly where the head oval sits
    lens_w = 18
    lens_h = 14
    # left lens
    draw.rectangle(
        [head_x - 30 - lens_w // 2, head_y - lens_h // 2,
         head_x - 30 + lens_w // 2, head_y + lens_h // 2],
        outline=PAL['ink'], width=2,
    )
    # right lens
    draw.rectangle(
        [head_x + 30 - lens_w // 2, head_y - lens_h // 2,
         head_x + 30 + lens_w // 2, head_y + lens_h // 2],
        outline=PAL['ink'], width=2,
    )
    # Bridge between lenses
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
    font_b = T.load_font(T.CAPTION_PX, bold=True)
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30), '"THIS THING', font_b,
        fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30 + int(T.CAPTION_PX * 1.4)), 'SHOULD NOT',
        font_b, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )
    T.draw_outlined_text(
        draw, (bx0 + 30, by0 + 30 + int(T.CAPTION_PX * 2.8)), 'BE CALM."',
        font_b, fill=PAL['ink'], stroke=PAL['ink'], stroke_width=1,
    )

    # Stamp "DR. KONACKI, 2005" under the portrait
    T.draw_stamp(
        draw, 'DR. KONACKI, 2005',
        xy=(fx + fw // 2 - 100, fy + fh + 20),
        accent_rgb=PAL['accent1'],
    )

    T.draw_caption(
        draw, "DOCTOR KONACKI LOOKED AT THE DATA",
        xy=(300, 600), color_rgb=PAL['caption'],
    )
    return img


def card_orbit_diagram(t=0.0):
    """Card 6: orbital diagram — 3 suns in middle, planet on a tight orbit around all 3."""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # 3 suns in a tight cluster in the center
    sun_center = (640, 400)
    # Place 3 small suns in a tight triangular cluster
    cluster_positions = [
        (sun_center[0] - 30, sun_center[1] - 20),
        (sun_center[0] + 30, sun_center[1] - 20),
        (sun_center[0], sun_center[1] + 30),
    ]
    cluster_sizes = [40, 40, 40]
    cluster_colors = [
        (PAL['accent1'], PAL['accent3']),
        (PAL['accent1'], PAL['accent1']),
        (PAL['accent1'], (255, 140, 50)),
    ]
    draw_3_suns(draw, cluster_positions, cluster_sizes, cluster_colors, seed=70)

    # Tight orbit around the cluster
    draw_orbit_path(
        draw, sun_center[0], sun_center[1], rx=200, ry=160,
        color=PAL['deep'], seed=71,
    )

    # The planet on the orbit
    draw_planet(draw, 840, 400, 22, PAL['planet'], seed=72)

    # Stickman in lower-left — pointing at the orbit
    sm.draw_stickman(
        img, x_center=180, y_top=450, height=240,
        pose='pointing', mouth='flat', seed=3,
    )

    T.draw_caption(
        draw, "LOCKED IN A TIGHT ORBIT AROUND ALL THREE",
        xy=(300, 650), color_rgb=PAL['caption'],
    )
    return img


def card_force_diagram(t=0.0):
    """Card 7: 'Three stars pull on a planet in three different directions
    at the same time.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['deep'])

    # Planet in the center
    planet_xy = (640, 400)
    draw_planet(draw, planet_xy[0], planet_xy[1], 50, PAL['planet'], outline=PAL['accent3'], seed=80)

    # 3 suns at the edges with arrows pointing at the planet
    sun_positions = [
        (180, 200, PAL['accent3']),    # yellow sun
        (1100, 220, PAL['accent1']),   # red sun
        (640, 100, (255, 140, 50)),    # orange sun
    ]
    for sx, sy, color in sun_positions:
        # Sun
        wobble_circle(
            draw, (sx, sy), 45, PAL['accent1'], fill=color, width=4,
            seed=int(sx + sy), segments=20, jitter=1.5,
        )
        # Arrow toward planet
        wobble_line(
            draw, (sx, sy), planet_xy, color=color, width=3,
            seed=int(sx + sy) + 1, segments=10,
        )
        # Arrow head
        ang = math.atan2(planet_xy[1] - sy, planet_xy[0] - sx)
        head_len = 14
        head_ang = 0.5
        hx, hy = planet_xy[0] - 60 * math.cos(ang), planet_xy[1] - 60 * math.sin(ang)
        h1 = (hx - head_len * math.cos(ang - head_ang), hy - head_len * math.sin(ang - head_ang))
        h2 = (hx - head_len * math.cos(ang + head_ang), hy - head_len * math.sin(ang + head_ang))
        draw.polygon([(hx, hy), h1, h2], fill=color, outline=color)

    # Stars
    rng = random.Random(8)
    for _ in range(50):
        sx = rng.randint(20, W - 20)
        sy = rng.randint(ILLUSTRATION_TOP + 10, ILLUSTRATION_BOT - 10)
        if 100 < sx < 1180 and 300 < sy < 500:
            continue  # don't draw stars on the planet
        sr = rng.choice([1, 1, 2])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=PAL['cream'])

    T.draw_caption(
        draw, "PULLED IN THREE DIRECTIONS",
        xy=(400, 600), color_rgb=PAL['caption'],
    )
    return img


def card_wobble_orbit(t=0.0):
    """Card 8: 'The orbit is not a circle. It is a slow, wobbling, slightly
    drunk figure eight.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['deep'])

    # Wobbling figure-eight orbit
    cx, cy = 640, 400
    rng = random.Random(90)
    pts = []
    for i in range(200):
        t = i / 200 * 2 * math.pi
        # Lemniscate-like (figure eight) with wobble
        denom = 1 + math.sin(t) ** 2
        x = (200 * math.cos(t)) / denom + cx + rng.uniform(-2, 2)
        y = 140 * math.sin(t) * math.cos(t) / denom + cy + rng.uniform(-2, 2)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=PAL['accent3'], width=2)

    # The planet on the orbit (at one of the lobes)
    draw_planet(draw, 800, 360, 30, PAL['planet'], outline=PAL['accent3'], seed=91)

    # 3 small stars in the background
    rng2 = random.Random(9)
    for _ in range(50):
        sx = rng2.randint(20, W - 20)
        sy = rng2.randint(ILLUSTRATION_TOP + 10, ILLUSTRATION_BOT - 10)
        sr = rng2.choice([1, 1, 2])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sy + sr], fill=PAL['cream']) if False else draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=PAL['cream'])

    T.draw_caption(
        draw, "A SLOW WOBBLING FIGURE EIGHT",
        xy=(360, 600), color_rgb=PAL['caption'],
    )
    return img


def card_no_idea_weather(t=0.0):
    """Card 9: 'We have no idea what its atmosphere does. We do not even
    know if it has weather.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['deep'])

    # Empty atmosphere — wisps of nothingness
    # A faint wobbly circle representing an atmosphere
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

    # The planet inside
    draw_planet(draw, 640, 400, 60, PAL['planet'], outline=PAL['accent3'], seed=103)

    # Question marks
    draw_question_marks(
        draw, 3, [(300, 250), (980, 280), (640, 150)], PAL['caption']
    )

    # Stars
    rng = random.Random(11)
    for _ in range(40):
        sx = rng.randint(20, W - 20)
        sy = rng.randint(ILLUSTRATION_TOP + 10, ILLUSTRATION_BOT - 10)
        sr = rng.choice([1, 1, 2])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=PAL['cream'])

    T.draw_caption(
        draw, "WE HAVE NO IDEA",
        xy=(520, 600), color_rgb=PAL['caption'],
    )
    return img


def card_calendar_lie(t=0.0):
    """Card 10: 'It is the kind of place where a calendar would be a lie.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['bg'])

    # Calendar with big X
    draw_calendar(
        draw, cx=440, cy=380, w=200, h=240,
        line_color=PAL['deep'], paper=PAL['paper'],
    )

    # Stickman on the right, shrugging (deadpan, arms out)
    sm.draw_stickman(
        img, x_center=950, y_top=380, height=300,
        pose='standing', mouth='flat', seed=4,
    )

    # A 'sunrise' crossed-out in the background
    # Small sun on the horizon
    wobble_circle(
        draw, (200, 600), 30, PAL['accent1'], fill=PAL['accent3'], width=3,
        seed=110, segments=18, jitter=1.0,
    )
    # X over the sun
    wobble_line(
        draw, (180, 580), (220, 620),
        color=PAL['alert'], width=5, seed=111, segments=4,
    )
    wobble_line(
        draw, (220, 580), (180, 620),
        color=PAL['alert'], width=5, seed=112, segments=4,
    )
    # "SUNRISE" label crossed out
    T.draw_stamp(draw, "SUNRISE = MEANINGLESS", xy=(150, 660), accent_rgb=PAL['deep'])

    T.draw_caption(
        draw, "A CALENDAR WOULD BE A LIE",
        xy=(420, 180), color_rgb=PAL['caption'],
    )
    return img


def card_sits_there(t=0.0):
    """Card 11 (closing): 'And the planet just sits there. Three suns.
    Wobbling. Doing its impossible thing. Nothing about it is calm.'"""
    img = Image.new('RGB', (W, H), PAL['paper'])
    draw = ImageDraw.Draw(img)
    draw_title_strip(img, 'HD 188753 AB')

    # Same dark-space background as the closing beat
    draw.rectangle([0, ILLUSTRATION_TOP, W - 1, ILLUSTRATION_BOT], fill=PAL['deep'])

    # The planet centered, slightly larger
    draw_planet(draw, 640, 400, 100, PAL['planet'], outline=PAL['accent3'], seed=120)

    # 3 small suns in the distance
    sun_positions = [
        (180, 200, PAL['accent3']),
        (1100, 220, PAL['accent1']),
        (640, 130, (255, 140, 50)),
    ]
    for sx, sy, color in sun_positions:
        wobble_circle(
            draw, (sx, sy), 30, PAL['accent1'], fill=color, width=3,
            seed=int(sx + sy), segments=18, jitter=1.2,
        )

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
    rng2 = random.Random(13)
    for _ in range(60):
        sx = rng2.randint(20, W - 20)
        sy = rng2.randint(ILLUSTRATION_TOP + 10, ILLUSTRATION_BOT - 10)
        sr = rng2.choice([1, 1, 2, 2])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=PAL['cream'])

    # Stickman in lower-left, deadpan — looking at the planet
    sm.draw_stickman(
        img, x_center=180, y_top=470, height=240,
        pose='standing', mouth='flat', seed=5,
    )

    T.draw_caption(
        draw, "NOTHING ABOUT IT IS CALM",
        xy=(380, 640), color_rgb=PAL['caption'],
    )
    return img


# --- Card schedule (driven by the alignment) ---

# Each card has a key, a renderer, and start/end word indices in the alignment
# (NOT phrases — the alignment is the ground truth). The card scheduler
# computes start/end times from the alignment.

# Card plan (from the alignment analysis):
# Card 1 (intro): "Imagine a sky with three suns."  words 0-5
# Card 2 (not_a_line): "Not in a line, like a cosmic cliche."  words 6-13
# Card 3 (waltz): "In a slow waltz."  words 14-17
# Card 4 (three_suns_detail): "One yellow, one orange, one red, drifting..."  words 18-37
# Card 5 (planet_portrait): "That is HD 188753 Ab. A gas giant... at once."  words 38-62
# Card 6 (konacki): "Discovered in 2005... this thing should not be calm."  words 63-93
# Card 7 (force_diagram): "Three stars pull on a planet in three different directions at the same time."  words 94-107
# Card 8 (wobble_orbit): "The orbit is not a circle. It is a slow, wobbling... close to another."  words 108-137
# Card 9 (no_idea_weather): "We have no idea what its atmosphere does... has weather."  words 138-165
# Card 10 (calendar_lie): "It is the kind of place... shadows are always lying."  words 166-198
# Card 11 (sits_there): "And the planet just sits there... Nothing about it is calm."  words 199-216

CARDS = [
    {'id': 'intro',             'start_w': 0,   'end_w': 5,   'renderer': card_intro},
    {'id': 'not_a_line',        'start_w': 6,   'end_w': 13,  'renderer': card_not_a_line},
    {'id': 'waltz',             'start_w': 14,  'end_w': 17,  'renderer': card_waltz},
    {'id': 'three_suns_detail', 'start_w': 18,  'end_w': 37,  'renderer': card_three_suns_detail},
    {'id': 'planet_portrait',   'start_w': 38,  'end_w': 62,  'renderer': card_planet_portrait},
    {'id': 'konacki',           'start_w': 63,  'end_w': 93,  'renderer': card_konacki},
    {'id': 'force_diagram',     'start_w': 94,  'end_w': 107, 'renderer': card_force_diagram},
    {'id': 'wobble_orbit',      'start_w': 108, 'end_w': 137, 'renderer': card_wobble_orbit},
    {'id': 'no_idea_weather',   'start_w': 138, 'end_w': 165, 'renderer': card_no_idea_weather},
    {'id': 'calendar_lie',      'start_w': 166, 'end_w': 198, 'renderer': card_calendar_lie},
    {'id': 'sits_there',        'start_w': 199, 'end_w': 216, 'renderer': card_sits_there},
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
        # Clamp to duration
        end = min(end, duration)
        schedule.append({
            'id': card['id'],
            'start': start,
            'end': end,
            'renderer': card['renderer'],
        })

    # Final card extends to the very end of the audio
    if schedule:
        schedule[-1]['end'] = duration

    return schedule


def render_segment(schedule, out_dir, fps=FPS, hold_last_frames=0):
    """Render all cards as a sequence of PNGs at `fps`."""
    os.makedirs(out_dir, exist_ok=True)
    total_frames = 0
    frame_map = []  # list of (frame_idx, card_id)

    for card in schedule:
        n_frames = max(1, int(round((card['end'] - card['start']) * fps)))
        img = card['renderer'](t=card['start'])
        for i in range(n_frames):
            fpath = os.path.join(out_dir, f'frame_{total_frames:05d}.png')
            img.save(fpath)
            frame_map.append({'frame': total_frames, 'card': card['id'], 't': card['start'] + i / fps})
            total_frames += 1

    if hold_last_frames > 0:
        # Hold the last frame for an extra moment
        last_img = schedule[-1]['renderer'](t=schedule[-1]['end'])
        for i in range(hold_last_frames):
            fpath = os.path.join(out_dir, f'frame_{total_frames:05d}.png')
            last_img.save(fpath)
            frame_map.append({'frame': total_frames, 'card': schedule[-1]['id'], 't': schedule[-1]['end']})
            total_frames += 1

    return total_frames, frame_map


def main():
    align_path = os.path.join(os.path.dirname(__file__), 'round_1_alignment.json')
    if not os.path.exists(align_path):
        print('Alignment file not found, run _make_audio_r1.py first.')
        return

    with open(align_path) as f:
        alignment = json.load(f)

    schedule = build_card_schedule(alignment)
    print('Card schedule:')
    for s in schedule:
        print(f"  {s['id']:25s}  {s['start']:.2f}s -> {s['end']:.2f}s  ({s['end']-s['start']:.2f}s)")

    out_dir = os.path.join(os.path.dirname(__file__), 'frames')
    n_frames, frame_map = render_segment(schedule, out_dir)
    print(f"\nTotal frames: {n_frames} at {FPS} fps = {n_frames / FPS:.2f}s")

    # Save the card schedule
    sched_path = os.path.join(os.path.dirname(__file__), 'round_1_card_schedule.json')
    with open(sched_path, 'w') as f:
        json.dump(
            [{'id': s['id'], 'start': s['start'], 'end': s['end']} for s in schedule],
            f, indent=2,
        )
    print(f"Card schedule saved: {sched_path}")


if __name__ == '__main__':
    main()
