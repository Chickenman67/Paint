# CHANNEL_BIBLE.md

*The operating manual for this channel. Paste this into a brand-new session and it should
be enough to build the next film correctly, without rediscovering anything the hard way.*

This is a **hand-drawn "secret bunkers" explainer** in the *Paint Explainer* lineage: a
narrated, roughly 14-minute film across nine chapters, every frame generated with Pillow
from primitives we draw ourselves, scored against a real published video used purely as a
style/pacing benchmark.

Everything here was earned. Where a rule exists, the *why* follows it, because the *why*
is the only thing that stops a future session from "optimising" the rule away. If you find
a rule you disagree with, read its incident history before changing it.

**Document status.** Written 2026-10-08, after blind-critic round 4 scored 9/18. Sections
marked `KNOWN DEFECT` describe live, unfixed bugs — those are the work-list, not history.

---

## 0. The two rules that override everything else

These were added by the user after watching the film and are now the highest-priority
constraints in the project. They override any conflicting technical preference below.

### RULE 1 — Text visibility and contrast

> Text must be highly visible and never blend into the background.
>
> **BANNED:** text with a black outline whose interior is gray or muted.
> **REQUIRED:** high-contrast, vibrant interior fill that reads against *any* background.

**Why this is a hard rule and not a preference.** The audience is a human watching at
normal speed while a narrator talks. Text is the one thing they *must* be able to read, and
it is the easiest thing to make illegible, because a caption that looks correct in the
source file can end up sitting on the same value as whatever it happens to land on at
render time. The narrator says the phrase; if the eye cannot find the words in the ~1.5s
they are on screen, the beat is lost forever.

**How it is enforced.** `scene_common.caption()` runs a resolver (`_legible_fill`) that
refuses a gray/near-black fill and recolours it. The paper *keyline* under the glyphs is
what actually carries contrast against a busy background — see §7.

### RULE 2 — Composition, de-cluttering, human perspective

> **BANNED:** overcrowded scenes, cluttered backgrounds, and too many competing visual
> elements that distort the narrative.
>
> **THE HUMAN AUDIENCE FILTER:** before passing any scene, evaluate it through the shoes of
> an average human viewer. If a scene is sensory overload, or cannot be parsed in **two
> seconds**, it **fails**. Simplify the background and elements immediately.

**Why.** An AI can hold an entire frame in mind. A human cannot. When six elements compete
for the same two seconds of attention, the viewer does not see all six — they see none of
them, and they stop following. We are not being judged on information density. We are being
judged on whether a person can tell, at a glance, what is happening.

**How it is applied.** Every frame gets the two-second test during composition review, and
the blind critic's loss pattern (§11) independently confirms it: our losses are dominated by
over-population, not by missing detail.

**The loop-save rule.** After any builder/critic check where a fix was made, append the
lesson to §14 (Lesson log). Show the updated section so the user can verify it is being
tracked. Keep the entry to a few lines — a rule that costs a turn per scene will get
skipped or gamed, which is exactly how the "capped gate list truncates the work-list"
failure (§10) happened.

---

## 1. Hard constraints

These are not negotiable and they are not stylistic preferences. Breaking any of them
breaks the project.

1. **Free, local tools only.** Pillow (PIL) + numpy for drawing and measurement;
   `chatterbox` for TTS; `ffmpeg`/`ffprobe` for mux and assembly; `yt-dlp` for the
   one-time reference download. **No new pip installs.** No paid tools, no API keys.
2. **No copyrighted assets. The repo is public.** Nothing we ship may be copied, traced,
   recoloured, or derived from the reference. Public-domain / CC0 external imagery is the
   only external source permitted, which is how the user's "use outside sources as
   references for your drawings" is honoured without breaking this rule.
3. **The reference is a benchmark, not a source.** We download it once so the critic can
   compare style and pacing. We never transcribe, paraphrase or quote its script, never
   download and recolour its frames, and never clone its character. The bible documents
   *technique*, never *content*.
4. **The builder firewall.** Scene builders never open `work/ref2/` or `measure/refscan/`.
   The reference is the critic's domain. This is what protects rule 3 — a builder that can
   see the reference will unconsciously drift toward it.
5. **Renders are sequential.** One chapter at a time. Concurrent renders have killed this
   box with memory pressure more than once.
6. **The 5-round cap is enforced as written.** When a segment reaches the cap without a
   blind win, we ship the best of the five and flag it for human review. We never raise
   the cap to chase a close round. (The user has ruled on this explicitly.)
