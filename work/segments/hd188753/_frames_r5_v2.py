# work/segments/hd188753/_frames_r5_v2.py — Round 5 v2 with PARADIGM SHIFT
#
# The core gap from all 5 rounds: stickman must be IN scenes not observing from margin.
# Using stickman_on_surface, stickman_in_space, stickman_with_environment functions
# to embed the character IN the triple-star world, experiencing the confusion.
#
# Audio: round_2_audio.wav, 64.64s
# Target: 1938 frames at 30fps

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lib')))
from stickman import stickman_on_surface, stickman_in_space, stickman_with_environment

# Type system
try:
    CONSOLAS_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 72)
    CAPTION_FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 32)
    STAMP_FONT = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 36)
except:
    CONSOLAS_BOLD = ImageFont.load_default()
    CAPTION_FONT = ImageFont.load_default()
    STAMP_FONT = ImageFont.load_default()

WIDTH, HEIGHT = 1280, 720
INK = (0, 0, 0)
CREAM = (245, 240, 230)

# Segment palette: warm oranges and yellows for triple-star system
ACCENT_YELLOW = (255, 200, 60)
ACCENT_ORANGE = (255, 140, 40)
ACCENT_RED = (200, 80, 60)
SURFACE_COLOR = (160, 120, 90)  # reddish moon surface


