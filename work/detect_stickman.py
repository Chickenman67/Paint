"""Detect stickman-shaped figures in extracted reference frames.
Uses scipy.ndimage for fast connected components.
"""
import os, sys, json
from PIL import Image
import numpy as np
from scipy.ndimage import label, find_objects

REF_DIR = "ref"
OUT_JSON = "ref/stickman_candidates.json"


def score_component(slc, full_mask, frame_shape):
    """Score a connected component for stickman-like shape.
    slc: tuple of slice objects bounding the component.
    full_mask: the binary mask of all ink in the frame.
    """
    sub = full_mask[slc]
    ys, xs = np.where(sub)
    n = len(ys)
    if n < 200 or n > 30000:
        return None
    h = ys.max() - ys.min() + 1
    w = xs.max() - xs.min() + 1
    if h < 150 or w < 50:
        return None
    if h < w * 1.3:  # must be vertical
        return None
    # Look for dense top (head) and thin body+limbs
    ymin, ymax = ys.min(), ys.max()
    h_band = max(1, int(h * 0.22))
    head_band = sub[0:h_band, :]
    body_band = sub[h_band:, :]
    head_pix = head_band.sum()
    body_pix = body_band.sum()
    if head_pix < 100 or body_pix < 100:
        return None
    hy, hx = np.where(head_band)
    if len(hy) == 0:
        return None
    head_h = hy.max() - hy.min() + 1
    head_w = hx.max() - hx.min() + 1
    by, bx = np.where(body_band)
    if len(by) == 0:
        return None
    body_h = by.max() - by.min() + 1
    body_w = bx.max() - bx.min() + 1
    if head_h < 8:
        return None
    heads = h / head_h
    if heads < 3.5 or heads > 9:
        return None
    head_density = head_pix / max(1, head_h * head_w)
    body_density = body_pix / max(1, body_h * body_w)
    # Stickman: head is dense (oval), body has lower density (lines)
    if head_density < 0.30:
        return None
    if body_density > 0.65:
        return None
    return {
        "n": n, "h": h, "w": w,
        "y0": int(ys.min() + slc[0].start), "y1": int(ys.max() + slc[0].start),
        "x0": int(xs.min() + slc[1].start), "x1": int(xs.max() + slc[1].start),
        "head_h": int(head_h), "head_w": int(head_w),
        "body_h": int(body_h), "body_w": int(body_w),
        "heads": float(heads),
        "head_density": float(head_density),
        "body_density": float(body_density),
    }


def scan_frame(path, frame_num, t_s):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    H, W, _ = arr.shape
    gray = arr.mean(axis=2)
    ink = gray < 80  # dark pixels = lines
    # search lower 2/3 of frame
    y_search_start = H // 3
    roi = np.zeros_like(ink)
    roi[y_search_start:] = ink[y_search_start:]
    # Connected components (8-connectivity via 2-pass with 3x3 structure)
    structure = np.ones((3, 3), dtype=bool)
    labels, n_comp = label(roi, structure=structure)
    slcs = find_objects(labels)
    candidates = []
    for cid, slc in enumerate(slcs, start=1):
        if slc is None:
            continue
        comp_mask = (labels == cid)
        s = score_component(slc, comp_mask, arr.shape)
        if s is not None:
            # Reject if touching left/right margin (assume interior)
            if s["x0"] < 40 or s["x1"] > W - 40:
                continue
            # Reject if too wide (multiple things touching)
            if s["w"] > 320:
                continue
            s["frame"] = frame_num
            s["t"] = t_s
            s["path"] = path
            candidates.append(s)
    candidates.sort(key=lambda c: -c["head_density"])
    return candidates


def main():
    results = []
    # Scan all frames in first 180s (fps=1)
    for frame in range(1, 181):
        path = os.path.join(REF_DIR, f"frame_{frame:04d}.png")
        if not os.path.exists(path):
            continue
        t_s = frame - 1
        cands = scan_frame(path, frame, t_s)
        for c in cands[:2]:
            results.append(c)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {len(results)} candidates to {OUT_JSON}")
    results.sort(key=lambda c: -c["head_density"])
    for c in results[:30]:
        print(f"  f{c['frame']:4d} t={c['t']:5.1f}s  H={c['h']:4d} W={c['w']:3d}  heads={c['heads']:.1f}  head={c['head_h']}x{c['head_w']}  body={c['body_h']}x{c['body_w']}  hd={c['head_density']:.2f} bd={c['body_density']:.2f}  x={c['x0']}-{c['x1']} y={c['y0']}-{c['y1']}")


if __name__ == "__main__":
    main()
