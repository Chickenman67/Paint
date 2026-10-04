# LTT 9779 b — PALETTE_SPEC

Segment 9 of the Gauntlet2 paint-explainer build.
Subject: a super-Earth so reflective it is the brightest thing in its own
system — it swallows almost no starlight and hands nearly all of it back.
Tone: quiet star, loud planet; borrowed light; a mirror, not a coal.

The renderer is `work/segments/ltt9779b/_cards.py`. It defines its OWN palette
(`MY_PAL`) and references it directly. `cardframe.PAL` is segment 3's palette
and is used only for the generic helpers (`void_backdrop`, `_radial_core`).

This spec OVERRIDES CLAUDE.md §4/§7 wherever the two disagree, per
`work/STYLE_CANON.md`.

---

## 1. The locked palette

Six colours. Every pixel on every one of the fourteen cards is one of these, of
a flat ink-black, or of a derived tint declared in §1.3.

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| `ink` | slate-black | `#14161C` | (20, 22, 28) | Every outline, every label, every type mark, on either register. Also the dark-side fill of the split sphere on `irradiated_dayside`. |
| `paper` | bone-cream | `#F2EAD6` | (242, 234, 214) | The cream register background; the 84 px title strip on void cards; the caption keyline on cream cards. |
| `deep` | void | `#05070E` | (5, 7, 14) | The void register background, under the starfield. |
| `silver` | mirror silver | `#C6D4DD` | (198, 212, 221) | The world's lit body, the metal cloud deck, the axis lines and plot traces on `checked_twice`, and every soft halo on a void card. |
| `amber` | signal amber | `#E8A33D` | (232, 163, 61) | The ONE accent. Arrows, rays, the reflected arrow, the incoming arrow, the plot peak, hero words, and the star's inner gradient. |
| `steel` | steel teal | `#4A7484` | (74, 116, 132) | The secondary / annotation colour: night sides, shadowed limbs, secondary labels, quiet diagram strokes. |

### 1.1 The shirt red is NOT a palette colour

`#C83232` (200, 50, 50) is the character's shirt, declared once as `SHIRT` and
referenced **only** by the stickman library. It is deliberately absent from the
table above.

The reason is a compositing rule, not an aesthetic one: if a card's accent were
also red, the character would dissolve into the background on exactly the six
cards where he appears. The whole segment therefore has **no red accent at
all** — its accent is amber.

**One documented exception: `the_bad_number` (beat 8).** That card has **no
character**, so a collision is physically impossible, and the script's own
visual is "one number underlined and circled twice in red pen". The red pen on
that card is `SHIRT` and nothing else uses it there. This is the only beat in
the segment where red appears.

### 1.2 Ink and cream per register

The character is drawn **cream-on-dark** in space and **dark-on-light** on
paper. This is the canon's two-register rule and it is not a preference: a dark
character on a near-black starfield is simply invisible.

| Register | Background | Character fill | Character outline | Type colour |
|---|---|---|---|---|
| `void` | `deep` + starfield | bone cream (`paper`) | `ink` | `amber` caption, `silver` labels |
| `cream` | `paper` | `ink` | `ink` | `ink` caption, `steel` secondary |

`C._draw_stickman(img, card, theme=...)` is called with `theme='dark'` on the
seven void cards and `theme='light'` on the three cream cards that carry him.

### 1.3 Derived tints (declared, not new hues)

These are computed constants, not palette entries. They are blends of two locked
colours and introduce no new hue:

| Name | Derivation | Used for |
|---|---|---|
| `SAND` | `paper` 0.70 + `amber` 0.30 | The `_ground` horizon band on every cream card. |
| `BONE_ISH` | `paper` + `silver`, ~50 % | The blazing world on `brilliant_and_bare`; its bright fill must clear the cream card by a visible step. |
| `WHITE_HOT` | `silver` + 88 % toward white | The crescent/grin on `smile_at_mild_star`, the glint on `hook_inverted`, the lit half of `irradiated_dayside`, the blazing limb on `no_survival`. Same hue as `silver`, one value up. |

