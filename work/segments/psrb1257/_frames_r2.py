# _frames_r2.py -- segment 3 (PSR B1257+12) round 2: the 31-card video.
#
# Assembles round_2_silent.mp4 from the 31 validated card renderers, the
# 0.25 s-quantized stamp motion layer (lib/motion.py), and the beat-boundary
# palette bridges.
#
# TIMING — the alignment contract (round_1_card_schedule.json):
#   * Card n is up from its schedule start to card n+1's start. HARD CUT, no
#     fade (CLAUDE.md §5.3): the cut IS the alignment event.
#   * Motion is sampled at 4 Hz (0.25 s stamps) and quantized. stamp_index =
#     int(elapsed_in_card / 0.25) is computed from the frame index, so nothing
#     in the output is a smooth tween.
#   * A 0.5 s BLACK palette bridge after the two cards the schedule names
#     (`bridges` field: after how_first and after name_just_digits). The
#     segment-exit bridge is the 3.75 s white bridge in lib/transition.py, which
#     supersedes CLAUDE.md §5.7's "0.5 s black frame" — so NO trailing bridge
#     here; assembly owns that one.
#   * The last card holds its still to the end of the audio (91.0 s) so video
#     length == WAV length and `-shortest` cannot clip narration. close_finale's
#     motion is "spin_step (never decelerates)", so continuing it is correct.
#
# BRIDGES ARE CARVED OUT OF THE PRECEDING CARD, NOT INSERTED BETWEEN CARDS.
# That is the whole reason the drift is zero. The schedule's card `start` times
# ARE the aligned word onsets (round_1_alignment.json, "predicted_schedule_
# discarded": true), so a card must never begin later than its schedule start.
# Appending a bridge in front of the next card pushes every subsequent card
# later than its own spoken word — an earlier build of this file appended a
# bridge after EVERY card and drifted a cumulative +13.0 s by the finale, which
# is the exact failure CLAUDE.md §5 is about. Instead the 0.5 s is taken from
# the tail of the card it follows, so the bridge still lands between the two
# beats while every card stays welded to its audio.
#
# MEMORY: cards are sequential, so each card's base still is built once, right
# before its first stamp, and dropped after its last — one still resident at a
# time (~3 MB), not 31 (~85 MB). That satisfies "precompute the still ONCE and
# reuse it across its stamps" without the cost of holding the whole segment.

import argparse
import json
import os
import subprocess
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))   # .../work
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import lib.cardframe as C          # noqa: E402
import lib.motion as M             # noqa: E402

SEG = 'PSR B1257+12'
W, H, FPS = 1280, 720, 30
STAMP_DT = M.STAMP_DT               # 0.25 s
BRIDGE_S = 0.5                      # black palette bridge between beats
BLACK = (0, 0, 0)

# The schedule's `bridges` field names exactly these two cards: "0.5s palette
# bridge after how_first and after name_punchline" (round_1_script.md line 110).
# name_punchline was renamed name_just_digits by fact flag E6, so that is the
# second one here. Anything not in this set gets NO bridge.
BRIDGE_AFTER = ('how_first', 'name_just_digits')


def load_cards(schedule_path):
    s = json.load(open(schedule_path, encoding='utf-8'))
    return s['cards'], s


def register_all(beat_ids):
    """Import each beat module and merge its RENDERERS into the dispatch table.
    Reads .RENDERERS directly rather than calling a register() helper -- b3 and
    b5 do not define one."""
    for b in beat_ids:
        m = __import__('_cards_b%d' % b)
        C.register(m.RENDERERS)


