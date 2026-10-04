# Scene-builder contract (read fully before writing any code)

You are writing ONE file: `work3/lib/<chapter>_scene.py`. It renders one chapter of a
Paint-Explainer-style hand-drawn video about the world's most secret bunkers and vaults.
Follow the proven template exactly. Read `work3/lib/pinegap_scene.py` end-to-end FIRST —
it is the reference implementation and every rule below is already solved there.

## Hard rules

1. **The builder firewall is absolute.** Do NOT open, read, grep, or reference
   `work/ref2/`, `work3/measure/refscan/`, any reference transcript, or any reference
   frame. The reference is the critic's domain only. Everything you draw is yours.
2. **Free/local tools only.** No new pip installs. Pillow + numpy + the local `v2*`
   modules only.
3. **Deterministic.** No wall clock, no unseeded randomness. Every seed is an explicit
   integer literal derived from the beat index. `render_frame(scene, t)` must be a pure
   function of (scene, t).
4. **Our own words and art.** The narration in `segments/<chapter>/script.json` is ours.
   Draw every subject yourself with the primitives; never reproduce a reference image.

## The template (mirror pinegap_scene.py)

```python
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import engine3 as E3, scene_common as SC
import v2paint as PA, v2subjects as S, v2draw as D, v2type as T

HERE  = os.path.dirname(os.path.abspath(__file__))
SEG   = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', '<chapter>'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = '<Chapter Title>'
W, H = SC.W, SC.H
INK = SC.INK

# palette: 1 ink, 1 paper/cream, 2-3 accents, 1 deep. Define as module constants.

def build():
    clock = SC.BeatClock(BEATS)
    els = [E3.E('page', 'bg', SC.paper_bg(99), at=0.0)]

    def T(i): return clock.at('b%02d' % i, 0)
    def card(i, j, draw, kind='subject', seed=0, motion=None):
        end = clock.duration if j > len(clock.meta['beats']) else T(j)
        return E3.E('card%02d' % i, kind, draw, at=T(i), until=end, motion=motion)
    def cap(i, cx, cy, **kw):
        return SC.caption(clock.ph('b%02d' % i, 0)[1], cx, cy, T(i),
                          until=clock.until_of('b%02d' % i, 0), **kw)

    # ---- one card per beat, in order ----
    def c_xxx(tile, fw, fh):
        # paint the WHOLE frame: background first, then subject
        ...
    els.append(card(1, 2, c_xxx))
    els.append(cap(1, x, y, size=30))
    ...
    return SC.finish(els, TITLE, clock)

if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames' % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv: SC.render_preview(sc, os.path.join(SEG, '_preview_sheet.png'), n=8)
    if '--video' in sys.argv:    SC.render_video(sc, os.path.join(SEG, '_silent.mp4'))
```

## The five rules that matter (each is a fix for a real past failure)

1. **ONE CARD PER BEAT, and each card paints its OWN WHOLE FRAME** (background →
   subject). Never stack independent elements over a permanent background: one card's
   art will bleed into the next. `beats.json` gives every beat an exact [start,end], so
   there is no guessing at card boundaries. The final card passes `j = len(beats)+1`.

2. **CAPTION = the phrase, and it HANDS OFF.** Every beat's line is one short
   sentence (≤8 words) and `MAX_PHRASE_WORDS` is 8, so `clock.ph('b%02d'%i, 0)[1]` is
   the whole sentence. `cap(i, ...)` sets `until` to the next phrase's start, so
   captions never pile up. Never append two captions for one beat, and never place a
   caption where the subject or a diagram label sits — captions go in clear space
   (usually bottom band y≈680-700, or a corner the subject leaves empty).

3. **FRAME-FILL.** The dominant subject owns the frame and is cropped BY an edge
   (bleeds off left/right/top/bottom). A small subject centred in an empty field is the
   recurring defect in this project's history — do not do it. Scale the subject up.

4. **CADENCE: still-dominant.** One cut per sentence (~1 cut per 2-3s). Pass
   `motion=` on a card ONLY for the 1-2 beats where the narrator explicitly describes
   something moving (e.g. "signals land", "the missile launches"). A reference compared
   at a common 6fps is ~2/3 still; a motion-dominated film reads as wrong.

5. **v2paint API discipline** (the #1 runtime bug):
   - `PA.fill_poly(PA.img_of(d), pts, col, seed=…, value=…)` — takes an **Image**.
   - `PA.fill_rect(img, [x0,y0,x1,y1], col, seed=…)` — takes an **Image**.
   - `PA.paper_overlay(img, seed=…)` — takes an **Image**.
   - `PA.hand_stroke(d, [pts...], col, width, seed=…, wavelength=…)` — takes an
     **ImageDraw**, and `pts` is a LIST of points (never a bare point, never 2 floats).
   - `S.character`/`C3.draw_character`/`C3.draw_head` take an **Image**; get it with
     `PA.img_of(d)`.

## Primitive inventory (use these; do not reinvent)

- v2paint: `fill_poly`, `fill_rect`, `paper_overlay`, `hand_stroke`, `ellipse_pts`,
  `arc_pts`, `pie_pts`, `wobble_edge`, `img_of`.
- v2draw: `draw_label`, `draw_title`, `draw_number`, `draw_bubble`, `draw_arrow`,
  `draw_red_box`, `draw_red_x`, `draw_circle_marks`.
- v2subjects: `star`, `sun_rays`, `orbit_path`, `planet`, `split_planet`, `pulsar`,
  `thermometer`, `gauge`, `bar`, `swatch`, `character`.
- scene_common: `SC.closeup(draw, hx, hy, hr, expression, seed)` (cropped-in character
  bust — use for the character beats), `SC.fullbody(draw, x, feet_y, height, pose,
  expression, seed)` (full-body presenter), `SC.caption`, `SC.label`, `SC.sky_bg`,
  `SC.night_bg`, `SC.paper_bg`, `SC.render_preview`, `SC.render_video`.

## The character (ONE recurring presenter — every chapter MUST use him ≥1 beat)

`SC.closeup(draw, hx, hy, hr, expression, seed)` for a cropped-in expressive bust, or
`SC.fullbody(draw, x, feet_y, height, pose, expression, seed)` for a standing figure.
Expressions available: `neutral skeptic worried scared awed deadpan smirk grim shock
disgust confused`. Poses: see `character3.py` (`standing`, `pointing`, `shrugging`,
`peeking`, `creeping`, `arms_up`, …). **Use hr≈180-240 for closeups** — a giant head
(hr≥280) exposes the primitives' limits and looks worse. The character's tone must be
readable from his face alone (memory: character-must-be-cropped-into-not-placed-on).

## Your chapter

Read `segments/<chapter>/script.json` for the narration and per-beat `visual` notes.
Draw each beat's subject to match its line. Factual content must match the script — if
the script says something, the card must show it.

## Verify before you finish

Run exactly these and fix until clean:

```
cd C:\VIBE_CODE_CENTRAL\Gauntlet3\work3
python lib/<chapter>_scene.py            # builds, prints element count + duration
python lib/_beat_frames.py <chapter> --all 8   # renders 8 full-res frames, no exception
```

The build must not raise, and `--all 8` must write 8 PNGs to `measure/`. If `beats.json`
does not exist yet for your chapter, say so in your final message and still deliver the
file (it will be built once audio lands) — but if it does exist, the two commands above
must both pass.

Report back: the file you wrote, the element count, and any beats where you were unsure
the subject read clearly.