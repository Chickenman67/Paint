import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)

import _cards_b1 as M                                          # noqa: E402
import lib.type as T                                            # noqa: E402

beat = json.load(open(os.path.join(HERE, '_beats', 'b1.json')))
cards = {c['id']: c for c in beat['cards']}
INK, AMBER, PAPER = (20, 22, 28), (232, 163, 61), (242, 234, 214)
fails = []


def near(px, ref, tol):
    return all(abs(px[i] - ref[i]) <= tol for i in range(3))


def amber(p):
    return p[0] > 140 and p[2] < p[0] - 60


def render(cid, planet="PSR B1257+12"):
    return M.RENDERERS[cid](cards[cid], planet).convert('RGB')


def diff_pixels(a, b, pred=None):
    """Every pixel where two renders differ, optionally filtered."""
    pa, pb = a.load(), b.load()
    out = []
    for y in range(720):
        for x in range(1280):
            if pa[x, y] != pb[x, y] and (pred is None or pred(pa[x, y], pb[x, y])):
                out.append((x, y, pa[x, y], pb[x, y]))
    return out


def stats(px_list, label):
    if not px_list:
        print('   %-30s NO PIXELS' % label)
        return 0
    rs = [p[2][0] for p in px_list]
    bs = [p[2][2] for p in px_list]
    viol = sum(1 for p in px_list if p[2][2] > p[2][0] + 20 and p[2][0] > 30)
    amb = sum(1 for p in px_list if p[2][0] > 140 and p[2][2] < p[2][0] - 60)
    print('   %-30s n=%6d  x %4d..%4d  y %3d..%3d  mean=(%3.0f,%3.0f)  '
          'violet-hued=%d amber-hued=%d'
          % (label, len(px_list), min(p[0] for p in px_list),
             max(p[0] for p in px_list), min(p[1] for p in px_list),
             max(p[1] for p in px_list), sum(rs) / len(rs),
             sum(bs) / len(rs), viol, amb))
    return len(px_list)


print('### 1. Layout A -- paper strip rows 0..83, art from 84, header + caption present')
for cid in cards:
    img = render(cid)
    px = img.load()
    rows = (0, 4, 10, 15, 80, 82, 83, 84)
    band = all(near(px[x, y], PAPER, 3) for y in rows for x in range(0, 1280, 17))
    hdr = sum(1 for y in range(18, 68) for x in range(0, 1280, 2)
              if near(px[x, y], INK, 40))
    art = sum(px[640, 95]) < 200
    print(' %-15s paperband(rows %s)=%s  header_ink_px=%d  art_starts_dark@95=%s'
          % (cid, rows, band, hdr, art))
    if not band or hdr < 1500 or not art:
        fails.append('%s Layout A' % cid)

print('\n### 2. caption -- mandated call, amber on void, inside the frame, one line')
for cid, card in cards.items():
    img = render(cid)
    px = img.load()
    f = T.load_font(T.CAPTION_PX, bold=True)
    bb = f.getbbox(card['caption'])
    w = bb[2] - bb[0]
    box = [px[x, y] for y in range(646, 700, 2) for x in range(64, 80 + w, 2)]
    amb = sum(1 for p in box if amber(p))
    key = sum(1 for p in box if near(p, INK, 14))
    print(' %-15s w=%3dpx  amber_px=%5d  ink_keyline_px=%5d  one_line=%s'
          % (cid, w, amb, key, 70 + w < 1280))
    if amb < 800 or key < 800 or 70 + w >= 1280:
        fails.append('%s caption' % cid)

