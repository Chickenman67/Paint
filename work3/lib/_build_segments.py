"""Render + mux every bunkers chapter to segments/<name>/segment.mp4.

Run AFTER `python lib/_coverage_gate.py` (window + render pass) and after the
determinism baselines are recorded. For each chapter this:

  1. builds the scene (so a crash is loud here rather than in ffmpeg),
  2. renders the silent video at fps (60),
  3. muxes silent video + audio.wav with -c:v copy / -c:a aac,
  4. verifies BOTH stream durations against the beats timeline.

The mux step is CLAUDE.md 9.2: audio MUST be re-encoded. With -c copy on both
streams every input's audio starts at PTS 0 and is not rebased onto a running
timeline, so the assembled audio timestamps come wrong while nb_frames still
reads correct -- the symptom is deceptive and cost a full assembly once.

    python lib/_build_segments.py                # all nine
    python lib/_build_segments.py pinegap vatican
    python lib/_build_segments.py --fps 30       # faster draft pass
"""

import importlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), 'work', 'lib'))

import scene_common as SC     # noqa: E402

# Chapter order is the FILM order -- this is the sequence the video plays.
CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']


def stream_duration(path, stream):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream,
                        '-show_entries', 'stream=duration',
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return -1.0


def build(chapter, fps):
    seg_dir = os.path.join(ROOT, 'segments', chapter)
    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    silent = os.path.join(seg_dir, '_silent.mp4')
    SC.render_video(scene, silent, fps=fps)
    SC.mux(seg_dir, fps=fps)
    out = os.path.join(seg_dir, 'segment.mp4')
    v, a = stream_duration(out, 'v'), stream_duration(out, 'a')
    want = scene.duration
    ok = abs(v - want) < 0.35 and abs(a - want) < 0.35
    print('%-11s video %.2f  audio %.2f  want %.2f  %s'
          % (chapter, v, a, want, 'OK' if ok else 'DESYNC'))
    return ok


def main(argv):
    fps = 60
    if '--fps' in argv:
        i = argv.index('--fps')
        fps = int(argv[i + 1])
        del argv[i:i + 2]
    chaps = [a for a in argv if not a.startswith('-')] or CHAPTERS
    bad = []
    for ch in chaps:
        try:
            if not build(ch, fps):
                bad.append(ch)
        except Exception as exc:
            print('%-11s BUILD/RENDER FAILED: %s: %s'
                  % (ch, type(exc).__name__, exc))
            bad.append(ch)
    print('\n%d/%d chapters ok' % (len(chaps) - len(bad), len(chaps)))
    if bad:
        print('FAILED: ' + ', '.join(bad))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))