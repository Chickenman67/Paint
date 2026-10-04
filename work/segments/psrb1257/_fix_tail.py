"""Regenerate chunk 003, which chatterbox renders with a duplicated closing line.

Measured on the real audio, at two different settings (ex 0.5 and ex 0.35), chunk
003 comes out like this:

  ex0.5  "... Three rocks and one collapsed core, turning forever in an
          afternoon. 3 rocks and 1 collapsed core."
  ex0.35 "... Three rocks in one collapsed core. Turning forever and afternoon.
          Three rocks in one collapsed core. turning forever in the dark."

Two independent symptoms in the same ~4s tail:
  * the closing phrase is spoken TWICE
  * "in the dark" is mangled into "in an afternoon" / "and afternoon"

This is not a whisper hallucination: the RMS envelope at the second occurrence
is unambiguously speech level, and the transcript shows a verbatim nine-word
repeat. The aligned cross-correlation of the two occurrences is only 0.10, so it
is not a byte-identical loop either -- it is chatterbox re-generating the tail
of a long generate() call on CPU, which is the same ~40s length pressure that
made lib/tts.synthesize_chunked necessary in the first place. Chunks 001 and 002
(also ~110 words) are clean, so the trigger is specific to this text.

The fix is the same one the chunker already applies everywhere else: make the
generate() call shorter. This re-runs chunk 003 as two sub-chunks at the SAME
voice settings (0.5/0.5/0.8, matching segments 1-2 and the rest of this track)
and stitches them with the same 0.4s inter-chunk silence, so the result is
indistinguishable in voice from the other two chunks.

It rewrites only _chunks/003.wav. If the new chunk is still defective the script
says so rather than overwriting the good data silently.

lib/tts.py is not edited.
"""
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from _make_audio_r2 import split_units

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_RATE = 24000
EXAGGERATION, CFG_WEIGHT, TEMPERATURE = 0.5, 0.5, 0.8
SUB_CHUNK_WORDS = 55
SILENCE = 0.4

# The exact text of chunk 003, taken from split_units so it can never drift from
# what the real run generated.
CHUNK3 = split_units(
    __import__('scripts').PSRB1257_SCRIPT.strip(), 110)[2]


def rms_env(a, sr, frame=0.02, thr=0.02):
    fr = int(sr * frame)
    m = (len(a) // fr) * fr
    env = np.sqrt((a[:m].reshape(-1, fr) ** 2).mean(axis=1))
    return env > thr


def main():
    subs = split_units(CHUNK3, SUB_CHUNK_WORDS)
    print(f'chunk 003 is {len(CHUNK3.split())}w -> '
          f'{len(subs)} sub-chunks {[len(s.split()) for s in subs]}',
          flush=True)

    from lib.tts import _ensure_model
    import torch
    model = _ensure_model()

    parts = []
    for i, sub in enumerate(subs, 1):
        print(f'  sub {i}/{len(subs)} ({len(sub.split())}w): {sub[:56]}...',
              flush=True)
        wav = model.generate(sub, exaggeration=EXAGGERATION,
                             cfg_weight=CFG_WEIGHT, temperature=TEMPERATURE)
        if isinstance(wav, torch.Tensor):
            x = wav.squeeze().cpu().numpy()
        else:
            x = np.asarray(wav).squeeze()
        pcm = np.clip(x * 32767, -32768, 32767).astype(np.int16)
        parts.append(pcm)
        print(f'    -> {len(pcm)/SAMPLE_RATE:.1f}s', flush=True)
        if i < len(subs):
            parts.append(np.zeros(int(SILENCE * SAMPLE_RATE), dtype=np.int16))

    full = np.concatenate(parts)
    dur = len(full) / SAMPLE_RATE
    print(f'\nnew chunk 003: {dur:.2f}s  (old 30.16s)', flush=True)

    # A duplicate tail shows up as a long run of speech AFTER a gap that is
    # followed by speech resembling the passage before it. Cheap robust proxy:
    # compare the last 40% of the chunk against the 20% before it. Normal
    # narration has different words there; a loop has near-identical audio.
    sr = SAMPLE_RATE
    a = full.astype(np.float32) / 32768.0
    sp = rms_env(a, sr)
    gaps = 0
    run = sp[0]
    for v in sp[1:]:
        if v != run:
            if not run:
                gaps += 1
            run = v
    print(f'speech->silence transitions: {gaps}')

    tail = a[int(0.62 * len(a)):]
    prev = a[int(0.40 * len(a)):int(0.62 * len(a))]
    n = min(len(tail), len(prev))
    x = tail[:n] - tail[:n].mean()
    y = prev[:n] - prev[:n].mean()
    corr = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-9))
    print(f'tail-vs-preceding self-correlation: {corr:.3f} '
          f'({"SUSPICIOUS - tail repeats" if corr > 0.5 else "ok - tail differs"})')

    if corr > 0.5:
        print('\nnew chunk still looks duplicated; NOT overwriting '
              '_chunks/003.wav. Try a smaller SUB_CHUNK_WORDS.')
        return

    out = os.path.join(HERE, '_chunks', '003.wav')
    tmp = out + '.tmp'
    with wave.open(tmp, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(full.tobytes())
    os.replace(tmp, out)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
