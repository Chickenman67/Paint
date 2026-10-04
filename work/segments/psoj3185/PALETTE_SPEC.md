# Segment 12 — PSO J318.5-22: palette + visual identity spec

Status: locked. Consumed by `work/segments/psoj3185/_cards.py` (the `MY_PAL` dict
at the top of that module is this document, in code).
Authority: `work/STYLE_CANON.md` (canonical, measured — it overrides `CLAUDE.md`
§4/§7 wherever they disagree), `work/lib/type.py` (the locked type scale),
`work/lib/stickman.py` (the character themes). No reference material was used to
produce this spec; the builder firewall in `CLAUDE.md` §8.8 holds.
Subject: PSO J318.5-22 — a rogue planet. No parent star, no system, no orbit. Cast
out of its system and falling through interstellar space forever, lit only by the
faint scattered light other stars leak at it from impossibly far away. Tone target:
the **quietest, emptiest, coldest** card set of the twelve. The register is
*loneliness*, not menace. Nothing in this segment may be bright, warm, or busy
except the two things that still remember a sun.

---

## 1. The palette (6 colors, locked)

Defined once, in `MY_PAL` at the top of `_cards.py`. `cardframe.PAL` belongs to
segment 3 (PSR B1257+12) and is **not** used for anything but its generic helpers
(`void_backdrop`, `_radial_core`, `add_glow`, `hero_word`, `_header`, `_caption`).

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| ink | Slate-black | `#13131A` | (17, 19, 26) | All linework (6px figure / 4px diagram / 2px fine), header glyph fill, **all type on cream cards** |
| paper | Cold bone | `#ECE9E0` | (236, 233, 224) | Title strip, every cream card's field, gauge faces, drawn instrument bodies |
| deep | Void | `#030409` | (3, 4, 9) | The space field on every `void` card |
| accent 1 | Pale bone | `#D0D8DE` | (208, 216, 222) | Linework and type **on the void**; limb rims, the caption keyline, starfield |
| accent 2 | Cold slate | `#4A5868` | (74, 88, 104) | Fills and washes only: dust bands, ground planes, orbit-ring fills, the mercury column, the ring's speck body |
| accent 3 | Ash | `#8A8F94` | (138, 143, 148) | The scattered-light wash. The neighbour in beat 2, the "grey smudge" in beat 6, the incoming beams in beat 5 |

Plus one more value that is a **body**, not a palette role, because it is used as
a fill on both registers and is not a card accent:

| Body | Hex | RGB | Where |
|---|---|---|---|
| rogue fill | `#3A3E46` | (58, 62, 70) | The planet as a lit-ish body (beats 8, 10) — a low-value neutral, darker than the paper and lighter than the void |
| rogue dark | `#1A1C23` | (26, 28, 35) | The planet as a moving silhouette against light (beats 3, 12) |
| rogue black | `#010103` | (1, 1, 3) | The planet as a hole, in the beats where it is *darker than the void around it* (beats 5, 9, 11, 13) |

### The one warm color, and why there is exactly one

| Role | Name | Hex | RGB | Where it is allowed |
|---|---|---|---|---|
| the only warm | Dusk amber | `#C68A4C` | (198, 138, 76) | The lost sun in beat 1 (emissive core), the glowing dust ring in beat 11 (emissive), the impact burst in beat 2, the pegged needle in beat 8, the tiny light-budget stub in beat 6, the ring's direction arrow in beat 10, the three strike-throughs in beat 7 |

Dusk amber is the segment's **only** warm hue, and it is rationed to a small,
enumerable set of subjects — never scattered as decoration. It appears on: the
lost sun in beat 1 (emissive core, plus its four ray strokes), the impact burst
in beat 2, the tiny light-budget stub in beat 6, the three strike-throughs and
the star icon in beat 7, the pegged needle in beat 8, the ring's direction
arrow in beat 10, and the glowing dust ring in beat 11 (emissive).

**Six of the thirteen cards carry no warm at all** — beats 3, 4, 5, 9, 12 and 13
are entirely cool, and they include the three loneliest frames in the segment
(the fall, the empty grid, the closing image). That is the discipline: the two
genuinely emissive bodies (beat 1's sun, beat 11's dust ring) are the two places
warm is brightest, and everything else borrows it only for a cancellation, a
needle, or a direction. There is no red, no orange, no `#00FFFF`-class value, and
no pure white anywhere on the frame — the brightest value in the segment is the
`#FFFFFF` center stop *inside* beat 1's sun at r < 0.25.

### The seventh color, deliberately excluded

The character's shirt red `#C83232` (`work/lib/stickman.py: SHIRT`). It is a
character global, identical across all twelve segments, and it is what makes him
findable. Because it is fixed, **no card accent in this segment may be red** —
which this palette satisfies with room to spare, since the nearest warm is amber
at H≈30° and the nearest cool is slate at H≈212°.

