# STYLOCANON-2 — measured from `work/ref2/ref_full.mp4`

**Source:** https://www.youtube.com/watch?v=yMwWSX_cvrc — 875.514s, 1280×720, **60 fps**, AV1.
This file **OVERRIDES** `work/STYLE_CANON.md` and the type/colour numbers in `CLAUDE.md` §4/§7.
It supersedes the old Paint-Explainer reference. Everything below was measured from
frames extracted directly from the file, not from a description.

---

## 0. What this reference actually is

A **"most classified places" listicle**: 9 chapters (Pine Gap, Area 51, Tomb of Qin Shi
Huang, Room 39, Mezhgorye, Cheyenne Mountain, Svalbard Global Seed Vault, Fort Knox,
Vatican Archives). It is *not* an exoplanet video. Our content stays 12 exoplanets;
this file governs **style, pacing, animation, and typography only**.

Chapter starts (from the creator's own description): 0, 89, 172, 314, 415, 483, 571, 666, 787.

---

## 1. Colour (measured)

| role | value | note |
|---|---|---|
| background | **`#fdfdfd`** | near-WHITE, not cream. 52/64 corner samples. |
| ink / outline | **`#000000`** | pure black, dominant dark colour by 16× |
| chapter accent | varies | e.g. `#523f2a` brown, `#536c33` olive, `#8f7d72` taupe |

**This is a high-contrast white-and-black cartoon.** Our current build is dark-space
with cream cards; that is the wrong register entirely and is the biggest single
difference. Our ink is not pure black and our paper is not white.

---

## 2. Typography (measured)

- **Title:** persistent for the whole chapter, top-centred.
  - cap height **46 px**, top of glyphs at **y≈21**, baseline **y≈67**
  - horizontally centred (e.g. 522–753 → centre 637 ≈ 640)
  - **ALL CAPS**, pure black, no outline, no shadow
- **Font is Comic Neue Bold** (SIL OFL, vendored at `work/fonts/ComicNeue-Bold.ttf`).
  It was selected by rendering the reference word "MEZHGORYE" at the measured
  46 px cap height in seven candidate faces and comparing glyph skeletons
  (`work/ref2/_font_compare.png`): same uniform monoline stroke, rounded
  terminals, same 'R' splay, 'G' crossbar and 'M' outer legs. **No Windows system
  font matches** — Segoe Print and Ink Free are handwriting (too cursive), Comic
  Sans is humanist (too even), Balsamiq Sans is too geometric.
- The title is drawn with a **per-letter wobble** (±2.6° rotation, ±2.2 px baseline
  offset, seeded so it is identical every re-render). That irregularity is what
  separates a real marker face from a system font pretending to be one. See
  `work/lib/v2draw.py:draw_title`.
- Other in-frame text uses the same family, smaller, in three roles — a yellow
  highlighter label, a red warning/emphasis label, and a blue quantity label.
- **COLOURED LABELS CARRY A BLACK KEYLINE.** Confirmed by reading the frames:
  the red "East" is red text inside a black outline. An earlier pass of this file
  claimed labels were flat fills with no outline — that was wrong, and it shipped
  into `v2draw.draw_label` before a frame read caught it. `draw_label` now adds a
  black `stroke_width` outline automatically for any non-INK label colour.
- The main **directional arrow is BLACK, thick, with a solid triangular head**
  (its "East →" arrow), not a thin red curve. The head's BASE sits on the shaft
  end (half-width >= shaft width) with the apex forward — not a small forward
  nub. Red is reserved for the marker-pen annotations (boxes, X, circling). See
  `work/lib/v2draw.py:draw_arrow` and the geometry note there.
- A **star's rays are tapered triangles** anchored into the disc rim, not
  hairline strokes and not lines floating off the rim. A constant-width ray
  reads as a stray pen mark next to a 6px keyline disc. See
  `work/lib/v2subjects.py:star`.
- **Flat vector, heavy keyline.** Buildings, soldiers, characters and props are
  all flat fills inside a thick (6–8 px) black outline. There is no gradient and
  no soft shading anywhere.

---

## 3. Layout

- One persistent title band at the top; the illustration occupies the rest.
- No caption band. Text on screen is sparse and short — a label, a number, or a
  speech bubble, never a sentence of narration.
- Generous white space. The frame is mostly empty around 1–3 elements.

---

## 4. Animation language (measured, this is the important one)

Frame-difference analysis over the whole file (`work/ref2/framediff.npy`):

- **The video is 88 % completely static.** Median inter-frame difference is
  **0.000** at 160×90. Total time with ANY motion is **103.5 s of 875 s (12 %)**.
- **Zero hard cuts.** `ffmpeg select='gt(scene,0.25|0.08|0.05)'` returns **0 frames**
  at every threshold. There are no snap cuts and no cross-fades in the modern sense —
  scenes are held and elements change within them.
- **1035 discrete pop events**, median gap **3.6 s** between them.

What an event looks like (verified frame-by-frame at 11.0–12.5 s and 121.0–122.3 s):
- An element **appears fully formed in a single frame** (0.1 s). No fade, no scale-up,
  no tween. Verified: a cougar is absent at 121.60 s and fully drawn at 121.72 s.
- Occasionally a **quick slide/rotate** over ~0.2 s: at 11.6 s an Australian flag
  pops in at the right edge, then translates left ~200 px and rotates slightly by
  11.8 s, then holds for seconds.
- Then a **long static hold**.

**Rule: elements pop in one at a time, in sequence, on a static background, and
hold.** The scene assembles itself as the narrator talks. Nothing loops, nothing
bobs, nothing idles.

---

## 5. Character

- A single line-figure: **round head, two dot eyes, a single-line mouth, thin black
  limbs, no fill, no nose, no hair.** Torso carries one small coloured mark.
- Frequently shown **very large** (head fills 40–50 % of frame height) with the
  mouth changing shape per expression.
- **Speech bubbles** with short text are a recurring device
  (e.g. "Nobody believes it" in red, "700,000 workers").
- NOT to be cloned. We keep our own character (`work/lib/stickman.py`) and adopt
  the *scale* and *speech-bubble* devices only.

---

## 6. Density

- On-screen text is a **label, a number, or a short bubble** — never a narration line.
- Photographs/imagery appear as insets, but the majority of frames are flat vector art.
- ~1–3 elements per frame. This is the "less clutter" the user asked for, quantified.

---

## 7. Pacing (measured, and in conflict with the brief)

| metric | reference | our target |
|---|---|---|
| words | 2998 | 2400 (across 12 segments) |
| overall wpm | **205.7** | **160** |
| per-chapter wpm | 193–220 | ~160 |
| median sentence | **17.5 words** | ≤10 words |
| sentences <10 words | 18% | majority |
| inter-word gap >0.3 s | 2.0% | 6–10% (deliberate breaths) |
| chapter length | 68–142 s (median 89) | ~75 s × 12 = ~15 min |
| fps | 60 | 60 |

**The reference is FASTER and DENSER than the brief.** The user asked for ~160 wpm
and for sentences a low-skill viewer can follow; the reference runs 205 wpm with
17.5-word sentences. We follow the **user's 160 wpm**, not the reference's 205.
The reference governs *look and motion*, the brief governs *pace and clarity*.

**Word budget.** We target ~15 min (the bar's length) at our slower 160 wpm, which
is ~2400 words total / ~200 per segment — a ~30% cut from the 2842-word v1
scripts. The cut is the "less clutter, simpler" the brief asks for. Because we go
slower, our 75-second segments feel less dense than the bar's 90-second chapters,
which is the intended effect.

**Reaching 160 wpm (the blocking engineering problem).** chatterbox has **no rate
or speed parameter** — `model.generate()` takes only `exaggeration`,
`cfg_weight`, `temperature`. Measured raw chatterbox output runs **209–228 wpm**
(215 wpm on koi55). The v1 pipeline only reached its 200 wpm target by padding
inter-beat silence clamped to `[0.12, 0.60] s`, which bottoms out near 191 wpm;
160 wpm is *unreachable* by padding alone (it would need ~2.0 s gaps, 3.3× over
the clamp).

**The fix** (`work/segments/_v2_audio.py`): a tempo stage with a **closed-form
pacing solve**. The breath is chosen first, then the speech budget is derived from
it, then the audio is stretched to fit:

```
gap            = 0.30 s                       # creative choice, made first
required_speech = (words / 160 * 60) - gap*n_gaps
atempo factor  = raw_total_s / required_speech   # <1 slows; pitch preserved
```

No iteration needed — the arithmetic is self-consistent to a sample. Verified on
koi55: 249 words, raw **214.8 wpm** → speech **166.3 wpm** → overall **160.4 wpm**,
12 beats all at factor 0.772, fundamental frequency unchanged (120.6 → 121.2 Hz),
3.5 % of runtime in deliberate breaths.

**Watch the sign.** `atempo=f` gives `output = input / f`, so **f < 1 slows**. The
first implementation inverted this and shipped a 261.8 wpm render that looked
plausible in the log. If a segment ever comes out ~2× the target length, the factor
is inverted, not the solve.

The *voice itself* is unhurried rather than the timeline padded with air, which is
what "slow down to 160 wpm" actually means. Word onsets for visual sync come from
whisper run on the FINAL slowed `v2_audio.wav`, so the visuals are timed to the
audio that actually plays.

---

## 8. Images we may not copy

The reference contains copyrighted photographs (satellite imagery, a dollar bill, a
portrait of Henry VIII, site photos). Per `CLAUDE.md` §1 we reproduce **none** of
them. Where the reference uses a photo inset we substitute an original flat-vector
drawing of the same subject.

---

## 9. v2 architecture (what the modules do)

The v1 two-register model (dark space + cream cards, `motion.py` stamp verbs,
`palette.py`) is **retired**. The v2 pipeline is a single white-page register with
a layer/pop compositor.

| module | status | role |
|---|---|---|
| `lib/v2type.py` | **new** | Comic Neue Bold, measured title geometry (46 px cap, top y=21, centred 640), page/ink/marker colours, label sizes. |
| `lib/v2draw.py` | **new** | The draw primitives: persistent title (with per-letter wobble), labels, big numbers, speech bubbles, red arrows/boxes/X, confusion circles. |
| `lib/v2engine.py` | **new** | The layer/pop compositor. A card is a list of `Layer`s; each pops fully-formed in one frame at its `t0` and holds. `SlideIn` is the rare ~0.2 s slide/rotate. No fades, no tweens, no idling. |
| `segments/_v2_audio.py` | **new** | Per-beat TTS + atempo tempo stage to reach 160 wpm. Writes `v2_audio.wav` + `v2_beats.json` (exact beat boundaries). |
| `lib/ink.py` | reuse as-is | 6 px strokes, low-frequency deterministic wobble, the flat-vector linework. Do not "modernize". |
| `lib/labels.py` | reuse as-is | style-neutral label placement / auto-contrast. |
| `lib/align.py` + `segments/_batch_align.py` | reuse as-is | whisper word onsets (run on the slowed `v2_audio.wav`). |
| `lib/stickman.py` | reuse (light theme) | our own character; the `light` theme already reads on white. Scale to ~40–50% frame height. |
| `lib/cardframe.py::hero_word` | preserve verbatim | stroke-aware clamp (the shipped-clipping fix). |
| `lib/motion.py`, `lib/palette.py`, `lib/emissive.py`, `lib/texture.py`, `lib/integrated_label.py` | **retired** | two-register / gradient machinery the v2 bar does not use. |

**Load-bearing invariants that must survive the rebuild** (from the reuse audit):
- `LINE_EQ`: `'\n'.join(beat.line).strip() == narration.strip()`, enforced in the
  TTS layer. The card and aligner layers depend on it.
- The `_WORD_RE` tokenizer in `_batch_audio.py` and `_batch_align.py` must stay
  byte-identical, or beat boundaries stop lining up with word onsets.
- The concat must run `_assemble.normalize_audio()` and every bridge must carry an
  `anullsrc` 44100/stereo stream; never `-c copy` audio (the 26-min-bug).

---

## 10. Where the visuals are timed

The card schedule is derived from whisper word onsets on the FINAL slowed audio
(`v2_alignment.json`), not predicted from word counts. Within a beat, elements pop
in on clause boundaries found in the per-word onsets. Snap (hard) appearance, no
cross-fade. The persistent chapter title lands on the spoken chapter name.
