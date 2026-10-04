# work/segments/kelt9b/_cards.py — segment 11 (KELT-9B) card renderers.
#
# ONE module for the whole segment, keyed by the 12 beat ids in script.json.
# Each renderer is fn(card, planet) -> PIL RGB 1280x720 and DRAWS the frame; it
# does not return a card dict. The frame generator merges RENDERERS and calls
# C.render(card, "KELT-9B").
#
# Beat table (script.json beats[] -> id / register):
#   1  hook          VOID   the white-hot host star, cream character, deadpan
#   2  the_record    CREAM  ranked ladder of hot worlds, mid-shrug, zigzag
#   3  the_orbit     VOID   tight track round a blue star, pointing, awed
#   4  no_escape     CREAM  lit half / dark half + the loop that never turns
#   5  the_star      VOID   blue A-type furnace with granulation, hands raised
#   6  the_light     CREAM  the star fires broad parallel rays onto the planet
#   7  the_dayside   VOID   the crescent. THE luminous body of the segment
#   8  molecules     CREAM  H2 pairs torn apart along the escaping tail
#   9  the_warning   VOID   the sharp seam: cool half vs white-hot half
#   10 unraveling    CREAM  the lattice holds, then scatters
#   11 nowhere_cool  VOID   ocean / shade / door, all struck through
#   12 closer        CREAM  one bright point among many, a very long arrow
#
# Register discipline (STYLE_CANON §0 / PALETTE_SPEC.md §2):
#   VOID  -> C.void_backdrop, C._header(paper_band=True), character theme='dark',
#            caption dark_bg=True (furnace gold on an ink keyline).
#   CREAM -> full-bleed PAPER, C._header(paper_band=False), character theme='light',
#            caption dark_bg=False (ink on a paper keyline).
#
#   The ONLY gradients in this segment are on genuinely EMISSIVE bodies: the
#   white-hot host star (1, 5, 6, 9), the blue A-type furnace (3, 5) and the
#   dayside crescent (7). Everything else is a flat fill or linework. The
#   planet's night side is a flat slate — it is dark because it emits nothing.
#
# Type (STYLE_CANON §2, nothing off-lock): the header via C._header at
# T.HEADER_PX, the one floating caption at T.CAPTION_PX, subject labels via
# T.draw_label at T.LABEL_PX, tiny diagram annotations via T.draw_stamp at
# T.STAMP_PX (18 where a stamp must be readable at a glance — both are inside
# the canon's 12-18 px stamp band). Consolas is retired; comicbd.ttf/comic.ttf
# only, loaded through lib.type. NO hero words anywhere in this segment: the
# caption is drawn by the schedule and a hero phrase can only restate it, so
# every idea is carried by the art plus one small label.
#
# Determinism: every wobble / stipple / starfield / cell call takes an explicit
# integer seed. No global random state, no hash(). Re-renders are byte-identical.

import math
import os
import sys

from PIL import Image, ImageDraw

# `lib.*` must resolve absolutely. When the frame generator imports this module
# it has already put work/ on sys.path; this block makes `python _cards.py` work
# from anywhere too, and is a no-op otherwise.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))     # .../work
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib.type as T
import lib.ink as K
import lib.cardframe as C

W, H = C.W, C.H


# ---------------------------------------------------------------------------
# The locked KELT-9B palette (PALETTE_SPEC.md §1). Six colors. Red is NOT in
# it and may not be added: #C83232 is the character's shirt, identical across
# all 12 segments, and it must stay the only red on screen.
# ---------------------------------------------------------------------------
MY_PAL = {
    'ink':    (20, 22, 28),    # #14161C  slate-black: all linework, header glyphs,
                               #            and the night side / dark half of a planet
    'paper':  (242, 234, 214),  # #F2EAD6  bone-cream: title strip, cream cards
    'deep':   (5, 6, 11),      # #05060B  void: every space field
    'furnace': (245, 178, 58),  # #F5B23A  furnace gold: captions on deep, hot
                               #            accents, the 4600 F reading, strikes
    'star':   (127, 178, 229),  # #7FB2E5  A-type blue: the host star's colour and
                               #            the cool counter-accent. Fills only —
                               #            2.0:1 on cream, so it never carries a word
    'bone':   (220, 230, 236),  # #DCE6EC  x-ray bone: emphasis on deep, lit rims,
                               #            starfield, the hot half's core
}

INK = MY_PAL['ink']
PAPER = MY_PAL['paper']
DEEP = MY_PAL['deep']
FURNACE = MY_PAL['furnace']
STAR = MY_PAL['star']
BONE = MY_PAL['bone']


# ---------------------------------------------------------------------------
# Shared helpers (private to this module; no lib constant is re-derived)
# ---------------------------------------------------------------------------

def _void(seed, stars=120):
    """Register-S space field. A distinct seed per card so no two beats share a
    literal starfield. This is the one gradient-legal part of a void card."""
    img = Image.new('RGB', (W, H), DEEP)
    C.void_backdrop(img, seed=seed, stars=stars)
    return img


def _cream():
    """Register-P paper card: full-bleed bone-cream, no visible strip edge."""
    return Image.new('RGB', (W, H), PAPER)


