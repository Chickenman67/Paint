# work/lib/texture.py — Painterly rendering primitives for the Guantlet2 rebuild.
#
# Per CLAUDE.md §4 + round-2 critic feedback for HD 80606 b:
#   The reference's visual signature is a smooth RADIAL GRADIENT on stars and
#   planets (no banding) plus a STIPPLE texture overlay (spray-paint grain).
#   Flat-shaded discs read as cartoon clip-art; the gradient + stipple is what
#   makes the reference feel like The Paint Explainer.
#
# This module provides:
#   - radial_gradient(size, colors, stops) -> Image
#       Smooth radial gradient (centered) with N color stops, no banding.
#   - stipple_overlay(image, density, color, seed) -> None
#       Spray-paint grain overlay using deterministic random noise.
#   - banded_planet(image, base_rgb, n_bands, palette) -> None
#       Horizontal painterly bands (gas-giant signature) as semi-transparent
#       overlays on a disc region.
#   - sun_disc(draw, cx, cy, r, palette, seed=0) -> None
#       Convenience: painterly sun with radial gradient + stipple + halo.
#   - planet_disc(draw, cx, cy, r, base_rgb, palette, n_bands=4, seed=0) -> None
#       Convenience: painterly planet with banded texture + stipple + outline.
#
# All functions are original implementations — we are rendering the signature
# (gradient + stipple + bands), not the reference frames.

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# --- Radial gradient --------------------------------------------------------

def radial_gradient(size, colors, stops=None, center=None):
    """Return a square Image of `size` with a centered radial gradient.

    colors: list of RGB tuples (3 stops minimum for a smooth blend).
    stops:  list of float positions in [0.0, 1.0] for each color; if None,
            evenly spaced.
    center: (cx, cy) in pixel space (default: image center).
    """
    n = size
    if stops is None:
        stops = [i / (len(colors) - 1) for i in range(len(colors))]
    assert len(colors) == len(stops), "colors and stops must match in length"

    # Build a distance map from the center, normalized to [0, 1] at the
    # farthest corner.
    cx = center[0] if center else n / 2.0
    cy = center[1] if center else n / 2.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_d = math.sqrt((n / 2.0) ** 2 + (n / 2.0) ** 2)
    d = d / max_d  # 0 at center, 1 at corner

    # Pre-build the color arrays as float32 for blending.
    cols = np.array(colors, dtype=np.float32)  # shape (k, 3)
    stops = np.array(stops, dtype=np.float32)  # shape (k,)

    # For each pixel, find which segment of the gradient it falls in and
    # linearly interpolate.
    # We do this with np.interp per channel.
    out = np.zeros((n, n, 3), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(d, stops, cols[:, ch])

    out = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode='RGB')


# --- Stipple overlay --------------------------------------------------------

def stipple_overlay(image, density=0.02, color=(255, 255, 255), seed=0,
                    mask=None):
    """Overlay a deterministic spray-paint grain onto `image` (in place).

    density: fraction of pixels to sprinkle as grains (0.01 = 1%).
    color:   RGB tuple for the grain pixels.
    seed:    int — deterministic per-element seed.
    mask:    optional PIL 'L' mode mask image (same size as `image`).
             Only pixels where mask >= 128 receive grains. If None, every
             pixel is eligible. CRITICAL: pass a disc mask when stippling
             a planet/sun region so the grains don't leak into the
             surrounding background.
    """
    w, h = image.size
    rng = random.Random(seed)
    n = int(w * h * density)
    px = image.load()
    if mask is not None:
        mp = mask.load()
    else:
        mp = None
    for _ in range(n):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        if mp is not None and mp[x, y] < 128:
            continue
        px[x, y] = color


def soft_stipple(image, density=0.015, color=(255, 255, 255), seed=0,
                 mask=None):
    """Like stipple_overlay but spreads a small 2-3 px cluster per grain
    (the reference looks like spray-paint, not pixel dust).
    """
    w, h = image.size
    rng = random.Random(seed)
    n = int(w * h * density)
    px = image.load()
    if mask is not None:
        mp = mask.load()
    else:
        mp = None
    for _ in range(n):
        cx = rng.randint(0, w - 1)
        cy = rng.randint(0, h - 1)
        if mp is not None and mp[cx, cy] < 128:
            continue
        for _ in range(rng.randint(2, 4)):
            dx = rng.randint(-1, 1)
            dy = rng.randint(-1, 1)
            x, y = cx + dx, cy + dy
            if 0 <= x < w and 0 <= y < h:
                if mp is not None and mp[x, y] < 128:
                    continue
                px[x, y] = color


