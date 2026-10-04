# _mux.py -- mux a segment's silent video with its narration WAV.
#
# Generalizes seg 3's _mux_r2.py. Encodes audio to AAC and copies video. The
# duration check (>50ms) is the guard that catches a frame-count bug before it
# becomes a clipped or padded narration.
#
# USAGE: python _mux.py --seg tres2b [--video round_1_silent.mp4] [--out round_1.mp4]

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def probe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def mux(seg, video, audio, out):
    for p in (video, audio):
        if not os.path.exists(p):
            sys.exit('missing input: %s' % p)
    vd, ad = probe_duration(video), probe_duration(audio)
    print('video %.3fs   audio %.3fs   delta %+.3fs' % (vd, ad, vd - ad))
    if abs(vd - ad) > 0.05:
        sys.exit('duration mismatch >50ms -- fix the frame count, not the mux')
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-i', video, '-i', audio,
           '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
           '-shortest', out]
    subprocess.run(cmd, check=True)
    print('wrote %s  (%.3fs)' % (out, probe_duration(out)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--video', default=None)
    ap.add_argument('--audio', default=None)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    d = os.path.join(HERE, args.seg)
    video = args.video or os.path.join(d, 'round_1_silent.mp4')
    audio = args.audio or os.path.join(d, 'round_1_audio.wav')
    out = args.out or os.path.join(d, 'round_1.mp4')
    mux(args.seg, video, audio, out)


if __name__ == '__main__':
    main()
