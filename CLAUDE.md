# Guantlet2 — Paint-Explainer Video Build

A ~15-minute YouTube explainer on 12 "most disturbing exoplanets," built in the visual style of *The Paint Explainer*'s "The Most Disturbing Planets Ever Found." Reference: `work/ref_full.mp4` (916.3s, 1280×720).

This file is the working brief for any future re-build, polish pass, or re-orchestration. Read it before touching the visuals. It documents what was actually built, why, where it failed, and what to do differently next time.

---

## 1. The hard constraints (do not relax these)

1. **No paid tools. No API keys. No copyrighted assets.** The whole pipeline must run on free, local software and self-generated content.
2. **Same script, Same artwork.** Same topic, same genre, same hand-drawn aesthetic — but the narration text, the planet portraits, the stickman, the captions, and the audio are all our own. We do not transcribe, paraphrase, or quote the reference. We do not download its frames and recolor them. We do not clone its character.
3. **The reference is a benchmark, not a source.** We download it once with yt-dlp so the orchestrator can compare style fidelity and pacing, and then we forget about it as a creative input.
4. **Free tools only:** `yt-dlp`, `ffmpeg`/`ffprobe`, `MS Paint` / `Paint.NET` / `MyPaint`, `Pillow` (Python PIL), `numpy`, optional `sox`/`Audacity`, optional `chatterbox` TTS. No Kokoro, no ElevenLabs, no Midjourney, no DALL·E.
5. **Break the work into the smallest judgeable piece and run a builder + a separate critic (with fresh context, no shared memory) on each piece.** The critic compares ours to the *same timestamp* in the reference **with labels stripped** and says which is better, naming the single biggest remaining gap. Praise is not useful — the critic must be harsh. Loop on each piece until the critic picks ours blind. Do not stop before that.
6. **One-character pipeline.** There is a single recurring stickman presenter. Every segment must use him in at least one beat. More on this in §6 — this is where the reference beat us hardest.

---

## 2. Stack and roles

| Stage | Tool | Role |
|---|---|---|
| Reference download | `yt-dlp` | Pull the reference once, store under `work/ref_full.mp4`. Per-chapter transcripts and audio come from this. |
| Reference analysis | `ffprobe`, `ffmpeg` | Get duration, fps, sample rate, per-chapter timestamps. |
| Per-segment script | handwritten by orchestrator | The 12 narrator scripts. ~190–213 wpm to match reference pacing. Original wording. |
| TTS | **chatterbox** (replacing Kokoro, see §3) | Voice synthesis per segment, 24 kHz WAV, ~210 wpm, natural micro-pauses. |
| Source artwork | `MyPaint` / `MS Paint` / `Paint.NET` | Hand-drawn wobbly outlines, flat fills, limited palette. PNGs at 1280×720. |
| Card composition | `Pillow` (Python) | Beat-by-beat card composition, type layout, cross-fade sequencing, frame-by-frame animation. |
| Type | `consolab.ttf` (Consolas Bold) + `consola.ttf` (Consolas Regular) | Both available system-wide on Windows. One type family — never mix. |
| Audio/video mux | `ffmpeg` | Concat, cross-fade, mux narration with visuals, export per-segment MP4. |
| Final concat | `ffmpeg -f concat -c copy` | Concatenate the 12 winning segments. |
| Orchestration | `Workflow` tool with builder + critic subagents | Each segment is its own builder→critic loop. |
| Live progress | `progress/index.html` polling `progress/state.json` | Public-visible status page. |

**Kokoro is OUT, chatterbox is IN.** See §3.

---

## 3. TTS: why we are switching to chatterbox

The original build used Kokoro with the `am_liam` voice. It worked — segments came in around 200–210 wpm and the timbre is warm — but two issues pushed us to chatterbox:

1. **No native prosody control.** Kokoro reads punctuation and that's about it. The reference has audible *small breaths between beats* and a slight rise-and-fall that signals "next thought coming." Kokoro flattens those cues. You have to fake them with silences inserted by hand, which throws off beat timing.
2. **Monotone in the low-energy beats.** On sentences like "The planet just sits there. Cooling." Kokoro's Liam rushes the second sentence. The reference's narrator slows down — a deliberate pacing choice that signals menace.

Chatterbox supports the things we need:

