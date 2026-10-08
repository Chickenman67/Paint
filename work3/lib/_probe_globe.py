"""Render _globe alone at the radius svalbard b13 uses."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join('..', 'work', 'lib'))

from PIL import Image, ImageDraw
import svalbard_scene as S

img = Image.new('RGB', (1280, 720), (206, 214, 224))
S._globe(ImageDraw.Draw(img), 790, 452, 336, 133)
img.save(os.path.join('..', 'measure', 'p_globe.png'))
print('saved p_globe.png')