7. **Ultracode / Workflow is on** for substantive tasks. Token cost is not a constraint.
   The exception: anything requiring image judgment stays in the main loop — see below.

### Environment constraints that will bite you

- **Vision works in the main loop ONLY.** Subagents on this setup cannot see images. So all
  image-level judgment — "does this frame read?", "is this caption legible?" — must happen
  in the orchestrator. Do not delegate art defects to a subagent; you cannot verify its
  claim. (Verified: model overrides fail on routing, not vision.)
- **Renders must be sequential**, per rule 5.
- **Tool-input corruption is a recurring harness fault on this setup.** Throughout long
  sessions the harness intermittently appends or duplicates a tail of the tool argument,
  which makes `Read` drop `file_path` and makes `Bash`/`PowerShell`/`Glob`/`Agent` fail JSON
  parsing. One workflow verify agent died of it. The recovery is to **resend the call
  unchanged — it clears within a few attempts.** Do not lower your standard, skip a
  verification, or conclude the tool is broken permanently. This is a harness fault, not a
  signal about your work. Prefer short, single-field calls when it is acting up.

---

## 2. Pipeline map

End-to-end, in order. Each stage names the module that runs it.

1. **Script / beats** — each chapter has `work3/segments/<chapter>/beats.json`: an ordered
   list of beats, each with an `id`, a `start`/`end` in seconds, and a `line` (the exact
   phrase the narrator says for that beat). Written by hand, ~165 WPM.
2. **Narration** — chatterbox TTS renders one WAV per chapter at 24 kHz mono 16-bit. The
   audio is fitted to the beat clock (pacing solve, §3).
3. **Scene / frames** — `work3/lib/<chapter>2_scene.py` builds a scene object: a list of
   elements, each with a draw function, a time window (`at`/`until`), and an optional
   motion track. `engine3.render_frame(scene, t)` rasterises a frame at time `t`.
4. **Segment video** — frames are encoded to a silent MP4, then muxed with the narration
   WAV.
5. **Gates** — the readability / coverage / population gates render frames and measure
   pixels (§10). They are report-and-judge, not pass/fail wizards.
6. **Assembly** — the nine segments plus black bridges are concatenated; audio is
   re-encoded (§12).
7. **Blind critic** — paired frames, ours vs the reference at matched chapter fractions,
   labels stripped three different ways, judged blind (§11).

**Shippable art lives in `<chapter>2_scene.py`, not `<chapter>_scene.py`.** `SC.scene_mod(chapter)`
resolves the 2-module. This wiring bug produced **three separate wrong-build incidents** —
the critic scored a build that was not in the film. Use `SC.scene_mod()`; never spell the
module name yourself.

---

## 3. Script & pacing

- **Target ~165 WPM.** This matches the reference's pacing and was measured, not guessed.
- **One digestible phrase per beat.** Never spoil: do not put a block of text on a frame
  before the narrator has said it. Text appears *when its phrase is spoken*.
- **Text on roughly every second or third beat.** A text-free beat is the common case. Do
  not put text on every beat — it gives the eye no rest and it robs the text of impact.
- **Solve the pacing gap first.** Gaps between beats *add* time, so the speech must be
  *faster* than the target WPM to hit a fixed total. Pick the gap you want first, then
  derive the speech rate from it. Do not set the speech rate first and discover you are
  2s long at the end.
- **The runtime is deliberately SHORTER than the reference** (~820s vs the reference's
  ~875s) and the user has explicitly forbidden padding the scripts to close the gap. Do
  not "fix" this. A short runtime is the intended outcome of cutting per-card.

---

## 4. Narration audio

- **chatterbox** TTS, per chapter: 24 kHz, mono, 16-bit PCM WAV.
- **atempo for fitting.** `atempo` factor **f < 1 SLOWS the audio down**; inverting the sign
  ships a plausible-looking 2×-too-fast render. Verify direction before trusting it.
- **Word timings → beats.json.** The narration's phrase boundaries drive when each beat's
  text and animation appear. The beat clock (`BeatClock.at(beat_id)`, `.duration`) is the
  single source of timing truth; cards are scheduled from it, never from predicted word
  counts.
- **Known TTS failure:** chatterbox **duplicates the tail of long chunks** and mangles short
  phrases. The fix is **smaller chunks**, not a rate change. Do not respond by speeding up
  or slowing down the voice.
- **Do not measure the reference's voice from its audio.** The reference track is narration
  *plus music*; its spectral centroid and syllable rate measure the music, not the voice.

---

