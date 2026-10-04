#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
work/lib/composition.py
=======================

Executable geometry for the G1 fix: make the subject FILL the frame and sit in
the lower two-thirds, instead of floating as a small element in the upper third.

This module is pure geometry and checking. It renders nothing. It is INDEPENDENT
of the pixel gate in ``work/segments/_gate.py``: it does not import it, and it
adds a check that gate does not have -- the size and placement of the PRIMARY
SUBJECT, which is a design-time property (a declared or measured bounding box),
not a whole-frame pixel statistic.

WHY A NEW CHECK (the G1 diagnosis)
----------------------------------
Measured with ``work/lib/measure_frames.py`` over the 11 blinded frame pairs and
over the new segments' cardsheets:

    metric                ours (tres2b)  ours (wasp17b)  reference
    ink_fraction            0.235          0.195         0.406
    v_centroid              0.485          0.370         0.586

``v_centroid`` is the strongest single discriminator in the whole report
(Cohen's d = -2.80, 117/121 cross-pairs): our frames put their visual mass in the
UPPER third, the reference puts it in the LOWER two-thirds. This module turns
"put the mass in the lower two-thirds" into an executable check a builder can run
before shipping a card.

The numbers here are ADOPTED FROM ``_gate.py`` by agreement, not by import, so the
project has ONE set of thresholds rather than two that disagree:
    INK_FRACTION_FLOOR = 0.30   (== _gate.INK_MIN["PAINT"])
    V_CENTROID_RANGE  = (0.42, 0.75)  (== _gate.V_CENTROID_RANGE)

SUBJECT_SCALE is new, and is grounded in a fresh measurement on the same blinded
pairs: the largest ink mass on the reference spans the FULL frame width
(median width fraction 1.00) with height fraction 0.665-0.719 centred at
y = 0.615-0.640. On ours the same measurement gives width 0.20 and height
0.35-0.43 -- the subject is a small element, and the dominant connected
component is a thin full-width TITLE STRIP near the top, not a body. So:

    SUBJECT_SCALE = 0.35   -- a primary subject must span >= 35% of frame width.

0.35 sits far above our current 0.20 (so the real failure is caught) and far below
the reference's ~1.0 (so a legitimately narrower subject -- a tall rocket, a
thermometer, a slim figure -- still passes). It is a floor on the SUBJECT, not a
demand that every card be edge-to-edge.

WHAT THIS MODULE WILL NOT DO
----------------------------
It does not chase ``dark_mask_fraction``. That metric is REGISTER-CONFOUNDED: a
space card with a near-black background scores ~0.5 from its BACKGROUND alone
while its linework is exactly as thin as a cream card's. Do not verify outline
weight here; the 6 px outline rule is STYLE_CANON and is verified by eye at full
resolution. ``muted_fraction`` is likewise bimodal by design and is not used.

THE CONSTANTS, AND WHAT THEY MEAN ON A 1280x720 CARD
----------------------------------------------------
    CARD_W, CARD_H        = 1280, 720     the frame every card is rendered at
    SUBJECT_SCALE         = 0.35          subject must span >= 448 px of width
    FIGURE_HEIGHT         = 0.55          standing figure spans >= 396 px height
    GROUND_Y_FRAC         = 0.86          feet / ground line at y = 619
    GROUND_Y              = 619           (== GROUND_Y_FRAC * CARD_H)
    INK_FRACTION_FLOOR    = 0.30          whole-frame non-background coverage
    V_CENTROID_RANGE      = (0.42, 0.75)  accepted window for mass centre
    SUBJECT_V_MIN         = 0.42          subject centre must be at/below this

GROUND_Y = 619 is in the BOTTOM QUARTER of the frame (bottom quarter starts at
720 * 0.75 = 540). It is corroborated by the reference's detected horizon rows in
``measure_frames_report.md`` section 1d, which cluster at row_frac 0.740 / 0.831 /
0.860 -- i.e. the reference draws its ground line in that same low band.

