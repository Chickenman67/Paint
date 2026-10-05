# work/lib/v2draw.py -- the v2 drawing primitives: paper, title, labels,
# red-marker overlays, and speech bubbles.
#
# These are the four text/overlay devices observed in work/ref2/ref_full.mp4, plus
# the page itself. Nothing here fades, tweens, or moves a layout element; the bar
# changes what is ON the page, not where the page elements sit. Motion lives in
# the v2engine pop scheduler, not here.
#
# Geometry contract (measured, STYLE_CANON2.md sec 2):
#   title cap top y=21, baseline y=67, centred at x=640. draw_title() places the
#   glyph box so the CAP TOP lands on TITLE_TOP_Y -- verified with the check in
#   lib/v2type.py and the specimen renders under work/ref2/.

import math
import random

from PIL import Image, ImageDraw

try:
    from . import v2type as T
    from . import v2paint as PA
except ImportError:
    import v2type as T            # imported flat
    import v2paint as PA          # imported flat


# --------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------

def page(seed=0, textured=True):
    """A page. Every card starts here.

    PAINTERLY (round-2 critic finding #3): the page used to be a single exact
    # #fdfdfd value across all 921600 pixels -- a dead field. The bar's page has
    tooth: a couple of levels of per-pixel grain plus a broad low-frequency
    blotch. Both are clipped hard (see v2paint.PAPER_GRAIN/BLOTCH) because the
    brief is "felt, not seen" -- anything stronger starts to look like a dirty
    scan and competes with the art.
    """
    img = Image.new("RGB", (T.W, T.H), T.PAPER)
    if textured:
        PA.paper_overlay(img, seed=seed)
    return img


# --------------------------------------------------------------------------
# title -- persistent chapter title, drawn on the art, no band, no outline
# --------------------------------------------------------------------------

_GLYPH_PAD = 30   # tile margin around one glyph, so rotation never clips it


