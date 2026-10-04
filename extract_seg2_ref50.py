import subprocess
import os

ref = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/ref_full.mp4"
out = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd80606/r6_critic/ref_t50.png"
cmd = ["ffmpeg", "-y", "-ss", "50", "-i", ref, "-vframes", "1", "-q:v", "2", out]
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"Extracted: {out} (exists={os.path.exists(out)}, size={os.path.getsize(out) if os.path.exists(out) else 'N/A'})")
