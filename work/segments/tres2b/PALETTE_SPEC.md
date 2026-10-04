# Segment 4 — TrES-2b: palette + visual identity spec

Status: **built and rendered.** All 14 beats in `script.json` have a renderer in
`_cards.py`, and `python tres2b/_cards.py` renders one still per beat into
`cardsheet/` and exits 0. No reference material was fetched, viewed, or used as a
creative input (builder firewall, CLAUDE.md §8).

Authority, in precedence order:
1. `work/STYLE_CANON.md` — the measured spec. Overrides CLAUDE.md §4 and §7 where
   they disagree.
2. `work/lib/type.py`, `work/lib/ink.py`, `work/lib/cardframe.py` — the shipped
   implementation of that spec.
3. CLAUDE.md §6 (the character), §7 (card anatomy, palette rules).

Subject: the darkest exoplanet ever measured — a tidally locked M-dwarf planet
that reflects under 1% of the light its star sends at it, keeps one hemisphere at
~2000 K and the other at nothing at all, and is being unmade by its own
swelling, dying star. Tone target: **absence**. Almost every word on this card
describes light that is not there. The palette has to make that legible, which is
why the segment's dominant colour is the field itself and its only saturated
colour is the dull ember of a planet nobody can see.

---

## 1. The palette (7 colours, locked)

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Slate-black | `#14161C` | (20, 22, 28) | All linework, the planet's own body, every word on a cream card, header glyph fill |
| paper | Bone-cream | `#F2EAD6` | (242, 234, 214) | Title strip, every Register-P card field, the keyline behind type on void |
| deep | Void | `#05060B` | (5, 6, 11) | The night hemisphere, the third swatch, the space field, the planet's dead side |
| beam | Signal amber | `#E8A33D` | (232, 163, 61) | Incoming starlight, the forever-loop, the contradiction underline, captions on deep |
| ember | Dull ember | `#C2482B` | (194, 72, 43) | The 2000 K day side, the atmosphere tail, the lit crescent, the furnace strata |
| bone | X-ray bone | `#DCE6EC` | (220, 230, 236) | The coal swatch, every word and rule on void, the swatch borders, the planet's void rim |
| ash | Asphalt grey | `#8E9499` | (142, 148, 153) | The asphalt swatch, the ground bands, the empty thermometer tubes |

**Not a card accent:** `EMBER_SHADE` `#963720` → `(150, 55, 32)`, defined at the
top of `_cards.py`. A flat shadow tone used *only* as a shape inside the ember
portrait (beat 8) and inside the furnace strata (beat 7). It never carries a word
and never appears on its own. At 1.49:1 against ember it reads as shading, not as
a second object.

**Eighth colour, deliberately not in the palette:** the stickman's shirt red
`#C83232` (`work/lib/stickman.py`, `SHIRT = (200, 50, 50)`). It is a global of the
character, identical in all 12 segments, and is what makes him findable. Because
it is fixed, **no card accent here may be a true red** — `ember #C2482B` is a
burnt orange-red, deliberately separated from the shirt in both hue and value
(h≈11° vs h≈0°, L≈45% vs L≈49% on adjacent backgrounds) precisely so the
character's red never dissolves into the planet's glow. The two never appear in
the same register: the shirt is on the character, ember is on the planet or the
sky.

### Why there is so little chroma

Highest chroma in the set is amber `#E8A33D` (H≈34°). Ember `#C2482B` is H≈11° at
S≈64%. Everything else — ink, paper, deep, bone, ash — sits inside a narrow cold
band between L≈8% and L≈85% with S under 20%. That is not a stylistic accident:
this is the segment about a planet that gives back almost no light, so the frame
must be mostly dark, and the only saturated things permitted on it are the two
things that *are* emitting — the incoming beam and the 2000 K limb. Add a third
hot colour and the card stops arguing.

### Measured contrast (WCAG 2.x ratios, computed from the values above)