- **Per-sentence pacing parameters** so we can mark "slow this one" without re-generating the whole file.
- **Pause tokens** (`<break time="0.4s"/>` style) that survive the WAV rather than getting faked in post.
- **Better prosody on short declaratives** — the "the planet just sits there" beat reads as ominous instead of rushed.

The migration steps when we re-build:
1. Swap the TTS script import: `from kokoro import KPipeline` → `import chatterbox` (or whatever the local wrapper is).
2. Keep the segment-by-segment WAV pipeline: one WAV per segment, sample rate 24 kHz mono, 16-bit PCM.
3. Keep the post-TTS step that **fingerprints the WAV word-timings** (we use a forced-aligner pass to get per-word onset times) — this drives beat timing. See §5.
4. The hand-tuning for "*small breaths between beats*" moves from "insert silence in Audacity" to "pass a pause token to chatterbox."

---

## 4. Visual style — what we were trying to hit

> **READ `work/STYLE_CANON.md` FIRST.** It is the measured, canonical spec and it
> **overrides** several numbers in this section. It was produced by measuring frames
> extracted directly from `work/ref_full.mp4` and reading them with vision. The rules
> that changed:
> - **Font is a rounded casual hand, not Consolas.** Headers/captions = `comicbd.ttf`
>   (Comic Sans Bold), planet labels = `comic.ttf`. The "Consolas only" rule below is
>   **retired** — Consolas is a monospace typewriter face and was our single largest
>   style mismatch for six rounds.
> - **Outlines are ~6 px, not 2-3 px.** Measured median on the reference is 6 px for
>   large shapes. The "2-3 px" below made our figures read as wires. Use 5-8 px big,
>   3-4 detail, 1-2 fine.
> - **Line quality is smooth hand curves with LOW-frequency wobble**, not per-vertex
>   jitter on straight polylines. The "no bezier curves" below is wrong; see
>   `work/lib/ink.py`.
> - **The character is drawn CREAM on dark/space backgrounds** and dark on light
>   backgrounds. Ours was hardcoded black, so it vanished into every space card. See
>   the theme system in `work/lib/stickman.py`.
> - **There is no caption band** — captions float on the art. The three-band template
>   in §7 is a simplification, not the reference.
>
> Everything below is retained for history/continuity but where it conflicts with
> `work/STYLE_CANON.md`, the canon wins.

The Paint Explainer look is not just "crude on purpose." It is a set of specific decisions. The reference follows them; we followed some and missed others.

### What we did right

- **Wobbly outlines, no anti-aliasing.** Outlines are drawn as 2-3px black strokes with hand-jittered vertices. No bezier curves, no smoothing passes, no Gaussian blur on the linework.
- **Flat fills, no gradients on shapes.** Cards and figures use solid color regions. We let *background* and *scaled-up planet portraits* have radial gradients in a few cases (KELT-9b) — that was a mistake, see §8.
- **Limited 4–6 color palette per segment.** Each planet gets its own palette so the eye registers "new segment" without an explicit title card.
- **Hand-lettered headers on the intro card of each segment.** A wobbly "KELT-9b" stamped across the top of the intro frame. The reference does this. We did too.
- **Cross-fades between cards within a segment.** Reference uses 0.4-0.8s cross-fades. We copied that. **It turned out to be too long for our density**, see §8.

### What we got wrong — the reference beat us on these

- **The stickman character.** Reference has a single named stickman who appears in nearly every segment with a *different* facial expression and pose per beat. We do not have him at all. This is the single biggest visual gap. See §6 — that gets its own section because the user explicitly flagged it.
- **Layout discipline.** Reference uses a strict "one idea per card" rule. The cross-fade is between two cards, and they don't overlap mid-sentence. We crammed 2-3 ideas per card to fit 12 planets into 15 minutes, and the cross-fades stack cards mid-sentence, which the brain reads as clutter.
- **Type scale consistency.** Reference uses one header size, one caption size, one hand-lettered accent — and sticks to it across the whole 15 minutes. We re-laid-out every card per segment, so the type scale drifts. Some cards use 36pt captions, others use 28pt. The drift is invisible beat-to-beat and obvious across a full watch.
- **Palette transitions between segments.** Reference's segment-to-segment transitions have a 0.3-0.5s bridge (a black screen, a blank card, a labeled "next" slate) so the new palette doesn't bleed into the old one. We cross-faded straight from one planet to the next, and the two palettes fight each other for the overlap window.
- **Character anchoring.** Reference's stickman is the audience surrogate — he's confused, he's scared, he makes little jokes. He is *the* way the viewer feels guided. We have no surrogate, so the viewer has to do all the emotional work themselves.

