# Approval Summary — Product 384 (Angle A)

**Product:** 384 · **SKU:** 17224539 · **Title:** انگشتر نقره مردانه شجر قائن طبیعی (Men's Silver Ring — Natural Qaen Tree Agate)
**Attachment (angle A):** 385 (featured original) · **Angle A = right-facing ring**
**Approved:** 2026-09-03 (owner command: خوبه، برو بعدی)
**Source release:** [media-originals-v1](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-originals-v1) — `radman-product-images-20260829-052041.zip`
**Pilot release:** [media-image-pipeline-v1-p384-a](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-image-pipeline-v1-p384-a) — `radman-image-pipeline-v1-product-384-angle-A.zip`
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## ✅ Owner decision

Angle A of product 384 owner-approved. All 4 outputs READY. Angle B is in production and will be submitted for review next.

## Approved outputs and storage

Copied byte-for-byte from the approved release asset (SHA-256 verified against the release ZIP before copying).

| Source output (release) | Stored as | wordpress_action |
|---|---|---|
| step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | **`replace_featured_image`** |
| step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |

## QA (from qa-report-384-angle-a.md)

| Output | ORIGINAL_REATTACHED | VIEWPOINT_UNCHANGED | RING_IDENTITY_PRESERVED | BAND_CLOSED | HAND_SIDE | Status |
|---|---|---|---|---|---|---|
| step1 | YES | YES | YES | YES | NA | READY |
| step2 | YES | YES | YES | YES | NA | READY |
| step3 | YES | NA (new still-life) | YES | YES | NA | READY |
| step4 | YES | NA (new on-hand) | YES | YES | RIGHT | READY |

- **Band closed:** all outputs render the complete closed shank (RADMAN rings are always closed-band).
- **Step1/Step2 are masked edits of the original** — watermark removed / pink→charcoal only; ring, box, viewpoint, crop unchanged.
- **Original re-attached:** the exact angle-A original (attachment 385) was re-read and attached before every AI call; no generated image used as reference.
- **Hand rule:** angle A (right-facing) → adult male **RIGHT** hand. Verified: back of right hand, thumb on left of frame, 5 fingers, ring on ring finger.

## Product identity lock

Oval milky-white Qaen tree agate cabochon with natural dark dendrite (tree-branch) pattern · beaded bezel · ornate openwork swirl/scroll 925 silver band · closed continuous shank · 3/4 upright right-facing viewpoint.

## Intended WordPress action (executed later by host from apply-manifest.tsv — nothing changed on WordPress)

- `ecommerce/main-black-bg-a.webp` → `replace_featured_image` (first approved main-black-bg for this product)
- all other three → `add_gallery_image`

## Pending

- Angle B (attachment 386, left-facing) — in production in this run; will be submitted as `media-image-pipeline-v1-p384-b`, stopped for owner review.
