import sys; sys.path.insert(0,'.')
import _coverage_gate as G
for ch in sys.argv[1:]:
    c=G.title_contrast(ch); b=G.band_intrusions(ch)
    print('%-10s contrast=%s  intrusions=%s'%(ch,c,b))