---

## 5. Audio-visual alignment — how to do it right

This is the second-hardest problem after the stickman, and the user's brief explicitly calls it out: visuals should "better align with the timing of the audio."

### The mistake we made

Our beat timing was driven by **script word counts divided by target wpm**. We pre-computed "this beat ends at t=14.7s" and laid out cards to that schedule, then ran the TTS and discovered the TTS came in 1-3s *longer* or *shorter* than predicted. The fix in the moment was "shift the next card by 0.4s and re-render," which means the visuals drifted out of phase with the actual audio by the end of every segment.

The result: at the start of a segment, a card lands precisely on the word it was drawn for. By the end, the card is 1.5-2s behind the audio, and you see card N while hearing the *next* sentence.

### How to do it right

1. **Generate the WAV first, get the word timings, then drive visuals from the timings.** Run a forced-aligner (Whisper word timestamps, Gentle, or wav2vec2 alignment) over the TTS output to get per-word onset times. Use those as ground truth. The card schedule is now *derived from the audio*, not predicted.
2. **One card = one phrase, not one beat.** A "beat" in our old system was a 12-15s block. In the new system, a card is a *phrase* — 2-5 seconds — and we cut to a new card every time there's a clause break in the audio. Visuals become a tighter score for the narration.
3. **Snap cuts, not cross-fades, for clause breaks.** When a sentence ends, hard-cut to the next card. Cross-fades only happen within a single thought (e.g., a camera-style "pan" across a still). This solves the "cluttered" problem *and* solves the audio-alignment problem simultaneously, because the cut is the alignment event.
4. **Reserve cross-fades for motion-only transitions** within a beat (e.g., the stickman walking from the left edge to the center). Cap those at 0.2s.
5. **The intro card and the first spoken word must land within 0.3s.** Reference nails this — the planet name is on screen exactly when the narrator says it. We were sometimes 1-2s late because the intro card was timed to the *segment start*, not to the *first word*.
6. **The "breath" is a visual event.** Reference has a small visual change at each narrator breath — a blink, a card color shift, a stickman head-tilt. We had no such event, so the breaths the user hears don't register visually. With chatterbox's pause tokens, we know exactly where the breaths are; we need a tiny visual event at each one.
7. **A 0.5s black frame at every segment boundary.** This is the palette bridge from §4. It also lets the audio engine emit its segment-end silence cleanly, which removes the "pop" you get when you concat segments with different ambient tones.

### The alignment file

For each segment, write `work/segments/<NAME>/alignment.json` with the shape:
```json
{
  "wav_path": "round_N_audio.wav",
  "duration_s": 74.03,
  "words": [
    {"t": 1.42, "w": "KELT", "end": 1.71},
    {"t": 1.71, "w": "9b.", "end": 2.05}
  ],
  "card_schedule": [
    {"card": "intro",   "start": 0.0,  "end": 2.4,  "type": "snap"},
    {"card": "world",   "start": 2.4,  "end": 13.7, "type": "hold", "motion": "shimmer"},
    {"card": "clock",   "start": 13.7, "end": 28.2, "type": "hold", "motion": "rotate"},
    ...
  ]
}
```
The builder reads this file and renders each card to start/end exactly, with motion only during the `hold` segments. No predicted timings. No drift.

---

## 6. The stickman — the gap the user flagged, and how to fix it

This is the biggest single visual gap vs the reference. The reference has a recurring stickman character who:
- Appears in nearly every segment (not all — the "data-graphic-only" beats are intentional)
- Has a *different* facial expression per beat (scared, confused, awed, deadpan, gleeful, skeptical)
- Has a *different* pose per beat (pointing, hands-up, shrugged, peeking, drawing on a chalkboard)
- Wears the same outfit every time so the audience can spot him
- Acts as the audience surrogate — he reacts the way the viewer is supposed to react

We have **none** of this. We are missing the emotional anchor of the whole show.

### What the stickman needs

