"""Find every label/bubble drawn in INK (near-black) on a DARK background.

The user rule is "text should never be gray or black because its hard to see."
That is not a contrast-ratio test -- a WCAG ratio gate flags perfectly readable
keylined gold-on-dark text (`keyline-is-the-contrast-not-the-fill`). The rule is
specifically about the FILL being near-black. v2draw.draw_label gives a non-INK
label a black keyline and an INK label NO keyline at all, so an INK fill is the
one case where the glyph itself has to carry the contrast against whatever is
behind it. On a dark register that is invisible.

So: flag a label when its fill is INK (or near-black) AND the median luminance
of the background actually rendered behind it is dark.

Run:  python lib/_audit_label_ink.py [chapter ...]
"""
import sys
import re
import statistics
import inspect

sys.path.insert(0, 'C:/VIBE_CODE_CENTRAL/Gauntlet3/work3/lib')
sys.path.insert(0, 'C:/VIBE_CODE_CENTRAL/Gauntlet3/work/lib')

from PIL import Image
import engine3 as E3
import scene_common as SC
import v2draw as D

W, H = 1280, 720
DARK_BG = 110.0     # median luminance below this = dark register
NEAR_BLACK = 90     # all channels under this = reads as black/gray
RING = 6            # px of background sampled around the glyph mask
# draw_label strokes a keyline of up to max(2, size*0.13) px around a non-INK
# label -- 5-6px at the sizes in use. Pad the glyph mask by this much before
# sampling the ring, or the keyline itself is counted as "background" and drags
# the median black. Derived from v2draw.draw_label's outline_w, not guessed.
KEYLINE_PAD = 8


