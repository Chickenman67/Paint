# work3/lib/audio3.py -- narration-audio pipeline for the work3 rebuild.
#
# TARGET: 165 wpm, near-continuous delivery.
#
# This is the carry-forward of work/segments/_v2_audio.py (which proved 170 wpm)
# with the target lowered to 165. The proven primitives and the closed-form
# pacing solve are unchanged; only the constants and the output paths moved.
#
# WHY A TEMPO STAGE EXISTS AT ALL (the blocking problem chatterbox creates):
#   chatterbox's model.generate() takes only exaggeration / cfg_weight /
#   temperature (plus sampling knobs). There is NO speed or rate knob, and its
#   natural CPU output runs ~210-220 wpm. So reaching 165 wpm by padding
#   inter-beat silence alone is UNREACHABLE (it would need multi-second gaps).
#
# THE SOLVE (closed-form, no iteration), in this order:
#   1. Squeeze chatterbox's internal sentence silences FIRST (the retention
#      lever), so the measured speech is near-continuous.
#   2. required_speech = (total_words / TARGET_WPM * 60) - gap * n_gaps
#   3. Stretch every beat by the constant ratio raw_total / required_speech via
#      ffmpeg `atempo` (pitch-preserving; free, no resampling). A small 3 dB
#      high shelf at 3.5 kHz undoes the timbral darkening the stretch costs.
#
#   *** ATEMPO DIRECTION (the one sign error that still "looks like it ran"):
#   atempo factor f gives output_duration = input_duration / f. So f < 1 SLOWS
#   (longer output) and f > 1 SPEEDS UP. chatterbox is fast (~215 wpm) and we
#   want 165, so f < 1. Inverting this ships a 2x-too-fast render that still
#   "looks like it ran." The solve below is written f = raw / required, which
#   is the correct direction: raw is longer than required, so f < 1, so slower.
#
# Reads   work3/segments/<KEY>/script.json
# Writes  work3/segments/<KEY>/audio.wav            24 kHz mono 16-bit (the audio)
#         work3/segments/<KEY>/beats.json            exact per-beat [start,end]
#         work3/segments/<KEY>/_beats_raw/NNN.wav   raw chatterbox renders
#         work3/segments/<KEY>/_beats_sq/NNN.wav    pause-squeezed, pre-tempo
#         work3/segments/<KEY>/_beats/NNN.wav        tempo-stretched + EQ (final)
#
# Beat boundaries are exact in audio.wav (the pieces ARE the file), not
# predicted from word counts, so the visual sync driven off beats.json cannot
# drift. The word regex is byte-identical to _batch_audio's, so phrase timing
# (phrase_timing.py) and the beat spans count words the same way.

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import wave

# chatterbox's sampler draws a tqdm bar per generate(); across ~130 beats that
# is enough spam to drown the run log. Disable it before chatterbox imports.
os.environ.setdefault('TQDM_DISABLE', '1')

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))          # .../work3/lib
WORK3 = os.path.dirname(HERE)                              # .../work3
SEG_ROOT = os.path.join(WORK3, 'segments')

SR = 24000

# --- pacing target ----------------------------------------------------------
# Lowered from the proven 170 to the requested 165. Everything else about the
# solve is unchanged, so this is a one-constant change.
TARGET_WPM = 165.0

# Inter-beat breath. A beat, not a breath: the boundary is still legible in the
# visuals via the snap cut, but there is no audible dead air (retention).
NOMINAL_GAP_S = 0.08

# Internal-pause squeeze (the retention fix). chatterbox leaves a 0.2-0.5 s hole
# at each sentence end INSIDE a beat; edge-trimming only strips the beat EDGES,
# so those holes survived. Any internal silence >= ABOVE_S is cut to TO_S.
# Applied to the cached raw PCM BEFORE the tempo solve so the solve measures
# the squeezed durations and stays self-consistent.
PAUSE_SQUEEZE_ABOVE_S = 0.16
PAUSE_SQUEEZE_TO_S = 0.07

# Brightness compensation for the atempo stretch. A pitch-preserving
# time-stretch lowers the spectral centroid and the f0 movement the more we
# slow it; that is damage WE introduce, so undoing it needs no reference. The
# target here is UNDAMAGE, not a (contaminated) reference number. 3 dB is
# deliberately modest -- our narration is full of /s/ ("stars", "surface") and
# a heavier shelf would read as sibilance.
BRIGHT_SHELF_HZ = 3500
BRIGHT_SHELF_DB = 3.0

