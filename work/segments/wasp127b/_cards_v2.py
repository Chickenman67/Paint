# wasp127b/_cards_v2.py -- the v2 card layers for WASP-127b, the gas giant with
# the fastest winds ever measured, and a leaking atmosphere.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - through-line: the screaming-wind banded giant, then the spectrum-bar
#     device (which colors are missing) explaining the leak.
#   - our stickman reacts to the wind and the leak.

import os
import sys

from PIL import ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))

import v2draw as D          # noqa: E402
import v2engine as E        # noqa: E402
import v2subjects as S      # noqa: E402
import v2type as T          # noqa: E402


def _rel(ctx, beat_id, word, offset=0.0):
    return max(0.0, ctx.when(beat_id, word, offset) - ctx.beat_start(beat_id))


def _rel_any(ctx, beat_id, *words, **kw):
    off = kw.get('offset', 0.0)
    for w in words:
        for ww in ctx.words_by_beat.get(ctx.beat_by_id[beat_id]['n'], []):
            if w.lower() in ww['w'].lower():
                return max(0.0, ctx.when(beat_id, w, off) - ctx.beat_start(beat_id))
    return 0.0


def _big_number(p, word, sub, y=280, color=None, size=112):
    D.draw_number(p, word, (640, y), size=size, color=color)
    D.draw_label(p, sub, center=(640, y + 130), color=T.LABEL_YELLOW, size=42)


def _char(p, x, foot_y, h, expr, pose):
    S.character(p, x, foot_y, h, expression=expr, pose=pose)


def _giant(p, cx=640, cy=380, r=270, seed=0, tilt=0.0):
    """The signature image: a big banded gas giant.

    `tilt` rolls the disc by that many degrees so two beats showing the same
    world are not two identical stickers. The first pass drew the same tan
    giant at the same size in 9 of 13 beats, which read as a slideshow of one
    image rather than a sequence.
    """
    d = ImageDraw.Draw(p)
    if not tilt:
        S.banded_gas(p, cx, cy, r, seed=seed, base='gas')
        return
    pad = int(r * 1.3)
    import PIL.Image as I
    tile = I.new('RGBA', (2 * pad, 2 * pad), (0, 0, 0, 0))
    S.banded_gas(tile, pad, pad, r, seed=seed, base='gas')
    tile = tile.rotate(tilt, resample=I.BICUBIC)
    p.paste(tile, (int(cx - pad), int(cy - pad)), tile)


