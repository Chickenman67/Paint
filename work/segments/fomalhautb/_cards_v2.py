# fomalhautb/_cards_v2.py -- the v2 card layers for Fomalhaut b (Dagon), the
# maybe-planet imaged in visible light inside a wide dust ring.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - through-line: the bright star, the wide dust ring, the faint dot inside
#     it, then the honest "maybe" -- dust OR world, same light, two meanings --
#     and finally the wild eccentric orbit that dooms it to a long fall.
#   - the two-idea compare (dust vs world) is the emotional turn; the character
#     carries the "it is still there" shrug.

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


def _star_and_ring(p, star_c=(320, 360), sr=110, seed=0, with_planet=True):
    """The signature image: the bright star, a wide flat dust ring, and a faint
    dot caught inside it."""
    d = ImageDraw.Draw(p)
    S.star(d, star_c[0], star_c[1], sr, seed=seed, col=S.C['star'])
    S.orbit_path(d, 640, 400, 500, 150, seed=seed + 1, width=7)
    if with_planet:
        S.planet(d, 1000, 400, 34, base='rock', seed=seed + 2)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook_brightest_star':
        def brightest(p):
            d = ImageDraw.Draw(p)
            S.star(d, 640, 360, 200, seed=1, col=S.C['star'], spike_len=1.3)
            D.draw_label(p, 'the brightest star in the autumn sky',
                         center=(640, 640), color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(brightest))

    elif beat_id == 'the_ring':
        def ring(p):
            d = ImageDraw.Draw(p)
            S.star(d, 320, 380, 100, seed=2, col=S.C['star'])
            S.orbit_path(d, 640, 400, 520, 160, seed=3, width=8)
            D.draw_label(p, 'a wide, thin ring of dust and ice',
                         center=(640, 660), color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(ring))

    elif beat_id == 'light_in_the_ring':
        def caught(p):
            d = ImageDraw.Draw(p)
            S.star(d, 280, 380, 100, seed=4, col=S.C['star'])
            S.orbit_path(d, 640, 400, 520, 160, seed=5, width=7)
            S.planet(d, 1020, 400, 36, base='rock', seed=6)
            D.draw_arrow(p, (1020, 400), (1120, 400))       # it caught the light
            D.draw_label(p, 'something caught the light', center=(640, 620),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(caught))

    elif beat_id == 'first_visible_planet':
        def first(p):
            d = ImageDraw.Draw(p)
            _star_and_ring(p, seed=7)
            D.draw_number(p, 'FIRST', (640, 640), size=76, color=T.RED)
        L.append(E.pop(0.0)(first))

    elif beat_id == 'the_headline':
        def headline(p):
            d = ImageDraw.Draw(p)
            D.draw_bubble(p, 'The headline.', (420, 240), tail_to=(640, 420))
            _star_and_ring(p, seed=8)
        L.append(E.pop(0.0)(headline))

    elif beat_id == 'not_the_end':
        def not_end(p):
            d = ImageDraw.Draw(p)
            _star_and_ring(p, seed=9)
            D.draw_label(p, 'but it was never the end', center=(640, 650),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(not_end))
        L.append(E.pop(_rel(ctx, beat_id, 'faint'))(
            lambda p: _char(p, 1090, 700, 300, 'skeptical', 'thinker')))

    elif beat_id == 'maybe_dust':
        def dust(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 400, 220, base='rock_dk', seed=10)
            import random as rnd_mod
            rnd = rnd_mod.Random(10)
            for _ in range(30):
                x = rnd.randint(440, 840); y = rnd.randint(200, 600)
                d.ellipse([x, y, x + 14, y + 14], fill=S.C['rock_dk'],
                          outline=T.INK, width=3)
            D.draw_label(p, 'maybe just dust', center=(640, 660),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(dust))

    elif beat_id == 'maybe_world':
        def world(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 400, 220, base='rock', seed=11)
            S.orbit_path(d, 640, 400, 320, 120, seed=12, width=7)
            D.draw_label(p, 'maybe a real world', center=(640, 660),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(world))

    elif beat_id == 'two_things_same_pixels':
        def two_things(p):
            d = ImageDraw.Draw(p)
            S.swatch(p, 340, 240, 200, 200, S.C['rock_dk'], label='dust')
            S.swatch(p, 740, 240, 200, 200, S.C['rock'], label='world')
            D.draw_label(p, 'same light. two very different things.',
                         center=(640, 560), color=T.LABEL_RED, size=40)
        L.append(E.pop(0.0)(two_things))

    elif beat_id == 'the_orbit':
        def orbit(p):
            d = ImageDraw.Draw(p)
            S.star(d, 320, 420, 110, seed=13, col=S.C['star'])
            # a wide eccentric orbit
            S.orbit_path(d, 640, 420, 520, 200, seed=14, width=7)
            S.planet(d, 1160, 420, 40, base='rock', seed=15)
            D.draw_label(p, 'it swings in close', center=(700, 640),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(orbit))

    elif beat_id == 'orbit_not_tidy':
        def not_tidy(p):
            d = ImageDraw.Draw(p)
            S.star(d, 400, 400, 120, seed=16, col=S.C['star'])
            S.orbit_path(d, 640, 400, 480, 200, seed=17, width=7)
            S.planet(d, 1120, 400, 40, base='rock', seed=18)
            D.draw_label(p, 'that wild does not stay tidy', center=(640, 650),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(not_tidy))

    elif beat_id == 'one_bad_pass':
        def bad_pass(p):
            d = ImageDraw.Draw(p)
            S.star(d, 340, 400, 140, seed=19, col=S.C['star_hot'])
            S.planet(d, 900, 400, 46, base='rock_dk', seed=20)
            D.draw_arrow(p, (480, 400), (820, 400), color=T.RED)   # one hard nudge
            D.draw_label(p, 'one bad pass', center=(640, 650),
                         color=T.LABEL_RED, size=48)
        L.append(E.pop(0.0)(bad_pass))

    elif beat_id == 'the_long_fall':
        def long_fall(p):
            d = ImageDraw.Draw(p)
            S.star(d, 240, 240, 90, seed=21, col=S.C['star'])
            S.planet(d, 980, 520, 44, base='rock_dk', seed=22)
            D.draw_arrow(p, (900, 460), (1120, 580), width=10, head=40)
            D.draw_label(p, 'a long, silent fall', center=(640, 660),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(long_fall))

    elif beat_id == 'cloud_world_or_gone':
        def closing(p):
            d = ImageDraw.Draw(p)
            S.orbit_path(d, 640, 400, 520, 170, seed=23, width=7)
            S.planet(d, 1020, 400, 40, base='rock', seed=24)
            D.draw_label(p, 'a cloud. a world. or gone.', center=(640, 650),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(closing))
        L.append(E.pop(_rel_any(ctx, beat_id, 'cloud', 'world', 'gone'))(
            lambda p: _char(p, 240, 700, 320, 'deadpan_grim', 'shrugged')))

    else:
        L.append(E.pop(0.0)(lambda p: _star_and_ring(p, seed=0)))

    return E.sort_layers(L)
