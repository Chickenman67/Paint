# _v2_align.py -- forced alignment for the v2 (atempo-paced) segments.
#
# IDENTICAL LOGIC to _batch_align.py, retargeted at the v2 artifacts:
#     reads  <seg>/script.json, v2_audio.wav, v2_beats.json
#     writes <seg>/v2_alignment.json
#
# The reason this is exact: v2 audio is still per-beat synthesized and
# concatenated with known sample counts, so every beat boundary in v2_beats.json
# is ground truth. The atempo stage only stretches each beat in place -- it does
# not move a boundary -- so the exactness survives the tempo pass. Whisper is
# still needed (and only) for the per-WORD onsets WITHIN a beat, which is what
# drives clause-level card pops.
#
# Word onsets come from the FINAL slowed audio, so the visuals are timed to the
# audio that actually plays. This is the CLAUDE.md SS5 drift fix.

import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))                 # .../work
sys.path.insert(0, os.path.join(HERE, 'psrb1257'))            # for _align_dp

from lib.align import align as whisper_align                    # noqa: E402
from _align_dp import align_tokens, resolve_spans                # noqa: E402

ORDER = [
    'tres2b', 'wasp17b', 'wasp127b', 'gliese436b', 'koi55', 'ltt9779b',
    'fomalhautb', 'psrb1257', 'kelt9b', 'psoj3185',
]


def tokenize(text):
    import re
    return re.findall(r"[A-Za-z0-9]+(?:[.'\-][A-Za-z0-9]+)*", text)


def run_segment(key, model_name='base.en'):
    seg_dir = os.path.join(HERE, key)
    wav = os.path.join(seg_dir, 'v2_audio.wav')
    beats_p = os.path.join(seg_dir, 'v2_beats.json')
    script_p = os.path.join(seg_dir, 'script.json')
    for p in (wav, beats_p, script_p):
        if not os.path.exists(p):
            print('  [%s] MISSING %s' % (key, os.path.basename(p)))
            return None

    with io.open(script_p, encoding='utf-8') as f:
        script = json.load(f)
    with io.open(beats_p, encoding='utf-8') as f:
        bmeta = json.load(f)

    cat = '\n'.join(b['line'] for b in script['beats']).strip()
    assert cat == script['narration'].strip(), 'LINE_EQ failed for %s' % key

    flat, ranges = [], []
    for b in script['beats']:
        ws = tokenize(b['line'])
        ranges.append((len(flat), len(flat) + len(ws), b['n']))
        flat.extend(ws)

    al = whisper_align(wav, script['narration'], model_name=model_name)
    wwords = [w['w'] for w in al['words']]
    if not wwords:
        print('  [%s] whisper returned no words' % key)
        return None

    mapping, notes = align_tokens(flat, wwords)
    mapping, span_notes = resolve_spans(mapping, flat, wwords)
    all_notes = notes + span_notes

    bspans = {b['n']: b for b in bmeta['beats']}
    out_words = []
    unplaced_clamped = 0
    for k, wi in enumerate(mapping):
        if wi is None or wi >= len(al['words']):
            continue
        ww = al['words'][wi]
        beat_n = None
        for (s0, s1, bn) in ranges:
            if s0 <= k < s1:
                beat_n = bn
                break
        bs = bspans.get(beat_n)
        if bs is None:
            continue
        t = ww['t']; e = ww['end']
        if t < bs['start'] or e > bs['end']:
            unplaced_clamped += 1
        t = min(max(t, bs['start']), bs['end'])
        e = min(max(e, bs['start']), bs['end'])
        if e < t:
            e = t
        out_words.append({'w': flat[k], 't': round(t, 3), 'end': round(e, 3),
                          'beat': beat_n})

    if not out_words:
        print('  [%s] no words placed' % key)
        return None

    for a, b in zip(out_words, out_words[1:]):
        if b['t'] < a['t'] - 1e-6:
            raise AssertionError(
                'non-monotonic alignment in %s: %r @%.3f then %r @%.3f'
                % (key, a['w'], a['t'], b['w'], b['t']))

    dur = al['duration_s']
    res = {
        'segment': key,
        'wav_path': 'v2_audio.wav',
        'duration_s': round(dur, 3),
        'beats_json': 'v2_beats.json',
        'word_count': len(out_words),
        'clamped_words': unplaced_clamped,
        'beat_boundaries_exact': True,
        'words': out_words,
        'notes': all_notes,
    }
    with io.open(os.path.join(seg_dir, 'v2_alignment.json'), 'w',
                 encoding='utf-8') as f:
        json.dump(res, f, indent=1, ensure_ascii=False)

    n_unplaced = sum(1 for n in all_notes if 'UNPLACED' in n or 'UNRESOLVED' in n)
    print('  [%s] %d words  %d beats  %.2fs  clamped=%d  unplaced=%d'
          % (key, len(out_words), len(bmeta['beats']), dur, unplaced_clamped,
             n_unplaced))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', nargs='*', default=None)
    ap.add_argument('--model', default='base.en')
    args = ap.parse_args()
    keys = args.segments or ORDER
    results = []
    for key in keys:
        try:
            r = run_segment(key, args.model)
            if r:
                results.append(r)
        except Exception as e:
            import traceback
            print('  [%s] FAILED: %s' % (key, e))
            traceback.print_exc()
    print('\n%d/%d segments aligned' % (len(results), len(keys)))
    out = os.path.join(HERE, '_v2_align_report.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump([{k: r[k] for k in ('segment', 'word_count', 'duration_s',
                                       'clamped_words')} for r in results],
                  f, indent=1)
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