### Measured contrast (WCAG, against the values above)

Computed from the hex table with the standard sRGB relative-luminance formula —
not estimated. Re-run `lib/type.py`-independent luminance on these seven values
to reproduce; the verdicts are what bind, not the second decimal.

| Pair | Ratio | Verdict |
|---|---|---|
| Cold bone on Void | **16.87:1** | text OK — the title strip header |
| Slate-black on Cold bone | **15.23:1** | text OK — this is the cream-card type colour |
| Pale bone on Void | **14.20:1** | text OK — this is the void-card type colour |
| Dusk amber on Void | **6.97:1** | text OK, and it is the only warm type on the void |
| Ash on Void | **6.28:1** | legible, but used as a **fill** — the beams, not the type |
| Cold slate on Cold bone | **5.99:1** | passes even for small text, but slate is a **fill** role in this segment and is never used for type |
| Cold slate on Void | **2.82:1** | **fills and large shapes only — never a word** |
| Dusk amber on Cold bone | **2.42:1** | **forbidden — amber type never sits on cream** |
| Pale bone on Cold bone | **1.19:1** | **forbidden — bone type never sits on cream** |

Binding rules that fall out of that table:
- On a **void** card, captions are dusk amber (via `C._caption(dark_bg=True)`) and
  every diagram label is pale bone. Cold slate never carries a word on the void.
- On a **cream** card, every piece of type is slate-black. Bone, slate and amber
  are fills and outlines only.
- The header glyphs are **slate-black on the cold-bone strip**, never an accent.
  Two of the three accents are illegible on paper (2.0:1 and 1.1:1 above), so ink
  is the header's accent — the same resolution `lib/palette.py:HEADER_COLOR` and
  the reference measurement both reach.

---

## 2. The two registers, per beat

The register comes from `script.json`'s `register` field, and the renderer
mirrors it: `void` → `void_backdrop` + `C._header(paper_band=True)` +
`theme='dark'` character + `dark_bg=True` caption. `cream` → full-bleed paper +
`C._header(paper_band=False)` + `theme='light'` + `dark_bg=False`.

| # | Beat id | Register | Card field | Character |
|---|---|---|---|---|
| 1 | `hook_a_sun_you_know` | void | horizon + lost sun | flat / shielding_eyes |
| 2 | `ejection_neighbor_comes_too_close` | cream | two worlds, escape arc, boundary wall | oval / hands_up |
| 3 | `thrown_into_the_between` | void | motion streak + ly tick scale | — (pure data beat) |
| 4 | `no_star_to_orbit` | cream | dashed orbital grid, crossed-out centre | — (pure data beat) |
| 5 | `no_light_of_its_own` | void | black disc, four leaking stars | — (pure data beat) |
| 6 | `barely_enough_to_see` | cream | grey smudge, light-budget scale | frown / shielding_eyes |
| 7 | `what_rogue_means` | void | three crossed-out rows | flat / shrugged |
| 8 | `coldest_and_darkest` | cream | thermometer + darkness dial | — (pure data beat) |
| 9 | `less_than_darkness` | void | the limb, figure standing on it | oval / hands_up |
| 10 | `the_dust_ring` | cream | dust ring + calipers | — (pure data beat) |
| 11 | `a_suns_worth_of_wreckage` | void | glowing ring, unlit planet | — (pure data beat) |
| 12 | `it_passes_you` | cream | dotted trail, ridge, observatory | flat / shielding_eyes |
| 13 | `the_loneliest_thing_found` | void | one dark sphere, dust horizon | oval / hands_down |

Six void, six cream, alternating with one exception (7 void between two creams) —
so the two fields never sit adjacent for more than one beat, and the segment
crosses registers eight times. That alternation is load-bearing: it is what stops
thirteen lonely cards from reading as thirteen variations of the same black
rectangle.

### Character ink per register

| Register | Theme | Limb / head fill | Eyes + mouth ink | Shirt |
|---|---|---|---|---|
| `void` (beats 1, 3, 5, 7, 9, 11, 13) | `'dark'` | cream `#F5F0E1` (245, 240, 225) | near-black `#191920` | `#D64A4A` (214, 74, 74) |
| `cream` (beats 2, 4, 6, 8, 10, 12) | `'light'` | black strokes, white head | black | `#C83232` (200, 50, 50) |

**The character is light on the void.** `theme='dark'` on every void card is a
correctness rule, not a taste call (`STYLE_CANON.md` §4): a black figure on a
`#030409` field is invisible. Seven appearances, five distinct expressions, and
the two `flat` beats are deliberately different performances — beat 7 is a shrug,
beat 12 is a shade-the-eyes watch — so they do not read as the same frame.

