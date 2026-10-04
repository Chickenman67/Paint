# _batch_audio.py -- per-beat TTS for the segment scripts, batched.
#
# WHY PER-BEAT AND NOT PER-110-WORD-CHUNK (seg 3's approach):
#
#   1. The chatterbox CPU bug "duplicates the tail of a long chunk" (memory:
#      chatterbox-cpu-duplicates-long-chunk-tail) is a long-chunk failure. Our
#      beats are 12-20 words, an order of magnitude under the 110-word cap.
#   2. Synthesizing beat-by-beat gives us EXACT beat boundaries in the audio
#      timeline. They are ground truth, not whisper estimates. This is the
#      cleanest possible answer to CLAUDE.md SS5's "visuals drift because the
#      TTS came in longer than predicted": the card schedule can never drift at
#      a beat boundary because there is no prediction involved.
#   3. It produces the "small breaths between beats" that CLAUDE.md SS3 says the
#      reference has and that Kokoro flattened. Here they are structural.
#
# Granularity is DECOUPLED: the TTS unit is a beat, but the CARD unit is a
# clause. A beat of 16 words is ~4.8s, which is coarser than the canon's ~3.5s
# median card. So the card layer sub-divides a beat at clause boundaries found
# in the per-word onsets WITHIN that beat. Safe chunking for the synthesiser,
# fine-grained cutting for the editor.
#
# Reads   <seg>/script.json
# Writes  <seg>/round_1_audio.wav       24 kHz mono 16-bit
#         <seg>/round_1_beats.json      exact per-beat [start,end] in that WAV
#         <seg>/_beats/NNN.wav          the raw per-beat renders (resumable)
#
# Resumable: a beat whose _beats/NNN.wav already exists and is non-trivial is
# reused, so an interrupted run does not restart from zero.

import argparse
import io
import json
import os
import re
import sys
import time
import wave

# chatterbox's sampler draws a tqdm bar per generate() call. Across ~120 beats
# that is ~120k lines of progress-bar spam that drowns the run log we actually
# read. Disable it before chatterbox imports.
os.environ.setdefault('TQDM_DISABLE', '1')

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))          # .../work/segments
sys.path.insert(0, os.path.join(HERE, '..'))                # .../work  (has lib/)

from lib.tts import _ensure_model  # noqa: E402

SR = 24000

# Target pacing. CLAUDE.md SS2 band is 190-213 wpm; we aim mid-band.
TARGET_WPM = 200.0
WPM_LOW, WPM_HIGH = 190.0, 213.0

# Inter-beat breath. Chatterbox itself adds a little dead air at each call
# boundary; we trim that, then re-insert a controlled gap. Clamped because a
# gap below ~0.12s reads as a stumble and above ~0.60s reads as a dead edit.
GAP_MIN, GAP_MAX = 0.12, 0.60

TRIM_MARGIN_S = 0.05   # keep this much air at each end of a beat after trimming
TRIM_RMS = 0.006       # below this RMS a beat is considered silent at its edge

ORDER = [
    ('tres2b', 4), ('wasp17b', 5), ('wasp127b', 6), ('gliese436b', 7),
    ('koi55', 8), ('ltt9779b', 9), ('fomalhautb', 10), ('kelt9b', 11),
    ('psoj3185', 12),
]


# ---------------------------------------------------------------------------
# WAV io
# ---------------------------------------------------------------------------

def read_wav(path):
    with wave.open(path, 'rb') as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    assert wf.getsampwidth() == 2, 'expected 16-bit'
    assert wf.getnchannels() == 1, 'expected mono'
    return np.frombuffer(raw, dtype=np.int16).copy(), sr


def write_wav(path, pcm, sr=SR):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(np.asarray(pcm, dtype=np.int16).tobytes())


