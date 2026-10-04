# work/lib/cardframe.py — schedule-card -> full frame, per work/STYLE_CANON.md.
#
# This is the renderer every segment should use. It takes one card dict from a
# *_card_schedule.json and draws a complete 1280x720 frame in the corrected canon:
#   - Layout A: an 84 px paper title strip (rows 0..83) with a bold rounded hand
#     header, full-bleed art below, NO caption band. The caption floats on the art.
#   - STRIP MODE: void/space cards get a distinct paper band (header text in ink
#     on paper, art starts at y=84 over a dark field). CREAM cards are full-bleed
#     cream with the header floating on top (no visible band edge — it's already
#     paper). This matches verified reference frames (void card = visible strip;
#     cream card = no strip).
#   - Two visual registers, per STYLE_CANON §0:
#       Register P (paint/scene): flat fills + THICK (5-8px) smooth organic outlines.
#       Register S (space/object): smooth airbrushed gradients, painterly stipple /
#         marbled contour bands, anti-aliased star dots, NO hard black outline.
#     Smooth gradients are legal on EMISSIVE bodies (the pulsar core, a lit sun) and
#     on space backgrounds. They are NOT legal on the planets-as-subjects or on any
#     diagram/character/caption (PALETTE_SPEC §3 denylist).
#   - The themed stickman (light on dark / dark on light) with its per-beat expression.
#
# It renders a STATIC frame. Quantized 0.25 s stamp MOTION is layered on by the
# per-segment frame generator (see motion= in the schedule); this module's job is the
# single still that every stamp is a small variation of.

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import lib.type as T
import lib.ink as K
import lib.stickman as S

W, H = 1280, 720

# Segment 3 (PSR B1257+12) locked palette — from its PALETTE_SPEC.md.
# VOID cards are space-register (dark bg -> cream character, gradient on the core).
# CREAM cards are paint-register (light bg -> dark character, flat fills only).
PAL = {
    'ink':      (20, 22, 28),      # slate-black
    'paper':    (242, 234, 214),   # bone-cream
    'deep':     (5, 6, 11),        # void
    'amber':    (232, 163, 61),    # signal amber
    'bone':     (220, 230, 236),   # x-ray bone
    'violet':   (110, 90, 156),    # magnet violet
    'shirt':    (200, 50, 50),     # character accent (never red on a card accent)
}

INK = PAL['ink']
PAPER = PAL['paper']


# ---------------------------------------------------------------------------
# Backdrops
# ---------------------------------------------------------------------------

def void_backdrop(img, seed=0, stars=120, top=(9, 10, 22), bot=(16, 18, 40)):
    """Register-S space field: smooth vertical gradient + anti-aliased starfield.
    Full bleed over the art area (y=ART_TOP..H)."""
    d = ImageDraw.Draw(img)
    for y in range(T.ART_TOP, H):
        t = (y - T.ART_TOP) / max(1, (H - T.ART_TOP))
        d.line([(0, y), (W, y)],
               fill=(int(top[0] * (1 - t) + bot[0] * t),
                     int(top[1] * (1 - t) + bot[1] * t),
                     int(top[2] * (1 - t) + bot[2] * t)))
    if stars:
        K.starfield(img, seed=seed + 1, n=stars, y0=T.ART_TOP, color=(230, 230, 245))
    return d


def _radial_core(img, cx, cy, r, stops, power=1.0, glow=1.0):
    """Smooth radial gradient disc — an EMISSIVE body (the pulsar core, a lit sun).
    This is the ONE legal gradient in a void card (STYLE_CANON §0). `glow` adds a
    soft halo (0 disables). Drawn in place; returns the ImageDraw."""
    d = ImageDraw.Draw(img, 'RGBA')
    steps = 72
    for i in range(steps, 0, -1):
        t = (i / steps) ** power
        rr = max(1, int(r * t))
        if t < 0.55:
            u = t / 0.55
            c = tuple(int(stops[0][k] * (1 - u) + stops[1][k] * u) for k in range(3))
        else:
            u = (t - 0.55) / 0.45
            c = tuple(int(stops[1][k] * (1 - u) + stops[2][k] * u) for k in range(3))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c + (255,))
    if glow > 0:
        add_glow(img, cx, cy, int(r * 2.1), stops[0], int(80 * glow))
    return d