subject_box(w, h) returns the region a primary subject should occupy, so a
renderer never has to guess:

    frame 1280x720, kind="figure", min_w = 0.35*w, feet on GROUND_Y:
        min subject width  = 0.35 * 1280 = 448 px   (x from 416 to 864 if centred)
        figure height floor= 0.55 * 1280... = 0.55*720 = 396 px
        ground line (feet) = y 619       (top of head ~ y 223)
        subject centre y    ~ 0.42       ... i.e. low, in the lower two-thirds

WORKED EXAMPLE -- a PASSING and a FAILING layout
-------------------------------------------------
Both are the same 1280x720 frame and the same subject, differing only in scale
and placement. Call::

    check_composition((x0, y0, x1, y1), w=1280, h=720, kind="body")

PASSING -- a planet that fills the frame, sitting low (this is the reference's
composition):
    bbox = (307, 176, 973, 842->clipped to (307,176,973,719))
    subject_w_frac = (973-307)/1280 = 0.52   >= 0.35  -> scale_ok  = True
    subject_v      = ((176+719)/2)/720 = 0.62  in [0.42,0.75] -> v_ok = True
    result["pass"] = True    ink_fraction ~0.44 (informational, floor 0.30)

FAILING -- the same planet shrunk into the upper third (this is our wasp17b /
tres2b failure):
    bbox = (512, 96, 768, 336)          # a 256 px disc floating high
    subject_w_frac = (768-512)/1280 = 0.20  <  0.35  -> scale_ok = False
    subject_v      = ((96+336)/2)/720 = 0.30   <  0.42  -> v_ok     = False
    result["pass"] = False   two failures: SUBJECT_SCALE, SUBJECT_V

The fix for the failing case is exactly the G1 instruction: scale the subject up
until it spans >= 0.35 of frame width, and move its centre down into the lower
two-thirds -- for a standing figure, put the feet on GROUND_Y (619).

USAGE
-----
    from composition import subject_box, check_composition, fill_frame_guidance
    box = subject_box(1280, 720)              # geometry a renderer should honour
    rpt = check_composition((x0, y0, x1, y1))  # declare the box you drew
    rpt = check_composition("cardsheet/beat_06.png")   # or measure a rendered PNG

    print(fill_frame_guidance())               # paste into a builder prompt
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Frame + geometry constants (all for a 1280x720 card)
# ---------------------------------------------------------------------------

CARD_W = 1280
CARD_H = 720

# Minimum fraction of frame WIDTH the primary subject must span.
# Grounded on blinded-pair measurement: reference body width ~1.00, ours ~0.20.
SUBJECT_SCALE = 0.35

# Minimum fraction of frame HEIGHT a standing FIGURE must span (head to feet).
# Grounded on blinded-pair measurement: reference body height 0.665-0.719.
FIGURE_HEIGHT = 0.55

# The ground line: where a standing figure's FEET belong, in the bottom quarter.
GROUND_Y_FRAC = 0.86                 # 0.86 * 720 = 619
GROUND_Y = int(round(GROUND_Y_FRAC * CARD_H))   # 619, bottom quarter starts at 540

# Whole-frame non-background coverage floor (adopted from _gate.INK_MIN["PAINT"]).
INK_FRACTION_FLOOR = 0.30

# Accepted window for the vertical centre of visual mass (adopted from
# _gate.V_CENTROID_RANGE). 0.5 = frame centre, 1.0 = bottom edge.
V_CENTROID_RANGE = (0.42, 0.75)

# A subject's own centre must sit at/below this, i.e. in the lower two-thirds.
SUBJECT_V_MIN = 0.42

