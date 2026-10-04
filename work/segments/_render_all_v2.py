# _render_all_v2.py -- re-render every v2 segment, ONE AT A TIME.
#
# Memory matters here. Two chatterbox TTS workers at ~2.6GB each is what got
# the whole session reaped once. Frame rendering is a single python proc piping
# rawvideo into one ffmpeg, so running the segments SEQUENTIALLY keeps peak
# memory at one render's worth instead of N.
#
#   python _render_all_v2.py                # all 10, render+mux
#   python _render_all_v2.py psoj3185       # just one
#   python _render_all_v2.py --silent-only  # skip the audio mux

import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Same order as _assemble_v2.py.
ORDER = ['tres2b', 'wasp17b', 'wasp127b', 'gliese436b', 'ltt9779b',
         'fomalhautb', 'psrb1257', 'koi55', 'kelt9b', 'psoj3185']


def have(seg, *files):
    return all(os.path.exists(os.path.join(HERE, seg, f)) for f in files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('segs', nargs='*')
    ap.add_argument('--silent-only', action='store_true')
    a = ap.parse_args()
    targets = a.segs or ORDER

    t0 = time.time()
    for i, seg in enumerate(targets):
        if not have(seg, '_cards_v2.py', 'v2_beats.json', 'v2_alignment.json',
                    'v2_audio.wav'):
            print('[%d/%d] SKIP %s (missing cards/beats/alignment/audio)'
                  % (i + 1, len(targets), seg), flush=True)
            continue
        cmd = [sys.executable, os.path.join(HERE, '_v2_frames.py'), '--seg', seg]
        if a.silent_only:
            cmd.append('--silent-only')
        print('[%d/%d] render %s ...' % (i + 1, len(targets), seg), flush=True)
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            print('  FAILED rc=%s' % rc, flush=True)
            continue
        print('  done (%.0fs elapsed)' % (time.time() - t0), flush=True)
    print('all renders complete in %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
