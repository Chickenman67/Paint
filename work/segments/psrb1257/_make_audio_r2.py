"""Resumable narration generation for PSR B1257+12 (round 1).

Why this exists, in place of a straight lib/tts.py call:
lib.tts.synthesize_chunked accumulates every chunk in memory and writes the WAV
only after the final chunk. On CPU a 110-word chunk takes minutes, so a process
killed part-way through (session end, terminal close) loses ALL completed work and
the next attempt starts from zero. That produced zero forward progress across
several attempts.

This version is checkpointed:
  * each chunk is written to _chunks/NNN.wav the moment it finishes
  * a re-run skips any chunk whose file already exists
  * only after all chunks exist does it stitch round_1_audio.wav

So the work is cumulative and interruption-safe. Killing it costs at most the
in-flight chunk.

The narration is canonical in work/scripts.py (PSRB1257_SCRIPT, 317 words,
fact-corrected E1-E6) and is never edited here.

CLAUDE.md §2 targets 190-213 wpm. If the measured rate is out of band, re-run
with overrides (lib/tts.py is never edited):
    python _make_audio_r2.py --exaggeration 0.45
Lower exaggeration => flatter/slower. Higher => more emphatic, usually faster.
"""
import argparse
import os
import re
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_RATE = 24000
WPM_LOW, WPM_HIGH = 190, 213


def split_units(text, max_chunk_words):
    """Split narration into chunks at sentence boundaries.

    Mirrors lib.tts.synthesize_chunked's policy so the two agree on pacing:
    prefer paragraph breaks, fall back to sentence breaks under the word cap.
    """
    paragraphs = [p.strip() for p in text.strip().split('\n\n') if p.strip()]
    units = []
    for para in paragraphs:
        if len(para.split()) <= max_chunk_words:
            units.append(para)
            continue
        sents = re.split(r'(?<=[.!?])\s+', para)
        cur, cur_words = [], 0
        for s in sents:
            sw = len(s.split())
            if cur_words + sw > max_chunk_words and cur:
                units.append(' '.join(cur))
                cur, cur_words = [s], sw
            else:
                cur.append(s)
                cur_words += sw
        if cur:
            units.append(' '.join(cur))
    return units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'round_1_audio.wav'))
    ap.add_argument('--chunk-dir', default=os.path.join(HERE, '_chunks'))
    ap.add_argument('--max-chunk-words', type=int, default=110)
    ap.add_argument('--silence-between-s', type=float, default=0.4)
    ap.add_argument('--exaggeration', type=float, default=0.5)
    ap.add_argument('--cfg-weight', type=float, default=0.5)
    ap.add_argument('--temperature', type=float, default=0.8)
    ap.add_argument('--restitch', action='store_true',
                    help='ignore existing chunks and regenerate all of them')
    args = ap.parse_args()

    from scripts import PSRB1257_SCRIPT
    from lib.tts import _ensure_model
    import torch

    text = PSRB1257_SCRIPT.strip()
    words = len(text.split())
    units = split_units(text, args.max_chunk_words)

    os.makedirs(args.chunk_dir, exist_ok=True)
    if args.restitch:
        for f in os.listdir(args.chunk_dir):
            if f.endswith('.wav'):
                os.remove(os.path.join(args.chunk_dir, f))
        print('restitch: cleared existing chunks', flush=True)

    print(f'{words} words -> {len(units)} chunks of '
          f'{[len(u.split()) for u in units]} words', flush=True)

    model = None
    for i, chunk in enumerate(units, 1):
        cpath = os.path.join(args.chunk_dir, f'{i:03d}.wav')
        if os.path.exists(cpath) and os.path.getsize(cpath) > 1000:
            print(f'  chunk {i}/{len(units)}: cached', flush=True)
            continue
        if model is None:
            print('  loading chatterbox model...', flush=True)
            model = _ensure_model()
        print(f'  chunk {i}/{len(units)} ({len(chunk.split())}w): '
              f'{chunk[:56]}...', flush=True)
        wav = model.generate(chunk,
                             exaggeration=args.exaggeration,
                             cfg_weight=args.cfg_weight,
                             temperature=args.temperature)
        if isinstance(wav, torch.Tensor):
            wav_np = wav.squeeze().cpu().numpy()
        else:
            wav_np = np.asarray(wav).squeeze()
        pcm = np.clip(wav_np * 32767, -32768, 32767).astype(np.int16)
        # Write atomically: a half-written chunk would look "cached" next run.
        tmp = cpath + '.tmp'
        with wave.open(tmp, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm.tobytes())
        os.replace(tmp, cpath)
        print(f'    -> {cpath} ({len(pcm)/SAMPLE_RATE:.1f}s)', flush=True)

    # Stitch only once every chunk is on disk.
    parts = []
    for i in range(1, len(units) + 1):
        cpath = os.path.join(args.chunk_dir, f'{i:03d}.wav')
        with wave.open(cpath, 'rb') as wf:
            assert wf.getframerate() == SAMPLE_RATE, f'chunk {i} has wrong sample rate'
            parts.append(np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16))
        if i < len(units):
            parts.append(np.zeros(int(args.silence_between_s * SAMPLE_RATE), dtype=np.int16))
    full = np.concatenate(parts)

    with wave.open(args.out, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(full.tobytes())

    dur = len(full) / SAMPLE_RATE
    wpm = (words / dur) * 60.0
    print(f'Wrote {args.out}', flush=True)
    print(f'duration {dur:.2f}s  {SAMPLE_RATE}Hz  {wpm:.1f} wpm', flush=True)
    if not (WPM_LOW <= wpm <= WPM_HIGH):
        print(f'WARNING: {wpm:.1f} wpm outside the {WPM_LOW}-{WPM_HIGH} band '
              f'(CLAUDE.md §2). Re-run with --exaggeration/--cfg-weight/--temperature '
              f'overrides before rendering frames.', flush=True)
    else:
        print('wpm in band', flush=True)


if __name__ == '__main__':
    main()
