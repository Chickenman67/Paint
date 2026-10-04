"""
Seg 2 (HD 80606 b) round 4 paired-frame extraction.
Extract 6 frames at our timestamps (2, 8, 14, 20, 28, 36) and the
matching ref timestamps (101, 107, 113, 119, 127, 135) which fall inside
the HD 80606 b segment in the reference video.
"""
import subprocess
import os

SEG = 'hd80606'
ROUND = 4
OURS_VIDEO = f'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{SEG}/round_{ROUND}.mp4'
REF_VIDEO = 'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/ref_full.mp4'
OUT_BASE = f'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{SEG}/critic/round{ROUND}'

pairs = [
    (2, 101),
    (8, 107),
    (14, 113),
    (20, 119),
    (28, 127),
    (36, 135),
]

for sub in ['ours', 'ref']:
    os.makedirs(os.path.join(OUT_BASE, sub), exist_ok=True)

for ours_t, ref_t in pairs:
    # Cap ours_t at video duration (40s)
    ours_tc = min(ours_t, 39.5)
    ours_out = f'{OUT_BASE}/ours/ours_t{ours_t:02d}.png'
    cmd1 = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{ours_tc:.2f}',
            '-i', OURS_VIDEO, '-frames:v', '1', ours_out]
    r1 = subprocess.run(cmd1, capture_output=True, text=True)
    print(f'ours t={ours_t:2d} (clamp {ours_tc:.2f}s) -> {r1.returncode} {ours_out}')

    # Ref timestamps come from the HD 80606 b segment in the reference video
    # (offset is +99 from ours based on round 2/3 pairing).
    ref_out = f'{OUT_BASE}/ref/ref_t{ref_t}.png'
    cmd2 = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{ref_t:.2f}',
            '-i', REF_VIDEO, '-frames:v', '1', ref_out]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    print(f'ref  t={ref_t:3d}                -> {r2.returncode} {ref_out}')

print('done')
