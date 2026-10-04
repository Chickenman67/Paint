# work3/lib/engine3.py -- the PROGRESSIVE, TIMED-REVEAL render engine.
#
# WHY THIS EXISTS (the defect it fixes)
#   The v2 engine (work/lib/v2engine.py) is POP-AND-HOLD: it draws one static card
#   and freezes it for 4-7 seconds. Measured against the reference
#   (work3/measure/REFERENCE_MEASUREMENTS.md):
#       OURS   : median gap between visual changes 5.08s, 96% still, 0% motion.
#       REF    : median gap between visual changes 1.00-1.67s, 83% still,
#                 7% motion, 10% cut.
#   So the old engine is ~3-4x too slow to change and has literally ZERO per-frame
#   motion. A single frozen card cannot match that bar.
#
# THE MODEL THIS ENGINE IMPLEMENTS
#   A beat is a SCENE: an ordered list of ELEMENTS. Each element is one visual
#   piece -- a background, a subject, the character, a caption fragment, a label,
#   a shape. Every element carries an `at` time = the WORD ONSET at which the
#   narrator begins the phrase that element illustrates.
#
#   Rendering a frame at time t:
#     - Composite every element whose `at <= t` (and, if it has one, `t < until`),
#       in list order (later = on top).
#     - An element may declare a MOTION TRACK: keyframes
#       [(t, x, y, scale, rot), ...]. At time t the engine interpolates the
#       transform (x, y offsets, scale, rotation) and composites the element at
#       that transform. This is what produces genuine PER-FRAME motion -- e.g. a
#       car driving in from off-frame, a character sliding to a mark, a planet
#       rotating -- instead of a frozen still.
#
#   Elements are drawn ONCE into a cached transparent tile (lazily, on first
#   render), then the engine composites that tile with the interpolated
#   transform. This keeps every draw call deterministic and side-effect free, and
#   makes a re-render byte-identical.
#
# DETERMINISM CONTRACT
#   render_frame(scene, t) is a pure function of (scene contents, t). There is no
#   wall-clock and no unseeded randomness anywhere in this module. Draw callables
#   are responsible for their own determinism (the ink/v2subjects primitives are
#   all seed-driven, so they are). The tile cache stores the FIRST render's bytes
#   and reuses them, so even a hypothetically non-deterministic draw callable
#   would still produce identical frames -- determinism is belt-and-braces.
#
# GEOMETRY MODEL
#   An element's draw callable renders into a transparent RGBA "tile" of the full
#   frame (1280x720) so the author can draw anywhere in absolute frame
#   coordinates -- the same coordinate space as the v2 primitives
#   (v2subjects/v2draw/ink all take absolute frame coords). The engine then
#   extracts the tile's ink bounding box once, crops to it, and composites at the
#   transform. An element therefore declares its art in frame coordinates, and
#   `motion` translates/scales/rotates that art about its own ink centroid.

import os
import sys
import math

from PIL import Image, ImageDraw

# Make the shared drawing primitives importable by absolute path. We do NOT
# rewrite them; we reuse them. See the module docstring for the contract.
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORK_LIB = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, "work", "lib"))
if os.path.isdir(_WORK_LIB) and _WORK_LIB not in sys.path:
    sys.path.insert(0, _WORK_LIB)

import numpy as np  # noqa: E402

# --- Frame constants (match the reference / v2type) -------------------------
W, H = 1280, 720
FPS = 60                      # the reference is 60 fps; match it

# Page + ink, sourced from v2type when available so we stay on the locked scale.
try:
    import v2type as _T          # noqa: E402
    PAPER = _T.PAPER
    INK = _T.INK
except Exception:                # pragma: no cover - fallback if libs absent
    _T = None
    PAPER = (253, 253, 253)
    INK = (0, 0, 0)

# Identity transform, used when an element has no motion track.
IDENTITY = (0.0, 0.0, 1.0, 0.0)   # (dx, dy, scale, rot_deg)


# ---------------------------------------------------------------------------
# keyframe interpolation
# ---------------------------------------------------------------------------

def _ease_in_out(u):
    """Smoothstep 0..1. Matches the reference's ease on drive-ins."""
    return u * u * (3.0 - 2.0 * u)


