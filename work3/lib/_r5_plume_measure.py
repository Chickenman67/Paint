"""Measure how much of the STAR'S DISC the atmosphere plume blankets.

The plume is drawn as its own element, so its contribution can be isolated: take
the element's own tile, put it through the SAME transform engine3 will apply at
time t, and read the alpha over the star's disc region. Eyeballing a yellow lens
on a yellow star cannot tell 20% coverage from 80%; this can.

Reports, for the star disc (and for an inner "core" of the disc, where the disc
must stay fully readable):
    cover_frac  -- fraction of disc pixels with plume alpha > 8
    mean_alpha  -- mean plume alpha over the whole disc
    p95         -- 95th percentile alpha over the disc
    inner_cover -- same cover_frac over the inner 60% of the disc radius
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'work', 'lib'))

W, H = 1280, 720


def element_alpha_on_frame(el, t):
    """The element's alpha as a full-frame 1280x720 float array at time t,
    produced with engine3's own transform code path (imported, not copied)."""
    import engine3 as E3
    tile, origin = el.tile_and_origin()
    dx, dy, scale, rot = el.transform_at(t)
    cim, cx0, cy0 = E3._apply_transform(tile, dx, dy, scale, rot, origin)
    full = np.zeros((H, W), np.float32)
    a = np.asarray(cim.getchannel('A')).astype(np.float32) / 255.0
    x1, y1 = min(W, cx0 + a.shape[1]), min(H, cy0 + a.shape[0])
    x0, y0 = max(0, cx0), max(0, cy0)
    if x1 > x0 and y1 > y0:
        full[y0:y1, x0:x1] = a[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0]
    return full


def star_disc(scene, t, disc_r, authored=(1075.0, 175.0), authored_r=92.0):
    """Where the star's DISC ends up at time t, using the same centroid rule
    engine3._apply_transform uses for scale-about-centroid."""
    star = [e for e in scene.elements if e.id == 'star'][0]
    tile, origin = star.tile_and_origin()
    dx, dy, scale, rot = star.transform_at(t)
    cx = origin[0] + tile.size[0] / 2.0 + dx
    cy = origin[1] + tile.size[1] / 2.0 + dy
    return cx, cy, authored_r * scale


def disc_mask(cx, cy, r, shrink=1.0):
    yy, xx = np.mgrid[0:H, 0:W]
    return (((xx - cx) ** 2 + (yy - cy) ** 2) <= (r * shrink) ** 2)


def report(tag, alpha, cx, cy, r):
    full = disc_mask(cx, cy, r)
    inner = disc_mask(cx, cy, r, shrink=0.60)
    a = alpha[full]
    ai = alpha[inner]
    return dict(
        tag=tag,
        disc_px=int(full.sum()),
        cover_frac=round(float((a > 8 / 255.0).mean()), 4),
        inner_cover=round(float((ai > 8 / 255.0).mean()), 4),
        mean_alpha=round(float(a.mean()), 4),
        p95_alpha=round(float(np.percentile(a, 95)), 4),
        peak_alpha=round(float(a.max()), 4),
    )


def main():
    import tres2b_scene as SC
    scene = SC.build()
    tail = [e for e in scene.elements if e.id == 'tail'][0]
    rows = []
    for t in (66.5, 67.0, 69.2, 71.0, 73.0):
        alpha = element_alpha_on_frame(tail, t)
        cx, cy, r = star_disc(scene, t, 92.0)
        rows.append(report('t=%.1f' % t, alpha, cx, cy, r))
    hdr = ('%-8s %9s %11s %11s %11s %10s %10s'
           % ('tag', 'disc_px', 'cover_frac', 'inner_cover', 'mean_alpha',
              'p95', 'peak'))
    print(hdr)
    print('-' * len(hdr))
    for row in rows:
        print('%-8s %9d %11.4f %11.4f %11.4f %10.4f %10.4f'
              % (row['tag'], row['disc_px'], row['cover_frac'],
                 row['inner_cover'], row['mean_alpha'], row['p95_alpha'],
                 row['peak_alpha']))


if __name__ == '__main__':
    main()
