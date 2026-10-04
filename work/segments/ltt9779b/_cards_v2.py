# ltt9779b/_cards_v2.py -- the v2 card layers for LTT 9779 b, the super-Earth
# with a metallic sky and a permanent gleam (brightest reflective world).
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - through-line: a normally-dull rocky world turned MIRROR-BRIGHT by a
#     metallic cloud deck, the "coin in the dark" image, then the unsettling
#     idea that the hottest worlds should be ovens but this one gleams.
#   - our stickman reacts with the "smiling" reveal.

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


def _gleaming(p, cx=640, cy=380, r=250, seed=0, base='rock'):
    """The signature image: a rocky world with a bright mirror sheen band.

    The sheen is a gold ellipse ARC across the disc (clipped to the circle) so
    it reads as a reflective cloud deck catching starlight, not a painted stripe.
    """
    d = ImageDraw.Draw(p)
    S.planet(d, cx, cy, r, base=base, seed=seed)
    # a bright reflective cloud-deck band, clipped to the disc by a mask
    import PIL.Image as I, PIL.ImageDraw as ID
    sz = int(2 * r) + 8
    mask = I.new('L', (sz, sz), 0)
    ID.Draw(mask).ellipse([4, 4, sz - 4, sz - 4], fill=255)
    band = I.new('RGB', (sz, sz), S.C['gold'])
    ID.Draw(band).ellipse([10, int(r * 0.95), sz - 10, int(r * 1.35)], fill=S.C['gold'])
    p.paste(band, (int(cx - r) - 4, int(cy - r) - 4), mask)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook_inverted':
        def inverted(p):
            d = ImageDraw.Draw(p)
            S.star(d, 320, 360, 110, seed=1, col=S.C['star'])
            S.planet(d, 880, 360, 150, base='rock', seed=2)
            D.draw_arrow(p, (470, 360), (700, 360))
            D.draw_red_x(p, (700, 300, 780, 420), width=8)   # light should NOT come back
            D.draw_label(p, 'it does not swallow the light', center=(640, 620),
                         color=T.LABEL_RED, size=42)
        L.append(E.pop(0.0)(inverted))

    elif beat_id == 'name_card':
        def name(p):
            d = ImageDraw.Draw(p)
            S.star(d, 300, 400, 100, seed=3, col=S.C['star'])
            S.planet(d, 900, 400, 190, base='rock', seed=4)
            D.draw_label(p, 'a super-Earth with a gleam', center=(640, 660),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(name))

    elif beat_id == 'planet_is_loud':
        def loud(p):
            d = ImageDraw.Draw(p)
            _gleaming(p, cx=640, cy=380, r=250, seed=5)
            D.draw_number(p, 'BRIGHT', (640, 660), size=88, color=T.RED)
        L.append(E.pop(0.0)(loud))

    elif beat_id == 'metal_sky':
        def metal_sky(p):
            d = ImageDraw.Draw(p)
            _gleaming(p, cx=640, cy=400, r=240, seed=6)
            D.draw_label(p, 'a sky made of metal', center=(640, 660),
                         color=T.LABEL_BLUE, size=46)
        L.append(E.pop(0.0)(metal_sky))

    elif beat_id == 'irradiated_dayside':
        def irradiated(p):
            d = ImageDraw.Draw(p)
            S.star(d, 260, 400, 120, seed=7, col=S.C['star_hot'])
            for i in range(4):
                D.draw_arrow(p, (420, 340 + i * 40), (620, 340 + i * 40),
                             color=T.RED, width=8, head=30)
            S.planet(d, 900, 400, 190, base='rock', seed=8)
            D.draw_label(p, 'baked, continuously', center=(640, 660),
                         color=T.LABEL_RED, size=42)
        L.append(E.pop(0.0)(irradiated))

    elif beat_id == 'nothing_absorbed':
        def nothing_absorbed(p):
            d = ImageDraw.Draw(p)
            # a bar of incoming light with almost none absorbed
            S.bar(d, 240, 300, 1040, 420, 0.04, seed=9, fill=S.C['gold'])
            D.draw_label(p, 'light in', center=(240, 270), color=T.LABEL_INK, size=36)
            D.draw_label(p, 'absorbed? this sliver', center=(640, 520),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(nothing_absorbed))

    elif beat_id == 'coin_in_the_dark':
        def coin(p):
            d = ImageDraw.Draw(p)
            # a bright mirror sphere, catching everything, like a coin on a table
            _gleaming(p, cx=560, cy=400, r=230, seed=10)
            for k in range(4):                     # specular glints on the sheen
                gx = 430 + k * 90
                d.ellipse([gx, 380, gx + 34, 414], fill=T.PAPER, outline=T.INK, width=4)
            D.draw_label(p, 'a coin in the dark', center=(980, 620),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(coin))

    elif beat_id == 'the_bad_number':
        def bad_number(p):
            d = ImageDraw.Draw(p)
            # Was a lone "2 / times re-checked" on white -- the blind critic
            # read it as a bare slide. The reference carries its beats with a
            # big reacting character, so the fact moves left and a skeptical
            # co-star close-up carries "did not believe it" on the right.
            D.draw_number(p, '2', (400, 330), size=150, color=T.RED)
            D.draw_label(p, 'times', center=(400, 470),
                         color=T.LABEL_YELLOW, size=44)
            D.draw_label(p, 're-checked', center=(400, 524),
                         color=T.LABEL_YELLOW, size=40)
            S.character_closeup(p, 930, 360, 470, expression='skeptical', seed=3)
        L.append(E.pop(0.0)(bad_number))

    elif beat_id == 'checked_twice':
        def checked(p):
            d = ImageDraw.Draw(p)
            _gleaming(p, cx=640, cy=380, r=250, seed=11)
            D.draw_label(p, 'one of the most reflective worlds',
                         center=(640, 660), color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(checked))

    elif beat_id == 'should_be_an_oven':
        def oven(p):
            d = ImageDraw.Draw(p)
            S.lava_planet(d, 640, 380, 240, seed=12)       # what a hot world should be
            D.draw_label(p, 'the hottest worlds should be ovens',
                         center=(640, 660), color=T.LABEL_RED, size=40)
        L.append(E.pop(0.0)(oven))

    elif beat_id == 'smile_at_mild_star':
        def smile(p):
            d = ImageDraw.Draw(p)
            S.star(d, 320, 380, 100, seed=13, col=S.C['star'])   # a MILD star
            _gleaming(p, cx=920, cy=420, r=190, seed=14)
            D.draw_label(p, 'this one is smiling', center=(640, 660),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(smile))
        L.append(E.pop(_rel(ctx, beat_id, 'smiling'))(
            lambda p: _char(p, 200, 700, 300, 'smile', 'shrugged')))

    elif beat_id == 'brilliant_and_bare':
        def brilliant(p):
            d = ImageDraw.Draw(p)
            _gleaming(p, cx=640, cy=400, r=250, seed=15)
            D.draw_label(p, 'brilliant. and bare.', center=(640, 660),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(brilliant))

    elif beat_id == 'no_survival':
        def no_survival(p):
            d = ImageDraw.Draw(p)
            _gleaming(p, cx=640, cy=400, r=240, seed=16)
            D.draw_label(p, 'no breath up there', center=(640, 660),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(no_survival))

    elif beat_id == 'borrowed_light':
        def borrowed(p):
            d = ImageDraw.Draw(p)
            S.star(d, 240, 240, 80, seed=17, col=S.C['star'])   # a distant sun
            _gleaming(p, cx=840, cy=420, r=200, seed=18)
            D.draw_arrow(p, (360, 260), (620, 400))              # borrowed light
            D.draw_label(p, "it's borrowing its light", center=(640, 660),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(borrowed))

    else:
        L.append(E.pop(0.0)(lambda p: _gleaming(p, seed=0)))

    return E.sort_layers(L)
