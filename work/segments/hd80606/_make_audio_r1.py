"""Generate round_1_audio.wav for HD 80606 b using chatterbox."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from lib.tts import synthesize
from scripts import HD_80606_SCRIPT


def main():
    out = os.path.join(os.path.dirname(__file__), 'round_1_audio.wav')
    text = HD_80606_SCRIPT.strip()
    print(f"Synthesizing {len(text.split())} words...")
    synthesize(text, out)
    print(f"Wrote {out}")


if __name__ == '__main__':
    main()
