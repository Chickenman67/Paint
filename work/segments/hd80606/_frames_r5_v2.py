# work/segments/hd80606/_frames_r5_v2.py
# Round 5 rebuild for segment 2 (HD 80606 b — the whiplash planet).
#
# PARADIGM SHIFT (round 5 verdict for seg 1 + seg 2):
#   "The reference embeds the character IN the world being explained, not
#    beside it as an external narrator."
#
# Round 5 changes every character beat to put the stickman IN the scene:
#   - t=2: Stickman on planet surface with banded gas-giant ground texture,
#          HUGE orange sun looming, awed/scared expression (oval or frown).
#          Integrated "A FEVER EVERY 40 DAYS" text from round 4.
#   - t=8: Stickman floating IN space near the whiplash orbit path (elliptical
#          orbit visible as swooping line), uncomfortable expression (zigzag).
#          The stickman is IN the orbit showing the viewer the WILD path.
#   - t=14: Close-approach beat — stickman on planet surface with fire aura
#           around the sun, integrated "SO CLOSE" text, scared expression (frown).
#           The emotional peak lands because the stickman is IN the heat.
#   - t=20: Fever peak — stickman on surface with integrated "FEVER" text,
#           distressed expression, HUGE spike-aura sun. Stickman is IN the fever.
#   - t=28: Absurdity peak — stickman on surface with integrated "NOTHING
#           REASONABLE" text, skeptical/wry expression (smirk or zigzag),
#           massive sun. The stickman skepticism reads IN the scene.
#   - t=36: Stickman standing on a calendar/time-marker surface (stylized),
#           downturned worried expression, showing the 40-day cycle as a place
#           the stickman inhabits.
#
# KEEP from round 4:
#   - Integrated captions (ALL-CAPS heavy text on diagrams)
#   - Fire/spike aura around close-pass sun
#   - Banded gas-giant texture on planet (painterly stipple)
#   - Locked orange/yellow/cream palette (no blue, no gradients except planet)
#   - Header band with painterly stipple
#
# Audio: round 4 audio (40s duration).
# Output: 1200 frames at 30fps.

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

# Round 5 PALETTE: same locked orange/yellow/cream from round 4
PAL = {
    'name': 'HD 80606 b',
    'ink': (0, 0, 0),                       # black ink
    'paper': (250, 232, 200),               # warm cream paper
    'bg': (10, 4, 2),                       # very dark brown-black
    'accent1': (255, 200, 60),              # warm yellow — captions
    'accent2': (255, 110, 25),              # orange — heat
    'accent3': (255, 240, 180),             # cream highlights
    'deep': (60, 18, 4),                    # dark red-brown
    'alert': (255, 70, 10),                 # bright red — "worse is coming"
    'planet': (255, 140, 40),               # warm orange — planet
    'planet_cool': (200, 130, 60),          # dim cool tone (cold side)
    'planet_dark': (160, 60, 20),           # dark red — deep heat
    'caption': (255, 215, 60),              # yellow floating captions
}

INK = PAL['ink']

# Heavy-caption font (for integrated diagram labels)
HEAVY_CAPTION_PX = 64
HEAVY_CAPTION_FONT = T.load_font(HEAVY_CAPTION_PX, bold=True)

# Header font
HEADER_FONT = T.load_font(72, bold=True)


def draw_banded_gas_giant_ground(img, horizon_y, palette):
    """Draw a banded gas-giant surface texture at the bottom of the image."""
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Ground region: horizon_y to bottom
    ground_h = H - horizon_y

    # Draw horizontal bands with slight wobble
    band_colors = [palette['planet'], palette['planet_dark'],
                   palette['planet_cool'], palette['accent2']]
    band_h = ground_h // len(band_colors)

    for i, color in enumerate(band_colors):
        y_start = horizon_y + i * band_h
        y_end = horizon_y + (i + 1) * band_h if i < len(band_colors) - 1 else H

        # Draw base band
        draw.rectangle([0, y_start, W, y_end], fill=color)

        # Add wobbly top edge
        for x in range(0, W, 4):
            jitter = random.randint(-2, 2)
            draw.line([(x, y_start + jitter), (x + 4, y_start + jitter)],
                     fill=INK, width=1)

        # Add stipple texture
        random.seed(42 + i)
        for _ in range(int((y_end - y_start) * W * 0.001)):
            sx = random.randint(0, W - 1)
            sy = random.randint(y_start, y_end - 1)
            draw.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=INK)


