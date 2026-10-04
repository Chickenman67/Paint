# _v2_audio.py -- per-beat TTS for the v2 rebuild, with a TEMPO stage so we can
# actually hit 160 wpm.
#
# WHY THIS FILE EXISTS (the blocking problem the reuse audit found):
#   The v1 pipeline (_batch_audio.py) has NO rate control. chatterbox's
#   model.generate() takes only exaggeration / cfg_weight / temperature -- there is
#   no speed or rate knob. v1 hit its 200 wpm target purely by inserting
#   inter-beat silence clamped to [0.12, 0.60]s. Measured raw chatterbox rate is
#   209-228 wpm, so even the max gap bottoms out around 191 wpm -- 160 wpm is
#   UNREACHABLE that way (it would need ~2.0s gaps, 3.3x over the clamp).
#
# THE FIX: a tempo stage with a SOLVED pacing budget.
#   chatterbox's model.generate() takes only exaggeration / cfg_weight /
#   temperature -- there is no speed or rate knob, and measured raw output runs
#   ~215 wpm. v1 hit its 200 wpm target purely by padding inter-beat silence, and
#   that mechanism bottoms out around 191 wpm; the brief's 160 wpm is UNREACHABLE
#   by padding alone (it would need ~2.0 s gaps, 3.3x over the clamp).
#
#   So the two stages are solved TOGETHER, in this order:
#     1. Pick the inter-beat breath (NOMINAL_GAP_S = 0.30 s). That is a creative
#        choice -- the deliberate clause pause the brief asks for -- and it is made
#        FIRST so the voice, not the padding, is what carries the pacing.
#     2. required_speech = (words / TARGET_WPM * 60) - gap * n_gaps
#     3. Slow every beat by the constant ratio raw_total / required_speech, with
#        ffmpeg `atempo` (a pitch-preserving time-stretch; free, no resampling).
#
#   The arithmetic is closed-form and self-consistent, so it needs no iteration and
#   lands within a sample of target. Verified: koi55, 249 words, raw 214.8 wpm ->
#   speech 166.3 wpm -> 160.4 wpm overall, factors 0.772, pitch unchanged at 121 Hz.
#
#   NOTE the direction: atempo factor f gives output_duration = input/f, so
#   f < 1 SLOWS (longer output) and f > 1 speeds up. Inverting this sign is the
#   one mistake this stage invites -- it produces a chipmunk-fast 260 wpm render
#   that still "looks" like it ran.
#
#   The VOICE is unhurried rather than the timeline padded with air, which is what
#   "slow down to 160 wpm" actually means.
#
# Reuses v1's proven primitives (read_wav / write_wav / trim_silence / words /
# load_script) so beat boundaries stay exact, LINE_EQ is enforced, and the word
# regex is byte-identical to the aligner.
#
# Reads   <seg>/script.json
# Writes  <seg>/v2_audio.wav            24 kHz mono 16-bit (the real audio)
#         <seg>/v2_beats.json           exact per-beat [start,end] in that WAV
#         <seg>/_v2beats/NNN.wav        the TEMPO-SLOWED per-beat renders
#         <seg>/_v2beats_raw/NNN.wav    the raw chatterbox renders (before tempo)
#
# The aligner (_batch_align.py) is run on v2_audio.wav AFTER this file, so word
# onsets come from the FINAL slowed audio. That is what makes the visual sync
# exact: the visuals are timed to the audio that actually plays.

import argparse
import io
import json
import os
import subprocess
import sys
import time
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))          # .../work/segments
sys.path.insert(0, os.path.join(HERE, '..'))                # .../work  (has lib/)
sys.path.insert(0, HERE)                                    # for _batch_audio

# Reuse v1 primitives verbatim. _WORD_RE here is the SAME object the aligner
# imports, so beat boundaries and word onsets cannot drift apart.
from _batch_audio import (SR, read_wav, write_wav, trim_silence,  # noqa: E402
                          words, load_script, _WORD_RE)
