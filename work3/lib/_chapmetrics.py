"""One-line cadence/motion/reframe metrics for any chapter.

The per-chapter numbers have been tracked in a running commentary for three
rounds, which is exactly the state that caused the earlier misdiagnosis: the
numbers were remembered, not measured, so "area51 still cuts every 2.5s" was
believed without a re-run after the scene file changed underneath it. This
prints the current numbers for any chapter from its OWN build() output, so a
before/after comparison is two commands and no memory.

Run:  python lib/_chapmetrics.py area51 cheyenne svalbard fortknox
"""
import sys

sys.path.insert(0, 'lib')
sys.path.insert(0, '../work/lib')

import scene_common as SC          # noqa: E402
import _readability_gate as G      # noqa: E402


def report(ch):
    # Beats come from segments/<chapter>/beats.json, NOT from the module. Every
    # scene module also exports a BEATS, but on these four it is a STRING (the
    # chapter's beat count or a joined label) -- passing it to check_cadence
    # raises 'str object has no attribute get'. Use the gate's own loader so
    # the shape is whatever the gate expects.
    scene, beats, mod = G.load(ch)
    out = {'chapter': ch, 'elements': len(scene.elements), 'beats': len(beats)}

    out['reframe_hits'] = len(G.check_reframe(scene, beats))
    cut, gap, ngaps = G.check_cadence(scene, beats)
    out['cut_s'] = round(cut, 2)
    out['still_gap'] = round(gap, 1)
    out['gaps'] = ngaps
    m = G.check_motion(scene, beats, fps=6)
    if isinstance(m, tuple):
        for i, v in enumerate(m):
            try:
                m[i] = round(v, 4)
            except (TypeError, ValueError):
                pass
    out['motion'] = m
    out['layer_ratio'] = G.check_layer_ratio(mod)

    # Every cap()/caption() element, and the fill it resolves to. This is the
    # population _audit_label_ink.py cannot see, because it only parses
    # draw_label/draw_bubble call sites.
    caps = [e for e in scene.elements if getattr(e, 'id', '').startswith('cap')]
    out['captions'] = len(caps)
    return out


if __name__ == '__main__':
    chaps = sys.argv[1:] or ['area51', 'cheyenne', 'svalbard', 'fortknox']
    for c in chaps:
        try:
            print(report(c))
        except Exception as e:
            print({'chapter': c, 'ERROR': '%s: %s' % (type(e).__name__, e)})