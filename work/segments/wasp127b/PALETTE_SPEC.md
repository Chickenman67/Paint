# Segment 6 — WASP-127b: palette + visual identity spec

Status: **implemented.** `_cards.py` renders all 14 beats; the self-test exits 0.
Authority: `work/STYLE_CANON.md` (canonical — it overrides CLAUDE.md §4/§7 wherever they disagree), CLAUDE.md §6 (the character), §10.6 (gradient limits).
Subject: a hot Jupiter in the tail of its own atmosphere — puffy and almost empty, the fastest winds ever measured on an exoplanet, shedding its air upward and never getting it back. Tone target: thin, cold, leaking. No neon.

---

## 1. The palette (6 colors, locked)

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Slate-black | `#14161C` | (20, 22, 28) | All linework (6px large / 4px detail / 2px fine / 1px hairline), header glyph fill, every word on a cream card, planet keylines |
| paper | Bone-cream | `#F2EAD6` | (242, 234, 214) | Title strip (rows 0..83), every cream-register card field, the olive band's lit face |
| deep | Void | `#05060B` | (5, 6, 11) | The space field, every void-register card, the starfield |
| accent 1 | Signal amber | `#E8A33D` | (232, 163, 61) | The star and its flares, the single "fastest measured" bar, captions and hero words on deep, hot stamps |
| accent 2 | X-ray bone | `#DCE6EC` | (220, 230, 236) | Wind ribbons and diagram linework on deep, the emissive core's mid-stop, hero words on deep, planet band highlights |
| accent 3 | Storm teal | `#2E7F86` | (46, 127, 134) | The wind and the escaping air — every ribbon, wash, bar and droplet that is *atmosphere in motion*. Semantic: teal is air leaving |

**Seventh color, deliberately outside the palette:** the stickman's shirt red `#C83232` (`work/lib/stickman.py`, `SHIRT = (200, 50, 50)`). It is a global of the character, identical across all 12 segments, and it is what makes him findable. Because it is fixed, **no card accent in this segment may be red** — his shirt is the only red on screen.

> **Documented override — beat 9.** `script.json` beat 9 asks for "three slices crossed out in **red**." That is drawn in **x-ray bone over slate-black slices** instead. Reason: red is reserved for the character (§1), and a red X on the spectrum bar would read as the character bleeding into a beat that is explicitly "no character." The cross-out still reads instantly because it is a high-value stroke over the lowest-value swatch. The beat's meaning is unchanged.

### Two colours outside the 6

- **Olive ground band** `#607046` (96, 112, 70) — a *stage* colour, not a card accent. STYLE_CANON's 2026-09-30 addendum asks for a wavy olive/dark-green ground plane wherever the character is the **subject** rather than a scale figure. That is exactly beats 6 (`nothing_inside`) and 12 (`throwing_its_away`). It sits mid-value so it reads as a painted surface against the bone-cream sky, not as a dark stripe. It never leaves the ground band and never becomes a card background.
- **Spectrum swatches** (7 flat values, below) — diagram-only, never a card field, never type. The spectrum bar is the one subject in the segment that is *supposed* to read as a ramp, so it carries discrete flat swatches instead of a gradient:

  `#EEB04A` · `#F6D080` · `#DCE6EC` · `#96C8C8` · `#2E7F86` · `#284E64` · `#1C2C3E`

  Derived from the locked set (amber → bone → teal → deep) so the bar still reads as this segment's art. A "bitten" or crossed-out slice is knocked **down toward slate-black**, never painted red.

### Why not neon

Highest chroma in the set is amber `#E8A33D` (H≈34°, S≈75%, L≈57%). Teal `#2E7F86` sits at S≈48%. There is no cyan, no pure green, no `#00FFFF`-class value anywhere, and the only pure white is `#FFFFFF` at the very centre of the beat-7 star core. Saturation lives in amber and teal only, and those two never touch the same card as the dominant — amber is *heat*, teal is *air*, and the segment needs them to stay separable.

### Measured contrast (WCAG ratios)

| Pair | Ratio | Verdict |
|---|---|---|
| X-ray bone on Void | 15.9:1 | text OK |
| Bone-cream on Void | 16.9:1 | text OK |
| Signal amber on Void | 9.4:1 | text OK |
| Storm teal on Void | 4.4:1 | large display type and fills only |
| Slate-black on Bone-cream | 15.1:1 | text OK |
| Signal amber on Bone-cream | 1.8:1 | **forbidden — amber type never sits on cream** |
| X-ray bone on Bone-cream | 1.1:1 | **forbidden — bone type never sits on cream** |
| Storm teal on Bone-cream | 3.4:1 | fills and large shapes only, never body type on cream |

