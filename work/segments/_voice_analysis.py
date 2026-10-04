# _voice_analysis.py -- measure DELIVERY characteristics of a narration WAV.
#
# WHY THIS EXISTS (the "match the Paint Explainer voice" reset):
#   CLAUDE.md §1.2 requires the audio to be OURS: "the narration text, the
#   planet portraits, the stickman, the captions, and the audio are all our own.
#   ... We do not transcribe, paraphrase, or quote the reference." So we do NOT
#   clone the reference narrator's voice -- that would be both a content copy and
#   a copy of a real identifiable person's voice.
#
#   What we CAN and DO match is the DELIVERY: the measurable, content-independent
#   characteristics that make a voice feel like a fast, punchy explainer.
#   Every metric below is computed from the waveform alone. Nothing here
#   transcribes, and nothing here needs to know what was said.
#
#   The metrics, and why each one matters for retention:
#
#     syllable_rate   syllables/second over VOICED time. Language-independent,
#                     so it compares English-to-English honestly. The single
#                     best proxy for "does this sound fast and energetic".
#     speech_duty     fraction of total time that is actually voiced. The
#                     complement of "pause_frac". High duty = few dead gaps =
#                     continuous, retention-friendly delivery. This is the
#                     number the "little to no pause" instruction moves.
#     pause_hist      the distribution of SILENCES between voiced runs. Tells us
#                     not just how many pauses but how LONG the worst one is. A
#                     single 0.6s hole mid-sentence is worse than many short ones.
#     f0_*            pitch register. median F0 sets the voice's perceived
#                     gender/age; f0_iqr sets expressiveness (a flat voice has a
#                     narrow IQR).
#     f0_range_norm   pitch movement per second, normalized -- how animated the
#                     delivery is rather than just how high.
#     bright          spectral centroid mean, normalized by F0. Timbre brightness
#                     relative to pitch, so a higher number is a brighter/more
#                     present voice at the same pitch.
#     energy_dyn      dynamic range in dB (p95 - p5). A flat, dead read has low
#                     dynamics; a punchy explainer pushes the key words.
#     breath_ratio    fraction of voiced energy that is low-energy (aspiration).
#                     Breathiness. Matters for "conversational vs announcer".
#
# Usage:
#   python _voice_analysis.py <wav> [<wav> ...]
#   python _voice_analysis.py --json <wav> ...

import argparse
import json
import os
import sys
import wave

import numpy as np

SR = 24000


# ---------------------------------------------------------------------------
# io
# ---------------------------------------------------------------------------

def read_wav(path):
    with wave.open(path, 'rb') as w:
        if w.getsampwidth() != 2:
            raise ValueError('%s: expected 16-bit, got %d bytes'
                             % (path, w.getsampwidth()))
        n = w.getnframes()
        raw = w.readframes(n)
        sr = w.getframerate()
        ch = w.getnchannels()
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        # linear resample -- good enough for envelope/F0 statistics
        n_out = int(round(len(a) * SR / float(sr)))
        a = np.interp(np.linspace(0, len(a) - 1, n_out),
                      np.arange(len(a)), a).astype(np.float32)
    return a


# ---------------------------------------------------------------------------
# voicing
# ---------------------------------------------------------------------------

def frame_energy(a, win=480, hop=120):
    """Short-time RMS envelope. win/hop at 24kHz -> 40ms/5ms. Vectorized."""
    if len(a) < win:
        return np.array([float(np.sqrt((a.astype(np.float64) ** 2).mean() + 1e-12))])
    n = 1 + (len(a) - win) // hop
    # cumulative-sum sliding energy: O(n) instead of building an n x win matrix
    cs = np.concatenate(([0.0], np.cumsum(a.astype(np.float64) ** 2)))
    starts = np.arange(n) * hop
    e = (cs[starts + win] - cs[starts]) / win
    return np.sqrt(np.maximum(e, 0.0) + 1e-12)


def voiced_mask(env, hop_s, floor_db=-38.0, min_run_s=0.035):
    """Binary voiced/unvoiced from the RMS envelope.

    floor_db is relative to the 95th percentile, so it adapts to any recording
    level (the reference and our TTS have very different absolute levels).
    """
    db = 20 * np.log10(env + 1e-12)
    ref = np.percentile(db, 95)
    voiced = db > (ref + floor_db)
    # close short holes (plosive stop closures are not pauses)
    hop_n = max(1, int(round(min_run_s / hop_s)))
    # binary closing: remove voiced runs shorter than min_run_s
    runs = _runs(voiced)
    out = np.zeros_like(voiced)
    for a0, b0, v in runs:
        if v and (b0 - a0) >= hop_n:
            out[a0:b0] = True
    return out