def _interp_keyframes(keys, t):
    """Interpolate a motion track at time t.

    keys: list of (t, x, y, scale, rot) tuples, sorted ascending by t.
    Returns (dx, dy, scale, rot).

    Before the first key and after the last key we CLAMP to that key's value
    (hold), so an element slides in over its window and then holds its final
    pose -- matching the reference's "move then hold" behaviour. Between keys we
    interpolate each channel linearly in eased time.
    """
    if not keys:
        return IDENTITY
    if t <= keys[0][0]:
        _, x, y, s, r = keys[0]
        return (x, y, s, r)
    if t >= keys[-1][0]:
        _, x, y, s, r = keys[-1]
        return (x, y, s, r)

    # find bracketing keys
    for i in range(len(keys) - 1):
        t0, x0, y0, s0, r0 = keys[i]
        t1, x1, y1, s1, r1 = keys[i + 1]
        if t0 <= t <= t1:
            span = t1 - t0
            u = 0.0 if span <= 0 else (t - t0) / span
            e = _ease_in_out(u)
            dx = x0 + (x1 - x0) * e
            dy = y0 + (y1 - y0) * e
            sc = s0 + (s1 - s0) * e
            rot = r0 + (r1 - r0) * e
            return (dx, dy, sc, rot)
    # Unreachable for well-formed keys, but be safe.
    _, x, y, s, r = keys[-1]
    return (x, y, s, r)


# ---------------------------------------------------------------------------
# Element
# ---------------------------------------------------------------------------

class Element:
    """One revealable, optionally-moving piece of a scene.

    id:     unique string id (for tests / debugging)
    kind:   'bg' | 'subject' | 'character' | 'text' | 'shape'
    draw:   callable(tile_rgba, frame_w, frame_h) -> None
            Renders the element's art INTO the provided transparent RGBA tile,
            in absolute frame coordinates (0,0)-(W,H). It is called at most once
            (its bytes are cached), so it may be relatively expensive.
    at:     reveal time in seconds (the word onset). Element is hidden for t < at.
    motion: optional list of (t, x, y, scale, rot) keyframes. Offsets are in px
            relative to the element's authored position; scale multiplies size
            about the element's ink centroid; rot is degrees clockwise.
    until:  optional time; the element is hidden for t >= until.
    """

    __slots__ = ("id", "kind", "draw", "at", "motion", "until",
                 "_tile", "_built", "_origin")

    def __init__(self, id, kind, draw, at=0.0, motion=None, until=None):
        self.id = id
        self.kind = kind
        self.draw = draw
        self.at = float(at)
        # normalise + copy so the track cannot be mutated behind our back
        self.motion = sorted(tuple(k) for k in motion) if motion else None
        self.until = None if until is None else float(until)
        self._tile = None     # cropped RGBA ink tile
        self._built = False

    # -- visibility ---------------------------------------------------------

    def visible(self, t):
        """Is this element part of the frame at time t?"""
        if t < self.at - 1e-9:
            return False
        if self.until is not None and t >= self.until - 1e-9:
            return False
        return True

    # -- tile construction (deterministic, cached) --------------------------

    def _build_tile(self):
        """Render the element once into a transparent tile cropped to its ink.

        The draw callable renders into a full-frame transparent RGBA canvas (so
        the author can use absolute frame coords). We then crop to the non-empty
        alpha bounding box and remember the crop origin so transforms are applied
        about the true ink centroid. Returns (tile_rgba, origin_xy) or
        (None,(0,0)) if the element drew nothing."""
        if self._built:
            return (self._tile, self._origin)

        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.draw(canvas, W, H)
        alpha = canvas.getchannel("A")
        bbox = alpha.getbbox()
        self._built = True
        if bbox is None:
            self._tile = None
            self._origin = (0, 0)
            return None, (0, 0)
        tile = canvas.crop(bbox).convert("RGBA")
        self._tile = tile
        self._origin = (bbox[0], bbox[1])
        return tile, self._origin

    def tile_and_origin(self):
        return self._build_tile()

    # -- transform at time t ----------------------------------------------

    def transform_at(self, t):
        """Interpolated (dx, dy, scale, rot) at absolute time t."""
        if not self.motion:
            return IDENTITY
        return _interp_keyframes(self.motion, t)

    # -- draw into a page ---------------------------------------------------

    def draw_at(self, page, t):
        """Composite this element onto `page` (RGB) at absolute time t, applying
        its interpolated transform. Returns True if it drew, else False."""
        if not self.visible(t):
            return False
        tile, origin = self._build_tile()
        if tile is None:
            return False
        dx, dy, scale, rot = self.transform_at(t)
        composited = _apply_transform(tile, dx, dy, scale, rot, origin)
        if composited is None:
            return False
        cim, cx0, cy0 = composited
        page.paste(cim, (cx0, cy0), cim)
        return True


