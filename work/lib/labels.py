# work/lib/labels.py — label placement, contrast, leader lines, floating captions.
#
# WHY THIS EXISTS (measured gaps from work/lib/measure_frames_report.md +
#   the segment beat sheets for tres2b / wasp17b):
#
#   G4  ILLUSTRATED LABEL WITH NO CONTRAST.
#       tres2b beat_03 draws the planet name in near-black ON the near-black
#       planet disc. Completely illegible. wasp17b beat_06 draws "JUPITER-SIZED"
#       in white on a tan beam. Unreadable. The label has to read against
#       whatever ground it lands on, decided per-frame, not per-segment.
#       -> auto_contrast()
#
#   G5  LABEL COLLISION AND CLIPPING.
#       wasp17b beat_06 puts "JUPITER-SIZED" on top of the balance beam and clips
#       an orphan fragment off the left frame edge. A label must sit NEAR its
#       subject, never on it, and never cross the frame edge.
#       -> place_label() and leader_line()
#
# Everything here is style-neutral about the CONTENT of a card: it only decides
# where a piece of text may legally sit and what colour it may legally be. All
# type comes from the locked scale in work/lib/type.py (comicbd.ttf / comic.ttf,
# HEADER 48 / LABEL 32 / CAPTION 28 / STAMP 15). Do not add a size or a font
# here; if a caller needs a hero word it goes through type.load_font_at().
#
# THE STROKE TRAP (see memory: "Hero word must account for stroke").
#   Clamping against the font's advance width is NOT enough. PIL draws the
#   stroke OUTSIDE the glyphs, so a label clamped to the frame edge using
#   font.getbbox() alone still loses its keyline to the crop. Every box in this
#   module is inflated by the stroke width on all four sides before it is
#   tested against the frame, and the box that is reported to the caller is the
#   INK box (glyphs + stroke), not the advance box.

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.type import (  # noqa: E402  (path shim must run first)
    CAPTION_PX,
    CAPTION_STROKE,
    H,
    LABEL_PX,
    STAMP_PX,
    W,
    load_font,
)
from lib.ink import DETAIL, FINE, INK, wobble_points  # noqa: E402
from lib.palette import YELLOW_CAPTION  # noqa: E402

try:  # numpy is present in this repo (work/lib/measure_frames.py) but degrade.
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None


# --- Locked constants -------------------------------------------------------

MARGIN = 16          # minimum gap between any label ink box and the frame edge
CAPTION_COLOR = YELLOW_CAPTION   # #FAB20B, the reference's caption yellow
MIN_CONTRAST = 4.5   # WCAG AA for large text; below this the caller gets outline
MID_TONE_LUMA = (0.18, 0.62)     # grounds that read as neither light nor dark
MID_TONE_CONTRAST = 7.0          # on a mid-tone ground only a strong ratio reads

# "Busy ground" threshold, in the SAME 0..1 linear-luminance units the sample
# reports. Calibrated by measuring real card regions with this module's own
# sampler: flat / stippled-only grounds land at std 0.000-0.089, while regions
# carrying linework, a two-tone boundary or a shape edge land at 0.143-0.387
# (work/segments/{tres2b,wasp17b}/cardsheet/beat_{03,06}.png). 0.12 sits in
# that gap: flat grounds keep a flat fill, contested grounds get the keyline.
BUSY_STD = 0.12


class Contrast(tuple):
    """The answer from auto_contrast().

    It IS an RGB triple, so it can be handed straight to
    draw.text(fill=...) / draw.rectangle(fill=...) with no unpacking. The
    extra attributes are the decision record:

        .mode   "dark" | "light" | "outline"
        .luma   relative luminance of the sampled ground, 0..1
        .ratio  WCAG contrast ratio of the returned colour against that ground
        .std    luma spread of the ground (business)
        .pad    the box that was sampled, in image coords

    mode == "outline" means neither flat option is safe on this ground: draw
    the glyph in `dark` (or whatever the caller prefers) WITH an ink outline
    or a light halo behind it. See outline_text().
    """

    def __new__(cls, color, mode, luma, ratio, std, pad):
        self = super().__new__(cls, tuple(int(c) for c in color))
        self.mode = mode
        self.luma = float(luma)
        self.ratio = float(ratio)
        self.std = float(std)
        self.pad = tuple(pad)
        return self

    @property
    def needs_outline(self):
        return self.mode == "outline"

    def __repr__(self):  # pragma: no cover - debugging aid
        return ("Contrast(rgb=%s, mode=%s, luma=%.3f, ratio=%.2f, std=%.1f)"
                % (tuple(self), self.mode, self.luma, self.ratio, self.std))


