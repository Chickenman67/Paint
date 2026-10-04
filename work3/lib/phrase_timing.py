# work3/lib/phrase_timing.py -- split a narration LINE into digestible PHRASES
# and give each phrase a {text, start, end} span, using the beat's [start,end]
# from beats.json and distributing the span by word-count proportion.
#
# This feeds the reveal engine: a card flips to its next phrase exactly when the
# narrator reaches that phrase. The beat boundaries in beats.json are exact
# (they ARE the audio file's layout, not an estimate). Within a beat we
# interpolate by word count -- no forced aligner -- and we anchor to BOTH ends,
# so the phrases tile the beat and can never drift off it.
#
# DETERMINISTIC and ASR-FREE: pure text processing plus the three known numbers
# (beat start, beat end, beat word count). Same input -> same output, always.
#
# Reads   work3/segments/<KEY>/beats.json
# Uses    work3/lib/audio3.py  _WORD_RE  (byte-identical to the aligner's regex)
#
# WORD-COUNT CONSISTENCY: phrases partition the line's word sequence, so the
# per-phrase word counts sum EXACTLY to the beat's word count and the spans tile
# [beat.start, beat.end] with no gaps or overlaps. The same _WORD_RE the aligner
# uses counts words, so beat boundaries line up with word onsets.

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .../work3/lib
sys.path.insert(0, HERE)

from audio3 import _WORD_RE                              # noqa: E402

# Phrase length bounds (words). The brief: short digestible phrases.
#
# MAX_PHRASE_WORDS IS 8, NOT 6. A narration sentence is already the unit of
# meaning; when the cap is lower than a typical sentence, the splitter has to
# cut MID-CLAUSE to fit, and the caption reads as a severed fragment ("It is
# run jointly by the" / "United States and Australia."). With the cap at 8 and
# the scripts written in short declaratives (<=8 words), each beat line is
# exactly one phrase and the caption always shows a whole thought.
MIN_PHRASE_WORDS = 2
MAX_PHRASE_WORDS = 8

# Words that end a phrase when they appear mid-sentence (clause boundaries).
# Matched case-insensitively against the bare word. The brief names "and", "but"
# and "then"; the rest are the same class of discourse marker.
CLAUSE_TOKENS = frozenset({
    'and', 'but', 'then', 'so', 'because', 'while', 'when', 'which', 'that',
    'or', 'yet', 'though', 'although', 'unless', 'until', 'since', 'after',
    'before',
})

# Cost of cutting a phrase after a given word (lower is better). A cut after a
# sentence end or a clause head is free; a cut after a comma is cheap; any other
# cut (mid-clause) is expensive but still allowed if the bounds require it.
CUT_FREE, CUT_COMMA, CUT_MIDSENTENCE = 0, 1, 6

_SENT_END = ('.', '!', '?')

# A word plus any punctuation glued to it. The tokenizer peels trailing
# punctuation off the word, so "down." is one WORD 'down' with punct='.', and
# "KOI-55." is WORD 'KOI-55' with punct='.'. The punct group captures ONLY
# punctuation marks, never whitespace or newlines -- capturing them would bake
# the layout whitespace into the token and render as double-spaces.
#
# The inner group takes [A-Za-z0-9] runs joined by '.', '-', "'" OR a COMMA
# BETWEEN DIGITS, so "18,000" stays a single token instead of splitting into
# "18," / "000" -- which put a caption break inside a number. A comma only
# counts when a digit follows it, so "Deep in the desert, in the center" is
# unaffected.
_WORDTOK_RE = re.compile(
    r"([A-Za-z0-9]+(?:[.'’\-][A-Za-z0-9]+|,(?=[0-9]))*)"
    r"([.,;:!?'\")\]]*)")


def _tokenize_words(text):
    """Split text into a list of (word, trailing_punct).

    Punctuation is ATTACHED to the word it follows, never emitted on its own.
    That is what makes the partition below order-preserving by construction: a
    phrase is a contiguous span of these tokens, so the rendered phrases are
    always a faithful, in-order rendering of the source line.
    """
    out = []
    for m in _WORDTOK_RE.finditer(text):
        out.append((m.group(1), m.group(2)))
    return out


def _cut_cost(tokens, j, n):
    """Cost of ending a phrase after word index j (0-based)."""
    if j == n - 1:
        return 0                              # end of line: free
    word, punct = tokens[j]
    if any(c in _SENT_END for c in punct):
        return CUT_FREE
    if word.lower() in CLAUSE_TOKENS:
        return CUT_FREE
    if ',' in punct or ';' in punct or ':' in punct:
        return CUT_COMMA
    return CUT_MIDSENTENCE


def _render(tokens):
    """Render word tokens back to text, re-attaching punctuation without the
    spaces the tokenizer implied ('planet.' not 'planet .')."""
    parts = []
    for w, p in tokens:
        parts.append(w + p if p else w)
    return ' '.join(parts)


