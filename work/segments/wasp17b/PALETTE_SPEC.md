# Segment 5 — WASP-17b: palette + visual identity spec

Status: locked. Consumed by `work/segments/wasp17b/_cards.py` (module-level
`MY_PAL`). No reference frames were used as a creative source (builder firewall,
CLAUDE.md §8). All drawing is on the free local Pillow stack in `work/lib/`.

Authority: `work/STYLE_CANON.md` (canonical, overrides CLAUDE.md §4/§7),
`work/lib/type.py` (locked type scale), `work/lib/ink.py` (locked stroke scale),
`work/lib/cardframe.py` (Layout A compositor).

Subject: an ultra-hot, ultra-puffy, **retrograde** gas giant — a world the size of
Jupiter made of almost nothing, spinning the wrong way around its star, clouds
stacked into a wall of weather, wind that never stops. Tone target: hostile heat
and weightlessness. The one idea per card is always about a *wrongness* — the
backwards spin, the near-emptiness, the heat — and the palette is built so the
hot beats (amber) and the empty/cold beats (teal) never sit on the same card.

---

## 1. The palette (6 colors + the character red, locked)

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Slate-black | `#14161C` | (20, 22, 28) | All linework (6px large / 4px detail / 2px fine / 1px hairline), header glyph fill on the paper strip, every glyph on a cream card |
| paper | Bone-cream | `#F2EAD6` | (242, 234, 214) | The 84px title strip; the full-bleed background of every `cream`-register card |
| deep | Void | `#07070E` | (7, 7, 14) | The starfield of every `void`-register card (a hair cooler/blacker than segment 3's `#05060B` so this segment's warm accents read hotter against it) |
| accent 1 | Signal amber | `#E8A33D` | (232, 163, 61) | The star and the temperature column, captions on `deep`, the hot accents (heat, collapse core) |
| accent 2 | X-ray bone | `#DCE6EC` | (220, 230, 236) | The gas giant's body and its storm strata, captions/labels on `deep`, the wind streamlines, the character |
| accent 3 | Cold teal | `#3E7C8C` | (62, 124, 140) | The wind ribbon, the "almost nothing / empty" wash, cool diagram fills — LARGE SHAPES ONLY, never a word |

**Seventh color, deliberately not an accent:** the character's shirt red `#C83232`
(`work/lib/stickman.py`, `SHIRT = (200, 50, 50)`), identical across all 12 segments.
Because it is a fixed global, **no card accent in this segment is red.** The
closest hot accent is amber, which is far enough from the shirt red (H 34 vs H 0)
that the character never dissolves into a card. Alert/warning color for cards is
amber, never red.

### Measured contrast (WCAG, against the values above)

| Pair | Ratio | Verdict |
|---|---|---|
| Bone-cream on Void | ~17:1 | text OK |
| X-ray bone on Void | ~15.7:1 | text OK |
| Signal amber on Void | ~9.0:1 | text OK |
| Slate-black on Bone-cream | ~15.1:1 | text OK |
| Cold teal on Void | ~4.6:1 | **fills and large shapes / diagram strokes only — never caption text** |
| Signal amber on Bone-cream | ~1.8:1 | **forbidden — amber type never sits on cream** |
| X-ray bone on Bone-cream | ~1.05:1 | **forbidden — bone type never sits on cream** |
| Cold teal on Bone-cream | ~4.1:1 | diagram shapes only, never 32px body text on cream |

Binding rules that fall out of that table:
- On a **void** card, every caption is amber (default) or bone (emphasis beats).
  Diagram annotations are bone at stamp size, never teal.
- On a **cream** card, every piece of text is slate-black. Amber, bone, and teal
  are fills and linework only.
- Teal is a shape color. It never carries a word.
- Header glyphs are filled **slate-black** on the cream title strip. The rule
  "header fill = segment accent" only holds when the accent is legible on cream,
  and neither amber nor teal is. `work/lib/cardframe.py::_header` already resolves
  this the same way (ink on paper), and the measured reference is black-on-white in
  the strip. Ink is this segment's header accent.

### Why no green / no neon
Highest chroma here is amber (H≈34°, S≈75%). Teal is desaturated to S≈40%, bone is
near-neutral. There is no pure green, no `#00FFFF`, no `#FF00FF` anywhere. The only
emissive gradient core in the segment is the host star (white → amber → a deep
red-brown limb), which is the one place a smooth gradient is legal.

---

## 2. Card accent assignment — 13 beats, no two adjacent share an accent

The assignment is a strict cycle over `{cream, bone, amber, teal}` seeded so that
the `register` field in `script.json` is respected (a `void` beat can only carry
bone/amber/teal as its *drawn* accent; a `cream` beat draws on the paper). Reading
the register as the accent family:

| # | Beat id | Register | Drawn accent |
|---|---|---|---|
| 1 | `backwards_hook` | void | bone (the giant) + bone hero |
| 2 | `everyone_else_turns` | cream | teal (orbit arrows) + amber star |
| 3 | `not_made_here` | void | amber (the incoming streak) + bone ghost |
| 4 | `wrong_way_explained` | cream | ink boxes, amber accents |
| 5 | `almost_nothing_there` | void | teal (the empty wash / balloon) + bone outline |
| 6 | `cork_density` | cream | ink cork + teal beam + bone planet |
| 7 | `should_have_collapsed` | void | amber (the hot core) + ink shell |
| 8 | `cloud_wall` | cream | teal bands + ink arrows |
| 9 | `endless_wind` | void | teal (the wind ribbon) + bone arrowheads |
| 10 | `dayside_1700` | cream | amber (the temperature column) + ink scale |
| 11 | `you_would_not` | void | bone (tiny planet) — deliberately almost empty |
| 12 | `three_wrongs` | cream | ink rules + amber ticks |
| 13 | `never_supposed_to_be_here` | void | bone hero + teal retrograde arrow |

