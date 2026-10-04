"""Render the round-3 test frames for the tres2b segment.

NOT the video -- just single 1280x720 frames at the timestamps where each beat
is fully composed, so the painterly texture, the silhouettes, and the character
close-up can be judged at 1:1. Judging a texture on a thumbnail is how the last
two rounds concluded the texture was "too subtle" when it was fine on a crop and
invisible on the frame.

Usage:  python lib/_r3_frames.py [outdir]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'work', 'lib'))

import engine3 as E3  # noqa: E402

# (filename, time) -- one per beat, chosen to land AFTER the beat's last reveal
# so the frame shows the beat fully composed rather than mid-build.
SHOTS = [
    ('01_hook_dark_planet',        4.20),
    ('02_one_percent',             8.60),
    ('03_darker_than_coal',       16.10),
    ('04_character_pointing',     22.60),
    ('05_two_faces_split',        27.10),
    ('06_thermos',                31.10),
    ('07_lava_furnace',           35.20),
    ('08_dull_red_glow_number',   42.40),
    ('09_character_shrug',        45.50),
    ('10_star_swell',             63.50),
    ('11_atmosphere_tail',        69.50),
    # INSIDE the finale beat's first phrase (70.03 -> 72.30). The old t=75.30
    # was past the phrase's `until`, so the caption was correctly hidden and
    # the close-up frame rendered with no text on it at all.
    ('12_finale_closeup',         71.50),
]


def main():
    import tres2b_scene as SC
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.abspath(os.path.join(HERE, os.pardir)), 'measure', 'round3_texture')
    os.makedirs(outdir, exist_ok=True)
    scene = SC.build()
    for name, t in SHOTS:
        img = E3.render_frame(scene, t)
        p = os.path.join(outdir, name + '.png')
        img.save(p)
        print('%s  t=%.2f  ->  %s' % (name, t, p))
    print('%d frames -> %s' % (len(SHOTS), outdir))


if __name__ == '__main__':
    main()