# BUILDER BRIEF — segment 3 (PSR B1257+12) card renderers

Read this file completely before writing any code. It is the whole contract.

## What you are producing

One Python module per beat: `work/segments/psrb1257/_cards_b<N>.py`, where `<N>` is
your beat number (1..6). Each module defines ONE renderer function per card in your
beat's JSON, plus a `RENDERERS` dict mapping card `id` -> function.

Renderer signature (exact):

```python
def render_<card_id>(card, planet="PSR B1257+12"):
    ...  # return a PIL.Image RGB, 1280x720
```

`card` is the schedule card dict (already parsed). You read `card['id']`,
`card['caption']`, `card['accent']`, `card['card_value']` ('void' or 'cream'),
`card.get('stickman')`, and the free-text `card['sketch']` field which describes
what to draw in detail. The sketch field is the AUTHORITATIVE art direction for
your card — follow it.

## Hard rules (violating any of these fails the build)

1. **NEVER import anything outside the free stack.** Only `PIL` (Pillow),
   `math`, `random`, and the project's own libs. No numpy-required paths, no
   downloads, no network.
2. **Only import from `lib.type`, `lib.ink`, `lib.stickman`, `lib.cardframe`.**
   Do NOT edit those files. Do not re-derive their constants.
3. **Layout A is mandatory.**
   - Rows 0..83 = the paper title strip (`T.HEADER_STRIP_BOTTOM` == 84).
   - Art fills rows 84..719 FULL BLEED (edge to edge, no side margins).
   - There is NO caption band. The caption floats ON the art.
   - Strip mode:
     - `card_value == 'void'`  -> `C._header(img, planet, paper_band=True)`
       (a visible cream band over dark art)
     - `card_value == 'cream'` -> `C._header(img, planet, paper_band=False)`
       (card is already full-bleed cream; header floats, no band edge)
   Call the helper; do not hand-roll the strip.
4. **Caption is mandatory on every card**, drawn with `C._caption(img, card['caption'], 70, 652, dark_bg=<True for void, False for cream>)`.
   Use exactly that call so every card in the segment has the caption in the same
   place and colour. Do not invent a caption position.
5. **Character.** If `card.get('stickman')` is truthy, draw it with
   `C._draw_stickman(img, card, theme='dark' if card_value=='void' else 'light')`.
   It reads x/y/height/pose/expression off the card. NEVER hardcode a pose,
   expression, size or position — the schedule owns all four, and the schedule is
   the alignment contract. Cards with `stickman: null` draw no character.
6. **Register discipline** — the single most important style rule:
   - **Register S (space/object)**: on `void` cards. Smooth airbrushed RADIAL
     GRADIENTS are legal **only on emissive bodies** (the pulsar core, a lit
     star) and on the starfield backdrop. Anti-aliased star dots. **NO thick
     black outline** on a space body. Painterly wavy contour bands on planets.
   - **Register P (paint/scene)**: on `cream` cards. Flat or painterly fills.
     Diagram shapes get THICK smooth organic outlines.
   - Gradients are **NEVER** legal on: the planets-as-subjects, orbit ellipses,
     the radiation wash, the starfield, the title strip, debris, or the character.
     (PALETTE_SPEC §3 denylist.) Getting this wrong is the #1 critic complaint.
7. **Outline weight**: 5-8 px (`K.OUTLINE`=6) for large shapes, 3-4 (`K.DETAIL`)
   for medium, 1-2 (`K.FINE`) for hairlines/stars. Never 2-3 px on a big shape.
8. **Line quality**: use `K.draw_smooth` / `K.draw_outline` for organic curves.
   These do smooth Catmull-Rom + LOW-frequency wobble. Do NOT hand-roll per-vertex
   random jitter, and do not draw raw straight polylines for organic silhouettes.
9. **Determinism**: every wobble/stipple/starfield call takes an explicit `seed=`.
   No `random.seed()` global state. Re-renders must be byte-identical.
