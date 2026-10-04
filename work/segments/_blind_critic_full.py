# _blind_critic_full.py -- ASSEMBLY-level label-blind critic, per CLAUDE.md S9.4.
#
# _blind_critic.py is per-segment (ours at round_1.mp4 vs the matching reference
# chapter window). S9.4 asks for something different: "10 paired frames at matched
# timestamps across the 15 minutes, label-blind, fresh context, overall verdict."
# That judges the FILM -- pacing, palette discipline, type-scale drift across
# segment joins, whether the 0.5s->3.75s bridges read right -- none of which a
# per-segment critic can see.
#
# Blinding is identical in spirit to _blind_critic.py and for the same reason
# (memory gauntlet-critic-ref-bias-12-to-1: a 12:1 ref-wins ratio was a judging
# defect caused by filenames leaking which side was the reference). Here the
# assignment is an FNV-1a hash of the PAIR INDEX, the sheet carries only "A" and
# "B", and the frames are written to neutral filenames.
#
# MATCHING. Segment-level mapping is proportional within a chapter. At assembly
# level both sides are laid out on the same normalized timeline: our_t = frac *
# our_total, ref_t = frac * ref_total. Both films are the same 12-planet
# structure, so the same narrative fraction lands on the same planet -- which is
# what makes the pairing meaningful rather than merely simultaneous.
#
# The reference is 916.376s and we are 866.9s, so an absolute-timestamp pairing
# would drift a full segment by the end. Normalized fraction avoids that.
#
# USAGE:
#   python _blind_critic_full.py --pairs 10
#   python _blind_critic_full.py --reveal        # AFTER recording verdicts

import argparse
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))       # .../work/segments
ROOT = os.path.join(HERE, '..')                          # .../work
REF = os.path.join(ROOT, 'ref_full.mp4')
OURS = os.path.join(ROOT, 'assembly', 'guantlet2_full.mp4')
OUT = os.path.join(ROOT, 'assembly', 'dbg_blind_critic_full')

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


def side(img_path):
    return Image.open(img_path).convert('RGB').resize((TH_W, TH_H), Image.LANCZOS)


def build(npairs, reveal):
    for p in (OURS, REF):
        if not os.path.exists(p):
            raise SystemExit('missing input: %s' % p)
    os.makedirs(OUT, exist_ok=True)
    our_dur = probe_duration(OURS)
    ref_dur = probe_duration(REF)
    print('ours %.2fs   ref %.2fs   delta %+.2fs' % (our_dur, ref_dur,
                                                      our_dur - ref_dur))

    key = {}
    rows = []
    for i in range(npairs):
        # Sample from 4% to 96% so we never land on the opening title or the
        # very end, but do cover the first and last segments.
        frac = 0.04 + 0.92 * (i / max(1, npairs - 1))
        our_t = round(frac * our_dur, 3)
        ref_t = round(frac * ref_dur, 3)
        rows.append({'n': i, 'frac': round(frac, 4),
                     'our_t': our_t, 'ref_t': ref_t})

        ours_is_a = (fnv1a('full_pair%d' % i) & 1) == 0
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
        sheet.paste(side(a_png), (PAD, PAD + LABEL_H))
        sheet.paste(side(b_png), (PAD * 2 + TH_W, PAD + LABEL_H))
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
    print('Record a verdict BEFORE reading _KEY.json.')
    if reveal:
        ours_a = sum(1 for v in key.values() if v['A'] == 'ours')
        print('REVEAL: ours is A in %d/%d pairs' % (ours_a, len(key)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', type=int, default=10)
    ap.add_argument('--reveal', action='store_true')
    args = ap.parse_args()
    build(args.pairs, args.reveal)


if __name__ == '__main__':
    main()