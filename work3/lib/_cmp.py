import sys; sys.path.insert(0,'.')
import numpy as np, json, os, importlib
import engine3 as E3, v2type as T
from PIL import Image
ch=sys.argv[1]; bid=int(sys.argv[2])
importlib.invalidate_caches()
m=importlib.import_module('%s_scene'%ch); s=m.build()
meta=json.load(open(os.path.join('..','segments',ch,'beats.json')))
beat=meta['beats'][bid-1]; mid=(beat['start']+beat.get('end',beat['start']+1))/2
y0,y1=0,90
blank=E3._blank_page(); E3._draw_title(blank,s.title,seed=s.title_seed)
a=np.asarray(blank.convert('L'))[y0:y1]
b=np.asarray(E3.render_frame(s,mid).convert('L'))[y0:y1]
# difference
d=np.abs(a.astype(int)-b.astype(int))
sheet=np.vstack([a,b,np.clip(d*3,0,255)])
Image.fromarray(np.dstack([sheet]*3).astype(np.uint8)).save('_cmp_%s_b%02d.png'%(ch,bid))
# row profile of where dark glyph pixels are
ra=(a<128); rb=(b<128)
print('blank dark rows:', [y0+i for i in np.nonzero(ra.any(axis=1))[0]][:5],'...',[y0+i for i in np.nonzero(ra.any(axis=1))[0]][-5:])
print('frame dark rows:', [y0+i for i in np.nonzero(rb.any(axis=1))[0]][:5],'...',[y0+i for i in np.nonzero(rb.any(axis=1))[0]][-5:])
