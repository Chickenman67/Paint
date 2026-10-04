# koi55/_cards_v2.py -- the v2 card layers for KOI-55.
#
# This is the REFERENCE card module for the v2 rebuild. Every other segment
# follows its shape:
#
#   build_beat(beat_id, ctx) -> [v2engine.Layer, ...]
#
# Each Layer pops its element in FULLY FORMED at a beat-relative time and holds
# (STYLE_CANON2 §4). Pop times are authored against SPOKEN WORDS via ctx.when()
# so the picture changes when the narrator says the thing -- the CLAUDE.md §5
# audio-visual alignment fix. No fades, no tween verbs, no idling.
#
# Visual grammar (all on the near-white page, 6px black ink, flat fills):
#   - a DOMINANT subject that fills the frame (CLAUDE.md §7 FRAME-FILL): the
#     planet or star is the subject, not a prop in an empty field.
#   - short in-frame text ONLY: a yellow/red label, a big number, or a speech
#     bubble -- never a narration line (STYLE_CANON2 §6).
#   - our stickman (theme='light') in at least one beat, with the segment's
#     emotion readable from his face alone.
#   - red marker arrows / boxes / X as the "look here" pen.

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


# ---------------------------------------------------------------------------
# reusable beat pieces (shared shape, per-beat data) -- one idea per card
# ---------------------------------------------------------------------------

def _beat_scene(draw_star=True, planet_base='rock', light=True, seed=0):
    """The scene furniture: star at left, planet on a close orbit at right."""
    def f(page):
        d = ImageDraw.Draw(page)
        if draw_star:
            S.star(d, 250, 340, 96, seed=seed, col=S.C['star_hot'])
        if light:
            S.split_planet(d, 930, 340, 150, light_dir=(-1, 0), seed=seed + 1)
        else:
            S.planet(d, 930, 340, 150, base=planet_base, seed=seed + 1)
    return f


# ---------------------------------------------------------------------------
# the 12 beats
# ---------------------------------------------------------------------------

