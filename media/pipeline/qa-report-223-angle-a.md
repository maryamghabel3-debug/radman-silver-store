# Product 223 — Angle A QA Report

- Product ID: 223
- SKU: NM-3599
- Title: انگشتر نقره مردانه دُر نجف تراش دامله (Men's silver ring with Najaf stone)
- Product role: featured (Angle A)
- Attachment ID: 224
- Source original: `product-223-sku-NM-3599-featured-attachment-224.webp` (1600x1600)
- Original re-downloaded from GitHub release `media-originals-v1`, persisted, then re-attached to every generation call.
- Angle A orientation: right-facing ring (crown to upper-right, band curving down-left).
- Watermark in original: gold ornate cartouche logo, lower-right corner.
- Original re-attached to every generation call before generation.

## Outputs (Angle A)

### step1-no-watermark.webp
- ORIGINAL_REATTACHED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- VIEWPOINT_UNCHANGED=YES (masked in-place edit, same crop/angle/box/background)
- WATERMARK_REMOVED=YES
- STATUS=READY

### step2-black-background.webp
- ORIGINAL_REATTACHED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- VIEWPOINT_UNCHANGED=YES (masked in-place edit; pink backdrop -> deep charcoal; white box stays white)
- WATERMARK_REMOVED=YES
- STATUS=READY

### step3-luxury-promo.webp
- ORIGINAL_REATTACHED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- NO_HAND=YES
- NO_TEXT=YES / NO_LOGO=YES / NO_WATERMARK=YES / NO_PRICE=YES
- STATUS=READY

### step4-on-finger.webp
- ORIGINAL_REATTACHED=YES
- RING_IDENTITY_PRESERVED=YES
- BAND_CLOSED=YES
- HAND_SIDE=RIGHT
- HAND=ADULT_MALE
- ANATOMY=PLAUSIBLE
- FINGER_COUNT=CORRECT
- RING_SCALE=NATURAL
- NO_FACE=YES / NO_TEXT=YES / NO_LOGO=YES / NO_WATERMARK=YES / NO_PRICE=YES
- STATUS=READY

## Summary
- Outputs generated: 4
- Status: 4/4 READY, 0 FAILED
- One angle per turn discipline: YES (this turn processed Angle A only)
- Generation attempts: 7 (step1 required 2 retries after empty-response; step4 required 2 retries to correct hand side)
- Retries used: step1 (2), step4 (2)
- Hand rule satisfied: Angle A (right-facing) = adult male RIGHT hand. Verified against the owner-approved product 226 angle A reference (fingers left, thumb lower-right foreground, cuff upper-right).
- Closed-band rule satisfied on all outputs.
- Resolution: 1024x1024 (matches accepted baseline for prior approved products).

## Hand-side verification (step4)
- Regenerated to match the owner-approved RIGHT-hand reference pose: fingers pointed to left, thumb spread on lower-right in foreground, cuff at upper-right. => RIGHT hand. Confirmed.
