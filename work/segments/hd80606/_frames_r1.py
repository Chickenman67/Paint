"""Render round_1 frames for HD 80606 b (the whiplash planet).

Reads round_1_alignment.json, plans cards around clause boundaries, renders
each card with a stickman in at least one beat. Outputs PNG frames at 30 fps.
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from lib.palette import SEGMENT_2
from lib.stickman import draw_stickman
from lib.type import draw_header, draw_caption, draw_stamp, HEADER_STRIP_BOTTOM, W, H

FPS = 30
OUT_DIR = os.path.join(os.path.dirname(__file__), 'frames')
os.makedirs(OUT_DIR, exist_ok=True)

# Per CLAUDE.md §5.5: planet name on screen at first spoken word.
# We start the intro card a bit before audio begins to give the snap.
PRE_AUDIO_LEAD_S = 0.20  # 200ms lead on intro card so the header lands first

# Colors
INK = SEGMENT_2['ink']
BG = SEGMENT_2['bg']
PAPER = SEGMENT_2['paper']
YELLOW = SEGMENT_2['accent1']
RED = SEGMENT_2['accent2']
DEEP_RED = SEGMENT_2['planet_dark']
PLANET_WARM = SEGMENT_2['planet']
PLANET_COOL = SEGMENT_2['planet_cool']
DARK = SEGMENT_2['deep']
CAPTION = SEGMENT_2['caption']
ALERT = SEGMENT_2['alert']

# Card layout (segment 2 deep-space variant)
# Title strip y=22..60 holds the planet name. Below that, full-bleed dark space.
# Captions are floating yellow text overlaid on the dark illustration.


def fill_bg(img, color=BG):
    """Solid-fill the background of `img`."""
    ImageDraw.Draw(img).rectangle([0, 0, W, H], fill=color)


def wobbly_ellipse(draw, bbox, fill, outline=INK, width=3, seed=0, n_verts=64):
    """Hand-drawn ellipse with vertex jitter."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    pts = []
    for i in range(n_verts):
        a = 2 * math.pi * i / n_verts
        # small radius jitter for wobbly outline
        r_jx = rng.uniform(-1.0, 1.0)
        r_jy = rng.uniform(-1.0, 1.0)
        x = cx + (rx + r_jx) * math.cos(a)
        y = cy + (ry + r_jy) * math.sin(a)
        pts.append((x, y))
    pts.append(pts[0])
    if fill is not None:
        draw.polygon(pts, fill=fill)
    draw.line(pts, fill=outline, width=width)


def draw_stars(draw, count=120, seed=42):
    """Scatter small white stars across the deep space background."""
    rng = random.Random(seed)
    for _ in range(count):
        x = rng.randint(0, W - 1)
        y = rng.randint(80, H - 1)  # below title strip
        s = rng.choice([1, 1, 1, 2])
        draw.ellipse([x, y, x + s, y + s], fill=(255, 255, 255))


def draw_planet_warm(draw, cx, cy, r, seed=1, glow=True):
    """The HD 80606 b day side: warm yellow with a hint of glow."""
    if glow:
        # Subtle outer glow ring (kept simple, no radial gradient)
        for i in range(3):
            rr = r + 4 * (i + 1)
            draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                         outline=(120, 50, 8), width=1)
    wobbly_ellipse(draw, [cx - r, cy - r, cx + r, cy + r],
                   fill=PLANET_WARM, outline=INK, width=4, seed=seed)
    # Day side highlight band
    draw.ellipse([cx - r * 0.4, cy - r * 0.5, cx + r * 0.4, cy + r * 0.5],
                 fill=(255, 220, 60), outline=None)


def draw_planet_hot(draw, cx, cy, r, seed=2):
    """The 'on fire' version — yellow with red heat band on the star-facing side."""
    wobbly_ellipse(draw, [cx - r, cy - r, cx + r, cy + r],
                   fill=PLANET_WARM, outline=INK, width=4, seed=seed)
    # Heat crescent on the star-facing side
    draw.ellipse([cx - r * 0.6, cy - r * 0.7, cx + r * 0.2, cy + r * 0.7],
                 fill=RED, outline=INK, width=2)
    # Deep red hot spot
    draw.ellipse([cx - r * 0.3, cy - r * 0.2, cx + r * 0.1, cy + r * 0.2],
                 fill=DEEP_RED, outline=INK, width=1)


