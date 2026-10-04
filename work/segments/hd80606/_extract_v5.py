"""
Seg 2 (HD 80606 b) round 5 paired-frame extraction.
CORRECTED REF OFFSET: HD 80606 b starts at t=10s in ref_full.mp4, NOT t=99s.
The +99 offset used in rounds 2-4 was WRONG — all those comparisons were invalid.

Extract 6 frames at our timestamps (2, 8, 14, 20, 28, 36) and the
matching ref timestamps using the CORRECT +10 offset: (12, 18, 24, 30, 38, 46).
"""
import subprocess
import os

SEG = 'hd80606'
ROUND = 5
OURS_VIDEO = f'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{SEG}/round_{ROUND}.mp4'
REF_VIDEO = 'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/ref_full.mp4'
OUT_BASE = f'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{SEG}/critic/round{ROUND}'

# CORRECTED pairs with +10 offset (ref HD 80606 b starts at t=10s)
pairs = [
    (2, 12),
    (8, 18),
    (14, 24),
    (20, 30),
    (28, 38),
    (36, 46),
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

    # Ref timestamps with CORRECTED +10 offset
    ref_out = f'{OUT_BASE}/ref/ref_t{ref_t:02d}.png'
    cmd2 = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{ref_t:.2f}',
            '-i', REF_VIDEO, '-frames:v', '1', ref_out]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    print(f'ref  t={ref_t:2d}                -> {r2.returncode} {ref_out}')

print('done — CORRECTED offset +10, not +99')
