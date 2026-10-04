import sys; sys.path.insert(0,'work')
from PIL import Image, ImageDraw
import lib.type as T, lib.ink as K, lib.stickman as S

# 1. fonts resolve to Comic, not Consolas
for bold in (True, False):
    f = T.load_font(48, bold=bold)
    print("font", "bold" if bold else "reg", "->", f.path if hasattr(f,'path') else f)

# 2. header + label + caption render, with the 84px strip and full-bleed art
img = Image.new('RGB',(1280,720),(198,197,254))
d = ImageDraw.Draw(img)
d.rectangle([0,0,1280,T.HEADER_STRIP_BOTTOM], fill=(251,251,254))
K.draw_ridge(d, -40, 1320, 470, 190, seed=3, fill=(157,119,134), segments=6)
K.draw_ground(d, -40, 1320, 520, 720, (86,62,73), seed=5)
K.starfield(img, seed=1, n=60, y0=T.ART_TOP, color=(240,240,255))
T.draw_header(d, "HD 188753 AB", ink_rgb=(0,0,0))
T.draw_caption(d, "IMAGINE A SKY WITH THREE SUNS", (60, 640))
T.draw_label(d, "HD 80606 b", (900, 560))
K.stipple(d, 300, 600, 900, 700, (50,34,42), seed=9, density=0.05)
img.save('work/study/t1_card.png')

# 3. both themes, side by side
a = Image.new('RGB',(640,720),(240,236,222))
S.draw_stickman(a, 160, 120, 320, pose='thinker', mouth='worried', theme='light')
b = Image.new('RGB',(640,720),(12,14,30))
K.starfield(b, seed=2, n=70)
S.draw_stickman(b, 400, 120, 320, pose='pointing', mouth='scream', theme='dark')
c = Image.new('RGB',(1280,720))
c.paste(a,(0,0)); c.paste(b,(640,0))
d2=ImageDraw.Draw(c)
d2.text((20,690),"theme=light",fill=(0,0,0),font=T.load_font(20))
d2.text((660,690),"theme=dark",fill=(255,255,255),font=T.load_font(20))
c.save('work/study/t2_themes.png')
print("OK")