class PlacedLabel(object):
    """What place_label() decided, so a caller can draw a leader to it."""

    __slots__ = ("text", "box", "xy", "fill", "mode", "lines", "line_h",
                 "clamped", "avoided", "leader", "font")

    def __init__(self, text, box, xy, fill, mode, lines, line_h, clamped,
                 avoided, leader, font):
        self.text = text
        self.box = box          # (x0, y0, x1, y1) INK box, inside the frame
        self.xy = xy            # (x, y) top-left of the INK box
        self.fill = fill        # Contrast (an RGB triple with .mode)
        self.mode = mode        # "dark" | "light" | "outline"
        self.lines = lines
        self.line_h = line_h
        self.clamped = clamped  # True if no candidate fit and we had to clamp
        self.avoided = avoided  # True if the final box clears every avoid region
        self.leader = leader    # None, or (from_xy, to_xy) for leader_line()
        self.font = font

    def as_dict(self):
        return {
            "text": self.text, "box": self.box, "xy": self.xy,
            "fill": tuple(self.fill), "mode": self.mode,
            "clamped": self.clamped, "avoided": self.avoided,
        }

    def __repr__(self):  # pragma: no cover - debugging aid
        return ("PlacedLabel(%r, box=%s, mode=%s, clamped=%s, avoided=%s)"
                % (self.text, self.box, self.mode, self.clamped, self.avoided))


# --- Contrast maths ---------------------------------------------------------

def _rel_luma(rgb):
    """WCAG relative luminance of an sRGB triple, 0..1."""
    out = 0.0
    for c, w in zip(rgb, (0.2126, 0.7152, 0.0722)):
        v = c / 255.0
        v = v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        out += w * v
    return out


