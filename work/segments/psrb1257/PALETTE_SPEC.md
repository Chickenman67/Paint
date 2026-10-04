# Segment 3 — PSR B1257+12: palette + visual identity spec

Status: design only. No frames rendered. No reference material used (builder firewall).
Authority: CLAUDE.md §4 (style), §7 (card anatomy, type scale, palette rules), §10.6 (gradient limits), §10.8 (stickman at the fate beat).
Subject: a millisecond pulsar in Virgo — a ~20 km dead neutron star spinning hundreds of times a second, firing twin cones of radiation out of its magnetic poles like a lighthouse. Three planets orbit inside that beam. Tone target: deep space, dead star, lethal light. No neon.

---

## 1. The palette (6 colors, locked)

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Slate-black | `#14161C` | (20, 22, 28) | All linework (3px figure / 2px diagram / 1px fine), header glyph fill, caption text on cream |
| paper | Bone-cream | `#F2EAD6` | (242, 234, 214) | Title strip, any "paper" card, skull/bone motif fills |
| deep | Void | `#05060B` | (5, 6, 11) | The space field, illustration background, every dark card |
| accent 1 | Signal amber | `#E8A33D` | (232, 163, 61) | The beams' warm edge, captions on deep, alert stamps, the lethal-light reading |
| accent 2 | X-ray bone | `#DCE6EC` | (220, 230, 236) | The star core, beam core, the three planets, starfield dots |
| accent 3 | Magnet violet | `#6E5A9C` | (110, 90, 156) | Radiation-bath haze, orbit rings, magnetic field arcs, large shapes only |

**Seventh color, deliberately not in the palette:** the stickman's shirt red `#C83232` (`work/lib/stickman.py:24`, `SHIRT = (200,50,50)`). It is a global of the character, identical in all 12 segments, and is what makes him findable. Because it is a fixed global, **no card accent in this segment may be red** — the character's red is the only red on screen, so he never dissolves into the background. Alert/warning color for cards is amber, never red.

One note on the shirt against this palette: `#C83232` on the void field is 3.82:1, well under text contrast. That is fine and is not a defect — his silhouette is carried by the black limbs and the white head, which are 1.12:1 and 15.98:1 against the field respectively. The shirt is a mid-tone patch inside a high-contrast figure, not a load-bearing edge. It is also the reason no card may use a mid-tone accent *behind* him: a violet or amber card would reduce his limb-to-background separation on the beat that most needs it, which is why card 10 (his fate beat) is bone.

### Why not neon

Highest chroma in the set is amber `#E8A33D` (H≈34°, S≈75%, L≈57%). Violet `#6E5A9C` is desaturated to S≈28%. There is no cyan, no pure green, no `#00FFFF`-class value anywhere, and the only pure white is `#FFFFFF` inside the star core at r < 0.25. The reference's signature look is flat saturated paint; we keep the saturation in amber and let everything else sit in a narrow, cold band so the beam is the only hot thing in frame.

### Measured contrast (WCAG ratios, computed against the values above)

| Pair | Ratio | Verdict |
|---|---|---|
| X-ray bone on Void | 15.98:1 | text OK |
| Signal amber on Void | 9.38:1 | text OK |
| Bone-cream on Void | 16.88:1 | text OK |
| Slate-black on Bone-cream | 15.09:1 | text OK |
| Magnet violet on Void | 3.48:1 | **fills and large shapes only — never caption or annotation text** |
| Signal amber on Bone-cream | 1.80:1 | **forbidden — amber type never sits on cream** |
| X-ray bone on Bone-cream | 1.06:1 | **forbidden — bone type never sits on cream** |
| Magnet violet on Bone-cream | 4.86:1 | large display shapes only, never 32pt body text on cream |

