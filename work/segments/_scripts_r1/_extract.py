# _extract.py -- pull the 9 segment scripts out of the script workflow's journal
# and save them under their canonical segment keys, with a consistency report.
import io
import json
import os

JOURNAL = ('C:/Users/david/.claude/projects/C--VIBE-CODE-CENTRAL-Gauntlet3/'
           '5c3a37e7-d13e-4124-b03b-f1a0685223d2/subagents/workflows/wf_9aa63f27-ab0/journal.jsonl')
OUT = os.path.dirname(os.path.abspath(__file__))

CANON = [
    ('TrES-2b', 4, 'tres2b'),
    ('WASP-17b', 5, 'wasp17b'),
    ('WASP-127b', 6, 'wasp127b'),
    ('Gliese 436', 7, 'gliese436b'),
    ('KOI-55', 8, 'koi55'),
    ('LTT 9779', 9, 'ltt9779b'),
    ('Fomalhaut', 10, 'fomalhautb'),
    ('KELT-9b', 11, 'kelt9b'),
    ('PSO J318', 12, 'psoj3185'),
]


def main():
    rows = []
    for line in io.open(JOURNAL, encoding='utf-8'):
        d = json.loads(line)
        if d.get('type') != 'result':
            continue
        r = d.get('result')
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except Exception:
                continue
        if isinstance(r, dict) and 'narration' in r:
            rows.append(r)

    seen = set()
    for r in rows:
        title = r['title']
        for name, num, key in CANON:
            if name in title and key not in seen:
                seen.add(key)
                r['_seg_no'] = num
                r['_key'] = key
                with io.open(os.path.join(OUT, key + '.json'), 'w', encoding='utf-8') as f:
                    json.dump(r, f, indent=1, ensure_ascii=False)
                break

    print('%-12s %-4s %-6s %-6s %-9s %-s' % ('key', 'no', 'words', 'beats', 'line_eq', 'title'))
    for name, num, key in CANON:
        p = os.path.join(OUT, key + '.json')
        if not os.path.exists(p):
            print('%-12s MISSING' % key)
            continue
        d = json.load(io.open(p, encoding='utf-8'))
        cat = '\n'.join(b['line'] for b in d['beats'])
        eq = cat.strip() == d['narration'].strip()
        wc = len(d['narration'].split())
        print('%-12s #%-3d %-6d %-6d %-9s %s'
              % (key, num, wc, len(d['beats']), eq, d['title'][:44].replace('—', '-')))


if __name__ == '__main__':
    main()