def contrast_ratio(rgb_a, rgb_b):
    """WCAG contrast ratio between two colours, 1.0 .. 21.0."""
    la, lb = _rel_luma(rgb_a), _rel_luma(rgb_b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


# --- Box maths --------------------------------------------------------------

def text_ink_box(font, text, stroke=0):
    """Ink box (glyphs + stroke) of a single line, in draw-offset coords.

    PIL's font.getbbox returns offsets from the draw origin using the default
    'la' anchor, so drawing at (X, Y) puts ink in
    [X + x0, X + x1] x [Y + y0, Y + y1]. The stroke is drawn OUTSIDE that, so
    it is inflated by `stroke` here. The caller adds the draw origin back.
    """
    try:
        x0, y0, x1, y1 = font.getbbox(text)
    except Exception:
        w = max(8, int(len(text) * font.size * 0.55))
        return 0, 0, w, int(font.size * 1.2)
    return x0 - stroke, y0 - stroke, x1 + stroke, y1 + stroke


def _lines_of(text):
    if isinstance(text, (list, tuple)):
        return [str(t) for t in text]
    return str(text).split("\n")


def _layout(text, font, stroke=0, line_gap=None):
    """Measure a (possibly multi-line) block.

    Returns (lines, draw_x, draw_y, w, h, line_h, tops) where
    (draw_x, draw_y) is the single draw origin that puts the block's INK box
    top-left corner at (0, 0) in block-local coordinates, and `tops[i]` is the
    extra y offset (relative to that origin) for line i's own ink top. Line 0
    is always 0, so a single-line block is just the plain draw origin.
    """
    lines = _lines_of(text)
    gap = line_gap if line_gap is not None else max(2, int(stroke))
    boxes = [text_ink_box(font, ln, stroke) for ln in lines]
    heights = [b[3] - b[1] for b in boxes]
    widths = [b[2] - b[0] for b in boxes]
    w = max(widths) if widths else 0
    h = sum(heights) + gap * max(0, len(lines) - 1)
    # The draw origin's y is chosen so line 0's INK top lands at local y=0.
    draw_x = -boxes[0][0] if boxes else 0
    draw_y = -boxes[0][1] if boxes else 0
    # Line i is drawn at draw_y + (sum of line 0..i-1 heights + gaps). Its ink
    # top relative to the block's ink top is that offset + boxes[i][1] - boxes[0][1].
    tops = []
    acc = 0
    for i, b in enumerate(boxes):
        tops.append(acc + b[1] - boxes[0][1])
        acc += heights[i] + gap
    line_h = (heights[0] + gap) if boxes else 0
    return lines, draw_x, draw_y, w, h, (line_h or 1), tops


def _draw_block(draw, xy, lines, font, draw_x, draw_y, tops, fill, stroke,
                stroke_fill, line_h):
    """Draw a measured block with its INK box top-left at `xy`."""
    x, y = xy
    for i, ln in enumerate(lines):
        if not ln:
            continue
        draw.text((x + draw_x, y + draw_y + tops[i]), ln, font=font, fill=fill,
                  stroke_width=stroke, stroke_fill=stroke_fill)


# --- G4: auto_contrast ------------------------------------------------------

def auto_contrast(img, text, xy, dark=(0, 0, 0), light=(255, 255, 255),
                 size_px=LABEL_PX, bold=False, stroke=0, font=None,
                 expand=4, min_contrast=MIN_CONTRAST,
                 mid_tone_contrast=MID_TONE_CONTRAST, busy_std=BUSY_STD):
    """Pick a text colour that reads against the ground behind `text`.

    `xy` is the TOP-LEFT of the label's INK box, matching the convention in
    work/lib/type.py. The box is grown by `expand` px before sampling so the
    sample is not decided by one stray pixel, and by the stroke width so the
    keyline is included.

    Returns a Contrast, which is an RGB triple you can pass to PIL directly.
    Check `.mode`:

        "dark"    -> return value is `dark`, it reads
        "light"   -> return value is `light`, it reads
        "outline" -> NEITHER flat option is safe. Draw the glyph in `dark`
                     with an ink outline / light halo. use outline_text().

    tres2b beat_03 (near-black label on a near-black disc) returns "light".
    wasp17b beat_06 (white label on a tan beam) returns "dark".
    A mid grey or a busy striped ground returns "outline".
    """
    if font is None:
        font = load_font(size_px, bold=bold)
    lines = _lines_of(text)
    _, dx, dy, bw, bh, _, tops = _layout(text, font, stroke)

    # The image-space box, padded for stroke and for the sample expand.
    pad = stroke + max(0, int(expand))
    x0 = int(math.floor(xy[0] - pad))
    y0 = int(math.floor(xy[1] - pad))
    x1 = int(math.ceil(xy[0] + bw + pad))
    y1 = int(math.ceil(xy[1] + bh + pad))

    W_, H_ = img.size
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W_, x1), min(H_, y1)
    pad_box = (cx0, cy0, cx1, cy1)

    if cx1 <= cx0 or cy1 <= cy0:
        # Entirely off-frame: nothing to sample. Black on an unknown ground is
        # the conservative pick; the caller will clamp the box anyway.
        return Contrast(dark, "dark", 0.5, 1.0, 0.0, pad_box)

    crop = img.crop(pad_box).convert("RGB")
    if _np is not None:
        a = _np.asarray(crop, dtype=_np.float32)
        v = a / 255.0  # normalise to 0..1 BEFORE the sRGB curve
        lin = _np.where(v <= 0.04045, v / 12.92,
                        ((v + 0.055) / 1.055) ** 2.4)
        lum = (0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2])
        luma = float(lum.mean())
        std = float(lum.std())
        # Mean RGB of the ground, used as the reference colour for the ratio.
        mean_rgb = tuple(int(round(c)) for c in a.reshape(-1, 3).mean(axis=0))
    else:  # pragma: no cover - PIL-only fallback
        px = list(crop.getdata())
        mean_rgb = tuple(int(round(sum(p[i] for p in px) / len(px))) for i in range(3))
        lums = [_rel_luma(p) for p in px]
        luma = sum(lums) / len(lums)
        std = math.sqrt(sum((v - luma) ** 2 for v in lums) / len(lums))

    r_dark = contrast_ratio(dark, mean_rgb)
    r_light = contrast_ratio(light, mean_rgb)
    if r_dark >= r_light:
        best, best_r, mode = dark, r_dark, "dark"
    else:
        best, best_r, mode = light, r_light, "light"

    mid = MID_TONE_LUMA[0] <= luma <= MID_TONE_LUMA[1]
    if best_r < min_contrast:
        mode = "outline"          # custom dark/light pair that is simply too close
    elif mid and best_r < mid_tone_contrast:
        # A mid-tone ground reads as neither light nor dark, so even a decent
        # ratio leaves the glyphs swimming. STYLE_CANON: put an outline or a
        # halo behind the glyphs.
        mode = "outline"
    elif std > busy_std:
        # Busy ground (stripes, stipple, linework): no flat fill is safe.
        mode = "outline"

    return Contrast(best, mode, luma, best_r, std, pad_box)