def trim_silence(pcm, sr=SR):
    """Strip leading/trailing near-silence, keeping a small margin.

    chatterbox pads each generate() call. Left in, 18 beats x ~0.3s of padding
    is 5.4s of dead air that has to be paid back out of the pacing budget.
    """
    if pcm.size == 0:
        return pcm
    a = pcm.astype(np.float32) / 32768.0
    win = max(1, int(0.01 * sr))                      # 10 ms analysis window
    n = (a.size // win) * win
    if n == 0:
        return pcm
    frames = a[:n].reshape(-1, win)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    loud = np.nonzero(rms > TRIM_RMS)[0]
    if loud.size == 0:                                 # all silent: keep as is
        return pcm
    margin = int(TRIM_MARGIN_S * sr)
    lo = max(0, loud[0] * win - margin)
    hi = min(pcm.size, (loud[-1] + 1) * win + margin)
    return pcm[lo:hi]


# ---------------------------------------------------------------------------
# Word counting -- must match how the card layer counts words, or the beat
# boundaries in round_1_beats.json will not line up with the word onsets.
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[.'\-][A-Za-z0-9]+)*")


def words(text):
    return _WORD_RE.findall(text)


def load_script(key):
    p = os.path.join(HERE, key, 'script.json')
    with io.open(p, encoding='utf-8') as f:
        d = json.load(f)
    beats = d['beats']
    # LINE_EQ is the load-bearing invariant: the beats' lines, newline-joined,
    # must reproduce `narration` exactly. lib/align.py and the card layer both
    # depend on it. Fail loudly rather than rendering a desynced segment.
    cat = '\n'.join(b['line'] for b in beats).strip()
    if cat != d['narration'].strip():
        raise SystemExit('LINE_EQ failed for %s -- refusing to synthesize' % key)
    return d, beats


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------

def synth_beat(model, text, path, ex, cfg, temp):
    """Synthesize one beat, trim it, cache it. Returns the trimmed pcm."""
    if os.path.exists(path):
        try:
            pcm, sr = read_wav(path)
            if sr == SR and pcm.size > SR * 0.2:
                return pcm
        except Exception:
            pass                                          # corrupt cache: redo
    t0 = time.time()
    wav = model.generate(text, exaggeration=ex, cfg_weight=cfg, temperature=temp)
    import torch
    if isinstance(wav, torch.Tensor):
        a = wav.squeeze().cpu().numpy()
    else:
        a = np.asarray(wav).squeeze()
    pcm = np.clip(a * 32767, -32768, 32767).astype(np.int16)
    pcm = trim_silence(pcm)
    write_wav(path, pcm)
    print('      %5.2fs render  %5.2fs audio  %2dw  %s'
          % (time.time() - t0, pcm.size / SR, len(words(text)), text[:44]))
    sys.stdout.flush()
    return pcm


def run_segment(model, key, ex, cfg, temp):
    seg_dir = os.path.join(HERE, key)
    beats_dir = os.path.join(seg_dir, '_beats')
    os.makedirs(beats_dir, exist_ok=True)
    script, beats = load_script(key)

    print('  [%s] %d beats' % (key, len(beats)))
    t_start = time.time()
    pcms, nwords = [], []
    for i, b in enumerate(beats):
        txt = b['line'].strip()
        pcms.append(synth_beat(model, txt,
                                os.path.join(beats_dir, '%03d.wav' % (i + 1)),
                                ex, cfg, temp))
        nwords.append(len(words(txt)))

    speech_s = sum(p.size for p in pcms) / SR
    total_w = sum(nwords)
    n_gaps = max(1, len(pcms) - 1)

    # Solve for the inter-beat gap that lands the segment on TARGET_WPM. This
    # is a measurement-driven pacing decision, not a guess: we know exactly how
    # long the synthesiser actually took for every beat.
    target_s = total_w / TARGET_WPM * 60.0
    gap = (target_s - speech_s) / n_gaps
    clamped = min(GAP_MAX, max(GAP_MIN, gap))
    total_s = (speech_s + clamped * n_gaps)
    wpm = total_w / total_s * 60.0

    print('    %d words  speech %.1fs  gap %.3fs (raw %.3fs) -> %.1fs  %.1f wpm'
          % (total_w, speech_s, clamped, gap, total_s, wpm))
    if clamped != gap:
        print('    NOTE: gap clamped to [%.2f,%.2f]; pacing set by synthesiser rate'
              % (GAP_MIN, GAP_MAX))

    # Stitch.
    gap_pcm = np.zeros(int(round(clamped * SR)), dtype=np.int16)
    parts, beat_spans, cur = [], [], 0
    for i, p in enumerate(pcms):
        parts.append(p)
        s0, s1 = cur / SR, (cur + p.size) / SR
        beat_spans.append({'n': beats[i]['n'], 'id': beats[i]['id'],
                           'beat': beats[i].get('beat', ''),
                           'register': beats[i].get('register', 'cream'),
                           'line': beats[i]['line'],
                           'start': round(s0, 3), 'end': round(s1, 3),
                           'dur': round(s1 - s0, 3), 'words': nwords[i],
                           'wav': '_beats/%03d.wav' % (i + 1)})
        cur += p.size
        if i < len(pcms) - 1:
            parts.append(gap_pcm)
            cur += gap_pcm.size
    full = np.concatenate(parts)

    wav_out = os.path.join(seg_dir, 'round_1_audio.wav')
    write_wav(wav_out, full)

    meta = {
        'segment': key,
        'wav_path': 'round_1_audio.wav',
        'duration_s': round(len(full) / SR, 3),
        'sample_rate': SR,
        'word_count': total_w,
        'speech_s': round(speech_s, 3),
        'gap_s': round(clamped, 4),
        'wpm': round(wpm, 1),
        'wpm_in_band': bool(WPM_LOW <= wpm <= WPM_HIGH),
        'params': {'exaggeration': ex, 'cfg_weight': cfg, 'temperature': temp},
        'boundary_basis': 'exact -- per-beat renders concatenated, not predicted',
        'beats': beat_spans,
        'render_s': round(time.time() - t_start, 1),
    }
    with io.open(os.path.join(seg_dir, 'round_1_beats.json'), 'w',
                 encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)

    flag = 'IN BAND' if meta['wpm_in_band'] else '** OUT OF BAND **'
    print('    -> round_1_audio.wav  %.2fs  %.1f wpm  %s  (render %.0fs)'
          % (meta['duration_s'], wpm, flag, meta['render_s']))
    sys.stdout.flush()
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', nargs='*', default=None,
                    help='segment keys; default is all 9 pending segments')
    ap.add_argument('--exaggeration', type=float, default=0.5)
    ap.add_argument('--cfg-weight', type=float, default=0.5)
    ap.add_argument('--temperature', type=float, default=0.8)
    args = ap.parse_args()

    keys = args.segments or [k for k, _ in ORDER]
    print('loading chatterbox model...')
    t0 = time.time()
    model = _ensure_model()
    print('model ready in %.1fs' % (time.time() - t0))
    sys.stdout.flush()

    results = []
    for key in keys:
        try:
            results.append(run_segment(model, key, args.exaggeration,
                                       args.cfg_weight, args.temperature))
        except SystemExit as e:
            print('  [%s] SKIPPED: %s' % (key, e))
        except Exception as e:                            # keep going, report at end
            print('  [%s] FAILED: %s: %s' % (key, type(e).__name__, e))
            sys.stdout.flush()

    print('\n%-12s %-7s %-7s %-6s %s' % ('key', 'dur_s', 'wpm', 'words', 'status'))
    for m in results:
        print('%-12s %-7.2f %-7.1f %-6d %s'
              % (m['segment'], m['duration_s'], m['wpm'], m['word_count'],
                 'in band' if m['wpm_in_band'] else 'OUT OF BAND'))
    out = os.path.join(HERE, '_batch_audio_report.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print('\nwrote %s' % out)


if __name__ == '__main__':
    main()