| Pair | Ratio | Verdict |
|---|---|---|
| Bone-cream on Void | 16.89:1 | text OK at any size |
| X-ray bone on Void | 15.98:1 | text OK at any size |
| Slate-black on Bone-cream | 15.08:1 | text OK at any size |
| Signal amber on Void | 9.39:1 | text OK at any size |
| X-ray bone on Void-field bottom `(16,18,40)` | 14.55:1 | text OK — the worst case on a real void card |
| Signal amber on Void-field top `(9,10,22)` | 9.13:1 | text OK — the worst case for a caption |
| Asphalt grey on Void | 6.60:1 | text OK; used as a fill and a ground, never as type |
| Dull ember on Bone-cream | 4.12:1 | large display type only (≥24 px), never a caption |
| Dull ember on Void | 4.10:1 | large display type only (≥24 px) — this is beat 7's "2000+ K" |
| Slate-black on Dull ember | 3.66:1 | **large display type only** — this is beat 5's "DAY" at 32 px. Above the 3:1 WCAG large-text threshold, below the 4.5:1 normal-text threshold. It is load-bearing and it passes, but it is the tightest type decision in the segment and should not be copied into 15–18 px stamps. |
| Character shirt `#C83232` on Void | 3.82:1 | acceptable — see note |
| Signal amber on Bone-cream | 1.80:1 | **forbidden — amber is a shape on cream, never a word** |
| X-ray bone on Bone-cream | 1.06:1 | **forbidden — bone is a shape on cream, never a word** |
| Asphalt grey on Bone-cream | 2.56:1 | fills and ground bands only, never type |

A note on the shirt, unchanged from segment 3: `#C83232` on the void field is
3.82:1, under the text threshold. That is not a defect. His silhouette is carried
by the cream limbs (14.55:1+) and the dark features inside the cream head, not by
the shirt, which is a mid-tone patch inside a high-contrast figure. It is also why
no card here puts a mid-tone accent *behind* him.

Binding rules that fall out of the table:

- On a **void** card every word is bone or amber. Ink is never type on void — it is
  1.02:1 against the field and would simply vanish.
- On a **cream** card every word is slate-black, always. Amber, bone and ash are
  fills and rules there.
- Ember carries words only at 32 px and larger, and only against void or against
  the ember field itself.
- Header glyphs are filled **slate-black**, not the card accent. The CLAUDE.md §7
  rule "header fill = segment accent" only survives if the accent is legible on
  cream, and here two of the four card accents are not (1.80:1 and 1.06:1).
  Ink is the header's accent.

---

## 2. The two registers

Every card is one of exactly two, taken from `script.json`'s own `register` field,
and the segment alternates them strictly: void, cream, void, cream … for all
fourteen beats. Nothing in the segment is a third thing.

| | **Void** (`'void'`) | **Cream** (`'cream'`) |
|---|---|---|
| Beats | 1, 3, 5, 7, 9, 11, 13 | 2, 4, 6, 8, 10, 12, 14 |
| Field | `C.void_backdrop` — a navy **vertical gradient** (9,10,22)→(16,18,40) plus a seeded starfield | flat `#F2EAD6` |
| Title strip | 84 px paper strip (`paper_band=True`) | none — the header floats on the card, which is already paper |
| Character ink | **cream** (`theme='dark'`) — limbs `#F5F0E1`, dark features | **dark** (`theme='light'`) — black strokes |
| Caption | amber `#E8A33D` on an ink keyline (`dark_bg=True`) | slate-black on a paper keyline (`dark_bg=False`) |
| Character grounding | **none** — he floats, as everything does in space | on an ash ground band with a wobbled top edge (`K.draw_ground`) |
| Halo around emissive bodies | `C.add_glow` — **additive**, correct on a dark field | `_cream_halo` — a blurred low-alpha warm **wash** |

### The additive-glow trap (this bit twice)

`cardframe.add_glow` is `ImageChops.add`. On the navy void field that is exactly
right — a dark field picks up light without washing out. On a bone-cream field
(near 242,234,214) *any* nonzero additive halo saturates to flat white, and the
star stops being a star and becomes a pale disc bug. Both cream beats that carry
a star — beat 4 and beat 10 — therefore go through `_cream_halo()` in `_cards.py`,
which builds the same warm halo as a Gaussian-blurred mask pasted with alpha. This
is a register rule, not a per-card preference: any future star on a cream card in
this segment must use `wash=`, not `glow=`.

---

## 3. Card accent assignment — 14 cards, no two adjacent share an accent

