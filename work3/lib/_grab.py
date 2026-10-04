import sys; sys.path.insert(0,'.')
import json, os, importlib
import engine3 as E3
ch=sys.argv[1]; bids=[int(x) for x in sys.argv[2].split(',')]
importlib.invalidate_caches()
m=importlib.import_module('%s_scene'%ch); s=m.build()
meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
from PIL import Image
ims=[]
for bid in bids:
    beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
    ims.append(E3.render_frame(s,mid))
if len(ims)==1:
    ims[0].save(sys.argv[3]); print('saved',sys.argv[3])
else:
    w,h=ims[0].size
    sheet=Image.new('RGB',(w//2*len(ims),h//2))
    for i,im in enumerate(ims): sheet.paste(im.resize((w//2,h//2)),(i*(w//2),0))
    sheet.save(sys.argv[3]); print('saved',sys.argv[3],len(ims),'frames')