def _catmull_open(pts, samples=12):
    """Catmull-Rom through `pts` as an OPEN polyline (dense output)."""
    p = list(pts)
    ext = [p[0]] + p + [p[-1]]
    out = []
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(samples):
            t = s / float(samples)
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(p[-1])
    return out


def _open_curve(draw, points, color, width=2, seed=0, wobble=1.2, wavelength=90.0):
    """An OPEN hand-wobbled smooth curve (the K.draw_outline(closed=False)
    equivalent, built locally so this module never depends on that path)."""
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    if len(pts) < 3:
        draw.line(list(pts), fill=color, width=width)
        return pts
    out = _catmull_open(pts, samples=12)
    draw.line(out, fill=color, width=width, joint='curve')
    return out


def _hrule(draw, y, x0, x1, color, width=K.DETAIL, seed=0, wobble=1.2):
    """A short hand-wobbled horizontal rule."""
    mid = (x0 + x1) / 2.0
    return _open_curve(draw, [(x0, y), (mid, y), (x1, y)], color, width,
                       seed=seed, wobble=wobble, wavelength=90.0)


def _vrule(draw, x, y0, y1, color, width=K.DETAIL, seed=0, wobble=1.2):
    """A short hand-wobbled vertical rule."""
    mid = (y0 + y1) / 2.0
    return _open_curve(draw, [(x, y0), (x, mid), (x, y1)], color, width,
                       seed=seed, wobble=wobble, wavelength=60.0)


