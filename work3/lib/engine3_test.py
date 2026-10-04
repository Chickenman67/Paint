# work3/lib/engine3_test.py
#
# Exercises engine3 against the measured reference spec
# (work3/measure/REFERENCE_MEASUREMENTS.md):
#   - reveal cadence ~1.0-1.5s, matching narration phrase onsets
#   - genuine per-frame motion (the v2 engine measured 0% motion; we require
#     >20% of consecutive frame pairs to differ)
#   - determinism: the same scene renders byte-identical frames every time
#
# It also reuses the shared drawing primitives (work/lib/ink.py, v2subjects.py,
# v2draw.py, stickman.py) to prove the engine composes REAL art, not just dots.
#
# Run:  python lib/engine3_test.py

import os
import sys
import math

import numpy as np
from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import engine3 as E            # noqa: E402

# Pull the shared primitives the way engine3 does, so we exercise the reuse path.
sys.path.insert(0, E._WORK_LIB)
import ink                     # noqa: E402
import v2subjects as S         # noqa: E402
import v2draw as D             # noqa: E402


# ---------------------------------------------------------------------------
# the test scene
# ---------------------------------------------------------------------------
# Target: a 12s scene at 60fps -> 720 frames.
#   - a static background (revealed at 0)
#   - an element revealed every 1.2s (the ~1.0-1.5s reference cadence)
#   - one element that slides across the screen over 1.5s (real per-frame motion)
#   - a stickman character element (real primitive, to prove reuse)
#   - a persistent title (drawn by v2draw)

SCENE_S = 12.0
FPS = E.FPS
EXPECT_FRAMES = int(round(SCENE_S * FPS))    # 720
REVEAL_EVERY = 1.2
SLIDE_FROM, SLIDE_TO, SLIDE_DUR = 1.5, 7.5, 1.5


def draw_background(tile, w, h):
    """A flat paper background with a faint ground ridge (ink primitive)."""
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 0, w, h], fill=E.PAPER + (255,))
    # a horizon so the scene isn't an empty field; seeds keep it deterministic
    ink.draw_ground(d, 0, w, int(h * 0.78), h, fill=(210, 205, 195, 255),
                    seed=7)


def make_planet(i):
    """Return a draw(tile, w, h) closure drawing one labelled planet.

    Each reveal gets a distinct planet position/size so a reveal is visibly a
    new element. Radii are deliberately large (FRAME-FILL: the subject should
    be a real share of the frame, not a timid prop) so each reveal registers as
    a substantial visual change, matching the reference's "cut" on a new beat.
    """
    def draw(tile, w, h):
        d = ImageDraw.Draw(tile)
        cx = 200 + (i * 190) % 820
        cy = 260 + (i * 90) % 180
        r = 130 + (i % 3) * 30
        base = ('gas', 'rock', 'rock_dk')[i % 3]
        S.planet(d, cx, cy, r, base=base, seed=100 + i, width=6,
                 fill=(150, 160, 190, 255) if base == 'gas' else None)
        D.draw_label(tile, "P%d" % i, center=(cx, cy + r + 40),
                     color=E.INK, size=30, outline_w=0)
    return draw


def draw_sliding_car(tile, w, h):
    """A 'car' that drives in from off-frame left to a resting mark.

    The body sits at absolute x 40..200 with wheels, so at the start of its
    slide (dx=-300) its right edge is already just on-frame at x~-100..: the
    car is visible for the whole slide window, giving a changed frame every
    frame it moves (the reference's "car drove in").
    """
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([40, 40, 200, 110], radius=18, fill=(200, 40, 40, 255),
                        outline=(0, 0, 0, 255), width=5)
    d.polygon([(80, 40), (110, 6), (160, 6), (185, 40)], fill=(120, 180, 220, 255))
    d.line([(80, 40), (110, 6), (160, 6), (185, 40)], fill=(0, 0, 0, 255),
           width=5, joint="curve")
    for wx in (78, 160):
        d.ellipse([wx - 20, 92, wx + 20, 132], fill=(30, 30, 30, 255),
                  outline=(0, 0, 0, 255), width=4)


