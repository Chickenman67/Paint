# Segment 7 — Gliese 436 b: palette + visual identity spec

Status: design + implemented in `_cards.py`. No reference material used (builder firewall).
Authority: `work/STYLE_CANON.md` (overrides all other docs), CLAUDE.md §4/§6/§7/§10.
Subject: a Neptune-sized water world whose surface is a *supercritical fluid* — ice that is on
fire and does not melt — dragging a glowing hydrogen/helium tail around its star. Tone target:
impossible physics, cold beauty, quiet menace. Not neon; not gory.

The locked palette lives in `_cards.py` as `MY_PAL` and is referenced directly by every renderer.
`lib/cardframe.py`'s module-level `C.PAL` belongs to segment 3 (PSR B1257+12) and is NOT used for
card accents here; only genuinely generic helpers (`void_backdrop`, `space_body`, `add_glow`,
`_radial_core`, `hero_word`) are borrowed from the lib.

---

## 1. The palette (6 colors + the character's fixed red, locked)

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Frost-slate | `#12181E` | (18, 24, 30) | All linework and outlines (6px large / 4px detail / 2px fine), header glyph fill, all type on cream |
| paper | Bone-cream | `#F0ECDC` | (240, 236, 220) | Title strip, the three cream/register-P cards, the ice-cube side faces |
| deep | Void | `#060A10` | (6, 10, 16) | The space field on every void card, the illustration background |
| accent 1 | Glacier | `#A8D8E8` | (168, 216, 232) | The ice / the planet's mass, captions-on-deep fallback, cold-crush arrows, pressure read |
| accent 2 | Steam | `#FAFCFF` | (250, 252, 255) | The supercritical smudge band, the ice cube's lit top face, the planet's lit crescent, the star's core |
| accent 3 | Ember | `#F09E34` | (240, 158, 52) | The burning / the tail / the heat arrows / the escape glow, "hot" stamps and the ship's hull |
| accent 4 | Abyss | `#2E3E60` | (46, 62, 96) | Cold depth: the phase-diagram lines, wash fields, the melt pool, flow strokes. Large shapes / thin diagram lines only |

**The one color that is not in the palette:** the stickman's shirt red `#C83232`
(`work/lib/stickman.py`). It is a global of the character, identical across all 12 segments, and is
what makes him findable. Because it is fixed, **no card accent here is red** — the ember is a warm
amber (`#F09E34`, H≈33°), deliberately clear of the shirt's red, so he never dissolves into the
background. "Hot/warning" for cards is always ember, never red.

`steam` is the near-white stop. It is only ever a fill or an emissive-core stop — **never type on
cream** (see the contrast table). Together `glacier` + `steam` + `ember` give the three readings the
segment needs: cold, in-between, hot.

### Measured contrast (WCAG ratios against the values above)

| Pair | Ratio | Verdict |
|---|---|---|
| Glacier on Void | 13.5:1 | text OK |
| Ember on Void | 9.0:1 | text OK (captions, hero words on deep) |
| Steam on Void | 19.3:1 | text OK (emphasis) |
| Frost-slate on Bone-cream | 15.7:1 | text OK (all type on cream) |
| Bone-cream on Void | 17.2:1 | text OK |
| Abyss on Void | 2.3:1 | **fills and thin diagram lines on deep only — never caption/annotation text** |
| Abyss on Bone-cream | 6.4:1 | large display / diagram lines on cream; not body text |
| Ember on Bone-cream | 2.0:1 | **forbidden as type on cream** (embber is a fill on cream cards) |
| Steam on Bone-cream | 1.03:1 | **forbidden as type on cream** |

Binding rules:
- On a **void** card, captions and hero words are ember (default via `C._caption`) or steam
  (emphasis). Diagram annotations are glacier or ember, never abyss (2.3:1).
- On a **cream** card, every piece of type is frost-slate ink. Ember, glacier and steam are fills
  and outlines only.
- Abyss is a cold depth/shape color. On void it is a thin diagram line (the phase diagram, the
  wash), never a word.

---

## 2. Card accent assignment — 10 cards, no two adjacent share an accent

Strict 4-cycle over `{glacier, ember, steam, abyss}`, truncated to however many cards the
alignment yields. Adjacent cards therefore never repeat an accent (frost-slate ink and bone-cream
paper are structural, not accents, so they never enter the cycle).

| # | Card id | Register | Accent | Character |
|---|---|---|---|---|
| 1 | `hook_burning_ice` | void | glacier `#A8D8E8` | flat, pointing at the world |
| 2 | `world_size` | void | abyss `#2E3E60` (wash) + glacier planet | awed, hands up |
| 3 | `hook_no_sense` | cream | steam (top face) + ember (drip/pool read) | shrugging, zigzag |
| 4 | `pressure_and_heat` | void | glacier (crush) + ember (heat) | shielding eyes, worried |
| 5 | `no_choice` | cream | ink lines + frost wash, steam smudge band | pointing, skeptical |
| 6 | `supercritical` | void | steam (no-seam planet) + ember dashed ring | pointing, flat |
| 7 | `burning_torch` | cream | ember sea + glacier ice crests | awed, hands up |
| 8 | `losing_mass` | void | glacier (planet) + abyss/frost ribbons | shrugging, zigzag |
| 9 | `glowing_tail` | void | ember (tail) + glacier (planet) | standing, flat |
| 10 | `closing_impossible` | void | ember (tail) + steam/ember star | hands down, deadpan-grim |