## 5. Visual style: registers, paint, and figure/ground

### Two registers

Every frame is in one of two registers and the rules differ:

- **Paint register (interiors, exteriors, daylight).** Paper-toned backgrounds, warm
  palettes, painterly tooth, dark ink outlines, the character drawn in **dark** ink.
- **Space / night register.** Dark backgrounds, light accents, the character drawn in
  **CREAM** so it does not vanish into the background.

**The register trap.** Several measurement axes (`dark_mask_fraction`, `muted_fraction`)
give misleading readings in one register or the other. The trustworthy axes are
`ink_fraction` and `v_centroid`. Calibrate any threshold per register, never globally.

### Paint and tooth

- Painterly **tooth** (the paper-tooth texture) is what makes a frame read as *made*. It is
  subtle at ship size — judge texture at **1280×720**, never magnified. A 3× crop shows
  texture a real frame does not (same trap as thumbnails, opposite cause).
- **KNOWN DEFECT — light fills have no tooth calibration.** `tooth_w = VALUE_FINE +
  DARK*(1.22 - luma/255)` gives a cream wall (luma ≈ 210) only ~1.9 levels of tooth, which
  is invisible at ship size. Light fills therefore read as soft out-of-focus gradients
  instead of paint. **This film is mostly light/cream fills**, so the majority of beats land
  in that regime — it is the mechanical cause of the "smooth, blurry, stock-render" look
  that lost the blind critic. Two remedies have been tried and both failed; do not attempt a
  third without reading the failure notes first. This is the highest-value open fix in the
  project.
- **The pigment / `tile_std` metric is INVERTED for quality.** It measures edge density. The
  highest-pigment frame in the film was a flat-vector mockup; a painterly frame scored
  lower. **Never rank frames by it.** A metric jump on a *worse* frame means the metric was
  gamed.
- Texture must never substitute for figure/ground. A textured field is not a subject.

### Figure/ground — the dominant failure

The recurring art defect is **not** missing detail or wrong facts. It is that the subject
does not separate from its background, so the eye lands nowhere. See §8.

---

## 6. The character system

A single recurring stickman presenter appears throughout. He is the audience surrogate: he
reacts the way the viewer is supposed to react.

- **Canonical proportions**, with proportion constants defined once. Do not redraw the
  figure per beat.
- **Head-rim stroke scales with head radius, not body stroke.** This single clamp is what
  makes the face legible; getting it wrong produces a "bandit mask".
- **The mouth does all the work.** Two dot eyes that never change; the mouth *shape* carries
  the expression (flat = deadpan, downturned arc = scared, wide oval = awed, smirk = wry,
  zigzag = uncomfortable). There is a mouth-shape table and an expression inventory; use
  them, do not invent faces.
- **Poses need a real elbow.** Arms drawn at equal-y, or anchored on the spine, read as
  scarecrows. Worse: a **7-degree elbow bend still reads as a single stroke** — elbow
  existence is not elbow visibility. The *angle* is what shows, so judge poses at ship size,
  not in the source.
- **Crop in, do not place on.** A close-up must **crop into the frame** so the face fills
  it. Insetting the character in dead space reads as set dressing and loses the beat.
- **When you resize a figure, check its neighbours.** Raising his height grows his whole
  footprint; he collides with display numerals and runs his arms off the frame edge.
  Render at full res after every size bump.
- **No motion layer may move layout.** Motion transforms apply to the element *tile*, never
  the whole frame. A transform on a rasterized frame once shipped backwards text and a
  crooked title strip.

### KNOWN DEFECTS — character

- `draw_character` accepts `head_fill` and `scale_x` and **silently ignores both**. A caller
  that passes `head_fill` gets nothing. (Verify before relying on either kwarg.)
- The determinism comment is wrong: the wobble seed does **not** use the pose name, so two
  poses with the same integer seed wobble identically. Pose separation is the caller's job
  via distinct seeds.
- The review contact sheet omits two expressions that exist in the library, and the mouth
  table implements shapes no expression uses — the inventories have drifted apart.
- Several chapters each restate their own "cream" value with no shared constant and no test.
- There is **no minimum-scale guard**: at a very small height the head rim degenerates into
  the bandit mask again. Nothing prevents it.
- There is **no collision check** between figure ink and caption ink; avoidance is currently
  hand arithmetic per beat.
- There is **no expression-coverage check** per chapter, even though character presence was
  a measured cause of several blind losses.

---

## 7. Type & captions

*(Carries RULE 1 from §0.)*