def _thick_curve(draw, points, fill, seed=0, width=24, wobble=2.0,
                 wavelength=150.0):
    """An OPEN curve stroked to a real width as a FILLED region.

    PIL's wide-line joint='curve' grows a nub at every near-duplicate vertex of a
    dense Catmull-Rom path, so the stroke is built geometrically instead: offset
    the smooth centreline by +/- half-width along its normal and fill the welded
    polygon. Clean edges, no nubs."""
    pts = K.wobble_points(points, seed=seed, amount=wobble, wavelength=wavelength)
    dense = _catmull_open(pts, samples=12)
    n = len(dense)
    hw = width / 2.0
    outer, inner = [], []
    for i in range(n):
        a = dense[max(0, i - 1)]
        b = dense[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        outer.append((dense[i][0] + nx * hw, dense[i][1] + ny * hw))
        inner.append((dense[i][0] - nx * hw, dense[i][1] - ny * hw))
    region = outer + inner[::-1]
    draw.polygon(region, fill=fill)
    return region


def _label(draw, text, xy, rgb, center_x=None):
    """Subject label, locked casual hand at T.LABEL_PX. Used only where the
    reference puts a label: ON or immediately BESIDE the thing it names."""
    return T.draw_label(draw, text, xy, ink_rgb=rgb, center_x=center_x)


def _stamp(draw, text, xy, rgb, px=None):
    """Tiny diagram annotation at the locked stamp size (T.STAMP_PX, or 18 where
    the canon's stamp band allows it and the note must read at a glance)."""
    if px is None or px == T.STAMP_PX:
        return T.draw_stamp(draw, text, xy, rgb, ink_rgb=INK if rgb != INK else PAPER)
    font = T.load_font_at(px, bold=False)
    d = draw
    T.draw_outlined_text(d, xy, text, font, fill=rgb,
                         stroke=INK if rgb != INK else PAPER, stroke_width=1)
    return T._bbox(d, text, font)


def _caption_fit(img, text, x, y, dark_bg):
    """The one caption call, with a width guard.

    C._caption is fixed at T.CAPTION_PX and does not clamp. A caption longer
    than the drawable span would run off the right edge, so the size steps down
    (never below 18) until it fits. Deterministic, and it keeps every caption in
    the segment at one type size in practice."""
    d = ImageDraw.Draw(img)
    px = T.CAPTION_PX
    font = T.load_font(px, bold=True)
    bb = T._bbox(d, text, font)
    pad = T.CAPTION_STROKE * 2 + 2
    while (bb[2] + pad) > (W - x - 40) and px > 18:
        px -= 2
        font = T.load_font(px, bold=True)
        bb = T._bbox(d, text, font)
    fill = FURNACE if dark_bg else INK
    key = INK if dark_bg else PAPER
    T.draw_caption(d, text, (x, y), color_rgb=fill, ink_rgb=key)
    return px


def _finish(img, card, planet, paper_band, dark_bg):
    """Layout-A tail: title strip, then the schedule-driven character, then the
    one caption every card in this segment shares."""
    C._header(img, planet, paper_band=paper_band)
    C._draw_stickman(img, card, theme=('dark' if dark_bg else 'light'))
    _caption_fit(img, card.get('caption', ''), 70, 652, dark_bg)
    return img


def _flat_ring(draw, cx, cy, r, rgb, alpha, width=K.FINE):
    """A FLAT concentric ring — a halo, a limb, an orbit. Never a gradient."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=rgb + (alpha,), width=width)


def _emissive(img, cx, cy, r, stops, seed, grain=0.03, glow=1.0, rings=()):
    """The segment's ONLY gradient: a 3-stop radial core with a real circular
    halo, plus optional FLAT concentric emission rings around it.

    Legal because every caller is a genuinely emissive body (STYLE_CANON §0).
    The grain is a deterministic stipple so the core keeps spray-paint texture
    instead of reading as a clean CG ramp."""
    C._radial_core(img, int(cx), int(cy), int(r), stops, glow=glow)
    d = ImageDraw.Draw(img, 'RGBA')
    if grain:
        K.stipple(d, cx - r * 0.95, cy - r * 0.95, cx + r * 0.95, cy + r * 0.95,
                  (60, 48, 30), seed=seed, density=grain, r=1, spread=1)
    for rr, rgb, a in rings:
        _flat_ring(d, cx, cy, rr, rgb, a, K.DETAIL)
    return d


def _spikes(draw, cx, cy, r0, r1, rgb, alpha, seed, n=4, width=K.DETAIL):
    """Four soft light-spikes across an emissive body (a generic astronomical
    convention, drawn as FLAT tapered bands — not a glow, not a gradient)."""
    for i in range(n):
        a = math.radians(45 + 90 * i)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(cx + r0 * ca, cy + r0 * sa),
               (cx + r1 * ca, cy + r1 * sa)]
        _thick_curve(draw, pts, rgb + (alpha,), seed=seed + i, width=width,
                     wobble=0.8, wavelength=200.0)


def _strike(draw, cx, cy, r, rgb, seed, width=K.OUTLINE):
    """The X that cancels an icon. Slate-black, NOT red: the character's shirt
    is the only red allowed on screen (PALETTE_SPEC.md §1)."""
    for i, sgn in enumerate((-1, 1)):
        pts = [(cx - r, cy - sgn * r), (cx + r, cy + sgn * r)]
        _thick_curve(draw, pts, rgb, seed=seed + i, width=width, wobble=1.6,
                     wavelength=70.0)

# ---------------------------------------------------------------------------
# Beat 1 — hook. VOID. The host star, white-hot, upper right.
# ---------------------------------------------------------------------------

def render_hook(card, planet="KELT-9B"):
    """B1/1 — one blazing body and one character looking up at it.

    The star is the segment's opening statement and the only thing on the card
    that emits: C._radial_core with a white -> bone -> furnace limb ramp, its
    real circular halo, and two FLAT emission rings outside the core. The night
    of the field is untouched. The label sits BESIDE the star, not across it."""
    img = _void(seed=1101, stars=126)

    cx, cy, r = 940, 262, 88
    d = _emissive(img, cx, cy, r,
                  [(255, 255, 255), BONE, FURNACE],
                  seed=1101, grain=0.025, glow=1.0,
                  rings=((132, FURNACE, 44), (166, STAR, 26)))
    _spikes(d, cx, cy, r * 0.92, r * 1.95, BONE, 34, seed=1102)

    d = ImageDraw.Draw(img)
    _label(d, 'A-TYPE HOST STAR', (cx, 392), BONE, center_x=cx)
    _stamp(d, 'HOTTER THAN ITS OWN PLANET', (cx - 148, 438), FURNACE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Beat 2 — the_record. CREAM. The ranked ladder of hot worlds.
# ---------------------------------------------------------------------------

_RECORD = [('KELT-9B', 1), ('WASP-33B', 2), ('KELT-20B', 3), ('WASP-121B', 4)]


def render_the_record(card, planet="KELT-9B"):
    """B2/2 — the record, as a hand-drawn ranked list on paper.

    Four ruled rows, hottest first. KELT-9B's row is the only one that is lit:
    a furnace marker disc, a furnace double rule and the name in furnace. The
    other three are slate-black on cream, which is the canon's rule for a cream
    card — no accent ever carries a word on paper."""
    img = _cream()
    d = ImageDraw.Draw(img)

    top, pitch = 168, 118
    for i, (name, rank) in enumerate(_RECORD):
        y = top + i * pitch
        lead = (name == 'KELT-9B')
        col = FURNACE if lead else INK
        # rank marker: a filled disc for the leader, a small hollow one below it
        if lead:
            K.draw_disc(d, 96, y + 6, 17, fill=FURNACE, outline=INK,
                        width=K.OUTLINE, seed=2100, wobble=2.0)
        else:
            K.draw_disc(d, 96, y + 6, 12, fill=PAPER, outline=INK,
                        width=K.DETAIL, seed=2100 + i, wobble=1.6)
        _label(d, name, (140, y - 16), col)
        _hrule(d, y + 36, 84, 900, col,
               width=K.OUTLINE if lead else K.DETAIL, seed=2110 + i)
        if lead:
            _hrule(d, y + 46, 84, 900, col, width=K.FINE, seed=2120 + i)

    _stamp(d, 'HOTTEST KNOWN WORLDS', (84, 620), INK)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Beat 3 — the_orbit. VOID. The tightest track in the video.
# ---------------------------------------------------------------------------

def render_the_orbit(card, planet="KELT-9B"):
    """B3/3 — the orbit, close in. A blue A-type core (emissive, legal) inside one
    tight bone track, with the planet riding the NEAREST point of that track.
    The single stamp carries the conversion the card exists for."""
    img = _void(seed=3101, stars=118)

    cx, cy = 700, 318
    rx, ry = 196, 84
    d = ImageDraw.Draw(img, 'RGBA')
    ring = [(cx + rx * math.cos(math.tau * i / 48),
             cy + ry * math.sin(math.tau * i / 48)) for i in range(48)]
    K.draw_outline(d, ring, color=BONE, width=K.DETAIL, closed=True,
                   seed=3102, wobble=1.0, wavelength=170.0)

    d = _emissive(img, cx, cy, 52, [(255, 255, 255), STAR, (26, 48, 92)],
                  seed=3103, grain=0.022)

    # the planet at the track's closest approach to the frame's upper right
    a = math.radians(-62)
    px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
    _emissive(img, px, py, 17, [(255, 255, 255), FURNACE, (150, 74, 20)],
              seed=3104, grain=0.0, glow=0.7)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, px, py, 26, BONE, 200, K.FINE)

    d = ImageDraw.Draw(img)
    _stamp(d, 'ONE YEAR = ONE AND A HALF DAYS', (px + 40, py + 34), BONE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Beat 4 — no_escape. CREAM. Lit half, dark half, and the loop that never ends.
# ---------------------------------------------------------------------------

def render_no_escape(card, planet="KELT-9B"):
    """B4/4 — the card the whole segment turns on: the planet never rotates away.

    A paper card with a drawn sun at the left throwing flat furnace rays right,
    a hard seam at x=880, and the night half in slate-black. Inside the night
    half the planet sits with a circular arrow that returns to itself — the
    diagram of 'it never turns its back'. The character is placed on the PAPER
    side (the schedule's x_center), so he keeps the cream-on-dark contrast
    rule instead of standing inside his own night half."""
    img = _cream()
    d = ImageDraw.Draw(img)

    # the night half: a hand-edged slate region, not a hard CAD rectangle
    K.draw_smooth(d, [(880, 84), (1280, 84), (1280, 720), (880, 720)],
                  fill=INK, outline=None, seed=4101, wobble=4.0,
                  wavelength=220.0)
    # The seam is the blob's own left edge — it IS the split, so no rule is
    # drawn over it. A rule here was buried inside the wobbled edge and read as
    # nothing at all.

    # the drawn sun, paper register: flat furnace fill, thick ink keyline
    sx, sy, sr = 178, 236, 62
    for i in range(7):
        a = math.radians(-26 + i * 8.7)
        _thick_curve(d, [(sx + sr * math.cos(a), sy + sr * math.sin(a)),
                         (sx + (sr + 78) * math.cos(a), sy + (sr + 78) * math.sin(a))],
                     FURNACE, seed=4110 + i, width=10, wobble=1.2, wavelength=90.0)
    K.draw_disc(d, sx, sy, sr, fill=FURNACE, outline=INK, width=K.OUTLINE,
                seed=4120, wobble=2.2)

    # the planet in the dark half, and the arrow that never lets go
    px, py = 1064, 330
    K.draw_disc(d, px, py, 40, fill=BONE, outline=INK, width=K.OUTLINE,
                seed=4130, wobble=2.4)
    # its lit sliver, hard against the seam
    K.draw_smooth(d, [(px - 40, py - 6), (px - 12, py - 22), (px - 12, py + 24)],
                  fill=FURNACE, outline=None, seed=4131, wobble=1.4)
    loop = [(px + 96 * math.cos(math.radians(a)), py + 96 * math.sin(math.radians(a)))
            for a in range(-40, 300, 20)]
    _thick_curve(d, loop, BONE, seed=4132, width=6, wobble=1.6, wavelength=160.0)
    _thick_curve(d, [(px + 96 * math.cos(math.radians(300)),
                      py + 96 * math.sin(math.radians(300))),
                     (px + 96 * math.cos(math.radians(268)),
                      py + 96 * math.sin(math.radians(268)))],
                 BONE, seed=4133, width=6, wobble=0.8, wavelength=60.0)

    d = ImageDraw.Draw(img)
    _stamp(d, 'NEVER TURNS AWAY', (px, 462), BONE, px=18)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)
# ---------------------------------------------------------------------------
# Beat 5 - the_star. VOID. The blue furnace, and the small dull thing it made.
# ---------------------------------------------------------------------------

def render_the_star(card, planet="KELT-9B"):
    """B5/5 - the host star as the dominant object. A blue A-type core (emissive,
    legal) with painterly granulation mottled over it and four flat spikes. The
    planet is a small dull slate dot with a bone rim: it emits nothing, so it is
    a flat fill with a keyline, never a gradient."""
    img = _void(seed=5101, stars=112)

    cx, cy, r = 566, 336, 168
    d = _emissive(img, cx, cy, r,
                  [(255, 255, 255), (206, 228, 255), STAR],
                  seed=5101, grain=0.02, glow=1.0,
                  rings=((214, STAR, 34),))
    _spikes(d, cx, cy, r * 0.9, r * 1.55, BONE, 30, seed=5102)

    # granulation: flat mottles over the core, seeded
    mottles = [(500, 268, 46), (612, 246, 40), (486, 388, 42), (628, 410, 48),
               (566, 336, 56)]
    for i, (mx, my, mr) in enumerate(mottles):
        K.draw_disc(d, mx, my, mr, fill=(120, 168, 224, 34), outline=None,
                    seed=5110 + i, wobble=6.0)

    # the planet: a dull slate dot, small, high right of the star
    px, py = 1046, 250
    K.draw_disc(d, px, py, 34, fill=INK, outline=BONE, width=K.DETAIL,
                seed=5120, wobble=2.6)
    d = ImageDraw.Draw(img)
    _label(d, 'KELT-9B', (px - 6, py + 48), BONE, center_x=px)
    _stamp(d, 'SPINS FAST', (cx - 66, 548), BONE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Beat 6 - the_light. CREAM. Broad parallel rays onto a pale world.
# ---------------------------------------------------------------------------

def render_the_light(card, planet="KELT-9B"):
    """B6/6 - the light itself, drawn. A white star at the left fires six broad
    FLAT furnace bands across the card onto a pale outlined planet at the right.
    Nothing here is a gradient: on paper the rays are painted bands with hand
    edges, and the planet is a pale disc with a thick ink keyline and one
    furnace lit crescent."""
    img = _cream()
    d = ImageDraw.Draw(img)

    # The star is pushed OFF the left edge so it reads as a SOURCE rather than as
    # the second half of a barbell, and the planet is the larger object. The
    # bundle is wide at the star and narrows onto the planet's lit face, so the
    # card reads as light ARRIVING rather than as two discs joined by stripes.
    sx, sy, sr = 84, 330, 104
    px, py = 958, 296

    # the ray bundle: seven broad FLAT bands, wide at the star, converging on the
    # planet. Paper register, so a painted band with a hand edge, never a glow.
    for i in range(7):
        u = (i - 3) / 3.0                       # -1 .. 1 across the bundle
        _thick_curve(d, [(sx + sr * 0.55, sy + u * 152),
                         ((sx + sr * 0.55 + (px - 84)) / 2.0,
                          sy + u * 112 + (py - sy) * 0.5),
                         (px - 84, py + u * 72)],
                     FURNACE, seed=6100 + i, width=18, wobble=1.8,
                     wavelength=200.0)

    # the star: flat bone disc, thick ink keyline, furnace limb facing the rays
    K.draw_disc(d, sx, sy, sr, fill=BONE, outline=INK, width=K.OUTLINE,
                seed=6110, wobble=2.4)
    K.draw_smooth(d, [(sx + 24, sy - 84), (sx + sr, sy - 46), (sx + sr, sy + 46),
                      (sx + 24, sy + 84)],
                  fill=FURNACE, outline=None, seed=6111, wobble=2.0)

    # the planet: pale disc + thick ink keyline + furnace lit crescent
    K.draw_disc(d, px, py, 132, fill=BONE, outline=INK, width=K.OUTLINE,
                seed=6120, wobble=3.0)
    K.draw_smooth(d, [(px - 132, py - 30), (px - 44, py - 112), (px - 44, py + 112),
                      (px - 132, py + 30)],
                  fill=FURNACE, outline=None, seed=6121, wobble=2.2)
    # contour lines so the pale disc reads as a sphere, flat fill only
    _hrule(d, py - 38, px - 88, px + 86, INK, width=K.FINE, seed=6130, wobble=2.0)
    _hrule(d, py + 44, px - 82, px + 80, INK, width=K.FINE, seed=6131, wobble=2.0)

    d = ImageDraw.Draw(img)
    _stamp(d, 'LIGHT MOST STARS NEVER GIVE', (px - 156, py + 132), INK)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Beat 7 - the_dayside. VOID. The crescent. The segment's brightest body.
# ---------------------------------------------------------------------------

def render_the_dayside(card, planet="KELT-9B"):
    """B7/7 - KELT-9b seen from the side: a white-hot crescent along the sunward
    edge, the night side a flat slate that emits nothing.

    The lit body IS an emissive body, so the ramp is legal here and only here.
    It is carved by pasting one flat slate disc over the gradient upper-left,
    which leaves the crescent and keeps the halo - a painted terminator, not a
    shaded sphere."""
    img = _void(seed=7101, stars=104)

    cx, cy, r = 660, 372, 236
    d = _emissive(img, cx, cy, r,
                  [(255, 255, 255), FURNACE, (128, 46, 12)],
                  seed=7101, grain=0.02, glow=1.15)

    # the night side: one flat slate disc, offset up-left, no gradient
    K.draw_disc(d, cx - 104, cy - 30, 214, fill=INK, outline=None,
                seed=7110, wobble=3.0)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, cx, cy, r + 4, FURNACE, 120, K.FINE)

    d = ImageDraw.Draw(img)
    _label(d, '4600 F', (cx + 74, cy + 66), FURNACE, center_x=cx + 74)
    _stamp(d, 'DAYSIDE', (cx - 226, cy - 268), BONE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Beat 8 - molecules. CREAM. The bonds losing.
# ---------------------------------------------------------------------------

def render_molecules(card, planet="KELT-9B"):
    """B8/8 - hydrogen coming apart, drawn. Three joined pairs on the left, three
    loose single dots on the right, an arrow between them, and the escaping tail
    at the right. Paper register throughout: flat fills, thick ink keys, no
    gradients anywhere on this card."""
    img = _cream()
    d = ImageDraw.Draw(img)

    y = 236
    pairs = (188, 396, 604)
    for i, x in enumerate(pairs):
        for j, sgn in enumerate((-1, 1)):
            K.draw_disc(d, x + sgn * 36, y, 25, fill=BONE, outline=INK,
                        width=K.OUTLINE, seed=8100 + i * 2 + j, wobble=2.0)
        _hrule(d, y, x - 14, x + 14, INK, width=K.DETAIL, seed=8110 + i)
        _stamp(d, 'H2', (x - 8, y + 42), INK)

    # the arrow that separates them
    _thick_curve(d, [(760, y), (852, y)], INK, seed=8120, width=7,
                 wobble=1.2, wavelength=90.0)
    _thick_curve(d, [(852, y), (826, y - 14)], INK, seed=8130, width=7,
                 wobble=0.8, wavelength=50.0)
    _thick_curve(d, [(852, y), (826, y + 14)], INK, seed=8140, width=7,
                 wobble=0.8, wavelength=50.0)

    # what is left: single dots, already drifting apart
    for i, x in enumerate((962, 1078, 1186)):
        K.draw_disc(d, x, y + (i - 1) * 16, 21, fill=FURNACE, outline=INK,
                    width=K.DETAIL, seed=8150 + i, wobble=2.0)

    # the escaping tail, lower right: the planet and its gas, flat blobs
    tx, ty = 1150, 470
    K.draw_disc(d, tx, ty, 26, fill=FURNACE, outline=INK, width=K.DETAIL,
                seed=8160, wobble=2.0)
    for i, (bx, by, br) in enumerate(((1210, 430, 20), (1244, 398, 15),
                                      (1222, 514, 17))):
        K.draw_disc(d, bx, by, br, fill=FURNACE, outline=None, seed=8170 + i,
                    wobble=3.0)

    _stamp(d, 'BONDS TORN APART', (188, 320), INK)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)# ---------------------------------------------------------------------------
# Beat 9 - the_warning. VOID. The seam where matter stops holding.
# ---------------------------------------------------------------------------

def render_the_warning(card, planet="KELT-9B"):
    """B9/9 - the card that stops you. A hard furnace seam down the middle: cool
    slate on the left, a white-hot half on the right. The hot half is emissive,
    so it takes the ramp and the halo; the cold half emits nothing and is flat
    slate with a bone keyline. The two labels name the halves, which is the one
    thing a viewer needs to read the diagram."""
    img = _void(seed=9101, stars=98)

    # the cold half: flat slate, bone keyline on the seam side
    d = ImageDraw.Draw(img)
    K.draw_smooth(d, [(60, 118), (596, 100), (604, 566), (60, 592)],
                  fill=INK, outline=None, seed=9102, wobble=4.0,
                  wavelength=200.0)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, 600, 330, 250, BONE, 26, K.FINE)

    # the hot half: an emissive body pushed off the right edge
    _emissive(img, 1030, 330, 268,
              [(255, 255, 255), FURNACE, (140, 50, 14)],
              seed=9103, grain=0.02, glow=1.1)

    # the seam itself: one hard furnace line, the brightest rule on the card
    _vrule(d, 620, 92, 606, FURNACE, width=K.OUTLINE, seed=9104, wobble=1.0)

    d = ImageDraw.Draw(img)
    _stamp(d, 'STILL BOUND', (150, 200), BONE, px=18)
    _stamp(d, 'COMING UNDONE', (830, 176), FURNACE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Beat 10 - unraveling. CREAM. The lattice, then the scatter.
# ---------------------------------------------------------------------------

def render_unraveling(card, planet="KELT-9B"):
    """B10/10 - the bonds that make matter simply lose. Paper register: a tidy
    ink lattice of joined dots on the left, a furnace vertical seam, and on the
    right the same dots with every link gone, drifting on their own. The links
    are the subject, so nothing else competes."""
    img = _cream()
    d = ImageDraw.Draw(img)

    rows, cols, pitch = 4, 4, 62
    ox, oy = 96, 176

    # left: a joined lattice
    for r in range(rows):
        for c in range(cols):
            x = ox + c * pitch
            y = oy + r * pitch
            K.draw_disc(d, x, y, 13, fill=BONE, outline=INK, width=K.DETAIL,
                        seed=10100 + r * 10 + c, wobble=1.4)
    for r in range(rows):
        for c in range(cols - 1):
            _hrule(d, oy + r * pitch, ox + c * pitch + 13,
                   ox + (c + 1) * pitch - 13, INK, width=K.FINE,
                   seed=10150 + r * 10 + c)
        if r < rows - 1:
            _vrule(d, ox + pitch * 1.5, oy + r * pitch + 13,
                   oy + (r + 1) * pitch - 13, INK, width=K.FINE, seed=10170 + r)

    # the seam
    _vrule(d, 604, 150, 432, FURNACE, width=K.OUTLINE, seed=10180)

    # right: the same dots, unlinked, drifting
    rnd_x = (676, 748, 862, 936)
    for r in range(rows):
        for c in range(cols):
            jx = rnd_x[c] + ((c * 37 + r * 53) % 26) - 13
            jy = oy + r * pitch + ((c * 29 + r * 41) % 30) - 15
            K.draw_disc(d, jx, jy, 12, fill=FURNACE, outline=INK,
                        width=K.DETAIL, seed=10200 + r * 10 + c, wobble=2.0)

    d = ImageDraw.Draw(img)
    _stamp(d, 'HOLDS', (ox + 96, 452), INK, px=18)
    _stamp(d, 'SCATTERS', (786, 452), FURNACE, px=18)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Beat 11 - nowhere_cool. VOID. Three things you would want, none of them.
# ---------------------------------------------------------------------------

def _icon_wave(draw, cx, cy, s, rgb, seed):
    """OCEAN - three hand-wobbled wave crests."""
    for i in range(3):
        y = cy - s * 0.5 + i * s * 0.5
        pts = [(cx - s + (2 * s) * k / 8.0,
                y + math.sin(k / 8.0 * math.tau) * s * 0.16)
               for k in range(9)]
        _open_curve(draw, pts, rgb, width=K.DETAIL, seed=seed + i, wobble=1.0,
                    wavelength=70.0)


def _icon_shade(draw, cx, cy, s, rgb, seed):
    """SHADE - a canopy arc on a pole."""
    arc = [(cx + s * math.cos(math.radians(a)), cy - s * 0.15
            + s * 0.62 * math.sin(math.radians(a)))
           for a in range(180, 361, 15)]
    _open_curve(draw, arc, rgb, width=K.DETAIL, seed=seed, wobble=1.0,
                wavelength=70.0)
    _vrule(draw, cx, cy - s * 0.15, cy + s * 0.8, rgb, width=K.DETAIL, seed=seed + 1)


def _icon_door(draw, cx, cy, s, rgb, seed):
    """DOOR - a frame with a knob."""
    _open_curve(draw, [(cx - s * 0.6, cy - s * 0.8), (cx + s * 0.6, cy - s * 0.8),
                       (cx + s * 0.6, cy + s * 0.8), (cx - s * 0.6, cy + s * 0.8),
                       (cx - s * 0.6, cy - s * 0.8)],
                rgb, width=K.DETAIL, seed=seed, wobble=1.2, wavelength=80.0)
    _open_curve(draw, [(cx + s * 0.36, cy - s * 0.04), (cx + s * 0.36, cy + s * 0.14)],
                rgb, width=K.DETAIL, seed=seed + 1, wobble=0.4, wavelength=40.0)


def render_nowhere_cool(card, planet="KELT-9B"):
    """B11/11 - ocean, shade, door: the three things every world has and this
    one does not. Bone linework icons in a row, each struck through.

    The strike is FURNACE GOLD, not red. PALETTE_SPEC.md §1 reserves red for the
    character's shirt so he never dissolves into a background, and the slate
    strike that stood in for it was invisible against the void. Gold is this
    segment's alert colour (beat 9 proves it reads), so the 'no' still lands."""
    img = _void(seed=11101, stars=96)

    d = ImageDraw.Draw(img)
    xs = (250, 640, 1030)
    names = ('OCEAN', 'SHADE', 'DOOR')
    for i, x in enumerate(xs):
        s = 96
        if i == 0:
            _icon_wave(d, x, 306, s, BONE, seed=11110)
        elif i == 1:
            _icon_shade(d, x, 300, s, BONE, seed=11120)
        else:
            _icon_door(d, x, 306, s, BONE, seed=11130)
        _strike(d, x, 306, int(s * 0.86), FURNACE, seed=11140 + i * 4)
        _stamp(d, names[i], (x - 34, 452), BONE, px=18)

    return _finish(img, card, planet, paper_band=True, dark_bg=True)


# ---------------------------------------------------------------------------
# Beat 12 - closer. CREAM. One bright point, very far away.
# ---------------------------------------------------------------------------

def render_closer(card, planet="KELT-9B"):
    """B12/12 - the closing card: KELT-9b as one bright point among many, with a
    long distance arrow running to it from the lower left. The sky is a slate
    window set into the paper with a wobbled horizon, so the card keeps the
    cream register while still reading as distance; the character stands on the
    paper below it at lower right, keeping his dark ink readable on cream. One
    label, on the point itself."""
    img = _cream()

    # The sky is a slate window set into the paper. It is built as a plain rect
    # for the body plus a separate hand-wobbled HORIZON band, NOT as one closed
    # spline: a spline whose top control points sit exactly on y=84 overshoots
    # above the row and painted over the title strip, which _header
    # (paper_band=False) does not re-fill. Rows 0..83 are now untouchable by
    # construction. The character stands on the paper below the horizon so his
    # dark ink keeps the cream-contrast rule.
    d = ImageDraw.Draw(img)
    d.rectangle([0, T.ART_TOP, W, 384], fill=INK)
    K.draw_smooth(d, [(0, 376), (320, 390), (760, 380), (1280, 394),
                      (1280, 430), (0, 430)],
                  fill=INK, outline=None, seed=12101, wobble=5.0,
                  wavelength=300.0)

    # the far field: small grey points, none of them the subject
    for i in range(26):
        x = 70 + (i * 173) % 1130
        y = 140 + (i * 97) % 230
        r = 2 + (i % 3)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 160, 176))

    # the subject: one bright furnace point, ringed, high in the field
    px, py = 946, 240
    K.draw_disc(d, px, py, 15, fill=FURNACE, outline=None, seed=12102, wobble=1.0)
    d = ImageDraw.Draw(img, 'RGBA')
    _flat_ring(d, px, py, 30, FURNACE, 190, K.FINE)
    _flat_ring(d, px, py, 46, FURNACE, 90, K.FINE)

    # the long distance arrow, split at the horizon so it is ink on paper and
    # bone inside the sky. It starts lower-LEFT and runs up to the point, so it
    # never crosses the character standing lower-right.
    _thick_curve(d, [(150, 606), (420, 540), (700, 442)], INK,
                 seed=12103, width=8, wobble=2.0, wavelength=280.0)
    _thick_curve(d, [(700, 442), (836, 348), (906, 276)], BONE,
                 seed=12106, width=8, wobble=2.0, wavelength=220.0)
    _thick_curve(d, [(906, 276), (858, 296)], BONE, seed=12104, width=8,
                 wobble=0.8, wavelength=60.0)
    _thick_curve(d, [(906, 276), (878, 320)], BONE, seed=12105, width=8,
                 wobble=0.8, wavelength=60.0)

    d = ImageDraw.Draw(img)
    _label(d, 'KELT-9B', (px, 306), BONE, center_x=px)

    return _finish(img, card, planet, paper_band=False, dark_bg=False)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

