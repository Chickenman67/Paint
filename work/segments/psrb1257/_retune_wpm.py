"""Retune the seg3 narration rate if the stitched WAV lands outside 190-213 wpm.

Why this is separate from _make_audio_r2.py: that script prints the warning, but
the decision of *how* to retune is a pacing judgement, not a mechanical one, so it
gets its own auditable step instead of an auto-retry loop that silently burns CPU.

CLAUDE.md 2 targets 190-213 wpm to match reference pacing. The generator's
exaggeration parameter is the primary rate lever on chatterbox:

    lower exaggeration  -> flatter, slower   (this is what we want if too fast)
    higher exaggeration -> more emphatic, usually faster

Caveat worth knowing: a rate change is NOT stitch-only. Cached chunks were
synthesized at the old rate, so --restitch is required to regenerate them. Only
--silence-between-s can be changed on a cached run.

Usage:
    python _retune_wpm.py --exaggeration 0.42
    python _retune_wpm.py --check          # measure only, change nothing
"""
import argparse
import os
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

WPM_LOW, WPM_HIGH = 190, 213
WAV = os.path.join(HERE, 'round_1_audio.wav')


def measure():
    """Return (words, duration_s, wpm) for the stitched WAV, or None if absent."""
    if not os.path.exists(WAV):
        return None
    from scripts import PSRB1257_SCRIPT
    with wave.open(WAV, 'rb') as wf:
        dur = wf.getnframes() / float(wf.getframerate())
    words = len(PSRB1257_SCRIPT.strip().split())
    return words, dur, words / dur * 60.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exaggeration', type=float, default=None,
                    help='new exaggeration; forces a full --restitch re-synth')
    ap.add_argument('--silence-between-s', type=float, default=None,
                    help='re-stitch only; does NOT need to re-synthesize chunks')
    ap.add_argument('--check', action='store_true', help='measure and report only')
    args = ap.parse_args()

    if args.check or (args.exaggeration is None and args.silence_between_s is None):
        m = measure()
        if m is None:
            print(f'No WAV yet at {WAV}. Nothing to measure.')
            return
        words, dur, wpm = m
        verdict = 'IN BAND' if WPM_LOW <= wpm <= WPM_HIGH else 'OUT OF BAND'
        print(f'{words} words / {dur:.2f}s = {wpm:.1f} wpm  [{verdict}] '
              f'(target {WPM_LOW}-{WPM_HIGH})')
        if wpm > WPM_HIGH:
            # Solve for the exaggeration that would land in band. The observed
            # relationship is roughly linear in this range, so a first-order
            # estimate is enough to aim the retry; the real check is the
            # measurement after the re-synth, not this number.
            target = (WPM_LOW + WPM_HIGH) / 2.0
            print(f'  too fast. Aim for ~{target:.0f} wpm, i.e. slow by '
                  f'{wpm / target:.2f}x. Try --exaggeration 0.42 (was 0.5).')
        elif wpm < WPM_LOW:
            print(f'  too slow. Try --exaggeration 0.56 (was 0.5).')
        return

    cmd = [sys.executable, os.path.join(HERE, '_make_audio_r2.py')]
    if args.exaggeration is not None:
        cmd += ['--exaggeration', str(args.exaggeration), '--restitch']
    if args.silence_between_s is not None:
        cmd += ['--silence-between-s', str(args.silence_between_s)]
    print('running:', ' '.join(cmd))
    subprocess.run(cmd, cwd=HERE, check=True)

    m = measure()
    if m:
        words, dur, wpm = m
        print(f'\nafter: {words} words / {dur:.2f}s = {wpm:.1f} wpm  '
              f'[{"IN BAND" if WPM_LOW <= wpm <= WPM_HIGH else "STILL OUT OF BAND"}]')


if __name__ == '__main__':
    main()
