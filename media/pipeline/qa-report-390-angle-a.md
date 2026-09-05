# QA Report — Product 390, Angle A (attachment 391)

Pilot `media-image-pipeline-v1-p390-a` — executed 2026-09-03
Source: `media-originals-v1` → `radman-product-images-20260829-052041.zip` → `product-390-sku-13204540-featured-attachment-391.webp`

Per-call discipline: the exact original file of this angle was re-read and re-attached as the product reference for **every** AI call. No generated image was ever used as a reference, no memory-based prompts. Logged per output below.

## step1-no-watermark.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES (edit computed from the original file on disk)
- VIEWPOINT_UNCHANGED=YES (pixel-identical outside the watermark mask)
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Removed only the gold "نقره مشهد" seller emblem (bottom-right). Adaptive mask: gold-color detection (r>130, g>90, r-b>45, g-b>20) filtered to bottom-right quadrant (y>0.55H, x>0.5W, area>400) + loose second pass + 13px dilation + close. Telea inpaint + gentle blur. Ring, box, crop, viewpoint, lighting unchanged elsewhere. Verified side-by-side: clean.

## step2-black-background.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES (base = cleaned original; only background changed)
- VIEWPOINT_UNCHANGED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Pink pixels (HSV hue 158–186, sat>30, val>55) masked, closed, dilated 25px, feathered, composited onto deep charcoal studio backdrop (0.055→0.10 top→bottom, neutral 0.96/0.96/0.98) with soft glow. Same ring, same box, same viewpoint, same crop. Watermark-free.

## step3-luxury-promo.webp — AI generation (prompt + reference)

- ORIGINAL_REATTACHED=YES
- VIEWPOINT_UNCHANGED=NA (new still-life; only steps 1–2 require unchanged viewpoint)
- RING_IDENTITY_PRESERVED=YES (same oval milky white-blue agate, same brown-red deer dendrite, same diamond-lattice shoulder engraving, polished bezel, right-facing presentation)
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Dark masculine luxury: charcoal slab, black background, rim light, warm reflection. No hand/face/text/logo/watermark/price. No retry (attempt 1/1).

## step4-on-finger.webp — AI generation (prompt + reference)

- ORIGINAL_REATTACHED=YES
- VIEWPOINT_UNCHANGED=NA
- RING_IDENTITY_PRESERVED=YES (deer-motif agate, lattice band preserved)
- BAND_CLOSED=YES
- HAND_SIDE=RIGHT (correct for angle A / right-facing ring; thumb at bottom-left = back of a RIGHT hand, verified at zoom)
- STATUS=READY
- NOTES=Adult male right hand: 5 fingers, ring worn on ring finger (index→pinky order), realistic skin/hairs/knuckles, correct scale, premium charcoal rim-lit framing, no face/text/logo/watermark. No retry (attempt 1/1).

## Overall

- TOTAL GENERATIONS USED: 2 of max 4 (+0 retries). Remaining budget: 2.
- All four outputs: STATUS=READY. BAND_CLOSED_ALL=YES. ORIGINAL_REATTACHED_ALL=YES.
- VIEWPOINT_UNCHANGED (step1 & step2)=YES.
- Nothing stored under `media/approved/` yet. Waiting for owner review.