- **The keyline is the contrast, not the fill.** For ink-on-paper text, the paper keyline
  under the glyphs is what survives a crossing background — not a brighter fill, and not a
  halo. Flag a caption only when the fill is effectively the keyline colour *and* that
  colour sits near the background. A naive contrast-ratio gate will flag perfectly readable
  keylined captions.
- **A grey guard swallows the page ink.** A "reject low-saturation dark fill" test also
  matches the page ink and will silently recolour every day-card caption. Exempt the page
  ink explicitly.
- **A keyline scaled with font size fills the counters at large type.** Hold the canon band,
  then go sublinear above it.
- **A median background cannot see a caption straddling two values.** Test the fill against
  **both** clusters behind the glyphs; a median matches one half and passes black-on-black.
- **Ring-sample the label background in the full render.** Removing the element to sample its
  background also deletes the panel it painted.
- **Clamp captions inside the frame.** A per-frame clamp is load-bearing; captions have
  shipped clipped at the bottom and top in real chapters.
- **Type scale is locked once and never drifts.** Drift is invisible beat-to-beat and
  obvious across a full watch.

### KNOWN DEFECTS — type

- **The never-grey mandate is not enforced for labels painted inside shapes.** Only
  `scene_common.caption()` runs the grey refusal. A label drawn directly inside a
  `shape`/`bg`/`subject` draw call — which is where most labels in these chapters actually
  live — bypasses the resolver and can be authored gray, or authored the same value as its
  own keyline. This is the single biggest hole under RULE 1.
- The grey guard's exemption tests one ink value while the real fill/keyline constant is
  pure black, so passing the pure-black constant would be silently recoloured.
- **Two different INK and two different PAPER constants coexist** with no comment
  reconciling them; a newcomer will not know which is the page ink.
- **No gate verifies the type scale has not drifted between chapters.**
- The fit/clip gate isolates only whole text elements, so an in-card label that overflows
  its shape is not covered.
- A font loader on one path has no fallback and will raise if its font files are missing,
  while a sibling loader degrades gracefully. Inconsistent failure modes.

---

## 8. Composition & human readability

*(Carries RULE 2 from §0.)*

- **One idea per beat.** If a frame has two ideas, it is two beats.
- **Frame-fill: the subject must dominate.** The recurring defect is a subject that is *too
  small in a wide empty field*. Scale the dominant subject until it owns the frame, let
  supporting geometry (orbits, belts, walls) run off the side edges so the frame admits the
  system is bigger than the picture, and **crop a secondary body at a frame edge** rather
  than parking it inside. The reference fills the frame and crops at the edge; a centred
  small subject in a large empty field is the tell.
- **Never jam a sign or label into a corner** where it collides with the title band or a
  caption. Corner-jamming has shipped real collisions (a sign breaking a chapter title, a
  label overflowing an edge).
- **Crowding beats art.** The blind critic's losses overwhelmingly trace to us packing
  *more* into a frame than the reference did. Fix crowding before fixing art.

### The two loss clusters (confirmed at full res, blind round 4)

The nine losing frames fall into two diseases, and both reduce to *"the eye does not know
where to look in two seconds"*:

- **Cluster A — figure/ground failure.** We paint tone; the subject does not separate or
  does not dominate. Example: a satellite rendered thumb-sized in a vast washed-out field,
  with no character, no text, and no contrast.
- **Cluster B — over-population + illegible pseudo-detail + stray artifacts.** Too many
  competing elements, plus: hard-edged stray rectangles, stray diagonal strokes, stray edge
  slivers, panels of fake glyphs standing in for text, heavy leader bars colliding with
  captions. Example: an amorphous blob under a scribed grid, a grid of fake "7" glyphs, a
  stray blue diagonal, a stray white edge sliver, a heavy labelled bar, and a caption
  crowding the blob — six competing elements and no focal point.

A recurring sub-cause of Cluster B is the **smooth/blurred hero object**: a photoreal-looking
soft-shaded sphere pasted onto a hand-drawn card. It reads as a stock render, not as paint.
That is the visible face of the light-fill tooth defect (§5).
---

## 9. Motion and beat staging

The film's dominant state is **still-with-cuts**. That is correct and matches the reference.

- **Compare cadence at a common sample fps.** At our native rate we look still and the
  reference looks animated; at a common rate the reference is ~8% motion and we were ~44%.
  **Default to still-with-cuts.** Add motion only as a short accent on the beat that earns it.
- **A stage wrapper is not a stage conversion.** Stage *counts* do not predict conversion.
  Only the rendered per-onset frame difference does.
