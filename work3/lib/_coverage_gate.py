"""Coverage gate: does every beat of every chapter actually get art?

WHY THIS EXISTS. A scene that references fewer cards than the chapter has beats
does NOT crash -- it just quietly paints the first ten beats and then holds the
last card to the end of the segment. fortknox was caught exactly this way: 10
cards for 44 beats, `build()` returned a valid scene, and nothing complained.
A crash is loud and gets fixed; a silent 25%-coverage scene ships looking fine
in a preview and is three quarters of a chapter missing in the film.

WHAT IT MEASURES, AND WHY NOT SIMPLY "did an element start in this beat".
The first version counted art ONSETS per beat and reported pinegap as 31/34,
naming b02, b13, b24. All three were false alarms: each is a two-phrase beat
("Look at this place." / "There is nothing here.") where the SECOND phrase
correctly keeps the first phrase's card and only swaps the caption. That is
the phrase-level reveal working, not a hole.

So the gate now measures two different things:

  MISSING  the beat has no live art at all. Always a real bug.
  STALL    the beat has live art but nothing NEW started in it. Fine for one
           beat (a caption refresh), a defect in a run. The reference changes
           its visual every 1.0-1.67s (measure/REFERENCE_MEASUREMENTS.md);
           a run longer than STALL_MAX beats means the viewer is looking at a
           frozen card while the narrator moves on, which is the exact defect
           this gate was built to catch.

  RENDER   every beat's midpoint is actually composited. The window checks
           above never call a draw function, so a card whose body references an
           undefined bare name (the tomb agent hit a bare `PAGE`) passes them
           and crashes at render time instead. Default ON; --no-render skips.

    python lib/_coverage_gate.py                  # all chapters, with render
    python lib/_coverage_gate.py --no-render      # fast window scan only
    python lib/_coverage_gate.py pinegap fortknox

THREE CHECKS, AND THE THIRD ONE EXISTS BECAUSE THE FIRST TWO WERE BOTH GREEN ON
A REAL DEFECT. The source scan (title_collisions) reads the scene as TEXT and can
only see constructs a human wrote by hand -- a draw_title call, a cap() at a low y.
It cannot see a LINE a card drew. pinegap b28 drew a radio antenna up to y=-29,
striking through the persistent title, and the source scan called the chapter
clean. band_intrusions() closes that by comparing each frame's title strip
against the per-pixel MEDIAN strip across the chapter: the title is drawn with a
deterministic per-letter wobble so it is byte-identical on every frame, and
anything that differs from the median is card art in the one band that is not
ours to draw in.
"""

import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), 'work', 'lib'))

import scene_common as SC     # noqa: E402
import v2type as T            # noqa: E402

# The persistent title band, measured off v2type. engine3 stamps the chapter
# title on every frame AFTER every element, so nothing else may sit here.
TITLE_BAND_BOTTOM = T.TITLE_BAND_BOTTOM
SAFE_TOP = T.SAFE_TOP

CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']

# Longest run of beats that may show the SAME card before it counts as a stall.
# One is legitimate (a beat whose two phrases share a card); the reference
# changes its visual every 1.0-1.67s, so 3 in a row is already behind it.
STALL_MAX = 2


def cover(chapter):
    """Rebuild the scene and classify each beat as painted / held / missing."""
    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    meta = json.load(open(os.path.join(ROOT, 'segments', chapter,
                                       'beats.json')))
    beats = meta['beats']
    n = len(beats)

    # Art elements, with their liveness windows. `kind` is the discriminator --
    # Elements carry no name (the first attempt matched on a `card*` name that
    # engine3 does not set, and reported 0 painted for every chapter).
    art, caps = [], []
    for el in scene.elements:
        kind = getattr(el, 'kind', '') or ''
        if kind == 'bg':
            continue
        at = float(getattr(el, 'at', 0.0) or 0.0)
        until = getattr(el, 'until', None)
        until = float(until) if until is not None else None
        (caps if kind == 'text' else art).append((at, until))

    def live(items, t):
        for at, until in items:
            if at <= t + 1e-6 and (until is None or t < until - 1e-9):
                return True
        return False

    painted, held, missing, nocap = [], [], [], []
    for i, b in enumerate(beats):
        mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        if not live(art, mid):
            missing.append(i + 1)
        elif any(at <= mid + 1e-6 and (u is None or mid < u - 1e-9)
                 and at >= b['start'] - 1e-6 for at, u in art):
            painted.append(i + 1)
        else:
            held.append(i + 1)
        if not live(caps, mid):
            nocap.append(i + 1)

    # longest run of consecutive held-or-missing beats (the freeze)
    gap = set(held) | set(missing)
    run = best = 0
    run_at = 0
    for i in range(1, n + 1):
        if i in gap:
            run += 1
            if run > best:
                best, run_at = run, i
        else:
            run = 0

    return dict(chapter=chapter, beats=n, painted=len(painted),
                held=len(held), captioned=len(beats) - len(nocap),
                missing=missing, nocap=nocap,
                stall=best, stall_end=run_at,
                duration=round(float(meta.get('duration_s') or scene.duration), 1))