def _wobble_glyph(ch, font, rot_deg, pad=_GLYPH_PAD):
    """Render one glyph into a small RGBA tile, rotated, ready to paste.

    The glyph INK TOP is placed at exactly `pad` px from the tile's top edge, so
    pasting the tile at screen y = (target_top - pad) lands the ink top on the
    target row.
    """
    r = font.getbbox(ch)
    gw, gh = max(1, r[2] - r[0]), max(1, r[3] - r[1])
    tile = Image.new("RGBA", (gw + pad * 2, gh + pad * 2 + 8), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.text((pad - r[0], pad - r[1]), ch, font=font, fill=T.INK + (255,))
    if rot_deg:
        tile = tile.rotate(rot_deg, resample=Image.BICUBIC)
    return tile, gw, gh


def draw_title(img, text, center_x=None, seed=0, rot=None, dy=None):
    """Draw the persistent chapter title with the bar's per-letter wobble.

    The glyph CAP TOP is pinned to TITLE_TOP_Y (21) and the block is centred on
    TITLE_CENTER_X. Per-letter rotation and baseline offset come from a seeded
    RNG so a title wobbles identically on every re-render.

    Returns the (x0, x1) horizontal extent actually inked.
    """
    center_x = T.TITLE_CENTER_X if center_x is None else center_x
    rot = T.TITLE_ROT_DEG if rot is None else rot
    dy = T.TITLE_DY_PX if dy is None else dy
    font = T.title_font()

    rnd = random.Random(seed ^ 0x5EED)
    advs = [font.getlength(ch) for ch in text]
    total = sum(advs)
    x = center_x - total / 2.0

    x0_seen, x1_seen = center_x, center_x
    for ch, adv in zip(text, advs):
        if ch.strip():
            r = rnd.uniform(-rot, rot)
            tile, gw, gh = _wobble_glyph(ch, font, r)
            oy = T.TITLE_TOP_Y + rnd.uniform(-dy, dy)
            img.paste(tile, (int(x - _GLYPH_PAD), int(oy - _GLYPH_PAD)), tile)
            x0_seen = min(x0_seen, x)
            x1_seen = max(x1_seen, x + adv)
        x += adv
    return x0_seen, x1_seen


# --------------------------------------------------------------------------
# labels -- short in-art text, never a narration line
# --------------------------------------------------------------------------

def _text_size(draw, text, font):
    x0, y0, x1, y1 = font.getbbox(text)
    return x1 - x0, y1 - y0


# Label type stops growing at about 48px -- the style canon's band is 28-48 --
# but the BEAT type goes far past it: 'AREA 51' at 120, 'CLOSED' at 120,
# 'KENTUCKY' at 118, 'PINE GAP' at 104, 'TONNES' at 104. There are 33 such
# calls in the nine bunker scenes.
#
# The keyline used to be size*0.13 at every size, which is right in the canon
# band (38 -> 5px, 48 -> 6px) and wrong well above it. PIL's stroke_width
# expands the glyph BOTH ways, so a 15.6px stroke on a 120pt word (stems only
# ~15px wide) eats the counters: 'AREA 51' rendered as one solid black slab with
# a few holes in it, which is the exact failure the user reported -- "text
# should never be gray or black because its hard to see". A keyline is meant to
# outline a letter, and at that ratio it IS the letter.
#
# So hold the canon band's arithmetic exactly, then make the weight SUBLINEAR
# above it: continuous at 48, growing as size**0.45 instead of size. 120pt gets
# a 9px keyline rather than 16. Nothing at 28-56px changes by a single pixel,
# which is what keeps this from regressing the other ~300 labels in the film.
KEYLINE_BAND = 48
KEYLINE_BAND_W = 6.24          # 48 * 0.13, so the curve is continuous


def keyline_w(size):
    if size <= KEYLINE_BAND:
        return max(2, int(round(size * 0.13)))
    return max(2, int(round(KEYLINE_BAND_W * ((float(size) / KEYLINE_BAND) ** 0.45))))


def draw_label(img, text, xy=None, color=None, size=None, center=None, bold=True,
               outline=None, outline_w=None):
    """Draw a short label. xy is top-left; center=(x,y) centres it on that point.

    color defaults to yellow highlighter; pass T.LABEL_RED / LABEL_BLUE / LABEL_INK.

    OUTLINE: the bar's COLOURED labels are not flat fills -- they carry a black
    keyline (its red "East" is red text inside a black outline). So any label
    whose colour is not INK gets a black outline by default. Pass outline_w=0
    to force flat, or outline=INK to force it on an INK label.
    """
    color = T.LABEL_YELLOW if color is None else color
    if outline is None and color != T.INK:
        outline = T.INK
    # Only pass the stroke to PIL when there is genuinely a stroke colour to
    # draw. PIL does NOT treat `stroke_width=n, stroke_fill=None` as "no
    # stroke" -- it expands the glyphs into a solid blob, so an INK label came
    # out as an illegible black smear. It was worse than that: the old line
    # read `stroke_fill: outline or T.INK`, so a None outline silently became
    # INK and the "no outline" case stroked anyway. Verified by rendering both
    # forms side by side. Default outline_w stays as the marker-pen weight for
    # COLOURED labels, which is what the bar actually does.
    if outline is not None and outline_w is None:
        outline_w = keyline_w(size or T.LABEL_PX)
    font = T.load_font(size or T.LABEL_PX, bold=bold)
    d = ImageDraw.Draw(img)
    tw, th = _text_size(d, text, font)
    x, y = xy if xy is not None else (0, 0)
    if center is not None:
        x, y = center[0] - tw // 2, center[1] - th // 2
    kw = {}
    if outline is not None and (outline_w or 0) > 0:
        kw = {'stroke_width': outline_w, 'stroke_fill': outline}
    d.text((x, y), text, font=font, fill=color, **kw)
    return (x, y, tw, th)


def draw_number(img, text, center, color=None, size=None, outline=None):
    """A single big number doing the talking. Centred on `center`."""
    color = T.INK if color is None else color
    if outline is None and color != T.INK:
        outline = T.INK
    font = T.load_font(size or T.NUM_PX, bold=True)
    d = ImageDraw.Draw(img)
    tw, th = _text_size(d, text, font)
    ow = max(3, int(round((size or T.NUM_PX) * 0.10)))
    kw = {}
    if outline:
        kw = {'stroke_width': ow, 'stroke_fill': outline}
    d.text((center[0] - tw // 2, center[1] - th // 2), text, font=font,
           fill=color, **kw)
    return (center[0] - tw // 2, center[1] - th // 2, tw, th)


# --------------------------------------------------------------------------
# speech bubble
# --------------------------------------------------------------------------

def draw_bubble(img, text, xy, tail_to=None, font_size=None, max_w=None):
    """Rounded white bubble, black edge, small tail. Text inside, short (2-6 words).

    xy is the bubble's top-left. tail_to=(x,y) aims the tail at the speaker's
    mouth. Returns the bubble box (x0,y0,x1,y1).
    """
    font = T.load_font(font_size or T.BUBBLE_PX, bold=True)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    # Honour explicit newlines BEFORE width-wrapping. v1 collapsed the whole
    # string to one `lines` entry when its measured width fit max_w, but
    # d.text() still renders the embedded \n as two lines, so the second line
    # fell outside the bubble's computed height and its border cut straight
    # through the text. Split on \n first, then wrap each segment.
    lines = []
    for para in text.split('\n'):
        tw, th = _text_size(probe, para, font)
        if max_w and tw > max_w:                 # wrap on spaces
            words = para.split()
            cur = ""
            for w in words:
                t = (cur + " " + w).strip()
                if _text_size(probe, t, font)[0] <= max_w or not cur:
                    cur = t
                else:
                    lines.append(cur); cur = w
            lines.append(cur)
        else:
            lines.append(para)
    th = max(_text_size(probe, l, font)[1] for l in lines)

    lh = th + 8
    bw = max(_text_size(probe, l, font)[0] for l in lines) + T.BUBBLE_PAD * 2
    bh = lh * len(lines) + T.BUBBLE_PAD * 2 - 8
    x0, y0 = xy
    x1, y1 = x0 + bw, y0 + bh

    d = ImageDraw.Draw(img)
    # PAINTERLY: rounded_rectangle -> polygon + hand_stroke. A PIL rounded rect
    # has a mathematically constant border width and a perfect corner radius,
    # which is exactly what a speech bubble must not look like.
    rrect = PA.round_rect_pts(x0, y0, x1, y1, T.BUBBLE_RADIUS)
    PA.fill_poly(img, rrect, T.BUBBLE_FILL, seed=0xB0 + int(x0), edge=1.2)
    PA.hand_stroke(d, rrect, T.BUBBLE_EDGE, T.BUBBLE_EDGE_W, closed=True,
                   seed=0xB1 + int(x0), vary=0.30)
    # tail: a small triangle hanging off the bottom edge, drawn as a filled
    # polygon then outlined on its two outer edges only -- so no seam line
    # crosses the bubble interior.
    if tail_to:
        ty = tail_to[1]
        tx = min(max(tail_to[0], x0 + 14), x1 - 14)
        ax = x0 + bw * 0.30 if tail_to[0] < x0 else x1 - bw * 0.30
        bx = ax + 26
        apex = (tx, max(ty, y1 + 6))
        tail = [(ax, y1 - 1), apex, (bx, y1 - 1)]
        PA.fill_poly(img, PA.wobble_edge(tail, seed=0xB2 + int(x0), amount=1.4,
                                         wavelength=26.0), T.BUBBLE_FILL,
                     value=0.0, tint=0.0, band=0.0, edge=0.0)
        PA.hand_stroke(d, [(ax, y1 - 1), apex], T.BUBBLE_EDGE,
                       T.BUBBLE_EDGE_W, closed=False, seed=0xB3 + int(x0))
        PA.hand_stroke(d, [(bx, y1 - 1), apex], T.BUBBLE_EDGE,
                       T.BUBBLE_EDGE_W, closed=False, seed=0xB4 + int(x0))

    ty = y0 + T.BUBBLE_PAD - 4
    for line in lines:
        lw, _ = _text_size(probe, line, font)
        d.text((x0 + (bw - lw) // 2, ty), line, font=font, fill=T.INK)
        ty += lh
    return (x0, y0, x1, y1)


# --------------------------------------------------------------------------
# red-marker overlays -- the bar's "look here" pen
# --------------------------------------------------------------------------

def draw_arrow(img, start, end, color=None, width=12, head=52, bow=0.0):
    """A thick directional arrow with a solid triangular head.

    Matches the bar's main 'look here' arrow (its black "East" arrow): straight
    shaft, heavy line, solid head. The head is deliberately large (head=52) --
    at head=34 the first pass rendered a nub on a shaft that read as a stray
    stroke rather than an arrow. pass bow>0 for a gentle curve.
    color defaults to INK (black); pass T.RED for the red marker-pen variant.
    """
    color = T.INK if color is None else color
    (x0, y0), (x1, y1) = start, end
    if bow:
        cx = (x0 + x1) / 2 - (y1 - y0) * bow
        cy = (y0 + y1) / 2 + (x1 - x0) * bow
        pts = []
        steps = 28
        for i in range(steps + 1):
            t = i / steps
            px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
            py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
            pts.append((px, py))
    else:
        pts = [(x0, y0), (x1, y1)]
    d = ImageDraw.Draw(img)

    # The head is a solid triangle whose BASE sits on the shaft end and whose
    # TIP points past it. Geometry: the shaft is drawn only to `end`; the head's
    # back edge is centred on `end`, half-width `hw`, perpendicular to the
    # direction; the apex is `head` forward of `end`. (The first pass offset the
    # base corners at +-1.05 rad from the endpoint, which made a lopsided thorn
    # jutting forward of the shaft instead of a centred arrowhead.)
    ax, ay = pts[-1]
    if len(pts) > 6:
        px, py = pts[-6]
    else:
        px, py = pts[0]
    ang = math.atan2(ay - py, ax - px)
    ux, uy = math.cos(ang), math.sin(ang)          # along the shaft
    nx, ny = -uy, ux                              # perpendicular
    hw = max(width * 0.85, head * 0.5)             # base half-width
    bx, by = ax - ux * head * 0.15, ay - uy * head * 0.15   # nudge base onto shaft
    # PAINTERLY: a marker-pen arrow has a shaft that swells as the hand presses
    # and a head whose edges are not two straight machine lines.
    PA.hand_stroke(d, pts, color, width, closed=False, seed=0xA1, vary=0.22,
                   wavelength=max(40.0, (x1 - x0 + y1 - y0) * 0.5))
    PA.fill_poly(img, PA.wobble_edge([(bx + nx * hw, by + ny * hw),
                                      (ax + ux * head, ay + uy * head),
                                      (bx - nx * hw, by - ny * hw)],
                                     seed=0xA2, amount=2.0, wavelength=head * 0.7),
                 color, value=0.0, tint=0.0, band=0.0, edge=0.0)
    return pts


def draw_red_box(img, box, color=None, width=5, rx=8):
    """A red highlight rectangle around a region (rounded, hand-drawn feel)."""
    color = T.RED if color is None else color
    d = ImageDraw.Draw(img)
    # PAINTERLY: "hand-drawn feel" was this function's stated INTENT all along,
    # but rounded_rectangle gives a constant-width border on a perfect-radius
    # corner. hand_stroke actually delivers the intent.
    PA.hand_stroke(d, PA.round_rect_pts(box[0], box[1], box[2], box[3], rx),
                   color, width, closed=True, seed=0xC1, vary=0.32,
                   wavelength=max(30.0, (box[2] - box[0]) * 0.4))


def draw_red_x(img, box, color=None, width=8):
    """A big red X struck over a box -- 'this does not happen'."""
    color = T.RED if color is None else color
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    pad = 6
    # one continuous hand-drawn stroke through the crossing point, not two
    # abutting straight lines whose join shows as a notch
    PA.hand_stroke(d, [(x0 + pad, y0 + pad), ((x0 + x1) / 2.0, (y0 + y1) / 2.0),
                       (x1 - pad, y1 - pad)], color, width, closed=False,
                   seed=0xD1, vary=0.26)
    PA.hand_stroke(d, [(x0 + pad, y1 - pad), ((x0 + x1) / 2.0, (y0 + y1) / 2.0),
                       (x1 - pad, y0 + pad)], color, width, closed=False,
                   seed=0xD2, vary=0.26)


def draw_circle_marks(img, box, color=None, width=5, n=5, seed=0):
    """A scatter of hollow yellow circles -- the bar's 'huh?' device for confusion."""
    color = T.YELLOW if color is None else color
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    for i in range(n):
        cx = rnd.uniform(x0, x1)
        cy = rnd.uniform(y0, y1)
        r = rnd.uniform(16, 30)
        # PAINTERLY: a ring whose line width breathes and whose circle is not
        # perfectly round (a hand cannot close a loop on the first pass).
        PA.hand_stroke(d, PA.ellipse_pts(cx, cy, r, r * rnd.uniform(0.92, 1.08),
                                         n=56), color, width, closed=True,
                       seed=seed ^ (0xE1 + i), vary=0.30, wavelength=r * 1.3)