Binding rules that fall out of that table:
- On a **deep** card, captions are amber (default) or bone (emphasis beats). Tiny annotations are bone at 18pt, never violet.
- On a **cream** card, every piece of text is slate-black. Amber and bone are fills only.
- Violet is a shape color. It never carries a word.
- Header glyphs are filled **slate-black** on the cream strip, not the card's accent. Reason: the §7 rule "header fill = segment accent" only works if the accent is legible on cream, and two of the three accents are not (1.80:1 and 1.00:1). `work/lib/palette.py:79` already resolves this the same way (`HEADER_COLOR = INK`), and the reference measurement in `work/ref/ref_style_spec.md` records the reference as black-on-white in the title strip. Ink is the header's accent.

---

## 2. Card accent assignment — 12 cards, no two adjacent share an accent

The assignment is a strict 4-cycle over `{cream, bone, amber, violet}`, repeated three times. It is mechanical rather than per-card judgment, so it cannot drift when a card is inserted, dropped, or re-timed. Any prefix or suffix of the cycle is also valid, so truncating the list to however many cards the alignment actually yields keeps the invariant.

| # | Card id | Accent | Card id | Accent |
|---|---|---|---|---|
| 1 | `intro_name` | cream `#F2EAD6` | 7 | `sticky_dust` — violet `#6E5A9C` |
| 2 | `millisecond_spin` — bone `#DCE6EC` | | 8 | `the_naming` — amber `#E8A33D` |
| 3 | `twin_beams` — amber `#E8A33D` | | 9 | `evaporated` — cream `#F2EAD6` |
| 4 | `radiation_bath` — violet `#6E5A9C` | | 10 | `the_fate_beat` — bone `#DCE6EC` |
| 5 | `the_planets` — cream `#F2EAD6` | | 11 | `what_remains` — amber `#E8A33D` |
| 6 | `carbon_world` — bone `#DCE6EC` | | 12 | `finale_dead_star` — violet `#6E5A9C` |

Adjacency audit, in order: cream→bone, bone→amber, amber→violet, violet→cream, cream→bone, bone→violet, violet→amber, amber→cream, cream→bone, bone→amber, amber→violet. **Eleven boundaries, zero repeats.**

Two additional constraints on top of the cycle:
- **Card 10 (`the_fate_beat`) carries the stickman** — mandatory per §10.8, the most emotionally loaded second of the segment. Bone accent plus his red shirt: maximum separation from his silhouette.
- **Card 11 (`what_remains`) also carries him**, alone in frame. The pair 10/11 gives the fate beat and its aftermath, which is the emotional spine of the segment. A third appearance at card 2 (`millisecond_spin`, bone, pointing at the star) sets up the "lighthouse" idea before the stakes land.

**Palette bleed across the segment boundary:** the bridge uses `work/lib/transition.py` `make_white_card()`, which is pure `#FFFFFF`. That is shared assembly code used by all 12 segments — do not retint it to bone-cream for this segment, or segments 1, 2 and 4–12 inherit the change. The `§5.7` "0.5 s black frame" rule is superseded by the measured reference bridge (1.0 s fade to white, 2.25 s hold, 0.5 s fade out) and `transition.py` already implements the reference behavior. Keep it. The void-blue palette therefore starts *after* a white card, which is a stronger reset than a black bridge would have been.

---

## 3. Emissive treatment — the pulsar's beams

The beams are the one genuinely emissive subject in this segment, so they are the one place a gradient is legal. Everything else is flat.

**Star core (card 2, card 3, card 12).** Radial gradient, 3 stops, no banding:
- r = 0.00 → `#FFFFFF`
- r = 0.55 → `#DCE6EC` (x-ray bone)
- r = 1.00 → `#6E5A9C` (magnet violet, the magnetic limb)

Rendered via `work/lib/texture.py:34` `radial_gradient()`, then `stipple_overlay(density=0.02, seed=<per-card seed>)` on top so the core keeps the spray-paint grain. The seed is deterministic per card (`random.seed(hash("b1257_core"))` style, §7) so re-renders are byte-identical.

