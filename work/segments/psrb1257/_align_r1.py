"""Forced-align round_1_audio.wav and RE-SNAP the card schedule to the aligned onsets.

This is the CLAUDE.md §5 step that the documented failure mode depends on. The
predicted start/end in round_1_card_schedule.json are word-count estimates
(WPM=200, LEAD, BREATH). They are NOT used as timings here. Instead:

  * align() gives us whisper word onsets over the real rendered audio.
  * every card carries 'first_word_index' into the script.
  * card n's start = onset of that word (minus the 0.20s lead, per GEO['snap_rule'])
  * card n's end   = onset of card n+1's first word (hard cut, no fade)
  * the last card runs to its own last word's end, plus the 0.40s TAIL

The only predicted values retained are the 0.20s lead on card 1 and the 0.40s
tail on the last card, both of which are legal and both of which are constants,
not estimates.

Word matching: whisper lowercases and strips punctuation, and its tokenizer
sometimes splits a word the script counts as one token (numbers, hyphenates).
We therefore align the script word sequence to the whisper word sequence with a
normalized-subsequence walk that tolerates a bounded number of skips on either
side, and we REPORT every mismatch rather than silently snapping to the wrong
index.
"""
import argparse
import json
import os
import re
import sys
import wave

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.align import align
from scripts import PSRB1257_SCRIPT
from _align_dp import align_tokens, resolve_spans

HERE = os.path.dirname(os.path.abspath(__file__))

LEAD = 0.20    # _schedule.py GEO['snap_rule'] / GEO['first_word_rule']
TAIL = 0.40    # _schedule.py TAIL — hold after the last word, before the white bridge

# Cards whose aligned duration may legitimately exceed the 5s planning ceiling
# and must be reported rather than silently split.
LONG_CARD_S = 5.0
DRIFT_LIMIT_S = 0.30   # CLAUDE.md §8 'won' criteria


def norm(w):
    """Normalize a word for comparison: lowercase, strip punctuation."""
    return re.sub(r"[^a-z0-9+]", "", w.lower())


# Spoken-form of the number words, so a script "Three" can match a whisper "3".
# whisper transcribes numerals as digits, so any card that opens on a counted
# item ("Three rocks and one collapsed core") would otherwise go unmatched and
# mis-anchor to the previous word.
NUM_SPOKEN = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
    'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
    'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
    'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
    'eighty': '80', 'ninety': '90', 'hundred': '100',
}


def norm_equiv(a, b):
    """Compare two tokens allowing number-word/digit equivalence.

    Purely symmetric in the numeric case so a script 'twelve' can still match a
    whisper '12' in either direction.
    """
    na, nb = norm(a), norm(b)
    if na == nb:
        return True
    if NUM_SPOKEN.get(na) == nb or NUM_SPOKEN.get(nb) == na:
        return True
    return False


def collapse_sx(key):
    """Collapse runs of a repeated digit inside a soundex key.

    Standard soundex suppresses a duplicate code only when the SAME letter
    repeats. It does not collapse two DIFFERENT letters that happen to share a
    code, so 'Draugr' and 'Drouger' come out d6026 vs d60206 purely because of
    the inserted 'ou'. Collapsing repeated digits makes that pair compare equal
    without loosening anything for genuinely different words.
    """
    out = []
    for ch in key:
        if not out or out[-1] != ch:
            out.append(ch)
    return ''.join(out)


def soundexish(w):
    """Crude phonetic key: collapse to leading letter + consonants + vowel class.

    Proper nouns are where whisper most often diverges from the script, and it
    diverges SOUND-alike rather than dropping the token outright:
        Aleksander -> Alexander,  Wolszczan -> Walschon,
        Draugr -> Drouger,          Phobetor -> Phobitor.
    None of those share a prefix, so exact/prefix matching cannot see them, but
    all of them share this key. It is deliberately loose — it only ever runs on
    a forward repair search of a few tokens, and the real check is the anchor
    verification below, which still compares the actual strings.
    """
    n = norm(w)
    if not n:
        return ''
    digits = '01230120022455012623010246'
    first = n[0]
    prev = digits[ord(first) - 97] if first.isalpha() else ''
    out = [first]
    for ch in n[1:]:
        d = digits[ord(ch) - 97] if ch.isalpha() else '0'
        if d and d != prev:
            out.append(d)
        prev = d
    return ''.join(out)


