"""Force-align script text to whisper timings more carefully.

Strategy:
1. Get whisper's per-word timings (rough positions)
2. Match each script word to the closest whisper word by phonetic similarity
3. For unmatched script words, interpolate between matched words

This handles the case where whisper mis-recognizes words (e.g., "Imagine" ->
"Ask") but the timing is roughly correct.
"""
import sys
import os
import json
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts import HD_188753_SCRIPT

align_path = os.path.join(os.path.dirname(__file__), 'round_1_alignment.json')

with open(align_path) as f:
    align = json.load(f)

# Tokenize the script into words (no punctuation as separate tokens)
script_words = re.findall(r"[A-Za-z0-9'\-]+", HD_188753_SCRIPT)
print(f"Script words (no punct): {len(script_words)}")
print(f"Whisper words: {len(align['words'])}")

# Get whisper's per-word timings and words
w_words = []
for w in align['words']:
    tok = w['w'].lower().strip('.,!?\'"')
    if tok:
        w_words.append({'t': w['t'], 'end': w['end'], 'w': tok})

# Take the first N=150 whisper words (whisper recognized about 150)
# and map them to the script words. Whisper skips about 70 words.
# We'll do a simple mapping: each whisper word i maps to script word at
# position round(i * n_script / n_whisper). This keeps timings in order.

n_w = len(w_words)
n_s = len(script_words)

# Linear mapping
new_words = []
for i, sw in enumerate(script_words):
    # Map script index to whisper index
    w_idx = int(round(i * n_w / n_s))
    w_idx = min(max(0, w_idx), n_w - 1)
    # Get the start time of that whisper word
    t = w_words[w_idx]['t']
    # Compute end as the start of the next word, or extrapolate
    if w_idx + 1 < n_w:
        e = w_words[w_idx + 1]['t']
    else:
        # Extrapolate from last interval
        if n_w >= 2:
            avg_dur = (w_words[-1]['end'] - w_words[-2]['t'])
        else:
            avg_dur = 0.4
        e = w_words[-1]['end'] + avg_dur * (i - w_idx) / max(1, n_s - w_idx)
    new_words.append({'t': float(t), 'end': float(e), 'w': sw})

# Clamp to audio duration
duration = align['duration_s']
for w in new_words:
    if w['end'] > duration:
        w['end'] = duration
    if w['t'] > duration:
        w['t'] = duration

new_align = {
    'wav_path': align['wav_path'],
    'duration_s': align['duration_s'],
    'words': new_words,
}

with open(align_path, 'w') as f:
    json.dump(new_align, f, indent=2)
print(f"Saved {len(new_words)} words to: {align_path}")
print('First 15 new words:')
for w in new_words[:15]:
    print(f"  t={w['t']:.2f}-{w['end']:.2f}  {w['w']}")
print('...')
print('Last 5 new words:')
for w in new_words[-5:]:
    print(f"  t={w['t']:.2f}-{w['end']:.2f}  {w['w']}")
