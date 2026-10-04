# work/study/labels_demo.py — exercise every case in work/lib/labels.py.
#
# Renders ONE 1280x720 sheet containing twelve numbered tiles, one per case.
#
# WHY EACH CASE IS ITS OWN IMAGE (this was the first version's bug):
#   place_label() and caption() only know ONE frame, so when several cases were
#   drawn onto a single sheet they all fought over the same 1280x720 boundary.
#   A case anchored at a "cell" corner but placed against the real frame drifted
#   into its neighbours, and the long caption anchored at (W-2, H-2) wrapped
#   upward across the whole sheet. The fix is to give every case its own small
#   PIL image. That tile IS then the frame the module clamps to, so no case can
#   overlap another by construction, and the 16 px margin / no-clip guarantees
#   are exercised on a real edge exactly as they are on the 1280x720 frame
#   (the module is frame-size agnostic — _verify() below sweeps the full frame).
#
#   python work/study/labels_demo.py
#
# Writes work/study/labels_demo.png.

import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from lib import ink  # noqa: E402
from lib import labels  # noqa: E402
from lib.type import ART_TOP, H, HEADER_STRIP_BOTTOM, W, draw_header, load_font  # noqa: E402

OUT = os.path.join(HERE, "labels_demo.png")

PAPER = (247, 243, 233)
INK = (0, 0, 0)
TEAL = (44, 160, 160)
RED = (214, 62, 40)
GREY = (128, 128, 128)
TAN = (198, 168, 118)
NEAR_BLACK = (14, 12, 16)
MUTED = (120, 118, 112)
BORDER = (216, 212, 202)
BADGE = (226, 222, 212)
BADGE_INK = (70, 68, 64)

# --- Grid: 4 cols x 3 rows inside the 636 px art area (under the title strip).
PAD = 14
GAP = 14
COLS, ROWS = 4, 3
TILE_W = (W - 2 * PAD - GAP * (COLS - 1)) // COLS
TILE_H = ((H - ART_TOP) - 2 * PAD - GAP * (ROWS - 1)) // ROWS

# Reserve this much of a tile's top-left corner for the number badge so no case
# ever draws under it (and auto_contrast never samples it).
BADGE_W, BADGE_H = 30, 22

REPORT = []


def tile_pos(col, row):
    return (PAD + col * (TILE_W + GAP),
            ART_TOP + PAD + row * (TILE_H + GAP))


def new_tile():
    """A fresh self-contained mini-frame. Everything in a case draws here, and
    the label functions clamp to THIS rectangle, so cases cannot collide."""
    img = Image.new("RGB", (TILE_W, TILE_H), PAPER)
    return img, ImageDraw.Draw(img)


def stamp(sheet, x, y, n):
    """Draw the case number on the SHEET, in the tile's reserved top-left
    corner, on an opaque badge. Drawn after the paste so no case content can
    cover it (the busy-stripe case would otherwise bury its own number)."""
    sd = ImageDraw.Draw(sheet)
    sd.rectangle([x, y, x + BADGE_W, y + BADGE_H], fill=BADGE)
    labels.note(sheet, str(n), (x + 11, y + 5), color=BADGE_INK)


def inkbox(font, text, stroke=0):
    _, _, _, bw, bh, _, _ = labels._layout(text, font, stroke)
    return bw, bh


def L(sz=None, bold=True):
    return load_font(sz if sz is not None else labels.LABEL_PX, bold=bold)


def emit(sheet, col, row, n, tile_img, title, note):
    x, y = tile_pos(col, row)
    sheet.paste(tile_img, (x, y))
    # Border and badge go on LAST, on the sheet, so the paste can never cover
    # them. Drawing the border before the re-paste erased it.
    sd = ImageDraw.Draw(sheet)
    sd.rectangle([x, y, x + TILE_W - 1, y + TILE_H - 1], outline=BORDER, width=2)
    stamp(sheet, x, y, n)
    REPORT.append((title, note))


# ==========================================================================
#  CASES 1-4  the four edges. The requested direction points OFF the tile, so
#  place_label abandons it and puts the label inboard instead of letting it
#  clip against the edge (G5).
# ==========================================================================
def case_left(sheet, col, row, n):
    img, d = new_tile()
    ax, ay = 16, TILE_H // 2
    ink.draw_disc(d, ax, ay, 18, fill=TEAL, outline=INK, width=4)
    pl = labels.place_label(img, "LEFT", (ax, ay), prefer="left", offset=26,
                            avoid_radius=20, fill=INK)
    emit(sheet, col, row, n, img, "1  left-edge anchor, prefer=left (off-frame)",
         "disc at the tile's left edge; 'LEFT' is placed inboard at %s, "
         "clamped=%s — never clipped" % (pl.box, pl.clamped))