# ---------------------------------------------------------------------------
# transform application (per-frame motion)
# ---------------------------------------------------------------------------

def _apply_transform(tile, dx, dy, scale, rot, origin):
    """Return (composited_rgba, paste_x, paste_y) for a tile moved by
    (dx, dy), scaled by `scale` and rotated `rot` degrees.

    Scale and rotation are applied to the TILE ONLY, never to the whole frame,
    so a moving element can never drag the title strip or a sibling with it
    (the failure documented in work/lib/motion.py and in project memory as
    "motion-layer-must-not-move-layout").

    Geometry: the element's authored ink centroid sits at frame position
    (origin_x + tw/2, origin_y + th/2). After scale/rotate the new tile has size
    (nw, nh) whose own centre must land at that same frame position (plus the
    requested dx/dy offset). Hence:

        paste_x = origin_x + tw/2 - nw/2 + dx
        paste_y = origin_y + th/2 - nh/2 + dy

    which reduces to origin + dx when nothing is scaled or rotated (nw==tw).
    """
    tw, th = tile.size

    # Fast path: identity transform -> paste the cached tile as-is.
    if (abs(dx) < 1e-6 and abs(dy) < 1e-6
            and abs(scale - 1.0) < 1e-6 and abs(rot) < 1e-6):
        return tile, origin[0], origin[1]

    nw, nh = tw, th
    if abs(scale - 1.0) > 1e-6:
        nw = max(1, int(round(tw * scale)))
        nh = max(1, int(round(th * scale)))
        tile = tile.resize((nw, nh), Image.BICUBIC)
    if abs(rot) > 1e-6:
        # PIL rotates counter-clockwise for positive degrees; a positive `rot`
        # here means clockwise on screen, hence the negation.
        tile = tile.rotate(-rot, resample=Image.BICUBIC, expand=True)
        nw, nh = tile.size

    paste_x = int(round(origin[0] + tw / 2.0 - nw / 2.0 + dx))
    paste_y = int(round(origin[1] + th / 2.0 - nh / 2.0 + dy))
    return tile, paste_x, paste_y


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class Scene:
    """An ordered list of elements with optional global metadata.

    elements: list of Element, composited in list order (later on top). Author
              them in the order they should stack; the engine does NOT re-sort,
              because stacking order and reveal order are independent.
    title:    optional persistent chapter-title string, drawn LAST, on top of
              everything, never moved by any element.
    duration: the scene length in seconds. Informational; frame_count derives
              from it.
    """

    def __init__(self, elements=None, title=None, title_seed=0, duration=None):
        self.elements = list(elements or [])
        self.title = title
        self.title_seed = title_seed
        if duration is None:
            # default duration: last element's `at`, or a small tail, so a
            # hand-built scene without explicit duration still renders frames.
            last = max((e.at for e in self.elements), default=0.0)
            ends = max((e.until for e in self.elements if e.until is not None),
                       default=0.0)
            duration = max(last, ends) + 1.0
        self.duration = float(duration)

    def add(self, element):
        self.elements.append(element)
        return element

    def extend(self, elements):
        self.elements.extend(elements)
        return self

    def frame_count(self, fps=FPS):
        return int(round(self.duration * fps))

    def visible_at(self, t):
        return [e for e in self.elements if e.visible(t)]

    def next_reveal_after(self, t):
        """The next element reveal time strictly after t (or None)."""
        future = [e.at for e in self.elements if e.at > t + 1e-9]
        return min(future) if future else None


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def _blank_page():
    return Image.new("RGB", (W, H), PAPER)


def render_frame(scene, t):
    """Render `scene` at absolute time t -> a fresh 1280x720 RGB PIL Image.

    Composites every visible element in list order, then the persistent title
    last. Pure function of (scene, t)."""
    page = _blank_page()
    for el in scene.elements:
        el.draw_at(page, t)
    if scene.title:
        _draw_title(page, scene.title, seed=scene.title_seed)
    return page


