# work/lib/motion.py — the quantized 0.25 s "stamp" motion layer.
#
# THE IDEA (STYLE_CANON.md §5, quantized motion): the reference's painterly
# aesthetic extends to TIME. Motion is not a smooth tween — it is sampled at a
# fixed 4 Hz, and each sample is a small deterministic variation of the still
# frame, like a painter flipping through a few drawings. So a card that lasts
# 2.26 s shows ~9 discrete poses, not a continuous drift.
#
# Every card in the schedule carries a free-text `motion` field, e.g.
#   "star_pulse_0.5Hz"  "spin_step_0.25s (4 stamps/rev)"  "collapse_in_1.2s + flash"
#   "on_off_strobe_1.1s"  "beam_sweep_3.0s"  "name_stamp_x3"  "none (static — ...)"
# This module parses that string into a small verb list and dispatches each verb
# to a generic (or special-cased) transform. The transform signature is:
#     f(img, card, stamp_index, n_stamps) -> new_img
# `stamp_index` is int(elapsed_in_card / 0.25), quantized; `n_stamps` is how many
# stamps the card has in total, so a verb can do "the first stamp is special".
#
# ---------------------------------------------------------------------------
# THE ONE HARD RULE IN THIS FILE
#
# This layer transforms an ALREADY-RASTERIZED frame, and that frame carries the
# layout: the paper title strip in rows 0..83, the floating caption near row 652,
# and the diagram annotations. Round 2 shipped two catastrophic bugs from
# ignoring that, and both were invisible in code review and obvious on screen:
#
#   - `_t_flip` mirrored the whole raster for 'digit_flip', so name_just_digits
#     went out with EVERY glyph backwards -- header, caption and all.
#   - `_t_head_tilt` rotated the whole raster for 'head_tilt_0.25s', so
#     hook_not_alone went out with a visibly CROOKED title strip and black
#     wedges in two corners.
#
# So: motion may vary LIGHT (brightness, colour, glow) over the entire frame,
# but it may only move GEOMETRY inside the safe art band -- rows 84..615 -- and
# even then only HORIZONTALLY, because a vertical shift would tear against the
# band's fixed edges. Everything a viewer reads as "the layout" is untouchable.
#
# Determinism: the same (card, stamp_index) always yields the same frame. No
# global random state; every stochastic touch takes a seed derived from the card id.

import math
import re

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

import lib.type as T

STAMP_DT = 0.25

# The safe horizontal-motion band: below the title strip, above the caption.
BAND_TOP = T.ART_TOP        # 84  — first art row
BAND_BOT = 612              # last row motion may touch (caption glyphs start ~632)


# ---------------------------------------------------------------------------
# Band helpers — how a transform is allowed to move geometry.
# ---------------------------------------------------------------------------

def _band_shift_x(img, dx):
    """Roll rows BAND_TOP..BAND_BOT horizontally by dx px, edge-clamped.

    Only the safe band moves. The title strip (rows 0..83) and everything from
    row 612 down -- the caption and its margin -- are pasted back untouched, so
    no transform in this file can ever tilt the strip or shear the caption."""
    if not dx:
        return img
    w = img.width
    dx = int(dx) % w
    if not dx:
        return img
    out = img.copy()
    top, bot = BAND_TOP, BAND_BOT
    band = img.crop((0, top, w, bot))
    rolled = Image.new('RGB', band.size)
    rolled.paste(band.crop((dx, 0, w, band.height)), (0, 0))
    # fill the vacated strip on the right by wrapping from the left, so a roll
    # never opens a black seam at the frame edge
    rolled.paste(band.crop((0, 0, dx, band.height)), (w - dx, 0))
    out.paste(rolled, (0, top))
    return out


def _light(img, scale=1.0):
    """The only whole-frame operation a transform may perform."""
    return ImageEnhance.Brightness(img).enhance(scale)


# ---------------------------------------------------------------------------
# Primitive transforms. Each returns a NEW image (or the same one if no-op).
# ---------------------------------------------------------------------------

def _t_none(img, card, k, n):
    return img


def _t_pulse(img, card, k, n, amount=0.06, period=8):
    """Breathe the whole frame slightly brighter/darker — a star 'beating'.
    Cheap, generic, and reads as life without moving anything."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + amount * math.sin(math.tau * ph))


def _t_arc_pulse(img, card, k, n, period=6):
    """Slightly stronger brightness pulse, for 'arc_pulse' (a spinning dead star)."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + 0.09 * math.sin(math.tau * ph))