### 1.4 Measured contrast (WCAG 2.1 relative luminance)

| Pair | Ratio | Verdict |
|---|---|---|
| `ink` on `paper` | 15.6 : 1 | AAA |
| `amber` on `deep` | 9.1 : 1 | AAA |
| `silver` on `deep` | 13.4 : 1 | AAA |
| `steel` on `deep` | 3.6 : 1 | AA for ≥24 px, **stamp size only** |
| `ink` on `paper` (labels) | 15.6 : 1 | AAA |
| `amber` on `paper` | 1.8 : 1 | **FAIL — prohibited** |

**Binding rule.** `amber` on `paper` fails at 1.8:1 and is never used. Every
amber mark on a cream card is a **fill or a shape**, never type: the reflected
arrow, the dimension rule and its arrowheads, and the oven door. Type on a cream
card is `ink` or `steel` only.

`steel` on `deep` at 3.6:1 is legal at `STAMP_PX` (15 px) and above and is used
only for secondary annotations (`NEVER COOLS`, `ONE WORLD`, `TOO HIGH TO BE
TRUE` is red not steel). It is never used for `LABEL_PX` or `CAPTION_PX`.

---

## 2. Accent cycle and adjacency

The accent cycle for this segment is deliberately **not** a repeating
4-colour rotation. There is only one accent (`amber`), so the cycle is a
three-state rotation over the three things an accent can mark:

```
state A — THE LIGHT IS THE SUBJECT   (amber on the subject itself)
state B — THE LIGHT IS THE ARGUMENT (amber on an arrow / a ray / a plot mark)
state C — NO ACCENT                 (the card is a pure scene; amber is absent)
```

Adjacency audit, beat by beat:

| Beat | State | Accent appears as |
|---|---|---|
| 1 `hook_inverted` | A + B | The glint and its halo; `NOT A COAL` stamp |
| 2 `name_card` | A | The M-dwarf's gradient core only |
| 3 `planet_is_loud` | A + B | The star core; the perihelion tick; `DIM STAR` |
| 4 `metal_sky` | — | **None.** Pure register-P scene. |
| 5 `irradiated_dayside` | B | The six rays; the `TERMINATOR` leader |
| 6 `nothing_absorbed` | B | The two fat reflected arrows |
| 7 `coin_in_the_dark` | A | The `MIRROR` stamp; the glare's core |
| 8 `the_bad_number` | — | **None** (red pen is a separate case, §1.1) |
| 9 `checked_twice` | B | The peak dash, the tick, `TWO CHECKS`, `SAME PEAK` |
| 10 `should_be_an_oven` | A | The oven door fill |
| 11 `smile_at_mild_star` | A | The grin crescent; `MILD STAR` |
| 12 `brilliant_and_bare` | B | The dimension rule and its arrowheads |
| 13 `no_survival` | B | The `NO SURFACE` hero word |
| 14 `borrowed_light` | B | The incoming arrow |

**Binding rule.** No two adjacent beats are both state A on the same element.
The three no-accent beats (4, 8, 12) are never adjacent to each other, so the
segment never goes two consecutive cards with no amber at all.

---

## 3. Emissive treatment and the gradient denylist

### 3.1 What is emissive

Exactly three things on exactly two beats:

- `name_card` (beat 2) — the M-dwarf's core.
- `planet_is_loud` (beat 3) — the same star's core.

Both use `C._radial_core`, a three-stop radial ramp. **These two calls are the
only smooth gradients in the segment.** The bright half of `irradiated_dayside`
and the blazing bodies on beats 12 and 13 are **flat fills** — a lit hemisphere
is a lit hemisphere, not a ramp, and a planet is not an emissive body.

### 3.2 Soft light: `_soft_halo`, never `C.add_glow`

`C.add_glow` fills an inner ellipse at full `strength`, blurs it by only
`0.40 * size`, and multiplies by a hard circular cutoff. The result is a broad
**saturated plateau with an abrupt rim**. That is correct for a white pulsar
core on black and wrong for everything else: on this segment's near-black
fields it shipped a visible tinted **disc** behind the subject on eight of the
fourteen cards — a brown ball at the glint, a grey plate around the star, a pale
disc over the whole sky.

