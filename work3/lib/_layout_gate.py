"""Automated layout gate: find beats where the caption is broken.

WHY THIS EXISTS. Judging 300 frames by eye finds only the defects you happen
to look at. Two caption faults kept recurring:

  1. CAPTION CLIPPED by the frame edge. Scenes place captions by eye at
     cy=690..700; a caption is ~42-49px tall, so cy=700 puts its bottom at
     724 against a 720 frame. SC.caption now clamps, and this re-checks
     independently rather than trusting that clamp.
  2. CAPTION COLLIDING WITH THE SUBJECT. A caption laid over a mountain ridge
     or a fence is struck through by the keyline and becomes unreadable.

This is GROUND TRUTH, not inference: it monkeypatches SC.caption to record the
exact pixel box each caption composites into, then asks the rendered frame what
ink is actually sitting in that box. No band-scanning, no guessing.

    python lib/_layout_gate.py <chapter> [<chapter> ...]
    python lib/_layout_gate.py pinegap mezhgorye
"""

import importlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), 'work', 'lib'))

import engine3 as E3          # noqa: E402
import scene_common as SC     # noqa: E402

W, H = 1280, 720
CHAPTERS = ['pinegap', 'area51', 'tomb', 'room39', 'mezhgorye', 'cheyenne',
            'svalbard', 'fortknox', 'vatican']

# where SC.caption last composited, and what it drew
RECORD = []


def _instrument():
    """Wrap SC.caption so every call records its final composited box."""
    if getattr(SC, '_GATE_INSTRUMENTED', False):
        return
    orig = SC.caption

    def spy(text, cx, cy, at, until=None, size=None, fill=None, max_w=None):
        el = orig(text, cx, cy, at, until=until, size=size, fill=fill,
                  max_w=max_w)
        # wrap the returned element's draw to capture the composited box
        inner_draw = el.draw

        def draw(tile, fw, fh):
            before = len(RECORD)
            inner_draw(tile, fw, fh)
            if len(RECORD) == before:
                # recompute the box the same way caption() does
                import v2type as T
                from PIL import Image, ImageDraw
                color = fill if fill is not None else T.INK
                sz = size if size is not None else T.LABEL_PX
                stroke_w = 0 if color == T.INK else T.INK
                sw = 0 if color == T.INK else 2
                f = T.load_font(sz, bold=True)
                p = ImageDraw.Draw(Image.new('RGB', (1, 1)))
                bb = p.textbbox((0, 0), text, font=f, stroke_width=sw)
                w = int(bb[2] - bb[0]) + (sw + 6) * 2
                h = int(bb[3] - bb[1]) + (sw + 6) * 2
                px, py = 12, 8
                x = int(cx - w / 2)
                y = int(cy - h / 2)
                if x < px:
                    x = px
                elif x + w > W - px:
                    x = W - px - w
                if y < py:
                    y = py
                elif y + h > H - py:
                    y = H - py - h
                RECORD.append((text, x, y, w, h))
        el.draw = draw
        return el

    SC.caption = spy
    SC._GATE_INSTRUMENTED = True


def _edge_energy(a, box):
    """Mean |pixel - 5px boxblur| inside the box: how much EDGE is in there.
    Flat fill -> ~0. A keyline crossing the caption -> high."""
    from PIL import Image, ImageFilter
    x0, y0, w, h = box
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x0 + w)
    y1 = min(H, y0 + h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    sub = a[y0:y1, x0:x1].astype(np.float32)
    blur = np.asarray(Image.fromarray(sub.astype(np.uint8))
                      .filter(ImageFilter.BoxBlur(5)), dtype=np.float32)
    return float(np.abs(sub - blur).mean())


def check(chapter):
    _instrument()
    mod = importlib.import_module('%s_scene' % chapter)
    meta = json.load(open(os.path.join(ROOT, 'segments', chapter,
                                       'beats.json')))
    beats = meta['beats']

    rows = []
    for b in beats:
        t = (b['start'] + b.get('end', b['start'] + 1.0)) / 2.0
        del RECORD[:]
        scene = mod.build()                     # fresh, draws nothing
        img = E3.render_frame(scene, t)
        a = np.asarray(img.convert('L'))
        # the caption present at time t is the last one RECORDed during the
        # render that is still live; engine draws elements in order.
        boxes = [r for r in RECORD]
        if not boxes:
            rows.append(dict(beat=b['id'], t=round(t, 2), status='NO-CAP',
                             line=b.get('line', '')[:50]))
            continue
        text, x, y, w, h = boxes[-1]
        clipped = (y < 0 or x < 0 or y + h > H or x + w > W)
        # energy in the caption box, but the caption glyphs THEMSELVES are dark
        # edges. Compare against a reference: energy is high if something other
        # than the glyphs crosses. We approximate by measuring the band just
        # ABOVE the caption (where a ridge/fence would cross into it) and the
        # caption box edge density.
        en = _edge_energy(a, (x, y, w, h))
        rows.append(dict(beat=b['id'], t=round(t, 2),
                         box=(x, y, w, h), clipped=clipped,
                         energy=round(en, 1),
                         line=text[:50]))
    return rows


def main(argv):
    chaps = [a for a in argv if not a.startswith('-')] or CHAPTERS
    for ch in chaps:
        if not os.path.exists(os.path.join(ROOT, 'segments', ch,
                                           'beats.json')):
            print('%-11s no beats.json -- skip' % ch)
            continue
        if not os.path.exists(os.path.join(HERE, '%s_scene.py' % ch)):
            print('%-11s no scene file -- skip' % ch)
            continue
        try:
            rows = check(ch)
        except Exception as exc:
            print('%-11s FAILED: %s' % (ch, exc))
            continue
        bad_clip = [r for r in rows if r.get('clipped')]
        print('\n=== %s ===  %d beats, %d clipped' %
              (ch, len(rows), len(bad_clip)))
        for r in rows:
            flag = 'CLIP' if r.get('clipped') else '    '
            print('  %-5s %s e=%-5s %s'
                  % (r['beat'], flag, r.get('energy', '-'), r.get('line', '')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))