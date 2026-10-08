"""Render _hand_drill alone at the size mezhgorye b10 actually uses, so the
primitive can be judged on its own instead of inferred from a full frame."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join('..', 'work', 'lib'))

from PIL import Image, ImageDraw
import mezhgorye_scene as M

img = Image.new('RGB', (1280, 720), (206, 214, 226))
M._hand_drill(ImageDraw.Draw(img), 640, 470, 300, 103, contact_y=560)
img.save(os.path.join('..', 'measure', 'p_drill.png'))
print('saved p_drill.png')

# Also the bare rock face the chips were landing on, so I can see whether the
# "confetti" is the drill's dust or the drift's shards.
img2 = Image.new('RGB', (1280, 720), (206, 214, 226))
M._hand_drill(ImageDraw.Draw(img2), 640, 400, 900, 103)
img2.save(os.path.join('..', 'measure', 'p_drill_big.png'))
print('saved p_drill_big.png')