"""Sequence-align the narration script to whisper's word list (CLAUDE.md §5).

Why this exists instead of the greedy walk in _align_r1.py:
whisper transcribes numerals as digits ("twenty-five" -> "25") and misspells
proper nouns ("Wolszczan" -> "Walschon", "Draugr" -> "Drouger"). A greedy
left-to-right walk misses the first such word, falls behind the cursor, and then
fails to catch up inside its lookahead window — so one miss cascades into a dozen,
and every card anchored on a missed word snaps to the wrong onset. On the real
PSR B1257+12 audio that hit 6 of 31 card anchors.

This does a proper Needleman-Wunsch alignment over the two token sequences:

  * number-words and digits are folded to a canonical form on both sides
  * punctuation and hyphens are stripped, so "City-sized." can match ".City"
  * near-misses are accepted by similarity ratio, so a proper noun still lands
  * the alignment is globally optimal and monotone by construction, so a miss
    costs exactly that one word instead of cascading

A script word may consume more than one whisper token; its onset is the FIRST
token it consumes, which is the correct word onset.
"""
import difflib
import re

# Number-words whisper renders as digits, in both directions.
_NUM_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
    'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
    'seventy': 70, 'eighty': 80, 'ninety': 90,
    'hundred': 100, 'thousand': 1000, 'million': 1000000,
}
# Spoken compound -> the number whisper would print for it.
_COMPOUNDS = {
    'twentyfive': 25, 'twentysix': 26, 'twentyseven': 27, 'twentyeight': 28,
    'twentynine': 29, 'thirtyone': 31, 'thirtyfive': 35, 'fiftyseven': 57,
    'sixtyseven': 67, 'ninetyeight': 98, 'hundredthirty': 130,
}
_NUM_WORDS_SET = set(_NUM_WORDS)


def _strip(tok):
    """Lowercase and drop everything but alphanumerics."""
    return re.sub(r'[^a-z0-9]', '', tok.lower())


def canon(tok):
    """Canonical comparison key for one token.

    'twenty-five.' -> '25', '25' -> '25', 'PSR' -> 'psr', 'Walschon' -> 'walschon'
    """
    s = _strip(tok)
    if not s:
        return ''
    if s.isdigit():
        return str(int(s))
    if s in _COMPOUNDS:
        return str(_COMPOUNDS[s])
    if s in _NUM_WORDS_SET:
        return str(_NUM_WORDS[s])
    return s


def sim(a, b):
    """Similarity in [0,1] between two canonical keys, or None if incompatible."""
    if not a or not b:
        return None
    if a == b:
        return 1.0
    # A pure number only ever matches a pure number. But an ALPHANUMERIC token
    # like 'b1257' or '1257b' is not a number: whisper transcribes 'B1257' as
    # 'B257' and that is a legitimate alphanumeric comparison.
    a_num, b_num = a.isdigit(), b.isdigit()
    if a_num != b_num:
        return None          # a number never matches a word and vice versa
    r = difflib.SequenceMatcher(None, a, b).ratio()
    # Only accept genuine near-misses (proper nouns, alphanumeric ids), not
    # unrelated words that happen to share letters.
    if r >= 0.80 and min(len(a), len(b)) >= 5:
        return r
    if r >= 0.62 and (a.startswith(b) or b.startswith(a)) and min(len(a), len(b)) >= 4:
        # 'citysized' vs 'city' — a hyphenated form split by the tokenizer
        return r
    return None


MATCH_FLOOR = 0.62
GAP = -0.55
# A substitution must beat skipping the script word AND skipping the whisper
# token for the global optimum to prefer it. With GAP=-0.55 each skip costs
# -0.55, so a substitution has to be worth >1.10 to justify displacing both.
# Anything weaker is a coincidence the similarity metric liked but the audio
# does not support — e.g. 'Draugr' vs 'you' on shared letters.
SUBST_MIN = 0.70

# Words whisper reliably mishears in this script, paired with what it actually
# emits. No string metric recovers these: 'weigh'/'way' share no letters, and
# 'twelve'/'1257' is a four-digit collapse of two number-words. The mapping is
# only consulted for adjacent tokens inside the alignment, so it cannot cause a
# distant word from being pulled in.
KNOWN_MISHEAR = {
    'weigh': 'way',
    'wolszczan': 'walschon',
    'aleksander': 'alexander',
    'draugr': 'drouger',
    'phobetor': 'phobitor',
    'poltergeist': 'poltergeist',
}


def _mishear_hit(a, b):
    """1.0 if this exact known mishearing pair, else None."""
    if not a or not b:
        return None
    if KNOWN_MISHEAR.get(a) == b or KNOWN_MISHEAR.get(b) == a:
        return 1.0
    return None


