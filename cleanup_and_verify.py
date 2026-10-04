import os

# Remove temporary scripts
for script in ["extract_seg2_ref.py", "cleanup_seg2.py", "extract_seg2_ref50.py"]:
    path = f"C:/VIBE_CODE_CENTRAL/Gauntlet3/{script}"
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed: {script}")

# Verify all frames
for seg, base in [("Seg1 hd188753", "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd188753/r6_critic"),
                  ("Seg2 hd80606", "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/hd80606/r6_critic")]:
    print(f"\n{seg}:")
    for f in sorted(os.listdir(base)):
        size = os.path.getsize(os.path.join(base, f))
        print(f"  {f} ({size} bytes)")