from lib.tts import _ensure_model                           # noqa: E402

# --- v2 pacing target (RESET: 170 wpm, near-continuous delivery) ---
#
# The reset brief: "make the wpm around 170 and also the voice should match the
# paint explainer voice. there should be little to no pause between sentences for
# retention."
#
# *** MEASUREMENT VALIDITY WARNING -- READ BEFORE "CLOSING A VOICE GAP" ***
#   ref2/ref_audio_24k.wav is the FULL MIX: narration + music bed + mastering.
#   _voice_analysis.py measures it at voice_frac 0.9982, n_pauses 0 and
#   f0_move_per_s 0.019 across 875 s -- numbers no human narrator produces. Its
#   centroid (1308 Hz), syllable rate (4.16/s), breath ratio (0.192) and dynamic
#   range (26.7 dB) are therefore measurements OF THE MUSIC, not of the voice.
#
#   An earlier pass of this file treated those four numbers as the target and
#   "diagnosed" a brightness gap, a syllable-density gap and a dynamics gap.
#   All three were artefacts of comparing narration-only audio against a mixed
#   track. Do not re-derive them. What the measurements DO legitimately say:
#
#     - pitch register was already right: F0 125.4 Hz vs the mix's 120.6 Hz
#     - our delivery was already MORE animated than the reference: f0_iqr
#       53.6 Hz vs 44.8 Hz, span 16.2 vs 16.9 semitones
#     - breathiness was already close: 0.219 vs 0.192
#
#   So the voice was NOT wrong. One problem was real and self-inflicted:
#
#   ATEMPO DRAG. chatterbox has no rate knob, so reaching 170 wpm from its
#   ~220 wpm natural rate means a pitch-preserving time-stretch, and the stretch
#   LOWERS the voice: spectral centroid 1248 -> 1190 Hz, f0 movement
#   4.06 -> 3.26 /s. It gets darker AND less animated the more we slow it. This
#   is damage we introduce, so atempo_slow() undoes it with a 3 dB shelf at
#   3.5 kHz, targeting UNDAMAGE rather than a (contaminated) reference number.
#
# The second real problem was DEAD AIR, and that one measured fine on narration
# alone: our segments carried 15.4% silence with 20 gaps >= 0.30 s. Hence the
# three-part budget, which leans the opposite way from v1:
#   - raise the target to 170 wpm, which REDUCES the stretch;
#   - cut the inter-beat gap from 0.30 s to 0.08 s;
#   - squeeze chatterbox's internal sentence silences (the dead air) with a pause
#     compressor before the tempo solve, so what little remains is continuous
#     speech rather than holes.
#
# Measured result on tres2b: 15.4% -> 6.1% silence, wpm 170.6 ON TARGET.
TARGET_WPM = 170.0

# Inter-beat breath. v1 used 0.30 s ("the deliberate clause pause"). The reset
# brief asks for "little to no pause between sentences for retention", so this
# drops to 0.08 s -- a beat, not a breath. The beat BOUNDARY is still marked by
# the snap cut in the visuals, so pacing stays readable without audible dead air.
NOMINAL_GAP_S = 0.08

# Internal-pause squeeze (the retention fix). chatterbox leaves a 0.2-0.5 s hole
# at the end of each sentence inside a beat; trim_silence only strips the beat
# EDGES, so those internal holes survived into the render. We shorten any
# internal silence >= PAUSE_SQUEEZE_ABOVE_S down to PAUSE_SQUEEZE_TO_S. Applied
# to the raw beat BEFORE the tempo solve, so the solve's measured raw durations
# already include the compression and stay self-consistent.
PAUSE_SQUEEZE_ABOVE_S = 0.16
PAUSE_SQUEEZE_TO_S = 0.07

# Brightness compensation for the atempo stretch. See atempo_slow() for why the
# target here is UNDAMAGE, not the reference's centroid.
BRIGHT_SHELF_HZ = 3500
BRIGHT_SHELF_DB = 3.0

