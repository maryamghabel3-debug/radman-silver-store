# QA Report — Product 384, Angle A (attachment 385)

Pilot `media-image-pipeline-v1-p384-a` — executed 2026-09-03
Source: `media-originals-v1` → `radman-product-images-20260829-052041.zip` → `product-384-sku-17224539-featured-attachment-385.webp`

Per-call discipline: the exact original file of this angle was re-read and re-attached as the product reference for **every** AI call. No generated image was ever used as a reference, no memory-based prompts. Logged per output below.

## step1-no-watermark.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES (edit computed from the original file on disk)
- VIEWPOINT_UNCHANGED=YES (pixel-identical outside the watermark mask; verified by diff)
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Removed only the gold "نقره مشهد" seller emblem (diamond crest + scrollwork, bottom-right). Mask built by gold-color detection within the emblem bounding box (x935–1505, y1150–1535) + 13px dilation, Telea inpaint + gentle pass blur. Ring, box, crop, viewpoint, lighting, composition byte-identical elsewhere. v1 left two faint scroll arcs; mask refined (second pass caught remaining gold components) and re-run. Final: clean.

## step2-black-background.webp — masked edit (no generation)

- ORIGINAL_REATTACHED=YES (base = cleaned step-1/step-2 of the original; only background changed)
- VIEWPOINT_UNCHANGED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=NA
- STATUS=READY
- NOTES=pink pixels (HSV hue 158–186, sat>30, val>55) masked, morphologically closed, dilated 25px, feathered 6px, composited onto deep charcoal (luma 0.055→0.10 top→bottom, value ~0.96/0.96/0.98 neutral) with a soft studio glow centered behind the ring. Same ring, same box, same viewpoint and crop. Watermark-free (base = step 1).

## step3-luxury-promo.webp — AI generation (prompt + reference)

- ORIGINAL_REATTACHED=YES
- VIEWPOINT_UNCHANGED=NA (new still-life; only steps 1–2 require unchanged viewpoint)
- RING_IDENTITY_PRESERVED=YES (same oval milky agate, same dendrite branch pattern, same beaded bezel, same scroll band, same right-facing presentation)
- BAND_CLOSED=YES (full closed shank visible, no gap)
- HAND_SIDE=NA
- STATUS=READY
- NOTES=Dark masculine luxury: charcoal stone slab, deep black background, rim light, warm reflection. No hand, no face, no text/logo/watermark/price. Verified at zoom; no retry needed (attempt 1/1).

## step4-on-finger.webp — AI generation (prompt + reference)

- ORIGINAL_REATTACHED=YES
- VIEWPOINT_UNCHANGED=NA
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=RIGHT (correct for angle A / right-facing ring; thumb on left edge of frame = back of a RIGHT hand, verified by edge crop)
- STATUS=READY
- NOTES=Adult male right hand, anatomical: 5 fingers, ring worn on the ring finger, realistic skin/hairs/knuckles, correct ring scale, premium charcoal rim-lit framing, no face/text/logo/watermark. Verified at zoom; no retry needed (attempt 1/1).

## Overall

- TOTAL GENERATIONS USED: 2 of max 4 (+0 retries). Remaining budget: 2.
- All four outputs: STATUS=READY. BAND_CLOSED_ALL=YES. ORIGINAL_REATTACHED_ALL=YES.
- VIEWPOINT_UNCHANGED (step1 & step2)=YES.
- Nothing stored under `media/approved/`. Waiting for owner review.
