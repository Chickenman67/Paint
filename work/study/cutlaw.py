import re, numpy as np
ts=[]
for line in open('work/refstudy/cuts.txt'):
    m=re.search(r'pts_time:([0-9.]+)',line)
    if m: ts.append(float(m.group(1)))
ts=sorted(set(round(t,3) for t in ts))
ts=[t for t in ts if t>0.5]
d=np.diff(np.array(ts))
d=d[d>0.05]
d=np.sort(d)
print(f"cuts n={len(ts)} span={ts[-1]-ts[0]:.1f}s")
print(f"gap (card duration proxy): median={np.median(d):.2f}s mean={d.mean():.2f}s")
for p in (10,25,50,75,90,95,99):
    print(f"  p{p} = {np.percentile(d,p):.2f}s")
print("short cards <2s:", int((d<2).sum()), " 2-4s:", int(((d>=2)&(d<4)).sum()), " >8s:", int((d>8).sum()))
print(f"shots/min implied = {60/np.median(d):.1f}")
