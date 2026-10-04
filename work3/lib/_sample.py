import sys; sys.path.insert(0,'.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T
ch=sys.argv[1]; bid=int(sys.argv[2])
importlib.invalidate_caches()
m=importlib.import_module('%s_scene'%ch); s=m.build()
meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
fr=E3.render_frame(s,mid).convert('L'); a=np.asarray(fr,dtype=np.int16)
for y in (60,64,68,72,76):
    row=a[y,470:820]
    print('y=%3d  min=%3d max=%3d  sample@x=640:%3d'%(y,row.min(),row.max(),a[y,640]))
