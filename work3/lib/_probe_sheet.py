"""Render shape primitives at the sizes they are ACTUALLY CALLED at, so a
contact sheet can be judged by eye.

Three harness mistakes this replaces, each of which produced confident
nonsense:

  1. Guessing arguments from parameter NAMES left half the sheet UNCALLABLE.
     A blank tile looks exactly like "this primitive draws nothing", so it
     invents defects. Dispatch is now by signature shape.
  2. Rendering every primitive at ONE guessed scale makes architecture look
     wrong -- `_archway` at w=99 reads as a beehive; at its real w=420 it is a
     perfectly good doorway. Every primitive is now sized from a real call site
     scraped out of the chapter's scene files.
  3. Reporting a count without saying how many failed to render, which is how
     a mostly-empty sheet gets read as a clean bill of health. The header now
     carries the failure count.

Usage:  python lib/_probe_sheet.py <chapter> [outprefix]
"""
import os, sys, re, ast, inspect, importlib, collections, functools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join('..', 'work', 'lib'))

from PIL import Image, ImageDraw, ImageFont

# Primitives are authored against a 1280x720 FRAME, so each one is rendered
# into a full-size frame and only then scaled down for the sheet. Rendering
# them into a 320x250 tile put every real call-site coordinate (x=560, y=446)
# outside the canvas, which looks identical to a primitive that draws nothing.
FW, FH = 1280, 720
TW, TH = 400, 225          # scaled tile
COLS, ROWS = 3, 3
PAD = 6
# MID-TONE, not paper. Two chapters' primitives drew near-white fills on a
# near-white sheet and reported as "draws nothing": `_snow_cap` (SNOW) and
# `_ghost_lines` (216,210,196). Both were fine art on an invisible background.
# A mid grey is visible to light fills and dark fills alike.
BG = (126, 128, 130)


def load_font(px):
    for nm in ('comicbd.ttf', 'consolab.ttf', 'arialbd.ttf'):
        p = os.path.join('C:\\Windows\\Fonts', nm)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except Exception:
                pass
    return ImageFont.load_default()


def scrape_calls(chapter, prim, gvars, src):
    """Find real `prim(...)` calls in ONE scene file and return their argument
    lists. These are the sizes that matter.

    The calls are NOT literal -- scene code passes colour constants and frame
    sizes by name (`INK`, `SNOW`, `H`, `seed`) -- so each argument is compiled
    and evaluated against that module's globals rather than run through
    ast.literal_eval, which fails on every one of them.
    """
    found = []
    p = os.path.join('lib', src + '.py')
    if os.path.exists(p):
        try:
            tree = ast.parse(open(p, encoding='utf-8').read())
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == prim):
                    continue
                pos, kw, ok = [], {}, True
                # The first positional is the draw target (`d` / `tile`), which
                # is a local and not in globals. Skip it -- render_prim supplies
                # the real draw object. Evaluating it is what made every single
                # call look non-literal.
                for a in node.args[1:]:
                    try:
                        pos.append(eval(
                            compile(ast.Expression(a), '<c>', 'eval'), gvars))
                    except Exception:
                        ok = False
                        break
                if ok:
                    for k in node.keywords:
                        try:
                            kw[k.arg] = eval(
                                compile(ast.Expression(k.value), '<c>', 'eval'),
                                gvars)
                        except Exception:
                            pass
                if not ok:
                    pos = None
                found.append((pos, kw))
    return found


SKIP = re.compile(r'_(mass|strata|shards|facets|scree|creases|contours|'
                  r'crystal|overlay|texture|glow|beam|ridge|paper)$')

# Primitives that COMPUTE geometry rather than draw it. These have no image to
# show, and forcing them onto a sheet just manufactures phantom defects.
NO_DRAW = re.compile(r'_(pts|points|path|poly|geom|coords|shape|curve)$')

