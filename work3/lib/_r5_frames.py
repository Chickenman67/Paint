"""Round 5 test-frame harness: renders selected FULL 1280x720 frames only."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'work', 'lib'))

OUT = os.path.join(ROOT, 'work3', 'measure', 'round5_texture')

DEFAULT = [
    # the plume / star collision (Priority 1)
    ('r5_tail',        67.00),
    ('r5_tail_late',   69.20),
    # the finale character close-up (Priority 2 + 3)
    ('r5_finale',      73.00),
    # NEW middle-segment character beats (Priority 2)
    ('r5_char3',       14.00),   # darker_than_coal, new deadpan pose
    ('r5_char6',       30.60),   # never_warms/never_cools, NEW close-up
    ('r5_char7',       34.60),   # day_side_furnace, NEW close-up
    ('r5_char8',       38.00),   # dull_red_glow, new awed pose
    ('r5_char10',      50.00),   # watch_the_star, new looking-up pose
    # painterly planet/star frames that MUST NOT regress
    ('r5_planet',      12.00),
    ('r5_star',        60.50),
]


def main():
    import tres2b_scene as SC
    from engine3 import render_frame
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        picks = []
        i = 0
        while i < len(args):
            picks.append((args[i].replace('.png', ''), float(args[i + 1])))
            i += 2
    else:
        picks = DEFAULT
    scene = SC.build()
    for name, t in picks:
        fr = render_frame(scene, t)
        p = os.path.join(OUT, name + '.png')
        fr.save(p)
        print('%s  t=%.2f  -> %s' % (name, t, p))


if __name__ == '__main__':
    main()
