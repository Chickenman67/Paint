"""Force-align the round_1 audio with whisper to get per-word timings."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from lib.align import align, save_alignment
from scripts import HD_80606_SCRIPT


def main():
    seg_dir = os.path.dirname(__file__)
    wav = os.path.join(seg_dir, 'round_1_audio.wav')
    out = os.path.join(seg_dir, 'round_1_alignment.json')
    text = HD_80606_SCRIPT.strip()
    print(f"Aligning {wav}...")
    a = align(wav, text, model_name='tiny.en')
    save_alignment(a, out)
    print(f"Wrote {out}: {a['duration_s']:.2f}s, {len(a['words'])} words")


if __name__ == '__main__':
    main()
