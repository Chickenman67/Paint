import json, io

OUT = "C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/wasp127b/script.json"
raw = io.open(OUT, "rb").read().decode("utf-8")
o = json.loads(raw)

# 1. the HARD INVARIANT, byte level
joined = "\n".join(b["line"] for b in o["beats"])
assert joined == o["narration"], "INVARIANT BROKEN (str)"
assert joined.encode("utf-8") == o["narration"].encode("utf-8"), "INVARIANT BROKEN (bytes)"

# 2. coverage: every narration line is consumed exactly once, in order
lines = o["narration"].split("\n")
assert lines == [b["line"] for b in o["beats"]], "line coverage mismatch"
assert o["narration"].count("\n\n") == 0, "blank line present"
assert not o["narration"].endswith("\n"), "trailing newline"

# 3. word count
wc = len(o["narration"].split())
assert wc == o["word_count"] == 237, "word count mismatch %d" % wc
assert 225 <= wc <= 250

# 4. ids distinct, n sequential
ids = [b["id"] for b in o["beats"]]
assert len(set(ids)) == len(ids), "duplicate id"
assert all(b["id"] == b["id"].lower() and " " not in b["id"] for b in o["beats"]), "id not snake_case"
assert [b["n"] for b in o["beats"]] == list(range(1, len(o["beats"]) + 1)), "n not sequential"
assert 10 <= len(o["beats"]) <= 14

# 5. registers
regs = [b["register"] for b in o["beats"]]
assert all(r in ("void", "cream") for r in regs)
assert all(regs[i] != regs[i + 1] for i in range(len(regs) - 1)), "registers not alternating"

# 6. character coverage >= 4, with expression + pose, and correct colour per register
char = [b for b in o["beats"] if "stickman" in b["visual"]]
assert len(char) >= 4, "character in fewer than 4 beats"
for b in char:
    v = b["visual"].lower()
    assert ("cream stickman" in v) == (b["register"] == "void"), "wrong stickman colour on beat %d" % b["n"]
    assert "mouth" in v, "no expression on beat %d" % b["n"]
assert 12 in [b["n"] for b in char], "loaded beat 12 must carry the character"

# 7. no caption band requested
assert not any("caption band" in b["visual"] or "bottom of the frame" in b["visual"] for b in o["beats"])

# 8. fact sanity: no invented numerals beyond the sanctioned facts
import re
nums = set(re.findall(r"\b\d[\d,\.]*\b", o["narration"]))
assert nums <= {"127"}, "unexpected numerals: %s" % nums

print("ALL CHECKS PASS")
print("bytes on disk :", len(raw.encode('utf-8')))
print("words         :", wc, "| seconds @200wpm:", round(wc / 200 * 60, 1))
print("beats         :", len(o["beats"]), "| stickman beats:", [b["n"] for b in char])
print("ids           :", ", ".join(ids))
print()
print(o["narration"])