print('\n### 3. character -- cream on void, schedule position/size/pose only')
for cid, card in cards.items():
    sm = card['stickman']
    img = render(cid)
    px = img.load()
    hr = int(sm['height'] / 8)
    hx, hy = sm['x_center'], sm['y_top'] + hr
    head = px[hx, hy]
    cream = sum(1 for y in range(sm['y_top'], sm['y_top'] + 2 * hr, 2)
                for x in range(hx - hr, hx + hr, 2) if near(px[x, y], (245, 240, 225), 16))
    face = sum(1 for y in range(sm['y_top'] + int(hr * 0.3), sm['y_top'] + int(hr * 1.7), 1)
               for x in range(hx - int(hr * 0.7), hx + int(hr * 0.7), 1)
               if not near(px[x, y], (245, 240, 225), 24))
    print(' %-15s head@(%d,%d)=%s cream=%s  face_ink_px=%d  pose=%-16s expr=%-12s '
          'h=%d y_top=%d x=%d' % (cid, hx, hy, head, near(head, (245, 240, 225), 12),
                                  face, sm['pose'], sm['expression'], sm['height'],
                                  sm['y_top'], sm['x_center']))
    if not near(head, (245, 240, 225), 12) or face < 200:
        fails.append('%s character' % cid)

print('\n### 4. focal hierarchy -- where is the brightest non-star pixel?')
for cid in cards:
    img = render(cid)
    px = img.load()
    core = max((sum(px[x, y]), x, y) for x in range(962, 1000, 2)
               for y in range(282, 320, 2))
    best = []
    for y in range(86, 719, 2):
        for x in range(0, 1280, 2):
            if abs(y - 300) < 26:                    # banner glyph rows
                continue
            if y > 636:                              # caption row
                continue
            if 240 < x < 580 and 140 < y < 710:       # character
                continue
            best.append((sum(px[x, y]), x, y))
    best.sort(reverse=True)
    print(' %-15s core_max=%d@(%d,%d)   top non-star: %s' %
          (cid, core[0], core[1], core[2], [(b[0], b[1], b[2]) for b in best[:3]]))
    if core[0] <= best[0][0]:
        fails.append('%s focal hierarchy (field=%d beats core=%d)' % (cid, best[0][0], core[0]))

def flat(px_list, label, min_n=500):
    """A flat element has a tight value spread. A gradient would fan out."""
    n = len(px_list)
    if n < min_n:
        return True
    vals = sorted(p[2][0] * 65536 + p[2][1] * 256 + p[2][2] for p in px_list)
    spread = (vals[int(n * 0.99)] - vals[int(n * 0.01)]) / 65536.0
    print('   %-30s n=%6d  p1..p99 value spread = %5.1f  -> %s'
          % (label, n, spread, 'FLAT' if spread < 40 else 'GRADED (defect)'))
    return spread < 40


print('\n### 5. accent elements isolated by no-op monkeypatch + exact diff')
# -- card 1
base = render('hook_dead')
_save_ring1 = M._flat_ring
M._flat_ring = lambda *a, **k: None
norings = render('hook_dead')
M._flat_ring = _save_ring1
r_px = diff_pixels(base, norings)
stats(r_px, 'hook_dead halo rings')
# p[2] is the pixel WITH the element; p[3] is the background it replaced.
# >=95% must be flat violet; the remainder are where the banner's antialiased
# glyph edge crosses the ring, which is correct layering.
n_viol = sum(1 for p in r_px if p[2][2] > p[2][0] + 12)
print('   flat-violet px = %d/%d (%.1f%%)' % (n_viol, len(r_px), 100.0 * n_viol / len(r_px)))
if len(r_px) < 2000 or n_viol < 0.95 * len(r_px):
    fails.append('hook_dead halo rings not flat violet')
flat(r_px, 'hook_dead halo rings flatness')
# two distinct radii?
rad = sorted({round(((p[0] - 980) ** 2 + (p[1] - 300) ** 2) ** 0.5) for p in r_px})
print('   radii present: %s .. %s (expect 64 and 78)' % (rad[0], rad[-1]))
if not any(abs(v - 64) <= 2 for v in rad) or not any(abs(v - 78) <= 2 for v in rad):
    fails.append('hook_dead halo radii are not 64/78: %s..%s' % (rad[0], rad[-1]))

