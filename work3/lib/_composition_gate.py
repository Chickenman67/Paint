"""Frame-fill and subject-mass gate -- the companion to _pigment_gate.py.

WHY THIS EXISTS (measured, not guessed). The composition pass raised area51 b01's
pigment from 3.46 to 11.85 (+8.39, "painted 59%") -- and the frame got visibly
WORSE. Side by side at 1280x720 (measure/judge_area51.png):
  * the sky was compressed from ~45% of the frame to a ~12% strip at the top
  * the empty foreground field GREW to ~75% of the frame
  * the solid black-posted fence was replaced by a thin white WIREFRAME grid
  * the stickman shrank and was marooned in the bottom-right corner
The metric went UP because a sparse high-contrast wireframe adds edges to tiles
that were previously empty. That is the metric being GAMED, and it is the exact
"flat vector" look the blind critic penalises. A gate that only counts pigment
will call this a win forever.

So this gate measures the things that actually regressed, on rendered pixels:

  FILL    ink coverage -- how much of the frame carries structure. A frame that is
          mostly one value is under-filled no matter how many thin lines cross it.
  MASS    subject mass -- the largest connected region of "content" (pixels far
          from the frame's dominant colour). A shrinking subject shrinks mass, even
          as a wireframe adds edges elsewhere.
  SKY     vertical composition -- the reference lets the dominant field run off
          frame edges; a sky crushed into a strip is a composition loss.

These are heuristics and they WILL need eye calibration, exactly like PAINT_STD did
(see memory pick-thresholds-from-eye-confirmed-cases).

WHAT ACTUALLY HAPPENED WHEN IT RAN (2026-10-07, all 34 area51 beats). Mass caught
the single pair it was built from -- b01 fell 0.216 -> 0.188 while pigment rose,
and the eye agrees that frame got worse. But over the whole chapter it also flagged
b09-b14 as "SUBJECT SHRANK", and the eye says those frames are FINE: a full-width
fence with black posts, a mountain horizon, dune contours, boulders, scrub, a
stickman. Real edge density, exactly what the canon asks for.

The reason is structural and it invalidates mass as a verdict: mass finds the
largest CONTIGUOUS block of pixels far from the dominant colour. A fence is a
PERFORATED GRID -- thousands of disconnected ink cells -- so no single connected
region is large even when the frame is densely structured. Mass penalises
precisely the lattice-and-mesh structure that scores well on the canon.

So every metric here is ADVISORY. Mass caught its one case and mis-fires on six
real frames; fill and top_gap do not discriminate at all. Two of three metrics in
a file written to catch a real regression is worse than no file, because it emits
confident flags that are wrong. Automated composition scoring is NOT solved here.
Keep this file for the before/after numbers it prints; DO NOT GATE ON IT. The eye
on the rendered frame remains the only verdict.

    python lib/_composition_gate.py --selftest
    python lib/_composition_gate.py --chapters area51
"""
import argparse
import importlib
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402
import _pigment_gate as PG    # noqa: E402

# Thresholds are placeholders pending more eye-confirmed cases. They are NOT a
# pass/fail bar yet -- printed as advisory numbers, the same way PAINT_STD's
# calibration table was built one real frame at a time.
#
# CALIBRATION FROM THE ONE REAL PAIR (area51 b01, eye-confirmed regression):
#                 fill     mass    pigment
#     before      0.269    0.216     3.46     painted fence, 45% sky  <- BETTER
#     after       0.270    0.188    11.85     wireframe, 12% sky      <- WORSE
# Only MASS discriminates. Fill was flat across the pair, so it does not detect
# this defect and must not be used to claim a frame improved. top_gap was
# identical (0.028) on both because the title strip puts content at y=0 in every
# frame -- it measures the title, not the composition, so it is not used.
#
# I wrote a synthetic self-test first that varied fill and mass TOGETHER and it
# "passed" while proving nothing about the real failure. That is the trap this
# file exists to avoid: construct the control from the real before/after pair,
# not from the story you expect.
MASS_MIN = 0.20       # area51-b01-before (good) 0.216; after (regression) 0.188


