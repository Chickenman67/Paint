"""Orchestrator-side determinism probe for engine3.

Deliberately does NOT import engine3_test: that file is being edited live by the
engine subagent, so any measurement taken against it measures a moving target.
This builds its own tiny scene so the check is under my control and stable.

The contract under test (engine3 docstring, "DETERMINISM CONTRACT"):
    render_frame(scene, t) is a pure function of (scene contents, t).

Concretely that means a re-render -- in a fresh process, at a different wall
clock, with different global RNG state -- must be byte-identical. Both halves
matter: engine3's module docstring claims "no unseeded randomness anywhere in
this module", so I perturb global random/np.random around each render to prove
no draw path reaches for them.

Run:  python lib/_determinism_probe.py
Exit 0 = deterministic. Exit 1 = NOT deterministic (prints which frame differs).
"""

import hashlib
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine3  # noqa: E402


def _seeded_ink_dot(seed):
    """A draw callable that uses its seed and NOTHING global.

    Deliberately does not touch random.* or np.random.* -- the point is to
    provide a well-behaved element so a failure means the ENGINE is at fault,
    not my draw code.
    """
    rnd = random.Random(seed)

    def draw(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        cx = 200 + (seed % 5) * 180
        cy = 200 + rnd.randint(0, 120)
        r = 40 + rnd.randint(0, 20)
        pts = []
        for i in range(20):
            a = i / 20 * 6.28318
            rr = r * (1.0 + 0.06 * rnd.random())
            pts.append((cx + np.cos(a) * rr, cy + np.sin(a) * rr))
        d.line(pts + [pts[0]], fill=(20, 20, 24, 255), width=6, joint='curve')
    return draw


def _adversarial_dot(seed):
    """A draw callable that DOES reach for the global RNG.

    If the engine leaks render order or global state into pixels, this element
    is the canary. It is expected to be cached-and-stable (engine builds each
    tile once), so it must still come out identical across processes.
    """
    def draw(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        cx = random.Random(seed).randint(100, 1100)   # stable anchor
        cy = 480 + (seed % 3) * 40
        r = random.uniform(30, 50)                     # global RNG on purpose
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=(200, 60, 60, 255))
    return draw


def build_scene():
    """A scene exercising the three things that can break determinism:
    a plain reveal, a moving element, and a global-RNG draw callable."""
    els = [
        engine3.E('bg', 'bg', lambda t, w, h: ImageDraw.Draw(t).rectangle(
            [0, 0, w, h], fill=(252, 252, 250, 255)), at=0.0),
        engine3.E('dot0', 'shape', _seeded_ink_dot(0), at=0.0),
        engine3.E('dot1', 'shape', _seeded_ink_dot(1), at=0.5),
        # slides in from off-frame over 1.5s -- pure per-frame transform
        engine3.E('slide', 'shape', _seeded_ink_dot(2), at=1.0,
                  motion=[(1.0, -600.0, 0.0, 1.0, 0.0),
                          (2.5, 0.0, 0.0, 1.0, 0.0)]),
        # rotates continuously -- the other transform axis
        engine3.E('spin', 'shape', _seeded_ink_dot(3), at=3.0,
                  motion=[(3.0, 0.0, 0.0, 1.0, 0.0),
                          (6.0, 0.0, 0.0, 1.0, 90.0)]),
        engine3.E('adv', 'shape', _adversarial_dot(7), at=4.0),
        engine3.E('late', 'shape', _seeded_ink_dot(4), at=5.0),
    ]
    return engine3.Scene(els, title='PROBE', title_seed=3, duration=6.0)


def render_all(tag):
    """Render the scene, deliberately perturbing global RNG state between
    frames so any dependence on it shows up as a byte diff."""
    sc = build_scene()
    out = []
    n = sc.frame_count()
    for i in range(n):
        random.seed(i * 7919)                 # poison global RNG per frame
        np.random.seed((i * 31 + 11) % (2 ** 32))
        out.append(engine3.render_frame(sc, i / engine3.FPS))
    h = hashlib.sha256()
    for fr in out:
        h.update(fr.tobytes())
    return out, h.hexdigest()


def main():
    frames_a, ha = render_all('a')
    # Second render in the SAME process, from a fresh Scene (fresh tile cache),
    # with global RNG seeded differently beforehand.
    random.seed(123456)
    np.random.seed(654321)
    frames_b, hb = render_all('b')

    print('frames: %d' % len(frames_a))
    print('hash A (run 1, poisoned global RNG): %s' % ha)
    print('hash B (run 2, same process, fresh cache): %s' % hb)

    if ha != hb:
        for i, (x, y) in enumerate(zip(frames_a, frames_b)):
            if x.tobytes() != y.tobytes():
                print('  FAIL: first differing frame = %d (t=%.3f)'
                      % (i, i / engine3.FPS))
                break
        print('RESULT: NOT deterministic within a process')
        return 1

    print('RESULT: deterministic within a process (identical hash)')
    print('cross-process digest: %s' % ha)
    return 0


if __name__ == '__main__':
    sys.exit(main())