| # | Beat id | Register | Accent | Character |
|---|---|---|---|---|
| 1 | `hook_never_see_it` | void | beam `#E8A33D` | yes — flat deadpan, shielding eyes |
| 2 | `albedo_one_percent` | cream | ink `#14161C` | no — pure data |
| 3 | `darker_than_coal` | void | bone `#DCE6EC` | no |
| 4 | `tidally_locked_reveal` | cream | ember `#C2482B` | yes — zigzag, shrugged |
| 5 | `two_faces_forever` | void | beam `#E8A33D` | no — diagram |
| 6 | `never_warms_never_cools` | cream | ash `#8E9499` | yes — scared arc, hands up |
| 7 | `day_side_furnace` | void | bone `#DCE6EC` | no — pure data |
| 8 | `dull_red_glow` | cream | ember `#C2482B` | no — portrait |
| 9 | `hot_but_too_dark` | void | beam `#E8A33D` | yes — awed oval, pointing |
| 10 | `watch_the_star` | cream | ember `#C2482B` | yes — worried, hands up |
| 11 | `star_running_out_of_fuel` | void | bone `#DCE6EC` | no — pure data |
| 12 | `swelling_and_closer` | cream | ember `#C2482B` | yes — scared arc, cowering |
| 13 | `atmosphere_as_tail` | void | beam `#E8A33D` | no — diagram |
| 14 | `unmade_by_its_own_sun` | cream | ash `#8E9499` | yes — zigzag, shrugged |

**Adjacency audit**, in order: beam → ink → bone → ember → beam → ash → bone →
ember → beam → ember → bone → ember → beam → ash. **Thirteen boundaries, zero
repeats.**

Two constraints layered on top of the cycle:

- **Beat 14 (`unmade_by_its_own_sun`) carries the character and almost nothing
  else.** Mandatory per CLAUDE.md §10.8 — the most emotionally loaded second of
  the segment. It is also the only card in the segment with no annotation, no
  leader and no second subject. The emptiness is the picture: on every other card
  something arrives at that planet, and here nothing does.
- **Beats 1 / 4 / 6 / 9 / 10 / 12 / 14 carry him — seven of fourteen.** CLAUDE.md
  §6 requires at least four. The pure-data beats are 2, 7 and 11, which is where
  `script.json` says "no character - pure data beat"; beats 3, 5 and 13 are the
  diagram and portrait beats, which are data by another name.

### The planet never gets an accent

On every one of the fourteen cards the planet is `INK` on cream and `DEEP` on
void, or `EMBER` where a hemisphere is being shown lit. It is never the card
accent, and it never takes a saturated outline. That is the whole subject: a
6 px ink keyline is the only edge this object is permitted, and on void it gets a
4 px bone *rim* instead so the silhouette separates from the field — see §4.

---

## 4. The shared-geometry rule

The most common defect class in this segment was a hand-drawn wobbled fill with a
perfect `ImageDraw.ellipse` or an independently-wobbled second shape drawn over
it. The two curves disagree by a few pixels on two sides and the result reads as
a mismatched ring or a pole spike, not as paint.

`lib/ink.draw_disc` builds from a wobbled 8-gon (`a = tau*i/8`) run through
`smooth_closed`, 14 samples per segment. `_cards.py` therefore does two things:

- `_black_planet()` keeps the dense polyline `draw_disc` returns and strokes the
  rim along **that exact edge** (`d.line(dense + [dense[0]])`), never a fresh
  ellipse. Fixes the void rim on beats 1 and 13.
- `_left_half(dense)` returns **slices of that same dense polyline** —
  segments 5, 4, 3 and 2, each reversed — for the tidally-locked hemisphere on
  beats 5 and 9, so the lit half and the dark half share a pixel-identical limb
  and meet on a straight bone terminator with no spikes at the poles.

Beats 5 and 9 are the only two cards where a sphere is split, and they are
**day side on the left, night side on the right** in both. That is not arbitrary:
the character stands on the left of both cards, and the lit hemisphere is the one
his eyeline reaches first.

---

## 5. Type — the canon's locked table, verbatim

No new sizes, no second family. `work/lib/type.py` constants only:
`HEADER_PX = 48`, `LABEL_PX = 32`, `CAPTION_PX = 28`, `STAMP_PX = 15`.