def add_glow(img, cx, cy, r, color, strength=90):
    """Add a soft radial halo IN PLACE around an emissive body (Register S).

    Built at 1/4 resolution and upscaled: a halo is a smooth low-frequency field,
    so quarter-res is visually identical and ~16x cheaper than the full-size pass.
    Additive (ImageChops.add) so a dark field picks up light without washing out.
    """
    r = max(1, int(r)); cx = int(cx); cy = int(cy)
    small = max(8, r // 4)
    mask = Image.new('L', (small * 2, small * 2), 0)
    md = ImageDraw.Draw(mask)
    # shrink the ellipse well inside the box so the blur always reaches 0 at the
    # edge — otherwise a faint square ring shows where the paste region ends.
    inset = int(small * 0.45)
    md.ellipse([inset, inset, small * 2 - inset, small * 2 - inset], fill=strength)
    mask = mask.filter(ImageFilter.GaussianBlur(small * 0.40))
    mask = mask.resize((r * 2, r * 2), Image.BILINEAR)
    # Hard circular cutoff. On a near-black sky ANY nonzero halo is visible, so
    # the corners of the square paste region must be EXACTLY zero — a threshold
    # on value is not enough because bilinear upsample leaves a faint floor.
    mw, mh = mask.size
    cutoff = Image.new('L', (mw, mh), 0)
    ImageDraw.Draw(cutoff).ellipse([1, 1, mw - 2, mh - 2], fill=255)
    mask = ImageChops.multiply(mask, cutoff)
    # the halo's COLOUR must be modulated by the mask, or it is a solid block.
    halo = Image.new('RGB', mask.size, color)
    halo = ImageChops.multiply(halo, Image.merge('RGB', (mask, mask, mask)))
    box = (cx - r, cy - r, cx + r, cy + r)
    region = img.crop(box).convert('RGB')
    img.paste(ImageChops.add(region, halo), (box[0], box[1]))
    return img


def soft_glow(img, cx, cy, r, color, alpha=60):
    """Backwards-compatible soft halo. Returns the image (also edits in place)."""
    return add_glow(img, cx, cy, r, color, alpha)


def space_body(img, cx, cy, r, base=(150, 158, 156), band=(96, 108, 112),
               hi=(196, 202, 200), seed=0, bands=5):
    """A painterly marbled planet (Register S). Smooth sphere, no black outline:
    a soft radial base, then wavy darker contour BANDS swept around it, then a
    highlight. Used for close-ups of the pulsar planets. This is the reference's
    actual planet treatment (soft gray-teal, wavy strata, airbrushed)."""
    d = ImageDraw.Draw(img, 'RGBA')
    # soft base disc (radial, low contrast)
    steps = 40
    for i in range(steps, 0, -1):
        t = i / steps
        rr = int(r * t)
        c = tuple(int(hi[k] * (1 - t) + base[k] * t) for k in range(3))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c + (255,))
    # wavy contour bands: sample a circle, displace radius by smooth noise.
    # At small radii the bands would dominate and read as a spiral/target, so we
    # scale band count, width and alpha DOWN with r — a small planet is a smooth
    # mottled sphere, not a bullseye.
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, math.tau) for _ in range(3)]
    if r < 30:
        bands = min(bands, 2)
    a_scale = 150 if r >= 30 else 70
    w = max(2, int(r * (0.055 if r >= 30 else 0.09)))
    for b in range(bands):
        frac = 0.24 + 0.62 * b / max(1, bands - 1)
        pts = []
        for s in range(64):
            a = math.tau * s / 64
            rr = r * frac * (1 + 0.10 * math.sin(2 * a + ph[b % 3])
                                   + 0.06 * math.sin(3 * a + ph[(b + 1) % 3]))
            pts.append((cx + rr * math.cos(a), cy + rr * 0.62 * math.sin(a)))
        d.line(pts + [pts[0]], fill=band + (a_scale,), width=w, joint='curve')
    # highlight (upper-left), soft
    return add_glow(img, cx, cy, int(r * 1.5), hi, 70)


# ---------------------------------------------------------------------------
# Layout: strip mode
# ---------------------------------------------------------------------------

def _header(img, planet, paper_band=True):
    """Draw the header. If paper_band, fill rows 0..83 with paper and put ink text on
    it (void cards). If not, the card is already full-bleed cream and the header
    simply floats (cream cards)."""
    d = ImageDraw.Draw(img)
    if paper_band:
        d.rectangle([0, 0, W, T.HEADER_STRIP_BOTTOM], fill=PAPER)
    T.draw_header(d, planet, ink_rgb=INK)


def _caption(img, text, x, y, dark_bg=True):
    """Floating caption ON the art (no band). Yellow on dark, ink on light."""
    d = ImageDraw.Draw(img)
    if dark_bg:
        T.draw_caption(d, text, (x, y), color_rgb=PAL['amber'], ink_rgb=INK)
    else:
        T.draw_caption(d, text, (x, y), color_rgb=INK, ink_rgb=PAPER)


