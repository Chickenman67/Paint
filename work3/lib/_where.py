import sys; sys.path.insert(0,'.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T
ch=sys.argv[1]; bid=int(sys.argv[2])
importlib.invalidate_caches()
m=importlib.import_module('%s_scene'%ch); s=m.build()
meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
cap=T.TITLE_CAP_PX; base=T.TITLE_BASELINE_Y
ty0=max(0,base-int(cap*1.25)); ty1=base+6
tw=min(620,int(11*cap*0.62)); tx0=max(0,T.TITLE_CENTER_X-tw//2); tx1=min(1280,T.TITLE_CENTER_X+tw//2)
blank=E3._blank_page(); E3._draw_title(blank,s.title,seed=s.title_seed)
mask=(np.asarray(blank.convert('L'))<128)
from scipy import ndimage
mask=ndimage.binary_dilation(mask,iterations=4)[ty0:ty1,tx0:tx1]
fr=E3.render_frame(s,mid).convert('L'); a=np.asarray(fr,dtype=np.int16)
rect=a[ty0:ty1,tx0:tx1]
bgp=rect[~mask]; bgl=float(np.median(bgp))
off=~mask; ink=off&(np.abs(rect-bgl)>25)
rows=np.nonzero(ink.any(axis=1))[0]
print('bgl=%.1f  ty0=%d  intruding rows (abs y): %s'%(bgl,ty0,[int(r+ty0) for r in rows]))
for r in rows:
    cols=np.nonzero(ink[r])[0]
    print('   y=%d  n=%d  x-range abs %d..%d'%(r+ty0,len(cols),cols.min()+tx0,cols.max()+tx0))