def build_beat(beat_id, ctx):
    L = []          # layers, each (draw_fn, t0)

    if beat_id == 'hook_closest_orbit':
        # "closer to its star than any planet we have found"
        def scene(p):
            d = ImageDraw.Draw(p)
            S.star(d, 300, 420, 130, seed=10, col=S.C['star_hot'])
            S.split_planet(d, 980, 400, 210, light_dir=(-1, 0), seed=11)
            D.draw_arrow(p, (470, 420), (740, 410), width=10, head=36)
        L.append(E.pop(0.0)(scene))
        L.append(E.pop(_rel(ctx, beat_id, 'closer') - 0.0)(
            lambda p: _split_label(p)))
        L.append(E.pop(_rel(ctx, beat_id, 'any'))(
            lambda p: _side_number(p, 640, 200, 'CLOSEST', 'we have found')))

    elif beat_id == 'hook_five_hours':
        # one year = 5h40m; sunrise/noon/sunset gone, over and over
        def clock(p):
            d = ImageDraw.Draw(p)
            S.star(d, 1050, 300, 80, seed=20, col=S.C['star_hot'])
            S.split_planet(d, 1050, 470, 90, light_dir=(-1, 0), seed=21)
            D.draw_number(p, '5h 40m', (430, 300), size=140)
            D.draw_label(p, 'one whole year', center=(430, 430), color=T.LABEL_YELLOW, size=44)
        L.append(E.pop(0.0)(clock))
        L.append(E.pop(_rel(ctx, beat_id, 'Sunrise'))(
            lambda p: _cycle_strip(p, 'sunrise  noon  sunset  gone')))

    elif beat_id == 'hook_breath':
        # the star swings around before the sentence ends; whole life in a breath
        def breath(p):
            d = ImageDraw.Draw(p)
            S.star(d, 700, 340, 140, seed=30, col=S.C['star_hot'])
            D.draw_number(p, 'ONE BREATH', (640, 580), size=64)
            D.draw_label(p, 'and that is a whole life', center=(640, 640),
                         color=T.LABEL_YELLOW, size=38)
        L.append(E.pop(0.0)(breath))
        L.append(E.pop(_rel(ctx, beat_id, 'breath'))(
            lambda p: S_character(p, 200, 700, 330, 'terrified', 'shielding_eyes')))

    elif beat_id == 'bare_rock_world':
        # bare rock, no air/ocean/weather; charred shell, dead core
        def rock(p):
            d = ImageDraw.Draw(p)
            S.cracked_rock(d, 400, 400, 210, seed=40, base='rock_dk')
            D.draw_bubble(p, 'no air. no ocean. no weather.', (760, 200),
                          tail_to=(560, 320))
        L.append(E.pop(0.0)(rock))
        L.append(E.pop(_rel(ctx, beat_id, 'charred'))(
            lambda p: _side_number(p, 960, 460, 'CHARRED', 'dead core')))

    elif beat_id == 'the_boiling':
        # enormous close hot star; boiling it since they formed; air taken off
        def boil(p):
            d = ImageDraw.Draw(p)
            S.star(d, 300, 360, 200, seed=50, col=S.C['star_hot'], spike_len=1.8)
            S.planet(d, 980, 360, 130, base='rock_dk', seed=51)
            D.draw_arrow(p, (500, 360), (820, 360))
            D.draw_label(p, 'boiling since day one', center=(660, 470), color=T.LABEL_RED)
        L.append(E.pop(0.0)(boil))
        L.append(E.pop(_rel(ctx, beat_id, 'atmosphere'))(
            lambda p: _atmosphere_off(p)))

    elif beat_id == 'melted_and_hardened':
        # melted, drained, hardened; a cinder, nothing closer in the catalog
        def cinder(p):
            d = ImageDraw.Draw(p)
            S.lava_planet(d, 400, 400, 220, seed=60)
        L.append(E.pop(0.0)(cinder))
        L.append(E.pop(_rel(ctx, beat_id, 'cinder'))(
            lambda p: _side_number(p, 950, 380, 'A CINDER', 'nothing closer')))

    elif beat_id == 'how_we_found_it':
        # Kepler only saw a shadow, a dip; KOI-55 is just a number
        def dip(p):
            d = ImageDraw.Draw(p)
            # star with a planet crossing it, and a light curve
            S.star(d, 400, 300, 120, seed=70, col=S.C['star'])
            S.planet(d, 400, 300, 34, base='rock_dk', seed=71)
            D.draw_arrow(p, (700, 300), (470, 300))
            D.draw_label(p, 'the shadow it cast', center=(760, 250), color=T.LABEL_RED)
        L.append(E.pop(0.0)(dip))
        L.append(E.pop(_rel(ctx, beat_id, 'number'))(
            lambda p: _number_only(p, 'KOI-55', 'just a catalogue number')))
        L.append(E.pop(_rel(ctx, beat_id, 'name'))(
            lambda p: S_character(p, 1090, 700, 300, 'flat', 'shrugged')))

    elif beat_id == 'the_spiral_in':
        # falling inward, orbit after orbit; nothing left underneath
        def spiral(p):
            d = ImageDraw.Draw(p)
            S.star(d, 640, 360, 150, seed=80, col=S.C['star_hot'])
            # three tightening orbits with a planet on each
            for k, rr in enumerate([520, 380, 250]):
                S.orbit_path(d, 640, 360, rr, rr * 0.55, seed=80 + k)
            S.planet(d, 640 + 250, 360, 40, base='rock_dk', seed=90)
        L.append(E.pop(0.0)(spiral))
        L.append(E.pop(_rel(ctx, beat_id, 'underneath'))(
            lambda p: D.draw_label(p, 'nothing left to fall toward', center=(640, 660),
                                   color=T.LABEL_RED, size=48)))

    elif beat_id == 'it_survived_being_eaten':
        # may already have been swallowed once; already survived being eaten
        def eaten(p):
            d = ImageDraw.Draw(p)
            S.star(d, 640, 400, 240, seed=100, col=S.C['star_hot'], spike_len=1.6)
            D.draw_red_box(p, (420, 250, 860, 550), width=9)
            D.draw_label(p, 'already inside the star?', center=(640, 660),
                        color=T.LABEL_RED, size=52)
        L.append(E.pop(0.0)(eaten))
        L.append(E.pop(_rel(ctx, beat_id, 'survived'))(
            lambda p: S_character(p, 1040, 700, 320, 'terrified', 'cowering')))

    elif beat_id == 'disturbing_part':
        # not that it dies -- that it is allowed to die twice
        def twice(p):
            d = ImageDraw.Draw(p)
            # Was a lone "TWICE" numeral. The reference carries its beats with a
            # big reacting character, so the word moves left and a co-star
            # carries the "that is the disturbing part" reaction on the right.
            D.draw_number(p, 'TWICE', (400, 340), size=150, color=T.RED)
            D.draw_label(p, 'not that it dies', center=(400, 470),
                         color=T.LABEL_YELLOW, size=42)
            D.draw_label(p, 'that it can die twice', center=(400, 522),
                         color=T.LABEL_YELLOW, size=38)
            S.character_closeup(p, 950, 370, 460, expression='terrified', seed=4)
        L.append(E.pop(0.0)(twice))

    elif beat_id == 'the_last_pass':
        # the next pass will not be a pass; it will be the last one
        def last(p):
            d = ImageDraw.Draw(p)
            S.star(d, 900, 360, 210, seed=110, col=S.C['star_hot'], spike_len=1.7)
            S.orbit_path(d, 900, 360, 420, 240, seed=111)
            S.planet(d, 480, 360, 46, base='rock_dk', seed=112)
            D.draw_red_x(p, (430, 310, 530, 410), width=9)
            D.draw_label(p, 'not a pass -- the last one', center=(430, 500),
                         color=T.LABEL_RED, size=44)
        L.append(E.pop(0.0)(last))

    elif beat_id == 'outro_cinder':
        # KOI-55, five hours forty minutes a year; one fall left
        def outro(p):
            d = ImageDraw.Draw(p)
            S.star(d, 640, 300, 150, seed=120, col=S.C['star_hot'])
            S.planet(d, 640, 520, 70, base='rock_dk', seed=121)
            D.draw_number(p, 'ONE FALL LEFT', (640, 660), size=56)
        L.append(E.pop(0.0)(outro))
        L.append(E.pop(_rel(ctx, beat_id, 'nothing'))(
            lambda p: S_character(p, 1080, 700, 310, 'deadpan_grim', 'hands_down')))

    else:
        # fallback: the scene, so nothing renders empty
        L.append(E.pop(0.0)(_beat_scene(seed=0)))

    return E.sort_layers(L)