def _runs(mask):
    """[(start, end, value), ...] for a boolean mask."""
    if mask.size == 0:
        return []
    d = np.diff(mask.astype(np.int8))
    starts = list(np.where(d == 1)[0] + 1)
    ends = list(np.where(d == -1)[0] + 1)
    if mask[0]:
        starts.insert(0, 0)
    if mask[-1]:
        ends.append(len(mask))
    return [(s, e, bool(mask[s])) for s, e in zip(starts, ends)]


# ---------------------------------------------------------------------------
# syllables
# ---------------------------------------------------------------------------

def count_syllable_nuclei(env, hop_s):
    """Count energy peaks -- an acoustic proxy for syllable nuclei.

    This is deliberately NOT an ASR transcription. A syllable nucleus is a local
    energy maximum; counting them gives a rate that is comparable across
    recordings and languages without knowing a single word.
    """
    e = env - np.median(env)
    if e.size < 5:
        return 0
    # light smoothing so noise wiggles do not count
    k = np.array([0.25, 0.5, 0.25])
    es = np.convolve(e, k / k.sum(), mode='same')
    # a nucleus is a local max at least `prom` above the local floor
    prom = 0.25 * (np.percentile(es, 95) - np.percentile(es, 10))
    n = 0
    last = -1e9
    min_sep = int(round(0.09 / hop_s))     # nuclei closer than 90ms are one syllable
    for i in range(1, len(es) - 1):
        if es[i] > es[i - 1] and es[i] >= es[i + 1] and es[i] > prom:
            if i - last >= min_sep:
                n += 1
                last = i
    return n


# ---------------------------------------------------------------------------
# pitch
# ---------------------------------------------------------------------------

