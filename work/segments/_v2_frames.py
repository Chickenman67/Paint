# _v2_frames.py -- the v2 per-segment frame generator.
#
# REPLACES the v1 _frames.py raster-motion path. The v2 model (STYLE_CANON2 §4,
# verified against the frame-diff analysis) is: within a beat, ELEMENTS POP IN
# fully-formed one at a time on clause boundaries, then HOLD. There are no
# cross-fades, no tween verbs, no idling. This driver therefore:
#
#   1. loads the segment's v2_alignment.json (word onsets on the FINAL slowed
#      audio) and v2_beats.json (exact beat spans),
#   2. loads the card module's LAYERS: a list of (pop_time_seconds_absolute,
#      draw_fn) -- the card author declares WHEN each element appears, in terms
#      of the spoken words, and the driver composes it,
#   3. renders one composed frame per beat-time step and pipes rawvideo to
#      ffmpeg, then muxes v2_audio.wav.
#
# Timing is DERIVED FROM THE AUDIO (whisper word onsets clamped into exact beat
# spans), not predicted from word counts -- this is the CLAUDE.md §5 drift fix.
# A card's element pop time is authored as the beat-relative onset of the word
# it illustrates, so the picture changes when the narrator says the thing.

import argparse
import importlib
import io
import json
import os
import subprocess
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))                 # .../work/segments
LIB = os.path.join(HERE, '..', 'lib')
sys.path.insert(0, HERE)                                           # for _v2_audio
sys.path.insert(0, os.path.join(HERE, '..'))                       # .../work
sys.path.insert(0, LIB)

import v2engine as E          # noqa: E402
import v2draw as D            # noqa: E402
import v2type as T            # noqa: E402

W, H, FPS = T.W, T.H, T.FPS

PLANET = {
    'tres2b': 'TRES-2B', 'wasp17b': 'WASP-17B', 'wasp127b': 'WASP-127B',
    'gliese436b': 'GLIESE 436 B', 'koi55': 'KOI-55', 'ltt9779b': 'LTT 9779 B',
    'fomalhautb': 'FOMALHAUT B', 'kelt9b': 'KELT-9B', 'psoj3185': 'PSO J318.5-22',
}


def load_layer_module(seg):
    """Import <seg>/_cards_v2.py. It exposes LAYERS(seg_ctx) -> dict of
    beat_id -> list of layers, plus helpers. We just need it to return a dict."""
    seg_dir = os.path.join(HERE, seg)
    if seg_dir not in sys.path:
        sys.path.insert(0, seg_dir)
    m = importlib.import_module('_cards_v2')
    importlib.reload(m)
    return m


def build_context(seg):
    """Assemble everything a card author needs: title, beat spans, word onsets,
    and a helper to turn a spoken word into an absolute pop time."""
    seg_dir = os.path.join(HERE, seg)
    with io.open(os.path.join(seg_dir, 'script.json'), encoding='utf-8') as f:
        script = json.load(f)
    with io.open(os.path.join(seg_dir, 'v2_beats.json'), encoding='utf-8') as f:
        bmeta = json.load(f)
    with io.open(os.path.join(seg_dir, 'v2_alignment.json'), encoding='utf-8') as f:
        al = json.load(f)

    beat_by_id = {b['id']: b for b in bmeta['beats']}
    script_by_id = {b['id']: b for b in script['beats']}
    # word onsets grouped by beat
    words_by_beat = {}
    for w in al['words']:
        words_by_beat.setdefault(w['beat'], []).append(w)

    # A simple attribute bag. (A class body cannot close over the enclosing
    # function's locals for its own assignments, so we use an instance.)
    ctx = type('Ctx', (object,), {})()
    ctx.seg = seg
    ctx.title = script.get('title_short') or PLANET.get(seg, seg.upper())
    ctx.planet = PLANET.get(seg, seg.upper())
    ctx.beats = bmeta['beats']
    ctx.duration = bmeta['duration_s']
    ctx.beat_by_id = beat_by_id
    ctx.script_by_id = script_by_id
    ctx.words_by_beat = words_by_beat
    ctx.alignment = al

    def when(beat_id, word_contains, offset=0.0):
        """Absolute time when the word matching word_contains is spoken in
        this beat. Lets a card author time an element to a spoken word."""
        b = beat_by_id[beat_id]
        ws = words_by_beat.get(b['n'], [])
        for w in ws:
            if word_contains.lower() in w['w'].lower():
                return max(b['start'], w['t'] + offset)
        return b['start'] + offset        # fall back to the beat start

    def beat_start(beat_id):
        return beat_by_id[beat_id]['start']

    ctx.when = when
    ctx.beat_start = beat_start
    return ctx


