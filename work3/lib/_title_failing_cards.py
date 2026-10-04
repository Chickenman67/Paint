"""Map failing title-contrast beats to the CARD element that draws them.

title_contrast() reports a beat; the fix has to land inside that card's draw
function, AFTER its background fill and BEFORE its art. The card that owns a
beat is the element whose [at, until) window contains the beat midpoint.

NOTE: engine3 Elements carry no `name` (gate comment) and no `__dict__`, so a
card is identified only by its (at, until, kind) window. The page bg is `kind
'bg'` at=0 with until=None, so it is excluded.

Run: python _title_failing_cards.py [chapter ...]
"""
import sys
sys.path.insert(0, '.')
import json
import os
import _coverage_gate as G

FAIL = {
    'pinegap':   [34],
    'area51':    [18, 34],
    'tomb':      [5,6,7,8,9,10,15,16,17,18],
    'room39':    [3,5,8,17,19,29,31,32,34,36],
    'mezhgorye': [19, 30],
    'cheyenne':  [16,25,27,28,29,37,38],
    'svalbard':  [1,2,19,31,33,34],
    'fortknox':  [22,23,24,27,28,29,32,33,44],
}

ROOT = os.path.dirname(os.path.abspath(__file__))


def scene_for(ch):
    import importlib
    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % ch)
    return mod, mod.build()


for ch in sys.argv[1:] or sorted(FAIL):
    beats = FAIL[ch]
    mod, scn = scene_for(ch)
    meta = json.load(open(os.path.join(ROOT, '..', 'segments', ch, 'beats.json')))
    print('=== %s ===' % ch)
    for b in beats:
        beat = meta['beats'][b-1]
        mid = (beat['start'] + beat.get('end', beat['start']+1.0)) / 2.0
        cover = []
        for e in scn.elements:
            kind = getattr(e, 'kind', '') or ''
            at = float(getattr(e, 'at', 0.0) or 0.0)
            until = getattr(e, 'until', None)
            until = float(until) if until is not None else None
            if kind == 'bg':
                continue
            live = (at <= mid) and (until is None or mid < until)
            if live and kind != 'text':
                cover.append('%s@%.2f' % (kind, at))
        print('  b%02d t=%.2f  art=%s' % (b, mid, ','.join(cover) or '(NONE)'))