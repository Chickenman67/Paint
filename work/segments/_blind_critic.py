# _blind_critic.py -- build label-blind paired contact sheets for a segment critic.
#
# Generalized from psrb1257/critic_r2/_blind_build.py. For a given segment it:
#   1. reads our MP4 duration and the reference chapter window from
#      work/chapters/chapter_map.json,
#   2. lays N evenly-spaced (our_t, ref_t) pairs across the segment (proportional
#      mapping, so both sides advance at the same narrative rate),
#   3. extracts one frame from each side, presents them as an A/B pair with the
#      label stripped, and
#   4. writes _KEY.json (which side is ours, per pair) that the critic must NOT
#      read until after recording a verdict.
#
# The blinding is the point. Memory gauntlet-critic-ref-bias-12-to-1 records a
# 12:1 ref-wins ratio that was a judging defect caused by filenames leaking the
# reference. Here nothing on the sheet says which side is which; the assignment
# is a deterministic FNV-1a hash of the pair id.
#
# USAGE:
#   python _blind_critic.py --seg tres2b --our round_1.mp4 [--pairs 14]
#   python _blind_critic.py --seg tres2b --reveal        # unseal after verdict

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
CHMAP = os.path.join(ROOT, 'chapters', 'chapter_map.json')

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
                        '-of', 'default=nw=1:nk=1', path], capture_output=True, text=True)
    return float(r.stdout.strip())


def grab(video, t, dst):
    """Frame-accurate extract (output seeking: -ss AFTER -i), with a retry.

    Under heavy CPU load (a concurrent TTS render is saturating the box) an
    ffmpeg call can transiently fail to produce its output file even when the
    grab is valid. Retry once on any failure or a missing/empty output, so a
    flaky extract never masquerades as a broken harness."""
    for attempt in range(3):
        try:
            subprocess.run(
                ['ffmpeg', '-y', '-v', 'error', '-i', video,
                 '-ss', '%.3f' % t, '-frames:v', '1', dst],
                check=True, capture_output=True)
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                return
        except subprocess.CalledProcessError:
            pass
        if os.path.exists(dst):
            os.remove(dst)
    raise RuntimeError('grab failed after 3 attempts: %s @ %.3f' % (video, t))


def side(img_path):
    return Image.open(img_path).convert('RGB').resize((TH_W, TH_H), Image.LANCZOS)


def build_pair_index(seg, our_dur, npairs):
    """N evenly-spaced pairs. our_t spans [0.15, 0.97]*our_dur; ref_t is the
    same fraction mapped onto the chapter's [start, end] window."""
    ch = None
    with io.open(CHMAP, encoding='utf-8') as f:
        for c in json.load(f)['chapters']:
            if c['key'] == seg:
                ch = c
                break
    if ch is None:
        raise SystemExit('no chapter window for %s' % seg)
    rows = []
    for i in range(npairs):
        frac = 0.15 + 0.82 * (i / max(1, npairs - 1))
        our_t = round(frac * our_dur, 3)
        ref_t = round(ch['start_s'] + frac * (ch['end_s'] - ch['start_s']), 3)
        rows.append({'n': i, 'our_t': our_t, 'ref_t': ref_t})
    return rows, ch


def build(seg, our_rel, npairs, reveal):
    seg_dir = os.path.join(HERE, seg)
    our_mp4 = os.path.join(seg_dir, our_rel)
    if not os.path.exists(our_mp4):
        raise SystemExit('missing our video: %s' % our_mp4)
    out = os.path.join(seg_dir, 'critic_r1')
    os.makedirs(out, exist_ok=True)
    our_dur = probe_duration(our_mp4)
    rows, ch = build_pair_index(seg, our_dur, npairs)
    print('seg %s  our=%.2fs  ref window %s..%s  pairs=%d'
          % (seg, our_dur, ch['start_s'], ch['end_s'], len(rows)))

    key = {}
    for r in rows:
        n = r['n']
        ours_is_a = (fnv1a('%s_pair%d' % (seg, n)) & 1) == 0
        a_src = 'ours' if ours_is_a else 'ref'
        b_src = 'ref' if ours_is_a else 'ours'
        a_t = r['our_t'] if a_src == 'ours' else r['ref_t']
        b_t = r['our_t'] if b_src == 'ours' else r['ref_t']
        a_png = os.path.join(out, 'p%02d_a.png' % n)
        b_png = os.path.join(out, 'p%02d_b.png' % n)
        grab(our_mp4 if a_src == 'ours' else REF, a_t, a_png)
        grab(our_mp4 if b_src == 'ours' else REF, b_t, b_png)
        key['p%02d' % n] = {'A': a_src, 'B': b_src}

        sheet = Image.new('RGB', (TH_W * 2 + PAD * 3, TH_H + LABEL_H + PAD * 2),
                          (16, 16, 20))
        d = ImageDraw.Draw(sheet)
        sheet.paste(side(a_png), (PAD, PAD + LABEL_H))
        sheet.paste(side(b_png), (PAD * 2 + TH_W, PAD + LABEL_H))
        d.text((PAD + 6, PAD + 6), 'A', fill=(255, 255, 255))
        d.text((PAD * 2 + TH_W + 6, PAD + 6), 'B', fill=(255, 255, 255))
        sheet.save(os.path.join(out, 'p%02d_pair.png' % n))

    with io.open(os.path.join(out, '_KEY.json'), 'w', encoding='utf-8') as f:
        json.dump({'seg': seg, 'our_duration_s': our_dur,
                   'ref_window': [ch['start_s'], ch['end_s']],
                   'key': key}, f, indent=1)
    with io.open(os.path.join(out, 'pair_index.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=1)
    print('built %d blinded pairs in %s' % (len(rows), out))
    if reveal:
        ours_a = sum(1 for v in key.values() if v['A'] == 'ours')
        print('REVEAL: ours is A in %d/%d pairs' % (ours_a, len(key)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--our', default='round_1.mp4')
    ap.add_argument('--pairs', type=int, default=14)
    ap.add_argument('--reveal', action='store_true',
                    help='print which side is ours (only AFTER a verdict)')
    args = ap.parse_args()
    build(args.seg, args.our, args.pairs, args.reveal)


if __name__ == '__main__':
    main()
