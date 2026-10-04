import sys; sys.path.insert(0,'.')
import json, os, importlib
import engine3 as E3
ch=sys.argv[1]; bid=int(sys.argv[2])
importlib.invalidate_caches()
m=importlib.import_module('%s_scene'%ch); s=m.build()
meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
im=E3.render_frame(s,mid)
im.crop((300,0,980,140)).save(sys.argv[3])
print('saved',sys.argv[3])
