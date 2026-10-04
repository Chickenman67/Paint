#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
work/segments/_gate.py
=======================

REGISTER-AWARE ACCEPTANCE GATE for cardsheet PNGs.

This tool answers exactly one question per frame:

    "does this frame's measured composition conform to a stated range?"

It does NOT answer "is this frame better than that frame". There is no winner,
no score, no ranking, and no comparison of two images anywhere in this file.
That refusal is inherited deliberately from work/lib/measure_frames.py, whose
compare() emits structured observations but never a verdict; pixel statistics
measure structure, not craft, and the moment a script ranks two frames it starts
producing confident nonsense. This gate therefore checks ONE frame against a
range and stops.

MEASUREMENT IS NOT REIMPLEMENTED. Every composition number comes from
measure_frames.measure(), which is verified against a brute-force BFS reference.
This file adds two checks the existing module does not have -- local text
contrast and edge clipping -- because both need a *local neighbourhood*, which
measure_frames deliberately does not compute (its binarisation is global: any
pixel more than L1 30 from the single most dominant cluster is "ink", so
dark-on-dark text is invisible to it by construction).

MEASUREMENT KEY PATHS (these are the real nested paths, not the leaf names)
------------------------------------------------------------------------
    ink_fraction          m['layout_metrics']['ink_fraction']
    v_centroid            m['layout_metrics']['v_centroid']
    dark_mask_fraction    m['stickman_detection']['dark']['dark_mask_fraction']
    muted_fraction        m['anti_aliasing_proxy']['muted_fraction']
    palette_entropy_bits  m['dominant_colors']['palette_entropy_bits']
    background colour     m['layout_metrics']['background_hex']
                          (equivalently m['dominant_colors']['palette'][0])

REGISTER, AND WHY TWO THRESHOLDS
--------------------------------
The cards alternate between two visual registers: PAINT (cream/paper ground)
and SPACE (near-black void). They are not variants of one thing; a card is
either on paper or in the void, and a threshold that is right for one is wrong
for the other. Register is therefore classified from the frame's OWN pixels --
never from the filename -- and ink_fraction is gated per register.

THE REGISTER-CONFOUNDED METRICS (printed, never gated)
-------------------------------------------------------
    dark_mask_fraction, muted_fraction

dark_mask_fraction counts every near-black pixel in the frame. A space card
scores ~0.5 from its BACKGROUND alone, while its linework is exactly as thin as
a cream card's. Chasing the reference's 0.371 by thickening outlines would make
every cream card wrong. muted_fraction is bimodal by design (~0.12 on paint
beats, ~0.97 on space beats) because the two registers alternate by design. Both
are reported because they are cheap and because a builder chasing composition
should see them, and both are excluded from the gate for that reason.

USAGE
-----
    python work/segments/_gate.py <segdir> [<segdir> ...]
    python work/segments/_gate.py tres2b wasp17b --json out.json