# --- Banded planet (gas-giant signature) -----------------------------------

def banded_planet(image, cx, cy, r, n_bands=4, palette=None, seed=0):
    """Draw horizontal painterly bands across a circular disc region.

    Soft, feathery bands like the reference — NOT hard opaque stripes.

    Each band is a SOLID color rectangle (no alpha), but with a soft top
    edge and a soft bottom edge achieved by compositing an alpha gradient
    mask. The rectangle fills the disc horizontally, then is composited
    with a Gaussian blur on the alpha channel so transitions between
    bands are feathery, not sharp.

    The result reads as the reference's soft gas-giant bands.
    """
    w, h = image.size
    if palette is None:
        palette = [
            (200, 200, 200),
            (160, 160, 160),
            (220, 220, 220),
            (140, 140, 140),
        ]
    rng = random.Random(seed)

    # Build the disc mask (255 inside disc, 0 outside).
    disc_mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )

    # For each band: build a SOLID-color band layer with a vertical alpha
    # gradient that's 0 at top, ramps up over the first ~30% of band_h,
    # stays at 1 for the middle, ramps down to 0 over the last ~30%, then
    # 0 below. This gives a SOFT top edge and a SOFT bottom edge on each
    # band, so adjacent bands feather into each other instead of cutting
    # hard.
    band_h = (2.0 * r) / n_bands
    feather = max(4, int(band_h * 0.35))  # feather zone, in pixels

    for i in range(n_bands):
        y0_band = int(cy - r + i * band_h)
        y1_band = int(cy - r + (i + 1) * band_h)
        col = palette[i % len(palette)]

        # Build a single-band RGBA layer.
        # Fill the band rect with the color, then build an alpha mask
        # with feathered top and bottom edges.
        band_w = 2 * r + 4
        band_h_px = y1_band - y0_band + 2 * feather
        # Pad with feather on top/bottom so the soft edges fully resolve.
        # The band_layer is positioned so the feathered edges land on the
        # actual band boundary.
        layer = Image.new('RGBA', (band_w, band_h_px), (*col, 255))
        alpha = np.zeros((band_h_px, band_w), dtype=np.float32)
        # Top feather: 0 -> 1 over [0, feather]
        # Solid: 1 in [feather, band_h_px - feather]
        # Bottom feather: 1 -> 0 over [band_h_px - feather, band_h_px]
        for row in range(band_h_px):
            if row < feather:
                alpha[row, :] = row / feather
            elif row >= band_h_px - feather:
                alpha[row, :] = max(0.0, (band_h_px - row) / feather)
            else:
                alpha[row, :] = 1.0
        # Mild per-row jitter so the band edges wobble like a hand-painted
        # stripe, not a clean ramp.
        for row in range(band_h_px):
            j = rng.uniform(0.85, 1.0)
            alpha[row, :] *= j
        # Slight horizontal Gaussian to soften the band edges further.
        alpha_img = Image.fromarray((alpha * 255).astype(np.uint8), mode='L')
        alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(1.5))
        layer.putalpha(alpha_img)

        # Clip to the disc: build a per-band disc mask, then composite.
        # The band's alpha already has feathered top/bottom; we also need
        # to clip the SIDES to the disc.
        # Build a horizontal mask: 1 inside the disc ellipse, 0 outside.
        # The band only occupies the middle band_h_px rows centered on
        # y0_band..y1_band, so we just need horizontal clipping.
        band_disc_mask = np.zeros((band_h_px, band_w), dtype=np.float32)
        for row in range(band_h_px):
            y = y0_band - feather + row
            if abs(y - cy) > r:
                continue  # outside disc vertically
            half_w_at_y = math.sqrt(max(0.0, r * r - (y - cy) ** 2))
            for col in range(band_w):
                x = cx - r - 2 + col
                if abs(x - cx) <= half_w_at_y:
                    band_disc_mask[row, col] = 1.0
        # Combine the band's feathered alpha with the disc clip.
        cur_alpha = np.array(layer.split()[-1], dtype=np.float32) / 255.0
        combined = cur_alpha * band_disc_mask
        layer.putalpha(Image.fromarray((combined * 255).astype(np.uint8), mode='L'))

        # Paste onto the image.
        image.paste(layer, (cx - r - 2, y0_band - feather), layer)


# --- Sun disc (convenience: painterly sun) ----------------------------------