Every beat carries a small diagram label or stamp beside its subject, and every one of them adds a
fact the caption does not — `CRUSH`/`HEAT` (beat 4), `SUPERCRITICAL`/`NO SEAM` (6), `ONE NEPTUNE`
(2), `SHIP` (7), `H + He` / `LEAVING NOW.` (8), `HYDROGEN + HELIUM` (10). No stamp restates its
caption; an earlier beat-10 stamp reading `BURNING ITS ICE` over the caption `BURNING ITS ICE.
QUIETLY. FOREVER.` was cut for exactly that reason.

Adjacency audit (accent family in order): glacier, abyss, steam, glacier+ember, steam, steam+ember,
ember+glacier, glacier+abyss, ember, ember. The dominant family never runs the same colour twice in
a row except where a card is deliberately two-tone (4, 7, 9), and even then the *secondary* differs.

**Character coverage (CLAUDE.md §6).** The stickman appears in **10 of 10** beats — far above the
one-per-segment minimum — with a distinct (pose, expression) per beat: pointing/flat, hands_up/awed,
shrugged/zigzag, shielding/worried, pointing/skeptical, pointing/flat, hands_up/awed,
shrugged/zigzag, standing/flat, hands_down/deadpan_grim. Every beat is drawn through
`C._draw_stickman(img, card, theme)`, so the pose/expression/position come from the schedule, not
from the renderer. Theme is `'dark'` (cream on space) on the seven void cards and `'light'` (dark on
cream) on the three cream cards.

---

## 3. Emissive treatment — the star and the burning

**The star (`_star`) — the one legal gradient.** A star is emissive, so `C._radial_core` (3-stop,
white → ember → deep amber) is the segment's only gradient. It is drawn on `pressure_and_heat` and
`closing_impossible`. Glow is kept low (`glow=0.42`) and a single hand-wobbled open arc carries the
rest. Two perfect concentric circles were tried first and read as a targeting reticle, so the halo is
now one painterly arc, not geometry.

**The burning planet (`_ice_planet`) — never a gradient.** Per STYLE_CANON §3 / PALETTE denylist, a
planet is not "emissive": it gets a flat glacier fill, a thick ink keyline, **three** wide flattened
latitude bands (glacier body, abyss/steam bands), a flat steam lit-crescent, and clipped stipple
grain. The `melt` parameter (0..1) flattens and fades the bands toward the equator — `melt=1.0` is
the supercritical card's **no seam**, `melt=0.6` the half-melted tail cards. Three bands (not five)
on purpose: a five-band set at these radii reads as a spiral/bullseye target.

**The escaping gas and the tail.** Thin tapered ribbons and nested flat bands in abyss/frost/ember
at low alpha, plus a few flat ember grains hugging the limb. Never a gradient, never a wide
rect-scatter (an early wide stipple read as confetti in the void).

**Glow layering.** `C.add_glow` is always drawn BEFORE the body it belongs to. Added on top, the
halo hazes across the disc and reads as a murky shadow rather than light escaping from it — this was
visible on both `glowing_tail` and `closing_impossible` before the order was reversed.

**The character's submersion (beat 7).** The character stands waist-deep in the ember sea, because
the card's point is that he cannot stand on it. A foreground wave is drawn OVER him after
`_finish` — an ember fill (no outline, so no ink verticals cut the caption row) plus one open ink
stroke along the waterline. This is what stops the library's merged leg strokes reading as a solid
black post. The caption is re-laid on top of the wave afterwards.

**Never gradient (explicit denylist).** The planet on every card. The pressure arrows and the
heat arrows. The gas ribbons and the tail. The phase-diagram lines and the smudge band. The ice
cube. The burning-ice sea and its crests. The ship. The void field except the starfield backdrop
built into `void_backdrop`. The title strip and the floating caption. The stickman, all of him,
every pose and expression. Any card-level wash or vignette.

---

## 4. Type sizes — the locked `type.py` set, verbatim

No new sizes. `work/lib/type.py` is the measured reference realization; use its constants
(`HEADER_PX`, `CAPTION_PX`, `LABEL_PX`, `STAMP_PX`) and never a literal px value or a font file.

| Role | Size | Face | Stroke | Color on this segment |
|---|---|---|---|---|
| Header — "Gliese 436 b" | `HEADER_PX` (48) | `comicbd.ttf` bold, caps | 3px ink | frost-slate on the bone-cream strip |
| Hero word (one per card) | 58–72 px, clamped by `C.hero_word` | `comicbd.ttf` bold, caps | 3px ink | ember / glacier / abyss on art |
| Floating caption | `CAPTION_PX` (28) | `comicbd.ttf` bold, caps | 3px keyline | ember on deep; frost-slate on cream |
| Planet label / diagram stamp | `STAMP_PX` (15, drawn via `_tiny` at 18–20) | `comic.ttf` regular | none | glacier or ember on deep; frost-slate on cream |

Every hero word goes through `C.hero_word`, which clamps the string inside the frame *including*
the 3px keyline and keeps it off the title strip and the caption band. A hero word must NOT restate
the caption — each card's hero adds a fact the caption does not say.

Consolas is retired from the type path; the family is Comic Sans Bold (headers/captions/heroes) +
Comic Sans (labels/stamps) only.

---

## 5. Files this spec lands in

- `work/segments/gliese436b/_cards.py` — `MY_PAL` (the 6 colors above) + one renderer per beat id
  in `script.json`, exposed via a module-level `RENDERERS` dict and merged by `register()`.
- `work/segments/gliese436b/_frames_*.py` (future) — the card table keyed by beat id.
- `work/lib/palette.py` — `get_segment_palette(7)` is intentionally NOT added here; this segment
  carries `MY_PAL` in its own module per the segment-local palette convention, so a change here
  cannot bleed into segments 1–6 or 8–12.