- **A canonical pose sheet.** 5-7 reference frames showing him front, 3/4, profile, hands-up, pointing, shrugged, deadpan-scared, awed. Every artist (human or LLM) drawing him must work from this sheet. Without the sheet, every stickman is a different person.
- **A canonical face.** Two dots for eyes, a single-line mouth, no nose. The mouth shape is the *only* thing that changes between expressions: a flat line = deadpan, an upside-down arc = scared, a wide oval = awed, a smirk = wry, a zigzag = uncomfortable. Eyes don't change. The mouth does all the work.
- **A canonical outfit.** Black outline strokes, white-cream fill, single accent color for the shirt (e.g., red). No skin tone. No detail. The reference keeps it deliberately abstract.
- **A canonical body proportion.** 5-6 heads tall, stick limbs with hand-blob ends, a single oval for the head. Don't redraw the proportions per beat.
- **Per-segment reactions.** Each planet gets a small set of (expression, pose) pairs the stickman will cycle through during the segment. For KELT-9b, that's mostly "scared" and "shielding eyes." For WASP-17b, "wide-eyed" and "shrugged." For PSO J318.5-22, "alone-and-cold" (the candle beat).
- **Motion scripting.** When the stickman appears, give him a tiny 1-2s loop: a head-tilt, a step, a hand-wave, a glance. Reference never holds him still for more than ~2s without a micro-motion.

### How to build him in Pillow

- A `Stickman` class that takes `(expression, pose, position, scale)` and draws to a PIL image. Internally it has the proportions as constants and the expression as a mouth-shape lookup table.
- A small library of pre-drawn full-body poses as PNGs (transparent background, 720px tall, anchor at feet). Compose the stickman by pasting a body PNG and overlaying the right mouth/eyes for the expression.
- A `StickmanScene` that schedules appearance windows: when does he enter, when does he leave, what does he do while on screen.
- Render the stickman *after* the background card, *before* the captions, in the layer order. He's the bridge between the diagram and the viewer.

### The hard rule

**Every segment must have the stickman in at least one beat, and the segment's tone must be readable from his face alone.** If you can delete the narration and still get the emotional arc from the stickman shots, the segment is well-designed.

---

## 7. Card composition — what to do, what to avoid

### Card anatomy (use this template for every card)

> **SUPERSEDED by `work/STYLE_CANON.md` §1.** The reference has an **84 px** title
> strip (not 80) and a **full-bleed 636 px** illustration (not a 480 px band with side
> margins), and **no caption band at all** — narration floats on the art. The template
> below is retained for history. The canon's layout is what builders must render;
> `work/lib/type.py` already encodes it.

```
┌──────────────────────────────────────────┐
│ [HAND-LETTERED PLANET NAME]      [stamp] │ ← 80px header band
│                                          │
│                                          │
│            [CARD CONTENT]                │ ← 480px main area
│          (diagram / scene /              │   one idea only
│           stickman / planet)             │
│                                          │
│                                          │
│ [CAPTION: 1 short sentence, ≤60 chars]   │ ← 100px caption band
└──────────────────────────────────────────┘
```
- 1280×720 frame. Three vertical bands. No content escapes the bands.
- **One idea per card.** If you have two ideas, that's two cards. Use a snap cut between them.
- **Caption is ≤60 chars, ≤12 words, on a single line.** If it doesn't fit, it doesn't belong on this card.
- **No body text in the main area.** The main area is for diagrams, characters, planets, scenes. Words go in the header or the caption band, not floating in the middle.

### Type scale (lock this in once, never change it)

> **SUPERSEDED by `work/STYLE_CANON.md` §2** and encoded in `work/lib/type.py`:
> Header 48 px bold rounded hand (Comic Sans Bold) in the 84 px strip; planet label
> 32 px Comic Sans regular; floating caption 28 px Comic Sans Bold, yellow with 3 px
> ink outline; stamp 15 px. **Consolas is retired from the type path.** The numbers
> below (72/36/32/18 Consolas) are historical and must not be used.

- Header (hand-lettered planet name): 72pt, wobbly, black outline 3px, fill = segment accent color
- Stamps ("127b", "ARCHIVE"): 36pt, all-caps, 1px stroke, accent color
- Caption body: 32pt, Consolas Regular, no stroke, ink color
- Caption emphasis: 32pt, Consolas Bold, no stroke, ink color
- Tiny annotations (numbers on diagrams): 18pt, Consolas Regular, no stroke, ink-soft color

