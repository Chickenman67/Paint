# _blind_build.py -- build the label-blind paired sheets for the segment-3 critic.
#
# For each of the 31 (our_t, ref_t) pairs in pair_index.json this extracts one
# frame from OUR round_2.mp4 and one from the reference, then presents them as an
# A/B pair with the label stripped. Which side is ours is decided by an FNV-1a
# hash of the pair index and written to _KEY.json, which the critic must NOT read
# until after recording a verdict. That is the whole point: the memory
# gauntlet-critic-ref-bias-12-to-1 records a 12:1 ref-wins ratio that turned out to
# be a judging defect caused by filenames leaking which side was the reference.
# Here nothing in the presented image says which is which.
#
# Usage: python _blind_build.py <our_mp4>   (ref path is fixed: work/ref_full.mp4)

import hashlib
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
# critic_r2 -> psrb1257 -> segments -> work
REF = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'ref_full.mp4'))
OUT = os.path.join(HERE, 'blind')
W, H = 1280, 720
TH_W, TH_H = 560, 315          # thumbnail size per side
PAD = 8
LABEL_H = 26


def fnv1a(s):
    h = 0x811c9dc5
    for b in s.encode('utf-8'):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def grab(video, t, dst):
    """Frame-accurate extract (output seeking: -ss AFTER -i)."""
    subprocess.run(
        ['ffmpeg', '-y', '-v', 'error', '-i', video, '-ss', '%.3f' % t,
         '-frames:v', '1', dst],
        check=True,
    )


def side(img_path):
    im = Image.open(img_path).convert('RGB')
    return im.resize((TH_W, TH_H), Image.LANCZOS)


def main():
    our_mp4 = sys.argv[1]
    rows = json.load(io.open(os.path.join(HERE, 'pair_index.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)

    key = {}
    for r in rows:
        n = r['n']
        # Which side is ours? Deterministic from the pair id so the assignment is
        # reproducible, but not something a human reading the sheet can predict.
        ours_is_a = (fnv1a('pair%d' % n) & 1) == 0
        a_src, b_src = ('ours', 'ref') if ours_is_a else ('ref', 'ours')
        a_t = r['our_t'] if a_src == 'ours' else r['ref_t']
        b_t = r['ref_t'] if a_src == 'ours' else r['our_t']
        a_png = os.path.join(OUT, 'p%02d_a.png' % n)
        b_png = os.path.join(OUT, 'p%02d_b.png' % n)
        if a_src == 'ours':
            grab(our_mp4, a_t, a_png)
        else:
            grab(REF, a_t, a_png)
        if b_src == 'ours':
            grab(our_mp4, b_t, b_png)
        else:
            grab(REF, b_t, b_png)
        key['p%02d' % n] = {'A': a_src, 'B': b_src}

        # paired sheet, labels are literally just "A" and "B"
        sheet = Image.new('RGB', (TH_W * 2 + PAD * 3, TH_H + LABEL_H + PAD * 2), (16, 16, 20))
        d = ImageDraw.Draw(sheet)
        sheet.paste(side(a_png), (PAD, PAD + LABEL_H))
        sheet.paste(side(b_png), (PAD * 2 + TH_W, PAD + LABEL_H))
        d.text((PAD + 6, PAD + 6), 'A', fill=(255, 255, 255))
        d.text((PAD * 2 + TH_W + 6, PAD + 6), 'B', fill=(255, 255, 255))
        sheet.save(os.path.join(OUT, 'p%02d_pair.png' % n))

    json.dump(key, io.open(os.path.join(OUT, '_KEY.json'), 'w', encoding='utf-8'), indent=1)
    print('built %d blinded pairs in %s' % (len(rows), OUT))


if __name__ == '__main__':
    main()