def draw_huge_sun(img, cx, cy, radius, palette, fire_aura=False, spike_aura=False):
    """Draw a huge orange sun with optional fire/spike aura."""
    draw = ImageDraw.Draw(img)

    # Fire aura (wide gentle glow)
    if fire_aura:
        for i in range(80, 0, -12):
            alpha_factor = i / 80.0
            glow_r = radius + i
            glow_color = (
                int(palette['accent2'][0] * alpha_factor * 0.4),
                int(palette['accent2'][1] * alpha_factor * 0.3),
                int(palette['accent2'][2] * alpha_factor * 0.2)
            )
            draw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
                        fill=glow_color)

    # Spike aura (aggressive rays)
    if spike_aura:
        random.seed(123)
        num_spikes = 24
        for i in range(num_spikes):
            angle = (i / num_spikes) * 2 * math.pi
            spike_len = random.randint(radius + 60, radius + 120)
            spike_width = random.randint(8, 16)

            x1 = cx + int(radius * 0.9 * math.cos(angle))
            y1 = cy + int(radius * 0.9 * math.sin(angle))
            x2 = cx + int(spike_len * math.cos(angle))
            y2 = cy + int(spike_len * math.sin(angle))

            # Spike triangle
            angle_offset = 0.15
            x3 = cx + int((radius + spike_width) * math.cos(angle - angle_offset))
            y3 = cy + int((radius + spike_width) * math.sin(angle - angle_offset))
            x4 = cx + int((radius + spike_width) * math.cos(angle + angle_offset))
            y4 = cy + int((radius + spike_width) * math.sin(angle + angle_offset))

            draw.polygon([(x1, y1), (x2, y2), (x4, y4)], fill=palette['accent2'])
            draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=palette['alert'])

    # Sun body
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 fill=palette['accent1'], outline=INK, width=4)

    # Sun core detail
    core_r = radius // 3
    draw.ellipse([cx - core_r, cy - core_r, cx + core_r, cy + core_r],
                 fill=palette['accent3'], outline=None)


def draw_elliptical_orbit_path(draw, palette):
    """Draw the whiplash elliptical orbit path as a swooping line."""
    W, H = 1280, 720

    # Ellipse parameters (very eccentric)
    cx = W // 2
    cy = H // 2 - 40
    a = 320  # semi-major axis
    b = 140  # semi-minor axis

    # Draw orbit as wobbly line
    points = []
    for t in range(0, 360, 3):
        rad = math.radians(t)
        x = cx + int(a * math.cos(rad))
        y = cy + int(b * math.sin(rad))
        points.append((x, y))

    # Draw the path
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=palette['accent3'], width=3)
    draw.line([points[-1], points[0]], fill=palette['accent3'], width=3)

    # Mark perihelion (closest approach) with a bright dot
    perihelion_x = cx + a
    perihelion_y = cy
    draw.ellipse([perihelion_x - 8, perihelion_y - 8,
                 perihelion_x + 8, perihelion_y + 8],
                fill=palette['alert'], outline=INK, width=2)


def draw_calendar_surface(img, horizon_y, palette):
    """Draw a stylized calendar/time-marker surface."""
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Ground as grid of calendar cells
    ground_h = H - horizon_y
    cell_w = 80
    cell_h = 60

    # Fill ground with calendar grid
    draw.rectangle([0, horizon_y, W, H], fill=palette['paper'])

    # Draw grid lines
    for x in range(0, W + cell_w, cell_w):
        draw.line([(x, horizon_y), (x, H)], fill=INK, width=2)
    for y in range(horizon_y, H + cell_h, cell_h):
        draw.line([(0, y), (W, y)], fill=INK, width=2)

    # Mark some cells with day numbers (40-day cycle)
    font = T.load_font(20, bold=True)
    for i in range(0, 5):
        cell_x = i * cell_w * 2 + 40
        cell_y = horizon_y + 30
        day_num = (i * 10) % 40
        text = f"D{day_num}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((cell_x - text_w // 2, cell_y - text_h // 2),
                 text, fill=palette['accent2'], font=font)


