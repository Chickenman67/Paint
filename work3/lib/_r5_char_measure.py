"""Measure every CHARACTER element's rendered alpha box, per beat.

Two defects the round-4/round-5 passes both hit by eye and then got wrong:
  * a hand or foot guillotined by the frame edge (reads as a rendering fault,
    not as a crop -- memory: character-must-be-cropped-into-not-placed-on)
  * a character element whose ink swallows the caption

So for each character element, at a time inside its own [at, until) window, we
report the alpha bbox and flag:
    EDGE   -- ink touches x=0, x=W-1, y=0 or y=H-1  (a HARD crop; a deliberate
              crop of a head is fine, but we want to see it, not discover it)
    BOTTOM -- ink runs off the bottom (expected for standing figures and for
              close-up busts, both of which are cropped by the frame)

Run: python lib/_r5_char_measure.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'work', 'lib'))

W, H = 1280, 720


def alpha_on_frame(el, t):
    import engine3 as E3
    tile, origin = el.tile_and_origin()
    dx, dy, scale, rot = el.transform_at(t)
    cim, cx0, cy0 = E3._apply_transform(tile, dx, dy, scale, rot, origin)
    full = [[0.0] * W for _ in range(H)]
    import numpy as np
    arr = np.zeros((H, W), np.float32)
    a = np.asarray(cim.getchannel('A')).astype(np.float32) / 255.0
    x1, y1 = min(W, cx0 + a.shape[1]), min(H, cy0 + a.shape[0])
    x0, y0 = max(0, cx0), max(0, cy0)
    if x1 > x0 and y1 > y0:
        arr[y0:y1, x0:x1] = a[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0]
    return arr


def main():
    import tres2b_scene as SC
    scene = SC.build()
    chars = [e for e in scene.elements if e.kind == 'character']
    hdr = ('%-8s %-7s %-24s %-18s %s' % ('id', 't', 'bbox x0..x1 y0..y1', 'flags', 'note'))
    print(hdr)
    print('-' * 92)
    for el in chars:
        end = el.until if el.until is not None else scene.duration
        t = el.at + min(1.0, max(0.0, (end - el.at) * 0.5))
        arr = alpha_on_frame(el, t)
        ys, xs = (arr > 0.02).nonzero()
        if len(xs) == 0:
            print('%-8s %-7.2f %-24s %-18s' % (el.id, t, '(nothing drawn)', 'EMPTY'))
            continue
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        flags = []
        if x0 <= 1:
            flags.append('LEFT')
        if x1 >= W - 2:
            flags.append('RIGHT')
        if y0 <= 1:
            flags.append('TOP')
        if y1 >= H - 2:
            flags.append('BOTTOM')
        note = ''
        if x1 == W - 1 or x0 == 0:
            note = 'hard side crop (ok if deliberate)'
        print('%-8s %-7.2f %-24s %-18s %s'
              % (el.id, t, '%d..%d %d..%d' % (x0, x1, y0, y1),
                 ','.join(flags) or '-', note))


if __name__ == '__main__':
    main()