| Role | Size | Face | Stroke | Where |
|---|---|---|---|---|
| Header — "TrES-2b" | 48 px | `comicbd.ttf` Comic Sans Bold | none | the 84 px strip on void; floated on the card on cream |
| Subject label — DAY, NIGHT, COAL, ASPHALT, 2000 K | 32 px | `comicbd.ttf` | none | on the subject it names |
| Diagram stamp — LYRA, ONE SIDE ONLY, NOT VISIBLE, NOW, THEN, AIR, THE FUEL LAYER | 18 px | `comicbd.ttf` | none | 18 is inside the canon's 12–18 stamp band |
| Floating caption | 28 px | `comicbd.ttf` | ink keyline on void, paper keyline on cream | one per card, schedule-supplied |
| Hero phrase — `< 1%` | 104 px | `comicbd.ttf` | 4 px paper keyline | beat 2 only |

**Consolas is retired** (STYLE_CANON §1–2). The segment uses one family —
Comic Sans Bold — for every word, at four sizes and one hero size.

**One hero word in the whole segment.** `< 1%` on beat 2, and it is in *symbols*,
not the caption's words, so it is not a restatement of what is being said. It goes
through `cardframe.hero_word`, which clamps **including** the keyline and
auto-shrinks; `_cards.py` never clamps against advance width, because the outline
stroke is drawn outside the glyphs and a phrase that passes an advance-width clamp
can still lose its last letter off the frame.

**No narration is ever printed as a caption.** The title strip carries the planet
name and nothing else. Everything else on screen is a subject label, a diagram
stamp, or the one hero phrase.

---

## 6. Gradient and texture denylist

**Legal gradients — exactly two locations in the segment**, both the red dwarf:
`_radial_core` with the flat stop ramp `#FFD696 → #C2482B → #601E14`, on beat 4
(`tidally_locked_reveal`, r=44) and beat 10 (`watch_the_star`, r=132). A star is
emissive; nothing else in this segment is.

**Never a gradient** (explicit):

- **The planet, in any card, at any size.** It is matte black on void, matte black
  on cream, and where a hemisphere is lit it is a FLAT `#C2482B` with a flat
  `EMBER_SHADE` crescent for shading. The instant this disc gets a specular it
  stops being the darkest planet in the catalogue. This is the segment's own
  subject and it is also the rule CLAUDE.md §10.6 exists to enforce.
- The swatch row on beat 3, the thermometers on beat 6, the concentric star
  outlines on beat 12, the atmosphere sheets and tail on beat 13, every ground
  band, the starfield, the title strip, and the character in every pose.

**Texture — `K.stipple` takes a RECT, not a circle.** Its corners land at
`r * 0.9 * 1.414 = 1.27r`, i.e. off the limb, which is how the first pass put
black measles on the cream paper around the beat 8 portrait. Every stipple in this
segment is inset to the **inscribed square at `r * 0.62`**.

**Stipple density is solved from the radius, not fixed.** A constant density puts
~160 black dots on a 132 px star and ~18 on a 44 px dwarf — measles on one,
clean on the other. `_red_dwarf` computes
`density = 48 / (1.5376 * r²)`, which is ~48 dots at any star size. The beat 8
portrait uses 0.0012, which is ~45 dots on a 488 px disc.

---

## 7. Determinism

Every `wobble_points`, `stipple`, `void_backdrop` and `draw_ground` call in
`_cards.py` takes an explicit integer seed. There is no global random state and no
`hash()` anywhere in the module, so a re-render is byte-identical — which is what
lets the builder/critic loop compare frames at the same timestamp across rounds
without the seed drift becoming a false difference.

---

## 8. Files

- `work/segments/tres2b/_cards.py` — the 14 renderers, the helpers above, and the
  self-test. `RENDERERS` is module-level and keyed by beat id; each `fn(card,
  planet)` returns a 1280×720 RGB `Image`. The frame generator merges it into
  `cardframe.RENDERERS`; this module does not redefine the global dispatch and
  does not edit anything in `work/lib/`.
- `work/segments/tres2b/script.json` — the narration, 228 words, 14 beats, the
  `register` and `visual` fields both drive this spec.
- `work/segments/tres2b/cardsheet/beat_01.png` … `beat_14.png` — the self-test
  output.

Self-test:

```
cd C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments && python tres2b/_cards.py
```

prints one line per beat, asserts every render is 1280×720 RGB, writes all 14
stills, and exits 0.
