"""Decide the fine canvas-tooth surface pass on a REAL frame, at ship size.

The reference book (blind pair q06_A) shows a fine woven CANVAS tooth on its light
pages -- a faint crosshatch weave, not uniform noise, not smooth cloud. Our light
fills (mezhgorye rooms, vatican/vatican backgrounds) have broad soft drift but no
fine structure, so they read as out-of-focus gradients.

My earlier synthetic swatch (lib/_calib_surface.py) added uniform/bristle noise to
one flat rectangle and it barely moved -- and memory judge-texture-at-ship-size says
the honest test is on a real frame at 1:1. So: take a real FLAT frame we have, apply
a woven crosshatch tooth at three amplitudes, and look. This decides whether a
subtle global canvas pass is worth doing; it does NOT modify v2paint (builders are
editing scene files concurrently -- the paint engine is off-limits until they stop).

    python lib/_calib_tooth.py
    -> measure/calib_tooth_<chapter>_<beat>.png   (3 panels: none / faint / stronger)
"""
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

# Real, eye-confirmed-flat frames: light fills, low pigment.
FRAMES = [('mezhgorye', 'b15'), ('vatican', 'b18'), ('pinegap', 'b10')]


def canvas_tooth(im, amp, period=3):
    """A faint woven crosshatch, like canvas showing through thin paint.

    Two out-of-phase line fields (a warp and a weft) at `period` px, averaged.
    Unlike uniform per-pixel noise this reads as TEXTILE, which is what the
    reference surface actually is. amp is in levels (1-8 typical).
    """
    a = np.asarray(im.convert('L'), dtype=np.float32)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = (np.sin(xx * (2 * np.pi / period))
             + np.sin(yy * (2 * np.pi / period))) * 0.5
    a = a + amp * weave
    out = im.convert('RGB').copy()
    rgb = np.asarray(out, dtype=np.float32)
    rgb[..., 0] = np.clip(rgb[..., 0] + amp * weave, 0, 255)
    rgb[..., 1] = np.clip(rgb[..., 1] + amp * weave, 0, 255)
    rgb[..., 2] = np.clip(rgb[..., 2] + amp * weave, 0, 255)
    return Image.fromarray(rgb.astype(np.uint8), 'RGB')


def tile_std(im):
    a = np.asarray(im.convert('L'), dtype=np.float32)
    t = 24
    h, w = a.shape
    b = a[:h // t * t, :w // t * t].reshape(h // t, t, w // t, t)
    b = b.transpose(0, 2, 1, 3).reshape(-1, t * t)
    return float(np.median(b.std(axis=1)))


out = os.path.join(ROOT, 'measure')
os.makedirs(out, exist_ok=True)

AMPS = [0.0, 4.0, 8.0]
for chapter, bid in FRAMES:
    importlib.invalidate_caches()
    mod = importlib.import_module(SC.scene_mod(chapter))
    scene = mod.build()
    t = dict(PG.beat_midpoints(chapter))[bid]
    tc = max(0.0, min(t, scene.duration - 0.05))
    base = E3.render_frame(scene, tc)
    panels = [canvas_tooth(base, a) for a in AMPS]
    from PIL import ImageDraw
    sheet = Image.new('RGB', (1280, 720 * len(panels)), (30, 30, 34))
    dd = ImageDraw.Draw(sheet)
    for i, (amp, pan) in enumerate(zip(AMPS, panels)):
        sheet.paste(pan, (0, i * 720))
        dd.text((12, i * 720 + 12),
                '%s %s  canvas_tooth amp=%.0f  tile_std=%.2f'
                % (chapter, bid, amp, tile_std(pan)),
                fill=(255, 240, 120))
        print('%-11s %-4s amp %4.1f  tile_std %.2f'
              % (chapter, bid, amp, tile_std(pan)))
    p = os.path.join(out, 'calib_tooth_%s_%s.png' % (chapter, bid))
    sheet.save(p)
    print('  -> %s\n' % os.path.basename(p))