def outline_text(draw, xy, text, font=None, size_px=LABEL_PX, bold=False,
                 fill=(0, 0, 0), halo=(255, 255, 255), stroke=3,
                 stroke_fill=None):
    """Draw text that must survive any ground: a halo/outline keyline first.

    This is the "third option" auto_contrast() points at. For a mid-tone or
    busy ground the glyph gets a thick keyline in the opposite tone, which is
    exactly what the reference does for its integrated planet labels.
    Returns the INK box.
    """
    if font is None:
        font = load_font(size_px, bold=bold)
    if stroke_fill is None:
        stroke_fill = halo
    lines = _lines_of(text)
    _, dx, dy, bw, bh, _, tops = _layout(text, font, stroke)
    _draw_block(draw, xy, lines, font, dx, dy, tops, fill, stroke,
                stroke_fill, 0)
    return (int(xy[0]), int(xy[1]), int(xy[0] + bw), int(xy[1] + bh))


# --- G5: leader_line --------------------------------------------------------

def leader_line(draw, from_xy, to_xy, color=INK, width=DETAIL, seed=0,
                bow=0.10, wobble=1.4, dot=True, arrow=False, dot_r=None,
                taper=False):
    """A hand-drawn leader from a subject out to its label.

    The reference's leader lines (e.g. the NOW / THEN callouts) are not rulers:
    they bow slightly, wander a little, and end in a round blob or a small
    arrowhead. Built from the same low-frequency wobble as every other line in
    the project (work/lib/ink.py), because per-vertex jitter reads as static.

    from_xy  the point ON the subject (usually its edge, not its centre)
    to_xy    the point on the label the line should arrive at
    color    ink colour
    width    3-4 px is the locked scale for diagram detail (ink.DETAIL)
    bow      sideways bow as a fraction of the line length (0 = straight)
    dot      draw the round terminator blob at to_xy (reference default)
    arrow    draw a two-stroke arrowhead at to_xy instead of / as well as dot
    taper    thin the line toward to_xy (needs a manual 2-pass draw)

    Returns the dense point list, so a caller can keep other marks clear of it.
    """
    ax, ay = float(from_xy[0]), float(from_xy[1])
    bx, by = float(to_xy[0]), float(to_xy[1])
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return [(bx, by)]

    # Perpendicular for the bow.
    px, py = -dy / length, dx / length
    steps = max(6, min(48, int(length / 14)))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        # Single bow that starts and ends on the anchor points: this is the
        # reference's "slightly hand-pulled curve", not a random walk.
        off = bow * length * math.sin(math.pi * t)
        pts.append((ax + dx * t + px * off, ay + dy * t + py * off))

    pts = wobble_points(pts, seed=seed, amount=wobble,
                        wavelength=max(50.0, length * 0.6))

    if taper:
        # Two passes with decreasing width, the second covering the far half.
        half = len(pts) // 2
        draw.line(pts[:half + 1], fill=color, width=max(1, width), joint="curve")
        draw.line(pts[half:], fill=color, width=max(1, int(round(width * 0.6))),
                  joint="curve")
    else:
        draw.line(pts, fill=color, width=max(1, int(width)), joint="curve")

    if dot:
        r = dot_r if dot_r is not None else max(3, int(round(width * 1.15)))
        draw.ellipse([bx - r, by - r, bx + r, by + r], fill=color)

    if arrow:
        ang = math.atan2(by - ay, bx - ax)
        head = max(9, int(width * 3.2))
        spread = 0.52  # radians either side of the shaft
        for s in (spread, -spread):
            hx = bx - head * math.cos(ang - s)
            hy = by - head * math.sin(ang - s)
            draw.line([(hx, hy), (bx, by)], fill=color,
                      width=max(1, int(width * 0.8)))

    return pts


