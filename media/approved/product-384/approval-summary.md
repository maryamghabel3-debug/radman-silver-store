# Approval Summary — Product 384 (FINAL, fully approved)

**Product:** 384 · **SKU:** 17224539 · **Title:** انگشتر نقره مردانه شجر قائن طبیعی (Men's Silver Ring — Natural Qaen Tree Agate)
**Attachments:** 385 (angle A, featured), 386 (angle B, gallery-1)
**Approved:** 2026-09-03 (owner command: خوبه، برو بعدی — both angles)
**Source release:** [media-originals-v1](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-originals-v1) — `radman-product-images-20260829-052041.zip`
**Pilot releases:** [media-image-pipeline-v1-p384-a](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-image-pipeline-v1-p384-a) · [media-image-pipeline-v1-p384-b](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-image-pipeline-v1-p384-b)
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## ✅ Owner decision

Product 384 owner-approved (both angles). All **8 images READY**.
Angle A = right-facing ring → male RIGHT hand; angle B = left-facing ring → male LEFT hand.
Bands closed, viewpoints preserved, ring identity intact. Nothing for this product remains pending.

## Angle coverage — complete

| Angle | Role | attachment_id | Original filename | Processed |
|---|---|---|---|---|
| A | featured | 385 | `product-384-sku-17224539-featured-attachment-385.webp` | ✅ 4/4 steps |
| B | gallery-1 | 386 | `product-384-sku-17224539-gallery-1-attachment-386.webp` | ✅ 4/4 steps |

All originals for this product_id are covered (2 of 2).

## Approved outputs and storage

Copied byte-for-byte from the approved release assets (SHA-256 verified against each release ZIP before copying).

| Angle | Source output (release ZIP) | Stored as | wordpress_action |
|---|---|---|---|
| A | step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| A | step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | **`replace_featured_image`** |
| A | step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| A | step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |
| B | step1-no-watermark.webp | `ecommerce/original-clean-b.webp` | `add_gallery_image` |
| B | step2-black-background.webp | `ecommerce/main-black-bg-b.webp` | `add_gallery_image` |
| B | step3-luxury-promo.webp | `gallery/luxury-promo-b.webp` | `add_gallery_image` |
| B | step4-on-finger.webp | `gallery/on-finger-b.webp` | `add_gallery_image` |

## Rejected outputs

None. All eight outputs approved for website use.

## Permanent rules — verified per output (from QA reports)

| Angle | Att | ORIGINAL_REATTACHED | VIEWPOINT_UNCHANGED (step1/2) | RING_IDENTITY_PRESERVED | BAND_CLOSED | HAND_SIDE (step4) | Status |
|---|---|---|---|---|---|---|---|
| A | 385 | YES | YES | YES | YES | RIGHT | 4/4 READY |
| B | 386 | YES | YES | YES | YES | LEFT | 4/4 READY |

- **Closed band:** all outputs render the complete closed shank (RADMAN rings are always closed-band).
- **Step1/Step2 are masked edits of each angle's own original** — watermark removed / pink→charcoal only; ring, box, viewpoint, crop unchanged (adaptive gold-emblem detection: A = bottom-right, B = bottom-left).
- **Original re-attached:** the exact original of each angle (attachments 385 / 386) was re-read and attached before every AI call; no generated image used as reference.
- **Hand rule:** angle A (right-facing) → adult male RIGHT hand; angle B (left-facing) → adult male LEFT hand. Opposite hands confirmed with edge crops (thumb position + back-of-hand).

## Product identity lock

Oval milky-white Qaen tree agate cabochon with natural dark dendrite (tree-branch) pattern · beaded bezel · ornate openwork swirl/scroll 925 silver band · closed continuous shank · 3/4 upright viewpoint (A faces right, B faces left).

## Intended WordPress action (executed later by host from apply-manifest.tsv — nothing changed on WordPress)

- `ecommerce/main-black-bg-a.webp` → `replace_featured_image` (first approved main-black-bg for this product)
- all other seven images → `add_gallery_image`

## Process constraints observed

- Source archives downloaded from release, single file extracted per angle, archive deleted immediately; only current-angle files kept on disk (work dir /tmp/radman, <200 MB).
- Outputs: WebP quality 90, 1024×1024 (step3/4), 1600×1600 masked edits.
- Work confined to branch `ai-media-cleaning-pilot-20260829`; `main` untouched; PR #36 **not merged**.

## Next

Product 384 is complete. Pipeline advanced to **product 390 (SKU 13204540), angle A** — shipped as `media-image-pipeline-v1-p390-a`, awaiting owner review.
