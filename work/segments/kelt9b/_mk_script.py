"""Build KELT-9b script.json. Narration lines are the single source of truth;
the beats' `line` fields are slices of that list, joined by newlines, so the
downstream alignment invariant holds by construction."""
import json
import os

LINES = [
    "This is the hottest planet ever found.",
    "It is hotter than most stars in the galaxy.",
    "Not a little hotter. Considerably hotter.",
    "Even the word planet feels like rounding it up.",
    "Its name is KELT plus nine b.",
    "It circles closer than any planet should.",
    "One year there lasts about a day and a half.",
    "Nothing about the arrangement is survivable for long.",
    "The sunrise there happens once every day and a half.",
    "Because it never turns its back on the star.",
    "The star it rides is a blue furnace, spinning fast.",
    "Up there it is hotter than the planet it made.",
    "The planet is cooking in a light most stars never give.",
    "Its dayside reaches about forty-six hundred degrees.",
    "That is not a temperature. That is a warning.",
    "Hydrogen molecules get torn apart before they can settle.",
    "Its atmosphere is pulled apart and dragged off into space.",
    "It leaves a glowing tail, forever losing weight.",
    "Here is the part that should stop you.",
    "On the dayside, atoms begin to come undone.",
    "The bonds that make matter simply lose.",
    "This is a planet disassembling itself in plain view.",
    "The night side is almost gentle by comparison.",
    "One half of it survives. The other half does not.",
    "And there is nowhere cooler to stand.",
    "No ocean. No shade. No door.",
    "Just a point you would call a star from far off.",
    "You would call it a planet. You would be generous.",
    "Somewhere out there, right now, it is happening.",
]

# (id, beat_label, first_line_index, last_line_index_inclusive, register, visual)
BEATS = [
    ("hook", "HOOK", 0, 2, "void",
     "A blazing white star fills the upper right of a deep navy starfield with a "
     "yellow floating caption of its face temperature, and the cream stickman stands "
     "at lower left in a flat-line deadpan mouth, arms loose, looking straight up at it."),
    ("the_record", "THE RECORD", 3, 4, "cream",
     "On cream paper a hand-drawn ranked list of the hottest known worlds runs down the "
     "left with KELT-9b stamped at the top, and the dark stickman stands at right "
     "mid-shrug with a zigzag uncomfortable mouth, palms up."),
    ("the_orbit", "THE ORBIT", 5, 6, "void",
     "A tight white orbit circle wraps a bright blue star in the center of a dark "
     "starfield, and the cream stickman stands beside it in a wide oval awed mouth, "
     "head tipped back, pointing up at the nearest point of the track."),
    ("no_escape", "NO ESCAPE", 7, 9, "cream",
     "A cream card splits into a lit half and a dark half with a single arrow showing "
     "the planet never rotating away, and the dark stickman stands at the seam in a "
     "downturned-arc scared mouth, shielding his eyes with one forearm."),
    ("the_star", "THE STAR", 10, 11, "void",
     "A hot blue A-type star with visible surface granulation dominates a deep navy "
     "frame beside a small dull planet dot, and the cream stickman stands at lower "
     "right with a wide oval awed mouth, one hand raised toward the star."),
    ("the_light", "THE LIGHT", 12, 12, "cream",
     "A cream card shows a white star on the left firing broad parallel rays onto a "
     "pale outlined planet on the right, and the dark stickman crouches beside the "
     "planet with a flat-line deadpan mouth, one finger pointing into the ray bundle."),
    ("the_dayside", "THE DAYSIDE", 13, 14, "void",
     "A close crescent of KELT-9b glows white-hot orange along its sunward edge "
     "against a black starfield with a 4600F annotation in yellow, and the cream "
     "stickman stands in the glow with a zigzag uncomfortable mouth, hands up near his "
     "face."),
    ("molecules", "DISSOCIATION", 15, 17, "cream",
     "On cream paper a neat row of paired hydrogen circles drifts apart into separate "
     "dots with arrows separating them, and a comet-like tail of escaping gas trails "
     "the planet at right, while the dark stickman stands below in a downturned-arc "
     "scared mouth, hands up."),
    ("the_warning", "THE WARNING", 18, 19, "void",
     "A single sharp yellow line separates a cool left hemisphere from a white-hot "
     "right hemisphere on a dark card, and the cream stickman stands at left in a "
     "zigzag uncomfortable mouth, half turned away from the bright side."),
    ("unraveling", "UNRAVELING", 20, 23, "cream",
     "A cream card shows the dayside losing its lattice: a tidy grid of joined dots "
     "on the left breaking into scattered unconnected dots on the right, and the dark "
     "stickman stands beneath in a wide oval awed mouth, shrugging at the scattered "
     "half."),
    ("nowhere_cool", "NOWHERE COOL", 24, 26, "void",
     "A dark card lists three crossed-out icons in a row, ocean, shade, door, each "
     "struck through in red ink, and the cream stickman stands below them in a "
     "downturned-arc scared mouth, arms crossed tight."),
    ("closer", "CLOSER", 27, 28, "cream",
     "A cream card shows KELT-9b as a small bright point among other far-off stars "
     "with a long distance arrow pointing to it, and the dark stickman stands at lower "
     "right in a flat-line deadpan mouth, shrugging, palm up toward the dot."),
]

narration = "\n".join(LINES)

beats = []
for n, (bid, label, a, b, reg, vis) in enumerate(BEATS, start=1):
    beats.append({
        "n": n,
        "id": bid,
        "beat": label,
        "line": "\n".join(LINES[a:b + 1]),
        "visual": vis,
        "register": reg,
    })

# --- invariants -------------------------------------------------------------
ids = [bt["id"] for bt in beats]
assert len(set(ids)) == len(ids), "duplicate beat id"
assert len(LINES) == sum(len(bt["line"].split("\n")) for bt in beats), "line count drift"
assert "\n".join(bt["line"] for bt in beats) == narration, "narration/beat mismatch"
covered = [ln for bt in beats for ln in bt["line"].split("\n")]
assert covered == LINES, "beats do not cover narration in order"
assert all(4 <= len(LINES[i].split()) <= 14 for i in range(len(LINES))), \
    [(i, LINES[i], len(LINES[i].split())) for i in range(len(LINES))
     if not 4 <= len(LINES[i].split()) <= 14]
regs = [bt["register"] for bt in beats]
for i in range(1, len(regs)):
    assert regs[i] != regs[i - 1], f"registers not alternating at beat {i + 1}"
assert regs[0] == "void"

word_count = len(narration.split())

out = {
    "title": "KELT-9b, the planet hotter than a star",
    "wrote_to": "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/kelt9b/script.json",
    "narration": narration,
    "word_count": word_count,
    "est_wpm": 200,
    "beats": beats,
}

os.makedirs("C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/kelt9b", exist_ok=True)
with open(out["wrote_to"], "w", encoding="utf-8", newline="\n") as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print(f"words={word_count}  lines={len(LINES)}  beats={len(beats)}  "
      f"dur@200={word_count / 200 * 60:.1f}s")
print("character beats:", sum(1 for v in (b["visual"] for b in beats)
                              if "stickman" in v))