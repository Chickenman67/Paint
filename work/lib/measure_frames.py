#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
work/lib/measure_frames.py
==========================

NON-VISION feature extraction for the gauntlet loop's critic stage.

WHY THIS EXISTS
---------------
The label-blind critic agents in round 6 died because the session model
(`free-stack`) has no vision: every frame-attachment request came back

    400 No target in combo free-stack has confirmed vision support
        for this image request

Blinding already succeeded (byte-identical copies under `pair_N_{A,B}.png`),
so the frames are on disk and unblinded-blind. What is missing is a way for a
*text-only* critic to say something non-hallucinating about them. This module
supplies that: it measures pixels, and only pixels.

GUARANTEES
----------
* PIL + numpy only. No vision model, no OCR, no network, no GPU.
* Fully deterministic. Same PNG in -> same numbers out, on any machine.
  (k-means uses a fixed seed and k-means++ init drawn from that seed.)
* Every number is measured from the file. Nothing is inferred from a filename,
  a directory name, or the segment it came from. This module NEVER opens
  `_KEY.json` and never learns which side is "ours".
* The `compare()` rules DO NOT emit a winner. They emit observations of the
  form "fewer_distinct_colors => more flat-fill / more hand-drawn" and leave
  the judgement to a human or a text critic. Auto-picking a winner from pixel
  statistics is the exact failure mode this file exists to avoid.

USAGE
-----
    python work/lib/measure_frames.py                     # run the built-in suite
    python work/lib/measure_frames.py IMG [IMG ...]       # measure specific PNGs
    python work/lib/measure_frames.py --json out.json     # machine-readable dump
    python work/lib/measure_frames.py --cmp A.png B.png   # side-by-side diff

Importable:

    from measure_frames import measure, compare, kmeans_colors
    f = measure("frame.png")
    d = compare("ours.png", "theirs.png")
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED = 1337                     # fixed k-means seed -> reproducible clusters
KMEANS_K = 6                    # k=6 dominant colors
KMEANS_ITERS = 40
KMEANS_SAMPLE = 60000           # pixels sampled for k-means (deterministic stride)
QUANT_LEVELS = 16               # 16-level-per-channel quantization for flat-fill count
TILE = 8                        # 8x8 tiles for local-contrast uniformity
GRID_COLS, GRID_ROWS = 4, 3     # 4x3 layout grid

# Character color, copied from work/lib/stickman.py line 24.
SHIRT_RGB = (200, 50, 50)
SHIRT_TOL = 70.0                # Euclidean RGB distance tolerance for "shirt red"

# Frame geometry the reference and our renderer both use.
EXPECT_W, EXPECT_H = 1280, 720

# Character proportions from work/lib/stickman.py, used to scale the priors.
CHAR_H_FRAC = 110.0 / 720.0     # 0.153 of frame height
HEAD_R_FRAC = 14.0 / 110.0      # head radius as a fraction of figure height
CHAR_W_FRAC = 0.55 * CHAR_H_FRAC

HERE = os.path.dirname(os.path.abspath(__file__))
SEGMENTS = os.path.normpath(os.path.join(HERE, "..", "segments"))

DEFAULT_SUITE = [
    os.path.join(SEGMENTS, "hd188753", "critic_blind_r6"),
    os.path.join(SEGMENTS, "hd80606", "critic_blind_r6"),
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_rgb(path):
    """Open a PNG as an HxWx3 uint8 numpy array. Handles RGBA, L, P."""
    with Image.open(path) as im:
        im.load()
        if im.mode in ("RGBA", "LA"):
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, im.convert("RGBA"))
        arr = np.asarray(im.convert("RGB"), dtype=np.uint8)
    return arr


def _sample_evenly(flat, n):
    """Deterministic uniform subsample of a flat pixel array."""
    total = flat.shape[0]
    if total <= n:
        return flat
    idx = np.linspace(0, total - 1, n).astype(np.int64)
    return flat[idx]


# ---------------------------------------------------------------------------
# 1. dominant_colors — k-means (hand-rolled) + flat_fill_score
# ---------------------------------------------------------------------------