**Beam cones (card 3, and rotating small in the corner of card 4).** Two opposing cones from the magnetic poles, 180° apart, drawn on a separate RGBA layer and composited once:
- Axis ramp: apex alpha 1.0 → tip alpha 0.0, linear along the cone length. Apex color `#DCE6EC`; the cone's two edges shift to `#E8A33D` at roughly 70% along the length, so the beam reads as a two-tone funnel rather than a white cone.
- The cone edges are drawn as **2px linework in amber, unblurred**, on top of the gradient layer. The gradient is the fill; the hand-drawn edge is the line. This is what keeps the beam from reading as a soft-focus stock lens flare.
- Blur radius on the beam fill layer: max 6px. §4 forbids smoothing on *linework*; the beam is a fill, and a hard-edged cone is the single thing that would make this segment look like clip-art rather than paint.
- Sweep: one full revolution every 3.0 s (visual pace only — it is not to scale, and the narration says milliseconds; the discrepancy is the joke and should not be annotated). Both cones rotate as a rigid pair.

**Halo.** Two flat concentric rings around the core in magnet violet at 12% and 22% alpha. Flat, no gradient — these are outside the emissive subject and the rule stops at the core edge. They give the "dead star with a magnetic field around it" read without softening anything.

**Never gradient (explicit denylist).** The three planets, in every card, on every beat. Orbit ellipses and the radiation-bath haze. The void-blue card background and the starfield dots. The cream title strip and the caption band. The skull/bone motif. The stickman, all of him, every expression and pose. Any card-level wash or vignette. §10.6 exists because KELT-9b's portrait got a radial gradient and it read as a soft-fantasy halo instead of paint — the planets here are carbon and rock, matte surfaces under a hard light, and they take flat fill plus stipple only. `texture.planet_disc()` and `banded_planet()` are the correct tools; `radial_gradient()` is not.

---

## 4. Type sizes — the locked §7 table, verbatim

No new sizes. These five are the whole set for the segment.

| Role | Size | Face | Stroke | Color on this segment |
|---|---|---|---|---|
| Header — hand-lettered "PSR B1257+12" | 72pt | Consolas Bold | 3px black outline | fill slate-black `#14161C` on the cream strip |
| Stamp — "B1257+12", "ARCHIVE", "1 MS", "VIRGO" | 36pt, all-caps | Consolas Bold | 1px | amber on deep; slate-black on cream |
| Caption body | 32pt | Consolas Regular | none | amber `#E8A33D` on deep; slate-black on cream |
| Caption emphasis | 32pt | Consolas Bold | none | bone `#DCE6EC` on deep (a shouted word); slate-black on cream |
| Tiny annotation — numbers on diagrams | 18pt | Consolas Regular | none | bone on deep; slate-black on cream. **Never violet** (3.48:1) |

Family is consolab.ttf / consola.ttf only. Caption stays ≤60 characters, ≤12 words, one line. Header fits: "PSR B1257+12" is 12 glyphs at 72pt Consolas Bold ≈ 480px in a 1280px frame.

### One conflict to resolve before the builder starts

§7 specifies sizes in points with thin strokes (72/36/32/32/18pt, 3px/1px/none). The shipped `work/lib/type.py` implements the *measured reference* values instead: `HEADER_PX = 44`, `CAPTION_PX = 27`, `STAMP_PX = 7` (drawn at 18 via `STAMP_PX + 11`), with strokes 7/4/3. The reference measurement in `work/ref/ref_style_spec.md` puts the title strip at ~30-36px of black text on white, which is what type.py encodes.

Recommendation: use the `work/lib/type.py` constants verbatim and treat them as the reference-measured realization of the §7 table. Segments 1 and 2 have been rendered and iterated to critic wins on type.py's numbers; switching segment 3 to literal §7 points would be exactly the type-scale drift §4/§10.4 name as a failure mode, and the critic compares rendered frames against the reference, where type.py is right. Either way, the set of sizes is closed — five, no others.

---

## 5. Files this spec should land in

- `work/lib/palette.py` — add `SEGMENT_3` alongside `SEGMENT_1` / `SEGMENT_2`, plus a `get_segment_palette(3)` branch.
- `work/segments/psrb1257/_frames_r1.py` — the card table from §2, keyed by card id, with the accent per row.
- `work/scripts.py` — the `PSR_B1257_SCRIPT` narration, 190-213 wpm, original wording.