Every soft light in this module therefore goes through `_soft_halo`, which builds
a quarter-resolution radial falloff mask with `numpy` (`np.clip(1 - t) ** k`),
resizes it bilinearly and adds it to the region. It falls to **zero at r** with
no plateau and no rim.

| Beat | Halo | Radius | Strength | Falloff |
|---|---|---|---|---|
| 1 | amber, at the glint | 132 | 96 | 2.8 |
| 3 | silver, at the planet | 96 | 54 | 2.6 |
| 3 | amber, at the star | 128 | 54 | 2.6 |
| 5 | silver, on the lit half | `r * 1.55` | 64 | 2.7 |
| 10 | amber, at the oven mouth | 208 | 62 | 2.8 |
| 7 | silver, terminating the camera glare (`_glare`) | `r * 2.4` | 70 | 2.6 |
| 11 | silver, behind the grin | `r * 1.15` | 60 | 2.8 |
| 12 | silver + white, on the blazing world | 420 / 260 | 96 / 90 | 2.2 / 2.4 |
| 13 | silver, on the blazing limb | `r * 1.85` | 56 | 2.9 |
| 14 | silver, on the small world | 300 | **34** | 2.0 |

**Binding rule.** On a **cream** card a halo's strength must stay low — at 56
and above on `borrowed_light` it printed a grey smudge on the paper. A shine on
paper has to sit well under the card's own value or it is dirt, not light.

### 3.3 Gradient denylist

The following **must never** carry a gradient:

