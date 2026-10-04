# Generates script.json for WASP-17b and guarantees the newline invariant:
# beats joined with "\n" == narration.
import json, os

B = []


def beat(bid, kind, register, lines, visual):
    B.append({
        "n": len(B) + 1,
        "id": bid,
        "beat": kind,
        "register": register,
        "line": "\n".join(lines),
        "visual": visual,
    })


beat("backwards_hook", "HOOK", "void", [
    "This planet goes the wrong way around its star.",
], "Deep navy starfield with a banded gas giant filling the right half and one fat hand-drawn arrow curling backwards around it, with the cream stickman standing at lower left, flat-line mouth, deadpan, head tipped back to watch the arrow.")

beat("everyone_else_turns", "SETUP", "cream", [
    "Almost every other world in the galaxy turns the same direction.",
    "This one runs backwards.",
], "Cream paper card with a single yellow star at center and six small planets orbiting it in tidy same-direction arrows, one of them drawn on a reversed arrow, with the dark stickman at the right edge shrugging, zigzag mouth, uncomfortable.")

beat("not_made_here", "TURN", "void", [
    "It was never made here.",
    "It was thrown, or captured, or flung into this orbit.",
], "Void card where the gas giant streaks in from off-frame on a hard jagged diagonal, its birthplace ghosted as a dashed circle far away, with the cream stickman at lower right pointing up the path, wide oval mouth, awed.")

beat("wrong_way_explained", "WHY", "cream", [
    "There is no ordinary reason for a world to turn against its star.",
    "Whatever put it here left it there.",
], "Cream card with two rough inked stamp boxes up top labeled CAPTURED and FLUNG, each holding a tiny careless sketch, and the dark stickman below them pointing at the left box, flat-line mouth, deadpan, standing.")

beat("almost_nothing_there", "REVEAL", "void", [
    "Now look at how little of it is actually there.",
    "It is one of the puffiest planets we have ever measured.",
], "Void card with the gas giant drawn as a thin, faint balloon outline inside its own oversized ring, most of the ring empty black, with the cream stickman at lower left with a downturned arc mouth, scared, hands up.")

beat("cork_density", "LOW_DENSITY", "cream", [
    "So low in density that it floats like a cork.",
    "A world the size of Jupiter, made of almost nothing.",
], "Cream card with a wine cork at left and a Jupiter-sized planet silhouette at right sitting on a thin seesaw beam that barely dips, with the dark stickman crouched by the beam, zigzag mouth, uncomfortable, shrugging.")

beat("should_have_collapsed", "TENSION", "void", [
    "It should have collapsed into itself a long time ago.",
    "The heat down inside holds it open. That is all.",
], "Void card with the planet's outer layers drawn as torn onion contours pressing inward on a small red-orange core, cracks spidering across the shell, with the cream stickman at the far left shielding his eyes, downturned arc mouth, scared.")

beat("cloud_wall", "CLOUDS", "cream", [
    "Its clouds stack so high they look like a wall of weather.",
    "And the wind in them never stops.",
], "Cream card where a towering vertical stack of flat cloud bands fills nearly the whole frame, small arrows drifting sideways along every band, with the dark stickman at bottom left head tipped straight back, wide oval mouth, awed, looking up.")

beat("endless_wind", "WINDS", "void", [
    "The whole atmosphere just runs, endlessly, around the day side.",
    "Those clouds move faster than anything that size should.",
], "Void card with long looping wind streamlines wrapping the planet's day side in a dense ribbon of arrows, all sweeping the same way, with the cream stickman braced at lower left, one arm over his face, zigzag mouth, uncomfortable.")

beat("dayside_1700", "HEAT", "cream", [
    "The side facing the star hits seventeen hundred degrees.",
], "Cream card dominated by one fat hand-drawn temperature column filled to the top and labeled 1700 C, with heat squiggles rising off it and a tiny planet pressed against its left edge, and the dark stickman standing motionless beside it, downturned arc mouth, scared.")

beat("you_would_not", "FATE", "void", [
    "You would not land here.",
    "You would not orbit here.",
    "You would not want to fall asleep here.",
], "Void card, almost empty starfield with one very small planet far off-center and a lot of dead space around it, with the cream stickman small at lower center taking one step backward, hands up, downturned arc mouth, scared.")

beat("three_wrongs", "RECAP", "cream", [
    "Backwards spin. Almost no weight. Endless wind.",
    "A planet that lost its place and never noticed.",
    "Every part of it is wrong.",
], "Cream card with three short checklist lines stacked at the left reading WRONG WAY, ALMOST NO WEIGHT, ENDLESS WIND, each ticked off in ink, with the dark stickman at the right shrugging, flat-line mouth, deadpan.")

beat("never_supposed_to_be_here", "CLOSER", "void", [
    "You are looking at a world nobody planned.",
    "It is still there. It is still turning.",
    "It was never supposed to be here.",
], "Void card with the gas giant alone and small at the center of a wide empty starfield, one faint retrograde arrow looping it, and the cream stickman at lower left standing with hands lowered, wide oval mouth, awed.")

narration = "\n".join(b["line"] for b in B)
words = len(narration.split())

obj = {
    "title": "WASP-17b: The Planet That Runs Backwards",
    "wrote_to": "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/wasp17b/script.json",
    "narration": narration,
    "word_count": words,
    "est_wpm": 200,
    "beats": B,
}

# invariants
assert "\n\n" not in narration, "blank line in narration"
assert narration == "\n".join(b["line"] for b in B)
ids = [b["id"] for b in B]
assert len(ids) == len(set(ids)), "duplicate beat id"
assert 10 <= len(B) <= 14, len(B)
chars = sum(1 for b in B if "stickman" in b["visual"])
print("beats:", len(B), "words:", words, "wpm-adjusted:", round(words / (len(narration) and 1), 0))
print("stickman beats:", chars)
for ln in narration.split("\n"):
    n = len(ln.split())
    assert 4 <= n <= 14, (n, ln)
    print(f"{n:>3}  {ln}")

path = obj["wrote_to"]
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(obj, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", path)