def _t_head_tilt(img, card, k, n, period=6):
    """'head_tilt_0.25s': a quantized brightness settle, NOT a rotation.

    Rotating the raster tilts the title strip, shears the header and exposes
    black corners — round 2 shipped exactly that on hook_not_alone. The head
    tilt has to be drawn INTO the still by the card renderer, which knows where
    the head is; this layer can only suggest it with light."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + 0.05 * math.sin(math.tau * ph))


def _t_spin_step(img, card, k, n, stamps_per_rev=4):
    """A 0.25 s 'tick' of a spin: a small horizontal roll of the art band plus a
    brightness blip, so a fast spin reads as discrete strobed steps."""
    ph = (k % stamps_per_rev) / max(1, stamps_per_rev)
    img = _band_shift_x(img, int(round(5 * math.sin(math.tau * ph))))
    return _light(img, 1.0 + 0.05 * math.sin(math.tau * ph))


def _t_counter_roll(img, card, k, n, period=5):
    """'counter_roll': a slow horizontal creep, like a dial turning."""
    ph = (k % period) / max(1, period)
    return _band_shift_x(img, int(round(6 * math.sin(math.tau * ph))))


def _t_strobe(img, card, k, n, on_pattern=(0, 1, 1, 0, 1)):
    """On/off strobe (the lighthouse). Flips between full and dimmed on a fixed
    pattern so it reads as a blinking beacon, not a smooth pulse."""
    return _light(img, 1.10 if on_pattern[k % len(on_pattern)] else 0.72)


def _t_flash(img, card, k, n, flash_stamp=0):
    """A single bright flash on one stamp (an explosion)."""
    return _light(img, 1.35) if k == flash_stamp else img


def _t_collapse(img, card, k, n):
    """'collapse_in_1.2s': the frame tightens and brightens over ~5 stamps, then
    holds. The ramp saturates at 5 stamps so a long collapse does not drift up
    for the whole card."""
    ramp = min(1.0, (k + 1) / max(1, min(n, 5)))
    img = _band_shift_x(img, int(round(3 * ramp)))
    return _light(img, 1.0 + 0.30 * ramp)


def _t_sweep(img, card, k, n):
    """'beam_sweep_3.0s': a soft vertical band of light walking across the ART.

    A travelling glow, not a travelling frame. The band is masked to rows
    BAND_TOP..BAND_BOT so the title strip and caption are never washed out, and
    the halo is multiplied by its own mask so its corners reach exactly zero
    (same near-black-sky trap as cardframe.add_glow)."""
    ph = (k % 8) / 8.0
    cx = int(img.width * ph)
    bh = BAND_BOT - BAND_TOP
    glow = Image.new('L', (img.width, bh), 0)
    ImageDraw.Draw(glow).rectangle([cx - 70, 0, cx + 70, bh], fill=34)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    out = img.copy()
    band = img.crop((0, BAND_TOP, img.width, BAND_BOT)).convert('RGB')
    halo = Image.merge('RGB', (glow, glow, glow))
    out.paste(ImageChops.add(band, halo), (0, BAND_TOP))
    return out


def _t_drift(img, card, k, n, dx=5):
    """'mist_drift': a slow horizontal creep of the art band."""
    return _band_shift_x(img, (k * dx) % 14 - 7)


def _t_swell(img, card, k, n, period=10):
    """'haze_swell': a long brightness breath."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + 0.07 * math.sin(math.tau * ph - math.pi / 2))


def _t_veil(img, card, k, n, period=8):
    """'veil_stripes': the radiation veil shimmers inside the safe band only."""
    out = img.copy()
    d = ImageDraw.Draw(out, 'RGBA')
    y = BAND_TOP + (k * 12) % max(1, (BAND_BOT - BAND_TOP - 6))
    d.rectangle([0, y, img.width, y + 3], fill=(255, 255, 255, 20))
    return out


def _t_shake(img, card, k, n, amp=3):
    """'debris_jitter': a tremor. Deterministic per (card, stamp) — no global
    random state, so a re-render is byte-identical."""
    # A stable integer hash; Python's builtin hash() is salted per process, so
    # it CANNOT be used here or renders would not reproduce across runs.
    seed = (abs(hash_str(card.get('id', ''))) + k * 2654435761) & 0xffff
    dx = ((seed % (2 * amp + 1)) - amp)
    return _band_shift_x(img, dx)