10. **No text on the art except:** the header (via `C._header`), the caption (via
    `C._caption`), and small diagram annotations via `T.draw_stamp` / `T.draw_label`
    / `T.draw_caption` at small sizes. Never a big paragraph of body text.

## The library API you must use

```python
import lib.type as T          # fonts + text
import lib.ink  as K          # strokes, wobble, fills, starfield
import lib.stickman as S      # the character (only via C._draw_stickman)
import lib.cardframe as C     # backdrops, strip, caption, stickman helper
```

### `lib.type`
```
T.HEADER_STRIP_BOTTOM = 84 ; T.ART_TOP = 84 ; T.W = 1280 ; T.H = 720
T.draw_header(draw, text, ink_rgb=(r,g,b))            # bold rounded, in the strip
T.draw_caption(draw, text, xy, color_rgb=..., ink_rgb=..., )  # 28px bold, yellow default
T.draw_stamp(draw, text, xy, accent_rgb, ink_rgb=(0,0,0))     # 15px tiny annotation
T.draw_label(draw, text, xy, ink_rgb=(0,0,0), center_x=None)  # 32px planet label
T.load_font(size_px, bold=True/False)                 # if you truly need an off-scale size
```
Do NOT use Consolas or any monospace face. The locked family is already wired in
`T.load_font`; go through `T.load_font_at` for anything else.

### `lib.ink`
```
K.OUTLINE=6 ; K.DETAIL=4 ; K.FINE=2 ; K.HAIRLINE=1
K.draw_smooth(draw, points, fill=None, outline=INK, width=K.OUTLINE, seed=0, wobble=3.0, wavelength=90.0, closed=True)
K.draw_outline(draw, points, color=INK, width=..., closed=True, seed=0, wobble=2.0)
K.draw_disc(draw, cx, cy, r, fill=None, outline=INK, width=..., seed=0, wobble=3.0)
K.draw_ridge(draw, x0, x1, y_base, height, seed=0, fill=None, segments=5, outline=INK, width=..., roughness=0.35)
K.draw_ground(draw, x0, x1, y_top, y_bottom, fill, seed=0, width=..., roughness=4.0)
K.stipple(draw, x0, y0, x1, y1, color, seed=0, density=0.06, r=1, spread=1)
K.starfield(img, seed=0, n=90, x0=0, y0=0, x1=1280, y1=720, color=(255,255,255))
K.wobble_points(pts, seed=0, amount=3.0, wavelength=90.0)
```

### `lib.cardframe` — backdrops and helpers you should build on
```
C.PAL          # the locked palette dict: ink, paper, deep, amber, bone, violet, shirt
C.W, C.H       # 1280, 720

# Build a void/space card. Full-bleed gradient + starfield over rows 84..719.
C.void_backdrop(img, seed=0, stars=120, top=(9,10,22), bot=(16,18,40))
    -> returns an ImageDraw. Call it right after creating the image.

# Emissive core (the pulsar). THE one legal gradient in a void card.
C._radial_core(img, cx, cy, r, [(255,255,255), (220,230,236), (60,52,92)], power=1.0)

# Painterly marbled planet, Register S. Smooth, wavy contour bands, no black outline.
C.space_body(img, cx, cy, r, base=(150,158,156), band=(96,108,112), hi=(196,202,200), seed=0, bands=5)
    -> RETURNS A NEW IMAGE. You must do: img = C.space_body(img, ...)
    Use this for any planet-as-subject on a void card. Below r~20 use bands=2..3.

C._header(img, planet, paper_band=True|False)
C._caption(img, text, x, y, dark_bg=True|False)
C._draw_stickman(img, card, theme='dark'|'light')
```

## Palette (locked — segment 3)

