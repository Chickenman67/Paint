# Segment 10 — Fomalhaut b (Dagon): palette + visual identity spec

Status: **built.** All 14 beats render; self-test exits 0. `work/segments/fomalhautb/_cards.py` is the single source of truth in code (`MY_PAL` at the top); this document is the same palette stated for humans, and it wins on any disagreement.

Authority: `CLAUDE.md` §4 (style), §6 (the character), §7 (card anatomy), §8 (build loop), §10.6 (gradient limits), §10.8 (character at the fate beat), and — above all — `work/STYLE_CANON.md`, which overrides several of those numbers. No reference frames were fetched or used (builder firewall, §8); nothing was pip-installed and no paid API was touched.

Subject: Fomalhaut b, the first planet ever imaged in visible light around a non-Sun star — a dot of light inside a wide dust-and-ice belt, which may be a planet shepherding the belt, a dust cloud kicked up by something passing through, or a world that swung too close to the star and fell out of the system entirely. Tone: cold, distant, unresolved. Not horror, not awe — **doubt that never resolves.** No neon.

---

## 1. The palette (6 colors, locked)

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Slate-black | `#12141E` | (18, 20, 30) | All linework (6px large / 4px detail / 2px fine / 1px hairline); every piece of type on a cream card; the header glyph fill |
| paper | Bone-cream | `#F3ECDB` | (243, 236, 219) | Title strip; the field of every "cream" (paint-register) card |
| deep | Void | `#04060E` | (4, 6, 14) | The space field behind every "void" card; the void-card ground band |
| accent 1 | Signal amber | `#F0B04A` | (240, 176, 74) | The star; captions on deep; the pick-out ring; arrows; the underlining on the closing card |
| accent 2 | X-ray bone | `#DEE8EE` | (222, 232, 238) | **Void cards only** — ice chunks, the ring arc, labels on deep, the falling dot |
| accent 3 | Cold teal | `#407A8A` | (64, 122, 138) | The dashed intruder path; the belt's *derived* tints on cream (see below); never a word |

### Two derived tints — not new hues

`teal` at full strength is 3.32:1 on cream and reads as a saturated CAD blob, so the cream cards never use it raw. Both tints are arithmetic blends of two locked colors and are computed in code by `_tint()`:

| Tint | Derivation | Hex | Role |
|---|---|---|---|
| **MID** | `teal` 55% / `paper` 45% | `#90ADAE` | Drawn linework and chunk bodies on cream: the belt on `the_ring` and `maybe_world`, the ghost dot and its rule on `one_bad_pass` |
| **PALE** | `teal` 22% / `paper` 78% | `#CBD2C9` | Fields only, never a line: the soft wash behind a diagram, and the cream-card ground band |

Rule of thumb: **MID carries a line, PALE carries a field, teal carries neither on cream.** On void, teal is used raw — it has 4.21:1 against the field and reads clearly.

**Seventh color, deliberately not in the palette:** the stickman's shirt red `#C83232` (`work/lib/stickman.py`, `SHIRT`). It is a global of the character, identical across all 12 segments, and is what makes him findable. Because it is fixed, **no card accent in this segment may be red** — his shirt is the only red on screen, so he never dissolves into the background. The "danger" color for cards is amber.

### Why not neon

Highest chroma in the set is amber `#F0B04A` (H≈37°, S≈85%, L≈62%). Teal is held down to S≈37%, bone to S≈32%. There is no pure green, no magenta, no `#00FFFF`-class value anywhere; the only near-white is `#FFFCF0` at the very centre of the star's core. The subject is a *faint* dot seen across 25 light-years — the palette's restraint is the point, and a neon card would assert a certainty the narration explicitly refuses.

### Measured contrast (WCAG ratios, computed from the values above)

