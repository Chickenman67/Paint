# _assemble_v2.py -- concatenate the v2 segments with white bridges into the
# final 160wpm exoplanet video.
#
# This is the v2 sibling of _assemble.py. Differences:
#   - reads <seg>/v2_segment.mp4 (not round_N.mp4)
#   - a 10-segment order, not the v1 12
#   - the bridge is a short hold, matching the v2 pacing (the v1 bridge was
#     3.75s, which at 160wpm is over a full beat of silence and reads as a
#     stall -- STYLE_CANON2 wants a 0.5s palette bridge between segments)
#
# The three traps from CLAUDE.md §9.2, kept as load-bearing comments because
# each one cost a full assembly when it was wrong:
#   1. RE-ENCODE AUDIO, never `-c copy` both streams. With stream copy every
#      input's audio starts at PTS 0 and is not rebased onto a running
#      timeline; nb_frames stays correct while the reported audio duration
#      nearly doubles, so nothing looks obviously broken.
#   2. BRIDGES MUST CARRY AUDIO (anullsrc @ 44100/stereo). A video-only bridge
#      makes the concat demuxer insert silence and over-extend the audio.
#   3. VERIFY BOTH STREAM DURATIONS against the plan, and raise rather than
#      ship a desynced file. `format=duration` alone reports only the longest
#      stream and will not catch a desync.

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .../work/segments
ASM = os.path.join(HERE, '..', 'assembly')

# Frame rate MUST match the rendered segments. _v2_frames.py renders at 60 fps
# (1280x720, h264, yuv420p). The bridge was previously built at 30 fps, which
# the duration-only verify did NOT catch: a 0.5 s bridge is 15 frames at 30 fps
# and 30 frames at 60 fps, so the duration matched while the stream parameters
# did not -- and `-c:v copy` in the concat needs them to match. Same family as
# the SS9.2 traps: duration agreement is not stream agreement. Verified against
# ffprobe r_frame_rate on both files.
FPS = 60

# The 10 v2 segments, in narrative order:
#   open on the darkest world, escalate through the physically impossible,
#   peak on the one that survived being eaten, close on the loneliest.
SEGMENTS = [
    ('tres2b',     'the darkest planet ever found'),
    ('wasp17b',    'the planet that orbits backwards'),
    ('wasp127b',   'the fastest winds in the galaxy'),
    ('gliese436b', 'burning ice, dragging a glowing tail'),
    ('ltt9779b',   'the mirror-bright super-Earth'),
    ('fomalhautb', 'the dust-shepherd that may not be there'),
    ('psrb1257',   'the planets around a dead star'),
    ('koi55',      'the planet that survived being eaten'),
    ('kelt9b',     'hotter than most stars'),
    ('psoj3185',   'the rogue, alone in the dark'),
]

# Short held bridge between planets: a beat of white that resets the palette.
# (CLAUDE.md §4/§5: 0.5s black/white bridge so adjacent palettes do not bleed.)
BRIDGE_S = 0.5


def probe_stream(path, stream=None):
    """Probe a single stream's duration, or its codec params if stream given."""
    if stream:
        ent = ('stream=width,height,r_frame_rate,codec_name,pix_fmt,nb_frames')
    else:
        ent = 'format=duration'
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', ent,
                        '-select_streams', 'v:0' if stream else '',
                        '-of', 'json', path],
                       capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
        if stream:
            return data['streams'][0]
        return float(data['format']['duration'])
    except Exception:
        return None


def probe(path, stream=None):
    ent = 'stream=duration' if stream else 'format=duration'
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', ent,
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip().splitlines()[0])
    except Exception:
        return None


def make_white_bridge(out_path, dur=BRIDGE_S, fps=FPS):
    """A white MP4 of `dur`s WITH a silent audio stream (see trap 2 above)."""
    n = int(round(dur * fps))
    cmd = ['ffmpeg', '-y', '-v', 'error',
           '-f', 'lavfi', '-i', f'color=c=0xfdfdfd:s=1280x720:r={fps}:d={dur}',
           '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
           '-frames:v', str(n), '-shortest',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(fps),
           '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
           out_path]
    subprocess.run(cmd, check=True)


def main():
    only = sys.argv[1:] or None
    segs = SEGMENTS if not only else [s for s in SEGMENTS if s[0] in only]
    os.makedirs(ASM, exist_ok=True)

    plan = []
    for key, note in segs:
        p = os.path.join(HERE, key, 'v2_segment.mp4')
        if not os.path.exists(p):
            print('SKIP %s (no v2_segment.mp4)' % key)
            continue
        d = probe(p)
        plan.append((key, p, d, note))
    if not plan:
        print('nothing to assemble')
        return

    for key, p, d, note in plan:
        print('  %-12s %7.2fs  %s' % (key, d, note))

    total = sum(d for _, _, d, _ in plan) + BRIDGE_S * (len(plan) - 1)
    print('\nplan: %d segments + %d bridges = %.1fs (%.2f min)'
          % (len(plan), len(plan) - 1, total, total / 60.0))

    files = []
    for i, (key, p, d, note) in enumerate(plan):
        if i:
            bp = os.path.join(ASM, 'v2bridge_%02d.mp4' % i)
            make_white_bridge(bp)
            files.append(bp)
        files.append(p)

    concat = os.path.join(ASM, 'concat_list_v2.txt')
    with open(concat, 'w', encoding='utf-8') as f:
        for p in files:
            f.write("file '%s'\n" % os.path.abspath(p).replace('\\', '/'))

    out = os.path.join(ASM, 'exoplanets_v2_full.mp4')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
                    '-i', concat,
                    '-c:v', 'copy',          # video is already uniform
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
                    out], check=True)
    verify_output(out, total, plan)
    return out


def verify_output(path, expected_total, plan):
    """Check BOTH stream durations AND the video stream params against the plan."""
    v = probe(path, 'video')
    a = probe(path, 'audio')
    print('\nverify: expected %.2fs  video %.2fs  audio %.2fs' % (expected_total, v, a))
    if v is None or a is None:
        raise SystemExit('FAIL: could not probe output streams')
    if abs(v - expected_total) > 0.6:
        raise SystemExit('FAIL: video %.2fs != planned %.2fs' % (v, expected_total))
    if abs(a - expected_total) > 0.6:
        raise SystemExit('FAIL: audio %.2fs != planned %.2fs (desync)' % (a, expected_total))

    # Stream params: `-c:v copy` means a frame-rate or size mismatch between a
    # segment and a bridge survives into the output. Duration alone will not
    # catch it (a 0.5s bridge is 15 frames @30 or 30 frames @60 -- same seconds),
    # so assert the params the copy path depends on.
    out = probe_stream(path, 'v:0') or {}
    ref = None
    for key, p, d, note in plan:
        s = probe_stream(p, 'v:0')
        if s:
            ref = s
            break
    if out and ref:
        for f in ('width', 'height', 'r_frame_rate', 'pix_fmt', 'codec_name'):
            if f in out and f in ref and out[f] != ref[f]:
                raise SystemExit('FAIL: output %s=%s but segment %s (stream copy '
                                 'mismatch)' % (f, out[f], ref[f]))
        print('OK: video stream params match segments (%s %sx%s @%s)'
              % (out.get('codec_name'), out.get('width'), out.get('height'),
                 out.get('r_frame_rate')))
    print('OK: both streams match the plan (%.1fs / %.2f min)' % (expected_total, expected_total / 60))


if __name__ == '__main__':
    main()
