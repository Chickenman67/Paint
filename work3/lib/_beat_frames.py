"""Render named beats of a chapter scene to full-res PNGs for main-loop judging.

WHY A SEPARATE FILE. _r5_frames.py is exoplanet-era and takes (name, t) pairs.
Judging a chapter is by BEAT, not by second, because the beat boundaries come
from the real WAV -- a beat's midpoint is always a legal, meaningful timestamp.
This maps beat id -> midpoint and writes 1280x720 frames.

    python lib/_beat_frames.py pinegap b03 b08 b17 b19 b20 b25
    python lib/_beat_frames.py pinegap --all 8            # 8 evenly spread

Frames go to measure/<chapter>_<beat>.png at FULL resolution. Memory
judge-art-at-full-res: a thumbnail reads invented defects that aren't there.
"""

import importlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402

OUT = os.path.join(ROOT, 'measure')


def load(chapter):
    """build() opens its own beats.json, so the scene is self-contained."""
    mod = importlib.import_module('%s_scene' % chapter)
    clock = SC.BeatClock(os.path.join(ROOT, 'segments', chapter, 'beats.json'))
    return clock, mod.build()


def main(argv):
    chapter = argv[0]
    if not chapter:
        print(__doc__)
        return 1
    rest = argv[1:]
    clock, scene = load(chapter)
    ids = [b['id'] for b in clock.meta['beats']]
    byid = {b['id']: b for b in clock.meta['beats']}

    picks = []
    if rest and rest[0] == '--all':
        n = int(rest[1]) if len(rest) > 1 else 8
        step = max(1, len(ids) // n)
        picks = ids[::step][:n]
    elif rest and rest[0] == '--sheet':
        # every beat's midpoint, for a contact sheet
        picks = ids
    else:
        picks = rest or ids

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for bid in picks:
        b = byid.get(bid)
        if b is None:
            # accept a bare index too
            if bid.isdigit() and int(bid) < len(ids):
                bid = ids[int(bid)]
                b = byid[bid]
            else:
                print('no beat %r' % bid)
                continue
        t = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        path = os.path.join(OUT, '%s_%s.png' % (chapter, bid))
        E3.render_frame(scene, t).save(path)
        print('%s  t=%.2f  %s' % (path, t, b.get('line', '')[:60]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))