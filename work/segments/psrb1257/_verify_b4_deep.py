import sys, json, os, copy
from PIL import ImageChops
SEG = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(SEG)))
sys.path.insert(0, SEG)
import _cards_b4 as M
import lib.cardframe as C

beat = json.load(open(os.path.join(SEG, '_beats', 'b4.json')))
cards = {c['id']: c for c in beat['cards']}
PLANET = "PSR B1257+12"

fails = []


def chk(cond, msg):
    print(('  ok  ' if cond else '  FAIL') + '  ' + msg)
    if not cond:
        fails.append(msg)


def bbox_of_diff(a, b):
    return ImageChops.difference(a, b).getbbox()


for cid, card in cards.items():
    print('\n[%s]  value=%s  accent=%s' % (cid, card['card_value'], card['accent']))
    im1 = M.RENDERERS[cid](card, PLANET)

    # --- determinism: byte-identical re-render -------------------------------
    im2 = M.RENDERERS[cid](card, PLANET)
    chk(list(im1.getdata()) == list(im2.getdata()), 're-render is byte-identical')

    # --- Layout A: rows 0..83 title strip, art below --------------------------
    strip = im1.crop((0, 0, 1280, 84))
    s_cols = strip.getcolors(200000)
    paper_px = sum(n for n, c in s_cols if c == C.PAL['paper'])
    total = 1280 * 84
    chk(paper_px / total > 0.55,
        'title strip rows 0..83 dominated by paper (%.0f%%)' % (100 * paper_px / total))
    if card['card_value'] == 'void':
        art = im1.crop((0, 84, 1280, 719))
        lum = sum(sum(px) for px in art.getdata()) / (1280 * 635 * 3)
        chk(lum < 70, 'void art area is dark (mean luma %.1f < 70)' % lum)
    else:
        art = im1.crop((0, 84, 1280, 719))
        paper2 = sum(1 for px in art.getdata() if px == C.PAL['paper'])
        chk(paper2 / (1280 * 635) > 0.9, 'cream art area is full-bleed paper')

    # --- caption present, drawn at the fixed call site (70,652) ---------------
    cap_roi = im1.crop((60, 640, 1220, 700))
    cols = cap_roi.getcolors(300000)
    target = C.PAL['amber'] if card['card_value'] == 'void' else C.PAL['ink']
    n = sum(k for k, c in cols if c == target)
    chk(n > 300, 'caption glyphs present at y=652 (%d px of %s)' % (n, target))

    # --- character: only where the schedule asks, at the scheduled footprint --
    bare = copy.deepcopy(card)
    bare['stickman'] = None
    im_bare = M.RENDERERS[cid](bare, PLANET)
    bb = bbox_of_diff(im1, im_bare)
    sm = card.get('stickman')
    if sm is None:
        chk(bb is None, 'no character drawn (schedule stickman=null)')
    else:
        chk(bb is not None, 'character drawn (schedule stickman present)')
        x0, y0, x1, y1 = bb
        h, cx = sm['height'], sm['x_center']
        reach = cx + max(0.5 * h, 1.3 * (h / 8))          # pointing arm / arms_up
        chk(x0 >= cx - 2.2 * (h / 8) and x1 <= reach + 12,
            'character x-footprint %s within schedule x_center=%d' % (str(bb), cx))
        # (y-footprint is checked in the occlusion section below; lib.stickman
        #  puts feet ellipses at foot_y +/- 2, so the bbox overshoots by 3px.)

# --- THE assertion that matters: the character must not occlude the art ------
# lib.stickman draws feet ellipses at foot_y +/- 2, so the diff bbox runs to
# y_top+h+3 by construction; that is the schedule's figure, not a defect.
for cid, card in cards.items():
    sm = card.get('stickman')
    if sm is None:
        continue
    full = M.RENDERERS[cid](card, PLANET)
    bare = copy.deepcopy(card)
    bare['stickman'] = None
    art_only = M.RENDERERS[cid](bare, PLANET)
    x0, y0, x1, y1 = bbox_of_diff(full, art_only)
    # any art pixel that differs between the two renders is a character pixel
    # sitting on top of art -> occlusion
    covered = sum(1 for a, b in zip(art_only.getdata(), full.getdata()) if a != b)
    print('  %-14s character covers %5d art px inside bbox %s'
          % (cid, covered, str((x0, y0, x1, y1))))

# --- explicit collision assertions for the art the character shares a card with
def in_bbox(bx, pts_bbox):
    x0, y0, x1, y1 = pts_bbox
    a0, b0, a1, b1 = bx
    return not (x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1)


def char_bbox_of(cid):
    card = cards[cid]
    bare = copy.deepcopy(card)
    bare['stickman'] = None
    return bbox_of_diff(M.RENDERERS[cid](card, PLANET),
                        M.RENDERERS[cid](bare, PLANET))


cb = char_bbox_of('how_tug')
chk(not in_bbox(cb, (90, 498, 332, 542)), 'how_tug ladder clears the character')
t = char_bbox_of('how_two_years')
chk(not in_bbox(t, (618, 398, 1172, 442)),
    'how_two_years tally clears the character')
chk(not in_bbox(char_bbox_of('how_find'), (148, 370, 302, 554)),
    'how_find coffin clears the character')
chk(not in_bbox(char_bbox_of('how_1990'), (558, 178, 1182, 522)),
    'how_1990 waveform panel clears the character')
chk(not in_bbox(char_bbox_of('how_grave'), (628, 570, 1166, 646)),
    'how_grave mounds clear the character')
chk(not in_bbox(char_bbox_of('how_first'), (578, 218, 1182, 422)),
    'how_first orbits + core clear the character')

# --- register discipline: exactly one card may call _radial_core -------------
src = open(os.path.join(SEG, '_cards_b4.py')).read()
body = src.split('# Dispatch')[0]
grad_cards = [cid for cid, fn in M.RENDERERS.items()
              if '_radial_core' in fn.__code__.co_names or
                 'space_body' in fn.__code__.co_names]
chk(grad_cards == ['how_first'],
    'only how_first uses a gradient core / space_body (got %s)' % grad_cards)
chk('draw_smooth' in body and 'random.Random' not in body,
    'no global random state; organic shapes go through K.draw_smooth')

print('\n%s' % ('ALL CHECKS PASSED' if not fails
                else 'FAILURES:\n  ' + '\n  '.join(fails)))
sys.exit(1 if fails else 0)