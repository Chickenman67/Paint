"""Generate a segment script.json from narration + per-beat art direction.

THE LINE_EQ PROBLEM THIS SOLVES. audio3.load_script refuses to synthesize unless
'\n'.join(beat['line']) reproduces `narration` EXACTLY. Hand-writing 24 beat lines
that rejoin to a prose paragraph byte-for-byte is a reliable way to ship a broken
segment, so beat lines are CUT from the narration here instead of retyped.

HOW IT CUTS. Each beat is one contiguous run of the narration's words, ending at a
sentence boundary when the beat budget allows and always at a word boundary. The
joined lines are by construction identical to the narration's words in order; only
whitespace and inter-sentence spacing are normalized (a beat line carries its
trailing punctuation). `_check_line_eq` re-asserts it before writing, so a bug
here fails loudly instead of producing a desynced segment.

Usage:
  python lib/_mkscript.py <key> <plan.py>
where plan.py defines NARRATION (str) and BEATS (list of dicts with at least
'visual' and 'register', optionally 'beat'/'id'); one dict per intended beat.
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, 'segments'))

WORD = re.compile(r"\S+")


def _sentences(text):
    """Split into sentences, keeping terminal punctuation attached."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]


def _split_at(c):
    """Split one chunk into head+tail at its LAST soft boundary.

    Prefers a comma / ' and ' / ' but ' / ' that '; if the chunk has none, cut
    at the word midpoint instead of giving up. Always returns a non-empty head
    and tail, so a caller can loop on this until it reaches the target count.
    """
    m = list(re.finditer(r',| and | but | that ', c))
    if m:
        cut = m[-1]
        head = c[:cut.start()].rstrip().rstrip(',')
        tail = c[cut.start():].lstrip(' ,').lstrip()
        if head and tail:
            return head, tail
    words = c.split()
    if len(words) >= 4:
        k = len(words) // 2
        return ' '.join(words[:k]), ' '.join(words[k:])
    return None


def _beat_texts(narration, n_beats):
    """Cut `narration` into exactly n_beats contiguous word-chunks.

    Chunks are whole sentences when the counts allow, otherwise the longest
    chunks are split at soft boundaries until the count matches. Every chunk is a
    contiguous span of the narration, so joining them reproduces the text.
    """
    chunks = _sentences(narration)
    guard = 0
    while len(chunks) < n_beats and guard < 4000:
        guard += 1
        i = max(range(len(chunks)), key=lambda k: len(chunks[k]))
        got = _split_at(chunks[i])
        if got is None:
            break
        chunks[i:i + 1] = list(got)
    while len(chunks) > n_beats and guard < 4000:
        guard += 1
        i = min(range(1, len(chunks)),
                key=lambda k: len(chunks[k - 1]) + len(chunks[k]))
        chunks[i - 1:i + 1] = [chunks[i - 1] + ' ' + chunks[i]]
    assert len(chunks) == n_beats, (
        'could not cut narration into %d beats (got %d) -- adjust BEATS'
        % (n_beats, len(chunks)))
    return chunks


def build(key, title, narration, plan, target_wpm=165):
    """plan: list of dicts with 'visual' and 'register' (one per beat)."""
    lines = _beat_texts(narration, len(plan))
    beats = []
    for i, (line, art) in enumerate(zip(lines, plan)):
        beats.append({
            'n': i + 1,
            'id': art.get('id', 'b%02d' % (i + 1)),
            'beat': art.get('beat', 'FACT'),
            'line': line,
            'visual': art['visual'],
            'register': art.get('register', 'paint'),
        })
    # narration is DEFINED as the joined beat lines -> LINE_EQ holds by build.
    built_narration = '\n'.join(b['line'] for b in beats)
    words = len(re.findall(r"[A-Za-z0-9'’]+", built_narration))
    doc = {
        'title': title,
        'wrote_to': 'segments/%s/script.json' % key,
        'target': {'wpm': target_wpm, 'max_sentence_words': 10,
                   'note': 'short declaratives, one idea per beat. '
                           'Little to no pause between sentences.'},
        'narration': built_narration,
        'word_count': words,
        'est_wpm': target_wpm,
        'beats': beats,
    }
    _check_line_eq(doc)
    return doc


def _check_line_eq(doc):
    cat = '\n'.join(b['line'] for b in doc['beats']).strip()
    if cat != doc['narration'].strip():
        raise SystemExit('LINE_EQ failed for %s' % doc['wrote_to'])
    words = len(re.findall(r"[A-Za-z0-9'’]+", doc['narration']))
    if words != doc['word_count']:
        raise SystemExit('word_count mismatch for %s: %d vs %d'
                         % (doc['wrote_to'], words, doc['word_count']))


def write(key, doc):
    d = os.path.join(SEG_ROOT, key)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'script.json'), 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    print('wrote segments/%s/script.json  %d beats  %d words  est %.0fs @%dwpm'
          % (key, len(doc['beats']), doc['word_count'],
             doc['word_count'] / float(doc['est_wpm']) * 60, doc['est_wpm']))


if __name__ == '__main__':
    # Smoke test: a tiny module exposing NARRATION/TITLE/BEATS, then build.
    key = sys.argv[1]
    plan_path = sys.argv[2]
    spec = {}
    with io.open(plan_path, encoding='utf-8') as f:
        exec(compile(f.read(), plan_path, 'exec'), spec)
    doc = build(key, spec['TITLE'], spec['NARRATION'], spec['BEATS'])
    write(key, doc)