def f0_track(a, hop_s=0.005, fmin=70.0, fmax=320.0):
    """Autocorrelation F0 per frame. Returns (times, f0_hz with 0 = unvoiced).

    Two speed measures, because this runs over 15 minutes of audio and has to be
    fast enough to iterate on:
      1. DECIMATE to 8 kHz first. F0 lives at 70-320 Hz, so 4 kHz Nyquist is
         ample, and this is a 3x cheaper FFT on 3x fewer samples.
      2. BATCH the autocorrelation as one numpy FFT over a zero-padded frame
         matrix, not a per-frame np.correlate loop (which was O(frames*win^2)
         and took MINUTES on a 90 s clip -- unusable for tuning a voice).
    """
    target_sr = 8000
    if SR != target_sr:
        n_out = int(round(len(a) * target_sr / float(SR)))
        ad = np.interp(np.linspace(0, len(a) - 1, n_out),
                       np.arange(len(a)), a).astype(np.float64)
        hop_s_dec = hop_s * (target_sr / float(SR))
    else:
        ad = a.astype(np.float64)
        hop_s_dec = hop_s
    step = max(1, int(round(hop_s_dec * target_sr)))
    win = max(8, int(round(0.040 * target_sr)))          # 40ms window in samples
    n = max(0, 1 + (len(ad) - win) // step)
    if n <= 0:
        return np.zeros(0), np.zeros(0)

    idx = np.arange(win)[None, :] + step * np.arange(n)[:, None]
    frames = ad[idx]
    frames -= frames.mean(axis=1, keepdims=True)

    energy = (frames * frames).mean(axis=1)

    nfft = 1
    while nfft < 2 * win:
        nfft <<= 1
    spec = np.fft.rfft(frames, n=nfft, axis=1)
    ac = np.fft.irfft(spec * np.conj(spec), n=nfft, axis=1)[:, :win]

    with np.errstate(invalid='ignore', divide='ignore'):
        acn = ac / ac[:, :1]
    acn[~np.isfinite(acn)] = 0.0

    lag_min = max(1, int(target_sr / fmax))
    lag_max = min(win - 2, int(target_sr / fmin))
    if lag_max <= lag_min:
        return np.arange(n) * hop_s_dec, np.zeros(n)

    seg = acn[:, lag_min:lag_max]
    k = np.argmax(seg, axis=1) + lag_min
    peak = acn[np.arange(n), k]
    voiced = (peak >= 0.30) & (energy > 1e-9)

    kc = np.clip(k, 1, win - 2)
    rows = np.arange(n)
    y0, y1, y2 = acn[rows, kc - 1], acn[rows, kc], acn[rows, kc + 1]
    den = y0 - 2 * y1 + y2
    shift = np.where(np.abs(den) > 1e-9, 0.5 * (y0 - y2) / np.where(den == 0, 1, den), 0.0)
    shift = np.clip(shift, -1.0, 1.0)

    f0 = np.zeros(n, dtype=np.float64)
    f0[voiced] = target_sr / (k[voiced] + shift[voiced])
    f0[(f0 < fmin) | (f0 > fmax)] = 0.0
    # report on the ORIGINAL 24 kHz timeline
    return np.arange(n) * hop_s_dec, f0


# ---------------------------------------------------------------------------
# main analysis
# ---------------------------------------------------------------------------

def analyse(path):
    a = read_wav(path)
    dur = len(a) / SR
    hop_s = 0.005
    env = frame_energy(a)
    mask = voiced_mask(env, hop_s)
    runs = _runs(mask)
    voiced_runs = [(s, e) for s, e, v in runs if v]
    silences = [(s, e) for s, e, v in runs if not v]

    voiced_s = sum(e - s for s, e in voiced_runs) * hop_s
    n_syl = count_syllable_nuclei(env, hop_s)
    syl_rate = n_syl / voiced_s if voiced_s > 0.1 else 0.0

    # silences that sit BETWEEN voiced runs (true pauses, not head/tail)
    inner = []
    for i, (s, e) in enumerate(silences):
        before = any(e2 >= s for _, e2 in voiced_runs)
        after = any(s2 <= e for s2, _ in voiced_runs)
        if before and after:
            inner.append((e - s) * hop_s)
    inner_s = sorted(inner)

    t, f0 = f0_track(a, hop_s=hop_s)
    f0v = f0[f0 > 0]

    # spectral centroid, computed on voiced frames only (batched rfft)
    bright = 0.0
    if f0v.size:
        N = 1024
        step = 480
        nfr = max(0, 1 + (len(a) - N) // step)
        if nfr:
            si = step * np.arange(nfr)
            idx = np.arange(N)[None, :] + si[:, None]
            fr = a[idx].astype(np.float64) * np.hanning(N)[None, :]
            sp = np.abs(np.fft.rfft(fr, axis=1)) ** 2
            # only frames the envelope calls voiced
            mrow = np.clip(si // (int(hop_s * SR)), 0, len(mask) - 1)
            keep = mask[mrow]
            if keep.any():
                frq = np.fft.rfftfreq(N, 1.0 / SR)
                p = sp[keep] + 1e-12
                cent = (p * frq[None, :]).sum(axis=1) / p.sum(axis=1)
                bright = float(np.mean(cent))

    db = 20 * np.log10(env + 1e-12)
    ref_db = np.percentile(db, 95)
    p5, p95 = np.percentile(db, 5), np.percentile(db, 95)

    # breathiness: energy below 40% of the running peak, on voiced frames
    breath = 0.0
    vm = db[mask]
    if vm.size:
        thr = ref_db - 16.0
        breath = float((vm < thr).mean())

    out = {
        'file': os.path.basename(path),
        'duration_s': round(dur, 2),
        'voice_frac': round(voiced_s / dur, 4) if dur else 0.0,
        'speech_duty': round(voiced_s / dur, 4) if dur else 0.0,
        'pause_frac': round(1 - voiced_s / dur, 4) if dur else 0.0,
        'n_pauses': len(inner_s),
        'pause_mean_s': round(float(np.mean(inner_s)), 3) if inner_s else 0.0,
        'pause_p50_s': round(float(np.percentile(inner_s, 50)), 3) if inner_s else 0.0,
        'pause_p90_s': round(float(np.percentile(inner_s, 90)), 3) if inner_s else 0.0,
        'pause_max_s': round(float(np.max(inner_s)), 3) if inner_s else 0.0,
        'syllable_nuclei': n_syl,
        'syllable_rate_per_s': round(syl_rate, 3),
        'f0_median_hz': round(float(np.median(f0v)), 1) if f0v.size else 0.0,
        'f0_p10_hz': round(float(np.percentile(f0v, 10)), 1) if f0v.size else 0.0,
        'f0_p90_hz': round(float(np.percentile(f0v, 90)), 1) if f0v.size else 0.0,
        'f0_iqr_hz': round(float(np.percentile(f0v, 75) - np.percentile(f0v, 25)), 1) if f0v.size else 0.0,
        'spectral_centroid_hz': round(bright, 1),
        'energy_dyn_db': round(float(p95 - p5), 1),
        'breath_ratio': round(breath, 4),
    }
    if f0v.size:
        # pitch movement rate, scale-free: how many semitones traversed per second
        span = np.log2(max(f0v.max(), 1e-6) / max(np.median(f0v), 1e-6)) * 12
        out['f0_span_semitones'] = round(float(span), 2)
        out['f0_move_per_s'] = round(float(span / max(dur, 1e-6)), 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('wavs', nargs='+')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    rows = []
    for w in a.wavs:
        if not os.path.exists(w):
            print('missing: %s' % w, file=sys.stderr)
            continue
        rows.append(analyse(w))
    if a.json:
        print(json.dumps(rows, indent=1))
    else:
        keys = [k for k in rows[0] if k != 'file'] if rows else []
        print('%-26s %s' % ('metric', ' '.join('%-16s' % r['file'][:16] for r in rows)))
        for k in keys:
            print('%-26s %s' % (k, ' '.join('%-16s' % r[k] for r in rows)))


if __name__ == '__main__':
    main()