def case_right(sheet, col, row, n):
    img, d = new_tile()
    ax, ay = TILE_W - 16, TILE_H // 2
    ink.draw_disc(d, ax, ay, 18, fill=TEAL, outline=INK, width=4)
    pl = labels.place_label(img, "RIGHT", (ax, ay), prefer="right", offset=26,
                            avoid_radius=20, fill=INK)
    emit(sheet, col, row, n, img, "2  right-edge anchor, prefer=right (off-frame)",
         "disc at the right edge; 'RIGHT' flips to a legal inboard spot at %s, "
         "clamped=%s" % (pl.box, pl.clamped))


def case_top(sheet, col, row, n):
    img, d = new_tile()
    ax, ay = TILE_W // 2, 20
    ink.draw_disc(d, ax, ay, 18, fill=TEAL, outline=INK, width=4)
    pl = labels.place_label(img, "TOP", (ax, ay), prefer="above", offset=26,
                            avoid_radius=20, fill=INK)
    emit(sheet, col, row, n, img, "3  top-edge anchor, prefer=above (off-frame)",
         "disc at the top edge; 'TOP' drops below it, box %s, inside the 16 px "
         "margin" % (pl.box,))


def case_bottom(sheet, col, row, n):
    img, d = new_tile()
    ax, ay = TILE_W // 2, TILE_H - 20
    ink.draw_disc(d, ax, ay, 18, fill=TEAL, outline=INK, width=4)
    pl = labels.place_label(img, "BOTTOM", (ax, ay), prefer="below", offset=26,
                            avoid_radius=20, size_px=labels.STAMP_PX + 8,
                            fill=INK)
    emit(sheet, col, row, n, img, "4  bottom-edge anchor, prefer=below (off-frame)",
         "disc at the bottom edge; 'BOTTOM' rises above it, box %s, clamped=%s"
         % (pl.box, pl.clamped))


# ==========================================================================
#  CASE 5  G4 dark-on-dark. A near-black disc with the planet name on it, the
#  exact beat_03 defect. auto_contrast must return LIGHT.
# ==========================================================================
def case_dark_on_dark(sheet, col, row, n):
    img, d = new_tile()
    text = "TrES-2b"
    font = L()
    bw, bh = inkbox(font, text, 3)
    dcx, dcy = TILE_W // 2, TILE_H // 2 + 6
    r = int(max(bw, bh) / 2 + 22)
    ink.draw_disc(d, dcx, dcy, r, fill=NEAR_BLACK, outline=INK, width=5)
    lx, ly = dcx - bw // 2, dcy - bh // 2
    ch = labels.auto_contrast(img, text, (lx, ly), font=font, stroke=3)
    if ch.mode == "outline":
        labels.outline_text(d, (lx, ly), text, font=font, fill=(0, 0, 0),
                            halo=(255, 255, 255), stroke=3)
    else:
        d.text((lx, ly), text, font=font, fill=tuple(ch), stroke_width=3,
               stroke_fill=INK)
    emit(sheet, col, row, n, img, "5  dark-on-dark disc (G4, tres2b beat_03)",
         "near-black disc, auto_contrast -> %s %s, ratio %.1f — the same "
         "label in ink would be invisible" % (ch.mode.upper(), tuple(ch), ch.ratio))


# ==========================================================================
#  CASE 6  G4 light-on-light. A tan beam with JUPITER-SIZED on it, the exact
#  wasp17b beat_06 defect. auto_contrast must return DARK.
# ==========================================================================
def case_light_on_light(sheet, col, row, n):
    img, d = new_tile()
    text = "JUPITER-SIZED"
    font = L(labels.STAMP_PX + 10, bold=True)
    bw, bh = inkbox(font, text, 0)
    beam_h = bh + 26
    by = TILE_H // 2 - beam_h // 2
    d.rectangle([14, by, TILE_W - 14, by + beam_h], fill=TAN, outline=INK, width=5)
    lx = (TILE_W - bw) // 2
    ch = labels.auto_contrast(img, text, (lx, by + 13), font=font, stroke=0)
    d.text((lx, by + 13), text, font=font, fill=tuple(ch), stroke_width=0)
    emit(sheet, col, row, n, img, "6  light-on-light beam (G4, wasp17b beat_06)",
         "tan beam, auto_contrast -> %s %s, ratio %.1f — white-on-tan is what "
         "shipped" % (ch.mode.upper(), tuple(ch), ch.ratio))