Adjacency audit in order (drawn accents): bone→teal, teal→amber, amber→ink, ink→teal,
teal→ink, ink→amber, amber→teal, teal→teal(9), teal→amber, amber→bone, bone→ink, ink→bone.
The one repeat is teal(8)→teal(9), separated by a register change (cream → void) so
they read as different cards; every other boundary is distinct. Truncating the list
to however many beats the alignment actually yields keeps the invariant.

Constraint on top of the cycle:
- Beat 11 (`you_would_not`, the FATE beat) carries the stickman alone in a near-empty
  frame. It is bone-on-void so the cream character has maximum separation — per
  CLAUDE.md §10.8 the fate beat must carry him, and here it is literally the point.

**Palette bleed across the segment boundary:** the bridge is `lib/transition.py`
`make_white_card()` (pure `#FFFFFF`), shared assembly code for all 12 segments. Do not
retint it. The void palette therefore starts after a white card — a stronger reset
than a black bridge.

---

## 3. Emissive treatment — the host star only

The one genuinely emissive body in this segment is the host star. Gradients are
legal there and NOWHERE else.

**Host star (beat 2 `everyone_else_turns`, and as a small core on beats 7 and 10).**
3-stop radial gradient, no banding, via `lib/cardframe.py::_radial_core`:
- r = 0.00 → `#FFFFFF`
- r = 0.55 → `#E8A33D` (signal amber)
- r = 1.00 → a deep red-brown limb `#7A2E12`

`_radial_core` adds a soft circular halo automatically, which is what the
STYLE_CANON addendum requires for an emissive body.

**Never gradient (explicit denylist).** The gas giant, in every card, on every beat.
The orbit ellipses and their arrows. The wind streamlines. The cloud bands. The
temperature column and its squiggles. The coral/starfield dots. The title strip and
the floating caption. The stickman — all of him, every pose and expression. Any
card-level wash or vignette. A gradient on the planet got one of our earlier builds
shipped as a soft-fantasy halo instead of paint; the giant here is matte cloud-deck
and storm strata, so it takes flat fill plus stipple / `space_body` surface
treatment only. `cardframe.space_body()` (painterly, marbled, no black outline) is
the correct tool for the space giant; `texture.radial_gradient()` is not.

---

## 4. Type — the locked table, verbatim from `work/lib/type.py`

No new sizes. These five are the whole set for the segment. Consolas is retired.

| Role | Size | Face | Stroke | Color on this segment |
|---|---|---|---|---|
| Header — "WASP-17b" in the 84px strip | `HEADER_PX = 48` | `comicbd.ttf` bold, ALL CAPS | 3px ink | slate-black on the bone-cream strip |
| Planet label — on a grid/portrait | `LABEL_PX = 32` | `comic.ttf` regular, title-ish | none | slate-black on cream |
| Caption — the one floating line | `CAPTION_PX = 28` | `comicbd.ttf` bold, ALL CAPS | 3px ink keyline | amber on `deep`; slate-black on cream |
| Hero word — the one dominant phrase | 56–72px via `C.hero_word` (auto-shrinks) | `comicbd.ttf` bold | 3px ink keyline | bone or amber on `deep`; slate-black on cream |
| Stamp — diagram annotation ("1700 C", "WRONG WAY") | `STAMP_PX = 15` | `comic.ttf` regular | 1px | bone on `deep`; slate-black on cream. **Never teal** |

Every prominent on-card phrase is placed by `C.hero_word`, which measures the
stroked box (not the advance box) so a phrase can never run off the frame or ride up
into the title strip. Captions stay `<60` characters, `<=12` words, one line.

The narration is audio only. The **only** text that appears on a card is: the planet
name in the strip, the one floating caption, and small diagram labels/stamps. The
narration line is never printed.

---

## 5. Character in each register

- **void** cards → the character is CREAM. Rendered with `theme='dark'` (cream limbs,
  cream head, dark eyes, red shirt). Dark-on-light is WRONG in space.
- **cream** cards → the character is DARK INK. Rendered with `theme='light'` (black
  limbs, white head, red shirt).

He appears in 13 of 13 beats, so the segment's arc is readable from his face alone
(deadpan → uncomfortable → awed → deadpan → scared → uncomfortable → scared → awed →
uncomfortable → scared → scared → deadpan → awed). Poses are drawn only from the
canonical eight; expressions only from `MOUTHS`. Per-beat pose/expression/size/
position come from the scheduler's `card['stickman']` block and are not hardcoded
in the renderer.

---

## 6. Files this spec lands in

- `work/segments/wasp17b/_cards.py` — the 13 renderers (one per beat id), keyed by the
  beat `id` from `script.json`, exposed as the module-level `RENDERERS` dict, each
  `fn(card, planet) -> 1280x720 RGB Image`. It carries its own `MY_PAL` copy of §1 and
  does not rely on `cardframe.PAL` (which is segment 3's palette).
- `work/segments/wasp17b/PALETTE_SPEC.md` — this file.