# Synthesized arguments for primitives whose call sites could not be evaluated.
# This exists because a primitive the sheet cannot draw is a primitive the audit
# cannot see -- and a wrong-object bug is invisible in source, so a blind spot
# here is exactly where one would survive to the final render.
#
# Order of preference per parameter: (1) the signature's own default, (2) a
# value from this table keyed on the parameter name, (3) a bare int 1.
_SYNTH = {
    'cx': 640, 'x': 640, 'x0': 380, 'x1': 900, 'ax': 480, 'bx': 800,
    'cy': 380, 'y': 380, 'y0': 240, 'y1': 540, 'ay': 290, 'by': 470,
    'w': 280, 'width': 280, 'rw': 140, 'bw': 200,
    'h': 320, 'height': 320, 'hh': 160, 'bh': 200,
    'r': 130, 'rad': 130, 'radius': 130, 'rr': 130, 'size': 280,
    'seed': 0, 's': 1.0, 'scale': 1.0, 'k': 1.0, 'amp': 40.0,
    'n': 7, 'count': 7, 'rows': 3, 'cols': 5, 'steps': 7, 'num': 6,
    't': 0.5, 't0': 0.0, 't1': 1.0, 'dur': 1.0, 'alpha': 255,
    'depth': 120, 'thick': 6, 'gap': 40, 'step': 34, 'off': 0,
    'phase': 0.0, 'span': 3.14159, 'a0': 0.0, 'a1': 3.14159,
}
_SYNTH_COLOR = (196, 150, 88)
_SYNTH_INK = (24, 24, 28)
_SYNTH_COLOR_NAMES = ('col', 'color', 'c', 'fill', 'fc', 'fg', 'tint', 'hue',
                      'base', 'body', 'wall', 'sky', 'accent', 'a')


def synth_args(fn):
    """Invent a plausible argument list from the primitive's own signature.

    Stamped SYNTH on the sheet, always. The harness has already learned the hard
    way that a wrong SCALE invents defects -- an archway at w=99 reads as a
    beehive -- so a SYNTH tile answers "is this the right OBJECT", never
    "is this the right SIZE". Only NOCALL tiles are silent holes.
    """
    out, kw = [], {}
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError):
        return None
    for i, p in enumerate(params):
        if i == 0:
            continue                      # the draw target; render_prim supplies it
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is not p.empty:
            val = p.default
        else:
            n = (p.name or '').lower()
            if n in _SYNTH:
                val = _SYNTH[n]
            elif n in _SYNTH_COLOR_NAMES:
                val = _SYNTH_COLOR
            elif 'ink' in n or 'line' in n or 'stroke' in n:
                val = _SYNTH_INK
            elif p.annotation is int or n.endswith(('_px', '_count')):
                val = 120
            elif p.annotation is float:
                val = 1.0
            else:
                val = 1
        if p.kind == p.KEYWORD_ONLY:
            kw[p.name] = val
        else:
            out.append(val)
    return (out, kw)


def render_prim(fn, call):
    """Draw one primitive into a fresh tile using a real call's arguments."""
    tile = Image.new('RGB', (FW, FH), BG)
    d = ImageDraw.Draw(tile)
    if call is None or call[0] is None:
        return tile, 'NOCALL'
    pos, kw = call
    status = ''
    try:
        first = fn.__code__.co_varnames[0]
        if first in ('tile', 'img', 'image'):
            fn(tile, *pos, **kw)
        else:
            fn(d, *pos, **kw)
    except TypeError:
        status = 'SIG'
    except Exception as e:
        status = type(e).__name__
    return tile.resize((TW, TH), Image.LANCZOS), status