A segdir is any directory containing a cardsheet/ subdirectory of PNGs.
Exit code is non-zero if any frame failed any gated check.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = os.path.normpath(os.path.join(_HERE, "..", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

import measure_frames as MF  # noqa: E402  (path must be set first)


# ---------------------------------------------------------------------------
# Stated acceptance ranges. Every number here is a RANGE CONFORMANCE TARGET,
# not a score, and not a comparison against another image.
# ---------------------------------------------------------------------------

# ink_fraction: the reference median is 0.406. Ours measured 0.235 (tres2b) and
# 0.195 (wasp17b) -- under half. The gates below are set below the reference so
# that a frame has to be genuinely under-occupied to fail, while still being a
# real floor rather than a rubber stamp.
INK_MIN = {"PAINT": 0.30, "SPACE": 0.22}

# v_centroid: 0.5 is frame centre, 1.0 is the bottom edge. The reference sits at
# 0.586 (lower two-thirds); ours hit 0.370 on wasp17b, i.e. visual mass in the
# UPPER third, which is the G1 composition defect. The window is deliberately
# generous upward so that a legitimately top-weighted space card is not failed,
# but 0.42 is already well above the 0.370 failure mode.
V_CENTROID_RANGE = (0.42, 0.75)


# --- local text contrast (G4) -------------------------------------------------
MORPH_K = 9          # structuring element for the local-background estimate
RESID_THR = 4.0      # luma units; must be below LOW_CONTRAST to be able to fire
LOW_CONTRAST = 25.0  # luma units; spec-mandated reporting threshold
MIN_GLYPH_AREA = 20
# GLYPH_H_MIN was 8, which let every 9x9 starfield dot through the detector and
# produced 749 "LOW_CONTRAST_TEXT" hits across 9 cardsheets -- almost all of them
# white stars on a dark space background, which is correct art. The smallest
# caption cap-height this project renders is 15px (the tiny annotation size in
# lib/type.py); the lock-scale captions are 28-48px. A component shorter than
# 13px cannot be type at any size in the locked scale, so it cannot be a legibility
# defect. Set to 13 to exclude starfield and stipple.
GLYPH_H_MIN = 13
GLYPH_H_MAX_FRAC = 0.22   # a 720p caption cap-height is ~20-100px
GLYPH_FILL_RANGE = (0.06, 0.80)
GLYPH_RUN_MAX_RATIO = 0.75  # median row-run length / height; separates type from shapes
# Minimum glyphs in a merged run. Raising GLYPH_H_MIN alone was not enough: it cut
# the star noise but wasp127b still reported 417 hits, and sampling them showed
# EVERY remaining false positive had glyphs=1 -- an isolated blob with no
# neighbours. A starfield dot, a stipple speck, and a single disconnected mark are
# all glyphs=1. Real type is a WORD: after _merge_runs, a legible label always
# brings up several components on one line. The known-true positive
# (tres2b beat_03, the near-black "TrES-2b" on the near-black disc) has glyphs=2
# at 128x28, so a floor of 2 keeps it. This is the discriminator that actually
# separates type from texture; size alone never did.
GLYPH_MIN_RUN = 2
# Cap-height consistency. Verified at full resolution on wasp127b beat_10: all 36
# of that frame's LOW_CONTRAST_TEXT hits were the segment's background STIPPLE
# texture, not type -- every real label on the card (UPWARD, AND KEEPS GOING,
# WASP-127B) is perfectly legible. Stipple and hatch marks merge into runs because
# they share rows, so run-merging alone cannot reject them. What reliably separates
# them is that letters in a word share a cap height and a baseline, while texture
# marks vary by a factor of two or more within any accidental group. Require the
# heights in a run to agree within this ratio.
GLYPH_RUN_HEIGHT_RATIO = 1.45
RING_IN = 6          # inner radius of the surround ring, px
RING_OUT = 14        # outer radius of the surround ring, px
RING_FLAT_SPREAD = 45.0  # max robust p95-p5 spread for the surround to count as "flat ground"

# --- edge clipping (G5) -------------------------------------------------------
CLIP_SIZE_FRAC = 0.45      # spec: bbox w OR h must be under this fraction
CLIP_BAND_FRAC = 0.97     # a component spanning this much of an axis is a band
# CLIP_LABEL_H_FRAC was 0.16 (115px on a 720px frame), which is wide enough to
# admit any small object that happens to touch the frame edge -- it produced 217
# CLIPPED_AT_EDGE hits across 9 cardsheets. A clipped caption glyph run is
# caption-scale: at the locked 28px caption size a 3-6 character run is roughly
# 60-160px tall including ascenders, but the overwhelming majority sit well
# under 80px. 0.11 (79px) keeps real clipped labels and drops edge dots.
CLIP_LABEL_H_FRAC = 0.11
MIN_CLIP_AREA = 20
CLIP_MIN_W_PX = 10      # nothing narrower than a readable glyph is a clipped label
CLIP_MIN_W_RATIO = 0.22  # ...and a clipped glyph is never a 4px-wide sliver


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def _hex_to_rgb(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], dtype=np.float64)


def classify_register(m):
    """
    Register from the frame's own pixels.

    Background = the dominant cluster measure_frames already found. If its luma
    is very dark the frame is SPACE; very light, PAINT. Otherwise fall back to
    the frame's mean luma against 128, which at least splits a mid-tone frame
    into a lighter and a darker half.

    Returns (register, bg_luma, mean_luma, how).
    """
    bg_hex = m["layout_metrics"]["background_hex"]
    bg_luma = float(_hex_to_rgb(bg_hex).dot([0.299, 0.587, 0.114]))
    lum = _luma_of(MF.load_rgb(m["path"]))
    mean_luma = float(lum.mean())

    if bg_luma < 40.0:
        reg, how = "SPACE", "bg luma %.1f < 40" % bg_luma
    elif bg_luma > 200.0:
        reg, how = "PAINT", "bg luma %.1f > 200" % bg_luma
    elif mean_luma < 128.0:
        reg, how = "SPACE", "mid-tone bg %.1f, frame mean luma %.1f < 128" % (bg_luma, mean_luma)
    else:
        reg, how = "PAINT", "mid-tone bg %.1f, frame mean luma %.1f >= 128" % (bg_luma, mean_luma)
    return reg, bg_luma, mean_luma, how


# ---------------------------------------------------------------------------
# Local structure -- shared by the contrast check and the clipping check
# ---------------------------------------------------------------------------

def _luma_of(arr):
    return 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]


