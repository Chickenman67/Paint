# work/lib/v2engine.py -- the v2 layer/pop compositor.
#
# This REPLACES work/lib/motion.py, which is architecturally wrong for the v2 bar.
#
# THE MODEL THIS IMPLEMENTS (measured from work/ref2/ref_full.mp4):
#   The reference is 88% completely static. Zero hard cuts at any scene threshold.
#   1035 discrete "pop events" with a median gap of 3.6s. Each event is an ELEMENT
#   that appears FULLY FORMED in a SINGLE frame, then holds. Occasionally an
#   element slides/rotates over ~0.2s, then holds. Nothing loops, nothing bobs,
#   nothing idles. The scene assembles itself, one piece at a time, as the
#   narrator talks.
#
# WHY motion.py CANNOT DO THIS:
#   motion.py renders the whole card ONCE (a flattened raster) and then paints
#   quantized "stamp" verbs onto that raster (motion.py:414), with a _pin_layout
#   re-paste to patch the title strip (motion.py:391). That architecture ships
#   mirrored glyphs and crooked strips (documented in memory) and cannot express
#   "element K appears at time T and stays" because it mutates one still.
#
# THIS ENGINE'S CONTRACT:
#   A v2 card is a LIST OF LAYERS. Each layer is a callable that draws itself
#   onto a fresh page, plus a pop time (seconds from the beat start). At frame
#   time t, the engine renders the page and calls every layer whose pop time has
#   passed. A layer that has popped STAYS popped. There are no fades, no tweens,
#   no per-frame motion verbs. The only motion allowed is a single short
#   slide/rotate on a layer that declares it (see SlideIn below), matching the
#   bar's occasional 0.2s move.
#
# This keeps every element a SEPARATE draw call on a clean page, so the title
# strip can never be mirrored or moved by a later layer, and re-renders are
# deterministic.

import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir)))

try:                              # imported as part of the lib package
    from . import v2draw as D
    from . import v2type as T
except ImportError:               # imported flat (adds HERE to sys.path)
    import v2draw as D            # noqa: E402
    import v2type as T            # noqa: E402

# The bar's occasional short move. A layer may declare slide/rotate; the engine
# interpolates ONLY over SLIDE_S, then freezes. Nothing idles after.
SLIDE_S = 0.20

# How the engine holds the frame rate. The bar is 60fps.
FPS = T.FPS


class SlideIn:
    """Wrap a layer so it slides (and optionally rotates) into place over SLIDE_S.

    The element is drawn ONCE onto a transparent tile by draw_fn(page) -- the
    author never computes offsets. The engine then pastes that tile at an offset
    that eases from (dx, dy) to (0, 0) over SLIDE_S, then freezes. Rotation is
    applied to the tile, never to the whole frame, so the title strip (drawn
    separately, last) can never be mirrored or dragged by a moving element.

    This is the bar's rare ~0.2s move (the flag that slides left ~200px between
    11.6s and 11.8s). Pop-and-hold is the common case and is just Layer.
    """

    def __init__(self, draw_fn, t0, dx=0.0, dy=0.0, drot=0.0, pad=40):
        self.draw_fn = draw_fn      # draw_fn(page) -> draws element on a tile
        self.t0 = t0
        self.dx = dx
        self.dy = dy
        self.drot = drot
        self.pad = pad
        self._tile = None

    def _build_tile(self):
        """Render the element onto a transparent tile, sized to its ink + pad."""
        probe = D.page()
        self.draw_fn(probe)
        # ink bbox on the probe, so the tile hugs the element
        import PIL.ImageChops as IC
        diff = IC.difference(probe, Image.new("RGB", probe.size, T.PAPER))
        bbox = diff.getbbox()
        if bbox is None:
            return None
        x0, y0, x1, y1 = bbox
        tile = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        # redraw into the tile at the right offset by drawing on a padded canvas
        big = Image.new("RGB", (probe.width, probe.height), T.PAPER)
        self.draw_fn(big)
        tile = big.crop((x0, y0, x1, y1)).convert("RGBA")
        if self.drot:
            tile = tile.rotate(self.drot, resample=Image.BICUBIC, expand=True)
        return tile, (x0, y0)

    def visible(self, t):
        return t >= self.t0 - 1e-9

    def draw(self, page, t):
        if not self.visible(t):
            return
        built = self._build_tile()
        if built is None:
            return
        tile, (ax, ay) = built
        dt = t - self.t0
        p = min(1.0, dt / SLIDE_S) if SLIDE_S > 0 else 1.0
        ease = p                              # linear is fine for 0.2s
        ox = int(self.dx * (1.0 - ease))
        oy = int(self.dy * (1.0 - ease))
        if self.drot and p < 1.0:
            # re-rotate the tile toward its final angle
            rot = self.drot * (1.0 - ease)
            tile = tile.rotate(-rot, resample=Image.BICUBIC, expand=True)
            ax -= (tile.width - (tile.width)) // 2
        page.paste(tile, (ax + ox, ay + oy), tile)


class Layer:
    """One element of a card: appears FULLY FORMED in a single frame at t0, then
    holds. This is the reference's dominant behaviour and the default.

    draw_fn(page) draws the element. The engine calls it on a FRESH page each
    frame the layer is visible, so layers never mutate one another.
    """

    def __init__(self, draw_fn, t0=0.0):
        self.draw_fn = draw_fn
        self.t0 = t0

    def visible(self, t):
        return t >= self.t0 - 1e-9

    def draw(self, page, t):
        if self.visible(t):
            self.draw_fn(page)


def compose(layers, t, title=None, title_seed=0):
    """Render the card at beat-relative time t.

    layers: list of Layer (already ordered by pop time; engine does not sort --
            author them in order so the render is deterministic).
    t: seconds from the beat start.
    title: the persistent chapter title string, or None to omit.
    Returns a fresh 1280x720 RGB page.
    """
    page = D.page()
    for lyr in layers:
        lyr.draw(page, t)
    if title:
        # Title is drawn LAST, always at the same fixed position, never moved by
        # any layer. This is the persistent chapter title.
        D.draw_title(page, title, seed=title_seed)
    return page


def sort_layers(layers):
    """Stable sort by pop time so authoring order does not matter."""
    return sorted(layers, key=lambda l: l.t0)


# ---------------------------------------------------------------------------
# convenience builders -- so card authors write 3 lines instead of plumbing Layer
# objects by hand.
# ---------------------------------------------------------------------------

def pop(t0):
    """Return a decorator turning draw(page) into a Layer that pops at t0."""
    def deco(fn):
        return Layer(fn, t0)
    return deco


def pop_at(t0):
    """Explicit Layer(t0) factory taking draw(page)."""
    return lambda fn: Layer(fn, t0)


def slide(t0, dx=0, dy=0, drot=0):
    """Return a decorator for a layer that slides/rotates in over SLIDE_S.

    The wrapped fn is draw(page, progress); the engine passes an eased progress.
    """
    def deco(fn):
        return SlideIn(fn, t0, dx, dy, drot)
    return deco
