import sys; sys.path.insert(0,'.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T
from PIL import Image
ch=sys.argv[1]; bid=int(sys.argv[2])
importlib.invalidate_caches()
m=importlib.import_module('%s_scene'%ch); s=m.build()
meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
cap=T.TITLE_CAP_PX; base=T.TITLE_BASELINE_Y
ty0=max(0,base-int(cap*1.25)); ty1=base+6
tw=min(620,int(11*cap*0.62)); tx0=max(0,T.TITLE_CENTER_X-tw//2); tx1=min(1280,T.TITLE_CENTER_X+tw//2)
blank=E3._blank_page(); E3._draw_title(blank,s.title,seed=s.title_seed)
tb=np.asarray(blank.convert('L')); mask=tb<128
for _ in range(4):
    d=mask.copy(); d[1:,:]|=mask[:-1,:]; d[:-1,:]|=mask[1:,:]; d[:,1:]|=mask[:,:-1]; d[:,:-1]|=mask[:,1:]; mask=d
fr=E3.render_frame(s,mid).convert('L'); a=np.asarray(fr,dtype=np.int16)
rect=a[ty0:ty1,tx0:tx1]; mrect=mask[ty0:ty1,tx0:tx1]
bgp=rect[~mrect]; bgl=float(np.median(bgp))
ink=(~mrect)&(np.abs(rect-bgl)>25)
# stack: frame band, mask, ink
band_rgb=np.asarray(E3.render_frame(s,mid).convert('RGB'))[ty0:ty1,tx0:tx1]
mask_vis=(~mrect*255).astype(np.uint8)
ink_vis=(ink*255).astype(np.uint8)
def rgb(g): return np.dstack([g,g,g])
sheet=np.vstack([band_rgb, rgb(mask_vis), rgb(ink_vis)])
Image.fromarray(sheet.astype(np.uint8)).resize((sheet.shape[1]*2, sheet.shape[0]*2), Image.NEAREST).save('_dbg_band_%s_b%02d.png'%(ch,bid))
print('saved _dbg_band_%s_b%02d.png  bgl=%.1f  inkpx=%d'%(ch,bid,bgl,ink.sum()))
