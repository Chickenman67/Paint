# _frames.py -- the per-segment frame generator, generalized from seg 3's
# _frames_r2.py. Assembles <out>_silent.mp4 from:
#   * the card renderers in <seg>/_cards.py (a RENDERERS dict keyed by beat id)
#   * round_1_beats.json  (EXACT beat spans -- the timing ground truth)
#   * round_1_alignment.json (per-word onsets, for within-beat detail; optional)
#   * lib/motion.py        (0.25 s-quantized stamp motion)
#
# ONE CARD PER BEAT. Each beat in script.json carries a single, distinct
# 'visual' description and exactly one RENDERERS entry keyed by its id, so the
# natural cut is one card per beat (3.4-5.1 s -- inside the canon's 2-5 s band).
# Card boundaries are the EXACT synthesized beat boundaries: card.start ==
# beat.start, card.end == beat.end. There is nothing predicted here, so a card
# can never drift from its spoken word (the CLAUDE.md §5 failure mode). If a
# future round sub-divides a beat, that logic belongs in the schedule, not here.
#
# The bridge rule from _frames_r2.py is preserved exactly: a 0.5 s palette bridge
# is CARVED OUT OF THE TAIL of the card that precedes a boundary, never appended
# in front of the next card, so the next card still starts on its own spoken word.
# The segment-exit 3.75 s white bridge is owned by lib/transition.py / assembly,
# not here, so no trailing bridge is added.
#
# USAGE:
#   python _frames.py --seg tres2b [--planet "TRES-2B"] [--bridge-after id id ...]
#                     [--out round_1_silent.mp4]

import argparse
import importlib
import json
import os
import subprocess
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))       # .../work/segments
ROOT = os.path.abspath(os.path.join(HERE, '..'))         # .../work
sys.path.insert(0, ROOT)

import lib.cardframe as C          # noqa: E402
import lib.motion as M             # noqa: E402

W, H, FPS = 1280, 720, 30
STAMP_DT = M.STAMP_DT               # 0.25 s
BRIDGE_S = 0.5
BLACK = (0, 0, 0)

# Planet display name per segment key, and (optionally) which cards get a
# carved palette bridge. Bridging every beat would be wrong; the reference
# bridges only at palette changes. Default: no intra-segment bridges (the
# reference's own segments run as one palette per planet with snap cuts).
PLANET = {
    'tres2b': 'TRES-2B', 'wasp17b': 'WASP-17B', 'wasp127b': 'WASP-127B',
    'gliese436b': 'GLIESE 436 B', 'koi55': 'KOI-55', 'ltt9779b': 'LTT 9779 B',
    'fomalhautb': 'FOMALHAUT B', 'kelt9b': 'KELT-9B', 'psoj3185': 'PSO J318.5-22',
}


def register_cards(seg_dir):
    """Import <seg>/_cards.py and merge its RENDERERS into the dispatch table."""
    if seg_dir not in sys.path:
        sys.path.insert(0, seg_dir)
    m = importlib.import_module('_cards')
    importlib.reload(m)
    C.register(m.RENDERERS)
    return m.RENDERERS


def build_cards(seg):
    """One card per beat, from the EXACT beat spans. Returns (cards, audio_dur)."""
    seg_dir = os.path.join(HERE, seg)
    with open(os.path.join(seg_dir, 'round_1_beats.json'), encoding='utf-8') as f:
        bmeta = json.load(f)
    with open(os.path.join(seg_dir, 'script.json'), encoding='utf-8') as f:
        script = json.load(f)
    by_id = {b['id']: b for b in script['beats']}

    cards = []
    for i, b in enumerate(bmeta['beats']):
        sb = by_id.get(b['id'], {})
        cards.append({
            'id': b['id'],
            'n': b['n'],
            'beat': sb.get('beat', 'B%d' % b['n']),
            'register': b.get('register', sb.get('register', 'cream')),
            'start': b['start'],
            'end': b['end'],
            'line': b.get('line', ''),
            # a short generic caption; the real renderers draw their own labels.
            'caption': '',
            'motion': sb.get('motion', 'hold'),
            'stickman': None,      # renderers draw their own character
        })
    return cards, bmeta['duration_s'], bmeta


