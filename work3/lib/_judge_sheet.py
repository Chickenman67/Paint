"""Before/after judging sheet for the composition pass, at ship size.

The builders wrote their own pre-change baselines to work3/renders/<chapter>/
(prefix "before_"). This renders the SAME beats from the CURRENT scene file and
lays them out as before|after rows so the orchestrator can judge with its eyes.

WHY a dedicated harness: builders report their own before/after pigment numbers,
and a self-reported number is exactly the thing this project has learned not to
trust (verify-file-integrity-after-agent-writes). The only verdict that counts is
the rendered pixels, and per judge-texture-at-ship-size they must be seen at
1280x720 -- a thumbnail invents gaps that aren't there and hides ones that are.

    python lib/_judge_sheet.py --chapter pinegap --beats b01 b10
    python lib/_judge_sheet.py --chapter vatican --all
    -> measure/judge_<chapter>.png   (rows: before on top, after below)
"""
import argparse
import importlib
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402
import _pigment_gate as PG    # noqa: E402

W, H = 1280, 720
LBL = 34


def find_before(chapter, bid):
    """The builder's own baseline PNG for this beat, if it wrote one.

    Builders used two naming conventions -- 'before_b01.png' (area51, cheyenne) and
    plain 'b01.png' in the chapter dir (mezhgorye). Accept both, plus a
    '<chapter>_before' sibling directory, so one harness judges every chapter.
    """
    cands = [os.path.join(ROOT, 'renders', chapter, 'before_%s.png' % bid),
             os.path.join(ROOT, 'renders', chapter, 'before%s.png' % bid),
             os.path.join(ROOT, 'renders', chapter, '%s_before.png' % bid),
             os.path.join(ROOT, 'renders', chapter + '_before', '%s.png' % bid)]
    for p in cands:
        if os.path.exists(p):
            return p
    # A plainly-named frame may be EITHER the builder's baseline or its own
    # post-change render, and using the latter would silently report a fake 0.00
    # delta. Disambiguate by freshness: a baseline must predate the scene edit
    # (memory signal-build-completion-by-file-freshness).
    plain = os.path.join(ROOT, 'renders', chapter, '%s.png' % bid)
    scene_py = os.path.join(HERE, '%s2_scene.py' % chapter)
    if not os.path.exists(plain):
        return None
    if os.path.exists(scene_py) and os.path.getmtime(plain) > os.path.getmtime(scene_py):
        return None                      # newer than the edit -> it's an AFTER shot
    return plain


def render_now(chapter, bid):
    importlib.invalidate_caches()
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    t = dict(PG.beat_midpoints(chapter))[bid]
    t = max(0.0, min(t, scene.duration - 0.05))
    im = E3.render_frame(scene, t)          # render ONCE (memory measure-render-throughput-in-a-loop)
    med, frac = PG.tile_std(im)             # returns (median_std, painted_fraction)
    return im, med, frac


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', required=True)
    ap.add_argument('--beats', nargs='*', default=None)
    ap.add_argument('--all', action='store_true',
                    help='every beat that has a builder baseline on disk')
    a = ap.parse_args()

    ch = a.chapter
    all_beats = sorted(dict(PG.beat_midpoints(ch)))
    if a.all:
        beats = [b for b in all_beats if find_before(ch, b)]
    elif a.beats:
        beats = a.beats
    else:
        beats = all_beats

    rows = []
    for bid in beats:
        before_p = find_before(ch, bid)
        if not before_p:
            print('  %s: no baseline PNG, skipping row' % bid)
            continue
        try:
            after_im, after_std, after_frac = render_now(ch, bid)
        except Exception as exc:                      # noqa: BLE001
            print('  %s: RENDER FAILED: %s' % (bid, exc))
            continue
        before_im = Image.open(before_p).convert('RGB')
        if before_im.size != (W, H):
            before_im = before_im.resize((W, H))
        rows.append((bid, before_im, after_im,
                     PG.tile_std(before_im)[0], after_std, after_frac))

    if not rows:
        print('no comparable rows for %s' % ch)
        return

    sheet = Image.new('RGB', (W, (H + LBL) * len(rows)), (26, 26, 30))
    dd = ImageDraw.Draw(sheet)
    for i, (bid, b_im, a_im, b_std, a_std, a_frac) in enumerate(rows):
        y = i * (H + LBL)
        dd.text((10, y + 9), '%s  %s   tile_std  before %.2f  ->  after %.2f  (%+.2f)   painted %.0f%%'
                % (ch, bid, b_std, a_std, a_std - b_std, a_frac * 100),
                fill=(255, 238, 120) if a_std >= b_std else (255, 150, 130))
        sheet.paste(b_im, (0, y + LBL))
        dd.line([(0, y + LBL), (W, y + LBL)], fill=(90, 90, 100), width=2)
        sheet.paste(a_im, (0, y + LBL + H))

    out = os.path.join(ROOT, 'measure')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'judge_%s.png' % ch)
    sheet.save(p)
    print('\n%-5s %10s %10s %8s %9s' % ('beat', 'before', 'after', 'delta', 'painted'))
    for bid, _b, _a, bs, as_, af in rows:
        print('%-5s %10.2f %10.2f %+8.2f %8.0f%%' % (bid, bs, as_, as_ - bs, af * 100))
    print('\n-> %s  (%d rows)' % (p, len(rows)))


if __name__ == '__main__':
    main()