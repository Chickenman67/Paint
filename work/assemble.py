# work/assemble.py — Final assembly: segment 1 + bridge + segment 2 → final MP4.
#
# Usage:
#   python work/assemble.py
#
# Reads:
#   work/segments/hd188753/round_<N>.mp4
#   work/segments/hd80606/round_<N>.mp4
# Writes:
#   work/assembly/guantlet2_full.mp4  (or similar)

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from make_bridge import main as make_bridge_main

FPS = 30
W, H = 1280, 720


def find_winning_round(seg_dir):
    """Find the highest round that has both an MP4 and a 'won' state."""
    if not os.path.isdir(seg_dir):
        return None
    rounds = []
    for name in os.listdir(seg_dir):
        if name.startswith('round_') and name.endswith('.mp4') and '_silent' not in name:
            try:
                n = int(name.split('_')[1].split('.')[0])
                rounds.append(n)
            except (ValueError, IndexError):
                continue
    if not rounds:
        return None
    return max(rounds)


def concat_mp4s(mp4s, out_mp4):
    """Concatenate MP4s using ffmpeg concat demuxer."""
    list_path = out_mp4 + '.concat.txt'
    with open(list_path, 'w') as f:
        for m in mp4s:
            # Use absolute paths and escape single quotes
            ap = os.path.abspath(m).replace("'", "'\\''")
            f.write(f"file '{ap}'\n")
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', list_path,
        '-c', 'copy',
        out_mp4,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    os.remove(list_path)
    return out_mp4


def main():
    seg1_dir = 'work/segments/hd188753'
    seg2_dir = 'work/segments/hd80606'
    out_dir = 'work/assembly'
    os.makedirs(out_dir, exist_ok=True)

    r1 = find_winning_round(seg1_dir)
    r2 = find_winning_round(seg2_dir)
    if r1 is None:
        print(f"No winning round in {seg1_dir}")
        return 1
    if r2 is None:
        print(f"No winning round in {seg2_dir}")
        return 1

    seg1_mp4 = os.path.join(seg1_dir, f'round_{r1}.mp4')
    seg2_mp4 = os.path.join(seg2_dir, f'round_{r2}.mp4')
    bridge_mp4 = os.path.join(out_dir, 'bridge.mp4')

    print(f"Segment 1: {seg1_mp4}")
    print(f"Segment 2: {seg2_mp4}")
    print(f"Building bridge: {bridge_mp4}")
    make_bridge_main(seg1_mp4, seg2_mp4, bridge_mp4)

    out_mp4 = os.path.join(out_dir, 'guantlet2_full.mp4')
    print(f"Concatenating: {out_mp4}")
    concat_mp4s([seg1_mp4, bridge_mp4, seg2_mp4], out_mp4)
    print(f"Done: {out_mp4}")

    # Report duration
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1', out_mp4]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Final duration: {r.stdout.strip()}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
