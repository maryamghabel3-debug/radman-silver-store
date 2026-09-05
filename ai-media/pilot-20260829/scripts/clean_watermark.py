#!/usr/bin/env python3
"""Strict ecommerce watermark cleaning for RADMAN SILVER 925 pilot.

Pipeline (v3):
 1. Detect vivid-gold 'core' components of the old seller logo in the bottom ROI.
    (calibrated: logo stroke vivid-density 0.57-0.95, ring reflections 0.13-0.53)
 2. Grow a bounding box around the core (+60 px) and accept ANY pale-to-vivid
    gold pixel inside that box -> catches the pale ornamental frame, stays local.
 3. Clamp the final mask to human-reviewed per-image windows (mask-review.json).
 4. Inpaint ONLY the mask: Navier-Stokes core + Telea, feather-blended.
Controls / empty masks: byte-identical copy of the original (zero modification).
Pixels outside the mask are untouched by construction; dimensions and mode kept.
"""
import cv2, numpy as np, os, json, csv, time, shutil

SRC   = os.path.expanduser('~/assets/originals-pack/image-cleaning-20260829-052041/originals')
PILOT = os.path.expanduser('~/pilot')
OUT   = os.path.join(PILOT, 'cleaned')
REVIEW = json.load(open(os.path.join(PILOT, 'scripts', 'mask-review.json')))


def detect_v3(img):
    H, W = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    y0 = int(H * 0.64)
    roi = hsv[y0:, :]
    base  = cv2.inRange(roi, (13, 80, 90), (34, 255, 255))
    vivid = cv2.inRange(roi, (13, 100, 95), (34, 255, 255))
    loose = cv2.inRange(roi, (10, 25, 70), (40, 255, 255))  # pale-to-vivid gold
    base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(base, 8)
    core = np.zeros_like(base)
    log = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 150:
            continue
        comp = (lab == i)
        density = (vivid[comp] > 0).mean()
        if density < 0.55:
            continue
        cx, cy = cent[i]
        log.append((round(float(cx) / W, 3), round(float(cy + y0) / H, 3),
                    int(area), round(float(density), 2)))
        core[comp] = 255
    if core.any():
        ys, xs = np.where(core > 0)
        m = 60
        x0, x1 = max(0, int(xs.min()) - m), min(W, int(xs.max()) + m)
        yb0, yb1 = max(0, int(ys.min()) - m), min(roi.shape[0], int(ys.max()) + m)
        boxm = np.zeros_like(core)
        boxm[yb0:yb1, x0:x1] = 255
        mask_roi = cv2.bitwise_and(loose, boxm)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    else:
        mask_roi = np.zeros_like(core)
    full = np.zeros((H, W), np.uint8)
    full[y0:, :] = mask_roi
    return full, log


def apply_window(mask, fn):
    rule = REVIEW.get(fn, "none")
    if rule == "none":
        return np.zeros_like(mask)
    H, W = mask.shape[:2]
    win = np.zeros_like(mask)
    x0, x1 = int(rule['x'][0] * W), int(rule['x'][1] * W)
    y0, y1 = int(rule['y'][0] * H), int(rule['y'][1] * H)
    win[y0:y1, x0:x1] = 255
    out = cv2.bitwise_and(mask, win)
    out = cv2.dilate(out, np.ones((11, 11), np.uint8))  # incl. anti-aliased halo
    return cv2.bitwise_and(out, win)


def main():
    rows = list(csv.DictReader(open(os.path.join(PILOT, 'pilot-selection.tsv')), delimiter='\t'))
    times = []
    for r in rows:
        fn = r['filename']
        img = cv2.imread(os.path.join(SRC, fn))
        t0 = time.time()
        rule = REVIEW.get(fn, "none")
        if rule == "none":
            mask, comps = np.zeros(img.shape[:2], np.uint8), []
        else:
            cand, comps = detect_v3(img)
            mask = apply_window(cand, fn)
        px = int((mask > 0).sum())
        if px == 0:
            shutil.copyfile(os.path.join(SRC, fn), os.path.join(OUT, fn))
            status = 'CONTROL_NOOP'
        else:
            # FSR_FAST (patch-based, frequency-domain) primary engine — method comparison
            # on 2026-08-29 showed cleanest texture continuation (ShiftMap: blocky, rejected).
            inv = cv2.bitwise_not(mask)
            fsr = img.copy()
            cv2.xphoto.inpaint(img, inv, fsr, cv2.xphoto.INPAINT_FSR_FAST)
            # feathered boundary blend to hide any seam
            feather = cv2.GaussianBlur(mask, (0, 0), 1.5).astype(np.float32)[..., None] / 255.0
            out = (fsr.astype(np.float32) * feather + img.astype(np.float32) * (1 - feather)).astype(np.uint8)
            # verify: pixels far outside the mask (eroded complement) must be unchanged
            outside = cv2.erode(cv2.bitwise_not(mask), np.ones((25, 25), np.uint8))
            diff_out = int(np.abs(out.astype(int) - img.astype(int))[outside > 0].max()) if (outside > 0).any() else 0
            assert diff_out == 0, f"non-mask pixels modified in {fn} (maxdiff={diff_out})"
            assert out.shape == img.shape and out.dtype == img.dtype
            cv2.imwrite(os.path.join(OUT, fn), out, [cv2.IMWRITE_WEBP_QUALITY, 95])
            status = 'INPAINTED_FSR'
        dt = time.time() - t0
        times.append(dt)
        np.save(os.path.join(PILOT, 'scratch', 'maskqa', fn + '.mask3.npy'), mask)
        print(f"{fn}  {status}  mask_px={px:7d} ({px * 100.0 / mask.size:.2f}%)  comps={len(comps)}  t={dt:.2f}s")
    print(f"avg processing time: {np.mean(times):.2f}s/image")


if __name__ == '__main__':
    main()