def sun_disc(image, cx, cy, r, palette=None, seed=0, halo=True):
    """Render a painterly sun at (cx, cy) with radius r.

    Steps:
      1. Build a radial gradient (yellow center -> orange -> red) on a square
         alpha mask sized to (2r+pad).
      2. Paste it onto the parent image.
      3. Add a soft outer halo (faint red glow) if halo=True.
      4. Stipple-overlay for spray-paint grain.
      5. Wobbly black outline on top.
    """
    if palette is None:
        palette = {
            'core':  (255, 240, 130),    # bright yellow core
            'mid':   (250, 178, 11),     # warm yellow
            'outer': (239, 68, 3),       # red
            'halo':  (120, 20, 6),       # dark red halo
        }

    # 1. Build the radial gradient on a small image, with the center positioned
    #    at the actual pixel center of the disc.
    pad = 8
    side = 2 * r + 2 * pad
    sun_img = radial_gradient(
        side,
        colors=[palette['core'], palette['mid'], palette['outer']],
        stops=[0.0, 0.45, 1.0],
        center=(side / 2.0, side / 2.0),
    )

    # 2. Mask to a disc and paste onto a scratch layer.
    sun_mask = Image.new('L', sun_img.size, 0)
    ImageDraw.Draw(sun_mask).ellipse(
        [0, 0, side - 1, side - 1], fill=255
    )
    sun_layer = Image.new('RGBA', sun_img.size, (0, 0, 0, 0))
    sun_layer.paste(sun_img, (0, 0), sun_mask)

    # 3. Optional soft halo: a WARM solid-color ring drawn UNDER the sun
    #    body, with a feathered inner edge only. The outer edge is a hard
    #    cut. Why this approach: any alpha-blended halo against a light BG
    #    produces desaturated mud. The ref's halos look warm because the
    #    halo is essentially OPAQUE warm color. We use a halo_pad=18
    #    (smaller than before) so the warm color band reads as a real glow
    #    ring on the BG. Inner edge is feathered over 4 pixels so it
    #    doesn't have a hard line where it meets the sun body.
    if halo:
        halo_pad = 18
        halo_side = side + 2 * halo_pad
        halo_r_inner = side // 2 - 4     # start feather slightly inside sun
        halo_r_outer = side // 2 + halo_pad
        halo_color = palette['halo']
        # Build a SOLID color image, then feather only the inner edge so
        # the outer edge of the ring is a clean hard cut.
        halo_layer = Image.new('RGBA', (halo_side, halo_side),
                               (*halo_color, 255))
        # Make a soft-alpha mask: 255 for the ring, 0 outside, with a
        # feather at the INNER edge (3-4 pixels) so the halo blends into
        # the sun body.
        mask_arr = np.zeros((halo_side, halo_side), dtype=np.float32)
        yy, xx = np.mgrid[0:halo_side, 0:halo_side].astype(np.float32)
        d = np.sqrt((xx - halo_side / 2.0) ** 2 + (yy - halo_side / 2.0) ** 2)
        feather = 4
        # Inside halo_r_inner: 0 (transparent)
        # halo_r_inner .. halo_r_inner+feather: 0 -> 1 (feather)
        # halo_r_inner+feather .. halo_r_outer: 1 (opaque)
        # > halo_r_outer: 0 (transparent)
        m = np.where(d < halo_r_inner, 0.0,
            np.where(d < halo_r_inner + feather,
                     (d - halo_r_inner) / feather,
                     np.where(d <= halo_r_outer, 1.0, 0.0)))
        # The outer edge: ALSO feather it over 2 pixels so the hard cut
        # doesn't look like a stamp. Soft outer edge: ramp 1.0 at
        # halo_r_outer-2 down to 0 at halo_r_outer.
        outer_feather = 2
        m = np.where(d > halo_r_outer - outer_feather,
                     np.maximum(0, (halo_r_outer - d) / outer_feather) * m,
                     m)
        halo_mask = Image.fromarray((m * 255).astype(np.uint8), mode='L')
        halo_layer.putalpha(halo_mask)
        # Paste the halo first, so the sun body sits on top of it.
        image.paste(
            halo_layer,
            (int(cx - halo_side / 2), int(cy - halo_side / 2)),
            halo_layer,
        )

    # Paste the sun itself.
    image.paste(
        sun_layer,
        (int(cx - side / 2), int(cy - side / 2)),
        sun_layer,
    )

    # 4. Spray-paint grain: deterministic per-sun stipple, masked to the disc
    #    so the grain doesn't leak into the surrounding background.
    disc_mask = Image.new('L', image.size, 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )
    soft_stipple(image, density=0.04, color=(255, 245, 200),
                 seed=seed + 11, mask=disc_mask)

    # 5. Wobbly black outline on top.
    draw = ImageDraw.Draw(image)
    rng = random.Random(seed + 7)
    n_verts = 64
    pts = []
    for i in range(n_verts):
        a = 2 * math.pi * i / n_verts
        jx = rng.uniform(-1.0, 1.0)
        x = cx + (r + jx) * math.cos(a)
        y = cy + (r + jx) * math.sin(a)
        pts.append((x, y))
    pts.append(pts[0])
    draw.line(pts, fill=(0, 0, 0), width=4)