# Safety clamp on the gap and the flag tolerance.
GAP_MIN, GAP_MAX = 0.02, 0.55
assert GAP_MIN <= NOMINAL_GAP_S <= GAP_MAX, \
    'NOMINAL_GAP_S must be inside the gap clamp band or pacing is unreachable'
# How far off TARGET_WPM a segment may land before it is flagged OFF TARGET.
# atempo is sample-exact, so with the gap fixed the solve is too; 4 wpm is
# ~0.3 s over a 75 s segment -- inside the visual sync tolerance.
WPM_TOL = 4.0

# Edge-trim parameters (carried from _batch_audio.py: strip chatterbox padding).
TRIM_MARGIN_S = 0.05
TRIM_RMS = 0.006

# The 10 segments, in film order.
ORDER = [
    'tres2b', 'wasp17b', 'wasp127b', 'gliese436b', 'koi55', 'ltt9779b',
    'fomalhautb', 'psrb1257', 'kelt9b', 'psoj3185',
]

# The word regex is byte-identical to _batch_audio.py (and hence the aligner's),
# so beat boundaries line up with word onsets. Do not change one without the
# other.
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[.'\-][A-Za-z0-9]+)*")


def words(text):
    return _WORD_RE.findall(text)


# ---------------------------------------------------------------------------
# WAV io
# ---------------------------------------------------------------------------

def read_wav(path):
    with wave.open(path, 'rb') as wf:
        sr = wf.getframerate()
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        n = wf.getnframes()
        raw = wf.readframes(n)
    assert sw == 2, 'expected 16-bit'
    assert nch == 1, 'expected mono'
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

    chatterbox pads each generate() call. Left in, ~14 beats x ~0.3 s of padding
    is dead air that must be paid back out of the pacing budget.
    """
    if pcm.size == 0:
        return pcm
    a = pcm.astype(np.float32) / 32768.0
    win = max(1, int(0.01 * sr))                      # 10 ms analysis window
    n = (a.size // win) * win
    if n == 0:
        return pcm
    frames = a[:n].reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float32) ** 2).mean(axis=1))
    loud = np.nonzero(rms > TRIM_RMS)[0]
    if loud.size == 0:                                 # all silent: keep as is
        return pcm
    margin = int(TRIM_MARGIN_S * sr)
    lo = max(0, loud[0] * win - margin)
    hi = min(pcm.size, (loud[-1] + 1) * win + margin)
    return pcm[lo:hi]


# ---------------------------------------------------------------------------
# pause squeeze (the retention lever)
# ---------------------------------------------------------------------------

def squeeze_pauses(pcm, above_s=PAUSE_SQUEEZE_ABOVE_S,
                   to_s=PAUSE_SQUEEZE_TO_S, thresh_db=-38.0):
    """Shorten internal silences to `to_s` so the read is near-continuous.

    Every internal silence longer than `above_s` is cut to `to_s`. Short plosive
    closures (< above_s) are left alone -- they are articulation, not pauses.
    The level-relative threshold (vs the 95th-percentile frame envelope) makes
    it work the same on a quiet beat and a loud one. Leading/trailing silence is
    skipped (edge-trim owns those).

    Returns (squeezed_pcm, seconds_saved).

    NOTE: the output list is NOT seeded with the full signal -- only the speech
    kept *before* each pause plus a short breath, then the tail. Seeding the
    list with the whole pcm would double the audio (a real landmine we hit
    before); `cur` tracks the read cursor so each region is emitted exactly once.
    """
    if pcm.size == 0:
        return pcm, 0.0
    a = pcm.astype(np.float32) / 32768.0
    win = 240                                     # 10 ms
    n = (a.size // win) * win
    if n == 0:
        return pcm, 0.0
    frames = a[:n].reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-12)
    silent = db < (np.percentile(db, 95) + thresh_db)
    if not silent.any():
        return pcm, 0.0

    # collapse boolean runs -> (start_frame, end_frame)
    d = np.diff(silent.astype(np.int8))
    starts = list(np.where(d == 1)[0] + 1)
    ends = list(np.where(d == -1)[0] + 1)
    if silent[0]:
        starts.insert(0, 0)
    if silent[-1]:
        ends.append(len(silent))
    min_frames = int(round(above_s * SR / win))
    keep_frames = int(round(to_s * SR / win))

    out = []
    cur = 0
    saved = 0
    for s0, e0 in zip(starts, ends):
        if (e0 - s0) < min_frames:
            continue                             # articulation, not a pause
        if s0 == 0 or e0 == len(silent):
            continue                             # edge -- trim_silence owns these
        out.append(pcm[cur:s0 * win])            # speech up to the pause
        out.append(pcm[s0 * win:s0 * win + keep_frames])   # a short breath
        saved += ((e0 - s0) * win) - keep_frames
        cur = e0 * win
    out.append(pcm[cur:])                          # tail after the last pause
    return np.concatenate(out), saved / SR


# ---------------------------------------------------------------------------
# tempo stage
# ---------------------------------------------------------------------------

def atempo_stretch(src_wav, dst_wav, factor):
    """Time-stretch by `factor` (pitch-preserving) and compensate the timbre
    the stretch costs. factor in (0.5, 2.0).

    output_duration = input_duration / factor. So factor < 1 SLOWS (longer),
    factor > 1 speeds up.

    The equalizer is a 3 dB high shelf at 3.5 kHz. A pitch-preserving stretch
    lowers the spectral centroid and the f0 movement; that is damage WE
    introduce by slowing, so undoing part of it is justified on its own merits
    and needs no reference. 3 dB is modest on purpose -- the narration is full
    of /s/ ("stars", "surface", "gas") and a heavier shelf reads as sibilance.
    """
    factor = max(0.5, min(2.0, factor))
    filt = ('atempo=%.4f,equalizer=f=%d:t=h:width=1200:g=%g'
            % (factor, BRIGHT_SHELF_HZ, BRIGHT_SHELF_DB))
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-i', src_wav, '-filter:a', filt, '-ar', str(SR),
           '-ac', '1', '-c:a', 'pcm_s16le', dst_wav]
    subprocess.run(cmd, check=True)
    return dst_wav


# ---------------------------------------------------------------------------
# synthesis (raw, cached)
# ---------------------------------------------------------------------------

def _ensure_model():
    from chatterbox.tts import ChatterboxTTS
    return ChatterboxTTS.from_pretrained(device='cpu')


_model = [None]


def get_model():
    if _model[0] is None:
        print('loading chatterbox model...')
        t0 = time.time()
        _model[0] = _ensure_model()
        print('model ready in %.1fs' % (time.time() - t0))
        sys.stdout.flush()
    return _model[0]


def synth_raw_beat(text, path, ex, cfg, temp):
    """Synthesize one beat at chatterbox's natural rate, trim, cache. Returns pcm.

    The cache is keyed only on the path (as in prior rounds). Clear the
    _beats_raw dir if you change synthesis params -- a stale cache would
    otherwise be silently reused. The model is fetched lazily, so a tempo-only
    re-run (all raw beats cached) never pays the ~20 s load.
    """
    if os.path.exists(path):
        try:
            pcm, sr = read_wav(path)
            if sr == SR and pcm.size > SR * 0.2:
                return pcm
        except Exception:
            pass                                          # corrupt cache: redo
    t0 = time.time()
    wav = get_model().generate(text, exaggeration=ex, cfg_weight=cfg,
                               temperature=temp)
    import torch
    if isinstance(wav, torch.Tensor):
        a = wav.squeeze().cpu().numpy()
    else:
        a = np.asarray(wav).squeeze()
    pcm = np.clip(a * 32767, -32768, 32767).astype(np.int16)
    pcm = trim_silence(pcm)
    write_wav(path, pcm)
    print('      raw %5.2fs audio  %2dw  %s'
          % (pcm.size / SR, len(words(text)), text[:44]))
    sys.stdout.flush()
    return pcm


# ---------------------------------------------------------------------------
# per-segment driver
# ---------------------------------------------------------------------------

def load_script(key):
    p = os.path.join(SEG_ROOT, key, 'script.json')
    with io.open(p, encoding='utf-8') as f:
        d = json.load(f)
    beats = d['beats']
    # LINE_EQ is load-bearing: the beats' lines, newline-joined, must reproduce
    # `narration` exactly. phrase_timing and the card layer depend on it. Fail
    # loudly rather than rendering a desynced segment.
    cat = '\n'.join(b['line'] for b in beats).strip()
    if cat != d['narration'].strip():
        raise SystemExit('LINE_EQ failed for %s -- refusing to synthesize' % key)
    return d, beats


def run_segment(key, ex, cfg, temp, force=False):
    seg_dir = os.path.join(SEG_ROOT, key)
    raw_dir = os.path.join(seg_dir, '_beats_raw')
    sq_dir = os.path.join(seg_dir, '_beats_sq')
    slow_dir = os.path.join(seg_dir, '_beats')
    for d in (raw_dir, sq_dir, slow_dir):
        os.makedirs(d, exist_ok=True)
    script, beats = load_script(key)

    print('  [%s] %d beats' % (key, len(beats)))
    t_start = time.time()

    # Pass 1: raw synthesis (cached), PAUSE SQUEEZE, and measure each beat.
    # The squeeze runs on the cached raw PCM (cheap, no model) and writes an
    # intermediate so the tempo stage and the solve both operate on SQUEEZED
    # durations. Measuring the squeezed audio is what keeps the closed-form
    # solve exact: the dead air we removed is not silently re-added by a
    # too-small atempo factor.
    sq_pcms, nwords, sq_s_list, saved_total, raw_speech_s = [], [], [], 0.0, 0.0
    for i, b in enumerate(beats):
        txt = b['line'].strip()
        raw = synth_raw_beat(txt, os.path.join(raw_dir, '%03d.wav' % (i + 1)),
                             ex, cfg, temp)
        sq, saved_s = squeeze_pauses(raw)
        write_wav(os.path.join(sq_dir, '%03d.wav' % (i + 1)), sq)
        sq_pcms.append(sq)
        nwords.append(len(words(txt)))
        sq_s_list.append(sq.size / SR)
        saved_total += saved_s
        raw_speech_s += raw.size / SR
    print('    squeeze: removed %.2fs internal pause (%.1f%% of raw speech)'
          % (saved_total, 100 * saved_total / max(1e-6, raw_speech_s)))

    # Pass 2: solve pacing, then apply the tempo stage.
    #
    # We want:
    #     total_s = total_w / TARGET_WPM * 60
    #     total_s = speech_s + gap * n_gaps
    # With gap fixed, speech must occupy total_s - gap*n_gaps. Each beat is then
    # scaled in proportion to its (squeezed) duration so the whole lands on
    # target. Self-consistent by construction -- no iteration needed.
    total_w = sum(nwords)
    n_gaps = max(1, len(sq_pcms) - 1)
    raw_total_s = sum(sq_s_list)
    target_total_s = total_w / TARGET_WPM * 60.0
    gap = NOMINAL_GAP_S
    required_speech_s = max(1.0, target_total_s - gap * n_gaps)

    # f = raw_total / required. Since chatterbox runs ~215 wpm and we want 165,
    # required > raw, so f < 1 -> SLOW. This is the correct direction.
    global_ratio = raw_total_s / required_speech_s

    slow_pcms = []
    factors = []
    for i, nw in enumerate(nwords):
        sq_wav = os.path.join(sq_dir, '%03d.wav' % (i + 1))
        slow_wav = os.path.join(slow_dir, '%03d.wav' % (i + 1))
        # per-beat factor: this beat's share of the required output / its raw len
        beat_required_s = required_speech_s * (sq_s_list[i] / raw_total_s)
        f = max(0.5, min(2.0, sq_s_list[i] / beat_required_s))
        factors.append(f)
        if force or not os.path.exists(slow_wav):
            atempo_stretch(sq_wav, slow_wav, f)
        sp, sr = read_wav(slow_wav)
        assert sr == SR, 'tempo stage changed sample rate'
        slow_pcms.append(sp)

    speech_s = sum(p.size for p in slow_pcms) / SR
    total_s = speech_s + gap * n_gaps
    wpm = total_w / total_s * 60.0
    pause_frac = (gap * n_gaps) / total_s

    print('    %d words  raw %.0fwpm  ratio %.3f  factors %.2f..%.2f  gap %.2fs'
          % (total_w, total_w / (raw_total_s / 60), global_ratio,
             min(factors), max(factors), gap))
    flag = 'ON TARGET' if abs(wpm - TARGET_WPM) <= WPM_TOL else '** OFF TARGET **'
    print('    -> %.1fs speech + %.1fs gaps = %.1fs  %.1f wpm  pause %.1f%%  %s'
          % (speech_s, gap * n_gaps, total_s, wpm, pause_frac * 100, flag))
    if abs(wpm - TARGET_WPM) > WPM_TOL:
        print('    ** WARNING: wpm %.1f is %.1f off target %.0f **'
              % (wpm, abs(wpm - TARGET_WPM), TARGET_WPM))

    # Stitch the slowed beats with the gap.
    #
    # The parts list is built by APPENDING each beat then the gap; it is NOT
    # seeded with the full signal (that doubled the audio once). `cur` is the
    # running sample cursor into audio.wav and advances by exactly the samples
    # emitted, so the recorded [start,end] spans ARE the file's layout.
    gap_pcm = np.zeros(int(round(gap * SR)), dtype=np.int16)
    parts, spans, cur = [], [], 0
    for i, p in enumerate(slow_pcms):
        parts.append(p)
        s0, s1 = cur / SR, (cur + p.size) / SR
        spans.append({'n': beats[i]['n'], 'id': beats[i]['id'],
                      'beat': beats[i].get('beat', ''),
                      'line': beats[i]['line'],
                      'start': round(s0, 3), 'end': round(s1, 3),
                      'dur': round(s1 - s0, 3), 'words': nwords[i],
                      'wav': '_beats/%03d.wav' % (i + 1)})
        cur += p.size
        if i < len(slow_pcms) - 1:
            parts.append(gap_pcm)
            cur += gap_pcm.size
    full = np.concatenate(parts)

    wav_out = os.path.join(seg_dir, 'audio.wav')
    write_wav(wav_out, full)

    meta = {
        'segment': key,
        'wav_path': 'audio.wav',
        'duration_s': round(len(full) / SR, 3),
        'sample_rate': SR,
        'word_count': total_w,
        'speech_s': round(speech_s, 3),
        'gap_s': round(gap, 4),
        'wpm': round(wpm, 1),
        'pause_frac': round(pause_frac, 3),
        'on_target': bool(abs(wpm - TARGET_WPM) <= WPM_TOL),
        'params': {'exaggeration': ex, 'cfg_weight': cfg, 'temperature': temp,
                   'target_wpm': TARGET_WPM, 'nominal_gap_s': NOMINAL_GAP_S,
                   'pause_squeeze_above_s': PAUSE_SQUEEZE_ABOVE_S,
                   'pause_squeeze_to_s': PAUSE_SQUEEZE_TO_S,
                   'bright_shelf_hz': BRIGHT_SHELF_HZ,
                   'bright_shelf_db': BRIGHT_SHELF_DB,
                   'tempo_factors': [round(f, 4) for f in factors],
                   'raw_wpm': round(total_w / (raw_total_s / 60.0), 1),
                   'speech_wpm': round(total_w / (speech_s / 60.0), 1),
                   'squeeze_saved_s': round(saved_total, 2)},
        'boundary_basis': 'exact -- per-beat renders atempo-stretched then concatenated',
        'beats': spans,
        'render_s': round(time.time() - t_start, 1),
    }
    with io.open(os.path.join(seg_dir, 'beats.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)

    print('    -> audio.wav  %.2fs  %.1f wpm  %s  (render %.0fs)'
          % (meta['duration_s'], wpm, flag, meta['render_s']))
    sys.stdout.flush()
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', nargs='*', default=None,
                    help='segment keys; default is all 10 in film order')
    ap.add_argument('--exaggeration', type=float, default=0.5)
    ap.add_argument('--cfg-weight', type=float, default=0.5)
    ap.add_argument('--temperature', type=float, default=0.8)
    ap.add_argument('--force', action='store_true',
                    help='re-do the tempo stage (ignore cached _beats/NNN.wav)')
    args = ap.parse_args()

    keys = args.segments or ORDER
    results = []
    for key in keys:
        try:
            results.append(run_segment(key, args.exaggeration, args.cfg_weight,
                                       args.temperature, force=args.force))
        except SystemExit as e:
            print('  [%s] SKIPPED: %s' % (key, e))
        except Exception as e:
            print('  [%s] FAILED: %s: %s' % (key, type(e).__name__, e))
            sys.stdout.flush()

    print('\n%-12s %-8s %-7s %-7s %-6s %s'
          % ('key', 'dur_s', 'wpm', 'pause%%', 'words', 'status'))
    for m in results:
        print('%-12s %-8.2f %-7.1f %-7.0f %-6d %s'
              % (m['segment'], m['duration_s'], m['wpm'],
                 m['pause_frac'] * 100, m['word_count'],
                 'on target' if m['on_target'] else 'OFF TARGET'))
    out = os.path.join(WORK3, 'audio3_report.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print('\nwrote %s' % out)


if __name__ == '__main__':
    main()