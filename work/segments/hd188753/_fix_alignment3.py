"""Better alignment: use whisper's actual 150 (no-punct) words as anchors."""
import sys
import os
import json
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts import HD_188753_SCRIPT

align_path = os.path.join(os.path.dirname(__file__), 'round_1_alignment.json')

# Re-run whisper (use the previous result as starting point, but we lost
# the original. Let me regenerate from scratch with a better prompt)
import whisper
import numpy as np
import wave
import scipy.signal

wav = os.path.join(os.path.dirname(__file__), 'round_1_audio.wav')
with wave.open(wav, 'rb') as wf:
    sr = wf.getframerate()
    n = wf.getnframes()
    raw = wf.readframes(n)
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
audio = scipy.signal.resample(audio, int(len(audio) * 16000 / sr))

print("Loading small.en...")
model = whisper.load_model('small.en')
prompt = HD_188753_SCRIPT.strip()
result = model.transcribe(
    audio,
    language='en',
    word_timestamps=True,
    initial_prompt=prompt,
    condition_on_previous_text=True,
    temperature=0.0,
    no_speech_threshold=0.1,
    logprob_threshold=-1.0,
)

# Collect whisper words (filtering empty/punct-only)
w_words = []
for seg in result.get('segments', []):
    for w in seg.get('words', []) or []:
        t = w.get('start')
        e = w.get('end')
        tok = w.get('word', '').strip()
        if t is None or e is None or not tok:
            continue
        # Skip tokens that are just punctuation
        if re.fullmatch(r'[.,!?\-]+', tok):
            continue
        w_words.append({'t': float(t), 'end': float(e), 'w': tok.lower()})

print(f"Whisper words (no punct): {len(w_words)}")
print('First 10:')
for w in w_words[:10]:
    print(f"  t={w['t']:.2f}-{w['end']:.2f}  {w['w']}")

# Tokenize the script
script_words = re.findall(r"[A-Za-z0-9'\-]+", HD_188753_SCRIPT)
print(f"Script words: {len(script_words)}")

# Strategy: linearly map the 217 script words to the 150 (or so) whisper words
# by time, not by index. We use whisper's per-word times as ANCHORS.
# For each script word, find the segment of the audio it's likely in by
# using the closest whisper word by position.

# We have 217 script words spread over 65s of audio.
# We have ~150 whisper words spread over ~65s of audio too.
# The script words are spaced ~0.30s apart on average.
# The whisper words are spaced ~0.43s apart on average.
# So whisper is dropping about 30% of words. We need to assign each
# script word a time.

# Use whisper's per-word times as anchors, then assign script words
# between consecutive whisper words.

duration = 65.0
n_s = len(script_words)
n_w = len(w_words)

# For each script word, compute its expected index in whisper's output:
# we linearly map script index i -> whisper index = i * (n_w-1) / (n_s-1)
# This works if whisper dropped words roughly evenly.
new_words = []
for i, sw in enumerate(script_words):
    w_pos = i * (n_w - 1) / max(1, (n_s - 1))
    w_idx_lo = int(w_pos)
    w_idx_hi = min(w_idx_lo + 1, n_w - 1)
    frac = w_pos - w_idx_lo
    t = w_words[w_idx_lo]['t'] + frac * (w_words[w_idx_hi]['t'] - w_words[w_idx_lo]['t'])
    if w_idx_lo == w_idx_hi:
        e = w_words[w_idx_lo]['end']
    else:
        e = w_words[w_idx_lo]['end'] + frac * (w_words[w_idx_hi]['end'] - w_words[w_idx_lo]['end'])
    new_words.append({'t': float(t), 'end': float(e), 'w': sw})

# Clamp to duration
for w in new_words:
    w['t'] = min(w['t'], duration)
    w['end'] = min(w['end'], duration)

new_align = {
    'wav_path': 'round_1_audio.wav',
    'duration_s': float(duration),
    'words': new_words,
}

with open(align_path, 'w') as f:
    json.dump(new_align, f, indent=2)
print(f"Saved {len(new_words)} words to: {align_path}")
print('First 15 new words:')
for w in new_words[:15]:
    print(f"  t={w['t']:.2f}-{w['end']:.2f}  {w['w']}")
print('...')
print('Last 5:')
for w in new_words[-5:]:
    print(f"  t={w['t']:.2f}-{w['end']:.2f}  {w['w']}")
