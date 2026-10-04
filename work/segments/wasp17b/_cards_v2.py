# wasp17b/_cards_v2.py -- the v2 card layers for WASP-17b, the back-orbiting
# gas giant that floats like a cork.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL): the puffy
#     banded gas giant is huge, often cropping a frame edge.
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - the "wrong way" motif is the visual through-line: a reversed rotation
#     arrow, an upside-down day/night, the planet counter-orbiting.
#   - our stickman (theme='light') reacts in the "you would not" beat.

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
    """Pop time for the FIRST of `words` that actually appears in this beat.

    ctx.when() silently falls back to the beat start when a word is absent, and
    0.0 is falsy -- so the obvious `_rel(a) or _rel(b)` idiom is unreliable. This
    checks presence explicitly instead.
    """
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


def _cw_arrow(p, cx, cy, r, color=None):
    """A circular motion arrow running CLOCKWISE (the ordinary direction)."""
    import math
    d = ImageDraw.Draw(p)
    color = color or T.INK
    start, sweep = 90, 300
    d.arc([cx - r, cy - r, cx + r, cy + r], start, start + sweep,
          fill=color, width=12)
    a1 = math.radians(start + sweep)
    tx, ty = cx + r * math.cos(a1), cy + r * math.sin(a1)
    tang = (math.sin(a1), -math.cos(a1))         # clockwise tangent
    D.draw_arrow(p, (tx, ty), (tx + tang[0] * 42, ty + tang[1] * 42),
                 color=color, width=9, head=32)


def _puffy(p, cx=700, cy=380, r=260, seed=0):
    """The signature image: a big soft banded gas giant."""
    d = ImageDraw.Draw(p)
    S.banded_gas(p, cx, cy, r, seed=seed, base='gas')


