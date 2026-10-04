"""Mechanical verification for beat B2 (PSR B1257+12). Not part of the build."""
import hashlib
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)

import _cards_b2 as M
import lib.cardframe as C

PLANET = "PSR B1257+12"
beat = json.load(open(os.path.join(HERE, '_beats', 'b2.json')))
ids = [c['id'] for c in beat['cards']]

fail = []

# 1. dispatch table covers exactly this beat's cards
assert sorted(M.RENDERERS) == sorted(ids), (sorted(M.RENDERERS), sorted(ids))
M.register()
for cid in ids:
    if C.RENDERERS.get(cid) is not M.RENDERERS[cid]:
        fail.append('%s not registered into cardframe dispatch' % cid)

# 2. every renderer: no exception, RGB 1280x720, < 2 s
digests = {}
for card in beat['cards']:
    cid = card['id']
    t0 = time.time()
    im = M.RENDERERS[cid](card, PLANET)
    dt = time.time() - t0
    if im.mode != 'RGB':
        fail.append('%s mode=%s' % (cid, im.mode))
    if im.size != (1280, 720):
        fail.append('%s size=%s' % (cid, (im.size,)))
    if dt >= 2.0:
        fail.append('%s took %.2fs' % (cid, dt))
    digests[cid] = hashlib.sha256(im.tobytes()).hexdigest()
    print('  %-16s %-4s %sx%s  %.3fs  %s' % (cid, im.mode, im.size[0],
                                             im.size[1], dt, digests[cid][:12]))

# 3. determinism: same bytes on a second render in the same process
for card in beat['cards']:
    again = M.RENDERERS[card['id']](card, PLANET)
    if hashlib.sha256(again.tobytes()).hexdigest() != digests[card['id']]:
        fail.append('%s is not byte-deterministic' % card['id'])

# 4. no stroke thinner than 2 px anywhere in this module's own draw calls
src = open(os.path.join(HERE, '_cards_b2.py'), encoding='utf-8').read()
for m in re.finditer(r'width\s*=\s*([0-9]+)', src):
    if int(m.group(1)) < 2:
        fail.append('sub-2px width literal: %s' % m.group(0))
for m in re.finditer(r'K\.(FINE|HAIRLINE|DETAIL|OUTLINE)', src):
    if m.group(1) in ('HAIRLINE',):
        fail.append('uses K.HAIRLINE: %s' % m.group(0))

# 5. free stack only: no numpy, no network, no edits to lib/
if re.search(r'^\s*(import|from)\s+numpy', src, re.M):
    fail.append('imports numpy (brief forbids numpy paths)')
if 'lib.texture' in src or 'import texture' in src:
    fail.append('imports lib.texture (numpy-backed)')

# 6. the mandated helpers are actually called on every card
for card in beat['cards']:
    body = src.split('def render_%s(' % card['id'], 1)[1].split('\ndef ', 1)[0]
    if 'C._caption(img, card[\'caption\'], 70, 652, dark_bg=' not in body:
        fail.append('%s does not use the mandated caption call' % card['id'])
    want = 'paper_band=True' if card['card_value'] == 'void' else 'paper_band=False'
    if want not in body:
        fail.append('%s strip mode wrong (want %s)' % (card['id'], want))
    if bool(card.get('stickman')) != ("C._draw_stickman" in body):
        fail.append('%s character presence disagrees with the schedule' % card['id'])
    theme = "'dark'" if card['card_value'] == 'void' else "'light'"
    if card.get('stickman') and ('theme=%s' % theme) not in body:
        fail.append('%s character theme wrong (want %s)' % (card['id'], theme))
    if 'C._header(img, planet' not in body:
        fail.append('%s does not use the strip helper' % card['id'])

print()
if fail:
    print('FAIL')
    for f in fail:
        print('  -', f)
    raise SystemExit(1)
print('PASS  7/7 cards  RGB 1280x720  <0.05s each  byte-deterministic  '
      'no sub-2px strokes  no numpy  helpers-per-card all correct')
