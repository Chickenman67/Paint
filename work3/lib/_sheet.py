"""Throwaway: render a contact sheet of every beat in a chapter.

One 5x7 grid of all beats at 320x180 each. This is the cheapest diagnostic
there is -- in svalbard it surfaced four defects (a gold traffic cone, a black
stickman on a night card, an unclear box, a copy-pasted wrong year) that
individual full-res renders had missed. Judge the layout and the storyboard
from here; judge texture and legibility only at full res.
"""
import sys, os, json
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../../work/lib'))
from PIL import Image
import engine3 as E3

NAME = sys.argv[1] if len(sys.argv) > 1 else 'cheyenne'
SCENE = sys.argv[2] if len(sys.argv) > 2 else NAME + '2_scene'
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 5

M = __import__(SCENE)
sc = M.build()
b = json.load(open('../segments/%s/beats.json' % NAME))
beats = b['beats']

TW, TH = 320, 180
rows = (len(beats) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * TW, rows * TH), (20, 20, 24))

for i, q in enumerate(beats):
    t = (q['start'] + q['end']) / 2.0
    fr = E3.render_frame(sc, t).resize((TW, TH), Image.BILINEAR)
    sheet.paste(fr, ((i % COLS) * TW, (i // COLS) * TH))

out = '_sheet_%s.png' % NAME
sheet.save(out)
print('%s  %d beats -> %s  (%dx%d)' % (NAME, len(beats), out, sheet.width, sheet.height))
for i, q in enumerate(beats):
    print('  row%d col%d  b%02d  %s' % (i // COLS, i % COLS, q['n'], q['line'][:56]))