# A full-width, short component is a TITLE STRIP / CAPTION BAND, not a body.
# When measuring a rendered frame we ignore such bands when picking the subject.
BAND_MAX_H_FRAC = 0.45               # shorter than this AND full width => a band
BAND_FULL_W_FRAC = 0.90              # at least this wide => counts as full width
SUBJECT_MIN_AREA_FRAC = 0.01         # ignore specks smaller than 1% of frame


# ---------------------------------------------------------------------------
# 2. subject_box(w, h) -> the region the primary subject should occupy
# ---------------------------------------------------------------------------

def subject_box(w: int = CARD_W, h: int = CARD_H, kind: str = "figure"):
    """
    Return the region a card's primary subject should occupy, as a plain dict.

    For the default 1280x720 card (kind="figure"), the numbers are::

        min_w        = 0.35 * 1280 = 448    # subject must span >= 448 px wide
        min_h        = 0.55 * 720  = 396    # a standing figure spans >= 396 px tall
        ground_y     = 619                  # feet land here (bottom quarter)
        centre_x     = 640
        x0, x1       = 416, 864             # a centred box of exactly min_w
        y0           = 223                  # ground_y - min_h (top of head)
        y1           = 619                  # the ground line itself

    The returned "bbox" is the MINIMUM ENVELOPE: a body (planet, star, diagram)
    should fill it or exceed it; a slim subject may be narrower than min_w as
    long as it is placed with its mass low and, for a figure, its feet on
    ground_y.

    kind="body"  -> min_h = 0 (only the width floor and the ground/centre matter).
    kind="figure"-> min_h = FIGURE_HEIGHT * h (head-to-feet floor as well).
    """
    min_w = int(round(SUBJECT_SCALE * w))
    min_h = int(round(FIGURE_HEIGHT * h)) if kind == "figure" else 0
    ground_y = int(round(GROUND_Y_FRAC * h))
    cx = w // 2

    x0 = cx - min_w // 2
    x1 = cx + min_w // 2
    y1 = ground_y
    y0 = ground_y - min_h if min_h else int(round(h * 0.20))   # default top for a body

    return {
        "frame": (w, h),
        "kind": kind,
        "min_w": min_w,
        "min_h": min_h,
        "ground_y": ground_y,
        "centre_x": cx,
        # minimum envelope a figure should fill (x0, y0, x1, y1), feet on ground_y
        "bbox": [int(x0), int(y0), int(x1), int(y1)],
        # where the subject's centre should land, as a fraction of frame height
        "subject_v": round(((y0 + y1) / 2.0) / h, 4),
        "note": "subject spans >= min_w of frame width; standing figure's feet on ground_y",
    }


# ---------------------------------------------------------------------------
# 3. check_composition(img_or_bbox, ...) -> dict  (the G1 executable check)
# ---------------------------------------------------------------------------

def _measure_subject_from_image(arr, w, h):
    """
    Given an HxWx3 RGB numpy array, return (ink_fraction, v_centroid, subject_bbox).

    The binarisation is NOT reimplemented: background is the single most dominant
    colour and ink is anything more than L1 distance 30 from it, which is exactly
    what measure_frames.layout_metrics does. The components come from
    measure_frames.connected_components / component_stats, which are the verified
    run-based union-find implementation. Using them keeps ONE measurement
    definition in this project -- if composition.py invented a second
    binarisation it would silently disagree with the numbers in the report.

    The "subject" is the largest-area ink component that is NOT a full-width
    short band. The band exclusion is essential and is not cosmetic: on these
    cards the single largest component is normally the title strip or the
    caption band, which spans the full width and sits at the top. Without the
    exclusion every frame measures as a full-width subject and this check
    becomes a rubber stamp -- measured on the blinded pairs, the exclusion is
    what makes the number discriminate (ours 0.20 vs reference 1.00).

    Returns subject_bbox as [x0, y0, x1, y1], or None if no body qualifies.
    """
    import os
    import sys

    import numpy as np

    _lib = os.path.dirname(os.path.abspath(__file__))
    if _lib not in sys.path:
        sys.path.insert(0, _lib)
    import measure_frames as MF  # path must be set first

    bg = np.array(MF.dominant_colors(arr)["palette"][0]["rgb"], dtype=np.int64)
    dist = np.abs(arr.astype(np.int64) - bg).sum(axis=2)
    ink = dist > 30

    total = float(ink.sum())
    if total == 0:
        return 0.0, 0.5, None

    ys = np.nonzero(ink)[0]
    ink_fraction = total / (w * h)
    v_centroid = float(ys.mean()) / h        # same definition as measure_frames

    labels, n_labels = MF.connected_components(ink)
    ccs = MF.component_stats(labels, n_labels)
    min_area = SUBJECT_MIN_AREA_FRAC * w * h

    bodies = [
        c for c in ccs
        if c["area"] >= min_area
        and not (c["w"] / w >= BAND_FULL_W_FRAC and c["h"] / h < BAND_MAX_H_FRAC)
    ]
    if not bodies:
        return ink_fraction, v_centroid, None

    best = max(bodies, key=lambda c: c["area"])
    return ink_fraction, v_centroid, [int(v) for v in best["bbox"]]


