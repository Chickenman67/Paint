# STYLE_CANON — the corrected, measured Paint-Explainer spec

**Status:** canonical. Supersedes `work/ref/ref_style_spec.md` and the layout/type
sections of `CLAUDE.md` §4 and §7 wherever they disagree.

**How this was made.** Every number below was either (a) measured by script on frames
extracted directly from `work/ref_full.mp4`, or (b) read by eye off a verified
`ref_full.mp4` frame in the orchestrator (the only context in this harness with
vision). Where this file disagrees with the old spec or with CLAUDE.md, this file is
right and the reason is given. Provenance: `work/study/` (measurement scripts +
specimen sheets) and `work/ref/frame_*.png` (1 fps reference grabs).

Reference source (the benchmark, never a creative source): 916.376 s, 1280x720, 60 fps.

---

## 0. What the reference actually is (the two registers)

The style is NOT one look. It is two registers, and confusing them is our single
biggest recurring error.

**Register P — PAINT / SCENE register.** Used for anything with a ground, a landscape,
or the character. Flat fills, thick 4-8 px organic black outlines, layered flat
shadow-shapes inside objects, hand-wobbled curves, warm/earthy palettes. Example:
t=5 s (HD 188753 Ab, three suns over mauve mountains, character in a thinking pose).

**Register S — SPACE / OBJECT register.** Used for planets, suns, and the grid cards.
Smooth airbrushed radial gradients on emissive bodies, anti-aliased star dots, no
outline on the body, soft glow halo, painterly stipple/noise band at gradient seams.
Example: t=20 s (single red-to-yellow sun on a navy starfield).

Rules that fall out of this:
- Flat fill + thick outline is for **Register P** (and for Register S when the object is
  a *planet* with surface detail, which gets a soft banded gradient + contour linework
  but keeps a dark keyline).
- Smooth gradient + glow is for **emissive** bodies (suns, lava, fire) and for the
  **background** of space cards. A *planet* is not "emissive" in the gradient sense —
  it gets surface treatment.
- Our old round-6 critic wrongly called the reference's smooth sun "off-genre." It is
  the correct Register S. We were the ones mixing registers on the wrong cards.

---

## 1. LAYOUT — the frame skeleton

Frame is 1280x720. Two layouts, like the old spec, but the vertical metrics are
corrected by direct measurement.

### Layout P/A — the dominant card ("title strip + full-bleed art")

```
y 0    ┌───────────────────────────────────────┐
        │  TITLE STRIP — paper/cream fill,     │  ~84 px  (measured: near-white
        │  bold rounded caps, centered         │           rows 0..83)
y 84    ├───────────────────────────────────────┤  HARD edge, no border
        │                                       │
        │  ILLUSTRATION — FULL BLEED,          │  636 px
        │  left/right margin 0, no caption     │
        │  band. Captions float inside.        │
        │                                       │
y 720   └───────────────────────────────────────┘
```

CORRECTIONS to the old numbers:
- **Title strip is ~84 px**, NOT 39 px and NOT the CLAUDE.md §7 "80 px header with a
  480 px art area." Measured: the near-white band occupies rows 0..83 on a verified
  frame. The old spec's "39 px" measured a different, thinner segment intro; the
  CLAUDE.md "80 px" was accidentally right. Use **84**.
- **Illustration is full-bleed to both edges** (x=0..1280) and runs strip-bottom to
  frame-bottom (y=84..720). NOT a 480 px "main area" with side margins.
- **There is no dedicated caption band.** Narration text floats ON the illustration in
  the space the art leaves. The old 3-band template (80/480/100) is a simplification we
  invented, not the reference.

### Layout B — the grid card ("planet line-up")

Full-bleed 3 columns x 2 rows of dark rounded-rect cells on cream, each cell = a
painterly planet portrait; a cream label strip overlaps the bottom of each cell with
the planet name in the light casual hand. Used for the "all the planets" / re-cap beats.
(Verified at t=200 s.)