def detail_residual(lum):
    """
    |luma - local flat background|, computed as the MAX of the distance to a
    grayscale OPENING and to a grayscale CLOSING of the frame.

    Why morphology and not a block median: a block-median background is wrong
    wherever a block straddles the edge of a large object. The leftover of the
    block's other colour then appears as a phantom strip at the block boundary.
    Measured on wasp17b beat_06 that produced three fake "text runs" of pure
    background cream sitting inside dark blocks. Opening and closing have no
    such seam: both preserve large flat regions and large object interiors, and
    both remove only details THINNER than the structuring element.

    Taking the max of the two distances is what makes the check polarity-blind:
      * dark glyph on light ground -> the CLOSING erases it, so it differs from
        the closing;
      * light glyph on dark ground -> the OPENING erases it, so it differs from
        the opening;
      * flat field, either polarity -> differs from neither;
      * a wide object edge -> is interior to the object, survives both.
    So a genuine thin detail fires and a large flat area cannot, without the
    detector ever being told which colour is on top.
    """
    im = Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8), "L")
    opening = np.asarray(
        im.filter(ImageFilter.MinFilter(MORPH_K)).filter(ImageFilter.MaxFilter(MORPH_K)),
        dtype=np.float64)
    closing = np.asarray(
        im.filter(ImageFilter.MaxFilter(MORPH_K)).filter(ImageFilter.MinFilter(MORPH_K)),
        dtype=np.float64)
    return np.maximum(np.abs(lum - opening), np.abs(lum - closing))


def _median_run_len(row_bool):
    runs = []
    start = None
    for i, v in enumerate(row_bool):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append(i - start)
            start = None
    if start is not None:
        runs.append(len(row_bool) - start)
    return runs


def _median_row_run_height(sub):
    heights = []
    col_any = sub.any(axis=1)
    start = None
    for i, v in enumerate(col_any):
        if v and start is None:
            start = i
        elif not v and start is not None:
            heights.append(i - start)
            start = None
    if start is not None:
        heights.append(len(col_any) - start)
    return float(np.median(heights)) if heights else 0.0


def _is_glyph_like(cc, h_px, w_px, run_h, run_w):
    """
    Does this component look like a glyph run rather than a shape?

    Two independent discriminators, because size alone does not separate them:
      * fill_ratio in GLYPH_FILL_RANGE -- rejects solid discs and bands, keeps
        the 0.3-0.6 of a run with whitespace between and inside glyphs;
      * run_w / run_h <= GLYPH_RUN_MAX_RATIO -- a glyph stroke is a few px wide
        against a 20-40px glyph height. A filled disc has rows that are one long
        span, so its run_w is comparable to its full width and this rejects it.
        This is the check that keeps a 101x35 planet-with-strata from being
        reported as low-contrast text.
    """
    if cc["area"] < MIN_GLYPH_AREA:
        return False, "area %d < %d" % (cc["area"], MIN_GLYPH_AREA)
    if not (GLYPH_H_MIN <= run_h <= GLYPH_H_MAX_FRAC * h_px):
        return False, "run_h %.0f outside [%d, %.0f]" % (run_h, GLYPH_H_MIN, GLYPH_H_MAX_FRAC * h_px)
    if not (GLYPH_FILL_RANGE[0] <= cc["fill_ratio"] <= GLYPH_FILL_RANGE[1]):
        return False, "fill_ratio %.2f outside %s" % (cc["fill_ratio"], GLYPH_FILL_RANGE)
    if run_h <= 0 or (run_w / run_h) > GLYPH_RUN_MAX_RATIO:
        return False, "run_w/run_h %.2f > %.2f (solid shape, not type)" % (
            run_w / run_h if run_h else 99.0, GLYPH_RUN_MAX_RATIO)
    return True, ""


