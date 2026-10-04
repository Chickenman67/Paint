# Build work/segments/psoj3185/script.json for PSO J318.5-22.
# The narration string is DERIVED from the beat lines so the two are byte-identical by construction.

import json
import os

BEATS = [
    dict(
        n=1,
        id="hook_a_sun_you_know",
        beat="HOOK",
        register="void",
        lines=[
            "Every planet you have met so far had a sun.",
            "A star to rise into, and set behind.",
        ],
        visual="Deep navy starfield with one small yellow sun at upper right; the cream stickman stands at lower left, flat-line mouth, shading his eyes.",
    ),
    dict(
        n=2,
        id="ejection_neighbor_comes_too_close",
        beat="SETUP",
        register="cream",
        lines=[
            "This one lost all of that.",
            "Something kicked it out of its system.",
            "A neighbor, moving too close, too fast.",
        ],
        visual="Cream paper card with two wobble-outlined planets crossing at center and a dashed escape arc flying off the right edge; the dark stickman stands at left with both hands up, wide oval mouth.",
    ),
    dict(
        n=3,
        id="thrown_into_the_between",
        beat="ESCAPE",
        register="void",
        lines=[
            "Thrown loose into the dark between the stars.",
            "It has been falling ever since.",
        ],
        visual="Void starfield with the rogue planet small and dead center trailing one long thin motion streak to the left edge; no character - pure data beat.",
    ),
    dict(
        n=4,
        id="no_star_to_orbit",
        beat="SETUP",
        register="cream",
        lines=[
            "It drifts through interstellar space, and nothing slows it.",
            "No star to orbit.",
            "No sunrise. No sunset. Nothing to rise or set.",
        ],
        visual="Cream paper card showing the rogue planet alone at the center of an empty dashed orbital grid with no star anywhere in it; no character - pure data beat.",
    ),
    dict(
        n=5,
        id="no_light_of_its_own",
        beat="REVEAL",
        register="void",
        lines=[
            "No light of its own.",
            "It is only ever lit by what other stars leak.",
        ],
        visual="Void starfield with the planet drawn as a black disk rimmed by the faintest gray wash thrown from four tiny far-off stars; no character - pure data beat.",
    ),
    dict(
        n=6,
        id="barely_enough_to_see",
        beat="PAYOFF",
        register="cream",
        lines=[
            "A thin drizzle of scattered light, from impossibly far away.",
            "Barely enough to see by.",
            "Barely enough for anyone to be seen.",
        ],
        visual="Cream paper card where the planet is a flat gray smudge barely darker than the page; the dark stickman at right leans forward to shield his eyes, downturned arc mouth.",
    ),
    dict(
        n=7,
        id="what_rogue_means",
        beat="CONTEXT",
        register="void",
        lines=[
            "This is what it means to be a rogue planet.",
            "No parent star. No system. No address at all.",
        ],
        visual="Void card with a hand-lettered list of a star, a system, and an address, each item crossed out in red; the cream stickman at left shrugs with a flat-line mouth.",
    ),
    dict(
        n=8,
        id="coldest_and_darkest",
        beat="ESCALATE",
        register="cream",
        lines=[
            "Among the coldest objects we have ever measured.",
            "Among the very darkest we know of.",
            "Nothing about this world is friendly.",
        ],
        visual="Cream paper card with a hand-drawn thermometer and a darkness gauge side by side, both needles pegged at the far end of their scales; no character - pure data beat.",
    ),
    dict(
        n=9,
        id="less_than_darkness",
        beat="PAYOFF",
        register="void",
        lines=[
            "Imagine standing there, and seeing nothing at all.",
            "Not darkness. Less than darkness.",
            "You would never find the edge of the ground.",
        ],
        visual="Void card with the planet's curved black limb sweeping across the bottom under one enormous empty starfield; the cream stickman stands tiny on the limb, both hands up, wide oval mouth.",
    ),
    dict(
        n=10,
        id="the_dust_ring",
        beat="REVEAL",
        register="cream",
        lines=[
            "A small ring of dust still orbits it.",
            "Leftovers from a system that no longer exists.",
        ],
        visual="Cream paper card with a thin wobbly ellipse of dust specks drawn around a plain dark circle; no character - pure data beat.",
    ),
    dict(
        n=11,
        id="a_suns_worth_of_wreckage",
        beat="ESCALATE",
        register="void",
        lines=[
            "A whole sun's worth of wreckage, in one thin circle.",
            "It circles nothing at all.",
            "The dust keeps its shape out of pure habit.",
        ],
        visual="Void card where the dust ring glows faint amber against the black while the planet inside it is completely unlit; no character - pure data beat.",
    ),
    dict(
        n=12,
        id="it_passes_you",
        beat="PAYOFF",
        register="cream",
        lines=[
            "You are watching it pass, and it will never know you.",
            "And you will never get there.",
        ],
        visual="Cream paper card with a small dark dot sliding left to right across the middle trailing a dotted line; the dark stickman at right watches it go, flat-line mouth, one hand shading his eyes.",
    ),
    dict(
        n=13,
        id="the_loneliest_thing_found",
        beat="FINALE",
        register="void",
        lines=[
            "It is the loneliest thing we have ever found.",
        ],
        visual="Void starfield, nearly empty, with the rogue planet a single dark speck at center; the cream stickman stands at lower right, head tipped back, wide oval mouth, utterly still.",
    ),
]

