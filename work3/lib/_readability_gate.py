"""Readability gate: does a human viewer actually follow this chapter?

This is the gate that tests the ACTUAL complaints, not structural tidiness.
Four things were wrong with the v1 bunker film as a viewer experience:

    "every sentence has a cut with a completely new image ... there are no
     animations or changes to the visual"
    "when there's also a bunch of text its hard to know whats happening"
    "text should never be gray or black because its hard to see"
    "dont just cut to an image with all the text and stuff on it"

Each of those is a separate check below. What they all share is that none of
them is visible in the source code, so every check here RENDERS and MEASURES
PIXELS. This project has a long list of gates that looked at the wrong thing:

    [[gates-must-render-not-just-inspect]]  a green gate that never called the
                                           draw function
    [[judge-art-at-full-res]]                a thumbnail invented a defect
    [[pick-thresholds-from-eye-confirmed-cases]]
                                           WCAG 3.0 flagged the most legible
                                           title in the film
    [[coverage-gate-catches-silent-scene-failure]]
                                           measure MISSING vs STALL, not art
                                           onsets, or every caption refresh
                                           reads as a gap

So: this gate renders, and `--selftest` proves each check is not a no-op by
running it against a DELIBERATELY BROKEN frame that it must flag.

THE TECHNIQUE. Isolating a caption's pixels from a composited 1280x720 frame is
the hard part, and getting it wrong is how a gate ends up measuring the
background and reporting a caption is unreadable when it is fine. Two attempts
failed first:

  * Threshold the frame for "text-coloured" pixels. Fires on stars, coloured
    art, and the paper wash -- this is [[pixel-gate-fires-on-stars]].
  * Re-derive the caption's rectangle from the cx/cy passed to caption() and
    trust it. The clamp in caption() slides a caption that would fall off the
    frame, and `D.draw_label` centres on a box computed from the FONT METRICS,
    not from cy. So the authored centre and the drawn centre disagree, and any
    defect at the edge is exactly the region where the guess is worst.

What works: render the beat TWICE, once whole and once with every `kind='text'`
element removed from the scene, and take the pixels that differ. That is
precisely the text's contribution -- no heuristic, no colour assumption, and it
picks up whatever the clamp and the font metrics actually did. The cost is two
renders per sampled frame, which is why sampling is time-based rather than
beat-based (a beat can be 1.2s or 4s and the text risk is per second, not per
beat).
"""

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# v2type/v2draw/v2paint live in the OLD project dir; engine3 puts it on the
# path when imported, but this module imports v2type-adjacent helpers directly,
# so it is added here too (same two lines _coverage_gate.py uses).
sys.path.append(os.path.join(os.path.dirname(ROOT), 'work', 'lib'))

W, H = 1280, 720

CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']

# Kept in sync with _coverage_gate.SCENE_MODULE: every chapter here is the
# persistent-stage rebuild, so the v1 scene module is the baseline, not the
# thing under test.
SCENE_MODULE = {'pinegap': 'pinegap2_scene',
                'room39': 'room39_2_scene',
                'cheyenne': 'cheyenne2_scene',
                'svalbard': 'svalbard2_scene',
                'vatican': 'vatican2_scene',
                'fortknox': 'fortknox2_scene',
                'tomb': 'tomb2_scene',
                'mezhgorye': 'mezhgorye2_scene',
                'area51': 'area51_2_scene'}

# ---------------------------------------------------------------------------
# Thresholds. Every one of these is a BAND, and every band has two
# eye-confirmed cases on either side of it. A one-sided threshold is a guess.
# ---------------------------------------------------------------------------

# (a) FIT. How close text ink may come to a frame edge. 6px, not 0: the
# caption is drawn with a 2px keyline plus a 3px pad on each side, so a
# correctly-placed caption has ink ~10px clear of the edge and anything tighter
# than 6 means the clamp failed. CALIBRATION: the real cheyenne-bottom and
# vatican-top clips sit at 0-3px (ink literally on the border row) and the
# tightest correct captions in the film measure 9-11px.
EDGE_CLEAR_PX = 6

