# gliese436b/_cards_v2.py -- the v2 card layers for Gliese 436b, the burning-ice
# world (a supercritical water planet dragging a glowing hydrogen tail).
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - the through-line is the impossible ICE: a blue-white disc that is also
#     burning, then the long comet-like hydrogen tail.
#   - our stickman (theme='light') reacts to the "no sense" reveal.

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


def _ice_disc(p, cx=640, cy=380, r=260, seed=0):
    """The signature image: a big blue-white ice world."""
    d = ImageDraw.Draw(p)
    S.planet(d, cx, cy, r, base='ice', seed=seed)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook_burning_ice':
        def base(p):
            d = ImageDraw.Draw(p)
            # planet pushed left so the two words have a clear right column;
            # at cx=560/r=240 the text at x=900 overlapped the disc's edge.
            _ice_disc(p, cx=400, cy=380, r=230, seed=1)
            D.draw_number(p, 'MADE OF ICE', (940, 300), size=64, color=T.RED)
            D.draw_number(p, 'ON FIRE', (940, 380), size=64, color=T.RED)
        L.append(E.pop(0.0)(base))
        L.append(E.pop(_rel(ctx, beat_id, 'fire'))(
            lambda p: D.draw_number(p, '?', (940, 500), size=120, color=T.RED)))

    elif beat_id == 'world_size':
        def size_neptune(p):
            d = ImageDraw.Draw(p)
            _ice_disc(p, cx=700, cy=370, r=260, seed=2)
            D.draw_label(p, 'about the size of Neptune', center=(640, 665),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(size_neptune))

    elif beat_id == 'hook_no_sense':
        def no_sense(p):
            d = ImageDraw.Draw(p)
            _ice_disc(p, cx=580, cy=380, r=215, seed=3)
            D.draw_red_x(p, (450, 250, 710, 510), width=10)   # the X on the rules
            D.draw_label(p, 'ice should melt', center=(640, 665),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(no_sense))
        L.append(E.pop(_rel(ctx, beat_id, 'melt'))(
            lambda p: _char(p, 1080, 700, 300, 'worried', 'thinker')))

    elif beat_id == 'pressure_and_heat':
        def press(p):
            d = ImageDraw.Draw(p)
            # arrows crushing inward on the ice disc
            _ice_disc(p, cx=640, cy=380, r=200, seed=4)
            for a in (0, 90, 180, 270):
                import math
                r0, r1 = 300, 260
                x0 = 640 + r0 * math.cos(math.radians(a))
                y0 = 380 + r0 * math.sin(math.radians(a))
                x1 = 640 + r1 * math.cos(math.radians(a))
                y1 = 380 + r1 * math.sin(math.radians(a))
                D.draw_arrow(p, (x0, y0), (x1, y1), width=10, head=34)
            D.draw_label(p, 'crushing pressure', center=(640, 660),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(press))

    elif beat_id == 'no_choice':
        def nochoice(p):
            d = ImageDraw.Draw(p)
            # The bubble auto-sized to a short string and rendered small and
            # cramped. Fixed width, bigger font, and lifted clear of the disc.
            D.draw_bubble(p, 'Solid. Liquid. Pick one.', (120, 200),
                          tail_to=(520, 430), font_size=44, max_w=520)
            _ice_disc(p, cx=820, cy=450, r=210, seed=5)
        L.append(E.pop(0.0)(nochoice))

    elif beat_id == 'supercritical':
        def super(p):
            d = ImageDraw.Draw(p)
            S.lava_planet(d, 640, 380, 250, seed=6)
            D.draw_number(p, 'SUPERCRITICAL', (640, 660), size=64, color=T.RED)
        L.append(E.pop(0.0)(super))

    elif beat_id == 'burning_torch':
        def torch(p):
            d = ImageDraw.Draw(p)
            # This was two flat swatches, which the blind critic correctly called
            # out as looking like unfinished placeholder rectangles. It is now
            # two actual worlds -- the ice planet and the lava planet -- so the
            # "flows like water / burns like a torch" contrast is shown, not
            # just colour-coded.
            S.planet(d, 420, 380, 230, base='ice', seed=30)
            S.lava_planet(d, 880, 380, 230, seed=31)
            D.draw_label(p, 'flows like water', center=(420, 660),
                         color=T.LABEL_BLUE, size=46)
            D.draw_label(p, 'burns like a torch', center=(880, 660),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(torch))

    elif beat_id == 'losing_mass':
        def losing(p):
            d = ImageDraw.Draw(p)
            _ice_disc(p, cx=380, cy=390, r=265, seed=7)
            D.draw_arrow(p, (700, 390), (1010, 390))       # mass streaming off
            D.draw_label(p, 'it is losing mass', center=(640, 668),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(losing))

    elif beat_id == 'glowing_tail':
        def tail(p):
            d = ImageDraw.Draw(p)
            # The planet was a small disc in the left third with a long empty
            # right half. It now anchors the left edge (cropped) and the tail
            # runs the full width, so the frame is filled.
            S.planet(d, 200, 400, 210, base='ice', seed=8)
            S.atmosphere_tail(d, 200, 400, 200, 900, seed=9, direction=(1, 0),
                             col=S.C['gold'])
            D.draw_label(p, 'a glowing tail', center=(760, 660),
                         color=T.LABEL_YELLOW, size=48)
        L.append(E.pop(0.0)(tail))

    elif beat_id == 'closing_impossible':
        def closing(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 190, 400, 195, base='ice', seed=10)
            S.atmosphere_tail(d, 190, 400, 185, 950, seed=11, direction=(1, 0),
                             col=S.C['gold'])
            D.draw_label(p, 'burning ice, dragging', center=(740, 630),
                         color=T.LABEL_RED, size=44)
            D.draw_label(p, 'a sun-lit tail', center=(740, 686),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(closing))
        L.append(E.pop(_rel(ctx, beat_id, 'picture'))(
            lambda p: _char(p, 1130, 700, 290, 'awed_brows', 'pointing')))

    else:
        L.append(E.pop(0.0)(lambda p: _ice_disc(p, seed=0)))

    return E.sort_layers(L)