def draw_wobbly_text(draw, text, pos, font, fill, stroke_width=3):
    """Hand-lettered wobbly text"""
    import random
    random.seed(hash(text))
    x, y = pos
    for i, char in enumerate(text):
        jitter_x = random.randint(-2, 2)
        jitter_y = random.randint(-1, 1)
        char_x = x + jitter_x
        char_y = y + jitter_y
        # Stroke
        for dx in range(-stroke_width, stroke_width+1):
            for dy in range(-stroke_width, stroke_width+1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((char_x+dx, char_y+dy), char, font=font, fill=INK)
        # Fill
        draw.text((char_x, char_y), char, font=font, fill=fill)
        # Advance
        bbox = draw.textbbox((0, 0), char, font=font)
        x += (bbox[2] - bbox[0]) + 2


def draw_triple_suns(draw, sun_positions, sun_colors, sun_radii):
    """Draw three suns in the sky with slight glow"""
    for (sx, sy), color, radius in zip(sun_positions, sun_colors, sun_radii):
        # Glow
        for i in range(20, 0, -5):
            alpha = i / 20.0
            glow_r = radius + i
            draw.ellipse([sx - glow_r, sy - glow_r, sx + glow_r, sy + glow_r],
                        fill=(int(color[0] * alpha * 0.4),
                              int(color[1] * alpha * 0.4),
                              int(color[2] * alpha * 0.4)))
        # Sun body
        draw.ellipse([sx - radius, sy - radius, sx + radius, sy + radius],
                    fill=color, outline=INK, width=2)


def make_frame(t):
    """Generate frame at time t (seconds)"""

    # Timeline:
    # t=0-4: Intro card with planet name
    # t=4-10: Stickman on moon surface, THREE suns in sky, AWED expression (KEY SCENE)
    # t=10-16: Stickman in space between suns, showing scale (KEY SCENE)
    # t=16-24: Environmental shot with stickman on planet watching orbit
    # t=24-32: Diagram of figure-8 orbit (data beat, stickman smaller but still present)
    # t=32-40: Stickman on surface, one sun setting another rising, SKEPTICAL expression (KEY SCENE)
    # t=40-50: Close-up on confusion - stickman looking up at shifting sky
    # t=50-64: Stickman floating/drifting in orbital path, SCARED expression (KEY SCENE)

    if t < 4:
        # Intro card
        img = Image.new('RGB', (WIDTH, HEIGHT), CREAM)
        draw = ImageDraw.Draw(img)
        draw_wobbly_text(draw, "HD 188753 Ab", (120, 60), CONSOLAS_BOLD, ACCENT_ORANGE)
        draw.text((80, 640), "The triple-star world where timekeeping breaks down",
                 font=CAPTION_FONT, fill=INK)
        return img

    elif t < 10:
        # t=2-10: KEY SCENE - Stickman on reddish moon surface, THREE suns visible, AWED
        # Using stickman_on_surface with custom sky to show three suns
        sky_top = (140, 100, 180)
        sky_horizon = (200, 140, 100)

        img = stickman_on_surface(
            expression='oval',  # wide-oval mouth for AWED
            pose='hands_up',    # arms up in awe
            surface_color=SURFACE_COLOR,
            sky_gradient=(sky_top, sky_horizon),
            ground_y_pct=0.68,
            stickman_height=140
        )

        # Add three suns to the sky
        draw = ImageDraw.Draw(img)
        sun_positions = [
            (320, 180),   # Yellow sun upper left
            (640, 140),   # Orange sun center high
            (960, 200)    # Red sun upper right
        ]
        sun_colors = [ACCENT_YELLOW, ACCENT_ORANGE, ACCENT_RED]
        sun_radii = [45, 50, 40]
        draw_triple_suns(draw, sun_positions, sun_colors, sun_radii)

        # Caption
        draw.text((80, 640), "Three suns in the sky — which one sets first?",
                 font=CAPTION_FONT, fill=INK)
        return img

    elif t < 16:
        # t=10-16: KEY SCENE - Stickman in space positioned between three suns
        # Using stickman_in_space with multiple bodies
        img = Image.new('RGB', (WIDTH, HEIGHT), (10, 10, 25))
        draw = ImageDraw.Draw(img)

        # Stars
        import random
        random.seed(42)
        for _ in range(100):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, HEIGHT)
            draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(220, 220, 240))

        # Three suns at different depths/sizes
        # Yellow sun (closest, largest)
        sun1_x, sun1_y = 280, 250
        sun1_r = 80
        for i in range(30, 0, -8):
            alpha = i / 30.0
            draw.ellipse([sun1_x - sun1_r - i, sun1_y - sun1_r - i,
                         sun1_x + sun1_r + i, sun1_y + sun1_r + i],
                        fill=(int(ACCENT_YELLOW[0] * alpha * 0.3),
                              int(ACCENT_YELLOW[1] * alpha * 0.3),
                              int(ACCENT_YELLOW[2] * alpha * 0.3)))
        draw.ellipse([sun1_x - sun1_r, sun1_y - sun1_r,
                     sun1_x + sun1_r, sun1_y + sun1_r],
                    fill=ACCENT_YELLOW, outline=INK, width=3)

        # Orange sun (mid-distance)
        sun2_x, sun2_y = 880, 200
        sun2_r = 60
        for i in range(25, 0, -7):
            alpha = i / 25.0
            draw.ellipse([sun2_x - sun2_r - i, sun2_y - sun2_r - i,
                         sun2_x + sun2_r + i, sun2_y + sun2_r + i],
                        fill=(int(ACCENT_ORANGE[0] * alpha * 0.3),
                              int(ACCENT_ORANGE[1] * alpha * 0.3),
                              int(ACCENT_ORANGE[2] * alpha * 0.3)))
        draw.ellipse([sun2_x - sun2_r, sun2_y - sun2_r,
                     sun2_x + sun2_r, sun2_y + sun2_r],
                    fill=ACCENT_ORANGE, outline=INK, width=2)

        # Red sun (farthest, smallest)
        sun3_x, sun3_y = 1000, 420
        sun3_r = 45
        for i in range(20, 0, -6):
            alpha = i / 20.0
            draw.ellipse([sun3_x - sun3_r - i, sun3_y - sun3_r - i,
                         sun3_x + sun3_r + i, sun3_y + sun3_r + i],
                        fill=(int(ACCENT_RED[0] * alpha * 0.3),
                              int(ACCENT_RED[1] * alpha * 0.3),
                              int(ACCENT_RED[2] * alpha * 0.3)))
        draw.ellipse([sun3_x - sun3_r, sun3_y - sun3_r,
                     sun3_x + sun3_r, sun3_y + sun3_r],
                    fill=ACCENT_RED, outline=INK, width=2)

        # Stickman floating in space (EMBEDDED in the stellar system)
        # Drawing manually to be small but visible
        stick_cx, stick_cy = 580, 480
        stick_h = 80
        head_r = 10

        # Head
        draw.ellipse([stick_cx - head_r, stick_cy - head_r,
                     stick_cx + head_r, stick_cy + head_r],
                    outline=INK, fill=(255, 255, 255), width=2)
        # Eyes
        draw.ellipse([stick_cx - 4, stick_cy - 2, stick_cx - 2, stick_cy], fill=INK)
        draw.ellipse([stick_cx + 2, stick_cy - 2, stick_cx + 4, stick_cy], fill=INK)
        # Mouth (zigzag for uncomfortable)
        mouth_y = stick_cy + 4
        for i in range(5):
            x1 = stick_cx - 5 + i * 2
            y1 = mouth_y + (1 if i % 2 == 0 else -1)
            x2 = stick_cx - 5 + (i+1) * 2
            y2 = mouth_y + (1 if (i+1) % 2 == 0 else -1)
            draw.line([(x1, y1), (x2, y2)], fill=INK, width=1)

        # Body
        neck_y = stick_cy + head_r
        hip_y = neck_y + 20
        draw.line([(stick_cx, neck_y), (stick_cx, hip_y)], fill=INK, width=2)

        # Arms (floating, asymmetric)
        draw.line([(stick_cx, neck_y + 4), (stick_cx - 18, neck_y + 14)], fill=INK, width=2)
        draw.line([(stick_cx, neck_y + 4), (stick_cx + 20, neck_y + 8)], fill=INK, width=2)
        draw.ellipse([stick_cx - 20, neck_y + 12, stick_cx - 16, neck_y + 16], fill=INK)
        draw.ellipse([stick_cx + 18, neck_y + 6, stick_cx + 22, neck_y + 10], fill=INK)

        # Legs (floating)
        draw.line([(stick_cx, hip_y), (stick_cx - 10, hip_y + 28)], fill=INK, width=2)
        draw.line([(stick_cx, hip_y), (stick_cx + 12, hip_y + 30)], fill=INK, width=2)
        draw.ellipse([stick_cx - 12, hip_y + 26, stick_cx - 8, hip_y + 30], fill=INK)
        draw.ellipse([stick_cx + 10, hip_y + 28, stick_cx + 14, hip_y + 32], fill=INK)

        draw.text((80, 640), "Lost in a stellar triangle",
                 font=CAPTION_FONT, fill=(220, 220, 220))
        return img

    elif t < 24:
        # t=16-24: Environmental shot - stickman on planet surface watching sky
        img = stickman_on_surface(
            expression='worried',
            pose='standing',
            surface_color=(140, 110, 80),
            sky_gradient=((180, 120, 100), (220, 160, 100)),
            ground_y_pct=0.72,
            stickman_height=120
        )

        draw = ImageDraw.Draw(img)

        # Two suns visible (third just set)
        draw_triple_suns(draw, [(420, 200), (900, 260)],
                        [ACCENT_YELLOW, ACCENT_ORANGE], [40, 48])

        # Orbital arc suggestion (figure-8 path sketch)
        import math
        for i in range(20):
            angle = i * math.pi / 10
            x = 640 + int(200 * math.sin(angle * 2))
            y = 180 + int(80 * math.sin(angle))
            draw.ellipse([x-2, y-2, x+2, y+2], fill=(100, 100, 120))

        draw.text((80, 640), "The planet traces a figure-8 through the system",
                 font=CAPTION_FONT, fill=INK)
        return img

    elif t < 32:
        # t=24-32: Figure-8 orbit diagram (data beat but stickman still present)
        img = Image.new('RGB', (WIDTH, HEIGHT), CREAM)
        draw = ImageDraw.Draw(img)

        # Three stars in triangular configuration
        star_positions = [(400, 280), (640, 180), (880, 280)]
        star_colors = [ACCENT_YELLOW, ACCENT_ORANGE, ACCENT_RED]
        for (sx, sy), color in zip(star_positions, star_colors):
            draw.ellipse([sx-35, sy-35, sx+35, sy+35], fill=color, outline=INK, width=2)

        # Figure-8 orbit path
        import math
        orbit_points = []
        for i in range(100):
            angle = i * 2 * math.pi / 100
            x = 640 + int(220 * math.sin(angle * 2))
            y = 240 + int(120 * math.sin(angle))
            orbit_points.append((x, y))

        for i in range(len(orbit_points)-1):
            draw.line([orbit_points[i], orbit_points[i+1]], fill=(80, 80, 100), width=2)

        # Small planet on the path
        planet_x, planet_y = orbit_points[int((t - 24) * 10) % 100]
        draw.ellipse([planet_x-12, planet_y-12, planet_x+12, planet_y+12],
                    fill=(100, 140, 180), outline=INK, width=2)

        # Stickman tiny but visible, on the planet
        stick_cx = planet_x
        stick_top = planet_y - 24
        stick_h = 20
        head_r = 3
        draw.ellipse([stick_cx-head_r, stick_top, stick_cx+head_r, stick_top+2*head_r],
                    fill=(255, 255, 255), outline=INK, width=1)
        draw.line([(stick_cx, stick_top+2*head_r), (stick_cx, stick_top+2*head_r+8)],
                 fill=INK, width=1)

        draw.text((80, 640), "Caught in gravitational chaos",
                 font=CAPTION_FONT, fill=INK)
        return img

    elif t < 40:
        # t=32-40: KEY SCENE - Stickman on surface, one sun setting another rising, SKEPTICAL
        img = stickman_on_surface(
            expression='skeptical',  # one brow raised
            pose='shrugged',
            surface_color=SURFACE_COLOR,
            sky_gradient=((100, 80, 140), (180, 120, 100)),
            ground_y_pct=0.70,
            stickman_height=135
        )

        draw = ImageDraw.Draw(img)

        # One sun low (setting)
        draw_triple_suns(draw, [(220, 440)], [ACCENT_RED], [55])

        # Another sun rising
        draw_triple_suns(draw, [(1000, 380)], [ACCENT_YELLOW], [50])

        # Shadows shifting (two shadow directions)
        horizon_y = int(HEIGHT * 0.70)
        # Shadow from red sun
        draw.polygon([(640, horizon_y-5), (580, horizon_y), (580, horizon_y+40), (640, horizon_y+40)],
                    fill=(80, 60, 50))
        # Shadow from yellow sun
        draw.polygon([(640, horizon_y-5), (700, horizon_y), (700, horizon_y+40), (640, horizon_y+40)],
                    fill=(90, 70, 60))

        draw.text((80, 640), "Sunset? Sunrise? Both? Neither?",
                 font=CAPTION_FONT, fill=INK)
        return img

    elif t < 50:
        # t=40-50: Close-up confusion - stickman looking up at shifting sky
        img = stickman_on_surface(
            expression='worried',
            pose='hands_up',
            surface_color=(150, 110, 85),
            sky_gradient=((160, 100, 120), (200, 140, 100)),
            ground_y_pct=0.75,
            stickman_height=180  # larger, closer view
        )

        draw = ImageDraw.Draw(img)

        # Sky shows multiple light sources creating complex lighting
        draw_triple_suns(draw, [(300, 150), (980, 200)],
                        [ACCENT_ORANGE, ACCENT_YELLOW], [38, 42])

        draw.text((80, 640), "The sky never settles into a pattern",
                 font=CAPTION_FONT, fill=INK)
        return img

    else:
        # t=50-64: KEY SCENE - Stickman floating/drifting in orbital path, SCARED
        # Show the stickman riding along the figure-8 path
        img = Image.new('RGB', (WIDTH, HEIGHT), (15, 15, 30))
        draw = ImageDraw.Draw(img)

        # Stars
        import random
        random.seed(123)
        for _ in range(120):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, HEIGHT)
            draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(200, 200, 220))

        # Three suns (smaller, more distant view)
        draw_triple_suns(draw, [(250, 300), (640, 180), (1030, 320)],
                        [ACCENT_YELLOW, ACCENT_ORANGE, ACCENT_RED],
                        [50, 55, 48])

        # Figure-8 path (faint)
        import math
        for i in range(80):
            angle = i * 2 * math.pi / 80
            x = 640 + int(280 * math.sin(angle * 2))
            y = 320 + int(150 * math.sin(angle))
            draw.ellipse([x-1, y-1, x+1, y+1], fill=(60, 60, 80))

        # Stickman floating along the path (SCARED expression)
        # Position moves along the figure-8
        progress = ((t - 50) / 14) % 1.0
        angle = progress * 2 * math.pi
        stick_cx = 640 + int(280 * math.sin(angle * 2))
        stick_cy = 320 + int(150 * math.sin(angle))

        stick_h = 110
        head_r = 14
        head_cy = stick_cy

        # Head
        draw.ellipse([stick_cx - head_r, head_cy - head_r,
                     stick_cx + head_r, head_cy + head_r],
                    outline=INK, fill=(255, 255, 255), width=2)
        # Eyes
        draw.ellipse([stick_cx - 5, head_cy - 3, stick_cx - 3, head_cy - 1], fill=INK)
        draw.ellipse([stick_cx + 3, head_cy - 3, stick_cx + 5, head_cy - 1], fill=INK)
        # Mouth (frown - upside-down arc for SCARED)
        draw.arc([stick_cx - 7, head_cy, stick_cx + 7, head_cy + 6],
                180, 360, fill=INK, width=2)

        # Body (tumbling pose)
        neck_y = head_cy + head_r
        hip_y = neck_y + 30
        draw.line([(stick_cx, neck_y), (stick_cx, hip_y)], fill=INK, width=2)

        # Arms flailing
        draw.line([(stick_cx, neck_y + 8), (stick_cx - 25, neck_y - 5)], fill=INK, width=2)
        draw.line([(stick_cx, neck_y + 8), (stick_cx + 28, neck_y + 2)], fill=INK, width=2)
        draw.ellipse([stick_cx - 27, neck_y - 7, stick_cx - 23, neck_y - 3], fill=INK)
        draw.ellipse([stick_cx + 26, neck_y, stick_cx + 30, neck_y + 4], fill=INK)

        # Legs flailing
        draw.line([(stick_cx, hip_y), (stick_cx - 15, hip_y + 35)], fill=INK, width=2)
        draw.line([(stick_cx, hip_y), (stick_cx + 18, hip_y + 38)], fill=INK, width=2)
        draw.ellipse([stick_cx - 17, hip_y + 33, stick_cx - 13, hip_y + 37], fill=INK)
        draw.ellipse([stick_cx + 16, hip_y + 36, stick_cx + 20, hip_y + 40], fill=INK)

        draw.text((80, 640), "Helpless in an infinite celestial dance",
                 font=CAPTION_FONT, fill=(220, 220, 220))
        return img


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', default='C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd188753')
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--duration', type=float, default=64.64)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    total_frames = int(args.duration * args.fps)
    print(f"Generating {total_frames} frames at {args.fps}fps for {args.duration}s")

    for i in range(total_frames):
        t = i / args.fps
        frame = make_frame(t)
        frame_path = os.path.join(args.out_dir, f"frame_{i:05d}.png")
        frame.save(frame_path)

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{total_frames} frames")

    print(f"Done. Frames saved to {args.out_dir}")


if __name__ == '__main__':
    main()