def _reverse_arrow(p, cx, cy, r, color=None):
    """A circular MOTION arrow running counter-clockwise (the wrong way).

    One ~300-degree arc with a single arrowhead tangent to the circle at the
    arc's leading end, so it reads as "this spins like this". (The first pass
    drew the arc PLUS a separate inward-pointing arrow at its start, which read
    as a spiral scribble or a dart stuck in a target, not as rotation.)
    """
    import math
    d = ImageDraw.Draw(p)
    color = color or T.RED
    start, sweep = 90, -300          # counter-clockwise: decreasing angle
    d.arc([cx - r, cy - r, cx + r, cy + r], start + sweep, start,
          fill=color, width=14)
    # arrowhead tangent to the circle at the arc's START end (the leading end
    # when sweeping negative): the tangent there points in the direction of travel.
    a0 = math.radians(start)
    tx, ty = cx + r * math.cos(a0), cy + r * math.sin(a0)
    # counter-clockwise tangent at angle a0
    tang = (-math.sin(a0), -math.cos(a0))     # for decreasing angle
    D.draw_arrow(p, (tx, ty), (tx + tang[0] * 46, ty + tang[1] * 46),
                 color=color, width=10, head=34)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'backwards_hook':
        def base(p):
            d = ImageDraw.Draw(p)
            S.star(d, 320, 380, 120, seed=1, col=S.C['star'])
            _puffy(p, cx=820, cy=380, r=210, seed=2)
            _reverse_arrow(p, 820, 380, 260)
        L.append(E.pop(0.0)(base))
        L.append(E.pop(_rel_any(ctx, beat_id, 'wrong', 'way'))(
            lambda p: D.draw_label(p, 'the wrong way around', center=(640, 650),
                                   color=T.LABEL_RED, size=48)))

    elif beat_id == 'everyone_else_turns':
        def compare(p):
            d = ImageDraw.Draw(p)
            S.star(d, 240, 400, 80, seed=3, col=S.C['star'])
            # three worlds spinning the ordinary way
            for i, (x, base) in enumerate([(520, 'rock'), (760, 'ice'), (1000, 'rock')]):
                S.planet(d, x, 400, 56, base=base, seed=4 + i)
                _cw_arrow(p, x, 400, 90, color=T.INK)     # clockwise: normal
            D.draw_label(p, 'all the same way', center=(640, 560),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(compare))

    elif beat_id == 'not_made_here':
        def thrown(p):
            d = ImageDraw.Draw(p)
            _puffy(p, cx=760, cy=380, r=230, seed=7)
            D.draw_arrow(p, (200, 380), (500, 380))          # flung in from outside
            D.draw_label(p, 'not made here', center=(640, 640),
                         color=T.LABEL_RED, size=50)
        L.append(E.pop(0.0)(thrown))

    elif beat_id == 'wrong_way_explained':
        def no_reason(p):
            d = ImageDraw.Draw(p)
            _reverse_arrow(p, 640, 400, 280)
            _puffy(p, cx=640, cy=400, r=180, seed=8)
            D.draw_label(p, 'no ordinary reason', center=(640, 660),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(no_reason))

    elif beat_id == 'almost_nothing_there':
        def empty(p):
            d = ImageDraw.Draw(p)
            _puffy(p, cx=640, cy=400, r=250, seed=9)
            D.draw_red_box(p, (390, 150, 890, 650), width=8)   # a huge frame on nothing
        L.append(E.pop(0.0)(empty))

    elif beat_id == 'cork_density':
        def cork(p):
            d = ImageDraw.Draw(p)
            S.swatch(p, 380, 220, 200, 240, S.C['rock_dk'], label='this world')
            S.swatch(p, 720, 220, 200, 240, S.C['gold'], label='a cork')
            D.draw_label(p, 'floats like a cork', center=(640, 560),
                         color=T.LABEL_RED, size=48)
        L.append(E.pop(0.0)(cork))

    elif beat_id == 'should_have_collapsed':
        def collapse(p):
            d = ImageDraw.Draw(p)
            _puffy(p, cx=640, cy=400, r=230, seed=10)
            D.draw_arrow(p, (640, 180), (640, 300))        # falling in on itself
            D.draw_label(p, 'should have collapsed', center=(640, 660),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(collapse))

    elif beat_id == 'cloud_wall':
        def wall(p):
            d = ImageDraw.Draw(p)
            # a limb-darkened gas giant: stacked bands with a towering edge
            _puffy(p, cx=640, cy=400, r=250, seed=11)
            for i in range(4):                    # weather stacked above the limb
                y = 250 - i * 34
                d.arc([640 - 250, y, 640 + 250, y + 500], 200, 340, fill=T.INK, width=6)
            _char(p, 180, 700, 300, 'skeptical', 'thinker')
            D.draw_label(p, 'clouds stack like a wall', center=(700, 660),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(wall))

    elif beat_id == 'endless_wind':
        def wind(p):
            d = ImageDraw.Draw(p)
            _puffy(p, cx=520, cy=400, r=200, seed=11)
            for y in (300, 380, 460):
                D.draw_arrow(p, (760, y), (1160, y), width=10, head=40)
            D.draw_label(p, 'endless wind', center=(520, 660),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(wind))

    elif beat_id == 'dayside_1700':
        def hot(p):
            d = ImageDraw.Draw(p)
            S.star(d, 300, 360, 110, seed=12, col=S.C['star_hot'])
            S.split_planet(d, 860, 360, 230, light_dir=(-1, 0), seed=13)
            D.draw_number(p, '1700', (860, 630), size=90, color=T.RED)
        L.append(E.pop(0.0)(hot))

    elif beat_id == 'you_would_not':
        def refuse(p):
            d = ImageDraw.Draw(p)
            D.draw_bubble(p, 'You would not land here.', (330, 200),
                          tail_to=(300, 420))
            _char(p, 300, 640, 320, 'terrified', 'hands_up')
        L.append(E.pop(0.0)(refuse))
        L.append(E.pop(_rel(ctx, beat_id, 'orbit'))(
            lambda p: D.draw_label(p, 'not land. not orbit. not stay.',
                                   center=(760, 520), color=T.LABEL_RED, size=44)))

    elif beat_id == 'three_wrongs':
        def wrongs(p):
            d = ImageDraw.Draw(p)
            D.draw_number(p, '1', (360, 300), size=80, color=T.RED)
            D.draw_label(p, 'backwards', center=(360, 370), color=T.LABEL_YELLOW, size=38)
            D.draw_number(p, '2', (640, 300), size=80, color=T.RED)
            D.draw_label(p, 'weightless', center=(640, 370), color=T.LABEL_YELLOW, size=38)
            D.draw_number(p, '3', (920, 300), size=80, color=T.RED)
            D.draw_label(p, 'endless wind', center=(920, 370), color=T.LABEL_YELLOW, size=38)
        L.append(E.pop(0.0)(wrongs))

    elif beat_id == 'never_supposed_to_be_here':
        def nobody(p):
            d = ImageDraw.Draw(p)
            _puffy(p, cx=640, cy=400, r=270, seed=14)
            D.draw_label(p, 'nobody planned this', center=(640, 660),
                         color=T.LABEL_RED, size=50)
        L.append(E.pop(0.0)(nobody))
        L.append(E.pop(_rel_any(ctx, beat_id, 'there', 'still'))(
            lambda p: _char(p, 1090, 680, 220, 'flat', 'shrugged')))

    else:
        L.append(E.pop(0.0)(lambda p: _puffy(p, seed=0)))

    return E.sort_layers(L)