def build_timeline(cards, audio_duration, bridge_after=()):
    """-> (segments, total_s). Bridges are carved from the preceding card's tail."""
    segs = []
    last = len(cards) - 1
    for i, c in enumerate(cards):
        t0 = float(c['start'])
        t1 = float(c['end']) if i < last else float(audio_duration)
        if t1 <= t0:
            t1 = t0 + STAMP_DT
        if c['id'] in bridge_after and i < last:
            hold = t1 - t0 - BRIDGE_S
            if hold >= STAMP_DT:
                segs.append({'kind': 'card', 'card': c, 't0': t0, 't1': t0 + hold})
                segs.append({'kind': 'bridge', 't0': t0 + hold, 't1': t1})
                continue
        segs.append({'kind': 'card', 'card': c, 't0': t0, 't1': t1})
    return segs, segs[-1]['t1']


def render_segment(seg, out, planet=None, bridge_after=()):
    seg_dir = os.path.join(HERE, seg)
    planet = planet or PLANET.get(seg, seg.upper())
    cards, audio_dur, bmeta = build_cards(seg)
    R = register_cards(seg_dir)

    missing = [c['id'] for c in cards if c['id'] not in R]
    if missing:
        raise SystemExit('no renderer for beat ids: %s' % ', '.join(missing))

    segs, total_s = build_timeline(cards, audio_dur, bridge_after)
    n_frames = int(round(total_s * FPS))
    n_bridges = sum(1 for s in segs if s['kind'] == 'bridge')
    print('[%s] cards=%d bridges=%d total=%.3fs audio=%.3fs frames=%d @%dfps'
          % (seg, len(cards), n_bridges, total_s, audio_dur, n_frames, FPS),
          flush=True)

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
        '-r', str(FPS), '-i', 'pipe:0', '-an',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    still, still_id, seg_i, written = None, None, 0, 0
    try:
        for fi in range(n_frames):
            t = fi / FPS
            while seg_i + 1 < len(segs) and t >= segs[seg_i]['t1']:
                seg_i += 1
            seg = segs[seg_i]
            if seg['kind'] == 'bridge':
                img = Image.new('RGB', (W, H), BLACK)
            else:
                card = seg['card']
                if still_id != card['id']:
                    still = C.render(card, planet)       # built ONCE per card
                    still_id = card['id']
                elapsed = t - seg['t0']
                n_stamps = max(1, int(round((seg['t1'] - seg['t0']) / STAMP_DT)))
                img = M.apply_motion(still, card, int(elapsed / STAMP_DT), n_stamps)
            proc.stdin.write(img.tobytes())
            written += 1
            if written % 900 == 0:
                el = time.time() - t_start
                print('  %d/%d  %.0f fps' % (written, n_frames,
                                              written / max(0.001, el)), flush=True)
    finally:
        proc.stdin.close()
        proc.wait()

    el = time.time() - t_start
    print('[%s] wrote %s: %d frames, %.1fs (%.0f fps)'
          % (seg, os.path.basename(out), written, el, written / max(0.001, el)))
    if proc.returncode != 0:
        raise SystemExit('ffmpeg failed rc=%s' % proc.returncode)
    if abs(total_s - audio_dur) > (1.5 / FPS):
        raise SystemExit('timeline %.3fs != audio %.3fs -- mux would clip'
                         % (total_s, audio_dur))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--planet', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--bridge-after', nargs='*', default=[])
    args = ap.parse_args()
    out = args.out or os.path.join(HERE, args.seg, 'round_1_silent.mp4')
    render_segment(args.seg, out, args.planet, tuple(args.bridge_after))


if __name__ == '__main__':
    main()
