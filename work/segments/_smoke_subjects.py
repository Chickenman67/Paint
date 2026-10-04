# _smoke_subjects.py -- render every v2subjects helper to a contact sheet so the
# primitives can be eyeballed for defects (missing outline, clipped fill, wrong
# scale, an unreadable colour) before any card is authored on top of them.
#
# This is a SELF-CHECK, not a deliverable. Judge art at full res (memory:
# judge-art-at-full-res) -- thumbnails lie about missing/faint elements.

import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))          # .../work
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))

import v2draw as D          # noqa: E402
import v2subjects as S      # noqa: E402

W, H = 1280, 720
OUT = os.path.join(HERE, '..', 'ref2', '_subjects_sheet.png')


def sheet():
    img = D.page()
    d = ImageDraw.Draw(img)
    # ---- row 1: planets
    S.planet(d, 110, 130, 70, base='rock', seed=1)
    S.banded_gas(img, 300, 130, 70, seed=2)
    S.split_planet(d, 480, 130, 70, light_dir=(1, 0), seed=3)
    S.ringed_planet(img, 680, 130, 70, seed=4)
    S.cracked_rock(d, 880, 130, 70, seed=5)
    S.lava_planet(d, 1090, 130, 70, seed=6)
    # ---- row 2: stars / paths / atmosphere
    S.star(d, 110, 320, 46, seed=7)
    S.sun_rays(d, 260, 320, 46, seed=8)
    S.orbit_path(d, 480, 320, 110, 60, seed=9)
    S.atmosphere_tail(d, 700, 320, 40, 170, seed=10, direction=(1, 0))
    S.star_close_and_planet(d, 900, 320, 34, 1050, 320, 26, 130, 70, seed=11)
    S.bar(d, 1080, 300, 1240, 340, 0.7, seed=12, segments=4)
    # ---- row 3: props
    S.thermometer(d, 120, 640, 240, 0.85, seed=13)
    S.gauge(img, 300, 590, 60, 0.35, seed=14, label='fuel')
    S.swatch(img, 420, 520, 120, 90, (40, 40, 40), seed=15, label='coal')
    S.swatch(img, 580, 520, 120, 90, (70, 70, 70), seed=16, label='asphalt')
    S.swatch(img, 740, 520, 120, 90, (18, 18, 22), seed=17, label='this planet')
    # ---- row 4: character poses + expressions + a title + a bubble
    for i, pose in enumerate(sorted(S.SM._POSES)):
        S.character(img, 90 + i * 130, 700, 150, expression='flat', pose=pose, seed=i)
    for i, ex in enumerate(sorted(S.SM.MOUTHS)[:6]):
        S.character(img, 900 + (i % 3) * 110, 620, 120, expression=ex,
                    pose='standing', seed=20 + i)
    D.draw_title(img, 'SUBJECT TEST', seed=99)
    D.draw_label(img, 'a short label', xy=(700, 120), color=D.T.LABEL_YELLOW)
    D.draw_bubble(img, 'nobody believes it', (1150, 480), tail_to=(1100, 560))
    return img


if __name__ == '__main__':
    out = sheet()
    out.save(OUT)
    print('wrote %s  (%dx%d)' % (os.path.abspath(OUT), out.width, out.height))
