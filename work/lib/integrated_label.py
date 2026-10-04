# work/lib/integrated_label.py — "So Close" integrated-label beat primitives.
#
# Per CLAUDE.md §4 + the round-2 critic verdict for HD 80606 b:
#   The reference uses INTEGRATED HAND-LETTERED LABELS that sit ON TOP of the
#   subject (planet, sun, etc.) — yellow text with a black outline, NOT a
#   floating caption. This is the emotional-punctuation beat type for the
#   segment's climax (the moment of closest approach).
#
# This module provides:
#   - draw_integrated_label(image, text, cx, cy, scale=1.0, seed=0) -> None
#       Hand-lettered yellow text with black outline, sitting at (cx, cy).
#       Each glyph has a slight per-character wobble; the outline is a
#       stack of 4-5 stroked text passes for the chunky comic-book look.
#   - draw_flame_halo(image, cx, cy, r, seed=0) -> None
#       A wobbly red-orange radial-gradient flame shape around a planet
#       (the visual cue for the "engulfed in fire" moment).

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.type import load_font


# --- Flame halo -------------------------------------------------------------

def draw_flame_halo(image, cx, cy, r, seed=0, palette=None):
    """Draw a wobbly red-orange flame halo around a disc at (cx, cy) r.

    Implementation:
      1. Build a radial gradient (yellow center -> orange -> red -> dark red)
         on a square sized 4r x 4r, then mask to a wobbly outer ring that
         is wider on the side facing the sun.
      2. Add flame-like protrusions (3-5 lobed bumps) around the rim for the
         "tongue of fire" silhouette.
      3. Stipple-overlay the whole thing.
    """
    if palette is None:
        palette = [
            (255, 220, 100),  # bright yellow
            (255, 130, 30),   # orange
            (239, 68, 3),     # red
            (120, 20, 6),     # dark red
        ]
    # We build a radial gradient on a large canvas then mask to a wobbly
    # annulus around the planet.
    pad = int(r * 1.6)
    side = 2 * r + 2 * pad
    grad = _radial_gradient_np(
        side,
        colors=palette,
        stops=[0.0, 0.3, 0.65, 1.0],
        center=(side / 2.0, side / 2.0),
    )

    # Build the flame mask: a wobbly outer ring with lobed protrusions.
    mask = Image.new('L', (side, side), 0)
    md = ImageDraw.Draw(mask)
    rng = random.Random(seed)

    # Outer wobbly disc with flame protrusions.
    n_verts = 96
    flame_pts = []
    n_flames = 9
    for i in range(n_verts):
        a = 2 * math.pi * i / n_verts
        # Modulate the radius by a sine pattern to make flame lobes.
        lobe = 0.18 * math.sin(n_flames * a + rng.uniform(0, 0.5))
        # Per-vertex jitter.
        jx = rng.uniform(-2.0, 2.0)
        rr = r + pad * (0.55 + lobe) + jx
        x = side / 2.0 + rr * math.cos(a)
        y = side / 2.0 + rr * math.sin(a)
        flame_pts.append((x, y))
    flame_pts.append(flame_pts[0])
    md.polygon(flame_pts, fill=255)

    # Punch out the inner planet so the halo only surrounds it.
    inner_pts = []
    for i in range(n_verts):
        a = 2 * math.pi * i / n_verts
        jx = rng.uniform(-0.6, 0.6)
        rr = r * 1.05 + jx
        x = side / 2.0 + rr * math.cos(a)
        y = side / 2.0 + rr * math.sin(a)
        inner_pts.append((x, y))
    inner_pts.append(inner_pts[0])
    md.polygon(inner_pts, fill=0)

    # Soften the halo edges a touch.
    halo_layer = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    halo_layer.paste(grad, (0, 0), mask)
    halo_layer = halo_layer.filter(ImageFilter.GaussianBlur(1.2))

    # Paste onto the image.
    image.paste(halo_layer, (int(cx - side / 2), int(cy - side / 2)), halo_layer)

    # Stipple the halo region for the painterly grain — masked to the
    # annulus so the grains don't leak into the surrounding background or
    # into the inner disc.
    halo_mask = Image.new('L', (side, side), 0)
    md2 = ImageDraw.Draw(halo_mask)
    md2.polygon(flame_pts, fill=255)
    md2.polygon(inner_pts, fill=0)  # exclude the inner planet area
    # Translate the local mask to image coordinates.
    full_mask = Image.new('L', image.size, 0)
    full_mask.paste(halo_mask, (int(cx - side / 2), int(cy - side / 2)))
    rng2 = random.Random(seed + 11)
    w, h = image.size
    px = image.load()
    mp = full_mask.load()
    # Bright yellow grains (the highlight).
    for _ in range(int(w * h * 0.010)):
        x = rng2.randint(0, w - 1)
        y = rng2.randint(0, h - 1)
        if mp[x, y] < 128:
            continue
        px[x, y] = (255, 230, 120)
    # Dark grains (the deep heat).
    for _ in range(int(w * h * 0.006)):
        x = rng2.randint(0, w - 1)
        y = rng2.randint(0, h - 1)
        if mp[x, y] < 128:
            continue
        px[x, y] = (60, 10, 4)


