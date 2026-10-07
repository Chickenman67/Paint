"""Measure painterly pigment per chapter, on RENDERED frames.

WHY THIS EXISTS. The blind critic scored us 5/18 (see measure/blind/VERDICTS2.txt)
and named one gap across five of six clean losses: our frames read as flat
vector. The win (svalbard q01, grainy painted snow) has pigment; the losses
(vatican q06, smooth gradient) do not. So the question is not "is the pigment
path missing" -- PA.paper_overlay exists and ships -- but "which chapters call
it". This measures that, per chapter, on real pixels.

RENDERS, DOES NOT SCAN SOURCE. Every other mistake in this project's gates came
from measuring the .py file instead of the picture (memory
title-band-gate-must-see-art-not-just-text, gates-must-render-not-just-inspect).
A source scan for `paper_overlay(` would read a call that sits in a draw
function which is never called at this timestamp, or miss a chapter that paints
its texture a different way. So: render N frames per chapter and measure the
pixels.

THE METRIC. Per 24x24 tile, the standard deviation of luma across the tile's
pixels. A flat / smoothly-shaded fill has std ~2-3. Real brush grain stacks to
std ~23-43. We report the median tile std over the frame, plus the fraction of
tiles above a paint threshold. Median-over-all-tiles is robust to the large flat
areas that dominate a vector frame; a mean would be dragged around by them.

PER BEAT, NOT PER CHAPTER. v1 of this gate sampled six frames on an even grid
and printed a chapter MEAN. It called all nine chapters PAINTED, including
fortknox at a mean of 22.27 -- in a chapter where the frame the critic actually
called flat measures 2.49. The mean of a rich frame and a dead frame describes
neither one. v2 renders every beat's MIDPOINT and a chapter is clean only when
every beat clears the bar, so the output is a list of specific flat beats to fix
instead of a score that hides them. This is memory
a-capped-gate-list-truncates-your-work-list and coverage-gate-catches-silent-
scene-failure in a new costume: a summary statistic that averages a defect away
is worse than no measurement, because it reports green.

THE THRESHOLD IS EYE-CALIBRATED. See the block above PAINT_STD. It is set from
six real frames the blind critic ruled on, all six inspected at 1280x720, with
the metric agreeing with the eye on every one. It is NOT set from the synthetic
self-test, which only spans 2.24-3.29 and cannot see the real gap.

POSITIVE CONTROL. --selftest renders a deliberately flat frame and a
deliberately textured one through the same measurement path and asserts the
flat one comes back below the painted one. If the self-test does not pass, every
number this gate prints is meaningless and the gate is a no-op. Run it before
believing a chapter's score.

    python lib/_pigment_gate.py --selftest
    python lib/_pigment_gate.py                  # all nine chapters, per beat
    python lib/_pigment_gate.py --chapters vatican svalbard
"""

import argparse
import importlib
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402
import v2paint as PA          # noqa: E402

CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']

TILE = 24

# A tile is "painted" when its internal luma spread reaches painterly grain.
#
# CALIBRATED FROM EYE-CONFIRMED REAL FRAMES, not guessed and not from the
# synthetic self-test. Six frames the blind critic actually ruled on were
# rendered at ship size and inspected; the metric agrees with the eye on all six
# and splits them into two clusters with a wide empty gap between:
#
#     fortknox  75.82  std 34.27  PAINTED  gold brick wall, per-brick value drift,
#                                         brush banding in the gold, rivets
#     svalbard  29.04  std 42.83  PAINTED  grainy snow, the round-2 win
#     vatican   27.62  std 23.56  PAINTED
#     ---------------- gap: nothing observed between 3.20 and 23.56 ------------
#     fortknox  32.49  std  2.49  FLAT     smooth blurry gradients, no grain
#     svalbard  67.75  std  3.20  FLAT     smooth wash; "2016" hangs off the
#                                         chart border; clipped rect at right edge
#     vatican   64.44  std  3.19  FLAT     blurry stair treads
#
# Log-midpoint of the gap is 8.68; 8.0 sits inside it with margin on both sides.
# NOTE the synthetic self-test only spans 2.24 (flat) to 3.29 (PA.fill_rect),
# which is why it could never set this number -- PA.fill_rect's +/-15% smooth
# brightness drift is subtle at a 24px tile. Real painted frames reach 23-43
# because the grain stacks with paper tooth and edge wobble. Set the threshold
# from the real cases; the self-test's job is only to prove the gate can tell
# the two drawing paths apart at all.
PAINT_STD = 8.0