Binding rules that fall out of that table:

- On a **void** card: the hero word and caption are **bone** (default) or **amber** (heat beats: 5, 11). Teal carries the subject, never the sentence — beat 9's `THE GAPS NAME IT` is the one deliberate exception, at 58px display size where 4.4:1 is acceptable, and teal is the only thing on that card that could be the word.
- On a **cream** card: **every** word is slate-black. Amber and bone are fills only. No exceptions in this segment.
- Header glyphs are **slate-black** on the cream strip, never the card accent — two of the three accents are illegible on cream (1.8:1, 1.1:1), so ink is the header's colour. This matches `C._header`.

---

## 2. Character ink colour, by register

The single most load-bearing rule in this segment, because half the beats are set in space.

| Register | Cards | Backdrop | Character theme | Result |
|---|---|---|---|---|
| `'dark'` (void / space) | 1, 3, 5, 7, 9, 11, 13 | `#05060B` starfield | `theme='dark'` | **Cream** limbs and head with a dark keyline. Dark-on-dark is wrong here — a hardcoded black character vanishes into every space card. |
| `'light'` (cream / paint) | 2, 4, 6, 8, 10, 12, 14 | `#F2EAD6` paper | `theme='light'` | **Dark ink** limbs and head with a cream keyline, flat fills, and — on 6 and 12 — grounded on the wavy olive band. |

The character appears on **6 of 14 beats** (1, 3, 6, 8, 12, 13) — above the CLAUDE.md §6 floor of four. The script marks beats 2, 4, 5, 7, 9, 10, 11, 14 as pure data beats and **no stickman is drawn on them**.

---

## 3. Card accent assignment — 14 cards

Accent = the colour that leads the card (the subject, or the hero word when the subject is neutral).

| # | Beat id | Register | Accent | Hero word |
|---|---|---|---|---|
| 1 | `hurricane_forget_it` | void | bone `#DCE6EC` | FORGET IT (bone) |
| 2 | `name_the_planet` | cream | amber `#E8A33D` | TOO CLOSE (ink) |
| 3 | `fastest_winds` | void | teal `#2E7F86` | NO BRAKES (bone) |
| 4 | `never_land` | cream | bone `#DCE6EC` | NEVER LANDS (ink) |
| 5 | `almost_empty` | void | amber `#E8A33D` | A GIANT MADE OF AIR (amber) |
| 6 | `nothing_inside` | cream | teal `#2E7F86` | NOTHING TO STAND ON (ink) |
| 7 | `read_the_star` | void | bone `#DCE6EC` | READ THE STAR (bone) |
| 8 | `swallowed_colors` | cream | bone `#DCE6EC` | THE COLOURS THAT VANISHED (ink) |
| 9 | `missing_tells_you` | void | teal `#2E7F86` | THE GAPS NAME IT (teal) |
| 10 | `water_leaving` | cream | teal `#2E7F86` | UPWARD (ink) |
| 11 | `grains_high_above` | void | amber `#E8A33D` | SMALL GRAINS (amber) |
| 12 | `throwing_its_away` | cream | teal `#2E7F86` | THROWING IT AWAY (ink) |
| 13 | `leak_no_bottom` | void | bone `#DCE6EC` | NO BOTTOM (bone) |
| 14 | `too_far_to_help` | cream | bone `#DCE6EC` | TOO FAR TO HELP (ink) |

**Adjacency audit — honest result.** The intended cycle is a strict 3-cycle `bone → amber → teal`. The rendered cards follow it through beat 7 and then hold the accent where the *semantics* demanded it, producing **three adjacent repeats** out of thirteen boundaries:

- **7 → 8** (bone, bone) — also a register flip, void → cream
- **9 → 10** (teal, teal) — also a register flip, void → cream
- **13 → 14** (bone, bone) — also a register flip, void → cream

Every one of the three is mitigated by a **register flip**, which is a far stronger visual break than an accent change: a bone-on-void diagram card does not read as continuous with a bone-on-cream diagram card. Recoloring them to satisfy the letter of the rule would have cost more than it bought — beat 10's dotted escape path and beat 9's droplet are both **atmosphere**, and teal is this segment's semantic colour for atmosphere in motion (§1). Making them a different hue to satisfy an adjacency rule would break the one colour association the segment actually builds. **The repeats are deliberate and load-bearing; do not "fix" them by recolouring the air.**

