You are fixing unreadable chapter titles in ONE scene file of a bunkers explainer
video. Work only in the file named below.

## The defect

The persistent chapter title ("<Title>") is drawn by the engine LAST on every
frame, and its fill is hardcoded near-black (v2draw._wobble_glyph fill=T.INK).
That reads fine on a light/paper card and is INVISIBLE on a dark/night card.
`_coverage_gate.title_contrast(chapter)` reports every beat where the title
fails to read (WCAG < 2.0 against its background).

## The fix (already proven on pinegap — copy this exactly)

1. `scene_common.py` now exports `title_backdrop(tile, seed, col=(r,g,b))`.
   It paints ONE uniform low-texture course across the title band (y=0..86) so
   the near-black title reads against it, plus faint masonry joints strictly
   BELOW the band. It must be drawn AFTER the card's background fill and BEFORE
   the card's art, so the art stays on top.

2. In each FAILING card's draw function, add ONE line right after the
   background fill(s) (after `paper_overlay` is fine), before any art:

       SC.title_backdrop(tile, <UNIQUE_SEED>, col=(R, G, B))

   Pick `<R,G,B>` to suit the chapter's night palette — a desaturated mid-tone
   that is clearly lighter than the card but still reads as "night". pinegap
   used (96, 104, 124). Look at the chapter's existing NIGHT/dark palette
   constants and choose a value in the same family, lightened. Keep it a single
   flat mid-tone: do NOT make it very light (that would look like a UI bar) and
   do NOT use a value that varies within the band.

3. Add near the top of the file (after TITLE is defined):

       TITLE_BACKDROP = (10, 73)

   This tells the intrusion gate that rows 10..73 carry a deliberate backdrop.
   It only forgives rows that are uniform end to end, so it cannot hide art.

4. Import: the file already does `import scene_common as SC`.

## Rules

- Only touch the FAILING cards listed below. Do NOT add a backdrop to cards that
  already pass (light/paper cards must stay clean).
- One backdrop per failing card. If several failing beats share one card (a card
  can cover beats i..j-1), add it ONCE to that card's draw.
- Give each card a DISTINCT seed (use the seed already in that card, +1000, or
  the card's own number) so the fills differ frame to frame.
- Do not change any other art, layout, caption, or beat.

## Verify before you finish

From the `lib` directory run:

    PYTHONUNBUFFERED=1 python _verify_one.py <chapter>

It prints `contrast=[...]` and `intrusions=[...]`. BOTH must be empty lists.
If contrast is non-empty you missed a card. If intrusions is non-empty your
backdrop value is too varied inside the band — flatten it (the gate measures
within-row variation; a single flat colour always passes).

Iterate until both are `[]`.

## Report back

One line: the contrast/intrusion result after your fix, and how many cards you
added a backdrop to.

## Your chapter

Chapter name: {CHAPTER}
File: {FILE}   (in the same directory)
Failing beats (add a backdrop to the card that covers each): {BEATS}
Current TITLE constant: {TITLE}
Dark/night palette constants in the file (grep for NIGHT/DARK/SHADOW/DEEP/etc): {PALETTE}