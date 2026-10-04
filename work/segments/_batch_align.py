# _batch_align.py -- forced alignment for the per-beat TTS segments.
#
# WHY THIS IS SIMPLER THAN SEG 3's ALIGNER. Seg 3 synthesized 110-word chunks
# and had to let whisper discover every boundary, so all of its timings were
# estimates. Here the audio was synthesized BEAT BY BEAT and concatenated with
# known sample counts, so every beat boundary in round_1_beats.json is exact
# (ground truth, not a prediction). That is the CLAUDE.md SS5 drift problem
# solved at the strongest joint: a card anchored to a beat can never drift.
#
# What whisper is still needed for: the per-WORD onsets WITHIN a beat, so the
# card layer can sub-divide a 4-5s beat into 2-3 clause cards at the right
# instants. We run whisper ONCE over the whole segment (full acoustic context --
# far more reliable than slicing into 4s fragments, which invite hallucination),
# DP-align the full script to the full whisper output, then clamp every word's
# onset/end into its beat's exact [start, end] span. The clamp can only pull a
# whisper estimate back toward ground truth, never invent a new boundary.
#
# Reads   <seg>/script.json, round_1_audio.wav, round_1_beats.json
# Writes  <seg>/round_1_alignment.json
#
# Emitted per-word times are ABSOLUTE seconds into round_1_audio.wav. Each word
# also carries its beat number so the card layer never has to re-derive which
# beat it is in.

import argparse
import io
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))                 # .../work
sys.path.insert(0, os.path.join(HERE, 'psrb1257'))            # for _align_dp

from lib.align import align as whisper_align                    # noqa: E402
from _align_dp import align_tokens, resolve_spans                # noqa: E402

ORDER = [
    ('tres2b', 4), ('wasp17b', 5), ('wasp127b', 6), ('gliese436b', 7),
    ('koi55', 8), ('ltt9779b', 9), ('fomalhautb', 10), ('kelt9b', 11),
    ('psoj3185', 12),
]


def tokenize(text):
    """Split a line into comparable tokens (mirrors _align_dp canon input)."""
    import re
    return re.findall(r"[A-Za-z0-9]+(?:[.'\-][A-Za-z0-9]+)*", text)


def run_segment(key, model_name='tiny.en'):
    seg_dir = os.path.join(HERE, key)
    wav = os.path.join(seg_dir, 'round_1_audio.wav')
    beats_p = os.path.join(seg_dir, 'round_1_beats.json')
    script_p = os.path.join(seg_dir, 'script.json')
    for p in (wav, beats_p, script_p):
        if not os.path.exists(p):
            print('  [%s] MISSING %s' % (key, os.path.basename(p)))
            return None

    with io.open(script_p, encoding='utf-8') as f:
        script = json.load(f)
    with io.open(beats_p, encoding='utf-8') as f:
        bmeta = json.load(f)

    # Build the flat script word list and the per-beat word ranges. The beats'
    # lines, joined, must equal narration (LINE_EQ) -- already checked in TTS,
    # but re-assert because the whole alignment depends on it.
    cat = '\n'.join(b['line'] for b in script['beats']).strip()
    assert cat == script['narration'].strip(), 'LINE_EQ failed for %s' % key

    flat, ranges = [], []          # ranges[i] = (start_idx, end_idx, beat_n)
    for b in script['beats']:
        ws = tokenize(b['line'])
        ranges.append((len(flat), len(flat) + len(ws), b['n']))
        flat.extend(ws)

    # Whisper over the whole segment.
    al = whisper_align(wav, script['narration'], model_name=model_name)
    wwords = [w['w'] for w in al['words']]
    if not wwords:
        print('  [%s] whisper returned no words' % key)
        return None

    # DP-align the full script to the full whisper list.
    mapping, notes = align_tokens(flat, wwords)
    mapping, span_notes = resolve_spans(mapping, flat, wwords)
    all_notes = notes + span_notes

    # Absolute times for each script word, clamped into its beat's exact span.
    bspans = {b['n']: b for b in bmeta['beats']}
    out_words = []
    unplaced_clamped = 0
    for k, wi in enumerate(mapping):
        if wi is None or wi >= len(al['words']):
            continue
        ww = al['words'][wi]
        # which beat does this word belong to?
        beat_n = None
        for (s0, s1, bn) in ranges:
            if s0 <= k < s1:
                beat_n = bn
                break
        bs = bspans.get(beat_n)
        if bs is None:
            continue
        t = ww['t']; e = ww['end']
        # Clamp into the beat's exact span. Whisper is a good within-beat
        # estimator but its absolute clock drifts slightly; the beat span is
        # ground truth, so the clamp is always toward the truth.
        if t < bs['start'] or e > bs['end'] or t < bs['start']:
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

    # Monotonicity invariant: card onsets must never go backwards. A decrease
    # here is a hard defect, so assert rather than paper over it.
    for a, b in zip(out_words, out_words[1:]):
        if b['t'] < a['t'] - 1e-6:
            raise AssertionError(
                'non-monotonic alignment in %s: %r @%.3f then %r @%.3f'
                % (key, a['w'], a['t'], b['w'], b['t']))

    dur = al['duration_s']
    res = {
        'segment': key,
        'wav_path': 'round_1_audio.wav',
        'duration_s': round(dur, 3),
        'beats_json': 'round_1_beats.json',
        'word_count': len(out_words),
        'clamped_words': unplaced_clamped,
        'beat_boundaries_exact': True,
        'words': out_words,
        'notes': all_notes,
    }
    with io.open(os.path.join(seg_dir, 'round_1_alignment.json'), 'w',
                 encoding='utf-8') as f:
        json.dump(res, f, indent=1, ensure_ascii=False)

    n_unplaced = sum(1 for n in all_notes if 'UNPLACED' in n or 'UNRESOLVED' in n)
    print('  [%s] %d words placed  %d beat spans  %.2fs  clamped=%d  notes=%d (unplaced=%d)'
          % (key, len(out_words), len(bmeta['beats']), dur, unplaced_clamped,
             len(all_notes), n_unplaced))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', nargs='*', default=None)
    ap.add_argument('--model', default='tiny.en')
    args = ap.parse_args()
    keys = args.segments or [k for k, _ in ORDER]
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
    out = os.path.join(HERE, '_batch_align_report.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump([{k: r[k] for k in ('segment', 'word_count', 'duration_s',
                                       'clamped_words')} for r in results],
                  f, indent=1)
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
