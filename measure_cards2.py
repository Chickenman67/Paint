#!/usr/bin/env python3
"""Refined card measurement: focus on stroke widths, margins, and 3-band structure."""
from PIL import Image
import numpy as np
import os
import json

REF_DIR = r"work/ref"

def find_row_density(arr, bg):
    """For each row, count pixels that differ significantly from bg."""
    diff = np.abs(arr.astype(int) - np.array(bg)).sum(axis=2)
    is_content = diff > 60
    return is_content.sum(axis=1)

def detect_3_bands(arr, bg):
    """Detect header/main/caption bands by row density."""
    h, w, _ = arr.shape
    density = find_row_density(arr, bg)

    # Background: corner color
    # The card has 3 bands separated by white space (gaps in density)
    # Find gaps in density
    threshold = w * 0.05  # at least 5% width has content

    # Find content rows
    has_content = density > threshold
    # Find first content from top
    first_content = np.argmax(has_content) if has_content.any() else 0
    last_content = h - 1 - np.argmax(has_content[::-1]) if has_content.any() else h - 1

    # Within the content range, find gaps
    content_density = density[first_content:last_content+1]
    has_content2 = content_density > threshold

    # Find runs of content
    runs = []
    in_run = False
    start = 0
    for i, v in enumerate(has_content2):
        if v and not in_run:
            start = i
            in_run = True
        elif not v and in_run:
            runs.append((start + first_content, i - 1 + first_content))
            in_run = False
    if in_run:
        runs.append((start + first_content, len(content_density) - 1 + first_content))

    # Merge runs separated by tiny gaps (< 15px)
    merged = []
    for s, e in runs:
        if merged and s - merged[-1][1] < 15:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))

    return density, merged

def measure_strokes(arr, bg, y_start, y_end, x_start, x_end):
    """Measure typical stroke widths in a region by detecting contiguous dark runs."""
    region = arr[y_start:y_end, x_start:x_end]
    is_ink = np.any(region < 80, axis=2)

    # For each row, find run lengths of ink
    run_lengths = []
    for row in is_ink:
        in_run = False
        run_len = 0
        for v in row:
            if v:
                if not in_run:
                    run_len = 1
                    in_run = True
                else:
                    run_len += 1
            else:
                if in_run:
                    if 1 <= run_len <= 10:  # skip very long fills
                        run_lengths.append(run_len)
                    in_run = False
                    run_len = 0
        if in_run and 1 <= run_len <= 10:
            run_lengths.append(run_len)
    if not run_lengths:
        return None
    from collections import Counter
    cnt = Counter(run_lengths)
    # Most common stroke widths
    return cnt.most_common(10)

def measure_horizontal_strokes(arr, bg, y_start, y_end, x_start, x_end):
    """Measure vertical stroke widths (horizontal line thickness)."""
    region = arr[y_start:y_end, x_start:x_end]
    is_ink = np.any(region < 80, axis=2)
    # Count consecutive ink rows
    run_lengths = []
    for col in is_ink.T:
        in_run = False
        run_len = 0
        for v in col:
            if v:
                if not in_run:
                    run_len = 1
                    in_run = True
                else:
                    run_len += 1
            else:
                if in_run:
                    if 1 <= run_len <= 10:
                        run_lengths.append(run_len)
                    in_run = False
                    run_len = 0
        if in_run and 1 <= run_len <= 10:
            run_lengths.append(run_len)
    if not run_lengths:
        return None
    from collections import Counter
    return Counter(run_lengths).most_common(8)

def measure_frame(path):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape

    # Use top-left corner as bg
    bg_top = tuple(arr[5, 5])
    bg_bot_left = tuple(arr[h-6, 5])
    bg_bot_right = tuple(arr[h-6, w-6])

    density, runs = detect_3_bands(arr, bg_top)
    result = {
        "path": os.path.basename(path),
        "size": (w, h),
        "bg_top_left": bg_top,
        "bg_bot_left": bg_bot_left,
        "bg_bot_right": bg_bot_right,
        "content_runs": runs,
    }

    # Measure margins in main area (largest gap)
    if len(runs) >= 2:
        # Use the second run as main area
        main_start = runs[1][0]
        main_end = runs[1][1]
        # Find left/right content extent within main area
        main_region = arr[main_start:main_end+1]
        diff = np.abs(main_region.astype(int) - np.array(bg_top)).sum(axis=2)
        is_content = diff > 60
        if is_content.any():
            ys, xs = np.where(is_content)
            result["main_content_bbox"] = {
                "x_start": int(xs.min()),
                "x_end": int(xs.max()),
                "y_start": int(ys.min()) + main_start,
                "y_end": int(ys.max()) + main_start,
            }
            result["main_margins"] = {
                "left": int(xs.min()),
                "right": w - 1 - int(xs.max()),
                "top_in_band": int(ys.min()),
                "bottom_in_band": main_end - int(ys.max()),
            }

        # Stroke widths in main area
        h_strokes = measure_strokes(arr, bg_top, main_start, main_end+1, 0, w)
        v_strokes = measure_horizontal_strokes(arr, bg_top, main_start, main_end+1, 0, w)
        result["h_strokes_in_main"] = h_strokes
        result["v_strokes_in_main"] = v_strokes

    # Header band: first run
    if runs:
        h_start, h_end = runs[0]
        result["header_band"] = (int(h_start), int(h_end), int(h_end - h_start + 1))

    # Caption band: last run
    if len(runs) >= 2:
        c_start, c_end = runs[-1]
        result["caption_band"] = (int(c_start), int(c_end), int(c_end - c_start + 1))
        # If there's a third run, it's a separator
        if len(runs) >= 3:
            result["main_band"] = (int(runs[1][0]), int(runs[1][1]), int(runs[1][1] - runs[1][0] + 1))

    return result

if __name__ == "__main__":
    frames = [1, 5, 10, 20, 30, 45, 60, 75, 90, 105, 120, 135, 150, 200, 300]
    out = []
    for f in frames:
        path = os.path.join(REF_DIR, f"frame_{f:04d}.png")
        if not os.path.exists(path):
            continue
        r = measure_frame(path)
        out.append(r)
        print(f"\n=== frame_{f:04d} ===")
        print(f"  size: {r['size']}")
        print(f"  bg_top: {r['bg_top_left']}, bg_bot: {r['bg_bot_left']}")
        print(f"  content_runs: {r['content_runs']}")
        if 'header_band' in r:
            print(f"  header_band: y={r['header_band'][0]}-{r['header_band'][1]} ({r['header_band'][2]}px)")
        if 'main_band' in r:
            print(f"  main_band: y={r['main_band'][0]}-{r['main_band'][1]} ({r['main_band'][2]}px)")
        if 'caption_band' in r:
            print(f"  caption_band: y={r['caption_band'][0]}-{r['caption_band'][1]} ({r['caption_band'][2]}px)")
        if 'main_margins' in r:
            print(f"  main_margins: {r['main_margins']}")
        if 'h_strokes_in_main' in r:
            print(f"  h_strokes: {r['h_strokes_in_main'][:5]}")
        if 'v_strokes_in_main' in r:
            print(f"  v_strokes: {r['v_strokes_in_main'][:5]}")

    with open("work/ref/card_measurements_v2.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