def hash_str(s):
    """FNV-1a — a stable, process-independent string hash."""
    h = 0x811c9dc5
    for ch in str(s):
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xffffffff
    return h


def _t_grow(img, card, k, n, period=6):
    """'mass_bar_grow': something thickens — a slow horizontal stretch."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + 0.06 * math.sin(math.tau * ph))


def _t_accumulate(img, card, k, n):
    """'debris_accumulate': a ramp that saturates partway through the card."""
    ramp = min(1.0, (k + 1) / max(1, n * 0.7))
    return _light(img, 1.0 + 0.22 * ramp)


def _t_settle(img, card, k, n, period=5):
    """'name_stamp_settle' / 'stamp_settle': a quick bright blip, then rest."""
    return _light(img, 1.08) if k % period == 0 else img


def _t_repeat(img, card, k, n, period=4):
    """'pulse_repeat': a double-blip rhythm."""
    return _light(img, 1.09) if (k % period) in (0, 2) else img


def _t_squash(img, card, k, n, period=6):
    """'waveform_squash': the wobble. Not a vertical squash — that would tear
    against the fixed band edges and shear the caption. A horizontal shear of the
    art band reads the same and is safe."""
    ph = (k % period) / max(1, period)
    return _band_shift_x(img, int(round(3 * math.sin(math.tau * ph))))


def _t_flip(img, card, k, n, period=6):
    """'digit_flip': an odometer rolling sideways.

    NOT a mirror. Mirroring the raster reverses every glyph on the frame — the
    header, the annotations AND the caption — and round 2 shipped name_just_digits
    entirely backwards. Motion may never reverse the reading direction of type.
    Rolling the art band sideways reads as a mechanical counter without touching
    a single letter."""
    return _band_shift_x(img, 14) if k % period == 0 else img


def _t_metronome(img, card, k, n, period=4):
    """'metronome_step': left-right jiggle, like a swinging weight."""
    ph = (k % period) / max(1, period)
    return _band_shift_x(img, int(round(6 * math.sin(math.tau * ph))))


def _t_ring_step(img, card, k, n, period=5):
    """'orbit_ring_step': rings tick outward — a small brightness pulse."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + 0.05 * math.sin(math.tau * ph))


def _t_arms_up(img, card, k, n, period=6):
    """'arms_up_stamp': a brightness lift on the character's beat."""
    return _light(img, 1.07) if (k % period) < 2 else img


def _t_extinguish(img, card, k, n):
    """'flame_extinguish': the light going out — a ramp DOWN."""
    ramp = min(1.0, (k + 1) / max(1, n))
    return _light(img, 1.0 - 0.40 * ramp)


def _t_grid(img, card, k, n, period=6):
    """'sky_grid': the chart shimmers faintly."""
    ph = (k % period) / max(1, period)
    return _light(img, 1.0 + 0.03 * math.sin(math.tau * ph))


def _t_crosshair(img, card, k, n, period=6):
    """'crosshair_drop': a survey reticle stepping down the ART band.

    Drawn thin (2px) and clipped to the safe band — it is an instrument overlay,
    not a Register-P object, and it must not cross the title strip or the
    caption."""
    out = img.copy()
    d = ImageDraw.Draw(out, 'RGBA')
    span = max(1, (BAND_BOT - BAND_TOP - 80))
    cx = 640
    cy = BAND_TOP + 40 + ((k * 26) % span)
    col = (255, 255, 255, 120)
    d.line([(cx - 34, cy), (cx - 8, cy)], fill=col, width=2)
    d.line([(cx + 8, cy), (cx + 34, cy)], fill=col, width=2)
    d.line([(cx, cy - 34), (cx, cy - 8)], fill=col, width=2)
    d.line([(cx, cy + 8), (cx, cy + 34)], fill=col, width=2)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=col, width=2)
    return out


def _t_tug(img, card, k, n, period=6):
    """'tug_step': something small pulling on the beam — a short horizontal pull."""
    ph = (k % period) / max(1, period)
    return _band_shift_x(img, int(round(5 * math.sin(math.tau * ph))))


def _t_tally(img, card, k, n):
    """'tally_2yr': a slow bloom over the two-year wait."""
    ramp = min(1.0, (k + 1) / max(1, n))
    return _light(img, 1.0 + 0.12 * ramp)


def _t_point(img, card, k, n, period=5):
    """'point_pulse': a blink."""
    return _light(img, 1.06) if k % period == 0 else img


