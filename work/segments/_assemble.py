# _assemble.py -- concatenate the 12 segment MP4s with white bridges into the
# final ~15-minute video.
#
# Per lib/transition.py and the measured reference, the inter-segment bridge is
# a ~3.75 s WHITE sequence (1.0 s fade to white, 2.25 s hold, 0.5 s fade out),
# NOT CLAUDE.md §5.7's "0.5 s black frame" -- the reference uses white, so we do.
# 12 segments -> 11 bridges.
#
# Segment -> MP4 mapping is EXPLICIT below rather than globbed, so a missing or
# stale file is a loud error and CLAUDE.md §10.10 (assembly not rebuilt after a
# fix) cannot happen silently. Each entry names the exact round that "won".
#
# USAGE:
#   python _assemble.py                       # build the full assembly
#   python _assemble.py --dry-run             # report the plan, touch nothing
#   python _assemble.py --segments tres2b ... # only these (partial, for review)

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))       # .../work/segments
ASM = os.path.join(HERE, '..', 'assembly')              # .../work/assembly
W, H, FPS = 1280, 720, 30

# The order of the 12 segments, and the exact MP4 filename that "won" each.
# Segments 1-2 were capped and flagged; 3 is round_2_v2; 4-12 are round_1.
SEGMENTS = [
    ('hd188753',   'round_6.mp4'),        # 1  won_by_cap_flagged (6 rounds)
    ('hd80606',    'round_6.mp4'),        # 2  won_by_cap_flagged (6 rounds)
    ('psrb1257',   'round_2_v2.mp4'),     # 3  won_round2
    ('tres2b',     'round_1.mp4'),        # 4
    ('wasp17b',    'round_1.mp4'),        # 5
    ('wasp127b',   'round_1.mp4'),        # 6
    ('gliese436b', 'round_2.mp4'),        # 7  round_2: frame-fill fix (critic p05)
    ('koi55',      'round_1.mp4'),        # 8
    ('ltt9779b',   'round_1.mp4'),        # 9
    ('fomalhautb', 'round_2.mp4'),        # 10 round_2: frame-fill fix (critic p07)
    ('kelt9b',     'round_1.mp4'),        # 11
    ('psoj3185',   'round_1.mp4'),        # 12
]

# Duration of the held white bridge segment that separates two planets. The
# full bridge is fade-in + hold + fade-out; for a concat we render it as a
# standalone white clip of TOTAL_BRIDGE seconds (the fades read fine against the
# hard cuts on either side and keep the concat a pure -c copy).
BRIDGE_S = 3.75


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration', '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return None


