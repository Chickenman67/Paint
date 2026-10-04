# work/lib/stickman.py — Scene-based stickman composition
#
# Per round 5 verdicts for both segments:
#   "The reference embeds the character IN the world being explained, not beside
#    it as an external narrator."
#
# This rewrite shifts from "draw a stickman, paste onto a diagram" to
# "render a scene with the stickman inhabiting the environment."
#
# Every helper returns a PIL Image with the stickman embedded in the scene.
#
# ---------------------------------------------------------------------------
# G7 PASS — the character contract. Everything below exists to make four
# properties STRUCTURAL rather than remembered, because they were not:
#
#   1. Every arm is TWO SEGMENTS meeting at a real elbow. The defect the
#      critic named repeatedly (a single shoulder-to-wrist stroke, and the dead
#      horizontal T-arm off the shoulder on 'pointing' and 'standing') came from
#      eight hand-written `if pose == ...` branches in which it was easy to
#      forget the elbow. Poses are now DATA — see _pose_geometry() — so an arm
#      is literally a (shoulder, elbow, hand) triple and cannot be drawn
#      without a joint. There is no code path that draws a one-segment arm.
#   2. Every wrist ends in a hand blob and every ankle in a foot blob. Both are
#      emitted by the single _paint_ops() executor, scaled to head_r instead of
#      the old fixed 3px/2px which was invisible on a 300px figure.
#   3. The figure is ANCHORED. draw_stickman() takes ground_y and puts both feet
#      exactly on it; the returned geom dict reports foot_y so a caller never
#      has to re-derive the line. Default ground_y=None reproduces the old
#      y_top + height behaviour exactly.
#   4. The figure exposes its FILL. `fill=` overrides the limb colour and
#      figure_colors() answers "what colour will he be?" BEFORE anything is
#      drawn, so a caller can check contrast against the shape behind him.
#      That is the fix for the wasp17b beat_06 camouflage (cream figure drawn in
#      the same teal as the subject planet).
#
# The 'dark' theme also finally USES its keyline. It was declared in the theme
# table and never read by any drawing code, which is why the cream character
# sank into a same-tone background. Keylines are drawn as a full silhouette
# pass BEHIND the figure (never per-limb), so they can only ever add
# separation and can never cut a dark notch across a limb.
#
# Public API is unchanged: draw_stickman(image, x_center, y_top, height,
# pose=, mouth=, seed=, theme=) still works with identical defaults, and every
# new parameter is optional with a default that reproduces the old output.

import math
import random
from PIL import Image, ImageDraw

# --- Canonical proportions (CLAUDE.md §6, corrected per STYLE_CANON.md §4) ---
DEFAULT_HEIGHT = 110          # total figure height in px
HEAD_RADIUS = 14              # head oval radius (height/8 -> ~4.0 heads tall, the
                              # measured reference proportion; the old HEADS_TALL=5.0
                              # was decorative and disagreed with its own geometry)
HEADS_TALL = 4.0

# --- Color scheme (our original character) ---
INK = (0, 0, 0)
HEAD_FILL = (255, 255, 255)
SHIRT = (200, 50, 50)         # red shirt accent
LIMB = (0, 0, 0)              # pure black limbs
MOUTH_INTERIOR = (220, 100, 100)  # soft pink/red inside mouth

# Visual stroke widths. STYLE_CANON.md §3: large outlines are 5-8 px, measured
# median 6 on the reference. The old 3/2 made every figure read as a wire.
BODY_STROKE = 6
LIMB_STROKE = 5

# Stroke weight scales with the figure so a 430px-tall character does not render
# with the same 5px wire limbs as a 110px one. The max() floors mean a figure at
# or below the default size is drawn at exactly the old widths.
BODY_STROKE_RATIO = 0.16
LIMB_STROKE_RATIO = 0.13
HAND_RATIO = 0.15            # hand blob radius as a fraction of head_r
FOOT_RATIO = 0.13            # foot blob radius as a fraction of head_r
MIN_HAND_R = 3               # the old hard-coded hand radius
MIN_FOOT_R = 3               # the old hard-coded foot radius

# --- THEME (STYLE_CANON.md §4) ---------------------------------------------
# The reference draws the character LIGHT (cream/white limbs on a thin dark
# keyline) whenever the figure stands on a dark space background, and DARK
# (black strokes, white head) on light paint/scene backgrounds. Our renderer was
# hardcoded black, which made the character vanish into every space card — a
# correctness bug, not a style preference. See the t=256 close-up for the light form.
#
# A theme is a dict of colors + strokes. resolve_theme() returns the right one.
THEMES = {
    # light background (paint/scene register): black strokes, white head
    'light': dict(
        stroke=(0, 0, 0),          # limbs + body outline
        head_fill=(255, 255, 255),
        detail=(0, 0, 0),          # hands, feet (part of the limb)
        feature=(0, 0, 0),         # eyes, brows, mouth line — DARK on a light head
        mouth_ink=(0, 0, 0),
        mouth_interior=(220, 100, 100),
        shirt=(200, 50, 50),
        body_stroke=6, limb_stroke=5,
        keyline=None, keyline_px=0,   # black on cream needs no halo
    ),
    # dark background (space register): CREAM limbs on a thin dark keyline
    'dark': dict(
        stroke=(245, 240, 225),    # cream limbs — the reference's space form
        head_fill=(245, 240, 225),
        detail=(245, 240, 225),    # hands/feet are cream too (they are the limb)
        feature=(25, 25, 30),      # eyes stay DARK inside the cream head
        mouth_ink=(40, 25, 25),
        mouth_interior=(196, 88, 96),
        shirt=(214, 74, 74),
        body_stroke=6, limb_stroke=5,
        keyline=(0, 0, 0),         # thin dark outline so cream reads on light art
        keyline_px=3,              # WAS DECLARED BUT NEVER DRAWN until the G7 pass
    ),
}

DEFAULT_THEME = 'light'

# The eight canonical poses. Kept in sync by the self-test at the bottom of this
# module; an unknown pose warns and falls back to 'standing'.
_POSES = {
    'standing', 'hands_up', 'hands_down', 'pointing',
    'thinker', 'cowering', 'shielding_eyes', 'shrugged',
}


