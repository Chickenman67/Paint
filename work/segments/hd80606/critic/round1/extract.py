"""Extract paired frames at the same beat offsets from both videos, then shuffle A/B labels with a recorded seed.

Corrected reference timing: the reference's HD 80606 B segment actually starts at t=99s, not t=70s
as the original brief assumed. Mapping our [2, 8, 14, 20, 28, 36] to ref times starting at t=99.
"""
import json
import os
import random
import subprocess

OUT = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\segments\hd80606\critic\round1"
OURS = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\segments\hd80606\round_1.mp4"
REF = r"C:\VIBE_CODE_CENTRAL\Gauntlet3\work\ref_full.mp4"

# Same beat offsets (in seconds) within each video.
# Ours starts at its own t=0. The reference's HD 80606 B segment starts at t=99s.
OURS_TIMES = [2.0, 8.0, 14.0, 20.0, 28.0, 36.0]
REF_TIMES = [101.0, 107.0, 113.0, 119.0, 127.0, 135.0]

# Randomly assign labels A and B with a recorded seed.
SEED = 1337
rng = random.Random(SEED)
videos = [
    ("ours", OURS, OURS_TIMES),
    ("ref", REF, REF_TIMES),
]
rng.shuffle(videos)
LABELS = ["A", "B"]
assignment = {}
for label, (true_id, path, times) in zip(LABELS, videos):
    assignment[label] = {"true_id": true_id, "path": path, "times": times}

print("Assignment:", json.dumps({k: v["true_id"] for k, v in assignment.items()}))

# Extract frames. ffmpeg uses the input video's native rate; the reference is 60fps so we still get
# a clean frame at each target timestamp.
def extract(path, t, out):
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{t:.3f}",
        "-i", path,
        "-frames:v", "1",
        "-q:v", "2",
        out,
    ]
    subprocess.run(cmd, check=True)

for label, info in assignment.items():
    for i, t in enumerate(info["times"]):
        out = os.path.join(OUT, f"t{i}_{label}.png")
        extract(info["path"], t, out)
        print(f"  {label} t={t} -> {out}")

# Save the assignment (with seed) so we know which label is which AFTER blind rating.
with open(os.path.join(OUT, "_assignment.json"), "w") as f:
    json.dump({"seed": SEED, "assignment": {k: {"true_id": v["true_id"], "path": v["path"]} for k, v in assignment.items()}}, f, indent=2)
print("Done.")