- **Never move the layout with a motion layer.** Transforms apply to the element tile only.
- **Clamp hero words against the stroke.** The outline sits outside the glyphs, so clamping
  to the advance width still clips.
- **The breath is a visual event.** Put a small visual change where the narrator pauses.
- **A gap in a beat is silent time, not dead air.** If a card outlives its phrase the viewer
  is looking at a finished idea; cut or fill it.

---

## 10. Gates and measurement methodology

This is the highest-value non-art section. Gates in this project have repeatedly been wrong
in *both* directions, and each rule below exists because the opposite behaviour shipped a bad
build or hid a real one.

- **A gate must render frames and measure pixels, never scan source.** A source scan that
  looked for a caption call was green on 37 real defects, because the caption was painted by
  a different call than the one being scanned.
- **A blank tile is a harness defect until proved otherwise.** On the primitive audit, all
  four "this primitive draws nothing" reports were rig bugs and zero were real art bugs: a
  near-white sheet background hid light fills; a name-keyed argument table missing `base_y`
  anchored structures at the frame top; the same table missing `top`/`bot` gave both 360 so
  a "row" had zero height; `s` was mapped to 1.0 when it is a pixel half-size, so a sensor
  rendered as a 2px box. A blank canvas and an absent drawing are pixel-identical.
- **When synthesising a missing argument, put unknown coordinates mid-frame (360) and
  unknown bands at genuinely different heights.** A generic fallback of a near-zero value is
  the worst choice: it draws the primitive off-canvas, and off-canvas is indistinguishable
  from missing.
- **Calibrate thresholds from eye-confirmed cases, never from intuition.** WCAG 3.0 flagged
  the most legible title in the film. A pixel gate flagged 749 stars as low-contrast text.
- **A guard that skips real defects is worse than no guard.** A "skip dark cards" branch hid a
  real defect in one chapter. Use a spatial median and test deviation in both directions.
- **A uniformity exemption cannot tell a fill from a solid stroke.** A backdrop-uniformity
  exemption forgave a full-width door beam. Verify the raw count, not the gated verdict.
- **Verify a remedy does not trip the gate that flags it.** A shared title lintel fixed the
  contrast and its own seam then tripped the intrusion gate. Make the backdrop uniform rather
  than widening the exemption.
- **A capped gate list truncates your work-list.** Printing 6 of 15 beats beside a correct
  count reads as a clean bill. Have builders re-measure the baseline themselves.
- **A median background cannot see a caption straddle.** The median matches one half of a
  two-value background and passes black-on-black. Test the fill against both clusters.
- **A gate control can be silently overridden.** An authored fill was replaced at frame time,
  reproducing the positive case. Read the output for evidence the input survived.
- **Ring-sample in the full render.** Removing the element to sample its background also
  deletes the panel it painted.
- **The keyline is the contrast, not the fill.** Flag only when fill is effectively the
  keyline colour *and* that colour sits near the background. A 4.5:1 ratio gate flags
  perfectly readable keylined captions.
- **A grey guard swallows the page ink.** A "reject low-saturation dark fill" test also
  matches the page ink and silently recolours every day-card caption. Exempt it explicitly.
- **Trustworthy axes:** `ink_fraction` and `v_centroid`. `dark_mask_fraction` and
  `muted_fraction` are register traps that lie.
- **Absolute ink does not map to quality.** A sparse frame can be a legitimate wide and a
  dense frame can be the frame-fill target. High ink with many live elements is the goal.
- **Measure MISSING versus STALL, not art onsets.** Otherwise every legitimate
  caption-refresh hold reads as a coverage gap.
- **Render at full res after every figure resize.** A taller character collides with display
  numerals and runs his arms off-frame.
- **An in-card `draw_title` overprints the persistent title strip**, because the engine draws
  the scene title last. That produces an illegible double title.
- **Gates are report-and-judge.** Most of these probes deliberately have no pass/fail verdict,
  because the judgment is a visual act and belongs in the main loop.

---

## 11. The blind critic

The critic is the only thing standing between us and shipping a worse film, so its
hygiene is non-negotiable.

- **Pair on a normalized fraction of each chapter, never on absolute timestamps.** Our film
  and the reference differ in length and the drift accumulates chapter by chapter, so by the
  last chapter an absolute offset is off by most of a segment.