- a planet body (beat 1's dark world, beat 3's planet, beat 7's coin, beat 11's
  grinning world, beat 14's small world);
- an orbit ellipse, an axis, a plot trace, a tick;
- the metal cloud deck or any stratum;
- the oven body, the oven door, the day/night halves;
- any card's title strip, any caption, any label, any stamp;
- the character's body, head, mouth or limbs.

### 3.4 Planets are painted, not shaded — and never bullseyes

`C.space_body` draws its "wavy contour bands" as **stroked ellipse outlines** at
alpha 150, width `0.055 * r`. On a light planet that reads as painterly strata.
On a **dark** planet it reads as a painted **bullseye** — beat 11 shipped a
four-ring dartboard with a grin lying across it, and beat 1 a three-ring target.

**Binding rule.** A dark planet is drawn FLAT: a single fill disc, one dim sheen
arc on the upper-left limb, one shadow crescent low-right. `_world` (a wrapper
that pulls `space_body`'s band colour 60 % toward base) is used only where the
base is light enough that the strata stay under the noise floor. No card in this
segment puts a bullseye on screen.

---

## 4. The red-pen exception, in full

`the_bad_number` (beat 8) is the only card in the segment that uses
`SHIRT` (200, 50, 50), and it uses it for exactly three things:

1. two concentric circles around the needle tip;
2. two margin arrows inside the panel;
3. four scribble strokes, at `K.DETAIL` (4 px) — at `K.FINE` (2 px) on cream
   they read as dead pixels, not as pen;
4. the `TOO HIGH TO BE TRUE` stamp.

The conditions that make this legal, all of which must hold:

- **No character on the card.** `SELF_TEST_SMITHMAN` has no entry for
  `the_bad_number`, and `script.json` marks it
  `no character - pure data beat`. A collision with the shirt is impossible.
- **The script asks for it.** Beat 8's `visual` field is "one number underlined
  and circled twice in red pen". Red pen is the subject.
- **Nothing else on the card is red.** The dial, ticks, needle, panel and labels
  are `ink`, `amber` and `steel` only.

If a character is ever added to this beat, this exception is void and the red
must be re-drawn as amber.

---

## 5. Type-size lock

From `work/lib/type.py`. These are the only four sizes in the segment. Consolas
is retired (CLAUDE.md §7's old 72/36/32/18 Consolas table is historical and must
not be used).

| Role | Constant | px | Face |
|---|---|---|---|
| Header (title strip) | `T.HEADER_PX` | 48 | `comicbd.ttf` Comic Sans Bold |
| Planet / subject label | `T.LABEL_PX` | 32 | `comicbd.ttf` |
| Floating caption | `T.CAPTION_PX` | 28 | `comicbd.ttf` |
| Stamp / tiny annotation | `T.STAMP_PX` | 15 | `comic.ttf` Comic Sans |

**One family.** `comicbd.ttf` for headers, labels and captions; `comic.ttf` for
stamps. Never mixed within a size, never a third face.

**The hero word.** Two cards carry one dominant phrase — `SAME PEAK` on beat 9
and `NO SURFACE` on beat 13. Both go through `C.hero_word`, never a local text
helper. `hero_word` measures the same call the renderer makes and clamps
**including** the 3 px keyline; a local clamp against `T._bbox`'s advance width
ignores the stroke and ships clipped text.

The request size is `px=48` on both, which is the ramp's own input, not a fifth
type size — `hero_word` is free to step it down if the phrase will not fit, and
both phrases are handed `y_max` so the word cannot drop onto the caption. These
two calls are the **only** `px=` literals in the module; every other mark goes
through `_label` (`T.LABEL_PX`), `_tiny` (`T.STAMP_PX`) or `C._caption`
(`T.CAPTION_PX`).

**Captions are audio, not type.** The narration line is never printed. The only
type on a card is the planet name in the strip, plus diagram labels and stamps.

---

## 6. Register assignment

| Beat | Register | Character | Ground band |
|---|---|---|---|
| 1 `hook_inverted` | void | yes (cream) | — |
| 2 `name_card` | cream | no | — |
| 3 `planet_is_loud` | void | no | — |
| 4 `metal_sky` | cream | yes (ink) | `_ground` at y=612 |
| 5 `irradiated_dayside` | void | no | — |
| 6 `nothing_absorbed` | cream | no | — |
| 7 `coin_in_the_dark` | void | yes (cream) | — |
| 8 `the_bad_number` | cream | no | — |
| 9 `checked_twice` | void | no | — |
| 10 `should_be_an_oven` | cream | yes (ink) | `_ground` at y=588 |
| 11 `smile_at_mild_star` | void | no | — |
| 12 `brilliant_and_bare` | cream | no | — |
| 13 `no_survival` | void | yes (cream) | — |
| 14 `borrowed_light` | cream | yes (ink) | `_ground` at y=606 |

Six beats carry the character, which satisfies CLAUDE.md §6's requirement of at
least four. The eight beats marked "no character" are exactly the eight whose
`script.json` `visual` field begins `no character - pure data beat`.

**Binding rule — the horizon must be at the character's feet.** On every cream
card with the character, `_ground`'s `y_top` equals `y_top + height` from the
schedule's stickman block. Beat 14's first pass had his feet at y=640 against a
horizon at y=606, so his legs were buried in the sand and he read as a bust.
If the live schedule moves him, **move the horizon with him**.

---

## 7. Determinism

Every `wobble_points` / `stipple` / `starfield` / `void_backdrop` /
`_radial_core` / `_soft_halo` call takes an explicit integer `seed=`. There is
no global random state anywhere in the module and builtin `hash()` is never
called (it is salted per process, so it would break re-render identity).

`python ltt9779b/_cards.py` re-renders all fourteen cards byte-identically and
exits 0. The self-test additionally asserts that no renderer mutates the `card`
dict it is handed, and cross-checks `RENDERERS` against `script.json` in both
directions — a missing beat id or an extra one is a `SystemExit`.

---

## 8. Files

| File | Role |
|---|---|
| `work/segments/ltt9779b/_cards.py` | All 14 renderers + `RENDERERS` + the `__main__` self-test |
| `work/segments/ltt9779b/PALETTE_SPEC.md` | This file |
| `work/segments/ltt9779b/script.json` | Narration and per-beat visual fields (read-only input) |
| `work/segments/ltt9779b/cardsheet/beat_NN.png` | Self-test output, one per beat |
| `work/lib/type.py`, `ink.py`, `cardframe.py`, `stickman.py` | Shared, read-only |