def render_frame_t02_stickman_on_planet(palette):
    """t=2: Stickman on planet surface, HUGE sun, banded ground, awed/scared expression.
    Integrated caption: A FEVER EVERY 40 DAYS"""

    # Create scene with stickman on surface
    ground_y_pct = 0.62
    img = sm.stickman_on_surface(
        expression='oval',  # awed/shocked
        pose='standing',
        surface_color=palette['planet'],
        sky_gradient=(palette['bg'], (40, 25, 10)),
        ground_y_pct=ground_y_pct,
        width=W,
        height=H,
        stickman_height=130
    )

    # Replace simple ground with banded gas-giant texture
    horizon_y = int(H * ground_y_pct)
    draw_banded_gas_giant_ground(img, horizon_y, palette)

    # Draw huge sun in sky
    sun_cx = W // 2 + 200
    sun_cy = 180
    sun_radius = 140
    draw_huge_sun(img, sun_cx, sun_cy, sun_radius, palette, fire_aura=True)

    # Integrated caption: A FEVER EVERY 40 DAYS
    caption_text = "A FEVER EVERY 40 DAYS"
    caption_font = T.load_font(58, bold=True)
    integrated_label.draw_integrated_label(
        img, caption_text, W // 2, int(H * 0.25),
        scale=1.0, seed=42,
        fill=palette['caption'], outline=INK,
        font=caption_font
    )

    # Header band
    title_band.draw_title_band(img, "HD 80606 B", palette['accent2'], palette['paper'])

    return img


def render_frame_t08_stickman_in_orbit(palette):
    """t=8: Stickman floating IN space near whiplash orbit path, uncomfortable expression."""

    # Create space scene with orbit
    img = Image.new('RGB', (W, H), palette['bg'])
    draw = ImageDraw.Draw(img)

    # Draw stars
    random.seed(88)
    for _ in range(100):
        sx = random.randint(0, W)
        sy = random.randint(0, H)
        draw.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(200, 200, 220))

    # Draw elliptical orbit path
    draw_elliptical_orbit_path(draw, palette)

    # Draw small sun at one focus (perihelion end)
    sun_cx = W // 2 + 320
    sun_cy = H // 2 - 40
    sun_r = 40
    draw.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
                fill=palette['accent1'], outline=INK, width=3)

    # Draw stickman floating IN the orbit path (uncomfortable)
    stickman_cx = W // 2 - 80
    stickman_cy = H // 2 + 60
    stickman_height = 110
    stickman_top_y = stickman_cy - stickman_height // 2

    geom = sm._draw_stickman_body(draw, stickman_cx, stickman_top_y,
                                   stickman_height, pose='hands_up')

    # Mouth: uncomfortable (zigzag)
    mouth_cy = geom['head_cy'] + int(geom['head_r'] * 0.4)
    sm.mouth_zigzag(draw, stickman_cx, mouth_cy, scale=1.0)

    # Header band
    title_band.draw_title_band(img, "HD 80606 B", palette['accent2'], palette['paper'])

    return img


def render_frame_t14_close_approach_stickman(palette):
    """t=14: Close-approach — stickman on surface, fire aura sun, scared expression.
    Integrated caption: SO CLOSE"""

    # Create scene with stickman on surface
    ground_y_pct = 0.65
    img = sm.stickman_on_surface(
        expression='frown',  # scared
        pose='shielding_eyes',
        surface_color=palette['planet'],
        sky_gradient=((80, 40, 20), (120, 60, 30)),
        ground_y_pct=ground_y_pct,
        width=W,
        height=H,
        stickman_height=120
    )

    # Replace simple ground with banded texture
    horizon_y = int(H * ground_y_pct)
    draw_banded_gas_giant_ground(img, horizon_y, palette)

    # Draw HUGE sun with fire aura (closer now)
    sun_cx = W // 2 + 150
    sun_cy = 160
    sun_radius = 180
    draw_huge_sun(img, sun_cx, sun_cy, sun_radius, palette,
                 fire_aura=True, spike_aura=False)

    # Integrated caption: SO CLOSE
    caption_font = T.load_font(68, bold=True)
    integrated_label.draw_integrated_label(
        img, "SO CLOSE", W // 2, int(H * 0.78),
        scale=1.0, seed=43,
        fill=palette['caption'], outline=INK,
        font=caption_font
    )

    # Header band
    title_band.draw_title_band(img, "HD 80606 B", palette['accent2'], palette['paper'])

    return img