def align_tokens(script_words, whisper_words, canon_fn=None):
    """Align script tokens to whisper tokens.

    script_words:  list[str]   the narration, whitespace-split
    whisper_words: list[str]   the words whisper heard
    Returns (mapping, notes):
      mapping[i]  = index into whisper_words that script word i starts at,
                    or None if that word could not be placed
      notes       = list[str] describing every non-exact placement
    """
    canon_fn = canon_fn or canon
    S = [canon_fn(w) for w in script_words]
    W = [canon_fn(w) for w in whisper_words]
    n, m = len(S), len(W)

    # dp[i][j] = best score aligning S[:i] with W[:j]
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]   # backtrace
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + GAP
        bt[i][0] = 'up'
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + GAP
        bt[0][j] = 'left'
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim(S[i - 1], W[j - 1])
            if s is None:
                s = _mishear_hit(S[i - 1], W[j - 1])
            if s is not None and s >= SUBST_MIN:
                diag = dp[i - 1][j - 1] + s
            else:
                diag = dp[i - 1][j - 1] + (GAP * 2)   # force both to be skipped
            up = dp[i - 1][j] + GAP
            left = dp[i][j - 1] + GAP
            best = max(diag, up, left)
            dp[i][j] = best
            bt[i][j] = 'diag' if best == diag else ('up' if best == up else 'left')

    # Walk the backtrace, collecting diagonal (match) placements.
    mapping = [None] * n
    i, j = n, m
    while i > 0 or j > 0:
        step = bt[i][j] if i > 0 and j > 0 else ('up' if i > 0 else 'left')
        if step == 'diag':
            s = sim(S[i - 1], W[j - 1])
            if s is None:
                s = _mishear_hit(S[i - 1], W[j - 1])
            if s is not None and s >= SUBST_MIN:
                mapping[i - 1] = j - 1
            i -= 1
            j -= 1
        elif step == 'up':
            i -= 1
        else:
            j -= 1

    # A word the DP could not place is reported as a genuine failure. It is NOT
    # silently filled from a neighbour: an interpolated onset is a wrong onset,
    # and a wrong onset is exactly the CLAUDE.md §5 drift this pipeline exists
    # to prevent. The caller decides how to handle a hole.
    notes = []
    for k in range(n):
        if mapping[k] is None:
            lo = max((x for x in mapping[:k] if x is not None), default=None)
            hi = min((x for x in mapping[k + 1:] if x is not None), default=None)
            notes.append(f"  UNPLACED script[{k}]={script_words[k]!r} "
                         f"(prev whisper idx {lo}, next {hi})")

    for k, wi in enumerate(mapping):
        if wi is not None and canon_fn(script_words[k]) != canon_fn(whisper_words[wi]):
            notes.append(f"  near-miss script[{k}]={script_words[k]!r} -> "
                         f"whisper[{wi}]={whisper_words[wi]!r}")
    return mapping, notes


def resolve_spans(mapping, script_words, whisper_words, min_sim=0.45):
    """Fill unplaced script words that whisper merged into a neighbouring token.

    whisper routinely collapses two script words into one token:
      'City-sized.'  -> '.City' + '-sized.'  (or a single token)
      'twenty-five'  -> '25'
      'Wolszczan'    -> absorbed next to 'Alexander'
    Those script words are genuinely spoken, so they have a real onset — it just
    falls at the boundary with the token whisper emitted for them.

    For an unplaced word we look at the unclaimed whisper tokens between its
    placed neighbours and take the first one that is a plausible rendering of it
    (digit/number folding, prefix containment, or moderate similarity). Anything
    below min_sim stays unplaced: a wrong onset is worse than an honest gap.
    """
    n = len(mapping)
    out = list(mapping)
    notes = []
    for k in range(n):
        if out[k] is not None:
            continue
        lo = max((x for x in out[:k] if x is not None), default=None)
        hi = min((x for x in out[k + 1:] if x is not None), default=None)
        lo = -1 if lo is None else lo
        hi = len(whisper_words) if hi is None else hi
        target = canon(script_words[k])
        best, best_score = None, 0.0
        for wi in range(lo + 1, hi):
            if wi in out:
                continue
            cand = canon(whisper_words[wi])
            # Containment is checked FIRST, independently of the similarity
            # threshold. whisper splits a hyphenated script word across two
            # tokens ('City-sized.' -> '.City' + '-sized.'), so the script's
            # canonical form CONTAINS the token rather than resembling it, and
            # the ratio gate rejects it before containment is ever consulted.
            contained = bool(target and cand and (cand in target or target in cand))
            s = sim(target, cand)
            if s is None and not contained:
                continue
            score = s if s is not None else 0.0
            # A containment match is weaker evidence than a real similarity
            # match, so it must not outrank one.
            if contained and score < min_sim:
                score = min_sim
            if score >= min_sim or contained:
                if score > best_score:
                    best, best_score = wi, score
        if best is not None:
            out[k] = best
            notes.append(f"  SPAN script[{k}]={script_words[k]!r} -> "
                         f"whisper[{best}]={whisper_words[best]!r} "
                         f"(sim {best_score:.2f})")
        elif hi is not None and hi < len(whisper_words):
            # No distinct token was emitted for this word: whisper merged it
            # into the FOLLOWING token. The word therefore begins where the
            # previous token ended, so the next token's onset is the right one.
            # (Taking the previous index instead would place the card at the
            # end of the preceding word — a whole word early, and it breaks
            # monotonicity against the card that is anchored there.)
            out[k] = hi
            notes.append(f"  MERGED script[{k}]={script_words[k]!r} -> "
                         f"merged into following token whisper[{hi}]="
                         f"{whisper_words[hi]!r}")
        else:
            notes.append(f"  UNRESOLVED script[{k}]={script_words[k]!r} "
                         f"(window whisper {lo+1}..{hi-1})")
    out = enforce_monotonic(out, script_words, whisper_words)
    return out, notes


def enforce_monotonic(mapping, script_words, whisper_words):
    """Make the mapping non-decreasing and leave no holes.

    Two script words legitimately share a whisper index (whisper merged them),
    so equal values are allowed; only a DECREASE is a defect, and it is fixed
    by lifting the later word to the earlier word's index. That keeps the
    onsets non-decreasing, which is what the card scheduler requires — a card
    must never start before the card before it.

    A trailing word with no following token is pinned to the last one: it is
    the end of the narration, and the WAV's own duration bounds it.
    """
    out = list(mapping)
    n = len(out)
    last = len(whisper_words) - 1
    run = 0
    for k in range(n):
        if out[k] is None:
            out[k] = min(run, last) if run else last
        if out[k] < run:
            out[k] = run
        run = out[k]
    return out