def make_white_bridge(out_path, dur=BRIDGE_S, fps=FPS):
    """A blank white MP4 of `dur` seconds, silent.

    THE BRIDGE MUST CARRY AN AUDIO STREAM. This function used to build a
    video-only clip (`-f lavfi -i color=...` with no audio input), and the
    concat demuxer silently mis-handled that: the first assembly produced a file
    whose VIDEO stream was correct at 867.08s but whose AUDIO stream ran to
    1593.31s. Video-only entries interleaved with audio-bearing segments make
    ffmpeg insert silence and advance the audio timeline by much more than the
    clip is long, so `format=duration` (which reports the longest stream) read
    26.6 minutes for a 14.4-minute film.

    Every segment is aac / 44100 / stereo, so the bridges are built to match
    exactly: a silent anullsrc source at the same rate and channel count. The
    `-shortest` guard keeps the two streams from drifting apart by a frame.
    """
    n = int(round(dur * fps))
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-f', 'lavfi', '-i', f'color=c=white:s=%dx%d:r=%d' % (W, H, fps),
           '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
           '-t', '%.3f' % dur, '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
           '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
           '-shortest', out_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def normalize_audio(src, dst, fps=FPS):
    """Copy video, re-encode audio to 44100 Hz stereo AAC.

    Every concat input passes through here so the whole list shares one audio
    format. See the call site for why that matters.
    """
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', src,
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100',
           '-ac', '2', dst]
    subprocess.run(cmd, check=True, capture_output=True)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--segments', nargs='*', default=None)
    ap.add_argument('--out', default='guantlet2_full.mp4')
    args = ap.parse_args()

    segs = SEGMENTS
    if args.segments:
        keep = set(args.segments)
        segs = [s for s in SEGMENTS if s[0] in keep]
        segs.sort(key=lambda s: [k for k, _ in SEGMENTS].index(s[0]))

    os.makedirs(ASM, exist_ok=True)
    missing = []
    plan = []
    for key, fname in segs:
        p = os.path.join(HERE, key, fname)
        if not os.path.exists(p):
            # fall back to any round_*.mp4 so a partial build still assembles,
            # but SAY so loudly -- silent fallback is how a stale segment ships.
            import glob
            alts = sorted(glob.glob(os.path.join(HERE, key, 'round_*.mp4')))
            alts = [a for a in alts if 'silent' not in a and 'pre-' not in a]
            if alts:
                print('  [%s] MISSING %s -- falling back to %s'
                      % (key, fname, os.path.basename(alts[-1])))
                p = alts[-1]
            else:
                missing.append(key)
                continue
        d = probe(p)
        plan.append((key, p, d))
        print('  [%s] %-18s %s  %.2fs' % (key, os.path.basename(p), 'OK', d or -1))

    if missing:
        sys.exit('MISSING segments with no fallback: %s' % ', '.join(missing))

    total = sum(d for _, _, d in plan) + BRIDGE_S * (len(plan) - 1)
    print('\nplan: %d segments + %d bridges = %.1fs (%.1f min)'
          % (len(plan), len(plan) - 1, total, total / 60.0))
    if args.dry_run:
        print('dry run - nothing written')
        return

    # Build the bridge files and the concat list.
    #
    # EVERY INPUT IS NORMALIZED to 44100 Hz stereo AAC first. The two capped
    # legacy segments (hd188753, hd80606) were muxed back when the narration
    # WAVs were still 24 kHz mono, so their audio is aac/24000/1 while the ten
    # newer segments are aac/44100/2. The concat demuxer does not reconcile
    # mismatched audio formats across entries: it hits the first format change,
    # loses the running timeline, and emits a storm of "Non-monotonic DTS"
    # until ffmpeg aborts with exit 69 -- or, with `-c copy`, silently ships a
    # file whose audio runs to 1592.97s against 866.90s of video. Normalizing
    # every input to the same rate/channels removes the discontinuity entirely.
    norm_dir = os.path.join(ASM, 'normalized')
    os.makedirs(norm_dir, exist_ok=True)
    entries = []
    for i, (key, path, d) in enumerate(plan):
        npath = os.path.join(norm_dir, '%s.mp4' % key)
        normalize_audio(path, npath)
        entries.append(npath)
        if i < len(plan) - 1:
            bpath = os.path.join(ASM, 'bridge_%02d_%s.mp4' % (i + 1, key))
            make_white_bridge(bpath)
            entries.append(bpath)

    concat = os.path.join(ASM, 'concat_list.txt')
    with open(concat, 'w', encoding='utf-8') as f:
        for p in entries:
            f.write("file '%s'\n" % p.replace('\\', '/').replace("'", r"'\''"))

    out = os.path.join(ASM, args.out)
    # Video is copied; AUDIO IS RE-ENCODED, and that is load-bearing.
    #
    # CLAUDE.md SS9.2 says `-c copy` is fine because "ffmpeg auto-corrects" the
    # non-monotonic DTS warnings. For video it does. For audio it does not: every
    # input's audio starts at PTS 0, and stream-copy does not rebase successive
    # inputs onto a running timeline, so the audio timestamps come out wrong.
    # The symptom is deceptive -- `nb_frames` (35313 AAC packets ~= 820s of real
    # audio) is right while the stream's reported duration is 1592.97s, i.e. the
    # timestamps are wrong rather than the samples, so nothing looks obviously
    # broken until you compare the two streams. Re-encoding audio makes ffmpeg
    # re-time it against the copied video, which is correct and cheap (aac on 12
    # short clips). Copying both streams would be faster and wrong.
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-f', 'concat', '-safe', '0', '-i', concat,
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100',
           '-ac', '2', out]
    subprocess.run(cmd, check=True)
    # Report the VIDEO stream, not probe(out). `format=duration` reports the
    # longest stream, so a runaway audio track inflates it well past the real
    # running time -- printing it here is what made the broken first assembly
    # read as "26.6 min" without anything looking wrong.
    print('\nwrote %s' % out)

    verify_output(out, total)


def stream_duration(path, kind):
    """Duration of one stream ('v' or 'a') in seconds."""
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', '%s:0' % kind,
         '-show_entries', 'stream=duration', '-of', 'csv=p=0', path],
        capture_output=True, text=True, check=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return float('nan')


def verify_output(out, expected_s, tol=0.5):
    """Fail loudly if the assembled streams disagree with the plan.

    `format=duration` reports the LONGEST stream, so a file whose audio ran away
    while video stayed correct still 'looks' plausible in a quick `ffprobe`. The
    first assembly was exactly that: video 867.08s, audio 1593.31s, and the
    format-level read said 26.6 minutes. Checking each stream against the plan is
    the only read that catches it.

    Returns True if both streams are within `tol` of the plan.
    """
    v = stream_duration(out, 'v')
    a = stream_duration(out, 'a')
    ok = True
    print('\nverify:')
    for kind, d in (('video', v), ('audio', a)):
        delta = d - expected_s
        good = abs(delta) <= tol
        ok = ok and good
        print('  %-5s %8.2fs   plan %8.2fs   delta %+7.2fs   %s'
              % (kind, d, expected_s, delta, 'OK' if good else 'MISMATCH'))
    if v > tol and abs(v - a) > tol:
        print('  WARNING: video and audio differ by %.2fs -- the streams are out '
              'of sync.' % (a - v))
    if not ok:
        raise SystemExit(
            'ASSEMBLY VERIFICATION FAILED. Do not ship this file. The usual '
            'cause is an input missing a stream the others have (the bridges '
            'used to be video-only, which inflated audio to 1593s while video '
            'stayed at 867s).')
    return ok


if __name__ == '__main__':
    main()