# --- G5: place_label --------------------------------------------------------

_DIR_VEC = {
    "right": (1.0, 0.0),
    "left": (-1.0, 0.0),
    "above": (0.0, -1.0),
    "below": (0.0, 1.0),
    "above-right": (0.7071, -0.7071),
    "above-left": (-0.7071, -0.7071),
    "below-right": (0.7071, 0.7071),
    "below-left": (-0.7071, 0.7071),
}

# Fallback order when the preferred direction has nowhere legal to go. Same
# side first (a label that flips across its subject is worse than one that
# slides above it), then the vertical neighbours, then the far side.
_FALLBACK = {
    "right": ("right", "above-right", "below-right", "above", "below",
              "left", "above-left", "below-left"),
    "left": ("left", "above-left", "below-left", "above", "below",
             "right", "above-right", "below-right"),
    "above": ("above", "above-right", "above-left", "right", "left",
              "below", "below-right", "below-left"),
    "below": ("below", "below-right", "below-left", "right", "left",
              "above", "above-right", "above-left"),
    "above-right": ("above-right", "above", "right", "below-right", "below",
                    "left", "below-left", "above-left"),
    "above-left": ("above-left", "above", "left", "below-left", "below",
                   "right", "below-right", "above-right"),
    "below-right": ("below-right", "below", "right", "above-right", "above",
                    "left", "above-left", "below-left"),
    "below-left": ("below-left", "below", "left", "above-left", "above",
                   "right", "above-right", "below-right"),
}
for _k in list(_DIR_VEC):
    _FALLBACK.setdefault(_k, tuple(_DIR_VEC))

_DISTANCES = (1.0, 1.35, 1.8, 2.4, 3.1, 4.0)


def _normalize_avoid(avoid, anchor, avoid_radius):
    """Accept None / a 4-tuple / a list of shapes; return a normalized list.

    A shape is ("box", (x0, y0, x1, y1)) or ("circle", (cx, cy, r)).
    """
    if avoid is None:
        return [("circle", (float(anchor[0]), float(anchor[1]),
                            float(avoid_radius)))]
    items = avoid if isinstance(avoid, (list, tuple)) and (
        len(avoid) == 0 or isinstance(avoid[0], (list, tuple)) and
        (len(avoid[0]) == 4 and all(isinstance(v, (int, float)) for v in avoid[0])
         or len(avoid[0]) == 3)) else [avoid]
    out = []
    for it in items:
        if len(it) == 4 and all(isinstance(v, (int, float)) for v in it):
            out.append(("box", tuple(float(v) for v in it)))
        elif len(it) == 3 and all(isinstance(v, (int, float)) for v in it):
            out.append(("circle", tuple(float(v) for v in it)))
        elif hasattr(it, "size"):  # a PIL region / bbox tuple subclass
            out.append(("box", tuple(float(v) for v in it)))
    return out or [("circle", (float(anchor[0]), float(anchor[1]),
                               float(avoid_radius)))]


def _rect_hits_box(rect, shape, gap):
    """Does rect (x0, y0, x1, y1) touch `shape` when `shape` is grown by gap?"""
    x0, y0, x1, y1 = rect
    kind, v = shape
    if kind == "box":
        sx0, sy0, sx1, sy1 = v[0] - gap, v[1] - gap, v[2] + gap, v[3] + gap
        return not (x1 <= sx0 or x0 >= sx1 or y1 <= sy0 or y0 >= sy1)
    cx, cy, r = v
    r += gap
    # Closest point on the rect to the circle centre.
    nx = min(max(cx, x0), x1)
    ny = min(max(cy, y0), y1)
    return (cx - nx) ** 2 + (cy - ny) ** 2 <= r * r


