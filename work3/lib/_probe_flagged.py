"""Render the EXACT frames the blind critic called FLAT, and measure them.

The chapter-spread pigment gate said every chapter is painted (vatican 8.86),
but the blind critic called vatican q06 (our_t 64.44) a smooth-gradient
under-filled book. Those disagree. One of them is wrong. Resolve it on the
actual pixels at the actual timestamp, not on an average over a chapter and
not on a metric. This renders the flagged frames full-res and measures the
same tile metric on them, so we can see whether the metric or the eye is
wrong on the specific case the critic named.
"""
import importlib
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402
import _pigment_gate as PG    # noqa: E402

# (chapter, our_t) for the five clean losses the blind critic named.
FLAGGED = [
    ('svalbard', 29.04),   # q01 the WIN -- control, should be high
    ('svalbard', 67.75),   # q02 ref-win chart -- our side
    ('fortknox', 32.49),   # q03 flat vector building -- our side
    ('fortknox', 75.82),   # q04 shocked stickman flat grass -- our side
    ('vatican', 27.62),    # q05 parchment scroll -- our side
    ('vatican', 64.44),    # q06 smooth-gradient book -- our side
]

out = os.path.join(ROOT, 'measure', 'flagged')
os.makedirs(out, exist_ok=True)

print('%-10s %8s %10s %10s' % ('chapter', 'our_t', 'median_std', 'painted_f'))
print('-' * 42)
for chapter, t in FLAGGED:
    importlib.invalidate_caches()
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    tc = max(0.0, min(t, scene.duration - 0.05))
    im = E3.render_frame(scene, tc)
    med, frac = PG.tile_std(im)
    p = os.path.join(out, '%s_%s.png' % (chapter, str(t).replace('.', '_')))
    im.save(p)
    print('%-10s %8.2f %10.2f %10.3f  -> %s'
          % (chapter, tc, med, frac, os.path.basename(p)))