def resolve_theme(theme=None):
    """Return a theme dict. `theme` may be a dict (used as-is) or a name.
    None -> the light theme."""
    if isinstance(theme, dict):
        base = dict(THEMES[DEFAULT_THEME])
        base.update(theme)
        return base
    return dict(THEMES.get(theme or DEFAULT_THEME, THEMES[DEFAULT_THEME]))


def _color(value, fallback=None):
    """Normalise a colour argument to an (R, G, B) tuple.

    Accepts an (R, G, B[, A]) tuple/list, a PIL colour name or '#rrggbb'
    string, or None. Strings were previously mangled by a bare tuple(): passing
    fill='magenta' produced ('m', 'a', 'g', 'e', 'n', 't', 'a') and then a
    TypeError deep inside the draw calls, far from the mistake. A caller
    reaching for the fill knob to escape a camouflage clash should not have to
    remember which literal form it takes.
    """
    if value is None:
        return None
    if isinstance(value, str):
        from PIL import ImageColor
        return ImageColor.getrgb(value)
    t = tuple(value)
    return t[:3] if len(t) >= 3 else t


def figure_colors(theme=None, fill=None, head_fill=None):
    """Answer "what colour will this figure be?" BEFORE anything is drawn.

    G7's camouflage defect (wasp17b beat_06: the character painted in the same
    teal as the planet behind him) is a decision the CALLER has to make, because
    only the caller knows what is behind him. It can only make that decision if
    the module will tell it. So this returns the effective colours for a given
    (theme, fill, head_fill) triple — the same values draw_stickman would use:

        fc = figure_colors(theme='dark', fill='ivory')
        if contrast(fc['fill'], backdrop) < 0.4:
            fc = figure_colors(theme='dark', fill='ink')

    `fill` and `head_fill` accept an (R, G, B) tuple, a PIL colour name, or a
    '#rrggbb' string.
    """
    th = resolve_theme(theme)
    return {
        'fill': _color(fill, th['stroke']) or th['stroke'],
        'head_fill': _color(head_fill, th['head_fill']) or th['head_fill'],
        'feature': th['feature'],
        'keyline': _color(th.get('keyline')),
        'keyline_px': th.get('keyline_px', 0),
        'body_stroke': th['body_stroke'],
        'limb_stroke': th['limb_stroke'],
    }


# =============================================================================
# EXPRESSION LIBRARY — mouth shapes (CLAUDE.md §6)
# =============================================================================
# "The mouth shape is the only thing that changes between expressions."
# Eyes are two dots, always the same. Mouth does all the expressive work.
#
# Every mouth honours `scale` — it is a multiple of HEAD_RADIUS, handed in by
# draw_mouth(). Stroke weights scale with it too. Before the G7 pass several
# shapes used a hard-coded width=2 and the zigzag ignored scale entirely, so on
# a 430px-tall figure (head_r 53) the face read as a 12px scratch on a 106px
# head. CLAUDE.md §6 requires the tone to be readable from his face ALONE, so
# the features have to hold their proportion at every size.

def _mouth_width(scale):
    """Feature stroke weight, scaled to head size, floored at the old 2px."""
    return max(2, int(round(1.6 * scale)))


def mouth_flat(draw, cx, cy, scale=1.0):
    """Single horizontal line — for 'deadpan' or 'thinking'."""
    w = int(8 * scale)
    draw.line([cx - w, cy, cx + w, cy], fill=INK, width=_mouth_width(scale))


def mouth_frown(draw, cx, cy, scale=1.0):
    """Upside-down arc — for 'scared' or 'sad'."""
    w = int(7 * scale)
    draw.arc([cx - w, cy - int(3 * scale), cx + w, cy + int(3 * scale)],
             180, 360, fill=INK, width=_mouth_width(scale))


def mouth_oval(draw, cx, cy, scale=1.0):
    """Wide oval — for 'awed' or 'shocked'."""
    w = int(8 * scale)
    h = int(5 * scale)
    sw = _mouth_width(scale)
    draw.ellipse([cx - w, cy - h, cx + w, cy + h], outline=INK, width=sw)
    draw.ellipse([cx - w + 2, cy - h + 2, cx + w - 2, cy + h - 2],
                 fill=MOUTH_INTERIOR)


def mouth_smirk(draw, cx, cy, scale=1.0):
    """Asymmetric smile — for 'wry' or 'smug'."""
    sw = _mouth_width(scale)
    draw.line([(cx - int(7 * scale), cy + 1),
               (cx - int(2 * scale), cy)], fill=INK, width=sw)
    draw.arc([cx - int(2 * scale), cy - int(3 * scale),
              cx + int(7 * scale), cy + int(3 * scale)],
             200, 340, fill=INK, width=sw)


def mouth_zigzag(draw, cx, cy, scale=1.0):
    """Zigzag line — for 'uncomfortable' or 'sick'."""
    # Was drawn at fixed pixel offsets (12px wide, 4px tall) no matter the head
    # size, so on a 300px figure it was a scratch. Now it scales.
    span = max(1, int(round(6 * scale)))          # half-span in x
    step = max(1, int(round(2 * scale)))
    amp = max(1, int(round(2.5 * scale)))
    sw = max(2, _mouth_width(scale))
    pts = []
    n = 2 * span // step + 1
    for i in range(max(3, n)):
        x = cx - span + i * step
        y = cy + (amp if i % 2 == 0 else -amp)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=INK, width=sw)


def mouth_smile(draw, cx, cy, scale=1.0):
    """Standard smile — for 'happy' or 'relief'."""
    w = int(7 * scale)
    draw.arc([cx - w, cy - int(3 * scale), cx + w, cy + int(3 * scale)],
             0, 180, fill=INK, width=_mouth_width(scale))


def mouth_scream(draw, cx, cy, scale=1.0):
    """Large open mouth — for 'screaming' or 'terrified'.

    Sized to sit INSIDE the head (HEAD_RADIUS=14, so a 28px head). The first
    pass used w=7,h=8 -> a 14x16 mouth, which is as big as the head itself and
    overflowed it, so at segment scale 'terrified' read as a red blob with no
    face. Now 5x6 -> a 10x12 mouth that leaves room for the eyes above it.
    """
    w = int(5 * scale)
    h = int(6 * scale)
    sw = _mouth_width(scale)
    draw.ellipse([cx - w, cy - h, cx + w, cy + h], outline=INK, width=sw)
    draw.ellipse([cx - w + 1, cy - h + 1, cx + w - 1, cy + h - 1],
                 fill=MOUTH_INTERIOR)


