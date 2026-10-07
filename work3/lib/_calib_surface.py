"""Calibrate the LIGHT-fill surface with my eye before touching the paint engine.

ROOT CAUSE (read off the code, then confirmed on frames). v2paint.fill_poly scales
its brush-scale tooth by darkness:

    tooth_w = VALUE_FINE + DARK * (1.22 - luma/255)

On a cream wall (luma ~210) that is 0.055 + 9*0.40 = ~1.9 levels -- invisible at
ship size. The broad VALUE drift (cells=5, +-15%) is smooth, so a light fill reads
as a soft GRADIENT, which is exactly the "blurry wash" the critic and my own eye
keep calling flat. This film is mostly light/cream fills, so 265/335 beats land
there. fortknox b26 scores 53 only because it stacks many small dark slabs that
each get the full 9-level tooth.

Round 3 already tried "just raise the constants" and the critic still read the
frames as flat, so I am NOT guessing new numbers. This sheet renders the SAME
cream room at four surface treatments, at ship size, so the choice is made by
looking -- which is the only thing that has ever actually moved this gate.

    python lib/_calib_surface.py
    -> measure/calib_surface.png   (four 640x360 panels side by side)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, '..', 'work', 'lib'))

import v2paint as PA  # noqa: E402

PW, PH = 640, 360
CREAM = (206, 214, 222)     # the mezhgorye room colour
INK = (24, 24, 28)


def _base_panel():
    """A representative light-fill panel: a big cream wall, a band, an inset."""
    im = Image.new('RGB', (PW, PH), (188, 196, 204))
    PA.fill_rect(im, [0, 0, PW, PH], (120, 132, 146), seed=1, value=0.05)
    PA.fill_rect(im, [30, 30, PW - 30, PH - 30], CREAM, seed=2, value=0.15)
    PA.hand_stroke(ImageDraw.Draw(im),
                   [(30, 30), (PW - 30, 30), (PW - 30, PH - 30), (30, PH - 30)],
                   INK, 6, closed=True, seed=3)
    return im


def panel_current():
    """v2paint exactly as it ships today."""
    return _base_panel()


def _fill_light_tooth(img, box, color, seed, tooth, freq_cells):
    """fill_poly but with the brush-scale tooth forced ON for light colours.

    This is the candidate fix: decouple the tooth amplitude from darkness so a
    cream wall gets real surface structure too, using a mid-frequency field
    (freq_cells) rather than per-pixel noise (which reads as video dither).
    """
    x0, y0, x1, y1 = box
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    d = ImageDraw.Draw(img)
    PA.fill_poly(img, pts, color, seed=seed, value=0.15)
    # now add mid-frequency tooth across the box, masked to the box
    bw, bh = int(x1 - x0), int(y1 - y0)
    if bw <= 0 or bh <= 0:
        return
    m = PA.fbm(bw, bh, seed=seed ^ 0x5A5A, cells=freq_cells, octaves=2)
    arr = np.asarray(img.crop((int(x0), int(y0), int(x1), int(y1))),
                     dtype=np.float32)
    arr += tooth * m[..., None]
    patch = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode='RGB')
    img.paste(patch, (int(x0), int(y0)))


def panel_light_tooth():
    """Candidate A: raise tooth on light fills with the existing fbm path."""
    im = _base_panel()
    _fill_light_tooth(im, [31, 31, PW - 30, PH - 30], CREAM, 22, 7.0, 13)
    return im


def panel_bristle():
    """Candidate B: mid-frequency bristle streaks, directional, like a brush."""
    im = _base_panel()
    x0, y0, x1, y1 = 31, 31, PW - 30, PH - 30
    bw, bh = int(x1 - x0), int(y1 - y0)
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    # vertical bristle streaks: a stretched noise along x, warped a little
    n = PA.fbm(bw, bh, seed=0xB21, cells=22, octaves=2)
    n = n * 0.7 + PA.fbm(bw, bh, seed=0xB22, cells=6, octaves=2) * 0.3
    streak = np.sin(xx * 0.28 + 3.0 * n)[..., None]
    patch = np.asarray(im.crop((x0, y0, x1, y1)), dtype=np.float32)
    patch += 6.0 * n[..., None] + 4.0 * streak
    im.paste(Image.fromarray(np.clip(patch, 0, 255).astype(np.uint8), 'RGB'),
             (x0, y0))
    return im


def panel_heavy():
    """Candidate C: A + B together, strongest."""
    im = _base_panel()
    x0, y0, x1, y1 = 31, 31, PW - 30, PH - 30
    bw, bh = int(x1 - x0), int(y1 - y0)
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    n = PA.fbm(bw, bh, seed=0xB31, cells=16, octaves=2)
    streak = np.sin(xx * 0.24 + 3.0 * n)[..., None]
    patch = np.asarray(im.crop((x0, y0, x1, y1)), dtype=np.float32)
    patch += 6.0 * n[..., None] + 4.0 * streak
    im.paste(Image.fromarray(np.clip(patch, 0, 255).astype(np.uint8), 'RGB'),
             (x0, y0))
    return im


PANELS = [
    ('CURRENT (tooth~2 on light)', panel_current),
    ('A light tooth fbm cells=13', panel_light_tooth),
    ('B bristle streaks', panel_bristle),
    ('C heavy combined', panel_heavy),
]

out = os.path.join(ROOT, 'measure')
os.makedirs(out, exist_ok=True)
sheet = Image.new('RGB', (PW * 2, PH * 2), (30, 30, 34))
dd = ImageDraw.Draw(sheet)
for i, (name, fn) in enumerate(PANELS):
    im = fn()
    a = np.asarray(im.convert('L'), np.float32)
    t = 24
    h, w = a.shape
    blocks = a[:h // t * t, :w // t * t].reshape(h // t, t, w // t, t)
    blocks = blocks.transpose(0, 2, 1, 3).reshape(-1, t * t)
    med = float(np.median(blocks.std(axis=1)))
    sheet.paste(im, ((i % 2) * PW, (i // 2) * PH))
    dd.text(((i % 2) * PW + 12, (i // 2) * PH + 12),
            '%s   tile_std=%.2f' % (name, med), fill=(255, 240, 120))
    print('%-28s tile_std %.2f' % (name, med))

p = os.path.join(out, 'calib_surface.png')
sheet.save(p)
print('\n-> %s' % p)