def tile_std(im):
    """Median per-tile luma standard deviation over the frame.

    Returns (median_std, painted_fraction). Both in the same units so a single
    number describes the frame.
    """
    a = np.asarray(im.convert('L'), dtype=np.float32)
    h, w = a.shape
    rows = h // TILE
    cols = w // TILE
    a = a[:rows * TILE, :cols * TILE]
    blocks = a.reshape(rows, TILE, cols, TILE).transpose(0, 2, 1, 3)
    blocks = blocks.reshape(rows * cols, TILE * TILE)
    stds = blocks.std(axis=1)
    return float(np.median(stds)), float((stds >= PAINT_STD).mean())


def render_chapter_frames(chapter, n=6):
    """Render n frames spread through the chapter. Returns [(t, PIL.Image)]."""
    importlib.invalidate_caches()
    # SC.scene_mod(), never '%s_scene' % chapter -- the v1 baseline is not what
    # ships. This wiring bug has already produced one void critic run.
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    out = []
    for i in range(n):
        # sample inside the chapter, avoiding the very first and last 2%
        t = scene.duration * (0.03 + 0.94 * (i + 0.5) / n)
        out.append((t, E3.render_frame(scene, t)))
    return out


def beat_midpoints(chapter):
    """[(beat_id, t)] at the MIDPOINT of every beat in the chapter.

    Sampling per beat, not on an even grid, is the whole point of this rewrite.
    The even-grid chapter average read PAINTED for all nine chapters -- including
    fortknox at 22.27, where b? at t=32.49 measures 2.49 -- because a rich frame
    and a dead frame average into one number that describes neither. The
    defect the critic named lives on individual BEATS, so the measurement has to
    land on individual beats for the work-list to be actionable.
    """
    path = os.path.join(ROOT, 'segments', chapter, 'beats.json')
    beats = json.load(open(path))['beats']
    out = []
    for b in beats:
        start = float(b.get('start', 0.0))
        end = float(b.get('end', start))
        dur = end - start
        # sample 60% through the beat: past any element arrival animation, still
        # before the beat turns over
        out.append((b.get('id', '?'), start + dur * 0.6))
    return out


def measure_chapter(chapter):
    """Render every beat midpoint and measure it. Returns a per-beat work-list."""
    importlib.invalidate_caches()
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    rows = []
    for bid, t in beat_midpoints(chapter):
        tc = max(0.0, min(t, scene.duration - 0.05))
        im = E3.render_frame(scene, tc)
        med, frac = tile_std(im)
        rows.append({'beat': bid, 't': round(tc, 2), 'median_std': round(med, 2),
                     'painted_fraction': round(frac, 3)})
    flat = [r for r in rows if r['median_std'] < PAINT_STD]
    meds = [r['median_std'] for r in rows]
    return {
        'chapter': chapter,
        'n_beats': len(rows),
        'n_flat': len(flat),
        'flat_beats': [r['beat'] for r in flat],
        'worst_frame': round(float(np.min(meds)), 2) if meds else 0.0,
        'median_std_mean': round(float(np.mean(meds)), 2) if meds else 0.0,
        # A chapter is only PAINTED if every beat clears the bar. This is the
        # rule the old average violated: 44 beats where 30 are painted and 14
        # are dead is not a painted chapter, it is a chapter with 14 defects,
        # and only the per-beat rule can say which 14.
        'verdict': 'PAINTED' if not flat else 'FLAT(%d/%d)' % (len(flat), len(rows)),
        'frames': rows,
    }