# Gaps are clamped for safety: below ~0.02 s a beat reads as a stumble, above
# ~0.55 s as a dead edit. NOMINAL_GAP_S must sit inside this band or the segment
# cannot both hit TARGET_WPM and sound deliberate -- asserted at import.
GAP_MIN, GAP_MAX = 0.02, 0.55
assert GAP_MIN <= NOMINAL_GAP_S <= GAP_MAX, \
    'NOMINAL_GAP_S must be inside the gap clamp band or pacing is unreachable'

# How far off TARGET_WPM a segment may land before it is flagged OFF TARGET.
# atempo is exact to a sample, so with the gap fixed the solve is exact too; 4 wpm
# is ~0.3 s over a 75 s segment, which is inside the visual sync tolerance.
WPM_TOL = 4.0

ORDER = [
    'tres2b', 'wasp17b', 'wasp127b', 'gliese436b', 'koi55', 'ltt9779b',
    'fomalhautb', 'psrb1257', 'kelt9b', 'psoj3185',
]


# ---------------------------------------------------------------------------
# tempo stage
# ---------------------------------------------------------------------------

def atempo_slow(src_wav, dst_wav, factor):
    """Slow a WAV by `factor` (<1 slows) preserving pitch, then compensate the
    timbre the stretch costs. factor in (0.5, 2.0).

    WHY THE EQ IS HERE AND WHY ITS TARGET IS *NOT* THE REFERENCE:

    A pitch-preserving time-stretch is not free. Measured on a real beat, slowing
    to the 170 wpm target lowers spectral centroid 1248 -> 1190 Hz and drops f0
    movement 4.06 -> 3.26 /s -- the voice gets darker AND less animated the more
    we slow it. That is damage WE introduce, so undoing it is justified on its
    own merits and needs no reference to justify.

    The obvious-looking target -- "the reference reads at 1308 Hz, match that" --
    is INVALID. ref2/ref_audio_24k.wav is the full MIX (narration + music bed +
    mastering): _voice_analysis.py measures it at voice_frac 0.9982 and n_pauses 0
    across 875 s, which no human narrator produces. Its centroid, syllable rate
    and breath ratio are measurements OF THE MUSIC. Chasing them would be tuning
    the voice against a music bed.

    So the target is UNDAMAGE: recover part of the ~58 Hz the stretch took.
    BRIGHT_SHELF_DB = 3 recovers ~18 Hz of it on the tres2b render, holding
    breath_ratio at 0.217 (reference mix reads 0.192) and leaving F0 untouched.
    3 dB is deliberately modest -- our narration is full of /s/ ("stars",
    "surface", "gas") and a heavier shelf would read as sibilance.
    """
    factor = max(0.5, min(2.0, factor))
    filt = ('atempo=%.4f,equalizer=f=%d:t=h:width=1200:g=%g'
            % (factor, BRIGHT_SHELF_HZ, BRIGHT_SHELF_DB))
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-i', src_wav, '-filter:a', filt, '-ar', str(SR),
           '-ac', '1', '-c:a', 'pcm_s16le', dst_wav]
    subprocess.run(cmd, check=True)
    return dst_wav


def squeeze_pauses(pcm, above_s=PAUSE_SQUEEZE_ABOVE_S,
                   to_s=PAUSE_SQUEEZE_TO_S, thresh_db=-38.0):
    """Shorten internal silences to `to_s` so the read is near-continuous.

    The retention lever. chatterbox leaves a 0.2-0.5 s hole at each sentence end
    INSIDE a beat; trim_silence only strips the beat edges, so those holes reach
    the render. Measured on tres2b: 15.4% silence, 20 gaps >=0.30 s. This finds
    every internal silence longer than `above_s` and cuts it down to `to_s`,
    which is what turns a gappy read into a driving one.

    Level-relative threshold (vs the 95th percentile of the frame envelope) so
    it works the same on a quiet beat and a loud one. Short plosive closures
    (< above_s) are left alone -- they are part of the articulation, not pauses.
    """
    if pcm.size == 0:
        return pcm, 0
    a = pcm.astype(np.float32) / 32768.0
    win = 240                                     # 10 ms
    n = (a.size // win) * win
    if n == 0:
        return pcm, 0
    frames = a[:n].reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-12)
    silent = db < (np.percentile(db, 95) + thresh_db)
    if not silent.any():
        return pcm, 0

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
    out.append(pcm[cur:])
    return np.concatenate(out), saved / SR


