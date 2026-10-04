from PIL import Image
import numpy as np
def ridge_strokes(p, y0,y1):
    a=np.asarray(Image.open(p).convert('RGB')).astype(int)
    dark=(a.sum(axis=2)<220)
    runs=[]
    for y in range(y0,y1):
        xs=np.where(dark[y])[0]
        if not len(xs): continue
        grp=[];s=xs[0];pv=xs[0]
        for x in xs[1:]:
            if x>pv+2: grp.append((s,pv)); s=x
            pv=x
        grp.append((s,pv))
        runs += [g[1]-g[0]+1 for g in grp]
    return sorted(runs)
for p in ('work/study/ref_s1_5.png','work/study/ours/o_5.png'):
    r=ridge_strokes(p, 300, 360)
    if r:
        import numpy as np
        print(f"{p:38s} n={len(r):4d} median={np.median(r):5.1f} p90={np.percentile(r,90):5.1f} max={max(r)}")
    else:
        print(f"{p:38s} NO dark strokes found in band")