- **RECORD THE LETTER, NEVER THE SIDE.** This is the rule that keeps getting broken. In round
  2 every per-pair letter was sound and the prose written around them was **inverted on 2 of
  18**, which sent a fix pass at nine segments to strip defects that were the *reference's*
  choices, and would have missed the two genuine losses entirely. Write a bare letter per
  pair. If a note needs to say "the reference," store a content description and resolve it
  after the reveal.
- **Blinding the pixels is not enough; blind the attribution.** Three leak vectors, all three
  have hit us: **pixels** (the chapter title is *drawn in the frame*, so a neutral filename
  does nothing), **filenames** (drive the side by a persisted per-pair coin flip so the same
  letter is not always the same side), and **the printed mapping** (the key is never printed
  before judging).
- **Mask the title band on both sides.** It is 72px, not 96px: 96 ate the top of our own
  captions and manufactured a defect that was entirely self-inflicted.
- **Fresh context per round.** The same critic must not see two rounds in a row, and the
  builder must not judge its own work.
- **Default to "ref wins" under uncertainty.** Praise is not useful.
- **Confirm every named gap on the full-res frame before you act on it.** A thumbnail read
  once invented a "missing character" gap that did not exist.

### Score history

| round | score |
|---|---|
| 1 | 1/12 |
| 2 | 3/18 |
| 4 | **9/18** |

Round 4 per chapter: pinegap 0/2, area51 2/2, tomb 0/2, room39 1/2, mezhgorye 2/2,
cheyenne 2/2, svalbard 1/2, fortknox 0/2, vatican 1/2.

**The three chapters at 0/2 are pinegap, tomb and fortknox.** They are the work-list. The
diagnosis for all three is in §8.

---

## 12. Assembly and post-production

- **Re-encode the audio; only video may be stream-copied.** With `-c copy` on both streams,
  every input's audio starts at PTS 0 and is not rebased onto a running timeline. The
  symptom is deceptive: `nb_frames` is correct while the reported duration is nearly double,
  so nothing looks obviously broken. Use `-c:v copy -c:a aac`.
- **Bridges must carry an audio stream.** A video-only bridge mixes badly into the concat.
  Build them with a silent audio source at the same rate and channel layout as the segments.
- **Check video and audio durations separately.** `format=duration` reports only the longest
  stream and will not catch a desync.
- **Back up the assembly before every fix pass.**
- **Signal completion by file freshness, not by a log line.** A killed process's log looks
  exactly like a finished one. Watch the output file's mtime.
- **Render sequentially.** See §1.

---

## 13. Process and failure modes

- **The builder/critic loop.** Build, then judge blind, then fix the named gap. The round
  cap is enforced as written; ship and flag rather than raise it.
- **Subagents stall before a large write** and announce a write that never lands. Instruct
  explicit incremental writes and verify with a directory listing *yourself*.
- **A stalled builder leaves a stub that still parses.** Check for the real function and its
  return, not just that the file compiles.
- **Art defects are the orchestrator's job**, because subagents cannot see images and you
  cannot verify a claim you cannot check.
- **The pigment metric is inverted for quality** and edge density is not texture.
- **Judge art at full resolution** (a thumbnail invented a gap) and **judge texture at ship
  size** (a magnified crop invented the opposite). Same trap, opposite cause.
- **The reference's audio mix is narration plus music**, so its voice metrics measure the
  music.
- **A large metric jump on a worse frame means the metric was gamed**, not that the frame
  improved.
- **Tool-input corruption is a harness fault, never a reason to lower a standard.** See §1.

---

## 14. Lesson log

*Appended by the loop-save rule after every builder/critic check that produced a fix.*

- **2026-10-08 — blind round 4 scored 9/18** (from 3/18). The three chapters at 0/2 are
  pinegap, tomb and fortknox. Full-res confirmation of the losing frames shows two diseases:
  **Cluster A** figure/ground failure (we paint tone, the subject does not separate or
  dominate) and **Cluster B** over-population with illegible pseudo-detail and stray
  artifacts (stray rectangles, stray diagonals, stray edge slivers, fake-glyph panels, heavy
  leader bars colliding with captions). Both reduce to "the eye does not know where to look
  in two seconds", which is the user's human-audience rule restated as an art defect. A
  recurring sub-cause is the smooth/blurred hero object, which is the visible face of the
  light-fill tooth calibration gap in §5.
- **2026-10-08 — the never-grey text rule is only enforced on captions, not on labels painted
  inside shapes.** Every label drawn inside a shape/background/subject draw call bypasses the
  resolver. This is the largest open hole under the user's text-visibility rule and should be
  the first fix of the next round.
