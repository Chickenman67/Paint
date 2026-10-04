# work/lib/transition.py — Cross-segment bridge logic.
# Per ref_style_spec.md ## Motion + Transitions, the inter-segment bridge is:
#   - 1.0 s cross-fade to white
#   - 2.25 s blank white card held
#   - 0.5 s cross-fade out (typical)
#   - hard cut into new segment with header appearing simultaneously
#   - The new segment's first card is held ~42 s with progressive in-card motion
#
# This contradicts CLAUDE.md §5.7 which said "0.5 s black frame". The reference
# uses a white bridge. We follow the reference.

from PIL import Image

W, H = 1280, 720

# Inter-segment bridge durations (from reference measurements)
BRIDGE_FADE_IN = 1.0   # cross-fade to white
BRIDGE_HOLD = 2.25     # held blank white
BRIDGE_FADE_OUT = 0.5  # cross-fade out of white

# Total bridge = ~3.75 s
TOTAL_BRIDGE = BRIDGE_FADE_IN + BRIDGE_HOLD + BRIDGE_FADE_OUT


def make_white_card(width=W, height=H, color=(255, 255, 255)):
    """A blank white card — the reference's bridge."""
    return Image.new('RGB', (width, height), color)


def render_bridge(last_frame, first_frame, fps, out_path):
    """Render the full bridge sequence as a sequence of PNGs and an MP4.

    last_frame: PIL Image of the segment-1 closing card
    first_frame: PIL Image of the segment-2 intro card
    fps: target fps
    out_path: output MP4 path
    """
    import subprocess
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        # Fade to white
        n_fade_in = int(round(BRIDGE_FADE_IN * fps))
        for i in range(n_fade_in):
            t = (i + 1) / n_fade_in
            blended = Image.blend(last_frame, make_white_card(), t)
            blended.save(os.path.join(tmp, f'frame_{i:04d}.png'))

        # Hold white
        n_hold = int(round(BRIDGE_HOLD * fps))
        for i in range(n_hold):
            make_white_card().save(os.path.join(tmp, f'frame_{n_fade_in + i:04d}.png'))

        # Fade out (white -> first frame)
        n_fade_out = int(round(BRIDGE_FADE_OUT * fps))
        start = n_fade_in + n_hold
        for i in range(n_fade_out):
            t = (i + 1) / n_fade_out
            blended = Image.blend(make_white_card(), first_frame, t)
            blended.save(os.path.join(tmp, f'frame_{start + i:04d}.png'))

        # Encode as MP4
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-i', os.path.join(tmp, 'frame_%04d.png'),
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-crf', '18',
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return out_path
