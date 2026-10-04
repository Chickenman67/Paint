// workflow: build the per-beat card modules for segments 4-12.
// The card MODULES (drawing code, keyed by beat id) do not depend on audio
// timing, so they can be authored while TTS renders in the background. Each
// agent writes its own module file and verifies it imports + renders every beat
// in its segment to a PNG that the orchestrator then reviews by eye (the
// orchestrator is the only one with vision).
//
// FIREWALL (CLAUDE.md §8): the builder does NOT see the reference video,
// transcript, or frames. These agents get the written style canon only.
export const meta = {
  name: 'build-card-modules',
  description: 'Author Pillow card modules for segments 4-12, one agent per segment',
  phases: [
    { title: 'Read exemplar + libs', detail: 'one agent distills the seg-3 card-module pattern and the lib APIs' },
    { title: 'Build modules', detail: 'one agent per segment writes and self-verifies its card module' },
  ],
}

const SEGMENTS = [
  { key: 'tres2b', no: 4, name: 'TrES-2b' },
  { key: 'wasp17b', no: 5, name: 'WASP-17b' },
  { key: 'wasp127b', no: 6, name: 'WASP-127b' },
  { key: 'gliese436b', no: 7, name: 'Gliese 436 b' },
  { key: 'koi55', no: 8, name: 'KOI-55' },
  { key: 'ltt9779b', no: 9, name: 'LTT 9779 b' },
  { key: 'fomalhautb', no: 10, name: 'Fomalhaut b' },
  { key: 'kelt9b', no: 11, name: 'KELT-9b' },
  { key: 'psoj3185', no: 12, name: 'PSO J318.5-22' },
]

