"""Generate round_1_audio.wav for PSR B1257+12 using chatterbox.

Mirrors the segment 1 pattern (work/segments/hd188753/_make_audio_r2.py): chatterbox
on CPU has a ~40s cap that truncates a long script mid-sentence, so we use the
chunked generator and stitch with explicit silences.

The narration is canonical in work/scripts.py (PSRB1257_SCRIPT, 317 words,
fact-corrected E1-E6). Do not edit the narration here.

CLAUDE.md §2 targets 190-213 wpm. If the measured rate falls out of band, re-run
with overrides — lib/tts.py itself is never edited:

    python _make_audio_r1.py --exaggeration 0.45 --cfg-weight 0.5 --temperature 0.8

Lower exaggeration => flatter/slower. Higher => more emphatic, usually faster.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from lib.tts import synthesize_chunked
from scripts import PSRB1257_SCRIPT

HERE = os.path.dirname(os.path.abspath(__file__))
WPM_LOW, WPM_HIGH = 190, 213


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'round_1_audio.wav'))
    ap.add_argument('--max-chunk-words', type=int, default=110)
    ap.add_argument('--silence-between-s', type=float, default=0.4)
    ap.add_argument('--exaggeration', type=float, default=0.5)
    ap.add_argument('--cfg-weight', type=float, default=0.5)
    ap.add_argument('--temperature', type=float, default=0.8)
    args = ap.parse_args()

    out = args.out
    text = PSRB1257_SCRIPT.strip()
    words = len(text.split())
    print(f"Synthesizing {words} words (chunked) with exaggeration={args.exaggeration} "
          f"cfg_weight={args.cfg_weight} temperature={args.temperature}...")
    synthesize_chunked(text, out,
                       max_chunk_words=args.max_chunk_words,
                       silence_between_s=args.silence_between_s,
                       exaggeration=args.exaggeration,
                       cfg_weight=args.cfg_weight,
                       temperature=args.temperature)
    print(f"Wrote {out}")

    import wave
    with wave.open(out, 'rb') as wf:
        dur = wf.getnframes() / wf.getframerate()
        sr = wf.getframerate()
    wpm = (words / dur) * 60.0
    print(f"duration {dur:.2f}s  sample_rate {sr}  measured {wpm:.1f} wpm")
    if not (WPM_LOW <= wpm <= WPM_HIGH):
        print(f"WARNING: {wpm:.1f} wpm is outside the {WPM_LOW}-{WPM_HIGH} band "
              f"(CLAUDE.md §2). Tune exaggeration/cfg_weight/temperature and re-run "
              f"before rendering frames.")


if __name__ == '__main__':
    main()
