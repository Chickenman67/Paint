# kelt9b/_cards_v2.py -- the v2 card layers for KELT-9b, the hottest planet ever
# found, hotter than most stars, where atoms unravel on the dayside.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - through-line: a close blue furnace star, the planet baking in its light,
#     the 4600-degree dayside, molecules torn apart, matter unraveling, and no
#     shade to stand in.
#   - the character shields his eyes at the light and gives up at the end.

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


def _blue_furnace(p, cx=300, cy=400, r=190, seed=0):
    d = ImageDraw.Draw(p)
    S.star(d, cx, cy, r, seed=seed, col=S.C['star_hot'])


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook':
        def hottest(p):
            d = ImageDraw.Draw(p)
            _blue_furnace(p, cx=300, cy=400, r=180, seed=1)
            S.planet(d, 960, 400, 150, base='rock', seed=2)
            D.draw_number(p, 'HOTTEST', (640, 660), size=76, color=T.RED)
        L.append(E.pop(0.0)(hottest))

    elif beat_id == 'the_record':
        def record(p):
            d = ImageDraw.Draw(p)
            D.draw_number(p, 'HOTTER THAN', (640, 260), size=64, color=T.RED)
            D.draw_number(p, 'MOST STARS', (640, 360), size=64, color=T.RED)
            D.draw_label(p, 'the word planet rounds it up', center=(640, 500),
                         color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(record))

    elif beat_id == 'the_orbit':
        def orbit(p):
            d = ImageDraw.Draw(p)
            _blue_furnace(p, cx=290, cy=360, r=150, seed=3)
            # ry kept small so the ellipse bottom (600) clears the caption band --
            # at ry=240 the curve ran straight through the label.
            S.orbit_path(d, 600, 380, 420, 220, seed=4, width=7)
            S.planet(d, 1020, 380, 46, base='rock', seed=5)
            D.draw_label(p, 'closer than any planet should', center=(640, 665),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(orbit))

    elif beat_id == 'no_escape':
        def no_escape(p):
            d = ImageDraw.Draw(p)
            # star lifted and shrunk: at cy=400/r=200 the lower rays reached
            # y=710 and the caption ran straight through them.
            _blue_furnace(p, cx=380, cy=330, r=160, seed=6)
            S.planet(d, 1000, 350, 70, base='rock_dk', seed=7)
            D.draw_label(p, 'not survivable for long', center=(640, 670),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(no_escape))

    elif beat_id == 'the_star':
        def blue_star(p):
            d = ImageDraw.Draw(p)
            S.star(d, 640, 400, 220, seed=8, col=S.C['star_hot'], spikes=12,
                   spike_len=1.4, ray_w=2.4)
            D.draw_label(p, 'a blue furnace, spinning fast', center=(640, 660),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(blue_star))

    elif beat_id == 'the_light':
        def light(p):
            d = ImageDraw.Draw(p)
            _blue_furnace(p, cx=260, cy=400, r=140, seed=9)
            for i in range(5):
                D.draw_arrow(p, (420, 320 + i * 40), (620, 320 + i * 40),
                             width=9, head=32)
            S.planet(d, 940, 400, 180, base='rock', seed=10)
            D.draw_label(p, 'a light most stars never give', center=(640, 660),
                         color=T.LABEL_RED, size=40)
        L.append(E.pop(0.0)(light))

    elif beat_id == 'the_dayside':
        def dayside(p):
            d = ImageDraw.Draw(p)
            # planet pushed left and the number moved to the clear right column.
            # At cx=640/r=260 the "4600" at x=860 landed squarely on the disc.
            S.split_planet(d, 470, 400, 280, light_dir=(-1, 0), seed=11)
            D.draw_number(p, '4600', (1000, 350), size=104, color=T.RED)
            D.draw_label(p, 'degrees', center=(1000, 440), color=T.LABEL_YELLOW, size=46)
            D.draw_label(p, 'on the dayside', center=(1000, 500),
                         color=T.LABEL_RED, size=40)
        L.append(E.pop(0.0)(dayside))

    elif beat_id == 'molecules':
        def molecules(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 400, 250, base='rock', seed=12)
            D.draw_red_x(p, (540, 300, 740, 500), width=10)   # bonds breaking
            D.draw_label(p, 'molecules torn apart', center=(640, 660),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(molecules))

    elif beat_id == 'the_warning':
        def warning(p):
            d = ImageDraw.Draw(p)
            # The first pass was type on an empty page -- no subject at all,
            # which fails the FRAME-FILL rule (CLAUDE.md §7). The furnace now
            # owns the left two thirds and the words sit in the right column.
            S.star(d, 330, 400, 250, seed=20, col=S.C['star_hot'], spikes=10,
                   spike_len=1.5, ray_w=2.4)
            D.draw_number(p, 'WARNING', (930, 285), size=76, color=T.RED)
            D.draw_label(p, 'atoms come apart', center=(930, 368),
                         color=T.LABEL_YELLOW, size=40)
            D.draw_label(p, 'on the dayside', center=(930, 424),
                         color=T.LABEL_RED, size=40)
            _char(p, 1170, 700, 240, 'terrified', 'shielding_eyes')
        L.append(E.pop(0.0)(warning))

    elif beat_id == 'unraveling':
        def unraveling(p):
            d = ImageDraw.Draw(p)
            # Atoms FLYING OFF the lit (left) limb, each on a short motion trail.
            # The first pass scattered 20 random red dashes over the whole disc,
            # which read as stray pen marks rather than matter coming apart. The
            # fan is biased up-and-left so no trail crosses the caption band.
            S.split_planet(d, 620, 430, 250, light_dir=(-1, 0), seed=13)
            import math, random as rnd_mod
            rnd = rnd_mod.Random(13)
            for _ in range(14):
                a = math.pi + rnd.uniform(-0.55, 0.75)      # up and to the left
                r0, r1 = 250, 250 + rnd.randint(70, 150)
                x0, y0 = 620 + r0 * math.cos(a), 430 + r0 * math.sin(a)
                x1, y1 = 620 + r1 * math.cos(a), 430 + r1 * math.sin(a)
                d.line([(x0, y0), (x1, y1)], fill=T.RED, width=6)
                d.ellipse([x1 - 11, y1 - 11, x1 + 11, y1 + 11],   # the escaping atom
                          fill=T.RED, outline=T.INK, width=4)
            D.draw_label(p, 'the bonds of matter lose', center=(640, 672),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(unraveling))

    elif beat_id == 'nowhere_cool':
        def nowhere(p):
            d = ImageDraw.Draw(p)
            # planet raised to cy=370 so its lower limb (630) clears the caption
            S.split_planet(d, 660, 370, 255, light_dir=(-1, 0), seed=14)
            D.draw_label(p, 'no ocean. no shade. no cool.',
                         center=(640, 672), color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(nowhere))

    elif beat_id == 'closer':
        def closer(p):
            d = ImageDraw.Draw(p)
            # star lifted so the lower rays clear the caption, and the planet
            # pulled left -- the character used to stand on top of it.
            _blue_furnace(p, cx=320, cy=330, r=165, seed=15)
            S.planet(d, 880, 370, 135, base='rock', seed=16)
            D.draw_label(p, 'you would be generous', center=(640, 655),
                         color=T.LABEL_YELLOW, size=40)
            D.draw_label(p, 'to call it a planet', center=(640, 705),
                         color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(closer))
        L.append(E.pop(_rel(ctx, beat_id, 'generous'))(
            lambda p: _char(p, 1130, 700, 290, 'deadpan_grim', 'hands_down')))

    else:
        L.append(E.pop(0.0)(lambda p: _blue_furnace(p, seed=0)))

    return E.sort_layers(L)
