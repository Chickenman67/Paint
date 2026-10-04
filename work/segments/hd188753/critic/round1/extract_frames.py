#!/usr/bin/env python3
"""Extract paired frames at the same timestamps from both videos.
A and B are randomly assigned (with recorded seed) so the critic does not know
which is ours and which is ref.
"""
import os
import random
import subprocess
import json
from pathlib import Path

CRITIC_DIR = Path(__file__).parent
OURS = Path("C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd188753/round_1.mp4")
REF = Path("C:/VIBE_CODE_CENTRAL/Gauntlet3/work/ref_full.mp4")
TIMESTAMPS = [2.0, 13.0, 25.0, 38.0, 50.0, 62.0]

# Record seed
SEED = 42
random.seed(SEED)

# A/B assignment: A is the first video, B is the second.
# We shuffle the pair (OURS, REF) to randomly assign.
pair = [("ours", OURS), ("ref", REF)]
random.shuffle(pair)
A_label, A_path = pair[0]
B_label, B_path = pair[1]

print(f"Seed: {SEED}")
print(f"A = {A_label} ({A_path})")
print(f"B = {B_label} ({B_path})")

# Save mapping
mapping = {
    "seed": SEED,
    "A": {"label": A_label, "path": str(A_path)},
    "B": {"label": B_label, "path": str(B_path)},
}
with open(CRITIC_DIR / "mapping.json", "w") as f:
    json.dump(mapping, f, indent=2)

# Extract frames
for t in TIMESTAMPS:
    tlabel = f"t{int(t*2):02d}"  # 2->04, 13->26, 25->50, 38->76, 50->100, 62->124
    # Actually use the spec naming: t<N>_A.png where N is the int(2*t)? The spec says t = 2.0 -> t2_A.png likely
    # Re-read spec: "naming `t<N>_A.png` and `t<N>_B.png`" with N being timestamp
    # Use t with one decimal -> e.g. t2.0_A.png
    safe_t = f"{t:.1f}"
    for which, vid in (("A", A_path), ("B", B_path)):
        out = CRITIC_DIR / f"t{safe_t}_{which}.png"
        # Use ffmpeg to seek to nearest frame and extract
        # For 30fps video at 2s, that's frame 60.
        # For 60fps ref, it's frame 120.
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", str(t), "-i", str(vid),
            "-frames:v", "1", "-q:v", "2",
            str(out)
        ]
        subprocess.run(cmd, check=True)
        print(f"  Wrote {out.name}")

print("Done extracting frames.")
