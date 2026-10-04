"""Regenerate progress/state3.json from on-disk work3 artifacts.

Same idea as _mkstate2.py but for the v3 build (new reference yMwWSX_cvrc,
165 wpm, phrase-level reveal). Reads each segment's script.json / beat audio and
derives status, so the page never drifts from the files.

Usage:  python _mkstate3.py
"""

import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))           # .../progress
W3 = os.path.abspath(os.path.join(HERE, os.pardir, 'work3'))
STATE = os.path.join(HERE, 'state3.json')

ORDER = ['tres2b', 'wasp17b', 'wasp127b', 'gliese436b', 'koi55',
         'ltt9779b', 'fomalhautb', 'psrb1257', 'kelt9b', 'psoj3185']

TITLES = {
    'tres2b': 'the darkest planet ever found',
    'wasp17b': 'the planet that orbits backwards',
    'wasp127b': 'the fastest winds in the galaxy',
    'gliese436b': 'burning ice, dragging a glowing tail',
    'koi55': 'the planet that survived being eaten',
    'ltt9779b': 'the mirror-bright super-Earth',
    'fomalhautb': 'the dust-shepherd that may not be there',
    'psrb1257': 'the planets around a dead star',
    'kelt9b': 'hotter than most stars',
    'psoj3185': 'the rogue, alone in the dark',
}


def _load(p):
    try:
        with io.open(p, encoding='utf-8') as f:
            return json.load(f)
    except (IOError, OSError, ValueError):
        return None


def main():
    with io.open(STATE, encoding='utf-8') as f:
        st = json.load(f)

    segs = st.setdefault('segments', {})
    for k in ORDER:
        d = os.path.join(W3, 'segments', k)
        e = segs.setdefault(k, {'key': k})
        e['title'] = TITLES.get(k, '')
        script = _load(os.path.join(d, 'script.json'))
        if script:
            e['script'] = 'done'
            e['words'] = script.get('word_count', 0)
            e['beats'] = len(script.get('beats', []))
        else:
            e['script'] = 'pending'

        beats = _load(os.path.join(d, 'beats.json'))
        if beats:
            e['audio'] = 'done'
            e['dur_s'] = round(beats.get('duration_s', 0), 2)
            e['wpm'] = round(beats.get('wpm', 0), 1)
            e['on_target'] = beats.get('on_target', False)
            e['pause_frac'] = round(beats.get('pause_frac', 0.0), 4)
        else:
            e['audio'] = 'pending'

        e['aligned'] = _load(os.path.join(d, 'alignment.json')) is not None
        e['video'] = os.path.exists(os.path.join(d, 'segment.mp4'))

    st['phase'] = 'phase-1-engine'   # engine+character built, audio in progress
    st['target']['segments'] = len(ORDER)
    st['last_update'] = 'script %d/%d | audio %d/%d | aligned %d | video %d' % (
        sum(1 for k in ORDER if segs[k]['script'] == 'done'), len(ORDER),
        sum(1 for k in ORDER if segs[k]['audio'] == 'done'), len(ORDER),
        sum(1 for k in ORDER if segs[k]['aligned']),
        sum(1 for k in ORDER if segs[k]['video']))

    st['last_update_unix'] = int(time.time())
    with io.open(STATE, 'w', encoding='utf-8') as f:
        json.dump(st, f, indent=1, ensure_ascii=False)
    print('wrote %s: %s' % (STATE, st['last_update']))


if __name__ == '__main__':
    main()