RENDERERS = {
    'hook': render_hook,
    'the_record': render_the_record,
    'the_orbit': render_the_orbit,
    'no_escape': render_no_escape,
    'the_star': render_the_star,
    'the_light': render_the_light,
    'the_dayside': render_the_dayside,
    'molecules': render_molecules,
    'the_warning': render_the_warning,
    'unraveling': render_unraveling,
    'nowhere_cool': render_nowhere_cool,
    'closer': render_closer,
}


def register(mapping=None):
    """Merge this module's renderers into the shared dispatch table. No import
    side effects: the frame generator calls this, or reads RENDERERS directly."""
    C.register(RENDERERS if mapping is None else mapping)
    return RENDERERS

# ---------------------------------------------------------------------------
# __main__ self-test: render every beat to cardsheet/beat_<NN>.png
# ---------------------------------------------------------------------------

# Per-beat default character for the self-test: (pose, expression, x, y_top,
# height) or None for a data-only beat. The real schedule supplies its own
# card['stickman']; these only stand in so each still is exercised with a
# character wherever the beat calls for one (CLAUDE.md 6).
_SELF_TEST_STICKMAN = {
    'hook':          ('standing', 'flat', 330, 300, 340),
    'the_record':    ('shrugged', 'zigzag', 1080, 330, 330),
    'the_orbit':     ('pointing', 'oval', 1010, 320, 340),
    'no_escape':     ('shielding_eyes', 'worried', 640, 300, 340),
    'the_star':      ('hands_up', 'oval', 1020, 420, 300),
    'the_light':     ('cowering', 'flat', 700, 430, 260),
    'the_dayside':   ('hands_up', 'zigzag', 1050, 400, 300),
    'molecules':     ('hands_up', 'worried', 420, 400, 300),
    'the_warning':   ('shrugged', 'zigzag', 300, 380, 320),
    'unraveling':    ('shrugged', 'oval', 640, 400, 280),
    'nowhere_cool':  ('cowering', 'worried', 640, 400, 320),
    'closer':        ('shrugged', 'flat', 986, 444, 206),
}