def compose_segment(seg, out, verbose=True):
    """Render one v2 segment to a silent MP4 from the card module's layers."""
    Ctx = build_context(seg)
    mod = load_layer_module(seg)
    # the card module exposes build(beat_id, ctx) -> list of E.Layer, OR
    # a single LAYERS dict. We support a build(beat_id, ctx) function.
    if hasattr(mod, 'build_beat'):
        build_beat = mod.build_beat
    elif hasattr(mod, 'build'):
        build_beat = mod.build
    else:
        raise SystemExit('card module for %s has no build_beat/build' % seg)

    # Pre-compose per beat: for each beat, build its layer list ONCE (layers are
    # declared with beat-relative pop times), then render frames for the beat's
    # span. To avoid recomposing identical static frames, we render only the
    # DISTINCT frame states and duplicate frames in the pipe -- but simplest
    # correct path: render every frame. 60fps * ~93s = ~5.6k frames/segment; a
    # compose is a handful of draws, so this is fine.
    segs = []
    for b in Ctx.beats:
        layers = E.sort_layers(build_beat(b['id'], Ctx))
        segs.append({'beat': b, 'layers': layers})

    total_s = Ctx.duration
    n_frames = int(round(total_s * FPS))
    if verbose:
        print('[%s] beats=%d total=%.2fs frames=%d @%dfps'
              % (seg, len(segs), total_s, n_frames, FPS), flush=True)

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
        '-r', str(FPS), '-i', 'pipe:0', '-an',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    si, written = 0, 0
    # Precompute the start times so the frame loop can binary-search the active
    # beat. We pick the LAST beat whose START <= t -- NOT the first whose END > t.
    # The distinction is the whole 0.3s inter-beat gap: during a gap (beat N has
    # ended, beat N+1 has not begun) we must HOLD beat N's finished card, not
    # advance to beat N+1 with a negative beat-relative time (which draws a blank
    # white page -> a 0.3s white flash at EVERY beat boundary, ~90 times per film).
    starts = [s['beat']['start'] for s in segs]
    import bisect
    try:
        for fi in range(n_frames):
            t = fi / FPS
            # last index with starts[idx] <= t  (holds the previous beat in a gap)
            si = max(0, bisect.bisect_right(starts, t) - 1)
            # beat-relative time for this frame
            tb = t - starts[si]
            img = E.compose(segs[si]['layers'], tb, title=Ctx.title,
                            title_seed=abs(hash(seg)) % 100000)
            proc.stdin.write(img.tobytes())
            written += 1
            if verbose and written % 1200 == 0:
                el = time.time() - t_start
                print('  %d/%d  %.0f fps' % (written, n_frames,
                                              written / max(0.001, el)), flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise SystemExit('ffmpeg failed rc=%s' % proc.returncode)
    if verbose:
        el = time.time() - t_start
        print('[%s] wrote %s: %d frames in %.1fs (%.0f fps)'
              % (seg, os.path.basename(out), written, el,
                 written / max(0.001, el)), flush=True)
    return out


def mux_audio(seg, silent, out):
    """Mux v2_audio.wav onto the silent video. Audio is re-encoded (never -c
    copy) -- see STYLE_CANON2 §9 / memory concat-stream-mismatch-inflates-audio."""
    seg_dir = os.path.join(HERE, seg)
    wav = os.path.join(seg_dir, 'v2_audio.wav')
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
           '-i', silent, '-i', wav,
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
           '-ar', '44100', '-ac', '2', '-shortest', out]
    subprocess.run(cmd, check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--silent-only', action='store_true')
    args = ap.parse_args()
    seg = args.seg
    seg_dir = os.path.join(HERE, seg)
    out = args.out or os.path.join(seg_dir, 'v2_segment.mp4')
    silent = os.path.join(seg_dir, 'v2_silent.mp4')
    compose_segment(seg, silent)
    if not args.silent_only:
        mux_audio(seg, silent, out)
        print('[%s] muxed -> %s' % (seg, out))


if __name__ == '__main__':
    main()
