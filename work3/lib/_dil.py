import sys; sys.path.insert(0,'.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T
def dilate(mask,n):
    for _ in range(n):
        d=mask.copy(); d[1:,:]|=mask[:-1,:]; d[:-1,:]|=mask[1:,:]; d[:,1:]|=mask[:,:-1]; d[:,:-1]|=mask[:,1:]; mask=d
    return mask
CASES=[('pinegap',34),('tomb',14),('svalbard',18),('room39',3),('cheyenne',16),('fortknox',22)]
for dil in (4,6,8,10):
    out=[]
    for ch,bid in CASES:
        importlib.invalidate_caches()
        m=importlib.import_module('%s_scene'%ch); s=m.build()
        meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
        beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
        cap=T.TITLE_CAP_PX; base=T.TITLE_BASELINE_Y
        ty0=max(0,base-int(cap*1.25)); ty1=base+6
        tw=min(620,int(11*cap*0.62)); tx0=max(0,T.TITLE_CENTER_X-tw//2); tx1=min(1280,T.TITLE_CENTER_X+tw//2)
        blank=E3._blank_page(); E3._draw_title(blank,s.title,seed=s.title_seed)
        mask=dilate(np.asarray(blank.convert('L'))<128, dil)[ty0:ty1,tx0:tx1]
        fr=E3.render_frame(s,mid).convert('L'); a=np.asarray(fr,dtype=np.int16)
        rect=a[ty0:ty1,tx0:tx1]; bgp=rect[~mask]; bgl=float(np.median(bgp))
        ink=(~mask)&(np.abs(rect-bgl)>25)
        out.append('%s b%02d=%d'%(ch,bid,int(ink.sum())))
    print('dil=%2d  %s'%(dil,'  '.join(out)))
