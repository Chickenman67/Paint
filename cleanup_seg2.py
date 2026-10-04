import os, glob

# Check seg2 r6_critic for stale files
out_dir = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd80606/r6_critic"

# Expected: ours at t=3,10,20,30,37 and ref at t=12,20,30,40,47
# Stale: ref_t3, ref_t10, ref_t37 (these were extracted at ours timestamps without offset)
stale = ["ref_t3.png", "ref_t10.png", "ref_t37.png"]
for name in stale:
    path = os.path.join(out_dir, name)
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed stale: {name}")
    else:
        print(f"Not found: {name}")

# List remaining
print("\nRemaining in seg2 r6_critic:")
for f in sorted(os.listdir(out_dir)):
    size = os.path.getsize(os.path.join(out_dir, f))
    print(f"  {f} ({size} bytes)")
