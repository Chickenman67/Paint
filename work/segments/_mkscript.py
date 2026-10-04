# _mkscript.py -- write a <seg>/script.json with narration and word_count
# DERIVED from the beat lines, so LINE_EQ can never drift.
#
# The v2 pipeline (lib) reads:
#   narration  = the whole spoken text
#   beats[i].line = one clause per beat
# and asserts that joining the beat lines reproduces the narration exactly
# (LINE_EQ). Hand-maintaining both copies is how they drift -- an earlier
# psrb1257 draft kept a duplicated clause in `narration` after the beat had
# already been fixed, and the two no longer matched.
#
# This helper is the single writer: supply the BEATS, and the narration and the
# word count are computed with the SAME regex the aligner and TTS use
# (lib._batch_audio._WORD_RE), so word_count always equals what the pipeline
# will count.
#
# usage:  python _mkscript.py <seg> <title>
#         (edit the BEATS list below, then run)

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from _batch_audio import _WORD_RE          # noqa: E402


def build(seg, title, beats):
    """beats: list of (id, beat_kind, line, visual). Returns the script dict."""
    narration = '\n'.join(b[2] for b in beats).strip()
    wc = len(_WORD_RE.findall(narration))
    out = []
    for i, (bid, kind, line, visual) in enumerate(beats, start=1):
        out.append({'n': i, 'id': bid, 'beat': kind, 'line': line,
                    'visual': visual, 'register': 'void'})
    return {
        'title': title,
        'narration': narration,
        'word_count': wc,
        'est_wpm': 160,
        'beats': out,
    }


def write(seg, title, beats, pred_wpm=160.0, gap_s=0.30):
    d = build(seg, title, beats)
    n = len(beats)
    pred = d['word_count'] / pred_wpm * 60.0 + (n - 1) * gap_s
    path = os.path.join(HERE, seg, 'script.json')
    with io.open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    print('%s: %d beats, %d words, pred %.1fs -> %s'
          % (seg, n, d['word_count'], pred, path))
    return d


# ---------------------------------------------------------------------------

PSR = [
    ('hook_dead_star', 'HOOK',
     'This star died a long time ago. It is still out there, spinning.',
     'Void; a small bright pulsar point dead-center, cream stickman small at '
     'lower left, deadpan grim.'),
    ('spinning_fast', 'HOOK',
     'It spins so fast that it is turning itself into a smear of light.',
     'The pulsar with concentric blur rings, red label "a smear of light".'),
    ('beam_sweeps', 'SETUP',
     'A beam of radiation sweeps out of it. It does this twice, every second.',
     'Two red beams sweeping from the pulsar point like a lighthouse, '
     'stickman shielding his eyes.'),
    ('planets_around', 'SETUP',
     'And there are planets. Real planets. Orbiting it right now.',
     'Three small planets on tight orbits, red label "planets, still there".'),
    ('named_undead', 'SETUP',
     'They are named after the undead. The first one is called Draugr.',
     'Name card: "DRAUGR" in red, stickman below looking uneasy.'),
    ('draugr_corpse', 'ESCALATE',
     'A draugr is a corpse that walks. That is the name they gave it.',
     'A red-outlined coffin-like box around a rock, red label "a corpse that '
     'walks".'),
    ('named_all_of_them', 'ESCALATE',
     'The next two are named Poltergeist and Lich. It does not get kinder.',
     'Three red name plates in a row: DRAUGR / POLTERGEIST / LICH.'),
    ('first_around_dead', 'ESCALATE',
     'These are the first planets ever found orbiting a dead star.',
     'The pulsar ringed by planets, red box around the system, label "first '
     'ever found".'),
    ('should_not_exist', 'ESCALATE',
     'They should not exist. A dead star has nothing left to hold on to.',
     'A planet with a slack broken orbit fading out, red X, "should not exist".'),
    ('carbon_dense', 'DISTURB',
     'The planets are carbon. They are the densest rock in the whole galaxy.',
     'A dark carbon-black planet with a down-arrow onto it, "densest rock".'),
    ('fist_of_coal', 'DISTURB',
     'A fist of coal you could hold in one hand, if you could ever stand on it.',
     'A single black carbon planet, hand-sized red box, "you could hold it".'),
    ('orbits_tight', 'DISTURB',
     'They whip around a dead star in a couple of hours each.',
     'A tight orbit path with the planet nearly touching the pulsar, "hours, not years".'),
    ('solar_system_size', 'DISTURB',
     'And the entire system is about the size of our own solar system.',
     'The whole system drawn small inside a red box, "about our size".'),
    ('graveyard', 'OUTRO',
     'A graveyard the size of ours, turning over and over in the dark.',
     'The graveyard system alone in a big dark frame, stickman small, sad.'),
    ('outro_beam', 'OUTRO',
     'The dead star beams at you. The planets do not care. They keep going.',
     'The pulsar beaming red at the stickman, who shrugs it off, deadpan.'),
]

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'psrb1257':
        write('psrb1257', 'PSR B1257+12 - the planets around a dead star', PSR)
    else:
        print('edit the BEATS list, then: python _mkscript.py <seg>')
