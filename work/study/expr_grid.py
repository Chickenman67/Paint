import sys; sys.path.insert(0,'work')
from PIL import Image
import lib.stickman as S
exprs=sorted(S.MOUTHS.keys())
cols=6; rows=(len(exprs)+cols-1)//cols
cell=200
img=Image.new('RGB',(cols*cell, rows*cell+40),(238,233,218))
for i,e in enumerate(exprs):
    x=(i%cols)*cell; y=(i//cols)*cell
    S.draw_stickman(img, x+cell//2, y+18, 150, pose='standing', mouth=e, theme='light')
import lib.type as T
d=__import__('PIL.ImageDraw',fromlist=['x']).Draw(img)
for i,e in enumerate(exprs):
    d.text(((i%cols)*cell+8,(i//cols)*cell+cell-20), e, fill=(60,60,60), font=T.load_font(13))
img.save('work/study/t3_exprs.png')
print("expressions:",len(exprs),exprs)
