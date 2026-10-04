# work/make_bridge.py — Build the inter-segment bridge between segment 1 and 2.
# Per ref_style_spec.md ## Motion + Transitions:
#   - 1.0 s cross-fade to white (the last beat of segment 1 fades to white)
#   - 2.25 s blank white card held (the palette bridge)
#   - 0.5 s cross-fade out (white fades into the first beat of segment 2)
#   - hard cut into the new segment with header appearing simultaneously
#
# This is the visual bridge. The audio bridge is handled by ensuring both
# segments have a small silence at start/end and concatenating with a small
# gap (or by simply concat-ing the mp4s with a generated bridge mp4 between).
#
# Usage: python work/make_bridge.py

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image
from lib.transition import (
    BRIDGE_FADE_IN, BRIDGE_HOLD, BRIDGE_FADE_OUT,
    TOTAL_BRIDGE, make_white_card,
)

FPS = 30
W, H = 1280, 720


def extract_last_frame(mp4_path, out_png):
    """Extract the last frame of an MP4 as a PNG."""
    cmd = ['ffmpeg', '-sseof', '-0.1', '-i', mp4_path, '-frames:v', '1', '-y', out_png]
    subprocess.run(cmd, check=True, capture_output=True)


def extract_first_frame(mp4_path, out_png):
    """Extract the first frame of an MP4 as a PNG."""
    cmd = ['ffmpeg', '-i', mp4_path, '-frames:v', '1', '-y', out_png]
    subprocess.run(cmd, check=True, capture_output=True)


def render_bridge_frames(last_png, first_png, out_dir, fps=FPS):
    """Render the bridge frames as a sequence of PNGs."""
    os.makedirs(out_dir, exist_ok=True)
    last_img = Image.open(last_png).convert('RGB')
    first_img = Image.open(first_png).convert('RGB')
    white = make_white_card()

    n_fade_in = int(round(BRIDGE_FADE_IN * fps))
    n_hold = int(round(BRIDGE_HOLD * fps))
    n_fade_out = int(round(BRIDGE_FADE_OUT * fps))

    idx = 0
    # Fade to white
    for i in range(n_fade_in):
        t = (i + 1) / n_fade_in
        blended = Image.blend(last_img, white, t)
        blended.save(os.path.join(out_dir, f'frame_{idx:04d}.png'))
        idx += 1
    # Hold white
    for i in range(n_hold):
        white.save(os.path.join(out_dir, f'frame_{idx:04d}.png'))
        idx += 1
    # Fade from white to first
    for i in range(n_fade_out):
        t = (i + 1) / n_fade_out
        blended = Image.blend(white, first_img, t)
        blended.save(os.path.join(out_dir, f'frame_{idx:04d}.png'))
        idx += 1
    return idx


def encode_mp4(frames_dir, out_mp4, fps=FPS):
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', os.path.join(frames_dir, 'frame_%04d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-crf', '18',
        out_mp4,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_mp4


def add_silence(audio_wav_in, audio_wav_out, silence_s):
    """Prepend `silence_s` seconds of silence to a WAV using ffmpeg."""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'anullsrc=r=24000:cl=mono',
        '-t', str(silence_s),
        '-i', audio_wav_in,
        '-filter_complex', f'[0:a][1:a]concat=n=2:v=0:a=1[a]',
        '-map', '[a]',
        '-c:a', 'pcm_s16le',
        audio_wav_out,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_wav_out


def main(seg1_mp4, seg2_mp4, out_mp4):
    """Main entry: produce the bridge MP4 between two segment MP4s."""
    seg1_dir = os.path.dirname(seg1_mp4)
    seg2_dir = os.path.dirname(seg2_mp4)
    bridge_dir = os.path.join(os.path.dirname(out_mp4), 'bridge_frames')
    last_png = os.path.join(bridge_dir, '..', 'seg1_last.png')
    first_png = os.path.join(bridge_dir, '..', 'seg2_first.png')
    os.makedirs(bridge_dir, exist_ok=True)
    extract_last_frame(seg1_mp4, last_png)
    extract_first_frame(seg2_mp4, first_png)
    n = render_bridge_frames(last_png, first_png, bridge_dir)
    print(f"Rendered {n} bridge frames ({n/FPS:.2f}s @ {fps} fps)")
    encode_mp4(bridge_dir, out_mp4, fps=FPS)
    print(f"Encoded bridge: {out_mp4} ({TOTAL_BRIDGE:.2f}s)")
    return out_mp4


if __name__ == '__main__':
    if len(sys.argv) >= 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Usage: make_bridge.py seg1_mp4 seg2_mp4 out_mp4")
        sys.exit(1)