def _wind(p, y_list, x0, x1, seed=0):
    d = ImageDraw.Draw(p)
    for i, y in enumerate(y_list):
        D.draw_arrow(p, (x0, y), (x1, y), width=10, head=38)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hurricane_forget_it':
        def wind_push(p):
            d = ImageDraw.Draw(p)
            # four wind lines, not three -- the first pass was three thin rules
            # over a mostly empty page with a small figure.
            _wind(p, [230, 320, 410, 500], 340, 1150)
            _char(p, 250, 700, 360, 'terrified', 'hands_up')
            D.draw_label(p, 'a hurricane you cannot survive', center=(780, 672),
                         color=T.LABEL_RED, size=42)
        L.append(E.pop(0.0)(wind_push))

    elif beat_id == 'name_the_planet':
        def name(p):
            d = ImageDraw.Draw(p)
            S.star(d, 250, 390, 105, seed=1, col=S.C['star'])
            _giant(p, cx=910, cy=390, r=185, seed=2, tilt=-12)
            D.draw_label(p, 'far too close to its star', center=(640, 665),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(name))

    elif beat_id == 'fastest_winds':
        def fast(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=430, cy=400, r=225, seed=3, tilt=-8)
            # The words used to sit at y=250/330, directly on the wind arrows
            # at y=320/400/480. They now sit under the arrow band, right column,
            # with clearance from the bottom edge.
            _wind(p, [300, 400, 500], 690, 1180)
            D.draw_number(p, 'FASTEST', (960, 610), size=58, color=T.RED)
            D.draw_number(p, 'WIND', (960, 674), size=58, color=T.RED)
        L.append(E.pop(0.0)(fast))

    elif beat_id == 'never_land':
        def noland(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=600, cy=370, r=270, seed=4, tilt=10)
            D.draw_label(p, 'never touching down', center=(640, 665),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(noland))

    elif beat_id == 'almost_empty':
        def empty(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=660, cy=380, r=250, seed=5, tilt=-14)
            D.draw_red_box(p, (410, 130, 910, 630), width=8)
            D.draw_label(p, 'almost empty inside', center=(640, 680),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(empty))

    elif beat_id == 'nothing_inside':
        def nothing(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=640, cy=400, r=275, seed=6, tilt=18)
            D.draw_number(p, 'NOTHING', (640, 400), size=96, color=T.RED)
        L.append(E.pop(0.0)(nothing))

    elif beat_id == 'read_the_star':
        def read(p):
            d = ImageDraw.Draw(p)
            S.star(d, 400, 360, 120, seed=7, col=S.C['star'])
            D.draw_arrow(p, (560, 360), (1000, 360))     # starlight into a bar
            D.draw_label(p, "read the star's light", center=(640, 640),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(read))

    elif beat_id == 'swallowed_colors':
        def spectrum(p):
            d = ImageDraw.Draw(p)
            S.bar(d, 200, 300, 1080, 420, 0.85, seed=8, fill=S.C['gold'], segments=6)
            D.draw_label(p, 'which colors are missing', center=(640, 218),
                         color=T.LABEL_INK, size=40)
        L.append(E.pop(0.0)(spectrum))

    elif beat_id == 'missing_tells_you':
        def missing(p):
            d = ImageDraw.Draw(p)
            # a bar with a chunk missing (red marker) + a red X on it
            S.bar(d, 200, 300, 1080, 420, 0.6, seed=9, fill=S.C['gold'], segments=5)
            D.draw_red_box(p, (620, 280, 760, 440), width=7)
            D.draw_label(p, 'the gaps tell you what is leaving',
                         center=(640, 560), color=T.LABEL_RED, size=40)
        L.append(E.pop(0.0)(missing))

    elif beat_id == 'water_leaving':
        def water(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=420, cy=440, r=180, seed=10)
            for i in range(5):
                D.draw_arrow(p, (640 + i * 90, 440), (640 + i * 90, 200),
                             color=T.RED, width=8, head=30)   # up and out
            D.draw_label(p, 'water, leaving upward', center=(880, 600),
                         color=T.LABEL_RED, size=42)
        L.append(E.pop(0.0)(water))

    elif beat_id == 'grains_high_above':
        def grains(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=620, cy=510, r=195, seed=11, tilt=-6)
            import random as rnd_mod
            rnd = rnd_mod.Random(11)
            for _ in range(22):
                x = rnd.randint(280, 980)
                y = rnd.randint(150, 300)
                d.ellipse([x, y, x + 12, y + 12], fill=S.C['rock'], outline=T.INK, width=3)
            D.draw_label(p, 'haze, floating too high', center=(640, 648),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(grains))

    elif beat_id == 'throwing_its_away':
        def throwing(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=430, cy=400, r=200, seed=12, tilt=6)
            # Arrow stops well short of the right edge: at x1=1080 its head
            # landed on the stickman's face.
            D.draw_arrow(p, (660, 400), (940, 400))     # throwing it off
            D.draw_label(p, 'throwing its own air away', center=(640, 665),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(throwing))
        L.append(E.pop(_rel(ctx, beat_id, 'planet'))(
            lambda p: _char(p, 1110, 700, 300, 'deadpan_grim', 'shrugged')))

    elif beat_id == 'leak_no_bottom':
        def leak(p):
            d = ImageDraw.Draw(p)
            # The leak IS the idea here, so it gets its own picture rather than
            # another banded disc: a giant with a ragged hole torn in its upper
            # limb and atmosphere streaming out of the gap.
            _giant(p, cx=560, cy=430, r=230, seed=13, tilt=6)
            import math
            hx, hy, hr = 700, 245, 52
            d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=T.PAPER,
                      outline=T.INK, width=7)
            for k in range(6):                              # air escaping the hole
                t = k / 5.0
                x0 = hx + 10 + t * 90
                y0 = hy - 20 - t * 120
                d.line([(x0, y0), (x0 + 46, y0 - 30)], fill=S.C['gold'], width=8)
            D.draw_label(p, 'your sky has a leak', center=(640, 668),
                         color=T.LABEL_RED, size=48)
        L.append(E.pop(0.0)(leak))

    elif beat_id == 'too_far_to_help':
        def toofar(p):
            d = ImageDraw.Draw(p)
            _giant(p, cx=900, cy=380, r=150, seed=14)     # small and far
            _char(p, 300, 700, 340, 'worried', 'hands_down')
            D.draw_label(p, 'too far away to help', center=(640, 660),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(toofar))

    else:
        L.append(E.pop(0.0)(lambda p: _giant(p, seed=0)))

    return E.sort_layers(L)
