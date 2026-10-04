"""Re-align with different settings."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import whisper
import numpy as np
import json
import wave
import scipy.signal
from scripts import HD_188753_SCRIPT

wav = os.path.join(os.path.dirname(__file__), 'round_1_audio.wav')
out = os.path.join(os.path.dirname(__file__), 'round_1_alignment.json')

with wave.open(wav, 'rb') as wf:
    sr = wf.getframerate()
    n = wf.getnframes()
    raw = wf.readframes(n)
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
audio = scipy.signal.resample(audio, int(len(audio) * 16000 / sr))
sr = 16000

# Use the entire script as the initial prompt so whisper has the exact vocabulary
prompt = HD_188753_SCRIPT.strip()

model = whisper.load_model('small.en')
print('Loaded small.en')
result = model.transcribe(
    audio,
    language='en',
    word_timestamps=True,
    initial_prompt=prompt,
    condition_on_previous_text=True,
    temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    no_speech_threshold=0.2,
    logprob_threshold=-1.0,
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
print('Words:', len(words))
for w in words[:50]:
    print('  t=%.2f-%.2f  %s' % (w['t'], w['end'], w['w']))
print('...')
for w in words[-10:]:
    print('  t=%.2f-%.2f  %s' % (w['t'], w['end'], w['w']))

# Save
result_dict = {
    'wav_path': 'round_1_audio.wav',
    'duration_s': float(len(audio) / sr),
    'words': words,
}
with open(out, 'w') as f:
    json.dump(result_dict, f, indent=2)
print('Saved to:', out)
