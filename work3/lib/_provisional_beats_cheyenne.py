"""PROVISIONAL beats.json for cheyenne -- written ONLY so the scene can be
built and frame-verified before the narration is synthesized.

*** THIS IS NOT AUDIO-DERIVED. *** The real beats.json is written by
lib/audio3.py and carries exact per-beat [start,end] spans read off the
rendered WAV (boundary_basis: "exact -- per-beat renders atempo-stretched
then concatenated"). This file PREDICTS the spans from word counts at the
chapter's target wpm with a fixed inter-beat gap, which is exactly the
predicted-timing failure CLAUDE.md warns about -- it is fine for judging
COMPOSITION, useless for judging sync.

Running `python lib/audio3.py --segments cheyenne` overwrites it.
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEG = os.path.join(ROOT, 'segments', 'cheyenne')
SCRIPT = os.path.join(SEG, 'script.json')
OUT = os.path.join(SEG, 'beats.json')

GAP_S = 0.08
TGT_WPM = 165.0
SEC_PER_WORD = 60.0 / TGT_WPM

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[.'’-][A-Za-z0-9]+)*")


def main():
    with io.open(SCRIPT, encoding='utf-8') as f:
        script = json.load(f)

    beats = script['beats']
    spans, cur = [], 0.0
    for i, b in enumerate(beats):
        nw = len(_WORD_RE.findall(b['line']))
        dur = round(nw * SEC_PER_WORD, 3)
        spans.append({
            'n': b['n'], 'id': b['id'], 'beat': b['beat'],
            'line': b['line'], 'start': round(cur, 3),
            'end': round(cur + dur, 3), 'dur': dur, 'words': nw,
        })
        cur += dur
        if i < len(spans) - 1:
            cur += GAP_S

    total_w = sum(s['words'] for s in spans)
    speech = sum(s['dur'] for s in spans)
    meta = {
        'segment': 'cheyenne',
        'wav_path': 'audio.wav',
        'provisional': True,
        'provisional_note': ('PREDICTED from word counts at %.0f wpm. NOT audio-derived. '
                             'Regenerate with: python lib/audio3.py --segments cheyenne'
                             % TGT_WPM),
        'duration_s': round(cur, 3),
        'sample_rate': 24000,
        'word_count': total_w,
        'speech_s': round(speech, 3),
        'gap_s': GAP_S,
        'wpm': round(total_w / cur * 60.0, 1),
        'boundary_basis': 'PROVISIONAL -- predicted from word counts, not the WAV',
        'beats': spans,
    }
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    print('provisional beats -> %s  %.2fs  %d beats  %.1f wpm'
          % (OUT, cur, len(spans), meta['wpm']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
