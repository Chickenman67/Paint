"""Run the PSR B1257+12 narration at a CHOSEN setting, into a settings-tagged chunk dir.

_make_audio_r2.py already does the resumable chunked synthesis we need, but it
always writes to _chunks/ — so re-running it at a different exaggeration would
silently reuse chunks rendered at the old setting and produce a track with two
different speaking rates stitched together. This wrapper points the chunk dir at
_chunks_<tag>/ so every chunk in a track comes from one setting, and then copies
the result to round_1_audio.wav.

Usage (after _calib_tts.py reports a setting in band):
    python _run_setting.py --tag ex040 --exaggeration 0.40 --cfg-weight 0.5 --temperature 0.8
"""
import argparse
import os
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from scripts import PSRB1257_SCRIPT

WPM_LOW, WPM_HIGH = 190, 213


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True,
                    help='short settings label, e.g. ex040; names the chunk dir')
    ap.add_argument('--out', default=os.path.join(HERE, 'round_1_audio.wav'))
    ap.add_argument('--max-chunk-words', type=int, default=110)
    ap.add_argument('--silence-between-s', type=float, default=0.4)
    ap.add_argument('--exaggeration', type=float, required=True)
    ap.add_argument('--cfg-weight', type=float, default=0.5)
    ap.add_argument('--temperature', type=float, default=0.8)
    ap.add_argument('--restitch', action='store_true',
                    help='discard cached chunks for this tag and regenerate')
    args = ap.parse_args()

    chunk_dir = os.path.join(HERE, f'_chunks_{args.tag}')
    cmd = [sys.executable, os.path.join(HERE, '_make_audio_r2.py'),
           '--chunk-dir', chunk_dir,
           '--max-chunk-words', str(args.max_chunk_words),
           '--silence-between-s', str(args.silence_between_s),
           '--exaggeration', str(args.exaggeration),
           '--cfg-weight', str(args.cfg_weight),
           '--temperature', str(args.temperature)]
    if args.restitch:
        cmd.append('--restitch')
    if args.out != os.path.join(HERE, 'round_1_audio.wav'):
        cmd += ['--out', os.path.join(chunk_dir, 'stitched.wav')]

    print('running:', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=HERE)

    produced = (os.path.join(chunk_dir, 'stitched.wav')
                if args.out != os.path.join(HERE, 'round_1_audio.wav')
                else args.out)
    if produced != args.out:
        import shutil
        shutil.copyfile(produced, args.out)

    words = len(PSRB1257_SCRIPT.strip().split())
    with wave.open(args.out, 'rb') as wf:
        dur = wf.getnframes() / wf.getframerate()
        sr = wf.getframerate()
        ch, sw = wf.getnchannels(), wf.getsampwidth()
    wpm = words / dur * 60.0
    print()
    print(f'WAV      {args.out}')
    print(f'  {dur:.2f}s  {sr}Hz  {ch}ch  {sw*8}-bit  {words} words  {wpm:.1f} wpm')
    ok = WPM_LOW <= wpm <= WPM_HIGH
    print(f'  band {WPM_LOW}-{WPM_HIGH}: {"IN BAND" if ok else "OUT OF BAND"}')


if __name__ == '__main__':
    main()
