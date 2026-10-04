"""Build LABEL-FREE paired frames: ours vs the bunkers reference, same chapter.

WHY NORMALIZED-FRACTION TIMING. Absolute timestamps cannot be paired across the
two films. Ours is ~820s, the reference is 875.5s, and the drift is not linear --
it accumulates chapter by chapter, so by the last chapter an absolute offset is
off by most of a segment. So each pair is sampled at the same FRACTION through
its own chapter: `our_t = c0 + frac * our_chapter_dur`,
`ref_t = r0 + frac * ref_chapter_dur`.

WHY THREE BLINDING VECTORS, ALL THREE HIT. (memory blind-pairs-leak-vectors)
1. PIXELS -- the chapter title is DRAWN IN THE FRAME (our persistent title
   strip reads "Cheyenne Mountain"; the reference draws its own headings). A
   neutral filename does nothing when the name is legible in the picture, so the
   top title band is masked on BOTH sides.
2. FILENAMES -- files are written as p07_A.png / p07_B.png with the side
   assignment driven by a per-pair coin flip persisted to disk, so the same
   letter does not always mean the same side.
3. THE PRINTED MAPPING -- the A/B -> side map is written to _blind_key.json and
   is NOT printed here. Reading it before judging is the exact failure in
   memory blind-verdicts-valid-narrative-inverted: the per-pair verdicts are
   sound, then the prose written around them inverts because the attribution
   was guessed. Judge the pairs, then run --reveal to map letters to sides.

    python lib/_blind_pairs.py            # build all pairs
    python lib/_blind_pairs.py --reveal   # print the letter -> side key AFTER judging
"""

import json
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
REF = os.path.join(REPO, 'work', 'ref2', 'ref_full.mp4')
OUT = os.path.join(ROOT, 'measure', 'blind')
KEY = os.path.join(OUT, '_blind_key.json')

CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']

# Reference chapter onsets, read from work/ref2/ref_transcript.json (segment
# starts where each chapter is first named). Measured, not guessed.
REF_START = {
    'pinegap': 0.0, 'area51': 88.8, 'tomb': 172.4, 'room39': 314.5,
    'mezhgorye': 421.0, 'cheyenne': 483.0, 'svalbard': 568.0,
    'fortknox': 663.3, 'vatican': 784.2,
}
REF_DUR = 875.514

# Sample each chapter at these fractions of the way through it. 0.30 and 0.70
# land inside real content on both sides (never the title card, never the tail).
FRACS = [0.30, 0.70]

# The title band, masked on both sides. engine3's persistent title glyphs occupy
# y ~= 14..68 (v2type.TITLE_TOP_Y=21, cap height 46, baseline 67).
#
# THIS WAS 96px AND THAT WAS A BUG. Captions in this build sit at cy 90-92, so a
# 96px mask ate the top of our own captions -- one pair came back with a caption
# that looked dark-on-dark and clipped, and that "defect" was entirely
# self-inflicted. Mask the glyphs, not the caption zone: 72px clears the
# baseline at 67 plus wobble, and leaves cy>=90 captions intact.
BAND_H = 72


def ref_frame(t, path):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % t,
                    '-i', REF, '-frames:v', '1', path], check=True)
    return path


def our_frame(chapter, t, path):
    """Render our scene at time t via the beat clock (t may fall in a gap)."""
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.join(REPO, 'work', 'lib'))
    import importlib
    import engine3 as E3
    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    t = max(0.0, min(t, scene.duration - 0.05))
    E3.render_frame(scene, t).save(path)
    return path


def mask_band(path):
    """Cover the top title strip so the chapter name cannot leak the side."""
    im = Image.open(path).convert('RGB')
    d = ImageDraw.Draw(im)
    # flat mid-grey, matching the paper tone so it does not itself read as
    # "redacted" and bias the judge
    d.rectangle([0, 0, im.width, BAND_H], fill=(150, 150, 150))
    im.save(path)
    return path


def main(argv):
    if '--reveal' in argv:
        key = json.load(open(KEY))
        print('REVEAL (read only AFTER judging):')
        for k in sorted(key):
            print('  %s -> %s' % (k, key[k]))
        return 0

    os.makedirs(OUT, exist_ok=True)
    # deterministic per-pair coin flip from a fixed seed: reproducible across
    # runs (so a re-run does not reshuffle a half-judged set) but not a fixed
    # A=ours bias.
    rng = random.Random(20261004)
    key = {}
    idx = 0
    for chapter in CHAPTERS:
        beats_path = os.path.join(ROOT, 'segments', chapter, 'beats.json')
        meta = json.load(open(beats_path))
        our_start = 0.0
        our_dur = float(meta.get('duration_s') or 0.0)
        ref_start = REF_START[chapter]
        # chapter length on the ref side = next chapter's start, last = to end
        order = CHAPTERS.index(chapter)
        ref_end = (REF_START[CHAPTERS[order + 1]]
                   if order + 1 < len(CHAPTERS) else REF_DUR)
        ref_ch_dur = ref_end - ref_start
        for frac in FRACS:
            idx += 1
            our_t = our_start + frac * our_dur
            ref_t = ref_start + frac * ref_ch_dur
            a_is_ours = rng.random() < 0.5
            stem = 'p%02d' % idx
            ours_p = os.path.join(OUT, '_tmp_%s_ours.png' % stem)
            ref_p = os.path.join(OUT, '_tmp_%s_ref.png' % stem)
            our_frame(chapter, our_t, ours_p)
            ref_frame(ref_t, ref_p)
            mask_band(ours_p)
            mask_band(ref_p)
            a_src, b_src = (ours_p, ref_p) if a_is_ours else (ref_p, ours_p)
            a_out = os.path.join(OUT, '%s_A.png' % stem)
            b_out = os.path.join(OUT, '%s_B.png' % stem)
            os.replace(a_src, a_out)
            os.replace(b_src, b_out)
            key[stem] = ('ours' if a_is_ours else 'ref')   # side of letter A
            key[stem + '_B'] = ('ref' if a_is_ours else 'ours')
            print('%s  %-11s frac %.2f  our_t %6.2f  ref_t %6.2f'
                  % (stem, chapter, frac, our_t, ref_t))
    json.dump(key, open(KEY, 'w'), indent=1)
    print('\n%d pairs -> %s' % (idx, OUT))
    print('JUDGE THE PAIRS FIRST. Run --reveal only after recording verdicts.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))