def render_beats(chapter):
    """Actually RENDER every beat's midpoint and report any that raise.

    WHY THIS EXISTS. The coverage classification above only inspects element
    WINDOWS -- it never calls a draw function. So a card whose body references
    a bare module name that was never defined (the tomb agent found `_crane`
    and `c_break` reaching for a bare `PAGE`) passes the window check and the
    gate prints OK, then crashes at render time when that card is finally
    composited. The fix is to render, not to inspect.

    Returns a list of (beat_no, 'ExcType: msg') for beats that raise.
    """
    importlib.invalidate_caches()
    import engine3 as E3
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    meta = json.load(open(os.path.join(ROOT, 'segments', chapter,
                                       'beats.json')))
    fails = []
    for i, b in enumerate(meta['beats'], 1):
        mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        try:
            E3.render_frame(scene, mid)
        except Exception as exc:
            fails.append((i, '%s: %s' % (type(exc).__name__, exc)))
    return fails


def band_intrusions(chapter):
    """Report beats whose ART (not a caption, not a draw_title) enters the title band.

    WHY THIS IS SEPARATE FROM title_collisions(). That function is a source scan
    for two specific constructs: a `D.draw_title(...)` call and a `cap(...)`
    placed too high. Both are text the builder positioned by hand. Neither can
    see a LINE the card drew.

    That hole shipped a real defect. pinegap's b28 radio icon drew its whip
    antenna to cy - s*1.15; at the only call site (cy=350, s=330) that is y=-29,
    so the stroke ran from the icon clean off the top of the frame and struck
    through the persistent "Pine Gap" title. title_collisions() reported pinegap
    clean. Found by eye, on a frame pulled out of the RENDERED mp4.

    HOW IT DETECTS IT. Three failed approaches first, all recorded so they are
    not retried:
      * Comparing each frame's title strip to the per-pixel MEDIAN strip across
        the chapter. Assumed the title (deterministic per-letter wobble) was
        byte-identical every frame, so the median would be "title, no art". But
        the painted PAPER WASH under the title is regenerated per frame, so every
        frame's strip differed from the median and all 34 pinegap beats flagged.
        A gate that flags everything is worse than no gate.
      * Comparing consecutive frames. Same problem -- the wash moves every frame.
      * Flagging "dark pixel in the band that is not under the title glyphs".
        False-positived on pinegap b34, a night card whose ENTIRE background is
        near-black: on a dark card almost every band pixel is "dark and not a
        glyph", so the card flagged 79k pixels with nothing crossing the title.
        This is the dark-background register trap (memory
        register-aware-style-gate): an absolute darkness test measures the card's
        BACKGROUND, not the art.

    * Diffing a bg-only render against a full render to isolate "ink". Also
        garbage, and for a dumber reason: the paper wash is regenerated per
        render CALL, so two renders at the same t have different backgrounds and
        the diff is noise everywhere (32 of 34 beats flagged). Anything that
        renders the scene twice and compares cannot work here.

    What actually works: ignore the title's own pixels (mask), then ask which
    pixels in the title's bounding box DISAGREE with the local background. The
    background is estimated as the SPATIAL median of the non-title pixels in the
    same rect -- a within-frame estimate, which is robust because art crossing
    the title is a minority of the rect and the wash blotches are too small to
    move a median.

    Note the earlier "compare to the median" attempt failed and this is not it:
    that one took the median ACROSS FRAMES, and the paper wash is regenerated per
    frame, so every frame differed. This takes the median WITHIN one frame, which
    the wash does not defeat.

    Deviation is measured in BOTH directions. A black outline on a light page is
    darker than its background; cream linework on a night card is lighter. Only
    testing "darker" would have missed the whole night-card register.

    WHY THE OLD DARK-CARD GUARD WAS DELETED, NOT KEPT AS A FALLBACK. It skipped any
    beat whose title-rect background was darker than ~150 greyscale, on the theory
    that on a night card the band is uniformly dark and darkness measures nothing.
    That theory was right and the threshold was wrong. tomb b14 is a LIGHT card --
    grey paper with a terracotta map -- but the map fills the title rect, and
    terracotta's greyscale luminance is ~110, under the threshold. So the guard
    skipped exactly the card it existed to protect, and b14 shipped with the map's
    black outline struck through "The Terracotta Army". A guard that hides a
    confirmed defect is worse than no guard, so the skip is gone entirely and the
    spatial-median test runs on every beat.

    Returns a list of (beat_no, 'Npx') for offending beats.
    """
    import importlib
    import engine3 as E3
    import numpy as np

    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    meta = json.load(open(os.path.join(ROOT, 'segments', chapter,
                                       'beats.json')))

    import v2type as _T
    cap = _T.TITLE_CAP_PX
    base = _T.TITLE_BASELINE_Y
    ty0 = max(0, base - int(cap * 1.25))
    ty1 = base + 6
    tw = min(620, int(11 * cap * 0.62))
    tx0 = max(0, _T.TITLE_CENTER_X - tw // 2)
    tx1 = min(1280, _T.TITLE_CENTER_X + tw // 2)

    # Mask of the pixels the title itself owns, on a blank page, dilated.
    blank = E3._blank_page()
    if scene.title:
        E3._draw_title(blank, scene.title, seed=scene.title_seed)
    tb = np.asarray(blank.convert('L'))
    title_mask = tb < 128
    for _ in range(4):
        d = title_mask.copy()
        d[1:, :] |= title_mask[:-1, :]
        d[:-1, :] |= title_mask[1:, :]
        d[:, 1:] |= title_mask[:, :-1]
        d[:, :-1] |= title_mask[:, 1:]
        title_mask = d

    # CALIBRATION -- THIS NUMBER WAS WRONG AT 55 AND WAS FIXED AT 25.
    #
    # 55 was fitted against the first defects found, which were all high-contrast:
    # a black outline on cream paper (tomb b14's map), a black antenna on a pale
    # sky (pinegap b22). Those deviate by 100+ levels, so 55 looked like a safe
    # margin below them.
    #
    # Then a contact sheet of all nine title bands -- the check nobody had done,
    # because every gate so far reported zero problems -- showed svalbard's bunker
    # hatch struck straight through "Svalbard", room39's red datum line through
    # "Object 739", and cheyenne's blast-door frame across "Cheyenne Mountain".
    # Re-measured, svalbard b18 has 2777 pixels deviating by more than 25 and
    # ZERO deviating by more than 55. The threshold was not conservative, it was
    # blind: it could only see defects that happen to be high-contrast, which is
    # a property of the accidents we happened to find first, not of the defect
    # class.
    #
    # 25 was then checked the other way, which is the direction that actually
    # matters -- does it fire on things that are FINE? Ten of the highest-scoring
    # frames were pulled and looked at, across the four chapters it flags
    # (room39 6, cheyenne 4, svalbard 3, fortknox 1). All ten are real
    # intrusions. Zero false positives. So 25 is not a loosened threshold
    # trading precision for recall; it is the correct threshold, and 55 was
    # under-reporting.
    #
    # The lesson is the one from [[pixel-gate-fires-on-stars]] applied in the
    # opposite direction: there, the gate fired on real-looking speckle and the
    # fix was to loosen it. Here the gate was silent on confirmed defects and the
    # fix was to tighten it. In both cases the arbiter was eye-confirmed frames,
    # never the intuition about what the number "should" be.
    DEV = 25
    MINPX = 40

    # A chapter may declare a deliberate title BACKDROP. This is not a way to
    # hide art, and the narrowness is the whole point:
    #
    #   * the chapter must expose `TITLE_BACKDROP = (y_top, y_bottom)`, and that
    #     span must sit ENTIRELY inside the title band. A backdrop that reaches
    #     below the band is art, and art is what this check is for.
    #   * only rows within that span are excused, and only as a whole row: a
    #     pixel is forgiven if its entire horizontal run across the rect agrees
    #     with the backdrop. A stroke, an outline, a shape edge or a glyph always
    #     breaks that agreement somewhere along its length, so it still fires.
    #
    # vatican is the only chapter that needs this. Its `_lintel` is a warm
    # mid-tone stone course whose entire purpose is to give the engine's
    # hardcoded-INK title something to read against on a near-black card -- the
    # engine draws the title unconditionally and cannot be changed for one
    # chapter, so the support has to live in the art. Flagging it is the gate
    # flagging its own remedy. Verified by disabling the lintel outright: the
    # b16 score went 222 -> 0, so the courses are the whole of the signal.
    backdrop = getattr(mod, 'TITLE_BACKDROP', None)
    band_lo, band_hi = None, None
    if backdrop:
        y0, y1 = int(backdrop[0]), int(backdrop[1])
        if ty0 <= y0 < y1 <= ty1:
            band_lo, band_hi = y0 - ty0, y1 - ty0

    hits = []
    for i, b in enumerate(meta['beats'], 1):
        mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        fr = E3.render_frame(scene, mid).convert('L')
        a = np.asarray(fr, dtype=np.int16)
        rect = a[ty0:ty1, tx0:tx1]
        mrect = title_mask[ty0:ty1, tx0:tx1]
        bgpix = rect[~mrect]
        if bgpix.size == 0:
            continue
        bg_level = float(np.median(bgpix))
        off = ~mrect
        ink = off & (np.abs(rect - bg_level) > DEV)
        if band_lo is not None:
            # Excuse a row only where the WHOLE row is uniform. Anything with
            # structure in it -- a stroke crossing, a glyph, an edge -- survives,
            # which is what keeps this from being a blanket exemption.
            rows = np.arange(rect.shape[0])
            inband = (rows >= band_lo) & (rows <= band_hi)
            for r in np.nonzero(inband)[0]:
                row = rect[r][off[r]]
                if row.size == 0:
                    continue
                lo, hi = row.min(), row.max()
                if hi - lo <= DEV:
                    ink[r] = False
        n = int(ink.sum())
        if n > MINPX:
            hits.append((i, n))
    return hits


def title_contrast(chapter):
    """Beats where the persistent title does not read against its background.

    A SEPARATE check from `band_intrusions`, because it is a different failure
    and neither implies the other. Intrusion is art crossing the band; low
    contrast is the band being the wrong VALUE for the title that sits on it.
    A card can be perfectly clean of intrusions and still have an invisible title,
    and every chapter here did.

    The mechanism is in v2draw._wobble_glyph: it hardcodes fill=T.INK, and the
    engine draws the title unconditionally, so the title is always near-black.
    That is fine on the paper register and unreadable on a night card. vatican
    already answers this with its `_lintel` backdrop (see band_intrusions); the
    other dark chapters have no equivalent and simply ship a black title on a
    near-black sky.

    MEASUREMENT. Absolute WCAG contrast, NOT a ratio against the background.
    Two earlier attempts at a relative measure were both wrong in opposite
    directions and both had to be discarded by looking at frames:
      - |ink-bg|/max(1,bg) reads 0.47 "healthy" on a card where the title is
        visibly invisible, because dividing by a small background inflates any
        small absolute difference into a large-looking ratio;
      - mean WCAG luminance over every masked pixel reads ~1.0 for ALL NINE
        chapters, including pinegap where the title is plainly crisp, because
        the mask is dilated and so averages real stroke with anti-aliased edge.

    This version compares the CORE of the glyph strokes against the median of the
    unmasked background, taking the darkest decile of stroke pixels rather than a
    mean (a mean is dragged around by the edge pixels), and it is calibrated by
    eye: on the all-chapters contact sheet, Pine Gap / The Terracotta Army /
    Cheyenne Mountain / The Vatican Archives are comfortably readable, while
    Area 51, Object 739, Mezhgorye and Fort Knox are not.

    THRESHOLD IS 2.0, NOT THE USUAL 3.0 OR 4.5. Those come from WCAG and are
    calibrated for BODY text. This is a 46px display title where 2.9 is plainly
    comfortable -- vatican b02 measures 2.93 against its lintel and is the most
    legible title in the film, while pinegap b34 measures 1.20 and is genuinely
    hard to read. The four eye-confirmed cases land at 1.14 / 1.18 / 1.20 / 2.93,
    so 2.0 separates them with margin on both sides. Copying a body-text
    threshold here would have failed vatican, which has a working backdrop
    solution already, and that is exactly the failure mode this check exists to
    catch: a chapter doing the right thing being reported as broken.
    """
    import importlib
    import engine3 as E3
    import numpy as np

    importlib.invalidate_caches()
    mod = importlib.import_module('%s_scene' % chapter)
    scene = mod.build()
    meta = json.load(open(os.path.join(ROOT, 'segments', chapter,
                                       'beats.json')))

    import v2type as _T
    cap = _T.TITLE_CAP_PX
    base = _T.TITLE_BASELINE_Y
    ty0 = max(0, base - int(cap * 1.25))
    ty1 = base + 6
    tw = min(620, int(11 * cap * 0.62))
    tx0 = max(0, _T.TITLE_CENTER_X - tw // 2)
    tx1 = min(1280, _T.TITLE_CENTER_X + tw // 2)

    blank = E3._blank_page()
    if scene.title:
        E3._draw_title(blank, scene.title, seed=scene.title_seed)
    tb = np.asarray(blank.convert('L'))
    # The CORE of the strokes: threshold low (120) and do NOT dilate. Edge
    # pixels are exactly what destroyed the mean-based attempt.
    core = tb < 120

    def _lin(v):
        c = v / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    hits = []
    for i, b in enumerate(meta['beats'], 1):
        mid = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        fr = E3.render_frame(scene, mid).convert('RGB')
        a = np.asarray(fr, dtype=np.uint8)
        rect = a[ty0:ty1, tx0:tx1]
        mrect = core[ty0:ty1, tx0:tx1]
        bgpx = rect[~mrect]
        stroke = rect[mrect]
        if bgpx.size == 0 or stroke.size < 40:
            continue
        med = np.median(bgpx, axis=0).astype(np.float64)
        # darkest decile of the stroke pixels = the glyph core
        g = stroke.mean(axis=1).astype(np.float64)
        corepix = stroke[g <= np.percentile(g, 10)].mean(axis=0)
        lb = float(0.2126 * _lin(med[0]) + 0.7152 * _lin(med[1])
                   + 0.0722 * _lin(med[2]))
        li = float(0.2126 * _lin(corepix[0]) + 0.7152 * _lin(corepix[1])
                   + 0.0722 * _lin(corepix[2]))
        ratio = (max(li, lb) + 0.05) / (min(li, lb) + 0.05)
        if ratio < 2.0:
            hits.append((i, round(ratio, 2)))
    return hits


def title_collisions(chapter):
    """Report in-card draw_title calls and captions that hit the title band.

    engine3 stamps the persistent scene title on EVERY frame, drawn last, on top
    of the art -- there is no band reserved for it. Two failure modes, both hit
    in the bunkers build:

      * a card draw function calling D.draw_title renders a second title UNDER
        the engine's own, and the two overprint into a smear (cheyenne b04).
      * a caption placed too high crowds the glyphs (nine fortknox captions at
        cy 64-112).

    This is a source-level check, so it is cheap and needs no render. It reads
    the scene module as text rather than inspecting built elements, because the
    caption y is a literal at the append site and the draw_title call is a call.

    Returns a list of (line_no, 'kind: detail') strings.
    """
    src_path = os.path.join(HERE, '%s_scene.py' % chapter)
    src = open(src_path, encoding='utf-8').read().splitlines()
    hits = []
    for i, line in enumerate(src, 1):
        stripped = line.strip()
        # skip the module docstring / comments that only MENTION draw_title
        if stripped.startswith('#') or stripped.startswith('"""'):
            continue
        if 'D.draw_title(' in stripped or 'v2draw.draw_title(' in stripped:
            hits.append((i, 'in-card draw_title underprints the title strip'))
        # A caption appended as cap(beat, x, cy, size=S) has its cap top at
        # roughly cy - 0.75*S. Flag it when that top edge reaches into the title
        # band. Comparing cy to a flat constant cried wolf on the borderline
        # cases (cy=90 size=32 -> top 66, two pixels of clearance), so compute
        # the real top edge from the size the caption was actually given.
        m = re.search(r'\bcap\(\s*\d+\s*,\s*[^,]+,\s*(\d+)\s*,'
                      r'(?:\s*size\s*=\s*(\d+))?', stripped)
        if m:
            cy = int(m.group(1))
            size = int(m.group(2)) if m.group(2) else 32
            top = cy - 0.75 * size
            if top < TITLE_BAND_BOTTOM + 4:
                hits.append((i, 'caption top=%.0f (cy=%d size=%d) enters title '
                                 'band ending %d' % (top, cy, size,
                                                     TITLE_BAND_BOTTOM)))
    return hits


def _fmt(ids, limit=14):
    if not ids:
        return ''
    head = ','.join('b%02d' % b for b in ids[:limit])
    return head + (',...' if len(ids) > limit else '')


def main(argv):
    chaps = [a for a in argv if not a.startswith('-')] or CHAPTERS
    do_render = '--no-render' not in argv
    bad = 0
    for ch in chaps:
        if not os.path.exists(os.path.join(ROOT, 'segments', ch,
                                           'beats.json')):
            print('%-11s no beats.json -- skip' % ch)
            continue
        if not os.path.exists(os.path.join(HERE, '%s_scene.py' % ch)):
            print('%-11s no scene -- skip' % ch)
            continue
        try:
            r = cover(ch)
        except Exception as exc:
            print('%-11s BUILD FAILED: %s: %s'
                  % (ch, type(exc).__name__, exc))
            bad += 1
            continue
        # RENDER every beat -- the window check above cannot see a draw-time
        # crash (a card body referencing an undefined bare name). Default ON;
        # --no-render skips it when you only want the fast window scan.
        rfail = []
        if do_render:
            try:
                rfail = render_beats(ch)
            except Exception as exc:
                print('%-11s RENDER HARNESS FAILED: %s: %s'
                      % (ch, type(exc).__name__, exc))
                rfail = [(0, '%s: %s' % (type(exc).__name__, exc))]
        stalls = r['stall'] > STALL_MAX
        # Title-band check is source-level and cheap; always run it.
        tbhits = title_collisions(ch)
        # Plus the render-level check that can see in-card ART crossing the band
        # (a line, a shape) which the source scan above cannot see at all.
        try:
            bhits = band_intrusions(ch)
        except Exception as exc:
            bhits = [(0, 'BAND HARNESS FAILED: %s: %s'
                      % (type(exc).__name__, exc))]
        # Every returned hit is a real one. The old 'darkcard-skip' entry point is
        # gone, so there is nothing to filter and no separate night-card count --
        # night cards are checked by the same spatial-median test now.
        real_bhits = bhits
        # Title READABILITY, which is a different failure from intrusion: a card
        # can be perfectly clear of art in the band and still have an invisible
        # title, because the engine hardcodes the title fill to near-black.
        try:
            chits = title_contrast(ch)
        except Exception as exc:
            chits = [(0, 'CONTRAST HARNESS FAILED: %s: %s'
                      % (type(exc).__name__, exc))]
        ok = (not r['missing'] and not r['nocap'] and not stalls
              and not rfail and not tbhits and not real_bhits and not chits)
        flag = 'OK  ' if ok else 'GAP '
        if not ok:
            bad += 1
        rend = ''
        if rfail:
            rend = '  RENDER CRASH: ' + ','.join(
                'b%02d(%s)' % (b, e.split(':')[0]) for b, e in rfail[:6])
            if len(rfail) > 6:
                rend += ',+%d' % (len(rfail) - 6)
        tb = ''
        if tbhits:
            tb = '  TITLE BAND: ' + ','.join(
                'L%d(%s)' % (ln, d.split('(')[0].strip())
                for ln, d in tbhits[:4])
            if len(tbhits) > 4:
                tb += ',+%d' % (len(tbhits) - 4)
        if real_bhits:
            tb += '  BAND ART: ' + ','.join(
                ('HARNESS' if b == 0 else 'b%02d' % b) for b, d in real_bhits[:6])
            if len(real_bhits) > 6:
                tb += ',+%d' % (len(real_bhits) - 6)
        if chits:
            tb += '  TITLE UNREADABLE: ' + ','.join(
                ('HARNESS' if b == 0 else 'b%02d' % b) for b, d in chits[:6])
            if len(chits) > 6:
                tb += ',+%d' % (len(chits) - 6)
        print('%s %-11s %2d new  %2d held  %2d/%-2d captioned  %5.1fs%s%s%s%s%s'
              % (flag, r['chapter'], r['painted'], r['held'],
                 r['captioned'], r['beats'], r['duration'],
                 ('  STALL %d beats ->b%02d' % (r['stall'], r['stall_end']))
                 if stalls else '',
                 ('  NO ART: ' + _fmt(r['missing'])) if r['missing'] else '',
                 ('  NO CAP: ' + _fmt(r['nocap'])) if r['nocap'] else '',
                 rend, tb))
    print('\n%d chapter(s) with gaps' % bad)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))