# (b) CONTRAST.
#
# THIS THRESHOLD IS NOT WCAG 4.5, AND THE REASON IS A SET OF EYE-CONFIRMED
# CASES. Measuring fill-vs-background alone flagged two kinds of caption:
#
#   UNREADABLE (correctly flagged, both since fixed by the background-resolving
#   fill in scene_common.caption):
#     svalbard b01  gold (216,192,120) on white snow (239,243,246)  1.6:1
#     cheyenne b03  black on near-black clothing                       1.19:1
#
#   CLEARLY READABLE (false positives, and the reason this was rewritten):
#     svalbard b06  red on mid-grey sky          2.56:1
#     cheyenne b38  amber on the dark door       4.1:1
#
# What separates the two groups is NOT the ratio. It is whether the fill and
# its 2px keyline are the SAME colour. `caption()` gives every coloured fill a
# black keyline, and that keyline is the contrast mechanism -- the glyph is
# read as a shape with a dark edge, not as coloured pixels. When the fill is
# also dark (cheyenne b03: INK fill, INK keyline) the keyline adds nothing, the
# letters have no interior, and it is unreadable at any ratio. When the fill
# differs from the keyline the glyph is legible well below 4.5:1, because the
# eye is resolving an edge, not a fill.
#
# So a caption is flagged only when the fill and the keyline are near-identical
# AND that shared colour is within KEYLINE_MERGE of the background. That is a
# much narrower, much more honest defect than "ratio < 4.5", and it is the shape
# of the thing that actually went wrong.
#
# WCAG 4.5 remains the bar for the AUTORRESOLVER in scene_common, which picks
# fills blind and must therefore be conservative. The gate here is allowed to be
# more permissive because it can see the keyline.
KEYLINE_MERGE = 40
MIN_FILL_VS_BG_WHEN_KEYLINED = 1.15

# (c) DENSITY. The user overrode the original rule: not a progressive list, and
# text only every couple of images. So the target is a text-free beat being the
# COMMON case. Below 0.25 a chapter has stopped explaining anything; above 0.55
# it is the wall-to-wall text the complaint named.
#
# CALIBRATION: the nine rebuilt chapters measure 0.35-0.42, comfortably inside.
# The v1 scenes, which had a caption on nearly every beat, measured 0.85+.
TEXT_FRAC_MIN = 0.25
TEXT_FRAC_MAX = 0.55

# Longest run of consecutive captioned beats. Two in a row is emphasis
# ("They are radomes. / A radome is a protective cover."); three is the
# rhythm being complained about.
TEXT_RUN_MAX = 2

# (d) CADENCE. The user's first complaint, measured two ways.
#
# The v1 film "cuts to a completely new image every sentence." Measured on
# pixels, that is a full-frame repaint every ~2.5s (v1 pinegap: 19 repaints,
# median gap 2.5s). The persistent-stage rebuild is supposed to make stages
# HOLD -- so a LONG median gap is the GOAL, not a defect, and there is no upper
# bound on it here. Two quantities are checked instead:
#
#   MEDIAN GAP < GAP_MIN  -> still cutting every sentence (the v1 defect)
#   MAX STILL GAP > STILL_MAX -> a single stretch with nothing changing for
#                                too long, so the eye disengages
#
# CALIBRATION against measured chapters (6fps, >24-level pixel diff, full
# repaint > 30% of frame):
#     v1 pinegap      med 2.5s  max-still 11s  motion  3%   <- the complaint
#     pinegap2        med 21.5s max-still 24s  motion 18%
#     room39_2        med 12.3s max-still 16s  motion 13%
#     mezhgorye_2     med  2.5s max-still  8s  motion  9%   <- still cutty
#     area51_2        med  2.5s max-still 33s  motion 10%
# GAP_MIN=3.0 separates v1/mezhgorye/area51 (2.5) from the well-held chapters.
# STILL_MAX=20s lets pinegap2's 21.5s median (fine, it has motion+layers to
# carry it) but catches area51's 33s dead stretch; room39's 16s passes.
#
# NOT a stage-window check on PURPOSE: counting "does every stage span 3-6
# beats" reads the element list and would have passed v1, whose stages were all
# exactly one beat wide -- one stage per beat IS a per-beat repaint. The
# complaint is about time the viewer experiences, so this is measured on pixels
# at the same 6fps the reference's cadence was (see
# [[cadence-must-be-compared-at-same-fps]]).
GAP_MIN = 3.0
STILL_MAX = 20.0

# (e) MOTION. Fraction of frames where something on screen is actually moving.
# The reference measures 7%; v1 pinegap measured 3%; the rebuilt chapters 9-18%.
# Reject < 5% (the "nothing moves" complaint) and cap high to catch an
# overcorrection (too much movement is its own readability problem).
MOTION_FRAC_MIN = 0.05
MOTION_FRAC_MAX = 0.22


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def scene_mod(chapter):
    return SCENE_MODULE.get(chapter, '%s_scene' % chapter)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(rgb):
    return (0.2126 * _lin(rgb[0]) + 0.7152 * _lin(rgb[1])
            + 0.0722 * _lin(rgb[2]))


