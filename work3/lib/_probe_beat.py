"""Render one chapter at ship size and save sampled beats, so a fix can be
checked IN CONTEXT rather than on an isolated primitive."""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join('..', 'work', 'lib'))

import scene_common as SC
import engine3 as E3
import _pigment_gate as PG

chapter = sys.argv[1]
beats = sys.argv[2].split(',')
tag = sys.argv[3] if len(sys.argv) > 3 else 'x'

mod = importlib.import_module(SC.scene_mod(chapter))
scene = mod.build()
print("%s elements %d dur %.2f" % (chapter, len(scene.elements), scene.duration))

mids = dict(PG.beat_midpoints(chapter))
for b in beats:
    t = mids.get(b)
    if t is None:
        print("  %s: no midpoint" % b)
        continue
    img = E3.render_frame(scene, t)
    p = os.path.join('..', 'measure', 'v_%s_%s.png' % (tag, b))
    img.save(p)
    print("  %s t=%.2f -> %s" % (b, t, p))