Mixing type families or sizes across segments is the drift problem from §4. Pick these five sizes, write them down, never deviate.

### Palette rules

> **FRAME-FILL RULE (from the 10/10 assembly critic, §9.4).** The dominant
> subject must be a real share of the frame — the two cards that originally lost
> had subjects under a fifth of the frame width and read as timid props in an
> empty field. Scale the subject up until it dominates, let supporting geometry
> (orbits, belts) exit the side edges so the frame admits the system is bigger
> than the picture, and **crop the secondary body at a frame edge** rather than
> parking it inside. The reference does exactly this. Note this is *not* a rule
> about shading: the reference uses smooth and even photoreal bodies, so smooth
> planet shading is not the tell.

- Each segment picks a 4-6 color palette: 1 ink, 1 cream/paper, 2-3 accents, 1 deep.
- Adjacent cards within a segment must use *different* accents. Same accent on two cards in a row = they read as one card with a glitch.
- Cross-segment palette bleed is solved by a 0.5s black bridge (see §5.7). No exceptions.
- Gradients are allowed only on **planet portraits that are themselves subjects** (e.g., the KELT-9b day-side glow). Never on cards, captions, or diagrams.

### Wobble rules

- Outlines are drawn as polylines with 1-2px vertex jitter. Use a deterministic seed per element (e.g., `random.seed(hash("kelt9b_intro"))`) so the same element wobbles the same way across re-renders.
- Stroke width: 3px for figure outlines, 2px for diagram outlines, 1px for fine details.
- No anti-aliasing on linework. PIL's `ImageDraw.line` is fine; do not pass through `ImageFilter.SMOOTH` on the linework layer.

---

## 8. The build loop — builder + critic, segment by segment

This is the orchestration pattern. It is the thing that made the project converge and is the most important thing to preserve in a rebuild.

### Per-segment loop (12 times, once per planet)

1. **Read the segment brief** (planet name, target wpm 190-213, target duration ~60-100s, key facts to convey, target emotions).
2. **Generate the WAV with chatterbox.** Save to `work/segments/<NAME>/round_N_audio.wav`.
3. **Force-align the WAV** to get per-word timings. Save `work/segments/<NAME>/round_N_alignment.json`.
4. **Build the visuals** (Pillow). Read the alignment file. Schedule cards to word-boundary snap points. Output silent MP4.
5. **Mux audio + visuals** to `work/segments/<NAME>/round_N.mp4`.
6. **Critic pass (fresh context, label-blind).** The critic receives:
   - Our segment at the same timestamps as the reference
   - The reference segment, with labels stripped
   - A prompt that asks: "Which one is better at being a Paint-Explainer-style video? Be brutal. Praise is not useful. Name the single biggest remaining gap on the loser. Default to 'ref wins' if uncertain."
   - The critic must return: a win/loss verdict, a per-criterion rating (style, layout, type, palette, audio-alignment, character), and the **one** biggest gap.
7. **If the critic says ref wins:** re-build. Update the visuals to close the named gap. Re-render. Loop.
8. **If the critic says ours wins:** lock the segment, mark it as `won` in `progress/state.json`, move to the next planet.
9. **Cap:** 5 rounds per segment. If 5 rounds pass without a win, ship the best of the 5 and flag for human review.

### Cross-segment rules

- The same critic agent does **not** see two segments in a row. Fresh subagent per round. This is the only way to keep the critic honest.
- The builder has access to all prior segment `alignment.json` and `round_*.py` files in the segments directory, so the type scale, palette rules, and stickman library stay consistent.
- The builder does **not** have access to the reference video, the reference transcript, or the reference frames. The reference is the critic's domain, not the builder's. This is the firewall that protects the "no copying" rule.

### The 12 segments in order

1. HD 188753 Ab — triple-star world, three-sun confusion
2. HD 80606 b — the whiplash planet, +500°C swings
3. PSR B1257+12 — pulsar planets, named after the undead
4. TrES-2b — the darkest exoplanet, darker than coal
5. WASP-17b — the back-orbiting gas giant, puffy as cork
6. WASP-127b — 200 mph winds, the spectrum bar
7. Gliese 436 b — burning ice under pressure
8. KOI-55 — the planet that survived being eaten
9. LTT 9779 b — the metallic hottest atmosphere
10. Fomalhaut b (Dagon) — the dust-shepherd, maybe
11. KELT-9b — hotter than most stars
12. PSO J318.5-22 — the rogue, alone, lit only by memory