def split_phrases(line, min_words=MIN_PHRASE_WORDS, max_words=MAX_PHRASE_WORDS):
    """Split `line` into phrases of 2-6 words, cutting on clause boundaries.

    Deterministic, ASR-free, and ORDER-PRESERVING: the phrases are a contiguous
    partition of the line's word sequence, so no word can ever move across a
    boundary (an earlier version of this file "balanced" short groups by moving
    words across punctuation and produced nonsense like "Five KOI-55 ." -- that
    class of bug is structurally impossible here).

    The partition is chosen by an exact dynamic program over word counts:
      - a group may hold min_words..max_words words;
      - cost 0 for cutting at a sentence end or a clause head ("and", "but",
        "then", ...), cost 1 after a comma, cost 6 mid-clause;
      - the final cut (end of line) is free.
    The cheapest partition wins, ties broken toward the EARLIER, longer first
    group so the output is stable.

    If the line has fewer than min_words words, one group is returned as-is --
    there is no legal partition, and returning the whole line beats dropping or
    reordering it.

    Returns a list of phrase strings whose word counts sum to the line's.
    """
    tokens = _tokenize_words(line)
    n = len(tokens)
    if n == 0:
        return []
    if n < min_words:
        return [_render(tokens)]

    min_words = max(1, min(min_words, n))
    max_words = max(min_words, min(max_words, n))

    # dp[i] = (cost, cut_end_index, path) for the cheapest partition of words i..n-1
    dp = [None] * (n + 1)
    dp[n] = (0, n, ())
    for i in range(n - 1, -1, -1):
        best = None
        for j in range(i + min_words - 1, min(i + max_words, n)):
            if dp[j + 1] is None:
                continue
            cost = _cut_cost(tokens, j, n) + dp[j + 1][0]
            # Tie-break: prefer the LONGER first group (larger j) so the result
            # is deterministic and does not fragment needlessly.
            key = (cost, -j)
            if best is None or key < best[0]:
                best = (key, j, dp[j + 1][2])
        if best is not None:
            dp[i] = (best[0][0], best[1], best[2])

    # Rebuild the partition from dp[0].
    spans = []
    i = 0
    while i < n:
        j = dp[i][1]
        spans.append(_render(tokens[i:j + 1]))
        i = j + 1
    return spans


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------

def _phrase_words(phrase):
    return _WORD_RE.findall(phrase)


def phrases_with_timing(line, beat):
    """Return [{text, start, end, w0, w1}] for one beat's line.

    `beat` is a beats.json entry with 'line', 'start', 'end', 'words'. The line
    is split into phrases and laid out proportionally to word count across
    [beat.start, beat.end]:

        t(i) = beat.start + (beat.end - beat.start) * (i / total_words)

    Phrase k spans t(cum_k) .. t(cum_{k+1}). The first phrase starts exactly at
    beat.start and the last ends exactly at beat.end, so the spans tile the beat
    with no gaps; adjacent spans share an endpoint, which is the cut point.
    """
    phrases = split_phrases(line)
    if not phrases:
        return []

    weights = [max(1, len(_phrase_words(p))) for p in phrases]
    total_w = float(sum(weights))

    t0 = float(beat['start'])
    t1 = float(beat['end'])
    span = t1 - t0

    out = []
    cum = 0
    for p, w in zip(phrases, weights):
        s = t0 + span * (cum / total_w)
        cum += w
        e = t0 + span * (cum / total_w)
        out.append({
            'text': p,
            'start': round(s, 3),
            'end': round(e, 3),
            'w0': cum - w,
            'w1': cum,
        })
    # Pin the ends exactly to the beat so the tiles are airtight.
    if out:
        out[0]['start'] = round(t0, 3)
        out[-1]['end'] = round(t1, 3)
    return out


def segment_phrases(beats_json_path, line=None):
    """Load beats.json and return per-beat phrase timings.

    With no `line`, returns {beat_id: [phrases]} for every beat. With `line`,
    returns the phrase list for the single beat whose line matches exactly.
    """
    with io.open(beats_json_path, encoding='utf-8') as f:
        meta = json.load(f)
    beats = meta['beats']

    if line is None:
        return {b['id']: phrases_with_timing(b['line'], b) for b in beats}

    matches = [b for b in beats if b['line'].strip() == line.strip()]
    if not matches:
        raise ValueError('no beat matches the given line')
    if len(matches) > 1:
        raise ValueError('line matches %d beats -- pass a beat id instead'
                         % len(matches))
    return phrases_with_timing(matches[0]['line'], matches[0])


def all_phrases_timed(beats_json_path):
    """Flat list of every phrase in the segment, in order, with timing and the
    beat it belongs to. This is the form the reveal engine wants."""
    with io.open(beats_json_path, encoding='utf-8') as f:
        meta = json.load(f)
    flat = []
    for b in meta['beats']:
        for ph in phrases_with_timing(b['line'], b):
            ph = dict(ph)
            ph['beat_id'] = b['id']
            ph['beat_n'] = b['n']
            flat.append(ph)
    return flat


# --- CLI --------------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('beats_json', help='path to a beats.json')
    ap.add_argument('--line', default=None,
                    help='show phrases for only this narration line')
    ap.add_argument('--all', action='store_true',
                    help='dump every phrase in the segment with timings')
    args = ap.parse_args()

    if args.all:
        for ph in all_phrases_timed(args.beats_json):
            print('%7.3f - %7.3f  [beat %2d %-26s] %s'
                  % (ph['start'], ph['end'], ph['beat_n'], ph['beat_id'],
                     ph['text']))
    else:
        with io.open(args.beats_json, encoding='utf-8') as f:
            meta = json.load(f)
        if args.line is not None:
            for ph in segment_phrases(args.beats_json, args.line):
                print('%7.3f - %7.3f  %s' % (ph['start'], ph['end'], ph['text']))
        else:
            b0 = meta['beats'][0]
            print('beat 1  %.3f - %.3f  (%dw)  %s'
                  % (b0['start'], b0['end'], b0['words'], b0['line']))
            for ph in phrases_with_timing(b0['line'], b0):
                print('   %7.3f - %7.3f  %s'
                      % (ph['start'], ph['end'], ph['text']))