# QA Report — Product 390, Angle B (attachment 392) — FINAL

Pilot `media-image-pipeline-v1-p390-b` — executed 2026-09-03 (step4 dedicated retry v3)
Source: `media-originals-v1` → `radman-product-images-20260829-052041.zip` → `product-390-sku-13204540-gallery-1-attachment-392.webp`

**RESULT: 4/4 READY** (step4 corrected on the owner-approved dedicated retry, attempt v3).

Per-call discipline: the exact original file of this angle was re-read and re-attached as the product reference for **every** AI call (original re-verified by SHA-256 before the retry call). No generated image was ever used as a reference.

## step1-no-watermark.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES
- VIEWPOINT_UNCHANGED=YES (pixel-identical outside the watermark mask)
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Removed only the gold "نقره مشهد" seller emblem (bottom-left). Adaptive gold detection (bbox 118,1046 → 709,1474; wm 88105px) + Telea inpaint + blur. Ring, box, crop, viewpoint, lighting unchanged elsewhere.

## step2-black-background.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES
- VIEWPOINT_UNCHANGED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Pink surroundings → deep charcoal studio backdrop (0.055→0.10, neutral, soft glow). Same ring, box, viewpoint, crop. Watermark-free.

## step3-luxury-promo.webp — AI generation (attempt 1/1)

- ORIGINAL_REATTACHED=YES
- RING_IDENTITY_PRESERVED=YES (deer-motif agate, lattice band, left-facing)
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Dark masculine luxury still-life, no hand/text/logo/watermark.

## step4-on-finger.webp — AI generation — **READY (dedicated retry v3)**

- ORIGINAL_REATTACHED=YES (original re-read + SHA-256 verified before the call)
- RING_IDENTITY_PRESERVED=YES (milky blue-white agate + brown-red deer dendrite, diamond-lattice band, exact ring)
- BAND_CLOSED=YES
- HAND_SIDE=LEFT (correct for angle B / left-facing ring; back of left hand, thumb on right of frame — verified at zoom)
- STATUS=READY
- NOTES=Attempt history: v1 middle finger (FAIL), v2 index finger (FAIL — retry consumed), v3 dedicated retry (owner choice "1") — ring worn on the **RING FINGER** (2nd finger from the pinky), 5 fingers, correct scale, masculine charcoal rim-lit framing, no face/text/logo. Verified at zoom: left strip (pinky + ring finger), right strip (thumb), ring close-up all correct.

## Overall

- Generations this run: 1 (dedicated step4 retry). Cumulative angle-B: v1+v2 (failed, not shipped) + v3 (shipped).
- All four outputs: STATUS=READY. BAND_CLOSED_ALL=YES. ORIGINAL_REATTACHED_ALL=YES.
- VIEWPOINT_UNCHANGED (step1 & step2)=YES. HAND_SIDE=LEFT.
- Nothing stored under `media/approved/` for angle B yet — awaiting owner review of the contact sheet (mandatory review pack).