```python
C.PAL['ink']    = (20, 22, 28)     # slate-black, outlines + type on cream
C.PAL['paper']  = (242, 234, 214)  # bone-cream, the strip + cream cards
C.PAL['deep']   = (5, 6, 11)       # void, the dark sky
C.PAL['amber']  = (232, 163, 61)   # signal amber (warm accent; also the void caption)
C.PAL['bone']   = (220, 230, 236)  # x-ray bone (cool accent)
C.PAL['violet'] = (110, 90, 156)   # magnet violet (cool accent)
C.PAL['shirt']  = (200, 50, 50)    # character accent; NEVER reuse as a card accent
```

Adjacent cards in the same beat must use **different** accents. Reference them per
card via `card['accent']` (already assigned by the schedule: bone/violet/amber/cream).
Use the card's own accent for that card's annotations and highlights. Two adjacent
cards sharing an accent is a critic-visible defect, but the accent is already fixed
per card by the schedule — just don't force two cards to look identical.

## Facts that are non-negotiable (fact_flags in the schedule)

- PSR B1257+12 is in **Virgo** (not Vela).
- Spin period **6.2 ms per revolution** (~161 rev/s). Say "six thousandths of a
  second", never "161 ms".
- Masses: Draugr **0.02** Earth, Phobetor **3.9**, Poltergeist **4.3**. One is
  Moon-ish, two are ~4 Earths.
- Periods: **25, 67, 98 days** (25.26 / 66.54 / 98.21).
- Wolszczan discovered the pulsar **1990**; planets announced **1992**; a two-year
  wait. No "nobody believed him" claim.
- PSR 1257+12 is a **sexagesimal sky coordinate**: 12h57m right ascension, +12°
  declination. There is NO base-eight joke and none may appear.

Any number or label you draw on a card MUST agree with the card's `narration`,
`caption` and `sketch`. If the sketch and the narration disagree, follow the
`narration`+`caption` (they were fact-corrected) and note it in your report.

## Style reference (no reference frames — build from these words)

- Space cards: near-black sky, a subtle cool vertical gradient, crisp white star
  dots of mixed size, one or a few glowing bodies. Restrained. The frame should
  feel EMPTY and vast, with the glowing body as the only bright thing.
- The character is the audience surrogate. Keep him at his scheduled size; do not
  scale him up to "fill" the card.
- Painterly, not vector. Soft shapes, layered translucent passes, stipple for
  texture. Nothing looks like a clean CAD render.
- Focal hierarchy per card: ONE dominant element (the glowing core, the disc, the
  character). Everything else supports it. Two competing focal points is a defect.

## Output contract

- One file: `work/segments/psrb1257/_cards_b<N>.py`.
- Module ends with:
  ```python
  RENDERERS = {'<card_id>': render_<card_id>, ...}
  ```
- Self-check at the bottom of the file (runs on import):
  ```python
  if __name__ != '__main__':
      raise SystemExit  # no side effects on import
  ```
  Actually — do NOT add import side effects. The frame generator imports this
  module to call `.register()`. Keep the module import-safe.
- Every renderer must return an `Image` in mode `'RGB'`, size `(1280, 720)`.

## How to verify your work (do this before you report)

From `work/` (the parent of `segments/`), run for YOUR beat only:

```python
import sys, json; sys.path.insert(0, '.')
import lib.cardframe as C
beat = json.load(open('segments/psrb1257/_beats/b<N>.json'))
mod = __import__('segments.psrb1257._cards_b<N>', fromlist=['RENDERERS'])
```
(that import path is awkward; easier: `exec(open('segments/psrb1257/_cards_b<N>.py').read())`
into a namespace, or add the segment dir to sys.path and `import _cards_b<N>`).

For each card: `img = C.RENDERERS_or_mod.RENDERERS[cid](card, planet)` — actually call
your module's own `RENDERERS[cid](card, "PSR B1257+12")`, save to
`segments/psrb1257/_beats/preview_b<N>_<cid>.png`, and confirm size/mode.

Then LOOK at nothing (you cannot see images). Instead assert mechanically:
- every render returns RGB 1280x720
- no exception, no >2 s per card
- no draw call uses width < 2 for a shape you consider "large"
Report the list of card ids you rendered + any sketch-vs-narration conflicts.