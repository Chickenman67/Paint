# work/lib/title_band.py — Clean white header band (the ref's signature).
#
# Per CLAUDE.md §7 (Card anatomy) + the round-2 critic verdict for HD 80606 b:
#   The reference uses a STRICT WHITE TITLE STRIP at the top of every card
#   (y=22..60) with CLEAN CONSOLAS BOLD ALL CAPS planet name, BLACK fill, NO
#   STROKE. Our round-1 used a black strip with wobbly yellow text — that was
#   the ref's "wobble signature" applied to the wrong element.
#
# This module provides:
#   - draw_title_band(image, text, color=(0,0,0), font=None) -> int y
#       Draws a 39-px-tall white rect at y=22..60 with the planet name in
#       clean Consolas Bold ALL CAPS, black fill, no stroke.
#       Returns the y-coordinate of the band bottom (so callers can layout
#       the content area below it).
#
# Callers should NOT call draw_header() (the wobbly hand-lettered one) on
# this layout. The title band replaces the header for Layout A (white band).

from PIL import Image, ImageDraw, ImageFont

import os
import sys

# Reuse the type-scale constants and font loader.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.type import (
    HEADER_PX, HEADER_STROKE, load_font,
    HEADER_STRIP_Y, HEADER_STRIP_H, W,
)

# The band is 39 px tall starting at y=22. This is the locked measurement
# from the reference; never change it.
BAND_Y = HEADER_STRIP_Y
BAND_H = HEADER_STRIP_H
BAND_BOTTOM = BAND_Y + BAND_H  # 61

# Default band color: pure white (255,255,255). Per ref.
BAND_COLOR = (255, 255, 255)

# Default text color: black. The reference uses BLACK on white for the
# segment header; never an accent color.
DEFAULT_INK = (0, 0, 0)


def draw_title_band(image, text, color=DEFAULT_INK, band_color=BAND_COLOR,
                    font=None, center_x=None):
    """Draw the white title band with the planet name in clean Consolas Bold.

    text:    the planet name (e.g. 'HD 80606 b'). We force ALL CAPS so
             passing 'HD 80606 b' and 'hd 80606 B' both render identically.
    color:   ink color for the text (default black).
    band_color: band background color (default white).
    font:    optional PIL ImageFont override (for tests).
    center_x: optional override for the band's horizontal center (default:
             image center).

    Returns the (x, y) of the rendered text bbox top-left.
    """
    if font is None:
        font = load_font(HEADER_PX, bold=True)

    draw = ImageDraw.Draw(image)

    # 1. White band background.
    if center_x is None:
        center_x = W // 2
    draw.rectangle(
        [0, BAND_Y, W, BAND_BOTTOM - 1],
        fill=band_color,
    )

    # 2. Force ALL CAPS — the reference never has lower-case letters in a
    #    segment header.
    text_upper = text.upper()

    # 3. Measure bbox and center horizontally inside the band.
    try:
        x0, y0, x1, y1 = font.getbbox(text_upper)
        bw, bh = x1 - x0, y1 - y0
    except Exception:
        bw, bh = len(text_upper) * 22, HEADER_PX

    x = center_x - bw // 2
    y = BAND_Y + (BAND_H - bh) // 2 - 2  # nudge to look right

    # 4. Draw the text — NO STROKE. The reference's header is a flat black
    #    sans-serif on white; no outline, no wobbly hand-lettered effect.
    draw.text((x, y), text_upper, font=font, fill=color)
    return x, y


def band_bottom():
    """Return the y-coordinate where the title band ends (61). Use this as
    the top of the content area when laying out cards.
    """
    return BAND_BOTTOM