### What "won" means for each segment

- Critic verdict: ours wins.
- Audio-visual alignment drift over the segment: <0.3s end-to-end.
- Stickman appears in ≥1 beat.
- Type scale is from the locked table in §7, no drift.
- Palette bridge (0.5s black) at the segment boundary.

---

## 9. Assembly and post-production

After all 12 segments have won:

1. **Cross-segment bridges.** Insert a 0.5s black frame between segments. Use ffmpeg concat with a bridge-list that contains both segment MP4s and the bridge files. The bridges also let the audio engine reset its ambient.
2. **Concat the 12 segments + 11 bridges.** `ffmpeg -f concat -safe 0 -i work/assembly/concat_list.txt -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 work/assembly/guantlet2_full.mp4`.
   **Do NOT use `-c copy` for both streams.** The earlier note that "`-c copy` is fine despite ffmpeg's non-monotonic-DTS warnings — ffmpeg auto-corrects" is **wrong for audio** and cost a full assembly. With stream copy, every input's audio starts at PTS 0 and is not rebased onto a running timeline, so the assembled audio timestamps come out wrong. The symptom is deceptive: `nb_frames` (the real sample count) is correct while the stream's *reported duration* is nearly double, so nothing looks obviously broken. Re-encode audio (`-c:a aac`); copy only video.
   **Also: the bridges must carry an audio stream.** They are built with `anullsrc` at 44100/stereo to match the segments; a video-only bridge mixes badly into the concat.
   `_assemble.py` now runs `verify_output()`, which checks video and audio durations against the plan separately and raises rather than shipping a desynced file. `format=duration` alone is not enough — it reports only the longest stream.
3. **Target duration: 916s ± 5s.** Reference is 916.3s. If we're outside that range, the per-segment audio alignment is drifting; fix the alignment files, not the concat.
4. **Final blind critic.** Same as the per-segment critic, but at the assembly level: 10 paired frames at matched timestamps across the 15 minutes, label-blind, fresh context, overall verdict. `_blind_critic_full.py` builds them on a **normalized-fraction timeline** (`our_t = frac * our_dur`, `ref_t = frac * ref_dur`) because absolute timestamps drift a full segment between our 867s and their 916s.
   **Current result: 10/10 ours.** Round 1 scored 8/10; the two losses were
   `gliese436b` and `fomalhautb`, both from the same defect, both fixed in round 2.
   The real defect is **subject too small / frame under-filled** — not smooth
   shading and not empty cards. The reference fills the frame and crops a body at
   the edge; our first build centred a small subject in a large empty field. Fix
   by scaling the dominant subject up (planet r62→126, star r46→150), widening the
   supporting geometry so it exits the side edges, and cropping the secondary body
   off an edge rather than parking it inside.
   **Do not judge by guessing which side is the reference.** See §10.11.
5. **Backup before any fix pass.** Always `Copy-Item guantlet2_full.mp4 guantlet2_full.pre-fixN.mp4` before re-running. We learned this the hard way.

---

## 10. Things we got wrong that a re-build should fix on day one

