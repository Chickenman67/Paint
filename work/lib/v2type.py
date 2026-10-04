# work/lib/v2type.py -- the v2 type scale, per work/STYLE_CANON2.md.
#
# OVERRIDES work/lib/type.py, which is the v1 Paint-Explainer scale.
# Every number here was measured from frames extracted from work/ref2/ref_full.mp4,
# then cross-checked against the reference title rendered at the same cap height.
#
# WHAT CHANGED FROM v1
#   v1: Consolas (retired) then Comic Sans Bold (also wrong for this bar).
#   v2: Comic Neue Bold -- the rounded MONOLINE marker face the bar actually uses.
#       Verified by rendering "MEZHGORYE" at the measured 46 px cap height in
#       seven candidates and comparing glyph skeletons (work/ref2/_font_compare.png).
#   v2 has no "header strip". The bar puts the chapter title directly on the art
#   at a fixed baseline. There is no caption band and no outline stroke on the
#   title -- it is pure ink on the white page.
#
# THE ONE MEASUREMENT THAT MATTERS MOST: the title is PERSISTENT. It stays up for
# the whole chapter rather than appearing and disappearing per card. That is a
# structural change, not a styling one, and it is why the render loop treats the
# title as a separate layer from the card art.

import os

from PIL import ImageFont

# --- Frame -----------------------------------------------------------------
W, H = 1280, 720
FPS = 60                      # the bar is 60 fps; match it

# --- Colour (measured) -----------------------------------------------------
PAPER = (253, 253, 253)       # #fdfdfd -- the page. Not cream.
INK = (0, 0, 0)               # #000000 -- pure black. Dominates dark pixels 16:1.

# Marker accents. The bar draws attention with a red pen and a yellow highlighter
# ON TOP of the art, never as a caption band.
RED = (208, 30, 32)
YELLOW = (246, 224, 92)
BLUE = (58, 140, 214)
GREEN = (86, 140, 62)

# --- Title (measured) ------------------------------------------------------
# cap height 46 px, glyph top y=21, baseline y=67, horizontally centred.
TITLE_CAP_PX = 46
TITLE_TOP_Y = 21
TITLE_BASELINE_Y = 67
TITLE_CENTER_X = 640

# Per-letter wobble. The bar's letters are NOT on a common baseline and NOT
# square to each other -- each is rotated a couple of degrees and offset. This is
# what separates a real marker face from a system font pretending to be one.
TITLE_ROT_DEG = 2.6           # +/- around 0
TITLE_DY_PX = 2.2             # +/- around the baseline

# The persistent title is stamped on EVERY frame by engine3.render_frame, after
# every element, so it sits on top of the art rather than in a reserved band --
# there is no strip reserved for it. Anything else drawn in this range collides
# with it. This bit the bunkers build twice: cheyenne b04 printed an in-card
# D.draw_title("CHEYENNE MOUNTAIN") underneath the engine's own "Cheyenne
# Mountain" and the two overprinted into an unreadable smear, and nine fortknox
# captions placed at cy 64-112 crowded the glyphs.
#
# So: the title occupies roughly y = TITLE_TOP_Y - glyph_pad .. BASELINE_Y,
# i.e. about 14..68. Nothing else that must stay legible goes above this line.
TITLE_BAND_BOTTOM = 68
# First y a caption or in-card heading may occupy. Anything with a top edge
# above this and a bottom edge below 68 overlaps the title.
SAFE_TOP = 96

# --- In-frame text (measured off the contact sheets) -----------------------
# The bar's in-frame text is a SHORT LABEL (1-4 words) in one of three roles.
# It is never a line of narration. See STYLE_CANON2.md sec 6.
LABEL_PX = 34                 # general in-art label, e.g. "3 Feet thick"
LABEL_SM_PX = 28              # smaller variant
NUM_PX = 46                   # a single big number doing the talking
BUBBLE_PX = 30                # speech-bubble text

# Label colours by role, as observed:
LABEL_YELLOW = YELLOW         # highlighter: a fact about the thing
LABEL_RED = RED               # warning / the twist / emphasis
LABEL_BLUE = BLUE             # quantity / scale ("Millions of Gallons")
LABEL_INK = INK               # plain black, on its own

# --- Speech bubbles (measured) --------------------------------------------
BUBBLE_FILL = (255, 255, 255)
BUBBLE_EDGE = INK
BUBBLE_EDGE_W = 4
BUBBLE_RADIUS = 26
BUBBLE_PAD = 22

# --- Type family -----------------------------------------------------------
# Comic Neue Bold, SIL Open Font License, vendored at work/fonts/.
# No Windows system font matches: Segoe Print and Ink Free are handwriting
# (too cursive), Comic Sans is humanist (too even), Balsamiq is too geometric.
_HERE = os.path.dirname(os.path.abspath(__file__))
_FONT_DIRS = [
    os.path.abspath(os.path.join(_HERE, os.pardir, "fonts")),
    r"C:\Windows\Fonts",
]

_BOLD = ["ComicNeue-Bold.ttf", "comicbd.ttf", "segoeprb.ttf"]
_REG = ["ComicNeue-Bold.ttf", "comic.ttf", "segoepr.ttf"]   # the bar is monoline:
# there is no light weight on screen, so regular roles reuse Bold.


def find_font(*names):
    for d in _FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def load_font(size_px, bold=True):
    """Comic Neue Bold at size_px. Falls back through the system stack."""
    for n in (_BOLD if bold else _REG):
        path = find_font(n)
        if path:
            try:
                return ImageFont.truetype(path, size_px)
            except Exception:
                continue
    return ImageFont.load_default()


def font_at_cap(cap_px, bold=True):
    """Return a font whose CAP height is exactly cap_px.

    Title geometry is specified by cap height, not by point size, because that is
    how it was measured (46 px from the glyph top to the baseline). PIL's size is
    an em size, so it has to be solved for.
    """
    lo, hi = 8, 220
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(find_font(*_BOLD), mid)
        box = f.getbbox("H")
        caph = box[3] - box[1]
        if best is None or abs(caph - cap_px) < abs(best[1] - cap_px):
            best = (f, caph)
        if caph < cap_px:
            lo = mid + 1
        elif caph > cap_px:
            hi = mid - 1
        else:
            return f
    return best[0]


TITLE_FONT = None


def title_font():
    """The persistent chapter title face, solved once to the measured cap height."""
    global TITLE_FONT
    if TITLE_FONT is None:
        TITLE_FONT = font_at_cap(TITLE_CAP_PX, bold=True)
    return TITLE_FONT