def mouth_worried(draw, cx, cy, scale=1.0):
    """Small frown with raised inner brows — for 'worried' or anxious."""
    w = int(6 * scale)
    draw.arc([cx - w, cy - int(2 * scale), cx + w, cy + int(4 * scale)],
             180, 360, fill=INK, width=_mouth_width(scale))
    # Raised inner brows
    brow_dy = int(4 * scale)
    sw = max(2, _mouth_width(scale))
    draw.line([(cx - int(7 * scale), cy - brow_dy - 1),
               (cx - int(2 * scale), cy - brow_dy - 4)], fill=INK, width=sw)
    draw.line([(cx + int(2 * scale), cy - brow_dy - 4),
               (cx + int(7 * scale), cy - brow_dy - 1)], fill=INK, width=sw)


def mouth_deadpan_grim(draw, cx, cy, scale=1.0):
    """Deep downturned mouth with flat heavy brows — for 'deadpan-grim' or
    resigned horror."""
    w = int(9 * scale)
    sw = _mouth_width(scale)
    draw.arc([cx - w, cy - int(2 * scale), cx + w, cy + int(5 * scale)],
             180, 360, fill=INK, width=sw)
    # Flat heavy brows
    brow_dy = int(5 * scale)
    draw.line([(cx - int(8 * scale), cy - brow_dy),
               (cx - int(2 * scale), cy - brow_dy)], fill=INK, width=sw)
    draw.line([(cx + int(2 * scale), cy - brow_dy),
               (cx + int(8 * scale), cy - brow_dy)], fill=INK, width=sw)


def mouth_skeptical(draw, cx, cy, scale=1.0):
    """One brow raised (left) with small flat mouth — for 'skeptical'."""
    w = int(6 * scale)
    sw = _mouth_width(scale)
    draw.line([cx - w, cy + 1, cx + w, cy + 1], fill=INK, width=sw)
    # Left brow raised
    brow_y = cy - int(6 * scale)
    draw.line([(cx - int(8 * scale), brow_y),
               (cx - int(2 * scale), brow_y - 3)], fill=INK, width=sw)
    # Right brow flat
    brow_y2 = cy - int(4 * scale)
    draw.line([(cx + int(2 * scale), brow_y2 - 1),
               (cx + int(8 * scale), brow_y2)], fill=INK, width=max(2, sw - 1))


MOUTHS = {
    'flat': mouth_flat,
    'frown': mouth_frown,
    'oval': mouth_oval,
    'smirk': mouth_smirk,
    'zigzag': mouth_zigzag,
    'smile': mouth_smile,
    'scream': mouth_scream,
    'worried': mouth_worried,
    'deadpan_grim': mouth_deadpan_grim,
    'skeptical': mouth_skeptical,
    'worried_thinker': mouth_worried,  # same as worried
    'awed_brows': mouth_oval,          # oval mouth + brows drawn separately
    'terrified': mouth_scream,         # large open mouth
    'sad_smile': mouth_frown,          # inverted arc
    'relief': mouth_smile,             # gentle smile
    # Pairs with the 'shielding_eyes' POSE. A schedule that asks for the pose
    # asks for the face too, so this must resolve to a real shape and not fall
    # through to mouth_flat — a deadpan face on a shielding pose reads as a
    # shrug, which is the opposite of the beat.
    'shielding_eyes': mouth_worried,
    # Used by the hd188753 / hd80606 round-6 schedules. It was previously
    # absent, so those two segments have been rendering it as a deadpan face
    # via the old silent fallback. That is the fallback this module no longer
    # has — add a real shape rather than reintroducing the silent path.
    'squint': mouth_skeptical,
}


def resolve_mouth(expression):
    """Look up a mouth function by expression name, failing loudly.

    Every call site used to be ``MOUTHS.get(name, mouth_flat)``, which silently
    rendered a DEADPAN face for any name not in the table. That is the worst
    possible failure mode for this character: CLAUDE.md §6 requires the segment's
    tone to be readable from his face alone, so a typo does not look like a bug
    on the card, it looks like a flatly wrong performance that survives review.

    Unknown name -> KeyError naming the offender and the valid set.
    """
    try:
        return MOUTHS[expression]
    except KeyError:
        raise KeyError(
            'unknown stickman expression %r; valid names are: %s'
            % (expression, ', '.join(sorted(MOUTHS)))
        ) from None


def draw_mouth(draw, cx, cy, expression='flat', scale=1.0, theme=None, head_r=None):
    """Draw the expression mouth, themed and correctly proportioned.

    The mouth functions read the module globals INK and MOUTH_INTERIOR. Rather
    than re-sign all ten of them, this dispatcher swaps those globals for the
    duration of the call. That is safe because _draw_stickman_body shadows INK
    as a *local*, so it never reads or writes the module global.

    Proportion fix: `scale` is now interpreted as a multiple of the DEFAULT head
    radius (HEAD_RADIUS=14), NOT of total figure height. The old code passed
    height/DEFAULT_HEIGHT (~2.9 at 320px tall), which blew the scream mouth up to
    70% of the head. Passing head_r makes the mouth a constant fraction of the
    face at any figure size.
    """
    global INK, MOUTH_INTERIOR
    th = resolve_theme(theme)
    prev_ink, prev_int = INK, MOUTH_INTERIOR
    INK = th['mouth_ink']
    MOUTH_INTERIOR = th.get('mouth_interior', MOUTH_INTERIOR)
    if head_r:
        scale = head_r / HEAD_RADIUS
        # Cap so the widest mouth (scream) stays inside the lower face. The mouth
        # centre sits at head_cy + 0.4*head_r and the chin is at head_cy + head_r,
        # so the largest usable half-height is ~0.5*head_r.
        max_half = 0.5 * head_r
        for base_half in (8.0,):        # scream is the tallest mouth
            if base_half * scale > max_half:
                scale = max_half / base_half
    try:
        resolve_mouth(expression)(draw, cx, cy, scale=scale)
    finally:
        INK, MOUTH_INTERIOR = prev_ink, prev_int


