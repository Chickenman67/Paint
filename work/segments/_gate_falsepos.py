# _gate_falsepos.py -- quantify _gate.py's LOW_CONTRAST_TEXT and CLIPPED_AT_EDGE
# false-positive rate before anyone acts on its output.
#
# Context: a first pass over all 9 cardsheets reported 677 LOW_CONTRAST_TEXT hits
# on wasp127b alone and 159 CLIPPED_AT_EDGE on psoj3185. Spot-checking a frame by
# eye showed most of the tiny hits are STARFIELD DOTS -- white stars on a dark
# space background, which is correct art, not a defect. A gate that cries wolf on
# stars sends the fix pass chasing noise while the one real defect (near-black
# text on a near-black disc) hides in the flood. After recalibration the raw
# counts fell to 19; this script is how you check that a future threshold change
# has not reopened the flood.
#
# IT COMPUTES NO VERDICT. It only bins hits by size so a human can look at the
# ones worth looking at.
#
# Schema note: the per-frame dict carries dedicated lists `low_contrast_text` and
# `clipped_at_edge`, each entry holding bbox/w/h/n_glyphs/run_h. The `failures`
# list is a flat list of {check, value, criterion} with no geometry -- reading
# bboxes from there is why the first version of this script reported everything
# as "tiny".
#
# USAGE:  python _gate.py <segdir> ... --json _gate_all.json
#         python _gate_falsepos.py [_gate_all.json]

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, '_gate_all.json')

# Bins are by the LARGER of w/h, i.e. the run's longest dimension, so a clipped
# label that is tall and thin still lands in a human-scale bucket instead of
# being mistaken for a speck.
BINS = [(14, 'A  tiny   <=14px  star-sized; noise unless confirmed by eye'),
        (26, 'B  small  15-26px single glyph; plausible label'),
        (60, 'C  medium 27-60px short label; likely real'),
        (10 ** 9, 'D  large  >60px  text line; certainly real')]


def bin_hits(hits):
    b = collections.Counter()
    ex = collections.defaultdict(list)
    for seg, fr, c in hits:
        size = max(int(c.get('w') or 0), int(c.get('h') or 0))
        for lim, label in BINS:
            if size <= lim:
                break
        b[label] += 1
        if len(ex[label]) < 4:
            bb = c.get('bbox')
            ex[label].append('%s/%s bbox=%s glyphs=%s' %
                             (seg, fr, bb, c.get('n_glyphs')))
    return b, ex


def iter_hits(doc, field):
    for seg, v in doc.get('segments', {}).items():
        frames = v if isinstance(v, list) else v.get('frames', [])
        for f in frames:
            for c in f.get(field) or []:
                yield seg, os.path.basename(f.get('basename', '?')), c


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        sys.exit('run: python _gate.py <segdir> ... --json %s first' % path)
    doc = json.load(open(path, encoding='utf-8'))

    for field, title in (('low_contrast_text', 'LOW_CONTRAST_TEXT'),
                         ('clipped_at_edge', 'CLIPPED_AT_EDGE')):
        hits = list(iter_hits(doc, field))
        print('=== %s: %d hits ===' % (title, len(hits)))
        if not hits:
            continue
        b, ex = bin_hits(hits)
        for _, label in BINS:
            if b[label]:
                print('  %-58s %d' % (label, b[label]))
                for e in ex[label]:
                    print('        e.g. %s' % e)
        real = sum(b[l] for lim, l in BINS if lim >= 27)
        print('  --> %d/%d (%.1f%%) are >=27px and worth a human look'
              % (real, len(hits), 100.0 * real / len(hits)))

    print('\n=== HOW TO READ THIS ===')
    print('Bins A and B are the noise floor: stars, stipple, hatch. They are only')
    print('actionable if you have confirmed one by eye at full resolution. C and D')
    print('are label-scale and should each be opened before a fix pass touches it.')


if __name__ == '__main__':
    main()
