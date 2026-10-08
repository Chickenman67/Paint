"""Print the narration line for named beats. Scratch probe, not part of the build."""
import json, glob, os, sys

want = {'mezhgorye': ['b10', 'b26'], 'svalbard': ['b13', 'b21']}
paths = sorted(glob.glob('**/beats.json', recursive=True))
print("FOUND %d beats.json" % len(paths))
for p in paths:
    name = os.path.basename(os.path.dirname(p))
    if name not in want:
        continue
    d = json.load(open(p, encoding='utf-8'))
    beats = d['beats'] if isinstance(d, dict) and 'beats' in d else d
    for b in beats:
        if b.get('id') in want[name]:
            print("%-10s %-4s | %s" % (name, b.get('id'),
                                       (b.get('line') or '')[:130]))