| Pair | Ratio | Verdict |
|---|---|---|
| Bone-cream on Void | 17.19:1 | text OK |
| X-ray bone on Void | 16.27:1 | text OK |
| Slate-black on Bone-cream | 15.58:1 | text OK |
| Signal amber on Void | 10.62:1 | text OK |
| Cold teal on Void | 4.21:1 | large shapes and 4px dashes; never caption text |
| MID on Bone-cream | 2.03:1 | **fills, chunks and 4px rules only — never type** |
| PALE on Bone-cream | 1.31:1 | **fields only — a ground band, never a line, never a word** |
| **Signal amber on Bone-cream** | **1.62:1** | **forbidden — amber type never sits on cream** |
| **X-ray bone on Bone-cream** | **1.06:1** | **forbidden — bone never appears on a cream card at all** |

Binding rules that fall out of that table:

- On a **void** card: captions are amber (the default), annotations and labels are bone, the path/arc linework may be teal.
- On a **cream** card: **every piece of text is slate-black.** Amber and bone are fills only; MID and PALE carry the diagram.
- **The single most expensive mistake available in this segment is drawing bone on cream.** The first build did exactly that — the ice chunks on `the_ring` and `maybe_world` were `#DEE8EE` at 1.06:1 and were literally invisible, so the belt read as an empty card. `_chunks()` therefore takes its colour as a required argument, and every cream call site passes `MID`; every void call site passes `BONE`.
- Header glyphs are **slate-black on the cream strip**, not the card's accent, for the same reason §7's "header fill = segment accent" only works if the accent is legible on cream — and two of the three accents are not.

---

## 2. Card register and accent assignment — 14 beats, mechanically assigned

The assignment is not a per-card aesthetic choice; it alternates on the beat boundary and is stated here so it cannot drift when a card is re-timed. **Register comes from `script.json` and is binding** — the narration alternates space and paint, and the visual register follows it exactly.

| # | Beat id | Register | Key accent | Character |
|---|---|---|---|---|
| 1 | `hook_brightest_star` | void | amber (the star) + bone type | yes — standing, flat |
| 2 | `the_ring` | cream | MID (the belt) + amber (the star) | yes — shrugged, flat |
| 3 | `light_in_the_ring` | void | bone (arc, blob) + amber (pick-out) | yes — pointing, awed |
| 4 | `first_visible_planet` | cream | ink (hero word) + amber (rule) | yes — hands up, oval |
| 5 | `the_headline` | void | bone (blob) + amber (pick-out) | yes — standing, flat |
| 6 | `not_the_end` | cream | grey smudge + ink (brackets, dot) | yes — shrugged, zigzag |
| 7 | `maybe_dust` | void | teal (path) + bone (dust) | yes — standing, flat |
| 8 | `maybe_world` | cream | amber (the world, arrows) + MID (belt) | yes — thinker, flat |
| 9 | `two_things_same_pixels` | void | bone (frame A) + amber (frame B) | yes — hands up, oval |
| 10 | `the_orbit` | cream | ink (the loop) + amber (close pass) | yes — shrugged, flat |
| 11 | `orbit_not_tidy` | void | bone, rising alpha | **no — diagram-only beat** |
| 12 | `one_bad_pass` | cream | ink (loop) + amber (the one dot) | yes — shrugged, flat |
| 13 | `the_long_fall` | void | amber (the system) + bone (the fall) | yes — pointing, oval |
| 14 | `cloud_world_or_gone` | cream | ink / amber / ink (the three words) | yes — hands up, flat |

Adjacency audit on the register, in order: void, cream, void, cream, void, cream, void, cream, void, cream, void, cream, void, cream. **Thirteen boundaries, zero repeats** — the alternation is perfect by construction, so no two neighbouring cards can ever share a background.

Accent adjacency within a register: consecutive void cards never lead with the same accent, and the one place where two cards share a dominant (10 and 12, both the ink loop on cream) is deliberate — they are the *same orbit*, and continuity of the drawing is the point.

### The character appears in 13 of 14 beats

CLAUDE.md §6 requires the character in at least one beat per segment; this segment puts him in thirteen. The single exception is `orbit_not_tidy` (beat 11), whose own art brief in `script.json` describes only the ellipse fraying — it reads as the segment's one pure-diagram card, and putting a figure on it would break the beat's "the LINE is the subject" logic. His absence there is a choice, not an oversight.

