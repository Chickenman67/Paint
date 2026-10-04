# psoj3185/_cards_v2.py -- the v2 card layers for PSO J318.5-22, the rogue planet
# cast out of its system, drifting alone, lit only by borrowed light.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - through-line: the ejection, the drift into the dark, no light of its own,
#     the cold, the dust ring from a dead system, and the loneliest close.
#   - the character is alone and small in a big empty frame for the loneliness
#     beats, then the "never know you" close.

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


def _rogue(p, cx=640, cy=400, r=220, seed=0):
    """The signature image: the lone planet, a cold dark disc, alone on the page."""
    d = ImageDraw.Draw(p)
    S.planet(d, cx, cy, r, base='night', seed=seed)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook_a_sun_you_know':
        def with_sun(p):
            d = ImageDraw.Draw(p)
            S.star(d, 340, 380, 120, seed=1, col=S.C['star'])
            S.planet(d, 940, 380, 150, base='rock', seed=2)
            D.draw_label(p, 'every planet had a sun', center=(640, 640),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(with_sun))

    elif beat_id == 'ejection_neighbor_comes_too_close':
        def ejected(p):
            d = ImageDraw.Draw(p)
            S.star(d, 260, 400, 130, seed=3, col=S.C['star_hot'])
            S.planet(d, 980, 400, 60, base='rock', seed=4)
            D.draw_arrow(p, (700, 400), (1160, 300), color=T.RED, width=12, head=48)
            D.draw_label(p, 'something kicked it out', center=(640, 640),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(ejected))

    elif beat_id == 'thrown_into_the_between':
        def between(p):
            d = ImageDraw.Draw(p)
            _rogue(p, cx=980, cy=380, r=160, seed=5)
            D.draw_arrow(p, (300, 400), (760, 400))         # drifting away
            D.draw_label(p, 'loose into the dark', center=(500, 200),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(between))

    elif beat_id == 'no_star_to_orbit':
        def no_star(p):
            d = ImageDraw.Draw(p)
            # Was one grey disc centred on the page. The point of this beat is
            # that there is NOTHING to orbit, so it now drifts among three
            # unrelated stars -- and deliberately has no orbit path at all,
            # while every star sits bare. The missing line is the idea.
            S.star(d, 250, 300, 90, seed=21, col=S.C['star'])
            S.star(d, 1040, 280, 70, seed=22, col=S.C['star'])
            S.star(d, 660, 220, 60, seed=23, col=S.C['star'])
            _rogue(p, cx=620, cy=470, r=150, seed=6)
            D.draw_label(p, 'nothing to orbit', center=(640, 668),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(no_star))

    elif beat_id == 'no_light_of_its_own':
        def no_light(p):
            d = ImageDraw.Draw(p)
            _rogue(p, cx=640, cy=400, r=220, seed=7)
            D.draw_number(p, 'NO LIGHT', (640, 660), size=76, color=T.RED)
        L.append(E.pop(0.0)(no_light))
        L.append(E.pop(_rel(ctx, beat_id, 'lit'))(
            lambda p: D.draw_label(p, "it's borrowing other stars' light",
                                   center=(640, 240), color=T.LABEL_YELLOW, size=38)))

    elif beat_id == 'barely_enough_to_see':
        def barely(p):
            d = ImageDraw.Draw(p)
            S.star(d, 200, 200, 60, seed=8, col=S.C['star'])    # impossibly far
            _rogue(p, cx=900, cy=460, r=160, seed=9)
            D.draw_label(p, 'a thin drizzle, from far away', center=(640, 660),
                         color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(barely))

    elif beat_id == 'what_rogue_means':
        def rogue(p):
            d = ImageDraw.Draw(p)
            # Every other world on this page is in a family: a star with an
            # orbit and a planet on it. The rogue sits alone at the far right
            # with no line to anything. The contrast IS the definition.
            S.star(d, 250, 380, 100, seed=31, col=S.C['star'])
            S.orbit_path(d, 250, 380, 175, 150, seed=32, width=6)
            S.planet(d, 250, 380, 34, base='rock', seed=33)
            S.star(d, 610, 380, 80, seed=34, col=S.C['star'])
            S.orbit_path(d, 610, 380, 140, 120, seed=35, width=6)
            S.planet(d, 610, 380, 28, base='rock', seed=36)
            _rogue(p, cx=1010, cy=380, r=150, seed=10)      # no orbit, no parent
            D.draw_label(p, 'no parent star', center=(640, 665),
                         color=T.LABEL_RED, size=48)
        L.append(E.pop(0.0)(rogue))

    elif beat_id == 'coldest_and_darkest':
        def cold(p):
            d = ImageDraw.Draw(p)
            # A small, far, lonely disc is CORRECT here -- the beat is about
            # being the coldest and lowest-gravity thing found, so the disc is
            # deliberately tiny and the mercury is slammed to the bottom. This
            # is the one place a small subject is the point.
            _rogue(p, cx=880, cy=390, r=120, seed=11)
            S.thermometer(d, 330, 600, 340, 0.04, seed=37, hot=False)
            D.draw_number(p, 'COLDEST', (640, 668), size=76, color=T.RED)
        L.append(E.pop(0.0)(cold))

    elif beat_id == 'less_than_darkness':
        def dark(p):
            d = ImageDraw.Draw(p)
            # "not even dark. nothing." -- so the page is mostly EMPTY and the
            # disc is cropped off the left edge, only a sliver of it present.
            # The void is the subject; the planet is almost not there.
            S.planet(d, 90, 400, 210, base='night', seed=12)   # cropped at edge
            D.draw_label(p, 'not even dark. nothing.', center=(760, 640),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(dark))
        L.append(E.pop(_rel(ctx, beat_id, 'standing'))(
            lambda p: _char(p, 1120, 700, 280, 'worried', 'hands_down')))

    elif beat_id == 'the_dust_ring':
        def dust_ring(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 400, 160, base='night', seed=13)
            S.orbit_path(d, 640, 400, 360, 120, seed=14, width=7)
            D.draw_label(p, "a ring of leftovers", center=(640, 660),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(dust_ring))

    elif beat_id == 'a_suns_worth_of_wreckage':
        def wreckage(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 400, 140, base='night', seed=15)
            S.orbit_path(d, 640, 400, 420, 150, seed=16, width=8)
            D.draw_label(p, "a whole sun's worth, in one circle",
                         center=(640, 660), color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(wreckage))

    elif beat_id == 'it_passes_you':
        def passes(p):
            d = ImageDraw.Draw(p)
            _rogue(p, cx=900, cy=380, r=180, seed=17)
            D.draw_arrow(p, (400, 380), (700, 380))          # passing us
            D.draw_label(p, 'it will never know you', center=(640, 620),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(passes))

    elif beat_id == 'the_loneliest_thing_found':
        def loneliest(p):
            d = ImageDraw.Draw(p)
            # The final frame of the whole film, so it has to be the strongest:
            # a BIG disc anchored left-of-centre, the character standing small
            # beside it looking up, and a lot of empty page around both. Big
            # subject + vast emptiness is the whole feeling in one composition.
            S.planet(d, 520, 340, 260, base='night', seed=18)
        L.append(E.pop(0.0)(loneliest))
        L.append(E.pop(_rel(ctx, beat_id, 'loneliest'))(
            lambda p: _char(p, 1010, 690, 300, 'sad_smile', 'hands_down')))
        L.append(E.pop(_rel(ctx, beat_id, 'loneliest', offset=0.35))(
            lambda p: D.draw_number(p, 'ALONE', (640, 655), size=86, color=T.RED)))

    else:
        L.append(E.pop(0.0)(lambda p: _rogue(p, seed=0)))

    return E.sort_layers(L)