def _draw_title(page, text, seed=0):
    """Draw the persistent chapter title, reusing v2draw when available.

    Falls back to a plain bold text draw if v2draw can't be imported, so the
    engine never hard-depends on the shared lib being present.
    """
    try:
        import v2draw as _D
        _D.draw_title(page, text, seed=seed)
        return
    except Exception:
        pass
    d = ImageDraw.Draw(page)
    font = None
    if _T is not None:
        try:
            font = _T.title_font()
        except Exception:
            font = None
    if font is not None:
        try:
            w = font.getlength(text)
            r = font.getbbox(text)
            d.text((W / 2 - w / 2 - r[0], 21 - r[1]), text, font=font, fill=INK)
            return
        except Exception:
            pass
    d.text((W / 2 - 4 * len(text), 21), text, fill=INK)


def render_range(scene, fps=FPS, t0=0.0, t1=None):
    """Render an inclusive-exclusive range of frames as a list of images.
    t0/t1 in seconds; t1 defaults to scene.duration."""
    if t1 is None:
        t1 = scene.duration
    n = int(round((t1 - t0) * fps))
    return [render_frame(scene, t0 + i / fps) for i in range(n)]


# ---------------------------------------------------------------------------
# frame-difference metrics (so tests + measurement share ONE definition)
# ---------------------------------------------------------------------------

def frame_diff(a, b):
    """Fraction of pixels that differ between two RGB frames, 0..1.

    Counts a pixel as 'different' if any channel differs by more than a small
    tolerance. Uses the same idea as the reference measurement (fraction of
    changed pixels between consecutive frames).
    """
    aa = np.asarray(a, dtype=np.int16)
    bb = np.asarray(b, dtype=np.int16)
    if aa.shape != bb.shape:
        return 1.0
    diff = np.abs(aa - bb).max(axis=2)
    return float((diff > 8).mean())


def motion_profile(frames, still_thresh=0.002):
    """Classify consecutive frame pairs as still / motion / cut.

    Returns (still_frac, motion_frac, cut_frac) mirroring the reference's
    83% / 7% / 10% split. A pair is:
      - still  : diff < still_thresh
      - motion : still_thresh <= diff < cut_thresh  (something moved, not a cut)
      - cut    : diff >= cut_thresh                (a reveal / big change)
    We expose cut_thresh so callers can tune; default matches the measurement's
    spirit (a reveal adds a whole element, so it's a larger delta).
    """
    cut_thresh = 0.02
    n = len(frames) - 1
    if n <= 0:
        return 1.0, 0.0, 0.0
    still = motion = cut = 0
    for i in range(n):
        d = frame_diff(frames[i], frames[i + 1])
        if d < still_thresh:
            still += 1
        elif d < cut_thresh:
            motion += 1
        else:
            cut += 1
    return still / n, motion / n, cut / n


def changed_pair_fraction(frames, thresh=0.0):
    """Simple fraction of consecutive frame pairs that are NOT byte-identical.
    This is the metric the task's test asserts (>20%)."""
    n = len(frames) - 1
    if n <= 0:
        return 0.0
    same = sum(1 for i in range(n) if frames[i].tobytes() == frames[i + 1].tobytes())
    return (n - same) / n


# ---------------------------------------------------------------------------
# convenience builders -- so a scene author writes one line per element
# ---------------------------------------------------------------------------

def E(id, kind, draw, at=0.0, motion=None, until=None):
    """Shorthand constructor for an Element."""
    return Element(id, kind, draw, at=at, motion=motion, until=until)


def reveal_every(scene_elements, draw, kind="subject", start=0.0, step=1.2,
                 n=None, motion=None):
    """Helper: produce `n` elements revealing every `step` seconds starting at
    `start`, all sharing the same draw callable but drawn with an index. The
    draw callable is called as draw(tile, W, H, i) -- but to keep Element.draw
    uniform we wrap it. Returns the list of elements (not added to a scene)."""
    if n is None:
        raise ValueError("reveal_every needs n")
    out = []
    for i in range(n):
        idx = i

        def wrapped(tile, fw, fh, _idx=idx):
            draw(tile, fw, fh, _idx)

        out.append(E("auto%d" % i, kind, wrapped, at=start + i * step,
                     motion=motion))
    return out
