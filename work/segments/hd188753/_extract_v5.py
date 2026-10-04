import subprocess
import os

OUT_DIR_OURS = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\segments\hd188753\critic\round5\ours"
OUT_DIR_REF = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\segments\hd188753\critic\round5\ref"
OURS_VIDEO = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\segments\hd188753\round_5.mp4"
REF_VIDEO = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\ref_full.mp4"

# HD 188753 Ab starts at t=10s in ref_full.mp4 per memory note
REF_OFFSET = 10

os.makedirs(OUT_DIR_OURS, exist_ok=True)
os.makedirs(OUT_DIR_REF, exist_ok=True)

ours_ts = [2, 8, 14, 20, 28, 36]

for t in ours_ts:
    out = os.path.join(OUT_DIR_OURS, f"ours_t{t:02d}.png")
    cmd = ["ffmpeg", "-y", "-ss", str(t), "-i", OURS_VIDEO, "-frames:v", "1", out]
    print("OURS:", " ".join(cmd))
    subprocess.run(cmd, capture_output=True)

for t in ours_ts:
    ref_t = t + REF_OFFSET
    out = os.path.join(OUT_DIR_REF, f"ref_t{t:02d}.png")
    cmd = ["ffmpeg", "-y", "-ss", str(ref_t), "-i", REF_VIDEO, "-frames:v", "1", out]
    print("REF:", " ".join(cmd))
    subprocess.run(cmd, capture_output=True)

print("Done.")
