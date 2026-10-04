# work/lib/tts.py — chatterbox TTS wrapper for the Guantlet2 pipeline.
#
# Per CLAUDE.md §3: chatterbox is our TTS. It supports per-sentence pacing
# parameters and pause tokens. Target 190-213 wpm (reference pacing).
#
# Note: chatterbox's generate() returns a torch tensor at 24kHz. We post-process
# to 16kHz mono for the alignment pass, then keep both (24kHz for the final mux).
#
# We use simple whole-script generation per segment. Per-clause pacing control
# can be added later via repetition_penalty/exaggeration tuning, or by generating
# per-clause and concatenating with explicit silences.

import os
import numpy as np
import torch
import wave

SAMPLE_RATE = 24000  # chatterbox outputs at 24 kHz
TARGET_WPM_LOW = 190
TARGET_WPM_HIGH = 213


def _ensure_model():
    """Load chatterbox model (cached after first call)."""
    global _model
    if _model is None:
        from chatterbox.tts import ChatterboxTTS
        _model = ChatterboxTTS.from_pretrained(device='cpu')  # use CPU for portability
    return _model


_model = None


def synthesize(text, out_wav_path, sample_rate=SAMPLE_RATE, exaggeration=0.5,
               cfg_weight=0.5, temperature=0.8):
    """Generate a single WAV file from the given text.

    text: the narration string
    out_wav_path: where to write the WAV
    """
    model = _ensure_model()
    wav = model.generate(
        text,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        temperature=temperature,
    )
    # wav is a torch tensor, shape [1, samples] or [samples]
    if isinstance(wav, torch.Tensor):
        wav_np = wav.squeeze().cpu().numpy()
    else:
        wav_np = np.asarray(wav).squeeze()

    # Write as 16-bit PCM
    wav_int16 = np.clip(wav_np * 32767, -32768, 32767).astype(np.int16)
    os.makedirs(os.path.dirname(out_wav_path) or '.', exist_ok=True)
    with wave.open(out_wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(wav_int16.tobytes())
    return out_wav_path


def synthesize_chunked(text, out_wav_path, sample_rate=SAMPLE_RATE,
                      max_chunk_words=110, silence_between_s=0.4,
                      exaggeration=0.5, cfg_weight=0.5, temperature=0.8):
    """Generate a long narration by chunking at sentence boundaries.

    chatterbox's `model.generate` truncates around 40s on CPU. For longer
    scripts we split at sentence boundaries (paragraphs preferred), generate
    each chunk separately, and stitch with a short silence between chunks.

    text: the narration string
    out_wav_path: where to write the final WAV
    max_chunk_words: target max words per chunk (chatterbox reliably handles
                     ~110 words / ~33s on CPU).
    silence_between_s: seconds of silence to insert between chunks.
    """
    import re

    # First, split on paragraph boundaries (double newlines), then on sentence
    # boundaries, so we keep natural pauses. The HD_188753 script has 9 paragraphs.
    paragraphs = [p.strip() for p in text.strip().split('\n\n') if p.strip()]
    units = []  # list of (text, source_paragraph_idx)
    for pi, para in enumerate(paragraphs):
        # Try paragraph first if it's under the cap
        if len(para.split()) <= max_chunk_words:
            units.append((para, pi))
        else:
            # Split paragraph into sentences
            sents = re.split(r'(?<=[.!?])\s+', para)
            cur = []
            cur_words = 0
            for s in sents:
                sw = len(s.split())
                if cur_words + sw > max_chunk_words and cur:
                    units.append((' '.join(cur), pi))
                    cur = [s]
                    cur_words = sw
                else:
                    cur.append(s)
                    cur_words += sw
            if cur:
                units.append((' '.join(cur), pi))

    print(f'  chunked into {len(units)} units:')
    for i, (u, pi) in enumerate(units):
        wc = len(u.split())
        print(f'    [{i+1}/{len(units)}] para {pi+1} {wc}w: {u[:60]}...')

    # Generate each chunk
    model = _ensure_model()
    pcm_parts = []
    for i, (chunk, pi) in enumerate(units):
        print(f'  generating chunk {i+1}/{len(units)} ({len(chunk.split())} words)...')
        wav = model.generate(
            chunk,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
        )
        if isinstance(wav, torch.Tensor):
            wav_np = wav.squeeze().cpu().numpy()
        else:
            wav_np = np.asarray(wav).squeeze()
        pcm = np.clip(wav_np * 32767, -32768, 32767).astype(np.int16)
        pcm_parts.append(pcm)
        # Inter-chunk silence (except after last)
        if i < len(units) - 1:
            silence_samples = int(silence_between_s * sample_rate)
            pcm_parts.append(np.zeros(silence_samples, dtype=np.int16))

    # Stitch
    full = np.concatenate(pcm_parts)
    total_s = len(full) / sample_rate
    print(f'  total: {len(full)} samples = {total_s:.2f}s')

    os.makedirs(os.path.dirname(out_wav_path) or '.', exist_ok=True)
    with wave.open(out_wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(full.tobytes())
    return out_wav_path


def estimate_wpm(text, duration_s):
    """Estimate WPM given a text and an audio duration in seconds."""
    n_words = max(1, len(text.split()))
    return (n_words / duration_s) * 60.0


def wpm_in_range(text, duration_s, low=TARGET_WPM_LOW, high=TARGET_WPM_HIGH):
    return low <= estimate_wpm(text, duration_s) <= high