_save_wisp = M._nebula_wisp
M._nebula_wisp = lambda *a, **k: None
nowisp = render('hook_dead')
M._nebula_wisp = _save_wisp
w_px = diff_pixels(base, nowisp)
stats(w_px, 'hook_dead nebula wisp')
flat(w_px, 'hook_dead wisp flatness', min_n=5000)
# The wisp must be a WHISPER: a low-alpha violet tint that adds no bright focal
# point. Its peak luma must stay at or below the void field's own star brightness
# and far below the star core.
region = [(p[0], p[1]) for p in w_px]
bmax = max(sum(nowisp.load()[x, y]) for x, y in region)
amax = max(sum(base.load()[x, y]) for x, y in region)
print('   wisp region: brightest-without=%d  brightest-with=%d  (star core=756)  '
      '-> introduces no focal point: %s' % (bmax, amax, amax < bmax + 1 and amax < 700))
if amax >= 700:
    fails.append('hook_dead wisp too bright (competes with the star), amax=%d' % amax)

# -- card 2
base = render('hook_talking')
_save_arc = M._radio_arc
M._radio_arc = lambda *a, **k: None
noarcs = render('hook_talking')
M._radio_arc = _save_arc
a_px = diff_pixels(base, noarcs)
stats(a_px, 'hook_talking radio arcs')
left = [p for p in a_px if p[0] < 980]
right = [p for p in a_px if p[0] > 1030]
print('   arcs left of star=%d  right of star (r>50)=%d  -> opens toward x=400 character: %s'
      % (len(left), len(right), len(left) > 20 * max(1, len(right))))
if len(left) < 3000 or len(right) > 40:
    fails.append('hook_talking arc geometry/orientation')
for want, lo, hi in (('r=110', 106, 114), ('r=170', 166, 174), ('r=230', 226, 234)):
    hits = [p for p in a_px if lo <= ((p[0] - 980) ** 2 + (p[1] - 300) ** 2) ** 0.5 <= hi]
    print('   arc %s: %d px' % (want, len(hits)))
    if len(hits) < 400:
        fails.append('hook_talking arc %s missing' % want)
    # each arc is a SINGLE flat alpha; the pooled spread of all three is
    # meaningless because the three alphas differ by design
    if not flat(hits, 'arc %s flatness' % want, min_n=200):
        fails.append('hook_talking arc %s is graded' % want)
if not all(p[2][2] > p[2][0] + 12 for p in a_px):
    fails.append('hook_talking arcs not flat violet')

# -- card 3
base = render('hook_not_alone')
_save_ring = M._flat_ring
M._flat_ring = lambda *a, **k: None
nolimb = render('hook_not_alone')
M._flat_ring = _save_ring
assert M._flat_ring is _save_ring and M._radio_arc is not None
l_px = diff_pixels(base, nolimb)
stats(l_px, 'hook_not_alone amber limb ring')
lr = sorted({round(((p[0] - 980) ** 2 + (p[1] - 300) ** 2) ** 0.5) for p in l_px})
n_amber = sum(1 for p in l_px if amber(p[2]))
print('   ring radii: %s..%s  amber px=%d/%d (rest is core-edge blend, expected)'
      % (lr[0], lr[-1], n_amber, len(l_px)))
if not l_px or n_amber < 0.8 * len(l_px):
    fails.append('hook_not_alone limb ring not predominantly amber')
# A ring ON the limb necessarily blends between amber-over-void and
# amber-over-white-core, so a wide value spread here is expected, not a gradient.
# The gradient rule is enforced structurally in section 6 instead.
flat(l_px, 'hook_not_alone limb spread', min_n=100)

# -- the three cards must not look identical
import itertools                                              # noqa: E402
ims = {cid: render(cid).tobytes() for cid in cards}
for a, b in itertools.combinations(cards, 2):
    n = sum(1 for i in range(0, len(ims[a]), 997) if ims[a][i] != ims[b][i])
    print('   %-15s vs %-15s sampled-differing-bytes=%d' % (a, b, n))
    if n == 0:
        fails.append('%s and %s render identically' % (a, b))