# --- Planet disc (convenience: painterly planet) ----------------------------

def planet_disc(image, cx, cy, r, base_rgb, palette=None,
                n_bands=4, seed=0, with_bands=True):
    """Render a painterly planet disc at (cx, cy) with radius r.

    Steps:
      1. Solid disc fill in base_rgb.
      2. Radial gradient overlay (lighter at center) for subtle dimensionality.
      3. Optional banded texture (gas-giant horizontal bands).
      4. Stipple-overlay for spray-paint grain.
      5. Wobbly black outline.
    """
    # 1. Solid disc fill (use draw for the rough wobbly fill).
    rng = random.Random(seed)
    n_verts = 64
    pts = []
    for i in range(n_verts):
        a = 2 * math.pi * i / n_verts
        jx = rng.uniform(-0.8, 0.8)
        x = cx + (r + jx) * math.cos(a)
        y = cy + (r + jx) * math.sin(a)
        pts.append((x, y))
    pts.append(pts[0])
    ImageDraw.Draw(image).polygon(pts, fill=base_rgb)

    # 2. Radial gradient overlay (highlight at the center).
    if palette is None:
        # Default: lighter version of base for center, deeper for edge.
        light = tuple(min(255, int(c * 1.25)) for c in base_rgb)
        deep = tuple(int(c * 0.7) for c in base_rgb)
    else:
        light = palette.get('light', base_rgb)
        deep = palette.get('deep', base_rgb)
    side = 2 * r + 4
    grad = radial_gradient(
        side,
        colors=[light, base_rgb, deep],
        stops=[0.0, 0.5, 1.0],
        center=(side / 2.0, side / 2.0),
    )
    # Mask to disc and paste as semi-transparent overlay.
    disc_mask = Image.new('L', grad.size, 0)
    ImageDraw.Draw(disc_mask).ellipse([0, 0, side - 1, side - 1], fill=180)
    image.paste(grad, (int(cx - side / 2), int(cy - side / 2)), disc_mask)

    # 3. Banded texture (the gas-giant signature).
    if with_bands:
        if palette is None or 'bands' not in (palette or {}):
            # Default bands: derived from base color.
            band_palette = [
                tuple(min(255, int(c * 1.2)) for c in base_rgb),
                tuple(int(c * 0.75) for c in base_rgb),
                tuple(min(255, int(c * 1.1)) for c in base_rgb),
                tuple(int(c * 0.6) for c in base_rgb),
            ]
        else:
            band_palette = palette['bands']
        banded_planet(image, cx, cy, r, n_bands=n_bands,
                      palette=band_palette, seed=seed + 3)

    # 4. Spray-paint grain on the disc region, masked so it doesn't leak
    #    into the surrounding background.
    disc_mask = Image.new('L', image.size, 0)
    ImageDraw.Draw(disc_mask).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=255
    )
    # Highlight grains: pale yellow in the bright parts (subtle).
    soft_stipple(image, density=0.012, color=(255, 245, 200),
                 seed=seed + 17, mask=disc_mask)
    # A few dark grains for texture.
    soft_stipple(image, density=0.006, color=(0, 0, 0),
                 seed=seed + 23, mask=disc_mask)

    # 5. Wobbly black outline (drawn last so it sits on top of everything).
    draw = ImageDraw.Draw(image)
    rng2 = random.Random(seed + 41)
    pts2 = []
    for i in range(n_verts):
        a = 2 * math.pi * i / n_verts
        jx = rng2.uniform(-1.0, 1.0)
        x = cx + (r + jx) * math.cos(a)
        y = cy + (r + jx) * math.sin(a)
        pts2.append((x, y))
    pts2.append(pts2[0])
    draw.line(pts2, fill=(0, 0, 0), width=4)