---

## 3. Emissive treatment — the two legal gradients

A gradient is legal in this segment on exactly two subjects, both of them
emissive bodies: **beat 1's sun** and **beat 11's dust ring**. Both use the same
3-stop ramp, so the two "warm" things in the segment are visibly the same kind
of thing:

- r = 0.00 → `#FFFFFF`
- r = 0.55 → `#C68A4C` dusk amber
- r = 1.00 → `#5C3016` deep ember (92, 48, 22)

Beat 1 renders it with `C._radial_core(img, cx, cy, r, stops, glow=1.25)` — the
`glow` term is the soft **circular** halo `STYLE_CANON`'s round-2 addendum
requires; the halo mask gets a hard circular cutoff after the blur, so the paste
region never shows its corners as a faint box. Beat 11 builds its ring as 46
stacked, progressively wider and fainter elliptical bands on an RGBA layer, each
blurred and composited, which is the same falloff applied to an ellipse seen at
a shallow angle. A deterministic stipple is laid over both so they keep the
spray-paint grain instead of reading as a clean CG ramp.

**Never gradient — explicit denylist.** The rogue planet in *every* card, in
every register. The horizon in beat 1. The ground bands in beats 6, 12 and 13.
The dust washes in `_void_field`. The orbit grid in beat 4. The streaks, beams,
calipers, tick scales, dial faces, thermometer and every diagram. The title
strip and the caption. The stickman, all of him, every pose and expression.

The rogue is the reason that list is not negotiable: a body with no light on it
is a **flat fill**, and the moment it becomes a radial ramp it acquires a lit
side it has no business having. Beats 5, 9, 11 and 13 go further and make it
darker than the void around it, which is the beat's argument.

---

## 4. Type — the locked `lib/type.py` scale, verbatim

No new sizes. These five are the whole set; every one is read from `lib/type.py`
and none is hardcoded as a pixel value except through `T.load_font_at` for the
small diagram labels, which `STYLE_CANON` §2 permits as the regular face.

| Role | Size | Face | Stroke | Color on this segment |
|---|---|---|---|---|
| Header — "PSO J318.5-22" in the 84px strip | 48px | Comic Sans Bold | 3px | slate-black `#13131A` on cold bone |
| Planet label | 32px | Comic Sans regular | none | slate-black on paper |
| Caption — the floating narration | 28px | Comic Sans Bold | 3px | dusk amber `#C68A4C` on void; slate-black on cream |
| Hero phrase — one per card, via `C.hero_word` | 34–44px | Comic Sans Bold | 3px | pale bone or cold slate |
| Diagram label / stamp | 15–20px | Comic Sans regular | 0 or 1px | pale bone on void; slate-black on cream |

**Consolas is retired** (`STYLE_CANON` §2). `lib/palette.py` still carries the
Consolas-era comment headers, and `lib/title_band.py` still draws a Consolas
strip — neither is on this segment's render path, and `_cards.py` calls
`C._header`, which goes through `T.draw_header` (Comic Sans Bold).

### Layout and the annotation band

Layout A: 84px paper strip (rows 0..83), full-bleed art (rows 84..719), **no
caption band**. Every caption is drawn by the one call
`C._caption(img, card['caption'], 70, 652, dark_bg=...)`, which puts its glyph
box at **y 661..685**. That band is the reason for the rule every card in this
module follows:

> **No other type may finish below y ≈ 645, and nothing at all may start above
> y = 84.**

The self-test's `_text_guard` enforces both, plus off-frame in any direction,
plus no overlap with the caption — checked against the real glyph bboxes the
renderer produced. This is not theoretical: the previous version of this module
had an orbit-path label whose bbox ran to **y=733** on a 720-row card, a diagram
label whose top row sat at **y=74** — ten rows inside the title strip — and four
cards where a hardcoded label was stacked straight through the caption. None of
those is visible to a `size == (1280, 720)` assertion, so the frame generator's
own gate does not catch them.

### Hero phrases

One per card, only where the card needs one, always through `C.hero_word` so it
is clamped inside the frame *including* its 3px keyline (the `STYLE_CANON`
addendum: a hand-rolled clamp against `T._bbox`'s advance width ignores the
stroke and ships clipped glyphs). Beats 4 and 8 carry **no** hero: their phrases
restated the narration line verbatim, which the same addendum names as a defect
even when the placement is correct. The crossed-out centre (4) and the two pegged
instruments (8) already carry the idea.

---

## 5. Determinism

Every `K.wobble_points`, `K.draw_smooth`, `K.stipple`, `K.starfield` and
`random.Random` call in this module takes an explicit integer seed, and no global
`random` state is used anywhere. Re-rendering a card is byte-identical, which the
self-test now asserts on every beat rather than assuming.