def hero_word(draw, text, cx, cy, fill_rgb, stroke_rgb=None, stroke_width=3,
              px=64, margin=40, y_max=None, clamp=True):
    """Stamp ONE dominant outlined word across a card, clamped to the frame.

    WHY THIS EXISTS. Every beat module grew its own text helper, and each one
    clamped against `T._bbox`'s ADVANCE width. But `draw_outlined_text` draws a
    `stroke_width` keyline outside the glyphs on all four sides, so the stroked
    text is `stroke_width` px wider and taller than the box that was clamped.
    hook_not_alone shipped "A NEUTRON STAR" with its final R cut off by the right
    edge — the clamp said it fit and it did not, because the clamp did not know
    about the stroke.

    So the margin here is `margin + stroke_width`, and the measurement is taken
    from the same call the renderer makes. Optionally fit-to-width: if the text
    is still too wide for the drawable span, step the size DOWN (never step it
    below `min_px`) rather than let it run off the edge.

    Returns (x, y) so a caller can draw a leader line to the thing it labels.
    """
    stroke_rgb = stroke_rgb if stroke_rgb is not None else PAL['ink']
    avail = W - 2 * margin
    size = int(px)
    font = T.load_font_at(size, bold=True)
    bb = T._bbox(draw, text, font)
    w, h = bb[2], bb[3]
    # the stroked box is this much bigger than the advance box
    pad = int(stroke_width) * 2 + 2
    while w + pad > avail and size > 18:
        size -= 2
        font = T.load_font_at(size, bold=True)
        bb = T._bbox(draw, text, font)
        w, h = bb[2], bb[3]
    cx = W // 2 if cx is None else int(cx)
    x = int(cx - w / 2)
    y = int(cy - h / 2)
    if clamp:
        lo, hi = margin, W - margin - w - pad
        x = lo if hi < lo else max(lo, min(hi, x))
        top = T.ART_TOP + margin
        bot = (y_max if y_max is not None else H - margin) - h - pad
        y = top if bot < top else max(top, min(bot, y))
    # draw_outlined_text places by the glyph bbox origin, so shift by bb[0]/bb[1]
    T.draw_outlined_text(draw, (x - bb[0], y - bb[1]), text, font,
                         fill=fill_rgb, stroke=stroke_rgb,
                         stroke_width=int(stroke_width))
    return x, y, w, h


def hero_text(img, text, cx=None, cy=140, color_rgb=None, dark_bg=True,
              px=None, margin=48):
    """Draw one line of in-card emphasis text at a SANE size, with edge protection.

    Why this exists: the round-2 build kept drawing hero words ("RUBBLE",
    "MOON-SIZE", "A NEUTRON STAR") at the 48px HEADER scale, where they shouted,
    ran off the right edge, or collided with the floating caption. This helper
    clamps the size to the caption scale, clamps x so the string never crosses the
    frame margin, and drops y if it would collide with the caption band.

    Use this for the ONE dominant phrase on a card. Never for paragraph text.
    """
    d = ImageDraw.Draw(img)
    px = px or T.CAPTION_PX
    font = T.load_font(px, bold=True)
    bx, by, bw, bh = T._bbox(d, text, font)
    if cx is None:
        cx = W // 2
    x = int(cx - bw / 2)
    x = max(margin, min(x, W - bw - margin))
    y = int(cy)
    # keep hero text clear of the caption band (caption baseline sits at y=652)
    if y + bh > 640:
        y = 640 - bh
    if color_rgb is None:
        color_rgb = PAL['bone'] if dark_bg else INK
    T.draw_caption(d, text, (x, y), color_rgb=color_rgb, ink_rgb=INK if dark_bg else PAPER)
    return x, y, bw, bh


def _draw_stickman(img, card, theme):
    sm = card.get('stickman')
    if not sm:
        return
    S.draw_stickman(img, sm['x_center'], sm['y_top'], sm['height'],
                    pose=sm['pose'], mouth=sm['expression'], theme=theme)


# ---------------------------------------------------------------------------
# Card renderers, one per card family. Each returns a finished frame.
# Void cards: void_backdrop + paper strip + dark-theme stickman.
# Cream cards: full-bleed paper + floating header + light-theme stickman.
# ---------------------------------------------------------------------------