def draw_moon(tile, w, h):
    """A small orbiting body that circles the scene (continuous motion).

    Drawn near its tile origin so the orbit keyframes (which are offsets from
    the authored position) place it on screen.
    """
    d = ImageDraw.Draw(tile)
    ink.draw_disc(d, 100, 100, 26, fill=(210, 210, 200, 255), outline=E.INK,
                  width=5, seed=5)


def draw_character(tile, w, h):
    """The recurring stickman, drawn big and cropped into frame (reference style).

    Uses theme='light' since this scene is on the light paper background.
    """
    S.character(tile, x_center=1080, foot_y=560, height=340,
                expression='oval', pose='pointing', seed=42)


def orbit_keys(cx, cy, rx, ry, t0, t1, turns=1.0, steps=48):
    """Keyframes tracing an ellipse from t0..t1, for a body in continuous orbit.

    Returned as absolute (t, x, y, scale, rot) offsets from the element's
    authored (centre-relative) position, which sits at (cx, cy) in the tile.
    Sampled densely so every rendered frame has a distinct transform -> real
    per-frame motion.
    """
    keys = []
    for i in range(steps + 1):
        u = i / steps
        t = t0 + (t1 - t0) * u
        ang = math.tau * turns * u
        keys.append((t, rx * math.cos(ang), ry * math.sin(ang), 1.0, 0.0))
    return keys


def build_scene():
    els = [E.E("bg", "bg", draw_background, at=0.0)]

    # one planet revealed every REVEAL_EVERY seconds
    for i in range(10):
        at = 0.6 + i * REVEAL_EVERY
        if at >= SCENE_S:
            break
        els.append(E.E("planet%d" % i, "subject", make_planet(i), at=at))

    # element 1: a car drives in from the left edge over SLIDE_DUR seconds.
    # It starts partly on-frame (right edge ~30px visible at dx=-170) so the
    # reveal itself is a visible change, then drives right across the frame --
    # the reference's "the car drove into frame" beat.
    els.append(E.E(
        "car", "subject", draw_sliding_car, at=SLIDE_FROM,
        motion=[(SLIDE_FROM, -170.0, 240.0, 1.0, 0.0),
                (SLIDE_FROM + SLIDE_DUR, 420.0, 240.0, 1.0, 0.0)],
    ))

    # element 2: a second car slides right-to-left over 1.2s (more real motion)
    els.append(E.E(
        "car2", "subject", draw_sliding_car, at=3.6,
        motion=[(3.6, 700.0, 120.0, 0.8, 0.0),
                (4.8, 200.0, 120.0, 0.8, 0.0)],
    ))

    # element 3: an orbiting moon circles for the back half (continuous motion)
    els.append(E.E(
        "moon", "subject", draw_moon, at=6.0,
        motion=orbit_keys(400, 300, 300, 90, 6.0, 12.0, turns=1.0, steps=72),
    ))

    # the character, revealed later so it reads as its own beat
    els.append(E.E("hero", "character", draw_character, at=5.0))

    return E.Scene(els, title="PROGRESSIVE REVEAL", duration=SCENE_S)


# ---------------------------------------------------------------------------
# helpers to measure one element's on-frame bounds
# ---------------------------------------------------------------------------

def element_ink_bbox(scene, el_id, t):
    """Render ONLY the given element (plus paper) and return its ink bbox.

    This isolates one element so we can watch its drawn bounds move over time,
    independent of siblings. Returns (x0,y0,x1,y1) or None.
    """
    solo = E.Scene([e for e in scene.elements if e.id == el_id], duration=scene.duration)
    frame = E.render_frame(solo, t)
    arr = np.asarray(frame, dtype=np.int16)
    # ink = anything meaningfully darker than the paper
    mask = (arr.max(axis=2) < 235)
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


# ---------------------------------------------------------------------------
# the test
# ---------------------------------------------------------------------------

