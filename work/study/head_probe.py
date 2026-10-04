from PIL import Image
import numpy as np
a=np.asarray(Image.open('work/study/ref_s1_5.png').convert('RGB')).astype(int)
# head circle approx: center (487,335) radius ~52
yy,xx=np.mgrid[0:720,0:1280]
d=np.sqrt((xx-487)**2+(yy-335)**2)
for r in (0.80,0.65,0.50,0.35,0.20):
    m=d<=52*r
    sub=a[m]
    bright=sub[sub.sum(axis=1)>450]   # near-white pixels only = fill, not features
    if len(bright):
        print(f"r<={r:.2f}  bright-fill px={len(bright):5d} mean={bright.mean(axis=0).astype(int)} std={bright.std(axis=0).astype(int)}")
print()
# radial profile of brightness from head center
print("radial brightness profile (mean of near-white channel, 8 annuli):")
for i in range(8):
    r0,r1=52*i/8,52*(i+1)/8
    m=(d>=r0)&(d<r1)
    sub=a[m]; b=sub[sub.sum(axis=1)>450]
    if len(b): print(f"  r {r0:4.1f}-{r1:4.1f}  n={len(b):4d} mean={b.mean(axis=0).mean():6.1f}  min={b.min():4d}")