def _clearance(rect, shape):
    """Positive distance-ish score: >0 means clear of the shape."""
    x0, y0, x1, y1 = rect
    kind, v = shape
    if kind == "box":
        sx0, sy0, sx1, sy1 = v
        dx = max(sx0 - x1, x0 - sx1, 0.0)
        dy = max(sy0 - y1, y0 - sy1, 0.0)
        if dx == 0.0 and dy == 0.0:
            # Overlapping in one axis only -> use the other axis's gap.
            return max(min(abs(x1 - sx0), abs(x0 - sx1)),
                       min(abs(y1 - sy0), abs(y0 - sy1)))
        return math.hypot(dx, dy)
    cx, cy, r = v
    nx = min(max(cx, x0), x1)
    ny = min(max(cy, y0), y1)
    return math.hypot(cx - nx, cy - ny) - r


def _in_frame(box, margin, frame):
    fw, fh = frame
    x0, y0, x1, y1 = box
    return (x0 >= margin and y0 >= margin and
            x1 <= fw - margin and y1 <= fh - margin)


def _clamp_box(box, margin, frame):
    fw, fh = frame
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w > fw - 2 * margin:            # wider than the frame: centre it
        x0 = (fw - w) / 2.0
    else:
        x0 = min(max(x0, margin), fw - margin - w)
    if h > fh - 2 * margin:
        y0 = (fh - h) / 2.0
    else:
        y0 = min(max(y0, margin), fh - margin - h)
    return (x0, y0, x0 + w, y0 + h)


