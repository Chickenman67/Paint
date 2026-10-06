"""Caption-length sweep, reading the PHRASES the film actually speaks.

Where the text lives. The scene modules do NOT hold caption text as literals.
Each one defines a local closure

    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, ...)

so the string is pulled from the narration beat at render time -- `clock.ph`
returns the beat's PHRASE, which originates in segments/<chapter>/beats.json.
Sweeping the scene files for `cap('...')` literals finds nothing, which is
correct and useless (it reported 0 caption sites across all nine chapters on
the first attempt).

So this reads the beat phrases from beats.json, keeps the ones a caption
actually uses, and measures those. The user asked for ONE important phrase
rather than a block of text; the readability gate measures whether a caption
FITS and whether it READS, and neither one notices that a perfectly legible
39-character SENTENCE has already given away the ending.

Run:  python lib/_caption_lens.py
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'lib')
SEG = os.path.join(ROOT, 'segments')

MAX_CHARS = 36
MAX_WORDS = 6

CHAPTERS = ['pinegap', 'room39', 'mezhgorye', 'tomb', 'vatican',
            'area51', 'cheyenne', 'svalbard', 'fortknox']


def cap_beats(chapter):
    """Beat numbers that carry a caption, from the scene module's cap() calls."""
    path = os.path.join(LIB, '%s2_scene.py' % chapter)
    if not os.path.exists(path):
        path = os.path.join(LIB, '%s_scene.py' % chapter)
    src = io.open(path, encoding='utf-8').read()
    return sorted(set(int(n) for n in re.findall(r'cap\(\s*(\d+)\s*,', src)))


def phrases(chapter):
    p = os.path.join(SEG, chapter, 'beats.json')
    with io.open(p, encoding='utf-8') as fh:
        data = json.load(fh)
    beats = data['beats'] if isinstance(data, dict) and 'beats' in data else data
    # The narration text is the `line` field. The first two attempts of this
    # sweep read `phrase` and `text` and both reported zero captions across all
    # nine chapters -- not because no chapter is captioned, but because a wrong
    # field name reads as an empty string rather than an error. Checked the
    # actual record: {"n":1,"id":"b01","beat":"HOOK","line":"...","start":...}.
    out = {}
    for b in beats:
        i = b.get('n', b.get('i'))
        if i is None and b.get('id'):
            m = re.search(r'(\d+)', str(b['id']))
            i = int(m.group(1)) if m else None
        if i is None:
            continue
        out[int(i)] = (b.get('line') or b.get('phrase') or b.get('text')
                       or '').strip()
    return out


def main():
    rows = []
    for ch in CHAPTERS:
        try:
            ph = phrases(ch)
        except (IOError, ValueError, KeyError) as e:
            print('%-11s SKIP (%s)' % (ch, e))
            continue
        for i in cap_beats(ch):
            text = ph.get(i, '')
            if not text:
                continue
            rows.append((ch, i, len(text), len(text.split()), text))

    over = [r for r in rows if r[2] > MAX_CHARS or r[3] > MAX_WORDS]
    print('%d captioned beats across %d chapters; %d over %d chars or %d words\n'
          % (len(rows), len(CHAPTERS), len(over), MAX_CHARS, MAX_WORDS))
    if not over:
        print('none')
        return 0
    for ch, i, n, w, text in sorted(over, key=lambda r: -r[2]):
        print('%-11s b%02d  %3dch %2dw  %s' % (ch, i, n, w, text))
    return 0


if __name__ == '__main__':
    sys.exit(main())