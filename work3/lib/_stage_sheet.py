# work3/lib/_stage_sheet.py -- contact sheet for eyeballing a converted chapter.
#
# WHY THIS EXISTS
#   Every metric in this project has lied at least once. Caption density counted
#   elements instead of beats; the "distinct image change" metric counted a
#   drifting element as a new picture; the motion profile counted continuous
#   large motion as churn. The ONLY measurement that has never lied is looking
#   at the frame -- which is why the pilot's text pile-ups, the globe that read
#   as a grey sphere, the radio mast that read as a crucifix, and the four
#   seconds of bare backdrop opening were all caught by eye and NOT by a gate.
#
#   So after every chapter conversion, render one representative frame per beat,
#   tile them, and LOOK at it. The gate tells you a number changed; this tells
#   you whether the picture is any good.
#
# USAGE
#   python lib/_stage_sheet.py mezhgorye2            # 6 cols, all beats
#   python lib/_stage_sheet.py mezhgorye2 --cols 5 --scale 380
#   python lib/_stage_sheet.py mezhgorye2 --beats 1,2,3,17,29,30
#
# Notes
#   * Samples each beat a little AFTER its onset (default +0.35s) so the beat's
#     art has actually arrived rather than catching it mid-arrival.
#   * Writes to work3/dbg/ (stable), NOT /tmp -- parallel jobs share /tmp and a
#     temp cleanup deleted a previous session's debug PNGs mid-run.
#   * Scales down for the sheet, but the caption text is checked at full
#     resolution separately: a thumbnail hides both texture and small type, and
#     project memory records judging art at thumbnail size inventing a "missing
#     character" defect that did not exist, and at ship size hiding texture
#     that did. Use --scale 1280 --beats N for a single full-res frame.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine3 as E3  # noqa: E402
import scene_common as SC  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DBG = os.path.join(ROOT, 'dbg')


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    mod_name = argv[0]
    cols = 6
    width = 400
    beats_arg = None
    i = 1
    while i < len(argv):
        if argv[i] == '--cols':
            cols = int(argv[i + 1]); i += 2
        elif argv[i] == '--scale':
            width = int(argv[i + 1]); i += 2
        elif argv[i] == '--beats':
            beats_arg = [int(x) for x in argv[i + 1].split(',')]; i += 2
        else:
            i += 1

    os.makedirs(DBG, exist_ok=True)
    import importlib
    mod = importlib.import_module(mod_name)
    scene = mod.build()
    clock = SC.BeatClock(mod.BEATS)

    if beats_arg:
        want = beats_arg
    else:
        want = [b['n'] if isinstance(b.get('n'), int) else i + 1
                for i, b in enumerate(clock.meta['beats'])]

    tiles = []
    height = int(round(width * E3.H / float(E3.W)))
    for n in want:
        t = clock.at('b%02d' % n, 0) + 0.35
        f = E3.render_frame(scene, t)
        if width != E3.W:
            f = f.resize((width, height), Image.LANCZOS)
        d = ImageDraw.Draw(f)
        d.rectangle([0, 0, 52, 20], fill=(0, 0, 0))
        d.text((4, 3), 'b%02d' % n, fill=(255, 255, 255))
        tiles.append(f)

    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (width * cols, height * rows), (250, 250, 250))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * width, (i // cols) * height))
    out = os.path.join(DBG, '%s_sheet.png' % mod_name)
    sheet.save(out)
    print('wrote %s  (%d beats, %dx%d, %d cols)'
          % (out, len(tiles), sheet.size[0], sheet.size[1], cols))

    # Report the numbers alongside, so the sheet is read with context.
    text = [e for e in scene.elements if e.kind == 'text']
    moving = [e for e in scene.elements if e.motion]
    stages = [e for e in scene.elements if e.id.startswith('stage')]
    n = len(clock.meta['beats'])
    print('  beats=%d  text=%d (%.0f%%)  motion=%d  stages=%d  elements=%d'
          % (n, len(text), 100.0 * len(text) / n, len(moving), len(stages),
             len(scene.elements)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))