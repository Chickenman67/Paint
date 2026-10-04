"""Assemble the 9 chapters into the full bunkers film.

THIS IS CLAUDE.md sec 9, AND EVERY RULE IN IT EXISTS BECAUSE IT WAS LEARNED THE
EXPENSIVE WAY. Read the comments before changing any flag.

  1. A 0.5s BLACK BRIDGE between chapters. This is the palette bridge -- without
     it the tail of one chapter's palette bleeds into the head of the next.

  2. THE BRIDGES MUST CARRY AN AUDIO STREAM. An earlier build made them
     video-only and then concat'd with `-c copy` on both streams; the result read
     26.6 minutes for a 14.4 minute film. `anullsrc` at 44100/stereo, matching the
     segments, is the fix.

  3. `-c:v copy -c:a aac`. NEVER `-c copy` on BOTH. With a stream copy, every
     input's audio starts at PTS 0 and is not rebased onto a running timeline, so
     the assembled audio timestamps come out wrong. The symptom is deceptive:
     `nb_frames` (the real sample count) reads CORRECT while the stream's
     *reported duration* is nearly double, so nothing looks obviously broken.
     Re-encode audio; copy only video.

  4. VERIFY BOTH STREAMS SEPARATELY. `format=duration` reports only the longest
     stream, so a file can be internally desynced and still report a plausible
     number. This raises rather than shipping one.

  5. BACK UP BEFORE ANY FIX PASS. `guantlet2_full.pre-fixN.mp4`.

    python lib/_assemble.py              # assemble + verify
    python lib/_assemble.py --backup     # copy current full film aside first

EXPECTED RUNTIME IS ~820s (13.7 min), NOT the reference's 875.5s. The 55s
shortfall is DELIBERATE -- the user forbade padding scripts to hit a duration.
See memory runtime-short-is-intended-not-a-defect. Do not "fix" this.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASM = os.path.join(ROOT, 'assembly')

CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']

BRIDGE_S = 0.5
FPS = 60
A_RATE = 44100
A_CH = 2

OUT = os.path.join(ASM, 'bunkers_full.mp4')
# The user ruled the 5-round segment cap holds as written, and the runtime
# shortfall is intended. So there is no "must hit 916s" assertion here -- see
# point 4 in the docstring. We assert instead that both streams AGREE with each
# other and with the sum of the parts, which is the thing that can actually break.
TOL = 0.35


def stream_duration(path, stream):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream,
                        '-show_entries', 'stream=duration',
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return -1.0


def make_bridge(path):
    """0.5s black frame WITH a silent stereo audio track.

    The audio track is not decoration. A video-only input concat'd with `-c:a
    copy` was half the cause of the 26.6-minute assembly; ffmpeg has to keep the
    audio streams aligned frame-for-frame across every input.
    """
    subprocess.run([
        'ffmpeg', '-y', '-v', 'error',
        '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=%d:d=%.2f' % (FPS, BRIDGE_S),
        '-f', 'lavfi', '-i', 'anullsrc=r=%d:cl=stereo:d=%.2f' % (A_RATE, BRIDGE_S),
        '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-ar', str(A_RATE), '-ac', str(A_CH),
        path], check=True)
    return path


def verify_inputs():
    missing = [c for c in CHAPTERS
               if not os.path.exists(os.path.join(ROOT, 'segments', c,
                                                  'segment.mp4'))]
    if missing:
        print('MISSING segment.mp4 for: ' + ', '.join(missing))
        print('Run: python lib/_build_segments.py')
        return None
    total = 0.0
    for c in CHAPTERS:
        d = stream_duration(os.path.join(ROOT, 'segments', c, 'segment.mp4'), 'v')
        total += d
        print('  %-11s %7.2fs' % (c, d))
    return total


def main(argv):
    os.makedirs(ASM, exist_ok=True)

    if '--backup' in argv and os.path.exists(OUT):
        n = 1
        while os.path.exists(os.path.join(ASM, 'bunkers_full.pre-fix%d.mp4' % n)):
            n += 1
        bak = os.path.join(ASM, 'bunkers_full.pre-fix%d.mp4' % n)
        shutil.copy2(OUT, bak)
        print('backup -> %s' % bak)

    print('inputs:')
    parts_total = verify_inputs()
    if parts_total is None:
        return 1
    print('  %-11s %7.2fs  (+ %d bridges x %.1fs = %.1fs)'
          % ('TOTAL', parts_total, len(CHAPTERS) - 1, BRIDGE_S,
             (len(CHAPTERS) - 1) * BRIDGE_S))
    want = parts_total + (len(CHAPTERS) - 1) * BRIDGE_S

    # interleave: chapter, bridge, chapter, bridge, ... (no trailing bridge)
    entries = []
    for i, c in enumerate(CHAPTERS):
        entries.append(os.path.join(ROOT, 'segments', c, 'segment.mp4'))
        if i < len(CHAPTERS) - 1:
            bp = os.path.join(ASM, '_bridge%d.mp4' % i)
            make_bridge(bp)
            entries.append(bp)

    lst = os.path.join(ASM, 'concat_list.txt')
    with open(lst, 'w') as f:
        for e in entries:
            f.write("file '%s'\n" % e.replace('\\', '/').replace("'", r"'\''"))
    print('concat list -> %s (%d entries)' % (lst, len(entries)))

    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
                    '-i', lst, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-ar', str(A_RATE), '-ac', str(A_CH), OUT], check=True)
    print('assembled -> %s' % OUT)

    v, a = stream_duration(OUT, 'v'), stream_duration(OUT, 'a')
    nv = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v',
                         '-count_frames', '-show_entries',
                         'stream=nb_read_frames', '-of', 'default=nw=1:nk=1',
                         OUT], capture_output=True, text=True).stdout.strip()
    ok = True
    print('\nVERIFY')
    print('  video stream duration   %8.2fs   want %8.2fs   %+.2f'
          % (v, want, v - want))
    print('  audio stream duration   %8.2fs   want %8.2fs   %+.2f'
          % (a, want, a - want))
    print('  nb_read_frames          %8s   (= %.2fs at %dfps)'
          % (nv, (int(nv) / FPS) if nv.isdigit() else -1, FPS))
    if abs(v - want) > TOL:
        print('  FAIL: video is %.2fs off the sum of the parts' % (v - want))
        ok = False
    if abs(a - want) > TOL:
        print('  FAIL: audio is %.2fs off the sum of the parts' % (a - want))
        ok = False
    if abs(v - a) > TOL:
        print('  FAIL: video and audio disagree by %.2fs -- DESYNC' % (v - a))
        ok = False
    if ok:
        print('  OK  both streams agree with each other and with the parts.')
        print('  NOTE: %.1fs vs the reference 875.5s is the INTENDED'
              % v)
        print('        runtime, not drift. See memory'
              ' runtime-short-is-intended-not-a-defect.')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))