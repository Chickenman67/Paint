import json, io, sys, os

TITLE = "WASP-127b - The Planet That Throws Its Own Sky Away"
OUT = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/wasp127b/script.json"

beats = [
    (1, "hurricane_forget_it", "HOOK", "void",
     "You know how a hurricane shoves you flat across open ground. Remember that. It is nothing.",
     "Wide starfield with a thin cream spiral of hurricane wind-lines arcing off the right edge; the cream stickman stands braced at left, feet planted, flat-line deadpan mouth."),
    (2, "name_the_planet", "REVEAL", "cream",
     "This is WASP-127b. A gas giant, far too close to its own star. And it is almost nothing.",
     "Cream paper card: a fat flat gas-giant portrait crowded against a huge orange star at the frame edge, with a wobbly arrow between them; no character."),
    (3, "fastest_winds", "DATA", "void",
     "The fastest winds ever measured on an exoplanet. Thousands of kilometers per hour, hour after hour.",
     "Three stacked yellow speed bars stacked to the right of a cream stickman pointing up at streaming wind ribbons, wide oval awed mouth, one arm raised."),
    (4, "never_land", "DATA", "cream",
     "They cross the entire planet without ever touching down anywhere. Nothing like that should hold together.",
     "Cream diagram card: the planet drawn as a plain oval with five long horizontal wind arrows crossing it edge to edge, none of them ending; no character."),
    (5, "almost_empty", "DATA", "void",
     "And inside all that fury, the planet is almost empty. One of the lowest densities ever measured.",
     "Pure data card: two grey circles side by side, one full banded giant and one almost hollow ring, with a low-density stamp; no character."),
    (6, "nothing_inside", "PIVOT", "cream",
     "A giant with nothing inside it, screaming at thousands of kilometers per hour. You cannot stand on that.",
     "Dark stickman shrugging with both palms up and a zigzag uncomfortable mouth, standing on a flat olive ground band under a plain sky, planet glowing behind him."),
    (7, "read_the_star", "METHOD", "void",
     "So you do what astronomers do. You read the star's light instead of standing out in the wind.",
     "Instrument diagram on black: a small star at left firing a white light-arrow into a prism at center, fanning out into a banded spectrum bar; no character."),
    (8, "swallowed_colors", "METHOD", "cream",
     "You map the atmosphere by watching which colors of starlight get swallowed on the way in.",
     "Cream card: the spectrum bar at center with dark bites taken out of it, and the dark stickman at right pointing straight at the bites, flat-line deadpan mouth."),
    (9, "missing_tells_you", "MECHANISM", "void",
     "Whatever colors are missing, exactly, tell you what is standing up there in the dark.",
     "Pure data card: the spectrum bar with three slices crossed out in red and a single small water drop drifting up off the top of the frame; no character."),
    (10, "water_leaving", "REVEAL", "cream",
     "Water. Leaving. Upward, fast, and not falling back down. Just going out, past the edge of everything.",
     "Cream card with no character: the planet low in frame trailing a dotted rising path off the top, three burst marks at the exit point and a long up-arrow."),
    (11, "grains_high_above", "REVEAL", "void",
     "And a thin haze of small grains, floating far too high above the top of the cloud deck.",
     "Close-up of the planet's upper limb on a starfield with a thin stippled band of tiny grains suspended far above it; no character."),
    (12, "throwing_its_away", "PIVOT", "cream",
     "That is not a planet holding its air. That is a planet throwing it away.",
     "Dark stickman with both hands up, downturned scared arc mouth with pink interior, standing on the olive ground band as the planet slides off the left edge."),
    (13, "leak_no_bottom", "LOADED", "void",
     "The air does not come back. Your sky has a leak, and that leak has no bottom at all.",
     "Cream stickman at left shading his eyes and looking off-frame right, wide oval awed mouth, small against an empty black sky with one thin leak-line running down it."),
    (14, "too_far_to_help", "CLOSE", "cream",
     "You are watching it from far too away to help. That is the whole story of this world.",
     "Cream paper closing card: the tiny planet alone at center of a huge empty field inside one thin wobbly hand-drawn circle; no character."),
]

narration = "\n".join(b[4] for b in beats)
word_count = len(narration.split())

obj = {
    "title": TITLE,
    "wrote_to": OUT,
    "narration": narration,
    "word_count": word_count,
    "est_wpm": 200,
    "beats": [
        {"n": b[0], "id": b[1], "beat": b[2], "line": b[4], "visual": b[5], "register": b[3]}
        for b in beats
    ],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(obj, ensure_ascii=False, indent=2))

# ---- verification ----
with io.open(OUT, "r", encoding="utf-8", newline="") as f:
    raw = f.read()
back = json.loads(raw)

rebuilt = "\n".join(b["line"] for b in back["beats"])
ok_inv = (rebuilt == back["narration"])
ok_bytes = (rebuilt.encode("utf-8") == back["narration"].encode("utf-8"))
ids = [b["id"] for b in back["beats"]]
ok_ids = len(set(ids)) == len(ids)
char = [b["n"] for b in back["beats"] if "stickman" in b["visual"]]
reg = [b["register"] for b in back["beats"]]
ok_alt = all(reg[i] != reg[i + 1] for i in range(len(reg) - 1))
wc_line = sum(len(b["line"].split()) for b in back["beats"])

print("word_count field      :", back["word_count"])
print("sum of beat lines     :", wc_line)
print("len(narration.split()):", len(back["narration"].split()))
print("in range 225-250      :", 225 <= back["word_count"] <= 250)
print("invariant (str)       :", ok_inv)
print("invariant (bytes)     :", ok_bytes)
print("beats                 :", len(back["beats"]))
print("distinct ids          :", ok_ids)
print("registers             :", " ".join(r[0] for r in reg), "| strictly alternating:", ok_alt)
print("stickman beats        :", char, "count:", len(char))
print("est seconds @200wpm   :", round(back["word_count"] / 200.0 * 60, 1))
