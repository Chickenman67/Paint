"""Smoke-test the v2 card modules without a full render.

For each segment: load the card module, build EVERY beat's layers, and compose
one frame at the END of each beat (where every layer is popped) into
<seg>/_checkframes/. Catches NameError/AttributeError/wrong-signature and shows
the finished look of every beat at once, so a card author can judge the whole
segment in a contact sheet.

Usage:  python _v2_smoke.py tres2b wasp17b [more...]
"""

import io
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))                 # .../work/segments
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))

import _v2_frames as F       # noqa: E402
import v2engine as E         # noqa: E402


def smoke(seg, cols=3, cell_w=420):
    ctx = F.build_context(seg)
    mod = F.load_layer_module(seg)
    outdir = os.path.join(HERE, seg, '_checkframes')
    os.makedirs(outdir, exist_ok=True)

    shots = []
    for b in ctx.beats:
        t = b['end'] - b['start']            # end of beat: all layers popped
        layers = E.sort_layers(mod.build_beat(b['id'], ctx))
        img = E.compose(layers, t, title=ctx.title, title_seed=abs(hash(seg)) % 99991)
        p = os.path.join(outdir, 'b%02d_%s.png' % (b['n'], b['id'][:22]))
        img.save(p)
        shots.append(img)
        print('  %-28s %2d layers  t=%.2f  -> %s'
              % (b['id'], len(layers), t, os.path.basename(p)), flush=True)

    # contact sheet
    rows = (len(shots) + cols - 1) // cols
    ch = int(cell_w * 720 / 1280)
    sheet = Image.new('RGB', (cols * cell_w, rows * ch), (230, 230, 230))
    for i, im in enumerate(shots):
        sheet.paste(im.resize((cell_w, ch), Image.LANCZOS),
                    ((i % cols) * cell_w, (i // cols) * ch))
    sp = os.path.join(outdir, '_sheet.png')
    sheet.save(sp)
    print('  sheet: %s (%d beats)' % (sp, len(shots)), flush=True)
    return len(shots)


def main():
    segs = sys.argv[1:] or ['koi55']
    total = 0
    for seg in segs:
        try:
            print('[%s]' % seg)
            total += smoke(seg)
        except Exception as e:
            import traceback
            print('  [%s] FAILED: %s' % (seg, e))
            traceback.print_exc()
    print('\n%d beats built across %d segments' % (total, len(segs)))


if __name__ == '__main__':
    main()