def contrast(fg, bg):
    a, b = _luminance(fg), _luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def load(chapter):
    """Build the scene and its beats. Returns (scene, beats, module)."""
    importlib.invalidate_caches()
    mod = importlib.import_module(scene_mod(chapter))
    scene = mod.build()
    with open(os.path.join(ROOT, 'segments', chapter, 'beats.json')) as fh:
        meta = json.load(fh)
    return scene, meta['beats'], mod


def sample_times(scene, beats, per_beat=3):
    """Render-check times in seconds: `per_beat` samples across every beat.

    Sampling by TIME would be simpler but would miss short beats entirely at the
    default rate, and a caption only exists during part of a beat -- the caption
    that runs off the bottom of the frame lives for exactly its own beat. So the
    samples are laid out per beat.
    """
    out = []
    for b in beats:
        s = float(b['start'])
        e = float(b.get('end', s + 1.0))
        if e <= s:
            e = s + 0.4
        for k in range(per_beat):
            out.append(s + (e - s) * (k + 0.5) / per_beat)
    return out


def text_mask_tiles(scene, t):
    """The alpha tiles every visible `kind='text'` element would paint at `t`.

    Built by calling the element's own build path, so the tile is byte-identical
    to the one render_frame composites. Returns a list of (x, y, rgba_image).
    """
    import engine3 as E3
    tiles = []
    for el in scene.elements:
        if (getattr(el, 'kind', '') or '') != 'text':
            continue
        if not el.visible(t):
            continue
        try:
            tile, (ox, oy) = el.tile_and_origin()
        except Exception:
            continue
        tiles.append((ox, oy, tile))
    return tiles


def frame_text_ink(scene, t):
    """Pixels this frame's captions contribute: (mask, bg_rgb, glyph_rgb).

    mask     bool HxW -- True where a caption changed the frame
    bg_rgb   HxWx3 uint8 -- the frame with the captions NOT drawn
    glyph_rgb HxWx3 uint8 -- the frame as rendered

    Isolate the text by rendering the beat twice and taking the pixels that
    differ. Everything else in the frame -- the paper wash, the wobble, the art
    -- is identical between the two renders because it is deterministic given
    (scene, t) and the text elements do not feed into it.
    """
    import numpy as np
    import engine3 as E3

    with_text = np.asarray(E3.render_frame(scene, t).convert('RGB'),
                           dtype=np.int16)

    # Same scene, same t, minus the text elements.
    bare = _SceneWithoutText(scene)
    without = np.asarray(E3.render_frame(bare, t).convert('RGB'),
                         dtype=np.int16)

    mask = (np.abs(with_text - without).max(axis=2) > 6)
    return mask, without.astype(np.uint8), with_text.astype(np.uint8)


class _SceneWithoutText(object):
    """A scene view with every `kind='text'` element removed.

    Deliberately a wrapper rather than a mutated copy: the engine caches built
    tiles on the ELEMENT, and text elements are the ones we want to reuse from
    cache across the two renders, not rebuild.
    """

    def __init__(self, scene):
        self.elements = [e for e in scene.elements
                         if (getattr(e, 'kind', '') or '') != 'text']
        self.title = scene.title
        self.title_seed = scene.title_seed
        self.duration = scene.duration


# ---------------------------------------------------------------------------
# (a) FIT -- text ink touching the frame edge
# ---------------------------------------------------------------------------

def check_fit(scene, beats, per_beat=3):
    """Report captions whose ink comes within EDGE_CLEAR_PX of a frame edge.

    POSITIVE CONTROL: `--selftest` builds a scene whose caption is centred at
    cy=716 with a 32px face, which lands the glyphs on the bottom border row.
    """
    import numpy as np
    hits = []
    for i, b in enumerate(beats, 1):
        for t in sample_times(scene, [b], per_beat):
            mask, _, _ = frame_text_ink(scene, t)
            if not mask.any():
                continue
            ys, xs = np.nonzero(mask)
            clear = min(int(xs.min()), int(ys.min()),
                        W - 1 - int(xs.max()), H - 1 - int(ys.max()))
            if clear < EDGE_CLEAR_PX:
                hits.append((i, round(t, 2), clear))
    return hits


# ---------------------------------------------------------------------------
# (b) CONTRAST -- measured off the pixels, not read off the source
# ---------------------------------------------------------------------------

