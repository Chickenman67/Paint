"""Provisional beats.json for a chapter whose audio has not landed yet.

WHY THIS EXISTS. Every scene file opens its own `segments/<chapter>/beats.json`
and `SC.BeatClock` will not start without one, so a scene cannot be built or
judged frame-by-frame until the narration WAV exists. audio3.py writes
beats.json as a side effect of synthesis, and synthesis needs chatterbox -- not
available on the free stack. So for build-time judging we lay the beats out
from the WORD COUNTS in script.json at the same target wpm and inter-beat gap
audio3 uses.

THIS IS A STAND-IN, NOT A MEASUREMENT. The boundaries are proportional to word
count, which is exactly the predicted-timing failure CLAUDE.md §5.1 warns about:
the real file, once audio lands, replaces this one and the cards re-cut to the
real word onsets. Nothing downstream should treat these numbers as ground truth
-- `provisional: true` is recorded in the file so it is obvious on sight.

    python lib/_mksbeats.py svalbard

audio3.py writes beats.json unconditionally (it never checks for an existing
one), so re-running the real render simply overwrites this.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from audio3 import _WORD_RE, TARGET_WPM, NOMINAL_GAP_S     # noqa: E402


def build_meta(key, chapter_title):
    seg_dir = os.path.join(ROOT, 'segments', key)
    with io.open(os.path.join(seg_dir, 'script.json'), encoding='utf-8') as f:
        script = json.load(f)

    beats = []
    for b in script['beats']:
        line = b['line']
        beats.append({
            'n': b['n'],
            'id': b['id'],
            'beat': b['beat'],
            'line': line,
            'words': len(_WORD_RE.findall(line)),
        })

    n_gaps = max(1, len(beats) - 1)
    total_w = sum(x['words'] for x in beats)
    speech_s = total_w / TARGET_WPM * 60.0
    # Split the budget proportionally, then charge each beat its share of the
    # gaps. Rounded to ms, and the running cursor is what the card schedule
    # reads, so the tiling stays airtight.
    speech_s -= NOMINAL_GAP_S * n_gaps
    t = 0.0
    for x in beats:
        dur = speech_s * (x['words'] / float(total_w))
        x['start'] = round(t, 3)
        x['dur'] = round(dur, 3)
        x['end'] = round(t + dur, 3)
        x['wav'] = '_beats/%03d.wav' % x['n']
        t += dur + NOMINAL_GAP_S
    duration = round(t - NOMINAL_GAP_S, 3)

    return {
        'segment': key,
        'chapter_title': chapter_title,
        'wav_path': 'audio.wav',
        'provisional': True,
        'provisional_note': ('word-count-proportional stand-in for the real '
                             'chatterbox render; overwritten by audio3.py when '
                             'the WAV lands. Do not treat these boundaries as '
                             'aligned to the narration.'),
        'duration_s': duration,
        'sample_rate': 24000,
        'word_count': total_w,
        'speech_s': round(speech_s, 3),
        'gap_s': NOMINAL_GAP_S,
        'wpm': round(total_w / duration * 60.0, 1),
        'on_target': True,
        'boundary_basis': 'provisional -- word-count proportional, no audio',
        'beats': beats,
    }


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    key = argv[0]
    seg_dir = os.path.join(ROOT, 'segments', key)
    with io.open(os.path.join(seg_dir, 'script.json'), encoding='utf-8') as f:
        title = json.load(f).get('title', key)
    meta = build_meta(key, title)
    out = os.path.join(seg_dir, 'beats.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    print('wrote %s  %.3fs  %d beats  %.1f wpm  (PROVISIONAL)'
          % (out, meta['duration_s'], len(meta['beats']), meta['wpm']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
