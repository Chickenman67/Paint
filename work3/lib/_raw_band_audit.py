"""RAW title-band intrusion audit: ignore TITLE_BACKDROP entirely.

WHY THIS EXISTS. band_intrusions forgives rows inside a chapter's declared
TITLE_BACKDROP span when the row is uniform END TO END. That rule is meant to
excuse the backdrop's flat fill. But a full-width horizontal BEAM is uniform for
the same reason a flat fill is -- it is a solid run of colour. So the exemption
cannot tell a deliberate backdrop from a solid stroke crossing the title, and a
chapter that has both will report a clean gate while shipping the defect.

svalbard hit exactly this: `_doorway`'s heavy INK frame is a full-width bar, the
exemption forgave it, and `contrast=[] intrusions=[]` was a FALSE GREEN. The
builder caught it by rendering the frame and looking, then dropped the geometry
until the RAW count was genuinely 0.

So this script re-measures every beat with the exemption SWITCHED OFF and prints
the raw intruding-pixel count. A chapter is only genuinely clean when its raw
count is 0 everywhere -- not when its gated count is 0.

Run: python _raw_band_audit.py [chapter ...]
"""
import sys
sys.path.insert(0, '.')

import importlib
import json
import os

import engine3 as E3
import numpy as np

import v2type as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV = 25
MINPX = 40


def raw_intrusions(chapter):
    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    meta = json.load(open(os.path.join(ROOT, 'segments', chapter, 'beats.json')))

    cap = T.TITLE_CAP_PX
    base = T.TITLE_BASELINE_Y
    ty0 = max(0, base - int(cap * 1.25))
    ty1 = base + 6
    tw = min(620, int(11 * cap * 0.62))
    tx0 = max(0, T.TITLE_CENTER_X - tw // 2)
    tx1 = min(1280, T.TITLE_CENTER_X + tw // 2)

    blank = E3._blank_page()
    if scene.title:
        E3._draw_title(blank, scene.title, seed=scene.title_seed)
    title_mask = np.asarray(blank.convert('L')) < 128
    for _ in range(4):
        d = title_mask.copy()
        d[1:, :] |= title_mask[:-1, :]
        d[:-1, :] |= title_mask[1:, :]
        d[:, 1:] |= title_mask[:, :-1]
        d[:, :-1] |= title_mask[:, 1:]
        title_mask = d

    hits = []
    for i, b in enumerate(meta['beats'], 1):
        mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        fr = E3.render_frame(scene, mid).convert('L')
        a = np.asarray(fr, dtype=np.int16)
        rect = a[ty0:ty1, tx0:tx1]
        mrect = title_mask[ty0:ty1, tx0:tx1]
        bgpix = rect[~mrect]
        if bgpix.size == 0:
            continue
        bg_level = float(np.median(bgpix))
        ink = (~mrect) & (np.abs(rect - bg_level) > DEV)
        n = int(ink.sum())
        if n > MINPX:
            hits.append((i, n))
    return hits


if __name__ == '__main__':
    chaps = sys.argv[1:] or ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye',
                             'cheyenne', 'svalbard', 'fortknox', 'vatican']
    bad = 0
    for ch in chaps:
        try:
            h = raw_intrusions(ch)
        except Exception as exc:
            print('%-10s HARNESS FAILED: %s: %s' % (ch, type(exc).__name__, exc))
            bad += 1
            continue
        if h:
            bad += 1
            print('%-10s RAW %d beat(s): %s' % (ch, len(h), h[:10]))
        else:
            print('%-10s raw 0  -- genuinely clean' % ch)
    print('\n%d chapter(s) with RAW intrusions' % bad)