def draw_sun(draw, cx, cy, r, seed=3):
    """Big red sun as the heat source."""
    # Outer faint red ring (no radial gradient)
    draw.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14],
                 fill=(80, 20, 6), outline=INK, width=2)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=RED, outline=INK, width=4)
    # Sun spots
    rng = random.Random(seed)
    for _ in range(5):
        sx = cx + rng.randint(-int(r * 0.6), int(r * 0.6))
        sy = cy + rng.randint(-int(r * 0.6), int(r * 0.6))
        sr = rng.randint(4, 9)
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                     fill=DEEP_RED, outline=INK, width=1)


def draw_thermometer_spike(draw, x, y, h, max_w=80, seed=0):
    """A spike-style thermometer that gets tall fast."""
    # Vertical bar
    draw.rectangle([x - max_w // 2, y - h, x + max_w // 2, y], fill=RED, outline=INK, width=3)
    # Tick marks
    for i in range(1, 6):
        ty = y - int(h * i / 6)
        draw.line([(x - max_w // 2 - 8, ty), (x - max_w // 2, ty)], fill=INK, width=2)
    # Bulb at bottom
    draw.ellipse([x - max_w // 2 - 6, y - 14, x + max_w // 2 + 6, y + 14],
                 fill=DEEP_RED, outline=INK, width=3)
    # Arrow at top pointing up
    draw.polygon([(x - 10, y - h - 4), (x + 10, y - h - 4), (x, y - h - 22)],
                 fill=ALERT, outline=INK, width=2)


def draw_arrow(draw, p0, p1, color=YELLOW, head=14, width=4):
    """A simple arrow from p0 to p1."""
    draw.line([p0, p1], fill=color, width=width)
    # arrowhead
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    # perpendicular
    px, py = -uy, ux
    left = (p1[0] - ux * head + px * head * 0.6, p1[1] - uy * head + py * head * 0.6)
    right = (p1[0] - ux * head - px * head * 0.6, p1[1] - uy * head - py * head * 0.6)
    draw.polygon([p1, left, right], fill=color, outline=INK, width=1)


def draw_orbit(draw, cx, cy, a, b, color=YELLOW, width=2, seed=0):
    """A stretched elliptical orbit (a > b)."""
    rng = random.Random(seed)
    pts = []
    n = 90
    for i in range(n):
        t = 2 * math.pi * i / n
        jx = rng.uniform(-1.0, 1.0)
        jy = rng.uniform(-1.0, 1.0)
        x = cx + (a + jx) * math.cos(t)
        y = cy + (b + jy) * math.sin(t)
        pts.append((x, y))
    pts.append(pts[0])
    draw.line(pts, fill=color, width=width)


def card_intro(t0_s, dur_s, start_frame):
    """Card 1: 'Now imagine a planet that gets a fever every forty days.'
    Header + warm planet with red/orange glow + small stickman in foreground.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Stars
        draw_stars(draw, count=80, seed=11)
        # Header
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Planet (right side)
        draw_planet_hot(draw, 900, 320, 110, seed=12)
        # Caption (the title phrase of the segment)
        # The whole phrase fits on one line at 27 px Consolas.
        # Use 2 lines to be safe.
        draw_caption(draw, 'A FEVER EVERY FORTY DAYS',
                     (90, 140), YELLOW, INK)
        draw_caption(draw, 'HD 80606 b is a gas giant on the most',
                     (90, 600), CAPTION, INK)
        # Stickman — worried, looking up at the planet
        draw_stickman(img, x_center=300, y_top=470, height=180,
                      pose='standing', mouth='frown', seed=5)
        # Slight head-tilt flicker every 15 frames for "breath"
        if (f // 8) % 2 == 0:
            # emphasize with a tiny red exclamation mark next to stickman's head
            draw.text((300 - 12, 470 - 25), '!?', fill=ALERT)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_orbit(t0_s, dur_s, start_frame):
    """Card 2: 'HD 80606 b. A gas giant about four times the mass of Jupiter,
    on an orbit so stretched out...' — stretched-out orbit diagram.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=80, seed=21)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Sun on the left
        draw_sun(draw, 220, 400, 90, seed=22)
        # Stretched orbit around the sun
        draw_orbit(draw, 220, 400, 470, 130, color=YELLOW, width=3, seed=23)
        # Planet at the far end of the orbit
        px, py = 690, 400
        draw_planet_warm(draw, px, py, 30, seed=24, glow=False)
        # Label
        draw_stamp(draw, '4 x JUPITER', (px - 60, py - 60), YELLOW, INK)
        # Caption
        draw_caption(draw, 'A STRETCHED-OUT ORBIT, 4 x JUPITER',
                     (90, 600), CAPTION, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_cold(t0_s, dur_s, start_frame):
    """Card 3: 'Most of the time, it sits far from its star. Cold. Quiet. Average.'
    Small cool planet in deep space.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=110, seed=31)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Tiny star at far left (just a yellow dot)
        draw.ellipse([140, 380, 168, 408], fill=YELLOW, outline=INK, width=2)
        # Cold planet (blue) on the right, far from the star
        wobbly_ellipse(draw, [800, 320, 920, 440], fill=PLANET_COOL,
                       outline=INK, width=4, seed=32)
        # Stamps under the planet
        draw_stamp(draw, 'COLD', (820, 460), PLANET_COOL, INK)
        draw_stamp(draw, 'QUIET', (820, 490), PLANET_COOL, INK)
        # Caption
        draw_caption(draw, 'MOSTLY FAR. COLD. QUIET.',
                     (90, 600), CAPTION, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_close_pass(t0_s, dur_s, start_frame):
    """Card 4: 'And then it swings in close. Very close. So close that the side
    facing the star gets hit with about eight hundred times more starlight...'
    Planet near a giant red sun, with the day side clearly hot.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=80, seed=41)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Big red sun on the right
        draw_sun(draw, 900, 360, 130, seed=42)
        # Planet on the left, very close, day side lit
        draw_planet_hot(draw, 380, 360, 110, seed=43)
        # Light rays from sun to planet (8 little arrows)
        rng = random.Random(44)
        for _ in range(8):
            x0 = 770 + rng.randint(0, 40)
            y0 = 280 + rng.randint(0, 160)
            x1 = 490 + rng.randint(-30, 30)
            y1 = y0 + rng.randint(-30, 30)
            draw.line([(x0, y0), (x1, y1)], fill=ALERT, width=2)
        # Caption
        draw_caption(draw, 'SWINGS IN CLOSE. 800 x STARLIGHT.',
                     (90, 600), CAPTION, INK)
        # Stamp: 800x
        draw_stamp(draw, '800x', (470, 220), ALERT, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_spike(t0_s, dur_s, start_frame):
    """Card 5: 'In a few hours, the temperature on the day side spikes by
    five hundred degrees Celsius. Five hundred.' — thermometer spike.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=70, seed=51)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Thermometer spike in the center
        draw_thermometer_spike(draw, 640, 580, 380, max_w=70, seed=52)
        # '500 C' label
        draw_stamp(draw, '+500 C', (590, 130), ALERT, INK)
        # Stickman on the right, hands up, screaming (oval mouth) — peak scare
        draw_stickman(img, x_center=1080, y_top=380, height=200,
                      pose='hands_up', mouth='oval', seed=53)
        # Caption
        draw_caption(draw, '+500 C IN A FEW HOURS.',
                     (90, 620), CAPTION, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_swingback(t0_s, dur_s, start_frame):
    """Card 6: 'Then it swings back out, and the temperature crashes just as fast.'
    Planet swinging back out, arrow showing trajectory outward.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=80, seed=61)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Sun on the left (smaller now — it has receded)
        draw_sun(draw, 180, 360, 70, seed=62)
        # Planet further right, cooler color (transitioning)
        # Blend between hot and cool for the swing-back
        wobbly_ellipse(draw, [800, 290, 940, 430], fill=PLANET_COOL,
                       outline=INK, width=4, seed=63)
        # A small hot patch fading
        draw.ellipse([810, 320, 870, 360], fill=DEEP_RED, outline=INK, width=1)
        # Arrow showing trajectory (planet moving away)
        draw_arrow(draw, (600, 380), (760, 380), color=YELLOW, head=14, width=4)
        # Caption
        draw_caption(draw, 'THEN IT SWINGS BACK. TEMPERATURE CRASHES.',
                     (90, 620), CAPTION, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_atmosphere(t0_s, dur_s, start_frame):
    """Card 7: 'The atmosphere cannot do anything reasonable with that. Models
    suggest winds on the order of several kilometers per second, supersonic
    shock waves, day side temperatures hot enough to glow.'
    Shock wave / wind diagram.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=80, seed=71)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # Hot planet center
        draw_planet_hot(draw, 640, 400, 140, seed=72)
        # Shock waves as concentric rings (3 of them)
        for i, r in enumerate([180, 220, 260]):
            color = ALERT if i == 0 else RED
            draw.ellipse([640 - r, 400 - r, 640 + r, 400 + r],
                         outline=color, width=3)
        # Wind arrows (chaotic)
        rng = random.Random(73)
        for i in range(6):
            x0 = 640 + rng.randint(-200, 200)
            y0 = 400 + rng.randint(-200, 200)
            x1 = x0 + rng.randint(-80, 80)
            y1 = y0 + rng.randint(-80, 80)
            draw_arrow(draw, (x0, y0), (x1, y1), color=YELLOW, head=10, width=3)
        # Caption (two lines)
        draw_caption(draw, 'WINDS AT KILOMETERS PER SECOND.',
                     (90, 580), CAPTION, INK)
        draw_caption(draw, 'SUPERSONIC SHOCK WAVES.',
                     (90, 620), CAPTION, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_loop(t0_s, dur_s, start_frame):
    """Card 8 (closing): 'Every forty days, the same thing. The planet gets cooked,
    then frozen, then cooked again. It is, as far as we can tell, the most violent
    routine in the galaxy. A fever, on a loop. With no medicine, and no off switch.'
    — loop / cycle diagram with closing stickman reaction.
    """
    n_frames = int(round(dur_s * FPS))
    # Phase 1: cycle diagram (first ~60% of card)
    cycle_end_frame = int(n_frames * 0.6)
    # Phase 2: closing stickman + caption (last 40%)
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=70, seed=81)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)

        if f < cycle_end_frame:
            # Cycle phase
            cx1, cy1 = 380, 260
            cx2, cy2 = 640, 460
            cx3, cy3 = 900, 260
            wobbly_ellipse(draw, [cx1 - 38, cy1 - 38, cx1 + 38, cy1 + 38],
                           fill=RED, outline=INK, width=3, seed=82)
            wobbly_ellipse(draw, [cx2 - 38, cy2 - 38, cx2 + 38, cy2 + 38],
                           fill=PLANET_COOL, outline=INK, width=3, seed=83)
            wobbly_ellipse(draw, [cx3 - 38, cy3 - 38, cx3 + 38, cy3 + 38],
                           fill=RED, outline=INK, width=3, seed=84)
            draw_arrow(draw, (415, 285), (605, 440), color=YELLOW, head=14, width=3)
            draw_arrow(draw, (675, 440), (875, 285), color=YELLOW, head=14, width=3)
            draw_stamp(draw, 'EVERY 40 DAYS', (cx2 - 50, cy2 + 50), YELLOW, INK)
            draw_caption(draw, 'COOKED. FROZEN. COOKED AGAIN.',
                         (90, 620), CAPTION, INK)
        else:
            # Closing phase — big planet, scared stickman
            wobbly_ellipse(draw, [450, 200, 830, 540], fill=PLANET_WARM,
                           outline=INK, width=4, seed=92)
            draw.ellipse([470, 260, 660, 480], fill=RED, outline=INK, width=2)
            # Big closing caption
            draw_caption(draw, 'THE MOST VIOLENT ROUTINE IN THE GALAXY.',
                         (90, 100), YELLOW, INK)
            # Stickman hands up, oval mouth (screaming) — peak reaction
            draw_stickman(img, x_center=180, y_top=470, height=190,
                          pose='hands_up', mouth='oval', seed=93)
            # Final caption at the bottom
            draw_caption(draw, 'A FEVER ON A LOOP. NO OFF SWITCH.',
                         (90, 660), ALERT, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


def card_closing(t0_s, dur_s, start_frame):
    """Card 9: 'It is, as far as we can tell, the most violent routine in the
    galaxy. A fever, on a loop. With no medicine, and no off switch.' — closing
    card with stickman screaming, hands up.
    """
    n_frames = int(round(dur_s * FPS))
    for f in range(n_frames):
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_stars(draw, count=110, seed=91)
        draw_header(draw, 'HD 80606 B', YELLOW, INK, center_x=W // 2)
        # The planet floating, half-hot, half-cool
        wobbly_ellipse(draw, [450, 220, 830, 540], fill=PLANET_WARM,
                       outline=INK, width=4, seed=92)
        draw.ellipse([470, 270, 660, 490], fill=RED, outline=INK, width=2)
        # Big caption — the closing line, hand-lettered style
        draw_caption(draw, 'THE MOST VIOLENT ROUTINE IN THE GALAXY.',
                     (90, 100), YELLOW, INK)
        # Stickman bottom-left, hands up, oval mouth — peak reaction
        draw_stickman(img, x_center=180, y_top=470, height=190,
                      pose='hands_up', mouth='oval', seed=93)
        # Second stickman right side, deadpan worried
        if n_frames > 30 and f > n_frames // 2:
            draw_stickman(img, x_center=1100, y_top=490, height=170,
                          pose='standing', mouth='frown', seed=94)
        # Final caption at the bottom
        draw_caption(draw, 'A FEVER ON A LOOP. NO OFF SWITCH.',
                     (90, 660), ALERT, INK)
        img.save(os.path.join(OUT_DIR, f'frame_{start_frame + f:06d}.png'))


# Card plan: (start_time, duration, render_fn)
# Times in seconds. Calibrated to the actual alignment (40.0s, 162 words,
# 243 wpm — the chatterbox delivery came in fast).
# Phrase boundaries chosen from the alignment word timings:
#   0.0    Now imagine a planet that gets a fever every forty days.   (ends 2.84)
#   2.84   HD 80606 b. A gas giant about four times the mass of Jupiter...
#   10.30  ...bent the ruler.
#   10.70  Most of the time, it sits far from its star. Cold. Quiet. Average.
#   14.24  And then it swings in close. Very close. So close...
#   20.30  ...than the side facing away.
#   20.82  In a few hours, the temperature on the day side spikes...
#   24.22  Five hundred.
#   25.16  Then it swings back out, and the temperature crashes just as fast.
#   27.80  The atmosphere cannot do anything reasonable with that.
#   35.80  Every 40 days, the same thing. The planet gets cooked and frozen...
#   39.36  It is, as far as we can tell, the most violent routine... (closing)
CARDS = [
    (-0.20, 3.04, card_intro),       # t0=-0.2 so the header is on at t=0
    ( 2.84, 7.46, card_orbit),
    (10.30, 3.94, card_cold),
    (14.24, 6.06, card_close_pass),
    (20.30, 4.86, card_spike),       # ends at 25.16
    (25.16, 2.64, card_swingback),   # ends at 27.80
    (27.80, 8.00, card_atmosphere),  # ends at 35.80
    (35.80, 4.20, card_loop),        # ends at 40.00
]


def render_silent(alignment):
    """Render all cards based on the plan. The plan is approximate; the final
    duration is filled out to match the actual WAV duration with a tiny tail.
    """
    wav_dur = alignment['duration_s']
    # Build a frame-by-frame index: which card is on screen at frame f?
    plan = []
    for t0, dur, fn in CARDS:
        plan.append([t0, dur, fn])
    last_end = plan[-1][0] + plan[-1][1]
    if last_end < wav_dur:
        plan[-1][1] = wav_dur - plan[-1][0]
    elif last_end > wav_dur:
        plan[-1][1] = wav_dur - plan[-1][0]

    # Render cards, advancing a running frame index so output frames are
    # contiguous (no gaps from float->int truncation).
    lead_s = -plan[0][0] if plan[0][0] < 0 else 0.0
    running_frame = 0
    for t0, dur, fn in plan:
        n_frames = int(round(dur * FPS))
        audio_t0 = t0 + lead_s
        fn(audio_t0, dur, running_frame)
        print(f"  {fn.__name__}: audio_t0={audio_t0:.2f}s dur={dur:.2f}s "
              f"n_frames={n_frames} out_frame_start={running_frame}")
        running_frame += n_frames
    total_s = wav_dur + lead_s
    print(f"Total frames written: {running_frame}")
    return lead_s, running_frame


def main():
    align_path = os.path.join(os.path.dirname(__file__), 'round_1_alignment.json')
    with open(align_path) as f:
        a = json.load(f)
    print(f"Alignment: {a['duration_s']:.2f}s, {len(a['words'])} words")
    render_silent(a)
    print("Done.")


if __name__ == '__main__':
    main()
