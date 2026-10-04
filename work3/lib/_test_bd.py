import sys; sys.path.insert(0,'.')
from PIL import Image
import scene_common as SC
im=Image.new('RGBA',(1280,720),(20,20,24,255))
SC.title_backdrop(im, 5)
im.convert('RGB').save('_test_bd.png')
# sample band luminance
import numpy as np
a=np.asarray(im.convert('L'),dtype=np.int16)
print('band y=10..73 median:', int(np.median(a[10:73, :])))
print('below band y=130 median:', int(np.median(a[130:200,:])))
