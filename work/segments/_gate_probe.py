# _gate_probe.py -- print only the gate metrics for a set of cardsheets.
#
# measure_frames.py computes ~40 features and refuses to pick a winner, by design.
# This wrapper reuses its measure() to print the handful that actually discriminate
# layout / linework weight / palette, so a segment's cardsheet can be checked
# against the reference's measured ranges in one line per frame.
#
# Reference ranges come from work/lib/measure_frames_report.md section 2 (B medians
# over 11 blinded pairs of the OLD segments). They are conformance targets, not a
# score: being outside the range means "look here", nothing more.
#
# USAGE: python _gate_probe.py tres2b [wasp17b ...]

import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import measure_frames as MF   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# (key, low, high) -- B medians +/- the observed spread, from report section 2.
GATE = {
    'v_centroid':          (0.50, 0.68),
    'ink_fraction':        (0.30, 0.55),
    'dark_mask_fraction':  (0.20, 0.60),
    'muted_fraction':      (0.38, 0.70),
    'palette_entropy_bits': (1.40, 2.40),
}

KEYS = ['v_centroid', 'ink_fraction', 'dark_mask_fraction', 'muted_fraction',
        'palette_entropy_bits']

# measure() nests its features; these are the paths, not the leaf names.
PATH = {
    'v_centroid':         ('layout_metrics', 'v_centroid'),
    'ink_fraction':       ('layout_metrics', 'ink_fraction'),
    'dark_mask_fraction': ('stickman_detection', 'dark', 'dark_mask_fraction'),
    'muted_fraction':     ('anti_aliasing_proxy', 'muted_fraction'),
    'palette_entropy_bits': ('dominant_colors', 'palette_entropy_bits'),
}


def dig(m, key):
    node = m
    for part in PATH[key]:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def probe_dir(d):
    pngs = sorted(glob.glob(os.path.join(d, 'cardsheet', '*.png')))
    rows = []
    for p in pngs:
        m = MF.measure(p)
        rows.append((os.path.basename(p), m))
    return rows


def main():
    for seg in sys.argv[1:]:
        d = os.path.join(HERE, seg)
        rows = probe_dir(d)
        if not rows:
            print('%-12s NO cardsheet' % seg)
            continue
        print('=== %s (%d frames) ===' % (seg, len(rows)))
        print('  %-14s %s' % ('frame', ''.join('%18s' % k[:17] for k in KEYS)))
        agg = {k: [] for k in KEYS}
        for name, m in rows:
            cells = []
            for k in KEYS:
                v = dig(m, k)
                if v is None:
                    cells.append('%18s' % 'n/a')
                    continue
                agg[k].append(float(v))
                lo, hi = GATE[k]
                flag = ' ' if lo <= float(v) <= hi else '*'
                cells.append('%17.3f%s' % (float(v), flag))
            print('  %-14s %s' % (name, ''.join(cells)))
        meds = []
        for k in KEYS:
            v = agg[k]
            meds.append('%17.3f' % (sorted(v)[len(v) // 2] if v else 0.0))
        print('  %-14s %s' % ('MEDIAN', ''.join(meds)))
        print()


if __name__ == '__main__':
    main()