narration = "\n".join("\n".join(b["lines"]) for b in BEATS)
word_count = len(narration.split())
est_wpm = 200

beats_out = [
    {
        "n": b["n"],
        "id": b["id"],
        "beat": b["beat"],
        "register": b["register"],
        "line": "\n".join(b["lines"]),
        "visual": b["visual"],
    }
    for b in BEATS
]

obj = {
    "title": "PSO J318.5-22 - The Loneliest Planet",
    "wrote_to": "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/psoj3185/script.json",
    "narration": narration,
    "word_count": word_count,
    "est_wpm": est_wpm,
    "beats": beats_out,
}

path = obj["wrote_to"]
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8", newline="") as f:
    json.dump(obj, f, ensure_ascii=False, indent=2)
    f.write("\n")

# ---- self verification, against the file just written ----
with open(path, "r", encoding="utf-8") as f:
    back = json.load(f)

rejoined = "\n".join(bt["line"] for bt in back["beats"])
checks = {
    "byte_identical": rejoined.encode("utf-8") == back["narration"].encode("utf-8"),
    "word_count_matches": back["word_count"] == len(back["narration"].split()),
    "word_count_in_range_225_250": 225 <= back["word_count"] <= 250,
    "beat_count_in_range_10_14": 10 <= len(back["beats"]) <= 14,
    "ids_unique": len({bt["id"] for bt in back["beats"]}) == len(back["beats"]),
    "ids_snake_case": all(bt["id"].replace("_", "").isalnum() and bt["id"].islower() for bt in back["beats"]),
    "beat_n_sequential": [bt["n"] for bt in back["beats"]] == list(range(1, len(back["beats"]) + 1)),
    "registers_valid": all(bt["register"] in ("void", "cream") for bt in back["beats"]),
    "registers_alternate": all(
        back["beats"][i]["register"] != back["beats"][i + 1]["register"]
        for i in range(len(back["beats"]) - 1)
    ),
    "no_blank_lines": all("" in ln for ln in []) and "\n\n" not in back["narration"],
    "est_seconds_ok": 65 <= (back["word_count"] / back["est_wpm"] * 60) <= 80,
}
line_word_counts = [(ln, len(ln.split())) for ln in back["narration"].split("\n")]
checks["all_lines_4_to_14_words"] = all(4 <= w <= 14 for _, w in line_word_counts)

char_beats = [
    bt["n"] for bt in back["beats"]
    if ("cream stickman" in bt["visual"] or "dark stickman" in bt["visual"])
]
checks["character_in_4_plus_beats"] = len(char_beats) >= 4

# register/character-color coherence
checks["character_color_matches_register"] = all(
    not (
        bt["register"] == "void" and "dark stickman" in bt["visual"]
    ) and not (
        bt["register"] == "cream" and "cream stickman" in bt["visual"]
    )
    for bt in back["beats"]
)

print(json.dumps({k: v for k, v in checks.items()}, indent=2))
print("word_count:", back["word_count"])
print("est_seconds:", round(back["word_count"] / back["est_wpm"] * 60, 1))
print("character beats:", char_beats)
bad = [(ln, w) for ln, w in line_word_counts if not (4 <= w <= 14)]
print("out-of-range lines:", bad)
print("ALL PASS:", all(checks.values()))