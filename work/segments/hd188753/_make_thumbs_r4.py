# work/segments/hd188753/_make_thumbs_r4.py
# Round 4 thumbnail extractor for the critic.
# Generates 4 thumbs at 25%, 50%, 75%, 100% of segment duration.
# Saves to thumbs_r4/thumb_{25,50,75,100}.png at 1280x720.

import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def get_duration(mp4):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', mp4],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def extract_thumb(mp4, t_seconds, out_path):
    """Extract a single frame at t_seconds from mp4, scaled to 1280x720."""
    cmd = [
        'ffmpeg', '-y', '-ss', f'{t_seconds:.3f}', '-i', mp4,
        '-vframes', '1', '-vf', 'scale=1280:720', out_path,
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


def main():
    mp4 = os.path.join(HERE, 'round_4.mp4')
    if not os.path.exists(mp4):
        print(f'round_4.mp4 not found at {mp4}')
        sys.exit(1)

    out_dir = os.path.join(HERE, 'thumbs_r4')
    os.makedirs(out_dir, exist_ok=True)

    duration = get_duration(mp4)
    print(f'round_4.mp4 duration: {duration:.2f}s')

    fractions = [
        ('25',  0.25),
        ('50',  0.50),
        ('75',  0.75),
        ('100', 1.00),
    ]
    for label, frac in fractions:
        t = duration * frac
        # Clamp to just before the end so we don't read past EOF
        t = min(t, max(0.0, duration - 0.05))
        out_path = os.path.join(out_dir, f'thumb_{label}.png')
        extract_thumb(mp4, t, out_path)
        print(f'  thumb_{label}: t={t:.2f}s -> {out_path}')

    print('Done.')


if __name__ == '__main__':
    main()