def render_hook_dead(card, planet="PSR B1257+12"):
    """Card 1 — the dead star, bone core + two FLAT violet halo rings, deadpan
    character. The opening card: establish the void, the star, and the surrogate."""
    img = Image.new('RGB', (W, H), PAL['deep'])
    void_backdrop(img, seed=0)

    # faint violet nebula wisp across the lower-left third — RGBA at low alpha
    dw = ImageDraw.Draw(img, 'RGBA')
    wisp = [(90, 575), (280, 530), (520, 590), (430, 672), (150, 668)]
    K.draw_smooth(dw, wisp, fill=PAL['violet'] + (26,), outline=None, seed=31, wobble=14)

    # dead star: bone core (emissive -> gradient legal) + 2 flat halo rings
    cx, cy, r = 980, 300, 46
    _radial_core(img, cx, cy, r, [(255, 255, 255), PAL['bone'], (60, 52, 92)])
    d = ImageDraw.Draw(img, 'RGBA')
    for rr, a in ((64, 30), (78, 48)):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=PAL['violet'] + (a,), width=3)

    T.draw_caption(d, "ALREADY DEAD", (cx - 130, cy - 18), color_rgb=PAL['bone'], ink_rgb=INK)

    _header(img, planet, paper_band=True)
    _draw_stickman(img, card, theme='dark')
    _caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


def render_masses(card, planet="PSR B1257+12"):
    """Card 11 — the mass ledger. CREAM card: full-bleed paper, floating header,
    dark character, FLAT discs (no gradient, no bands). The radii 16/40/42 carry
    the corrected fact: one Moon-ish speck, two near-twin heavies."""
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    _header(img, planet, paper_band=False)

    # three rules + one disc each
    rows = [200, 330, 460]
    xs = [700, 880, 1090]
    rad = [18, 40, 42]
    for y, x, rr in zip(rows, xs, rad):
        d.line([(560, y), (1180, y)], fill=INK, width=3)
        K.draw_disc(d, x, y, rr, fill=INK, outline=INK, width=3, seed=x)
    # mass figures on the discs
    T.draw_stamp(d, "MOON-SIZE", (560, 150), PAL['ink'])
    T.draw_stamp(d, "4 EARTH", (760, 280), PAL['ink'])
    T.draw_stamp(d, "4 EARTH", (970, 410), PAL['ink'])

    _draw_stickman(img, card, theme='light')
    _caption(img, card['caption'], 70, 652, dark_bg=False)
    return img


def render_finale(card, planet="PSR B1257+12"):
    """Card 31 — the whole system at once. Void, tiny core, three orbit ellipses,
    three painterly planets, bone labels. The character is deadpan_grim."""
    img = Image.new('RGB', (W, H), PAL['deep'])
    void_backdrop(img, seed=0)

    cx, cy = 900, 360
    d = ImageDraw.Draw(img, 'RGBA')
    # three orbit ellipses (bone, 2px)
    for rr, ry in ((150, 58), (240, 92), (330, 126)):
        d.ellipse([cx - rr, cy - ry, cx + rr, cy + ry], outline=PAL['bone'], width=2)
    # core
    _radial_core(img, cx, cy, 24, [(255, 255, 255), PAL['bone'], (60, 52, 92)])
    # three painterly planets on the inner rings
    for ang, rr_disc in ((200, 16), (20, 19), (320, 26)):
        a = math.radians(ang)
        px = cx + 150 * math.cos(a)
        py = cy + 58 * math.sin(a)
        img = space_body(img, px, py, rr_disc, seed=int(ang))
    # bone labels
    d = ImageDraw.Draw(img)
    T.draw_stamp(d, "DRAUGR", (600, 250), PAL['bone'], ink_rgb=INK)
    T.draw_stamp(d, "PHOBETOR", (600, 180), PAL['bone'], ink_rgb=INK)
    T.draw_stamp(d, "POLTERGEIST", (600, 110), PAL['bone'], ink_rgb=INK)

    _header(img, planet, paper_band=True)
    _draw_stickman(img, card, theme='dark')
    _caption(img, card['caption'], 70, 652, dark_bg=True)
    return img


# Dispatch by card id. Extended by the per-beat renderer modules.
RENDERERS = {
    'hook_dead': render_hook_dead,
    'planet_masses': render_masses,
    'close_finale': render_finale,
}


def register(mapping):
    """Merge a beat module's renderers into the dispatch table."""
    RENDERERS.update(mapping)


def render(card, planet="PSR B1257+12"):
    """Render one schedule card by id. Raises if no renderer is registered."""
    cid = card['id']
    fn = RENDERERS.get(cid)
    if fn is None:
        raise KeyError('no renderer for card %r; registered: %s'
                       % (cid, ', '.join(sorted(RENDERERS))))
    return fn(card, planet)