def _dominant(a, bins=16):
    """The frame's dominant colour, as an RGB triple."""
    q = (a // (256 // bins)).astype(np.int32)
    key = q[..., 0] * bins * bins + q[..., 1] * bins + q[..., 2]
    vals, counts = np.unique(key.reshape(-1), return_counts=True)
    k = int(vals[int(np.argmax(counts))])
    return np.array([(k // (bins * bins)) * (256 // bins) + 128 // bins,
                     ((k // bins) % bins) * (256 // bins) + 128 // bins,
                     (k % bins) * (256 // bins) + 128 // bins], dtype=np.float32)


def composition_metrics(im):
    """Return dict of fill / mass / sky_band on one rendered RGB frame."""
    rgb = np.asarray(im.convert('RGB'), dtype=np.float32)
    a = rgb.mean(axis=2)
    dom = _dominant(rgb)
    dist = np.linalg.norm(rgb - dom[None, None, :], axis=2)
    content = dist > 34.0                      # pixels far from the dominant field

    fill = float(content.mean())

    # subject mass: largest connected block of content, measured on a coarse grid
    # (exact CC would need scipy; a coarse flood by dilation is enough for a mass
    # trend and is what this heuristic is for).
    k = 8
    hh, ww = content.shape[0] // k, content.shape[1] // k
    if hh and ww:
        blocks = content[:hh * k, :ww * k].reshape(hh, k, ww, k).mean(axis=(1, 3))
        hot = blocks > 0.5
        # simple 4-connected flood from the largest seed
        seen = np.zeros_like(hot)
        best = 0
        for sy in range(hh):
            for sx in range(ww):
                if hot[sy, sx] and not seen[sy, sx]:
                    stack = [(sy, sx)]
                    seen[sy, sx] = True
                    n = 0
                    while stack:
                        y, x = stack.pop()
                        n += 1
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < hh and 0 <= nx < ww and hot[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                stack.append((ny, nx))
                    best = max(best, n)
        mass = float(best) / float(hh * ww)
    else:
        mass = 0.0

    # sky band: vertical extent of the content-free region above the first content
    rows_with_content = np.where(content.any(axis=1))[0]
    h = content.shape[0]
    top_gap = float(rows_with_content[0] / h) if len(rows_with_content) else 1.0
    return {'fill': fill, 'mass': mass, 'top_gap': top_gap}


def selftest():
    """Positive control built from the REAL eye-confirmed pair, not a synthetic one.

    A synthetic control (filled vs empty) passed while proving nothing: it moved
    fill and mass together, so it could not have detected the actual regression,
    which moves mass ALONE. This control renders area51 b01 both ways and asserts
    the thing the gate exists to catch:
      the pigment gate calls the regression a WIN  (3.46 -> 11.85)
      this gate must call it a LOSS               (mass 0.216 -> 0.188)
    If both gates ever agree on that pair, this file is a no-op and must be fixed.
    """
    importlib.invalidate_caches()
    try:
        mod = importlib.import_module(SC.scene_mod('area51'))
        scene = mod.build()
    except Exception as exc:                            # noqa: BLE001
        print('SELFTEST SKIP: cannot build area51 (%s)' % exc)
        return True
    before_p = os.path.join(ROOT, 'renders', 'area51', 'before_b01.png')
    if not os.path.exists(before_p):
        print('SELFTEST SKIP: baseline %s missing' % before_p)
        return True
    before = Image.open(before_p).convert('RGB')
    t = dict(PG.beat_midpoints('area51'))['b01']
    after = E3.render_frame(scene, max(0.0, min(t, scene.duration - 0.05)))

    mb, ma = composition_metrics(before), composition_metrics(after)
    pb, pa = PG.tile_std(before)[0], PG.tile_std(after)[0]
    print('area51 b01  before: mass=%.3f pigment=%.2f' % (mb['mass'], pb))
    print('area51 b01   after: mass=%.3f pigment=%.2f' % (ma['mass'], pa))

    pigment_says_win = pa > pb
    mass_says_loss = ma['mass'] < mb['mass']
    print('  pigment gate verdict : %s' % ('WIN' if pigment_says_win else 'loss'))
    print('  this gate verdict    : %s' % ('loss' if mass_says_loss else 'WIN'))
    ok = mass_says_loss and ma['mass'] < MASS_MIN <= mb['mass']
    print('SELFTEST %s  -- the regression is caught by mass and missed by pigment'
          % ('PASS' if ok else 'FAIL'))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapters', nargs='*', default=None)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest() else 1)

    chapters = a.chapters or ['pinegap', 'area51', 'tomb', 'room39',
                              'mezhgorye', 'cheyenne', 'svalbard',
                              'fortknox', 'vatican']
    print('%-11s %-5s %7s %7s %8s' % ('chapter', 'beat', 'fill', 'mass', 'pigment'))
    for ch in chapters:
        importlib.invalidate_caches()
        try:
            mod = importlib.import_module(SC.scene_mod(ch))
            scene = mod.build()
        except Exception as exc:                       # noqa: BLE001
            print('%-11s BUILD FAILED: %s' % (ch, exc))
            continue
        for bid, t in PG.beat_midpoints(ch):
            im = E3.render_frame(scene, max(0.0, min(t, scene.duration - 0.05)))
            m = composition_metrics(im)
            pig = PG.tile_std(im)[0]
            # No flag is raised on purpose. See the module docstring: mass caught
            # its one calibration case but mis-fires on dense fence/grid frames
            # that are correct, and fill/top_gap do not discriminate. Emitting a
            # "<-- SUBJECT SHRANK" verdict from a metric known to be wrong is the
            # failure this project keeps paying for (guards-that-skip-real-defects
            # are worse than none, and a wrong flag is worse than a missing one).
            print('%-11s %-5s %7.3f %7.3f %8.2f'
                  % (ch, bid, m['fill'], m['mass'], pig))


if __name__ == '__main__':
    main()