def render_frame_t20_fever_peak_stickman(palette):
    """t=20: Fever peak — stickman on surface, spike-aura sun, distressed expression.
    Integrated caption: FEVER"""

    # Create scene with stickman on surface
    ground_y_pct = 0.68
    img = sm.stickman_on_surface(
        expression='scream',  # terrified
        pose='hands_up',
        surface_color=palette['planet_dark'],
        sky_gradient=((140, 60, 20), (180, 80, 30)),
        ground_y_pct=ground_y_pct,
        width=W,
        height=H,
        stickman_height=115
    )

    # Replace simple ground with banded texture
    horizon_y = int(H * ground_y_pct)
    draw_banded_gas_giant_ground(img, horizon_y, palette)

    # Draw HUGE sun with spike aura (peak heat)
    sun_cx = W // 2 + 100
    sun_cy = 140
    sun_radius = 200
    draw_huge_sun(img, sun_cx, sun_cy, sun_radius, palette,
                 fire_aura=True, spike_aura=True)

    # Integrated caption: FEVER
    caption_font = T.load_font(72, bold=True)
    integrated_label.draw_integrated_label(
        img, "FEVER", W // 2, int(H * 0.80),
        scale=1.0, seed=44,
        fill=palette['caption'], outline=INK,
        font=caption_font
    )

    # Header band
    title_band.draw_title_band(img, "HD 80606 B", palette['accent2'], palette['paper'])

    return img


def render_frame_t28_absurdity_stickman(palette):
    """t=28: Absurdity peak — stickman on surface, skeptical/wry expression, massive sun.
    Integrated caption: NOTHING REASONABLE"""

    # Create scene with stickman on surface
    ground_y_pct = 0.70
    img = sm.stickman_on_surface(
        expression='skeptical',  # one eyebrow raised
        pose='shrugged',
        surface_color=palette['planet'],
        sky_gradient=((100, 50, 20), (140, 70, 30)),
        ground_y_pct=ground_y_pct,
        width=W,
        height=H,
        stickman_height=125
    )

    # Replace simple ground with banded texture
    horizon_y = int(H * ground_y_pct)
    draw_banded_gas_giant_ground(img, horizon_y, palette)

    # Draw massive sun (absurdly large)
    sun_cx = W // 2 + 180
    sun_cy = 150
    sun_radius = 190
    draw_huge_sun(img, sun_cx, sun_cy, sun_radius, palette,
                 fire_aura=True, spike_aura=True)

    # Integrated caption: NOTHING REASONABLE
    caption_font = T.load_font(52, bold=True)
    integrated_label.draw_integrated_label(
        img, "NOTHING REASONABLE", W // 2, int(H * 0.82),
        scale=1.0, seed=45,
        fill=palette['caption'], outline=INK,
        font=caption_font
    )

    # Header band
    title_band.draw_title_band(img, "HD 80606 B", palette['accent2'], palette['paper'])

    return img