The emotional arc is legible from his face alone, which is the §6 test: flat (1) → flat (2) → awed (3) → awed (4) → flat, deadpan (5) → *zigzag, asking* (6) → flat, watching (7) → considering (8) → oval, stunned (9) → flat (10) → — → flat (12) → awed, small (13) → flat (14). The zigzag at beat 6 is the pivot: it is the only beat where he is visibly *unsure*, and it sits exactly where the narration admits the signal might be a cloud.

**`the_long_fall` (13) is the fate beat** and CLAUDE.md §10.8 requires the character at the most emotionally loaded second. He is there, small, at frame left, mouth a small awed oval, watching the dot leave. Not omitted.

### Two cards where the drawing must tell the truth

- **Beat 2** carries the label "THE BELT RUNS OFF FRAME". The ring is therefore drawn at `RING_CX=430, RING_RX=900`, so its geometry spans −470…1330 and genuinely leaves both edges. The first build had `rx=880` with the star parked near the ellipse's *left vertex*, which produced two sparse horizontal bands and a star that was not encircled at all — the label was describing a drawing that did not exist. The star now sits at the ring's **centre** and the ring is what runs off frame.
- **Beat 10** is "runs off the far edge of the card". The orbit is a genuine eccentric ellipse with the star at its left focus (a=620, e=0.75), so its far vertex lands at x=1385 — past the right edge. The "CLOSE PASS" tick in the first build was computed at x=−344, i.e. entirely off-frame, so the one labelled feature of the beat was simply missing from the render.

A label on a diagram is a claim about the drawing. If the geometry does not support it, the label is the thing that is wrong.

---

## 3. Emissive treatment — the star, and only the star

The star is the one genuinely emissive subject in this segment, so it is the one place a gradient is legal. Everything else is flat.

**Void register (beats 1, 3, 11, 13).** `C._radial_core` with `glow=0`, three stops: r=0.00 → `#FFFCF0`, r=0.55 → amber `#F0B04A`, r=1.00 → `#B06A28`. Then a deterministic stipple at `density=0.005` so the core keeps spray-paint grain instead of reading as a clean CG ramp.

**The halo is built locally, not with `C.add_glow`.** `add_glow` terminates its mask with a *hard circular cutoff*; on a near-black sky any nonzero halo is visible, and it was drawing a grey disc of radius r·2.1 with a definite edge around the star — the most conspicuous artefact on the first build's hook card. `_halo()` instead writes its rim ring at value 0, so the falloff is a smooth power ramp `(1−t)^2.3` to nothing, with no boundary to see. A halo that has an edge is not a halo.

**Light spikes (void only).** Four spikes on their own RGBA layer, composited once, `GaussianBlur(r·0.20)`. Built as flat polygons they read as a hard-edged grey crosshair laid over the frame; blurring the layer is what turns them into light.

**Cream register (beats 2, 4, 8, 10, 12) — no gradient, no glow, no spikes.** A flat amber disc, a `K.OUTLINE` ink outline, and ONE flat darker crescent for form. A painted sun is a shape with a rim; a gradient sun is a lens flare. The spikes are a Register S signature and simply do not exist on paper.

**The blob — the object the whole segment is about — is never emissive.** `_blob()` is four overlapping flat bone discs at rising alpha (62/100/150/210), so it reads as a genuinely faint smudge. It is drawn the same way on every card that shows it: in the pick-out ring on beats 3 and 5, inside both identical data frames on beat 9, and as the grey smudge on beat 6. Its faintness is the plot.

**Never gradient (explicit denylist).** The belt and its chunks, on every card. The orbit ellipses. The starfield and the void ground band. The title strip and the caption. The character, all of him, every pose and expression. The cream wash and the cream ground band. The smudge on beat 6 and the dust bulge on beat 7 — both are blurred *flat fills*, not ramps. §10.6 exists because KELT-9b's portrait got a radial gradient and read as a soft-fantasy halo instead of paint.

