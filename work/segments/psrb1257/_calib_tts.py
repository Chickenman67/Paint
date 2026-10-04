"""TTS rate calibration for PSR B1257+12.

Chunk 001 of the production run came in at 110 words / 29.4s = 224.5 wpm, which is
above the 190-213 band in CLAUDE.md §2. Rather than burn a full 3-chunk run at the
wrong setting, synthesize one short probe paragraph at several settings and measure.

The probe is the REAL clause sequence from the script (clauses 1-7), not filler,
so the measurement reflects this narrator's actual pacing.

lib/tts.py is never edited; exaggeration/cfg_weight/temperature are passed through.
"""
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from lib.tts import _ensure_model
from scripts import PSRB1257_SCRIPT

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE_DIR = os.path.join(HERE, '_calib')

# Clauses 1-7 of PSRB1257_SCRIPT: 43 words, mixed short declaratives + a long one.
PROBE = """Here is a star that has already died.
It is still spinning, and it is still talking.
And it is not spinning alone.
A neutron star.
City-sized.
Denser than anything should be allowed.
Its fuel ran out, it exploded, and the rest collapsed in here."""

SAMPLE_RATE = 24000

SETTINGS = [
    (0.35, 0.5, 0.8),
    (0.42, 0.5, 0.8),
    (0.50, 0.5, 0.8),
    (0.50, 0.35, 0.7),
    (0.30, 0.35, 0.7),
    (0.25, 0.5, 0.6),
]


def main():
    import torch

    os.makedirs(PROBE_DIR, exist_ok=True)
    n_words = len(PROBE.split())
    print(f'probe: {n_words} words', flush=True)

    model = _ensure_model()
    rows = []
    for ex, cfg, temp in SETTINGS:
        tag = f'ex{ex}_cfg{cfg}_t{temp}'
        out = os.path.join(PROBE_DIR, f'{tag}.wav')
        if not (os.path.exists(out) and os.path.getsize(out) > 1000):
            wav = model.generate(PROBE, exaggeration=ex, cfg_weight=cfg,
                                 temperature=temp)
            if isinstance(wav, torch.Tensor):
                wav_np = wav.squeeze().cpu().numpy()
            else:
                wav_np = np.asarray(wav).squeeze()
            pcm = np.clip(wav_np * 32767, -32768, 32767).astype(np.int16)
            tmp = out + '.tmp'
            with wave.open(tmp, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(pcm.tobytes())
            os.replace(tmp, out)
            print(f'  generated {tag}', flush=True)
        with wave.open(out, 'rb') as wf:
            dur = wf.getnframes() / wf.getframerate()
        rows.append((ex, cfg, temp, dur, n_words / dur * 60.0))
        print(f'  {tag:<26} {dur:>6.2f}s  {rows[-1][4]:>6.1f} wpm', flush=True)

    print()
    print(f"{'exag':>6} {'cfg':>6} {'temp':>6} {'dur_s':>8} {'wpm':>7}  band")
    for ex, cfg, temp, dur, wpm in rows:
        band = 'IN' if 190 <= wpm <= 213 else '--'
        print(f'{ex:>6} {cfg:>6} {temp:>6} {dur:>8.2f} {wpm:>7.1f}  {band}')

    # The probe is a partial script; a full run adds 2 inter-chunk silences, so the
    # full-track wpm runs marginally BELOW the probe wpm. Prefer a probe slightly
    # above the target midpoint so the full track lands mid-band.
    print()
    print('full-track estimate (probe wpm minus ~0.5 wpm for 2x silence):')
    for ex, cfg, temp, dur, wpm in rows:
        print(f'  ex={ex} cfg={cfg} temp={temp} -> {wpm - 0.5:.1f} wpm')


if __name__ == '__main__':
    main()