_SELF_TEST_CAPTION = {
    'hook': 'HOTTER THAN MOST STARS',
}


def _self_test():
    """Render one still per beat id to cardsheet/beat_<NN>.png.

    Exercises the exact production path (C.register + C.render) so a missing key
    or a bad signature fails here, not 91 s into a video."""
    import os
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'cardsheet')
    os.makedirs(out_dir, exist_ok=True)

    C.register(RENDERERS)
    for i, cid in enumerate(RENDERERS, start=1):
        sm = _SELF_TEST_STICKMAN.get(cid)
        card = {
            'id': cid,
            'caption': _SELF_TEST_CAPTION.get(cid, 'SELF TEST CAPTION'),
            'stickman': None if not sm else {
                'pose': sm[0], 'expression': sm[1],
                'x_center': sm[2], 'y_top': sm[3], 'height': sm[4],
            },
        }
        img = C.render(card, 'KELT-9B')
        assert img.size == (W, H) and img.mode == 'RGB', \
            '%s: bad frame %r %r' % (cid, img.size, img.mode)
        path = os.path.join(out_dir, 'beat_%02d.png' % i)
        img.save(path)
        who = 'char=%s/%s' % (sm[0], sm[1]) if sm else 'char=none'
        print('beat %02d  %-14s  %s  ->  %s'
              % (i, cid, who, os.path.basename(path)))
    print('self-test OK: %d beats rendered, exit 0' % len(RENDERERS))
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(_self_test())