def _coerce_frame_size(obj):
    """Return (w, h) for an image-like object, or None if not image-like."""
    if hasattr(obj, "size") and not isinstance(obj, (tuple, list)):
        w, h = obj.size[:2]
        return int(w), int(h)
    return None


def _coerce_bbox(obj):
    """Return [x0, y0, x1, y1] if obj looks like a bbox, else None."""
    if isinstance(obj, (tuple, list)) and len(obj) == 4:
        try:
            x0, y0, x1, y1 = (int(v) for v in obj)
        except (TypeError, ValueError):
            return None
        if x1 >= x0 and y1 >= y0:
            return [x0, y0, x1, y1]
    return None


def _load_rgb(obj):
    """Coerce a path / PIL Image / numpy array to an HxWx3 uint8 numpy array."""
    import numpy as np
    from PIL import Image

    if isinstance(obj, np.ndarray):
        arr = obj
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        return arr[..., :3].astype(np.uint8)
    if isinstance(obj, Image.Image):
        return np.asarray(obj.convert("RGB"))
    if isinstance(obj, (str, bytes)) or hasattr(obj, "__fspath__"):
        return np.asarray(Image.open(obj).convert("RGB"))
    raise TypeError("unsupported image input: %r" % (type(obj),))


def check_composition(img_or_bbox, *, w: int = CARD_W, h: int = CARD_H,
                      kind: str = "body", include_ink: bool = True):
    """
    Return a dict reporting whether the primary subject meets the SCALE FLOOR and
    whether its vertical centre of mass sits in the LOWER TWO-THIRDS. This is the
    G1 fix as an executable check, independent of the pixel gate in _gate.py.

    img_or_bbox may be:
      * a bbox tuple (x0, y0, x1, y1) in pixels -- declare the box you drew;
      * a PIL Image, a numpy RGB array, or a path to a PNG -- measure the frame.

    Parameters
    ----------
    kind : "body"   -> enforce the WIDTH floor (SUBJECT_SCALE). Default.
            "figure" -> enforce the HEIGHT floor (FIGURE_HEIGHT) instead, which is
            the right rule for a standing character (a stickman is legitimately
            narrower than 35% of the frame).

    Returns a dict with at least:
        pass        bool  -- scale_ok AND v_ok
        scale_ok    bool  -- subject meets the size floor for `kind`
        v_ok        bool  -- subject centre y is in the lower two-thirds
        subject_w_frac, subject_h_frac, subject_v, subject_bbox
        ink_fraction, ink_ok  (image inputs only; informational, NOT part of pass)
        failures    list[str]  -- e.g. ["SUBJECT_SCALE", "SUBJECT_V"]
    """
    report = {
        "source": None,
        "frame": (w, h),
        "kind": kind,
        "thresholds": {
            "SUBJECT_SCALE": SUBJECT_SCALE,
            "FIGURE_HEIGHT": FIGURE_HEIGHT,
            "SUBJECT_V_MIN": SUBJECT_V_MIN,
            "INK_FRACTION_FLOOR": INK_FRACTION_FLOOR,
            "V_CENTROID_RANGE": list(V_CENTROID_RANGE),
            "GROUND_Y": int(round(GROUND_Y_FRAC * h)),
        },
    }

    bbox = _coerce_bbox(img_or_bbox)

    if bbox is not None:
        # ---- declared-subject path: we know exactly what was drawn ----------
        report["source"] = "bbox"
        x0, y0, x1, y1 = bbox
        subject_w_frac = (x1 - x0 + 1) / float(w)
        subject_h_frac = (y1 - y0 + 1) / float(h)
        subject_v = ((y0 + y1) / 2.0) / h
        subject_bottom = (y1 + 1) / float(h)
        ink_fraction = None
        ink_ok = None
        v_centroid = None
    else:
        # ---- measured-frame path: read the rendered PNG --------------------
        arr = _load_rgb(img_or_bbox)
        ih, iw = arr.shape[0], arr.shape[1]
        w, h = iw, ih                       # trust the image's real size
        report["frame"] = (w, h)
        report["source"] = "image"
        ink_fraction, v_centroid, body = _measure_subject_from_image(arr, w, h)
        if body is None:
            report.update({
                "subject_bbox": None,
                "subject_w_frac": 0.0,
                "subject_h_frac": 0.0,
                "subject_v": v_centroid,
                "subject_bottom_frac": 0.0,
                "scale_ok": False,
                "scale_detail": "no ink component larger than %.0f%% of frame that is not a full-width band"
                                % (SUBJECT_MIN_AREA_FRAC * 100),
                "v_ok": False,
                "v_detail": "no subject to place",
                "ink_fraction": round(ink_fraction, 4),
                "ink_ok": ink_fraction >= INK_FRACTION_FLOOR,
                "v_centroid": round(v_centroid, 4),
                "pass": False,
                "failures": ["NO_SUBJECT", "SUBJECT_SCALE", "SUBJECT_V"],
                "note": ("no component qualified as the subject: every ink blob is either a "
                         "full-width band (title strip / caption) or smaller than %.0f%% of the "
                         "frame. The card has no body to fill the frame with."
                         % (SUBJECT_MIN_AREA_FRAC * 100)),
            })
            return report
        x0, y0, x1, y1 = body
        report["subject_bbox"] = [x0, y0, x1, y1]
        subject_w_frac = (x1 - x0 + 1) / float(w)
        subject_h_frac = (y1 - y0 + 1) / float(h)
        subject_v = ((y0 + y1) / 2.0) / h
        subject_bottom = (y1 + 1) / float(h)

    # ---- the two gates -----------------------------------------------------
    if kind == "figure":
        scale_ok = subject_h_frac >= FIGURE_HEIGHT
        scale_detail = "figure height %.3f (floor %.2f)" % (subject_h_frac, FIGURE_HEIGHT)
    else:
        scale_ok = subject_w_frac >= SUBJECT_SCALE
        scale_detail = "subject width %.3f (floor %.2f)" % (subject_w_frac, SUBJECT_SCALE)

    v_ok = SUBJECT_V_MIN <= subject_v <= V_CENTROID_RANGE[1]
    v_detail = "subject centre %.3f (must be in [%.2f, %.2f])" % (
        subject_v, SUBJECT_V_MIN, V_CENTROID_RANGE[1])

    # informational whole-frame ink coverage (image inputs only)
    ink_ok = None
    if include_ink and ink_fraction is not None:
        ink_ok = ink_fraction >= INK_FRACTION_FLOOR

    failures = []
    if not scale_ok:
        failures.append("SUBJECT_SCALE")
    if not v_ok:
        failures.append("SUBJECT_V")

    report.update({
        "subject_bbox": report.get("subject_bbox", bbox),
        "subject_w_frac": round(subject_w_frac, 4),
        "subject_h_frac": round(subject_h_frac, 4),
        "subject_v": round(subject_v, 4),
        "subject_bottom_frac": round(subject_bottom, 4),
        "scale_ok": bool(scale_ok),
        "scale_detail": scale_detail,
        "v_ok": bool(v_ok),
        "v_detail": v_detail,
        "ink_fraction": (round(ink_fraction, 4) if ink_fraction is not None else None),
        "ink_ok": ink_ok,
        "v_centroid": (round(v_centroid, 4) if v_centroid is not None else None),
        "pass": bool(scale_ok and v_ok),
        "failures": failures,
    })
    if ink_fraction is not None:
        report["note"] = ("ink_fraction is whole-frame coverage (informational). "
                          "dark_mask_fraction and muted_fraction are register-confounded "
                          "and are deliberately not used here.")
    return report


