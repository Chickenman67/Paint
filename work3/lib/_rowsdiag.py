"""Per-row uniformity report inside the title band, using the GATE's own test.

band_intrusions forgives a row only when the whole horizontal run of unmasked
pixels spans <= DEV (25) levels. This prints, for the declared backdrop span,
which rows are NOT uniform and how wide the excursion is, so a card can be told
apart from its neighbour's art.
"""
import sys
sys.path.insert(0, '.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T

ch = sys.argv[1]
beats = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else None
importlib.invalidate_caches()
m = importlib.import_module('%s_scene' % ch)
s = m.build()
meta = json.load(open(os.path.join('..', 'segments', ch, 'beats.json')))

cap = T.TITLE_CAP_PX; base = T.TITLE_BASELINE_Y
ty0 = max(0, base - int(cap * 1.25)); ty1 = base + 6
tw = min(620, int(11 * cap * 0.62))
tx0 = max(0, T.TITLE_CENTER_X - tw // 2); tx1 = min(1280, T.TITLE_CENTER_X + tw // 2)
print('cap=%s base=%s  ty0=%d ty1=%d  rect x %d..%d' % (cap, base, ty0, ty1, tx0, tx1))

blank = E3._blank_page()
if s.title:
    E3._draw_title(blank, s.title, seed=s.title_seed)
tb = np.asarray(blank.convert('L'))
mask = tb < 128
for _ in range(4):
    d = mask.copy()
    d[1:, :] |= mask[:-1, :]; d[:-1, :] |= mask[1:, :]
    d[:, 1:] |= mask[:, :-1]; d[:, :-1] |= mask[:, 1:]
    mask = d

bd = getattr(m, 'TITLE_BACKDROP', None)
if bd:
    print('TITLE_BACKDROP=%s -> abs rows %d..%d' % (bd, bd[0], bd[1]))

if beats is None:
    beats = range(1, len(meta['beats']) + 1)

for i in beats:
    b = meta['beats'][i - 1]
    mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
    fr = E3.render_frame(s, mid).convert('L')
    a = np.asarray(fr, dtype=np.int16)
    rect = a[ty0:ty1, tx0:tx1]; mrect = mask[ty0:ty1, tx0:tx1]
    off = ~mrect
    lo_b, hi_b = (bd[0], bd[1]) if bd else (ty0, ty1)
    bad = []
    for r in range(rect.shape[0]):
        y = r + ty0
        if not (lo_b <= y <= hi_b):
            continue
        row = rect[r][off[r]]
        if row.size == 0:
            continue
        lo, hi = int(row.min()), int(row.max())
        if hi - lo > 25:
            bad.append((y, hi - lo))
    if bad:
        print('b%02d t=%.2f  NON-UNIFORM rows: %s' % (i, mid, bad))