# ==========================================================================
#  CASE 7  G4 third option, MID TONE. Neither black nor white clears the bar
#  on a mid ground, so mode == "outline" and the caller gets a keyline.
# ==========================================================================
def case_mid_tone(sheet, col, row, n):
    img, d = new_tile()
    text = "MID TONE"
    font = L(labels.STAMP_PX + 12, bold=True)
    bw, bh = inkbox(font, text, 3)
    dcx, dcy = TILE_W // 2, TILE_H // 2 + 4
    r = int(max(bw, bh) / 2 + 20)
    ink.draw_disc(d, dcx, dcy, r, fill=GREY, outline=INK, width=5)
    lx, ly = dcx - bw // 2, dcy - bh // 2
    ch = labels.auto_contrast(img, text, (lx, ly), font=font, stroke=3)
    labels.outline_text(d, (lx, ly), text, font=font, fill=(0, 0, 0),
                        halo=(255, 255, 255), stroke=3)
    emit(sheet, col, row, n, img, "7  mid-tone ground (G4 third option)",
         "grey disc, auto_contrast -> %s (luma %.2f, ratio %.1f): neither flat "
         "fill is safe, so a white keyline is drawn" % (ch.mode.upper(), ch.luma, ch.ratio))


# ==========================================================================
#  CASE 8  G4 third option again, BUSY. Fires on the luma SPREAD, not the mean,
#  so it catches linework/shape edges a mean-only test would average away.
# ==========================================================================
def case_busy(sheet, col, row, n):
    img, d = new_tile()
    text = "BUSY"
    font = L(labels.STAMP_PX + 12, bold=True)
    bw, bh = inkbox(font, text, 3)
    bx0, by0 = 12, 12
    bx1, by1 = TILE_W - 12, TILE_H - 12
    d.rectangle([bx0, by0, bx1, by1], fill=(238, 236, 228), outline=INK, width=4)
    for i in range(-(by1 - by0), (bx1 - bx0) + 60, 22):   # hard stripes
        d.line([(bx0 + i, by1), (bx0 + i + 70, by0)], fill=(92, 92, 92), width=7)
    lx = bx0 + ((bx1 - bx0) - bw) // 2
    ly = by0 + ((by1 - by0) - bh) // 2
    ch = labels.auto_contrast(img, text, (lx, ly), font=font, stroke=3)
    labels.outline_text(d, (lx, ly), text, font=font, fill=(0, 0, 0),
                        halo=(255, 255, 255), stroke=3)
    emit(sheet, col, row, n, img, "8  busy two-tone ground (G4 third option)",
         "striped panel, auto_contrast -> %s (luma %.2f, std %.3f): the SPREAD "
         "says no flat fill is safe" % (ch.mode.upper(), ch.luma, ch.std))


# ==========================================================================
#  CASES 9-10  G5 leader lines. The label sits clear of the subject and a
#  hand-drawn line joins them (dot terminator and arrowhead).
# ==========================================================================
def case_leader(sheet, col, row, n):
    img, d = new_tile()
    # 9: dot terminator
    sx, sy, sr = 58, TILE_H - 46, 26
    ink.draw_disc(d, sx, sy, sr, fill=TEAL, outline=INK, width=5)
    pl = labels.place_label(img, "MASS", (sx, sy), prefer="above",
                            avoid_radius=sr + 6, fill=INK, leader=True,
                            leader_width=ink.DETAIL, dot=True)
    # 10: arrowhead
    ax, ay, ar = TILE_W - 52, TILE_H - 46, 24
    ink.draw_disc(d, ax, ay, ar, fill=RED, outline=INK, width=5)
    pl2 = labels.place_label(img, "HEAT", (ax, ay), prefer="right",
                             avoid_radius=ar + 6, fill=INK, leader=True,
                             leader_width=ink.DETAIL, dot=False, arrow=True)
    emit(sheet, col, row, n, img,
         "9  leader line (dot) + 10 arrowhead leader",
         "labels %s and %s sit clear of their discs and are joined by wobbled "
         "leader lines" % (pl.box, pl2.box))


# ==========================================================================
#  CASE 11  G5 orphan fragment: a long label anchored hard against the left
#  edge. place_label keeps it inside the 16 px margin (the wasp17b beat_06
#  clipped-fragment bug).
# ==========================================================================
def case_orphan(sheet, col, row, n):
    img, d = new_tile()
    ax, ay = 8, TILE_H // 2
    ink.draw_disc(d, ax + 12, ay, 12, fill=RED, outline=INK, width=4)
    pl = labels.place_label(img, "ORPHAN-FRAGMENT-FIX", (ax + 12, ay),
                            prefer="right", offset=24, avoid_radius=16,
                            size_px=labels.STAMP_PX, fill=INK)
    emit(sheet, col, row, n, img, "11 long label anchored on the frame edge (G5)",
         "box %s — fully inside the %d px margin, clear of the disc, no clipped "
         "orphan" % (pl.box, labels.MARGIN))


