"""Render character3 poses standalone, for main-loop judging in isolation.

Why a separate file: the head/face defects (heavy eye rings, a hair crescent
that reads as a hood, oversized hand blobs) are SYSTEMIC -- every chapter scene
calls SC.fullbody/SC.closeup, so a fix here changes all nine films at once. But
judging them means reading a character on a busy painted card, where the fence
wires and the caption compete for attention and make defects ambiguous.

So render the figure alone on flat paper at ship size, plus a 2x head crop.
Frames go to measure/_char_<pose>.png and measure/_char_<pose>_head.png.

    python lib/_char_probe.py standing deadpan peeking shrug pointing armscrossed
    python lib/_char_probe.py --all
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), 'work', 'lib'))

from PIL import Image, ImageDraw                      # noqa: E402
import scene_common as SC                               # noqa: E402

OUT = os.path.join(ROOT, 'measure')

# (pose, expression) pairs worth looking at together: the same pose under a flat
# expression and a dramatic one tells you which defects are pose-independent.
PAIRS = [
    ('standing',   'deadpan'),
    ('standing',   'awed'),
    ('shrug',      'skeptic'),
    ('peeking',    'deadpan'),
    ('pointing',   'shock'),
    ('armscrossed', 'deadpan'),
    ('sitting',    'awed'),
    ('arms_up',    'scared'),
]


def main(argv):
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    if argv and argv[0] == '--all':
        picks = PAIRS
    elif argv:
        # any mix of poses and expressions; pair them up in order, defaulting
        # each unpaired pose to 'neutral'
        picks = []
        for i in range(0, len(argv), 2):
            pose = argv[i]
            expr = argv[i + 1] if i + 1 < len(argv) else 'neutral'
            picks.append((pose, expr))
    else:
        picks = PAIRS

    W, H = SC.W, SC.H
    for pose, expr in picks:
        tile = Image.new('RGB', (W, H), SC.CREAM if hasattr(SC, 'CREAM') else (242, 238, 226))
        d = ImageDraw.Draw(tile)
        SC.fullbody(d, 400, 690, 450, pose=pose, expression=expr, seed=7)
        # a second figure at closeup scale on the right, so a defect that only
        # appears at large size (eye rings, hairline) is visible in the same look
        SC.closeup(d, 980, 380, 210, expr, seed=11)
        path = os.path.join(OUT, '_char_%s_%s.png' % (pose, expr))
        tile.save(path)
        print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))