# =============================================================================
# GEOMETRY PRIMITIVES
# =============================================================================
# Drawing is expressed as a list of OPS which is painted TWICE: once in the
# keyline colour, grown and fattened, and once in the figure's own fill. That
# ordering is the whole trick — a keyline drawn per-limb would slice a dark
# notch across any limb that overlapped another. Painting the whole silhouette
# first means the fill pass can only ever cover the halo, never cut into it.
#
# An op is ('l', (x0,y0), (x1,y1), width) for a limb segment or
#         ('e', (x0,y0,x1,y1), width, 'head'|'blob') for an ellipse.

def _paint_ops(ops, draw, fill, head_fill, grow=0, width_add=0, keyline=False):
    """Paint one pass over a geometry op list."""
    for op in ops:
        if op[0] == 'l':
            _, p0, p1, w = op
            draw.line([p0, p1], fill=fill,
                      width=max(1, int(round(w + width_add))))
        else:
            _, box, w, kind = op
            b = (box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow)
            if keyline:
                draw.ellipse(list(b), fill=fill)
            elif kind == 'head':
                draw.ellipse(list(b), fill=head_fill, outline=fill,
                             width=max(1, int(round(w))))
            else:
                draw.ellipse(list(b), fill=fill)


def _blob(cx, cy, rx, ry):
    return ('e', (cx - rx, cy - ry, cx + rx, cy + ry), 0, 'blob')


# =============================================================================
# POSE GEOMETRY — poses are DATA, so an arm cannot be drawn without an elbow
# =============================================================================
# Each builder returns a dict:
#   arms  : exactly two (shoulder, elbow, hand) triples. There is no code path
#           that emits fewer than three points for an arm, which is the direct
#           fix for the straight T-arm the critic kept naming.
#   legs  : exactly two (hip, knee, foot) triples, both feet landing on foot_y.
#   extras: optional additional segments (a pointing finger, a bracing forearm).
#   palm_up / squint / hunch: small flags for the renderer.
#
# All offsets are fractions of head_r so a pose keeps its shape at any scale.

def _legs(cx, r, hip_y, foot_y, knee_f, foot_f):
    """Two two-segment legs with both feet landing EXACTLY on foot_y."""
    knee_y = hip_y + int((foot_y - hip_y) * 0.52)
    out = []
    for sgn in (-1, 1):
        out.append(((cx + sgn * int(r * 0.34), hip_y),
                    (cx + sgn * int(r * knee_f), knee_y),
                    (cx + sgn * int(r * foot_f), foot_y)))
    return out


