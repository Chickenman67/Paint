# psrb1257/_cards_v2.py -- the v2 card layers for PSR B1257+12, the planets
# orbiting a dead star. The first exoplanets ever found around a pulsar.
#
# Follows the koi55 reference shape (build_beat -> [Layer, ...]).
#   - the DOMINANT subject fills the frame (CLAUDE.md §7 FRAME-FILL).
#   - one idea per beat; short in-frame text only (label / number / bubble).
#   - through-line: a star that died and kept spinning, a beam sweeping the
#     dark twice a second, and planets that should not exist going round it.
#   - the subject is a PULSAR (v2subjects.pulsar), never `star()` -- a pulsar
#     is a point of light the size of a city, and drawing it as a normal star
#     made this segment indistinguishable from the other nine.
#   - our stickman (light theme) shields his eyes from the beam, then shrugs.

import os
import sys

import math
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
    0.0 is falsy -- so the obvious `_rel(a) or _rel(b)` idiom is unreliable.
    """
    off = kw.get('offset', 0.0)
    for w in words:
        for ww in ctx.words_by_beat.get(ctx.beat_by_id[beat_id]['n'], []):
            if w.lower() in ww['w'].lower():
                return max(0.0, ctx.when(beat_id, w, off) - ctx.beat_start(beat_id))
    return 0.0


def _char(p, x, foot_y, h, expr, pose):
    S.character(p, x, foot_y, h, expression=expr, pose=pose)


def _dead_star(p, cx=640, cy=380, r=60, seed=0, beams=0, blur=True, beam_len=520):
    """The signature image: the dead star. `beams=0` for the silent beats."""
    d = ImageDraw.Draw(p)
    S.pulsar(d, cx, cy, r=r, seed=seed, beams=beams, beam_len=beam_len,
             blur=blur)


# The beats -------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []

    if beat_id == 'hook_dead_star':
        def died(p):
            d = ImageDraw.Draw(p)
            _dead_star(p, cx=640, cy=360, r=58, seed=1, blur=True)
            D.draw_label(p, 'this star died', center=(640, 560),
                         color=T.LABEL_RED, size=52)
            D.draw_label(p, 'it is still spinning', center=(640, 622),
                         color=T.LABEL_INK, size=44)
        L.append(E.pop(0.0)(died))
        L.append(E.pop(_rel(ctx, beat_id, 'spinning'))(
            lambda p: _char(p, 1130, 700, 300, 'deadpan_grim', 'hands_down')))

    elif beat_id == 'spinning_fast':
        def smear(p):
            d = ImageDraw.Draw(p)
            # a big halo stack: the "smear of light" idea at full frame scale.
            # Ink, not white -- a white halo on a white page is invisible. Thin
            # rings, and pulled below the title strip so they don't collide.
            for k, rr in enumerate([250, 195, 145, 100]):
                d.ellipse([640 - rr, 400 - rr, 640 + rr, 400 + rr],
                          outline=T.INK, width=max(4, 16 - k * 4))
            d.ellipse([640 - 58, 400 - 58, 640 + 58, 400 + 58],
                      fill=T.INK, outline=T.INK, width=6)
            d.ellipse([640 - 20, 400 - 20, 640 + 20, 400 + 20],
                      fill=S.C['white'], outline=T.INK, width=4)
            D.draw_label(p, 'a smear of light', center=(640, 640),
                         color=T.LABEL_RED, size=48)
        L.append(E.pop(0.0)(smear))

    elif beat_id == 'beam_sweeps':
        def beam(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 640, 380, r=54, seed=3, beams=2, beam_len=560,
                     blur=False)
            D.draw_label(p, 'a beam, twice a second', center=(640, 660),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(beam))
        L.append(E.pop(_rel_any(ctx, beat_id, 'twice', 'second'))(
            lambda p: _char(p, 1120, 700, 300, 'terrified', 'shielding_eyes')))

    elif beat_id == 'planets_around':
        def planets(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 640, 380, r=48, seed=4, beams=0, blur=False)
            for k, rr in enumerate([250, 175]):
                S.orbit_path(d, 640, 380, rr, rr * 0.92, seed=4 + k, width=6)
            S.planet(d, 890, 380, 46, base='rock_dk', seed=6)
            S.planet(d, 465, 300, 34, base='rock_dk', seed=7)
            D.draw_label(p, 'planets. still there.', center=(640, 660),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(planets))

    elif beat_id == 'named_undead':
        def name(p):
            d = ImageDraw.Draw(p)
            D.draw_number(p, 'DRAUGR', (640, 330), size=96, color=T.RED)
            D.draw_label(p, 'the first one is called that', center=(640, 430),
                         color=T.LABEL_INK, size=40)
        L.append(E.pop(0.0)(name))
        L.append(E.pop(_rel(ctx, beat_id, 'Draugr'))(
            lambda p: _char(p, 250, 700, 320, 'worried', 'shrugged')))

    elif beat_id == 'draugr_corpse':
        def corpse(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 470, 400, 220, base='rock_dk', seed=10)
            D.draw_red_box(p, (250, 180, 690, 620), width=9)   # a coffin
            D.draw_label(p, 'a corpse that walks', center=(980, 400),
                         color=T.LABEL_RED, size=48)
            D.draw_label(p, 'that is the name', center=(980, 470),
                         color=T.LABEL_INK, size=40)
        L.append(E.pop(0.0)(corpse))

    elif beat_id == 'named_all_of_them':
        def all_names(p):
            d = ImageDraw.Draw(p)
            for k, nm in enumerate(['DRAUGR', 'POLTERGEIST', 'LICH']):
                D.draw_number(p, nm, (250 + k * 390, 330), size=54, color=T.RED)
            D.draw_label(p, 'it does not get kinder', center=(640, 520),
                         color=T.LABEL_INK, size=44)
        L.append(E.pop(0.0)(all_names))

    elif beat_id == 'first_around_dead':
        def firstever(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 640, 400, r=52, seed=12, beams=0, blur=True)
            S.orbit_path(d, 640, 400, 300, 250, seed=13, width=6)
            S.planet(d, 930, 400, 40, base='rock_dk', seed=14)
            D.draw_red_box(p, (300, 120, 980, 660), width=8)
            D.draw_label(p, 'the first ever found', center=(640, 692),
                         color=T.LABEL_YELLOW, size=40)
        L.append(E.pop(0.0)(firstever))

    elif beat_id == 'should_not_exist':
        def notexist(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 400, 210, base='rock_dk', seed=15)
            # a broken, sagging orbit that fades out -- nothing is holding it
            S.orbit_path(d, 640, 400, 330, 210, seed=16, width=6, dashed=True)
            D.draw_red_x(p, (520, 280, 760, 520), width=11)
            D.draw_label(p, 'nothing left to hold on to', center=(640, 668),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(notexist))

    elif beat_id == 'carbon_dense':
        def carbon(p):
            d = ImageDraw.Draw(p)
            # A flat featureless disc with an arrow pointing into nothing did not
            # say "carbon" or "densest". Give it a scorched carbon texture, put
            # the "look here" pen on the material, and stack the two words BELOW
            # the subject so nothing lands on the disc face.
            S.cracked_rock(d, 640, 330, 215, seed=17, base='rock_dk')
            D.draw_red_box(p, (400, 95, 880, 565), width=9)
            D.draw_number(p, 'DENSEST', (640, 622), size=58, color=T.RED)
            D.draw_label(p, 'carbon, all the way through', center=(640, 682),
                         color=T.LABEL_YELLOW, size=38)
        L.append(E.pop(0.0)(carbon))

    elif beat_id == 'fist_of_coal':
        def coal(p):
            d = ImageDraw.Draw(p)
            S.planet(d, 640, 390, 240, base='rock_dk', seed=18)
            D.draw_red_box(p, (600, 350, 700, 440), width=8)   # a fist, for scale
            D.draw_label(p, 'a fist of coal', center=(640, 680),
                         color=T.LABEL_YELLOW, size=46)
        L.append(E.pop(0.0)(coal))

    elif beat_id == 'orbits_tight':
        def tight(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 640, 400, r=50, seed=19, beams=0, blur=False)
            S.orbit_path(d, 640, 400, 150, 150, seed=20, width=7)
            S.planet(d, 790, 400, 40, base='rock_dk', seed=21)
            D.draw_label(p, 'a couple of hours each', center=(640, 660),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(tight))

    elif beat_id == 'solar_system_size':
        def size_of_ours(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 640, 400, r=44, seed=22, beams=0, blur=False)
            S.orbit_path(d, 640, 400, 230, 190, seed=23, width=6)
            S.planet(d, 860, 400, 32, base='rock_dk', seed=24)
            D.draw_red_box(p, (350, 150, 930, 650), width=8)
            D.draw_label(p, 'about our size', center=(640, 690),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(size_of_ours))

    elif beat_id == 'graveyard':
        def graveyard(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 400, 380, r=54, seed=25, beams=0, blur=True)
            for k in range(4):
                a = k * math.pi / 4
                S.planet(d, 400 + 210 * math.cos(a), 380 + 150 * math.sin(a),
                         34, base='rock_dk', seed=26 + k)
            D.draw_label(p, 'a graveyard, in the dark', center=(880, 400),
                         color=T.LABEL_RED, size=46)
        L.append(E.pop(0.0)(graveyard))
        L.append(E.pop(_rel(ctx, beat_id, 'graveyard'))(
            lambda p: _char(p, 1000, 700, 320, 'frown', 'hands_down')))

    elif beat_id == 'outro_beam':
        def outro(p):
            d = ImageDraw.Draw(p)
            S.pulsar(d, 400, 380, r=52, seed=30, beams=2, beam_len=420,
                     beam_half=30, blur=False)
            _char(p, 1050, 700, 320, 'flat', 'shrugged')
            D.draw_label(p, 'the planets keep going', center=(700, 640),
                         color=T.LABEL_YELLOW, size=42)
        L.append(E.pop(0.0)(outro))

    else:
        L.append(E.pop(0.0)(lambda p: _dead_star(p, seed=0)))

    return E.sort_layers(L)
