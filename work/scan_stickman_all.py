"""Scan ALL 916 frames for stickman-like figures. Relaxed thresholds.
Look for ANY small connected figure that is not part of the diagram/planet.
"""
import os, sys, json
from PIL import Image
import numpy as np
from scipy.ndimage import label, find_objects

REF_DIR = "ref"
OUT_JSON = "ref/stickman_candidates_all.json"


def is_figure_candidate(slc, full_mask, frame_shape):
    """Score a connected component for stickman-like shape with relaxed thresholds."""
    sub = full_mask[slc]
    ys, xs = np.where(sub)
    n = len(ys)
    if n < 300 or n > 8000:
        return None
    h = ys.max() - ys.min() + 1
    w = xs.max() - xs.min() + 1
    if h < 80 or w < 30:
        return None
    if h < w * 1.2:  # vertical-ish
        return None
    # Look for dense top (head) and thinner body
    h_band = max(1, int(h * 0.25))
    head_band = sub[0:h_band, :]
    body_band = sub[h_band:, :]
    head_pix = head_band.sum()
    body_pix = body_band.sum()
    if head_pix < 30 or body_pix < 50:
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
    if head_h < 6 or head_w < 6:
        return None
    heads = h / head_h
    if heads < 2.5 or heads > 12:
        return None
    head_density = head_pix / max(1, head_h * head_w)
    body_density = body_pix / max(1, body_h * body_w)
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


def scan_frame(path, frame_num, t_s, W, H):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    gray = arr.mean(axis=2)
    ink = gray < 80  # dark pixels
    # Search lower 2/3 of frame
    y_search_start = H // 3
    roi = np.zeros_like(ink)
    roi[y_search_start:] = ink[y_search_start:]
    structure = np.ones((3, 3), dtype=bool)
    labels, n_comp = label(roi, structure=structure)
    slcs = find_objects(labels)
    candidates = []
    for cid, slc in enumerate(slcs, start=1):
        if slc is None:
            continue
        comp_mask = (labels == cid)
        s = is_figure_candidate(slc, comp_mask, arr.shape)
        if s is not None:
            # Reject if touching left/right margin
            if s["x0"] < 20 or s["x1"] > W - 20:
                continue
            # Reject very wide
            if s["w"] > 400:
                continue
            s["frame"] = frame_num
            s["t"] = t_s
            s["path"] = path
            candidates.append(s)
    candidates.sort(key=lambda c: -c["head_density"])
    return candidates


def main():
    # Get image size
    sample = Image.open(os.path.join(REF_DIR, "frame_0001.png"))
    W, H = sample.size
    print(f"Frame size: {W}x{H}")
    del sample

    results = []
    # Scan all 916 frames
    for frame in range(1, 917):
        path = os.path.join(REF_DIR, f"frame_{frame:04d}.png")
        if not os.path.exists(path):
            continue
        t_s = frame - 1
        cands = scan_frame(path, frame, t_s, W, H)
        for c in cands[:3]:
            results.append(c)
        if frame % 50 == 0:
            print(f"  scanned frame {frame}, found {len(results)} total candidates so far")
    with open(OUT_JSON, "w") as f:
        json.dump([{k: (int(v) if hasattr(v, 'item') else v) for k, v in c.items()} for c in results], f, indent=2)
    print(f"\nWrote {len(results)} candidates to {OUT_JSON}")
    # group by frame
    by_frame = {}
    for c in results:
        by_frame.setdefault(c["frame"], []).append(c)
    print(f"\nFound in {len(by_frame)} unique frames")
    # Top 30 by head_density
    results.sort(key=lambda c: -c["head_density"])
    print("\nTop 30 by head_density:")
    for c in results[:30]:
        print(f"  f{c['frame']:4d} t={c['t']:5.1f}s  H={c['h']:4d} W={c['w']:3d}  heads={c['heads']:.1f}  head={c['head_h']}x{c['head_w']}  body={c['body_h']}x{c['body_w']}  hd={c['head_density']:.2f} bd={c['body_density']:.2f}  x={c['x0']}-{c['x1']} y={c['y0']}-{c['y1']}")


if __name__ == "__main__":
    main()
