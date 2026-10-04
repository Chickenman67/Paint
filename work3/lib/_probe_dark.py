import sys; sys.path.insert(0,'.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T
FAIL={'pinegap':[34],'area51':[18,34],'tomb':[5,6,7,8,9,10,15,16,17,18],
'room39':[3,5,8,17,19,29,31,32,34,36],'mezhgorye':[19,30],
'cheyenne':[16,25,27,28,29,37,38],'svalbard':[1,2,19,31,33,34],
'fortknox':[22,23,24,27,28,29,32,33,44]}
cap=T.TITLE_CAP_PX; base=T.TITLE_BASELINE_Y
ty0=max(0,base-int(cap*1.25)); ty1=base+6
tw=min(620,int(11*cap*0.62)); tx0=max(0,T.TITLE_CENTER_X-tw//2); tx1=min(1280,T.TITLE_CENTER_X+tw//2)
for ch in (sys.argv[1:] or sorted(FAIL)):
    importlib.invalidate_caches()
    m=importlib.import_module('%s_scene'%ch); s=m.build()
    meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
    blank=E3._blank_page()
    if s.title: E3._draw_title(blank,s.title,seed=s.title_seed)
    core=(np.asarray(blank.convert('L'))<120)[ty0:ty1,tx0:tx1]
    lv=[]
    for b in FAIL[ch]:
        beat=meta['beats'][b-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
        fr=E3.render_frame(s,mid).convert('L'); a=np.asarray(fr,dtype=np.int16)
        r=a[ty0:ty1,tx0:tx1]; bgp=r[~core]
        lv.append(int(np.median(bgp)))
    dark=sum(1 for v in lv if v<150)
    print('%-10s n=%2d dark(<150)=%2d  medians=%s'%(ch,len(lv),dark,lv))