def build_timeline(cards, audio_duration, bridge_after=BRIDGE_AFTER):
    """-> (segments, total_s). Each segment is a dict:
         kind='card'   -> card, t0, t1
         kind='bridge' -> t0, t1  (black)
       Cards keep their schedule boundaries except where a bridge is carved out
       of a tail; the last card runs to the end of the audio."""
    segs = []
    last = len(cards) - 1
    for i, c in enumerate(cards):
        t0 = float(c['start'])
        t1 = float(c['end']) if i < last else float(audio_duration)
        if t1 <= t0:
            t1 = t0 + STAMP_DT
        # carve the bridge out of this card's tail (never append it in front of
        # the next card -- see the BRIDGES note in the header)
        if c['id'] in bridge_after and i < last:
            hold = t1 - t0 - BRIDGE_S
            if hold >= STAMP_DT:
                segs.append({'kind': 'card', 'card': c, 't0': t0, 't1': t0 + hold})
                segs.append({'kind': 'bridge', 't0': t0 + hold, 't1': t1})
                continue
        segs.append({'kind': 'card', 'card': c, 't0': t0, 't1': t1})
    return segs, segs[-1]['t1']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--schedule', default=os.path.join(HERE, 'round_1_card_schedule.json'))
    ap.add_argument('--out', default=os.path.join(HERE, 'round_2_silent.mp4'))
    ap.add_argument('--audio', default=os.path.join(HERE, 'round_1_audio.wav'))
    ap.add_argument('--debug', action='store_true',
                    help='stamp the frame index on every frame. OFF by default: '
                         'a debug-on-by-default build leaked stamps into the '
                         'final assembly (CLAUDE.md §10.9).')
    args = ap.parse_args()

    cards, sched = load_cards(args.schedule)
    audio_dur = float(sched.get('timing', {}).get('audio_duration_s')
                      or sched.get('duration_s'))

    beats = sorted({int(c['beat'].split()[0][1:]) for c in cards})
    register_all(beats)

    segs, total_s = build_timeline(cards, audio_dur)
    n_frames = int(round(total_s * FPS))
    n_bridges = sum(1 for s in segs if s['kind'] == 'bridge')
    print('cards=%d beats=%s bridges=%d total=%.3fs audio=%.3fs frames=%d @%dfps'
          % (len(cards), beats, n_bridges, total_s, audio_dur, n_frames, FPS),
          flush=True)

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
        '-r', str(FPS), '-i', 'pipe:0',
        '-an',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
        args.out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t_start = time.time()
    still = None
    still_id = None
    seg_i = 0
    frames_written = 0
    try:
        for fi in range(n_frames):
            t = fi / FPS
            # segments are short and contiguous; advance a cursor instead of
            # rescanning every card for every frame
            while seg_i + 1 < len(segs) and t >= segs[seg_i]['t1']:
                seg_i += 1
            seg = segs[seg_i]

            if seg['kind'] == 'bridge':
                img = Image.new('RGB', (W, H), BLACK)
            else:
                card = seg['card']
                if still_id != card['id']:
                    still = C.render(card, SEG)     # built ONCE per card
                    still_id = card['id']
                elapsed = t - seg['t0']
                n_stamps = max(1, int(round((seg['t1'] - seg['t0']) / STAMP_DT)))
                img = M.apply_motion(still, card, int(elapsed / STAMP_DT), n_stamps)

            if args.debug:
                _stamp_debug(img, frames_written, FPS)

            proc.stdin.write(img.tobytes())
            frames_written += 1
            if frames_written % 600 == 0:
                el = time.time() - t_start
                print('  %d/%d frames  %.1fs elapsed  %.0f fps'
                      % (frames_written, n_frames, el,
                         frames_written / max(0.001, el)), flush=True)
    finally:
        proc.stdin.close()
        proc.wait()

    el = time.time() - t_start
    print('wrote %s: %d frames, %.2fs render (%.0f fps)'
          % (args.out, frames_written, el, frames_written / max(0.001, el)))
    if proc.returncode != 0:
        sys.exit('ffmpeg failed rc=%s' % proc.returncode)
    if abs(total_s - audio_dur) > (1.5 / FPS):
        sys.exit('timeline %.3fs != audio %.3fs -- mux would clip narration'
                 % (total_s, audio_dur))


def _stamp_debug(img, fi, fps):
    """Debug overlay. Opt-in only (--debug). Never on in an assembly build."""
    from PIL import ImageDraw
    import lib.type as T
    d = ImageDraw.Draw(img)
    T.draw_stamp(d, 'DEBUG seg3 round2 f%d t=%.2f' % (fi, fi / fps), (24, 690),
                 (255, 0, 0), ink_rgb=(0, 0, 0))


if __name__ == '__main__':
    main()