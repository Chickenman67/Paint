# work/lib/align.py — Forced alignment using whisper word-level timestamps.
#
# Per CLAUDE.md §5, the new pipeline must drive visuals from per-word onset
# times of the generated WAV, not from predicted word counts. This module
# returns per-word timings that the card scheduler can snap to.
#
# We use openai-whisper (already installed). It returns per-word timings via
# the word_timestamps=True option in transcribe().

import json
import os
import wave

import numpy as np


def load_wav(path):
    """Read a WAV file as a float32 numpy array (mono, normalized to [-1, 1])."""
    with wave.open(path, 'rb') as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    if wf.getsampwidth() == 2:
        a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif wf.getsampwidth() == 4:
        a = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {wf.getsampwidth()}")
    return a, sr


def align(wav_path, reference_text, model_name='tiny.en'):
    """Run whisper on the WAV, returning per-word onset/end times.

    reference_text: the original narration (used to guide whisper; whisper can
    also auto-detect, but for TTS the words are already known).
    Returns: dict with keys 'duration_s', 'words' (list of {t, end, w}).
    """
    import whisper

    audio, sr = load_wav(wav_path)
    # whisper expects 16 kHz
    if sr != 16000:
        # simple resample (scipy would be better but we keep deps minimal)
        import scipy.signal
        audio = scipy.signal.resample(audio, int(len(audio) * 16000 / sr))
        sr = 16000

    model = whisper.load_model(model_name)
    result = model.transcribe(
        audio,
        language='en',
        word_timestamps=True,
        initial_prompt=reference_text,
        condition_on_previous_text=False,
    )

    words = []
    for seg in result.get('segments', []):
        for w in seg.get('words', []) or []:
            t = w.get('start')
            e = w.get('end')
            tok = w.get('word', '').strip()
            if t is None or e is None or not tok:
                continue
            words.append({'t': float(t), 'end': float(e), 'w': tok})

    duration_s = len(audio) / sr
    return {
        'wav_path': wav_path,
        'duration_s': float(duration_s),
        'words': words,
    }


def save_alignment(alignment, out_json_path):
    os.makedirs(os.path.dirname(out_json_path) or '.', exist_ok=True)
    with open(out_json_path, 'w') as f:
        json.dump(alignment, f, indent=2)
    return out_json_path


def load_alignment(json_path):
    with open(json_path) as f:
        return json.load(f)
