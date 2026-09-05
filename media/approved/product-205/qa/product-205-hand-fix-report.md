# Product 205 — Final Right-Hand Redo Report

**Product:** 205 · **SKU:** NM-3605 · **Title:** انگشتر نقره مردانه عقیق باباقوری
**Date:** 2026-09-02
**Scope:** `angle-A/step4-on-finger.webp` only. Angle B's approved LEFT-hand image was kept unchanged. `step1`, `step2`, `step3` untouched for both angles.

## Root cause of the rejected image

The previous right-hand render changed the ring. The reference image had been re-derived from a cached working copy rather than freshly re-read, and the framing was wide enough that the ring occupied only a small part of the frame, so the model reconstructed a generic mount instead of reproducing the real one.

**Both causes are now fixed:**
1. Attachment 206 was **re-downloaded from release `media-originals-v1`**, extracted alone, the ZIP deleted, and that fresh file attached to every generation call.
2. The framing was tightened so the ring is large and its details are readable.

## Permanent rules applied

- `ORIGINAL_REATTACHED=YES` for every call — the real original of that exact angle was attached each time; no generated output was ever used as the product reference.
- `BAND_CLOSED` — RADMAN rings are always closed-band. Every output must render a complete continuous shank with no gap, split or open ends.

## Attempts

| Attempt | Original re-attached | Result | Verdict |
|---|---|---|---|
| 1 | YES | Ring too small in frame; mount simplified, long silver claw prongs not reproduced | REJECTED — not stored |
| 2 | YES | Close-up framing; large oval honey→cream cabochon, long curved silver claw prongs, openwork pierced shoulders, all-silver, closed band | **ACCEPTED** |

**PRODUCT205_RIGHT_HAND_ATTEMPTS=2** (limit was 3; the fallback to the medium-quality image was not needed).

---

## Output QA

### angle-A/step4-on-finger.webp — attachment 206 — REGENERATED

| Field | Value |
|---|---|
| ORIGINAL_REATTACHED | **YES** (attachment 206, freshly re-downloaded) |
| RING_IDENTITY_PRESERVED | **YES** |
| BAND_CLOSED | **YES** |
| HAND_SIDE | **RIGHT** |
| STATUS | **READY** |

**Notes:** Hand enters from the right, fingers pointing left, thumb in the foreground ⇒ right hand. Ring matches the original: one large oval banded-agate cabochon, honey/caramel-amber fading to pale cream, gripped by many long slender curved **silver** claw prongs, openwork pierced silver shoulders, no gold anywhere. Band is a complete closed shank. Premium masculine styling with dark suit cuff, warm controlled commercial lighting and shallow depth of field, matching the approved angle-B image. No face, text, logo or watermark.

### angle-B/step4-on-finger.webp — attachment 207 — UNCHANGED

| Field | Value |
|---|---|
| ORIGINAL_REATTACHED | YES (at time of generation) |
| RING_IDENTITY_PRESERVED | **YES** |
| BAND_CLOSED | **YES** |
| HAND_SIDE | **LEFT** |
| STATUS | **READY** |

### Previously stored outputs — band re-verified this run

| Output | BAND_CLOSED | STATUS |
|---|---|---|
| angle-A/step1-no-watermark.webp | YES (band continuous; bottom occluded by the box, no gap rendered) | READY |
| angle-A/step2-black-background.webp | YES | READY |
| angle-A/step3-luxury-promo.webp | YES (closed continuous shank) | READY |
| angle-B/step1-no-watermark.webp | YES | READY |
| angle-B/step2-black-background.webp | YES | READY |
| angle-B/step3-luxury-promo.webp | YES (closed continuous shank) | READY |

No stored product 205 output violates the closed-band rule, so no other output needed regeneration.

## Summary

| Angle | Attachment | Hand | Ring identity | Band closed | Status |
|---|---|---|---|---|---|
| A | 206 | **RIGHT** | preserved | YES | **READY** |
| B | 207 | **LEFT** | preserved | YES | **READY** |

All eight product 205 outputs are READY. Nothing is FAILED, and nothing remains pending.
