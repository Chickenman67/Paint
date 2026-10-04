# tres2b/_cards_v2.py -- the v2 card layers for TRES-2b, the darkest exoplanet.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the planet is the DOMINANT subject and FILLS the frame (CLAUDE.md §7
#     FRAME-FILL): it is a night world, so the split day/night disc is huge and
#     crops a frame edge.
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - our stickman (theme='light') carries the reaction in the reveal beats.
#   - pop times keyed to SPOKEN WORDS via ctx.when(), so the picture changes when
#     the narrator says the thing (STYLE_CANON2 §4, CLAUDE.md §5).

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
    """Beat-relative pop time for when `word` is spoken in this beat."""
    return max(0.0, ctx.when(beat_id, word, offset) - ctx.beat_start(beat_id))


def _rel_any(ctx, beat_id, *words, **kw):
    """Pop time for the FIRST of `words` that actually appears in this beat.

    ctx.when() silently falls back to the beat start when a word is absent, and
    0.0 is falsy -- so `_rel(a) or _rel(b)` is unreliable. Check presence.
    """
    off = kw.get('offset', 0.0)
    for w in words:
        for ww in ctx.words_by_beat.get(ctx.beat_by_id[beat_id]['n'], []):
            if w.lower() in ww['w'].lower():
                return max(0.0, ctx.when(beat_id, w, off) - ctx.beat_start(beat_id))
    return 0.0


# A few reusable pieces -------------------------------------------------------

def _big_number(p, word, sub, y=280, color=None, size=118):
    D.draw_number(p, word, (640, y), size=size, color=color)
    D.draw_label(p, sub, center=(640, y + 130), color=T.LABEL_YELLOW, size=42)


def _char(p, x, foot_y, h, expr, pose):
    S.character(p, x, foot_y, h, expression=expr, pose=pose)


