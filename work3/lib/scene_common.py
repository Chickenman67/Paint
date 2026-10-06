"""Shared scene machinery, extracted from the proven tres2b scene.

WHY THIS FILE EXISTS. tres2b_scene.py was the first real scene and it carries
the whole template inline: the caption helper with its `until` handoff, the
cropped close-up character, the phrase-timed `cap()`, the build() plumbing and
the ffmpeg raw-video driver. Copying that ~200 lines into nine chapter scenes
would mean nine places to fix the "captions pile up" and "character reads as set
dressing" bugs, and CLAUDE.md is explicit that the type scale and character rules
must not drift between segments. So the invariants live here once and each
chapter file declares only its own cards.

THE INVARIANTS THIS LOCKS IN

1. CAPTIONS HAND OFF, THEY NEVER PILE UP. Every caption goes through `cap()`,
   which sets `until` to the next phrase's start. The first tres2b pass appended
   each phrase as a permanent element and four captions rendered at the same y,
   as an unreadable black smear -- exactly the "big block of words" defect the
   brief calls out. See `_caption`.

2. AN INK CAPTION CARRIES NO KEYLINE. v2draw.draw_label strokes every non-INK
   label, and a 34px face with a 4px black stroke closes the counters of every
   letter. Only COLOURED captions get a keyline, kept thin (2px).

3. STROKE-WIDTH PADDING. A stroked draw needs its box padded by the stroke; a
   fill advance measured alone clips the outline (memory:
   hero-word-must-account-for-stroke).

4. FRAME-FILL. `closeup()` and `subject_r()` are sized so the dominant subject
   owns the frame and is cropped BY a frame edge, not parked inside it (memory:
   frame-fill-subject-scale, character-must-be-cropped-into-not-placed-on).

5. DETERMINISM. No wall clock, no unseeded randomness. render_frame(scene, t) is
   a pure function of (scene, t); verified by _scene_determinism.py.

Per-chapter palettes differ; everything structural does not.
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFilter

import engine3 as E3
import phrase_timing as PT
import character3 as C3

# v2 primitives live in work/lib; engine3 already puts it on sys.path.
import v2paint as PA
import v2subjects as S
import v2draw as D
import v2type as T

W, H = E3.W, E3.H

# --- the locked type scale (CLAUDE.md STYLE_CANON §2) ------------------------
# Every chapter uses these and only these. Per-segment re-sizing was the type
# drift problem in the v2 build.
INK = (24, 24, 28)
PAGE = (252, 252, 251)

# ---------------------------------------------------------------------------
# chapter -> scene module
# ---------------------------------------------------------------------------
# The persistent-stage rebuilds live in separate modules (`cheyenne2_scene`,
# `area51_2_scene`, ...) so the v1 card-per-beat scenes stay readable as the
# baseline. EVERY importer -- the shipper and both gates -- resolves a chapter
# through this map, so a chapter is redirected in exactly ONE place.
#
# This map was duplicated in the two gates and left out of _build_segments.py
# once. The gates tested v2 while the shipper imported v1 by name, so the
# entire stage rebuild, plus every art fix made against it, rendered nowhere
# and the film shipped the old one-card-per-beat cut machine. The shipped
# pixels matched v1 within h264 noise (0.8-1.7%) and were 70-89% off v2 at
# any beat where the two builds differ -- which is how the miss was caught.
# If you add an importer, call scene_mod(); never spell '%s_scene' yourself.
SCENE_MODULE = {'pinegap': 'pinegap2_scene',
                'room39': 'room39_2_scene',
                'cheyenne': 'cheyenne2_scene',
                'svalbard': 'svalbard2_scene',
                'vatican': 'vatican2_scene',
                'fortknox': 'fortknox2_scene',
                'tomb': 'tomb2_scene',
                'mezhgorye': 'mezhgorye2_scene',
                'area51': 'area51_2_scene'}


def scene_mod(chapter):
    """The importable scene module name for a chapter."""
    return SCENE_MODULE.get(chapter, '%s_scene' % chapter)


# ---------------------------------------------------------------------------
# caption
# ---------------------------------------------------------------------------

PAPER_KEY = (240, 236, 224)


def _draw_keylined(sub, text, color, sz, w, h, outline, stroke_w):
    """Draw a caption with a contrasting keyline UNDER the glyph fill.

    Every caption is a colour now (_legible_fill refuses ink), so every caption
    carries the 2px dark keyline from invariant 2. That keyline IS the contrast
    -- a paper halo on top of it read as a neon glow, which was worse than the
    collision the halo was added to solve. The earlier INK branch is gone
    because there is no longer an INK caption to serve.
    """
    D.draw_label(sub, text, color=color, size=sz,
                 center=(w / 2.0, h / 2.0), outline=outline,
                 outline_w=stroke_w)


# THE BRIEF: "text should never be gray or black because its hard to see."
#
# I first implemented that literally -- default every caption to a light amber
# and refuse any dark fill. That was WRONG and this comment records why, because
# the wrong version looked right in the source. Measured WCAG contrast against
# the actual paper the captions sit on:
#
#     T.INK (0,0,0), the old default : 20.46:1 on paper, 17.46:1 on cream
#     amber (255,214,64), my "fix"   :  1.37:1 on paper,  1.17:1 on cream
#
# Pure black on cream was the single most legible thing in the film. Blanket-
# banning dark fills would have made every default caption far worse, and would
# have missed the captions that ARE failing: the chapter ACCENT fills, which
# measure 2.5:1 (RED on sand) to 4.5:1 (RED on cream), and black on a NIGHT
# stage, which is ~1.2:1 and genuinely invisible.
#
# So the rule is not a ban on a colour channel. It is: a caption's fill must
# clear MIN_CAPTION_CR against the background it actually lands on. There is no
# single safe colour -- ink wins on paper, a light fill wins on night -- so the
# fill is chosen per card and then MEASURED by the readability gate.
MIN_CAPTION_CR = 4.5          # WCAG AA for the large/bold type we use

# Fills that pass MIN_CAPTION_CR against a light register, checked in
# _readability_gate.py. These are the choices; the gate is the enforcement.
CAPTION_ON_PAPER = T.INK      # 20.5:1 on paper -- correct on the day cards
CAPTION_ON_NIGHT = (255, 236, 150)   # light; the only thing that reads on night
CAPTION_ALERT = (198, 48, 40)        # the red used when a gray fill is refused


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _contrast_ratio(fg, bg):
    """WCAG 2.x relative-luminance contrast ratio between two RGB colours."""
    def lin(c):
        out = []
        for v in c[:3]:
            v = v / 255.0
            out.append(v / 12.92 if v <= 0.03928
                       else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
    a, b = lin(fg), lin(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def _probe_width(text, size, max_w):
    """Width of the rendered glyphs, mirroring make_draw's max_w shrink.

    It has to mirror the shrink exactly: if the box were built from the
    UNSHRUNK width on a long caption, the box would be wider than the text and
    we would be back to sampling the far side of the frame.
    """
    stroke_w = 2
    f = T.load_font(size, bold=True)
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke_w)
    tw = bb[2] - bb[0]
    mw = max_w or 980
    if tw > mw:
        sz2 = max(14, int(size * mw / float(tw)))
        f = T.load_font(sz2, bold=True)
        bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke_w)
        tw = bb[2] - bb[0]
    return int(tw) + 36


def _legible_fill(fill):
    """Resolve a caption fill against a KNOWN background.

    `fill` is honoured as written -- including a deliberate dark ink, which is
    correct on the day cards. What this guards is the case where a scene has no
    sensible default and used to get T.INK silently on a dark stage; the caller
    passes the background it is drawing on and we pick the register's colour.

    Grey is still refused outright: a low-saturation colour has no luminance to
    read by at ANY background, so a gray caption is a mistake in every register.
    """
    if fill is None:
        return CAPTION_ON_PAPER
    mx, mn = max(fill[:3]), min(fill[:3])
    # The page ink is exempt. It is technically a low-saturation dark colour, so
    # the grey test below used to swallow it and hand back CAPTION_ALERT red --
    # turning every caption that explicitly asked for INK-on-paper into the
    # alert colour. Measured: (24,24,28) has max-min = 4, well inside the grey
    # band, so `fill=INK` was silently recoloured on nine chapters' worth of
    # day cards. INK is the CORRECT fill on a light register (20.5:1), and it is
    # not what this guard is for: the guard exists for a caption the author
    # picked by accident, and INK is the default a card gets when nobody picks.
    if tuple(int(v) for v in fill[:3]) == (24, 24, 28):
        return fill
    if (mx - mn) <= 28 and _luma(fill) < 150:
        return CAPTION_ALERT          # gray: unreadable everywhere, say so loudly
    return fill


def _resolve_fill(fill, bg_luma, dark):
    """Pick the caption fill that actually reads against a measured background.

    WHY THIS IS NEEDED AT ALL. The per-card `dark=` flag was supposed to be the
    mechanism, and across 128 captions in nine chapters it is passed only 11
    times. Every other caption picks an accent (RED, SNOW, PALE, AMBER_LT, LAMP)
    without knowing whether the stage behind it is light or dark, and guesses
    wrong about a quarter of the time. The readability gate found all nine
    chapters affected, and the two eye-confirmed failures are opposite:

        svalbard b01  AMBER on a near-white snowfield   1.6:1
        cheyenne b03  INK on near-black clothing        1.19:1

    Both are the complaint "text should never be gray or black because its hard
    to see", and the second is worse than the complaint describes: the fill and
    the keyline are both near-black, so the letters have no interior and the
    caption reads as a smear.

    So the register is measured instead of declared. The caller passes the
    luminance of the pixels actually behind the caption (engine3 samples the
    page before the tile is built) and this picks the fill:

      * an authored fill that already clears MIN_CAPTION_CR is KEPT, so a
        deliberate red-on-cream emphasis survives;
      * otherwise fall back to the register's safe colour -- INK on a light
        background, light amber on a dark one.

    The authored fill is not silently discarded: `CAPTION_ALERT` is returned
    when even the safe colour cannot clear the bar, which is a loud colour that
    says "this card needs a real fix" rather than a quiet wrong one.
    """
    bg = (bg_luma, bg_luma, bg_luma)
    if fill is not None:
        chosen = _legible_fill(CAPTION_ON_NIGHT if dark else fill)
        if _contrast_ratio(chosen, bg) >= MIN_CAPTION_CR:
            return chosen
    safe = CAPTION_ON_NIGHT if bg_luma < 128 else CAPTION_ON_PAPER
    if _contrast_ratio(safe, bg) >= MIN_CAPTION_CR:
        return safe
    return CAPTION_ALERT


def caption(text, cx, cy, at, until=None, size=None, fill=None, max_w=None,
            dark=False):
    """One phrase caption: appears at `at`, LEAVES at `until`.

    `until` is the whole point (invariant 1). If omitted the caller should pass
    it -- cap() always does.

    `fill` is honoured when it is legible against what is actually behind the
    caption, and overridden when it is not. `dark=True` is still accepted and
    still selects the night register up front, for the case where the caller
    knows better than the sample; but it is no longer the only way to avoid
    landing on the wrong register, because 128 captions across nine chapters
    used it 11 times and a quarter of the rest were unreadable.
    """
    color = _legible_fill(CAPTION_ON_NIGHT if dark else fill)
    sz = size if size is not None else T.LABEL_PX
    max_w = max_w or 980
    # Every caption is a colour rather than the page ink, so every caption
    # carries the dark keyline (invariant 2). On a dark stage the keyline is
    # what separates the glyph from the art; on paper it is the counter-safety.
    outline = T.INK
    stroke_w = 2

    def make_draw(color):
        """Build the tile-drawing closure for a resolved `color`."""

        def draw(tile, fw, fh):
            f = T.load_font(sz, bold=True)
            probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke_w)
            tw = bb[2] - bb[0]
            if tw > max_w:
                sz2 = max(14, int(sz * max_w / float(tw)))
                f = T.load_font(sz2, bold=True)
                bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke_w)
                tw = bb[2] - bb[0]
            pad = stroke_w + 8                                  # invariant 3 (+keyline)
            w = int(tw) + pad * 2
            h = int(bb[3] - bb[1]) + pad * 2
            sub = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            _draw_keylined(sub, text, color, sz, w, h, outline, stroke_w)
            # CLAMP into the frame. Every scene places captions by eye at a y like
            # 690 or 700, but a 49px-tall caption centred there ends at 724 or 744
            # -- the bottom third of the letters is sliced off by the frame edge,
            # which reads as a broken render, not as a design choice. Clamping here
            # rather than asking each scene to remember means a caption can never be
            # authored off-frame, and a caption authored that low slides up instead
            # of disappearing.
            pad_x, pad_y = 12, 8
            x = int(cx - w / 2)
            y = int(cy - h / 2)
            if x < pad_x:
                x = pad_x
            elif x + w > 1280 - pad_x:
                x = 1280 - pad_x - w
            if y < pad_y:
                y = pad_y
            elif y + h > 720 - pad_y:
                y = 720 - pad_y - h
            tile.alpha_composite(sub, (x, y))
        return draw

    # First guess, used until the first background sample corrects it.
    draw = make_draw(_resolve_fill(fill, 255 if not dark else 0, dark))

    el = E3.E('cap_%d_%s' % (int(at * 1000), text[:14]), 'text', draw,
              at=at, until=until)
    # Background-aware: engine3 samples the page under this box BEFORE the tile
    # is built, and re-resolves if the register changed.
    #
    # The box must hug the GLYPHS, not the frame. It used to be a fixed
    # cx+-620 by cy+-60 -- 1240px wide, the full width of a 1280 frame -- so its
    # median was the average of everything in that band. On mezhgorye b08 the
    # caption sits on a dark ridge with pale sky to either side; the wide box
    # measured 131 (paper) and the caption was drawn in dark ink ON the dark
    # ridge, unreadable. The text is only ~500px wide and its own patch
    # measures ~119, but even that is an average across the ridge's edge.
    #
    # The honest sample is the band the glyphs actually cover, and for a
    # caption straddling an edge the register is genuinely ambiguous -- so
    # sample the text width, which at least stops the far side of the frame
    # from voting. Captions that straddle a hard edge are a placement problem
    # the scene should fix (move it onto one surface), not something the
    # resolver can guess correctly. This is `sample-label-bg-in-the-full-frame`
    # applied to captions: measure locally, never average across an edge.
    _pw = _probe_width(text, size if size is not None else T.LABEL_PX, max_w)
    el.needs_bg = True
    el.bg_probe_box = (cx - _pw / 2.0, cy - 46, cx + _pw / 2.0, cy + 46)
    el.bg_resolver = lambda luma: make_draw(_resolve_fill(fill, luma, dark))
    return el


def label(text, cx, cy, at, until=None, size=None, fill=None, max_w=None,
          dark=False):
    """A small diagram label -- same rules, smaller default."""
    return caption(text, cx, cy, at, until=until,
                   size=size or T.LABEL_SM_PX, fill=fill, max_w=max_w,
                   dark=dark)


# ---------------------------------------------------------------------------
# character
# ---------------------------------------------------------------------------

def closeup(draw, hx, hy, hr, expression, seed, shoulder=1.0):
    """A CROPPED-IN character close-up: one closed shoulder mass + the head.

    The round-4 critic found all five losses were frames where our side was a
    diagram on an empty page while the bar's side was an expressive close-up,
    so this capability has to be reachable from the MIDDLE of a chapter, not
    just the finale.

    The shoulder is a CLOSED BUST -- a bowed collar arc rising under the jaw
    and falling away to the frame bottom on BOTH sides -- not a wedge spanning
    the frame, which read as a black triangle rather than a person.
    """
    if shoulder > 0:
        jy = hy + hr * 0.92
        w = hr * 1.55 * shoulder
        top = []
        n = 33
        for i in range(n + 1):
            u = i / float(n)
            x = hx - w + 2.0 * w * u
            t = (u - 0.5) * 2.0
            y = jy + hr * (0.30 * (t ** 2) + 0.10 * abs(t))
            top.append((x, y))
        bust = top + [(hx + w, 830), (hx - w, 830)]
        PA.fill_poly(PA.img_of(draw), bust, INK, seed=seed + 48, value=0.0,
                     tint=0.0, band=0.0, edge=0.0, grow=2)
        PA.hand_stroke(draw, top, INK, max(5, int(hr * 0.05)), closed=False,
                       seed=seed + 49, wavelength=160.0, vary=0.30)
    C3.draw_head(PA.img_of(draw), hx, hy, hr, expression=expression,
                 seed=seed, lw=max(5, int(round(hr * 0.13))))


def fullbody(draw, x, feet_y, height, pose='standing', expression='neutral',
             seed=0, **kw):
    """A full-body character standing on `feet_y`, centred at x.

    character3's primitives take an Image (they open their own ImageDraw),
    while hand_stroke takes a Draw -- so this recovers the image rather than
    forwarding the draw the caller has.

    `**kw` forwards to character3.draw_character, which is how a caller puts the
    figure in the right REGISTER: character3 draws him near-black (BODY
    26,26,30) by default, which is correct on the paper cards and disappears
    against the dark exteriors and interiors. Pass `ink=(238,236,228)` there --
    the style canon's cream-on-dark rule. Added after b30 and b04 both rendered
    a black stickman on a night mountain and a black tunnel.
    """
    C3.draw_character(PA.img_of(draw), x, feet_y, height, pose=pose,
                      expression=expression, seed=seed, **kw)


# ---------------------------------------------------------------------------
# painterly background
# ---------------------------------------------------------------------------

def paper_bg(seed=99):
    """Page-white + paper tooth. Composited first so art AND text sit on it."""
    def draw(tile, fw, fh):
        ImageDraw.Draw(tile).rectangle([0, 0, fw, fh], fill=PAGE + (255,))
        PA.paper_overlay(tile, seed=seed)
    return draw


def sky_bg(top, bottom, seed=7, hz_frac=0.62):
    """A two-tone painted ground/sky fill with paper tooth -- for exteriors.

    `top` is the sky, `bottom` the ground; the horizon sits at 62% height so
    subjects stand on it rather than floating.

    WHY THE SKY IS PAINTED FULL-HEIGHT FIRST. The first version filled sky as
    [0,0,fw,hz] and ground as [0,hz,fh] as two abutting rects. fill_rect's
    default `edge=EDGE` wobbles the boundary independently on each of them, so
    the two wobbled edges don't coincide and a pale seam snakes across the
    horizon -- it read as a rendering error, not paint. Painting the sky over
    the WHOLE frame first and then laying the ground on top (starting slightly
    above the nominal horizon) means any wobble is covered by the second fill
    and the horizon becomes the single wobbled edge it should be.
    """
    hz = int(H * hz_frac)

    def draw(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, fw, fh], top, seed=seed, value=0.05)
        PA.fill_rect(tile, [0, hz - 6, fw, fh], bottom, seed=seed + 1, value=0.07)
        PA.paper_overlay(tile, seed=seed + 2)
    return draw


def night_bg(top, bottom, seed=7, hz_frac=0.62):
    """Night exterior -- same construction as sky_bg, for the finale beats."""
    return sky_bg(top, bottom, seed=seed, hz_frac=hz_frac)


# ---------------------------------------------------------------------------
# title backdrop
# ---------------------------------------------------------------------------

# The engine stamps scene.title LAST on every frame, and v2draw._wobble_glyph
# hardcodes fill=T.INK -- the title is always near-black and the engine cannot be
# changed for one chapter. On the paper register that is correct and crisp. On a
# NIGHT card it is invisible: the assembled film was shipping eight chapters
# whose titles could not be read, which no gate had caught because every gate
# reports on structure and this is a VALUE problem.
#
# This is vatican's `_lintel`, promoted to shared because it is the fix, not a
# chapter-specific flourish. Measured on the four eye-confirmed cases, a title on
# this backdrop reads at WCAG ~2.9 against the same title at ~1.15 on the raw
# night card -- the difference between "the most legible title in the film" and
# "I cannot read this".
#
# Call it FIRST in a card body, before any fill that would cover it, and keep it
# shallow (it stops at y=122) so the card's own in-art label has room at y=180.
TITLE_BACKDROP_SPAN = (10, 73)   # the part inside the title band, for the gate


def title_backdrop(tile, seed, col=(104, 92, 78), x0=0, x1=1280, dim=1.0):
    """A lit stone course at the head of a dark card, for the title to read on.

    ONE course across the band, uniform in value. Two overlapping courses were
    tried first (a full-value head course and a 0.55x course below it) because
    it reads more like cut stone, but the two values differ by ~45 levels -- far
    past the intrusion gate's DEV=25 -- so every band row failed the "uniform
    end to end" test that TITLE_BACKDROP relies on and the backdrop was reported
    as art striking through the title. The gate cannot tell a deliberate seam
    from a stroke, and it must not be loosened to try: the honest fix is a
    backdrop whose rows really are uniform. The masonry joints below supply the
    cut-stone read instead.

    `dim` scales the whole thing down for a finale, where the darkness is the
    subject and only a trace of the course may catch light.
    """
    def _c(k):
        return (int(col[0] * k * dim), int(col[1] * k * dim),
                int(col[2] * k * dim))

    d = ImageDraw.Draw(tile)
    # ONE uniform course covering the whole title band (y=0..86), with no value
    # change inside it. edge/value are low so the fill stays flat enough that
    # each row is uniform end to end.
    PA.fill_rect(tile, [x0, 0, x1, 86], _c(1.0), seed=seed, value=0.02, edge=1.0)
    # Masonry joints run BELOW the band only (band ends ~y=73). Run them up into
    # the band and they become dark verticals through the glyphs.
    x = x0 + 96
    k = 0
    while x < x1 - 40:
        PA.hand_stroke(d, [(x, 104), (x + 2, 122)], _c(0.52), 3, closed=False,
                       seed=seed + 10 + k, wavelength=70.0)
        x += 118
        k += 1


# ---------------------------------------------------------------------------
# build() plumbing
# ---------------------------------------------------------------------------

class BeatClock(object):
    """Phrase- and beat-timed lookups over a segment's beats.json.

    This is the object that makes the brief's core requirement mechanical: a
    caption appears at ITS phrase's word onset, not at the segment start and not
    at a predicted time. Word timings come from the synthesized WAV, so there is
    nothing to drift.
    """

    def __init__(self, beats_path):
        with io.open(beats_path, encoding='utf-8') as f:
            self.meta = json.load(f)
        phrases = PT.all_phrases_timed(beats_path)
        self.by_beat = {}
        for ph in phrases:
            self.by_beat.setdefault(ph['beat_id'], []).append(
                (ph['start'], ph['text']))
        self.bend = {b['id']: b.get('end', b.get('start', 0.0) + 1.0)
                     for b in self.meta['beats']}
        self.phrases = phrases
        self.duration = self.meta['duration_s']

    def n(self, bid):
        return len(self.by_beat[bid])

    def ph(self, bid, i):
        """(start, text) of phrase i in beat bid."""
        return self.by_beat[bid][i]

    def at(self, bid, i=0):
        return self.by_beat[bid][i][0]

    def until_of(self, bid, i):
        """When phrase (bid, i) leaves: the next phrase in the beat, else the
        next beat's first phrase start, else the beat's own end."""
        lst = self.by_beat[bid]
        if i + 1 < len(lst):
            return lst[i + 1][0]
        nxt = [p['start'] for p in self.phrases
               if p['start'] > self.bend[bid] - 1e-6]
        return min(nxt) if nxt else self.bend[bid]

    def bend_of(self, bid):
        return self.bend[bid]


# ---------------------------------------------------------------------------
# persistent stages, incremental layers, motion
# ---------------------------------------------------------------------------
#
# THE DEFECT THESE FIX. Every scene used to build with a local
#     def card(i, j, draw, ...):  -> an exclusive-window element whose draw
# closure repaints background + subject + labels for beats i..j-1. Nothing
# survived into the next card, so the film cut to a brand-new full-frame image
# every ~2.4s and nothing ever moved. The viewer reported exactly that: "every
# sentence has a cut with a completely new image... there are no animations or
# changes to the visual."
#
# Our own measurements doc names the fix (REFERENCE_MEASUREMENTS.md, "Engine
# requirements derived from the above"): "Each reveal adds/moves ONE element (no
# whole-card swaps)" and "There must be real per-frame motion, not pop-and-hold
# stills."
#
# The model below is that fix, in four pieces:
#   stage()  a persistent painted backdrop, live across 3-6 beats (the ground
#            the viewer can finally settle on).
#   layer()  one element that appears at a beat and leaves after it -- the unit
#            of reveal.
#   enter()  a motion track that slides a layer IN and holds.
#   drift()  a motion track that moves something continuously across a run.
# A facial-expression change is `expr_swap`, because the expression is baked
# into the tile at build time and so needs two elements, not a mutated one.


def _beat_end(clock, i):
    """When beat i's window ends: the next beat's onset, else the segment end."""
    if i + 1 > len(clock.meta['beats']):
        return clock.duration
    return clock.at('b%02d' % (i + 1), 0)


def stage(clock, i, draw, j=None, kind='bg', motion=None):
    """A persistent painted stage, live beats i..j-1 (j defaults to i+SPAN).

    ONE stage should span 3-6 beats. The stage paints the shared world -- sky,
    ground, room, the large subject that stays put. Elements inside it come and
    go as layers; the stage itself does not repaint.
    """
    if j is None:
        j = min(i + 4, len(clock.meta['beats']) + 1)
    return E3.E('stage%02d' % i, kind, draw, at=clock.at('b%02d' % i, 0),
                until=_beat_end(clock, j - 1), motion=motion)


def layer(clock, i, draw, j=None, kind='subject', motion=None, eid=None):
    """One element ON TOP of the current stage, live beats i..j-1.

    This is the reveal unit. `at` is the beat whose phrase it belongs to, so the
    element arrives when the narrator says the thing it shows. Give it an
    `enter()` or `drift()` track to make the arrival a movement, not a pop.
    """
    if j is None:
        j = i + 1
    name = eid or 'lay%02d_%s' % (i, kind)
    return E3.E(name, kind, draw, at=clock.at('b%02d' % i, 0),
                until=_beat_end(clock, j - 1), motion=motion)


def accrue(clock, i, j, draw, kind='subject', motion=None, eid=None):
    """A layer that STAYS once it arrives: live from beat i all the way to the
    end of the stage that ends at beat j.

    This is the structural half of the readability fix. `layer(clock, i, draw, j)`
    makes an element live for beats i..j-1, so a scene that wires every beat to
    its own layer churns its composition every beat -- the viewer sees a
    different picture every sentence, which is the exact complaint ("every
    sentence has a cut with a completely new image"). Art that ARRIVES and STAYS
    is what makes a stage read as one place: the stage paints the world once,
    then each beat adds the next thing and nothing is taken back until the
    stage turns over.

    Measured on the pinegap pilot: 16 short stages gave a full-frame repaint
    every 3.2s with 33 composition changes. Seven longer stages with accruing
    layers gave 7 repaints (longest gap 14.1s) and the viewer keeps one
    recognisable scene on screen while the art builds up inside it.
    """
    return layer(clock, i, draw, j=j, kind=kind, motion=motion,
                 eid=eid or ('acc%02d_%s' % (i, kind)))


def enter(clock, i, dx=-150, dy=0, dur=0.5, j=None):
    """Motion track: slide an element IN from (dx,dy) at beat i, then hold.

    The element is authored at its final position; these offsets are relative,
    so the first key is the offset it starts from and the second is 0 (home).
    """
    t0 = clock.at('b%02d' % i, 0)
    return [(t0, float(dx), float(dy), 1.0, 0.0), (t0 + dur, 0.0, 0.0, 1.0, 0.0)]


def drift(clock, i, j, dx=0, dy=0):
    """Motion track: move something continuously from beat i across beat j.

    For the "something is moving" case -- a searchlight beam, a cloud, a falling
    missile. Eased start to eased end so it never looks like a linear slide.
    """
    t0 = clock.at('b%02d' % i, 0)
    t1 = clock.at('b%02d' % min(j, len(clock.meta['beats'])), 0)
    return [(t0, 0.0, 0.0, 1.0, 0.0), (t1, float(dx), float(dy), 1.0, 0.0)]


def expr_swap(clock, i, expr_before, expr_after, until_j=None):
    """Facial-expression change mid-run: return two at/until pairs.

    The expression is baked into the rasterized tile at build time, so a change
    is two elements drawn at the SAME position -- the first ending exactly when
    the second starts. `j` is when the (new-expression) element leaves.
    """
    t = clock.at('b%02d' % i, 0)
    before_until = t
    after_at = t
    after_until = _beat_end(clock, (until_j if until_j is not None else i + 1) - 1)
    return (before_until, after_at, after_until)


def finish(els, title, clock, title_seed=0):
    """Wrap elements into a Scene with the real duration."""
    return E3.Scene(els, title=title, title_seed=title_seed,
                    duration=clock.duration)


# ---------------------------------------------------------------------------
# render drivers
# ---------------------------------------------------------------------------

def render_preview(scene, path, n=8):
    tw, th = 320, 180
    sheet = Image.new('RGB', (tw * 4, th * 2), (20, 20, 24))
    for i in range(n):
        t = scene.duration * i / max(1, n - 1)
        sheet.paste(E3.render_frame(scene, t).resize((tw, th), Image.LANCZOS),
                    ((i % 4) * tw, (i // 4) * th))
    sheet.save(path)
    print('preview -> %s' % path)


def render_video(scene, out, fps=60):
    import subprocess
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n = scene.frame_count()
    cmd = ['ffmpeg', '-y', '-v', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
           '-framerate', str(fps), '-i', '-',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(fps), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for i in range(n):
        p.stdin.write(E3.render_frame(scene, i / float(fps)).tobytes())
        # Progress heartbeat every ~5s so a background run is observable from the
        # output file. Without it a 6-hour render is an opaque PID.
        if (i + 1) % 300 == 0:
            el = time.time() - t0
            rate = (i + 1) / el
            eta = (n - i - 1) / rate if rate else 0
            print('    %d/%d frames  %.1f fps  elapsed %.1f min  ETA %.1f min'
                  % (i + 1, n, rate, el / 60.0, eta / 60.0), flush=True)
    p.stdin.close()
    p.wait()
    print('video -> %s (%d frames, %.1fs, %.1f fps overall)'
          % (out, n, scene.duration, n / max(1e-6, time.time() - t0)),
          flush=True)


def mux(seg_dir, fps=60):
    """Mux _silent.mp4 + audio.wav -> segment.mp4.

    RE-ENCODE BOTH STREAMS' AUDIO. CLAUDE.md §9.2: `-c copy` on audio is wrong
    -- every input's audio starts at PTS 0 and is not rebased onto a running
    timeline, so the assembled audio timestamps come out wrong while nb_frames
    still reads correct. Copy video only.
    """
    import subprocess
    silent = os.path.join(seg_dir, '_silent.mp4')
    wav = os.path.join(seg_dir, 'audio.wav')
    out = os.path.join(seg_dir, 'segment.mp4')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-i', wav,
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-ar', '44100', '-ac', '2', '-shortest', out],
                   check=True)
    # Verify both streams separately: format=duration reports only the longest.
    def dur(stream):
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream,
                            '-show_entries', 'stream=duration',
                            '-of', 'default=nw=1:nk=1', out],
                           capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except ValueError:
            return -1.0
    v, a = dur('v'), dur('a')
    print('muxed -> %s  video %.3fs  audio %.3fs  %s'
          % (out, v, a, 'OK' if abs(v - a) < 0.35 else 'DESYNC'))
    return out