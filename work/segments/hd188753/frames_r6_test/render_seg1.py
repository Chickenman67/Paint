"""Render 4 test frames from segment 1 round 6 to verify lib/stickman fixes."""
import sys, os
parent = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import importlib.util
spec = importlib.util.spec_from_file_location("_frames_r6", os.path.join(parent, "_frames_r6.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

OUT = os.path.join(os.path.dirname(__file__))

# 1. p1_3suns — hands_up + awed_brows (antenna fix check)
img = mod.card_p1_3suns(t=0.5)
img.save(os.path.join(OUT, "seg1_p1_3suns.png"))
print("saved seg1_p1_3suns.png")

# 2. p3_waltz — thinker pose + worried_thinker (new pose check)
img = mod.card_p3_waltz(t=0.5)
img.save(os.path.join(OUT, "seg1_p3_waltz.png"))
print("saved seg1_p3_waltz.png")

# 3. p20_weather — cowering + terrified (new pose + diamond legs check)
img = mod.card_p20_weather(t=0.5)
img.save(os.path.join(OUT, "seg1_p20_weather.png"))
print("saved seg1_p20_weather.png")

# 4. p26_sits_there — hands_down + relief (new pose check)
img = mod.card_p26_sits_there(t=0.5)
img.save(os.path.join(OUT, "seg1_p26_sits_there.png"))
print("saved seg1_p26_sits_there.png")
