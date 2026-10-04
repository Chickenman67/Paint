"""Finalize the PSR B1257+12 alignment: DP word match + re-snapped card schedule.

This does NOT re-run whisper. round_1_alignment.json already holds the per-word
onsets whisper measured over the real audio; re-running it would cost minutes and
return the same list. This reads that list, re-matches the 317 script words to it
with the DP aligner in _align_dp.py, re-snaps all 31 cards, validates, and writes
both outputs.

It is separate from _align_r1.py because that file is being edited concurrently
by another agent on this segment; this path is idempotent and can be re-run.

Why the DP aligner rather than _align_r1.py's greedy walk: whisper mishears
several words in this script ("weigh"->"way", "Draugr"->"Drouger", "B1257"->
"B257", "twenty-five"->"25") and the greedy walk cascades off the first miss,
leaving 6 of 31 card anchors snapped to the wrong onset.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from scripts import PSRB1257_SCRIPT
from _align_dp import align_tokens, resolve_spans

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = 0.20    # _schedule.py GEO['snap_rule'] / GEO['first_word_rule']
TAIL = 0.40    # _schedule.py TAIL
LONG_CARD_S = 5.0
DRIFT_LIMIT_S = 0.30   # CLAUDE.md §8 'won' criteria
WPM_LOW, WPM_HIGH = 190, 213


def main():
    align_path = os.path.join(HERE, 'round_1_alignment.json')
    sched_path = os.path.join(HERE, 'round_1_card_schedule.json')
    pred_path = os.path.join(HERE, '_schedule_predicted_backup.json')

    with open(align_path, encoding='utf-8') as f:
        al = json.load(f)
    words = al['words']
    ww = [x['w'] for x in words]
    dur = al['duration_s']

    sw = PSRB1257_SCRIPT.strip().split()
    print(f'script words  {len(sw)}')
    print(f'whisper words {len(ww)}  ({len(ww)-len(sw):+d})')
    print(f'audio         {dur:.2f}s  {len(sw)/dur*60:.1f} wpm')

    mp, notes = align_tokens(sw, ww)
    mp, notes2 = resolve_spans(mp, sw, ww)
    unplaced = [i for i, x in enumerate(mp) if x is None]
    print(f'placed        {len(sw)-len(unplaced)}/{len(sw)}  unplaced={len(unplaced)}')
    for n in notes:
        if 'near-miss' in n or 'UNPLACED' in n:
            print(n)
    for n in notes2:
        print(n)

    # The invariant the card scheduler needs is NON-DECREASING, not strictly
    # increasing: whisper legitimately merges two script words into one token,
    # so equal indices are correct, not a defect. Only a decrease is a failure.
    pairs = [(mp[i], mp[i + 1]) for i in range(len(mp) - 1)
             if mp[i] is not None and mp[i + 1] is not None]
    merges = [(i, x) for i, (x, y) in enumerate(pairs) if x == y]
    drops = [(i, x, y) for i, (x, y) in enumerate(pairs) if x > y]
    print(f'monotonic (non-decreasing): {not drops}   decreases={len(drops)}')
    print(f'merged pairs (equal index, legitimate): {len(merges)}')
    for i, x in merges:
        print(f"  script[{i}]={sw[i]!r} + script[{i+1}]={sw[i+1]!r} "
              f"both at whisper[{x}]={ww[x]!r}")

    with open(pred_path, encoding='utf-8') as f:
        sched = json.load(f)
    cards = sched['cards']
    pred = {c['n']: (c['start'], c['end']) for c in cards}

    # Card start = onset of its first_word_index word. Card end = next card's
    # start (hard cut, §5.3). Last card ends at its final word + TAIL.
    starts = []
    for c in cards:
        wi = min(max(int(c['first_word_index']), 0), len(words) - 1)
        starts.append(float(words[mp[wi]]['t']))

    snapped = []
    for idx, c in enumerate(cards):
        ps, pe = pred[c['n']]
        start = max(0.0, starts[idx] - (LEAD if idx == 0 else 0.0))
        if idx + 1 < len(cards):
            end = starts[idx + 1]
        else:
            last_wi = min(c['first_word_index'] + c['words'] - 1, len(sw) - 1)
            end = float(words[mp[last_wi]]['end']) + TAIL
        end = min(end, dur)
        start = min(start, end)
        c['start'] = round(start, 2)
        c['end'] = round(end, 2)
        c['duration'] = round(end - start, 2)
        c['type'] = 'hold'
        c['transition_in'] = 'snap'
        c['timing_source'] = 'aligned_word_onset'
        c['timing_predicted_start'] = ps
        c['timing_predicted_end'] = pe
        c['timing_delta_s'] = round(start - ps, 2)
        wi = int(c['first_word_index'])
        c['_align_word_index'] = int(mp[wi])
        c['_align_word'] = words[mp[wi]]['w']
        c['_align_word_novel'] = sw[wi]
        snapped.append(c)

    sched['cards'] = snapped
    sched['duration_s'] = round(max(c['end'] for c in snapped), 2)
    sched['timing'] = {
        'source': 'round_1_alignment.json whisper word onsets (lib/align.py)',
        'matcher': ('_align_dp.py Needleman-Wunsch over canonicalised tokens '
                    '(number folding, punctuation/hyphen stripping, similarity '
                    'threshold, known-mishear table) + span resolution'),
        'rule': (f'card n starts at the onset of its first_word_index word '
                 f'(card 1 minus {LEAD}s); card n ends at the onset of card '
                 f'n+1 first word; last card ends at its final word + {TAIL}s'),
        'lead_s': LEAD,
        'tail_s': TAIL,
        'audio_duration_s': round(dur, 2),
        'predicted_schedule_discarded': True,
        'script_words_placed': len(sw) - len(unplaced),
        'script_words_unplaced': len(unplaced),
    }
    al['card_schedule'] = [
        {'card': c['id'], 'n': c['n'], 'start': c['start'], 'end': c['end'],
         'type': c['type'], 'motion': c['motion']} for c in snapped
    ]
    al['wav_path'] = 'round_1_audio.wav'
    al['matcher'] = sched['timing']['matcher']
    al['script_words_placed'] = len(sw) - len(unplaced)
    al['script_words_unplaced'] = len(unplaced)

    with open(align_path, 'w', encoding='utf-8') as f:
        json.dump(al, f, indent=2)
    with open(sched_path, 'w', encoding='utf-8') as f:
        json.dump(sched, f, indent=1, ensure_ascii=False)

    # ---- sanity checks (§5 / §8) -----------------------------------------
    errs = []
    if len(snapped) != 31:
        errs.append(f'expected 31 cards, got {len(snapped)}')
    for c in snapped:
        if c['end'] <= c['start']:
            errs.append(f"card {c['n']} ({c['id']}): non-positive duration")
        if c['end'] > dur + 0.01:
            errs.append(f"card {c['n']}: end {c['end']} > audio {dur:.2f}")
    for a, b in zip(snapped, snapped[1:]):
        if b['start'] < a['start']:
            errs.append(f"cards {a['n']}->{b['n']}: non-monotonic")
        if abs(b['start'] - a['end']) > 0.005:
            errs.append(f"cards {a['n']}->{b['n']}: gap {b['start']-a['end']:+.3f}s != 0")
    first_word_t = snapped[0]['start'] + LEAD
    if first_word_t > 0.30:
        errs.append(f'first word at {first_word_t:.2f}s > 0.30s (5.5)')

    span = snapped[-1]['end'] - snapped[0]['start']
    pspan = pred[31][1] - pred[1][0]
    maxdelta = max(abs(c['timing_delta_s']) for c in snapped)
    uncovered = [c['id'] for c in snapped if c['first_word_index'] in set(unplaced)]

    print()
    print(f'cards         {len(snapped)}   all have start+end: '
          f'{all("start" in c and "end" in c for c in snapped)}')
    print(f'schedule      {snapped[0]["start"]:.2f}s -> {snapped[-1]["end"]:.2f}s '
          f'(span {span:.2f}s)')
    print(f'audio         {dur:.2f}s')
    print(f'first word    t={first_word_t:.2f}s  (needs <= 0.30s)')
    print(f'predicted     {pred[1][0]:.2f}s -> {pred[31][1]:.2f}s (span {pspan:.2f}s)')
    print(f'max |delta|   {maxdelta:.2f}s  <- how far the predicted schedule was off')
    print(f'drift         {span-pspan:+.2f}s end-to-end vs prediction')
    print(f'anchor words  {len(sw)-len(unplaced)}/{len(sw)} placed; '
          f'cards anchored on an unplaced word: {uncovered or "none"}')
    longs = [c for c in snapped if c['duration'] > LONG_CARD_S]
    shorts = [c for c in snapped if c['duration'] < 2.0]
    print(f'cards >{LONG_CARD_S}s  {len(longs)}  '
          f'(need splitting at a clause break)')
    for c in longs:
        print(f"   {c['n']:>2} {c['id']:<22} {c['duration']:>5.2f}s clauses {c['clauses']}")
    print(f'cards <2.0s   {len(shorts)}')
    for c in shorts:
        print(f"   {c['n']:>2} {c['id']:<22} {c['duration']:>5.2f}s ({c['words']}w)")
    print()
    if errs:
        print('SANITY CHECK FAILED')
        for e in errs:
            print('  ! ' + e)
        raise SystemExit(1)
    print('all sanity checks pass')
    print()
    print(f"  {'n':>2} {'id':<22} {'start-end':>16} {'dur':>6}  anchor")
    for c in snapped:
        print(f"  {c['n']:>2} {c['id']:<22} {c['start']:>7.2f}-{c['end']:>6.2f} "
              f"{c['duration']:>6.2f}  {c['_align_word_novel']!r} -> "
              f"whisper[{c['_align_word_index']}]={c['_align_word']!r} "
              f"(d{c['timing_delta_s']:+.2f})")


if __name__ == '__main__':
    main()