def place_label(img, text, anchor_xy, prefer="right", avoid=None,
                avoid_radius=96, offset=None, margin=MARGIN, gap=10,
                size_px=LABEL_PX, bold=False, font=None, fill=None,
                ink=INK, stroke=0, stroke_fill=None, contrast=True,
                dark=(0, 0, 0), light=(255, 255, 255), halo=(255, 255, 255),
                line_gap=None, seed=0, frame=None, leader=False,
                leader_color=None, leader_width=DETAIL, dot=True, arrow=False):
    """Draw a label NEAR a subject: never on it, never off the frame.

    This is the G5 fix. wasp17b beat_06 clipped an orphan text fragment off
    the left frame edge and printed "JUPITER-SIZED" straight onto the balance
    beam it was describing. Both are placement bugs and both are decided here
    rather than by the caller's arithmetic.

        img          an RGB/RGBA PIL Image (drawn into, not copied)
        text         the label; "\\n" makes a multi-line block
        anchor_xy    a point ON or NEAR the subject, usually its centre
        prefer       "right" | "left" | "above" | "below" | "above-right" |
                     "above-left" | "below-right" | "below-left", or an explicit
                     (dx, dy) direction pair. The label is tried here first.
        avoid        shapes the label must not touch. Accepts a 4-tuple box, a
                     (cx, cy, r) circle, or a list of either. Default: a circle
                     of `avoid_radius` around the anchor.
        avoid_radius radius of that default exclusion circle
        offset       first standoff in px from the anchor. DEFAULT None means
                     "just outside the subject", computed as
                     avoid_radius + gap + 10, so a label can never be told to
                     sit on the thing it is labelling by accident. The standoff
                     is then stepped outward (x1.35, x1.8, ...) as needed.
        margin       minimum gap to the frame edge (locked at 16)
        gap          extra px of clearance required from `avoid` shapes
        fill         explicit label colour. When given, `contrast` is skipped.
        contrast     when True (default) the colour is chosen by auto_contrast()
                     against the ground the label actually landed on, and an
                     "outline" verdict is honoured. This is the G4 fix.
        leader       also draw a leader_line from the anchor to the label, so
                     the association survives the label's distance
        frame        (w, h) override, defaults to the image size

    Returns a PlacedLabel. Check `.clamped` (True = nothing fit, we forced it)
    and `.avoided` (True = the final box clears every avoid shape).
    """
    if font is None:
        font = load_font(size_px, bold=bold)
    if frame is None:
        frame = img.size
    if offset is None:
        offset = avoid_radius + gap + 10

    lines = _lines_of(text)
    _, draw_x, draw_y, bw, bh, line_h, tops = _layout(text, font, stroke,
                                                      line_gap)
    shapes = _normalize_avoid(avoid, anchor_xy, avoid_radius)

    if isinstance(prefer, str):
        order = _FALLBACK.get(prefer.lower(), _FALLBACK["right"])
    elif prefer is None:
        order = _FALLBACK["right"]
    else:
        vx, vy = float(prefer[0]), float(prefer[1])
        m = math.hypot(vx, vy) or 1.0
        best = min(_DIR_VEC, key=lambda k: abs(
            _DIR_VEC[k][0] - vx / m) + abs(_DIR_VEC[k][1] - vy / m))
        order = _FALLBACK[best]

    ax, ay = float(anchor_xy[0]), float(anchor_xy[1])

    def box_for(vec, d):
        vx, vy = vec
        x = ax + vx * d - (bw if vx < 0 else 0.0)
        y = ay + vy * d - (bh if vy < 0 else 0.0)
        return (x, y, x + bw, y + bh)

    best_box = None
    best_key = None
    for key in order:
        vec = _DIR_VEC[key]
        for mult in _DISTANCES:
            d = offset * mult
            rect = box_for(vec, d)
            if not _in_frame(rect, margin, frame):
                continue
            if any(_rect_hits_box(rect, s, gap) for s in shapes):
                continue                       # this one lands ON the subject
            best_box, best_key = rect, (len(shapes), 0.0, mult)
            break
        if best_box is not None:
            break

    clamped = False
    avoided = True
    if best_box is None:
        # Nothing fit cleanly. Score every candidate: prefer in-frame, then
        # maximum clearance from the subject, then the smallest standoff.
        cands = []
        for key in order:
            vec = _DIR_VEC[key]
            for mult in _DISTANCES:
                d = offset * mult
                rect = box_for(vec, d)
                inset = min(rect[0] - margin, rect[1] - margin,
                            frame[0] - margin - rect[2],
                            frame[1] - margin - rect[3])
                clr = min([_clearance(rect, s) for s in shapes] or [0.0])
                fits = 1 if inset >= 0 else 0
                cands.append(((fits, round(min(clr, gap + 40.0), 2), -mult), rect))
        cands.sort(key=lambda t: t[0], reverse=True)
        best_box = cands[0][1]
        avoided = best_box is not None and not any(
            _rect_hits_box(best_box, s, gap) for s in shapes)
        clamped = True

    rect = _clamp_box(best_box, margin, frame)
    xy = (int(round(rect[0])), int(round(rect[1])))

    # Sample the ground the label will actually sit on, then draw.
    if fill is not None:
        choice = Contrast(fill, "explicit", 0.0, 0.0, 0.0,
                          (xy[0], xy[1], xy[0] + bw, xy[1] + bh))
    elif contrast:
        choice = auto_contrast(img, text, xy, dark=dark, light=light,
                               font=font, stroke=stroke)
    else:
        choice = Contrast(dark, "dark", 0.0, 0.0, 0.0,
                          (xy[0], xy[1], xy[0] + bw, xy[1] + bh))

    draw = ImageDraw.Draw(img)
    if choice.mode == "outline":
        outline_text(draw, xy, text, font=font, fill=dark, halo=halo,
                     stroke=max(3, stroke or 3), stroke_fill=stroke_fill)
    else:
        _draw_block(draw, xy, lines, font, draw_x, draw_y, tops,
                    tuple(choice), stroke, stroke_fill, line_h)

    # The leader arrives on the label's edge nearest the anchor, and starts
    # just outside the anchor's own exclusion circle so it never crosses the
    # silhouette it is labelling.
    lead = None
    if leader:
        near_x = rect[0] if ax < (rect[0] + rect[2]) / 2 else rect[2]
        near_y = rect[1] if ay < (rect[1] + rect[3]) / 2 else rect[3]
        sx, sy = ax, ay
        for kind, v in shapes:
            if kind != "circle":
                continue
            cx, cy, r = v
            if math.hypot(ax - cx, ay - cy) > r + 1:
                continue          # anchor already outside: start there
            # Anchor is inside the exclusion circle (usually dead centre of the
            # subject). Exit the circle heading for the label, not "stay put",
            # so the leader visibly emerges from the silhouette it labels.
            ux, uy = near_x - cx, near_y - cy
            m = math.hypot(ux, uy)
            if m < 1e-6:
                ux, uy, m = ax - cx, ay - cy, math.hypot(ax - cx, ay - cy)
            if m < 1e-6:
                ux, uy, m = 0.0, -1.0, 1.0
            sx = cx + ux / m * (r + 4)
            sy = cy + uy / m * (r + 4)
        leader_line(draw, (sx, sy), (near_x, near_y),
                    color=leader_color if leader_color is not None else ink,
                    width=leader_width, seed=seed, dot=dot, arrow=arrow)
        lead = ((sx, sy), (near_x, near_y))

    return PlacedLabel(text, (int(rect[0]), int(rect[1]),
                              int(math.ceil(rect[2])), int(math.ceil(rect[3]))),
                       xy, choice, choice.mode, lines, line_h, clamped,
                       avoided, lead, font)