def _merge_runs(glyphs):
    """
    Union glyph components that sit on the same line into runs, so a word is
    measured as one thing. A glyph is not a word: 'TrES-2b' is eight components
    and the surround ring of any one of them is contaminated by its neighbours,
    which would bias the contrast DOWNWARD (conservative) but also report eight
    bboxes instead of one. Merging fixes both.

    `glyphs` is the list of {"cc", "run_h", "run_w"} dicts. Merging is on their
    component bboxes only; the shape metrics are looked up per member afterwards.

    Same-line test: vertical overlap of at least 60% of the shorter component,
    and a horizontal gap no larger than 1.5x the taller component's height.
    """
    n = len(glyphs)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for i in range(n):
        ax0, ay0, ax1, ay1 = glyphs[i]["cc"]["bbox"]
        ah = ay1 - ay0 + 1
        for j in range(i + 1, n):
            bx0, by0, bx1, by1 = glyphs[j]["cc"]["bbox"]
            bh = by1 - by0 + 1
            ov = min(ay1, by1) - max(ay0, by0) + 1
            if ov < 0.6 * min(ah, bh):
                continue
            gap = max(ax0, bx0) - min(ax1, bx1)
            if gap <= 1.5 * max(ah, bh):
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def analyse_structure(path):
    """
    Both new checks share one segmentation pass.

    Returns (low_contrast_findings, clipped_findings, stats).
    """
    arr = MF.load_rgb(path)
    h, w, _ = arr.shape
    lum = _luma_of(arr)
    resid = detail_residual(lum)
    mask = resid > RESID_THR

    labels, n = MF.connected_components(mask)
    if n == 0:
        return [], [], {"detail_components": 0}

    ccs = [c for c in MF.component_stats(labels, n) if c["area"] >= MIN_GLYPH_AREA]

    shapes = []
    for c in ccs:
        x0, y0, x1, y1 = c["bbox"]
        sub = labels[y0:y1 + 1, x0:x1 + 1] == c["label"]
        run_h = _median_row_run_height(sub)
        row_runs = []
        for r in range(sub.shape[0]):
            if sub[r].any():
                row_runs.extend(_median_run_len(sub[r]))
        run_w = float(np.median(row_runs)) if row_runs else 0.0
        shapes.append({"cc": c, "run_h": run_h, "run_w": run_w})

    # ---------------- LOW_CONTRAST_TEXT ----------------
    glyphs = []
    for s in shapes:
        ok, why = _is_glyph_like(s["cc"], h, w, s["run_h"], s["run_w"])
        if ok:
            glyphs.append(s)

    low_contrast = []
    for grp in _merge_runs(glyphs):
        # A real label is a WORD. After _merge_runs, an isolated blob stays a
        # single-component group -- that is a star, a stipple speck, or a lone
        # stray mark, never a legibility defect. Requiring >= GLYPH_MIN_RUN
        # components is what finally separated type from texture here; the height
        # and fill-ratio gates alone could not.
        if len(grp) < GLYPH_MIN_RUN:
            continue
        members = [glyphs[i] for i in grp]
        # Reject texture: stipple and hatch marks accidentally group by row, but
        # their heights disagree wildly. Letters on a line share a cap height.
        hs = [m["run_h"] for m in members if m["run_h"] > 0]
        if len(hs) >= 2 and (max(hs) / min(hs)) > GLYPH_RUN_HEIGHT_RATIO:
            continue
        bxs = [m["cc"]["bbox"] for m in members]
        x0 = min(b[0] for b in bxs)
        y0 = min(b[1] for b in bxs)
        x1 = max(b[2] for b in bxs)
        y1 = max(b[3] for b in bxs)

        # the run's own pixels
        own = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=bool)
        for m in members:
            mx0, my0, mx1, my1 = m["cc"]["bbox"]
            own[my0 - y0:my1 - y0 + 1, mx0 - x0:mx1 - x0 + 1] |= (
                labels[my0:my1 + 1, mx0:mx1 + 1] == m["cc"]["label"])

        lum_win = lum[y0:y1 + 1, x0:x1 + 1]
        own_luma = float(lum_win[own].mean())

        # ring: RING_IN..RING_OUT px outside the bbox, excluding any other detail
        # pixel so that a neighbouring glyph cannot drag the surround toward it
        rx0, ry0 = max(0, x0 - RING_OUT), max(0, y0 - RING_OUT)
        rx1, ry1 = min(w - 1, x1 + RING_OUT), min(h - 1, y1 + RING_OUT)
        inner = np.zeros((ry1 - ry0 + 1, rx1 - rx0 + 1), dtype=bool)
        inner[max(0, y0 - RING_IN) - ry0: y1 + RING_IN - ry0 + 1,
              max(0, x0 - RING_IN) - rx0: x1 + RING_IN - rx0 + 1] = True
        detail = mask[ry0:ry1 + 1, rx0:rx1 + 1]
        ring = ~inner & ~detail
        if int(ring.sum()) < 40:
            continue
        ring_vals = lum[ry0:ry1 + 1, rx0:rx1 + 1][ring]
        ring_luma = float(ring_vals.mean())
        ring_spread = float(np.percentile(ring_vals, 95) - np.percentile(ring_vals, 5))

        # A genuinely low-contrast label sits in the MIDDLE of a flat field of
        # one colour -- text and ground are the same tone, which is the defect.
        # The morphological residual also fires on the 1-2px antialiased RIM of
        # a thick, perfectly readable stroke; that rim's surround straddles the
        # stroke edge and is wildly non-uniform. Requiring the surround to be
        # flat separates the two: measured on wasp17b beat_06 the rim artifact
        # had ring p95-p5 spread 212 on a uniform cream card, while the real
        # dark-on-dark TrES-2b label on tres2b beat_03 had spread 0. Without this
        # guard the rim reports as "low contrast text" on every frame that has a
        # bold header, which is noise, not a finding.
        if ring_spread > RING_FLAT_SPREAD:
            continue

        contrast = abs(own_luma - ring_luma)

        if contrast < LOW_CONTRAST:
            low_contrast.append({
                "check": "LOW_CONTRAST_TEXT",
                "bbox": [x0, y0, x1, y1],
                "w": x1 - x0 + 1, "h": y1 - y0 + 1,
                "n_glyphs": len(members),
                "run_h": round(max(m["run_h"] for m in members), 1),
                "text_luma": round(own_luma, 1),
                "surround_luma": round(ring_luma, 1),
                "surround_spread": round(ring_spread, 1),
                "contrast": round(contrast, 1),
                "threshold": LOW_CONTRAST,
            })

    # ---------------- CLIPPED_AT_EDGE ----------------
    # Same glyph test as the contrast check, with one extra bound: a clipped
    # LABEL is caption-scale. Without that cap a scene stroke that happens to
    # bleed off an edge and happens to be thin (a planet limb arc, a torn shell
    # contour) passes every text test and gets reported as a clipped label. The
    # cap is what separates "wasp127b beat_10 has three caption words running
    # off the left edge" from "gliese436b beat_09 has a 1021px arc that leaves
    # the right edge" -- both are thin, both are glyph-shaped by run width, only
    # one is type.
    clipped = []
    # Only a component that merged into a multi-component line can be a clipped
    # LABEL. Verified at full resolution on psoj3185 beat_02: every one of that
    # frame's 119 CLIPPED_AT_EDGE hits was a white hatch stroke of the
    # "EDGE OF THE SYSTEM" wedge, clipped by the wedge's own outline near x=0.
    # Nothing was actually clipped -- the frame is full-bleed by design. Hatch
    # strokes are isolated single components; a clipped caption glyph has company
    # on its baseline. Reusing the glyph list and the merged-run grouping is what
    # makes this check honest; iterating raw components (as it did) reports scene
    # texture as typography.
    glyph_idx = {id(g["cc"]): i for i, g in enumerate(glyphs)}
    clipped_runs = {frozenset(grp) for grp in _merge_runs(glyphs)
                    if len(grp) >= GLYPH_MIN_RUN}
    for s in shapes:
        c = s["cc"]
        gi = glyph_idx.get(id(c))
        if gi is None:
            continue
        if not any(gi in grp for grp in clipped_runs):
            continue
        x0, y0, x1, y1 = c["bbox"]
        edges = []
        if x0 == 0:
            edges.append("left")
        if x1 == w - 1:
            edges.append("right")
        if y0 == 0:
            edges.append("top")
        if y1 == h - 1:
            edges.append("bottom")
        if not edges:
            continue

        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        # spec: only text or a thin label, never a full-bleed band or a scene
        if not (bw < CLIP_SIZE_FRAC * w or bh < CLIP_SIZE_FRAC * h):
            continue
        # a band spans a whole axis and touches both ends of it -- that is the
        # background, not a clipped label
        if bw >= CLIP_BAND_FRAC * w and "left" in edges and "right" in edges:
            continue
        if bh >= CLIP_BAND_FRAC * h and "top" in edges and "bottom" in edges:
            continue
        if c["area"] < MIN_CLIP_AREA:
            continue
        ok, why = _is_glyph_like(c, h, w, s["run_h"], s["run_w"])
        if not ok:
            continue
        if s["run_h"] > CLIP_LABEL_H_FRAC * h:
            continue
        # A starfield dot touching the border is a 4-6px sliver: the height test
        # above reads run_h, not bbox width, so a 4x55 vertical speck passed every
        # glyph test and was reported as a clipped label (130 such hits on
        # psoj3185). A real clipped glyph or word has width commensurate with its
        # height -- even the tall thin characters (l, I, 1) keep bw >= ~0.22*bh.
        # Require that, plus a minimum absolute width so nothing smaller than a
        # readable glyph can qualify.
        if bw < CLIP_MIN_W_PX or bw < CLIP_MIN_W_RATIO * bh:
            continue

        clipped.append({
            "check": "CLIPPED_AT_EDGE",
            "edges": edges,
            "bbox": [x0, y0, x1, y1],
            "w": bw, "h": bh,
            "fill_ratio": c["fill_ratio"],
            "run_h": round(s["run_h"], 1),
            "area": c["area"],
        })

    low_contrast.sort(key=lambda d: d["contrast"])
    clipped.sort(key=lambda d: (d["bbox"][1], d["bbox"][0]))
    return low_contrast, clipped, {
        "detail_components": int(n),
        "glyph_like_components": len(glyphs),
        "detail_pixel_fraction": round(float(mask.mean()), 5),
    }