# ---------------------------------------------------------------------------
# 4. fill_frame_guidance() -> prompt-ready rules with explicit numbers
# ---------------------------------------------------------------------------

def fill_frame_guidance() -> str:
    """
    Return a short human-readable statement of the composition rules, with the
    numbers spelled out, suitable for pasting into a renderer prompt so it cannot
    get them wrong.
    """
    min_w_px = int(round(SUBJECT_SCALE * CARD_W))
    fig_h_px = int(round(FIGURE_HEIGHT * CARD_H))
    bottom_q = int(round(0.75 * CARD_H))
    return (
        "COMPOSITION / FILL THE FRAME (G1). The primary subject must FILL the frame and sit "
        "in the LOWER two-thirds, not float small in the upper third.\n"
        "  - ink_fraction (whole-frame non-background coverage): >= %.2f. Ours runs %.2f-%.2f; "
        "the reference median is 0.41. Scale the subject up until this is met.\n"
        "  - subject SCALE: the primary subject must span >= %.0f%% of the frame WIDTH "
        "(>= %d px on a 1280-wide card). Ours is ~20%%; the reference is ~100%%.\n"
        "  - a standing FIGURE must span >= %.0f%% of the frame HEIGHT (>= %d px), head to feet.\n"
        "  - vertical centre of mass (v_centroid / subject centre y): in the window "
        "[%.2f, %.2f] -- i.e. the LOWER two-thirds. Reference median 0.59; ours as low as 0.37.\n"
        "  - GROUND LINE: a standing figure's FEET belong at y = %d (bottom quarter of a 720-tall "
        "card, which starts at y = %d). Draw him standing ON that line; no floating feet.\n"
        "Do NOT chase dark_mask_fraction -- it is register-confounded (a space card scores high "
        "from its background alone). Do NOT gate on muted_fraction -- it is bimodal by design.\n"
        "Do NOT let a label collide with the subject silhouette or cross the frame edge."
        % (
            INK_FRACTION_FLOOR, 0.195, 0.235,
            SUBJECT_SCALE * 100, min_w_px,
            FIGURE_HEIGHT * 100, fig_h_px,
            V_CENTROID_RANGE[0], V_CENTROID_RANGE[1],
            GROUND_Y, bottom_q,
        )
    )


# ---------------------------------------------------------------------------
# Self-test: run directly to print a PASSING and a FAILING layout.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(subject_box(CARD_W, CARD_H))
    print()
    print("PASSING (subject fills frame, sits low):")
    import json
    print(json.dumps(check_composition((307, 176, 973, 719), kind="body"), indent=2))
    print()
    print("FAILING (small subject floating high):")
    print(json.dumps(check_composition((512, 96, 768, 336), kind="body"), indent=2))
    print()
    print(fill_frame_guidance())