def selftest():
    """Positive control. A gate that cannot tell flat from painted is a no-op.

    The two controls are the two ways this codebase actually draws a shape:
      FLAT      ImageDraw.rectangle  -- solid vector fill, no pigment
      PAINTED   PA.fill_rect          -- the fBm value drift, brush banding,
                                        tint wobble and irregular edge
    Both get paper_overlay afterwards, because every scene calls it, so the
    page tooth is held constant and the test isolates the shape pigment.
    """
    flat = Image.new('RGB', (1280, 720), (110, 150, 80))
    fd = ImageDraw.Draw(flat)
    fd.rectangle([60, 60, 620, 660], fill=(150, 150, 150))
    fd.rectangle([660, 60, 1220, 660], fill=(120, 96, 74))
    fd.line([(0, 360), (1279, 360)], fill=(20, 20, 20), width=6)
    PA.paper_overlay(flat, seed=4242)

    painted = Image.new('RGB', (1280, 720), (110, 150, 80))
    PA.fill_rect(painted, [60, 60, 620, 660], (150, 150, 150), seed=11)
    PA.fill_rect(painted, [660, 60, 1220, 660], (120, 96, 74), seed=12)
    PA.hand_stroke(ImageDraw.Draw(painted), [(0, 360), (1279, 360)],
                   (20, 20, 20), 6, seed=13)
    PA.paper_overlay(painted, seed=4242)

    f_med, f_frac = tile_std(flat)
    p_med, p_frac = tile_std(painted)

    print('SELFTEST -- flat vector fill vs PA.fill_rect, same page tooth')
    print('  flat      median_std %6.2f  painted_frac %.3f' % (f_med, f_frac))
    print('  painted   median_std %6.2f  painted_frac %.3f' % (p_med, p_frac))

    ok_flat = f_med < p_med
    ok_sep = p_med >= PAINT_STD
    print('  flat scores below painted:       %s' % ('PASS' if ok_flat else 'FAIL'))
    print('  painted at/above threshold %4.1f: %s' % (PAINT_STD, 'PASS' if ok_sep else 'FAIL'))
    if not (ok_flat and ok_sep):
        print('\nSELFTEST FAILED -- every score this gate prints is meaningless.')
        return 1
    print('\nSELFTEST PASSED -- the gate discriminates. Threshold %0.1f sits '
          'between them.' % PAINT_STD)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapters', nargs='*', default=None)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--json', default=None)
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    chapters = a.chapters or CHAPTERS
    results = []
    print('PIGMENT COVERAGE -- per BEAT midpoint, tile=%dpx, '
          'threshold std>=%.1f (eye-calibrated)\n' % (TILE, PAINT_STD))
    print('%-12s %5s %6s %8s  %s' % ('chapter', 'beats', 'flat', 'worst',
                                     'verdict'))
    print('-' * 56)
    for ch in chapters:
        r = measure_chapter(ch)
        results.append(r)
        print('%-12s %5d %6d %8.2f  %s'
              % (r['chapter'], r['n_beats'], r['n_flat'], r['worst_frame'],
                 r['verdict']))

    clean = [r for r in results if r['verdict'] == 'PAINTED']
    dirty = [r for r in results if r['verdict'] != 'PAINTED']
    tot_flat = sum(r['n_flat'] for r in results)
    tot_beats = sum(r['n_beats'] for r in results)
    print('\nCLEAN  (%d ch): %s' % (len(clean),
          ', '.join(r['chapter'] for r in clean) or '-'))
    print('FLAT   (%d ch): %s' % (len(dirty),
          ', '.join(r['chapter'] for r in dirty) or '-'))
    print('\nFLAT BEATS: %d / %d' % (tot_flat, tot_beats))
    for r in results:
        if r['flat_beats']:
            print('  %-12s %s' % (r['chapter'], ' '.join(r['flat_beats'])))

    if a.json:
        json.dump({'threshold': PAINT_STD, 'tile': TILE, 'results': results},
                  open(a.json, 'w'), indent=1)
        print('\n-> %s' % a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())