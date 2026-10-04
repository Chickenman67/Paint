# validate_scripts.py -- gate every segment script before it reaches TTS/alignment.
#
# The load-bearing invariant is LINE_EQ: the concatenation of the beats' `line`
# fields, joined with single newlines, must be byte-identical to `narration`.
# The aligner force-matches the WAV word-by-word against these lines and the frame
# generator cuts cards at their boundaries, so any drift here desynchronises the
# whole segment. Everything else is a quality warning.
import io
import json
import os

SEG = os.path.dirname(os.path.abspath(__file__))
ORDER = [
    ('tres2b', 4, 'TrES-2b'), ('wasp17b', 5, 'WASP-17b'), ('wasp127b', 6, 'WASP-127b'),
    ('gliese436b', 7, 'Gliese 436 b'), ('koi55', 8, 'KOI-55 b'), ('ltt9779b', 9, 'LTT 9779 b'),
    ('fomalhautb', 10, 'Fomalhaut b'), ('kelt9b', 11, 'KELT-9b'), ('psoj3185', 12, 'PSO J318.5-22'),
]
MIN_W, MAX_W = 215, 260


def main():
    print('%-12s %-4s %-6s %-6s %-9s %-6s %-5s %-5s %s'
          % ('key', 'no', 'words', 'beats', 'LINE_EQ', 's/beats', 'char', 'uniq', 'warnings'))
    fails = 0
    for key, no, name in ORDER:
        p = os.path.join(SEG, key, 'script.json')
        if not os.path.exists(p):
            print('%-12s #%-3d MISSING' % (key, no))
            fails += 1
            continue
        d = json.load(io.open(p, encoding='utf-8'))
        n = d['narration']
        b = d['beats']
        cat = '\n'.join(x['line'] for x in b)
        eq = cat.strip() == n.strip()
        wc = len(n.split())
        ids = [x['id'] for x in b]
        uniq = len(set(ids)) == len(ids)
        char = sum(1 for x in b if 'stickman' in x.get('visual', '').lower())
        # seconds per card at 200wpm
        secs = len(b) and (wc / 200.0 * 60.0) / len(b)
        warns = []
        if not eq:
            warns.append('LINE_EQ_FAIL')
        if not (MIN_W <= wc <= MAX_W):
            warns.append('WORDS_OUT_OF_BAND')
        if not uniq:
            warns.append('DUP_IDS')
        if char < 4:
            warns.append('CHAR_UNDER_4')
        if secs > 5.0:
            warns.append('CARDS_COARSE(%.1fs>5.0)' % secs)
        if any(x.get('register') not in ('void', 'cream') for x in b):
            warns.append('BAD_REGISTER')
        hard = [w for w in warns if w.endswith('FAIL') or w == 'DUP_IDS']
        if hard:
            fails += 1
        print('%-12s #%-3d %-6d %-6d %-9s %-6.1f %-5d %-5s %s'
              % (key, no, wc, len(b), eq, secs, char, uniq, ','.join(warns) or '-'))
    print('\n%d hard failures' % fails)
    return fails


if __name__ == '__main__':
    raise SystemExit(1 if main() else 0)
