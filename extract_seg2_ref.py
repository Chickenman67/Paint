import subprocess, os

timestamps = [12, 20, 30, 40, 47]
ref = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/ref_full.mp4"
out_dir = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd80606/r6_critic"

for t in timestamps:
    out = os.path.join(out_dir, f"ref_t{t}.png")
    cmd = ["ffmpeg", "-y", "-ss", str(t), "-i", ref, "-vframes", "1", "-q:v", "2", out]
    subprocess.run(cmd, capture_output=True)
    print(f"t={t} -> {out}")
print("All done")