# ==========================================================================
#  CASE 12  caption(). A long caption anchored at the tile's bottom-right
#  corner: it wraps and clamps instead of running off the edge.
# ==========================================================================
def case_caption(sheet, col, row, n):
    img, d = new_tile()
    cap = ("DARKER THAN COAL - IT ABSORBS OVER 99 PERCENT OF THE LIGHT THAT "
           "REACHES IT")
    box = labels.caption(img, cap, xy=(TILE_W - 2, TILE_H - 2),
                         anchor="bottom-right", color=labels.CAPTION_COLOR,
                         ink=INK, stroke=3, size_px=labels.STAMP_PX + 9,
                         max_width=TILE_W - 2 * labels.MARGIN)
    emit(sheet, col, row, n, img, "12 long caption anchored at the frame corner",
         "box %s — wrapped to the tile width and clamped to the %d px margin, "
         "stroke included" % (box, labels.MARGIN))


# ==========================================================================
#  Verify the two hard guarantees over a sweep at the real 1280x720 frame.
# ==========================================================================
def _verify():
    probe = Image.new("RGB", (W, H), PAPER)
    texts = ["TrES-2b", "JUPITER-SIZED", "MASS", "NOW", "THEN",
             "DARKER THAN COAL", "ORPHAN-FRAGMENT-FIX", "X", "200 MPH"]
    prefers = ["right", "left", "above", "below", "above-right",
               "above-left", "below-right", "below-left"]
    anchors = [(gx, gy)
               for gx in (0, 4, 20, 80, 200, 640, 1200, 1258, 1276, 1279)
               for gy in (0, 2, 30, 120, 400, 700, 718, 719)]
    bad_frame = bad_avoid = n = 0
    for (ax, ay) in anchors:
        for t in texts:
            for pr in prefers:
                n += 1
                pl = labels.place_label(probe, t, (ax, ay), prefer=pr,
                                        offset=30, avoid_radius=40, gap=10,
                                        contrast=False)
                b = pl.box
                if (b[0] < labels.MARGIN or b[1] < labels.MARGIN or
                        b[2] > W - labels.MARGIN or b[3] > H - labels.MARGIN):
                    bad_frame += 1
                if not pl.avoided:
                    bad_avoid += 1
    return n, bad_frame, bad_avoid


def main():
    sheet = Image.new("RGB", (W, H), PAPER)
    sd = ImageDraw.Draw(sheet)
    sd.rectangle([0, 0, W, HEADER_STRIP_BOTTOM - 1], fill=(255, 255, 255))
    draw_header(sd, "LABELS.PY", ink_rgb=INK)
    labels.note(sheet, "PLACEMENT / CONTRAST / LEADER / CAPTION", (W - PAD - 2, 34),
                color=MUTED)

    # Grid order left-to-right, top-to-bottom = ascending case number:
    #   row 0: 1 left  2 right  3 top  4 bottom
    #   row 1: 5 dark  6 light  7 mid-tone  8 busy
    #   row 2: 9+10 leader  11 orphan  12 caption
    case_left(sheet, 0, 0, 1)
    case_right(sheet, 1, 0, 2)
    case_top(sheet, 2, 0, 3)
    case_bottom(sheet, 3, 0, 4)
    case_dark_on_dark(sheet, 0, 1, 5)
    case_light_on_light(sheet, 1, 1, 6)
    case_mid_tone(sheet, 2, 1, 7)
    case_busy(sheet, 3, 1, 8)
    case_leader(sheet, 0, 2, 9)          # cases 9 and 10 share one tile
    case_orphan(sheet, 1, 2, 11)
    case_caption(sheet, 2, 2, 12)

    sd.rectangle([0, 0, W - 1, H - 1], outline=(214, 62, 40), width=2)
    sheet.save(OUT)

    n, bad_frame, bad_avoid = _verify()

    print("wrote %s" % OUT)
    print("")
    print("VERIFY  %d placements swept at %dx%d (9 texts x 8 directions x %d "
          "anchors, incl. all four frame edges)"
          % (n, W, H, n // (9 * 8)))
    print("VERIFY  %d outside the 16 px frame margin, %d overlapping the subject"
          % (bad_frame, bad_avoid))
    print("VERIFY  %s" % ("PASS - every box is inside the frame with >= 16 px "
                          "margin and clear of its subject"
                          if not (bad_frame or bad_avoid) else
                          "*** FAILED - a hard guarantee is broken ***"))
    print("")
    print("WHAT EACH CASE DEMONSTRATES")
    for title, note in REPORT:
        print("  %s" % title)
        print("      %s" % note)
    return OUT


if __name__ == "__main__":
    main()