# ---------------------------------------------------------------------------
# Per-frame gate
# ---------------------------------------------------------------------------

# MEASUREMENT_ERROR is a check in its own right: it fires when a frame could not
# be measured at all, which happens in practice because a builder re-rendering a
# cardsheet can delete and rewrite a PNG between our glob and our open. A frame
# we could not measure has NOT passed, so it counts as a failure.
GATE_CHECKS = ("INK_FRACTION", "V_CENTROID", "LOW_CONTRAST_TEXT", "CLIPPED_AT_EDGE",
               "MEASUREMENT_ERROR")


def gate_frame(path):
    m = MF.measure(path)
    reg, bg_luma, mean_luma, reg_how = classify_register(m)

    lm = m["layout_metrics"]
    aa = m["anti_aliasing_proxy"]
    sd = m["stickman_detection"]["dark"]

    failures = []
    notes = []

    ink = float(lm["ink_fraction"])
    ink_min = INK_MIN[reg]
    if ink < ink_min:
        failures.append(("INK_FRACTION", ink, "min %.2f for %s" % (ink_min, reg)))

    vc = float(lm["v_centroid"])
    if not (V_CENTROID_RANGE[0] <= vc <= V_CENTROID_RANGE[1]):
        failures.append(("V_CENTROID", vc, "must be in [%.2f, %.2f]" % V_CENTROID_RANGE))

    low_contrast, clipped, stats = analyse_structure(path)
    for f in low_contrast:
        failures.append(("LOW_CONTRAST_TEXT", f["contrast"], f["bbox"], f))
    for f in clipped:
        failures.append(("CLIPPED_AT_EDGE", 0.0, f["bbox"], f))

    return {
        "path": path,
        "basename": os.path.basename(path),
        "register": reg,
        "register_reason": reg_how,
        "background_hex": lm["background_hex"],
        "background_luma": round(bg_luma, 1),
        "mean_luma": round(mean_luma, 1),
        "gated": {
            "ink_fraction": ink,
            "ink_fraction_min": ink_min,
            "v_centroid": vc,
            "v_centroid_range": list(V_CENTROID_RANGE),
        },
        "informational": {
            "dark_mask_fraction": sd["dark_mask_fraction"],
            "muted_fraction": aa["muted_fraction"],
            "palette_entropy_bits": m["dominant_colors"]["palette_entropy_bits"],
            "note": ("dark_mask_fraction and muted_fraction are REGISTER-CONFOUNDED "
                     "and INFORMATIONAL ONLY -- a space card scores high on dark_mask_fraction "
                     "from its background alone, and muted_fraction is bimodal by design "
                     "(~0.12 paint, ~0.97 space). Do not gate on either."),
        },
        "structure": stats,
        "low_contrast_text": low_contrast,
        "clipped_at_edge": clipped,
        "failures": failures,
        "passed": not failures,
        "measure": m,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _fmt(v, nd=3):
    return "n/a" if v is None else ("%.*f" % (nd, v))


def print_frame_table(rows):
    hdr = ("%-16s %-6s %8s %9s %9s %10s %10s %6s" %
           ("frame", "reg", "ink", "ink_min", "v_cent", "dark_msk*", "muted*", "result"))
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        g = r["gated"]
        info = r["informational"]
        print("%-16s %-6s %8s %9s %9s %10s %10s %6s" % (
            r["basename"], r["register"],
            _fmt(g["ink_fraction"]), _fmt(g["ink_fraction_min"], 2),
            _fmt(g["v_centroid"]),
            _fmt(info["dark_mask_fraction"]), _fmt(info["muted_fraction"]),
            "PASS" if r["passed"] else "FAIL"))
    print("* dark_mask_fraction and muted_fraction are REGISTER-CONFOUNDED and "
          "INFORMATIONAL ONLY. They are printed, never gated: a space card scores "
          "high on dark_mask_fraction from its background alone, and muted_fraction "
          "is bimodal by design (~0.12 paint beats, ~0.97 space beats).")
    print()


def print_detail(rows, seg):
    """Print the register reason and every failure with the frame's own numbers."""
    print("--- %s : per-frame detail ---" % seg)
    for r in rows:
        g, info = r["gated"], r["informational"]
        print("\n  %s  [%s]  %s" % (
            r["basename"], r["register"], r["register_reason"]))
        print("      background %s (luma %.1f)   frame mean luma %.1f" % (
            r["background_hex"], r["background_luma"], r["mean_luma"]))
        print("      ink_fraction %.3f   (gate: >= %.2f for %s)   v_centroid %.3f   (gate: %.2f..%.2f)"
              % (g["ink_fraction"], g["ink_fraction_min"], r["register"],
                 g["v_centroid"], g["v_centroid_range"][0], g["v_centroid_range"][1]))
        print("      informational: dark_mask_fraction %.3f   muted_fraction %.3f   palette_entropy_bits %.3f"
              % (info["dark_mask_fraction"], info["muted_fraction"], info["palette_entropy_bits"]))
        if r["passed"]:
            print("      PASS - all gated checks conform.")
            continue
        for f in r["failures"]:
            if f[0] == "LOW_CONTRAST_TEXT":
                d = f[3]
                print("      FAIL LOW_CONTRAST_TEXT  bbox=%s  %dx%d  glyphs=%d  run_h=%.0fpx" % (
                    d["bbox"], d["w"], d["h"], d["n_glyphs"], d["run_h"]))
                print("           text luma %.1f vs local surround luma %.1f (surround spread %.1f)  ->  contrast %.1f "
                      "(threshold %.1f)" % (d["text_luma"], d["surround_luma"], d["surround_spread"],
                                            d["contrast"], d["threshold"]))
            elif f[0] == "CLIPPED_AT_EDGE":
                d = f[3]
                print("      FAIL CLIPPED_AT_EDGE  edges=%s  bbox=%s  %dx%d  fill_ratio %.2f  run_h=%.0fpx" % (
                    ",".join(d["edges"]), d["bbox"], d["w"], d["h"], d["fill_ratio"], d["run_h"]))
            elif f[0] == "INK_FRACTION":
                print("      FAIL INK_FRACTION  ink_fraction %.3f  %s" % (f[1], f[2]))
            elif f[0] == "V_CENTROID":
                print("      FAIL V_CENTROID  v_centroid %.3f  %s" % (f[1], f[2]))
            elif f[0] == "MEASUREMENT_ERROR":
                print("      FAIL MEASUREMENT_ERROR  %s" % (f[2],))
    print()


def print_summary(seg, rows):
    counts = {}
    for r in rows:
        for f in r["failures"]:
            counts[f[0]] = counts.get(f[0], 0) + 1
    for c in GATE_CHECKS:
        counts.setdefault(c, 0)
    n_fail = sum(1 for r in rows if not r["passed"])
    print("SUMMARY %s: %d frames, %d passed, %d failed   [%s]" % (
        seg, len(rows), len(rows) - n_fail, n_fail,
        ", ".join("%s=%d" % (c, counts[c]) for c in GATE_CHECKS)))


NO_VERDICT = ("NO WINNER, NO SCORE, NO RANKING is computed anywhere in this tool, "
              "and no two images are ever compared. Each frame is checked against a "
              "stated range on its own pixels. Deciding what the numbers mean is the "
              "critic's job.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def find_cardsheets(segdir):
    sheet = os.path.join(segdir, "cardsheet")
    if not os.path.isdir(sheet):
        # accept being handed the cardsheet dir itself
        if os.path.basename(segdir) == "cardsheet":
            sheet = segdir
        else:
            return []
    pngs = sorted(glob.glob(os.path.join(sheet, "*.png")))
    return [p for p in pngs if not os.path.basename(p).startswith("_")]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Register-aware acceptance gate for cardsheet frames. "
                    "Checks ONE frame against a stated range. Emits no winner.")
    ap.add_argument("segdirs", nargs="+", help="dirs containing cardsheet/*.png")
    ap.add_argument("--json", dest="json_out", help="write full per-frame results as JSON")
    args = ap.parse_args(argv)

    print("=" * 100)
    print("CARDSHEET GATE -- register-aware conformance check")
    print(NO_VERDICT)
    print("Measurement reused from work/lib/measure_frames.py (measure()); not reimplemented.")
    print("=" * 100)

    all_out = {}
    total_failed_frames = 0
    total_frames = 0
    total_failures = []

    for sd in args.segdirs:
        sd = os.path.normpath(sd)
        seg = os.path.basename(sd)
        pngs = find_cardsheets(sd)
        if not pngs:
            print("\n!! %s: no cardsheet/*.png found -- skipped" % sd)
            continue
        print("\n\n" + "#" * 100)
        print("# %s   (%d frames)" % (sd, len(pngs)))
        print("#" * 100)

        rows = []
        for p in pngs:
            try:
                rows.append(gate_frame(p))
            except FileNotFoundError as exc:
                # A builder re-rendering the cardsheet deleted this PNG between
                # our glob and our open. It is not a conformance failure; it is
                # an unstable input, and it is reported as its own check so it is
                # never mistaken for a pass.
                print("\n!! %s: file vanished mid-run (cardsheet is being "
                      "re-rendered concurrently?): %s" % (p, exc))
                print("\n!! %s: measurement failed: %s" % (p, exc))
                rows.append({
                    "path": p, "basename": os.path.basename(p),
                    "register": "?", "register_reason": "measurement failed: %s" % exc,
                    "background_hex": "?", "background_luma": 0.0, "mean_luma": 0.0,
                    "gated": {"ink_fraction": 0.0, "ink_fraction_min": 0.0,
                              "v_centroid": 0.0, "v_centroid_range": list(V_CENTROID_RANGE)},
                    "informational": {"dark_mask_fraction": 0.0, "muted_fraction": 0.0,
                                      "palette_entropy_bits": 0.0, "note": ""},
                    "structure": {}, "low_contrast_text": [], "clipped_at_edge": [],
                    "failures": [("MEASUREMENT_ERROR", 0.0, "file vanished mid-run"
                                  if isinstance(exc, FileNotFoundError) else str(exc))],
                    "passed": False, "measure": None,
                })

        print_frame_table(rows)
        print_detail(rows, seg)
        print_summary(seg, rows)
        print()

        total_frames += len(rows)
        total_failed_frames += sum(1 for r in rows if not r["passed"])
        for r in rows:
            for f in r["failures"]:
                total_failures.append({"segment": seg, "frame": r["basename"], "check": f[0]})
        all_out[seg] = [{
            "basename": r["basename"], "path": r["path"], "register": r["register"],
            "register_reason": r["register_reason"],
            "background_hex": r["background_hex"],
            "background_luma": r["background_luma"], "mean_luma": r["mean_luma"],
            "gated": r["gated"], "informational": r["informational"],
            "structure": r["structure"],
            "low_contrast_text": r["low_contrast_text"],
            "clipped_at_edge": r["clipped_at_edge"],
            "failures": [
                {"check": f[0], "value": f[1],
                 "detail": (f[3] if len(f) > 3 else None),
                 "criterion": f[2]}
                for f in r["failures"]
            ],
            "passed": r["passed"],
        } for r in rows]

    counts = {}
    for f in total_failures:
        counts[f["check"]] = counts.get(f["check"], 0) + 1
    print("=" * 100)
    print("OVERALL: %d frames checked, %d passed, %d failed" %
          (total_frames, total_frames - total_failed_frames, total_failed_frames))
    if counts:
        print("failing checks: " + ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    for f in total_failures:
        print("   FAIL %-20s %s / %s" % (f["check"], f["segment"], f["frame"]))
    print(NO_VERDICT)
    print("=" * 100)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({
                "tool": "_gate.py",
                "note": NO_VERDICT,
                "ranges": {
                    "ink_fraction_min": INK_MIN,
                    "v_centroid": list(V_CENTROID_RANGE),
                    "low_contrast_luma": LOW_CONTRAST,
                    "clip_size_frac": CLIP_SIZE_FRAC,
                },
                "gated_checks": list(GATE_CHECKS),
                "informational_only": ["dark_mask_fraction", "muted_fraction"],
                "segments": all_out,
            }, fh, indent=2, default=str)
        print("\nJSON written to %s" % args.json_out)

    return 1 if total_failed_frames else 0


if __name__ == "__main__":
    raise SystemExit(main())