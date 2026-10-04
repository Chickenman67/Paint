#!/usr/bin/env python3
"""Measure card layout template from reference frames."""
from PIL import Image
import numpy as np
import os
import json
import sys

REF_DIR = r"work/ref"
OUT_JSON = r"work/ref/card_measurements.json"

def sample_bg(img, samples=None):
    if samples is None:
        # 4 corners + center
        w, h = img.size
        samples = [(5,5), (w-6,5), (5,h-6), (w-6,h-6), (w//2, h//2)]
    return [img.getpixel(p) for p in samples]

def dominant_bg(img, n=5):
    """Return top-N most common colors in a thin border band."""
    w, h = img.size
    arr = np.array(img)
    # Use 8px border for sampling
    border = np.concatenate([
        arr[0:8, :].reshape(-1, 3),
        arr[-8:, :].reshape(-1, 3),
        arr[:, 0:8].reshape(-1, 3),
        arr[:, -8:].reshape(-1, 3),
    ])
    # Round to nearest 8 for binning
    rounded = (border // 16) * 16
    from collections import Counter
    cnt = Counter(map(tuple, rounded))
    return cnt.most_common(n)

def find_text_rows(arr, threshold=80, min_run=8):
    """Find rows that contain 'dark' pixels (text/ink)."""
    # A pixel is "ink" if any channel is below threshold
    is_ink = np.any(arr < threshold, axis=2)
    row_has_ink = np.any(is_ink, axis=1)
    # Find runs of ink rows
    runs = []
    in_run = False
    start = 0
    for y, v in enumerate(row_has_ink):
        if v and not in_run:
            start = y
            in_run = True
        elif not v and in_run:
            if y - start >= min_run:
                runs.append((start, y - 1))
            in_run = False
    if in_run:
        runs.append((start, len(row_has_ink) - 1))
    return runs

def find_band_breaks(arr):
    """Find horizontal bands of dense ink (text/diagram)."""
    h, w, _ = arr.shape
    # Count ink pixels per row
    is_ink = np.any(arr < 80, axis=2)
    ink_per_row = is_ink.sum(axis=1)
    # Smooth with a 5-row kernel
    kernel = np.ones(5) / 5
    smoothed = np.convolve(ink_per_row, kernel, mode='same')

    # Find peaks: rows where ink count > 5% of width (for text) or > 30% (for diagram fills)
    # Plot the density
    return smoothed

def find_main_content_bbox(arr, bg_threshold=40):
    """Find bounding box of non-background content in main area."""
    h, w, _ = arr.shape
    # Assume background is light or a known color; non-bg = different from corner
    corners = [tuple(arr[5,5]), tuple(arr[5,w-6]), tuple(arr[h-6,5]), tuple(arr[h-6,w-6])]
    # Use the most common corner color as bg
    from collections import Counter
    bg = Counter(corners).most_common(1)[0][0]
    # Distance from bg
    diff = np.abs(arr.astype(int) - np.array(bg)).sum(axis=2)
    is_content = diff > 60
    return is_content, bg

def measure_frame(path):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape

    result = {
        "path": path,
        "size": (w, h),
        "corners": sample_bg(img),
        "dominant_colors": dominant_bg(img, 3),
    }

    # Find ink rows
    ink_runs = find_text_rows(arr, threshold=80, min_run=3)
    result["ink_runs"] = [(s, e, e - s + 1) for s, e in ink_runs[:20]]

    # Find main content
    is_content, bg = find_main_content_bbox(arr)
    if is_content.any():
        ys, xs = np.where(is_content)
        result["content_bbox"] = {
            "left": int(xs.min()),
            "right": int(xs.max()),
            "top": int(ys.min()),
            "bottom": int(ys.max()),
            "width": int(xs.max() - xs.min() + 1),
            "height": int(ys.max() - ys.min() + 1),
        }

    # Find horizontal density profile (ink per row)
    ink_per_row = is_content.sum(axis=1)
    # Find the row with the maximum content
    result["max_content_row"] = int(ink_per_row.argmax())
    result["max_content_count"] = int(ink_per_row.max())

    # Header band detection: scan from top, find rows that have ANY non-bg content
    # but not a full bleed (i.e., header text typically has 5-30% row coverage)
    # The header band is a contiguous block of rows near the top
    # Let's find: rows 0-200 density
    density_top = ink_per_row[:200]
    density_bot = ink_per_row[-200:]

    # The header is where we first see sustained content near the top
    # Caption is where we see sustained content near the bottom
    threshold_density = w * 0.02  # at least 2% of width has content

    # Find first sustained run from top
    def find_first_run(density, thresh, min_len=3, max_gap=5):
        run_start = None
        gap = 0
        for y, v in enumerate(density):
            if v > thresh:
                if run_start is None:
                    run_start = y
                gap = 0
            else:
                if run_start is not None:
                    gap += 1
                    if gap > max_gap:
                        return run_start, y - gap
        if run_start is not None:
            return run_start, len(density) - 1
        return None, None

    hdr_start, hdr_end = find_first_run(density_top, threshold_density, max_gap=10)
    # If the header starts very early (e.g., y=0), it's a full-bleed card
    result["header_band_candidate"] = (hdr_start, hdr_end)

    # Bottom scan
    density_bot_rev = ink_per_row[::-1][:200]
    cap_start_rev, cap_end_rev = find_first_run(density_bot_rev, threshold_density, max_gap=10)
    if cap_start_rev is not None:
        cap_start = h - cap_end_rev - 1
        cap_end = h - cap_start_rev - 1
        result["caption_band_candidate"] = (cap_start, cap_end)
    else:
        result["caption_band_candidate"] = None

    return result

if __name__ == "__main__":
    # Sample segments 1-2 (first ~150 seconds = frames 1-150 at fps=1)
    # Actually, the reference is 15:15 = 915s. At 1fps that's 915 frames.
    # The 12 segments are roughly 76s each. Segments 1-2 = 0-152s = frames 1-152.
    # Let's sample 1 frame every 10s in segments 1-2, and add a few across the whole video.
    frames_to_measure = []
    # Segments 1-2: frames 1-150
    for f in [1, 5, 10, 20, 30, 45, 60, 75, 90, 105, 120, 135, 150]:
        frames_to_measure.append(f"frame_{f:04d}.png")

    # Add a couple from later segments for sanity
    for f in [200, 300, 500, 700, 900]:
        frames_to_measure.append(f"frame_{f:04d}.png")

    results = []
    for fname in frames_to_measure:
        path = os.path.join(REF_DIR, fname)
        if not os.path.exists(path):
            print(f"SKIP: {path}")
            continue
        r = measure_frame(path)
        results.append(r)
        print(f"\n=== {fname} ===")
        print(f"  Size: {r['size']}")
        print(f"  Corners: {r['corners']}")
        print(f"  Dominant: {r['dominant_colors'][:2]}")
        print(f"  Content bbox: {r.get('content_bbox')}")
        print(f"  Header band candidate: {r.get('header_band_candidate')}")
        print(f"  Caption band candidate: {r.get('caption_band_candidate')}")
        print(f"  Ink runs (top 5): {r['ink_runs'][:5]}")

    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} measurements to {OUT_JSON}")