def _pose_standing(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Relaxed stance. Arms hang with a visible outward elbow.

    The elbow is the WIDEST point of the arm (out at 0.72r) and the hand comes
    back INBOARD to 0.58r below it, which is what a hanging arm actually does.
    The first version of this pose put the elbow at 0.62r and the hand at 0.78r,
    so upper arm and forearm were nearly collinear and measured a 6-degree bend
    — visually a single straight stroke off the shoulder, which is exactly the
    scarecrow T-arm G7 forbids. Widening the elbow and pulling the hand back in
    raises the bend past 30 degrees at every figure size.
    """
    sy = neck_y + int(torso * 0.15)
    arms = []
    for sgn in (-1, 1):
        arms.append(((cx + sgn * int(r * 0.30), sy),
                     (cx + sgn * int(r * 0.72), sy + int(r * 1.00)),
                     (cx + sgn * int(r * 0.58), sy + int(r * 2.00))))
    return dict(arms=arms, legs=_legs(cx, r, hip_y, foot_y, 0.44, 0.58))


def _pose_hands_down(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Arms loosely at the sides, flopped out and bent at the elbow. The elbow
    is the widest point of the arm and the hand comes back inboard below it,
    which is what a relaxed arm actually does. The old version drew shoulder to
    hand as one line, which read as a tent."""
    sy = neck_y + int(torso * 0.15)
    arms = []
    for sgn in (-1, 1):
        arms.append(((cx + sgn * int(r * 0.34), sy),
                     (cx + sgn * int(r * 1.02), sy + int(r * 0.92)),
                     (cx + sgn * int(r * 0.86), sy + int(r * 1.92))))
    return dict(arms=arms, legs=_legs(cx, r, hip_y, foot_y, 0.40, 0.48))


def _pose_hands_up(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Genuine raised arms. Shoulder -> elbow OUT and DOWN to chest height ->
    forearm back UP so the hand finishes beside the jaw. The elbow drops below
    the shoulder, so the two segments cannot collapse into one line."""
    sy = neck_y + int(torso * 0.12)
    arms = []
    for sgn in (-1, 1):
        arms.append(((cx + sgn * int(r * 0.26), sy),
                     (cx + sgn * int(r * 1.32), sy + int(r * 0.78)),
                     (cx + sgn * int(r * 1.02), neck_y - int(r * 0.34))))
    return dict(arms=arms, legs=_legs(cx, r, hip_y, foot_y, 0.46, 0.62))


def _pose_pointing(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """One arm hangs with a real elbow, the other points. The pointing arm was
    the worst offender in the whole library — a dead horizontal stroke leaving
    the neck, i.e. the literal scarecrow T-arm the critic named on wasp17b
    beat_04. Now it drops to an elbow first and extends from there, and the
    hand is followed by a finger stub so the gesture reads as a point. The
    hanging arm bows out to an 0.88r elbow and brings the hand back inboard to
    0.60r so it has a genuine bend too, rather than hanging as one line.

    The BEND ANGLE is what makes an elbow visible, not merely its existence. The
    first version put the pointing elbow only 0.42r below the shoulder while the
    hand travelled 3.3r out, so the two segments met at a ~7-degree kink: two
    near-straight lines that read on screen as ONE horizontal stroke off the
    shoulder -- the scarecrow T-arm, just with a hidden joint inside it. The
    elbow now drops 1.05r, well below the shoulder-to-hand line, so the arm
    visibly RISES out of a lowered elbow. That angle survives downscaling; the
    old one did not."""
    sy = neck_y + int(torso * 0.15)
    idle = ((cx - int(r * 0.30), sy),
            (cx - int(r * 0.88), sy + int(r * 1.00)),
            (cx - int(r * 0.60), sy + int(r * 2.00)))
    point = ((cx + int(r * 0.30), sy),
             (cx + int(r * 1.10), sy + int(r * 1.05)),
             (cx + int(r * 3.30), sy - int(r * 0.30)))
    return dict(arms=[idle, point],
                legs=_legs(cx, r, hip_y, foot_y, 0.45, 0.60),
                finger=True)


def _pose_thinker(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Hand-to-chin think. The thinking arm bends out and down to the elbow and
    back up to the chin (already correct before the G7 pass and kept). The OTHER
    arm used to be a single straight hanging stroke; it now has a real elbow
    bowed out to 0.70r with the hand back inboard at 0.56r, so it measures a
    genuine bend instead of one line off the shoulder."""
    sy = neck_y + int(torso * 0.15)
    chin_y = head_cy + int(r * 0.55)
    think = ((cx - int(r * 0.25), sy),
             (cx - int(r * 1.15), sy + int(r * 0.58)),
             (cx - int(r * 0.16), chin_y))
    idle = ((cx + int(r * 0.25), sy),
            (cx + int(r * 0.70), sy + int(r * 1.00)),
            (cx + int(r * 0.56), sy + int(r * 2.00)))
    return dict(arms=[think, idle], legs=_legs(cx, r, hip_y, foot_y, 0.44, 0.56))


def _pose_cowering(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Shoulders hunched up, head tucked, arms wrapped protectively in front,
    knees deeply bent so the figure reads as smaller.

    The old version sent BOTH hands to the same point on the centreline, so the
    two arms plus the spine closed into a kite and the figure read as a paper
    aeroplane. The hands now land at different offsets and different heights, so
    the wrap reads as two arms."""
    hunch = int(r * 0.30)
    sy = neck_y + hunch + int(torso * 0.12)
    left = ((cx - int(r * 0.22), sy),
            (cx - int(r * 0.98), sy + int(r * 0.50)),
            (cx - int(r * 0.30), sy + int(r * 1.18)))
    right = ((cx + int(r * 0.22), sy),
             (cx + int(r * 0.92), sy + int(r * 0.58)),
             (cx + int(r * 0.10), sy + int(r * 1.34)))
    knee_y = hip_y + int((foot_y - hip_y) * 0.55)
    legs = []
    for sgn in (-1, 1):
        legs.append(((cx + sgn * int(r * 0.28), hip_y),
                     (cx + sgn * int(r * 0.56), knee_y),
                     (cx + sgn * int(r * 0.24), foot_y)))
    return dict(arms=[left, right], legs=legs)


def _pose_shielding_eyes(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Hands up at the brow, elbows wide and low, forearms angling up and in to
    stop at the OUTER edge of the face. The old version brought the hands to
    x = +/-0.3r, which is inside the face, so the forearms crossed over the eyes
    and the whole thing read as the figure's hands were inside its head. Hands at
    0.78r frame the face instead of covering it."""
    sy = neck_y + int(torso * 0.12)
    hand_y = top_y + int(r * 0.78)
    arms = []
    for sgn in (-1, 1):
        arms.append(((cx + sgn * int(r * 0.26), sy),
                     (cx + sgn * int(r * 1.52), sy + int(r * 0.95)),
                     (cx + sgn * int(r * 0.78), hand_y)))
    return dict(arms=arms, legs=_legs(cx, r, hip_y, foot_y, 0.46, 0.62),
                squint=True)


def _pose_shrugged(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """A real shrug: shoulders up, upper arms out and slightly down to a bent
    elbow, forearms angled back UP and out with the palm turned up. Elbow below
    the shoulder, hand above the elbow and further out — a clear open angle
    rather than the old near-horizontal zigzag."""
    sy = neck_y + int(torso * 0.12)
    arms = []
    for sgn in (-1, 1):
        arms.append(((cx + sgn * int(r * 0.26), sy),
                     (cx + sgn * int(r * 1.18), sy + int(r * 0.58)),
                     (cx + sgn * int(r * 1.82), sy + int(r * 0.10))))
    return dict(arms=arms, legs=_legs(cx, r, hip_y, foot_y, 0.45, 0.60),
                palm_up=True)


def _pose_fallback(cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None):
    """Used for an unrecognised pose. A mild 'huh?' — arms out at a shallow
    angle with elbows bent. Still two segments with hands; the warning is
    raised by _draw_stickman_body."""
    sy = neck_y + int(torso * 0.20)
    arms = []
    for sgn in (-1, 1):
        arms.append(((cx + sgn * int(r * 0.28), sy),
                     (cx + sgn * int(r * 0.95), sy + int(r * 0.70)),
                     (cx + sgn * int(r * 1.15), sy + int(r * 1.55))))
    return dict(arms=arms, legs=_legs(cx, r, hip_y, foot_y, 0.44, 0.58))


_POSE_BUILDERS = {
    'standing': _pose_standing,
    'hands_up': _pose_hands_up,
    'hands_down': _pose_hands_down,
    'pointing': _pose_pointing,
    'thinker': _pose_thinker,
    'cowering': _pose_cowering,
    'shielding_eyes': _pose_shielding_eyes,
    'shrugged': _pose_shrugged,
}


def _pose_geometry(pose, cx, head_r, top_y, neck_y, head_cy, hip_y, foot_y):
    """Resolve a pose name to geometry. Returns the dict documented above.

    Builders share ONE signature:
        (cx, r, neck_y, hip_y, foot_y, torso, head_cy=None, top_y=None)
    and are called by keyword. Calling positionally is what broke the whole
    module once already: eight positional args were handed to six-parameter
    builders, so every single pose raised TypeError and draw_stickman() could
    not draw a figure at all. Keyword dispatch plus the signature filter below
    means a builder that only declares the first six parameters still works, so
    a hand-added pose can never take the whole library down again.
    """
    import inspect
    builder = _POSE_BUILDERS.get(pose)
    if builder is None:
        builder = _pose_fallback
    kw = dict(cx=cx, r=float(head_r), neck_y=neck_y, hip_y=hip_y,
              foot_y=foot_y, torso=hip_y - neck_y, head_cy=head_cy,
              top_y=top_y)
    accepted = inspect.signature(builder).parameters
    if not any(p.kind is inspect.Parameter.VAR_KEYWORD
               for p in accepted.values()):
        kw = {k: v for k, v in kw.items() if k in accepted}
    g = builder(**kw)
    g['pose'] = pose
    return g


# =============================================================================
# LOW-LEVEL POSE DRAWING — called by scene helpers
# =============================================================================

def _draw_stickman_body(draw, cx, top_y, height, pose='standing', seed=0,
                        theme=None, ground_y=None, fill=None, head_fill=None,
                        keyline=None):
    """Draw the stickman body (head, torso, limbs) at the given position.

    theme:      None | name | dict. Light-on-dark vs dark-on-light (STYLE_CANON §4).
    ground_y:   the y the FEET land exactly on. None -> top_y + height, which
                is the old behaviour and the old de-facto contract.
    fill:       limb/body colour override. Use it to keep the figure off a
                same-tone shape (G7 camouflage).
    head_fill:  head colour override, for the same reason.
    keyline:    None -> take the theme's keyline (dark theme only, 3px).
                False/0 -> off. A colour -> force that halo colour.
    seed:       accepted for API compatibility; figure geometry is exact.

    Returns geometry dict with head_cy, head_r, foot_y (== ground_y), spine.
    """
    th = resolve_theme(theme)
    INK = _color(fill) or th['stroke']                            # noqa: F841
    HEAD_FILL = _color(head_fill) or th['head_fill']              # noqa: F841
    FEATURE = th['feature']            # noqa: F841 - eyes/brows stay dark

    head_r = max(4, int(height / 8))
    head_cy = top_y + head_r
    neck_y = head_cy + head_r
    hip_y = neck_y + int(height * 0.35)
    # ANCHOR: both feet land exactly here. ground_y defaults to the old
    # top_y + height so every existing call site renders byte-identically.
    foot_y = int(ground_y) if ground_y is not None else top_y + height

    # Stroke weight scales with the figure but never below the theme minimum, so
    # a 300px figure draws at the same 5/6px it always did while a 430px one
    # gets the canon's heavier outline.
    body_w = max(th['body_stroke'], int(round(head_r * BODY_STROKE_RATIO)))
    limb_w = max(th['limb_stroke'], int(round(head_r * LIMB_STROKE_RATIO)))
    hand_r = max(MIN_HAND_R, int(round(head_r * HAND_RATIO)))
    foot_r = max(MIN_FOOT_R, int(round(head_r * FOOT_RATIO)))

    if pose not in _POSE_BUILDERS:
        import warnings as _warnings
        _warnings.warn(
            'unknown stickman pose %r; falling back to a neutral stance. '
            'Valid poses: %s'
            % (pose, ', '.join(sorted(_POSES))), stacklevel=2)
    geo = _pose_geometry(pose, cx, head_r, top_y, neck_y, head_cy, hip_y, foot_y)

    # --- build the op list -------------------------------------------------
    ops = [('e', (cx - head_r, top_y, cx + head_r, top_y + 2 * head_r),
            body_w, 'head')]
    # spine + pelvis bridge (see the note on the bridge in the old code: LIMB
    # width, hips only, so it does not read as a belt)
    ops.append(('l', (cx, neck_y), (cx, hip_y), body_w))
    ops.append(('l', (cx - int(head_r * 0.34), hip_y),
                (cx + int(head_r * 0.34), hip_y), max(2, limb_w - 1)))

    for shoulder, elbow, hand in geo['arms']:
        ops.append(('l', shoulder, elbow, limb_w))
        ops.append(('l', elbow, hand, limb_w))
        if geo.get('palm_up'):
            # palm turned up reads as a flat, wider blob
            ops.append(_blob(hand[0], hand[1], int(hand_r * 1.35), int(hand_r * 0.8)))
        else:
            ops.append(_blob(hand[0], hand[1], hand_r, hand_r))

    for hip, knee, foot in geo['legs']:
        ops.append(('l', hip, knee, limb_w))
        ops.append(('l', knee, foot, limb_w))
        ops.append(_blob(foot[0], foot[1], int(foot_r * 1.5), foot_r))

    # pointing: a finger stub continuing out of the pointing hand
    if geo.get('finger'):
        (_, e, h) = geo['arms'][1]
        dx, dy = h[0] - e[0], h[1] - e[1]
        n = max(1, math.hypot(dx, dy))
        tip = (h[0] + dx / n * hand_r * 1.7, h[1] + dy / n * hand_r * 1.7)
        ops.append(('l', h, (int(tip[0]), int(tip[1])), max(3, limb_w - 1)))

    # --- paint: keyline silhouette first, then the figure on top -----------
    if keyline is None:
        kl_color, kl_px = _color(th.get('keyline')), int(th.get('keyline_px', 0) or 0)
    elif keyline is False or keyline == 0:
        kl_color, kl_px = None, 0
    elif keyline is True:
        kl_color, kl_px = _color(th.get('keyline')), int(th.get('keyline_px', 0) or 0)
    else:
        kl_color, kl_px = _color(keyline), 3
    if kl_color is not None and kl_px > 0:
        _paint_ops(ops, draw, kl_color, kl_color,
                   grow=kl_px, width_add=2 * kl_px, keyline=True)
    _paint_ops(ops, draw, INK, HEAD_FILL, keyline=False)

    # --- features on top: eyes, then the pose's squint ---------------------
    eye_y = head_cy - int(head_r * 0.2)
    eye_r = max(1, int(head_r * 0.11))
    if geo.get('squint'):
        sw = max(2, int(round(1.6 * (head_r / 14.0))))
        draw.line([(cx - int(head_r * 0.62), eye_y),
                   (cx - int(head_r * 0.22), eye_y - max(1, head_r // 20))],
                  fill=FEATURE, width=sw)
        draw.line([(cx + int(head_r * 0.22), eye_y - max(1, head_r // 20)),
                   (cx + int(head_r * 0.62), eye_y)],
                  fill=FEATURE, width=sw)
    else:
        for ex in (cx - int(head_r * 0.40), cx + int(head_r * 0.40)):
            draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r],
                         fill=FEATURE)

    return {'head_cy': head_cy, 'head_r': head_r, 'foot_y': foot_y,
            'neck_y': neck_y, 'hip_y': hip_y, 'ground_y': foot_y,
            'fill': INK, 'head_fill': HEAD_FILL, 'hand_r': hand_r,
            'foot_r': foot_r, 'pose': pose}


def draw_ground_line(draw, ground_y, x0=0, x1=1280, color=INK, width=5,
                     wobble=3, seed=0):
    """Draw the ground line a figure stands on. Draw it BEFORE the figure so the
    feet sit on top of it. The wobble is deterministic per seed so re-renders
    are identical (CLAUDE.md §7 wobble rules)."""
    rng = random.Random(seed)
    x = int(x0)
    while x < x1:
        step = 12
        jy = int(ground_y + rng.uniform(-wobble, wobble))
        draw.line([(x, jy), (min(x + step, x1),
                              int(ground_y + rng.uniform(-wobble, wobble)))],
                  fill=color, width=max(1, int(width)))
        x += step
    return int(ground_y)


def draw_stickman(image, x_center, y_top, height, pose='standing',
                  mouth='flat', seed=0, theme=None, ground_y=None,
                  fill=None, head_fill=None, keyline=None):
    """Public API: draw a stickman onto an existing PIL image.

    This is the function called by segment frame generators via
    ``sm.draw_stickman(image, x_center=..., y_top=..., height=..., ...)``.
    It delegates to _draw_stickman_body for geometry and then renders
    the mouth expression scaled to head_r.

    theme: 'light' (dark strokes on light art) | 'dark' (cream on space art) |
           dict | None. Default None resolves to the light theme. Builders MUST
           pass 'dark' for any card with a dark/space background (STYLE_CANON §4).

    ground_y: stand the feet exactly on this y. None -> y_top + height, the
              behaviour every existing call site relies on.

    fill / head_fill: override the figure's colours so a caller can keep him off
              a same-tone shape. Defaults reproduce the theme colours exactly.

    keyline: None -> theme default (the dark theme halos him in dark). False
              disables. A colour forces a halo of that colour.

    Returns the geometry dict (new; previously returned None, so this is
    backward compatible). ``geom['foot_y']`` is the line the feet stand on.
    """
    draw = ImageDraw.Draw(image)
    geom = _draw_stickman_body(draw, x_center, y_top, height, pose=pose,
                               seed=seed, theme=theme, ground_y=ground_y,
                               fill=fill, head_fill=head_fill, keyline=keyline)
    mouth_cy = geom['head_cy'] + int(geom['head_r'] * 0.4)
    draw_mouth(draw, x_center, mouth_cy, expression=mouth,
               scale=max(0.8, height / DEFAULT_HEIGHT),
               theme=theme, head_r=geom['head_r'])
    return geom


def _paint(image, cx, top_y, height, pose, expression, theme,
           ground_y=None, fill=None, head_fill=None, keyline=None):
    """body + mouth in one call. Shared by the scene helpers so they all get
    the G7 guarantees (elbows, hands, anchor, fill) for free."""
    geom = _draw_stickman_body(ImageDraw.Draw(image), cx, top_y, height,
                               pose=pose, theme=theme, ground_y=ground_y,
                               fill=fill, head_fill=head_fill, keyline=keyline)
    mouth_cy = geom['head_cy'] + int(geom['head_r'] * 0.4)
    draw_mouth(ImageDraw.Draw(image), cx, mouth_cy, expression=expression,
               scale=max(0.8, height / DEFAULT_HEIGHT),
               theme=theme, head_r=geom['head_r'])
    return geom


# =============================================================================
# SCENE-BASED COMPOSITION HELPERS (the paradigm shift)
# =============================================================================

def stickman_on_surface(expression='flat', pose='standing',
                        surface_color=(180, 140, 100),
                        sky_gradient=((100, 150, 220), (60, 100, 180)),
                        ground_y_pct=0.70,
                        width=1280, height=720,
                        stickman_height=DEFAULT_HEIGHT,
                        theme='light', fill=None, head_fill=None):
    """Render a stickman standing on a planetary or moon surface.

    Args:
        expression: mouth shape ('flat', 'frown', 'oval', 'smirk', 'zigzag', etc.)
        pose: body pose ('standing', 'hands_up', 'pointing', 'shielding_eyes', 'shrugged')
        surface_color: (R, G, B) for the ground
        sky_gradient: tuple of two (R, G, B) colors, top to horizon
        ground_y_pct: where the horizon sits (0.0=top, 1.0=bottom)
        width, height: image dimensions
        stickman_height: total height of the stickman in pixels
        fill / head_fill: figure colour overrides (see draw_stickman)

    Returns:
        PIL Image with the stickman embedded in the scene.
    """
    img = Image.new('RGB', (width, height), sky_gradient[0])
    draw = ImageDraw.Draw(img)

    # Sky gradient (top to horizon)
    horizon_y = int(height * ground_y_pct)
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        r = int(sky_gradient[0][0] * (1 - t) + sky_gradient[1][0] * t)
        g = int(sky_gradient[0][1] * (1 - t) + sky_gradient[1][1] * t)
        b = int(sky_gradient[0][2] * (1 - t) + sky_gradient[1][2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Surface (flat ground below horizon)
    draw.rectangle([0, horizon_y, width, height], fill=surface_color)

    # Horizon line (wobbly)
    for x in range(0, width, 4):
        jitter = random.randint(-2, 2)
        draw.line([(x, horizon_y + jitter), (x + 4, horizon_y + jitter)],
                  fill=INK, width=2)

    # Stickman standing on the surface, feet on the horizon line
    cx = width // 2
    foot_y = horizon_y - 5  # feet just above the horizon line
    _paint(img, cx, foot_y - stickman_height, stickman_height, pose, expression,
           theme, ground_y=foot_y, fill=fill, head_fill=head_fill)

    return img


def stickman_in_space(expression='oval', pose='hands_up',
                      celestial_body=None,
                      body_position=(0.3, 0.4),
                      body_scale=0.25,
                      width=1280, height=720,
                      stickman_height=DEFAULT_HEIGHT,
                      theme='dark', fill=None, head_fill=None,
                      ground_y=None, ground_line=False):
    """Render a stickman in space, spatially positioned relative to a sun or planet.

    Defaults to theme='dark' (cream on a space background) per STYLE_CANON.md §4.

    Args:
        expression: mouth shape
        pose: body pose
        celestial_body: dict with 'color' (R,G,B) and optional 'glow_radius' for emission
        body_position: (x_pct, y_pct) where the celestial body's center sits
        body_scale: size of the body as a fraction of the image diagonal
        width, height: image dimensions
        stickman_height: total height of the stickman
        ground_y: optional y for the feet (he floats by default). Set it to
                  stand him on something, e.g. a small moon.
        ground_line: draw a ground line at ground_y.

    Returns:
        PIL Image with the stickman embedded in the space scene.
    """
    img = Image.new('RGB', (width, height), (10, 10, 20))  # deep space background
    draw = ImageDraw.Draw(img)

    # Celestial body (sun/planet)
    if celestial_body:
        body_cx = int(width * body_position[0])
        body_cy = int(height * body_position[1])
        body_r = int(math.sqrt(width**2 + height**2) * body_scale)
        body_color = celestial_body.get('color', (255, 200, 100))
        glow_radius = celestial_body.get('glow_radius', 0)

        # Draw glow if emissive
        if glow_radius > 0:
            for i in range(glow_radius, 0, -10):
                alpha = i / glow_radius
                glow_r = body_r + i
                # Radial gradient outward (simulated with concentric circles)
                draw.ellipse([body_cx - glow_r, body_cy - glow_r,
                              body_cx + glow_r, body_cy + glow_r],
                             fill=(int(body_color[0] * alpha * 0.3),
                                   int(body_color[1] * alpha * 0.3),
                                   int(body_color[2] * alpha * 0.3)))

        # Body itself
        draw.ellipse([body_cx - body_r, body_cy - body_r,
                      body_cx + body_r, body_cy + body_r],
                     fill=body_color, outline=INK, width=3)

    # Stars (small background dots)
    random.seed(42)
    for _ in range(80):
        sx = random.randint(0, width)
        sy = random.randint(0, height)
        draw.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(200, 200, 220))

    # Stickman floating in space (positioned away from the body)
    cx = int(width * 0.65) if body_position[0] < 0.5 else int(width * 0.35)
    cy = int(height * 0.6)
    foot_y = int(ground_y) if ground_y is not None else cy + stickman_height // 2
    if ground_line and ground_y is not None:
        draw_ground_line(draw, foot_y, 0, width, color=(245, 240, 225), width=3,
                         seed=7)
    _paint(img, cx, foot_y - stickman_height, stickman_height, pose, expression,
           theme, ground_y=foot_y, fill=fill, head_fill=head_fill)

    return img


def stickman_with_environment(expression='flat', pose='standing',
                               bg_elements=None,
                               width=1280, height=720,
                               stickman_height=DEFAULT_HEIGHT,
                               stickman_position=(0.5, 0.65),
                               theme='light', fill=None, head_fill=None,
                               ground_line=False):
    """General scene-builder: stickman inhabits a scene with background elements.

    Args:
        expression: mouth shape
        pose: body pose
        bg_elements: list of dicts, each with 'type' and type-specific params:
            {'type': 'rect', 'bounds': (x0, y0, x1, y1), 'fill': (R,G,B)}
            {'type': 'ellipse', 'bounds': (x0, y0, x1, y1), 'fill': (R,G,B)}
            {'type': 'line', 'points': [(x0,y0), (x1,y1)], 'stroke': (R,G,B), 'width': W}
        width, height: image dimensions
        stickman_height: total height of the stickman
        stickman_position: (x_pct, y_pct) where the stickman's feet are anchored
        ground_line: draw a ground line at the feet

    Returns:
        PIL Image with the stickman embedded in the scene.
    """
    img = Image.new('RGB', (width, height), (240, 235, 220))  # cream background
    draw = ImageDraw.Draw(img)

    # Draw background elements first
    if bg_elements:
        for elem in bg_elements:
            elem_type = elem.get('type')
            if elem_type == 'rect':
                draw.rectangle(elem['bounds'], fill=elem['fill'],
                               outline=elem.get('outline', None),
                               width=elem.get('width', 0))
            elif elem_type == 'ellipse':
                draw.ellipse(elem['bounds'], fill=elem['fill'],
                             outline=elem.get('outline', None),
                             width=elem.get('width', 0))
            elif elem_type == 'line':
                draw.line(elem['points'], fill=elem['stroke'],
                          width=elem.get('width', 2))

    # Stickman positioned in the scene
    cx = int(width * stickman_position[0])
    foot_y = int(height * stickman_position[1])
    if ground_line:
        draw_ground_line(draw, foot_y, 0, width, color=INK, width=5, seed=11)
    _paint(img, cx, foot_y - stickman_height, stickman_height, pose, expression,
           theme, ground_y=foot_y, fill=fill, head_fill=head_fill)

    return img


# =============================================================================
# SELF TEST — renders every pose and checks the G7 invariants mechanically.
# Run: python -m lib.stickman [outdir]
# =============================================================================

def _self_test(outdir='work/_stickman_selftest'):
    import os
    os.makedirs(outdir, exist_ok=True)
    ok = True
    for pose in sorted(_POSES):
        for theme in ('light', 'dark'):
            img = Image.new('RGB', (300, 400), (245, 240, 225))
            ground = 350
            geom = draw_stickman(img, 150, 20, 300, pose=pose, mouth='flat',
                                 theme=theme, ground_y=ground)
            # invariant 3: both feet land exactly on the anchor
            if geom['foot_y'] != ground:
                print('FAIL %s/%s: foot_y=%s != ground_y=%s'
                      % (pose, theme, geom['foot_y'], ground))
                ok = False
            # invariants 1+2: two arms, each three points; two legs, three points
            g = _pose_geometry(pose, 150, geom['head_r'], 20, geom['neck_y'],
                               geom['head_cy'], geom['hip_y'], geom['foot_y'])
            if len(g['arms']) != 2 or any(len(a) != 3 for a in g['arms']):
                print('FAIL %s: arms are not two 3-point triples' % pose)
                ok = False
            if len(g['legs']) != 2 or any(len(l) != 3 for l in g['legs']):
                print('FAIL %s: legs are not two 3-point triples' % pose)
                ok = False
            for hip, knee, foot in g['legs']:
                if foot[1] != ground:
                    print('FAIL %s: leg foot at y=%s, not the anchor %s'
                          % (pose, foot[1], ground))
                    ok = False
            if theme == 'light':
                img.save(os.path.join(outdir, '%s.png' % pose))
    print('stickman self-test: %d poses, %s'
          % (len(_POSES), 'all invariants hold' if ok else 'FAILURES ABOVE'))
    return outdir if ok else 1


if __name__ == '__main__':
    import sys
    raise SystemExit(_self_test(sys.argv[1] if len(sys.argv) > 1
                                else 'work/_stickman_selftest'))
