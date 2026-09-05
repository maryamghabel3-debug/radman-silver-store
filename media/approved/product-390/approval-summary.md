# Approval Summary — Product 390 (Angle A)

**Product:** 390 · **SKU:** 13204540 · **Title:** انگشتر نقره مردانه شجر طبیعی نقش آهو (Men's Silver Ring — Natural Tree Agate, Deer Motif)
**Attachment (angle A):** 391 (featured original) · **Angle A = right-facing ring**
**Approved:** 2026-09-03 (owner command: خوبه برو بعدی)
**Source release:** [media-originals-v1](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-originals-v1) — `radman-product-images-20260829-052041.zip`
**Pilot release:** [media-image-pipeline-v1-p390-a](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-image-pipeline-v1-p390-a) — `radman-image-pipeline-v1-product-390-angle-A.zip`
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## ✅ Owner decision

Angle A of product 390 owner-approved after contact-sheet review (2026-09-03). All 4 outputs READY. Angle B in production; will be submitted for review next.

## Approved outputs and storage

Copied byte-for-byte from the approved release asset (SHA-256 verified against the release ZIP before copying).

| Source output (release) | Stored as | wordpress_action |
|---|---|---|
| step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | **`replace_featured_image`** |
| step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |

## QA (from qa-report-390-angle-a.md)

| Output | ORIGINAL_REATTACHED | VIEWPOINT_UNCHANGED | RING_IDENTITY_PRESERVED | BAND_CLOSED | HAND_SIDE | Status |
|---|---|---|---|---|---|---|
| step1 | YES | YES | YES | YES | NA | READY |
| step2 | YES | YES | YES | YES | NA | READY |
| step3 | YES | NA (new still-life) | YES | YES | NA | READY |
| step4 | YES | NA (new on-hand) | YES | YES | RIGHT | READY |

- **Band closed:** all outputs render the complete closed shank (RADMAN rings always closed-band).
- **Step1/Step2 are masked edits of the original** — watermark removed / pink→charcoal only; ring, box, viewpoint, crop unchanged.
- **Original re-attached:** the exact angle-A original (attachment 391) was re-read and attached before every AI call.
- **Hand rule:** angle A (right-facing) → adult male **RIGHT** hand. Verified: back of right hand, thumb bottom-left, 5 fingers, ring on ring finger.

## Product identity lock

Oval milky white-blue Qaen tree agate cabochon with dramatic natural brown-red deer (آهو) dendrite motif · plain polished bezel · wide 925 silver band with dense diagonal diamond-lattice engraved shoulders and beaded borders · smooth polished lower band · closed continuous shank · 3/4 upright right-facing viewpoint.

## Intended WordPress action (executed later by host from apply-manifest.tsv — nothing changed on WordPress)

- `ecommerce/main-black-bg-a.webp` → `replace_featured_image` (first approved main-black-bg for this product)
- all other three → `add_gallery_image`

## Pending

- Angle B (attachment 392, left-facing) — in production this run; will be submitted as `media-image-pipeline-v1-p390-b` with contact sheet, stopped for owner review before any registration.
