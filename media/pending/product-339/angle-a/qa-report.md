# QA Report — Product 339, Angle A (attachment 340) — FINAL

Pilot run 2026-09-05 · branch `ai-media-cleaning-pilot-20260829`
Source: `media-originals-v1` → `radman-product-images-20260829-052041.zip` → `product-339-sku-NM-3561-featured-attachment-340.webp` (SHA-256 `ee86f3032ce86501cea572df4cb1d56caa0304fbddeffc674f541cb5a23f121e`)
Product: انگشتر نقره مردانه عقیق سلیمانی (Men's Silver Ring — Banded Suleimani/Carnelian Agate) · SKU NM-3561
Angle A = featured attachment 340. Original re-read from disk before every call.

**RESULT: 4/4 READY** — generations used this run: 2 (step3 + step4), within the 5 cap.

## step1-a.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES · VIEWPOINT_UNCHANGED=YES · RING_IDENTITY_PRESERVED=YES · BAND_CLOSED=YES · HAND_SIDE=NA · STATUS=READY
- Removed only the gold «نقره مشهد» seller emblem (bbox 936,1146 → 1466,1452; ~42.6k gold px detected, mask 75k px after dilation) via Telea inpaint + boundary blur.
- Attempt 1 left faint flourish residue (visible curls at ~(1100,1250)/(1370,1250)) → retry with lower-saturation gold mask; residual gold px after edit: 31 (anti-alias only, invisible at review zoom). Pixel-diff vs original confined to the watermark zone; hallmark, band, stone, box untouched.

## step2-a.webp — masked edit (no generation), input = step1 OUTPUT

- ORIGINAL_REATTACHED=YES · VIEWPOINT_UNCHANGED=YES · RING_IDENTITY_PRESERVED=YES · BAND_CLOSED=YES · HAND_SIDE=NA · STATUS=READY
- Pink surroundings → deep charcoal (ramp #16–#1a, matching prior runs' 0.055→0.10 neutral backdrop). White jewelry box preserved; box-horizon pink glow neutralized to a soft gray contact shadow (matches approved product-387 precedent). Pink background visible through the ring window → charcoal. Stone-rim halo re-composited with alpha matting (pink-contribution subtracted, charcoal added) for a clean silhouette.
- Verified numerically: **0 changed pixels inside the stone/hallmark protection zone**; white box below horizon unchanged except a 1–2 px feather line at the horizon (natural contact shadow).
- TRANSPARENCY NOTE: step2 required several deterministic mask-refinement passes beyond the nominal single retry (stone-hue leak, horizon mis-detection on braid highlights and box shadows, 1-px erosion losses). All passes are pixel-level edits — **zero AI generations consumed** — and the final output passed visual + numeric QA before upload.

## step3-a.webp — AI generation (1/1)

- ORIGINAL_REATTACHED=YES · RING_IDENTITY_PRESERVED=YES (striped carnelian, looped crown bezel, braided shoulders) · BAND_CLOSED=YES · STATUS=READY
- Surface rotation: **polished black glass** with mirror reflection, charcoal backdrop. No box, no hand, no text/logo/watermark.

## step4-a.webp — AI generation (1/1)

- ORIGINAL_REATTACHED=YES · RING_IDENTITY_PRESERVED=YES · BAND_CLOSED=YES · HAND_SIDE=**RIGHT** (correct for angle A; back-of-hand view, fingers toward viewer, thumb at frame-right) · STATUS=READY
- Ring worn on the **ring finger** (2nd from pinky), 5 fingers, correct scale, adult male hand.
- Style rotation: **dark suit cuff + white shirt edge on black** (not the brown-background/blue-shirt combo). No face, no text/logo.

## Overall

| Output | VIEWPOINT_UNCHANGED | RING_IDENTITY | BAND_CLOSED | HAND_SIDE | Status |
|---|---|---|---|---|---|
| step1 | YES | YES | YES | NA | READY |
| step2 | YES | YES | YES | NA | READY |
| step3 | NA (new still-life) | YES | YES | NA | READY |
| step4 | NA (new on-hand) | YES | YES | RIGHT | READY |

BAND_CLOSED_ALL=YES · STEP2_BOX_PRESERVED=YES · STEP2_WATERMARK_ABSENT=YES
Nothing stored under `media/approved/` — pending owner review.