def kmeans_colors(pixels, k=KMEANS_K, iters=KMEANS_ITERS, seed=SEED):
    """
    Deterministic k-means over RGB pixels. Returns (centroids uint8, shares float).

    Init is k-means++ using a numpy Generator seeded with `seed`, so the whole
    thing is reproducible without depending on global random state.
    """
    rng = np.random.default_rng(seed)
    n = pixels.shape[0]
    k = min(k, n)

    # --- k-means++ seeding ---
    centers = np.empty((k, 3), dtype=np.float64)
    centers[0] = pixels[rng.integers(0, n)]
    closest = ((pixels - centers[0]) ** 2).sum(axis=1)
    for i in range(1, k):
        total = float(closest.sum())
        if total <= 0.0:
            centers[i] = pixels[rng.integers(0, n)]
        else:
            probs = closest / total
            centers[i] = pixels[rng.choice(n, p=probs)]
        d = ((pixels - centers[i]) ** 2).sum(axis=1)
        closest = np.minimum(closest, d)

    # --- Lloyd iterations ---
    labels = np.zeros(n, dtype=np.int32)
    for _ in range(iters):
        # (n, k) squared distances via expansion; n is <= KMEANS_SAMPLE so this
        # stays in the low tens of MB.
        d2 = (
            (pixels ** 2).sum(axis=1)[:, None]
            - 2.0 * pixels @ centers.T
            + (centers ** 2).sum(axis=1)[None, :]
        )
        new_labels = np.argmin(d2, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for i in range(k):
            member = pixels[labels == i]
            if member.size:
                centers[i] = member.mean(axis=0)

    counts = np.bincount(labels, minlength=k).astype(np.float64)
    # Empty clusters get a zero share; keep them so the palette width is honest.
    order = np.argsort(-counts)
    cents = np.clip(np.round(centers[order]), 0, 255).astype(np.uint8)
    shares = counts[order] / float(n)
    keep = shares > 0
    return cents[keep], shares[keep]


def _hexof(rgb):
    return "#%02x%02x%02x" % (int(rgb[0]), int(rgb[1]), int(rgb[2]))


def dominant_colors(arr, k=KMEANS_K):
    """
    Returns dict with:
      palette        : [{hex, rgb, share}] sorted by share desc
      palette_width  : number of non-empty clusters
      flat_fill_score: count of distinct 16-level-per-channel colors present
      distinct_ratio : flat_fill_score / (QUANT_LEVELS ** 3)
      entropy_bits   : Shannon entropy of the cluster shares (max log2(k))
    """
    h, w, _ = arr.shape
    flat = arr.reshape(-1, 3).astype(np.float64)
    sample = _sample_evenly(flat, KMEANS_SAMPLE)
    cents, shares = kmeans_colors(sample, k=k)

    # Distinct quantized colors over the FULL frame (not the sample) -- a cheap
    # unique() on the reduced-precision cube.
    q = (arr.astype(np.uint16) * QUANT_LEVELS // 256).astype(np.uint8)
    packed = (q[..., 0].astype(np.uint32) << 16) | (q[..., 1].astype(np.uint32) << 8) | q[..., 2]
    distinct = int(np.unique(packed).size)

    nz = shares[shares > 0]
    entropy = float(-(nz * np.log2(nz)).sum()) if nz.size else 0.0

    return {
        "palette": [
            {"hex": _hexof(c), "rgb": [int(c[0]), int(c[1]), int(c[2])], "share": round(float(s), 5)}
            for c, s in zip(cents, shares)
        ],
        "palette_width": int(cents.shape[0]),
        "flat_fill_score": distinct,
        "quant_levels": QUANT_LEVELS,
        "quant_space": QUANT_LEVELS ** 3,
        "distinct_ratio": round(distinct / float(QUANT_LEVELS ** 3), 6),
        "palette_entropy_bits": round(entropy, 4),
        "max_entropy_bits": round(math.log2(k), 4),
    }


# ---------------------------------------------------------------------------
# 2. edge_profile
# ---------------------------------------------------------------------------

def _sobel_mag(gray):
    """Plain 3x3 Sobel magnitude on a float array. No PIL filters, no smoothing."""
    a = gray.astype(np.float64)
    p = np.pad(a, 1, mode="edge")
    gx = (
        p[:-2, 2:] + 2.0 * p[1:-1, 2:] + p[2:, 2:]
        - p[:-2, :-2] - 2.0 * p[1:-1, :-2] - p[2:, :-2]
    )
    gy = (
        p[2:, :-2] + 2.0 * p[2:, 1:-1] + p[2:, 2:]
        - p[:-2, :-2] - 2.0 * p[:-2, 1:-1] - p[:-2, 2:]
    )
    return np.hypot(gx, gy) / 4.0  # ~0..255


def edge_profile(arr, rel_thresh=0.06):
    """
    Strong-edge detection on luma. The threshold is RELATIVE to each frame's own
    edge-magnitude distribution, so a dark frame and a bright frame are treated
    the same way. Without this, absolute thresholds silently measure exposure
    rather than structure.

    Returns per-row and per-column edge counts plus their summary stats and the
    fraction of pixels that are edge pixels.
    """
    h, w, _ = arr.shape
    luma = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
    mag = _sobel_mag(luma)

    # Robust relative threshold: mean + rel_thresh * std of the magnitude field.
    thr = float(mag.mean() + rel_thresh * mag.std())
    strong = mag > thr

    row_counts = strong.sum(axis=1).astype(np.float64)
    col_counts = strong.sum(axis=0).astype(np.float64)

    def stats(v):
        return {
            "mean": round(float(v.mean()), 3),
            "std": round(float(v.std()), 3),
            "max": int(v.max()),
            "min": int(v.min()),
        }

    return {
        "threshold": round(thr, 3),
        "row_edge_counts": stats(row_counts),
        "col_edge_counts": stats(col_counts),
        "edge_pixel_fraction": round(float(strong.mean()), 6),
        "edge_count_total": int(strong.sum()),
        # How much the edge density varies along the two axes. A sparse
        # hand-drawn frame concentrates edges into a few bands (high std/mean);
        # a photographic frame spreads them (low std/mean).
        "row_banding": round(float(row_counts.std() / max(row_counts.mean(), 1e-9)), 4),
        "col_banding": round(float(col_counts.std() / max(col_counts.mean(), 1e-9)), 4),
    }


# ---------------------------------------------------------------------------
# 3. anti_aliasing_proxy
# ---------------------------------------------------------------------------

def _hsv_from_rgb(arr):
    """Vectorized RGB->HSV. h in [0,1), s in [0,1], v in [0,1]."""
    a = arr.astype(np.float32) / 255.0
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    d = mx - mn
    h = np.zeros_like(mx)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    nz = d > 1e-6
    idx = nz & (mx == r)
    h[idx] = ((g[idx] - b[idx]) / d[idx]) % 6.0
    idx = nz & (mx == g)
    h[idx] = ((b[idx] - r[idx]) / d[idx]) + 2.0
    idx = nz & (mx == b)
    h[idx] = ((r[idx] - g[idx]) / d[idx]) + 4.0
    h = h / 6.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    return h, s, mx


def anti_aliasing_proxy(arr, cents=None, band=45.0, off_palette_l1=60):
    """
    Four tone-population measurements. The primary one is `off_palette_fraction`.

    * off_palette_fraction -- pixels more than `off_palette_l1` (L1 RGB distance)
      from EVERY k-means centroid. This is the honest anti-aliasing / gradient
      proxy: a frame built from six flat fills lands almost entirely on its own
      palette, so this is near zero. A photo, a smooth gradient or a
      anti-aliased stroke leaves a large tail of off-palette pixels. Unlike a
      "band between the top two colors" test it does not blow up when the two
      most dominant colors happen to be close in value.
    * intermediate_tone_fraction -- pixels in a narrow band between the two most
      dominant colors. Reported for continuity with the original spec, but it
      is a WEAK measure: when both dominant colors are light, the band is wide
      and low-contrast frames score high. Read it only alongside
      off_palette_fraction.
    * muted_fraction -- saturation < 0.20. Flat art on paper cream and pure ink
      is mostly desaturated; a lit planet render is not.
    * saturated_fraction -- saturation >= 0.60 AND value >= 0.25. Where the
      loud accents (the red shirt, an alarm-red planet) live.
    * luma_entropy_bits -- spread of the luma histogram. Flat art has few
      distinct tones; a graded render has many.
    """
    h, w, _ = arr.shape

    if cents is None:
        flat = arr.reshape(-1, 3).astype(np.float64)
        cents, _ = kmeans_colors(_sample_evenly(flat, KMEANS_SAMPLE), k=KMEANS_K)
    cents = np.asarray(cents, dtype=np.float64)
    if cents.shape[0] >= 2:
        c0, c1 = cents[0], cents[1]
    else:
        c0 = np.array([255.0, 255.0, 255.0])
        c1 = np.array([0.0, 0.0, 0.0])
    lo, hi = np.minimum(c0, c1), np.maximum(c0, c1)
    span = hi - lo
    mid = (lo + hi) / 2.0
    half = np.minimum(band, span / 2.0)
    near = np.all(np.abs(arr.astype(np.float64) - mid) <= half, axis=2)
    if (half <= 0).all():
        near = np.zeros((h, w), dtype=bool)

    # --- off-palette: distance to the NEAREST centroid, not the top two ---
    a32 = arr.astype(np.int32)
    dmin = np.full((h, w), 1 << 30, dtype=np.int32)
    for c in cents:
        d = np.abs(a32 - c.astype(np.int32)).sum(axis=2)
        np.minimum(dmin, d, out=dmin)

    hh, ss, vv = _hsv_from_rgb(arr)
    luma = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    hist = np.bincount(luma.astype(np.uint8).ravel(), minlength=256).astype(np.float64)
    p = hist[hist > 0] / hist.sum()
    luma_entropy = float(-(p * np.log2(p)).sum())

    return {
        "band_colors": [_hexof(c0), _hexof(c1)],
        "off_palette_l1_threshold": off_palette_l1,
        "off_palette_fraction": round(float((dmin > off_palette_l1).mean()), 6),
        "median_dist_to_palette_l1": float(np.median(dmin)),
        "p95_dist_to_palette_l1": float(np.percentile(dmin, 95)),
        "intermediate_tone_fraction": round(float(near.mean()), 6),
        "intermediate_tone_caveat": "weak measure; inflates when the top-2 colors are both light",
        "muted_fraction": round(float((ss < 0.20).mean()), 6),
        "saturated_fraction": round(float(((ss >= 0.60) & (vv >= 0.25)).mean()), 6),
        "mean_saturation": round(float(ss.mean()), 5),
        "mean_value": round(float(vv.mean()), 5),
        "luma_entropy_bits": round(luma_entropy, 4),
        "luma_max_entropy_bits": 8.0,
    }


# ---------------------------------------------------------------------------
# Connected components (hand-rolled iterative CCL, union-find)
# ---------------------------------------------------------------------------

def _row_runs(row):
    """Yield (start, end_inclusive) index pairs for each True run in a bool row."""
    idx = np.flatnonzero(np.diff(np.concatenate(([0], row.view(np.int8), [0]))))
    return zip(idx[0::2], idx[1::2] - 1)


def _vertical_edge_strength(gray):
    """Per-row fraction of columns carrying a strong vertical gradient.

    A horizontal line -- a horizon, a ground line, a header-band rule, a
    letter's crossbar -- produces a strong vertical gradient across many
    columns on the same rows. Returns (row_frac array H, mag array HxW).
    """
    a = gray.astype(np.float64)
    p = np.pad(a, 1, mode="edge")
    gy = (p[2:, :-2] + 2.0 * p[2:, 1:-1] + p[2:, 2:]
          - p[:-2, :-2] - 2.0 * p[:-2, 1:-1] - p[:-2, 2:]) / 4.0
    amag = np.abs(gy)
    thr = float(amag.mean() + 0.35 * amag.std())
    strong = amag > thr
    return strong.mean(axis=1), amag


def connected_components(mask):
    """
    Label an HxW boolean mask with 4-connectivity. Returns (labels int32 HxW, n).

    Classic run-based two-pass union-find:

      pass 1 -- scan rows top to bottom, split each row into maximal True runs.
      A run's candidate label is the label directly above its left end or its
      right end (or both, in which case the two are unioned). A run with neither
      gets a fresh label. Because a run's predecessor in the same row is
      background by construction, there is no left-neighbour case to handle.

      pass 2 -- flatten the union-find and relabel contiguously from 1.

    No recursion; a Python list for the parent array; O(H*W) label memory. Exact,
    not an approximation: verified against a brute-force BFS flood fill.
    """
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    parent = [0]                      # 0 is the background sentinel
    next_label = 1
    has_any = False

    prev = np.zeros(w, dtype=np.int32)
    for y in range(h):
        row = mask[y]
        if not row.any():
            prev = labels[y]
            continue
        has_any = True
        cur = np.zeros(w, dtype=np.int32)
        for x0, x1 in _row_runs(row):
            # Every non-background label in the run's span directly above is a
            # predecessor -- not just the two end pixels. A staggered shape can
            # have background above one end of the run and ink above its middle,
            # and taking only the ends would split one blob into two.
            seg = prev[x0:x1 + 1]
            cands = np.unique(seg[seg > 0])
            if cands.size == 0:
                lab = next_label
                parent.append(next_label)
                next_label += 1
            else:
                lab = int(cands[0])
                for other in cands[1:]:
                    _union(parent, lab, int(other))
            cur[x0:x1 + 1] = lab
        labels[y] = cur
        prev = cur

    if not has_any:
        return labels, 0

    parent_arr = np.array(parent, dtype=np.int64)
    _resolve_all(parent_arr)
    uniq, inv = np.unique(parent_arr[1:], return_inverse=True)
    remap = np.zeros(next_label, dtype=np.int32)
    remap[1:] = (inv + 1).astype(np.int32)
    return remap[labels].astype(np.int32), int(uniq.size)


def _find(parent, x):
    root = x
    while parent[root] != root:
        root = parent[root]
    while parent[x] != root:      # path compression
        parent[x], x = root, parent[x]
    return root


def _union(parent, a, b):
    ra, rb = _find(parent, a), _find(parent, b)
    if ra != rb:
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb


def _resolve_all(parent_arr):
    """Flatten the union-find path iteratively. No recursion, no mutation of i."""
    for i in range(1, parent_arr.shape[0]):
        r = i
        while parent_arr[r] != r:
            r = parent_arr[r]
        parent_arr[i] = r
    return parent_arr


def component_stats(labels, n_labels):
    """bbox, area and fill ratio for each label. Returns list of dicts, largest first.

    Fully vectorized: one pass builds the per-label pixel index, then numpy does
    the per-label min/max. Avoids the O(n_labels * npix) trap.
    """
    if n_labels == 0:
        return []
    h, w = labels.shape
    flat = labels.ravel()
    counts = np.bincount(flat, minlength=n_labels + 1)
    keep = min(n_labels, 400)
    order = np.argsort(-counts[1:])[:keep] + 1        # 400 largest is plenty

    ys_all, xs_all = np.nonzero(labels)
    lab_all = labels[ys_all, xs_all]
    out = []
    for lab in order:
        sel = lab_all == lab
        if not sel.any():
            continue
        ys = ys_all[sel]
        xs = xs_all[sel]
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        area = int(sel.sum())
        bbox_area = max((y1 - y0 + 1) * (x1 - x0 + 1), 1)
        out.append({
            "label": int(lab),
            "area": area,
            "bbox": [x0, y0, x1, y1],
            "w": x1 - x0 + 1,
            "h": y1 - y0 + 1,
            "fill_ratio": round(area / bbox_area, 5),
        })
    return out


# ---------------------------------------------------------------------------
# 4. stickman_detection
# ---------------------------------------------------------------------------

def _largest_blob(ccs):
    return ccs[0] if ccs else None


def stickman_detection(arr, shirt_rgb=SHIRT_RGB, shirt_tol=SHIRT_TOL):
    """
    Heuristic search for the recurring stick figure.

    Three independent pieces of evidence, combined with stated priors:

      (a) RED  -- pixels within `shirt_tol` Euclidean RGB of SHIRT_RGB.
                  Plausibility gates: the patch must be a plausible shirt
                  (2%..30% of frame area) and roughly 1.6..7x wider than tall
                  (a torso), plus roughly convex (solidity-like check via
                  fill_ratio >= 0.55).
      (b) DARK -- the largest connected near-black component with a LOW fill
                  ratio. A line drawing has fill_ratio well under 1; a filled
                  black shape has fill_ratio near 1. This is the same
                  component the stickman's limbs, head outline and eyes live in.
      (c) GEOMETRY -- the red patch's bbox sits in the upper part of the dark
                  component's bbox, and horizontally inside it.

    Returns every intermediate number so a reader can disagree with the verdict.
    """
    h, w, _ = arr.shape
    total = float(h * w)
    a = arr.astype(np.float64)

    # --- (a) shirt red ---
    d = np.sqrt(((a - np.array(shirt_rgb, dtype=np.float64)) ** 2).sum(axis=2))
    red_mask = d <= shirt_tol
    red_frac = float(red_mask.mean())
    rlab, rn = connected_components(red_mask)
    rccs = [c for c in component_stats(rlab, rn) if c["area"] >= 200]
    red_blob = rlab  # kept for geometry
    red = _largest_blob(rccs)
    red_ok = False
    red_report = {
        "target_rgb": list(shirt_rgb),
        "tolerance": shirt_tol,
        "pixel_count": int(red_mask.sum()),
        "frame_fraction": round(red_frac, 6),
        "largest_component": red,
        "n_components_over_200px": len(rccs),
    }
    if red is not None:
        ar = red["area"] / total
        wh = red["w"] / max(red["h"], 1)
        red_ok = (0.02 <= ar <= 0.30) and (1.6 <= wh <= 7.0) and (red["fill_ratio"] >= 0.55)
        red_report.update({
            "area_fraction": round(ar, 6),
            "w_over_h": round(wh, 3),
            "fill_ratio": red["fill_ratio"],
            "plausible_torso": bool(red_ok),
        })

    # --- (b) dark line-drawing region ---
    v = a.max(axis=2)
    s = (a.max(axis=2) - a.min(axis=2)) / np.maximum(a.max(axis=2), 1.0)
    dark_mask = (v <= 70) & (s <= 0.55)
    dlab, dn = connected_components(dark_mask)
    dccs = [c for c in component_stats(dlab, dn) if c["area"] >= 150]
    thin = [c for c in dccs if c["fill_ratio"] <= 0.45]
    thin.sort(key=lambda c: -c["area"])
    dark = thin[0] if thin else None
    dark_report = {
        "dark_mask_fraction": round(float(dark_mask.mean()), 6),
        "n_components_over_150px": len(dccs),
        "n_thin_components": len(thin),
        "largest_thin": dark,
        "fill_ratio_cut": 0.45,
    }

    # --- (c) geometry ---
    geo = {"red_above_dark": None, "dx_within_dark": None, "overlap_y": None}
    geo_ok = False
    if red is not None and dark is not None:
        rx0, ry0, rx1, ry1 = red["bbox"]
        dx0, dy0, dx1, dy1 = dark["bbox"]
        red_cy = (ry0 + ry1) / 2.0
        dark_cy = (dy0 + dy1) / 2.0
        red_cx = (rx0 + rx1) / 2.0
        dark_cx = (dx0 + dx1) / 2.0
        dx = abs(red_cx - dark_cx)
        inside_x = dx <= (dark["w"] / 2.0)
        above_or_overlap = red_cy <= dy1
        oy = max(0, min(ry1, dy1) - max(ry0, dy0) + 1)
        geo = {
            "red_center": [round(red_cx, 1), round(red_cy, 1)],
            "dark_center": [round(dark_cx, 1), round(dark_cy, 1)],
            "dark_bbox_h": dark["h"],
            "dark_vertical_extent": round(float(abs(ry1 - ry0) / max(dark["h"], 1)), 3),
            "red_above_dark": bool(above_or_overlap),
            "dx_within_dark": bool(inside_x),
            "overlap_y": int(oy),
        }
        geo_ok = bool(above_or_overlap and inside_x)

    # --- priors on size, from work/lib/stickman.py proportions ---
    size_ok = False
    size_report = {}
    if dark is not None:
        dh, dw = dark["h"], dark["w"]
        dh_f, dw_f = dh / h, dw / w
        dh_lo, dh_hi = 0.4 * CHAR_H_FRAC, 4.0 * CHAR_H_FRAC
        dw_lo, dw_hi = 0.4 * CHAR_W_FRAC, 5.0 * CHAR_W_FRAC
        size_ok = (dh_lo <= dh_f <= dh_hi) and (dw_lo <= dw_f <= dw_hi)
        size_report = {
            "dark_h_frac": round(dh_f, 5),
            "dark_w_frac": round(dw_f, 5),
            "expected_h_frac_window": [round(dh_lo, 5), round(dh_hi, 5)],
            "expected_w_frac_window": [round(dw_lo, 5), round(dw_hi, 5)],
            "char_h_frac_prior": round(CHAR_H_FRAC, 5),
            "size_plausible": bool(size_ok),
        }

    likely = bool(red_ok and dark is not None and geo_ok and size_ok)
    return {
        "stickman_likely": likely,
        "evidence": {"red": red_ok, "dark_present": dark is not None,
                     "geometry": geo_ok, "size": size_ok},
        "red": red_report,
        "dark": dark_report,
        "geometry": geo,
        "size": size_report,
    }


# ---------------------------------------------------------------------------
# 5. layout_metrics
# ---------------------------------------------------------------------------

def layout_metrics(arr, cents):
    """
    4x3 ink-coverage grid, vertical centroid of ink, and a horizon test.

    Background = the single most dominant cluster (the paper/void color).
    Ink = everything else. A centered-diagram frame puts its mass in the middle
    row; a scene-with-ground frame puts mass in the bottom row with a hard
    horizontal break between them.
    """
    h, w, _ = arr.shape
    bg = np.array(cents[0], dtype=np.int64)
    dist = np.abs(arr.astype(np.int64) - bg).sum(axis=2)
    ink = dist > 30                      # anything meaningfully not background

    ys, xs = np.nonzero(ink)
    total_ink = float(ink.sum())
    if total_ink == 0:
        v_centroid, h_centroid = 0.5, 0.5
    else:
        v_centroid = float(ys.mean()) / h
        h_centroid = float(xs.mean()) / w

    grid = []
    for r in range(GRID_ROWS):
        row = []
        for c in range(GRID_COLS):
            y0, y1 = r * h // GRID_ROWS, (r + 1) * h // GRID_ROWS
            x0, x1 = c * w // GRID_COLS, (c + 1) * w // GRID_COLS
            cell = ink[y0:y1, x0:x1]
            row.append(round(float(cell.mean()), 5))
        grid.append(row)

    # --- horizon test.
    # A horizon is a horizontal boundary that SPANS the frame: many columns
    # simultaneously show a strong vertical gradient, sustained across a small
    # band of rows. That is a different (and much more specific) signal than
    # "row y has more edges than row y-4" -- that one fires on any band change
    # and on the bottom edge of the frame, and produced a false positive on
    # every single frame in the first version of this function.
    #
    # `width_coverage` is ALWAYS reported. `horizon_detected` is only True when
    # the peak clears 60% of the width AND 2x the frame's own baseline. On the
    # 22 blind frames measured so far the peak coverage never exceeded 0.47, so
    # no horizon was detected in ANY of them -- that is a measurement of the
    # frames, not a failure of the test.
    gray = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    vfrac, _ = _vertical_edge_strength(gray)
    k = max(3, h // 120)                       # small sustained band
    vs = np.convolve(vfrac, np.ones(k) / k, mode="same")
    peak = int(np.argmax(vs))
    span = float(vfrac[max(0, peak - k):peak + k + 1].mean())
    global_v = float(vfrac.mean())
    detected = bool(span >= 0.60 and span >= 2.0 * max(global_v, 1e-9))
    horizon = {
        "detected": detected,
        "row": peak,
        "row_frac": round(peak / h, 4),
        "width_coverage": round(span, 4),
        "global_width_coverage": round(global_v, 4),
        "coverage_ratio": round(span / max(global_v, 1e-9), 2),
        "criterion": "width_coverage >= 0.60 AND >= 2x frame baseline",
    }

    top = sum(grid[0]); mid = sum(grid[1]); bot = sum(grid[2])
    return {
        "background_hex": _hexof(np.array(cents[0])),
        "ink_fraction": round(total_ink / (h * w), 5),
        "ink_grid_4x3": grid,
        "ink_grid_note": "rows top->bottom, 4 cols; fraction of non-background pixels per cell",
        "band_mass": {"top": round(top, 4), "middle": round(mid, 4), "bottom": round(bot, 4)},
        "v_centroid": round(v_centroid, 5),
        "h_centroid": round(h_centroid, 5),
        "horizon": horizon,
    }


# ---------------------------------------------------------------------------
# 6. type_metrics
# ---------------------------------------------------------------------------

def type_metrics(arr, cents, min_h_frac=0.04, max_run_h_frac=0.25,
                 min_area=120, max_w_over_h=0.8):
    """
    Approximate "how much type is on screen, and is the scale consistent."

    This is NOT OCR. It counts blocks and measures their height distribution.
    It never reads a character.

    Pipeline:
      1. Binarize against the dominant background (L1 distance > 60).
      2. Connected components; drop specks below `min_area`.
      3. Exclude BLOBS. A filled circle, a planet disc or a solid shape has a
         high fill ratio. A run of text has a fill ratio around 0.3-0.6 because
         the whitespace between and inside glyphs is excluded. Components with
         fill_ratio >= 0.75 are dropped, which is what stops a 307px planet
         portrait from being counted as a 307px letter.
      4. What survives is grouped into text-like blocks (single glyphs, or
         words whose glyphs are bridged by anti-aliasing). Each block is
         re-measured for height using the MEDIAN run height inside its bbox.
         Run height is the right measure: a word box is only as tall as its
         lowercase-plus-cap height, and is often much wider than tall, so
         measuring the bbox would report every word at 3x its true type size.
      5. Exclude OVERSIZED blocks. Nothing in a 720p explainer frame is a
         180px-tall letter (the 72pt header is ~96px), so a block whose median
         run height exceeds 25% of frame height is a drawing, not type. This is
         a hard cap, not a soft prior, and the rejected count is reported.

    `type_scale_px` is the headline number: the median run height of the
    type-like blocks, directly comparable to a point size.
    """
    h, w, _ = arr.shape
    bg = np.array(cents[0], dtype=np.int64)
    dist = np.abs(arr.astype(np.int64) - bg).sum(axis=2)
    fg = dist > 60

    lab, n = connected_components(fg)
    ccs = [c for c in component_stats(lab, n) if c["area"] >= min_area]
    min_h = min_h_frac * h
    max_run_h = max_run_h_frac * h
    ccs = [c for c in ccs if c["h"] >= min_h]
    # --- blob rejection ---
    ink_like = [c for c in ccs if c["fill_ratio"] < 0.75]

    def median_run_height(bbox):
        x0, y0, x1, y1 = bbox
        sub = fg[y0:y1 + 1, x0:x1 + 1]
        heights = [e - s + 1 for s, e in _row_runs(sub.any(axis=1))]
        return float(np.median(heights)) if heights else 0.0

    blocks, oversized = [], []
    for c in ink_like:
        rh = median_run_height(c["bbox"])
        if rh < 8 or rh > max_run_h:
            if rh > max_run_h:
                oversized.append({"bbox": c["bbox"], "run_h": int(round(rh))})
            continue
        if c["w"] / max(rh, 1) <= max_w_over_h:
            blocks.append({"bbox": c["bbox"], "area": c["area"],
                           "w": c["w"], "h": c["h"],
                           "run_h": int(round(rh)),
                           "w_over_run_h": round(c["w"] / max(rh, 1), 3)})

    runs = np.array([b["run_h"] for b in blocks], dtype=np.float64)
    if runs.size == 0:
        summary = {
            "count": 0, "type_scale_px": None, "type_scale_px_cv": None,
            "run_h_min": None, "run_h_median": None, "run_h_max": None,
            "run_h_iqr": None, "area_fraction_of_type": 0.0,
        }
        dist_hist = {}
    else:
        summary = {
            "count": int(runs.size),
            "type_scale_px": int(round(float(np.median(runs)))),
            # CV of the per-block run height. A locked type scale gives a tight
            # distribution; per-card ad-hoc sizing gives a wide one. This is the
            # closest available proxy for the "type scale drift" problem in
            # CLAUDE.md section 4. Note it is computed WITHIN one frame, so it
            # measures intra-frame consistency; cross-frame drift must be
            # compared by hand across the type_scale_px values.
            "type_scale_px_cv": round(float(runs.std() / max(runs.mean(), 1e-9)), 4),
            "run_h_min": int(runs.min()),
            "run_h_median": int(round(float(np.median(runs)))),
            "run_h_max": int(runs.max()),
            "run_h_iqr": int(np.percentile(runs, 75) - np.percentile(runs, 25)),
            "area_fraction_of_type": round(
                float(sum(b["area"] for b in blocks)) / (h * w), 5),
        }
        hist, edges = np.histogram(runs, bins=8)
        dist_hist = {f"{int(edges[i])}-{int(edges[i+1])}px": int(hist[i]) for i in range(len(hist))}

    return {
        "min_height_px": int(min_h),
        "max_run_height_px": int(max_run_h),
        "min_area_px": min_area,
        "blob_fill_ratio_cut": 0.75,
        "n_components_ge_min_area": len(ccs),
        "n_rejected_as_blobs": len(ccs) - len(ink_like),
        "n_rejected_as_oversized": len(oversized),
        "oversized_rejected": oversized[:6],
        "n_type_like": summary,
        "type_block_detail": blocks[:12],
        "type_height_histogram": dist_hist,
    }


# ---------------------------------------------------------------------------
# 7. texture_uniformity
# ---------------------------------------------------------------------------

def texture_uniformity(arr, tile=TILE):
    """
    Std-dev of local contrast across non-flat tiles, and its coefficient of
    variation. Stipple, hatching and painterly noise raise local variance AND
    raise the CV (because the variance becomes uneven across the frame). Large
    flat color fields give a near-zero mean.
    """
    h, w, _ = arr.shape
    luma = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]).astype(np.float64)
    th, tw = h // tile, w // tile
    crop = luma[:th * tile, :tw * tile]
    blocks = crop.reshape(th, tile, tw, tile).transpose(0, 2, 1, 3).reshape(th * tw, tile * tile)
    local_std = blocks.std(axis=1)
    # A tile whose whole 8x8 is one flat color has no texture at all.
    textured = local_std[local_std > 1.0]
    if textured.size == 0:
        return {
            "tile": tile, "n_tiles": int(th * tw),
            "mean_local_std": 0.0, "std_local_std": 0.0, "cv_local_std": 0.0,
            "n_textured_tiles": 0, "textured_tile_fraction": 0.0,
        }
    return {
        "tile": tile,
        "n_tiles": int(th * tw),
        "mean_local_std": round(float(textured.mean()), 4),
        "std_local_std": round(float(textured.std()), 4),
        "cv_local_std": round(float(textured.std() / max(textured.mean(), 1e-9)), 4),
        "n_textured_tiles": int(textured.size),
        "textured_tile_fraction": round(float(textured.size) / (th * tw), 5),
    }


# ---------------------------------------------------------------------------
# Top-level measure()
# ---------------------------------------------------------------------------

def measure(path, verbose=False):
    """Run every measurement over one PNG. Returns a plain dict."""
    arr = load_rgb(path)
    h, w, _ = arr.shape

    dom = dominant_colors(arr)
    cents = np.array([[p["rgb"][0], p["rgb"][1], p["rgb"][2]] for p in dom["palette"]], dtype=np.uint8)

    out = {
        "path": path,
        "basename": os.path.basename(path),
        "size": [w, h],
        "aspect_ok": abs((w / h) - (EXPECT_W / EXPECT_H)) < 0.01,
        "dominant_colors": dom,
        "edge_profile": edge_profile(arr),
        "anti_aliasing_proxy": anti_aliasing_proxy(arr, cents=cents),
        "stickman_detection": stickman_detection(arr),
        "layout_metrics": layout_metrics(arr, cents),
        "type_metrics": type_metrics(arr, cents),
        "texture_uniformity": texture_uniformity(arr),
    }
    if verbose:
        print(f"  {os.path.basename(path)}  {w}x{h}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------
# compare() — side-by-side diff + conservative heuristic rules. NO WINNER.
# ---------------------------------------------------------------------------

# (key_path, label, direction) -- direction says which way is "more X".
_RULE_SPECS = [
    (("dominant_colors", "flat_fill_score"), "distinct_colors", "lower"),
    (("dominant_colors", "palette_entropy_bits"), "palette_entropy", "lower"),
    (("edge_profile", "edge_pixel_fraction"), "edge_density", "lower"),
    (("edge_profile", "row_banding"), "row_edge_concentration", "higher"),
    (("anti_aliasing_proxy", "off_palette_fraction"), "off_palette_pixels", "lower"),
    (("anti_aliasing_proxy", "intermediate_tone_fraction"), "intermediate_tones", "lower"),
    (("anti_aliasing_proxy", "muted_fraction"), "muted_pixels", "higher"),
    (("anti_aliasing_proxy", "luma_entropy_bits"), "luma_tones", "lower"),
    (("layout_metrics", "v_centroid"), "ink_v_centroid", "none"),
    (("layout_metrics", "horizon", "width_coverage"), "horizon_width_coverage", "higher"),
    (("layout_metrics", "horizon", "detected"), "horizon_detected", "higher"),
    (("type_metrics", "n_type_like", "type_scale_px"), "type_scale_px", "none"),
    (("type_metrics", "n_type_like", "count"), "type_block_count", "none"),
    (("texture_uniformity", "cv_local_std"), "local_variance_cv", "higher"),
    (("stickman_detection", "stickman_likely"), "stickman_detected", "higher"),
]


def _dig(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def compare(a_path, b_path):
    """
    Structured A-vs-B feature diff plus a list of conservative observations.

    DELIBERATELY EMITS NO WINNER, NO SCORE, AND NO RANKING. Every rule is
    phrased as "<measured fact> => <plain-language observation>". Deciding what
    the numbers mean is the critic's job.
    """
    a = measure(a_path)
    b = measure(b_path)

    metrics = {}
    for spec in _RULE_SPECS:
        path, key, direction = spec[0], spec[1], spec[2]
        va, vb = _dig(a, path), _dig(b, path)
        entry = {"a": va, "b": vb, "more_is": direction}
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            denom = max(abs(float(va)), abs(float(vb)), 1e-9)
            entry["abs_delta"] = round(float(vb) - float(va), 6)
            entry["rel_delta"] = round((float(vb) - float(va)) / denom, 4)
        metrics[key] = entry

    rules = _apply_rules(a, b, metrics)
    return {
        "a": a,
        "b": b,
        "diff": metrics,
        "observations": rules,
        "note": (
            "HEURISTIC OBSERVATIONS ONLY -- no winner is computed and none "
            "should be inferred. Pixel statistics measure structure, not craft."
        ),
    }


def _apply_rules(a, b, m):
    out = []

    def add(key, text):
        out.append({"metric": key, "observation": text})

    # 1. Flat-fill / hand-drawn-ness.
    fa, fb = m["distinct_colors"]["a"], m["distinct_colors"]["b"]
    if fa and fb:
        lo, hi = (fa, fb) if fa <= fb else (fb, fa)
        side = "A" if fa <= fb else "B"
        add("distinct_colors",
            f"{side} has fewer distinct quantized colors ({lo} vs {hi}) "
            f"=> more flat-fill / more hand-drawn")
    ea, eb = m["edge_density"]["a"], m["edge_density"]["b"]
    if ea is not None and eb is not None and abs(ea - eb) > 1e-4:
        side = "A" if ea < eb else "B"
        add("edge_density",
            f"{side} has lower strong-edge density ({min(ea, eb):.4f} vs {max(ea, eb):.4f}) "
            f"=> sparser linework")
    oa, ob = m["off_palette_pixels"]["a"], m["off_palette_pixels"]["b"]
    if oa is not None and ob is not None and abs(oa - ob) > 1e-4:
        side = "A" if oa < ob else "B"
        add("off_palette_pixels",
            f"{side} has fewer off-palette pixels ({min(oa, ob):.4f} vs {max(oa, ob):.4f}) "
            f"=> less anti-aliasing / fewer gradients; pixels land on its own palette")
    ia, ib = m["intermediate_tones"]["a"], m["intermediate_tones"]["b"]
    if ia is not None and ib is not None and abs(ia - ib) > 1e-4:
        side = "A" if ia < ib else "B"
        add("intermediate_tones",
            f"{side} has fewer intermediate-tone pixels ({min(ia, ib):.4f} vs {max(ia, ib):.4f}) "
            f"=> WEAK measure, see caveat; prefer off_palette_pixels")
    ra, rb = m["row_edge_concentration"]["a"], m["row_edge_concentration"]["b"]
    if ra is not None and rb is not None and abs(ra - rb) > 1e-3:
        side = "A" if ra > rb else "B"
        add("row_edge_concentration",
            f"{side} concentrates its edges into fewer row bands (CV {max(ra, rb):.3f} vs {min(ra, rb):.3f}) "
            f"=> more banded, poster-like composition")

    # 2. Palette.
    la, lb = m["luma_tones"]["a"], m["luma_tones"]["b"]
    if la is not None and lb is not None:
        side = "A" if la < lb else "B"
        add("luma_tones",
            f"{side} uses fewer distinct luma tones ({min(la, lb):.2f} vs {max(la, lb):.2f} bits) "
            f"=> flatter tonal range")

    # 3. Layout.
    va, vb = m["ink_v_centroid"]["a"], m["ink_v_centroid"]["b"]
    if va is not None and vb is not None:
        if abs(va - vb) > 0.04:
            side = "A" if va > vb else "B"
            add("ink_v_centroid",
                f"{side} sits its visual mass lower (v-centroid {max(va, vb):.3f} vs {min(va, vb):.3f}; 0.5=center, 1.0=bottom) "
                f"=> more scene-with-ground, less centered-diagram")
    ha, hb = a["layout_metrics"]["horizon"], b["layout_metrics"]["horizon"]
    add("horizon_row",
        f"strongest full-width horizontal band: A at row_frac {ha['row_frac']} covering "
        f"{ha['width_coverage']*100:.0f}% of width, B at row_frac {hb['row_frac']} covering "
        f"{hb['width_coverage']*100:.0f}% => horizon_detected A={ha['detected']}, B={hb['detected']} "
        f"(needs >=60% of width AND >=2x the frame's own baseline)")
    ba, bb = a["layout_metrics"]["band_mass"], b["layout_metrics"]["band_mass"]
    add("band_mass",
        f"ink by third -- A top/mid/bottom = {ba['top']:.3f}/{ba['middle']:.3f}/{ba['bottom']:.3f}, "
        f"B = {bb['top']:.3f}/{bb['middle']:.3f}/{bb['bottom']:.3f}")

    # 4. Type.
    ta = a["type_metrics"]["n_type_like"]["count"]
    tb = b["type_metrics"]["n_type_like"]["count"]
    sa_ = a["type_metrics"]["n_type_like"]["type_scale_px"]
    sb_ = b["type_metrics"]["n_type_like"]["type_scale_px"]
    add("type_block_count", f"type-like blocks: A={ta}, B={tb} => proxy for 'how much type is on screen'")
    add("type_scale_px",
        f"median glyph run height: A={sa_}px, B={sb_}px => apparent type size; "
        f"cross-frame, a drifting value is the CLAUDE.md section 4 type-scale-drift problem")
    cva = a["type_metrics"]["n_type_like"]["type_scale_px_cv"]
    cvb = b["type_metrics"]["n_type_like"]["type_scale_px_cv"]
    if cva is not None and cvb is not None:
        side = "A" if cva < cvb else "B"
        add("type_height_cv",
            f"{side} has a tighter glyph-height distribution within the frame "
            f"(CV {min(cva, cvb):.3f} vs {max(cva, cvb):.3f}) => more consistent apparent type scale")
    else:
        add("type_height_cv", f"type-height CV unavailable (A={cva}, B={cvb}) => too few type blocks to judge scale")

    # 5. Texture.
    ua, ub = m["local_variance_cv"]["a"], m["local_variance_cv"]["b"]
    if ua is not None and ub is not None and abs(ua - ub) > 1e-3:
        side = "A" if ua > ub else "B"
        add("local_variance_cv",
            f"{side} has more uneven local texture (CV {max(ua, ub):.3f} vs {min(ua, ub):.3f}) "
            f"=> more painterly / stippled surface")

    # 6. Character.
    sa = a["stickman_detection"]["stickman_likely"]
    sb = b["stickman_detection"]["stickman_likely"]
    add("stickman_detected",
        f"heuristic stick-figure detection: A={sa}, B={sb} => a FALSE POSITIVE here is likely "
        f"(any torso-sized saturated red above a thin dark region trips it); a FALSE NEGATIVE is "
        f"likely if the shirt is desaturated, scaled small, or the frame crops the figure")

    for r in out:
        r["heuristic"] = True
    return out


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def _fmt(v, nd=4):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def print_pair_report(result, pair_name, a_name="A", b_name="B"):
    a, b, obs = result["a"], result["b"], result["observations"]
    print(f"\n{'='*100}\n{pair_name}   ({a_name} = {a['basename']}  |  {b_name} = {b['basename']})\n{'='*100}")

    print(f"{'metric':<38} {a_name:>26} {b_name:>26}")
    print("-" * 100)
    rows = [
        ("dominant_colors.flat_fill_score", a["dominant_colors"]["flat_fill_score"], b["dominant_colors"]["flat_fill_score"], 0),
        ("dominant_colors.palette_entropy_bits", a["dominant_colors"]["palette_entropy_bits"], b["dominant_colors"]["palette_entropy_bits"], 3),
        ("edge_profile.edge_pixel_fraction", a["edge_profile"]["edge_pixel_fraction"], b["edge_profile"]["edge_pixel_fraction"], 5),
        ("edge_profile.row_edge_counts.mean", a["edge_profile"]["row_edge_counts"]["mean"], b["edge_profile"]["row_edge_counts"]["mean"], 2),
        ("edge_profile.row_edge_counts.std", a["edge_profile"]["row_edge_counts"]["std"], b["edge_profile"]["row_edge_counts"]["std"], 2),
        ("edge_profile.col_edge_counts.mean", a["edge_profile"]["col_edge_counts"]["mean"], b["edge_profile"]["col_edge_counts"]["mean"], 2),
        ("edge_profile.row_banding", a["edge_profile"]["row_banding"], b["edge_profile"]["row_banding"], 3),
        ("aa.off_palette_fraction", a["anti_aliasing_proxy"]["off_palette_fraction"], b["anti_aliasing_proxy"]["off_palette_fraction"], 5),
        ("aa.intermediate_tone_fraction", a["anti_aliasing_proxy"]["intermediate_tone_fraction"], b["anti_aliasing_proxy"]["intermediate_tone_fraction"], 5),
        ("aa.muted_fraction", a["anti_aliasing_proxy"]["muted_fraction"], b["anti_aliasing_proxy"]["muted_fraction"], 5),
        ("aa.saturated_fraction", a["anti_aliasing_proxy"]["saturated_fraction"], b["anti_aliasing_proxy"]["saturated_fraction"], 5),
        ("aa.luma_entropy_bits", a["anti_aliasing_proxy"]["luma_entropy_bits"], b["anti_aliasing_proxy"]["luma_entropy_bits"], 3),
        ("layout.ink_fraction", a["layout_metrics"]["ink_fraction"], b["layout_metrics"]["ink_fraction"], 5),
        ("layout.v_centroid", a["layout_metrics"]["v_centroid"], b["layout_metrics"]["v_centroid"], 4),
        ("layout.h_centroid", a["layout_metrics"]["h_centroid"], b["layout_metrics"]["h_centroid"], 4),
        ("layout.horizon_detected", str(a["layout_metrics"]["horizon"]["detected"]), str(b["layout_metrics"]["horizon"]["detected"]), None),
        ("layout.horizon_cover", a["layout_metrics"]["horizon"]["width_coverage"], b["layout_metrics"]["horizon"]["width_coverage"], 4),
        ("layout.horizon_row_frac", a["layout_metrics"]["horizon"]["row_frac"], b["layout_metrics"]["horizon"]["row_frac"], 4),
        ("type.block_count", a["type_metrics"]["n_type_like"]["count"], b["type_metrics"]["n_type_like"]["count"], 0),
        ("type.type_scale_px", a["type_metrics"]["n_type_like"]["type_scale_px"], b["type_metrics"]["n_type_like"]["type_scale_px"], 0),
        ("type.run_h_cv", a["type_metrics"]["n_type_like"]["type_scale_px_cv"], b["type_metrics"]["n_type_like"]["type_scale_px_cv"], 3),
        ("type.rejected_blobs", a["type_metrics"]["n_rejected_as_blobs"], b["type_metrics"]["n_rejected_as_blobs"], 0),
        ("texture.mean_local_std", a["texture_uniformity"]["mean_local_std"], b["texture_uniformity"]["mean_local_std"], 3),
        ("texture.cv_local_std", a["texture_uniformity"]["cv_local_std"], b["texture_uniformity"]["cv_local_std"], 3),
        ("stickman.stickman_likely", str(a["stickman_detection"]["stickman_likely"]), str(b["stickman_detection"]["stickman_likely"]), None),
        ("stickman.red.frame_fraction", a["stickman_detection"]["red"]["frame_fraction"], b["stickman_detection"]["red"]["frame_fraction"], 5),
    ]
    for name, va, vb, nd in rows:
        print(f"{name:<38} {_fmt(va, nd or 0):>26} {_fmt(vb, nd or 0):>26}")

    for side, m in ((a_name, a), (b_name, b)):
        lm = m["layout_metrics"]
        print(f"\n  {side} ink grid 4x3 (rows top->bottom), background {lm['background_hex']}:")
        for r in lm["ink_grid_4x3"]:
            print("      " + "  ".join(f"{v:.3f}" for v in r))
        print(f"  {side} palette: " + "  ".join(
            f"{p['hex']} {p['share']*100:.1f}%" for p in m["dominant_colors"]["palette"]))

    print(f"\n  {a_name} type-height histogram: {a['type_metrics']['type_height_histogram']}")
    print(f"  {b_name} type-height histogram: {b['type_metrics']['type_height_histogram']}")

    print(f"\n  HEURISTIC OBSERVATIONS (no winner implied):")
    for o in obs:
        print(f"    - [{o['metric']}] {o['observation']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def discover_pairs(dirs):
    import glob
    pairs = []
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "pair_*_*.png"))):
            base = os.path.basename(f)
            stem, side = base[:-4].rsplit("_", 1)
            pairs.append((os.path.join(d, base), stem, side))
    return pairs


def run_suite(dirs, emit_json=None):
    import collections
    by_dir = collections.OrderedDict()
    for full, stem, side in discover_pairs(dirs):
        by_dir.setdefault(os.path.dirname(full), []).append((full, stem, side))

    all_results = {}
    for d, entries in by_dir.items():
        # Key on the SEGMENT name, not the leaf dir: both blind dirs are called
        # "critic_blind_r6", so the leaf alone would collide and silently drop
        # one segment's results.
        seg = os.path.basename(os.path.dirname(os.path.normpath(d)))
        stems = sorted({s for _, s, _ in entries}, key=lambda s: int(s.split("_")[1]))
        print(f"\n\n{'#'*100}\n# {d}\n{'#'*100}")
        for stem in stems:
            fa = next((f for f, s, sd in entries if s == stem and sd == "A"), None)
            fb = next((f for f, s, sd in entries if s == stem and sd == "B"), None)
            if not (fa and fb):
                print(f"\n!! {stem}: missing A or B, skipped")
                continue
            res = compare(fa, fb)
            all_results[f"{seg}/{stem}"] = res
            print_pair_report(res, stem)

    if emit_json:
        with open(emit_json, "w", encoding="utf-8") as fh:
            json.dump(all_results, fh, indent=2, default=str)
        print(f"\nJSON written to {emit_json}")
    return all_results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[3],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="*", help="PNG paths to measure")
    ap.add_argument("--cmp", nargs=2, metavar=("A", "B"), help="compare two PNGs")
    ap.add_argument("--dir", action="append", help="add a critic_blind dir to the suite")
    ap.add_argument("--json", help="write full results as JSON")
    args = ap.parse_args(argv)

    if args.cmp:
        print_pair_report(compare(args.cmp[0], args.cmp[1]), "comparison")
        return 0

    if args.images:
        for p in args.images:
            m = measure(p)
            print(f"\n=== {p} ({m['size'][0]}x{m['size'][1]}) ===")
            print(json.dumps(m, indent=2, default=str))
        return 0

    dirs = args.dir or DEFAULT_SUITE
    dirs = [d for d in dirs if os.path.isdir(d)]
    if not dirs:
        print("No critic_blind directories found.", file=sys.stderr)
        return 1
    print("measure_frames.py -- non-vision feature extraction")
    print("NO WINNER IS COMPUTED ANYWHERE IN THIS TOOL.")
    print("Every number below is measured from pixels. Interpretations are heuristics.")
    run_suite(dirs, emit_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