const EXEMPLAR = `
You are authoring ONE Pillow card-render module for the Gauntlet3 Paint-Explainer
video pipeline. The segment you own is described by an existing script.json.

FIRST, read these files to learn the exact APIs and patterns (do not guess any
function signature — read them):
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/STYLE_CANON.md          (canonical measured style; OVERRIDES other docs)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/cardframe.py       (C.render(card) — the card compositor API)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/ink.py             (wobbly outline strokes, smooth curves)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/stickman.py        (Stickman(pose, expression) + MOUTHS)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/type.py            (locked type scale: comicbd.ttf/comic.ttf)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/palette.py         (per-segment 4-6 color palettes)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/texture.py         (paper/canvas texture, starfield)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/title_band.py      (white 84px title strip)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/transition.py       (snap cuts, motion helpers)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/psrb1257/_cards_b1.py   (a real exemplar beat-group module)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/psrb1257/_cards_b4.py   (another exemplar)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/psrb1257/PALETTE_SPEC.md (a locked palette spec to imitate)
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{SEG}/script.json       (YOUR segment: beats, lines, visual descriptions, register)

STYLE CANON — non-negotiable rules you must follow (these OVERRIDE anything else):
  - Layout A: 84px white/cream paper TITLE STRIP on top (rows 0..83) with the
    hand-lettered planet name; full-bleed 636px ART below (rows 84..719). There
    is NO caption band. Narration is audio only — do NOT print the narration.
  - Type: comicbd.ttf (Comic Sans Bold) for headers/captions, comic.ttf for
    small labels/stamps. Consolas is retired. One type family, locked sizes from
    type.py. Never invent a new size.
  - Outlines: ~6px on large shapes (5-8 big, 3-4 detail, 1-2 fine). Thick
    organic hand-drawn lines, NOT thin wires.
  - Lines: smooth hand curves with LOW-frequency wobble (lib/ink.py), not
    per-vertex jitter.
  - Two registers:
      * 'void' (space) — pure black starfield background, CREAM character and
        cream type (dark-on-light is WRONG in space cards).
      * 'cream' (scene/paint) — cream/paper background, DARK ink character and
        dark ink outlines. Flat fills. The character is usually GROUNDED on a
        wavy horizon band, not floating.
  - Subject labels sit ON or immediately BESIDE the thing they name. Overlap
    between a label and its subject is authentic, not a defect.
  - Hard snap cuts between cards. No cross-fades between beats.
  - Deterministic wobble: seed every random wobble with a stable per-beat seed
    so re-renders are identical.

THE CARD INTERFACE — THE EXACT CONTRACT YOU MUST MATCH. Read cardframe.py and
_cards_b1.py to confirm, but this is the true shape:

  * Each beat module is a normal python module in the segment directory that
    defines a module-level dict named RENDERERS:
        RENDERERS = { '<card_id>': <fn>, ... }
    where every <fn> has the signature  fn(card, planet) -> PIL.Image  and
    returns a complete 1280x720 RGB frame. <card_id> is the beat's id field
    from script.json (unique per segment).
  * The frame generator does:  C.register(module.RENDERERS)  for each beat
    module, then calls  C.render(card, SEGMENT_PLANET_NAME)  once per card to
    bake the still, then layers quantized 0.25s motion on top. So your function
    receives the already-built card dict and must DRAW the frame — you do NOT
    return a card dict. The dispatch key is card['id'].
  * The card dict the scheduler hands you contains at least:
        card['id']        the beat id (also the RENDERERS key)
        card['caption']   a SHORT floating caption string to draw on the art
        card['stickman']  None, or a dict {x_center, y_top, height, pose,
                          expression} — draw the character with
                          C._draw_stickman(img, card, theme='dark'|'light')
                          (it reads card['stickman'] itself), or call
                          S.draw_stickman directly if you need the raw API.
    Anything else your renderer needs (custom geometry) it computes itself or
    you hardcode it per card — that is the established pattern.
  * Do NOT redefine the global dispatch or edit work/lib/cardframe.py. Register
    via your own RENDERERS dict; the frame generator merges it.
  * cardframe.py's module-level PAL is SEGMENT 3's palette. For your segment,
    define your OWN palette dict in your module and reference it directly
    (e.g. MY_PAL['bone']); do not rely on C.PAL except for genuinely generic
    helpers like void_backdrop/space_body/add_glow/_radial_core.

WHAT TO PRODUCE (exactly two deliverables, both written by you, no exceptions):
  1. C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{KEY}/_cards.py
     — a self-contained module with a module-level RENDERERS dict covering EVERY
       beat in your segment's script.json (keyed by beat id), each fn(card,
       planet)->Image, PLUS a __main__ self-test that, for every beat, builds a
       minimal card dict (id, caption=<a short generic caption>, stickman with a
       default pose/expression at a reasonable position when the beat has a
       character) and renders it to work/segments/{KEY}/cardsheet/beat_<NN>.png,
       printing one line per beat.
  2. C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/{KEY}/PALETTE_SPEC.md
     — the locked 4-6 color palette for this segment: hex values, the accent
       cycle order, ink/cream/deep/accent roles, and the character ink color for
       each register. Imitate the structure of psrb1257/PALETTE_SPEC.md.

RULES:
  - Use ONLY the free local stack already in work/lib/. Do not pip install
    anything. Do not use any paid API. Do not fetch the reference video or any
    of its frames.
  - Every beat must render without raising. The self-test must exit 0.
  - The stickman must appear in at least 4 beats (CLAUDE.md §6) — the script.json
    'visual' fields already say where. Follow them. Where a beat says
    "no character - pure data beat", draw no stickman.
  - Do not print the narration line as a caption. Only the planet title goes in
    the title strip, plus small diagram labels/stamps.

SELF-VERIFICATION before you finish — actually run it and iterate until clean:
    cd C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments && python {KEY}/_cards.py
It must print one line per beat and exit 0, with all beat_*.png written. Then
report, as your final text (this IS the return value):
  - confirmation that the module exposes a module-level RENDERERS dict keyed by
    every beat id, each fn(card, planet)->1280x720 Image
  - the palette hexes you locked
  - the list of beat ids rendered, and confirmation the self-test exited 0
  - any beat you could not draw to canon and why (be honest)
`

phase('Read exemplar + libs')
const guide = await agent(
  `Read these files and produce a precise, dense technical briefing I can hand
to 8 parallel coding agents as their shared spec. Focus on EXACT function
signatures, the card dict schema, and the palette/type constants — anything a
coder would otherwise have to guess.
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/cardframe.py
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/stickman.py
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/type.py
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/ink.py
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib/palette.py
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/psrb1257/_cards_b1.py
  C:/VIBE_CODE_CENTRAL/Gauntlet3/work/segments/psrb1257/PALETTE_SPEC.md
Return: the exact card dict schema, the RENDERERS-dict module contract, every
public helper signature (with arg names and return types), the type scale
constants, the Stickman API, and a minimal working module that defines
RENDERERS and registers with C.register correctly.`,
  { label: 'exemplar-guide', phase: 'Read exemplar + libs', effort: 'high' }
)

phase('Build modules')
const results = await pipeline(
  SEGMENTS,
  (s) => agent(EXEMPLAR.replaceAll('{SEG}', s.key).replaceAll('{KEY}', s.key) +
    `\n\nA prior agent distilled the following shared API briefing. Trust it over\nyour own guesses, but still read the lib files to confirm:\n\n${guide}`,
    { label: `cards:${s.key}#${s.no}`, phase: 'Build modules', effort: 'high' })
)

return results.filter(Boolean)
