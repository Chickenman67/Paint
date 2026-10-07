"""Eye-check four beats across the pigment distribution before acting on 265/335.

The per-beat gate says 265 of 335 beats are flat, and the >=8 cluster is almost
entirely fortknox b26-b33/b36/b41 (gold brick vault) and svalbard b08/b10 (snow)
-- the two frames I already confirmed painted by eye. Before treating a 79%
number as real I need to look, at ship size, at:

    mezhgorye b15  1.95  the most flat chapter, 30/30 beats flat
    pinegap    b10         a flat beat from a chapter that reads painted on average
    area51     b13  9.06  borderline, just OVER the threshold -- the false-green risk
    fortknox   b26 53.64  the highest frame in the film -- the positive control

area51 b13 is the one that decides the threshold. If a frame at 9.06 looks flat,
8.0 is too low and the gate is under-reporting; if it looks painted, 8.0 holds.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402
import _pigment_gate as PG    # noqa: E402

PROBE = [
    ('mezhgorye', 'b15', 1.95, 'most-flat chapter, 30/30 beats flat'),
    ('pinegap', 'b10', None, 'flat beat from an "average-painted" chapter'),
    ('area51', 'b13', 9.06, 'BORDERLINE, just over the 8.0 threshold'),
    ('fortknox', 'b26', 53.64, 'highest in the film -- positive control'),
]

out = os.path.join(ROOT, 'measure', 'spread')
os.makedirs(out, exist_ok=True)

print('%-11s %-5s %8s %10s  %s' % ('chapter', 'beat', 'std', 't', 'note'))
print('-' * 78)
for chapter, bid, expect, note in PROBE:
    importlib.invalidate_caches()
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    t = dict(PG.beat_midpoints(chapter))[bid]
    tc = max(0.0, min(t, scene.duration - 0.05))
    im = E3.render_frame(scene, tc)
    med, frac = PG.tile_std(im)
    p = os.path.join(out, '%s_%s.png' % (chapter, bid))
    im.save(p)
    print('%-11s %-5s %8.2f %10.2f  %s' % (chapter, bid, med, tc, note))
print('\n-> %s' % out)