#!/usr/bin/env python3
"""Detect old gold seller-logo watermark (نقره مشهد ornamental logo) in bottom region.
Generates a narrow binary mask for inpainting. Controls must yield empty masks."""
import cv2, numpy as np, os, sys, csv

SRC = os.path.expanduser('~/assets/originals-pack/image-cleaning-20260829-052041/originals')
SEL = os.path.expanduser('~/pilot/pilot-selection.tsv')
QA  = os.path.expanduser('~/pilot/scratch/maskqa')

def detect(img_bgr):
    H, W = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    y0 = int(H * 0.66)
    roi = hsv[y0:, :]
    # gold ornamental logo: warm hue, saturated, bright-ish
    mask = cv2.inRange(roi, (13, 60, 80), (34, 255, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mask = cv2.dilate(mask, np.ones((13, 13), np.uint8))
    # drop tiny specks
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    out = np.zeros_like(mask)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 60:
            out[lab == i] = 255
    full = np.zeros((H, W), np.uint8)
    full[y0:, :] = out
    ys, xs = np.where(full > 0)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
    return full, bbox

rows = list(csv.DictReader(open(SEL), delimiter='\t'))
for r in rows:
    fn = r['filename']
    img = cv2.imread(os.path.join(SRC, fn))
    mask, bbox = detect(img)
    np.save(os.path.join(QA, fn + '.mask.npy'), mask)
    vis = img.copy()
    vis[mask > 0] = (0.35 * vis[mask > 0] + 0.65 * np.array([0, 0, 255])).astype(np.uint8)
    if bbox:
        x0, y0, x1, y1 = bbox
        cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 255, 255), 3)
    cv2.imwrite(os.path.join(QA, fn + '.overlay.jpg'), vis, [cv2.IMWRITE_JPEG_QUALITY, 85])
    px = int((mask > 0).sum())
    print(f"{fn}  mask_px={px:7d}  bbox={bbox}")
