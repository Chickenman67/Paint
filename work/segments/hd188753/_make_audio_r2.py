"""Generate round_2_audio.wav for HD 188753 Ab using chatterbox.

Round 2 regen: round_1 audio was lost. The first regen hit chatterbox's
~40s CPU cap and got truncated mid-sentence. This version uses the
chunked generator that splits at paragraph boundaries and stitches.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from lib.tts import synthesize_chunked
from scripts import HD_188753_SCRIPT


def main():
    out = os.path.join(os.path.dirname(__file__), 'round_2_audio.wav')
    text = HD_188753_SCRIPT.strip()
    print(f"Synthesizing {len(text.split())} words (chunked)...")
    synthesize_chunked(text, out, max_chunk_words=110, silence_between_s=0.4)
    print(f"Wrote {out}")


if __name__ == '__main__':
    main()