# --- Floating caption -------------------------------------------------------

def wrap_lines(text, font, max_width, stroke=0):
    """Greedy word wrap to `max_width` measured on the INK box."""
    out = []
    for para in _lines_of(text):
        words = para.split(" ")
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            b = text_ink_box(font, trial, stroke)
            if (b[2] - b[0]) <= max_width or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = wd
        out.append(cur)
    return out


def caption(img, text, xy=None, anchor="center", color=CAPTION_COLOR,
            ink=INK, stroke=CAPTION_STROKE, size_px=CAPTION_PX, bold=True,
            font=None, max_width=None, margin=MARGIN, line_gap=None,
            wrap=True, frame=None):
    """The standard floating caption, in the locked type scale.

    The reference has NO caption band: the caption floats on the illustration
    in comicbd.ttf at 28 px, yellow #FAB20B, with a 3 px ink keyline. That is
    exactly work/lib/type.py's scale, so this function only adds the thing
    type.draw_caption() does not have: the label is guaranteed to sit inside
    the frame.

        xy        (x, y). Required unless anchor is "center".
        anchor    "top-left" | "center" | "bottom" | "top-right" | ... The
                  anchor names which point of the block lands on xy.
        max_width wrap width in px. Defaults to the frame width minus 2*margin,
                  which is what keeps a long caption inside the frame instead of
                  letting it run off the edge.
        margin    min gap to the frame edge (locked at 16)

    Returns the INK box (x0, y0, x1, y1).
    """
    if frame is None:
        frame = img.size
    if font is None:
        font = load_font(size_px, bold=bold)
    if max_width is None:
        max_width = frame[0] - 2 * margin

    if wrap:
        lines = wrap_lines(text, font, max_width, stroke)
    else:
        lines = _lines_of(text)

    _, draw_x, draw_y, bw, bh, line_h, tops = _layout("\n".join(lines), font,
                                                      stroke, line_gap)
    if xy is None:
        xy = (frame[0] / 2.0, frame[1] / 2.0)
    if isinstance(anchor, str) and "-" in anchor:
        hpart, vpart = anchor.split("-", 1)
    else:
        hpart, vpart = anchor, "top"

    x, y = float(xy[0]), float(xy[1])
    if hpart == "center":
        x -= bw / 2.0
    elif hpart == "right":
        x -= bw
    if vpart == "center":
        y -= bh / 2.0
    elif vpart == "bottom":
        y -= bh

    # Clamp with the STROKE included (see the note at the top of this file).
    box = _clamp_box((x, y, x + bw, y + bh), margin, frame)
    xy2 = (int(round(box[0])), int(round(box[1])))

    draw = ImageDraw.Draw(img)
    _draw_block(draw, xy2, lines, font, draw_x, draw_y, tops, color, stroke,
                ink, line_h)
    return (xy2[0], xy2[1], int(math.ceil(box[2])), int(math.ceil(box[3])))


def note(img, text, xy, size_px=STAMP_PX, color=(255, 255, 255),
         ink=(0, 0, 0), margin=MARGIN):
    """A tiny clamped annotation, for beat_11-style NOW / THEN callouts.

    Same locked stamp size as type.draw_stamp, plus the frame clamp, so an
    annotation can never be the thing that breaks a card.
    """
    return caption(img, text, xy=xy, anchor="top-left", color=color, ink=ink,
                   stroke=1, size_px=size_px, bold=False, wrap=False,
                   margin=margin)


# --- self-test --------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "study"))
    import labels_demo
    print(labels_demo.main())