---

## 2. TYPE — the corrected type system

The reference uses **two** type treatments, not one family. (The old spec said "one
type family"; that is wrong and it is why our headers and labels read the same weight.)

| Role | Face | Size (px) | Weight | Case | Color |
|---|---|---|---|---|---|
| **Header** (title strip planet name) | rounded geometric sans | 44-52 cap | BOLD | ALL CAPS | ink (#000) on paper |
| **Planet label** (in-grid / on-planet) | casual hand, lighter | 28-34 | regular | Title-ish ("HD 80606 b", "TrES-2b") | ink on paper strip |
| **Caption** (floating narration) | rounded sans | 24-30 | bold | ALL CAPS | accent (yellow #F0E040) or paper, 3 px ink outline |
| **Stamp** (tiny diagram annotation) | rounded sans | 12-18 | regular | any | segment accent, thin ink outline |

**FONT SUBSTITUTION (free, local, Windows system fonts only):**
- Header + Caption  -> `comicbd.ttf`  (Comic Sans MS Bold)
- Planet label + Stamp -> `comic.ttf`  (Comic Sans MS)
- (Segoe Print `segoepr.ttf` is an acceptable alternate for the hand label, but its
  numerals are sloppier; Comic Sans Bold wins for the header.)

CORRECTION: we currently use **Consolas** (`consolab.ttf`/`consola.ttf`) for everything.
Consolas is a monospace typewriter face. The reference is a rounded casual hand. This
single swap is one of the largest readability/style wins available. Consolas must be
removed from the header/label/caption path entirely.

**Type-size lock (write these into `work/lib/type.py`, never deviate):**
- HEADER_PX = 48   (fits the 84 px strip; measured cap-height ~28-34, bbox ~44)
- LABEL_PX  = 32
- CAPTION_PX = 28  (with 3 px black outline, floating on the art)
- STAMP_PX  = 15

---

## 3. STROKE — the biggest measured gap (our #1 fix)

Measured on verified reference frames vs our round-6 output (median dark-run width,
`work/study/stroke_cmp.py`):

| | reference | ours (round 6) |
|---|---|---|
| object outline (ridge/limb) | **6 px median** (p90 ~17 for overlapping) | **3 px median** |

- **Large shape outlines (planets, mountains, character body, sun rim): 5-8 px.**
  Use 6 px as the default. This is the dominant visual signature of Register P.
- **Medium detail (contour lines on planets, small objects): 3-4 px.**
- **Fine (star specks, tick marks, stipple): 1-2 px.**

CORRECTION: the old spec's "outline stroke ~6-8 px measured, *visual* 2-3 px" is a
misreading — it folded wobble-doubling into a small number and then called the visual
result "2-3 px." Measured directly, the visual stroke on large shapes is **~6 px**.
CLAUDE.md §4's "2-3 px for figure outlines" is likewise wrong and is why our figures
look spindly and unfinished. The character at 6 px reads as a solid hand-drawn figure;
at 3 px it reads as a wire.

**Line quality.** Register P outlines are **smooth, hand-drawn curves** (gently
wobbling bezier-ish paths), not jittered polylines. CORRECTION: CLAUDE.md §4's
"wobbly polylines, no bezier curves" is wrong — the reference ridgelines are smooth
organic curves with low-frequency variation. Draw with smooth curves + a *small*
deterministic low-frequency wobble, not per-vertex 1-2 px jitter on straight segments.

---

## 4. THE CHARACTER (our recurring surrogate)

Design constraints (CLAUDE.md §1.2: do NOT clone the reference character). The
reference character is a "nervous nerd": round head, chunky glasses, eyebrows, detailed
mouth with tongue, ~4 heads tall. We must design our OWN, clearly distinct, but keep the
functional proofs.

**Our canonical character (locked):**
- Body: true stick figure, thin monoline limbs, small filled hand/foot blobs.
- Proportion: **4.0 heads tall** (total height / head height). Reference measures 4.0.
  (The old lib claimed HEADS_TALL=5.0; measured geometry of that lib is ~3.9. Use 4.0
  and derive geometry FROM this number, do not let a decorative constant lie.)
- Head: **round**, white fill. On **full-body** scale: flat white, no gradient. On
  **close-up**: allow a soft gray sphere shade (the reference does this at close range;
  verified on the t=256 close-up).
- Face: two dot eyes, expressive **brows**, and a **mouth that is the primary
  expression carrier** (per CLAUDE.md §6: flat=deadpan, down-arc=scared, wide oval=
  awed, smirk=wry, zigzag=uncomfortable, smile=warm, scream=shocked). Optional pink
  mouth interior for the big reactions.
- **NO glasses** — that is the reference's signature; we deliberately do not copy it.
- Signature: a single **accent shirt** (pick a per-segment accent; default a strong red
  #C83232) on EVERY appearance, so the audience has a constant to lock onto.

**CRITICAL — the character is LIGHT on dark backgrounds.** On space/register-S cards
the reference character is drawn with **cream/white limbs on a thin dark keyline** (see
t=256 close-up), not black strokes. Our character is always black, which disappears
against space. The character renderer must take a `theme` (light-on-dark vs dark-on-
light) and invert appropriately. This is a correctness bug, not a style nit.

**Scale and frequency.** Reference: ~6-10 character shots per segment at 1 fps, i.e.
roughly one every 8-10 s, in 11 of 12 segments. §6 hard rule (character in >=1 beat,
tone readable from the face) stays, but aim for the reference's density, not one lonely
figure.

**Framing varies** — full body most of the time, close-ups for the emotional peaks.
Never hold the same full-body framing for a whole segment.

---

## 5. MOTION — quantized, not tweened

Measured over the first 180 s at 4 fps (719 frame pairs): CUT 3.8%, FADE 6.1%,
HOLD 90.1%. In-card motion arrives as **discrete ~0.25 s steps** (one brush stroke
per step), NOT continuous interpolation.

- Cross-fades: **median 0.50 s**, range 0.25-0.75 s. (CLAUDE.md §4's "0.4-0.8 s" is
  close; use 0.5 s.)
- Hard snap cuts between cards/ideas.
- In-card animation (character bob, planet being drawn, orbit sweep) = a sequence of
  **0.25 s stamps**. Do not tween.

**Pacing law (card duration).** The old spec's motion analysis (correct instrument)
gives: median card 3.5 s, **bimodal** — short "data card" beats under 4 s plus long
"narrative hold" beats 9-42 s. Target the median ~3.5 s. Do NOT use a scene-score
cut histogram to measure this (it also catches the 0.25 s stamps and gives a
meaningless ~0.8 s "median"); measure real cuts at diff > 50.

---

## 6. SEGMENT BRIDGE — white, not black

CORRECTION to CLAUDE.md §5.7: the inter-segment bridge is a **WHITE** card, not black.
Sequence (measured, t=88-98 s):
1. ~1.0 s cross-fade to white,
2. ~2.25 s held blank white,
3. ~0.5 s cross-fade out, hard cut into the new segment's header+background together.
Total ~3.75 s. `work/lib/transition.py` already implements this correctly — keep it.

---

## 7. PALETTE

Each segment picks a discipline of ~5-6 colors: 1 ink, 1 paper, 2-3 accents, 1 deep.
Register P favors warm/earthy + one cool sky. Register S favors dark navy/black
background + 1-2 hot accents. Text picks the highest-contrast slot, ink always
available as the outline/keyline. Adjacent cards in a segment use different accents.

---

## 8. WHAT TO FIX IN OUR BUILD (priority order)

1. **Font: Consolas -> Comic Sans MS Bold (header/caption) + Comic Sans MS (label/stamp).**
   Single biggest readability + style win.
2. **Stroke weight: 3 px -> 6 px on all large outlines** (figures, planets, mountains,
   object rims). Our figures currently look like wires.
3. **Line quality: smooth hand curves, not jittered polylines** on Register P.
4. **Character theme: light-on-dark in space cards** (currently black-on-dark, i.e.
   invisible/muddy).
5. **Canonical character consistency:** ONE body build everywhere, accent shirt on
   every appearance, proportion actually 4.0 heads, and vary framing (full-body +
   close-up) instead of one static full-body for a whole segment.
6. **Title strip = 84 px, full-bleed 636 px art, no caption band.**
7. **Register discipline:** gradients/glow only for emissive + space backgrounds; flat
   fills + thick outlines for paint/scene. Don't airbrush a landscape; don't
   flat-fill a sun.

Everything above is builder-facing and must be encoded in `work/lib/` (type.py, a new
stroke/curve helper, stickman.py theme support) so no builder re-derives it.


---

## Addendum (2026-09-30, round-2 build) — emissive-body glow + small-planet rule

Two rules the round-2 build got wrong and the library now enforces in
`lib/cardframe.py`. Both were found by reading the rendered cards, not the prose.

**1. An emissive core needs a real halo, and the halo must be circular.**
The pulsar is the brightest object on every void card. A bare radial-gradient disc
reads as a small speck (this was the round-2 complaint). `_radial_core` now adds a
soft additive halo (`add_glow`) by default.

The non-obvious part: on a near-black sky, **any** nonzero additive contribution is
visible, so a square paste region shows its own corners as a faint box. The halo
mask therefore gets a hard circular cutoff (`ImageChops.multiply` with an ellipse
mask) after the blur — a value threshold is not enough, because bilinear upsampling
leaves a faint floor in the corners. The halo's *colour* must also be multiplied by
the mask, or you paste a solid rectangle.

The halo is built at quarter resolution and upscaled: a halo is a low-frequency
field, so this is visually identical and ~8x faster (finale card: 0.33s -> 0.04s).
That speed matters — the frame generator renders 91s x 30fps of stamps.

**2. Small planets get FEWER, FAINTER marbling bands.**
`space_body` scales band count, width and alpha down below r=30. At full strength a
small planet reads as a spiral/bullseye (a target), not a sphere. A small planet is a
smooth mottled ball; a large one can afford strata.

**3. In-card hero text is clamped.**
`hero_text()` clamps the size to caption scale, keeps the string inside a 48px frame
margin, and refuses to collide with the caption band. The round-2 build drew hero
words ("RUBBLE", "MOON-SIZE", "A NEUTRON STAR") at the 48px header scale, where they
shouted, ran off the right edge, or landed on top of the caption. One dominant phrase
per card, at caption scale, with a margin — nothing more.

---

## Addendum (2026-09-30, round-2 render) — the motion layer may not move the layout

The 0.25 s stamp motion operates on an ALREADY-RASTERIZED frame, and that frame
carries the layout: the paper title strip (rows 0..83) and the floating caption
(near row 652). Round 2 shipped two catastrophic, code-review-invisible bugs
because the motion transforms treated the raster as free to move:

- `_t_flip` mirrored the whole raster for `digit_flip`, so `name_just_digits`
  went out with EVERY glyph backwards — header, caption and all. Catastrophic.
- `_t_head_tilt` rotated the whole raster for `head_tilt_0.25s`, so
  `hook_not_alone` went out with a visibly CROOKED title strip and black wedges
  in two corners.

The rule, now enforced centrally in `lib/motion.py::_pin_layout`:

> Motion may vary LIGHT over the whole frame. It may only move GEOMETRY inside
> the safe art band (rows 84..612) and only HORIZONTALLY. After every transform
> the strip (rows 0..84) and the caption band (rows 612..720) are spliced back
> from the unmoved still, byte for byte.

Enforcement is centralised, not per-verb, because leaving it to each verb did not
work: a whole-frame brightness pulse is ALSO wrong on the protected bands. It
drags the cream strip toward white and back (the band visibly flickers), and the
strobe's 0.72 dim makes the amber caption unreadable. A viewer's anchor cannot
breathe. So the art is alive and the layout is welded.

**Any new motion verb must be checked against this**: it may only ever touch rows
84..612 horizontally, or change light. Never rotate, mirror, translate vertically,
or resize the raster. `apply_motion` re-pins the layout regardless, but a verb
that fights the pin will visibly tear at the band edge.

## Addendum (2026-09-30) — hero words must be placed by `hero_word`, never by hand

Every beat module grew its own hero-text helper, and each clamped against
`T._bbox`'s ADVANCE width — but `draw_outlined_text` draws a `stroke_width`
keyline OUTSIDE the glyphs, so the stroked text is wider and taller than the box
that was clamped. `hook_not_alone` shipped "A NEUTRON STAR" with its final R cut
off by the right edge; `how_two_years` shipped "IT CAME BACK." overlapping the
title strip.

`lib/cardframe.py::hero_word` is the single correct way to place a dominant
on-card phrase. It measures from the same call the renderer makes, clamps to the
frame INCLUDING the stroke, keeps y below the title strip, and auto-shrinks a long
phrase rather than letting it run off. Route every hero/banner phrase through it.

Corollary, from the same pass: a hero word that merely RESTATES the caption is a
defect even when it is placed correctly ("IT CAME BACK." over a caption ending
"...IT CAME BACK."; "IN AN AFTERNOON." over "...BY AFTERNOON."). One idea per
card: if the caption says it, the art does not also say it in type.

---

## Addendum (2026-09-30) — read directly off verified reference frames (t=205–271)

Read from `ref_full.mp4` frames at the segment-3 window, mapped in
`segments/psrb1257/critic_r2/ref_contact.png`. Three structural things the
reference does that our round-2 segment does NOT. These are style *principles*
to apply going forward, not assets to copy — the reference's stickman face,
its exact ring colours and any photographic portraits stay out of our build
per CLAUDE.md §1.2 ("we do not clone its character").

**1. The character is usually GROUNDED on a horizon, not floating.**
In roughly a third of the reference's character beats the stickman stands on a
wavy olive/dark-green GROUND BAND across the lower third of the frame, against a
plain dark sky — a paint-register scene, not a starfield. Our round-2 segment
puts the surrogate at `x=400, feet_y=680` on an undifferentiated starfield, so
he reads as pasted on rather than placed in a world. **For segments 4-12: any card
where the character is the subject rather than a scale figure should give him a
ground plane** (`K.draw_ground`, a flat band with a wobbled top edge). This is
the single largest remaining gap between our space cards and the reference's.

**2. Subject labels are placed ON or immediately BESIDE the thing they name.**
The reference stamps "Draugr", "Phobetor" and "Poltergeist" directly against
their planets, and stamps a word across the pulsar's face. So overlap between a
label and its subject is *authentic*, not a defect — what matters is that the type
is fully on-screen, has its keyline, and stays off the title strip and caption.
Do not over-correct by pushing every label into empty space; keep the label with
its subject and let `hero_word` guarantee it fits.

**3. The pulsar reads as concentric emission rings, not a plain ball.**
The reference's pulsar is a white-hot core inside cyan -> magenta -> pink
concentric rings with four soft diagonal light-spikes. Ours is a bone/amber
gradient orb with a thin amber limb ring: correct register (emissive core, legal
gradient) but visually plainer. Concentric emission shells and soft radial spikes
are generic astronomical-rendering conventions, not that video's character, so
they are fair to use — in OUR palette (amber/bone/violet), not theirs.

**What we already match, and should not "fix":** the cream title strip with a
rounded black heading, centred; planets as grey spheres with wavy white contour
strata (our `space_body` does exactly this); a pure-black starfield; and hard
snaps between one-idea cards.
