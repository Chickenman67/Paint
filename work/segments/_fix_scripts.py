# _fix_scripts.py -- regenerate narration + word_count from beats for every v2
# script, guaranteeing the LINE_EQ invariant:
#     '\n'.join(beat.line).strip() == narration.strip()
#
# The card and aligner layers depend on this exact equality. When a script is
# hand-edited, the narration block is the part that drifts, so we always derive
# it from the beats (the beats are the source of truth) and recompute word_count.
#
# Safe to re-run any time. Idempotent.

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _batch_audio import load_script, words  # noqa: E402

ORDER = [
    'tres2b', 'wasp17b', 'wasp127b', 'gliese436b', 'koi55', 'ltt9779b',
    'fomalhautb', 'kelt9b', 'psoj3185',
]


def rebuild(key):
    p = os.path.join(HERE, key, 'script.json')
    d = json.load(io.open(p, encoding='utf-8'))
    beats = d['beats']
    d['narration'] = '\n'.join(b['line'] for b in beats).strip()
    d['word_count'] = len(words(d['narration']))
    d['est_wpm'] = 160
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    return d


def report(d):
    nar = d['narration']
    ls = [len(s.split()) for s in re.split(r'(?<=[.!?])\s+', nar) if s.strip()]
    ls_sorted = sorted(ls)
    med = ls_sorted[len(ls_sorted) // 2] if ls else 0
    over = sum(1 for x in ls if x > 10)
    joined = '\n'.join(b['line'] for b in d['beats']).strip()
    eq = joined == nar.strip()
    return med, over, len(ls), eq


if __name__ == '__main__':
    keys = sys.argv[1:] or ORDER
    print('%-12s %5s %5s %5s %6s %6s %s'
          % ('seg', 'words', 'beats', 'sents', 'med_s', '>10w', 'LINE_EQ'))
    tot = 0
    for k in keys:
        d = rebuild(k)
        med, over, ns, eq = report(d)
        tot += d['word_count']
        print('%-12s %5d %5d %5d %6.1f %6d %s'
              % (k, d['word_count'], len(d['beats']), ns, med, over,
                 'ok' if eq else '** MISMATCH **'))
    print('TOTAL %d words -> %.1f min at 160wpm' % (tot, tot / 160))