1. **No stickman.** The single biggest gap. §6 is the fix.
2. **Cross-fades too long.** 0.4-0.8s overlaps stack two cards mid-sentence. Fix: snap cuts at clause boundaries, 0.2s cross-fades only for within-beat motion.
3. **Drift between predicted and actual audio timing.** Cards rendered to predicted word counts, then TTS came in 1-3s off, then nothing was resynced. Fix: align WAVs to text first, then schedule cards from alignment.
4. **Type scale drift.** Per-segment layout picked its own sizes. Fix: lock the five sizes in §7, never deviate.
5. **Palette bleeding across segments.** Adjacent palettes fought each other. Fix: 0.5s black bridge between segments.
6. **One KELT-9b beat used a radial gradient on the planet portrait.** Reference uses flat fills even for planet subjects in most cases. Limit gradients to genuinely-emissive subjects (stars, lava), not the planets themselves.
7. **Crammed 2-3 ideas per card to fit 15 minutes.** Better: cut the scripts harder and let each card do one thing. The reference is generous with time per idea; we were stingy.
8. **No stickman at the moment of the planet's "fate" beat.** The most emotionally loaded second of each segment — "and then it gets worse" — should always have the stickman reacting, even if the diagram is the focus. The reference does this. We didn't.
9. **Debug header artifacts (SEGMENT 1 stamps, round-N tags) leaked into the build.** We had a debug-on-by-default mode that left stamps in the output. Fix: debug mode is opt-in, off by default in any render meant for the final assembly. Add a `--no-debug` flag to the frame-build CLI.
10. **Final assembly wasn't re-built after the last 3 segment fixes.** The 3 wins (WASP-127b round_8, PSO round_3, KELT-9b round_4) were newer than the full assembly file by hours. We re-concat'd manually after spotting it. Fix: the build pipeline should detect "wins newer than assembly" and trigger a rebuild automatically.
11. **We blinded the pixels but not the attribution, and it inverted every conclusion.** At the assembly critic, per-pair verdicts formed from looking at the two images are sound — that part worked (8/10 on the first pass). What failed was writing prose *around* them: while keeping notes we labelled each side by inferring from how it looked ("flat lavender sky and a jagged sun, that's the reference") and were **wrong in 5 of 10 pairs**. The 5 misattributed frames were ours, so the diagnosis came out exactly backwards — I was about to launch a fix pass across nine segments to strip "neon rainbow gradients" and "empty starfield cards" as defects when those are the *reference's* choices, and I would have missed the two genuine losses entirely. Fix: record a bare list of letters with no side names attached, run `--reveal`, map letters to sides, and only then write anything. If a note needs to say "the reference," store a content description instead and resolve it after the reveal. Blinding the pixels is not enough; blinding the *attribution* is the part that protects the result.

---

## 11. Quick reference: the one-page checklist

For a fresh build session:

- [ ] Lock the 5 type sizes in §7 into a shared module `work/lib/type.py`.
- [ ] Lock the stickman library in §6 into `work/lib/stickman.py` with the canonical proportions and the mouth-shape lookup.
- [ ] Lock the palette rules and bridge logic into `work/lib/transition.py`.
- [ ] Set up the chatterbox TTS wrapper at `work/lib/tts.py` with pause-token support.
- [ ] Set up the forced-aligner at `work/lib/align.py` producing per-word onset JSON.
- [ ] Build segment 1 (HD 188753 Ab) end-to-end. Render. Watch it. Re-watch with the reference muted, then with our audio muted. If the stickman doesn't carry the segment alone, rebuild.
- [ ] Run the critic. If it says "ref wins," identify the named gap and rebuild.
- [ ] Lock the segment, move to the next.
- [ ] After all 12: insert 11 bridges, concat, final critic, ship.

---

## 12. File map

```
Guantlet2/
├── CLAUDE.md                                  ← this file
├── progress/
│   ├── state.json                             ← per-segment status, last update, final critic verdict
│   └── index.html                             ← live progress page (polls state.json every 4s)
├── work/
│   ├── ref_full.mp4                           ← the reference (do not re-use as a creative input)
│   ├── segments/
│   │   ├── _summary.json                      ← reference per-chapter transcripts + wpm
│   │   ├── <NAME>/
│   │   │   ├── _frames_r<N>.py                ← Pillow frame generator
│   │   │   ├── _make_audio_r<N>.py            ← TTS generator
│   │   │   ├── round_<N>_audio.wav            ← generated narration
│   │   │   ├── round_<N>_silent.mp4           ← visuals only
│   │   │   ├── round_<N>.mp4                  ← muxed final per-segment
│   │   │   └── round_<N>_alignment.json       ← forced-alignment (new in re-build)
│   ├── assembly/
│   │   ├── concat_list.txt                    ← the 12 segments in order
│   │   ├── guantlet2_full.mp4                 ← the final 15:15 video
│   │   ├── guantlet2_full.pre-fixN.mp4        ← backups before each fix pass
│   │   ├── dbg_post_fixN/                     ← verification frames
│   │   └── dbg_blind_critic/{ours,ref}/       ← paired frames for the final critic
│   └── lib/                                   ← (new) shared modules: type, stickman, transition, tts, align
└── research/                                  ← reference analysis artifacts
```
