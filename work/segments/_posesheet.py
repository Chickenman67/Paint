# _posesheet.py -- contact sheet of every pose in the stickman library, rendered
# at the SHIPPED size (260px tall, as wasp17b beat_04 uses) so shallow-bend
# defects that only appear at final scale are visible.
#
# WHY: a pose can have a real elbow in its data and still read as one straight
# stroke if the two segments are nearly collinear. That is invisible when the
# stickman is drawn large at 700px and shows up as a scarecrow T-arm at the 260px
# we actually ship. Every pose must be judged at ship size, on a ground line.
#
# The figure is drawn onto the cell image IN PLACE (draw_stickman returns a
# geometry dict, not a picture), so we keep the cell and paste it with itself
# as the mask.
#
# USAGE: python _posesheet.py [out.png]

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))

import stickman as S                                          # noqa: E402
from PIL import Image, ImageDraw                              # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else '_posesheet.png'
H = 260          # the height wasp17b beat_04 ships
CELL_W = 300
CELL_H = 330
COLS = 6

# Read the valid sets from the library itself so this sheet cannot drift: an
# unknown pose silently falls back to 'standing', which would show up here as
# two identical cells and quietly hide a pose that never renders.
POSES = sorted(S._POSES)
EXPRS = ['flat', 'worried', 'skeptical', 'terrified', 'relief', 'scream']


def main():
    rows = (len(POSES) + COLS - 1) // COLS
    img = Image.new('RGB', (COLS * CELL_W, rows * CELL_H + 260), (247, 242, 233))
    d = ImageDraw.Draw(img)

    for i, pose in enumerate(POSES):
        gx = (i % COLS) * CELL_W
        gy = (i // COLS) * CELL_H
        cx, cy = CELL_W // 2, 50          # CELL-LOCAL: the cell is only CELL_W
        try:                              # wide, so sheet coords clip the figure
            fig = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
            S.draw_stickman(fig, cx, cy, H, pose=pose, mouth='flat', theme='light')
            img.paste(fig, (gx, gy), fig)
        except Exception as exc:                                # noqa: BLE001
            d.text((gx + 30, gy + cy), 'ERR %s' % type(exc).__name__, fill=(200, 0, 0))
        d.line([(gx + 10, gy + cy + H), (gx + CELL_W - 10, gy + cy + H)],
               fill=(215, 200, 185))
        d.text((gx + cx - 50, gy + cy + H + 6), pose, fill=(20, 20, 20))

    base = rows * CELL_H
    for j, expr in enumerate(EXPRS):
        gx = j * CELL_W
        cx, cy = CELL_W // 2, 40
        try:
            fig = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
            S.draw_stickman(fig, cx, cy, 200, pose='standing', mouth=expr,
                            theme='light')
            img.paste(fig, (gx, base), fig)
        except Exception as exc:                                # noqa: BLE001
            d.text((gx + 30, gy + cy), 'ERR %s' % type(exc).__name__, fill=(200, 0, 0))
        d.line([(gx + 10, base + cy + 200), (gx + CELL_W - 10, base + cy + 200)],
               fill=(215, 200, 185))
        d.text((gx + cx - 45, base + cy + 206), expr, fill=(20, 20, 20))

    img.save(OUT)
    print('wrote %s  (%dx%d)  poses=%d mouths=%d'
          % (OUT, img.width, img.height, len(POSES), len(EXPRS)))


if __name__ == '__main__':
    main()