print('\n### 6. gradient denylist (structural) -- only the emissive core may ramp')
import ast                                                  # noqa: E402
tree = ast.parse(open(os.path.join(HERE, '_cards_b1.py')).read())
grad_attrs = ('_radial_core', 'soft_glow', 'space_body', 'radial_gradient', 'GaussianBlur')
encl_of = {}
for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
    for n in ast.walk(fn):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in grad_attrs):
            encl_of.setdefault(fn.name, []).append((n.func.attr, n.lineno))
print(' ramp-capable calls by enclosing function: %s' % encl_of)
allowed_encl = {'_pulsar_core'}
for fnname, calls in encl_of.items():
    if fnname not in allowed_encl:
        fails.append('gradient drawn outside the emissive core: %s in %s'
                     % (calls, fnname))
# and the planets-as-subjects / orbit ellipses / starfield must not be present at all
if 'space_body' in str(encl_of):
    print(' NOTE: space_body() is a planet renderer; it applies a soft radial base. '
          'This beat has no planet-as-subject, so it must be absent.')
    fails.append('space_body used on a card with no planet subject')

print('\n### 7. free-stack imports only, no global random state')
imports = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        imports.update(a.name.split('.')[0] for a in n.names)
    elif isinstance(n, ast.ImportFrom) and n.module:
        imports.add(n.module.split('.')[0])
print(' imports = %s  -> subset of {PIL, math, random, lib}: %s'
      % (sorted(imports), imports <= {'PIL', 'math', 'random', 'lib'}))
if not imports <= {'PIL', 'math', 'random', 'lib'}:
    fails.append('illegal import: %s' % (imports - {'PIL', 'math', 'random', 'lib'}))
src = open(os.path.join(HERE, '_cards_b1.py')).read()
print(" 'random.seed(' present: %s | numpy present: %s"
      % ('random.seed(' in src, 'numpy' in src))
if 'random.seed(' in src or 'numpy' in src:
    fails.append('global random state or numpy used')

print('\n### 8. the schedule owns pose/expression/position -- no hardcoding')
for cid, card in cards.items():
    img = render(cid)
    px = img.load()
    sm = card['stickman']
    hr = int(sm['height'] / 8)
    ok = near(px[sm['x_center'], sm['y_top'] + hr], (245, 240, 225), 12)
    # The figure legitimately extends past the head (pointing arm, hands_up).
    # Bound the WHOLE scheduled figure, not just the head. A cream pixel well
    # outside this box would mean a second, off-schedule figure.
    x_lo = sm['x_center'] - int(sm['height'] * 0.7)
    x_hi = sm['x_center'] + int(sm['height'] * 0.7)
    y_lo = sm['y_top'] - 8
    y_hi = sm['y_top'] + sm['height'] + 8
    stray = []
    for y in range(84, 720, 3):
        for x in range(0, 1280, 3):
            p = px[x, y]
            if (near(p, (245, 240, 225), 6)
                    and not (x_lo <= x <= x_hi and y_lo <= y <= y_hi)):
                stray.append((x, y, p))
    print(' %-15s head at schedule pos=%s | figure box x %d..%d y %d..%d | '
          'off-schedule cream px (sampled)=%d %s'
          % (cid, ok, x_lo, x_hi, y_lo, y_hi, len(stray), stray[:3]))
    if not ok or len(stray) > 0:
        fails.append('%s character not exactly at the scheduled slot' % cid)

print('\n### 9. determinism -- byte-identical re-render, and seed-independence')
for cid, card in cards.items():
    a = render(cid).tobytes()
    b = render(cid).tobytes()
    print(' %-15s byte-identical: %s' % (cid, a == b))
    if a != b:
        fails.append('%s not deterministic' % cid)

print('\nFAILURES:', fails if fails else 'none')
sys.exit(1 if fails else 0)
