# work/lib/type.py — Locked type scale, per work/STYLE_CANON.md §2.
#
# CORRECTION (measured, not opinion): the reference does NOT use Consolas/a monospace
# face. It uses a rounded casual hand. Verified by eye on frames extracted directly
# from work/ref_full.mp4 (t=5 header "HD 188753 AB", t=256 header "PSR B1257+12") and
# confirmed with a rendered specimen sheet (work/study/font_specimen.png):
#   - Header + caption : bold rounded geometric sans, ALL CAPS  -> comicbd.ttf
#   - Label + stamp    : lighter casual hand, title-case       -> comic.ttf
# Consolas is a monospace typewriter face and reads as "computer terminal", which is
# the single largest style mismatch this file previously had.
#
# The reference also uses TWO treatments (bold header vs lighter in-illustration
# planet label), not one family. See t=200 (3x2 grid) for the label treatment.

from PIL import Image, ImageDraw, ImageFont
import os
import platform

# --- Locked type scale (STYLE_CANON.md §2) ---
HEADER_PX = 48      # bold rounded caps, in the 84 px title strip
LABEL_PX = 32       # casual hand, planet labels (grid cards / on-planet)
CAPTION_PX = 28     # bold rounded caps, floating ON the illustration
STAMP_PX = 15       # tiny diagram annotation

HEADER_STROKE = 3   # ink keyline on header letters
CAPTION_STROKE = 3  # ink keyline so the caption reads on any art
STAMP_STROKE = 1

# Title strip occupies rows 0..83 (measured near-white band on a verified frame).
HEADER_STRIP_Y = 0
HEADER_STRIP_H = 84
HEADER_STRIP_BOTTOM = HEADER_STRIP_H  # 84

# Illustration runs strip-bottom to frame-bottom, full bleed, no side margins.
ART_TOP = HEADER_STRIP_BOTTOM
ART_H = 720 - ART_TOP

# Frame dimensions
W, H = 1280, 720

# --- Type family (free, local, Windows system fonts) ---
_FONT_DIRS = [
    r"C:\Windows\Fonts",
    "/usr/share/fonts/truetype",
    "/System/Library/Fonts",
]
# Bold rounded hand: headers + captions.
_BOLD = ["comicbd.ttf", "comicb.ttf", "ComicSansMS-Bold.ttf",
         "segoeprb.ttf", "DejaVuSans-Bold.ttf"]
# Light casual hand: planet labels + stamps.
_REG = ["comic.ttf", "comicms.ttf", "ComicSansMS.ttf",
        "segoepr.ttf", "DejaVuSans.ttf"]


def find_font(*names):
    for d in _FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def load_font(size_px, bold=False):
    """Load Consolas at a specific pixel size. Falls back to default if missing."""
    names = _BOLD if bold else _REG
    for n in names:
        path = find_font(n)
        if path:
            try:
                return ImageFont.truetype(path, size_px)
            except Exception:
                continue
    return ImageFont.load_default()


# --- Text drawing (outlined, like the reference) ---

def _bbox(draw, text, font):
    """Return (x, y, w, h) of text bbox using font.getbbox."""
    try:
        x0, y0, x1, y1 = font.getbbox(text)
        return x0, y0, x1 - x0, y1 - y0
    except Exception:
        try:
            w, h = draw.textsize(text, font=font)
            return 0, 0, w, h
        except Exception:
            return 0, 0, 100, 30


def draw_outlined_text(draw, xy, text, font, fill, stroke, stroke_width):
    """Draw text with a thick black outline and a colored fill (the reference style).

    xy: (x, y) — top-left of the bbox
    text: the string
    font: PIL ImageFont
    fill: RGB tuple — the inner color
    stroke: RGB tuple — the outline color
    stroke_width: px
    """
    # PIL's text with stroke_width draws the outline around the glyphs.
    draw.text(
        xy,
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke,
    )


def draw_header(draw, text, accent_rgb=None, ink_rgb=(0, 0, 0), center_x=None, fill_rgb=None):
    """Draw a planet-name header centered in the 84 px title strip.

    Per the reference the header letters are INK (black) on the paper strip.
    accent_rgb is accepted for call-site compatibility but ignored unless
    fill_rgb is explicitly given.

    Returns (x, y) of the bbox top-left.
    """
    if fill_rgb is None:
        fill_rgb = ink_rgb
    font = load_font(HEADER_PX, bold=True)
    bx, by, bw, bh = _bbox(draw, text, font)
    if center_x is None:
        center_x = W // 2
    x = center_x - bw // 2
    y = HEADER_STRIP_Y + (HEADER_STRIP_H - bh) // 2
    draw_outlined_text(draw, (x, y), text, font, fill=fill_rgb, stroke=ink_rgb, stroke_width=HEADER_STROKE)
    return x, y


def draw_label(draw, text, xy, ink_rgb=(0, 0, 0), center_x=None):
    """Draw a planet label in the LIGHT casual hand.

    This is the reference's SECOND type treatment (see t=200 grid cards:
    "HD 80606 b" / "TrES-2b" / "PSR B1257+12"). Lighter, smaller, title-case —
    distinct from the bold all-caps header. Usually ink on a paper strip.
    Pass center_x to center horizontally instead of using xy[0].
    """
    font = load_font(LABEL_PX, bold=False)
    bx, by, bw, bh = _bbox(draw, text, font)
    x = (center_x - bw // 2) if center_x is not None else xy[0]
    draw_outlined_text(draw, (x, xy[1]), text, font, fill=ink_rgb, stroke=ink_rgb, stroke_width=0)
    return x, xy[1]


def draw_caption(draw, text, xy, color_rgb=(240, 224, 64), ink_rgb=(0, 0, 0)):
    """Draw a floating caption at xy (top-left), ON the illustration.

    There is NO caption band in the reference — this text sits in whatever space
    the art leaves. Default color is the reference's yellow (#F0E040).
    """
    font = load_font(CAPTION_PX, bold=True)
    draw_outlined_text(draw, xy, text, font, fill=color_rgb, stroke=ink_rgb, stroke_width=CAPTION_STROKE)
    return _bbox(draw, text, font)


def draw_stamp(draw, text, xy, accent_rgb, ink_rgb=(0, 0, 0)):
    """Draw a small stamp/accent diagram annotation at xy."""
    font = load_font(STAMP_PX, bold=False)
    draw_outlined_text(draw, xy, text, font, fill=accent_rgb, stroke=ink_rgb, stroke_width=STAMP_STROKE)
    return _bbox(draw, text, font)


def load_font_at(size_px, bold=False):
    """Load the locked family at an arbitrary size. Builders that need an
    off-scale size (e.g. a hero headline) should go through here, never through
    Consolas, so the whole video stays in one family."""
    return load_font(size_px, bold=bold)