# ---------------------------------------------------------------------------
# small element painters used above
# ---------------------------------------------------------------------------

def _split_label(p):
    d = ImageDraw.Draw(p)
    D.draw_label(p, 'closer than any we have found', center=(640, 560),
                 color=T.LABEL_YELLOW, size=44)


def S_character(p, x, foot_y, height, expression, pose):
    S.character(p, x, foot_y, height, expression=expression, pose=pose)


def _big_number(p, word, sub, y=250, color=None, size=104):
    """A big number doing the talking, with the sub-label clearly below it.

    y is the number's CENTRE. Keep it in a clear band (top third, or a side),
    not over a centred subject -- the first pass drew these at y=280-300 with a
    subject also at cy~380, so the number sat on top of the art.
    """
    D.draw_number(p, word, (640, y), size=size, color=color)
    D.draw_label(p, sub, center=(640, y + 110), color=T.LABEL_YELLOW, size=40)


def _side_number(p, cx, cy, word, sub, size=76):
    """A big number in a SIDE column, so it never lands on a centred subject."""
    D.draw_number(p, word, (cx, cy), size=size)
    D.draw_label(p, sub, center=(cx, cy + 80), color=T.LABEL_YELLOW, size=36)


def _number_only(p, word, sub):
    d = ImageDraw.Draw(p)
    D.draw_number(p, word, (640, 340), size=120)
    D.draw_label(p, sub, center=(640, 460), color=T.LABEL_YELLOW, size=40)


def _cycle_strip(p, text):
    d = ImageDraw.Draw(p)
    D.draw_label(p, text, center=(430, 560), color=T.LABEL_RED, size=40)


def _atmosphere_off(p):
    d = ImageDraw.Draw(p)
    S.atmosphere_tail(d, 980, 360, 120, 260, seed=52, direction=(1, 0))
    D.draw_label(p, 'air stripped away', center=(1000, 520), color=T.LABEL_RED)