def size_of(src, default=38):
    """The size= argument on the same draw_label call, if the call sets one.

    Needed because the solo re-render must reproduce the real glyph extent;
    guessing the size would build a mask that does not match the drawn text.
    """
    m = re.search(r'size=(\d+)', src)
    return int(m.group(1)) if m else default


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def audit(chapter):
    modname = SC.scene_mod(chapter)
    scene = __import__(modname)
    SCN = scene.build()

    def pal(name):
        # Dotted names MUST resolve. The scenes do not all define their palette
        # locally: svalbard2_scene writes color=VT.LABEL_YELLOW, which is a
        # v2type attribute reached through an imported module alias. A plain
        # getattr(scene, 'VT.LABEL_YELLOW') returns None, the old code fell
        # through to INK, and the gate then flagged six labels that are
        # (246,224,92) -- bright yellow -- as near-black on dark. That is the
        # `a-grey-guard-swallows-the-page-ink` failure in reverse: a gate that
        # silently mis-resolves its palette invents defects, and a gate with
        # invented defects is worse than no gate because every fix it suggests
        # is churn. Walk the dots.
        name = name.strip()
        obj = scene
        for part in name.split('.'):
            obj = getattr(obj, part, None)
            if obj is None:
                break
        if obj is None:
            obj = getattr(SC, name, None)
        if not (isinstance(obj, tuple) and len(obj) == 3):
            return SC.INK
        return obj

    out = []
    for el in SCN.elements:
        fn = getattr(el, 'draw', None) or getattr(el, 'fn', None)
        if fn is None:
            continue
        try:
            src = inspect.getsource(fn)
        except Exception:
            continue
        if 'draw_label' not in src and 'draw_bubble' not in src:
            continue
        calls = re.findall(
            r"draw_(?:label|bubble)\(\s*tile,\s*(.+?),\s*"
            r"center=\(([-\d.]+),\s*([-\d.]+)\)"
            # The colour group must accept a DOTTED path. It used to be (\w+),
            # which cannot match VT.LABEL_YELLOW, so every label written with a
            # module-qualified colour came back with color=None and was scored
            # as INK -- which is how six (246,224,92) yellow labels on svalbard
            # were reported as near-black on dark. A gate that mis-parses its
            # own subject invents defects; fix the parser, not the art.
            r"(?:,\s*color=([\w.]+))?", src)
        if not calls:
            continue
        t = (el.at or 0.0) + 0.05
        # The background is sampled from the FULL frame, with the element
        # PRESENT -- not from a render with the element removed.
        #
        # Removing the element was the original idea (see
        # title-band-gate-must-see-art-not-just-text) and it is wrong here.
        # Several labels are drawn by an element that FIRST paints its own
        # backing panel and THEN writes the text on it: fortknox h_sealed lays
        # a pale band across the top of the frame and puts 'NEVER BELOW IT' on
        # it; vatican lay20_shape draws the catalogue page and writes
        # 'CATALOGUED ONCE' across it. Drop the element and you drop the panel,
        # so the sampler reads the bare dark backdrop behind the card and calls
        # a perfectly legible dark-on-pale label 'dark on dark'. Eye-confirmed
        # on 2026-10-05: the element-removed fortknox frame is a uniform dark
        # field where the real frame shows pale text on a pale band.
        #
        # Render the element twice: once normally (full frame = what the viewer
        # sees) and once with the label's own ink suppressed is NOT possible
        # without re-implementing draw_label, so instead measure the ring in
        # the full frame and, to avoid counting the glyph's own keyline as
        # background, sample a ring that starts OUTSIDE the drawn mask.
        full = E3.render_frame(SCN, t)
        bg = full
        for text, cx, cy, colname in calls:
            cx, cy = float(cx), float(cy)
            fill = pal(colname) if colname else SC.INK
            if max(fill) >= NEAR_BLACK:
                continue          # not near-black -> the user's rule is satisfied
            half_w = max(40, len(text.strip("'")) * 11)
            x0, x1 = max(0, int(cx - half_w)), min(W, int(cx + half_w))
            y0, y1 = max(0, int(cy - 26)), min(H, int(cy + 26))
            if x1 <= x0 or y1 <= y0:
                continue
            # Measure the background AROUND THE GLYPHS, not a box median.
            #
            # The old version took the median luminance of a whole
            # len(text)*11 x 52 box. That box routinely straddles a
            # high-contrast boundary -- the title-strip edge at y~170, the
            # bottom edge of a document, the right edge of a card -- so the
            # median reported whichever side happened to be darker and the
            # gate flagged legible labels. Eye-checked false positives on
            # 2026-10-05, all one cause: fortknox 'NEVER BELOW IT' (INK on a
            # light grey band, box dipped into the black strip below), tomb
            # 'XI'AN'/'OUTSIDE' (INK on a white card, box ran off the card),
            # vatican 'CATALOGUED ONCE' (INK on a cream page, box dipped past
            # the page edge).
            #
            # So: draw the label ALONE on a black tile to recover its true
            # glyph mask, dilate that mask by a few px, and sample the real
            # background in that ring. The ring hugs the letterforms, so it
            # cannot reach across a boundary the glyphs themselves do not
            # cross. This is `title-band-gate-must-see-art-not-just-text` and
            # `judge-art-at-full-res` applied to the sampler.
            solo = Image.new('RGB', (W, H), (0, 0, 0))
            try:
                D.draw_label(solo, text.strip("'"), center=(cx, cy),
                             color=(255, 255, 255), size=size_of(src))
            except Exception:
                continue
            sp = solo.load()
            # Threshold LOW enough that the black KEYLINE drawn around a
            # non-INK label is counted as part of the glyph. If the keyline
            # leaked into the ring it would drag the median toward black and
            # re-create the false positive we are removing. On the black solo
            # tile a keyline is invisible, so we instead dilate the glyph mask
            # by KEYLINE_PAD below and start the ring outside that.
            glyph = {(x, y) for y in range(max(0, int(cy - 40)),
                                            min(H, int(cy + 40)))
                     for x in range(max(0, int(cx - half_w - 20)),
                                    min(W, int(cx + half_w + 20)))
                     if sum(sp[x, y]) > 90}
            for (gx, gy) in list(glyph):
                for ddx in range(-KEYLINE_PAD, KEYLINE_PAD + 1):
                    for ddy in range(-KEYLINE_PAD, KEYLINE_PAD + 1):
                        glyph.add((gx + ddx, gy + ddy))
            if not glyph:
                continue
            ring = set()
            for (gx, gy) in glyph:
                for ddx in range(-RING, RING + 1):
                    for ddy in range(-RING, RING + 1):
                        px_, py_ = gx + ddx, gy + ddy
                        if 0 <= px_ < W and 0 <= py_ < H \
                                and (px_, py_) not in glyph:
                            ring.add((px_, py_))
            bpx = bg.load()
            vals = [lum(bpx[px_, py_]) for (px_, py_) in ring]
            med = statistics.median(vals) if vals else 999.0
            if med < DARK_BG:
                out.append(dict(chapter=chapter, id=el.id, t=round(t, 2),
                                text=text.strip("'")[:26], cx=int(cx), cy=int(cy),
                                color=colname or 'INK', bg_lum=round(med, 1)))
    return out


if __name__ == '__main__':
    chaps = sys.argv[1:] or ['pinegap', 'room39', 'cheyenne', 'svalbard', 'vatican',
                             'fortknox', 'tomb', 'mezhgorye', 'area51']
    allbad = []
    for c in chaps:
        try:
            r = audit(c)
        except Exception as e:
            print('%-12s ERROR %s' % (c, e))
            continue
        allbad.extend(r)
        print('%-12s %d ink-on-dark labels' % (c, len(r)))
    print()
    for r in sorted(allbad, key=lambda r: (r['chapter'], r['id'])):
        print('%-11s %-20s %-26s %6s %5s  bglum=%5.1f' %
              (r['chapter'], r['id'], repr(r['text']), r['cx'], r['cy'], r['bg_lum']))
    print()
    print('TOTAL %d ink-on-dark labels across %d chapters' %
          (len(allbad), len({r['chapter'] for r in allbad})))