# ---------------------------------------------------------------------------
# Verb table: token in the motion string -> transform.
# The regex below requires a word-ish boundary, so 'step' never matches inside
# 'metronome_step'.
# ---------------------------------------------------------------------------

_VERBS = [
    ('collapse_in', _t_collapse),
    ('star_pulse', _t_pulse),
    ('arc_pulse', _t_arc_pulse),
    ('core_breathe', _t_pulse),
    ('crosshair_drop', _t_crosshair),
    ('head_tilt', _t_head_tilt),
    ('spin_step', _t_spin_step),
    ('counter_roll', _t_counter_roll),
    ('on_off_strobe', _t_strobe),
    ('beam_sweep', _t_sweep),
    ('flash', _t_flash),
    ('mist_drift', _t_drift),
    ('haze_swell', _t_swell),
    ('veil_stripes', _t_veil),
    ('debris_jitter', _t_shake),
    ('debris_accumulate', _t_accumulate),
    ('mass_bar_grow', _t_grow),
    ('orbit_ring_step', _t_ring_step),
    ('ring_step', _t_ring_step),
    ('waveform_squash', _t_squash),
    ('digit_flip', _t_flip),
    ('name_stamp', _t_settle),
    ('stamp_settle', _t_settle),
    ('pulse_repeat', _t_repeat),
    ('metronome_step', _t_metronome),
    ('tug_step', _t_tug),
    ('tally_2yr', _t_tally),
    ('flame_extinguish', _t_extinguish),
    ('sky_grid', _t_grid),
    ('arms_up_stamp', _t_arms_up),
    ('point_pulse', _t_point),
    ('jitter', _t_shake),
    ('step', _t_ring_step),
    ('pulse', _t_pulse),
    ('drift', _t_drift),
    ('breathe', _t_pulse),
    ('sweep', _t_sweep),
    ('grow', _t_grow),
    ('extinguish', _t_extinguish),
    ('arms_up', _t_arms_up),
    ('tally', _t_tally),
    ('grid', _t_grid),
]


def _verbs_for(motion_str):
    """Parse a motion string into an ordered list of (verb, fn), de-duplicated."""
    s = (motion_str or '').lower()
    found = []
    for verb, fn in _VERBS:
        pat = re.compile(r'(?<![a-z_])' + re.escape(verb) + r'(?![a-z])')
        if pat.search(s):
            found.append((verb, fn))
    # Subsumption: if one matched verb's name is a contiguous substring of
    # another's, keep only the longer. 'pulse_repeat' contains 'pulse' and
    # 'tally_2yr' contains 'tally', and each would otherwise apply twice,
    # compounding the brightness on one card.
    filtered = []
    for verb, fn in found:
        subsumed = any(verb != verb2 and verb in verb2 for verb2, _ in found)
        if not subsumed and verb not in [v for v, _ in filtered]:
            filtered.append((verb, fn))
    return filtered


def _pin_layout(original, moved):
    """Restore the two layout bands from the unmoved still.

    This is the single enforcement point for the hard rule above, and it exists
    because leaving it to each verb did not work. Brightness over the whole
    frame is ALSO wrong on the protected bands: a 0.5 Hz pulse drags the cream
    title strip from (242,234,214) toward white and back, so the band visibly
    flickers, and the strobe's 0.72 dim makes the amber caption unreadable. A
    viewer's anchor cannot breathe.

    So: motion runs on the whole raster for speed and simplicity, then the
    strip and the caption band are spliced back from the original, byte for
    byte. The result is a frame whose ART is alive and whose LAYOUT is welded.
    """
    if moved is original:
        return moved
    out = moved.copy()
    out.paste(original.crop((0, 0, original.width, T.ART_TOP)), (0, 0))
    out.paste(original.crop((0, BAND_BOT, original.width, original.height)),
              (0, BAND_BOT))
    return out


def apply_motion(img, card, stamp_index, n_stamps):
    """Apply the card's motion for one 0.25 s stamp. Returns a new image.

    Unknown / 'none' / static motion -> the still unchanged.
    """
    verbs = _verbs_for(card.get('motion'))
    if not verbs:
        return img
    out = img
    for _verb, fn in verbs:
        try:
            out = fn(out, card, stamp_index, n_stamps)
        except Exception:
            # A motion verb must NEVER take down a frame render. Fall back to
            # the previous image and keep going.
            pass
    return _pin_layout(img, out)