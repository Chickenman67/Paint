# _mux_r2.py -- segment 3 round 2: mux the silent video with the narration WAV.
#
# The audio was generated and aligned in round 1 (round_1_audio.wav, 91.0s) and
# is UNCHANGED in round 2 -- round 2 is a pure visual re-render against the same
# narration, so the same WAV is the correct track. The card schedule is derived
# from round_1_alignment.json, which is what makes the 5.1/5.3 alignment rules
# hold: no predicted timings anywhere in this segment.

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(HERE, 'round_2_silent.mp4')
AUDIO = os.path.join(HERE, 'round_1_audio.wav')
OUT = os.path.join(HERE, 'round_2.mp4')


def probe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    for p in (VIDEO, AUDIO):
        if not os.path.exists(p):
            sys.exit('missing input: %s' % p)
    vd, ad = probe_duration(VIDEO), probe_duration(AUDIO)
    print('video %.3fs   audio %.3fs   delta %+.3fs' % (vd, ad, vd - ad))
    if abs(vd - ad) > 0.05:
        sys.exit('duration mismatch >50ms -- fix the frame count, not the mux')

    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-i', VIDEO, '-i', AUDIO,
           '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'copy',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
           '-shortest', OUT]
    subprocess.run(cmd, check=True)
    print('wrote %s  (%.3fs)' % (OUT, probe_duration(OUT)))


if __name__ == '__main__':
    main()