def main():
    chapter = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else chapter
    base = importlib.import_module('%s_scene' % chapter)

    cands = []
    for nm, fn in vars(base).items():
        if not nm.startswith('_') or nm.startswith('__') or not callable(fn):
            continue
        if SKIP.search(nm) or NO_DRAW.search(nm):
            continue
        cands.append((nm, fn))
    cands.sort()

    font = load_font(15)
    lf = load_font(13)

    tiles = []
    # evaluate each scene file's calls against THAT file's globals, because the
    # 2_scene modules rebind names (colours, sizes) the base module does not.
    gvars_map = {}
    for src in ('%s_scene' % chapter, '%s2_scene' % chapter):
        try:
            m = importlib.import_module(src)
            gvars_map[src] = dict(vars(m))
        except Exception:
            gvars_map[src] = {}

    for nm, fn in cands:
        calls = []
        for src in ('%s_scene' % chapter, '%s2_scene' % chapter):
            calls += scrape_calls(chapter, nm, gvars_map.get(src, {}), src)
        pick = None
        for c in calls:
            if c and c[0] and any(isinstance(a, (int, float)) for a in c[0]):
                pick = c
                break
        if pick is None:
            for c in calls:
                if c and c[0]:
                    pick = c
                    break
        if pick is None:
            # No real call site evaluated. Synthesize from the signature so the
            # primitive is at least JUDGED, and mark it SYNTH so nobody reads
            # size off it. A hole is worse than a guess.
            sp = synth_args(fn)
            if sp is not None:
                tile, st = render_prim(fn, sp)
                if not st:
                    st = 'SYNTH'
                tiles.append((nm, tile, st))
            else:
                tiles.append((nm, Image.new('RGB', (TW, TH), BG), 'NOCALL'))
            continue
        tile, status = render_prim(fn, pick)
        tiles.append((nm, tile, status))

    per = COLS * ROWS
    ns = (len(tiles) + per - 1) // per
    for si in range(ns):
        chunk = tiles[si * per:(si + 1) * per]
        W = COLS * TW + (COLS + 1) * PAD
        H = ROWS * TH + (ROWS + 1) * PAD + 26
        sheet = Image.new('RGB', (W, H), (60, 60, 64))
        sd = ImageDraw.Draw(sheet)
        bad = sum(1 for t in chunk if t[2] == 'NOCALL')
        synth = sum(1 for t in chunk if t[2] == 'SYNTH')
        hdr = '%s  %d/%d  %d prims' % (chapter, si + 1, ns, len(tiles))
        if synth:
            hdr += '  (%d synth)' % synth
        if bad:
            hdr += '  (%d BLIND)' % bad
        sd.text((8, 5), hdr, font=font, fill=(240, 240, 236))
        for i, (nm, tile, st) in enumerate(chunk):
            c, r = i % COLS, i // COLS
            x, y = PAD + c * (TW + PAD), 26 + PAD + r * (TH + PAD)
            dd = ImageDraw.Draw(tile)
            for gx in range(0, TW, 40):
                dd.line([(gx, 0), (gx, TH)], fill=(150, 152, 154))
            for gy in range(0, TH, 40):
                dd.line([(0, gy), (TW, gy)], fill=(150, 152, 154))
            if st:
                banner = (196, 150, 60) if st == 'SYNTH' else (190, 70, 60)
                dd.rectangle([0, 0, TW, 18], fill=banner)
                dd.text((3, 3), st, font=lf, fill=(255, 244, 232))
            dd.rectangle([0, TH - 20, TW, TH], fill=(40, 40, 44))
            dd.text((4, TH - 18), nm, font=lf, fill=(240, 240, 236))
            sheet.paste(tile, (x, y))
        p = os.path.join('..', 'measure', 'sheet_%s_%d.png' % (prefix, si + 1))
        sheet.save(p)
        print('wrote', p)
    nbad = sum(1 for t in tiles if t[2] == 'NOCALL')
    nsyn = sum(1 for t in tiles if t[2] == 'SYNTH')
    print('TOTAL %d prims, %d blind (NOCALL), %d synthesized (SYNTH)'
          % (len(tiles), nbad, nsyn))
    if nbad:
        print('  BLIND:', ', '.join(t[0] for t in tiles if t[2] == 'NOCALL'))
    if nsyn:
        print('  SYNTH:', ', '.join(t[0] for t in tiles if t[2] == 'SYNTH'))


if __name__ == '__main__':
    main()