# work3/lib/_density_probe.py -- text density, counted PER BEAT.
#
# WHY THIS EXISTS
#   The readability plan's density rule is "text on ~40% of beats, not every
#   beat". The pilot was measured at "18 text elements / 34 beats = 53%", which
#   looks like a miss -- but that counts ELEMENTS, and a caption placed at b05
#   with until=b07's onset is live across b05 AND b06. Two beats, one element.
#   The rule is written about beats, so the only honest measurement is:
#   for each beat, is any text element live at ANY point inside its window?
#
#   Three denominators, reported together so a disagreement is visible:
#     whole  -- text live at some point anywhere in the beat window
#     mid    -- text live at the beat midpoint (the strictest reading)
#     cover  -- mean over the beat of the fraction of the beat with text live
#
# USAGE:  python lib/_density_probe.py pinegap

import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pinegap2_scene as S


def probe(mod_name='pinegap2_scene'):
    mod = importlib.import_module(mod_name)
    scene = mod.build()
    clock = S.SC.BeatClock(mod.BEATS)
    beats = clock.meta['beats']

    text_els = [e for e in scene.elements if e.kind == 'text']
    n_els = len(text_els)

    n = len(beats)
    whole = 0
    mid = 0
    cover = 0.0
    rows = []
    for k, b in enumerate(beats):
        t0 = float(clock.at(b['id'], 0))
        t1 = float(clock.bend[b['id']])
        tm = (t0 + t1) / 2.0
        SAMP = 10
        live = 0
        for i in range(SAMP + 1):
            t = t0 + (t1 - t0) * i / SAMP
            if any(e.visible(t) for e in text_els):
                live += 1
        frac = live / (SAMP + 1)
        cover += frac
        w = live > 0
        m = any(e.visible(tm) for e in text_els)
        whole += w
        mid += m
        rows.append((b.get('n', k), b.get('beat', ''), w, m, frac))

    print('scene: %s  (%d beats, %d text elements, %d elements total)'
          % (mod_name, n, n_els, len(scene.elements)))
    print('text ELEMENTS per beat : %.1f%%   <- the number that read as 53%%'
          % (100.0 * n_els / n))
    print('text WHOLE per beat     : %.1f%%   (live at any point in the beat)'
          % (100.0 * whole / n))
    print('text MID   per beat     : %.1f%%   (live at the beat midpoint)'
          % (100.0 * mid / n))
    print('text COVER per beat     : %.1f%%   (mean fraction of beat covered)'
          % (100.0 * cover / n))
    print()
    print('beat  label                       whole mid  cover')
    for nb, lab, w, m, f in rows:
        print('  %-3s %-26s %-5s %-5s %.2f'
              % (nb, str(lab)[:26], 'T' if w else '.', 'T' if m else '.', f))
    return dict(els=n_els, whole=whole, mid=mid, cover=cover, n=n)


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'pinegap2_scene'
    probe(name)