def main():
    print("engine3 self-test")
    print("=" * 60)
    scene = build_scene()
    n_el = len(scene.elements)
    print("scene: %d elements, duration %.1fs, fps %d" % (n_el, scene.duration, FPS))

    frames = E.render_range(scene, fps=FPS, t0=0.0, t1=SCENE_S)
    failures = []

    # ---- (a) frame count -------------------------------------------------
    print("\n(a) frame count")
    print("    expected %d, got %d" % (EXPECT_FRAMES, len(frames)))
    if len(frames) != EXPECT_FRAMES:
        failures.append("frame count %d != %d" % (len(frames), EXPECT_FRAMES))
    else:
        print("    PASS")

    # ---- (b) determinism -------------------------------------------------
    print("\n(b) determinism (render frame 50 twice, byte-identical)")
    a = E.render_frame(scene, 50 / FPS)
    b = E.render_frame(scene, 50 / FPS)
    same = a.tobytes() == b.tobytes()
    print("    frame@%.4fs identical bytes: %s" % (50 / FPS, same))
    if not same:
        failures.append("frame 50 not deterministic")
    else:
        print("    PASS")
    # also: a re-render deep in the range matches the original sequence
    if frames[50].tobytes() != a.tobytes():
        failures.append("cached-sequence frame 50 != fresh render")
    else:
        print("    (also matches the pre-rendered sequence) PASS")

    # ---- (c) motion: >20% of consecutive pairs differ --------------------
    print("\n(c) motion: fraction of consecutive frame pairs that differ")
    changed = E.changed_pair_fraction(frames)
    print("    changed-pair fraction: %.1f%%  (need > 20%%)" % (changed * 100))
    if changed <= 0.20:
        failures.append("changed-pair fraction %.3f <= 0.20" % changed)
    else:
        print("    PASS")

    # richer still/motion/cut profile (reference bar: 83/7/10)
    still, motion, cut = E.motion_profile(frames)
    print("    still %.0f%% / motion %.0f%% / cut %.0f%%  (ref 83/7/10)"
          % (still * 100, motion * 100, cut * 100))

    # ---- (d) the slide element's bounds actually shift -------------------
    print("\n(d) sliding element actually moves (ink bbox over time)")
    # sample well inside the slide window, where the car is fully on-frame
    t0 = SLIDE_FROM + 0.4
    t1 = SLIDE_FROM + SLIDE_DUR - 0.2
    bbox0 = element_ink_bbox(scene, "car", t0)
    bbox1 = element_ink_bbox(scene, "car", t1)
    print("    bbox @%.2fs: %s" % (t0, bbox0))
    print("    bbox @%.2fs: %s" % (t1, bbox1))
    if bbox0 is None or bbox1 is None:
        failures.append("sliding element had no ink at one of the sample times")
    else:
        dx = bbox1[0] - bbox0[0]
        dy = bbox1[1] - bbox0[1]
        print("    shift: dx=%d dy=%d px" % (dx, dy))
        # it drove right by design (dx ~ +740); require a clear rightward move
        if dx < 300:
            failures.append("sliding element only moved dx=%d (expected >>0)" % dx)
        else:
            print("    PASS")

    # ---- extra: reveals actually change the frame (cadence sanity) ------
    print("\n(e) reveal cadence: a new element every ~%.1fs produces cuts" % REVEAL_EVERY)
    reveal_times = [e.at for e in scene.elements if e.at > 0]
    print("    %d timed reveals over %.1fs (median gap %.2fs)"
          % (len(reveal_times), SCENE_S,
             float(np.median(np.diff(sorted(reveal_times)))) if len(reveal_times) > 1 else -1))
    # count frames that differ from the previous frame right at a reveal time
    reveal_frames_hit = 0
    for at in reveal_times:
        idx = int(round(at * FPS))
        if 0 < idx < len(frames) and frames[idx].tobytes() != frames[idx - 1].tobytes():
            reveal_frames_hit += 1
    print("    reveals that visibly changed the frame: %d/%d" % (reveal_frames_hit, len(reveal_times)))
    if reveal_frames_hit < len(reveal_times):
        failures.append("some reveals did not change the frame")
    else:
        print("    PASS")

    # ---- summary ---------------------------------------------------------
    print("\n" + "=" * 60)
    if failures:
        print("FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("ALL CHECKS PASS")
    print("measured motion (changed consecutive pairs): %.1f%%" % (changed * 100))
    print("still/motion/cut profile: %d%% / %d%% / %d%%"
          % (round(still * 100), round(motion * 100), round(cut * 100)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
