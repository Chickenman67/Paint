from PIL import Image
import numpy as np, sys, collections

p = sys.argv[1]
im = Image.open(p).convert('RGB'); a = np.asarray(im).astype(int)
H,W,_ = a.shape
print(f"=== {p}  {W}x{H} ===")

# 1. title strip: find rows that are near-uniform white
rowmean = a.mean(axis=(1,2))
white_rows=[y for y in range(H) if rowmean[y]>246 and a[y].std()<6]
print("near-white uniform rows:", (min(white_rows),max(white_rows)) if white_rows else None, "count",len(white_rows))
# contiguous run from top
if white_rows:
    y0=0
    while y0+1 in white_rows: y0+=1
    print(f"  -> title strip height = {y0+1}px (rows 0..{y0})")

# 2. stroke width: scan a column through a dark outline on the mountain ridge
dark = (a.sum(axis=2) < 200)
col_runs=[]
for y in range(int(H*0.45), int(H*0.52)):
    xs=np.where(dark[y])[0]
    if len(xs)==0: continue
    # group consecutive
    grp=[]; start=xs[0]; prev=xs[0]
    for x in xs[1:]:
        if x>prev+2:
            grp.append((start,prev)); start=x
        prev=x
    grp.append((start,prev))
    for g in grp:
        col_runs.append(g[1]-g[0]+1)
if col_runs:
    print("  ridge stroke widths px:", sorted(col_runs)[:12], " median", int(np.median(col_runs)))

# 3. dominant colors (k-means-ish via quantize)
q = im.quantize(colors=8, method=Image.MEDIANCUT).convert('RGB')
cnt=collections.Counter(q.getdata())
tot=sum(cnt.values())
print("  dominant colors:")
for c,n in cnt.most_common(8):
    print(f"    #{c[0]:02X}{c[1]:02X}{c[2]:02X}  {100*n/tot:5.1f}%")

# 4. head shading: is the white head actually flat?
# sample interior of the head circle (approx x 480,y 335 from visual)
def region_stats(x0,y0,x1,y1,label):
    sub=a[y0:y1,x0:x1].reshape(-1,3)
    print(f"  {label}: mean={sub.mean(axis=0).astype(int)} std={sub.std(axis=0).astype(int)}")
region_stats(455,300,525,365,"head interior")
region_stats(150,150,300,260,"sky")