def render_frame_t36_calendar_stickman(palette):
    """t=36: Stickman standing on calendar surface, worried expression, showing 40-day cycle."""

    # Create base image
    ground_y_pct = 0.65
    img = Image.new('RGB', (W, H), (180, 160, 140))

    # Sky gradient
    draw = ImageDraw.Draw(img)
    horizon_y = int(H * ground_y_pct)
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        r = int(180 * (1 - t) + 220 * t)
        g = int(160 * (1 - t) + 200 * t)
        b = int(140 * (1 - t) + 180 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Draw calendar surface
    draw_calendar_surface(img, horizon_y, palette)

    # Draw stickman on calendar surface
    stickman_cx = W // 2
    foot_y = horizon_y - 5
    stickman_height = 120
    top_y = foot_y - stickman_height

    geom = sm._draw_stickman_body(draw, stickman_cx, top_y,
                                   stickman_height, pose='standing')

    # Mouth: worried
    mouth_cy = geom['head_cy'] + int(geom['head_r'] * 0.4)
    sm.mouth_worried(draw, stickman_cx, mouth_cy, scale=1.0)

    # Caption: 40 DAYS (small, at top)
    caption_font = T.load_font(48, bold=True)
    caption_text = "40 DAYS"
    bbox = draw.textbbox((0, 0), caption_text, font=caption_font)
    text_w = bbox[2] - bbox[0]
    text_x = (W - text_w) // 2
    text_y = 120

    # Outline
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                draw.text((text_x + dx, text_y + dy), caption_text,
                         fill=INK, font=caption_font)
    # Fill
    draw.text((text_x, text_y), caption_text, fill=palette['accent2'], font=caption_font)

    # Header band
    title_band.draw_title_band(img, "HD 80606 B", palette['accent2'], palette['paper'])

    return img


def main():
    parser = argparse.ArgumentParser(description='Render HD 80606 b round 5 frames')
    parser.add_argument('--out', default='work/segments/hd80606/r5_frames',
                       help='Output directory for frames')
    parser.add_argument('--duration', type=float, default=40.0,
                       help='Duration in seconds (from round 4 audio)')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    total_frames = int(args.duration * FPS)
    print(f"Rendering {total_frames} frames at {FPS} fps for {args.duration}s duration")

    # Card schedule (aligned to round 4 audio word timings)
    # These timestamps match the round 4 alignment
    schedule = [
        (0, 6, 't02', render_frame_t02_stickman_on_planet),      # intro + "fever every 40 days"
        (6, 12, 't08', render_frame_t08_stickman_in_orbit),      # whiplash orbit
        (12, 18, 't14', render_frame_t14_close_approach_stickman), # close approach
        (18, 26, 't20', render_frame_t20_fever_peak_stickman),   # fever peak
        (26, 34, 't28', render_frame_t28_absurdity_stickman),    # absurdity
        (34, 40, 't36', render_frame_t36_calendar_stickman),     # 40-day cycle
    ]

    # Pre-render each card once
    card_cache = {}
    for _, _, card_name, render_fn in schedule:
        if card_name not in card_cache:
            print(f"Pre-rendering card: {card_name}")
            card_cache[card_name] = render_fn(PAL)

    # Render frames with cross-fades
    for frame_idx in range(total_frames):
        t = frame_idx / FPS

        # Find active card(s)
        current_card = None
        next_card = None
        blend_alpha = 0.0

        for i, (t_start, t_end, card_name, _) in enumerate(schedule):
            if t_start <= t < t_end:
                current_card = card_name
                # Check for cross-fade to next card (0.4s transition)
                if i + 1 < len(schedule):
                    next_t_start = schedule[i + 1][0]
                    fade_duration = 0.4
                    fade_start = t_end - fade_duration
                    if fade_start <= t < t_end:
                        next_card = schedule[i + 1][2]
                        blend_alpha = (t - fade_start) / fade_duration
                break

        # Blend frames if in transition
        if next_card and blend_alpha > 0:
            img1 = card_cache[current_card]
            img2 = card_cache[next_card]
            img = Image.blend(img1, img2, blend_alpha)
        elif current_card:
            img = card_cache[current_card].copy()
        else:
            # Fallback: black frame
            img = Image.new('RGB', (W, H), (0, 0, 0))

        # Save frame
        frame_path = os.path.join(args.out, f'frame_{frame_idx:04d}.png')
        img.save(frame_path)

        if frame_idx % 60 == 0:
            print(f"  Frame {frame_idx}/{total_frames} (t={t:.2f}s)")

    print(f"Rendered {total_frames} frames to {args.out}/")
    print("Done.")


if __name__ == '__main__':
    main()
