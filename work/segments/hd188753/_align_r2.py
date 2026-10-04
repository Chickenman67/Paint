"""Re-align round_2_audio.wav to per-word timestamps using whisper.

Round 2 audio was regenerated via chunked TTS. Re-align so that the
card schedule snaps to the actual audio, not the round 1 timings.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from lib.align import align, save_alignment
from scripts import HD_188753_SCRIPT


def main():
    wav_path = os.path.join(os.path.dirname(__file__), 'round_2_audio.wav')
    out_path = os.path.join(os.path.dirname(__file__), 'round_2_alignment.json')

    print(f"Aligning {wav_path}...")
    result = align(wav_path, HD_188753_SCRIPT, model_name='tiny.en')
    save_alignment(result, out_path)
    print(f"Wrote {out_path}: {len(result['words'])} words, "
          f"duration={result['duration_s']:.2f}s")


if __name__ == '__main__':
    main()
