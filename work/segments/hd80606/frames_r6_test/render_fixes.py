"""Quick test: render 3 frames to verify round 6b fixes."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'frames_r6_src'))
# Actually, just import the module directly
sys.path.insert(0, os.path.dirname(__file__))
parent = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent)

import importlib.util
spec = importlib.util.spec_from_file_location("_frames_r6", os.path.join(parent, "_frames_r6.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

OUT = os.path.join(os.path.dirname(__file__))

# 1. Intro card — hands_up pose (should NOT have triangle above head)
img = mod.card_intro(t=0.5)
img.save(os.path.join(OUT, "test_intro_fix.png"))
print("saved test_intro_fix.png")

# 2. "800X STARLIGHT" card — stickman should NOT overlap sun
img = mod.card_so_close_part2(t=0.5)
img.save(os.path.join(OUT, "test_800x_fix.png"))
print("saved test_800x_fix.png")

# 3. "FIVE. HUNDRED." — pure stickman, should look good
img = mod.card_pure_stickman(t=0.3)
img.save(os.path.join(OUT, "test_five_hundred_fix.png"))
print("saved test_five_hundred_fix.png")

# 4. "SO CLOSE" part1 — stickman cowering left, planet+sun right
img = mod.card_so_close_part1(t=0.5)
img.save(os.path.join(OUT, "test_so_close_fix.png"))
print("saved test_so_close_fix.png")