def _radial_gradient_np(size, colors, stops=None, center=None):
    """NumPy version of radial_gradient (used by draw_flame_halo)."""
    if stops is None:
        stops = [i / (len(colors) - 1) for i in range(len(colors))]
    n = size
    cx = center[0] if center else n / 2.0
    cy = center[1] if center else n / 2.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_d = math.sqrt((n / 2.0) ** 2 + (n / 2.0) ** 2)
    d = d / max_d
    cols = np.array(colors, dtype=np.float32)
    stops = np.array(stops, dtype=np.float32)
    out = np.zeros((n, n, 3), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(d, stops, cols[:, ch])
    out = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode='RGB')


# --- Integrated hand-lettered label ---------------------------------------

def draw_integrated_label(image, text, cx, cy, scale=1.0, seed=0,
                          fill=(250, 178, 11), outline=(0, 0, 0),
                          font=None):
    """Draw a hand-lettered label with chunky black outline at (cx, cy).

    Per the reference's "So Close" beat: yellow text with a thick black
    outline, sitting ON TOP of a planet. The text is rendered as a series
    of stroked text passes (1-2 px step) to build up a chunky outline that
    is robust to the underlying colors.
    """
    if font is None:
        # Use a chunky size. The reference's "So Close" is roughly 90-120 px
        # on a 720-tall frame.
        font = load_font(int(90 * scale), bold=True)

    text_upper = text.upper()
    draw = ImageDraw.Draw(image)

    # 1. Measure the text bbox so we can center it.
    try:
        x0, y0, x1, y1 = font.getbbox(text_upper)
        bw, bh = x1 - x0, y1 - y0
    except Exception:
        bw, bh = int(len(text_upper) * 50 * scale), int(80 * scale)
    x = int(cx - bw / 2)
    y = int(cy - bh / 2)

    # 2. Build the chunky outline by drawing the text multiple times with
    #    increasing stroke widths. This produces a "comic book" outline
    #    that survives any background.
    rng = random.Random(seed)
    for i in range(6, 0, -1):
        # Slight per-pass jitter for a hand-lettered feel.
        jx = rng.randint(-1, 1) if i <= 3 else 0
        jy = rng.randint(-1, 1) if i <= 3 else 0
        draw.text(
            (x + jx, y + jy),
            text_upper,
            font=font,
            fill=outline,
            stroke_width=i,
            stroke_fill=outline,
        )
    # 3. Final pass: the yellow fill, no stroke, on top.
    draw.text((x, y), text_upper, font=font, fill=fill)

    return (x, y, bw, bh)