---

## 4. Type — the locked `type.py` scale, with one documented addition

Family is **Comic Sans Bold / Comic Sans Regular only** (`comicbd.ttf` / `comic.ttf`, resolved by `T.load_font_at`). Consolas is retired (`STYLE_CANON` §1); `psrb1257/PALETTE_SPEC.md` §4 still lists it and is obsolete for this segment. The sizes below are `work/lib/type.py` verbatim, not the points in CLAUDE.md §7.

| Role | Size | Face | Stroke | Color on this segment |
|---|---|---|---|---|
| Header — hand-lettered "FOMALHAUT b" | `HEADER_PX` 48 | Comic Sans Bold | 3px ink | slate-black on the cream strip |
| Label | `LABEL_PX` 32 | Comic Sans Regular | 1px | bone on deep; slate-black on cream |
| Caption | `CAPTION_PX` 28 | Comic Sans Bold | 3px ink keyline | amber on deep; slate-black on cream |
| Stamp | `STAMP_PX` 15 | Comic Sans Regular | 1px | bone on deep; slate-black on cream |
| **Subject label** | **`SUB` 20** | Comic Sans Regular | none | bone on deep; slate-black on cream |

**`SUB = 20` is the one documented addition** to the type scale, and it is used for exactly one job: the small label that sits **on or immediately beside the thing it names** — "SOMETHING IN HERE", "NOT OUR SUN", "ONE BAD PASS", "A CLOUD" / "A WORLD", "DUST". It is a single constant used at every call site, still resolved through `T.load_font_at` so the family stays locked, and it is not a second diagram size: diagram labels proper are `STAMP_PX`.

Hero words (a dominant on-card phrase) go through **`C.hero_word` and nothing else.** Hand-rolled clamping measures the advance width and ignores the 3px keyline that `draw_outlined_text` draws *outside* the glyphs, which is how a hero phrase once shipped with its final letter cut off. `hero_word` measures the same call the renderer makes, clamps including the stroke, auto-shrinks, and keeps the word below the title strip.

A hero word must also **not restate the caption.** On beat 1 the caption is "THE BRIGHTEST STAR IN THE SKY" and the hero is "BRIGHTEST-1 / IN THE AUTUMN SKY" — the superlative in type, the sentence in the caption, each carrying something the other does not.

The closing card (14) is the one deliberate exception to `hero_word`: three words stacked down the left, centred in a hero and therefore not the right tool for a stack, so `_left_word()` places them left-anchored with the same clamping discipline. Still one size, still one family.

Captions stay **≤60 characters, ≤12 words, one line.** The narration is **never** printed as a caption — audio carries it.

---

## 5. Files

- `work/segments/fomalhautb/_cards.py` — this segment's renderers. Module-level `RENDERERS` keyed by all 14 beat ids; `register()` merges into `work/lib/cardframe.py`'s dispatch. `MY_PAL` at the top is the code-side source of truth. Run it directly for the self-test.
- `work/segments/fomalhautb/script.json` — the narration and the per-beat art briefs (binding).
- `work/segments/fomalhautb/cardsheet/beat_01.png … beat_14.png` — the self-test output, one frame per beat at 1280×720.
- `work/lib/cardframe.py` — **not edited.** Layout-A tail (`_header` / `_draw_stickman` / `_caption`) and the gradient/glow helpers are used as shipped.

### Known lib limitation, carried not worked around

`lib/ink._smooth_open` is broken — its Catmull-Rom pad is two elements short and raises `IndexError` for any polyline of three or more points, so `draw_outline(closed=False)` and `draw_smooth(closed=False)` are unusable. `_catmull_open()` in this module re-implements the open path from the same `K.wobble_points` engine (pad `[p[0]] + p + [p[-1]]`, iterate `range(len(p)-1)`), which is the workaround `_cards_b4.py` established. Every open curve in this segment goes through it. The closed path is unaffected and used as shipped.
