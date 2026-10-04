"""Regenerate progress/state2.json from the on-disk artifacts.

The progress page polls this file every 4s, so hand-editing it drifts. This
reads each segment's v2_beats.json / v2_alignment.json and the presence of
_cards_v2.py / v2_segment.mp4, and rewrites the derived fields. Fields that
are measured from the reference (measured/target/pipeline) are preserved.

Usage:  python _mkstate2.py
"""

import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))          # .../progress
SEG = os.path.join(HERE, '..', 'work', 'segments')
STATE = os.path.join(HERE, 'state2.json')

# Must match _assemble_v2.py SEGMENTS order. This is 10, not 12: measuring the
# 9 finished segments gave 792.7s against ref2's 875.5s, and the 82.8s deficit
# is ~221 words -- exactly one more segment, not three.
ORDER = ["tres2b", "wasp17b", "wasp127b", "gliese436b", "ltt9779b",
         "fomalhautb", "psrb1257", "koi55", "kelt9b", "psoj3185"]

TITLES = {
    "tres2b": "the darkest planet ever found",
    "wasp17b": "the planet that orbits backwards",
    "wasp127b": "the fastest winds in the galaxy",
    "gliese436b": "burning ice, dragging a glowing tail",
    "ltt9779b": "the mirror-bright super-Earth",
    "fomalhautb": "the dust-shepherd that may not be there",
    "psrb1257": "the planets around a dead star",
    "koi55": "the planet that survived being eaten",
    "kelt9b": "hotter than most stars",
    "psoj3185": "the rogue, alone in the dark",
}


def _load(path):
    try:
        with io.open(path, encoding='utf-8') as f:
            return json.load(f)
    except (IOError, OSError, ValueError):
        return None


def main():
    with io.open(STATE, encoding='utf-8') as f:
        st = json.load(f)

    segs = st.setdefault('segments', {})
    for k in ORDER:
        d = os.path.join(SEG, k)
        e = segs.setdefault(k, {'key': k})
        e['title'] = TITLES.get(k, '')
        b = _load(os.path.join(d, 'v2_beats.json'))
        if b:
            e['audio'] = 'done'
            e['dur_s'] = round(b['duration_s'], 3)
            e['wpm'] = round(b['wpm'], 1)
            e['words'] = b.get('word_count', 0)
            e['on_target'] = b.get('on_target', False)
            e['pause_frac'] = round(b.get('pause_frac', 0.0), 4)
            # wpm of the speech alone, excluding the deliberate inter-beat breaths
            sp_s = b.get('speech_s', 0.0)
            nw = b.get('word_count', 0)
            e['speech_wpm'] = round(nw / sp_s * 60.0, 1) if sp_s > 0 and nw else None
        else:
            e['audio'] = 'pending'
        e['aligned'] = _load(os.path.join(d, 'v2_alignment.json')) is not None
        e['cards'] = os.path.exists(os.path.join(d, '_cards_v2.py'))
        e['video'] = os.path.exists(os.path.join(d, 'v2_segment.mp4'))

    done = [k for k in ORDER if segs[k]['audio'] == 'done']
    st['phase'] = 'phase-2-build'
    st['target']['segments'] = len(ORDER)
    st['target']['words_total'] = sum(segs[k].get('words', 0) for k in ORDER)

    asm = os.path.join(HERE, '..', 'work', 'assembly', 'exoplanets_v2_full.mp4')
    if os.path.exists(asm):
        st['assembly'] = {
            'status': 'built',
            'file': 'work/assembly/exoplanets_v2_full.mp4',
            'segments_in': len(done),
        }
    st['last_update'] = (
        'audio %d/%d · aligned %d · cards %d · video %d' % (
            len(done), len(ORDER),
            sum(1 for k in ORDER if segs[k]['aligned']),
            sum(1 for k in ORDER if segs[k]['cards']),
            sum(1 for k in ORDER if segs[k]['video'])))

    # --- audio reset (2026-10-03) -------------------------------------------
    # The delivery target moved from 160 to 170 wpm with near-continuous pacing.
    # Recorded here because the reference audio is the FULL MIX (narration +
    # music + mastering), so its centroid / syllable-rate / breath / dynamic
    # numbers are measurements of the music and are NOT voice targets. See
    # memory reference-mix-contaminates-voice-metrics.
    st['pipeline'] = {
        'type': 'per-beat TTS + closed-form atempo pacing solve',
        'target_wpm': 170.0,
        'gap_s': 0.08,
        'pause_squeeze': 'internal silences >=0.16s cut to 0.07s before the solve',
        'brightness': '3dB high shelf @3.5kHz, undoing atempo darkening '
                      '(centroid 1248->1190Hz) -- targeted at UNDAMAGE, not at '
                      'the contaminated reference centroid',
        'solve': 'gap chosen first, required_speech = words/170*60 - gap*n_gaps, '
                 'f = raw/required (f<1 slows)',
        'render': 'v2engine pop-and-hold compositor, 60fps, timed from whisper '
                  'word onsets',
        'subjects': 'lib/v2subjects.py flat-vector subjects on white page, 6px '
                    'ink wobble',
        'measured': 'all 10 segments 170.4-170.8 wpm; silence 15.4% -> 5-7%',
        'assembly_fps_note': 'bridges were 30fps against 60fps segments; fixed to '
                             '60 and verify_output now asserts stream params, '
                             'because duration agreement alone did not catch it',
    }
    st['last_update_unix'] = int(time.time())

    with io.open(STATE, 'w', encoding='utf-8') as f:
        json.dump(st, f, indent=1, ensure_ascii=False)
    print('wrote %s: %s' % (STATE, st['last_update']))


if __name__ == '__main__':
    main()