**Palette bleed across the segment boundary:** the bridge is `work/lib/transition.py`'s `make_white_card()` — pure `#FFFFFF`. That is shared assembly code used by all 12 segments; **do not retint it** for this segment or every other segment inherits the change. The void palette therefore starts after a white card, which is a stronger reset than the CLAUDE.md §5.7 black bridge it supersedes.

---

## 4. Emissive treatment and the gradient denylist

**The one legal gradient** is the beat-7 star core, drawn with `C._radial_core` at three stops — `#FFFFFF` → bone `#DCE6EC` → violet `(110, 90, 156)` — plus `add_glow` on a hard circular cutoff. This is the segment's only emissive body.

**Never gradient — explicit denylist:**

- Every planet, on every beat, including beat 11's close-up limb. They are matte gas giants under a hard light: flat banded fills plus a 6px slate keyline. A radial gradient on a planet here reads as a soft-fantasy halo, which is the exact failure CLAUDE.md §10.6 records against KELT-9b.
- The spectrum bar (7 flat swatches, §1) and every bite or cross-out on it.
- The wind ribbons and the escape streaks — these are **blurred flat washes** (`_soft_wash`), which are soft-edged but flat in value. They are not gradients and carry no ramp.
- The olive ground band, the cream sky washes, the starfield, the title strip, the caption, and the character in every pose and expression.
- Any card-level vignette.

`lib/texture.py`'s `planet_disc()` is **off-canon for this segment** — it applies a hard width-4 black outline, and the canon keyline is `K.OUTLINE` = 6px in slate-black. Use `_banded_giant` instead.

---

## 5. Type — the locked `lib/type.py` scale

Consolas is **retired**. One family: `comicbd.ttf` (Comic Sans Bold) for headers and hero words, `comic.ttf` (Comic Sans) for small labels and stamps. No new sizes are permitted.

| Role | Constant | Size | Face | Stroke | Colour on this segment |
|---|---|---|---|---|---|
| Header — "WASP-127b" | `T.HEADER_PX` | 48px | comicbd | 3px | slate-black on the cream strip |
| Hero word — the card's one dominant phrase | via `C.hero_word` | 46–64px | comicbd | 3px keyline on void, 0 on cream | bone / amber / teal on void; slate-black on cream |
| Label — subject labels on the art | `T.LABEL_PX` | 32px | comic | 3px | bone on void; slate-black on cream |
| Caption | `T.CAPTION_PX` | 28px | comicbd | 3px | bone on void; slate-black on cream |
| Stamp — `TOO HIGH`, `HEAT`, `FASTEST MEASURED` | `T.STAMP_PX` | 15px | comic | 1px | bone on void; slate-black on cream |

Every dominant phrase goes through `C.hero_word`, never a hand-rolled draw. `hero_word` clamps against the measured glyph bounds **including** the 3px stroke; clamping against `T._bbox`'s advance width does not, and clips the last glyph — a trap this segment's long phrases (`THE COLOURS THAT VANISHED`, `NOTHING TO STAND ON`) would both have hit.

**The narration line is never printed.** Captions on every card are short floating labels; the spoken text is audio only.

---

## 6. Stroke scale

`K.OUTLINE` 6px on large shapes (planets, ground band, arrow shafts) · `K.DETAIL` 4px on detail (arrow barbs, bar keylines) · `K.FINE` 2px on fine linework and small annotations · `K.HAIRLINE` 1px only where a 1px line cannot be seen against its ground.

---

## 7. Files

- `work/segments/wasp127b/_cards.py` — the module. `RENDERERS` keyed by beat id; every `fn(card, planet) -> 1280x720 RGB`. `MY_PAL` is local to this module; `lib/cardframe.py`'s `PAL` is segment 3's and is used only for genuinely generic helpers.
- `work/segments/wasp127b/script.json` — the 14 beats and their binding `visual` briefs.
- `work/segments/wasp127b/cardsheet/beat_01.png` … `beat_14.png` — the self-test output.

Run the self-test with:

```
cd C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments && python wasp127b/_cards.py
```

It prints one line per beat and exits 0.

---

## 8. Known deviations from a literal reading of the briefs

1. **Beat 9's red cross-outs** are bone, not red — §1.
2. **Beat 4's wind arrows are ruler-straight.** Canon asks for low-frequency wobble on linework; these five are deliberately straight because the beat's argument is that they never deviate and never land, and a data-diagram beat reads better as measured than as hand-drawn.
3. **The olive ground band** appears on beats 6 and 12 only, per the STYLE_CANON addendum's "character is the subject, not a scale figure" condition. The other four character beats (1, 3, 8, 13) are scale or void beats and are not grounded.