def _split_dark(p, cx=880, cy=360, r=250, light_dir=(-1, 0), seed=0):
    """The signature image: one half blazing day, one half absolute night."""
    d = ImageDraw.Draw(p)
    S.split_planet(d, cx, cy, r, light_dir=light_dir, seed=seed)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook_never_see_it':
        def base(p):
            d = ImageDraw.Draw(p)
            _split_dark(p, cx=800, cy=350, r=280, light_dir=(-1, 0), seed=1)
        L.append(E.pop(0.0)(base))
        L.append(E.pop(_rel(ctx, beat_id, 'never'))(
            lambda p: D.draw_label(p, 'you will never see this side',
                                   center=(640, 655), color=T.LABEL_RED, size=46)))
        L.append(E.pop(_rel(ctx, beat_id, 'once'))(
            lambda p: _char(p, 190, 700, 330, 'flat', 'shielding_eyes')))

    elif beat_id == 'albedo_one_percent':
        # bounces back under 1% of the light
        def base(p):
            d = ImageDraw.Draw(p)
            S.star(d, 250, 360, 120, seed=2, col=S.C['star'])
            S.planet(d, 900, 360, 90, base='rock', seed=3)
            D.draw_arrow(p, (400, 360), (760, 360))     # light in
        L.append(E.pop(0.0)(base))
        L.append(E.pop(_rel_any(ctx, beat_id, 'less', 'one'))(
            lambda p: D.draw_number(p, '<1%', (900, 560), size=96, color=T.RED)))

    elif beat_id == 'darker_than_coal':
        # darker than coal, darker than asphalt -> comparison swatches
        def swatches(p):
            d = ImageDraw.Draw(p)
            S.swatch(p, 380, 260, 200, 200, S.C['rock_dk'], label='asphalt')
            S.swatch(p, 700, 260, 200, 200, S.C['night'], label='the planet')
        L.append(E.pop(0.0)(swatches))
        L.append(E.pop(_rel(ctx, beat_id, 'coal'))(
            lambda p: D.draw_label(p, 'darker than coal', center=(640, 560),
                                   color=T.LABEL_RED, size=48)))

    elif beat_id == 'tidally_locked_reveal':
        def reveal(p):
            d = ImageDraw.Draw(p)
            _split_dark(p, cx=700, cy=380, r=280, light_dir=(-1, 0), seed=4)
        L.append(E.pop(0.0)(reveal))
        L.append(E.pop(_rel(ctx, beat_id, 'obscene'))(
            lambda p: D.draw_label(p, 'one side never moves', center=(420, 620),
                                   color=T.LABEL_YELLOW, size=44)))

    elif beat_id == 'two_faces_forever':
        def faces(p):
            d = ImageDraw.Draw(p)
            S.split_planet(d, 500, 400, 200, light_dir=(1, 0), seed=5)
            D.draw_label(p, 'ALWAYS DAY', center=(720, 240), color=T.RED, size=40)
            D.draw_label(p, 'ALWAYS NIGHT', center=(280, 610), color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(faces))

    elif beat_id == 'never_warms_never_cools':
        def thermo(p):
            d = ImageDraw.Draw(p)
            S.thermometer(d, 900, 600, 380, 0.12, seed=6, hot=False)   # night side
            S.split_planet(d, 380, 400, 200, light_dir=(1, 0), seed=7)
            D.draw_label(p, 'night never warms', center=(250, 200), color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(thermo))

    elif beat_id == 'day_side_furnace':
        def furnace(p):
            d = ImageDraw.Draw(p)
            S.lava_planet(d, 700, 400, 250, seed=8)                    # the day half blazing
            D.draw_number(p, 'FURNACE', (640, 640), size=88, color=T.RED)
        L.append(E.pop(0.0)(furnace))

    elif beat_id == 'dull_red_glow':
        def glow(p):
            d = ImageDraw.Draw(p)
            _split_dark(p, cx=700, cy=400, r=250, light_dir=(-1, 0), seed=9)
            D.draw_label(p, 'a dull red glow', center=(700, 650),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(glow))

    elif beat_id == 'hot_but_too_dark':
        def hotdark(p):
            d = ImageDraw.Draw(p)
            S.thermometer(d, 880, 600, 380, 0.95, seed=10, hot=True)
            D.draw_label(p, 'hot enough to burn', center=(880, 240),
                         color=T.LABEL_RED, size=40)
            D.draw_label(p, 'too dark to see it', center=(880, 300),
                         color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(hotdark))
        L.append(E.pop(_rel(ctx, beat_id, 'hand'))(
            lambda p: _char(p, 240, 700, 340, 'terrified', 'hands_up')))

    elif beat_id == 'watch_the_star':
        def star_small(p):
            d = ImageDraw.Draw(p)
            S.star(d, 980, 200, 90, seed=11, col=S.C['star'])
            D.draw_label(p, 'it orbits this', center=(980, 360),
                         color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(star_small))

    elif beat_id == 'star_running_out_of_fuel':
        def dying(p):
            d = ImageDraw.Draw(p)
            S.star(d, 640, 380, 180, seed=12, col=S.C['star_hot'])
            D.draw_label(p, 'running out of fuel', center=(640, 620),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(dying))

    elif beat_id == 'swelling_and_closer':
        def swell(p):
            d = ImageDraw.Draw(p)
            S.star(d, 400, 380, 200, seed=13, col=S.C['star_hot'])
            S.orbit_path(d, 640, 380, 360, 220, seed=14)
            S.planet(d, 1000, 380, 70, base='rock_dk', seed=15)
            D.draw_arrow(p, (640, 380), (900, 380))     # creeping closer
        L.append(E.pop(0.0)(swell))

    elif beat_id == 'atmosphere_as_tail':
        def tail(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 380, 400, 130, base='rock_dk', seed=16)
            S.atmosphere_tail(d, 380, 400, 120, 420, seed=17, direction=(1, 0))
            D.draw_label(p, 'the whole air, trailing off', center=(880, 620),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(tail))

    elif beat_id == 'unmade_by_its_own_sun':
        def unmade(p):
            d = ImageDraw.Draw(p)
            S.star(d, 900, 380, 200, seed=18, col=S.C['star_hot'], spike_len=1.4)
            S.planet(d, 400, 400, 90, base='rock_dk', seed=19)
            D.draw_arrow(p, (520, 400), (700, 400))     # being pulled in
            D.draw_label(p, 'unmade by its own sun', center=(640, 640),
                         color=T.LABEL_RED, size=48)
        L.append(E.pop(0.0)(unmade))
        L.append(E.pop(_rel(ctx, beat_id, 'unmade'))(
            lambda p: _char(p, 200, 700, 320, 'deadpan_grim', 'shrugged')))

    else:
        L.append(E.pop(0.0)(lambda p: _split_dark(p, seed=0)))

    return E.sort_layers(L)