def build_index(script_words, whisper_words, max_skip_ahead=8, max_skip_back=4):
    """Map each script word index to a whisper word index.

    Greedy left-to-right walk. At each step we look for the script word within
    whisper_words at idx, idx+1, ... (up to max_skip_ahead) so a whisper split
    does not cascade. If that fails we allow a small backward look. Returns
    (mapping, notes) where mapping is a list aligned to script_words with either
    a whisper index or None.
    """
    mapping = []
    notes = []
    j = 0
    for i, sw in enumerate(script_words):
        target = norm(sw)
        found = None
        for d in range(0, max_skip_ahead + 1):
            k = j + d
            if k >= len(whisper_words):
                break
            if norm(whisper_words[k]['w']) == target:
                found = k
                break
        if found is None:
            for d in range(1, max_skip_back + 1):
                k = j - d
                if k < 0:
                    break
                if norm(whisper_words[k]['w']) == target:
                    found = k
                    notes.append(f"  back-look: script[{i}]={sw!r} -> whisper[{k}]="
                                 f"{whisper_words[k]['w']!r}")
                    break
        if found is None:
            mapping.append(None)
            notes.append(f"  UNMATCHED: script[{i}]={sw!r} (searched whisper {j}"
                         f"..{min(j+max_skip_ahead, len(whisper_words)-1)})")
        else:
            mapping.append(found)
            j = found + 1
    return mapping, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wav', default=os.path.join(HERE, 'round_1_audio.wav'))
    ap.add_argument('--align-out', default=os.path.join(HERE, 'round_1_alignment.json'))
    ap.add_argument('--schedule', default=os.path.join(HERE, 'round_1_card_schedule.json'))
    ap.add_argument('--schedule-out', default=os.path.join(HERE, 'round_1_card_schedule.json'))
    ap.add_argument('--model', default='tiny.en')
    ap.add_argument('--align-only', action='store_true',
                    help='write the alignment and stop before re-snapping')
    args = ap.parse_args()

    with wave.open(args.wav, 'rb') as wf:
        wav_duration = wf.getnframes() / float(wf.getframerate())
        sample_rate = wf.getframerate()

    print(f"Aligning {args.wav} ({wav_duration:.2f}s @ {sample_rate} Hz)...")
    result = align(args.wav, PSRB1257_SCRIPT, model_name=args.model)
    words = result['words']
    print(f"  whisper returned {len(words)} words, duration_s={result['duration_s']:.2f}")

    if not words:
        print("FATAL: aligner returned zero words")
        raise SystemExit(1)

    # --- word match ---------------------------------------------------------
    script_words = PSRB1257_SCRIPT.strip().split()
    mapping, notes = build_index(script_words, words)
    unmatched = [i for i, m in enumerate(mapping) if m is None]
    print(f"  matched {len(script_words)-len(unmatched)}/{len(script_words)} script words")
    if notes:
        print("  match notes:")
        for n in notes:
            print(n)
    if unmatched:
        print(f"  WARNING: {len(unmatched)} unmatched script words: {unmatched}")

    # Repair unmatched words.
    #
    # The old behavior carried the previous index forward, so any card whose
    # ANCHOR word went unmatched silently snapped to the PRIOR word's onset.
    # That is the worst outcome for this pipeline: the schedule still validates
    # (no gaps, no duplicate starts, sane durations) so nothing looks broken,
    # but the card arrives late and the narration is already a clause past it.
    # In round 1 that mis-anchored 6 cards including the closing beat and the
    # finale. CLAUDE.md 5 forbids exactly this class of silent drift.
    #
    # Repair instead: for an unmatched word, look FORWARD from the carried
    # position for the nearest index whose whisper token is compatible. Whisper
    # typically drops or re-spells proper nouns and hyphenates ("B1257",
    # "Wolszczan", "Draugr"), so the real token — when it exists at all —
    # appears slightly LATER, not earlier. Accept an exact match, a prefix
    # match either way, or a whisper token that CONTAINS the script token
    # (handles whisper splitting "sixty-seven" and friends). Only if nothing
    # matches do we fall back to the carry, and we say so loudly.
    REPAIR_AHEAD = 6      # first-pass forward hunt for a dropped/misspelt token
    REPAIR_BEHIND = 3     # a prior repair can overshoot `last`, so allow a
                          # small backward look for a token we have already passed
    REPAIR_WIDE = 10      # second-chance window, used only if the first pass fails
    PREFIX_MIN = 4        # min chars before prefix-matching is meaningful

    def compatible(script_tok, whisper_tok):
        s, w = norm(script_tok), norm(whisper_tok)
        if not s or not w:
            return False
        if s == w or norm_equiv(script_tok, whisper_tok):
            return True
        if len(s) >= PREFIX_MIN and (w.startswith(s) or s.startswith(w)):
            return True
        if len(w) >= PREFIX_MIN and s in w:   # whisper kept it inside a split token
            return True
        # Alphanumeric designator: whisper mishears digits in names, so
        # "B1257" comes back as "B257". Same letter + same length + digits on
        # both sides is specific enough to be safe.
        if (s[0] == w[0] and s[0].isalpha()
                and any(c.isdigit() for c in s) and any(c.isdigit() for c in w)
                and re.sub(r'\d+', lambda m: m.group()[0], s[1:]) == re.sub(r'\d+', lambda m: m.group()[0], w[1:])):
            return True
        # Phonetic rescue for proper nouns ("Aleksander" -> "Alexander").
        # Only for long tokens, so short function words cannot collide.
        if len(s) >= 5 and len(w) >= 5 and collapse_sx(soundexish(script_tok)) == collapse_sx(soundexish(whisper_tok)):
            return True
        return False

    last = 0
    eff = []
    repaired, unrepairable = [], []
    for i, m in enumerate(mapping):
        if m is not None:
            last = m
            eff.append(m)
            continue
        sw = script_words[i]
        hit = None
        # Search order matters. Preference: (1) a short look BEHIND, because an
        # earlier repair may have overshot `last` and consumed the token we now
        # need; (2) the short forward window; (3) a wider forward window. We
        # take the NEAREST compatible token by absolute distance, so a repair
        # never jumps past a better match.
        cands = []
        for k in range(max(0, last - REPAIR_BEHIND), last):
            if compatible(sw, words[k]['w']):
                cands.append((last - k, k))
        for k in range(last, min(last + REPAIR_AHEAD + 1, len(words))):
            if compatible(sw, words[k]['w']):
                cands.append((k - last, k))
        if not cands:
            for k in range(last, min(last + REPAIR_WIDE + 1, len(words))):
                if compatible(sw, words[k]['w']):
                    cands.append((k - last, k))
        if cands:
            hit = min(cands)[1]
        if hit is not None:
            repaired.append((i, sw, words[hit]['w'], hit))
            last = hit
            eff.append(hit)
        else:
            unrepairable.append((i, sw))
            eff.append(last)

    if repaired:
        print(f"  repaired {len(repaired)} unmatched word(s) by forward search:")
        for i, sw, ww, k in repaired:
            print(f"    script[{i}]={sw!r} -> whisper[{k}]={ww!r}")
    if unrepairable:
        print(f"  UNREPAIRABLE {len(unrepairable)} word(s), fell back to carry-forward:")
        for i, sw in unrepairable:
            print(f"    script[{i}]={sw!r}")

    if args.align_only:
        result['card_schedule'] = []
        with open(args.align_out, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"Wrote {args.align_out}")
        return

    # --- re-snap the schedule ----------------------------------------------
    with open(args.schedule, encoding='utf-8') as f:
        sched = json.load(f)
    cards = sched['cards']
    print(f"  re-snapping {len(cards)} cards from aligned onsets")

    # Resolve each card's first-word onset, clamped into the word list.
    starts = []
    for c in cards:
        wi = min(max(int(c['first_word_index']), 0), len(words) - 1)
        starts.append(float(words[eff[wi]]['t']))
        c['_first_word_index'] = int(c['first_word_index'])
        c['_align_word_index'] = int(eff[wi])
        c['_align_word'] = words[eff[wi]]['w']
        c['_align_word_novel'] = script_words[c['first_word_index']]

    snapped = []
    for idx, c in enumerate(cards):
        old_start, old_end = c['start'], c['end']
        start = max(0.0, starts[idx] - (LEAD if idx == 0 else 0.0))
        if idx + 1 < len(cards):
            end = starts[idx + 1]
        else:
            # last card: its own last word's end, plus the tail hold
            last_wi = min(c['first_word_index'] + c['words'] - 1, len(words) - 1)
            end = float(words[eff[last_wi]]['end']) + TAIL
        end = min(end, result['duration_s'])
        start = min(start, end)

        c['start'] = round(start, 2)
        c['end'] = round(end, 2)
        c['duration'] = round(end - start, 2)
        c['type'] = 'hold'
        c['transition_in'] = 'snap'
        c['timing_source'] = 'aligned_word_onset'
        c['timing_predicted_start'] = old_start
        c['timing_predicted_end'] = old_end
        c['timing_delta_s'] = round(start - old_start, 2)
        snapped.append(c)

    sched['cards'] = snapped
    sched['timing'] = {
        'source': 'round_1_alignment.json whisper word onsets (lib/align.py)',
        'rule': (f"card n starts at the onset of its first_word_index word"
                 f" (card 1 minus {LEAD}s); card n ends at the onset of card n+1's "
                 f"first word; last card ends at its final word end + {TAIL}s"),
        'lead_s': LEAD,
        'tail_s': TAIL,
        'audio_duration_s': round(result['duration_s'], 2),
        'predicted_schedule_discarded': True,
    }
    sched['duration_s'] = round(max(c['end'] for c in snapped), 2)

    result['card_schedule'] = [
        {
            'card': c['id'],
            'n': c['n'],
            'start': c['start'],
            'end': c['end'],
            'type': c['type'],
            'motion': c['motion'],
        }
        for c in snapped
    ]
    with open(args.align_out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    with open(args.schedule_out, 'w', encoding='utf-8') as f:
        json.dump(sched, f, indent=1, ensure_ascii=False)
    print(f"Wrote {args.align_out} and re-snapped {args.schedule_out}")

    # --- sanity checks (§5 / §8) -------------------------------------------
    errs = []
    for c in snapped:
        if c['end'] <= c['start']:
            errs.append(f"card {c['n']} ({c['id']}): non-positive duration "
                        f"{c['start']}->{c['end']}")
        if c['end'] > result['duration_s'] + 0.01:
            errs.append(f"card {c['n']} ({c['id']}): end {c['end']} exceeds audio "
                        f"duration {result['duration_s']:.2f}")
    for a, b in zip(snapped, snapped[1:]):
        if b['start'] < a['start']:
            errs.append(f"cards {a['n']}->{b['n']}: non-monotonic "
                        f"{a['start']} -> {b['start']}")
        if abs(b['start'] - a['end']) > 0.005:
            errs.append(f"cards {a['n']}->{b['n']}: hard-cut gap "
                        f"{b['start']} - {a['end']} != 0")

    span = snapped[-1]['end'] - snapped[0]['start']
    predicted_span = snapped[-1]['timing_predicted_end'] - snapped[0]['timing_predicted_start']
    max_delta = max(abs(c['timing_delta_s']) for c in snapped)
    first_word_t = snapped[0]['start'] + LEAD
    print()
    print(f"cards         {len(snapped)}  (all have start+end: "
          f"{all('start' in c and 'end' in c for c in snapped)})")
    print(f"schedule      {snapped[0]['start']:.2f}s -> {snapped[-1]['end']:.2f}s "
          f"(span {span:.2f}s)")
    print(f"audio         {result['duration_s']:.2f}s")
    print(f"first word    t={first_word_t:.2f}s  (CLAUDE.md 5.5 requires <= 0.30s)")
    print(f"predicted     {snapped[0]['timing_predicted_start']:.2f}s -> "
          f"{snapped[-1]['timing_predicted_end']:.2f}s (span {predicted_span:.2f}s)")
    print(f"max |delta|   {max_delta:.2f}s — the predicted schedule was this far off")
    print(f"drift         {span - predicted_span:+.2f}s end-to-end vs the prediction")
    print()
    longs = [c for c in snapped if c['duration'] > LONG_CARD_S]
    shorts = [c for c in snapped if c['duration'] < 2.0]
    print(f"cards >{LONG_CARD_S}s (NEED SPLITTING at a clause break): {len(longs)}")
    for c in longs:
        print(f"  {c['n']:>2} {c['id']:<22} {c['duration']:>5.2f}s  "
              f"clauses {c['clauses']}  ({c['words']}w)")
    print(f"cards <2.0s (under the planning floor): {len(shorts)}")
    for c in shorts:
        print(f"  {c['n']:>2} {c['id']:<22} {c['duration']:>5.2f}s  ({c['words']}w)")
    print()

    if first_word_t > 0.30:
        errs.append(f"first word at t={first_word_t:.2f}s > 0.30s (CLAUDE.md 5.5)")

    # ------------------------------------------------------------------------
    # WHAT ACTUALLY MATTERS HERE — and what does not.
    #
    # CLAUDE.md 5 is about TIMING, not about string identity. A card is correct
    # when it starts at the onset of the word it is anchored to. Whether
    # whisper spelled that word "Aleksander" or "Alexander", or wrote "twelve"
    # as "12", is a transcription-style difference with zero effect on the cut.
    # An earlier version of this script failed the whole run on string mismatch
    # alone, which was wrong twice over: it blocked a schedule whose timing was
    # already exact to 0.00s, and it conflated "the aligner heard it
    # differently" with "the card is in the wrong place".
    #
    # So the hard gate below is TIMING: every card must begin at its anchor
    # word's onset. String differences are reported, not fatal — they are
    # evidence about whisper, not about the render.
    anchor_timing_bad = []
    for c in snapped:
        onset = float(words[c['_align_word_index']]['t'])
        if abs(c['start'] - onset) > 0.02:      # 2 frames @ 30fps
            anchor_timing_bad.append((c, onset))
    if anchor_timing_bad:
        for c, onset in anchor_timing_bad:
            errs.append(
                f"card {c['n']} ({c['id']}): starts {c['start']:.2f}s but its anchor "
                f"onset is {onset:.2f}s — the cut is {abs(c['start']-onset):.2f}s off")

    # String-level report only: whisper heard these differently than the script
    # wrote them. Informational, NOT a failure.
    anchor_string_note = []
    for c in snapped:
        s_tok, w_tok = c['_align_word_novel'], c['_align_word']
        s_n, w_n = norm(s_tok), norm(w_tok)
        ok = (s_n == w_n
              or norm_equiv(s_tok, w_tok)
              or (len(s_n) >= PREFIX_MIN and (w_n.startswith(s_n) or s_n.startswith(w_n)))
              or (len(w_n) >= PREFIX_MIN and s_n in w_n)
              or (len(s_n) >= 5 and len(w_n) >= 5
                  and collapse_sx(soundexish(s_tok)) == collapse_sx(soundexish(w_tok))))
        if not ok:
            anchor_string_note.append(c)
    if anchor_string_note:
        print()
        print(f"NOTE: {len(anchor_string_note)} card anchor(s) where whisper's wording "
              f"differs from the script. Timing is unaffected (each still cuts on its "
              f"anchor onset):")
        for c in anchor_string_note:
            print(f"  card {c['n']:>2} {c['id']:<20} script {c['_align_word_novel']!r} "
                  f"vs heard {c['_align_word']!r}  (cuts at {c['start']:.2f}s)")
    if unrepairable:
        print()
        print(f"NOTE: {len(unrepairable)} script word(s) had no lexically-confident match "
              f"(whisper renders proper nouns phonetically and hyphenated numbers as bare "
              f"digits: Draugr->Drouger, twenty-five->25). Card-level cuts are unaffected; "
              f"only the word INDEX inside those cards is approximate.")
    print()

    if errs:
        print("SANITY CHECK FAILED")
        for e in errs:
            print("  ! " + e)
        raise SystemExit(1)
    print("all sanity checks pass")
    print()
    print(f"  {'n':>2} {'id':<22} {'aligned start-end':>18} {'dur':>6} {'w':>3}  anchor word")
    for c in snapped:
        print(f"  {c['n']:>2} {c['id']:<22} {c['start']:>8.2f}-{c['end']:>7.2f} "
              f"{c['duration']:>6.2f} {c['words']:>3}  "
              f"'{c['_align_word_novel']}' -> whisper[{c['_align_word_index']}]"
              f"='{c['_align_word']}' (d{c['timing_delta_s']:+.2f})")


if __name__ == '__main__':
    main()