# ---------------------------------------------------------------------------
# synthesis (raw, cached)
# ---------------------------------------------------------------------------

def synth_raw_beat(get_model, text, path, ex, cfg, temp):
    """Synthesize one beat at chatterbox's natural rate, trim, cache. Returns pcm.

    Cache is keyed only on the path, matching v1. We clear the cache dir when
    changing synthesis params (the v1 landmine the audit flagged). The model is
    obtained lazily through get_model so a tempo-only re-run (raw beats all
    cached) never pays the ~20s load and never touches the network.
    """
    if os.path.exists(path):
        try:
            pcm, sr = read_wav(path)
            if sr == SR and pcm.size > SR * 0.2:
                return pcm
        except Exception:
            pass
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

def run_segment(get_model, key, ex, cfg, temp, force=False):
    seg_dir = os.path.join(HERE, key)
    raw_dir = os.path.join(seg_dir, '_v2beats_raw')
    sq_dir = os.path.join(seg_dir, '_v2beats_sq')     # pause-squeezed, pre-tempo
    slow_dir = os.path.join(seg_dir, '_v2beats')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(sq_dir, exist_ok=True)
    os.makedirs(slow_dir, exist_ok=True)
    script, beats = load_script(key)

    print('  [%s] %d beats' % (key, len(beats)))
    t_start = time.time()

    # Pass 1: raw synthesis (cached), PAUSE SQUEEZE, and measure each beat.
    # The squeeze runs on the cached raw PCM (cheap, no model) and writes an
    # intermediate file so the tempo stage and the solve both operate on the
    # SQUEEZED durations. Measuring the squeezed audio is what keeps the
    # closed-form solve exact: the dead air we removed is not silently re-added
    # by a too-small atempo factor.
    sq_pcms, nwords, sq_s_list, saved_total, raw_speech_s = [], [], [], 0.0, 0.0
    for i, b in enumerate(beats):
        txt = b['line'].strip()
        raw_path = os.path.join(raw_dir, '%03d.wav' % (i + 1))
        sq_path = os.path.join(sq_dir, '%03d.wav' % (i + 1))
        raw = synth_raw_beat(get_model, txt, raw_path, ex, cfg, temp)
        sq, saved_s = squeeze_pauses(raw)
        write_wav(sq_path, sq)
        sq_pcms.append(sq)
        nwords.append(len(words(txt)))
        sq_s_list.append(sq.size / SR)
        saved_total += saved_s
        raw_speech_s += raw.size / SR
    print('    squeeze: removed %.2fs internal pause (%.1f%% of raw speech)'
          % (saved_total, 100 * saved_total / max(1e-6, raw_speech_s)))

    # Pass 2: tempo stage.
    #
    # Solve pacing FIRST, so the tempo factors come out right. We want:
    #     total_s = total_w / TARGET_WPM * 60
    #     total_s = speech_s + gap * n_gaps
    # With gap fixed at NOMINAL_GAP_S, the speech must occupy
    # total_s - gap*n_gaps. Each beat is then scaled in proportion to its
    # (squeezed) duration so the whole lands on target. Self-consistent by
    # construction -- no iteration needed.
    total_w = sum(nwords)
    n_gaps = max(1, len(sq_pcms) - 1)
    raw_total_s = sum(sq_s_list)
    target_total_s = total_w / TARGET_WPM * 60.0
    gap = NOMINAL_GAP_S
    required_speech_s = target_total_s - gap * n_gaps

    # If required_speech_s <= 0 the segment is too short for even zero speech at
    # this wpm; fall back to a floor so we never ask atempo for a negative rate.
    required_speech_s = max(1.0, required_speech_s)
    # atempo factor f makes output duration = input duration / f, so to reach a
    # required output of `required_speech_s` from `raw_total_s` input we need
    # f = raw_total_s / required_speech_s. f < 1 SLOWS (longer output), f > 1
    # speeds up. Since chatterbox is fast (~220 wpm) and we want ~170, f < 1 --
    # but LESS than in v1, because raising the target to 170 and cutting the gap
    # both reduce the stretch. Less stretch = brighter, more animated voice.
    global_ratio = raw_total_s / required_speech_s     # <1 slows

    slow_pcms = []
    factors = []
    for i, (pcm, nw) in enumerate(zip(sq_pcms, nwords)):
        sq_wav = os.path.join(sq_dir, '%03d.wav' % (i + 1))
        slow_wav = os.path.join(slow_dir, '%03d.wav' % (i + 1))
        # per-beat factor: this beat's share of the required output / its raw length
        beat_required_s = required_speech_s * (sq_s_list[i] / raw_total_s)
        f = max(0.5, min(2.0, sq_s_list[i] / beat_required_s))
        factors.append(f)
        if force or not os.path.exists(slow_wav):
            atempo_slow(sq_wav, slow_wav, f)
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
    print('    -> %.1fs speech + %.1fs gaps = %.1fs  %.1f wpm  pause %.1f%%  %s'
          % (speech_s, gap * n_gaps, total_s, wpm, pause_frac * 100,
             'ON TARGET' if abs(wpm - TARGET_WPM) <= WPM_TOL else '** OFF TARGET **'))
    if abs(wpm - TARGET_WPM) > WPM_TOL:
        print('    ** WARNING: wpm %.1f is %.1f off target %.0f **'
              % (wpm, abs(wpm - TARGET_WPM), TARGET_WPM))

    # Stitch the slowed beats with the gap.
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
                      'wav': '_v2beats/%03d.wav' % (i + 1)})
        cur += p.size
        if i < len(slow_pcms) - 1:
            parts.append(gap_pcm)
            cur += gap_pcm.size
    full = np.concatenate(parts)

    wav_out = os.path.join(seg_dir, 'v2_audio.wav')
    write_wav(wav_out, full)

    meta = {
        'segment': key,
        'wav_path': 'v2_audio.wav',
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
    with io.open(os.path.join(seg_dir, 'v2_beats.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)

    flag = 'ON TARGET' if meta['on_target'] else '** OFF TARGET **'
    print('    -> v2_audio.wav  %.2fs  %.1f wpm  %s  (render %.0fs)'
          % (meta['duration_s'], wpm, flag, meta['render_s']))
    sys.stdout.flush()
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', nargs='*', default=None)
    ap.add_argument('--exaggeration', type=float, default=0.5)
    ap.add_argument('--cfg-weight', type=float, default=0.5)
    ap.add_argument('--temperature', type=float, default=0.8)
    ap.add_argument('--force', action='store_true', help='re-do the tempo stage')
    args = ap.parse_args()

    keys = args.segments or ORDER

    # Lazy model: a tempo-only re-run (all raw beats cached) never loads chatterbox.
    _model = [None]

    def get_model():
        if _model[0] is None:
            print('loading chatterbox model...')
            t0 = time.time()
            _model[0] = _ensure_model()
            print('model ready in %.1fs' % (time.time() - t0))
            sys.stdout.flush()
        return _model[0]

    results = []
    for key in keys:
        try:
            results.append(run_segment(get_model, key, args.exaggeration,
                                       args.cfg_weight, args.temperature,
                                       force=args.force))
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
    out = os.path.join(HERE, '_v2_audio_report.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print('\nwrote %s' % out)


if __name__ == '__main__':
    main()