def check_contrast(scene, beats, per_beat=3):
    """Report captions whose glyph core is below MIN_CONTRAST against its bg.

    Three earlier approaches at this were all wrong and are recorded so they are
    not retried:

      * Read `fill` off the caption call and compute the ratio against a guessed
        background. Wrong twice: the guess is the problem (a caption lands on
        whatever the stage painted, which varies per chapter and per beat) and
        so is trusting the source when `caption()` may clamp and rescale.
      * Mean WCAG luminance over the glyph mask. Reads ~1.0 for everything,
        because the mask is a two-pixel keyline plus anti-aliased edges and a
        mean averages the core away.
      * A ratio against the whole frame's mean background. A caption crosses a
        frame with two backgrounds (sky behind the top, art behind the bottom)
        and one mean number describes neither.

    This measures the CORE of the glyph (the brightest decile of the text
    pixels -- with a dark keyline the keyline is the darkest and the fill is the
    brightest, so the decile picks the fill) against the MEDIAN of the pixels
    immediately around the text's own bounding box, which is the actual
    background it sits on.

    POSITIVE CONTROL: a caption drawn in mid-grey over mid-grey.
    """
    import numpy as np
    hits = []
    for i, b in enumerate(beats, 1):
        for t in sample_times(scene, [b], per_beat):
            mask, bg, drawn = frame_text_ink(scene, t)
            if mask.sum() < 40:
                continue
            ys, xs = np.nonzero(mask)
            y0, y1 = int(ys.min()), int(ys.max())
            x0, x1 = int(xs.min()), int(xs.max())
            if (y1 - y0) < 4 or (x1 - x0) < 4:
                continue

            sel = mask[y0:y1 + 1, x0:x1 + 1]
            stroke = drawn[y0:y1 + 1, x0:x1 + 1][sel].astype(np.float64)

            # Two colour clusters: the FILL and the INK KEYLINE. Both are found
            # by colour, not by a luminance decile -- see the long note in the
            # module docstring; the first version measured the anti-aliased
            # fringe and called the most legible caption in the film a 1.88:1
            # failure.
            q = (stroke // 24 * 24).astype(np.int32)
            keys = q[:, 0] * 65536 + q[:, 1] * 256 + q[:, 2]
            vals, counts = np.unique(keys, return_counts=True)
            order = np.argsort(counts)[::-1]

            def _rgb(k):
                return np.array([(k >> 16) & 255, (k >> 8) & 255, k & 255],
                                dtype=np.float64)

            def _luma(c):
                return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

            top = _rgb(vals[order[0]])
            key = _rgb(vals[order[1]]) if len(order) > 1 else top

            # Which cluster is the keyline? The near-black one. T.INK is
            # (24,24,28) but rasterises to (0,0,0), which is 28 away on the blue
            # channel, so an "is it INK" test has to be a near-black luminance
            # test rather than a distance-to-INK test.
            if _luma(top) < 70 and _luma(key) >= 70:
                fill_c, key_c = key, top
            elif _luma(key) < 70:
                fill_c, key_c = top, key
            else:
                # No near-black cluster: an ink fill on paper, where fill and
                # keyline are the same pixels. Treat it as its own keyline.
                fill_c = key_c = top

            # Background: a ring of non-text pixels immediately around the box,
            # so it is the surface this caption actually sits on.
            pad = 14
            ry0, ry1 = max(0, y0 - pad), min(H, y1 + 1 + pad)
            rx0, rx1 = max(0, x0 - pad), min(W, x1 + 1 + pad)
            ring = bg[ry0:ry1, rx0:rx1].reshape(-1, 3)
            bgc = np.median(ring, axis=0)

            ratio = contrast(fill_c, bgc)
            merged = np.abs(fill_c - key_c).max() <= KEYLINE_MERGE
            # The defect is a keyline that cannot separate: fill and keyline are
            # the same colour, so the glyph has no interior and its edge carries
            # no information. Combined with a background close to that shared
            # colour, the caption is a smear.
            if merged and contrast(key_c, bgc) < MIN_FILL_VS_BG_WHEN_KEYLINED:
                hits.append((i, round(t, 2), round(float(ratio), 2),
                             'fill==keyline %s on bg %s'
                             % (tuple(int(v) for v in fill_c),
                                tuple(int(v) for v in bgc))))
    return hits


# ---------------------------------------------------------------------------
# (c) DENSITY -- text on too few / too many beats
# ---------------------------------------------------------------------------

def check_density(scene, beats):
    """Text-beat fraction and the longest run of consecutive captioned beats."""
    caps = []
    for el in scene.elements:
        if (getattr(el, 'kind', '') or '') != 'text':
            continue
        caps.append((float(getattr(el, 'at', 0.0) or 0.0),
                     getattr(el, 'until', None)))

    def live(t):
        for at, until in caps:
            u = float(until) if until is not None else float('inf')
            if at <= t + 1e-6 and t < u - 1e-9:
                return True
        return False

    nocap = []
    for i, b in enumerate(beats, 1):
        mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        if not live(mid):
            nocap.append(i)

    n = len(beats)
    frac = (n - len(nocap)) / float(n) if n else 0.0
    trun = tbest = 0
    trat = 0
    for i in range(1, n + 1):
        if i not in set(nocap):
            trun += 1
            if trun > tbest:
                tbest, trat = trun, i
        else:
            trun = 0
    return frac, tbest, trat, nocap


# ---------------------------------------------------------------------------
# (d) CADENCE -- how long until the whole frame changes
# ---------------------------------------------------------------------------

def check_cadence(scene, beats, fps=6):
    """Median seconds between FULL frame repaints, and the longest stretch
    with no significant change. Returns (median_gap, max_still_gap, n_repaints).

    "Full repaint" is >30% of the frame's pixels changing by >24 levels -- the
    thing a viewer perceives as a cut to a new image. A caption refresh or a
    moving element does NOT count as a repaint (it changes a small fraction of
    pixels), which is correct: [[coverage-gate-catches-silent-scene-failure]]
    established that a caption refresh is a legitimate hold, not a new scene.
    """
    import numpy as np
    import engine3 as E3

    dur = float(scene.duration or beats[-1].get('end', 0.0))
    n = max(3, int(dur * fps))
    prev = None
    cuts = []
    last_change_t = 0.0
    max_still = 0.0
    for i in range(n):
        t = dur * i / float(n)
        fr = np.asarray(E3.render_frame(scene, t).convert('L'), dtype=np.int16)
        if prev is not None:
            d = float((np.abs(fr - prev) > 24).mean())
            if d > 0.30:
                cuts.append(t)
                last_change_t = t
            else:
                max_still = max(max_still, t - last_change_t)
        prev = fr

    if len(cuts) < 2:
        return -1.0, round(max_still, 1), len(cuts)
    gaps = sorted(cuts[i + 1] - cuts[i] for i in range(len(cuts) - 1))
    return gaps[len(gaps) // 2], round(max_still, 1), len(cuts)


# ---------------------------------------------------------------------------
# (d2) REFRAME -- does a persistent stage actually stay persistent?
# ---------------------------------------------------------------------------
#
# check_cadence tells us a chapter is cutting. It does not say WHERE, and the
# place it turned out to be was not the one the onsets suggested. The six
# unconverted chapters each wrap their beats in SC.stage() -- the backdrop
# really does persist -- but paint a fresh full-frame subject on every beat
# INSIDE that stage, handing off at until/at. The viewer sees a cut every
# sentence while every structural measurement says the stage held.
#
# So this check reports the offenders, not a summary. It measures each element
# ONSET (not each sampled frame, which at 6fps smears a 0.4s arrival across
# samples) and asks which onsets repaint the frame. A stage-change onset is
# legitimate -- that is the cut to the next place. A subject onset that repaints
# >REFRAME_MAX of the frame is the defect: it is a new image wearing the old
# stage's clothes.
#
# There is deliberately no cap on the printed list. A truncated work-list reads
# as "covered everything" when it did not
# ([[a-capped-gate-list-truncates-a-work-list]]).

REFRAME_MAX = 0.30


def check_reframe(scene, beats):
    """Return the list of full-frame subject swaps inside a persistent stage.

    Each hit is (t, fraction, beat_label, [element ids]). `fraction` is how much
    of the frame changed; beat_label is the beat whose onset this is, so the
    fix can be located in the scene file without hunting.
    """
    import numpy as np
    import engine3 as E3

    els = list(getattr(scene, 'elements', []))
    if not els:
        return []

    # Which onsets belong to a stage (backdrop) change rather than a subject?
    def kinds_at(t, tol=0.01):
        return set((getattr(e, 'kind', '') or '') for e in els
                   if abs(float(e.at) - t) < tol)

    times = sorted(set(round(float(e.at), 3) for e in els))
    hits = []
    for t in times:
        # A stage swap is a real cut to a new place. Not the defect.
        if 'bg' in kinds_at(t):
            continue
        prev = max(0.0, t - 0.20)
        after = t + 0.20
        dur = float(scene.duration or beats[-1].get('end', 0.0))
        if after > dur:
            after = dur
        a = np.asarray(E3.render_frame(scene, prev).convert('RGB'), dtype=np.int16)
        b = np.asarray(E3.render_frame(scene, after).convert('RGB'), dtype=np.int16)
        frac = float((np.abs(a - b).max(axis=2) > 24).mean())
        if frac <= REFRAME_MAX:
            continue
        ids = sorted(e.id for e in els if abs(float(e.at) - t) < 0.01)
        # nearest beat label
        lab = 'b??'
        best = None
        for bt in beats:
            s = float(bt.get('start', 0.0))
            if best is None or abs(s - t) < abs(best - t):
                best, lab = s, bt.get('id') or bt.get('beat') or 'b??'
        hits.append((round(t, 2), round(frac, 3), str(lab), ids))
    hits.sort(key=lambda h: -h[1])
    return hits



# ---------------------------------------------------------------------------
# (e) MOTION -- is anything actually moving
# ---------------------------------------------------------------------------

def check_motion(scene, beats, fps=6):
    """Fraction of frames with a real change, and how much of it is motion.

    Returns (motion_fraction, still_fraction). A frame counts as MOTION if it
    differs from the previous frame by more than `still_thresh` of its pixels
    but the frame as a whole is NOT a repaint -- i.e. something small moved,
    rather than the whole set changing.
    """
    import numpy as np
    import engine3 as E3

    dur = float(scene.duration or beats[-1].get('end', 0.0))
    n = max(3, int(dur * fps))
    prev = None
    motion = still = 0
    for i in range(n):
        t = dur * i / float(n)
        fr = np.asarray(E3.render_frame(scene, t).convert('L'), dtype=np.int16)
        if prev is not None:
            frac = float((np.abs(fr - prev) > 12).mean())
            if frac > 0.30:
                still += 1            # a cut / full repaint, not motion
            elif frac > 0.0008:
                motion += 1
        prev = fr
    total = max(1, n - 1)
    return motion / float(total), still / float(total)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def run(chapter, per_beat=3, fps=6):
    scene, beats, mod = load(chapter)
    res = {'chapter': chapter, 'beats': len(beats)}

    res['fit'] = check_fit(scene, beats, per_beat)
    res['contrast'] = check_contrast(scene, beats, per_beat)
    frac, trun, trat, nocap = check_density(scene, beats)
    res['text_frac'] = frac
    res['text_run'] = trun
    res['text_run_end'] = trat
    res['text_free'] = len(nocap)
    res['cadence'], res['max_still'], res['repaints'] = check_cadence(scene, beats, fps)
    res['motion'], res['still'] = check_motion(scene, beats, fps)
    res['reframe'] = check_reframe(scene, beats)

    res['bad'] = []
    if res['fit']:
        res['bad'].append('FIT %d' % len(res['fit']))
    if res['contrast']:
        res['bad'].append('CONTRAST %d' % len(res['contrast']))
    if frac < TEXT_FRAC_MIN:
        res['bad'].append('TEXT %.0f%% TOO LOW' % (100 * frac))
    if frac > TEXT_FRAC_MAX:
        res['bad'].append('TEXT %.0f%% TOO HIGH' % (100 * frac))
    if trun > TEXT_RUN_MAX:
        res['bad'].append('TEXT RUN %d ->b%02d' % (trun, trat))
    if 0 <= res['cadence'] < GAP_MIN:
        res['bad'].append('CADENCE %.1fs (cutting every sentence)'
                          % res['cadence'])
    if res['max_still'] > STILL_MAX:
        res['bad'].append('STILL GAP %.0fs' % res['max_still'])
    if not (MOTION_FRAC_MIN <= res['motion'] <= MOTION_FRAC_MAX):
        res['bad'].append('MOTION %.0f%%' % (100 * res['motion']))
    if res['reframe']:
        res['bad'].append('REFRAME %d full-frame swaps inside a stage'
                          % len(res['reframe']))
    return res


def main(argv):
    selftest = '--selftest' in argv
    chaps = [a for a in argv if not a.startswith('-')] or CHAPTERS
    if selftest:
        return selftest_main()
    bad = 0
    for ch in chaps:
        if not os.path.exists(os.path.join(ROOT, 'segments', ch, 'beats.json')):
            print('%-11s no beats.json -- skip' % ch)
            continue
        try:
            r = run(ch)
        except Exception as exc:
            print('%-11s GATE FAILED: %s: %s' % (ch, type(exc).__name__, exc))
            bad += 1
            continue
        ok = not r['bad']
        if not ok:
            bad += 1
        print('%s %-11s %2d beats  text %3.0f%% (run %d)  cut %4.1fs/%-2d  '
              'still-gap %4.0fs  motion %2.0f%%  %s'
              % ('OK  ' if ok else 'GAP ', r['chapter'], r['beats'],
                 100 * r['text_frac'], r['text_run'], r['cadence'],
                 r['repaints'], r['max_still'],
                 100 * r['motion'],
                 ('  ' + '  '.join(r['bad'])) if r['bad'] else ''))
        for label, key in (('fit', 'fit'), ('contrast', 'contrast')):
            if r[key]:
                s = ','.join('b%02d@%.1fs' % (b, t) for b, t, *_ in r[key][:8])
                print('              %s: %s%s'
                      % (label, s, ',+%d' % (len(r[key]) - 8)
                         if len(r[key]) > 8 else ''))
        # The work-list. No cap: a truncated list reads as "covered everything".
        if r['reframe']:
            print('              reframe (%d full-frame swaps inside a stage):'
                  % len(r['reframe']))
            for t, frac, lab, ids in r['reframe']:
                print('                %-5s t=%-6.2f %3.0f%%  %s'
                      % (lab, t, 100 * frac, ' '.join(ids[:5])))
    print('\n%d chapter(s) with gaps' % bad)
    return 0


# ---------------------------------------------------------------------------
# --selftest: prove each check is not a no-op
# ---------------------------------------------------------------------------

def _fake_scene(caption_kw, beats):
    """A two-beat scene carrying one caption, for the self-test only."""
    import engine3 as E3
    import scene_common as SC

    def sky(tile, fw, fh):
        from PIL import ImageDraw
        ImageDraw.Draw(tile).rectangle([0, 0, fw, fh], fill=(236, 232, 220))

    els = [E3.E('bg', 'bg', sky, at=0.0)]
    els.append(SC.caption(**caption_kw))
    return E3.Scene(elements=els, title=None, duration=4.0)


def selftest_main():
    """Each check must FAIL on a frame that is broken on purpose.

    A gate that cannot be shown to fail is not a gate -- it is a comment that
    runs. This builds deliberately broken scenes and asserts the matching check
    catches each one.
    """
    from PIL import ImageDraw
    import engine3 as E3
    import scene_common as SC

    beats = [{'start': 0.0, 'end': 4.0, 'text': 'x'}]
    failures = []

    # (a) FIT: a caption WIDER than the frame. This is the trigger that works,
    # and finding out which trigger works matters, so the reasoning is kept.
    #
    # The obvious control -- a caption centred at cy=718, hanging off the bottom
    # -- does NOT fire, and that is a result rather than a test bug: caption()
    # clamps y so y+h <= 720-pad_y, and the probe shows any cy from 700 to 900
    # all resolve to ink at y 683..708, i.e. 11px clear of the edge. The bottom
    # clamp is solid, so a caption cannot be hung off the bottom edge.
    #
    # The clamp does NOT protect against WIDTH. Its x branch is
    #   if x < pad_x: x = pad_x
    #   elif x + w > 1280 - pad_x: x = 1280 - pad_x - w
    # which for a caption wider than the frame computes a NEGATIVE x, but the
    # first branch already won (x < pad_x is true for a very wide centred box),
    # so it pins x to pad_x and the tile simply overflows the RIGHT edge. Probed:
    # a caption with max_w=3000 lands ink at x 23..1279, clear=0, glyphs on the
    # border column. That is the real edge-clip defect and it is what this
    # control must reproduce.
    sc = _fake_scene(dict(text='THIS IS AN EXTREMELY LONG CAPTION THAT SHOULD '
                               'NOT FIT INSIDE THE FRAME AT ALL',
                          cx=640, cy=360, at=0.0, until=4.0, size=32,
                          max_w=3000), beats)
    hits = check_fit(sc, beats, per_beat=1)
    if not hits:
        failures.append('FIT: an over-wide caption was NOT flagged')
    print('%-9s control (caption wider than frame) -> %s'
          % ('FIT', 'FLAGGED %s' % hits if hits else 'MISSED'))

    # Negative: a normal-width caption must NOT be flagged (no false positive).
    sc = _fake_scene(dict(text='CENTRED PROPERLY', cx=640, cy=360,
                          at=0.0, until=4.0, size=32), beats)
    hits = check_fit(sc, beats, per_beat=1)
    if hits:
        failures.append('FIT: a centred caption was flagged %s' % hits)
    print('%-9s negative (normal caption at 360)   -> %s'
          % ('FIT', 'FLAGGED (false positive!)' if hits else 'clean'))

    # (b) CONTRAST.
    #
    # The control is the eye-confirmed cheyenne b03 defect: an INK caption on a
    # dark card, where the fill and the 2px INK keyline are the SAME colour, so
    # the glyph has no interior and reads as a smear.
    #
    # Note it bypasses SC.caption on purpose. The background resolver added to
    # caption() means INK-on-night can no longer be PRODUCED through the normal
    # path -- it is corrected before it reaches the frame. That is the fix
    # working, not the gate being unnecessary: a scene that draws its own text,
    # or a caption on a frame split light-behind/dark-in-front where the median
    # sample picks the wrong register, can still produce it. The gate is the
    # backstop for those, so the control has to be able to make the thing.
    def _dark_scene():
        def night(tile, fw, fh):
            ImageDraw.Draw(tile).rectangle([0, 0, fw, fh], fill=(28, 32, 44))

        def ink_text(tile, fw, fh):
            import v2type as T
            f = T.load_font(32, bold=True)
            s = 'A DARK ROOM, A DARK WORD'
            bb = ImageDraw.Draw(tile).textbbox((0, 0), s, font=f,
                                              stroke_width=2)
            ImageDraw.Draw(tile).text(
                (fw / 2.0 - (bb[2] - bb[0]) / 2.0, fh / 2.0 - 24), s,
                font=f, fill=SC.INK, stroke_width=2, stroke_fill=T.INK)
        els = [E3.E('bg', 'bg', night, at=0.0),
               E3.E('inktext', 'text', ink_text, at=0.0)]
        return E3.Scene(elements=els, title=None, duration=4.0)

    sc = _dark_scene()
    hits = check_contrast(sc, beats, per_beat=1)
    if not hits:
        failures.append('CONTRAST: INK-on-night was NOT flagged')
    print('%-9s control (INK fill==keyline on night) -> %s'
          % ('CONTRAST', 'FLAGGED %s' % [(h[0], h[2]) for h in hits]
             if hits else 'MISSED'))

    # Negative: a KEYLINED coloured caption on a mid background. This measured
    # 2.56:1 and was flagged by the ratio-only version, but by eye it is plainly
    # readable -- the black keyline supplies the edge. It must NOT be flagged.
    def _grey_scene():
        def sky(tile, fw, fh):
            ImageDraw.Draw(tile).rectangle([0, 0, fw, fh], fill=(128, 132, 140))
        els = [E3.E('bg', 'bg', sky, at=0.0)]
        els.append(SC.caption(text='RED ON MID GREY IS FINE', cx=640, cy=360,
                              at=0.0, until=4.0, size=32,
                              fill=(198, 48, 40)))
        return E3.Scene(elements=els, title=None, duration=4.0)

    sc = _grey_scene()
    hits = check_contrast(sc, beats, per_beat=1)
    if hits:
        failures.append('CONTRAST: a keylined red caption was flagged %s' % hits)
    print('%-9s negative (red+keyline on mid grey)   -> %s'
          % ('CONTRAST', 'FLAGGED (false positive!)' if hits else 'clean'))

    # (c) DENSITY: a caption on every beat is wall-to-wall text.
    sc = _fake_scene(dict(text='TEXT ON EVERY BEAT', cx=640, cy=360,
                          at=0.0, until=4.0, size=32), beats)
    frac, trun, trat, nocap = check_density(sc, beats)
    if frac <= TEXT_FRAC_MAX:
        failures.append('DENSITY: 100%% captioned measured %.0f%%' % (frac * 100))
    print('%-9s control (text on every beat)      -> %.0f%% (max %.0f%%)'
          % ('DENSITY', 100 * frac, 100 * TEXT_FRAC_MAX))

    # (d) CADENCE / (e) MOTION: a scene with no motion at all.
    sc = _fake_scene(dict(text='STATIC', cx=640, cy=360,
                          at=0.0, until=4.0, size=32), beats)
    cad, still_gap, ncut = check_cadence(sc, beats, fps=6)
    mot, still = check_motion(sc, beats, fps=6)
    if mot > MOTION_FRAC_MIN:
        failures.append('MOTION: a static scene measured %.0f%% motion'
                        % (100 * mot))
    print('%-9s control (nothing moves)          -> %.0f%% motion, %d cuts, '
          'still-gap %.1fs'
          % ('MOTION', 100 * mot, ncut, still_gap))

    print()
    if failures:
        for f in failures:
            print('SELFTEST FAIL: %s' % f)
        return 1
    print('SELFTEST OK: every check fires on its known-bad frame and stays '
          'quiet on the good one.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))