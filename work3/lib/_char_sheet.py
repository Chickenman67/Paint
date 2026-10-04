"""Contact sheet for character3, for MY visual judgement.

Deliberately does not reuse any existing sheet generator: the one that produced
measure/_char3_sheet.png laid two rows out so they overlapped (the top row's
feet landed on the bottom row's head), which is a layout bug that made the
figures hard to read. This lays cells out on a strict grid with padding computed
from the figure height, so overlap is impossible by construction.

Usage:  python lib/_char_sheet.py [out.png]
"""

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import character3 as C  # noqa: E402

# Poses across, expressions down. Chosen to cover the ranges that matter:
# a relaxed default, the extremes of each arm, and the two body-height poses.
POSES = ['standing', 'pointing', 'handsup', 'shrug',
         'recoil', 'peeking', 'wave', 'armscrossed']
EXPRS = ['neutral', 'skeptic', 'worried', 'scared',
         'awed', 'smirk', 'shock', 'confused']

FIG_H = 300          # rendered figure height in px
PAD_X, PAD_Y = 26, 54
LABEL_H = 18
COLS, ROWS = len(POSES), len(EXPRS)

CELL_W = FIG_H * 0.85 + PAD_X * 2
CELL_H = FIG_H + PAD_Y + LABEL_H
W = int(CELL_W * COLS)
H = int(CELL_H * ROWS)


def build():
    img = Image.new('RGB', (W, H), (250, 250, 248))
    d = ImageDraw.Draw(img)
    for r, expr in enumerate(EXPRS):
        for c, pose in enumerate(POSES):
            x0 = c * CELL_W
            y0 = r * CELL_H
            # cell guide box (very light) so an overflow is obvious
            d.rectangle([x0 + 4, y0 + 4, x0 + CELL_W - 4, y0 + CELL_H - 4],
                        outline=(228, 228, 224))
            cx = x0 + CELL_W / 2.0
            y_feet = y0 + PAD_Y + FIG_H
            C.draw_character(img, cx, y_feet, FIG_H, pose=pose,
                             expression=expr, seed=c * 13 + r)
            d.text((x0 + CELL_W / 2 - 22, y0 + CELL_H - LABEL_H + 2),
                   '%s/%s' % (pose[:6], expr[:6]), fill=(90, 90, 95))
    for c, pose in enumerate(POSES):
        d.text((c * CELL_W + CELL_W / 2 - 24, 4), pose, fill=(40, 40, 45))
    return img


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir,
        'measure', '_char3_sheet2.png')
    out = os.path.abspath(out)
    im = build()
    im.save(out)
    print('wrote %s (%dx%d)' % (out, im.size[0], im.size[1]))