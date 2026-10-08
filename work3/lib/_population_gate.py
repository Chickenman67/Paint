"""Per-beat POPULATION census: how full is each frame, and how many elements
are live in it.

WHY THIS IS NOT _pigment_gate
    `tile_std` measures edge density, so it is a texture signal and -- per the
    pigment-inverted-for-quality lesson -- it is INVERTED for quality: the
    highest-scoring frame in the bunker film was a flat vector mockup. Ranking
    frames by it is meaningless. This probe measures something else entirely:

      ink_fraction  fraction of pixels that are neither background nor the
                    paper-tooth overlay. Answers "how much of the frame has
                    something in it" -- the under-filled / over-populated axis.

      n_live        how many elements are simultaneously live at this beat. The
                    blind critic's dominant loss cause was packing MORE into a
                    frame than the reference did; element count is the direct
                    measurement of that, and it is a count, not an opinion.

    Both are rendered from the real frame at the real beat midpoint, so this
    is a measurement, not a source scan (memory: gates must render, not inspect).

USAGE:  python lib/_population_gate.py pinegap [chapter ...]
"""
import os
import sys
import json
import importlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import scene_common as SC          # noqa: E402
import engine3 as E3               # noqa: E402


def beat_midpoints(chapter):
    path = os.path.join(ROOT, 'segments', chapter, 'beats.json')
    beats = json.load(open(path, encoding='utf-8'))['beats']
    out = []
    for b in beats:
        start = float(b.get('start', 0.0))
        end = float(b.get('end', start))
        out.append((b.get('id', '?'), start + (end - start) * 0.6))
    return out


def _box_mean(a, k):
    """Cheap box blur via cumulative sums, edge-padded."""
    pad = k // 2
    ap = np.pad(a, ((pad, pad), (pad, pad)) + ((0, 0),) * (a.ndim - 2),
                mode='edge')
    c = np.cumsum(np.cumsum(ap, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)) + ((0, 0),) * (a.ndim - 2), mode='constant')
    H, W = a.shape[:2]
    s = (c[k:k + H, k:k + W]
         - c[0:H, k:k + W] - c[k:k + H, 0:W] + c[0:H, 0:W])
    return s / float(k * k)


def ink_fraction(img, k=25, thresh=26):
    """Fraction of pixels that differ strongly from their LOCAL neighbourhood.

    A first attempt measured distance from the frame's modal colour and read
    ink=1.000 on every frame: the paint has no dominant background (the top
    quantised colour is only 6.6% of a frame), so "far from background" is
    everywhere. That is the gate reporting nonsense -- see the
    blank-tile-is-a-harness-defect memory; a gate whose output is constant is
    worse than no gate.

    The fix is local, not global. Painterly tooth varies slowly across a region,
    so a pixel far from the mean of its own 25x25 neighbourhood is a STROKE, a
    fill edge, or TEXT, regardless of what colour that region is. That measures
    "how much of the frame has drawn content in it", which is the quantity the
    over-population / under-filled axis is about.
    """
    a = np.asarray(img.convert('L'), dtype=np.float32)     # luminance
    local = _box_mean(a, k)
    resid = np.abs(a - local)
    # also colour distance, so a hue change at constant luminance still counts
    ac = np.asarray(img.convert('RGB'), dtype=np.float32)
    localc = _box_mean(ac, k)
    residc = np.sqrt(((ac - localc) ** 2).sum(axis=2))
    mask = (resid > thresh) | (residc > thresh * 1.6)
    return float(mask.mean())


def live_elements(scene, t):
    n = 0
    for e in scene.elements:
        if getattr(e, 'visible', None) is False:
            continue
        a = getattr(e, 'at', 0.0)
        u = getattr(e, 'until', None)
        if u is None:
            u = float('inf')
        if a - 1e-6 <= t < u - 1e-6:
            n += 1
    return n


def census(chapter):
    importlib.invalidate_caches()
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    rows = []
    for bid, t in beat_midpoints(chapter):
        tc = max(0.0, min(t, scene.duration - 0.05))
        im = E3.render_frame(scene, tc)
        rows.append({'beat': bid, 't': round(tc, 2),
                     'ink': round(ink_fraction(im), 4),
                     'n_live': live_elements(scene, tc)})
    inks = [r['ink'] for r in rows]
    nls = [r['n_live'] for r in rows]
    return {
        'chapter': chapter,
        'n_beats': len(rows),
        'ink_min': round(min(inks), 4) if inks else 0,
        'ink_max': round(max(inks), 4) if inks else 0,
        'ink_mean': round(float(np.mean(inks)), 4) if inks else 0,
        'live_max': max(nls) if nls else 0,
        'frames': rows,
    }


if __name__ == '__main__':
    # REPORT ONLY. There is deliberately no pass/fail verdict here.
    #
    # A first cut flagged ink<0.12 as UNDERFILLED and ink>0.55 as DENSE. Both
    # flags were checked against eye-confirmed frames and both were WRONG:
    #   b04 (ink 0.098) is a wide desert establishing shot -- two distant mesas,
    #         sparse rocks, big sky. A legitimate wide, not a defect.
    #   b08 (ink 0.354, 8 live) is four radomes behind a fence filling the
    #         frame, cropped at the edges. That is the frame-fill target the
    #         critic keeps asking for, and the flag called it DENSE.
    # High ink with many live elements is the GOAL. Low ink is often a wide.
    # Absolute ink does not map to quality, so this prints a census and the
    # OUTLIERS; judging them is a visual act and belongs to the main loop.
    chs = sys.argv[1:] or ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye',
                           'cheyenne', 'svalbard', 'fortknox', 'vatican']
    for ch in chs:
        c = census(ch)
        print(json.dumps({k: v for k, v in c.items() if k != 'frames'}))
        inks = [r['ink'] for r in c['frames']]
        if inks:
            lo, hi = min(inks), max(inks)
        else:
            lo = hi = 0.0
        for r in c['frames']:
            edge = ''
            if hi - lo > 1e-6:
                rel = (r['ink'] - lo) / (hi - lo)
                if rel <= 0.10:
                    edge = '  [sparse]'
                elif rel >= 0.90:
                    edge = '  [dense]'
            print('   %-6s t=%6.2f ink=%.3f live=%d%s'
                  % (r['beat'], r['t'], r['ink'], r['n_live'], edge))