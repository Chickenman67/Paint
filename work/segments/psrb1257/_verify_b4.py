import sys, json, time, os
SEG = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(os.path.dirname(SEG))   # work/
sys.path.insert(0, WORK)
sys.path.insert(0, SEG)

import _cards_b4 as M
import lib.cardframe as C

beat = json.load(open(os.path.join(SEG, '_beats', 'b4.json')))
cards = beat['cards']
assert set(M.RENDERERS) == {c['id'] for c in cards}, (
    set(M.RENDERERS) ^ {c['id'] for c in cards})

out = os.path.join(SEG, '_beats')
worst = 0.0
for card in cards:
    cid = card['id']
    t0 = time.time()
    img = M.RENDERERS[cid](card, "PSR B1257+12")
    dt = time.time() - t0
    worst = max(worst, dt)
    assert img.mode == 'RGB', (cid, img.mode)
    assert img.size == (1280, 720), (cid, img.size)
    p = os.path.join(out, 'preview_b4_%s.png' % cid)
    img.save(p)
    print('%-14s %s  %.3fs' % (cid, img.mode + str(img.size), dt))

print('OK  worst=%.3fs  files=%d' % (worst, len(cards)))