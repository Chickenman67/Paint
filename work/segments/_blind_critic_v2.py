# _blind_critic_v2.py -- ASSEMBLY-level label-blind critic for the v2 film,
# against the NEW reference (work/ref2/ref_full.mp4), per CLAUDE.md §9.4.
#
# This is _blind_critic_full.py repointed at ref2 and the v2 assembly. It reuses
# that script's design wholesale, because the design is the point:
#
#   * A/B assignment is an FNV-1a hash of the PAIR INDEX, so it is stable across
#     re-runs but uncorrelated with which side is which.
#   * The sheet carries only "A" and "B" and the frames go to neutral filenames,
#     so nothing in the artifact leaks the reference.
#   * MATCHING is on a normalized fraction: our_t = frac*our_dur, ref_t =
#     frac*ref_dur. ref2 is 875.5s and our 10-segment film will be ~865s, so an
#     absolute-timestamp pairing would drift a full segment by the end.
#
# THE RULE THAT MATTERS (memory blind-verdicts-valid-narrative-inverted):
# record the verdicts as a BARE LIST OF LETTERS with no side names attached,
# then run --reveal and map letters to sides, and only then write any prose.
# The v1 pass formed valid per-pair verdicts but then wrote the narrative by
# GUESSING which side was the reference from how it looked -- and was wrong in
# 5 of 10, which inverted the entire diagnosis. Blinding the pixels is not
# enough; blinding the ATTRIBUTION is what protects the result.
#
# USAGE:
#   python _blind_critic_v2.py --pairs 10          # build the blinded pairs
#   python _blind_critic_v2.py --reveal             # AFTER writing the letters

import argparse
import io
import json
import os
import subprocess

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))       # .../work/segments
ROOT = os.path.join(HERE, '..')                        # .../work
REF = os.path.join(ROOT, 'ref2', 'ref_full.mp4')        # the NEW reference
OURS = os.path.join(ROOT, 'assembly', 'exoplanets_v2_full.mp4')
OUT = os.path.join(ROOT, 'assembly', 'dbg_blind_critic_v2')

W, H = 1280, 720
TH_W, TH_H = 560, 315
PAD = 8
LABEL_H = 26


def fnv1a(s):
    h = 0x811c9dc5
    for b in s.encode('utf-8'):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def probe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def grab(video, t, dst):
    """Frame-accurate extract (output seeking: -ss AFTER -i), with retry."""
    for _ in range(3):
        try:
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', video,
                            '-ss', '%.3f' % t, '-frames:v', '1', dst],
                           check=True, capture_output=True)
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                return
        except subprocess.CalledProcessError:
            pass
        if os.path.exists(dst):
            os.remove(dst)
    raise RuntimeError('grab failed: %s @ %.3f' % (video, t))


def side(img_path, mask_title=True):
    """Load a frame as a thumbnail, optionally masking the title strip.

    The chapter title ("WASP-127B" vs "TOMB OF QIN SHI HUANG") is rendered INTO
    the pixels, so even though the FILENAMES are neutral, the critic could read
    which side was the reference off the artwork. That is the same class of leak
    as the filename leak in gauntlet-critic-ref-bias-12-to-1, just carried in the
    image instead of the path. Masking the top band of BOTH sides equally makes
    the pass genuinely blind to segment identity while leaving the artwork,
    layout, type, palette and character fully judgeable.
    """
    im = Image.open(img_path).convert('RGB').resize((TH_W, TH_H), Image.LANCZOS)
    if mask_title:
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, TH_W, int(TH_H * 0.13)], fill=(16, 16, 20))
    return im


def build(npairs, reveal, mask_title=True):
    for p in (OURS, REF):
        if not os.path.exists(p):
            raise SystemExit('missing input: %s' % p)
    os.makedirs(OUT, exist_ok=True)
    our_dur = probe_duration(OURS)
    ref_dur = probe_duration(REF)
    print('ours %.2fs   ref %.2fs   delta %+.2fs' % (our_dur, ref_dur, our_dur - ref_dur))

    key = {}
    rows = []
    for i in range(npairs):
        frac = 0.04 + 0.92 * (i / max(1, npairs - 1))   # skip the opening title
        our_t = round(frac * our_dur, 3)
        ref_t = round(frac * ref_dur, 3)
        rows.append({'n': i, 'frac': round(frac, 4), 'our_t': our_t, 'ref_t': ref_t})

        ours_is_a = (fnv1a('v2_pair%d' % i) & 1) == 0
        a_src = 'ours' if ours_is_a else 'ref'
        b_src = 'ref' if ours_is_a else 'ours'
        a_t = our_t if a_src == 'ours' else ref_t
        b_t = our_t if b_src == 'ours' else ref_t
        a_png = os.path.join(OUT, 'p%02d_a.png' % i)
        b_png = os.path.join(OUT, 'p%02d_b.png' % i)
        grab(OURS if a_src == 'ours' else REF, a_t, a_png)
        grab(OURS if b_src == 'ours' else REF, b_t, b_png)
        key['p%02d' % i] = {'A': a_src, 'B': b_src}

        sheet = Image.new('RGB', (TH_W * 2 + PAD * 3, TH_H + LABEL_H + PAD * 2),
                          (16, 16, 20))
        d = ImageDraw.Draw(sheet)
        sheet.paste(side(a_png, mask_title), (PAD, PAD + LABEL_H))
        sheet.paste(side(b_png, mask_title), (PAD * 2 + TH_W, PAD + LABEL_H))
        d.text((PAD + 6, PAD + 6), 'A', fill=(255, 255, 255))
        d.text((PAD * 2 + TH_W + 6, PAD + 6), 'B', fill=(255, 255, 255))
        sheet.save(os.path.join(OUT, 'p%02d_pair.png' % i))
        print('  pair %02d  frac %.3f  our %.1fs / ref %.1fs' % (i, frac, our_t, ref_t))

    with io.open(os.path.join(OUT, '_KEY.json'), 'w', encoding='utf-8') as f:
        json.dump({'our_duration_s': our_dur, 'ref_duration_s': ref_dur,
                   'key': key}, f, indent=1)
    with io.open(os.path.join(OUT, 'pair_index.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=1)
    print('\nbuilt %d blinded pairs in %s' % (len(rows), OUT))
    print('Record a verdict (a bare list of A/B letters) BEFORE reading _KEY.json.')
    if reveal:
        ours_a = sum(1 for v in key.values() if v['A'] == 'ours')
        print('REVEAL: ours is A in %d/%d pairs' % (ours_a, len(key)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', type=int, default=10)
    ap.add_argument('--reveal', action='store_true')
    ap.add_argument('--no-mask-title', action='store_true',
                    help='show the chapter title strip (breaks blinding on segment identity)')
    args = ap.parse_args()
    build(args.pairs, args.reveal, mask_title=not args.no_mask_title)


if __name__ == '__main__':
    main()
