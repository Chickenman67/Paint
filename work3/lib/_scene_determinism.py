"""Cross-process render determinism for the REAL scene, not just the engine.

`_determinism_probe.py` builds its own toy scene, so it proves `engine3` is
deterministic but says nothing about the drawing layer. After the painterly
rewrite every fill goes through seeded fbm noise in `v2paint.py`, which is
exactly where an unseeded `random.random()` or a cached-module-level RNG would
slip in and make frame N differ between renders.

So render the actual tres2b scene at several timestamps, in a fresh process,
twice, and compare digests. Nonzero exit names the first frame that differs.

Usage:  python lib/_scene_determinism.py tres2b
"""

import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'work', 'lib'))

# Round 4 note: extended to cover the beats whose drawing code was rewritten
# this round -- the star swell, the atmosphere tail, and the finale close-up.
# The probe used to stop at 66.0, which never rendered `atmosphere_tail` or the
# big `draw_head` face, so it could not catch a determinism regression in the
# exact code we touched.
TIMES = [2.0, 12.0, 19.0, 25.0, 33.0, 40.5, 45.0, 50.0, 60.0, 66.0,
         69.50, 71.50]


def render_all(seg):
    import importlib
    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % seg)
    from engine3 import render_frame
    scene = mod.build()
    return [hashlib.sha256(
                render_frame(scene, t).convert('RGB').tobytes()).hexdigest()
            for t in times_for(scene.duration)]


def times_for(duration):
    """Sample timestamps that lie INSIDE this scene's real duration.

    The probe used to carry a hard-coded TIMES list written for tres2b (ending
    at 71.5s). Every chapter has a different duration -- Pine Gap is 69.9s --
    so those times render the final card or fall off the end, and the probe
    stops testing the code we actually changed. Times are spread across the
    segment's own span.

    It then moved to 12 evenly-spread samples, which fixed the duration
    mismatch but opened a worse hole: at a chapter's real beat density, 12
    samples can skip whole beats entirely. room39 has 37 beats -- b22
    (51.8-54.0s) and b23 (54.1-56.1s) both fell between the samples at 48.7s
    and 56.8s, so edits to both of those cards produced an UNCHANGED digest.
    A determinism probe that reports "identical" for cards it never rendered
    is worse than no probe, because it looks like a pass.

    So sample EVERY beat midpoint (plus the two ends). Beat midpoints are the
    timestamps that matter -- they are where a card's own draw function is
    guaranteed to be the live one, which is exactly the code that regressed
    in room39. ~35 extra frames per chapter at ~0.6s is worth it for a gate
    that cannot lie.
    """
    try:
        import json
        # HERE is .../work3/lib, so segments/ is directly under its parent
        # (work3). ROOT is two levels up (the repo root) and is NOT where the
        # beat files live -- reaching for ROOT/segments silently falls through
        # to the 12-sample fallback, which is the exact sparse-sampling hole
        # this function exists to close.
        beats_path = os.path.join(os.path.dirname(HERE), 'segments',
                                  _CURRENT_CHAPTER, 'beats.json')
        beats = json.load(open(beats_path))['beats']
        mids = [(b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
                for b in beats]
        return sorted(set(mids + [0.0, duration]))
    except Exception as exc:
        print('  (beats sampling unavailable for %s: %s -- using 12-sample '
              'fallback)' % (_CURRENT_CHAPTER, exc), file=sys.stderr)
        n = 12
        return [duration * i / float(n - 1) for i in range(n)]


# Set by main() before times_for() is called; times_for() is a module function
# so it cannot take the chapter as an argument without threading it everywhere.
_CURRENT_CHAPTER = 'tres2b'


def main():
    seg = sys.argv[1] if len(sys.argv) > 1 else 'tres2b'
    global TIMES, _CURRENT_CHAPTER
    import importlib
    importlib.invalidate_caches()
    _CURRENT_CHAPTER = seg
    mod = importlib.import_module('%s_scene' % seg)
    TIMES = times_for(mod.build().duration)
    digests = render_all(seg)
    for t, d in zip(TIMES, digests):
        print('t=%-6s %s' % (round(t, 2), d[:16]))
    print('DIGEST %s  (%d frames)' % (hashlib.sha256(
        ''.join(digests).encode()).hexdigest(), len(digests)))


if __name__ == '__main__':
    main()