# Approval Summary — Product 226 (PARTIALLY_APPROVED_PENDING_ANGLE_B)

**Product:** 226 · **SKU:** NM-3598 · **Attachments:** 227 (angle A), 228 (angle B)
**Title:** انگشتر نقره مردانه عقیق سوسنی یمنی (Men's silver ring with Yemeni Sosani agate)
**Storage date:** 2026-09-03
**Original set:** `media-originals-v1` (attachments 227 / 228; source `01-45.webp` / `02-43.webp`)
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## ✅ Owner decision (angle A)

Product 226 **angle A** (attachment 227, featured) owner-approved on 2026-09-03. All 4 outputs READY.
Angle A = right-facing ring. Bands closed, viewpoint preserved, ring identity intact.

`APPROVED_OUTPUTS (angle A)=step1,step2,step3,step4`

## ⏳ Angle B pending

Product 226 **angle B** (attachment 228, gallery-1) has been **generated and delivered as a pre-release** but is **NOT yet owner-approved** for storage. It is flagged `review_only` in `apply-manifest.tsv`. Do NOT mark product 226 complete.

## Angle coverage

| Angle | Role | attachment_id | Original filename | Processed |
|---|---|---|---|---|
| A | featured | 227 | `product-226-sku-NM-3598-featured-attachment-227.webp` | ✅ 4/4 steps (APPROVED) |
| B | gallery-1 | 228 | `product-226-sku-NM-3598-gallery-1-attachment-228.webp` | ⏳ 4/4 generated (REVIEW_PENDING) |

## Approved outputs and storage (angle A)

| Angle | Source output | Stored as | wordpress_action |
|---|---|---|---|
| A | pilot/angle-A/step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| A | pilot/angle-A/step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | `replace_featured_image` |
| A | pilot/angle-A/step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| A | pilot/angle-A/step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |

## ✅ Permanent rules — verified per output (angle A)

| Angle | Att | ORIGINAL_REATTACHED | VIEWPOINT_UNCHANGED (step1/2) | RING_IDENTITY_PRESERVED | BAND_CLOSED | HAND_SIDE (step4) | Status |
|---|---|---|---|---|---|---|---|
| A | 227 | YES | YES | YES | YES | RIGHT | 4/4 READY |

- **Closed band:** RADMAN rings are always closed-band; any apparent opening in an original is only the display box hiding part of the shank. All outputs rendered a complete continuous closed shank.
- **Viewpoint preserved:** angle A step1/step2 done as strict masked in-place edits; viewpoint/crop/box unchanged.
- **Original re-attached:** the real original of angle A (attachment 227, re-downloaded from `media-originals-v1`) was attached before every generation call. No generated output was used as a reference.
- **Hand rule:** angle A (right-facing) → adult male RIGHT hand. (Angle B, when approved, uses adult male LEFT hand per the hand rule.)

## Product identity lock

Pale lilac / milky translucent agate cabochon in an all-silver claw-prong crown mount · ornate engraved silver shoulders · engraved inscription band beneath the bezel · continuous closed silver shank.

## Intended WordPress action (angle A)

To be executed later by the WordPress host from `apply-manifest.tsv`. **No WordPress or hosting change has been made.**

- `ecommerce/main-black-bg-a.webp` → `replace_featured_image` (featured image for attachment 227)
- all other three approved angle-A images → `add_gallery_image`

## Process constraints observed

- Output format: WebP quality 90, 1024×1024 (matches accepted baseline for prior approved products).
- Work confined to branch `ai-media-cleaning-pilot-20260829`; `main` untouched.
- No WordPress or hosting-server modification. Pull request #36 **not merged**.
